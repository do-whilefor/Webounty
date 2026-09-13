<h1 align="center">Webounty</h1>

<p align="center">面向授权漏洞赏金与 AI 辅助漏洞研究的单会话 Wiki 与证据检索 Skill，用于跨轮积累观察、检索可复用的能力与前提、提出并验证漏洞链。</p>

<p align="center">
  <a href="#使用边界"><img src="https://img.shields.io/badge/Scope-Authorized%20Security%20Research-blue" alt="Scope: Authorized Security Research"></a>
  <a href="#安装与使用"><img src="https://img.shields.io/badge/Skill-Claude%20Code%20%7C%20Codex-6f42c1" alt="Skill: Claude Code and Codex"></a>
  <a href="#安装与使用"><img src="https://img.shields.io/badge/Python-3.10%2B-informational" alt="Python 3.10+"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow" alt="License: MIT"></a>
</p>

`Webounty` 是一个面向授权 Web 安全测试、漏洞赏金和 CTF 的 Skill。

它解决长轮次研究中的状态丢失问题：上下文压缩、执行者更换、目标追加或子问题并行时，模型容易重复测试、遗漏已排除路径，或把未经验证的推测重新当成事实。

`Webounty` 将当前研究状态写入项目 Wiki，将实际请求、响应和结果作为独立原始观察保存，并通过能力供需关系重新连接已有发现。宿主 Claude 负责推理和调用现有工具执行；附带脚本只负责存储、检索、组合与条件检查，不扫描网络、不发起请求、不攻击目标。

---

## 核心原则

> 广泛探索，严格验证。没有完整证据，不确认漏洞。

本仓库强调以下原则：

- 以服务端认证、授权、对象归属、租户隔离、状态流转和业务规则为主要安全边界。
- 静态分析、扫描器结果、错误信息、指纹和历史案例只能生成线索，不能替代动态验证。
- 技术命中不等于漏洞成立；必须继续验证可获得的能力、影响对象、数据或资产、业务结果、影响范围和前置条件。
- 用文件保存状态和证据，不让模型仅凭上下文记忆重建结论。
- 候选链、检索分数和机械检查结果固定为非证据；步骤分别成功也不代表连接或整条链已经成立。
- 所有测试仅限合法、明确授权和可控的环境。

## 解决的问题

### 1. 让「本轮理解」和「原始证据」分离

Wiki 保存本轮对目标的判断、适用条件、反证和缺口；`evidence/` 保存实际观察的请求、响应与文件。页面只保存摘要和引用，不复制原件内容。这样判断可以随新观察修订，而原始证据保持不可变，随时可以按 ID 回取核对。

### 2. 按能力供需检索，而不是按漏洞名称检索

记录不只保存「高分漏洞」。正常业务步骤同样可以声明自己提供什么能力（`capability.provides`）、需要什么前提（`capability.needs`）以及控制范围。

当路径受阻或需要补齐缺口时，检索会在整个会话范围内寻找消费者、前提提供者、正常基线和可能改变判断的反证，而不是只搜索漏洞名称。

### 3. 检查多输入组合的完整条件

一个消费者可能需要多个输入同时成立（AND），每个输入又可能存在多个来源（OR）。脚本按组合检查前提、共同条件和反证，并在当前方案有缺口时继续检查备选。

`plan`、`inputs` 和 `alternatives` 都只是待验证线索。

### 4. 区分反证、未复现与无法判断

负结果记录「哪个命题、在什么条件下、通过什么有效观察被否定」。一次 403、404、工具失败或空输出本身不是整个漏洞类别安全的证明。

条件未变时不重复无增益尝试；新能力补齐旧缺口时，可以重新评估此前关闭的路径。

### 5. 本地观察对照

`compare` 读取本轮两份已保存观察及其关联原件，输出来源 ID、修订与定位、身份和条件、请求变化、HTTP 状态、body 摘要与选定业务字段。

HTTP 200/403、长度变化或单次耗时变化都不自动说明漏洞、反证或修复。

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

对应命令为 `context` → `record` → `discover` → `compare` / `read`。

`context` 支持跨轮游标读取变化项、缺口和候选链；上下文压缩后可使用 `--refresh` 恢复当前问题的完整视图。

## 仓库内容

```text
webounty/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── assets/
│   ├── icon.svg
│   └── record-example.json
├── references/
│   ├── claude-code.md
│   ├── storage.md
│   ├── retrieval.md
│   ├── wiki-layout.md
│   ├── observation-comparison.md
│   ├── scoring.md
│   ├── wiki-knowledge.schema.json
│   ├── web-vulnhunt-LICENSE.txt
│   └── methods/
├── scripts/
├── tests/
├── THIRD_PARTY_NOTICES.md
├── README.md
└── LICENSE
```

## 安装与使用

### 安装

将完整的 `webounty` 文件夹放到 Claude Code 的个人或项目技能目录：

```text
~/.claude/skills/webounty/
```

或：

```text
.claude/skills/webounty/
```

确保 `SKILL.md` 直接位于 `webounty/` 目录下。

依赖：

- Python 3.10+，核心功能仅使用标准库。
- Node.js 18+，仅 CVSS 3.1 计算器需要。

### 开始

在当前研究项目中启用 `Webounty` 后，由宿主按照 `SKILL.md` 的工作循环调用脚本。

会话资料默认保存在当前项目：

```text
.webounty/<session-id>/
```

需要手动使用时，可直接查看：

```bash
python3 scripts/session.py --help
```

### 常用命令

| 命令 | 用途 |
|---|---|
| `start` | 创建或复用会话 |
| `record` | 写入观察、记录和 Wiki |
| `context` | 读取当前知识、变化和缺口 |
| `discover` | 检索能力、前提和候选连接 |
| `read` | 按 ID 回取记录、页面或证据 |
| `compare` | 对比两份已保存观察 |
| `methods` | 按需读取验证方法 |
| `finish` | 结束本轮会话 |

评分工具：

```bash
node scripts/cvss31-calculator.js \
  --json 'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N'
```

CVSS 仅用于严重性评估，不替代漏洞成立所需的证据验证。

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

本仓库中的 Skill、脚本、方法、配置和文档仅用于合法授权的安全研究、教育、代码审计和测试环境。

使用者必须自行确认其拥有充分授权，并对目标范围、测试方法、工具配置、数据处理、证据保存、漏洞提交和后续影响承担全部责任。仓库作者不对任何未经授权的使用、错误配置、数据丢失、业务中断、法律责任、第三方索赔或其他直接或间接损失承担责任。

本仓库不保证能够发现漏洞，也不保证检索结果、候选链、工具输出、评分或漏洞结论始终正确、完整或适用于特定环境。检索分数、`ready`、`compatible` 与 `coverage.complete` 均不构成漏洞成立证明，任何结论都应独立验证。

本 Skill 不安装 hook、不修改客户端配置，脚本也不扫描网络或执行攻击。异常关窗或进程被终止时，不保证立即清理 `.webounty/` 下的会话资料。

## License

本仓库中作者有权许可的原创和修改内容采用 [MIT License](LICENSE)。
