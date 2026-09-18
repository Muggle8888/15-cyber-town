# 候选任务卡：F-009 安全、成本与性能优化

## 2026-09-04：单次 canonical 诊断完成，未复现旧异常

当前状态：`step_6_in_progress / canonical_diagnostic_complete_not_reproduced / space_C_quality_blocked`。本轮仅完成用户单独授权的脱敏诊断适配、自测和一次精确节点复现尝试。该节点本次通过，旧 quality-13 的 canonical 失败根因仍未确认，不能标记修复、完整 quality 通过或 Step6 完成。

实现：仅 scripts/f009_step6_qa.py 与 backend/tests/test_f009_step6_qa.py。CanonicalPathError 向后兼容原 resolved 属性和异常语义；仅在原有拒绝发生后附加 QA 根内原路径、受限解析目标类别、主库/sidecar 角色、注册事件、身份及完整父链的 lstat 快照。快照标记 after_rejection_not_atomic，不再次 resolve，不打开解析目标；超根目标不输出文本，只分类。pytest hook 按 nodeid/phase 加锁关联异常与失败报告，输出元数据而非完整 traceback。原 canonical/reparse/身份拒绝和真实 provider 禁令均保留，没有改产品、原 runner、SQL/migration、依赖/CI、负载或性能门禁。

验证：两 QA 文件 Ruff check --no-cache 与 format --check --no-cache 均 exit0。全新 self-tests 执行 7 passed / 0 failed / 0 skipped：四种 SQLite 主库/sidecar 脱敏拒绝、NTFS retired 分类且不访问目标、8线程16条报告关联不串线，以及原有“不同解析目标必须拒绝”回归。此为六项新增诊断用例与一项既有回归。报告关联用合成异常验证，不表示捕获过本轮真实 canonical 故障。

随后在全新 reproduction 中仅执行一次 backend/tests/test_architecture_probe_step5.py::test_v23_waiter_conflict_and_concurrent_prepare_have_one_owner，1 passed / 0 failed / 0 skipped。该次原用例的8线程16次prepare及1 owner/15 waiter、单一 execution、冲突拒绝和唯一 quota断言通过。没有捕获 canonical 异常，无真实 expected/resolved 失败元数据，不能由此确认瞬态sidecar竞态或宣称旧问题消失。没有第二次运行、循环压力或完整 quality 重试。

两次命令作用域的环境/TEMP/sys.path恢复，39项保护缓存均保持；boundary_violations={}，自测与复现各自创建前登记7/6路径，分别抑制6/1个可选current别名。TEMP与缓存沿用既有QA统一入口隔离，不新增原生例外。未运行全量mypy、全部QA用例、新性能绑定用例、完整native quality或性能；这些仍是后续Step6门禁，不能与本次选择性验证合并称作完成。

本轮冻结98文件 SHA256=c6c97588e319913349ad1ff2fa9c8f9762aed27e3ab69164f28de068192d4e2f，执行前后匹配；相对25d0fa23...仅两个QA文件变化，其余96文件一致。脚本LF、测试CRLF保持。双方branch/HEAD/本地origin/main/staged0保持，HEAD=1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3；正式工作树仍仅五文档修改，无提交/推送/PR/合并/部署或Step7。

证据均在 E:\Agent\cyber-town-f009-step6-qa\canonical-diagnostic-01：
- self-tests-summary.json：SHA256=5abd8a22c936dfd40f0c0762f302c53c63366e1ed93cb12114b97808b08725ae。
- reproduction-summary.json：SHA256=ef26f7b6d74ce05087b43f249b2a01249e0533963564aad2243ecb7aaaf3ae22。
- diagnostic-summary.json：SHA256=8b6f7387246892335a2c6cf31814b7a3309349c0894e670fe7aac03daa01853e，status=diagnostic_completed_not_reproduced、target_attempt_count=1、original_failure_resolved=false、step6_complete=false。

旧quality13三份摘要SHA256保持：quality fde8ff8c9da6bed12fd919574719689d4721fb4b740ca08fa1dde74a62a1ffb1，pytest f3a905274e644d6e2b5ba339d62dd859c78ce25f9f8d50328444fb21edc5e38c，native 929c6934e51ad8990131dd2dc95362b174673fc63e350b9d0dca002cec4bfbb1。原55passed/1failed及所有历史指纹登记、83文件表、28哈希缺失解释和SIM300失败摘要完整保留，没有覆盖旧证据或重开旧SQLite。

资源收口：诊断根4文件/10目录（含根）/22715字节，含1个全新synthetic SQLite主库与3份JSON；0 WAL/SHM、嵌套Git、只读文件、.env或key，reparse0。全QA根10954文件/9594目录/1739636052字节，9011 SQLite3、13 .db、161 WAL、161 SHM、61嵌套Git、70只读文件、13 synthetic .env名称、11测试key。相对前表新增14路径，removed=[]，旧路径仅QA根目录mtime变化；旧文件身份、大小和时间均保持，包括11个既有key，未读取/哈希key内容。quality13仍104文件/85目录/43505833字节。39项保护缓存metadata SHA256=cd441f082436fb555a4951c684e0f230ea36102c04e4c1caa999569caed744e5不变；默认24个数据库/sidecar路径不存在，8000/8001空闲，相关执行进程已退出。性能新根control-space-performance-v1仍不存在，唯一一次性能额度未使用。

资源分类：正式/feature工作树、QA工具和Step5工具链仍在使用；本次诊断根、quality13以及全部旧QA/quality/A/B/性能SQLite、sidecar、缓存、分支和成功失败摘要明确保留。当前无到期项；用户已删除V30—V33仍不存在，不重建；历史Codex获准删除记录沿用原台账。本轮删除0、回收0字节，未访问外部服务或真实provider。

后续边界：本次“精确节点一次”额度已经用完，不自行重复。旧故障尚无可验证根因，当前不提出绕过安全检查的修复。若用户后续决定恢复C，应单独批准在全新预登记根携带诊断执行完整native quality，以恢复旧失败的原执行上下文并保留新证据；本轮没有授权或执行quality-14。仅在完整语义/quality门禁满足且恢复执行获准后，才能使用保留的一次固定warm-up+5-run性能额度。Step7仍未授权。


## 2026-09-04：canonical-diagnostic-01 获准，诊断适配待验证

当前状态：`step_6_in_progress / canonical_diagnostic_validation`。用户单独批准补充 QA 脱敏路径诊断，并在全新 E:\Agent\cyber-town-f009-step6-qa\canonical-diagnostic-01 复现原节点一次；不包含完整 quality、性能、产品修复或放宽路径拒绝。

仅 scripts/f009_step6_qa.py、backend/tests/test_f009_step6_qa.py 改动：CanonicalPathError 保留原异常/解析目标属性，仅附加受限元数据；拒绝后对 QA 原路径及父链做 lstat 快照，明确不是原子状态。不解析第二次，不读取解析目标。超根目标仅分类（NTFS retired/other），不输出目标文本。注册处附加受限事件类别；pytest hook 按 nodeid/phase 加锁关联失败元数据，原拒绝继续抛出。新增六项诊断测试，另执行一个既有不同解析目标拒绝回归。

冻结98文件 SHA256=c6c97588e319913349ad1ff2fa9c8f9762aed27e3ab69164f28de068192d4e2f；相对25d0fa23...仅上述两个 QA 文件变化，其他96文件匹配。双方 branch/HEAD/本地 origin/main/staged0保持，原历史和quality13失败摘要保留。

资源准确目录为根、self-tests、reproduction；文件为 self-tests-summary.json、reproduction-summary.json、diagnostic-summary.json。仅 synthetic pytest/SQLite 与脱敏摘要，无原生工具、key或新增动态例外；实际子路径仍由 ResourceGuard 在创建前登记。TEMP/缓存沿用既有统一 QA 根隔离。全部保留至用户另行手动处置，Codex不删除。

顺序：两QA静态检查 → 六项诊断自测和一项既有路径拒绝回归 → 只运行 backend/tests/test_architecture_probe_step5.py::test_v23_waiter_conflict_and_concurrent_prepare_have_one_owner 一次 → 不论是否复现均停止并报告；不得试到通过。新的门禁失败仍停止。唯一性能额度保持未使用，不进入Step7。


## 2026-09-04：专项 C 三行修正通过，quality-13 在 canonical 检查失败后收口

当前状态：`step_6_in_progress / space_C_quality_blocked`。仅获准的 test_f009_step6_qa.py 第 352/374/405 行比较顺序已修正，字节数不变、CRLF 保持。旧 SIM300 失败摘要完整保留。专项 C 已恢复执行一次 quality-13，但全量 pytest 失败，遵守用户“验证失败即停止”规则，不修复新的缺陷、不重跑、不启用性能。

门禁结果：两 QA 文件 Ruff check 和 format --check 均 exit0；完整 native quality 的 lock、ruff、mypy、schema、godot-import、godot-unit、connectivity、dialogue-connectivity 八命令 exit0。connectivity 的 connected、duplicate_rejected、http_error_recovery、invalid_recovery、non_string_rejected、redirect_rejected、stopped_service、timeout_recovery、unavailable 九场景均通过。第九命令 pytest exit1：55 passed / 1 failed / 0 skipped，-x 后停止。quality 前置 ignore/sensitive 策略通过；最后策略检查因 pytest 失败未执行。

失败节点：backend/tests/test_architecture_probe_step5.py::test_v23_waiter_conflict_and_concurrent_prepare_have_one_owner；failure_location=scripts/f009_step6_qa.py:49，触发 CanonicalPathError / step6_resource_canonical_mismatch。该节点使用 8 个线程执行 16 次 synthetic SQLite prepare。ResourceGuard 在 sqlite3.connect 前逐一验证主库及 WAL/SHM/journal 路径；validate_path 在 canonical 不等价时直接抛异常，未经过 guard.reject，所以报告 boundary_violations={} 不能解释成没有发生边界拒绝。

已确认与不确定项：本次停止发生在 QA canonical 检查，现有摘要没有保留 expected/resolved 路径和对应调用栈，只能定位抛出位置，不能确认是哪一个具体 sidecar，也不能判断产品 owner 语义通过或失败。监测器本批捕获两条其他路径的退役 SQLite sidecar 通知并按既有例外完成核对；这支持“临时 sidecar 路径解析竞态”的候选解释，但不是本失败的根因证明。不得把 NTFS 退役目标当作可访问资源，不得通过跳过验证或放宽整个根边界继续运行。

未完成项：完整 pytest 其余用例、六个新增性能根绑定用例、此前延期的 test_long_term_dialogue_integration.py::test_godot_scene_fastapi_sqlite_and_fake_provider_form_a_real_local_loopback 精确节点（本批尚未运行，不能由 dialogue-connectivity 替代）、quality 最后策略检查及正式性能/同批数据库空间核对。warm-up1+正式5 性能额度未使用，E:\Agent\cyber-town-f009-step6-qa\control-space-performance-v1 仍不存在。Step6 未完成，未进入 Step7。

冻结与作用域：98 文件 SHA256=25d0fa2396059e51ca5eebaef354d66a92fbbb6aba3c6039493ab6d681c34198，执行前后匹配。相对前次 a7941293... 仅授权的 QA 测试三行变化，其余 97 文件匹配。双方 branch/HEAD/本地 origin/main 保持 1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3，staged0；产品、既有 runner、SQL/migration/依赖/CI/工作量/门禁未改。command_scope 的环境、TEMP、sys.path 已恢复；39 项保护缓存保持，metadata SHA256=cd441f082436fb555a4951c684e0f230ea36102c04e4c1caa999569caed744e5。相关 Python/Godot 进程查询为空，8000/8001 空闲，默认 24 个数据库/sidecar 路径不存在。

原生监测：completed=true 只表示监测作用域完成，不表示 quality 通过。实际 2824 个事件、unknown_paths=[]、reparse0、overflow=false，31 个游戏源/副本 SHA256 一致；原生 summary 的 103 文件/43456344 字节是在写入自身前统计。最终根盘点为 104 文件 / 85 目录（含根）/ 43505833 字节，49 SQLite3、1 .db、0 WAL/SHM、0 嵌套 Git、1 原生生成的测试 key；该 key 仅核对元数据，未读取/哈希/复制内容。pytest 创建前登记 215 路径，46 个可选 current 别名未创建。

全 QA 根最终 10950 文件 / 9584 目录（含根）/ 1739613337 字节；9010 SQLite3、13 .db、161 WAL、161 SHM、61 嵌套 Git、70 只读文件、13 synthetic .env 名称、11 测试 key，reparse0。相对前批新增 189 路径（104 文件+85目录），旧资源移除0；旧路径仅 QA 根目录 mtime 变化，旧文件元数据均保持，包括 10 个旧 key。A/B control-space-v1 仍为 904 文件 / 839 目录 / 130287236 字节；semantic-summary-04.json SHA256 保持 cd9beeed531af48ab00402f8f4bf7f382d4b0f42b1d6e79b61417f7a4efa6cee。逐路径增量表和本批三份摘要哈希见 evidence。

摘要准确路径均位于 E:\Agent\cyber-town-f009-step6-qa\quality-13：
- quality-summary.json：fde8ff8c9da6bed12fd919574719689d4721fb4b740ca08fa1dde74a62a1ffb1。
- pytest-summary.json：f3a905274e644d6e2b5ba339d62dd859c78ce25f9f8d50328444fb21edc5e38c。
- native-summary.json：929c6934e51ad8990131dd2dc95362b174673fc63e350b9d0dca002cec4bfbb1。

资源分类：正式/feature 工作树和旧 Step5 工具链仍在使用；quality-13、全部旧 QA/quality/A/B/原 full-matrix-01 的 SQLite、sidecar、缓存、成功失败摘要及分支明确保留。无当前到期项。用户已删除 V30—V33 仍不存在，仅登记不重建；历史 Codex 获准删除说明保留。本轮删除0、回收0字节。不安装、不访问真实 provider/外部服务、不提交/推送/PR/合并/部署。

下一步最小诊断提案（未授权、未执行）：
1. 仅 scripts/f009_step6_qa.py 与 backend/tests/test_f009_step6_qa.py：为 canonical 异常及失败报告补充脱敏元数据，包含 QA 根内原路径、解析目标的受限类别、事件类别、主库/sidecar 角色和可获取的身份/父链状态；超根目标只输出分类，不读取其内容。不保留原始业务输出、key、秘密或整个 traceback。
2. 新测试验证报告确实记录失败原因、并发记录不串线和敏感字段不输出；原 canonical/reparse/身份拒绝行为保持，不能用“已登记”跳过复核，也不启用历史候选 runner。
3. 若获准，先在 evidence 登记全新 E:\Agent\cyber-town-f009-step6-qa\canonical-diagnostic-01（目前未创建），内容仅 synthetic pytest 子目录和诊断摘要。静态检查及诊断自身用例通过后，只复现上述精确失败节点一次；失败即保留摘要停止，不重复试到通过。所有实际 Python 子路径仍创建前逐项登记，沿用 QA TEMP/缓存隔离，全程无需原生新例外。
4. 拿到确切 expected/resolved/身份证据后再提出修复；本提案不包含放宽路径边界、产品修复、quality-14、重用 quality-13 或性能执行。已有未使用性能根和一次固定额度继续保留。

简短复盘：前期原生监测已能区分退役 sidecar 的通知，但 Python 路径拒绝摘要只有代码行号，导致本轮无法直接归因。后续应把受限、脱敏、并发安全的失败元数据作为 QA 工具自身验收项，记录在本任务实施说明；不修改全局偏好，不降低安全门禁。


## 2026-09-04：获准修正三行 SIM300，恢复专项 C

当前状态：`step_6_in_progress / space_C_validation_running`。用户允许仅修正三行、保留失败摘要后恢复已授权 C。实际仅 test_f009_step6_qa.py 第 352/374/405 行交换 assert 比较两侧，字节数不变、CRLF 保持；原失败摘要完整保留。

执行前 a7941293... 冻结匹配；修正后 98 文件 SHA256=25d0fa2396059e51ca5eebaef354d66a92fbbb6aba3c6039493ab6d681c34198，相对前批仅该 QA 测试文件变化，其余 97 文件匹配。双方 branch/HEAD/本地 origin/main/staged0 保持，产品、runner、migration/依赖/CI/工作量/门禁均未改。

quality-13 与 control-space-performance-v1 仍全新不存在，沿用已完成的 372 固定目标和原动态类别预登记及本轮已授权目录；8000/8001 空闲，39 项保护缓存保持。恢复顺序：两 QA 静态检查 → 完整原 native quality（包含真实 Godot 回环及六个新用例）→ 通过后唯一一次 warm-up1+正式5 性能复验 → 同批数据库/资源核对。新的验证失败仍立即停止，不自行修复或重复性能批次。


## 2026-09-04：专项 C 静态检查失败，按硬停止规则暂停

当前状态：`step_6_in_progress / space_C_static_blocked`。专项 C 已获授权，但新增 QA 用例在第一个正式静态检查失败；遵守用户“验证失败即停止”，不修复、不继续 quality 或性能，不标记 Step6 完成。

实际失败：两 QA 文件的 Ruff check --no-cache 返回 1，backend/tests/test_f009_step6_qa.py 第 352、374、405 行各触发 SIM300（tuple 置于比较左侧）。这是本轮新增测试写法的静态规则缺陷。format --check 因首项失败未执行；完整 native quality、Godot 回环、pytest 6 个新增用例、mypy/contracts 等后续工程门禁及一次 warm-up1+正式5 性能批次均未启动。准备阶段的 stdin formatter 返回 0 不等同于 lint/测试通过。原 A/B 通过结论和全部旧失败证据保持，不将其拼作 C 通过。

当前冻结 98 文件 SHA256=a794129399497a3596609a2257877281137d0e0625958f651e14df2b50241cd8；执行后未改。仅两个 QA 文件相对 B 有变化，其余 96 文件相同；既有 runner、产品/SQL/migration/依赖/CI/负载/门禁均未改。双方 branch/HEAD/本地 origin/main 保持 1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3、staged0；正式工作树只有五文档修改。

已完成创建前登记：372 个固定资源目标及既有动态类别。E:\Agent\cyber-town-f009-step6-qa\quality-13 与 E:\Agent\cyber-town-f009-step6-qa\control-space-performance-v1 均不存在；没有创建 key、SQLite、quality 摘要或性能摘要，唯一性能额度未使用。静态失败摘要和完整只读资源核对已写入正式 evidence，无须为本次失败新建报告目录。

停止收口盘点：QA 根 10846 文件 / 9499 目录（含根）/ 1696107504 字节；8961 SQLite3、12 .db、161 WAL、161 SHM、61 嵌套 Git、70 只读文件、13 synthetic .env 名称、10 测试 key，reparse0。相对 B-04 完整元数据表 added/removed/changed 均为空。control-space-v1 904 文件 / 839 目录 / 130287236 字节不变。12 个 A/B 摘要 SHA256、15 个 migration SHA256、10 个 key 元数据均不变（未读取或哈希 key 内容）。39 项保护缓存 metadata SHA256=cd441f082436fb555a4951c684e0f230ea36102c04e4c1caa999569caed744e5 保持；默认 24 个数据库/sidecar 路径不存在，8000/8001 空闲。

资源分类：正式/feature 工作树与 Step5 工具链仍在使用；全部旧 QA、quality、原 full-matrix-01、A/B SQLite/sidecar/缓存及成功失败摘要明确保留，当前无到期项。用户已删除 V30—V33 仍不存在，不重建；历史 Codex 获准删除说明沿用旧台账。本轮删除 0、回收 0 字节。没有提交、推送、PR、合并、部署、Step7 或外部服务访问。

最小恢复提案（尚未执行）：只将 test_f009_step6_qa.py 第 352、374、405 行的 assert (benchmark.CORE_REVALIDATION_ROOT, benchmark._INDEPENDENT_CLIENT) == original 改为 assert original == (benchmark.CORE_REVALIDATION_ROOT, benchmark._INDEPENDENT_CLIENT)，保持 CRLF、用例含义和其他源码不变。保留本失败摘要并重新冻结后，从两 QA 静态检查恢复已有 C 顺序。仅需允许这三处修正并解除本次硬停止；现有 quality-13/性能根授权继续有效，不需换根或追加性能批次。

简短复盘：新增测试再次因静态规则停止，根因是编写断言时没有沿用同文件已有通过模式，且格式化只能处理排版，不能替代 lint。以后新增断言优先沿用已通过写法，在创建原生资源前完成静态门禁。建议落点为本任务 QA 实施说明；本次仅记录，不修改全局规则、不关闭 SIM300。


## 2026-09-04：专项 C QA 适配完成，冻结后开始验证

当前状态：`step_6_in_progress / space_C_validation_running`。仅两个 QA 文件适配 quality-13 和独立性能根，新增 6 个用例验证正常/异常恢复、已有矩阵/非目录/越界拒绝及根身份变化后恢复。原 runner、产品和 migration 未改。

当前冻结仍为 98 文件，SHA256=a794129399497a3596609a2257877281137d0e0625958f651e14df2b50241cd8；相对 B 的 907def7f... 仅两个 QA 文件变化，其余 96 文件匹配。372 个固定资源目标已经在创建前逐路径登记：性能 45 目录/267 文件目标含 66 主库全部 sidecar，quality 固定目录/元数据、31 个 game 源副本和原生 key 精确路径；原有五类动态例外也已登记。两个新根尚未创建；端口 8000/8001 空闲，39 项工作树保护缓存保持。

以下按已授权顺序执行两 QA 静态检查、完整 native quality（含 Godot 回环），全部通过后才启用一次固定 warm-up1+正式5 性能复验。任何验证失败即停止，保留摘要及资源，不自行修复或重复批次。


## 2026-09-03：专项 C 已授权，准备完整 native quality 与一次性能复验

当前状态：`step_6_in_progress / space_C_authorized`。用户单独授权专项 C：完整 fake-only native quality（含 Godot 回环）以及一次固定 warm-up1+正式5 性能复验。该授权覆盖此阶段所需的全新根和最小 QA 作用域适配；保留失败即停止、旧资源留存和 Step7/Git 交付禁令。

执行前冻结 98 文件 SHA256=907def7f9995695b89448497d78ce8234daaa9b564b8dff1bb711431dcb08db2 已匹配；双方 branch/HEAD/本地 origin/main 不变，staged0。A/B 已通过证据和全部失败历史保留，当前正式空间门禁尚未复验。

准确路径：E:\Agent\cyber-town-f009-step6-qa\quality-13 用于完整 native quality；E:\Agent\cyber-town-f009-step6-qa\control-space-performance-v1 用于本次性能复验，其固定 runner 子目录为 full-matrix-01。两个根均要求全新、canonical/完整父链无 reparse，并在任何创建前完成正式 evidence 登记。旧 quality12/full-matrix01 不启用、不复制或重开旧 SQLite。

文件与适配：仅 scripts/f009_step6_qa.py 和 backend/tests/test_f009_step6_qa.py。将当前 native quality 精确绑定从 quality-12 换为 quality-13，复用已通过 probe04；添加专用性能配置作用域，将既有 f009_step5_benchmark 的 CORE_REVALIDATION_ROOT 绑定到新性能父根，原 runner 文件不改。入口/退出核对根身份与完整父链，拒绝已有 full-matrix-01、非目录和越界路径；正常/异常退出均恢复输出根和 _INDEPENDENT_CLIENT。新针对性测试随完整 quality 执行，通过前不能开始性能。

quality13 资源为 tmp、cache/mypy、cache/uv、cache/ruff、pytest、冻结 game 副本、appdata、localappdata、git-template/info/exclude、native-monitor-ready.json、native-monitor-drain.marker、quality-summary.json、pytest-summary.json、native-summary.json。沿用用户已批准的原生“目录/类别预登记＋运行期记录＋结束核对”：game/.godot、appdata/Godot、localappdata/Godot、pytest/**/.git、cache/uv。只有 quality13/appdata/Godot/keystores/debug.keystore 可由原生 Godot 生成；Python 禁止读取/哈希/复制/使用内容，仅核对元数据。不新增动态类别，不改变网络/子进程/文件身份检查。

性能根资源：根目录、tmp、原 gate_boundary_matrix_manifest 的 43 个矩阵/运行目录、全部 66 套主库/WAL/SHM/journal 与 performance-summary.json；另有根下 boundary-summary.json 和 database-audit.json 记录配置恢复、资源与独立数据库/空间门禁核对。实际清单在创建前由原 manifest 展开并加齐 journal 后登记。沿用统一 command_scope 的 QA TEMP/缓存隔离；新父根 tmp 为原 runner 要求的登记目录。运行期仅 Python/SQLite 和真实本地回环，性能父根不加入 NATIVE_ROOTS。

顺序：完成最小 QA 适配及新冻结 → 两 QA 静态检查 → 完整原 quality 九命令及前后策略检查，包含全 pytest、被延期的真实 Godot/FastAPI/SQLite/fake 回环和新增适配测试 → 全部通过后只执行一次原固定 gate-boundary matrix → 核对同批新库与所有空间门禁、五文档及资源收口。保留原负载、随机标识生成、统计中位数、全部延迟/吞吐和 256/512/768KiB 阈值。三 SQLite 延迟为非阻塞诊断，但其 control/observability/combined 独立空间限制不能豁免；不追加批次找通过。

所有新旧资源保留至 Step6 收口后用户另行手动处置。无自动删除/清理缓存、安装或真实 provider 调用；用户已删除 V30—V33 只登记。当前尚未创建新根、未启动 quality 或新增性能额度，尚无专项 C 通过结论。


## 2026-09-03：空间专项 A/B 验证完成，等待专项 C 授权

当前状态：`step_6_in_progress / space_AB_complete / awaiting_space_C_authorization`。本轮三处 QA 导入错误已按用户授权修正，B 剩余验收全部通过。A/B 实现与专项验证可以收口；完整 Step6 尚未完成，SPACE-01 的正式空间门禁仍待专项 C 复验，不标记 step_6_complete 或 awaiting_step_7_authorization。

本轮仅对 test_f009_step6_qa.py 删除两处多余导入空行和一处冗余局部 Any 导入（减少 32 字节，保留 CRLF）；scripts/f009_step6_qa.py 仅更改两处新摘要目标为 semantic-summary-04.json（保留 LF）。没有全文件重排。产品/SQL/migration/依赖/CI/性能 runner、统计协议和阈值未改。

执行前及结束后的 98 文件 SHA256 均为 907def7f9995695b89448497d78ce8234daaa9b564b8dff1bb711431dcb08db2；相对本轮起点 105ab330... 仅上述两 QA 文件变化，其余 96 文件一致。双方 branch/HEAD/本地 origin/main 保持，HEAD=1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3，staged0。正式仓库仅五文档修改，未提交/推送/PR/合并/部署或进入 Step7。

实际门禁：六授权 Python 文件 Ruff check --no-cache 和 format --check --no-cache、全 backend/src/backend/tests/scripts mypy、contracts.export --check 均 exit0。全新 pytest-semantic-02 为 180 passed / 0 skipped / 0 failed：新恢复校验 17、long_term_memory_application 70、long_term_retrieval 42、sqlite_long_term_memory 26、sqlite_observability 17、observability_step5 8。pytest 创建前登记 658 路径，138 个可选 current 别名未创建；内层/外层 boundary_violations 均 {}，39 项保护缓存保持，command_scope 环境/TEMP/sys.path 恢复通过。

三个独立 evaluator 报告已实际生成，各为 25/25 passed、0 failed、11 维度，进程 ID 分别为 45608、42324、49648；canonical_digest 均为 1986a20db79cce74dfe458193ce0f2ab52e0d457d047b31d2e9465aeadf624bb。scope 泄漏、重复计费/业务写入、越权 provider dispatch、retry amplification、rate-limit bypass、非零成本与禁止内容命中均为 0，预算归属和熔断转换一致性均为 1000000 ppm。此为本轮独立三进程实测，不借用已有 evaluator 单测结果。

A 的 75 项/12 对布局通过证据保留，固定输入与 v9 草案未改；B 前批 e44a... 快照的 757 passed / 55 历史 skipped / 1 Godot 原生拒绝保留原记录。本轮 180 项属于当前 907def... 快照，不能把前后批次拼称为本轮全量重跑。旧三个失败摘要与所有 A 摘要哈希/身份保持，不覆盖、不隐藏。用户批准延期的精确 Godot 回环节点仍在 pending_native_quality_tests 中，后续完整 native quality 必须真实执行通过；未新增 skip，未将旧失败改成通过。

通过摘要：E:\Agent\cyber-town-f009-step6-qa\control-space-v1\semantic-summary-04.json，SHA256=cd9beeed531af48ab00402f8f4bf7f382d4b0f42b1d6e79b61417f7a4efa6cee，passed=true、scope=python_semantic_remainder、step6_complete=false。pytest-semantic-02/qa-summary.json 和 evaluator-process-01/02/03.json 均已生成，准确路径与实际子路径创建前登记，哈希/逐文件明细见 evidence。无第二次运行、无 A 重跑或额外核心性能批次。

最终资源盘点：QA 根 10846 文件 / 9499 目录（含根）/ 1696107504 字节；8961 SQLite3、12 .db、161 WAL、161 SHM、61 嵌套 Git、70 只读文件、13 synthetic .env 名称、10 测试 key、reparse0。control-space-v1 为 904 文件 / 839 目录 / 130287236 字节，831 SQLite3、6 WAL、6 SHM，无嵌套 Git/key/.env/只读文件。本轮净增 137 文件 / 139 目录 / 13928843 字节，其中专项根增加 13924747 字节，QA 隔离 mypy cache 增加 4096 字节。逐路径盘点无资源移除；已存路径只观察到专项目录及 QA mypy 缓存元数据变化，完整增量清单附 evidence。

10 个既有测试 key 的身份/大小/时间不变，未读取或哈希内容；39 项保护缓存 metadata SHA256=cd441f082436fb555a4951c684e0f230ea36102c04e4c1caa999569caed744e5 不变。15 个 migration 哈希与本轮前一致，原 14 个历史 migration 未改；默认数据库/sidecar 24 路径不存在，8000 无监听，QA 执行进程已退出。quality-13 未创建，V30—V33 仍不存在，仅登记不重建。

资源分类：正式/feature 工作树与旧 Step5 工具链仍在使用；全部旧、新 QA/A/B/quality12/full-matrix01/SQLite/sidecar/缓存/V29/分支及失败、成功摘要明确保留。无本轮到期项。用户已删除 V30—V33，历史 Codex 获准删除说明沿用原台账。本轮删除 0、回收 0 字节；任何后续人工回收仍需单独盘点，不能把本轮通过视为删除许可。

下一步只在取得专项 C 授权后执行：在当前冻结代码上启用全新、预登记且沿用既有动态资源例外的 native quality 根，完整 fake-only quality 和全部工程门禁包含被延期的 Godot 回环；语义/quality 通过后，执行额外获准的一次固定统一 warm-up + 5-run 核心性能复验，保留原阈值/工作量/统计口径。原 full-matrix-01 的 control median 260KiB>256KiB 失败证据仍保留，原批次额度已用完，不能自行追加或凭 A 布局节省推断性能门禁通过。专项 C、完整 Step6 收口和 Step7 本轮均未执行。


## 2026-09-03：三处 QA 导入错误获准修正，恢复 B

当前状态：`step_6_in_progress / space_B_import_fix_resumed`。用户批准仅修正三处错误、保留摘要后继续 B。恢复前 98 文件 SHA256=105ab33039127ffdb27fa419eef12c4ac1961d7c3e306ebd6cc0645b92d6d09e 完全匹配；双方 branch/HEAD/本地 origin/main/staged 不变，七份历史 A/B 摘要哈希及文件身份与正式记录匹配。

本轮最小修改：backend/tests/test_f009_step6_qa.py 仅移除两处 _pytest/scripts 导入间多余空行及一处冗余局部 Any 导入，共减少 32 字节，保留 CRLF；scripts/f009_step6_qa.py 仅将新摘要的新鲜性检查/写入两处 semantic-summary-03.json 改为 semantic-summary-04.json，保留 LF。未重新格式化整个文件，产品/SQL/migration/原用例/性能门禁不改。

执行冻结 98 文件 SHA256=907def7f9995695b89448497d78ce8234daaa9b564b8dff1bb711431dcb08db2；相对恢复前仅上述两 QA 文件变化，其余 96 文件完全一致。test_f009_step6_qa.py SHA256=03e8ddb3bf11925125468af221bb67bca1a4c75658a82976f373a9dba9a32492；f009_step6_qa.py SHA256=ff1013831383dc870de98949ed4b7bb7c12fa34b852afd8ac4171c6f81f01fa4。完整冻结表附 evidence。

准确新摘要 E:\Agent\cyber-town-f009-step6-qa\control-space-v1\semantic-summary-04.json 已在正式 evidence 于创建前登记（F009-Step6，脱敏 B 恢复摘要），保留到 Step6 收口后用户手动处置。已登记的 pytest-semantic-02 及三个 evaluator 输出仍不存在，canonical/完整父链无 reparse；沿用其已有登记，所有实际子路径创建前逐项登记。旧 semantic-summary.json/-02/-03 不覆盖，不复用任何旧 SQLite。

本轮仍执行四静态门禁 → 17 个恢复校验用例和五个剩余 Python 文件 → 三个独立 evaluator。旧 757/55/1 明确保留原快照归属；Godot 仍是后续完整 native quality 必验项。统一命令入口、TEMP/缓存、原生守卫、环境退出恢复和失败即停止均保持。A 不重跑；当前不执行完整 quality、额外正式性能或 Step7。尚无本轮通过结论。


## 2026-09-03：B 剩余入口已修正，但新 QA 导入错误阻塞首项静态门禁

当前状态：`step_6_blocked / space_B_resume_qa_import_lint_failed / awaiting_user_direction`。用户批准修正清单并继续 B 后，本轮仅修改两个 QA 文件，完成剩余入口和 17 个针对性用例；正式执行在第一项 Ruff check --no-cache 失败后停止。没有运行 format --check、mypy、schema、新 pytest 或三个独立 evaluator；代码尚未通过验收，B/SPACE-01/Step6 均未完成。旧 A 通过和 e44a... 快照的 757 passed / 55 历史 skipped / 1 原生失败完整保留，不冒充本轮结果。

准确失败（均 backend/tests/test_f009_step6_qa.py）：1893 和 1933 的 I001，两个函数中的 _pytest 与 scripts 导入之间多插入一行空白；2169 的 F401，新增全局 Any 后该函数的局部 typing.Any 导入变成冗余。对应函数为 test_qa_real_numbered_pytest_directory_has_no_alias_notification、test_qa_pytest_alias_scope_rejects_invalid_request_and_restores、test_qa_godot_rename_notification_strictly_revalidates_paths_and_identity。Ruff exit1，共 3 项；这些是代理本次 QA 编辑引入的问题。停止后没有修正或重跑，没有发现新的产品语义验证结果。

本轮执行与停止后的 98 文件 SHA256 同为 105ab33039127ffdb27fa419eef12c4ac1961d7c3e306ebd6cc0645b92d6d09e。与本轮起点 e44a494daf31675fe6a36ed3e0b05a9f1eb863621e5c2d4be99e0f6a40df7dc3 相比仅 scripts/f009_step6_qa.py 和 backend/tests/test_f009_step6_qa.py 变化，其余 96 文件不变。产品、SQL、migration、依赖、CI、原性能 runner/协议/阈值均未改。原 14 migration 保持，v9 与 A 草案及上轮 SHA256 一致。

新摘要 E:\Agent\cyber-town-f009-step6-qa\control-space-v1\semantic-summary-03.json 已在创建前正式登记并保留，2737 字节，SHA256=a76f555fce4300c32a9e12177a50c34ca77f537c4adf2c5acbb4772d975d49d2，passed=false / static_check_failed。本轮 guard 违规 {}、39 项保护缓存不变、command_scope 的环境/TEMP/sys.path 恢复通过；旧 inner guard 的原生拒绝仍在 prior_result 单列保留，未覆盖。六份原 A/B 摘要的哈希及 file_id/device/size/mtime 全部匹配。

恢复代码实现的边界仍待验证：读取旧 B 摘要前后身份/哈希，757/55/1、唯一原生失败、无剩余覆盖重叠校验；只选新 17 个恢复用例和五个尚未执行的 Python 文件；显式 pending_native_quality_tests 和 step6_complete=false；后续新 pytest 内层违规独立记录。Godot 节点仍是后续完整 native quality 必验项，不新增 skip、不算通过。此处仅说明已写入代码，不代表上述新增测试通过。

最终资源：QA 根 10709 文件 / 9360 目录（含根）/ 1682178661 字节；8832 SQLite3、12 .db、161 WAL、161 SHM、61 嵌套 Git、70 只读文件、13 synthetic .env 名称、10 测试 key、reparse0。control-space-v1 为 767 文件 / 700 目录 / 116362489 字节，702 SQLite3、6 WAL、6 SHM，无嵌套 Git/key/.env/只读文件。相对上轮逐路径元数据盘点，仅新增 semantic-summary-03.json 及其父目录 mtime 变化，其他路径元数据保持；无资源删除或缺失。10 key 仅核对元数据，未读取/哈希内容。默认数据库/sidecar 24 路径不存在，8000 无监听，本轮 QA 进程已退出。

仍在使用：正式与 feature 工作树、既有 Step5 工具链。明确保留：所有旧 A/B/QA/quality12/full-matrix01/SQLite/sidecar/缓存/分支及三个 B 失败摘要。已到期项：无。用户已删除：V30—V33，仍不存在、不重建。历史 Codex 获准删除说明保持原台账；本轮删除 0、回收 0 字节。pytest-semantic-02、三个 evaluator 报告和 quality-13 均未创建。branch/HEAD/本地 origin/main 不变，staged0；正式仅五文档修改。未启动 full quality、新核心性能、Step7；未提交/推送/PR/合并/部署。

复盘：格式准备的 Windows 文本管道插入了空行；代理随后用手工导入分类规则恢复分组，该规则与本项目 Ruff 对 scripts/_pytest 的实际分组不符，同时未考虑新增全局 Any 与已有局部导入的关系。Ruff format 只完成格式整理，不能代替 lint 通过。以后对这种局部错误按 Ruff 给出的准确位置作最小字节补丁，保持原导入布局；源码传输使用 UTF-8 bytes，不再全文件重整空白或自行推断导入分组。此规则只登记在任务文档，不修改全局设置。

准确下一步（方案，未执行）：按用户“验证失败即停止”等待恢复指示。仅删除上述两处多余空行和一处冗余局部 Any 导入；在脚本中把 B 输出的新鲜性检查与写入目标两处 semantic-summary-03.json 改为 semantic-summary-04.json，并先在正式 evidence 预登记新摘要。旧 semantic-summary.json/-02/-03 全部保留并校验。已登记的 pytest-semantic-02 仍全新可用，无需新测试根或 quality-13；原两 QA 文件/外层根授权持续有效。修正后重新冻结，仅继续原四静态门禁、17 个新 QA 用例、五个剩余 Python 文件和三个 evaluator；A 和旧 757 项不重跑，Godot 仍留待完整 native quality，任何验证失败即停。


## 2026-09-03：B 剩余专项执行冻结

执行冻结 98 文件 SHA256=105ab33039127ffdb27fa419eef12c4ac1961d7c3e306ebd6cc0645b92d6d09e；与恢复前 e44a494d... 快照相比仅两个授权 QA 文件变化，其余 96 文件及产品/migration 全部不变。scripts/f009_step6_qa.py SHA256=1b7d19c816cada3c7f4d5b77c0f566056b517b4dcf9c00913d3ebe63fbebf48a（LF）；test_f009_step6_qa.py SHA256=4d0f0c2d4981018c494472910803da5fabf8f7d411d21f1dadd3b41a26cfc7a5（统一 CRLF）。

实现：--space-semantic 现在限定为获批的 Python 剩余验收。先核验三份旧 B 摘要哈希/读取前后身份、757/55/1 实际结果、唯一 Godot 失败节点、四静态门禁与无剩余覆盖重叠，再执行显式五文件及新增 QA 节点。新摘要保留旧失败与原指纹，分列新 pytest 的内层边界违规，并保留 pending_native_quality_tests、step6_complete=false；不继承旧原生失败为绿灯。新 17 个 QA 用例为 1 个正常恢复、13 个不批准历史变体、3 个文件哈希/读取身份场景。

正式命令：既有 Python -B scripts/f009_step6_qa.py --space-semantic，经原 main/command_scope/subprocess_isolation 运行。先六授权 Python 文件 Ruff check / format --check，再全 mypy / schema check，再全新 pytest-semantic-02 的 17 个 QA 用例与五个文件，最后三个独立 evaluator。报告 semantic-summary-03.json；所有六个根/摘要准确路径已在下方 evidence 于创建前登记，动态子路径仍由守卫逐项预登记。没有运行 A/full quality/新核心性能/Step7。

编辑准备期间一次范围过宽的导入断言中断了编辑脚本，随后以精确整函数和完整占位符继续完成授权编辑；没有启动产品测试或正式门禁。格式准备发现 Windows 文本 stdin 会重复转换 CRLF，导致额外空行；现改用 bytes stdin/stdout，清除额外空白并恢复导入分组，整理前后 AST 完全相同，确认测试文件不存在多行字符串，不改变既有字符串值。此类准备过程不计为验收结果；正式验证仍只执行一次，任何验证失败即停止。

当前状态仍为 step_6_in_progress / space_B_remainder_running。以下冻结表记录每一文件状态、字节及 SHA256，历史快照完整保留；旧 757 项的 QA/产品结果保留在原 e44a... 快照，本轮只验证新恢复入口和未完成文件。


## 2026-09-03：获准修正 QA 清单并继续 B 剩余专项

当前状态：`step_6_in_progress / space_B_remainder_authorized`。用户已批准上节恢复方案；原七文件与 control-space-v1 授权、失败即停止和全部资源保留规则持续有效。本轮仅修改 scripts/f009_step6_qa.py 与 backend/tests/test_f009_step6_qa.py，实现显式五文件剩余清单、旧失败证据校验、原生待验标记及相关针对性测试。产品/SQL/migration/阈值/既有 Godot 测试不改。

恢复前 98 文件 SHA256=e44a494daf31675fe6a36ed3e0b05a9f1eb863621e5c2d4be99e0f6a40df7dc3 完全一致，双方 branch/HEAD/本地 origin/main/staged 不变。六份历史 A/B 摘要的 SHA256 和上轮正式盘点记录的 device/file_id/size/mtime 全部匹配。旧 757 passed / 55 skipped / 1 failed 保留原快照归属；只允许继承已核验且未改产品/原测试的结果，不把旧失败改写成通过。精确 Godot 节点继续列为后续完整 native quality 必验项。

资源均属于 F-009 Step6、synthetic Python/SQLite 或脱敏摘要：E:\Agent\cyber-town-f009-step6-qa\control-space-v1\pytest-semantic-02 及 qa-summary.json；同根 semantic-summary-03.json、evaluator-process-01.json、evaluator-process-02.json、evaluator-process-03.json。当前均不存在，canonical/完整父链无 reparse。下方正式创建前逐项登记完成后才可创建；所有 pytest 实际动态子路径仍由 ResourceGuard 创建前登记。保留至 Step6 收口后用户手动处置，代理不删除，不复用旧 SQLite/失败 basetemp。

顺序：准备两个 QA 文件并统一原有换行；执行必要静态门禁；在全新 pytest-semantic-02 中执行新增恢复校验用例和五个未运行 Python 文件；通过后运行三个独立 evaluator。使用既有 command_scope/subprocess_isolation 和 TEMP/缓存策略，原生守卫不放宽。A 不重跑，完整 quality、专项 C 性能额度和 Step7 不执行。当前没有新增通过结论。


## 2026-09-03：18 行换行已修正；B 在误选的 Godot 用例处停止

当前状态：`step_6_blocked / space_B_native_case_selection_mismatch / awaiting_user_direction`。本轮已按用户授权统一一个 QA 文件的 18 行换行、保留旧失败摘要后恢复 B。四项静态门禁通过；专项 pytest 为 757 passed / 55 历史 skipped / 1 failed。用户“验证失败即停止”规则已触发，停止后只作只读诊断、资源盘点及正式五文档更新，未继续改代码或重跑。A 已通过，B 尚未完成，SPACE-01 和 Step6 均未关闭。

本轮代码修改仅两 QA 文件：test_f009_step6_qa.py 的 18 行 LF→CRLF，非换行内容完全相同；scripts/f009_step6_qa.py 两处 B 汇总路径改为全新 semantic-summary-02.json，保留原 semantic-summary.json。执行前/停止后 98 文件 SHA256 均为 e44a494daf31675fe6a36ed3e0b05a9f1eb863621e5c2d4be99e0f6a40df7dc3；产品与 migration 未因本次恢复再改。原失败摘要及 A 三份摘要哈希保持。新 B 摘要 passed=false / semantic_tests_failed，不得据外层空违规字典宣称资源门禁通过。

实际结果：六个授权 Python 文件 Ruff check --no-cache、format --check --no-cache、全 backend/src/backend/tests/scripts 的 mypy、contracts.export --check 均 exit0。专项包括 SQLite 控制 68、预算 75、retry 18、独立 QA 318 项通过；55 跳过是既有 V10 诊断 53 项和异步持久化历史诊断 2 项，未新增 skip。完整按文件计数与失败节点见 evidence。25-case evaluator 的既有单元测试及三进程一致性用例通过，但 B 专门要求的三份独立 evaluator 报告尚未生成，二者不能混记。

失败节点：backend/tests/test_long_term_dialogue_integration.py::test_godot_scene_fastapi_sqlite_and_fake_provider_form_a_real_local_loopback。测试先启动本地 fixture server，再在 resolve_godot_executable 的 --version 探测中遭 QA 原生进程守卫拒绝；inner boundary_violations={step6_native_precreation_boundary_unavailable:1}，outer={}。Godot 未启动，不能记作真实回环通过。原生用例被代理误纳入仅 Python 的 B 清单，是 QA 编排缺陷；现有证据没有证明本轮出现新的产品语义缺陷。fixture 的 finally 负责停止线程；结束核对未发现本轮 QA 残留进程，8000 无监听。

剩余 B：五个尚未执行的 Python 文件 test_long_term_memory_application.py、test_long_term_retrieval.py、test_sqlite_long_term_memory.py、test_sqlite_observability.py、test_observability_step5.py（均 backend/tests），以及三个独立 evaluator 报告。Godot 是已执行集成文件最后一项；该文件前 36 项通过。建议用户恢复后，在冻结/历史摘要核对基础上保留已通过记录，仅继续上述剩余内容；将该 Godot 节点明确登记为后续完整 native quality 必须补验的待验项，不算通过、不新增 skip、不取消 Step6 门禁。准确恢复方案见 implementation-plan/evidence；当前仅方案，未实施。

资源已盘点并全部保留：QA 根 10708 文件 / 9360 目录（含根）/ 1682175924 字节；8832 SQLite3、12 .db、161 WAL、161 SHM、61 嵌套 Git、70 只读文件、13 synthetic .env 名称、10 测试 key、reparse0。control-space-v1 为 766 文件 / 700 目录 / 116359752 字节，702 SQLite3、6 WAL、6 SHM，无嵌套 Git/key/.env/只读文件。本轮 QA 净增 684 文件 / 604 目录 / 102256796 字节；其中专项目录净增 102195356 字节，其余 QA 隔离区域净增 61440 字节。完整实际路径、身份、时间与类别已登记 evidence。pytest 子进程创建前登记 3140 路径，491 个可选 current 别名未创建。

39 工作树旧缓存元数据与 10 个既有测试 key 的身份/大小/时间均不变；未读取或哈希 key 内容。15 migration 哈希与本轮前一致，原 14 个历史 migration 未改，v9 仍与 A 草案逐字节一致。默认数据库/sidecar 24 路径仍不存在。用户已删除的 V30—V33 仍不存在，仅登记不重建。两处 branch/HEAD/本地 origin/main 不变，staged0；feature 37 tracked modified / 61 actual untracked，正式仓库仅五文档修改。

仍在使用：正式/feature 工作树和既有 Step5 工具链。明确保留：未验收 B 代码、所有 A/B 数据库/sidecar/失败及成功摘要、旧 QA/quality12/full-matrix01/缓存/V29/分支。无本轮到期删除项；历史资源处置说明保留，本轮删除 0、回收 0 字节。未创建 quality-13；未启动本轮完整 quality、新正式性能批次或 Step7，未提交/推送/PR/合并/部署。

简短复盘：多次停顿暴露了代理对 QA 准备工作的检查不完整。换行问题已解决，本次根因是按文件名选测试却未检查内部原生子进程依赖。以后应在执行前核对“具体节点→工具/资源→授权范围”，将剩余覆盖与已有证据明确关联，避免整批重跑与递增根。此处仅登记任务内改进，不修改全局偏好/安全规则。


## 2026-09-03：获准统一18行换行并保留失败摘要，恢复B

当前状态：`step_6_in_progress / space_B_resumed`。用户允许将一个QA文件的18行换行统一，并保留失败摘要后继续B。原七文件/同一control-space-v1授权有效，原验证失败即停止、安全边界和资源保留规则不变。

恢复前98文件SHA256=e23f657acf24af29f4a65543f6cdec4771e1f9cf4fee9b42b24d20fe63d6ce59完全匹配；双方branch/HEAD/origin/main/staged保持。test_f009_step6_qa.py仅将18行LF统一为CRLF，99023→99041字节，非换行内容完全相同，新文件SHA256=846afc6bc14d560b6398ffa9bb2fc476f689c5bf75ec29b875626e5757732c88。scripts/f009_step6_qa.py仅将B汇总文件的全新检查/创建两处路径改为semantic-summary-02.json，保留其他流程不变。

原semantic-summary.json SHA256=8e2f04d70cf3b61f61ea722bd98ae33f07814135a98dcb49f9e33b7ddd45f7bd经只读核对保持，绝不覆盖。新汇总准确路径E:\Agent\cyber-town-f009-step6-qa\control-space-v1\semantic-summary-02.json已在正式evidence创建前登记，类别脱敏B恢复摘要，保留至Step6收口后用户手动处置。pytest-semantic-01和三个evaluator输出均尚不存在、canonical完整父链无reparse；仍按原22文件顺序和既有创建前登记机制执行。

执行冻结98文件SHA256=e44a494daf31675fe6a36ed3e0b05a9f1eb863621e5c2d4be99e0f6a40df7dc3；相对恢复前仅两个QA文件发生上述变化，产品/v9/其他文件不变。先完整B静态门禁，再全新pytest-semantic-01的专项测试，再三个独立evaluator；失败即停。A的75项/12对结果保留，不重跑、不复用A SQLite。当前不宣称B通过，不执行完整quality、额外正式性能或Step7，不创建quality-13。

## 2026-09-03：SPACE-01 A 已通过；B 在格式门禁停止，语义回归未启动

当前状态：`step_6_blocked / space_B_qa_mixed_line_endings / awaiting_user_direction`。本轮用户允许修正三处 QA 行长后恢复 A/B，原七文件和 control-space-v1 授权持续有效；“验证失败即停止”仍适用。本轮已完成 A 并写入 B 产品/测试适配，但 B 验收未完成，原空间 P1 尚未关闭，Step6不能收口。未进入Step7/完整quality/额外核心性能批次，未提交、推送、PR、合并、部署或删除资源。

A执行前修复三处E501，统一Ruff check/format --check通过。A冻结97文件SHA256=ce9959c6a011257125bb4efa950dfc1b6a860e007428d88332fbe4cd2863817d；候选75 passed/0 skipped，271路径在创建前登记，54个可选current别名未创建，boundary_violations={}。固定三种子×serial/fifo/lifo/recovery共12对布局均完整逻辑等价，occupied实际节省8192或12288字节，每对达到两页晋级标准；未换种子、重跑或选取有利结果。24布局库及54个用例库均全新，未复用旧SQLite。

A布局页数/字节守恒、完整scope、非空迁移、坏数据拒绝、PK/FK/CHECK、九故障节点回滚均通过。A结果属于上述执行快照；随后B改变产品及部分测试，不能据此声称最终98文件上的所有用例已经通过。A的候选SQL和固定输入未因B调整，实际迁移文件与A草案逐字节相同；完整control工作量≤256KiB及B产品语义仍待验证。

B本轮实际改动限七文件：sqlite_control.py新增v9登记、原生unhex检查、三个完整scope的严格编码/匹配及BLOB查询/写入；新增0009_provider_permit_scope_storage.sql事务重建，全部值/行/约束/索引/FK保留；test_sqlite_control.py补升级、回滚、坏数据、并发/归属/release用例，历史v8专项明确固定前八migration；budget/retry测试仅更新当前版本期望；两个QA文件增加B入口及其必要测试适配。具体代码见前节“B实现冻结”。

当前schema STRICT断言同步补强为PRAGMA table_list的表名列row[1]，并校验完整表集合，避免schema列row[0]造成空集断言；属于授权迁移验证范围，不放松旧门禁。候选fixture在每个测试作用域绑定到本用例tmp_path，便于后续完整QA在新根运行，QA_ROOT/native例外不扩展。原14 migration字节/哈希未改，唯一新增v9 SHA256=5411728141759627130e7b5032f665430bbe19fb57e001a23707a91a21dbd342，与A草案完全一致。没有修改既有性能runner、依赖、CI、统计协议或阈值。

B实际只执行静态前两项：六个授权Python文件Ruff check --no-cache exit0；format --check --no-cache exit1，五文件已格式化、一文件未通过。失败位于backend/tests/test_f009_step6_qa.py:154—162、215—223的换行字节：全文件2376行CRLF与18行LF混合，18行位置与本轮局部格式化补丁一致。显示内容相同的diff不是产品语义失败，也不能算format通过。代理的文本模式格式化/局部patch写回没有保证换行字节一致，这是本轮QA编辑流程缺陷。

按用户硬停止，本轮未修正该问题或重跑B；mypy、schema、22文件pytest、三个独立evaluator均未执行。pytest-semantic-01尚未创建，三个evaluator文件不存在。B仅写入已预登记的semantic-summary.json记录exit1/passed=false；资源边界违规{}、39旧缓存不变。该失败摘要保留，不能在后续恢复时覆盖或假称不存在。完整quality、quality-13和新的正式性能额度未启动，原full-matrix-01失败证据继续保留。

停止后仅执行只读代码/文件身份/资源核对并更新五份正式文档。最终98文件SHA256=e23f657acf24af29f4a65543f6cdec4771e1f9cf4fee9b42b24d20fe63d6ce59，与B执行前一致；相对A仅七授权文件变化，其余91文件不变；相对本轮最初97文件仅六已有文件变化和一新migration。feature37 tracked modified/61 actual untracked，正式仅五文档修改，两处staged0；branch、HEAD和本地origin/main仍为原值1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3。不得将该未通过快照标作step_6_complete。

资源最终盘点：QA根10024文件/8756目录（含根）/1579919128字节；8208 .sqlite3、12 .db、155 WAL、155 SHM、61嵌套Git、70只读文件、13 synthetic .env名称、10测试key、reparse0。本轮control-space-v1为82文件/96目录/14164396字节：78个SQLite及4个JSON，无留存WAL/SHM、无嵌套Git、无key/.env/只读文件；实际子路径在创建前登记，完整目录清单附于evidence。本轮QA净增82文件、96目录、14164396字节，无其他根新增。A已关闭SQLite的sidecar登记与闭库后不存在分别保留，不为凑文件数重建。

39旧缓存metadata SHA256=cd441f082436fb555a4951c684e0f230ea36102c04e4c1caa999569caed744e5不变；10个既有测试key仅元数据且身份/大小/mtime不变，未读取/哈希内容。默认三库及sidecar24路径不存在；V30—V33经只读检查仍不存在，不重建。A/B入口及静态子进程已结束，本轮未启动应用HTTP服务。

仍在使用：正式/feature工作树和既有Step5工具链。明确保留：B未验收代码、control-space-v1的A通过证据与B失败摘要，以及所有旧QA/quality12/full-matrix01/SQLite/缓存/V29/分支。无本轮到期删除项。用户已删除：V30—V33。历史Codex获准删除说明保持原台账；本轮删除0、回收0字节，不能把上述证据当可自动清理资源。

简短复盘：本轮编辑准备曾因未显式UTF-8读取源码遇到GBK解码错误，未写入文件后改为显式UTF-8；最终阻塞进一步暴露了“字符相同不等于原始换行字节一致”。今后源码格式化落盘应对单个授权文件采用一致换行、保留内容，不能靠文本模式的局部差异忽略EOL。本次仅登记此改进规则，未在硬停止后改代码或全局配置。

准确下一步：获用户恢复指示后，仅统一test_f009_step6_qa.py这18行换行，再执行B静态门禁及剩余专项。pytest-semantic-01仍全新可用；不得重跑A矩阵、复用A SQLite或覆盖semantic-summary.json。恢复入口须在本已授权根下预登记一个新的B汇总文件名（建议semantic-summary-02.json），保留旧失败摘要后继续，不能借此执行第二性能批次。当前尚未适配或创建该文件；无需重新批准七文件范围、目录或quality-13。

## 2026-09-03：B 实现冻结，开始一次专项验证

B执行快照：98文件SHA256=e23f657acf24af29f4a65543f6cdec4771e1f9cf4fee9b42b24d20fe63d6ce59，相对A执行快照仅七个授权feature文件变化（六现有文件加唯一v9migration）。产品migration原始字节与A验证草案完全一致，SHA256=5411728141759627130e7b5032f665430bbe19fb57e001a23707a91a21dbd342。原14migration、既有runner、依赖、CI、工作量和门禁不改。

实现：provider_permits三列完整scope使用BLOB32；active统计与INSERT同样编码，已有permit独立匹配二进制值，admission/预算TEXT匹配不变。初始化在变更schema前检测原生unhex；v9事务重建、约束/索引/FK/所有行保留。已增加真实产品升级、八个DDL故障节点、坏旧数据/不支持unhex拒绝、三轴归属、独立写入连接竞争及五种release幂等用例；历史v8专项显式固定前八migration并保留原检查。

为保证新migration断言实际有效，当前版本STRICT检查改用PRAGMA table_list正确的表名列row[1]，并增加表集合非空/完整相等断言，避免旧row[0]（schema名）筛选出空集合。此改动属于已授权test_sqlite_control.py的迁移验证补强，没有放松断言。新候选测试fixture只在自身测试作用域内绑定SPACE_ROOT到当前tmp_path，以保持严格归属且可在后续获批完整quality的全新basetemp执行；不扩大QA_ROOT或native例外。

B精确入口：scripts.f009_step6_qa.run_space_semantics，经command_scope和现有ResourceGuard/子进程双层隔离。先对六个授权Python文件运行Ruff check及format --check，再运行mypy backend/src backend/tests scripts及contracts.export --check；随后仅在全新control-space-v1/pytest-semantic-01执行22个相关测试文件，摘要为该basetemp/qa-summary.json，实际所有子路径创建前登记。通过后再启三个独立evaluator进程，各输出evaluator-process-01/02/03.json，外层汇总semantic-summary.json。仅Python工具/精确无缓存只读Ruff，不启用Git/Godot/uv原生操作。

22文件为：test_sqlite_control、test_budget_control_step3、test_retry_breaker_step4、test_f009_step6_qa、test_safety_step1、test_safety_control_step2、test_dialogue_control_step2、test_control_evaluation_step5、test_control_performance_contract_step5、test_async_sqlite、test_sqlite_connection_lifecycle、test_dialogue_async_persistence、test_async_persistence_api、test_multi_npc_adversarial、test_multi_npc_isolation_matrix、test_multi_npc_dialogue、test_long_term_dialogue_integration、test_long_term_memory_application、test_long_term_retrieval、test_sqlite_long_term_memory、test_sqlite_observability、test_observability_step5（均backend/tests/*.py）。这不是完整quality，也不运行统一核心性能批次。

当前上述B门禁尚未执行，不宣称通过；任一失败即停止，不复用失败basetemp或追加执行。所有A/B资源保留，无删除；完整quality、额外正式性能额度、Step7仍未授权进入。

## 2026-09-03：SPACE-01 A 通过，进入已授权 B 产品适配与专项回归

当前状态：`step_6_in_progress / space_A_passed / space_B_in_progress`。三处 QA 行长已修正，Ruff check/format --check 均通过。A：75 passed、0 skipped、boundary_violations={}，pytest创建前登记271路径、54个可选current别名未创建。固定12对布局全部逻辑等价，每对occupied节省8192或12288字节，全部达到8192字节候选标准；v8→候选迁移、完整字段、坏数据拒绝、九故障节点回滚和页字节守恒通过。没有重试、换种子或追加正式性能批次。

A执行冻结97文件SHA256=ce9959c6a011257125bb4efa950dfc1b6a860e007428d88332fbe4cd2863817d；A后再算完全一致。新根E:\Agent\cyber-town-f009-step6-qa\control-space-v1已启用，layout-plan.json、layout-summary.json、pytest-layout-01/qa-summary.json及本次24个布局库/sidecar均在操作前登记。所有A资源保留，不复用其中SQLite继续B。

按已批准条件进入B，只允许原七个feature文件：sqlite_control.py、唯一新增backend/src/cyber_town/infrastructure/control/migrations/0009_provider_permit_scope_storage.sql、test_sqlite_control.py、test_budget_control_step3.py、test_retry_breaker_step4.py、scripts/f009_step6_qa.py及test_f009_step6_qa.py。新migration将使用A实际验证的SQL草案，原始UTF-8 SHA256=5411728141759627130e7b5032f665430bbe19fb57e001a23707a91a21dbd342；旧14migration不改。B使用全新pytest-semantic-01及三个独立evaluator摘要，实际子路径仍创建前登记。

A仅证明固定合成生命周期的无损布局与迁移，不等于完整control工作量增长≤256KiB，也不替代B产品语义或完整quality/正式性能。B或任何验证失败即停；完整quality、新正式性能额度和Step7均不执行。当前原SPACE-01门禁缺陷尚未最终关闭。

## 2026-09-03：获准修正三处 QA 行长并恢复 SPACE-01 A/B

当前状态：`step_6_in_progress / space_A_prevalidation_resumed`。用户明确允许修正三处 QA 行长错误后恢复已授权 A/B，原七文件和 control-space-v1 范围有效，不需 quality-13；验证失败即停止及其余边界保持。

恢复前 97 文件 SHA256=794340bc3f2a9c2b191fa278aa44dc344e44dcc863ff229e48b0d3125f2961f4 完全匹配；双方 branch/HEAD/origin/main/staged 未变；新根和 quality-13 不存在、canonical/完整父链无 reparse。仅修正两 QA 文件的三处 E501：SQL 字符串拆行且运行时查询内容相同，候选常量仅缩短注释，不改变 DDL。修正后 97 文件 SHA256=ce9959c6a011257125bb4efa950dfc1b6a860e007428d88332fbe4cd2863817d；候选 SQL 草案 SHA256=5411728141759627130e7b5032f665430bbe19fb57e001a23707a91a21dbd342。其余 95 文件与历史 14 migration 保持，产品 v9 文件尚未创建。

先执行既有统一静态门禁，通过后只启用 control-space-v1 执行 A。固定 146 个设计路径沿用前节清单；运行时仍须 ResourceGuard 在操作前将准确子路径同步登记正式 evidence，之后才创建。先候选 pytest，再固定三种子/四调度的 12 对布局验证；每对 occupied 节省至少8192字节且逻辑等价、约束/回滚通过才可晋级。A 全部通过后才实施 B；失败立即停止，不重试、换种子或申请递增根。当前尚无 A/B 新通过结论。

资源仅 synthetic Python/SQLite 与脱敏结果，完整父链、身份/归属、TEMP/缓存、子进程隔离与退出恢复不变；无新增 native 动态例外。仍使用工作树/既有工具链，保留所有既有QA/SQLite/缓存/分支，无到期删除项；V30—V33 不存在记录保持，不重建。本轮不删除资源，不执行完整quality、新正式性能批次或Step7。

## 2026-09-03：SPACE-01 A/B 已获批；A 启动前 QA 静态检查失败并硬停止

当前状态：`step_6_blocked / space_A_qa_lint_failed / awaiting_user_direction`。用户已批准专项方案 A/B、列明七文件、三列 HMAC 无损编码/v9 migration，以及全新 E:\Agent\cyber-town-f009-step6-qa\control-space-v1；同时明确“验证失败即停止”。授权范围持续有效，但本轮已触发停止条件。当前未执行固定 12 对布局验证，未进入 B；SPACE-01 产品空间 P1 尚未修复，Step 6 未完成，Step 7 未开始。此节为最新结论，下方保留方案及全部历史。

执行前复核通过：97 文件冻结 SHA256=39790f6b181fa508c1677ae79c39ae9fc7a4c189612936d0dc5ce461576886d5 逐项一致；正式 main、feature feat/f-009-safety-cost-performance，HEAD/本地 origin/main 均为 1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3，staged0；新根和 quality-13 不存在，完整父链 canonical/无 reparse。

本轮仅修改 scripts/f009_step6_qa.py 与 backend/tests/test_f009_step6_qa.py：编写固定三种子/四调度输入、v8 全新合成库构建、候选事务迁移草案、全部应用列/行的规范化摘要、逐对象页守恒/空间统计和 A 阶段入口；补充迁移九个故障节点、坏数据/约束/资源边界用例。新代码尚未通过验收。产品 sqlite_control.py、既有预算/retry/SQLite 测试、所有历史 runner/SQL 与 14 个 migration 均未改，0009 migration 文件未创建。

代码格式化准备使用既有 Ruff，经统一隔离入口的精确只读 stdin 白名单；仅返回格式化文本，由代理在两个授权 QA 文件应用，不增加原生动态文件类别或 native 根。首次 stdin 文本传输遇到 Windows 默认 GBK 无法编码源码 Unicode 的错误；未生成输出文件、未启动候选测试。随后显式 UTF-8 完成此编辑准备，未改变产品或测试结果。

正式静态检查由现有 run_static_checks/command_scope/subprocess_isolation 执行：Ruff check --no-cache exit1，三项 E501：
- backend/tests/test_f009_step6_qa.py:99，105 > 100，UPDATE SQL 字符串。
- scripts/f009_step6_qa.py:1604，105 > 100，候选 SQL 常量首行注释。
- scripts/f009_step6_qa.py:1904，106 > 100，逻辑摘要查询字符串。

检查发现的是代理本轮新增 QA 代码问题，不能据此否定原产品或宣称候选编码方案无效。按用户“验证失败即停止”，没有修正后重跑、没有继续第二条 format --check 命令；mypy/schema、候选 pytest、12 对布局、B 产品落地、独立 evaluator、完整 quality 和新性能复验均未执行。静态门禁记录 protected_cache_entries=39、protected_cache_unchanged=true、boundary_violations={}。只读 stdin 格式化的完成不等于 format --check 或 lint 通过。

停止后仅作只读代码/资源核对和正式五文档更新。最终 97 文件 SHA256=794340bc3f2a9c2b191fa278aa44dc344e44dcc863ff229e48b0d3125f2961f4；相对本轮开始仅两 QA 文件变化，其余 95 文件/文件集合/branch/HEAD 不变，feature 37 tracked modified/60 actual untracked，staged0。原 14 migration 哈希不变。39 旧缓存元数据 SHA256=cd441f082436fb555a4951c684e0f230ea36102c04e4c1caa999569caed744e5 不变。

实盘资源核对：QA 根 9942 文件、8660 目录（含根）、1565754732 字节；8130 SQLite3、12 .db、155 WAL、155 SHM、61 嵌套 Git 目录、70 只读文件、13 synthetic .env 名称、10 测试 key、reparse0，与上轮数量/字节一致。key 仅元数据且身份/大小/mtime 与前次一致，未读取或哈希内容。本轮 QA 净增文件/目录/字节均为 0；control-space-v1 与 quality-13 仍不存在，未创建候选数据库、摘要或新测试根。既有数据库未打开或复用；资源核对仅 lstat/路径元数据，既有工具/源码哈希按授权读取。

仍在使用：正式/feature 工作树和 Step5 既有工具链。明确保留：两个 QA 文件的未通过草稿、全部旧 QA/quality12/full-matrix01、数据库/sidecar/缓存/V29/分支。没有本轮到期删除清单；用户已删除的 V30—V33 经只读检查仍不存在，不重建。历史 Codex 获准删除说明保持原台账，本轮删除0、回收0字节。不创建或申请递增修复根来处理本次格式错误。

简短复盘：自动格式化不负责拆分所有 SQL 字符串/多行常量，代理新增代码未在编写时遵守行宽，导致启动前 lint 阻塞；Windows 默认管道编码也不适合含 Unicode 的源码。以后此类编辑准备显式使用 UTF-8，并在生成 SQL 字符串/注释时直接满足行宽。这个错误属于 QA 实施准备不足，应修正原两文件，不应转化成新 quality 目录审批。这里只登记复盘，未修改全局规则或扩大权限。

准确后续动作已定位：仅拆分上述两条 SQL 字符串、调整候选常量声明/注释的行宽，保留 SQL 语义；登记两 QA 文件的新指纹后重新执行静态门禁，再按已批准 A/B 顺序继续。因本轮硬停止，需用户指示恢复；七文件范围和 control-space-v1 授权无需重新批准，quality-13 与新的正式性能额度仍不在本轮执行范围。

## 2026-09-03：SPACE-01 专项修复方案已制定，待批准实施

当前状态：`step_6_blocked / control_storage_growth_fix_plan_ready / awaiting_fix_plan_authorization`。用户本轮仅要求针对空间超限制定独立方案，无需先批准 quality-13。方案全文见本目录 implementation-plan.md 顶部“QA-F009-SPACE-01 空间超限专项修复方案”；准确资源及验证边界同步登记于 evidence.md。本节是最新结论，以下保留全部历史。

现有 P1：默认 control 与三 SQLite 组的 control 增长中位数均为 260 KiB，超过 256 KiB。相同批次的失败/通过样本唯一占页差异在 provider_permits（9 对 8 页）；具体页分裂因果尚未完全验证。quality-12 已通过 2242 tests / 133 expected skips，其中独立 QA 243 passed；这些事实与空间失败同时保留，Step 6 尚未完成。

推荐候选：仅将 provider_permits 三列完整 HMAC 从 TEXT64 无损编码为 BLOB32，应用层仍为原字符串，保留完整位数、全部 permit、归属校验、约束、索引、并发与恢复语义。100 行原始值预计节省 9600 字节，实际页数与完整工作量门禁尚未验证。六个现有 feature 文件加一个 append-only v9 migration 的准确范围、事务重建与兼容性风险已列明；历史 14 个 migration 原字节保持。

拟议顺序为 A 固定三种子×四调度的 12 对布局/迁移预验证，B 通过后落地产品并完成专项语义/故障/三进程 evaluator，C 后续新冻结指纹上的完整 quality 与单独获准的一次额外固定性能复验。A 每对至少节省两页作为候选余量标准，不更改正式阈值；合成布局证明不替代产品和性能验收。任何阶段失败停止，不能追加种子、复用失败根或增批寻找通过。

A/B 唯一拟议新根为 E:\Agent\cyber-town-f009-step6-qa\control-space-v1，目前不存在、尚未获准创建；仅 Python 专项资源，不扩大原生动态例外。可在后续一次修复授权中同时批准列明七文件、物理编码例外和该根，有条件连续完成 A/B。当前无需批准 quality-13；原 full-matrix-01 的唯一性能额度已用完，修复后新的正式性能复验必须另获明确额度/资源授权。不得进入 Step 7 或 Git 交付。

本轮仅只读审查及正式五文档更新；feature 97 文件冻结 SHA256=39790f6b181fa508c1677ae79c39ae9fc7a4c189612936d0dc5ce461576886d5 与计划前逐项一致；双方 branch/HEAD/origin/main 保持既有值，staged0。拟议修复根和 quality-13 均不存在，完整父链 canonical/无 reparse。没有修改产品/QA/SQL，没有创建新磁盘库、候选根或性能批次；仅以纯内存 SQLite 标量检查确认本机 3.47.1 的 unhex 能力，尚未验证候选 DDL/迁移、CI 兼容或空间收益。

所有现有资源继续保留。本轮未生成新的 QA 文件/目录，未删除任何资源，回收 0 字节；沿用 quality12 收口清单（QA 根 9942 文件/8660 目录/1565754732 字节，其中 full-matrix01 199 文件/43 目录/20454979 字节），这些为上轮实盘统计，本轮未重新全盘盘点。V30—V33 的既有不存在记录保持，不重建。旧 83 文件表、28 个哈希缺失及全部 quality/性能历史不改写。


## 2026-09-03：quality12完整通过；唯一性能复验control空间超限

当前状态：`step_6_blocked / control_storage_growth_gate_failed / awaiting_separate_fix_authorization`。Step5及此前单独授权的预算投影/retry修复保留已完成事实；Step6的完整quality已经通过，当前P1为性能空间门禁失败。不得标记step_6_complete，不进入Step7、提交、推送、PR、合并、部署或删除。

用户本轮批准全新E:\Agent\cyber-town-f009-step6-qa\quality-12沿用既有例外，以新增诊断定位connectivity后继续剩余验收。预检97文件9f18b5372ce95983d33c446b489bffe037ed91368c1cc3130dbfabecb9a1f5b2完全匹配；仅两QA文件将quality11→12绑定，最终执行冻结SHA256=`39790f6b181fa508c1677ae79c39ae9fc7a4c189612936d0dc5ce461576886d5`，其余95及文件集合不变。产品、既有runner/测试、14 migration、SQL、依赖、CI、工作量与阈值本轮均未修改。

**完整quality通过**：2242 passed / 133 expected skipped，其中backend/tests/test_f009_step6_qa.py为243 passed。lock、Ruff、mypy、schema、Godot import/unit、connectivity、Dialogue/Multi-NPC、完整pytest九命令exit0，前后ignore/sensitive均通过。connectivity九场景均有通过marker，failed marker/失败类别为空。quality11 exit1没有复现，原始诊断已丢失，根因不能还原；保留“未复现/原因未明”历史发现，不声称根因已定位或修复，不为它继续追加尝试。本次实际全量通过与历史失败分别保留。

133 skip分别为attribution V7/V9 45、budget V10 53、projection V14—V19 33、dialogue async V8 2；均为旧一次性实验根/诊断开关未启用，与既有登记一致。未启用历史候选、未复用旧SQLite、未新增skip掩盖产品失败。pytest创建前登记4392路径，1082个非必要current别名未创建，boundary_violations={}。native监测53826事件、completed=true、unknown=[]、reparse0、overflow=false；31 game源/副本哈希、1043个summary生成前文件身份/大小一致，40个SQLite退役通知及89个原生瞬态路径有记录，无uv退役或rename回退命中。quality owner PID52644已结束。

**唯一固定性能批次已消费并失败**：E:\Agent\cyber-town-f009-step6-qa\full-matrix-01，原runner统一warm-up1+正式5，不追加批次。43目录/265文件表（含66套SQLite主文件/WAL/SHM/journal和summary）事前登记；实际执行注册308路径，guard违规{}，性能输出根与独立客户端配置退出恢复，39旧缓存不变。真实本地TCP+独立客户端，18次HTTP运行（3配置各1+5），全量正式逐请求样本保留于performance-summary.json。runner exit1，failure_codes=[runtime_default_control_database_growth_exceeded]，warning_codes=[]。

P1发现QA-F009-SPACE-01：默认control-on+NoOp的control增长五轮为260、260、256、260、260 KiB，中位数260 KiB，上限256 KiB，超4 KiB/一页。warm-up同为260 KiB。按冻结口径max(main增长, occupied增长, 0)计算；典型初始main144 KiB/occupied128 KiB，结束main/occupied388 KiB，故main增长244 KiB、occupied增长260 KiB。不能改用只算主文件增长来通过，也不能挑唯一256 KiB那轮。业务库每轮60 KiB单列、不计control+observability合计。

同一P1亦影响三SQLite组：control五轮260、256、256、260、260 KiB，中位260 KiB，仍超独立control空间上限；observability为420、432、420、436、432 KiB，combined中位688 KiB，后两项通过。runner自身diagnostic_codes仅列three_sqlite_p95_exceeded、three_sqlite_p99_exceeded；这两项延迟趋势按授权非阻塞，独立QA另将control空间超限列为阻塞，不以“非阻塞诊断”豁免空间门禁。

默认HTTP聚合p95/p99=237.7786/299.2949ms、吞吐12.826782/s，on-off p95差93.2436ms；in-memory p95/p99=2.9363/4.6332ms，差0.1651ms，配对吞吐94.0893%；SQLite observability p95/p99=99.7916/121.0466ms、13.409294/s，增长300 KiB；rate/budget/breaker reject p95=2.8685/2.3158/1.8794ms、dispatch0。以上按冻结“五轮统计中位数”门禁通过，不等于每轮均低于阈值；逐轮慢样本完整保留。三SQLite诊断p95/p99=596.7714/792.5274ms、5.956505/s，不宣称生产容量。

失败后仅做只读核对，没有修复、重跑或追加性能。66新库（business18/control36/observability12）integrity=ok、FK0、WAL/FULL、主文件身份/哈希不变；HTTP business每库100状态/事件/独立请求，control-on每库100 admission/permit/owner/reservation/settlement/settled intent且join一致，fake成本0、projection副本一致；12 observability库各100完整trace、dispatch100、成本0、1400 stage且每trace14阶段，NoOp无observability SQLite。QA243项包含真实长期磁盘写入/遗忘/替换/restart和scope，不用性能基准的空长期表代替该语义覆盖。

只读物理页归属进一步比较本批loopback-on-1和loopback-on-3：总页97对96，完整字节守恒、未知页0、freelist0，所有表行数相同；唯一物理占页差异在provider_permits，9页/36864bytes对8页/32768bytes，同为28800 payload bytes，无overflow。页利用率/分配差异解释本对样本一页差距；实际插入/更新顺序与页分裂因果、稳定修复方式尚未验证。不将它未经验证地归因于0008预算投影修复，不删除审计行、修改标识符分布、重排固定基准或放松约束找通过。

原Step6语义424 passed/55历史skip、独立114和retry alignment18，以及三个独立进程25-case evaluator（25/25、11维度、digest=1986a20db79cce74dfe458193ce0f2ab52e0d457d047b31d2e9465aeadf624bb）保留；本批完整pytest重测了当前QA/产品测试，不把上述旧专项与2242相加。违规原文、重复写入/计费、未授权dispatch、scope leak与非零fake成本按已完成的独立QA/evaluator均为0。当前性能P1未关闭，因此Step6不能收口通过。

正式/feature branch、HEAD及本地origin/main均保持预期1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3；正式main仅五文档修改，feature37 tracked modified/60 actual untracked，两处staged0，tracked diff-check和60 untracked whitespace通过（11条仅换行提示）。14 migration原始哈希一致，39旧缓存metadata SHA256=cd441f082436fb555a4951c684e0f230ea36102c04e4c1caa999569caed744e5。默认三库及sidecar24路径不存在；8000/8001及18个性能HTTP端口共20端口无监听。旧9 key仅metadata且不变，本批新key仅精确批准路径原生生成，Python未读/哈希/复制/使用。

资源最终盘点：QA根9942文件、8660目录（含根）、1565754732bytes（1493.220 MiB）；8130.sqlite3、12.db、155 WAL、155 SHM、61嵌套Git目录、70只读文件、13 synthetic .env名称、10测试key，reparse0。quality12为1044文件/1407目录/151098618bytes；full-matrix01为199文件/43目录/20454979bytes（66SQLite、66 WAL、66 SHM、1summary）。本轮净增1243文件/1450目录/171553597bytes。仓库外QA资源无tracked Git归属；嵌套Git仅synthetic测试。正式ignored14723（.env名称1）、featureignored67（.env名称0），仅元数据盘点未读取真实.env。

仍在使用：正式/feature工作树、Step5工具链、Step6根/失败证据。明确保留：quality12、full-matrix01、旧quality/探针/SQLite/缓存/V29和分支。无本轮到期删除清单；用户已删除的V30—V33仍不存在，不重建。历史Codex获准删除说明保持旧台账，本轮删除0/回收0bytes。当前建议保留全部证据，不提出手动删除命令；收口后如需删除，由用户另行手动处置，不能从Git恢复这些数据库/摘要。

下一步不是批准quality13。按原“既有产品/测试/runner缺陷硬停止”规则，需要单独授权QA-F009-SPACE-01的最小修复设计/受控验证。焦点为provider_permits的持久化行宽、acquire/release/recover更新路径及页分配，保持所有历史migration、标识符/归属/permit语义、WAL/FULL、安全检查、事务和256/512/768KiB门禁。任何新增schema/物理编码、产品文件变更及新的性能复验必须先给出准确方案、文件和资源并另获授权；本轮未创建新修复根、quality13或第二性能批次。

关于连续quality目录的复盘：这些编号是同一Step6完整验收的独立证据/缓存/SQLite批次，不是新的开发阶段。逐根批准来自用户全新目录、失败保留、原生例外绑定精确路径的边界；频繁重启主要来自新增QA隔离工具在Windows文件通知、子进程和证据登记组合上的准备不足，不能全归为Step5产品失败。改进已落实：正式台账地址固定、原生事件严格分类、actual child_entrypoint验证、固定枚举诊断；本批完整调用链最终通过。后续先把QA工具组合验证充分，不靠反复申请新目录试运行；安全边界和长期规则本轮未改变。


## 2026-09-03：quality12获批，使用脱敏诊断定位connectivity并恢复Step6验收

当前状态：step_6_in_progress / quality_12_authorized。用户批准全新E:\Agent\cyber-town-f009-step6-qa\quality-12并沿用既有例外。执行前97文件SHA256=9f18b5372ce95983d33c446b489bffe037ed91368c1cc3130dbfabecb9a1f5b2完全匹配；双方branch/HEAD/origin/main保持1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3、staged0；quality12及full-matrix01均不存在，canonical/完整父链无reparse，39旧缓存metadata SHA256=cd441f082436fb555a4951c684e0f230ea36102c04e4c1caa999569caed744e5不变。

只切换scripts/f009_step6_qa.py和backend/tests/test_f009_step6_qa.py的quality11→12绑定，其余95文件冻结。复用已完成probe04；新批次纳入正式evidence地址稳定、实例重放输出与child_entrypoint多层审计修复，验证Godot/Python已登记改名、uv退役通知、Windows asyncio入口、SQLite通知与pytest便捷别名边界，并执行原完整quality。所有质量和资源门禁通过后才执行唯一固定warm-up+5-run核心性能，不调整协议、阈值或工作量，不增批找通过。仅Step6，既有产品/测试/runner缺陷硬停止，不进入Step7或Git交付。

本根资源属F009-Step6：tmp、cache/mypy、cache/uv、cache/ruff、pytest、31文件game副本、appdata、localappdata、git-template/info/exclude、native-monitor-ready.json、native-monitor-drain.marker、quality-summary.json、pytest-summary.json、native-summary.json。Python实际子路径由ResourceGuard在创建前同步精确登记。原生动态类别预登记：game/.godot、appdata/Godot、localappdata/Godot、pytest/**/.git、cache/uv；运行期记录并在结束逐路径核对。仅该根appdata/Godot/keystores/debug.keystore允许Godot原生生成，Python禁止读取/哈希/复制/使用内容、仅metadata核对。不启用其他原生类别，不复用失败根或旧SQLite，不联网、不安装。

所有新旧资源均保留至Step6收口后由用户手动处置；属于synthetic/fake/工具缓存或脱敏metadata，测试key例外如上。V30—V33旧根不存在仅登记、不重建。quality11及历史失败记录保留，完整quality和性能当前尚未通过。

保留quality11 connectivity exit1且根因未明的事实。新批加入固定错误类别/九场景枚举诊断；未知输出不推断根因、不保留原始文本。不能以新一批通过宣称quality11根因已定位或修复；先处理失败证据，再继续后续门禁。


## 2026-09-03：quality11在connectivity停止；QA诊断补充22项通过

当前状态：`step_6_blocked / connectivity_failure_unclassified / awaiting_fresh_quality_12_authorization`。Step5、预算投影一致性修复及retry v8保持完成；Step6尚未完成，Step7未开始。本节是当前结论，下方保留历史批准、失败与修复记录。

本轮执行前97文件SHA256=19c85cb32bc0cd9cf6debd69f8f4998599c30ccf0cf20408975ff99183588275匹配。仅切换两QA文件quality10→11绑定后，执行快照为c6279737078700c17d3e2b137f67eb0911e182a82581fb01c54d1192cc0bc54d。quality11实际通过preflight ignore/sensitive以及lock、Ruff、mypy、schema、Godot import、Godot unit六命令；connectivity exit1，error_classes/boundary_codes均空。Dialogue/Multi-NPC、完整pytest及final ignore/sensitive未到达。原始stdout/stderr没有保留，具体失败场景与根因不能从现存证据还原；不据此宣称产品有缺陷、资源越界或只是偶发错误。

native-summary的completed=true仅表示资源观察完成：186事件、unknown=[]、reparse0、overflow=false，31个game源/副本哈希及53个留存文件身份/大小核对通过，18个原生瞬态路径已记录；没有退役SQLite/uv例外或改名回退命中。quality仍失败。PID52548已结束，8000/8001无监听；24个默认SQLite主文件/sidecar路径均不存在。

确认QA诊断缺口：既有connectivity.main将异常包装为普通提示，而QA只提取traceback式错误；故失败只剩exit1。沿用两QA文件授权，仅在scripts/f009_step6_qa.py加入内存输出白名单分类（固定场景名、固定错误类别、失败提示布尔值），在backend/tests/test_f009_step6_qa.py增加合成正负/未知/脱敏用例。退出码、硬停止、原测试断言、路径/父链/reparse/身份/资源归属、原生授权与作用域恢复不变。未修改既有connectivity runner、产品、SQL/migration、依赖、CI、工作量或阈值；此补充没有修复或解释quality11的实际失败。

通过实际child_entrypoint多层审计执行22项诊断用例：22 passed/0 skipped、boundary_violations={}。用例为纯函数，无basetemp实体创建；6251字节结果文件在创建前由两层guard分别登记。两QA lint/format、131个源文件mypy及两QA源码敏感信息扫描通过，39旧缓存metadata不变。最初lint三处行长提示已修正。未重跑原221项独立QA或完整quality，不将22项与历史结果相加。

最终冻结97文件SHA256=`9f18b5372ce95983d33c446b489bffe037ed91368c1cc3130dbfabecb9a1f5b2`。相对本轮开始仅两授权QA文件改变，其余95及文件集合一致；feature37 tracked modified/60 actual untracked/staged0，正式仅五文档修改。双方branch/HEAD及本地origin/main保持1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3；14 migration哈希、tracked diff --check、60 untracked whitespace检查通过。39旧缓存metadata SHA256=cd441f082436fb555a4951c684e0f230ea36102c04e4c1caa999569caed744e5；旧8个测试key只核对metadata且一致。

资源盘点：QA根8699文件、7210目录（含根）、1394201135字节（1329.614 MiB），含7301个.sqlite3、10个.db、78 WAL、78 SHM、47嵌套Git目录、53只读文件、10个synthetic .env名称、9个测试key，reparse0。quality11为54文件、31目录（含根）、42150424字节，其中1个工具缓存.db，无业务SQLite/WAL/SHM；native-summary自身34302字节不在生成前53文件计数内。另有诊断summary6251字节；本轮净增55文件、31目录、42156675字节。新测试key仅该批准路径原生生成，Python未读/哈希/复制/使用其内容。

仍在使用：正式/feature工作树、Step5既有工具链、QA根与证据。明确保留：quality11失败根、诊断summary、所有旧批次/数据库/缓存/分支及V29；本轮无到期删除清单。用户已删除：V30—V33仍不存在，仅登记不重建。历史由Codex获准删除记录保持原台账，本轮Codex删除0、回收0字节。全部本轮资源保留至Step6收口后用户手动处置，不自动清理。

原Step6语义424 passed/55历史skip、独立114项、retry alignment18项及三个新进程25-case evaluator的同一digest仍有留存证据，产品95文件未变；不声称本轮重跑。probe04已完成9命令，不重复执行。完整quality尚未通过，唯一固定warm-up+5-run性能未启动，full-matrix01不存在。只有全部验收条件满足才可标记step_6_complete / awaiting_step_7_authorization。

下一步为定位connectivity失败后继续Step6验收。全新E:\Agent\cyber-town-f009-step6-qa\quality-12目前不存在、未启用、未加入允许列表。需单独批准该根及相同Godot/Git/uv动态类别、精确debug.keystore例外，原因来自用户“全新目录、失败资源保留、原生例外绑定具体根”要求。获批后按最终冻结指纹检查，仅切换两QA绑定；使用新增脱敏诊断定位/复验，保留quality11失败，不能仅凭下一批通过宣称其根因已定位或修复。确认既有产品/测试/runner缺陷则硬停止等待单独修复授权。所有质量/语义/资源门禁通过并处理未解释失败后，才执行唯一性能批次和最终五文档收口；不进入Step7或Git交付。

重复流程复盘：连续批次因不同资源边界及审计组合停止，本轮又暴露错误包装与摘要格式不一致，导致失败不可定位。已落实的本地规则：通过实际child_entrypoint验证QA；真实资源登记地址固定；失败证据保留固定类别和场景枚举，未知情况明确留空。后续不以空错误列表当作“无问题”，不以新一批通过代替失败处置；不保留原始日志，不修改全局安全规则。


## 2026-09-03：quality11获批，恢复完整Step6验收

当前状态：step_6_in_progress / quality_11_authorized。用户批准全新E:\Agent\cyber-town-f009-step6-qa\quality-11并沿用既有例外。执行前97文件SHA256=19c85cb32bc0cd9cf6debd69f8f4998599c30ccf0cf20408975ff99183588275完全匹配；双方branch/HEAD/origin/main保持1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3、staged0；quality11及full-matrix01均不存在，canonical/完整父链无reparse，39旧缓存metadata SHA256=cd441f082436fb555a4951c684e0f230ea36102c04e4c1caa999569caed744e5不变。

只切换scripts/f009_step6_qa.py和backend/tests/test_f009_step6_qa.py的quality10→11绑定，其余95文件冻结。复用已完成probe04；新批次纳入正式evidence地址稳定、实例重放输出与child_entrypoint多层审计修复，验证Godot/Python已登记改名、uv退役通知、Windows asyncio入口、SQLite通知与pytest便捷别名边界，并执行原完整quality。所有质量和资源门禁通过后才执行唯一固定warm-up+5-run核心性能，不调整协议、阈值或工作量，不增批找通过。仅Step6，既有产品/测试/runner缺陷硬停止，不进入Step7或Git交付。

本根资源属F009-Step6：tmp、cache/mypy、cache/uv、cache/ruff、pytest、31文件game副本、appdata、localappdata、git-template/info/exclude、native-monitor-ready.json、native-monitor-drain.marker、quality-summary.json、pytest-summary.json、native-summary.json。Python实际子路径由ResourceGuard在创建前同步精确登记。原生动态类别预登记：game/.godot、appdata/Godot、localappdata/Godot、pytest/**/.git、cache/uv；运行期记录并在结束逐路径核对。仅该根appdata/Godot/keystores/debug.keystore允许Godot原生生成，Python禁止读取/哈希/复制/使用内容、仅metadata核对。不启用其他原生类别，不复用失败根或旧SQLite，不联网、不安装。

所有新旧资源均保留至Step6收口后由用户手动处置；属于synthetic/fake/工具缓存或脱敏metadata，测试key例外如上。V30—V33旧根不存在仅登记、不重建。quality10及历史失败记录保留，完整quality和性能当前尚未通过。


## 2026-09-03：quality10监测完成，evidence隔离修复221项通过

当前状态：`step_6_blocked / awaiting_fresh_quality_11_authorization`。Step5、预算投影修复和retry v8保持完成；Step6尚缺完整quality通过及唯一固定性能复验，Step7未开始。执行前97文件SHA256=c90a52065a8a0219334597354b223c2ee376c2586ced98f44b6667f76b503496匹配；只切换quality09→10绑定后的执行快照为3e5120fe60f6ceb0af795d847c56e957ab227b82200662b683943c16ed8a162d。

quality10前置ignore/sensitive及八项命令（lock、Ruff、mypy、schema、Godot import/unit、connectivity、Dialogue/Multi-NPC）通过。完整pytest为1222 passed/133 expected skipped/1 failed，其中失败前QA175项通过；失败为test_qa_uv_retired_notification_requires_observed_removal_and_stable_anchor[removed_leaf]，在validate_path第37行拒绝正式evidence目录写入。quality exit1，结束ignore/sensitive未执行。133 skip分布为attribution45（V7/V9）、budget-control53（V10）、budget-projection33（V14—V19）、dialogue-async2（V8）；对应产品/既有测试未修改，无新增skip，未启用历史实验根。

本轮原生监测正常完成：native-summary completed=true，26762事件、unknown_paths=[]、reparse0、overflow=false，31个game源/副本hash一致；16条退役SQLite记录、1条真实Godot改名记录、18条瞬态native路径。真实改名为game/.godot/editor/project_metadata.cfg8183650.tmp→project_metadata.cfg，旧路径再次严格校验且已不存在，根/父/目标身份核对通过。uv退役记录0，仅可记本轮uv lock通过。528个监测文件的size/device/file-id/hardlinks在最终只读盘点全部一致。completed只代表监测完成，不代表quality通过；摘要自身写入后quality10实际529文件。

P1（QA自测隔离缺陷，已修复并验证）：重放测试修改模块全局EVIDENCE，但完整quality先由child_entrypoint安装活动ResourceGuard，再运行QA脚本安装另一层guard。修改全局EVIDENCE改变了前一层对正式台账写入的识别，导致后一层合法预登记被拒绝。Python-only的pytest-evidence-repro-01通过同一child_entrypoint稳定复现1 failed、同一第37行；不依赖重新运行原生quality。

只修改两授权QA文件：NativeWatcher将既有native event/uv retired/rename metadata追加集中为实例方法，生产路径仍固定写正式EVIDENCE并flush；重放测试只替换自身观察器的输出，将模拟内容写入已预登记synthetic文件。全局EVIDENCE不再被测试替换，所有真实资源预登记继续写正式台账。新增活动guard下验证“真实登记进入正式evidence、模拟payload只进入测试文件”的用例，并在原uv/Godot重放用例中检查正式路径不变。没有改变validate_path、文件身份、原生授权、审计钩子或产品行为。

pytest-evidence-isolation-01采用与完整quality相同的child_entrypoint多层审计调用方式，最终221 passed/0 skipped、boundary_violations={}，1399路径事前登记、172个pytest便捷别名未创建，包含此前失败的uv用例。两QA lint/format与131个源文件mypy通过；mypy使用os.devnull且无缓存变更。初次lint的三处断言顺序提示已修正。专项通过不替代完整quality，不相加1222与221为通过总数；尚未在新原生quality批次完成修复后全链验收。

最终冻结97文件SHA256=19c85cb32bc0cd9cf6debd69f8f4998599c30ccf0cf20408975ff99183588275；相对c90a520仅scripts/f009_step6_qa.py与backend/tests/test_f009_step6_qa.py变化，其余95及文件集合一致。feature37 tracked modified/60 actual untracked/staged0，正式仅五文档修改。双方branch、HEAD与本地origin/main保持1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3；14 migration原始bytes指纹、tracked diff --check及60 untracked whitespace检查通过（11条仅换行提示）。39旧缓存metadata SHA256=cd441f082436fb555a4951c684e0f230ea36102c04e4c1caa999569caed744e5不变。产品、既有测试/runner、SQL/migration、依赖、CI、工作量与门禁均未修改。

QA根最终8644文件、7178子目录、1352044460bytes（1289.41MiB），7301个.sqlite3、9个.db、78 WAL/78 SHM、47个嵌套synthetic Git、53只读文件、10个synthetic .env*、8个测试key、reparse0。本轮新增857文件/1010目录/146260184bytes；quality10为529文件/751目录含根/104650703bytes，含448个.sqlite3、1个.db、5 WAL/5 SHM、1个synthetic .env*和1个新测试key，无嵌套Git；repro01为0文件/2目录含根，isolation01为326文件/257目录含根/41534644bytes，另两根级metadata摘要共74837bytes。native-summary生成前528文件/104468095bytes，摘要自身182608bytes，差异已核对。

新key仅在获批quality10/appdata/Godot/keystores/debug.keystore原生生成，2714bytes；7个旧key元数据完全一致，全部8个key均不读取/哈希/复制/使用内容。正式/feature24个默认DB surfaces不存在，quality10 owner44432及所属子进程已结束，8000/8001释放。feature ignored67，正式ignored14723（1个.env名称仅metadata）；QA根外层不属Git仓库，内部47个Git单列。全部新增资源逐路径台账见正式evidence，内容为synthetic/fake、工具缓存或脱敏metadata。

仍使用feature工作树与V13工具链；所有新旧QA、Step5历史根、工作树/分支/cache明确保留，当前无到期可删目标或删除建议，历史Codex获准删除台账无新增，回收0。V30—V33仍不存在，仅登记、不重建、不阻塞。原Step6独立语义424 passed/55历史skip、三个全新进程25-case evaluator和已完成probe04证据保留，不冒充本轮重跑，也不替代未完成的完整quality。

quality11和full-matrix01不存在，唯一固定warm-up+5-run性能批次未启动、未消费。依据用户“全新目录、失败资源保留、原生例外绑定具体根”的要求，quality10不可复用。下一步需批准全新E:\Agent\cyber-town-f009-step6-qa\quality-11及其既有动态类别/精确测试key例外；先复核最终97文件指纹与branch/HEAD，只切换两QA当前绑定，再完成完整quality及全部资源门禁。通过后才执行唯一固定性能复验，全部收口条件满足才标记step_6_complete / awaiting_step_7_authorization。

重复问题复盘：仅用直接启动QA脚本的专项验证，没有覆盖完整quality的child_entrypoint多层审计组合；测试全局替换evidence目的地破坏了真实资源登记。后续规则已落实在两QA文件：模拟输出只替换观察器实例的sink，正式台账全局地址保持稳定；相关验收使用实际child_entrypoint路径。修复未放宽路径或权限检查；独立专项结果继续与完整quality结果分别报告。


## 2026-09-03：quality10获批，恢复完整Step6验收

当前状态：step_6_in_progress / quality_10_authorized。用户批准全新E:\Agent\cyber-town-f009-step6-qa\quality-10并沿用既有例外。执行前97文件SHA256=c90a52065a8a0219334597354b223c2ee376c2586ced98f44b6667f76b503496完全匹配；双方branch/HEAD/origin/main保持1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3、staged0；quality10及full-matrix01均不存在，canonical/完整父链无reparse，39旧缓存metadata SHA256=cd441f082436fb555a4951c684e0f230ea36102c04e4c1caa999569caed744e5不变。

只切换scripts/f009_step6_qa.py和backend/tests/test_f009_step6_qa.py的quality09→10绑定，其余95文件冻结。复用已完成probe04；新批次验证Godot/Python已登记改名、uv退役通知、Windows asyncio入口、SQLite通知与pytest便捷别名边界，并执行原完整quality。所有质量和资源门禁通过后才执行唯一固定warm-up+5-run核心性能，不调整协议、阈值或工作量，不增批找通过。仅Step6，既有产品/测试/runner缺陷硬停止，不进入Step7或Git交付。

本根资源属F009-Step6：tmp、cache/mypy、cache/uv、cache/ruff、pytest、31文件game副本、appdata、localappdata、git-template/info/exclude、native-monitor-ready.json、native-monitor-drain.marker、quality-summary.json、pytest-summary.json、native-summary.json。Python实际子路径由ResourceGuard在创建前同步精确登记。原生动态类别预登记：game/.godot、appdata/Godot、localappdata/Godot、pytest/**/.git、cache/uv；运行期记录并在结束逐路径核对。仅该根appdata/Godot/keystores/debug.keystore允许Godot原生生成，Python禁止读取/哈希/复制/使用内容、仅metadata核对。不启用其他原生类别，不复用失败根或旧SQLite，不联网、不安装。

所有新旧资源均保留至Step6收口后由用户手动处置；属于synthetic/fake/工具缓存或脱敏metadata，测试key例外如上。V30—V33旧根不存在仅登记、不重建。quality09及历史失败记录保留，完整quality和性能当前尚未通过。


## 2026-09-03：quality09在Godot改名通知处停止，QA修复220项通过

当前状态：`step_6_blocked / awaiting_fresh_quality_10_authorization`。Step5、预算投影修复和retry v8仍完成；Step6完整quality、运行期资源门禁与唯一性能复验尚未完成，Step7未开始。quality09执行前97文件SHA256=6ea0c01ec1dbbd89ee198b00f6acc8574e714960b17b959fccf6cdf206618a2e匹配；只切换两QA当前批次绑定后，执行快照为1a71e879db707988b7dd9c88b28b6f66e7529929216618703da2be10f50e7263。

quality09前置ignore/sensitive及lock、Ruff、mypy、schema四命令通过。Godot import期间第136个事件后，action1的game/.godot/global_script_class_cache.cfg4303753.tmp首次resolve已返回同目录global_script_class_cache.cfg，触发step6_resource_canonical_mismatch。quality-summary exit1，仅记录四项通过；Godot import未计通过，后续Godot unit、connectivity、Dialogue/MultiNPC、完整pytest及结束ignore/sensitive未到达，native-summary/pytest-summary均不存在。uv lock本轮通过但retired_uv记录为0，不能声称本轮实际触发并验证了uv退役分支。

仅两授权QA文件修复通知改名竞态。接受范围为：当前批准根内既有Godot缓存/config/userdata类别的同目录“目标名+数字.tmp”改名，或源/目标两端均已精确预登记的Python改名；只接受create/modify/rename-old通知。原路径须重新严格校验且已不存在，目标及完整父链须严格canonical/无reparse，批次根身份不变，父目录和regular目标文件身份稳定、目标同卷且单hardlink。记录原名、目标名和身份metadata，不打开目标内容；实际访问validate_path、既有uv/SQLite通知规则、子进程隔离与作用域恢复均不放宽。

pytest-godot-rename-01为146 passed/1 QA failed，旧QA真实rename用例复现相同竞态（两端已登记source.tmp→target.dat），失败资源保留。补齐双端精确登记处理后，pytest-godot-rename-02为220 passed/0 skipped、boundary_violations={}；1397实际路径事前登记、171个pytest便捷别名未创建。新增26用例（6接受/20拒绝）覆盖Godot三类资源、创建/修改/旧名、Python双端登记及缺少任一端登记、错误根/目标/父链/设备/身份/reparse等。真实Python文件改名及通知测试通过；Godot场景用真实synthetic文件改名配捕获形态的通知重放，修复后的真实Godot import仍待全新quality根。

最终两QA lint/format和131个源文件mypy通过。补充mypy前两次命令因大写NUL不匹配mypy源码的os.devnull判断，被子进程guard在缓存目录创建前拦截；一次仅为显示traceback定位。改用os.devnull后通过，未关闭检查、创建仓库缓存或改依赖。初版格式问题也已在两QA文件内修正。失败尝试如实保留，不计为通过；不把多个批次的通过数相加为完整quality。

最终冻结97文件SHA256=c90a52065a8a0219334597354b223c2ee376c2586ced98f44b6667f76b503496。相对6ea0c01仅scripts/f009_step6_qa.py与backend/tests/test_f009_step6_qa.py变化，其余95和文件集合一致；feature37 tracked modified/60 actual untracked/staged0，正式仅五文档修改。两工作树branch、HEAD及本地origin/main保持1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3；14 migration原始bytes指纹一致，tracked diff --check和60 untracked whitespace检查通过（11条仅换行提示）。39旧缓存metadata SHA256=cd441f082436fb555a4951c684e0f230ea36102c04e4c1caa999569caed744e5不变。产品、既有测试/runner、SQL/migration、依赖、CI、工作量和门禁未修改。

资源最终盘点：QA根7787文件、6168子目录、1205784276bytes（1149.93MiB），6578个.sqlite3、8个.db、70 WAL/70 SHM、47个嵌套synthetic Git、53只读文件、9个synthetic .env*、7个测试key、reparse0。本轮增加664文件/402目录/125276136bytes；quality09为52文件、31目录含根、42093734bytes，新增1个mypy cache.db和1个原生debug.keystore（2714bytes），没有业务SQLite；rename01为285文件/115目录含根/41517185bytes，rename02为325文件/256目录含根/41533967bytes，另根级两份metadata摘要共131250bytes。

31份game副本最终只读哈希一致；6个旧key身份/size/mtime/hardlinks不变，新key仅位于获批精确路径，全部7个key不读取/哈希/复制/使用内容。quality09运行期观察到37个不同native路径，监测停止后仍有5个Godot缓存文件无对应观察事件；结束盘点已逐路径登记，均属原获批godot_import_cache类别、无类别外未登记资源，但不能补作运行期观察通过。具体五路径及所有新增资源的逐项metadata见正式evidence。

quality09 owner46324及所属子进程结束，8000/8001释放；正式与feature共24个默认DB surfaces不存在。feature ignored67，正式ignored14723（1个.env名称仅metadata，未读内容）；QA根外层不在Git仓库，内部47个Git单列。仍使用feature工作树与V13工具链；全部新旧QA、Step5历史资源、工作树/分支/cache明确保留，无本轮到期可删目标/删除建议，历史Codex获准删除台账无新增，回收0。V30—V33仍不存在，仅登记、不重建、不阻塞。

原Step6语义424 passed/55历史skip、三个全新进程25-case evaluator相同digest及完成的probe04保留；不声称本轮重跑，不用历史或专项结果代替完整quality。quality10和full-matrix01均不存在，唯一warm-up+5-run批次尚未消费。依据用户“全新目录、失败资源保留、原生例外绑定具体根”规则，quality09不能复用；下一步需批准全新E:\Agent\cyber-town-f009-step6-qa\quality-10及该根既有动态类别/精确测试key例外，再按最终冻结指纹继续完整quality。所有门禁通过后才执行唯一性能复验，全部收口条件满足才可标记step_6_complete / awaiting_step_7_authorization。

重复问题复盘：原生创建/改名/删除通知并非当前路径状态的快照，按每个工具补单个文件名不能覆盖同一竞态。修复落点为两QA文件中的统一通知改名核对和拒绝回归：Python依赖双端精确登记，Godot依赖既有批准类别与命名约束，均重新严格校验路径和身份；实际文件访问继续硬校验。类型检查命令以后使用os.devnull，避免大小写差异触发无效缓存创建。本轮没有放宽长期资源安全规则。


## 2026-09-03：quality09获批，恢复完整Step6验收

当前状态：step_6_in_progress / quality_09_authorized。用户批准全新E:\Agent\cyber-town-f009-step6-qa\quality-09并沿用既有例外。执行前97文件SHA256=6ea0c01ec1dbbd89ee198b00f6acc8574e714960b17b959fccf6cdf206618a2e完全匹配；双方branch/HEAD/origin/main保持1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3、staged0；quality09及full-matrix01均不存在，canonical/完整父链无reparse，39旧缓存metadata SHA256=cd441f082436fb555a4951c684e0f230ea36102c04e4c1caa999569caed744e5不变。

只切换scripts/f009_step6_qa.py和backend/tests/test_f009_step6_qa.py的quality08→09绑定，其余95文件冻结。复用已完成probe04；新批次验证uv退役通知、Windows asyncio入口、SQLite通知与pytest便捷别名边界，并执行原完整quality。所有质量和资源门禁通过后才执行唯一固定warm-up+5-run核心性能，不调整协议、阈值或工作量，不增批找通过。仅Step6，既有产品/测试/runner缺陷硬停止，不进入Step7或Git交付。

本根资源属F009-Step6：tmp、cache/mypy、cache/uv、cache/ruff、pytest、31文件game副本、appdata、localappdata、git-template/info/exclude、native-monitor-ready.json、native-monitor-drain.marker、quality-summary.json、pytest-summary.json、native-summary.json。Python实际子路径由ResourceGuard在创建前同步精确登记。原生动态类别预登记：game/.godot、appdata/Godot、localappdata/Godot、pytest/**/.git、cache/uv；运行期记录并在结束逐路径核对。仅该根appdata/Godot/keystores/debug.keystore允许Godot原生生成，Python禁止读取/哈希/复制/使用内容、仅metadata核对。不启用其他原生类别，不复用失败根或旧SQLite，不联网、不安装。

所有新旧资源均保留至Step6收口后由用户手动处置；属于synthetic/fake/工具缓存或脱敏metadata，测试key例外如上。V30—V33旧根不存在仅登记、不重建。quality08及历史失败记录保留，完整quality和性能当前尚未通过。


## 2026-09-03：quality08在uv通知检查处停止，QA修复194项通过

当前状态：`step_6_blocked / awaiting_fresh_quality_09_authorization`。Step5、预算投影修复和retry v8保持完成；Step6完整quality及性能验收尚未完成，Step7未开始。本轮启用获批quality08前，97文件SHA256=d36c6e4eb282e0c4f479cd1f3db79d722a4fc1099f38a459d58c5e04614cdc56完全匹配；绑定07→08后执行快照为ebca791ecc19ea1e07d7d5e722e9f58969551d61a8571571f0459d9cc30c89d5。

quality08前置ignore/sensitive通过，但在uv lock运行期间，第37个原生通知(action=2)触发step6_resource_canonical_mismatch：已记录创建的cache/uv/.tmpevxwVg/python/get_interpreter_info.py，其父目录退役后的首次resolve落入同卷NTFS $Extend/$Deleted。quality-summary为exit_code=1、commands=[]；lock不记通过，pytest未开始，native-summary未生成，不能将手动最终盘点写成运行期资源门禁通过。

修复仅scripts/f009_step6_qa.py与backend/tests/test_f009_step6_qa.py：新增uv退役通知的窄范围metadata处理，必须同时满足当前批准根/cache/uv、此前创建记录与正确类别、删除或rename-old动作、同卷NTFS退役路径的hex及尾部匹配、原路径再次严格canonical/完整父链无reparse、缓存锚点设备与文件身份不变。只记录通知，不访问NTFS内部目标；实际文件访问和结束盘点仍用原严格检查，既有SQLite通知规则未扩大，作用域隔离与权限撤销保持。

全新pytest-uv-retirement-01中独立QA为194 passed、0 skipped、boundary_violations={}；新增17个uv通知用例覆盖3个接受场景及14个拒绝场景。1261路径事前登记，145次pytest便捷别名未创建。两QA文件lint/format及131个源文件mypy通过。测试重放了实际捕获的uv通知形态，但修复后尚未在新的真实uv运行中验证；专项测试不能替代完整quality。quality07的2066 passed/133 expected skipped/1 failed及后续203项专项修复记录均保留，不与本轮194相加。已完成probe04不重跑；原Step6三进程25-case evaluator结果保持，不声称本轮重新执行。

最终冻结97文件SHA256=6ea0c01ec1dbbd89ee198b00f6acc8574e714960b17b959fccf6cdf206618a2e；相对本轮开始仅两QA文件改变，其余95与文件集合一致。feature37 tracked modified/60 actual untracked/staged0，正式仅五文档修改；双方branch、HEAD及本地origin/main保持1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3。14 migration原始bytes指纹一致，tracked diff --check和60个untracked whitespace检查通过。39旧缓存metadata SHA256=cd441f082436fb555a4951c684e0f230ea36102c04e4c1caa999569caed744e5不变。产品、既有测试/runner、SQL/migration、依赖、CI、工作量和门禁均未修改。

资源盘点：QA根7123文件、5766子目录、1080508140bytes（1030.45MiB），6029个.sqlite3、7个.db、64 WAL/64 SHM、47个嵌套synthetic Git、53只读文件、9个synthetic .env*、6个旧测试key、reparse0。本轮新增334文件/170目录/41697336bytes；quality08为39文件、20目录含根、101909bytes，无新SQLite/Git/key；pytest-uv-retirement-01为294文件、150目录含根、41527706bytes，另根级摘要67721bytes。31个game副本最终只读哈希核对一致。6个旧key仅metadata核对且未变，不读取/哈希/复制/使用内容。逐路径记录见正式evidence。

quality08 owner40780及所属子进程已结束，8000/8001释放；正式与feature的24个默认DB surfaces均不存在。feature ignored67、正式ignored14723（1个.env名称仅metadata）；QA外层不属Git仓库，内部Git单列。全部新旧QA资源、工具链、Step5历史根、工作树/分支/cache保留，回收0，无新增Codex删除记录或删除建议；V30—V33仍不存在，只登记、不重建。quality09和full-matrix01不存在；唯一固定warm-up+5-run性能批次尚未消费。

下一步需用户批准全新E:\Agent\cyber-town-f009-step6-qa\quality-09并沿用该根的Godot/Git/uv动态类别及精确debug.keystore原生生成、metadata-only例外。新根授权要求来自用户“全新目录、失败资源保留、原生例外绑定具体根”的边界；quality08不得重用。获批后先复核最终97文件指纹与branch/HEAD，只切换两QA文件当前绑定，完成完整quality和全部资源门禁后才执行唯一固定warm-up+5-run性能，满足全部收口条件后才能标记step_6_complete / awaiting_step_7_authorization。

重复问题复盘：SQLite与uv均出现原生资源删除后才送达的NTFS通知，旧监测器对“已退役对象通知”与“实际路径访问”采用相同存活假设，导致质量流程多次中止。后续规则已落在两QA文件：通知例外按资源类别、先前创建证据、动作、路径和锚点身份分别验证，并配拒绝回归；实际访问继续严格校验。当前修复的实际uv验证仍待全新quality根，不以模拟成功推断真实流程通过。


## 2026-09-03：quality08获批，恢复完整Step6验收

当前状态：step_6_in_progress / quality_08_authorized。用户已批准全新 E:\Agent\cyber-town-f009-step6-qa\quality-08，沿用既有Godot/Git/uv动态类别及精确测试key例外。执行前97文件SHA256=d36c6e4eb282e0c4f479cd1f3db79d722a4fc1099f38a459d58c5e04614cdc56完全一致；双方branch/HEAD/origin/main不变、staged0，新quality08与full-matrix01不存在，canonical/完整父链无reparse。39旧缓存metadata SHA256=cd441f082436fb555a4951c684e0f230ea36102c04e4c1caa999569caed744e5不变。

仅修改两QA文件当前quality07→08绑定，其余95冻结；不重跑已完成probe04。完整quality覆盖lock/Ruff/mypy/schema/Godot import/unit/connectivity/Dialogue/MultiNPC/完整pytest及前后ignore/sensitive、运行期/结束资源核对，纳入Windows asyncio入口、pytest便捷别名、SQLite通知与子权限撤销修复。全部通过后只执行一次固定warm-up+5-run核心性能；不改工作量/门禁，不进入Step7/Git交付。

quality08资源属于F009-Step6：tmp、cache/mypy、cache/uv、cache/ruff、pytest、31文件game副本、appdata、localappdata、git-template/info/exclude、native-monitor-ready.json、native-monitor-drain.marker、quality-summary.json、pytest-summary.json、native-summary.json。Python实际路径创建前同步登记；native目录类别预登记并运行期记录/结束核对：game/.godot、appdata/Godot、localappdata/Godot、pytest/**/.git、cache/uv。仅本新根appdata/Godot/keystores/debug.keystore允许Godot原生生成，Python禁止读取/哈希/复制/使用内容；不允许hsperfdata或其他native类别。其他资源仅synthetic/fake/metadata，全部新旧资源保留至Step6收口后由用户手动处置，Codex不删除、不复用旧SQLite。

## 2026-09-03：quality07资源监测完成，asyncio入口修复已验证

当前状态：`step_6_blocked / awaiting_fresh_quality_08_authorization`。本轮按授权启用全新quality07；Step5、预算投影修复与retry v8保持完成，Step6未完成，Step7未开始。执行前f3e552冻结97文件完全匹配，probe04保持已完成、不再需要重跑探针。

quality07前置ignore/sensitive与8项命令（lock、Ruff、mypy、schema、Godot import/unit、connectivity、Dialogue/MultiNPC）通过。完整pytest为2066 passed/133 expected skipped/1 failed，失败用例 `backend/tests/test_sqlite_connection_lifecycle.py::test_unprofiled_benchmark_uses_independent_tcp_client` 在独立客户端启动JSON握手阶段失败；不能标完整quality通过，final ignore/sensitive未执行。该用例固定2请求，仅属原有测试，不是一次warm-up+5-run性能批次；full-matrix01仍不存在、名额未消费。

native-summary completed=true仅代表监测/结束盘点完成，不代表quality通过：50591事件、unknown_paths=[]、reparse0、overflow=false，31个game源/副本哈希一致；89条瞬态native路径、49个退役SQLite sidecar记录。pytest便捷别名966次未创建，边界违规{}；原SQLite通知/pytest alias适配在完整quality中通过资源核对。最终root934文件130389096bytes；native-summary自身写入前为933文件129992731bytes。

P1（QA工具入口覆盖缺口）：Windows asyncio.windows_utils.Popen继承原subprocess.Popen，绕过只patch模块Popen的旧QA包装。metadata-only新进程探针仅触发sys.audit模拟open，未执行实际文件操作，确认asyncio子进程无QAguard。与原测试启动握手失败及修复后通过构成定位证据；不推断未保存的子进程stderr细节、不认定产品逻辑缺陷。

修复仅两授权QA文件：普通Popen与Windows asyncio Popen共用argv/env/child_entrypoint检查，保留原overlapped pipe实现；作用域退出恢复两处入口。新增真实async子进程文件预登记/审计继承、native与shell拒绝、作用域恢复验证。初版factory参数与launcher源码字符串重名，pytest-async-boundary01为114 passed/1 QA failed，mypy入口未成功启动；已纠正并保留失败批次。最终pytest-async-boundary02为203 passed/0 skipped，其中QA177、SQLite lifecycle26，包含原失败TCP用例；1310路径事前登记、边界违规{}、153便捷别名未创建。最终两QA lint/format、全131源mypy通过，39旧缓存metadata不变。不相加2066与203充作独立总数，不用专项替代完整quality。

最终97文件SHA256=`d36c6e4eb282e0c4f479cd1f3db79d722a4fc1099f38a459d58c5e04614cdc56`；相对f3e552仅两QA文件变化，其余95及集合完全一致。feature37 tracked modified/60 actual untracked/staged0；正式仅五文档修改；双方branch/HEAD/origin/main仍1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3。tracked diff --check通过；逐60个untracked无whitespace错误（no-index exit1是与NUL内容差异，11条仅换行提示）；14 migration按历史工作区原始bytes指纹全部匹配。没有修改产品/既有测试/runner/SQL/migration/依赖/CI/工作量/门禁。

最终QA根6789文件、5596子目录、1038810804bytes（990.69MiB）；5754个.sqlite3后缀文件、7个.db、61 WAL/61 SHM、47个实际嵌套Git、53只读文件、9个synthetic .env*、6个测试key，reparse0。本轮增加1524文件214793021bytes。quality07为934文件/1209目录含根/130389096bytes，含14 synthetic Git、17只读文件、3个synthetic .env*、仅1个新key；async01为280文件/111目录含根/41517056bytes；async02为308文件/158目录含根/42766599bytes；另两根级metadata摘要共120270bytes。新key仅原生生成2714bytes，5旧key逐项metadata不变；6个key均不读/哈希/复制/使用内容。

QA根在Git仓库外，外层tracked/untracked/ignored不适用；内部47 synthetic Git单列。feature ignored67，正式ignored14723（1个.env名称仅metadata，未读内容），现有缓存不变。quality owner44664及子孙结束，8000/8001释放，正式/feature24默认DB surfaces不存在。仍使用feature工作树与V13工具链；全部新旧QA、V29等历史Step5根、工作树/分支/cache明确保留；V30—V33为用户已删除且仍不存在，不重建、不阻塞。无本轮到期可删目标/删除建议，历史Codex获准删除台账无新增，回收0。

恢复所需新根：`E:\Agent\cyber-town-f009-step6-qa\quality-08`（尚不存在、未加入允许列表）。依据用户规定每次quality必须全新目录、不复用失败SQLite，原生例外精确绑定批次根；quality07不能重新执行。新根获批后仅切换两QA绑定，沿用既有Godot/Git/uv与该根精确测试key例外；完整quality及结束资源门禁通过后，执行唯一固定warm-up+5-run性能并最终五文档收口。无需新增产品修复授权，不进入Step7。

## 2026-09-03：quality07获批，恢复完整Step6验收

当前状态：step_6_in_progress / quality_07_authorized。用户已批准全新 E:\Agent\cyber-town-f009-step6-qa\quality-07，沿用既有Godot/Git/uv动态类别及精确测试key例外。执行前97文件SHA256=f3e5523e0f844acb6ec149f7dc7c751488fda7856ca390c102f51e71a5542047完全一致；双方branch/HEAD/origin/main不变、staged0，新quality07与full-matrix01不存在，canonical/完整父链无reparse。39旧缓存metadata SHA256=cd441f082436fb555a4951c684e0f230ea36102c04e4c1caa999569caed744e5不变。

仅修改两QA文件当前quality06→07绑定；其余95冻结。保留probe04已完成结果，不重复探针。完整quality覆盖lock/Ruff/mypy/schema/Godot import/unit/connectivity/Dialogue/MultiNPC/完整pytest及前后ignore/sensitive、运行期通知与结束资源核对；包含已修正pytest辅助别名、SQLite退役通知、子权限撤销边界。所有前置门禁通过后只执行一次固定warm-up+5-run核心性能。仅Step6，不进入Step7/提交/推送/PR/合并/部署/删除。

quality07资源所属F009-Step6：tmp、cache/mypy、cache/uv、cache/ruff、pytest、31文件game副本、appdata、localappdata、git-template/info/exclude、native-monitor-ready.json、native-monitor-drain.marker、quality-summary.json、pytest-summary.json、native-summary.json。Python实际子路径创建前同步精确登记；native目录/类别先登记，运行期记录和结束逐项核对：game/.godot；appdata/Godot；localappdata/Godot；pytest/**/.git；cache/uv。仅本新根appdata/Godot/keystores/debug.keystore允许Godot原生生成，Python禁止读取/哈希/复制/使用；不启用hsperfdata或其他native类别。其他资源仅synthetic/fake或metadata。全部新旧资源保留至Step6收口后由用户手动处置，Codex不删除、不复用旧SQLite。

## 2026-09-03：quality06停止，pytest目录别名适配已修复验证

当前状态：`step_6_blocked / awaiting_fresh_quality_07_authorization`。Step5、预算投影修复、retry v8仍完成；Step6尚未完成，Step7未开始。本轮按用户批准启用全新quality06，执行前de518冻结97文件匹配；native probe04仍为已完成，不需再跑探针。

quality06通过ignore/sensitive预检与lock、Ruff、mypy、schema、Godot import/unit、connectivity、Dialogue/Multi-NPC共8项命令。完整pytest期间event785/action1发现未登记的 `E:\Agent\cyber-town-f009-step6-qa\quality-06\pytest\test_initialization_only_uses_current`，监测器按规则硬停止。quality-summary exit1；pytest-summary与native-summary不存在，不能报告完整pytest通过数或完整quality通过；结束政策检查未执行。唯一性能full-matrix01仍未创建、未消费。

P1（QA资源边界，非已确认产品缺陷）：当前安装pytest的make_numbered_dir隐式调用_force_symlink创建prefix+current便捷别名，失败异常可被pytest吞掉；原QA未拦截该系统调用。监测路径与该辅助机制相符，事后无current/reparse残留，不声称曾成功创建有效链接。既有Godot/Git/uv例外不覆盖此类别，未扩大例外。

QA修复仅两个授权文件：run_pytest作用域保留真实编号目录、严格核对root/target/编号归属并阻止非必要current别名创建；退出恢复pytest helper。audit额外拒绝os.symlink/os.link，实际canonical/完整父链/reparse检查继续严格。未修改产品、既有测试、runner、SQL/migration、依赖文件、CI、工作量或阈值。

修复验证：pytest-alias-boundary-01为216 passed/0 skipped，其中独立QA174、既有synthetic ledger42；1434路径事前登记，boundary_violations={}，169次便捷链接未创建。新用例真实Windows NativeWatcher确认编号目录创建且无current通知，另有非法目标/作用域恢复及symlink/hardlink拒绝反例。与历史166+5不相加计数。最终两QA文件受控lint/format通过；修复后禁持久缓存mypy全131源文件通过；39旧缓存metadata摘要不变。此验证不能替代完整quality。

最终97文件SHA256=`f3e5523e0f844acb6ec149f7dc7c751488fda7856ca390c102f51e71a5542047`，相对de518仅两QA文件变化，其余95及集合不变。feature37 tracked modified/60 actual untracked/staged0；正式仅五文档修改；两branch/HEAD/origin/main不变。双方tracked diff --check通过；60 untracked no-index无whitespace错误（exit1为与NUL内容不同，11项仅Git换行提示）；14 migration原始bytes指纹与正式历史登记匹配。

资源：QA根5265文件、4118子目录、824017783 bytes；4495个.sqlite3后缀文件、5个.db、46 WAL/46 SHM、33实际嵌套Git、36只读文件、6旧synthetic .env*、5个key，reparse0。新增392文件85012115bytes。quality06为63文件/45目录含根/42808493bytes；pytest-alias-boundary01为328文件/174目录含根/42131727bytes，另有根级71895bytes元数据摘要。quality06新key仅原生生成2714bytes，5个key均只核元数据，不读取/哈希/复制/使用；4旧key metadata不变。

QA根在Git仓库外，新批次无嵌套Git，tracked/untracked/ignored不套用仓库索引；全QA含33个旧synthetic Git。feature忽略文件67，正式14723（其中1个.env名称，仅metadata，不读取）；source与资源没有混入提交。quality owner57700及子孙退出，8000/8001空闲，正式/feature24默认DB surfaces不存在。

资源处置：仍使用feature工作树与V13工具链；全部新旧QA、V29等历史Step5根、工作树/分支/cache明确保留。V30—V33仍为用户已删除/当前不存在，不重建、不阻塞。没有本轮可删除或到期回收目标；历史Codex获准删除记录沿用原台账，无新增删除；本轮回收0。Step6未完成前不建议删除失败证据或新测试资源。

下一步唯一新资源授权：`E:\Agent\cyber-town-f009-step6-qa\quality-07`（尚不存在、尚未加入允许列表）。因用户要求每轮全新目录/不复用旧SQLite且原生例外精确绑定批次根，quality06已消耗不能重跑。批准新根后只切换两QA当前绑定，沿用Godot/Git/uv类别及新根精确debug.keystore例外，先全部quality/资源门禁，通过后唯一固定warm-up+5-run核心性能及最终盘点；不新增产品修复，不进入Step7。

## 2026-09-03：quality-06获批，恢复完整Step6验收

当前状态：step_6_in_progress / quality_06_authorized。用户已批准全新 E:\Agent\cyber-town-f009-step6-qa\quality-06，沿用既有 Godot/Git/uv 动态资源例外。执行前97文件聚合 de518f9f38f07fea261ffb736d2966fafe4b236ac0c49693457d0159685a75ed 完全一致；双方 branch/HEAD/origin/main 未变、staged0，新根及 full-matrix-01 不存在，canonical/完整父链无reparse。

修改范围仅 scripts/f009_step6_qa.py 与 backend/tests/test_f009_step6_qa.py 的 quality-05→quality-06 当前绑定。保留 probe04 成功结果，不重跑探针；不修改95个其余冻结文件。完整quality重跑lock、Ruff、mypy、schema、Godot import/unit、connectivity、dialogue/MultiNPC、全部pytest及前后ignore/sensitive和资源盘点。独立边界、SQLite退役通知、子进程权限撤销均纳入完整pytest。全部前置门禁通过后只运行一次固定warm-up+5-run核心性能；不调整门禁/工作量。

资源属于 F009-Step6：新根下 tmp、cache/mypy、cache/uv、cache/ruff、pytest、31文件game副本、appdata、localappdata、git-template/info/exclude、native-monitor-ready、native-drain-marker、quality-summary.json、pytest-summary.json、native-summary.json。Python实际路径创建前精确同步登记；Godot game/.godot、appdata/Godot、localappdata/Godot；pytest/**/.git 合成Git内部；cache/uv 动态目录/类别预登记并运行期记录、结束逐项核对。仅本新根 appdata/Godot/keystores/debug.keystore 允许原生生成测试key，Python禁止读取/哈希/复制；其他资源仅synthetic/fake或脱敏metadata。hsperfdata仍禁止。全部新旧资源保留至Step6收口后用户手动处置，Codex不删除。本次不创建quality07，不进入Step7。

## 2026-09-03：原生probe04完成，quality05停止后QA通知修正已验证

当前状态：`step_6_blocked / awaiting_fresh_quality_06_authorization`。本轮已完成用户批准的probe04九项原生验收及资源核对；不再需要新的原生探针。Step5、预算投影修复与retry v8保持完成；Step6尚未完成、Step7未开始。

probe04：Git五项、uv、Ruff、Godot import/unit全部成功；native-summary completed=true，251事件、未知路径/reparse/overflow均0，31-game-copy哈希一致，23瞬态native路径已记录。JVM hsperfdata不存在，禁止该附加文件的真实效果通过；仅新root下原生生成测试key，未读/哈希/复制内容。最终root含56文件3439078bytes（native-summary自身写入前报告55文件3396835bytes，差值为metadata摘要）。

随后quality05已通过ignore/sensitive预检和lock/Ruff/mypy/schema/Godot import/unit/connectivity七命令。Dialogue阶段event389遇到已预登记isolated.sqlite3-journal，首次resolve捕获同卷NTFS $Extend/$Deleted内部删除路径，监测器停止。完整pytest、quality结束政策检查和native结束盘点未完成；不能标完整quality通过。quality05保留，不能复用其中DB/cache；唯一性能full-matrix01未创建/未消费。

QA修正仅限两授权文件：实际访问及最终盘点的validate_path仍严格；异步通知仅对database与-journal/-wal/-shm均有SQLite类别事前登记、同卷NTFS精确退役目标、本批次归属且parent完整安全检查通过的路径处理。原leaf已消失则记录退役；同名leaf现存必须再次通过严格canonical检查，否则拒绝；不访问NTFS系统路径、不新增native例外、不允许活别名/未登记路径。新增真实64次SQLite journal事务验证integrity/FK和通知。初版164 passed/1 failed保留；补足同名重建窗口后166 passed/0边界违规。该真实复验通过，但未声称其一定重新触发NTFS竞态；退役/重建分支另有明确模拟正反例。

完整quality上下文还补足受限子作用域：native_root=None时移除F009_NATIVE_ROOT/PID，外层wrapper不得恢复已撤销环境授权。最后该修正后的5项相关回归全部通过、边界违规0；不能将166+5当作171独立用例或最终全量pytest。SQLite修正后禁持久缓存mypy对131源文件通过；发生在最后权限继承修正之前。最终两QA的受控lint/format通过，39旧缓存metadata不变。

恢复所需唯一新资源批准：`E:\Agent\cyber-town-f009-step6-qa\quality-06`（尚未创建/未加入允许列表）。沿用既有Godot/Git/uv类别与该新根appdata/Godot/keystores/debug.keystore单独例外；不复用quality05，不重跑已完成probe04。获批后切换QA质量批次绑定，运行完整quality全部命令/pytest/结束资源门禁；通过后仅一次固定warm-up+5-run核心性能，并更新五文档收口。不是新增产品修复或Step7授权。

最新97文件聚合SHA256=`de518f9f38f07fea261ffb736d2966fafe4b236ac0c49693457d0159685a75ed`，相对264d仅两QA文件变化、其余95相同；37 tracked modified/60 actual untracked/staged0，正式只改五文档，两处branch/HEAD/origin/main不变，diff --check均0。产品、既有测试/runner、SQL/migration、依赖、CI、工作量和性能阈值未改。

资源：QA根4873文件/3899目录/739005668 bytes（704.77 MiB），本轮增加695文件/129179726 bytes；4173个.sqlite3后缀文件、4个.db（含缓存/合成文件）、42 WAL、42 SHM、33实际嵌套Git、36只读文件、6旧synthetic .env*、4个key，reparse0。本轮新key仅probe04与quality05各2714bytes，两旧key保持原mtime；均仅metadata，不读/哈希/复制。全部新旧资源保留、无删除建议、回收0。quality owner50120及子孙已退出，8000/8001空闲，正式/feature24默认DB surface不存在。V30—V33仍不存在，V13/V29/其余旧根/worktree/分支/cache保留。

## 2026-09-03：probe-04获批，继续独立Step6验收

当前状态：step_6_in_progress / native_boundary_probe_04。用户已批准全新E:\Agent\cyber-town-f009-step6-qa\native-boundary-probe-04并沿用既有例外。执行前97文件264d2f917dc5db6d8d04cf93cfdd650e94f4fc54fcfcb2eca6679892b619d5c0一致，双方branch/HEAD/origin/main符合冻结登记，staged0。probe04、quality05、性能full-matrix01不存在，canonical及完整父链无reparse。

仅两QA文件切换当前探针与对应测试，旧01/02/03不可复用。既有31-game-copy及Godot/Git/uv类别不变；新key精确限定probe04/appdata/Godot/keystores/debug.keystore，仅Godot原生生成且不读/哈希/复制。Godot子环境启用-XX:-UsePerfData以禁止非必要JVM计数共享内存文件，hsperfdata仍不在例外。先受控静态检查与针对性绑定/JVM/canonical用例，再真实九项探针与资源完整盘点；通过后运行quality05全部工程门禁，再唯一固定warm-up+5-run性能复验。Step7未授权。

资源属于F009-Step6，synthetic/fake与metadata，新key单列原生例外；所有Python路径在实际创建前精确登记，native类别按既有批准运行期记录/结束核对。全部保留用户手动处置，不删除/提交/推送/PR/合并/部署。

## 2026-09-03：probe-03通过Git/uv/Ruff，JVM临时文件阻塞后完成QA修正

当前状态：`step_6_blocked / awaiting_fresh_native_probe_04_authorization`。本轮已按用户授权创建并执行probe-03，未复用旧probe。Step5、预算投影修复与retry v8保持完成；Step6尚未完成，Step7未开始。既有Godot/Git/uv动态资源例外继续有效。

执行前97文件ddf03d886e85c9183ef58dc8451c2d80129e9aafd434cc9c064841eb9e264637一致。切换probe-03后11项绑定/uv/canonical针对性测试通过；受控lint/format通过，39个旧缓存metadata条目不变。真实probe-03已有七项成功：Git init/add/hash-object/update-index/ls-files、uv lock --check、Ruff。此前canonical失败未重现。

Godot-import阶段监测器在event_count=192收到未预登记tmp/hsperfdata_24696创建通知，报step6_native_unregistered_other_tool_resource并停止。Godot-import未计通过、Godot-unit未启动，native-summary不存在，不能算九项完整探针通过。停止后hsperfdata目录为空；没有新增key或SQLite；owner PID55468及其子孙已退出。quality-05和唯一性能full-matrix-01仍未创建/未启动。

只读本地JDK21.0.7 release/src.zip确认hsperfdata是JVM PerfData共享内存目录；jvm.dll含UsePerfData开关。本次未捕获Java子PID，不把具体keytool归属推断写成进程实测。最小QA修正仅在Godot子进程环境设置JAVA_TOOL_OPTIONS=-XX:-UsePerfData，并移除该子环境的_JAVA_OPTIONS/JDK_JAVA_OPTIONS干扰；不修改父/全局环境、安装、产品、工作量或性能门禁。hsperfdata仍不在例外中，所有资源检查继续启用。最终完整专项157 passed、0 skipped、boundary_violations={}，含参数隔离、父环境保持、其他native不受影响与hsperfdata仍拒绝；本次静态lint/format通过。禁止JVM附加文件的真实原生效果尚未验收，不能用模拟参数测试冒充Godot通过。

恢复需要新的明确批准根：`E:\Agent\cyber-town-f009-step6-qa\native-boundary-probe-04`（仅提案，未创建/未加入允许列表）。沿用原Godot/Git/uv类别及新根下唯一debug.keystore例外；不新增JVM资源例外。获批后先验证新Godot参数与九项原生探针/完整资源盘点，通过后执行quality-05全部门禁，再唯一固定warm-up+5-run性能与最终五文档收口。旧probe03保留、不得重跑。

最新97文件聚合SHA256=`264d2f917dc5db6d8d04cf93cfdd650e94f4fc54fcfcb2eca6679892b619d5c0`；相对ddf0只有两QA文件变化，其余95相同；37 tracked modified/60 actual untracked/staged0，正式仅五文档修改。两处branch/HEAD/origin/main不变，git diff --check均0。未改产品、既有测试/runner、SQL/migration、依赖、CI、工作量或阈值。

资源：QA根4178文件/3574目录/609825942 bytes（581.58 MiB），本轮增加334文件/41682353 bytes；3618 SQLite、36 WAL、36 SHM、32嵌套Git、35只读文件、6旧synthetic .env*、2旧keystore，reparse0。probe03为47文件/40目录/103219bytes，31游戏副本文件与来源哈希一致；旧key各2714bytes仅metadata，未读/哈希/复制/使用。旧两Ruff缓存mtime/大小未改变。8000/8001空闲，默认24 DB surface均不存在。V30—V33仍不存在；V13工具环境/V29/其余旧根、worktree、分支、缓存及本轮所有资源保留，不建议删除，回收0。

## 2026-09-03：probe-03获批，恢复Step6原生验收

当前状态：step_6_in_progress / native_boundary_probe_03。用户已明确批准全新E:\Agent\cyber-town-f009-step6-qa\native-boundary-probe-03，沿用上一具体提案与既有Godot/Git/uv类别、该新根下唯一Godot debug.keystore例外。旧probe01/02保留，不复用。执行前97文件聚合ddf03d886e85c9183ef58dc8451c2d80129e9aafd434cc9c064841eb9e264637一致，分支/HEAD/origin/main不变，staged0。新probe03、quality05、full-matrix01均不存在且canonical完整父链无reparse。

仅修改两QA文件的探针绑定与对应独立用例，不改任何产品、既有测试/runner或性能门禁。先受控静态检查及绑定/uv/通知针对性测试，再新probe九项；通过完整资源核对后进入quality05，最后仅一次固定warm-up+5-run性能。最终五文档收口。资源属于F009-Step6、synthetic/fake或metadata；key仅原生生成且禁止Python读/哈希/复制，全部资源保留用户手动处置，不删除。Step7未授权。

## 2026-09-03：统一QA入口与canonical修正通过专项，等待全新原生探针

当前状态：`step_6_blocked / awaiting_fresh_native_probe_authorization`。用户授权的统一QA命令入口修正已完成并通过专项；Step5、预算投影修复与retry v8保持完成。Step6尚未完成，Step7未开始。Godot/Git/uv既有动态资源例外继续有效，无需重复批准。

两QA文件新增统一command_environment/command_scope与--static-checks入口；Python/native子进程即使传入旧缓存环境也强制隔离TEMP和缓存，Ruff显式--no-cache，固定静态命令拒绝漏参；退出恢复原环境和tempfile配置。静态lint/format通过，39个正式/feature缓存元数据条目前后相同，上轮误写的两Ruff条目mtime/大小未再改变。首轮新根151 passed；随后canonical修正后的最终完整专项154 passed、0 skipped、boundary_violations={}，分别登记1215路径。151与154不可相加视为305独立用例。

新probe-02已执行Git init/add/hash-object/update-index/ls-files五项，全部exit0。uv启动后删除通知cache/uv/.tmpFGtxpB/python/get_interpreter_info.py在event_count=137触发canonical mismatch；已保存原事件，后续停止，Godot与probe Ruff未运行，native-summary未生成，不能算探针通过。准确首次resolve值该次仍未留存；第二次已恢复。只读查看本地Python3.12 ntpath代码并模拟OS调用，复现文件消失时realpath保留DOS前缀导致同一路径不相等。QA现只接受准确相同绝对路径的标准/DOS两种表示，仍拒绝任何不同target并完整检查父链/reparse/归属，同时保存首次失败resolve。该竞态机制已独立复现并回归通过；本次事件与之符合，但不得将未捕获的首次返回值当作已知事实。

probe-02已使用且必须保留，不能复用。恢复真实原生验收需要一个明确批准的全新根：`E:\Agent\cyber-town-f009-step6-qa\native-boundary-probe-03`（仅提案，未加入允许列表、未创建）；对应新key为该根appdata\Godot\keystores\debug.keystore，仅Godot原生生成且Python不读/哈希/复制。quality-05及唯一full-matrix-01仍不存在，未消费性能批次。下一步获批新根后：切换两QA文件的探针绑定 → 完整原生探针九项和资源盘点 → quality-05全部工程门禁 → 唯一固定warm-up+5-run性能 → 五文档Step6收口。

最新97文件聚合SHA256=`ddf03d886e85c9183ef58dc8451c2d80129e9aafd434cc9c064841eb9e264637`；相对51a0基线仅两QA文件变化，其余95完全相同，37 tracked modified/60 untracked/staged0，两处branch/HEAD/origin/main不变，diff --check均0；正式只改五份文档。产品、既有测试/runner、SQL/migration、依赖、CI、工作量和阈值未修改。

资源：QA根3844文件/3419目录/568143589 bytes（541.82 MiB），本轮增加617文件/83253917 bytes；3344 SQLite、33 WAL、33 SHM、31实际嵌套Git、34只读文件、6旧synthetic .env*、2旧keystore，reparse0。旧key各2714 bytes，仅metadata未读/未用/未删；本轮无新增key。probe-02保留45文件/102966bytes，无SQLite/key。PID47444及其子孙均已退出，8000/8001空闲，正式/feature24默认DB surface不存在。旧V30—V33只登记不存在；V13工具环境、V29、其余旧根、worktree、分支、缓存均保留。没有删除建议或本轮删除，回收0。

## 2026-09-03：统一QA命令入口后继续已授权Step6

当前状态：step_6_in_progress / command_cache_boundary_repair。用户明确授权修正统一命令入口并继续探针与剩余验收。执行前51a03d8a564d1cc591b34ec0f5887ab8a437d95f255383bc08bda6260da0dbad聚合一致，97文件、branch/HEAD未变。仅两QA文件加五正式文档，旧Ruff越界缓存保留。新增--static-checks入口：限定固定Ruff检查argv、强制禁缓存；所有子进程统一环境覆盖；作用域退出恢复。静态检查不生成外部缓存/报告，只追加正式evidence元数据。

资源：pytest-uv-boundary-01及uv-boundary-summary-01.json沿用已登记且仍全新路径；native-boundary-probe-02、quality-05沿用已批准全新根和Godot/Git/uv类别；所有Python实际子路径仍须事前登记。资源属于F009-Step6，synthetic/fake或metadata；新keystore仅原生Godot限定路径生成且不读内容。保留至收口后用户手动处置，不删除。新独立用例验证带污染环境的启动覆盖、缺少no-cache的拒绝、退出恢复、旧缓存metadata不变；与既有uv范围/通知用例一起验收。通过后继续probe、quality；仅全部语义/工程门禁通过后消费唯一固定性能批次。

## 2026-09-03：uv批准已落实，QA命令误写Ruff缓存后停止

当前状态：`step_6_blocked / awaiting_qa_command_boundary_resolution`。uv动态资源例外和全新native-boundary-probe-02已经获批，授权继续有效；本轮停止不是uv授权缺失。Step5、预算投影修复与retry v8仍已完成；Step6未完成，Step7未开始。

本轮两QA文件已改为probe-02绑定，限定uv动态缓存在probe-02/quality-05的cache/uv，拒绝旧根继承例外，并保存canonical失败事件的原路径与resolve诊断。新增7个独立用例尚未执行；最终两文件ruff check/format --check --no-cache通过，但未运行新pytest、完整quality或性能，不能将静态检查计为验收通过。旧probe所有现存路径只读canonical/父链检查通过，历史瞬态异常仍无法从旧记录准确还原。

**执行事故：Codex在18:09:50（UTC+08）调用ruff format时漏传--no-cache，写入feature/.ruff_cache/0.16.4下两个缓存条目，总现存5464 bytes，未进行正式事前登记，且不在批准QA缓存根。**这是本轮命令失误，uv例外不覆盖Ruff缓存；事后盘点不追认为事前合规。发现后停止验收，仅进行只读盘点与正式文档收口，不删除/还原缓存。

97文件最新聚合SHA256=`51a03d8a564d1cc591b34ec0f5887ab8a437d95f255383bc08bda6260da0dbad`，相对08fb基线仅两QA文件变化，其余95文件相同，branch/HEAD/origin/main未变、staged0。正式只改五份文档。probe-02、quality-05、full-matrix-01及本轮pytest根/摘要均不存在；唯一性能批次未消费。

QA根仍为3227文件、3159目录、484889672 bytes（462.43 MiB）；2796 SQLite、27 WAL、27 SHM、30嵌套Git目录、33只读文件、2旧keystore均保留，reparse0。旧key只核对元数据，未读/哈希/复制。另保留本轮两Ruff缓存条目；QA根没有新增资源。8000/8001空闲，正式/feature 24个默认数据库surface均不存在。V30—V33继续缺失、不重建；V13/V29/其他旧根、worktree、分支、缓存继续保留。无删除建议，回收0。

剩余：先将所有QA命令入口（包括静态格式检查）纳入缓存隔离约束并验证，再按已有授权运行新probe-02、quality-05与尾检；全部语义/工程门禁通过后，执行唯一固定warm-up+5-run性能并收口。现有uv/Godot/Git例外无需重复批准；这次独立执行事故必须如实保留，不降低门禁，不将Step6标记完成。

## 2026-09-03：uv动态资源例外获批，恢复Step6验收

当前状态：`step_6_in_progress / native_boundary_probe_02_preparation`。用户已批准uv缓存适用既有动态资源例外并启用全新native-boundary-probe-02。批准范围仅为该新根和quality-05中的cache/uv；Godot与synthetic Git既有例外继续有效。旧probe-01保留、不复用。新probe的debug.keystore仅允许Godot在新路径原生初始化，Python不得读取/哈希/复制；不在旧probe创建key。

执行前97文件聚合08fbba17a795202dc78ac29e426a63dea3a7d058f684d91d2c0789ef6dfb0022一致，branch、HEAD及origin/main均未变化、staged0。只允许两QA文件适配与五份正式文档；产品和既有runner保持冻结。旧probe现存路径均通过canonical与完整父链检查，历史异常无last_event，尚不能还原准确触发路径；严格canonical校验继续保留，新探针失败必须留存原始事件与解析路径诊断。

计划顺序：QA范围/通知回归 → 新原生探针 → 全新quality-05与尾检 → 唯一固定warm-up+5-run性能 → 全部Step6收口。任一硬失败停止，性能尚未启动。Step7未授权。

## 2026-09-03：native专项例外执行后停止——uv缓存范围遗漏

当前状态：`step_6_blocked / awaiting_native_resource_boundary_resolution`。**用户已批准上一提案的两项专项例外，授权继续有效；本轮不是等待重新批准Godot/Git例外。**Step5、预算投影修复和retry v8同步保持完成，Step6未完成、Step7未开始。

本轮只改两QA文件，加入Windows目录通知、运行期metadata记录、结束盘点、子进程归属与作用域恢复、31文件哈希一致的game QA副本。137项专项通过；探针失败后3项无文件写入的针对性回归通过；最终两文件ruff/format与全仓131文件mypy通过。137项是探针前版本结果，不能代替最终完整quality。

`native-boundary-probe-01`的Git init/add/hash-object/update-index/ls-files五项退出码均0，已记录真实随机对象临时文件和原子重命名。随后启动uv lock --check时，监测器报`step6_resource_canonical_mismatch`并停止；最终触发事件路径当时未保存，准确原因尚未定位，不能未经证据解释成无害rename。只读盘点另确认uv生成3目录+3文件未逐路径预登记；uv不在仅限Godot/Git的动态资源例外中，因此探针失败、不能继续quality。其缓存中空.git标记被旧匹配逻辑误归为Git资源的QA缺陷已经修正；后续未知其他工具创建事件将报错并保存last_event。产品、既有测试和runner未修改。

Godot、probe中的ruff均未启动；未创建任何新增keystore；quality-05和唯一性能full-matrix-01均不存在。现已增加quality强制前置：原生探针必须有完成盘点且全部九项成功，否则在创建quality目录前报`step6_native_probe_not_complete`，真实零新增资源验证通过。没有跳过门禁或消费性能批次。

下一步准确缺口：uv原生动态缓存的允许范围，以及一次新的全新探针目录；同时需要凭完整事件诊断处理canonical通知异常。上一批准的两项例外无需重复申请；额外限定提案见evidence末尾“UV范围与新探针的增量提案（未执行）”。不能复用失败探针、扩大native类型或把未知路径事后登记算成合规。

最新97文件聚合SHA256=`08fbba17a795202dc78ac29e426a63dea3a7d058f684d91d2c0789ef6dfb0022`；相对3cd0基线仅两QA文件变化，其他95文件/HEAD/branch不变；37 tracked modified、60 actual untracked、staged0。正式仅五份文档修改。

QA根`E:\Agent\cyber-town-f009-step6-qa`保留3227文件、484889672 bytes（462.43 MiB），本轮增加329文件/41675096 bytes；30个实际嵌套Git目录、另1个uv .git空标记文件、33只读文件、6个旧synthetic .env*、2个旧keystore。旧keystore各2714bytes，本轮未读/未用/未删；新probe无SQLite和keystore。全部资源保留，删除建议清单为空，回收0；V30—V33继续不存在，V13/V29/其他旧根、worktree、分支和缓存保留。probe owner PID44616及其子孙已退出；其他任务的uv/Git进程未动；8000/8001空闲。未提交、push、PR、merge、部署或删除资源。



## 2026-09-03：S6-QA-002启动拦截已验证，原生预登记能力仍未解决

当前状态：`step_6_blocked / awaiting_native_resource_boundary_resolution`。Step5、S6-QA-001预算投影修复与retry v8同步保持完成。**本轮完成了阻止未受控原生工具启动的安全修正；尚未完成允许Godot/Git安全运行的原生适配，不能标记Step6完成。**

本轮仅修改两份QA文件：`scripts/f009_step6_qa.py`、`backend/tests/test_f009_step6_qa.py`。移除native父目录登记后直接放行的逻辑；原生预创建覆盖不可用时默认拒绝；quality在创建批次或导入产品quality前停止；Python只允许当前解释器，拒绝shell/executable替换与伪装child标记绕过。pytest纳入同一进程启动边界，作用域退出恢复。没有修改产品、既有测试/runner、SQL/migration、依赖、CI或性能门禁。

本轮新根专项130 passed / 0 skipped / 0 failed，包含原114项独立专项与16项QA边界/恢复检查；其中旧的native Git模板启动用例已改为启动拒绝验证，**130通过不证明native Git或完整quality通过**。真实Python子进程验证synthetic文件事前登记与native Git拒绝；全仓mypy131文件通过、两QA文件ruff/format通过。最后仅将quality预检前移到产品导入前，并以真实CLI验证：exit2、quality_started=false、新增路径0；这项拒绝是预期防护结果，不是quality合格。

仍缺：可验证的Godot/native Git实际路径创建前登记与密钥类别解决方案、完整fake-only quality及尾检、唯一统一warm-up+5-run性能复验、最终全部收口门禁。固定Git有tmp_obj_XXXXXX等内部随机文件；Python审计钩子不能在其创建前登记。固定Godot历史上自动生成debug.keystore，本轮没有启动它试探未验证的禁生成设置。原用户“全部实际子路径事前登记”“不得包含密钥”及两QA文件最小适配约束仍适用，不能以本轮修复授权解释为放宽这些条件。

最新97文件聚合SHA256=`3cd0c3a56f38020456df5b5ab65936b2122c7fa1d6d913ab9df0a9b35fa11ae9`，相对8f23基线仅两QA文件变化；37 tracked modified / 60 actual untracked / staged0，HEAD和分支未变。完整结果、资源盘点及尚未执行的具体恢复提案见evidence末尾“本轮S6-QA-002停止收口”。

资源保留：QA根`E:\Agent\cyber-town-f009-step6-qa`共2898文件、443214576 bytes（约422.68 MiB），本轮增加283文件/41571236 bytes；新专项281文件/113目录的394实际路径均有正式事前登记，另保留两份metadata测试摘要。旧两keystore各2714 bytes，仍仅核对元数据，未读/未用/未删；29嵌套Git、6个旧synthetic .env*、32只读文件均保留；reparse0。V30—V33继续不存在；V13工具环境、V29及其他旧资源/worktree/分支/缓存保留。未建议删除任何资源，回收量0。8000/8001空闲，本轮测试进程已退出。未执行新的完整quality或性能，未进入Step7或Git交付/部署。



## 2026-09-03：Step6剩余验收停止收口——QA原生资源边界

当前唯一状态：`step_6_blocked / awaiting_native_resource_boundary_resolution`。**Step5保持完成；S6-QA-001预算投影修复保持通过；retry测试v7→v8单行同步已完成。Step6仍未完成，Step7未授权、未开始。**下方旧预算修复/版本同步待授权记录均为历史，不覆盖本节。

本轮完成：retry/breaker完整文件18 passed；独立QA专项114 passed；相关完整语义/磁盘/故障回归424 passed/55历史skip；新进程隔离/保留适配2 passed与synthetic Git模板1 passed；三全新evaluator进程均25/25且digest一致；全仓131文件ruff/format/mypy、schema通过。批次存在重叠，不相加充当独立用例总数。独立专项274个新库只读integrity/FK通过，162 trace/2268 stage全部14-stage且有终态，已测成本/禁止sentinel命中均0。

当前阻塞S6-QA-002（QA资源合规P1）：本轮新QA脚本仅对Python创建操作逐路径审计，对native Godot/Git使用目录与类别登记，不能据此声称全部原生产物已逐路径预登记。Godot在quality-03与quality-04的APPDATA/Godot内自动创建未展开登记的export_templates、feature_profiles、keystores、script_templates、text_editor_themes、objectdb_snapshots、editor_settings，以及各1份debug.keystore（各2714bytes）。未读取keystore内容，不能宣称敏感资源为0。这是Codex新增QA适配器的遗漏，未确认新的产品缺陷。

quality-03的Godot import/unit、connectivity、Dialogue/Multi-NPC通过；全量pytest为1698 passed/133 expected skipped/1 QA模板适配失败后停止。模板问题已在QA文件修复并定向通过。quality-04再次通过上述前置门禁，但在全量pytest期间发现原生资源登记缺口，已停止其4个owned Python进程；未生成该轮最终pytest/quality摘要，不宣称通过。133旧skip核对为V7/V9=45、V10=53、V14—V19=33、V8=2，无新增skip。

唯一统一warm-up+5-run核心性能尚未执行，批次未消耗，逐轮/聚合warning/failure未生成。完整quality尾检、原生产物资源合规、受中断批次的最终审计及性能仍待完成。不能标记step_6_complete或进入Step7；下一步先提交原生工具资源范围与创建前登记的具体方案，未经解决不再次运行quality或性能。

QA根保留2615文件/2902后代目录/401643340bytes（约383.04MiB），包括2248 SQLite、21 WAL、21 SHM、62 JSON、29 synthetic嵌套Git、6 synthetic .env* fixture、32只读Git对象及2份未读取的Godot debug.keystore；reparse=0。quality-03/04及中断现场不复用、不删除。旧V30—V33不存在，不重建；V29、V13 tooling、其他旧根、worktree/分支及缓存继续保留。当前手动删除建议为空，尚需保留现场证据。

两处HEAD/local origin/main保持1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3；正式main仅五文档修改，功能37tracked/60actual-untracked/staged0；14migration哈希匹配，tracked和60个untracked whitespace检查通过（11条LF→CRLF告知不是whitespace失败）。24正式库/sidecar路径不存在，8000/8001空闲，4个owned进程已退出，不停止其他任务进程。当前97文件聚合SHA256=`8f23b432bb34fa2ba5c22b67877206abffaafb1caf44375e8c085c98f0851f25`；相对本轮开始97冻结快照仅retry测试和两QA文件获准变化，产品/runner/migration本轮未再修改。无提交、推送、PR、合并、部署或资源删除。

## 2026-09-03：Step6剩余验收恢复执行

当前状态：`step_6_in_progress / remaining_acceptance_running`。用户在明确下一步为retry测试v7→v8单行同步及剩余QA后批准继续完成Step6，本轮直接执行该项，不再等待重复确认。预算投影修复和Step5完成状态保持；下方旧待授权状态均为历史。

执行前97文件聚合SHA256=`3ba8d89a1a8a1b85610f015e8df8070bbb3cf8700d54756387db6c44317c5f85`完全匹配；两处HEAD/local origin/main=1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3，分支匹配，正式仅五文档、功能37tracked/60actual-untracked、staged0。14migration哈希匹配、24正式库及sidecar路径不存在、8000空闲，QA canonical及完整父链/现有子树无reparse。

本轮允许将 `E:\Agent\comprehensive-cases\15-cyber-town-f009\backend\tests\test_retry_breaker_step4.py:351` 的当前版本断言由(7,)改为(8,)；继续仅在两份既有Step6 QA文件扩展独立用例/隔离编排。产品、既有runner、其他测试不顺带修改。先语义/全量quality，再唯一统一warm-up+5-run；任何新既有缺陷或门禁失败按原硬停止规则报告。Step7/Git交付/部署/删除不执行。

## 2026-09-03：S6-QA-001 修复验证收口

当前状态：`step_6_in_progress / awaiting_retry_test_version_alignment_authorization`。**预算投影缺陷已修复并通过定向/邻近回归；Step5仍保持完成，Step6尚未全部完成。**原“等待预算修复/扩大schema范围授权”已经解除，以下相关文字是历史，不覆盖本节。

新增control v8持久化三项校验副本，固定四scope读取时比对；reserve/settle/release/expiry在原事务同步维护，损坏则回滚并fail-closed；v7升级后首次admission/recovery从ledger重建，不复制旧投影值。保持有界查询、原SQL次数、无跨请求安全缓存、WAL/FULL和全部原门禁。

定向8 passed；完整预算/control/新QA邻近回归135 passed/53历史skip；扩展故障27 passed；综合语义143 passed；根适配4 passed。批次有重叠，不相加冒充独立用例数。三个新进程evaluator均25/25且digest一致；全仓131文件ruff/format/mypy、schema、ignore/sensitive通过。固定100 execution空间前置growth=262144bytes，恰好上限，无余量；完整核心性能尚未执行。

尚待用户回复此前异步问题：`backend/tests/test_retry_breaker_step4.py:351` 当前仍固定user_version=(7,)，需唯一一行改为(8,)以兼容获准迁移。这一行不在原列出的两份既有测试文件中，未擅自修改；不是新产品缺陷，也不是再次申请预算修复授权。其余未完成Step6领域、完整quality/Godot/loopback/唯一1+5性能仍需继续，不能标step_6_complete或进入Step7。

仅获准6文件修改/新增，原94中91文件不变，旧13 migration不变。当前97文件聚合SHA256=`3ba8d89a1a8a1b85610f015e8df8070bbb3cf8700d54756387db6c44317c5f85`。QA根415文件/254后代目录/113212431bytes保留；V30—V33不存在不重建，无Git交付/部署/资源删除命令。详见evidence最前收口节。

## 2026-09-03：S6-QA-001 扩展修复授权执行

状态：`step_6_fix_authorized / projection_integrity_red_pending`。用户已批准上一节所列扩展范围。仅实施有界投影完整性方案，不重做Step5；先失败测试，再产品/迁移，再定向与邻近回归。发现新既有缺陷或超出已列文件立即停止。

## 2026-09-03：S6-QA-001 修复范围核查收口

当前唯一状态：`step_6_blocked / awaiting_bounded_projection_integrity_scope_authorization`。本轮单独修复授权已收到并用于调查及全新失败优先复现，不是再次等待同一授权。原P1仍未修复：全新库同样ledger15→16、active permit1。最小文件范围与既有有界查询/禁止安全缓存/schema冻结约束冲突，按用户“超范围停止”规则未改产品或QA源码。

原94文件及两QA文件指纹不变，13migration匹配。仅五份正式文档更新；本轮新增1个synthetic控制库及1份metadata摘要。QA根累计140文件/54后代目录/32,297,043bytes，全部保留。独立覆盖仍为41通过/1未关闭产品失败；本轮再复现一次同缺陷失败，不算新finding。quality/evaluator/三进程digest及唯一1+5性能仍未运行，不能进入Step7。

准确范围缺口、候选设计、扩展文件及Prompt见evidence最前收口节。以下已获授权前的状态均为历史。

## 2026-09-03：S6-QA-001 单独修复授权与范围核查

用户已单独授权修复预算投影一致性检查。当前状态：`step_6_fix_authorized / projection_integrity_design_check`。原94文件聚合SHA256仍为 `0094cdb520fe8406f764124db4a35e2282e810def7c734d3b52be6bb90b8dc27`；上轮两个QA文件SHA256逐项匹配，功能37 tracked/59 actual untracked/staged0，正式仅五文档/staged0/untracked0。两处HEAD/local origin/main和分支符合登记，diff-check通过，正式数据库及sidecar不存在、8000空闲，QA根canonical及完整父链无reparse。

已读取失败用例、产品projection实现及既有性能契约：每次admission不能恢复O(active ledger)扫描，不能跨请求缓存安全判断，现有13 migration与索引不可改。修复候选必须同时满足这些条件。当前暂未改产品或QA文件；先在全新子目录执行已授权失败优先复现，再明确是否可在原最小范围实施。

## Step 6独立QA：P1阻塞收口（2026-09-03）

当前状态：`step_6_blocked / awaiting_projection_integrity_fix_authorization`。两个预检授权问题已解除；本轮42个不同独立用例为41通过/1产品失败。S6-QA-001：ledger15次已结算且第16次原本被拒绝，将4行projection计数降为0后，产品却放行第16次并留下1permit。违反ledger真相/损坏fail-closed，未改产品。

已按硬停止终止后续quality、evaluator、三进程digest和性能；两个新QA文件静态检查通过，原94文件指纹和13migration不变。新根138文件/52后代目录/32,140,348bytes保留，旧V30—V33不存在不重建；正式三库不存在、8000空闲。不进入Step7或Git交付。

准确复现、覆盖缺口、资源和最小修复Prompt见[evidence](evidence.md)最前Step6收口节。下方准备中/预检阻塞/旧Step5失败均为历史，不覆盖当前状态。

## 2026-09-03：Step 6恢复执行

当前状态：`step_6_authorized / independent_qa_preparing`。用户已确认94文件冻结基线并批准新QA脚本作用域根绑定；恢复指纹、Git、13migration、正式库和端口预检全部符合。首批资源已在evidence最前节创建前登记，实际创建前还须精确路径校验；独立测试未运行。原预检阻塞记录是历史，保留且不作为当前授权阻塞。Step6未完成，不进入Step7/Git交付；既有缺陷硬停止边界保持。

## Step 6 独立QA预检阻塞（2026-09-03）

当前状态：`step_6_preflight_blocked / awaiting_baseline_confirmation_and_qa_root_adapter_authorization`。用户已授权 Step 6，本轮触发预检硬停止；Step 5 保持完成，Step 6 未完成，Step 7 未授权。下方 Step 5 blocked/待授权表述属于完整保留的历史记录，不覆盖本节。

正式五文档登记了 37 tracked modified + 57 actual untracked，但未找到当前 94 文件的完整指纹登记；28 个当前 SHA-256 在本次写入前五文档中均无记录。旧 V9 完整83文件表仅作历史比较：63相同、20不同、11当前文件未列入。不能据此认定产品漂移，也不能把本次观测快照自行认定为获认可基线。

现有benchmark还硬编码V29根，不能直接接入Step6根，未尝试绕过。Git/13migration/正式库不存在/端口检查通过；动态QA、quality、evaluator及性能均未运行。新QA根未创建；V30—V33旧根不存在，不重建；功能worktree/分支/旧根/缓存保留。

恢复前：提供可核验的当前94文件既有登记，或明确确认本次快照 SHA256=`0094cdb520fe8406f764124db4a35e2282e810def7c734d3b52be6bb90b8dc27` 可作为后续冻结 QA 基线；确认仅通过已列入范围的 `scripts/f009_step6_qa.py` 安全接入全新根，保留原测量协议/工作量/门禁/产品路径，禁止修改既有 runner 和产品。准确恢复 Prompt 见 evidence。

完整94文件快照、findings、资源与恢复Prompt见[evidence](evidence.md)最前Step6节。当前不得申请Step7或Git交付。

## Step 5 完成（2026-09-02）

状态：`step_5_complete / awaiting_step_6_authorization`。V33已闭合最后22项测试基础设施失败和4项格式门禁：V14—V19一次性rolling-projection候选在普通pytest中固定安全跳过；steady-profile在自身作用域强制本地HTTP客户端并恢复原independent-client全局值；storage migration测试依据当前注册表验证control v7；4个文件仅作机械格式化。failure-first为3 failed，定向绿测为2 passed/33 expected skipped。

唯一完整fake-only质量入口通过：ignore/sensitive preflight/final、lock、ruff、129文件mypy、schema、Godot import/unit、connectivity 9/9、Dialogue 10基础场景+Multi-NPC、全量pytest `1997 passed / 133 expected skipped`。全仓129文件format、tracked/untracked whitespace、migration哈希、正式数据库不存在及8000端口释放均通过。Step 5已完成，但F-009/R-10未完成；不得自动进入Step6、Git交付、部署或资源删除。

V30—V33综合根已到期，可由用户按evidence中的精确路径手动删除；F-009 worktree、分支、缓存和其余历史根保持不动，Step6仍需单独授权。

## Step 5 Dialogue integration runner 已修复，完整质量入口仍阻塞（2026-09-02）

状态：`step_5_comprehensive_acceptance_blocked / awaiting_remaining_test_harness_authorization`。单场 failure-first 稳定复现旧 `invalid_recovery` 在第一次调用后错误要求 Retry；最小 test-only 修复后 `provider_invalid_response` 保持 `invalid_response`、Retry 不可用、`can_retry()=false`、provider 调用严格为1。全部 Dialogue loopback 的10个基础场景及Multi-NPC通过；unavailable/timeout仍各只执行一次手动Retry，冻结请求不变。没有修改Godot产品、后端产品、migration、Dialogue v1、阈值或业务语义。

完整 `scripts/quality.py` 已通过 ignore/sensitive preflight、lock、ruff、129文件mypy、schema、Godot import/unit、connectivity 9/9和Dialogue loopback，随后全量pytest为 `2008 passed / 100 skipped / 22 failed`。22项均位于本轮未授权的测试基础设施：20项V14—V19 rolling-projection历史候选未与普通入口隔离或仍假定旧索引/阶段allowlist，1项steady-profile测试仍访问已变更runner接口，1项storage migration测试仍固定断言control v6而产品为v7。另行全仓format check仍有4个本轮未授权文件不符合格式。Step 5不能完成，不进入Step 6；下一步需单独授权只调查并修复这些剩余测试harness/格式基线，不得把它们当作产品缺陷直接改产品。

V32根为 `E:\Agent\cyber-town-f009-step5-tests\step5-comprehensive-v32-dialogue-harness`；当前仅作失败证据保留，不复用或删除。其完整盘点见evidence。

## Step 5 综合验收 harness 修复结果（2026-09-02，范围阻塞）

状态：`step_5_comprehensive_acceptance_blocked / awaiting_test_only_godot_runner_authorization`。本轮红测 `4 failed`，最小测试基础设施修复后同组 `4 passed`；综合磁盘/故障回归为 `412 passed / 100 skipped`，其中100项全部是未配置专用全新根时按契约跳过的V7/V8/V9/V10历史一次性runner。固定 evaluator 再次 `19 passed`，25/25 case与三进程digest契约保持通过。普通回归不再读取旧固定根，缺失环境变量不再展开环境映射。

完整质量入口已依次闭合 synthetic `ContextVar token` 假阳性、v7测试格式债务、sibling test双模块名和性能spy静态类型问题；最新一次通过ignore/sensitive、lock、ruff、129文件mypy、schema、Godot import/unit及connectivity 9/9。剩余唯一阻塞是Dialogue loopback旧`invalid_recovery`仍要求`provider_invalid_response`可手动Retry，而F-009冻结契约和Godot单测均明确该错误`retryable=false`。仅改Python fixture的候选已失败并回退；正确修复需要修改`game/tests/run_dialogue_fake_integration.gd`这一测试runner，但本轮明确禁止Godot修改，因此停止。产品、migration、Dialogue v1、Godot产品代码、阈值和业务语义均未修改；Step 5未完成，不进入Step 6。

## Step 5 综合验收测试基础设施最小修复（2026-09-02，已授权）

状态：`step_5_comprehensive_harness_fix_authorized / failure_first_pending`。本轮只修复过期的 control v6 测试断言、普通综合回归对 V7/V8/V9/V10 历史一次性 runner 的默认收集依赖，以及缺失环境变量时异常展开整个环境映射的测试诊断风险；不修改产品、migration、Dialogue v1、Godot、性能阈值或业务语义。

全新登记根为 `E:\Agent\cyber-town-f009-step5-tests\step5-comprehensive-v31-harness-fix`，仅容纳 synthetic pytest/TEMP、隔离业务/control/observability SQLite、25-case evaluator 与三进程 metadata-only 输出、完整 fake-only 质量入口产物。历史 runner 只有在对应专用环境与全新登记根同时存在时才允许运行；普通 pytest/quality 必须安全跳过，不连接、复用或覆盖旧证据 SQLite。全部门禁通过前不得把 Step 5 标记完成，也不得进入 Step 6。

## Step 5 综合验收首次执行（2026-09-02，已停止）

状态：`step_5_comprehensive_acceptance_blocked / awaiting_test_harness_fix_authorization`。固定 evaluator 专项 `19 passed`，25/25 case、11 维度和三个全新 Python 进程均通过，三个 metadata-only 输出完全相同，canonical digest=`1986a20db79cce74dfe458193ce0f2ab52e0d457d047b31d2e9465aeadf624bb`；所有零泄漏/零重复/零非授权指标满足任务卡。

随后综合磁盘/故障回归为 `440 passed / 48 failed / 60 deselected`，触发硬停止。48 项中 47 项来自历史诊断测试对 V7/V8/V9 固定根或专用环境变量的直接依赖，无法作为普通综合测试运行；另 1 项是 Step 4 测试仍把 control `PRAGMA user_version` 固定断言为 v6，而当前已批准并验证的产品版本为 v7。当前证据是测试 harness/过期断言阻塞，尚未确认新的产品缺陷。完整 `scripts/quality.py` 未运行，Step 5 不完成，也不进入 Step 6。

失败堆栈再次由测试框架展开进程环境映射；任何值均未写入本地 summary、项目文档或 Git。后续必须单独授权：把普通综合套件与历史一次性诊断 runner 解耦、把 v6 断言更新到 v7，并增加防止异常渲染整个环境映射的测试安全修复；随后在全新 basetemp 重跑综合回归与完整质量入口。不得在当前状态提交、推送、PR、部署或删除资源。

## V29 in-memory 门禁修订与核心复验完成（2026-09-02）

状态：`step_5_core_revalidation_complete / awaiting_step_5_completion_authorization`。V29 推荐门禁已按用户批准实施，失败优先契约、必要控制/预算/取消/重启/migration 回归和唯一一次统一 1 warm-up + 5 measured 核心矩阵全部完成。核心 `failure_codes=[]`、`warning_codes=[]`；本轮没有修改产品控制状态机、repository、SQL、migration、Dialogue v1 或 Godot，也没有运行 Step 5 综合验收或进入 Step 6。

V29 内存结果：no-recorder control p95/p99=`1.9320/2.3962ms`，in-memory recorder p95/p99=`1.7970/2.3656ms`，recorded-baseline p95 delta=`-0.1350ms`，配对吞吐比=`111.69%`。recorded 五轮 p95=`1.3925/1.7970/1.7701/2.5097/1.9900ms`；本次唯一批次本身也低于旧2ms中位门槛，但没有追加或挑选批次，最终判定使用已批准的 3.0/3.5ms 绝对 warning/fail 与 0.5/0.75ms 配对 warning/fail 契约。

其余阻塞门禁全部通过：SQLite observability p95/p99=`66.8231/185.9938ms`、吞吐=`17.568613/s`、growth=`307200`；pre-dispatch reject p95=`1.2838ms`、dispatch=`0`；正式默认 HTTP control-off/on p95=`68.3627/184.5241ms`，on p99=`209.3907ms`、吞吐=`22.820349/s`、control growth=`262144 bytes`，相对增量=`116.1614ms`，未触发125ms warning或140ms fail。three-SQLite p95/p99=`586.8882/671.2532ms`只产生既有两个非阻塞诊断码。

下一步只能在用户单独授权后执行 Step 5 综合验收；不得把本节状态解释为 Step 5、R-10 或 Git 交付已经完成。

## V29 in-memory 门禁修订执行（2026-09-02，已授权）

用户已批准 V29 推荐契约：在固定 Windows/Python 3.12/fake-only/current-three-fence/统一 1+5 profile 下，recorded p95 `>3.0ms` 产生 warning、`>3.5ms` 才 fail；paired recorded-baseline p95 delta `>0.5ms` 产生 warning、`>0.75ms` 才 fail；原 p99 `<=5ms` 与 paired throughput `>=80%` 保持不变。边界值本身不告警、不失败，profile 变化必须重建基线。

本轮精确功能范围仅为 `backend/src/cyber_town/application/control_performance.py`、`backend/tests/test_control_performance_contract_step5.py`、`scripts/f009_step5_benchmark.py`。执行顺序为失败优先契约、必要语义回归、唯一一次统一 1 warm-up + 5 measured 核心矩阵；不修改产品控制状态机、repository、SQL、migration、Dialogue v1 或 Godot。当前状态：`step_5_v29_gate_revision_authorized / failure_first_pending`。

## V29 Step 0 in-memory 门禁只读评审草案（2026-09-02，等待批准）

本轮没有修改性能契约、产品、测试、migration 或阈值，也没有运行新核心矩阵或创建资源。评审基于 V28 当前三-fence产品路径唯一1+5样本：recorded run-level p95中位=`2.844435ms`、MAD=`0.089335ms`、`median+3*MAD=3.112440ms`、最大=`3.204800ms`；paired baseline中位=`2.723745ms`。逐轮 recorded-baseline p95 delta 为`0.109900/0.608455/-0.200280/0.271300/0.210025ms`，中位=`0.210025ms`、MAD=`0.100125ms`、robust upper=`0.510400ms`。

门禁适用性结论：当前 `2ms` 同时阻断 recorder 和 no-recorder 共用的完整控制状态机，而正式默认 HTTP、p99、吞吐、空间和安全语义均通过；它不能区分 recorder 回归与控制链固定成本。V28 已排除旧API测量、GC、scope-tag重算和无savepoint小修复，继续维持2ms只能选择更大规模的control状态机/SQL重构，风险覆盖取消、故障回滚、replay/waiter、restart及预算归属，且没有可证伪的达标收益证据。

推荐候选（尚未获准）：将相同 Windows/Python3.12/fake-only/current-three-fence profile 的 in-memory gate 分成两层：①完整 recorded p95 `>3.0ms` warning、`>3.5ms` fail；②五轮聚合 recorded-baseline p95 delta `>0.5ms` warning、`>0.75ms` fail；原 p99 `<=5ms` 和 paired throughput `>=80%` 保持。3.0/3.5 来自 recorded 3MAD上界3.1124与观测最大3.2048后的显式warning/工程余量；0.5/0.75来自paired delta 3MAD上界0.5104及额外异常余量，不是从单次最好样本挑选。任何OS、Python/SQLite、产品fence、工作量、顺序或并发变化必须重建基线。

备选候选（不推荐，尚未获准）：维持绝对p95 `2ms`，另行设计并预验证减少完整控制状态机SQL/编排的架构重构。该路线不能采用移除savepoint、禁GC、减少事件、降低工作量或缓存安全判断，必须先证明取消/失败/重启/回滚语义和至少`0.85ms` p95收益；现有证据不足，不能直接实施。

若用户批准推荐候选，精确功能范围仅为`backend/src/cyber_town/application/control_performance.py`、`backend/tests/test_control_performance_contract_step5.py`和`scripts/f009_step5_benchmark.py`；先失败优先锁定边界与稳定warning/failure code，再使用全新已登记测试根执行必要回归和唯一统一1+5核心复验。批准前状态保持`step_5_v28_core_gate_failed / awaiting_in_memory_gate_review_authorization`。

## V28 Step 5 当前产品路径复验与门禁适用性结论（2026-09-02）

状态：`step_5_v28_core_gate_failed / awaiting_in_memory_gate_review_authorization`。V27 内存 runner 仍调用已被 V24 三-fence 取代的分解式 control API；V28 先以失败优先契约将其纠正为产品实际使用的 `admit_provider_dispatch()` / `finalize_provider_success()`，再严格执行一次统一协议 1 warm-up + 5 measured 核心矩阵。除 `in_memory_p95_exceeded` 外所有阻塞门禁通过；Step 5、性能 P1 与 R-10 仍开放，不进入综合验收或 Step 6。

V28 权威内存结果：no-recorder control p95/p99=`2.7237/3.1882ms`，in-memory recorder p95/p99=`2.8436/3.6704ms`，配对吞吐比=`104.33%`。两组共享同一控制链并共同超过 `2ms`，recorder 增量不是阻塞；五轮 p95 分别为 baseline `2.1462/2.2007/3.0447/2.9335/2.7237ms`、recorded `2.2561/2.8091/2.8444/3.2048/2.9338ms`，显示固定成本与同机运行波动同时存在。

问题二继续通过：正式默认 control-off/on p95=`169.9669/234.0655ms`，on p99=`250.1393ms`、吞吐=`18.029168/s`，相对增量=`64.0986ms`，低于 `125ms` warning / `140ms` fail；control growth=`262144 bytes`，恰好满足上限。SQLite observability、pre-dispatch reject、dispatch/成本/数据库完整性也通过；three-SQLite 仍只是非阻塞诊断。

当前产品成功路径每次执行 78 条 SQLite statement，其中七组 nested savepoint 贡献 14 条。只读诊断在不落盘且不作为验收的成功路径上完全移除这些 savepoint 后，固定五轮 p95 仍为 `2.3793ms`，而且该做法会丢失异常隔离/局部回滚，不能实施。结合 V20 已测的 SQL、Python 编排、HMAC/DTO 成本，目前没有证据支持一个保持全部故障语义的“小修复”能可靠回收至少 `0.8436ms` 并留出运行波动余量；继续做无证据微优化风险高于收益。

两个补充的无落盘 non-gating 对照进一步排除小修复路线：同工作量关闭 GC 只把 p95 中位从 `2.5262ms` 降到 `2.4591ms`，GC 不是主要阻塞；同一 execution 复用 player/NPC/player+NPC scope tag 的候选只把 p95 从 `2.6358ms` 降到 `2.5680ms`，吞吐从 `730.147/s` 变为 `719.948/s`，收益落入运行波动且不足以达到2ms，因此不实施。SQL按阶段为 ingress=`6`、provider admission=`43`、success finalization=`29` statements；剩余成本是完整控制状态机的共同固定成本，不是单点查询或 recorder。

门禁来源复核：`2/5ms` 是 F-009 Step 0 为 fake-only 开发/CI 设定的设计预算，任务卡明确标注“不构成生产 SLA”；它早于 V24 durable execution-intent 三-fence 产品路径，且当前正式默认 HTTP 的用户可见绝对、吞吐、相对增量与空间门禁均已通过。不得在本轮擅自修改 `2ms`。下一步需要用户单独授权回到 Step 0，只重审该 in-memory p95 门禁的适用对象和统计阈值；在授权前不得把 V28 解释为通过，也不得继续扩大产品事务架构。

V28 摘要：`E:\Agent\cyber-town-f009-step5-tests\performance-v28-memory-product-path\full-matrix-01\performance-summary.json`，SHA-256=`B0A0D80C87FF9A0194633E386EAEDE33A862E2B4041E7279FDEE5475E3B3500D`。根终盘为 `211 files / 83 descendant dirs / 46,364,362 bytes`，含 `67 SQLite / 66 WAL / 66 SHM / 2 JSON` 及已登记 `tmp` 内 3 组 mypy cache metadata；reparse、`.env*`、nested Git 均为0。资源保留至 Step 5 收口，由用户手动删除，Codex 不删除。

## V27 Step 5 核心性能复验（2026-09-02，已停止）

状态：`step_5_core_revalidation_failed / awaiting_in_memory_gate_decision`。V26 后唯一完整 warm-up + 5-run 核心矩阵已执行且按固定门禁停止；唯一阻塞码为 `in_memory_p95_exceeded`。不得执行 Step 5 综合验收或 Step 6。

内存 recorded 五轮中位 p95/p99=`2.3465/3.2453ms`，相对阈值 `2/5ms`，p95 超 `0.3465ms`；同工作量 no-recorder control p95=`2.4102ms` 也超限，而 recorded/no-recorder 吞吐比=`102.03%`，说明本轮失败属于两者共有的控制链固定成本，不是 recorder 独有回归。non-gating companion 的共同热点仍为 budget reservation、execution admission、budget settlement、ingress admission 和 provider permit acquire。

其余阻塞门禁通过：正式默认 control-on HTTP p95/p99=`217.294/241.6763ms`、吞吐=`19.124091/s`；相对 control-off p95 增量=`69.2078ms`，不触发 125ms warning/140ms fail；control growth=`262144 bytes`，恰好通过上限。SQLite observability p95/p99=`70.9902/169.2042ms`、`16.142476/s`、growth=`307200`；三类 reject p95 均低于2ms且 dispatch=0。three-SQLite p95/p99=`602.2961/740.0241ms`，仍仅为非阻塞诊断。

复验边界保持不变：内存 no-recorder/in-memory recorder 配对，独立 SQLite observability，三类 pre-dispatch reject，正式默认 control-off/control-on + NoOp observability，以及非阻塞 three-SQLite 诊断；真实 HTTP 使用本地 TCP、独立客户端和逐请求计时。阻塞门禁继续采用内存 `p95/p99 <= 2/5ms`、配对吞吐 `>=80%`，SQLite observability `<=150/200ms` 且 `>=8 trace/s`，reject `p95<=50ms` 且 dispatch=0，正式默认 HTTP `<=250/400ms` 且 `>=4/s`，control-on 相对增量 `>125ms` warning、`>140ms` fail，control/observability 空间上限 `256/512KiB`；three-SQLite 仅输出诊断码。

新根固定为 `E:\Agent\cyber-town-f009-step5-tests\performance-v27-core-revalidation`，实际 199 files / 44 descendant dirs / 20,437,923 bytes；summary SHA256=`C811F320551145979208FF1312DB2C6BFD176E10BB1D21EE2356BC1B45B6D6AD`。资源保留至 Step 5 收口，由用户手动删除，Codex 不删除。

## V26 产品 Gate 2 空间门禁解决（2026-08-31，当前权威状态）

状态：`step_5_problem_2_space_gate_resolved / awaiting_step_5_core_revalidation_authorization`。synthetic memory runner 已改为 initialize、普通 repository operation 与 composed transaction 共用同一 `:memory:` connection；修复前红测 `1 failed`，修复后核心三项 `3 passed`，格式化后复验仍为 `3 passed`。green 批次均未创建磁盘 SQLite，BEGIN IMMEDIATE、savepoint、rollback、close 和重复初始化契约通过。

排除独立 V10 候选专项后的 Gate 2 定向回归为 `118 passed / 53 deselected`；更新后的 v7 migration/user_version 断言包含在内。随后唯一五对 fresh control 空间门禁全部通过：每对 baseline occupied growth=`266240 bytes`，product v7=`258048 bytes`，稳定回收=`8192 bytes` 并满足 `<=262144 bytes`；candidate index pages=`3 -> 0`，v6/v7 schema、逻辑 digest、WAL/FULL、integrity/FK、预算/dispatch/归属均通过，failure codes=`[]`。

产品 `0007`、loader 注册和 runner fix 均保持未提交。下一步只能另行批准 Step 5 核心复验；不得把本轮空间结果替代完整性能矩阵、综合对抗、Step 5 综合验收或 Step 6。已知非语义遗留：`test_sqlite_control.py` 有一处既有 ruff-format 长行，本轮严格范围不允许修改，需在后续授权中单独收口。

## V26 产品 Gate 2 memory runner 阻塞（2026-08-31，当前权威状态）

状态：`step_5_problem_2_v26_product_gate_2_memory_runner_blocked / awaiting_benchmark_runner_fix_authorization`。已按补充授权仅把 `test_budget_control_step3.py` 的 migration 清单和 `PRAGMA user_version` 断言从 v6 更新为 v7；预算业务断言未改变。随后在全新 `pytest-followup-01` 中隔离运行两项 memory performance contract，结果仍为 `2 failed`，按硬停止条件没有继续回归或五对空间门禁。

根因已由源码与磁盘 surface 闭合：benchmark `_MemoryControl.initialize()` 经覆写 `_connect()` 把 schema 建在 `:memory:`，但 V24 execution-intent recovery 使用继承的 `_composed_transaction()`，后者经 `_writer` 打开磁盘占位库。两项测试各产生一个 4096-byte `not-created-memory-control.sqlite3`，其中没有 migration 表，因此 `recover_open_execution_intents()` 报缺 `control_execution_intents`。真实文件库专项已通过，当前证据确认这是 synthetic benchmark runner 的双连接缺陷，不是产品 migration 7 缺陷。

下一步必须单独授权只修改 `scripts/f009_step5_benchmark.py` 和对应 memory contract 测试，使 `_MemoryControl` 的 composed transaction 与普通 `_connect()` 使用同一 in-memory connection，并验证关闭/rollback/重复运行不创建磁盘占位库。修复通过后才能复验 v7 断言及排除 V10 的定向回归，再决定是否运行五对空间门禁。

## V26 产品 Gate 2 定向回归阻塞（2026-08-31，当前权威状态）

状态：`step_5_problem_2_v26_product_gate_2_regression_blocked / awaiting_test_scope_authorization`。失败优先阶段得到预期 `8 failed`；注册 migration 7、增加精确 append-only `0007_drop_redundant_budget_owner_npc_index.sql` 并补齐授权测试/runner 后，同一 8 项专项为 `8 passed / 35 deselected`。`0007` 仅含获准的 `DROP INDEX idx_budget_owners_npc;` 与 `PRAGMA user_version=7;`，`sqlite_control.py` 仅增加 migration 7 注册。

扩大定向回归得到 `113 passed / 57 failed`，触发硬停止，因此没有运行五对 fresh control 空间门禁，也没有生成 Gate 2 summary。失败分类：2 项是未在本轮授权修改范围内的 `test_budget_control_step3.py` 仍把 user_version/migration 清单固定为 v6；53 项属于旧 V10 候选专项缺少其独立 synthetic 环境，不是本 Gate 2 产品语义结论；另 2 项 memory performance contract 需在全新 basetemp 中隔离复核，当前不得判断为产品缺陷。原始失败输出未写入报告；其中测试框架展开了进程环境映射，证据仅保留脱敏分类，不保留或复述任何值。

产品 `0007` 及测试修改保持未提交，不回退、不扩大 schema。下一步需单独授权：①仅更新 `backend/tests/test_budget_control_step3.py` 的 v7 migration/version 断言；②在新登记 basetemp 隔离复核 2 项 memory contract；③明确 V10 专用候选测试从本 Gate 2 回归集合排除，或另行提供全新 V10 环境授权。上述收口通过后才可重新申请五对空间门禁；当前不得标记 `space_gate_resolved`。

## V26 query-plan Gate 1 修复通过（2026-08-31，当前权威状态）

状态：`step_5_problem_2_v26_query_plan_gate_1_complete / awaiting_revised_product_gate_2_authorization`。在全新授权根中，baseline 由初始化完成后的独立只读连接取得 EXPLAIN；candidate 精确执行 `DROP INDEX idx_budget_owners_npc` 并 commit、关闭写连接后，再由全新只读连接验证。candidate 的 `sqlite_master`/`PRAGMA index_list` 均不存在该索引，dbstat pages=`0`，active-NPC EXPLAIN 不再引用该索引；三个正常预算查询计划与 baseline 逐项一致。summary status=`query_plan_gate_passed`、failures=`[]`。

本轮只修复 synthetic query-plan probe。没有重跑 history、空间五对或完整性能矩阵；上一轮已通过的 history/空间证据保持只读且未连接旧 SQLite。产品 `0007` 未创建。下一步必须单独批准修订后的产品 Gate 2：允许 `sqlite_control.py` 注册 migration 7，并允许 append-only `0007` 精确包含 DROP INDEX 与 `PRAGMA user_version=7`；不得修改其他 repository 逻辑。

工程收口：纯契约 `11 passed`；两文件 ruff、format、mypy、tracked/untracked whitespace 通过；0001—0006 哈希不变；两套新 synthetic control SQLite integrity=`ok`；正式/功能三类数据库均不存在，8000 空闲。新根终盘=`7 files / 6 descendant dirs / 362790 bytes`，无 reparse、`.env*`、嵌套 Git 或禁止原文命中；保留至 Step 5 收口，由用户手动删除，Codex 不删除。

## V26 synthetic Gate 1 失败并停止（2026-08-31，当前权威状态）

状态：`step_5_problem_2_v26_synthetic_preflight_failed / awaiting_query_plan_probe_fix_authorization`。唯一失败码为 `candidate_query_plan_retained_dropped_index`：同一 query-plan 数据库执行 synthetic `DROP INDEX idx_budget_owners_npc` 后，`EXPLAIN QUERY PLAN` 仍报告该索引。五个 candidate 空间数据库的 `dbstat` 均确认候选索引页面为 0，因此当前证据更像同连接 statement/schema cache 导致的诊断冲突，但按用户硬停止条件不得修补或重跑。

其余 Gate 1 证据均通过但不能越过上述失败：100/1,000/10,000 ledger 的 baseline/candidate 结果一致，candidate 最坏缺失 NPC lookup p95=`27.79ms <= 50ms`；五对空间均为 baseline growth=`266240`、candidate=`258048`、saving=`8192 bytes`，且 integrity/FK/归属/零成本正常。产品 `0007` 未创建，Step 5/R-10 继续开放。

后续若要继续，必须单独授权 query-plan probe 使用“DROP commit 后关闭连接，再以全新连接执行 EXPLAIN”的修复并在全新 V26 子根复验，不得复用本轮数据库。另需在进入产品 Gate 2 前解决已发现的授权范围冲突：现有 migration loader 要求把 `(7, 0007...)` 加入 `sqlite_control.py`，且 migration 必须设置 `PRAGMA user_version=7`；原“0007 只能含 DROP INDEX、不得修改 repository”范围无法被产品加载。

## V26 独立 8KiB control 空间修复（2026-08-31，当前执行）

状态：`step_5_problem_2_v26_space_preflight_authorized / failure_first_pending`。本轮先只在 synthetic v6 control SQLite 删除候选非唯一索引 `idx_budget_owners_npc`，验证 query plan、缺失 projection fail-closed、100/1,000/10,000 ledger 规模和五对 fresh 空间门禁；全部通过后才允许进入产品 `0007`。不运行完整性能矩阵、Step 5 综合验收或 Step 6。

候选根为 `E:\Agent\cyber-town-f009-step5-tests\performance-v26-control-space-index`，全部目录和文件 surface 已在 evidence 预登记；仅含 synthetic pytest/TEMP、control SQLite/WAL/SHM 和 metadata-only 摘要，保留至 Step 5 收口后由用户手动删除。Codex 不删除资源。

## Step 0 control-on 门禁修订实施完成（2026-08-31，当前权威状态）

状态：`step_0_control_overhead_gate_revision_complete / awaiting_8kib_space_fix_authorization`。已按用户批准把同一运行 profile 的 control-on p95 overhead 契约改为：增量 `>125ms` 记录 `control_on_relative_p95_warning`，增量 `>140ms` 才记录既有阻断码 `control_on_relative_p95_regression`；边界值 125/140ms 本身分别不告警/不失败。

精确功能范围为 `application/control_performance.py`、`scripts/f009_step5_benchmark.py` 和 `test_control_performance_contract_step5.py`。性能契约新增固定常量及 metadata-only warning evaluator；完整核心 runner、V13 storage A/B 和 V21/V24 HTTP pair 的摘要均输出 warning codes，但 warning 不改变退出码。HTTP p95/p99=`250/400ms`、吞吐、control 空间、dispatch/retry/计费/业务写入、WAL/FULL、路径身份和全部语义门禁未改变。

失败优先证据：新增测试最初因常量/evaluator 不存在在 collection 阶段失败；实现后边界专项 `2 passed`。首次扩展绿测因测试仅构造两个场景却错误断言完整门禁为空而得到 `1 failed / 1 passed`，收窄为只检查本轮稳定 warning/failure code 后，最终相关契约 `5 passed / 23 deselected`。ruff、format、mypy 三文件全绿；未运行新性能矩阵、服务或 SQLite。

依据 V24 既有 summary 重新解释时，延迟增量 `117.1586ms` 低于 125ms warning 边界，因此延迟项通过修订契约；这不是新性能结果。问题二仍受 control 空间 `270336 > 262144 bytes` 独立阻塞，Step 5 与 R-10 仍未完成。下一步只能另行批准 8KiB 空间候选，不得自动运行矩阵或 Step 5 综合验收。

## Step 0 control-on 相对 p95 门禁重审（2026-08-31，历史评审记录）

状态：`step_0_control_overhead_gate_review_complete / awaiting_threshold_revision_authorization`。本轮只读复核 V13、V21、V22、V24、V25 的真实 TCP、独立客户端、WAL/FULL、1 warm-up + 5 measured 证据，没有运行新矩阵、修改产品/migration/业务语义或进入 Step 6。

原门禁 `on p95 - off p95 <= max(off p95 * 20%, 30ms)` 是 Step 0 冻结的设计预算，不是从项目实测基线推导的 SLA。现有五组五轮汇总增量为：V13 E USB=`98.1198ms`、V13 C NVMe=`86.3302ms`、V21 五边界=`90.9713ms`、V22 group-commit=`125.2705ms`、V24 三-fence=`117.1586ms`。两种介质与三代 durability 架构均从未达到 30ms；同时这些批次的 control-on 绝对 p95/p99 与吞吐多数通过 `250/400ms`、`>=4/s`，说明 30ms 阻断的是固定安全持久化成本，而不是用户可见总延迟失控。

统计口径：上述五个汇总增量的中位数=`98.1198ms`，MAD=`11.7896ms`，`median + 3*MAD = 133.4886ms`；历史最大汇总增量=`125.2705ms`。V24 当前产品基线为 `117.1586ms`。据此建议把同一机器/同一 profile 的硬门禁修订为：`control-on p95 - control-off p95 <= 140ms`；`>125ms` 先标记 warning，`>140ms` 才 fail。140ms 是将 robust 上界 133.49ms 向上取整的工程余量，不是生产 SLA，也不覆盖绝对 HTTP 门禁。

适用 profile 必须同时满足：Windows 本地 fake-only、Python 3.12、真实 loopback TCP、独立客户端、FakeProvider、NoOp observability、business + control SQLite、WAL/FULL、每次 lease 路径身份检查、相同 synthetic fixture/并发/工作量、1 warm-up + 5 measured、每轮 100 execution、五个 run-level p95 的中位数、全部慢样本保留。任何 OS、Python/SQLite、硬件类别、durability、concurrency、工作量或 observability mode 改变都必须建立新 baseline，不能套用 140ms。

回归规则保持两层：① control-on 绝对 p95/p99=`<=250/400ms`、吞吐=`>=4/s` 继续硬阻断；② control overhead 五轮汇总增量 `>125ms` warning、`>140ms` fail。额外报告五轮 paired delta 的 median/MAD/min/max 作为诊断，但不替换既有“各场景五个 run-level percentile 中位数”的验收算法。space、dispatch、重复计费/业务写入、WAL/FULL 和语义门禁完全不变。

该评审轮本身没有修改代码中的 30ms 常量；随后用户已单独批准并完成 125/140ms 契约实施，以上内容仅保留为决策依据。8,192-byte 空间超限仍独立开放；Step 5、R-10 均未完成。

## 问题二 V25 三-fence 有界归因收口（2026-08-31，当前权威状态）

状态：`step_5_problem_2_v25_attribution_blocked / awaiting_architecture_or_step_0_decision`。V25 没有得到可信的逐请求三-fence outer attribution：`*-01` 因 Python SQLite 缺 `dbstat` 停止；`*-02` 暴露并发到达序号不能代表 request_id；`*-03` 进一步证明 ingress storage call 在 control worker 中执行，worker 的 `ContextVar` 变更不会传播回请求 task，因此 task-local 延迟绑定仍不成立。按“三次失败即停止”的既定边界，没有创建第四批、没有生成 `summary.json`，不得用失败探针结果替代 V24 plain gate。

现有 V24 可信证据已经排除两个方向：control-on/off 的 connection count 均为 `207/100 requests`，因此新增连接不是相对增量；control writer wait p95 仅 `0.0112—0.0158ms`，因此 writer 锁也不是主因。control-on 相比 off 每 100 请求增加 `304` 次 writer/path lease 和 `301` 次 write commit，符合每请求三个 durable fence。control-on path-check p95=`3.7009—4.4684ms`，全部写提交 p95=`9.4659—16.3477ms`。这些是“固定三次 WAL/FULL durability + 每次路径身份检查”为结构性成本的中强证据，但因为缺少逐请求/fence 关联，不能严谨宣称 30ms 已被证明物理不可达，也没有证据支持继续做局部代码微调。

空间页归属已经完整：V24 聚合以 occupied bytes 计量，空 v6 schema 为 `36 pages / 3 freelist / 33 occupied`，100 execution 后为 `98—99 pages / 0 freelist`，occupied growth=`65—66 pages`；冻结上限为 `64 pages`，最差正好多 `2 × 4096 = 8192 bytes`。66 个增长页中，表=`54`、PK/UNIQUE 必要约束索引=`6`、三个 owner scope 非唯一索引=`6`；新 `control_execution_intents` 表占 `3` 页。空间没有不可解释泄漏。三个非唯一索引各占 `2` 页且被缺失 projection row 的 fail-closed ledger 检查使用；删除其中一个理论上足以回收 2 页，但会把对应异常检查从索引查找退化为扫描，未经专门 query-plan/规模/故障性能预验证不能认定为安全最小修复。

决策：停止无证据微优化。若坚持 `<=30ms` 相对门禁，下一步必须单独设计超出当前三次同步 fence 的架构调整，并重新证明取消、崩溃、replay/waiter 和 durability 语义；若不扩大架构，则回到 Step 0，依据 V24 真实 TCP 基线重审相对门禁。空间问题可另行授权“仅一个非唯一 owner scope 索引”的 append-only 候选预验证，但它不能解决延迟。问题二、性能 P1、Step 5 和 R-10 均保持开放。

## 问题二 V24 execution-intent 产品实施启动（2026-08-31，当前权威状态）

状态：`step_5_problem_2_v24_performance_gate_failed / awaiting_next_authorization`。用户批准的三-fence语义已经产品化，append-only `0006_control_execution_intent.sql`、repository/application 状态转换以及取消/restart/replay/waiter/迟到/真实三库归属均通过。真实 TCP 1+5 仍失败：control-on 相对 p95 增量 `117.1586ms > 30ms`，control growth `270336 > 262144 bytes`；绝对 p95/p99、吞吐和副作用归属通过。问题二尚未解决，按硬门禁停止。

V24 测试根已按登记创建：`E:\Agent\cyber-town-f009-step5-tests\performance-v24-execution-intent-product`。首次启动现场 `tcp-1plus5` 保留；有效门禁位于 `tcp-1plus5-retry-01`，summary SHA256=`7D7BFE23DEFAEFB1EF93B579449FD90A41D2E0D1EB311EFFD89EBC9DFA18B6A4`。资源由用户在 Step 5 收口后手动删除，Codex 不删除。

## 问题二 V23 execution-intent synthetic 预验证通过（2026-08-31，当前权威状态）

状态：`step_5_problem_2_v23_synthetic_preflight_passed / awaiting_product_architecture_authorization`。test-only 三-fence execution-intent 状态机在用户为预验证确认的两项语义下闭合：execution quota 仅在 provider attempt intent 创建时消费；intent 后 receipt 未知的 restart 保守结算；clean cancellation 在 provider 调用前 release。正常成功路径模型为 ingress / intent / final 三个 durable fence。

最终完整 architecture probe 为 `16 passed`；semantic 摘要状态为 `synthetic_candidate_passed`。6 个 execution 产生 6 个 quota + intent、5 个 settlement、1 个 clean release、2 个 conservative settlement；重复 dispatch、settlement、business-write claim 均为 0。owner/waiter/replay/conflict、迟到结果丢弃、重复 recovery、prepare/finalize rollback、provider 已开始后的取消均通过；integrity=`ok`、FK violations=0、scope/payload禁止命中=0。

本轮没有创建产品 `0006`，V21 六个产品/基准文件哈希保持不变，11 份既有 migration 未修改。结果只证明候选状态机在 test-only control SQLite 内语义可闭合；尚未证明产品 repository 接入、真实 business SQLite 跨库写入归属或 30ms 性能门禁。因此问题二、性能 P1、Step 5 和 R-10 仍开放，不得进入 Step 5 综合验收或 Step 6。

下一步如获单独授权，才允许 append-only 产品 `0006_control_execution_intent.sql`、control/application/repository 接入及磁盘语义回归；必须先证明业务写入 permission 的唯一归属，再运行单请求 commit 计数和真实 TCP 1+5。任一重复副作用、取消/restart 差异或相对 p95 仍超限即停止。

## 问题二 V23 execution-intent synthetic 预验证（2026-08-31，当前执行）

状态：`step_5_problem_2_v23_synthetic_preflight_authorized / failure_first_pending`。用户仅为 synthetic 候选确认两项预验证语义：execution quota 在真正进入 provider attempt 边界时消费；durable dispatch intent 后若崩溃且 provider receipt 未知，restart 按“可能已 dispatch”保守结算；clean cancellation 在 provider 调用前仍 release。本轮只扩展既有 architecture probe 和测试，不创建产品 `0006`，不修改产品 repository、Dialogue v1、Godot 或既有 migration，不运行完整性能矩阵、Step 5 综合验收或 Step 6。

唯一新根为 `E:\Agent\cyber-town-f009-step5-tests\performance-v23-execution-intent-preflight`。固定 surface：`tmp`、`pytest-red-01`、`pytest-green-01`、`semantic-01`、`semantic-01\control.sqlite3{,-wal,-shm}`、`semantic-01\summary.json`。仅允许 synthetic UUID/fixture、pytest/TEMP、测试专用 control SQLite 与 metadata-only 摘要；禁止 business/observability/正式数据库、`.env*`、真实 scope/payload/秘密及 F-005 资源。保留至 Step 5 收口，由用户手动删除精确根，Codex 不删除。

硬门禁：三-fence 状态机必须覆盖 clean cancel、intent 后 crash/restart、replay/waiter、迟到结果、重复 recovery、重复 dispatch/计费/业务写入和事务回滚；终态与归属必须唯一。若需要 provider receipt、语义不闭合或无法证明唯一归属，立即停止，不实施产品候选。

## 问题二 V22 精确回退与单请求持久化边界重设计（2026-08-31，当前权威状态）

状态：`step_5_problem_2_v22_rolled_back / awaiting_single_request_durability_architecture_decision`。已仅回退 V22 在六个授权文件中的 group-commit 增量，保留 F-009 Step 1—5、问题一产品 `0005`、V21 五边界修复及全部其他未提交实现。V22 symbols 命中为 0；V21 语义集合在全新 `semantic-01\run-04` 为 `153 passed / 55 deselected`；ruff、format、mypy、diff check 通过；功能文件集合恢复为 `33 tracked modified + 53 actual untracked + 0 staged`。

单请求成功路径的五个现有 durable fence 为：① JSON decode 前的 ingress 限流；②幂等 owner 建立时的 execution admission；③ provider 前的 breaker + budget reservation + permit；④真正调用 provider 前的 dispatched 标记；⑤ provider 完成后的 budget settlement + breaker result + permit release。③与⑤已经分别各用一个物理事务；provider await 不能放在数据库事务内。④若提前并入③，崩溃/取消发生在“intent 已落盘但 provider 尚未收到请求”的窗口时，当前 `released-before-dispatch` 与 `settled-after-dispatch` 语义无法区分；V21 四边界原型已经实际捕获该缺陷。V22 只合并不同请求的同时 fence，不能合并同一请求的因果边界。

在保持以下条件全部不变时，不存在可证明等价的进一步 fence 合并：WAL/FULL、每次继续前实际 durability、decode 前 ingress、防重复 execution、provider 前预算/permit、provider 调用前 dispatch 归属、取消与 restart 精确区分、provider 无可验证幂等回执。因此不得继续无证据微优化或再次包装 group-commit。

候选 A（推荐的可实施方向，但需要新语义授权）：新增 append-only control `0006_control_execution_intent.sql` 与统一 `control_execution_state`，正常成功路径收敛为三个 fence：ingress；`execution admission + breaker + budget + permit + dispatch intent`；final settlement/result/release。权威 budget ledger 及 `0005` 保留。clean cancellation 在 provider 调用前仍可 release；进程在 intent 已持久化、provider receipt 未知的极小窗口崩溃时，restart 必须按“可能已 dispatch”保守结算。execution rate 也改为只在真正进入 provider attempt 边界时消费。该候选预计减少正常路径两次 FULL commit，但明确改变 admission 时点和 crash-window 归属，必须由用户单独确认；不得把它描述为零语义变化。

候选 B（保持精确 dispatch 语义，但当前边界外）：要求 provider 支持 execution-scoped idempotency key 与可持久验证的 dispatch receipt；本地 journal 可在重启后确定外部调用是否被接受，再合并 intent/dispatch。它需要 provider contract、FakeProvider 与真实 provider 适配，且在现有外部模型 API 未证明支持前不可实施；仍需另行设计 valid request 的 ingress/execution 合并，否则正常路径至少四个 fence，未必能满足 30ms。

推荐决策：若目标是继续解决问题二，应先单独批准候选 A 的两项语义变化及 synthetic 架构预验证；先建立取消/崩溃/restart/replay/waiter 的失败优先状态机，再运行真实 TCP 1+5。若不接受任何语义变化，也不引入 provider receipt，则当前 30ms 相对门禁与严格 durability 架构存在边界冲突，应回到 Step 0 重新决定门禁，而不是继续实施局部优化。

## 问题二 V22 group-commit 门禁失败（2026-08-31，当前权威状态）

状态：`step_5_problem_2_v22_core_gate_failed / awaiting_rollback_or_architecture_decision`。V22 bounded coordinator、逐item savepoint、取消drain及API/Dialogue routing已实现；并发专项证明两个同时item可共享一次物理commit，item级逻辑/仓储失败互相隔离，真正SQLite物理故障整批回滚。完整语义集合为`158 passed / 55 deselected`，六文件ruff、format、mypy和diff check通过。

固定真实TCP 1 warm-up + 5 measured门禁失败：control-off/on p95=`104.4321/229.7026ms`，实际增量=`125.2705ms`，允许增量=`30ms`；唯一失败码为`control_on_relative_p95_regression`。on绝对p95/p99、吞吐、control增长`258048 <= 262144 bytes`、dispatch和数据库审计均通过。

根因结论：固定矩阵按独立客户端逐请求等待，同一逻辑fence几乎没有同时到达的其他request可合批。五个measured on run每100请求仍有`590—598`次write commit和`492—500`次control path check，与V21约五次control lease/request基本等价；group-commit只改善同时并发请求，不能降低单请求内部按顺序等待的durable fence。因此问题二、性能P1、Step5和R-10继续开放。按停止条件不得继续扩大架构或放宽阈值；V22六文件候选保留未提交，等待用户授权精确回退，或另行批准重新设计持久化边界。

## 问题二 V22 group-commit 实施（2026-08-31，已授权）

状态：`step_5_problem_2_v22_authorized / failure_first_pending`。用户已明确批准六文件范围和 V22 测试根。V21 已证明每请求五个逻辑 durable fence 仍产生约五次物理 control commit，五轮相对 p95 增量 `90.9713ms > 30ms`。V22 不删除任何 fence，而只让同一 event-loop turn 内的并发请求在同一 fence 上共享一次物理 WAL/FULL commit。

设计边界：`SafetyControl` 增加 event-loop-owned bounded coordinator；API ingress、Dialogue control call、provider admission/finalization 均提交 typed operation。flush 只等待一个 `call_soon` 调度点，不使用计时 sleep；已取消且尚未开始的 item 不执行，已开始 item按现有 finish-on-cancel语义drain。repository在一个`BEGIN IMMEDIATE`内顺序执行各item；每个既有repository方法继续用savepoint保持独立结果，逻辑异常只回滚该item；外层SQLite/commit故障则整批回滚并fail-closed，不向任一调用方提前返回成功。所有future只在FULL commit完成后解析。

顺序/隔离不变量：单 request 的 ingress → execution admission → pre-provider → dispatch → post-completion 顺序不变；同 request replay/waiter 仍只有 owner 产生 operation；不同请求可以共享物理 commit，但预算、bucket、breaker、permit和返回异常逐item归属。不得跨provider await持有transaction，不减少路径身份检查频率（每个物理lease检查一次），不改变migration、SQL schema、WAL/FULL或recovery。

授权范围严格为六文件：`backend/src/cyber_town/application/control.py`、`backend/src/cyber_town/application/dialogue.py`、`backend/src/cyber_town/api/dialogue.py`、`backend/src/cyber_town/infrastructure/control/sqlite_control.py`、`backend/tests/test_dialogue_control_step2.py`、`scripts/f009_step5_benchmark.py`。新根为`E:\Agent\cyber-town-f009-step5-tests\performance-v22-control-group-commit`；创建时间登记为`2026-08-31T13:12:15+08:00`。固定一级surface为`tmp`、`pytest-red-01`、`pytest-green-01`、`semantic-01`、`performance-01`；pytest管理的用例目录只能位于对应basetemp内。内容仅限synthetic pytest/TEMP、FakeProvider、隔离business/control SQLite、WAL/SHM和metadata-only摘要；不得包含observability SQLite、`.env*`、真实scope/payload/秘密、正式数据库或F-005资源。保留至Step 5收口，届时由用户手动删除精确根，Codex不执行删除。

失败优先顺序：先验证两item同批仅一物理commit、结果/异常逐item隔离、取消前后、批外故障全回滚及commit后才唤醒；再跑预算/限流/熔断/幂等/取消/重启磁盘回归；最后运行真实TCP 1+5。停止条件为任一语义差异、batch归属率不足100%、未授权资源，或相对p95仍超过30ms。即使group-commit失败，也不得放宽阈值。

## 问题二 V21 durable boundary 修复启动（2026-08-31，当前执行）

状态：`step_5_problem_2_v21_failure_first / control_on_relative_p95_gate_open`。目标是在不改变预算、限流、熔断、幂等、取消、重启恢复、路径身份检查和 WAL/FULL 语义的前提下，减少正常 control-on 请求的 durable SQLite 提交次数，并以既定相对门禁 `on p95 - off p95 <= max(off p95 * 20%, 30ms)` 判定完成。

只读证据确认：V13 每 100 个请求，control-off 为 `102 write commits / 1 empty commit / 2 path checks`；control-on 为 `903 write commits / 103 empty commits / 905 path checks`。差额即 control-on 每请求约 `8.01` 次写提交、`1.02` 次空提交和 `9.03` 次路径检查。C NVMe 上 control-on 相对增量仍为 `86.33ms > 30ms`，E USB SSD 为 `98.12ms > 30ms`，因此问题不是单纯换盘可解。

V21 不复用已失败的 V12 调用层长事务。当前可证伪假设为：把正常 provider 调用前的 breaker/budget/permit/dispatch 状态收口为一个仓储内部短事务，把成功后的 settlement/breaker-result/permit-release 收口为另一个仓储内部短事务；所有调用仍等待实际持久化，provider 前后 durable fence、取消/失败/retry/replay/waiter 和 recovery 语义不变。先建立提交次数红测和磁盘语义回归；若正常路径无法降至目标提交边界，或任何语义变化，立即停止，不运行性能矩阵。

失败优先基线已建立：新增的单请求契约在全新 `pytest-red-01/run-02` 稳定得到 `(COMMIT, path-check)=(9,9)`。首个四边界原型虽达到 `(4,4)`，但磁盘取消回归证明把 dispatch 合入 pre-provider 事务会使“reservation 期间取消”过早留下 dispatched 状态；该方向已被语义门禁否决。当前候选恢复独立 dispatch fence，目标为 `(5,5)`，不得以少一次提交交换取消语义。

新资源根预登记为 `E:\Agent\cyber-town-f009-step5-tests\performance-v21-control-durable-boundary`；准确一级 surface 为 `tmp`、`pytest-red-01`、`pytest-green-01`、`semantic-01`、`performance-01`。仅允许 synthetic pytest/TEMP、FakeProvider、隔离 business/control SQLite、必要 WAL/SHM 和 metadata-only 摘要；不含 observability SQLite、`.env`、真实秘密、真实对话或 F-005 资源。保留至 F-009 Step 5 收口，由用户手动删除；Codex 不执行删除。

首次性能启动在 `performance-01\loopback-off-0` warm-up 导入独立客户端时因仓库根未进入 `PYTHONPATH` 中止；该目录作为中止证据保留，不复用、不覆盖。完整批次追加一级目录 `performance-02`，内容边界与原登记相同。

V21 五边界候选已完成语义与性能验证，但**尚未解决目标门禁**。成功 HTTP 从 `(9 COMMIT,9 path-check)` 降至 `(5,5)`；控制/熔断 `33 passed`、预算/仓储 `79 passed`、磁盘取消/重启/回放/长期写入 `25 passed`，四边界取消缺陷修正后的专项 `2 passed`。完整真实 TCP 1 warm-up + 5 measured 得到 control-off/on p95=`72.3115/163.2828ms`，增量=`90.9713ms > 30ms`；绝对 on p95/p99、吞吐、空间、dispatch 和数据库审计通过，唯一性能失败码仍为 `control_on_relative_p95_regression`。

结论：单请求局部合并足以减少44.4%的 control lease/commit，但不能关闭相对门禁；性能 P1 与目标继续开放。下一候选不得继续微调 SQL，而应验证跨并发请求的 durable group-commit 是否能在不改变四个必需 fence（ingress、execution admission、pre-dispatch、post-completion）及各请求独立回滚/错误归属的前提下共享物理提交。若四个 FULL fence 的实测下界仍超过30ms，应报告冻结阈值与当前持久化架构冲突，不得放宽阈值或伪造通过。

## 问题一独立修复完成（2026-08-31，当前权威状态）

状态：`step_5_problem_1_budget_history_growth_resolved / problem_2_and_step_5_still_open`。产品 control schema 已以 append-only `0005_budget_window_projection.sql` 增加“权威 ledger + 可重建滚动汇总”；每次 admission 只读取当前四类 scope 的固定汇总行，不再扫描最近 24 小时全部 ledger。旧查询在 1000 条 ledger 时约 `52,107` SQLite VM steps；产品投影 lookup 在 100/1000 条时为 `188/178` steps，10 倍历史增长没有增加查询工作量。

权威 ledger、四类 scope、严格 cutoff、reserve/replay/dispatch/settle/release、16 并发、回滚、重启重建及 fail-closed 语义保持。相关回归本轮最终为 `3 + 69 + 109 passed`，ruff、format、mypy、whitespace 和旧 migration hash 通过。整条控制链的 `p95 <=2ms` 与 control-on 多次 durable commit 属于剩余基础成本/问题二，不能反向否定问题一已经消除 O(n) 历史扫描；Step 5、性能 P1 与 R-10 仍未完成。

资源 `E:\Agent\cyber-town-f009-step5-tests\problem1-budget-projection-product` 当前为 227 files、248 descendant directories、42,987,613 bytes，均为隔离 synthetic control SQLite；reparse、`.env*`、nested Git 均为0。保留至 F-009 Step 5 收口，由用户手动回收，Codex 不删除。

## V20 控制链固定成本归因完成（2026-08-31，当前权威状态）

状态：`step_5_v20_fixed_cost_attribution_complete / awaiting_control_state_boundary_design_authorization`。V20 仅扩展 synthetic attribution 工具与测试，使用 V19 single-write rolling projection 候选完成唯一一组 1 warm-up pair + 5 measured pair、每场1000 execution 的 non-gating 归因；未实施产品 `0005`，性能 P1、Step 5 和 R-10 继续开放。

baseline 五热点合计均时约 `1.056843ms`：事务框架 `0.031866ms / 3.02%`、SQL `0.309551ms / 29.29%`、HMAC/DTO `0.138308ms / 13.09%`、剩余 Python 状态校验/编排 `0.573922ms / 54.31%`。recorded 对应为 `1.114199ms`，占比约 `2.95% / 28.87% / 15.70% / 53.37%`。五个 baseline p95 为 `2.4310/2.4587/2.4424/2.3405/2.0954ms`，带探针结果仅用于归因，不替代 V19 plain 门禁。

决策：不把 execution-level scope tag 复用作为主修复；即使理想化消除全部 HMAC/DTO，也只覆盖五热点均时约13%，不足以解释或关闭 V19 baseline p95 的 `0.6911ms` 缺口。也不重启 V12 式简单事务批次：事务框架本体仅约3%，且 V12 已实测扩大临界区、增加取消复杂度而无稳定收益。下一步应只起草“execution control context + durable control state boundary”方案，同时减少重复 SQL/owner lookup/状态校验/Python DTO 编排；scope tags 只作为该边界内的安全复用项，不单独落地。未经新授权不得实施。

## V19 single-write rolling projection 门禁失败（2026-08-31，当前权威状态）

状态：`step_5_v19_single_write_performance_gate_failed / awaiting_next_performance_decision`。本轮 synthetic 候选成功消除两类固定 SQL 开销：每 1000 execution 的 lifecycle delta 从 4000 降为 2000 条写语句；expiration 从 3996 降为 1939 条语句（999 probe + 940 update），59 个无过期批次完全跳过 totals 写入。语义、四 checkpoint、空间、稳定性、吞吐、p99 和隐私通过。

仍失败三项资格：recorded plain p95=`3.0901ms > 2ms`；reservation stage p95=`1.0247ms`，相对 V17 基准不是至少 35% 降低而是慢 5.14057%；settlement=`0.4372ms`，仅改善 4.248795%（要求至少 20%）。baseline p95 本身为 `2.6911ms`，说明剩余阻塞不是只由 recorder 或已消除的固定 SQL 数造成。候选不具备产品 `0005` 实施资格；性能 P1、Step 5 和 R-10 保持开放。

expiration 在同一事务和快照内合并 1h/24h 过期区间：先做固定参数化存在性探测；无记录时只推进 projection state，不写 totals；有记录时才用一条聚合 UPDATE 应用 delta，并以缺失 scope guard 阻止部分更新。ledger、严格 `reserved_at_ns > cutoff`、四类 scope、replay/并发/rollback/rebuild、WAL/FULL、CHECK/PK/FK/UNIQUE 和全部冻结阈值不变。

新根：`E:\Agent\cyber-town-f009-step5-tests\performance-v19-projection-single-write`。最终摘要 `summary-v19-03.json`，SHA256=`469A0FD30DEBA99FAF4DA587DB74EE8AFE19EC425B7FB64CF624790C37AAFB8C`。资源保留至 Step 5 收口，由用户手动删除，Codex 不删除。

红测使用 `pytest-red-01\run-01`；首轮 green 使用 `pytest-green-01\run-01`。历史 V18 completed-root freshness 断言修正后的独立复核追加 `pytest-green-01\run-02`，内容边界相同且不得复用旧 basetemp。

`run-02` 为 33 passed；格式/类型及 runner 收口后的最终定向复核追加 `pytest-green-01\run-03`，不得复用 run-01/run-02。

首次正式批次在 `validation-01` 的 clock-rollback checkpoint 因诊断 mixin 动态重建调用错误触发 `AttributeError`；无摘要，未进入 space/plain/stage，不作为候选语义结论。保留该证据不覆盖。修正仅限 synthetic runner，完整重跑追加 `validation-02\semantic|space|plain|stage` 和完成时 `summary-v19-02.json`；不得连接、复用或修改 `validation-01` 数据库。

`validation-02` 的 16 reserve/settlement、hour/day/rollback、integrity/FK 均通过，但 runner 未安排无过期推进场景却要求 skip counter>0，产生 harness-only `semantic_gate_failed`，未进入 space/plain/stage。保留 validation-02 与 `summary-v19-02.json`。修正为显式 `no_expiration_advance` checkpoint 后，完整重跑追加 `validation-03\semantic|space|plain|stage` 和 `summary-v19-03.json`；不得复用前两批数据。

validation-03 完成后，最终 completed-root 与工程门禁复核追加 `pytest-green-01\run-04`；不得复用此前 basetemp。

## V18 revised set-based 性能门禁失败（2026-08-31，当前权威状态）

状态：`step_5_v18_revised_performance_gate_failed / awaiting_revised_projection_performance_decision`。统一协议固定批次已完成且不追加重跑。空间 196608 bytes、稳定性、吞吐比 0.944995、recorded p99 3.7507ms、语义和隐私通过；但 recorded p95=3.1542ms>2ms，reservation p95=1.0807ms（相对 V17 反而慢 10.8865%），settlement p95=0.4132ms（仅改善 9.5050%，要求至少 20%）。候选不具备产品 0005 实施资格。

阶段证据显示每 1000 execution 执行 1998 个 expiration logical batch/3996 SQL statement，以及 2000 个 lifecycle delta batch/4000 SQL statement。zero-seed + UPDATE 修复了负 delta 语义，却把每个 logical delta 固定为两条 SQL；对无实际过期行的 day-window 推进仍执行两条 no-op SQL，未降低端到端热点。

## V18 revised set-based 性能预验证（2026-08-31，当前权威状态）

状态：`step_5_v18_revised_performance_authorized / prevalidation_pending`。仅执行全新空间门禁、统一 `f-009-memory-control-protocol-v1` plain 1+5 和独立 non-gating stage companion；引用已通过 semantic 摘要 SHA256=`65BBB6EA...A0B4`，不连接或复用其 SQLite。即使全部通过也不实施产品 0005。

新根：`E:\Agent\cyber-town-f009-step5-tests\performance-v18-projection-set-based-revised-performance`。surface：根、`tmp`、`pytest-red-01`、`pytest-green-01`、`validation-01\space`、`validation-01\plain`、`validation-01\stage`，完成时 `summary-performance-01.json`；唯一磁盘数据库为 `validation-01\space\control.sqlite3` 及必要 WAL/SHM。保留至 Step 5 收口，由用户手动删除，Codex 不删除。

## V18 revised synthetic semantic 通过（2026-08-31，当前权威状态）

状态：`step_5_v18_revised_semantic_passed / awaiting_set_based_performance_prevalidation_authorization`。zero-seed + set-based UPDATE 修订已在全新隔离 control SQLite 中通过：16 并发 reservation/settlement、严格 1h/24h cutoff、时钟回退重建、ledger/projection 一致、integrity/FK 和隐私门禁全部通过。未运行 plain 1+5 或 stage companion，未实施产品 0005。

下一步只能另行授权恢复 V18 统一协议性能预验证；仍须满足原 reservation/settlement 降幅、recorded p95/p99、吞吐、稳定性和空间全部门禁后，才具备产品 0005 实施资格。

## V18 revised set-based semantic 修订（2026-08-31，当前权威状态）

状态：`step_5_v18_revised_semantic_authorized / zero_seed_update_pending`。仅修订 synthetic 候选：先以固定批次建立零值 totals 行，再用 set-based `UPDATE` 应用正/负 delta；随后只执行全新 synthetic 语义门禁。旧 V18 两个数据库保持只读且不连接；不运行 plain/stage 性能、不实施产品 0005。

新根：`E:\Agent\cyber-town-f009-step5-tests\performance-v18-projection-set-based-revised-semantic`。surface 为根、`tmp`、`pytest-red-01`、`pytest-green-01`、`semantic-01` 和完成时 `summary-semantic-01.json`；唯一 SQLite 为 `semantic-01\control.sqlite3` 及必要 WAL/SHM。保留至 Step 5 收口，由用户手动删除，Codex 不删除。

## V18 synthetic 语义门禁失败（2026-08-31，当前权威状态）

状态：`step_5_v18_synthetic_semantic_gate_failed / awaiting_revised_set_based_candidate_authorization`。红测在缺少 V18 symbols 时按预期 collection failed；实现后 25 项定向测试、ruff、format、mypy 通过。唯一正式 preflight 在 space workload 的窗口过期路径停止：固定 `INSERT ... ON CONFLICT` 将负 delta 作为候选插入值，SQLite 在 conflict update 前先执行 `attempts_1h >= 0` CHECK，触发 `IntegrityError` 并安全回滚。

这证明当前 V18 单语句负 delta 形状不满足既有 CHECK 语义；不是 ledger、窗口或产品 migration 已变更。按硬停止规则，没有运行 plain 1+5、stage companion，没有生成 summary，没有实施产品 0005/repository/产品回归。性能 P1、Step 5、R-10 保持开放。

## V18 set-based rolling projection 修复（2026-08-31，当前权威状态）

状态：`step_5_v18_set_based_projection_authorized / synthetic_preflight_pending`。仅先执行 synthetic set-based delta 语义、隐私、空间、统一 plain 1+5 与独立 non-gating stage companion；只有全部门禁通过才允许实施 append-only 产品 `0005` 与 repository 回归。性能 P1、Step 5、R-10 继续开放。

授权根：`E:\Agent\cyber-town-f009-step5-tests\performance-v18-projection-set-based`。准确 surface 为根、`tmp`、`pytest-red-01`、`pytest-green-01`、`preflight-01`、`preflight-01\semantic`、`preflight-01\space`、`preflight-01\plain`、`preflight-01\stage` 和完成时的 `summary-preflight-01.json`；pytest 管理的内部临时项只能位于已登记 basetemp。`space\control.sqlite3` 及其必要 WAL/SHM 是显式空间门禁所需的唯一 synthetic 磁盘 control 数据库，不是正式/产品数据库。

内容仅限 synthetic pytest/TEMP、FakeProvider/内存 control 候选、上述隔离 control SQLite 和 metadata-only 摘要；不含 `.env`、真实秘密/对话、F-005 资源、business/observability/正式数据库。保留至 Step 5 收口，由用户只读复核后手动删除；Codex 不删除。

## V17 rolling projection non-gating 阶段归因（2026-08-30，当前权威状态）

状态：`step_5_v17_projection_stage_attribution_complete / awaiting_v18_candidate_authorization`。synthetic rolling projection候选已按`f-009-memory-control-protocol-v1`完成唯一non-gating companion：1个warm-up pair、5个固定`no_recorder_control -> in_memory_control` measured pair、每场1000 execution，共12000 execution；没有重跑V16 plain门禁。

归属完整率100%，12阶段每run均为1000次，flat sibling区间无重叠，线程始终1→1。instrumented baseline/recorded五轮聚合p95=`2.9959/3.007ms`，仅差`0.0111ms`；不能把V16失败归咎于recorder。recorder直接阶段`observability_stage_records` p95=`0.1683→0.1913ms`，增量`0.023ms`；terminal增量`0.0004ms`。recorded GC每轮为32—37/3—4/0—1次，明显多于baseline的9—10/0—1/0，但跨阶段差值和运行顺序波动说明这只能作为内存压力相关证据，不能单独判定GC为根因。

共同热点按五轮run-level p95中位为：budget reservation=`0.9355/0.9746ms`、budget settlement=`0.4145/0.4566ms`、execution admission=`0.4378/0.4488ms`、ingress admission=`0.446/0.4457ms`、permit acquire=`0.4269/0.3861ms`（baseline/recorded）。未归属时间中位仅`0.047325/0.049285ms per execution`，说明allowlist已覆盖主要成本。各stage p95不能相加为请求p95，只用于热点排序。

推荐候选A：先在synthetic candidate内把projection totals的四scope逐行`SELECT + UPSERT`、过期delta逐scope调整与四次窗口读取改成固定形状的set-based delta apply/read；保持同一事务、ledger真相、CHECK/fail-closed、cutoff、replay/rollback和空间边界。先验证SQL调用数、预算reservation/settlement局部收益与统一plain绝对门禁；通过后才能条件式实施产品`0005`和repository。候选B仅为execution级不可变scope-tag context复用，当前没有独立HMAC/DTO耗时证据且会触及replay/waiter/取消归属，暂不推荐实施。

预登记唯一新根：`E:\Agent\cyber-town-f009-step5-tests\performance-v17-projection-stage-attribution`。允许surface仅为`tmp`、`pytest-red-01`、`pytest-green-01`、`attribution-01`及`summary-attribution-01.json`；内容仅synthetic pytest/TEMP、内存候选运行目录和metadata-only stage/runtime摘要，不含持久产品数据库、business/observability SQLite、`.env`、真实秘密/对话或F-005资源。复用既有V13 Python 3.12工具环境；保留至Step5收口，由用户手动删除，Codex不执行删除。

## V16 rolling projection 统一协议重验（2026-08-30，当前权威状态）

状态：`step_5_v16_projection_unified_performance_gate_failed / awaiting_next_performance_authorization`。rolling projection synthetic 候选已按 `f-009-memory-control-protocol-v1` 完成唯一一次重验：1个warm-up pair、5个固定`no_recorder_control -> in_memory_control` measured pair、每场1000 execution、五轮run-level分位数中位，并记录12个plain run的GC、CPU、wall、thread和order metadata。

语义和空间通过：16并发reservation/16 settlement，projection与ledger一致，integrity=`ok`、FK failures=`0`；100个完整control execution的主文件增长=`196608 <= 262144 bytes`。等工作量reserve稳定性通过，五轮聚合 early/middle/late median=`0.43045/0.35795/0.43095ms`，`stable_tail=true`。

统一绝对性能门禁失败：no-recorder p95/p99=`2.7582/3.6022ms`，in-memory recorder p95/p99=`3.2393/4.215ms`；recorded p95超过`2ms`，配对吞吐比=`0.805846`通过。该结果说明rolling projection消除了原24小时ledger扫描造成的持续增长，但在统一协议下仍未满足完整控制链路绝对p95，因此候选不能进入产品`0005`。本轮按停止条件未运行non-gating stage companion、产品矩阵、Step5综合验收或Step6，也未实施产品代码。

预登记唯一新根：`E:\Agent\cyber-town-f009-step5-tests\performance-v16-budget-projection-unified`。允许 surface 仅为 `tmp`、`pytest-red-01`、`pytest-green-01`、`validation-01\semantic`、`validation-01\space`、`validation-01\performance` 和 `summary-unified-01.json`；内容仅 synthetic pytest/TEMP、隔离 control SQLite/WAL/SHM 与 metadata-only 摘要，不含业务/observability SQLite、`.env`、真实秘密、真实对话、正式数据库或 F-005 资源。复用既有 V13 Python 3.12 工具环境，不新建 venv、不联网；资源保留至 Step 5 收口，由用户手动删除，Codex 不执行删除。

## V15 测量协议统一与核心归因（2026-08-30，当前权威状态）

状态：`step_5_v15_protocol_attribution_complete / awaiting_next_performance_authorization`。synthetic 与正式核心矩阵现共同使用 `f-009-memory-control-protocol-v1`：1个warm-up pair、5个固定`no_recorder_control -> in_memory_control` measured pair、每场1000 execution、五轮run-level分位数中位。plain逐轮记录GC/CPU/wall/thread/order；stage attribution使用同协议的独立non-gating companion，不进入正式2ms样本。

有界验证在当前已回退的control v4上完成：plain no-recorder/in-memory p95=`3.777/3.9668ms`、p99=`5.0916/5.0825ms`、配对吞吐=`92.0058%`。non-gating companion 的stage p95五轮中位以`budget_reservation=2.3661ms`最高，其次为ingress admission=`0.4474ms`、execution admission=`0.4346ms`、permit acquire=`0.4205ms`。这证明归因链路可定位当前O(n)预算热点，但不是产品0005或性能P1通过证据。

本轮没有恢复产品0005、运行完整核心矩阵、改变阈值或进入Step5综合验收/Step6。下一步如继续，只能先用统一协议重新执行rolling projection synthetic候选；通过后再单独决定是否重新实施产品0005。

## V14 产品 0005 核心门禁失败收口（2026-08-30，当前权威状态）

状态：`step_5_v14_product_core_gate_failed / awaiting_next_performance_authorization`。产品 `0005_budget_window_projection.sql`、repository rolling projection、产品测试和 benchmark 接入曾在 synthetic 前置门禁通过后按授权实施；迁移/预算语义产品测试 `18 passed`、相关兼容回归 `168 passed`。唯一完整 warm-up+5-run 核心矩阵随后命中三个冻结门禁失败码，按预设停止条件立即停止；本轮产品 migration、repository、产品测试和 benchmark 接入已精确回退，产品 `0005` 当前不存在，原 10 份 migration 未改变。

核心矩阵：

- no-recorder control p95/p99=`2.2485/2.8005ms`；in-memory recorder p95/p99=`2.2077/2.8267ms`，两者 p95 均超过 `2ms`，失败码 `in_memory_p95_exceeded`。
- 正式默认 HTTP control-off p95/p99=`96.05/168.3019ms`；control-on=`199.0348/412.2446ms`。control-on p95 增量=`102.9848ms`，允许值=`30ms`，并且 p99 超过 `400ms`；失败码分别为 `control_on_relative_p95_regression`、`full_loopback_p99_exceeded`。
- SQLite observability p95/p99=`104.0234/120.3313ms`、吞吐=`11.330651/s`，独立门禁通过；拒绝路径 p95=`2.8679ms`、dispatch=`0`。三库组合仍只作为非阻塞诊断。
- 证据：`E:\Agent\cyber-town-f009-step5-tests\performance-v14-budget-projection-product\performance-01\full-matrix-01\performance-summary.json`，SHA256 `262C37648E314FEFB6595BA2C7C7F8600E770C1E137CD16D4EE2AFDFBA78652C`。

结论：rolling projection 的 synthetic 语义/空间/稳定性前置证据仍有效，但产品核心矩阵没有证明冻结性能目标成立，因此预算历史增长问题不能标记为产品已解决。性能 P1、Step 5 与 R-10 继续开放，Step 5 综合验收和 Step 6 未进入。下一步必须先形成新的有界性能方案；不得重新实施同一产品候选或挑选性重跑矩阵。

## V14 corrected projection p95 有界补证收口（2026-08-30，当前权威状态）

状态：`step_5_v14_p95_attribution_passed / awaiting_product_0005_implementation_authorization`。用户授权的唯一5组AB/BA补证已完成；corrected rolling projection 的语义、空间、等工作量稳定性、完整 in-memory p95/p99和配对吞吐前置门禁现均有通过证据。产品 control `0005`、产品 repository 和产品测试仍未创建；性能P1、Step5与R-10继续开放，Step6未进入。

补证结论：

- 固定顺序为 `AB/BA/AB/BA/AB`，A=no-recorder control、B=in-memory recorder control；每个场景5个全新内存库运行、每轮1000 execution，没有warm-up、追加批次或慢样本删除。
- recorded五轮聚合 p50/p95/p99=`0.8147/1.9879/2.62ms`，满足`p95<=2ms/p99<=5ms`；throughput=`945.477079/s`，baseline=`910.827609/s`，配对比=`1.038042>=0.8`。负delta只按运行噪声解释，不宣称recorder加速。
- recorded逐轮p95=`1.9302/1.9879/2.0437/1.9813/2.1382ms`，2/5超限；baseline逐轮p95=`2.0757/2.1333/2.0406/2.1798/2.071ms`，5/5超限。同一pair共同超限2/5，低于预先锁定的4/5共同基础阻塞判据，`common_foundation_blocker=false`。
- corrected stability继续通过：等工作量五轮聚合 reserve median=`0.19385/0.2334/0.218ms`，`stable_tail=true`；5轮中4轮单独通过，所有逐轮结果保留。
- 摘要：`E:\Agent\cyber-town-f009-step5-tests\performance-v14-budget-projection-p95-attribution\summary-attribution-01.json`，SHA256 `B8C04FE0525AEDA9CC1A893C608148E16699AA289472A9CE8F8134926ACEE566`，status=`passed`。

建议：现在可以另行授权按既定候选A精确产品范围实施 append-only control `0005_budget_window_projection.sql` 和 repository投影，随后先验证迁移/预算等价/restart/rollback，再运行完整核心矩阵。该授权仍不能自动进入Step5综合验收或Step6，也不能把预算投影解释为已解决control-on多次durable commit问题。

## V14 synthetic 稳定性验证 v2 收口（2026-08-30，历史状态）

状态：`step_5_v14_validation_corrected_absolute_performance_gate_failed / awaiting_next_performance_authorization`。用户授权修正 V14 synthetic 验证后，已确认旧 D1 的首100/末100比较混入了不同的窗口过期工作量；该“稳定性失败”结论被本轮等工作量验证取代。产品 control `0005`、产品 repository 和产品测试仍未创建，性能 P1、Step 5 与 R-10 继续开放，Step 6 未进入。

修正与结果：

- 稳定性只比较 execution `101—200`、`501—600`、`901—1000`；三段每个 reserve 均为2个新 scope 行、1条1h过期记录、0条24h过期记录、8组 totals 调整。全部5个正式 run 都参与聚合，不再只看最后一轮。
- 等工作量聚合 reserve median=`0.1988/0.20785/0.2244ms`，末段较早段约 `12.9%`，在原 `<=max(25%,0.05ms)` 规则内，`stable_tail=true`。因此没有证据证明 totals 主键表在本规模下产生不合格的持续增长。
- 语义、空间与吞吐继续通过：projection/ledger match=true、integrity=ok、FK=0；control growth=`196608 <=262144 bytes`；paired throughput ratio=`0.978712`。
- 本轮唯一 corrected validation 的完整 in-memory recorded p95/p99=`2.3483/3.7771ms`，其中 p95 超过冻结的 `2ms`；配对 no-recorder control p95也为`2.1569ms`。因此最终状态仍为 `performance_gate_failed`，不得挑选性重跑或据此实施产品0005。
- 摘要：`E:\Agent\cyber-town-f009-step5-tests\performance-v14-budget-projection-validation-v2\summary-validation-01.json`，SHA256 `621F52959D68A0D4105C3C549F339F83974FCBD200AE5F1F5D8961ACC35E6265`。

停止边界：本轮只修正 synthetic 验证。不得自动进入产品 migration/repository、核心矩阵、Step 5 综合验收或 Step 6。下一步需另行决定是对 no-recorder/recorded 同轮绝对 p95 波动做有界补证，还是重新审查产品落地门禁；不得把已通过的稳定性结论解释为完整性能 P1 已解决。

## V14 rolling projection D1 预验证失败收口（2026-08-30，历史状态，已由 v2 修正）

状态：`step_5_v14_projection_preflight_failed / awaiting_revised_projection_design_authorization`。D1 已按失败优先完成候选 schema、严格 cutoff、lifecycle、rebuild、并发、空间和完整 in-memory warm-up+5-run；产品 control `0005`、产品 repository 修改和 product 测试根均未创建。性能 P1、Step 5 与 R-10 继续开放，Step 6 未进入。

门禁结果：

- 语义通过：16 并发 reservation、16 settlement，ledger/projection 一致，integrity=`ok`、FK failures=`0`；候选单测先红后 `12 passed`。
- 空间通过：100 unique execution/完整 control 写入，主文件由 `147456` 增至 `344064` bytes，增长 `196608 <= 262144`；`idx_budget_attempt_quota_time` 承担时间范围查询，owner 通过 PK covering index 关联。
- 完整 in-memory 绝对门禁通过：recorded p95/p99=`1.428/2.13ms`，配对吞吐比=`0.976981`；no-recorder control p95/p99=`1.5289/2.2226ms`。
- 稳定性门禁失败：同一正式轮 reserve median 首100=`0.1731ms`、中100=`0.21145ms`、末100=`0.23855ms`，末段较首段增长约 `37.8%`；候选仍随唯一 scope 投影表扩大产生可测增长，不能按锁定规则解释为“历史无增长”。
- D1 最终状态为 `performance_gate_failed`，摘要 `E:\Agent\cyber-town-f009-step5-tests\performance-v14-budget-projection\summary-03.json`，SHA256 `24D1BA627B73A19651E97BFBA69D7148460E4D1726A9D6D82BCFDF8932ADBA27`。

停止边界：不实施或保留产品 0005，不修改产品 repository，不创建 `performance-v14-budget-projection-product`，不追加批次寻找通过结果。下一步只能先只读分析为什么 totals 主键表随唯一 scope 数增加仍产生末段增长，并提出不改变预算语义/阈值的新候选；未经授权不得继续。

## V14 rolling projection 实施授权与资源登记（2026-08-30，当前权威状态）

状态：`step_5_v14_projection_implementation_authorized / synthetic_preflight_pending`。用户已批准按“两道硬门禁”执行：先完成候选 A 的 synthetic 语义、空间和 in-memory 性能预验证；仅当全部通过时，才直接实施产品 control `0005` 与 repository 投影。任一门禁失败立即停止，不进入产品实现或后续阶段。

预登记资源：

- `E:\Agent\cyber-town-f009-step5-tests\performance-v14-budget-projection`：D1 synthetic pytest/TEMP、隔离 control SQLite/WAL/SHM、空间/性能 metadata-only 摘要；不存在、父目录 `E:\Agent\cyber-town-f009-step5-tests` 非 reparse point。
- `E:\Agent\cyber-town-f009-step5-tests\performance-v14-budget-projection-product`：仅在 D1 全绿后创建，容纳产品红绿测试、隔离 control SQLite/WAL/SHM、核心矩阵所需 synthetic 数据和 metadata-only 摘要；当前不存在、父目录非 reparse point。
- 工具固定复用 `E:\Agent\cyber-town-f009-step5-tests\performance-v13-storage-ab\tooling-venv\Scripts\python.exe`，SHA256 `FCC90DA3456501E815F4C0A4C50AACB5772F67563225B1FC3A1DB1FBA49FA5B9`；不新建 venv、不联网、不读取 `.env`。

两个新根均不含真实 scope/payload/秘密、正式数据库或 F-005 资源；保留至 Step 5 收口，由用户手动删除，Codex 不执行删除。固定子类别为 `tmp`、失败优先 pytest basetemp、语义、空间、性能、产品绿测和核心矩阵；不得写入登记根之外。

## V14 durable budget/control 聚合状态架构草案（2026-08-30，当前权威状态）

状态：`step_5_v14_architecture_draft_complete / awaiting_v14_projection_prevalidation_authorization`。本轮只读完成源码、migration、V9/V10/V12/V13 metadata-only 证据分析及候选设计；没有修改功能源码、测试、脚本或 migration，没有运行测试/profiling/矩阵/服务，没有创建资源。性能 P1、Step 5 与 R-10 继续开放，Step 6 未进入。

### 已确认成本与证据强度

1. **in-memory 的历史扫描热点为高强度证据。** V9 使用真实 v1—v4 control schema、1000 execution/settlement，预算查询 VM 下界由首 100 的 `2360` 增至中段 `26170`、末 100 的 `45240`；扫描均时由 `0.102ms` 增至 `0.752/1.239ms`，scope tag 与 DTO 没有同幅增长。当前 `_BUDGET_WINDOW_SQL` 每次从 `budget_reservations`、owner、settlement 读取 24h 活跃历史并计算四 scope 的 12 项统计，复杂度随窗口内 ledger 行数增长。
2. **继续改同一 SQL 形状已被否定。** V8 仅减少局部 VM 步数而端到端仍失败；V10 候选 VM 末段反增 35%，plain 尾部没有改善。不能再以 CTE、FILTER 或单查询重排冒充架构修复。
3. **HTTP 的主成本不是预算查询。** V9 control-on 每 100 execution 约 `900` 次 control commit，其中 `801` 次有写；预算扫描均值仅约 `0.177ms`。V13 NoOp observability 下，E/C 均通过绝对 HTTP 门禁，却分别以 `98.1198ms`、`86.3302ms` 的 p95 增量失败。E/C control-on write-commit p95 五轮中位约 `8.7113/5.7714ms`；更快介质降低绝对成本但没有消除固定事务序列。
4. **V12 是重要反证。** 既有调用层 intra-execution 事务批次扩大临界区、引入取消复杂度且没有稳定改善，已精确回退。不能重新包装同一批次候选；若未来研究 group commit，必须是跨 execution、每个 await 仅在真实 commit 后完成的独立架构，并另做补证。

### 候选 A：watermarked exact rolling projection（推荐先预验证）

保留 `budget_execution_owners`、`budget_reservations`、`budget_settlements` 为唯一权威 ledger；新增可从 ledger 原子重建的派生投影，不新增每-attempt 四倍 contribution 行。

候选 append-only `0005_budget_window_projection.sql`：

- 新表 `budget_window_projection_state`：单例、projection/policy version、`hour_cutoff_ns`、`day_cutoff_ns`、revision、`rebuilt_at_ns`；所有时间/版本/单例约束固定。
- 新表 `budget_window_totals`，建议 `STRICT, WITHOUT ROWID`：`scope_class`（player_npc/player/npc/global）、metadata-only `scope_tag`（global 使用固定非敏感值）、`attempts_1h`、`attempts_24h`、`cost_24h_micro_usd`、revision、`updated_at_ns`；三项总量均非负，主键 `(scope_class, scope_tag)`。
- 继续保留 `idx_budget_attempt_quota_time`、reservation/settlement PK/FK/UNIQUE/CHECK 和全部业务表字段。候选明确申请删除且仅删除三个已不再服务产品查询的非唯一 owner scope 索引：`idx_budget_owners_player`、`idx_budget_owners_npc`、`idx_budget_owners_player_npc`，用以抵消投影空间和 owner 写放大；不得删除其他索引或约束。此项必须先用真实 query-plan/空间证据确认。
- 既有 `0001—0004` 哈希不变；新代码只承诺 v1—v4 库向 v5 原子升级并读取。v5 不承诺旧程序反向打开；不改业务/observability migration。

运行时语义：

- 投影在 `BEGIN IMMEDIATE` 内推进。以旧/新 cutoff 的半开区间从现有 ledger 读取新到期 reservation，按 owner scope 分组扣减；`reserved_at_ns == cutoff` 必须过期，从而保持原 `reserved_at_ns > cutoff` 语义。随后读取四 scope totals，并继续按现有 `ATTEMPT_WINDOW_SPECS`、`COST_WINDOW_SPECS` 顺序产生 warning 或首个 hard reject。
- reserve 成功时，同一事务插入 owner/reservation并增量更新四 scope totals；reject/异常全部回滚。replay 已有 reservation 不重复加总。
- dispatch 不改变 totals。settlement 在同一事务把仍处于 24h 窗口的预留成本替换为实际成本；release 在同一事务从仍活跃的 1h/24h attempt 和 cost totals 中扣除。迟到/重复 settlement 继续由原 PK 与等价检查保证唯一。
- 时钟前进时只处理自上次 watermark 后新到期范围；时钟倒退、缺失投影、版本不匹配或 projection 校验失败时，不猜测修补，必须在启动/recovery 事务中由 ledger 全量重建或 fail-closed。重建前不得服务新 admission。
- `recover_open_budget_attempts` 在同一事务完成 reserved→released、dispatched→conservative settled 后重建投影；崩溃前未提交的 migration/rebuild 自动回滚，崩溃后重复 recovery 幂等。投影不是新的计费真相，ledger 始终可验证/重建。
- 不跨请求缓存安全判断，不减少路径/身份检查，不自动 DELETE/VACUUM，不保存原始 scope/payload/秘密。

预期收益与局限：预算窗口读取从 O(active ledger) 变为四个 totals 主键读取；稳定流量下到期推进为按“新到期行”增量工作，能直接针对 V9 的增长热点。它不减少 admission、breaker、permit、dispatch、settlement/release 的 durable commit 数，因此**不承诺**单独解决 HTTP 相对增量。投影表空间、首次/倒退时重建、长时间空闲后的到期突发以及删除三个 owner 索引的兼容性必须先做 synthetic 预验证。

### 候选 B：跨 execution bounded durable group commit（暂不推荐实施）

在候选 A 之上，以 control lane 单 writer 收集最多 2 个不同 execution 的兼容 control command，使用 savepoint 隔离语义拒绝，外层一次真实 commit；每个调用只有在该 commit 完成后才返回，不 fire-and-forget、不提前确认 durability。目标是减少并发 2 场景的实际 fsync 次数，而不是把同一 execution 的多个生命周期步骤包成长事务。

风险高：需要新的队列/关闭生命周期、storage error 全批 fail-closed、取消排队/运行中/提交后归属、不同 request 的错误隔离、breaker/permit/预算状态机组合，以及单请求无可批对象时不能回归。V12 已说明简单批事务会扩大临界区；当前没有修复后跨 execution 原型收益证据。因此 B 仅保留为 A 通过且 HTTP 相对增量仍失败后的独立 D2 研究项，不进入下一产品授权。

### 推荐验证顺序和停止条件

1. 下一步仅授权候选 A 的 script/test synthetic D1，不创建产品 `0005`。使用全新 `E:\Agent\cyber-town-f009-step5-tests\performance-v14-budget-projection`，先登记再创建；真实 v1—v4 schema、固定 clock/ID/顺序，旧证据 SQLite 不连接/复用。
2. 红测必须覆盖错误 totals、错误 cutoff、错误 cost delta、时钟倒退、迁移/rebuild 中断、scope/版本错配和索引缺失；工具若不能识别故意破坏的候选即停止。
3. 等价 oracle 覆盖四 scope、1h/24h cutoff 前/等于/后、reserved/dispatched/settled/released、零/非零成本、attempt 2、warning/reject 顺序、16 并发、replay、rollback、取消/迟到和 restart recovery。ledger 与投影逐项相等，泄漏/重复计费/重复写入均为 0。
4. 空间预验证必须使用 100 unique execution/三 NPC/完整 control 写入；候选 control growth 仍须 `<=256KiB`。删除三个索引前后分别报告 query plan、主文件/占用/freelist/WAL/SHM，不用预分配、VACUUM 或旧空闲页制造通过。
5. 性能预验证使用真实 migration、1000 execution、相同状态分布；plain 末段 budget/reserve 成本必须稳定下降，完整 in-memory control warm-up + 5-run 必须通过 p95/p99 `2/5ms` 与配对吞吐 `>=80%`。只降 VM、只降均值或落入波动范围即失败。
6. D1 任一语义、空间或 in-memory 门禁失败即停止，不创建产品 migration，不扩大表/索引。D1 全部通过后仍停止，等待候选 A 产品实施授权。
7. 产品实施后先重跑语义/迁移/restart，再跑完整核心矩阵。若 HTTP 相对增量仍失败，只记录证据并另行申请候选 B 补证；不得自动进入 B、Step 5 综合验收或 Step 6。

### 候选 A 精确产品范围（仅设计，不代表已授权）

- 新增：`backend/src/cyber_town/infrastructure/control/migrations/0005_budget_window_projection.sql`。
- 修改：`backend/src/cyber_town/infrastructure/control/sqlite_control.py`。
- 测试：新增 `backend/tests/test_budget_projection_step5.py`；修改 `backend/tests/test_budget_control_step3.py`、`backend/tests/test_sqlite_control.py`、`backend/tests/test_storage_migrations_v4.py`、`backend/tests/test_control_performance_contract_step5.py`、`backend/tests/test_attribution_step5.py`。
- 脚本：仅在 D1/产品授权后分别新增/修改 `scripts/f009_step5_budget_projection_preflight.py`、`scripts/f009_step5_attribution.py`、`scripts/f009_step5_benchmark.py`。
- 明确不改：application/control/dialogue、API/composition/app、AsyncSqliteExecutor、observability、Dialogue v1、Godot、业务 migration、依赖、CI 与全部冻结阈值。若实际需要这些文件，立即停止申请扩大授权。

## V13 存储介质 A/B 收口（2026-08-30，历史状态）

状态：`step_5_v13_storage_ab_complete / awaiting_next_performance_plan_authorization`。Python 3.12 工具环境已在离线、frozen 边界内建立，V13 runner 红绿与静态门禁通过，同工作量 E: USB SSD / C: NVMe SSD A/B 已完成。两盘均通过正式默认 HTTP 的绝对 p95/p99、吞吐、control 空间、dispatch、成本和数据归属门禁，但均失败于 `control_on_relative_p95_regression`；因此停止存储介质路线，不支持把运行时数据根迁到 C 盘。性能 P1、Step 5 与 R-10 继续开放，Step 5 综合验收和 Step 6 未获授权。

- 工具环境：现有 Python 3.12.10 与 uv 0.6.14；43 个锁定依赖全部从离线缓存安装，`uv sync --offline --frozen --no-install-project --all-groups` 审计通过。dry-run 唯一 `Would download 1` 是未缓存的本地 editable 项目，不是缺失的网络 wheel；全程未访问网络，也未在 worktree 创建 `.venv`。
- runner：新增 8 项 V13 契约测试后，完整性能契约 `23 passed`；两文件 ruff、format、mypy、tracked/untracked whitespace 通过。runner 固定真实 TCP、独立客户端进程、逐请求计时、off→on、1 warm-up + 5 runs、每轮 100 execution；E/C 配置 digest 均为 `a51a52ee2949ff0f48e4440f67cdb720ff235ecdcfc19f08ce659704e7a7c6b0`。
- E: 汇总 off p95/p99 `67.8951/103.3343ms`、`31.913079/s`；on p95/p99 `166.0149/348.0677ms`、`13.632462/s`、control growth `233472 bytes`。绝对门禁通过，但 p95 增量 `98.1198ms`，允许 `30ms`，失败。
- C: 汇总 off p95/p99 `53.8412/73.0652ms`、`40.498043/s`；on p95/p99 `140.1714/155.9144ms`、`16.158938/s`、control growth `237568 bytes`。绝对门禁通过，但 p95 增量 `86.3302ms`，允许 `30ms`，失败。
- 介质差异存在但不能解释阻塞：C 的 on p95 比 E 低 `25.8435ms`，两盘仍稳定命中相同相对门禁失败码。按预先规则结论为 `storage_media_route_not_supported`，不得实施数据根迁移或追加有利批次。
- 语义审计：E/C 各 12 个隔离场景、2,400 次 HTTP；business/control integrity=`ok`、FK error=0、NoOp observability SQLite surface=0、fake cost=0、audit failure=0。正式三数据库不存在，所有临时端口及 8000 均已释放，10 份 migration 哈希不变。
- 剩余阻塞：独立 in-memory p95/p99 仍开放；control-on 相对增量仍超限。下一轮应另行授权有界的 durable budget/control 聚合状态架构方案或等价根因方案，先只读起草并明确语义/迁移/重启边界，不再继续存储介质 A/B 或无新证据微优化。
- 资源：E 侧 V13 根当前 5,037 files / 525 dirs / 149,773,738 bytes；C 侧根 73 files / 14 dirs / 5,711,848 bytes；reparse、`.env`、nested Git 均为 0。全部保留至 Step 5 收口，由用户手动删除，Codex 不删除。最终 whitespace 命令额外生成 `static-tmp/no-index-script.txt`（70,095 bytes）和 `static-tmp/no-index-test.txt`（19,735 bytes）；内容为代码 diff、敏感命中 0，属于已登记 static 根内的非必要临时文本，建议随 V13 根一并手动回收。

## V13 存储 A/B 环境预检阻塞（2026-08-30，历史状态）

状态：`step_5_v13_preflight_blocked / awaiting_offline_tooling_resolution_authorization`。V13 仅完成只读 Git、介质、路径和 Python 环境预检；未创建 tooling venv、E/C A/B 根、SQLite、日志、缓存或报告，未修改 runner，也未运行红测、A/B 或 Step 5 综合验收。性能 P1、Step 5 与 R-10 继续开放。

- Git/边界通过：正式 main 仍仅五份文档；功能分支仍 `33 tracked modified + 50 actual untracked`、staged 0，两处 HEAD/origin/main 均 `1a4fc2c…`。V12 专项测试不存在，8 组 V12 标识命中 0，10 migration 哈希与登记一致，V12 摘要 SHA-256 仍为 `91896223…3051A`。
- 介质证据充分：C 为 Disk 0 `YMTC PC300-512GB-B`、BusType `NVMe`、MediaType `SSD`；E 为 Disk 1 `YMTC PC3 00-512GB-B`、BusType `USB`、MediaType `SSD`。两卷 NTFS/Healthy/Online，空间分别约 45.1GB/134.3GB。候选父链 canonical 一致且无 symlink/junction/reparse。
- 环境阻塞：没有现成且同时包含 pytest、ruff、mypy、FastAPI、HTTPX、Pydantic、Uvicorn 和项目依赖的 Python 3.12 环境。授权候选 `tooling-venv` 的 `uv sync --dry-run --offline` 解析 45 包、计划安装 44 包，但明确显示仍需下载 1 包。按照“离线缓存不能满足即停止”规则，没有执行实际 sync、网络访问或降级到 Python 3.11。
- 下一步需要单独解决离线 tooling 来源：由用户提供/批准一个已经存在的完整 Python 3.12 环境，或另行授权补齐缺失离线包。环境就绪后必须重新从 V13 预检开始，不得把本次只读 dry-run 当作 A/B 已启动。

## V12 失败候选精确回退与存储 A/B 待确认（2026-08-29，当前权威状态）

状态：`step_5_v12_candidate_reverted / awaiting_storage_ab_validation_authorization`。V12 事务批次候选已从四个既有文件撤销，唯一新增专项测试已按用户明确授权移除；性能 P1、Step 5 与 R-10 继续开放，不得进入 Step 5 综合验收、Step 6 或 Git 交付。

- 功能文件集合恢复为 V12 创建前登记的 `33 tracked modified + 50 actual untracked`，暂存 0；正式目录仍仅五份项目文档。`ProviderAttemptAdmission`、`admit_provider_attempt`、`record_provider_success_and_release`、批连接包装、批事务上下文和 `V12_ROOT` 命中均为 0。
- 回退后 breaker check、budget reserve、permit acquire、breaker success 与 permit release 恢复为 V12 前的独立可等待调用；此前 V7/V8 的取消、幂等、owner、重启和预算实现未撤销。未 reset、stash、切换分支或覆盖其他改动，也未删除任何临时资源。
- 最小门禁：四文件 ruff/format 通过，Python 3.12 AST 与回退结构契约 4/4 通过，功能/正式 `git diff --check` 通过。当前可调用 pytest 环境只有 Python 3.11，无法解析项目 Python 3.12 类型参数语法；本轮按“不得新建虚拟环境/资源”边界没有创建环境或测试根，因此没有把结构检查表述为运行时全回归。
- V12 性能证据根 `E:\Agent\cyber-town-f009-step5-tests\performance-v12-control-transaction` 保留且未修改/删除；其中失败矩阵仍是回退决策证据，不得因代码回退而改写历史结果。

### E USB / C NVMe 同工作量 synthetic A/B 候选方案（仅起草，未授权执行）

目标只验证正式默认 `control-on + NoOp observability` 的 HTTP 尾延迟是否主要受运行数据盘影响；该试验不能解决或豁免独立的 in-memory p95/p99 阻塞。

1. 后续单独授权时，候选根分别为 `E:\Agent\cyber-town-f009-step5-tests\performance-v13-storage-ab\e-usb` 与 `C:\Users\24696\AppData\Local\Temp\cyber-town-f009-v13-storage-ab\c-nvme`。创建前须只读确认卷/物理介质映射、canonical path、父链 reparse 边界、可用空间和路径不存在；无法证明介质类型时只能标记为 E/C 卷对照，不得冒称 USB/NVMe。
2. 两组固定同一提交、解释器、synthetic key、FakeProvider、输入/ID/时钟/顺序、业务与 control migration、WAL/FULL、路径身份检查和写入次数；只改变批准的数据根。使用真实本地 TCP、独立客户端进程和逐请求计时，均执行 1 次 warm-up + 5 次 100-execution 正式默认 HTTP；不得删慢样本、降低同步或复用旧库空闲页。
3. 报告每轮 p50/p95/p99、吞吐、control-off/on 相对增量、writer/commit/路径检查摘要、数据库增长和完整性；冻结门禁仍为 HTTP `250/400ms`、`>=4/s`、control-on p95 增量 `<=max(off×20%,30ms)`，空间与零 dispatch/零成本边界不变。
4. 只有 C 五轮稳定通过且 E 在同工作量下稳定失败，才可提出“通过既有依赖注入配置运行时数据根”的最小产品候选；仍须另获产品/API/配置/测试文件授权，且不得读取 `.env`。若两盘均失败或差异落入波动范围，停止并转入 durable budget/control 聚合状态架构方案，不继续微优化。
5. 两个候选根只允许 synthetic 三 SQLite/WAL/SHM、FakeProvider、pytest/TEMP 与 metadata-only 摘要；不含真实 payload、秘密、正式数据库或 F-005 资源。保留至 Step 5 收口，登记于 evidence，由用户手动删除，Codex 不执行删除。

## V12 in-memory / control-on 性能续修收口（2026-08-29，当前权威状态）

状态：`step_5_v12_core_gate_failed / awaiting_next_architecture_authorization`。原子批次候选已被完整五轮实测否定；性能 P1、Step 5 与 R-10 继续开放，不得进入 Step 5 综合验收、Step 6 或 Git 交付。

- 只读复核确认 V11 五轮摘要 SHA-256 仍为 `c8a69168f1e1adc81ddd8c2ecabad5bc9924ebf1f3697100d9229fb95f16f323`，正式 main 仅五份项目文档，功能分支仍为登记的 `33 tracked modified + 50 actual untracked`，10 份 migration 未改，正式数据库不存在且 8000 端口空闲。
- 无落盘 cProfile 证实 in-memory 配对场景的主要增长成本仍是预算 24h 历史聚合；NoOp 与 InMemory recorder 结果接近，recorder 不是根因。既有 V10 CTE 候选和本轮一次性 UNION/事务原型均未稳定达到 2ms，均不落地、不冒充修复。
- control-on 相对增量继续与每成功请求约 9 次 control 事务/约 8 次写提交相符。最小候选只把 provider 前 `breaker check + budget reserve + permit acquire` 与 provider 后 `budget settle + breaker success + permit release` 分别放入两个原子事务；dispatch 标记保持独立，取消、retry、replay、waiter、restart、预算与业务归属不变。
- 功能修改上限为 5 个文件：`backend/src/cyber_town/application/control.py`、`backend/src/cyber_town/application/dialogue.py`、`backend/src/cyber_town/infrastructure/control/sqlite_control.py`、`backend/tests/test_control_transaction_batch_step5.py`、`scripts/f009_step5_benchmark.py`。范围不足即停止，不扩大 migration、SQL schema、Dialogue v1、Godot、依赖或 CI。
- 新资源根登记为 `E:\Agent\cyber-town-f009-step5-tests\performance-v12-control-transaction`；计划仅含 `tmp`、`pytest-red-01`、`pytest-green-01`、`matrix-01` 及其 synthetic pytest/TEMP、FakeProvider、隔离 business/control/observability SQLite、WAL/SHM 和 metadata-only 摘要。目标当前不得预先存在，父链须无 reparse point；具体矩阵子路径由固定 manifest 在创建前完整打印并复核。资源保留至 Step 5 收口，由用户手动删除，Codex 不执行删除。

失败优先与语义结果：契约红测 3 failed；实现后专项 3 passed。首轮扩大回归发现取消等待 permit 时 reservation 未释放，已将 pre-dispatch 批次收窄为 `breaker + reserve`，permit 恢复原等待位置；随后取消及批次专项 4 passed。批内 success 只合并 `breaker result + permit release`，实际 SQL trace 各批次均 1 次 COMMIT；故障注入同时回滚两项。控制/预算/契约主集为 142 passed、1 failed、53 deselected；唯一失败是内存连接覆写误落盘，修正后相关聚焦组 5 passed。按性能失败停止条件没有重跑整组，不能把 142 项表述为修复后的完整回归。旧 V7/V10 需专用环境变量的用例未作为产品失败计入。

完整 warm-up + 5-run 结果：in-memory p95/p99 `4.3027/5.0302ms`，仍超过 `2/5ms`；control-off p95 `111.2434ms`，control-on p95/p99 `293.2776/374.8972ms`，control-on 绝对 p95 和相对增量 `182.0342ms > 30ms` 均失败。SQLite observability `104.3828/126.7426ms`、`11.598357/s`、增长 `307200 bytes` 继续通过；拒绝、dispatch、零成本、空间和吞吐通过；三 SQLite `593.0271/704.9206ms` 仍仅诊断。固定阻塞码为 `control_on_relative_p95_regression`、`full_loopback_p95_exceeded`、`in_memory_p95_exceeded`、`in_memory_p99_exceeded`。摘要 SHA-256 `91896223b621e91a18243e2ed80f82f5291364663a90496141aaf83c1563051a`。

结论：事务批次没有稳定降低内存尾部，并使本轮 control-on 绝对 p95 相比 V11 基线回归；不得落地或继续叠加微优化。V12 候选代码及新增专项测试当前仍未提交地保留在功能 worktree，等待单独授权决定精确回退/移除或进入更大的控制存储架构决策；Codex 不擅自删除新增测试文件。

## Step 0 门禁边界修订与完整矩阵收口（2026-08-29，当前权威状态）

状态：`step_5_gate_boundary_matrix_failed / awaiting_next_performance_authorization`。门禁边界修订已落地，但核心 warm-up + 5-run 仍有 3 个阻塞失败；性能 P1、Step 5 与 R-10 继续开放，不得进入 Step 5 综合验收或 Step 6。

- 正式默认 HTTP 阻塞场景现为 `control-on + NoOp observability`；其 p95/p99 为 225.9758/324.5334ms，吞吐 13.805406/s，绝对 250/400ms 与 4/s 门禁通过，control 增长 237,568 bytes 低于 256KiB。
- control-off p95 为 69.1876ms；control-on 增量 156.7882ms，高于冻结允许值 30ms，`control_on_relative_p95_regression` 仍阻塞。
- in-memory control p95/p99 为 3.8461/5.0193ms，高于 2/5ms；配对吞吐 482.767377/s 对 454.118851/s，吞吐比例约 106.31%，吞吐门禁通过。
- SQLite observability 独立门禁全部通过：p95/p99 94.7476/118.9803ms、12.456485 trace/s、增长 311,296 bytes。
- 三 SQLite 组合仅作为非阻塞诊断：p95/p99 585.708/722.9288ms、6.221093/s、增长 671,744 bytes；只产生 `three_sqlite_p95_exceeded` 与 `three_sqlite_p99_exceeded`，不进入阻塞失败码。
- rate/budget/breaker pre-dispatch、no-recorder、绝对 HTTP、SQLite recorder、吞吐、空间、dispatch 与零成本检查通过。66 个新 SQLite integrity/FK 检查无问题，observability 每完整场景 1,400 stages；正式数据库不存在，8000 端口释放。

下一步必须单独授权调查两个剩余边界：内存链路尾延迟，以及 control-on 相对增量。不得因正式默认绝对 HTTP 已通过而把性能 P1 或 Step 5 标记完成，也不得放宽冻结阈值。

## V11 正式运行模式边界验证收口（2026-08-29，当前权威状态）

状态：`runtime_default_slo_passed / awaiting_step0_gate_boundary_decision`。性能 P1、Step 5 与 R-10 仍开放；V11 只完成边界验证，没有运行最终 warm-up + 5-run、Step 5 综合验收或 Step 6。

V11 以真实本地 TCP、独立客户端、两请求并发和 100 次 execution 实测正式默认 `control-on + NoOpObservabilityRecorder`：p50/p95/p99 为 120.4389/157.1363/173.28ms，吞吐 14.865986/s，100 次 provider dispatch，冻结的 250/400ms 与 4/s 门禁全部通过。business/control 均为 WAL/FULL、integrity ok、FK 错误 0；100 admission、permit、owner、reservation、settlement 唯一归属，成本 0；100 关系状态/事件/请求唯一，长期记忆写入 0 符合本固定普通对话场景；observability SQLite surface 为 0。

已证实阻塞来自**门禁场景边界错配**：当前 `full_loopback_control_on` 强制叠加 SQLite observability，但正式 composition 默认不注入 recorder。V9 的三 SQLite 慢尾仍是有效诊断事实，不应改写为通过；它也不应继续作为默认运行路径的 HTTP 阻塞门禁。

等待用户确认以下 Step 0 门禁边界，不在 V11 自动修改契约：

1. HTTP p95/p99/吞吐门禁应用于正式默认 `control-on + NoOp observability`。
2. opt-in SQLite observability 继续使用独立 p95/p99/吞吐与 512KiB 门禁。
3. business + control + SQLite observability 三库组合保留为非阻塞诊断/趋势基线，不用于宣告默认 HTTP SLO 失败。
4. 阈值数字、WAL/FULL、14-stage、业务/预算/幂等语义均不变。确认后另行授权最小契约/benchmark 调整及完整 warm-up + 5-run；本轮未执行。

## V10 预算候选 A 预验证收口（2026-08-29，当前权威状态）

状态：`step_5_v10_candidate_a_rejected / awaiting_media_ab_authorization`。候选仅存在诊断/测试代码，**不值得落地到产品**；性能 P1、Step 5、R-10 继续开放。本轮没有修改产品 SQL、HTTP、migration、benchmark/steady_profile、Dialogue v1 或 Godot，也没有进入最终矩阵、综合验收或 Step 6。

- 红测 7 failed；实现工具后 7 passed。真实 4 migration 控制库 53 项回归通过：192 行独立 oracle、4 个错误 SQL 全部被检出，当前/候选的四 scope × 三项统计完全一致；回放、无重复结算、released、零/非零成本、严格 cutoff、首拒顺序、16 并发 reservation、约束/FK、缺失 settlement、仓储故障与回滚保持。
- 53 个数据库 integrity/FK/WAL/FULL 与 4 migration 通过。候选计划为逐行 coroutine，没有显式临时结构。
- 固定且仅一次的 profile/plain：当前/候选 × no-recorder/in-memory，每场 1000 execution，共 8000；无 warm-up、追加批次或 HTTP。每场 1000 settlement、1000 FakeProvider dispatch、成本 0；profile 归属完整，plain 无探针。
- plain p95/p99：当前 off 1.6415/1.8955ms，候选 off 2.0138/2.6218ms；当前 on 1.7481/2.4013ms，候选 on 1.9503/2.5676ms。候选 p95 分别恶化 22.7%/11.6%；吞吐 off 950.433→875.824/s（-7.8%），on 921.840→912.156/s（-1.1%）。
- 末 100 次 VM 下界由当前 45,240 增至候选 61,090（+35.0%）；预算扫描均时 off 0.9783→0.9376ms、on 1.0351→1.0092ms，只有微小且不一致的 profile 变化，plain 尾部也未改善。协程减少重复表达式，却增加 Yield/Copy 等工作。按停止条件拒绝产品落地，不追加第二候选。
- 最终工具回归 99 passed/45 deselected；ruff、3 文件 format、mypy、tracked 与 50 untracked whitespace 通过。V9 的 83 文件表除本轮 3 项外仍一致；3 项当前 SHA256 见 evidence，10 migration 及全部历史证据指纹不变。
- 两处 HEAD/origin/main 仍 `1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3`；正式 main 五文档，功能分支 33 tracked modified + 50 actual untracked，暂存 0。正式三数据库不存在；8000 及内部 self-pipe 端口均释放。无 .env、真实模型、外部服务或 F-005 访问。

资源：`E:\Agent\cyber-town-f009-step5-tests\performance-v10-budget-equivalence` 为 167 文件/65 子目录/103,179,290 bytes（8 JSON、53 control SQLite、53 WAL 0-byte、53 SHM），reparse/.env/嵌套 Git 均 0。Step 5 父根已包含 V10，共 4665 文件/2576 子目录/787,990,388 bytes。当前保留至 Step 5 收口，Codex 不删除；届时用户复核后手动删除精确 V10 根，非 Git 证据不可由 Git 恢复。

### 阻塞重新定性

V10 已反证“继续优化预算 SQL”路线。V9 证据显示 HTTP 尾延迟来自 FULL 同步下的大量真实 write commit 与单 writer 队列：control-on 每 100 请求约 900 次 control commit（801 次写），observability 每请求 15/20 次写 commit；request/owner 锁等待和预算 SQL 都不是 HTTP 主热点。

继续做 SQL、锁范围或路径检查微调不会解决双并发 p95 与 control-on 增量。

### 新发现：存储介质是未控制变量（2026-08-29）

只读系统核对显示：E: 为健康 NTFS/4096、**USB 总线 SSD**（Disk 1，YMTC PC3 00-512GB-B）；C: 为健康 NTFS/4096、**NVMe SSD**（Disk 0，YMTC PC300-512GB-B）。项目、功能 worktree 和历次性能 SQLite 均在 E:。Storage Reliability Counter 未提供设备级延迟，但总线差异已确认；fsutil 详细卷查询因系统权限拒绝，不影响上述 Get-Volume/Get-Disk 证据。

SQLite WAL/FULL 的每次 commit 必须经过 durable flush。USB 桥接与 NVMe 的 flush 尾延迟可能数量级不同。V9 已证明真实 commit/单 writer 队列是 HTTP 热点，而 V10 的内存当前 SQL plain p95 已为 1.6415/1.7481ms；二者共同说明：**先把介质作为变量做同工作量 A/B，比直接改事务架构更有信息增益**。此前所有局部优化都在同一 E: USB 介质上，不能区分代码成本和介质 flush 成本。

下一步推荐顺序改为：

1. 先用完全相同代码、WAL/FULL、真实写入和计时口径，在新的 E: USB 与 C: NVMe synthetic 根运行有界 A/B；不改产品。
2. 若 C 通过而 E 失败：阻塞属于运行时数据位置/验收环境。保留源码在 E，候选修复是通过既有 DI 显式配置本地 NVMe 运行时数据根；不得读取 .env，安全路径边界仍 fail-closed。
3. 若 C 和 E 均失败且差异不足：再进入 control 事务编排＋observability 跨 execution group commit。
4. 若 C、E 都通过：失败主要是运行噪声/测试口径，先冻结可重复环境，不改产品架构。

未经授权不在 C 盘创建任何文件。C 盘候选仅用于 synthetic A/B，属于存储偏好的明确例外；路径、内容、期限和用户手动回收必须先登记。

## V9 修复后有限归因收口（2026-08-28，当前权威状态）

状态：`step_5_v9_attribution_complete / awaiting_scoped_remediation_authorization`。本轮仅诊断补证完成；**性能P1、Step5、R-10继续开放**，不得进入Step6或Step5综合验收。没有改产品、benchmark、steady_profile、SQL、migration、Godot/依赖/CI；没有提交、推送、PR、部署或删除。下方V9授权与V8为历史。

实际执行恰好1profile+1plain、每组6场，共800 HTTP＋4000内存execution，未追加warm-up/重复批次/最终矩阵。HTTP真实TCP＋独立客户端逐请求计时；plain卸载性能探针（仅保留相同的synthetic工作量和客户端TEMP绑定）。V8取消、幂等、真实长期写入专项结论保持，不把本次核心HTTP空长期表当完整业务写入性能验收。

| 场景 | profile p95/p99 ms | plain p95/p99 ms | plain 吞吐/s |
|---|---:|---:|---:|
| http-off-single | 160.159 / 275.287 | 134.443 / 295.698 | 8.670 |
| http-on-single | 362.657 / 486.388 | 204.953 / 446.975 | 5.203 |
| http-off-pair | 364.157 / 507.561 | 407.685 / 522.315 | 9.636 |
| http-on-pair | 482.163 / 641.293 | 587.509 / 739.684 | 6.703 |
| memory-off | 4.790 / 5.656 | 2.834 / 3.491 | 638.002 |
| memory-on | 4.256 / 4.824 | 3.074 / 3.734 | 638.373 |

plain复现内存p95超2ms、HTTP双并发off/on超250/400ms。pair p95增量179.824700ms > 允许81.536940ms；single增量70.510000ms > 30ms，on single p99也超400ms。内存配对吞吐100.0582%，只说明本批>=80%，不声称recorder加速。不是warm-up+5-run验收，不能据一次采样宣布稳定通过/改善。
### 已证实归因与不可外推事项

1. **新request/owner锁不是本工作量的排队热点。** profile pair on，每请求request wait均值0.009046ms、p95 0.0128ms；owner wait均值0.000898ms、p95 0.0015ms。guard引用计数、取消等待者和原对象保留均有工具测试。长hold覆盖仓储await，不等于其他请求在等锁；不能把hold与其包住的storage重复相加。
2. **HTTP尾部与实际写commit/单writer队列对齐。** pair on每请求observability仓储操作均值118.564ms，队列50.952ms；实际write commit均值67.525ms（这些是嵌套/相邻区间，不相加冒充总成本）。请求67客户端630.598ms，其中repository区间并集467.406ms、write-commit子区间362.723ms、queue125.277ms；相邻68 queue239.546ms。pair off慢请求85/86同样有241.746/216.723ms commit子区间及134.561/216.482ms queue。全样本保留，非只看峰值。
3. **control-on的额外工作真实存在。** profile steady off每请求15次observability写commit，on20次；on control每100请求900次commit，其中801次有写、99次只读/无更改commit；business每请求1次写commit、2次连接开启/关闭。完整14-stage保持，额外控制事件未删减。on新增成本并不由100次规模预算SQL解释：预算扫描均值仅0.177ms。
4. **内存预算历史扫描是已测量的增长热点。** 两组profile使用4份真实control migration/1000execution/1000 settlement，不是简化表。首100/中501—600/末100 VM下界均值2360/26170/45240（每查询误差<1000步，两组一致）。memory-on预算扫描均时0.102/0.752/1.239ms，整体reserve 0.374/1.922/1.594ms；中段有87.632ms慢样本，未删除。scope-tag均时0.136/0.143/0.146ms，DTO及其他控制无同幅历史增长。每次查询仍O(n)扫描；累计工作随历史扩张，不能叫O(1)。
5. **探针时间不是plain性能。** profile内存加入SQL/DTO/VM等测量，且固定运行顺序有时间漂移；profile memory-on快于off不能当优化收益。尾部物理sync/操作系统调度/GIL/存储设备的内部比例没有分离，不能把commit耗时全叫磁盘flush下界。
6. **checkpoint未证实。** 新库setup读取page_size4096、synchronous2/FULL、wal_autocheckpoint1000；没有setter、手动checkpoint或WAL正文读取。这些配置与慢commit不能单独证明checkpoint因果。本轮没有扩大系统追踪/外部服务。
7. **归属与去重边界。** 400个profile HTTP和2000个profile内存请求全部有归属，parent/storage operation关联检查100%，稳态无未归属span。每请求按区间并集及父子边界分析，不将各类别inclusive/p95相加。初始化与收尾通过首/末请求区间划分；原case_index=0包含部分请求外收尾检查，不能仅靠“0=setup”解读。JSON保留原始时间边界，未覆盖改写。profile观察到的setup/teardown span范围不等于完整生命周期墙钟下界。plain没有性能span，不虚报plain的操作级归属测量。
8. **证据不足以选定整体必过方案。** 已排除“继续缩全局锁”“只修budget就能解决HTTP”“业务连接复用必然解决全部P1”；没有证明冻结门禁不可达，也没有可承诺的整体修复收益。

### 精确产品候选与推荐范围（均未授权实施）

推荐只把预算作为**局部、可证伪候选A**，不打包承诺HTTP修复：
- 产品候选唯一文件：`E:\Agent\comprehensive-cases\15-cyber-town-f009\backend\src\cyber_town\infrastructure\control\sqlite_control.py`，限固定参数化_BUDGET_WINDOW_SQL/_all_window_totals的行内scope/status/cutoff/cost重复计算消除；继续单查询、同一BEGIN IMMEDIATE快照，不新增索引/计数表/触发器/跨请求缓存。现有FILTER对每类scope的三项统计重复求条件；是否能在真实布局减少VM而不增加物化成本，尚须等价/收益预验。
- 测试候选：`E:\Agent\comprehensive-cases\15-cyber-town-f009\backend\tests\test_budget_control_step3.py`、`E:\Agent\comprehensive-cases\15-cyber-town-f009\backend\tests\test_attribution_step5.py`。
- 诊断候选：`E:\Agent\comprehensive-cases\15-cyber-town-f009\scripts\f009_step5_attribution.py`，仅真实schema固定工作量的SQL等价/VM与分段成本对照；benchmark/steady_profile继续不改。
- 收益依据与局限：预算扫描末段均时约1.239ms是热点规模，不是可全消除成本；plain内存p95尚需减少1.074ms。当前不能给可置信的预计节省比例，更不能直接扣除均值换算p95。预验必须同时看到实际VM和末段耗时下降、12项统计完全等价；只有VM下降或收益不足以支持端到端改善则停止，不再重复无收益微优化。
- 先失败优先覆盖四scope/所有状态/cutoff前等于后/NULL损坏/警告与首拒顺序/replay/16并发/回滚，再用真实迁移1000execution对照；无收益不改产品。有效后才另批落地及磁盘取消/重启/故障回归，最终另批warm-up+5-run。当前没有执行候选。
- 如需物化/临时结构、额外文件、索引/计数仓储、降同步或改变字段/阈值，必须停止并另提架构方案，不把它们隐含在本候选里。

不推荐候选B（业务仓储连接生命周期复用）作为下一次整体修复：
- 可能影响`E:\Agent\comprehensive-cases\15-cyber-town-f009\backend\src\cyber_town\infrastructure\persistence\sqlite_long_term_memory.py`、`sqlite_relationship.py`及对应生命周期/取消测试；本轮0修改。
- 证据仅为每请求2次connect+close，pair on平均约11.778ms、close p95 14.951ms。不是可保证消除的时间，远小于HTTP on p95差额337.509ms；且新增连接身份、关闭、取消、并发风险。没有足够收益依据批准扩到业务连接改造。
- HTTP当前保留“实际commit慢尾及队列放大”的机制级结论，底层原因/边界内可消除项仍不足。**本轮不提供伪确定的HTTP产品补丁，不继续扩大试验，不宣称阈值不可达。**

若用户希望先解决内存局部热点，下一授权必须明确候选A的预验/修改文件及新资源；若要求一次解决全部P1，应先确认存储架构与冻结持久化/尾延迟目标之间的决策范围，不能继续笼统授权“微优化”。两者均不自动执行。
### 门禁与Git

- 红测14 failed/8 passed；最终必要工具回归92 passed/45 deselected，包含23项V9新测试；其余69项既有工具/DTO回归。未运行原磁盘专项、全量质量或最终矩阵。pytest -s/-p no:cacheprovider，红绿basetemp始终未创建；只读确认不存在后调用，不复用已存在目录。
- ruff、两文件format、mypy通过；tracked diff及50个untracked no-index whitespace通过。无新venv/pytest/bytecode/cache；既有四处ignored缓存未变。pytest空设备审计误拦已按精确os.devnull修正，实际文件写入没有放开。
- 24个新磁盘库integrity/FK通过；800 trace、11200 stage、800 dispatch、400 control-on settlement，归属错0、成本0；4个内存场各1000 settlement、成本0、integrity/FK通过。
- 12份JSON禁止原文sentinel命中0；运行审计越界尝试0。无.env读取/真实模型/外部服务/F005访问。未把测试局部无命中当成对未来所有输入的隐私证明。
- growth最大control228KiB、observability432KiB、combined660KiB，business每场60KiB另列；全部在256/512/768冻结上限内。本轮没有SQLite recorder独立场景/拒绝场景，不重复声称这些门禁本轮已重验。
- 两处HEAD/origin/main仍1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3；正式main五文档、功能feat/f-009-safety-cost-performance仍33 tracked modified+50实际untracked，暂存0。本轮仅两个已存在untracked诊断文件变化；其他81文件、10migration、5旧证据、18 V7 JSON及V8摘要指纹不变。产品修复保留完整。
- 正式/功能data业务、control、observability SQLite均不存在。8000与本轮8个临时loopback端口均释放。
### 资源收口与手动处理建议

- 新根 `E:\Agent\cyber-town-f009-step5-tests\performance-v9-postfix-attribution`：**84文件、15子目录、93,006,274 bytes**。24个synthetic SQLite、24 WAL、24 SHM、12 metadata-only JSON；tmp为空，pytest-red-01/pytest-green-01未创建。所有实际路径都在先前登记清单内。
- 最终只读完整性查询在已登记路径补产生8组WAL/SHM，因此早期盘点68文件/92,744,130bytes不是最终清单；这些sidecar全部预先获准，未创建清单外资源。
- Step5父根 `E:\Agent\cyber-town-f009-step5-tests` 合计4498文件、2510子目录、684,811,098bytes，**已包含V9，不重复相加**；既有部分仍4414文件/2494子目录/591,804,824bytes，未动旧库。两个根reparse/env-like/嵌套Git均0，位于Git仓库外，tracked/untracked/ignored不适用。
- 功能worktree下既有ignored缓存：`.ruff_cache` 5文件/6682bytes；`.mypy_cache` 3/38301925；`backend\.mypy_cache` 4/34480371；`game\.godot` 6/3079；全部保留，不删除。
- **现在建议保留全部V9/V8及旧证据、worktree和缓存，当前立即删除清单为空。** V9是当前决策依据，期限仍至Step5收口。不要把worktree的83项未交付源码/测试当缓存。
- 将来Step5收口、用户确认不再需要后，重新核对精确路径/父链/占用/文件数与大小，再由用户手动执行：`Remove-Item -LiteralPath 'E:\Agent\cyber-town-f009-step5-tests\performance-v9-postfix-attribution' -Recurse`。仅作用该根；不删除父根/其他证据/worktree/缓存/分支。数据库及逐请求原始样本不在Git，删除不能从Git恢复；本命令**不是现在执行指令**。Codex不删除，只在用户反馈后只读复核。
- 候选后续根 `E:\Agent\cyber-town-f009-step5-tests\performance-v10-budget-equivalence` 当前不存在，未创建/未授权。若采用候选A，仅规划synthetic pytest/TEMP、真实迁移隔离control库及metadata等价摘要，保留至Step5收口；逐子路径仍须先打印并登记evidence，用户手动回收。不得复用V9数据库或覆盖JSON。

## V9 有限归因补证（2026-08-27，历史授权记录）

状态：`step_5_v9_attribution_authorized / diagnostic_tests_in_progress`。用户授权仅两个诊断文件；产品代码、benchmark、SQL、migration保持不变。预检83功能文件、10migration、5旧证据、18份V7 JSON及V8摘要SHA256全部一致；Git正式main五文档，功能33 tracked modified+50 untracked，两处HEAD/origin/main=1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3。性能P1/Step5/R-10开放。下方V8为历史。

本轮固定上限1profile+1plain，各4×100 HTTP及2×1000内存，总800/4000；真实TCP/独立客户端/逐请求计时；无额外warm-up/批次/最终矩阵。探针先红绿，探针不透明、归属不全、新产品缺陷或未复现立即停止。沿用V8真实长期写入/取消专项，不重复修复。

资源准确清单见evidence首节V9创建前台账；现有证据/缓存保留，禁止删除。

## V8 失败证据只读复核（2026-08-27，历史记录）

复核子状态：`step_5_v8_review_complete / awaiting_v9_attribution_authorization`。性能事实仍为 V8 core gate failed；性能P1、Step5、R-10继续开放。只读证据复核和下一方案起草已完成；**未修改任何产品/测试/脚本，未运行测试、profiling、性能矩阵或服务，未创建资源，未提交/推送/PR/部署/删除**。下方V8执行与V7记录为历史，不覆盖本节。

预检通过：正式main仅current-task、implementation-plan、roadmap、progress、evidence五文档；功能feat/f-009-safety-cost-performance仍33 tracked modified+50实际untracked。两处HEAD/本地origin/main均1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3。83功能文件对照evidence最新V8表一致，10migration/5旧证据/18份V7归因JSON/1份V8摘要指纹均一致。基线迁移完整哈希位于current-task历史锁定表，不只在evidence；按五文档登记综合比对。旧SQLite只hash，未建立连接。V8两处修复及取消修复保持；199项通过属于上轮结果，本轮未重跑。

证据来源（均只读）：
- V8：`E:\Agent\cyber-town-f009-step5-tests\performance-v8-minimal-fix\matrix-01\performance-summary.json`，SHA256 `7ef8bae909cb22c672badca4e7bf97838e1eaf16a22efd313fed7b006ee1a3fa`。
- V7：`E:\Agent\cyber-town-f009-step5-tests\performance-v7-attribution-resume-01` 内登记的18份JSON。它们发生于V8修复前，只作历史依据，不是当前热点实测。
- 功能源码：scripts/f009_step5_benchmark.py:164/307/377/408/558/705；scripts/f009_step5_steady_profile.py:254/313；scripts/f009_step5_attribution.py:320/495/539/737；application/control_performance.py:87/121、dialogue.py:351/604/945/1097；control/sqlite_control.py:65/714/1328；persistence/async_sqlite.py:43、sqlite_connection.py:119；以及既有取消/预算测试。相对路径均以功能worktree为根。

### 现有样本的新复核事实

全部计算仅在内存中处理已存在JSON，没有运行产品/诊断代码或另存报告。

| V8场景 | 五轮分位数中位数 p95/p99 ms | 直接从合并原始样本计算 p95/p99 ms（仅诊断） | 超限请求数 |
|---|---:|---:|---|
| 内存recorder | 3.3513 / 4.0356 | 3.4413 / 4.2232 | >2ms：1855/5000 |
| HTTP off | 360.5960 / 531.5800 | 377.4953 / 536.1903 | >250ms：46/500；>400ms：21/500 |
| HTTP on | 581.8708 / 694.0736 | 578.4650 / 740.5104 | >250ms：448/500；>400ms：45/500 |

冻结验收仍使用五轮统计中位数，未改成合并分位数。两种计算都没有推翻失败；内存p95、HTTP off/on绝对尾延迟和HTTP相对增量均非仅一轮异常。

| 同工作量内存链路 | 首100次均时的五轮中位数 | 中段501—600次 | 末100次 |
|---|---:|---:|---:|
| no-recorder control | 0.819993ms | 1.684435ms | 2.356611ms |
| in-memory control | 0.850067ms | 1.939205ms | 2.674376ms |

- recorder末段均时约首段3.15倍；该趋势在五轮recorder/no-recorder均存在，但个别中段尖峰说明仍有运行噪声。不能将增量全部归于预算，需在真实表布局测各操作。
- 内存每轮吞吐比为0.990228、1.086254、0.948917、0.843126、1.000406；冻结的“吞吐中位数之比”仍89.7562%，不是“各轮比值的中位数”。全部配对>=80%，不可据个别>100%称recorder加速。
- HTTP相对p95每轮差值为213.6211、342.0387、215.5915、148.2948、316.8796ms；对应允许72.1192、58.2761、64.56068、86.7152、78.66248ms，五轮均失败。
- HTTP on各轮p50约279—288ms，整体并非仅少数尾部请求慢。off慢样本出现在11/12、41/42、61/62、91/92等多个不同批次位置，不能把全部尖峰归于首请求初始化；这些只是样本位置，不是checkpoint证明。
- 相比当前汇总p95，达到冻结值需要内存减少1.3513ms（40.3%）、HTTP off减少110.596ms（30.7%）、on减少331.8708ms（57.0%）。这是验收差额，不是可消除物理成本下界，也不能拿局部平均耗时直接抵扣p95。

### 测量口径与覆盖核对

1. 正式矩阵各内存场景5×1000、各磁盘/HTTP场景5×100，另有一轮warm-up；源码逐请求perf_counter，nearest-rank分位数、五轮中位数符合原任务卡。HTTP为真实TCP、独立客户端，每次请求开始至响应解码计时，不是pair总时间/2；输入管道提交前与输出管道返回后不属于客户端HTTP计时。
2. throughput使用服务端驱动整个批次elapsed，因此包含批间驱动/IPC/时钟推进/文件元数据采样等额外开销；它与逐请求客户端延迟不是互为倒数。保持原定义，不做缩短计时制造通过。
3. recorder/no-recorder control调用相同控制/预算/provider/stage工作量；空no-op recorder微基准另列，不能作为复杂链路的吞吐对照。配对顺序固定off→on，未随机化，存在时间漂移风险；本轮只指出，不更改采样设计。
4. 每轮新仓储/新数据库。显式initialize、请求集合及服务启动在主要计时外；懒加载线程/连接首次使用仍可能在请求内。warm-up不是在同一业务库中预分配或复用空闲页；V8没有逐操作span，无法把每个样本的冷启动成本精确拆出。保留首样本，不剔除。
5. growth取max(0,逻辑主库增长,占用页增长)，combined仅control+observability，business另列；WAL/SHM是pair边界采样，不是所有瞬间真实峰值。上轮232/432/660KiB通过的结论保持。运行时WAL观测约4.1—4.2MB与收口主文件不是同一个指标，不能据此判空间门禁失败或忽略WAL。
6. SQLite recorder独立场景与HTTP使用的阶段/额外控制事件工作量不同，不能拿其101.606ms p95作为整条HTTP成本。核心HTTP写关系事件但长期表为空；真实长期记忆写入/忘记/替换/重启隔离由上轮磁盘专项证明。
7. 自动evaluate_performance_gate对HTTP绝对阈值只检查control-on；off超限由报告明确揭示。属于门禁自动覆盖局限，不能默认为off通过；本轮不修改该产品文件，未来如需修正须另列授权。

### 根因分级与被否定假设

| 判断 | 证据等级 | 结论/局限 |
|---|---|---|
| HTTP不能只怪预算或control-on | 已测量事实 | off自身全部五轮超限；on持续成本及尾部增量另有问题 |
| 当前全局map锁仍await落盘 | 已被源码否定 | V8全局锁仅purge；request/owner fence保留实际await，不能重复做旧修复 |
| 本矩阵同scope竞争是主要解释 | 源码推断不支持 | 每请求player/request/conversation唯一、NPC轮转，owner也不同；实际fence等待仍须测量，不能跳过安全锁 |
| 单writer队列与逐事务落盘仍有成本 | 源码确认机制；当前占比缺证据 | executor每lane单worker，control/obs每borrow路径+identity检查；各stage仍BEGIN/写/commit，business连接按操作开关。V7时间不能冒充V8占比 |
| 内存历史扫描没有被消除 | 源码+样本趋势 | 当前SQL仍扫描day窗口并join；每请求synthetic clock推进60秒，1000次总时长不足24h，历史可累积。没有O(1)保证 |
| 53.1%VM下降等于真实链路下降53.1% | 已被样例口径否定 | 该测试只建三张简化表、四类status各25%，有released；矩阵使用完整迁移且历史为settled。对照证明局部等价收益，不证明真实表物理布局、全settled数据与完整admission的同等收益 |
| recorder是内存超限唯一原因 | 已被对照否定 | no-recorder control五轮p95也均>2ms，末段同样增长 |
| WAL checkpoint已被证明是尖峰根因 | 未证实假设 | V8有成对慢样本及约4MB WAL采样，但没有逐commit对齐/实际autocheckpoint设置；不得改checkpoint策略或将WAL大小作因果证据 |
| 冻结阈值在当前硬件必然不可达 | 未证实 | 无可成立的物理下界；也没有证据承诺新微优化能通过 |

关键探针缺口：f009_step5_attribution.py当前只替换service._idempotency_lock和_scope_locks，未测V8新增_ownership_locks中的request/owner锁。其DTO探针只覆盖既有observability三类，预算/permit DTO并未全部覆盖。现有V8JSON只保留逐请求总耗时，没有修复后的锁、队列、commit、预算VM分布。因此不能可靠选定下一产品修复文件。

### 唯一推荐候选：V9 修复后有限归因补证（未授权实施）

本轮不提出缺乏收益证据的产品补丁。候选直接性能收益为0，目标是得到足够精确的修复选择依据；不承诺后续必然达标。

**精确后续文件范围（均位于功能worktree）**
- 修改 `E:\Agent\comprehensive-cases\15-cyber-town-f009\scripts\f009_step5_attribution.py`：V9根/有界runner与只在诊断期间启用的探针。
- 修改 `E:\Agent\comprehensive-cases\15-cyber-town-f009\backend\tests\test_attribution_step5.py`：探针、边界、隐私与计数回归。
- 产品文件0、新增源码文件0；不改benchmark、steady_profile、application/API/composition/repository、SQL、migration、Godot、依赖/CI。需要其他文件则停止申请，不靠运行时替换业务逻辑绕过范围。

**固定运行上限**
- 一组profile＋一组plain，各六场：http-off-single/http-on-single/http-off-pair/http-on-pair/memory-off/memory-on。
- 每HTTP场100 execution；每内存场1000 execution，合计800 HTTP＋4000内存。不增加warm-up批次、不追加重复轮数，不作为最终验收矩阵。
- 两组使用相同版本、synthetic输入/ID/时钟/顺序与对应同工作量；真实TCP、独立客户端、逐请求计时。保持14-stage、全部控制/关系写入、WAL/FULL、路径检查。plain不装任何性能探针。
- 这不是V8 random UUID数据的逐字重放；固定诊断ID用于本轮profile/plain内部对照，不能把与旧V8差异直接解释为收益。所有正常/慢样本保留；首请求与后续分开展示但都纳入总计。
- 不再重复整套取消修复或199项回归。新增探针须先通过聚焦的排队/重复取消/异常/关闭透明性测试；真实业务语义回归结论仍来自V8。

**可证伪测量要求**
1. 同一request的事件循环、request/owner/global/scope锁等待与持有、lane slot/queue/repository/resume必须关联固定synthetic序号与operation标识；原始UUID/scope只在运行内使用，不落摘要。只包裹真实锁调用，不改变获取顺序、生命周期、引用计数或await/取消结果。
2. 分开初始化、稳态、收尾；逐请求覆盖100%，每个storage submit有完整归属。按同请求区间并集/父子关系给exclusive与重叠说明，不相加inclusive，不把队列和其持锁者成本重复算进同一请求。
3. 在实际迁移创建的内存control schema与原1000 execution工作量内，测_all_window_totals的VM下界/误差、预算整体、scope tag、相关DTO、其他控制及recorder开销。首100/中段501—600/末100分别报告，不另建简化SQL表替代真实布局，不做新查询优化。
4. HTTP记录每库实际写commit与只读/空commit、连接开关、路径检查及writer等待；同步输出全部逐请求耗时与对应span。对尾部请求与同pair邻居对齐，但不丢弃其他请求。
5. 新实验连接可在setup仅读取wal_autocheckpoint/page_size/synchronous等配置metadata；不设置PRAGMA、不调用任何wal_checkpoint（包括PASSIVE）、不改变同步/自动checkpoint、不读取WAL业务内容。已有commit跨度和边界WAL大小不足以证明checkpoint时，明确保留该证据缺口，不扩大到系统追踪/新依赖。
6. 若只剩小额成本不足以解释p95差额，不能凭均值收益建议又一轮补丁；只有与慢请求对齐、有可消除重复操作证据且不触及冻结语义，才提出精确产品文件/可证伪收益判据。此时也不实施。
7. profile观测用于归因，plain才用于说明复现；只跑一组plain无法声称稳定回归通过或量化修复收益。未复现、探针归属不全/改变语义、缺文件授权、资源登记失败或发现新产品缺陷立即停止，不追加试验。

**失败优先和收口顺序**
A. 先列出完整新资源清单并登记；建立探针红测：新request/owner锁类型归属及无原文泄漏；跨线程operation关联/嵌套去重；取消/异常清理；真实预算调用计数及resource先登记后创建。
B. 仅修诊断工具，绿测通过后运行上述固定profile/plain；不修产品。老33取消组合不在本次重复范围，若探针暴露缺陷只报告。
C. 定向ruff/format/mypy须无新缓存，tracked/untracked whitespace、全部原指纹、新库integrity/FK/trace14-stage/dispatch/零成本和端口收口。真实长期写入不在新性能工作量中，明确继承既有专项证据。
D. 产出一项有依据的产品修复候选，或报告仍不足/架构待决；停止等待单独授权。之后真正产品修复仍须红测→磁盘语义→完整warm-up+5-run，所有门禁通过才申请Step5综合。

**新增风险与所需授权**
探针本身会增开销；新增锁包装、跨线程context及取消路径存在改变行为风险，因此先做透明性测试，plain完全卸载探针。当前没有收益证据授权业务连接池、减少提交、缓存安全校验或改变checkpoint；这些都不包含在V9。需要用户明确批准上述两个诊断文件及新资源根，产品授权仍为0。

### 资源规划与保留建议

候选V9根：`E:\Agent\cyber-town-f009-step5-tests\performance-v9-postfix-attribution`。只读确认不存在、父链无reparse；本轮没有创建。
候选直属路径：该根下`tmp`、`pytest-red-01`、`pytest-green-01`、`profile-01`、`plain-01`。profile/plain下只规划上述六个固定case目录及同名metadata-only JSON；HTTP目录内仅business.sqlite3/control.sqlite3/observability.sqlite3及WAL/SHM，内存case不创建control磁盘库。获准后每个实际完整子路径须先展开、打印、写入evidence，再创建；不得复用已存在basetemp。
内容类别synthetic pytest/TEMP、FakeProvider、隔离三库及metadata；无.env/真实密钥/真实对话/F005。TEMP/TMP/tempfile.tempdir固定候选tmp；既有解释器、不建venv/安装依赖。责任F009 Step5 V9，保留至Step5收口；用户手动回收，Codex不删除。

现有资源只读盘点未变化：
- V8根`E:\Agent\cyber-town-f009-step5-tests\performance-v8-minimal-fix`：775文件/136目录/56,353,518bytes。
- Step5父根`E:\Agent\cyber-town-f009-step5-tests`：4414文件/2494目录/591,804,824bytes（包含V8，不重复相加）。
- 功能worktree四处ignored缓存：.ruff_cache=5文件/6682bytes；.mypy_cache=3/38301925；backend/.mypy_cache=4/34480371；game/.godot=6/3079，均在`E:\Agent\comprehensive-cases\15-cyber-town-f009`。
- 无reparse/env-like/嵌套Git；测试父根位于Git外，tracked/untracked/ignored不适用；四缓存仍ignored。worktree本身有83项未交付源码/测试，不可当临时缓存删除。
- **本轮新增0、删除0，当前无建议立即删除的资源。** 保留V8/旧证据至Step5结束。未来用户确认不再需要后，重新审核路径/大小/占用，再按既有evidence精确Remove-Item -LiteralPath单根手动删除；不得删父目录/缓存/源码。实验数据库和原始样本不在Git，删除不可从Git恢复。worktree回收另行审核，使用git worktree remove，不用递归删除。

### 多轮未达标的简短复盘

- 已有有效修复解决了空间超限、事件循环阻塞、取消归属和全局锁覆盖过大，但这些是不同问题；解决其中一项不意味着总体性能通过。
- 诊断滞后：V8改了锁结构，V7探针和数据未同步覆盖新结构。没有当前逐请求成本账本就再选补丁，会重复猜测。
- 样例外推：简化预算表/混合状态的VM下降只能证明局部收益，不应外推真实布局/全settled历史和HTTP。
- 测量边界：warm-up与新库初始化、ratio-of-medians与median-of-ratios、主库增长与WAL边界采样、空长期表与真实写入，都应明示。现有失败不能由换口径消除。
- 以后本任务的落点：把“探针覆盖当前结构、真实工作量、固定补证上限、没有新证据不再微优化”写入本轮任务卡/实施计划；不修改全局AGENTS或其他范围。按investigate的根因优先与多次失败后重新审视架构原则，本轮不进行无证据产品改造。


### 下一条建议授权 Prompt（尚未执行）

```text
批准 F-009 Step5 P1 的 V9 修复后有限归因补证，按当前任务卡本节执行；不直接修改产品。

先只读核对两处HEAD/本地origin/main仍1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3，正式main仅五份项目文档，功能feat/f-009-safety-cost-performance仍33tracked+50实际untracked，83功能文件、10migration、旧V5/V6/V7及V8摘要指纹一致。差异立即停止，不reset/stash/覆盖/切分支。

仅允许修改功能worktree内：
E:\Agent\comprehensive-cases\15-cyber-town-f009\scripts\f009_step5_attribution.py
E:\Agent\comprehensive-cases\15-cyber-town-f009\backend\tests\test_attribution_step5.py
产品、benchmark、steady_profile、SQL、migration、Godot均不改；范围不足停止。

批准新根：
E:\Agent\cyber-town-f009-step5-tests\performance-v9-postfix-attribution
仅synthetic pytest/TEMP、FakeProvider、隔离三SQLite/WAL/SHM及metadata-only摘要。每个实际路径须先完整展开、打印并登记evidence，成功后才能创建；红绿/各批次使用全新目录，旧证据库不连接/复用。只用既有解释器，不建venv/安装依赖；TEMP/TMP/tempfile.tempdir固定已登记tmp，pytest正斜杠绝对basetemp、-s、禁缓存。保留至Step5收口，用户手动删除。

先失败优先验证新request/owner锁归属、跨线程/父子span去重、隐私、取消/异常透明性和资源边界；不得改真实锁顺序、owner引用、事务、await或取消结果。

绿测后仅一组profile＋一组plain，各六场：
HTTP off/on×单/双并发，每场100execution；
内存recorder/no-recorder，每场1000execution。
合计800HTTP＋4000内存，不追加warm-up/批次，不运行最终矩阵。

保持同一版本synthetic输入/ID/时钟/工作量、真实TCP独立客户端逐请求计时；plain卸载探针，全部慢样本保留。新增request/owner锁必须测到；预算必须在真实迁移schema与实际1000execution内测VM、预算整体、scope tag、DTO及其他控制开销，不以简化表替代。

分开初始化/稳态/收尾、锁、队列、连接、路径和每库实际commit；逐请求归属100%，使用区间并集/父子边界，不相加inclusive。新库setup只可读取autocheckpoint等配置，不设置PRAGMA、不手动checkpoint、不改变WAL/FULL或采集WAL正文。证据不足不能认定checkpoint根因。

保持14-stage增量落盘、durable open/restart abandoned、路径身份检查、scope/预算/dispatch/业务语义及全部冻结阈值。继承V8取消和真实长期写入专项结果，不用核心空长期表冒充完整写入性能。

发现新产品缺陷、探针影响语义、归属不全、资源越界或缺新文件权限立即停止；没复现也停止，不增加试验。不实施任何产品修复。

完成定向工具测试与无新缓存的ruff/format/mypy、whitespace、指纹、新库完整性/FK/14-stage/dispatch/零成本、端口收口；只更新正式五份文档，报告根因证据、测量局限、精确产品候选/收益判据或仍缺证据，并盘点资源给手动建议。

不读.env、不访问外部服务/真实模型/F005，不删除、不提交/推送/PR/部署，不关闭性能P1/Step5，不运行Step5综合或Step6。即使补证成功，也停止等待产品实施授权。
```

## V8 最小性能修复收口（2026-08-27，历史执行记录）

状态：`step_5_v8_core_gate_failed / awaiting_next_authorization`。两处最小产品修复及磁盘语义回归通过，但核心性能门禁失败；**性能 P1、Step5 和 R-10 仍开放**。本轮已停止，不执行 Step5 综合验收、Step6、进一步调优或 Git 交付。下方 V7 及更早章节均为历史记录，不覆盖本节。

### 修复与收益

- 产品仅 dialogue.py 与 sqlite_control.py：request owner 锁和 player+npc commit/revision 保护将磁盘 await 移出全局幂等锁；pending admission 计入容量，同 request 仍单 admission/execution/dispatch。按 request→owner 固定顺序，锁持有者及排队者引用计数防止锁实例替换；取消仍等待实际落盘，已完成业务/缓存/结算不回滚。
- 预算仍为同一 BEGIN IMMEDIATE 中单条固定参数化聚合，返回四 scope 的12项统计；等价使用 FILTER 减少重复计算，保留严格 cutoff、released 排除、reserved/dispatched 预留成本、settled 实际成本、warning/reject顺序和回滚。未增索引、计数表、缓存或 migration。
- 局部收益：1000行同数据预算查询 VM 步数 111036→52107，下降约53.1%；一组100次配对查询均时 1.332046→0.733808ms。此为局部对照，不代表端到端门禁通过；不同scope阻塞红测证明进展能力恢复，不等同总体尾延迟已解决。
- 本轮实际改动6个获准文件：2产品、2测试、2脚本；test_attribution_step5.py未改，既有取消修复保持。脚本只调整批准根/测量接入，不改工作量/阈值。

### 核心性能复验

完整无 profiling warm-up + 5-run 已运行。表中是五轮各自分位数/吞吐的中位数，不是合并样本分位数；内存每场每轮1000 execution，磁盘/HTTP每场每轮100 execution。HTTP采用真实本地TCP、独立客户端进程和逐请求计时，不删除慢样本。

| 场景 | p95 ms | p99 ms | 吞吐 /s | 结论 |
|---|---:|---:|---:|---|
| no-recorder 空记录基线 | 0.0007 | 0.0008 | 2324500.145 | 通过，不作为有控制工作量的配对基线 |
| no-recorder control | 2.9680 | 3.4966 | 579.648 | 同工作量配对基线 |
| in-memory control | 3.3513 | 4.0356 | 520.270 | p95 > 2，失败；p99 <= 5 |
| SQLite recorder | 101.6056 | 116.7823 | 12.359 | 通过 150/200ms、8/s |
| HTTP control-off | 360.5960 | 531.5800 | 8.820 | 自身已超过 250/400ms |
| HTTP control-on | 581.8708 | 694.0736 | 6.120 | 超过 250/400ms；吞吐通过 |
| rate reject | 3.0998 | 3.5668 | 628.271 | p95 <= 50ms、dispatch 0 |
| budget reject | 3.2739 | 3.7289 | 509.625 | p95 <= 50ms、dispatch 0 |
| breaker reject | 2.0731 | 2.6529 | 987.813 | p95 <= 50ms、dispatch 0 |

- 同工作量内存吞吐比 89.7562%（>=80%，通过）；预算仍随历史规模扫描，不能把单查询宣称 O(1)。
- HTTP control-on p95 增量 221.2748ms，大于允许的 max(360.596×20%,30)=72.1192ms，失败。
- HTTP十二个 warm-up/正式批次中，control/observability/combined 最大增长 232/432/660KiB，均通过 256/512/768KiB。business 每100请求增长60KiB，单列、不计 combined；SQLite recorder 最大增长312KiB。
- 固定失败码：`control_on_relative_p95_regression`、`full_loopback_p95_exceeded`、`full_loopback_p99_exceeded`、`in_memory_p95_exceeded`。HTTP off 绝对尾延迟同样超限，不能只归因于 control-on。
- 性能摘要：`E:\Agent\cyber-town-f009-step5-tests\performance-v8-minimal-fix\matrix-01\performance-summary.json`，SHA256 `7ef8bae909cb22c672badca4e7bf97838e1eaf16a22efd313fed7b006ee1a3fa`。全部逐轮数值及逐请求样本保留在该 metadata-only JSON。

### 验证与边界

- 红测3项：2个跨scope进展场景与1个预算VM等价/收益场景。修复后共199项不同测试通过：budget/async 94 + attribution 103 + 已单独运行的跨scope 2；先前27项绿测有重叠，不重复累计。
- 覆盖原33项磁盘取消、fresh/replay/waiter/owner-with-waiter、排队/运行/阶段提交后一次及重复取消、persona、orphan/迟到/旧generation、关闭/重启/abandoned/重复recovery、真实长期记忆写入/忘记/替换/owner隔离、预算边界/状态/顺序/并发/回滚。
- 本轮256个绿测/矩阵新库 integrity/FK、WAL/FULL 与闭合trace阶段检查通过；6个红测库仅保留，未拿失败阶段数据冒充最终验收。HTTP含warm-up共1200 trace/16800 stage、1200 dispatch、1200关系事件；control-on 600次结算实际成本0。语义用例验证真实长期写入；核心HTTP长期表为空，不能称长期写入性能验收。
- 7个允许文件定向ruff、format、mypy通过；两处tracked diff check及50个untracked no-index whitespace通过。77个未变功能文件、10 migration、5份旧证据及18份V7归因JSON指纹均不变；83文件最新指纹见 evidence。
- metadata摘要禁字段/固定原文sentinel命中0；没有读取.env、外网/真实模型/F005访问。FakeProvider链路成本0；预算专项中的明确synthetic价格样例不属于真实计费。
- 正式/功能6条运行时数据库路径均不存在，8000及12个矩阵临时端口均无监听。未运行 evaluator/digest、完整质量入口、Step5综合或Step6。

### Git、资源与下一步

正式目录 main 仅五份项目文档修改；功能分支 feat/f-009-safety-cost-performance 仍33 tracked modified + 50实际untracked（83文件）。两处HEAD/本地origin/main仍为 1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3。未新建/切换分支、reset、stash、提交、推送、PR、部署或删除；保留全部未交付内容。

新根 `E:\Agent\cyber-town-f009-step5-tests\performance-v8-minimal-fix`：775文件、136目录、56,353,518 bytes；262 synthetic SQLite、256 WAL、256 SHM、1 metadata-only JSON，tmp为空。全部实际文件路径已在 evidence 预登记；无reparse/env-like/嵌套Git。新库只读核验产生的WAL/SHM也在原预登记清单内。Step5父根合计4414文件、2494目录、591,804,824 bytes（已含V8，不能重复相加），旧证据继续保留。四处既有ignored缓存共18文件未变化。当前建议全部保留至Step5收口，**不建议立即删除**；功能worktree含未提交源码，更不能当缓存删除。精确子根、缓存及未来用户手动命令见 evidence。

后续必须另行授权。建议先只读对照V8失败样本和已有归因证据，再决定是否有证据支持新的最小范围；本轮没有证据支持继续扩大优化或放宽冻结阈值。取消与持久化语义通过不等于性能P1解决；不承诺下一方案必然达标。

## V7剩余补证与归因收口（2026-08-27，历史记录）

状态：`step_5_v7_attribution_complete / awaiting_minimal_product_fix_authorization`。已完成本轮授权的剩余磁盘补证、1组profile和2组plain；**性能P1、Step5、R-10仍开放，Step6未进入**。V7-CANCEL-RESPONSE-MAPPING修复保持；本轮产品修改0，仅诊断脚本和专项测试修改。没有最终warm-up+5-run、Step5综合、Git交付或清理。

### 完成与边界

- 开始/结束：正式main仅current-task/implementation-plan/roadmap/progress/evidence五文档；功能feat/f-009-safety-cost-performance为33tracked+50实际untracked，两处HEAD/本地origin/main仍1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3。除获准脚本/测试外81功能文件、10migration、5份V5/V6/V7旧证据SHA256不变；旧证据SQLite只hash、不连接。
- 新归因基础工具红测2 failed（缺失工具类/摘要函数）；补齐后最终69非磁盘测试通过，另11剩余磁盘用例通过，共80项不同测试。新增实际executor测试验证跨线程owner及slot/queue/repository/resume归属；历史取消33场景没有重复跑或重新实施修复。
- 剩余磁盘：orphan/忽略取消的迟到provider、旧generation忘记/替换、仓储故障、事务回滚/每lease校验、recorder故障隔离、owner/waiter、关闭、durable open重启abandoned/重复recovery和真实长期记忆写入/重启隔离。新库终检17trace/238stage，无open；abandoned是partial而非成功。recorder全故障用例业务成功但无trace，属于预期fail-open，不能将它算作完整trace。31库integrity/FK/WAL/FULL通过。
- 1profile+2plain均6场：每场HTTP100 execution（off/on×单/双并发），内存每场1000 execution（recorder/no-recorder同工作量）。总计1200 HTTP+6000内存执行，18份metadata-only JSON；真实TCP独立客户端逐请求计时，不除并发总时长，不删除慢样本。HTTP新库1200trace/16800stage、1200dispatch、1200关系事件；control-on共600次结算，无重复写入，cost0。核心HTTP长期表为空，不能称真实长期写入性能验证；实际长期写入单列在磁盘专项。
- 两文件ruff/format/mypy、两处tracked及50untracked whitespace通过。18份JSON固定禁字段/原文sentinel命中0，源码定向secret模式命中0，6条正式数据库不存在，8000及本轮13个临时端口无监听。无.env读取、真实模型/外网/F005访问、提交/推送/PR/部署/删除。

### 已证实根因与证据缺口

1. **HTTP跨请求全局锁与单writer排队**：profile双并发off/on全局幂等锁等待平均50.443/51.619ms每请求，观测writer队列55.311/56.385ms；scope锁等待约0.001ms。源码dialogue.py的全局幂等锁内仍await业务fingerprint/关系提交、control admission及observability阶段落盘。因此其他scope也受阻，不能只归咎预算或同scope串行。
2. **落盘与路径检查仍是显著成本**：off每请求15次observability写commit；on为20次，control9次事务（800次常规写+首次额外1次、99次无写commit/100请求），business1次写commit与2次连接/关闭。on双并发每请求obs写commit/路径均值66.549/41.762ms，control27.415/18.449ms；业务连接+关闭约11.632ms。它们嵌套在repository/锁区间中，**不可再相加为总延迟或物理下界**。
3. **内存预算历史扫描是独立热点**：固定单SQL每请求仍扫描窗口内历史；两组profile配对前/中/后平均VM步数均4030/39760/75460，末段约前段18.72倍。recorded预算扫描均值0.159→1.014→1.743ms；DTO均值约0.050ms/请求、scope tag约0.185ms/请求。no-recorder也超限，不能把问题判成recorder本身。
4. 事件循环heartbeat p95约2.35–3.02ms、p99约9.32–10.26ms；只能说明观测到调度波动，不能把其与磁盘/排队重叠时间再累加。没有测得可证明冻结阈值不可达的物理下界，也没有测得任何产品修复收益。本轮只定位根因，不承诺后续必然修好。
5. 两plain的内存吞吐比为114.28%/101.73%，满足80%但有运行噪声，不应宣称recorder加速。HTTP吞吐均>=4/s、control/obs/combined增长最大232/436/668KiB满足对应空间阈值；尾延迟/内存p95仍不通过。双并发control-on增量第一组39.46ms通过，第二组180.29ms失败，不能挑好的一组验收。

### 无profiling复现结果（p95 / p99，ms）

| 场景 | plain-01 | plain-02 | 冻结阈值 |
|---|---:|---:|---:|
| HTTP off单并发 | 143.749 / 205.622 | 150.160 / 336.733 | 250 / 400 |
| HTTP on单并发 | 341.971 / 497.415 | 346.101 / 510.242 | 250 / 400 |
| HTTP off双并发 | 453.158 / 672.506 | 412.161 / 658.779 | 250 / 400 |
| HTTP on双并发 | 492.620 / 800.092 | 592.452 / 847.104 | 250 / 400 |
| 内存no-recorder控制对照 | 4.152 / 5.026 | 4.048 / 4.990 | 配对基线，不冒充无工作量基线 |
| 内存recorder | 3.485 / 4.212 | 3.522 / 4.109 | 2 / 5 |

固定结论码（文档归因，不新增产品enum）：`V7_HTTP_TAIL_LATENCY_UNRESOLVED`、`V7_MEMORY_P95_UNRESOLVED`、`V7_HTTP_CONTROL_INCREMENT_UNSTABLE`。上述两plain不是最终矩阵验收。

### 资源状态与处置

新根`E:\Agent\cyber-town-f009-step5-tests\performance-v7-attribution-resume-01`：**224 files / 35 dirs / 71,440,568 bytes**，70 synthetic SQLite、68 WAL、68 SHM、18 metadata-only JSON，tmp为空；无env-like/reparse/nested Git/read-only。根位于Git仓库外，内部无tracked/untracked/ignored或嵌套仓库，不入功能Git。当前建议保留，待Step5收口且确认不再需要后用户手动回收；原始磁盘证据不能从Git恢复。

首次profile在独立客户端启动前被审计拦截1次TEMP随机探测写入，文件未创建、请求采样0；显式绑定已登记tempfile.tempdir后仅首场转入全新retry子目录，旧初始化库保留不复用。其后3批运行审计越界尝试均0。该诊断环境问题非产品缺陷，不能隐藏为全程尝试0。今后诊断启动需先固定TEMP/TMP与tempfile.tempdir，不能放行随机探测或让pytest清理旧目录。

全部Step5父根现3639files/2357dirs/535,451,306bytes（含本轮，不可重复加总）。既有四缓存仍18 ignored files、未变化；功能worktree和所有旧证据继续保留。精确分类、子根大小与报告指纹见evidence本轮收口。Codex未删除资源；本轮没有建议立即删除的资源。

本节结论优先于下方更早的历史授权/执行记录；后续建议仍未获产品实施授权。

### 推荐下一轮：两处产品热点的最小修复（待单独批准）

推荐一个分步方案，不默认扩大为仓储/线程重构：

1. 产品仅`backend/src/cyber_town/application/dialogue.py`：将全局幂等map锁收窄为短状态操作，使用明确的request/execution归属和必要的player+npc revision/commit fence，避免其他scope因await完整仓储/阶段落盘被全局锁串行阻塞。**不能简单移出await**；同request共享执行、conflict、取消前后归属、memory revision、关闭及已提交业务不可回滚必须先红测。每个持久化操作仍等待实际完成，阶段不合并/不延迟、不fire-and-forget。已有锁内等待是收益机会，不是已验证收益；其他单writer排队可能抵消收益。
2. 产品仅`backend/src/cyber_town/infrastructure/control/sqlite_control.py`：等价降低固定参数化预算聚合的重复scope/status/窗口运算，保持四scope和12项统计、严格cutoff、released排除、预留/实际成本、首个失败limit与原子事务不变。先比较VM步数/末段成本，不能把单SQL说成O(1)。不新增索引/计数表/触发器/跨请求缓存，不修改migration。具体SQL降低成本尚未经对照，若没有收益就停止，不扩大范围。
3. 精确测试范围：`backend/tests/test_dialogue_async_persistence.py`、`backend/tests/test_budget_control_step3.py`、`backend/tests/test_attribution_step5.py`；诊断/验收脚本仅`scripts/f009_step5_attribution.py`与`scripts/f009_step5_benchmark.py`的根配置/测量接入，不能放宽门禁或修改工作量。
4. 本轮明确不推荐直接扩张到业务仓储连接池、OS安全检查缓存、异步延迟提交或新migration。业务连接关闭的测得开销不足以解释全部尾延迟；没有足够收益证据将其加入最小产品范围。
5. 可证伪：不同scope在另一request等待磁盘时应能完成短幂等状态阶段；同request仍单execution/dispatch，commit fence阻止orphan/旧generation新写入。预算同输入返回完全一致的12项统计，VM/末段耗时下降才构成局部收益；最终仍只有完整冻结门禁全通过才算性能P1解决。不以局部指标下降代替p95/p99验收。
6. 顺序：失败优先→最小产品变更→真实三库取消/迟到/关闭/重启/长期写入和并发故障语义→无profiling完整warm-up+5-run核心矩阵。所有绝对/相对/吞吐/空间/dispatch门禁全绿后，才另申请Step5综合；任一语义新缺陷或范围不足停止，性能失败不继续Step5综合/Step6。
7. 候选新根：`E:\Agent\cyber-town-f009-step5-tests\performance-v8-minimal-fix`，本轮只读确认不存在，未创建。类别synthetic pytest/TEMP、三库/WAL/SHM、metadata-only摘要；不含秘密/F005；期限Step5收口，evidence登记、用户手动回收。每个实际路径成功展开打印登记后再创建；红绿和性能批次全新隔离，不复用旧DB/basetemp，只用既有解释器。

### 下一条产品修复授权Prompt（建议，本轮不执行）

> 批准按当前任务卡V7收口方案，最小修复F-009 Step5性能P1。先核对正式main仅五文档、功能feat/f-009-safety-cost-performance为33tracked+50实际untracked；两处HEAD/本地origin/main均1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3，83功能最新指纹/10migration/旧V5-V7证据及18份V7新JSON指纹不变，任一差异停止。产品修改仅限application/dialogue.py的全局幂等短临界区及owner/revision/commit fence，以及infrastructure/control/sqlite_control.py的等价预算聚合；测试及脚本范围严格按上述清单。授权新根E:\Agent\cyber-town-f009-step5-tests\performance-v8-minimal-fix，实际子路径先打印登记；仅既有解释器/synthetic三库/metadata-only/TEMP，不复用旧DB、不建venv、不安装依赖、不删资源。先红测再最小修复，先证明同request单执行、跨scope可进展及四scope预算完全等价，再过真实磁盘取消、迟到、重复取消、waiter/replay、orphan/旧generation、关闭/重启与真实长期写入回归。严禁只把await移出锁而丢失归属原子性。语义全绿后才运行无profiling完整warm-up+5-run、真实TCP独立客户端逐请求计时；保留全部Step0冻结阈值、WAL/FULL、每lease路径/身份检查、14-stage/durable open/abandoned、migration/约束、业务/Dialogue v1/Godot。产品范围不足、新语义缺陷或任一性能门禁失败立即停止，不扩大优化；只有全部性能门禁通过才标记performance_p1_resolved/awaiting_step_5_completion_authorization。仅正式五文档更新，不读.env、不访问外部服务/真实模型/F005，不提交、推送、PR、部署，不自动Step5综合或Step6。资源由用户手动回收。



## V7恢复补证执行登记（2026-08-27，当前状态）

用户已批准新根及V7剩余补证。状态：`step_5_v7_remaining_semantics_in_progress`。基线33tracked+50untracked、两处HEAD/origin/main=1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3、83功能/10migration/5证据指纹通过；正式仅五文档。旧SQLite未连接。此前取消修复保持，产品不修改；性能P1/Step5开放，Step6未进入。

先运行工具归属/隐私/资源边界回归及11项剩余磁盘语义；任一产品缺陷停止。仅语义全部通过才构建并执行1profile+2plain，非最终矩阵。新增诊断功能仍须失败优先。仅脚本f009_step5_attribution.py及test_attribution_step5.py可修改。

资源根：`E:\Agent\cyber-town-f009-step5-tests\performance-v7-attribution-resume-01`，批准创建，创建前确认不存在/无reparse父链。内容synthetic三库/WAL/SHM及pytest/TEMP，不含真实payload/秘密/F005；保留至Step5收口，用户手动删除，Codex不删除。实际路径创建前已成功打印，完整台账见evidence本节。未创建profile/plain目录；后续逐批登记。以下为历史状态，不覆盖本节。



## V7恢复授权与资源门禁（2026-08-27，当前状态）

用户已授权恢复V7剩余补证与归因；已完成只读预检。状态：`step_5_v7_resumption_preflight_complete / awaiting_resource_authorization`。此前V7-CANCEL-RESPONSE-MAPPING修复保持完成，不重复修改。性能P1/Step5/R10仍开放，Step6未进入。

- 正式main仍仅五文档；功能feat/f-009-safety-cost-performance仍33tracked+50实际untracked；两处HEAD/本地origin/main均1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3。
- 83功能文件、10migration及V5/V6 JSON/V7三库五份既有证据指纹与最新收口一致；两处git diff --check通过。证据SQLite只做文件SHA256核对，没有建立连接。
- 剩余执行顺序：诊断工具归属/隐私/资源边界失败优先测试；独立orphan/迟到、旧generation、仓储故障回滚、durable open/abandoned及关闭恢复语义；通过后仅一组profile+两组plain。HTTP off/on×单/双并发每场100execution，内存配对每场1000execution。真实TCP独立客户端逐请求计时，不把两组plain当最终五轮验收。
- 功能改动仍限`scripts/f009_step5_attribution.py`和`backend/tests/test_attribution_step5.py`；不改产品application/API/composition/repository/SQL、migration、现有benchmark、Godot或冻结阈值。任何确认产品缺陷立即停止申请独立修复。
- 现有诊断脚本只有归属基础设施，还需在获准脚本范围内补齐实际runner/探针及测试；不能把历史V5/V6数据当本轮V7执行结果。

**尚需确认的精确新资源根**：`E:\Agent\cyber-town-f009-step5-tests\performance-v7-attribution-resume-01`。只读确认不存在，现有父链无reparse。当前恢复授权已确认任务范围，但未列明新根；依既有资源规则，先提出准确路径供确认，本轮不创建。不能改用旧取消根、覆盖旧证据或让pytest清理已有basetemp。

候选内容仅synthetic pytest/TEMP、FakeProvider数据、隔离business/control/observability SQLite及WAL/SHM、metadata-only归因摘要。责任F009 Step5 V7，保留至Step5收口；台账为evidence.md，用户手动回收，Codex不删除。根获批后，每个实际目录/数据库/sidecar/摘要路径仍须成功展开、打印、登记再创建，红绿批次隔离。

本轮只读调查及五文档状态更新，产品/脚本/测试修改0、测试/profiling0、新临时资源0、删除0。全部历史Step5证据、worktree和缓存继续保留，无需新增清理。无.env读取、外部服务/真实模型/F005访问，无提交/推送/PR/部署。停止等待精确新根确认，不恢复最终矩阵或Step5综合。

下一条资源确认可用：批准创建E:\Agent\cyber-town-f009-step5-tests\performance-v7-attribution-resume-01，按上述范围继续已授权V7补证与归因；全部实际子路径先打印登记，不复用旧库或basetemp，完成后由用户手动回收，不自动执行产品修复、最终矩阵、Step5综合或Step6。

以下为上轮修复收口及历史记录，不覆盖本节恢复授权状态。


## V7取消契约修复收口（2026-08-27，上轮状态）

状态：`step_5_v7_cancel_fix_complete / awaiting_v7_attribution_resumption_authorization`。V7-CANCEL-RESPONSE-MAPPING在本轮授权的33项磁盘取消场景中修复并验证；**性能P1、Step5、R-10仍未完成，Step6/7未进入**。本轮不恢复V7归因，不运行性能采样、最终矩阵或Step5综合验收。

- 保留此前dialogue部分修复，本轮仅追加正确的cache replay取消from_cache传递，并在observability DTO只放行REPLAYED/CANCELLED两种缓存重放终态；其他execution/dispatch/idempotency/scope/零成本约束不变。仅四个获准功能文件修改。
- 失败优先：DTO红测40 passed/1 failed；新三库replay取消红测1 failed，均复现ValueError。修复后最终专项**100 passed，17.99s**（41 DTO、25工具、原33磁盘、1长期记忆正向写入/重启）；既有DTO/persona内存回归**48 passed，0.88s**，共148项不同场景。最后格式/类型注解调整后又复核66项非磁盘专项通过，不重复计数。
- 原33磁盘覆盖fresh/replay/waiter/owner-with-waiter、排队/运行中/response_mapping阶段提交后、一次/重复取消、persona、关闭在途、三库重建与重复recovery；取消调用方收到CancelledError，唯一finish、14阶段；正常缓存重放仍REPLAYED。已完成execution缓存/预算/关系不回滚，不重复dispatch或业务写入。
- 最终green-02的102库只读终检：76 trace、1064 stage、33 cancelled（含6 replay cancelled）、open0、dispatch25、cost0、integrity/FK失败0。25个provider execution各一次关系event和预算结算；另1个local-memory正向用例确实写入1条长期记忆，重启后仅原player+npc可读，跨NPC/player不可读；不将其冒充取消中长期写入或性能覆盖。
- 四文件ruff/format/mypy、两处tracked/50untracked whitespace、定向sensitive与ignore检查通过；其余79功能文件、全部10migration与V5/V6/V7旧证据指纹不变。正式main五文档、功能33tracked+50untracked，两处HEAD/本地origin/main仍1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3；6条正式数据库路径不存在、8000无监听。
- 第一轮green为77 passed/1 failed，错误是测试把摘要查询当完整字段而触发KeyError，不是新产品缺陷；改为直接核对新库trace_runs字段，另建green-02完整重跑，不复用失败库。此前命令长度与登记patch失败均在创建/运行前阻断，没有越界资源；进程审计越界尝试0。

资源：仅新建`E:\Agent\cyber-town-f009-step5-tests\performance-v7-cancel-fix\contract-followup-01`，现**345files / 51dirs / 24,711,168bytes**，包括141个synthetic SQLite、102个空WAL和102个SHM（只读终检新库时SQLite生成，均已预登记）。无.env-like、reparse、nested Git、只读文件或新增缓存。红测/中途green/最终green-02均保留，不删除。完整绝对路径、分类与手动回收条件见[evidence](evidence.md)。

**现在建议保留全部本轮及历史Step5证据、功能worktree与四缓存；无须现在删除。** Step5收口、确认不再需要后，用户才手动回收精确contract-followup-01子根，原始磁盘证据无法从Git恢复。Codex不删除、移动或清理任何资源。未提交/推送/PR/部署或切换分支。

剩余：V7尚需原计划中未执行的独立orphan/旧generation、故障/abandoned恢复等语义补证，以及1 profile+2 plain归因；是否恢复须另行授权。真实长期写入性能、完整warm-up+5-run和Step5综合仍未运行，不能由本轮绿测宣告性能P1解决。下一步只能建议单独授权恢复V7未完成补证，不重复实施已完成取消修复，不直接进入Step6。

以下记录为历史快照，不覆盖本节。


## V7 取消修复部分实施、契约阻塞收口（2026-08-27，历史状态）

状态：`step_5_v7_cancel_fix_partial / awaiting_cache_replay_contract_authorization`。**V7-CANCEL-RESPONSE-MAPPING尚未完整解决，性能P1/Step5/R10仍开放；Step6/7未进入。** 本轮未运行性能采样/矩阵/Step5综合。现有部分修复保留在未提交工作区，不擅自回退或继续扩大文件范围。

### 已执行、已证实与停止点

- 预检：正式main仅五文档，功能33tracked+50untracked，两处HEAD/本地origin/main=`1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3`。83既有功能文件、10migration和V5/V6/V7证据指纹一致；旧库仅核文件哈希，不建立SQLite连接。
- 红测独立新库：原排队场景1 failed（open/12-stage/finish0）；另2 failed证明运行中及response_mapping阶段提交后取消未抛CancelledError。后两项是同一取消窗口的已授权分支，不是性能测试。“提交后”指阶段事务已落盘、请求尚未返回，不指推翻已持久化的最终成功终态。
- 产品仅改`backend/src/cyber_town/application/dialogue.py`：把response构造及RESPONSE_MAPPING await移入既有try/CancelledError处理，worker drain后调用_check_cancelled；不改业务commit、预算、worker或仓储。诊断脚本只切换固定授权根，专项添加batch隔离和24项取消归属组合。
- 绿测**35 passed / 1 failed，4.12s**：工具25、persona磁盘8、原排队复现1、fresh排队归属/重建1通过；随后cache replay排队取消失败，立即停止，**22项剩余场景未执行**。不能称24项矩阵或全部取消修复完成。
- 原复现已变为complete/cancelled、14阶段、finish1、execution link1、dispatch1、关系event1、预算预留/结算各1。fresh场景另验证取消后缓存replay不重复provider/关系/预算，三库重建trace和计数不变、重复recovery=0；persona8项亦保持14阶段与唯一finish。
- 成功场景共45项synthetic scope/message/key比对命中0；3变更文件sensitive/ignore=0。仅限已完成测试覆盖，不冒称完整scope/隐私/真实模型验收。
- 运行中/阶段提交后绿测、waiter/owner-with-waiter、重复取消矩阵及关闭在途专项尚未执行。长期记忆正向写入、abandoned恢复、性能补证继续留待后续授权，不将空长期表当完整业务验证。

### 新阻塞：CACHE_REPLAY终态契约与取消冲突

最小复现：先完成一个fake请求→相同request cache replay→让replay的RESPONSE_MAPPING排队→取消该attempt→已有取消收口调用afinish。实际抛出`ValueError("Cache replay invariants are inconsistent")`，未向调用者保持预期CancelledError；失败位置`application/observability.py:457`。测试`test_disk_response_mapping_cancel_ownership[1-queued-replay]`；该失败库未再连接/改写以补结果。

源码证据：TraceMetadata._validate_attempt对CACHE_REPLAY同时要求from_cache=True、execution_id=None、dispatch0、idempotency=CACHE_REPLAY，**且终态只能REPLAYED**；dialogue取消分支传CANCELLED但未传from_cache（默认False）。仅补from_cache仍会被终态限制拒绝。把取消写作成功REPLAYED或改attempt身份会掩盖真实取消，不在本轮语义边界内。需要修改未授权的application/observability.py，故停止。是否遗留open的后续库状态本轮未追加查询，不以源码推断冒充新磁盘测量。

### 最小新增授权建议（本轮不实施）

1. 在已有dialogue.py范围内，为已识别的cache replay取消收口保留from_cache=True。
2. **新增唯一产品文件授权**：`E:\Agent\comprehensive-cases\15-cyber-town-f009\backend\src\cyber_town\application\observability.py`。只允许兼容“CACHE_REPLAY + CANCELLED”的明确组合，不改变正常REPLAYED路径；继续强制execution_id=None、dispatch0、idempotency=CACHE_REPLAY、from_cache=True、零成本、合法request/scope和唯一终态。不得将其他无效组合一并放宽。
3. 测试仍在test_attribution_step5.py：先DTO正负红测与replay磁盘复现，再最小修复，重跑原33磁盘场景及25工具回归；增加错误终态/错误execution/dispatch/from_cache等拒绝样例。脚本只调整新批次资源边界。
4. 候选全新子根：`E:\Agent\cyber-town-f009-step5-tests\performance-v7-cancel-fix\contract-followup-01`（本轮确认不存在，未创建）。仅synthetic三库/WAL/SHM/pytest/TEMP；每个实际路径创建前展开打印登记，red/green不复用；保留至Step5收口，用户手动回收。
5. 现有SQLite已包含cancelled枚举，因此目前未发现需要migration的依据；这不是放行DDL。保持全部10migration、14-stage/WAL/FULL、scope/预算/幂等及外部契约不变。需要其他产品文件或新缺陷立即停止。
6. 通过标准：cache replay取消为complete/cancelled、from_cache=True、无execution/dispatch，已有execution无重复结算/业务写入；正常replay保持replayed，24组合和persona/关闭/重建全部通过。**不承诺任何性能收益**，通过后仍停止，不自动恢复V7 profiling。

### Git、静态检查与资源

本轮仅三个获准文件变化，其余80既有功能文件和10migration/V5/V6/V7证据SHA256不变。正式仍main五文档；功能仍33tracked modified+50untracked，分支和HEAD未变。3文件ruff/format/mypy通过，两处tracked和50untracked whitespace通过；正式/功能6条正式DB路径不存在，8000监听0；没有提交/推送/PR/部署/删除。

`E:\Agent\cyber-town-f009-step5-tests\performance-v7-cancel-fix`：**42 files / 17 dirs / 6,365,184 bytes**；red9files/3dirs/1,363,968bytes，green33files/11dirs/5,001,216bytes，tmp空；都是synthetic SQLite，无保留WAL/SHM、日志、JSON、reparse、env-like、nested Git或read-only。已登记33绿测用例中只有11个创建，另22个尚未创建。准确全路径清单及已创建状态见[evidence](evidence.md)。

旧V7根仍30/13/4,546,560，四缓存盘点不变（5/6682、3/38301925、4/34480371、6/3079，文件数/bytes），18ignored文件；Step5父根3070files/2269dirs/439,299,570bytes，包含上述子根，不能重复相加。

**处理建议：现在保留新红/绿测试库、旧V7证据和全部worktree/缓存。** 没有到期即可安全删除的必需证据。Step5收口并确认不再需要后，由用户手动删除精确performance-v7-cancel-fix根；将丢失42库的实测状态，不能从Git恢复，不得删除父根或工作区。Codex不删除。手动命令和核对条件见evidence；新contract-followup-01未创建无需处理。

### 下一条授权 Prompt（建议，不执行）

> 批准修复V7 cache replay取消契约冲突。保留当前dialogue.py部分修复；新增允许修改application/observability.py，仅兼容CACHE_REPLAY+CANCELLED，并保持from_cache=True、execution_id=None、dispatch0、零成本、原scope/身份约束和正常REPLAYED语义；dialogue取消收口传递正确from_cache。继续只修改这两个产品文件、test_attribution_step5.py及诊断脚本的资源配置，不改SQL/migration/worker/repository/API/Godot/冻结阈值。先复核当前main五文档、功能33+50、两处1a4fc2c、10migration及已有证据哈希；差异停止。授权全新E:\Agent\cyber-town-f009-step5-tests\performance-v7-cancel-fix\contract-followup-01子根，所有实际路径先打印登记，旧证据和red/green目录不打开/复用/覆盖；仅synthetic三库/WAL/SHM/pytest/TEMP，保留至Step5收口由用户手动删除。先DTO正负红测和磁盘replay复现，再最小修复及原33磁盘/25工具回归、关闭/重建/预算owner验证。需扩展其他产品文件或发现新缺陷立即停止。只用既有解释器，不建venv/安装依赖，不读.env、不联网/真实模型/F005，不删除资源，不提交/推送/PR/部署，不进入Step6，不关闭性能P1/Step5；完成后只收口五文档并停止，不跑性能采样/矩阵/综合验收。

## 以下为上一轮V7结果和历史记录，不覆盖上述部分修复状态


## V7 磁盘验证收口（2026-08-27，当前权威状态）

状态：`step_5_v7_semantic_gate_failed / awaiting_response_mapping_cancel_fix_authorization`。**性能 P1、Step 5、R-10 均未完成；Step 6/7 未进入。** 已确认独立产品缺陷 `V7-CANCEL-RESPONSE-MAPPING`（P1），未实施产品修复。原 V6-CANCEL-01 persona 修复在本轮八个真实磁盘场景通过；不等于所有取消边界均通过。

### 本轮执行与停止点

- 开始预检全部符合：正式 main 五文档；功能指定分支 33 tracked modified + 48 untracked；两处 HEAD/本地 origin/main = `1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3`；81既有功能文件、10migration、V5/V6摘要指纹一致。
- 仅新增 `scripts/f009_step5_attribution.py`、`backend/tests/test_attribution_step5.py`。归属/区间exclusive时间/固定metadata/资源登记基础先红17再绿17；补SQLite路径与只读URI边界先红8再绿8，最终工具基础25 passed，文件写入尝试0。
- 真实三SQLite磁盘专项：**8 passed / 1 failed，3.28s**，审计越界尝试0；首个产品失败立即停止。25工具+8磁盘通过不合称全量质量通过。
- 已通过：known/missing persona × queued/running × once/twice cancellation；每例trace complete/cancelled、14阶段、finish一次、dispatch/成本/业务写入/预算预留0；已开始worker等待完成后关闭；同库重建两次recovery均0且trace不变。40项synthetic原始scope/message/key比对命中0。
- 三库 integrity/FK/WAL/FULL 检查在9个实际验证用例共27库通过，**不能代表30个保留库均已验收**（另3库属于审计误拦尝试）。
- 不再执行response_mapping其他时点、独立迟到/orphan/旧generation、完整预算owner/replay矩阵、abandoned恢复或长期记忆正向写入。当前复现long_term_memories=0，**不得称为完整业务/长期写入验证**。
- 1 profile + 2 plain、HTTP逐请求归因、memory配对1000、新性能矩阵、evaluator/digest、完整quality、CI均未运行。

### P1 最小复现、期望与实际

1. FakeProvider + AsyncSqliteExecutor + 隔离 business/control/observability SQLite（真实磁盘，WAL/FULL）。
2. 完成实际execution及STATE_COMMIT；保持observability worker忙碌，使RESPONSE_MAPPING持久化operation排队。
3. 取消HTTP尝试对应的service task；释放阻塞并await服务关闭。
4. 只读查询本用例库：`record_status=open`、`terminal_outcome=null`、`trace_stage_events=12`、`finish_calls=0`；provider_calls=1，relationship_events=1，budget_reservations=1，budget_settlements=1，execution_links=0，long_term_memories=0。
5. 失败断言：`V7_CANCEL_RESPONSE_MAPPING_OPEN`。期望已取消attempt完成唯一终态收口且14阶段完整；已提交业务/预算保留，不重新dispatch、重复结算或回滚已成功execution。

根因证据：`application/dialogue.py:510` 的RESPONSE_MAPPING await位于既有try/CancelledError处理之后；worker排队任务可被取消并向上传播CancelledError，因而跳过afinish。observability._apply_async不吞CancelledError是正确传播边界，不能用吞取消掩盖缺陷；worker drain/关闭仅收敛操作，不代替请求终态。已确认影响是attempt trace收口/阶段和execution关联不完整；未发现本用例重复业务写入，不推断所有其他scope安全。重启可能将遗留open归为abandoned是源码推断，本轮按停止规则未重启该失败库验证。

### 最小产品修复建议（待授权）

- 唯一产品候选：`E:\Agent\comprehensive-cases\15-cyber-town-f009\backend\src\cyber_town\application\dialogue.py`。将response mapping等待纳入取消收口范围，已开始operation drain后重新确认取消；保留完成execution和缓存结果、dispatch/预算owner，attempt终态只finish一次。不改变预算SQL、worker、repository、schema或业务写入语义。
- 测试：现有 `backend/tests/test_attribution_step5.py` 补response_mapping queued/running/committed、一次/重复取消、replay/waiter、关闭/重启及原persona8项回归；`scripts/f009_step5_attribution.py` 仅允许新授权测试根配置/路径审计所需小改，不混入性能实现。若单个产品文件不足，停止并申请精确新增文件授权。
- 可证伪收益：失败码消失、取消trace complete/cancelled、14阶段、唯一finish；已完成execution仍只dispatch/结算/写状态一次，replay不重复；完成trace重建不变、重复recovery无修改、非取消成功/拒绝不回归。**这是正确性收益，不承诺p95/p99改善或冻结门禁可达。**
- 测试顺序：新根登记→工具路径/隐私红绿→磁盘P1红测→最小产品修复→取消/关闭/重启/ownership回归→静态检查。任一产品缺陷或需扩大修改立即停止。
- 候选新根 `E:\Agent\cyber-town-f009-step5-tests\performance-v7-cancel-fix` 已只读确认不存在，本轮不创建；只容纳synthetic三SQLite/WAL/SHM及pytest/TEMP，期限Step5收口，台账本任务卡/evidence，用户手动回收。旧V7证据保留、不打开/复用/覆盖。
- 即使取消修复通过，也停止等待恢复V7归因的单独确认；不自动跑最终warm-up+5-run或Step5综合验收。HTTP/内存性能根因仍缺V6改造后的逐请求归因，V5预算扫描热点和V6四项性能失败证据不变。

### 收口门禁与资源

2文件ruff/format/mypy通过（mypy使用精确小写`os.devnull=nul`，首次大写NUL引发工具内部错误，未作为通过证据）；两处tracked diff、2新增文件no-index whitespace通过（exit1/无输出为有diff非whitespace失败）。2新文件sensitive=0、ignore违规=0。81既有功能文件、10migration、V5/V6摘要SHA256不变；功能33tracked+50实际untracked，正式main仍仅五文档；无提交/推送/PR/分支操作。两处正式business/observability/control数据库均不存在，8000监听0。

本轮资源根 `E:\Agent\cyber-town-f009-step5-tests\performance-v7-attribution`：**30 files / 13 dirs / 4,546,560 bytes**（根目录本身不计dirs），30个synthetic SQLite，无保留WAL/SHM、日志或JSON报告；reparse/env-like/嵌套Git/read-only均0。tmp空；两次harness误拦分别保留一个空目录和3库，不复用。准确逐路径台账、复现库指纹、工具误拦复盘见[evidence](evidence.md)。不在Git仓库内，tracked/untracked/ignored计数不适用。

Step5父根现3028 files / 2251 dirs / 432,934,386 bytes；扣除V7子树后原2998/2237/428,387,826不变。V6仍1660/1323/220,710,337。四缓存保持 .ruff_cache=5/6682、.mypy_cache=3/38301925、backend/.mypy_cache=4/34480371、game/.godot=6/3079（文件数/bytes），18ignored文件，无新venv/pytest缓存/bytecode。建议**现在保留全部V7失败证据、旧Step5证据及功能worktree/缓存**；Step5收口、证据确认不再需要后再由用户手动删除精确V7根。删除将不可从Git恢复这些实测数据库；不得删除Step5父目录或功能worktree。Codex本轮创建资源但未执行任何删除。

### 建议下一条产品修复授权 Prompt

> 批准最小修复 F-009 Step5 的 V7-CANCEL-RESPONSE-MAPPING P1，仅修复 response_mapping 取消终态收口，不执行性能优化或归因采样。先核对正式main五文档、功能feat/f-009-safety-cost-performance的33tracked+50untracked，HEAD/本地origin/main均1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3，10migration和V5/V6/V7证据指纹不变；差异立即停止。仅允许修改功能worktree的backend/src/cyber_town/application/dialogue.py、backend/tests/test_attribution_step5.py；scripts/f009_step5_attribution.py仅限新测试根配置和审计边界。授权新根E:\Agent\cyber-town-f009-step5-tests\performance-v7-cancel-fix，先展开打印登记全部实际子路径再创建，既有basetemp不复用，旧证据数据库不打开/覆盖/复用。仅synthetic三SQLite/WAL/SHM/pytest/TEMP，保留至Step5收口由用户手动删除。先失败优先复现，再修复，验证queued/running/committed、一次/重复取消、replay/waiter、关闭/重启和persona回归；已完成execution不得重新dispatch/结算/写业务，取消attempt保持唯一终态和14阶段，正常与降级行为不变。需修改其他产品文件或发现新缺陷立即停止。保持10migration、Dialogue v1、Godot、scope/幂等、WAL/FULL、逐stage提交、每lease路径/身份检查及全部冻结阈值不变。只用既有解释器，不建venv、不安装依赖、不读.env、不访问外部服务/F005。完成定向测试及ruff/format/mypy/diff/哈希/隐私/资源检查，仅更新正式五文档；不删除、提交、推送、PR、部署，不关闭性能P1/Step5，不进入Step6。修复通过后停止，另行确认恢复V7归因。

## 以下为 V7 启动及此前历史记录，不覆盖上述状态


## V7 执行启动（2026-08-27，当前授权）

用户已批准V7归因补证与磁盘取消验证，不授权产品修复。预检正式main五文档、功能33tracked+48untracked、两处1a4fc2c、81文件/10migration指纹和V5/V6证据哈希全部一致。仅新增scripts/f009_step5_attribution.py、backend/tests/test_attribution_step5.py。先诊断工具红绿，再磁盘取消；确认产品缺陷即停止，不执行后续性能场景。

资源创建前登记（责任F009 Step5 V7，尚未创建）：

- E:\Agent\cyber-town-f009-step5-tests\performance-v7-attribution
- E:\Agent\cyber-town-f009-step5-tests\performance-v7-attribution\tmp

类别：synthetic pytest/TEMP与后续隔离三库；不含.env、真实秘密或F005资源。期限Step5收口，用户手动删除，Codex不代删。首次红/绿测试-s、no cache/bytecode，进程审计拒绝文件写入及磁盘SQLite，不创建/复用basetemp。后续实际数据库及sidecar路径在创建前另列完整清单，打印和登记失败则不得创建。已有V5/V6/其他Step5证据不打开不覆盖；既有缓存保留不修改。



## V7 剩余性能方案只读收口（2026-08-27，当前权威状态）

状态：`step_5_performance_gate_failed / awaiting_v7_attribution_authorization`。本轮只读调查和方案起草已完成，**性能 P1 / Step 5 / R-10 未完成，Step 6/7 未进入**。V6-CANCEL-01 保持 `fixed / in_memory_regression_verified`；113 passed 为上一轮内存回归证据，本轮没有测试或 profiling，不重复修复 persona 取消收口。

### 预检与证据真实性

- 正式目录 `E:\Agent\comprehensive-cases\15-cyber-town` 为 main，仅 current-task、implementation-plan、roadmap、progress、evidence 五文档修改；功能 `E:\Agent\comprehensive-cases\15-cyber-town-f009` 为 feat/f-009-safety-cost-performance，33 tracked modified + 48 实际 untracked。
- 两处 HEAD / 本地 origin/main 均为 `1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3`；81 个既有功能/测试文件与取消修复收口指纹完全一致，10 份 migration 与最新登记完全一致。未 fetch、切分支、reset、stash、提交或修改功能文件。
- V6 性能摘要：`E:\Agent\cyber-town-f009-step5-tests\performance-v6-async\matrix-01\performance-summary.json`；SHA-256 `19A78F01793340F2D6EFFA9571ACF1DA00FDB8E78B816E0FE02A2DF210B872AE`。
- V5 诊断摘要：`E:\Agent\cyber-town-f009-step5-tests\performance-v5-architecture\diagnostics-01\summary.json`；SHA-256 `BA5433017569BD2F87640C2F2B5E4C971290B006129341D2A4B14EE57A9643DD`。
- 只读取源码、测试、文档和上述 metadata JSON；未连接任何旧 SQLite，未创建数据库、日志、报告、缓存、测试根或服务。investigate 仅用于证据/假设分离；其全局日志、遥测、同步、测试和提交动作均未执行。

### 已证实结果与不能推出的结论

V6 是完整 1 warm-up + 5-run；下表是五个正式轮次统计量的中位数，不是把全部样本混为一组。原始慢样本保留。

| 场景 | p95 / p99 (ms) | 吞吐 /s | 判定 |
| --- | --- | --- | --- |
| HTTP control-off | 435.4531 / 591.6488 | 9.302233 | 基础链路已高于 on 的 250/400 目标；单修预算不能证明整体达标 |
| HTTP control-on | 696.8400 / 872.0176 | 6.241478 | 两项绝对延迟失败；p95 差 261.3869 > 允许 87.09062 |
| 同工作量 no-recorder control | 2.5431 / 3.3675 | 699.903105 | 控制本体的 p95 已高于 2ms，不是只有 recorder 额外开销 |
| in-memory control | 2.7913 / 3.3676 | 688.481478 | p95 失败，p99 通过，配对吞吐 98.37% 通过 |
| SQLite observability | 73.7811 / 187.4854 | 15.880428 | 汇总门禁通过；正式轮 1/3 的 p99 为 229.10/204.63ms，尾部波动不得隐藏 |

稳定失败码仍为 `control_on_relative_p95_regression`、`full_loopback_p95_exceeded`、`full_loopback_p99_exceeded`、`in_memory_p95_exceeded`。不新增或放宽冻结验收定义；单轮波动单列风险，不把汇总通过说成每轮均通过。control/observability/combined 占用增长仍是先前通过的 232 / 420—436 / 652—668 KiB，业务另列 60 KiB；本轮未打开库重验。

1. **预算扫描热点：已有测量支持。** `sqlite_control.py:68` 的单条 SQL 扫描日窗口 reservation，JOIN owner / settlement，计算四 scope 的 12 项聚合；在 `reserve_budget` 的同一个 BEGIN IMMEDIATE 中执行。V5 前100/中800/后100每查询 VM 指令估算 4030/39760/75460，后段约前段18.7倍。on 后100聚合总耗时140.9757ms，占控制层 reserve_budget 的162.3667ms约86.82%；这是预算预留内部占比，不是整个请求占比，也不是物理下界。
2. **不是单纯 recorder 或线程导致内存超限。** 内存 benchmark 直接调用同步 SafetyControl + 内存 SQLite，未走 V6 worker；同工作量 no-recorder 也超限。单SQL≠常数复杂度。V5 未 profile 的 on 前/后100 p95为0.9943/3.9606ms；这支持随工作集增长的成本，不证明任一 SQL 重写能节省多少。
3. **HTTP 当前主因仍欠归因。** V6 JSON只有端到端样本、吞吐和库增长，没有 worker 入队/开始/结束/await恢复的逐请求区间，也没有改造后事件循环、全局锁和每库事务等待的关联时间线。V5 是改造前的同步执行，不能用其事件循环阻塞或锁等待数值证明 V6 的当前占比。
4. **可见结构风险，但收益未量化。** `application/dialogue.py:1047` 起在全局幂等锁内 await business 写入、relationship stage 和 state_commit stage；`async_sqlite.py` 每 lane 单 worker，存在跨请求排队可能；两个业务 repository 的 `_connect` 仍按调用开关连接。V5 pair有200次business connect/close，累计170.31/805.02ms，100次写commit累计914.50ms。这些总量不能相加为单请求下界，也不能直接预测 V6 复用连接收益。
5. **原 profiling 不可原样当作 V6 分线程证据。** `SteadyProfile.phase/segment/values` 是共享可变状态；缺少逐 operation/span 身份和跨线程归属。需要诊断包装在提交瞬间冻结 synthetic case/operation 身份，并为事件收集加保护；不可用全局 segment 给并发请求分账。独立客户端现有源码确实逐请求计时并并发发送，没有发现“并发总时间除请求数”的测量方式。
6. **不能承诺冻结阈值必然可达。** 只读证据既未证明物理下界不可达，也未证明去除某个热点足以达标。不得据此减少 commit、移除安全检查或扩大架构改造。

### 取消和业务验证缺口

| 边界 | 下一轮必须验证的语义（未执行） |
| --- | --- |
| persona 已知/缺失 × 排队/已开始 × 单次/重复取消 | 用真实三 SQLite 重验八组合；未开始的工作不执行，已开始必须 drain；终态只一次，14-stage完整，dispatch/业务写入为0，重启不改已收口 trace |
| stage 已commit、await尚未恢复 | 不能把线程当成已被取消；不得重复写入或伪称 rollback；取消与已提交结果按既有 ownership 协调 |
| RESPONSE_MAPPING 排队/开始/提交后 | `application/dialogue.py:510` 的 await 在统一取消捕获范围之外，结构类似 persona 缺口；仅标 **STATIC-CANCEL-RESPONSE-MAPPING / 待复现**，不是新已确认 P1，不修改产品。验证已提交业务状态保持、trace不遗留open、replay不增加dispatch |
| budget reserved/dispatched/settled | 未dispatch预留可释放；已dispatch按既有规则结算；重复取消/recovery不重复记账，不把“HTTP取消”误解为“从未执行” |
| waiter/orphan/旧generation/关闭 | 剩余waiter不被取消；孤儿/迟到不能新写业务；关闭等待已开始工作并拒绝新工作，重复关闭安全 |
| 故障/重启 | 真实事务错误原子rollback；普通完成和取消已收口trace保持；只有遗留open转abandoned，重复recovery为0；新进程短期history为空 |
| 长期记忆 | 重跑现有显式 Remember 命令的真实写入、同库重建和跨player/NPC隔离；核心HTTP benchmark的长期表为空，不能称其包含长期写入性能 |

若新增边界得到可重复失败：记录级别、最小复现、期望/实际和影响 scope，停止并单独申请修复。不得将既有 persona 修复重新标为未完成，也不得因为静态疑点就宣布新产品缺陷已确认。

### 唯一推荐候选：V7 逐请求归因补证，不直接改产品

当前不足以选择有收益证据的产品修复，因此按本轮授权的证据不足分支，只提出这一项候选，不用猜测拼成产品修改清单。

**精确新增文件，待授权且目前不存在：**

- `E:\Agent\comprehensive-cases\15-cyber-town-f009\scripts\f009_step5_attribution.py`
- `E:\Agent\comprehensive-cases\15-cyber-town-f009\backend\tests\test_attribution_step5.py`

不改 application/API/composition/repository、既有 benchmark、migration、Godot 或依赖。新脚本可以在诊断进程中包装现有调用，保留真实执行器/完整操作，不把业务搬到替代简化实现。新测试可复用现有 synthetic builder，并重跑已有相关测试；不复用旧数据库。

**可证伪假设与判据：**

- H-HTTP：尾部主要由全局幂等锁内的持久化等待、lane排队、业务连接/关闭或实际写commit中的一项/组合贡献，而非仅事件循环阻塞。分别测 off/on × 单/双并发，各100execution；区分初始化/稳态。记录 server内同一单调时钟的 submit/slot-acquired/worker-start/operation-end/await-resume、锁wait/hold、writer/path/connect/BEGIN/SQL/write-commit/close。用互斥区间或时间区间并集分解，单列重叠和无法归因残差，不加 inclusive 时间；客户端时长独立报告，不把不同进程时钟直接相减。
- H-MEMORY：预算聚合在1000execution后段仍是主要CPU增长源。off/on配对、前100/中800/后100，各自统计聚合时间、VM工作量、scope tag、DTO及其他操作；只有测量证明才选择下一步 SQL 表达式等价重写。不默认新增索引/缓存/计数表，不因fake成本为0跳过结算读取或完整性检查。
- 诊断一组带instrumentation + 两组不带instrumentation对照，均从新库开始、相同输入/ID/时钟/顺序；内存每场1000execution，HTTP每场100execution。两组plain只用于确认现象稳定性，不是收益对照（没有产品修改），更不是最终warm-up+5-run验收。无profile组不启用事件循环采样器或时间包装。
- 诊断工具自身先红测：并发operation归属不串扰、元数据不含payload/原始scope/SQL参数、线程计数不丢失、区间计算不重复累计、资源清单失败时不创建任何后续资源；再进行真实磁盘取消回归。任何确认产品缺陷立即停止，不能继续性能场景掩盖。
- 保留每场完整stage/commit/dispatch数量、FK/integrity/零成本；原始prompt/reply/记忆正文仅存在synthetic业务测试所需隔离库，不进入metadata摘要。明确长期写入语义单独验证。

**潜在产品落点只是后续授权方向，不是此次许可：**

- 预算若确认等价低常数计算可行，候选落点为 `backend/src/cyber_town/infrastructure/control/sqlite_control.py` 与 `backend/tests/test_budget_control_step3.py`，仍单固定参数化SQL/同一事务快照/原先失败优先级。现无收益数据，不声称已选定SQL改法。
- HTTP若证明业务连接生命周期为主要热点，才另列两份业务repository、`persistence/sqlite_connection.py` 和生命周期测试；若证明全局锁等待为主，需另列 `application/dialogue.py` 的ownership方案与测试。不能在本轮把连接复用或移锁自动授权；每库单writer、安全检查及取消原子边界必须维持。
- RESPONSE_MAPPING 如被复现，单独申请最小取消收口授权，不捆绑性能架构改造。

### 候选资源与清理边界

候选根 `E:\Agent\cyber-town-f009-step5-tests\performance-v7-attribution` 已只读确认不存在，父目录准确为 `E:\Agent\cyber-town-f009-step5-tests` 且不是reparse point。本轮未创建；真正执行前须再核对完整祖先边界。责任F-009 Step5 V7；仅synthetic/FakeProvider/隔离三库/WAL/SHM/pytest/TEMP和metadata-only归因摘要；禁止.env、真实秘密和F-005资源。

候选子路径（均未创建）：

- `E:\Agent\cyber-town-f009-step5-tests\performance-v7-attribution\resource-plan.json`
- `E:\Agent\cyber-town-f009-step5-tests\performance-v7-attribution\tmp`
- `E:\Agent\cyber-town-f009-step5-tests\performance-v7-attribution\pytest-cancellation-01`
- `E:\Agent\cyber-town-f009-step5-tests\performance-v7-attribution\profile-01`
- `E:\Agent\cyber-town-f009-step5-tests\performance-v7-attribution\plain-01`
- `E:\Agent\cyber-town-f009-step5-tests\performance-v7-attribution\plain-02`
- `E:\Agent\cyber-town-f009-step5-tests\performance-v7-attribution\summary.json`

三个诊断批次下固定六个case目录名为http-off-single/http-off-pair/http-on-single/http-on-pair/memory-off/memory-on。四个HTTP目录各包含business.sqlite3/control.sqlite3/observability.sqlite3及其WAL/SHM；内存场景不创建磁盘control库。pytest实际用例子路径须在执行前完整展开成绝对路径，写入正式evidence并成功打印，再创建；不能把上述父目录清单冒充已登记全部实际路径。新basetemp不得存在/复用；首次红测与后续绿测如需不同根，必须先追加准确路径取得确认，不让pytest自动清旧basetemp。

解释器继续用 `E:\Agent\comprehensive-cases\15-cyber-town\.venv\Scripts\python.exe`；不建venv/安装依赖。TEMP/TMP固定V7/tmp、pytest basetemp使用正斜杠绝对路径，禁用pytest cache和bytecode，不产生授权外缓存。保留至Step5收口，台账写正式evidence；由用户手动回收，Codex不删除。

**现有资源：当前全部继续保留，不建议此刻删除证据。**

| 准确路径 | 文件 / bytes | 处理建议 |
| --- | --- | --- |
| `E:\Agent\cyber-town-f009-step5-tests` | 2998 / 428387826 | P1仍开放，保留；2237目录、reparse/env-like/嵌套Git均0 |
| `E:\Agent\cyber-town-f009-step5-tests\performance-v6-async` | 1660 / 220710337 | 父根内子集，不重复计容量；保留归因基线 |
| `E:\Agent\comprehensive-cases\15-cyber-town-f009\.ruff_cache` | 5 / 6682 | 保留至F009交付后另行审计 |
| `E:\Agent\comprehensive-cases\15-cyber-town-f009\.mypy_cache` | 3 / 38301925 | 同上 |
| `E:\Agent\comprehensive-cases\15-cyber-town-f009\backend\.mypy_cache` | 4 / 34480371 | 同上 |
| `E:\Agent\comprehensive-cases\15-cyber-town-f009\game\.godot` | 6 / 3079 | 同上 |

功能worktree含81个未提交功能/测试文件，必须保留；缓存可重建但当前不清理；测试证据未入Git，删除后不能从Git恢复。V7未创建，无可回收内容。本轮新增/删除资源均0。

### 停止条件与后续验收顺序

1. 本轮到此停止，等待V7补证授权；尚无可以承诺达标的产品修复方案。
2. V7归因工具/资源边界不可信，或磁盘取消/完整性/ownership出现确认缺陷：停止，给出最小证据与单独授权范围。
3. V7证据仍不能确定最小高收益落点，或需要改变冻结语义/同步强度/索引/安全检查：停止，不扩大实验；说明证据不足或确有证据的架构冲突，不能用一次尖峰宣布不可达。
4. 只有具体产品修复方案另获批准后，先红测→最小改动→取消/并发/故障/重启/真实长期记忆语义→完整无profiling warm-up+5-run。HTTP真实TCP独立客户端逐请求计时；combined只计control+observability；内存对照同工作量。
5. 全部冻结绝对/相对/吞吐/空间/零dispatch门禁通过后，才申请Step5 evaluator、三进程digest、故障组合、完整质量入口。不得自动继续Step6。

冻结值：内存p95/p99≤2/5ms、配对吞吐≥80%；SQLite recorder≤150/200ms且≥8trace/s；拒绝p95≤50ms且dispatch0；HTTP≤250/400ms且≥4/s；on增量≤max(off p95×20%,30ms)；control/obs/combined≤256/512/768KiB。14-stage、durable open/restart abandoned、WAL/FULL、每次lease安全检查、预算/幂等/scope/业务/API/Godot/migration全部保持。

### 下一条建议授权 Prompt（补证门禁，不是空白产品修复授权）

当前证据不足以填写有收益依据的产品修改清单，因此先建议以下授权；V7完成后必须给出真正最小的产品修复Prompt，不能凭本段直接修改产品。

> 批准 F-009 Step5 P1 的 V7 逐请求归因补证与磁盘取消验证。先按本节核对正式main五文档、功能feat/f-009-safety-cost-performance的33tracked+48untracked、两处HEAD/本地origin/main=1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3、10migration及V5/V6证据哈希；差异停止。仅授权新增功能scripts/f009_step5_attribution.py、backend/tests/test_attribution_step5.py及E:\Agent\cyber-town-f009-step5-tests\performance-v7-attribution。全部实际子路径创建前成功展开、打印并登记；新basetemp不得复用，清单失败不得继续。先失败优先验证诊断归属/隐私/资源边界，再执行真实三SQLite persona/response_mapping取消、迟到、关闭、恢复和长期记忆语义验证；确认任何产品缺陷即停止等待单独修复授权，不改产品。语义通过后，仅执行任务卡的一组profile和两组plain，off/on×单/双HTTP各100、内存配对各1000，真实TCP独立客户端逐请求计时、逐span排他归因，保留全部事件/事务/写入。profile只定位，plain不冒充最终五轮验收。使用既有解释器，不建venv/安装依赖，不改application/API/composition/repository/SQL/migration/现有benchmark/Godot/冻结阈值，不访问旧SQLite、不覆盖证据。TEMP/TMP固定新根，禁用额外缓存，全程fake-only/no .env/no外部服务/no F005。只运行必要专项和定向ruff/format/mypy/diff/hash/隐私/新库integrity/FK，工具若需新缓存先登记确认。仅更新正式五文档；完成报告归因、覆盖缺口、精确产品授权清单及资源盘点。证据仍不足就停止，不扩大实验；不运行最终矩阵或Step5综合验收，不关闭P1/Step5，不进入Step6、不提交/推送/PR/部署/删除资源。

工程复盘：历次微优化通过定向正确性测试，并不代表端到端收益；从同步改为worker后必须重建线程/锁归因，不能延用旧同步profile下结论。当前通过明确的V7证据门禁限制下一轮范围，不再将“查询数少/线程化”直接等同于性能达标。此复盘仅写本任务文档，不改全局规则或AGENTS。

以下为历史记录，旧的“当前状态/待修复”以本节为准。


## V6-CANCEL-01 修复收口（2026-08-27 19:28 +08，当前状态）

V6-CANCEL-01：`fixed / in_memory_regression_verified`。用户仅授权取消收口最小修复，现已完成；整体仍为 `step_5_performance_gate_failed / awaiting_remaining_performance_plan_authorization`，性能P1/Step5/R10未完成，Step6未进入。

根因已以真实AsyncSqliteExecutor+内存durable协议fake复现：persona等待在统一try之外，排队取消遗留open；未知persona的已开始写入在drain后未检查取消，误走npc_not_found拒绝。红测6 failed/2 passed；把persona处理纳入既有try/CancelledError收口，并在未知persona写入返回后检查取消。仅修改功能application/dialogue.py和既有backend/tests/test_dialogue_async_persistence.py，未修改observer/worker/仓储/预算/SQL/migration/API/Godot/阈值。

新增9专项：已知/缺失persona × 排队/已开始 × 一次/重复取消8例，加未取消的未知persona拒绝1例。取消trace只finish一次、complete/cancelled、14-stage、execution未创建、dispatch/成本0、synthetic原始scope/message/key序列化命中0；未取消仍为rejected/npc_not_found/not_reached、不可retry。最终相关回归 **113 passed，1.98s**；2文件ruff/format/mypy通过；48untracked whitespace和两处tracked diff通过；10migration哈希不变，其余79个既有dirty文件指纹不变。两文件敏感扫描0、ignore违规0；其他文件的两个既有ContextVar命名提示不在此次修复范围，未称完整quality全绿。

本轮无新增临时资源：测试-s禁用落盘capture，禁用pytest cache/bytecode；进程审计钩子拒绝写文件、建目录及磁盘SQLite。首次启动误拦pytest日志NUL设备，发生在打开前，无文件创建；只放行准确os.devnull设备后，红/绿及最终回归filesystem_write_attempts=0。未创建/打开/复用旧SQLite，未重跑磁盘集成、HTTP性能矩阵、evaluator、digest、完整quality或CI。内存fake验证的是取消控制流和recorder调用契约，不冒充磁盘durability/restart验收；后续磁盘重验需先确认新子路径。

正式main仍仅五文档；功能分支feat/f-009-safety-cost-performance仍33tracked modified+48实际untracked；两处HEAD/本地origin/main均1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3。未提交、推送、PR、部署、切换分支、创建worktree或删除资源。已有性能证据仍是V6四项失败，不能用此次113绿测替代性能达标。

资源只读复核：E:\Agent\cyber-town-f009-step5-tests仍2998files/2237dirs/428387826bytes；其内performance-v6-async仍1660files/1323dirs/220710337bytes。四缓存.ruff_cache=5files/6682bytes、.mypy_cache=3/38301925、backend/.mypy_cache=4/34480371、game/.godot=6/3079，均未改变盘点；reparse/env-like/嵌套Git均0。**现在继续保留全部Step5证据、功能worktree与缓存；本轮新增0，无需新增清理。** 到Step5收口再由用户手动回收精确测试子根；完整路径、删除影响、不可从Git恢复及安全命令沿用下面V6资源台账，Codex不代删。

下一步仅建议用户另行授权剩余性能方案调查；预算扫描、HTTP架构修复及新测试子根/矩阵不能自动继续。已完成的取消修复无需重复授权。以下此前“取消待复现/修复”的记录均为历史状态，不覆盖本段。

### 最小复现、修复及可重复验证

- 复现：真实单worker执行器中先卡住request_validation，把另一工作排在persona stage前；persona提交后取消请求，释放worker，旧代码得到open而非complete。另一分支卡住正在执行的未知persona stage，再取消，旧代码抛NPC错误而非CancelledError。只用synthetic输入和内存fake，无SQLite。
- 修复：application/dialogue.py:436起将persona选择与astage归入既有异常收口；未知persona的drain返回后_check_cancelled；删除重复的独立error finish/log，沿用相同稳定错误映射。没有触碰response mapping、其他阶段或修改worker取消策略。
- 新测试：backend/tests/test_dialogue_async_persistence.py:104正常拒绝；:129八种取消组合。预派发execution_id为空、idempotency未创建；这是当前控制流的前置验证，不冒充真实业务库写入测量。
- 回归文件：test_async_sqlite.py、test_observability.py、test_observability_integration.py、test_dialogue_application.py，以及上述9个新测试节点。现有磁盘测试15例不在本次无落盘集合；不能称全量测试通过。
- 解释器：E:\Agent\comprehensive-cases\15-cyber-town\.venv\Scripts\python.exe；不创建venv/安装依赖。PYTHONDONTWRITEBYTECODE=1，PYTEST_DISABLE_PLUGIN_AUTOLOAD=1，PYTEST_ADDOPTS为空，CYBER_TOWN_LOAD_DOTENV=0，LLM_PROVIDER=fake；PYTHONPATH指向功能backend/src和根，TEMP/TMP仅指向已经存在的E:\Agent\cyber-town-f009-step5-tests\performance-v6-async\tmp。pytest参数-p no:cacheprovider -p anyio.pytest_plugin -s -q --tb=short；未使用tmp_path或basetemp。
- investigate流程只用于根因→红测→最小改动→绿测。未运行Skill全局日志/遥测/同步/提交，也未扩大为全套performance或质量入口。工程复盘：新增await必须纳入原异常收口；finish_on_cancel保留已开始工作的结果，不等于调用方已放弃取消，需要在选择终态前重新协调。

## 此前记录（历史快照）

## V6-CANCEL-01 最小修复启动（2026-08-27）

用户仅授权取消收口修复，不继续性能/预算优化。预检正式main五文档、功能33tracked+48untracked、两处1a4fc2c及81文件指纹一致。计划只改功能application/dialogue.py、既有backend/tests/test_dialogue_async_persistence.py；以真实AsyncSqliteExecutor和内存durable协议fake复现已知/未知persona、排队/已开始、重复取消，验证终态和14-stage。不创建测试根/SQLite/报告/缓存，不复用旧证据数据库。pytest禁用落盘capture/cache/bytecode并以审计钩子拒绝文件写入、mkdir和磁盘SQLite；TEMP/TMP仅指向已存在的V6/tmp，不新增资源。新磁盘集成测试需先单列路径获得确认，本轮不冒然执行。性能P1/Step5仍开放。

## V6 实施与核心门禁收口（2026-08-27 18:46 +08，当前权威状态）

状态：`step_5_performance_gate_failed / awaiting_v6_followup_authorization`。异步边界已经实施，但性能P1、Step5、R10均未完成；另有persona阶段排队取消的静态边界缺口待定向复现/修复。已按失败停止条件停止，不运行evaluator、三进程digest、故障综合、完整quality或Step6；无提交、推送、PR、部署、删除。

### 授权范围与实现

仅本轮7个产品文件、3个新增测试文件及benchmark最小接入：application的observability/control/dialogue，API的dialogue/composition/app，新增infrastructure/persistence/async_sqlite.py；测试test_async_sqlite.py、test_dialogue_async_persistence.py、test_async_persistence_api.py。每库一个有界worker（容量16），一次提交完整同步仓储操作；调用方等待实际提交，保留WAL/FULL、逐stage、路径/身份检查和原事务。DTO准备和asyncio状态仍在事件循环；已开始线程不会被当成已取消，需排空和归属协调。关闭排空请求、execution、orphan和worker。benchmark只注入同一执行器、await关闭与改用V6输出根。

没有修改预算聚合SQL/索引/计数表/缓存、10份migration、Dialogue v1、Godot、阈值。原76个dirty文件仅6个允许的既有文件变更，另新增app.py的tracked修改和4个新文件；其余70个原dirty文件指纹不变。

### 失败优先与语义证据

初始红测：executor缺模块、服务缺storage_executor；后续捕获open trace首stage排队取消未收口、顺序closed event loop重用兼容、新waiter接管历史取消标记等回归并修正。新测试夹具误读snapshot/recovery字段、Windows目录参数及URI审计器曾导致非产品失败，逐项留存，没有把失败报告记为产品通过。回归05工具输出截断，不作为验收；06以新basetemp重跑。

最终回归06：**414 passed / 1 deselected，40.01s**，包括28个新专项。覆盖整事务/线程归属、有界排队、开始前/后取消、重复取消、共享waiter、orphan/迟到、旧memory revision、replay、真实长期记忆写入与同库重建、recorder故障、逐lease校验、回滚和关闭。排除的是旧单次性能基线测试，随后完整核心矩阵独立执行。此结果不代表所有取消时点已穷尽。

静态复审发现 **V6-CANCEL-01（候选P1，待定向复现）**：application/dialogue.py 的persona astage等待位于_execute_attempt的try/CancelledError收口之前；若open和前两stage已提交，persona操作排在busy observability lane后，此时取消可以取消尚未开始的Future并从try之外退出。预期为cancelled终态+14-stage，按代码路径可能遗留open直到重启recovery。影响为当前尝试trace收口，预派发时业务写入/dispatch应仍为0；没有本轮定向实测，不冒充已复现。unknown NPC分支也需一并审计。矩阵运行期间发现此项，未在采样中修改产品；性能失败后不继续实施或追加测试。下一次必须先补红测和最小收口，再谈性能。

### 完整核心 warm-up + 5-run

1 warm-up+5正式轮；内存组各1000样本/轮，其余各100；9组共21600个采样操作（含warm-up），正式样本18000。HTTP真实TCP、独立客户端、双并发逐请求计时，不启用profiling、不剔除慢样本。下表为既有五轮统计量中位数，非每一轮均过限的承诺。

| 场景 | p50 / p95 / p99 ms | 吞吐/s | 增长KiB | 结论 |
| --- | --- | --- | --- | --- |
| full_loopback_control_off | 186.8473 / 435.4531 / 591.6488 | 9.302233 | 304 | 配对基线 |
| full_loopback_control_on | 273.1755 / 696.84 / 872.0176 | 6.241478 | 656 | 失败 |
| in_memory_control | 1.2805 / 2.7913 / 3.3676 | 688.481478 | 0 | 失败 |
| no_recorder | 0.0002 / 0.0003 / 0.0005 | 2782414.678823 | 0 | 汇总通过 |
| no_recorder_control | 1.2853 / 2.5431 / 3.3675 | 699.903105 | 0 | 配对基线 |
| sqlite_observability | 59.9901 / 73.7811 / 187.4854 | 15.880428 | 304 | 汇总通过 |
| sqlite_pre_dispatch_reject | 0.6065 / 1.7968 / 2.5615 | 1240.565499 | 0 | 汇总通过 |

rate/budget/breaker拒绝p95分别1.7307/1.8278/1.7968ms，均dispatch=0、增长=0。内存配对吞吐为98.37%（>=80%通过）；p95仍超过2ms。HTTP on-off p95增量261.3869ms，允许87.09062ms；on p95/p99阈值250/400ms仍失败。稳定失败码：control_on_relative_p95_regression、full_loopback_p95_exceeded、full_loopback_p99_exceeded、in_memory_p95_exceeded。

| 场景 | 五轮p95 ms（依次1—5） | 五轮p99 ms（依次1—5） |
| --- | --- | --- |
| full_loopback_control_off | 281.5602 / 483.4672 / 435.4531 / 443.4371 / 404.9013 | 622.6236 / 512.5296 / 602.1254 / 584.2198 / 591.6488 |
| full_loopback_control_on | 501.2911 / 696.8400 / 713.6026 / 732.4352 / 661.4268 | 878.7736 / 724.4514 / 876.2425 / 872.0176 / 834.3778 |
| in_memory_control | 2.9788 / 2.8391 / 2.6842 / 2.7913 / 2.6484 | 3.7527 / 3.3676 / 3.3549 / 3.4270 / 3.2706 |
| no_recorder | 0.0002 / 0.0002 / 0.0006 / 0.0003 / 0.0003 | 0.0003 / 0.0002 / 0.0121 / 0.0005 / 0.0005 |
| no_recorder_control | 2.5032 / 2.8460 / 2.8276 / 2.5431 / 2.4809 | 2.9520 / 3.4430 / 3.8489 / 3.3675 / 3.1147 |
| sqlite_observability | 72.4589 / 73.7811 / 74.8165 / 73.9943 / 73.3438 | 229.1000 / 82.8054 / 204.6324 / 187.4854 / 113.2407 |
| sqlite_pre_dispatch_reject | 1.7968 / 1.8841 / 1.4946 / 1.9759 / 1.5942 | 2.3202 / 3.2789 / 2.4153 / 2.5884 / 2.5615 |

SQLite recorder汇总p99通过，但第1/3正式轮p99为229.1000/204.6324ms，原始慢样本保留，未隐藏。不能据本轮宣称异步改造已改善HTTP尾延迟；相较V4的五轮汇总仍无达标收益，非同轮A/B不得推定纯线程收益或架构物理下界。V5已证实预算扫描随窗口增长，本轮未授权优化该SQL，内存超限仍存在。

核心HTTP on空间（含warm-up）control占用增长232KiB、observability420—436KiB、combined652—668KiB；对照主逻辑文件增长分别204、376—392、580—596KiB；按max(物理逻辑增长,占用增长)验收，未靠初始freelist复用。业务增长另列60KiB，不计combined。保留初末页/WAL/SHM和边界峰值证据，没有预分配/VACUUM/减事件/降同步。核心HTTP业务库各100条关系事件、100条关系状态，长期表为0，不能称完整长期写入性能验收；实际长期写入与隔离由上述单独语义测试验证。

### 终检与证据定位

- 11文件ruff、format、mypy通过；两处tracked diff检查通过；48untracked逐项no-index whitespace无错误，7项既有LF→CRLF提示未修改文件。
- 10migration SHA256全部与V4登记一致；业务/Schema/Godot本轮指纹不变。
- 60个新matrix SQLite以mode=ro&immutable=1检查，确认WAL为0后读取，integrity/FK通过。18个obs库各100trace/1400stage/100唯一dispatch owner/0成本、终态completed；6个HTTP on control库各100 settlement、0 active permit、0成本。
- 48个control/obs库+1摘要，共49 metadata surface ×10本轮synthetic sentinel，命中0；并非对任意秘密的形式证明。没有读取旧证据SQLite或F005资源。
- ignore违规0。81个dirty源码/测试/fixture扫描仍有两个既有credential_assignment命名提示：benchmark.py:224、steady_profile.py:407（ContextVar局部token，不是凭据）；未扩大修改范围，不称完整quality/CI全绿。
- 正式main五份文档；功能feat/f-009-safety-cost-performance为33tracked modified+48实际untracked。两处HEAD/本地origin/main仍1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3；worktree list为正式目录与F009。无分支、提交、推送或PR操作。
- 正式/功能三类data SQLite均不存在；8000及12个本轮端口62607/34554/34326/2954/57282/6223/41210/17726/46434/26998/2667/16370均无listener。
- 核心摘要：E:\Agent\cyber-town-f009-step5-tests\performance-v6-async\matrix-01\performance-summary.json；SHA256=19A78F01793340F2D6EFFA9571ACF1DA00FDB8E78B816E0FE02A2DF210B872AE。完整样本、初末页/sidecar、正式轮结果在此；路径预登记在matrix-plan.json。

### 临时资源最终台账与用户处置

V6创建于2026-08-27T18:09:44.2257680+08:00，责任F009 Step5 V6；matrix创建18:37:24+08。测试根只含synthetic三库/负向损坏夹具、WAL/SHM、metadata摘要与资源索引；无.env/真实密钥或对话。全部列明根reparse、hidden、read-only、嵌套Git为0。V6在任何Git工作树之外，tracked/untracked/ignored不适用（不在版本管理）；不是可以从Git恢复的资源。四缓存均为既有ignored共18文件，未新增授权外cache/venv/bytecode。

| 准确路径 | files / dirs / bytes | 状态与处理 |
| --- | --- | --- |
| E:\Agent\cyber-town-f009-step5-tests | 2998 / 2237 / 428387826 | 保留；父子统计不重复求和；用户手动回收 |
| E:\Agent\cyber-town-f009-step5-tests\performance-v3-diagnostic | 178 / 115 / 22407848 | 保留；父子统计不重复求和；用户手动回收 |
| E:\Agent\cyber-town-f009-step5-tests\performance-v4-gate | 455 / 336 / 55719927 | 保留；父子统计不重复求和；用户手动回收 |
| E:\Agent\cyber-town-f009-step5-tests\performance-v5-architecture | 13 / 10 / 4710307 | 保留；父子统计不重复求和；用户手动回收 |
| E:\Agent\cyber-town-f009-step5-tests\performance-v6-async | 1660 / 1323 / 220710337 | 保留；父子统计不重复求和；用户手动回收 |
| E:\Agent\comprehensive-cases\15-cyber-town-f009\.ruff_cache | 5 / 1 / 6682 | 保留；父子统计不重复求和；用户手动回收 |
| E:\Agent\comprehensive-cases\15-cyber-town-f009\.mypy_cache | 3 / 1 / 38301925 | 保留；父子统计不重复求和；用户手动回收 |
| E:\Agent\comprehensive-cases\15-cyber-town-f009\backend\.mypy_cache | 4 / 1 / 34480371 | 保留；父子统计不重复求和；用户手动回收 |
| E:\Agent\comprehensive-cases\15-cyber-town-f009\game\.godot | 6 / 2 / 3079 | 保留；父子统计不重复求和；用户手动回收 |

功能worktree E:\Agent\comprehensive-cases\15-cyber-town-f009 总234files/41dirs/75041988bytes，包含81个未提交功能改动及上述缓存，**必须保留，不得直接删目录**。唯一env-like为既有.env.example文件名，本轮未读取；.venv、.pytest_cache、__pycache__不存在。Step5父根=旧1338files/207677489bytes+V6新增1660files/220710337bytes；V3/V4/V5盘点未变。

| V6准确直接子路径 | files / dirs / bytes | 创建时间 +08 |
| --- | --- | --- |
| E:\Agent\cyber-town-f009-step5-tests\performance-v6-async\matrix-01 | 181 / 36 / 19531493 | 2026-08-27T18:37:24.2602914+08:00 |
| E:\Agent\cyber-town-f009-step5-tests\performance-v6-async\pytest-integration-green-01 | 3 / 1 / 454656 | 2026-08-27T18:18:08.6769524+08:00 |
| E:\Agent\cyber-town-f009-step5-tests\performance-v6-async\pytest-integration-green-02 | 3 / 1 / 454656 | 2026-08-27T18:18:55.4496402+08:00 |
| E:\Agent\cyber-town-f009-step5-tests\performance-v6-async\pytest-integration-red-01 | 3 / 1 / 454656 | 2026-08-27T18:14:21.6350107+08:00 |
| E:\Agent\cyber-town-f009-step5-tests\performance-v6-async\pytest-regression-01 | 213 / 203 / 29319225 | 2026-08-27T18:25:30.2112848+08:00 |
| E:\Agent\cyber-town-f009-step5-tests\performance-v6-async\pytest-regression-02 | 218 / 202 / 29171769 | 2026-08-27T18:27:48.7804181+08:00 |
| E:\Agent\cyber-town-f009-step5-tests\performance-v6-async\pytest-regression-03 | 228 / 206 / 30543929 | 2026-08-27T18:30:26.4096236+08:00 |
| E:\Agent\cyber-town-f009-step5-tests\performance-v6-async\pytest-regression-04 | 228 / 206 / 30543929 | 2026-08-27T18:31:51.5146925+08:00 |
| E:\Agent\cyber-town-f009-step5-tests\performance-v6-async\pytest-regression-05 | 228 / 206 / 30543929 | 2026-08-27T18:32:34.5373216+08:00 |
| E:\Agent\cyber-town-f009-step5-tests\performance-v6-async\pytest-regression-06 | 228 / 206 / 30543929 | 2026-08-27T18:36:18.8150817+08:00 |
| E:\Agent\cyber-town-f009-step5-tests\performance-v6-async\pytest-semantic-01 | 24 / 8 / 3637248 | 2026-08-27T18:22:00.8466575+08:00 |
| E:\Agent\cyber-town-f009-step5-tests\performance-v6-async\pytest-semantic-02 | 27 / 9 / 4091904 | 2026-08-27T18:23:21.7912321+08:00 |
| E:\Agent\cyber-town-f009-step5-tests\performance-v6-async\pytest-semantic-03 | 33 / 11 / 5001216 | 2026-08-27T18:23:55.7267538+08:00 |
| E:\Agent\cyber-town-f009-step5-tests\performance-v6-async\pytest-semantic-04 | 36 / 12 / 5455872 | 2026-08-27T18:24:23.7225703+08:00 |
| E:\Agent\cyber-town-f009-step5-tests\performance-v6-async\tmp | 0 / 0 / 0 | 2026-08-27T18:09:44.2377718+08:00 |

V6根另有matrix-plan.json（40404bytes）和6份pytest-regression-01至06-resource-index.jsonl（合计921522bytes），各SQLite/mkdir路径在创建前登记；所有实际子路径保存在这些索引和上表。pytest-red-01/pytest-green-01只预留，未实际产生目录。V6总体1502个SQLite、75个WAL（0bytes）、75个SHM（2457600bytes）、2个JSON、6个JSONL；matrix子根60库/60WAL/60SHM+1摘要=181files/19531493bytes。

**现在建议保留Step5全部失败/回归/性能证据、worktree和缓存，继续用于下一修订。没有自动删除。** V6到Step5收口后可由用户手动删除精确子根，预计回收220710337bytes；将失去所有该轮数据库、失败夹具和摘要，Git无法恢复。删除前重新核对路径、父目录、数量/大小、reparse与占用；若有变化先停止。届时用户命令仅为：

```powershell
Remove-Item -LiteralPath 'E:\Agent\cyber-town-f009-step5-tests\performance-v6-async' -Recurse
```

不要删除E:\Agent、Step5父根、功能worktree或缓存，不用Force；失败则停止报告。更早Step5资源和缓存仍按各自台账保留，worktree回收仅在Git交付后单独授权并使用普通git worktree remove。用户删除后Codex只读复核。

### 下一步建议授权范围（未执行）

先批准V6-CANCEL-01红测与最小终态收口修复（仍限已列application/dialogue、observability及三份V6测试），同时仅只读分析本轮metadata和已授权产品代码，提出HTTP尾延迟与预算扫描的下一最小方案。新测试子根和确切文件清单先登记确认，不覆盖V6证据。预算SQL/数据结构优化、扩大worker架构或下一核心矩阵必须另行明确批准；不得改阈值、migration、14-stage或业务语义。任何故障/门禁失败停止，不进入Step6。

## V6之前的阶段与授权历史（保留追溯，不覆盖上述当前状态）

## V6 异步边界实施启动（2026-08-27，历史过程）

最终语义回归06：414 passed、1 deselected，40.01s；排除旧单次性能采样，尚不代表性能门禁通过。核心矩阵全部219个候选资源路径已成功输出并登记至 E:\Agent\cyber-town-f009-step5-tests\performance-v6-async\matrix-plan.json（含台账自身、matrix-01、36组目录、60个SQLite及WAL/SHM、performance-summary.json）。目标此前不存在，祖先无reparse。只使用synthetic数据，保留至Step5收口由用户手动删除；矩阵不启用profiling、不使用旧库，1warm-up+5-run，内存每轮1000、其余每轮100，真实TCP独立客户端逐请求计时。开始运行，任何门禁失败不继续evaluator/digest/完整quality或Step6。

回归05结束输出因工具上下文截断未能取回，不将其认定为通过。为取得可核验最终结果，预登记新根 E:\Agent\cyber-town-f009-step5-tests\performance-v6-async\pytest-regression-06 及同级 pytest-regression-06-resource-index.jsonl；类别、期限、创建前逐路径登记和用户手动回收同05，旧证据保留、不复用。后续命令结果先存储再展示，避免丢失验收退出码。

重启新测试再次暴露断言字段误读：abandoned_after_restart是terminal_outcome而非reason_code，已对照旧enum与recovery实现修正测试，不改产品。复盘：此类夹具失败已重复，应先对照现有恢复测试/字段契约再写断言，不能凭文档简称推定字段。下一回归精确路径为E:\Agent\cyber-town-f009-step5-tests\performance-v6-async\pytest-regression-05及同级pytest-regression-05-resource-index.jsonl，内容/期限/回收同前，不复用旧库。11变更文件ruff和format通过。

回归03为413 passed/1 failed/1 deselected，唯一失败为新重启测试误以为initialize自动调用recovery；沿用既有显式recover_open_traces契约修正测试，不改仓储。11文件mypy通过。下一精确资源：E:\Agent\cyber-town-f009-step5-tests\performance-v6-async\pytest-regression-04及同级pytest-regression-04-resource-index.jsonl，类别/期限/用户手动回收同03。benchmark输出根仅从旧V4根切换为本次已授权V6根，避免旧证据复用。

回归02为409 passed/1 deselected（排除旧单次性能采样，不替代最终核心矩阵）。继续补齐事务回滚/逐lease检查、recorder故障、关闭取消及durable open重启幂等专项；benchmark只注入同一执行器并等待关闭，不改样本和阈值。下一精确资源：E:\Agent\cyber-town-f009-step5-tests\performance-v6-async\pytest-regression-03、同级pytest-regression-03-resource-index.jsonl；创建前逐路径flush登记，内容、期限和手动回收规则同02，不覆盖01/02。

下一次回归路径预登记：E:\Agent\cyber-town-f009-step5-tests\performance-v6-async\pytest-regression-02 及同级pytest-regression-02-resource-index.jsonl，类别/期限/用户手动回收边界同01。01结果389 passed/21 failed：资源审计器错误解释Windows file:///E:/只读URI，连接前拦截，未创建越界资源；另确认顺序asyncio.run调用的兼容性与被新waiter接管的旧取消标记两项回归。执行器仅在旧loop已关闭且无pending工作时允许重绑定；执行链按实际active waiter归属判断，不因历史cancelling计数误杀已接管执行。不新增缓存/索引/阈值修改。

V6根及tmp创建于2026-08-27 18:09:44 +08。执行器红测缺模块，11绿测通过；服务接入红测缺storage_executor参数。专项已到23 passed，补获并修复open-trace首stage排队取消未收口问题。期间pytest-integration-red-01、pytest-integration-green-01/02、pytest-semantic-01/02/03/04子根均在运行前输出；无旧basetemp复用。失败数据保留，不删除。第一次integration绿测误用snapshot读取持久trace，改为只读query_traces；参数化目录名和固定异常构造器两项测试夹具错误已纠正，非产品契约变更。

下一回归预登记：E:\Agent\cyber-town-f009-step5-tests\performance-v6-async\pytest-regression-01，以及同级pytest-regression-01-resource-index.jsonl。索引仅记准确绝对资源路径和类别，测试每次mkdir/SQLite连接前先flush登记；不含SQL、参数、scope或payload。新根内synthetic pytest/TEMP/三库/sidecar，保留至Step5收口，用户手动回收，不自动删除。此回归不运行完整quality、evaluator或性能矩阵。

用户已确认三份专项测试、benchmark最小接入及V6测试根。状态：step_5_async_boundary_in_progress。正式main五文档、功能32tracked+44untracked、两处1a4fc2c和十份migration预检通过；原76功能文件已只读指纹登记。范围沿用下方V6清单，预算扫描不实施。

资源首次创建清单已成功输出：E:\Agent\cyber-town-f009-step5-tests\performance-v6-async、其下tmp及pytest-red-01。责任F009 Step5 V6，仅synthetic三SQLite/pytest/TEMP/metadata摘要，保留至Step5收口，用户手动删除，Codex不删除；创建时间随后登记。pytest-red-01预留给pytest自行创建，禁止复用已有basetemp。其余实际子路径创建前再报告。旧证据数据库不打开、不复用、不覆盖。

## V6 实施授权已收到，等待测试清单与资源确认（2026-08-27）

当前状态：`step_5_async_boundary_authorized / awaiting_test_resource_confirmation`。用户已批准V5提出的application observability/control/dialogue、API dialogue/composition/app及新增async_sqlite.py的最小产品调用边界；无需重复申请这些产品文件。预算扫描优化不在此次授权内，既有SQL、索引、表、migration、14-stage/WAL/FULL及所有冻结阈值保持不变。P1/Step5/R10仍开放，未进入Step6。

本轮仅只读核对和五文档授权登记，尚未改产品/测试、未运行测试、未创建资源。正式main五文档，功能分支32tracked modified+44实际untracked；两处HEAD/本地origin/main均为1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3。原74文件与10migration匹配V4指纹；V5摘要SHA256仍BA5433017569BD2F87640C2F2B5E4C971290B006129341D2A4B14EE57A9643DD。关系写入处仍由幂等锁内waiter/task/revision检查保护，必须先验证新增await的取消/提交归属，不能只搬入线程。应用目前无仓储执行器关闭生命周期，需要在已授权API文件接入。

### 待确认的准确测试与资源清单

上轮V5候选明确“必要测试另列，实施前确认精确清单”，且未列新测试根。本轮将遗漏一次列清，尚未创建：

- E:\Agent\comprehensive-cases\15-cyber-town-f009\backend\tests\test_async_sqlite.py：有界排队、整事务、线程/连接归属、提交确认、取消、关闭、回滚及路径检查。
- E:\Agent\comprehensive-cases\15-cyber-town-f009\backend\tests\test_dialogue_async_persistence.py：真实服务的replay/waiter/orphan/旧generation、关系与短期提交边界、长期记忆写入及restart。
- E:\Agent\comprehensive-cases\15-cyber-town-f009\backend\tests\test_async_persistence_api.py：入口、错误/validation trace、显式注入、应用关闭与metadata-only边界。
- E:\Agent\comprehensive-cases\15-cyber-town-f009\scripts\f009_step5_benchmark.py：仅在必要时接入同一产品执行器与关闭生命周期，保持场景、样本数、独立TCP逐请求计时和所有门禁不变，不改预算测量口径或过滤慢样本。

候选根：E:\Agent\cyber-town-f009-step5-tests\performance-v6-async。只读确认不存在，父根及E:\Agent不是reparse point。责任F009 Step5 V6；状态“待授权、未创建”，无创建时间；仅synthetic pytest/TEMP、FakeProvider、隔离business/control/observability SQLite及WAL/SHM、metadata-only摘要，不含.env、真实秘密/对话/F005资源。建议保留至Step5收口，由用户手动回收，Codex不删除。

候选直接子路径：该根下tmp、pytest-red-01、pytest-green-01、pytest-regression-01、matrix-01。授权后各实际子路径须在创建前成功输出并登记；pytest basetemp用正斜杠绝对路径，既有basetemp和旧证据数据库不复用；若需要额外子路径先报告。只用正式目录既有解释器，不建venv/安装依赖、不创建授权外缓存。完整性能矩阵只在语义验证全通过后运行，失败即停止，不继续evaluator/digest/完整quality，不关闭P1。

### 只读资源复核及处置

Step5父根仍1338files/913dirs/207677489bytes；V3=178/115/22407848，V4=455/336/55719927，V5=13/10/4710307（父子不重复求和）。已有四缓存仍.ruff_cache=5files/6682bytes、.mypy_cache=3/38301925、backend/.mypy_cache=4/34480371、game/.godot=6/3079。上述目录内reparse/env-like/嵌套Git均0。未打开任何旧SQLite，未新增、移动、删除或清理资源。正式/功能目录三类正式DB均不存在，8000及V5登记四端口无listener。

现在建议保留Step5旧证据和活动worktree/缓存，不删除。V6不存在，无需清理。旧资源不再需要时按V5台账先复核再由用户手动处理；数据库/摘要不能从Git恢复，不因本次实施授权推定允许删除。

建议确认语：批准上述三份专项测试、benchmark最小接入及performance-v6-async测试根；继续已授权异步边界实施，先语义后完整核心warm-up+5-run，保持所有既有停止条件。预算扫描优化仍另行授权。

## V5 根因诊断收口（2026-08-27，历史状态）

状态：step_5_v5_diagnostic_complete / awaiting_product_async_boundary_authorization。P1/Step5/R10仍未完成；未实施异步产品架构、未进入Step6、未提交/推送/PR/部署/删除。

### 实际执行与证据

正式main五文档与功能32tracked+42untracked基线预检通过，两处HEAD/本地origin/main仍1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3。全部10migration和V4三JSON哈希匹配。新增仅 scripts/f009_step5_architecture_probe.py、backend/tests/test_architecture_probe_step5.py；原74文件及10migration终检哈希不变，功能当前32tracked+44untracked。

本轮8组：4×1000内存execution、4×100真实TCP请求，共4400；HTTP客户端独立进程，每请求计时，single/pair使用相同synthetic请求、时钟和两请求一组的推进顺序，区别仅是否同时发出。profile/plain分开，初始化/稳态/收尾分开。此为诊断单轮，既不是warm-up+5-run，也没有修复后A/B收益，不关闭任何性能门禁。

| 场景 | p95 / p99 ms | 吞吐/s | dispatch |
| --- | --- | --- | --- |
| memory-off-profile | 3.1017 /3.8091 | 515.7200 | 1000 |
| memory-on-profile | 3.3929 /4.2293 | 497.7936 | 1000 |
| memory-off-plain | 2.8401 /3.3693 | 608.8116 | 1000 |
| memory-on-plain | 3.1586 /3.9606 | 556.7031 | 1000 |
| HTTP single-profile | 190.9559 /312.9970 | 6.2006 | 100 |
| HTTP pair-profile | 626.3679 /783.3679 | 5.8702 | 100 |
| HTTP single-plain | 259.9669 /482.1753 | 5.9233 | 100 |
| HTTP pair-plain | 699.9403 /900.3817 | 6.1133 | 100 |

### 根因分解、否定与未知

- H1支持：源码同步仓储调用直接发生于async链路；5ms heartbeat实测single/pair事件循环延迟p95=134.0024/173.3560ms，max=380.6626/562.5792ms。plain组未开启heartbeat，其0-count不是“零调度延迟”。不能从这两轮直接量化线程改造的因果收益。
- 两组profile均每100请求control900、observability2000、business100次commit，WAL/FULL实际写入事件分别801/2000/100（99control为空提交，不能当实际落盘下界）。pair三库commit累计2376.93/6228.35/913.90ms；逐次路径校验2900次、3824.71ms；business connect/close各200次、170.31/805.02ms。每个统计口径独立，禁止相加nested inclusive方法时间。
- 显式锁等待并非本样本主要热点：pair幂等锁400次等待累计1.69ms，scope100次0.29ms，writer2900次20.41ms。幂等锁持有400次累计4518.47ms（包含内部操作，不另加到数据库耗时）。低锁等待不说明无串行化：事件循环被同步工作阻塞时，其他任务尚未获得调度来请求锁。本场景为unique scope，不能替代同scope waiter验证。
- H2支持：同工作量内存off/on中，预算单SQL的VM指令估算前100/中800/后100均值为4030/39760/75460，约18.7倍增长。每次progress callback计1000指令，单查询误差不足1000；这是VM工作量估算，不是扫描行数或物理下界。on前/后100聚合累计9.76→140.98ms、预算预留27.64→162.37ms；后段聚合约占预留87%，不是整个请求的87%。_scope_tags后段100请求累计8.45ms、预算tag2.66ms、1400个stage DTO构造3.29ms，低于聚合。单SQL仍随窗口数据增长，不能靠“查询数1”证明常数成本；没有实施另一SQL优化、缓存或计数表。
- 否定“仅recorder造成内存超限”：off plain仍2.8401ms>2ms；不得将不同运行的分位数差直接视为纯recorder成本。
- 尚未证明：冻结阈值在现有硬件绝对不可达；线程原型必然有效；全局锁可安全缩小；预算某个新SQL必然达标。未做产品异步原型、worker取消/迟到/关闭/重启矩阵，未补长期记忆写入；本轮HTTP长期记忆写入未发生，不冒称完整三类业务写入。

### 原型停止原因与下一最小授权范围

固定停止码：synchronous_persistence_contract_requires_await_boundary。DialogueTrace.stage/record_progress、SafetyControl.reserve_budget等为同步协议；调用点不会await返回值。把仓储替换为返回Future会提前继续，future.result()则继续阻塞事件循环。关系写入在全局幂等锁内检查waiter/task/revision后执行；新增await必须重新定义取消及commit归属。原型如果复制整个DialogueService、运行时改写AST或挪整个async服务到线程，会绕过本轮“忠实接入且不改产品”边界，因此没有执行。此是授权/接口限制，不是实测异步架构性能失败。

上一轮建议Prompt没有充分拆清脚本原型与产品调用边界的依赖，本轮不为完成原型而扩大权限。下一步建议单独授权最小async边界实现/验证，候选产品文件：
1. backend/src/cyber_town/application/observability.py：loop内构造不可变metadata，await持久化确认；不能把可变trace对象直接跨线程。
2. backend/src/cyber_town/application/control.py：保留现有sync业务规则，以async facade等待完整仓储事务。
3. backend/src/cyber_town/application/dialogue.py：实际await点及幂等/active waiter/generation/revision与取消后的写入归属。
4. backend/src/cyber_town/api/dialogue.py：入口限流及错误/validation trace路径的await。
5. backend/src/cyber_town/api/composition.py、api/app.py：显式注入有界执行器及关闭生命周期。
6. 新增 backend/src/cyber_town/infrastructure/persistence/async_sqlite.py：每库有界调度完整lease/事务，绝不按SQL拆任务，不共享未保护事务；不修改旧migration/同步强度/业务仓储连接复用。
必要测试另列，实施前仍需确认精确清单；这只是最小候选，不承诺无需其他文件。预算单查询CPU热点另需等价低VM SQL的候选与收益预验证，不引入跨请求缓存/新索引/表，若需这些须另授权。

确认后先失败优先验证排队前/中、执行中、提交后取消、orphan、旧generation、replay/waiter、关闭、rollback及restart；完整语义通过才进行不带profiling的核心warm-up+5-run（所有既有场景/阈值/样本量保留）。只要绝对/相对/空间/dispatch任一失败立即停，不运行evaluator/digest或完整quality。核心通过也只可标性能P1解决，Step5综合完成仍需授权。

### 门禁与资源台账

红测为新模块缺失1collection error，新增10项专项通过；两新文件ruff、format、mypy通过。mypy首次大写NUL导致工具把NUL/3.12视为路径而报内部错误（没有创建目录）；只读检查本机安装源码后改用os.devnull对应小写nul，无缓存模式通过。隐式模块re-export的20项类型错误已改为直接导入同一类对象，无语义变更；未重跑性能数据，不把import整理称为性能修复。tracked与两新文件no-index whitespace通过；新文件和五文档敏感扫描0，ignore策略通过。V4原两处ContextVar token命名提示不在本轮修改范围，仍保留。

仅对本轮12个新SQLite在sidecar为空/不存在后immutable只读审计：integrity全过，FK错误0；4个observability各100completed/fake、1400stage、14distinctsequence/trace、100dispatch link、零成本；4个control各100settlement。负面/取消/重启和长期写入不在这些结果内。9个metadata surface×8个payload/key/raw-player/NPC sentinel命中0，不替代完整scope/秘密检测。8000及23076/64205/40922/41101无listener；正式与功能目录三类正式SQLite均不存在。

新根 E:\Agent\cyber-town-f009-step5-tests\performance-v5-architecture 创建2026-08-27T17:37:54.8203713+08:00；责任F009 Step5 V5；13files/10dirs/4,710,307bytes，12synthetic SQLite+1metadata JSON，无剩余WAL/SHM、reparse/hidden/readonly/env-like/嵌套Git。tmp为空，四memory目录为空；仓库外tracked/untracked/ignored不适用。全部创建路径在stdout成功flush和文档登记后创建。summary.json为274339bytes，SHA256 BA5433017569BD2F87640C2F2B5E4C971290B006129341D2A4B14EE57A9643DD。

四个HTTP子目录均3文件（business/control/observability.sqlite3）：http-single-profile=1114112bytes，http-pair-profile=1105920bytes，http-single-plain=1110016bytes，http-pair-plain=1105920bytes。这些是最终绝对文件大小，不是冻结的增长值；本轮未作新增长门禁。

旧V3仍178files/115dirs/22407848bytes，V4仍455/336/55719927。Step5父根现1338files/913dirs/207677489bytes，差额仅V5，旧资源未连接/复用/删除。功能已有缓存保持原盘点：.ruff_cache=5files/6682bytes，.mypy_cache=3/38301925，backend/.mypy_cache=4/34480371，game/.godot=6/3079；共18ignored文件，无新venv/cache/bytecode。现有74功能文件完整保留。

处置建议：现在保留V3/V4/V5至Step5收口，尤其保留摘要；无服务占用但仍属待用证据。用户确认不再需要后、再次只读核对路径/占用/reparse/盘点，可手动执行：
    Remove-Item -LiteralPath 'E:\Agent\cyber-town-f009-step5-tests\performance-v5-architecture' -Recurse
只移除V5的13文件/约4.71MB，不能从Git恢复；不删除父根、V3/V4、worktree、分支或缓存，不使用Force，失败停止。Codex没有删除资源，本轮没有新增用户已删除资源。

## V4 性能续修收口（2026-08-27 17:15 +08，历史性能门禁）

状态：step_5_performance_gate_failed / awaiting_revised_performance_plan。性能P1、Step5和R10均未完成；不进入Step6，不继续evaluator/digest/故障组合/完整quality或Git交付。

### 可行性、限定修复与验证

- 预检匹配：正式main五文档，功能指定分支32 tracked modified+42实际untracked；两处HEAD/本地origin/main仍为1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3。旧V3根178files/115dirs/22407848bytes，十份migration哈希一致。
- 新隔离三库100请求、两两并发、独立TCP客户端：control/observability/business各900/2000/100次commit；有实际写入且WAL/FULL的commit分别801/2000/100，排除99个无写入control commit。50对请求的写入commit合计min/p50/p95/p99=139.911/154.545/201.784/439.148ms。BEGIN与writer锁等待单列，初始化和稳态分开。尖峰不是不可达物理下界，未触发“明确不可能”停止条件；不把累计inclusive时间相加冒充下界。
- 路径检查改为writer锁内每次重新lstat数据库和所有祖先，检查批准根、普通文件/目录、POSIX symlink与Windows全类reparse；canonical路径在构造时解析，不缓存安全判断。等待后检查文件身份；新连接开启前后对照祖先及已有文件身份；异常路径使writer不可继续复用。回滚、关闭、PID检查及commit语义保持。Windows实测及模拟POSIX/重解析边界测试通过，没有原生Linux验证。
- 100请求稳态：Path.resolve 8700→0；优化后每次完整验证共2900次、20300次lstat（7个组件/次，含批准根以上祖先），不是跳过检查。旧observability校验2000次/4614.736ms；新全部control+observability校验2900次/3159.774ms，覆盖口径不同，不作等量百分比。control._connect inclusive 2273.369→1016.593ms；100 durable open/1300 progress/100 finish及全部commit次数不变。
- 预算同一BEGIN IMMEDIATE快照下固定参数化SQL一次返回四scope×1h计数/24h计数/24h成本，4→1；不增加缓存/表/索引/migration。严格cutoff、released排除、reserved/dispatched预留、settled实际成本、warning和首个拒绝limit顺序不变。100HTTP聚合调用400→100；定位轮不替代1000execution内存门禁。
- 本轮仅修改批准的7文件：三个SQLite仓储/连接文件、两个测试文件、steady_profile与benchmark。原74文件中其他67文件哈希不变，10migration不变；无新源码文件、业务/API/Godot/依赖/CI改动。
- 红绿：45 failed/1 passed→46 passed；补齐联合回归首轮169 passed/1 failed（新增测试误期望仓储异常，实际应用层按既有契约映射ControlUnavailableError，修正测试期望），最终170 passed。覆盖24窗口边界组合、所有状态、12个拒绝优先级、NULL/重复/类型/状态约束、回滚、replay、16并发reservation、取消/迟到、连接、14-stage读回及独立HTTP。
- 7文件ruff/format/mypy通过；mypy新测试object未收窄问题已用类型断言修正。tracked及42untracked whitespace通过；旧SQL的CRLF提示不是whitespace缺陷，复核使用命令级core.safecrlf=false，不改配置或文件。

### 不带profiling的核心 warm-up + 5-run

每组1预热+5正式轮；内存每轮1000样本，其余每轮100；9组（拒绝分rate/budget/breaker）合计18000正式样本，含预热21600。HTTP为真实本地TCP、独立客户端进程逐请求计时，没有并发总耗时除以请求数。沿用冻结的“五轮分位数取中位数”口径：

| 场景 | p50 / p95 / p99 ms | 吞吐/s | 每轮增长 | 结果 |
| --- | --- | --- | --- | --- |
| no-recorder | 0.0002 /0.0002 /0.0002 | 3829950.077402 | 0 | 通过 |
| 同工作量no-recorder control | 1.2924 /2.5941 /3.4323 | 703.972913 | 0 | 配对参考 |
| in-memory control | 1.2567 /2.6070 /3.3372 | 716.052164 | 0 | p95>2失败 |
| SQLite observability | 57.5316 /71.8303 /144.8482 | 16.562827 | 304KiB | 汇总通过 |
| breaker reject | 0.5423 /1.3784 /1.9551 | 1412.648857 | 0 | 零dispatch，通过 |
| rate reject | 0.6019 /1.5552 /2.3796 | 1275.741269 | 0 | 零dispatch，通过 |
| budget reject | 0.8286 /2.1083 /2.7145 | 927.917512 | 0 | 零dispatch，通过 |
| HTTP control-off | 165.9293 /367.6284 /559.2154 | 10.360086 | combined300KiB | 相对参考 |
| HTTP control-on | 265.2642 /595.2054 /826.5936 | 6.518017 | combined652KiB | p95/p99/相对增量失败 |

on五轮p95=595.2054/624.9600/654.8554/539.4114/590.1285ms，p99=749.5839/826.5936/733.5629/848.9852/881.1104ms；内存五轮p95=2.6070/2.8637/2.4606/2.3929/2.8325ms。SQLite recorder单轮p99最大231.475ms，冻结的五轮中位数通过不意味着没有尖峰。

失败码：control_on_relative_p95_regression、full_loopback_p95_exceeded、full_loopback_p99_exceeded、in_memory_p95_exceeded。HTTP相对增量227.577ms，允许max(367.6284×20%,30)=73.52568ms；内存吞吐比101.72%，通过80%下限。阈值不变。

on各轮control增长224—228KiB、observability420—436KiB、combined648—660KiB，逐轮均低于256/512/768KiB；business各60KiB单列。combined不含业务，取主文件/扣freelist占用增长较大值。逐轮样本、吞吐、增长见JSON，未用旧库空闲页制造通过。

### 终检及未完成门禁

- 本轮66个性能/诊断库连接前确认WAL为0后immutable只读：integrity/FK全过。20个observability库各100 completed/fake、1400stage、dispatch=1/trace、零成本；14组HTTP关系事件各100，control-on各100settlement/300cost/200retry事件。预算拒绝库15条settlement属于预热前置数据，正式拒绝dispatch=0。负向pytest库故意损坏，不纳入健康性能库计数。
- 55个本轮control/observability/JSON surface初次跨fixture混用UUID sentinel得到96匹配；只读证实为6个预算拒绝库各16个合法request_id。按实际case的conversation ID（预算200、HTTP1—100）及原文/key/player/NPC sentinel复核，禁止原文命中0。该有限检查不替代完整scope/evaluator QA。
- ignore策略通过；5正式文档+74功能文件敏感扫描仍有2项自动提示：benchmark.py:223与steady_profile.py:407的局部变量token是ContextVar恢复标记，不是凭据，人工分类为命名误报。未改扫描器或在性能失败后重命名代码；完整quality/CI不能称全绿。后续须授权最小命名修正并复验。
- 两目录正式三类SQLite均不存在。8000和37583/35473/49015/20302/11591/23241/31344/64470/1958/17061/23942/28318/8088/30771/37767/32668/28255无listener；本轮服务/客户端已退出。无新venv、pytest cache、bytecode。
- 流程遗漏：矩阵逐项路径清单的PowerShell命令失败后，没有先检查返回码便启动矩阵，完整清单补报晚于部分子目录创建。全部资源仍在批准matrix-01内，无越界/旧库复用；已告知用户。后续必须先确认清单输出成功再创建，不把补报称为全部事前报告，不修改全局规则。
- 当前两项最小优化不足；没有证明冻结阈值必然不可达，也不承诺继续微调必然成功。下一步重新确认剩余性能/架构方案及命名扫描提示处理；不自行扩大异步架构、业务连接、migration、安全边界或阈值。

### 精确资源台账与手动处置

责任F009 Step5 P1，均synthetic，保留至Step5收口。新根E:\Agent\cyber-town-f009-step5-tests\performance-v4-gate，创建2026-08-27T16:52:37.0764305+08:00，455files/336dirs/55719927bytes：296SQLite、78WAL、78SHM、3metadata JSON。无reparse、hidden、read-only、env-like、嵌套Git；仓库外tracked/untracked/ignored不适用。

| 准确绝对路径 | 创建时间（2026-08-27 +08） | files / dirs / bytes | 建议 |
| --- | --- | --- | --- |
| E:\Agent\cyber-town-f009-step5-tests\performance-v4-gate\feasibility-01 | 16:52:53 | 10 /1 /1840594 | 保留可行性证据 |
| E:\Agent\cyber-town-f009-step5-tests\performance-v4-gate\after-optimized-01 | 17:02:16 | 10 /1 /1796788 | 保留优化后证据 |
| E:\Agent\cyber-town-f009-step5-tests\performance-v4-gate\matrix-01 | 17:03:11 | 181 /36 /19511091 | 保留失败矩阵 |
| E:\Agent\cyber-town-f009-step5-tests\performance-v4-gate\pytest-red-01 | 16:56:05 | 5 /21 /389120 | 已结束，按Step5期限保留 |
| E:\Agent\cyber-town-f009-step5-tests\performance-v4-gate\pytest-green-01 | 16:57:51 | 5 /21 /389120 | 已结束，按Step5期限保留 |
| E:\Agent\cyber-town-f009-step5-tests\performance-v4-gate\pytest-regression-01 | 17:00:03 | 122 /124 /15896607 | 含故障库，按期限保留 |
| E:\Agent\cyber-town-f009-step5-tests\performance-v4-gate\pytest-regression-02 | 17:01:34 | 122 /124 /15896607 | 最终170回归，保留 |
| E:\Agent\cyber-town-f009-step5-tests\performance-v4-gate\tmp | 16:52:37 | 0 /0 /0 | 空TEMP/TMP，保留 |

两诊断子根各含http-separated-on/business.sqlite3、control.sqlite3、observability.sqlite3及各-wal/-shm和summary.json。matrix-01中sqlite-observability-0…5、sqlite-reject-rate/budget/breaker-0…5、loopback-off/on-0…5含对应库及sidecar，另有performance-summary.json。pytest实际层级限定于各固定basetemp，目录/SQLite创建时输出准确路径；未复用basetemp。父子资源不重复求和。

旧V3准确路径E:\Agent\cyber-town-f009-step5-tests\performance-v3-diagnostic仍178files/115dirs/22407848bytes。其余旧Step5资源未连接/复用/删除；整个E:\Agent\cyber-town-f009-step5-tests现1325files/902dirs/202967182bytes，旧部分870files/147247255bytes，差额仅V4。各根无reparse/env-like/嵌套Git。

保留活动worktree E:\Agent\comprehensive-cases\15-cyber-town-f009（32 tracked modified、42实际untracked、18 ignored文件），不得递归删除。既有缓存：

- E:\Agent\comprehensive-cases\15-cyber-town-f009\.ruff_cache：5files/1dir/6682bytes；
- E:\Agent\comprehensive-cases\15-cyber-town-f009\.mypy_cache：3files/1dir/38301925bytes；
- E:\Agent\comprehensive-cases\15-cyber-town-f009\backend\.mypy_cache：4files/1dir/34480371bytes；
- E:\Agent\comprehensive-cases\15-cyber-town-f009\game\.godot：6files/2dirs/3079bytes。
均既有ignored资源，无reparse；无分支/worktree/缓存清理。正式main仍五文档、功能32+42，未提交。

现在建议全部保留。Step5收口、确认不再需要证据并再次核对路径/占用/reparse后，可由用户手动执行：

    Remove-Item -LiteralPath 'E:\Agent\cyber-town-f009-step5-tests\performance-v4-gate' -Recurse

仅移除V4的455文件及目录、约55.72MB；数据库/JSON不能从Git恢复。不删除父根、V3、worktree、分支或缓存，不用Force；失败停止并只读复核。Codex未执行删除；本轮没有新增用户已删除资源。

证据SHA256：
- performance-v4-gate/feasibility-01/summary.json：c22332d38d010180c99bd47e806fe2690ccae770b544ce6fe12c8f33870fd522；
- performance-v4-gate/after-optimized-01/summary.json：d07d83686cca622273e6bdb338c02ded4698d87918caf721cf2e331e236fe9aa；
- performance-v4-gate/matrix-01/performance-summary.json：d2d8ebcb946d247dbc3c095bfdd1e6ab730af2233ddb1a7af33448c5ec2ed68f。


## V4 授权与资源登记（2026-08-27，历史授权快照）

用户批准可行性验证→路径逐次等价去重→预算4→1聚合→核心warm-up+5-run；每道停止条件优先，不进入Step6或后续综合验收。预检：正式main五文档，功能指定分支32modified/42untracked；两处HEAD/本地origin/main=1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3，十迁移哈希不变。旧performance-v3-diagnostic为178files/115dirs/22407848bytes，无reparse，不连接或复用旧库。

新授权根`E:\Agent\cyber-town-f009-step5-tests\performance-v4-gate`，责任F009 Step5 P1，状态批准待创建；仅synthetic三SQLite/pytest/TEMP及metadata-only摘要，无真实秘密、原文、F005或正式库。保留至Step5收口，用户手动回收，Codex不删除。首批准确子路径为`tmp`、`feasibility-01/http-separated-on`（business.sqlite3、control.sqlite3、observability.sqlite3及各-wal/-shm）和`feasibility-01/summary.json`。本地HTTP仅127.0.0.1随机端口，启动报告、结束关闭。既有解释器与已授权缓存复用，不新建venv/安装依赖；后续子路径创建前另行报告。先区分有写入WAL/FULL commit和空事务、初始化和稳态，不能把累计profiling时间当作物理p95下界。P1仍开放。

状态：`step_5_diagnostic_complete / awaiting_remaining_performance_plan`，性能 P1 仍开放。

## 诊断先行历史收口（2026-08-27 14:48 +08，已被V4取代）

已完成分库/分操作稳态profiling、独立HTTP客户端进程对照和有证据的预算SQL最小优化。仅本轮改动：`backend/src/cyber_town/infrastructure/control/sqlite_control.py`、`backend/tests/test_budget_control_step3.py`，新增`scripts/f009_step5_steady_profile.py`、`backend/tests/test_steady_profile_step5.py`。原72个未提交文件中其余70个SHA256不变，全部10份migration（含两份0004）不变；无业务/API/Godot改动。功能32tracked modified+42untracked，正式仍main五文档，两处HEAD/本地origin/main为1a4fc2c。未提交、推送、PR、部署或清理。

### 根因证据与有界修复

- 同工作量内存对照每组1000execution：原预算预留每次8次attempt窗口+4次cost窗口聚合。开启recorder组最后100次，窗口聚合211.954ms/预算预留234.895ms，约90%；不是recorder独有问题。
- 最小优化只在原BEGIN IMMEDIATE事务内按四scope惰性合并1h/24h计数与24h成本，12→4条聚合；不增加跨请求缓存/计数表/索引，不改严格`>`窗口、released排除、reserved/dispatched预留、settled实际成本、拒绝优先级、warning/commit语义。优化后最后100次窗口聚合133.716ms、预算预留153.754ms；这是带profiling的定位证据，不是最终性能收益承诺。
- 真实HTTP稳态100execution，control-on每轮900control commit、2000observability commit、100business commit；各100open/1300progress/100finish，提交次数前后不变。基线独立客户端组observability路径校验约6132ms、三库commit累计约9525ms；方法inclusive数据不可与嵌套SQL耗时相加。剩余HTTP热点是每次路径检查和同步持久化，不是预算聚合本身。
- 客户端分离后仍慢，不能以同事件循环测量干扰撤销旧门禁。新诊断不含初始化于稳态，独立子进程逐请求测量；吞吐包含父子进程协调开销。各组单轮，未作为warm-up+5-run最终验收。

| 带profiling诊断 | 基线p95/p99 ms | 查询优化后p95/p99 ms | 冻结阈值 |
| --- | --- | --- | --- |
| in-memory+control | 3.8597 /4.7574 | 3.1644 /3.9020 | 2 /5，p95仍超限 |
| 同进程HTTP control-on | 797.5076 /899.5344 | 752.0218 /1115.7164 | 250 /400，仍超限 |
| 独立客户端HTTP control-on | 682.9391 /1043.7379 | 627.1403 /724.9823 | 250 /400，仍超限 |

**停止扩展修复。** 本轮没有改路径校验、同步强度或异步架构，没有降低阈值。旧核心五项失败仍未解除；完整warm-up+5-run矩阵、真实长期记忆写入场景、evaluator/三进程digest/故障组合和最终全量质量仍未完成。P1、Step5、R10不关闭，不进入Step6。

### 验证与诊断工具问题

- 诊断模块缺失红测成立；初版10passed。首次诊断因内存组父目录未创建被既有边界拒绝，仅留下空baseline；新增回归1failed/10passed，修正脚本后含2请求独立HTTP冒烟的12passed。该问题属于新诊断脚本，不是产品缺陷。空目录保留、不删除，正式对照改用baseline-02。
- 查询红测25failed：原聚合数12而非4、新helper未实现；实现后25passed。预算、限流、SQLite control、Dialogue control、retry/取消、连接、性能契约与诊断联合asyncio回归132passed，命令显式anyio插件、`-k 'not trio'`。不冒称全仓质量门禁。
- 最终四个变更Python文件ruff、format、mypy通过。首次mypy遗漏MYPYPATH、后续诊断测试隐式模块导出错误均修正调用/测试导入，不改产品语义。tracked diff及42untracked no-index检查通过；no-index的exit1表示相对空文件存在内容，不是whitespace失败。
- 本轮新建8组HTTP三库只读收口（确认WAL为0后immutable读取）：各100completed/fake、1400stage、100dispatch、100relationship event；control-on各100settlement/300cost/200retry event，off对应0；24库integrity/FK检查全过，异常stage集合/非零成本均0。没有读取旧证据库。
- 本轮18个control/observability/JSON surface、8项原文/key sentinel命中0，仅声明该检查覆盖范围，不替代完整隐私/隔离QA。两目录正式三类DB均不存在，8000及8个诊断端口全部释放；无新增venv/pytest cache/bytecode。
- 证据：`performance-v3-diagnostic/baseline-02/summary.json` SHA256 `7564ace36044dfec8a392e7825f75eae5918daba841ae3bbfb91b268adfad4e0`；`after-query/summary.json` SHA256 `e03f678f533ed7b7b99903ee9da930345d05c477cae6f9b79a52ba33fa63a99b`。两轮总4800诊断execution，不含专项/联合测试。

### 临时资源台账与手动处置

新根准确路径`E:\Agent\cyber-town-f009-step5-tests\performance-v3-diagnostic`，创建2026-08-27T14:30:37.9797095+08:00；责任F009 Step5 P1；诊断结束，保留至Step5收口。当前178files/115dirs/22407848bytes（116synthetic SQLite、30WAL、30SHM、2metadata JSON），无reparse/hidden/read-only/.env-like/嵌套Git，位于Git仓库外，tracked/untracked/ignored不适用。

以下子路径均位于该精确根下，创建前已向用户报告；不重复求和父子资源：

| 子路径 | 创建时间（2026-08-27 +08） | files /dirs /bytes | 建议 |
| --- | --- | --- | --- |
| baseline | 14:34:10 | 0/0/0 | 失败启动空目录，保留或用户手动删除 |
| baseline-02 | 14:35:32 | 37/6/4383474 | 修复前证据，保留 |
| after-query | 14:41:54 | 37/6/4364183 | 修复后证据，保留 |
| pytest-harness-02 | 14:34:44 | 0/1/0 | 红测空目录，保留 |
| pytest-harness-03 | 14:35:17 | 9/4/552960 | 诊断冒烟SQLite，保留至收口 |
| pytest-query-red-01 | 14:39:09 | 1/1/147456 | 查询红测，保留至收口 |
| pytest-query-green-01 | 14:39:56 | 1/1/147456 | 查询绿测，保留至收口 |
| pytest-regression-01 | 14:41:03 | 93/87/12812319 | 联合回归，保留至收口 |
| tmp | 14:30:37 | 0/0/0 | TEMP/TMP空目录，保留 |

预告的pytest-red-01/pytest-green-01未实际创建（原测试不需要tmp_path）。Step5整个父根当前870files/565dirs/147247255bytes，旧资源未删除或复用。功能缓存root .ruff_cache=5files/6682bytes，root .mypy_cache=3/38301925，backend/.mypy_cache=4/34480371，game/.godot=6/3079；均为既有ignored资源，保留。活动worktree/分支不得手动递归删除。

推荐现在保留两份诊断摘要及其数据库，后续修订仍需要；收口后用户可在再次核对路径/占用/reparse/盘点后手动执行：`Remove-Item -LiteralPath 'E:\Agent\cyber-town-f009-step5-tests\performance-v3-diagnostic' -Recurse`。仅删除该诊断子根，不删父测试根、worktree或缓存；将移除上述全部synthetic SQLite/sidecar/JSON和测试产物，不能从Git恢复。Codex未执行且不会代执行。若现在只希望去掉空baseline，可手动执行`Remove-Item -LiteralPath 'E:\Agent\cyber-town-f009-step5-tests\performance-v3-diagnostic\baseline'`。

### 下一步边界

建议另行批准剩余性能方案：优先研究逐次路径检查中重复系统调用的等价去重，仍每次检查canonical边界、所有祖先reparse和文件身份；禁止缓存安全判断、跳过检查或降低持久化。内存组剩余窗口聚合仍需给出有依据方案。先明确精确文件、失败优先对抗/并发验证和新子路径，再实施；若需要异步架构或业务库连接改造，单独申请。此前不再试索引/存储编码，不重跑已知不足的完整矩阵，不承诺现有阈值一定可达。

## 诊断先行续修授权（2026-08-27 14:29 +08，历史授权快照）

用户确认诊断先行范围及新临时子路径，允许profiling或有证据支持的最小修复。先分库/分操作、区分初始化与稳态，再用独立HTTP客户端进程对照同事件循环客户端。旧性能失败仍有效，不以诊断样本替代warm-up+5-run最终门禁。预算窗口重复查询为待证假设，仅证实后才做原事务内等价聚合优化；不扩大业务仓储连接/异步架构，不改migration、14-stage持久化、同步强度、业务/API/Godot或阈值。越界即停，P1/Step5不关闭，Step6未授权。

预检两处HEAD/origin/main=1a4fc2c，正式main五文档、功能指定分支32tracked+40untracked。72文件及10份SQL指纹内存留存。新根不存在、父边界无reparse；仅使用正式目录既有Python3.12，不建venv/安装依赖。

资源：`E:\Agent\cyber-town-f009-step5-tests\performance-v3-diagnostic`，责任F009 Step5 P1，状态批准待创建，登记2026-08-27T14:29:37+08:00，保留至Step5收口，由用户手动回收。子路径：`tmp`，`pytest-red-01`、`pytest-green-01`（不复用）；`baseline/memory-off`、`baseline/memory-on`（仅内存SQLite，不创建DB文件）；`baseline/http-colocated-off`、`baseline/http-colocated-on`、`baseline/http-separated-off`、`baseline/http-separated-on`（每个仅business/control/observability.sqlite3及各-wal/-shm）；`baseline/summary.json`。仅synthetic/FakeProvider/metadata，无.env/真实秘密/真实原文/F005；不输出HTTP payload或异常详情。服务仅127.0.0.1系统分配端口，启动报告实际端口并结束关闭，客户端子进程隐藏。旧证据不连接/覆盖/复用/删除。缓存仅复用已授权位置，pytest禁用cache/bytecode；新子路径创建前报告。台账同步evidence，Codex不删除。

来源：roadmap `R-10`。Step 0—4 已完成。用户明确批准候选 C 物理编码例外后，synthetic 空间/语义预验证通过（232/420/652 KiB）；已追加两份产品0004并实施有界连接复用，未修改旧migration、业务/API/Godot或阈值。核心warm-up+5-run性能门禁仍失败：完整HTTP control-on p95/p99为787.5748/853.159ms，in-memory+control为5.0921/7.1039ms，另有control-on相对p95超限。已按“失败立即停止”停止；完整矩阵余下场景、evaluator、三进程digest、故障组合及最终综合回归未运行。P1/Step5/R10未完成，等待修订性能方案；不进入Step6。

## 用户价值与目标

在不改变现有三 NPC 对话体验和状态隔离语义的前提下，为 Dialogue v1 增加可验证的输入防护、限流、预算、有限重试、超时与熔断治理，并以 F-008 的 metadata-only 可观测性建立性能回归基线。目标是使恶意输入、异常 provider、并发放大、重复计费和资源耗尽均能被确定性拒绝、归属和验证，同时保持隐私边界与 fake-only 可重复性。

## 当前基线与必须保持的不变量

- 基线为 F-008 交付后的 `main / origin/main`：`1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3`；Step 0 已完成只读复核。
- 固定 persona 保持为 `neon_guide / Nia`、`signal_archivist / Ivo`、`night_courier / Rhea`。
- 短期状态严格使用 `player_id + npc_id + conversation_id`；长期记忆与关系严格使用 `player_id + npc_id`。
- Dialogue v1、既有 JSON Schema、业务 migration `0001_long_term_memory.sql` / `0002_relationship_state.sql` 默认保持不变。
- 复用 F-008 的 `trace_id`、`request_id`、`execution_id`、HMAC scope tag、14-stage metadata-only 链路、只读 CLI 和 synthetic fixture-only replay 边界。
- 不记录原始对话、system prompt、记忆正文、原始关系 suggestion、provider body、原始 scope 或秘密。
- 不读取、修改或复用 F-005 验收数据库、调用台账和预算。
- F-008 worktree、分支及缓存继续保留，不复用为 F-009 资源，不在本任务卡起草阶段清理。

## 威胁模型

### 受保护资产

- persona 身份、system prompt 和策略边界；
- player/NPC/conversation 的短期、长期和关系 scope；
- provider dispatch、execution 归属和可用容量；
- 成本/预算记账、幂等状态与业务 SQLite 一致性；
- F-008 trace、评估和 replay metadata 的完整性与隐私；
- Dialogue v1 的兼容性以及 Godot 当前可恢复的 loading/error/retry 体验。

### 攻击者与异常来源

- 构造恶意 Dialogue JSON 的客户端；
- 利用 Unicode、路径、大小写、空白、重复 member、深层嵌套或超大 payload 绕过验证的输入；
- prompt injection、persona 越权、system prompt 探测、长期记忆投毒、恶意关系 suggestion；
- 非法或异常 provider 响应，包括 tool call、reasoning content、非预期字段和 finish reason；
- retry、replay、concurrent waiter、取消、迟到结果、orphan、重启造成的放大或错误归属；
- recorder、限流器、预算仓储或 breaker 自身故障。

### 信任边界与总原则

- Godot 和所有外部 JSON 均不可信；FastAPI 入口先做语法、大小和结构边界，再进入领域解析。
- provider 输出均不可信；必须在记忆、关系和响应映射前通过严格 allowlist 验证。
- identifier 不做会改变身份的“自动修复”或宽松归一化；非法值稳定 fail-closed。
- 所有拒绝必须发生在 provider dispatch、记忆写入和关系写入之前；错误不得回显或记录原始恶意 payload。
- 同一实际 `execution_id` 是 dispatch、retry、成本、限流和状态写入归属的核心单位；waiter/replay 不得制造新 execution。

## 1. 安全输入与边界防护

### Dialogue 请求与身份字段

- 为请求体定义严格字节上限、JSON 深度、集合长度、字符串长度和字段 allowlist；拒绝重复 JSON member、额外字段、非 UTF-8、非法数值和错误类型。
- 对 `player_id`、`npc_id`、`conversation_id`、`request_id` 分别锁定类型、长度和字符策略；拒绝控制字符、双向文本控制、路径分隔符、点路径、首尾空白、大小写变体和混淆性同形字。
- `npc_id` 必须严格命中现有 registry allowlist；未知或变体 ID 沿用安全错误路径。
- validation failure 不生成未经验证的 scope tag，不进入 provider、短期/长期记忆或关系写入。

### Prompt、persona、记忆与关系

- 建立固定 synthetic 攻击集，覆盖忽略指令、角色替换、system prompt 探测、数据外泄诱导、跨 NPC/player/conversation 注入。
- 用户消息只能作为不可信 user content；不得改变 persona version、system role、scope 或工具权限。
- 长期记忆候选必须继续通过既有结构化、确定性规则；拒绝指令型、越权型、跨 scope 或超限内容。
- 关系 suggestion 继续是受限分类建议；非法类别、置信度、幅度、scope 或附加字段不得改变关系状态。

### Provider 输出

- 只接受明确版本和字段 allowlist；拒绝 tool call、reasoning content、unexpected finish reason、未知字段、类型错误、超限文本和 scope/identity 回传企图。
- 区分可安全降级、可重试的暂时性错误与必须立即拒绝的协议/内容错误。
- 稳定 error/reason code 只记录类别和 metadata，不保存异常详情或 provider body。

## 2. 限流与并发治理候选契约

### 候选 scope

| Scope | 目的 | Step 0 结论 |
| --- | --- | --- |
| 全局 | 防止整体 provider 容量耗尽 | 启用 ingress token bucket 与全局并发上限，数值见锁定决策 C |
| player | 限制单玩家总体消耗 | 需要明确匿名/轮换 player 的规避风险 |
| player + npc | 防止单角色热点并保持跨 NPC 并发 | 与关系/长期 scope 一致，建议作为核心候选 |
| conversation | 限制单会话突发和同 scope 串行 | conversation 轮换可能绕过，不能单独依赖 |
| IP / 客户端 | 入口防滥用的补充边界 | 只使用 direct socket peer；忽略所有 forwarded header |

### 候选算法

- 固定窗口：实现简单但有窗口边界突发；仅作为对照方案。
- 滑动窗口：公平性较好但状态和 SQLite 成本更高。
- token bucket：允许受控突发、支持稳定 refill，已选定为实施算法；容量、补充率和持久化策略见锁定决策 C/E。

### 归属不变量

- 正常新 execution 在 dispatch 前只消费一次额度；实际未创建 execution 的 validation failure、replay 和 conflict 不消费 provider 额度。
- concurrent waiter 只关联已有 execution，不重复限流、dispatch、计费或业务写入。
- retry 属于同一 execution；可以记录尝试次数，但不能当作新用户请求重复扣除请求级额度。
- 跨 NPC 可并发；同一受保护 scope 维持既有串行和幂等规则。
- 限流决定、lease/permit 和释放必须可在取消、迟到、异常、orphan 与重启场景下确定性收口。

## 3. 成本与预算控制候选契约

### metadata 与归属

- 记录输入字符、上下文预算、prompt/completion/total token、provider dispatch、attempt、execution 和 metadata-only cost。
- fake/local/disabled provider 的 token 成本和货币成本固定为 `0`；不得用 synthetic 值冒充真实账单。
- replay、waiter、冲突、取消后的迟到结果不得重复记账；预算记账必须与实际 provider execution 归属 100% 一致。

### 候选预算维度

- per request / execution hard cap；
- per player 时间窗预算；
- per player + NPC 或 NPC 时间窗预算；
- 全局时间窗预算及并发容量；
- soft warning、hard reject 和安全降级三种候选语义。

具体额度、币种精度、时间窗、预留/结算方式和降级语义已在锁定决策 D/H 中冻结。

### 存储候选

- 候选 A：仅进程内 token bucket 与 synthetic budget ledger，适合先验证状态机，但重启后不保留。
- 候选 B：新增独立、默认关闭的控制数据库 `data/cyber-town-control.sqlite3`，使用独立候选 migration `backend/src/cyber_town/infrastructure/control/migrations/0001_safety_cost_control.sql`，保存 metadata-only 限流/预算/breaker 状态。
- 候选 C：在 F-008 observability 数据库追加控制表；耦合审计与控制职责，默认不推荐。

Step 0 已选定候选 B；本阶段仍不创建数据库或 migration，不修改业务 `0001/0002`，不复用 F-005 资源。

## 4. Retry、timeout 与 circuit breaker

### Retry / timeout

- 仅对明确标记的 timeout/unavailable 且尚未产生不可逆业务提交的 provider 尝试有限重试。
- validation failure、未知 NPC、request_id conflict、内容安全拒绝、非法 provider 响应和预算/限流拒绝不得自动重试。
- 最大 attempt、单次 timeout、总 execution deadline、退避、jitter 和取消传播规则已在锁定决策 F 中冻结。
- clock、随机 jitter 和 sleeper 必须可注入，保证 fake-only 测试和三进程 digest 可重复。
- waiter 共享已有 execution 及其最终结果，不能放大 provider 调用。

### Circuit breaker

- 状态固定为 `closed / open / half_open`；转换由稳定 reason code、阈值和注入时钟驱动。
- scope 候选为 provider kind、provider instance 或全局；不得按原始 player/scope 泄露身份。
- `open` 时在 dispatch 前快速失败或进入已批准降级；`half_open` 只允许有限 probe execution。
- 重启后的状态恢复、orphan attempt、迟到结果和旧 generation 不得错误关闭 breaker 或写入相邻 scope。

### 组件故障语义候选

| 组件 | 候选原则 | Step 0 结论 |
| --- | --- | --- |
| recorder | 继续不改变 Dialogue 成功/错误及业务写入 | 默认 fail-open，仅丢失 metadata |
| 限流器 | 防资源耗尽与可用性之间取舍 | fail-closed |
| 预算仓储 | 不允许失去预算边界后继续真实 dispatch | 默认建议 fail-closed |
| breaker store | 不得因故障造成 retry amplification | fail-closed |

## 5. 性能优化与回归基线

复用 F-008 已建立的 metadata-only 基线作为候选参照，不将其视为生产 SLA：

| Recorder | p50 | p95 | p99 | 吞吐 | SQLite 增长 |
| --- | ---: | ---: | ---: | ---: | ---: |
| no-recorder | 0.003 ms | 0.005 ms | 0.015 ms | 275,988.928/s | 0 bytes |
| SQLite recorder | 100.763 ms | 111.243 ms | 116.297 ms | 9.938 trace/s | 172,032 bytes |

Step 0 已只读核对基线测量口径，并为以下矩阵冻结回归阈值；数值见锁定决策 J：

- no-recorder、in-memory recorder、SQLite recorder；
- 单 scope 串行、跨 NPC 并发、concurrent waiter、replay；
- retry、circuit-open、半开 probe、取消和重启恢复；
- p50/p95/p99、吞吐、provider dispatch 放大系数、控制/observability SQLite 增长。

不得进行生产压测、访问外部模型服务或把本机 fake-only 数据声明为生产容量。

## 6. F-008 observability 集成边界

- 复用既有 trace/request/execution 关联、HMAC scope tag 和 14-stage 链路，不复制原始 scope。
- 规划固定 enum/outcome/reason code：`rate_limit_outcome`、`budget_outcome`、`retry_outcome`、`breaker_state/outcome`、attempt/count/cost/limit metadata。
- 保持字段 allowlist；禁止 message、reply、system prompt、history、记忆正文、原始 suggestion、provider body、异常详情、原始 scope 和秘密。
- 已锁定 append-only `observability/0002_safety_cost_performance.sql`；不得改写 `observability/0001_observability.sql`。
- 真实 metadata trace 继续不可执行；只有仓库内版本化 synthetic fixture 可按已知 `case_id` replay。

## 7. API 与 Godot 最低可见契约

- 首选保持 Dialogue v1 和 JSON Schema 不变，用现有错误映射表达安全降级。
- 已锁定 HTTP `413/429/502/503`、受限 `Retry-After` 和稳定限流/预算/熔断错误码；成功响应字段不扩展，细节见锁定决策 H。
- Godot 优先复用现有 loading、error、retry 和 trace 展示；不增加正式安全、预算或监控 UI。
- 若必须新增最小提示，先提交 640×400 低保真文本契约，用户确认后才允许后续 Step 实现。

## 8. Fake-only 评估与对抗框架

- 三个固定 persona 的身份/version/system prompt 归属与 Nia 兼容性。
- 短期三元 scope、长期/关系双元 scope 的跨 player/NPC/conversation 隔离。
- prompt injection、persona 越权、system prompt 探测、scope 篡改、记忆投毒和恶意 suggestion。
- rate-limit 与 budget 的性质测试、窗口/令牌状态机、绕过和边界竞争。
- retry/timeout/breaker 的状态转换、attempt 上限、取消传播、waiter 共享和放大系数。
- replay、冲突、并发、迟到、orphan、旧 generation、重启与 synthetic replay。
- recorder、限流器、预算仓储和 breaker store 的故障注入及业务不变量。
- 固定 synthetic fixture、稳定 failure code、冻结阈值和至少三个全新 Python 进程中的 canonical digest 一致性。
- FakeProvider 仅验证工程控制与确定性行为，不能冒充真实模型的安全性或回复质量结论。

## Step 0—7 阶段地图

| Step | 目标 | 完成门禁 |
| --- | --- | --- |
| 0 | 只读锁定威胁、identifier/JSON 边界、scope、算法、阈值、存储、API、故障和隐私决策 | **已完成**；基线与实现证据只读核对，决策见下文；未创建分支、资源或实现 |
| 1 | 失败优先建立严格安全验证、provider 响应防火墙和固定 enum/error code | **已完成**；对抗输入在 dispatch/write 前 fail-closed，限制性 v1/schema 变更和 Godot 错误映射已验证 |
| 2 | 实现限流与并发治理 | **已完成**；无绕过、无重复 dispatch/permit，waiter/replay 归属正确，测试根已由用户手动删除并只读复核 |
| 3 | 实现预算、预留/结算与成本控制 | **已完成**；execution 记账一致；fake/local/disabled 成本为 0；无重复计费 |
| 4 | 实现 timeout、有限 retry、取消传播和 circuit breaker | **已完成**；无 retry amplification；breaker 转换 100% 一致 |
| 5 | 性能基线、综合对抗、三进程评估和组件故障注入 | **已完成**；以V33最终收口为准，旧失败行完整保存在evidence历史原文；不替代Step6验证 |
| 6 | 独立 fake-only QA | **阻塞、未完成**；预算修复和v8断言同步通过，当前S6-QA-002原生资源登记边界待解决；完整quality/唯一1+5性能未收口 |
| 7 | 用户本地 UAT、最终门禁和 Git 交付准备 | **未授权、未开始**；Step6全部阻塞门禁通过后另行申请 |

任何 Step 只在用户单独授权后进入；Step 完成不自动进入下一 Step，不自动提交、推送、创建 PR、合并或部署。

## 候选验收标准

| 指标 | 候选标准 |
| --- | ---: |
| 未授权 provider dispatch | 0 |
| scope 泄漏 | 0 |
| 禁止原文记录/回显 | 0 |
| 重复计费 | 0 |
| 重复业务状态写入 | 0 |
| rate-limit 绕过 | 0 |
| retry amplification | 0 |
| breaker 状态转换一致性 | 100% |
| 预算记账与 provider execution 归属一致性 | 100% |
| 固定评估 case verdict 与三进程 digest | 100% 可重复 |
| fake/local/disabled 非零成本 | 0 |
| 性能回归 | 不超过 Step 0 冻结阈值 |
| 工程门禁 | ruff、format、mypy、schema、Godot、全部 loopback、fake-only quality、ignore/sensitive、CI 全绿 |

## 明确非目标

- 不做 NPC 自主行为、NPC 间互动或社交图谱。
- 不做正式游戏 UI、美术、部署、生产配置或生产压测。
- 不引入云 telemetry、第三方 SaaS、Qdrant 或新外部数据库。
- 不调用真实模型进行自动红队、评价或性能测试。
- 不修改或复用 F-005 验收数据库、调用台账和预算。
- 不把 R-11 游戏 UI 或 R-12 最终演示提前混入 F-009。
- 不自动清理或复用 F-008 worktree、分支、缓存和历史资源。

## 持续安全与隐私边界

- 不读取 `.env`，不调用真实模型或访问外部模型服务。
- 所有验证使用 FakeProvider、synthetic fixture、synthetic HMAC key、metadata-only 结果和隔离临时 SQLite。
- 不保存或输出原始 prompt/reply/system prompt、记忆正文、关系 suggestion、provider body、原始 scope、密钥、token、cookie 或异常详情。
- 不创建或使用正式 `data/cyber-town.sqlite3`、`data/cyber-town-observability.sqlite3` 或候选 `data/cyber-town-control.sqlite3` 进行自动验证。
- Codex 不执行临时资源删除；只盘点并给出用户手动处理建议，用户删除后仅做只读复核。

## 候选临时资源规划

以下为全阶段资源规划。Step 1—3 测试根已由用户手动回收；Step 4 根当前不存在，不推断删除主体。Step 5 根已创建并用于性能调查；Step 6—7 路径未创建。后续路径必须在对应授权后登记，若工具需要其他路径，必须先报告并取得授权。

| 候选绝对路径 | 用途与内容类别 | 敏感性 | 保留期限 | 用户手动回收方式 |
| --- | --- | --- | --- | --- |
| `E:\Agent\comprehensive-cases\15-cyber-town-f009` | F-009 功能 worktree、源码、测试与 ignored 缓存 | 不得含真实秘密、payload、正式/F-005 SQLite | Git 交付完成且另行审计前 | 审计干净状态后，用户从正式仓库执行普通 `git worktree remove E:\Agent\comprehensive-cases\15-cyber-town-f009`；不得 `--force` |
| `E:\Agent\cyber-town-f009-step1-tests` | 安全验证 synthetic payload、pytest tmp、隔离业务 SQLite | 只含人工 synthetic 攻击字符串，不含真实数据 | 已回收；Step 2 预检及当前复核均确认不存在 | 不得重建或复用 |
| `E:\Agent\cyber-town-f009-step2-tests` | 限流/并发 fake clock、状态与隔离 SQLite；创建于 `2026-08-26T21:23:40.6534472+08:00` | metadata-only / synthetic；曾误生成 80 个 observability SQLite/WAL/SHM surface，违反本 Step 资源类别限制但无真实数据/秘密 | Step 2 收口时已由用户手动删除，Codex 只读确认不存在 | 已回收；不得重建或复用 |
| `E:\Agent\cyber-town-f009-step3-tests` | 预算 ledger、成本、隔离控制/业务 SQLite 与 append-only observability `0002` 所需 metadata-only SQLite；创建于 `2026-08-26T22:13:13.4358635+08:00`；终盘 1,673 files/2,211 dirs/161,147,765 bytes | metadata-only / synthetic；1,556 SQLite、45 WAL、45 SHM、27 JSON；0 `.env*`、真实秘密、reparse、nested Git、hidden 或 read-only | 已由用户手动删除；Step 4 预检只读确认不存在 | 已回收；不得重建或复用 |
| `E:\Agent\comprehensive-cases\15-cyber-town-f009\.venv` | `uv run --no-sync` 解释器探测曾误创建的空虚拟环境外壳 | 未运行 pytest、未含项目 payload/SQLite/`.env`/秘密；不属于 Step 3 授权资源类别 | 已由用户手动删除，Codex 只读复核确认不存在 | 已回收；不得重建。后续测试只复用正式目录既有 Python 3.12 环境 |
| `E:\Agent\cyber-town-f009-step4-tests` | retry/breaker fake time、故障注入和隔离 SQLite；创建于 `2026-08-26T23:46:40.7756150+08:00`；终盘 1,269 files/1,738 dirs/145,773,129 bytes | metadata-only / synthetic；1,203 SQLite、24 WAL、24 SHM、18 JSON；0 `.env*`、reparse、nested Git、hidden、read-only，control/observability sentinel 命中 0 | Step 4 已完成；当前路径不存在，未推断删除主体 | 已回收；不得重建或复用 |
| `E:\Agent\cyber-town-f009-step5-tests` | 性能、综合对抗、三进程输出和隔离 SQLite；创建于 `2026-08-27T00:32:05.5555323+08:00` | metadata-only / synthetic；不得含 payload、`.env`、真实秘密、nested Git 或新虚拟环境 | Step 5 完成 | 完成后由 Codex 盘点并建议用户手动删除精确目录；Codex 不删除 |
| `E:\Agent\cyber-town-f009-qa` | 独立 QA 的 synthetic tmp、隔离 SQLite、报告摘要 | metadata-only / synthetic | Step 6 完成 | 同上 |
| `E:\Agent\cyber-town-f009-uat` | 用户本地 fake-only UAT 的隔离 SQLite 与摘要 | metadata-only / synthetic | Step 7 完成 | 同上 |

每次收口必须报告准确路径、文件/目录数、字节数、resource category、reparse 状态、tracked/untracked/ignored、嵌套 Git、到期状态、影响范围和不可恢复性；不得自动删除。

## Step 0 基线证据

- 正式目录只读核对为 `main == origin/main == 1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3`；Step 0 开始时唯一差异为本任务卡。
- F-008 功能 worktree 仍注册在 `E:\Agent\comprehensive-cases\15-cyber-town-f008`，功能分支、文档分支及 `.ruff_cache`、`.mypy_cache`、`.pytest_cache`、`game/.godot` 均保持存在，未清理、移动或复用。
- Dialogue v1 当前为严格 Pydantic 模型、五个固定请求字段、message `1..1000` 字符、identifier `1..64`、额外字段拒绝；HTTP adapter 已拒绝重复 JSON member，但会在没有字节/深度门禁的情况下完整读取请求体。
- 当前 player identifier 会 strip、UUID pattern 接受大小写十六进制；这些行为不足以满足身份不可归一化和大小写 fail-closed 要求。
- provider adapter 已禁用 SDK retry、thinking 和 stream；应用已拒绝非单 choice、tool call、reasoning content、未知 finish reason、超长/空 reply，但 DeepSeek JSON envelope 尚未拒绝重复 member，非法 provider response 当前仍被标记为可重试。
- 当前应用已有全局 provider semaphore `2`、三元 conversation lock、request idempotency/replay/waiter/cancel/orphan 归属；尚无限流、预算、自动 retry 或 breaker。
- F-008 trace 固定 14 stage，`trace_id/request_id/execution_id` 和 HMAC scope tag 已可用；observability `0001` 明确约束 `cost_micro_usd = 0`，因此 F-009 只能通过追加式存储扩展，不能改写既有表。
- F-008 性能证据是单机各 30 个 fake-only trace 的测量基线，不是生产 SLA：no-recorder `0.003/0.005/0.015 ms`、`275,988.928/s`、0 bytes；SQLite recorder `100.763/111.243/116.297 ms`、`9.938/s`、172,032 bytes。

## Step 0 锁定决策

### A. HTTP、JSON 与 identifier 边界

| 项目 | 锁定值 |
| --- | --- |
| Content-Type | 仅 `application/json`，允许标准参数；`Content-Encoding` 仅允许缺失或 `identity` |
| 原始 body | 最大 `8,192 bytes`，在完整 materialize 和 JSON decode 前流式计数；超过立即 `413` |
| JSON 结构 | UTF-8；根必须为 object；最多 4 层 container nesting、最多 16 个 object member/array item 的预解析上限；最终仍必须精确五个唯一 member |
| JSON 特殊值 | 拒绝重复 member、NaN、Infinity、无效 surrogate、非 UTF-8 和 trailing data |
| `player_id` | 原始值 `1..64`；小写 ASCII；正则 `^[a-z0-9](?:[a-z0-9_-]{0,62}[a-z0-9])?$`；不得 trim/normalize |
| `npc_id` | 原始值必须精确等于 `neon_guide`、`signal_archivist` 或 `night_courier`；不得 trim、casefold 或 Unicode normalize |
| `request_id` / `conversation_id` | 恰好 36 字符的小写 canonical UUID `8-4-4-4-12`；不限制 UUID version，但禁止大写、braces、URN 和非 canonical 形式 |
| `message` | 原始值 `1..1000` Unicode scalar 且 UTF-8 最大 4,000 bytes；不得仅为空白或带首尾空白；允许内部 LF/TAB，拒绝 CR、其他 C0/C1、DEL、Unicode `Cf/Cs`、bidi override/isolate 和无效 scalar |

身份字段拒绝所有 Unicode、同形字、路径分隔符、`.`/`..`、控制字符和大小写变体；绝不通过“修复后接受”改变 scope。message 不做有损归一化；安全检测可在内存中对 inspection copy 做 NFKC + casefold，但不得记录该副本。

### B. Prompt injection、记忆投毒与 provider 防火墙

- 固定策略版本为 `f-009-input-policy-v1`。结构/身份攻击始终 pre-dispatch fail-closed；语义策略以仓库内 synthetic 高置信规则集识别直接角色替换、system/developer prompt 探测、秘密提取、跨 scope 指令、工具调用诱导和“把记忆当指令”等类别。命中任一高置信规则返回 `unsafe_content`，不调用 provider，不写入状态。
- 普通角色扮演、引用词语或讨论安全概念不得仅因单个关键词被拒绝；规则必须以短语/结构组合为准，并设置固定允许控制 case。F-009 不声称覆盖未知自然语言注入，也不用 FakeProvider 结果冒充真实模型安全性。
- system prompt/persona 继续由不可变 registry 选择；用户 message、短期 history 和长期事实均以不可信 data 进入，不能选择 role、persona version、provider、scope 或控制组件。
- 长期记忆继续只允许现有四个结构化 fact key 和领域校验；任何指令、URL、秘密、跨 scope、未知字段或非法 Unicode 候选均 inert，不得持久化。关系 suggestion 仍须精确二字段、固定五类、整数置信度；任何重复/额外/嵌套/类型或 scope 字段均 inert。
- DeepSeek adapter 必须严格解析唯一 JSON envelope：精确 `reply + relationship`，拒绝重复 member、额外字段和 trailing data。provider/model 必须命中 composition allowlist；choice 必须为 1；tool call/reasoning content 必须不存在；finish reason 仅允许 `stop` 或受控 `content_filter`。
- usage 必须为非负严格整数；prompt tokens 最大 `32,768`、completion tokens 最大配置值 `256`、total 最大 `33,024` 且加和一致。任何越界均为 `provider_invalid_response`，不可自动 retry；已发生 dispatch 的额度按保守结算规则归属，但记忆/关系/短期状态不写入。

### C. 限流算法、scope 与额度归属

采用连续 refill 的 token bucket；固定窗口只保留比较测试，滑动窗口不实施。所有适用 bucket 必须在控制 SQLite 的同一事务内原子检查/消费，任一拒绝不得造成部分扣减。

| Scope | refill | burst | 适用对象 |
| --- | ---: | ---: | --- |
| ingress global | 120 次/分钟 | 30 | 所有 Dialogue HTTP 尝试，包括 validation failure |
| direct peer IP | 60 次/分钟 | 15 | 只信任 socket peer；忽略 `Forwarded` / `X-Forwarded-For` |
| player | 20 次/分钟 | 5 | 通过 validation、persona 与幂等判断后的新 execution admission |
| player + NPC | 10 次/分钟 | 3 | 同上 |
| conversation | 6 次/分钟 | 2 | 同上 |

- validation failure、未知 NPC、conflict 只消费 ingress；cache replay 和 concurrent waiter 只消费 ingress，绝不重复消费领域 bucket。
- 客户端在已失败终态后以同 request ID 手动 retry 会建立新的 execution 并重新消费领域 bucket；同一 execution 内的自动 provider retry 不再次消费领域 bucket。
- 自动 retry 的每次 provider attempt 都计入 dispatch/预算；waiter 只共享已有 execution。
- 达到领域 bucket 后立即 `429 rate_limited`，不排队；`Retry-After` 为补足下一 token 的向上取整秒数，范围 `1..60`。
- 并发上限锁定为：全局 provider execution `2`、同 player `2`、同 player+NPC `1`、同 conversation `1`。跨 NPC 可并发，但不得突破 player/global 上限；既有 conversation scope lock 等待上限保持 `2.0s`。

### D. 预算、成本和结算

| 预算维度 | 1 小时 rolling hard limit | 24 小时 rolling hard limit |
| --- | ---: | ---: |
| player + NPC provider attempts | 15 | 50 |
| player provider attempts | 30 | 100 |
| NPC provider attempts | 120 | 500 |
| global provider attempts | 300 | 1,000 |

- per execution 固定最多 `2` 次 provider attempts；上下文继续使用 UTF-8 工程预算 `8,192 units`，completion cap `256 tokens`。soft warning 为任一预算的 `80%`，只产生 metadata，不改变成功响应；hard limit 在 dispatch 前拒绝。
- 货币使用非负整数 `micro-USD`，所有乘除向上取整。synthetic/fake/local/disabled 的价格和成本恒为 0。
- fake-only 测试使用版本化 synthetic pricing policy；真实 provider 不内置或猜测价格。启用真实 provider 时必须显式注入已批准的版本化价格表和以下 hard cap，否则 composition fail-closed：per execution reserve `2,000`、player+NPC/24h `25,000`、player/24h `50,000`、NPC/24h `250,000`、global/24h `500,000 micro-USD`。
- dispatch 前在同一事务内预留本 attempt 最大成本与 attempt quota；有可信 usage 时结算实际值并释放差额。dispatch 前取消释放预留；dispatch 后 timeout、unavailable、取消或无可信 usage 时保守消耗全部预留，防止用失败绕过预算。
- replay、waiter、validation、conflict、rate/budget/breaker 拒绝均不预留、不结算。迟到结果只能结算原 execution/attempt 一次，不能触发业务写入。
- hard budget 返回 `429 budget_exhausted / retryable=false`，不提供即时 Retry；错误中不披露余额、价格、scope 或窗口明细。

### E. 控制存储与 migration

- 采用独立、默认不在 provider disabled 状态创建的 `data/cyber-town-control.sqlite3`；migration 锁定为 `backend/src/cyber_town/infrastructure/control/migrations/0001_safety_cost_control.sql`。
- 不修改业务 `0001/0002`，不复用 observability SQLite，更不接触 F-005 数据。控制库只保存 schema/policy version、UUID execution/request linkage、HMAC scope/peer tag、bucket 数值、预算预留/结算、breaker state、时间和固定 code；不保存原始 scope、IP、payload、prompt、reply、memory、suggestion、provider body 或秘密。
- 控制库使用 STRICT tables、外键/check、`BEGIN IMMEDIATE`、WAL、`busy_timeout=2.0s`、显式 allowed root 和 reparse 防护。启用 provider 时控制仓储是必需依赖；provider disabled 不创建正式数据库；自动化只注入隔离临时路径。
- bucket 与 breaker 采用按 scope 原位更新；预算 window 聚合更新。execution ownership metadata 保留 7 天或最近 10,000 条，只标记 expired，不自动 DELETE/VACUUM；达到容量且不能安全登记时 fail-closed 并主动报告处置建议。

### F. Retry、timeout 与 circuit breaker

- 每个 execution 最多 `2` 次 provider attempt（initial + 1 retry）；单 attempt timeout `5.0s`，execution 总 deadline `12.0s`。
- 仅 `provider_timeout` 和明确的 `provider_unavailable` 可自动 retry；固定 backoff `200ms`，full jitter `0..200ms`。测试使用注入时钟和固定 jitter；取消必须传播到排队、sleep 和 provider task。
- validation/NPC/conflict/unsafe/rate/budget/circuit/control failure、content filter 与 provider invalid response 均不得自动 retry。attempt 2 前重新检查 deadline、预算和 breaker，但不重复消费领域 rate token。
- breaker scope 为 `provider kind + model`。eligible execution failure 为 timeout、unavailable 或 invalid response；取消、内容过滤和所有 pre-dispatch 拒绝不计失败。
- 同一 scope 在 `60s` 内连续 `5` 个 eligible execution failure 后 open `30s`；到期进入 half-open，最多 1 个并发 probe；连续 2 个 probe success 后 closed，任一 probe failure 立即重新 open `30s`。成功 execution 清零 closed failure streak。
- open 时返回 `503 circuit_open / retryable=true` 和 `Retry-After: 1..30`；重启必须从控制库恢复。orphan、迟到结果和旧 generation 不得改变 breaker。

### G. 组件故障语义

| 组件 | 锁定行为 |
| --- | --- |
| observability recorder | fail-open；不改变 Dialogue 语义、dispatch 或业务写入，只允许丢失 metadata |
| ingress/domain limiter | fail-closed；返回 `503 control_unavailable`，零 provider dispatch/业务写入 |
| budget repository | fail-closed；未能原子预留或结算时不得产生新的 dispatch/业务提交 |
| breaker repository | fail-closed；不得在未知状态下绕过 open 或放大 retry |
| post-dispatch settlement | 业务状态 commit 前必须成功；失败则不提交短期/长期/关系状态，预留保持保守占用 |

`control_unavailable` 为 `retryable=true`，不返回内部 SQLite/exception/path 详情。

### H. Dialogue v1、错误和 Godot

- 成功请求/响应字段和路径保持不变，不新增 response metadata。为安全硬化，request schema 收紧 identifier/UUID/message pattern，并新增稳定错误枚举；这是 v1 的限制性兼容变更，现有 Godot 生成的 lowercase UUID、`local_player` 和三个 NPC 均兼容。
- 新增：`413 payload_too_large / retryable=false`；`429 rate_limited / true`；`429 budget_exhausted / false`；`502 provider_invalid_response / false`；`503 circuit_open / true`；`503 control_unavailable / true`。既有错误保持原语义。
- 仅 `rate_limited`、`circuit_open` 返回整数秒 `Retry-After`；重复/非法该 header 必须 fail-closed。服务端不自动向客户端暴露额度、成本或 breaker 计数。
- Godot 不新增正式 UI、面板或 response 字段；只扩展严格错误 allowlist，复用现有 validation/unavailable/invalid-response/retry/trace 状态。rate/breaker 使用现有 unavailable 文本并在本地计时结束前禁用 Retry；budget 不允许 Retry。若 640×400 需要新增可见文本，必须先提交低保真契约另行确认。

### I. F-008 observability 兼容方案

- 保持 `OBSERVABILITY_SCHEMA_VERSION=1`、14 stage 和 `0001_observability.sql` 不变；新增独立 `SAFETY_CONTROL_SCHEMA_VERSION=1` DTO/enum。
- 追加候选 migration `backend/src/cyber_town/infrastructure/observability/migrations/0002_safety_cost_performance.sql`，仅新增通过 trace/execution 外键关联的 control decision/attempt/cost 表和索引，不 ALTER 既有表，不改变 `trace_runs.cost_micro_usd = 0`。
- 固定 metadata enum 至少包括 rate/budget/retry/breaker outcome、decision point、attempt number、limit class、pricing/policy version 和稳定 error/reason code；真实 DeepSeek 成本只进入 `0002` 新表，fake/local/disabled 为 0。
- 继续复用 F-008 player/NPC/conversation HMAC tag；peer IP 使用单独领域分隔 HMAC tag。validation failure 不生成 scope tag；禁止原文和秘密清单不变。
- control 决策映射到现有 14 stage，不新增第 15 stage：ingress 属于 request validation；domain admission 属于 idempotency resolution 后；attempt/breaker 属于 provider queue/completion。真实 trace 继续不可执行，synthetic fixture-only replay 不变。

### J. Fake-only 性能门禁

F-008 的 30-sample 数值仅作历史参照。F-009 Step 5 采用同机、固定 fixture、注入时钟之外的真实性能计时；每组至少 1 次 warm-up 后 5 个独立 run，no/in-memory 每 run 1,000 trace，SQLite 每 run 100 trace，报告五次 run 的中位 p50/p95/p99、吞吐和增长。

| 场景 | 冻结阈值 |
| --- | --- |
| no-recorder metadata | p95 `<=0.050ms`，p99 `<=0.100ms` |
| in-memory recorder + control | p95 `<=2ms`，p99 `<=5ms`，吞吐不低于同轮 no-recorder 的 `80%` |
| SQLite observability recorder | p95 `<=150ms`，p99 `<=200ms`，吞吐 `>=8 trace/s` |
| SQLite pre-dispatch rate/budget/breaker reject | p95 `<=50ms`，provider dispatch 为 0 |
| 完整 FakeProvider + 业务/control/observability SQLite loopback | 排除注入等待后 p95 `<=250ms`，p99 `<=400ms`，concurrency=2 时 `>=4 completed execution/s` |
| fresh observability DB 增长 | 每 100 trace `<=512 KiB` |
| fresh control DB 增长 | 每 100 unique execution `<=256 KiB` |
| 两库合计增长 | 每 100 unique execution/trace `<=768 KiB` |

同一机器上的 F-009 control-on 相对 control-off p95 回归还必须不超过 `max(20%, 30ms)`；rate/budget/circuit-open 的 provider dispatch amplification 为 0，正常 execution 最大 2 attempts，replay/waiter 为 0。任一绝对或相对阈值失败即门禁失败，不把本机结果声明为生产容量。

## Step 0 冲突与剩余风险

- 严格 lowercase UUID、ASCII player ID、message 控制字符和新增错误码会收紧已发布 v1 的接受集合；现有 Godot 兼容，但第三方客户端需按更新后的 schema 迁移。这是经 Step 0 接受的安全型限制性变更，不是字段形状变更。
- 语义 prompt injection 规则只能覆盖固定高置信模式，存在漏报和误报；必须以可解释 code、允许控制样例和 fake-only 声明约束结论。
- 真实 provider 定价可能变化；F-009 不访问外部服务验证价格。真实 provider 未显式注入批准价格表时必须 fail-closed，因此真实对话恢复需要未来单独的本地验收授权和价格配置。
- 独立 control SQLite 增加第二个控制事务边界；Step 3—5 必须重点验证业务 SQLite、控制 SQLite 和 observability SQLite 之间无“已写业务但未结算”的不一致。
- F-008 性能样本量小且来自单机；冻结阈值只适用于 fake-only 开发/CI 门禁，不构成生产 SLA。

## Step 1 实施与验证证据

- 从锁定基线 `1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3` 创建 `feat/f-009-safety-cost-performance` 与隔离 worktree `E:\Agent\comprehensive-cases\15-cyber-town-f009`；正式目录保持 `main`，文档未混入功能 worktree。
- 失败优先首轮因 `cyber_town.application.safety` 尚不存在而在收集阶段失败；实现后新增不可变 `f-009-input-policy-v1`、固定安全/未来控制 enum、版本化 synthetic fixture，以及高置信 persona 越权、prompt 探测、秘密提取、跨 scope、tool 与记忆指令化规则。
- HTTP 边界现为 `application/json`、缺失/`identity` encoding、8,192-byte 流式上限、四层 container、16 member/item、唯一 member、严格 UTF-8、有限 JSON 数值、无 trailing data；identifier 与 message 按 Step 0 锁定值拒绝，不执行 trim/casefold/normalize 修复。
- DeepSeek adapter 只接受唯一 `reply + relationship` envelope、单 choice、批准 model、`stop/content_filter`、无 tool/reasoning，并要求 prompt/completion/total usage 为严格整数、上限内且加和一致。任何非法 completion 映射为 `502 provider_invalid_response / retryable=false`，不写入短期、长期或关系状态。
- v1 成功字段形状不变；限制性接受集合和错误 enum 已重新导出到 JSON Schema。Godot 只扩展严格错误 allowlist/status-code 组合及 lowercase UUID 验证，没有场景、布局或新可见 UI。
- 红测阶段曾得到模块缺失收集错误；中间广泛回归以 `840 passed / 23 failed` 精确暴露既有测试对旧 `404 unknown npc`、宽松 NPC scope 与可重试 invalid response 的预期，按 Step 0 决策修正测试后最终相关矩阵 `876 passed`。
- 最终门禁：ruff 全绿；mypy `86 source files` 全绿；schema export/check 全绿；17 个变更 Python 文件 format 全绿；Godot 4.7.2 import/unit 全绿；tracked diff check 和 3 个 untracked no-index whitespace check 全绿。全仓 format 仍仅有 3 个与 `origin/main` 完全一致的既有基线文件，未越界修改。
- 安全结果：validation/injection 路径 provider dispatch 为 0；短期、长期和关系写入为 0；恶意 message、原始 player/NPC/conversation scope、provider body、system prompt、记忆正文、原始 suggestion 与秘密在公共错误、异常、日志和 in-memory observability snapshot 中禁止原文命中为 0。
- 未实施 Step 2—4：不存在 token bucket/rate-limit state、预算 reservation/settlement、control migration/SQLite、observability `0002`、自动 retry/backoff/jitter 或 circuit breaker；业务 migration `0001/0002` 未修改。

## Step 1 临时资源终盘

| 绝对路径 | 终盘 | 状态与建议 |
| --- | --- | --- |
| `E:\Agent\cyber-town-f009-step1-tests` | 删除前 696 files / 1,078 dirs / 60,767,790 bytes；676 个隔离业务 SQLite、20 个 synthetic JSON；0 `.env*`、0 reparse、0 nested Git | 已由用户手动回收；Step 2 预检及当前只读复核均确认路径不存在，Codex 未删除 |
| `E:\Agent\comprehensive-cases\15-cyber-town-f009\game\.godot` | 6 files / 2 dirs / 3,079 bytes；Godot import/script cache；0 SQLite/`.env*`/reparse | 保留至 F-009 Git 交付；之后由用户手动随 worktree 回收或精确删除 |
| `E:\Agent\comprehensive-cases\15-cyber-town-f009\.ruff_cache` | 5 files / 1 dir / 5,674 bytes；0 reparse | 早期门禁在预先报告前误建；已停止写入，保留至 Git 交付后由用户手动处理 |
| `E:\Agent\comprehensive-cases\15-cyber-town-f009\.mypy_cache` | 4 files / 1 dir / 37,548,322 bytes；0 reparse | 同上；后续门禁使用 `--no-incremental`，不得自动删除 |

正式目录和功能 worktree 中的 `data/cyber-town.sqlite3`、`data/cyber-town-observability.sqlite3`、`data/cyber-town-control.sqlite3` 均不存在；F-008 worktree/分支/缓存保持原状，F-005 验收资源未读取、修改或复用。

Step 1 已完成。

## Step 2 实施与验证证据

- 新增 `f-009-safety-control-v1`、五级连续 refill token bucket、领域分隔 HMAC tag、原子 execution admission、provider permit/lease 和独立 STRICT control SQLite `0001_safety_cost_control.sql`。控制库使用 `BEGIN IMMEDIATE`、WAL、2 秒 busy timeout、显式 allowed root、reparse 防护与固定 schema checksum；只保存 UUID execution/request linkage、HMAC tag、数值、时间和固定 code。
- HTTP 每次尝试先消费 ingress global/direct socket peer；忽略 forwarding headers。validation、未知 NPC、conflict、cache replay、concurrent waiter 不消费领域 token；只有新 execution 原子消费 player、player+NPC、conversation bucket，同 execution 重入幂等。
- provider permit 上限为 global 2、player 2、player+NPC 1、conversation 1；完成、provider 异常、取消和重启 orphan 均释放或收口。permit 排队超时不放大 dispatch；control admission/permit 获取或释放仓储失败均 fail-closed，状态不提交。
- 失败优先起点为 3 个缺模块收集错误，首轮骨架后为 `11 passed / 7 failed`；最终 Step 2 专项共 38 项通过，覆盖五类 bucket 容量/refill/Retry-After、时间回退、原子拒绝、SQLite 并发竞争、replay/waiter/conflict、global/player/player+NPC/conversation permit、取消、provider 异常、busy/损坏/schema/root/reparse 与仓储故障注入。
- 相关 Step 1/Dialogue/persona/scope/记忆/关系/observability 矩阵 `329 passed`；除会创建 `.env` 的 3 个不相关测试文件外，安全范围后端大回归最终 `1082 passed`。曾有 2 个长期记忆 evaluator case 因 Step 1 三 NPC public allowlist 拒绝其内部 `other_npc` fixture 而失败；只在测试中显式绕过 public DTO 后，19 项 evaluator 与大回归全绿。
- schema export/check、Godot 4.7.2 import/unit、ruff、32 个 F-009 Python 文件 format、92 source files mypy、tracked diff、10 个实际 untracked no-index whitespace、ignore/sensitive 均通过。全仓 format 仍只报告 2 个与 `origin/main` 一致的既有基线文件，未修改。
- 业务 migration `0001/0002` 与 observability `0001` 的 SHA-256 分别保持 `3d50bb…f4a4`、`7751c9…9c48`、`3827fe…cce8`，与 `origin/main` 无 diff；正式业务/observability/control SQLite 均不存在，8000 端口无 listener。
- 禁止原文结果：repository/DTO/异常/in-memory snapshot 专项为 0；203 个 control SQLite/WAL/SHM surface 对 synthetic raw player/NPC/peer/message/reply/provider detail 的二进制 sentinel 命中为 0。未读取 `.env`、调用真实模型、访问外部服务或触及 F-005 资源。

## Step 2 临时资源终盘与收口

删除前，`E:\Agent\cyber-town-f009-step2-tests` 为普通目录、父目录 `E:\Agent`、0 reparse；共 1,151 files / 1,523 dirs / 127,051,909 bytes，含 1,088 `.sqlite3`、18 WAL、18 SHM、23 JSON、0 `.env*`、0 nested Git、0 hidden、0 read-only。26 个非数据库文本/metadata 文件的 sensitive findings 和 scan error 均为 0。

扩大后端回归时，F-008 persistence 测试在该根内生成了 44 个 `observability.sqlite3`、18 WAL、18 SHM，共 80 surface / 8,601,600 bytes。它们均为 synthetic，但违反 Step 2“不得包含 observability SQLite”的资源类别边界。Codex 未执行删除；用户随后手动删除精确根。只读复核确认该路径不存在，父目录 `E:\Agent` 保持普通目录，正式仓库、功能 worktree、源码、分支和缓存未受影响；未重建测试根或重跑测试。

Step 2 已完成，后续 Step 3 已在单独授权下执行并完成。

## Step 3 实施与验证证据

- 新增不可变 `f-009-budget-policy-v1`、版本化 synthetic pricing、整数 micro-USD 向上取整、固定 1h/24h attempt/cost window 和 80% warning。fake/local/disabled 价格强制为 0；真实 provider composition 未显式注入匹配 model/provider 的批准价格表时，在创建 provider 或数据库前 fail-closed。
- control 迁移只追加 `0002_budget_cost_control.sql`，增加 execution owner、reservation、settlement 与 rolling-window 索引；既有 `0001_safety_cost_control.sql` 未修改。原子顺序为 rate admission → budget reservation → provider permit → dispatch → settlement → business commit。
- 同一 execution/attempt 的预留、dispatch 和结算均幂等；dispatch 前取消释放预留；timeout/unavailable/非法响应/provider cancel 与重启后的 dispatched orphan 均按最大预留保守结算；可信 usage 结算实际成本并释放差额。reservation/settlement 仓储失败均阻断 provider 或业务提交，recorder 故障保持 fail-open。
- observability 只追加 `0002_safety_cost_performance.sql`，保留 `0001`、真实 trace 不可回放和 `trace_runs.cost_micro_usd = 0`；新表只保存 trace/execution/attempt、固定 outcome、HMAC tag、token/cost 与时间。budget hard reject 为 `429 budget_exhausted / retryable=false`，无 `Retry-After`、余额、价格、scope 或数据库细节；Dialogue v1 成功字段与 Godot 场景/UI 均未改变。
- 失败优先首轮为缺少 `cyber_town.application.budget` 的 1 个收集错误；最终 Step 3 专项 `26 passed`。扩大后端回归首轮 `1122 passed / 1 failed`，唯一失败为旧 composition 路径测试未显式注入 test-only no-op control；按原测试职责修正后最终 `1123 passed`。配置为 `353 passed / 1 deselected`，仅排除会实际创建 `.env` 的用例。
- lock offline、schema、ruff、94 source mypy、36 个变更 Python format、Godot 4.7.2 import/unit、tracked diff、14 个 untracked no-index whitespace、ignore/sensitive 均通过。重复计费、重复 settlement、额外 provider dispatch、结算失败后的业务写入、scope 泄漏和禁止原文命中均为 0。
- 业务 `0001/0002` 与 observability `0001` 均与 `origin/main` 无 diff；SHA-256 分别为 `3d50bb6116de59b2d15293a50c7ed8bceddcdc567a413f43040d92b76eacf4a4`、`7751c9a990ed6825613e738601f4f07cf0affe5f937dfe0396be492edbb89c48`、`3827fe6cb658d6f2e02f4bbb1fbf93ccc27845a638127a07d048c0c14ac9cce8`。control `0001` 为 `9ce97b82e7675bd0a1057238b125fe39acf4dd1902ec53c44f564e5dfea16da6`。

## Step 3 临时资源终盘

- `E:\Agent\cyber-town-f009-step3-tests` 已到期，最终精确盘点见 evidence；只含 synthetic pytest/TEMP、业务/control/observability SQLite、WAL/SHM 与 JSON，0 `.env*`、reparse、nested Git、hidden 或 read-only。Codex 未删除；建议用户手动删除该精确目录后由 Codex 只读复核。
- 功能 worktree 内 `.ruff_cache`、`.mypy_cache` 与 `game/.godot` 继续保留到 Git 交付；`.pytest_cache` 不存在。误建 `.venv` 已由用户手动删除并复核，不得重建。
- 正式目录和功能 worktree 的正式业务/control/observability SQLite 均不存在；8000 端口无 listener。

Step 3 已完成。不得进入 Step 4、提交、推送、创建 PR 或部署，直到用户另行授权。

## Step 4 实施与验证证据

- 新增固定 `f-009-retry-breaker-v1`：每个 execution 最多 2 次 provider attempt，单次 timeout `5.0s`、总 deadline `12.0s`、backoff `200ms`、full jitter `0..200ms`；clock/sleeper/jitter 均显式注入。只有 timeout/unavailable 自动重试，其他拒绝、非法 response、replay 与 waiter 均不重试。
- retry 保持原 `execution_id`，每个实际 dispatch 独立完成 attempt 预算 reservation/dispatch/settlement；waiter 共享结果，replay 不创建 attempt。取消可传播到 backoff/provider，取消抵抗型迟到 completion 不改变 breaker、不提交短期/长期/关系状态。
- control 只追加 STRICT `0003_retry_circuit_breaker.sql`，按 provider kind + model 的 HMAC scope 保存 closed/open/half-open 状态、单 probe lease 和 execution 结果幂等。60 秒内连续 5 个 eligible execution failure 后 open 30 秒；half-open 只放行一个 probe，连续 2 次成功关闭，任一失败重新 open；重启释放 stale lease 但不伪造状态转换。
- observability 只追加 STRICT `0003_retry_circuit_breaker.sql`，保存固定 attempt/retry/breaker metadata；仍复用 14-stage trace，不保存 payload、原始 scope 或秘密，真实 trace 仍不可执行回放。recorder 故障 fail-open；breaker repository check/result 故障均 fail-closed 为 `control_unavailable`。
- `circuit_open` 映射为稳定 `503 / retryable=true`，`Retry-After` 限于 `1..30`；Dialogue v1 成功字段、Godot 场景和布局不变，Godot 复用既有 unavailable/retry 文本和错误 allowlist。
- 失败优先起点为缺少 `CircuitOpenError` 的 1 个收集错误；首轮骨架为 `3 passed / 4 failed`。最终 Step 4 专项 `18 passed`，相关控制/预算/可观测性/API 回归 `123 passed`，安全范围后端 `1141 passed`；配置 `353 passed / 1 deselected`，只排除会实际创建 `.env` 的用例。
- ruff、38 个 F-009 变更 Python format、96 source mypy、schema、Godot 4.7.2 import/unit、tracked diff、18 个实际 untracked no-index whitespace、ignore/sensitive 全绿。scope 泄漏、禁止原文、重复计费、重复业务写入、retry amplification 超过 2 和未授权 dispatch 均为 0。
- 既有 migration SHA-256 保持：业务 `0001=3d50bb…f4a4`、`0002=7751c9…9c48`，control `0001=9ce97b…6da6`、`0002=5c09d2…63f3`，observability `0001=3827fe…cce8`、`0002=4333b2…74a`；新增 control `0003=e03a8e…80b1d`、observability `0003=a90eda…2d7d`。正式业务/control/observability SQLite 均不存在，8000 无 listener。

## Step 4 临时资源终盘

- `E:\Agent\cyber-town-f009-step4-tests` 为普通目录，父目录 `E:\Agent`，根和递归项均无 reparse；共 1,269 files / 1,738 dirs / 145,773,129 bytes，包含 1,203 SQLite（144,826,835 bytes）、24 WAL（0 bytes）、24 SHM（786,432 bytes）和 18 JSON。
- `.env*`、nested Git、hidden、read-only 均为 0；该根位于 Git worktree 外，不属于 tracked/untracked/ignored 集合。control/observability SQLite/WAL/SHM 对 synthetic player/message/reply/HMAC key sentinel 的二进制命中为 0。
- 资源已到期但 Codex 未删除。建议用户仅手动删除精确路径 `E:\Agent\cyber-town-f009-step4-tests`；操作不可恢复，删除前不得扩大到父目录。worktree 的 `.ruff_cache`、`.mypy_cache` 与 `game/.godot` 继续保留到 Git 交付，`.pytest_cache` 不存在。

Step 4 已完成；用户随后已单独授权进入 Step 5。仍不得提交、推送、创建 PR 或部署。

## Step 5 未关闭性能缺陷

- 严重级别：P1（冻结交付门禁阻断，无数据正确性或隐私泄漏证据）。
- 最小复现：同机 FakeProvider、隔离业务/control/observability SQLite、concurrency=2；warm-up 后运行 5 个独立 run，每 run 100 completed execution。另以 fresh observability SQLite 每 run 100 trace。
- 期望：完整 loopback p95 `<=250ms`、p99 `<=400ms`、吞吐 `>=4/s`；control-on 相对 control-off p95 回归不超过 `max(20%, 30ms)`；observability 每 100 trace 增长 `<=512 KiB`。
- 实际五轮中位：control-off p95 `1257.8538ms`、p99 `1483.6411ms`、`1.949754/s`；control-on p95 `1843.02425ms`、p99 `2095.8564ms`、`1.063318/s`；fresh observability 增长 `671,744 bytes`。control-on 相对 p95 增加 `585.17045ms`，超过允许的 `251.57076ms`。
- 影响 scope：本机 fake-only SQLite instrumentation 与完整本地 loopback 性能；不声明为生产 SLA。provider dispatch 均为每轮 100，未观察 retry amplification。
- 测量限制：脚本的 `combined_database_growth_exceeded` 将业务 SQLite 也计入“两库合计”，该 failure code 不作为已确认产品缺陷；in-memory 吞吐口径也需在修复授权中复核。上述明确超限项不依赖这两个争议口径。

Step 5 已停止，状态为 `step_5_performance_gate_failed / awaiting_fix_authorization`。不得在未获单独修复授权时继续故障组合、三进程输出、完整回归或进入 Step 6。

## Step 5 P1 修复授权后的调查阻塞

- 用户已授权最小性能修复，但明确禁止放宽阈值、修改 migration、业务语义或外部契约。
- 2026-08-27 profiling：4 个 synthetic execution、4 dispatch，共 127 次连接/关闭、123 次事务；commit `0.865s`、close `0.670s`，52 次 stage progress `1.028s`。总耗时 `2.315s`；事务/连接关闭是候选热点。修订调查纠正：该 profile 含初始化，尚未单独测量稳态和 WAL checkpoint，不能断言 close 全由 WAL 收尾引起。
- 空间调查保持原表、字段、索引和数据：100 trace/1400 stage 的记录/索引 cell 合计 `596,448 bytes`（不是文件增长值）；6 种 fresh page layout 的最小实际增长为 `581,632 bytes`，仍大于 `524,288 bytes`。对应 page size 512/1024/2048/4096/8192/16384 的增长为 `715264/672768/651264/647168/581632/589824 bytes`。不以放大空库预分配或漏计索引来制造通过结果。
- control-on 的 control DB 为 `458,752 bytes`，同工作负载 control-off 的空 control DB 为 `147,456 bytes`，差额 `311,296 bytes` 也高于 256 KiB；完整空间修复需一并确认 control/observability 的索引存储边界。
- 当前授权下未找到能诚实满足全部空间阈值的最小 schema-preserving 方案。建议下一步只批准兼容、append-only 的 control/observability 索引优化方案审查，保持既有 migration 文件 hash、表字段、唯一约束、14-stage durable/recovery 和业务/API/Godot 语义；未获批准前不实施。
- 本轮只新增两个诊断脚本与授权根内 synthetic profiling/storage 实验，未修改产品实现、migration 或阈值。故未进入失败优先产品修复、五轮性能复验、evaluator/故障组合和完整回归。
- 资源现为 71 files/29 dirs/32,672,604 bytes：66 SQLite、3 metadata JSON、1 WAL(0 bytes)、1 SHM(32,768 bytes)；0 env-like/reparse/nested Git。保留作为阻塞证据，由用户手动回收，Codex 不删除。

该次调查结束时为 `step_5_performance_fix_blocked / awaiting_storage_contract_authorization`，不代表 Step 5 完成。

## Step 5 P1：append-only 索引迁移候选方案（2026-08-27，历史方案）

本节保留起草时的候选边界。用户随后已批准先预验证、通过后实施；预验证失败后的最新结论见下节，不能再将本节的“待确认”或条件式实施步骤理解为当前可继续执行的授权。

### 授权与只读核对

- 本轮只起草方案和更新项目文档；不创建 SQL 文件、不运行 migration、不连接/改写测试库、不测试，不修改功能 worktree。后续实施必须再次取得用户明确确认。
- 正式目录仍为 `main`；功能目录仍为 `feat/f-009-safety-cost-performance`；两者 HEAD 与本地 `origin/main` 均为 `1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3`。正式目录为五份项目文档改动，功能目录为 31 tracked modified + 26 实际 untracked；无 reset/stash/分支切换或联网。
- 只读依据：control/observability 的既有迁移、repository SQL、benchmark 源码及此前 profiling/storage evidence。没有以 SQL 名称检索未命中替代运行期查询计划验证；下列收益均为候选，不保证仅索引调整就能满足门禁。

### A. 迁移文件和兼容性边界

仅提出两个新文件；当前均不得创建：

1. `E:\Agent\comprehensive-cases\15-cyber-town-f009\backend\src\cyber_town\infrastructure\control\migrations\0004_compact_secondary_indexes.sql`
2. `E:\Agent\comprehensive-cases\15-cyber-town-f009\backend\src\cyber_town\infrastructure\observability\migrations\0004_compact_secondary_indexes.sql`

实施获准后，只向各自 migration 清单追加版本 4，按原迁移事务机制登记新 checksum 并将对应 SQLite `user_version` 推进到 4。`OBSERVABILITY_SCHEMA_VERSION=1`、各 DTO/policy version 和既有 migration/checksum 记录均不改。这里的 append-only 指**历史迁移文件不改写**；新迁移拟执行下表列明的非唯一 `DROP INDEX`，不是删除表、列、约束或业务/metadata 行。

不使用 `IF EXISTS` 隐藏漂移；先确认索引所属表、SQL、列顺序和 `unique=0` 与预期相同，异常即 fail-closed。保留所有 PK、UNIQUE（包括 SQLite autoindex 和 partial UNIQUE）、FK、CHECK、STRICT、表字段/SQL、数据值及行数；无 ALTER TABLE、表重建、行压缩或事件合并。只允许迁移台账新增第 4 条，不能通过减少事件数量降低增长。

### B. 固定候选清单：control 4 个 + observability 6 个非唯一索引

| 库 | 拟删除的精确索引名 | 静态依据、保留访问路径与风险 |
| --- | --- | --- |
| control | `execution_admissions_request_idx` | 当前 admission 以 execution PK 读取，再比较 request；无 request_id 查询入口。将来若新增此类查询，需重新评估索引，不能宣称所有未来查询无回归 |
| control | `idx_budget_attempt_execution_status` | execution 内最多 2 个 attempt；保留 `(execution_id, attempt_number)` PK，状态过滤最多两行；须验证并发/幂等和实际查询计划 |
| control | `idx_budget_cost_window_time` | 当前预算窗口使用 reservation 的 `reserved_at_ns`，settlement 按双元 PK JOIN；不按 `settled_at_ns` 范围检索。成本计算与时间归属不变 |
| control | `breaker_results_scope_time_idx` | 当前结果幂等按 execution PK，breaker 状态按 scope PK；没有结果按 scope/time 查询。保留 FK；未来父行删除/更新或范围审计可能扫描，当前不增加这些操作 |
| observability | `idx_trace_stage_events_stage_outcome` | 当前 stage 读取按 trace PK 前缀并按 sequence 排序；没有 stage/outcome 检索 API/CLI。保留 stage PK 和 `UNIQUE(trace_id, stage)` 两个约束 |
| observability | `idx_trace_stage_events_retention` | 过期传播通过 trace_id 子查询，保留 trace PK 前缀；独立 retention COUNT 可能改为扫描，须比较结果、计划和耗时；不取消 retention 标记 |
| observability | `idx_execution_links_retention` | 同上，保留 trace PK；retention 统计扫描的权衡需实测，不改变过期状态或清理权限 |
| observability | `idx_safety_cost_player_window` | 当前 safety-cost event 去重/读取按 trace+attempt+kind；没有按 player/time 查询入口。真正的预算窗口在 control 库，其 owner 索引不删 |
| observability | `idx_safety_cost_npc_window` | 同上，NPC 成本归属字段、事件和 control NPC 窗口计算全部保留 |
| observability | `idx_safety_cost_player_npc_window` | 同上，双元 HMAC tag 和每条 reservation/dispatch/settlement 事件完整保留 |

**必须保留**：三个 active permit partial 索引、三个 budget owner scope 索引、`idx_budget_attempt_quota_time`、全部 trace 查询索引、`idx_execution_links_one_dispatch_owner` 唯一索引、execution/attempt 检索索引、evaluation/replay 索引及全部约束索引。本方案不扩大到替换/删除更多索引；预验证不能满足阈值时停止，另报证据与待决策项。

### C. 既有 migration SHA-256 锁定清单

本轮只读重新计算如下，后续每次迁移验证和最终门禁都必须逐项一致：

| 目录类别 / 文件 | SHA-256 |
| --- | --- |
| persistence / `0001_long_term_memory.sql` | `3d50bb6116de59b2d15293a50c7ed8bceddcdc567a413f43040d92b76eacf4a4` |
| persistence / `0002_relationship_state.sql` | `7751c9a990ed6825613e738601f4f07cf0affe5f937dfe0396be492edbb89c48` |
| control / `0001_safety_cost_control.sql` | `9ce97b82e7675bd0a1057238b125fe39acf4dd1902ec53c44f564e5dfea16da6` |
| control / `0002_budget_cost_control.sql` | `5c09d2ab966d23c4a1766d05784620184174fbd5a46cc89e7edf222bdfb963f3` |
| control / `0003_retry_circuit_breaker.sql` | `e03a8e8fb08477288f51b7e1d7c4d7fbe10b51f708404e6b66e8772c4ba80b1d` |
| observability / `0001_observability.sql` | `3827fe6cb658d6f2e02f4bbb1fbf93ccc27845a638127a07d048c0c14ac9cce8` |
| observability / `0002_safety_cost_performance.sql` | `4333b27520de58dd15d89c0478b266a64643097842930a7510c0961f177cb74a` |
| observability / `0003_retry_circuit_breaker.sql` | `a90eda95d7eccf13b021e6d89c213f89f42afb53db2d7ca02683a89b7b4a2d7d` |

### D. 确认后的执行顺序与失败门禁（本轮不执行）

1. **先验证索引候选收益**：仅在授权 Step 5 根内新建 synthetic v3/v4 对照库，用相同 100 unique execution/trace、完整 14-stage 和真实产生的 safety-cost/retry/breaker metadata 填充。对上述 10 个非唯一索引做精确候选实验，输出每库增长、索引/页计数、查询计划和查询耗时。不得拿只有 trace/stage、没有控制事件的子集冒充完整链路。只有空间达到 512/256/768 KiB 且查询/正确性可接受，才落产品 `0004` 和追加 migration 清单；否则保留证据并停止，不扩大清单或调阈值。
2. **失败优先迁移验证**：新库 0→4、已有 synthetic v3→4、再次打开幂等；既有版本 1/2 升级仍逐版本执行；旧文件 hash、旧台账、表 SQL/字段、PK/UNIQUE/FK/CHECK、非台账行数/metadata digest 不变。验证 10 个目标索引消失且其余全部保留、`foreign_key_check`/完整性检查通过、migration 中途故障整库事务回滚（含台账与 user_version）、schema/checksum/索引漂移 fail-closed。
3. **durability 与业务回归**：保持 durable open trace、每个已确认 stage 的事务持久化、14-stage 终态和重启 abandoned 语义；不改成只在 terminal 落库，不后台丢弃或异步缓冲已确认 stage。增量断点重启、completed 不变、重复 recovery、dispatch owner 唯一、replay/waiter/取消/迟到、预算原子预留结算与 breaker/probe 全部回归；保持 WAL 和现有持久化强度，不降低同步级别。
4. **性能修复与完整复验**：索引迁移只减少索引写放大，不能证明解决 127 connect/close、123 commit 的热点。继续原已授权的最小连接生命周期调查/修复必须以 profiling 和失败优先测试为前提，不减少事务承诺、不改业务 SQL 结果/契约；如需进一步 schema/语义变更则停止再请求授权。先完成下述口径纠正，再执行完整 warm-up + 5-run 矩阵；全部绝对/相对门禁通过后，才恢复原 Step 5 的 evaluator、三进程 digest、组件故障组合和完整回归，不进入 Step 6。

兼容范围是**新代码读取/升级旧库，升级后业务与查询结果不变**，不承诺旧 v3 程序能打开 v4 库。迁移时停止相关 writer，不允许旧/新版本混用；两库各自事务原子，不伪装跨库原子。若一库成功另一库失败，停止启动，报告两库版本，等待处置，不擅自降级。提交前迁移故障回滚由事务完成；成功后只考虑另获授权的后续恢复索引迁移，不改历史、不调低 user_version、不覆盖数据库，不实施生产迁移或自动备份/清理。

### E. 测量口径纠正与冻结阈值

- `combined DB growth` 只计 control + observability；业务库单列且仍完整执行，不能停写业务以换取性能。固定 fresh v4 schema 完成、尚无 workload 时为基线；报告 checkpoint 后主文件增量、WAL/SHM 起止和运行峰值，使用一致状态对照，不靠未 checkpoint 的 WAL 隐藏增长。升级旧库回收的 freelist 与 fresh 增长分开报告，不能用旧库空闲页抵扣 fresh 门禁；不预分配、VACUUM、清数据或缩减事件。DROP INDEX 不保证旧数据库文件立即缩小。
- `in-memory throughput`：独立 no-recorder 微基准保留；80% 相对比较须使用同轮、相同 control 决策/输入/执行规模的 no-op 与 in-memory recorder 配对，仅 recorder 变体不同。每 run 1,000 个独立 synthetic trace，不能把预构造的同一对象重复 append 代替完整 control+recorder 工作量，报告绝对门禁和配对比值。
- 源码核对发现当前 `_loopback_run` 实际直接调用 `DialogueService.execute`，且将并发 pair 总耗时除以 2 作为每请求延迟。旧数值仅保留为服务层诊断，不是合格 HTTP 端到端分位数。复验须使用真实本地 HTTP→FastAPI→DialogueService→FakeProvider→三 SQLite 链路，逐请求 start/end 计时、吞吐用整轮 wall clock，不能平均摊薄并发延迟；不改变 Godot 或 API。注入等待原值另列，只排除明确注入的等待，不减去真实 SQLite/调度开销。
- 单独的 completed `save_trace` 微基准与实际 14-stage 增量写链路分别报告，不能相互替代；pre-dispatch rate、budget、breaker 三种拒绝均覆盖，不能只测 breaker。
- Step 0 J 表全部保持：no-recorder p95/p99 `0.050/0.100ms`；in-memory+control `2/5ms` 且配对吞吐 `>=80%`；SQLite recorder `150/200ms`、`>=8/s`；三种拒绝 p95 `<=50ms`、dispatch 0；完整链路 `250/400ms`、concurrency 2 时 `>=4/s`；control-on 相对 p95 `<= max(20%,30ms)`；空间 `512/256/768 KiB`。仍为 warm-up + 5 独立 run、no/in-memory 每 run 1,000、SQLite 每 run 100，不降低样本数、不挑选最佳 run。

### F. 临时资源候选与人工处置

本轮新增临时资源为 **0**。只读终检确认原根 `E:\Agent\cyber-town-f009-step5-tests` 仍为 71 files/29 dirs/32,672,604 bytes，含 66 SQLite、3 JSON、1 WAL、1 SHM，0 env-like/reparse/nested Git；实施前仍须重新核对。既有 profiling/performance/storage 证据不得覆盖、移动或删除。worktree 的 ruff/mypy/Godot cache 分别为 5 files/6,682 bytes、3 files/38,138,085 bytes、6 files/3,079 bytes，全部保留，本轮没有写入缓存。

若用户确认实施，下列精确子目录才允许创建；任一已存在或为 reparse point 即停止，不复用覆盖、不自行换路径：

| 精确候选路径 | 内容、敏感性与使用期限 |
| --- | --- |
| `E:\Agent\cyber-town-f009-step5-tests\index-v4-preflight` | synthetic v3/v4 候选索引实验库、EXPLAIN/页计数/查询耗时 metadata JSON；无真实 payload/秘密，保留到 Step 5 结束 |
| `E:\Agent\cyber-town-f009-step5-tests\index-v4-tests` | synthetic 迁移/故障/重启测试 SQLite、pytest/TEMP 产物和 metadata 摘要；业务库仅 synthetic，control/observability 不保存原文；保留到 Step 5 结束 |
| `E:\Agent\cyber-town-f009-step5-tests\performance-v4` | 修正口径后的 warm-up/5-run 三库数据与 metadata-only summary，含 evaluator/三进程/故障组合的独立子路径；保留到 Step 5 结束 |

责任人/任务为 F-009 Step 5；台账位置为本任务卡本节及 `progress.md`、`evidence.md`。创建前报告最终解析路径；pytest basetemp 使用正斜杠绝对路径并避免复用导致自动删除，TEMP/TMP 只在授权根内。不创建新 venv、测试根外缓存、正式 DB、`.env` 或日志原文；不读/改/复用 F-005 资源，不调用模型或外部服务。

处置建议：现在保留 Step 5 根用于修复证据；Step 5 结束后重新盘点文件数/字节/类型/reparse/嵌套 Git/占用，再向用户提供仅针对精确根的手动删除建议和命令，删除结果不可恢复。Codex 不删除；worktree、分支与已有缓存继续保留到 Git 交付后单独处理。

### 待用户确认

确认范围为上述两个 `0004`、固定 10 个非唯一索引候选、只追加迁移版本、先做收益预验证再落产品迁移、测量口径纠正及原最小性能修复续行。未确认前，不执行这些操作。收益不确定、retention 查询扫描和旧程序版本不兼容均已明确；不足以达标时停止，不能默认获得更多索引或表结构变更权限。

方案起草结束时为 `step_5_performance_fix_blocked / awaiting_index_migration_confirmation`；F-009 Step 5 与 P1 当时均未完成。

## Step 5 固定索引收益预验证：失败并停止（2026-08-27）

### 授权、方法与红测

- 用户批准仅在原 Step 5 根预验证固定 control 4 + observability 6 个非唯一索引；空间或查询门禁不通过立即停止，不扩展清单。基线仍为 `1a4fc2c`，正式 main 五份文档、功能分支既有 31 tracked/26 untracked 均完整。
- 本轮只新增 `scripts/f009_step5_index_preflight.py` 与 `backend/tests/test_index_preflight_step5.py`，未修改产品实现。纯函数测试先因模块不存在产生 1 个收集错误，随后最终 `3 passed`；验证精确索引数量、不含 dispatch 唯一索引、冻结空间阈值及空闲页不能掩盖占用增长。ruff、format、2 source mypy 和新增文件 whitespace 通过。mypy 首次缺少 MYPYPATH 的环境问题经显式指向功能源码修正，没有安装依赖或创建 venv。
- 以相同规模分别执行 baseline-v3 与 candidate-indexes：各 100 unique execution、三个 NPC、并发 2；HTTP 请求通过 in-process ASGI→FastAPI→DialogueService→FakeProvider→隔离三 SQLite。未使用 TCP listener，因此本次是空间/完整事件预验证，**不是最终真实 HTTP loopback 延迟验收**。
- 候选仅在新建实验库应用固定 `DROP INDEX`；产品 migration 文件/清单不变，实验库 `user_version` 仍为 3，报告明确 `product_migration_applied=false`。未伪造第 4 条迁移记录。索引删除前后表 SQL、全部唯一约束与初始化行 digest 不变；其他索引全部保留。

### 实测结果：每组 100 次执行

| 口径 | control | observability | 两库合计（排除业务库） |
| --- | --- | --- | --- |
| 原索引主文件/占用页增长 | 311,296 bytes / 304 KiB | 978,944 bytes / 956 KiB | 1,290,240 bytes / 1,260 KiB |
| 固定候选主文件增长 | 270,336 bytes / 264 KiB | 663,552 bytes / 648 KiB | 933,888 bytes / 912 KiB |
| 固定候选占用页增长 | 286,720 bytes / 280 KiB | 688,128 bytes / 672 KiB | 974,848 bytes / 952 KiB |
| 冻结上限 | 262,144 bytes / 256 KiB | 524,288 bytes / 512 KiB | 786,432 bytes / 768 KiB |

- 原因解释：移除固定索引确有空间收益，但剩余表与必须保留的索引增长仍超过门禁。候选初始化后产生 control 4 页、observability 6 页空闲页；将其后续复用单独计入占用增长，避免与真正 fresh 增长混淆。即使只看较低的主文件增量，三项也全部失败，结论不依赖保守计量方式。业务库每组独立增长 61,440 bytes，不计入“两库合计”。
- 固定失败码：`control_growth_exceeded`、`observability_growth_exceeded`、`combined_growth_exceeded`。预验证进程 exit 1；未继续五轮性能矩阵、原 benchmark 口径修复、连接生命周期修复、evaluator/三进程 digest/故障组合或完整回归，未进入 Step 6。
- 每组 100 completed/100 dispatch、100 trace/1,400 stage、300 safety-cost event、200 retry-breaker event；预算 owner/reservation/settlement 各 100，原/候选各表行数一致，stage 数异常 0、fake 成本 0，完整性检查通过、FK 错误 0。这里只证明该 synthetic 正常完成场景，不能替代完整隔离/取消/restart 矩阵。
- 8 类查询结果一致；attempt 查询转用 execution+attempt PK，预算窗口继续使用 owner scope/双元 PK；retention COUNT 如预期退化为表扫描。20 次取样的 stage retention 最大耗时从 `0.3569ms` 到 `0.4825ms`、link retention 从 `0.0552ms` 到 `0.1802ms`；样本小，不据此声明延迟门禁通过。
- 13 个 control/observability SQLite/WAL/SHM/summary surface 对 synthetic raw scope、message、reply、HMAC key sentinel 命中为 0；没有读取 `.env`、调用真实模型/外部服务或访问 F-005 资源。八份既有 migration hash 保持锁定值。

### 本轮临时资源终盘与手动处理建议

| 精确路径 | 准确盘点 | 状态与处置建议 |
| --- | --- | --- |
| `E:\Agent\cyber-town-f009-step5-tests\index-v4-preflight` | 创建时间 `2026-08-27T11:36:55.7787444+08:00`；15 files / 2 dirs / 3,403,285 bytes：6 SQLite、4 零字节 WAL、4 SHM、1 metadata JSON | 本次预验证结束；建议保留为 P1 阻塞证据，待决定后续方案或 Step 5 收口再由用户手动删除。精确删除只移除本次对照库/报告，不影响源码；不可恢复 |
| `E:\Agent\cyber-town-f009-step5-tests` | 含上行；86 files / 32 dirs / 36,075,889 bytes：72 SQLite、5 零字节 WAL、5 SHM、4 JSON | 仍保留全部 Step 5 证据；当前不建议删除。后续明确结束/放弃证据时，再重新审计并由用户手动删除精确根；不得连同父目录删除 |
| `E:\Agent\comprehensive-cases\15-cyber-town-f009\.ruff_cache` | 5 files / 6,682 bytes | 保留到 F-009 Git 交付后单独处理，本轮 ruff 使用 no-cache |
| `E:\Agent\comprehensive-cases\15-cyber-town-f009\.mypy_cache` | 4 files / 38,158,581 bytes，含本次 mypy 生成的 16-byte `missing_stubs` 和既有 cache.db | 保留到 Git 交付后单独处理，不清理；本轮仅复用既有缓存目录 |
| `E:\Agent\comprehensive-cases\15-cyber-town-f009\game\.godot` | 6 files / 3,079 bytes | 本轮未运行 Godot，保留到 Git 交付后单独处理 |

测试根及新子目录均为普通目录，0 reparse/env-like/nested Git/hidden/read-only，位于 Git 仓库外（tracked/untracked/ignored 不适用）；三类 worktree 缓存均 ignored，0 reparse。`index-v4-tests`、`performance-v4`、功能 `.venv`/`.pytest_cache` 与两份产品 `0004` 均不存在。Codex 未删除或移动任何资源，既有实验文件未覆盖。`summary.json` 为 15,893 bytes，可用于只读复核。

若用户决定只放弃本轮对照证据，先重新核对边界/占用，再由用户执行 `Remove-Item -LiteralPath 'E:\Agent\cyber-town-f009-step5-tests\index-v4-preflight' -Recurse`；不要同时删除其父目录。当前建议仍为保留，而非立即回收。

### 收口与下一决策

正式目录仍仅五份项目文档，功能 worktree 为 31 tracked modified + 28 实际 untracked（本轮新增 2 个诊断/测试文件）；没有产品迁移或实现变更、提交、推送、PR、部署。两目录正式业务/control/observability DB 均不存在，8000 listener 为 0。

固定索引方案不足以通过门禁，不建议实施当前 `0004`。本次预验证结束时为 `step_5_index_preflight_failed / awaiting_revised_plan_authorization`，P1 和 Step 5 均未完成；随后获准的只读修订方案见下一节，不能把该起草授权视为修复授权。

## Step 5 P1 修订存储与性能方案（2026-08-27，仅起草）

### 1. 只读预检与结论

- 正式目录仍为 main，功能目录仍为 `feat/f-009-safety-cost-performance`；两者 HEAD 与本地 origin/main 均为 `1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3`。正式目录仅 current-task、implementation-plan、roadmap、progress、evidence 五份文档；功能目录 31 tracked modified + 28 实际 untracked，未触碰既有实现。
- 两份产品 `0004_compact_secondary_indexes.sql` 不存在；业务 0001/0002、control 0001—0003、observability 0001—0003 共八份 migration SHA-256 与上文锁定清单一致。本轮不创建替代 `0004`，也不改 migration 清单。
- 只读取相关源码/测试/migration 和现有 `index-v4-preflight/summary.json`、`storage-probe.json`、`profile-before-2.json`；未直接打开 SQLite、未重跑实验、未建立连接或生成 WAL/SHM。
- **已证实**：固定清单不足，主文件增长和排除空闲页复用的占用增长都失败。**未证实**：剩余空间由哪些对象主导、物理布局是否能补足差额、连接复用能否通过延迟门禁。没有可直接实施且已证明达标的默认边界内方案。
- 使用 investigate 的证据/假设分离方法；用户只读边界优先，不执行技能的初始化写入、遥测、外网搜索、实验、修复或自动提交流程。

### 2. 剩余空间：分别归属，禁止混用口径

| 对象类别 | control | observability | 能证明什么 / 缺口 |
| --- | --- | --- | --- |
| 实测占用增长 / 冻结上限 | 280 / 256 KiB，差 24 KiB | 672 / 512 KiB，差 160 KiB | 合计差 184 KiB；这是完整候选正常场景的总量，不是逐对象分解 |
| 表记录 | token_buckets 302 行；admission、permit、budget owner/reservation/settlement、breaker result 各 100；breaker 1、probe 0 | trace 100、stage 1400、execution link 100、cost 300、retry/breaker 200；evaluation/replay 为空 | JSON 有行数，无完整链路各表占用页/溢出页/碎片字节；空表不能推出其真实使用场景免费 |
| PK / UNIQUE 所需存储 | 9 张业务控制表的主键及 probe execution 唯一约束 | trace/stage/link/cost/retry 主键，stage 的 trace+stage UNIQUE，dispatch owner 部分唯一索引等 | 不能删除或放松约束；当前 rowid 表存在表树和非整数 PK 索引，重复键的实际净开销尚未分解 |
| 保留的非唯一索引 | 3 个 active permit、3 个 budget owner scope、attempt quota 时间索引 | trace 的 8 个查询索引、execution 查询索引、cost/retry execution+attempt 索引及 evaluation/replay 索引 | 不能把“当前某个 SQL 未命中”当作额外删除授权；原 10 个之外全部保留 |
| 空闲页 | 候选空库 4 页 × 4096 = 16 KiB，结束 0 页 | 候选空库 6 页 × 4096 = 24 KiB，结束 0 页 | 这解释主文件 264/648 KiB 与占用 280/672 KiB 的差异；不是可再次宣称的修复收益 |
| WAL / SHM | 开始/结束 checkpoint 快照为 0 | 开始/结束 checkpoint 快照为 0 | 后续查询留下的 4 个 WAL 为 0 bytes、4 个 SHM 共 128 KiB；不是数据库主文件增长，也不代表运行时 WAL 峰值为 0 |

旧 `storage-probe.json` 只估算基础 trace/stage/link：记录 cell 分别 43,300 / 156,373 / 10,200 bytes；stage PK/UNIQUE cell 估算 64,172 / 86,472 bytes。它没有覆盖 control、cost/retry 完整对象；其 596,448 bytes 合计不含完整页布局成本，脚本还依赖 rowid，并非通用的部分索引/新布局分析器。**这些数字既不是物理增长下界，也不是可回收字节承诺。**

原页布局实验仅有基础 trace 数据：4096 页增长 647,168 bytes，8192 页为 581,632 bytes，差 64 KiB；不能将这 64 KiB 直接从完整候选 672 KiB 中扣除，更不能据此断言任何新布局必然失败或成功。固定索引报告的文件尺寸峰值只在请求对完成时取样；未持续观测 WAL/SHM，不当作完整运行峰值。

### 3. 两个有界候选与推荐

**候选 A：保留 rowid 表，原 10 索引清单 + 新实验库 4096/8192 页对照。**

- 精确范围：control/observability 全库页布局；表字段/约束不变，非唯一索引只限上文已列明的 4+6。实验只涉及新诊断脚本及新 synthetic 库；如果将来采纳，产品涉及两库 repository 的新库初始化策略、原拟定两份 `0004_compact_secondary_indexes.sql` 和 migration 测试。
- 依据：旧基础数据的 8192 页布局改善约 64 KiB；control 尚无同类证据。没有足够依据认为它能补足完整场景的 24/160 KiB，收益方向也不保证跨数据分布成立。
- 风险：更大页可能增加小事务写入量和 WAL 成本、降低少量行占用效率；旧库无法仅靠新增索引迁移获得新页布局。现有旧库适配可能需要重建/转换，不能暗中 VACUUM、预分配或改写历史 migration。
- 边界：不扩大索引、字段或逻辑约束清单；但**新库页参数与旧库转换不是已有索引授权的自动延伸**，需另行确认。当前不推荐直接实施，也不再无界枚举页尺寸。

**候选 B：原 10 索引清单 + 有界叶表 WITHOUT ROWID 物理布局预验证。**

- 假设：用主键组织表，可能避免独立 rowid 表树与非整数 PK 索引的部分重复键存储。这里只提出可证伪假设，不承诺节省量。stage PK 的历史 cell 估算约 62.7 KiB；control 的 302 个 bucket 的 64 字符 tag 仅字符材料为 19,328 bytes；二者都不能当作净回收量，尤其不能覆盖尚缺的全部差额。
- 精确候选表共八张：control 的 `token_buckets`、`provider_permits`、`budget_settlements`、`breaker_execution_results`；observability 的 `trace_stage_events`、`execution_links`、`safety_cost_events`、`retry_breaker_events`。当前 migration 中它们没有被其他表引用的入向 FK；有出向 FK 的表仍须保留原约束与父表，不重建 trace_runs/admission/owner/reservation/circuit 等父表。
- 所有列、类型、默认值、NOT NULL、PK 列及次序、UNIQUE、FK 动作、CHECK、STRICT 和唯一 dispatch owner 语义必须等价。只允许原 10 个非唯一索引候选移除；其余具名索引全部保留。物理 PK 树/自动索引表示会改变，**这属于新的物理表布局/重建权限，不是“保持旧索引删除授权即可实施”**。
- 产品候选精确文件（均未创建）：`backend/src/cyber_town/infrastructure/control/migrations/0004_leaf_table_storage_layout.sql`、`backend/src/cyber_town/infrastructure/observability/migrations/0004_leaf_table_storage_layout.sql`；相应 `control/sqlite_control.py`、`observability/sqlite_observability.py` 的 migration 清单，以及 `backend/tests/test_sqlite_control.py`、`backend/tests/test_sqlite_observability.py`。它替代而非叠加原两个 `0004` 命名，最终仍须逐条 SQL 单独确认。
- 预验证候选文件为 `scripts/f009_step5_layout_preflight.py`、`backend/tests/test_layout_preflight_step5.py`；原 `f009_step5_index_preflight.py` 与 `f009_step5_storage_probe.py` 依赖 rowid，不应直接用于新布局或覆盖旧证据。产品仓储静态检索未发现 rowid/lastrowid/blobopen 依赖，这只是兼容性线索，不替代测试。
- 风险：宽复合主键可能放大保留的二级索引定位键，抵消收益；主键顺序/NULL 拒绝行为必须逐例比较。复制重建有临时双份空间、写锁、故障中断风险；两库升级不是跨库原子事务。旧版本严格校验 migration 清单，不能承诺旧程序直接打开 v4。查询计划、CLI、retention 扫描、取消和重启恢复均需复验。
- 新增授权须明确：仅新 synthetic 实验库内重建上述八表、比较物理布局；**不授权产品 migration、不接触既有证据库或正式库**。通过后另行授权产品 append-only 迁移，要求事务内复制/约束校验/失败回滚，不关闭 FK、不修复/丢弃数据、不擅自改变接受集合。

**推荐路径：D0 逐对象空间归属诊断 → 再确认是否试候选 B。** B 比仅改变页大小更直接针对键重复假设，但证据不足以直接推荐落地。D0 不改变 schema 或索引清单，也不试 B；先分清控制库的 24 KiB、观测库的 160 KiB 差额由哪些表/索引占用。若实际数据不支持 B、或 B 需要超出八表/原十索引/逻辑约束边界，停止重新报告。候选 A 保留为比较项，不自动并行试验；不新增字段编码、字典表、压缩、裁剪事件等第三方案。

### 4. 与空间方案独立的连接/事务修复候选

已有 profiling 包含初始化：4 次执行共 127 connect/close、123 begin/commit、429 PRAGMA，commit/close 约 0.865/0.670 秒，另有 66 CREATE。说明连接和提交路径值得调查，**不能把初始化计数直接当作稳态每请求成本，也不能据 close 累计时间断定全是 WAL checkpoint**。

精确候选文件为两库 `sqlite_control.py`、`sqlite_observability.py` 及相应 repository 测试；如果需要生命周期注入，再单列 `backend/src/cyber_town/api/composition.py` 的最小关闭/释放变更供确认。先把 schema 初始化、稳态 connect/PRAGMA、begin/commit、close/checkpoint 的计数/时间分开，避免重复累计嵌套 profiler 时间。

候选是在明确的 repository/线程所有权内有限复用连接，显式 close；每次业务操作仍保留原 begin/commit/rollback 边界。不得跨 await 持有事务，不默认全局共享连接或直接关闭线程校验；需证明并发锁、公平性、跨线程 TestClient、取消和关闭无死锁/重复写。路径/reparse 防护仍有效，不能为了减少 `_validate_current_path` 耗时取消安全校验。保持既有 journal/synchronous 强度，14-stage 逐次 durable commit、open trace 和 restart abandoned 不变；不延迟落盘、不以 pending 缓冲替代 live progress，不减少终态事件。此项不计入空间收益，长连接积累的 WAL 不能藏入未计量区。

### 5. 失败优先顺序、完整测量与停止条件（本轮均未执行）

1. **D0 先补证据，完成即停。** 另获授权后，在新精确子根重建 baseline-v3 与 fixed-ten-index 两组 fresh synthetic 三库，保持 100 unique execution、3 NPC、100 trace/1400 stage/300 cost/200 retry-breaker、业务写入，逐对象统计表树、必要约束索引、保留非唯一索引、overflow、页内闲置与 freelist。输出增量与绝对量、初末尺寸、采样 WAL/SHM、检查点状态。不得把对象数/cell 估算标成物理字节。
   已知当前 bundled SQLite 不提供 dbstat；不安装扩展或换 SQLite。优先设计仅对**新生成且已关闭/checkpoint 的 control/observability 文件**读取页归属的诊断，保留原 rootpage/类型等元数据，不输出 cell 内容/键值。先以 synthetic 页形状/部分索引/空闲和溢出页失败优先测试核对；各对象页、schema/管理页与 freelist 必须和总页数守恒。若无法可靠归属，明确报告 unknown 并停止，不能用重建单表库的尺寸之和冒充全库物理分解。业务库不做原始页内容分析。
2. **D1 单独批准一个固定布局预验证。** 在 D0 证据支持且用户批准候选 B 后，才允许新库内八叶表布局对照；不同时改连接、业务或计时器。先红测布局/逻辑约束/守恒断言，后比较完整事件、行值等价、FK/UNIQUE/CHECK/NULL/STRICT 和查询结果。复制/重建本身可能腾出碎片，必须同时报告 fresh 目标布局与 v3 升级路径，不能拿一次压实收益充当持续每 100 execution 的增长改善。
3. **空间可行性门禁先行。** 每个独立 fresh 对照保留完整 100 样本，报告 checkpoint 后主文件和排除初始 freelist 复用的占用增长；control/observability/combined 各不超过 256/512/768 KiB，业务库单列。空间初验不替代最终 warm-up + 5-run。任一超限、约束/事件变化、未知分解或仅靠旧库空页才通过，立即停止；不扩大表/索引清单，不放宽阈值。
4. **D2 产品最小迁移另行批准。** 只有空间和语义预验证通过，才草拟确认最终 SQL 并实施两份 append-only `0004`。先红测 0→4、3→4、重复初始化、复制中断/回滚、任一库升级失败、CLI 版本兼容和重启；八份旧 migration hash、字段及全部约束不变。不执行真实数据迁移或自动备份/替换任何正式数据库。
5. **D3 单独验证连接修复与测量口径。** 对原事务边界、14-stage、durable open、逐 stage 崩溃、abandoned recovery、cancel/orphan/late generation、并发预算和幂等写入做失败优先测试；先证实热点，再改最小连接生命周期。`scripts/f009_step5_benchmark.py` 与 `backend/tests/test_control_performance_contract_step5.py` 纠正 combined 只计 control+observability、in-memory 与同控制/持久化工作量 no-recorder 配对、真实本地 TCP HTTP→FastAPI→service→FakeProvider→三库逐请求计时，禁止 pair 总时间除以 2 充当延迟。
6. **D4 全矩阵通过才恢复 Step 5 余项。** 同机每组 warm-up + 5 独立 run，no/in-memory 各 1000/run、SQLite/完整 HTTP 各至少 100/run；保留所有样本，报告每轮和五轮中位数，失败/超时不能从分母排除。覆盖串行、跨 NPC、waiter、replay、retry、circuit-open、restart；计入实际短期/长期/关系写入，不以预验证的空长期表替代应有的记忆场景。只排除明确注入等待，不排除排队/锁/commit/网络。运行时 WAL/SHM 采样峰值和静止后的主文件增量分别报告，不以预分配空库、VACUUM、旧库空页或省略业务写入制造通过。

全部冻结门禁继续适用：no-recorder p95/p99 <=0.050/0.100ms；in-memory+control <=2/5ms、配对吞吐 >=80%；SQLite observability <=150/200ms、>=8 trace/s；三类 pre-dispatch reject p95 <=50ms/dispatch 0；完整 HTTP <=250/400ms、并发 2 >=4 execution/s；control-on p95 增量 <=max(配对 control-off p95 的 20%, 30ms)，以及 256/512/768 KiB 增长。完整矩阵任何绝对/相对门禁失败都停止，不先运行 evaluator 以掩盖性能阻断。

只有完整矩阵通过，才恢复原 Step 5 实际 evaluator、三进程 canonical digest、组件故障组合和全部 fake-only 回归、ruff/format/mypy/schema/Godot/loopback/diff/ignore/sensitive/migration 门禁。固定 fixture 目前为 25 case/11 维度；历史 23 passed 只是契约测试，不是最终综合验收。新 P1/兼容性缺陷需另报，不自行扩大修复；始终不自动进入 Step 6。

### 6. 候选资源与生命周期（本轮未创建）

| 精确候选路径 | 内容与敏感性 | 授权阶段 / 期限 |
| --- | --- | --- |
| `E:\Agent\cyber-town-f009-step5-tests\storage-breakdown-v2` | fresh baseline/candidate synthetic 三 SQLite、pytest/TEMP、只含计数/页归属的 JSON；业务 fixture 明确 synthetic，control/observability metadata-only，无真实 payload/秘密 | 下一建议授权只允许 D0；诊断结束保留至 Step 5 收口 |
| `E:\Agent\cyber-town-f009-step5-tests\layout-preflight-v2` | 八叶表布局 synthetic 对照库、约束/页计数 metadata；同上隐私边界 | D1 单独批准后；保留至 Step 5 收口 |
| `E:\Agent\cyber-town-f009-step5-tests\migration-v4-tests` | synthetic 迁移/回滚/恢复 SQLite、pytest/TEMP 和 metadata 摘要 | D2/D3 单独批准后；保留至 Step 5 收口 |
| `E:\Agent\cyber-town-f009-step5-tests\performance-v2` | 修正测量的独立 warm-up/五轮三库、metadata-only 性能/evaluator/digest/故障摘要 | D4 授权后；保留至 Step 5 收口 |

责任 F-009 Step 5；台账为本节及 progress/evidence。四路径本轮均不存在；不得覆盖旧 `index-v4-preflight/summary.json` 或复用 pytest basetemp 导致自动清空。各后续命令须提前声明精确子路径，Windows basetemp 使用正斜杠；TEMP/TMP 在对应新子根，既有解释器、不建 venv、不安装依赖，不新建授权外缓存或 `.env`。诊断源码候选仅 `scripts/f009_step5_storage_breakdown.py`、`backend/tests/test_storage_breakdown_step5.py`，位于既有功能 worktree，仍需下一授权才能创建。

当前只读盘点与上轮一致：Step 5 根 86 files/32 dirs/36,075,889 bytes，内含 index-v4-preflight 的 15 files/2 dirs/3,403,285 bytes；ruff 5 files/6,682 bytes、mypy 4 files/38,158,581 bytes、Godot 6 files/3,079 bytes。根和缓存均 0 reparse/env-like/nested Git；没有新资源。本轮建议保留所有失败证据，不删除。未来诊断/Step 5 结束后重新审计准确目标、占用和 Git/reparse 边界，由用户手动删除精确实验子根或整个 Step 5 根，不能两级重复删除；删除不可恢复，Codex 只复核。worktree/分支/缓存仍留至交付后另行决定，不随测试根处理。

### 7. 下一步建议授权 Prompt：仅 D0，不自动试布局或修复

```text
批准 F-009 Step 5 P1 修订方案中的 D0：仅补齐逐对象空间归属诊断。
不得实施候选 A/B、产品修复、0004、连接复用或完整性能矩阵。

正式目录 E:\Agent\comprehensive-cases\15-cyber-town 保持 main；
功能目录 E:\Agent\comprehensive-cases\15-cyber-town-f009 保持
feat/f-009-safety-cost-performance；HEAD/本地 origin/main 均为
1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3。
先只读确认正式五份文档、功能 31 tracked modified + 28 untracked、
八份旧 migration hash 及产品 0004 不存在；不符立即停止。

授权新增且仅新增诊断源码 scripts/f009_step5_storage_breakdown.py、
backend/tests/test_storage_breakdown_step5.py，并创建唯一临时子根
E:\Agent\cyber-town-f009-step5-tests\storage-breakdown-v2。
这些源码只做诊断，不改产品。子根仅允许 synthetic 三 SQLite、
pytest/TEMP、metadata-only 页归属/计数 JSON，无 .env 或真实秘密。
保留至 Step 5 收口，由用户手动删除，Codex 不删除。

按修订方案 D0 先写失败优先的诊断正确性测试，再以 fresh v3 与原
固定十索引候选各执行完整 100 unique execution 的 FakeProvider
工作量。只在新实验库应用原十索引清单，不更改表布局或唯一约束。
只分析新生成且已关闭/checkpoint 的 control/observability 文件；
不得连接、复制、修改或覆盖旧证据库，旧证据仅读取 metadata JSON。
分别报告表、必要约束索引、非唯一索引、overflow、页内闲置、
freelist、WAL/SHM；物理页归属总数必须守恒，不能用 cell 估算替代。
若不能可靠归属、指标/完整事件不一致或需要新增依赖/扩展，停止报告。
此步骤只做诊断，现有空间超限是预期已知缺陷，不能宣称修复。

只使用既有解释器；不创建 .venv，不安装依赖；运行前报告各精确子路径，
pytest basetemp 使用正斜杠且不可复用已存在目录，TEMP/TMP 固定新子根；
不创建授权外缓存。允许诊断专项测试、ruff no-cache、format check、
复用现有 mypy cache 的定向检查以及 tracked/untracked whitespace。
不读取 .env，不访问外部服务，不调用真实模型，不触及 F-005 资源。

完成后只在正式五份文档更新空间分解、候选 B 的可行性判断、缺口和
资源准确盘点，报告并停止，等待单独的布局预验证授权。
不创建 migration，不降低冻结阈值，不关闭 P1/Step 5，
不进入 Step 6，不提交、推送、PR、部署或删除资源。
```

本轮最终为 `step_5_performance_fix_blocked / awaiting_revised_plan_confirmation`；**仅修订方案完成，P1/Step 5 未完成**。下一次用户若采用上述 Prompt，只授权 D0，不自动获得候选 B、两份产品 `0004`、连接修复或 D4 的权限。

## D0 空间归属诊断启动（2026-08-27）

用户“授权继续修复”按上一建议执行 D0，已先向用户说明不自动开展候选 A/B、产品迁移或连接修复。预检通过：正式 main 五份文档、功能指定分支 31 tracked + 28 untracked，HEAD/本地 origin 为 1a4fc2c；八份迁移哈希一致，产品 0004 不存在。原 59 个功能文件的聚合 SHA-256 为 `809d7b59b1d88b8a22c05223f64429c07683406064ff5742c22845e75cb94587`，用于结束时验证既有实现未改动。

新根 `E:\Agent\cyber-town-f009-step5-tests\storage-breakdown-v2` 已于 `2026-08-27T12:06:09.4873610+08:00` 创建，canonical parent 为原 Step 5 根，0 reparse。所属 F-009 Step 5/D0，状态使用中，保留至 Step 5 收口，由用户手动回收、Codex 不删除。仅允许 `tmp`、`baseline-v3`、`candidate-indexes` 和 `summary.json`：synthetic 三库、运行临时文件、metadata-only 页归属摘要；不含真实 payload/秘密。当前只创建根及空 tmp；专项页解析测试使用内存 SQLite，不生成测试数据库文件。不创建新 venv、缓存或读取旧证据数据库。

## D0 完成：真实物理页分解，不代表 P1 已修复（2026-08-27）

### 方法、红测与正确性

只新增 `scripts/f009_step5_storage_breakdown.py`、`backend/tests/test_storage_breakdown_step5.py`；原 59 文件结束时聚合指纹与启动值一致。未修改产品实现或旧诊断脚本。红测为缺模块的 1 个收集错误；实现后 D0 专项 12 passed，加原索引纯函数 3 项共 15 passed；ruff、两个文件 format check、2 source mypy、tracked/untracked whitespace 通过。首次 lint 的 import 排序/raw regex 提示仅在新测试文件修正，未扩大范围。

按 investigate 方法先验证诊断器，而不是用估算证明修复：内存 SQLite 测试覆盖 512/4096/65536 页、表/索引内部与叶节点、部分索引、overflow、freelist、损坏头/截断/保留字节/未知 pointer-map、遗漏/重复 root、重叠 cell、固定错误码及 sentinel。解析仅读取页头、指针和 cell 长度，不解码/输出记录值；页内 payload+结构+闲置、对象页总和+freelist 与整个文件逐级守恒，不能可靠归属即 fail-closed。

实际两组仅在新子根：baseline-v3 和 fixed-ten-index，各 fresh 100 unique execution，经 in-process ASGI HTTP→FastAPI→DialogueService→FakeProvider→三 SQLite。每组 100 completed/100 dispatch、100 trace/1400 stage/300 cost/200 retry-breaker，control admission/permit/owner/reservation/settlement/result 各 100、bucket 302、breaker 1；业务 relationship state/event 各 100，长期记忆表为 0。行数一致、integrity 通过、FK 错误 0、stage 异常 0、fake cost 0；这不是完整记忆/取消/restart 评估或真实 TCP 延迟验收。

只对新 control/observability 在完成 checkpoint、关闭 SQL 连接且 WAL 为 0 后读取文件页；旧证据只读 JSON，未连接/复制旧数据库。四个新 metadata SQLite 与 JSON 共 5 个 surface，110 个 synthetic raw scope/message/reply/system prompt/key sentinel 命中 0；业务 SQLite 不进行原始页内容分析。未读取 `.env`、访问外部服务或 F-005 资源。

### 物理占用增长结果（每组 100 次执行）

| 口径 | control | observability | 两库合计，不含业务 |
| --- | --- | --- | --- |
| baseline 主文件 / 占用 | 304 / 304 KiB | 940 / 940 KiB | 1244 / 1244 KiB |
| 固定十索引候选主文件 | 264 KiB | 644 KiB | 908 KiB |
| 固定十索引候选占用 | 280 KiB | 668 KiB | 948 KiB |
| 冻结上限 | 256 KiB | 512 KiB | 768 KiB |
| 本轮仍超出 | 24 KiB | 156 KiB | 180 KiB |

候选初始 control/observability 的 4/6 页 freelist 最终均为 0，排除复用后得到上述占用值。业务库各增长 60 KiB，单列、不混入 combined。本轮 668 KiB 与上次 672 KiB 均是独立观测；新 trace/execution ID 和运行计时未固定为逐字相同，不能把几页差异归因于修复，也不能取较小一次数字宣称门禁通过。最终仍须原定 warm-up + 5-run。

| 候选占用增长的实际归属 | control | observability |
| --- | --- | --- |
| 表 B-tree | 180 KiB | 360 KiB |
| 必要 PK/UNIQUE 索引 | 76 KiB | 232 KiB |
| 保留非唯一索引 | 24 KiB | 76 KiB |
| schema 增长 | 0 | 0 |
| 合计 | 280 KiB | 668 KiB |

- control 最大对象：token_buckets 表 40 KiB、其 PK 28 KiB；admission/owner/permit 表各 32 KiB。observability：stage 表 156 KiB、cost 表 112 KiB、stage UNIQUE(trace,stage) 104 KiB、stage PK(trace,sequence) 72 KiB。数值是新旧对象占用页差，不是将 record cell 估算转称物理下界。
- 候选页内闲置最终绝对量 control 162,970 bytes（gap 148,897/freeblock 14,072/fragment 1）、observability 239,491 bytes（gap 221,360/freeblock 18,044/fragment 87）。初始分别已有 118,867/171,301 bytes；闲置增量仅 44,103/68,190 bytes，不能把终态闲置全部当作每 100 次执行可节省量，更不能承诺跨对象回收。control 非唯一索引的闲置增量为负，表示利用了初始页内空间，不是负文件大小。
- control 无 overflow；observability 唯一 overflow 属于 sqlite_schema，初末均有，不构成本次执行增长。新子根最终 WAL/SHM 均不存在；请求对结束时采样也为 0，**不是持续监测的运行峰值结论**。

### 对候选 B 的判断与停止点

八叶表独立 PK 索引的实测增长为 control 52 KiB（bucket 28，其余三表各 8）、observability 112 KiB（stage 72/link 8/cost 20/retry 12）。control 的键重复值得验证；observability 即使先假设 112 KiB 全可消除，仍有 44 KiB 差额没有解释。这只是算术压力检查，**不是 WITHOUT ROWID 的净收益估算或可行性下界**：新的主键表结构、保留索引定位键及页填充都会改变，可能增加而非减少体积。

D0 足以定位对象类别，但不足以直接批准产品 `0004`。若继续，建议只确认 D1 八叶表 synthetic 布局预验证，页大小固定 4096、原十索引清单不扩展；不同时试候选 A 或连接修复。对照须固定 synthetic 输入/ID/时钟/执行顺序，或明确报告无法固定因素与重复性限制，不把随机页填充差异当作因果收益。空间任一超限、逻辑约束改变、事件不完整或需要新增表/索引/依赖，立即停止，不落产品迁移；D1 通过后仍需单独的 D2 授权。

### 资源终盘与处置建议

| 准确路径 | 当前内容 | 处置 |
| --- | --- | --- |
| `E:\Agent\cyber-town-f009-step5-tests\storage-breakdown-v2` | 7 files / 3 dirs / 3,481,274 bytes：6 synthetic SQLite 3,235,840 bytes、metadata summary 245,434 bytes；tmp 为空，无 WAL/SHM | D0 已结束，建议暂留作为后续方案依据。若用户决定放弃实验，可手动删除此精确子根，不影响源码；删除不可恢复 |
| `E:\Agent\cyber-town-f009-step5-tests` | 含上行，93 files / 36 dirs / 39,557,163 bytes：78 SQLite、5 JSON、旧 5 WAL(0 bytes)/5 SHM(163,840 bytes) | Step 5 尚未结束，建议保留，不与子根重复删除 |
| `E:\Agent\cyber-town-f009-step5-tests\index-v4-preflight` | 15 files / 2 dirs / 3,403,285 bytes，与开始前相同 | 旧失败证据，未打开数据库、未覆盖，继续保留 |
| `E:\Agent\comprehensive-cases\15-cyber-town-f009\.ruff_cache` | 5 files / 6,682 bytes | 本轮 no-cache，保留到交付后单独处理 |
| `E:\Agent\comprehensive-cases\15-cyber-town-f009\.mypy_cache` | 3 files / 38,158,565 bytes | 复用既有缓存；mypy 正常维护后 16-byte missing_stubs 标记不再存在，未执行缓存清理命令；保留到交付 |
| `E:\Agent\comprehensive-cases\15-cyber-town-f009\game\.godot` | 6 files / 3,079 bytes | 未运行 Godot，保持保留 |

上述目录 0 reparse/env-like/nested Git/hidden/read-only。实验根位于 Git 外，tracked/untracked/ignored 不适用；三类 worktree cache 均 ignored。新子根 7 文件独占只读打开检查无占用；未创建功能 `.venv`、`.pytest_cache` 或授权外缓存。四类后续目录中仅 storage-breakdown-v2 本次创建，layout-preflight-v2/migration-v4-tests/performance-v2 均仍未创建。

需要手动放弃 D0 证据时，再确认没有新进程使用它，由用户执行：

```powershell
Remove-Item -LiteralPath 'E:\Agent\cyber-town-f009-step5-tests\storage-breakdown-v2' -Recurse
```

只影响新 D0 6 库和摘要；不删除父目录、旧证据、worktree、缓存或分支。当前建议保留，不要求立即删除，Codex 不代删。

证据索引：`E:\Agent\cyber-town-f009-step5-tests\storage-breakdown-v2\summary.json`，SHA-256 `381b27124e187208a9ec53ba86e7c26634002f9fab586c0e1c8c0625aae5fe84`。诊断进程 exit 0 仅代表页归属/事件检查完成；报告仍列三项 known_growth_failures，不代表性能或 P1 通过。

### 下一建议授权：D1 仅八叶表布局预验证

```text
批准 F-009 Step 5 P1 的 D1：仅进行候选 B 的 synthetic 空间预验证。
不得实施产品迁移、连接修复、完整性能矩阵或进入 Step 6。

先核对正式目录 main/五份文档，功能目录
E:\Agent\comprehensive-cases\15-cyber-town-f009 位于
feat/f-009-safety-cost-performance，HEAD/本地 origin/main 均为
1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3；功能 31 tracked modified
+ 30 实际 untracked，八份旧 migration 哈希不变，产品 0004 不存在。
任何差异停止，不 reset/stash/覆盖/切换分支或自行调整基线。

仅授权新增 scripts/f009_step5_layout_preflight.py、
backend/tests/test_layout_preflight_step5.py，以及新临时子根
E:\Agent\cyber-town-f009-step5-tests\layout-preflight-v2。
仅 synthetic 三 SQLite、pytest/TEMP 与 metadata-only 摘要；
保留至 Step 5 收口，由用户手动删除。不得修改或复用旧证据数据库。
所有实际子路径创建前报告；只用既有解释器，不建 venv/安装依赖，
pytest 路径用正斜杠且不复用已存在 basetemp；不创建授权外缓存。

页大小固定 4096；只在新实验库预验证以下叶表的 WITHOUT ROWID：
control：token_buckets、provider_permits、budget_settlements、
breaker_execution_results；observability：trace_stage_events、
execution_links、safety_cost_events、retry_breaker_events。
这是实验库物理表重建授权，不是产品 0004 或正式库迁移授权。
保留全部字段/默认值/NOT NULL/PK/UNIQUE/FK/CHECK/STRICT 语义；
非唯一索引只限原 control 4 + observability 6，其他具名索引和
dispatch owner 唯一约束全部保留；不关闭 FK、不丢弃或修复数据。

失败优先验证布局、所有约束和重复/NULL拒绝、原子回滚；再用同规模
100 unique execution/三 NPC/FakeProvider/完整三库写入对照，
保持 14-stage 增量持久化、durable open/restart abandoned 与业务语义。
使用 D0 已验证的页归属分析器，固定 synthetic 输入/ID/时钟/顺序，
报告初末物理/占用/freelist/页内闲置和 WAL/SHM，业务增长单列。
control/observability/combined 仍须 <=256/512/768 KiB；
不通过即停止，不扩大八表/十索引，不预分配/VACUUM/减少事件制造通过。

只运行专项、定向 lint/format/mypy/diff 与约束/完整性检查。
结果及准确资源清单仅更新正式五份文档。通过也须停止等待 D2 授权；
不创建产品 0004、不改旧 migration/Dialogue v1/Godot/冻结阈值。
不读取 .env、不访问外部服务或 F-005 资源；
不提交、推送、PR、部署或删除资源，不关闭 P1/Step 5。
```

最终状态 `step_5_storage_diagnostic_complete / awaiting_layout_prevalidation_authorization`。P1/Step 5 仍阻塞；正式五份文档、功能 31 tracked + 30 untracked，新增仅两个诊断文件；无产品 `0004`，八份旧 migration 与正式数据库边界不变。

## D1 授权与执行台账（2026-08-27）

用户已单独批准候选 B 八叶表 synthetic 空间预验证。当前仅 D1 执行中，P1/Step 5 不关闭；不授权 D2、产品 0004、连接修复、完整性能矩阵或 Step 6。预检通过：正式 main 五份文档；功能指定分支 31 tracked + 30 untracked；两处 HEAD/本地 origin/main 为 `1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3`，八份旧迁移哈希一致，无产品 0004。

新资源唯一根 `E:\Agent\cyber-town-f009-step5-tests\layout-preflight-v2`，D1 创建日期 2026-08-27，责任 F-009 Step 5 P1 D1，状态使用中。下属 `tmp`（TEMP/TMP）、`baseline-v3`/`candidate-b`（各 business/control/observability.sqlite3 及按需 WAL/SHM）、`restart/observability.sqlite3`（独立重启验证）与 `summary.json`（metadata-only）。pytest 预留互不复用的 `pytest-red-01`、`pytest-green-01`、`pytest-final-01`，不使用 tmp_path 时不创建。无真实数据/秘密/外部调用；仅新 synthetic 数据库，不打开旧证据数据库。保留至 Step 5 收口，由用户手动删除，Codex 仅盘点与复核。

文件系统创建时间 `2026-08-27T12:49:23.1161241+08:00`（启动登记采样时间为 `12:49:23.1824890+08:00`）。首轮诊断启动后发现配对摘要漏排除业务迁移台账 `applied_at`（只排除了 ms/ns 两列）；新增三种字段的负向测试证实 1 failed/2 passed。仅中止本轮拥有的诊断子进程，保留未完成库，不将首轮作为空间验收。只修正新诊断脚本的摘要口径，工作负载时间字段仍纳入对照。重新运行前已报告同一授权根下新增 `paired-fixed`，内含 `baseline-v3`/`candidate-b` 各三库与按需 WAL/SHM、`restart/observability.sqlite3`、`summary.json`；不复用首轮库。问题为诊断器遗漏，不是产品缺陷或布局门槛失败，不改变候选八表/十索引。

### D1 最终验证与停止结论

- 仅新增 `scripts/f009_step5_layout_preflight.py` 和 `backend/tests/test_layout_preflight_step5.py`。初始红测为缺模块 1 collection error；布局/约束专项初次 30 passed，补齐迁移时钟测试后 D1 33 + D0 12 + 固定索引 3 = **48 passed**。ruff、format check、定向 mypy（2 source files）和 tracked/untracked whitespace 通过。mypy 首次命令遗漏 MYPYPATH，修正为本 worktree 的 `backend/src` 后通过；未安装依赖或新建 venv。
- 实验库逐表复制原 DDL 的字段/默认值/NOT NULL/PK/UNIQUE/FK/CHECK/STRICT，仅改变指定八表的物理组织；原十个非唯一索引以外的全部具名索引及 dispatch-owner UNIQUE 保留。所有字段变异、PK 重复、NOT NULL、FK/STRICT/nullable 行为配对验证通过；四个重建边界分别注入故障，两类库均原子回滚到同一内存镜像。外键未关闭，未丢弃/修复记录，无 VACUUM/预分配。
- 完整对照位于 `layout-preflight-v2/paired-fixed`，创建时间 `2026-08-27T12:58:54.8894181+08:00`。两组各 **100 unique execution、100 completed、100 dispatch、1400 stage、300 cost event、200 retry/breaker event**；各 100 durable-open、1300 增量 progress 从新连接读回。terminal 为第 14 阶段，在既有 finish 事务落库，没有减少或延后既有承诺。关系状态/事件各 100；普通 synthetic 消息无长期记忆写入意图，长期表为 0，未用此对照冒充完整业务矩阵。
- 请求/trace/execution/关系事件 ID、synthetic HMAC key、业务/观测时钟和串行执行顺序均固定。两组三库逻辑行 digest 完全相同，仅排除 schema_migrations 三种建库时间字段；业务时间仍参与 digest。business/control/observability digest 分别为 `99ac7888a8bc4fadff4b2d4de7ed1513ede034d08e82ea0dfc269eb237e68aeb` / `b167e5efb89fb707326c49b7977a66c5fb1b6855c4d58fc7d095334e29cd9bc6` / `a568af01e8ed7c9574d22f2443f43e3be9bc36cacbe39f276df22ad98a37ecfa`。这不是三进程 evaluator digest 门禁。
- 单独 restart 库：先保留完整 trace，再将 open trace 的 9 个阶段逐次提交并读回；重建 repository 后只收口 1 个 abandoned，两个 trace 共 28 stages，completed 原记录/阶段不变；再次 recovery=0、完整行 digest 不变。integrity_check 全部 ok，FK/stage 异常 0，fake 成本 0。

| 每 100 次执行 | control | observability | combined（不含业务） |
| --- | --- | --- | --- |
| 本轮 baseline-v3 主文件/占用增长 | 304 KiB | 944 KiB | 1248 KiB |
| 候选 B 主文件增长 | 204 KiB | 588 KiB | 792 KiB |
| 候选 B 占用增长（排除初始 freelist 复用） | **232 KiB** | **632 KiB** | **864 KiB** |
| 冻结上限 | 256 KiB | 512 KiB | 768 KiB |
| 占用门禁 | 通过，余 24 KiB | **失败，超 120 KiB** | **失败，超 96 KiB** |

业务库两组各增长 60 KiB，单列不计 combined。页大小始终 4096。候选 control 主文件 144→348 KiB、占用 116→348 KiB，freelist 7→0；observability 主文件 212→800 KiB、占用 168→800 KiB，freelist 11→0。基线 freelist 初末均为 0。由 D0 页归属分析器逐页核算，所有页/字节守恒、unaccounted=0；并非以 cell 估算代替物理增长。

| 候选占用增长归属 | control | observability |
| --- | --- | --- |
| 表 B-tree | 184 KiB | 416 KiB |
| 必要约束索引 | 24 KiB | 108 KiB |
| 保留非唯一索引 | 24 KiB | 108 KiB |
| 合计 | 232 KiB | 632 KiB |

对照原布局的 observability 表增长为 360 KiB，候选为 416 KiB：去掉独立 PK B-tree 并非等额净节省；WITHOUT ROWID 主键表及保留索引定位键也占空间。候选 stage 表增长 184 KiB、cost 表 136 KiB、stage UNIQUE 92 KiB。以上是本轮有序数据的实际页增长，不是物理下界，不与 D0 不同 ID/时钟的 668 KiB 简单相减来宣称独立布局收益。

页内闲置（bytes）：候选 control 106812→140795（gap 105270→124020、freeblock 1542→16774、fragment 0→1），observability 151082→254264（gap 151069→219886、freeblock 13→34226、fragment 0→152）。基线为 control 134515→183026、observability 194811→296563。control 无 overflow；observability 的 schema overflow 初末均为 1 页，不构成执行增长。完整对照的请求结束采样及终态 WAL/SHM 均 0；不代表运行期连续峰值。首轮中止遗留 WAL/SHM 独立列入下方台账，不隐藏。

6 个有效新 metadata surface（4 个 control/observability 库、restart 库、summary）对 110 个 raw scope/message/reply/system prompt/key sentinel 的只读扫描命中 **0**；未扫描业务原始页或打开旧证据库。摘要 `E:\Agent\cyber-town-f009-step5-tests\layout-preflight-v2\paired-fixed\summary.json` 为 234635 bytes，SHA-256 `8e9feef5a6d18b38983027fb275020afc04b59d4d7756a1e80d93babdbdf72e0`。

实验 exit 1 明确对应 `observability_growth_exceeded`、`combined_growth_exceeded`，不能转称通过。**D1 未通过，D2 前置条件未满足；P1/Step 5 保持阻塞。** 未实施产品 0004、连接修复、完整矩阵、evaluator/三进程/故障组合；不进入 Step 6。下一步只能等待用户重新确认存储方案边界，本轮不扩大八表/十索引、不放宽阈值，也不承诺现边界内必然可修好。

### D1 资源终盘与手动处置

| 准确绝对路径 | 文件/子目录/bytes | 当前内容与建议 |
| --- | --- | --- |
| `E:\Agent\cyber-town-f009-step5-tests\layout-preflight-v2` | 17 / 8 / 6526123 | 本轮总根，14 SQLite=6258688 bytes、1 JSON=234635、1 WAL=32、1 SHM=32768；D1 已停，按授权保留至 Step 5 收口，Codex 不删除 |
| `E:\Agent\cyber-town-f009-step5-tests\layout-preflight-v2\paired-fixed` | 8 / 3 / 3572875 | 有效失败证据：7 SQLite=3338240 bytes + summary；无 WAL/SHM，建议保留 |
| `E:\Agent\cyber-town-f009-step5-tests\layout-preflight-v2\baseline-v3` | 3 / 0 / 1794048 | 首轮中止实验组成部分，不计入验收；可由用户手动删除，但当前依保留期限暂留 |
| `E:\Agent\cyber-town-f009-step5-tests\layout-preflight-v2\candidate-b` | 5 / 0 / 942112 | 首轮中止 3 库=909312 bytes + 32-byte WAL/32768-byte SHM，不重新连接/修复；同上 |
| `E:\Agent\cyber-town-f009-step5-tests\layout-preflight-v2\restart` | 1 / 0 / 217088 | 首轮独立重启库，不计最终对照；同上 |
| `E:\Agent\cyber-town-f009-step5-tests` | 110 / 45 / 46083286 | 含 D1 总根；92 SQLite、6 JSON、6 WAL(32 bytes)、6 SHM(196608 bytes)，Step 5 未结束，继续保留，不重复累计子根 |
| `E:\Agent\cyber-town-f009-step5-tests\storage-breakdown-v2` | 7 / 3 / 3481274 | D0 旧证据，盘点未变，未打开 SQLite，继续保留 |
| `E:\Agent\cyber-town-f009-step5-tests\index-v4-preflight` | 15 / 2 / 3403285 | 旧索引预验证证据，盘点未变，继续保留 |
| `E:\Agent\comprehensive-cases\15-cyber-town-f009\.ruff_cache` | 5 / 1 / 6682 | ignored；本轮 no-cache，保留至交付 |
| `E:\Agent\comprehensive-cases\15-cyber-town-f009\.mypy_cache` | 3 / 1 / 38199525 | ignored；既有缓存正常维护，保留至交付 |
| `E:\Agent\comprehensive-cases\15-cyber-town-f009\game\.godot` | 6 / 2 / 3079 | ignored，未运行 Godot，保留至交付 |

D1 根及全部父路径为普通目录，0 reparse/env-like/nested Git/hidden/read-only；17 文件独占只读打开检查无占用。实验根不在 Git 仓库内，tracked/untracked/ignored 不适用。`tmp` 为空，三个预留 pytest basetemp 均未创建；无新 venv、pytest/bytecode 缓存。功能 worktree 与分支继续保留，当前不能删除含未提交功能的 worktree。

若用户选择丢弃首轮非验收产物，可在确认无新进程使用后**手动**删除上表首轮 `baseline-v3`、`candidate-b`、`restart` 三目录（合计 2953248 bytes）；不要误删 `paired-fixed`。Step 5 收口或明确放弃证据后，可只删除整个 D1 总根：

```powershell
Remove-Item -LiteralPath 'E:\Agent\cyber-town-f009-step5-tests\layout-preflight-v2' -Recurse
```

只影响本轮 synthetic 库/sidecar/摘要，不影响源码、旧证据、分支或缓存；没有备份时不可恢复。不要删除父目录，不使用 `-Force` 绕过变化；出现占用/边界差异先停止并重新审计。当前建议保留，Codex 未执行任何删除。

Git 终检：正式 main 仅五份文档；功能分支仍 31 tracked + 32 untracked，新增仅授权两文件。原 61 文件聚合指纹仍 `957571e5b7a92418c84af1bef8313ca7eb52ce066a7cd83a91328538d8a3f45f`；两目录 HEAD/本地 origin/main 均为 `1a4fc2c`，八份旧 migration hash 不变，产品 0004 不存在。正式与功能目录三类正式数据库均不存在，8000 无 listener。不读 .env、不访问外部服务/F-005、不提交/推送/PR/部署。

## P1 续修调查：紧凑存储边界待确认（2026-08-27）

用户授权解决当前问题，完整目标仍为解决空间及延迟 P1、通过冻结性能矩阵并恢复 Step 5 后续验证，不缩成“写完方案”。本轮先只读核对：正式 main 五文档、功能指定分支 31 tracked + 32 untracked、两处 HEAD/本地 origin/main `1a4fc2c`、八旧迁移 hash 和 D1 summary hash 均符合；无产品 0004。未测试、创建资源或修改功能文件，仅补充本节与阶段文档。

此前已明确禁止新增字段编码，并要求不改变列类型/默认值/CHECK 物理表达；通用“解决问题”授权没有明确撤销这项限制。因此先提出精确例外供用户确认，不默认把它解释为任意 schema 重构权限。investigate 的根因优先/架构歧义停止规则用于此处，不运行其遥测、外部同步、自动提交或删除流程。

### 有据可查的修复方向

- 空间：D1 的观测库 stage 表增长 184 KiB（payload 增长149500 bytes），cost 表136 KiB（payload105700 bytes），stage UNIQUE92 KiB（payload80900 bytes）。源 SQL/仓储确认阶段、结果、reason/error、policy 文字重复入库，cost 每事件还写入三个64字符 HMAC tag。不能从这些字节推导必然可回收120 KiB，但比继续微调页大小/填充更直接针对记录宽度。
- 延迟：既有 metadata-only `profile-before-2.json` 再次核对为4次执行、127 connect/close、123 commit；commit约0.865s、close约0.670s。仓储每次操作重新连接并设置 WAL，退出即关闭。连接生命周期可作为独立修复对象；证据尚不证明具体 checkpoint 归因或最终加速倍数，必须复测，不能减少逐 stage 提交或降低同步强度。
- 原八表/十索引保持不扩展；control 采用已验证的 B 物理布局，不新增编码。observability 只在原四叶表增加可逆编码，父表 trace_runs 和业务库不动。无需外部数据库、扩展、依赖、字典表、通用压缩或云服务。

### 候选 C：需要新增批准的精确字段表示

| 表 | 候选物理变化 | 不变边界 |
| --- | --- | --- |
| trace_stage_events | stage/outcome/reason_code/error_code/retention_status 由 TEXT 固定枚举改为固定 INTEGER code | trace_id 仍 TEXT 引用父表；sequence 1..14、schema_version、时间/计数不变；stage/sequence 一一对应、PK(trace,sequence)、UNIQUE(trace,stage) 语义保留 |
| execution_links | link_kind/retention_status 改固定 INTEGER code；execution_id 从 canonical UUID TEXT 改16-byte BLOB | trace_id及其FK不变；唯一 dispatch-owner 和共享 waiter/local execution 规则不变 |
| safety_cost_events | event_kind/provider_kind/outcome/policy_version 改固定 INTEGER code；execution_id 改16-byte BLOB；三个 HMAC scope tag 改32-byte BLOB | trace_id FK、attempt/金额/token/时间和 pricing_version TEXT不变；PK三元归属不变，HMAC算法/key/领域分隔不变 |
| retry_breaker_events | event_kind/policy_version/retry_outcome/breaker_state/breaker_outcome/可空failure_reason 改固定 INTEGER code；execution_id 改16-byte BLOB | trace_id FK、attempt/backoff/jitter/deadline/时间不变；NULL含义、PK及状态规则不变 |

这是改变指定列的 SQLite 存储类型及 CHECK/default 的等价表达，**不是保持原 SQL 字段类型不变的方案**。不改变字段名、PK列及次序、FK目标/动作、唯一性或允许的有效业务状态；其余具名索引与原十索引边界保持。DTO、trace schema、CLI和HTTP继续输出原枚举文字、canonical UUID和64位小写HMAC tag；仓储负责严格 encode/decode。

固定映射须显式、版本化、可逆，不能依赖 enum 声明顺序生成漂移编码；未知码/超长或错误 BLOB/版本不匹配 fail-closed，错误不得回显原值。旧数据先完整校验再转换；发现非法旧值、碰撞、FK/CHECK失败则整库迁移事务回滚，不修复、丢弃或截断数据。对受支持有效值证明 round-trip、查询排序/过滤及幂等一致性；不得承诺旧程序直接读新物理库。

候选文件范围：`observability/sqlite_observability.py` 读写/查询/recovery/retention边界，新增同目录 `storage_codec.py`；`control/sqlite_control.py` 迁移清单；两份候选 `control/migrations/0004_leaf_table_storage_layout.sql`、`observability/migrations/0004_compact_event_storage.sql`；现有仓储测试及新的 codec/迁移测试、synthetic 预验证脚本。**本轮均不创建/修改**；预计超过5个文件，需用户确认影响面。旧八份 migration hash不变，追加而不改写。

### 确认后的失败优先顺序与停止点

1. 先独立验证codec的有效值round-trip、未知值/秘密不回显、跨scope不可混淆；验证表约束、NULL/重复/唯一dispatch-owner、事务故障回滚和旧库异常整库拒绝。
2. 只在新synthetic库中验证C：固定4096页、100 unique execution/三个NPC/完整三库写入、固定ID/时钟/顺序、14-stage增量和重启收口。用现有页归属分析器报告初末main/occupied/freelist/页内闲置/WAL/SHM，业务增长单列；比较解码后的逻辑行digest，不比较不同物理编码的原始行digest。control/observability/combined仍<=256/512/768KiB。预验证失败立即停止，不扩大四叶表编码或十索引清单，不挑最好一次，也不做产品迁移。
3. 只有空间/语义通过且本节完整续修权限获准，才失败优先实施两份产品append-only0004及fresh/v3升级、原子回滚、查询/CLI/retention/recovery验证。不得打开既有验收/证据库或创建正式data库；两库各自原子，不冒称跨库原子。
4. 再独立验证有界连接复用：保持每次事务提交、WAL/synchronous强度、逐次路径与reparse校验、取消/并发/异常回滚与关闭职责；不合并事件、不延后durable open/stage承诺。必须计数证明连接下降而提交语义未变，再比较真实本地HTTP逐请求计时。
5. 完整warm-up+5-run矩阵，修正combined只计两库和in-memory同工作量配对；全部绝对/相对阈值通过后才恢复Step5 evaluator、三进程digest、故障组合和完整回归。仍不进入Step6或Git交付。不保证候选C一定足够；新越界需求或失败停止报告。

### 待批准资源及回收

仅提出、不创建：`E:\Agent\cyber-town-f009-step5-tests\compact-preflight-v1`（新synthetic三库、codec/约束pytest/TEMP、metadata-only摘要）；通过后才用既有规划 `E:\Agent\cyber-town-f009-step5-tests\migration-v4-tests` 和 `E:\Agent\cyber-town-f009-step5-tests\performance-v2`。所有具体子路径仍须创建前报告，不能覆盖或复用D0/D1/索引预验证证据。只用既有解释器，不建venv/安装依赖；pytest basetemp用新正斜杠路径，缓存只复用获准既有目录。

所属F-009 Step5 P1，数据仅synthetic/FakeProvider/metadata，无.env/真实秘密/原始对话/F-005资源；保留至Step5收口，台账写本任务卡/evidence，Codex只盘点，由用户手动回收。当前现有资源继续保留，本轮新增资源0。仍保持 `step_5_layout_prevalidation_failed / awaiting_revised_storage_decision`，目标未完成，等待用户明确批准上述物理编码例外及分阶段续修。

## 候选 C 明确授权与执行台账（2026-08-27）

用户已明确批准上节原四 observability 叶表的物理编码例外；先 synthetic 空间/语义预验证，通过后才追加迁移、连接修复及 Step 5 后续验证，失败立即停止，不进入 Step 6。原八表/十索引、旧 migration 哈希、冻结阈值、14-stage 与业务语义保持。预检：正式 main 五文档，功能指定分支 31 tracked modified + 32 untracked，两处 HEAD/origin/main 均 1a4fc2c，八旧 migration 哈希匹配。旧证据不打开/复用，无产品 0004。

资源根 `E:\Agent\cyber-town-f009-step5-tests\compact-preflight-v1`，责任 F-009 Step5 P1 候选 C，状态已批准待创建；父路径无 reparse，目标不存在。计划子路径：`tmp`（TEMP/TMP）；`pytest-red-01`、`pytest-green-01`、`pytest-final-01`（互不复用，未需要 tmp_path 时不创建）；`paired-fixed/baseline-v3`、`paired-fixed/candidate-c` 各含 `business.sqlite3`、`control.sqlite3`、`observability.sqlite3`；`paired-fixed/restart/observability.sqlite3`；`paired-fixed/summary.json`。所有 DB sidecar 仅相应 `-wal`/`-shm`。仅 synthetic 三库/约束测试与 metadata-only 摘要，不含真实秘密、原文、F-005 资源。保留至 Step5 收口，由用户手动删除，Codex 不删除。

预验证代码限 codec、实验适配器/脚本和专项测试；实验适配器保留原仓储事务与调用链，在 SQL 参数/结果边界验证编码，未注册产品 migration。性能不从此 ASGI 实验推导，仍须后续真实 HTTP 矩阵。

### C 空间/语义预验证通过，转入获准的追加迁移

性能根实际创建2026-08-27T14:02:21+08:00。profile-after完成：4HTTP completed/dispatch、56stage，18connect/close，127commit（旧直接service诊断123，真实HTTP新增4ingress事务）；提交语义另由16commit专项验证，不能将不同入口总量当完全同口径速度对比。profile-after.json仅metadata。已预告matrix-01及六组sqlite-observability、sqlite-reject-rate/budget/breaker、loopback-off/on各0、1、2、3、4、5子目录；前组仅observability.sqlite3，三拒绝组仅control.sqlite3，loopback各business/control/observability.sqlite3和各-wal/-shm，摘要performance-summary.json。只使用新数据，不覆盖profile或旧证据；保留至Step5收口，用户手动回收。核心绝对/相对门禁失败即停止其余场景与evaluator；未完成完整矩阵前不关闭P1。

固定对照 exit0：control/observability 占用增长 237568/430080 bytes，即232/420/652KiB，低于256/512/768KiB。各100 completed/dispatch、1400 stage、300cost/200retry-breaker、100durable-open/1300stage读回；三库解码后行digest一致；独立restart只收口1abandoned、completed不变、repeat0。业务增长61440bytes单列。6metadata surfaces/107sentinel命中0；summary SHA256 `d6b5bcfd898d9140ad3ac428b62ed69a1583a3714d1cfec3f600d5301bd273ff`。这只通过空间预验证，不代表性能/Step5完成。

按已批准条件开始两份产品0004及仓储编码集成；迁移注册红测为3!=4（1failed），追加SQL后内存迁移/codec70passed。原八迁移文件不改。新资源 `E:\Agent\cyber-town-f009-step5-tests\migration-v4-tests`，已批准待创建，责任F009Step5P1C；子路径 `tmp`（TEMP/TMP）、`regression-red-01`、`regression-green-01`（各自唯一pytest基根，子目录为synthetic用例隔离SQLite）。仅synthetic业务/control/observability及metadata，不含.env/嵌套Git/真实秘密/F005；保留至Step5收口，用户手动删除。性能根尚不创建。
连接/迁移扩展回归132passed，测量专项8passed。新增writer每仓储有界1连接，16次提交测试保持schema+open+13progress+terminal；跨线程串行、锁等待、回滚、路径检查、显式close测试通过。旧物理enum/版本断言已改为解码比较，不变更逻辑期望。完整性能尚未验证。

资源续登记（2026-08-27 14:03 +08，F009Step5P1）：migration-v4-tests内已用regression-red-01/green-01/final-01/final-02/final-03、connection-red-01/green-01/final-01、measurement-red-01/green-01。connection-red-01运行前遗漏单独子路径预告（仍在已授权根），已向用户披露；保留失败产物不删除。其后均创建前预告，不复用basetemp。性能根E:\Agent\cyber-town-f009-step5-tests\performance-v2即将创建，子路径tmp、profile-after/{business,control,observability}.sqlite3及各-wal/-shm、profile-after.json。仅synthetic/metadata，无真实秘密/env/F005；本地127.0.0.1临时端口HTTP profiling结束关闭。保留至Step5收口用户手动删除，Codex不删除。完整矩阵子路径后续另行先报告。
## C续修终检：空间通过、核心性能失败（2026-08-27）

当前状态以本节和文件开头为准；上面的D0/D1/C执行中记录保留为历史。用户明确授权的C编码预验证通过后才实施产品迁移/连接修复；核心性能门禁失败后停止，没有继续调参、改代码或运行剩余验收。

### 已实施与定向证据

- C预验证：control/observability占用232/420KiB，合计652KiB；原阈值256/512/768KiB。两组各100unique execution/三NPC、1400stage、300cost、200retry-breaker，100durable-open/1300progress读回；解码后三库digest相同，restart只收口1abandoned、重复0。summary SHA256 `d6b5bcfd898d9140ad3ac428b62ed69a1583a3714d1cfec3f600d5301bd273ff`。这是空间/语义证据，不是TCP性能验收。
- 产品追加：control/0004_leaf_table_storage_layout.sql、observability/0004_compact_event_storage.sql。原八迁移哈希不变，原八叶表/十非唯一索引范围不扩大。显式版本化codec只改变获准四observability叶表的物理编码，保留逻辑约束；新库/旧v3/重复初始化/失败事务回滚和CLI定向验证通过。
- 连接：control/observability各一个受锁writer，逐次路径检查；借用归还时回滚遗留事务，重置row_factory；保持FK/WAL/FULL同步和原提交边界，提供显式close。单trace专项为1次建连接、16次commit（schema+open+13progress+terminal），独立读连接逐stage可见；跨线程串行、超时、回滚/关闭通过。
- 红绿记录：codec缺模块红测；C专项57+既有48=105passed。产品迁移注册红测1failed（3!=4），内存迁移/codec70passed；扩展仓储首次5failed/46passed均为旧版本/物理文本断言，解码适配后53passed；再扩展后132passed。测量新增3failed/4passed，实现后8passed。新增连接测试曾因断言插入错位出现NameError，属于测试自身错误，纠正后计入132passed，不冒称产品缺陷。定向ruff/format和8文件mypy通过；不是最终全量质量门禁。
- profiling为4次真实TCP HTTP请求，18connect/close、127commit、4dispatch、56stage；旧直接service诊断为127connect/close、123commit，多出的4commit对应HTTP ingress。不能把不同入口耗时当完全配对收益。profile摘要SHA256 `60825f5373276e0c74b1c9a5d2ab6a506abce0414ddd9bc0fef69e322dcd9106`。

### 核心性能门禁与停止原因

每组warm-up1轮+正式5轮；三个内存/metadata组每轮1000样本，SQLite/HTTP/三类拒绝组每轮100。共18000个正式样本（不含warm-up），保留全部计时；HTTP逐请求计时，不再使用pair总耗时/2。in-memory组使用同一控制SQL工作量的synthetic内存SQLite配对，仅诊断，不是产品fallback。纯no-op metadata单独判定微秒级门禁。

| 核心指标 | 五轮统计 | 冻结要求 | 结果 |
| --- | --- | --- | --- |
| no-recorder metadata p95/p99 | 0.0002/0.0002ms | <=0.050/0.100ms | 通过 |
| in-memory+control p95/p99 | 5.0921/7.1039ms | <=2/5ms | 失败 |
| in-memory配对吞吐 | 346.943716 vs384.352768/s，约90.27% | >=80% | 通过 |
| SQLite observability p95/p99/吞吐 | 133.9627/151.7158ms、9.027181/s | <=150/200ms、>=8/s | 通过 |
| rate/budget/breaker reject p95 | 5.5845/4.5555/4.2306ms | <=50ms，dispatch0 | 通过，三组dispatch均0 |
| 完整HTTP control-off p95/p99 | 526.6708/613.4983ms | 配对基线 | 非control-on绝对门禁 |
| 完整HTTP control-on p95/p99/吞吐 | 787.5748/853.159ms、4.030231/s | <=250/400ms、>=4/s | 延迟失败，吞吐通过 |
| control-on相对p95增量 | 260.904ms | <=max(20%×526.6708,30)=105.33416ms | 失败 |

五个固定失败码：control_on_relative_p95_regression、full_loopback_p95_exceeded、full_loopback_p99_exceeded、in_memory_p95_exceeded、in_memory_p99_exceeded。命令exit1后立即停止后续实施/性能场景，P1未关闭。收口仅做只读检查：本轮17个Python文件ruff和format --check通过，两目录diff --check通过；没有因此重跑功能测试或声称最终全量质量通过。

空间口径已将combined限定为control+observability，业务单列。核心HTTP五轮占用增长control均228KiB，observability为428/424/420/424/428KiB，combined中位652KiB；业务每轮60KiB不计入combined。报告中main_bytes为page_count×4096的主库容量，file_bytes另列实际文件字节（起点schema仍可能在WAL）；不能把起点4096-byte主文件当作完整空库容量。单项observability占用304KiB。WAL/SHM为请求对边界采样，control/obs最大约4.14/4.18MB，各SHM32768；这不是全时段峰值，也未将WAL当成持久库增长。C的独立关闭/checkpoint空间证据保留，不能据核心部分结果宣布完整最终物理增长门禁完成。

尚未完成：完整矩阵的单scope串行、waiter/replay/retry/restart，以及真正长期记忆命令写入场景（核心HTTP使用普通对话，不把空长期事实表冒充写入覆盖）；Step5实际evaluator、三进程digest、组件故障组合、全量回归/schema/Godot/loopback与最终质量入口。旧定向回归不替代这些门禁。最终性能摘要SHA256 `631ce8eab06fea2ee29e6705f2b8533333103ddbebd6da630f98e4348069df52`。

### 隐私、Git与临时资源

只读终检：新performance-v2的152个control/observability/JSON surface，11类原始scope/message/reply/synthetic-key sentinel命中0；C的6个metadata surface/107sentinel命中0。未读取.env、F005资源或调用外部服务。八旧migration哈希一致；当前代码没有本轮新增Dialogue v1/Godot/业务迁移改动。原63个未提交文件中53个指纹未变，10个为获准仓储/测试/benchmark更新；另改既有observability_step5测试并新增8文件。正式main五文档，功能32tracked modified+40untracked，HEAD/本地origin/main均1a4fc2c；未提交/推送/PR/部署。tracked及40个untracked whitespace检查通过（旧LF/CRLF警告未通过改文件处理）。两处正式业务/control/observability库均不存在，8000无listener。worktree仅正式与F009。

盘点于2026-08-27 14:14—14:16 +08；全部Step5临时根无reparse、hidden/read-only、env-like文件、嵌套Git，不属于任何Git仓库，tracked/untracked/ignored分类不适用。SQLite有故意无效的synthetic负向样本；不将其当正式数据。

| 精确路径 | files / dirs / bytes | 状态与处理建议 |
| --- | --- | --- |
| E:\Agent\cyber-town-f009-step5-tests | 692 /449 /124839407 | 包含旧证据和以下三个子根，勿重复求和；Step5未结束，整体保留 |
| E:\Agent\cyber-town-f009-step5-tests\compact-preflight-v1 | 8 /5 /3355539 | 7synthetic SQLite+1metadata JSON；C空间证据，保留 |
| E:\Agent\cyber-town-f009-step5-tests\migration-v4-tests | 383 /357 /55357803 | 345synthetic SQLite、19WAL(0bytes)、19SHM；包含失败与成功回归，保留 |
| E:\Agent\cyber-town-f009-step5-tests\performance-v2 | 191 /39 /20042779 | 63synthetic SQLite、63WAL(0bytes)、63SHM、2metadata JSON；失败性能证据，优先保留 |
| E:\Agent\comprehensive-cases\15-cyber-town-f009 | 226 /41 /74901021 | 活动工作树，有未提交代码；不得手动递归删除，保留至交付并单独审计 |
| E:\Agent\comprehensive-cases\15-cyber-town-f009\.ruff_cache | 5 /1 /6682 | ignored，保留 |
| E:\Agent\comprehensive-cases\15-cyber-town-f009\.mypy_cache | 3 /1 /38273253 | ignored，本轮复用，保留 |
| E:\Agent\comprehensive-cases\15-cyber-town-f009\backend\.mypy_cache | 4 /1 /34480373 | ignored，00:09已存在的旧缓存，本轮未运行维护；补列盘点，保留 |
| E:\Agent\comprehensive-cases\15-cyber-town-f009\game\.godot | 6 /2 /3079 | ignored，本轮未运行Godot，保留 |

三个新子根共78756121bytes。工作树含167tracked、40untracked、18ignored文件及1个合法worktree .git指针；其唯一env-like文件为既有tracked .env.example(643bytes)，仅读名称/大小，未读内容；没有.env、.venv或.pytest_cache。root hidden项为.git指针，不是嵌套仓库。worktree/cache总量存在包含关系，不重复累计。

当前建议全部保留，勿删除仍需诊断的原始证据。若用户决定放弃某项本轮测试证据，在重新核对路径、reparse、文件数/大小与占用后，可仅手动执行相应一条命令；不可从Git恢复测试SQLite，后续重跑必须使用新的授权路径。不要删除父根、worktree或分支，不使用--force或Remove-Item -Force：

```powershell
Remove-Item -LiteralPath 'E:\Agent\cyber-town-f009-step5-tests\compact-preflight-v1' -Recurse
Remove-Item -LiteralPath 'E:\Agent\cyber-town-f009-step5-tests\migration-v4-tests' -Recurse
Remove-Item -LiteralPath 'E:\Agent\cyber-town-f009-step5-tests\performance-v2' -Recurse
```

以上仅为用户手动处置入口，不是本轮删除执行；遇到占用/边界差异应停止。Codex未删除任何资源。流程复盘：connection-red-01遗漏事前单独子路径预告，已披露；工作树盘点还补列旧backend/.mypy_cache，不能仅枚举已知顶层缓存。后续必须先列实际子路径，再创建；最后同时核对Git ignored集合。未改AGENTS或全局规则。

下一建议仅授权只读分析现有profile-after.json和performance-summary.json及相关源码，区分同步事务提交、路径校验、控制算法/SQL、业务库连接和HTTP排队开销，提出保持14-stage/同步强度/阈值的有界方案与证据不足点。本轮不再实施、不重测、不新增资源；若需要新的profiling或扩展连接改动，必须明确新范围和路径后另获授权。不保证剩余阈值在现有边界内可达标。
