# T-0057: Raveil atomic-claim prior-art audit

Status: Non-authoritative literature review; no novelty or clearance conclusion
Date: 2026-09-20
Task: T-0057 supplementary audit; Gate 5 prerequisite / T-0044 comparison design
Context: RFC-0001, RFC-0004, RFC-0005; ADR-0014, ADR-0039, ADR-0041; EXP-0003
Evidence class: literature + repository code/record inspection; no new performance measurement

## 判定の要点

Raveilの広い「依存を明示し、実行知識を保存して再利用する」という説明だけでは差別化できない。
28件に分解し、指定された10系統と280セルで照合した。個々の仕組みの先行例と、
Raveil全体の新規性・性能・実装完成度を別々に判定する。

- **既知の仕組みとして扱う:** 明示依存、静的schedule、空間配置、構成再利用、局所memory、
  明示移動、runtime readiness、processorとの分担、限定実行部のOoO探索省略、bounded graph。
- **部分重複または調査不足:** effects/alias/resource admission、4-plane権限、identity束縛、
  意味検証、private publication/cancel、Experience保持・選択・失敗利用、lifetime ROI。
  独自名称や既知部品の組合せを根拠に新規としない。
- **C26は対象条件で否定済み:** EXP-0003のbounded Experience 5%改善仮説。
  **C27は未検証:** matched CPUに対する全lifecycle便益。
  **C28は未確立:** 統合そのものの独自性。

このclaim群は、既存記録の機構記述・採択条件・研究仮説を比較可能な単位に正規化したもの。
28件すべてを「従来Raveilが発明と公言していた」と扱わない。とくにC28は既存レビューが
明示的に保留していた命題であり、今回も成立としない。

## 対象treeと過去レビューの訂正

基準HEADは `7c38a36a7ca5e9f19fc930cb1a6dc80c09e432f6`。元branchは
`feat/t-0106-project-workspace`、本監査branchは `research/t-0057-atomic-claim-audit`。
開始時からCPU token診断・records等18ファイルに未コミット変更があった。
それらの機能を今回の成果とはしない。他の多数のlocal branchの実装・実験はこの監査の
実装確認対象に混ぜていない。本資料はこのcheckoutの主張集合の監査である。

[2026-08-11 matrix](2026-08-11-T-0057-native-graph-prior-art-matrix.md)は
OoO/EPIC/TRIPS/EDGE/WaveScalar/DySER/CGRAを中心にしたmechanism-level reviewだった。
Groq/SambaNova/Graphcore/Cerebras/Tenstorrent/Plasticineの明示照合がなく、T-0057完了から
広範な先行研究網羅性を読み取れる状態は不適切だった。完了済みなのはADR-0039の
**bounded simulation契約定義**。その受容を遡って取り消したり、今回新ISAを受容したりしない。

## 読み方と再検証可能性

`E` = そのatomic mechanismに先行例あり。実装細部や全systemの同一性ではない。
`P` = 部分重複。成立しない条件・粒度差はCSV/JSONのrationaleに記載。
`D` = 選んだ資料が示す具体的方式の相違。会社全製品・系統全体の不存在ではない。
`U` = 読んだ範囲では未確定。空白の代用ではなく、未確認対象を明示した結果。
Uが多いauthority/Experience列から「競合にはない」と結論しない。

[JSON](2026-09-20-T-0057-atomic-claim-matrix.json)が各claim、各セル、source ID、
版、URL、section/page locator、差分理由を保持する。
[CSV](2026-09-20-T-0057-atomic-claim-matrix.csv)は同じ280セルのlong format。
Markdownのセルは判定とsource IDの索引であり、詳細根拠は両artifactにある。

TRIPSは具体的実装、EDGEはISAの系統として分ける。CGRA列はADRESの一次論文を代表例にする。
dataflow machine列はManchester tagged-tokenとWaveScalarを明記して使い分け、古典全機種を
一括判定しない。PlasticineとSambaNovaの著者・部品名の近さから実装同一性を推定しない。

## 28 atomic claimsと個別処置

