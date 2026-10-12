#!/usr/bin/env python3
"""Revalidate captured grid runs and reject altered copies without execution."""
import argparse,copy,json,shutil,sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from raveil import project as p,project_mf01_grid as a,project_dag_batch as b,mf01_grid as g


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace',type=Path,action='append',required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--rebind-source',action='store_true',help='also try consistent v2 source/plan/lowering rewrites')
    args=parser.parse_args();out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    parents=[];rejections=[]
    with patch('subprocess.Popen',side_effect=AssertionError('saved audit must not execute')):
        for workspace in args.workspace:
            project=p.Project(workspace.resolve())
            for identity in project.workspace.ls('grids'):
                record=a.load(project,identity)
                parents.append(dict(workspace=str(project.root),id=identity,status=record['status']))
                print('PASS saved',identity,record['status'],flush=True)
        first=next(r for r in parents if r['status']=='succeeded')
        source=Path(first['workspace'])/'grids'/first['id']
        cases=['source','lowered','layout','word-float','child-id']
        if args.rebind_source:cases+=['rebind-vector','rebind-shape','rebind-input']
        for case in cases:
            project=p.Project(p.init_project(out/case));root=project.root/'grids'/first['id']
            shutil.copytree(source,root);record=json.loads((root/'record.json').read_text())
            if case.startswith('rebind-'):
                value=json.loads((root/'source.json').read_text())
                if value['schema']!=g.SCHEMA_V2:raise ValueError('rebind probes require a v2 first parent')
                if case=='rebind-vector':value['kernel']['views']['a']['row']=[0,0]
                elif case=='rebind-shape':value['shape'][0]-=1
                else:value['inputs'][0]['words'][0]^=1
                compiled=g.compile(value);raw=p.encoded(value)
                filename=json.loads((root/'plan.json').read_text())['input_file']
                (root/'source.json').write_bytes(raw);(root/'lowered.json').write_bytes(p.encoded(compiled['batch']))
                (root/'plan.json').write_bytes(p.encoded(a._plan(record['id'],filename,raw,compiled)))
            elif case in ['source','lowered','layout']:
                filename={'source':'source.json','lowered':'lowered.json','layout':'plan.json'}[case]
                path=root/filename;value=json.loads(path.read_text())
                if case=='source':value['inputs'][0]['words'][0]^=1
                elif case=='lowered':value['items'][0]['dag']['jobs'][0]['inputs'][0][0]^=1
                else:value['layout'][0]['row']=-1
                path.write_bytes(p.encoded(value))
            elif case=='word-float':record['output']['words'][0]=float(record['output']['words'][0])
            else:record['batch_id']='missing'
            record['files']=b._inventory(root);raw=p.encoded(record)
            (root/'record.json').write_bytes(raw);(root/'record.sha256').write_text(p.digest(raw)+'\n')
            try:a.load(project,record['id'])
            except ValueError as error:
                if case.startswith('rebind-') and 'captured batch differs' not in str(error):raise
                rejections.append(dict(case=case,error=str(error)));print('PASS reject',case,flush=True)
            else:raise AssertionError('accepted altered '+case)
    result=dict(evidence_class='saved-QEMU-RTL-grid-proof-revalidation',parents=parents,rejections=rejections,process_creation=False)
    (out/'summary.json').write_bytes(p.encoded(result));print(json.dumps(dict(parents=len(parents),rejections=len(rejections))))


if __name__=='__main__':main()
