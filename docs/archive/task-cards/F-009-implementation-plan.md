# 已归档实施计划：F-009 安全、成本与性能优化

归档准备日期：2026-09-18

> 本文件保存归档提交前的完整实施计划。最终交付包括Step 6验收证据、Step 7归档包装修复、跨平台CI适配及PR #13绿色Quality门禁；归档随同一PR合并进入`main`时生效。

更新时间：2026-09-18

## 当前：Step 7 分支交付完成，等待 PR 授权

QA observer恢复、V1–V4、tool16/R7、最终quality10及同一冻结版本的固定gate-boundary matrix均已通过。Step 7将100个功能文件与19个正式文档按主题提交，并只推送到 `origin/feat/f-009-delivery`；远端核对完成。

只改三个QA文件：等待marker时不再反复做完整容量扫描，仍保留10秒、observer error和确认后的完整check；新增确定性慢check回归；活动根轮换到tool16/R7并归档tool15/R6。不得修改产品、超时、阈值、skip、安全边界、quality命令或业务服务。

固定性能复用 `scripts/f009_step5_benchmark.py` 的 `gate_boundary_matrix_manifest` 与 `_run_gate_boundary_matrix`，通过QA的 `space_performance_root_binding` 仅在作用域内绑定新鲜performance根并恢复原配置。协议为统一warm-up一次+5测量，8类场景及三SQLite诊断，失败不改阈值、不重跑。

完成检查点：quality10九阶段全部exit0，完整pytest 2,942 passed/133既有契约skip/0 failed；S3固定1+5全部阻断门禁通过。交付分支119路径、敏感扫描0、五个冻结哈希一致，远端ahead/behind=`0/0`；功能worktree专用 `AGENTS.md` 原样保留且未提交。下一项只等待PR授权，不自动创建PR、运行CI、合并、同步main或删除资源。

## 上轮：tool11完整工具就绪补齐已完成（不恢复quality）

两QA最小接入、完整静态与唯一136函数531参数已通过并停止；准备修正1/2、工具运行1/1，历史额度保留。冻结fc8ce66ac661f695f89a7511c7e254cedaa0fb404a9119c1fc36d18d1fe473a2稳定，其余98项既有变更未动。下一步仅只读审定完整fake-only语义验收条件与新额度，不自动运行。

完成范围：tool11独立台账/精确登记及tool10历史来源分离；原454+迁移84去重9+两凭据负例=531，136函数全参数；凭据统一原6+迁移4文件并核验两原迁移8阶段证据。新增阶段校验只在pytest正常返回时执行，失败报告及收口顺序保持；未修改产品/摘要helper/迁移测试或Win32、owner、observer、路径、等待规则。

完整静态：Ruff check/format --no-cache、原Python AST/5嵌入fixture/531参数来源、strict mypy四目标--no-incremental --cache-dir=nul/MYPYPATH=backend/src、两仓diff及100文件冻结均通过。初次静态全通过，源码复核后使用第1轮准备修正并完整复验通过；具体诊断、准确命令、指纹唯一见evidence。

唯一真实父observer+受保护子pytest运行531passed，原35闭环/UV17/Godot回放26/迁移及报告链/实际synthetic False和True全部有直接证据；observer5214事件完整、无边界违规、已安全收口。未追加真实负载，不运行FastAPI/Godot产品场景/connectivity/quality/性能。

资源：qa-tool-contract-11已完成、530文件4713256bytes<256MiB，38旧台账/旧681508413bytes资源及运行期四文档不变；恢复总686221669bytes<2GiB。全部新旧证据和临时资源保留，当前任务保留原操作前精确登记，机器过程只在独立台账。收尾结果、退出码及产物hash见evidence，不重复复制过程。

成功仅本版本与清单工具就绪，不等于产品验收或原connectivity/observer内部原因关闭。original_failure_resolved=true仅历史ownership/canonical，step6_complete=false，Step7未授权；本轮无后续自动动作。

## 上轮：observer失败证据闭环（保留）

已完成并停止：完整静态通过，唯一13函数35参数全部passed；真实父observer完成且无溢出/未知路径，冻结9341d9fd1a5ea71346ef439db696c5bd543aa8797f8cff9595cbf9e15aabd258前后不变。初次Ruff3项失败；修正1后静态全通过；就绪复核的报告容量前置缺口在修正2补齐并增加2负例，完整静态全通过。准备2/2、定向1/1耗尽；精确结果和资源见evidence。仅证明失败证据闭环，不证明原溢出原因已消除，不恢复quality。下一步仅审定溢出风险的最小处理与验证边界。

2026-09-10明确授权；基线629a5a56599ebbe64a6b06a313e544341f36fb92e8e41b6853e0165f226410ce、两仓Git/staged0/100与19变化、32旧台账/6841文件494822154bytes核对一致，无相关进程，批准新根尚不存在。仅两QA及正式四份当前文档；不改产品，不恢复quality，历史quality06 1/1耗尽保留。

最小设计：NativeWatcher仅补接收阶段/API/成功零字节/失败码/时间/已处理计数的有界标量记录，原64KiB、通知过滤、重新arm顺序、路径/owner/收口和等待规则不变。native_session复用现有drain/close，分别保留主失败、drain/close/报告失败；主失败优先且对象不替换，次级失败独立报告；只有无主失败才传播收口或写入失败。失败不调用成功inventory，输出completed=false/observation_complete=false/inventory_complete=false，unknown_paths=null；不伪造最终状态。失败报告写不出时，仅既有stderr输出固定限量证据不完整码并给原异常加固定备注，不绕守卫写其他文件。

run_observed只增加可选有界命令状态，记录已启动/被中断、所持Popen PID与可取得的缓存退出码和来源；不新增poll/Win32查询/终止/重试。quality摘要在会话收口后写入，先登记命令条目再启动；观察失败/收口失败整体exit1，原quality命令内容、顺序及门禁不改。本轮不加入pytest增量结果，中断的数量继续未知。

