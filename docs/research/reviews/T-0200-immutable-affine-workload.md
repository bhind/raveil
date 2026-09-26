# T-0200: One trained affine operator before specialization

Status: Planning and host-functional commissioning; no EXP frozen
Date: 2026-09-26
Task: T-0200 / Issue #269; ADR-0103, RFC-0007
Base: `3d804e8222f53b9153d7e96fe18988efdb4670b8`

## Selection before inspecting parameter values

Select the complete first-layer feed-forward input projection of the official
EleutherAI/Pythia-14M checkpoint, batch one: `z = W x + b`. First layer and
whole matrix are fixed before viewing values or testing a transform. This is
small enough to inspect without downloading or executing a complete model.
It is a genuine trained linear operator, not representative production Groq
inference, a full MLP, or an end-to-end language-model quality benchmark.

Source: https://huggingface.co/EleutherAI/pythia-14m/tree/cf967c0a9a04383db6f7b1108d86b2962634b4ac
Revision: `cf967c0a9a04383db6f7b1108d86b2962634b4ac`.
File: `model.safetensors`, 28,143,920 bytes; upstream-reported SHA-256
`116a02532db461f91386a5b20f942ff2c8d4de7341e21b55caafc3d7b25f49a1`.
This is an upstream whole-file identity, not a locally verified full-file hash.
Verified keys: `gpt_neox.layers.0.mlp.dense_h_to_4h.weight` and `.bias`;
F16 shapes `[512,128]` and `[512]` were confirmed against the pinned header.
These were the preselected expected descriptors, not chosen after value inspection.

The official card states Apache-2.0 for the model. It also documents a prior
URL identity change: the current model uses standard Pile, and the previous
deduplicated model moved to a separate repository. Pinning the revision is
mandatory. PM permits a bounded private research extract under the published
model license; no weights, copied implementation or training data are added
to Git. This is not patent/FTO, training-data-rights or redistribution clearance.
Card SHA-256: `d1f2cf1d5181daedeaa70208ddd5cc5251867bde9acf6db7bb45a2265e25e163`.
Config SHA-256: `f97f966a66c444890ed461fff2a51eefb15d74303df05b948124719f199b0b17`.

## Numerical contract fixed before extraction

Immutable W and b are finite, stored binary16 numbers; do not quantize, prune,
clip, replace or change them. Input x is 128 finite binary16 numbers with
`abs(x) <= 8`. Each operand widens exactly to binary32. Output is binary32.
The target mathematical affine result is the exact real sum, including bias;
this is an explicitly isolated operator contract, not a claim to reproduce
all original PyTorch FP16 intermediate/output rounding or full-model logits.

An implementation must return finite outputs satisfying, per row,
`abs(y - exact(Wx+b)) <= gamma_258 * (sum(abs(W*x)) + abs(b))`, where
`u=2^-24` and `gamma_258=258*u/(1-258*u)`. Use exact rational comparisons in
the oracle; a NaN must fail rather than bypass a comparison. This permits the
bounded binary32 roundoff/reassociation of ordinary BLAS and FMA; it does not
permit lower precision or changed weights. Zero scale requires exact zero.
The exact affine function must be retained for every admitted input; a candidate
must establish its algebraic identity without dropping coefficients. These
finite tests cannot prove that universal property. Run round-to-nearest with
no fast low-precision approximation; evaluate the error inequality rationally.
Finite binary16 operands and the input bound prevent binary32 overflow;
products are multiples of `2^-48`, avoiding binary32 underflow in these sums.

Oracle: every finite binary16 is an integer times `2^-24`. Decode its bits
independently and form an integer dot product at scale `2^-48`; bias contributes
its integer representation shifted by 24 bits. Compare each implementation's
exact binary32 value as a rational. Do not use the BLAS output as oracle.

## Input provenance and untouched partitions

Commissioning inputs only: zero, all-one, all-negative-one, alternating +/-8,
unit basis at indices 0 and 127, and dyadic xorshift32 vectors with seeds 2000
and 2001 (values in quarter steps within [-8,8]). These are synthetic functional
probes, not captured language-model activations and not a performance corpus.
Do not tune a transformation with them and call that a holdout result.

Reserve layer 1 and layer 2 of this same pinned file as parameter holdouts;
reserve xorshift seeds 2002 and 2003 as input holdouts. Do not extract/evaluate
those parameters or generate those inputs in this packet. A later evaluation
also needs actual activation provenance and scale/shape generalization; this
operator alone cannot establish either. Replacement W/b always invalidates
the specialization identity, including compiled constants and admission proof.

## Baselines and decision sequence

- Ordinary optimized control: installed Apple Accelerate `cblas_sgemv`,
  row-major W512x128, alpha=1, beta=1 with b copied into y; widened binary32
  operands. Record platform identity; no speed claim from a functional call.
  Official BLAS operation: https://www.netlib.org/blas/ ; SGEMV specification:
  https://www.netlib.org/lapack/explore-html/d7/dda/group__gemv_ga0d35d880b663ad18204bb23bd186e380.html
- Diagnostic control: owned serial binary32 multiply then add in increasing
  column order, starting with bias. This is not the competitive baseline.
- Required next control: an equally optimized fixed-parameter implementation,
  including normal compiler simplification, fusion/CSE and layout choices under
  this same numerical envelope. No such implementation is claimed yet.
- Closest prior-art screens: Mirage-like algebra/schedule search for floating
  tensors, and constant-matrix/da4ml methods only where their numerical domain
  applies. Integer-only methods are not defeated by a floating workload.
- No residual Raveil mechanism exists in this packet. Stop a novelty claim if
  known methods explain all gains. Apply the same frontend transformations to
  any future conventional and proposed hardware backends.

