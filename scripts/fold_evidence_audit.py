"""Revalidate retained MF01 evidence and reject rehashed structural mutations.

This executes no guest/RTL process and never modifies a supplied evidence root.
Mutation probes operate only on temporary copies. Output is a new audit record.
"""
import argparse
import copy
import json
from pathlib import Path
import shutil
import tempfile
from unittest.mock import patch
from raveil import fold_session as s, fold_chain as c, fold_dag as d, project as p
from raveil.sonatine_fold import digest
from raveil.fold_evidence import loads

MODULES={f'raveil.fold-{name}-run.v1':module for name,module in [('session',s),('chain',c),('dag',d)]}


def audit(roots):
    records=[];chosen={};seen=set();probes=[];skipped=[]
    with patch('subprocess.Popen',side_effect=AssertionError('saved audit must not execute')):
        for directory in roots:
            for path in sorted(Path(directory).rglob('receipt.json')):
                if path.resolve() in seen:continue
                seen.add(path.resolve());raw=loads(path.read_text())
                if type(raw) is not dict:raise ValueError('receipt must be an object')
                module=MODULES.get(raw.get('schema'))
                if module is None:
                    skipped.append(dict(root=str(path.parent),schema=raw.get('schema')));continue
                before=digest(path);record=module.verify(path.parent)
                assert digest(path)==before
                records.append(dict(root=str(path.parent),receipt_sha256=before,schema=record['schema'],processed=record['processed'],halted=record['halted']))
                if record['halted']==0 and all(row['result']['approved'] for row in record['jobs']):
                    old=chosen.get(module)
                    if old is None or record['processed']<old[1]['processed']:chosen[module]=(path.parent,record)
        if set(chosen)!=set(MODULES.values()):raise ValueError('need at least one successful saved record of each protocol')
        for module,(source,original) in chosen.items():
            def reject(label,root,receipt=None):
                try:module.verify(root) if receipt is None else module._verify(root,receipt)
                except ValueError as exc:probes.append(dict(schema=original['schema'],case=label,rejected=str(exc)))
                else:raise AssertionError(f'mutation accepted: {module.__name__}/{label}')
            mutations=[('planned-float',['planned'],float(original['planned'])),('halted-bool',['halted'],False),
                       ('index-bool',['jobs',0,'index'],False),('approved-int',['jobs',0,'result','approved'],1),
                       ('word-float',['jobs',0,'result','output',0],float(original['jobs'][0]['result']['output'][0])),
                       ('binding-count-float',['jobs',0,'binding','count'],float(original['jobs'][0]['binding']['count']))]
            mutations += [('version-float',['version'],float(original['version']))] if module is s else [('version-float',['versions',0],float(original['versions'][0]))]
            if module is d:mutations += [('available-int',['output','available'],1),('final-word-float',['output','output',0],float(original['output']['output'][0]))]
            for label,parts,value in mutations:
                bad=copy.deepcopy(original);obj=bad
                for part in parts[:-1]:obj=obj[part]
                obj[parts[-1]]=value;reject(label,source,bad)
            for name in ['receipt.json','session.json','plan.json','jobs/00/dispatch.json']:
                with tempfile.TemporaryDirectory(prefix='raveil-evidence-audit-') as tmp:
                    root=Path(tmp)/'copy';shutil.copytree(source,root);path=root/name
                    text=path.read_text();key=next(iter(loads(text)))
                    path.write_text('{'+json.dumps(key)+':null,'+text[1:])
                    if name!='receipt.json':
                        bad=copy.deepcopy(original);bad['files'][name]=digest(path);(root/'receipt.json').write_bytes(p.encoded(bad))
                    reject('duplicate-'+name,root)
            module.verify(source)
    return dict(evidence_class='saved-functional-evidence-revalidation',records=records,probes=probes,skipped=skipped,
                verified=len(records),processed=sum(row['processed'] for row in records),rejected=len(probes))


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',action='append',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();result=audit(args.root)
    with args.output.open('x') as out:json.dump(result,out,indent=2);out.write('\n')
    print(json.dumps({key:result[key] for key in ('verified','processed','rejected')}))


if __name__=='__main__':main()
