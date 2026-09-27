# T-0201: Ordinary compiler controls for the pinned affine function

Date: 2026-09-27. Task [#272](https://github.com/bhind/raveil/issues/272).
Context: ADR-0103, proposed RFC-0007; host-functional and analytical compiler
observations only. No EXP freeze, performance collection or Gate conclusion.
Owner explicitly approved this successor after the earlier registration refusal.
Base: `2d75317657ad41bd34965d0fcf83a7ff52ce6639` (T-0200 / PR271).

## Question and matched controls

Does making the unchanged T-0200 parameter table visible to an ordinary
compiler remove work, as distinct from changing its reduction schedule?
Four controls were fixed before compilation: runtime/fixed table crossed with
serial/fma4. Same dimensions, row-major layout, eight commissioning vectors,
parameter bytes, compiler and flags within each pair. Runtime parameters are
supplied on every invocation; fixed parameters are `static const float` in
the compilation unit. Fixed code retains the same call signature but ignores
runtime W/b arguments. This is conventional constant specialization, not a
new Raveil mechanism. The manually partitioned fma4 reduction is also known
practice, not an optimizer discovered by Raveil.

The [T-0200 source and numerical contract](T-0200-immutable-affine-workload.md)
remains unchanged. No source refetch, quantization, pruning, holdout execution,
activation corpus, framework installation or RTL expansion. Source/revision,
reference/probe/compiler hashes and results are in the
[receipt](../receipts/T-0201-compiler-controls.json).

## Numerical argument and artifact identity

All admitted operands are exactly widened finite binary16 values; x is bounded
by 8. Serial executes 128 products and 128 additions from b. Four-lane fma4
executes 32 explicit correctly rounded fused operations in each independent
accumulator, then `((s0+s1)+(s2+s3))+b`. Each coefficient occurs exactly once,
so both source expressions implement the same real affine function. Each
fma4 contribution traverses at most 32 fused roundings and three final adds;
`gamma_36` is a conservative bound within the unchanged `gamma_258` envelope.
The earlier no-overflow/no-underflow argument applies. Bias and every product
remain in the absolute-sum error scale, including cancellation.

Build uses `-std=c11 -O3 -fno-fast-math -ffp-contract=off -fPIC` and an explicit
installed SDK root. Contraction is forbidden in serial and explicit through
`__builtin_fmaf` in fma4. A compiled `fegetround()==FE_TONEAREST` check is
required. No reassociation flag or approximate arithmetic is enabled.
This is a source-level mathematical argument under those execution semantics,
not a proof of compiler correctness. Functional tests are finite checks.

C literals use exact hexadecimal float spelling with `f` suffix. The verifier
compares the whole widened W and b images with the compiled object's readonly
constant bytes. It does not export table getters that would force otherwise
unused constants to survive. Original source hashes must match before any
source generation or compiler invocation. Existing output directories reject;
failed and successful runs stay separate. Inputs remain the eight constructed
T-0200 vectors; this is not an arbitrary-input public admission API.

Each C invocation overwrites an output initially filled with NaNs, then repeats
with 123 in every component. Both results must be finite, satisfy the independent
integer oracle's rational bound and match bitwise. Runtime/fixed results must
also match bitwise within each reduction. Accelerate is separately checked
against the same exact oracle, not used as truth. Its different rounding need
not match either reduction bitwise.

## Observed compiler output

Apple clang21.0.0 (`clang-2100.1.1.101`), arm64, macOS26.6.2, Python3.14.6.
The compiler path/hash and explicit SDK path are in the receipt. Generated
source, assembly, objects, dylibs and raw command logs stay private outside Git;
only owned generator/test code and hashes/counts are committed.

| Control | Object `__TEXT,__text` bytes | Object `__TEXT,__const` bytes | Static affine instructions |
|---|---:|---:|---:|
| runtime serial | 232 | 0 | 51 |
| fixed serial | 244 | 264,192 | 54 |
| runtime fma4 | 412 | 0 | 96 |
| fixed fma4 | 136 | 264,192 | 27 |

Text sections include the common rounding-mode check; affine instruction
inventories exclude that helper and count each instruction once, including
`ret`. Section bytes are not an installation image, working set, executed
instruction count or physical traffic. Runtime controls still require the
same 264,192 bytes of externally supplied widened parameters; zero object
constants does not make that storage free. Whole object/dylib/source byte sizes
and relocation counts are retained separately. Dylib UUID/link metadata may
vary between repeated builds, so whole-file byte identity is not a claim.

Inspecting the retained assembly explains the apparent fma4 code shrinkage:
runtime unrolls each row into 32 `fmla.4s`; fixed emits two `fmla.2s` inside a
32-iteration inner loop. Both perform 128 scalar FMA lanes per row, or 65,536
across 512 rows. Serial uses four `fmul.4s` and sixteen scalar adds per inner
iteration, repeated eight times per row: 65,536 multiplications and 65,536
additions across rows. These are loop-derived analytical counts, not hardware
counters. No coefficient multiplication disappeared through fixed-table
specialization in these four emitted kernels. This is a scoped observation,
not a theorem that immutable parameters can never reduce work.

Runtime fma4 additionally has a 128-byte stack frame (input spills and saved
registers); fixed fma4 has none in the affine kernel. Runtime hoists input loads
and fixed repeatedly loads inputs through its loop. Neither instruction count,
stack size nor source-level byte count establishes actual cache/DRAM transfers
or which implementation is faster. This compiler portfolio is not an exhaustive
layout, unrolling, multi-row-vectorization, LTO or constant-expression search.
Mirage and other published approaches have not been executed or defeated.

## Full-cost boundary and result

The unchanged source W+b is 132,096 bytes; widening needs 264,192 bytes in
both representations. Generation, compilation, object verification and loading
are explicit preparation for fixed code. Runtime widening/allocation also costs
work. Fixed parameter replacement requires regeneration/recompilation and
reverification; runtime replacement requires validation/widening. No replacement
cost, compilation time, execution time or break-even point was measured.

C reads b in its row calculation and overwrites y directly: no separate b-to-y
copy. Accelerate's `beta=1` API initializes y by a 2,048-byte bias copy each
invocation. Both produce 2,048 bytes from a 512-byte widened x. Record these
API differences rather than pretending identical reset operations. Python/ctypes
validation scaffolding and simultaneously loaded libraries are not a measured
production working set. Physical movement, lazy initialization and dispatch
remain unsealed for any future performance experiment.

All four C controls pass eight inputs and two output initializations: 32,768
component checks. Accelerate adds 4,096 checks. Both matched pairs are bitwise
equal on these eight inputs. No new optimization, speed, energy, area, full-model
quality, hardware contribution or Groq superiority follows.

The next research question is now concrete: can a precisely stated exact-real
transformation reduce the retained coefficient work beyond these and the closest
applicable published controls without relocating the cost into larger code,
configuration, preparation or numerical error? Do not commission hardware or
freeze a timing experiment from these results. A further mechanism/search scope
is not part of T-0201; retain it as an uncommissioned question.

## Reproduction

From the repository root, using the unchanged verified T-0200 private source:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_pythia_compiler_controls -q
PYTHONDONTWRITEBYTECODE=1 python3 -O docs/research/probes/pythia_compiler_controls.py --source-dir ../T-0200-evidence --output-dir ../T-0201-evidence/NEW-RUN
PYTHONDONTWRITEBYTECODE=1 python3 .agents/skills/raveil-task-governance/scripts/check_records.py
git diff --check
```

Use a new directory for every run. Compare input/output hashes, constants,
flags, section counts and instruction inventory; do not demand identical dylib
UUIDs. Retained setup failures: run1 lacked explicit SDK lookup (`fenv.h` not
found); run2 compiled but the loader rejected omitted LC_UUID. Adding the
installed SDK and retaining the normal linker UUID fixed those separate local
setup defects. Run3 passed; run4 removed table getters; run5 corrected the
static inventory to include operand-free `ret`. No numerical failure or
post-data numerical-contract change occurred.
