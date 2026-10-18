"""Structural/compiler tests; backend interpreter execution is host evidence."""
import copy
import random
import unittest
from unittest.mock import patch

from raveil import array_program as a, array_fusion as fusion, mf01_grid as grid
from scripts.array_program_cases import cases
from scripts.array_program_system_checks import cases as system_cases
from tests.test_array_program import chain, gemm, program, source, literal, execute


def v2(value):
    value = copy.deepcopy(value); value['schema'] = a.SCHEMA_V2
    return value


class ArrayFusionTests(unittest.TestCase):
    def check(self, value, expected=None):
        original = copy.deepcopy(value)
        actual = execute(value)
        self.assertEqual(actual, a.reference(value))
        self.assertEqual(value, original)
        if expected is not None:
            self.assertEqual(actual, expected)
        return a.compile(value)

    def test_new_acceptance_formulas(self):
        from scripts.array_fusion_cases import cases as fusion_cases
        for name, value, expected in fusion_cases():
            with self.subTest(name=name):
                self.check(value, expected)

    def test_prior_independent_workload_formulas(self):
        for name, value, expected in list(cases()) + list(system_cases()):
            with self.subTest(name=name):
                self.check(v2(value), expected)

    def test_legacy_policy_remains_scalar_and_new_policy_is_explicit(self):
        old = chain(24)
        self.assertEqual(len(a.compile(old)['passes']), 24)
        self.assertNotIn('policy', a.compile(old))
        new = v2(old); plan = self.check(new)
        self.assertEqual(len(plan['passes']), 2)
        self.assertTrue(all(s['op'] == 'block' for s in plan['passes']))
        with self.assertRaises(ValueError):
            a.bind(old, plan['passes'][0], {})
        for schema in ('raveil.array-program/v3', None, False):
            invalid = copy.deepcopy(new); invalid['schema'] = schema
            with self.assertRaises(ValueError):
                a.compile(invalid)

    def test_large_gemm_is_not_unrolled_into_host_passes(self):
        old = gemm(17, 19, 64)
        with self.assertRaises(ValueError):
            a.compile(old)
        new = v2(old); plan = self.check(new)
        self.assertEqual(len(plan['passes']), 1)
        self.assertEqual(plan['passes'][0]['tile'], [5, 5])
        self.assertEqual(plan['sessions'], 16)
        self.assertEqual(plan['scalar_evaluations'], 17 * 19 * 255)
        self.assertEqual(plan['work_words'], 17 * 19)
        self.assertEqual(plan['jobs'], 16)
        expected = [sum((r * 64 + t) * (t * 19 + c) for t in range(64)) & a.MASK
                    for r in range(17) for c in range(19)]
        self.assertEqual(execute(new)[0]['words'], expected)

    def test_long_maps_and_signed_blocks(self):
        for count in (16, 24, 40, 128):
            value = v2(chain(count, 2, 3)); plan = self.check(value)
            self.assertLess(len(plan['passes']), count)
        value = v2(chain(24, 64, 64)); plan = self.check(value)
        self.assertEqual(plan['sessions'], 32)
        self.assertEqual(plan['work_words'], 8192)
        value = v2(chain(24, 1, 5))
        value['stages'][0]['source']['inputs'][0]['words'] = [0, 0x7fffffff, 0x80000000, 0xffffffff, 9]
        nodes = value['stages'][0]['source']['kernel']['nodes']
        for i in (5, 14, 22):
            nodes[i] = dict(id=f'n{i}', op='relu_i32', args=[f'n{i-1}'])
        self.check(value)

    def test_dead_nodes_fanout_and_live_values_do_not_disappear(self):
        s = source(1, 2); nodes = [dict(id=f'x{i}', op='load', view='v') for i in range(9)]
        previous = 'x0'
        for i in range(1, 9):
            name = f'z{i}'; nodes.append(dict(id=name, op='add', args=[previous, f'x{i}'])); previous = name
        s['kernel'].update(nodes=nodes, result=previous)
        plan = self.check(v2(program(s)))
        self.assertEqual(plan['source_nodes'], 17)
        self.assertEqual(len(plan['passes']), 17)  # Multiple live values require cuts.
        value = v2(chain(24)); value['stages'][0]['source']['kernel']['result'] = 'n0'
        self.check(value)  # Later declared operations remain represented.
        value['stages'][0]['source']['kernel']['nodes'][-1]['args'] = ['missing']
        with self.assertRaises(ValueError):
            a.compile(value)

    def test_mixed_stage_binding_and_pinned_lifetimes(self):
        value = v2(chain(24, 2, 3))
        s = source(3, 2, [dict(id='x', op='load', view='v')]); s['inputs'] = [{'from': 'answer'}]
        s['kernel']['views']['v'].update(row=[0, 1], column=[1, 0])
        value['stages'].append(dict(name='transpose', source=s)); value['outputs'] = ['transpose', 'answer']
        plan = self.check(value)
        self.assertEqual([s['op'] for s in plan['passes']], ['block', 'block', 'fused'])
        pinned = {x['producer'] for x in plan['outputs']}
        self.assertTrue(all(not pinned.intersection(s['release']) for s in plan['passes']))
        value['stages'].reverse()
        self.assertEqual(a.compile(value), plan)

    def test_plan_independent_of_words_including_tile_search(self):
        for original in (gemm(17, 19, 64), chain(24), program()):
            value = v2(original); expected = a.compile(value)
            for stage in value['stages']:
                for item in stage['source']['inputs']:
                    item['words'] = [0xffffffff - i for i in range(len(item['words']))]
            self.assertEqual(a.compile(value), expected)

    def test_post_stays_after_full_wrapped_fold_and_counts_jobs(self):
        _, value, expected = next(x for x in cases() if x[0] == 'wrapped-fold-post')
        plan = self.check(v2(value), expected)
        self.assertEqual(plan['jobs'], 2 * plan['sessions'])
        self.assertEqual(plan['work_words'], 2 * len(expected[0]['words']))

    def test_full_input_and_packed_words_are_in_plane_accounting(self):
        s = source(1, 1); s['inputs'] = [literal(64, 64)]
        value = v2(program(s)); plan = self.check(value)
        # Original input + the full bound copy, even though output is one word.
        self.assertEqual(plan['peak_plane_words'], 8195)
        with patch.object(a, 'MAX_PLANES', 8195):
            a.compile(value)
        with patch.object(a, 'MAX_PLANES', 8194), self.assertRaisesRegex(ValueError, 'plane-word'):
            a.compile(value)
        with patch.object(a, 'MAX_PLANES', 8192), self.assertRaisesRegex(ValueError, 'plane-word'):
            a.compile(value)
        with patch.object(fusion, 'MAX_SCALAR_EVALUATIONS', 1), self.assertRaisesRegex(ValueError, 'scalar-evaluation'):
            a.compile(value)
        with patch.object(a, 'MAX_SESSIONS', 1), self.assertRaisesRegex(ValueError, 'session'):
            a.compile(v2(chain(24)))
        with patch.object(a, 'MAX_WORK', 1), self.assertRaisesRegex(ValueError, 'work'):
            a.compile(v2(program()))

    def test_generated_branching_programs_and_numerical_edges(self):
        rng = random.Random(237)
        for _ in range(40):
            nodes = [dict(id='n0', op='load', view='v')]
            for i in range(1, rng.randrange(16, 40)):
                op = rng.choice(['add', 'mul', 'max', 'max_i32', 'relu_i32', 'add_imm', 'ge_imm'])
                node = dict(id=f'n{i}', op=op, args=[f'n{rng.randrange(i)}' for _ in range(a.OPS[op])])
                if op in ('add_imm', 'ge_imm'):
                    node['imm'] = rng.randrange(16)
                nodes.append(node)
            s = source(1, 4, nodes); s['inputs'][0]['words'] = [rng.getrandbits(32) for _ in range(4)]
            self.check(v2(program(s)))


if __name__ == '__main__':
    unittest.main()
