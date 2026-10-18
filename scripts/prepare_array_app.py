#!/usr/bin/env python3
"""Create a fresh relocatable local array application from explicit artifacts."""
import argparse
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from raveil import project as p, project_fold as f, project_array_workspace as w


LAUNCHER = '''#!/usr/bin/env python3
"""Run this prepared workspace using the adjacent engine, from any directory."""
from pathlib import Path
import sys
root = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
import json
marker = root/'app.json'
if marker.is_symlink() or not marker.is_file() or marker.stat().st_size > 4*1024*1024:
    raise SystemExit('Incomplete application preparation; create a fresh application directory.')
try:
    manifest = json.loads(marker.read_text())
    if (type(manifest) is not dict or manifest.get('schema') != 'raveil.local-array-app/v1' or
        set(manifest) != {'schema','engine','environment','initial_source_sha256','launcher_sha256','evidence_class'}):
        raise ValueError('invalid marker')
except (OSError, ValueError):
    raise SystemExit('Invalid application marker; create a fresh application directory.')
allowed = {'array-doctor', 'array-check', 'array-run', 'array-output', 'array', 'arrays', 'array-diff', 'array-import'}
if not sys.argv[1:] or sys.argv[1] in {'-h', '--help'}:
    print('Raveil local arrays: ./raveil ACTION [options]')
    print('Actions: '+', '.join(sorted(allowed)))
    print('Edit workspace/inputs/program.json; then array-check, array-run, array-output.')
    raise SystemExit(0)
if sys.argv[1] not in allowed:
    raise SystemExit('Use one of: '+', '.join(sorted(allowed)))
sys.path.insert(0, str(root/'engine'))
from raveil.cli import main
arguments = sys.argv[1:]
if arguments[0] == 'array-run': arguments = [*arguments, '--summary', '--progress']
raise SystemExit(main(['project', *arguments, '--project', str(root/'workspace')]))
'''


README = '''# Raveil local arrays

This folder is a ready local simulation workspace. Run from here:

    ./raveil array-doctor
    ./raveil array-check
    ./raveil array-run --timeout-seconds 300
    ./raveil array-output
    ./raveil array-output --format csv > result.csv
    ./raveil arrays

Import headerless integer CSV into a named literal input without changing the source:

    ./raveil array-import --stage first --slot 0 --csv data.csv --output data.json
    ./raveil array-run --input data.json

The matrix changes that operand's shape/data; computation shape and views remain
unchanged. Use --dtype i32 explicitly for signed decimal values. See the input
preparation guide in engine/docs/guides/ARRAY_INPUT.md for CSV and Python examples.

Edit workspace/inputs/program.json, run again and compare the printed IDs:

    ./raveil array-diff FIRST_ID SECOND_ID

Use `./raveil array-output ID --name OUTPUT` for a selected saved output. All
outputs are verified before display. A failure or interruption publishes none.
Retry starts a fresh attempt; keep the previous captured directories unchanged.
An ambiguous latest timestamp requires an explicit ID, not an arbitrary choice.
Progress is printed to stderr. Optional --timeout-seconds limits the whole run;
Ctrl+C requests a stop. Exit 130 means interrupted, 143 terminated, 124 timed out,
and 2 a failure. Cleanup may continue after the deadline. Stop diagnostics identify
the preserved attempt. Before atomic result publication a stop publishes no output;
a stop racing the final commit can find already completed work. Use `arrays` to
inspect attempt status, then run again. Do not edit failed captured directories.

The entire folder can move, including across paths containing spaces. The launcher
works from any current directory. No previous checkout or research-artifact path
is needed. Avoid commas in paths, as required by QEMU/Docker mount syntax.
External prerequisites are Python >=3.11 on POSIX, qemu-system-riscv64, Docker and
the exact already-local runtime image reported by array-doctor. This folder does
not install or download them. Doctor is a prerequisite check, not an execution test.
Native Windows is not supported; the accepted environment is macOS with existing
QEMU/Docker. The owned integer-array compiler/runtime is included under engine/.
app.json records the prepared engine inventory; it is provenance, not a signature.

Arithmetic uses uint32 words with explicit signed operations; shapes are at most
64x64 with additional whole-program admission bounds. This is functional QEMU/RTL
simulation. Floating point, arbitrary model import, FPGA performance and Groq
superiority are not claimed. See ARRAY_GUIDE.md and workspace/ARRAY_README.md.
'''


