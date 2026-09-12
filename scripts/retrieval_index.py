"""Rebuildable SQLite term projection. State, Wiki and evidence remain authoritative.

Warm reads inspect metadata/stat signatures and fetch only query postings. A hit
must still pass Corpus.package's current source/hash checks before evidence use.
No cached text or cached validation verdict is returned as evidence.
"""

from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
import sqlite3


FORMAT_VERSION = "1"


def _encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _digest(value):
    return hashlib.sha256(_encode(value).encode()).hexdigest()


def _metadata(row):
    return {key: value for key, value in row.items() if not key.startswith("_") and key != "text"}


def _references(value):
    """Explicit structured links only, including links nested in knowledge facets."""
    if isinstance(value, dict):
        for field, child in value.items():
            if field.endswith(("_ref", "_refs", "_ids")) or field in {
                    "requires", "steps", "contradicts", "corrected_by", "superseded_by", "contradicted_by"}:
                for item in child if isinstance(child, list) else [child]:
                    if isinstance(item, str):
                        yield item
                    elif isinstance(item, dict) and "id" in item:
                        yield item["id"]
            if isinstance(child, (dict, list)):
                yield from _references(child)
    elif isinstance(value, list):
        for child in value:
            yield from _references(child)


class _Signatures:
    def __init__(self, corpus):
        self.corpus = corpus
        self.files, self.page_candidates = {}, {}

    def file(self, relative):
        if relative not in self.files:
            path = self.corpus.path(relative)
            try:
                stat = path.stat()
                value = (str(path), stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns, stat.st_ino)
            except FileNotFoundError:
                value = (str(path), "missing")
            self.files[relative] = value
        return self.files[relative]

    def artifact(self, aid):
        meta = self.corpus.artifacts.get(aid)
        if meta is None:
            return aid, "missing"
        derived = (meta.get("sha256") in self.corpus.derived_hashes or
                   self.corpus.path(meta["path"]) in self.corpus.derived_paths)
        return meta, self.file(meta["path"]), derived

    def linked_sources(self, block):
        """Invalidate knowledge fields when any reachable premise or source changes.

        This follows provenance metadata; it does not open all source files or
        treat references as proof. Reverse correction edges and page discovery
        candidates ensure newly arrived counterevidence invalidates old entries.
        """
        corpus = self.corpus
        pending_blocks = [block["page_id"] + "/" + block["block_id"]]
        seen_blocks, pending, values = set(), [], []
        while pending_blocks:
            key = pending_blocks.pop()
            if key in seen_blocks:
                continue
            seen_blocks.add(key)
            row = corpus.blocks.get(key)
            if row is None:
                values.append((key, "missing"))
                continue
            page = corpus.pages[row["page_id"]]
            values.append((key, _metadata(row), self.file(page["path"])))
            pending.extend(_references(row))
            pending.extend(ref if isinstance(ref, str) else ref["id"]
                           for ref in page.get("source_refs", []))
            if hasattr(corpus, "candidates"):
                if row["page_id"] not in self.page_candidates:
                    self.page_candidates[row["page_id"]] = corpus.candidates(page)
                candidates = self.page_candidates[row["page_id"]]
                values.append(("candidates", row["page_id"], candidates))
                pending.extend(item["id"] for item in candidates)
            pending_blocks.extend(ref["page_id"] + "/" + ref["block_id"]
                                  for ref in row.get("required_block_refs", []))
            for ref in row.get("artifact_refs", []):
                values.append(("artifact", ref["artifact_id"], self.artifact(ref["artifact_id"])))
        seen = set()
        while pending:
            rid = pending.pop()
            if rid in seen:
                continue
            seen.add(rid)
            row = (corpus.records.get(rid) or corpus.entities.get(rid)
                   or corpus.observations.get(rid))
            values.append((rid, row))
            if row is None:
                continue
            pending.extend(_references(row))
            pending.extend(getattr(corpus, "reverse_corrections", {}).get(rid, ()))
            for field in ("artifact_id", "source_artifact_id"):
                if row.get(field):
                    values.append(("artifact", row[field], self.artifact(row[field])))
            for ref in row.get("artifact_refs", []):
                values.append(("artifact", ref["artifact_id"], self.artifact(ref["artifact_id"])))
        return sorted(values, key=_encode)

    def document(self, key, row):
        kind, _ = key
        values = [_metadata(row) if kind == "block" else row]
        if kind == "block":
            page = self.corpus.pages[row["page_id"]]
            # Siblings' prose does not affect this block, but a page file change
            # must be checked to detect unsanctioned edits and broken anchors.
            values.extend(({k: v for k, v in page.items() if k != "blocks"},
                           self.file(page["path"]), self.corpus.navigation_paths[row["page_id"]]))
            if row.get("knowledge"):
                values.append(self.linked_sources(row))
        elif kind == "observation":
            values.extend(self.artifact(row[field]) for field in ("artifact_id", "source_artifact_id")
                          if row.get(field))
        return _digest(values)


