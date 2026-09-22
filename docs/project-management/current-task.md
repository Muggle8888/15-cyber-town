# 当前任务：F-014 暮光信号余波

更新时间：2026-09-22

## 当前状态面板

| 判断项 | 当前唯一口径 |
| --- | --- |
| 当前任务卡 | `F-014 暮光信号余波` |
| 路线图任务状态 | `ACTIVE` |
| 当前所在步骤 | Step 4：Git 交付准备 |
| 当前业务闭环 | 完成 F-013 → 听取三方方案 → 在信号校准台选择 → 场景持久变化 → 回访三人 |
| 当前执行状态 | `READY_FOR_GIT_DELIVERY` |
| 已完成到哪里 | 视觉、实现、自动/Fake、统一质量和真实模型 UAT 均已通过；用户主动跳过的人工试玩项仍明确未验证 |
| 精确阻塞点 | 无；真实模型 UAT 已通过，Git 交付授权已生效 |
| 唯一最小下一项 | 刷新远端引用并完成精确审查、提交、PR、CI、合并与归档 |
| 下一动作类型 | `GIT_DELIVERY` |
| 本阶段不执行 | 资源删除、外部素材、新地图、强推、分支删除、tag 或发布 |

## 当前执行合同

```yaml
task_id: F-014
task_name: 暮光信号余波
roadmap_status: ACTIVE
step: "Step 4 / Git delivery"
execution_status: READY_FOR_GIT_DELIVERY
current_goal: 在保留 UAT 资源和人工跳过项事实的前提下完成 F-014 Git 交付与归档
blocked_at: null
next_action: 刷新远端引用，精确审查并交付当前分支
next_action_type: GIT_DELIVERY
authorization:
  task_card_and_branch: AUTHORIZED_BY_USER_2026_09_22
  local_implementation_and_offline_fake_tests: AUTHORIZED_BY_USER_2026_09_22_AFTER_VISUAL_GATE
  visual_capture: AUTHORIZED_BY_USER_2026_09_22
  external_assets: NOT_AUTHORIZED
  real_provider_calls: AUTHORIZED_BY_USER_2026_09_22
  git_commit_push_pr_merge: AUTHORIZED_BY_USER_2026_09_22_AFTER_REAL_UAT_PASS
branch:
  base: main@193d97c1cb4844eb6e1f74efbe42f34368acc06f
  current: feat/f-014-twilight-signal-aftermath
planned_resources:
  design_spec: E:/Agent/comprehensive-cases/15-cyber-town/docs/design/twilight-signal-aftermath/design-spec.md
  step_0_screenshot: E:/Agent/comprehensive-cases/15-cyber-town/docs/design/twilight-signal-aftermath/godot-aftermath-choice-v1.png
  final_outcome_screenshot: E:/Agent/comprehensive-cases/15-cyber-town/docs/design/twilight-signal-aftermath/godot-aftermath-outcome-v1.png
  deterministic_test_save: E:/Agent/comprehensive-cases/15-cyber-town/game/.godot/f014-aftermath-state-test.json
  fake_test_save: E:/Agent/comprehensive-cases/15-cyber-town/game/.godot/f014-aftermath-state-fake.json
  user_uat_f013_save: E:/Agent/comprehensive-cases/15-cyber-town/game/.godot/f014-user-uat-f013-v1.json
  user_uat_aftermath_save: E:/Agent/comprehensive-cases/15-cyber-town/game/.godot/f014-user-uat-v1.json
  uat_data: E:/Agent/comprehensive-cases/15-cyber-town/data/uat/f-014
  acceptance_ledger: E:/Agent/comprehensive-cases/15-cyber-town/data/acceptance-ledgers/f-014.sqlite3
  current_step_created: design spec and 640x360 tracked Godot screenshot
  current_step_sensitive_content: none

validation:
  visual_gate: "USER_APPROVED_2026_09_22"
  choice_screenshot: "640x360, 89269 bytes, SHA256 AB030C9A75FE17BC229F053173E03B3D95CBD3F9C5DDC279A507F2BE85119F10"
  outcome_screenshot: "640x360, 67166 bytes, SHA256 04F246C7C1CEA9AD7A82A3EBDAC226FE477CFCBF00DECC13453EB24FFFD09BD5"
  godot_import: passed_via_unified_quality
  town_tests: TOWN_TESTS=PASS
  town_fake: "PASS, 13 Provider calls, deterministic choice adds zero calls"
  unified_quality: "PASS, pytest 2163 passed / 969 skipped / 0 failed"
  user_uat: "USER_ENDED_DEMO_AND_SKIPPED_REMAINING_CHECKS; save remained at nia_briefing; not counted as passed"
  real_provider_uat: "PASS, calls 6, checks 6, retries 0, prompt tokens 1807, completion tokens 807, cost 1513 micro-USD, pending 0"
```

