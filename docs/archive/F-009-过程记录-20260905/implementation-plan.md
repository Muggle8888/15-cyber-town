# 当前实施计划

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

### B 恢复提案（未执行，等待用户恢复指示）

恢复原因与边界：用户明确要求验证失败即停止，因此本轮不能自行修正 QA 清单再跑。原七文件/外层 control-space-v1 授权仍有效；不需批准 quality-13，不引入 native 例外。拟仅在两个已授权 QA 文件中实现和验证“剩余 B”入口；产品、SQL、migration、阈值、既有测试中的 Godot 节点均不改。

1. 只读复核本节冻结 98 文件、branch/HEAD、原失败摘要、A 摘要和 semantic-summary-02.json / pytest-semantic-01/qa-summary.json 的身份及哈希。若出现非本次明确 QA 适配引起的变化则停止。校验历史 B 仅有此精确 Godot 节点失败、757 passed、55 历史 skipped，记录 inner guard 的一次拒绝，不把旧记录改为绿灯。
2. 以显式剩余文件清单继续五个未运行的 Python 文件；旧 757 项属于原 e44a... 快照，不能伪称新入口全部重跑。若 QA 入口有修改，只复核其相关选择/边界测试和必要静态门禁；产品及原测试字节不变的历史结果带哈希引用保留。发现影响已验语义的变化须重新界定验证，不能无条件继承结果。
3. 将上述精确 Godot 节点列为后续完整 native quality 待验；仍要求真实引擎/回环通过才能最终关闭 Step6。不得新增 pytest.skip、吞掉 guard 拒绝、放宽边界或将待验项计入通过。
4. 通过后执行原固定 25-case evaluator 三个全新 Python 进程，保留独立 digest 摘要和对比；已通过的 evaluator 单测不替代这三份报告。任一验证失败即停，不追加试跑。
5. 候选新资源均在已授权外层根 E:\Agent\cyber-town-f009-step6-qa\control-space-v1 内：pytest-semantic-02（全新 basetemp）、pytest-semantic-02\qa-summary.json、semantic-summary-03.json，以及仍未创建的 evaluator-process-01.json、evaluator-process-02.json、evaluator-process-03.json。当前仅提案，不视为创建许可或正式预登记。恢复后先将实际准确路径写入正式 evidence，再创建；pytest 每个动态子路径仍在创建前逐项登记。失败的 pytest-semantic-01 / semantic-summary.json / semantic-summary-02.json 全部保留，SQLite 不复用。
6. 沿用既有统一 command_scope / subprocess_isolation、QA TEMP/缓存隔离、canonical 完整父链无 reparse、fresh/文件身份/归属和退出恢复。A 不重跑。B 完成后只报告专项结果；完整 quality 及针对空间修复额外一次 warm-up+5-run 核心性能额度须按专项 C 单独授权执行，不能沿用已耗尽的原批次额度。不得进入 Step7。


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

## 2026-09-03：QA-F009-SPACE-01 空间超限专项修复方案（待授权实施）

当前状态：`step_6_blocked / control_storage_growth_fix_plan_ready / awaiting_fix_plan_authorization`。本轮用户要求“针对空间超限单独制定修复方案，无需先批准 quality-13”。本节是当前方案；下面保留完整执行历史。仅完成只读分析及正式五文档更新，未修改产品/测试/runner/SQL，未创建修复根或 quality-13，未重跑 quality 或性能。SPACE-01 仍为未关闭 P1；Step 6 未完成，Step 7 未开始。

### 1. 证据、目标与未知项

本批默认 control-on 的 control 增长为 260、260、256、260、260 KiB，中位数 260 KiB，超过冻结上限 256 KiB；三 SQLite 组的 control 中位数同为 260 KiB。冻结计算公式仍为 max(0, main_after-main_before, occupied_after-occupied_before)，不能通过改统计口径、选取一轮或调整阈值消除失败。

同批 loopback-on-1 与 loopback-on-3 的只读物理页核对显示：总页 97 对 96；唯一占页差异是 provider_permits 的 9 对 8 页；两库该表各 100 行、有效载荷各 28800 字节，无 overflow，完整页归属守恒。此证据定位了一页差异的物理对象，尚未证明具体 UUID 插入顺序、release 更新时机与页分裂的完整因果。没有证据把这次失败直接归因于 0008 预算投影修复。

修复目标：保留全部 permit、scope 归属、并发门禁、幂等、恢复和审计语义，通过减少实际持久化行宽取得稳定空间余量，再按原门禁验收。quality-12 的 2242 passed / 133 expected skipped、243 项独立 QA 及原性能失败记录保留；未来修改后必须重新取得适用的验收证据，不能借用修复前通过结果宣称新版本通过。

### 2. 推荐候选：仅压缩 permit 的三个完整 HMAC 标识

仅将 provider_permits.player_scope_tag、player_npc_scope_tag、conversation_scope_tag 从 64 字符小写十六进制 TEXT 改为 32 字节 BLOB。保留完整 256 bit 值；不截断、不更换密钥、不重算 HMAC、不删除字段。应用层 PermitScopeTags 继续使用原字符串，execution_admissions 和预算相关 scope 继续按现有 TEXT 存储和验证。

三个值每行合计减少 96 个原始值字节，100 行减少 9600 字节；record header 和页分配可能进一步改变实际占页。该估算不是已测空间收益，不保证最终降到 256 KiB，必须由下述固定矩阵验证。

继续保留 execution_id 的 TEXT 主键/FK、policy_version、acquired_at_ns、released_at_ns、五种 release_reason、STRICT/WITHOUT ROWID、全部 CHECK 和三个 active partial index；独立的 permit/admission scope 一致性检查继续存在。release/recover 仍更新原记录，禁止清除已释放 permit、移走审计历史或在测量结束追加 VACUUM。

不采用删除冗余 scope 后仅 join admission 的方案，因为那会改变当前独立归属校验；不采用仅缩短 reason/policy 的小额节省，因为目前更需要超过单页边界的余量。其他表、索引、预算投影一致性字段、WAL/FULL、事务与工作量均保持现状。

### 3. 精确文件范围与迁移方式

以下路径均相对 feature 工作树 E:\Agent\comprehensive-cases\15-cyber-town-f009。拟议范围为六个现有文件加一个新 migration，另更新正式工作树五份管理文档。当前仅制定方案，以下七个 feature 文件尚未因此修改。

| 文件 | 拟议修改及边界 |
| --- | --- |
| backend/src/cyber_town/infrastructure/control/sqlite_control.py | 注册 v9；仅增加 permit 私有严格编码/匹配函数；active scope COUNT/SUM 与 INSERT 使用 BLOB；admission/budget 原 TEXT 匹配保持。 |
| backend/src/cyber_town/infrastructure/control/migrations/0009_provider_permit_scope_storage.sql | 唯一新 SQL 文件：在既有迁移事务中无损重建 provider_permits，保留行、约束、索引与外键；版本升为 9。 |
| backend/tests/test_sqlite_control.py | 增加迁移/编码/并发/恢复/坏数据与事务回滚用例；当前版本断言升 9；历史 v8 专项显式固定前八个 migration，保留原断言。 |
| backend/tests/test_budget_control_step3.py | 仅更新当前 schema 版本/迁移列表期望，并覆盖预算与 permit 归属、结算不变；历史诊断根/跳过策略保持。 |
| backend/tests/test_retry_breaker_step4.py | 仅更新当前 schema 版本期望并验证 retry/recover 的 permit 释放语义。 |
| scripts/f009_step6_qa.py | 增加固定空间专项入口、合成布局及独立逻辑摘要；沿用 ResourceGuard/command_scope/子进程审计。当前阶段不启用新 native 根，不修改既有性能 runner 或性能额度。 |
| backend/tests/test_f009_step6_qa.py | 独立验证上述专项入口的边界、布局守恒、逻辑摘要、异常与退出恢复；不放宽已有断言。 |

迁移草案的确定操作顺序：
1. 验证运行时原生 unhex 能力以及现有迁移前缀/校验和，能力缺失时在 schema 改动前拒绝，不联网升级或另装工具。
2. 在既有 BEGIN IMMEDIATE 迁移事务内创建 v9_provider_permits；除三个 scope 改为 BLOB NOT NULL CHECK(typeof(column)='blob' AND length(column)=32)，其余列定义与当前 v4 表完全相同。
3. INSERT ... SELECT 全量复制原表。每个 scope 仅在 typeof='text'、length=64 且不包含 0-9a-f 之外字符时使用 unhex；否则返回 NULL，由 NOT NULL 使迁移整体失败。不能利用 unhex 的宽松输入接受大写、空白或坏数据。下方表达式分别用于三个 scope：

~~~sql
CASE
  WHEN typeof(player_scope_tag) = 'text'
   AND length(player_scope_tag) = 64
   AND player_scope_tag NOT GLOB '*[^0-9a-f]*'
  THEN unhex(player_scope_tag)
  ELSE NULL
END
~~~

4. 全量复制完成后，在同一事务中 DROP 原 provider_permits、将 v9_provider_permits 重命名为 provider_permits，再按原名称/列/WHERE released_at_ns IS NULL 重建三个 partial index，设置 PRAGMA user_version=9。这里的 DROP 是需要专项批准的表重建步骤，事务内保留所有逻辑行，不是删除历史数据；不关闭 foreign_keys 或安全检查。
5. 使用既有 schema_migrations 登记、表集合校验和提交机制；任何中途故障整体回滚。0001—0008 原始字节和哈希不改，business 两个及 observability 四个历史 migration 同样不改。

仓储实现将 permit 的 BLOB 匹配与原 _scope_matches 分开。新私有匹配要求三个值均为恰好 32 字节且与经严格验证的 PermitScopeTags 完整值一致；错误类型、长度或不匹配继续拒绝，不回显值。active 查询的三个参数与 INSERT 三列同步编码；已有 permit 仍先核对 admission，再核对 permit，并保持已释放执行不能重新获取、active 幂等以及所有并发限制。release_permit/recover 的字段与条件本身无需改写。

本机既有 Python 的 SQLite 3.47.1 已通过纯内存标量检查确认原生 unhex 可用；未执行候选迁移或文件数据库试验。其他环境及 CI 的能力尚未验证。若目标环境不支持，先报告兼容性缺口，不静默引入 UDF、改依赖、改 CI 或提高项目最低版本。v9 是前向迁移；旧 v8 程序应因迁移前缀不匹配而拒绝新库，不提供降级或混合版本写入。迁移可能暂占新旧表及 WAL 空间，该暂态开销必须记录；本方案不迁移任何真实/历史数据库。

### 4. 受控实施与验证顺序

A. 固定候选预验证（先验证布局，再改产品）

批准后先仅在两个 QA 文件中编写候选布局/迁移用例。全部数据库从原始历史 migration 新建到 v8，再对候选侧应用与拟议 v9 一致的草案；不复制或重开旧实验 SQLite。直接 SQL 合成 permit 生命周期只用于布局及迁移证明，不能替代真实仓储的产品语义验收。

固定三组种子 F009-permit-layout-01/02/03 与四种调度 serial、fifo、lifo、recovery，共 12 对、24 个全新数据库。每对使用完全相同的 100 个 execution/request ID、scope、时间和生命周期事件；ID 由固定种子构造 UUIDv4 格式的非单调序列，不选择有利种子、不排序重写正式基准 UUID。fifo/lifo 使用两个允许并存的不同 NPC/conversation；recovery 包含未正常释放后恢复的记录。种子、事件计划和顺序须在执行前登记摘要，不能依据页数结果改矩阵。

每对先比较所有逻辑行，再核对表/索引逐对象页、main/occupied/freelist/WAL/SHM 和完整字节归属。仅三个 permit BLOB 列在独立摘要中还原为原小写十六进制；其余应用表所有列和所有行保持，schema_migrations/user_version 的预期版本变化单独完整核对。不能直接把 TEXT 与 bytes 的 repr 哈希不同视为语义不同，也不能通过遗漏列/表来取得相同摘要。

候选晋级要求：12 对逻辑等价和约束/回滚用例全部通过，且每对相同观测时点的 occupied 总字节至少节省 8192 字节（两页），同时保留 main 和各对象原始数据。该两页要求是本方案的候选余量标准，不修改正式 256 KiB 门禁；此合成工作量尚未证明完整 control 工作量的增长上限。若候选仅省一页、任一对不满足或出现语义差异，停止并报告，不追加种子/批次筛选结果。有效 v8 基线不必每一对都复现 260 KiB；本批原失败证据继续成立。

B. 产品落地及专项语义验收（A 通过后，限七文件）

将已验证的草案落为唯一 v9 migration，与 A 草案逐字节核对；实现仓储适配和上述测试。执行前重新确认批准前 97 文件、branch/HEAD；实施后逐项对照七文件 allowlist，登记新的文件集合和聚合指纹，不继续冒用旧 97 文件指纹。

