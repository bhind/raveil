# T-0057: Groqと同じ推論目標に対する5つの実行原理

Disposition 2026-09-23: preserved alternative / prior screening, not the
current P0 or selected architecture. ADR-0103 and the T-0197 restart review
supersede this memo's suggested next-work ordering. Original evidence and
negative findings below are retained.

Status: Comparative research options; none establishes novelty or advantage
Date: 2026-09-20
Task: T-0057 prior-art and direction review; possible comparisons belong to T-0044
Context: ADR-0039/RFC-0005 unchanged; no new architecture accepted
Evidence: primary publications and current-tree inspection; no benchmark or simulation result

## 今回はゴールを動かさない

ユーザーは、前の「不規則な遅延に強いcompiler」への絞り込みではなく、Groqと同じ
低遅延・高効率の推論を、もっと違う実行原理で達成する候補を求めた。
[前のpivot案](2026-09-20-T-0057-groq-pivot-proposal.md)は一候補として残すが、唯一の推奨方向とはしない。

固定する比較目標は、同じmodel/品質条件の低batch推論。LLMならdecodeのtime/token、
p50/p99、joules/token、weight/KV容量、対応context長、総device数を揃える。
同時requestを増やしたthroughputを、単一requestのlatency向上と混同しない。
量子化方式や学習済みmodelを変更する実験は、実行方式だけを変更する実験と分ける。

