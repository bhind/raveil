#!/usr/bin/env python3
"""Actual acceptance: v5 shares signed transforms on the unchanged QEMU/RTL backend."""
import argparse,json,subprocess,sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from raveil import project as p,project_mf01_grid as a,project_dag_batch as b,project_mf01_flow as f,fold_dag as d
from scripts.mf01_numeric_shared_cases import cases,branch_flow as gemm_bias_relu


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['output','kernel','build']:parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();root=args.output.resolve();root.mkdir(parents=True,exist_ok=False)
    project=p.Project(p.init_project(root/'workspace'));rows=[]
    def cli(label,*options):
        command=[sys.executable,'-m','raveil','project',*options,'--project',str(project.root)]
        result=subprocess.run(command,capture_output=True)
        (root/(label+'.command.json')).write_bytes(p.encoded(command));(root/(label+'.stdout')).write_bytes(result.stdout);(root/(label+'.stderr')).write_bytes(result.stderr)
        assert result.returncode==0,(label,result.returncode,result.stderr.decode(errors='replace'))
        return json.loads(result.stdout)
    def counts(record):
        batch=b.load(p.Project(project.root/'grids'/record['id']/'child'),record['batch_id'])
        return len(batch['children']),sum(x['processed'] for x in batch['children'])
    for name,value,expected in cases():
        raw=p.encoded(value);(project.root/'inputs/grid.json').write_bytes(raw)
        cli(name+'-check','grid-check','--input','grid.json')
        record=cli(name+'-run','grid-run','--input','grid.json','--kernel',str(args.kernel),'--build',str(args.build))
        assert record['status']=='succeeded' and record['output']['words']==expected
        assert (project.root/'inputs/grid.json').read_bytes()==raw
        sessions,jobs=counts(record);row=dict(name=name,id=record['id'],sessions=sessions,jobs=jobs,words=len(expected));rows.append(row)
        print('PASS',json.dumps(row),flush=True)
    diff=cli('partition-equivalence','grid-diff',rows[0]['id'],rows[1]['id']);assert diff['changed_cells']==0
    value,expected=gemm_bias_relu();raw=p.encoded(value);(project.root/'inputs/flow.json').write_bytes(raw)
    proposal=cli('flow-plan','flow-plan','--input','flow.json','--output','selected.json')
    record=cli('flow-run','flow-run','--input','selected.json','--kernel',str(args.kernel),'--build',str(args.build))
    assert record['status']=='succeeded' and record['outputs']==[dict(name='activation',rows=3,columns=5,words=expected)]
    assert (project.root/'inputs/flow.json').read_bytes()==raw
    sessions=jobs=0
    for index,entry in enumerate(record['children']):
        cp=p.Project(project.root/'flows'/record['id']/'children'/f'{index:02d}')
        grid=a.load(cp,entry['id'])
        child=b.load(p.Project(cp.root/'grids'/grid['id']/'child'),grid['batch_id'])
        sessions+=len(child['children']);jobs+=sum(x['processed'] for x in child['children'])
    assert sessions==proposal['sessions']==2 and jobs==proposal['jobs']==2
    flow_row=dict(id=record['id'],sessions=sessions,jobs=jobs,words=len(expected));print('PASS flow',json.dumps(flow_row),flush=True)
    run=d.run;value=list(cases())[3][1];(project.root/'inputs/grid.json').write_bytes(p.encoded(value))
    def inject(session,kernel,build,destination):return run(session,kernel,build,destination,injections=['none','wrong-word'])
    with patch.object(d,'run',side_effect=inject):failed=a.run(project,'grid.json',args.kernel,args.build)
    assert failed['status']=='incomplete' and failed['output'] is None
    assert counts(failed)==(1,2)
    with patch('subprocess.Popen',side_effect=AssertionError('saved validation executed')):
        for row in rows:a.load(project,row['id'])
        a.load(project,failed['id']);f.load(project,flow_row['id'])
        assert a.compare(project,rows[0]['id'],rows[1]['id'])['changed_cells']==0
    summary=dict(evidence_class=a.CLASS,grids=rows,flow=flow_row,fault=dict(id=failed['id'],sessions=1,jobs=2),
                 sessions=sum(x['sessions'] for x in rows)+sessions+1,jobs=sum(x['jobs'] for x in rows)+jobs+2,
                 final_words=sum(x['words'] for x in rows)+len(expected),partition_changed_cells=0,saved_validation_no_process=True)
    (root/'summary.json').write_bytes(p.encoded(summary));print(json.dumps(summary),flush=True)


if __name__=='__main__':main()