必须通过：
- 空库→v9、v7→v9、v8→v9、重复 initialize；旧迁移原哈希、全部逻辑行、五种 release_reason/active 状态、PK/FK/CHECK/三个 partial index 和 STRICT/WITHOUT ROWID 均正确；旧 v8 程序对 v9 拒绝。
- 合法 TEXT64 与 BLOB32 无损往返；大写/非 hex/空白/错误长度/错误存储类型被拒绝。仅在全新合成坏库构造异常，不能关闭产品连接安全检查；迁移复制中途、建表后/换表后/记账前故障注入均回滚至可验证的原 schema/version/迁移记录/逻辑数据，不遗留 v9 临时表。
- permit 与 admission 的三个 scope 分别单独不一致均拒绝；完整长度但值不同的 BLOB 同样拒绝；不能只验证存储类型。active 幂等、released 不重开、两独立连接竞争的 global=2/player=2/player-NPC=1/conversation=1 和释放再竞争均维持。
- 正常结束、cancel、provider 失败、control_failure、重启放弃五种释放；开放 execution intent 恢复；retry/waiter/replay 无重复 permit/结算/计费，预算投影三个完整性计数及原一致性拒绝仍有效，fake 成本 0。
- 在全新真实磁盘三库中执行现有完整生命周期场景并核对 WAL/FULL、integrity_check、foreign_key_check、owner joins、ledger/projection、长期记忆隔离/遗忘/替换/restart。由既有相关测试复用产品入口，不能以 A 的直接 SQL 布局用例替代。
- 独立 25-case evaluator 再启三个新进程，25/25、11 维度与冻结 digest 一致；先前所有适用独立边界/对抗场景重新验证。专项 Ruff/mypy/schema 与资源边界通过。任何新缺陷或超出七文件需求停止报告。

A/B 不运行正式统一 warm-up+5-run，也不产生新的性能通过结论。允许在列明的两个首次使用 basetemp 中依序运行预验证和专项回归；同一失败根不复用，失败后先分析，不能自动申请/启用递增根来重试。

C. 修复后的 Step 6 正式收口（后续另行授权）

A/B 成功仅表示“候选已实现且专项验证通过”，不能标记 Step 6 完成。之后提交新冻结指纹、全部专项结果与资源清单，再申请全新 native quality 根并执行完整 fake-only quality；当前不要求批准 quality-13。

原唯一 full-matrix-01 性能额度已经执行并失败，不能继续当作可用额度。修复后须另获明确的一次新增“统一 warm-up1+正式5”完整性能复验授权及准确的新根。已有 QA benchmark_root_binding 只绑定 QA_ROOT，原 runner 固定子名 full-matrix-01 已存在；必须先给出只在 QA 作用域绑定到已批准全新子根、完整恢复配置的适配与测试，不能覆盖旧目录或修改既有 runner。该后续适配/资源在申请时具体登记，当前不实施、不自动获批。

完整 quality 和所有语义门禁先通过，才运行一次新增性能批次。保持原 workload、随机标识生成、统计协议和所有延迟/吞吐及 256/512/768 KiB 门禁；默认 control 和三 SQLite control 均必须满足独立空间上限，诊断延迟的非阻塞性质不能豁免空间。失败则保留原始结果并停止，禁止增加批次找通过。全部条件和五文档/资源盘点完成后，方能标记 step_6_complete / awaiting_step_7_authorization。

### 5. A/B 拟议资源清单与边界（尚未创建，待随修复授权）

唯一新增 Python 专项根拟为 E:\Agent\cyber-town-f009-step6-qa\control-space-v1，当前不存在。该路径只用于 A/B 的 Python/SQLite 合成测试，不成为 Godot/Git/uv 原生动态例外根。

| 拟议相对路径 | 用途与登记方式 |
| --- | --- |
| layout/seed-01、seed-02、seed-03 下的 serial、fifo、lifo、recovery，各自 baseline/control.sqlite3 与 candidate/control.sqlite3 | 12 对固定布局库；24 个主文件及每库 -wal/-shm/-journal 的准确全路径在执行前生成并写入正式 evidence。无旧库拷贝。 |
| pytest-layout-01 | A 的迁移/坏库/回滚/入口测试唯一全新 basetemp；每个 Python 实际子目录、SQLite 及 sidecar 创建前由 ResourceGuard 同步精确登记。 |
| pytest-semantic-01 | B 的产品语义与独立回归唯一全新 basetemp；相同创建前登记和身份校验。 |
| layout-plan.json、layout-summary.json、semantic-summary.json | 固定矩阵/计划摘要、布局数值、脱敏语义与命令结果，不写入原始 scope 或请求文本。 |
| evaluator-process-01.json、evaluator-process-02.json、evaluator-process-03.json | 三个独立进程的 case/维度计数与 digest，逐个创建前精确登记。 |

父目录本身同样在创建前登记。测试临时资源继续使用已统一的 QA_ROOT/tmp 与 QA_ROOT/cache 内受控配置，通过 command_scope/command_environment(QA_ROOT) 传递；不将 control-space-v1 偷加到 NATIVE_ROOTS，也不从旧 quality 根继承 F009_NATIVE_ROOT/F009_NATIVE_PID。需要测试子进程时只使用既有批准 Python 和受审计入口；不启动 Git/Godot/uv 原生工具进行 A/B。mypy/Ruff 等可用既有 Python 模块、缓存严格局限 QA 已配置根。

必须保留 canonical 完整父链无 reparse、全新目录、文件身份与归属检查、父子两层审计、Python 实际子路径创建前登记、TEMP/cache 隔离与退出恢复。原生动态例外不会自动延伸到本根；如专项测试需要原生动态文件，须停止并说明缺口。所有新库、sidecar、失败证据和结果留存，不删除、不清理缓存。拟议资源清单是待批准设计，不等于已授权创建；实际每个路径登记完成后才能创建。

### 6. 本轮计划结论与下一次批准的准确范围

本轮可审查结论：优先验证 provider_permits 三个完整 HMAC 的无损 BLOB 编码，以七文件和 append-only v9 最小范围处理 SPACE-01。尚无候选运行结果，不能承诺空间下降或修复成功。下一次可以一次批准 A/B 的有条件实施，避免把每个内部小步骤都变成新的批准轮次；A 不通过即停。

建议后续授权文本：
“批准按《QA-F009-SPACE-01 空间超限专项修复方案》执行 A/B。仅批准列出的七个 feature 文件及正式五文档，允许 provider_permits 三列完整 HMAC 从 TEXT64 无损编码为 BLOB32，并以 append-only v9 在事务内重建该表；批准全新 E:\Agent\cyber-town-f009-step6-qa\control-space-v1 的列明 Python 专项资源。先完成固定 12 对候选预验证，全部满足晋级标准后再落地产品并完成专项语义验证。原迁移哈希、归属/并发/恢复语义、安全检查、阈值、工作量和资源保留规则保持。超出范围或验证失败即停止。本授权不含新的完整 quality/native 根、新增正式性能复验额度或 Step 7，不提交、推送、PR、合并、部署或删除资源。”

当前五文档计划更新完成不构成上述修复批准。授权需求源于原 Step 6 的产品/SQL 冻结和既有缺陷硬停止边界，以及原性能额度已消费的事实；并非要求先批准 quality-13。


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

## Step 6执行结果与下一授权（2026-09-03）

当前状态：`step_6_blocked / awaiting_projection_integrity_fix_authorization`。原94冻结基线已确认，根适配授权范围已明确。

1. [x] 独立HTTP/注入/合法Unicode/replay/三NPC磁盘记忆与三fence恢复41用例通过。
2. [x] 独立projection损坏故障1用例失败，确认P1并停止；失败库不恢复/不修补。
3. [x] 新QA两文件ruff/format/mypy、ignore/sensitive、Git/13migration/正式库/端口及资源收口。
4. [ ] 等待S6-QA-001最小修复单独授权；候选仅control/sqlite_control.py及新增QA测试/隔离脚本。
5. [ ] 修复后以新批次恢复全部剩余独立领域、既有语义/故障、25-case三进程evaluator、完整quality、唯一统一1+5性能。
6. [ ] 全部门禁通过才标step_6_complete / awaiting_step_7_authorization；当前不进入Step7。

准确最小修复Prompt和资源清单见[evidence](evidence.md)最前收口节；历史执行记录完整保留。

## 2026-09-03：Step 6恢复执行

当前状态：`step_6_authorized / independent_qa_preparing`。用户已确认94文件冻结基线并批准新QA脚本作用域根绑定；恢复指纹、Git、13migration、正式库和端口预检全部符合。首批资源已在evidence最前节创建前登记，实际创建前还须精确路径校验；独立测试未运行。原预检阻塞记录是历史，保留且不作为当前授权阻塞。Step6未完成，不进入Step7/Git交付；既有缺陷硬停止边界保持。

## F-009 Step 6预检停止（2026-09-03）

当前状态：`step_6_preflight_blocked / awaiting_baseline_confirmation_and_qa_root_adapter_authorization`。用户已授权 Step 6，本轮触发预检硬停止；Step 5 保持完成，Step 6 未完成，Step 7 未授权。下方 Step 5 blocked/待授权表述属于完整保留的历史记录，不覆盖本节。

1. [x] 恢复上下文，核同分支/HEAD/37+57集合、tracked/untracked whitespace、13migration和正式库/端口。
2. [x] 保存94文件当前只读快照，记录完整既有指纹缺口；不重设基线。
3. [x] 静态确认benchmark固定V29根；按硬停止要求，QA根/脚本/测试均不创建。
4. [ ] 恢复前：提供可核验的当前94文件既有登记，或明确确认本次快照 SHA256=`0094cdb520fe8406f764124db4a35e2282e810def7c734d3b52be6bb90b8dc27` 可作为后续冻结 QA 基线；确认仅通过已列入范围的 `scripts/f009_step6_qa.py` 安全接入全新根，保留原测量协议/工作量/门禁/产品路径，禁止修改既有 runner 和产品。准确恢复 Prompt 见 evidence。
5. [ ] 恢复后先完整子路径预登记，再完成独立专项、产品语义/磁盘/故障、三进程evaluator、quality及唯一统一1+5性能。
6. [ ] 全部门禁通过才收口为step_6_complete / awaiting_step_7_authorization。

本轮仅更新正式五文档；准确findings/资源/恢复Prompt与旧阶段行完整保存在[evidence](evidence.md)最前Step6节。

## F-009 Step 5 最终收口（2026-09-02，完成）

1. [x] Dialogue test-only runner：不可恢复provider invalid response与可恢复transport/malformed场景契约闭合。
2. [x] 剩余harness failure-first：projection、steady-profile、migration三组各稳定红测，共3 failed。
3. [x] 最小修复：历史projection默认隔离；steady runner模式局部化并恢复；migration版本跟随注册表；4项纯格式差异闭合。
4. [x] 定向绿测：2 passed / 33 expected skipped。
5. [x] 完整quality：ruff、129文件mypy、schema、Godot、connectivity 9/9、Dialogue loopback、全量pytest `1997 passed / 133 expected skipped`、final ignore/sensitive全部通过。
6. [x] 独立format：129 files already formatted；tracked diff-check和57个untracked no-index whitespace通过。
7. [x] migration哈希、正式数据库不存在、8000端口、Git边界及V33资源盘点通过。

状态：`step_5_complete / awaiting_step_6_authorization`。下一步仅可在用户单独授权后进入Step6独立fake-only QA；不得提交、推送、PR、部署或由Codex删除资源。

## Step 5 Dialogue runner 修复与剩余质量阻塞（2026-09-02）

1. [x] 单场红测：旧`invalid_recovery`因强制要求不可恢复错误启用Retry而失败，provider实际调用1次。
2. [x] 最小test-only修复：显式区分`provider_invalid_response`不可重试与客户端malformed-response可重试契约；Python场景改为1次provider调用。
3. [x] 单场绿测和全部Dialogue loopback：10个基础场景+Multi-NPC通过；恢复场景冻结请求且最多一次手动Retry。
4. [x] quality前置：ignore/sensitive、lock、ruff、129文件mypy、schema、Godot import/unit、connectivity 9/9和Dialogue loopback通过。
5. [ ] 全量pytest：`2008 passed / 100 skipped / 22 failed`；20项历史projection候选、1项steady-profile runner、1项v6 migration断言不在本轮授权范围。
6. [ ] 全仓format：本轮允许的`dialogue_integration.py`已格式化；另有4个未授权文件仍不符合格式。
7. [ ] 单独授权剩余测试基础设施调查/修复后，使用全新登记根重跑完整quality；全部通过才关闭Step5。

状态：`step_5_comprehensive_acceptance_blocked / awaiting_remaining_test_harness_authorization`。不得进入Step6、提交、推送、PR、部署或删除资源。

## Step 5 综合验收 harness 修复续项（2026-09-02）

1. [x] v6→v7过期测试断言、历史runner默认收集和环境映射泄漏风险：红测4 failed，绿测4 passed。
2. [x] 综合磁盘/故障回归：412 passed / 100 expected skipped；不连接旧V7/V8/V9/V10证据库。
3. [x] evaluator：19 passed；25/25 case与三进程一致性保持。
4. [x] quality前置：ignore/sensitive、lock、ruff、129文件mypy、schema、Godot import/unit、connectivity 9/9。
5. [ ] Dialogue loopback：旧test-only Godot runner错误要求不可重试的provider invalid response启用Retry；当前Godot修改未授权。
6. [ ] 单独授权后仅修test-only runner，使用全新登记根重跑Dialogue loopback和完整quality；全部通过才关闭Step 5。

状态：`step_5_comprehensive_acceptance_blocked / awaiting_test_only_godot_runner_authorization`。不得进入Step 6、提交、推送、PR、部署或清理资源。

## F-009 Step 5 综合验收首次执行（2026-09-02，阻塞）

1. [x] 只读预检正式/功能 Git、13份migration、V29摘要、正式数据库和端口边界。
2. [x] 在创建前登记 `E:\Agent\cyber-town-f009-step5-tests\step5-comprehensive-v30` 及允许目录/文件 surface；复用既有 Python 3.12，不建 venv、不联网。
3. [x] 固定 evaluator：`19 passed`；25/25 case、11维度、三进程相同 digest，所有安全/归属/成本计数为0。
4. [ ] 综合磁盘/故障回归：首次 `440 passed / 48 failed / 60 deselected`；47项为旧固定根/专用环境依赖，1项为 control v6 过期测试断言。
5. [ ] 完整 fake-only `scripts/quality.py`：因上一步硬停止未运行。
6. [ ] 单独授权测试 harness 修复后，用全新已登记 basetemp 重跑综合回归；全绿后才能运行完整质量入口并关闭 Step 5。

