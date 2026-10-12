#!/usr/bin/env python3
"""Real coupled fault injections through the workspace wrapper, not host fixtures."""
import argparse,json,sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from raveil import project as p,project_dag as a,fold_dag as d
from scripts.fold_dag_cases import graph,job,linked


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['kernel','build','output']:parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();root=args.output.resolve();root.mkdir(parents=True,exist_ok=False)
    project=p.Project(p.init_project(root/'workspace'));original=d.run;rows=[]
    for name,g,injections in [('pinned',graph([job('answer',1),job('later',1)],'answer'),['none','wrong-word']),
                              ('failed-producer',graph([job('root',1),job('answer',1,linked('root'))]),['wrong-word','none'])]:
        (project.root/'inputs/dag.json').write_bytes(p.encoded(g))
        # The shim only selects the real executor's transport fault injection.
        with patch.object(d,'run',side_effect=lambda *v:original(*v,injections=injections)):
            r=a.run(project,'dag.json',args.kernel,args.build)
        a.load(project,r['id']);assert r['status']=='incomplete'
        assert r['output']['available']==(name=='pinned')
        rows.append(dict(name=name,id=r['id'],processed=r['processed'],halted=r['halted'],output=r['output']))
    (root/'summary.json').write_text(json.dumps(dict(evidence_class='host-mediated-QEMU-RTL-dag-functional',cases=rows),indent=2)+'\n')
    print(json.dumps(rows))


if __name__=='__main__':main()