| ID | 検査する一つの命題 | Raveil内の状態・locator | 判定 | 残る差分／必要な証拠 |
|---|---|---|---|---|
| C01 | 演算間のproducer–consumer依存を実行表現に明示する | 部分実装; `raveil/static_region.py:compile_static_stencil_descriptor; RFC-0001 §Proposal` | **既知** | 明示グラフ自体は撤回対象。残るのはeffects/authorityを含む契約の検証可能性。 |
| C02 | メモリアクセスにobject単位のREAD/WRITE effectを付ける | 限定実装; `raveil/static_region.py:compile_static_stencil_descriptor; RFC-0001 §Proposal` | **部分重複** | read/write命令やmemory orderとcapability付きobject effectは別。型付きeffect/領域解析との追加比較が必要。 |
| C03 | alias不明の領域を実行前admissionで拒否する | 限定実装; `raveil/static_region.py:validate_static_stencil_descriptor; RFC-0005 §Alias and memory contract` | **部分重複** | 現行は固定A/B記述の独立性検査。一般alias証明器の実装・独自性を主張しない。 |
| C04 | 実行前admissionで使用資源の上限を検証する | 限定実装; `raveil/static_region.py:validate_static_stencil_descriptor; RFC-0005 §Construction and admission` | **部分重複** | 配置時の資源制約は既知。敵対的proposalへの独立検査・証明書形式の差分は未評価。 |
| C05 | コンパイラが固定した演算scheduleで限定kernelを実行する | 契約＋限定実装; `raveil/static_region.py:compile_static_stencil_descriptor; hardware/chisel/StaticStencilRegion.scala; RFC-0005 §Candidate boundary` | **既知** | Groq/ADRESが直接先行。Raveil現在のowned-memory接続にはrequest/response待ちがあり、全系固定latencyとは別。 |
| C06 | 演算を空間的な機能資源へ配置する | 構想＋固定候補; `RFC-0001 §Proposal; docs/ARCHITECTURE.md §RISC-V and Graph Execution Subsystem` | **既知** | 自動汎用mapperは未実装。配置・routing単体は差別化しない。 |
| C07 | 実行構成を保存して新しい入力で再利用する | 限定契約/実装; `raveil/static_region.py:configuration_id; RFC-0005 §Identity and invalidation` | **既知** | WaveCacheに新入力での再利用先行例。ADRES context RAMは部分対応。結果memoizationと構成再利用は区別する。 |
| C08 | software管理の局所memoryを演算器の近傍に置く | 限定simulation; `hardware/chisel/StaticStencilRegion.scala; RFC-0005 §Alias and memory contract` | **既知** | 容量・port・latency・controllerを含む同一資源比較が必要。scratchpadという名前では差がない。 |
| C09 | データ移動を実行計画として明示する | 構想＋限定実装; `RFC-0001 §Proposal; raveil/graph_mvp.py:MemoryPlan; raveil/static_region.py` | **既知** | descriptorのMemoryPlanは一般的な移動強制機構ではない。移動/同期/host境界費用を比較する。 |
| C10 | 可変遅延に対して実行時readiness/backpressureを残す | 構想；command/memory handshakeのみ限定実装; `RFC-0001 §Proposal; hardware/chisel/StaticStencilRegion.scala` | **既知** | Plasticine/Manchester等に先行例。RFC-0005にはruntime token schedulerがないためelastic Graph実装済みとはしない。 |
| C11 | graphに適さない処理を汎用processor側に残す | 受容済み方針＋限定baseline; `docs/decisions/ADR-0003-risc-v-control-and-daphnis-execution.md; RFC-0001 §Dynamic islands` | **既知** | ADRESのkernel/non-kernel分割が直接比較。hostの存在だけで自動fallback一致とはしない。 |
| C12 | 限定Graph実行部で汎用OoO依存探索機構を省く | 限定simulation; `hardware/chisel/StaticStencilRegion.scala; RFC-0005 §Candidate boundary` | **既知** | Groqが直接先行、ADRESはcompiler scheduleの部分対応。CPU fallback、通信、検証状態を含む総コスト減は別claim C27。 |
| C13 | Program/Graph/Data/Experienceの書込み権限を分離する | Sonatine限定実装; `sonatine/include/plane_authority.h; sonatine/src/job_authority.c; ADR-0030` | **未確立** | 10系統の本文ではこの4分類を未確認。capability OS、Harvard、typed IRとの比較なしに新規としない。 |
| C14 | variantをprogram/contract/target等のidentityに束縛する | host限定実装; `raveil/graph_mvp.py:GraphVariant,OptimizationProposal,MiroirsStructuralValidator; raveil/static_region.py:configuration_id` | **未確立** | hashと来歴束縛だけでは新規性なし。content-addressed build、artifact signing、cache invalidationとの比較が必要。 |
| C15 | 最適化結果を独立した意味検査で検証する | 有限入力で実装; `raveil/graph_mvp.py:PavaneSemanticOracle; raveil/static_region.py:static_stencil_oracle` | **部分重複** | X1が直接の検証思想先行。checksum一致は全入力意味等価証明ではない。 |
| C16 | 検証承認まで出力をprivateに保ち可視化を遅延する | Sonatine byte shadow実装；Graph全lifecycle未完; `sonatine/src/job_authority.c; ADR-0031; RFC-0005 §Completion, interruption, and publication` | **部分重複** | TRIPS block commitと可視化延期が類似。Raveil job/object publicationはCPU architectural commitと同一ではない。 |
| C17 | cancel時に未公開出力を無効化する | 限定simulation/host; `hardware/chisel/StaticStencilRegion.scala; tests/test_simulation_adapter.py; RFC-0005 §Completion, interruption, and publication` | **部分重複** | speculative state discardやtransaction rollbackとの比較が必要。全CPU post-A rollbackは未完。 |
| C18 | admitするgraphの大きさを制限する | 限定実装; `raveil/static_region.py:validate_static_stencil_descriptor; RFC-0005 §Candidate boundary` | **既知** | TRIPS等のbounded blockが先行。64 nodes/128 edgesという定数自体は研究貢献ではない。 |
| C19 | 学習器の提案に実行承認権限を与えない | host/方針で実装; `raveil/graph_mvp.py:GraphExecutor; docs/decisions/ADR-0002-experience-advises-measurement-governs.md` | **部分重複** | X1/X2は提案と検査/実測を分ける部分先行。全capability境界の一致は未確認。LLM未導入。 |
| C20 | trusted baselineの実測後にcandidateを選択する | host/measurement実装; `raveil/policy.py:Tuner.tune; raveil/graph_mvp.py:GraphExecutor.execute` | **部分重複** | X2の実測選択と類似。各trialでbaseline-firstを強制する細則の利点はablationで示す必要。 |
| C21 | 最適化の生の観測履歴をappend-onlyに保存する | Python実装; `raveil/experience.py:ExperienceStore.append; tests/test_minimum.py` | **未確立** | 10系統のhardware資料には記載未確認。ログ/実験DBの既知性と本schemaの差分を別調査する。 |
| C22 | onlineで使うExperience集合の大きさを制限する | Python実装; `raveil/experience.py:ExperienceStore._consolidate; tests/test_minimum.py` | **未確立** | 記録上の上限は確認。coreset/continual learning/replay buffer先行例との厳密比較は残る。 |
| C23 | 似たworkload/contextの過去結果でcandidateを順位付けする | Python実装；実機便益未立証; `raveil/experience.py:ExperienceStore.nearest; raveil/policy.py:NearestExperiencePolicy.rank` | **部分重複** | X3のkernel-class transferが先行。NN距離、shape、hardware差を含むtransfer利得は未立証。 |
| C24 | 過去の失敗を近傍candidateの評価へ反映する | Python実装; `raveil/policy.py:NearestExperiencePolicy.rank; tests/test_minimum.py:test_low_memory_experience_avoids_known_invalid_keep_candidate` | **部分重複** | X2はinvalid/timeoutを観測。Raveilの距離減衰penalty/尾部保持との一致は未確認、既知negative-transfer研究を追加比較。 |
| C25 | 将来の再利用回数を含む総費用で最適化投資を判断する | 研究仮説；T-0058 open; `docs/VISION.md §Economic objective; docs/EXPERIENCE.md; TODO.md T-0058` | **部分重複** | X2/X3は探索費用の償却・再利用が先行。検証/rollback/storage込みの純便益を測る必要。 |
| C26 | 等予算下でbounded Experienceがcoldよりlatency/energyを各5%以上改善する | 事前登録仮説は否定済み; `docs/experiments/EXP-0003-gate1-bounded-experience.md §Final pinned TVM result and disposition; docs/STATUS.md` | **否定済み** | EXP-0003の固定Cとpinned TVMの対象条件に限定。両中央値改善0。Experience一般やGraph hardwareの反証にはしない。 |
| C27 | Graphがmatched CPUより全lifecycle費用で有利になる | 未検証仮説; `RFC-0005 §Matched controls and accounting; TODO.md T-0044; docs/STATUS.md` | **未検証** | 相手の性能表は証拠にならない。同一演算/資源/メモリとcold/warm反復、area/timing、検証・fallback費用が必要。 |
| C28 | 契約・検証・Experienceの統合自体が既存方式にない | 調査対象の推論；既存記録は未主張; `docs/research/reviews/2026-08-09-RFC-0001-industry-prior-art.md §Adoptable research framing` | **未確立** | 部品が既知でも統合新規とも非新規とも即断しない。単一先行systemの全要素対応とcontrolled ablationが必要。 |