状态：`step_5_comprehensive_acceptance_blocked / awaiting_test_harness_fix_authorization`。不进入 Step 6、Git 交付或资源清理。

## F-009 Step 5 V29 核心复验收口（2026-09-02，完成）

1. [x] 失败优先锁定 V29 四个阈值、等于/刚超过边界、稳定 warning/failure code、缺失配对及原 p99/throughput 语义；red=`6 failed / 1 passed`，最终契约=`39 passed`。
2. [x] 必要回归：主批 `182 passed / 2 environment failures / 53 deselected`；两项专项在独立预建数据根复验为 `2 passed`，有效覆盖为184项通过。
3. [x] ruff、format、mypy、tracked 与三份 untracked no-index whitespace、13份migration指纹通过。
4. [x] 唯一统一1+5核心矩阵完成；`failure_codes=[]`、`warning_codes=[]`，HTTP/SQLite/reject/空间/内存绝对与配对门禁全部通过。
5. [x] 66 个矩阵 SQLite immutable只读复核：integrity failures=0、FK violations=0；1,200 trace均14阶段，非零成本/token、未释放permit、非settled intent/reservation均为0。
6. [x] 正式数据库不存在、8000端口空闲、Git边界与资源生命周期复核完成。
7. [x] 用户已单独批准 Step 5 综合验收；首次执行因测试 harness/过期断言阻塞，详见上节。

状态：`step_5_core_revalidation_complete / awaiting_step_5_completion_authorization`。

## F-009 Step 5 V29 门禁修订与核心复验（2026-09-02，执行中）

1. [x] 用户批准 recorded p95 `3.0ms warning / 3.5ms fail`、paired p95 delta `0.5ms warning / 0.75ms fail`，p99 `5ms` 与 throughput `80%` 不变。
2. [x] 只读预检正式/功能 Git、13 份 migration、V28 摘要指纹和新根父链；新根创建前不存在，父链无 reparse point。
3. [x] 完整展开并打印初始 48 个允许目录、199 个矩阵文件；测试构造与专项环境跟进均先登记新路径，当前允许 surface 为 55 个目录、199 个文件，SHA256=`BB008757BE606D692CD93B40AA04AA12988EAD9000CF88CCE7012A3A15BB93D9`。
4. [x] 失败优先锁定绝对/配对 warning、fail 边界及原 p99/throughput 契约。
5. [x] 实施三文件最小契约更新并运行必要语义/静态回归。
6. [x] 回归全绿后运行唯一统一 1+5 核心矩阵；全部阻塞码为空，已收口为 `awaiting_step_5_completion_authorization`。

## F-009 Step 0 V29 in-memory 门禁评审草案（2026-09-02，未实施）

1. [x] 只读确认当前 gate 实现仅位于 `application/control_performance.py`，由 `test_control_performance_contract_step5.py` 验证并由 `f009_step5_benchmark.py`输出；产品control/repository无需改变。
2. [x] 计算 V28 五轮稳健统计：recorded p95 median/MAD/3MAD上界=`2.844435/0.089335/3.112440ms`；paired p95 delta=`0.210025/0.100125/0.510400ms`。
3. [x] 对比门禁目标：绝对2ms当前无法区分共同控制成本和recorder回归；p99、paired throughput及正式HTTP仍独立约束尾部、整体开销和用户可见性能。
4. [ ] 用户批准推荐门禁：recorded p95 3.0ms warning/3.5ms fail；paired p95 delta 0.5ms warning/0.75ms fail；p99 5ms和throughput 80%不变。
5. [ ] 获准后仅修改三文件，失败优先锁定等于/刚超过边界、缺失配对、负delta、warning不影响exit以及原p99/throughput不变。
6. [ ] 使用全新登记根完成定向回归和唯一1+5核心复验；所有阻塞码为空后才收口为`awaiting_step_5_completion_authorization`。

## F-009 Step 5 V28 当前产品路径复验（2026-09-02，等待门禁评审授权）

1. [x] 只读复核 V27/V26、正式与功能 Git、migration、正式数据库和端口边界。
2. [x] 失败优先发现并修正内存 benchmark 仍调用旧分解式 control API 的契约错误；red=`1 failed`，产品路径/runner 绿测=`5 passed`，完整性能契约=`32 passed`。
3. [x] 在不改产品语义和阈值的前提下运行唯一一次 V28 统一协议 1+5 核心矩阵；未删除慢样本或追加批次。
4. [x] 确认 HTTP、SQLite observability、reject、相对增量、空间和问题二全部通过；唯一阻塞为 in-memory p95=`2.8436ms > 2ms`。
5. [x] 区分 recorder 开销、共同控制链固定成本与运行波动：paired baseline p95=`2.7237ms`，吞吐比=`104.33%`；五轮结果存在明显同机漂移。
6. [x] 量化成功路径 SQL：78 statements、7 savepoint/7 release。无持久文件的成功路径理论对照完全消除 savepoint 后 p95 仍=`2.3793ms`，且不满足异常隔离，排除该微优化作为产品修复。
7. [x] 排除 GC 与 scope-tag 重算两个小候选：GC off p95=`2.4591ms`（on=`2.5262ms`）；execution-level scope reuse p95=`2.5680ms`（current=`2.6358ms`）且吞吐略降，均不足以可靠达到2ms，不实施产品改动。
8. [ ] 用户单独批准 Step 0 in-memory 门禁适用性评审；批准前不改 `2ms`、不扩大事务架构、不进入 Step 5 综合验收。
9. [ ] 若评审形成并另行批准兼容的新门禁契约，失败优先更新契约/benchmark/测试，再执行全新统一 1+5 核心复验；只有全部阻塞门禁通过才能申请 Step 5 综合验收。

## F-009 Step 5 V27 核心性能复验（2026-09-02，已停止）

1. [x] 只读核对正式/功能 Git 基线、五文档/功能文件集合、migration 指纹、正式数据库、端口与新根边界。
2. [x] 失败优先锁定新的 `CORE_REVALIDATION_ROOT`，避免复用 V11 旧证据；完整资源 surface 已展开、打印并登记。
3. [x] 运行定向 runner 契约与静态检查，确认只允许全新 V27 根；red=`1 failed`，green=`1 passed`，最终契约=`8 passed`。
4. [x] 创建 V27 根和 `tmp`，运行唯一一次完整 warm-up + 5-run 核心矩阵；未追加批次。
5. [x] 复核阻塞/告警/诊断码、66 个数据库 integrity/FK、migration 指纹、正式数据库和端口。
6. [x] 更新五份文档及资源台账并停止；唯一阻塞为 in-memory p95，未进入 Step 5 综合验收或 Step 6。
7. [ ] 下一步需单独决定：继续优化两种内存场景共有的控制链固定成本，或回到 Step 0 重新审查 2ms p95 门禁及适用 profile；不得把本轮 p99/吞吐通过替代 p95。

## F-009 Step 5 V26 产品 Gate 2 最终收口（2026-08-31，完成）

1. [x] 失败优先证明 inherited writer 会把 memory composed transaction 路由到磁盘占位库；红测 1 failed。
2. [x] `_MemoryControl` 最小覆写 transaction routing，共用单一 in-memory connection，保持 BEGIN/savepoint/rollback/close/error mapping。
3. [x] runner 契约两次绿测均为 3 passed；green 磁盘 SQLite=0。
4. [x] v7 断言及排除 V10 的 Gate 2 定向回归：118 passed / 53 deselected。
5. [x] 五对 fresh 空间门禁：5/5 product growth=258048，saving=8192，failure=[]；schema/integrity/FK/归属全绿。
6. [x] 当前授权范围 ruff、format、mypy、diff、migration hash、正式数据库和端口检查通过。
7. [ ] 等待 Step 5 核心复验单独授权；本轮不运行完整性能矩阵、Step 5 综合验收或 Step 6。

## F-009 Step 5 V26 memory runner follow-up（2026-08-31，阻塞）

1. [x] 在 evidence 预登记并创建唯一全新 `pytest-followup-01`；未复用旧 SQLite。
2. [x] 仅把 budget control 测试中的 migration/user_version 断言更新为 v7，未改变预算语义。
3. [x] 隔离运行两项 memory performance contract；结果 `2 failed`，按硬停止条件没有继续。
4. [x] 只读确认根因：in-memory schema 与 inherited writer/composed transaction 指向不同数据库；失败属于 benchmark runner，而非产品 migration。
5. [ ] 等待单独授权修复 `_MemoryControl` transaction routing 并增加“不创建磁盘占位库”的失败优先测试。
6. [ ] runner 修复全绿后，才复验 v7 断言、排除 V10 的定向回归及五对 fresh 空间门禁。

## F-009 Step 5 V26 产品 Gate 2（2026-08-31，回归阻塞）

1. [x] 全新产品 Gate 2 根和允许 surface 已预登记；旧 V26 SQLite 未连接或覆盖。
2. [x] 失败优先：实施前产品 Gate 2 专项 `8 failed`；实施 migration 注册、精确 0007、授权测试/runner 后为 `8 passed / 35 deselected`。
3. [x] 0007 内容与授权完全一致；sqlite_control 仅注册 migration 7；既有 0001—0006 未修改。
4. [x] 扩大定向回归已执行并按 `113 passed / 57 failed` 触发硬停止；没有运行五对空间批次。
5. [ ] 获得测试范围补充授权：更新旧 v6 断言、以全新 basetemp 隔离 2 项 memory contract，并明确 53 项 V10 专项的 Gate 2 排除/独立环境策略。
6. [ ] 仅在补充回归全绿后运行五对 fresh control 空间门禁及后续静态/完整性收口；未通过前不得改为 `space_gate_resolved`。

## F-009 Step 5 V26 query-plan Gate 1 修复（2026-08-31，完成）

1. [x] 全新根预登记并确认与旧 V26 证据隔离；旧 SQLite 未建立连接。
2. [x] 失败优先固定 baseline 独立连接、DROP commit/close、candidate 全新连接和四类持久 surface 契约；红测为 1 collection error。
3. [x] 最小修复 query-plan-only probe；纯契约 11 passed。
4. [x] 唯一批次确认 candidate 的 sqlite_master/index_list/dbstat/EXPLAIN 均不再保留候选索引，三个正常预算计划不退化。
5. [x] ruff、format、mypy、whitespace、migration hash、integrity、隐私、正式数据库和端口检查通过；资源已终盘登记。
6. [ ] 等待修订后的产品 Gate 2 单独授权；本轮不创建 0007、不注册 migration 7、不运行 history/空间五对/完整矩阵或 Step 5 综合验收。

## F-009 Step 5 V26 Gate 1 收口（2026-08-31，失败）

1. [x] 失败优先契约与诊断工具：初始缺模块红测；最终纯契约 5 passed，ruff/format/mypy 通过。
2. [x] query plan、六个 history 场景和五对 fresh 空间场景已按唯一批次执行。
3. [x] history/恢复/约束/空间/完整性均通过；五对 candidate 均回收 8192 occupied bytes 并落到 258048 bytes。
4. [ ] query-plan 硬门禁失败：DROP 后同连接 EXPLAIN 仍命中候选索引；按停止条件不修 runner、不重跑、不创建产品 0007。
5. [ ] 下一授权若继续，只能先用全新连接/全新子根修正 query-plan 证据；通过后还需扩充产品 Gate 2 的 loader/user_version 授权范围。

## F-009 Step 5 V26 独立空间修复（2026-08-31，执行中）

1. [x] 只读核对 main/功能分支、33/54 文件集合、125/140ms 契约、0001—0006 指纹、0007 缺失和 V26 父链无 reparse。
2. [ ] 新增失败优先的 V26 synthetic preflight 脚本/测试。
3. [ ] 验证 query plan、projection 故障/recovery、100/1,000/10,000 ledger 和五对 fresh 空间门禁。
4. [ ] 仅在所有 synthetic 条件通过后实施 append-only 0007 与产品回归；否则立即停止。
5. [ ] 运行定向静态/完整性/隐私门禁并收口五份项目文档和资源台账。

## F-009 Step 0 control overhead 门禁修订实施（2026-08-31，完成）

- [x] 固定 `125ms` warning、`140ms` failure 常量；删除产品/runner 中旧 `max(off*20%,30ms)` 判定。
- [x] warning 使用独立稳定 code，写入 benchmark metadata-only 摘要，不进入 failure/退出码。
- [x] 完整 gate、storage A/B、V21/V24 HTTP pair 共用同一契约；绝对 HTTP、吞吐、空间和安全/持久化门禁不变。
- [x] 失败优先和边界测试通过；ruff、format、mypy、diff check 通过；未运行性能矩阵。
- [ ] 下一授权仅处理 control occupied growth 多出的 2 页/8KiB；延迟门禁不再触发架构改造。空间通过后仍需单独申请恢复 Step 5 综合验证。

## F-009 Step 0 control overhead 门禁修订候选（2026-08-31，历史决策记录）

1. 采用现有五组真实 TCP 五轮证据，不追加样本：汇总增量范围=`86.3302—125.2705ms`，中位数=`98.1198ms`，MAD=`11.7896ms`，robust 三 MAD 上界=`133.4886ms`。
2. 建议把相对门禁从 `max(off*20%,30ms)` 改为同 profile 的固定 overhead budget：`<=140ms`；`>125ms` warning，`>140ms` fail。继续使用 `median(on run p95) - median(off run p95)`，不改变五轮聚合算法。
3. 保持绝对 p95/p99=`250/400ms`、吞吐=`>=4/s`、空间、零放大、WAL/FULL、路径身份检查和全部业务/取消/restart/replay 语义门禁。
4. 140ms 只适用于当前 Windows/Python3.12/FakeProvider/NoOp observability/真实 TCP/独立客户端/business+control SQLite profile。环境或协议变更必须另建 baseline。
5. 该候选随后已获用户批准并完成性能契约、benchmark 与对应测试实施；当前下一动作是独立的 8KiB control 空间门禁修复授权，空间通过后仍需单独申请恢复 Step 5 核心验收。

