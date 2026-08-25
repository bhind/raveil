import copy
import json
from pathlib import Path
import tempfile
import unittest

from raveil.graph_device_affine import (
    CONFIG_MAGIC,
    GraphDeviceAffineError,
    affine_oracle,
    compile_artifact,
    config_bytes,
    config_words,
    expected_transactions,
    finalize,
    install_abi_id,
    load_install_abi,
    prepare,
    profile,
    profiles,
    software_fallback,
    source_id,
    validate_config_words,
    validate_profile,
)
from raveil.graph_device_mvp import device_abi_id, load_device_abi
from raveil.riscv_stencil_signature import input_words


ROOT = Path(__file__).resolve().parents[1]
CHISEL = ROOT / "hardware" / "chisel"


class GraphDeviceAffineTests(unittest.TestCase):
    def _trace_line(self, transaction: dict[str, object]) -> str:
        data = transaction["data"] if transaction["data"] is not None else 0
        return (
            "GraphDevice-TRACE-V1 event=transaction "
            f"write={int(bool(transaction['write']))} "
            f"address={transaction['address']} data={int(data):08x}"
        )

    def _prepared(self, root: Path) -> Path:
        evidence = root / "evidence"
        prepare(evidence)
        runs = (("baseline", 1, 0), ("compact", 2, 0), ("compact", 4, 1))
        lines = [
            "GraphDevice-AFFINE-NEGATIVE-V1 partial=FAULT order=FAULT "
            "duplicate=FAULT digest=FAULT busy=FAULT mutation=0 cases=5"
        ]
        for name, seed, restart in runs:
            oracle_path = evidence / "oracles" / f"{name}-seed-{seed}.bin"
            output_path = evidence / f"private-output-{name}-seed-{seed}.bin"
            output_path.write_bytes(oracle_path.read_bytes())
            words = [
                int.from_bytes(oracle_path.read_bytes()[index:index + 4], "little")
                for index in range(0, oracle_path.stat().st_size, 4)
            ]
            active = profile(name)["active_outputs"]
            checksum = sum(words[:active]) & 0xFFFFFFFFFFFFFFFF
            polls = 3072 if name == "baseline" else 768
            lines.append(
                "GraphDevice-AFFINE-RUN-V1 "
                f"profile={name} seed={seed} status=COMPLETED staged_words=324 "
                f"polls={polls} output_valid=1 output_words=256 "
                f"active_outputs={active} checksum={checksum:016x} restart={restart}"
            )
        lines.extend([
            "GraphDevice-AFFINE-CANCEL-V1 profile=compact seed=3 "
            "status=CANCELLED output_valid=0 output_words=0 blocked_read=1 published=0",
            "GraphDevice-AFFINE-RUNTIME-V1 status=OK completed=3 cancelled=1 "
            "resets=10 profiles=2 invalid_cases=5 "
            "evidence=rtl-simulation-functional performance=not-measured",
        ])
        (evidence / "device.log").write_text("\n".join(lines) + "\n", encoding="ascii")
        (evidence / "environment.txt").write_text(
            "schema=raveil.graph-device-affine-environment/v1\n"
            "platform=linux/amd64\n"
            f"dockerfile_sha256={'b' * 64}\n"
            f"image_id=sha256:{'c' * 64}\n"
            "Scala CLI version: 1.10.1\n"
            'openjdk version "17.0.19"\n'
            "Verilator 4.038\n",
            encoding="ascii",
        )
        (evidence / "simulator.sha256").write_text("a" * 64 + "\n", encoding="ascii")
        trace = ["GraphDevice-TRACE-V1 event=reset", "GraphDevice-TRACE-V1 event=start"]
        trace.extend(
            self._trace_line(item)
            for item in expected_transactions(profile("baseline"), 3)[:1]
        )
        trace.extend([
            "GraphDevice-TRACE-V1 event=cancel",
            "GraphDevice-TRACE-V1 event=reset",
            "GraphDevice-TRACE-V1 event=start",
        ])
        trace.extend(
            self._trace_line(item)
            for item in expected_transactions(profile("baseline"), 1)
        )
        trace.extend([
            "GraphDevice-TRACE-V1 event=reset",
            "GraphDevice-TRACE-V1 event=start",
        ])
        trace.extend(
            self._trace_line(item)
            for item in expected_transactions(profile("compact"), 2)
        )
        trace.append("GraphDevice-TRACE-V1 event=reset")
        trace.append("GraphDevice-TRACE-V1 event=start")
        trace.extend(
            self._trace_line(item)
            for item in expected_transactions(profile("compact"), 3)[:9]
        )
        trace.extend([
            "GraphDevice-TRACE-V1 event=cancel",
            "GraphDevice-TRACE-V1 event=reset",
            "GraphDevice-TRACE-V1 event=start",
        ])
        trace.extend(
            self._trace_line(item)
            for item in expected_transactions(profile("compact"), 4)
        )
        (evidence / "transaction-trace.txt").write_text(
            "\n".join(trace) + "\n", encoding="ascii"
        )
        return evidence

    def test_abi_profiles_and_artifact_are_deterministic(self) -> None:
        abi = load_install_abi()
        self.assertEqual(abi["max_payload_words"], 16)
        self.assertEqual([value["name"] for value in profiles()], ["baseline", "compact"])
        self.assertEqual(
            [len(expected_transactions(value, 1)) for value in profiles()],
            [1536, 384],
        )
        first = compile_artifact()
        self.assertEqual(first, compile_artifact())
        self.assertEqual(first["execution_abi_sha256"], device_abi_id(load_device_abi()))
        self.assertEqual(first["install_abi_sha256"], install_abi_id())
        self.assertEqual(first["source_sha256"], source_id())
        self.assertEqual(first["evidence_class"], "rtl-simulation-functional")
        self.assertEqual(first["performance"], "not-measured")

    def test_oracle_fallback_parity_and_inactive_tail(self) -> None:
        for value in profiles():
            for seed in (1, 2, 3, 4):
                expected = affine_oracle(input_words(seed), value)
                self.assertEqual(expected, software_fallback(input_words(seed), value))
                self.assertTrue(all(word == 0 for word in expected[value["active_outputs"]:]))

    def test_payload_is_fixed_width_little_endian_and_whitelisted(self) -> None:
        baseline = profile("baseline")
        compact = profile("compact")
        self.assertEqual(len(config_bytes(baseline)), 64)
        self.assertEqual(config_bytes(baseline)[:4], CONFIG_MAGIC.to_bytes(4, "little"))
        self.assertEqual(validate_config_words(config_words(compact)), compact)
        bad_payloads = [config_words(compact)[:15], list(reversed(config_words(compact)))]
        changed_digest = config_words(compact)
        changed_digest[8] ^= 1
        bad_payloads.append(changed_digest)
        for payload in bad_payloads:
            with self.subTest(payload_words=len(payload)):
                with self.assertRaises(GraphDeviceAffineError):
                    validate_config_words(payload)

    def test_bounds_identity_and_unknown_profile_fail_closed(self) -> None:
        bad_stride = copy.deepcopy(profile("compact"))
        bad_stride["input_stride"] = 8
        with self.assertRaises(GraphDeviceAffineError):
            validate_profile(bad_stride)
        bad_identity = copy.deepcopy(profile("compact"))
        bad_identity["configuration_sha256"] = profile("baseline")["configuration_sha256"]
        with self.assertRaises(GraphDeviceAffineError):
            config_words(bad_identity)
        with self.assertRaises(GraphDeviceAffineError):
            profile("unknown")

    def test_prepare_binds_headers_payloads_inputs_oracles_and_source(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            evidence = Path(temporary) / "evidence"
            artifact = prepare(evidence)
            self.assertEqual(
                json.loads((evidence / "affine-artifact.json").read_text()), artifact
            )
            self.assertTrue((evidence / "graph_device_abi_generated.h").is_file())
            self.assertTrue((evidence / "graph_device_affine_generated.h").is_file())
            self.assertEqual((evidence / "config-baseline.bin").read_bytes(), config_bytes(profile("baseline")))
            self.assertEqual((evidence / "config-compact.bin").read_bytes(), config_bytes(profile("compact")))
            self.assertEqual((evidence / "inputs" / "seed-4.bin").stat().st_size, 324 * 4)
            self.assertEqual(
                (evidence / "oracles" / "compact-seed-4.bin").stat().st_size,
                256 * 4,
            )

    def test_finalizer_binds_complete_matrix_and_is_append_once(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            evidence = self._prepared(Path(temporary))
            receipt = finalize(evidence)
            self.assertEqual(receipt["completed_transaction_counts"], [1536, 384, 384])
            self.assertEqual(receipt["cancelled_transaction_counts"], [1, 9])
            self.assertTrue(receipt["trace_equivalent"])
            self.assertTrue(receipt["store_data_oracle_match"])
            self.assertTrue(receipt["inactive_tail_zero"])
            self.assertTrue(receipt["execution_abi_unchanged"])
            self.assertFalse(receipt["rtl_regenerated_per_profile"])
            self.assertEqual(len(receipt["runs"]), 3)
            with self.assertRaisesRegex(GraphDeviceAffineError, "append-once"):
                finalize(evidence)

    def test_finalizer_rejects_output_trace_config_header_and_log_tamper(self) -> None:
        mutations = (
            ("output", "private-output-compact-seed-2.bin"),
            ("trace", "transaction-trace.txt"),
            ("config", "config-compact.bin"),
            ("header", "graph_device_affine_generated.h"),
            ("log", "device.log"),
            ("environment", "environment.txt"),
        )
        for label, relative in mutations:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                evidence = self._prepared(Path(temporary))
                path = evidence / relative
                if label == "environment":
                    text = path.read_text(encoding="ascii")
                    path.write_text(
                        text.replace("platform=linux/amd64", "platform=linux/arm64"),
                        encoding="ascii",
                    )
                else:
                    payload = bytearray(path.read_bytes())
                    payload[len(payload) // 2] ^= 1
                    path.write_bytes(payload)
                with self.assertRaises((GraphDeviceAffineError, UnicodeError)):
                    finalize(evidence)

    def test_installer_core_runtime_and_runners_preserve_boundaries(self) -> None:
        installer = (CHISEL / "GraphDeviceAffineConfigInstaller.scala").read_text()
        core = (CHISEL / "chipyard-overlay" / "RaveilStaticStencilCore.scala").read_text()
        runtime = (CHISEL / "graph_device_affine_runtime.cpp").read_text()
        wrapper = (CHISEL / "graph_device_verilator.cpp").read_text()
        runner = (CHISEL / "run-graph-device-affine.sh").read_text()
        inner = (CHISEL / "run-graph-device-affine-in-container.sh").read_text()
        self.assertIn("io.address =/= nextIndex", installer)
        self.assertIn('seen =/= "hffff".U', installer)
        self.assertIn("io.busy || !loadingReg || faultReg", installer)
        self.assertIn("logicalRow := outputIndex / io.columns", core)
        self.assertIn("lastOutput", core)
        self.assertIn("run_invalid_matrix", runtime)
        self.assertIn("RAVEIL_AFFINE_RUNTIME", wrapper)
        self.assertIn("--network none", runner)
        self.assertIn("cmp /evidence/rtl-first.hashes", inner)
        self.assertIn("performance=not-measured", runtime)
        for forbidden in ("Vivado", "bitstream", "UIO", "/dev/mem"):
            self.assertNotIn(forbidden, runner + inner + runtime)

    def test_source_is_task_neutral_and_execution_abi_is_unchanged(self) -> None:
        source = (ROOT / "raveil" / "graph_device_affine.py").read_text()
        for forbidden in ("T-0114", "G3", "t0114", "t0113"):
            self.assertNotIn(forbidden, source)
        abi = (ROOT / "contracts" / "graph_device_abi_v1.json").read_text()
        self.assertNotIn("affine", abi.lower())
        self.assertNotIn("install", abi.lower())


if __name__ == "__main__":
    unittest.main()