## Claim × system matrix

| Claim | Groq | SambaNova | Graphcore | Cerebras | Tenstorrent |
|---|---|---|---|---|---|
| C01 | P G1 | E S1 | P I2 | P C1 | P T1 |
| C02 | P G1 | P S1 | P I2 | U C1 | P T1 |
| C03 | U G1 | U S1 | P I2 | U C1 | U T1 |
| C04 | P G1 | P S1 | P I2 | P C1 | P T1 |
| C05 | E G1 | P S1 | P I1 | D C1 | P T1 |
| C06 | E G1 | E S1 | E I2 | E C1 | E T1 |
| C07 | P G1 | P S1 | P I2 | P C1 | P T1 |
| C08 | P G1 | E S1 | E I1 | E C1 | E T1 |
| C09 | E G1 | E S1 | E I1 | E C1 | E T1 |
| C10 | D G1 | P S1 | P I1 | E C1 | E T1 |
| C11 | U G1 | P S1 | P I1 | P C1 | P T1 |
| C12 | E G1 | P S1 | P I1 | P C1 | U T1 |
| C13 | U G1 | U S1 | U I1,I2 | U C1 | U T1 |
| C14 | U G1 | U S1 | U I1,I2 | U C1 | U T1 |
| C15 | U G1 | U S1 | U I1,I2 | U C1 | U T1 |
| C16 | U G1 | U S1 | U I1,I2 | U C1 | P T1 |
| C17 | U G1 | U S1 | U I1,I2 | U C1 | U T1 |
| C18 | P G1 | U S1 | P I2 | U C1 | U T1 |
| C19 | U G1 | U S1 | U I1,I2 | U C1 | U T1 |
| C20 | U G1 | U S1 | U I1,I2 | U C1 | U T1 |
| C21 | U G1 | U S1 | U I1,I2 | U C1 | U T1 |
| C22 | U G1 | U S1 | U I1,I2 | U C1 | U T1 |
| C23 | U G1 | U S1 | U I1,I2 | U C1 | U T1 |
| C24 | U G1 | U S1 | U I1,I2 | U C1 | U T1 |
| C25 | U G1 | U S1 | U I1,I2 | U C1 | U T1 |
| C26 | U G1 | U S1 | U I1,I2 | U C1 | U T1 |
| C27 | U G1 | U S1 | U I1,I2 | U C1 | U T1 |
| C28 | U G1 | U S1 | U I1,I2 | U C1 | U T1 |

