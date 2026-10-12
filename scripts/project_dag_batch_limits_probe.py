#!/usr/bin/env python3
"""Actual maximum child/job count using one-word MF01 jobs and existing tools."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from raveil import project as p,project_dag_batch as b
from scripts.fold_dag_cases import job,graph


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['kernel','build','output']:parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();root=args.output.resolve();root.mkdir(parents=True,exist_ok=False);project=p.Project(p.init_project(root/'workspace'))
    batch={'schema':b.INPUT,'items':[dict(name=f'item-{i}',dag=graph([job(f'j{k}',1,[[i],[k]]) for k in range(8)])) for i in range(16)]}
    (project.root/'inputs/batch.json').write_bytes(p.encoded(batch));preview=b.check(project,'batch.json');assert preview['jobs']==128
    record=b.run(project,'batch.json',args.kernel,args.build)
    assert record['status']=='succeeded' and [o['words'] for o in record['outputs']]==[[i+7] for i in range(16)]
    assert b.load(project,record['id'])==record
    summary=dict(evidence_class=b.CLASS,id=record['id'],sessions=16,processed_jobs=128,checked_words=128,
                 named_outputs=16,artifact_entries=len(record['files']))
    (root/'summary.json').write_bytes(p.encoded(summary));print(json.dumps(summary))


if __name__=='__main__':main()
