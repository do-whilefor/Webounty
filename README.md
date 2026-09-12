<h1 align="center">webounty</h1>

<p align="center">面向授权漏洞赏金与 AI 辅助漏洞研究的单会话 Wiki 与证据检索 Skill，用于跨轮积累观察、检索可复用的能力与前提、提出并验证漏洞链。</p>

<p align="center">
  <a href="#使用边界"><img src="https://img.shields.io/badge/Scope-Authorized%20Security%20Research-blue" alt="Scope: Authorized Security Research"></a>
  <a href="#安装与使用"><img src="https://img.shields.io/badge/Skill-Claude%20Code%20%7C%20Codex-6f42c1" alt="Skill: Claude Code and Codex"></a>
  <a href="#安装与使用"><img src="https://img.shields.io/badge/Python-3.10%2B-informational" alt="Python 3.10+"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow" alt="License: MIT"></a>
</p>

`webounty` 是一个面向授权 Web 安全测试、漏洞赏金和 CTF 的 Skill。

它要解决的问题很具体：一次研究往往跨越很多轮对话，中途会遇到上下文压缩、执行者更换、目标追加和子问题并行。模型的对话记忆在这些情况下不可靠——容易重复已经做过的测试、漏掉已经排除的路径，或者反过来把几轮之前的推测当成已验证结论继续使用。

`webounty` 把「本轮对目标的理解」写进项目内的 Wiki，把「实际观察到的原始请求、响应和结果」单独封存为不可变观察，再提供一套按能力供需检索的机制，让新取得的观察能够和之前的能力、前提、反证对上。宿主 Claude 负责推理和调用现有工具执行；附带脚本只负责存储、检索与条件检查，不扫描网络、不发起请求、不攻击目标。

---

## 核心原则

> 广泛探索，严格验证。没有完整证据，不确认漏洞。

本仓库强调以下原则：

- 以服务端认证、授权、对象归属、租户隔离、状态流转和业务规则为主要安全边界。
- 静态分析、扫描器结果、错误信息、指纹和历史案例只能生成线索，不能替代动态验证。
- 技术命中不等于漏洞成立；必须继续验证可获得的能力、影响对象、数据或资产、业务结果、影响范围和前置条件。
- 用文件保存状态和证据，不让模型仅凭上下文记忆重建结论。
- 候选链、检索分数和机械检查结果固定为非证据。类型或别名一致只说明可能相关；`compatible` 和 `coverage.complete` 只表示声明的条件通过了机械检查，实际成立仍须证明产物被下游真实消费。
- 两个步骤分别成功不等于连接成功，各边分别成功也不保证整条链在同一组条件下成立。
- 所有测试仅限合法、明确授权和可控的环境。

## 解决的问题

### 1. 让「本轮理解」和「原始证据」分离

Wiki 保存本轮对目标的判断、适用条件、反证和缺口；`evidence/` 保存实际观察的请求、响应与文件。页面只保存摘要和引用，不复制原件内容。这样判断可以随新观察修订，而原始证据保持不可变，随时可以按 ID 回取核对。

### 2. 按能力供需检索，而不是按漏洞名称检索

记录不只保存「高分漏洞」。正常业务步骤同样可以声明自己提供什么能力（`capability.provides`）、需要什么前提（`capability.needs`）以及控制范围。当路径受阻或需要补齐某个缺口时，检索会在整个会话范围内向前找消费者、向后找前提提供者，包括当前分支之外的目录。

查询应当说明谁能为缺失输入提供数据、谁消费新产物、正常基线在哪里、哪项反证可能改变判断，而不是只搜索一个漏洞名称。

### 3. 检查多输入组合的完整条件

一个消费者常常需要多个输入同时成立（AND），其中每个输入又有备选来源（OR）。脚本按组合逐个检查前提、共同条件和反证，并在当前方案有缺口时继续检查备选，不把单个方案的失败当作整个组合失败。`plan`、`inputs` 和 `alternatives` 都是待验证线索。

### 4. 区分反证、未复现与无法判断

负结果记录「哪个命题、在什么条件下、通过什么有效观察被否定」。一次 403、404、工具失败或空输出本身不是整个漏洞类别安全的证明。条件未变时不重复无增益的尝试；记录适用条件和重开条件，新能力补齐旧缺口时重新评估。

### 5. 本地观察对照

`compare` 只读取本轮两份已保存观察及其关联原件，输出来源 ID、修订与定位、已记录的身份和条件、请求变化路径、HTTP 状态、body 摘要与选定业务字段。差异视图是派生分析，保存判断时应引用两份原始观察，不把比较报告另当独立原件。

HTTP 200/403、长度或单次耗时变化都不自动说明漏洞、反证或修复。

## 工作循环

```text
读取本会话知识
  → 找到缺口
  → 取得新观察
  → 写入 Wiki
  → 检索可连接的能力与前提
  → 验证连接
  → 更正受影响判断
  → 更新 Wiki
```

对应的命令为 `context` → `record` → `discover` → `compare` / `read`。`context` 支持跨轮游标只读变化项、缺口和候选链；上下文压缩后加 `--refresh` 重发当前问题的完整视图。

