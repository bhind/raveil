#!/usr/bin/env python3
"""Additional real-backend boundary checks, isolated from the positive campaign."""
import argparse,copy,json,subprocess,sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from raveil import project as p,project_array as a,project_fold as f,project_dag_batch as b,fold_dag as d
from scripts.array_program_cases import literal,view,load,src,program,output
from scripts.array_program_acceptance import counts


def cases():
    words=[0xffffffff,0x80000000,7];rhs=[1,0x7fffffff,11]
    s=src(1,3,words);s['inputs'].append(literal(1,3,rhs));s['kernel']['views']['w']=view(1)
    s['kernel'].update(nodes=[load(),load('y','w'),dict(id='z',op='max',args=['x','y'])],result='z')
    yield 'unsigned-map-max',program(s),[output('answer',1,3,[max(x,y) for x,y in zip(words,rhs)])]
    s=src(1,1,[17]);s['shape']=[64,64];s['kernel']['views']['v']=view(row=(0,0),column=(0,0))
    yield 'maximum-shape-broadcast',program(s),[output('answer',64,64,[17]*4096)]
    stages=[]
    for i in range(8):
        s=src(1,2,[3,5]);s['inputs']=[{'from':f's{i-1}'}] if i else s['inputs']
        stages.append(dict(name=f's{i}',source=s))
    yield 'eight-stage-eight-output',dict(schema=a.array.SCHEMA,stages=list(reversed(stages)),outputs=[f's{i}' for i in range(8)]),[output(f's{i}',1,2,[3,5]) for i in range(8)]
    s=src(1,2,[0,0]);s['inputs']=[literal(1,2,[i,2*i]) for i in range(8)];s['kernel']['views']={f'v{i}':view(i) for i in range(8)}
    nodes=[load(f'n{i}',f'v{i}') for i in range(8)];previous='n0'
    for i in range(1,8):
        name=f'z{i}';nodes.append(dict(id=name,op='add',args=[previous,f'n{i}']));previous=name
    s['kernel'].update(nodes=nodes,result=previous)
    yield 'eight-inputs',program(s),[output('answer',1,2,[28,56])]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ['output','kernel','build']:parser.add_argument('--'+key,type=Path,required=True)
    args=parser.parse_args();root=args.output.absolute();root.mkdir(parents=True,exist_ok=False)
    project=p.Project(p.init_project(root/'workspace'));rows=[]
    for name,value,expected in cases():
        p.write_new(project.root/'inputs'/f'{name}.json',p.encoded(value))
        command=[sys.executable,'-m','raveil','project','array-run','--project',str(project.root),'--input',name+'.json','--kernel',str(args.kernel),'--build',str(args.build)]
        (root/(name+'.command.json')).write_bytes(p.encoded(command));result=subprocess.run(command,capture_output=True)
        (root/(name+'.stdout')).write_bytes(result.stdout);(root/(name+'.stderr')).write_bytes(result.stderr)
        assert result.returncode==0,(name,result.stderr.decode(errors='replace'))
        record=json.loads(result.stdout);assert record['outputs']==expected
        row=dict(name=name,id=record['id'],words=sum(len(o['words']) for o in expected),**counts(project,record));rows.append(row)
        print('PASS',name,row['sessions'],row['words'],flush=True)
    # Real device cancellation is intentionally not a normal protocol option.
    # The saved options mismatch must fail closed at the coupled boundary.
    value=program(src(1,3,[1,2,3],[load(),dict(id='z',op='add_imm',args=['x'],imm=2)]))
    p.write_new(project.root/'inputs/cancel.json',p.encoded(value));before=set(project.workspace.ls('arrays'));run=f.run;cancelled=[]
    def cancel(*args,**kwargs):
        kwargs['cancel_after']=1;record=run(*args,**kwargs);cancelled.append((args[0],record));return record
    with patch.object(f,'run',side_effect=cancel):
        try:a.run(project,'cancel.json',args.kernel,args.build)
        except ValueError as exc:assert 'execution options changed' in str(exc)
        else:raise AssertionError('changed cancellation options were admitted')
    identity=(set(project.workspace.ls('arrays'))-before).pop();failed_root=project.root/'arrays'/identity
    assert not (failed_root/'record.json').exists() and len(cancelled)==1
    cp,record=cancelled[0];verified=f.load(cp,record['id']);assert verified['status']=='incomplete' and verified['output'] is None
    device=json.loads((cp.root/'folds'/record['id']/'device/device.json').read_text());assert device['cancelled']==1
    preserved=p.tree(failed_root,max_bytes=b.MAX_BYTES,max_entries=b.MAX_ENTRIES);retry=a.run(project,'cancel.json',args.kernel,args.build)
    assert retry['outputs']==[output('answer',1,3,[3,4,5])];assert p.tree(failed_root,max_bytes=b.MAX_BYTES,max_entries=b.MAX_ENTRIES)==preserved
    rows.append(dict(name='cancel-fresh-retry',id=retry['id'],words=3,**counts(project,retry)))
    # Full-tree preservation, including parent seals, on a sealed failed attempt.
    fault_value=copy.deepcopy(value);k=fault_value['stages'][0]['source']['kernel']
    k['nodes'].extend([dict(id='third',op='add_imm',args=['z'],imm=1),dict(id='fourth',op='add_imm',args=['third'],imm=1)]);k['result']='fourth'
    p.write_new(project.root/'inputs/fault.json',p.encoded(fault_value));actual=d.run;calls=[]
    def inject(session,kernel,build,destination):
        i=len(calls);calls.append(destination)
        return actual(session,kernel,build,destination,injections=['wrong-word' if i==2 else 'none'])
    with patch.object(d,'run',side_effect=inject):failed=a.run(project,'fault.json',args.kernel,args.build)
    assert failed['status']=='incomplete' and failed['outputs'] is None and len(calls)==3
    sealed_root=project.root/'arrays'/failed['id'];sealed_before=p.tree(sealed_root,max_bytes=b.MAX_BYTES,max_entries=b.MAX_ENTRIES)
    fault_counts=counts(project,failed)
    recovered=a.run(project,'fault.json',args.kernel,args.build)
    assert recovered['outputs']==[output('answer',1,3,[5,6,7])]
    assert p.tree(sealed_root,max_bytes=b.MAX_BYTES,max_entries=b.MAX_ENTRIES)==sealed_before
    rows.append(dict(name='sealed-fault-fresh-retry',id=recovered['id'],words=3,**counts(project,recovered)))
    with patch('subprocess.Popen',side_effect=AssertionError('saved inspection executes')):
        for row in rows:a.load(project,row['id'])
        assert next(x for x in a.history(project) if x['id']==identity)['status']=='unsealed'
        f.load(cp,record['id']);a.load(project,failed['id'])
    summary=dict(evidence_class=a.CLASS,positive=rows,cancellation=dict(id=identity,status='unsealed',rtl_id=record['id'],device_cancelled=1,changed_options_rejected=True,old_capture_preserved=True),sealed_fault=dict(id=failed['id'],full_tree_unchanged=True,**fault_counts),sessions=sum(r['sessions'] for r in rows)+fault_counts['sessions'],jobs=sum(r['jobs'] for r in rows)+fault_counts['jobs'],final_words=sum(r['words'] for r in rows),saved_validation_no_process=True)
    (root/'summary.json').write_bytes(p.encoded(summary));print('COMPLETE',summary['sessions'],summary['final_words'],flush=True)


if __name__=='__main__':main()