## F-009 Step 5 问题二 V25 有界归因收口（2026-08-31）

1. V25 临时三-fence probe 因跨 worker/request 关联设计不足连续三次 fail-closed；按停止条件不再创建第四批，不生成结果摘要，不修改产品。
2. 只接受 V24 plain summary 的可信聚合证据：新增连接与 writer 锁等待已排除；每请求约三次 control lease/write commit 与三-fence 架构吻合，WAL/FULL commit 和路径身份检查是剩余结构性成本。
3. 当前没有证据充分的局部代码修复；缺少逐请求 fence 关联意味着也不能把 30ms 宣告为严格物理不可达。后续不得继续 SQL/锁/连接微调寻找通过。
4. 延迟下一决策二选一：坚持 30ms 时另起架构调整方案；保持现有三次同步 durability 时回到 Step 0 重审相对门禁。
5. 空间另行处理：页级证据为 66 增长页对 64 页上限；一个 2 页非唯一 owner scope 索引理论上足以消除 8 KiB 超限，但必须先独立验证 query plan、长历史、缺失 projection fail-closed 与恢复性能，不与延迟候选绑定。

## F-009 Step 5 问题二 V24 产品实施（2026-08-31）

- Gate 1：已完成。append-only control `0006` 红测、repository 三-fence 状态转换、application 接入、磁盘取消/重启/replay/waiter/迟到/跨库业务写入归属和单请求 fence 计数均通过。
- Gate 2：已执行并失败。相对 p95 增量与 control 空间门禁未通过；按停止条件未运行 Step 5 综合验收或 Step 6。后续只能先只读分析 V24 证据并另行批准最小候选，不得追加批次寻找通过结果。
- V24 根：`E:\Agent\cyber-town-f009-step5-tests\performance-v24-execution-intent-product`，先登记后创建，Step 5 收口后由用户手动删除。
- 当前不得执行 Step 5 综合验收、Step 6 或 Git 交付。

## F-009 Step 5 问题二 V23 收口（2026-08-31）

- synthetic state-machine：通过；产品实施：未授权。
- semantic：三 fence、clean cancel release、unknown receipt restart conservative settlement、replay/waiter/conflict、late result、recovery idempotency、rollback 和零重复副作用均通过。
- 工程门禁：最终 `16 passed`；ruff、format、mypy、tracked/untracked whitespace 通过；正式数据库不存在。
- 下一候选产品范围仅可包括 append-only control `0006`、`application/control.py`、`application/dialogue.py`、`infrastructure/control/sqlite_control.py`，以及对应 control/budget/retry/async-persistence/performance tests 与 benchmark。API ingress、Dialogue v1、Godot、既有 migration 不得修改。
- 产品实施顺序：migration/state-machine 红测 → repository 原子转换 → application 接入 → clean/crash/restart/replay/waiter/late result → business-write permission 唯一归属 → 单请求三 fence 计数 → 真实 TCP 1+5。
- 即使产品语义通过，30ms 相对性能门禁未通过前不得关闭问题二或 Step 5。

## F-009 Step 5 问题二 V23 synthetic state-machine（2026-08-31）

1. 保持 V22 回退后的 V21 产品状态，只修改 `scripts/f009_step5_architecture_probe.py` 与 `backend/tests/test_architecture_probe_step5.py`。
2. 先红测锁定三 fence、owner/waiter/replay、clean cancel、crash recovery、迟到结果、重复 recovery、事务回滚及零重复副作用。
3. 诊断代码内建立 test-only SQLite schema；它不是 migration，不得被产品加载。
4. 使用全新 V23 basetemp 绿测，再运行唯一 semantic scenario 并输出 metadata-only `summary.json`。
5. 运行定向 ruff/format/mypy/diff、隐私、SQLite integrity/FK、migration hash 和正式数据库检查。
6. 任一语义不闭合、需要 provider receipt 或重复归属不为0时停止；即使通过也只形成产品实施建议，不创建 `0006` 或进入性能矩阵。

## F-009 Step 5 问题二：V22 回退后架构决策（2026-08-31）

- 已完成：六文件 V22 增量精确回退；V22 symbol=0；V21 定向语义 `153 passed / 55 deselected`；ruff/format/mypy/diff/Git 集合通过。
- 已证实下界：现有成功路径包含 ingress、execution admission、pre-provider、dispatch marker、post-provider 五个顺序 durability 边界；pre/post provider 已各自是单事务，provider await 不可置于事务中。
- 禁止重复路线：跨请求 group-commit、调用层长事务、把 dispatch 提前并入 reservation，分别已由 V22、V12、V21 语义/性能证据否决。
- 推荐候选 A：先仅在 synthetic state-machine 中验证 append-only `0006_control_execution_intent.sql`，把 execution admission、provider control admission 与 dispatch intent 合并，正常成功路径目标为三个 fence。硬前提是用户接受“intent 后崩溃保守结算”和“execution quota 在 provider attempt 边界消费”两项变化。
- 备选 B：provider 提供 execution-scoped idempotency key + durable receipt；未证明外部 provider 支持前不得实施。
- 验证顺序（获新授权后）：状态机红测 → migration/rollback/rebuild → clean cancel 与 crash-window → replay/waiter/late result/restart → 单请求 commit 计数目标 → 真实 TCP 1 warm-up + 5 measured → 全部静态/隐私/数据库门禁。
- 停止条件：任何重复 dispatch/计费/业务写入、scope 泄漏、非唯一终态、recovery 不确定性未按锁定规则收口，或 1+5 相对增量仍大于 30ms。失败时不得扩大 schema、放宽 WAL/FULL 或重复局部优化。
- 当前不实施候选、不进入 Step 5 综合验收或 Step 6。

## 问题二 V22 失败收口（2026-08-31，当前权威状态）

- [x] 建立同tick bounded group coordinator、逐item savepoint、取消前后和物理故障回滚红绿测试。
- [x] 修正item级breaker存储失败不能回滚已完成budget settlement的语义回归；专项`5 passed`。
- [x] 完整控制/预算/breaker/取消/异步持久化集合`158 passed / 55 deselected`；静态门禁通过。
- [x] 完成真实TCP固定1+5矩阵，绝对HTTP、吞吐、空间和数据库审计通过。
- [ ] 相对p95增量=`125.2705ms > 30ms`；V22候选不具备保留为产品修复的性能资格。
- [ ] 下一步必须二选一并另行授权：精确回退仅V22六文件增量；或先设计能减少**单请求内部durable fence**的恢复兼容架构。不得直接继续微调group窗口、放宽阈值或进入Step5综合验收/Step6。

## 问题二 V22 待授权执行序列（2026-08-31）

1. 只读复核 V21 SHA、六文件指纹与 V22 路径不存在/reparse 边界。
2. 预登记并创建 V22 的 `tmp`、red、green、semantic、performance 子根。
3. 先红测 bounded coordinator：同批一次 commit、逐 item savepoint、取消、异常、关闭和 durable acknowledgement。
4. 实施 API/Dialogue routing 与 repository group runner；不得引入固定时间窗口或跨 provider await transaction。
5. 运行五边界计数、控制语义、真实三库取消/重启/长期写入回归。
6. 只有全部语义通过才运行真实 TCP 1 warm-up + 5 measured；门禁仍为 `on p95-off p95 <= max(off*20%,30ms)`。
7. 未通过即保留目标开放并报告架构/阈值冲突证据，不执行 Step5 综合验收或 Step6。

## 问题一：预算历史增长修复收口（2026-08-31，当前权威状态）

状态：`step_5_problem_1_budget_history_growth_resolved / problem_2_and_step_5_still_open`。

- [x] 用旧产品 SQL 复现 24 小时 ledger 扫描随历史线性增长：1000 行约 52,107 VM steps。
- [x] 新增 append-only control `0005`，保留 ledger 为唯一真相，以可重建 projection 保存四类 scope 的1h/24h attempt及24h成本。
- [x] reserve/replay/dispatch/settle/release、严格 cutoff、16并发、rollback、restart recovery 和 fail-closed 回归通过。
- [x] 历史有界证据：100/1000 ledger 的产品 lookup 为188/178 VM steps。
- [x] ruff、format、mypy、whitespace、migration hash、integrity/FK 与正式数据库不存在检查通过。
- [ ] 问题二（control-on 多次 durable commit）与整链绝对 p95 继续独立处理；不得把问题一完成误写成 Step 5/R-10 完成。

## V20 固定成本归因收口（2026-08-31，当前权威状态）

状态：`step_5_v20_fixed_cost_attribution_complete / awaiting_control_state_boundary_design_authorization`。

- [x] 只读核对正式/功能 Git、V19 摘要、10 migration 和产品 `0005` 不存在。
- [x] 预登记 V20 精确资源 surface、敏感性、期限和用户手动回收方式。
- [x] 失败优先锁定五热点、父子区间去重、跨 request 归属和五轮聚合：`3 failed -> 4 passed`；相关 V9/V10/V20 工具回归最终 `34 passed`。
- [x] 完成唯一 non-gating 1+5 paired attribution，共12000 fake-only execution，归属完整、隐私命中0、产品0005=false。
- [x] 排除“scope tag 复用单独解决2ms”和“仅减少BEGIN/commit单独解决2ms”；前者约13%，后者约3%。
- [ ] 下一步仅允许先设计 execution control context 与 durable state boundary；不得重新包装 V12 intra-execution transaction batching，不得实施产品或运行完整矩阵。
- [x] 性能 P1、Step5、R-10 保持开放；未进入综合验收或Step6。

## V19 single-write projection 失败收口（2026-08-31，当前权威状态）

状态：`step_5_v19_single_write_performance_gate_failed / awaiting_next_performance_decision`。

- [x] 复核正式/功能 Git、V18 失败摘要 SHA256、10 migration、产品 `0005` 不存在及新根边界。
- [x] 锁定候选：reserve 单 UPSERT；settlement/release 单 UPDATE；1h/24h expiration 合并探测，无数据跳过 totals 写入。
- [x] 预登记 V19 精确 surface、敏感性、期限和用户手动回收方式。
- [x] 红测锁定每个 lifecycle delta 仅一条写 SQL、无过期数据零 totals write、有过期数据单聚合 UPDATE、缺行/负值/rollback 继续 fail-closed；最终定向 `33 passed`。
- [x] validation-03 完成 semantic、space、统一 plain 1+5 和独立 non-gating stage companion；SQL 数量目标、语义/空间/稳定性/吞吐/p99通过。
- [x] 首次 validation-01 在 clock-rollback runner 调用缺陷处停止；保留不复用，修正后改用全新 validation-02 完整重跑。
- [x] validation-02 全部既有语义 checkpoint 通过，但缺少 no-expiration 场景导致 skip 门禁误判；保留不复用，validation-03 将该场景列入正式清单。
- [ ] recorded p95、reservation 降幅、settlement 降幅失败；不得实施产品 `0005`。
- [x] 按停止条件未进入 Step 5 综合验收或 Step 6。

## V18 revised performance 失败收口（2026-08-31，当前权威状态）

状态：`step_5_v18_revised_performance_gate_failed / awaiting_revised_projection_performance_decision`。

- [x] 空间门禁通过：增长 196608/262144 bytes。
- [x] plain 1+5 与独立 stage companion 按固定协议完成，共 24000 execution，无追加批次。
- [ ] recorded p95、reservation 降幅、settlement 降幅三项失败；不得实施产品 0005。
- [ ] 下一方案必须先消除无过期行的 day-window no-op SQL，并证明 logical delta 不再固定翻倍为 seed+UPDATE；需另行授权，不能在本轮继续微调。

## V18 revised performance 预验证（2026-08-31，当前权威状态）

状态：`step_5_v18_revised_performance_authorized / prevalidation_pending`。

- [x] 核对 revised semantic summary、Git、migration、产品 0005 与新根边界。
- [x] 预登记 revised-performance 精确 surface；旧数据库不得连接/覆盖。
- [ ] 失败优先锁定 fresh root、semantic summary 指纹、plain/stage 协议和完整资格 verdict。
- [ ] 运行空间、plain 1+5、独立 stage companion；不得追加批次。
- [ ] 只报告产品实施资格，不创建产品 0005。

## V18 revised semantic 通过收口（2026-08-31，当前权威状态）

状态：`step_5_v18_revised_semantic_passed / awaiting_set_based_performance_prevalidation_authorization`。

- [x] 固定四 scope zero-seed 后以 set-based UPDATE 应用 delta；负值由最终 totals CHECK fail-closed。
- [x] 红测 collection error；实现后 27 passed，ruff/format/mypy 通过。
- [x] 全新磁盘 semantic：16 并发、settlement、hour/day exact cutoff、clock rollback rebuild、projection/integrity/FK/隐私全绿。
- [ ] 统一 plain 1+5、独立 stage companion 与空间门禁等待单独授权；产品 0005 仍受全绿硬门禁约束。

## V18 revised semantic 修订（2026-08-31，当前权威状态）

状态：`step_5_v18_revised_semantic_authorized / zero_seed_update_pending`。

