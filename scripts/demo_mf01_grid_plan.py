#!/usr/bin/env python3
"""Actual CLI tile planning for a blocked matrix product and an existing stencil."""
import argparse,json,subprocess,sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from raveil import project as p,project_mf01_grid as a,mf01_grid as g
from scripts.mf01_grid_affine_cases import matmul
from scripts.mf01_grid_cases import cases
from scripts.fold_box_batch import full_reference


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['kernel','build','output']:parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();root=args.output.resolve();root.mkdir(parents=True,exist_ok=False)
    project=p.Project(p.init_project(root/'workspace'));rows=[];sources={}
    def cli(label,*arguments,expected=0):
        command=[sys.executable,'-m','raveil','project',*arguments,'--project',str(project.root)]
        (root/(label+'-command.json')).write_bytes(p.encoded(command))
        proc=subprocess.run(command,cwd=p.REPOSITORY,capture_output=True,text=True)
        (root/(label+'.stdout')).write_text(proc.stdout);(root/(label+'.stderr')).write_text(proc.stderr)
        assert proc.returncode==expected,(label,proc.returncode,proc.stderr)
        return json.loads(proc.stdout) if expected==0 else None
    matrix,expected=matmul(17,19,64)
    box=next(v for name,v in cases() if name=='box-sum')
    workloads=[('matmul',matrix,expected,[5,5]),('box',box,full_reference(box['inputs'][0]['words'],24,24),[12,12])]
    for name,value,expected,tile in workloads:
        filename=name+'.json';(project.root/'inputs'/filename).write_bytes(p.encoded(value));sources[filename]=p.digest(p.encoded(value))
        if name=='matmul':
            cli('original-check','grid-check','--input',filename,expected=2)
            cli('original-run','grid-run','--input',filename,'--kernel',str(args.kernel.resolve()),'--build',str(args.build.resolve()),expected=2)
            assert not (project.root/'grids').exists()
        before=p.tree(project.root/'inputs')
        proposal=cli(name+'-preview','grid-plan','--input',filename)
        assert before==p.tree(project.root/'inputs') and proposal['selected']['tile']==tile
        saved=cli(name+'-select','grid-plan','--input',filename,'--output',name+'-selected.json')
        assert saved['source']==proposal['source']
        cli(name+'-check','grid-check','--input',name+'-selected.json')
        record=cli(name+'-run','grid-run','--input',name+'-selected.json','--kernel',str(args.kernel.resolve()),'--build',str(args.build.resolve()))
        assert record['status']=='succeeded' and record['output']['words']==expected
        row=dict(name=name,id=record['id'],tile=tile,sessions=proposal['selected']['sessions'],words=len(expected),admitted_tiles=proposal['admitted'])
        rows.append(row);print('PASS',json.dumps(row),flush=True)
    impossible,_=matmul(64,64,64);(project.root/'inputs/impossible.json').write_bytes(p.encoded(impossible))
    previous=project.workspace.ls('grids');cli('impossible-plan','grid-plan','--input','impossible.json','--output','impossible-selected.json',expected=2)
    assert not (project.root/'inputs/impossible-selected.json').exists() and project.workspace.ls('grids')==previous
    with patch('subprocess.Popen',side_effect=AssertionError('saved reads must not execute')):
        for row in rows:assert a.load(project,row['id'])['status']=='succeeded'
    for filename,sha in sources.items():assert p.digest((project.root/'inputs'/filename).read_bytes())==sha
    result=dict(evidence_class=a.CLASS,records=rows,parents=len(rows),sessions=sum(r['sessions'] for r in rows),words=sum(r['words'] for r in rows),
                original_sources_unchanged=True,infeasible_has_no_output=True,saved_revalidated=True)
    (root/'summary.json').write_bytes(p.encoded(result));print(json.dumps(result))


if __name__=='__main__':main()
