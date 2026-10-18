#!/usr/bin/env python3
"""Real edited-input/relocation acceptance for the prepared local application."""
import argparse
import csv
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from raveil import project as p, project_dag_batch as b
from scripts.prepare_array_app import prepare


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('output', 'kernel', 'build'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args(); root = args.output.absolute(); root.mkdir(parents=True, exist_ok=False)
    staging = root/'disposable originals'; staging.mkdir()
    shutil.copyfile(args.kernel, staging/'kernel.elf'); p.tree(args.build, staging/'runtime')
    app = root/'original app'; prepare(app, staging/'kernel.elf', staging/'runtime')
    environment = dict(os.environ, PYTHONPATH=''); sequence = 0

    def command(*arguments, code=0):
        nonlocal sequence
        sequence += 1; label = f'{sequence:02d}-'+arguments[0]
        argv = [str(app/'raveil'), *arguments]
        (root/(label+'.command.json')).write_bytes(p.encoded(dict(argv=argv,cwd=str(root))))
        result = subprocess.run(argv, cwd=root, env=environment, capture_output=True, text=True, timeout=300)
        (root/(label+'.stdout')).write_text(result.stdout); (root/(label+'.stderr')).write_text(result.stderr)
        assert result.returncode == code, (argv, result.returncode, result.stderr)
        print('PASS', label, flush=True)
        return result.stdout

    assert json.loads(command('array-doctor'))['ready']
    assert json.loads(command('array-check'))['sessions'] == 3
    first = json.loads(command('array-run'))
    expected1 = [dict(name='first',rows=2,columns=3,words=[23,24,25,26,27,28]),
                 dict(name='transpose',rows=3,columns=2,words=[23,26,24,27,25,28])]
    assert first['outputs'] == expected1 and first['status'] == 'succeeded'
    first_tree = p.tree(app/'workspace/arrays'/first['id'], max_bytes=b.MAX_BYTES, max_entries=b.MAX_ENTRIES)
    moved = root/'app with spaces'; app.rename(moved); app = moved
    shutil.rmtree(staging)  # Only disposable copies created above; original build evidence is retained.
    assert json.loads(command('array-output',first['id']))['outputs'] == expected1
    assert json.loads(command('array-doctor'))['ready']
    source = app/'workspace/inputs/program.json'; value = json.loads(source.read_text())
    value['stages'][0]['source']['inputs'][0]['words'][0] = 10
    source.write_bytes(p.encoded(value))
    second = json.loads(command('array-run'))
    expected2 = [dict(name='first',rows=2,columns=3,words=[33,24,25,26,27,28]),
                 dict(name='transpose',rows=3,columns=2,words=[33,26,24,27,25,28])]
    assert second['outputs'] == expected2 and second['status'] == 'succeeded'
    exported = json.loads(command('array-output')); assert exported['id'] == second['id'] and exported['outputs'] == expected2
    csv_rows = list(csv.DictReader(io.StringIO(command('array-output',second['id'],'--format','csv'))))
    assert [(r['output'],int(r['row']),int(r['column']),int(r['value'])) for r in csv_rows] == [
        (o['name'],i//o['columns'],i%o['columns'],word) for o in expected2 for i,word in enumerate(o['words'])]
    selected = json.loads(command('array-output',second['id'],'--name','transpose'))
    assert selected['outputs'] == [expected2[1]]
    difference = json.loads(command('array-diff',first['id'],second['id']))
    assert difference['changed_cells'] == 2
    assert p.tree(app/'workspace/arrays'/first['id'], max_bytes=b.MAX_BYTES, max_entries=b.MAX_ENTRIES) == first_tree
    before = sorted((app/'workspace/arrays').iterdir())
    good_source = source.read_bytes(); source.write_text('{"schema":null}')
    command('array-run',code=2); source.write_bytes(good_source)
    backend = app/'workspace/array-runtime'; unavailable = root/'temporarily unavailable runtime'
    backend.rename(unavailable)
    assert not json.loads(command('array-doctor',code=2))['ready']
    command('array-run',code=2)
    assert json.loads(command('array-output',first['id']))['outputs'] == expected1
    assert before == sorted((app/'workspace/arrays').iterdir())
    unavailable.rename(backend)
    final = root/'app'; app.rename(final); app = final
    assert json.loads(command('array-doctor'))['ready']
    assert json.loads(command('array-output',first['id']))['outputs'] == expected1
    # A separate process imports only the delivered engine. Inside it, saved reads
    # must not create any process at all; history/compare use the ordinary verifier.
    code = '''import sys,json
from pathlib import Path
from unittest.mock import patch
sys.dont_write_bytecode=True
sys.path.insert(0,sys.argv[1])
from raveil import project as p,project_array as a,project_array_workspace as w
assert p.REPOSITORY == Path(sys.argv[1]).resolve()
for name,module in tuple(sys.modules.items()):
 if name=='raveil' or name.startswith('raveil.'):
  assert Path(module.__file__).resolve().is_relative_to(p.REPOSITORY),name
project=p.Project(Path(sys.argv[2]))
with patch('subprocess.Popen',side_effect=AssertionError('saved reader executed')):
 assert len(a.history(project))==2
 for identity in sys.argv[3:]: assert json.loads(w.output(project,identity))['id']==identity
 assert a.compare(project,*sys.argv[3:])['changed_cells']==2
print('saved reads verified without process creation')
'''
    (root/'saved-read.py').write_text(code)
    saved_argv = [sys.executable, str(root/'saved-read.py'),str(app/'engine'),str(app/'workspace'),first['id'],second['id']]
    (root/'saved-read.command.json').write_bytes(p.encoded(saved_argv))
    checked = subprocess.run(saved_argv,cwd=root,env=environment,capture_output=True,text=True,timeout=180)
    (root/'saved-read.stdout').write_text(checked.stdout); (root/'saved-read.stderr').write_text(checked.stderr)
    assert checked.returncode == 0,checked.stderr
    manifest = json.loads((app/'app.json').read_text()); assert p.tree(app/'engine') == manifest['engine']
    summary = dict(evidence_class='actual QEMU emulation and RTL functional simulation',
                   app=str(app), first=first['id'],second=second['id'],published_words=24,changed_cells=2,
                   relocated=True,disposable_originals_removed=True,first_tree_preserved=True,
                   invalid_preflight_creates_no_attempt=True,saved_reads_no_process=True,engine_unchanged=True,
                   independent_expected=[expected1,expected2])
    (root/'summary.json').write_bytes(p.encoded(summary)); print('COMPLETE',json.dumps(summary),flush=True)


if __name__ == '__main__':
    main()