- [x] 核对旧失败数据库哈希、Git、10 migration、产品 0005 与新根边界。
- [x] 预登记 revised-semantic 新根；禁止连接或覆盖旧 V18 SQLite。
- [ ] 红测锁定 zero-seed、set-based UPDATE、负值 CHECK/rollback 与 fresh manifest。
- [ ] 仅运行全新磁盘 semantic gate；不运行任何性能批次。

## V18 synthetic 失败收口（2026-08-31，当前权威状态）

状态：`step_5_v18_synthetic_semantic_gate_failed / awaiting_revised_set_based_candidate_authorization`。

- [x] 基线、资源、红测、set-based 固定 SQL 初版及 25 项定向回归。
- [x] semantic 并发/投影一致性前置执行；space workload 进入窗口过期时确认负 delta 与 CHECK 的 SQL 形状冲突并回滚。
- [ ] 需另行授权后，将“确保 totals 行存在”与“只对既有非负 totals 执行 set-based UPDATE”分离设计，再以全新证据根重做语义门禁；不得在本轮重跑。
- [ ] plain 1+5、stage companion、产品 0005/repository 均未执行。

## V18 set-based rolling projection（2026-08-31，当前权威状态）

状态：`step_5_v18_set_based_projection_authorized / synthetic_preflight_pending`。

- [x] 核对 main/功能 worktree、33 tracked + 52 actual untracked、staged 0、10 migration、V16/V17 哈希、产品 0005 不存在及路径边界。
- [x] 预登记 `E:\Agent\cyber-town-f009-step5-tests\performance-v18-projection-set-based` 及准确 surface；生命周期至 Step 5 收口，用户手动回收，Codex 不删除。
- [ ] 失败优先锁定 set-based delta、单查询 totals、聚合 expiration、回滚/负值/隐私契约。
- [ ] 运行 semantic、space、统一 plain 1+5 与独立 non-gating stage companion。
- [ ] 仅全部 synthetic 门禁通过时实施 append-only 产品 0005/repository 及产品回归；否则立即停止。

## V15 测量协议统一与归因计划（2026-08-30，当前权威状态）

状态：`step_5_v15_protocol_attribution_complete / awaiting_next_performance_authorization`。

- [x] 失败优先锁定统一协议版本、warm-up、固定pair顺序、1000 execution、五轮聚合和plain/non-gating边界；红测`3 failed / 38 passed`。
- [x] plain每轮记录GC、CPU、wall、thread与order metadata；逐请求正式样本不运行stage探针。
- [x] 相同协议运行独立stage attribution companion，固定12-stage allowlist、顺序非嵌套计时、metadata-only输出。
- [x] 定向测试`41 passed`，ruff、format、mypy、tracked/untracked whitespace与隐私检查通过；一次24,000 execution有界协议验证完成。
- [ ] 下一步需单独授权：用统一协议重新验证rolling projection synthetic候选，不复用旧根或旧摘要；任何语义/稳定性/绝对门禁失败即停止。
- [ ] synthetic统一协议全绿后才能再次申请产品0005；完整核心矩阵、Step5综合验收和Step6仍未执行。

## V14 产品 0005 核心门禁失败后的计划（2026-08-30，当前权威状态）

状态：`step_5_v14_product_core_gate_failed / awaiting_next_performance_authorization`。

- [x] synthetic 前置语义、空间、稳定性和有界 p95 补证完成。
- [x] 按授权失败优先实施产品 `0005`、repository rolling projection、产品测试与 benchmark 接入；产品专项 `18 passed`，相关兼容回归 `168 passed`。
- [x] 运行唯一完整 warm-up+5-run 核心矩阵并保留全部样本；SQLite observability、拒绝路径、空间/归属门禁通过。
- [ ] 冻结门禁仍失败：in-memory p95 `2.2077ms >2ms`；默认 HTTP control-on p99 `412.2446ms >400ms`；control-on p95 增量 `102.9848ms >30ms`。
- [x] 按停止条件精确回退且不保留产品 `0005`/repository/产品测试/benchmark 接入；回退后 `149 passed`、ruff、format、mypy、diff check 通过，功能文件集合恢复为 `33 tracked + 52 untracked + 0 staged`。
- [ ] 下一步需另行授权，只能先复核产品矩阵与 synthetic 有界补证之间的工作量/尾延迟差异，并设计新的可证伪候选；不得追加同候选矩阵寻找通过结果。
- [ ] 性能 P1 解决且核心门禁全绿后，才可申请恢复 Step 5 综合验收；Step 6、Git 交付未授权。

## V14 corrected projection p95 补证后的计划（2026-08-30，当前权威状态）

状态：`step_5_v14_p95_attribution_passed / awaiting_product_0005_implementation_authorization`。

- [x] 新根、AB/BA顺序、相同工作量、五组固定运行和共同基础阻塞判据失败优先锁定；最终候选测试`16 passed`。
- [x] 唯一补证批次完成：recorded p95/p99=`1.9879/2.62ms`、paired throughput=`103.8042%`、corrected stability=true。
- [x] baseline/recorded共同p95超限仅2/5，未形成>=4/5共同基础稳定阻塞；GC、进程CPU/墙钟、顺序metadata完整落摘要。
- [x] ruff、format、mypy、tracked/untracked whitespace、migration hash、隐私和正式数据库检查通过；未创建产品0005。
- [ ] 下一步仅在单独授权后实施既定候选A产品0005/repository/测试；先迁移、等价、recovery和rollback，再跑核心矩阵。
- [ ] 产品通过核心矩阵后才可申请恢复Step5综合验收；Step6、Git交付仍未授权。HTTP多durable commit阻塞继续单独开放。

## V14 synthetic 稳定性验证 v2 后续计划（2026-08-30，历史状态）

状态：`step_5_v14_validation_corrected_absolute_performance_gate_failed / awaiting_next_performance_authorization`。

- [x] 将稳定性分段改为等工作量的 `101—200 / 501—600 / 901—1000`，排除第61次开始额外1h过期处理造成的旧口径偏差。
- [x] 聚合全部5个正式 run，记录逐轮分段结果和统一 workload signature；新增契约测试后最终 `14 passed`。
- [x] corrected stability 通过：aggregate median `0.1988 -> 0.20785 -> 0.2244ms`，`stable_tail=true`。
- [x] 语义、空间和配对吞吐继续通过。
- [ ] corrected validation 的 recorded p95=`2.3483ms >2ms`，且同轮 no-recorder p95=`2.1569ms`；绝对门禁失败，产品0005不得实施。
- [ ] 另获授权后只能先选择有界的绝对 p95 补证或门禁复核，不追加有利批次、不降低阈值；产品 migration/repository、核心矩阵、Step 5 综合验收与 Step 6 均保持未执行。

## V14 rolling projection D1 失败后的计划（2026-08-30，历史状态，已由 v2 修正）

状态：`step_5_v14_projection_preflight_failed / awaiting_revised_projection_design_authorization`。

- [x] 基线、证据、路径和资源登记预检。
- [x] 候选 DDL、生命周期 delta、rebuild、严格 cutoff、并发与隐私红绿测试；最终 `12 passed`。
- [x] 100 execution 空间门禁通过：`196608 <= 262144 bytes`。
- [x] 完整 in-memory p95/p99 与配对吞吐通过：`1.428/2.13ms`、`97.6981%`。
- [ ] 历史稳定性失败：reserve median `0.1731 -> 0.21145 -> 0.23855ms`，不得落地产品。
- [ ] 另获授权后只读分析 scope-row B-tree/UPSERT/read 成本，形成修订候选；不得直接新增 migration、索引、缓存或批次。
- [ ] 产品 0005、repository、产品测试、核心矩阵、Step 5 综合验收与 Step 6 均保持未执行。

## V14 rolling projection 实施计划（2026-08-30，当前权威状态）

状态：`step_5_v14_projection_implementation_authorized / synthetic_preflight_pending`。

- [x] 只读预检正式 main 五文档、功能 33 tracked/50 untracked/staged 0、两处 HEAD/origin/main、旧 migration 与 V13 证据指纹。
- [x] 预登记 D1/product 两个 E 盘测试根、内容边界、工具解释器、期限和用户手动回收方式。
- [ ] 失败优先建立 candidate DDL/rolling projection synthetic oracle，验证 cutoff、lifecycle、rollback、recovery 和隐私边界。
- [ ] 完成 100 execution 空间门禁及 1000 execution warm-up+5-run in-memory 门禁；任一失败停止。
- [ ] 仅在 D1 全绿后实施 append-only control 0005、repository 投影和产品回归。
- [ ] 重跑核心矩阵与静态/敏感/迁移门禁；HTTP 相对增量只记录，不作为本轮预算投影成功的替代结论。
- [ ] 更新五文档和资源台账；不进入 Step 5 综合验收或 Step 6。

## V14 durable budget/control 架构草案后的计划（2026-08-30，当前权威状态）

状态：`step_5_v14_architecture_draft_complete / awaiting_v14_projection_prevalidation_authorization`。

- [x] 只读确认 V9 的 O(n) budget ledger 扫描是 in-memory 增长热点，V10 SQL 重排无收益。
- [x] 只读确认 HTTP 相对增量主要对应约 9 control commit/request；V13 两盘同失败，介质路线关闭。
- [x] 比较两个候选：A=ledger 派生的 watermarked exact rolling projection；B=跨 execution bounded durable group commit。
- [x] 推荐 A 先做 synthetic D1；B 因 V12 反证和缺少跨 execution 收益证据暂不实施。
- [ ] 另获授权后只在 script/test 中预验证 A 的精确 cutoff、四 scope、lifecycle delta、rebuild、回滚、并发、空间和 in-memory 收益；不得创建产品 0005。
- [ ] D1 必须同时满足语义全等、control growth `<=256KiB`、in-memory p95/p99 `<=2/5ms`、配对吞吐 `>=80%`；任一失败停止。
- [ ] D1 通过并再次授权后，才可实施 append-only 0005 与 sqlite repository 投影；完整核心矩阵通过后再决定是否需要 B。

下一候选根：`E:\Agent\cyber-town-f009-step5-tests\performance-v14-budget-projection`；内容仅 synthetic pytest/TEMP、真实 v1—v4 migration 创建的隔离 control SQLite/WAL/SHM 及 metadata-only 摘要；保留至 Step 5 收口，由用户手动删除，Codex 不删除。本轮未创建。

## V13 存储介质 A/B 收口后的计划（2026-08-30，历史状态）

状态：`step_5_v13_storage_ab_complete / awaiting_next_performance_plan_authorization`。

- [x] Python 3.12 tooling 使用现有 uv/Python 和锁定离线缓存建立；43 包 frozen/offline 审计通过，无网络、无 worktree `.venv`。
- [x] E: USB SSD 与 C: NVMe SSD 的卷/物理盘映射、路径、空间及 reparse 边界复核通过。
- [x] V13 A/B runner 失败优先契约与 E/C TEMP 隔离完成；完整契约 23 passed，ruff/format/mypy/whitespace 通过。
- [x] E/C 各 1 warm-up + 5 run × off/on × 100 execution，同 digest、真实 TCP、独立客户端、逐请求计时完成；总计 2,400 HTTP execution。
- [x] 两盘绝对 HTTP、吞吐、control 空间、dispatch、成本、integrity/FK 与 NoOp observability 边界通过。
- [x] 两盘均命中 `control_on_relative_p95_regression`，按预设结论停止介质路线；不实施 C 盘数据根候选。
- [ ] 另获授权后只读起草 durable budget/control 聚合状态候选：必须保持预算/attempt/dispatch 归属、原子 admission、replay/waiter、取消、重启、WAL/FULL 与安全路径检查，并单独分析 migration 与重建兼容性。
- [ ] 候选经用户确认后才能失败优先实施与核心矩阵复验；相对增量及 in-memory 门禁全部通过后，才可恢复 Step 5 evaluator、三进程 digest、故障组合和完整质量入口。

停止条件：性能 P1、Step 5 和 R-10 保持开放；不得把 C 快于 E 的局部差异当成迁移依据，不追加 A/B 批次，不自动进入 Step 5 综合验收、Step 6 或 Git 交付。

## V13 环境门禁后的计划（2026-08-30，历史状态）

状态：`step_5_v13_preflight_blocked / awaiting_offline_tooling_resolution_authorization`。

- [x] Git、V12 回退、10 migration、旧证据、E/C 路径和介质映射只读预检通过。
- [x] 证明 C 为 NVMe SSD、E 为 USB SSD；目标及 tooling venv 均不存在，父链无 reparse。
- [x] 搜索现有 Python 3.12 环境并执行不落盘的 uv offline dry-run。
- [ ] 离线依赖仍缺 1 包；未获新的离线来源授权前不得创建 tooling venv。
- [ ] 环境解决后重新登记完整资源 surface，再创建 A/B 根、写 runner 红测并运行 E/C 对照。
- [ ] A/B、in-memory 阻塞、Step 5 综合验收与 Step 6 均未执行。

## V12 回退后的下一计划（2026-08-29，当前权威状态）

状态：`step_5_v12_candidate_reverted / awaiting_storage_ab_validation_authorization`。

- [x] 精确移除 V12 四文件事务批次增量及唯一新增专项测试，恢复 `33 tracked + 50 untracked` 文件集合。
- [x] ruff、format、Python 3.12 AST/结构契约和两目录 whitespace 通过；未创建 venv、pytest 根、SQLite、缓存或报告。
- [ ] 另获授权后，先只读确认 E/C 卷介质与路径边界，再建立全新的同工作量 synthetic A/B 根。
- [ ] 以真实 TCP、逐请求计时和各自 warm-up + 5-run 验证正式默认 HTTP；只改变数据根，不改变阈值、WAL/FULL、写入语义或样本。
- [ ] 即使 C 盘对照通过，仍须单独处理 in-memory p95/p99；两项核心门禁全部通过后才能恢复 Step 5 综合验收。
- [ ] 若两盘均失败或差异不足，停止盘介质路线，单独起草 durable budget/control 聚合状态架构，不继续无证据微优化。

