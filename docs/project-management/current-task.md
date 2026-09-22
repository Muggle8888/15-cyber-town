# 当前任务：F-012 街区探索与情境对话

更新时间：2026-09-22

## 当前状态面板

| 判断项 | 当前唯一口径 |
| --- | --- |
| 当前任务卡 | `F-012 街区探索与情境对话` |
| 路线图任务状态 | `ACTIVE` |
| 当前所在步骤 | Step 5：三层验收与本地质量均通过，等待 Git 交付授权 |
| 当前业务闭环 | 探索固定地标 → 主动记下发现 → 接近对应 NPC → 生成可见草稿 → 玩家编辑并发送 → NPC 结合角色回应 |
| 当前执行状态 | `READY_FOR_GIT_DELIVERY` |
| 已完成到哪里 | 视觉、完整实现、Godot/Fake/统一质量、用户试玩和隔离真实模型 UAT 均已通过 |
| 精确阻塞点 | Git 交付尚未获得独立授权，F-012 不能提交、推送、创建 PR、合并或归档 |
| 本阶段不执行 | Git 提交/推送/PR/合并、外部素材或资源删除 |
| 唯一最小下一项 | 用户决定是否授权 F-012 的精确审查、提交、推送、PR、CI、合并与归档 |
| 下一动作类型 | `AUTHORIZE_OR_DEFER_GIT_DELIVERY` |
| 授权状态 | 本地实现、三层验收和真实模型 UAT 已授权并完成；Git 交付未授权 |
| 环境与副作用 | 真实 UAT 已创建并保留隔离数据根与账本；8000/18010 均空闲，未删除任何资源 |

## 当前执行合同

```yaml
task_id: F-012
task_name: 街区探索与情境对话
roadmap_status: ACTIVE
step: "Step 5 documentation and Git delivery authorization"
execution_status: READY_FOR_GIT_DELIVERY
current_goal: 让玩家的街区探索以可见、可编辑的情境文本自然进入对应NPC对话
completed_checkpoint: "visual, implementation, Godot, Fake, full quality, user gameplay and real-provider UAT passed"
blocked_at: GIT_DELIVERY_AUTHORIZATION
next_action: 用户授权或推迟F-012 Git交付与归档
next_action_type: AUTHORIZE_OR_DEFER_GIT_DELIVERY
authorization:
  planning_and_task_card: authorized_by_user_2026_09_22
  local_code_changes: AUTHORIZED_STEP_0_TO_4_BY_USER_2026_09_22
  local_tests: AUTHORIZED_OFFLINE_AND_FAKE_STEP_0_TO_4_BY_USER_2026_09_22
  visual_generation_or_capture: AUTHORIZED_GODOT_SCREENSHOTS_BY_USER_2026_09_22
  external_assets: NOT_AUTHORIZED
  real_provider_calls: AUTHORIZED_AND_CONSUMED_8_CALLS_BY_USER_2026_09_22
  git_branch_commit_push_pr_merge: NOT_AUTHORIZED
usage:
  local_fix_rounds: "1 Step 0 prompt-refresh correction; no Step 1-4 repair rounds"
  formal_acceptance_runs: "town targeted 2 passed; Fake town loopback 2 passed; full quality 2 passed; user UAT passed; real-provider UAT passed"
  real_provider_calls: "8 / hard cap 8; 6 checks passed; 2 semantic retries; 1917 micro-USD; pending 0"
branch:
  current: feat/f-012-contextual-exploration
  head_at_planning: 2bf190d5a7656bbfb2c2ae8415c67860b60cd5c5
  planned_feature_branch: feat/f-012-contextual-exploration
  branch_created: true
planned_resources:
  design_spec: E:/Agent/comprehensive-cases/15-cyber-town/docs/design/contextual-exploration/design-spec.md
  step_0_screenshot: E:/Agent/comprehensive-cases/15-cyber-town/docs/design/contextual-exploration/godot-observation-normal-v1.png
  final_observation_screenshot: E:/Agent/comprehensive-cases/15-cyber-town/docs/design/contextual-exploration/godot-exploration-observation-v2.png
  context_menu_screenshot: E:/Agent/comprehensive-cases/15-cyber-town/docs/design/contextual-exploration/godot-context-topic-menu-v1.png
  uat_data: E:/Agent/comprehensive-cases/15-cyber-town/data/uat/f-012
  acceptance_ledger: E:/Agent/comprehensive-cases/15-cyber-town/data/acceptance-ledgers/f-012.sqlite3
  status: "design artifacts and UAT resources created and retained; no resource deletion authorized"
```

## 用户目标与业务价值

玩家在当前小街区移动时，可以检查三处与 Nia、Ivo、Rhea 身份相关的地标，主动记下一个发现，再把这个真实发生在场景中的观察带进对应 NPC 的对话。完成后，探索不再只是从一个 NPC 走到另一个 NPC；玩家的移动和观察会形成下一次对话的明确上下文。