## 仓库内容

```text
webounty/
├── SKILL.md                        # 技能入口：工作循环与命令
├── agents/
│   └── openai.yaml                 # Codex / OpenAI 接口描述
├── assets/
│   ├── icon.svg
│   └── record-example.json         # 记录提交格式示例（虚构数据，非目标证据）
├── references/
│   ├── claude-code.md              # 安装、依赖、会话语义与本地检查
│   ├── storage.md                  # 存储职责与 batch 提交格式
│   ├── retrieval.md                # 检索、游标与链路组合
│   ├── wiki-layout.md              # Wiki 页面组织与写法
│   ├── observation-comparison.md   # 本地观察对照及原脚本复用取舍
│   ├── scoring.md                  # CVSS 3.1 评分
│   ├── wiki-knowledge.schema.json  # 知识视图结构
│   ├── web-vulnhunt-LICENSE.txt    # 第三方 MIT 声明
│   └── methods/
│       ├── catalog.json            # 方法卡索引与来源哈希
│       └── *.md                    # 13 张验证方法卡
├── scripts/                        # 存储、检索、组合与评分（Python 标准库）
├── tests/                          # unittest 测试、回放与基准
├── THIRD_PARTY_NOTICES.md
├── README.md
└── LICENSE
```

### 验证方法卡

`references/methods/` 收录 13 张方法卡，按需读取，不遍历整个方法库：

| 方法 | 关注点 |
|---|---|
| `baseline-authz` | 业务正常基线与授权对照 |
| `flow-chain` | 多阶段业务流程与协议链 |
| `static-dynamic-retest` | 静态与动态关联、条件复测 |
| `observer-validity` | 观察器有效性与差分对照 |
| `controller-reach` | 过滤器、路由与控制器可达性 |
| `capability-consumer` | 凭证能力及其最终消费者 |
| `protocol-binding` | 协议挑战、主体与消费者绑定 |
| `patch-differential` | 补丁差分与部署条件 |
| `authorization-context` | 授权范围与操作语义 |
| `evidence-linkage` | 执行关联与指纹不确定性 |
| `asset-attribution` | 资产归因与发现有效性 |
| `impact-assessment` | 影响评估与项目评分 |
| `hypothesis-lifecycle` | 条件化命题关闭与报告更正 |

方法是验证建议，不是目标证据。用 `python3 scripts/session.py methods --query '当前验证缺口'` 读取。

## 安装与使用

### 1. 安装

把完整的 `webounty` 文件夹放入个人技能目录 `~/.claude/skills/webounty/` 或项目技能目录 `.claude/skills/webounty/`，确保 `SKILL.md` 直接位于该目录，不要多套一层目录。

依赖：

- Python 3.10+，仅使用标准库，无需 pip、向量数据库、独立模型 API 或固定 MCP。
- Node.js 18+，仅 CVSS 计算器需要。

系统使用 `python` 命令时，确认它是 Python 3 后替换示例中的 `python3`。

### 2. 开始一次研究

在本次研究的项目目录执行 start，资料保存到该项目的 `.webounty/<会话标识>/`：

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/session.py" start \
  --session-id "${CLAUDE_SESSION_ID}" --question '当前研究目标与完成条件'
```

当前工作目录不是项目目录时，加 `--project-root '项目绝对路径'`。脚本不自动向上查找 Git 根目录。

`${CLAUDE_SKILL_DIR}` 和 `${CLAUDE_SESSION_ID}` 是 Claude Code 在技能正文中替换的变量，不是要求自己设置的 shell 环境变量。其他宿主不支持替换时，显式填写技能目录并为本次研究生成一次随机会话 ID。

记住返回的 `project_root / root / run_id / session_id`，后续命令显式传本轮 `root` 和 `run_id`，即使切换工作目录也沿用。

### 3. 常用命令

运行 `python3 scripts/session.py --help`，每个子命令也支持 `--help`。

| 命令 | 用途 |
|---|---|
| `start` | 创建或复用会话 |
| `record` | 提交观察、记录和 Wiki，并返回相关连接 |
| `context` | 默认返回紧凑知识与来源引用；`--cursor` 跨轮差量，`--refresh` 恢复当前视图 |
| `discover` | 全会话能力供需检索、候选路径、多输入组合与表达复核 |
| `read` | 按 ID 读取记录、页面、观察或工件及必要来源 |
| `compare` | 并列比较两份已存观察的条件、响应和业务字段 |
| `methods` | 读取固定方法，不创建会话 |
| `audit` / `wiki audit` / `wiki knowledge` | 检查存储、引用或读取知识视图 |
| `finish` | 明确收尾，可显式导出快照 |

### 4. 评分

```bash
node "${CLAUDE_SKILL_DIR}/scripts/cvss31-calculator.js" \
  --json 'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N'
```

仅计算 CVSS 3.1 Base，保留向量、分数和各指标依据。单项分数不相加，不因可能组合抬高单项影响，不因低分删除有用能力。证据状态与严重性分开。

### 5. 收尾

普通回复结束不是会话结束。只有明确结束本次研究时才 finish：

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/session.py" finish \
  --root '本轮root' --run-id '本轮run_id' --session-id '本轮session_id'
```

