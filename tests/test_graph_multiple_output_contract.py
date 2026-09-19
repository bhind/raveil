"""T-0183 planning vectors, not a multi-output runtime implementation."""
import copy
import json
import re
from pathlib import Path
import unittest

from raveil.graph_device_dag import compile_descriptor, graph_oracle, GraphDeviceDagError

ROOT = Path(__file__).resolve().parents[1]


class MultipleOutputContractTests(unittest.TestCase):
    def setUp(self):
        self.biased = json.loads((ROOT / "examples/graph-workloads/inputs/sensor-energy-bias-descriptor.json").read_text())
        self.raw = copy.deepcopy(self.biased)
        self.raw["graph_id"] = "sensor-energy-raw"
        self.raw["nodes"] = self.raw["nodes"][:2] + [{"id": "store", "op": "STORE_U32", "input": "energy"}]

    def test_two_current_single_output_graphs(self):
        for graph in (self.raw, self.biased):
            compile_descriptor(graph)
        values = [0, 1, 65535, 65536, 0xffffffff, 0x80000000, 17]
        words = [values[i % len(values)] for i in range(324)]
        raw = graph_oracle(self.raw, words)
        biased = graph_oracle(self.biased, words)
        for row in range(8):
            for col in range(8):
                x = words[(row + 1) * 10 + col + 1]
                offset = row * 8 + col
                self.assertEqual(raw[offset], (x * x) & 0xffffffff)
                self.assertEqual(biased[offset], (x * x + 17) & 0xffffffff)
        self.assertEqual(raw[64:], [0] * 192)
        self.assertEqual(biased[64:], [0] * 192)

    def test_current_zero_output_is_rejected(self):
        graph = copy.deepcopy(self.raw)
        graph["nodes"] = graph["nodes"][:-1]
        with self.assertRaisesRegex(GraphDeviceDagError, "exactly one final STORE"):
            compile_descriptor(graph)

    def test_current_two_output_is_rejected(self):
        graph = copy.deepcopy(self.biased)
        graph["nodes"].insert(-1, {"id": "raw-store", "op": "STORE_U32", "input": "energy"})
        with self.assertRaisesRegex(GraphDeviceDagError, "STORE_U32 is invalid"):
            compile_descriptor(graph)

    def test_scalar_wraparound_is_not_saturation(self):
        for x, raw, biased in ((0, 0, 17), (65536, 0, 17), (0xffffffff, 1, 18)):
            self.assertEqual((x * x) & 0xffffffff, raw)
            self.assertEqual((x * x + 17) & 0xffffffff, biased)

    def test_proposed_name_contract(self):
        # Planning predicate only; no runtime admission implementation here.
        def names_valid(names):
            return (1 <= len(names) <= 2 and len(set(names)) == len(names)
                    and all(re.fullmatch(r"[a-z][a-z0-9_-]{0,30}", name, flags=re.ASCII) for name in names))
        for names in (["raw", "biased"], ["a" * 31], ["schema", "outputs"]):
            self.assertTrue(names_valid(names))
        for names in ([], ["a", "b", "c"], ["raw", "raw"], [""], ["a" * 32],
                      ["../raw"], ["raw/child"], ["raw\n"], ["raw\t"], ["Raw"], ["é"], ["e\u0301"]):
            self.assertFalse(names_valid(names))

    def test_proposed_ordered_names_are_values_not_paths(self):
        plan = [{"name": name, "slot": slot} for slot, name in enumerate(("raw", "biased"))]
        self.assertEqual(plan, [{"name": "raw", "slot": 0}, {"name": "biased", "slot": 1}])


if __name__ == "__main__":
    unittest.main()
