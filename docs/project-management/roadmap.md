# Cyber Town 路线图

更新时间：2026-09-22

| 顺序 | 任务 | 状态 | 依赖与出口 |
| --- | --- | --- | --- |
| 1 | F-001—F-008 | 已完成或已归档 | 历史卡与证据见归档 |
| 2 | F-009 安全、成本与性能优化 | 已完成 | 独立fake-only QA、语义门禁、固定性能复验及Step 7交付门禁均通过 |
| 3 | F-009 Step 7 交付收口 | 已完成 | PR #13最终HEAD CI、合并及合并后`main` CI均通过；归档已生效 |
| 4 | F-010 Cyber Town 基础可玩版本 | 已完成 | Fake、用户试玩、真实模型 UAT、本地统一质量、PR #14、PR CI、合并及合并后 `main` CI 均通过 |
| 5 | F-011 NPC 回访体验强化 | 交付中 | 实现与三层验收均已通过；端到端 GitHub 交付与同 PR 归档已获授权并正在执行 |

F-009 Step 0—7均已完成。PR #13最终HEAD `a0911b95`的Quality run `35343077888`通过，随后以 `75171492070bddddffef58cc4f0fe9552d40bb77` 合并到`main`；合并后Quality run `35343297890`再次通过，归档正式生效。F-010 以功能提交 `3399726e` 经 PR #14 合并为 `49598b6c`；PR HEAD Quality run `35691505073` 与合并后 `main` Quality run `35691653263` 均通过，归档正式生效。F-011 的实现、视觉、Fake、统一质量、用户试玩与真实模型 UAT 均已通过，端到端 GitHub 交付与同 PR 归档已获授权并正在执行。本文件只表达任务级顺序。当前状态见 [current-task.md](current-task.md)，F-011 设计规格见 [npc-return-visit/design-spec.md](../design/npc-return-visit/design-spec.md)，历史归档见 [task-cards](../archive/task-cards/)。
