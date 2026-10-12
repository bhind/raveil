#!/usr/bin/env python3
"""Read retained single-job coupling proofs and test exact representation changes."""
import argparse,copy,json,shutil,subprocess,sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from raveil import fold_bridge as b,project as p,project_fold as f
from raveil.fold_evidence import loads,same


def duplicate(raw,key):
    value=loads(raw)
    return ('{'+json.dumps(key)+':'+json.dumps(value[key])+','+raw.decode().lstrip()[1:]).encode()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['previous','base','index','output']:parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();root=args.output.resolve();root.mkdir(parents=True,exist_ok=False);base=args.base.resolve()
    index_raw=args.index.read_bytes();index=loads(index_raw)
    if type(index) is not dict or index.get('receipts')!=42 or type(index.get('records')) is not list or len(index['records'])!=42:
        raise ValueError('expected the retained42-receipt acceptance index')
    paths=[];success=fault=None;rows=[]
    with patch('subprocess.Popen',side_effect=AssertionError('saved validation executed')):
        for entry in index['records']:
            path=(base/entry['path']).resolve();path.relative_to(base)
            if path.name!='receipt.json' or path in paths:raise ValueError('invalid/duplicate indexed receipt')
            paths.append(path);record=b.verify(path.parent)
            if not same([entry['approved'],entry['words']],[record['result']['approved'],len(record['result']['output'])]):raise ValueError('index differs from verified receipt')
            if record['injection']=='none' and success is None:success=path.parent
            if record['injection']=='rtl-fault':fault=path.parent
            rows.append(dict(path=entry['path'],receipt_sha256=p.digest(path.read_bytes()),approved=entry['approved'],words=entry['words']))
    assert success is not None and fault is not None
    mutants=[]
    probe='''import json,sys
from pathlib import Path
from unittest.mock import patch
from raveil import fold_bridge as b,project_fold as f,project as p
with patch('subprocess.Popen',side_effect=AssertionError('saved validation executed')):
 try:
  path=Path(sys.argv[2])
  result=b.verify(path) if sys.argv[1]=='bridge' else f.load(p.Project(path.parent.parent),path.name)
 except Exception as error:print(json.dumps(dict(outcome='rejected',type=type(error).__name__,message=str(error))))
 else:print(json.dumps(dict(outcome='accepted')))
'''
    def inspect(label,kind,target):
        before=subprocess.run([sys.executable,'-c',probe,kind,str(target)],cwd=args.previous.resolve(),capture_output=True,text=True)
        (root/(label+'-before.stdout')).write_text(before.stdout);(root/(label+'-before.stderr')).write_text(before.stderr)
        assert before.returncode==0,before.stderr;old=loads(before.stdout);assert old['outcome']=='accepted',(label,old)
        with patch('subprocess.Popen',side_effect=AssertionError('saved validation executed')):
            try:
                if kind=='bridge':b.verify(target)
                else:f.load(p.Project(target.parent.parent),target.name)
            except ValueError as error:new=dict(outcome='rejected',type='ValueError',message=str(error))
            else:raise AssertionError(label+' was accepted')
        mutants.append(dict(name=label,previous=old,current=new))
    for label in ['approved-int','status-float','sequence-bool','output-float','dispatch-bool','dispatch-float','receipt-duplicate','dispatch-duplicate','region-duplicate']:
        target=root/label;shutil.copytree(success,target);record=loads((target/'receipt.json').read_bytes())
        if label=='approved-int':record['result']['approved']=1
        elif label=='status-float':record['result']['status']=float(record['result']['status'])
        elif label=='sequence-bool':record['result']['sequence']=True
        elif label=='output-float':record['result']['output']=[float(x) for x in record['result']['output']]
        elif label in ['dispatch-bool','dispatch-float']:
            path=target/'dispatch.json';value=loads(path.read_bytes());value['sequence']=True if label.endswith('bool') else 1.0;path.write_bytes(p.encoded(value));record['files']['dispatch.json']=b.digest(path)
        elif label!='receipt-duplicate':
            filename,key=('dispatch.json','sequence') if label=='dispatch-duplicate' else ('region.json','fold')
            path=target/filename;path.write_bytes(duplicate(path.read_bytes(),key));record['files'][filename]=b.digest(path)
        raw=p.encoded(record);(target/'receipt.json').write_bytes(duplicate(raw,'schema') if label=='receipt-duplicate' else raw)
        inspect(label,'bridge',target)
    fault_record=loads((fault/'receipt.json').read_bytes());source=fault/'project/folds'/fault_record['rtl_id']
    for label,value in [('incomplete-build-bool',True),('incomplete-build-float',1.0),('incomplete-build-text','not-a-hash')]:
        project_root=root/label/'project';p.init_project(project_root);(project_root/'folds').mkdir()
        target=project_root/'folds'/source.name;shutil.copytree(source,target)
        plan=loads((target/'plan.json').read_bytes());plan['build_sha256']=value;(target/'plan.json').write_bytes(p.encoded(plan))
        record=loads((target/'record.json').read_bytes());record['files']=f._inventory(target);(target/'record.json').write_bytes(p.encoded(record))
        inspect(label,'fold',target)
    # Every original remains bound to its initial bytes after all copy mutations.
    for path,row in zip(paths,rows):assert p.digest(path.read_bytes())==row['receipt_sha256']
    summary=dict(evidence_class='saved-proof-readonly-validation',index_sha256=p.digest(index_raw),retained=rows,
                 verified_receipts=len(rows),successful=sum(row['approved'] for row in rows),rejected=sum(not row['approved'] for row in rows),words=sum(row['words'] for row in rows),mutants=mutants,new_qemu_rtl_executions=0)
    (root/'summary.json').write_bytes(p.encoded(summary));print(json.dumps({key:value for key,value in summary.items() if key!='retained'}),flush=True)


if __name__=='__main__':main()
