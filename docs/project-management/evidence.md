# F-009 当前证据索引

更新时间：2026-09-21

## 当前结论

B1、Q1、B2与R2已完成；QA observer恢复、tool16/R7、最终quality10及固定性能1+5均已通过。Step 7最终PR HEAD CI、PR #13合并及合并后`main` CI均已通过，任务卡与实施计划归档已经生效。当前无活动任务，F-009授权已消费完毕。

## 2026-09-21 文档偏移校准与本地资源复核

只读文件系统复核确认 `E:/Agent/comprehensive-cases/15-cyber-town-f009`、`E:/Agent/cyber-town-f009-step5-tests` 和 `E:/Agent/cyber-town-f009-step6-qa` 均不存在。现有Git与文档证据不能确定删除时间、执行主体或外部授权链，因此只记录“观察为不存在”，不反向伪造删除执行记录。本次文档收尾未执行删除、移动、压缩、服务、测试、quality、性能或真实Provider调用。

`git worktree list --porcelain` 仍登记 `E:/Agent/comprehensive-cases/15-cyber-town-f009`，HEAD为 `69da08982760cff23736a37cdd25c2c779a9ce36`，并报告 `prunable gitdir file points to non-existent location`。本轮没有运行会写入仓库元数据的 `git worktree prune/remove`，也没有删除本地或远程分支。原worktree的未提交`AGENTS.md`差异不再可从该路径读取，只保留2026-09-19清单中的摘要与SHA-256。

两个仓库外证据根历史盘点合计4,480,321,135 bytes，其中的原始SQLite、运行目录和测试现场未完整进入Git，当前不能仅凭仓库恢复。必须长期保留的证据仍包括正式仓、`docs/project-management/`、归档任务卡、`docs/archive/F-009-过程记录-20260905/`、机器索引、manifest、9个分片及整体SHA-256。历史段落继续表示其记录时点的事实；当前资源状态以本节和[F-009本地资源处置清单](F-009-本地资源处置清单.md)为准。

用户随后单独批准审查上述15个正式文档变化、提交并仅推送当前 `docs/f-009-post-merge-closeout` 分支。该授权不包含产品测试、quality/性能重跑、资源删除、`git worktree prune/remove`、分支删除、PR、合并或`main`修改；实际提交与远端分支结果以本轮Git复核为准。

## 2026-09-19 PR #13合并、本地main同步与收尾证据

GitHub仓库规范地址为 `https://github.com/Muggle8888/15-cyber-town.git`。PR [#13](https://github.com/Muggle8888/15-cyber-town/pull/13) 的最终HEAD为 `a0911b95b657f3fb557d2a422c15836e14fcb9fc`；最终PR Quality run [`35343077888`](https://github.com/Muggle8888/15-cyber-town/actions/runs/35343077888) 为completed/success。PR于2026-09-18 20:10:43 +08:00合并，`main`合并提交为 `75171492070bddddffef58cc4f0fe9552d40bb77`；PR最终HEAD与该squash提交的Git tree一致。

合并后`main`触发的Quality run [`35343297890`](https://github.com/Muggle8888/15-cyber-town/actions/runs/35343297890) 为completed/success，证明远端主分支已通过交付后的完整CI门禁。正式仓origin已校准到规范地址，执行`git fetch origin`后，本地`main`从 `1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3`安全快进到 `75171492070bddddffef58cc4f0fe9552d40bb77`，随后从该提交创建本地文档收尾分支 `docs/f-009-post-merge-closeout`。

本地整理前正式仓工作区干净。功能worktree `E:/Agent/comprehensive-cases/15-cyber-town-f009`继续保留，既有未暂存`AGENTS.md`修改未被覆盖；Step 6证据根 `E:/Agent/cyber-town-f009-step6-qa/recovery-20260905-01`继续保留。8000/8001监听均为0。本次收尾未运行测试、quality、性能、真实Provider或业务服务，未删除worktree、分支、证据或其他资源，也未新建PR或向远端推送。

## 2026-09-18 Step 7交付CI与归档准备证据

归档包装提交 `265a5441d44eef8ba1ae261a7d950271fabb6139` 精确包含12个归档目标；工作树与暂存索引均按机器索引重组为36,115,596 bytes，SHA256保持 `7faa58c14a36029de2864fc410fcdd6bfd2e15ee648ac4079141e708fba979`。ignore检查、完整仓库敏感扫描和`git diff --cached --check`均通过后推送。Quality run [`35340779561`](https://github.com/Muggle8888/15-cyber-town/actions/runs/35340779561) 在Linux mypy阶段失败：4个QA/测试文件共36项Windows专属属性类型错误；敏感信息门、lock和Ruff已通过。该失败分类为Step 7交付环境兼容缺陷，不是产品、性能或安全扫描失败。

提交 `aefa027ca11d385b1e61094d56821d996cd1f2d0` 只修改上述4个文件，为Windows last-error语义增加非Windows synthetic fallback，并用可移植属性读取保持Windows真实行为。提交前Ruff、mypy 132个源文件、42个相关用例、定向敏感扫描和diff检查均通过。Quality run [`35341763570`](https://github.com/Muggle8888/15-cyber-town/actions/runs/35341763570) 已通过敏感信息前门、lock、Ruff、mypy、schema、Godot import/unit、connectivity和dialogue-connectivity，随后pytest以2,503 passed、133 skipped、192 failed、247 errors停止。439项非通过精确归类为：F-009 Step 6专项QA在无授权Windows根的通用Linux运行中428项、Step 5硬编码Windows根的归因测试10项、deadline剩余时间精确浮点断言1项。

提交 `4991f317f6b3a86c1751bfb71f95f58d651bc993` 将F-009 Step 6专项套件限定为仅在显式`F009_NATIVE_ROOT`授权上下文收集执行；QA runner的`native_session`在正式tool/readiness/quality批次中会在pytest收集前设置该变量，因此历史Step 6覆盖语义不变。5个归因测试改用pytest临时绝对根，deadline断言改为1毫秒绝对容差。提交前Ruff、mypy 132文件、受影响测试16 passed/6 context-skipped、敏感扫描0 finding及diff检查均通过。

Quality run [`35342268748`](https://github.com/Muggle8888/15-cyber-town/actions/runs/35342268748) 在 `4991f317` 上completed/success：ignore与敏感信息前后门、lock、Ruff、mypy、schema、Godot import/unit、9场景connectivity、10基础+multi-NPC dialogue-connectivity及pytest全部通过；pytest为2,106 passed、969 skipped、0 failed/error。新增的836个skip全部来自缺少显式授权根时不运行F-009 Windows专项套件；原133个历史条件skip保持。未运行Step 6 quality10、性能1+5或真实Provider，未启动持续业务服务。

完整F-009活动任务卡与实施计划已复制到 `docs/archive/task-cards/F-009-safety-cost-performance.md` 和 `F-009-implementation-plan.md`；`current-task.md`与当前实施计划已重置为无活动任务。此归档提交只表示“归档已准备、以PR合并生效”；它改变PR HEAD，必须等待该HEAD的新Quality CI全绿后才允许squash merge。merge SHA与最终CI由GitHub PR #13记录，合并后只做远端main与PR状态只读核对，不为抄写merge SHA再建第二个PR。

## 2026-09-18 Step 7-R3 定向敏感信息preflight证据

执行前正式仓、功能worktree、PR #13、base/head及旧Quality run均未漂移；staged为0，Git变化精确为R2的16个授权路径。扫描器、wrapper和workflow无工作区修改。

唯一一次入口为项目既有 `.venv`、`PYTHONPATH=backend/src`、`python -B`，直接调用 `cyber_town.quality.scan_paths`。固定目标12个：归档入口、机器索引、manifest以及 `part-001.md` 至 `part-009.md`。实际运行1/1，exit code=0，finding_count=0；输出没有匹配原文或疑似敏感值。

本次没有调用 `scan_repository`、`_check_repository_policies` 或 `scripts/quality.py`，没有运行Ruff、mypy、pytest、Godot、完整quality、CI或服务；没有修改归档、扫描器、测试、门槛或workflow。R3关闭了R2分片正文的定向内容验证缺口，`content_verified_by_current_gate=true`；完整仓库最终结论仍以推送后新HEAD的Quality CI为准。

## 2026-09-18 Step 7-R2 归档包装修复与完整性证据

执行前正式仓仍为 `feat/f-009-delivery@8a88c571eeae478f494c4e1ab7ab456fbe049280`、upstream ahead/behind=`0/0`，只有R0/R1四份治理文档变化；功能worktree仍只保留既有 `AGENTS.md`。PR #13保持OPEN、非Draft、MERGEABLE/UNSTABLE，base/head未变，唯一Quality run仍为 `35333874674` completed/failure。

拆分源严格使用 `HEAD:docs/archive/F-009-过程记录-20260905/evidence.md`：原Git blob为36,115,596 bytes，SHA256=`7faa58c14a36029de2864fc410fcfcdd6bfd2e15ee648ac4079141e708fba979`。源是有效UTF-8，共203,810行，最大单行29,725 bytes，满足固定换行边界拆分前置。

R2只在UTF-8完整换行边界拆分，生成 `evidence.parts/part-001.md` 至 `part-009.md` 共9片；最小2,562,794 bytes、最大4,194,242 bytes，全部大于0、不超过4,194,304 bytes且严格低于5,242,880 bytes。所有分片均可UTF-8解码，编号连续且无重复或缺号。

机器索引为 `docs/archive/F-009-过程记录-20260905/evidence.index.json`，入口仍为同目录 `evidence.md`，manifest为同目录 `manifest.json`。按索引顺序原始字节连接9片，重组结果为36,115,596 bytes，SHA256仍为 `7faa58c14a36029de2864fc410fcfcdd6bfd2e15ee648ac4079141e708fba979`。索引保留manifest既有来源记录36,275,701 bytes/SHA256 `3b03fcef07d1784f41d39660935a908874995d8c8eee854bbb1490042ec85f74`，没有丢弃或摘要化历史字节流。

`manifest.json` 的空数组finding键已从 `github_live_token` 改为 `github_live_token_matches`，值仍为空数组；其他finding及patterns历史含义保持。机器索引与manifest均通过重复键拒绝式JSON解析，入口、索引、manifest及全部分片均低于5 MiB。R2修复1/1及离线完整性核验1/1已用。

本轮未调用 `scan_repository`、`scan_paths`、`_check_repository_policies` 或 `scripts/quality.py`，未运行Ruff、mypy、pytest、Godot、quality、性能、CI或服务；未执行git add、commit、push或PR操作。因此当前只证明包装和无损重组，`content_verified_by_current_gate=false`，不得宣称归档正文已通过敏感信息门禁。下一项仍需用户单独批准一次定向preflight。

## 2026-09-18 Step 7 PR #13 CI只读诊断结论

诊断前后只读复核一致：正式仓为 `feat/f-009-delivery@8a88c571eeae478f494c4e1ab7ab456fbe049280`，upstream=`origin/feat/f-009-delivery`、ahead/behind=`0/0`、`origin/main=1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3`；除R0已登记的四份治理文档外无新增变化。功能worktree为 `feat/f-009-safety-cost-performance@69da08982760cff23736a37cdd25c2c779a9ce36`，只保留既有未暂存 `AGENTS.md`。PR [#13](https://github.com/Muggle8888/15-cyber-town/pull/13) 仍为OPEN、非Draft、MERGEABLE/UNSTABLE，base/head未变；只有 [Quality run 35333874674](https://github.com/Muggle8888/15-cyber-town/actions/runs/35333874674) 且仍为completed/failure。`environment_drift=false`。

`docs/archive/F-009-过程记录-20260905/evidence.md` 的Git HEAD blob为36,115,596 bytes；扫描器 `MAX_TEXT_FILE_BYTES=5 * 1024 * 1024`，对超过该值且不是识别二进制的内容直接记录 `oversized_text_file` 并跳过正文扫描。因此该finding分类为 `archive_packaging_policy_conflict`，`content_verified_by_current_gate=false`，形成 `final_delivery_validation_gap=true`。本诊断没有读取、复制或重写该大文件正文。

`docs/archive/F-009-过程记录-20260905/manifest.json` 中 `sensitive_scan.findings.github_live_token` 的值类型为empty array、元素数为0；GitHub/OpenAI/AWS token及private-key-header四类签名匹配均为0。结构化扫描器因字段名以 `TOKEN` 结尾且值是非字符串、非null容器而无条件生成 `credential_assignment`。因此该finding分类为 `deterministic_scanner_false_positive`，不是已确认凭据或安全事件。

`backend/src/cyber_town/quality.py`、`scripts/quality.py` 与 `.github/workflows/quality.yml` 在PR HEAD和 `origin/main` 的Git blob分别完全一致；归档文件只由提交 `165aa3e` 引入，PR CI是119文件最终组装后的首次正式扫描。以上结论来自 `git cat-file -s`、`git rev-parse <ref>:<path>`、`git log --follow`、静态源码检索、`gh pr view`、`gh run list/view --log-failed`，未运行本地扫描器、测试、quality或服务。

候选最小修复尚未授权：维持全局5 MiB上限；不按目录skip、不压缩或伪装二进制；把大证据按确定性顺序拆为每片小于5 MiB的文本，并用小型索引记录顺序、每片字节数/SHA256、原文件整体SHA256与重组方法；将 `github_live_token` 改为中性字段名并更新manifest哈希/索引。修复完成后也只能在单独授权下运行定向敏感信息preflight，随后提交、推送与CI重跑仍需独立授权。精确路径+SHA豁免属于另一项独立安全决策，本轮未选择、未授权、未实施。

额度：Step 7-P1与R0保持已用；本次CI只读诊断1/1及R1文档持久化1/1已用。修复、定向验证、提交、推送、CI重跑、合并均为0且未授权；未修改归档、manifest、扫描器、workflow或任何产品/测试文件。

## 2026-09-18 Step 7 PR #13 CI失败停止证据

PR [#13](https://github.com/Muggle8888/15-cyber-town/pull/13) 已创建，state=`OPEN`、非Draft、mergeable=`MERGEABLE`、mergeStateStatus=`UNSTABLE`；base=`main@1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3`，head=`feat/f-009-delivery@8a88c571eeae478f494c4e1ab7ab456fbe049280`。GitHub PR files分页API确认119个文件且无重复；正式交付worktree在P1停止时仍为ahead/behind=`0/0`且工作区干净，功能worktree只保留未暂存的专用 `AGENTS.md`。

唯一初始CI为 [Quality run 35333874674](https://github.com/Muggle8888/15-cyber-town/actions/runs/35333874674)，2026-09-18 10:16:43 UTC创建、10:16:55 UTC完成，event=`pull_request`、status=`completed`、conclusion=`failure`，head仍为 `8a88c571eeae478f494c4e1ab7ab456fbe049280`。job=`quality` 的 `Run unified quality gate` 在 `sensitive-information-preflight` 报告两个扫描finding：`docs/archive/F-009-过程记录-20260905/evidence.md:0: oversized_text_file` 与 `docs/archive/F-009-过程记录-20260905/manifest.json:0: credential_assignment`。本状态对账未读取两个文件的内容；`credential_assignment` 只表示扫描器finding，尚未确认为真实凭据或安全事件。

P1按失败即停止合同在初始CI失败后停止：fetch 1/1、远端与重复PR核验1/1、PR创建1/1、初始CI观察1/1已用；PR元数据修正0/1、状态提交0/1、状态推送0/1、后续HEAD CI观察0/1均未执行，并随P1授权消费而关闭，不得继承。P1没有修改文件、提交、再次推送、重跑CI、启动服务、修改main或合并。R0只校准 `current-task.md`、`progress.md`、`evidence.md` 与 `roadmap.md` 四份正式治理文档，不提交、不推送、不诊断或修复；后续只可另行申请只读CI失败诊断授权。

## 2026-09-18 Step 7 Git分支交付

授权前fetch确认 `origin/main=1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3`，与两个worktree原HEAD一致；远端目标分支事前不存在。功能worktree精确暂存100个批准文件并排除专用 `AGENTS.md`，提交 `69da08982760cff23736a37cdd25c2c779a9ce36`；正式worktree基于该提交创建 `feat/f-009-delivery`，治理提交为 `fdc92075c7353e7e60cc3fc702b8de845056b2f7`，Step 6状态/归档提交为 `165aa3e2a88fb17efc156e50913b937d52bcd636`。

最终内容审查覆盖119个路径：`git diff --check`通过，敏感模式与环境/SQLite/日志/缓存风险路径均为0，QA runner/runtime/test、API入口和benchmark五个冻结SHA256全部与Step 6证据一致。交付worktree无staged或未提交变化；原功能worktree只保留未暂存的专用 `AGENTS.md`。未重跑测试、quality、性能或服务。

`origin/feat/f-009-delivery` 已创建，首次推送后本地、tracking与远端SHA均为 `165aa3e2a88fb17efc156e50913b937d52bcd636`，ahead/behind=`0/0`。GitHub提示仓库新位置为 `Muggle8888/15-cyber-town`，本次旧origin通过重定向成功；未修改remote配置。未创建PR、未合并、未修改main、未删除资源；本状态收口提交推送后，唯一下一项为等待PR授权。

## 2026-09-18 Step 6 完成证据

S3实际唯一矩阵使用冻结 `scripts/f009_step5_benchmark.py` SHA256 `D4ABD8F52AFBD9D5D8D6013194E78DA759B7085B816DCD366F3598348969DCE7`，完成1次warm-up、5次测量、8个场景及43目录/199文件的固定manifest。`failure_codes=[]`、`warning_codes=[]`；所有阻断延迟、吞吐、空间与dispatch ownership门禁通过。三SQLite仅记录 `three_sqlite_p95_exceeded`、`three_sqlite_p99_exceeded` 两个合同预定义的非阻断诊断，未修改阈值。

关键实际结果：完整回环off p95/p99=51.9231/57.4220ms、on=169.2692/232.0144ms，on/off p95增量约117.3461ms≤140ms；内存control p95/p99=2.0215/2.5517ms，no-recorder-control p95=1.9378ms，配对增量约0.0837ms≤0.75ms；SQLite observability p95/p99=71.2849/107.9719ms、吞吐16.722478 req/s；pre-dispatch reject p95=1.716ms且dispatch=0。control/observability/three-SQLite增长分别满足256/512/768KiB空间合同。

performance根199文件/20,357,594 bytes；`performance-summary.json` 733,658 bytes/SHA256 `A777ACD208535767C9C9820C89803EE4E85789F997DF40F05673B69D150174A1`。恢复区最终19,611文件/1,147,659,064 bytes<2GiB，8000/8001及全部Python监听为0，冻结QA代码哈希与功能仓101项变化计数保持。

此前两次入口组装错误分别在import阶段缺少 `PYTHONPATH=backend/src`、在matrix创建前缺少已登记TEMP根；两次均无 `full-matrix-01`、warm-up=0、测量=0，不构成性能运行。实际矩阵是S3唯一一次，额度1/1已用。tool16、R7、quality10与S3全部完成后，Step 6满足验收契约，状态迁移为 `COMPLETE + CONSUMED`、`step6_complete=true`、`awaiting_step_7_authorization=true`；不得自动进入Step 7。

## 2026-09-18 R7 observer drain最小恢复合同

R4与R6失败签名一致：marker文件写入后，native失败报告均记录last_action=3、last_relative_path=`native-monitor-drain.marker`、drain_completed=false、close_returned=true及关闭阶段Win32 995；R4 marker到native摘要登记约19.6秒，R6约19.8秒。R5与tool14/tool15曾成功，说明不是固定路径拒绝或必现的Windows API失败。

源码控制流确认 `drain()` 在marker未进入seen时每轮调用 `self.check()`；活动根的check会扫描batch树、整个recovery树和identity树。当前946,122,185 bytes/16,696文件上的等价单次只读检查实测6.374616秒。循环条件只在check之前读取seen；check返回后先检查10秒deadline。若marker在第二次耗时check期间被observer确认，代码仍可不复核seen而直接抛超时。R4/R6约20秒时序与“两次重检查+失败报告容量扫描”一致。

覆盖缺口明确：所有直接 `NativeWatcher(...).drain()` 回归都使用tmp_path，tmp_path不在BATCH_LIMITS，因而 `check()` 不执行完整recovery/identity扫描；外层真实observer只有批次级随机通过/失败，没有确定性覆盖“慢check期间marker确认”。因此允许一次最小修复：等待阶段只轮询observer error与现有10秒deadline，marker确认后保留原完整check；新增慢check确定性回归。不得延长超时、忽略observer error、删容量检查或放宽路径/ledger/identity语义。

用户再次确认总授权适用，R7合同修复/tool16/R7各0/1。新鲜tool16与R7根已于08:42:44 UTC在操作前精确登记；当前恢复区加两根上限为1,281,666,505 bytes<2GiB。quality10仍条件冻结，不得在tool16/R7全过前创建。

最小修复已实施且额度1/1已用，只改三个QA文件：`drain()` 等待循环不再重复完整check，仍即时传播observer error、保留原10秒deadline，并在marker确认后执行一次完整check；新增 `test_native_drain_single_post_ack_check`，通过慢check与异步marker确认稳定区分旧/新控制流。活动根轮换tool16/R7，tool15/R6台账进入历史只读。

V1最终通过：三个AST可解析，tool16为138函数/533参数且清单/计数集合一致，R7为18选择器/43节点且索引完整，新回归进入两份清单，tool16/R7/quality10根仍不存在。首个V1辅助断言只查看函数顶层、未递归到最后一条check而自身失败；校正只读断言后通过，不形成项目失败或批次写入。V2 Ruff check/format-check最终通过；首轮仅暴露长测试名被formatter合并后触发E501，等义缩短名称后完整复验通过。V3 strict mypy三个文件通过。V4真实执行fixture/call矩阵与新回归为2 passed，并对固定R7清单collect-only得到43 tests。未创建批次、未启动服务、未访问外部服务。

冻结runner/runtime/test/API SHA256依次为 `C27A32121EFB2738A1DB68AE9F73C87036DF7685882B25974A86F07791EFF4D0`、`F3E4ABD384640DDBCE73594E374A87208C3421FE6F795748720BBB9733C39CE0`、`35D16BECB8E68D0C2B274DA3D77A0D84365E6E46F3C90DC4144AE2F63C4BBB10`、`9A3957F67F084CDD233A87D4B92C24D53DB0C4D9B66D94477B972A436BE1800A`。功能仓总变化计数仍101，8000/8001无监听；tool16/R7/quality10均不存在。下一项只运行一次tool16，失败保留根并停止，通过后才运行R7。

tool16唯一入口在功能仓执行并exit0：138函数/533参数全部passed，all_selected_functions_executed=true、formal_evidence_unchanged=true、boundary_violations为空；父observer PID30896，native completed=true、event_count=5,218、overflow=false、unknown_paths为空、reparse=0。observer已退出，8000/8001无监听，四个冻结哈希与功能仓101项变化计数无漂移；R7和quality10仍不存在。

tool16根531文件/4,714,834 bytes，恢复区累计17,227文件/950,837,019 bytes。固定产物：contract-summary 42,545 bytes/SHA256 `B982CF165A672BF679EA8F8028CED6C2837980C4B81992FB9776A4ECE6B754C4`；pytest-summary 126,418/`8E73CAC055F09C8907EC4E69989CE0262D2441B6DD62F6A6F42F48D8F991FE56`；native-summary 205,923/`88B2CE7756A18E20031D10B280910F7306A6E7F6EC34DD64FDF10092EB0F4F3E`；ledger 902,349/`EBFAE4ABD8570B916499B0AA22D3CF602F92C20417AA0DF21301E63C30536260`；owner-ready 104/`E81D842D167048B83ADF634496AB9424295F93A9F6B45344D4221547BB024B40`；drain 24/`00C3296A81DE6FFFBBF013D93D61DC405359F776143D5961F2EEBC29A453F626`。tool16 1/1已用；下一项只运行一次R7。

R7唯一入口在功能仓执行并exit0。18选择器展开43节点全部completed，failed/skipped/xfailed/not_run均为空，first_failure=null，pytest exit0；报告state=passed，owned_processes_closed、port/environment/temp恢复、old_evidence_unchanged及report_redacted全部为true，quality/performance/product_service_started均为false。native completed=true、event_count=144、overflow=false、unknown_paths为空、reparse=0；observer PID66088已退出，8000/8001无监听，四个冻结哈希与功能仓101项变化计数无漂移。

R7根17文件/61,706 bytes，恢复区累计17,244文件/950,898,725 bytes；加quality10的1GiB上限为2,024,640,549 bytes≤2,147,483,648。固定产物：tool-readiness 6,477 bytes/SHA256 `C28A998E33F7F7BF6D79B757F05C46E789B538E6E7E2080FB68E01B71E8F4CB2`；pytest-summary 9,658/`5148392D6FF145F13871A00B9C0FAA3EB7873F0D63BE96689690BEC1AA8C51DB`；native-summary 5,523/`7084983BC59EFE6D8DB3A8F522042904B7C3764428C8AECA189F6563C7F6E982`；invocation 2,914/`BA6DE25B85E65324C0540F6CD41BFF918B6E027A5D7FE6ED0EAC0039E227C4E0`；ledger 33,756/`5CB32A6CA0FE2121BC85113B7BE0C4BA6DDB28D47AF843DAE2CA15C90EA0B963`；owner-ready 107/`0C519118A058276FB2ADFE867E82C419D368AC3BF550A2D979DF3BDB88207698`；drain 24/`00C3296A81DE6FFFBBF013D93D61DC405359F776143D5961F2EEBC29A453F626`。R7 1/1已用，QA工具冻结；下一项只运行第三个且最终quality10。

quality10唯一入口在功能仓执行并exit0。quality-summary记录lock、Ruff、mypy、schema、Godot import、Godot unit、connectivity、dialogue-connectivity、pytest九命令全部exit0且boundary/error为空，前后ignore-policy与敏感信息门通过。完整pytest共3,075结果：2,942 passed、133 skipped、0 failed，identity/termination拒绝为空；skip分布为budget_control 53、attribution 45、budget_projection历史诊断33、dialogue历史根2，均由历史根未配置的既有契约触发，与quality09一致，没有新增skip或修改测试。

quality10父observer PID59308，native completed=true、event_count=83,840、overflow=false、unknown_paths为空、reparse=0；observer已退出，8000/8001无监听，四个冻结代码哈希与功能仓101项变化计数未漂移。quality10根2,168文件/176,402,745 bytes，恢复区19,412文件/1,127,301,470 bytes。固定产物：quality-summary 10,396 bytes/SHA256 `3141585D89BB019D86659DDB99740E0525B40E0875C9A489324DE870E6A64E74`；pytest-summary 720,348/`EE8371D36F1C2FA661B6A7E15E20AD943DB2C57F7548D8C14DF4E8F5440DD267`；native-summary 860,629/`4AE402176F29EC5509607FEE311DEAEBE1CD4FA2216E270C6B0E348C8CBB0B53`；ledger 5,551,403/`0D76237FCA0A62CE38575EA42084AABDED1699F7CD1570BC73405A40715BCF42`；owner-ready 102/`8805735F74AF3541E0EAAA4A84FF080828BF51EC2745E62EF4579CB7C316E451`；drain 24/`00C3296A81DE6FFFBBF013D93D61DC405359F776143D5961F2EEBC29A453F626`。quality10 1/1已用且是最终完整批次。

S3只读前置：新根 `recovery-20260905-01/performance` 不存在；旧根外历史矩阵约20,454,979 bytes仅作容量参考，不复用。当前恢复区加新根256MiB上限为1,395,736,926 bytes<2GiB。冻结 `scripts/f009_step5_benchmark.py` SHA256=`D4ABD8F52AFBD9D5D8D6013194E78DA759B7085B816DCD366F3598348969DCE7`；精确manifest为43目录/199文件，统一warm-up 1次+5次测量。S3 0/1，失败不改阈值或追加运行。

S3入口准备发生两次命令组装失败，但实际矩阵均未开始：第一次在import前因直接Python未带 `PYTHONPATH=backend/src` 抛ModuleNotFoundError；第二次补路径后在 `_run_gate_boundary_matrix` 创建matrix前因缺少已登记 `performance/tmp` 抛 `Gate boundary TEMP root is not registered`。两次均确认 `full-matrix-01` 不存在、performance根空、warm-up 0、测量0，不属于实际性能失败或重跑。根因是入口准备未一次性覆盖模块路径与TEMP前置；现补登记 `performance/tmp`，最终入口同时绑定PYTHONPATH、TEMP、TMP，同一performance根不更名。矩阵一旦创建即计S3 1/1，任何失败停止。

## 2026-09-18 R6 observer drain失败证据

唯一R6入口 `E:\\Agent\\comprehensive-cases\\15-cyber-town\\.venv\\Scripts\\python.exe -B scripts/f009_step6_qa.py --tool-readiness --root E:\\Agent\\cyber-town-f009-step6-qa\\recovery-20260905-01\\s1-qa-stabilization-r6` 在功能仓执行，exit1。受保护pytest exit0：17个选择器展开42个节点全部passed，failed/skipped/xfailed/not-run均为空，包含 `test_s1_current_root_allowed_and_external_root_rejected` 的S1上下文直接证据；boundary_violations为空。

唯一外层首错为 `step6_native_watch_drain_timeout`。tool-readiness报告为failed，但owned_processes_closed、port_state_restored、environment_restored、temp_path_restored、old_evidence_unchanged、report_redacted均为true；quality_started、performance_started、product_service_started均为false。native摘要明确completed=false、observation_complete=false、inventory_complete=false、drain_completed=false、close_returned=true，mode=`incomplete_native_observation_not_acceptance`；failure记录event_count=136、last_action=3、last_relative_path=`native-monitor-drain.marker`、stage=read、api=GetOverlappedResult、win32_error=995。不能用pytest通过替代native完整收口，也不能把关闭阶段995单独解释为根因。

该签名与R4记录的drain marker action 3未在10秒内确认、随后关闭取消995一致，属于第二次出现的QA observer收口风险。tool14、R5和tool15之间曾未复现，不足以关闭；当前合同要求任一步失败立即停止，因此不延长超时、不改watcher、不重跑R6、不创建quality10。唯一合理下一项是另行审定只读诊断，先区分通知确认时序、observer线程状态与资源压力；它不自动授权修复或新运行。

R6 observer PID59116已退出，8000/8001无监听；冻结runner/runtime/test/API SHA256仍为 `09174E80B41FB85C228B4428D0A91A5E512C0666FDCFB9296136F83A381E2D22`、`AA6F715C37098CDF1F0CB9AEF6F6A228E6E36BD6D5C5B6E87E08E5A2155529BF`、`8488FDD7C769CDB5870BFBF42F5CF2324849528702DC71D452A5FD798565BBC2`、`9A3957F67F084CDD233A87D4B92C24D53DB0C4D9B66D94477B972A436BE1800A`；功能仓Git计数仍为0/39/62/101，diff-check通过。R6根16文件/54,927 bytes，恢复区累计16,696文件/946,122,185 bytes，quality10不存在。

R6固定产物：tool-readiness 6,339 bytes/SHA256 `062849F1FAEC81BF071E8BA3F968318E37EC64B34E5CB2BB699502BFF56D3CE6`；pytest 9,478/`FC34FC54631CA0F5CAE41237F463821E557A97752872047226F45AEE2CC49D59`；native 761/`611FDAADD327A10643AF3BA9402E23DA992AD8BC3852EF89472ABBF35A1FDB86`；invocation 2,829/`CCB02819857A1B28C5DA7487A4C2CE874496A2697DD76A992828E74CB559BF9B`；ledger 32,166/`380AD501AF46E1283ABB8FAF4F2B9CFC9EE3C93EEDAAECA37423382B569756C7`；owner-ready 107/`35A9A1821EBC7892CD4E8A710B55B536CAEA0607A42DA910E66AF10380BF28E9`；drain 24/`00C3296A81DE6FFFBBF013D93D61DC405359F776143D5961F2EEBC29A453F626`。本合同修复/tool15/R6均1/1已用；quality10 0/1未消费但因条件失败不可用，S3未到达。

## 2026-09-18 最终QA生命周期恢复合同

用户明确授权：“批准最小 QA 生命周期修复、tool15/R6 双上下文验证，并允许一次第三个且最终的完整 `native-quality-10` 批次。”这项显式授权只覆盖一次最小QA修复、一次tool15、一次R6，以及前两批全部通过后的一次quality10；它覆盖既有“不得第三个替代批次”停止规则的这一项例外，但不重置quality08/09或其他历史额度。quality10后不得再创建完整quality批次。

直接根因保持不变：`test_s1_current_root_allowed_and_external_root_rejected` 把 `machine_ledger()` 的活动根等同于readiness根；在R5上下文该假设成立，在quality09上下文不成立。修复不得扩大 `authorize_readiness_root`，而须让测试显式使用 `CURRENT_TOOL_READINESS_ROOT` 验证允许，并在tool/quality活动上下文验证非S1根被拒绝；同一测试同时进入tool15和R6清单，形成非S1与S1双上下文直接证据。

精确修改范围仅三个QA文件；固定门为V1 AST/根/历史/清单计数、V2 Ruff check/format-check、V3 strict mypy、V4矩阵真实执行和选择器核验。V1–V4全过才可创建tool15；tool15全过才可创建R6；R6全过且正式readiness回执可读，且按实际资源重新证明容量，才可创建quality10。任一步失败保留新根、写明未执行项并停止，不修改产品、阈值、skip或安全边界。

创建前只读事实：2026-09-18 08:19:40 UTC，tool15、R6、quality10均不存在，8000/8001无监听；恢复区16,150文件/941,352,283 bytes。tool15≤256MiB、R6≤64MiB；两者结束后再用实际恢复区总量加quality10的1GiB上限核验2GiB总约束。精确路径与ledger预登记见current-task；本合同额度为修复0/1、tool15 0/1、R6 0/1、quality10 0/1，S3 0/1未到达。

唯一修复已完成且1/1已用，只改三个QA文件。V1无项目导入地解析三个AST并确认tool15/R6/quality10、历史tool14/R5/quality09、137/532与17/42；首次V1辅助命令因试图对AST下标直接literal_eval而自身失败，未产生项目结论或写入，修正辅助读取后V1通过。V2 Ruff check与format-check通过；V3 strict mypy三个文件通过；V4真实执行fixture/call矩阵为1 passed，并对17个R6选择器collect-only得到42 tests。冻结runner/runtime/test/API SHA256为 `09174E80B41FB85C228B4428D0A91A5E512C0666FDCFB9296136F83A381E2D22`、`AA6F715C37098CDF1F0CB9AEF6F6A228E6E36BD6D5C5B6E87E08E5A2155529BF`、`8488FDD7C769CDB5870BFBF42F5CF2324849528702DC71D452A5FD798565BBC2`、`9A3957F67F084CDD233A87D4B92C24D53DB0C4D9B66D94477B972A436BE1800A`。功能仓Git计数保持0/39/62/101，三个新根仍不存在；下一项只运行一次tool15。

tool15唯一入口执行exit0：137函数/532参数全部passed，新增生命周期测试在tool15非S1活动根下通过；all_selected_functions_executed=true、formal_evidence_unchanged=true、boundary_violations为空，full_quality_started=false、performance_started=false。native completed=true、event_count=5,224、overflow=false、unknown_paths为空、reparse=0；observer PID11304已退出，8000/8001无监听，冻结指纹和功能仓0/39/62/101未漂移。

tool15根530文件/4,714,975 bytes；恢复区累计16,680文件/946,067,258 bytes。固定产物：contract-summary 42,290 bytes/SHA256 `E6772B245FB83A15DEE803952032B6D74C02B455EF973F5EBF05970B6CECA002`；pytest-summary 126,899/`23C995AE635475B867103C1CAC14B880056E23B563BEC9F55EF67CB0A1DDADCE`；native-summary 205,802/`F351FDEEB750430FBF9E48FA6B9A6A0BE9B32464BC6652C9077934E5E65296B0`；ledger 902,159/`D24D229F8134464406E3DE92B787A1624579DCCC3A2EC10F76F8E5E1BF34D18F`；owner-ready 104/`AEE067B8F1AA58DBBFA2A10872B0A9655B067113C202FC33620575D24F46251C`；drain 24/`00C3296A81DE6FFFBBF013D93D61DC405359F776143D5961F2EEBC29A453F626`。tool15 1/1已用；下一项只运行一次R6。

## 2026-09-18 S2 替代 quality09 失败证据

唯一入口 `E:\\Agent\\comprehensive-cases\\15-cyber-town\\.venv\\Scripts\\python.exe -B scripts/f009_step6_qa.py --quality recovery-20260905-01/native-quality-09` 在功能仓执行，外层exit 1。repository preflight通过；lock、Ruff、mypy、schema、Godot import、Godot unit、connectivity、dialogue-connectivity均exit0。connectivity的connected、duplicate_rejected、http_error_recovery、invalid_recovery、non_string_rejected、redirect_rejected、stopped_service、timeout_recovery、unavailable九个场景全部通过。完整backend pytest随后exit1，repository final未执行。

pytest摘要记录2,011条结果：1,877 passed、133 skipped、1 failed；boundary_violations为空，identity/termination diagnostic rejection均为空，raw_output_retained=false。唯一失败为 `backend/tests/test_f009_step6_qa.py::test_s1_current_root_allowed_and_external_root_rejected`，phase=call，failure_location=`scripts/f009_step6_runtime.py:66`，也是当前摘要最后一条；没有可靠collection总数，不能把未报告节点说成通过或给出伪造not-run数量。

源码链路直接解释失败：完整quality的受保护pytest通过 `command_environment` 继承 `F009_MACHINE_LEDGER=native-quality-09/machine-ledger.md`；`machine_ledger()` 因而返回活动quality根。测试以 `current = qa.machine_ledger().path.parent` 取得该根，再调用 `authorize_readiness_root(current, ..., require_fresh=False)`；runtime第66行只允许 `canonical in S1_ROOTS`，所以活动quality根必然触发 `step6_s1_root_not_approved`。同一测试在R5定向运行时活动根就是R5，因此曾通过。该测试缺少S1与完整quality生命周期区分，是QA工具/测试契约缺陷，不是产品行为、性能指标或环境问题。

quality09 native completed=true、event_count=50,198、overflow=false、unknown_paths为空、reparse=0。observer PID40148与lock/ruff/mypy/schema/Godot/connectivity/dialogue/pytest九个命令PID均已退出，8000/8001无监听；冻结runner/runtime/test/API入口哈希与运行前完全一致，两仓Git计数仍为功能0/39/62/101、正式0/9/10/19。quality09根1,634文件/120,362,783 bytes；恢复区累计16,150文件/941,352,283 bytes<2GiB。

固定产物：quality-summary 10,310 bytes/SHA256 `891A2ED88A8890DC432A70EBC9D1F7AC4E5029F595D06A3BFEA2B4B91BA253D4`；pytest-summary 480,404/`8BD42696C9BD35E6A835E6E33D93059FA2ECAB52529ED9E7A0A9FEB3F82D1A8B`；native-summary 586,587/`0B159AC94E0A005C5C6E1AF579E0EF811AAC024FECC305C96E9E3C6BE1422192`；ledger 3,799,615/`986439ED8691C9C9264521BC2B12F8D5C99FA0007DC8BFDC16566AB6BEAF329C`；owner-ready 102/`2BB22A46A2EBDDFEE83D9A6880A353D1391C6B204F6BB8A5F5760901FB29C0DD`；drain 24/`00C3296A81DE6FFFBBF013D93D61DC405359F776143D5961F2EEBC29A453F626`。全部资源保留，不删除或覆盖。

状态迁移为 `BLOCKED + CONSUMED`：quality09 1/1已用，QA工具解除冻结，S3禁止进入。既有合同明确不得重跑或创建第三个替代quality批次；下一步需要用户显式决定是否建立独立QA生命周期修复，并是否改变该批次数停止规则。普通“必要授权预先批准”不能自动覆盖这一明确禁止项。

## 2026-09-18 S2 替代完整 quality 合同

历史quality08的1/1不重置：该批唯一失败已被直接证据归类为QA台账生命周期缺陷。R5随后只修QA工具并重新通过V1–V4、tool14与当前readiness，正式回执接受R5的5份产物和4个冻结代码指纹。用户预先批准的必要授权现固化为唯一一次 replacement `native-quality-09`；不授权失败后重跑或第三个替代quality批次。

运行范围只包含 `E:\\Agent\\comprehensive-cases\\15-cyber-town\\.venv\\Scripts\\python.exe -B scripts/f009_step6_qa.py --quality recovery-20260905-01/native-quality-09`，cwd功能仓。保留既有repository preflight/final及lock、Ruff、mypy、schema、Godot import/unit、connectivity、dialogue-connectivity、完整backend pytest原顺序和语义。冻结runner/runtime/test/API入口SHA256分别为 `12164BB7985975FE96CAD4478D7AC6A8E30143E60B444FD54929FB1AAB9F15ED`、`ACC41E5B6DF9D2A8346BA5D587F510B4F75BEBC6EF9A95E91C9C33606130A8CA`、`340102639AE096B17C81B9E0F0D9013C03227E90EA258CCDE10A53EB72F2E90E`、`9A3957F67F084CDD233A87D4B92C24D53DB0C4D9B66D94477B972A436BE1800A`；运行期间不得修改代码、断言、skip或阈值。

创建前直接事实：quality09不存在，R5正式回执可读，8000/8001无监听，两仓Git计数为功能0/39/62/101、正式0/9/10/19，恢复区14,516文件/820,989,500 bytes；加quality09的1GiB上限为1,894,731,324 bytes<2GiB。沿用07:03:48 UTC的操作前精确预登记，不增加重复路径记录。运行环境local + synthetic + fake-only、provider disabled、外部调用0；任一阶段失败保留证据、分类并停止，不运行性能。

## 2026-09-18 R5 当前工具就绪通过与 QA 重新冻结证据

唯一入口为 `E:\\Agent\\comprehensive-cases\\15-cyber-town\\.venv\\Scripts\\python.exe -B scripts/f009_step6_qa.py --tool-readiness --root E:\\Agent\\cyber-town-f009-step6-qa\\recovery-20260905-01\\s1-qa-stabilization-r5`，cwd功能仓，exit 0。17个固定选择器展开42个参数节点，completed=42、passed=42，failed/skipped/xfailed/not-run均为空，first_failure=null、secondary_failures为空；原失败的fixture矩阵和生命周期五分支均实际执行通过。

readiness报告确认owned_processes_closed、port_state_restored、environment_restored、temp_path_restored、old_evidence_unchanged、report_redacted全部为true；quality_started、performance_started、product_service_started全部为false。native completed=true、event_count=134、overflow=false、unknown_paths为空、reparse=0；observer PID26588已退出，8000/8001无监听，R4的drain超时在tool14与R5均未重现。

正式 `read_current_readiness_receipt()` 只读校验成功：接受R5根、5份当前产物、17个选择器、`{"passed":42}` 及runner/runtime/test/API入口4个当前指纹。R5根16文件/59,317 bytes；恢复区累计14,516文件/820,989,500 bytes。固定产物：tool-readiness 6,309 bytes/SHA256 `44AF975E8B9CADEDF4EA48E4770C89AA00FF679C4ACDC9B550FDCE757FC1480B`；pytest 9,478/`09B09F2C98AC39E40ECE5A6522AD8A1A3FA74A6F8BE3ECB78A4AAC9F0C993E54`；native 5,181/`68234C5EC660A7214E4F2084F179075DB497310FCF6F713A80189CB1DEA20957`；invocation 2,829/`6B7E5E066F6F443ABF81BE95BB00455A628E946E66ECF064917887870059FE90`；ledger 32,166/`B522466DAFA542F06919EA6E8695DC24EB659BB455E65073113557ADD9B55904`；owner-ready 107/`8288E3017F280ED783826315F021DF5F6CD54E35550155A467E2824B8D35F86E`；drain 24/`00C3296A81DE6FFFBBF013D93D61DC405359F776143D5961F2EEBC29A453F626`。

状态迁移为QA工具重新冻结。R5修复1/1、tool14 1/1、R5 readiness 1/1全部已用；quality09 0/0且根不存在，S3性能未到达。本R5合同已消费；下一阶段须先将用户预先授权固化为独立S2替代完整fake-only quality合同，不能在本轮创建quality09或运行quality。

## 2026-09-18 R5 最小恢复合同

R4主失败已由失败位置和AST精确证实：`test_qa_ledger_sources_separate_lifecycles` 的参数为 `case, native_test_root`，其中 `case` 来自parametrize，而 `test_s1_fixture_and_call_signature_matrix` 的固定fixture允许集遗漏 `native_test_root`。R5唯一行为修复是在该允许集中补齐已存在的fixture；不得更改选择器、参数化、断言语义、skip或产品代码。

R4的native drain marker超时保留为次级时序风险。既有源码表明watcher在记录事件后才加入seen，单次报告不足以证明可安全修改observer；因此R5不修改watcher。tool14和R5必须各自证明native完整收口；若drain再次超时，立即停止并升级重复风险，不创建新根、不进入quality。

R5精确修改范围只有 `scripts/f009_step6_qa.py`、`scripts/f009_step6_runtime.py`、`backend/tests/test_f009_step6_qa.py`：补齐fixture允许项，把tool13/R4台账转为历史只读，并把活动根轮换到尚不存在的tool14/R5。修复额度1次。V1检查AST、根绑定、17选择器/42节点和fixture允许集；V2执行三个文件Ruff check/format-check；V3执行三个文件strict mypy；V4先真实执行矩阵测试，再collect固定17选择器并确认42节点。V1–V4全过后只运行一次tool14；tool14全过后只运行一次R5 readiness。任一失败保留证据并停止。

R5唯一修复已完成且修复额度1/1已用。V1通过：三个文件AST可解析，tool14/R5绑定、17个唯一选择器、42个参数节点及fixture允许集均准确；V2 Ruff check与format-check通过；V3 strict mypy三个文件无错误；V4真实执行 `test_s1_fixture_and_call_signature_matrix` 为1 passed，并对17个固定选择器collect-only得到42 tests。runner/runtime/test SHA256分别为 `12164BB7985975FE96CAD4478D7AC6A8E30143E60B444FD54929FB1AAB9F15ED`、`ACC41E5B6DF9D2A8346BA5D587F510B4F75BEBC6EF9A95E91C9C33606130A8CA`、`340102639AE096B17C81B9E0F0D9013C03227E90EA258CCDE10A53EB72F2E90E`；产品API入口仍为 `9A3957F67F084CDD233A87D4B92C24D53DB0C4D9B66D94477B972A436BE1800A`。两仓Git计数仍为功能0/39/62/101、正式0/9/10/19，diff-check通过；tool14、R5与quality09在静态阶段均不存在，8000/8001无监听。

唯一tool14入口 `E:\\Agent\\comprehensive-cases\\15-cyber-town\\.venv\\Scripts\\python.exe -B scripts/f009_step6_qa.py --tool-contract` 在功能仓执行，exit 0。136函数/531参数全部passed，all_selected_functions_executed=true，boundary_violations为空，migration_stage_evidence_complete=true，formal_evidence_unchanged=true；full_quality_started=false、performance_started=false。native completed=true、event_count=5,240、overflow=false、unknown_paths为空、reparse=0；observer PID62876已退出，8000/8001无监听，R4的drain超时未重现。

tool14根530文件/4,711,278 bytes；恢复区累计14,500文件/820,930,183 bytes。固定产物：contract-summary 41,987 bytes/SHA256 `69A1D32A5B18CD42E0DF864AF98F8FA7D70CA60146E41AACD479C329833A0297`；pytest-summary 126,042/`53FE1C262DE46B609135B14E658F38DA56FAADC9475E12D093D059427491467F`；native-summary 205,803/`EEE8E5C81BBD9008CCF525E4FEA5C3D27A0D6CC5FF99675617B151611E903C1F`；ledger 900,062/`97D89B89C1A3B60620BAFFF4D33AD4A4F91493BAB16D1095BF1B307B3D6B58F0`；owner-ready 104/`5E3A893BA9D2075B2857270BA378AF7591E8AC11722A466C4D354213E6BD0494`；drain 24/`00C3296A81DE6FFFBBF013D93D61DC405359F776143D5961F2EEBC29A453F626`。tool14 1/1已用，R5仍未创建；下一项只运行一次R5 readiness。

创建前只读检查：tool14、R5与quality09根均不存在；8000/8001无监听；恢复区既有13,970文件/816,218,905 bytes，加入tool14的256MiB与R5的64MiB上限仍低于2GiB。R5修复 `0/1`、tool14 `0/1`、R5 readiness `0/1`；quality09 `0/0`，不得创建。预登记时间与精确根见current-task。用户已预先批准恢复路线中的必要授权，本合同只消费R5范围，不重置R4或S2额度。

## 2026-09-18 R4 readiness 失败证据

唯一入口为 `E:\\Agent\\comprehensive-cases\\15-cyber-town\\.venv\\Scripts\\python.exe -B scripts/f009_step6_qa.py --tool-readiness --root E:\\Agent\\cyber-town-f009-step6-qa\\recovery-20260905-01\\s1-qa-stabilization-r4`，cwd功能仓，exit 1。R4完成22个nodeid，其中前21个passed，第22个 `test_s1_fixture_and_call_signature_matrix` 在 `backend/tests/test_f009_step6_qa.py:7958` 失败；后续7个选择器未执行。

直接AST对照确认唯一主断言原因：新增到readiness清单的 `test_qa_ledger_sources_separate_lifecycles` 参数为 `case, native_test_root`，其中 `case` 来自parametrize，但矩阵的fixture allowlist仍只有 `monkeypatch, request, tmp_path`，所以 `arguments <= fixture_names | parameters` 必然为false。R3只暴露了该函数的第一个过期断言16/37；R4修复数量后才到达第二个过期断言。此前V4只是collect-only，没有执行fixture矩阵函数；tool13清单也不包含该S1矩阵函数，因此两项通过都不能证明矩阵自检通过。这是门禁覆盖缺口，不是产品或性能失败。

失败收口另记录独立次级异常：native drain marker超时，drain_completed=false、drain_error=`step6_native_watch_drain_timeout`、close_returned=true；最后通知为drain marker action 3，随后关闭取消产生Win32 995。现有证据不足以判断marker为何未进入 `seen`，不得把该次级异常忽略为正常995，也不得在未诊断前修改watcher。observer PID67436已退出，8000/8001无监听；readiness报告确认environment/port/temp恢复、旧证据不变、报告脱敏，未启动quality、性能或产品服务。

R4根最终16文件/50,340 bytes；恢复区累计13,970文件/816,218,905 bytes。固定产物：pytest-summary 5,911 bytes/SHA256 `72D38114F8FD890CB5275B4B248FF4DA44754B0D37255E317BD024BFF0A05E75`；tool-readiness-summary 5,318/`102B0C58755A3DAEF6F1141EB20EF8B62EDA800E1C066C5B70D166F4C0EB55F1`；native-summary 762/`2F5D13B37E2C921D5B8AD40B52C40B15A2209DC1066BE112B503776F3F731976`；invocation 2,829/`7AE5F7169A150CF8CA3E254808372243B57C1EB1CFE96DDA3433C77C0DD05957`；ledger 32,166/`C32DB03289B57D266B890111072412195C967DAC82140713B9EE8658B7201B8B`；owner-ready 107/`99E0E784A344553A093D8267435AFFEEFD1DC1365421655E1D88830743AB46BF`；drain 24/`00C3296A81DE6FFFBBF013D93D61DC405359F776143D5961F2EEBC29A453F626`。全部旧证据与失败R4根保留。

额度：R4修复1/1、tool13 1/1、R4 readiness 1/1均已耗；R5 0/0、quality09 0/0，S3未到达。当前停止于 `BLOCKED + CONSUMED`。候选R5必须先诊断drain超时，再只修已证实的fixture allowlist，并将矩阵测试的真实执行加入静态门；不得直接重跑或进入quality。

## 2026-09-18 R4 根因确认与最小恢复合同

R3主失败已由源码与直接报告共同确认：当前 `S1_READINESS_TESTS` 有17个唯一选择器，`S1_READINESS_COUNTS` 合计42；`test_s1_fixture_and_call_signature_matrix` 第7922/7924行仍硬编码16/37，因此该节点必然失败。修复只需同步这两个自检常量；不得删除选择器、降低计数、增加skip或改变测试语义。

Win32 995不是独立observer缺陷。本机对995的定义为“由于线程退出或应用程序请求，已中止I/O操作”。`NativeWatcher.close()` 先设置 `stop_requested`，再调用 `CancelIoEx`；观察线程仅在停止标志已设置且 `GetOverlappedResult` 返回995时正常break，否则仍抛 `step6_native_watch_read_failed`。R3的 `drain_completed=true`、`close_returned=true`、observer PID34728已退出及8000/8001无监听与该正常路径一致。failure详情保留995只是最后一次Win32操作诊断；native inventory未签发是因为fixture主失败已存在，finalizer按设计对任何主失败输出 incomplete 模式。R4不得修改watcher行为。

R4精确范围只有三个QA文件：`scripts/f009_step6_qa.py`、`scripts/f009_step6_runtime.py`、`backend/tests/test_f009_step6_qa.py`。允许动作仅为16/37更新到17/42、把已消费tool12/R3转为历史只读、把活动根轮换到预登记且尚不存在的tool13/R4。修复额度1次；固定静态V1–V4全部通过后才可运行一次tool13，tool13完整通过后才可运行一次R4 readiness。任一失败保留证据并停止；成功只重新冻结QA工具并停止。quality09仍为0/0，不得创建；不得运行性能、产品服务或修改产品、阈值、依赖和skip。

R4唯一修复已完成且没有修改watcher：fixture矩阵16/37更新为17/42；tool12与R3台账加入历史只读；活动根轮换到tool13/R4。V1三个文件AST、根绑定、17/42与生命周期选择器通过；V2三个文件Ruff check与format-check通过；V3 strict mypy三个文件通过；V4对17个固定选择器实际收集42个节点通过。R4修复1/1已用。

唯一tool13入口 `E:\\Agent\\comprehensive-cases\\15-cyber-town\\.venv\\Scripts\\python.exe -B scripts/f009_step6_qa.py --tool-contract` 在功能仓执行，exit 0。136函数/531参数全部passed，all_selected_functions_executed=true，生命周期五分支包含在内，migration_stage_evidence_complete=true，formal_evidence_unchanged=true；full_quality_started=false、performance_started=false。native completed=true、event_count=5,264、overflow=false、unknown_paths为空、reparse=0；observer PID51420已退出，8000/8001无监听。

tool13根530文件/4,713,471 bytes；恢复区累计13,954文件/816,168,565 bytes。固定产物：contract-summary 41,987 bytes/SHA256 `E79ECFF7A3AA24888E5C76ABC13FADEE3CD8E464A4E386A08F24230A9BF4885C`；pytest-summary 126,042/`F8F866ACC20E4D71C97F7124BFE3112FDF2742E68ACE0F517AF6555278A516F2`；native-summary 205,794/`FA9CBEF64B66429F9CF9A1C522FA8C6454BA4809D8ED4555736F963A5D097FD7`；ledger 901,989/`A7E4A92D4815ED252307D4E81091CAECF3F3D1A9B53941AF75E08E9E0C632395`；owner-ready 104/`BF8883272BA6A30E14B8E34B44354905D51982CC35E11D5F70300F01C950B6EF`；drain 24/`00C3296A81DE6FFFBBF013D93D61DC405359F776143D5961F2EEBC29A453F626`。tool13 1/1已用，R4仍未创建；下一项只执行一次R4 readiness。

## 2026-09-18 R3 当前工具就绪失败证据

唯一入口为 `E:\\Agent\\comprehensive-cases\\15-cyber-town\\.venv\\Scripts\\python.exe -B scripts/f009_step6_qa.py --tool-readiness --root E:\\Agent\\cyber-town-f009-step6-qa\\recovery-20260905-01\\s1-qa-stabilization-r3`，cwd功能仓，exit 1。运行前R3与quality09均不存在，tool12凭据与当前runner/test指纹一致，恢复区加R3上限仍低于2GiB，8000/8001无监听，两仓Git状态仍为功能0 staged/39 tracked修改/62 untracked、正式0/9/10；两仓 `git diff --check` 通过。

固定清单为17个选择器/42个参数节点。R3实际完成22个nodeid，其中前21个passed，第22个 `backend/tests/test_f009_step6_qa.py::test_s1_fixture_and_call_signature_matrix` 在call阶段失败；failure_location为 `backend/tests/test_f009_step6_qa.py:7922`。该行仍断言 `len(S1_READINESS_TESTS)==16`，第7924行仍断言计数总和为37，而当前清单已扩展为17/42。这是QA测试适配遗漏，不是产品、性能或业务环境失败。后续7个选择器未执行，其中包含当前readiness回执、根绑定与原目标生命周期测试；不能用tool12或V4收集结果替代R3通过。

父native observer在正常关闭取消期间由 `GetOverlappedResult` 返回Win32 995；源码明确在 `stop_requested` 已设置时将其作为正常break，且报告记录drain_completed=true、close_returned=true。observation_complete/inventory_complete/completed为false，是因为fixture主失败已存在时finalizer拒绝签发完整观察凭据；`step6_native_failure_unclassified` 对应主异常 `step6_identity_validation_failed` 的安全归类，不是995的失败分类。因此 `owned_processes_closed=false` 只是整体readiness未满足，不代表残留进程；只读收口确认observer PID34728已退出，8000/8001无监听。tool-readiness报告同时确认environment_restored=true、port_state_restored=true、temp_path_restored=true、old_evidence_unchanged=true、report_redacted=true；quality_started=false、performance_started=false、product_service_started=false。

R3根最终16文件/50,309 bytes；恢复区累计13,424文件/811,455,094 bytes。固定产物SHA256：pytest-summary `CA65DA2027BE5C3922743625FB1AFEC91690D0D6967E3CC47EC63A004EA2FF48`；tool-readiness-summary `1C67D201E0510F40896866F0CF3054E41F7B6A61E5C90F9B83684E3A3F49A734`；native-summary `F865CBFD9905AA237FE9168A6C2B57503600875E65FAB867003BF4F88631F97A`；invocation `3D9F9FA173D6D3F76E38A322DDE33155B931923E039E91CC65CA540D1D02A23D`；machine-ledger `E2C074BF245BC1DE48C9ABBC6CDD8A01B7C392DA0495018116D1E4BE39208D0D`；owner-ready `1E047156A17765D2F498124A811CE4B488E7FA93B3ABCE3907F45BC3F8D7C15C`；drain `00C3296A81DE6FFFBBF013D93D61DC405359F776143D5961F2EEBC29A453F626`。全部旧证据及R3失败根保留，不删除、不覆盖。

R3收口时额度为S2R结构修复1/1、tool12 1/1、R3 1/1与原S2 1/1均已耗。随后基于用户预先批准的必要恢复授权建立独立R4合同；当前R4修复0/1、tool13 0/1、R4 readiness 0/1，quality09 0/0，S3未到达。R4范围与顺序以本文顶部R4合同为准。

## 2026-09-18 S2R 生命周期修复与 tool12 通过证据

根因不是 `resource_ledger_sources()` 缺少去重，而是B2把已消费 `qa-tool-contract-11/machine-ledger.md` 加入历史后，仍让 `TOOL_CONTRACT_ROOT` 指向tool11；同一根同时承担历史与active生命周期。S2R没有放宽断言或静默去重，只修改 `scripts/f009_step6_qa.py`、`scripts/f009_step6_runtime.py`、`backend/tests/test_f009_step6_qa.py`：tool11/quality08/R2转为历史只读，活动根轮换到尚不存在的tool12/quality09/R3；原失败生命周期测试的5个参数分支加入R3固定清单。产品、SQL、Godot、依赖、skip、性能阈值与 `resource_ledger_sources()` 均未修改。

固定静态结果：V1三个文件AST及tool12/R3/quality09绑定通过；V2 Ruff check与format-check通过；V3 strict mypy三个文件通过；V4 17个选择器准确收集42个节点，包含原失败生命周期测试的tool/quality/other/wrong_path/unapproved五分支。首次V1辅助脚本因Windows路径键格式不一致产生KeyError，未发现项目失败、未写文件；修正只读脚本后V1通过，不计结构修复轮。

唯一tool12入口为 `E:\\Agent\\comprehensive-cases\\15-cyber-town\\.venv\\Scripts\\python.exe -B scripts/f009_step6_qa.py --tool-contract`，cwd功能仓，外层与pytest exit 0。136函数/531参数全部passed，all_selected_functions_executed=true，boundary_violations为空，migration_stage_evidence_complete=true，formal_evidence_unchanged=true；full_quality_started与performance_started均false。原失败的 `test_qa_ledger_sources_separate_lifecycles` 五分支全部属于本批531结果。

tool12 native completed=true、event_count=5,205、overflow=false、unknown_paths为空、reparse=0；observer PID39504已退出，8000/8001无监听。根共530文件/4,714,604 bytes，恢复区累计13,408文件/811,404,785 bytes<2GiB。固定产物：contract-summary 41,987 bytes/SHA256 `CE2B75567E8955E0A96EFFA8B14EEE281D0166E958BC84A1F7E028B999677624`；pytest-summary 126,042/`0A31F39BB7D3ADE5E4AF285884A7B9123B3F57E509E82AEAC6CA7C4D3C677C7F`；native-summary 206,010/`ED153256D7BC233D99A47D6E2659563640D5C53F68DD060B33640560FA1913E1`；ledger 902,560/`57800262CE26F4BD917CFD35103B5C632BF46D43636C9AD54629FC983DEEEC1D`；owner-ready 104/`FE67955A88CD88E9FD38A05C7FC85F820BE69BE3A9FF5777F614B42A3BD98488`；drain 24/`00C3296A81DE6FFFBBF013D93D61DC405359F776143D5961F2EEBC29A453F626`。

tool12收口时的快照为：S2R结构修复 `1/1`、tool12 `1/1` 已用，R3 `0/1`；当时的下一项是执行一次R3的17选择器/42参数节点。R3后续失败及当前额度以本文顶部R3失败证据为准；quality09仍未创建，S3未到达。

## 2026-09-18 S2 完整 fake-only quality 停止证据

唯一S2入口为 `E:\\Agent\\comprehensive-cases\\15-cyber-town\\.venv\\Scripts\\python.exe -B scripts/f009_step6_qa.py --quality recovery-20260905-01/native-quality-08`，cwd功能仓，外层exit 1。S2在创建前接受R2当前回执和四个冻结代码指纹；`native-quality-08` 为预登记后首次创建的新鲜根，没有复用旧quality批次。lock、全工程Ruff、全工程mypy、schema、Godot import、Godot unit、connectivity、dialogue-connectivity依次exit 0；connectivity的connected、duplicate_rejected、http_error_recovery、invalid_recovery、non_string_rejected、redirect_rejected、stopped_service、timeout_recovery、unavailable九个场景均通过。

全量backend pytest随后exit 1。`pytest-summary.json` 共记录1,979个结果：1,845 passed、133 skipped、1 failed；boundary_violations为空，identity与termination diagnostic rejection为空。唯一失败为 `backend/tests/test_f009_step6_qa.py::test_qa_ledger_sources_separate_lifecycles[tool]`，phase=call，failure_location为测试文件第7633行；它也是当前已报告结果的最后节点。失败后quality后置门未执行，本轮没有补跑、重跑或创建第二批。

源码只读归因：测试7611行令tool case使用当前 `TOOL_CONTRACT_ROOT`，7617行把其 `machine-ledger.md` 作为active；runner的 `HISTORICAL_LEDGERS` 第149行已经包含同一个 `qa-tool-contract-11/machine-ledger.md`，`resource_ledger_sources` 第1885行又把active追加到末尾。因此7631行的完整序列断言仍可成立，但7633行 `sources.count(active) == 1` 必然失败。这是冻结QA工具/测试的台账生命周期集合矛盾，不是产品行为、性能指标或环境故障；R2定向37节点没有覆盖这项全量QA测试，说明“定向工具就绪通过”仍不足以证明完整quality内所有QA自测一致。

S2固定产物：quality-summary 10,219 bytes/SHA256 `5D335C6943C4996019946FA896A92880E6ECB941E3C29778D1632D174CDF5195`；pytest-summary 473,393/`0EF7614740C515D49E9D39C2143A701ED5E869BF44E59C67DF8BC96C044A2FF5`；native-summary 582,874/`466F40959F7D1BCDCC6E70644159E13913609A336AF290207D1AEAE424E2D918`；machine-ledger 3,785,540/`4D0B71510E9ECE4A83FC2C0D39346F1029E28D9D975119EC2717C8D105B04E2F`；owner-ready 102/`548D27FC71C525FEF32613B42F5086AEA0BD4766E3FE400F564FE3F0A0A3277B`；drain 24/`00C3296A81DE6FFFBBF013D93D61DC405359F776143D5961F2EEBC29A453F626`。

S2根共1,625文件/120,337,125 bytes，恢复区累计12,878文件/806,690,181 bytes<2GiB。native observer completed=true、event_count=50,059、overflow=false、unknown_paths为空、reparse=0；所有已知命令PID均已退出，8000/8001无监听。runner/runtime/test/API入口SHA256仍分别为 `97FD9AFB074061A8DEEFD916EE3C91FED165C94EA156CAD092C4A2F75F4C4A6C`、`0A12AB1C91AAE6C4F29B1A603D34710691F63EE5918919D87C61BB0B60CDF1C8`、`5873C19C0FEF61066F40F173413C76ADC201B2094088B0EE758249EEBD44D374`、`9A3957F67F084CDD233A87D4B92C24D53DB0C4D9B66D94477B972A436BE1800A`；运行期间未修改冻结代码、产品、断言、skip或阈值。

状态迁移为 `BLOCKED + CONSUMED`：S2 `1/1` 已用，S3 `0/1` 未到达。唯一下一项只能是另行审定最小QA台账生命周期修复契约；不得把当前失败解释为性能失败，不得自动修复并重跑quality，也不得启动S3、业务服务或Step 7。

## 2026-09-18 R2 工具就绪通过与 QA 工具冻结证据

R2 只将当前工具就绪根推进到 `s1-qa-stabilization-r2`、把R1台账加入历史只读集合，并在历史失败节点的 monkeypatch 作用域内绑定临时正式根与受控 readiness 回执；生产入口仍只接受 `native-quality-08` 和真实当前凭据。固定V1 AST/入口/16选择器、V2 Ruff check/format-check、V3 strict mypy、V4 fixture/调用参数矩阵全部通过。冻结runner/runtime/test SHA256为 `97FD9AFB074061A8DEEFD916EE3C91FED165C94EA156CAD092C4A2F75F4C4A6C`、`0A12AB1C91AAE6C4F29B1A603D34710691F63EE5918919D87C61BB0B60CDF1C8`、`5873C19C0FEF61066F40F173413C76ADC201B2094088B0EE758249EEBD44D374`。

唯一 R2 入口为 `E:\\Agent\\comprehensive-cases\\15-cyber-town\\.venv\\Scripts\\python.exe -B scripts/f009_step6_qa.py --tool-readiness --root E:\\Agent\\cyber-town-f009-step6-qa\\recovery-20260905-01\\s1-qa-stabilization-r2`，cwd功能仓，外层与pytest exit 0。16个选择器展开的37个参数节点全部completed，failed/skipped/xfailed/not_run均为空，first_failure与secondary_failures为空；owned_processes_closed、port_state_restored、environment_restored、temp_path_restored、old_evidence_unchanged、report_redacted均为true，quality/performance/product_service_started均为false。

正式入口的 `read_current_readiness_receipt()` 随后只读校验成功：接受R2根、37个passed节点、五份当前产物哈希及四个当前代码指纹。该读取没有创建quality根或消费S2额度。`native-quality-08`仍不存在；PID33076、60760、65076均已退出，8000/8001无监听。R2根16文件/57,700 bytes，恢复区累计11,253文件/686,353,056 bytes<2GiB；两仓计数保持功能0/39/62/101、正式0/9/10/19。

R2固定产物：tool-readiness 5,741 bytes/SHA256 `96164A454C537B09FBFC00C2B826E7A3BE785ACA13809B695107F7B93385EF41`；pytest 8,517/`9FF337BEBC92A6D6A12B72D527C732D7227B989CAB374AA9BE41EE099E74E511`；native 5,181/`40C2E02C7D22F96AD6E73BC91BD19D9F4661A6E1FAAAAB56DBDED03741BE8070`；invocation 2,741/`521A60D0120ACB8E92AEACD1ADDCFB9BDAC5D284463D165921CB0571CC7B3E1A`；ledger 32,166/`D29449B7B02CEE9FF0F4A648EF3AD6729D89F4CF294A6BEF0F82C3FAAC45595F`；owner-ready 107/`667449C3223EF59525A6202789C3B6EEC4C6EDD1FBB5EBC15C52CF456E2EC281`；drain 24/`00C3296A81DE6FFFBBF013D93D61DC405359F776143D5961F2EEBC29A453F626`。

状态迁移为“QA工具冻结，S2已授权但未运行”：R2最小适配 `1/1`、R2工具就绪 `1/1` 均已消费；S2 `0/1`、S3 `0/1`。唯一下一项是对预登记新鲜根 `native-quality-08` 执行一次完整 fake-only quality；运行前后不得修改冻结QA代码。S2若发现产品缺陷则转独立产品修复，发现QA工具缺陷或环境问题则停止，均不得创建第二个quality批次；只有S2通过才能进入S3。

## 2026-09-18 B2 静态通过与 R1 失败证据

B2 限定修改 `scripts/f009_step6_qa.py` 与 `backend/tests/test_f009_step6_qa.py`：旧 `native-quality-07` 加入历史只读台账，新正式根为 `native-quality-08`；S2只接受该根，并在创建前读取R1的tool-readiness、invocation、pytest、native及owner五份产物，严格核对当前四文件指纹、16选择器/37参数、恢复字段和native完整性。旧tool11校验函数保留给历史契约，不再作为S2当前凭据。`native-quality-08`与R1的root/ledger已精确预登记，均未在静态阶段创建。

固定静态首次V1通过；V2只发现一处SIM300断言顺序和一处format-check单行格式，唯一B2修复只做这两项等义调整。随后V1 AST/入口/16选择器、V2 Ruff check与format-check、V3 strict mypy、V4 fixture/调用参数矩阵全部通过；37参数节点静态可解析，fixture仅monkeypatch/request/tmp_path，unresolved为空。runner/runtime/test冻结SHA256为 `00FAD0DF9379F74B21B47D877FB7BD213E3A3231889D102120DB22AF5BA9A305`、`0A12AB1C91AAE6C4F29B1A603D34710691F63EE5918919D87C61BB0B60CDF1C8`、`B46C53CB33E8BB63E9F3A611687C654AB78D11E0D98562B91F8C6A4946D3F0F0`。B2修复1/1已用；静态期间未运行pytest/quality/性能/服务。

R1准确入口为 `E:\Agent\comprehensive-cases\15-cyber-town\.venv\Scripts\python.exe -B scripts/f009_step6_qa.py --tool-readiness --root E:\Agent\cyber-town-f009-step6-qa\recovery-20260905-01\s1-qa-stabilization-r1`，cwd功能仓，唯一运行exit1。pytest只记录 `test_observer_quality_failure_report[command]` failed，failure_location为测试文件第772行；其余36参数节点未执行，boundary与identity/termination rejection均为空。tool-readiness首失败为该节点，secondary为 `step6_identity_validation_failed`，旧证据/端口/环境/临时路径恢复为true；quality/performance/product_service_started均false。

失败原因来自明确源码调用链：测试706—790行将 `require_native_quality_boundary` 替换为临时根校验后，用临时根调用 `run_quality_acceptance`，但没有替换B2新增的正式根等值检查和 `read_current_readiness_receipt`。因此入口先抛前置边界拒绝，772行的对象身份断言 `caught.value is primary` 失败。pytest摘要按脱敏合同没有保存异常文本，但失败位置与调用顺序足以证明这是B2 synthetic测试适配缺口；不是产品缺陷、性能失败或环境问题。本轮没有修改或重跑。

R1产物：tool-readiness 3,825 bytes/SHA256 `9E67586932B77C2B0B410ED0C20E1595295434219F61954E7D4D6275B6C28C02`；pytest 870/`ACDF6119727957BB14086769B910876B300528243AB4B4A9CF88576D04C621CB`；native 731/`46E3FFEC9FE36DABF93C52248CD29FDA7C0C08FF1886E79450393940A77ACAF7`；invocation 2,741/`B90EE56AEA321E4FE6A515AA85566BD3653D722D6B99DE5C00B144B672E5C2A3`；ledger 11,519/`A6F781C48029FFB3B81156BDCA0C40EEC98F973CE48037C175919DA2980D6EB7`。native因测试主失败记录为不完整验收，observer PID68152已关闭；R1共9文件/19,860 bytes。恢复区累计11,237文件/686,295,356 bytes<2GiB，8000/8001无监听，`native-quality-08`不存在，两仓计数未漂移。

状态按层停止：R1 `1/1` 已消费，S2 `0/1` 未消费，S3 `0/1` 未到达。唯一下一项只能是独立R2最小测试适配：在该synthetic测试的monkeypatch作用域内绑定临时正式根并提供受控readiness receipt替身，保持生产入口“仅新正式根+真实当前凭据”不变；随后重新执行固定静态，成功才允许一次R2重新冻结。不得复用R1、修改产品、放宽S2边界或运行quality。

## 2026-09-18 Q1 通过与 S2 前置阻塞证据

B1 只在 `scripts/f009_step6_qa.py` 增加 Ruff 要求的导入块分隔空行。固定 V1 AST/入口/14选择器、V2 Ruff check与format-check、V3 strict mypy、V4 fixture/调用参数矩阵全部通过；runner/runtime/test SHA256分别为 `485B69DDAC6786E58EE6E1970B3DDA5F6152358B42541A2B01B26AC087A505EF`、`0A12AB1C91AAE6C4F29B1A603D34710691F63EE5918919D87C61BB0B60CDF1C8`、`C550BB5A8705A0D5D5909F2ADC522EB2631A86B421A6F37D6BB6F8D9AF67B8C8`。累计机械恢复额度 `3/3` 已用。

Q1 准确入口为 `E:\Agent\comprehensive-cases\15-cyber-town\.venv\Scripts\python.exe -B scripts/f009_step6_qa.py --tool-readiness --root E:\Agent\cyber-town-f009-step6-qa\recovery-20260905-01\s1-qa-stabilization-i0`，cwd为功能仓；唯一运行 exit 0。`tool-readiness-summary.json` 为 `state=passed`、pytest exit 0，14个选择器展开的26个节点全部completed，failed/skipped/xfailed/not_run均为空；first_failure为空，secondary_failures为空。owned processes、端口、环境、临时路径全部恢复，旧证据不变、报告脱敏；quality/performance/product service started均为false。

I0 根共16文件/53,827 bytes；`tool-readiness-summary.json` 4,621 bytes/SHA256 `F54B28FAC28A8E479F0C32CBA3A57E0352B452EFF4EA380634840F57E767E971`，`pytest-summary.json` 6,498/`19792BBB5007E4F4711807324EDDCAC25E64E196A398A8EECEC4FBB332258882`，`native-summary.json` 5,179/`6F7242D5BA92D166BAED936DEAA054997D47B81AD11345A1CC2BD188041F3A65`，`invocation.json` 2,582/`FCEA7361360703B272B02369FA677AFE1091A04F403BA4468E633D731ED466F8`，`machine-ledger.md` 32,166/`FB217EF2E60578F305FED3D252A1AC98226336649CCE8AF19E009FDCDB5CFF68`。native completed=true、event_count134、overflow=false、unknown_paths=[]、reparse=0；报告写入后恢复区累计11,228文件/686,275,496 bytes<2GiB。observer PID20796及受控PID26892/61332均已关闭，8000/8001无监听。运行前后QA三文件哈希一致；两仓staged均0，功能仓tracked/untracked/total=39/62/101，正式仓=9/10/19。

S2 创建前只读调用链证据：`scripts/f009_step6_qa.py:54` 将 `NATIVE_QUALITY_ROOT` 固定为 `native-quality-07`；`run_quality_acceptance` 在2482—2486行先校验根并对该根读取tool11凭据；2613—2616行要求根属于固定集合且必须不存在。`native-quality-07` 当前已存在（2,158文件/176,150,712 bytes），不能复用。`require_current_tool_receipt` 在4023—4040行要求凭据代码指纹等于当前代码；现存 `qa-tool-contract-11/contract-summary.json` 的runner SHA256为 `ACAEA748263ED01702D679C09C0B916BF6D14AC5FC2E817FB3B21B15356336F8`，与当前冻结runner `485B69DD...` 不同。因此 S2 在资源创建前即不满足合同；未创建新 quality 根、未运行 quality，S2 `0/1` 未消费。

问题分类为 QA 工具入口/凭据接入缺陷，不是产品缺陷或性能失败。按状态机必须停止，不能借用 S1 R1/R2 根、复用 `native-quality-07`、跳过凭据校验或自动修改冻结代码。唯一下一项是另行审定一个只处理“当前凭据 + 新鲜正式 quality 根绑定”的最小恢复契约；不得混入产品优化、阈值变更、性能或 Step 7。

## 2026-09-18 S1 QA 工具稳定化停止证据

基线：功能仓 `feat/f-009-safety-cost-performance`、正式仓 `main`，共同 HEAD `1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3`，staged均0；功能仓tracked/untracked/total为39/61/100，正式仓为9/10/19。I0/R1/R2三个精确根均不存在，8000/8001无监听。39个旧machine-ledger加正式evidence的聚合SHA256为 `714C3309826B1AEEA347D9AF89392E729E1BFDFF6954A5FEC0AF778E6CD1E8FF`。

初次实现：V1 AST解析三个QA文件、14个固定选择器及入口通过。V2 Ruff check报告6项：test文件1个E501、runner 1个E501与2个B904、runtime 2个E501；format-check同时报告三文件需格式化。没有运行V3/V4/V5，没有创建根。初始失败不计修复轮。

R1：只做等义换行和显式异常链。重跑V1通过，V2 check/format全部通过；V3 strict mypy报告 `f009_step6_runtime` 顶层fallback import-not-found及 `s1_runtime` no-redef两项。没有运行V4/V5，没有创建根。R1消耗1/2。

R2：只把双分支导入改为单一 `load_s1_runtime()` 动态加载函数。重跑V1通过；V2 Ruff仅报告 `scripts/f009_step6_qa.py:3` I001（导入块未按格式分隔）。按“第二轮仍出现新的QA工具缺陷立即停止”不再补空行，V3/V4/V5未运行。R2消耗2/2。

停止前只读收尾：功能仓分支/HEAD/staged/tracked保持，untracked因批准的新支持模块由61增至62，总数101；正式仓分支/HEAD/staged及19项计数保持。I0/R1/R2仍均不存在；8000/8001无监听；旧证据聚合SHA仍为上述基线值。三个代码文件停止时SHA256分别为 runner `0A6FCC92D8A13FD025791B0C3ED249709DBAC6CB7446C683097FCBB306B5593B`、runtime `0A12AB1C91AAE6C4F29B1A603D34710691F63EE5918919D87C61BB0B60CDF1C8`、test `C550BB5A8705A0D5D5909F2ADC522EB2631A86B421A6F37D6BB6F8D9AF67B8C8`。正式evidence本节属于停止后的人工收尾更新，不计入运行期旧证据漂移。

## 2026-09-10 tool11完整工具就绪补齐

### 唯一运行结果与收尾

准确外层命令：E:/Agent/comprehensive-cases/15-cyber-town/.venv/Scripts/python.exe -B scripts/f009_step6_qa.py --tool-contract，cwd=E:/Agent/comprehensive-cases/15-cyber-town-f009。2026-09-10T15:23:07Z初始化，15:25:07Z pytest摘要、15:25:19Z contract/drain、15:25:48Z native摘要；外层/pytest exit0，136函数531参数全部passed，failed/skipped/未执行均0。完整清单、参数计数、真实子命令与10文件SHA保存在[contract-summary.json](E:/Agent/cyber-town-f009-step6-qa/recovery-20260905-01/qa-tool-contract-11/contract-summary.json)，逐条记录在[pytest-summary.json](E:/Agent/cyber-town-f009-step6-qa/recovery-20260905-01/qa-tool-contract-11/pytest-summary.json)。UV17、Godot受控回放26、原35闭环保留；未选test_observer_capacity_real_load，未追加512文件/8轮真实负载，未运行Godot产品场景或业务服务。

原迁移[control]/[observability]各有initialize→initialize_returned→first_digest→first_digest_returned→repeat_initialize→repeat_initialize_returned→repeat_digest→repeat_digest_returned八阶段。迁移4项真实import/runpy父回归全passed；子报告各精确1控制passed+1预期failed/exit1，非法scope为ValueError/invalid_storage_value、未知BLOB为TypeError/unsupported_json_value，阶段synthetic_digest，正常导入与__main__标识准确，未留原始输出，父回归脱敏哨兵断言通过。两个单文件指纹变化负例通过；新增阶段完整性与凭据拒绝在现有测试内验证。受控子失败不混入外层531计数。既有入口报告9、真实startup报告10、termination报告14及有限等待报告6共39项passed。

本批实际Python synthetic（不是FastAPI）：[False] launcher50692、business2568，父子绑定与创建时间已记录；各自retained_query_handle最终alive=false/exit_code_available=true/final_exit_code=1，natural_exit_code=null，主动收口且termination_attempted=true/错误码null。[True] launcher22896、business31432，各自保留查询句柄自然/最终码7、alive=false，未主动终止。附随Popen cleanup_report使用缓存返回码、wait_returned=false/signaled_confirmed=null，不冒充保留句柄的新确认。这些是本次退出证据，不复用历史74或tool10结果。

父observer PID9636、pytest launcher父PID10176；native completed=true/event_count5214/overflow=false/unknown_paths=[]/reparse0，外层boundary={}、identity/termination diagnostic rejections=[]，没有替身observer。收尾查无相关Python/Godot/Uvicorn进程和8000/8001监听；未处理无关进程。native真实通知只支持本批观察完整，不作为新压力负载或历史溢出根因关闭。

[独立台账及产物](E:/Agent/cyber-town-f009-step6-qa/recovery-20260905-01/qa-tool-contract-11)：ledger903239bytes/SHA E5F5D512E47D22A6762E4E9B0D6D2FC6495E021455B85BEF74BA106D3771CC87；contract41986/CE1534F29EE1E3C0669ECD9ADF304D455CCEC874455A406E0CE8895DDFF0D5E7；pytest126012/F27D440378DD2AB2EE413C09BCE19922E30852CF6CAB956CEE775CB35F0C35C4；native206220/6E0141628DF11C191D3971A1EA7F9E9EF9D56935B2E84194535253BF57EB7D47。-Force盘点530文件4713256bytes<256MiB；各层observer命名产物合计215267bytes<8MiB，台账/摘要均低于限额，无reparse。恢复11212文件686221669bytes<2GiB。旧10682文件681508413bytes元数据SHA EA16E411ECF43CA150F5DB353F7E8E7D9E096CE82BB44DD06633AE341553E2A4及38旧ledger SHA逐项不变，全部保留不删除。

运行前后100文件SHA与冻结fc8ce66ac661f695f89a7511c7e254cedaa0fb404a9119c1fc36d18d1fe473a2一致，10凭据SHA与当前文件逐项一致，两仓HEAD/branch/staged0/100及19不变。工具Python文件SHA FCC90DA3456501E815F4C0A4C50AACB5772F67563225B1FC3A1DB1FBA49FA5B9稳定。四当前文档运行期完全一致：evidence251213bytes/SHA08D83D0BD5E6F8AEDA5395E681A85653CA900EBD635E7BE668F9620901CDCEC2；task139778/2FD4B4DA80B22F27399763EC52CE4FA35751FF51AA6A930FCE48E3B2F241EA63；plan48747/D26F3E473418E16F7B16C6978A556B14E884BB0AAD546EAA6515790F99C0D179；progress709/D7A0FD860AE7380317170C9C9127CF42A6213DA0037C6DEBDC3C5B736D3F5A2B。机器只进新ledger，以下当前文档变化属于运行结束后人工收尾。

本次准备修正1/2、唯一tool11运行1/1耗尽；未用准备余量不转为运行额度。成功仅本版本/本清单工具就绪，历史quality07失败不被改写；原connectivity/observer内部原因仍独立未知。唯一下一动作：只读审定完整fake-only语义验收的条件与新额度，不直接启动。original_failure_resolved=true仍仅历史ownership/canonical，step6_complete=false，Step7未授权。本轮停止。

### 授权、准备及冻结（运行前记录）

基线887d9942c74a58e53053aa6ec25f9a456b9cbe417c39bc1226e9bb11dd4d8f57核对一致，两仓feat/f-009-safety-cost-performance/main、HEAD1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3、staged0、100/19变更；38ledger及10682文件681508413bytes资源与迁移收尾一致，无相关进程。用户明确批准两QA接入、初次准备+最多2轮范围内修正、tool11唯一531项，不追加真实通知负载/quality。新根qa-tool-contract-11新鲜，current-task43项固定精确预登记；旧tool10加入历史只读，不创建新quality根，quality07仍未恢复。动态资源复用guard操作前逐项登记。

仅两QA变化：script SHAacaea748263ed01702d679c09c0b916bf6d14ac5fc2e817fb3b21b15356336f8；test SHA1b498b80074ac0b0473004a75b9438b0b9476483a68e05405dc9d47879d91b0d；全100文件按原path+NUL+lowerSHA+LF/Ordinal算法冻结fc8ce66ac661f695f89a7511c7e254cedaa0fb404a9119c1fc36d18d1fe473a2，其余98文件不变。原454+迁移84-重叠9+两个单文件指纹负例=136函数531参数；UV17/Godot回放26/原35闭环/报告链/原两个实际synthetic最后保留，不含real_load。凭据生产/校验统一原6+迁移4文件；阶段检查复用原逻辑，并在现有命令上下文测试内精确拒绝缺参数、重复参数和缺完成标记，未额外增加参数数目。

初次实现期间两次apply_patch上下文定位失败，均未写入；原因分别为分块上下文重叠及短锚点匹配PREVIOUS前缀。改用完整行锚点后写入，后续源码块及98文件指纹复核无误；未用还原/覆盖既有成果方式处理。初次ruff format仅QA脚本格式整理。初次完整静态全0；源码就绪复核发现阶段检查可能覆盖pytest已失败时的首个错误，按范围内准备修正第1轮改为仅code==0时校验，失败仍走原报告与失败关闭路径。第1轮完整静态再次全0，修正累计1/2；尚无运行失败或重跑。

静态准确工具：E:\Agent\comprehensive-cases\15-cyber-town\.venv\Scripts\python.exe，cwd功能目录；-B -m ruff check --no-cache scripts/f009_step6_qa.py backend/tests/test_f009_step6_qa.py；-B -m ruff format --check --no-cache同两目标；-B -c内联ast.parse/literal_eval（不导入QA/业务）核对两QA、5个内嵌fixture、各所选函数的全部装饰器/静态常量/range参数及原迁移文件，136函数531参数全部解析、无unresolved。mypy：-B -m mypy --no-incremental --cache-dir=nul scripts/f009_step6_qa.py backend/tests/test_f009_step6_qa.py scripts/f009_step5_compact_preflight.py backend/tests/test_storage_migrations_v4.py；strict原配置、MYPYPATH=backend/src作用域恢复，4source无问题。两仓git --no-optional-locks diff --check均0，未跟踪QA另以源码块/指纹核对（git diff不会显示其内容）。未改产品、依赖、owner/Win32/observer/路径/等待/台账安全规则。

唯一待执行命令：在功能cwd，用上述python.exe -B scripts/f009_step6_qa.py --tool-contract。入口自身真实父observer、受保护子pytest、固定tool11台账；实际命令/清单/指纹写contract-summary，逐条结果写pytest-summary。任何意外失败/字段缺失/观察缺口/资源越界/漂移即停，无运行修复额度，不补参数、不续quality。根≤256MiB、ledger≤8MiB、observer合计≤8MiB、pytest/contract各≤1MiB，满额恢复949943869bytes<2GiB，旧证据全部保留。

## 2026-09-10 迁移摘要解码契约（历史保留）

用户批准4文件限定修正、初次准备及最多2轮范围内修正/完整静态复验、migration-digest-validation-01唯一回归；不恢复quality。基线dd83ff99f277392eab2d9b943c850f3fc01e205d0c170a92c2fbbcfd0cb8df07一致，两仓原分支/HEAD/staged0、100/19，37旧ledger与10660文件680757114bytes无漂移，新根不存在、无相关进程。root/ledger及固定初始化/子报告路径已在current-task预登记，尚未创建。

初次实现后格式整理3文件；首次完整静态：Ruff check exit1（内嵌MIGRATION_REPORT_FIXTURE单处E501），format-check exit0，AST四源码/5fixture/22函数84参数/旧454清单保留exit0，mypy exit1（run_identity_validation.extra的固定长度元组推断不能接受4项新指纹）；两仓diff --check exit0。未运行pytest或创建运行根。第1轮针对性修正仅fixture等义换行及extra显式tuple[str,...]，不改执行顺序/安全语义，随后完整复验。

第1轮完整复验：Ruff check/format、AST及两仓diff均exit0，mypy仍exit1同一extra元组长度错误。源码差异复核发现注解误加到run_startup_diagnostic的同名extra，目标run_identity_validation未改到；无运行行为变化，但补丁定位错误。第2轮撤回本轮误加注解，以完整函数上下文为锚点，仅对目标extra声明tuple[str,...]，再次完整复验；本次准备2/2，唯一运行仍0/1、新根未创建。复盘：同名局部变量不能仅凭短上下文打补丁，修复后先核对函数归属；建议作为本任务执行检查，不修改全局规则。

第2轮完整静态全部exit0：原Python E:\Agent\comprehensive-cases\15-cyber-town\.venv\Scripts\python.exe，cwd=E:\Agent\comprehensive-cases\15-cyber-town-f009，四目标scripts/f009_step6_qa.py backend/tests/test_f009_step6_qa.py scripts/f009_step5_compact_preflight.py backend/tests/test_storage_migrations_v4.py；-B -m ruff check --no-cache、-B -m ruff format --check --no-cache、-B -c仅AST四文件/5内嵌fixture/22函数84参数、-B -m mypy --no-incremental --cache-dir=nul（strict、MYPYPATH=backend/src并退出恢复），两仓git --no-optional-locks diff --check。没有模块导入/测试预跑。最后一轮修正已正确限制在run_identity_validation.extra，启动函数本轮注解误改已撤回；其余96文件字节不变、旧资源/台账不变。

新冻结887d9942c74a58e53053aa6ec25f9a456b9cbe417c39bc1226e9bb11dd4d8f57（原Ordinal path+NUL+lowerSHA+LF算法）。backend/tests/test_f009_step6_qa.py SHA fafa04e2f95f10ad7101bf4eb8fb110775faa3d164ab54cacdf82ce64fcda0f7；backend/tests/test_storage_migrations_v4.py SHA 331b83d8eee8a6bedd0f30443315cbb903edaa67f589de48ece726820be97909；scripts/f009_step5_compact_preflight.py SHA eea759ab2ac4772e5074dc4630eebb62b781feaca676fe8dd7dc1dab29f54608；scripts/f009_step6_qa.py SHA 29c825dc0da8fd404f4a0c49ecfb8582173bf570ae03de36e4cdb95cdf0a72a1。运行前源码就绪复核：新根同时进入BATCH_LIMITS/NATIVE_ROOTS/IDENTITY_VALIDATION_ROOTS并不改变tool10/quality07绑定；静态配置与当前owner分离，root/ledger先登记；本批追加四个关联源码指纹，原observer/owner/退出处理不变。固定清单见scripts的MIGRATION_DIGEST_COUNTS，22函数84参数=10批次/隔离+4真实报告+47解码边界+23原迁移基线，原[control]/[observability]最后执行；不删旧覆盖、不启动真实服务或真实负载。两个错误类×import/runpy子pytest为4个预设负例，父断言精确验证，不能把其他失败当预期。

唯一命令（尚未执行）：上述Python -B scripts/f009_step6_qa.py --migration-digest-validation；入口复用run_identity_validation/native_session，真实父observer、固定本批ledger，单次受保护pytest；原失败两参数必须分别出现initialize/first_digest/repeat_initialize/repeat_digest及返回共8个阶段。运行期四文档固定、机器只写本批，结束后核对旧台账/指纹/容量/进程。准备2/2已耗尽，定向0/1，不额外运行quality；任何运行失败立即停止。

### 唯一运行结果与收尾

2026-09-10 14:12:37Z初始化，准确入口为E:\Agent\comprehensive-cases\15-cyber-town\.venv\Scripts\python.exe -B scripts/f009_step6_qa.py --migration-digest-validation，cwd功能目录；14:13:31Z进入drain，14:13:55Z写native-summary，外层exit0、pytest-summary.exit_code=0。固定22函数84参数全部passed，失败0/skip0/未执行0。清单由MIGRATION_DIGEST_COUNTS、invocation.command及pytest-summary完整nodeid对应，未执行tool全集、真实通知负载、业务服务、Godot、quality或性能。

两原迁移参数[control]和[observability]均passed，各保留initialize→initialize_returned→first_digest→first_digest_returned→repeat_initialize→repeat_initialize_returned→repeat_digest→repeat_digest_returned八个固定阶段。原23项基线（v4原15/compact6/v9[7][8]2）全部保留通过，47解码边界及10根/owner/台账/登记回归通过。说明旧decoded_digest缺少v9三个scope的严格解码已在本次定向验证修复，不以成功回写quality07未保存的具体调用栈。

4个真实报告回归父测试全部passed。import/runpy×invalid_scope/unknown_blob各子pytest exit1、准确1passed/1预设failed；父严格检查节点/phase=call/类型/错误消息与摘要，非任意exit1。invalid_scope报告ValueError+invalid_storage_value+synthetic_digest，位置compact_preflight.py:62；unknown_blob报告TypeError+unsupported_json_value+synthetic_digest，位置json/encoder.py:180。4个子失败是受控负例（另有4个控制节点passed，不混入外层84项计数），非法值哨兵没有进入摘要/stdout/stderr；没有任意异常属性或原始栈输出。既有identity-events为空是本批没有身份查询异常，不充当迁移证据；迁移元数据在pytest及四子报告。

真实父observer PID39520 completed=true、374 events、overflow=false、unknown_paths=[]、reparse=0，外层boundary={}、identity/termination diagnostic rejections=[]；没有使用替身observer或放宽路径/进程/台账规则。本轮退出后相关Python/Godot/Uvicorn进程和8000/8001监听均无；没有处理其他进程或删除资源。

[独立批次](E:/Agent/cyber-town-f009-step6-qa/recovery-20260905-01/migration-digest-validation-01)：pytest-summary.json 19512bytes/SHA FD31D1EF6671F999D0C8E7FC941D9F27374A1CDDF7CC7D4D73FDB9390640F327；native-summary.json 7744/B7B63CC7361D7C9B15E2F39EEC5C68B23643E168463E8B558E4C56F49B055ABD；invocation.json 3847/CD1842E1770A2403E08E1DC51899F0443EE11D2D79F2F43AA0F22CE97C9D4C37；machine-ledger.md 43038/38FFAC9A77EDAA73D18E38BEA4811AFB045F8BE7470A828C3CB59FE056CE1630；四子报告位于migration-report/{import,runpy}/{invalid_scope,unknown_blob}/pytest-summary.json，各1586—1629bytes。原始过程只在新台账与产物中，正式evidence未被机器追加。

收尾-Force盘点新22文件751299bytes<32MiB，observer合计7883<8MiB，fixture/临时其他677019<8MiB，台账43038<8MiB，调用3847<64KiB、摘要19512<1MiB；恢复10682文件681508413bytes<2GiB。旧10660文件680757114bytes元数据SHA3312FF2C5F9C258442AFACF5C251C25EED462397A85866789AF704D42EC46C34与运行前一致，37旧ledger SHA逐项不变。新旧证据和synthetic SQLite全部继续保留，不删除、不建议自动回收。

运行前后冻结均887d9942c74a58e53053aa6ec25f9a456b9cbe417c39bc1226e9bb11dd4d8f57，100变更文件SHA一致；与本次起点相比仅4获批文件变化，其余96不变，两仓原分支/HEAD/staged0/100与19未变。四文档运行期大小/哈希完全一致：evidence243275bytes/SHA A57C1718E454FE9B151A7A5FEC6413FFE2B943F54E9AB752BEFF13CDBCE35D5F；task124151/2DA4767175A3692B02074B5BC1EA0F7A244CD01E69DB1FCD3E32A55C392FC18D；plan48680/4D5E471EF07CF67827259865034A85E0BB03FAEF0075B8644F03B0299AC420A6；progress949/FC24502F09784CCF8CBD0D1E9157660765C7559978B142288B06E897236664F5。上述为运行结束后的人工摘要。

累计本次准备2/2、唯一回归1/1已耗尽；运行后未修改代码/重跑或补参数。下一步仅审定当前冻结版本完整工具就绪补齐范围与新额度；不自动恢复quality。历史tool10/quality07结果保持原适用版本，original_failure_resolved=true仍仅历史ownership/canonical，原connectivity与observer溢出内部原因仍独立未知，step6_complete=false。

## 2026-09-10 tool10及条件式quality07（历史保留）

### 唯一运行结果与停止收尾

tool10：2026-09-10T13:11:08Z初始化，13:12:35Z pytest摘要，13:12:41Z drain，13:12:57Z native摘要完成；外层/pytest exit0，119函数454参数全部passed、0未执行。原35闭环、UV17、Godot回放26、真实import/runpy报告链和两实际synthetic均通过，未选真实负载。父observer53904，completed=true、event_count4881、overflow=false、unknown_paths=[]、reparse0，诊断拒绝/边界均空。False launcher15516/business34704，各自保留句柄最终码1、自然码null、主动收口；True launcher41468/business45332，各自自然/最终码7、未主动终止。相关进程均已退出。

tool后quality前：六文件凭据实际hash一致，454计数/清单、owner/ledger/外层及observer完成通过；tool前35旧ledger/7984旧文件500627406bytes元数据67A40429E7F7B32AA24E8736A4CB21DE5E1E97B58F7C85FEF7D5EF3B729AE8FF未变，四文档未变，quality根不存在、8000/8001无监听、无相关进程。依据用户明确的新独占窗口继续原条件额度，没有复跑tool或修改代码/配置。

quality07：13:14:14Z初始化，唯一--quality recovery-20260905-01/native-quality-07；前置仓库策略完成，lock、全工程ruff/mypy、schema、Godot import/unit、connectivity、dialogue-connectivity八命令exit0。connectivity记录9个passed场景，无failed/runner失败；只说明本次通过，原超时内部原因未查明。完整backend pytest（PID17028）exit1，13:23:00Z生成摘要，合计3003条结果=2869 passed/133 skipped/1 failed。失败节点backend/tests/test_storage_migrations_v4.py::test_repository_populated_upgrade_repeat_and_cli_boundary[control]，phase=call，failure_location指向已用解释器Lib/json/encoder.py:180；该源码位置为不可JSON序列化对象的TypeError分支，但摘要未保留具体对象类型或调用链，不能直接认定SQL迁移、产品或QA包装哪个有错。本轮仅定位摘要与必要源码，不修复、不复现。quality-summary completed=false/exit1/failure_code=null：既有quality.main捕获命令失败返回1，此null不表示成功。失败后剩余pytest参数与后置仓库策略未执行；报告未保存完整剩余集合，数量不猜测，也未collect-only补查。

已执行的独立语义结果：精确Godot节点test_long_term_dialogue_integration.py::test_godot_scene_fastapi_sqlite_and_fake_provider_form_a_real_local_loopback passed；test_control_evaluation_step5.py的fixture25-case维度、test_baseline_report_meets_all_step5_control_thresholds、test_same_fixture_and_key_match_in_three_fresh_python_processes均passed，非额外加跑。原test_v23_waiter_conflict_and_concurrent_prepare_have_one_owner passed；QA文件812结果均passed（包含工具安全/报告及既有负载），不把回放当成Godot实测。安全control16、retry/breaker18、SQLite control68/connection lifecycle26、space preflight11、multi_npc_adversarial25等当前已执行节点passed；完整语义仍被迁移失败阻断。133 skipped分布attribution45、budget_control53、historical projection33、dialogue_async_persistence2；对应原显式历史诊断root/开关未配置，未修改skip或启用旧批，不把skipped记作当前验证通过。

quality内唯一既有通知负载：512文件各1KiB，created_files512/completed_rounds8，observed_files512、missing_indices=[]、final_sizes_verified/drain_completed/thread_closed=true，局部event_count9327；固定262144。这是本次完整pytest内真实OS通知证据，没有独立负载加跑或旧64KiB对照。整个quality父observer PID20256，completed=true、event_count83566、overflow=false、unknown_paths=[]、reparse0；13:23:09Z drain，13:23:36Z native摘要，13:23:41Z quality摘要，外层最终exit1。没有本次observer溢出，但不能由83566事件数推导容量充分或历史溢出根因关闭。运行边界/identity/termination拒绝均空，收口无新增错误。

quality中实际synthetic False launcher33592/business30632各自保留句柄码1、自然码null、主动收口；True launcher60108/business61404各自自然/最终码7。Popen摘要的缓存退出码/未再次等待与独立句柄证据分开；这些不是业务FastAPI独立退出码。tool父/子、quality父/pytest和上述已知synthetic PID结束；当前无相关进程及8000/8001监听，未操作无关进程。

产物：[tool10](E:/Agent/cyber-town-f009-step6-qa/recovery-20260905-01/qa-tool-contract-10) contract-summary36292bytes/SHA13994B79B855FD840DCF96451D433B5F6210DFED9C115538802A3C783AEA906F；pytest108390/B0B38428FFB2EFA5BED7A3065C168FFC9E161E200D62C0ECFE097BE30142096A；native201760/06A56E5440BBBB22F7E2ECA54F470076FD8B02C3FB72E61C151B9ADB7776F1B1；ledger873088/F835FE03B37CF6E807560BE929811CD8C1A67BADB88C4780EE3B2CB0F578CDE8。[quality07](E:/Agent/cyber-town-f009-step6-qa/recovery-20260905-01/native-quality-07) quality-summary7448/5DC6CCE787ACDEEB03604661C2514E2BE65045469C806116247109CEEA81714A；pytest703723/36737995FAD7CC367360C55B3F4CD9D0FE2C98E259D8A7ED5EC13B87DA40E055；native858313/46625A7BE80B209E7621A762300BEE295A0452AEB6FB81083AE8836653D42889；ledger5536420/DDAA6D2CBE51985BBFD664232F7136EFB467B07FF8F69703DAF98D44B58D6881。准确命令、结果、身份metadata和清单保存在独立产物；全量报告读取曾因工具输出截断未解析，随后只读提取明确字段，未重写证据或运行代码。

收尾全量-Force盘点含隐藏父目录内容：tool10 518文件3978996bytes/observer201888bytes；quality07 2158文件176150712bytes/observer858439bytes。两个ledger及固定摘要均低于限额，两批新增180129708bytes，恢复总10660文件680757114bytes<2GiB。quality前全部8502文件504606402bytes（含tool10）元数据406FE7EBEB639F1A0ECE46590BDC12605053A840E3C5FCF856E1862D372E194B不变，36旧ledger hash均不变；全部新旧证据继续保留，未删除/复用。普通目录盘点未含隐藏父目录的临时计数不作最终容量证据。

冻结dd83ff99f277392eab2d9b943c850f3fc01e205d0c170a92c2fbbcfd0cb8df07及全部100文件hash运行前后相同，两仓原branch/HEAD/staged0/100与19变化不变。tool及quality运行期四文档完全未变：evidence231925bytes/SHAABC7B6B586230168BCA5A6805D9D12DE6E17029E9B92455B2296C3C461AAB20D；task107765/628EFD2F675541F68270B81C5E151FFF68E92092C43C89DF28AEC766518466FC；plan50047/12DEA4DA557EDDB2CA80BE0278C73E37BEF0A66C2DF54CB6E6F5DE7134676B68；progress985/950D8E241D72DF8EE221D6267553CCC6717874B05EDA48A04EAA09EB409D912D。机器仅追加各批ledger，本节为运行结束后人工摘要。

准备修正0/2，tool10 1/1、quality07 1/1均耗尽；成功工具证据与失败产品验收分开，旧额度保留。唯一下一动作：只读诊断迁移用例的JSON序列化失败，核对具体调用与现有取证缺口；不直接修复、补跑或开启新quality。original_failure_resolved=true仍仅历史ownership/canonical；原connectivity/observer溢出内部原因独立未知；step6_complete=false，性能及Step7未执行。本轮已停止。

### 准备与冻结（本批运行前记录）

基线e383e469e71825cccdac5527089d1d9c2c6a28a709389dec5964eb26009b31c4核对一致；新冻结dd83ff99f277392eab2d9b943c850f3fc01e205d0c170a92c2fbbcfd0cb8df07，script SHA1d75caab961296c937686e78f72ff9c995b52b3acfb1a8faae5ce5d1a5358468，test SHA6deaf8551595ed724e037630500dd0a1f05a8e1b86e40e743f382096349ada91。仅两活动根同时切tool10/quality07、tool09/quality06加入历史、对应精确配置/旧根拒绝断言适配；逐字节与保存源码的限定替换比较完全一致，其余98文件未变。119函数454参数及所有运行逻辑不变，产品不改。首次元数据审计超过命令初始返回窗口，未就绪JSON读取为空；随后延长只读等待取得完整结果，无代码/测试失败或资源写入。

首次完整静态全部exit0：原Python E:\Agent\comprehensive-cases\15-cyber-town\.venv\Scripts\python.exe，cwd=E:\Agent\comprehensive-cases\15-cyber-town-f009；-B -m ruff check --no-cache scripts/f009_step6_qa.py backend/tests/test_f009_step6_qa.py；同目标-B -m ruff format --check --no-cache；-B -m mypy --no-incremental --cache-dir=nul同两目标，strict/MYPYPATH=backend/src并退出恢复；-B -c仅AST两QA/4内嵌fixture/119函数454参数精确计数及原35/119覆盖保留；两仓diff --check通过。准备修正0/2，运行未开始，不迁移历史额度。

两仓HEAD1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3，功能feat/f-009-safety-cost-performance/正式main，staged0，100/19既有变化。35旧ledger与7984旧资源500627406bytes及元数据同前轮，父链无reparse、两新根不存在、无相关进程/监听。用户已确认本轮8000/8001独占窗口，tool后/quality前仍复核，不处理其他项目或进程。

本轮唯一tool命令为上述Python -B scripts/f009_step6_qa.py --tool-contract；全部454及外层observer/owner/六文件凭据通过后才一次-B scripts/f009_step6_qa.py --quality recovery-20260905-01/native-quality-07。完整命令/关键节点映射见当前plan，保持原quality与受保护缓存语义，完整pytest内精确Godot/evaluator/三新进程不额外补跑；既有512文件8轮负载仅quality内一次。tool、quality均失败即停，不修复重跑或补跑；性能0，Step7未授权，原ownership/canonical关闭与原connectivity/溢出内部原因独立。

精确预登记见current-task：[tool10](E:/Agent/cyber-town-f009-step6-qa/recovery-20260905-01/qa-tool-contract-10)≤256MiB，[quality07](E:/Agent/cyber-town-f009-step6-qa/recovery-20260905-01/native-quality-07)≤1GiB；各ledger≤8MiB，pytest/contract或quality≤1MiB，observer合计≤8MiB及更小原限额。两批满额总1842804686bytes<2GiB；每项资源先登记后操作，所有证据保留，机器只写各批ledger，运行期四文档保持。

## 2026-09-10 tool09完整工具就绪（当前）

### 唯一运行结果与收尾

2026-09-10T12:48:28Z初始化，12:49:52Z受保护pytest摘要，12:50:00Z父drain，12:50:19Z native摘要完成；唯一--tool-contract外层/pytest exit0，119函数454参数全部passed、0failed/0未执行。原418+新增36完全匹配冻结清单；原35失败闭环、UV17、Godot受控回放26、根/owner/台账与容量契约全部通过。identity/termination诊断拒绝=[]、boundary_violations={}；未选择真实负载节点，未创建其负载目录，无新增512文件8轮。真实构造5次ReadDirectoryChangesW均固定262144，同一缓冲/递归/0x1F与线程关闭断言通过；受控大块/畸形不是OS压力结果。

原入口报告9参数（含observation_error/reader_error）及10叠加收口负例全部通过。正常import/runpy真实报告链身份10、终止14、有限等待6全部通过；受控子pytest失败由父断言核验，不能作为外层意外失败忽略。实际Python synthetic两分支本批最后执行：[False] launcher12720/business38264，父子归属及初始绑定成立，分别通过保留查询句柄确认不再alive、final_exit_code=1且available=true；natural_exit_code=null，terminated_by_diagnostic/termination_attempted=true，无终止错误。[True] launcher33460/business10968，各自保留句柄final/natural_exit_code=7、available=true，不再alive，无主动终止尝试。cleanup_report中Popen已缓存1/7，未再次调用terminate/wait、signaled_confirmed=null；不得把这个Popen摘要替代独立保留句柄证据。上述是本批真实本地synthetic，不是FastAPI或历史74项证据。

父observer PID50576（受保护pytest PID9192），owner根为tool09，completed=true、event_count4870、overflow=false、unknown_paths=[]、reparse0；drain marker存在，外层结束exit0。六文件凭据hash与当前文件逐一相同，聚合e383e469e71825cccdac5527089d1d9c2c6a28a709389dec5964eb26009b31c4运行前后不变；两仓branch/HEAD/staged0/100与19变化及其余98文件未漂移。50576/9192/12720/38264/33460/10968均不存在，无F009相关进程或8000/8001监听，未额外终止进程。

根[qa-tool-contract-09](E:/Agent/cyber-town-f009-step6-qa/recovery-20260905-01/qa-tool-contract-09)固定产物：contract-summary.json 36292bytes/SHA1E8029BB42990BA308D4D14BA379279FBFE8A05806CFA305BCD958C9BCE43A80；pytest-summary.json 108388/C107EA37CA04D93D997B0B2607F61BF3D11E8BBEFB7532687B45C3DCB00EA770；native-summary.json 201541/9C3377FB6F1468BAB376413B4354262F5F454B6FCE3F03060A69285A6963A502；machine-ledger.md 871945/D9DA53EDD0F1716D292F0C34755E32A1CAEF5A792B7F38528A72A75A460C4527。详细节点/参数、命令/cwd/六文件hash、独立退出metadata与最终inventory均在这些产物，不重复保存完整机器过程。

新批518文件3977379bytes，observer三文件201669bytes，非根固定产物2759085bytes，各固定/批次限额均合规。34旧台账SHA未变，7466旧资源496650027bytes元数据AB0B768395E7E557658719FA114D5F8B9F55A3BDD090D158A05AF1861D975AA3不变；恢复总7984文件500627406bytes<2GiB。全部继续保留，未删除/复用旧批。

运行期四文档byte/SHA完全不变：evidence224860/E97F041B35C136C698584B7597115276BC43D7C05A99311F2E6CEAE073455E70；current-task90478/9F32DA9FBFF5EDC8DC372482F7E4716F7D2A6B4C77093D064A2D49F1C81B3775；plan48799/74D8F20711DBB74EAD93FFC2811490088670D545EF689B55113271C3B1ABF040；progress962/56F1DA75ADD658D4FCC82D4FBCFD95AE17A4E693AAC1A162D5956ACDB0E3CD8E。机器仅追加新ledger；本节为运行完成后的人工收尾。任务卡篇幅新增精确预登记，证据新增本批结论索引，没有重复归档。

准备修正0/2、工具唯一1/1已消耗；历史额度保留，剩余准备额度不构成后续运行许可。仅说明当前接入版本454项完整工具基线就绪，不证明完整产品验收或原溢出因果消除；持续高负载/原quality06内部溢出原因及原connectivity原因仍未知。唯一下一动作：只读审定当前冻结完整fake-only语义验收的条件与新额度，不直接运行。FastAPI/Godot/connectivity/quality/性能及Step7均未运行；step6_complete=false，本轮停止。

### 准备与冻结（本批运行前记录）

基线00decc20c2ec5d4757407ab69c2545856f58d532ec6accdf718514b773f893a9一致；新冻结e383e469e71825cccdac5527089d1d9c2c6a28a709389dec5964eb26009b31c4。script SHAff5e18391db7833129076d264c17f873009e2848dacbf49e2c019f69cedae2ce，test SHAc84881843fe7594b746645583b12fc7ada3810025854383f1ab0bd2ce5a143dd。仅TOOL_CONTRACT_ROOT tool08→09、tool08加入历史、11节点/36参数入清单及测试直接断言适配；与保存源码逐项比较，除这些明确修改外两QA完全相同（LF不改写），其余98文件无漂移。两仓原branch/HEAD/staged0/100与19变化不变。

首次完整静态全exit0：原Python E:\Agent\comprehensive-cases\15-cyber-town\.venv\Scripts\python.exe，cwd=E:\Agent\comprehensive-cases\15-cyber-town-f009；-B -m ruff check --no-cache scripts/f009_step6_qa.py backend/tests/test_f009_step6_qa.py；同目标-B -m ruff format --check --no-cache；-B -m mypy --no-incremental --cache-dir=nul同两目标，原strict/MYPYPATH=backend/src（退出恢复）；-B -c仅AST两QA/4内嵌fixture/119函数454参数逐项计数、原119定向/35失败链/容量非负载覆盖保留；两仓diff --check通过。辅助读取曾定位不存在的backend/pyproject.toml，纠正为根pyproject.toml；补丁提交因重复文件段/段落顺序两次被工具原子拒绝、未修改文件，重组后一次应用；这些未执行静态或运行，不记失败后修正轮次。本次初次静态通过、准备修正0/2，唯一定向0/1，旧额度不重置。

准确清单为源码TOOL_CONTRACT_TESTS/COUNTS：原108函数418参数完整保留，加入test_observer_capacity_batch_contract(1)、test_observer_failure_batch_contract(1)、test_observer_capacity_real_constructor(1)、test_observer_capacity_large_notification_block(4)、test_observer_receive_failure_contract(6)、test_observer_failure_fields(1)、test_observer_finish_failure_contract(10)、test_observer_session_failure_restoration(2)、test_observer_quality_failure_report(5)、test_observer_command_failure_order(3)、test_observer_actual_command_evidence(2)。去重119/454；test_observer_capacity_real_load未选择，历史512文件8轮不计本批，实际Python synthetic False/True最后。无新增测试框架、负载、pytest增量记录、产品/权限/observer/进程逻辑变化。

唯一执行原Python -B scripts/f009_step6_qa.py --tool-contract；准确受保护子命令、全部清单/参数和六文件hash由新contract-summary.json记录。真实父observer并行保护，须同时外层exit0、pytest454passed/诊断无拒绝、native completed/drain/关闭、owner/指纹、旧台账与运行期文档不变；摘要passed不能代替退出后的observer完成证据。失败即停、不修复重跑、不补跑。

新根[qa-tool-contract-09](E:/Agent/cyber-town-f009-step6-qa/recovery-20260905-01/qa-tool-contract-09)当前不存在，current-task精确登记已就位；≤256MiB/ledger8MiB/pytest及contract各1MiB/observer合计8MiB及既有较小限额，恢复≤2GiB。34旧ledger及7466旧文件496650027bytes与基线完全一致，无相关进程/监听、父链无reparse。机器只写新ledger，运行期四文档冻结，所有产物保留，不删除。历史quality06已耗尽，本轮所有业务/quality/性能额度0；成功失败均停止。

## 2026-09-10 固定256KiB容量适配（当前）

### 唯一运行结果与收尾

2026-09-10T12:11:20Z初始化，12:12:28Z父drain，12:12:41Z最终inventory；冻结命令仅执行一次，外层/受保护pytest exit0。31函数112参数全部passed，0failed/0未执行；原35完整保留并通过，新增配置/owner、构造、大块/畸形、台账、sidecar、UV17、Godot受控重命名26及真实通知回归全部有本批直接结果，不是实际Godot或产品验收。boundary_violations={}，identity/termination诊断拒绝=[]。

真实构造：5次ReadDirectoryChangesW提交均262144字节、递归True、filter0x1F、同一缓冲对象，原API真实委派，线程已关闭。受控合法通知块135168bytes（512个记录）完整解析，截断/偏移及原零字节/API失败负例拒绝；这是内存回放，不声称OS实际一次交付135168bytes。

最后一次真实负载：512个file-0000.bin至file-0511.bin全部先登记，实际创建512/各1024bytes、完成8轮定长改写；局部真实observer观察到全部512必见路径，missing_indices=[]、event_count9291、drain_completed=true、final_sizes_verified=true、thread_closed=true。父observer PID19904，completed=true、event_count13258、overflow=false、unknown_paths=[]、reparse0。两层事件计数不同且不等于写调用数，不据此推导丢失率或原quality容量余量。未运行旧64KiB对照，不把本次未溢出说成原根因关闭。

原35中实际Python命令回归：interrupt Popen PID7008，受控检查注入overflow后由既有收口取得缓存码2，source=held_popen_returncode_after_cleanup，cleanup_attempted=true/cleanup_error=null；complete PID18928，正常缓存码7/source=held_popen_returncode，无收口尝试。双管道错误均[]。这是本批launcher/Popen证据，不是FastAPI或独立business句柄退出证据，不借用历史False/True。

证据根[observer-capacity-validation-01](E:/Agent/cyber-town-f009-step6-qa/recovery-20260905-01/observer-capacity-validation-01)：invocation.json 4183bytes/SHA0380FD2D3B0A29322E521FC1E633043D51026900CA50706CF459AB121E1DBAB5；pytest-summary.json 25580/0A21C764985B630C343BB3F7184B2671AE8542559848D7044668DD530D13BF49；native-summary.json 233866/52CB4309E4C1FAF6B8310611C658F94FEA37732FB4A00B20FE1C69EB6EB0B898；machine-ledger.md 927859/DC62825E204AC6B5AFFA422831FB86E50B2086D6702C69355AD42E97A65C2641。局部负载和构造证据在pytest metadata，最终文件清单在native摘要。identity-events.jsonl按既有入口为空，不含本次不存在的身份查询异常。

收尾：冻结00decc20c2ec5d4757407ab69c2545856f58d532ec6accdf718514b773f893a9及全部100文件hash前后相同，两仓原分支/HEAD/staged0/100与19状态不变。33旧台账SHA及6865旧文件494906482bytes、元数据0F25098B96F9BA759B8E2C7582E08A0803A3233631207BED4E502A5C9D4CC769保持。新批601文件1743545bytes，fixture/负载/子报告551433bytes，其中512负载文件524288bytes；observer三文件234006bytes、ledger927859bytes，均低于各类别/32MiB限额。恢复7466文件496650027bytes，小于2GiB。PID19904/7008/18928不存在，无F009相关进程或8000/8001监听，未额外处理进程或删除资源。

运行期四文档完全不变，机器仅进入新ledger：evidence217223bytes/SHA8F0139149CDE27E1A56DAB79E6D2706E6D43A5422CFCB8FF901B213B4255BEA6；task81415/F929D21769BF9A3B4F70A3B215820E8F4B0E5FF7E32864EB736615D75F39892E；plan49132/0EAE3F43453A7A5A3C13907506CED8CE2AD37346CE9AB8897D43248F862DF5B5；progress981/187FCD0A92AA0B9705E3F82BB903D9BD9C34DDB1FDF4F67139946442B2AC2307。本节为结束后人工摘要，无重复归档。

本次准备修正2/2、唯一定向1/1耗尽，历史额度保留。结论仅“固定256KiB容量适配在本次有界负载下验证通过”；完整工具就绪与产品验收未执行，原quality06溢出内部原因、持续高负载/不同事件突发下的容量余量仍未知。不继续扩大缓冲或叠加负载，不自动恢复quality。唯一下一动作：审定当前冻结版本的完整工具就绪补齐范围与新额度，仍不直接运行quality。step6_complete=false、Step7未授权，original_failure_resolved=true仅历史ownership/canonical；性能未运行。本轮停止。

### 准备与运行前冻结（历史过程）

当前完整静态与源码就绪通过，唯一运行0/1待执行；只修改两QA的固定容量、新根/现有入口接入与直接测试，不改变产品、其他observer/进程安全或pytest增量记录。基线9341d9fd…aabd258一致；新冻结00decc20c2ec5d4757407ab69c2545856f58d532ec6accdf718514b773f893a9，script SHA9f3af6a21528a855fcad53af433052f7bc835a6c840431c04fbcfd1f6df26400，test SHA68389e1daf2d416cdac077c24e686fef8b3d9463d9537066d1425592fc7d9721。内存中反向去除本轮新增常量/根/清单/分派、容量替换和新增测试后，分别精确还原原两文件SHA1edc1d…a3301/51cd54…df5b；其余98文件、两仓分支/HEAD/staged0/100与19变化不变。

准备记录：初次辅助AST计数对含bytes乘法表达式的参数列表literal_eval失败ValueError；修正为只计AST List/Tuple元素数，不求值、不导入执行模块，按修正1/2记账。随后完整静态仅Ruff N802（测试代理直接使用Win32方法名）失败，format/AST/mypy/diff均通过；修正2将代理小写方法由__getattr__显式映射原API名，调用参数/真实委派不变；完整静态全部exit0。准备2/2耗尽，运行失败不可修复。未运行collect-only或测试探针。

静态准确环境：E:\Agent\comprehensive-cases\15-cyber-town\.venv\Scripts\python.exe，cwd=E:\Agent\comprehensive-cases\15-cyber-town-f009；-B -m ruff check --no-cache scripts/f009_step6_qa.py backend/tests/test_f009_step6_qa.py；同两目标-B -m ruff format --check --no-cache；-B -m mypy --no-incremental --cache-dir=nul同两目标，原strict/MYPYPATH=backend/src；-B -c仅AST两QA/4内嵌fixture/原108函数418参数、119清单保留及新31函数112参数逐项计数；两仓git --no-optional-locks diff --check、tracked/untracked/空白/指纹。两文件format命令实际无改动。

准确冻结清单（31函数112参数，按顺序；原35参数全部保留）：
test_observer_capacity_batch_contract(1)、test_qa_contract_context_requires_current_live_owner(5)、test_qa_contract_ledger_registration_precedes_operation(1)、test_observer_failure_batch_contract(1)、test_qa_batch_binding_cannot_switch_active_ledger(1)、test_qa_batch_child_keeps_ledger_when_native_permission_is_revoked(1)、test_qa_batch_prior_ledgers_are_read_only(1)、test_observer_capacity_real_constructor(1)、test_observer_capacity_large_notification_block(4)、test_qa_native_notification_corruption_fails_closed(3)、test_qa_native_observer_overflow_is_a_hard_failure(1)、test_observer_receive_failure_contract(6)、test_observer_failure_fields(1)、test_observer_finish_failure_contract(10)、test_observer_session_failure_restoration(2)、test_observer_quality_failure_report(5)、test_observer_command_failure_order(3)、test_qa_ledger_native_inventory_after_real_observer(1)、test_observer_actual_command_evidence(2)、test_qa_contract_ledger_half_line_is_retained_until_complete(1)、test_qa_contract_ledger_write_failure_does_not_grant_registration(1)、test_qa_contract_ledger_concurrent_writers_visible_to_real_observer(1)、test_qa_repeat_registration_reconciles_only_registered_retired_sqlite_sidecar(2)、test_qa_retired_sqlite_registration_rejects_incomplete_prior_registration(2)、test_qa_late_sqlite_notification_requires_registered_absent_sidecar(8)、test_qa_real_sqlite_journal_lifecycles_keep_guarded_notifications(1)、test_qa_real_notification_rename_checks_preregistered_paths(1)、test_qa_uv_retired_notification_requires_observed_removal_and_stable_anchor(17)、test_qa_godot_rename_notification_strictly_revalidates_paths_and_identity(26)、test_qa_canonical_failure_preserves_original_notification(1)、test_observer_capacity_real_load(1)。

唯一执行命令：上述Python -B scripts/f009_step6_qa.py --observer-capacity-validation。复用run_identity_validation/真实父observer/独立台账/受保护子pytest，不签发业务或完整工具就绪凭据。实际构造代理仅记录固定262144/True/0x1F及缓冲对象身份，真实API、线程、drain、close不替换；受控大块解析记录与真实OS通知分开。最后真实負载512个预登记file-0000.bin至file-0511.bin，各1KiB，创建后8轮定长改写，无重试或删除；实际目录pytest/test_observer_capacity_real_lo0。state以有限pytest metadata保留创建数/完成轮次/必见路径计数与缺失索引、最终尺寸/drain/关闭结果，不保存原始数据。

新根observer-capacity-validation-01尚不存在，精确bootstrap和子资源登记见current-task，≤32MiB/ledger8MiB/observer8MiB/fixture8MiB/summary1MiB/invocation64KiB。E:固定NTFS，父链无reparse，无相关进程/监听。33旧台账不变，6865旧文件494906482bytes、元数据0F25098B96F9BA759B8E2C7582E08A0803A3233631207BED4E502A5C9D4CC769；恢复总≤2GiB。运行期四文档固定，机器只写新ledger，新旧所有资源保留。本次成功也不关闭原溢出因果，不恢复quality/性能/Step7，step6_complete=false。

## 2026-09-10 observer失败证据闭环（历史保留）

### 唯一运行与收尾

2026-09-10T11:32:54Z初始化，11:33:21Z drain，11:33:32Z最终inventory；仅执行下述冻结命令一次，外层与受保护pytest exit0。13函数35参数全部passed，0failed/0未执行，boundary_violations={}、identity/termination报告拒绝均[]。受控zero/read/wait/rearm/record/ledger与drain/close/write/capacity等负例均按精确断言通过；不能把这些内层受控失败写成真实父observer溢出。父observer PID71280、completed=true、event_count244、overflow=false、unknown_paths=[]、reparse=0，ready/drain/native报告均存在；父会话成功不替代内层失败schema验证。

真实本地Python两例：interrupt持有Popen PID7188，受控检查注入step6_native_watch_overflow，state=interrupted，cleanup_attempted=true、cleanup_error=null，exit_code=2，来源held_popen_returncode_after_cleanup；这是主动收口后的launcher码，不是自然退出或独立business查询句柄证据。complete持有Popen PID23936，state=completed、exit_code=7、来源held_popen_returncode，无收口尝试。两例pipe_close_errors=[]；最终pytest metadata保存上述有限字段。未运行FastAPI或历史StartupProcess False/True，不借用历史74/119/418项的独立退出证据。identity-events.jsonl为空是本集合不产生身份查询诊断的既有输出，不表示缺失上述Popen证据。

证据根[observer-failure-evidence-validation-01](E:/Agent/cyber-town-f009-step6-qa/recovery-20260905-01/observer-failure-evidence-validation-01)：invocation.json 2336bytes/SHA01B55A211EEC963F9035D00855729856189CF08704F6386FDCF11F07569C8F2C；pytest-summary.json 7933/F97F9CAC7088367750F6C5860D9E0591A9EABFDC9E5F2B67C992B53E7C6B2F49；native-summary.json 8603/85D1495A0DBE3E54514EB3CBB459A56DE6A356CF67BA973A9F1833FB70C4A221；machine-ledger.md 57115/291CE9645D6BF6448E7476DAA3EAE0774404AAF27A3A973603E57DA90A4E1A8E。内层失败native/quality摘要保留在各pytest case目录，不冒充产品验收。observer三文件合计8751bytes；新批24文件84328bytes，小于32MiB及全部固定/类别限额。恢复6865文件494906482bytes，小于2GiB。

代码聚合及两QA SHA与下述冻结完全一致，其余98文件和两仓分支/HEAD/staged0/100与19状态无漂移。32旧台账SHA全同；6841旧文件494822154bytes，元数据162914D938D10A56FEB45064DC1AB714D466D7CBEA84F443BB8E352D284CE3EC不变。运行后PID71280/7188/23936均不存在，未发现相关F009进程或8000/8001监听，无额外终止/删除。四文档运行前后（人工收尾编辑前）完全不变：evidence208774bytes/SHA C6800CEB64C1802FDD596DB34F47C31CB8C59DF37B402D444127F87EAF4A44C2；task75827/FAA885A2C7A0898F6EC00E24B543AA6AB97C1A1AB489627BF48351BAC27586DA；plan45685/8D290CCF2913DF4B560F0DB1D1E0D3BFDC11808DE35EE8491D79BCDA9741DE31；progress948/5A54E2000983B2EA9F206EC586463629F0CE1917823A8B93F287D2350DBB7647。机器记录仅写新独立台账；本节为运行后人工摘要。

本次准备2/2、唯一synthetic1/1耗尽，全部旧额度/结果保留。成功仅指失败证据闭环通过；原溢出的内部因果仍未知，中断pytest历史缺失数量不能补回，没有加入增量记录。本轮结束，不自动恢复quality。唯一下一动作：审定observer溢出风险的最小处理方案与后续验证边界，不直接新增quality或探针。

### 实现与运行前冻结记录

实现范围仅scripts/f009_step6_qa.py及backend/tests/test_f009_step6_qa.py。记录有限接收阶段/API/即时错误码/字节数/时间和台账写入结果；native失败后不伪装成功inventory，保留主异常及独立drain/close/报告失败；run_observed记录已启动/中断命令与持有Popen缓存退出证据，quality最终摘要在native收口后写入。报告单文件及原批次/恢复总容量写前检查保留。未改64KiB缓冲、通知过滤、重新arm顺序、等待/终止权限、owner、路径守卫或台账隔离；未加入pytest增量结果，不运行真实quality命令。

准备诊断：初次完整静态Ruff失败SIM300/SIM117/I001三项，其余format/AST/mypy/diff通过。准备修正1处理三项及有限台账写入错误码，完整静态全通过。源码就绪发现observer关闭后的报告写入须显式保护原容量，准备修正2补齐两类报告写前容量核对、quality摘要提前登记及2个容量负例；完整静态全部exit0。准备2/2耗尽，不再新增修正。

准确静态环境：E:\Agent\comprehensive-cases\15-cyber-town\.venv\Scripts\python.exe，cwd=E:\Agent\comprehensive-cases\15-cyber-town-f009；-B -m ruff check --no-cache scripts/f009_step6_qa.py backend/tests/test_f009_step6_qa.py；同目标-B -m ruff format --check --no-cache；-B -m mypy --no-incremental --cache-dir=nul同两目标（原strict、MYPYPATH=backend/src）；-B -c仅AST两QA/4内嵌fixture/选择器与全部参数计数；两仓git --no-optional-locks diff --check及tracked/untracked指纹核对。未导入执行QA或产品。旧108函数418参数及119定向清单保留但不重跑。

冻结聚合9341d9fd1a5ea71346ef439db696c5bd543aa8797f8cff9595cbf9e15aabd258；script SHA1edc1d4bb13673ea55ce0e4dde2cdc695cc2ae83ee5e57203b6edd21719a3301，test SHA51cd54ad802062b2141052291c6e5306dcdaeb34be1534e7bffa430acd06df5b。相对629a5a…410ce仅两QA改变，其余98文件未变；两仓原分支/HEAD/staged0/100与19状态一致。32旧台账不变，6841旧文件494822154bytes，旧元数据SHA162914D938D10A56FEB45064DC1AB714D466D7CBEA84F443BB8E352D284CE3EC。新根不存在，父链无reparse，无相关进程/8000或8001监听。资源逐项预登记见current-task，唯一根≤32MiB、恢复总≤2GiB。

固定13函数35参数（按执行顺序）：test_observer_failure_batch_contract(1)、test_qa_batch_binding_cannot_switch_active_ledger(1)、test_qa_batch_child_keeps_ledger_when_native_permission_is_revoked(1)、test_qa_batch_prior_ledgers_are_read_only(1)、test_qa_native_observer_overflow_is_a_hard_failure(1)、test_observer_receive_failure_contract(6)、test_observer_failure_fields(1)、test_observer_finish_failure_contract(10)、test_observer_session_failure_restoration(2)、test_observer_quality_failure_report(5)、test_observer_command_failure_order(3)、test_qa_ledger_native_inventory_after_real_observer(1)、test_observer_actual_command_evidence(2)。内部受控API/报告失败须由精确断言核验；实际Python中断及exit7最后，不是FastAPI或历史False/True重跑。外层真实父observer始终保护，不用替身冒充其通过。

唯一待运行命令：上述Python -B scripts/f009_step6_qa.py --observer-failure-validation，cwd同上。根observer-failure-evidence-validation-01；固定machine-ledger.md、invocation.json、pytest-summary.json、identity-events.jsonl及native三产物。运行期四当前文档不变，机器只进独立台账；任何意外失败即停，不修复重跑、不补跑。本次不签发产品/启动就绪凭据，成功也不证明溢出原因消除。

## 2026-09-10 恢复原quality06唯一语义验收

### 唯一运行失败与收尾（人工摘要）

2026-09-10T10:40:45Z开始初始化、10:51:19Z失败收口，原命令仅执行一次，外层exit1。lock、Ruff、mypy、schema、Godot import/unit、connectivity、dialogue-connectivity八项exit0，已完成命令boundary_codes/error_classes均空。connectivity九场景有通过标记、无failed/runner failure marker，本次未出现原监听超时，但不提供历史超时的因果解释。完整backend pytest已启动，观察溢出中断后根pytest-summary.json未生成；不能恢复总收集/通过/失败/skip/未执行数量，也不能由资源存在或受控子pytest失败摘要推导父节点通过。精确Godot本地回环、25-case evaluator、三个fresh-process digest、安全/预算成本/重试/SQLite空间/对抗及原故障回归的本批最终结果均缺完整节点证据；不写成未收集或通过。后置repository policy未取得完成记录。性能复验未执行。

直接错误链（本次工具输出保留）：scripts/f009_step6_qa.py:2269 run_observed → :2037 watcher.check → :1569 RuntimeError(step6_native_watch_overflow)；native_session :1896 watcher.close → :1612 check再次抛出同码。源码显示close先于:1897 inventory和:1905 native-summary写入；当前仅ready存在，父drain/native-summary均缺失。因此不能报告completed=true、完整event_count或unknown_paths为空，也不能以八项命令无boundary code排除全程边界问题。溢出的内部触发原因尚未诊断。run_observed异常通路调用既有stop_owned_tree并关闭双管道；收尾CIM未发现F009相关进程，8000/8001无监听，owner49664已不存在。未额外终止其他进程；pytest子进程独立退出码未保留，不能用外层1代填。

证据根[native-quality-06](E:/Agent/cyber-town-f009-step6-qa/recovery-20260905-01/native-quality-06)：quality-summary.json 4073bytes/SHA EC6C6396CD8F4BA9269F31943ED841C3B348CE2986234A22EF55C8F7CAC8EA52，exit_code=1，仅八项完成命令；machine-ledger.md 3817010bytes/SHA DAA2E74CB61352633F974761D41A2C4CADB704FCEC4B88DA204C56AEB1609D99；native-monitor-ready.json 102bytes/SHA 2F1A312C62E674BE4004232C252ED5E9F42B7818A82827103018CFE18CDB05A7，owner49664。嵌套受控fixture/报告全部保留，不冒充完整pytest或真实observer最终结果。未新建事后报告批次或补跑。

冻结运行前后均629a5a56599ebbe64a6b06a313e544341f36fb92e8e41b6853e0165f226410ce，两QA及其余98既有变化无漂移；两仓分支/HEAD/staged0/100与19状态保持。31旧ledger SHA全同；5569旧文件360935289bytes，旧资源元数据CEAC9A15326EF3A2CEB1EC76B6EC8279332BCD65E1418BBF5FC14A48A921316D不变。新1272文件133886865bytes（小于1GiB），台账小于8MiB；恢复共6841文件494822154bytes（小于2GiB）。这些事后文件核对不能补足运行期observer事件缺口。

运行前/后人工收尾编辑前四文档完全相同：evidence201309bytes/SHA029AFF72E4CF504F704B9595D8DDD53AB18F4B9BE048CF62DFD13B74FB47C498；task71132/B9817C57D6C0A24AF03DB088A8DA13495AF77C40C3D8C731AA40947B18CFB6D4；plan42850/4E25B98DA8CA0D50C5185B0BCF360BDA555B38115ABCFE1FDC8413D461215CEC；progress796/CA1354DCBB1570C87BED490E29903357E66DE11CD4AC41D43CC21F1F9A83B276。机器登记只进入新固定ledger；本节为运行结束后的人工摘要，不改写旧记录。

quality06原一次额度已耗尽；准备2/2、tool08 1/1及全部旧失败照实保留。唯一下一动作：只读审定observer overflow触发条件和异常收口报告缺口，区分通知丢失与工具状态影响，不预设原因，不扩大缓冲/权限或叠加探针，不直接开新quality。无论原因如何，本轮不修复、不重跑，不执行性能或Step7。

明确授权恢复原0/1，不新增编号或额度，用户确认8000/8001独占窗口继续有效。基线629a5a56599ebbe64a6b06a313e544341f36fb92e8e41b6853e0165f226410ce与两仓Git/HEAD1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3/feature与main/staged0/100与19变化一致。31旧台账、5569文件360935289bytes，元数据CEAC9A15326EF3A2CEB1EC76B6EC8279332BCD65E1418BBF5FC14A48A921316D；quality06不存在、父链无reparse、bootstrap根和ledger准确两条（1GiB/8MiB）预登记有效，无相关进程/8000/8001监听。

tool08 contract passed=true、418参数/六文件hash/owner65736与native completed=true一致，无overflow/unknown/reparse或边界拒绝；关键SHA保持上一节记录。本轮不改代码、不重跑工具或静态，不安装依赖。原工具环境和历史native probe能力证据只读保留。唯一命令：E:\Agent\comprehensive-cases\15-cyber-town\.venv\Scripts\python.exe -B scripts/f009_step6_qa.py --quality recovery-20260905-01/native-quality-06；cwd=E:\Agent\comprehensive-cases\15-cyber-town-f009。完整9命令/关键pytest节点映射见implementation-plan，原完整quality缓存与安全规则不变。资源/子类别预登记沿current-task，固定台账machine-ledger.md，不写旧批或向正式evidence追加机器过程；运行期四文档保持不变。运行失败即停止，不修复重跑、不补跑剩余项；性能/Step7无授权。

## 2026-09-10 入口fixture适配与tool08

### tool08唯一运行与收尾

2026-09-10T10:25:21Z初始化，10:27:06Z drain，10:27:29Z最终inventory；外层/受保护pytest exit0，108函数418参数全部passed，0failed/0未执行，contract passed=true。原entry_reporting9（含launcher_error/both_error/observation_error/reader_error）、cleanup10、completion3、evidence3与新增6全部通过；真实身份import/runpy10、终止14、等待6报告均通过；UV17/Godot受控回放26通过。原launcher_error现在验证真实wait控制流的精确超时错误，非直接放行码5；叠加失败保持最终异常对象与独立API错误事件，正常等待退出和未知码分别报告。新增受控组合不是实际Win32错误5或原connectivity自然复现，未运行真实FastAPI/Godot/connectivity/quality/性能。

本轮实际Python synthetic False：launcher12736(parent39940,created100ns134335096191185160)、business51164(parent12736,created134335096191940453)，均initial_binding且final_state_source=retained_query_handle，各自final_alive=false/final_exit_code=1/available=true；termination_attempted=true、terminated_by_diagnostic=true、termination_error_code=null、natural_exit_code=null。本轮True：launcher64072(parent39940,created134335096196958365)、business61672(parent64072,created134335096197304177)，各自保留查询句柄final_alive=false/final_exit_code=7/available=true、natural_exit_code=7；无终止尝试，terminated_by_diagnostic=false。Popen后备报告独立保留缓存码1/7，termination_requested=false/wait_returned=false/signaled_confirmed=null，不替代查询句柄证明。实际两分支未出现码5，不关闭原因未知的历史失败。

证据根[qa-tool-contract-08](E:/Agent/cyber-town-f009-step6-qa/recovery-20260905-01/qa-tool-contract-08)：contract-summary.json 33540bytes SHA B1812A16FB90772162AF9F84443210DF0CA58939240A3738199A00B8C1F985F8（准确命令/108选择器/六文件hash/owner65736）；pytest-summary.json 100626/25E0D5DC67120A2683272DF9FD13E6BDDA124BCC3B3B74466249C6AD606641D4；machine-ledger.md 826381/29BCD2D55FC1DFD7478CDA79A5925DA85AAEBCC00BE3C43801ED0D5EE4C69D82；native-summary.json 196218/9D39F971233F0A43ADF85D0981ED67FF2A6E90F8E0A3E3AEECE812916995F7D9。真实父observer65736，event_count4577、completed=true、overflow=false、unknown_paths=[]、reparse0；boundary={}、identity/termination诊断拒绝均[]。ready104+drain24+native196218合计196346bytes。

收口：聚合629a5a56599ebbe64a6b06a313e544341f36fb92e8e41b6853e0165f226410ce运行前后稳定，两仓Git/staged0及100/19既有变化不变。30旧台账SHA全同，5067旧文件元数据775406BE3E2C31BF289D4AF002E6480CF8759EAD7D1D5B7EA0709E75E4A98612保持。新502文件3906180bytes，恢复5569文件360935289bytes，各限额未超。四文档运行期完全不变：evidence196060bytes/A99782346E05F003CC58D2FC076B2DD6589D97601823F96239279F2032F48750；task71148/9B6522F2E82472BB91E5E52F328D2E25CD4C0F6D80F74B163111A255D25A2BD1；plan41141/14009EA9DF83BAFAC88DBA20D30DD57549A1F7A1374CFB581D91624100F2D441；progress826/9C20CD2DB491B53DA0E330826C56E8D80A482CFC51D5EA677E4481618368D434。机器仅写本批固定台账，此段为收尾人工摘要。65736/39940/12736/51164/64072/61672均不存在，无F009相关进程及8000/8001监听，没有额外终止或删除。

历史额度保留；准备累计2/2（本轮消耗剩余1轮）、tool08 1/1耗尽。quality06 0/1保持暂停，根未创建；性能/Step7无授权。成功仅表述本轮入口fixture修复和完整工具就绪通过，不等于完整语义验收。唯一下一动作是审定当前冻结版本是否恢复原quality06一次，不自动运行或新增启动诊断。

用户明确批准审定的局部适配、剩余准备1轮与tool08唯一一次；成功也不恢复quality06。基线547fd2c0d91eb5e5333327e2639dbad1d9af08171d015e5d061a1f7a2ce624e8/两仓Git/staged0/100与19变化一致，30旧台账、5067文件357029109bytes，元数据775406BE3E2C31BF289D4AF002E6480CF8759EAD7D1D5B7EA0709E75E4A98612；tool08不存在、父链无reparse、无相关进程或监听。资源/初始化预登记见current-task；不覆盖或删除旧证据。

修改：QA脚本仅tool08精确根、tool07只读历史、一个新增工具选择器及计数；反向去除四处配置变化SHA精确还原7abb31a5f01226dbded2c5819f7e9e8bf38a629605c1d4ab685e2c89920e9af1，运行/Win32/权限/等待/owner/observer逻辑不变。测试仅入口helper/新6case及root历史断言：实例EntryAPI复用真实wait方法与5000参数，在自身kernel模拟信号/超时/失败；返回5事件、最终stop错误、释放结果与退出报告分别断言。原25入口参数保留，launcher_error仍为超时拒绝；叠加错误保持既有优先级、错误对象及独立事件，wait/close/双管道/释放次数和替身恢复验证保留。新增等待中退出/等待前退出/等待失败/码未知/观察错误后launcher退出/business错误后launcher退出，不运行真实FastAPI或Godot。

完整静态：E:\Agent\comprehensive-cases\15-cyber-town\.venv\Scripts\python.exe，cwd功能worktree；-B -m ruff check --no-cache scripts/f009_step6_qa.py backend/tests/test_f009_step6_qa.py；同目标-B -m ruff format --check --no-cache；-B -m mypy --no-incremental --cache-dir=nul同两目标（原strict，MYPYPATH=backend/src）；-B -c仅AST两QA/4内嵌fixture/108函数参数化计数418/原119保留；两仓git --no-optional-locks diff --check及tracked/untracked指纹检查。初次全部exit0；源码就绪发现入口工厂替身会遮蔽新增wait的真实类型引用，保存规范导入类型于局部且增加恢复断言，消耗剩余准备轮次（累计2/2），完整静态再次全部exit0，无未解析参数。未导入执行QA/业务，尚无测试运行。

新冻结629a5a56599ebbe64a6b06a313e544341f36fb92e8e41b6853e0165f226410ce；scriptSHA acbb7bdf0ad84cacc73a9891123b51fa5c6f2724b643b14f36e0c744695d6943，testSHA4cb2bad40669d57044fbe3e621569ba9231e09dcf5580a2826a9a5c898a3fc48；其余98文件、Git、30旧台账与5067资源元数据无漂移。唯一运行命令：上述Python -B scripts/f009_step6_qa.py --tool-contract，当前精确根qa-tool-contract-08，原真实父observer、固定台账/owner/受保护pytest；固定108函数418参数，原报告链/119项及FalseTrue最后。运行期四文档不改，详细结果仅进入本批contract/pytest/native-summary和独立ledger；无quality06、业务启动或性能额度。

## 2026-09-10 tool07与条件式quality06

### tool07运行失败与停止（本轮最终）

固定107函数412参数，2026-09-10T09:57:47Z初始化；09:58:32Z drain，09:58:51Z最终inventory。外层与受保护pytest exit1，255passed/1failed（实际完成256参数，156未执行），失败节点backend/tests/test_f009_step6_qa.py::test_startup_entry_reporting[launcher_error]、phase=call、failure_location=test第916行、metadata=[]。entry前5参数health/health_failed/timeout/early_exit/business_error通过；both_error/observation_error/reader_error及后续真实import/runpy报告、旧14终止报告、新6等待报告和实际Python False/True均未执行。UV17、Godot受控回放26通过；不等于精确Godot回环或产品启动。quality06未创建，FastAPI/connectivity/完整quality/性能未运行。

最小源码解释：_startup_entry_case的terminate对launcher返回受控5且不更新alive；现有StartupProcess.stop保留launcher/5的有限等待路径，随后调用原保留句柄wait。StartupAPIStub.wait第916行仍assert not alive，父fixture又统一期待StartupTerminationError，因此发生替身契约不一致。此次不是实际TerminateProcess错误5，不能归因自然退出竞态/权限，也不是原connectivity复现。复盘：独立termination fixture已适配但入口共享fixture消费方仍遗漏；下一项只审定入口相关参数的等待/状态/最终异常与报告适配，保留安全负例，不修改运行逻辑或增探针。本轮未实施修复或重跑。

证据根[qa-tool-contract-07](E:/Agent/cyber-town-f009-step6-qa/recovery-20260905-01/qa-tool-contract-07)：contract-summary.json 31065bytes SHA A4F50F94EA423292D2DC348D209B26E4BAA9A50444E82B0F04A1753042F265B1（passed=false、准确命令/107选择器/六文件hash/owner41380）；pytest-summary.json 55122/814391521C6E4046D3AF5EA9C84BBFC9C0F83E31377BCBB2C175130C76E39836；machine-ledger.md 377275/1580CB958E08E608F3AB975B7BF34D0B99019DD7F5DB880530F92857DE173F3D；native-summary.json 91314/421420B6A9A44791F818D2C600908BC2DE0BB600C6A31418AADFF0F8E01509F6。ready104+drain24+native91314=91442bytes。真实父observer41380，event_count2325，completed=false（测试失败）、overflow=false、unknown_paths=[]、reparse0；boundary={}、identity/termination诊断拒绝均[]。drain已生成并完成最终inventory，不把completed=false写成门禁通过。

收口核对：冻结547fd2c0d91eb5e5333327e2639dbad1d9af08171d015e5d061a1f7a2ce624e8/全部100文件hash与运行前一致，两仓Git状态不变。29旧台账SHA全同，4885旧文件元数据43639D6C973BAEFC4C708F2F63E3E415591D15D3E63E682D098F133A23E40834一致；新182文件770502bytes，恢复5067文件357029109bytes，低于256MiB/8MiB/2GiB等限额。observer41380及相关F009进程均无残留，8000/8001空闲，未另行终止或删除资源。四文档运行期不变：evidence189616bytes/D897D14F53C3D59FA806874F6D0C8B7146EA42A371A7E946AC01C4ED43F0C378，task67931/0F00C961B3BD977D84E13D8688EB6D1F4AA0503FE6845A1E6B6E9C261C0E84FF，plan39534/6F69784683ECB8BBA7777678B41150D74EBDB7925114B15950C4564DBE155609，progress870/C8B49CA461ED70E217B28C9849AA502AE6ADE4054513208995DC8354721DC771。此段为运行后人工摘要，机器未追加正式evidence。

累计：历史额度不变；本次初次静态辅助脚本失败、准备修正1/2通过、tool07 1/1耗尽、quality06 0/1因就绪失败暂停。准备剩余1轮不授权运行失败后修复。全部新旧资源保留；唯一下一动作是审定上述入口fixture适配及新工具验证额度，不自动使用quality06，也不将独占窗口结束视为允许其他项目重启。

用户明确批准最小接入、初次准备及最多2轮准备修正/静态复验、tool07一次与条件式quality06一次，并确认8000/8001跨项目独占。基线61ba167b6f363635946d341c1804f2e023719eb3c343e96d689b5b5ce218f476及两仓Git一致；29旧台账、4885文件356258607bytes，元数据聚合43639D6C973BAEFC4C708F2F63E3E415591D15D3E63E682D098F133A23E40834；两个根不存在、父链安全、无相关进程/监听。预登记仅四当前文档，本轮不复制归档/旧台账。

修改仅两QA：tool07/quality06精确根、旧tool06/quality05历史源与关联断言、原358参数合并最新119项中缺失54参数，107函数412参数，实际False/True最后。反向去除本轮精确差异后两文件SHA均还原基线1963f2dbd19e4a066696a24894a0b7538e297f1ea6f88c65570c0bbf5a32733b和f1ff230cadef303acbbf16b98773a4295d4a9797680c12eeb42ed3abf9dbfd51；运行/权限/owner/等待/守卫/observer/产品逻辑未变，其余98文件SHA及Git状态不变。

静态准确环境：E:\Agent\comprehensive-cases\15-cyber-town\.venv\Scripts\python.exe；cwd=功能worktree；-B -m ruff check --no-cache scripts/f009_step6_qa.py backend/tests/test_f009_step6_qa.py；同目标-B -m ruff format --check --no-cache；-B -m mypy --no-incremental --cache-dir=nul同两目标，MYPYPATH=backend/src/原strict；-B -c仅AST读取两QA/4内嵌fixture/固定选择器及107函数的全部参数化计数，不导入QA/业务；两仓git --no-optional-locks diff --check及tracked/untracked SHA/空白检查。初次Ruff/format/mypy/diff均exit0，辅助AST因LAUNCHER_EXIT_COUNTS使用短名而误按完整nodeid索引，KeyError；仅核对脚本修正前缀后记准备修正1/2，完整清单再次全exit0，AST107/412、119保留、未解析参数0。没有测试运行或无变更碰运气重跑。

运行前新聚合547fd2c0d91eb5e5333327e2639dbad1d9af08171d015e5d061a1f7a2ce624e8；scriptSHA7abb31a5f01226dbded2c5819f7e9e8bf38a629605c1d4ab685e2c89920e9af1，testSHA21f2ce590a64ad02608d5a232adf23cf3beb1d3f7c79fe521685ae59305c5596。命令冻结：上述Python -B scripts/f009_step6_qa.py --tool-contract；条件满足后上述Python -B scripts/f009_step6_qa.py --quality recovery-20260905-01/native-quality-06。运行期四文档不改，机器进入各自machine-ledger.md；正式结果、参数清单/六文件指纹和真实observer以各批contract/quality/pytest/native-summary为证据，不用本段准备结果冒充通过。资源/子类别/初始化顺序见current-task，完整语义节点映射见implementation-plan；运行失败即停止，准备剩余额度不可用于重跑。

## 2026-09-10 单处换行恢复与02定向

用户批准单处E501等义换行、一次完整静态及条件式原02唯一119项，历史准备2/2不重置。基线9e33e66000998b1b6e636e869924bb212663be65d6c12f6d2a5e00eae9e16778/两仓Git/100既有变化与28台账、4817文件355844493bytes核对一致，旧01关键hash及此前4787元数据与原证据相同。仅test_f009_step6_qa.py中三引号fixture的构造调用1行拆3行，无其他实现变化；新测试hash f1ff230cadef303acbbf16b98773a4295d4a9797680c12eeb42ed3abf9dbfd51，script仍1963f2dbd19e4a066696a24894a0b7538e297f1ea6f88c65570c0bbf5a32733b。

一次完整静态全部exit0：E:\Agent\comprehensive-cases\15-cyber-town\.venv\Scripts\python.exe，cwd=E:\Agent\comprehensive-cases\15-cyber-town-f009；-B -m ruff check --no-cache 两QA，-B -m ruff format --check --no-cache 两QA，-B -m mypy --no-incremental --cache-dir=nul 两QA（MYPYPATH=backend/src、原strict）；-B -c AST两QA/4fixture、22函数119参数（原14报告+新6）、空白检查，换行前后fixture AST相同、按实际LF还原测试精确匹配6120f4471873161f0c683407f754754aa7d08853afae8cd703f5c489ab7568fb、script hash不变；两仓git --no-optional-locks diff --check。未导入QA/业务，无缩小目标实验。

源码就绪复核沿用原固定台账/owner/真实父observer，report fixture的显式合成异常与真实控制流失败有独立标记，原14、新6及最后实际False/True顺序不变。新冻结61ba167b6f363635946d341c1804f2e023719eb3c343e96d689b5b5ce218f476，其他99文件未变、旧资源元数据不变，无相关进程/8000/8001。02不存在且父链安全，原逐项预登记有效；固定32MiB/ledger8MiB等限额不变。唯一待执行命令为上述Python -B scripts/f009_step6_qa.py --launcher-exit-contract-validation，当前根launcher-exit-contract-validation-02；本次静态1/1通过、原02定向0/1，不授权后续业务或完整quality。

### 02唯一119项运行与收口

上述冻结命令于2026-09-10T09:34:25Z初始化，09:35:09Z完成drain，09:35:17Z最终inventory；外层runner及受保护pytest均exit0，固定22函数119参数全部通过（0失败、0未执行）。原call-import及14终止报告、新6等待报告、10身份正常import/runpy通路全过；canonical/伪造异常/非法字段/限额/等待保护覆盖保留。父回归严格校验子pytest受控失败的节点、阶段、退出结果、诊断及固定fixture_contract，未将任意exit1判通过。

报告证据区分：call/setup类在stop正常完成并取得替身final7后明确标记origin=synthetic_report_injection；原码5事件与注入异常均保留。state_failure/wait_timeout/wait_failed/exit_code_unknown标记origin=control_flow、stop_completed=false，并分别核验原状态错误、两类等待错误或退出观察缺失；wait_result分别null/258/4294967295/0，无伪造最终码，原终止事件仍一条。cleanup_failure保留独立PermissionError errno5且最终异常不再冒充原终止异常。以上为受控替身/报告链证据，不是Win32错误5自然重现。

实际Python synthetic[False]：business57144（parent22520、created100ns134335065028557862）与launcher22520（parent测试进程73216、created134335065028451771）均从自己的retained_query_handle取得final_alive=false/final_exit_code=1/available=true，termination_attempted=true、terminated_by_diagnostic=true、termination_error_code=null、natural_exit_code=null。实际[True]：business57920（parent49416、created134335065031776276）与launcher49416（parent73216、created134335065031653353）均final_alive=false/final_exit_code=7/available=true，natural_exit_code=7，termination_attempted=false、terminated_by_diagnostic=false。各身份均initial_binding；原查询句柄未用Popen码代填。Popen最终后备报告在两分支均已取得码且termination_requested=false/wait_returned=false/signaled_confirmed=null，独立保留其未知字段。实际两分支此次未出现码5，不能凭通过关闭历史码5因果或原connectivity。

机器证据根[launcher-exit-contract-validation-02](E:/Agent/cyber-town-f009-step6-qa/recovery-20260905-01/launcher-exit-contract-validation-02)：invocation.json 3134bytes SHA AE77231467C9820D1E8B2070AE20C3B9DE539D2BF1397EF0E5D124E60E1036EA含精确命令/23选择器/三文件hash/owner46748/fake-only/product_start_attempts0；pytest-summary.json 38048bytes/E1D288AD06F3C7C0550EE6DBF6F046EC2D2D74E424BFC511D1131408FCEC1D38；termination-events.jsonl 9773bytes/904CF809FF908F21C75FD62EB5A657AD6FBA22C75046BD230DA83F7ABC96BC0B；machine-ledger.md 115078bytes/82981BCC87557D495DDB79CF6E51D23B41BD7C5A28CAA98E12D2B2FF19DDB8B8；native-summary.json 24196bytes/3B37CC00CA4AAC635CF0680F47D76EACA6C00373B7D012CDAD911CF31D5A8E8E。真实父observer46748、event_count563、completed=true/overflow=false/unknown_paths=[]/reparse0；boundary={}，identity/termination拒绝表均空。ready121+drain24+native24196合计24341bytes。无FastAPI/Godot/connectivity/quality/性能运行。

运行前后聚合61ba167b6f363635946d341c1804f2e023719eb3c343e96d689b5b5ce218f476一致，两仓Git不变。旧28台账SHA全同，旧4817文件元数据聚合95E13EBF92307CE2BB8212A03AC2741D698F4361EB8860CF4FE3E2256D840C0E不变；新68文件414114bytes（必要子资源223740bytes），恢复4885文件356258607bytes，全部低于既有限额。四文档运行期均不变：evidence182525bytes/55C386AEB9F6AC8D21F4C7020C0B47F922EA94127175E154B3A2D9F1E192A7AA；task61375/0D237281E59706BC46DF1906A182B0ACBCFE834E854E1EC2CDFAF35D0427FAE2；plan37070/7E7AC49FC34C920EA6C23474DA150D8F4F887ED55935E201B46409A492A73F61；progress1027/84CA401A81E7482409E1B380EACA7B8B8F9A7A229C9AA5B85EA878DDB1DA788F。本段为运行结束后人工摘要，机器只追加02台账。只读核对46748/73216/22520/57144/49416/57920均已不存在，无F009相关进程及8000/8001监听，没有额外终止或删除。

额度收尾：历史准备2/2、01定向1/1及旧失败保留；本次静态恢复1/1、02定向1/1已用，全部证据留存。停止于本轮定向完成，唯一下一动作：审定当前冻结版本恢复完整fake-only语义验收的工具就绪条件与新额度，不自动运行或再开独立启动诊断。 不把本轮通过当完整工具就绪凭据，不自动恢复旧验收额度。

## 2026-09-10 报告fixture关联适配与02静态停止

用户批准既定范围、剩余准备及02一次119项。接续3f7cf34b7eda3a70c8cfeb7357039a000e3ff0a58ead0a23e90d8b32a05c2d31，两仓HEAD/branch/staged、100既有变化、28台账/4817文件355844493bytes一致；旧01ledger/pytest/native SHA与上段原记录相同，旧4787文件元数据5DC28868DB1527CD8D1D0A152DF91FFAAD48336520DE2EB2EB8E36BF1C1A1D09一致。02不存在、父链无reparse、无相关进程或8000/8001监听。02资源已在任务卡预登记，未创建。

仅两QA：script当前根切换02、定向选择器及计数新增6项；测试fixture支持私有状态模型及原5000ms wait方法，核验一次终止/等待和句柄关闭；成功stop后核验final7与natural未知，再显式注入报告异常。状态失败/等待超时/等待失败/未知退出码由原stop控制流抛精确RuntimeError，原码5事件独立保留。父回归核验固定fixture_contract、精确异常和cleanup优先级，forged/invalid不变。原14报告参数保留，新6参数独立函数共用fixture/父校验；共22函数119参数，未改其他旧工具计数、进程逻辑、权限、owner、路径、observer或报告器。

第2轮命令均用E:\Agent\comprehensive-cases\15-cyber-town\.venv\Scripts\python.exe、cwd功能目录。准备-B -m ruff format --no-cache仅测试文件exit0且未改变；-B -m ruff check --no-cache 两QA exit1，仅test_f009_step6_qa.py:2943的fixture异常构造语句102字符E501。-B -m ruff format --check --no-cache 两QA exit0；-B -m mypy --no-incremental --cache-dir=nul 两QA（MYPYPATH=backend/src、原strict）exit0；两仓git --no-optional-locks diff --check exit0。准备累计2/2已耗尽，失败后未继续改代码或重跑。

AST辅助-B -c已经完成两QA及4个既有fixture语法解析、原14+新6/总119/22函数与空白断言；最后27行的配置还原指纹断言exit1，因误用CRLF移除新增行，而实际脚本全部LF。随后只读PowerShell内存字节对照，撤去根切换/新增选择器/计数3处配置精确还原基线script afda1f48929ea0df35982d7acecdfbafd2f644e4493d9f7fcb349c82dcfe945e；运行逻辑未改，不是未知漂移。不得将该辅助命令整体写成exit0。首个接续工具调用因跨轮存储失效缺cmd被拒绝，随后按已记录算法重建只读审计；无资源写入或测试运行。收尾文档补丁首次因同一路径重复update被工具拒绝、未写入，改为每文件单次update，不触及QA。

保存点9e33e66000998b1b6e636e869924bb212663be65d6c12f6d2a5e00eae9e16778；script1963f2dbd19e4a066696a24894a0b7538e297f1ea6f88c65570c0bbf5a32733b，test6120f4471873161f0c683407f754754aa7d08853afae8cd703f5c489ab7568fb。其他98文件/Git不变，28台账SHA和4817文件元数据与本轮起点相同，总355844493bytes。02和其台账仍不存在，定向0/1未消耗，无新observer或实际进程退出证据；evidence仅人工更新，没有机器追加。

复盘与唯一下一动作：formatter不处理三引号中的Python源码，外层format-check不能替代fixture行宽检查。本次漏两字符换行，按额度停止；仅申请该构造语句等义拆行、完整静态复验（辅助还原按实际LF），全部通过才恢复原02一次119项。不新增批次、不重跑旧01，不恢复业务/quality/性能或Step7。

## 2026-09-09 launcher有限退出等待准备

仅两QA：已绑定launcher码5的即时未signaled路径进入原一次5000ms等待，不增加终止/权限/查询，不改变business控制流或Popen后备；失败终止的自然退出归因保持未知。新增12参数直接契约与精确根、保留原安全/报告及实际False/True，固定21函数113参数，LAUNCHER_EXIT_TESTS/COUNTS逐参数门禁。旧tool06及此前错误原因保留。

初次静态：Ruff check exit1（一处E501）、format-check exit1（三处等义格式）；mypy exit0、两仓diff --check exit0。第1轮仅格式补丁后完整静态全部exit0：原解释器E:\Agent\comprehensive-cases\15-cyber-town\.venv\Scripts\python.exe，cwd功能目录；-B -m ruff check --no-cache及-B -m ruff format --check --no-cache，两QA；-B -m mypy --no-incremental --cache-dir=nul，两QA，MYPYPATH=backend/src、原strict；-B -c源码AST解析两QA及4个fixture、21函数113参数、两QA空白检查；两仓git --no-optional-locks diff --check。未导入QA/业务。准备1/2、定向0/1。

基线3f2c5f0d0a6e3b8c37016b15a6dce06db892ae9e6149619905953160ff637ce7→冻结3f7cf34b7eda3a70c8cfeb7357039a000e3ff0a58ead0a23e90d8b32a05c2d31；脚本afda1f48929ea0df35982d7acecdfbafd2f644e4493d9f7fcb349c82dcfe945e，测试2624518a2ef65fae92d1fc3288771401912b4026fd895e6b0b1d8e4af832fbc8。其他98文件、旧27台账/4787文件355691113bytes完全一致，两仓分支/HEAD/staged不变，无相关进程/8000或8001监听。新根launcher-exit-contract-validation-01不存在、父链无reparse，精确登记见任务卡；唯一运行命令为上述Python -B scripts/f009_step6_qa.py --launcher-exit-contract-validation。该结果不作为启动就绪凭据。

### launcher唯一运行与停止

2026-09-09T13:46:43Z初始化，13:47:03Z失败收口，13:47:10Z最终inventory；外层runner及受保护pytest均exit1。固定21函数113参数，实际98项（97passed/1failed）、后15项未执行。新根/owner/ledger等4项和新增12项有限等待契约、Popen原4路、身份正常import/runpy真实报告10项通过。终止真实报告14项的首项test_termination_real_pytest_report_path[call-import]失败；其余13项及实际Python synthetic[False]/[True]未执行。新增delayed/exited的7为受控替身值，不是实际进程退出码；原码5事件保持、natural未知的断言通过。历史实际子进程退出证据不得冒充本轮。

直接失败链：外层测试3027行访问failed[termination_observations]，子pytest确有control通过/expected_failure失败、exit1、无边界/字段拒绝，但子失败定位本批termination-report/import/call/test_termination_report_fixture.py:33，即原API.wait抛AssertionError(unexpected_wait)。源码TERMINATION_REPORT_FIXTURE:2888仍假定launcher码5不进入wait；known_error期待StartupTerminationError，故在record(startup_termination_observation)之前被不匹配异常打断。不是报告器已采集后丢字段，也不是新Win32故障；本轮没有同步该真实通路fixture，是关联适配遗漏，不能把偶然子exit1视为受控负例成功。剩余修正额度不用于运行后修复/补跑。

机器根[launcher-exit-contract-validation-01](E:/Agent/cyber-town-f009-step6-qa/recovery-20260905-01/launcher-exit-contract-validation-01)：invocation.json含准确22选择器/命令/cwd/三文件hash/固定ledger/observer52140/product_start_attempts=0；pytest-summary.json 28880bytes SHA256 F872FD4955F9CA35387EDF4546B80A8C9F0D1C80C2718A8BEFD7467526EFB9CB；termination-events.jsonl 8582bytes/8263CF494AFE306FFE61CA7EBA10AD56237502BE0259D496D756DDAFFB8E7EDB；machine-ledger.md 58707bytes/D35317B3BDE4D318876DEE0A45B76987CEE21B2E0DEDCF8686FD2097AFAAFD2C；native-summary.json 10637bytes/AB5F6E251C86625285E5D04ABA82168CC01A425A12B105FD157714F44F3A8EE4。父observer52140/event_count271/overflow=false/unknown=[]/reparse0，boundary={}及两类诊断拒绝表空；ready121+drain24+native10637合计10782bytes，completed=false对应验证失败。运行后observer及F009相关进程均无残留，8000/8001空闲，无额外终止或业务运行。

运行前后聚合3f7cf34b7eda3a70c8cfeb7357039a000e3ff0a58ead0a23e90d8b32a05c2d31一致，两仓branch/HEAD/staged不变。旧27ledger SHA一致；旧4787文件元数据聚合5DC28868DB1527CD8D1D0A152DF91FFAAD48336520DE2EB2EB8E36BF1C1A1D09不变。新30文件153380bytes（子资源43386bytes），恢复4817文件355844493bytes，均低于上限。正式evidence运行前后均173501bytes/SHA2373B5EC066CBDAC422AC2E2A6779527A9BBD1B53FB111A6B84E9670E475CB55；task58855/4A8B89B958B45E4613244260D07BBA509F654091FD9141F64B52EA1FED0FF300、plan32947/E1AC6F32BD98E8312BDC999CDB464ED680EB3BA4F2085FC80A4287C5F026E104、progress1115/A52CF774B2597DB1446221A1980EE3BEF2627E4B247281B3A4309CF1C749340E亦未变。机器记录仅独立台账，本段为运行结束后的人工摘要。准备修正1/2，定向1/1耗尽，不重跑、不删除、不恢复业务或quality。

最小下一动作待批准：适配TERMINATION_REPORT_FIXTURE的wait与状态模型，分离原API失败事件和最终异常的报告断言，保留14个原参数及真实import/runpy通路；通过受控等待结果验证而不把任意子exit1视作成功。需要另行批准新鲜定向资源/一次额度，未登记、未创建。复盘：直接替身已覆盖新契约，但真实报告fixture仍残留旧即时失败假设；后续准备须对同一stop调用的直接替身和报告fixture一并审查。本次不更新全局规则，不再叠加探针。

## 2026-09-09 显式摘要限额与tool06准备

基线eb4ab0ac6a4e35dc9057cdc634f97a8ff06078714f96ae35c87637b049716b6f、两仓HEAD1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3/feature feat/f-009-safety-cost-performance与正式main/staged均0；100既有变化、26台账/4357资源352085970bytes核对无漂移，无相关进程和8000/8001监听。新tool06核实不存在/完整父链无reparse；精确预登记见current-task。旧根全保留，未创建新quality。

初次准备：仅两QA修改显式限额/确定LF、根纯配置函数、固定contract写入前限额、工具根06和旧tool05历史、原330覆盖加28参数。静态原解释器为正式.venv/Scripts/python.exe，cwd功能目录：-B -m ruff check --no-cache 两QA exit0；format --check --no-cache exit1，仅新增边界测试字符串引号格式；-B -m mypy --no-incremental --cache-dir=nul 两QA（MYPYPATH=backend/src，原strict配置）exit0；两仓git diff --check exit0。AST两源码/4fixture已解析，新增静态参数计数器对包含算术表达式的参数元组误用literal_eval而ValueError（非QA导入或测试失败）；修正为只取AST Tuple/List的elts长度，不求值、不执行模块。首次精确格式补丁因转义文本未匹配而未写入，随后以原字面转义匹配完成；无语义变化。以上纳入第1轮准备修正（1/2），tool06仍0/1，运行仅一次且失败即停。

第1轮复验：上述Ruff check/format、mypy、两仓diff --check全部exit0；AST两源码+4fixture、98函数358参数、100changed文件及Python空白检查exit0。源码就绪核验保留原330项，增加28项；根限额矩阵只读配置不写旧根，实际pytest子进程在tool06下验证import/runpy正常/超限，正式pytest调用显式1MiB及工具contract固定写入前1MiB，LF保证序列化UTF-8与文件字节一致。没有路径/owner/observer或进程语义变化。新冻结3f2c5f0d0a6e3b8c37016b15a6dce06db892ae9e6149619905953160ff637ce7；脚本73259e06c4813f4b7608d508bf79881d2ad70804f2127328cfd057e0e56e519f，测试b0119ccc1641f3f47534acbfaf24ce06c972ec1e7cab73206369da2f694e866e。其余98文件/旧台账与资源不变。工具唯一命令：E:\Agent\comprehensive-cases\15-cyber-town\.venv\Scripts\python.exe -B scripts/f009_step6_qa.py --tool-contract；cwd功能目录，新精确root=qa-tool-contract-06，真实父observer及受保护子pytest，当前待执行、额度0/1。没有quality或业务后续条件授权。

### tool06唯一运行与停止

上述冻结命令于2026-09-09T13:20:39Z初始化，13:21:48Z失败收口，13:21:57Z写最终inventory；外层runner与受保护pytest均exit1。固定98函数358参数中实际357项：356passed/1failed，只有test_startup_observe_actual_business_child[True]未执行。原termination7（含oversize）/identity限额1与新增根配置9/字节边界6/import-runpy真实通路4/调用契约1合计28全过；cleanup原9及正常导入/runpy身份10/终止14报告通路全过。新增oversize子pytest按预期exit1并校验精确step6_identity_summary_limit、无摘要与无payload输出，不属于本批意外失败。正常子报告仅import920bytes/runpy905bytes；本轮固定pytest79566bytes、contract31084bytes，均小于1MiB。身份/quality根参数为配置验证，不称实际旧根或quality执行。

唯一意外失败：backend/tests/test_f009_step6_qa.py::test_startup_observe_actual_business_child[False]，phase=call，脚本4583行。已绑定business35592、parent launcher37340；business原保留查询句柄最终alive=false/code1/available=true，natural=null、主动收口=true。launcher37340（parent68224、created100ns=134334337020580976）终止句柄TerminateProcess返回Win32码5；原失败后状态阶段post_terminate_state，attempt/state单调ns均558767125000000，after_alive=true、after_exit_code=null/available=false；因此原错误准确传播，并非缺少摘要或被限额错误覆盖。随后既有finally Popen收口报告：termination_requested=true、terminate_call_completed=true、wait_returned=true、final_exit_code=1/available=true，但terminate_api_succeeded=null、signaled_confirmed=null，不能据此把前一个API失败改称成功。未取得launcher原查询句柄最终码，不用Popen值代填。两种报告同时保留，原错误5的因果仍未知，不推断为权限不足或自然退出竞态。此次非FastAPI、不复现原connectivity。

机器证据固定根E:\Agent\cyber-town-f009-step6-qa\recovery-20260905-01\qa-tool-contract-06：pytest-summary.json SHA256 D5325D7963FAD5FD44C7FA62BA7802129A0EC34B10749AD138EAE86A6F482D8E；contract-summary.json 21DC854DBAEB006A7968C15EDA23BD237A835BA238FB3E2B86051953FC897B1F，passed=false；native-summary.json 172081bytes/2318288397064E532C5D8F2CD395AB5573C855618CB36366DD0DE9AC831E49AA；machine-ledger.md 728969bytes/4D53B21F9B8F62CC28B7ED7DA6F87FDBB35FDE5769745AFFD8ACF9F4FDF794CD。真实父observer62312与ready/receipt一致，event_count4150/overflow=false/unknown_paths=[]/reparse0；pytest boundary={}且identity/termination拒绝表均空。drain24bytes及ready104bytes已生成，observer产物172209bytes；native.completed=false由本批异常退出保留，不能写成通过。没有观察器独立异常证据。

运行前后代码聚合3f2c5f0d0a6e3b8c37016b15a6dce06db892ae9e6149619905953160ff637ce7一致；两仓branch/HEAD/staged保持。旧26ledger SHA全部相同，含hidden的旧4357文件352085970bytes元数据聚合228E5D044E260C1DFDE4834041DF30B40B5ED652233329DF6ADE7909901F0B83完全相同；首次辅助盘点未带Force漏5个hidden元数据文件，补为与原算法一致的Force只读盘点后核对通过，不是资源删除。新430文件3605143bytes，恢复4787文件355691113bytes，均未超限。收尾只读核验62312/68224/37340/35592已不存在，无F009相关进程及8000/8001监听，没有额外终止操作。读审计结果时一次JSON解析遇到命令尚未返回完整内容，随后只读长等待核对；没有新增测试或运行额度。

四当前文档运行期SHA均保持：task9AD4E27EA887A1AB00782095F0ED35EDF2010B7CB910FF4256CB235094D95EAC；plan28654940A01D07634DDE43E12B1DB329B6026C4F1A62EFC50A681B069E51403F；progress78B7005A3C1FF2A35EEEEF161892B0B79115BCEA66FE88CB87177686D0330814；evidence167374bytes/A5242117519E1E4311252239373D8E7D39F0C21092DDF64A212B8E1C149E791C。机器没有追加正式evidence，本段仅停止后人工收尾。准备1/2、tool06 1/1耗尽、业务/quality/性能0次；不修复重跑。下一步仅审定launcher两条收口通路已有证据的最小处理方案，不自动增加探针或开启完整quality。

## 2026-09-09 端口协调后恢复tool05与条件quality05

本段以下为历史已耗尽批次，不作为本轮运行结果。

用户明确授权13项目侧释放8000/暂停重启并恢复未用额度。只读OS归属：39156→37284（13项目venv）→uv46676→pwsh43148→Codex36732，命令无reload标记。向活动任务“5-综合案例-智能旅行助手-6”（01a07500-38e6-7532-a4b8-2d6bc3e665a4）发送限定收口请求，不直接强制终止他方进程或修改产品/系统配置。持有任务确认Uvicorn属于其F008 R5浏览器批次，先关闭命名浏览器会话，再向持有执行会话92345发送Ctrl+C；服务退出，没有reload/守护/循环，且暂停后续启动直到用户另行批准。该任务批次因协调中断保持未完成，本条不作为F008通过证据。

本任务随后独立复核8000/8001无监听、39156/37284/46676不存在；保存点eb4ab0ac6a4e35dc9057cdc634f97a8ff06078714f96ae35c87637b049716b6f、两仓Git/旧24台账/3338文件282815701bytes与原停止点一致，两根未创建，父链无reparse。沿原预登记/256MiB工具根、1GiB质量根、各ledger8MiB/恢复2GiB，不新增编号，不重复已通过静态或实现。

实际唯一命令：E:\Agent\comprehensive-cases\15-cyber-town\.venv\Scripts\python.exe -B scripts/f009_step6_qa.py --tool-contract；通过后同解释器-B scripts/f009_step6_qa.py --quality recovery-20260905-01/native-quality-05；cwd均E:\Agent\comprehensive-cases\15-cyber-town-f009。各一次，工具清单与quality既定完整命令不变，无额外静态/修复或独立诊断。以下产物均在原恢复根对应tool05/quality05子目录，详细机器记录只在各自固定ledger。

tool05：12:51:25Z开始，12:52:36Z收尾；runner/pytest exit0，92函数330参数全部passed，无缺项、skip、boundary或identity/termination报告拒绝。UV17及Godot受控回放26通过（不是产品精确回环）；父observer54756与凭据一致，native completed=true/event_count4026/overflow=false/unknown=[]/reparse0。原实际Python[False] launcher67008/business60716，两原保留查询句柄final_alive=false/final_code1/natural=null，为主动收口；[True] launcher72648/business37296，两原句柄natural/final7，退出而无主动终止。两分支仅tool05 synthetic证据，不是FastAPI或quality05节点证据。10项正常导入/runpy身份报告及14项终止报告在330项中全部通过。

quality05：12:53:28Z开始，12:57:11Z记录pytest失败，12:57:19Z完成native收尾；runner/quality/pytest exit1。lock、ruff、mypy、schema、godot-import、godot-unit、connectivity、dialogue-connectivity全部exit0；connectivity九个passed_scenario_markers为connected/duplicate_rejected/http_error_recovery/invalid_recovery/non_string_rejected/redirect_rejected/stopped_service/timeout_recovery/unavailable，无failure category或failed marker。没有本次端口占用拒绝或五秒超时记录，但不证明历史native-quality03相同内部原因已被解释。

完整pytest记录1498行：1364passed/133skipped/1failed。唯一失败backend/tests/test_f009_step6_qa.py::test_termination_schema_and_limits[oversize]，phase=call、failure_location该文件2801行、metadata=[]；其余6个同函数参数通过。该行期待step6_identity_summary_limit，调用write_pytest_summary未传max_bytes；源码默认1MiB仅对IDENTITY_VALIDATION_ROOTS生效，本次quality根不是该集合。这里只记录源码关联和适用上下文差异，不改类型/限额/根、不把缺失具体异常摘要补成完整traceback。tool05清单无此函数（实际0项），因此330passed没有覆盖该负例；应先审定测试适用根与显式限额契约/关联清单，不继续完整quality逐个发现QA遗漏。

本轮quality直接通过节点：test_control_evaluation_step5.py的test_fixture_is_strict_versioned_and_covers_all_step5_dimensions、test_baseline_report_meets_all_step5_control_thresholds、test_same_fixture_and_key_match_in_three_fresh_python_processes，以及test_architecture_probe_step5.py的test_v23_waiter_conflict_and_concurrent_prepare_have_one_owner。精确test_godot_scene_fastapi_sqlite_and_fake_provider_form_a_real_local_loopback及quality内实际Python[False]/[True]没有执行记录，不能借用tool05结果；完整收集/未执行总数未写入现有摘要，不新collect来补数。其余安全/预算成本/SQLite/对抗只按已有具体passed节点，不宣称全部覆盖完成。

133skip分布：历史attribution磁盘根45、budget-control V10根53、budget-projection旧候选版本33、dialogue旧磁盘根2；源码既有历史根缺失skip/旧批条件，不是本轮新增或为失败放行。摘要未保存每项skip reason，不能仅凭133与旧值相同认定完整契约豁免；正式语义验收已失败，后续审定仍须按这些实际nodeid逐项确认适用性，不重建旧根或恢复旧性能批次。

quality父observer58592，native completed=true/event_count14168/overflow=false/unknown=[]/reparse0；pytest边界{}及identity/termination报告拒绝[]，drain marker保留。native completed仅指观察收尾，不能覆盖quality exit1。两批进程均结束、8000/8001空闲；已向13项目任务发送本轮结束通知但不授权重启，其浏览器批次中断仍由用户另行决定。

代码聚合eb4ab0ac6a4e35dc9057cdc634f97a8ff06078714f96ae35c87637b049716b6f运行前后不变，两仓HEAD/分支/staged0保持。排除两个精确新子树后旧24台账SHA、3338旧文件长度mtime聚合与接续完全一致；tool05的ledger/contract/native/pytest/owner在quality运行期间SHA均未变。四当前文档跨两批运行期hash相同，evidence运行前后159829bytes/SHA256=B55A62130810837D2E8AA63FAFB07FD918E1F607C9D1994928CE5CEBEAAABE82；只在收尾人工更新，不曾机器追加。

资源：tool05 420文件1476449bytes，ledger704675bytes/SHA256=F5CE46F7677B5D1EA992808C9247EE35C0EE833AC498D8B73A945B9F07A8B4A2，contract29964bytes/7CE46BD32CF39CBE3B0589CE9216CFE62BA0413EAAD208FA5CCB462E7F15CAE0，pytest78984bytes/1117BF6B50E10DFFF25C2FF40F221FA8009247AB604153813CE5EE73B998297C，native168690bytes/A3F0BB62462DA63C7B4B604743F12F5D01C81962832BEBC0E3B970BB204752D8。quality05 599文件67793820bytes，ledger1562206bytes/60A7EECE862D07B847331450FCC952F19FCB28998DD1C8511F35C433802372E6，quality4711bytes/03EE8BC74C52302ABC9498B25E67A8C8BC45504B3482093FDDF8C4F7630B5294，pytest342768bytes/9AB2CC1C8E790EF8A7630410CB215B84DEFC8C697B2C63268275669986E37812，native218126bytes/305FFFBF994742F8F7EB378ACD03091FB855D25CBF0059D7A29D4ADA8A70D47E。observer产物分别168818/218252bytes；新增1019文件69270269bytes，恢复4357文件352085970bytes，均在原限额内。两批和全部旧证据保留，不删除、不复用。准备0/2、tool05=1/1、quality05=1/1；性能/Step7未执行，结束后停止。

## 2026-09-09 tool05/quality05接入静态通过，独占窗口失效停止

接续原聚合0f6541aa00e41f2954b1fce952045e44200d61f701e5e833ea45189f0ad1fedc，与两仓原分支/HEAD1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3、staged0、100/19变化一致；旧24台账/3338文件282815701bytes保留，元数据聚合82C11FEB3F36D81B6AF5A494B59B95683D84F3BA5EF07218B9E88C5FA88D87ED。初始8000/8001空闲且无相关进程，两新根不存在；用户确认整个验收窗口其他项目不启动/重启占用服务，本轮只登记两新根和台账，没有实际创建。

代码只改两QA：TOOL_CONTRACT_ROOT/NATIVE_QUALITY_ROOT切至05，HISTORICAL_LEDGERS新增固定qa-tool-contract-04/native-quality-04台账；在既有test_qa_ledger_preserved_history_and_precreation_contract中验证新精确根/256MiB和1GiB配置、两旧根属于历史且不属于活动白名单、batch_ledger_path仍精确拒绝旧根。没有修改任何函数运行逻辑、产品、权限/owner/守卫/observer/进程/等待或质量命令。对内存中本轮精确差异做反向字节校验（不还原磁盘），两文件原hash分别190885400aacaf6a438f2c1c1dba84516d500ad96d56bca7cc264717c23ef02e和ce951589fa2e1629404ea54d8124e0c51b72b95c8863963244efbe4746d9e188，与基线一致；其他98项及正式项目其他文件hash相同。

初次静态全部exit0，修正额度0/2：cwd功能目录，原正式.venv/Scripts/python.exe -B -m ruff check --no-cache scripts/f009_step6_qa.py backend/tests/test_f009_step6_qa.py；同解释器-B -m ruff format --check --no-cache 两QA；-B -c仅ast.parse两源码及3原fixture字符串、不导入QA；MYPYPATH=backend/src，-B -m mypy --no-incremental --cache-dir=nul 两QA，原strict配置不变；两仓git --no-optional-locks diff --check及61个untracked中的文本空白检查均通过。AST核对92个唯一函数/TOOL_CONTRACT_COUNTS总330与原选择器/装饰参数未改变，新增断言不增加参数；这些仅静态事实，不声明tool05通过。

保存点eb4ab0ac6a4e35dc9057cdc634f97a8ff06078714f96ae35c87637b049716b6f；scripts/f009_step6_qa.py SHA256=d095c3abdf1715fdd868a2d35b4f2ef161fb2f4dd495d8ac54e4e4cdac5918f5，backend/tests/test_f009_step6_qa.py SHA256=5ce9c9ce263cf1a13ccfe16b9fa1c894ca9770c09a9e6824769a74b951346ea1。

停止事实：静态后冻结复核发现127.0.0.1:8000监听PID39156；2026-09-09T12:41:42Z只读复核仍在。PID39156为uv CPython3.13.3，父37284解释器路径属于13-intelligent-travel-assistant/backend/.venv；两者创建于12:39:40Z，命令无f009/本批标识。8001无监听。只看OS归属元数据，不读取该项目文件或完整命令/环境，不终止对方。该结果直接说明本次运行窗口不满足，并非运行时测试失败或原connectivity超时复现；本轮没有FastAPI/fixture/Godot或synthetic启动，不填造子进程退出证据。

tool05=0/1、quality05=0/1，两根仍未创建，新增运行资源0bytes；24旧台账SHA和3338旧文件元数据与接续一致，恢复282815701bytes。所有旧失败及快照/台账保留，无删除。正式四文档只人工更新，没有新机器记录或observer运行。复盘：quality04与本次准备均遇到其他项目占用8000，单次空闲快照不能保证整个运行窗口；应由资源所有者协调暂停占用服务及自动重启，而不是增加同类启动探针或修改F009端口/超时。唯一下一动作是用户完成该协调并明确恢复当前未用tool05/条件quality05；本轮不自动等空闲后运行，不新增额度。

## 2026-09-09 native-quality-04唯一完整语义验收

运行前：原聚合0f6541aa00e41f2954b1fce952045e44200d61f701e5e833ea45189f0ad1fedc；两仓HEAD1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3、feature/main、staged0、100/19变化一致。23台账SHA、旧3283文件长度/mtime聚合无漂移，恢复240633553bytes；quality04根尚不存在、父链无reparse、无相关进程及8000/8001监听。tool04的contract/native/owner与冻结6文件、92函数330参数一致，completed=true/overflow=false/unknown=[]/reparse=0；旧probe的9命令退出0仅保留工具事实。无新代码修改、无重复测试或静态。

唯一命令：`E:\Agent\comprehensive-cases\15-cyber-town\.venv\Scripts\python.exe -B scripts/f009_step6_qa.py --quality recovery-20260905-01/native-quality-04`；cwd=`E:\Agent\comprehensive-cases\15-cyber-town-f009`。2026-09-09T10:51:55Z开始初始化，10:52:50Z记录connectivity失败，10:52:54Z收尾inventory登记；外层runner与quality exit1。额度1/1已耗尽，未修复重跑。机器结果位于`E:\Agent\cyber-town-f009-step6-qa\recovery-20260905-01\native-quality-04`，以下均为该根文件；本节仅人工摘要，原命令逐项argv/cwd/exit及脱敏分类见quality-summary.json。

已执行：lock、ruff、mypy、schema、godot-import、godot-unit六项exit0；第七connectivity exit1，diagnostics.failure_categories=[runner_loopback_busy]、passed_scenario_markers=[]、failed_scenario_markers=[]、runner_failure_marker=true，所有commands.boundary_codes/error_classes为空。后续dialogue-connectivity及完整pytest未执行，pytest-summary.json不存在；精确Godot本地回环、25-case evaluator、3新进程digest、安全/预算成本/SQLite/对抗及原ownership节点均无本轮pytest执行证据。未执行性能；不使用tool04或更旧结果冒充本轮。

失败边界：connectivity源码218–222行在场景前要求8000空闲；QA分类也覆盖fixture/业务启动前的同类占用拒绝，摘要未保留具体匹配原文，不能仅凭类别确定所有内部细节。收尾只读OS元数据见当前127.0.0.1:8000监听PID26380，其父60432的解释器位于13-intelligent-travel-assistant/backend/.venv，业务解释器为uv的CPython3.13.3；两进程创建于10:50:49Z、无f009/quality04命令标识。只记录当前元数据，不读取另一项目内容、不终止/修改其进程。该事实支持跨项目端口竞争候选，但没有失败时监听PID证据，不倒推同一PID必然造成当时拒绝；也不是原native-quality03五秒未监听的同因复现。FastAPI启动/health无本轮完成证据，不填造业务退出码。

observer：native-monitor-ready记录root准确、父PID25992；native-summary completed=true、event_count303、overflow=false、unknown_paths=[]、reparse0，drain marker保留。此completed仅表明native观察/收尾路径完成，不代表quality通过；父PID25992已退出，无f009相关进程残留。8000外部监听仍在、8001无监听，未擅自处理。

完整性：原聚合0f6541aa00e41f2954b1fce952045e44200d61f701e5e833ea45189f0ad1fedc与100项文件SHA逐项不变，两仓Git/HEAD/staged无漂移。排除本轮精确子树后旧3283文件长度mtime聚合和23台账SHA均与运行前完全一致。四当前文档运行前后hash相同；evidence为151628bytes/SHA256=0AAE770815CCD66FC4162FDE892418DB6B5E5F423E2DDC32CD31CE7C12BCA9B1，运行后仅本次人工收口更新，不曾机器追加。

资源/索引：本轮55文件42182148bytes（含native-summary自身；inventory写入前54文件42143719bytes），恢复3338文件282815701bytes，均低于1GiB/总2GiB。machine-ledger.md=54459bytes/SHA256=8642614E8E2D927E16ED052E375EE2F7632A2584513E2C69F684BFC0AC258D95；quality-summary.json=3335bytes/SHA256=0E4347C618A405732927B8E8C99F501699D7A7F5DF9F26BD19AE02CAF8183482；native-summary.json=38071bytes/SHA256=7A984D6E18867C07CD063EBC54ACDCC59733E35ECE8D873CF8FF7915D00122D8；ready102bytes、drain24bytes，observer合计38197bytes。全部新旧批次/快照/台账作为证据保留，无删除。唯一下一动作是审定端口占用与跨项目运行窗口及恢复语义验收条件；不直接修复代码、新增探针或开下一批。

## 2026-09-09 历史来源生命周期修正与工具契约04

接续fd0fb70d8dd25f88e3e9a1fb955aa9d9c909a1d88d021a3db1242d48a812e8b9，两仓HEAD1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3、原分支、staged0和100/19变化一致；旧2863文件239158532bytes/22台账SHA及长度mtime聚合不变，无相关进程/8000或8001监听。tool04/quality04均不存在，父链无reparse；25份现有读取来源（22台账+归档/快照3）元数据存在性核对通过，没有展开历史正文。

只改两QA：tool04新根与失败tool03历史，HISTORICAL_LEDGERS剥离活动tool/quality常量，readiness02/diagnostic05固定历史路径；resource_ledger_sources纯选择必需历史/任务卡/原绑定活动台账，仅quality附加当前tool前置；require_ledger_sources保留真实缺失拒绝，run_tool_contract创建根前先检查历史。旧入口断言适配已完成readiness02历史/只读和当前运行绑定；没有宽泛跳过缺失来源、预建quality根、全局替身或新框架。AST函数/类指纹对照：脚本既有函数只registered_resource_paths、run_tool_contract变化；测试既有函数只test_entry_readiness_contract变化。native_session/inventory、Win32、权限/owner、守卫、observer、收口及所有产品保持。

静态初次Ruff一处SIM300（已完成readiness路径比较顺序）；format-check、AST2文件3fixture、strict mypy及diff均exit0。第1轮等义交换比较顺序，完整静态全部exit0，准备1/2。沿既有解释器/cwd、两QA Ruff check/format-check --no-cache、原AST不导入QA、原两个mypy目标/MYPYPATH=backend/src/--no-incremental/--cache-dir=nul；两仓diff及untracked空白通过，无安装。

冻结0f6541aa00e41f2954b1fce952045e44200d61f701e5e833ea45189f0ad1fedc；脚本190885400aacaf6a438f2c1c1dba84516d500ad96d56bca7cc264717c23ef02e，测试ce951589fa2e1629404ea54d8124e0c51b72b95c8863963244efbe4746d9e188，其余98项不变。清单92函数330实例，原87/299保留，新增四个生命周期函数5+1+4+1共11参数、既有入口20参数；这31项前置，原失败节点及真实报告通路不删，实际Python False/True仍最后。AST展开与TOOL_CONTRACT_COUNTS逐项一致，未import/collect/run测试来计数。

唯一命令：`& 'E:\Agent\comprehensive-cases\15-cyber-town\.venv\Scripts\python.exe' -B scripts/f009_step6_qa.py --tool-contract`，cwd E:\Agent\comprehensive-cases\15-cyber-town-f009。准确子命令/清单/六文件凭据进入本批contract-summary；初始工具0/1，任何意外失败立即停止不修复补跑，质量/业务启动0授权。根与ledger创建前登记在current-task；其他固定/动态子资源仍既有guard操作前登记。批次≤256MiB、ledger≤8MiB及原更小报告限额，恢复≤2GiB；四当前文档运行期只读，新旧证据全部保留。

执行结果：唯一工具命令runner/pytest均exit0，92函数330参数全passed，无失败/skip/未执行项，contract-summary passed=true/all_selected_functions_executed=true，准确参数计数匹配。原历史读取失败节点及新增真实NativeWatcher→drain/close→native_inventory回归通过，真实缺失历史负例精确拒绝；工具完成时future native-quality04仍不存在，未预建或绑定其台账。配置用例的quality来源选择只是纯契约验证，不是quality运行。

真实报告链：正常导入/runpy组合的身份报告10项和终止报告14项全部通过；受控子pytest预期失败由父断言核验，不忽略外层错误。入口原9项（含observation_error/reader_error）、叠加收口10、缺证据3、取证失败3、Popen四路4及schema等全部通过。UV17、Godot回放26、ownership直接回归通过；回放不代表精确Godot产品回环。

本次实际Python synthetic False：launcher40688(parent54512)、business63368(parent40688)，初次绑定后各自持续持有查询句柄；两者natural_exit_code=null、主动收口=true、termination_attempted=true/error=null，最终alive=false/code_available=true/code1，final_state_source=retained_query_handle。True：launcher47216(parent54512)、business24008(parent47216)，两者natural/final7、无主动终止、最终alive=false、各自保留查询句柄来源。Popen后备两路均未尝试终止，返回已有1/7，底层API/signaled仍unknown，不以缓存值替代保留句柄观察。以上不是FastAPI，也不是历史74/183项退出码。

真实父observer PID40900与contract/ready一致，native-summary实际生成completed=true、4012events、overflow=false、unknown_paths=[]、reparse0；pytest boundary={}、identity/termination拒绝均空。新旧资源核对完成，未发现相关Python/Godot残留或8000/8001监听，没有处理无关进程。

冻结及六文件凭据运行前后与磁盘均匹配：聚合0f6541aa00e41f2954b1fce952045e44200d61f701e5e833ea45189f0ad1fedc，两仓原分支/HEAD/staged0、100/19保持，其余98项不变；22旧台账SHA和旧2863文件长度/mtime聚合不变。四当前文档运行期逐一字节/hash相同，evidence运行前后146653bytes/SHA9B5C882BB739DA95CF5A2209B8655F3F058D74672429AD98622EBA1B5DDA3976；机器仅当前固定台账，结束后才人工摘要更新。

容量：新tool04为420文件1475021bytes，ledger703177、contract-summary29964、pytest-summary78984、native-summary168703、ready104、drain24bytes，observer合计168831bytes；均在批准限额内。恢复3283文件240633553bytes<2GiB，新旧证据全部保留不删除。主要SHA：contract-summary=60D3276EFEF9DA8A7D6B2034975DE1430719F39F7466496CA85CF65E67D596A4，pytest-summary=CE75DA349E76D49F2AF70A2589E9673D0757DAEFEFD1904A2651B2E07DCDDAE8，native-summary=AD2C882E416B0185147FD318BD85532BEB1B1C1C552843D5FC042AF36B17813E，ledger=B47473ACA3D8B182951AC7BB24FD977E0E436B1300D25F5421BAB39560200AD5。

收口结论：本轮历史来源生命周期工具缺陷修复并验证；首次绑定/来源选择、历史读取/缺失拒绝、报告通路、真实inventory收尾及两个实际子进程均有直接证据。本次准备1/2、工具1/1已用，历史额度不迁移；质量/业务/性能运行授权0。本次未执行完整quality、精确Godot/evaluator/digest产品验收或性能，不关闭历史connectivity因果，不宣称Step6完成。唯一下一动作：审定当前冻结及有效工具凭据下是否恢复原未消耗native-quality04一次完整fake-only语义验收；本轮结束，不自动启动。

## 2026-09-09 工具契约03与完整语义验收04

接续聚合fc0e74a5e8b82cd3d4159ea807d09d2b3039728a807ff877516fe7186d3d3128、两仓原分支/HEAD1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3/staged0、100/19变化一致；旧2752文件238697138bytes、21台账SHA及资源长度/mtime聚合未漂移，无相关进程和8000/8001占用。新tool03/quality04路径不存在且父链无reparse，bootstrap登记在current-task；未新建环境或读取真实.env。

只改两QA：tool03/quality04精确配置及旧台账历史覆盖、动态生成当前工具子命令、六文件/清单/准确参数和真实observer凭据核验、直接回归。受保护进程/权限/守卫/台账语义、产品字节和原quality命令不改。冻结87函数/299实例：原70函数201参数不删，凭据新增2反例后203；新增17函数96参数，含真实import/runpy报告、收口/上下文及实际Python False/True最后。UV17、Godot回放26保留；回放不作为产品回环。AST逐函数展开与计数表完全一致，未import/collect QA。

初次静态：Ruff54处E501（新增完整nodeid计数表）；format-check0、AST0（2文件3fixture）、mypy0、diff0。第1轮将长字符串作括号内等义拼接，完整静态全部exit0；准备修正1/2。未执行运行时修复/重跑。准确命令cwd均feature：原venv python.exe -B -m ruff check --no-cache 两QA；同解释器-m ruff format --check --no-cache 两QA；-B -c仅ast.parse两源码及3个fixture字符串；MYPYPATH=backend/src，同解释器-m mypy --no-incremental --cache-dir=nul scripts/f009_step6_qa.py backend/tests/test_f009_step6_qa.py，strict配置不变；git --no-optional-locks diff --check（两仓）及untracked空白检查。工具环境复用原venv，无安装。

运行前冻结fd0fb70d8dd25f88e3e9a1fb955aa9d9c909a1d88d021a3db1242d48a812e8b9；脚本011f966f56f8adbadd775c1bb0afa25a636b5465b87a2a87e546fa142a42fe56，测试6ee6a8e31da1d0ffb02708a0ff5e7960a4ee7213ad3690762b75e2e093357fb5，其余98项不变。完整清单/计数在脚本TOOL_CONTRACT_TESTS/COUNTS冻结，并进入contract-summary。旧21台账、运行期四文档只读；机器仅本批固定台账。

唯一工具命令：`& 'E:\Agent\comprehensive-cases\15-cyber-town\.venv\Scripts\python.exe' -B scripts/f009_step6_qa.py --tool-contract`；只有其实际299参数全过、native完成/owner一致/无违规、当前六文件/聚合与旧资源稳定才同解释器-B脚本`--quality recovery-20260905-01/native-quality-04`一次。cwd为E:\Agent\comprehensive-cases\15-cyber-town-f009。完整quality既有精确Godot/evaluator/三进程digest均在全backend pytest，不另跑；任何运行失败即停、保留未执行节点。初始工具0/1、quality0/1；新根≤256MiB/1GiB，ledger各≤8MiB，恢复≤2GiB，全部保留不删除。

本轮运行收口：工具命令仅一次，runner/pytest退出1；pytest-summary为162passed/1failed，共执行163/299，剩余136未执行，无skip。失败节点test_qa_contract_history_covers_preserved_sources_and_fixed_ledger，phase=call，脚本1743行；最后通过为台账并发可见性回归。UV17及Godot回放26通过，后续原ownership节点、新增报告/收口/上下文及实际Python False/True均未执行，不能代填历史183/74项结果。

直接原因：HISTORICAL_LEDGERS第112行仍引用当前NATIVE_QUALITY_ROOT。该常量本轮切换native-quality-04，而新quality根/ledger按条件尚未创建；registered_resource_paths把每个历史来源视为必需，在1743抛step6_resource_ledger_missing。只读核实quality04/root及ledger不存在，旧quality03/ledger仍保留。因此这不是丢失旧证据，而是把未来资源误列为已存在历史。外层先产生step6_tool_contract_tests_failed；native_session已走drain/close，随后native_inventory再次读取同一来源，抛相同missing并阻断native-summary写入。异常顺序按实际保留，不修复或补写假summary。

证据边界：真实父observer启动，ready记录PID45248，drain marker已创建；pytest boundary={}、身份/终止报告拒绝均空，但native-summary不存在，不能据此宣称observer完整/所有原生边界零违规。运行结束无相关Python/Godot进程或8000/8001监听；未额外终止任何进程。完整quality、精确Godot回环、evaluator/三进程digest、性能全部未执行，quality04根未创建。

运行前后聚合fd0fb70d8dd25f88e3e9a1fb955aa9d9c909a1d88d021a3db1242d48a812e8b9，两仓原Git/100与19变化/staged0保持；其余98项不变，21旧台账SHA及旧2752文件长度/mtime聚合不变。四份正式文档运行期字节/hash一致；evidence运行前后140479bytes、SHA4E6C4170A134235118AABED4632D8EA5DC2BD11DDD65896055BD0C089A0A9042，仅结束后人工摘要更新，机器没有追加正式evidence。

新tool03为111文件461394bytes，ledger277744、contract-summary26046、pytest-summary38112、ready104、drain24bytes；恢复2863文件239158532bytes，全部低于批准容量。新旧资源均为继续保留的证据，不删除；quality04未启用。pytest-summary SHA6176964D315989464C2446F528B89216598FE313DE42C6819A982E525135B30B，contract-summary SHAC5F6FE3C9C6676A3CCF14AB169F924D6110DA99245C73FFB4CBF4904E32E0448，ledger SHA63E31F3168C452E33C5670E158EE6AE4032EBEF2FD9CF2E9901CCBA9F24BD509。详细节点/登记留独立qa-tool-contract-03批次，旧证据未覆盖。

额度与复盘：准备1/2、唯一工具1/1已用，quality0/1因就绪失败阻断；剩余准备不适用于本次运行故障，未修复重跑。触发是本轮当前根轮换，遗漏是历史源列表仍依赖活动常量；后续应在创建/运行前静态核对“必需历史均存在、未来条件批次不进入必需历史”，并保留缺失真实历史必须拒绝的负例。建议落点仅两QA的历史来源配置与直接回归，不宽泛跳过缺失来源或预建quality目录。唯一下一动作：审定该最小修正及新工具验证额度，不自动恢复完整quality。原ownership/canonical关闭独立保留，原connectivity因果仍未知、step6_complete=false。

## 2026-09-09 新就绪02与条件诊断05：运行前冻结

用户明确批准两QA最小接入、最多两轮准备修正及完整静态、一次新就绪02；全部通过才允许diagnostic05五前置一次/FastAPI一次/health至多一次。接续7d4bec7ad344569d572b6935a8ba4b6309d6571d6d7cf693472947fdd1686852、两仓原分支/HEAD/staged0、100/19、旧2365文件237342815bytes/19台账核对无漂移。新02及05均不存在、全部父链无reparse、无相关进程/8000或8001监听。02新根/ledger精确预登记见current-task，05复核既有精确登记不重复追加；新授权独立计账，不迁移旧额度。

代码只改两QA当前就绪根/旧台账来源、报告计数和直接配置断言；REPORT_READINESS_ROOT从01切至02，旧01/CLEANUP两批只读列入历史源，05已完成配置不重写。保留原启动/收口、Win32/权限/owner/guard/observer和产品字节。清单33函数/34选择器，AST静态展开183参数且与计数表逐项一致：原159+schema新增4+异常收口10+正常缺证据3+取证失败3+Popen四路4；实际False/True仍最后各一次。AST只读解析源码，未import/collect/run QA。

初次完整静态全部exit0（原两QA Ruff check --no-cache、format --check --no-cache、AST2文件3fixture、原strict mypy/MYPYPATH/backend/src/--no-incremental/--cache-dir=nul、两仓diff --check），准确原命令见下方AST恢复记录；本次准备修正0/2，未作失败后修复。冻结fc0e74a5e8b82cd3d4159ea807d09d2b3039728a807ff877516fe7186d3d3128，脚本125803afa6970f407b8eb0533a7e73b7a81aa41a6a89160e0592e8634adb81a4，测试17d2ef850bc90a34f360e8cdc58486db5067a7c7e57f64ffd732345787f9258f；其余98项不变。

唯一就绪命令：`& 'E:\Agent\comprehensive-cases\15-cyber-town\.venv\Scripts\python.exe' -B scripts/f009_step6_qa.py --startup-report-readiness`。仅全部通过、observer完成/零拒绝/无漂移后，同解释器-B脚本`--startup-report-diagnostic`，cwd均功能worktree。后者仅验证当前六文件及四报告凭据，不重复集合，原五前置后一次业务启动/原五秒/health。运行前就绪0/1、前置0/1、启动0/1、health0/1；失败即停不修复补跑。02≤32MiB、05≤128MiB、各ledger≤8MiB及更小产物限额，恢复≤2GiB；运行期四文档及19旧台账只读。

本次执行收口：新就绪02仅运行一次，runner/pytest均exit0，实际183passed/0failed/0skipped，33函数/34选择器全部参数计数匹配，无未执行项。包括9个原入口参数、10个叠加收口负例、3个正常缺证据、3个取证失败、Popen四路，以及import/runpy真实报告通路。受控子pytest的预期失败由父测试验证，不是外层忽略失败。父observer29808完成，2382events，overflow=false/unknown=[]/reparse0，boundary={}，身份/终止报告拒绝均空。

本轮实际Python synthetic False：business14780/parent launcher14576（parent41552），两者原保留查询句柄final1、alive=false、code_available=true，自然码null，终止API成功且error=null；True：business14500/launcher72248，两者自然及最终码7、无主动终止。两个Popen后备报告均未发起终止，返回已有1或7且API/signaled未知；不能替代原保留查询句柄证据。历史74项及旧失败False均不代填本轮结果；本次两分支未复现历史终止错误，不关闭其OS内部原因。

通过后只核验就绪四报告哈希/六文件冻结，未重复就绪集合。diagnostic05仅运行一次，原五前置按stopped_service、unavailable、duplicate_rejected、non_string_rejected、redirect_rejected顺序通过，原请求计数/拒绝断言及fixture收口保持，preconditions-summary exit0/all_original_assertions_passed=true。端口空闲后一次原解释器-m cyber_town.api，实际包装命令/cwd/fake-only安全摘要见05/invocation.json。未执行后续connected/recovery Godot或完整quality。

05原Popen返回起算543241.437，deadline543246.437；5次TCP探测，前4次false，543242.593首次true（起算后1.156s），同一记录时刻唯一health通过；这是观察到开放时间，不是精确bind时刻。观察期间launcher51972（parent70540）与business13140（parent51972）存活，已按OS父子/创建身份绑定并持有查询句柄；随后主动收口，两者独立保留句柄最终alive=false/code1/available=true、natural=null、termination_attempted=true/error=null。码1不是业务自然启动错误。无Popen后备触发；543242.609 process_closed、543242.828 port_released，最终无相关进程或8000/8001监听。

六阶段完整：业务入口线程49596、wrapper binding t543241.578；before_composition_import543242.421，composition_import_returned543242.453；main_entered、settings_returned、before_service_assembly、before_uvicorn_run均记录543242.453。composition区间32ms，wrapper→首标记约843ms；相同时间戳不代表各步骤无耗时，最后阶段只表示uvicorn.run调用前。543242.593已达到health并开始收口，早于采样计划543243.078/543245.078，两slot均cancelled，实际位置采样0次、无补采，没有位置阻塞证据。所需10个模块来源全部观测到，产品模块来自feature/backend/src、依赖来自既有venv；不为取证额外导入。

观察边界：05父observer70540完成，39events、overflow=false/unknown=[]/reparse0，业务boundary={}；输出readers_finished=true、6phase/2cancelled位置事件，丢弃1条非白名单输出，未保存原始内容。evidence-status中reporting_complete/finalization_complete/cleanup_completed=true，normal_completion_validated=false是既有收口时快照；不将它改报true。本次后续正常校验通过依据完整phase_evidence/observations及runner exit0，状态快照本身不是完整验收凭据。未修改这一报告语义或追加运行。

容量：02为342文件1188048bytes，ledger495878、observer118114、其余固定/临时均在限额内；05为45文件166275bytes，ledger26329、observer18641、phase680/position374/timeline5969/stdout0/stderr2373bytes。两批新增1354323bytes<160MiB，恢复2752文件238697138bytes<2GiB。19旧台账SHA、旧2365文件长度/mtime聚合不变；02四凭据哈希在05后仍一致，02台账最后写入09:01:39.0155723Z，早于05创建09:02:39.9048013Z，尺寸不变。新旧资源全部保留，不删除。

运行前后代码聚合均fc0e74a5e8b82cd3d4159ea807d09d2b3039728a807ff877516fe7186d3d3128，两仓原分支/HEAD/staged0及100/19保持。四文档两个运行期间逐一字节/哈希不变；evidence运行前后132347bytes/SHA8A310A96F60EEDF93EEB865387550F2BA72A83442A3ED40CF5AA43428EE409B6。机器仅独立台账，之后仅人工摘要收口。

主要证据SHA256：02 pytest-summary=61A398582842DEEE61E2DAD7EFBE773E65032A79B68E23B38A9329EE96DA22C2，ledger=C18C6CCA91E8AC4D43C3D08E74A2C0A2A6D6398A63D1402FDE411F525362D855；05 timeline=8F012BF6F93B86E5CDD1B6A579943F67DC3CEE3426FA0FA8AE417219175BE369，native=4FE3E2D6D7A89EE8BF264B85194CFB8EAC368EE8164C5390639748B554EDE691，ledger=8AC7D8BB7C44B90693E65C799E0CF5C0E2AB9D20A3378B40668E1A3A2DCD67AE。准确机器过程均保留对应独立批次，不改旧结果。

独立结论：工具接入与新就绪通过；五前置通过；本次启动/监听/health通过且归属收口证据齐全；原超时未复现，因果根因仍未知。相对原native-quality-03存在当前QA与既有获批composition导入调整、新缓存/台账、观察开销和编排差异，未重跑前六完整工程门禁，不能称等价复现或原故障关闭。本次所有运行额度1/1已用、准备修正0/2，不迁移剩余额度；唯一下一动作待审定恢复完整fake-only语义验收的就绪条件与新额度，不再自动追加同类启动探针。性能和Step7不进入，结束本轮。

## 2026-09-09 AST类型恢复与运行前冻结

用户已批准局部类型适配及原唯一定向恢复。仅测试中`ast.Module`边界改为`list[ast.stmt]`（变量`methods`），原`FunctionDef`筛选、方法体及脚本均不变；没有Any/cast/ignore适配。原73809585保存点与18台账/2349资源逐项核对一致。本次完整静态复验按下方原五项准确命令，Ruff/format/AST/mypy/两仓diff均exit0；AST为2文件/3fixture且不导入QA，mypy两目标原strict/MYPYPATH及小写nul。初次失败记录保留，本次仅已批准的一次类型恢复及完整复验。

冻结聚合7d4bec7ad344569d572b6935a8ba4b6309d6571d6d7cf693472947fdd1686852；测试SHA5628b7acaefac8f392041315c88bcc3bfb716c22d04a59d5856a05f73493be41，脚本仍0ea8b15e2482ca4af8f967cf33833070f94372dbd69508dad9121e7797e47617。相对接续仅获批两行替换，其余99项不变，无尾空白；两仓分支/HEAD/staged0及100/19保持。新根/全部父链无reparse，端口8000/8001空闲，无相关进程，旧资源237263969bytes/18台账未变。

固定CLEANUP_SEMANTICS_TESTS沿原9函数/12选择器、31预计参数实例不变。唯一运行命令：`& 'E:\Agent\comprehensive-cases\15-cyber-town\.venv\Scripts\python.exe' -B scripts/f009_step6_qa.py --cleanup-report-semantics-validation`，cwd功能根；资源使用current-task已精确预登记的新startup-cleanup-report-semantics-validation-01，真实父observer/固定机器台账/路径守卫与受保护pytest，不调用业务或实际False/True。运行前定向0/1，启动即消耗；失败不修复复跑，四文档运行期只读、机器记录只进独立台账。此结果不得作为业务就绪凭据。

本次最终结果：唯一上述命令exit0，受保护pytest实际31passed/0failed/0skipped，9函数/12选择器的全部参数均执行，没有延期项。顺序为根/owner/台账4→局部owned4→报告6→Popen四路4→schema9→真实报告通路4。原实际Python False/True、FastAPI/Godot/connectivity/quality/性能均未执行；PID20和各模拟返回码只是fixture，不能当实际launcher/business退出证据。

四路最终摘要（底层terminate_api_succeeded、signaled_confirmed全部null，未被Popen表层返回证明）：

| 受控路径 | termination_requested | terminate_call_completed | wait_returned | final_exit_code |
| --- | --- | --- | --- | --- |
| success | true | true | true | 1 |
| error_exit | true | true | true | 7 |
| error_active | true | false | false | null |
| cached | false | false | true | 7 |

error_active严格捕获同一PermissionError对象、winerror5、cleanup_call_completed=false、exit_code_available=false；没有将码5放行。error_exit是所选CPython方法原有行为返回7，报告不宣称TerminateProcess成功。cached的断言确认未调用TerminateProcess或WaitForSingleObject，wait_returned只表示方法返回。四项cleanup_report已贯通MetadataReporter至顶层pytest-summary和termination-events；不依赖测试对象上暂存字段。

四份termination-report/{import,runpy}/{cleanup_success,cleanup_failure}/pytest-summary.json均是父回归严格核验的预期失败子pytest：exit1、1passed/1failed，失败节点test_expected_failure/phase=call，主观察与cleanup_report分离且无串项/拒绝。success的cleanup final1但API/signaled未知，failure的cleanup码5/未知最终码，原终止观察单独保留。受控子失败不是外层意外失败；外层四参数均通过，不吞业务异常或修改安全边界。

父observer PID56572与ready归属一致，native.completed=true、130events、overflow=false、unknown_paths=[]、reparse0、game_hashes={}；drain/close/最终库存完成。顶层及四子报告boundary={}、identity/termination_diagnostic_rejections=[]，无报告缺字段。最终只读无相关进程及8000/8001监听；本轮没有业务/实际False/True独立PID退出码可报告。

资源16文件78846bytes（<32MiB），台账32694（<8MiB）、observer三文件6142（<8MiB）、临时fixture/子报告26194（<8MiB）；恢复2365文件237342815bytes（<2GiB）。旧2349文件长度/mtime聚合和18台账SHA均不变；冻结聚合运行前后同7d4bec7ad344569d572b6935a8ba4b6309d6571d6d7cf693472947fdd1686852。四文档运行期字节/哈希逐一不变；正式evidence运行前后125846bytes/SHA 5C4B443BEEA4D69E7E8409B4A1028EC9D1962CB72F632D8FF3B715C47E71DECC，机器只写新固定台账。之后仅人工收口摘要更新；新旧全部证据保留，不删除。

本批固定产物：invocation.json=2341bytes/SHA256 E70410BA4541FA37C8343087C7CF42FDE11D362768B93F16DBC0FACB1F6CF1C6；machine-ledger.md=32694bytes/SHA256 0FC8750A05BA2B54AAE915C6828D755E4CED886765916C5CBFE12A8F4C594F2B；native-monitor-drain.marker=24bytes/SHA256 00C3296A81DE6FFFBBF013D93D61DC405359F776143D5961F2EEBC29A453F626；native-monitor-ready.json=131bytes/SHA256 4A346E67BBF290D4E477233F76358F75B8520F7CABBA80A5E931A6597D089701；native-summary.json=5987bytes/SHA256 B899B35BDD1A8B44DE6C4E4078D7E420C8774656BFB086DD643D076CDA628A9E；pytest-summary.json=9113bytes/SHA256 64CC39913E1AE3116AAD67CF2CD1297B0DED03E684EE40B3F04C7BA7259000DE；termination-events.jsonl=2362bytes/SHA256 8BEAD7083D4E16268BE7AA261BE83D6845FB196281CE9D29296D6AF1BE742EB9。

初次mypy类型失败历史保留，本次获批类型恢复及完整静态复验1次；原定向1/1已耗尽，不复跑。有限复盘：Popen方法返回、获得缓存码与内核API成功/signaled是不同证据层，本次用受控四路和真实报告通路约束表述；不能反推历史码5的OS原因。仅可称本次报告语义修正并通过直接回归，不是完整启动就绪或产品验收。下一动作只待审定原connectivity诊断恢复条件与新额度，本轮结束不自动启动。

## 2026-09-09 Popen收口报告语义候选（静态停止，未运行）

用户批准仅两QA报告语义、直接synthetic回归和新startup-cleanup-report-semantics-validation-01（32MiB，精确登记见current-task）；不得改权限、顺序、等待、安全规则或恢复业务。本次从eb3fbb50d45af35cb16221e89527300ff8d27a8ba5e01c6e5fd955b003df154f接续。只增加调用局部标量和封闭报告字段：termination_requested、terminate_call_completed、cleanup_call_completed、wait_returned、exit_code_available；Popen不透明接口的terminate_api_succeeded/signaled_confirmed均null，exit_code_before_cleanup不冒充自然退出。既有error/errno/winerror和独立报告保留，无额外进程查询/终止。两QA直接消费方与实际报告回归断言同步，新根不进入业务凭据允许集。

当前报告语义勘误：下方旧raw字段completed=true、terminated_by_diagnostic=true和Popen final1，只证明当时后备调用正常返回及Popen返回码，不足以确认底层TerminateProcess成功、该句柄已signaled或主动终止因果。CPython3.12.10的terminate可在PermissionError后读取非STILL_ACTIVE码并返回；_wait在returncode已有缓存时不调用WaitForSingleObject。原受限终止句柄码5与后备返回码1并不构成“权限差异已证实”；旧机器记录不改写，错误5内部原因仍未知。

候选集合9函数/12选择器、源码静态计数31实例，未收集/未执行：新根与原owner/台账直接4；owned helper4；cleanup报告6；Popen四路4（success/error_exit/error_active/cached）；封闭字段和限量9；现有termination真实import/runpy的cleanup_success/cleanup_failure4。四路仅从已安装subprocess.py提取未改动Windows terminate/_wait的AST方法体，私有namespace+假句柄，不替换共享_winapi、Popen或observer；不执行真实False/True、业务或采样。静态通过后原计划唯一命令为原解释器 -B scripts/f009_step6_qa.py --cleanup-report-semantics-validation；本次未调用，未形成启动就绪凭据。

初次准备对两QA执行ruff format --no-cache（2 files reformatted），随后以下完整静态；cwd均功能worktree，解释器仍正式项目.venv，未安装/升级。准确命令：
1. `& 'E:\Agent\comprehensive-cases\15-cyber-town\.venv\Scripts\python.exe' -B -m ruff check --no-cache scripts/f009_step6_qa.py backend/tests/test_f009_step6_qa.py`
2. `& 'E:\Agent\comprehensive-cases\15-cyber-town\.venv\Scripts\python.exe' -B -m ruff format --check --no-cache scripts/f009_step6_qa.py backend/tests/test_f009_step6_qa.py`
3. `& 'E:\Agent\comprehensive-cases\15-cyber-town\.venv\Scripts\python.exe' -B -c 'import ast; from pathlib import Path; paths=[Path("scripts/f009_step6_qa.py"),Path("backend/tests/test_f009_step6_qa.py")]; trees=[ast.parse(p.read_text(encoding="utf-8"),filename=str(p)) for p in paths]; fixtures=[n.value.value for n in trees[1].body if isinstance(n,ast.Assign) and isinstance(n.value,ast.Constant) and isinstance(n.value.value,str) and any(isinstance(t,ast.Name) and t.id in {"PHASE_PRODUCT_FIXTURE","REPORT_PATH_FIXTURE","TERMINATION_REPORT_FIXTURE"} for t in n.targets)]; [ast.parse(s) for s in fixtures]; print("AST",len(trees),"files;",len(fixtures),"fixtures")'`
4. `$env:MYPYPATH='backend/src'; & 'E:\Agent\comprehensive-cases\15-cyber-town\.venv\Scripts\python.exe' -B -m mypy --no-incremental --cache-dir=nul scripts/f009_step6_qa.py backend/tests/test_f009_step6_qa.py`
5. 两仓分别 `git --no-optional-locks diff --check`；untracked两QA独立读取检查无尾空白，并与原100路径逐文件SHA比对。

结果：Ruff check=0；format-check=0（2 files already formatted）；AST=0（2 files、3 fixture字符串，未导入QA）；mypy=1；两仓diff=0。唯一错误为测试2358：Argument "body" to "Module" has incompatible type "list[FunctionDef]"; expected "list[stmt]" [arg-type]，list不变型。它是新回归AST容器类型适配问题，不是Win32/Popen运行失败；没有执行测试取得运行证据。本次完整静态初次1次；没有失败后修改或复验，没有消耗旧剩余准备额度。

未验证保存点73809585cf0b718a8231fc9a4c2f650110d2f348734317845f38a8946e247be5（原Ordinal path+NUL+小写SHA+LF算法）。脚本SHA0ea8b15e2482ca4af8f967cf33833070f94372dbd69508dad9121e7797e47617；测试SHAc533167f22f09cee7323b60452adefe55bdbf7a8a4e3450bdf8d33dd1a9a83d3。仅两QA变更，其余98文件及路径集合不变；kernel_api、StartupProcessAPI/StartupProcess、subprocess_isolation、validate_path实现正文逐段未变。两仓仍feat/f-009-safety-cost-performance/main、HEAD1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3、staged0、100/19变化。

资源最终仍2349文件237263969 bytes/18台账，全部旧资源长度/mtime聚合和18台账SHA不变；新批次不存在，新增资源0bytes、定向0/1、无本轮observer/PID/退出码证据。相关进程及8000/8001监听为空；四文档仅人工更新，未产生机器追加。evidence本轮编辑前118596bytes/SHA CC4D14C0C501B744A065EF590238FA405A9FE604E5A633188B1D161D8C62CA9A；本次无运行期可比，不能声称observer验证通过。全部旧证据保留不删除。

唯一下一动作待批准：将该局部AST节点容器明确为list[ast.stmt]并保持FunctionDef筛选，完整静态复验后才恢复尚未消耗的唯一定向；不执行真实子进程False/True或业务。不得以Any/cast/ignore掩盖该类型不一致。当前结束且停止，无自动恢复。

## 2026-09-09 异常收口控制流定向复验

接续42887026e94b6cc7a233b37c6e8a9b83399e5a2bf1b37da675cf8639d0d3a24d已核对。初次候选静态Ruff5处E501（测试1869/1870/2182/2204、脚本4889），format两文件需整理；AST两QA/三嵌入fixture、mypy两目标、diff通过。第1轮限定整理，并在源码复核中保留句柄关闭失败优先级，补关闭失败直接断言；完整静态五项全exit0。仅两QA变更，产品/Win32/权限/终止等待/owner/guard/observer规则未修改。

准确静态命令：解释器E:\Agent\comprehensive-cases\15-cyber-town\.venv\Scripts\python.exe，cwd E:\Agent\comprehensive-cases\15-cyber-town-f009；-B -m ruff check --no-cache及-B -m ruff format --check --no-cache，目标scripts/f009_step6_qa.py backend/tests/test_f009_step6_qa.py；原解释器-B AST parse两文件与三个既有fixture，不导入QA；MYPYPATH=backend/src，-B -m mypy --no-incremental --cache-dir=nul同两目标/原strict；两仓git --no-optional-locks diff --check。Ruff formatter仅两获批文件，非全仓修复。

设计/优先级：正常完成校验移出异常finally；business/launcher停止仍各原调用一次，原后者异常优先；句柄关闭异常保持收口失败优先，输出/双管道关闭/端口释放均一次，次生输出或释放错误不能替代既有观察/收口对象。局部cleanup事件写入失败延后标记evidence-status.json.reporting_complete=false，已有主异常保留且附固定incomplete提示，无主异常则失败；状态文件写失败也不能返回成功。状态文件不声称已完成正常验收。仍严格拒绝正常缺business、阶段或实际退出码，未知结果不补造。

CLEANUP_CONTROL_TESTS静态展开14函数/15选择器/61参数实例（非运行结果）：A test_cleanup_control_batch_contract、test_qa_batch_binding_cannot_switch_active_ledger、test_qa_batch_child_keeps_ledger_when_native_permission_is_revoked、test_qa_batch_prior_ledgers_are_read_only各1；B原test_startup_entry_reporting的health/health_failed/timeout/early_exit/business_error/launcher_error/both_error/observation_error/reader_error共9；C test_startup_entry_cleanup_failures的observation_cleanup/observation_output/observation_release/observation_all/release_error/output_release/close_error/observation_close/pipe_close_error/observation_pipe_close共10；D test_startup_entry_completion_requirements的missing_business/missing_phase/missing_exit共3；E test_startup_entry_evidence_failure的reporting_error/observation_reporting/cleanup_reporting共3，另test_startup_two_pipes_drain、test_termination_report_isolation各1、test_startup_report_module_source_rejection的file/spec/definition/termination共4；F test_startup_real_pytest_report_path的import/runpy×call/setup/forged/invalid/canonical共10，test_termination_real_pytest_report_path的import/runpy×call/setup/cleanup_success/cleanup_failure/state_failure/forged/invalid共14；G原test_startup_observe_actual_business_child[False]/[True]各1。上述选择器统一前缀backend/tests/test_f009_step6_qa.py::，不重跑159项，不修改原9参数或用新增覆盖替代实际子进程。

唯一运行命令：上述解释器-B scripts/f009_step6_qa.py --cleanup-control-validation，cwd功能根。复用真实父observer/受保护pytest、独立固定台账、路径逐项先登记；当前新根startup-cleanup-control-validation-01不存在，32MiB/ledger8MiB/observer8MiB/临时及子报告8MiB等限额，精确登记见current-task；新增evidence-status.json≤64KiB计临时总额。结果不接入startup_read_readiness允许集，直接反例核验拒绝。入口测试只用局部API/Popen替身及匿名双管道，合成PID10/20不是实际服务；F是受控预期失败子pytest，G才是实际本地Python synthetic子进程，不是FastAPI。

冻结eb3fbb50d45af35cb16221e89527300ff8d27a8ba5e01c6e5fd955b003df154f，原Ordinal路径+NUL+小写SHA+LF聚合；脚本d09418d0f0346a14f42b83ea803e7b10e857aef6c4442baea12333f022a9b0f8，测试3f6b4073e648b23f86c5e1015c10024c2dd81924d516a9760718b0edf9024e36。其余98项未变，两仓原分支/HEAD/staged0、100/19保持；旧2043文件236350366 bytes元数据与17台账SHA一致，无相关进程。运行前再核实冻结/新鲜度/原证据，运行期间四文档不改、机器只写新台账；运行意外失败立即停止，不修复重跑或补参数。准备修正1/2，定向0/1；所有业务额度0，不创建diagnostic05，不迁移旧授权。历史74项退出证据不记本轮结果。

本次最终运行（2026-09-09，保留前述运行前登记时序）：唯一--cleanup-control-validation已执行，runner/pytest exit1。固定14函数/15选择器静态预计61参数；实际报告60=59passed/1failed，未出现skip/xfail，True1项未执行；摘要未记录独立collected总数字，不将预计值冒充collect-only结果。A4、B9、C10、D3、E9、F24全部通过，第60项原test_startup_observe_actual_business_child[False]失败，phase=call，location scripts/f009_step6_qa.py:4187，-x停止，没有补跑True或修改代码。

控制流直接证据：原observation_error捕获同一预设异常对象，cleanup_completed=true，两个reader finish和两个管道close各一次，只有一条port_released，没有后续phase_evidence；reader_error保全6阶段/2位置部分输出，readers_finished=false、finalization_complete=false，原输出异常对象传播而非成功返回。10项叠加/独立失败验证主观察/停止/关闭/输出/释放优先级及单次操作；missing_business/missing_phase/missing_exit均按精确错误拒绝。取证写入失败3例的evidence-status.reporting_complete=false，无主异常时整体失败，有主观察/收口异常时对象不替换并附固定incomplete说明。各entry-report/<case>是API/Popen替身和实际匿名双管道，PID10/20为合成值；未启动FastAPI或Godot。单个output错误分别在reader和入口被记录，不代表reader重复finish；次数断言已通过。

F的10项身份/canonical与14项终止真实报告回归全部通过：正常import/runpy两加载方式，子pytest受控call/setup/收口/字段非法/伪造失败由父断言严格核验节点、退出状态和摘要；不是忽略外层门禁失败。这24项是本轮实际执行证据，不引用历史74项代替。阶段/角色报告隔离、来源拒绝、双管道排空和共享替身恢复直接检查均通过。

G False的实际本地Python子进程：business PID67212，parent57736，创建时间134334135958960300（100ns）；initial_binding身份，retained_query_handle最终alive=false、exit_code_available=true、final1、natural_exit_code=null、terminated_by_diagnostic=true、termination_attempted=true、termination_error_code=null。launcher PID57736，parent61892，创建时间134334135958878660，原已绑定终止句柄的TerminateProcess实际失败：win32_error5、stage=post_terminate_state、active_cleanup=true，after_alive=true、after_exit_code=null、available=false、state_error=none。attempt_ns及state_ns均538661781000000，分辨率内相同时刻不能据此推断内部先后竞态。异常经startup_termination_diagnostic及独立termination_observations完整保留，最终查询句柄退出码读取尚未完成。

随后原测试finally中的既有Popen句柄后备收口（不是本轮添加的新重试）：cleanup_report.pid57736/source=popen_handle/attempted=true/completed=true、terminated_by_diagnostic=true、final_exit_code1、failure_kind=none，收口前poll为null。该码只属于Popen句柄，不能代填launcher原查询句柄或自然退出码。实际True没有执行；历史74项False business72852/launcher26072 final1、True business9748/launcher28876自然/最终7仍只属于launcher-termination-report-validation-01。当前仅确认API拒绝事实及后备收口结果，不能凭码5断言权限差异、自然退出竞态或OS内部根因，更不是原connectivity超时复现。

父observer PID4208，与invocation/native-monitor-ready的root/ledger绑定一致；实际子pytest父链受原保护。native-summary已生成且排空marker存在，event_count2030、overflow=false、unknown_paths=[]、reparse0；completed=false因为外层测试失败。pytest boundary_violations={}、identity_diagnostic_rejections=[]、termination_diagnostic_rejections=[]。运行后无相关Python/Godot/QA残留或8000/8001监听，未处理无关进程；diagnostic05仍不存在。取证失败负例的局部reporting_complete=false是受控预设，不是父observer观察缺口。

资源最终306文件913603 bytes（<32MiB），ledger427023（<8MiB），observer三产物105173（<8MiB），其余临时/fixture/子报告362171（<8MiB）；恢复2349文件237263969 bytes（<2GiB）。旧2043文件236350366 bytes长度/mtime聚合C9E1519FF331E5111F062A2987C53C6759E1AD68527EA6447DEFC528172EAF71不变，17旧台账SHA逐份不变。代码运行前后聚合均eb3fbb50d45af35cb16221e89527300ff8d27a8ba5e01c6e5fd955b003df154f；两仓Git及100路径清单未漂移。

产物固定在E:\Agent\cyber-town-f009-step6-qa\recovery-20260905-01\startup-cleanup-control-validation-01：machine-ledger.md427023 bytes/SHA65FCBD6BA42F7DE18F5F99AD5CDE40C244BDE8FB7D4F5A7D464A0A14DE546764；invocation.json2482/SHA38F572DBE5B9EBB35F7FF52C52D53F1CC9D3673F6DAC03FFEC10A9B7F3C7C6EF；pytest-summary.json15374/SHA627D2166FB9786B54C022925BB712A4BF6C4C4CDEDE173C7798937373BDD08D6；termination-events.jsonl1380/SHA4F8F693D068354D15D53D493102E77DE038364D80A28159A485ECBD62C13C402；native-summary.json105028/SHA009217591B508795FB4B29CA0F355B9AB695CB67BAB51C2EABD7EB8C5B8DEF57。入口控制流细节见entry-report各固定case的timeline/phase/position/evidence-status；未额外创建不登记的分析资源。

四当前文档运行期大小/哈希完全不变，正式evidence运行前后112160 bytes/SHA682129B044C72FF0442B7F5A5C78E7B025954E5D54248F39E3BFADC95D75915C；机器未追加evidence，收尾才人工更新当前事实。初次静态与第1轮结果如上，准备修正1/2，唯一定向1/1已耗尽；剩余准备额度不能用于运行失败修复，未使用业务/性能/完整quality额度。

有限复盘：正常验收放在finally曾覆盖主错误并重复释放；本轮用异常对象/单次操作/真实报告通路的直接证据修正该控制流，不能据此推断真实Win32收口每次成功。相同launcher API失败再次出现时，应保留本次错误码与不同句柄的状态来源，不自动归因为竞态或靠重跑碰运气。唯一下一动作待审定：只读对照受限终止句柄与既有Popen后备收口的调用、权限和退出状态时序，先判断已有证据能否区分候选；不追加探针、放宽安全规则或恢复业务。定向整体未通过，step6_complete=false，结束本轮。

## 2026-09-09 启动入口报告接入与条件诊断


用户批准两QA和四当前文档、新就绪一次及条件启动一次。起点1aa2235c04155e593d10bdc909e03388ff7d04ae238d40087235698b55638511核实；两仓feat/f-009-safety-cost-performance/main、HEAD均1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3、staged0、100/19变化。恢复1963文件236104865 bytes/16台账已只读冻结，新就绪与diagnostic05均未创建、父链无reparse、无相关进程/8000或8001监听。diagnostic05本轮明确重新授权，非迁移旧额度。

代码仅两QA：新根/台账/六文件凭据/参数计数；各原stop调用外围有界报告，不改StartupProcess/Win32调用；异常时两reader排空、阶段/位置部分证据保存，完成验证标false，未知终止/最终状态不补造。原异常保留，输出整理失败另记；失败路径只补原端口释放检查，不追加终止。真实入口回归使用精确synthetic API/Popen与fixture返回替身，不启动业务；外层真实父observer和已安装审计/固定台账不替换。替身退出后恢复，原实际synthetic与真实报告子pytest仍按既有路径验证。

初次静态：Ruff F401未用导入1处，mypy9条（两处实例方法赋值、可空process读取、局部state与同名函数冲突）；format/AST/diff全0。第1轮局部修正完整静态全0，补凭据按函数参数数量核验。第2轮源码就绪复核修正模拟端口对业务绑定/读取线程先后依赖，补确切分类/双角色错误/部分证据断言，完整静态全0。无运行失败修复，准备2/2耗尽。准确命令：既有E:\Agent\comprehensive-cases\15-cyber-town\.venv\Scripts\python.exe，cwd功能根；-B -m ruff check --no-cache、-B -m ruff format --check --no-cache，目标scripts/f009_step6_qa.py backend/tests/test_f009_step6_qa.py；-B AST parse两QA和三个既有嵌入fixture（未导入）；MYPYPATH=backend/src，-B -m mypy --no-incremental --cache-dir=nul同两目标/原strict；git diff --check。格式化仅两获批文件，无全仓自动修复。

最终冻结42887026e94b6cc7a233b37c6e8a9b83399e5a2bf1b37da675cf8639d0d3a24d，原Ordinal路径+NUL+小写SHA+LF算法；仅两QA变化，其余98项及清单不变。QA脚本c63f509e196c732bbc1c14e5eed752db7361e863b5bb9c7917e4e33fcd2d3253，QA测试9aebceff7899b22927234982f3388cf66e3483607c93a3d730be03ef979651d1。旧资源元数据及容量复核无漂移。

固定REPORT_READINESS_TESTS为29函数/30选择器，AST参数展开159实例：凭据20、实际入口synthetic9、前置/阶段/产品入口stub/管道/分类及台账、直接终止/退出安全契约、原10+终止14真实报告子pytest、实际False/True各1。保留相关覆盖且去除重复选择器，不运行无关全量；159是静态展开预计数，待报告实际结果，未执行collect-only。预计最多46次子进程启动调用（外层1、上下文1、产品入口stub18、报告24、实际synthetic2）；新增入口9例只有API/Popen替身及OS匿名管道，不创建真实子进程。唯一就绪命令：上述解释器-B scripts/f009_step6_qa.py --startup-report-readiness。只有完整通过/observer完成/零拒绝/无漂移才允许同解释器--startup-report-diagnostic，凭据只读不重跑集合→五前置→一次FastAPI/原五秒/health最多一次。

资源精确预登记见current-task：startup-report-integration-readiness-01≤32MiB，connectivity-startup-diagnostic-05≤128MiB，台账各8MiB；固定产物与子fixture沿更小限额/操作前登记，新增≤160MiB、恢复≤2GiB。机器只进新批次台账，旧证据全部保留。运行意外失败立即停止，不修复重跑、不给旧额度续命；当前就绪/前置/启动/health均0/1，无quality/后续Godot/性能/Step7。

本轮最终执行结果（保留前述运行前时序）：唯一--startup-report-readiness已执行，runner exit1，pytest exit1，实际28项=27passed/1failed，无skip/xfail。20项凭据反例/正例、入口health/health_failed/timeout/early_exit/business_error/launcher_error/both_error共7项通过；第28项test_startup_entry_reporting[observation_error]失败，phase=call，failure_location测试2031（pytest.raises期待原RuntimeError的上下文）。固定159中剩余131未执行，含reader_error、既有真实报告子pytest和实际子进程False/True。只有外层受保护pytest启动调用，9个入口参数中的已运行者均API/Popen替身、匿名管道，PID10/20为合成值，不是FastAPI或实际业务PID。

直接证据：新根entry-report/observation_error/timeline.jsonl记录operation_failure/observation，随后launcher从原保留句柄路径取得合成final1/natural=null、cleanup_completed=true，business=null；output_preserved为6阶段/2位置、readers_finished=true、completion_validated=false，最后出现两条port_released。最后期望原错误的断言失败；pytest摘要未保存实际异常正文/完整栈，不补造错误消息。源码复核可见：观察异常的raise仍在外层finally中，内层收口finally补一次释放检查后，原后续释放/阶段验证仍继续执行；business为None会命中step6_startup_phase_identity_mismatch，从而可能覆盖原观察异常。此解释是已保存时间线加控制流推断，不声称额外运行捕获了该错误码。

business_error/launcher_error/both_error的timeline已分别保全受控TerminateProcess码5、post_terminate_state、business/launcher角色和原state after_alive=true；both_error同时保留两个操作失败及实例观察，最终两者退出状态未知、port_release_unknown，外层测试按预期通过。这些均为明确synthetic负例，不是历史终止失败重现。新入口原异常优先级仍有缺陷，不能把先行7项通过当完整报告链就绪；未执行的原真实报告通路保持历史结论，不虚构本轮通过。

父observer排空/关闭与库存文件已生成，native-summary completed=false（测试失败）、event_count499、overflow=false、unknown_paths=[]、reparse0；pytest boundary_violations={}、identity_diagnostic_rejections=[]、termination_diagnostic_rejections=[]。库存采样79文件217730 bytes不含最后摘要/登记；最终新批80文件245501 bytes，台账110015，全部固定文件/临时类别≤本批32MiB及各小限额，恢复236350366 bytes<2GiB。根保留不删除，diagnostic05仍未创建；8000/8001无监听，无相关Python/Godot/QA残留。没有处理无关进程，没有启动真实前置场景或业务。

产物均在E:\Agent\cyber-town-f009-step6-qa\recovery-20260905-01\startup-report-integration-readiness-01：invocation.json4046 bytes/SHA21BC21324900285DB0C66ECB0B87473E1BC907A4017DC8BDA1B6D04E8874B938；pytest-summary.json5969/SHAF547778FD30F5ABBE6BAD69A93957D993808189B47D9B7C4D718CA9E980F9491；native-summary.json27391/SHADD7B68012FEA4F7944A016A3170A4A1C763FCA95917EE9D3DB0ECD05788FD143；machine-ledger.md110015/SHAD7AC728CD2CCAB3AB599951FB93C9F1CF99EC676A3AA12F1D30994CF763E8F07。termination-events.jsonl为0 bytes，因为外层受控异常均由入口负例断言捕获，失败本身为原异常断言；取证正文在各entry-report/<case>/timeline.jsonl，不将空文件视为完整链路已通过。

运行前后聚合均42887026e94b6cc7a233b37c6e8a9b83399e5a2bf1b37da675cf8639d0d3a24d，原100项字节指纹全部相同。旧1963文件236104865 bytes的长度/修改时刻聚合与16台账SHA完全一致；四当前文档运行期大小/哈希完全相同，evidence102865 bytes/SHA6D94282ECBE15C31332F19B1F1A1CCB9B62A7E2D08DB3EA6730C993C62733E1E。机器未追加正式evidence，收尾才人工更新。本轮准备2/2、独立就绪1/1；五前置/FastAPI/health0/1未使用且不迁移、不自动解锁；无quality/后续Godot/性能/Step7，失败后未修改代码或复跑。

简短复盘：此次不是Win32新故障，而是入口嵌套finally报告适配仍未覆盖“主观察失败、收口成功”的异常优先级；只验证字段存在不足以证明异常贯通。最小下一动作待审定：保持原进程调用/身份/权限，明确主失败、收口失败、证据整理失败的职责；失败路径完成一次有界整理/释放检查后不得再落入正常阶段校验或覆盖原错误，并直接覆盖本次失败组合。不追加同类探针、不为缺日志重启业务。暂停保留，下一修复与验证需新的明确授权。

## 2026-09-09 launcher终止失败报告补齐

用户批准两QA及四当前文档；新增来源核验的StartupTerminationError(OSError)，保留errno/原拒绝条件。stop只把原terminate返回码和原state复查结果/时间写入实例标量；state复查异常原样传播，已采集码保留。Reporter与最终摘要按封闭字段/大小/来源/节点阶段验证；原实际测试finally记录两个绑定对象观察后，薄适配按原poll→startup_stop_owned路径记录Popen收口，不增加查询/终止/重试或改变关闭顺序。主终止失败和收口失败分别保存，后备收口未取得时final码和terminated状态为未知；exit_code_before_cleanup仅是Popen原观测，不冒充自然退出。

初次静态：Ruff E501一处、mypy两处类型收窄错误，format/AST/diff通过；第1/2轮完整静态全0。源码复核补5个cleanup schema负例作为第2/2轮，最终Ruff/checkformat/AST/mypy/diff全0，准备额度2/2，运行0/1。工具准确为E:\Agent\comprehensive-cases\15-cyber-town\.venv\Scripts\python.exe，cwd E:\Agent\comprehensive-cases\15-cyber-town-f009；-B -m ruff check --no-cache、-B -m ruff format --check --no-cache，两个目标scripts/f009_step6_qa.py/backend/tests/test_f009_step6_qa.py；原解释器-B AST parse两QA与REPORT_PATH_FIXTURE/TERMINATION_REPORT_FIXTURE（未导入）；MYPYPATH=backend/src，-B -m mypy --no-incremental --cache-dir=nul两QA/原strict配置；git diff --check。初次formatter及两轮formatter仅获批文件，无全仓修复。补丁匹配失败未改动目标、未运行验证，不作为额外执行轮次。

冻结1aa2235c04155e593d10bdc909e03388ff7d04ae238d40087235698b55638511，起点4827a57ef8fe3793870911e9175a76885c6f73cec136f3474086ef1aa45ea23d。沿原100项Ordinal路径/NUL/小写SHA/LF算法，仅两QA变化，其余98项哈希不变，无清单新增/删除。QA脚本SHA4EA88889C44D9554A2D806A88CA0FD3D1E6F6D4B6435D84C1C80D1A9972BDF7C，QA测试SHAAD8D023B4801F26FC7D6023FB112DE9CE7E39C355FA677463E2A75C6C7C633D8；两仓分支/HEAD/staged0及100/19变化保持。旧1907文件235845973 bytes/15台账冻结，新根未创建、父链无reparse、无相关并发进程。

固定TERMINATION_TESTS为18函数/19选择器，AST展开预计74实例（不是运行/collect-only）：根owner1、三台账/环境各1、即时码2、终止分流4、退出状态4、身份变化2、退出后/别名4、初始绑定拒绝5、收口6、终止schema7、收口schema5、报告隔离1、来源核验4、原真实身份/canonical报告10、新真实终止报告14、原实际synthetic False/True各1。顺序A直接契约→B真实报告链→C两个实际Python子进程；报告子pytest预期失败由父断言核验，C意外失败不可改称预期。最多28次子进程启动调用：外层pytest1、上下文1、报告24、实际synthetic2；非业务服务。

唯一命令：上述python.exe -B scripts/f009_step6_qa.py --launcher-termination-validation；同功能cwd。新根launcher-termination-report-validation-01≤32MiB，独立台账8MiB、termination-events/pytest-summary各1MiB、invocation64KiB、observer8MiB、fixture/临时8MiB及原更小输出限额；恢复总≤2GiB。根/ledger精确预登记见current-task，固定初始化及每个fixture/子报告由guard操作前逐项登记。运行不改代码/文档、不写旧台账；任一意外失败/缺字段/边界/漂移/超限即停止，不重跑或启动业务，旧资源全保留。

最终运行结果：上述唯一命令已执行1次，exit0，实际摘要74passed/0failed、无skip/xfail，18函数/19选择器与冻结清单一致。没有独立collect-only；74为实际结果行数量。A直接契约通过，原即时错误码不被后续覆盖、终止状态复查次数/身份保护/别名关闭与未知状态断言通过；B原10+新增14个真实报告子pytest通过父断言，含正常导入/runpy、call/setup、不串项、同名伪造/非法字段拒绝、大小限制、原canonical/身份保留。子pytest的已知负例分别exit1或非法字段exit3，不是外层吞失败。

新增底层采集→异常/实例观察→MetadataReporter→最终摘要链路证据见新根termination-report/{import,runpy}/{call,setup,cleanup_success,cleanup_failure,state_failure,forged,invalid}/pytest-summary.json。例如runpy/cleanup_failure同时保存受控TerminateProcess码5、launcher/termination、post_terminate_state/after_alive=true，以及Popen后备收口errno5、completed=false、final码/terminated状态未知；runpy/state_failure保留原state错误分类及终止码5、after_alive=null，不将查询失败当通过。这里码5均为synthetic注入，不能推断历史真实错误码也是5。限量事件留新台账及子摘要，不输出异常全文/配置/局部变量。

原实际synthetic False：business72852（父launcher26072，创建134334081832820996）、launcher26072（父57884，创建134334081832712106）各自initial_binding/retained_query_handle确认final alive=false/code1/available=true，natural=null、terminated_by_diagnostic=true，终止调用均成功、error=null。True：business9748（父28876，创建134334081835632004）、launcher28876（父57884，创建134334081835544228）各自自然码和最终码7，无主动终止。两个finally额外报告均来自原Popen观察，收口attempted=false/completed=true、原码分别1/7；此处terminated_by_diagnostic=false只表示本次后备收口没有再发起终止，不覆盖前面原保留句柄的主动终止证据。本次没有真实终止失败，不能关闭历史Win32原因或原connectivity。

新批次证据根E:\Agent\cyber-town-f009-step6-qa\recovery-20260905-01\launcher-termination-report-validation-01，完整保留56文件/258892 bytes：machine-ledger.md=95463 bytes/SHAA59C34B1C0A961D33AA1CA0CC4F505414468B7916854473837A1F0FE5BF31C8B；pytest-summary.json=20025/SHAE193018FF9B9C4E6597446D60616FD29927102291EA5C23E2A5A3AD822C1FCAB；termination-events.jsonl=873/SHA8DA086404853413647DD07D2CC2275F2A7399F4A85B1D8E1FC53ECC634070B38；invocation.json=2828/SHA41A303C57920D4097E1CC6FA2B2000A55D10A7E46E1D17917631F0C2AA5CD8E9；native-summary.json=20162/SHA44F54CE383F640225AB14FFFEA5C7428977DCCE74FEFE430B629EC84899BA036。各产物/临时和批次限额通过，恢复总236104865 bytes<2GiB。父observer completed=true、event_count455、overflow=false、unknown_paths=[]、reparse0；外层boundary_violations={}、两类diagnostic_rejections=[]。库存采样238348 bytes/55文件不含最后摘要和登记，最终盘点56文件。

运行前后冻结均1aa2235c04155e593d10bdc909e03388ff7d04ae238d40087235698b55638511，旧1907文件235845973 bytes元数据及15旧台账SHA全部相同，两仓原分支/HEAD/staged0和100/19保持。四当前文档运行期哈希/大小不变，evidence运行期95975 bytes/SHAFF952688A08A989AA38E754572539419087C8ACCD8D0D4C7834524B032324049；收尾才作人工摘要更新，机器没有追加本文件。相关进程及上述四PID均无残留，8000/8001无监听，diagnostic05未创建。准备修正2/2、唯一直接回归1/1；FastAPI/Godot/connectivity/quality/性能均0，不迁移旧额度，不自动继续。

本轮仅可表述为“终止失败与收口报告补齐并通过直接验证”。取证新增标量/时间记录可能影响终止窗口，本次未复现不能否定历史失败；重复错误的报告缺口已覆盖，但OS内部原因与首次失败是否同因仍未知。唯一下一动作待另行审定：是否将已验证报告能力用于恢复一次受控启动，须明确新的接入/就绪要求及运行额度；本轮不接入业务诊断、不新增批次、不自动关闭故障。

## 2026-09-09 composition 调整后受控启动接入



只改两QA：新根/固定台账/历史只读来源、精确就绪清单及六文件凭据接入。产品composition、api入口和两产品测试保持原字节；未改观察/审计/权限/收口/超时。新根及子资源类别创建前登记见current-task，运行机器仅写各自独立台账。当前初次静态全0，失败后静态修正0/2；独立就绪、五前置、FastAPI、health均0/1。

准确静态：解释器 E:\Agent\comprehensive-cases\15-cyber-town\.venv\Scripts\python.exe，cwd E:\Agent\comprehensive-cases\15-cyber-town-f009；-B -m ruff check --no-cache、-B -m ruff format --check --no-cache，目标 scripts/f009_step6_qa.py backend/tests/test_f009_step6_qa.py；原解释器-B AST parse两QA及嵌入PHASE_PRODUCT_FIXTURE/REPORT_PATH_FIXTURE（未导入模块）；MYPYPATH=backend/src，-B -m mypy --no-incremental --cache-dir=nul 同两目标/原strict配置；git diff --check均exit0。初次格式化仅获批QA测试文件，未消耗失败后修正；源码复核诊断配置与当前运行根分离，保留安全语义。

冻结由9a297637d9c91e2eea847b3852c0862fcce43e46fc24b6e1b4bc9b34658584aa变为4827a57ef8fe3793870911e9175a76885c6f73cec136f3474086ef1aa45ea23d。沿原100项Ordinal路径+NUL+小写SHA+LF聚合，仅两QA变化，其余98项无漂移、无新增/删除清单项；两仓分支/HEAD/staged0不变。旧1843文件235512054 bytes及14台账已内存冻结供运行后核验。

固定COMPOSITION_STARTUP_TESTS为18选择器/17函数，AST展开预计94参数化用例：新凭据18、根owner3、上下文5、三台账/子环境各1、阶段报告8、实际产品入口stub18、脱敏8、限量/双管道各1、分类6、前置stub6、模块位置1、真实报告通路10、退出契约4、实际synthetic False/True各1。最多32次子进程启动调用：受保护pytest1、上下文1、入口stub18、报告10、实际synthetic2；这些不启动真实业务服务。受控子pytest负例必须由父断言核验，不能掩盖外层意外失败。不重复上轮33或历史222集合。

唯一就绪命令：上述python.exe -B scripts/f009_step6_qa.py --composition-startup-readiness。仅全部通过、父observer完成/边界0/指纹不变后，执行唯一条件命令：同解释器/cwd -B scripts/f009_step6_qa.py --composition-startup-diagnostic；只读取就绪凭据不重跑集合，然后原五前置→端口8000/8001空闲→一次FastAPI/原五秒/health至多一次→收口。新根composition-startup-readiness-01≤32MiB、connectivity-startup-diagnostic-05≤128MiB，各台账≤8MiB、更小产物限额不变，新增≤160MiB、恢复≤2GiB。任何意外失败停止，不修复后重跑或转入完整验收。

本轮最终结果（上述0/1为运行前记录，保留时序）：唯一就绪命令exit1；固定预计94实例中摘要实际执行93，92passed/1failed，无skip/xfail。最后[False]失败后-x停止，[True]未执行，不补跑。新根/凭据/阶段stub/10项真实报告通路/退出替身等先行92项全部通过，但不能据此声明本轮就绪通过。pytest摘要不另含独立收集数量字段，94是冻结清单静态展开数，不冒充额外collect-only结果。

失败node为test_startup_observe_actual_business_child[False]，phase=call，failure_location脚本3985。已记录business PID66508、parent launcher25556、creation100ns=134334058603297051；initial_binding身份，retained_query_handle最终alive=false/exit1/available=true，natural=null，主动终止/attempted=true、termination_error=null。测试1782完成business.stop并于1786写入上述metadata，1787随后launcher.stop；结合3985分支可确定launcher的TerminateProcess返回失败且原查询句柄复查alive=true，尚未进入launcher最终wait/状态记录。该OSError的Win32错误码及launcher最终退出码未进入既有摘要；不能用business码或外层runner码代填，更不能归因为自然退出竞态/权限不足。不是之前QueryFullProcessImageNameW错误31，也不是原connectivity超时复现。identity-events为0 bytes仅因该错误不是身份异常，暴露终止失败取证链仍有缺口，不能改称未发生失败。

父observer已执行drain/close并产出库存，但native-summary completed=false（会话内测试失败，不等于observer成功门禁）；event_count463、overflow=false、unknown_paths=[]、reparse0，pytest boundary_violations={}、identity_diagnostic_rejections=[]。无边界违规记录不能消除上述观察/退出码缺口。测试finally沿既有持有Popen对象的收口，运行后只读检查无66508/25556或其他相关Python/Godot残留，8000/8001无监听；现态不能补造launcher退出码。

产物根E:\Agent\cyber-town-f009-step6-qa\recovery-20260905-01\composition-startup-readiness-01：pytest-summary.json=20258 bytes/SHA70D920234B49C444A8DA607FC52C6F8C7F1F5CB3B6DAEB68242503F7D7EE42DB；invocation.json=3047/SHA00F53B59E8F4D9F90273D7DC48B3840EBCB50B99402B235ABC03B2D88BB96552；native-summary.json=21892/SHA59758B7447EDC2342EDA9D7A519E66D624B421AB929D74B41E41D7C3A4F2F865；machine-ledger.md=93247/SHA189A24F4A7E7BD5EAE42765B69F5504D5839EC0C0DFC03D0E408FDC52FCFFB81。原始失败批次完整保留，批次64文件/333919 bytes，低于32MiB和各产物限额；恢复总235845973 bytes<2GiB。旧1843文件元数据/235512054 bytes及14旧台账哈希全部不变。

运行前后代码聚合均4827a57ef8fe3793870911e9175a76885c6f73cec136f3474086ef1aa45ea23d；两仓原分支/HEAD/staged0、100/19既有变化保持。四当前文档运行期大小/哈希全部不变；evidence运行期87454 bytes/SHA95E6FA0E6E88FC4D4D8F353DB7AD2F4F397732A757F838497DAF68BF26840DF4，机器只进新台账，当前这段为完成后人工摘要。静态修正0/2、唯一就绪1/1已耗尽；五前置/FastAPI/health均0/1且条件未满足，不迁移、不执行，diagnostic05未创建。无quality/后续Godot/性能/Step7。

唯一下一动作待审定：仅为已复现的launcher终止失败补齐即时Win32错误码、角色/阶段、保留句柄存活与最终收口结果的有界报告，再以直接终止负例和原[False]验证；不修改终止权限或拒绝条件、不重跑本批、不给业务启动解锁。简短复盘：同类终止错误再次出现，当前身份异常白名单链不覆盖终止OSError，导致能定位分支却不能解释系统拒绝原因；以后先验证这条具体错误的最终报告通路，再决定是否恢复业务诊断，不再用大就绪集合反复寻找该错误。建议落点限两QA及当前证据，不修改全局规则；历史首次终止错误仍不能自动认定同因。

## 2026-09-09 composition 导入调整（33项通过，已收口）

用户本次批准composition.py延后唯一DeepSeekProvider导入、两个原测试构造替换目标适配及直接回归，两QA仅新根/固定清单/指纹与调用接入。disabled和注入fake不再提前触发SDK导入错误；配置拒绝、SDK参数、构造/导入异常传播和安全机制保留。不是原connectivity已确认根因修复，不增加采样、不启动服务。

初次静态全0：正式既有.venv/Scripts/python.exe -B -m ruff check --no-cache、ruff format --check --no-cache；-B AST parse五文件及COMPOSITION_IMPORT_CHILD（未导入）；-B -m mypy --no-incremental --cache-dir=nul，MYPYPATH=backend/src，原strict配置。五目标为backend/src/cyber_town/api/composition.py、backend/tests/test_deepseek_provider.py、backend/tests/test_long_term_dialogue_integration.py、scripts/f009_step6_qa.py、backend/tests/test_f009_step6_qa.py。初次准备格式化仅一个获批测试文件，其余4无格式变化；失败后静态修正0/2，运行0/1。git diff --check exit0。

保存点由52a31b1f2563b7d2e4d17e6b6346d04c484232d0d19b2a8773fdc3308bbfa6b1变为9a297637d9c91e2eea847b3852c0862fcce43e46fc24b6e1b4bc9b34658584aa；原100项中仅批准5文件变化，其余95哈希不变，无新增/删除清单项。两仓分支/HEAD/staged保持原值。旧1811文件/235011400 bytes元数据及13份既有台账已内存冻结，运行后只读对比。

固定COMPOSITION_TESTS为17个节点选择器、16个函数，预计33个参数化用例。顺序为新根/owner/台账、报告与退出契约、导入/构造/配置及原两个受影响测试、实际synthetic退出两分支。最多17次子进程启动调用：受保护主pytest1、上下文继承子进程1、报告负例子pytest10、新鲜导入子进程3、实际退出子进程2；Windows launcher/business属于同次调用的不同OS进程，不混淆数量。报告负例严格断言exit1或指定invalid场景exit3，不能将其他失败视为预期。产品FastAPI/Godot/connectivity/quality/性能次数全部0。

唯一运行命令（已执行一次，exit0）：E:\Agent\comprehensive-cases\15-cyber-town\.venv\Scripts\python.exe -B scripts/f009_step6_qa.py --composition-validation；cwd E:\Agent\comprehensive-cases\15-cyber-town-f009。入口复用run_identity_validation/native_session/原真实父observer；新根composition-import-validation-01为32MiB、台账8MiB，其他更小限额沿用，创建前预登记见current-task。invocation、pytest-summary、identity-events、native-summary和machine-ledger均进入该独立根；不写旧台账、不向本文件追加机器事件。

实际收集/执行33项全部passed，无skip/xfail/意外失败，16函数/17选择器与冻结清单一致。新鲜disabled、injected、import_error子进程分别exit0；前两者在安装精确SDK导入阻断器前确认模块不存在，后确认无导入尝试；后者明确捕获原ImportError且验证来源/消息，未吞异常。三个配置拒绝和构造参数/同一异常对象传播通过；两个原受影响测试及离线路由通过。10个真实报告通路子pytest按预期exit1或invalid专例exit3，由父回归严格核验，不是外层忽略失败；最终identity_diagnostic_rejections=[]、boundary_violations={}。identity-events为0 bytes因为外层没有身份失败，不表示负例报告链缺失，其证据在report-regression子摘要。

实际synthetic False：business63660/parent launcher14136，launcher parent14352；两者分别由原查询句柄确认final alive=false/exit1/available=true，natural=null，主动终止true，无termination错误。True：business60456/launcher19328，launcher parent14352；两者final exit7/natural7，无主动终止。创建时间和身份来源分别保留pytest-summary.metadata，不使用launcher码代填business。收尾只读进程核对无相关残留，8000/8001无监听。

批次原始证据根：E:\Agent\cyber-town-f009-step6-qa\recovery-20260905-01\composition-import-validation-01。pytest-summary.json=11830 bytes/SHA28CC3BBC91348F8DD5077F30CF2F05919B5520090FB59F828FAAF3A81C089AEB；invocation.json=3302/SHADEF18B9E3E0C291F47CEF444570DB06BA06785F9C84CD3643856F2DFCAB47E48；native-summary.json=11227/SHA6598BA8F221589FFA4DF59153FE370391B3B383E51A84728111182C174E8FB1F；machine-ledger.md=75194/SHAD19A89AEF660B164F63FD77E0BD11ADB84A513B310C7E5C14A3A24CC21C41B1F。observer completed=true、event_count536、overflow=false、unknown_paths=[]、reparse0；其库存采样489054 bytes/31文件不含最终摘要及末次登记，最终含隐藏文件盘点32文件/500654 bytes，低于全部限额。恢复总235512054 bytes，旧1811文件/235011400 bytes元数据及13旧台账SHA全相同，无删除或重写。

代码冻结9a297637d9c91e2eea847b3852c0862fcce43e46fc24b6e1b4bc9b34658584aa运行前后一致；四当前文档运行期均相同，evidence=81915 bytes/SHAB03C6D13AB195D39A92BF8B9A2BF492939C5ABEB7D032A3104F58E05D73FDB5E。本段为完成后人工摘要，未增加机器写入来源。额度最终：静态修正0/2，唯一回归1/1；新鲜导入3、报告子pytest10、真实synthetic退出2分支均已执行；业务启动及完整验收0。成功只证明产品导入依赖调整和直接回归，下一项受控启动须另行批准，不能自动关闭connectivity或Step6。

## 2026-09-09 阶段观察与diagnostic04（已收口）

代码仅api/__main__.py及两QA：六个默认关闭的固定阶段事件、原线程两次定点采样、严格字段/限量/错误识别、新根与三文件receipt接入及直接回归。未改产品功能、进程权限/身份/等待/owner/路径/observer规则。既有合法测试根和诊断目的根分开；配置参数证明不是历史quality执行证明。

| 准备阶段 | 结果及依据 |
| --- | --- |
| 初次静态 | Ruff exit1：5处E501、两处相邻zip触发B905/RUF007共4项；format/AST/diff exit0；mypy exit1：3340 binding返回Any/no-any-return，无INTERNAL ERROR |
| 修复1 | 长行/pairwise/严格字段适配后完整静态全0；冻结ccc046bfe124e2db8455a5183d2abb0e5483d864bc6f755b7f4197e7f91cb363；[readiness01摘要](../../../../cyber-town-f009-step6-qa/recovery-20260905-01/startup-phase-readiness-01/pytest-summary.json)为217passed。随后源码复核发现synthetic根仅限readiness、未来合法quality上下文会误失败，阻断真实运行 |
| 修复2 | 根配置选择与实际owner/台账分离、增加5配置参数；完整静态全0，[readiness02摘要](../../../../cyber-town-f009-step6-qa/recovery-20260905-01/startup-phase-readiness-02/pytest-summary.json)为222passed/37函数；原184覆盖全部保留 |

上述相对资源链接仅作索引，准确权威产物根为E:\Agent\cyber-town-f009-step6-qa\recovery-20260905-01（不是功能或正式项目内的副本）。两就绪入口分别为正式.venv/Scripts/python.exe -B scripts/f009_step6_qa.py --startup-readiness 01/02，cwd功能worktree；真实诊断命令同解释器 -B scripts/f009_step6_qa.py --startup-diagnostic 02，02只选择已完成就绪凭据，运行根固定connectivity-startup-diagnostic-04，synthetic_rerun=false。命令和完整固定用例清单保留各批invocation.json，结果保留pytest/native摘要及独立machine-ledger.md。

完整静态准确设置：上述解释器 -B -m ruff check --no-cache、-B -m ruff format --check --no-cache；AST parse不导入三文件并解析两嵌入fixture；-B -m mypy --no-incremental --cache-dir=nul，MYPYPATH=backend/src/strict原pyproject配置；目标始终scripts/f009_step6_qa.py、backend/tests/test_f009_step6_qa.py、backend/src/cyber_town/api/__main__.py，git diff --check及全清单指纹核对。修复2/2已用，独立就绪2/3；第三根未创建，不可无改动重跑。

18个真实产品入口stub子pytest、10个原报告通路组合、访问/引用释放/上限/缺失/错误和退出句柄回归通过。真实接口在synthetic中两次触发原审计hook无违规；替身只证明上层不枚举/不读禁止字段，不声称底层接口只获取单线程。原False/True实际本地synthetic两分支最终码分别1（主动、natural=null）/7（自然），不是FastAPI结果。两个就绪observer均完成且边界0；01为435695 bytes、02为436717 bytes。

真实诊断：五前置按原顺序和请求/拒绝断言全部通过，端口空闲后业务启动一次；Popen返回t=525665.171、原deadline=525670.171。20次TCP探测均false，最后完成t=525670.281，结果listen_timeout在525670.328；未延长期限，原探测/sleep粒度使完成记录略越deadline。health没有执行。

| 阶段/观察 | 单调时间与含义 |
| --- | --- |
| wrapper_entered/线程绑定 | 525665.296；实际业务PID47380、ident/native_id23576 |
| composition导入前 | 525666.171，等待起点+1.000s |
| composition导入返回 | 525670.250，导入区间4.079s，起点+5.079s |
| main进入、Settings返回、组装前、uvicorn.run调用前 | 均记录525670.250；六阶段全部出现，但相同时间戳不证明耗时为零，也不证明Uvicorn已启动或监听 |
| 采样1 | 计划/实际525666.796；目标顶层python/Lib/importlib/_bootstrap_external.py:1190 |
| 采样2 | 计划525668.796/实际525668.843，偏移47ms；同一白名单源码行 |

两个槽均实际执行，late=false按实现100ms分类阈值，不隐去47ms偏移。已核对既有CPython3.12.10对应Lib/importlib/_bootstrap_external.py:1190为with _io.open_code(str(path)) as file。没有读取frame局部变量或原始文件路径，不能判断两次是否同一文件/调用，不能把它解释为连续阻塞2秒或磁盘/Windows/SDK已定因；也未量化审计/观察开销。最后可证完成为Settings与服务组装，最后标记是uvicorn.run调用前；Uvicorn内部初始化/监听暂无完成证据。

launcher35656（父29108）与business47380（父35656）经原OS/保留句柄绑定；观察期均alive，随后主动收口。各自原查询句柄final alive=false/exit1/available=true，natural=null、termination_attempted=true、termination_error_code=null；不以启动器值代填。process_closed=525670.359、port_released=525670.562，外部只读核对无相关残留、8000/8001无监听。

证据目录connectivity-startup-diagnostic-04：phase-events.jsonl675 bytes/SHA DB8C2A45E01645051644BA6EC55AB7EF45FDC567E19044A3F9795721FEEA686E；position-events.jsonl442/SHA76A246630729055A88B7E88BEA72C4B361A6F90E43E39299120BAB322D1B985C；timeline.jsonl9133/SHA EBC7E62A602695C9F4AF07CC3CEF3ABB233C26D9DE62D29FBDCFB49FB22D82F3；其余准确命令、安全配置、前置、模块来源与输出见invocation/preconditions-summary/stderr-redacted。stderr2657、stdout0、dropped0；native-summary completed=true/event_count36/overflow=false/unknown_paths=[]/reparse0，guard违规0。阶段/采样归属及报告链完整通过，缺失的wrapper_finished是主动结束所致，不伪造业务自然返回。

最终代码聚合52a31b1f2563b7d2e4d17e6b6346d04c484232d0d19b2a8773fdc3308bbfa6b1运行前后相同；三文件SHA分别product9a3957f67f084cdd233a87d4b92c24d53db0c4d9b66d94477b972a436be1800a、script cc49d7e1571d6f2baed3593b267baa346c85038a0d402a108f6f92d0dec822fc、test0a14d50d359c122a2e6268a980a7d163f60528ba089dcda3fc9f6167c6ca2e88。feature原分支/main原分支，HEAD仍1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3，staged0，100/19变化；其余97项既有变更按原算法核对不变。

全部含隐藏文件盘点：旧1585文件/233970372 bytes及元数据SHA A2ECB2BE1761D0D90B6F8C98E697EE33BBEC554927B96AF7DB7E0A9AC2BC35A8不变；诊断前12台账SHA运行后不变。新增三批共226文件/1041028 bytes（435695+436717+168616）；恢复1811文件/235011400 bytes，低于各批/新增224MiB/总2GiB。machine-ledger分别142499/142499/25958 bytes，均<8MiB；全部保留，无删除/清理。正式evidence真实运行前后75599 bytes/SHA C1CDFA0F15B0F96EA6F5BC7F370A30C7E8E653FF75B5638669A684EA56D6E0FC，四当前文档运行期均未变；本段仅收尾人工更新，不接收机器追加。

本轮五场景1/1、FastAPI1/1、health0/1、真实位置采样2/2；无quality/后续Godot/性能/Step7。与native-quality03不同：当前QA/产品观察版本、新缓存和台账、观察与句柄开销、独立就绪编排且未重跑六工程门禁。因此只定位本次导入预算区间，不关闭原connectivity或旧TerminateProcess未知原因。唯一下一动作待批准：只读评审composition传递导入与open_code/open审计链，选一个最小有判别力的修复或对照方案；不自动加探针、启动或优化。

## 2026-09-08 connectivity 受控诊断03（已收口）

真实入口仅一次：正式既有python.exe -B scripts/f009_step6_qa.py --startup-diagnostic 01，功能cwd；01只指向已完成readiness-01，真实写入根固定diagnostic-03。入口核验invocation/pytest/native/owner四文件的内容及SHA、当前代码/完整集合/边界与observer完成，synthetic_rerun=false。五场景按stopped_service→unavailable→duplicate_rejected→non_string_rejected→redirect_rejected原序各一次，原请求计数/拒绝/fixture收口全部通过，子场景runner exit0。8000/8001空闲后才启动一次原业务命令；没有后续connected/recovery/Godot回环或其他验收。

诊断结果为listen_timeout，顶层runner exit0仅代表取证与安全收口完成，不代表产品通过。Popen返回起算t=453299.156，固定deadline=453304.156；20次原TCP探测均false，最后探测完成t=453304.265，超时分类t=453304.312。探测/原循环sleep粒度导致完成时间略过deadline，代码未延长5秒期限。health实际0次。监听期间业务与launcher保留句柄状态均alive（首次探测业务尚未绑定）；无自然提前退出证据。

| 角色 | 已核验身份 | 最终状态与来源 |
| --- | --- | --- |
| launcher | PID73516/parent61892，创建134333282335290331；正式.venv启动映像 | 主动收口前alive；原保留查询句柄确认alive=false、exit1/available=true；natural=null，termination_attempted/terminated_by_diagnostic=true，error=null |
| business | PID14780/parent73516，创建134333282335421970；正式.tools既有Python映像 | 主动收口前alive；其独立原查询句柄确认alive=false、exit1/available=true；natural=null，termination_attempted/terminated_by_diagnostic=true，error=null |

历史绑定身份标为initial_binding，最终状态来源retained_query_handle；不得把主动终止码1解释为启动崩溃码。t=453304.640记录收口，453304.843确认8000释放；外部收尾也确认两个PID/父runner及相关进程无残留、8000/8001无监听。无失败API/Win32错误记录，未知值没有用另一进程填补。

已记录wrapper_entered/configured/owner_verified/guard_active/module_entry；10个目标模块均观察到，业务模块来源feature/backend/src，FastAPI/Pydantic/Settings/Uvicorn来自既有venv。composition首次在t=453300.468出现。仅观察sys.modules已有对象，不额外导入；这不证明模块顶层执行完成，也没有main进入/Settings完成/build_dialogue_service返回/uvicorn.run进入的分段证据。stdout0 bytes，脱敏stderr1433 bytes，dropped_lines=0，无已记录异常或Uvicorn生命周期；不声称存在可恢复原始日志。源码__main__.py显示Settings→build_dialogue_service→uvicorn.run，disabled配置在composition函数内直接返回None，但现有时间线不足以证明已执行到该返回。较支持“仍处于监听前初始化/导入区间”的候选，不足排除该区间不同步骤或未记录监听内部故障。

与原native-quality-03不完全等价：本轮QA含保留句柄与诊断观察、独立就绪批次；新缓存/台账和隔离game；新增流式脱敏/模块采样/身份观察开销；父子编排通过定向入口而非完整quality子链；未重跑前六工程门禁。MYPYPATH只用于静态类型检查，运行时来源由本次已加载模块证据确认。本次只复现超时表象，不能证明原失败相同内部原因。第1轮历史TerminateProcess原因仍未知，本次没有该失败；不另开支线。

证据：[diagnostic-03 timeline](../../../../cyber-town-f009-step6-qa/recovery-20260905-01/connectivity-startup-diagnostic-03/timeline.jsonl)、同根preconditions-summary.json、invocation.json（业务/包装命令、cwd、安全配置与readiness引用）、stderr-redacted.txt、native-summary.json、machine-ledger.md。observer completed=true/events29/overflow=false/unknown_paths=[]/reparse0，guard boundary={}；game源/副本哈希复核通过。42文件/161951 bytes，ledger25194 bytes/SHA256 9F1B0088DC0C6C34E251C92A47005DBE12722DC5BF1F1889DAEDE2A4D1E70B7C；timeline7241 bytes/SHA256 D19493ECE009463FD206E089D346339F17DBFC238FFCF4CABBC0D3A462AFFD96，observer三产物合计17721 bytes，均低于各限额。pytest-summary未创建，因诊断不重复pytest。

本轮新增373080 bytes（约0.356MiB）/97文件；恢复1585文件/233970372 bytes（约223.132MiB），低于各批32/128MiB、新增224MiB及总2GiB。两后备readiness根未创建。代码冻结584a20f1…d861bfdc运行前后相同，其余97项无漂移；两仓原分支/HEAD/staged0及99/19变化保持。八旧台账SHA和旧1488文件元数据聚合不变，就绪ledger与四份输入证据也不变。正式四文档真实运行期大小/哈希均不变；evidence从运行前66436 bytes到运行后仍66436 bytes，SHA256 B0EFA252F0EBE30DF1FD7A64D47D364CD75D11B657067496314752DF6C07D3F7，收尾后仅人工摘要更新。机器记录只追加各自独立ledger，全部新旧证据保留，无删除。

额度最终：初次准备完成，失败后修复0/2、readiness1/3、五前置完整序列1/1、FastAPI1/1、health0/1（未监听故不调用）；不把未用额度迁移下一轮。原超时仍未关闭，完整quality/精确Godot/evaluator/digest/性能本轮均未运行。唯一下一动作建议：另行授权只读审查composition导入至uvicorn.run的启动链路，先选定最小低扰动分段取证点；不自动增加启动批次或修改产品。

就绪已执行一次：正式python -B scripts/f009_step6_qa.py --startup-readiness 01，UTC08:00:31.730009—08:00:59.159946，runner/pytest均0，实际33函数/184passed；较原98新增startup未重复32、receipt参数48、批次3及完整性3，保留原A/B/C全部覆盖。父observer completed=true/events464/overflow=false/unknown_paths=[]/reparse0，顶层boundary={}、diagnostic_rejections=[]。False两进程各主动终止最终1、自然null；True各自然7，无终止尝试；本次仅synthetic，不是FastAPI。10个真实报告子pytest的受控负例由父回归验证通过。证据：[readiness-01 pytest](../../../../cyber-town-f009-step6-qa/recovery-20260905-01/connectivity-startup-readiness-01/pytest-summary.json)、同根invocation.json/native-summary.json/machine-ledger.md；55文件/211129 bytes，ledger92350 bytes/SHA256 E733E5D7CEDF1CF96573378CF3F0D470DDC5857F518820128F375AEEC677A4AF。冻结不变、四文档运行期大小/hash一致；evidence65218 bytes/SHA256 3BD10FB205503681EBA6F2161C02179F11950295A6CE716F49BBB452B8D611E5。失败修复0/2、就绪1/3，真实额度尚0/1；现按授权登记diagnostic-03，绝不重复synthetic或旧批次。

接续7d18b739…3948f049与两仓99/19变化、staged0一致。仅两QA新增精确根/独立就绪核验及启动记录适配，无权限/进程校验/产品逻辑变更；完整静态在初次准备通过（源码复核补充owner身份文件一致性后全部复验也通过，无失败消耗）。准确静态：正式既有.venv/Scripts/python.exe -B -m ruff check --no-cache，以及ruff format --check --no-cache，两目标scripts/f009_step6_qa.py、backend/tests/test_f009_step6_qa.py；AST仅parse不导入；mypy --no-incremental --cache-dir=nul相同两目标，MYPYPATH=backend/src调用后恢复，功能cwd/既有strict配置；git diff --check及全部tracked/untracked指纹。Ruff/format/AST/mypy均exit0。格式准备仅两文件，不做全仓自动修复。

冻结584a20f113e8c23f66c95fa1ddac962b34d88c9a7273162f6f702721d861bfdc；脚本07af0cfcd008c5773f3bf1d0565473fabcc67906d7bc79bc6a9999911b89988b，测试0b8ce5f62455c439dfc3444e58b8e6b04168735ccbb08a74b9d5814a482380be。原算法99路径、其余97项未变。旧1488文件/233597292 bytes及八台账不变；旧资源元数据聚合ACC2278D3F5314E2AB076BD18AECB1E1CA371C7126D14DEC4132B44175D7DF23。readiness-01创建前精确登记见current-task；准备失败后修复0/2、就绪0/3、五场景/启动/health均0/1。运行期当前文档只读、机器只写独立台账。第1轮历史TerminateProcess原因继续未知。

## 2026-09-08 退出观察契约收口

两轮均使用正式既有.venv/Scripts/python.exe、功能cwd；静态为两QA的Ruff check --no-cache、format --check --no-cache、AST（含synthetic报告fixture）、mypy --no-incremental --cache-dir=nul（MYPYPATH=backend/src，调用后恢复）、tracked/untracked/空白检查，全部exit0。第2轮准确入口`-B scripts/f009_step6_qa.py --exit-validation 02`，UTC05:50:59.3030581—05:51:20.2095904，runner退出0；18函数实际98passed（A50/B46/C2），不是仅清单推算。原65覆盖保留，第一轮新增27、第二轮新增6；新增实例未替换原实际分支。修复2/2、定向2/2，历史额度不清零，后续运行零授权。

结果：首次绑定仍核验PID/父子/创建时间/映像，运行中及终止前完整核验；确认退出后从原保留句柄读状态，不依赖映像重查，不重新按PID绑定。失败终止调用即时保存ctypes错误副本，仅同一原句柄确认退出才读最终状态；存活仍抛准确OSError、无效句柄拒绝、码不可取保留None。终止尝试、是否成功主动终止、历史绑定和实际最终码分开记录。方案复用既有API/state/wait，不提高权限或增加框架；依据[Win32进程对象生命周期](https://learn.microsoft.com/en-us/windows/win32/procthread/terminating-a-process)与[GetExitCodeProcess](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getexitcodeprocess)，不声称官方文档解释了错误31。

实际False：business PID76584/parent5648、launcher5648/parent50032，各自原查询句柄确认最终alive=false/code1/available=true；两者termination_attempted=true、terminated_by_diagnostic=true、natural_exit_code=null。实际True：business16252/parent18540、launcher18540/parent50032，均自然码/最终码7、available=true，无终止尝试。四者termination_error_code=null。收尾这些PID及相关任务进程均无残留。第2轮未实际触发终止失败窗口，窗口分流由4个controlled参数及2个即时错误码参数证明；不能据此确认第1轮失败的角色、错误码或OS内部原因。

证据位于恢复根`startup-process-exit-validation-02/`：[pytest-summary](../../../../cyber-town-f009-step6-qa/recovery-20260905-01/startup-process-exit-validation-02/pytest-summary.json)、invocation.json（2695 bytes，准确命令/代码SHA/独立台账/observer）、identity-events.jsonl（0 bytes，无顶层身份失败）、machine-ledger.md（87682 bytes，SHA256 DA0ECFB575D8AA11B16E9932EF18BE89FB137040B116544BE82940C139DDF03A）、native-summary.json。report-regression/{import,runpy}/{call,setup,forged,invalid,canonical}/pytest-summary.json的10份真实子报告均由父回归通过严格核验：8个预期exit1，2个非法字段fail-closed预期exit3；未吞掉非预期失败，不把受控错误当真实进程复现。旧canonical与字段白名单/限量/来源核验/阶段隔离通过。

最终冻结7d18b739e246a7b576af6b7dea98bcbd248e160971eac56c9de27d3e3948f049，脚本SHA256 34d6c71425abfabd5ea1ca134a938c03d2b7522cb5d84900ac30471e3602a3c1，测试6d275b270dc5035cc4a2e4f0ba0e20f1ae6a255130da3de71008d640e6fa6278；运行前后相同，其余97项未变。第1批52文件/181983 bytes、第2批52文件/187428 bytes，新增369411 bytes，恢复1488文件/233597292 bytes。第2批observer合计18392 bytes、非固定必要子资源53932 bytes，均低于各8MiB；顶层pytest24727 bytes，各固定产物低于限额。native-summary清单51文件/168804 bytes不含自身最终写入，最终盘点为52文件；completed=true/event_count435/overflow=false/unknown_paths=[]/reparse0。旧六台账与资源未变；第2轮前后含第一批的旧资源元数据聚合E79BF964A9B33903EC29438A17641530ECD8376E4566CC3AF20D6506BEAA8C85一致，第1台账SHA256 9CC3C5A3C217A283C215F47FE032DBEB549A14326AF9B46752FDFD201723E51D未变。新旧证据全部明确保留，未删除或处理无关进程。

正式四当前文档各轮运行期均未变；第2轮evidence运行前后58830 bytes/SHA256 B61B03CBA8A9F0DA8D30AC1441D5726691642D930BABC1EAF6E217B54DCE4652，收尾才人工更新。本轮文档新增主要为必要根/子资源预登记、当前设计和结果索引；机器轨迹未追加到人工evidence，未重复归档。复盘结论：退出生命周期与报告组合必须先用真实工具验证，本轮按阶段复用现有能力，未修改全局规则。唯一下一动作是另行确认原connectivity最小诊断方案/授权，不自动进入后续阶段。

## 2026-09-08 第1轮保留记录

2026-09-08 退出观察契约第1轮：完整Ruff check/format-check、AST两QA及报告fixture、mypy两目标（--no-incremental --cache-dir=nul，MYPYPATH=backend/src）、diff/空白通过。冻结a697902b31b725d0fa9a8e584d436cfb710815786f5affe44a0d70f98062a545。调用正式.venv/Scripts/python.exe -B scripts/f009_step6_qa.py --exit-validation 01，cwd功能目录；UTC05:42:18.8114603—05:42:52.8243033，runner退出1。新根startup-process-exit-validation-01/pytest-summary.json为90 passed/1 failed，A44/B46通过，C False在脚本3561/TerminateProcess失败分支，True未执行；本次无具体Win32码或调用角色，不能声称已确定自然退出竞态。native-summary completed=false、overflow=false、unknown_paths=[]，无相关进程残留；正式evidence运行期57546 bytes/SHA256 76DA6A2DA6A2CFE3F34501342DB71CDB84B1F14C4BDCF95D7F4A05E6542D83C9不变，旧资源不变。保留此批，不覆盖。原单行AST清单计数辅助命令曾有括号语法错误，改正后只读计数92实例；不涉及导入/测试或QA代码修复。第2轮仅在用户已有两轮授权内补终止检查到调用之间的退出窗口契约与直接负例，保留失败码、不以确认已退出冒充终止成功；不是已证实OS根因或产品修复。

- 最新模块身份适配：完整静态通过；startup-process-observation-validation-01 唯一运行 63 passed/1 failed，A17/B46 全通过，C [False] 失败、[True] 未执行。真实报告通路取得 QueryFullProcessImageNameW/post_wait/business/query/31，主动收口标志 true；这不是 FastAPI 或原 connectivity 复现。详见下节。

## 2026-09-07 异常模块身份适配：唯一运行结果

代码仅两份 QA。采用明确类对象及模块 __file__/spec.origin/定义来源核验，未共享活动 guard/台账/observer，未改变 Win32、权限、owner、等待或终止规则。两轮准备及完整静态通过记录保留于本文件后文；运行冻结 2bb5f5744af80e1223418310874c3d803141b8a34b0480fc51a02294501b6aa6 前后相同，其他 97 项未变。

准确调用：E:\Agent\comprehensive-cases\15-cyber-town\.venv\Scripts\python.exe -B scripts/f009_step6_qa.py --identity-validation；cwd=E:\Agent\comprehensive-cases\15-cyber-town-f009。2026-09-07T14:53:30.7578365Z 至 14:53:51.3570725Z；runner 退出码 1（PowerShell 包装命令自身退出码 0 不代表门禁通过）。固定 65 顶层实例，实际摘要 64 项：A17/B46 通过，C [False] 失败后 -x 停止，[True] 未执行。不将 AST 清单数冒充实际执行数。

B 的 import/runpy 两种加载方式 × call/setup/forged/invalid/canonical 共 10 个真实子 pytest 全部由父断言验证通过：每次一个控制节点通过；八次已知失败退出 1，两个非法字段负例维持 fail-closed/退出 3，仅保留固定拒绝元数据，父断言严格核验节点/阶段/退出码。身份字段与 canonical 保留，同名伪造和非法字段不进入身份摘要，控制节点无诊断串项。这些是 synthetic 负例，不是实际 Win32 故障证据。

实际 C [False]：最终 pytest-summary.json 与 identity-events.jsonl 均保留 api=QueryFullProcessImageNameW，stage=post_wait，process_role=business，handle_role=query，pid=expected_pid=9332，created_100ns=134332664258167995，image_status=approved，active_cleanup=true，win32_error=31。最近观察 last_alive=true/last_observed_ns=391491734000000 是收口前历史状态，不表示失败时仍存活。源码控制流表明终止调用及持有查询句柄的 wait 已成功返回，随后映像查询失败；同次 GetProcessId/GetProcessTimes 已通过短路判断。不能由错误31推断权限/PID复用或操作系统内部原因。最终 state/GetExitCodeProcess 尚未执行，没有独立最终退出码；不以启动进程退出码代替。收尾查询 PID9332、父 observer PID65336 及相关进程均无残留。本轮不修改退出后检查，不补跑 True。

证据索引（均在恢复根 startup-process-observation-validation-01）：invocation.json（准确命令/冻结/observer）、pytest-summary.json（64项及错误字段）、identity-events.jsonl（313 bytes）、report-regression/{import,runpy}/{call,setup,forged,invalid,canonical}/pytest-summary.json（10份真实子报告）、machine-ledger.md（89,204 bytes）、native-summary.json/ready/drain（observer 合计18,757 bytes）。observer event_count=436、overflow=false、unknown_paths=[]、reparse=0；已排空并生成清单，但本次门禁失败故 completed=false，不能称整批通过。

最终盘点 52 文件/179,157 bytes，小于32 MiB；必要非固定子资源54,282 bytes，小于8 MiB，固定文件均低于各限额。native-summary 中51文件/160,168 bytes 是写入自身前的清单，不替代最终盘点。恢复合计233,227,881 bytes，小于2 GiB。五旧台账SHA256及旧1,332文件/233,048,724 bytes的路径/长度/mtime聚合 DBCDAF416EAC22F834930B88CC1040A3F6361403925F815367DB96BA1AFE5D8C 未变。正式四份当前文档运行期均未变；evidence运行前后52,915 bytes，SHA256 5080BE5B6C140372C379301AFB9B8D98F3D7AE521D4A139BDC6BDFD69EAC2C4F，收尾才人工增加本摘要。未向正式 evidence 追加机器记录。

本轮准备2/2、定向1/1，旧额度保留，不复用此根。最小下一动作仅为请求退出后身份复核安全恢复方案授权：持续持有查询句柄、绑定身份及终止前完整核验保持，先明确已退出状态与映像重查的关系并补直接回归，另批受保护验证；不得按错误31整体豁免身份失败。当前已确定本次查询失败位置和调用阶段，底层错误成因与原 connectivity 根因仍未确定。历史工具回归及 original_failure_resolved=true 独立保留，step6_complete=false、Step7未授权；未运行任何产品/完整quality/性能。

## 保留的历史验收结论

- F-009 Step 6 未完成；original_failure_resolved=true；step6_complete=false；awaiting_step_7_authorization=false。
- 原 ownership/canonical 关闭依据：tool-validation-03 的 sidecar 两态、缺失登记反例和 ownership 共 5 passed；native-quality-02 同组再次通过且 ResourceGuard 有两种状态的直接登记证据。受控注入不表述为原竞态自然重现。
- 历史 native-quality-02 完整 pytest 为 1314 passed / 133 skipped / 1 failed，边界违规 0；新 UV 测试于第 2311 行按 quality- 前缀取根失败。完整 quality 未通过。
- 精确 Godot 本地回环暂无执行记录；性能未运行，warm-up + 5-run 额度保留。Step 7 未授权。
- 历史接入回归 qa-tool-contract-02 为 201 passed；native-quality-03 在 connectivity/runner_port_open_timeout 失败即停，完整 pytest、精确 Godot/evaluator/digest 未进入。
- 历史诊断 01 为 synthetic 26 passed、一次端口/health 通过但业务 PID 独立退出码缺失。当前诊断 02 类型修正与完整静态通过，唯一 synthetic 实际 42 passed/1 failed，另 1 实例未执行；已停止，五前置场景及真实 FastAPI 未执行。最新运行冻结指纹、失败位置与证据边界见末尾。

## 接续与原文保全

- 正式 main 与功能 feat/f-009-safety-cost-performance 的 HEAD 均为 1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3；staged 0。
- 接续 99 文件按序数路径排序，以 path + NUL + 文件 SHA256 + LF 聚合：0b8583a2ad0c92dfa0649c1a11210f72dbf2d1d4ba1b89fef454764f79046a75。
- 接续脚本 SHA256 cbf97f0aeeda97546d95fe1dec4fcaa8747b8617164a2a9f8dc9467487b72d85；测试 2ed47b964b03b9b8f40cb32617ca7c423aabda73448377cfb7d1d4384cf31303。
- evidence 原文 2,334,209 bytes，SHA256 f7d1213f7af94ce8388dcacb429fa3d7cd04963cb3ab1f3edba90fc75d78d357。2026-09-06T23:59:30+08:00 副本逐字节一致后才收敛本文件。
- 接续恢复根 991 文件 / 187,301,694 bytes / reparse 0；未发现相关 QA 写入进程。初始化资源已先登记于 current-task。

## 证据与台账索引

恢复根：E:\Agent\cyber-town-f009-step6-qa\recovery-20260905-01。

| 来源 | 位置与职责 |
| --- | --- |
| 原历史证据 | ../archive/F-009-过程记录-20260905/evidence.md |
| 已保全恢复台账 | ../archive/F-009-过程记录-20260905/recovery-20260905-01-evidence-ledger.md |
| 本次字节保真快照 | 恢复根/ledger-separation-01/evidence-before-split.md |
| 保全清单 | 恢复根/ledger-separation-01/manifest.json |
| 本批次机器台账 | 恢复根/qa-tool-contract-01/machine-ledger.md；固定追加，运行完成后保留，限 8 MiB |
| 工具契约结果 | 恢复根/qa-tool-contract-01/contract-summary.json、pytest-summary.json、native-summary.json |
| 新批接入回归 | 恢复根/qa-tool-contract-02/contract-summary.json、pytest-summary.json、native-summary.json、machine-ledger.md |
| 当前完整验收失败 | 恢复根/native-quality-03/quality-summary.json、native-summary.json、machine-ledger.md；未生成 pytest-summary.json |
| 历史定向结果 | 恢复根/tool-validation-03/targeted-summary.json |
| 历史完整失败 | 恢复根/native-quality-02/quality-summary.json、pytest-summary.json、native-summary.json |
| mypy 独立诊断 | 恢复根/static-diagnostic-01/diagnosis.md、invocation.json、traceback.txt；一次复现已停止 |
| 当前授权与初始化登记 | [current-task.md](current-task.md) |
| 当前执行顺序与自测范围 | [implementation-plan.md](implementation-plan.md) |
| 有效验收契约 | [F-009-验收契约.md](F-009-验收契约.md) |

原文保留全部登记（包括重复项）、时间、失败结果、指纹和旧索引。历史读取覆盖两个历史台账、本次快照及新台账。快照和台账为必须保留证据，不得按临时目录清理。

## 本轮结果

### 实现与停止点

- 仅两份 QA 文件改变：当前 root/owner/anchor fixture、指定路径/线程注入、负例错误码、机器台账与历史显式来源、正式项目根独立、固定 63 函数工具自测入口。产品代码、SQL、migration、依赖、CI、Godot 产品文件和完整 quality 命令未变。
- 新自测覆盖 UV 全部 17 例、Godot 重命名回放全部 26 例、相关真实通知、共享替身、台账半行/时序/并发可见性/写失败与原 sidecar/ownership。以上是已固定清单，不是通过结果。
- 台账 bootstrap 代码先核对 current-task 对根及台账的精确预登记，才创建两者；其余子资源走 ResourceGuard。该新初始化及固定路径/身份/游标逻辑尚未运行验证。

### 静态初检（仅一次，未重试）

既有工具链：E:\Agent\comprehensive-cases\15-cyber-town\.venv\Scripts。执行目录为功能 worktree；未导入执行 QA 模块，未建立新环境。

- Ruff check --no-cache（仅两份 QA 文件）：exit 1；E501 五处（测试 1957、2426；脚本 1094、1095、1256），SIM300 一处（测试 2962）。
- Ruff format --check --no-cache：exit 1，两份文件需要格式整理。
- AST parse：两份通过；git diff --check：exit 0（untracked 两份 QA 不由 Git diff 检查覆盖，另由 AST/Ruff 检查）。
- mypy 命令：python.exe -B -m mypy --no-incremental --cache-dir=NUL scripts/f009_step6_qa.py backend/tests/test_f009_step6_qa.py；MYPYPATH 临时绑定 backend/src 并恢复。
- mypy 1.20.2：INTERNAL ERROR，exit 2，仅给出建议查看 traceback；未输出代码定位，未使用其他缓存配置/命令重跑。原因未确定，不能断言代码通过或归因环境。
- 停止原因：mypy 内部错误不属于已批准的格式、导入、换行等机械修正。机械修正 0/2；运行自测 0/1，qa-tool-contract-01 及 machine-ledger.md 均未创建。

### 保全、指纹和资源收口

- 停止点 99 文件聚合：645ac444a4450d485c579ef30067951655f95c570b9a9842589a8916c8d0b03b。这是未通过静态门禁的保存点，不是可运行验收冻结版本。
- 脚本 SHA256：7b6898c6229a9e632064675e713a37cb4d51ab5c81af255f59a60099ea6d2946；测试：daadcc56013ab86a2451f5ec6245cdffce1d69abf8e27f0004ed4b7ed0bb4007。
- 仅在计算中代入两份 QA 的接续哈希，聚合恢复为 0b8583a2ad0c92dfa0649c1a11210f72dbf2d1d4ba1b89fef454764f79046a75，证明其余 97 项内容未漂移；未执行文件还原。
- 原 evidence 2,334,209 bytes；收敛后静态结束时 3,174 bytes，SHA256 1983d80a6939bc85859ba7cbca6919bc6039cadd0e9894979e98683b07fe3d97，机器记录行数 0。本段为人工收口摘要新增；没有工具运行前后对照，因为自测未启动。
- 快照仍为 2,334,209 bytes / f7d1213f7af94ce8388dcacb429fa3d7cd04963cb3ab1f3edba90fc75d78d357；manifest 1,120 bytes。两项新增证据均在上限内。
- 恢复根收口：993 文件 / 189,637,023 bytes / reparse 0，低于 2 GiB。只新增保全快照与 manifest；旧批次全部保留，没有删除。未发现相关 QA 写入进程。
- 原故障关闭结论不变；新 UV/替身/台账实现尚未验证，完整 quality 未通过、精确 Godot 回环暂无执行记录、性能未执行。step6_complete=false。

### 2026-09-07 有边界诊断收口

- 仅在原 mypy 命令末尾增加 --show-traceback，一次调用 exit 2；完整元数据与脱敏 trace 见上述独立诊断索引。大写 NUL 未命中本机工具对小写 os.devnull 的判断，创建 NUL\3.12 失败，尚未进入 QA 类型分析。仅改为小写 nul 是待批准恢复候选，未执行、未宣称解决。
- 功能 99 项保存点聚合仍为 645ac444a4450d485c579ef30067951655f95c570b9a9842589a8916c8d0b03b，两份 QA 哈希未变；两仓 HEAD/分支不变，staged 0。旧快照与 manifest 保留且未变；未发现相关运行进程。
- 新增仅 static-diagnostic-01 三份预登记证据，共 9,665 bytes（上限 32 MiB）；恢复根合计 996 文件 / 189,646,688 bytes / reparse 0（上限 2 GiB）。诊断 1/1 已使用，机械 0/2、自测 0/1 不变；qa-tool-contract-01 及 machine-ledger.md 未初始化。
- 未运行任何修复、其他静态复验、工具自测、quality、Godot 或性能。原故障关闭结论保持，新 QA 实现未验证，step6_complete=false；当前 evidence 仅人工摘要/索引更新，没有机器台账追加。

### 2026-09-07 静态恢复（第一轮）

- 接续保存点 645ac444a4450d485c579ef30067951655f95c570b9a9842589a8916c8d0b03b 一致。本轮仅两份 QA 的五处 E501 换行、一处 SIM300 等值比较顺序及格式整理，LF 保留。人工逐项 diff 与 untracked 行尾空白检查通过，其他 97 项哈希完全不变。
- 执行目录均为功能 worktree；既有正式项目 `.venv/Scripts/ruff.exe`：`format --no-cache scripts/f009_step6_qa.py backend/tests/test_f009_step6_qa.py`（1 file reformatted、1 unchanged）；随后同两目标 `check --no-cache` 和 `format --check --no-cache` 均 exit 0。仅第一轮机械 1/2，未使用第二轮。
- 既有正式项目 `.venv/Scripts/python.exe -B -c` 对同两文件用 ast.parse/pathlib.read_text 解析，2 passed，未导入 QA；`git diff --check` exit 0，untracked 两份另与接续内存原文逐行审查及空白核验。
- mypy 准确调用：`E:\Agent\comprehensive-cases\15-cyber-town\.venv\Scripts\python.exe -B -m mypy --no-incremental --cache-dir=nul scripts/f009_step6_qa.py backend/tests/test_f009_step6_qa.py`；MYPYPATH=backend/src，退出恢复。2026-09-07T15:14:32.0348149+08:00 至 15:14:43.0279776+08:00，exit 0，Success: no issues found in 2 source files。原 1.20.2/解释器/strict 配置未变；本次实际通过缓存初始化及类型分析，没有创建实体 mypy 缓存或追加实验。
- 新冻结聚合 ccd611706d26020040ad7a0a1c82c20a546abcb11c18ecc08a51e0305cdf42db；脚本 a67e7c73d6d28560e352f473c1f2c29069cb479b91ea94fed520971a497ffef8；测试 c308ac1f9251b3026c2c5cdea7048891bfcc3868516160ba03e7e9f8de858ea9。算法与原保存点完全相同；不是完整验收通过声明。

### 2026-09-07 唯一工具契约自测与收口

- 准确入口：`E:\Agent\comprehensive-cases\15-cyber-town\.venv\Scripts\python.exe -B scripts/f009_step6_qa.py --tool-contract`，cwd=功能 worktree。启动前重新确认根新鲜、两条原 bootstrap 登记有效、父链无 reparse、无并发写入。15:17:33.1396146 至 15:17:52.5572957（+08:00）只运行一次，exit 0。
- 固定 63 函数全部执行。结果台账有 181 个唯一已收集并完成的 nodeid：142 个带参数实例、39 个非参数化项，全部 passed，无失败/skip；UV 17、Godot 重命名回放 26。runner 未另存独立的 collection 总数字段，以上计数来自实际完整结果台账，未额外跑 collect-only 或改变选择范围。
- 真实父 observer 的 completed=true，1,923 个事件、overflow=false、unknown_paths=[]、reparse=0；子进程 boundary_violations={}。真实通知测试与受控回放分别通过；没有把 Godot 文件回放或原生文件通知称为精确 Godot 回环。
- 新台账/共享替身契约通过：历史读取、登记先于操作、半行处理、并发写入可见性、身份/截断/容量拒绝、写入失败关闭及退出恢复。独立台账有 597 条预登记、130 条 native runtime event；ResourceGuard 两态直接记录分别为 absent 与 current_path_strictly_revalidated（受控注入），与 2 条 NativeWatcher 退役通知分开判断。原 ownership 节点也通过；original_failure_resolved=true 保持。
- 正式 evidence 在运行前后均 9,476 bytes，SHA256 均 293bfa33e69b669178d6286cc271e4529db2eee4459554348d4fe9753d5e442e；formal_evidence_unchanged=true，机器记录行数 0。本段是运行后人工收口摘要，不是机器追加。machine-ledger.md 最终 287,972 bytes（低于 8 MiB），保持固定路径，无移动/截断/切换。
- 最终批次 116 文件 / 542,700 bytes（低于 256 MiB）；恢复根 1,112 文件 / 190,189,388 bytes（低于 2 GiB）。native-summary 的 115 文件 / 472,364 bytes 是写入自身之前的盘点，最终容量包含该报告及末尾台账追加，不用中间计数代替最终审计。
- 冻结聚合仍 ccd611706d26020040ad7a0a1c82c20a546abcb11c18ecc08a51e0305cdf42db，两份 QA 哈希同上；两仓分支/HEAD/staged 不变。旧 996 份恢复文件 SHA256/修改时间未变；保护缓存元数据未变；相关进程已退出。所有新旧资源保留，无删除或重建旧批次。
- 额度：机械 1/2，未用第二轮；工具自测 1/1 已耗尽；旧诊断 1/1 不变。新 QA 工具范围已验证，但完整 quality/精确 Godot/性能未运行，step6_complete=false，Step 7 未授权。

### 2026-09-07 新批次接入与静态冻结

- 本轮只接入两份 QA：qa-tool-contract-02（256 MiB）/native-quality-03（1 GiB）各自一次绑定 machine-ledger.md（8 MiB），子进程传递独立台账上下文，禁止运行中切换及写入其他批次台账；bootstrap 核对精确路径/任务/容量预登记。两个新根都检查各自与总 2 GiB 容量。旧 qa-tool-contract-01 台账列入历史读取，不追加。
- 初检：7 E501、5 RUF043、两文件需格式化，AST 2 passed；本轮机械第 1 轮只整理换行和无转义内容的 raw-string 标记（字符串值未变）。复验 Ruff check/format-check --no-cache、AST、git diff --check 均 exit 0；untracked 修改逐项审查，仅接入和直接测试，无行尾空白；其他 97 项哈希不变。
- 准确静态命令沿用上一静态恢复所列两目标及既有解释器；mypy `-B -m mypy --no-incremental --cache-dir=nul scripts/f009_step6_qa.py backend/tests/test_f009_step6_qa.py`，MYPYPATH=backend/src 并恢复，16:01:07.4815200 至 16:01:14.9334323（+08:00），exit 0，2 source files 无错误。没有修改完整 quality 的缓存策略或检查目标。
- 新冻结聚合：1e5611d26e23fb10b5ce4794e7847d75392dccd992611a61ce75754a2daf5b1f；脚本 29764f2a049568143f22b4e7944ee4304008f1b11f5ae5347a6283ce6e3e8c63；测试 ebd9ce8197487711af07bc61b375a449bdaecf8d6f5945b2ea1584dd4c1d8d21。原 63 函数完整保留，新增 7 个接入函数/预计 20 实例，静态清单唯一函数数 70。
- 完整验收映射见 implementation-plan：工程 9 条原命令与 preflight/final policy；精确 Godot、25-case evaluator、三新进程 digest 及全部安全/预算/成本/重试/SQLite/空间/对抗均已包含在完整 backend pytest，不重复补跑。该映射不代表已执行。
- 运行前旧 qa-tool-contract-01 台账 287,972 bytes / 534427b5754bfa70d5d6b9334360a7bd62861d2115084de66400a861405fb829；快照/manifest/诊断保持原哈希。两个新目录不存在、无相关进程/reparse，8000/8001 无监听；新额度回归 0/1、quality 0/1、机械 1/2。

### 2026-09-07 两批执行结果与失败收口

- 接入命令：既有正式项目 `.venv/Scripts/python.exe -B scripts/f009_step6_qa.py --tool-contract`，cwd=功能目录；16:04:14.3745492 至 16:04:29.9103197（+08:00），exit 0。70 函数全部执行、201 唯一 nodeid passed（159 参数化实例 + 42 非参数化项），原 181 与新增 20 均覆盖，无失败/skip；UV17、Godot 回放26。实际结果计数不冒充独立 collection 日志。
- 接入 observer completed=true，1,933 events，overflow=false、unknown_paths=[]、reparse=0；子进程 boundary_violations={}。当前根/owner、父子台账、bootstrap、两批容量、旧台账写入拒绝及当前工具报告/代码匹配回归通过。原 sidecar 两态/ownership 在本接入批次通过；受控回放仍不等于精确 Godot 回环。
- 条件确认：接入 exit 0/observer 完成，冻结代码和 evidence 未变，旧台账未变，native-quality-03 新鲜且无相关进程/端口占用后才启动完整验收。准确命令：同解释器 `-B scripts/f009_step6_qa.py --quality recovery-20260905-01/native-quality-03`，同 cwd；16:05:34.4539710 至 16:06:37.4021000（+08:00），exit 1。
- 完整 quality：lock、全目录 Ruff/mypy、schema、Godot import、Godot unit 六项 exit 0；connectivity exit 1，分类 runner_port_open_timeout。已记录通过标记 duplicate_rejected/non_string_rejected/redirect_rejected/stopped_service/unavailable；没有 failed-scenario marker，不能据此确定具体失败场景、端口或根因。命令记录未报告边界错误码。没有重跑或修改策略。
- 未执行：dialogue-connectivity、完整 backend pytest（pytest-summary.json 不存在）、其内的精确 Godot 本地回环、25-case evaluator、三个全新进程 digest 和本轮完整安全/预算/成本/重试/SQLite/空间/对抗回归。quality 的 final policy 未到达；不能用接入回归或历史验收代替。
- quality observer completed=true、500 events、overflow=false、unknown_paths=[]、reparse=0；completed 仅表示 observer 正常收口，不是 quality 通过。运行后无相关进程和 8000/8001 监听。故障根因尚未诊断，当前唯一确认的失败分类是监听建立超时。
- 两次运行前、中间及结束，正式 evidence 均 14,424 bytes / b498123646981c470dd2a9e1dd28c7e9c65919ce084b8988f3b0ea4bd48e4c23，机器记录 0 行；本段为运行后人工收口。旧 qa-tool-contract-01 台账哈希同上；qa-tool-contract-02 台账在 quality 前后均 290,086 bytes / 8225b4fb3eedd8d912370b6d143d8139a1db8df7cb636dc20fec1d654bc4e961。quality 只写自己的台账：54,487 bytes / 396bb5257bf50a6267e38bafacc55c4fc9181e64e26ba6585f06d9e18c535ce6。
- 资源最终审计：qa-tool-contract-02 为 116 文件 / 550,407 bytes；native-quality-03 为 55 文件 / 42,127,219 bytes；恢复资源总计 1,283 文件 / 232,867,014 bytes，均在各批/台账/总容量内。native-summary 在写入自身前的文件数/字节数不是最终容量。所有新旧批次、快照/manifest/诊断保留，无删除；历史保全文件哈希未变。
- 两仓分支/HEAD/staged 不变，运行前后聚合仍 1e5611d26e23fb10b5ce4794e7847d75392dccd992611a61ce75754a2daf5b1f，仅获批两份 QA 有本轮变化。额度：新机械 1/2、接入 1/1、quality 1/1；历史额度不变，失败即停止已执行。original_failure_resolved=true 独立保留；step6_complete=false，Step 7 未授权。

上轮下一动作是只读诊断；该诊断已在回复中交付。本轮最新停止状态见下，不执行性能或任何未获恢复授权的批次。

### 2026-09-07 启动诊断候选实现：静态源码复核停止

- 仅两份 QA 新增精确 32 MiB 根、固定台账/产物限额、专用 --startup-diagnostic 入口、双管道流式白名单脱敏、进程退出/监听时间线、已加载模块采样及 9 函数 synthetic 清单；不改产品或 connectivity_integration.py。该实现尚未运行验证，不能作为工具就绪或故障关闭证据。
- 静态初检包含 E501、RUF043、SIM117、SIM102、RUF021、I001 与格式差异。机械第 1 轮只做等义括号/短路条件及 with 语法整理、无转义 raw-string 标记、导入分隔和 formatter；复验仅剩一处 102 字符的 E501，format-check 通过。第 2 轮将该字面量等义拆分，最终 Ruff check/format-check --no-cache、AST 2 文件（不导入 QA）、git diff --check 全部 exit 0。
- mypy 准确命令：E:\Agent\comprehensive-cases\15-cyber-town\.venv\Scripts\python.exe -B -m mypy --no-incremental --cache-dir=nul scripts/f009_step6_qa.py backend/tests/test_f009_step6_qa.py；cwd=功能目录，MYPYPATH=backend/src 后恢复。17:10:02.9901006 至 17:10:10.3794561（+08:00），exit 0，2 source files 无类型错误。
- 随后的源码就绪复核发现本轮新增 test_startup_root_and_owner（backend/tests/test_f009_step6_qa.py:224）的第 229 行 assert native_test_root == qa.STARTUP_ROOT。pyproject.toml:39 的完整 backend/tests 入口也会收集它，其他合法 native quality 根会产生误失败。这是非机械测试上下文缺陷，不是格式问题；依本轮停止条件停止，未修复、未加 skip/放宽门禁、未执行 synthetic 或真实 FastAPI。
- 保存点聚合：dd4157167e7db37c5327ad8bfcb45a3a00f16a5ce17b392fe821102df5592283；script 6329e04c66afa6cbb8717de0b94e0b5dd91379f247f25ab9f0aa3292bcff7921；test dbea2cbf767c0c468e6f9ae91228cb1a72ed36a7f428a053fd371e0198d3c8dd。此为未验证候选保存点，不是运行就绪冻结版本。功能其余 97 项哈希不变；两仓分支/HEAD/staged 保持原状态。
- 额度：本轮机械 2/2，synthetic 0/1，真实启动 0/1；历史额度不变。诊断根仍不存在，仅 current-task 精确预登记，没有 invocation/timeline/输出/observer 运行产物。因此没有 FastAPI PID、退出码、监听或复现结论；观察开销也未经实测。旧三份机器台账 SHA256 不变，旧 1,283 文件大小/mtime 不变，恢复总额仍 232,867,014 bytes；无相关进程和 8000/8001 监听。没有删除或新建恢复资源。
- 下一项最小恢复：单独批准修正新增测试的执行上下文假设，将配置中的诊断根限额验证与当前合法 native 根/owner/台账验证分开；不新增 skip、不依赖旧目录存在，明确剩余静态恢复额度，完成就绪复核后才考虑尚未消耗的一次 synthetic 和一次启动。停止状态不因运行额度未用而自动解除。
- original_failure_resolved=true 与历史工具回归/台账隔离结论独立保留；connectivity 根因仍未确定，step6_complete=false，Step 7 未授权，性能未执行。

### 2026-09-07 启动测试批次假设恢复：运行前冻结

- 接续 dd4157167e7db37c5327ad8bfcb45a3a00f16a5ce17b392fe821102df5592283 一致。本轮代码只改 test_startup_root_and_owner：精确诊断根/32 MiB/台账静态配置与当前 native_test_root 分开，三种配置目标检验跨批选择永远不同于当前根；真实 owner attach、路径校验、精确切换错误码及原台账对象/identity 不变断言保留。无 skip/xfail，不创建历史根；同组其他 8 函数未发现相同批次/容量假设。
- 首次 Ruff 为一处 SIM300，format-check 通过；本轮机械第 1 轮仅调整两个 Path 的等值比较顺序。复验 Ruff check/format-check --no-cache、AST 两文件不导入 QA、git diff --check 全部 exit 0。mypy 原正式 .venv/Scripts/python.exe -B -m mypy --no-incremental --cache-dir=nul scripts/f009_step6_qa.py backend/tests/test_f009_step6_qa.py，cwd=功能目录，MYPYPATH=backend/src 后恢复；17:32:24.9341961 至 17:32:32.5083312（+08:00），exit 0，无类型错误。
- 新冻结聚合 caa73b48f1380edfaad1d07a0dac190828f05b7acd67b9a6b899460fb6b52b86；脚本 6329e04c66afa6cbb8717de0b94e0b5dd91379f247f25ab9f0aa3292bcff7921（与接续相同）；测试 bb9cbdc94c60e8a6250dac160147892312b4be100ac24d16092af393d3f5cc95。其余 98 项哈希不变，两仓分支/HEAD/staged 不变。固定 STARTUP_TESTS 9 函数，预计 26 实例（原 24 加两项配置参数），运行实际计数另报。
- 精确入口：E:\Agent\comprehensive-cases\15-cyber-town\.venv\Scripts\python.exe -B scripts/f009_step6_qa.py --startup-diagnostic，cwd=E:\Agent\comprehensive-cases\15-cyber-town-f009。一个固定父 observer/台账会话先 synthetic，条件满足后一次原 API 子进程启动；不执行旧批次、Godot、quality 或性能。新机械 1/2；synthetic 0/1、真实启动 0/1 恢复原额度，未另增次数。

### 2026-09-07 唯一 synthetic 与真实启动诊断收口

- 上述入口仅执行一次，17:34:43.7404774 至 17:35:00.1364431（+08:00），外层诊断 exit 0。先完成 9 函数/26 唯一 nodeid passed，无失败/skip，boundary_violations={}；三项参数只是静态配置选择和本次真实根契约，不是三个真实 quality 批次。synthetic-summary.json 的 real_start_attempts=0 是真实启动前保存的门禁状态，不代表之后未启动。
- 实际业务命令与包装命令、cwd、安全配置和 owner 见诊断根/invocation.json。父 observer PID 13144；Popen PID 35472，stderr 中业务包装器自报 PID 71704、ppid=35472。timeline.jsonl 的 wait_started=372357.390、deadline=372362.390；17 次 TCP 探测，前 16 次未开放，首次开放 t=372361.515（+4.125 秒），一次 health t=372361.531（+4.141 秒）通过。原五秒期限未延长，不运行 Godot 或前五个 fixture 场景。
- 收口结果：Popen 的 natural_exit_code=null、terminated_by_diagnostic=true、final_exit_code=1；这是主动结束所持解释器启动进程的结果，不能称为 FastAPI 自然启动失败码。实际业务 PID 71704 的独立退出码未保存，存在进程层级观察缺口；日志证明其为所持 PID 的子进程，但未记录其独立 handle/poll/退出码。事后只读复核 13144/35472/71704 均不存活，8000/8001 无监听，没有额外终止其他进程。外层 exit 0 不能替代缺失取证。
- stderr-redacted.txt 观测 wrapper_entered/configured/owner_verified/guard_active/module_entry 和 Uvicorn 启动/监听生命周期。10 个关键模块来源全部观测：cyber_town、api、api.__main__、app、composition、config 均为 feature/backend/src；FastAPI/Uvicorn/Pydantic/pydantic-settings 为 venv/Lib/site-packages。来源是加载中的对象观察，不等于各模块当时已完成初始化。无已记录错误类别；未知输出丢弃 1 行，不推断其内容。stdout 0 bytes；stderr 1,584 bytes，未保存原始日志。
- 本次未复现原超时，根因未确定。当前通过只排除本次启动中的提前退出/五秒监听失败/health 失败，不能倒推原批次。首次开放距期限约 0.875 秒，但不据此归因机器慢或超时过短。新根/缓存/台账、双管道排空、50ms 模块采样与时间线写入，以及省略前五场景均为差异，未做无观察对照，不能量化观察对时序的影响。
- 父 observer completed=true、31 events、overflow=false、unknown_paths=[]、reparse=0；此为文件观察正常收口，不补足业务进程退出码。native-summary.json 为最终写入自身前的 10 文件/24,900 bytes；最终根为 11 文件/28,734 bytes，总恢复资源 1,294 文件/232,895,748 bytes，各产物及总容量均未超限。machine-ledger.md 11,188 bytes，SHA256 a68ca74dcd3bdad3f93d3046a764af9c355a0452f971ac4a6b0d2ac09a947e8b；所有新旧资源保留，不复用、不删除。
- 运行前后正式 evidence 均 23,347 bytes / ac5deeafff2a8b29715d62006d6c3f171b877c78630ccf4b81c5f8fe8343b9e6，没有机器追加；本段为运行后人工摘要。旧三份台账哈希及旧 1,283 文件大小/mtime 均未变。代码聚合仍 caa73b48f1380edfaad1d07a0dac190828f05b7acd67b9a6b899460fb6b52b86，两仓分支/HEAD/staged 不变；脚本未改，只有获批测试发生本轮代码变化。
- 独立产物索引：恢复根/connectivity-startup-diagnostic-01 下的 invocation.json、timeline.jsonl、stderr-redacted.txt、stdout-redacted.txt、synthetic-summary.json、pytest-summary.json、native-summary.json、machine-ledger.md；原始机器证据不改写。额度：本轮机械 1/2、synthetic 1/1、真实启动 1/1；历史额度保留。发现进程观察缺口后不修脚本、不补跑。
- 唯一下一动作建议：另行批准补齐实际业务 PID/退出码的最小观察能力，再决定保留原前置场景的一次定向对照诊断；不直接恢复完整 quality。历史工具回归/台账隔离及 original_failure_resolved=true 独立保留；step6_complete=false，Step 7 未授权，性能未执行。

### 2026-09-07 诊断 02 候选：首次静态非机械问题停止

- 本轮授权仅两份 QA 的最小进程观察、直接 synthetic 及条件一次前置/启动定向序列。接续聚合 caa73b48f1380edfaad1d07a0dac190828f05b7acd67b9a6b899460fb6b52b86 匹配；两仓原分支/HEAD/staged 不变。资源初读因未包含隐藏 .git 子树少 5 文件/435 bytes，含隐藏文件复核后与历史 1,294 文件/232,895,748 bytes 一致，非未知漂移。
- 已保存候选：精确诊断 02 根/128 MiB/固定台账，旧诊断 01 退出活动批次配置并作为历史读取；Win32 query/synchronize 句柄读取 PID/创建时间/可执行文件、候选绑定时核对 OS 父关系、收口前重新核验终止句柄；启动/业务状态分离，运行时自然退出码 null，退出码不可得明确标记。前置适配仅调用原 connectivity 的 Godot/fixture 函数、原场景顺序与请求计数拒绝条件。新增直接 synthetic 参数覆盖进程状态/身份/归属/收口和前置断言。上述均未运行验证，不是工具就绪证据。API 语义只读核对 Microsoft GetProcessTimes、GetExitCodeProcess、PROCESSENTRY32W 文档；无业务模块额外导入或服务执行。
- 首次静态准确命令（cwd=E:\Agent\comprehensive-cases\15-cyber-town-f009）：E:\Agent\comprehensive-cases\15-cyber-town\.venv\Scripts\ruff.exe check --no-cache scripts/f009_step6_qa.py backend/tests/test_f009_step6_qa.py；同解释器目录 ruff.exe format --check --no-cache 同两个目标。各 exit 1。
- check 诊断：测试文件第 430/431 行 Connectivity.active/scenarios 两处 RUF012（Mutable default value for class attribute）；脚本第 3676/3682 行两处 E501（103 > 100）。format-check 报两份文件需格式化，未执行 formatter。局部替身类每次测试重新定义，当前没有运行证据证明跨测试或 observer 污染；但状态归属调整不在等义机械格式范围内，按非机械停止条件不修复、不加 ClassVar/noqa 绕过。AST/mypy 未执行，完整静态清单未通过，不将剩余额度视为解除停止。
- 本轮机械 0/2，synthetic 0/1、前置序列 0/1、真实 FastAPI 0/1。没有本轮 PID、退出码、监听/health 时间线；不能给出复现或未复现结论。旧机械及所有旧批次消耗不重置。
- 未验证保存点：80a7dda75a029ce681e2eb497954c0ce7c4a50e53e9a3737508590897b7ac71b；沿用原 99 路径 Ordinal 排序、path+NUL+SHA256+LF 聚合。script SHA256 dec41ea12aed108b8225bbdc55aeacaa5c96b3fc38adb9ee41be59c35976bedf；test SHA256 83976d3842aea4bf57c2b66845686629de5d772e8845d1243505e29d62c52dc8。只有两份 QA 相对接续变化，其余 97 项哈希一致，无删除/还原/stash/新环境/Git 交付。
- 新根 E:\Agent\cyber-town-f009-step6-qa\recovery-20260905-01\connectivity-startup-diagnostic-02 尚未创建，仅 current-task 精确预登记；没有新增机器台账/日志/临时资源。恢复资源仍 1,294 文件/232,895,748 bytes，四份旧台账 SHA256 和旧资源大小/mtime 不变。无相关进程及 8000/8001 监听，没有进程需要收口；所有旧证据保留。正式 evidence 只有人工停止摘要，没有本轮机器追加。
- 下一项最小恢复建议：另行批准将 test_startup_preconditions_order_and_assertions 的局部 Connectivity 替身 active/scenarios 初始化为实例状态，随后在剩余机械额度内整理两文件格式、执行完整静态和源码就绪复核；通过后才考虑恢复未消耗的诊断 02 synthetic/定向额度，不新增批次。其他 Win32/类型/运行问题仍未排除，不能承诺仅此一项即可就绪。原 connectivity 根因未确定；历史工具回归、台账隔离及 original_failure_resolved=true 保留，step6_complete=false，Step 7 未授权，未运行 quality/Godot/性能。

### 2026-09-07 RUF012 恢复：mypy 普通类型错误停止

- 接续 80a7dda75a029ce681e2eb497954c0ce7c4a50e53e9a3737508590897b7ac71b 已匹配。本轮非机械修改仅 test_startup_preconditions_order_and_assertions 的局部 Connectivity：active/scenarios 从类属性移到 __init__(self) -> None；新增两实例列表身份不同、修改独立实例不影响运行实例、原断言结束后独立实例状态保持的检查。原场景顺序、请求计数、异常拒绝与 fixture 收口断言保留。新增断言尚未运行，不能称为实例隔离已经实测通过。
- 沿用原机械额度第 1 轮：原 .venv/Scripts/ruff.exe format --no-cache scripts/f009_step6_qa.py backend/tests/test_f009_step6_qa.py；2 files reformatted，exit 0。随后同 ruff.exe check --no-cache 两目标及 format --check --no-cache 两目标均 exit 0。未执行 --fix/全仓自动修复/忽略规则；脚本只有等义格式/换行变化。
- AST 检查用原 .venv/Scripts/python.exe -B -c，逐文件 ast.parse 并以 ast.dump(include_attributes=False) SHA256 核对，不导入 QA。获批列表修正后、formatter 前后两文件 AST 完全相同：script 9c06dbda967aedd207ac85e6fbe22314448ecfd095d4531cd2c7bf4d22ed5452；test d4d569a51ba8e34a36c29e53c068a7fed9b95e53315b58760b702f3f25658b39。
- mypy 准确调用：E:\Agent\comprehensive-cases\15-cyber-town\.venv\Scripts\python.exe -B -m mypy --no-incremental --cache-dir=nul scripts/f009_step6_qa.py backend/tests/test_f009_step6_qa.py；cwd=E:\Agent\comprehensive-cases\15-cyber-town-f009；MYPYPATH=backend/src 在调用作用域绑定后恢复。19:32:24.7410871 至 19:32:33.2973727（+08:00），mypy exit 1（外层 PowerShell exit 0 不代表通过）。
- 精确诊断：backend/tests/test_f009_step6_qa.py:350 为 Dict entry 1 has incompatible type "str": "int"; expected "str": "bool | None" [dict-item]；:399 为 "str": "int | None"，预期同上。两项均来自既有 StartupAPIStub.states：初始化只有布尔值和 None，使状态字典推断过窄；terminate 写入 1、early_exit 写入 7/None 时失败。两目标都被检查，未见 INTERNAL ERROR。此非 RUF012 修正或等义格式问题，未添加类型注解/cast/ignore、未变参或重跑。
- 完整静态未通过，因此未进入源码就绪冻结与任何运行。git diff --check exit 0；两份 untracked QA 另行检查 trailing whitespace=0，当前均 LF；status 路径集合及各文件 SHA256 核对仅两份 QA 本轮变化，其余 97 项哈希不变。两仓仍 feat/f-009-safety-cost-performance / main、HEAD 1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3、staged 0。
- 未验证保存点聚合 34b690378ab334b8eb62cb0e10af16afdb28eddc385ff66d5980d2ff77139231（沿用原 99 路径 Ordinal/path+NUL+SHA256+LF 算法）；script e83113a62b4dd8bdd58d9cac8b25beffa9f77d3764c4349bb29c8a1a0a1648fc；test 56c70b74d5128dda578648ac5d053ec73d043077786219ca7844bdd7a35dadbb。不是就绪/验收通过指纹。
- 额度：沿用机械 1/2，synthetic 0/1、五前置序列 0/1、真实启动 0/1，历史额度不重置。诊断 02 根及 machine-ledger.md 仍未创建，旧四份台账 SHA256/全部旧资源大小与 mtime 未变；恢复仍 1,294 文件/232,895,748 bytes，无相关进程和 8000/8001 监听，未执行任何服务收口或资源删除。正式 evidence 仅人工摘要，无新机器记录；全部旧证据保留。
- 简短复盘：连续暴露的是新增 QA 替身的状态归属与类型建模遗漏，不是原 connectivity 故障证据。后续最小授权应覆盖 StartupAPIStub.states 的完整值类型及其初始化/存活/终止/提前退出/未知退出码赋值点，一次完成局部契约对照；不只改某个整数、不扩展通用框架或运行逻辑。本轮只提出，未实施。
- 唯一下一动作：请求批准上述最小状态类型修正及恢复完整静态；通过后才恢复尚未消耗的诊断 02 条件额度，不新增批次。未启动，故没有本轮 PID/退出码/监听/health 或复现结论；原 connectivity 根因仍未确定，历史工具回归和 original_failure_resolved=true 保留，step6_complete=false，Step 7 未授权，未执行完整 quality/后续 Godot/性能。

### 2026-09-07 states 类型恢复：运行前冻结

- 接续 34b690378ab334b8eb62cb0e10af16afdb28eddc385ff66d5980d2ff77139231 一致。本轮仅 self.states 添加用户批准的 dict[int, dict[str, bool | int | None]]；PID 整数、两项状态保留布尔值、exit_code 保留整数/None。对照初始化、terminate(1)、early_exit(7)/unknown(None)、state 的字典复制、wait 及关联状态断言；未使用 Any/cast/ignore 或修改测试行为。将这一行在内存替换回原声明得到原文件 SHA256 56c70b74d5128dda578648ac5d053ec73d043077786219ca7844bdd7a35dadbb，证明本次只有该行变化；不是还原磁盘文件。
- Ruff check --no-cache、ruff format --check --no-cache、原解释器 AST 两文件（不导入 QA）、git diff --check 全部 exit 0；untracked QA 另查无尾随空白。没有机械修正，沿用 1/2 不增加。mypy 准确命令：E:\Agent\comprehensive-cases\15-cyber-town\.venv\Scripts\python.exe -B -m mypy --no-incremental --cache-dir=nul scripts/f009_step6_qa.py backend/tests/test_f009_step6_qa.py；cwd=功能目录，MYPYPATH=backend/src 后恢复；21:21:39.0151228 至 21:21:47.9056485（+08:00），exit 0，2 source files 无错误。
- 新冻结聚合 457bd148bd30bdc723f26a70d5f4f38da31b1ce9a9abe46ca9953d28de9e78e2（原 99 路径 Ordinal/path+NUL+SHA256+LF 算法）；script e83113a62b4dd8bdd58d9cac8b25beffa9f77d3764c4349bb29c8a1a0a1648fc；test 8a1ab3203e8df914df7f4d8ec1e2fcfff2185a5804eafa32176e0e7db51f9e8c。其余 98 项及两仓分支/HEAD/staged 不变。源码复核保留配置根/实际运行根分离、双实例隔离、句柄/owner/路径/台账边界；本轮未修改 Win32 或运行编排。
- 固定 STARTUP_TESTS 13 函数、44 参数实例，原 9 函数/26 实例加进程状态 8、身份变化 2、前置计数/顺序 6、实际 synthetic 子进程 2；由 AST 读取清单及参数数量，不是 pytest 收集/通过证据。原五前置顺序和后续单启动条件见脚本；不执行 connected/recovery Godot 或六项工程门禁。
- 工具沿用 Python 3.12.10（正式项目 .venv/Scripts/python.exe）、mypy 1.20.2、Ruff 0.16.4、pytest 8.4.2、既有 Godot 4.7.2 与 Git。版本信息只读包元数据；未安装、切换解释器或配置。原五秒/8000/health 不变；新缓存、句柄观察与缺少原六工程门禁仍是明确环境差异，不声称与 quality 等价。
- 唯一运行入口：上述 python.exe -B scripts/f009_step6_qa.py --startup-diagnostic，cwd=E:\Agent\comprehensive-cases\15-cyber-town-f009。启动前根不存在，父链均无 reparse，无相关进程或 8000/8001 监听；current-task 两条 bootstrap 精确预登记有效，子资源沿原类别先登记后操作。128 MiB 根/8 MiB 台账/各产物限额/总 2 GiB 不变；恢复资源 1,294 文件/232,895,748 bytes，四份旧台账哈希与旧资源元数据不变。旧根只读保留。
- 此段仅静态就绪与运行前冻结，不代表 synthetic/前置/真实启动已执行或原 connectivity 已关闭。各额度仍 0/1，运行期间不修改代码/正式 evidence；机器记录只进入诊断 02 独立台账，全部保留。

### 2026-09-07 诊断 02 唯一 synthetic 失败收口

- 上述 --startup-diagnostic 入口只执行一次：21:26:23.4232199 至 21:26:31.2670525（+08:00），诊断进程 exit 1；外层 PowerShell exit 0 不代表通过。根/台账预登记已核对，必要目录与 31 个 Git 可见 game 文件按原守卫先登记后复制/核验；没有实际启动 Godot。
- 固定清单 13 函数/44 参数实例。pytest-summary 实际记录 43 项（13 函数均有调用记录），42 passed/1 failed，无 skip；-x 后剩余 test_startup_observe_actual_business_child[True] 未执行。44 是冻结 AST 清单数量，报告没有独立 collection 总数字段，不将其冒充另有收集记录。测试 runner exit 1，boundary_violations={}。
- 已通过：原 26 实例、进程受控状态/错误归属 8、身份变化 2、前置顺序/计数/实例隔离 6。以上均是 synthetic 证据；配置三参数不代表三个真实运行批次，前置回放不代表实际 Godot 场景。真实 synthetic 子进程观察 [False] 失败，不能宣称 Win32 观察能力就绪。
- 失败节点 backend/tests/test_f009_step6_qa.py::test_startup_observe_actual_business_child[False]，call 阶段，failure_location 为 scripts/f009_step6_qa.py:3293。该源码行抛 step6_startup_process_identity_unavailable；前置条件合并 GetProcessId、GetProcessTimes、QueryFullProcessImageNameW 的失败。现有 metadata 没有保留具体失败 API、GetLastError、调用阶段或完整栈，不能判断是初次绑定、退出后再查、权限或其他原因；不编造异常前后的 PID/退出码，也未追加实验。
- synthetic-summary passed=false、real_start_attempts=0。五前置序列和真实 FastAPI 均未执行；preconditions-summary.json、invocation.json、timeline.jsonl、stdout-redacted.txt、stderr-redacted.txt 不存在，只是事前登记过。没有本轮 FastAPI PID、自然退出码、主动终止码、监听/health 时间线或原 connectivity 复现结论。执行过的 Python 子进程属于 synthetic 验证，不是产品服务。
- 父 observer 23 events、overflow=false、unknown_paths=[]、reparse=0，已写 drain marker 与最终 inventory；native-summary completed=false 对应整体 synthetic 失败，不能称为成功完成。原 inventory 在写入自身前为 37 文件/136,616 bytes；含 native-summary 的实际根为 38 文件/152,976 bytes。退出后只读核验无相关进程和 8000/8001 监听，未人工终止其他进程。
- 独立产物索引：恢复根/connectivity-startup-diagnostic-02/{machine-ledger.md,pytest-summary.json,synthetic-summary.json,native-summary.json,native-monitor-ready.json,native-monitor-drain.marker}。ledger 25,949 bytes / SHA256 6f3a98567d81029df557bee944575e87b52040ab8b5854e8ce757cc8059d9ce6；pytest-summary 9,277 bytes / 77cdb80aa279edf587fade16bad5516104faa71497e9b77f7242922d05324fcd；synthetic-summary 1,378 bytes / 507af3d7a5359bf712fd93e3c0106391898722d1fb17473bd0ba63eaffe2fe24；native-summary 16,360 bytes / 7729b19ec136791faf4e9154ff665e5f8a3bf25f226b50ff9117c48d2c1bc693。全部必须保留，不复用、覆盖或删除。
- 运行前后代码聚合均 457bd148bd30bdc723f26a70d5f4f38da31b1ce9a9abe46ca9953d28de9e78e2；两份 QA 哈希同上，只有本轮获批声明变化，其余 98 项及两仓分支/HEAD/staged 未漂移。四份旧台账 SHA256、旧 1,294 文件大小/mtime 未变；当前恢复总额 1,332 文件/233,048,724 bytes，在根 128 MiB/ledger 8 MiB/总 2 GiB 内。
- 正式 evidence 运行前后均 38,821 bytes / SHA256 0a3efead4e2bb8cc142e8ceda13f072c6e3559196588017d9c9cea7f082bbbf6，没有机器追加；本段仅运行后人工收口。机器过程记录进入诊断 02 自己的固定台账，旧根及保全快照未写入。
- 额度：机械沿用 1/2（本次类型修正未增加机械消耗），synthetic 1/1 已耗，前置序列/真实启动各 0/1；新根已用，未耗额度不允许自动复用失败批次。停止后没有改代码、重复验证或新建其他批次。唯一下一动作建议：另行授权只读定位身份查询三个 API 的生命周期契约与现有取证缺口，先区分原因，再决定最小修复/验证范围，不直接追加完整 quality 或无限诊断。
- 历史工具回归、台账隔离及 original_failure_resolved=true 独立保留；原 connectivity 根因仍未确定。step6_complete=false，Step 7 未授权，完整 quality、五前置 Godot、后续 Godot 与性能均未执行。

### 2026-09-07 最小身份取证增强：静态冻结与运行前登记

- 上轮只读诊断结论：合并判断及多阶段调用使 3293 无法定位 API/内部阶段；stub 在进程退出后仍始终返回身份。退出后映像查询失败是候选，非已定根因。本轮只增强取证，不改变权限、顺序、短路、身份、owner、等待、终止和退出后检查。
- 接续 457bd148bd30bdc723f26a70d5f4f38da31b1ce9a9abe46ca9953d28de9e78e2 一致；两仓 HEAD 1a4fc2cdf142b00f823bebf9b2abe6e74ba23ab3、功能 feat/f-009-safety-cost-performance/正式 main、staged 0、99/19 项变化一致。只改两 QA，其余 97 项哈希未变；旧 1,332 文件/233,048,724 bytes 元数据、五旧台账哈希不变，无相关进程。
- 实现：三 API 分别立即保存 ctypes.get_last_error，StartupIdentityError 固定错误消息与严格字段 schema（单记录 2048 bytes）；阶段、角色、句柄角色、PID/expected_pid、已知创建时间与 approved/unknown 映像摘要、最近存活/单调时间及进入收口状态。未知保留 None，不记录原始路径或任意异常属性。MetadataReporter 单独保存身份诊断，不改变 canonical 通路；最终 write_pytest_summary 再验证并对新根实施 1 MiB 上限。
- 准备/静态第 1 轮：两文件 Ruff format --no-cache 等义整理；Ruff check 发现四处 RUF043（正则须显式 raw）；format-check、AST、mypy、git diff --check 均 exit 0。第 2 轮仅四处字符串加 r，不改匹配目的；完整清单全部 exit 0，额度 2/2。两文件均 LF，无尾随空白。未执行全仓自动修复。
- 准确静态命令（cwd 功能目录）：正式 .venv/Scripts/ruff.exe check --no-cache <两 QA>；同 ruff.exe format --check --no-cache <两 QA>；正式 .venv/Scripts/python.exe -B -c 仅 pathlib 读取/ast.parse 两文件（不导入 QA）；同 python.exe -B -m mypy --no-incremental --cache-dir=nul scripts/f009_step6_qa.py backend/tests/test_f009_step6_qa.py（MYPYPATH=backend/src 后恢复）；git --no-optional-locks diff --check 及 tracked/untracked 清单/哈希核对。沿用原工具链，未安装依赖。
- 新冻结（原 Ordinal/path+NUL+SHA256+LF 算法）：bcdb84fb6e2ff30bf16cc6e74964369237a4e1674b553f7f084ec4a8b759929a。script edf116b7bfa2540fe1f0d1244090d921e2029a84bb2f8951f19c4cb5f63f1d95；test 47c1184d5b6b1c2af0ebe2b1a67a582e9f1ead952914a4771f0406d6d746c0d7。
- 固定 IDENTITY_TESTS：A=identity_api_failure(3)、identity_after_exit(4)、process_observation(8)、process_rejects_identity_changes(2)；B=identity_report_chain(24)、identity_report_rejects_invalid_fields(7)、identity_summary_limit(1)、canonical_diagnostic_reports_concurrent_failures_without_cross_talk(1)；C=observe_actual_business_child[False]/[True] 各 1。完整函数名均带 test_startup_ 前缀，canonical 使用 test_qa_ 前缀，以代码清单为准。合计 9 函数/52 实例为 AST 冻结，不是已执行证据；A/B 的阶段/角色回放不冒充真实系统行为。
- 唯一新根 startup-process-observation-validation-01 当前不存在，父链无 reparse；精确预登记/产物/额度见 current-task。运行命令：正式 .venv/Scripts/python.exe -B scripts/f009_step6_qa.py --identity-validation；无产品入口调用、不复制 Godot。父 native observer、受保护子进程和固定独立台账复用既有实现；本根 32 MiB、ledger 8 MiB、总 2 GiB。任一失败保留取证后停，无修复重跑。运行前定向额度 0/1，其他运行额度为零，step6_complete=false。

### 2026-09-07 身份取证候选：最终源码就绪复核停止（未运行）

- 完整静态通过后，创建前最后调用链核对发现新增实现的报告缺口：subprocess_isolation 在脚本 774 先从 scripts.f009_step6_qa 导入 child_entrypoint；脚本参数分支 844 使用 runpy.run_path(target, run_name="__main__")，会另建一组 __main__ 类。实际 run_pytest 构造该组 MetadataReporter，而测试从 scripts.f009_step6_qa 导入并抛出另一组 StartupIdentityError。620 的 type(error) is StartupIdentityError 不匹配，导致实际失败的身份诊断未被采集。此结论来自明确源码调用链，没有新增执行实验。
- test_startup_identity_report_chain（测试 642 起）以同一导入模块创建异常与 reporter，虽覆盖底层 API/异常/报告器/最终文件序列化，但没有覆盖真实受保护 pytest 入口的双模块身份组合。这是本轮实现/就绪测试的遗漏，不是历史 Win32 身份查询失败或原 connectivity 的已定根因。原 canonical 代码分支未被移除，也未新增运行来证明其当前实际入口覆盖。
- 因准备/静态 2/2 已耗，本轮立即停在资源创建前，没有第三轮改动/静态、没有 pytest、synthetic、FastAPI、Godot、connectivity、quality 或性能；没有启动需要收口的 synthetic 进程。前述“源码复核通过/运行前冻结”的阶段性表述已撤回：当前只可称静态通过的未验证保存点，取证链路没有通过证据。A/B/C 全部未执行，52 仅候选 AST 清单；原 False/True 均无本轮结果，不给出 API/阶段/Win32 错误码或复现结论。
- 保存点仍 bcdb84fb6e2ff30bf16cc6e74964369237a4e1674b553f7f084ec4a8b759929a；两 QA 哈希同上，其余 97 项不变。结束时新根仍不存在，定向额度 0/1；全部旧 1,332 文件/233,048,724 bytes 和五份台账哈希不变，旧文件 size/mtime 清单校验一致，无相关进程。本轮资源增量 0，未产生独立机器记录或 observer 报告。根/台账和子资源预登记作为未创建时序保留，不覆盖旧证据。
- 唯一下一动作：另行批准最小异常模块身份一致性适配（仍两 QA）与真实受保护 pytest 报告通路验证，并恢复必要完整静态；不得按类名、任意异常属性或放宽类型/schema 来绕过。仅修报告身份和验证缺口，不改进程身份/owner/权限/终止或退出后检查；静态和就绪通过后才使用此新根原 0/1 定向额度，不新开批次。本轮未自行执行该修复。
- 简短复盘：触发点是新增自测用同模块对象验证报告器；遗漏是没有在实现前把实际启动方式/runpy 双加载纳入异常类型契约。后续应先审查“实际入口→模块身份→异常来源→pytest hook→最终序列化”，再设计链路负例；建议落点为两 QA 的直接回归，不修改全局安全规则。历史工具回归、台账隔离、original_failure_resolved=true 独立保留；原 connectivity 根因未确定，step6_complete=false，Step 7 未授权。

### 2026-09-07 异常模块身份恢复：静态与运行前冻结

- 接续 bcdb84fb6e2ff30bf16cc6e74964369237a4e1674b553f7f084ec4a8b759929a 一致；两仓原分支/HEAD/staged 0，旧 1,332 文件/233,048,724 bytes 及五台账未变，无相关进程。用户新批准两轮准备和恢复原一次定向额度，不新开批次。
- 仅两 QA 修改：verified_report_classes 核验规范模块 __file__/ModuleSpec.origin 和构造函数代码来源，使用本地及经核验模块的明确类对象；不按类名识别，不读取任意异常属性，不合并 guard/台账/observer 实例。canonical 保留并接受经核验对应类。非法身份字段继续抛校验错误，仅新增固定拒绝码/nodeid/phase 便于精确验证预期 pytest INTERNALERROR，不改变其退出码。
- 第 1 轮 Ruff format --no-cache 两文件整理，Ruff check/format-check、AST 两 QA 与 synthetic fixture 及 git diff --check 通过；mypy 两处类型收窄诊断（返回 tuple 的类对象可空、BaseException 无 diagnostic 声明）。第 2 轮增加明确 class 检查和仅对已验证 canonical 实例读取固定字段后，完整静态全部 exit 0。无 noqa/ignore/cast、依赖变更或 Win32/权限/owner/终止逻辑变更；本轮 2/2，旧 2/2 保留。
- 静态命令与环境沿上条原完整清单：正式 .venv/Scripts/ruff.exe check、format --check 均 --no-cache；正式 .venv/Scripts/python.exe -B 仅 AST 读取，不执行模块；同 python -B -m mypy --no-incremental --cache-dir=nul 两 QA、cwd 功能目录、MYPYPATH=backend/src 后恢复；tracked/untracked/空白和原聚合算法核对。两文件 LF、无尾随空白。
- 新冻结 2bb5f5744af80e1223418310874c3d803141b8a34b0480fc51a02294501b6aa6；script b5254e4ccd2d1bc4fbfb1f0afcefd76ab18dd5f03b54d93704859f2b06e6df5f；test 250dd89dadd7f2cc1fd266e0916af85045a2a669614257a78aaa878099e56a27。只有两 QA 变化，其他 97 项不变。
- 固定顶层 65 参数实例/11 函数：保留前条 52 项，B 在 C 前新增 test_startup_report_module_source_rejection(3)、test_startup_real_pytest_report_path(10)。A17→B46→C2。10 个真实报告回归 = import/runpy × call/setup/forged/invalid/canonical；每个子 pytest 先 test_control 通过，再 test_expected_failure 精确失败。非法字段要求 exit 3 和固定拒绝记录，其余要求 exit 1 和对应失败摘要；父回归核对模块名、节点/阶段、字段、计数、无串项和脱敏。当前数量来自 AST，不代表已经运行。
- 原新根尚不存在，bootstrap 与封闭 2×5 子资源已预登记；本根/台账/子资源限额及父 observer/owner 守卫不变。唯一执行命令仍为 python.exe -B scripts/f009_step6_qa.py --identity-validation。机器证据只进新根，当前文档运行期不变；任何非预期失败即停。当前定向 0/1，不运行任何产品服务/Godot/quality/性能。
