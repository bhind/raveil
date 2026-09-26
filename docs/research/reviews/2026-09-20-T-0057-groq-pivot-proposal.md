# T-0057: Groqとの比較から選ぶpivot案

Disposition 2026-09-23: preserved alternative / prior screening, not the
current P0 or selected architecture. ADR-0103 and the T-0197 restart review
supersede this memo's suggested next-work ordering. Original evidence and
negative findings below are retained.

Status: Proposed research direction; novelty and advantage unestablished
Date: 2026-09-20
Task: T-0057 prior-art screen / T-0044 comparison design
Context: ADR-0039 and RFC-0005 retained; a variable-latency implementation needs a separate contract
Evidence: primary-source review and current-tree inspection; no simulation or performance result

Follow-up scope: the user subsequently requested multiple execution principles
while retaining Groq's inference goal. See the
[same-goal alternatives](2026-09-20-T-0057-pure-inference-alternatives.md).
This earlier variable-latency proposal remains one option, not the selected pivot.

## 推奨する転換

**小さな資源予算の下で、可変遅延を吸収する場所と容量をコンパイラが選ぶ研究へ絞る。**
新しいCPU全体を作ることやdense tensorの最高速度を当面の主張にせず、
外部memoryの待ち時間が変動する反復kernelの、総完了時間とtail latencyを対象にする。

研究命題の候補:

> 同じ演算器・memory interface・総資源上限で、静的領域の分割と境界bufferを同時に選び、
> 未見の遅延系列でも、既存の選択的dynamic schedulingより小さい完了時間を得られるか。

独自性を獲得できると確認済みの命題ではない。Groqとの差があることと、全先行研究に対する
新規性は別の関門である。今回の成果は、前者だけで研究を進めない比較対象と停止条件を
定めたこと。現在のfixed-stencil実装を新機構の実装済み証拠には数えない。

## Groqの弱点を仮定して作らない

2020 TSPではcompilerが演算・移動・時刻を管理する[G20]。そのモデルと異なる
不確定なmemory完了時刻を入力条件として比較するが、「Groqは間接アクセス不能」
「dynamic workloadを実行不能」「hostと分担できない」とは主張しない。
TSP論文§III.Bはstream-indirect addressingも記載している。

2026-03-16のNVIDIA Groq 3 LPX公式説明には、compiler/runtimeによるSRAM配置と明示移動、
Rubin GPUとLPXによるdecode処理分担が記載される[G26]。従って「CPU/GPUと組み合わせる」
「MoEを扱う」だけでも差にならない。2020年の論文だけで現在の製品の欠如を認定しない。

実機Groqに同一kernel・resource・memory条件を持ち込めなければ、比較相手は
**Groqに着想を得た静的実行モデル**と明記する。その結果を「Groq製品より速い」と呼ばない。

## 採らないpivotと理由

| 方向 | 今回の扱い |
|---|---|
| Groqより静的にしてfetch/decodeを削る | 特殊化の強さだけで勝ちやすい。programmability・mapping coverage・構成費を揃えない限り主張にしない |
| AI/ExperienceをGroqに足す | optimizerの付加はGroq側にも可能。EXP-0003の負の結果を覆す独立証拠もない |
| 静的実行とelastic実行を混ぜる | REVEL等が先行[R]。混合そのものを発明としない |
| 不規則処理をregular stageへ分ける | Fiferが直接先行[F] |
| 動的化が必要な領域だけcompilerで選ぶ | 2023年のCompiler Discovered Dynamic Schedulingが直接先行[D] |
| FIFO容量を自動最適化する | FIFOAdvisor等が先行[Q] |

## 変更する機構を具体化する

対象はread-only入力とexclusiveなprivate outputを持つbounded kernel。
最初は整数のindirect gather–map–reduceと、row長に上限を設けたCSR SpMVを候補にする。
共通の論理kernel範囲を全方式で実装し、一方だけ固定function回路にしない。
入力依存addressは扱うが、未知のread/write alias、MMIO、coherent shared write、
一般的な例外回復は初期範囲に入れない。

一つのcompiler passが次を**同時に**選ぶことを処置とする:

1. どこで固定scheduleのregionを区切るか。
2. region間の有限FIFO/creditに何byte・何slotを割り当てるか。

regionは必要入力と出力spaceを確保した時に起動し、内部の固定scheduleを実行する。
可変遅延memory operationはboundary側へ出す。固定regionを途中で止める場合は
全内部stateを一貫してfreezeできることを別途証明する。単純なready信号だけを加えて
scheduleの正しさが保たれると仮定しない。

