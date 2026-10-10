"""Host-only differential tests for independent global-grid semantics."""
import copy
import random
import unittest
from raveil import grid_kernel as k, project_graph as g
from raveil.project import encoded
from raveil.graph_device_dag import graph_oracle


def rich_kernel():
    # Deliberately includes forward references; all seven existing opcodes.
    return {"schema": k.KERNEL, "graph_id": "editable-rich", "nodes": [
        {"id": "decision", "op": "GE_IMM_U32", "input": "bias", "immediate": 1000},
        {"id": "bias", "op": "ADD_IMM_U32", "input": "max", "immediate": 7},
        {"id": "center", "op": "LOAD_U32", "address": {"row_delta": 0, "column_delta": 0}},
        {"id": "diagonal", "op": "LOAD_U32", "address": {"row_delta": -1, "column_delta": 1}},
        {"id": "sum", "op": "ADD_U32", "inputs": ["center", "diagonal"]},
        {"id": "square", "op": "MUL_U32", "inputs": ["sum", "sum"]},
        {"id": "max", "op": "MAX_U32", "inputs": ["square", "center"]},
        {"id": "out", "op": "STORE_U32", "input": "decision"}]}


def grid(rows, columns, seed=3):
    rng = random.Random(seed)
    return {"schema": k.INPUT, "rows": rows, "columns": columns,
            "words": [rng.randrange(1 << 32) for _ in range(rows * columns)]}


def direct_rich(data, mode):
    rows, cols, words = data['rows'], data['columns'], data['words']
    result = []
    for r in range(rows):
        for c in range(cols):
            nr, nc = r - 1, c + 1
            if mode == 'wrap': nr, nc = nr % rows, nc % cols
            if mode == 'clamp': nr, nc = max(nr, 0), min(nc, cols - 1)
            neighbor = words[nr * cols + nc] if 0 <= nr < rows and 0 <= nc < cols else 0
            center = words[r * cols + c]
            summed = (center + neighbor) & 0xffffffff
            square = summed * summed & 0xffffffff
            biased = (max(square, center) + 7) & 0xffffffff
            result.append(int(biased >= 1000))
    return result


class GridKernelTests(unittest.TestCase):
    def test_full_limit_serialization_and_exact_types(self):
        value = grid(64, 64); value['words'] = [0xffffffff] * 4096
        self.assertGreater(len(encoded(value)), 65536)
        self.assertEqual(k.read_input(encoded(value)), value)
        for patch in ({'rows': 0}, {'rows': 65}, {'columns': True}, {'rows': 1.0},
                      {'words': [0] * 4095}, {'words': [False] * 4096}, {'words': [-1] * 4096},
                      {'words': [1 << 32] * 4096}, {'extra': 0}, {'schema': 'unknown'}):
            with self.subTest(patch=list(patch)), self.assertRaises(ValueError):
                k.read_input(encoded({**value, **patch}))
        with self.assertRaises(ValueError): k.read_input(b' ' * (128 * 1024 + 1))
        with self.assertRaises(ValueError): k.read_input(b'{"schema":1,"schema":2}')

    def test_all_ops_forward_dependencies_against_direct_formula(self):
        desc = k.compile_kernel(encoded(rich_kernel()))
        for shape in ((1,1),(1,64),(64,1),(17,19),(16,16),(31,33),(64,64)):
            data = grid(*shape)
            for mode in k.BOUNDARIES:
                with self.subTest(shape=shape, mode=mode):
                    self.assertEqual(k.reference(data, desc, mode), direct_rich(data, mode))

    def test_modular_wrap_occurs_before_max_and_comparison(self):
        desc = k.compile_kernel(encoded(rich_kernel()))
        data = grid(1, 4); data['words'] = [0xffffffff, 0xfffffffe, 0, 0x10000]
        self.assertEqual(k.reference(data, desc, 'zero'), [0, 0, 0, 1])
        self.assertEqual(k.reference(data, desc, 'wrap'), direct_rich(data, 'wrap'))

    def test_partial_tile_differential_against_existing_graph_oracle(self):
        desc = k.compile_kernel(encoded(rich_kernel()))
        for shape in ((1,1),(1,64),(64,1),(17,19),(31,33),(64,64)):
            data = grid(*shape)
            for mode in k.BOUNDARIES:
                assembled = [None] * len(data['words'])
                for tile in k.layout(data):
                    output = graph_oracle(desc, k.halo(data, tile, mode))
                    for r in range(tile['rows']):
                        for c in range(tile['columns']):
                            index = (tile['row'] + r) * shape[1] + tile['column'] + c
                            self.assertIsNone(assembled[index])
                            assembled[index] = output[r * 16 + c]
                self.assertEqual(assembled, direct_rich(data, mode), (shape, mode))

    def test_global_boundary_halos_not_tile_local(self):
        data = grid(17, 19); data['words'] = list(range(323))
        last = k.layout(data)[-1]
        self.assertEqual((last['row'], last['column'], last['rows'], last['columns']), (16,16,1,3))
        # (global17,19) is the right/bottom exterior, not a tile-local edge.
        for mode, expected in (('zero',0), ('clamp',322), ('wrap',0)):
            self.assertEqual(k.halo(data,last,mode)[2*18+4],expected)
        self.assertEqual(k.halo(data,last,'wrap')[2*18+5],1)
        self.assertEqual(k.halo(data,last,'zero')[0],15*19+15)

    def test_kernel_rejects_cycles_invalid_ops_types_and_capacity(self):
        base = rich_kernel()
        mutations = []
        def changed(edit):
            value = copy.deepcopy(base); edit(value); mutations.append(value)
        changed(lambda v: v.update(extra=1))
        changed(lambda v: v['nodes'][0].update(input='decision'))
        changed(lambda v: v['nodes'][0].update(input='missing'))
        changed(lambda v: v['nodes'][0].update(op='DIV_U32'))
        changed(lambda v: v['nodes'][0].update(immediate=True))
        changed(lambda v: v['nodes'][0].update(immediate=1<<22))
        changed(lambda v: v['nodes'][2]['address'].update(row_delta=2))
        changed(lambda v: v['nodes'][2]['address'].update(column_delta=False))
        changed(lambda v: v['nodes'].extend(v['nodes'] * 3))
        for value in mutations:
            with self.assertRaises(ValueError): k.compile_kernel(encoded(value))
        with self.assertRaises(ValueError): k.compile_kernel(b' ' * (16*1024+1))
        for mode in ('mirror',None,True,[]):
            with self.assertRaises(ValueError): k.boundary(mode)

    def test_unsigned_max_and_ge_and_immediate_endpoints(self):
        value = rich_kernel()
        value['nodes'][0]['immediate'] = 0
        value['nodes'][1]['immediate'] = (1<<22)-1
        desc = k.compile_kernel(encoded(value))
        self.assertEqual(k.reference(grid(2, 3), desc, 'wrap'), [1]*6)
        self.assertEqual(g.compile_graph(desc)['instruction_count'],8)


if __name__ == '__main__': unittest.main()
