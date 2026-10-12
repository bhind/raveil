#!/usr/bin/env python3
"""Actual source edits and all-cell verification over the general grid workflow."""
import argparse,json,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from raveil import project as p,project_dag_batch as b
from scripts.mf01_grid_cases import cases
from scripts.fold_box_batch import full_reference


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['kernel','build','output']:parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();root=args.output.resolve();root.mkdir(parents=True,exist_ok=False);project=p.Project(p.init_project(root/'workspace'))
    source=next(v for name,v in cases() if name=='box-sum');records=[];frozen=[]
    def cli(label,*arguments):
        cmd=[sys.executable,'-m','raveil','project',*arguments,'--project',str(project.root)]
        (root/(label+'-command.json')).write_text(json.dumps(cmd)+'\n');proc=subprocess.run(cmd,capture_output=True,text=True,check=True,cwd=p.REPOSITORY)
        (root/(label+'.json')).write_text(proc.stdout);(root/(label+'.stderr')).write_text(proc.stderr);return json.loads(proc.stdout)
    for label in ['first','input-edit','program-edit']:
        if label=='input-edit':source['inputs'][0]['words'][12*24+12]^=0xffffffff
        elif label=='program-edit':
            source['kernel']['nodes'].append(dict(id='biased',op='add_imm',args=['sum'],imm=1));source['kernel']['result']='biased'
        (project.root/'inputs/grid.json').write_bytes(p.encoded(source));cli(label+'-check','grid-check','--input','grid.json')
        record=cli(label,'grid-run','--input','grid.json','--kernel',str(args.kernel.resolve()),'--build',str(args.build.resolve()))
        expected=full_reference(source['inputs'][0]['words'],24,24)
        if label=='program-edit':expected=[(v+3)&0xffffffff for v in expected]
        assert record['output']['words']==expected
        records.append(record);frozen.append(b._inventory(project.root/'grids'/record['id']))
    diffs=[cli('diff-'+str(i),'grid-diff',records[i]['id'],records[i+1]['id']) for i in range(2)];assert [r['changed_cells'] for r in diffs]==[9,576]
    history=cli('history','grids')
    for i,r in enumerate(records):
        assert cli('inspect-'+str(i),'grid',r['id'])==r
        assert b._inventory(project.root/'grids'/r['id'])==frozen[i]
    summary=dict(evidence_class='host-tiled-QEMU-RTL-grid-functional',records=[r['id'] for r in records],parents=3,sessions=27,jobs=27,checked_words=1728,
                 changed_cells=[9,576],saved_unchanged=True,history=len(history))
    (root/'summary.json').write_bytes(p.encoded(summary));print(json.dumps(summary))


if __name__=='__main__':main()
