from pathlib import Path
import unittest

from raveil.riscv_stencil_signature import (
    RiscvStencilSignatureError,
    input_words,
    parse_signature,
    validate_signature,
)
from raveil.static_region import static_stencil_oracle


ROOT = Path(__file__).resolve().parents[1]
C_SOURCE = ROOT / "hardware" / "chisel" / "riscv_stencil_smoke.c"
ASM_SOURCE = ROOT / "hardware" / "chisel" / "riscv_stencil_smoke.S"
SCRATCHPAD_LINKER = (
    ROOT / "hardware" / "chisel" / "riscv_stencil_system_scratchpad.ld"
)


class RiscvStencilSignatureTests(unittest.TestCase):
    def test_independent_oracle_accepts_exact_signature(self) -> None:
        expected = static_stencil_oracle(input_words(1))
        text = "".join(f"{word:08x}\n" for word in expected)
        self.assertEqual(validate_signature(text), expected)

    def test_signature_shape_and_word_drift_fail_closed(self) -> None:
        expected = static_stencil_oracle(input_words(1))
        lines = [f"{word:08x}" for word in expected]
        with self.assertRaisesRegex(RiscvStencilSignatureError, "256"):
            parse_signature("\n".join(lines[:-1]))
        lines[17] = f"{expected[17] ^ 1:08x}"
        with self.assertRaisesRegex(RiscvStencilSignatureError, "output 17"):
            validate_signature("\n".join(lines))

    def test_riscv_workload_has_exact_shapes_and_private_signature(self) -> None:
        c_source = C_SOURCE.read_text(encoding="utf-8")
        assembly = ASM_SOURCE.read_text(encoding="utf-8")
        self.assertIn("input_words[324]", c_source)
        self.assertIn("output_words[256]", c_source)
        self.assertIn("y <= 16U", c_source)
        self.assertIn("x <= 16U", c_source)
        self.assertIn("begin_signature", assembly)
        self.assertIn("end_signature", assembly)
        self.assertIn(".space 1024", assembly)
        self.assertIn("BOOM_SERIALIZE_DISPATCH", assembly)

    def test_system_scratchpad_linker_separates_buffers_from_control(self) -> None:
        assembly = ASM_SOURCE.read_text(encoding="utf-8")
        linker = SCRATCHPAD_LINKER.read_text(encoding="utf-8")
        self.assertIn("RFC0005_SYSTEM_SCRATCHPAD", assembly)
        self.assertIn(".scratchpad.input", assembly)
        self.assertIn(".scratchpad.signature", assembly)
        self.assertIn(". = 0x80000000", linker)
        self.assertIn(". = 0x08000000", linker)
        self.assertIn("64K", linker)
        self.assertLess(linker.index(".tohost"), linker.index(".scratchpad (NOLOAD)"))


if __name__ == "__main__":
    unittest.main()
