"""Host-only bridge proof fixtures; no QEMU/RTL process is executed."""
import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from raveil import fold_bridge as b,project as p
from raveil.sonatine_fold import command_for
from scripts.affine_fold_vectors import vectors


def fixture(root):
    case=vectors()[0];descriptor=case['descriptor'];inputs=case['inputs'];expected=case['expected'];rid=7
    request=b.request_bytes(case['config'],inputs,rid);binding=dict(request_id=rid,epoch=rid,sequence=1,cookie='12'*16,count=len(expected))
    response,wire=b.injected_response(binding,expected,'none')
    stdout=('RAVEIL-FOLD-DISPATCH-V1 request=0000000000000007 epoch=0000000000000007 sequence=0000000000000001 cookie='+binding['cookie']+' count=1 envelope='+request.hex()+'\n'+
            '>'*len(wire)+'\nRAVEIL-FOLD-BRIDGE-STATE-V1 stable=1 objects=1 version=2 inflight=0 shadows=0 completions=0\n'+
            'RAVEIL-FOLD-RESULT-V1 request=0000000000000007 status=1 approved=1 epoch=7 sequence=1 cookie='+binding['cookie']+' chunks=1 version=2 count=1 output='+f'{expected[0]:08x}'+'\n')
    docs={'region.json':descriptor,'inputs.json':inputs,'command.json':command_for('/test/qemu',root),'dispatch.json':binding}
    for name,value in docs.items():(root/name).write_bytes(p.encoded(value))
    for name,value in {'kernel.elf':b'HOST FIXTURE','request.bin':request,'response.bin':response,'wire.txt':wire,'stdout.log':stdout.encode(),'stderr.log':b'','qemu-version.txt':b'HOST FIXTURE'}.items():(root/name).write_bytes(value)
    project=p.Project(p.init_project(root/'project'));saved=project.root/'folds/fixture';saved.mkdir(parents=True)
    (saved/'region.json').write_bytes(p.encoded(descriptor));(saved/'input.json').write_bytes(p.encoded(dict(schema='raveil.fold-input/v1',buffers=inputs)))
    record=dict(schema='raveil.fold-bridge.v1',evidence_class='host-mediated-QEMU-RTL-functional-coupling',request_id=rid,injection='none',rtl_id='fixture',
                result=b.parse(stdout,rid,len(expected)),files={name:b.digest(root/name) for name in b.FILES})
    (root/'receipt.json').write_bytes(p.encoded(record))
    return record,dict(id='fixture',status='succeeded',output=expected)


class BridgeEvidenceTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);self.root=Path(tmp.name)
        self.record,rtl=fixture(self.root)
        self.load=patch.object(b.f,'load',return_value=rtl);self.load.start();self.addCleanup(self.load.stop)
        self.proc=patch('subprocess.Popen',side_effect=AssertionError('saved verification executed'));self.proc.start();self.addCleanup(self.proc.stop)
        self.assertEqual(b.verify(self.root),self.record)
    def test_result_boolean_integer_float_substitution_rejected(self):
        for key in ['approved','status','epoch','sequence','chunks','version','output']:
            for convert in [float,bool,int]:
                changed=copy.deepcopy(self.record);old=changed['result'][key]
                if key=='output':new=[convert(x) for x in old]
                else:new=convert(old)
                if type(old) is type(new) and (key!='output' or all(type(x) is type(y) for x,y in zip(old,new))):continue
                changed['result'][key]=new
                with self.subTest(key=key,convert=convert),self.assertRaises(ValueError):b._verify_record(self.root,changed)
    def test_dispatch_coercion_rejected_after_rehash(self):
        path=self.root/'dispatch.json';original=path.read_bytes()
        for key in ['sequence','count']:
            for changed in [True,1.0]:
                dispatch=json.loads(original);dispatch[key]=changed;path.write_bytes(p.encoded(dispatch))
                record=copy.deepcopy(self.record);record['files']['dispatch.json']=b.digest(path)
                with self.subTest(key=key,value=changed),self.assertRaises(ValueError):b._verify_record(self.root,record)
        path.write_bytes(original)
    def test_duplicate_fields_rejected_after_rehash(self):
        for name,key in [('receipt.json','schema'),('dispatch.json','sequence'),('region.json','fold')]:
            path=self.root/name;raw=path.read_bytes();value=json.loads(raw)
            text='{'+json.dumps(key)+':'+json.dumps(value[key])+','+raw.decode().lstrip()[1:];path.write_text(text)
            record=copy.deepcopy(self.record)
            if name!='receipt.json':record['files'][name]=b.digest(path);(self.root/'receipt.json').write_bytes(p.encoded(record))
            with self.subTest(name=name),self.assertRaises(ValueError):b.verify(self.root)
            path.write_bytes(raw);(self.root/'receipt.json').write_bytes(p.encoded(self.record))
    def test_malformed_receipt_and_command_types_reject_cleanly(self):
        for field,value in [('injection',[]),('files',None),('rtl_id',True),('result',None)]:
            bad=copy.deepcopy(self.record);bad[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):b._verify_record(self.root,bad)
        with self.assertRaises(ValueError):b._verify_record(self.root,None)
        path=self.root/'command.json';command=json.loads(path.read_bytes());command[0]=None;path.write_bytes(p.encoded(command))
        record=copy.deepcopy(self.record);record['files']['command.json']=b.digest(path)
        with self.assertRaises(ValueError):b._verify_record(self.root,record)
    def test_json_field_order_remains_irrelevant(self):
        record={key:self.record[key] for key in reversed(self.record)};(self.root/'receipt.json').write_text(json.dumps(record))
        self.assertEqual(b.verify(self.root),record)
