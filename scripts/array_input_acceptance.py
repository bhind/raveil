#!/usr/bin/env python3
"""Actual CSV matrix import/edit/GEMM acceptance on the unchanged QEMU/RTL path."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from raveil import project as p,project_array as a,project_array_workspace as w,project_dag_batch as b
from scripts.prepare_array_app import prepare
from scripts.array_control_acceptance import inspect_resources


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('output','kernel','build'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();root=args.output.absolute();root.mkdir(parents=True,exist_ok=False)
    app=root/'initial app';prepare(app,args.kernel,args.build);sequence=0
    def command(*arguments,code=0):
        nonlocal sequence
        sequence+=1;label=f'{sequence:02d}-'+arguments[0];argv=[str(app/'raveil'),*arguments]
        (root/(label+'.command.json')).write_bytes(p.encoded(dict(argv=argv,cwd=str(root))))
        result=subprocess.run(argv,cwd=root,capture_output=True,text=True,timeout=300)
        (root/(label+'.stdout')).write_text(result.stdout);(root/(label+'.stderr')).write_text(result.stderr)
        assert result.returncode==code,(argv,result.returncode,result.stderr)
        assert 'Traceback' not in result.stderr
        print('PASS',label,'exit',code,flush=True)
        return json.loads(result.stdout) if result.stdout else None
    def tree(path):return p.tree(path,max_bytes=b.MAX_BYTES,max_entries=b.MAX_ENTRIES)
    assert command('array-doctor')['ready']
    baseline=command('array-run','--timeout-seconds','300')
    assert baseline['outputs']==[dict(name='first',rows=2,columns=3,words=[23,24,25,26,27,28]),dict(name='transpose',rows=3,columns=2,words=[23,26,24,27,25,28])]
    workspace=app/'workspace';default=(workspace/'inputs/program.json').read_bytes()
    old_tree=tree(workspace/'arrays'/baseline['id'])
    p.write_new(workspace/'inputs/gemm.json',(p.REPOSITORY/'examples/array-program/import-gemm.json').read_bytes())
    original=(workspace/'inputs/gemm.json').read_bytes();data=app/'data';data.mkdir()
    for name,raw in [('A.csv',b'\xef\xbb\xbf1,2,3\r\n4,5,6\r\n'),('B.csv',b'7,8\n9,10\n11,12\n'),
                     ('A-edited.csv',b'2,2,3\n4,5,6\n'),('A-signed.csv',b'-1,2,3\n4,5,6\n'),('bad.csv',b'1,2\n3\n')]:
        p.write_new(data/name,raw)
    def imported(csv,source,target,slot,dtype='u32'):
        receipt=command('array-import','--stage','answer','--slot',str(slot),'--csv',str(data/csv),
                        '--input',source,'--output',target,'--dtype',dtype)
        assert receipt['csv_sha256']==p.digest((data/csv).read_bytes())
        assert receipt['output_sha256']==p.digest((workspace/'inputs'/target).read_bytes())
        return receipt
    receipts=[imported('A.csv','gemm.json','with-A.json',0),imported('B.csv','with-A.json','with-AB.json',1)]
    first=command('array-run','--input','with-AB.json','--timeout-seconds','300')
    expected=lambda words:[dict(name='answer',rows=2,columns=2,words=words)]
    assert first['outputs']==expected([58,64,139,154])
    first_tree=tree(workspace/'arrays'/first['id']);prepared=(workspace/'inputs/with-AB.json').read_bytes()
    moved=root/'app with spaces';app.rename(moved);app=moved;workspace=app/'workspace';data=app/'data'
    receipts.append(imported('A-edited.csv','with-AB.json','edited.json',0))
    second=command('array-run','--input','edited.json','--timeout-seconds','300')
    assert second['outputs']==expected([65,72,139,154])
    assert command('array-diff',first['id'],second['id'])['changed_cells']==2
    receipts.append(imported('A-signed.csv','with-AB.json','signed.json',0,'i32'))
    third=command('array-run','--input','signed.json','--timeout-seconds','300')
    assert third['outputs']==expected([44,48,139,154])
    before=tree(workspace)
    command('array-import','--stage','answer','--slot','0','--csv',str(data/'bad.csv'),'--input','gemm.json','--output','bad.json',code=2)
    command('array-import','--stage','transpose','--slot','0','--csv',str(data/'A.csv'),'--output','linked.json',code=2)
    command('array-import','--stage','first','--slot','0','--csv',str(data/'A.csv'),'--output','program.json',code=2)
    assert tree(workspace)==before
    assert (workspace/'inputs/program.json').read_bytes()==default
    assert (workspace/'inputs/gemm.json').read_bytes()==original
    assert (workspace/'inputs/with-AB.json').read_bytes()==prepared
    assert tree(workspace/'arrays'/first['id'])==first_tree
    assert tree(workspace/'arrays'/baseline['id'])==old_tree
    final=root/'app';app.rename(final);app=final;workspace=app/'workspace'
    project=p.Project(workspace)
    with patch('subprocess.Popen',side_effect=AssertionError('saved read executed')):
        assert len(a.history(project))==4
        for record in (baseline,first,second,third):assert a.load(project,record['id'])['outputs']==record['outputs']
        assert a.compare(project,first['id'],third['id'])['changed_cells']==2
        assert json.loads(w.output(project))['id']==third['id']
    resources=inspect_resources(workspace)
    # Also inspect the old execution prefixes after relocation.
    for prior in (root/'initial app/workspace',root/'app with spaces/workspace'):
        checked=inspect_resources(prior);assert not checked['containers'] and not checked['qemu']
        resources['queries'].extend(checked['queries'])
    assert not resources['containers'] and not resources['qemu']
    (root/'resources.json').write_bytes(p.encoded(resources))
    assert p.tree(app/'engine')==json.loads((app/'app.json').read_bytes())['engine']
    result=dict(evidence_class='actual QEMU emulation and RTL functional simulation',app=str(app),
                imports=receipts,records=[record['id'] for record in (baseline,first,second,third)],
                published_words=24,gemm_outputs=[row['outputs'] for row in (first,second,third)],changed_cells=2,
                source_and_prepared_inputs_preserved=True,prior_trees_preserved=True,saved_without_execution=True)
    (root/'summary.json').write_bytes(p.encoded(result));print('PASS complete',flush=True)
    return 0

if __name__=='__main__':raise SystemExit(main())
