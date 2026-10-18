"""Independent numerical, metric-boundary and experiment-policy checks."""
import copy
import json
from pathlib import Path
import random
import shutil
import struct
import subprocess
import tempfile
import unittest
import sys
from unittest.mock import patch
from scripts import image_demo as image
from scripts.image_demo_experiment import collect,disposition,command,paired,frozen_app
from scripts.image_demo_report import write
from tests.test_array_program import execute
from raveil import project as p


class ImageTests(unittest.TestCase):
    def test_hand_computed_signed_clamped_edges_activation_and_pool(self):
        pixels=[[10,20,5,0],[0,0,255,255]]
        expected=[[10,0xfffffffb,0xffffffec,0xfffffffb,0,255,255,0],
                  [10,0,0,0,0,255,255,0],[255,255]]
        self.assertEqual([x['words'] for x in image.reference(pixels)],expected)
        for fused in (False,True):self.assertEqual(execute(image.source(pixels,fused)),image.reference(pixels))

    def test_generated_corpus_and_schema_only_comparison(self):
        rng=random.Random(241)
        cases=list(image.cases())+[('small',[[rng.randrange(256) for _ in range(6)] for _ in range(4)])]
        for name,pixels in cases:
            original=copy.deepcopy(pixels);old=image.source(pixels,False);new=image.source(pixels,True)
            self.assertEqual(dict(old,schema=new['schema']),new)
            for value in (old,new):
                with self.subTest(name=name,schema=value['schema']):self.assertEqual(execute(value),image.reference(pixels))
            self.assertEqual(pixels,original)

    def test_uniform_images_have_no_boundary_artifact_and_oracle_is_independent(self):
        with patch('raveil.array_program.reference',side_effect=AssertionError('shared oracle')):
            for n in (0,255):
                for output in image.reference([[n]*4 for _ in range(2)]):self.assertFalse(any(output['words']))

    def test_strict_input_and_pgm_roundtrip(self):
        for bad in ([],[[1]],[[1,2],[3]],[[True,0],[0,0]],[[256,0],[0,0]],[[0.0,0],[0,0]],[[0,0]]*3):
            with self.assertRaises(ValueError):image.source(bad)
        for _,pixels in image.cases():self.assertEqual(image.read_pgm(image.pgm(pixels)),pixels)
        for bad in (b'P2\n2 2\n255\n1234',b'P5\n2 2\n255\nabc',b'P5\n2 2\n255\nabcde',b'P5\n3 2\n255\nabcdef'):
            with self.assertRaises(ValueError):image.read_pgm(bad)


class MetricTests(unittest.TestCase):
    def fixture(self):
        rows=[(0,0,0,0,0,0),(1,5,0,0,7,0),(0,9,1,648,7,0),(1,12,1,648,0,0)]
        raw=b''.join(struct.pack('<6I',*r) for r in rows)
        device=dict(schema='raveil.fold-device/v1',success=1,fault=0,cancelled=0,accepted=2,completed=2,reads=1,writes=1)
        return rows,raw,device

    def test_cycle_zero_and_final_response_inclusive(self):
        _,raw,device=self.fixture()
        self.assertEqual(image.trace_metrics(raw,device),dict(rtl_active_cycles=13,reads=1,writes=1,transactions=2,interface_payload_bytes=8))

    def test_invalid_incomplete_and_miscounted_traces_reject(self):
        rows,raw,device=self.fixture()
        badrows=[rows[:-1],rows+[rows[-1]],[rows[0],rows[0],*rows[1:]],
                 [rows[0],(1,5,0,1,7,0),*rows[2:]],[(2,*rows[0][1:]),*rows[1:]],
                 [*rows[:-1],(1,12,1,648,0,1)]]
        for bad in [b'',raw[:-1],*[b''.join(struct.pack('<6I',*r) for r in rr) for rr in badrows]]:
            with self.assertRaises(ValueError):image.trace_metrics(bad,device)
        for key,value in [('success',0),('fault',1),('cancelled',1),('reads',2),('accepted',3),('completed',1)]:
            with self.assertRaises(ValueError):image.trace_metrics(raw,dict(device,**{key:value}))

    def test_bound_job_aggregation_and_seed_rejection(self):
        _,raw,device=self.fixture()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);project=p.Project(p.init_project(root/'workspace'));root=project.root;parent=root/'arrays/id';parent.mkdir(parents=True)
            (parent/'plan.json').write_text(json.dumps(dict(build_sha256='build',kernel_sha256='kernel')))
            session=root/'session';p.init_project(session/'project');jobs=[dict(rtl_id=str(i),result=dict(approved=True)) for i in range(2)]
            for job in jobs:
                folded=session/'project/folds'/job['rtl_id'];(folded/'device').mkdir(parents=True)
                (folded/'device/trace.bin').write_bytes(raw);(folded/'device/device.json').write_text(json.dumps(device))
                (folded/'plan.json').write_text(json.dumps(dict(options=dict(seed=213,cancel_after=0,fault_at=0))))
            with patch('scripts.image_demo_experiment.a.load',return_value=dict(status='succeeded',outputs=[])), \
                 patch('scripts.image_demo_experiment.counts',return_value=dict(receipts=[dict(path=str(session))])), \
                 patch('scripts.image_demo_experiment.dag.verify',return_value=dict(jobs=jobs)), \
                 patch('scripts.image_demo_experiment.f.load',return_value=dict(status='succeeded')):
                result=collect(project,'id');self.assertEqual((result['sessions'],result['jobs'],result['rtl_active_cycles'],result['transactions']),(1,2,26,4))
                (session/'project/folds/0/plan.json').write_text(json.dumps(dict(options=dict(seed=1,cancel_after=0,fault_at=0))))
                with self.assertRaises(ValueError):collect(project,'id')

    def test_decision_requires_every_case_and_separates_host_cost(self):
        good=dict(cycle_reduction=.3,transaction_reduction=.3,scalar=dict(median_wall_seconds=2),fused=dict(median_wall_seconds=1))
        self.assertIn('融合を維持',disposition([good]))
        self.assertIn('ホスト側',disposition([dict(good,fused=dict(median_wall_seconds=3))]))
        self.assertIn('満たさない',disposition([good,dict(good,cycle_reduction=.19)]))


