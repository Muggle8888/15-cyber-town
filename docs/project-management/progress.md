# 项目进度

更新时间：2026-09-19

## 当前结论

F-009 Step 0—7已经完整收口。PR #13最终HEAD `a0911b95b657f3fb557d2a422c15836e14fcb9fc`的Quality run `35343077888`成功；PR随后以 `75171492070bddddffef58cc4f0fe9552d40bb77` 合并到`main`，合并后Quality run `35343297890`再次成功。正式仓本地`main`已快进同步到该合并提交，任务卡与实施计划归档已经生效。

当前无活动任务、无实现阻塞，也没有沿用的F-009授权。功能worktree及其既有`AGENTS.md`修改、远程功能分支和全部Step 6证据均保留，未执行清理。下一步只能由用户选择新任务，或另行精确授权资源处置。

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

全部历史根及tool16/R7/quality10/performance根继续保留。恢复区最终19,611文件/1,147,659,064 bytes<2GiB；全部observer和受控进程已退出，8000/8001及Python监听均为0。全部资源保留不删除，详细结果见evidence。
