<p align="center"><strong>Webounty</strong> 是一个在本地会话中运行的漏洞研究 Skill，用项目内的 Wiki 和原始证据，把授权范围内的漏洞链验证持续推进下去。
<p align="center">
  <img src="https://github.com/do-whilefor/Webounty/blob/main/assets/icon.svg" alt="Webounty" width="15%" />
</p>
</br>如果你在 Claude Code 里使用，把 <code>webounty/</code> 放进技能目录即可，见 <a href="#安装并启用-webounty">Quickstart</a>。
</br>如果你在 Codex 或其他宿主里使用，见 <a href="./references/claude-code.md">宿主接入</a>，脚本工作流保持一致。
</br>如果你想知道它解决什么问题、怎么工作，直接读 <a href="./SKILL.md">SKILL.md</a>。</p>

---

## Quickstart

### 安装并启用 Webounty

克隆到 Claude Code 的个人技能目录：

```shell
git clone https://github.com/do-whilefor/Webounty.git ~/.claude/skills/webounty
```

只在单个项目里启用时，克隆到项目技能目录：

```shell
git clone https://github.com/do-whilefor/Webounty.git .claude/skills/webounty
```

<details>
<summary>也可以用 Release 压缩包或仓库快照手动放置：把完整的 <code>webounty/</code> 目录放进技能目录，确保 <code>SKILL.md</code> 直接位于该目录内，不要多套一层。</summary>

更新时整体替换技能目录；项目里正在进行的 `.webounty/` 会话资料不属于技能包，保持不动。

依赖：

- Python 3.10+，核心脚本只用标准库，不需要 pip 包、向量数据库或独立模型 API。
- Node.js 18+，仅 CVSS 3.1 计算器需要。
- 系统用 `python` 命令时，确认它是 Python 3 后再替换示例里的 `python3`。

</details>

### 使用

在 Claude Code 输入 `/webounty` 并说明研究目标，也可以由 Claude 按技能描述自动加载。

会话资料写在当前项目下，同名项目和会话重复 `start` 会复用同一工作区：

```text
.webounty/<会话标识>/
```

技能本身只读取本地资料：不扫描网络、不安装 hook、不修改客户端配置、不主动发起请求。实际取证沿用宿主已有的工具和当前任务的授权。

需要手动调用脚本时：

```shell
python3 scripts/session.py --help
```

## Docs

- [**SKILL.md**](./SKILL.md) — 工作循环、命令入口与使用约束
- [**宿主接入**](./references/claude-code.md) — 安装、依赖、会话语义、本地检查与基准脚本
- [**存储与提交格式**](./references/storage.md)
- [**检索与链路组合**](./references/retrieval.md)
- [**问题级检索**](./references/question-retrieval.md)
- [**Wiki 组织**](./references/wiki-layout.md)
- [**观察对照**](./references/observation-comparison.md)
- [**CVSS 评分**](./references/scoring.md)
- [**验证方法库**](./references/methods/)
- [**记录示例**](./assets/record-example.json) — 虚构数据，不是目标证据

## 使用边界

仅用于合法授权的安全研究：明确授权的漏洞赏金与 SRC 范围、用户自有系统与测试环境、CTF 与靶场、经授权的代码审计与漏洞复现。

<details>
<summary>展开禁止事项</summary>

- 未经授权扫描、探测、入侵或利用第三方系统。
- DoS、DDoS、持续压测、资源耗尽或影响业务可用性的行为。
- 删除、破坏或不可逆修改真实业务数据。
- 建立 WebShell、后门、计划任务、启动项、反向 Shell 或其他持久化访问。
- 横向移动、攻击无关资产、窃取凭证、钓鱼、撞库或社会工程。
- 对非测试账号执行真实支付、退款、权限变更、批量通知或其他高影响业务操作。
- 违反适用法律、平台规则、漏洞赏金政策、SRC 规则或目标方明确限制的行为。

</details>

## 免责声明

Skill、脚本、方法和文档仅用于合法授权的安全研究、教育、代码审计和测试环境。

<details>
<summary>展开完整免责声明</summary>

使用者必须自行确认拥有充分授权，并对目标范围、测试方法、工具配置、数据处理、证据保存、漏洞提交和后续影响承担全部责任。仓库作者不对任何未经授权的使用、错误配置、数据丢失、业务中断、法律责任、第三方索赔或其他直接或间接损失承担责任。

本仓库不保证能够发现漏洞，也不保证检索结果、候选链、工具输出、评分或漏洞结论始终正确、完整或适用于特定环境。检索分数、`ready`、`compatible` 与 `coverage.complete` 均不构成漏洞成立证明，任何结论都应独立验证。

本 Skill 不安装 hook、不修改客户端配置，脚本也不扫描网络或执行攻击。异常关窗或进程被终止时，不保证立即清理 `.webounty/` 下的会话资料。

</details>

本仓库中作者有权许可的原创和修改内容采用 [MIT License](LICENSE)。
