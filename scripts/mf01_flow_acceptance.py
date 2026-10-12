#!/usr/bin/env python3
"""Actual editable whole-grid flows through the CLI and coupled executor."""
import argparse,json,subprocess,sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from raveil import project as p,project_mf01_flow as a,project_mf01_grid as g,project_dag_batch as b,fold_dag as d
from scripts.mf01_flow_cases import cases,pair,eight,product


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['output','kernel','build']:parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();root=args.output.resolve();root.mkdir(parents=True,exist_ok=False)
    project=p.Project(p.init_project(root/'workspace'));rows=[];identities=[]
    def cli(name,*options):
        command=[sys.executable,'-m','raveil','project',*options,'--project',str(project.root)]
        result=subprocess.run(command,capture_output=True)
        (root/(name+'.command.json')).write_bytes(p.encoded(command));(root/(name+'.stdout')).write_bytes(result.stdout);(root/(name+'.stderr')).write_bytes(result.stderr)
        assert result.returncode==0,(command,result.stderr.decode(errors='replace'))
        return json.loads(result.stdout)
    def summarize(name,record):
        sessions=jobs=0
        for i,entry in enumerate(record['children']):
            cp=p.Project(project.root/'flows'/record['id']/'children'/f'{i:02d}')
            grid=g.load(cp,entry['id']);gp=cp.root/'grids'/entry['id'];batch=b.load(p.Project(gp/'child'),grid['batch_id'])
            sessions+=len(batch['children']);jobs+=sum(c['processed'] for c in batch['children'])
        row=dict(name=name,id=record['id'],stages=len(record['children']),sessions=sessions,jobs=jobs,
                 final_words=sum(len(x['words']) for x in record['outputs']) if record['outputs'] else 0,status=record['status'])
        rows.append(row);identities.append(record['id']);print('PASS',json.dumps(row),flush=True)
    for name,value,expected in cases():
        (project.root/'inputs/flow.json').write_bytes(p.encoded(value));before=p.tree(project.root,max_bytes=b.MAX_BYTES,max_entries=b.MAX_ENTRIES)
        cli(name+'-check','flow-check','--input','flow.json');assert p.tree(project.root,max_bytes=b.MAX_BYTES,max_entries=b.MAX_ENTRIES)==before
        record=cli(name+'-run','flow-run','--input','flow.json','--kernel',str(args.kernel),'--build',str(args.build))
        assert record['status']=='succeeded' and record['outputs']==expected;summarize(name,record)
    value,_=pair();first=value['stages'][1]['source'];first['inputs'][0]['words'][0]^=1
    ab=product(first['inputs'][0]['words'],first['inputs'][1]['words'],5,6,7)
    expected=product(ab,value['stages'][0]['source']['inputs'][1]['words'],5,4,6)
    (project.root/'inputs/flow.json').write_bytes(p.encoded(value))
    record=cli('edited-run','flow-run','--input','flow.json','--kernel',str(args.kernel),'--build',str(args.build))
    assert record['outputs'][0]['words']==expected;summarize('edited-two-products',record)
    delta=cli('edited-diff','flow-diff',identities[0],record['id']);assert delta['changed_cells']>0
    value,_=eight();(project.root/'inputs/flow.json').write_bytes(p.encoded(value));run=d.run;calls=[]
    def fail_middle(session,kernel,build,destination):
        injections=['none']*len(session['jobs'])
        if len(calls)==2:injections[0]='wrong-word'
        calls.append(destination);return run(session,kernel,build,destination,injections=injections)
    with patch.object(d,'run',side_effect=fail_middle):record=a.run(project,'flow.json',args.kernel,args.build)
    assert record['status']=='incomplete' and record['outputs'] is None and len(calls)==3;summarize('failed-middle',record)
    with patch('subprocess.Popen',side_effect=AssertionError('saved read executed')):
        for identity in identities:a.load(project,identity)
        assert len(a.history(project))==5
        assert a.compare(project,identities[0],identities[3])['changed_cells']==delta['changed_cells']
    summary=dict(evidence_class=a.CLASS,flows=rows,parents=len(rows),sessions=sum(r['sessions'] for r in rows),
                 jobs=sum(r['jobs'] for r in rows),final_words=sum(r['final_words'] for r in rows),saved_without_execution=len(identities))
    (root/'summary.json').write_bytes(p.encoded(summary));print(json.dumps(summary))


if __name__=='__main__':main()
