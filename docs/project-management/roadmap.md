# Cyber Town 路线图

更新时间：2026-09-22

| 顺序 | 任务 | 状态 | 依赖与出口 |
| --- | --- | --- | --- |
| 1 | F-001—F-008 | 已完成或已归档 | 历史卡与证据见归档 |
| 2 | F-009 安全、成本与性能优化 | 已完成 | 独立fake-only QA、语义门禁、固定性能复验及Step 7交付门禁均通过 |
| 3 | F-009 Step 7 交付收口 | 已完成 | PR #13最终HEAD CI、合并及合并后`main` CI均通过；归档已生效 |
| 4 | F-010 Cyber Town 基础可玩版本 | 已完成 | Fake、用户试玩、真实模型 UAT、本地统一质量、PR #14、PR CI、合并及合并后 `main` CI 均通过 |
| 5 | F-011 NPC 回访体验强化 | 已完成（PR #16 合并生效） | 实现与三层验收均通过；归档已在同一 PR 准备，最终 HEAD CI 与合并事实以 GitHub 为准 |
| 6 | F-012 街区探索与情境对话 | 已完成（PR #17 合并后生效） | 三层验收与首次 PR HEAD CI 均通过；归档提交进入同一 PR，最终 CI 与合并后在 `main` 生效 |

F-009 Step 0—7均已完成。PR #13最终HEAD `a0911b95`的Quality run `35343077888`通过，随后以 `75171492070bddddffef58cc4f0fe9552d40bb77` 合并到`main`；合并后Quality run `35343297890`再次通过，归档正式生效。F-010 以功能提交 `3399726e` 经 PR #14 合并为 `49598b6c`；PR HEAD Quality run `35691505073` 与合并后 `main` Quality run `35691653263` 均通过，归档正式生效。F-011 已通过三层验收并由 PR #16 合并为 `2bf190d5`，合并后 Quality run `35709407498` 成功。F-012 功能提交 `d10be31` 已推送到 PR #17，首次 Quality run `35720207231` 通过；归档已在同一 PR 准备，需等待最终 HEAD CI 与合并后在 `main` 生效。本文件只表达任务级顺序。当前状态见 [current-task.md](current-task.md)，历史归档见 [task-cards](../archive/task-cards/)。