## V12 性能候选失败后的计划（2026-08-29，当前权威状态）

状态：`step_5_v12_core_gate_failed / awaiting_next_architecture_authorization`。

- [x] 分离确认 in-memory 预算历史扫描与 control-on 多事务提交根因；否定不稳定 SQL/内存原型。
- [x] 失败优先实现并收窄原子批次；取消前 reservation 释放、批内回滚和单 COMMIT 语义通过。
- [x] 运行完整 warm-up + 5-run；SQLite recorder、拒绝、吞吐、空间、dispatch/成本通过。
- [ ] in-memory p95/p99 `4.3027/5.0302ms` 仍未达到 `2/5ms`。
- [ ] control-on p95 `293.2776ms` 及相对增量 `182.0342ms` 仍未达到 `250ms/30ms`。
- [ ] 另获授权后精确回退 V12 失败候选，或批准新的持久控制架构方案；不得继续无证据微优化。
- [ ] 只有新的核心矩阵全部通过后，才可恢复 Step 5 evaluator、三进程 digest、故障组合与完整质量入口。


## Step 0 门禁边界修订与完整矩阵收口（2026-08-29，当前权威状态）

状态：`step_5_gate_boundary_matrix_failed / awaiting_next_performance_authorization`。

- [x] 失败优先锁定：默认 HTTP 使用 control-on + NoOp；SQLite observability 独立阻塞；三 SQLite 仅诊断。
- [x] 更新性能 enum/契约、benchmark runner、资源 manifest 与对应测试；首次资源前置检查按预期失败且未创建矩阵，修正后再执行。
- [x] 定向契约 14 passed；ruff、format、mypy、diff 通过。
- [x] 完成 1 次 warm-up + 5 次测量：no-recorder、配对 in-memory、SQLite observability、三类 pre-dispatch reject、默认 control-off/on 和三 SQLite 诊断。
- [x] 正式默认 HTTP 绝对门禁、SQLite recorder 独立门禁、空间/dispatch/成本门禁通过。
- [ ] 解决 in-memory p95/p99 3.8461/5.0193ms 对 2/5ms 的失败。
- [ ] 解决 control-on 相对 p95 增量 156.7882ms 对允许 30ms 的失败。
- [ ] 仅在上述阻塞清零并重新完成核心矩阵后，另行申请恢复 Step 5 综合 evaluator、三进程 digest、故障组合与完整质量入口。

停止条件已触发：不得继续 Step 5 综合验收、Step 6 或 Git 交付；不得把三 SQLite 非阻塞化解释为其他门禁自动通过。

## V11 正式运行模式边界验证收口（2026-08-29，当前权威状态）

状态：`runtime_default_slo_passed / awaiting_step0_gate_boundary_decision`。V11 已完成，性能 P1/Step 5/R-10 未完成。

- [x] 只读核对 main/功能分支、33+50 文件集合、83 文件指纹及 10 migration。
- [x] 先登记 V11 根与两库/sidecar/摘要，再建立 3 个失败优先契约测试；红测 3 failed，最小诊断实现后 3 passed，完整契约文件 11 passed。
- [x] 运行单组真实 TCP、独立客户端、两请求并发、100 execution 的 `control-on + NoOp observability`；p95/p99 157.1363/173.28ms、吞吐 14.865986/s、失败码 0。
- [x] 核对 business/control WAL/FULL、integrity/FK、100 次 execution/dispatch/预算/关系归属、成本 0、observability SQLite 0。
- [ ] 用户确认 Step 0 门禁边界：默认 HTTP、独立 SQLite recorder、三 SQLite 非阻塞诊断三者分离。
- [ ] 获得单独授权后，失败优先调整性能契约与 benchmark 场景；不得改变阈值、产品运行语义或 recorder 默认值。
- [ ] 新契约通过后再运行正式 warm-up + 5-run 核心矩阵；全部门禁通过后才恢复 Step 5 evaluator、三进程 digest、故障组合与完整质量入口。

停止条件：用户未确认门禁边界前，不继续介质 A/B、事务架构改造或最终矩阵；若后续默认运行五轮仍失败，恢复性能 P1 并重新申请介质/架构调查授权。

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


完整建议授权Prompt见current-task当前首节；未获用户确认前不创建候选根、不改诊断文件。

## V8 最小性能修复收口（2026-08-27，历史执行记录）

状态：`step_5_v8_core_gate_failed / awaiting_next_authorization`。两处最小产品修复及磁盘语义回归通过，但核心性能门禁失败；**性能 P1、Step5 和 R-10 仍开放**。本轮已停止，不执行 Step5 综合验收、Step6、进一步调优或 Git 交付。下方 V7 及更早章节均为历史记录，不覆盖本节。

执行进度：①只读预检完成；②资源预登记及红测完成；③两处最小修复及磁盘回归完成；④完整核心矩阵已执行但失败；⑤文档/资源收口完成，停止等待授权。

- 产品仅 dialogue.py 与 sqlite_control.py：request owner 锁和 player+npc commit/revision 保护将磁盘 await 移出全局幂等锁；pending admission 计入容量，同 request 仍单 admission/execution/dispatch。按 request→owner 固定顺序，锁持有者及排队者引用计数防止锁实例替换；取消仍等待实际落盘，已完成业务/缓存/结算不回滚。
- 预算仍为同一 BEGIN IMMEDIATE 中单条固定参数化聚合，返回四 scope 的12项统计；等价使用 FILTER 减少重复计算，保留严格 cutoff、released 排除、reserved/dispatched 预留成本、settled 实际成本、warning/reject顺序和回滚。未增索引、计数表、缓存或 migration。
- 局部收益：1000行同数据预算查询 VM 步数 111036→52107，下降约53.1%；一组100次配对查询均时 1.332046→0.733808ms。此为局部对照，不代表端到端门禁通过；不同scope阻塞红测证明进展能力恢复，不等同总体尾延迟已解决。
- 本轮实际改动6个获准文件：2产品、2测试、2脚本；test_attribution_step5.py未改，既有取消修复保持。脚本只调整批准根/测量接入，不改工作量/阈值。

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

- 红测3项：2个跨scope进展场景与1个预算VM等价/收益场景。修复后共199项不同测试通过：budget/async 94 + attribution 103 + 已单独运行的跨scope 2；先前27项绿测有重叠，不重复累计。
- 覆盖原33项磁盘取消、fresh/replay/waiter/owner-with-waiter、排队/运行/阶段提交后一次及重复取消、persona、orphan/迟到/旧generation、关闭/重启/abandoned/重复recovery、真实长期记忆写入/忘记/替换/owner隔离、预算边界/状态/顺序/并发/回滚。
- 本轮256个绿测/矩阵新库 integrity/FK、WAL/FULL 与闭合trace阶段检查通过；6个红测库仅保留，未拿失败阶段数据冒充最终验收。HTTP含warm-up共1200 trace/16800 stage、1200 dispatch、1200关系事件；control-on 600次结算实际成本0。语义用例验证真实长期写入；核心HTTP长期表为空，不能称长期写入性能验收。
- 7个允许文件定向ruff、format、mypy通过；两处tracked diff check及50个untracked no-index whitespace通过。77个未变功能文件、10 migration、5份旧证据及18份V7归因JSON指纹均不变；83文件最新指纹见 evidence。
- metadata摘要禁字段/固定原文sentinel命中0；没有读取.env、外网/真实模型/F005访问。FakeProvider链路成本0；预算专项中的明确synthetic价格样例不属于真实计费。
- 正式/功能6条运行时数据库路径均不存在，8000及12个矩阵临时端口均无监听。未运行 evaluator/digest、完整质量入口、Step5综合或Step6。

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

### 下一步阶段门禁

V7补证已完成→等待上述两处产品热点最小修复授权→语义先行→冻结完整核心性能复验→通过后再申请Step5综合→Step6仍需独立授权。精确文件清单、新根与Prompt见[current-task](current-task.md)。本轮没有推进任何后续门禁。



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


## V7取消修复部分实施，等待replay契约授权（2026-08-27，历史状态）

状态：`step_5_v7_cancel_fix_partial / awaiting_cache_replay_contract_authorization`。Step0—4完成；取消P1尚未完整解决，性能P1/Step5/R10开放；Step6/7未进入。

红测3项失败确认排队遗留open、运行中/阶段提交后取消未传播。产品仅dialogue.py将RESPONSE_MAPPING纳入原取消try并在drain后检查取消；两个获准脚本/测试文件仅做资源配置与专项扩充。绿测35 passed/1 failed：工具25、persona8、原复现1、fresh归属/重建1通过；cache replay排队取消触发observability DTO校验错误，剩余22场景停止。原复现现complete/cancelled、14阶段、finish1，provider/关系/预算各1，无重复写入。

阻塞：CACHE_REPLAY DTO要求from_cache=True且终态只能REPLAYED；取消需要CANCELLED，单改dialogue无法保持真实attempt身份和终态。需要新增application/observability.py精确契约授权，本轮未修改；不把取消伪装为成功replay。下一步只建议授权兼容cache-replay cancelled组合与正确from_cache传递，再验证完整取消矩阵，不能宣告性能达标。完整授权Prompt见[current-task](current-task.md)。

3文件ruff/format/mypy、tracked/50untracked whitespace、定向sensitive/ignore通过；其余80功能文件、10migration及旧V5/V6/V7证据哈希不变。正式main五文档，功能33tracked+50untracked，两处1a4fc2c；正式数据库不存在，8000无监听。未提交/推送/PR/部署/删除。

新根performance-v7-cancel-fix现42files/17dirs/6,365,184bytes，建议保留至Step5收口，用户手动回收。旧V7及四缓存未变；Step5父根3070files/2269dirs/439,299,570bytes。完整路径、已创建/仅计划状态和手动处置条件见[evidence](evidence.md)。性能采样、最终矩阵、综合验收均未运行；以下记录为历史。


## V7 已确认取消缺陷，暂停归因（2026-08-27，当前地图）

状态：`step_5_v7_semantic_gate_failed / awaiting_response_mapping_cancel_fix_authorization`。Step0—4完成；Step5性能P1未解决；Step6/7未进入。

| V7子门禁 | 本轮结论 |
| --- | --- |
| Git/10migration/V5/V6证据预检 | 通过；既有81功能文件不变 |
| 工具归属、隐私、资源边界TDD | 17+8预期红测；最终25 passed，写入尝试0 |
| persona真实磁盘取消 | 8 passed；complete/cancelled、14阶段、finish1、dispatch/成本/写业务0；重建与两次recovery不变 |
| response_mapping排队取消 | **P1确认：open、12阶段、finish0；已dispatch1/关系写入1/预算结算1** |
| 剩余磁盘取消/长期记忆正向写入/完整owner矩阵 | 未运行，不能由空长期表或row count替代 |
| 1 profile + 2 plain | 按缺陷停止，未运行 |
| 最终性能/Step5综合/Step6 | 未运行、未授权自动恢复 |

下一步最小产品候选只改application/dialogue.py的response_mapping取消收口，专项扩充test_attribution_step5.py；诊断脚本只做新测试根配置。新候选根performance-v7-cancel-fix尚不存在，所有实际子路径必须另获授权后先列出登记。先红测，再最小修复，再磁盘/关闭/重启/幂等回归；产品范围不足或新缺陷即停止。修复通过只代表取消正确性，不宣告HTTP/内存性能达标，需再确认恢复V7归因。

本轮2新文件ruff/format/mypy、whitespace、ignore/sensitive通过；功能33tracked+50untracked，正式main五文档，两处1a4fc2c。资源V7=30files/13dirs/4,546,560bytes，建议保留；完整P1复现、资源台账、下一条产品授权Prompt见[current-task](current-task.md)与[evidence](evidence.md)。不修改产品、不提交、不删除。

以下是此前计划历史，不覆盖当前门禁。


## V7 补证计划待授权（2026-08-27，当前地图）

- Step0—4完成；Step5性能P1阻塞；V6-CANCEL-01已最小修复且113项内存回归通过，磁盘重验未做；Step6/7未进入。
- 当前状态：`step_5_performance_gate_failed / awaiting_v7_attribution_authorization`。本轮只读调查已完成，不等于产品修复完成。
- 正式main五文档、功能33tracked+48untracked、两处1a4fc2c、81功能文件/10migration指纹及V5/V6摘要哈希一致。功能分支不改、不提交。

### 推荐且唯一当前候选：先补归因，再选择产品修复

1. 另获授权才新增 `E:\Agent\comprehensive-cases\15-cyber-town-f009\scripts\f009_step5_attribution.py` 和 `E:\Agent\comprehensive-cases\15-cyber-town-f009\backend\tests\test_attribution_step5.py`。不改现有产品/benchmark/SQL。
2. 候选根 `E:\Agent\cyber-town-f009-step5-tests\performance-v7-attribution` 当前不存在；准确子根和逐case/SQLite/pytest资源清单按[任务卡V7方案](current-task.md)创建前展开、成功打印、登记后再创建，禁止复用basetemp。TEMP/TMP固定候选tmp，不建venv、安装依赖或授权外缓存。
3. 诊断工具先红测：逐operation归属、并发线程记录保护、互斥区间计算、metadata-only、资源清单失败前置；不得复用SteadyProfile的全局phase/segment来给线程分账。
4. 真实三库磁盘取消验证先行：persona八组合、response_mapping排队/开始/commit后、重复取消、budget归属、waiter/orphan/旧generation、close/drain、事务rollback、restart abandoned及实际长期写入隔离。新response_mapping问题仅静态风险，若复现则停止申请独立产品修复，不自行修。
5. 语义通过后仅一组profile + 两组plain：HTTP off/on×单/双并发，各100execution；内存off/on各1000execution。初始化和稳态分开，真实TCP独立客户端逐请求计时。profile按server单调时钟做span关联；plain关闭探针，不能直接用两组plain替代最终五轮。
6. profile至少区分slot/queue/worker/await恢复、幂等锁与scope锁wait/hold、writer/path/connect/BEGIN/SQL/write-commit/close；预算按前100/中800/后100报告VM与耗时。重复或跨线程错分、无法解释残差须报告，不把inclusive时间相加。
7. 证据足够后输出最小产品修复文件与收益判据，另行授权才实现。预算SQL重写、业务连接复用、移动全局锁边界均未获许可。证据不足或要求破坏冻结边界则停止。

