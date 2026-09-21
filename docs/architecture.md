# 架构与当前实现边界

## 分层与单向流

```text
Godot（场景 / 输入 / 动画 / UI）
  -- REST JSON --> FastAPI API（鉴权边界 / schema / 错误映射 / trace_id）
  --> 对话编排应用层（persona、记忆、关系、安全、预算、重试/熔断、可观测性）
  --> NPC 领域层（版本化 persona、结构化事实、关系规则与 provider-neutral 契约）
  --> 适配层（业务/控制/可观测 SQLite、DeepSeek client、fake provider、脱敏报告）
```

Godot 不直连 LLM 或数据库；领域层不直接依赖 FastAPI、Godot、具体 LLM SDK 或 Qdrant。外部模型返回与工具参数一律作为不可信输入处理。

## F-009 当前模块

| 模块 | 职责 | 不负责 |
| --- | --- | --- |
| `game/` | 最小场景、固定 NPC 选择、对话 UI、只读关系快照与旧回调抑制 | 角色推理、持久化、好感度规则 |
| `backend/api/` | HTTP schema、错误码、关联 trace_id | 业务策略与 SQL 细节 |
| `backend/application/` | 显式记住/忘记、双元长期检索、三元 scope 短期记忆、确定性关系、安全/限流/预算、成本归因、重试/熔断、可观测事件、统一 UTF-8 预算、并发与幂等 | SQL 细节、HTTP、Godot 或具体 SDK |
| `backend/domain/` | Nia/Ivo/Rhea 固定版本 persona registry、结构化长期事实/scope/status、受限关系分类/状态机、provider-neutral DTO/错误和严格 loader | 网络、ORM、LLM SDK |
| `backend/infrastructure/llm/` | fake provider 与隔离 DeepSeek adapter、SDK 错误分类和 usage 转换 | 业务决策、持久化或原始 provider 对象外泄 |
| `backend/infrastructure/persistence/` | 长期事实、关系状态和验收计量的标准库 SQLite repository，以及把同步 SQLite 移出事件循环的异步执行边界 | 模型判断、完整聊天备份、向量检索或公开 API |
| `backend/infrastructure/control/` | 安全、预算、成本、provider permit、重试与熔断的独立控制 SQLite 和追加迁移 | 对话正文、persona 或 UI 状态 |
| `backend/infrastructure/observability/` | 脱敏事件、延迟、usage、成本和结果的紧凑 SQLite 存储及报告数据源 | 原始 prompt、玩家消息、模型回复、密钥或 reasoning |
| `scripts/` | 统一 quality、离线评估、报告和冻结的 F-009 QA/性能适配 | 生产业务状态或额外授权 |

当前 API 提供 `GET /api/v1/health`、冻结的 `POST /api/v1/dialogue`，以及只读 `GET /api/v1/relationships/{player_id}/{npc_id}?request_id=<optional UUID>`。公开 Dialogue v1 和其 JSON Schema 不变。persona registry 只允许 `neon_guide / Nia`、`signal_archivist / Ivo`、`night_courier / Rhea`；未知或有损规范化的 `npc_id` 在 provider 和持久化前 fail-closed。只有已校验且 `completed` 的同次 provider completion 才传递其受限 `category + confidence` 内部建议；确定性引擎和业务 SQLite 事务拥有分值、冷却、事件与回放权，degraded/失败/取消不写关系。Godot 只读取快照，不持有 API key 或直连 provider/数据库。启用 provider 时，composition 在受限项目 `data/` 范围内分别装配业务、控制与可观测 repository；自动化始终使用 pytest 或短生命周期 loopback 临时数据库。embedding、Qdrant、工具调用和 NPC 自主对话仍不存在。

F-009 在 provider dispatch 前执行输入安全、频率、预算、permit 与 circuit 状态检查；只有获得确定性许可的请求才能进入 adapter。结算、失败分类、重试结果和脱敏事件分别进入控制与可观测 repository。三个 SQLite 职责域保持分离，但都由 application protocol 驱动，API 和领域层不直接执行 SQL。

## 工程门禁边界

