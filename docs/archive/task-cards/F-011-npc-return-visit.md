# 待生效归档任务卡：F-011 NPC 回访体验强化

更新时间：2026-09-22

> 功能、三层验收和 PR #16 首次 HEAD CI 已通过。本归档随包含它的 PR #16 最终 HEAD CI 通过并合并到 `main` 后生效；最终 HEAD、CI 和 merge SHA 以 GitHub 记录为准。

## 当前状态面板

| 判断项 | 当前唯一口径 |
| --- | --- |
| 当前任务卡 | `F-011 NPC 回访体验强化` |
| 路线图任务状态 | `COMPLETE_ON_PR_MERGE` |
| 当前所在步骤 | Step 5：文档与 Git 交付 |
| 当前业务闭环 | NPC 引导话题与显式记忆写入 → 双端重启 → 独立召回 → 关系阶段与回复风格影响后续体验 |
| 当前执行状态 | `ARCHIVE_PREPARED_PENDING_PR_MERGE` |
| 已完成到哪里 | 功能提交 `5b42c529` 已推送；PR #16 首次 Quality run `35708257630` 通过；本归档已准备 |
| 精确阻塞点 | 包含本归档的最终 PR HEAD 必须通过新一轮 CI 后才可 squash merge |
| 本阶段不执行 | 资源删除、强推、分支删除、tag、发布、新地图/任务/物品/新美术 |
| 唯一最小下一项 | 提交并推送归档，等待 PR #16 最终 HEAD CI，通过后 squash merge |
| 授权状态 | 本地开发、离线测试和真实模型 UAT 已完成；Git 提交、推送、PR、CI、合并与归档已获用户授权 |
| 环境与副作用 | 已读取本地测试配置并访问 DeepSeek；F-011 隔离数据与验收账本已创建并保留 |

## 当前执行合同

```yaml
task_id: F-011
task_name: NPC 回访体验强化
roadmap_status: COMPLETE_ON_PR_MERGE
step: "Step 5 / archive prepared in PR #16"
execution_status: ARCHIVE_PREPARED_PENDING_PR_MERGE
current_goal: 等待归档提交的最终CI并完成PR #16 squash merge
completed_checkpoint: "offline quality, fake town loop, user gameplay UAT, and six-call real-provider UAT passed; ports 8000 and 18010 released"
blocked_at: FINAL_PR_HEAD_CI_AND_MERGE
next_action: 提交并推送归档，最终CI通过后squash merge PR #16
next_action_type: ARCHIVE_COMMIT_CI_AND_MERGE
authorization:
  plan_implementation: authorized_by_user_2026_09_22
  local_code_changes: authorized_for_f011
  local_offline_tests: authorized_for_f011
  real_provider_calls: "COMPLETED_2026_09_22; 6 calls, 6 checks, USD 0.001039"
  git_commit_push_pr_merge: AUTHORIZED_BY_USER_2026_09_22
delivery:
  pr: 16
  url: https://github.com/Muggle8888/15-cyber-town/pull/16
  feature_commit: 5b42c529508160fab8447b8780faa59666774a4e
  initial_pr_ci_run: 35708257630
  initial_pr_ci_status: passed
  archive_effective_when: final PR head CI passes and PR 16 merges to main
branch:
  name: feat/f-011-npc-return-visit
  base: 2f48184dba8f352f36335d339ed2fd7b6c3ee93d
design:
  spec: docs/design/npc-return-visit/design-spec.md
  first_capture: docs/design/npc-return-visit/godot-menu-normal-v1.png
  status: FIRST_VISUAL_GATE_APPROVED
validation:
  local_quality: "2138 passed, 969 skipped, 0 failed; full quality passed"
  fake_provider: passed
  user_gameplay_uat: passed
  user_gameplay_note: "Fake 固定回复不构成 Persona、语义召回或关系语气验收"
  real_provider_uat: "passed; 6 calls, 6 checks, 2111 prompt tokens, 336 completion tokens, USD 0.001039, pending 0"
  ports_after_real_uat: "8000 free; 18010 free"
  port_18010_after_user_close: free
temporary_resources:
  planned_uat_data: E:/Agent/comprehensive-cases/15-cyber-town/data/uat/f-011
  planned_acceptance_ledger: E:/Agent/comprehensive-cases/15-cyber-town/data/acceptance-ledgers/f-011.sqlite3
  planned_pr_body: E:/Agent/.codex-temp/cyber-town-f011-pr.md
  created:
    - "E:/Agent/comprehensive-cases/15-cyber-town/data/uat/f-011 (2 files, 262144 bytes)"
    - "E:/Agent/comprehensive-cases/15-cyber-town/data/acceptance-ledgers/f-011.sqlite3 (24576 bytes)"
  registration:
    owner: F-011 Step 4 real-provider UAT
    content: low-sensitivity structured facts, deterministic relationship state, control metadata, and metadata-only acceptance usage
    may_contain_secrets: false
    retention: retain through F-011 Git delivery and request user disposition afterward
    deletion: Codex will not delete; user manual action only after inventory
  pr_body_registration:
    owner: F-011 Step 5 Git delivery
    content: user-visible PR title and description only
    may_contain_secrets: false
    retention: retain through F-011 Git delivery and request user disposition afterward
    deletion: Codex will not delete; user manual action only after inventory
```

## 用户价值与完成定义

玩家可对 Nia、Ivo、Rhea 使用清楚、可确认的引导动作保存主题和回复风格；重启游戏及后端后，相关 NPC 仍能独立召回自己的结构化事实，关系阶段和回复风格会影响下一次普通模型回复。公开 API 不变，客户端不显示事实键、隐藏分数或规则码。

F-011 只有在自动与 Fake 验证、用户试玩、另行授权的真实模型 UAT 和必要质量门禁分别通过后才能标记完成。Fake、截图或历史 F-010 证据不能替代真实模型验收。

## 范围边界

- 保留现有地图、三名 NPC、Dialogue v1 与 relationship GET Schema。
- 不加入任务、奖励、物品、室内、多地图、NPC 自主移动、自然语言自动记忆提取、向量数据库、embedding、多 Agent 或模型驱动世界状态。
- `请记住` 继续使用既有 30 天 TTL；聊天记录和 conversation ID 不跨游戏重启。
- 本次真实 Provider 授权已按 6 次调用消费完毕；F-011 Git 交付已单独授权并在 PR #16 合并时消费，后续真实调用、其他 Git 交付和资源删除仍分别需要新的明确授权。