复用run_identity_validation接入唯一observer根与专用精简选择器，不生成tool/业务就绪凭据。验证：精确根/owner/台账/容量；零字节与API失败分类、受控接收循环；主失败+重复check/独立close/写入失败及单独输出失败；实际失败摘要schema与就绪拒绝；实际quality适配控制流仅注入局部synthetic命令，父observer不替换；真实受保护Python子进程中断、关闭/退出报告及共享状态恢复。原overflow硬失败及相关台账安全负例保留。静态两QA Ruff check/format --no-cache、AST/内嵌fixture与全部选择器参数计数、原strict mypy两目标/MYPYPATH=backend/src/--no-incremental/--cache-dir=nul、diff/空白/指纹。初次准备后最多两轮有依据的范围内修正与完整静态复验，历史额度不重置；运行前冻结准确节点/参数/配置。

仅一次--observer-failure-validation，真实父observer保护pytest和synthetic子进程；受控内层失败须由父断言精确核验，不能影响外层真实observer。外层任何意外失败/缺字段/观察缺口/漂移/越界即停止，不修复重跑、不补跑。新根及所有固定/派生资源创建前登记，≤32MiB、总≤2GiB；旧资源只读保留，机器记录仅新ledger，运行期四文档不变。细项登记见current-task。成功仅说明失败证据链通过，不证明overflow根因消除，不恢复quality/性能/Step7。

## 上轮quality06停止事实（保留）

本轮已执行原quality06一次并失败停止，不改代码、不重跑工具/静态或验收。前八项命令exit0；完整pytest期间step6_native_watch_overflow在run_observed的watcher.check抛出，native_session.close再次抛出，导致父native-summary及drain未生成；根pytest-summary也不存在。quality-summary exit1仅有八项完成命令。各pytest实际数量/关键节点结果未知，不以子fixture摘要或历史通过代填；后置repository policy无执行完成证据。

收尾已核验冻结不漂移、31旧台账/5569旧文件和运行期四文档不变，本批容量与恢复总量未超限，当前无相关进程/8000/8001监听。quality06 1/1耗尽，全部新旧产物保留；不补跑、不新增批次。唯一下一动作：只读审定本次observer overflow触发条件与失败收口报告缺口，先区分实际通知丢失和工具状态影响；不预设原因、不自动修复或扩大观察/缓冲/权限。tool08历史结论保留但不代替本次验收，性能和Step7仍未授权；详细数据及索引见evidence最新收尾。

本次只适配入口fixture消费契约并接入tool08：测试局部EntryAPI继承StartupAPIStub，按预设case复用真实StartupProcessAPI.wait的5000ms调用形状、仅替换该实例kernel；不改共享Stub/真实Win32/权限/等待/终止/owner。区分终止API返回5、stop最终错误、端口释放、最终退出报告；原25入口参数全部保留，launcher_error保留超时负例，both_error/observation_cleanup/observation_all/cleanup_reporting同步核验最终异常对象及独立阶段证据。新增6参数：launcher_delayed_exit、launcher_exited_before_wait、launcher_wait_failed、launcher_exit_code_unknown、observation_then_launcher_exit、business_error_then_launcher_exit。覆盖等待中/前退出、失败/未知码、观察与business错误优先级，原报告链/有限等待/实际FalseTrue不删。

仅两QA：脚本只改tool08根、将tool07加入历史、增加新函数及计数；quality06配置/运行逻辑不改。旧107函数412参数+新1函数6参数=108/418，实际FalseTrue最后。先完整静态Ruff check/format-check --no-cache、两QA与4内嵌fixture AST/全参数计数、原strict mypy两目标/MYPYPATH=backend/src/--no-incremental/--cache-dir=nul、tracked/untracked差异及空白，再源码复核冻结；唯一tool08使用真实父observer和原受保护pytest，运行失败即停，不修复重跑。初次适配及静态获批；仅恢复此前剩余1轮失败后准备修正，历史已用1/2不重置，不用于运行失败。

新鲜root=E:\Agent\cyber-town-f009-step6-qa\recovery-20260905-01\qa-tool-contract-08，≤256MiB、ledger≤8MiB、observer合计≤8MiB及既有更小产物限额/2GiB总额；创建前逐项预登记见current-task。新6case只写本批pytest/<冻结nodeid编号>/entry-report/<case>，沿原timeline/phase/position/evidence-status/脱敏stdout-stderr文件限额，不另开子批次、不启动FastAPI或Godot。结束核对30旧台账、5067旧资源元数据、代码/四文档运行期hash和进程。成功或失败均停止，quality06/性能/Step7不恢复。

设计：仅切换TOOL_CONTRACT_ROOT至qa-tool-contract-07、NATIVE_QUALITY_ROOT至native-quality-06；旧tool06/quality05台账加入明确历史，未来根不作为先决历史。复用固定台账、真实父observer、owner、环境/缓存和容量机制；根配置断言与当前运行根分离。原98函数358参数与119项去重合并，新增9函数54参数，目标107函数412参数，实际Python False/True最后。只适配精确根、历史来源与清单，不修改权限、进程等待/收口、产品或quality命令语义。

顺序：逐项预登记→接入→两QA Ruff check/format-check --no-cache、原解释器AST两QA/内嵌fixture和清单、strict mypy两目标/MYPYPATH=backend/src/--no-incremental/--cache-dir=nul、tracked/untracked差异及空白→源码复核冻结六文件/聚合/清单/资源/环境→tool07一次→凭据、真实observer完成、旧台账/证据不变及端口/指纹复核→quality06一次。运行失败立即停，不修复重跑；tool通过后实现再变也停。初次准备及失败后修正分别计数，后者最多2轮，不适用于运行失败。

完整验收映射：复用quality原9命令及前后repository policy：lock、ruff、mypy、schema、Godot import/unit、connectivity、dialogue-connectivity、完整backend pytest。pytest包含test_long_term_dialogue_integration.py::test_godot_scene_fastapi_sqlite_and_fake_provider_form_a_real_local_loopback；test_control_evaluation_step5.py::test_baseline_report_meets_all_step5_control_thresholds（25case）与test_same_fixture_and_key_match_in_three_fresh_python_processes；安全/预算成本/重试熔断/SQLite-WAL-FULL/空间/对抗节点按原完整收集执行，不另外重复这些项目。逐项核验实际结果与skip依据，历史probe不替代本版就绪。原受保护quality缓存策略不变，不执行性能、独立启动诊断或Step7。

