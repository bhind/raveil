"""Captured v2 coordinator tests with sealed host child fixtures, not RTL evidence."""
import copy
import shutil
import unittest
from unittest.mock import patch

from raveil import project as p, project_array as a, array_program as compiler
from raveil import project_dag_batch as b, project_mf01_grid as g, fold_dag as d
from tests import test_project_dag_batch as fixtures
from tests import test_project_array as legacy
from tests.test_array_program import program, source, chain
from tests.test_array_fusion import v2


class FusedWorkspaceTests(unittest.TestCase):
    save = fixtures.BatchTests.save
    fake = fixtures.BatchTests.fake
    save_source = legacy.ArrayWorkspaceTests.save_source
    execute = legacy.ArrayWorkspaceTests.execute
    reseal = legacy.ArrayWorkspaceTests.reseal

    def setUp(self):
        fixtures.BatchTests.setUp(self)
        self.source = v2(program()); self.save_source()

    def test_same_cli_path_saved_validation_and_legacy_comparison(self):
        self.source['schema'] = compiler.SCHEMA; self.save_source(); old = self.execute()
        self.source['schema'] = compiler.SCHEMA_V2; self.save_source(); new = self.execute()
        self.assertEqual(old['outputs'], new['outputs'])
        self.assertEqual(len(old['children']), 2); self.assertEqual(len(new['children']), 1)
        self.kernel.unlink(); shutil.rmtree(self.build)
        with patch('subprocess.Popen', side_effect=AssertionError('saved read executed')):
            self.assertEqual(a.load(self.project, old['id']), old)
            self.assertEqual(a.load(self.project, new['id']), new)
            self.assertEqual(a.compare(self.project, old['id'], new['id'])['changed_cells'], 0)

    def test_fused_failure_suppresses_earlier_requested_output_and_fresh_retry(self):
        s = source(); s['inputs'] = [{'from': 'answer'}]
        self.source['stages'].append(dict(name='later', source=s)); self.source['outputs'].append('later')
        self.save_source(); calls = []
        def fail(*args):
            i = len(calls); calls.append(i)
            return self.fake(*args, failed=0 if i == 1 else None)
        failed = self.execute(fail)
        self.assertEqual(failed['status'], 'incomplete'); self.assertIsNone(failed['outputs'])
        root = self.project.root/'arrays'/failed['id']; before = p.tree(root)
        retry = self.execute(); self.assertEqual(retry['outputs'], compiler.reference(self.source))
        self.assertNotEqual(retry['id'], failed['id']); self.assertEqual(before, p.tree(root))

    def test_block_to_fused_producer_and_input_edit(self):
        self.source = v2(chain(24, 1, 2)); s = source(1, 2); s['inputs'] = [{'from': 'answer'}]
        self.source['stages'].append(dict(name='later', source=s)); self.source['outputs'] = ['later']
        self.save_source(); first = self.execute()
        self.assertEqual(first['outputs'][0]['words'], [26, 27])
        self.source['stages'][0]['source']['inputs'][0]['words'][1] = 10
        self.save_source(); second = self.execute()
        self.assertEqual(a.compare(self.project, first['id'], second['id'])['changed_cells'], 1)

    def test_resealed_version_and_structural_plan_tampering_reject(self):
        record = self.execute(); root = self.project.root/'arrays'/record['id']
        raw = (root/'source.json').read_bytes(); original = copy.deepcopy(record)
        changed = copy.deepcopy(self.source); changed['schema'] = compiler.SCHEMA
        (root/'source.json').write_bytes(p.encoded(changed)); self.reseal(record)
        with self.assertRaises(ValueError): a.load(self.project, record['id'])
        (root/'source.json').write_bytes(raw); self.reseal(original)
        plan_raw = (root/'plan.json').read_bytes()
        import json
        plan = json.loads(plan_raw); plan['preview']['passes'][0]['tile'] = [1, 1]
        (root/'plan.json').write_bytes(p.encoded(plan)); self.reseal(original)
        with self.assertRaises(ValueError): a.load(self.project, record['id'])

    def test_invalid_unused_stage_and_resource_fail_before_attempt(self):
        bad = source(); bad['kernel']['nodes'][-1]['args'] = ['missing']
        self.source['stages'].append(dict(name='unused', source=bad)); self.save_source()
        with patch.object(g, 'run', side_effect=AssertionError('invalid source dispatched')):
            with self.assertRaises(ValueError): self.execute()
        self.assertNotIn('arrays', self.project.workspace.ls('/'))
        self.source = v2(program()); self.save_source()
        with patch.object(b, 'MAX_BYTES', 1), self.assertRaises(ValueError): self.execute()
        self.assertNotIn('arrays', self.project.workspace.ls('/'))

    def post_budget_fixture(self):
        from scripts.array_fusion_cases import cases
        self.source = next(value for name, value, _ in cases() if name == 'wrapped-fold-post')
        self.save_source(); compiled = compiler.compile(self.source)
        self.assertEqual((len(compiled['passes']), compiled['sessions'], compiled['jobs']), (1, 1, 2))
        return compiled

    def test_post_job_runtime_byte_budget_rejects_before_attempt(self):
        compiled = self.post_budget_fixture(); raw = p.encoded(self.source)
        runtime = sum((self.build/path.lstrip('/')).stat().st_size
                      for path, kind in p.tree(self.build).items() if kind != 'directory')
        budget = a._capture_budget(raw, compiled, self.kernel.read_bytes(), self.build)
        self.assertEqual(budget['known_bytes'], len(raw) + 4*runtime + 3*self.kernel.stat().st_size)
        self.assertEqual(budget['reserved_bytes'], 65536 + 2*131072)
        # This ceiling admits the old one-job/session estimate, but misses a runtime.
        ceiling = budget['known_bytes'] + budget['reserved_bytes'] - runtime
        with patch.object(b, 'MAX_BYTES', ceiling), patch.object(g, 'run', side_effect=AssertionError('dispatch')):
            with self.assertRaisesRegex(ValueError, 'reservation'): self.execute()
        self.assertNotIn('arrays', self.project.workspace.ls('/'))

    def test_post_job_runtime_entry_budget_rejects_before_attempt(self):
        self.post_budget_fixture(); entries = len(p.tree(self.build))
        ceiling = 4*entries + 64 + 2*32 - entries
        with patch.object(b, 'MAX_ENTRIES', ceiling), patch.object(g, 'run', side_effect=AssertionError('dispatch')):
            with self.assertRaisesRegex(ValueError, 'reservation'): self.execute()
        self.assertNotIn('arrays', self.project.workspace.ls('/'))


if __name__ == '__main__':
    unittest.main()
