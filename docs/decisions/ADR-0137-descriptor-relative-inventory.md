# ADR-0137: Descriptor-relative bounded inventory traversal

Status: Proposed
Date: 2026-10-17
Task: T-0242 / Issue300 (local candidate; Project/PR integration pending)
Context: ADR-0107, ADR-0135; EXP-0013 completed image workflow; EXP-0014.
Authority: owner directs continued implementation toward usable local execution.

## Decision

Optimize the existing project tree inventory with descriptor-relative POSIX reads.
Open each directory once per traversal, reject symlinks and special files, and read
regular files through no-follow nonblocking descriptors with a total-budget-plus-one
bound. Preserve sorted virtual paths, empty directories,256 entries per directory,
4096-byte virtual paths, caller byte/entry bounds, root-only seal exclusion checks,
exclusive copy publication and cooperative cancellation. Unsupported platforms fail
explicitly; Native Windows remains outside the supported execution path. One open
descriptor is retained per active directory depth. OS descriptor exhaustion fails
closed and closes owned descriptors; unusually deep trees can reach this limit
sooner than the prior path walker. No unrestricted resource-parity claim is made.

Check the workspace root identity throughout traversal and at return. Compare
opened entries against their pre-open device/inode/type/size/mtime/ctime metadata,
then recheck metadata and the directory entry after reads/recursion. Check directory
metadata before/after enumeration and traversal. Ignore access time only. This
rejects observed replacement and content/namespace changes and adds bounded reads;
it is not an atomic snapshot or isolation from a hostile concurrent host. Changes
after an entry's final check remain possible under the existing cooperative model.

Keep every existing inventory invocation, nested semantic/trace/oracle validator,
seal check and before-publication verification. No memoization, persistent trust,
shared mutable verification results or schema changes. Destination copy failures
continue to leave an unsealed partial tree, never a claimed valid capture.

## Acceptance

Exact manifest/copy parity; empty directories; root/nested symlinks and special
files; entry, directory, byte and path bounds; root-only exclusions; file growth,
file/ancestor/root replacement and cancellation; descriptor cleanup on errors.
Rerun affected project/workspace/compiler/control UT, revalidate prior image
captures without processes, and execute fresh unchanged images with both versions.
Host wall time remains separate from RTL simulated cycles and physical hardware.