资源：仅恢复根下qa-tool-contract-07≤256MiB、native-quality-06≤1GiB，各machine-ledger.md≤8MiB；固定摘要/observer/缓存/Godot隔离副本/SQLite及fixture子资源沿现有分类、较小限额和操作前登记，详细预登记见current-task。两批满额后恢复总1698435887bytes，≤2GiB。全部保留、不覆盖删除；收尾对比29旧台账、4885旧文件元数据、四文档运行期hash、代码、容量和进程，机器过程只进独立台账。

当前恢复授权：2026-09-10用户仅批准fixture单处E501等义拆行及一次完整静态；历史准备2/2保留，本次单独计一次恢复。基线9e33e66000998b1b6e636e869924bb212663be65d6c12f6d2a5e00eae9e16778核对一致。脚本不改；两QA静态/4fixture AST与原LF指纹、22函数119参数、两仓差异全部通过后，才执行原02唯一--launcher-exit-contract-validation。已有精确预登记继续有效，根不存在、父链安全，无并发进程；不新增运行批次，运行失败停止不修复。收尾核对28旧台账/4817文件355844493bytes、代码及四文档运行期hash，详细机器记录仅新台账。

2026-09-10用户批准审定范围；基线3f7cf34b7eda3a70c8cfeb7357039a000e3ff0a58ead0a23e90d8b32a05c2d31。仅两QA：测试的有限等待/状态模型与报告断言、02根/台账/精确计数；不改StartupProcess.stop、Win32、权限、owner、observer、等待或报告器识别。原14参数保持，新增3种失败×import/runpy以独立6参数函数复用同一fixture/父校验，原113+6=119，避免改动其他既有工具清单计数。

fixture区分：成功等待后核验原句柄最终整数码、自然码未知、原API错误5保留，再显式构造并注入报告测试异常；不称stop自然抛错。状态/等待超时/等待失败/退出码未知由真实stop控制流产生精确RuntimeError，验证类型/args、等待次数/关闭次数，再分别登记终止事件及固定合成结果标记。父回归核验nodeid/阶段/精确标记/错误/退出结果/字段隔离；原cleanup优先级、forged/invalid及脱敏保留。未知异常不得被受控负例掩盖。

计数：历史准备1/2不重置，本轮关联修正使用剩余第2轮；完整静态后仍失败则停止，02定向最多1次且失败不修复重跑。流程：登记→上述适配→两QA Ruff check/format --no-cache、AST两源码与4fixture/清单计数、原strict mypy/MYPYPATH=backend/src/--no-incremental/--cache-dir=nul、tracked/untracked差异/空白/指纹→源码复核冻结→原--launcher-exit-contract-validation仅绑定02→审计收口。固定顺序原安全/根/报告，新增报告6项，再原实际synthetic False/True；全部通过也不形成业务就绪凭据。

唯一新根launcher-exit-contract-validation-02≤32MiB；路径类别与分项限额见任务卡，创建前复核新鲜度/父链/进程，旧01不重用。机器过程仅独立台账；运行前后核验两仓/代码/四文档/28旧台账与4817资源355844493bytes。FastAPI/Godot/connectivity/quality/性能/Step7均零额度。普通格式或报告适配不是新增进程框架；超范围立即停止。

本轮停止：已保存关联适配，第2轮Ruff check exit1，仅fixture内2943行E501；format/mypy/diff exit0，AST两QA/4fixture与22函数119参数断言完成，但末尾辅助还原指纹因误用CRLF而exit1；按实际LF只读对照已还原基线script hash，未执行额外静态复验。准备累计2/2耗尽，02未创建、运行0/1。保存点9e33e66000998b1b6e636e869924bb212663be65d6c12f6d2a5e00eae9e16778，等待仅等义换行及静态恢复授权；无运行后修复或业务启动。

## 历史：launcher有限退出等待契约与01定向验证

用户已确认选择实施而非继续暂停。基线3f2c5f0d0a6e3b8c37016b15a6dce06db892ae9e6149619905953160ff637ce7，两仓Git/27台账/4787文件355691113bytes无漂移。仅两QA与四当前文档；复用run_identity_validation及既有报告/句柄/owner/ledger，不新增探针或通用框架。

修正：成功绑定的launcher在TerminateProcess返回5且即时原句柄未signaled时，不立即判最终收口失败，进入原一次5000ms等待与post_wait查询；不重试终止或重新OpenProcess，不增加权限，不改变business的终止控制流及Popen后备通路。超时/无效句柄继续原异常传播，终止诊断独立保留；该launcher路径缺少最终退出码时明确失败。终止尝试失败后仅记录真实final码，natural_exit_code/available保持未知；已有直接类型/替身/归因断言同步，不以码5直接放行。

验证：新根/owner/ledger/预登记/容量；延迟signaled、已退出、持续存活、等待/状态失败、未知退出码、非5及business/unknown角色原拒绝、错误身份/初始绑定、一次终止/一次原等待/关闭次数；原Popen四路报告、正常import/runpy报告链及schema限额；实际synthetic[False]/[True]最后各一次。先静态AST固定全部选择器和参数数量，不运行收集；然后唯一受保护定向批次。该结果不作为业务启动或完整工具就绪凭据。

流程：精确登记→实现→两QA Ruff check/format --no-cache、AST不导入、原strict mypy/MYPYPATH=backend/src/--no-incremental/--cache-dir=nul、tracked/untracked diff/空白/指纹→冻结→一次--launcher-exit-contract-validation→收口。准备普通问题按现行规则最多2轮有依据修正及完整静态复验，本次单独计账，历史不重置；定向1次，运行失败即停，不修复补跑。无业务/FastAPI/Godot/connectivity/quality/性能/Step7。

唯一新根launcher-exit-contract-validation-01≤32MiB、ledger≤8MiB、observer合计≤8MiB、必要fixture/子报告合计≤8MiB、invocation≤64KiB、pytest摘要/termination事件各≤1MiB，恢复≤2GiB；具体路径/类别见任务卡。运行前后核验冻结、四文档hash、旧27台账和4787文件、资源与进程；全部旧结果保留。成功仅表示退出等待契约验证，错误5内部原因和原connectivity因果不自动关闭。

