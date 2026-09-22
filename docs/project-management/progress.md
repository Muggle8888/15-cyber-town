# 项目进度

更新时间：2026-09-22

## 当前结论

F-011 `NPC 回访体验强化` 的本地实现与全部三层验收已完成。当前分支为 `feat/f-011-npc-return-visit`，基于 `main@2f48184d`；用户已通过“话题与记忆”弹层的 640×360 实机视觉门禁和实际 Fake 模式试玩。客户端引导话题、写入确认、展示文本与原始载荷分离、精确重试和关系状态反馈，以及后端关系阶段/持续回复风格受控上下文均已实现。最终统一质量完整通过，结果为 2138 passed、969 个既有条件 skip、0 failed。经单独授权的 `deepseek-flash` 真实模型 UAT 一次完成 6 次计划调用与 6 项检查，累计 2111 输入 token、336 输出 token、费用 USD 0.001039、未决调用 0。`8000` 与 `18010` 均已释放；用户已授权 commit、push、PR、CI、合并与归档，当前进入 `GIT_DELIVERY_IN_PROGRESS`。

用户已批准 `F-010 Cyber Town 基础可玩版本` 的概念视觉，并于 2026-09-22 通过首个 `640 × 360` Godot 实机画面 `godot-normal-v2.png`。城镇现已成为产品入口，包含一街一广场、玩家四向移动、碰撞、有限摄像机、三名固定 NPC、最近目标提示、健康状态、底部中文对话、按 NPC 恢复的会话与六回合记录、关系阶段、失败/重试/降级反馈、基础声音和静音开关。

F-010 功能提交为 `3399726e03369d0b4a693d529fdcf56804f7b81e`。Godot 4.7.2 编辑器导入、F-010 城镇定向测试、既有 Godot 诊断/对话回归和独立端口 `18010` 的 fake FastAPI—Godot 城镇回环均通过。用户于 2026-09-22 实际试玩后确认“除 Fake 固定回复外，功能和手感试玩通过”；用户随后正常关闭试玩窗口。完整 Noto Sans CJK SC OFL 字体已接入。

当前执行状态为 `COMPLETE`。DeepSeek 规范模型名、当前价格预算、v10 控制数据库迁移、隔离 UAT 脚本与追加式未知结果解决账本已接入；最终统一质量为 2115 passed、969 个既有条件 skip、0 failed。真实 UAT 在 9 次硬上限内完成：8 次取得官方 usage，1 次未知结果保留原记录并按最大预留保守计费；累计 2065 输入 token、307 输出 token，保守费用 11,130 微美元。9 项检查覆盖三名 NPC 身份、Nia 多轮上下文与跨服务长期事实召回、Ivo 跨 NPC 长期事实隔离和关系事件。

PR [#14](https://github.com/Muggle8888/15-cyber-town/pull/14) 的最终 HEAD Quality run [`35691505073`](https://github.com/Muggle8888/15-cyber-town/actions/runs/35691505073) 通过，随后以 `49598b6c1962c528d32a63829e82ea6832f1c623` 合并到 `main`；合并后 Quality run [`35691653263`](https://github.com/Muggle8888/15-cyber-town/actions/runs/35691653263) 再次通过。本地 `main` 已快进到该合并提交，F-010 归档正式生效，当前没有活动任务。

视觉基线见 [`docs/design/playable-town/visual-baseline.md`](../design/playable-town/visual-baseline.md)，当前任务与后续步骤分别见 [current-task.md](current-task.md) 和 [implementation-plan.md](implementation-plan.md)。

## F-009历史执行摘要

两个finding已分别归类：`docs/archive/F-009-过程记录-20260905/evidence.md` 的HEAD blob为36,115,596 bytes，超过全局5 MiB文本上限，属于 `archive_packaging_policy_conflict`，且该大文件正文尚未被当前门禁验证；`manifest.json` 的 `sensitive_scan.findings.github_live_token` 值为空数组、元素数0、真实token/私钥签名匹配0，属于 `deterministic_scanner_false_positive`。扫描器、包装入口和workflow与 `origin/main` 同blob，`environment_drift=false`。这不是产品、性能或环境失败，但仍构成最终交付验证缺口。

R2实际产生9个连续分片，范围2,562,794—4,194,242 bytes，均为有效UTF-8且低于4 MiB固定上限；机器索引和manifest均可严格JSON解析。R3定向扫描入口、索引、manifest和9片后0 finding，`content_verified_by_current_gate=true`。随后正式CI完整执行敏感信息前后门、静态、schema、Godot、两组集成及pytest并通过；未重跑Step 6的quality10或性能矩阵。

只读诊断确认：活动批次的drain等待循环每轮执行完整batch/recovery/identity扫描，当前等价检查6.374616秒；循环在耗时检查后先判deadline而未复核marker。R4/R6均有marker action3、约20秒失败及随后995，现有tmp_path测试不覆盖活动根容量扫描。最小修复只移除等待循环内的重复全树check，确认后仍执行完整check，不改10秒超时或安全边界。

本次修复在等待marker时只轮询observer error与原10秒deadline，marker确认后仍执行一次原完整check；新增确定性慢check回归要求完整check只在确认后执行一次。V1–V4最终全过：tool16 138函数/533参数，R7 18选择器/43节点，Ruff与strict mypy通过，定向2 passed、固定清单collect 43 tests。三个运行根仍不存在，冻结指纹见evidence。

tool16唯一运行138函数/533参数全passed，native completed=true、5,218 events、无overflow/unknown/reparse，边界为空，observer退出且端口恢复。tool16根531文件/4,714,834 bytes，恢复区950,837,019 bytes；R7与quality10仍不存在。

R7唯一运行43/43节点全部通过且正式readiness回执有效；failed/skipped/xfailed/not_run均为空，native completed=true、144 events，全部恢复项和脱敏为true。恢复区950,898,725 bytes，加quality10 1GiB上限为2,024,640,549 bytes≤2GiB；quality10现可执行一次且仅一次。

quality10唯一运行九阶段全部exit0；完整pytest共3,075结果，2,942 passed、133既有历史根条件skip、0 failed，前后策略/敏感信息门通过。native completed=true、83,840 events，无overflow/unknown/reparse；根176,402,745 bytes，恢复区1,127,301,470 bytes。S3性能根新鲜，按256MiB上限后总量仍<2GiB，固定benchmark与1+5协议已冻结。

S3唯一实际矩阵完成1次warm-up+5次测量，8场景的failure/warning均为空；三SQLite p95/p99仅触发合同明确的非阻断诊断，空间与dispatch ownership通过。performance根199文件/20,357,594 bytes，恢复区最终19,611文件/1,147,659,064 bytes，8000/8001及Python监听均为0。S3 1/1已用，不再追加性能运行。

最小修复及V1–V4已通过；tool15随后137函数/532参数全部passed。R6的17选择器/42节点为42 passed、0 failed、0 not-run，但 `step6_native_watch_drain_timeout` 使native observation/inventory不完整。R6 1/1已用，不得重跑；下一项只可另行审定observer drain超时诊断，不能创建quality10。

## 资源与边界

历史执行时，恢复区最终为19,611文件/1,147,659,064 bytes<2GiB，全部observer和受控进程已退出，8000/8001及Python监听均为0；这些数字是验收时快照。当前承载tool16/R7/quality10/performance原始现场的仓库外Step 6根已经不存在，原始SQLite与运行目录不再可本地复查。Git内归档、索引、manifest、分片哈希和脱敏结论继续保留，详细校准见evidence与本地资源处置清单。