class CpuTests(unittest.TestCase):
    def test_native_c_matches_independent_python_for_all_images(self):
        clang=shutil.which('clang');self.assertIsNotNone(clang,'existing clang required')
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);binary=root/'cpu'
            subprocess.run([clang,'-O3','-std=c11','-Wall','-Wextra','-Werror',str(p.REPOSITORY/'scripts/image_demo_cpu.c'),'-o',str(binary)],check=True,capture_output=True)
            for name,pixels in image.cases():
                path=root/(name+'.pgm');path.write_bytes(image.pgm(pixels))
                result=subprocess.run([str(binary),str(path),'10'],check=True,capture_output=True,text=True)
                value=json.loads(result.stdout);self.assertEqual(value['outputs'],[o['words'] for o in image.reference(pixels)])
                self.assertGreater(value['elapsed_seconds'],0)


class CollectionTests(unittest.TestCase):
    def test_timeout_preserves_partial_logs_and_requests_graceful_child_exit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            code="import signal,time,sys;signal.signal(signal.SIGTERM,lambda *a:(print('drained',flush=True),sys.exit(143)));print('started',flush=True);time.sleep(30)"
            with self.assertRaises(RuntimeError):command([sys.executable,'-u','-c',code],root,'timeout',.3)
            result=json.loads((root/'timeout.execution.json').read_bytes())
            self.assertEqual(result['failure'],'TimeoutExpired');self.assertEqual(result['code'],143)
            self.assertIn('started',result['stdout']);self.assertIn('drained',result['stdout'])
            self.assertTrue((root/'timeout.command.json').is_file())

    def test_pairing_matches_repeat_not_execution_order(self):
        values=[dict(repeat=i,variant=v,elapsed_seconds=2 if v=='scalar' else 1)
                for i in range(3) for v in (('scalar','fused') if i%2 else ('fused','scalar'))]
        result=paired(values);self.assertEqual([p['fused_over_scalar'] for p in result],[.5]*3)
        self.assertEqual(result[0]['order'],['fused','scalar'])
        with self.assertRaises(ValueError):paired(values[:-1])

    def test_frozen_engine_launcher_and_manifest_mutations_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            app=Path(tmp);(app/'engine').mkdir();(app/'engine/a.py').write_bytes(b'pass\n');(app/'raveil').write_bytes(b'launch\n')
            manifest=dict(engine=p.tree(app/'engine'),launcher_sha256=p.digest((app/'raveil').read_bytes()))
            original=p.encoded(manifest);(app/'app.json').write_bytes(original);before=frozen_app(app)
            for path in (app/'engine/a.py',app/'raveil'):
                raw=path.read_bytes();path.write_bytes(raw+b' ')
                with self.assertRaises(ValueError):frozen_app(app)
                path.write_bytes(raw)
            (app/'app.json').write_bytes(original+b' ');self.assertNotEqual(frozen_app(app),before)


if __name__=='__main__':unittest.main()