静态与源码就绪已通过，准备修正1/2；AST冻结21函数113参数，runner逐函数参数计数及报告拒绝表一并核验。新聚合3f7cf34b7eda3a70c8cfeb7357039a000e3ff0a58ead0a23e90d8b32a05c2d31，仅两QA变化。精确命令为原解释器 -B scripts/f009_step6_qa.py --launcher-exit-contract-validation，定向0/1；运行前再次确认新根不存在且父链无reparse，旧台账/资源未变。

本轮已停止：唯一运行97passed/1failed，后15项未执行；新12契约和身份真实报告10项通过，终止真实报告首项call-import在旧fixture unexpected_wait失败。它尚未登记termination_observations，父3027行发现缺字段；本轮关联fixture适配遗漏，不解释为预期负例。实际False/True未执行。准备1/2、运行1/1耗尽，无运行后修复；下一步仅审定fixture适配与新额度，详见evidence当前结果。

## 历史：显式摘要限额修正与唯一tool06（已耗尽）

用户批准两QA的限定修正和一个新工具验证额度。基线eb4ab0ac6a4e35dc9057cdc634f97a8ff06078714f96ae35c87637b049716b6f；旧tool05/quality05均1/1耗尽。此次仅修termination超限负例显式1MiB并核验未创建文件；分离路径隐式限额计算与当前合法运行路径；正式pytest摘要显式1MiB，工具contract摘要写入前1MiB，两者采用确定LF以使UTF-8限额等于落盘字节。保持身份根隐式上限、字段白名单/错误码/排他创建与路径守卫，不给任意fixture统一套1MiB，不改observer、权限、owner或进程语义。

工具根仅接入qa-tool-contract-06（旧tool05加入固定只读历史），quality根不接入新编号、额度为零。保留原92函数330参数，补termination7和identity限额1，新增根/显式限额9、两摘要字节边界6、正常导入/runpy真实pytest超限/正常通路4、实际调用与就绪拒绝1，计划98函数358参数；静态AST核验清单/计数及4个fixture源码，运行摘要确认实际全部参数。真实子pytest的受控超限退出1由父断言验证错误码/无摘要，不将其他错误视为预期；原报告、canonical、退出观察、False/True及owner/ledger覆盖保留。

顺序：登记→实施→两QA Ruff check/format --no-cache、AST不导入、原strict mypy/MYPYPATH=backend/src/--no-incremental/--cache-dir=nul、tracked/untracked diff/空白/指纹→源码复核冻结→唯一--tool-contract→收口。准备普通问题最多2轮有依据修正和完整静态复验，运行仅1次且失败即停不重跑；所有历史额度保留。机器证据仅新ledger/固定摘要；准确命令和静态诊断记录evidence。运行前后核验四文档、旧26台账、旧4357文件、代码、容量、observer及进程，全部证据保留。

资源与类别详见任务卡本轮预登记；新工具根256MiB、ledger8MiB、固定pytest/contract各1MiB、observer合计8MiB、恢复总2GiB。本轮FastAPI/Godot场景/connectivity/quality/性能/Step7均零额度。通过也仅证明本轮工具修复，不恢复旧语义验收。共同原因是历史根隐式约束被带入通用测试且工具清单未覆盖；以显式限额与消费方矩阵防止再用完整quality寻找工具遗漏。

本轮收尾：完整静态第1轮复验通过（准备1/2）；tool06唯一运行356passed/1failed，新增及补入28项全过，原实际[False] launcher错误5失败而[True]未执行。冻结未漂移；tool06额度1/1耗尽，禁止使用剩余准备额度修复本次运行失败后重跑。范围内摘要缺陷有直接通过证据，但整个工具就绪失败；现仅等待审定launcher已有取证的最小处理方案，不能恢复业务/quality。详细结果、各PID状态、资源与文档hash见evidence。

## 上轮tool05/quality05接入与结果（原证据保留）

用户已确认独占窗口：从验收启动到收口，其他项目不启动/自动重启8000/8001服务或并发操作F009。本轮只改两QA：当前根切换tool05/quality05，已完成tool04与失败quality04以固定路径加入必需历史；关联测试在既有函数中核验精确根/限额、历史只读及禁止旧根活动。没有产品/权限/owner/路径/observer/进程或端口逻辑改动，不新增探针框架。旧失败原因不改写。

顺序：基线/旧资源核对→最小配置及关联断言→完整静态→冻结→一次tool05全部通过→再次核对冻结/凭据/新鲜根/8000与8001→一次quality05→收口。准备初次+最多2轮范围内修正及完整静态；工具和quality各1次，任一运行失败不修复重跑，不迁移旧额度。两QA Ruff check/format-check --no-cache、AST源码及原fixture、strict mypy原目标/MYPYPATH=backend/src/--no-incremental/--cache-dir=nul、两仓diff/空白及指纹；不安装依赖。

复用E:\Agent\comprehensive-cases\15-cyber-town\.venv\Scripts\python.exe，cwd=E:\Agent\comprehensive-cases\15-cyber-town-f009。先-B scripts/f009_step6_qa.py --tool-contract（当前精确tool05），保持原92函数330参数，关联断言直接增强原测试不缩减覆盖；静态展开与计数表核对，实际数量以唯一摘要为准。全部通过后-B scripts/f009_step6_qa.py --quality recovery-20260905-01/native-quality-05；保留完整quality原缓存策略，不机械套用静态nul。真实父observer/owner/固定ledger/隔离子进程全程有效。

固定清单：既有quality.py顺序lock、ruff、mypy、schema、godot-import、godot-unit、connectivity、dialogue-connectivity、完整backend/tests（受保护pytest子进程）。完整pytest已含test_long_term_dialogue_integration.py::test_godot_scene_fastapi_sqlite_and_fake_provider_form_a_real_local_loopback，test_control_evaluation_step5.py::test_baseline_report_meets_all_step5_control_thresholds及test_same_fixture_and_key_match_in_three_fresh_python_processes；不额外重复精确回环、25-case evaluator或3进程digest。安全/预算/成本/重试熔断/SQLite与空间/对抗及原ownership回归同在完整集合；核验各项实际节点/参数结果及所有skip的契约依据，不凭名称/总数推定通过。