## Full-cost ledger and non-claims

Reset y from b on every independent invocation, including repeated identical
inputs; both controls pay that copy. Account for one-time F16 widening, layout,
packing and lazy-library initialization separately from steady-state calls.
Neither candidate nor baseline receives free preprocessing or hidden state.

Record source parameter bytes, widened runtime parameter bytes, input/output
bytes, emitted code/configuration, live storage, compilation/search, verification,
installation, steady execution and replacement costs separately. Logical unique
bytes do not establish DRAM/cache/device transfer volume. A constant embedded in
code has moved representation; it has not disappeared. No timing, search budget,
area, energy or break-even result is collected here. Any performance collection
requires a separate pre-data EXP and the existing human-confirmation boundary.

The present Graph device uses a bounded uint32 contract; it cannot execute this
F16/FP32 operator as-is. This packet neither weakens that contract nor approves
an ISA/RTL expansion. A software-only outcome or negative finding is valid.

## Verified source and functional receipt

Header validation confirmed the expected F16 keys and shapes. Retrieved only
8-byte length, 8,488-byte header, 131,072-byte W and 1,024-byte b: 140,592 bytes
in total via exact HTTP206 Content-Range checks, not the full 28MB file.
Source manifest, range offsets and hashes are in
[the receipt](../receipts/T-0200-workload.json). Extract hashes are locally
verified; the full-file upstream hash is not locally recomputed and no
cryptographic range-membership proof is claimed. Private extracts and the
pre-extraction selection packet are retained outside Git.

Run from the repository root on the recorded macOS environment:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 docs/research/probes/pythia_affine_reference.py --self-test
PYTHONDONTWRITEBYTECODE=1 python3 -O docs/research/probes/pythia_affine_reference.py --source-dir ../T-0200-evidence
```

The offline probe verifies fixed sizes/hashes before decoding or invoking BLAS.
It contains no network, model deserializer, installation or timing path. All
63,488 finite binary16 bit patterns agree with the independent decoder; all
nonfinite encodings reject. Twelve maximum/subnormal/cancellation cases and
three deliberately invalid output cases test the rational bound implementation.
Eight preselected vectors pass serial binary32 and actual Accelerate SGEMV,
plus a fresh-bias repeat: 12,288 output-component checks. Two input cases yield
different serial/BLAS bit patterns; both satisfy the predeclared rational
bound. Equality of their hashes is not required or misreported.

Local environment: macOS26.6.2 arm64, Python3.14.6, installed Accelerate
`cblas_sgemv`; library default threading/FMA dispatch, not a timing condition.
The system library binary is not hash-sealed. A later performance protocol
must additionally pin library/build, threading, dispatch and warm/cold policy.
Apple API source: https://developer.apple.com/documentation/accelerate/1513065-cblas_sgemv

| Ledger item | Verified logical bytes |
|---|---:|
| Immutable source W+b (F16) | 132,096 |
| Widened resident W+b (F32) | 264,192 |
| Input source / widened runtime | 256 / 512 |
| Output | 2,048 |
| Fresh bias initialization per invocation | 2,048 |

These byte counts are not measured physical transfers, peak working set or
an execution-cost reduction. Emitted specialization code/configuration remains
unknown because no specialization exists. Holdout parameters/inputs remain
untouched; no activation corpus or new mechanism is claimed.

## Reproduction and remaining baseline work

The committed receipt binds the acquisition-script hash, fixed-revision
card/config hashes and official API metadata whose resolved revision matches
the pin. These provenance fields were added during review; the original
pre-extraction selection packet remains separately hash-bound. This is not a
signed whole-file or toolchain seal. Raw extracts are private ignored artifacts.
An independent reader can retrieve the two exact ranges from the pinned URL
and run the offline probe, which rejects wrong sizes/hashes before BLAS:

```sh
mkdir -p artifacts/T-0200-source
curl --fail --location --range 26029616-26160687 --max-filesize 131072 'https://huggingface.co/EleutherAI/pythia-14m/resolve/cf967c0a9a04383db6f7b1108d86b2962634b4ac/model.safetensors' --output artifacts/T-0200-source/weight.f16
curl --fail --location --range 26028592-26029615 --max-filesize 1024 'https://huggingface.co/EleutherAI/pythia-14m/resolve/cf967c0a9a04383db6f7b1108d86b2962634b4ac/model.safetensors' --output artifacts/T-0200-source/bias.f16
python3 docs/research/probes/pythia_affine_reference.py --source-dir artifacts/T-0200-source
```

These are reproduction instructions, not additional executed acquisitions.
The probe accepts only its eight constructed commissioning inputs; it is not
an admission API for arbitrary caller data. A later such API must validate raw
F16 length/finiteness/domain before either candidate or oracle execution.

The installed compiler available for the next ordinary fixed-parameter control
is Apple clang21.0.0 (`clang-2100.1.1.101`, arm64-apple-darwin25.6.0). Pin that
identity and actual build flags in the next receipt. A readonly constant table
plus normal optimization is a required conventional control, not a new Raveil
mechanism. Do not call a strict serial reduction the strongest compiler result;
compare admitted vectorization/FMA/layout choices under the common envelope.
Any relaxation must be justified before running it; numerical agreement on
finite tests is not a universal proof.

Mirage's OSDI2025 paper covers GPU-hierarchy algebra/schedule search and
probabilistic equivalence: https://www.usenix.org/conference/osdi25/presentation/wu-mengdi .
Its abstract does not prove support for this exact F16-input/F32-result error
contract or a CPU backend. Applicability, version and any adoption remain open;
it has neither run nor been defeated. This is why the next task commissions
known fixed-parameter controls rather than proposing a hardware advantage.
