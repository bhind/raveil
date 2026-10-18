"""Portable local array workspaces over the unchanged verified coordinator."""
import csv
import io
import os
import sys
from pathlib import Path
import shutil
import subprocess

from . import project as p, project_fold as f, project_array as a
from . import project_dag_batch as b, array_program as compiler
from .fold_evidence import loads
from .workspace import NativeWorkspace

SCHEMA = 'raveil.array-environment/v1'
FOLDER = 'array-runtime'


def prepare(directory, kernel, build, source=None):
    """Snapshot explicitly selected artifacts into a fresh workspace; never replace."""
    directory = Path(directory).absolute()
    if ',' in str(directory):
        raise ValueError('array workspace path cannot contain a comma (QEMU/Docker mount syntax)')
    kernel = Path(kernel).absolute(); build = Path(build).absolute()
    kernel_bytes = f._bytes(kernel.parent, kernel.name)
    identity = f.verify_build(build, current=True)
    source = Path(source).absolute() if source else p.REPOSITORY/'examples/array-program/fused-stages.json'
    raw = NativeWorkspace(source.parent).read_text(source.name, maximum=b.INPUT_LIMIT).encode()
    compiled = compiler.compile(loads(raw))
    a._capture_budget(raw, compiled, kernel_bytes, build)
    project = p.Project(p.init_project(directory))
    root = project.root/FOLDER; project.workspace.mkdir(FOLDER, mode=0o700)
    p.write_new(root/'kernel.elf', kernel_bytes)
    p.tree(build, root/'runtime'); (root/'runtime/simulator.bin').chmod(0o700)
    if f.verify_build(root/'runtime', current=True) != identity:
        raise ValueError('runtime changed while preparing; keep this incomplete workspace and retry in a fresh directory')
    p.write_new(project.root/'inputs/program.json', raw)
    environment = dict(schema=SCHEMA, kernel_sha256=p.digest(kernel_bytes), build_sha256=identity)
    # Publish only after artifacts, source and guide are complete. No external path is stored.
    p.write_new(project.root/'ARRAY_README.md', GUIDE.encode())
    p.write_new(root/'environment.json', p.encoded(environment))
    backend(project)
    return dict(project=str(project.root), input='program.json', environment=environment,
                source_sha256=p.digest(raw), sessions=compiled['sessions'])


def backend(project):
    if FOLDER not in project.workspace.ls('/'):
        raise ValueError('no prepared array runtime; use project array-prepare or pass both --kernel and --build')
    project.workspace.stat(FOLDER)  # Reject symlink traversal through the project boundary.
    root = project.root/FOLDER
    value = loads(f._bytes(root, 'environment.json'))
    if type(value) is not dict or set(value) != {'schema', 'kernel_sha256', 'build_sha256'} or value['schema'] != SCHEMA:
        raise ValueError('invalid array environment manifest')
    if p.digest(f._bytes(root, 'kernel.elf')) != value['kernel_sha256']:
        raise ValueError('prepared array kernel identity differs')
    if f.verify_build(root/'runtime', current=True) != value['build_sha256']:
        raise ValueError('prepared array runtime identity differs')
    return root/'kernel.elf', root/'runtime'


def resolve(project, kernel=None, build=None):
    if (kernel is None) != (build is None):
        raise ValueError('pass both --kernel and --build, or omit both to use the prepared runtime')
    return (Path(kernel), Path(build)) if kernel is not None else backend(project)