资源：恢复根下qa-tool-contract-05≤256MiB，native-quality-05≤1GiB，ledger各≤8MiB，合计新增≤1.25GiB、恢复≤2GiB。创建前在任务卡逐根/ledger预登记，固定子资源和动态类别沿原守卫操作前逐项登记，旧24台账/3338文件只读保留。没有占位绑定或关停其他项目；端口再次被占、安全违规、观察缺口、未知漂移或超限即停止。quality05未满足全部前置时不得创建。

收尾：准确命令/退出码、参数执行数及未执行项、observer完成/边界/owner、运行前后代码冻结及旧24台账/3338文件、四当前文档运行期hash、资源容量/进程/端口。机器只进各自ledger/摘要，人工过程只集中evidence。通过的就绪不能替代产品验收；connectivity成功不证明旧超时因果已确定。

执行收尾：tool05=1/1，92函数330参数全部通过；quality05=1/1，lock至dialogue-connectivity前八命令通过，完整pytest1364passed/133skipped/1failed，在test_termination_schema_and_limits[oversize]停止。该节点不在tool05清单；精确Godot与剩余节点没有本轮执行记录，不补跑。evaluator/3进程digest/ownership节点已有当前quality直接通过证据。代码冻结不变，准备修正0/2，两observer收尾完整，旧24台账/资源及四文档运行期保持，端口释放且无本批残留。下一步只审定超限负例的适用根/显式限额契约及关联工具覆盖，不能继续用完整quality逐个找QA遗漏。不授权修复/新运行；step6_complete=false，性能/Step7未授权。

## 历史：受控启动入口报告接入（唯一就绪失败，已停止）

本轮仅两QA及四当前文档；起点1aa2235c04155e593d10bdc909e03388ff7d04ae238d40087235698b55638511。候选补各原调用处有界错误/归属/状态报告及异常输出整理；双角色终止受控负例通过，但观察失败的原异常贯通未通过，不能声称接入已就绪。未增加查询、终止、重试或放宽关闭/等待安全条件；代码已冻结保留，不现场修复。

修改点：新startup-report-integration-readiness-01根、owner/台账/容量/父子上下文；凭据绑定六文件冻结和精确清单、两类拒绝记录为空；诊断入口接入终止报告和异常输出整理；直接测试实际入口控制流（精确业务/fixture替身，外层真实observer和守卫仍有效）、原真实报告通路、两个实际synthetic分支及相关阶段/前置/退出契约。产品文件保持原字节，不增加探针/SDK调整。

计划顺序保留：完整静态/源码复核→独立就绪→凭据只读→五前置→一次启动→收口。本次已停在独立就绪，后续均未执行。初次静态失败后第1轮全过；第2轮修正模拟端口/读取线程时序假设及补报告断言，完整静态再次全过，准备2/2。固定29函数/30选择器/159实例，AST计数核对；冻结42887026e94b6cc7a233b37c6e8a9b83399e5a2bf1b37da675cf8639d0d3a24d。就绪1/1耗尽、五前置/FastAPI/health0/1未使用，不迁移；历史额度照实保留。

就绪运行最终27passed/1failed，28项实际执行，余131项未执行（含reader_error、真实报告子pytest及实际False/True）；失败后-x停止，不补跑。准备2/2、就绪1/1；五前置/FastAPI/health0/1且禁止条件推进。新就绪80文件245501 bytes，旧1963文件/16台账及运行期四文档不变；恢复236350366 bytes，diagnostic05未创建，无相关残留。时间线显示原观察异常后已收口/保全部分输出，却继续正常验证且重复port_released；源码支持business未绑定的阶段检查可能覆盖原异常。摘要无异常全文，不伪造实际错误消息；详细证据与最小建议只归evidence。step6_complete=false，后续待审定、不自启。

## 上轮已完成：launcher终止失败报告补齐

本轮仅两QA及四当前文档。原terminate即时ctypes错误码不变；新增明确来源的OSError子类保留errno及原拒绝条件，stop记录原调用处的标量/时间/状态复查结果，未增加API调用。复查失败原样传播、已采集码保留；原测试finally记录绑定对象观察并薄适配原Popen收口，原调用和关闭顺序保持，主失败/收口失败分开留证，未知码或是否完成终止不补造。

报告消费方MetadataReporter/write_pytest_summary/原实际测试/独立termination-events均接入。只接受封闭字段、类型、大小及来源核验；按nodeid/phase隔离，保留身份/canonical与正常导入/runpy通路。不增加框架、权限、重试，不改owner/路径/observer/等待/终止或退出后检查。

初次静态1处E501和2处类型收窄错误，第1轮修正完整静态通过，第2轮补5项cleanup负例后完整静态通过，准备2/2。唯一固定集合18函数/19选择器/74实际参数实例全部通过：A根/台账与终止/退出/身份/别名/schema，B原10+新增14个真实报告子pytest，C原实际False/True各一次。受控子pytest失败均经父断言核验，非外层忽略错误。runner exit0、父observer完成、边界0；定向1/1已用，停止，不自动继续任何阶段。

False business72852/launcher26072各自retained_query_handle final1/natural=null、主动终止成功；True business9748/launcher28876各自final7/natural7。两分支后备Popen报告确认已退出、未再次终止，含动作范围不覆盖前面主终止证据。系统终止失败本次未复现，受控码5只证明报告字段和异常/收口通路，历史原因仍未知。

资源按current-task根/ledger预登记→bootstrap固定绑定→各子路径guard先登记后创建→真实父observer/受保护pytest→收口库存。新根launcher-termination-report-validation-01为32MiB，实际56文件258892 bytes，台账95463 bytes，其他产物限额通过；恢复236104865 bytes<2GiB。旧1907文件235845973 bytes及15台账不变，全保留不删除。无相关残留或8000/8001监听，diagnostic05未创建。

冻结1aa2235c04155e593d10bdc909e03388ff7d04ae238d40087235698b55638511运行前后不变；仅两QA变化，其余98项未变，两仓原分支/HEAD/staged0及100/19保持。四当前文档运行期哈希不变，机器过程仅独立台账；准确命令/诊断/结果及哈希归evidence，当前计划不复制长过程。

上述为历史74项结论，非本轮启动许可。当前original_failure_resolved=true仅历史ownership/canonical，原connectivity/终止内因仍未知；step6_complete=false、Step7未授权。本轮新就绪失败，下一动作限审定异常收口控制流的最小修正与新复验，不自动恢复业务。