Groqの参照原理は「compilerが演算・移動・時刻を決めた命令streamを、空間的な演算資源で
実行する」[G]。空間配置やweight residency自体はGroqにもあるので、それだけを差としない。
2020 TSPと2026製品を同一視しない。現在の製品は
[前の案のG26](2026-09-20-T-0057-groq-pivot-proposal.md#一次資料のledger)に別記済み。

## 5案の比較

これらは互いに排他的な製品分類ではなく、変更する原理が異なる設計軸。
Aは演算の指定方法、Bは発火時刻、Cは計算場所、D/Eは算術の表現を変える。

| 案 | 何を置き換えるか | 残る実行制御 | 便益の仮説 | 支配的な弱点 | Groqとの差 / 研究新規性 |
|---|---|---|---|---|---|
| A モデルを常設の演算回路へ | 反復的な演算命令streamを、設置済みの演算cell・接続・局所counterへ | layer/tile反復、address生成、構成切替は残る | 命令読出し/解釈と中間データの往復を減らす | model全体の容量、配線、演算器利用率、変更時の再構成 | 命令stream中心からの差は明確。FINN/Tartanが先行し、新規性は未確立 |
| B 到着したデータが局所的に発火 | cycle表と広域の時刻整合を、入力・出力spaceの局所handshakeへ | ready/ack、buffer、fork/join、completion | timing余裕や広域同期の費用を減らす可能性 | handshake費、局所backpressure、deadlock、物理設計 | Groqの時刻指定と違う。2006 Tartan等が先行 |
| C 重みのある場所で計算 | weightを演算器へ運ぶdigital経路を、memory array内の積和へ | array選択、変換器、digital非線形/制御 | weight移動とdigital MACの費用を減らす | 精度、周辺回路、変換、容量、reprogram、製造技術 | 計算の物理原理が違う。PUMA等が直接先行 |
| D 有効bitだけ計算 | 固定幅の乗算を、非zero bitに対応するshift/addへ | bit抽出、lane完了、部分和 | 同じ数値を表す無効な部分積を省く | bit密度、最も遅いlane、符号処理、metadata/serial化 | 計算量をoperandのbit構造へ比例させる。Bit-Pragmaticが直接先行 |
| E 積和を表引きへ | 各weightとの乗算を、共有部分和tableのlookupとreductionへ | table生成、index読出し、bank選択、scale/補正 | 多数の出力で同じactivation部分和を共有 | table容量/port/fanout、毎入力の生成、accumulation | MAC中心の実行から明確に違う。LUT-GEMM/T-MAC/LUT-LLMが直接先行 |

## A: 「programを実行する」から「設置した回路へ入力する」

固定した小さなmodel/blockの演算cellと接続を設置し、その後は入力だけを流す。
FPGAに毎回巨大netlistを焼く方式だけでなく、再構成可能なcell群を設定する方式も比較候補。
ただし演算ごとにschedule RAMから制御wordを読むなら、instruction fetchを別名にしただけに
なり得る。どの制御bitを設置後に保持し、どれを反復読出しするかを明示する。

FINNはmodelごとのstreaming architecture、layer別engine、foldingを持つ[F]。
Raveilでの審査対象は、同じmodel範囲を扱うprogrammable stream方式に対して、
常設化による節約がconfiguration storage・routing・低利用率を上回るか。
現行の固定stencil FSMだけを汎用回路への勝利として使わない。

**反証:** 同じmodel/数値形式・area/SRAMで、重み容量・reconfigurationも含めると負ける。
また、autoregressive token間の依存はlayer pipelineでも消えない。pipelineの最大throughputを
1 tokenのlatencyと読み替えない。全modelが載らない時のfolding/交換費を隠さない。

## B: 「何cycle目か」から「値が揃ったか」

各cellは入力値と出力spaceが揃えば進む。最も純粋な案はclockless handshake回路で、
同期ready/valid実装とは別に扱う。FPGA上の同期モデルで非同期回路のenergyを立証できない。

[Tartan: Evaluating Spatial Computation for Whole Program Execution (2006)](https://www.microsoft.com/en-us/research/wp-content/uploads/2006/10/asplos06.pdf)
は各IR nodeをclockless data-triggered pipeline stageにする[T]。
同名の2017年の精度可変DNN acceleratorとは別論文である。

**反証:** denseで予測可能な推論において、handshake/buffer/routerの費用が、節約した同期や
clock distributionを超える。同じ計算DAGの本質的なcritical pathは、clockを除いても消えない。
局所発火一般をRaveilの新規性にはしない。

## C: 「weightを読む」から「weightが演算素子になる」

analog crossbarではweightをconductanceに対応させ、入力を印加し、columnの出力から
matrix-vector積を得る。PUMAはこの方式をprogrammable digital機構と組み合わせる[P]。
命令自体は残り得るので、CとAは別軸。CIMを「命令なし」の意味に使わない。

**反証:** ADC/DAC、bit slicing、校正/誤差対処、非MVM処理、array間reductionまで含め、
同じ品質でdigital方式に勝てない。analogとdigital CIMを混同しない。digital CIMも
別の候補だが、そのmacro/adder/routing費の資料とtoolchain調査は今回未完。

Raveilの現在のChisel/Verilator資産だけでanalog siliconの優位性は立証できない。
この案は原理上の差が大きい一方、最初の検証路としては最も遠い。

## D: 「固定幅の積」から「必要な部分積だけ」

選んだ固定小数点modelに対し、zero bitが作るzero部分積を計算しない。
精度を落として仕事を減らす実験とは区別し、符号・accumulator幅・丸めを固定する。
Bit-Pragmaticはこの方向とlane同期のtradeoffまで扱う[B]。

**反証:** 実modelのactivationがbit-dense、または最もbitの多いlaneに全体が引きずられ、
encoder/shifter/extra cycles込みで通常MACに負ける。CNNでの論文結果からLLMに外挿しない。
「平均nonzero bit数が少ない」だけでは低latencyを証明できない。

## E: 「掛け算」から「共通部分和を一度作り選ぶ」

例えばactivationの4要素に対し、bit-patternに対応する16通りの部分和tableを作る。
weightをbit-planeへ分解すれば、その4bitをindexとしてtableを読み、出力へ加算できる。
多くの出力rowが同じtableを共有する。これは説明用の既知原理であり新提案のalgorithmではない。

重要なのは、**activationに依存するtableは入力/tokenが変われば作り直す**こと。
weightが固定だから全tableを永久保存できる、という説明は誤り。
lookupの後にもscaling、符号補正、accumulationが残り、attentionやnormalization全体まで
乗算がなくなるわけでもない。LUT-GEMMとT-MACが直接先行する[L/M]。
さらにLUT-LLMはactivation/weightのvector quantizationとFPGA向けtable機構を扱う[Q]。

検討する実装候補は「入力からtableを生成する部分」と「常設のweight-indexを使う
lookup/reduction部分」を分け、演算ごとの命令読出しをどこまで不要にできるか。
**AとEを組み合わせる候補だが、先行LUT acceleratorとの一致確認が先である。**

**反証:** table生成・複製・読出しport・distributionの費用で負ける、低bit化の品質損失で
条件を満たさない、あるいはtoken時間の大半が対象外のKV/attentionである。
LUT-LLMの量子化modelと元modelを「同じ処理」として速度比較しない。

## 優先する比較

私案では**AとEを最初の比較対象**にする。理由は、Groqと異なる実行原理を検討でき、
既存digital実装環境で反証しやすいこと。勝てる確率や新規性が高いと測定済みだからではない。
Bは別の回路研究、Cはdevice/macro研究、Dは実activationのbit分布を確認してからの候補。

A+Eを最初から一つの発明としてまとめず、次の2×2を比較する:

| | 同じ数値形式のMAC | 同じ数値契約のlookup/reduction |
|---|---|---|
| 静的命令stream | Groqに着想を得たdigital参照モデル | 算術変更だけ |
| 設置済みcell/接続 | 制御変更だけ | A+E |

RTL段階では同じprocess/library、総area、全on-chip記憶、外部帯域、clock制約と対応model範囲を
揃える。LUTの追加table/indices/portsを無料扱いせず、MAC数を揃えるだけの比較にもせず、
同じbudgetの設計点とPareto曲線を示す。Groq風モデルは実機Groqの再現ではない。

最小順序は、共通の量子化model/shapeとsemantic referenceを固定 →
演算・weight/table traffic・容量の内訳を集める → 2×2の小blockを同じbackendで比較 →
model全体のdecodeを測る。単blockの成功は全modelの成功ではない。
取得したholdout前にcompile/install償却、quality、latency/energyの判断条件を固定する。
現時点ではmodel選定・profile収集・実装・EXP登録をしていない。

新規性を求めるなら、最後に残すのは具体的なmapping/共有/配線/算術機構の差分一つ。
5案のカテゴリ自体、独自名称、A+Eという組合せだけでは独自性の証拠にならない。

## 一次資料ledger

全て2026-09-20本文確認。論文の性能値を本比較へ転用しない。

| ID | sourceとlocator | 支持する範囲 |
|---|---|---|
| G | Abts et al., [Think Fast](https://www.researchgate.net/publication/342914141_Think_Fast_A_Tensor_Streaming_Processor_TSP_for_Accelerating_Deep_Learning_Workloads), ISCA 2020, §I–III、著者公開版 | TSPの時刻指定・機能slice・命令fetch。現在の全製品機能ではない |
| F | Umuroglu et al., [FINN](https://phwl.org/assets/papers/bnn_fpga17.pdf), FPGA 2017, §4.1/4.4/6 | BNNのmodel別streaming architecture、folding、on-chip容量条件。一般LLM実装の証拠ではない |
| T | [Tartan: Evaluating Spatial Computation for Whole Program Execution](https://www.microsoft.com/en-us/research/wp-content/uploads/2006/10/asplos06.pdf), ASPLOS 2006, §3 / Fig.3、PDF p.4 | clockless data-triggered stage。2017年の同名DNN精度研究とは別 |
| P | Ankit et al., [PUMA](https://ielhajj.github.io/publications/paper/paper-puma-asplos19.pdf), ASPLOS 2019 author PDF, §3.1–3.2 / Fig.3 / §7.4 | analog crossbarとdigital周辺/命令処理。digital CIMの費用根拠ではない |
| B | Albericio et al., [Bit-Pragmatic Deep Neural Network Computing](https://www.eecg.utoronto.ca/~roman/professional/research/pdfs/micro17_deep_nn_moshovos_ieee.pdf), MICRO 2017, §5.1–5.5 | nonzero部分積、lane同期、buffer/port費。LLMのbit分布は別途必要 |
| L | Park et al., [LUT-GEMM](https://proceedings.iclr.cc/paper_files/paper/2024/file/a4f98ce85f440ee269b0df57b4368719-Paper-Conference.pdf), ICLR 2024 proceedings, §3.1–3.2 / Eq.2 | table生成＋lookupの費用、quantized weightとactivationの部分和共有 |
| M | Wei et al., [T-MAC](https://arxiv.org/pdf/2407.00088v2), arXiv v2, 2025-03-25, §3.1–3.3 / Algorithm 1 / §4 | weight bit-plane、online activation table、layout/lookup。実装上の精度変更も別途評価が必要 |
| Q | [LUT-LLM](https://arxiv.org/pdf/2511.06174v2), arXiv v2, 2026-03-22, §II–IV | activation/weight vector quantization、2D lookup、FPGA設計。元modelにbit-exactとはしない |

残る調査は、各案の後続研究、同じmodel/数値形式における最適化済み対照、code/licenseと
reproducibility、technology cost、特許family/権利状態。いずれも独自性・FTOの肯定結論はない。
既存のruntime契約・検証・記録は比較基盤として使うが、それを発明とは数えない。