| Claim | Plasticine | TRIPS | EDGE | CGRA | dataflow machine |
|---|---|---|---|---|---|
| C01 | E P1 | E R1 | E E1 | P A1 | E D1 |
| C02 | P P1 | P R1 | P E1 | P A1 | P D2 |
| C03 | P P1 | D R1 | U E1 | U A1 | D D2 |
| C04 | P P1 | P R1 | P E1 | P A1 | U D1,D2 |
| C05 | P P1 | D R1 | P E1 | E A1 | D D1 |
| C06 | E P1 | E R1 | P E1 | E A1 | P D1 |
| C07 | P P1 | P R1 | U E1 | P A1 | E D2 |
| C08 | E P1 | D R1 | U E1 | P A1 | P D1 |
| C09 | E P1 | E R1 | E E1 | E A1 | E D1 |
| C10 | E P1 | E R1 | E E1 | U A1 | E D1 |
| C11 | U P1 | D R1 | P E1 | E A1 | D D2 |
| C12 | P P1 | P R1 | P E1 | P A1 | P D1 |
| C13 | U P1 | U R1 | U E1 | U A1 | U D1,D2 |
| C14 | U P1 | U R1 | U E1 | U A1 | U D1,D2 |
| C15 | U P1 | U R1 | U E1 | U A1 | U D1,D2 |
| C16 | U P1 | P R1 | P E1 | U A1 | U D1,D2 |
| C17 | U P1 | P R1 | U E1 | U A1 | U D1,D2 |
| C18 | P P1 | E R1 | P E1 | P A1 | U D1,D2 |
| C19 | U P1 | U R1 | U E1 | U A1 | U D1,D2 |
| C20 | U P1 | U R1 | U E1 | U A1 | U D1,D2 |
| C21 | U P1 | U R1 | U E1 | U A1 | U D1,D2 |
| C22 | U P1 | U R1 | U E1 | U A1 | U D1,D2 |
| C23 | U P1 | U R1 | U E1 | U A1 | U D1,D2 |
| C24 | U P1 | U R1 | U E1 | U A1 | U D1,D2 |
| C25 | U P1 | U R1 | U E1 | P A1 | U D1,D2 |
| C26 | U P1 | U R1 | U E1 | U A1 | U D1,D2 |
| C27 | U P1 | U R1 | U E1 | U A1 | U D1,D2 |
| C28 | U P1 | U R1 | U E1 | U A1 | U D1,D2 |

