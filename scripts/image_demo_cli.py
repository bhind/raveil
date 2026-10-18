#!/usr/bin/env python3
"""Prepare, run and view the existing integer image pipeline."""
import argparse
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
if (root/'app/engine').is_dir():
    sys.path.insert(0, str(root/'app/engine'))
from raveil import project as p, project_array as a, project_fold as f
from raveil import project_array_workspace as workspace, run_control
from scripts.image_demo import source, read_pgm, reference
from scripts.image_demo_report import pixels


def read_image(path):
    """Read at most the admitted P5 bound; reject links and special files."""
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as handle:
        info = os.fstat(handle.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_size > 8192:
            raise ValueError('PGM must be a regular file of at most8192 bytes')
        raw = handle.read(8193)
    if len(raw) > 8192:
        raise ValueError('PGM too large')
    return read_pgm(raw)


def publish(path, raw):
    """Expose a complete file exclusively; never replace an earlier result."""
    path = Path(path)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.image-pending-', delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(raw)
        os.link(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink()


def view(project, identity, output):
    record = a.load(project, identity)
    if record['status'] != 'succeeded':
        raise ValueError('result is incomplete')
    value = json.loads((project.root/'arrays'/record['id']/'source.json').read_bytes())
    operand = value['stages'][0]['source']['inputs'][0]
    width, height = operand['columns'], operand['rows']
    image = [operand['words'][r*width:(r+1)*width] for r in range(height)]
    if (value != source(image, value['schema'] == 'raveil.array-program/v2') or
            record['outputs'] != reference(image)):
        raise ValueError('saved program is not the specified image pipeline')
    figures = [('入力', image)]
    for item in record['outputs']:
        if item['name'] == 'gradient':
            continue
        figures.append((item['name'], [item['words'][r*item['columns']:(r+1)*item['columns']]
                                      for r in range(item['rows'])]))
    page = ('<!doctype html><html lang="ja"><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>Raveil image result</title><style>body{font-family:system-ui;'
            'max-width:960px;margin:40px auto;padding:16px}section{display:flex;'
            'flex-wrap:wrap;gap:24px}figure{flex:1;min-width:160px;margin:0}'
            'svg{width:100%;image-rendering:pixelated}</style>'
            '<h1>検証済みの画像処理結果</h1><p>保存済みQEMU／RTL出力。'
            'この表示のための新しい実行は行っていません。</p><section>')
    page += ''.join('<figure>'+pixels(matrix)+'<figcaption>'+name+'</figcaption></figure>'
                    for name, matrix in figures) + '</section></html>'
    publish(output, page.encode())
    return record


def package(output, image, kernel, build):
    from scripts.prepare_array_app import prepare
    output = Path(output).absolute()
    if ',' in str(output):
        raise ValueError('application path cannot contain a comma')
    value = source(read_image(image))
    # Fail missing/invalid artifacts before reserving the new destination.
    f._bytes(Path(kernel).absolute().parent, Path(kernel).name)
    f.verify_build(Path(build).absolute(), current=True)
    run_control.checkpoint()
    output.mkdir(parents=True, mode=0o700, exist_ok=False)
    p.write_new(output/'program.json', p.encoded(value))
    prepare(output/'app', kernel, build, output/'program.json')
    helpers = output/'scripts'
    helpers.mkdir(mode=0o700)
    p.write_new(helpers/'__init__.py', b'')
    for name in ('image_demo_cli.py', 'image_demo.py', 'image_demo_report.py', 'prepare_array_app.py'):
        p.write_new(helpers/name, f._bytes(Path(__file__).resolve().parent, name))
    guide = root/'docs/guides/IMAGE_DEMO.md'
    if not guide.is_file():
        guide = root/'IMAGE_GUIDE.md'
    guide_text = f._bytes(guide.parent, guide.name).decode()
    guide_text = guide_text.replace('(ARRAY_WORKSPACE.md)', '(app/engine/docs/guides/ARRAY_WORKSPACE.md)')
    guide_text = guide_text.replace('(../experiments/EXP-0013-image-fusion-comparison.md)',
                                    '(https://github.com/bhind/raveil/blob/main/docs/experiments/EXP-0013-image-fusion-comparison.md)')
    p.write_new(output/'IMAGE_GUIDE.md', guide_text.encode())
    p.write_new(output/'START_HERE.md', b'''# Raveil image workspace

Open report.html after a successful run. It shows verified QEMU/RTL outputs.
From this folder, prepare an edited PGM and run the existing portable app:

    python3 -B scripts/image_demo_cli.py prepare --image edited.pgm --output app/workspace/inputs/edited.json
    ./app/raveil array-run --input edited.json --timeout-seconds 900
    python3 -B scripts/image_demo_cli.py view --project app/workspace --id PRINTED_RUN_ID --output edited.html

Keep earlier inputs and attempts unchanged. Choose fresh input/report names.
The entire folder can move. Python, QEMU, Docker and the exact local image are
still required; nothing is downloaded. See IMAGE_GUIDE.md for one-command runs.
A failed/interrupted preparation or execution retains its folder for diagnosis;
retry the run command with a fresh destination. No report means no report was
published, not necessarily that the underlying array attempt failed: inspect
./app/raveil arrays and retry view with a successfully verified explicit ID.
''')
    return output


def run(args, control):
    with control.active(signals=True):
        directory = package(args.output, args.image, args.kernel, args.build)
        project = p.Project(directory/'app/workspace')
        kernel, build = workspace.backend(project)
        record = a.run(project, 'program.json', kernel, build)
        if record['status'] != 'succeeded':
            raise ValueError('array result is incomplete; no image report published')
        # The parent is committed before presentation. Never reset that boundary:
        # a report failure preserves the successful run for a separate view retry.
        view(project, record['id'], directory/'report.html')
    return dict(directory=str(directory), id=record['id'], report=str(directory/'report.html'),
                evidence_class=record['evidence_class'])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    prepare = commands.add_parser('prepare')
    prepare.add_argument('--image', type=Path, required=True)
    prepare.add_argument('--output', type=Path, required=True)
    show = commands.add_parser('view')
    show.add_argument('--project', type=Path, required=True)
    show.add_argument('--id', required=True)
    show.add_argument('--output', type=Path, required=True)
    execute = commands.add_parser('run', help='prepare a fresh portable app, execute, verify and render')
    execute.add_argument('--image', type=Path, required=True)
    execute.add_argument('--output', type=Path, required=True)
    execute.add_argument('--kernel', type=Path, required=True)
    execute.add_argument('--build', type=Path, required=True)
    execute.add_argument('--timeout-seconds', type=float, default=900)
    args = parser.parse_args(argv)
    control = None
    try:
        if args.command == 'prepare':
            publish(args.output, p.encoded(source(read_image(args.image))))
        elif args.command == 'view':
            view(p.Project(args.project), args.id, args.output)
        else:
            control = run_control.Control(args.timeout_seconds, sys.stderr)
            print(p.encoded(run(args, control)).decode(), end='')
            return 0
        print(str(args.output))
        return 0
    except run_control.Stopped as error:
        print(json.dumps(control.diagnostic(error)), file=sys.stderr)
        return error.code
    except KeyboardInterrupt:
        print('Interrupted; keep captured attempts and retry with a fresh output path.', file=sys.stderr)
        return 130
    except (OSError, RuntimeError, ValueError, KeyError, IndexError, subprocess.SubprocessError) as error:
        if control is not None:
            diagnostic = control.diagnostic(error)
            diagnostic['array_committed'] = control.committed
            diagnostic['status'] = 'report-failed' if control.committed else 'failed'
            diagnostic['recovery'] = ('Inspect the explicit attempt ID; a successful saved array can be viewed again. '
                                      'Keep captures unchanged and use a fresh destination for another run.')
            print(json.dumps(diagnostic), file=sys.stderr)
        else:
            print(str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