提案する探索方式の最小形:

- bounded graphの合法な分割候補を列挙する。小graphでは全探索してheuristicの基準にする。
- FIFO容量候補を組み合わせ、token conservation、credit上限、循環待ちを検査する。
- 同じmapping/演算資源について、独立遅延・burst・複数要求の相関遅延を含む
  **training側の複数scenario**で費用を計算する。
- `max_s Q99(completion_time | scenario_s)`を、control areaと総buffer上限の下で
  最小化する候補を選ぶ。compile/search時間も記録する。
- held-out inputとlatency scenarioでは選び直さない。将来の完了時刻をruntimeへ教えない。

これは具体的に実装可能な**候補algorithm**であり、全探索・robust目的関数・FIFOの各要素に
新規性があるという主張ではない。region選択とbuffer sizingを別々に行う強い方式へも
同じscenario情報と探索予算を渡す。単に情報を多く与えた差をalgorithmの差にしない。
主比較Cと容量探索controlにも、同じ`max_s Q99`目的、同じscenario標本、
同じcontrol＋FIFOの総資源上限を与える。nominal/平均latencyだけに最適化した相手を主比較にしない。

残る新規性の審査対象は、**相関した遅延scenarioに対するregion分割とbuffer配分の共同選択が、
最も近い先行algorithmとはどこで異なり、その結合に独立の便益があるか**。
同じ定式化が見つかれば、研究新規性の主張を止め、再現・実用比較として扱う。
「論文にp99の表がなかった」だけでは新規性にならない。

## 最小の反証実験

以下は提案条件であり、既存RFC-0005の採択閾値を上書きしない。実施前に専用RFC/EXPへ固定する。

| 要素 | 条件 |
|---|---|
| A 静的control | software pipeline、prefetch、double buffer、legal region stallを許した最適化済み静的方式。毎回最悪遅延分のNOPを強制する弱い方式にはしない |
| B dynamic control | 同じbounded semanticsのelastic dataflow。不要なgeneral LSQやOoOを強制せず、同じalias情報を渡す |
| C 主比較 | 2023 selective dynamic方式に対応する実装と、独立したbuffer最適化の組合せ。manual hybridも診断用に残す |
| P 提案 | 上記joint region/buffer選択。A–Cと同じtrace情報、探索時間/評価回数、資源上限 |
| ablation | joint vs 分割→容量の二段階、複数scenario vs nominalのみ。前者には同じrobust目的、後者には同じjoint探索を用い、差を混ぜない |
| 資源 | ALU/乗算器、ports、帯域、outstanding要求数、SRAM総量を固定。FIFO・credit・tags・private outputも総量へ加算。RTL段階でcontrol area・配線・Fmaxを追加評価 |
| workload | 2つのkernel familyを、サイズ・row長・局所性・burst条件でholdout分割。密で規則的な条件と、予測不能な逐次pointer chainをnegative controlに含む |
| memory | 全方式で同じ因果的memory/queue model。request時刻と競合から完了を計算する。固定completion timestampを全方式に配るoracleモデルにはしない |
| 正しさ | exact integer oracle、tokensの欠落/重複なし、buffer上限、cancel時の未公開出力無効化、drain後の再開始。環境の応答/fairness仮定を明記し、有限trace無失敗を一般的deadlock freedomと呼ばない |
| 総費用 | compile/install/stage/execute/validate/publish/fallbackの全期間。1/4/16/64/256回で償却を示す。kernel単体も内訳として別報告 |
| 仮の継続閾値 | 主比較Cに対し2 familyのheld-out p99で各15%以上改善、各改善の95%下限が0超、regular controlのmedian悪化5%以内、資源上限内。閾値は目標で実績ではない |
| 統計 | pilotでtail標本数と独立反復数を決め、holdout前に固定。request内相関を保存してsession単位で区間を作る。標本不足でp99結論を出さない |
| 停止条件 | Cと同じ定式化、jointの効果なし、追加buffer/帯域だけの勝利、Fmax悪化で総時間が逆転、oracle不一致、実在するlatency条件への接続不能 |

RTLではcycle数だけで勝敗を決めず、合成後clockとwall-time換算を報告する。
同じdatapathで比較する制御overheadの実験と、同じ総areaで比較する設計点は別に報告する。
全elasticが予算内に収まらない場合も、縮小した構成やPareto frontierを示して不公平な勝利を避ける。

最初のmodel実験はsynthetic scheduling evidenceに限定する。そこを通過しても、実測traceと
RTL timing/resource評価がなければhardware優位性へ昇格しない。

