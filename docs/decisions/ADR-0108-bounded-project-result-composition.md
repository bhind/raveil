# ADR-0108: Publish a bounded named result set only after all children pass

Status: Accepted
Date: 2026-10-10
Task: T-0197 / Issue266
Authority: owner directs continuous implementation under ADR-0107; T-0183
accepted planning selects host composition over new hardware STORE effects.

## Decision

Add an explicit `project compose --input FILE --output NAME=RECIPE` command
(one or two ordered outputs), separate from ordinary `project run`. FILE is
one existing project inputs JSON containing324 uint32 words. It explicitly
replaces each selected recipe's seed/input choice for this composition only.
Compile both captured descriptors and validate names/input before child launch.
Names follow ASCII `[a-z][a-z0-9_-]{0,30}`, are unique values and never paths.

Capture input and both recipe/descriptor identities once, with bounded bytes.
Save an append-only parent plan under a fresh `compositions/ID`. Each numeric
child slot contains a private minimal project with the same frozen input and
its captured descriptor; invoke the existing Project.run rtl-sim path without
changing its admission, oracle, fallback or RTL implementation. This duplicates
execution and input storage; it neither shares arithmetic nor claims speedup.

Store child run IDs and input/descriptor/output/record hashes. Parent success
requires all child validations and saved-artifact checks, plus revalidation of
all snapshots before publication. Failed/cancelled attempts retain valid earlier
child evidence and an incomplete parent. Retry always allocates a fresh ID.
No two-STORE, resource-capacity, ABI or QEMU-to-RTL change is introduced.

## Publication and observation

One/two outputs only; zero, excess, duplicate or unsafe names fail before any
child run. Input is explicit and frozen once; source edits after capture do not
change either child. SIGINT/KeyboardInterrupt and cooperative cancellation
before/between/after children yield incomplete attempts. An abrupt process kill
can leave a directory with no sealed parent; history labels it incomplete.

Write the sealed record checksum and pending record privately, check cancellation,
then atomically create the final record with a no-overwrite hard link. This is
the parent publication point. A cancellation after that point does not revoke
an already-published result. An interrupted seal without a final record is not
complete. Retained pending seal bytes are not part of output authority.

A separate composition history/inspection path rechecks hashes, frozen inputs,
child records and oracle results. It renders named output only for a complete
parent. Existing run/history/Garden remains single-child functionality; a child
view must not be interpreted as parent completeness. Do not add parent records
to ordinary run history under an ambiguous success label.

The storage model remains cooperative local integrity, not signed attestation,
hostile concurrent-writer isolation or crash durability across power loss.
Cap initial input/descriptor capture at4MiB to leave room for duplicated child
snapshots within the existing16MiB artifact-tree budget; retain
existing path/symlink and exclusive-write checks. Internal paths use numeric
slots, not output labels. Existing single-output CLI behavior remains unchanged.

## Acceptance

Host fault-injection covers malformed plans/names, changed live sources,
changed saved artifacts/receipts, second-child failure, cancellation at each
publication boundary, retained evidence, fresh retry and output-read integrity.
Actual cached Chisel/Verilator execution must produce raw x*x and biased
x*x+17 modulo2^32 from one frozen input; both match independent scalar results,
existing oracle and C++ fallback, with inactive output words zero. Separate host
fixtures from this actual RTL evidence. Record exact tool/source identities.
