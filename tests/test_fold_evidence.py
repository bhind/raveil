"""Host transcript fixtures; RTL loading is mocked, protocol checks are real."""
import copy
import json
import shutil
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from raveil import fold_evidence as e, fold_session as s, fold_chain as c, fold_dag as d
from raveil import project as p, fold_bridge as b
from raveil.sonatine_fold import command_for, digest
from scripts.fold_dag_cases import job, graph


def fixture(module, root):
    j=job('answer',1);session={'schema':f'raveil.fold-{module.__name__.split("_")[-1]}.v1','jobs':[j]}
    if module is d:session=graph([j])
    expected=module.reference(j['region'],j['inputs']);envelope,requests=module.encode(session,99,[2])
    request=requests[0];cookie='12'*16
    dispatch=('RAVEIL-FOLD-DISPATCH-V1 request=0000000000000002 epoch=0000000000000063 '
              f'sequence=0000000000000001 cookie={cookie} count=1 envelope={request.hex()}')
    binding=b.dispatch(dispatch,request,2,1,epoch=99,sequence=1)
    response,wire=s.reply(binding,expected,'none',None)
    suffix=module.__name__.split('_')[-1].upper();prefix=f'RAVEIL-FOLD-{suffix}'
    common='index=0 stable=1 framed=1 '
    if module is s:
        content=expected+[0]*255;tail='version=2';start=f'{prefix}-START-V1 epoch=0000000000000063 jobs=1 version=1'
        state=common+'version=2 ';result_extra='version=2 '
    else:
        model=module.State(session);_,source,destination=model.resolve(0)
        model.commit(0,destination,expected,True)
        content=[v for bank in model.banks for v in bank];tail='versions='+model.version_text()
        start=(d.start_line(session,99) if module is d else f'{prefix}-START-V1 epoch=0000000000000063 jobs=1 versions=1,1')
        state=common+(f'writes={destination} reads={source} ' if module is d else f'destination={destination} source={source} ')+tail+' '
        result_extra='' if module is d else 'version=2 '
    state+= 'ledger=1 submissions=0 inflight=0 shadows=0 completions=0 content='+''.join(f'{v:08x}' for v in content)
    result=(f'{prefix}-RESULT-V1 index=0 request=0000000000000002 epoch=0000000000000063 '
            f'sequence=1 cookie={cookie} status=1 approved=1 {result_extra}count=1 output={expected[0]:08x}')
    step=[dispatch,'>'*len(wire),f'{prefix}-STATE-V1 '+state,result]
    if module is s:checked,out,_=s.check_step(step,0,request,2,99,expected,wire,'none',1,[0]*256)
    else:checked,out=module.check_step(step,0,request,2,99,expected,wire,'none',module.State(session),source,destination)
    lines=[start]+step+([model.final_line()] if module is d else [])+[f'{prefix}-END-V1 epoch=0000000000000063 processed=1 total=1 halted=0 {tail}']
    root.mkdir(exist_ok=True);jr=root/'jobs/00';jr.mkdir(parents=True);p.init_project(root/'project')
    documents={'session.json':session,'plan.json':dict(schema=f'raveil.fold-{suffix.lower()}-plan.v1',epoch=99,request_ids=[2],injections=['none'],build_sha256='0'*64),
               'command.json':command_for('/test/qemu',root),'jobs/00/dispatch.json':binding}
    for name,value in documents.items():(root/name).write_bytes(p.encoded(value))
    for name,value in {'kernel.elf':b'host-fixture','request.bin':envelope,'jobs/00/request.bin':request,'jobs/00/response.bin':response,'jobs/00/wire.txt':wire}.items():(root/name).write_bytes(value)
    (root/'stdout.log').write_text('\n'.join(lines)+'\n');(root/'stderr.log').write_text('');(root/'qemu-version.txt').write_text('host fixture')
    receipt=dict(schema=f'raveil.fold-{suffix.lower()}-run.v1',evidence_class=module.CLASS,epoch=99,processed=1,planned=1,halted=0,
                 jobs=[dict(index=0,name='answer',rtl_id='fixture',binding=checked,result=out)],files={name:digest(root/name) for name in module.files_for(1)})
    if module is s:receipt['version']=2
    else:receipt['versions']=model.versions
    if module is d:receipt['output']=model.final()
    (root/'receipt.json').write_bytes(p.encoded(receipt))
    return receipt,expected