def doctor(project):
    """Read-only checks; never pull an image, build, or launch the simulation."""
    checks = []
    def add(name, ok, detail):
        checks.append(dict(name=name, ok=bool(ok), detail=str(detail)[:1024]))
    add('python', sys.version_info >= (3, 11), sys.version.split()[0]+'; Python 3.11 or later required')
    add('platform', os.name == 'posix', 'POSIX workspace APIs required; native Windows is not supported')
    try:
        backend(project); add('prepared-runtime', True, 'kernel/runtime hashes and current RTL sources match')
    except (OSError, ValueError) as error:
        add('prepared-runtime', False, error)
    add('workspace-path', ',' not in str(project.root), 'QEMU/Docker paths must not contain commas')
    for name, arguments in (
        ('qemu-system-riscv64', ['--version']),
        ('docker', ['image', 'inspect', '--format', '{{.Id}}', f.IMAGE]),
    ):
        executable = shutil.which(name)
        if not executable:
            add(name, False, 'missing executable on PATH: '+name); continue
        try:
            result = subprocess.run([executable, *arguments], capture_output=True, text=True, timeout=15)
            ok = result.returncode == 0
            if name == 'docker': ok = ok and result.stdout.strip() == f.IMAGE
            add(name, ok, result.stdout.strip() if ok else
                'local runtime check failed; '+(result.stderr.strip() or result.stdout.strip()))
        except (OSError, subprocess.TimeoutExpired) as error:
            add(name, False, error)
    return dict(schema='raveil.array-doctor/v1', ready=all(c['ok'] for c in checks), checks=checks,
                evidence_class='local prerequisite inspection; no simulation or performance result')


def output(project, identity=None, name=None, format='json'):
    if format not in ('json', 'csv'):
        raise ValueError('output format must be json or csv')
    if identity is None:
        if 'arrays' not in project.workspace.ls('/') or not project.workspace.ls('arrays'):
            raise ValueError('no array attempts; run project array-run first')
        # Never hide a newer failed/unsealed attempt by falling back to older success.
        identities = project.workspace.ls('arrays')
        newest = max(p.name(item).split('-', 1)[0] for item in identities)
        candidates = [item for item in identities if item.split('-', 1)[0] == newest]
        if len(candidates) != 1:
            raise ValueError('multiple attempts share the latest timestamp; specify an explicit array ID')
        identity = candidates[0]
    record = a.load(project, identity)
    if record['status'] != 'succeeded':
        raise ValueError('array attempt is incomplete; no outputs are published')
    outputs = record['outputs']
    if name is not None:
        outputs = [item for item in outputs if item['name'] == name]
        if not outputs: raise ValueError('unknown output name: '+name)
    if format == 'json':
        return p.encoded(dict(id=identity, outputs=outputs)).decode()
    text = io.StringIO(newline=''); writer = csv.writer(text, lineterminator='\n')
    writer.writerow(['output', 'row', 'column', 'value'])
    for item in outputs:
        for index, word in enumerate(item['words']):
            writer.writerow([item['name'], index//item['columns'], index%item['columns'], word])
    return text.getvalue()


GUIDE = '''# Your prepared array workspace

The kernel and verified RTL runtime are copied into array-runtime/. Original
artifact paths are not needed. Keep array-runtime/ unchanged; edit inputs/program.json.
The existing QEMU executable, Docker daemon and pinned local image are still required.
No command here downloads or installs them. No physical accelerator is required.

From this directory, using the Raveil checkout's scripts/raveil launcher:

    raveil project array-doctor
    raveil project array-check
    raveil project array-run
    raveil project array-output
    raveil project array-output --format csv > result.csv
    raveil project arrays
    raveil project array-diff FIRST_ID SECOND_ID

Edit literals or the computation in inputs/program.json and run again. Every run
gets a fresh ID and keeps its original inputs. Output inspection verifies saved
proofs and does not run QEMU or Docker. Optional --name selects one named output.
Without an ID, array-output inspects the latest attempt, including failures; it
never silently displays an older success. If multiple attempts share the latest
timestamp, supply an explicit ID. CSV rows are output,row,column,value;
values retain the uint32 bit-pattern contract, including explicitly signed operations.

A failed or interrupted attempt must not be edited or reused. Inspect its record
with `raveil project arrays`; only sealed records accept `array ID`. Retry as a new run. Prepared runtime corruption
requires a fresh workspace via array-prepare; it is never silently repaired.
Move the whole workspace if needed. Avoid commas in paths (QEMU/Docker syntax).
This is functional QEMU emulation plus RTL simulation, not physical performance.
'''
