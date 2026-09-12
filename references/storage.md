# 存储与提交格式

## 文件职责

以下路径均相对本轮 root：`<项目目录>/.webounty/<会话ID的SHA-256>/`。start 默认以调用时的工作目录作为项目目录，也可传 `--project-root`；后续命令直接沿用返回的 root。每个会话有独立状态、Wiki、原件和索引。

| 文件 | 职责 |
|---|---|
| session.json | 项目路径、会话 ID、run_id 与工作区归属 |
| state.json | 当前 Goal/Fact/Step/Finding/Capability/Chain 与实体、观察和工件索引 |
| evidence/ | 每次不可覆盖的观察 JSONL、可选原文件副本 |
| wiki/pages/ | 有稳定页面与块 ID 的 Markdown |
| wiki/manifest.json | 稳定页面/块定位、父页面 ID、哈希、来源修订、检索字段及可选知识注释 |
| wiki/index.md | 派生导航 |
| cache/page-checks.json | 可重建的首页检查缓存；不作为来源，不替代读取和审计 |
| logs/ | 操作记录，不复制凭据或完整流量 |

一个会话一份工作区，多轮对话持续更新；ID 不含实际凭据。记录是真实状态，页面是有来源的解释，检索结果是读取视图。不要手工改哈希或清单，也不要把 Wiki 当作新的原始证据。

## 提交一个 batch

record --input 接收 UTF-8 JSON 文件，或 `--input -` 从 stdin 读取。顶层包含 entities、observations、records、pages 四个数组；没有更新的数组可省略。每项由作者提供稳定 id，脚本生成 revision、来源定位、工件哈希和 Markdown 锚点。

示例见 [record-example.json](../assets/record-example.json)。第一次可只提交观察和对应事实；有价值的能力随理解形成再补充，不要求一次填全。

### 原始观察

```json
{
  "id": "O-001",
  "summary": "本次实际观察的简短描述",
  "subject_refs": ["E-API"],
  "content": {
    "environment": "lab-v1",
    "actor_ref": "E-USER",
    "session_generation": "1",
    "stage": "submit",
    "request": {"method": "POST", "url": "https://training.invalid/export"},
    "response": {"status": 202, "body": {"job_id": "DEMO-JOB"}}
  }
}
```

content 可保存 HTTP、日志、源码定位、用户输入等 JSON 对象，字段来自真实资料；上例为虚构格式。主体 ID 必须先登记或在同批 entities 中登记。没有主体时使用空数组，不编造。

source_path 可填写实际输入文件的绝对路径，脚本复制原件并登记来源；原路径不会删除。观察存为单独 JSONL，不允许重复覆盖 ID。证据更正用新观察和对应记录的更正关联表达。

### 实体

实体字段为 id、kind、title/summary，按实际需要增加 aliases、source_refs、owner_ref、tenant_ref、asset_ref。后面三个字段引用实体；source_refs 引用研究记录。观察到、文档声明和推测关系的区别在事实及正文中说明，名字相同不是同一实体的证明。

### 研究记录

共同字段：id、kind、status、summary、subject_refs、observation_refs。kind 可用 Goal、Fact、Step、Finding、Capability、Chain。其余字段按问题需要添加，如 title、conditions、limitations、reopen_when、change_reason、cvss。

| 类型 | 推荐用途与状态 |
|---|---|
| Goal | 目标、范围、完成条件；active/completed/blocked |
| Fact | 有条件的观察表述；observed |
| Step | 假设、缺口、下一验证；active/blocked/done |
| Finding | 候选漏洞及影响；candidate/verified/refuted/needs_review |
| Capability | 可供组合的能力与必要条件；observed/candidate/verified/refuted/needs_review |
| Chain | 组合及逐边状态；candidate/verified/refuted/needs_review |

记录关系 source_refs、requires、evidence_refs、supporting_fact_ids 等引用**记录 ID**。observation_refs 引用**观察 ID**。不要把原始观察 ID 填入 evidence_refs；Chain.links[].evidence_refs 是例外，专门引用连接观察。

capability.provides / capability.needs 是能力供需，不要混用记录级 requires 字段。详细结构见 [retrieval.md](retrieval.md)。

更新同一 ID 时，传入字段覆盖该字段，未传字段保留；嵌套对象和数组按整体替换，所以修改 capability 或 observation_refs 时传完整新值。用 change_reason 简要说明更正原因。脚本维护修订，不提供版本回滚。

修订时自动保存简短 history 条目，用于说明旧判断为何变化；其 record_refs / observation_refs 是历史定位，不加入当前必需证据。首页分区、发现详情、负结果和修订区的写法见 [Wiki 组织](wiki-layout.md)。

新反证可单独建记录并设 contradicts:[旧记录ID]。旧记录需要被修正时同时更新其 status 和关联；不要删除旧原件。依赖变化会让相关 Chain 转为 needs_review，页面会返回来源变化提示，Claude 应复核后重新发布。

曾取得的能力后来撤销或过期时，保留历史取得观察，新增当前失效观察，并修订该能力的当前可用性。摘要与 change_reason 说明反证针对的是“现在仍可使用”，不否定过去确实取得；尚未确认失效时保留待复核状态。

新记录的 contradicts 与旧记录对应的 contradicted_by 可以同时登记，表达同一反证关系；检索保留两端和原始观察。无需为反向查找重复登记。真正的 source_refs、requires 等循环依赖仍会被拒绝。

### 页面

