# Cyber Town 路线图

更新时间：2026-09-21

| 顺序 | 任务 | 状态 | 依赖与出口 |
| --- | --- | --- | --- |
| 1 | F-001—F-008 | 已完成或已归档 | 历史卡与证据见归档 |
| 2 | F-009 安全、成本与性能优化 | 已完成 | 独立fake-only QA、语义门禁、固定性能复验及Step 7交付门禁均通过 |
| 3 | F-009 Step 7 交付收口 | 已完成 | PR #13最终HEAD CI、合并及合并后`main` CI均通过；归档已生效 |
| 4 | F-010 Cyber Town 基础可玩版本 | 进行中 / 等待真实模型 UAT | 用户 Fake 模式试玩与修复后统一质量均已通过；真实模型及 Git 交付未授权 |

F-009 Step 0—7均已完成。PR #13最终HEAD `a0911b95`的Quality run `35343077888`通过，随后以 `75171492070bddddffef58cc4f0fe9552d40bb77` 合并到`main`；合并后Quality run `35343297890`再次通过，归档正式生效。F-010 的视觉基线、本地实现、首个实机视口、用户 Fake 模式功能/手感试玩和修复后统一质量均已通过。任务仍需另行授权的真实模型 UAT，不能宣称完成。本文件只表达任务级顺序。当前状态见 [current-task.md](current-task.md)，视觉基线见 [playable-town/visual-baseline.md](../design/playable-town/visual-baseline.md)，历史归档见 [task-cards](../archive/task-cards/)。
