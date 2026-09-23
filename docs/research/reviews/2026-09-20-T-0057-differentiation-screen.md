# T-0057: 差別化候補の反証と最小比較条件

Disposition 2026-09-23: preserved alternative / prior screening, not the
current P0 or selected architecture. ADR-0103 and the T-0197 restart review
supersede this memo's suggested next-work ordering. Original evidence and
negative findings below are retained.

Status: Non-authoritative research screening; no surviving novelty claim
Date: 2026-09-20
Task: T-0057 supplementary audit; T-0058 lifetime accounting; T-0044 comparison design
Context: RFC-0005 / ADR-0039 simulation scope; EXP-0003 closed negative
Evidence: primary literature, current-tree inspection, synthetic call trace; no performance measurement

## 結論

**今回検討した3候補には、「先行方式の未解決問題 → Raveil固有の変更 → 便益」を
つなげて新規性を支持できるものがなかった。** 保存・再利用、独立検証、失敗に応じた
探索制御の一般論を、明示依存や静的scheduleに代わる新規性として採用しない。
これは全探索空間の不可能性証明ではなく、このcheckoutと下記一次資料による判断。

[28-claim matrix](2026-09-20-T-0057-atomic-claim-matrix.md)のC13–C17、C21–C24、
C28を追加で絞り込んだ。先行例のない欄を探すだけでは不十分で、同じ契約を実装した
通常の方式に対し、何を一つ変えるか説明できる必要がある。

## 候補ごとの判定

| 候補 | 解きたい具体的問題 | 仮に加える変更は一つだけ | 最も近い先行方式と限界 | 現行Raveilとの差 | 判定 |
|---|---|---|---|---|---|
| H1: 検証済み構成の部分再検証 | 同じgraphでobject bindingだけ変わるたびに、変わらない構造まで再確認するコスト | 検証条件と依存対象の対応を保存し、失効した条件だけ再評価する | CUDA Graphの個別node更新は変更のないnodeの比較とtopology検査を省く[G]。Dynamoは条件を満たすcompiled artifactを再利用する[Y]。両者がRaveilの全権限契約を実装するとは言わない | RFC-0005は既にdescriptor identityとinvocation bindingを分離している。一般的な検証証明cacheは未実装 | 広い新規性は棄却。通常のguard cacheにも依存indexを許すと、固有の変更がまだ定義できない |
| H2: 資源状態に条件付けた失敗利用 | 低memoryでの失敗を高memoryでも避ける誤転移と、同じ失敗の再試行 | 失敗証拠をresource context付き制約観測として候補選択に使う | SafeOptは安全集合を推定[S]、contextual版は状況をまたいで推定を共有[B]、XSFは失敗情報と残予算で探索を調整[X]。数学的仮定付きであり絶対的権限検査ではない | 現行policyは距離で減衰する加点。形式的な失敗領域、soundness rule、context失効規則はない | 「失敗を覚えて安全に探索」は棄却。新しい一般化則も実測便益も未確立 |
| H3: 提案者を信用せず、受容時の検証を再利用 | optimizerを権限主体にせず、再実行のたびに全面検証しない | 実行artifactを検証条件・証拠に束縛し、consumer側で受容する | PCCはconsumerのpolicyとproof checkerを分離[P]。Translation validationはコンパイル結果ごとに変換を検査[V]。PCCの安全性証明と意味同値性は区別する | structural validatorとsemantic oracleはあるが、一般的なproof producer/checkerや再利用証明にはなっていない | 検証と提案の分離自体は棄却。Raveil全契約の合成証明は未確立であり、その欠落は新規性ではない |

H1–H3を組み合わせてC28の独自性に昇格させる根拠も得られていない。
既知要素の組合せに研究価値が生じる可能性は残るが、具体的な相互作用、比較対象、
効果の切り分けが必要。「全く同じ製品が見つからなかった」はその代わりにならない。

## 実装で確認した制約

### Graphの開発用executorは繰り返し実行の配備cacheではない

[graph_mvp.py](../../../raveil/graph_mvp.py)の`GraphExecutor.execute`は毎回
`MiroirsStructuralValidator.validate`を呼び、baselineを実行・検査してから候補を実行する。
structural validatorは`GraphCompiler(contract).compile(program)`との一致も確認する。
`committed-proposal`はその開発用呼出しの選択結果であり、次回のbaseline省略を意味しない。

同じexecutor、program、variants、proposalで2回呼び出したsynthetic backendのtrace:

```text
outcomes: ['committed-proposal', 'committed-proposal']
calls: ['baseline-ijk', 'tile32-fused', 'baseline-ijk', 'tile32-fused']
```

これは呼出し順の実行確認のみ。backendが返す200/100は作り物の値で、latency測定でも
高速化結果でもない。全Raveil経路・RTLにこの挙動を一般化しない。既存のbaseline-first
境界をこの調査で解除しない。選択されたkernel単体の値を全lifecycle便益と混同しない。

