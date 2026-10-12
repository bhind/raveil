#!/usr/bin/env python3
"""Actual editable workspace DAG demonstration with retained named results."""
import argparse,json,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from raveil import project as p,project_dag as a


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['kernel','build','output']:parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();root=args.output.resolve();root.mkdir(parents=True,exist_ok=False)
    workspace=p.init_project(root/'workspace');project=p.Project(workspace)
    source=workspace/'inputs/dag.json';source.write_bytes((p.REPOSITORY/'examples/fold-dag-diamond.json').read_bytes())
    def cli(label,*words):
        cmd=[sys.executable,'-m','raveil','project',*words,'--project',str(workspace)]
        proc=subprocess.run(cmd,capture_output=True,text=True,check=True,cwd=p.REPOSITORY)
        (root/(label+'-command.json')).write_text(json.dumps(cmd)+'\n')
        (root/(label+'.json')).write_text(proc.stdout);(root/(label+'.stderr')).write_text(proc.stderr)
        return json.loads(proc.stdout)
    cli('preview','dag-check','--input','dag.json');records=[];frozen=[]
    for label in ['first','input-edit','program-edit']:
        if label!='first':
            g=json.loads(source.read_text())
            if label=='input-edit':g['jobs'][0]['inputs'][0][0]=4
            else:g['jobs'][-1]['region']['nodes'][-1]['op']='max'
            source.write_bytes(p.encoded(g))
        record=cli(label,'dag-run','--input','dag.json','--kernel',str(args.kernel.resolve()),'--build',str(args.build.resolve()))
        records.append(record);frozen.append(p.tree(workspace/'dags'/record['id']))
    values=[r['output']['output'] for r in records]
    if values!=[[34],[38],[27]]:raise AssertionError(values)
    comparisons=[cli('diff-'+str(i),'dag-diff',records[i]['id'],records[i+1]['id']) for i in range(2)]
    history=cli('history','dags')
    for i,record in enumerate(records):
        if cli('inspect-'+str(i),'dag',record['id'])!=record:raise AssertionError('changed inspection')
        if p.tree(workspace/'dags'/record['id'])!=frozen[i]:raise AssertionError('saved record mutated')
    summary=dict(evidence_class='host-mediated-QEMU-RTL-dag-functional',records=[r['id'] for r in records],
                 final_outputs=values,processed=sum(r['processed'] for r in records),
                 changed_cells=[d['changed_cells'] for d in comparisons],saved_unchanged=True,history=len(history))
    (root/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary))


if __name__=='__main__':main()