## 上轮已完成：退出后进程观察契约

2026-09-08 用户明确解除工具修复暂停，新授权最多两轮“针对性修复—完整静态—定向复验”，现已用2/2并收口；历史準备2/2、observation-validation-01定向1/1及更早额度不清零。接续时2bb5f5744af80e1223418310874c3d803141b8a34b0480fc51a02294501b6aa6一致，两仓原分支/HEAD/staged0、99/19变化，旧1384文件/233227881 bytes，六旧台账只读基线无漂移；两个exit-validation根创建前均新鲜无相关进程。上次独立证据见evidence及旧根，不重复复现旧版本。本次最终状态见下方执行结果。

最小设计（仅两QA文件及当前文档）：

| 阶段 | 必需证据与行为 | 不可削弱条件 |
| --- | --- | --- |
| 首次绑定 | 原查询句柄完整PID/创建时间/映像，OS父子归属核验 | 退出不能跳过首次绑定；失败关闭且不获得可信身份 |
| 已绑定且运行中 | 原保留句柄先读状态，存活仍完整身份比较，再读最新状态 | 不吞存活阶段查询失败，不捕获31放行；查询期间退出的竞态仍按实际错误拒绝 |
| 主动终止前 | 新终止句柄完整身份对比，原查询句柄强制完整复核并观察状态 | 不提高权限、不改变5秒等待；身份不符不终止，原句柄不释放/按PID重认领 |
| 已确认退出 | 原保留句柄wait/state确定退出，同句柄GetExitCodeProcess | 不要求退出后的映像重查；历史绑定、实际退出与最终码分开标明；无效句柄报错、码未知保留None |

复用StartupProcess/API.state/wait，不新增进程框架或依赖；check调整阶段职责，stop同时覆盖入口、pre_terminate、post_wait及自然退出/别名收口。原API/权限/owner/路径/台账/observer不变，新增批次仅精确接入既有运行器。修复假设是“退出状态读取被不必要的映像重查阻塞”；不是解释错误31的OS内部成因，更不是原connectivity归因。微软进程终止/GetExitCodeProcess文档支持保留句柄观察退出；通过实际两分支验证具体效果。

验证：保留原A/B全部安全覆盖和10个真实子pytest报告组合；扩展退出后映像不可查、初始已退出不能免核验、存活失败/终止前身份变化、无效句柄/未知退出码、别名关闭次数与前置状态到退出的转换；最后原C False/True，各将本进程退出证据写入摘要。固定清单在静态通过后冻结。两份Ruff check/format --check --no-cache、AST（含报告fixture）、mypy --no-incremental --cache-dir=nul/MYPYPATH=backend/src、diff/空白/全部99路径指纹。每轮失败保留原因和产物，只在有依据且无安全违规时使用剩余轮次；不能无改动重跑。

资源：恢复根下startup-process-exit-validation-01/02，各32MiB、合计64MiB；仅第一批启用前精确登记，第二批需第一批失败及范围内修复后才登记/创建。沿用独立ledger8MiB、身份事件1MiB、pytest摘要1MiB、invocation64KiB、observer合计8MiB、必要临时子资源合计8MiB及总2GiB。复用report-regression封闭路径集合、既有初始化/逐项预登记，不复制Godot。准确根与子资源类别见current-task。运行期当前文档不写入，收尾核对六旧台账与旧资源、代码、容量、无进程残留。

复杂度复盘：此前把“可信身份建立/运行中保护”与“已退出对象状态读取”混为同一check，替身默认退出后映像查询始终成功，实际运行才暴露契约遗漏。本轮用阶段分离和真实两分支证据收口，不继续叠API错误例外；超范围架构/权限变化即停。FastAPI/Godot/connectivity/quality/性能均零额度；成功只表述工具缺陷修复，original_failure_resolved=true、step6_complete=false、Step7未授权。

本轮执行状态：两轮已结束，修复2/2、定向2/2。第1轮静态通过、90passed/1failed，失败批完整保留；第2轮完整静态及98项全部通过，原False/True两分支有独立退出码，真实报告链路通过，observer完成且无边界违规/残留。冻结7d18b739e246a7b576af6b7dea98bcbd248e160971eac56c9de27d3e3948f049运行前后不变。终止失败后已退出/仍存活分流有受控直接证据，本次实际未再次触发该窗口，不倒推第1批未知原因。最终结果和资源链接只见evidence/progress；本轮工具修复验证完成，下一阶段须另行授权。

## 上轮：最小身份取证增强与唯一固定定向验证（未运行保存点）

2026-09-07 用户明确授权；接续聚合 457bd148bd30bdc723f26a70d5f4f38da31b1ce9a9abe46ca9953d28de9e78e2 已核对，两仓原分支/HEAD/staged 0、99/19 项变化一致，无相关运行进程。只读诊断已完成：3293 合并三个 API 失败且多阶段可达，现有摘要不足以定位；退出后查询失败仅为候选，不改身份/权限/终止/等待规则。

1. 仅 scripts/f009_step6_qa.py、backend/tests/test_f009_step6_qa.py：拆开三 API 短路判断，同线程立即保存 ctypes.get_last_error；附加白名单、严格类型和有界的阶段/角色/句柄/PID/已知身份摘要/最近存活时间/主动收口元数据。保留 canonical 报告与全部原安全判断。
2. 贯通异常、MetadataReporter 和最终 pytest JSON；验证实际序列 A（三 API、错误码覆盖、退出后查询、别名/关闭、归属/身份变化）→ B（报告链路、脱敏、限量、字段保留）→ C（原实际 Python 子进程 False、True 各一次）。C 不是 FastAPI；最终节点清单在静态冻结处记录。
3. 本轮准备修正/静态最多两轮；原解释器，两文件 Ruff check/format-check --no-cache、AST、不变目标 mypy --no-incremental --cache-dir=nul（MYPYPATH=backend/src）、tracked/untracked/空白/聚合检查。源码复核通过后冻结，运行期间不改代码。
4. 唯一新根 recovery-20260905-01/startup-process-observation-validation-01，32 MiB；ledger 8 MiB、身份事件 1 MiB、pytest 摘要 1 MiB、调用元数据 64 KiB、observer 合计 8 MiB、必要临时资源合计 8 MiB。新根与台账创建前在 current-task 精确预登记，子资源逐项登记后操作；新根不复制 Godot 产品，不运行服务。恢复总上限 2 GiB，旧 1,332 文件/233,048,724 bytes 只读保留。
5. 复用真实父 native observer、受保护 pytest 子进程、owner、路径及固定独立台账。仅一次定向，任何意外失败/报告缺字段/观察或容量违规立即停止；不修复重跑、不迁移诊断 02 未用额度。失败保留 API/阶段/错误码后分析，成功仅本次未复现。
6. FastAPI/Godot/connectivity/quality/性能均不执行。机器过程只写新台账，当前文档运行期不变；结束核对代码、旧证据、容量、进程收口，人工摘要就地更新。original_failure_resolved=true 独立保留，step6_complete=false，Step 7 未授权。