class EvidenceTests(unittest.TestCase):
    def test_strict_json_and_type_sensitive_trees(self):
        self.assertTrue(e.same(e.loads('{"b":[true,null],"a":2}'),{'a':2,'b':[True,None]}))
        for text in ['{"a":1,"a":1}','{"a":{"x":1,"x":2}}','[1.0]','1e0','NaN','Infinity','-Infinity']:
            with self.subTest(text=text),self.assertRaises(ValueError):e.loads(text)
        for a,bv in [(True,1),(False,0),(1.,1),([1],[True]),({'x':0},{'x':False}),((1,),[1]),(float('nan'),float('nan'))]:
            self.assertFalse(e.same(a,bv))
    def each(self,check):
        for module in [s,c,d]:
            with self.subTest(module=module.__name__),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);receipt,expected=fixture(module,root)
                with patch.object(module.f,'load',return_value={}),patch.object(module,'rtl_values',return_value=expected),patch('subprocess.Popen',side_effect=AssertionError('must not execute')):
                    self.assertEqual(module.verify(root),receipt);check(module,root,receipt)
    def test_reconstructed_fields_reject_type_substitution(self):
        def check(module,root,receipt):
            paths=[['epoch'],['planned'],['halted'],['jobs',0,'index'],['jobs',0,'binding','count'],['jobs',0,'result','status'],['jobs',0,'result','approved'],['jobs',0,'result','output',0]]
            paths += [['version']] if module is s else [['versions',0]]
            if module is d:paths += [['output','index'],['output','available'],['output','output',0],['output','objects',0,'generation']]
            for path in paths:
                for conversion in [float,bool,int]:
                    bad=copy.deepcopy(receipt);obj=bad
                    for key in path[:-1]:obj=obj[key]
                    before=obj[path[-1]];after=conversion(before)
                    if type(before) is type(after):continue
                    obj[path[-1]]=after
                    with self.subTest(path=path,conversion=conversion),self.assertRaises(ValueError):module._verify(root,bad)
        self.each(check)
    def test_processed_count_cannot_exceed_declared_jobs(self):
        def check(module,root,receipt):
            shutil.copytree(root/'jobs/00',root/'jobs/01')
            bad=copy.deepcopy(receipt);bad['processed']=2;bad['jobs'].append(copy.deepcopy(bad['jobs'][0]))
            lines=(root/'stdout.log').read_text().splitlines();lines[5:5]=lines[1:5]
            (root/'stdout.log').write_text('\n'.join(lines)+'\n')
            bad['files']={name:digest(root/name) for name in module.files_for(2)}
            with self.assertRaisesRegex(ValueError,'processed count exceeds declared jobs'):module._verify(root,bad)
        self.each(check)
    def test_duplicate_fields_reject_even_with_updated_hashes(self):
        def check(module,root,receipt):
            for name in ['receipt.json','session.json','plan.json','jobs/00/dispatch.json']:
                path=root/name;original=path.read_bytes();value=json.loads(original);key=next(iter(value))
                changed=('{'+json.dumps(key)+':null,'+original.decode()[1:]).encode();path.write_bytes(changed)
                bad=copy.deepcopy(receipt)
                if name!='receipt.json':
                    bad['files'][name]=digest(path);(root/'receipt.json').write_bytes(p.encoded(bad))
                with self.subTest(name=name),self.assertRaises(ValueError):module.verify(root)
                path.write_bytes(original);(root/'receipt.json').write_bytes(p.encoded(receipt))
        self.each(check)
    def test_bad_container_types_and_command_items_fail_cleanly(self):
        def check(module,root,receipt):
            for value in [None,[],True,{'jobs':[]}]:
                with self.assertRaises(ValueError):module._verify(root,value)
            for key,value in [('jobs',{}),('files',[]),('jobs',[None]),('processed',True)]:
                bad=copy.deepcopy(receipt);bad[key]=value
                with self.assertRaises(ValueError):module._verify(root,bad)
            command=json.loads((root/'command.json').read_text());command[0]=None
            (root/'command.json').write_bytes(p.encoded(command));bad=copy.deepcopy(receipt);bad['files']['command.json']=digest(root/'command.json')
            with self.assertRaises(ValueError):module._verify(root,bad)
        self.each(check)


class AuditDiscoveryTests(unittest.TestCase):
    def test_duplicate_unknown_schema_cannot_hide_receipt(self):
        from scripts.fold_evidence_audit import audit
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/'receipt.json').write_text('{"schema":"raveil.fold-dag-run.v1","schema":"unknown"}')
            with self.assertRaisesRegex(ValueError,'duplicate'):audit([root])
            (root/'receipt.json').write_text('[]')
            with self.assertRaisesRegex(ValueError,'object'):audit([root])
