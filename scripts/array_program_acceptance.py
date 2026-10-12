#!/usr/bin/env python3
"""Owned common-source acceptance through real QEMU and existing functional RTL."""
import argparse,copy,json,subprocess,sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from raveil import project as p,project_array as a,array_program as compiler,project_mf01_grid as g,project_dag_batch as b,fold_dag as d,project_fold as f
from scripts.array_program_cases import cases


def counts(project,record):
    rows=[]
    for index,entry in enumerate(record['children']):
        cp=p.Project(project.root/'arrays'/record['id']/'children'/f'{index:03d}')
        child=g.load(cp,entry['id']);root=cp.root/'grids'/child['id']/'child/batches'/child['batch_id']
        batch=b.load(p.Project(root.parent.parent),child['batch_id'])
        for i,_ in enumerate(batch['children']):
            path=root/'children'/f'{i:02d}';receipt=d.verify(path)
            rows.append(dict(path=str(path),processed=receipt['processed'],approved=sum(x['result']['approved'] is True for x in receipt['jobs'])))
    assert len({r['path'] for r in rows})==len(rows)
    return dict(sessions=len(rows),jobs=sum(r['processed'] for r in rows),approved=sum(r['approved'] for r in rows),receipts=rows)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ['output','kernel','build']:parser.add_argument('--'+key,type=Path,required=True)
    parser.add_argument('--case',action='append',dest='selected',help='run only named positive cases (no failure campaign)')
    args=parser.parse_args();root=args.output.absolute();root.mkdir(parents=True,exist_ok=False)
    project=p.Project(p.init_project(root/'workspace'));rows=[];positive=list(cases());known={n for n,_,_ in positive}
    if args.selected and not set(args.selected)<=known:raise ValueError('unknown acceptance case')
    def cli(label,*options,code=0):
        command=[sys.executable,'-m','raveil','project',*options,'--project',str(project.root)]
        result=subprocess.run(command,capture_output=True)
        (root/(label+'.command.json')).write_bytes(p.encoded(command));(root/(label+'.stdout')).write_bytes(result.stdout);(root/(label+'.stderr')).write_bytes(result.stderr)
        assert result.returncode==code,(label,result.returncode,result.stderr.decode(errors='replace'))
        return json.loads(result.stdout) if code==0 else None
    def save(name,value):
        raw=p.encoded(value);p.write_new(project.root/'inputs'/f'{name}.json',raw);return raw
    def row(name,record,expected):
        assert record['status']=='succeeded' and record['outputs']==expected
        result=dict(name=name,id=record['id'],status=record['status'],final_words=sum(len(x['words']) for x in expected),**counts(project,record));rows.append(result)
        print('PASS',json.dumps({k:v for k,v in result.items() if k!='receipts'}),flush=True);return result
    for name,value,expected in positive:
        if args.selected and name not in args.selected:continue
        raw=save(name,value);preview=cli(name+'-check','array-check','--input',name+'.json')
        assert compiler.reference(value)==expected
        record=cli(name+'-run','array-run','--input',name+'.json','--kernel',str(args.kernel),'--build',str(args.build))
        result=row(name,record,expected);assert result['sessions']==preview['sessions']
        assert (project.root/'inputs'/f'{name}.json').read_bytes()==raw
    failure_rows=[]
    if not args.selected:
        name,value,expected=next(x for x in positive if x[0]=='pointwise-1-3')
        changed=copy.deepcopy(value);changed['stages'][0]['source']['inputs'][0]['words'][0]=9
        changed_expected=copy.deepcopy(expected);changed_expected[0]['words'][0]=16;save('edited',changed)
        record=cli('edited-run','array-run','--input','edited.json','--kernel',str(args.kernel),'--build',str(args.build));edited=row('edited',record,changed_expected)
        baseline=next(r for r in rows if r['name']==name)
        assert cli('edited-diff','array-diff',baseline['id'],edited['id'])['changed_cells']==1
        # A short four-pass chain makes the third session an unambiguous middle pass.
        value=copy.deepcopy(value);k=value['stages'][0]['source']['kernel']
        k['nodes'].extend([dict(id='next',op='add_imm',args=['z'],imm=1),dict(id='last',op='add_imm',args=['next'],imm=1)]);k['result']='last'
        save('retry',value);expected=compiler.reference(value);run=d.run
        for injection in ['wrong-word','rtl-fault']:
            calls=[]
            def inject(session,kernel,build,destination):
                i=len(calls);calls.append(str(destination))
                return run(session,kernel,build,destination,injections=[injection if i==2 else 'none'])
            with patch.object(d,'run',side_effect=inject):failed=a.run(project,'retry.json',args.kernel,args.build)
            assert failed['status']=='incomplete' and failed['outputs'] is None and len(calls)==3
            before=b._inventory(project.root/'arrays'/failed['id']);result=dict(name=injection,id=failed['id'],status='incomplete',**counts(project,failed));failure_rows.append(result)
            retry=a.run(project,'retry.json',args.kernel,args.build);row(injection+'-retry',retry,expected)
            assert before==b._inventory(project.root/'arrays'/failed['id'])
            print('PASS failure',injection,failed['id'],flush=True)
        # Rejection must occur before any attempt or process, not merely before publication.
        invalid=copy.deepcopy(value);invalid['stages'][0]['source']['kernel']['nodes'][-1]['args']=['missing'];save('invalid',invalid)
        before=set(project.workspace.ls('arrays'))
        with patch('subprocess.Popen',side_effect=AssertionError('invalid input executed')):
            try:a.run(project,'invalid.json',args.kernel,args.build)
            except ValueError:pass
            else:raise AssertionError('invalid input accepted')
        assert before==set(project.workspace.ls('arrays'))
    with patch('subprocess.Popen',side_effect=AssertionError('saved read executed')):
        for r in rows+failure_rows:a.load(project,r['id'])
        history=a.history(project);assert len(history)==len(rows)+len(failure_rows)
    receipts=[x for r in rows+failure_rows for x in r['receipts']]
    assert len({x['path'] for x in receipts})==len(receipts)
    summary=dict(evidence_class=a.CLASS,positive=rows,failures=failure_rows,sessions=len(receipts),jobs=sum(x['processed'] for x in receipts),approved=sum(x['approved'] for x in receipts),final_words=sum(r['final_words'] for r in rows),saved_validation_no_process=True)
    (root/'summary.json').write_bytes(p.encoded(summary));print('COMPLETE',json.dumps({k:v for k,v in summary.items() if k not in ('positive','failures')}),flush=True)


if __name__=='__main__':main()
