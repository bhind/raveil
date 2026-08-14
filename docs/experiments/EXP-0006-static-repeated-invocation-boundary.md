# EXP-0006: Static repeated-invocation boundary

Status: Completed
Evidence class: RTL simulation pilot
Date: 2026-08-14
Task: T-0044
Authority: RFC-0004, RFC-0005, ADR-0039, ADR-0046, T-0042 integration
commit `528fbe28a0dcdfbab65d4ae2995c0876857e053a`, boundary implementation
commit `10b4f0fc2efe1e0b7f3d6a8722c5c766a23a6c2d`, collector implementation
commit `7575602e6651cc1e755e8d2f7b255aa8872db856`, runtime-fix commit
`80a35e61881393ba9790b19719eb1f6dcb4ee415`, installation-accounting
commit `cf454e4cd847d43d223fe7166b20d75dae0c2ffe`, log-synchronization commit
`988c25e615feaf711cb4d91f121d551bf88420ea`, completed-outer-log
verification commit `4a3faefc4c37aeb02c642b37fb4d20827021fb34`
Docker-output-drain commit `45a453ce8ee61bd2aba67caf282d5b5de44ba99a`,
and Graph raw-transport commit
`75d911c714458ddd5a747f1584641152c1a7fd15`.
Prior evidence: EXP-0005 (preserved unchanged)
Manifest: `benchmarks/manifests/t0044-static-repeated-invocation-v1.json`
Frozen manifest SHA-256:
`b979f7448a1f73485d7ed42d1e499dcd50f58ff80c6091d0ee11cb89cbb6121d`

## Falsifiable question

Can static Graph, Rocket in-order, and BOOM OoO each execute ordered fresh
RFC-0005 inputs in one simulator process with one reset, one installation, no
artifact reload, exact per-invocation lifecycle accounting, independently
verified output bytes, and the same execution-window meaning? BOOM
serialize-dispatch is included only as a retained-structure diagnostic.

The commissioning stage answers only whether inputs 1--4 establish this
boundary and identifies fairness gaps. It is non-claim evidence. Only after it
passes unchanged may a separate 256-invocation RUN-ID derive the frozen
1/4/16/64/256 prefix accounts. Neither stage completes T-0044 or supplies
energy, timing, area, other Graph organizations, FPGA, ASIC, or silicon
evidence.

## Frozen session and phase contract

Each candidate session has exactly one simulator process, reset, installation,
and artifact, with no re-elaboration, reboot, program/descriptor reload, or
artifact replacement between inputs. Inputs are deterministic versions 1--256
in fixed order; input and output storage is overwritten every invocation and
actual 256-word output responses are hashed against the independent oracle.

Installation ends at the first owned input request. Staging runs from that edge
or the previous validation response through the final current-input staging
response and includes candidate-local preparation. Execution retains EXP-0005's
same-meaning final-staging-response through final-output-write-response window;
the Graph launch cycle is included. Drain/completion ends at the first
validation request. Validation ends at the 256th output response. Publication
is zero-cycle because output evidence is emitted on validation responses. The
account ends at the final validation response; later CPU checksum/`tohost`
cycles are outside it.

The CPU generates deterministic inputs with candidate-local instructions while
Graph generation is testbench-side. This asymmetry is frozen and visible. It
does not invalidate the execution window, but staging and end-to-end claims are
ineligible unless commissioning proves a same-meaning interpretation. The
predeclared result for an unresolved asymmetry is `pause`, not silent omission.

## Primary, diagnostic, estimator, and inference unit

The primary matrix is static Graph, Rocket in-order, and BOOM OoO. Each retains
lawful optimization: CPU load reuse stays enabled and Graph's extra traffic is
reported. CPU weakening is forbidden. BOOM serialize-dispatch remains
diagnostic-only and is never an “OoO-disabled CPU”. No secondary matched-load
ablation is active.