Agent 在本任务中仍负责角色化理解与回应。三名 NPC 是共享同一编排和模型客户端、但拥有独立 Persona、会话、长期事实和关系状态的三个领域实例；它们不是相互自治协作的多 Agent。地标、发现状态和 NPC 映射由 Godot 确定性控制，模型不能解锁内容、修改地图或写入隐藏世界状态。

## 玩家体验契约

### 三处固定地标

| 地标 | 对应 NPC | 固定观察 | 讨论草稿 |
| --- | --- | --- | --- |
| 暮光导览牌 | Nia | 导览牌标出一条只在傍晚亮起的夜市灯带 | `我在暮光导览牌上看到傍晚夜市灯带的标记，你会怎么带我逛？` |
| 信号校准台 | Ivo | 校准记录中反复出现同一段旧广播编号 | `我在信号校准台看到一段重复的旧广播编号，你知道它的来历吗？` |
| 雨棚投递板 | Rhea | 投递板上留有一条褪色的雨夜路线标记 | `我在雨棚投递板看到一条褪色的雨夜路线标记，它现在还在使用吗？` |

所有内容都是作者编写的固定文本，不由模型生成，不代表任务、谜题或隐藏奖励。

### 交互规则

- 玩家进入范围时只显示一个最近目标提示：NPC 显示“`E` 与 Nia 交谈”，地标显示“`E` 查看暮光导览牌”。
- 最近目标在距离相同时优先 NPC；地图布局应避免必须依赖平局规则才能选中地标。
- 检查地标后打开紧凑观察卡并暂停移动；卡片显示地标名称、固定观察、对应 NPC、“记下话题”和“关闭”。
- 只有玩家点击“记下话题”才保存本次游戏启动期发现；关闭或 `Esc` 不保存。
- 已记下的地标可以再次查看，但不得重复创建发现或重复提示成功。
- 对应 NPC 的“话题与记忆”菜单新增“讨论街区发现”；未记下发现时不显示该入口。
- 选择“讨论街区发现”只把冻结的自然语言草稿填入输入框，不自动发送。玩家可编辑，最终网络载荷与发送时输入框可见文本完全一致。
- 发现按地标和对应 NPC 隔离；Nia 的发现不得出现在 Ivo 或 Rhea 菜单中。
- 发现只存在于当前游戏启动期间；重启游戏后清空。它不是长期记忆，玩家仍可使用 F-011 的显式记忆动作保存允许的长期偏好。
- 后端不可用时仍可探索、查看和记下发现；发送对话继续使用现有不可用提示与手动重试。

## UI 与视觉门禁

- 复用当前 640×360 暖色傍晚像素画面、中文字体、边框、按钮和音效；不引入外部美术资源。
- Step 0 先形成一张真实 Godot 正常状态截图：玩家站在暮光导览牌旁，最近目标提示和观察卡同时可见。
- 观察卡不得遮住地标名称、主要角色身份或顶部连接状态；正文在 640×360 下无需滚动即可读完。
- 用户批准首个观察卡正常状态后，才实现三地标完整交互、已记下状态和 NPC 菜单入口。
- 真实页面完成后再次提供同尺寸截图并取得视觉确认；截图不能替代实际试玩。

## 后端与 Agent 边界

- 保持 `POST /api/v1/dialogue`、关系 GET 和公开 Schema 不变。
- 不新增世界状态 API、任务 API、工具调用、WebSocket、SSE 或隐藏 system context。
- 情境信息以玩家看得见、可以编辑的普通对话文本进入既有 Dialogue v1；不得额外附加玩家不可见的地标描述。
- 继续复用现有 Persona、短期会话、长期事实、关系阶段、安全、预算、重试、熔断和可观测性边界。
- 普通情境对话可以参与既有短期会话和关系规则；检查地标或记下话题本身为纯本地操作，不调用 Provider、不改变关系、不写长期记忆。

## 明确非目标

- 不加入任务、奖励、物品、成就、谜题完成状态或收集进度条。
- 不加入动态生成事件、随机地标文本、昼夜变化、室内、多地图或扩大城镇。
- 不加入 NPC 自主移动、寻路、NPC 间对话或多 Agent 协作。
- 不保存跨重启探索记录，不新增账号、存档格式或客户端数据库。
- 不让模型决定地标是否可用、玩家是否完成事件或地图如何变化。
- 不下载新素材、不购买资源、不生成新概念图；只复用现有画面组件完成首版。

## 验收标准

1. 玩家可分别找到三处地标，且同一时刻只看到一个最近交互目标。
2. 打开观察卡时玩家停止移动；关闭后恢复，且取消不会记录发现。
3. 点击“记下话题”后，只有对应 NPC 菜单出现“讨论街区发现”。
4. 选择讨论入口只填入可编辑草稿，未自动发送，实际请求内容等于发送时可见文本。
5. 三个地标、三个 NPC、会话历史、重试状态与发现状态均不串联。
6. 检查和记录发现不访问网络、不调用 Provider、不改变关系或长期记忆。
7. 后端不可用时探索仍工作；恢复连接后可发送已记下的情境草稿。
8. 游戏重启后发现清空；既有长期记忆和关系生命周期不受影响。
9. Fake 回环、用户视觉与手感验收、另行授权的真实模型情境对话 UAT 分别记录，不互相替代。