再現コマンド（repository root、Python 3.14.6 / Darwin arm64）:

```sh
python3 - <<'PY'
from raveil.graph_mvp import GraphProgram, GraphCompiler, AnalyticalPredictor, PavaneSemanticOracle, GraphExecutor
from raveil.native_backend import NativeMeasurement
program = GraphProgram.create("gemm_bias_relu", 64, 64, 64)
variants = GraphCompiler().compile(program)
proposal = AnalyticalPredictor().propose(program, variants)
checksum = PavaneSemanticOracle().expected_checksum(program)
class CountingBackend:
    def __init__(self):
        self.calls = []
    def measure(self, context, candidate):
        self.calls.append(candidate.candidate_id)
        fake_latency = 200 if candidate.trusted_baseline else 100
        return NativeMeasurement(fake_latency, checksum, checksum, True, "")
backend = CountingBackend()
executor = GraphExecutor(backend)
results = [executor.execute(program, variants, proposal) for _ in range(2)]
assert all(result.outcome == "committed-proposal" for result in results)
assert backend.calls == ["baseline-ijk", proposal.variant_id] * 2
print("outcomes:", [result.outcome for result in results])
print("calls:", backend.calls)
PY
```

### Toyの資源制約は学習以前に計算できる

[policy.py](../../../raveil/policy.py)の`NearestExperiencePolicy.rank`では失敗履歴は
scalar scoreへのpenaltyであり、admissionを保証する境界ではない。
[model.py](../../../raveil/model.py)の`Context.distance`はshape、memory budget、
hardware name、lanes等を使う手書き距離。

[backend.py](../../../raveil/backend.py)の`ToyDaphnis.measure`では、memory policyごとの
peak bytesとbudget超過が既知の式で決まる。例えば`keep`は
`16 * min(shape, tile_length) + 4 * tile_length` bytesである。
この条件の失敗を学習で回避できても、既知式による事前feasibility filterを比較から
外したら弱いbaselineになる。これはmodelの定義の確認で、未知の実機制約を解いた証拠ではない。

### Installed static regionも既存仕様を新提案と数えない