静态通过保存点（不是运行就绪冻结）：准备/静态 2/2，第 1 轮 Ruff 四处 RUF043，第 2 轮 raw 字符串等义修正后完整静态全清；聚合 bcdb84fb6e2ff30bf16cc6e74964369237a4e1674b553f7f084ec4a8b759929a。IDENTITY_TESTS 候选 9 函数/52 参数实例，A17→B33→C2，未执行。

最终源码复核停止：__main__ runner 与 scripts.f009_step6_qa 导入模块的 StartupIdentityError 不是同一类；新增严格类型判断会漏收真实 pytest 异常。同模块 B 组不足以证明受保护实际入口的报告链路。已用完准备 2/2，因此不再修改代码/复验，不创建新根或运行定向（0/1）。本轮前述“源码复核通过/运行前冻结”仅为阶段性判断，现明确撤回；必要最小下一授权见 evidence 收口。根/台账预登记保留未创建状态。

## 上轮：最小进程观察与定向启动诊断 02（历史保留）

本轮已按失败条件收口：仅 states 类型声明变化，完整静态通过，运行前后冻结 457bd148bd30bdc723f26a70d5f4f38da31b1ce9a9abe46ca9953d28de9e78e2 不变。唯一 synthetic 执行 43 项，42 passed/1 failed，清单剩余 1 未执行；失败定位脚本 3293 的身份查询不可用分支，未进入五前置/真实启动。机械 1/2、synthetic 1/1、前置及真实启动各 0/1；以下执行清单保留为对照，不授权复用失败根。

1. 仅两份 QA 文件：保留诊断 01 为历史只读，接入 connectivity-startup-diagnostic-02（128 MiB）及独立 machine-ledger.md（8 MiB）。初始化与复制资源复用既有逐项登记、Godot 隔离副本和真实父 observer；旧根/台账不得追加。
2. 日志自报 PID 仅作候选。以 Win32 只读观察句柄核验 PID、创建时间、可执行文件，单次候选父关系快照核对本次 Popen 链；保留句柄防 PID 复用。分别记录启动/业务进程存活、自然退出（运行时为 null）、诊断主动收口和最终退出；归属未确认不得终止，未知退出码不得借用。
3. 保留双管道排空/限量白名单脱敏/已加载模块观察。直接 synthetic 清单保留原 9 函数，补 PID 不同、提前退出/存活、归属错误、身份改变、主动收口与退出码不可得，以及新根配置、前置顺序/断言的直接回归；配置检查不依赖目录存在，不假定当前运行根必为诊断根。
4. 完整静态已通过：两文件 Ruff check / format-check --no-cache、原解释器 AST（不导入 QA）、mypy 原两个目标 --no-incremental --cache-dir=nul，cwd 功能目录、MYPYPATH=backend/src 后恢复；tracked/untracked diff、空白与全部既有指纹核对通过。源码复核保留诊断配置/当前运行根分离、独立实例和句柄/owner/路径边界；机械仍 1/2。冻结 457bd148bd30bdc723f26a70d5f4f38da31b1ce9a9abe46ca9953d28de9e78e2，STARTUP_TESTS 原 13 函数/44 参数实例不缩减。
5. 静态全部通过后冻结代码、配置、测试清单、工具环境。新根创建前精确预登记并复核新鲜度/端口/进程/容量。唯一入口内先一次 synthetic；失败/观察缺口/漂移即停，不修复重跑。
6. synthetic 通过后复用 connectivity 的原函数和原断言，按 stopped_service、unavailable、duplicate_rejected、non_string_rejected、redirect_rejected 顺序各一次并完成 fixture 收口；任一失败即停。前置通过才启动一次原解释器 python -m cyber_town.api，原 QA 包装/fake-only/127.0.0.1:8000/五秒等待/一次原 health；随后立即按已核验归属收口。
7. 不执行原六项工程门禁、connected/recovery Godot、完整 connectivity/quality/性能/Step 7；新缓存、前置时序与新增观察仍非原 quality 等价。新批上限 128 MiB，恢复总额 2 GiB，各固定产物沿用前批限额；所有证据保留，不覆盖或删除。
8. 收口：原 --startup-diagnostic 入口仅执行一次；pytest exit 1、外层诊断 exit 1。observer 23 events，无 overflow/unknown_paths/reparse，已写 drain/final inventory，整体 completed=false。根 38 文件/152,976 bytes，恢复 1,332 文件/233,048,724 bytes，旧台账/元数据和代码未变；正式 evidence 运行期 38,821 bytes/哈希不变。无相关进程/监听，全部证据保留。下一动作仅提议只读定位三个 Win32 身份查询分支和错误证据缺口，不新增尝试；original_failure_resolved=true 保留，step6_complete=false。

## 上轮：新批次接入与条件完整验收（历史保留）

执行收口：接入与完整静态通过，qa-tool-contract-02 为 70 函数 / 201 passed；native-quality-03 在 connectivity 的 runner_port_open_timeout 处失败即停。尚未进入 dialogue-connectivity/完整 pytest/精确 Godot/evaluator/digest，原故障关闭结论保持。详细结果只见 evidence，以下清单不授权恢复或补跑。