## 测试与验收矩阵

| 风险/行为 | 最低验证 | 失败证明 |
| --- | --- | --- |
| 最近目标选择 | Godot 单元/场景测试 | 同时显示多个提示、超范围目标或平局不稳定时失败 |
| 观察卡移动锁定 | Godot 场景测试 | 打开仍可移动、关闭后未恢复或请求期错误切换时失败 |
| 发现与 NPC 映射 | Godot 单元测试 | 未发现即出现入口、跨 NPC 泄漏或重复记录时失败 |
| 可见文本即载荷 | Godot 客户端测试、Fake HTTP 回环 | 存在隐藏附加文本、自动发送或重试载荷漂移时失败 |
| 纯本地观察 | Fake Provider 计数与关系快照 | 检查/记下动作产生 Provider 调用或关系变化时失败 |
| 生命周期 | Godot 重建与后端重启组合测试 | 客户端重启后发现未清空或后端状态被误删时失败 |
| 回归 | 既有 town、dialogue、connectivity 与统一 quality | F-010/F-011 任一核心流程退化时失败 |
| 玩家体验 | 640×360 实机截图与用户试玩 | 文本不可读、遮挡严重、目标选择困惑或流程无法理解时失败 |
| 真实语义 | 另行授权的隔离真实模型 UAT | NPC 不理解可见观察、Persona/关系语气失真或跨 NPC 混淆时失败 |

## 文件影响范围

预计允许修改：

- `game/scenes/`：新增或复用地标可交互场景；不扩大地图边界。
- `game/scripts/town/`：地标契约、最近交互目标、启动期发现状态和观察卡控制。
- `game/scripts/dialogue/`：仅在确有需要时增加安全的草稿填入接口，不改变网络 Schema。
- `game/tests/run_town_tests.gd` 及相关 Godot/Fake 回环测试。
- `docs/design/contextual-exploration/`：获批设计规格与实机截图。
- 当前项目管理、架构、Agent 与测试文档中受实际实现影响的部分。

明确不修改：

- `contracts/v1/` 和公开 API Schema。
- Persona 文件、关系规则、长期记忆白名单与数据库迁移。
- Provider 价格、预算、重试、熔断和生产配置。
- 地图尺寸、正式资产包、字体许可证和音频来源。

## 资源、授权与验收边界

- 用户已批准任务卡、功能分支及 Step 0—4 本地实现、Godot 截图与离线/Fake 测试。
- 功能分支为 `feat/f-012-contextual-exploration`；当前不授权提交、推送、PR 或合并。
- 首个视觉状态必须由真实 Godot 运行截图产生，并在用户确认后才进入 Step 1—4 的完整交互实现。
- Step 0 受版本控制的设计产物为 `docs/design/contextual-exploration/design-spec.md` 与 `godot-observation-normal-v1.png`；内容仅为项目 UI 规范和渲染画面，不含密钥或运行数据，作为 F-012 设计证据长期保留，Codex 不删除。
- Fake/离线验证不得读取 `.env` 或调用真实模型。
- 真实模型 UAT 建议为 6 次计划调用、最多 2 次失败重试、8 次硬上限与 USD 0.05 费用上限；执行前重新核验模型、官方价格、配置和预算，并取得单独授权。
- 计划隔离资源为 `data/uat/f-012` 与 `data/acceptance-ledgers/f-012.sqlite3`；创建前必须再次登记和核验路径，当前均未创建。
- commit、push、PR、合并、资源处置和下一任务均需独立授权。

## 风险与回滚

- 主要产品风险：观察卡与话题菜单叠加后 640×360 信息密度过高。通过 Step 0 单状态视觉门禁提前验证。
- 主要交互风险：玩家靠近 NPC 与地标时目标跳动。通过固定距离、稳定平局规则、地图摆位与场景测试控制。
- 主要 Agent 风险：为了“世界感知”引入隐藏上下文，导致玩家不知道模型收到了什么。本任务禁止隐藏注入，只发送输入框可见文本。
- 回滚方式：移除地标交互和启动期发现状态，恢复现有最近 NPC 选择和 F-011 话题菜单；后端和数据库无需迁移回滚。

## 工作量与完成定义

预计工作量为 **5～8 个工作日**，不含用户等待、真实模型授权等待或 Git 交付等待。

- [x] 用户批准本任务卡和产品范围。
- [x] 观察卡设计状态与真实 Godot 截图分别通过用户视觉门禁。
- [x] 三地标探索、记录与对应 NPC 情境草稿闭环可实际试玩。
- [x] 负向、隔离、重试、生命周期和回归验证通过。
- [x] 用户完成约 10 分钟功能与手感验收。
- [x] 另行授权的真实模型 UAT 通过。
- [x] 统一质量与敏感信息门禁通过。
- [ ] Git 交付另行授权并完成后，任务卡才可归档。
