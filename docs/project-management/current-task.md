# 当前任务：F-010 Cyber Town 基础可玩版本

更新时间：2026-09-22

## 当前状态面板

| 判断项 | 当前唯一口径 |
| --- | --- |
| 当前任务卡 | `F-010 Cyber Town 基础可玩版本` |
| 路线图任务状态 | `ACTIVE` |
| 当前所在步骤 | Step 5：Fake、用户试玩、统一质量与真实模型 UAT 均通过，进入 Git 交付 |
| 当前业务闭环 | 将现有 Agent 后端和低保真表单转化为可移动、可接近三名 NPC 并对话的 2D 小街区 |
| 当前执行状态 | `READY_FOR_GIT_DELIVERY` |
| 已完成到哪里 | v2 视觉门禁、城镇闭环、Fake/用户试玩、统一质量（2115 passed）与 9 次硬上限内真实模型 UAT 全部通过 |
| 精确阻塞点 | 无产品或验收阻塞；待完成提交、推送、PR、远端 CI 和合并记录 |
| 当前未执行 | Git 提交、推送、PR、远端 CI 和合并 |
| 唯一最小下一项 | 审查最终差异后完成 F-010 Git 交付 |
| 下一动作类型 | `DELIVER_F010_GIT` |
| 授权状态 | 用户于 2026-09-21 批准视觉基线、`F-010` 及本地实现；2026-09-22 明确批准本轮真实模型 UAT；Git 交付仍未授权 |
| 外部调用 | 1 次内置图像生成；官方 CC0/OFL 素材下载；F-010 真实 UAT 共 9 次（8 次官方 usage、1 次未知结果按最大预留保守计费） |
| 当前分支 | `feat/playable-town`，从 `2666f54180f6f31c79de785f38a6ac64e58ea85b` 创建 |
| 环境与副作用 | 已按授权读取本地测试配置但未输出密钥；隔离 UAT 与台账资源保留在受忽略 `data/` 路径；未删除、重置或清理资源 |
| 当前证据 | [视觉基线、获批 v2 与交互版 v3 截图](../design/playable-town/visual-baseline.md) |

## 任务合同

```yaml
task_id: F-010
working_id: PLAYABLE-TOWN
task_name: Cyber Town 基础可玩版本
roadmap_status: ACTIVE
step: git_delivery
execution_status: READY_FOR_GIT_DELIVERY
current_goal: 完成F-010提交、PR、CI与合并交付
completed_checkpoint: visual and playable loop, fake and user UAT, full quality 2115 passed, real UAT passed at 9-call hard cap
blocked_at: none
next_action: 审查最终差异并完成Git交付
next_action_type: DELIVER_F010_GIT
authorization:
  plan_implementation: authorized_by_user_2026_09_21
  visual_preproduction: consumed
  game_code_changes: authorized_by_user_2026_09_21
  local_tests: authorized_for_f010
  real_provider_calls: authorized_by_user_2026_09_22_7_planned_9_hard_cap_usd_0_05
  git_commit_push_pr_merge: unauthorized
external_calls:
  image_generation: 1
  real_provider_completed_with_usage: 8
  real_provider_unknown_conservatively_charged: 1
  real_provider_total: 9
branch:
  name: feat/playable-town
  base: 2666f54180f6f31c79de785f38a6ac64e58ea85b
design:
  baseline: docs/design/playable-town/visual-baseline.md
  concept: docs/design/playable-town/concept-v1.png
  approved_capture: docs/design/playable-town/godot-normal-v2.png
  current_capture: docs/design/playable-town/godot-interactive-v3.png
  status: FIRST_VISUAL_GATE_APPROVED
```

## 用户目标与业务价值

玩家进入一处统一画面的 2D 小街区，控制角色移动，接近 Nia、Ivo、Rhea，与其对话并感知记忆和关系变化，然后继续探索。完成后项目首次具备玩家可观察的游戏闭环，而不再只是连接页和独立表单。

## 非目标

- 不做室内、多地图、任务、物品、战斗、昼夜、天气或开放世界。
- 不做 NPC 自主移动、多 Agent 协作、复杂寻路或世界状态写入。
- 不做移动端、手柄、语音、角色自定义或跨重启聊天记录。
- 不修改公开 Dialogue v1 与 relationship API Schema。

## UI 与视觉验收合同

- 设计产物：`docs/design/playable-town/visual-baseline.md` 与 `concept-v1.png`。
- 用户设计确认状态：`approved`（2026-09-21）。
- 首个实机验收视口：Godot `640 × 360`，暖色傍晚正常状态，Nia 对话面板打开。
- 必须一致：一街一广场、三名 NPC 空间分布、暖色窗灯/蓝紫阴影、低密度轻科幻装饰、底部面板比例、中文可读性。
- 允许差异：角色和建筑细节服从最终获批的 16×16 素材；概念图远景、河流和心形图标不进入实机。
- 禁止出现：风格混杂、生成图直接切片、战斗元素、过量霓虹、调试字段占据玩家 UI。
- 核心页面状态：正常、加载、成功、降级、超时、不可用、非法输入和手动重试均已实现；用户已确认除 Fake 固定回复外，功能、视觉与手感试玩通过。

## 验收标准摘要

1. 玩家可在城镇移动、碰撞并被摄像机稳定跟随。
2. 只有接近的最近 NPC 显示互动提示，未知 NPC 标识无法发起请求。
3. 三名 NPC 的会话、聊天记录、关系和请求状态严格隔离。
4. 对话、重试、降级、超时和后端不可用均有明确中文反馈。
5. fake 功能验收、用户视觉/手感验收和另行授权的真实模型 UAT 分别通过后，任务才可完成。

## 文件与安全边界

视觉批准后允许修改 `game/`、相关 Godot 测试、统一质量入口的必要契约及对应权威文档。未经独立授权不得读取 `.env`、调用真实模型、提交、推送、创建 PR、合并、部署或删除资源。

## 视觉门禁

[项目规则](../../AGENTS.md)要求的设计批准、首个实机视口和用户 Fake 模式手感验收均已完成：用户先批准概念基线与 F-010，再于 2026-09-22 通过 `godot-normal-v2.png`，并确认除 Fake 固定回复外功能与手感试玩通过。这不等于真实模型 UAT 或 Git 交付获批。
