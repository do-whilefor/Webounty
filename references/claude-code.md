# Claude Code 接入

## 安装与依赖

把完整 webounty 文件夹放入个人目录 `~/.claude/skills/webounty/` 或项目目录 `.claude/skills/webounty/`，确保 SKILL.md 直接位于该目录，不要多套一层目录。

需要 Python 3.10+；仅 CVSS 需要 Node.js 18+。Python 只用标准库，无需 pip、向量数据库、独立模型 API 或固定 MCP。系统使用 python 命令时，确认它是 Python 3 后替换示例中的 python3。

在 Claude Code 输入 `/webounty` 并说明目标，也可由 Claude 按描述加载。`${CLAUDE_SKILL_DIR}` 和 `${CLAUDE_SESSION_ID}` 是技能正文替换变量，不是要求用户自己设置的 shell 环境变量。手动终端运行时填写实际目录和会话 ID。

其他宿主不支持替换变量时，显式填写技能目录，直接用 UUID 为本次研究生成一次随机会话 ID，无需询问用户或其他 Agent，后续沿用。此时仅支持脚本工作流，不承诺其他宿主自动接入。

## 会话语义

- start 在当前工作目录下创建 `.webounty/<会话ID的SHA-256>/`；`--project-root PATH` 可指定项目目录。路径以返回的 project_root/root 为准，不自动向上查找 Git 根目录。
- 同一项目和会话复用工作区；不同项目或不同会话分别隔离。session.json 登记项目归属，后续命令按 root 定位，切换工作目录不改变已创建会话的位置。
- 工作区属于整个研究会话，多个发现、Step、查询和子任务共享。start 重复调用不改写已有目标。
- 上下文压缩后保留 session_id/root/run_id；同一 context 游标加 --refresh 重发当前问题的完整视图，按 ID 补读当前 Goal 和活动 Step，再继续 discover。
- 目录已清理则原证据不可恢复；新会话不自动加载其他会话数据。
- finish 只删除归属匹配的会话子目录，项目、`.webounty/` 中其他会话和原始用户文件保持不变。需要导出时使用本会话目录之外的新目录。
- 本包不安装 hook 或修改客户端配置。普通回复结束不是会话结束；异常退出可能在项目下残留会话资料。
- 将来若接宿主自动清理，应处理真实会话结束。Claude Code 的 Stop 是一次回复结束，不能用于清理本轮知识。

## 命令

运行 `python3 scripts/session.py --help`，每个子命令也支持 --help。

| 命令 | 用途 |
|---|---|
| start | 创建或复用会话 |
| record | 提交观察、记录和 Wiki，并返回相关连接 |
| context | 默认返回紧凑知识与来源引用；--cursor 跨轮差量，--refresh 恢复当前视图 |
| discover | 全会话能力供需检索、候选路径、多输入组合与表达复核 |
| read | 按 ID 读取记录、页面、观察或工件及必要来源 |
| compare | 并列比较两份已存观察的条件、响应和业务字段 |
| methods | 读取固定方法，不创建会话 |
| audit | 检查存储和引用 |
| wiki audit / wiki knowledge | 检查语义块或读取知识视图 |
| finish | 明确收尾；可显式导出快照 |

辅助脚本不扫描网络或执行攻击。实际取证沿用宿主工具及当前任务授权。

## 本地检查

在技能目录运行：

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

测试使用虚构资料和临时目录，覆盖存储、检索、候选关系和评分算术，不代表所有真实目标上的链路发现效果。

固定检索案例可另运行 `python3 -B tests/evaluate_retrieval.py`。它报告 MRR、Recall@5 及词法检索耗时；统计对象是标注的记录/观察，完整上下文与 Wiki 来源闭包另由工作流测试覆盖。日常 context 耗时写入本会话 `logs/operations.jsonl` 的 elapsed_ms，不记原始查询内容。

record/context/discover/read 等命令的本地日志还记录 metrics.stages_ms 与 counts：状态读取、索引、来源验证、候选发现、装包、视图处理、变化影响及发布检查分别计时；CLI 的 response 日志补充最终序列化与实际输出字符数。计时不进入给模型的 JSON。阶段是包含子阶段的耗时，不能相加当总耗时。files_read、snapshot_files_read 分别统计 Corpus 初读与一致性复读；publish_evidence_files_read 统计发布中实际读取的不同证据文件，排除内存里的待写材料。

`python3 -B tests/benchmark_retrieval.py --sizes 100 300` 检查冷/热查询、单条更新、父目录改名、紧凑输出和游标恢复；报告本地耗时、索引更新数和 JSON 字符量，不把字符当作 Claude token。

`python3 -B tests/replay_session.py` 执行固定六轮回放，覆盖问句改写、新能力补齐前提、无关修改、目录改名、反证和压缩后恢复。它核对读取者已获资料加本轮增量是否覆盖人工标签中的必要引用、反证、候选与缺口，记录实际发起的原件补读；`--scripts-dir` 可指向旧版脚本做同案例对照。输出包含分阶段计时、读取与索引计数、额外返回比例和字符量。host_tokens 为 null：离线回放不测 Claude 理解、真实攻击实验或实际 token 消耗；新增影响解释可能增加变更轮输出。

官方依据：[Skills](https://code.claude.com/docs/en/skills)；[Hooks](https://code.claude.com/docs/en/hooks)。