## 一件ずつの対抗説明と比較条件

| 系統 | Raveilから新規性を取り除く直接の点 | 同一視してはいけない点／次に比較するもの |
|---|---|---|
| Groq | C05/C06/C09/C12。コンパイラが時間とデータ移動を管理する方向は先行。G1 §II。 | TSPにもinstruction fetch/decodeがある。「scheduleを持つ」から全命令制御不要とはならない。Raveilはstencil限定、TSPはtensor stream。 |
| SambaNova | C01/C06/C08/C09。graphをPCU/PMUへ空間配置する。S1 slides 5–16。 | スライドで独立verifier、rollback、Experienceを確認できないことは非搭載証拠でない。PMU/AG/host境界を含む費用が対照。 |
| Graphcore | C06/C08/C09。graph/variable mappingと局所memory、明示exchange。I1/I2。 | BSPのsyncとtile内命令実行を残す。Graphという名前だけでRFC-0005と同じ機械ではない。barrier/vertex granularityを揃える。 |
| Cerebras | C06/C08/C09/C10。配置・local memory・wavelet-triggered tasks。C1。 | PEはPC/codeを持ちtask pickerで動く。wafer規模と小さなstencil RTLのraw throughputは比較しない。 |
| Tenstorrent | C06/C08/C09/C10。core割当、L1、専用data movement、CB同期。T1。 | RISC-V搭載はRaveilのfallback semanticsと同義でない。reader/compute/writer間のbuffer費用と待ちを含める。 |
| Plasticine | C01/C06/C08/C09/C10。parallel patterns、PCU/PMU、token/credit。P1 §§2–3。 | 局所static pipelineとunit間の動的制御は両立する。Raveilが今除外している疎・不規則処理を持つ。 |
| TRIPS | C01/C06/C09/C10/C18。direct targets、bounded block、data-ready issue。R1 §2。 | reservation station、cache、speculation、architectural block commitを残す。private B publicationは意味が違う。 |
| EDGE | C01/C09/C10と「hardwareによる依存再発見を減らす」という問題設定自体。E1 pp.45–47。 | ISA系統とTRIPSの実装パラメータを区別。Raveilは現在product ISAを選定していない。 |
| CGRA / ADRES | C05/C06/C09/C11が直接対応。C01/C07/C12は部分対応。modulo schedule、configuration RAM、VLIW分担。A1 §§2–3。 | Raveilのstatic候補に特に近い対照。A1はcache hierarchyを共有し、固定scratchpadと等価ではない。 |
| dataflow machine | C01/C09/C10はManchester、C07はWaveCacheに先行。D1/D2。 | tagged token matching、wave ordering、配置、memory semanticsは別々。token管理の削減をstatic限定の利益として測る必要。 |

## Authority / Experienceを逃げ道にしない補助比較

10系統は主として実行機構の文献なので、C13–C25には資料の射程外が多い。
この欠落を統合新規性に転換せず、異なる研究分野の直接先行例も置く。

