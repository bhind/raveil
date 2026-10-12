"""Sealed fixture coordinator UT. Stub child execution is never hardware evidence."""
import copy
import json
import os
import shutil
import subprocess
import sys
import unittest
from unittest.mock import patch
from raveil import project as p, project_array as a, array_program as compiler
from raveil import project_mf01_grid as g, project_dag_batch as b, fold_dag as d
from tests import test_project_dag_batch as fixtures
from tests.test_array_program import program, source, chain, gemm


class ArrayWorkspaceTests(unittest.TestCase):
    save=fixtures.BatchTests.save
    fake=fixtures.BatchTests.fake

    def setUp(self):
        fixtures.BatchTests.setUp(self);self.source=program();self.save_source()

    def save_source(self):
        (self.project.root/'inputs/array.json').write_bytes(p.encoded(self.source))

    def execute(self,callback=None):
        with patch.object(d,'run',side_effect=callback or self.fake):
            return a.run(self.project,'array.json',self.kernel,self.build)

    def reseal(self,record):
        root=self.project.root/'arrays'/record['id'];record['files']=b._inventory(root);raw=p.encoded(record)
        (root/'record.json').write_bytes(raw);(root/'record.sha256').write_text(p.digest(raw)+'\n')

    def test_preview_readonly_long_expression_and_saved_diff(self):
        self.source=chain(20,1,2);self.save_source();before=p.tree(self.project.root)
        self.assertEqual(len(a.check(self.project,'array.json')['passes']),20);self.assertEqual(before,p.tree(self.project.root))
        first=self.execute();self.assertEqual(first['outputs'],compiler.reference(self.source))
        self.source['stages'][0]['source']['inputs'][0]['words'][0]=7;self.save_source();second=self.execute()
        self.kernel.unlink();shutil.rmtree(self.build)
        with patch('subprocess.Popen',side_effect=AssertionError('saved read executes')):
            self.assertEqual(a.load(self.project,first['id']),first);self.assertEqual(len(a.history(self.project)),2)
            self.assertEqual(a.compare(self.project,first['id'],second['id'])['changed_cells'],1)

    def test_linked_gather_and_post_execute_through_verified_planes(self):
        self.source=gemm(2,2,2);s=source(2,2);s['inputs']=[{'from':'answer'}];s['kernel']['views']['v'].update(row=[0,1],column=[1,0])
        s['post']=dict(nodes=[dict(id='p',op='load',view='reduced'),dict(id='r',op='relu_i32',args=['p'])],result='r')
        self.source['stages'].append(dict(name='later',source=s));self.source['outputs']=['later','answer'];self.save_source()
        record=self.execute();self.assertEqual(record['outputs'],compiler.reference(self.source))
        self.assertEqual(a.load(self.project,record['id']),record)

    def test_frozen_literals_kernel_and_failed_prefix_then_fresh_retry(self):
        self.source=chain(5);self.save_source();expected=compiler.reference(self.source);calls=[]
        def failure(*args):
            (self.project.root/'inputs/array.json').write_text('changed');self.kernel.write_bytes(b'changed')
            i=len(calls);calls.append(i);return self.fake(*args,failed=0 if i==2 else None)
        record=self.execute(failure);self.assertEqual(len(calls),3)
        self.assertEqual(record['status'],'incomplete');self.assertIsNone(record['outputs'])
        old=p.tree(self.project.root/'arrays'/record['id']);self.save_source();self.kernel.write_bytes(b'HOST FIXTURE')
        retry=self.execute();self.assertEqual(retry['outputs'],expected)
        self.assertEqual(old,p.tree(self.project.root/'arrays'/record['id']))
        self.assertEqual(a.load(self.project,record['id']),record)
        with self.assertRaises(ValueError):a.compare(self.project,record['id'],retry['id'])

    def test_unused_stage_failure_suppresses_completed_output(self):
        self.source['stages'].append(dict(name='unused',source=source()));self.save_source();calls=[]
        def fail(*args):
            i=len(calls);calls.append(i);return self.fake(*args,failed=0 if i==2 else None)
        record=self.execute(fail);self.assertEqual(len(calls),3);self.assertIsNone(record['outputs'])

    def test_all_preflight_failures_leave_no_attempt(self):
        for value in [chain(129),chain(9,64,64),program()]:
            if value==program():value['stages'].append(dict(name='later',source=source()));value['stages'][-1]['source']['kernel']['result']='missing'
            self.source=value;self.save_source()
            with patch.object(g,'run',side_effect=AssertionError('dispatch')),self.assertRaises(ValueError):self.execute()
            self.assertNotIn('arrays',self.project.workspace.ls('/'))
        self.source=program();self.save_source()
        with patch.object(b,'MAX_BYTES',100),self.assertRaisesRegex(ValueError,'reservation'):self.execute()
        self.assertNotIn('arrays',self.project.workspace.ls('/'))

    def test_capture_reservation_counts_each_session_runtime_copy(self):
        plan=compiler.compile(self.source);raw=p.encoded(self.source)
        budget=a._capture_budget(raw,plan,self.kernel.read_bytes(),self.build)
        runtime=sum((self.build/path.lstrip('/')).stat().st_size for path,kind in p.tree(self.build).items() if kind!='directory')
        self.assertEqual(budget['known_bytes'],len(raw)+5*runtime+5*self.kernel.stat().st_size)
        # A ceiling between old (3 copies) and correct (5 copies) must reject pre-attempt.
        limit=budget['known_bytes']+budget['reserved_bytes']-runtime
        with patch.object(b,'MAX_BYTES',limit),self.assertRaisesRegex(ValueError,'reservation'):self.execute()
        self.assertNotIn('arrays',self.project.workspace.ls('/'))

    def test_capture_entry_reservation_counts_session_runtime_trees(self):
        count=len(p.tree(self.build))
        # Two passes and two sessions: five runtime trees, plus entry reservation.
        correct=5*count+64*2+32*2
        with patch.object(b,'MAX_ENTRIES',correct-count),self.assertRaisesRegex(ValueError,'reservation'):self.execute()
        self.assertNotIn('arrays',self.project.workspace.ls('/'))

    def test_strict_json_filename_size_and_symlink_rejection(self):
        path=self.project.root/'inputs/array.json'
        for raw in [b'{"schema":null,"schema":null}',b' '*(b.INPUT_LIMIT+1)]:
            path.write_bytes(raw)
            with self.assertRaises(ValueError):a.check(self.project,'array.json')
        for name in ['../array.json',True,'a/b.json']:
            with self.assertRaises(ValueError):a.check(self.project,name)
        path.unlink();path.symlink_to(self.kernel)
        with self.assertRaises(ValueError):a.check(self.project,'array.json')

    def test_valid_wrong_child_and_executable_fail_before_downstream(self):
        original=g.run
        for kind in ['words','kernel']:
            calls=[]
            def substitute(project,input_file,kernel,build):
                calls.append(input_file)
                if kind=='words':
                    path=project.root/'inputs'/input_file;value=json.loads(path.read_text());value['inputs'][0]['words'][0]=91;path.write_bytes(p.encoded(value))
                else:
                    kernel=self.root/'other.elf';kernel.write_bytes(b'OTHER')
                return original(project,input_file,kernel,build)
            with patch.object(g,'run',side_effect=substitute),self.assertRaises(ValueError):self.execute()
            self.assertEqual(len(calls),1)
        self.assertEqual([x['status'] for x in a.history(self.project)],['unsealed']*2)

    def test_forged_return_is_ignored_and_actual_incomplete_stops(self):
        original=g.run;calls=[]
        def forged(*args):
            result=original(*args);calls.append(result['status']);result['status']='succeeded';result['output']=dict(rows=2,columns=3,words=[999]*6)
            return result
        with patch.object(g,'run',side_effect=forged):
            record=self.execute(lambda *args:self.fake(*args,failed=0))
        self.assertEqual(calls,['incomplete']);self.assertEqual(record['status'],'incomplete');self.assertIsNone(record['outputs'])

    def test_resealed_parent_cannot_rebind_original_child(self):
        record=self.execute();root=self.project.root/'arrays'/record['id']
        value=json.loads((root/'source.json').read_text());value['stages'][0]['source']['inputs'][0]['words'][0]=42
        raw=p.encoded(value);(root/'source.json').write_bytes(raw)
        plan=json.loads((root/'plan.json').read_text());plan.update(source_sha256=p.digest(raw),preview=compiler.compile(value))
        (root/'plan.json').write_bytes(p.encoded(plan));self.reseal(record)
        with self.assertRaisesRegex(ValueError,'producer binding'):a.load(self.project,record['id'])

    def test_resealed_prefix_output_plan_and_identity_tampering(self):
        for kind in ['float','omit','reorder','extra','name','kernel','plan','hash']:
            record=self.execute();root=self.project.root/'arrays'/record['id']
            if kind=='float':record['outputs'][0]['words'][0]=float(record['outputs'][0]['words'][0])
            elif kind=='omit':record['children'].pop();shutil.rmtree(root/'children/001')
            elif kind=='reorder':record['children'].reverse()
            elif kind=='extra':(root/'children/002').mkdir()
            elif kind=='name':record['children'][0]['name']='p999'
            elif kind=='kernel':
                (root/'kernel.elf').write_bytes(b'OTHER');plan=json.loads((root/'plan.json').read_text());plan['kernel_sha256']=p.digest(b'OTHER');(root/'plan.json').write_bytes(p.encoded(plan))
            elif kind=='plan':
                plan=json.loads((root/'plan.json').read_text());plan['preview']['passes'][0]['release']=[];plan['preview']['sessions']=2.0;(root/'plan.json').write_bytes(p.encoded(plan))
            self.reseal(record)
            if kind=='hash':(root/'record.sha256').write_text('0'*64)
            with self.subTest(kind=kind),self.assertRaises(ValueError):a.load(self.project,record['id'])

    def test_full_source_oracle_mismatch_never_publishes(self):
        with patch.object(compiler,'reference',return_value=[]),self.assertRaisesRegex(ValueError,'oracle mismatch'):self.execute()
        self.assertEqual(a.history(self.project)[0]['status'],'unsealed')

    def test_overflow_unsealed_and_checked_between_passes(self):
        inventory=b._inventory;calls=[]
        def capped(root):
            if root.parent.name=='arrays':raise ValueError('capture overflow')
            return inventory(root)
        def execute(*args):calls.append(args);return self.fake(*args)
        with patch.object(b,'_inventory',side_effect=capped),self.assertRaisesRegex(ValueError,'overflow'):self.execute(execute)
        self.assertEqual(len(calls),1);self.assertEqual(a.history(self.project)[0]['status'],'unsealed')

    def test_cancel_uncertain_cleanup_and_atomic_publication(self):
        for error in [KeyboardInterrupt(),b.f.CleanupUncertain('writer'),ValueError('execution')]:
            with patch.object(g,'run',side_effect=error),self.assertRaises(type(error)):self.execute()
        link=os.link
        for when in ['before','after','collision']:
            def publish(src,dst):
                is_parent='/arrays/' in str(dst) and '/children/' not in str(dst)
                if is_parent and when=='before':raise KeyboardInterrupt()
                if is_parent and when=='collision':raise FileExistsError('existing')
                result=link(src,dst)
                if is_parent and when=='after':raise KeyboardInterrupt()
                return result
            with patch.object(a.os,'link',side_effect=publish):
                if when=='after':self.assertEqual(self.execute()['status'],'succeeded')
                else:
                    with self.assertRaises(KeyboardInterrupt if when=='before' else FileExistsError):self.execute()
        self.assertEqual(sorted(x['status'] for x in a.history(self.project)),['succeeded']+['unsealed']*5)

    def test_compare_requires_same_layout_and_executables(self):
        first=self.execute();self.source['stages'][0]['name']='renamed';self.source['outputs']=['renamed'];self.save_source();second=self.execute()
        with self.assertRaises(ValueError):a.compare(self.project,first['id'],second['id'])
        self.source=program();self.save_source();self.kernel.write_bytes(b'OTHER');third=self.execute()
        with self.assertRaises(ValueError):a.compare(self.project,first['id'],third['id'])

    def test_cli_preview_history_parser_and_failure_exit(self):
        def cli(*args):
            return subprocess.run([sys.executable,'-m','raveil','project',*args,'--project',str(self.project.root)],capture_output=True,text=True)
        result=cli('array-check','--input','array.json');self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(result.stdout)['sessions'],2)
        self.assertEqual(json.loads(cli('arrays').stdout),[])
        for args in [('array','missing'),('array-diff','first','second'),('array-run','--input','array.json','--kernel','missing','--build','missing')]:
            self.assertEqual(cli(*args).returncode,2)
        # Main dispatch uses a stubbed coordinator; no subprocess fixture survives across a CLI process.
        from raveil.cli import main
        with patch.object(a,'run',return_value={'status':'incomplete'}),patch('builtins.print'):
            self.assertEqual(main(['project','array-run','--project',str(self.project.root),'--input','array.json','--kernel',str(self.kernel),'--build',str(self.build)]),2)
