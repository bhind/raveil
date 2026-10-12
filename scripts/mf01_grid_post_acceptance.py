#!/usr/bin/env python3
"""Actual post-map DAG execution, global formulas and both stage failures."""
import argparse,json,sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from raveil import project as p,project_mf01_grid as a,project_dag_batch as b,fold_dag as d
from scripts.mf01_grid_post_cases import cases,with_post
from scripts.mf01_grid_affine_cases import matmul


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['kernel','build','output']:parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();root=args.output.resolve();root.mkdir(parents=True,exist_ok=False)
    project=p.Project(p.init_project(root/'workspace'));rows=[];faults=[]
    def execute(value):
        (project.root/'inputs/grid.json').write_bytes(p.encoded(value))
        return a.run(project,'grid.json',args.kernel,args.build)
    for name,value,expected in cases():
        record=execute(value);assert record['status']=='succeeded' and record['output']['words']==expected
        child_project=p.Project(project.root/'grids'/record['id']/'child');batch=b.load(child_project,record['batch_id'])
        row=dict(name=name,id=record['id'],sessions=len(batch['children']),jobs=sum(x['processed'] for x in batch['children']),output_words=len(expected))
        rows.append(row);print('PASS',json.dumps(row),flush=True)
    source,_=matmul(3,5,4,(2,3));source=with_post(source);run=d.run
    for stage in [0,1]:
        children=[]
        def inject(session,kernel,build,destination):
            injections=['none','none'];injections[stage]='wrong-word'
            record=run(session,kernel,build,destination,injections=injections);children.append(record);return record
        with patch.object(d,'run',side_effect=inject):record=execute(source)
        assert record['status']=='incomplete' and record['output'] is None and len(children)==1
        child=children[0];assert child['processed']==stage+1 and not child['output']['available']
        faults.append(dict(stage=stage,id=record['id'],sessions=1,jobs=child['processed'],successful_words=sum(len(j['result']['output']) for j in child['jobs'] if j['result']['approved'])))
        print('PASS fault',json.dumps(faults[-1]),flush=True)
    summary=dict(evidence_class=a.CLASS,successes=rows,faults=faults,parents=len(rows)+len(faults),
                 sessions=sum(r['sessions'] for r in rows)+len(faults),jobs=sum(r['jobs'] for r in rows)+sum(r['jobs'] for r in faults),
                 final_words=sum(r['output_words'] for r in rows),successful_job_words=2*sum(r['output_words'] for r in rows)+sum(r['successful_words'] for r in faults))
    (root/'summary.json').write_bytes(p.encoded(summary));print(json.dumps(summary))


if __name__=='__main__':main()
