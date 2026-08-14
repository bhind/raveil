import pathlib
import re
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class PhysicalProxyToolchainTests(unittest.TestCase):
    def test_toolchain_is_pinned_and_commissioning_only(self) -> None:
        dockerfile = (ROOT / "hardware/chisel/Dockerfile.physical-proxy").read_text()
        self.assertIn("mambaorg/micromamba:1.4.2", dockerfile)
        self.assertIn("yosys=0.27_4_gb58664d44", dockerfile)
        self.assertIn("openroad=2.0_7070_g0264023b6", dockerfile)
        self.assertIn("open_pdks.sky130a=1.0.457_0_g32e8f23", dockerfile)
        self.assertIn("libgomp=15.2.0", dockerfile)
        self.assertIn("libgl1=1.3.2-1", dockerfile)
        self.assertNotRegex(dockerfile, re.compile(r"\b(latest|master|main)\b"))

        inner = (
            ROOT / "hardware/chisel/run-physical-proxy-smoke-in-container.sh"
        ).read_text()
        self.assertIn("evidence=synthesis-toolchain-commissioning", inner)
        self.assertIn("performance=not-measured", inner)
        self.assertIn("sky130_fd_sc_hd__tt_025C_1v80.lib", inner)
        self.assertIn("stat -liberty", inner)
        self.assertIn("report_checks", inner)
        self.assertIn("sta -exit", inner)
        self.assertIn("conda_environment_sha256", inner)
        self.assertIn("system_packages_sha256", inner)

    def test_outer_wrapper_is_offline_and_hash_binds_inputs(self) -> None:
        wrapper = (
            ROOT / "hardware/chisel/run-physical-proxy-toolchain-smoke.sh"
        ).read_text()
        self.assertIn("--network none", wrapper)
        self.assertIn("--security-opt no-new-privileges=true", wrapper)
        self.assertIn("docker image inspect", wrapper)
        self.assertIn("--provenance=false", wrapper)
        self.assertIn("Dockerfile.physical-proxy", wrapper)
        self.assertIn("physical_proxy_smoke.sv", wrapper)
        self.assertIn("physical_proxy_smoke.sdc", wrapper)
        self.assertIn("run-physical-proxy-smoke-in-container.sh", wrapper)
        self.assertIn("performance=not-measured", wrapper)

    def test_smoke_is_not_a_candidate(self) -> None:
        smoke = (ROOT / "hardware/chisel/physical_proxy_smoke.sv").read_text()
        self.assertIn("module PhysicalProxySmoke", smoke)
        self.assertNotIn("StaticStencilRegion", smoke)
        self.assertNotIn("Rocket", smoke)
        self.assertNotIn("Boom", smoke)


if __name__ == "__main__":
    unittest.main()
