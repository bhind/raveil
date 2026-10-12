# ADR-0126: finite uniform tile advice through existing admission

Status: Proposed
Date: 2026-10-11
Task: T-0224
Context: ADR-0107; Proposed ADR-0124/ADR-0125

## Concrete obstacle

The existing matrix source builder defaults to 8x8 output tiles. Multiplying
17x64 by 64x19 then exceeds the 324-word packed-input bound, although 5x5 tiles
fit in exactly 16 independent sessions. Requiring users to discover that legal
partition by trial and error is an unnecessary source-interface restriction.

## Local design

`grid-plan --input SOURCE.json` is host-only advice. It checks the original source
schema and scalar tile bounds, then enumerates every row/column tile size 1..16.
The requested partition may fail capacity or tile-count admission; other source
fields are never repaired. Every candidate goes through the unchanged full grid
compiler, MF01 program validation and DAG resource admission. A malformed program
or a source without an admitted uniform partition yields no executable proposal.

Rank admitted candidates lexicographically by actual number of coupled sessions,
sum of packed input words across all tiles, nominal tile area, nominal rows and
columns. The final three fields only break ties deterministically. These static
counts are not a latency/energy model and do not claim the fastest hardware plan.
Search is finite: 256 candidates, each retaining all existing bounds.

The advisory result contains input and selected-source hashes, the requested tile,
search/admission counts, rejection counts, selected tile/costs and ordinary source
JSON with only `tile` changed. It is not an execution record or authority token.
No new source schema, opcode, guest capability, object slot or RTL is introduced.

## Workspace behavior

Preview reads one bounded source and writes nothing and starts no executor.
`--output SELECTED.json` explicitly saves the selected source as a new input file;
path traversal, symlink inputs and existing outputs are rejected. Source JSON is
strictly parsed and selected output is bounded by the existing 4 MiB input cap.
No input is overwritten and no grid attempt is allocated by planning.

Users execute the selected ordinary source with existing grid-run. It undergoes
all source/contract/resource/semantic/proof checks again; altering advisory hashes
or metadata cannot bypass them because the executor never consumes that advice.
The saved grid parent freezes the selected explicit source in the existing way.
The advisory input hash retains the original request for review, without adding
new authority to the original or selected partition choice.

## Limits and evidence

This searches uniform rectangles within the current bounds. It does not perform
nonuniform graph partitioning, reduction splitting, sparse packing, learned
scheduling or cross-session object transfer. Enumeration and tile selection are
known methods and no novelty or Groq advantage is claimed. Exact host and coupled
functional evidence belongs in STATUS/log; no physical performance experiment,
gate, hardware budget or public-adoption decision is made here.
