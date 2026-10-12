"""Batch host fixtures; mocked child verification is not actual coupled evidence."""
import copy,json,os,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from raveil import project as p,project_dag_batch as b,project_fold as f,fold_dag as d
from scripts.fold_dag_cases import job,graph,linked
from tests import test_project_dag as fixtures


class BatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.project=p.Project(p.init_project(self.root/'workspace'))
        self.batch={'schema':b.INPUT,'items':[{'name':f'item-{i}','dag':graph([job('a',1,[[i],[3]]),job('b',1,linked('a'))])} for i in range(3)]};self.save()
        self.kernel=self.root/'kernel.elf';self.kernel.write_bytes(b'HOST FIXTURE')
        self.build=self.root/'build';(self.build/'source').mkdir(parents=True)
        for name in f.SOURCES:shutil.copyfile(p.REPOSITORY/'hardware/chisel'/name,self.build/'source'/name)
        (self.build/'simulator.bin').write_bytes(b'HOST FIXTURE');(self.build/'toolchain.txt').write_text('host fixture')
        (self.build/'rtl').mkdir();(self.build/'rtl/fixture.sv').write_text('host fixture');f.seal_build(self.build)
        self.mockverify=patch.object(d,'verify',side_effect=lambda root:json.loads((Path(root)/'receipt.json').read_text())).start();self.addCleanup(patch.stopall)
    def save(self):(self.project.root/'inputs/batch.json').write_bytes(p.encoded(self.batch))
    def fake(self,*args,**kw):return fixtures.ProjectDagTests.fake(self,*args,**kw)
    def run_fixture(self,executor=None):
        with patch.object(d,'run',side_effect=executor or self.fake):return b.run(self.project,'batch.json',self.kernel,self.build)
    def reseal(self,r):
        root=self.project.root/'batches'/r['id'];r['files']=b._inventory(root);raw=p.encoded(r)
        (root/'record.json').write_bytes(raw);(root/'record.sha256').write_text(p.digest(raw)+'\n')
    def test_readonly_preview_admits_all_and_boundaries(self):
        before=p.tree(self.project.root);preview=b.check(self.project,'batch.json');self.assertEqual(preview['jobs'],6);self.assertEqual(before,p.tree(self.project.root))
        for count in [0,17]:
            value={'schema':b.INPUT,'items':[dict(name=f'i{i}',dag=graph([job('a',1)])) for i in range(count)]}
            with self.assertRaises(ValueError):b.validate(value)
        maximum={'schema':b.INPUT,'items':[dict(name=f'i{i}',dag=graph([job(f'j{k}',1) for k in range(8)])) for i in range(16)]}
        self.assertEqual(b.preview(maximum)['jobs'],128)
        self.batch['items'][-1]['dag']['jobs'][0]['inputs']=[{'from':'missing'},[3]];self.save()
        with patch.object(d,'run',side_effect=AssertionError('no dispatch')),self.assertRaises(ValueError):b.run(self.project,'batch.json',self.kernel,self.build)
        self.assertFalse((self.project.root/'batches').exists())
    def test_names_paths_duplicate_json_and_size_reject(self):
        for name in ['../outside','bad/name',True]:
            value=copy.deepcopy(self.batch);value['items'][0]['name']=name
            with self.assertRaises(ValueError):b.validate(value)
        value=copy.deepcopy(self.batch);value['items'][1]['name']=value['items'][0]['name']
        with self.assertRaises(ValueError):b.validate(value)
        source=self.project.root/'inputs/batch.json';source.write_text('{"schema":null,"schema":"raveil.dag-batch.v1","items":[]}')
        with self.assertRaises(ValueError):b.check(self.project,'batch.json')
        source.write_bytes(b' '*(b.INPUT_LIMIT+1))
        with self.assertRaises(ValueError):b.check(self.project,'batch.json')
        source.unlink();source.symlink_to(self.kernel)
        with self.assertRaises(ValueError):b.check(self.project,'batch.json')
    def test_capture_saved_history_diff_and_no_original_executables(self):
        first=self.run_fixture();self.assertEqual([o['words'] for o in first['outputs']],[[6],[8],[10]])
        self.batch['items'][1]['dag']['jobs'][0]['inputs'][0]=[7];self.save();second=self.run_fixture()
        self.kernel.unlink();shutil.rmtree(self.build)
        with patch('subprocess.Popen',side_effect=AssertionError('must not execute')):
            self.assertEqual(b.load(self.project,first['id']),first);self.assertEqual(len(b.history(self.project)),2)
            diff=b.compare(self.project,first['id'],second['id']);self.assertEqual(diff['changed_cells'],1);self.assertEqual(diff['items'][1]['first_change'],dict(index=0,before=8,after=20))
    def test_live_source_edits_after_capture_do_not_change_later_children(self):
        calls=[]
        def run(*args):
            calls.append(args);(self.project.root/'inputs/batch.json').write_text('changed');self.kernel.write_bytes(b'changed')
            return self.fake(*args)
        r=self.run_fixture(run);self.assertEqual(len(calls),3);self.assertEqual([o['words'] for o in r['outputs']],[[6],[8],[10]])
    def test_incomplete_pinned_child_stops_prefix_and_hides_all_outputs(self):
        self.batch['items'][1]['dag']=graph([job('answer',1),job('later',1)],'answer');self.save();calls=[]
        def run(*args):
            index=len(calls);calls.append(args);return self.fake(*args,failed=1 if index==1 else None)
        r=self.run_fixture(run);self.assertEqual(len(calls),2);self.assertEqual(r['status'],'incomplete');self.assertIsNone(r['outputs'])
        root=self.project.root/'batches'/r['id'];child=json.loads((root/'children/01/receipt.json').read_text());self.assertTrue(child['output']['available'])
        self.assertFalse((root/'children/02').exists());self.assertEqual(b.load(self.project,r['id']),r)
        with self.assertRaises(ValueError):b.compare(self.project,r['id'],r['id'])
    def test_exception_interrupt_and_cleanup_uncertain_remain_unsealed(self):
        for error in [ValueError('execution failed'),KeyboardInterrupt(),f.CleanupUncertain('writer unknown')]:
            with patch.object(d,'run',side_effect=error),self.assertRaises(type(error)):b.run(self.project,'batch.json',self.kernel,self.build)
        self.assertEqual([r['status'] for r in b.history(self.project)],['unsealed']*3)
    def test_saved_prefix_omission_reorder_and_extra_directory_reject(self):
        for case in ['omit','reorder','extra','after-incomplete']:
            r=self.run_fixture();root=self.project.root/'batches'/r['id']
            if case=='omit':r['children']=r['children'][:-1];r['attempted']=2
            elif case=='reorder':r['children'].reverse()
            elif case=='extra':(root/'children/03').mkdir()
            else:
                path=root/'children/01/receipt.json';child=json.loads(path.read_text());child['jobs'][-1]['result']['approved']=False;path.write_bytes(p.encoded(child))
                r['children'][1]=b._entry(path.parent,1,self.batch['items'][1],child);r['status']='incomplete';r['outputs']=None
            self.reseal(r)
            with self.subTest(case=case),self.assertRaises(ValueError):b.load(self.project,r['id'])
    def test_rehashed_source_kernel_build_output_and_counter_tamper_reject(self):
        for case in ['source','kernel','build','word','counter','preview','symlink']:
            r=self.run_fixture();root=self.project.root/'batches'/r['id']
            if case=='source':
                path=root/'children/00/session.json';v=json.loads(path.read_text());v['jobs'][0]['inputs'][0][0]=77;path.write_bytes(p.encoded(v))
            elif case=='kernel':(root/'children/00/kernel.elf').write_bytes(b'changed')
            elif case=='build':
                path=root/'children/00/plan.json';v=json.loads(path.read_text());v['build_sha256']='f'*64;path.write_bytes(p.encoded(v))
            elif case=='word':r['outputs'][0]['words']=[6.0]
            elif case=='counter':r['attempted']=3.0
            elif case=='preview':
                path=root/'plan.json';v=json.loads(path.read_text());v['preview']['jobs']=6.0;path.write_bytes(p.encoded(v))
            else:
                path=root/'children/00/kernel.elf';path.unlink();path.symlink_to(self.kernel)
                with self.assertRaises(ValueError):b.load(self.project,r['id'])
                continue
            self.reseal(r)
            with self.subTest(case=case),self.assertRaises(ValueError):b.load(self.project,r['id'])
    def test_before_after_publication_interrupt_and_no_overwrite(self):
        link=os.link
        for after in [False,True]:
            def publish(src,dst):
                if after:link(src,dst)
                raise KeyboardInterrupt()
            with patch.object(b.os,'link',side_effect=publish):
                if after:self.assertEqual(self.run_fixture()['status'],'succeeded')
                else:
                    with self.assertRaises(KeyboardInterrupt):self.run_fixture()
        with patch.object(b.os,'link',side_effect=FileExistsError('existing')),self.assertRaises(FileExistsError):self.run_fixture()
    def test_diff_rejects_layout_and_executable_mismatch(self):
        first=self.run_fixture();self.batch['items'][0]['name']='renamed';self.save();second=self.run_fixture()
        with self.assertRaises(ValueError):b.compare(self.project,first['id'],second['id'])
        self.batch['items'][0]['name']='item-0';self.save();self.kernel.write_bytes(b'other kernel');third=self.run_fixture()
        with self.assertRaises(ValueError):b.compare(self.project,first['id'],third['id'])
    def test_cli_preview(self):
        result=subprocess.run([sys.executable,'-m','raveil','project','batch-check','--project',str(self.project.root),'--input','batch.json'],capture_output=True,text=True,check=True)
        self.assertEqual(json.loads(result.stdout)['independent_sessions'],3)


