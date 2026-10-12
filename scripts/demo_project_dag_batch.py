#!/usr/bin/env python3
"""Actual nine-tile box sum, input edit, saved history and independent oracle."""
import argparse,json,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from raveil import project as p,project_dag_batch as b
from scripts.fold_box_batch import lower,assemble,full_reference


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['kernel','build','output']:parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();root=args.output.resolve();root.mkdir(parents=True,exist_ok=False)
    project=p.Project(p.init_project(root/'workspace'));words=[((i*7919)^0xa5a55a5a)&0xffffffff for i in range(576)];words[0]=0xffffffff
    records=[];hashes=[];expected=[]
    def cli(label,*arguments):
        cmd=[sys.executable,'-m','raveil','project',*arguments,'--project',str(project.root)]
        (root/(label+'-command.json')).write_text(json.dumps(cmd)+'\n');proc=subprocess.run(cmd,capture_output=True,text=True,check=True,cwd=p.REPOSITORY)
        (root/(label+'.json')).write_text(proc.stdout);(root/(label+'.stderr')).write_text(proc.stderr);return json.loads(proc.stdout)
    for label in ['first','edited']:
        if label=='edited':words[12*24+12]^=0xffffffff
        batch,layout=lower(words,24,24,8);(project.root/'inputs/batch.json').write_bytes(p.encoded(batch));(root/(label+'-grid.json')).write_bytes(p.encoded(dict(rows=24,columns=24,words=words,layout=layout)))
        preview=cli(label+'-check','batch-check','--input','batch.json');assert preview['independent_sessions']==9 and preview['jobs']==9
        record=cli(label,'batch-run','--input','batch.json','--kernel',str(args.kernel.resolve()),'--build',str(args.build.resolve()))
        actual=assemble(record['outputs'],layout,24,24);oracle=full_reference(words,24,24)
        if actual!=oracle:raise AssertionError('full-grid oracle mismatch')
        records.append(record);expected.append(oracle);hashes.append(b._inventory(project.root/'batches'/record['id']))
    diff=cli('diff','batch-diff',records[0]['id'],records[1]['id']);history=cli('history','batches')
    assert diff['changed_cells']==9
    for i,record in enumerate(records):
        assert cli(f'inspect-{i}','batch',record['id'])==record
        assert b._inventory(project.root/'batches'/record['id'])==hashes[i]
    summary=dict(evidence_class=b.CLASS,records=[r['id'] for r in records],sessions=18,processed_jobs=18,
                 checked_words=sum(len(v) for v in expected),changed_cells=diff['changed_cells'],history=len(history),saved_unchanged=True)
    (root/'summary.json').write_bytes(p.encoded(summary));print(json.dumps(summary))


if __name__=='__main__':main()
