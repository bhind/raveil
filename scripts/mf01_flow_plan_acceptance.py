#!/usr/bin/env python3
"""Advisory flow planning, actual selected execution and saved baseline comparison."""
import argparse,json,shutil,subprocess,sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from raveil import project as p,project_mf01_flow as a
from scripts.mf01_flow_cases import diamond
from scripts.mf01_flow_plan_cases import rescue,impossible


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['output','kernel','build','baseline-workspace']:parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();root=args.output.resolve();root.mkdir(parents=True,exist_ok=False);project=p.Project(p.init_project(root/'workspace'));rows=[]
    def cli(name,*options,code=0):
        command=[sys.executable,'-m','raveil','project',*options,'--project',str(project.root)]
        result=subprocess.run(command,capture_output=True)
        (root/(name+'.command.json')).write_bytes(p.encoded(command));(root/(name+'.stdout')).write_bytes(result.stdout);(root/(name+'.stderr')).write_bytes(result.stderr)
        assert result.returncode==code,(name,result.returncode,result.stderr.decode(errors='replace'))
        return json.loads(result.stdout) if code==0 else None
    value,expected=rescue();raw=p.encoded(value);(project.root/'inputs/rescue.json').write_bytes(raw)
    cli('original-check','flow-check','--input','rescue.json',code=2)
    cli('original-run','flow-run','--input','rescue.json','--kernel',str(args.kernel),'--build',str(args.build),code=2)
    assert 'flows' not in project.workspace.ls('/')
    before=p.tree(project.root);cli('preview','flow-plan','--input','rescue.json');assert p.tree(project.root)==before
    for name,value,expected in [('rescue',value,[dict(name='second',rows=3,columns=9,words=expected)]),('diamond',*diamond())]:
        raw=p.encoded(value);(project.root/'inputs'/f'{name}.json').write_bytes(raw)
        proposal=cli(name+'-plan','flow-plan','--input',name+'.json','--output',name+'-selected.json')
        cli(name+'-check','flow-check','--input',name+'-selected.json')
        record=cli(name+'-run','flow-run','--input',name+'-selected.json','--kernel',str(args.kernel),'--build',str(args.build))
        assert record['status']=='succeeded' and record['outputs']==expected
        assert (project.root/'inputs'/f'{name}.json').read_bytes()==raw
        row=dict(name=name,id=record['id'],sessions=proposal['sessions'],jobs=proposal['jobs'],packed_input_words=proposal['packed_input_words'],final_words=sum(len(x['words']) for x in expected))
        rows.append(row);print('PASS',json.dumps(row),flush=True)
    original=p.Project(args.baseline_workspace.resolve())
    baseline=next(path for path in (original.root/'flows').iterdir() if json.loads((path/'source.json').read_text())['outputs']==['product','join'])
    old=a.load(original,baseline.name);assert old['status']=='succeeded'
    shutil.copytree(baseline,project.root/'flows'/baseline.name)
    difference=cli('baseline-diff','flow-diff',baseline.name,rows[1]['id']);assert difference['changed_cells']==0
    before=set(project.workspace.ls('flows'));(project.root/'inputs/impossible.json').write_bytes(p.encoded(impossible()))
    cli('impossible','flow-plan','--input','impossible.json','--output','impossible-selected.json',code=2)
    assert not (project.root/'inputs/impossible-selected.json').exists() and set(project.workspace.ls('flows'))==before
    with patch('subprocess.Popen',side_effect=AssertionError('saved validation executed')):
        for row in rows:a.load(project,row['id'])
        assert a.compare(project,baseline.name,rows[1]['id'])['changed_cells']==0
    summary=dict(evidence_class=a.CLASS,selected=rows,new_parents=2,new_sessions=sum(x['sessions'] for x in rows),new_jobs=sum(x['jobs'] for x in rows),
                 final_words=sum(x['final_words'] for x in rows),imported_baseline=dict(id=baseline.name,new_execution=False,changed_cells=0),infeasible_no_output=True)
    (root/'summary.json').write_bytes(p.encoded(summary));print(json.dumps(summary))


if __name__=='__main__':main()