[static_region.py](../../../raveil/static_region.py)の
`compile_static_stencil_descriptor`と`validate_static_stencil_descriptor`は固定stencil用。
汎用graphの任意alias解析や証明cacheではない。
[RFC-0005 §Identity and invalidation](../../rfcs/RFC-0005-bounded-installed-static-graph-region.md#identity-and-invalidation)
は既に構成のidentityと呼出し時のobject/version/range/capability検査を分けている。
この分離を今回発見した固有の機構に数え直さない。

## 残せる最小の検証案: H1の有用性screen

新規性を支持できた案ではない。**同じ権限・意味契約を保った普通のcacheに対し、
再検証範囲の表現を変える価値があるか**という、検証可能な問いに縮める。
新ISAやAIを実験変数に混ぜない。以下は未実施の比較設計で、採択済みEXPではない。

| 要素 | 固定する具体的条件 |
|---|---|
| 問題 | graphの構造は同じだがbinding/version/capabilityが変わる反復呼出しで、安全に再利用できる検証結果の範囲を求める |
| 唯一の処置 | 検証条件と依存対象の表現・失効処理だけを差し替える。kernel、候補選択、入力、verifier、capability/semantic/publication契約は共通 |
| B0 診断control | 毎回全面検証。削減可能コストの内訳を調べるだけで、B0への勝利を差別化としない |
| B1 主比較 | 通常のartifact cache + runtime guards。hash/version key、binding検査、依存index、変更のない条件の再利用を許す。不要な全走査を強制しない |
| B2 該当targetのcontrol | GPUで検証する場合はCUDA Graph個別node更新も利用可能な範囲で比較。共通の契約検査を上に置き、その追加コストも計上。CPU実験の代用品にはしない |
| 処置P | H1固有の追加表現を、B1との差分として擬似codeで指定する。現時点ではこの差分が未定義。B1と同じならここで打ち切る |
| 入力系列 | 同じbindingで新data、許可された別objectへのrebind、version更新、capability失効、alias/range違反、compiler/oracle/target変更、cache evictionを別々に試す。未変更・単一変更・一括変更・高頻度失効を含む |
| 正しさ | 失効した権限で実行/公開しない。再利用の前提が不明なら全面検証またはfallback。検査から使用までの状態固定と失効規則を両群で一致させる。テスト無失敗を一般的soundnessの証明にしない |
| 費用 | 初期compile/証拠生成、installation、全admission、guard、hash/index更新、lookup、実行、失効、fallback、evictionを含む観測期間の総時間とcache bytes。kernel単体と分ける |
| 反復 | RFC-0005との接続用に1/4/16/64/256 invocationsを報告。高い反復数だけ選ばない。小さな固定stencilの結果を一般graphへ外挿しない |
| 比較方法 | 同一traceでpaired比較し実行順を交互化。独立したprocess/sessionを反復単位にする。pilotは分散推定専用、holdout traceと標本数・実用差の閾値をEXP開始前に固定 |
| 判定量 | B1とPの総時間のpaired差、および95%区間。未達・区間不明・構造による逆転を報告。新規性と速度差は別に判定 |

**現在の停止位置はPの定義。** 既存guard cacheと異なる機構をまだ指定できないため、
「全面再検証より速い」という実験を先に作って勝ちを宣言しない。
実用性のscreenを実施すると決めた場合はT-0058で専用EXPを先に定義する。
[EXP-0004](../../experiments/EXP-0004-native-command-graph.md)はprocess/toolのCommand Graph用であり、
この比較の結果を流し込まない。

H2を再開するなら、同一measurement/retention予算で、現行kNN、exact-context failure cache、
既知資源式のfilter、contextual constraint-aware探索を比較する。未知のworkload/contextを
分離し、失敗回数だけでなく総探索費とnegative transferを報告する。
これは追加の機構が先行方式を超えたと確認できてからの話であり、
[EXP-0003](../../experiments/EXP-0003-gate1-bounded-experience.md)の負の結論を置き換えない。

## 一次資料と証拠の範囲

全て2026-09-20に本文の下記箇所を確認。外部資料の数値をRaveilとの比較に転用していない。
以下は7件の追加資料で、元matrixの15件/280セルを遡及的に再採点しない。

| ID | 一次資料・版・locator | この調査で支持する範囲 / 支持しない範囲 |
|---|---|---|
| G | NVIDIA, [CUDA C++ Programming Guide 12.8.0](https://docs.nvidia.com/cuda/archive/12.8.0/cuda-c-programming-guide/index.html#updating-instantiated-graphs), §3.2.8.7.5–.5.2 | instantiation再利用、個別node更新、topologyが変わる場合の制約。Raveil全意味・権限契約の同一性は支持しない |
| Y | Animesh Jain, [Inside torch.compile Guards](https://docs.pytorch.org/devlogs/dynamo/2025-06-04-inside-torch-compile-guards/), 2025-06-04表示、retrieval時に追記あり; Building the Guard Programming Model / guardsとcompile unitの説明 | 入力等のassumptionsをguardとしてartifact再利用を決める。unsafeなguard省略を安全性同等の比較に使わない。文書は固定releaseではない |
| P | Necula / Lee, [Safe Kernel Extensions Without Run-Time Checking](https://www.usenix.org/legacy/publications/library/proceedings/osdi96/full_papers/necula/html/node2.html), OSDI 1996, Proof-Carrying Code節 | consumerがpolicyを定義し、producerのproofを検査後native codeを実行する分離。任意semantic equivalenceやmutable capability再利用の証明ではない |
| V | Necula, [Translation Validation for an Optimizing Compiler](https://people.eecs.berkeley.edu/~necula/Papers/tv_pldi00.pdf), PLDI 2000, abstract/§1–2, PDF pp.1–3 | compilerを全面的に信用する代わりに個々の変換結果を検査する。cache失効・再検証の方式までは示さない |
| S | Sui et al., [Safe Exploration for Optimization with Gaussian Processes](https://proceedings.mlr.press/v37/sui15.pdf), ICML 2015, §2/Algorithm 1/Theorem 1, PDF pp.2–5 | 初期safe set、kernel/Lipschitz等の仮定下の安全な探索。Raveilの絶対的capability検査を代替しない |
| B | Berkenkamp et al., [Bayesian Optimization with Safety Constraints](https://arxiv.org/pdf/1602.04450v3), arXiv v3, 2020-04-07, §4.2.1/Assumption 1/Theorem 2/Fig.3, PDF pp.9–10 | contextをまたぐsafe-set推定。各contextに既知safe parameterがある等の仮定付き。任意の分布変化で安全とは言わない |
| X | Marco et al., [Excursion Search for Constrained Bayesian Optimization under a Limited Budget of Failures](https://arxiv.org/pdf/2005.07443v1), 2020-05-15, §4.2–4.3, PDF pp.5–6 | 失敗観測、残り失敗予算、未知/unsafe領域に応じる探索方針。resource regime用のRaveil形式契約そのものではない |

PCCは元auditではPDF抽出が不良でpositive cellに使わなかった。今回はUSENIXのHTML本文を
読めたため追加根拠にした。元auditの取得失敗記録・hashは保持する。
本調査は公開一次資料の技術比較であり、特許family・jurisdiction・権利状態・FTOは未評価。

## 記録上の扱い

新規性を主張する根拠は現時点で未確立。既存ADR-0039のbounded simulation受容を
取り消す判断や、新しいdesignの受容はしない。T-0057の広い調査はopenのまま。
T-0044のmatched CPU + static/VLIW/CGRA-like controlによる便益検証も未実施のまま。

主張として残せるのは「既知のgraph実行・検証・履歴利用を、明示した制約下で実装し、
比較する研究用基盤」。固有機構が見つかるまでは、新ISA・AI統合・lifetime benefitを
独自性が立証された成果として説明しない。
