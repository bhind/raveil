"""Host checks for the bounded T-0185 workload staging pack.

These checks use independent domain formulas and are not RTL evidence.
"""
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from raveil.graph_device_dag import compile_descriptor, graph_oracle, software_fallback
from raveil.project import Project, init_project
from raveil.project_graph import input_bytes


ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "examples" / "graph-workloads"
MASK = 0xFFFFFFFF


def load(name):
    return json.loads((PACK / "inputs" / name).read_text(encoding="ascii"))


def cross_domain_oracle(words):
    output = [0] * 256
    for row in range(8):
        for column in range(8):
            center = (row + 1) * 10 + column + 1
            output[row * 8 + column] = max(
                words[center], words[center - 10], words[center + 10],
                words[center - 1], words[center + 1],
            )
    return output


def energy_domain_oracle(words, bias=17):
    output = [0] * 256
    for row in range(8):
        for column in range(8):
            sample = words[(row + 1) * 10 + column + 1]
            output[row * 8 + column] = (sample * sample + bias) & MASK
    return output


class GraphWorkloadExampleTests(unittest.TestCase):
    def descriptor_and_words(self, stem):
        descriptor = load(f"{stem}-descriptor.json")
        payload = (PACK / "inputs" / f"{stem}-input.json").read_bytes()
        decoded = json.loads(payload)
        self.assertEqual(len(input_bytes(payload)), 324 * 4)
        return descriptor, decoded["words"]

    def assert_three_oracles(self, descriptor, words, domain):
        expected = domain(words)
        program = compile_descriptor(descriptor)
        self.assertEqual(program["affine"], {
            "rows": 8, "columns": 8, "input_stride": 10, "output_stride": 8,
        })
        self.assertEqual(graph_oracle(descriptor, words), expected)
        self.assertEqual(software_fallback(program, words), expected)

    def test_pack_has_exactly_two_snapshot_recipes(self):
        names = sorted(path.name for path in (PACK / "recipes").glob("*.json"))
        self.assertEqual(names, ["cross-dilate-binary.json", "sensor-energy-bias.json"])
        for name in names:
            recipe = json.loads((PACK / "recipes" / name).read_text(encoding="ascii"))
            self.assertEqual(recipe["schema"], "raveil.project-recipe/v2")
            self.assertEqual(recipe["kind"], "graph-device")
            self.assertEqual(set(recipe), {"schema", "kind", "descriptor", "input"})
            self.assertTrue((PACK / "inputs" / recipe["descriptor"]).is_file())
            self.assertTrue((PACK / "inputs" / recipe["input"]).is_file())

    def test_pack_stages_through_existing_project_discovery_and_show(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "workspace"
            init_project(root)
            for folder in ("recipes", "inputs"):
                for source in (PACK / folder).iterdir():
                    shutil.copyfile(source, root / folder / source.name)
            project = Project(root)
            listed = project.recipes()
            self.assertIn("cross-dilate-binary: graph-device; backends=rtl-sim", listed)
            self.assertIn("sensor-energy-bias: graph-device; backends=rtl-sim", listed)
            self.assertIn("instructions=10/16", project.show("cross-dilate-binary"))
            self.assertIn("instructions=4/16", project.show("sensor-energy-bias"))

    def test_cross_dilation_matches_independent_domain_oracle(self):
        descriptor, words = self.descriptor_and_words("cross-dilate-binary")
        self.assertEqual(compile_descriptor(descriptor)["instruction_count"], 10)
        self.assert_three_oracles(descriptor, words, cross_domain_oracle)
        output = cross_domain_oracle(words)
        self.assertEqual(sum(output), 15)
        self.assertEqual(set(output), {0, 1})

    def test_cross_halo_is_semantic_but_transport_padding_is_not(self):
        descriptor, words = self.descriptor_and_words("cross-dilate-binary")
        baseline = cross_domain_oracle(words)
        north_halo = words.copy()
        north_halo[1] = 1
        self.assertEqual(cross_domain_oracle(north_halo)[0], 1)
        self.assertNotEqual(cross_domain_oracle(north_halo), baseline)
        for index in (100, 323):
            padding = words.copy()
            padding[index] = MASK
            self.assertEqual(cross_domain_oracle(padding), baseline)
            self.assertEqual(graph_oracle(descriptor, padding), baseline)

    def test_energy_bias_wraps_as_uint32_and_matches_three_oracles(self):
        descriptor, words = self.descriptor_and_words("sensor-energy-bias")
        self.assertEqual(compile_descriptor(descriptor)["instruction_count"], 4)
        self.assert_three_oracles(descriptor, words, energy_domain_oracle)
        first_row = energy_domain_oracle(words)[:8]
        self.assertEqual(first_row, [17, 18, 21, 4294836242, 17, 18, 21, 18])

    def test_energy_transport_padding_is_ignored(self):
        descriptor, words = self.descriptor_and_words("sensor-energy-bias")
        baseline = energy_domain_oracle(words)
        for index in (100, 323):
            padding = words.copy()
            padding[index] = MASK
            self.assertEqual(energy_domain_oracle(padding), baseline)
            self.assertEqual(graph_oracle(descriptor, padding), baseline)


if __name__ == "__main__":
    unittest.main()