def prepare(output, kernel, build, source=None):
    output = Path(output).absolute()
    if ',' in str(output): raise ValueError('application path cannot contain a comma')
    output.mkdir(parents=True, mode=0o700, exist_ok=False)
    engine = output/'engine'; engine.mkdir(mode=0o700)
    files = sorted(p.REPOSITORY.joinpath('raveil').rglob('*.py'))
    files += [p.REPOSITORY/'hardware/chisel'/name for name in f.SOURCES]
    files += sorted((p.REPOSITORY/'examples/array-program').glob('*.json'))
    files += [p.REPOSITORY/'LICENSE']
    files += sorted((p.REPOSITORY/'docs/guides').glob('ARRAY_*.md'))
    files += [p.REPOSITORY/'docs/guides/GENERALIZATION_COMPLETION.md']
    files += [p.REPOSITORY/'docs/decisions'/name for name in (
        'ADR-0132-materialized-array-program.md', 'ADR-0133-admitted-array-fusion.md',
        'ADR-0134-prepared-array-workspace.md', 'ADR-0135-foreground-array-run-control.md',
        'ADR-0136-explicit-array-data-input.md',
        'ADR-0137-descriptor-relative-inventory.md')]
    total = 0
    for path in files:
        raw = f._bytes(path.parent, path.name); total += len(raw)
        if total > p.MAX_BYTES or len(files) > p.MAX_ENTRIES:
            raise ValueError('application source inventory exceeds bound')
        destination = engine/path.relative_to(p.REPOSITORY)
        destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        p.write_new(destination, raw)
    prepared = w.prepare(output/'workspace', kernel, build, source)
    for name in f.SOURCES:
        if (engine/'hardware/chisel'/name).read_bytes() != (output/'workspace'/w.FOLDER/'runtime/source'/name).read_bytes():
            raise ValueError('copied engine and runtime sources differ')
    p.write_new(output/'raveil', LAUNCHER.encode()); (output/'raveil').chmod(0o700)
    p.write_new(output/'README.md', README.encode())
    guide = (p.REPOSITORY/'docs/guides/ARRAY_FUSION.md').read_text()
    guide = guide.replace('(../decisions/', '(engine/docs/decisions/').replace('(ARRAY_PROGRAM.md)', '(engine/docs/guides/ARRAY_PROGRAM.md)')
    p.write_new(output/'ARRAY_GUIDE.md', guide.encode())
    manifest = dict(schema='raveil.local-array-app/v1', engine=p.tree(engine),
                    environment=prepared['environment'], initial_source_sha256=prepared['source_sha256'],
                    launcher_sha256=p.digest(LAUNCHER.encode()), evidence_class='local preparation; execution not yet tested')
    pending = output/'.app.pending'
    p.write_new(pending, p.encoded(manifest))
    os.link(pending, output/'app.json')
    pending.unlink()
    return dict(directory=str(output), launcher=str(output/'raveil'), **manifest)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--kernel', type=Path, required=True)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--source', type=Path)
    args = parser.parse_args(argv)
    try:
        result = prepare(args.output, args.kernel, args.build, args.source)
    except (OSError, ValueError) as error:
        parser.exit(2, 'error: '+str(error)+'\n')
    print(p.encoded({key: result[key] for key in ('directory', 'launcher', 'environment', 'evidence_class')}).decode(), end='')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
