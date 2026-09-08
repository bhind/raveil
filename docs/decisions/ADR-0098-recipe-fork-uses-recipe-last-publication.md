# ADR-0098: Recipe fork uses recipe-last publication

Status: Accepted
Date: 2026-09-08
Task: T-0178
Related: ADR-0085, ADR-0096

## Decision

The bounded `project fork SOURCE DESTINATION` operation preflights the admitted
source recipe, every referenced Graph descriptor/input byte and every confined
destination before writing. It creates copied Graph inputs with exclusive new
file creation, rewrites only the copied recipe's references, and creates the
destination recipe last. The recipe is the visibility commit marker because
project discovery starts in `recipes/`; an absent recipe cannot execute orphan
inputs.

If a caught write failure occurs, Raveil removes only destination files whose
device/inode identity matches a file newly created by that invocation. It never
removes the source, a pre-existing destination, a replaced path or a past run.
If safe cleanup cannot prove identity, it reports the retained paths and stops.

This is a cooperative single-user, single-writer operation. Do not run two fork
operations concurrently in one workspace, modify destinations while fork is
running, or use a synchronizing/shared directory as a concurrent mutation
surface. An operating-system crash or power loss can leave an orphan copied
input or a partial unavailable recipe. Before reusing that destination name,
inspect the named `recipes/` and `inputs/` paths; use a fresh destination when
ownership is uncertain. This is an operating constraint, not a filesystem
transaction, hostile-writer defense or sandbox.

## Alternatives and consequences

A single versioned bundle directory could use one directory rename as a
stronger publication boundary, but it changes the existing recipe/input schema,
workspace compatibility, Garden paths and run capture. A journal could support
crash recovery, but requires recovery ownership and lifecycle semantics far
beyond a small fork command. Copying only the recipe would be smaller but would
leave Graph variants sharing mutable descriptor/input files, defeating the
independent-editing outcome. Individual temporary-file renames still cannot
atomically commit entries across both existing directories.

Recipe-last publication therefore minimizes current product and migration
impact while preventing a caught failure from exposing an admitted incomplete
recipe. Its material limitation becomes medium-to-high if Raveil later supports
multi-user workspaces, daemon writers, synchronized storage, signed generation
or automatic crash recovery. Such a product change must select a bundle or
journal design in a superseding ADR.

## Acceptance

Test command and Graph recipe copies, rewritten independent references, source
and past-run byte preservation, existing destination, traversal, symlink and
missing-source rejection, and injected caught-failure cleanup. Demonstrate a
copied Graph edit affecting only the copy. The accepted demonstration runs the
source and edited copy through the same existing generic RTL simulator and
requires both outputs to match their descriptor oracle and C++ fallback. This
is RTL-simulation-functional evidence and creates no performance or silicon
claim.