## Raveilから使うものと変更が必要なもの

使える資産は[owned memory境界](../../../hardware/chisel/OwnedFixedLatencyScratchpad.scala)の
accepted/completed計数、initiator/phase記録、[static region](../../../hardware/chisel/StaticStencilRegion.scala)の
private output・cancel/drain、および既存oracle/記録検査の設計。
これらは測定と正しさの足場であり、それ自体を新規性に数えない。

現行scratchpadは一要求outstanding、局所応答1cycle。現行static regionは固定stencil用であり、
可変遅延のoverlapや選択的elasticityを評価できる汎用executorではない。
新規の分割IR、boundary制御、複数outstandingの因果的memory model、compiler探索が必要。
readiness/tokenを除外したADR-0039/RFC-0005へ無断で継ぎ足さず、別の提案・契約とする。

推奨する投資順は、T-0057でD/Qおよび関連研究とのalgorithm差分を詰める →
T-0044で小さなmodelと強い比較Cを揃える → 通過した機構だけRTLへ進める。
新ISA、汎用CPU置換、学習器の高度化、大規模な新benchmark campaignを先行させない。
本書はこの優先順位の提案で、既存gateの取消しや新architectureの受容ではない。

## 一次資料のledger

2026-09-20閲覧。版と節を区別し、sourceの数値をRaveilへ転用しない。

| ID | source / locator | 重なる部分と、この調査の限界 |
|---|---|---|
| G20 | Abts et al., [Think Fast](https://www.researchgate.net/publication/342914141_Think_Fast_A_Tensor_Streaming_Processor_TSP_for_Accelerating_Deep_Learning_Workloads), ISCA 2020, §II / §III.A.3 / §III.B、著者公開本文 | 静的な演算・移動・命令制御。現在の製品の全機能を代表しない |
| G26 | NVIDIA, [Inside NVIDIA Groq 3 LPX](https://developer.nvidia.com/blog/inside-nvidia-groq-3-lpx-the-low-latency-inference-accelerator-for-the-nvidia-vera-rubin-platform), 2026-03-16, 本文Introducing / MEM / Deterministic execution | GPU/LPX分担とcompiler/runtime memory管理。自動要約やmarketing性能倍率は根拠に使わない |
| R | Weng et al., [A Hybrid Systolic-Dataflow Architecture for Inductive Matrix Algorithms](https://web.cs.ucla.edu/~tjn/papers/hpca2020-revel.pdf), HPCA 2020, §III / §V–VI、PDF pp.4/6/9 | systolic/dataflow分割と異なるflow-control機構。hybrid自体は既知 |
| F | Nguyen & Sanchez, [Fifer](https://people.csail.mit.edu/qmn/papers/nguyen_fifer_micro_2021.pdf), MICRO 2021, abstract / §1 / §3 | irregular処理をregular stageへ分解し、FIFO接続とdynamic stage scheduling。分解一般は既知 |
| L | Carloni et al., [Theory of Latency-Insensitive Design](https://www.cs.columbia.edu/~luca/research/lipTransactions.pdf), TCAD 2001, §V | stallable processのwrapperとrelayによるlatency equivalence。可変遅延に耐えること自体は既知 |
| D | Szafarczyk et al., [Compiler Discovered Dynamic Scheduling of Irregular Code in HLS](https://arxiv.org/pdf/2308.15120v1), arXiv v1, 2023-08-29（FPL 2023予定と記載のe-printを確認）, §III Algorithm 1 / §IV、PDF pp.3–5 | modulo-schedulingから部分dynamic化を選択しmemoryもdecoupleする、最重要の直接比較。本文で見た目的だけから後続研究の不在を推定しない |
| Q | Stefan Abi-Karam, Rishov Sarkar, Suhail Basalama, Jason Cong, Callie Hao, [FIFOAdvisor: A DSE Framework for Automated FIFO Sizing of High-Level Synthesis Designs](https://arxiv.org/pdf/2510.20981v1), arXiv v1, 2025-10-23、§III / §IV.B、PDF pp.2–4 | FIFO配置の容量vector、latency/memoryのPareto探索、trace再利用。容量探索一般は既知。revisionの凍結と実装再現は実験前に必要 |

未完の調査: D/Qの関連・後続研究、robust/SDF buffer allocation、correlated delayを扱う
設計空間探索、compilerの同一問題定式化、source実装の版・license。
特許family・権利状態・FTOは未評価。未発見を独自性の証明にしない。
