# 待生效归档任务卡：F-013 暮光失联信号

更新时间：2026-09-22

> 功能、三层验收和 PR #18 首次 HEAD CI 已通过。本归档随包含它的 PR #18 最终 HEAD CI 通过并合并到 `main` 后生效；最终 HEAD、CI 和 merge SHA 以 GitHub 记录为准。

## 当前状态面板

| 判断项 | 当前唯一口径 |
| --- | --- |
| 当前任务卡 | `F-013 暮光失联信号` |
| 路线图任务状态 | `COMPLETE_ON_PR_MERGE` |
| 当前所在步骤 | Step 5：Git 交付与归档 |
| 当前业务闭环 | Nia 异常灯光 → 三处地标线索 → Ivo/Rhea 核对 → 返回 Nia 归档 |
| 当前执行状态 | `ARCHIVE_PREPARED_PENDING_PR_MERGE` |
| 已完成到哪里 | 功能提交 `b7fe341` 已推送；PR #18 首次 Quality run `35732218406` 通过；本归档已准备 |
| 精确阻塞点 | 包含本归档的最终 PR HEAD 必须通过新一轮 CI 后才可 squash merge |
| 本阶段不执行 | 资源删除、外部素材获取、强推、分支删除、tag 或发布 |
| 唯一最小下一项 | 提交并推送归档，等待 PR #18 最终 HEAD CI，通过后 squash merge |
| 下一动作类型 | `ARCHIVE_COMMIT_CI_AND_MERGE` |

## 当前执行合同

```yaml
task_id: F-013
task_name: 暮光失联信号
roadmap_status: COMPLETE_ON_PR_MERGE
step: "Step 5 / archive prepared in PR #18"
execution_status: ARCHIVE_PREPARED_PENDING_PR_MERGE
current_goal: 等待归档提交的最终CI并完成PR #18 squash merge
completed_checkpoint: "feature commit b7fe341 pushed; PR 18 initial Quality run 35732218406 passed; archive prepared in the same PR"
blocked_at: FINAL_PR_HEAD_CI_AND_MERGE
next_action: 提交并推送归档，最终CI通过后squash merge PR #18
next_action_type: ARCHIVE_COMMIT_CI_AND_MERGE
authorization:
  planning_and_task_card: AUTHORIZED_BY_USER_2026_09_22
  local_branch_and_code_changes: AUTHORIZED_STEP_0_TO_4_BY_USER_2026_09_22
  local_offline_and_fake_tests: AUTHORIZED_STEP_0_TO_4_BY_USER_2026_09_22
  visual_capture: AUTHORIZED_GODOT_SCREENSHOTS_BY_USER_2026_09_22
  external_assets: NOT_AUTHORIZED
  real_provider_calls: AUTHORIZED_BY_USER_2026_09_22_CONTINUE_REMAINING_AFTER_EXPLICIT_SCOPE
  git_commit_push_pr_merge: AUTHORIZED_BY_USER_2026_09_22_CONTINUE_REMAINING_AFTER_EXPLICIT_SCOPE
delivery:
  pr: 18
  url: https://github.com/Muggle8888/15-cyber-town/pull/18
  feature_commit: b7fe341da816b4303aa0d12ce7e4ee48ae0d3126
  initial_ci_run: 35732218406
usage:
  local_validation: "town tests and Fake loopback passed; full quality 2155 passed, 969 skipped, 0 failed"
  user_gameplay_uat: "passed across restart; complete event and replay reset confirmed"
  real_provider_calls: "6 / hard cap 8; 6 checks passed; 0 semantic retries; 1318 micro-USD; pending 0"
branch:
  base: main@5d60d3458e9ef67b2e5327f38cf661a7336ffddb
  current: feat/f-013-twilight-signal-event
planned_resources:
  design_spec: E:/Agent/comprehensive-cases/15-cyber-town/docs/design/twilight-lost-signal/design-spec.md
  step_0_screenshot: E:/Agent/comprehensive-cases/15-cyber-town/docs/design/twilight-lost-signal/godot-event-tracker-normal-v1.png
  final_dialogue_screenshot: E:/Agent/comprehensive-cases/15-cyber-town/docs/design/twilight-lost-signal/godot-event-dialogue-v2.png
  final_completion_screenshot: E:/Agent/comprehensive-cases/15-cyber-town/docs/design/twilight-lost-signal/godot-event-complete-v1.png
  deterministic_test_save: E:/Agent/comprehensive-cases/15-cyber-town/game/.godot/f013-event-state-test.json
  fake_test_save: E:/Agent/comprehensive-cases/15-cyber-town/game/.godot/f013-event-state-fake.json
  uat_data: E:/Agent/comprehensive-cases/15-cyber-town/data/uat/f-013
  acceptance_ledger: E:/Agent/comprehensive-cases/15-cyber-town/data/acceptance-ledgers/f-013.sqlite3
  status: screenshots are tracked design evidence; synthetic saves and UAT resources are ignored and retained; no secrets or raw model dialogue are recorded
```

## 玩家体验契约

固定事件 ID 为 `twilight_lost_signal_v1`。玩家按以下确定顺序完成事件：

1. 与 Nia 讨论异常灯光；
2. 在暮光导览牌记录线索；
3. 请 Ivo 核对旧广播编号；
4. 在信号校准台记录线索；
5. 请 Rhea 核对雨夜路线；
6. 在雨棚投递板记录线索；
7. 返回 Nia 归档事件。

事件对话草稿对玩家可见、可编辑且不自动发送。只有从当前事件入口发送给正确 NPC、并获得 `completed` 回复的请求才推进；普通对话、错误、超时、`degraded`、其他 NPC 或晚到回复均不推进。模型内容不参与完成判断。

事件进度使用版本化 Godot 本地存档跨游戏重启保存。关系阶段只改变称呼、语气和完成文案，不阻止完成；关系不可用时使用中性文本。完成后不发放物品、奖励或成就，可经二次确认重新调查，且只重置 F-013 进度。

## Agent 与接口边界

- 三名 NPC 继续共享编排和模型客户端，同时保持独立 Persona、会话、长期事实与关系状态；不改造成自治协作的多 Agent。
- Godot 确定性拥有事件状态、线索、存档和推进规则；模型不能解锁内容、写入世界或决定完成。
- 保持 Dialogue v1、关系 GET 和公开 Schema 不变；事件步骤只保存在客户端，不进入网络载荷。
- 情境必须通过玩家可见输入文本发送，不增加隐藏世界上下文、任务 API、工具调用、WebSocket 或 SSE。

## 完成定义

- [x] 用户通过 Step 0 事件追踪卡视觉门禁。
- [x] 七阶段状态机、本地存档、损坏恢复和确认重置通过验证。
- [x] 三处地标、四次事件对话、重试和晚到响应保护形成可玩闭环。
- [x] 四种关系阶段改变表现但不阻断事件。
- [x] 自动、Fake、用户跨重启试玩和统一质量分别通过。
- [x] 真实模型 UAT 已授权并通过：6 calls / 6 checks / 0 retries / 1318 micro-USD / pending 0。
- [ ] Git 交付另行授权并完成后才归档。

## 非目标

不建设通用任务编辑器、分支结局、物品奖励、新地图、室内、NPC 自主移动、动态事件、多 Agent、云存档或新美术资源。
