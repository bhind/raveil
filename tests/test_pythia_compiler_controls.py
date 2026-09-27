"""Meaningful failure/binding tests; builds are an explicit offline acceptance run."""
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

PROBES = Path(__file__).resolve().parents[1] / 'docs/research/probes'
sys.path.insert(0, str(PROBES))
import pythia_compiler_controls as controls
import pythia_affine_reference as ref


class CompilerControlTests(unittest.TestCase):
    def test_wrong_source_never_invokes_tool_or_creates_output(self):
        for data in (b'', b'\0'*131072):
            with self.subTest(length=len(data)), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                (root/'weight.f16').write_bytes(data)
                with patch.object(controls, 'command', side_effect=AssertionError('tool reached')):
                    with self.assertRaisesRegex(ValueError, 'source (byte length|SHA-256) mismatch'):
                        controls.run(root, root/'output')
                self.assertFalse((root/'output').exists())

    def test_hex_literals_round_trip_all_finite_halves(self):
        for bits in range(65536):
            if (bits>>10)&31 == 31:
                continue
            v = struct.unpack('<e', struct.pack('<H', bits))[0]
            self.assertEqual(struct.pack('<f', float.fromhex(v.hex())), struct.pack('<f', v))

    def test_same_reduction_body_and_no_retention_getters(self):
        weights, bias = [0.5]*(512*128), [-0.5]*512
        for mode in controls.MODES:
            runtime = controls.generate(weights, bias, False, mode)
            fixed = controls.generate(weights, bias, True, mode)
            body = fixed.split('void affine',1)[1].replace('W[','w[').replace('B[','b[')
            self.assertEqual(body, runtime.split('void affine',1)[1])
            self.assertNotIn('fixed_w', fixed)
            self.assertIn('0x1.0000000000000p-1f', fixed)

    def test_corrupt_output_cannot_pass_common_oracle(self):
        with self.assertRaisesRegex(ValueError, 'envelope exceeded'):
            ref.validate([1.0], [0], [0])
        for v in (float('nan'), float('inf')):
            with self.assertRaisesRegex(ValueError, 'finite binary32'):
                ref.validate([v], [0], [1])

    def test_instruction_inventory_excludes_directives_and_other_functions(self):
        asm = '_affine:\n\t.cfi_startproc\n\tfmul.4s v0, v1, v2\nLBB0_1:\n\tret\n\t.cfi_endproc\n_other:\n\tfadd s1, s2, s3\n'
        inventory = controls.kernel_assembly(asm)
        self.assertEqual(inventory['static_instruction_histogram'], {'fmul.4s':1, 'ret':1})


if __name__ == '__main__':
    unittest.main()
