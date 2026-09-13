"""Streaming local evidence I/O. Buffer sizes control memory, never corpus size."""

from __future__ import annotations

import codecs
from dataclasses import dataclass
import hashlib
from pathlib import Path


BUFFER_BYTES = 1024 * 1024
TEXT_CHUNK_BYTES = 64 * 1024
TEXT_OVERLAP_BYTES = 256


def fingerprint(path):
    path = Path(path)
    stat = path.stat()
    return (str(path.resolve()), stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns, stat.st_ino)


def scan(path):
    before = fingerprint(path)
    checksum, size = hashlib.sha256(), 0
    decoder = codecs.getincrementaldecoder("utf-8")()
    text = True
    with Path(path).open("rb") as stream:
        for data in iter(lambda: stream.read(BUFFER_BYTES), b""):
            checksum.update(data)
            size += len(data)
            if text:
                try:
                    decoder.decode(data)
                    text = b"\0" not in data
                except UnicodeError:
                    text = False
    if text:
        try:
            decoder.decode(b"", final=True)
        except UnicodeError:
            text = False
    if before != fingerprint(path):
        raise ValueError("source changed while reading")
    return {"sha256": checksum.hexdigest(), "bytes": size,
            "text_encoding": "utf-8" if text else None, "fingerprint": before}


@dataclass
class FileCopy:
    """A proposed immutable file, copied only after publication validation."""

    source: Path
    metadata: dict

    def write_to(self, stream):
        checksum, size = hashlib.sha256(), 0
        with self.source.open("rb") as source:
            for data in iter(lambda: source.read(BUFFER_BYTES), b""):
                checksum.update(data)
                size += len(data)
                stream.write(data)
        if checksum.hexdigest() != self.metadata["sha256"] or size != self.metadata["bytes"]:
            raise ValueError("source changed before publication; submit the current source")


def text_chunks(path):
    """Yield UTF-8 source windows with byte locators, preserving every source byte.

    The overlap is only for raw lexical matching; Wiki judgments stay whole.
    No extracted window is a new independent observation.
    """
    tail, offset = b"", 0
    with Path(path).open("rb") as stream:
        while data := stream.read(TEXT_CHUNK_BYTES):
            # Finish the last UTF-8 code point before assigning a byte locator.
            while True:
                try:
                    data.decode("utf-8")
                    break
                except UnicodeDecodeError as exc:
                    if exc.reason != "unexpected end of data":
                        raise
                    extra = stream.read(1)
                    if not extra:
                        raise
                    data += extra
            window = tail + data
            yield {"offset": offset - len(tail), "length": len(window),
                   "sha256": hashlib.sha256(window).hexdigest()}, window.decode("utf-8")
            offset += len(data)
            tail = window[-TEXT_OVERLAP_BYTES:]
            while tail and tail[0] & 0xC0 == 0x80:
                tail = tail[1:]
