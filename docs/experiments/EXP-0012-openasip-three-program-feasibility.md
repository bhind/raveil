# EXP-0012: OpenASIP three-program feasibility witness

Status: In progress
Task: T-0191
Date: 2026-09-09

## Question

Can one exact OpenASIP v2.2 machine execute three topology- and
memory-distinct Raveil-owned programs without regenerating the machine, while
Raveil retains oracle, cancellation, fallback and publication authority?

## Frozen identities

- OpenASIP: `f2282048f4c78d18190a9b77e7497e29a164721d` (`2.2-r1`)
- llvmtce: `b47e651cc052ba9e097701efa8840e8f3081c84d`
- ADF SHA-256: `1b290e9d90cfe93397200b356979ba3f2bf8da3df56b5e27e879483b5a976b5c`
- Linux/amd64 toolchain image: `sha256:c78fee2f78956bc0ca8acc9527e42648dc2c00e57b4906276ebd7ff44e13048b`
- input manifest SHA-256: `e3fa3cdefbf02fe83d01dccd2fbe44040128fb4eea32cbe2b11529d3841d6a7a`
- normalized generated-VHDL tree SHA-256:
  `19b6128e75369e8f3198f0dfceb15804a0a00b0d55138e2bc768c8be3149689b`

The macOS arm64 host ran the exact linux/amd64 image through Docker. Runtime
containers were read-only, networkless, non-root, capability-free and bounded.
The fixed-machine compiler plugin was generated at image-build time so runtime
did not require writable executable scratch.

## Result

All three independent unsigned-32 oracles matched one fixed `ttasim` run per
program. TPEF disassembly was non-empty and passed a bounded anti-constant-folding
witness: at least 20/8/12 `ld32` operations for neighborhood/elementwise/
reduction, plus an elementwise `__mulsi3` witness.

| Program | Result | TPEF bytes | TPEF SHA-256 | Static `ld32` witness | `ttasim` run-cycle counter, n=1 |
|---|---:|---:|---|---:|---:|
| neighborhood | 170 | 3,530 | `c464870ebbf5183a514f6818827146477bf6f646e7a65e681ad5773b760c607f` | 28 | 136 |
| elementwise | 740 | 4,694 | `ef063bb10ceedc9fff39ff216023a42b8893276ba5aa7336ab50188173c6cc5b` | 21 | 386 |
| reduction | 374 | 2,243 | `ce276d0716b4fb51cfa2d058fdadc324517a79bcc52d9cacd20883175a9ba6f8` | 13 | 64 |

The private local run receipt SHA-256 is
`5201f55e8c788601a74802484b58617984173eb6a053edf11939679aa265e272`;
the post-oracle Raveil-authorized receipt is
`e85cfeae2232a432c5162a4ad38bef1392cede97936b4954cd5a6da0b8b94543`.
It binds exact argv, source/TPEF/log/disassembly hashes, diagnostic host
integration durations and simulator-reported register-access statistics. Raw
files are not committed or published by this partial result.

The actual simulator entrypoint now runs through the Raveil-owned lifecycle
boundary. Cancellation-before-start does not invoke the candidate, candidate
failure or oracle mismatch selects the actual native-CPU fallback, candidate output
begins unpublished, and only Raveil changes an oracle-matching receipt to
published. In-flight cancellation parity remains unproved.

`generateprocessor` plus the recorded same-image repair produced ten VHDL
files totalling 76,211 bytes from the same ADF. Two independent generations
had the same normalized tree identity above; raw `rf_bool.vhd` and
`rf_rf.vhd` hashes differed only in OpenASIP's generated-on timestamp comment.
The second sealed RTL receipt SHA-256 is
`dc9bdcb9c1b925838accd147b6c60e1e21bd7ed369d980ed1ca6096a569007e8`.
Generation took 3.124 seconds of host integration time in that run. A
documented Docker Desktop bind-copy failure for the 14,325-byte stock
`lsu_le.vhdl` was repaired from the exact same image and then hash-sealed.

TPEF program-image payloads were 3,530, 4,694 and 2,243 bytes. Separate
container-plus-ADF-plus-TPEF load probes completed in 563.9, 541.4 and 564.9 ms
respectively. These are n=1 host integration diagnostics, not device
configuration time or performance measurements.

## Interpretation and remaining gate

This answers the narrow three-program simulator feasibility question
positively. It does **not** complete T-0191. A durable approved raw-artifact
destination, in-flight cancellation parity, and independent
final review remain open.

The counters above are not latency, throughput, memory/cache traffic or a
cross-backend comparison. Host integration duration includes Docker and host
scheduling and is diagnostic only. This record makes no performance, PPA,
FPGA, ASIC, silicon, adoption, patent or FTO claim and cannot close T-0044 or
ADR-0049.

## Commands

```text
docker --config <isolated-empty-docker-config-directory> build --platform linux/amd64 --target toolchain --tag raveil-openasip:toolchain experiments/openasip
./experiments/openasip/run_three_programs.sh --simulate --evidence-dir <private-empty-directory>
python3 experiments/openasip/generate_rtl.py --output <private-empty-directory>
python3 experiments/openasip/verify_evidence.py run <private-run-directory>
python3 experiments/openasip/verify_evidence.py rtl <private-rtl-directory>
python3 -m unittest tests.test_t0191_openasip
```
