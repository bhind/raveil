# Import array input data

Use a headerless CSV to fill an existing literal input without editing its JSON
words. The example below assumes a program with a stage named `answer` and two
literal matrix operands. Select a different stage/slot for your program.

```sh
cp -n engine/examples/array-program/import-gemm.json workspace/inputs/gemm.json
./raveil array-import --stage answer --slot 0 --csv A.csv --input gemm.json --output with-A.json
./raveil array-import --stage answer --slot 1 --csv B.csv --input with-A.json --output with-AB.json
./raveil array-check --input with-AB.json
./raveil array-run --input with-AB.json --timeout-seconds 300
./raveil array-output --format csv
```

`--slot` starts at zero. `--output` must be a new `.json` filename inside workspace
inputs/. Existing files are never overwritten. The original input and saved runs
remain unchanged. Use the printed new filename with `--input`; the default source
is not silently switched. Each import runs complete compiler admission and prints
source/CSV/result hashes. This preparation receipt is not execution evidence.

CSV contains1..64 rows and1..64 columns of decimal integers, separated by commas:

```csv
1,2,3
4,5,6
```

UTF-8 with optional BOM, CRLF, quoted numbers and surrounding whitespace work.
Headers, blank/ragged rows, empty cells, floats, exponent or hex notation do not.
The CSV limit is128 KiB and each number has at most10 decimal digits plus a sign.
Default `--dtype u32` accepts0..4294967295. Explicit `--dtype i32` accepts
-2147483648..2147483647 and encodes the same uint32 bit patterns used by the runtime.
It does not turn unsigned operators into signed ones.

Only a literal slot can be filled; a `{"from": "stage"}` dependency must remain a
producer link. The matrix sets the selected operand's dimensions. **It does not
reshape the computation or its outputs.** Existing view coordinates, fold extent
and zero/clamp/wrap boundary rules still apply. Inspect `array-check` and edit the
computation deliberately when changing its intended shape.

From a source checkout, use `scripts/raveil project array-import ... --project DIR`.
The CLI requires the original file to pass admission before replacement. The pure
helper below requires a structurally valid source and fully admits the replacement;
it can also prepare a previously unadmitted source whose resource excess is fixed
by changing literal dimensions. Neither route returns an unadmitted result.

Python callers can prepare data without file I/O:

```python
import json
from raveil.array_input import replace_literal

with open("program.json") as handle:
    program = json.load(handle)
prepared = replace_literal(program, "answer", 0, [[1, 2, 3], [4, 5, 6]])
# program is unchanged; prepared has passed full array compiler admission.
with open("with-A.json", "x") as handle:
    json.dump(prepared, handle)
```

The Python file-writing example uses ordinary exclusive creation, not the CLI's
atomic publication. The CLI rejects symlink inputs and publishes only a complete
new JSON. If interrupted, keep the source and inspect whether the selected output
exists: publication may already have completed. Never edit captured run folders.
See [ADR-0136](../decisions/ADR-0136-explicit-array-data-input.md) for the contract.
