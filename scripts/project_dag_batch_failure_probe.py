#!/usr/bin/env python3
"""Actual coupled fault injection into a batch; no simulated child results."""
import argparse,json,sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from raveil import project as p,project_dag_batch as b,fold_dag as d
from scripts.fold_dag_cases import job,graph


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['kernel','build','output']:parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();root=args.output.resolve();root.mkdir(parents=True,exist_ok=False);project=p.Project(p.init_project(root/'workspace'))
    batch={'schema':b.INPUT,'items':[dict(name='first',dag=graph([job('value',1)])),
        dict(name='pinned',dag=graph([job('answer',1),job('fault',1)],'answer')),
        dict(name='must-not-run',dag=graph([job('value',1)]))]}
    (project.root/'inputs/batch.json').write_bytes(p.encoded(batch));execute=d.run;count=0
    def injected(session,kernel,build,destination):
        nonlocal count
        injections=['none','wrong-word'] if count==1 else None;count+=1
        return execute(session,kernel,build,destination,injections=injections)
    with patch.object(d,'run',side_effect=injected):record=b.run(project,'batch.json',args.kernel,args.build)
    saved=project.root/'batches'/record['id'];child=d.verify(saved/'children/01')
    assert record['status']=='incomplete' and record['outputs'] is None and record['attempted']==count==2
    assert child['output']['available'] and not (saved/'children/02').exists()
    with patch('subprocess.Popen',side_effect=AssertionError('verification must not execute')):assert b.load(project,record['id'])==record
    summary=dict(evidence_class=b.CLASS,id=record['id'],attempted=2,planned=3,processed_jobs=3,successes=2,
                 parent_outputs=None,incomplete_child_output_available=True,later_child_absent=True)
    (root/'summary.json').write_bytes(p.encoded(summary));print(json.dumps(summary))


if __name__=='__main__':main()
