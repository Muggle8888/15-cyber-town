# Cyber Town

一个用于系统学习 Agent 工程的 AI NPC 赛博小镇项目。目标是在 Godot 场景中让玩家与具备角色、记忆和可审计行为边界的 NPC 交互。

当前任务与阶段见 [current-task.md](docs/project-management/current-task.md)，交付历史见 [任务档案](docs/archive/task-cards/)；此处不重复维护测试数和完成状态。项目规则与文档权威入口见 [AGENTS.md](AGENTS.md) 和 [docs/README.md](docs/README.md)。当前任务的 fake-only、真实 `.env`/模型限制与运行资源授权必须先核对，以下常规命令不自动构成当前 Step 的运行授权。

当前统一验证命令：`uv run --frozen python scripts/quality.py`。它执行 Git ignore/敏感信息预检、lock、ruff、mypy、schema、Godot 导入与单测、9 个 F-002 健康 loopback、10 个对话 fake loopback、诊断页与城镇各 1 个三 NPC loopback、pytest 和最终策略复检；对话场景包含连续多轮与失败后的手动 Retry 恢复。每个质量子进程强制禁用 `.env`、剔除继承的 provider key 并固定 `LLM_PROVIDER=disabled`；对话集成仅使用本地 FastAPI 和 fake provider。需要 Godot 4.7.2，可通过 `CYBER_TOWN_GODOT` 指向 executable；Windows 默认也会检查本项目批准的便携路径。

## 当前产品能力与架构

Cyber Town 当前提供三名固定 NPC（Nia、Ivo、Rhea）的本地玩家对话闭环。Godot 主入口是一处可移动、碰撞、接近交互的暖色傍晚街区，并按 NPC 保存本次启动内的会话与六回合记录；旧连接页和独立对话页继续作为诊断入口。FastAPI 负责严格 API、请求编排和错误映射；应用层组合 persona、三元 scope 短期记忆、双元 scope 长期事实、确定性关系引擎、安全/限流/预算、重试/熔断和可观测性；DeepSeek 或 FakeProvider 只位于可替换适配器之后。

模型回复和内部建议始终是不可信输入。记忆写入、关系分值、预算、权限、状态迁移和持久化由确定性服务及 SQLite 事务控制，模型不能直接修改游戏状态。业务状态、控制状态和可观测事件分别通过受限 SQLite repository 管理；自动化只使用隔离临时数据库，默认 provider 为 disabled。完整设计见 [架构](docs/architecture.md)、[Agent 边界](docs/agent-design.md)、[记忆设计](docs/memory-design.md)和[技术栈](docs/tech-stack.md)。

## 本地验证

项目要求稳定 Python 3.12.10 和 `uv 0.6.14`。在仓库根目录执行：

```powershell
uv sync --locked --all-groups
uv run --frozen python scripts/quality.py
```

## 本地诊断场景

无需真实模型的基础可玩演示可使用独立端口 `18010` 启动；关闭 Godot 窗口后 fake 服务会退出并释放端口：

```powershell
.venv\Scripts\python.exe -B scripts\dialogue_integration.py --godot E:\Agent.tools\godot\4.7.2\Godot_v4.7.2-stable_win64_console.exe --town-demo
```

该模式只验证移动、交互、会话隔离、关系反馈和界面手感；固定离线回复不能替代真实模型的 Persona、记忆与关系体验验收。

先在仓库根目录启动后端：

```powershell
uv run --frozen python -m cyber_town.api
```

再开一个终端运行 Godot 主场景：

```powershell
E:\Agent.tools\godot\4.7.2\Godot_v4.7.2-stable_win64_console.exe --path game
```

默认产品场景请求 `GET http://127.0.0.1:8000/api/v1/health`，timeout 为 3 秒；连接失败不阻止城镇探索，玩家可从顶部状态条手动重试。接近 NPC 后按 `E` 打开对话，`Ctrl+Enter` 发送，`Esc` 关闭；原生桌面客户端不需要 CORS。

## CI 边界

`.github/workflows/quality.yml` 在 `main` push、pull request 和人工触发时运行同一入口。workflow 只有 `contents: read` 权限，不引用 secrets、不持久化 checkout 凭证、不启动服务容器，也不访问真实 LLM、正式数据库或生产服务；SQLite 测试只使用隔离临时数据库。runner 从公开发行源取得 action、uv、Python、锁定依赖和经 SHA-256 固定的 Godot 4.7.2 Standard Linux 包；所有集成流量仅在 runner 的 `127.0.0.1:8000` 内发生。F-009 最终交付由 PR #13 合并为 `75171492070bddddffef58cc4f0fe9552d40bb77`，最终 PR CI 与合并后 `main` CI 均通过；详细运行事实见 [evidence.md](docs/project-management/evidence.md)。

## 本地对话场景

真实 provider 默认关闭，统一自动化与 CI 不读取真实 `.env`、不继承 provider key、不调用真实模型。只有取得明确外部调用授权后，才能在当前 PowerShell 进程启用本地 `.env` 中已被 Git 忽略的配置：

```powershell
$env:LLM_PROVIDER = 'deepseek'
[Environment]::SetEnvironmentVariable('ALL_PROXY', $null, 'Process')
uv run --frozen python -m cyber_town.api
```

清除当前进程的 `ALL_PROXY` 只用于规避本机 SOCKS 代理需要额外 `socksio` 的限制，不修改系统代理；既有 HTTP/HTTPS 代理保持不变。不要输出 `.env`、API key、玩家消息或模型回复。每个真实请求可能产生费用，SDK 不自动重试。

后端启动后，在另一个终端打开独立对话场景：

```powershell
& 'E:\Agent.tools\godot\4.7.2\Godot_v4.7.2-stable_win64_console.exe' --path game --scene res://scenes/dialogue.tscn
```

短期记忆按 `(player_id, npc_id, conversation_id)` 最多保留最近 6 个成功完整回合，最多 128 个活动会话，空闲 TTL 为 1800 秒；该层随服务重启丢失。长期层只允许 `game_alias`、`preferred_language`、`reply_style`、`favorite_cyber_town_topic` 四类低敏感事实，按 `(player_id, npc_id)` 使用标准库 SQLite 保留、更新、过期和遗忘。三名 NPC 的 persona、短期记忆、长期事实和关系状态严格隔离；F-009 进一步在 provider dispatch 前执行安全、预算与 permit 控制，并把成本、重试、熔断和脱敏可观测事件写入独立控制/可观测 repository。

启用 provider 的常规启动会装配受限项目 `data/` 路径，但不会自动获得真实调用、验收预算或外部访问授权。历史真实评估额度已经消费；任何新的真实 provider 调用都必须建立新的明确授权和独立计量边界。

上下文上限 8192 为 UTF-8 字节与固定开销的工程估算，不是 provider 官方 token 数；长期事实最多 2048，固定预留 256 回复单位。当前所选 NPC 的唯一 persona system 之后，只注入标记为不可信的事实及完整短期回合。没有可用记忆或已遗忘时返回确定性 `degraded / local-fallback`，不调用 provider、不计费。