## 玩家价值与完成定义

玩家完成“暮光失联信号”后，可以听取 Nia、Ivo、Rhea 对信号用途的不同意见，选择一种等价方案，并在场景和三名 NPC 的后续反应中看到跨重启保留的结果。Agent 负责角色化解释和回应；解锁、选择、视觉变化、存档与完成仍由 Godot 确定性控制。

三种结局固定为：

| 方案 ID | 提案者 | 玩家可见名称 | 持久化表现 |
| --- | --- | --- | --- |
| `night_market_guide` | Nia | 夜市导引 | 暖橙与粉色灯光，标牌显示“夜市导引” |
| `archive_monitor` | Ivo | 档案监听 | 蓝紫灯光，标牌显示“档案监听” |
| `rain_route_beacon` | Rhea | 雨夜信标 | 青绿色灯光，标牌显示“雨夜信标” |

三种结局均可完成，不存在隐藏最佳答案、关系门槛或选择本身造成的关系分数变化。

## 玩家体验契约

固定事件 ID 为 `twilight_signal_aftermath_v1`。七项进度为：Nia 开场、Ivo/Rhea 任意顺序咨询、确定性选择、Nia/Ivo/Rhea 任意顺序回访。三人回访全部完成后归档事件。

- 事件草稿对玩家可见、可编辑且不自动发送。
- 只有当前阶段、正确 NPC、冻结请求 ID 的 `completed` 回复推进；普通聊天、错误 NPC、降级、失败、超时与晚到响应不推进。
- 选择面板二次确认后本地写入，零 Provider 调用、零长期记忆写入、零直接关系变更。
- 选定方案立即改变信号校准台灯光、标牌与事件卡，跨游戏重启恢复。
- 回访草稿明确包含玩家选择；模型只从输入框可见文本得知结局，不获得隐藏世界状态。
- “重温余波”只重置 F-014；F-013、关系、长期记忆和聊天生命周期保持原契约。

## 状态与兼容契约

新增独立版本化 JSON 存档，不修改 F-013：

```text
user://twilight_signal_aftermath_v1.json
locked → nia_briefing → consulting → decision_ready → aftermath → completed
```

存档字段固定为 `schema_version`、`event_id`、`stage`、`consulted_npcs`、`selected_outcome`、`reacted_npcs`、`completed`。未知版本、非法枚举、重复 NPC 或组合不一致时只重置 F-014，并显示非阻断提示。

F-013 未完成时 F-014 锁定；首次完成 F-013 后自动解锁。F-014 解锁后重温 F-013 不删除其进度，追踪卡在 F-013 重温期间暂时显示前篇，完成后恢复余波。

## Agent 与接口边界

- 保持 Dialogue v1 与关系 GET 的公开 Schema 不变。
- 三名 NPC 继续共享编排和模型客户端，同时保持 Persona、会话、长期事实和关系隔离。
- 不新增任务 API、世界状态 API、工具调用、WebSocket、隐藏 system context 或多 Agent 协作。
- 模型回复不参与选择、状态转移或完成判定，也不能直接写入游戏世界。

## 验收门禁

- [x] Step 0：用户批准真实 Godot 三方案选择画面的位置、文字和信息层级。
- [x] Step 1：状态、严格存档、前置解锁与 F-013 协调通过。
- [x] Step 2：三方咨询、确定性选择、精确重试与错误保护通过。
- [x] Step 3：三人回访、三种视觉结局和重温通过。
- [x] Step 4：自动/Fake 与统一质量通过。
- [ ] Step 4：用户跨重启试玩通过；用户已要求跳过选择恢复、三人回访、完成和重温验证，因此未计为通过。
- [x] 真实模型 UAT 获独立授权并通过。
- [ ] Git 交付获独立授权并完成后归档。

## 非目标

不扩大地图，不加入室内、新 NPC、新素材包、物品、奖励、战斗、动态事件、NPC 自主移动、关系锁结局、模型驱动状态转移、自然语言自动记忆或 NPC 间自治协作。