```text
开发者 / GitHub Actions
  --> uv sync --locked --all-groups
  --> scripts/quality.py
      --> Git ignore / 敏感信息预检
      --> lock freshness --> ruff --> mypy --> schema drift
      --> Godot import/unit --> loopback connectivity/recovery --> pytest
      --> Git ignore / 敏感信息复检
```

本地与 CI 复用同一入口。安全预检在其他工具前执行，同时检查 worktree 与 stage-0 Git index；扫描结果只输出路径、行号和规则。集成 harness 只占用 `127.0.0.1:8000`：启动真实 FastAPI 验证 connected，并以测试专用 loopback fixture 验证 503、非法 JSON、延迟、手动 retry 和端口回收，不向生产 API 增加故障路由。CI 仅有 `contents: read`，不读取 secrets、不启动 service container、不调用业务外部系统；bootstrap 从公开发行源下载经 SHA-256 固定的 Godot 4.7.2 Linux 包。F-009 最终 PR HEAD CI 和合并后 `main` CI 均通过，当前交付基线为 `75171492070bddddffef58cc4f0fe9552d40bb77`。

## 状态与一致性

- 工作记忆作用域固定为完整 `(player_id, npc_id, conversation_id)`；长期事实作用域固定为 `(player_id, npc_id)`，允许同玩家/NPC 跨 conversation 及服务重启召回，禁止跨 player/NPC 泄漏。
- F-004 在当前进程内为每个 scope 保留最近 6 个成功完成的完整 user/assistant 回合；最多 128 个活动会话、idle TTL 1800 秒、过期优先和确定性 LRU；在途 session 不得驱逐，无法安全回收时返回可重试 503。
- 上下文预算按 `64 + system + untrusted_long_term_facts + history + current + 256 <= 8192` 估算，每条消息额外 16 单位加 UTF-8 字节；长期事实最多 2048。这不是 provider 官方 token 数。与当前 `npc_id` 严格对应的唯一 persona system 和当前 user 不裁剪；长期事实只作为不可信 user 数据整条加入，历史只按完整回合从新到旧选择、从旧到新发送。
- 同 scope 请求串行，最多等待 2 秒；跨 scope 可并发但 provider 全局上限 2。仅 `completed` 成功请求提交完整回合；degraded、timeout、无效响应、失败、取消、孤儿和晚到结果均不写入。
- 每次 HTTP 尝试生成独立 `trace_id`；客户端 `request_id` 标识逻辑请求。进程内幂等 TTL 10 分钟、最多 256 项，同 ID 同 payload 合并/复用，同 ID 不同 payload 返回冲突。
- 进程重启后对话幂等缓存和短期工作记忆均丢失；显式批准的低敏感长期事实与记住/忘记 operation 通过业务 SQLite 持久化，并可跨进程恢复。provider dispatch 的安全、预算、permit、重试/熔断状态由控制 SQLite 原子维护；脱敏事件由可观测 SQLite 保存。所有运行数据库均须 Git 忽略，自动化只创建 pytest 或短生命周期 loopback 临时数据库。

## 失败与通信

首版 REST 足够。当前诊断场景加载后自动发起一次健康请求，同一时刻只允许一个在途请求；3 秒 timeout 或失败后仅允许用户手动 Retry。严格匹配健康 JSON 才进入 connected；非 2xx、无效/多余/缺失字段及非 timeout 传输失败进入 unavailable；`RESULT_TIMEOUT` 进入 timeout。Windows 4.7.2 下后端未监听的真实行为实测为 timeout，503 fixture 明确覆盖 unavailable。

仅当需要 token 级流式回复、服务器主动推送、多人同时状态广播或高频世界同步时，评估 WebSocket/SSE；不能因“实时”标签提前引入。

模型调用继续采用并发上限 2、provider timeout 12 秒、Godot timeout 15 秒、non-thinking、non-stream 和 SDK 零自动 retry。只有用户手动 Retry 可以再次发起逻辑相同的失败请求；内容过滤可返回确定性 local fallback 且不写记忆，当前消息超预算返回 422，内部最小预算/会话容量/scope 等待失败返回可重试 503，provider 无效响应/超时维持 502/504。审计只记录 allowlist 元数据、长度、usage、延迟和费用估算，不记录密钥、原始 prompt、历史内容、玩家消息、模型回复或 provider body。