1. 接续核对 ccd611706d26020040ad7a0a1c82c20a546abcb11c18ecc08a51e0305cdf42db；两仓 HEAD=1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3，staged 0，功能 99 项；无相关进程。历史 qa-tool-contract-01 的 181 passed 不重跑，不作为修改后就绪证据。
2. 仅两份 QA 文件：明确 qa-tool-contract-02/native-quality-03 精确根及限额；进程内一次绑定台账，子进程继承同一台账（撤销 native 权限不等于改换台账）；bootstrap 精确预登记，旧台账拒绝写入，observer 固定身份/游标，容量检查覆盖两个新根。补充接入回归，原 63 函数及参数不删减。
3. 完整静态已通过：两文件 Ruff check/format-check --no-cache、原解释器 AST（不导入 QA）、原两目标 mypy --no-incremental --cache-dir=nul（MYPYPATH=backend/src）、tracked/untracked diff/空白/原聚合指纹。新机械已用 1/2；新增 7 函数/20 实例，原 63 函数/181 实例不删减，预计共 70 函数/201 实例，以实际结果为准。
4. 静态全部通过后冻结两文件、清单、资源配置及工具环境；运行一次 qa-tool-contract-02。真实父 observer；验证根/owner、父子台账一致、旧台账未变、bootstrap 和两批容量边界。运行失败即停，不修复重跑。
5. 仅接入回归全部通过且指纹不变，运行一次 native-quality-03 的现有 --quality 入口。历史探针仅为原工具事实；当前回归报告及冻结代码须一致。运行中不改实现或配置，任何失败即停，不启动性能。
6. 简洁更新当前状态；详细结果仅 evidence 索引与独立机器报告。运行期间正式 evidence 不变；前后核验代码/旧台账/资源/observer。step6_complete=false，Step 7 未授权。

## 固定完整验收映射

下表来自源码静态核对；通过与否只看本批次实际结果，不凭名称或历史结果推断。既有入口能覆盖全部本轮语义要求，无需补跑独立 evaluator/Godot 或改产品 runner。

| 契约 | 现有命令/节点 | 执行位置 |
| --- | --- | --- |
| 工程 quality | cyber_town.quality.quality_commands：uv lock --check；python -m ruff check backend/src backend/tests scripts；python -m mypy 同三目录；python -m cyber_town.contracts.export --check | --quality；保持原命令语义及受保护缓存策略 |
| Godot import/unit | Godot --headless --editor --path game --quit；Godot --headless --path game --script res://tests/run_tests.gd | quality 原清单，路径由现有 native adapter 隔离 |
| connectivity/dialogue | python scripts/connectivity_integration.py --godot <既有Godot>；python scripts/dialogue_integration.py --godot <既有Godot> | quality 原清单，各一次 |
| 完整 backend pytest | 原 pytest 命令由既有 QA 子进程适配为 --batch <本批>/pytest --output <本批>/pytest-summary.json backend/tests；不缩减收集范围 | quality 的 pytest 阶段 |
| 精确 Godot 本地回环 | backend/tests/test_long_term_dialogue_integration.py::test_godot_scene_fastapi_sqlite_and_fake_provider_form_a_real_local_loopback | 已在完整 pytest；独立 fake SQLite/FakeProvider/fixture server，调用既有 Godot 脚本，非 F-005 真实资源 |
| 25-case evaluator | backend/tests/test_control_evaluation_step5.py::test_baseline_report_meets_all_step5_control_thresholds；test_fixture_is_strict_versioned_and_covers_all_step5_dimensions | 已在完整 pytest |
| 三个全新进程 digest | 同文件 ::test_same_fixture_and_key_match_in_three_fresh_python_processes，源码明确 subprocess.run 三次并比较三份 report/digest | 已在完整 pytest；不再额外执行三次 |
| 安全/预算/成本/重试 | test_safety_control_step2.py、test_dialogue_control_step2.py、test_budget_control_step3.py、test_budget_projection_preflight_step5.py、test_attribution_step5.py、test_retry_breaker_step4.py | 完整 pytest 全文件 |
| SQLite/空间/对抗 | test_sqlite_control.py、test_sqlite_connection_lifecycle.py、test_async_sqlite.py、test_control_space_preflight_step5.py、test_compact_storage_step5.py、test_multi_npc_adversarial.py 等 | 完整 pytest，不用工具自测代替 |
| 原 ownership/canonical | test_architecture_probe_step5.py::test_v23_waiter_conflict_and_concurrent_prepare_have_one_owner；QA sidecar 两态及登记反例 | 接入回归与完整 pytest 分别保留结果 |

产品 quality 同时执行 preflight/final ignore-policy 与 sensitive-information 检查；只扫描 Git 可见内容，不读取真实 .env。完整 pytest 中已含性能契约断言不等于运行性能协议；本轮不执行 benchmark/warm-up/测量。

## 资源与额度

- 恢复根 E:\Agent\cyber-town-f009-step6-qa\recovery-20260905-01；接续 1,112 文件 / 190,189,388 bytes，总上限 2 GiB。
- qa-tool-contract-02 一次、256 MiB；native-quality-03 一次、1 GiB；各自 machine-ledger.md 8 MiB，包含在批次容量内。精确预登记在 current-task，必要子资源仍登记先于操作。
- 新批次创建前再次核实新鲜度、父链、进程和容量；所有旧批次、快照、台账、static-diagnostic-01 只读保留，不归档重写或删除。
- 本轮收口：回归 1/1、完整 quality 1/1、新机械 1/2；历史 qa-tool-contract-01 为 1/1、此前机械 1/2，旧失败批次额度不重置。新资源均保留，不复用。
- 复用既有正式项目 .venv 及固定 uv/Godot/Git，fake-only；禁止安装依赖、真实 provider/.env/F-005 真实资源、Git 交付。
- 性能仍保留 E:\Agent\cyber-town-f009-step6-qa\recovery-20260905-01\performance 下统一 warm-up 一次 + 5 个测量 run；需覆盖无 recorder、内存 recorder、SQLite observability、pre-dispatch reject、完整本地回环 on/off 及三 SQLite 空间/ownership 诊断。只有完整语义验收通过后另获批准、核对新鲜度并预登记才可执行；阈值与验收契约第 6 节不变，当前不得启动。

原完整验收停止状态仍保留。下一动作仅提议另行批准实际业务 PID/退出码观察缺口的最小修正，并据此确定保留原前置条件的单次对照诊断；当前不修复、不新增批次、不运行完整 quality 或性能。