`finish` 只清理 `.webounty/` 下归属匹配的本轮会话子目录，保留项目、其他会话和原始用户文件。需要保留快照时加 `--export '新的输出目录'`。

## 本地检查

在技能目录运行：

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

测试使用虚构资料和临时目录，覆盖存储、检索、候选关系与评分算术，不代表所有真实目标上的链路发现效果。

| 脚本 | 用途 |
|---|---|
| `python3 -B tests/evaluate_retrieval.py` | 固定检索案例的 MRR、Recall@5 与词法检索耗时 |
| `python3 -B tests/benchmark_retrieval.py --sizes 100 300` | 冷/热查询、单条更新、父目录改名、紧凑输出与游标恢复 |
| `python3 -B tests/replay_session.py` | 固定六轮回放：问句改写、新能力补齐前提、无关修改、目录改名、反证与压缩后恢复 |

回放的 `host_tokens` 为 `null`：离线回放不测 Claude 的理解、真实攻击实验或实际 token 消耗。

## 使用边界

本仓库仅用于以下场景：

- 明确授权的漏洞赏金和 SRC 测试范围。
- 用户自有系统、测试环境、实验室或本地搭建的开源项目。
- CTF、靶场、安全课程和防御性研究。
- 经授权的代码审计、接口测试、浏览器分析和漏洞复现。

禁止用于：

- 未经授权扫描、探测、入侵或利用第三方系统。
- DoS、DDoS、持续压测、资源耗尽或影响业务可用性的行为。
- 删除、破坏或不可逆修改真实业务数据。
- 建立 WebShell、后门、计划任务、启动项、反向 Shell 或其他持久化访问。
- 横向移动、攻击无关资产、窃取凭证、钓鱼、撞库或社会工程。
- 对非测试账号执行真实支付、退款、权限变更、批量通知或其他高影响业务操作。
- 违反适用法律、平台规则、漏洞赏金政策、SRC 规则或目标方明确限制的行为。

## 免责声明

本仓库中的 Skill、脚本、方法卡、配置和文档仅用于合法授权的安全研究、教育、代码审计和测试环境。

使用者必须自行确认其拥有充分授权，并对目标范围、测试方法、工具配置、数据处理、证据保存、漏洞提交和后续影响承担全部责任。仓库作者不对任何未经授权的使用、错误配置、数据丢失、业务中断、法律责任、第三方索赔或其他直接或间接损失承担责任。

本仓库不保证能够发现漏洞，不保证发现数量或严重程度，也不保证检索结果、候选链、工具输出、评分或漏洞结论始终正确、完整、适用于特定环境或符合特定平台规则。检索分数、`ready` 状态、`compatible` 与 `coverage.complete` 均只表示资料可读取或声明的条件通过机械检查，不构成漏洞成立证明。任何结论都应由具备资质的测试人员进行独立验证。

本 Skill 不安装 hook、不修改客户端配置，脚本也不扫描网络或执行攻击。异常关窗或进程被终止时，不保证立即清理 `.webounty/` 下的会话资料。

仓库中引用、收录或改编的第三方资料、方法、文档和代码，其著作权和许可证仍归原作者或权利人所有。根目录 MIT License 仅适用于仓库作者有权许可的原创或修改内容；第三方材料应遵循其各自的许可证、署名和使用条件，详见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

## 第三方材料与归属

- Wiki / RAG 原型来自用户提供的材料，本仓库对其进行了工程化改造，新增会话发布与能力发现代码。
- CVSS 计算器与方法卡的部分内容改编自 Jase-SecKit 的 Web-Vulnhunt，其 MIT 声明保留在 [references/web-vulnhunt-LICENSE.txt](references/web-vulnhunt-LICENSE.txt)，版权归 w1th0ut（U-Sec / 无界安全）所有。本仓库修正了 Scope Changed、浮点 Roundup 与输入处理，使其符合 FIRST CVSS v3.1。
- Wiki 总览/详情/负结果的组织方式与本地观察对照借鉴了 Web-Vulnhunt 的报告结构、被否决假设、复核日志、负对照、授权矩阵与补丁验证思路。原网络 Shell 脚本未收录，其状态码启发式和针对特定目标的结论不作为证据。
- 评分的规范性依据为 [FIRST CVSS v3.1 规范](https://www.first.org/cvss/v3.1/specification-document) 与 [用户指南](https://www.first.org/cvss/v3.1/user-guide)，以链接方式引用，不再分发。CVSS 由 FIRST.Org, Inc. 所有并经许可使用。

## 贡献与维护

提交修改时建议：

```cmd
git add -A -- .
git status --short
git commit -m "更新说明"
git pull --rebase origin main
git push origin main
git status
```

目标结论不得回写技能文件；通用方法可以保留。不扫描其他会话目录寻找经验。

## License

本仓库中作者有权许可的原创和修改内容采用 [MIT License](LICENSE)。第三方材料适用其各自许可证，见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