Commissioning derives prefixes 1 and 4 from one four-input session per member.
The campaign, if authorized, derives 1/4/16/64/256 from one 256-input session
per member; these nested prefixes are not independent samples. The inference
unit for input-dependent behavior is the fresh input at its frozen position.
Report exact vectors, cumulative and amortized totals, median, minimum,
maximum, and paired candidate/Rocket ratios. An input-dependent 95% paired
percentile bootstrap uses 100,000 MT19937 resamples with seed 6006 while
holding installation fixed once per resampled account. Input-invariant cycles
use exact values and distinct-input reproducibility counts without an
inferential interval. Commissioning intervals are never claim-bearing.

## Fail-closed and transition rules

Stop on oracle or resource failure; unexplained/pending traffic; missing
accounting; source, config, toolchain, artifact, or session drift; incomplete
matrix; different execution-window meaning; restart/reset/reload; or duplicate
or missing input/output versions. Dynamic traffic inequality alone is not a
failure, but an unexplained fairness boundary is claim-ineligible.

The full campaign may start only after the four-member commissioning passes and
a fairness review finds no source/config/toolchain change. Campaign account
256 is a new RUN-ID and artifact parameterization and must independently pass
its prefix 1 and 4 gates. Any other implementation/config/toolchain change
requires a new freeze and commissioning. Failed runs remain evidence.

Below 64 fresh inputs no RFC-0005 numerical no-go is permitted. Latency/traffic
cannot declare go. Missing energy, timing, and area always makes the result
partial/pilot. The only terminal labels are `advance`, `pause`, and
`early no-go`.

## Evidence layout and commands

Raw logs and exact command metadata are written under ignored
`artifacts/research/EXP-0006/<RUN-ID>/raw/`; derived analysis is written under
`derived/`; `raw-seal.json` binds raw bytes and the derived report. Host
wall-clock is operations-only.

Commissioning from a clean checkout of the freeze commit:

```sh
python3 -m raveil.t0044_repeated collect \
  --repo . \
  --manifest benchmarks/manifests/t0044-static-repeated-invocation-v1.json \
  --chipyard-source /path/to/pinned/chipyard \
  --account 4 \
  --run-dir artifacts/research/EXP-0006/<RUN-ID>
```

Earlier freezes produced only retained failed commissioning attempts. Stack,
installation-accounting, completed-outer-log verification, and bounded Docker
output-drain corrections changed source, so the manifest was re-frozen with
the hash above before any replacement run or complete-matrix observation.
RUN-ID `20260814T093000Z-7d24062-commission7` then failed closed before any
matrix result: Graph outer raw contained 215/1,024 required output markers
after the 30-second wait. The Graph wrapper was applying its legacy 240-line
interactive preview to repeated evidence despite holding and internally
verifying a complete temporary log. No value from this run is promoted. The
repeated-only full-log transport correction requires a replacement freeze.
That correction is now replacement manifest authority under the hash above;
no subsequent complete-matrix data existed at this re-freeze.

## Estimate

The initial narrow estimate was 2--5 hours at medium confidence. Discovering
the compile-time CPU seed and one-shot manager changed it to 3--6 hours for
implementation/freeze plus about 15--60 minutes for commissioning, at
medium-to-low confidence until the first end-to-end run. This is a range, not a
single-date commitment. The first completed end-to-end matrix used
382.929190 operations-only wall-clock seconds in total (38.487 Graph, 71.478
Rocket, 77.670 BOOM, and 195.294 diagnostic BOOM). With the same warm build
volumes, a clean replay is now estimated at 6--20 minutes at medium confidence;
host wall-clock is not CPU performance evidence. The 256-input campaign is not
estimated or authorized while the pause below remains.

## Completed commissioning evidence

RUN-ID: `20260814T100000Z-7b6e5df-commission8`

- Collection/freeze commit: `7b6e5df1fa5620407cbca5f5d76857742cc57a7f`
- Manifest SHA-256:
  `b979f7448a1f73485d7ed42d1e499dcd50f58ff80c6091d0ee11cb89cbb6121d`