class TreeBudgetTests(unittest.TestCase):
    def test_seal_files_excluded_before_budget_but_nested_records_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'data').write_bytes(b'x')
            with patch.object(b,'MAX_BYTES',1),patch.object(b,'MAX_ENTRIES',1):
                expected=b._inventory(root)
                for name in ['record.json','record.sha256','.record.pending']:(root/name).write_bytes(b'y'*100)
                self.assertEqual(b._inventory(root),expected)
                (root/'child').mkdir();(root/'child/record.json').write_bytes(b'x')
                with self.assertRaises(ValueError):b._inventory(root)
    def test_limits_are_typed_bounded_and_defaults_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'data').write_bytes(b'ab')
            for kwargs in [dict(max_bytes=True),dict(max_entries=0),dict(max_bytes=128*1024*1024+1),dict(max_entries=16385),dict(exclude_root_files=frozenset({'data'}))]:
                with self.assertRaises(ValueError):p.tree(root,**kwargs)
            with self.assertRaises(ValueError):p.tree(root,max_bytes=1)
            self.assertEqual(p.tree(root,max_bytes=2,max_entries=1),{'/data':p.digest(b'ab')})
            with self.assertRaises(ValueError):p.tree(root,root/'copy',exclude_root_files=frozenset({'record.json'}))
    def test_excluded_root_symlinks_and_directories_reject(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'data').write_text('x');(root/'record.json').symlink_to(root/'data')
            with self.assertRaises(ValueError):b._inventory(root)
            (root/'record.json').unlink();(root/'record.json').mkdir()
            with self.assertRaises(ValueError):b._inventory(root)
