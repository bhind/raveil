# ADR-0134: Prepared local array workspace

Status: Proposed
Date: 2026-10-17
Task: T-0238 (local provisional; live registration awaits GitHub authentication)
Context: ADR-0107, ADR-0132, ADR-0133; EXP-0002 functional evidence only

The owner directs finishing a usable simulation implementation without stopping
at the preceding compiler milestone. Primary is sole mutation owner. The active
GitHub token is still invalid; local implementation proceeds from the verified
T-0237 packet while canonical main and the dirty donor remain unchanged.

## Candidate contract

`array-prepare` validates an explicitly supplied kernel/runtime and initial source,
then creates a fresh or empty workspace, copies the artifacts to fixed relative
locations, verifies the copied runtime against current sources and publishes its
manifest last. The manifest has no external paths. Interrupted preparation remains
incomplete and is never repaired or overwritten automatically. Hashes establish
local integrity; kernel ABI compatibility requires actual execution evidence.

`array-run` accepts either both explicit kernel/build flags or neither. With
neither it verifies the prepared copies. Existing explicit flags and saved-proof
interpretation remain compatible. Check/run default to editable inputs/program.json.
`array-doctor` checks Python/POSIX support, copied identities and current RTL
sources, QEMU availability and the exact local Docker image with bounded read-only
commands. It does not install, download, build or execute the simulation. Ready
means prerequisites checked, not that application execution has been proven.

`array-output` validates the entire saved parent before emitting JSON or long-form
CSV (output,row,column,value) to stdout. It preserves uint32 words, suppresses
incomplete/unsealed/tampered output and can select one named result. An omitted ID
selects the latest timestamp; multiple attempts with that timestamp require an
explicit ID, avoiding arbitrary UUID ordering. It never falls back to older success.
No saved-reader subprocess or mutation is introduced.

## Verification and delivery

UT must cover snapshot relocation, source/backend tamper and symlinks, preparation
interruption, old explicit invocation, missing/timeout prerequisites, saved-only
JSON/CSV, failed/latest ambiguity and read-only behavior. Then prepare a fresh
local distribution/workspace, relocate it, remove its disposable original backend
copies, and run an edited source through QEMU/RTL using implicit backend selection.
Verify all outputs independently, compare the two runs and preserve old captures.
The app publishes app.json via a fully written pending file and an atomic
no-overwrite link. The launcher rejects malformed markers and disables bytecode
writes; ordinary usage leaves the packaged engine unchanged. Bundle the complete Python package and current-source RTL files with a relative
launcher; no research artifact path may be necessary for ordinary use. Existing
local QEMU/Docker prerequisites remain external; native Windows is not claimed.
No numeric/ISA change, hardware acquisition or performance claim is included.

## Local acceptance — 2026-10-17

324 distinct UT pass; a final 34-test subset verifies the last display-only CLI
change. Fresh kernel and offline RTL builds reproduce the preceding verified hashes.
Relocated actual use passes two runs/six sessions/six jobs, all approved, publishing
24 independently expected words. Editing the first input changes exactly two named
output cells. JSON/CSV/named output, diff, no-attempt preflight rejection, no-process
saved reads and full old-tree/engine preservation pass. The supplied disposable
original artifacts are removed before the second run; imported Raveil modules are
asserted to reside in the delivered engine. The whole original checkout was not
made unavailable. Local acceptance does not promote proposed research architecture
or establish universal runtime readiness. Remote registration/adoption awaits auth.
