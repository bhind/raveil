"""Pure data preparation and atomic new-file tests; no mocked execution evidence."""
import contextlib
import copy
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from raveil import array_input as i, array_program as a, project as p
from raveil.cli import main
from tests.test_array_program import program,source,gemm
from tests import test_project_dag_batch as fixtures
from scripts.prepare_array_app import prepare


class MatrixTests(unittest.TestCase):
    def test_unsigned_and_explicit_signed_extremes(self):
        self.assertEqual(i.literal([[0,0xffffffff]])['words'],[0,0xffffffff])
        self.assertEqual(i.literal([[-2147483648,-1,0,2147483647]],'i32')['words'],[0x80000000,0xffffffff,0,0x7fffffff])
        for dtype,values in [('u32',[-1,1<<32]),('i32',[-2147483649,2147483648])]:
            for value in values:
                with self.assertRaises(ValueError):i.literal([[value]],dtype)

    def test_no_implicit_types_or_irregular_matrix(self):
        bad=[None,[],[[]],[[1],[2,3]],[[True]],[[1.0]],[['1']],[(1,)],[[0]*65],[[0]]*65]
        for matrix in bad:
            with self.subTest(matrix=matrix),self.assertRaises(ValueError):i.literal(matrix)
        for dtype in (None,False,1,'float32',[],{}):
            with self.assertRaises(ValueError):i.literal([[1]],dtype)
        self.assertEqual(len(i.literal([[0]*64 for _ in range(64)])['words']),4096)

    def test_csv_bom_crlf_quotes_whitespace_and_signed(self):
        raw=b'\xef\xbb\xbf" 1 ",+2\r\n3,4\r\n'
        self.assertEqual(i.read_csv(raw),[[1,2],[3,4]])
        self.assertEqual(i.read_csv(b' '*(i.CSV_LIMIT-1)+b'1'),[[1]])
        self.assertEqual(i.read_csv(b'-2147483648,-1\n0,2147483647','i32'),[[-2147483648,-1],[0,2147483647]])

    def test_csv_strict_grammar_size_and_encoding(self):
        bad=[b'',b'\n',b'1\n\n',b'A,B\n1,2',b'1,',b'1,2\n3',b'0x10',b'1e2',b'1.0',b'True',b'1;2',b'"1',b'1\x00',b'\xff',b'1'*11,b'0'*(i.CSV_LIMIT+1),b'1\n'*65,b','.join([b'1']*65)]
        for raw in bad:
            with self.subTest(raw=raw[:20]),self.assertRaises(ValueError):i.read_csv(raw)
        for raw in ('1,2',bytearray(b'1')):
            with self.assertRaises(ValueError):i.read_csv(raw)
        with self.assertRaises(ValueError):i.read_csv(b'-1')
        with self.assertRaises(ValueError):i.read_csv(b'2147483648','i32')

    def test_v1_and_v2_full_admission_source_and_matrix_immutable(self):
        for schema in (a.SCHEMA,a.SCHEMA_V2):
            value=gemm(2,2,3);value['schema']=schema;before=copy.deepcopy(value)
            matrix=[[1,2,3],[4,5,6]];original=copy.deepcopy(matrix)
            prepared=i.replace_literal(value,'answer',0,matrix)
            prepared=i.replace_literal(prepared,'answer',1,[[7,8],[9,10],[11,12]])
            self.assertEqual(a.reference(prepared)[0]['words'],[58,64,139,154]);a.compile(prepared)
            self.assertEqual(value,before);self.assertEqual(matrix,original)
            prepared['stages'][0]['source']['inputs'][0]['words'][0]=99
            self.assertEqual(value,before);self.assertEqual(matrix,original)

    def test_shape_follows_operand_but_computation_and_boundaries_stay(self):
        value=program();before=copy.deepcopy(value)
        prepared=i.replace_literal(value,'answer',0,[[10]])
        self.assertEqual(prepared['stages'][0]['source']['shape'],[2,3])
        self.assertEqual(prepared['stages'][0]['source']['kernel'],before['stages'][0]['source']['kernel'])
        self.assertEqual(a.reference(prepared)[0]['words'],[13,3,3,3,3,3])
        self.assertEqual(value,before)

    def test_target_rejection_and_link_cannot_be_replaced(self):
        value=program();linked=source();linked['inputs']=[{'from':'answer'}]
        value['stages'].append(dict(name='later',source=linked));before=copy.deepcopy(value)
        for stage,slot in [('missing',0),([],0),('answer',True),('answer',-1),('answer',1),('later',0)]:
            with self.assertRaises(ValueError):i.replace_literal(value,stage,slot,[[1]])
        self.assertEqual(value,before)
        with self.assertRaises(ValueError):i.replace_literal({'schema':'invalid'},'answer',0,[[1]])

    def test_full_program_resource_rejection_after_replacement(self):
        # Fifteen full planes plus a small literal fit; expanding the last crosses
        # the real global limit without changing output shape or computation.
        value=program(source(1,1));large=dict(schema='raveil.grid-input/v2',rows=64,columns=64,words=[0]*4096)
        value['stages'][0]['source']['inputs']=[copy.deepcopy(large) for _ in range(8)]
        second=source(1,1);second['inputs']=[copy.deepcopy(large) for _ in range(7)]+[dict(schema='raveil.grid-input/v2',rows=1,columns=1,words=[0])]
        value['stages'].append(dict(name='second',source=second));a.compile(value);before=copy.deepcopy(value)
        with self.assertRaisesRegex(ValueError,'plane'):i.replace_literal(value,'second',7,[[0]*64 for _ in range(64)])
        self.assertEqual(value,before)


class ImportTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.project=p.Project(p.init_project(self.root/'workspace'));self.value=program();self.value['schema']=a.SCHEMA_V2
        self.path=self.project.root/'inputs/program.json';self.path.write_bytes(p.encoded(self.value))
        self.csv=self.root/'data.csv';self.csv.write_bytes(b'10,20,30\r\n40,50,60\r\n');self.original_names=self.names()
    def execute(self,**kw):
        args=dict(project=self.project,input_file='program.json',output_file='new.json',stage='answer',slot=0,csv_file=self.csv)
        return i.import_csv(**(args|kw))
    def names(self):return sorted(x.name for x in (self.project.root/'inputs').iterdir())

    def test_import_is_readonly_to_source_preserves_raw_hash_and_no_execution(self):
        before=p.tree(self.project.root)
        with patch('subprocess.Popen',side_effect=AssertionError('import executed')):receipt=self.execute()
        self.assertEqual(receipt['csv_sha256'],p.digest(self.csv.read_bytes()))
        self.assertEqual(receipt['source_sha256'],p.digest(self.path.read_bytes()))
        self.assertEqual(receipt['output_sha256'],p.digest((self.path.parent/'new.json').read_bytes()))
        after=p.tree(self.project.root);self.assertEqual(set(after)-set(before),{'/inputs/new.json'})
        self.assertTrue(all(after[key]==value for key,value in before.items()))
        self.assertEqual(a.reference(json.loads((self.path.parent/'new.json').read_bytes()))[0]['words'],[13,23,33,43,53,63])

    def test_invalid_input_filename_slot_csv_and_bounds_create_nothing(self):
        before=p.tree(self.project.root)
        for kw in ({'stage':'missing'},{'slot':9},{'input_file':'../program.json'},{'output_file':'../new.json'},{'output_file':'a/b.json'},{'output_file':True},{'dtype':'float32'}):
            with self.assertRaises((OSError,ValueError)):self.execute(**kw)
            self.assertEqual(p.tree(self.project.root),before)
        for raw in (b'header',b'x'*(i.CSV_LIMIT+1),b'\xff'):
            self.csv.write_bytes(raw)
            with self.assertRaises((OSError,ValueError)):self.execute()
            self.assertEqual(p.tree(self.project.root),before)

    def test_existing_symlink_directory_and_source_collision_preserved(self):
        for kind in ('file','symlink','directory'):
            target=self.path.parent/'new.json'
            if kind=='file':target.write_bytes(b'keep')
            elif kind=='symlink':target.symlink_to(self.csv)
            else:target.mkdir()
            with self.assertRaises(ValueError):self.execute()
            if kind=='directory':target.rmdir()
            else:target.unlink()
        with self.assertRaises(ValueError):self.execute(output_file='program.json')
        self.assertEqual(json.loads(self.path.read_bytes()),self.value)
        other=self.root/'link.csv';other.symlink_to(self.csv)
        with self.assertRaises((OSError,ValueError)):self.execute(csv_file=other)
        raw=self.path.read_bytes();self.path.unlink();self.path.symlink_to(self.csv)
        with self.assertRaises((OSError,ValueError)):self.execute()
        self.assertEqual(self.names(),self.original_names)

    def test_racing_destination_never_overwritten(self):
        link=os.link
        def race(src,dst,**kw):Path(dst).write_bytes(b'other writer');return link(src,dst,**kw)
        with patch.object(i.os,'link',side_effect=race),self.assertRaises(FileExistsError):self.execute()
        self.assertEqual((self.path.parent/'new.json').read_bytes(),b'other writer')
        self.assertEqual(self.names(),sorted([*self.original_names,'new.json']))

    def test_interrupted_partial_write_and_precommit_leave_no_output(self):
        write=p.write_new
        def partial(path,data,created):write(path,data[:12],created);raise KeyboardInterrupt()
        for context in (patch.object(p,'write_new',side_effect=partial),patch.object(i.os,'link',side_effect=KeyboardInterrupt())):
            with context,self.assertRaises(KeyboardInterrupt):self.execute()
            self.assertEqual(self.names(),self.original_names);self.assertEqual(json.loads(self.path.read_bytes()),self.value)

    def test_partial_os_write_failure_cleans_own_pending_file(self):
        write=os.write;calls=[]
        def fail(fd,data):
            calls.append(len(data))
            if len(calls)==1:return write(fd,data[:7])
            raise OSError('injected full disk')
        with patch.object(p.os,'write',side_effect=fail),self.assertRaises(OSError):self.execute()
        self.assertEqual(len(calls),2);self.assertEqual(self.names(),self.original_names)
        self.assertEqual(json.loads(self.path.read_bytes()),self.value)

    def test_compiler_rejection_before_publication_keeps_workspace_unchanged(self):
        before=p.tree(self.project.root);original=a.compile;calls=[]
        def reject(value):
            calls.append(value)
            if len(calls)==2:raise ValueError('admission rejected replacement')
            return original(value)
        with patch.object(a,'compile',side_effect=reject),self.assertRaisesRegex(ValueError,'admission'):
            self.execute()
        self.assertEqual(len(calls),2);self.assertEqual(p.tree(self.project.root),before)

    def test_interrupt_after_commit_keeps_complete_admitted_file(self):
        link=os.link
        def committed(*args,**kwargs):link(*args,**kwargs);raise KeyboardInterrupt()
        with patch.object(i.os,'link',side_effect=committed),self.assertRaises(KeyboardInterrupt):self.execute()
        value=json.loads((self.path.parent/'new.json').read_bytes());a.compile(value)
        self.assertEqual(value['stages'][0]['source']['inputs'][0]['words'],[10,20,30,40,50,60])
        self.assertEqual(self.names(),sorted([*self.original_names,'new.json']))

    def test_cli_success_errors_and_interrupt_codes(self):
        argv=['project','array-import','--project',str(self.project.root),'--stage','answer','--slot','0','--csv',str(self.csv),'--output','new.json']
        out=io.StringIO()
        with contextlib.redirect_stdout(out):self.assertEqual(main(argv),0)
        self.assertEqual(json.loads(out.getvalue())['output_file'],'new.json')
        with contextlib.redirect_stderr(io.StringIO()):self.assertEqual(main(argv),2)
        with patch.object(i,'import_csv',side_effect=KeyboardInterrupt()),contextlib.redirect_stderr(io.StringIO()):self.assertEqual(main(argv),130)
        self.assertFalse((self.project.root/'arrays').exists())


class PackagedImportTests(unittest.TestCase):
    save=fixtures.BatchTests.save
    def setUp(self):fixtures.BatchTests.setUp(self)
    def test_relocated_app_import_then_check_without_runtime_execution(self):
        app=self.root/'app';prepare(app,self.kernel,self.build);moved=self.root/'moved app';app.rename(moved)
        data=self.root/'data.csv';data.write_text('10,20,30\n40,50,60\n')
        before=p.tree(moved/'engine');source=(moved/'workspace/inputs/program.json').read_bytes()
        result=subprocess.run([str(moved/'raveil'),'array-import','--stage','first','--slot','0','--csv',str(data),'--output','new.json'],cwd=self.root,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr);self.assertEqual(json.loads(result.stdout)['output_file'],'new.json')
        result=subprocess.run([str(moved/'raveil'),'array-check','--input','new.json'],cwd=self.root,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(before,p.tree(moved/'engine'));self.assertEqual(source,(moved/'workspace/inputs/program.json').read_bytes())
        self.assertFalse((moved/'workspace/arrays').exists())

if __name__=='__main__':unittest.main()