| Source | 対象claim | 確認した先行点 | 残る差分 |
|---|---|---|---|
| X1 Translation Validation | C15/C19 | compilerの結果を別途検査する。 | Raveilは有限入力oracle/checksum。一般的な証明手法の新規性はない。capability境界の一致とは別。 |
| X2 Ansor | C19/C20/C24/C25 | 学習cost modelで探索し実測をfeedback、task別に探索時間を配分、invalid/timeoutも観測する。 | baseline-firstの強制、append-only/active-limit、距離減衰失敗penalty、rollbackを含む同一protocolは未確認。 |
| X3 Transfer-Tuning | C23/C25 | kernel classとshapeを跨いでscheduleを再利用、invalid transferを区別する。 | Raveilの全context・hardware transfer、negative-transfer抑制、総費用削減は別途検証。 |

C13/C14/C16/C17/C21/C22について、capability OS、content-addressed artifact、transaction/shadow paging、
experiment DB、coreset/experience replayの系統的claim照合は未完である。
Proof-Carrying Codeの著者資料も探索したが、今回のPDF抽出は文字化けし、本文locatorに基づく
判定には使っていない。したがって「安全性＋履歴はRaveil固有」という結論も出せない。

## 比較で生き残る研究課題と停止条件

残る候補は「この限定workload集合・契約・実装条件で、既知のGraph/CGRA技法に
Raveilのadmission/identity/private publicationを追加する費用と利益を再現可能に測れるか」。
これは新規性認定ではなく研究設問である。最低限、次を同一workloadで対照にする。

1. matched sequential/Rocket/BOOMに加え、同じ資源上の普通のstatic/VLIW/CGRA-like schedule。
   大規模商用chip同士の数値競争を今回の小規模RTLに要求するのではなく、
   観測した既知機構を対照として切り分ける。
2. configurationを毎回作る条件／reuseする条件。入力bytesは更新し、結果cacheを禁止する。
3. 検証・権限・identity・publicationを同じ強さで両側に適用する。安全性を外して速さを作らない。
4. 別campaignでのみ、cold／exact-key reuse／nearest transfer／bounded／full-historyを
   同じtarget測定予算で比較。EXP-0003を都合よく再解釈しない。

ライフサイクルのlatencyについては、例えば
`Delta(N) = N*(Tbaseline - Tgraph) - (Tbuild + Tverify + Tinstall + Tlookup + Trecovery)`
を定義し、各項の計測境界と重複計上を固定する。energyは別に積算する。
area、storage、tail riskを単位換算なしで時間へ足さない。符号が正と確認できない領域では
勝利を主張しない。matching未完・semantic failure・retained machineryで利益消滅ならno-go。
RFC-0005のno-go条件を緩和せず、C27はT-0044の未検証仮説のままとする。

## 書き換えるべき対外説明

避ける表現: 「グラフを直接実行する新CPU」「依存再発見をなくした初の方式」
「構成を覚えること自体が新しい」「AIが蓄積するので速くなる」
「競合には検証・失敗履歴がない」「統合したので新規」。

現時点で根拠のある表現:
「Raveilは既知の明示グラフ・静的実行・再利用技法を土台に、admission、意味検査、
identity、private publication、非権威的Experienceの境界を検証する研究実装である。
限定機能の正しさは確認されているが、matched hardwareの総費用優位と統合の新規性は
未立証であり、最初のExperience改善仮説は対象条件で否定された。」

## 一次資料台帳

ページは特記なき場合PDF先頭を1とする。web本文のsection名を恒久locatorの代わりに使う場合は
versionを併記した。全URLは2026-09-20に本文を開いて照合。
ローカルPDFのhash固定・全改訂履歴・errata/retractionの網羅確認は未実施。
G1/D1のミラーについてはホストの権威と原論文の著者性を区別する。

