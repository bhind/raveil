"""Acceptance workload UT; actual execution is a separately invoked harness."""
import unittest
from scripts.array_program_cases import cases
from scripts.array_program_system_checks import cases as system_cases
from tests.test_array_program import execute
from raveil import array_program as a


class ArrayAcceptanceCasesTests(unittest.TestCase):
    def test_owned_formulas_match_automatic_lowering(self):
        seen=set()
        for name,source,expected in cases():
            with self.subTest(case=name):
                self.assertNotIn(name,seen);seen.add(name)
                self.assertEqual(a.reference(source),expected)
                self.assertEqual(execute(source),expected)
        self.assertEqual(len(seen),14)

    def test_cases_require_long_maps_pressure_shapes_and_all_operations(self):
        all_cases={name:value for name,value,_ in [*cases(),*system_cases()]}
        self.assertGreater(a.compile(all_cases['long-expression'])['source_nodes'],15)
        self.assertGreaterEqual(a.compile(all_cases['nine-live-values'])['peak_plane_words'],60)
        self.assertEqual(a.compile(all_cases['pointwise-17-19'])['sessions'],8)
        self.assertEqual(len(a.compile(all_cases['fanout-join'])['outputs']),2)
        ops={n['op'] for v in all_cases.values() for st in v['stages'] for region in [st['source']['kernel'],*([st['source']['post']] if 'post' in st['source'] else [])] for n in region['nodes']}
        self.assertEqual(ops,{'load','add','mul','max','add_imm','max_i32','relu_i32','ge_imm'})
        self.assertEqual({st['source']['kernel']['fold'] for v in all_cases.values() for st in v['stages']},{'sum','max'})

    def test_system_boundary_formulas_and_maximum_declared_counts(self):
        for name,source,expected in system_cases():
            with self.subTest(case=name):
                self.assertEqual(a.reference(source),expected)
                self.assertEqual(execute(source),expected)
        values={n:v for n,v,_ in system_cases()}
        self.assertEqual(a.compile(values['maximum-shape-broadcast'])['sessions'],16)
        self.assertEqual(len(a.compile(values['eight-stage-eight-output'])['outputs']),8)
        self.assertEqual(len(values['eight-inputs']['stages'][0]['source']['inputs']),8)
