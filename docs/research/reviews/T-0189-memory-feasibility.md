# T-0189/S04: Scratchpad representation before FPGA mapping

Date: 2026-09-28. [Issue284](https://github.com/bhind/raveil/issues/284).
Authority: ADR-0105/0106; source revision `9a51cc93af843a4a80fb9a1b5c1220a023cf4f29`.
Evidence class: source inspection and generic-netlist structural analysis.
This is not a benchmark, mapped FPGA resource count or performance result.

## Finding

`hardware/chisel/StaticStencilRegion.scala:104` instantiates
`OwnedFixedLatencyScratchpad(1024, 580)`. The scratchpad's `storage` in
`hardware/chisel/OwnedFixedLatencyScratchpad.scala:76` is a zero-initialized
1024-element vector of32-bit registers. The source provides580 valid words;
the remaining444 addresses are rejected. The physical vector is still1024
words. Byte-mask writes select old bytes from the same array.

The S03 verified structural netlist contains no memory cells. After the cached
Yosys `opt` pass, all1024 named storage words remain32 bits each. Counting unique
net bits, then intersecting with sequential-cell Q outputs, confirms32,768
storage bits driven by `$adffe` cells. This is not an alias/name count alone.
The generic netlist also retains variable division/modulo for output-index
addressing (`chipyard-overlay/RaveilStaticStencilCore.scala`, logicalRow and
logicalColumn). Neither fact establishes the eventual critical path or resource
bottleneck. The initial S03 pass used `opt_clean`; this additional `opt` probe
rules out that single omitted generic optimization as the explanation.

Do not convert these numbers to a board FF/LUT/BRAM count, assume all bits
survive vendor optimization, or conclude that the candidate board cannot fit.
This probe performs no memory inference experiment, device mapping or placement.
It identifies what to inspect in the vendor hierarchy/resource report.

## Compatibility obligations for any future RAM implementation

The current source and existing `owned_fixed_latency_scratchpad_sim_main.cpp`
make reset-zero reads, byte-mask merging, next-cycle response availability,
held response stability, one outstanding transaction and deterministic bounds
errors observable. A replacement must preserve them, together with initiator,
phase and transaction/stall accounting. A synchronous memory declaration alone
is not evidence that this boundary is preserved.

A possible future design is unreset data storage plus resettable per-byte
validity: unwritten bytes read as zero, masked writes make only their enabled
bytes valid. This is an unimplemented engineering candidate, not an accepted
ADR, new invention, proven BRAM inference or measured saving. Read-enable
alignment, held data across backpressure and reset while a response is pending
must be specified and checked. Reset must not expose old data, including after
partial writes. Zero-mask writes and repeated reset/write/read sequences matter.
A reset-time full-array sweep would add an initialization interval and cannot
silently replace the current ready/latency contract.

If adopted, keep the existing register backend as a cycle-by-cycle reference.
A bounded candidate test must compare every cycle's ready/valid/error/data and
counters under masks, stalls, reset and invalid addresses; then repeat S01/S02
board-boundary/workload recovery tests. Generic memory-cell inference and actual
vendor resource/clock reports are separate acceptance requirements. Existing
finite tests alone are insufficient to accept that rewrite. No backend changes
are made by S04, and no accepted invariant or historical EXP is superseded.

## Reproduction and identities

Run from the matching source checkout. Input is the source-bound S03 receipt,
verified separately with the command below. Output directory is new. All probe
commands returned0 on macOS26.6.2/Python3.14.6 using cached linux/amd64 Yosys
0.27+3 (b58664d44), pinned image below; no pull/network/install/purchase.

```sh
python3 -m raveil.graph_device_board_preflight verify artifacts/research/T-0189-S03/structural-final
mkdir -p artifacts/research/T-0189/2026-09-28-memory-diagnostic
docker run --rm --pull=never --network none --platform linux/amd64 \
  --mount type=bind,src="$PWD/artifacts/research/T-0189-S03/structural-final/result",dst=/input,readonly \
  --mount type=bind,src="$PWD/artifacts/research/T-0189/2026-09-28-memory-diagnostic",dst=/out \
  sha256:7a0db885c100695626175931d3e053ba6a1602d949167b83e2ef60888eea7169 \
  yosys -Q -T -l /out/opt.log \
  -p 'read_json /input/structural.json; opt; check -assert; write_json /out/optimized.json'
```

`check -assert` reports0 problems. Diagnostic outputs are local cooperative
artifacts, not signed attestations. Preserve source revision and hashes; do not
substitute a differently generated input. Input `structural.json` SHA256:
`56d8c39890ed09cad0e57ba71033cf5f531f70dabfdf3f6813b771fbc17a8568`.
Output `optimized.json`:
`74f9dd0487e8e085cf49e0760a09eb7f50745385407d4edceca8c4b1db30b78e`.
Raw `opt.log`:
`053bd164c27d8850e3cd1ed727601710bf1911f2a03331e29e92afcae7ca7e94`.
Scratchpad source SHA256:
`ce6be8a2d16811268dbaa3bdd5a758f78e4085242d31f68e6ac9fe58a3eec07f`.

Reproduce the structural attribution without interpreting it as utilization:

```python
import json
from collections import Counter
from pathlib import Path
p = Path("artifacts/research/T-0189/2026-09-28-memory-diagnostic/optimized.json")
m = json.loads(p.read_bytes())["modules"]["GraphDeviceBoardBridge"]
nets = [v["bits"] for n, v in m["netnames"].items()
        if n.startswith("core.core.scratchpad.storage_")]
assert len(nets) == 1024 and all(len(bits) == 32 for bits in nets)
storage = {bit for bits in nets for bit in bits}
assert all(type(bit) is int for bit in storage)
covered, drivers = set(), Counter()
for cell in m["cells"].values():
    if "dff" in cell["type"]:
        overlap = set(cell["connections"]["Q"]) & storage
        assert not (covered & overlap)
        covered |= overlap
        if overlap:
            drivers[cell["type"]] += len(overlap)
assert len(storage) == 32768 and covered == storage
assert drivers == {"$adffe": 32768}
assert not any(c["type"].startswith("$mem") for c in m["cells"].values())
print("storage attribution verified; FPGA mapping not measured")
```

## Next decision

T-0188/#194 actual Windows/tool inventory remains the next executable external
prerequisite. T-0189 vendor synthesis must inspect memory realization and
resource distribution before purchasing hardware or prioritizing a RAM rewrite.
This diagnosis makes that inspection concrete; it does not establish that the
existing design needs replacement. No duplicate implementation task is Ready.
If measured fit/resource pressure warrants the candidate, prepare its exact
interface/verification packet and new ADR before changing the backend.