- **G1** — [Abts et al., Think Fast: A Tensor Streaming Processor (TSP) for Accelerating Deep Learning Workloads](https://www.researchgate.net/publication/342914141_Think_Fast_A_Tensor_Streaming_Processor_TSP_for_Accelerating_Deep_Learning_Workloads)。ISCA 2020; DOI 10.1109/ISCA45697.2020.00023; author upload 2022-01-24。Locator: §I.A–B, printed pp.146–147: functional slicing / parallel lanes and streams; §II Architecture Overview, printed p.147; §II.C staggered instruction execution; §II, printed p.147 and §II.B memory bandwidth; §III.A instruction fetching。Max Bakerのauthor-upload本文を確認。公式旧PDFは404/502、別ミラーはTLS/取得失敗。2026年製品記事の仕様を2020年TSPへ遡及しない。
- **S1** — [Prabhakar and Jairath, SambaNova SN10 RDU: Accelerating Software 2.0 with Dataflow](https://hc33.hotchips.org/assets/program/conference/day2/SambaNova%20HotChips%202021%20Aug%2023%20v1.pdf)。Hot Chips 33, 2021-08-24。Locator: slides 5–6: SambaFlow / spatial compilation; slides 11–16: tile, PCU, PMU, address generation, switch; slides 4, 11: host and RDU connectivity。公式学会のベンダー発表。SN10のみ。Plasticineの詳細をSambaNova製品に自動転記しない。
- **I1** — [Graphcore, IPU Programmer’s Guide: IPU hardware overview](https://docs.graphcore.ai/projects/ipu-programmers-guide/en/3.3.0/about_ipu.html)。SDK guide 3.3.0。Locator: §2.1 Memory architecture; §2.2 Execution; §2.3 Tile architecture。命令を実行するtileとBSP。名称Graphから命令粒度dataflow firingを推定しない。
- **I2** — [Graphcore, IPU Programmer’s Guide: Programming model](https://docs.graphcore.ai/projects/ipu-programmers-guide/en/3.3.0/programming_model.html)。SDK guide 3.3.0。Locator: §3.2.1 Data variables; §3.2.2 Copying data and executing compute sets; §3.2.4 Compute sets; §3.2.3 Control flow: sequences, conditionals and loops; §3.5.1 Variable liveness。固定された変数アクセス集合とtile mappingを、Raveil capability証明と混同しない。
- **C1** — [Cerebras, A Conceptual View](https://cerebras-sdk-docs-140.netlify.app/computing-with-cerebras)。Cerebras SDK documentation 1.4.0。Locator: A processing element (PE); The programming model; Programs and Tasks; Task IDs and Types of Tasks; Communication; Communication and examples of @bind_data_task。公式SDKの版別サイト。WSE-2のcolorとWSE-3のinput queueの相違を保持。各PEにはPCとcodeがある。
- **T1** — [Tenstorrent, TT-Metalium Eltwise binary example](https://docs.tenstorrent.com/tt-metal/v0.59.0/tt-metalium/tt_metal/examples/eltwise_binary.html)。TT-Metalium v0.59.0。Locator: Circular buffers; Data movement and compute kernels; Host code / CreateKernel / EnqueueWriteBuffer; reader and compute kernel listings。reader/compute/writerとreserve/wait/push/popを確認。文書中のCB数とc_16例の不整合があるため個数は採用しない。
- **P1** — [Prabhakar et al., Plasticine: A Reconfigurable Architecture for Parallel Patterns](https://csl.stanford.edu/~christos/publications/2017.plasticine.isca.pdf)。ISCA 2017; DOI 10.1145/3079856.3080256。Locator: §2 Parallel Patterns, PDF pp.2–3; §3.1 PCU / §3.2 PMU, PDF pp.4–5; §3.3 Interconnect / §3.4 Off-chip Memory Access, PDF p.6; §3.5 Control Flow, PDF pp.6–7。大学著者PDF。評価はsimulation/synthesis由来でありRaveil実測へ転用しない。
- **R1** — [Gebhart et al., An Evaluation of the TRIPS Computer System](https://www.cs.utexas.edu/~mckinley/papers/trips-eval-asplos-2009.pdf)。ASPLOS 2009, author PDF。Locator: §2 TRIPS System Overview, PDF pp.2–3: EDGE ISA and block outputs; §2, PDF p.3: TRIPS Microarchitecture; §2, PDF pp.3–4: TRIPS Compiler。TRIPSは具体的実装。128命令block、reservation station、複数block speculationとcommitを保持。
- **E1** — [Burger et al., Scaling to the End of Silicon with EDGE Architectures](https://www.cs.utexas.edu/~cart/trips/publications/computer04.pdf)。IEEE Computer, July 2004, pp.44–55。Locator: Architecture Comparisons, printed p.45 / PDF p.2; EDGE ISA discussion, printed p.46 / PDF p.3; TRIPS architecture discussion, printed p.47 / PDF p.4。EDGEはISAの系統。TRIPSとの重複は独立発明の件数に数えない。
- **A1** — [Mei et al., Design Methodology for a Tightly Coupled VLIW/Reconfigurable Matrix Architecture: A Case Study](https://cecs.uci.edu/~papers/date08/PAPERS/2004/DATE04/PDFFILES/09G_2.PDF)。DATE 2004, 6-page conference paper。Locator: §2 ADRES Architecture Overview, PDF pp.1–2; §3 C-Based Design Flow, PDF pp.2–3。CGRA代表をADRESに固定。2003原論文のimec公開口はrequest-a-copyだったため本文判定はこの2004一次論文。
- **D1** — [Gurd, Kirkham and Watson, The Manchester Prototype Dataflow Computer](https://cartheur.com/Files/manchester-data-flow.pdf)。CACM 28(1), January 1985, pp.34–52。Locator: printed pp.34–39 / PDF pp.1–6: graphs, firing rules, static versus dynamic dataflow; printed p.39 / PDF p.6: matching unit, tags, token queue, instruction store。原論文の第三者ホストscan。書誌と本文を確認したが配布権・ファイルhashは未確認。
- **D2** — [Swanson et al., WaveScalar](https://homes.cs.washington.edu/~oskin/wavescalar.pdf)。MICRO-36 2003, 12-page author PDF。Locator: §1 Introduction, PDF pp.1–2: resident instructions in WaveCache; §3, wave-ordered memory; §4 WaveCache architecture。classic dataflowの全系統を代表するものではない。Manchesterと別のmemory/placement方式として比較。
- **X1** — [Necula, Translation Validation for an Optimizing Compiler](https://people.eecs.berkeley.edu/~necula/Papers/tv_pldi00.pdf)。PLDI 2000, 12-page author PDF。Locator: Abstract and §1 Introduction, PDF p.1; §2, PDF pp.2–3。変換結果を別途検証する先行例。Raveilの有限入力checksum検査は一般的意味等価証明より弱い。
- **X2** — [Zheng et al., Ansor: Generating High-Performance Tensor Programs for Deep Learning](https://www.usenix.org/system/files/osdi20-zheng.pdf)。OSDI 2020, proceedings pp.863–879。Locator: §3 Design Overview; §5 Performance Tuning; §6 Task Scheduler; §7.4 Search Time; §7.5 Cost Model Evaluation: invalid or timed-out programs。学習cost model、実測feedback、探索時間配分の先行例。数値改善率は転記しない。
- **X3** — [Gibson and Cano, Transfer-Tuning: Reusing Auto-Schedules for Efficient Tensor Program Code Generation](https://arxiv.org/pdf/2201.05587)。arXiv:2201.05587, retrieved 12-page PDF; exact revision/hash unpinned。Locator: §4.1–4.3, PDF pp.4–6: kernel classes, schedule reuse and invalid transfers; §4.3 Applying transfer-tuning, PDF pp.6–7。同種kernel間schedule再利用の先行例。ハードウェア構成を跨ぐRaveil transferの実証ではない。

## 調査限界とIPの扱い

このmatrixは技術主張の比較であり、特許の法的claim chartではない。公開資料だけを用い、
非公開compiler/runtimeや全世代製品の内部仕様を推定しない。ベンダー自身の性能宣伝も
Raveilの測定証拠として採用しない。

ADR-0014と既存[T-0057b disposition](2026-08-12-T-0057b-simulation-ip-disposition.md)の
WaveCache/EDGE関連識別子（US7490218B2、US10824429B2、WO2015069583A1等）は
既存の未審査リスクとして残る。今回、特許family/法域/存続/請求項/ライセンスの調査は更新していない。
新たな6社の文献を追加しても特許clearanceにならない。copyright/access、OSS license、
patent/FTOは別の状態で、全sourceの権利・採用可否はunreviewedのまま。

## Verification

検証コマンド・環境・結果は[当日log](../../log/2026-09-20.md)に記録する。
今回のテストは既存host契約の再確認であり、RTL再実行、性能測定、silicon実験ではない。
280セルの数が多くても調査網羅性を保証しない。Uセルと追加比較課題を残した状態が成果である。