### 产品修复获批后的顺序（不是本轮许可）

失败优先→最小产品改动→取消/并发/故障/重启/真实长期写入语义→完整无profiling warm-up+5-run（所有原场景/样本/阈值）→全绿后申请Step5 evaluator/digest/故障组合/full-quality。任何门禁失败停止，不进入Step6。

冻结阈值、14-stage、durable open/restart abandoned、每次lease安全检查、WAL/FULL、预算/幂等/业务/API/Godot/全部migration不变。combined只计control+observability，memory严格配对，不减少写入或删除慢样本。

本轮只新增五文档内容，无测试/profiling/新资源或删除。现有Step5根2998files/428387826bytes（含V6子集1660/220710337）及worktree/四缓存继续保留；收口后由用户手动回收，详见任务卡资源台账。下文是历史地图，不覆盖本节。


## V6-CANCEL-01 修复收口（2026-08-27 19:28 +08，当前状态）

当前地图：Step0—4完成；Step5取消缺陷已修复、性能P1继续阻塞；Step6/7未进入。本轮无权恢复Step5性能修复或综合验收。

V6-CANCEL-01：`fixed / in_memory_regression_verified`。用户仅授权取消收口最小修复，现已完成；整体仍为 `step_5_performance_gate_failed / awaiting_remaining_performance_plan_authorization`，性能P1/Step5/R10未完成，Step6未进入。

根因已以真实AsyncSqliteExecutor+内存durable协议fake复现：persona等待在统一try之外，排队取消遗留open；未知persona的已开始写入在drain后未检查取消，误走npc_not_found拒绝。红测6 failed/2 passed；把persona处理纳入既有try/CancelledError收口，并在未知persona写入返回后检查取消。仅修改功能application/dialogue.py和既有backend/tests/test_dialogue_async_persistence.py，未修改observer/worker/仓储/预算/SQL/migration/API/Godot/阈值。

新增9专项：已知/缺失persona × 排队/已开始 × 一次/重复取消8例，加未取消的未知persona拒绝1例。取消trace只finish一次、complete/cancelled、14-stage、execution未创建、dispatch/成本0、synthetic原始scope/message/key序列化命中0；未取消仍为rejected/npc_not_found/not_reached、不可retry。最终相关回归 **113 passed，1.98s**；2文件ruff/format/mypy通过；48untracked whitespace和两处tracked diff通过；10migration哈希不变，其余79个既有dirty文件指纹不变。两文件敏感扫描0、ignore违规0；其他文件的两个既有ContextVar命名提示不在此次修复范围，未称完整quality全绿。

本轮无新增临时资源：测试-s禁用落盘capture，禁用pytest cache/bytecode；进程审计钩子拒绝写文件、建目录及磁盘SQLite。首次启动误拦pytest日志NUL设备，发生在打开前，无文件创建；只放行准确os.devnull设备后，红/绿及最终回归filesystem_write_attempts=0。未创建/打开/复用旧SQLite，未重跑磁盘集成、HTTP性能矩阵、evaluator、digest、完整quality或CI。内存fake验证的是取消控制流和recorder调用契约，不冒充磁盘durability/restart验收；后续磁盘重验需先确认新子路径。

正式main仍仅五文档；功能分支feat/f-009-safety-cost-performance仍33tracked modified+48实际untracked；两处HEAD/本地origin/main均1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3。未提交、推送、PR、部署、切换分支、创建worktree或删除资源。已有性能证据仍是V6四项失败，不能用此次113绿测替代性能达标。

资源只读复核：E:\Agent\cyber-town-f009-step5-tests仍2998files/2237dirs/428387826bytes；其内performance-v6-async仍1660files/1323dirs/220710337bytes。四缓存.ruff_cache=5files/6682bytes、.mypy_cache=3/38301925、backend/.mypy_cache=4/34480371、game/.godot=6/3079，均未改变盘点；reparse/env-like/嵌套Git均0。**现在继续保留全部Step5证据、功能worktree与缓存；本轮新增0，无需新增清理。** 到Step5收口再由用户手动回收精确测试子根；完整路径、删除影响、不可从Git恢复及安全命令沿用下面V6资源台账，Codex不代删。

下一步仅建议用户另行授权剩余性能方案调查；预算扫描、HTTP架构修复及新测试子根/矩阵不能自动继续。已完成的取消修复无需重复授权。以下此前“取消待复现/修复”的记录均为历史状态，不覆盖本段。


## 此前记录（历史快照）

## V6 当前收口（2026-08-27 18:46 +08）

当前阶段地图：Step0—4完成；Step5性能P1阻塞（V6核心四项门禁失败，取消收口风险待复现）；Step6独立QA未进入；Step7 UAT/交付准备未进入。不得把V6实现或414项定向绿测等同于Step5完成。

状态：`step_5_performance_gate_failed / awaiting_v6_followup_authorization`。V6已实施有界异步仓储调用和关闭生命周期，但P1/Step5/R10仍开放，未进入Step6。414相关测试通过（含28新专项）、1个旧单次性能测试排除；11文件ruff/format/mypy、10migration哈希、tracked/48untracked whitespace通过。新增取消边界静态缺口V6-CANCEL-01（persona排队await在终态try之外）尚待定向复现/修复，不能以现有绿测覆盖全部取消时点。

完整核心1warm-up+5-run仍失败：内存p95=2.7913ms>2；HTTP on p95/p99=696.8400/872.0176ms>250/400；相对off p95增量261.3869ms>87.09062。off p95/p99=435.4531/591.6488；内存配对吞吐98.37%；SQLite recorder汇总p95/p99=73.7811/187.4854ms，吞吐15.880428/s；三类拒绝dispatch0。combined增长652—668KiB、业务另列60KiB。已停止evaluator/digest/故障综合/完整quality，未降低阈值或继续扩展修复。SQL预算扫描未获新授权，未修改。

60新matrix库integrity/FK通过；18obs库各100trace/1400stage/100dispatch/0成本；49metadata表面×10sentinel命中0。核心长期表为空，实际长期写入/同库重建隔离另由专项验证；不宣称完成长期写入性能。81dirty文件敏感扫描仍有两项既有ContextVar token命名提示，不称完整quality或CI全绿。

正式main仅五文档，功能33tracked+48untracked，两处HEAD/本地origin/main=1a4fc2c。仅本轮授权11文件变化，其余既有内容和migration保持。正式/功能三类正式DB不存在，8000及12临时端口释放。无提交/推送/PR/部署/删除。

资源：V6 E:\Agent\cyber-town-f009-step5-tests\performance-v6-async 为1660files/1323dirs/220710337bytes；Step5全根2998files/2237dirs/428387826bytes（父子不重复计）；原V3/V4/V5及四缓存盘点未变。V6 reparse/env-like/嵌套Git均0，不在Git内；四缓存共18ignored文件。当前建议保留到Step5收口，再由用户手动回收，Codex不删除。234files/75041988bytes的活动功能worktree含未提交代码，必须保留。准确逐项路径、创建时间、期限、手动命令、不可恢复性和所有轮次见[current-task.md](current-task.md)最前V6收口节。

证据：E:\Agent\cyber-town-f009-step5-tests\performance-v6-async\matrix-01\performance-summary.json，SHA256 19A78F01793340F2D6EFFA9571ACF1DA00FDB8E78B816E0FE02A2DF210B872AE；预登记matrix-plan.json和6份资源JSONL均保留。下一步先授权取消收口最小修复和只读分析，预算/HTTP新方案须明确边界，不自动扩大实施。


## V6之前的阶段与授权历史（保留追溯，不覆盖上述当前状态）

最新V6授权登记（2026-08-27）：`step_5_async_boundary_authorized / awaiting_test_resource_confirmation`。用户已授权V5所列最小产品异步边界，不重复申请产品权限；三份新增专项测试、benchmark最小接入与全新E:\Agent\cyber-town-f009-step5-tests\performance-v6-async尚待准确清单确认，均未创建/修改。已完成只读预检：main五文档、功能32tracked+44untracked、两处HEAD/本地origin/main=1a4fc2c，10migration及原74文件指纹不变，V5摘要哈希不变。没有运行测试或创建资源，P1/Step5/R10仍开放。现有Step5根1338files/207677489bytes和四缓存保持不变，建议保留；V6不存在，无需清理。详细授权边界、测试清单、候选子路径和用户手动回收规则见current-task最前V6节。以下V5及更早内容为历史记录，不覆盖本段；预算扫描优化仍需另行授权。

最新V5（2026-08-27）：step_5_v5_diagnostic_complete / awaiting_product_async_boundary_authorization。完成4000内存+400真实TCP诊断；普通计时memory-on p95/p99=3.1586/3.9606ms，HTTP single=259.9669/482.1753ms、pair=699.9403/900.3817ms。不是warm-up+5-run或修复收益。pair profile事件循环延迟p95=173.356ms，显式锁等待较短；内存预算单查询VM估算由前段4030/次升至后段75460/次，后段聚合约占预算预留87%。不得相加nested耗时或宣告阈值不可达。

按授权停止原型：同步stage/预算协议没有await边界，关系写入还受幂等锁及active waiter/revision检查保护；只替换仓储无法忠实异步接入，未复制/改写产品链路。下一步需单独授权application observability/control/dialogue、API dialogue/composition/app与候选async_sqlite适配器及必要测试；精确方案见current-task最前V5节。未执行worker取消/迟到/重启原型，也未补长期记忆写入。P1/Step5/R10不完成，不进入Step6。

新增仅诊断脚本和测试2文件，原74文件及10migration哈希不变；正式main五文档、功能32tracked+44untracked，两处HEAD/origin/main仍1a4fc2c。10专项、两文件ruff/format/mypy/whitespace通过；12新SQLite完整性/FK通过，4组各100trace/1400stage/100dispatch/零成本，9metadata surface×8sentinel命中0。新文件敏感扫描0，V4两项命名提示仍保留，未跑全量quality。正式DB不存在，8000及4临时端口释放。

V5根E:\Agent\cyber-town-f009-step5-tests\performance-v5-architecture为13files/10dirs/4710307bytes；12SQLite+1JSON，无剩余sidecar/reparse/env-like/嵌套Git。V3/V4与缓存未动，Step5父根1338files/913dirs/207677489bytes。建议现在保留至Step5收口，之后用户手动回收，Codex不删除。精确子路径、SHA256、风险和手动命令见current-task的V5台账。

以下V4及更早内容为历史快照，不覆盖上述V5状态。

状态：F-009 / step_5_v5_diagnostic_complete / awaiting_product_async_boundary_authorization，性能P1开放。

最新V4结论（2026-08-27 17:15 +08）：step_5_performance_gate_failed / awaiting_revised_performance_plan。可行性调查、逐次路径校验去重和预算4→1聚合已完成，170相关回归与7文件ruff/format/mypy通过；核心warm-up+5-run仍失败：in-memory p95=2.607ms，HTTP control-on p95/p99=595.2054/826.5936ms，相对p95增量227.577ms>73.52568ms。四个稳定失败码见current-task最新V4节；P1/Step5/R10不关闭，Step6未授权。

SQLite recorder五轮汇总、吞吐、零dispatch拒绝和各库增长通过；66个新性能/诊断库integrity/FK/14-stage/零成本通过。敏感扫描2项ContextVar局部变量token命名提示尚未消除，不能称完整quality/CI全绿。初次96个跨fixture UUID匹配已核实为合法request_id，按实际scope重核的55个metadata surface原文命中0；不是完整evaluator验收。

正式main仍五文档；功能指定分支32tracked modified+42untracked，原74文件仅本轮允许7个变化，10migration哈希不变，两处HEAD/本地origin/main=1a4fc2c。正式三类库不存在，8000及登记服务端口释放。没有提交、推送、PR、部署、旧证据复用、删除或后续综合验收。

V4新根E:\Agent\cyber-town-f009-step5-tests\performance-v4-gate，创建16:52:37+08，455files/336dirs/55719927bytes；V3仍178/115/22407848，整个Step5根1325/902/202967182。无reparse/env-like/嵌套Git。工作树和既有4类缓存保留，精确子路径、文件数、大小和用户手动回收命令见current-task最新V4台账。现在建议保留至Step5收口，Codex不删除。

流程遗漏已告知用户：矩阵逐项资源清单命令失败后未检查返回码就启动，详细清单补报晚于部分子目录创建；全部资源仍在批准matrix-01内，没有越界。后续创建必须以前置清单输出成功为条件，不把补报冒称事前报告。下一步等待重新确认剩余性能/架构与命名门禁方案，不继续未经授权的异步或业务连接改造。


以下为V3及更早历史计划快照，不代表V4已通过。