def _open(corpus):
    directory = corpus.path("cache")
    directory.mkdir(exist_ok=True)
    path = corpus.path("cache/retrieval.sqlite")
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA foreign_keys=ON")
    connection.executescript("""
        CREATE TABLE IF NOT EXISTS metadata (name TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS documents (
            doc_id INTEGER PRIMARY KEY, kind TEXT NOT NULL, rid TEXT NOT NULL,
            signature TEXT NOT NULL, role TEXT, usable INTEGER NOT NULL,
            UNIQUE(kind, rid));
        CREATE TABLE IF NOT EXISTS fields (
            doc_id INTEGER NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
            field TEXT NOT NULL, length INTEGER NOT NULL, PRIMARY KEY(doc_id, field));
        CREATE TABLE IF NOT EXISTS terms (
            term TEXT NOT NULL, doc_id INTEGER NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
            field TEXT NOT NULL, count INTEGER NOT NULL, PRIMARY KEY(term, doc_id, field));
        CREATE INDEX IF NOT EXISTS terms_by_document ON terms(doc_id);
    """)
    scope = {"format": FORMAT_VERSION, "run_id": corpus.run_id}
    if dict(connection.execute("SELECT name, value FROM metadata")) != scope:
        connection.execute("DELETE FROM documents")
        connection.execute("DELETE FROM metadata")
        connection.executemany("INSERT INTO metadata VALUES (?, ?)", scope.items())
        connection.commit()
    return connection


def lexical_projection(corpus, documents, query_terms, fields_for, tokenize, role_for):
    """Sync changed documents, then retrieve postings without retokenizing old text."""
    from wiki_structure import navigation_paths

    corpus.navigation_paths = navigation_paths(corpus.pages)
    signatures = _Signatures(corpus)
    connection = _open(corpus)
    totals = {"documents": len(documents), "reused_documents": 0, "indexed_documents": 0,
              "deleted_documents": 0, "tokenized_fields": 0}
    roles, unavailable = {}, set()
    field_cache = {}
    try:
        stored = {(kind, rid): (doc_id, signature, role, usable)
                  for doc_id, kind, rid, signature, role, usable in connection.execute(
                      "SELECT doc_id, kind, rid, signature, role, usable FROM documents")}
        connection.execute("BEGIN")
        removed = stored.keys() - documents.keys()
        connection.executemany("DELETE FROM documents WHERE doc_id=?",
                               ((stored[key][0],) for key in removed))
        totals["deleted_documents"] = len(removed)
        for key, row in documents.items():
            signature = signatures.document(key, row)
            previous = stored.get(key)
            if previous is not None and previous[1] == signature:
                totals["reused_documents"] += 1
                if key[0] == "block":
                    roles[key] = previous[2]
                    if not previous[3]:
                        unavailable.add(key)
                continue
            if key[0] == "block" and hasattr(corpus, "ensure_page"):
                corpus.ensure_page(row["page_id"])
            usable = not (key[0] == "block" and (row.get("_issues") or
                corpus.page_issues.get(row["page_id"])))
            role = role_for(row) if key[0] == "block" else None
            if key[0] == "block":
                roles[key] = role
                if not usable:
                    unavailable.add(key)
            if previous is not None:
                doc_id = previous[0]
                connection.execute("DELETE FROM fields WHERE doc_id=?", (doc_id,))
                connection.execute("DELETE FROM terms WHERE doc_id=?", (doc_id,))
                connection.execute("UPDATE documents SET signature=?, role=?, usable=? WHERE doc_id=?",
                                   (signature, role, usable, doc_id))
            else:
                doc_id = connection.execute(
                    "INSERT INTO documents(kind, rid, signature, role, usable) VALUES(?,?,?,?,?)",
                    (*key, signature, role, usable)).lastrowid
            totals["indexed_documents"] += 1
            if not usable:
                continue
            for field, value in fields_for(key[0], row, corpus).items():
                if not value:
                    continue
                if value not in field_cache:
                    field_cache[value] = Counter(tokenize(value))
                    totals["tokenized_fields"] += 1
                counts = field_cache[value]
                length = sum(counts.values())
                if not length:
                    continue
                connection.execute("INSERT INTO fields VALUES(?,?,?)", (doc_id, field, length))
                connection.executemany("INSERT INTO terms VALUES(?,?,?,?)",
                                       ((term, doc_id, field, count) for term, count in counts.items()))
        averages = dict(connection.execute("SELECT field, AVG(length) FROM fields GROUP BY field"))
        postings, field_lengths = defaultdict(dict), defaultdict(dict)
        # Query terms use a temporary table rather than SQLite's parameter limit;
        # callers need no artificial query-length or top-k cap.
        connection.execute("CREATE TEMP TABLE query_terms (term TEXT PRIMARY KEY)")
        connection.executemany("INSERT INTO query_terms VALUES(?)", ((term,) for term in query_terms))
        for term, kind, rid, field, count, length in connection.execute("""
            SELECT t.term, d.kind, d.rid, t.field, t.count, f.length
            FROM query_terms q JOIN terms t ON t.term=q.term
            JOIN documents d ON d.doc_id=t.doc_id
            JOIN fields f ON f.doc_id=t.doc_id AND f.field=t.field
        """):
            key = kind, rid
            postings[term].setdefault(key, {})[field] = count
            field_lengths[key][field] = length
        # An eager Corpus may hold old bytes while stat() already sees a new
        # file. Never commit that mixed signature/text pair for the next query.
        # The caller still checks its snapshot before using returned candidates.
        if corpus.stable():
            connection.commit()
        else:
            connection.rollback()
            totals["snapshot_changed"] = True
        corpus.retrieval_index_stats = totals
        return postings, field_lengths, averages, roles, unavailable
    finally:
        connection.close()
