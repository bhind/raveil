#!/usr/bin/env python3
"""Saved v3 proof validation and coordinated post-map tamper probes."""
import argparse,json,shutil,sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from raveil import project as p,project_mf01_grid as a,project_dag_batch as b,mf01_grid as g


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['workspace','output']:parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();project=p.Project(args.workspace.resolve());out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    rows=[];rejections=[]
    with patch('subprocess.Popen',side_effect=AssertionError('saved audit must not execute')):
        for identity in project.workspace.ls('grids'):
            record=a.load(project,identity);rows.append(dict(id=identity,status=record['status']));print('PASS saved',identity,flush=True)
        first=next(r for r in rows if r['status']=='succeeded');original=project.root/'grids'/first['id']
        for case in ['post-rebind','remove-post','intermediate-output','float-output']:
            altered=p.Project(p.init_project(out/case));root=altered.root/'grids'/first['id'];shutil.copytree(original,root)
            record=json.loads((root/'record.json').read_text())
            if case in ['post-rebind','remove-post']:
                source=json.loads((root/'source.json').read_text());assert source['schema']==g.SCHEMA_V3
                if case=='post-rebind':source['post']['nodes'][1]['imm']+=1
                else:source['schema']=g.SCHEMA_V2;del source['post']
                compiled=g.compile(source);raw=p.encoded(source);filename=json.loads((root/'plan.json').read_text())['input_file']
                (root/'source.json').write_bytes(raw);(root/'lowered.json').write_bytes(p.encoded(compiled['batch']))
                (root/'plan.json').write_bytes(p.encoded(a._plan(record['id'],filename,raw,compiled)))
            elif case=='intermediate-output':record['output']['words']=[(v-7)&0xffffffff for v in record['output']['words']]
            else:record['output']['words'][0]=float(record['output']['words'][0])
            record['files']=b._inventory(root);raw=p.encoded(record)
            (root/'record.json').write_bytes(raw);(root/'record.sha256').write_text(p.digest(raw)+'\n')
            try:a.load(altered,record['id'])
            except ValueError as error:
                if case in ['post-rebind','remove-post'] and 'captured batch differs' not in str(error):raise
                rejections.append(dict(case=case,error=str(error)));print('PASS reject',case,flush=True)
            else:raise AssertionError('accepted '+case)
    result=dict(evidence_class='saved-QEMU-RTL-post-map-revalidation',parents=rows,rejections=rejections,process_creation=False)
    (out/'summary.json').write_bytes(p.encoded(result));print(json.dumps(dict(parents=len(rows),rejections=len(rejections))))


if __name__=='__main__':main()
