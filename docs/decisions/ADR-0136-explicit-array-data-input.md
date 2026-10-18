# ADR-0136: Explicit data preparation for existing array literals

Status: Proposed
Date: 2026-10-17
Task: T-0240 (local candidate; remote registration pending)
Context: ADR-0107, ADR-0132 through ADR-0135; EXP-0002 functional validation.
Authority: owner directs continued implementation toward usable local execution.

## Decision

Provide a pure Python `replace_literal(program, stage, slot, matrix, dtype='u32')`
helper and a matching `array-import` command for headerless integer CSV. Use the
existing source schema and compiler. This is input preparation, not a model
importer, new numeric execution mode, dependency rewrite or device change.

A matrix is a rectangular list of1..64 lists, each with1..64 Python integers.
Booleans, floats, strings and out-of-range integers are rejected. `u32` is the
default range0..2^32-1. Explicit `i32` accepts -2^31..2^31-1 and converts to uint32
bit patterns. Signed arithmetic still requires the existing explicit signed ops;
selecting the input encoding never changes an operator's semantics.

CSV is bounded to128 KiB, UTF-8 with optional BOM, comma separated, with no header
or blank rows. Quoted fields, CRLF and surrounding field whitespace are accepted.
Each field is an optional sign and1..10 ASCII decimal digits. No header, shape,
delimiter, floating-point, scientific-notation or base inference is performed.

Select an existing named stage and zero-based literal input slot. Producer-linked
slots cannot be replaced. The selected operand's dimensions follow the matrix;
output/computation shapes, views, fold extent and boundary mode stay unchanged.
Existing zero/clamp/wrap semantics apply when operand dimensions differ. The pure helper requires a structurally valid source; the CLI also admits the
original file first. Copy the source and run complete compiler admission on the
replacement before returning or publishing it. Neither route returns an unadmitted
replacement; the helper can repair a resource excess caused by literal dimensions.

The CLI requires a new output JSON filename in the same workspace inputs/ folder.
It never overwrites the source, another prepared file or a captured attempt. A
complete bounded temporary file is published with an exclusive atomic hard link;
interruption before publication cannot expose a partial final input. An interrupt
racing publication may leave a complete new output file. Cleanup removes only the
operation's own temporary inode. This is cooperative local filesystem behavior,
not hostile-host isolation, concurrent-editor transactionality or crash durability.

## Acceptance and scope

Require UT for dtype boundaries, CSV grammar and size, shapes, source immutability,
v1/v2 full admission, linked/unknown target rejection, resource failure, collisions,
path/symlink rejection and interruption on both sides of atomic publication. Verify
the CLI and relocated prepared launcher. Actual acceptance imports two GEMM operands,
runs them through unchanged QEMU/RTL, edits/imports again, verifies expected changed
cells and preserves original source/captured results. Saved reads must not execute.
No additional hardware, runtime install, array schema, opcode or performance claim.
