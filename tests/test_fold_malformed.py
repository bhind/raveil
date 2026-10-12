"""Malformed JSON must reject before dispatch or workspace mutation."""
import copy,contextlib,io,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from raveil import affine_fold as a,fold_dag as d,fold_session as s,project as p,project_dag_batch as batch
from raveil.cli import main
from scripts.fold_dag_cases import job,graph


def malformed():
    base=graph([job('a',1)])
    for schema in [[],{},True,None]:
        value=copy.deepcopy(base);value['schema']=schema;yield 'schema',value
    for name in [None,True,[],{},3]:
        value=copy.deepcopy(base);value['jobs'][0]['name']=name;yield 'name',value
    for region in [None,True,[],3,'region']:
        value=copy.deepcopy(base);value['jobs'][0]['region']=region;yield 'region',value
    for key in ['shape','lengths','nodes','views','result']:
        for invalid in [None,True,3,{},[]]:
            value=copy.deepcopy(base);value['jobs'][0]['region'][key]=invalid;yield key,value
    value=copy.deepcopy(base);value['jobs'][0]['region']['nodes']=[None];yield 'null-node',value
    for key,invalid in [('op',[]),('args',[[],'b']),('args',[{},'b']),('view',[]),('id',[])]:
        value=copy.deepcopy(base);node=value['jobs'][0]['region']['nodes'][0 if key in ('view','id') else 2];node[key]=invalid;yield key,value
    for invalid in [None,3,True,{'bad':1}]:
        value=copy.deepcopy(base);value['jobs'][0]['inputs'][0]=invalid;yield 'literal-buffer',value


class MalformedAdmissionTests(unittest.TestCase):
    def test_dag_and_shared_region_rejection(self):
        for label,value in malformed():
            with self.subTest(label=label,value=value),self.assertRaises(ValueError):d.validate(value)
    def test_session_uses_same_typed_region_and_names(self):
        for label,value in malformed():
            if label=='schema':continue
            session=dict(schema='raveil.fold-session.v1',jobs=value['jobs'])
            with self.subTest(label=label),self.assertRaises(ValueError):s.validate(session)
    def test_cli_batch_rejection_is_exit2_without_writes_or_processes(self):
        with tempfile.TemporaryDirectory() as tmp:
            project=p.Project(p.init_project(Path(tmp)/'project'))
            for label,dag in malformed():
                value=dict(schema=batch.INPUT,items=[dict(name='a',dag=dag)])
                (project.root/'inputs/bad.json').write_bytes(p.encoded(value));before=p.tree(project.root)
                for command in ['batch-check','batch-run']:
                    args=['project',command,'--project',str(project.root),'--input','bad.json']
                    if command=='batch-run':args+=['--kernel','unused.elf','--build','unused-runtime']
                    error=io.StringIO()
                    with self.subTest(label=label,command=command),patch('subprocess.Popen',side_effect=AssertionError('invalid input executed')),contextlib.redirect_stderr(error),contextlib.redirect_stdout(io.StringIO()):
                        self.assertEqual(main(args),2)
                    self.assertTrue(error.getvalue().startswith('error: '));self.assertNotIn('Traceback',error.getvalue());self.assertEqual(p.tree(project.root),before)
    def test_name_helper_rejects_non_text(self):
        for value in [None,True,[],{},3,b'a']:
            with self.assertRaises(ValueError):p.name(value)


class SavedDiscoveryTests(unittest.TestCase):
    def test_duplicate_schema_and_wrong_root_cannot_disappear_from_audit(self):
        from scripts.mf01_rejection_saved_audit import receipts
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);path=root/'receipt.json';schema='raveil.fold-dag-run.v1'
            for raw in ['{"schema":"raveil.fold-dag-run.v1","schema":"unknown"}','[]','{"schema":"unknown","n":1.0}']:
                path.write_text(raw)
                with self.assertRaises(ValueError):receipts(root,schema,1)
            path.write_bytes(p.encoded(dict(schema=schema)))
            self.assertEqual(receipts(root,schema,1),[root.resolve()])
            with self.assertRaises(ValueError):receipts(root,schema,2)
    def test_existing_direct_sequence_arguments_remain_supported(self):
        class Region(dict):pass
        region=Region(job('a',1)['region']);region['shape']=(1,1);region['lengths']=(1,1)
        self.assertEqual(a.reference(region,[(2,),range(3,4)]),[5])
        self.assertEqual(a.reference(region,[bytes([2]),bytearray([3])]),[5])
