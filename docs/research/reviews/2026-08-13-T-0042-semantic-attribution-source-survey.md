# T-0042 semantic-attribution source survey

Status: read-only implementation packet
Date: 2026-08-13
Decision context: ADR-0045

This packet locates the pinned CPU lifecycle signals relevant to the first
commit-aware attribution diagnostics. It is source inspection, not an
implemented probe, RTL result, semantic proof, patent search, legal opinion, or
permission to implement a patent claim. Line numbers are revision-specific.

## Exact source boundary

- Chipyard: `ac58f38d77c99e9d1cafa64dfd6d4b00bdcd43e1` (tag `1.11.0`)
- Rocket Chip: `749a3eae9678bc70b029c5b9091fae33fad539c4`
- BOOM: `9459af0c1f6847f8411622dac770ac78fe10847c`
- Pin records: `hardware/chisel/rocket-pin.env` and
  `hardware/chisel/boom-pin.env`
- The inspected ignored Chipyard tree resolved to those exact revisions and
  reported no local tracked-source changes.

The upstream license locators and SHA-256 values are:

- Chipyard `LICENSE`:
  `c36c8dd92ba95a48aaed1b89de09a636d5a4e1dd2e726428d0c0b3644a267cd5`
- Chipyard `LICENSE.SiFive`:
  `63b453c2c3f5e5d31007f55eaacc2b72e8b7a40e6ab33eae6972ba010fa7acc4`
- Rocket Chip `LICENSE.Berkeley`:
  `54349a017a8a0876fcc5ef281fc37aedbf5a008158395eaad0f589ade7f019cc`
- Rocket Chip `LICENSE.SiFive`:
  `63b453c2c3f5e5d31007f55eaacc2b72e8b7a40e6ab33eae6972ba010fa7acc4`
- Rocket Chip `LICENSE.jtag`:
  `8d0cdcf66ae00aefe3b2f4d48798bca923651cb1ad297ff007b16cfab122ec00`
- BOOM `LICENSE`:
  `0dff9c3cc0950c7ae66a0d88eec0cee96a978d0bb3525a9cddc309fcd860b004`
- BOOM `LICENSE.SiFive`:
  `63b453c2c3f5e5d31007f55eaacc2b72e8b7a40e6ab33eae6972ba010fa7acc4`

These files establish source provenance and copyright-license locators only.
They do not establish patent scope, non-infringement, or freedom to operate.

## Rocket lifecycle locators

All paths below are under
`external/chipyard/generators/rocket-chip/src/main/scala/rocket/`.

- `RocketCore.scala:238,257,274,506,572,632` locates the EX, MEM, and WB PC
  registers and their pipeline transfer.
- `RocketCore.scala:514` locates structural replay before request acceptance.
- `RocketCore.scala:606-611` locates DCache kill, MEM replay, common kill, and
  exception-related kill composition.
- `RocketCore.scala:637-670,707,721-723` locates WB exception, replay/redirect,
  exception-free WB validity, and architectural retirement.
- `RocketCore.scala:917-937` locates the EX-stage DCache request fields and the
  following `s1_kill` decision. The token must bind the pipeline PC belonging
  to this same candidate rather than a later unrelated MEM value.
- `RocketCore.scala:962` and `HellaCache.scala:168-180` locate downstream replay,
  kill, nack, and exception interfaces.

The Rocket implementation must still fix and test the exact conjunction of
WB valid, no exception, store control, and retirement used for store
authorization. This survey does not choose that signal expression.

## BOOM lifecycle locators

All paths below are under
`external/chipyard/generators/boom/src/main/scala/`.

- `common/micro-op.scala:59,77` locates branch mask and ROB index. Both are
  bounded, reusable lifecycle context and are not unique identity.
- `lsu/lsu.scala:56-135` locates execution, DCache, and core LSU interfaces.
- `lsu/lsu.scala:188-201,217-238` locates load/store queue state, the committed
  bit, queue heads, and the explicit request/replay state machine.
- `lsu/lsu.scala:487-500,563` locates store-commit issue eligibility and its
  scheduler selection.
- `lsu/lsu.scala:645-706,765-821` locates kill, memory exception, request fields,
  and replay issue paths.
- `lsu/lsu.scala:1273-1303,1408-1428` locates response/nack handling plus branch
  mask update and kill behavior.
- `lsu/lsu.scala:1450-1513` locates ROB-driven queue commit and the condition
  that a committed store was successfully sent to memory.
- `exu/rob.scala:118-140,390-435,640-675` locates commit/rollback signals, LSU
  and CSR exception capture, commit eligibility, and oldest-exception checks.

The BOOM implementation must correlate a repository-owned sequence and epoch
with these signals. ROB index reuse and branch-mask updates may validate the
lifecycle but never mint or recycle an identity.

## Similarity and IP-risk triage

The token/epoch and fail-closed verifier are diagnostic interface mechanisms.
Their replay, precise retirement, exception recovery, ROB/LSU correlation, and
memory-completion concepts overlap conventional OoO machinery and the
TRIPS/EDGE commit and precise-exception material already identified in
`2026-08-11-T-0057-native-graph-prior-art-matrix.md`. The narrower RFC-0005
simulation disposition in
`2026-08-12-T-0057b-simulation-ip-disposition.md` deliberately excluded a
general token store, ROB, LSU, commit frontier, and precise architectural block
commit.

ADR-0045 authorizes only CPU-specific diagnostic probes and repository-owned
metadata under the existing pinned-source boundary. It authorizes no copied
upstream implementation and supplies no novelty basis. If later work adopts a
generalized commit frontier, block-atomic commit, target instruction encoding,
dependency-ready issue, or another mechanism beyond these diagnostics, stop
and perform a new claim-to-feature review with qualified legal escalation as
appropriate. Existing patent-family, transitive-license, non-infringement, and
FTO gaps remain open.

## Implementation gate

Before either CPU token feeds the ADR-0043 bridge, its diagnostic must record
exact patch/source hashes and pass every ADR-0045 positive and negative case.
Untested lifecycle paths remain unknown. Source/origin classifiers remain
transport evidence and cannot fill a missing token or commit correlation.

## Commands used

```text
git -C external/chipyard rev-parse HEAD
git -C external/chipyard status --short
git -C external/chipyard/generators/rocket-chip rev-parse HEAD
git -C external/chipyard/generators/boom rev-parse HEAD
rg -n 'mem_reg_pc|ex_reg_pc|io\.dmem\.req|dcache_kill_mem|replay_next|wb_xcpt|csr\.io\.retire' <Rocket sources>
rg -n 'rob_idx|br_mask|committed|can_fire_store_commit|stq_commit|mem_xcpt_valid|s1_kill|nack|rbk_valids' <BOOM sources>
shasum -a 256 <Chipyard, Rocket Chip, and BOOM license files>
```
