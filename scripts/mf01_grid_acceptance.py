#!/usr/bin/env python3
"""Actual generic grid programs and incomplete-child suppression."""
import argparse,json,sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from raveil import project as p,project_mf01_grid as a,project_dag_batch as b,fold_dag as d,mf01_grid as g
from scripts.mf01_grid_cases import make,cases


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['kernel','build','output']:parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();root=args.output.resolve();root.mkdir(parents=True,exist_ok=False);project=p.Project(p.init_project(root/'workspace'));rows=[]
    for name,source in cases():
        if name=='box-sum':continue  # Separate CLI demo covers source/program edits.
        (project.root/'inputs/grid.json').write_bytes(p.encoded(source));record=a.run(project,'grid.json',args.kernel,args.build)
        assert record['output']['words']==g.reference(source)
        rows.append(dict(name=name,id=record['id'],sessions=len(g.compile(source)['layout']),words=len(record['output']['words'])));print('PASS',json.dumps(rows[-1]),flush=True)
    source=make(3,5,(2,3));(project.root/'inputs/grid.json').write_bytes(p.encoded(source));execute=d.run;count=0
    def inject(session,kernel,build,destination):
        nonlocal count
        fault=count==1;count+=1;return execute(session,kernel,build,destination,injections=['wrong-word'] if fault else None)
    with patch.object(d,'run',side_effect=inject):record=a.run(project,'grid.json',args.kernel,args.build)
    assert record['status']=='incomplete' and record['output'] is None and count==2
    with patch('subprocess.Popen',side_effect=AssertionError('saved inspection must not execute')):assert a.load(project,record['id'])==record
    result=dict(evidence_class=a.CLASS,successes=rows,failure=dict(id=record['id'],sessions=2,successful_words=6,output=None))
    (root/'summary.json').write_bytes(p.encoded(result));print(json.dumps(dict(parents=len(rows)+1,sessions=sum(r['sessions'] for r in rows)+2,successful_words=sum(r['words'] for r in rows)+6)))


if __name__=='__main__':main()
