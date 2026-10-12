#!/usr/bin/env python3
"""Actual affine-source coupled runs versus direct workload formulas."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from raveil import project as p,project_mf01_grid as a,mf01_grid as g
from scripts.mf01_grid_affine_cases import cases


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['kernel','build','output']:parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();root=args.output.resolve();root.mkdir(parents=True,exist_ok=False)
    project=p.Project(p.init_project(root/'workspace'));rows=[]
    for name,value,expected in cases():
        (project.root/'inputs/grid.json').write_bytes(p.encoded(value))
        record=a.run(project,'grid.json',args.kernel,args.build)
        assert record['status']=='succeeded' and record['output']['words']==expected
        row=dict(name=name,id=record['id'],sessions=len(g.compile(value)['layout']),words=len(expected));rows.append(row);print('PASS',json.dumps(row),flush=True)
    result=dict(evidence_class=a.CLASS,records=rows,parents=len(rows),sessions=sum(r['sessions'] for r in rows),words=sum(r['words'] for r in rows))
    (root/'summary.json').write_bytes(p.encoded(result));print(json.dumps(result))


if __name__=='__main__':main()
