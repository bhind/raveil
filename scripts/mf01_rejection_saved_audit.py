#!/usr/bin/env python3
"""Revalidate retained proof and reproduce over-count rejection without execution."""
import argparse,copy,json,shutil,subprocess,sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from raveil import project as p,fold_dag as dag,fold_session as session,fold_chain as chain
from raveil.fold_evidence import loads


def receipts(parent, schema, expected):
    roots=[]
    for path in sorted(parent.resolve().rglob('receipt.json')):
        value=loads(path.read_bytes())
        if type(value) is not dict:raise ValueError('receipt must be an object')
        if value.get('schema')==schema:roots.append(path.parent)
    if len(roots)!=expected:raise ValueError('saved receipt count differs from expected inventory')
    return roots


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['previous','dag-root','session-root','output']:parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--expected-dag',type=int,required=True);parser.add_argument('--expected-session',type=int,required=True)
    parser.add_argument('--chain-root',type=Path);parser.add_argument('--expected-chain',type=int)
    args=parser.parse_args()
    if (args.chain_root is None)!=(args.expected_chain is None):parser.error('--chain-root and --expected-chain must be supplied together')
    kinds=[('dag',dag,args.dag_root,args.expected_dag),('session',session,args.session_root,args.expected_session)]
    if args.chain_root is not None:kinds.append(('chain',chain,args.chain_root,args.expected_chain))
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=False);rows=[]
    for label,module,parent,expected in kinds:
        if expected<1:raise ValueError('positive expected receipt count required')
        roots=receipts(parent,'raveil.fold-'+label+'-run.v1',expected);chosen=None
        with patch('subprocess.Popen',side_effect=AssertionError('saved validation executed')):
            for root in roots:
                value=module.verify(root)
                if chosen is None and value['processed']==value['planned']<8 and all(row['result']['approved'] for row in value['jobs']):chosen=root
        assert chosen is not None,(label,'missing suitable saved fixture')
        target=out/label;shutil.copytree(chosen,target);receipt=loads((target/'receipt.json').read_bytes());n=receipt['processed']
        shutil.copytree(target/'jobs'/f'{n-1:02d}',target/'jobs'/f'{n:02d}')
        receipt['processed']=n+1;receipt['jobs'].append(copy.deepcopy(receipt['jobs'][-1]))
        lines=(target/'stdout.log').read_text().splitlines();prefix='RAVEIL-FOLD-'+label.upper()+'-START';start=next(i for i,line in enumerate(lines) if line.startswith(prefix))
        # Append a four-line phase after the valid prefix. Claimed job count stays
        # bound to the original input: only processed rows exceed declared jobs.
        at=start+1+4*n;lines[at:at]=lines[at-4:at];(target/'stdout.log').write_text('\n'.join(lines)+'\n')
        receipt['files']={name:module.digest(target/name) for name in sorted(module.files_for(n+1))}
        (target/'receipt.json').write_bytes(p.encoded(receipt))
        probe='''import json,sys
from unittest.mock import patch
from raveil import fold_dag,fold_session,fold_chain
module={'dag':fold_dag,'session':fold_session,'chain':fold_chain}[sys.argv[1]]
with patch('subprocess.Popen',side_effect=AssertionError('saved validation executed')):
 try:module.verify(sys.argv[2])
 except Exception as error:print(json.dumps(dict(type=type(error).__name__,message=str(error))))
 else:raise AssertionError('modified proof accepted')
'''
        before=subprocess.run([sys.executable,'-c',probe,label,str(target)],cwd=args.previous.resolve(),capture_output=True,text=True)
        (out/(label+'-before.stdout')).write_text(before.stdout);(out/(label+'-before.stderr')).write_text(before.stderr)
        assert before.returncode==0,before.stderr;old=json.loads(before.stdout);assert old['type']=='IndexError',old
        with patch('subprocess.Popen',side_effect=AssertionError('saved validation executed')):
            try:module.verify(target)
            except ValueError as error:assert str(error)=='processed count exceeds declared jobs';message=str(error)
            else:raise AssertionError('modified proof accepted')
        row=dict(kind=label,retained_verified=len(roots),original=str(chosen),original_receipt_sha256=p.digest((chosen/'receipt.json').read_bytes()),
                 declared_jobs=n,modified_processed=n+1,previous=old,current=dict(type='ValueError',message=message))
        rows.append(row);print(json.dumps(row),flush=True)
    (out/'summary.json').write_bytes(p.encoded(dict(evidence_class='saved-proof-readonly-validation',rows=rows,new_qemu_rtl_executions=0)))


if __name__=='__main__':main()
