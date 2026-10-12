#!/usr/bin/env python3
"""Saved coupled flow revalidation and rehashed-copy tamper rejection."""
import argparse,copy,json,shutil,sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from raveil import project as p,project_mf01_flow as a,project_dag_batch as b


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--workspace',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();root=args.output.resolve();root.mkdir(parents=True,exist_ok=False);project=p.Project(args.workspace.resolve());rows=[]
    with patch('subprocess.Popen',side_effect=AssertionError('saved audit executed')):
        records=[a.load(project,row['id']) for row in a.history(project)]
        first=next(r for r in records if r['status']=='succeeded' and len(r['children'])==2)
        # The acceptance workspace's first two-stage flow is the owned pair().
        for kind in ['producer-rebind','kernel-rebind','float-output','missing-stage']:
            target=p.Project(p.init_project(root/kind));(target.root/'flows').mkdir();source=project.root/'flows'/first['id'];dest=target.root/'flows'/first['id'];shutil.copytree(source,dest)
            record=copy.deepcopy(first)
            if kind=='producer-rebind':
                value=json.loads((dest/'source.json').read_text());value['stages'][0]['source']['inputs'][0]=dict(schema='raveil.grid-input/v2',rows=5,columns=6,words=[0]*30)
                raw=p.encoded(value);(dest/'source.json').write_bytes(raw);plan=json.loads((dest/'plan.json').read_text())
                plan['source_sha256']=p.digest(raw);plan['preview']=a.flow.compile(value);(dest/'plan.json').write_bytes(p.encoded(plan))
            elif kind=='kernel-rebind':
                (dest/'kernel.elf').write_bytes(b'rebound kernel');plan=json.loads((dest/'plan.json').read_text());plan['kernel_sha256']=p.digest(b'rebound kernel');(dest/'plan.json').write_bytes(p.encoded(plan))
            elif kind=='float-output':record['outputs'][0]['words'][0]=float(record['outputs'][0]['words'][0])
            else:record['children'].pop()
            record['files']=b._inventory(dest);raw=p.encoded(record);(dest/'record.json').write_bytes(raw);(dest/'record.sha256').write_text(p.digest(raw)+'\n')
            try:a.load(target,record['id'])
            except ValueError as error:
                message=str(error)
                expected={'producer-rebind':'producer binding','kernel-rebind':'executables differ','float-output':'noninteger number','missing-stage':'exact scheduled prefix'}[kind]
                assert expected in message,message;rows.append(dict(case=kind,rejected=message));print('PASS reject',kind,message,flush=True)
            else:raise AssertionError('modified proof accepted: '+kind)
    summary=dict(evidence_class='saved-functional-proof-audit',parents=len(records),modified_rejections=rows,process_creation=False)
    (root/'summary.json').write_bytes(p.encoded(summary));print(json.dumps(summary))


if __name__=='__main__':main()
