#!/usr/bin/env python3
"""Revalidate the owned34+2 standalone captures, then mutate copies only."""
import argparse,copy,json,shutil,subprocess,sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from raveil import sonatine_fold as s,project as p
from raveil.fold_evidence import loads
from scripts.mf01_bridge_saved_audit import duplicate


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['acceptance','cli','previous','output']:parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();out=args.output.resolve();out.mkdir(parents=True,exist_ok=False);paths=[];rows=[]
    for parent,count in [(args.acceptance,34),(args.cli,2)]:
        found=sorted(parent.resolve().rglob('receipt.json'))
        if len(found)!=count:raise ValueError('retained receipt count differs')
        paths.extend(found)
    if len(set(paths))!=36:raise ValueError('duplicate retained receipt')
    with patch('subprocess.Popen',side_effect=AssertionError('saved validation executed')):
        for path in paths:
            receipt=s.verify(path.parent);rows.append(dict(path=str(path),sha256=p.digest(path.read_bytes()),words=len(receipt['result']['output'])))
    assert sum(row['words'] for row in rows)==2176
    mutations=[]
    for label in ['approved-int','status-float','sequence-bool','output-float','receipt-duplicate','region-duplicate']:
        target=out/label;shutil.copytree(paths[0].parent,target);receipt=loads((target/'receipt.json').read_bytes())
        if label=='approved-int':receipt['result']['approved']=1
        elif label=='status-float':receipt['result']['status']=1.0
        elif label=='sequence-bool':receipt['result']['sequence']=True
        elif label=='output-float':receipt['result']['output']=[float(x) for x in receipt['result']['output']]
        elif label=='region-duplicate':
            path=target/'region.json';path.write_bytes(duplicate(path.read_bytes(),'fold'));receipt['files']['region.json']=s.digest(path)
        raw=p.encoded(receipt);(target/'receipt.json').write_bytes(duplicate(raw,'schema') if label=='receipt-duplicate' else raw)
        probe='''import sys
from unittest.mock import patch
from raveil.sonatine_fold import verify
with patch('subprocess.Popen',side_effect=AssertionError('saved verification executed')):verify(sys.argv[1])
print('accepted')
'''
        before=subprocess.run([sys.executable,'-c',probe,str(target)],cwd=args.previous.resolve(),capture_output=True,text=True)
        (out/(label+'-before.stdout')).write_text(before.stdout);(out/(label+'-before.stderr')).write_text(before.stderr)
        assert before.returncode==0 and before.stdout=='accepted\n',before.stderr
        with patch('subprocess.Popen',side_effect=AssertionError('saved validation executed')):
            try:s.verify(target)
            except ValueError as error:reason=str(error)
            else:raise AssertionError('modified standalone proof accepted')
        mutations.append(dict(name=label,previous='accepted',current='ValueError',reason=reason))
    for path,row in zip(paths,rows):assert p.digest(path.read_bytes())==row['sha256']
    summary=dict(evidence_class='saved-QEMU-proof-readonly-validation',receipts=36,words=2176,originals=rows,mutants=mutations,new_qemu_executions=0)
    (out/'summary.json').write_bytes(p.encoded(summary));print(json.dumps({k:v for k,v in summary.items() if k!='originals'}))


if __name__=='__main__':main()
