# Bounded Graph capacity pressure: T-0184

Status: planning findings; no compiler, ABI, RTL or capacity change
Date: 2026-09-19
Authority: main `1a6b18e`, Issue #183, ADR-0088

## Reproduce

```sh
PYTHONDONTWRITEBYTECODE=1 python3 tests/fixtures/graph_pressure/check_pressure.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_graph_device_dag tests.test_graph_device_affine -q
```

The retained `cases.json` contains exact descriptors and rejection messages.
The checker enforces all 17 named cases (six admits, eleven rejects) against
the unchanged compiler, including when Python uses `-O`. These are constructed
boundary probes, not real-user frequency or representative performance data.
The dilation probe extends T-0185's workload question; the other probes are
synthetic controls. No RTL simulation, device, timing or area collection ran.

For each admitted descriptor, seeds 0, 5 and 19 give direct Graph oracle/encoded
fallback agreement. These paths share dependencies; no independent hardware
verification is claimed. The schedule pair has identical nodes/edges and equal
direct-oracle outputs for the three seeds despite different admission. Printed
hashes cover fixtures and three named source modules, not the whole dependency
closure/environment; the output is not a sealed experiment receipt.

## Observed boundaries

| Dimension | Admitted control | Actual rejection | Interpretation |
|---|---|---|---|
| Instructions | 16-node chain; eight-neighbor dilation (16) | 17-node chain; center-inclusive 3x3 dilation (18) | Current 16-instruction program budget |
| Retained registers | Eight loads and STORE (9 nodes) | Nine loads and STORE (10 nodes) | Eight loads are unused; this is not nine semantically live values |
| Author order | Consume l0/l1 before loading l2..l8 (11 nodes) | Load all nine first (same 11 nodes) | Descriptor-order-sensitive allocation; seven unused nodes in both cases |
| Shape | 16x16, strides18/16 | rows17; columns17 | Explicit shape bound |
| Stride/windows | 8x8, strides10/8 | input stride9 or37; output stride7 or40 | Minimum layout and 324-input/256-output windows |
| Halo | Relative (+1,+1) | Relative (+2,0) | Existing one-cell relative-load contract |

The error “more than eight live values” overstates semantic liveness for these
register examples. `compile_descriptor` frees a source at its last consumer,
but zero-consumer results never reach that release path. These probes do not
establish intrinsic demand for more hardware registers. Moving a consumer
earlier admits one example without changing nodes, edges or arithmetic; it
does not admit the 18-instruction dilation.

## Alternatives and one selected follow-up

1. **Keep stable compilation; add actionable hints to `project check`.**
   Preserves admission, accepted payloads, trace, ABI and oracle behavior.
   The benefit is an editing path; no larger program is admitted automatically.
2. **Bounded reuse scheduling / unused-result retirement.** Could reduce the
   retained slots in these examples, but is not implemented or simulated here.
   Any later proposal must define deterministic selection, lifetime traces and
   already-admitted-program compatibility under ADR-0088. These dead-node
   probes do not justify general schedule search or hardware expansion.
3. **Host spatial tiling.** Might handle larger grids within existing per-tile
   windows, but requires edge/halo/assembly and partial-failure contracts. It
   does not shrink an 18-instruction per-cell expression or provide radius-two
   loads. Multi-pass expression decomposition is a different design.
4. **Increase capacity.** Reopens the 32-word transport, instruction/register
   encoding, compiler/validators/traces and RTL; not authorized or justified
   by the register examples.

Choose option 1 as the only next slice. On known Graph rejection, retain the
original admission failure and explain the current instruction, affine/halo or
register-retention boundary. Unknown errors remain unchanged. A hint never
proves that an edited descriptor will pass: normal admission still decides.
Independent review suggested rejecting unreachable nodes; that would newly
reject currently admitted examples, so prefer advisory-only feedback here.

Compatibility: unchanged 16 instructions, eight registers, 32-word transport,
324/256 windows, schemas, instruction bytes, source hashes and oracle/RTL paths.
Acceptance: retained controls keep identical preflight pass/fail, files remain
unchanged, no tools execute, known rejects receive bounded useful hints.
No-go: automatic pruning/reordering, changed acceptance/bytecode, new
schema/RTL/transport, or treating a heuristic as proof. Capacity implementation
remains a separate architectural choice; no research gate or Sprint ceremony
is closed by this report.