- Derived report SHA-256:
  `6578f708833774291d0e591ddcbeb544663173c51eb671d2f3ab6bd8e79a2fcd`
- Raw seal SHA-256:
  `746d672ce0271c2480442712c5538afcdf2c74f6daeb5476ef390aca7fe6c401`
- Environment: Apple Silicon host operating pinned `linux/amd64`
  Docker/Verilator paths; host wall-clock is operations-only.
- All four commands exited zero. Inputs 1--4 are distinct, every 256-word
  output matches the independent oracle byte-for-byte, and the primary
  contract/resource/output hashes agree for each input.
- Every candidate session has one process, reset, installation, and artifact,
  with no reload. Installation is nonzero only on CPU invocation one; later
  CPU installation cycles and reads/writes are zero.

The exact command was:

```sh
python3 -m raveil.t0044_repeated collect \
  --repo . \
  --manifest benchmarks/manifests/t0044-static-repeated-invocation-v1.json \
  --chipyard-source /private/tmp/raveil-t0042-small-start-impl/external/chipyard \
  --account 4 \
  --run-dir artifacts/research/EXP-0006/20260814T100000Z-7b6e5df-commission8
```

### Primary 1/4 latency and traffic

Cycles are exact RTL-simulation counts for ordered fresh inputs, not repeated
samples of one deterministic input. `Total@4` is cumulative installation,
staging, execution, completion, validation, and publication. Traffic is the
accepted/completed execution-window transaction count per input.

| Candidate | Execution cycles, inputs 1--4 | Traffic/input | First-input phase cycles I/S/E/C/V/P | Total@4 |
| --- | --- | ---: | --- | ---: |
| Static Graph | 3,073 / 3,073 / 3,073 / 3,073 | 1,536 | 0 / 648 / 3,073 / 1 / 512 / 0 | 16,936 |
| Rocket in-order | 14,592 / 14,548 / 14,548 / 14,548 | 1,056 | 48,239 / 4,511 / 14,592 / 16 / 4,367 / 0 | 142,104 |
| BOOM OoO | 21,904 / 21,900 / 21,902 / 21,903 | 1,056 | 48,315 / 4,199 / 21,904 / 14 / 6,631 / 0 | 179,420 |

Per input, every candidate reports 1,280 useful loads, 1,024 adds, 256 useful
stores, and 256 outputs. Graph exposes those as 1,280 reads plus 256 writes
(5,120/1,024 bytes); each CPU lawfully reuses loaded values and exposes 800
reads plus 256 writes (3,200/1,024 bytes). All accepted operations complete,
pending/unexpected/non-origin traffic is zero, and request stall plus response
backpressure are both zero. Graph reports 3,072 schedule-active plus one launch
cycle. CPU frontend and rename/ROB/issue/LSU activity are explicitly
unavailable, not imputed as zero.

CPU invocation one also accounts 580 installation writes, 324 staging writes,
1,056 execution operations, and 256 validation reads: 2,216 accepted and
completed lifecycle operations. Later inputs omit installation and account
1,636 accepted and completed operations each. Publication is zero cycles
because output words are observed at validation responses.

### Diagnostic only

BOOM serialize-dispatch records execution cycles
70,871 / 70,862 / 70,862 / 70,862 and cumulative four-input total 506,210.
It is a same-core diagnostic only, is not an “OoO-disabled CPU”, and does not
replace either primary baseline. The secondary matched-operation/load ablation
was not activated.

### Immutable identities

Common contract SHA-256 is
`ebdf8c046ca692959e8cad7cdf419ba4f991345c653a281be0bc235ea8979bb9` and
common resource SHA-256 is
`16664d8ed96865c60ea41c91452b5e6748b055e0dfef3f786b13bd6f90127748`.