最新诊断先行轮已完成：分库稳态/独立HTTP客户端证实预算重复聚合和路径检查/同步提交热点；原事务内12→4聚合最小优化完成，25项新增专项与132项相关回归通过，四文件ruff/format/mypy通过。带profiling复测in-memory p95=3.1644ms、独立HTTP control-on p95/p99=627.1403/724.9823ms，仍不足以通过冻结门禁；未重跑最终完整五轮矩阵，不进入Step6。仅改control仓储/预算测试并新增诊断脚本/测试，全部migration及业务/API/Godot未动。下一步需单独确认剩余路径校验/SQL方案，禁止扩大异步架构或削弱安全检查。资源178files/22407848bytes及精确台账见current-task最前收口节。

当前任务：[`F-009《安全、成本与性能优化》`](current-task.md)，来源于 roadmap `R-10`。

## 阶段状态

| Step | 状态 | 实施边界 |
| --- | --- | --- |
| 0 | complete | 威胁、JSON/identity、限流/预算/retry/breaker、存储、API、隐私与性能阈值已锁定 |
| 1 | complete | 严格 HTTP/JSON/identifier、固定安全 enum/input policy、provider response firewall、schema 与 Godot 错误映射已完成 |
| 2 | complete | token bucket、原子 admission、provider permit、control SQLite、门禁和用户手动资源收口均已完成 |
| 3 | complete | 预算预留、attempt 配额、成本结算、restart recovery 与 metadata-only observability `0002` 已完成 |
| 4 | complete | provider timeout、有限 retry、取消传播、持久化 circuit breaker 与 Step 4 门禁已完成 |
| 5 | complete | V33最终收口覆盖早期失败；旧行原文保留在evidence，不代替本轮QA |
| 6 | blocked | S6-QA-001及v8断言同步通过；S6-QA-002原生资源登记待解决，完整quality/唯一1+5性能未收口 |
| 7 | awaiting authorization | Step6通过后另行申请，本轮不进入 |

功能 worktree 为 `E:\Agent\comprehensive-cases\15-cyber-town-f009`，分支为 `feat/f-009-safety-cost-performance`，当前改动未提交、未推送。正式目录只保存任务卡、计划、进度和证据更新，不得把文档混入功能 worktree。

历史执行快照（已由V33最终收口覆盖）：C空间门禁通过后已实施两份0004和有界连接复用；132项迁移/连接/控制回归、8项测量专项通过。核心性能运行完成但门禁五项失败，不能继续Step5剩余验证。详见[当前任务卡](current-task.md)末节；以下索引/D0/D1段落为历史阶段快照，不代表当前仍未实施0004。当前阶段以最前Step6节及阶段状态表为准。

条件式实施顺序与实际结果：

1. **已执行、失败并停止**：固定 10 个非唯一索引的候选主文件增长为 control 264 KiB、observability 648 KiB、合计 912 KiB；扣除基线空闲页复用的占用增长为 280/672/952 KiB，均超过 256/512/768 KiB。两组各 100 completed、1400 stage、300 cost event、200 retry/breaker event；没有省略事件来制造通过。
2. **未执行**：产品新旧库迁移/事务回滚验证、两个 `0004_compact_secondary_indexes.sql` 与 migration 清单更新。
3. **未执行**：连接生命周期修复、原 benchmark 的 in-memory/真实 HTTP 计时纠正及完整 warm-up + 5-run 复验。本次 ASGI 空间实验不作为最终 TCP/HTTP 延迟门禁。
4. **未执行**：原 Step 5 evaluator、三进程最终 digest、故障组合和完整回归；仍不能进入 Step 6。

用户随后批准的只读修订方案起草已完成，详见任务卡“Step 5 P1 修订存储与性能方案”；该起草轮没有测试、SQLite 连接或新资源。之后获准执行的 D0 结果见下方地图，P1 和 Step 5 仍未完成。

## 修订方案的授权地图（D0 完成，D1 失败并停止）

1. **D0，已完成并停止**：15 项定向测试、两组各 100 execution，物理页/字节归属守恒。候选 control 表/约束索引/非唯一索引增长为 180/76/24 KiB，observability 为 360/232/76 KiB；合计 280/668/948 KiB，仍超过 256/512/768 KiB。完整事件、行数/完整性、零 fake 成本与 sentinel 检查通过；不是延迟验收。
2. **D1，已授权执行并失败停止**：只试 B：4096 页、原十个非唯一索引、任务卡列明八叶表 WITHOUT ROWID；未试 A。48 项定向测试通过，100 unique execution/三 NPC/三库同数据对照完成。主文件增长 204/588/792 KiB；排除 freelist 后占用 232/632/864 KiB，observability 与 combined 仍超过 512/768 KiB。逻辑字段/约束、具名索引边界、增量阶段与重启保持；不得扩大表/索引清单。
3. **D2，空间/语义预验证通过后另行批准**：先失败优先验证新旧库、回滚、完整约束、CLI/重启，再实施确认后的两份 append-only `0004`；旧八份 migration hash 不变。
4. **D3，独立性能修复**：先分离初始化与稳态 profiling，再最小化连接生命周期开销；原事务/逐 stage 持久化、同步强度、路径安全检查不能退让。连接方案不计作空间修复。
5. **D4，完整矩阵与续行门禁**：纠正 combined=control+observability、in-memory 同工作量配对、真实 TCP HTTP 逐请求计时；保持 warm-up + 5-run、完整样本和全部绝对/相对冻结阈值。全矩阵通过后才恢复 evaluator、三进程 digest、故障组合与完整回归；否则继续阻塞。

D0 唯一新子根 `E:\Agent\cyber-town-f009-step5-tests\storage-breakdown-v2` 为 7 files/3 dirs/3,481,274 bytes，诊断结束、保留作为证据。八叶表 PK 索引增长为 control 52 KiB、observability 112 KiB；后者比本轮 156 KiB 缺口少 44 KiB，不能据此保证 B 成功。D1 只建议 synthetic 预验证，不直接实施产品迁移；精确八表/原十索引、资源与下一 Prompt 见任务卡。

原测试根含新 D0 后为 93 files/36 dirs/39,557,163 bytes；旧 index-v4-preflight 盘点未变。ruff/Godot 缓存未动，mypy 复用后 16-byte missing_stubs 标记由工具正常维护，不再存在。建议保留所有失败/诊断证据；若用户放弃 D0 可在检查占用后手动回收精确子根，Codex 不删除。功能原 59 文件指纹不变，仅新增两个 D0 文件，当前 31 tracked + 30 untracked；P1/Step 5 未完成，不进入 Step 6、提交、推送、PR 或部署。

### D1 最终收口（取代上述 D0 时点的资源/文件数量）

D1 33 + D0 12 + index 3 = 48 passed；ruff/format/定向 mypy/whitespace 通过。仅新增布局诊断脚本与测试，原 61 文件指纹不变，功能当前 31 tracked + 32 untracked；正式仍五文档。八旧迁移不变，无产品 0004。

首轮诊断遗漏业务迁移 `applied_at` 的摘要排除，通过 1 failed/2 passed 的专项红测纠正；首轮中止文件保留，不作验收。新的 `layout-preflight-v2/paired-fixed` 使用固定 ID/时钟/顺序，三库逻辑行 digest 配对完全相同；工作负载时间没有从 digest 中删除。各组 100 completed/dispatch、1400 stages、300 cost/200 retry-breaker、100 durable-open/1300 progress 读回；restart 9 个增量阶段后只收口 1 abandoned，重复 recovery 0。6 个 metadata surface/110 sentinel 命中 0。

D1 新总根 `E:\Agent\cyber-town-f009-step5-tests\layout-preflight-v2` 为 17 files/8 dirs/6526123 bytes；有效 paired-fixed 为 8/3/3572875，其余首轮非验收文件合计 2953248 bytes。包含 14 synthetic SQLite、1 summary、首轮遗留 32-byte WAL/32768-byte SHM；有效对照无 sidecar。父 Step 5 根现 110/45/46083286，旧 D0/index 盘点未变。缓存 ruff/mypy/Godot 为 6682/38199525/3079 bytes，继续保留；无新 venv/pytest cache。

**停止条件已触发：空间门禁失败。** 不执行 D2、连接修复、完整性能矩阵或后续 evaluator/三进程/故障组合；P1/Step 5 不完成，不进入 Step 6。下一步等待用户重新确认存储方案边界，不能直接批准产品迁移。资源按授权保留至 Step 5 收口，由用户手动删除；精确盘点、命令和风险见任务卡 D1 末节。

### 用户授权解决后的下一决策（仅调查，未实施）

已只读核对基线/八迁移/D1 metadata证据和仓储SQL。建议候选C：control保留B布局；仅原四observability叶表的固定枚举/policy转整数、execution UUID转16-byte BLOB、cost三HMAC tag转32-byte BLOB，DTO/CLI恢复原值；父trace_id FK和八表/十索引边界不扩大。精确字段、文件、兼容风险见任务卡“P1续修调查”。这需要用户明确放开原字段类型/CHECK物理表达和禁止编码限制，通用续修授权不用于暗中改schema。

获准后顺序仍为codec/约束红测→新synthetic空间预验证→通过后append-only0004→连接生命周期修复→完整warm-up+5-run→原Step5其余验证；失败或新增越界需求停止。候选资源compact-preflight-v1/migration-v4-tests/performance-v2本轮未创建，旧证据不连接/复用；不降低阈值、不减少事件、不进入Step6。完整目标尚未达成。

### 候选 C 已获明确批准，预验证执行中

2026-08-27 用户批准物理编码例外与条件式续修。正式/功能基线及八旧迁移哈希复核符合。新增 codec、实验 SQL 参数/结果适配器和专项测试；没有产品迁移或既有仓储改动。codec 缺模块红测成立，专项 57 + D1/D0/index 48 = 105 passed；定向 ruff/format/mypy 通过。一个新增 waiter 测试 fixture 初次漏设 inflight_shared，被既有 DTO 正确拒绝，已纠正测试而非放宽不变量。

固定三库 100 execution 对照运行中，不以测试通过推定空间通过。资源 compact-preflight-v1 于 2026-08-27 13:29:36 +08:00 创建，具体子路径/保留期限见任务卡台账。后续 migration-v4-tests/performance-v2 未创建；失败立即停止，P1/Step5 不关闭。
### C续修实际结果与停止点（最新）

C空间/语义预验证通过：232/420/652KiB，105项相关测试；获准条件满足后追加两份0004及codec仓储集成，随后有界writer连接修复，迁移/连接/控制132passed、测量8passed。八旧迁移及业务/API/Godot不变。

核心warm-up+5-run共18000正式样本，SQLite观测单项和三类拒绝通过；完整HTTP control-on p95/p99=787.5748/853.159ms，相对增量260.904ms（允许105.33416）；in-memory+control=5.0921/7.1039ms，五项失败，exit1后停止。空间中位652KiB不能替代这些门禁。

剩余矩阵（含实际长期记忆写入）、evaluator、三进程digest、故障组合和最终全量质量未运行。当前step_5_performance_gate_failed / awaiting_revised_performance_plan，Step6不进入。下一步只建议先分析现有metadata/源码形成有界性能方案，是否新增profiling/实现由用户再确认。正式五文档、功能32+40；Step5资源692files/124839407bytes，详见任务卡C续修终检，全部保留由用户手动回收。
# F-009 Step 5 V16 rolling projection 统一协议重验（2026-08-30）

状态：`completed_with_performance_gate_failure / stopped`。失败优先契约最终`18 passed`，ruff、format、2-source mypy与diff通过。V16语义、空间、稳定性和配对吞吐通过，但recorded p95=`3.2393ms > 2ms`，已按停止条件终止；不得实施产品`0005`或继续完整矩阵。下一步需单独决定是否调查no-recorder与recorded共同的基础控制链路成本，不得重跑V16寻找有利样本。

资源固定为 `E:\Agent\cyber-town-f009-step5-tests\performance-v16-budget-projection-unified` 及已登记子路径，保留至 Step 5 收口并由用户手动回收；Codex 不删除。
# F-009 Step 5 V17 rolling projection 阶段归因（2026-08-30）

状态：`completed / awaiting_v18_candidate_authorization`。缺少V17入口的红测成立，最终`21 passed`；ruff、format、2-source mypy与whitespace通过。唯一companion归属100%，定位共同控制链路成本而非recorder独有瓶颈。下一步建议只授权候选A的synthetic set-based projection delta预验证；未达到局部收益和统一plain绝对门禁即停止，不创建产品`0005`。

资源固定为`E:\Agent\cyber-town-f009-step5-tests\performance-v17-projection-stage-attribution`及已登记surface；保留至Step5收口并由用户手动回收，Codex不删除。


## 2026-09-05：Step 6 整改与受控恢复计划

1. 核对正式/功能 worktree、冻结98项与方法论同步差异；未知业务变更即停止。
2. 在已登记归档根完整备份当前五份项目管理文档并逐文件校验 SHA-256；随后按唯一职责压缩当前文档，把有效长规格集中到 F-009-验收契约.md，机器资源台账迁到单一索引。
3. 仅在两个 QA 文件中建立失败回归并最小修复 evidence 台账依赖和 canonical/sidecar 工具故障；机械修正与工具修复各最多两轮。
4. 在 recovery-20260905-01 内先做工具就绪/定向验证，成功后一次完整 native quality；仅全部语义门禁通过才使用保留的一次 warm-up+5-run 性能复验。
5. 正式验收失败、未知变更、产品/Schema/runner/阈值问题、资源越界或额度耗尽即停止；不进入 Step 7 或 Git 交付。

资源预登记：E:\Agent\comprehensive-cases\15-cyber-town\docs\archive\F-009-过程记录-20260905，F-009 Step 6 文档治理历史副本，可能包含 synthetic 路径、测试元数据和既有脱敏证据，不含已知真实秘密；保留至任务归档后人工复核，Codex 不删除。固定子路径为五份原文件名与 manifest.json。