不传 pages 时，每个新增/更新记录自动生成其主页 `WK-记录ID`。需要合并实体解释、业务流程或多个相关事实时，可显式提交：

```json
{
  "id": "WK-FLOW",
  "kind": "flow",
  "title": "报表生成与下载流程",
  "record_refs": ["F-001", "C-001"],
  "blocks": [{
    "id": "B-SUBMIT",
    "title": "提交响应能证明什么",
    "text": "受理响应提供任务标识，尚不能证明后台处理或下载成功。",
    "source_refs": ["F-001", "C-001"]
  }]
}
```

页面 kind 为 entity/flow/capability/question/chain。record_refs 是页面依据，块的 source_refs 可进一步缩小到其实际依赖。省略 blocks 则从记录生成可阅读块。

一块表达一个完整判断，条件、否定和结论不要切散。需要依赖其他块时用 required_block_refs:[{page_id,block_id}]。可选 knowledge 支持已有 boundary、controls、experiments、capability_links 和 lifecycle；详见 [知识注释 schema](wiki-knowledge.schema.json)。基础写入不要求填复杂注释。

页面可设 `parent_page_id` 指向同会话已有页面，或同批提交的页面；根页省略此字段或设为 `null`。目录关系只用于导航与检索，不增加事实依赖，也不意味着父页结论适用于所有子页。不存在的父页和循环关系会令提交失败。

页面和块均可提交 `summary`、`questions`、`keywords`、`aliases`；也可用 `retrieval` 对象组织已有检索字段。`summary` 使用简短文本，其余用字符串数组。问题优先取实际会话提问或当前已明确的缺口；仅有问题不能证明答案或能力已成立，不需要每轮为整个 Wiki 生成问答。检索字段写入 manifest，正文和原始证据仍各自保留；它们不替代来源和适用条件。

```json
{
  "id": "WK-FLOW",
  "parent_page_id": "WK-REPORTS",
  "questions": ["提交得到的任务标识能否满足下载流程的前提？"],
  "keywords": ["导出", "任务标识"]
}
```

已有页面只提交 `id` 加标题、父 ID、kind 或上述检索字段时，执行元数据更新：保留原块、稳定锚点、来源修订和已审阅集合。标题改变只更新页首；移动目录不改正文。祖先标题路径由当前父子关系派生，不在每个后代中存副本；索引根据变化路径更新受影响条目。改名或移动不代表已复核旧解释，待复核状态不会因此消失。

提交 `blocks` 或 `record_refs` 时仍是完整页面编辑，应提供完整的新解释及实际来源；需要保留的父关系与检索字段也一并传入。自动从记录生成的块由脚本标为 `representation: record`，使紧凑读取能避免重复返回同一记录正文；作者块不能自行声明这个标记。

同一判断保持主要页面，其余页面用链接。脚本只刷新提交的页面或自动主页，不会冒充读懂所有相关新证据；未复核的新资料应保持 review_required 提示。

发布时按需读取页面和原件。首页检查复用上一轮与当前依赖签名、相关文件元数据均相同的结果；新反证、来源修订、主体候选变化和适用条件变化会使相关检查失效。显式 `required_block_refs` 指向的解释待复核时，引用它的页面也显示待复核。新增资料不会自动加入旧页的已审阅集合。

仅改名或移动页面时校验页面内容，不重新展开未变化的证据。当前状态、清单和候选签名仍会参与本次计算，首页仍按当前状态重写；局部更新指减少无关页面与原件读取，并不声称所有处理都是常数成本。

检查缓存保存在 `cache/page-checks.json`，可删除后由下次提交重建。文件大小、修改时间、变更时间等用于发现普通外部修改，相关检查会重新读取并验证哈希。缓存只供首页发布复用；`read / recall / audit` 仍独立验证所需内容，完整 `audit` 保持全量。缓存和其他派生文件不能导入为原始证据。

## Chain 记录

Chain.steps 是拓扑有序记录 ID，links 描述前面的能力如何提供后面步骤的输入。一个步骤可有多个必要输入和多条入边，仍须满足全部前提。

```json
{
  "id": "CH-001", "kind": "Chain", "status": "candidate",
  "summary": "研究导出产物能否进入下载流程",
  "steps": ["C-001", "C-002"],
  "conditions": {"environment": "lab-v1"},
  "links": [{
    "producer_ref": "C-001", "consumer_ref": "C-002",
    "provide_index": 0, "need_index": 0,
    "assessment": "candidate", "evidence_refs": [],
    "conditions": {"environment": "lab-v1"},
    "note": "仍缺实际消费证据"
  }],
  "observation_refs": []
}
```

provide_index 和 need_index 从 0 开始。连接 assessment 为 candidate/verified/refuted。已验证连接需有双方原始观察及实际消费说明；最终 observation_refs 单独引用整链结果。脚本检查来源覆盖与明确条件冲突，不能判断作者写下的消费说明是否真实。

已具备的起始能力可写 needs:[]，明确能力已经取得的观察和适用条件；不能为了让整链通过而删除尚未满足的前提。只有实际验证后才提交 verified。

## 读取与复核

```bash
python3 scripts/session.py read --root '本轮root' --run-id '本轮run_id' --id C-001 --id WK-FLOW
python3 scripts/session.py audit --root '本轮root' --run-id '本轮run_id'
```

数据不正确时先修正当前 batch，命令失败后不要重放外部取证动作。一次提交在写入前检查结构和来源，但不是多文件事务或崩溃恢复系统；当前 MVP 要求单写者。
