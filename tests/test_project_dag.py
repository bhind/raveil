"""Adapter host fixtures; mocked child verification is not QEMU/RTL evidence."""
import copy,json,os,shutil,subprocess,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from raveil import project as p,project_fold as f,project_dag as a,fold_dag as d
from scripts.fold_dag_cases import job,graph,linked


class ProjectDagTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.project=p.Project(p.init_project(self.root/'project'));self.session=graph([job('a',1,[[3],[5]]),job('b',1,linked('a'))]);self.save()
        self.kernel=self.root/'kernel.elf';self.kernel.write_bytes(b'HOST FIXTURE NOT ELF')
        self.build=self.root/'build';(self.build/'source').mkdir(parents=True)
        for name in f.SOURCES:shutil.copyfile(p.REPOSITORY/'hardware/chisel'/name,self.build/'source'/name)
        (self.build/'simulator.bin').write_bytes(b'HOST FIXTURE NOT RTL');(self.build/'toolchain.txt').write_text('host fixture')
        (self.build/'rtl').mkdir();(self.build/'rtl/fixture.sv').write_text('host fixture');f.seal_build(self.build)
        self.mockverify=patch.object(d,'verify',side_effect=lambda root:json.loads((Path(root)/'receipt.json').read_text())).start()
        self.addCleanup(patch.stopall)
    def save(self):
        (self.project.root/'inputs/dag.json').write_bytes(p.encoded(self.session))
    def fake(self,session,kernel,build,destination,*,failed=None):
        root=Path(destination);root.mkdir();(root/'session.json').write_bytes(p.encoded(session));shutil.copyfile(kernel,root/'kernel.elf')
        (root/'plan.json').write_bytes(p.encoded({'build_sha256':f.verify_build(build)}))
        m=d.State(session);rows=[];halted=0
        for i in range(len(session['jobs'])):
            resolved=m.resolve(i)
            if resolved is None:halted=3;break
            j,reads,writes=resolved;expected=d.reference(j['region'],j['inputs']);ok=i!=failed;m.commit(i,writes,expected,ok)
            rows.append({'result':{'approved':ok}})
        receipt={'processed':len(rows),'planned':len(session['jobs']),'halted':halted,'jobs':rows,'output':m.final()}
        (root/'receipt.json').write_bytes(p.encoded(receipt));return receipt
    def run_fixture(self,**kwargs):
        with patch.object(d,'run',side_effect=lambda *args:self.fake(*args,**kwargs)):
            return a.run(self.project,'dag.json',self.kernel,self.build)
    def reseal(self,r):
        root=self.project.root/'dags'/r['id'];r['files']=a._inventory(root);payload=p.encoded(r)
        (root/'record.json').write_bytes(payload);(root/'record.sha256').write_text(p.digest(payload)+'\n')
    def test_preview_readonly_and_large_literal_json(self):
        before=p.tree(self.project.root);self.assertEqual(a.check(self.project,'dag.json')['evidence_class'],'static-admission');self.assertEqual(before,p.tree(self.project.root))
        self.session=graph([job(f'j{i}',256) for i in range(8)])
        for j in self.session['jobs']:
            j['region']['lengths']=[324,324];j['inputs']=[[4294967295]*324,[4294967295]*324]
        self.save();raw=(self.project.root/'inputs/dag.json').read_bytes();self.assertGreater(len(raw),65536)
        self.assertEqual(len(a.check(self.project,'dag.json')['jobs']),8)
    def test_frozen_inputs_inspection_without_original_executables_and_diff(self):
        first=self.run_fixture();self.session['jobs'][0]['inputs'][0][0]=4;self.save();second=self.run_fixture()
        self.kernel.unlink();shutil.rmtree(self.build)
        with patch.object(d,'run',side_effect=AssertionError('must not execute')):
            self.assertEqual(a.load(self.project,first['id'])['output']['output'],[16]);self.assertEqual(a.load(self.project,second['id'])['output']['output'],[18])
            diff=a.compare(self.project,first['id'],second['id']);self.assertEqual(diff['changed_cells'],1);self.assertEqual(diff['first_change']['before'],16)
            self.assertEqual(len(a.history(self.project)),2)
    def test_live_edits_after_capture_do_not_change_inputs_or_kernel(self):
        def execute(*args):
            (self.project.root/'inputs/dag.json').write_text('later invalid data');self.kernel.write_bytes(b'changed source kernel')
            return self.fake(*args)
        with patch.object(d,'run',side_effect=execute):r=a.run(self.project,'dag.json',self.kernel,self.build)
        self.assertEqual(r['output']['output'],[16])
    def test_pinned_available_output_is_distinct_from_all_jobs_success(self):
        self.session=graph([job('answer',1),job('later',1)],'answer');self.save()
        partial=self.run_fixture(failed=1);self.assertEqual(partial['status'],'incomplete');self.assertTrue(partial['output']['available'])
        full=self.run_fixture();self.assertEqual(a.compare(self.project,partial['id'],full['id'])['statuses'],['incomplete','succeeded'])
    def test_unavailable_designated_result_has_no_diff(self):
        failed=self.run_fixture(failed=0);full=self.run_fixture()
        self.assertFalse(failed['output']['available']);self.assertEqual(failed['halted'],3)
        with self.assertRaises(ValueError):a.compare(self.project,failed['id'],full['id'])
    def test_interrupt_and_cleanup_uncertainty_remain_unsealed(self):
        for error in [KeyboardInterrupt(),f.CleanupUncertain('fixture cleanup unknown')]:
            with patch.object(d,'run',side_effect=error):
                with self.assertRaises(type(error)):a.run(self.project,'dag.json',self.kernel,self.build)
        self.assertEqual([r['status'] for r in a.history(self.project)],['unsealed','unsealed'])
    def test_interrupt_before_and_after_atomic_publication(self):
        link=os.link
        for after in [False,True]:
            def publish(src,dst):
                if after:link(src,dst)
                raise KeyboardInterrupt()
            with patch.object(a.os,'link',side_effect=publish):
                if after:self.assertEqual(self.run_fixture()['status'],'succeeded')
                else:
                    with self.assertRaises(KeyboardInterrupt):self.run_fixture()
        self.assertEqual(sorted(r['status'] for r in a.history(self.project)),['succeeded','unsealed'])
    def test_no_overwrite_publication(self):
        with patch.object(a.os,'link',side_effect=FileExistsError('fixture collision')):
            with self.assertRaises(FileExistsError):self.run_fixture()
        self.assertEqual(a.history(self.project)[0]['status'],'unsealed')
    def test_tamper_nested_snapshot_and_output_rejected_even_rehashed(self):
        for field in ['output','input','kernel']:
            r=self.run_fixture();root=self.project.root/'dags'/r['id']
            if field=='output':r['output']['output']=[99]
            elif field=='input':
                g=copy.deepcopy(self.session);g['jobs'][0]['inputs'][0][0]=99;(root/'execution/session.json').write_bytes(p.encoded(g))
            else:(root/'execution/kernel.elf').write_bytes(b'other kernel')
            self.reseal(r)
            with self.assertRaises(ValueError):a.load(self.project,r['id'])
    def test_saved_numeric_type_substitutions_and_preview_are_rejected(self):
        for field in ['processed','planned','halted','available','word','preview']:
            r=self.run_fixture();root=self.project.root/'dags'/r['id']
            if field in ['processed','planned']:r[field]=float(r[field])
            elif field=='halted':r[field]=False
            elif field=='available':r['output']['available']=1
            elif field=='word':r['output']['output']=[16.0]
            else:
                plan=json.loads((root/'plan.json').read_text());plan['preview']['jobs'][0]['index']=0.0
                (root/'plan.json').write_bytes(p.encoded(plan))
            self.reseal(r)
            with self.assertRaises(ValueError):a.load(self.project,r['id'])
    def test_rehashed_child_and_wrapper_cannot_share_invalid_output_types(self):
        r=self.run_fixture();root=self.project.root/'dags'/r['id']
        child=json.loads((root/'execution/receipt.json').read_text())
        child['output']['output']=[16.0];r['output']['output']=[16.0]
        (root/'execution/receipt.json').write_bytes(p.encoded(child));self.reseal(r)
        with self.assertRaises(ValueError):a.load(self.project,r['id'])
    def test_diff_rejects_kernel_or_output_name_or_shape_change(self):
        first=self.run_fixture()
        self.kernel.write_bytes(b'different');other=self.run_fixture()
        with self.assertRaises(ValueError):a.compare(self.project,first['id'],other['id'])
        self.kernel.write_bytes(b'HOST FIXTURE NOT ELF');self.session['output']='a';self.save();other=self.run_fixture()
        with self.assertRaises(ValueError):a.compare(self.project,first['id'],other['id'])
        self.session=graph([job('b',128)]);self.save();other=self.run_fixture()
        with self.assertRaises(ValueError):a.compare(self.project,first['id'],other['id'])
    def test_invalid_paths_duplicate_json_symlinks_and_oversize_have_no_run(self):
        for path in ['../dag.json','/dag.json','a/b.json','dag.txt']:
            with self.assertRaises(ValueError):a.check(self.project,path)
        path=self.project.root/'inputs/dag.json'
        for raw in [b'{"schema":1,"schema":2}',b' '*(a.INPUT_LIMIT+1)]:
            path.write_bytes(raw)
            with self.assertRaises((ValueError,OSError)):a.run(self.project,'dag.json',self.kernel,self.build)
        path.unlink();path.symlink_to(self.kernel)
        with self.assertRaises((ValueError,OSError)):a.check(self.project,'dag.json')
        self.assertFalse((self.project.root/'dags').exists())
    def test_cli_preview_routes_without_execution(self):
        result=subprocess.run([os.sys.executable,'-m','raveil','project','dag-check','--project',str(self.project.root),'--input','dag.json'],cwd=p.REPOSITORY,capture_output=True,text=True,check=True)
        self.assertEqual(json.loads(result.stdout)['output'],'b');self.assertFalse((self.project.root/'dags').exists())

    def test_v2_subrange_capture_and_saved_preview(self):
        from scripts.fold_dag_range_cases import scenarios
        self.session=next(scenarios())[1];self.save()
        preview=a.check(self.project,'dag.json');self.assertEqual(preview['jobs'][-1]['references'],3)
        self.assertEqual(preview['jobs'][-1]['ranges'][0]['offset'],128)
        first=self.run_fixture();self.session['jobs'][-1]['inputs'][0]['offset']=64;self.save();second=self.run_fixture()
        with patch.object(d,'run',side_effect=AssertionError('must not execute')):
            self.assertEqual(a.load(self.project,first['id'])['output']['output'],[134+2*i for i in range(128)])
            self.assertEqual(a.load(self.project,second['id'])['output']['output'],[70+2*i for i in range(128)])
            self.assertEqual(a.compare(self.project,first['id'],second['id'])['changed_cells'],128)