| Candidate | Source SHA-256 | Configuration SHA-256 | Artifact SHA-256 | Toolchain SHA-256 |
| --- | --- | --- | --- | --- |
| Static Graph | `a761b632245a5e336641011f62daa48f689ffa5678c4d37ce9f40146ab639d3e` | `cc99bc01f0b38ded9757a5cd19bd0288e7cfe5f591546c4a094a2403af406b65` | `2571973187981cd52046c05a06b8a7a278926518b81513175be3d24432df4146` | `2009341570a17fbe47fb9600be97eec8fa50b1dceba0b04357c2eb01fe947037` |
| Rocket in-order | `81f471d35ff572db27ee4d58bc9f4d85ea3480b54ef2c6d70bb99caee699e74d` | `d53e5d2a50260dd93498c275a56c1bedafbd481eecd5fa62e74e34dc22323303` | `fdbc185fa292d9770f75a7cb474c956d5b5fef03a37e4a431f3e0eda3ef0e7e0` | `ae2488b8904a8f6246a11df60be85bc08e965c3aee0518c976319bc34d448eee` |
| BOOM OoO | `4b62c323bb6feda48ade153ffc78798b6f75a12696eb3950003d025ef2149248` | `8a4ff53d6dbff159edd6872dde9ef8dc9d53d9a3725ffbb809d5b71c8dcfbbef` | `52e8b8db29e14ee7928625d976365caf78590d6b69a1e9f4ee5404358e89140e` | `ae2488b8904a8f6246a11df60be85bc08e965c3aee0518c976319bc34d448eee` |
| BOOM serialize diagnostic | `a23c33af74fa19efe6047db6275bb165f2db18fccd44ada750bdad69248a8e75` | `bbfddf865a7201e9441d98f7ccf9c061de15b8e4d9efdd94217363f0df0ba5f7` | `304e6e2064caa6618e46fee1ba6784c817d321d8e4b2ed733b5c4995bfbd578e` | `ae2488b8904a8f6246a11df60be85bc08e965c3aee0518c976319bc34d448eee` |

### Fairness and terminal decision

The primary execution window has the same meaning, retains lawful CPU load
reuse, exposes Graph's extra traffic, and is eligible as partial RTL-simulation
latency/traffic pilot evidence. The commissioning vectors are exact; no
claim-bearing 95% interval is produced at four inputs. The frozen campaign
would use the preregistered paired interval only after authorization.

Staging and end-to-end amortization remain claim-ineligible: CPU fresh-input
generation executes candidate-local instructions, whereas Graph input
generation occurs testbench-side before owned staging requests. Commissioning
does not prove these initiators have the same meaning. Energy, synthesis
timing, area, VLIW/CGRA, elastic, stream, and hybrid candidates are also absent.
T-0044 remains open; neither RFC-0005 go nor numerical no-go is decided.

**Decision: `pause` — resolve only the same-meaning input-staging initiator
boundary before any 1/4/16/64/256 campaign.**

## Closeout verification

The following commands completed with exit code zero on the dedicated
worktree after record reconciliation:

```sh
python3 -m unittest tests.test_controlled_run -v
python3 -m unittest tests.test_t0044_repeated tests.test_t0044_pilot \
  tests.test_controlled_run tests.test_owned_memory_boundary \
  tests.test_static_region -v
./hardware/chisel/run-controlled-three-way-stencil.sh
python3 .agents/skills/raveil-task-governance/scripts/check_records.py
git diff --check
git merge-base --is-ancestor ae606de HEAD
```

The exact unit command passed 10 tests and the combined suite passed 71. The
three-way replay cold-built its separate cache and returned a functional
aggregate with oracle/resource/quiescence/traffic checks passing,
`comparison_eligible=true`, `dynamic_memory_traffic_equal=false`,
`semantic_initiator=not-proven`, and
`t0044_measurement_claim_ready=false`. That replay is a T-0042 functional
regression check, not additional EXP-0006 performance data.
