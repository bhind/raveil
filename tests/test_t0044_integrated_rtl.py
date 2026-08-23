import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from raveil.t0044_integrated_rtl import (
    CLOCK_ROOTS,
    MEMORY_MACRO_CONTRACT,
    MEMORY_MACRO_COUNTS,
    MEMORY_MACRO_PORTS,
    VARIANTS,
    analyze_clock_inventory,
    analyze_export,
    analyze_hierarchy,
    compare_reports,
    load_rtlil_hierarchy,
    validate_export,
)
from raveil.t0044_physical import tree_sha256


ROOT = Path(__file__).parents[1]
HEX = "a" * 64


def hierarchy_document(*, graph: bool, rocket_count: int = 1):
    ports = {
        "clock_uncore": {"direction": "input", "bits": [1]},
        "jtag_TCK": {"direction": "input", "bits": [2]},
        "serial_tl_0_clock_in": {"direction": "input", "bits": [3]},
        "reset_io": {"direction": "input", "bits": [4]},
        "custom_boot": {"direction": "input", "bits": [5]},
        "axi4_mem_0_clock": {"direction": "output", "bits": [6]},
        "clock_tap": {"direction": "output", "bits": [7]},
    }
    system_type = "RaveilIntegratedGraphDigitalTop" if graph else "DigitalTop"
    top_cells = {"system": {"type": system_type}}
    system_cells = {
        "rocket": {"type": "Rocket"},
        "dcache": {"type": "DCache"},
        "xbar": {"type": "TLXbar"},
        "owned": {"type": "RaveilOwnedTLMemory"},
    }
    if rocket_count == 0:
        system_cells.pop("rocket")
    for index in range(1, rocket_count):
        system_cells[f"rocket_{index}"] = {"type": "Rocket"}
    if graph:
        system_cells["core"] = {"type": "RaveilStaticStencilCore"}
        system_cells["client"] = {"type": "RaveilStaticStencilTLClient"}
    for macro_name, count in MEMORY_MACRO_COUNTS.items():
        for index in range(count):
            system_cells[f"macro_{macro_name}_{index}"] = {"type": macro_name}
    modules = {
        "ChipTop": {"ports": ports, "cells": top_cells},
        system_type: {"cells": system_cells},
        "Rocket": {"ports": {"clock": {"direction": "input", "bits": [1]}}},
        "DCache": {"cells": {}},
        "TLXbar": {"cells": {}},
        "RaveilOwnedTLMemory": {
            "cells": {"fixture": {"type": "RaveilFixtureInputProvider"}}
        },
        "RaveilFixtureInputProvider": {"cells": {}},
    }
    if graph:
        modules["RaveilStaticStencilCore"] = {"cells": {}}
        modules["RaveilStaticStencilTLClient"] = {"cells": {}}
    for module_index, (macro_name, signature) in enumerate(MEMORY_MACRO_PORTS.items()):
        next_bit = 1000 + module_index * 1000
        ports = {}
        for port_name, (direction, width) in signature.items():
            ports[port_name] = {
                "direction": direction,
                "bits": list(range(next_bit, next_bit + width)),
            }
            next_bit += width
        modules[macro_name] = {"attributes": {"blackbox": "1"}, "ports": ports}
    return {"modules": modules}


def flat_document():
    ports = hierarchy_document(graph=True)["modules"]["ChipTop"]["ports"]
    return {
        "modules": {
            "ChipTop": {
                "ports": ports,
                "cells": {
                    "main_ff": {
                        "type": "$dff",
                        "port_directions": {"CLK": "input", "D": "input", "Q": "output"},
                        "connections": {"CLK": [1], "D": ["0"], "Q": [10]},
                    },
                    "jtag_ff": {
                        "type": "$adff",
                        "port_directions": {"CLK": "input", "ARST": "input", "D": "input", "Q": "output"},
                        "connections": {"CLK": [2], "ARST": [4], "D": ["0"], "Q": [11]},
                    },
                    "serial_memory": {
                        "type": "$mem_v2",
                        "port_directions": {"RD_CLK": "input", "WR_CLK": "input"},
                        "connections": {"RD_CLK": [3], "WR_CLK": ["0"]},
                    },
                },
            }
        }
    }


def write_export(root: Path, variant: str, *, rocket_text: str = "module Rocket; endmodule\n"):
    (root / "generated-src").mkdir(parents=True)
    (root / "generated-src/ChipTop.sv").write_text("module ChipTop; endmodule\n")
    (root / "generated-src/Rocket.sv").write_text(rocket_text)
    (root / "ChipTop.top.f").write_text("generated-src/ChipTop.sv\ngenerated-src/Rocket.sv\n")
    (root / "rtl-files.txt").write_text("generated-src/ChipTop.sv\ngenerated-src/Rocket.sv\n")
    (root / "pre-firtool.fir").write_text("circuit ChipTop:\n")
    (root / "top-module-hierarchy.json").write_text("{}\n")
    (root / "lowering-provenance.txt").write_text("status=shared-elaboration-identical\n")
    macro_contract = "\n".join(MEMORY_MACRO_CONTRACT.values()) + "\n"
    (root / "memory-macro-contract.txt").write_text(macro_contract)
    rocket_hash = hashlib.sha256(rocket_text.encode()).hexdigest()
    metadata = {
        "schema": "raveil.exp-0011-rtl-export/v1",
        "variant": variant,
        "config": VARIANTS[variant],
        "top": "ChipTop",
        "performance": "not-measured",
        "chipyard_revision": "chipyard-revision",
        "rocket_revision": "rocket-revision",
        "image_id": "sha256:" + HEX,
        "normal_lowering": "normal",
        "physical_lowering": "physical",
        "rocket_rtl_sha256": rocket_hash,
        "memory_macro_contract_sha256": hashlib.sha256(macro_contract.encode()).hexdigest(),
    }
    for field in ("source_sha256", "input_sha256", "runner_sha256", "lock_sha256", "image_rootfs_sha256"):
        metadata[field] = HEX
    metadata.update({
        "rtl_sha256": tree_sha256(root / "generated-src"),
        "rtl_filelist_sha256": hashlib.sha256((root / "rtl-files.txt").read_bytes()).hexdigest(),
        "firrtl_sha256": hashlib.sha256((root / "pre-firtool.fir").read_bytes()).hexdigest(),
        "hierarchy_sha256": hashlib.sha256((root / "top-module-hierarchy.json").read_bytes()).hexdigest(),
        "lowering_provenance_sha256": hashlib.sha256((root / "lowering-provenance.txt").read_bytes()).hexdigest(),
    })
    (root / "export-metadata.json").write_text(json.dumps(metadata))


class TestIntegratedRTL(unittest.TestCase):
    def test_recursive_integrated_hierarchy(self):
        report = analyze_hierarchy(hierarchy_document(graph=True), "integrated-static-graph-rocket")
        self.assertEqual(report["rocket_instance_path"], "system/rocket")
        self.assertEqual(report["blackboxes"], len(MEMORY_MACRO_CONTRACT))

    def test_matched_baseline_excludes_graph(self):
        report = analyze_hierarchy(hierarchy_document(graph=False), "matched-rocket-system")
        self.assertFalse(any(report["graph_paths"].values()))

    def test_rocket_must_be_exactly_one(self):
        for count in (0, 2):
            with self.subTest(count=count), self.assertRaises(ValueError):
                analyze_hierarchy(
                    hierarchy_document(graph=True, rocket_count=count),
                    "integrated-static-graph-rocket",
                )

    def test_graph_presence_is_variant_specific(self):
        with self.assertRaises(ValueError):
            analyze_hierarchy(hierarchy_document(graph=False), "integrated-static-graph-rocket")
        with self.assertRaises(ValueError):
            analyze_hierarchy(hierarchy_document(graph=True), "matched-rocket-system")

    def test_reachable_blackbox_fails(self):
        document = hierarchy_document(graph=True)
        document["modules"]["Rocket"]["attributes"] = {"blackbox": "1"}
        with self.assertRaisesRegex(ValueError, "blackbox"):
            analyze_hierarchy(document, "integrated-static-graph-rocket")

    def test_memory_macro_boundary_requires_exact_count_and_ports(self):
        document = hierarchy_document(graph=True)
        document["modules"]["RaveilIntegratedGraphDigitalTop"]["cells"].pop(
            "macro_cc_dir_ext_0"
        )
        with self.assertRaisesRegex(ValueError, "memory-macro"):
            analyze_hierarchy(document, "integrated-static-graph-rocket")
        document = hierarchy_document(graph=True)
        document["modules"]["cc_dir_ext"]["ports"]["RW0_addr"]["bits"].append(99999)
        with self.assertRaisesRegex(ValueError, "port contract drift"):
            analyze_hierarchy(document, "integrated-static-graph-rocket")

    def test_required_component_and_port_fail_closed(self):
        document = hierarchy_document(graph=True)
        document["modules"]["RaveilIntegratedGraphDigitalTop"]["cells"].pop("xbar")
        with self.assertRaisesRegex(ValueError, "interconnect"):
            analyze_hierarchy(document, "integrated-static-graph-rocket")
        document = hierarchy_document(graph=True)
        document["modules"]["ChipTop"]["ports"].pop("custom_boot")
        with self.assertRaisesRegex(ValueError, "required ports"):
            analyze_hierarchy(document, "integrated-static-graph-rocket")

    def test_three_clock_roots_cover_sequential_and_memory_endpoints(self):
        report = analyze_clock_inventory(flat_document())
        self.assertEqual(report["allowed_roots"], sorted(CLOCK_ROOTS))
        self.assertEqual(report["sequential_endpoint_count"], 3)

    def test_rtlil_hierarchy_loader_keeps_only_structural_identity(self):
        text = """attribute \\top 1
module \\ChipTop
  wire input 1 \\clock_uncore
  wire width 2 output 2 \\out
  cell \\Rocket \\rocket
    connect \\clock \\clock_uncore
  end
  process $proc$ignored
  end
end
attribute \\blackbox 1
module \\Rocket
  wire input 1 \\clock
end
"""
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "hierarchy.rtlil"
            path.write_text(text)
            document = load_rtlil_hierarchy(path)
        self.assertEqual(document["modules"]["ChipTop"]["cells"]["\\rocket"]["type"], "Rocket")
        self.assertEqual(len(document["modules"]["ChipTop"]["ports"]["out"]["bits"]), 2)

    def test_rtlil_canonical_hash_elides_only_yosys_auto_ids_and_unit_order(self):
        def rocket_rtlil(
            first_id: int,
            *,
            reverse: bool,
            width: int = 1,
            source_line: int = 10,
            cell_type: str = "$and",
            input_name: str = "named_input",
        ) -> str:
            units = [
                (
                    f'  attribute \\src "generated-src/Rocket.sv:{source_line}.1-{source_line}.8"\n'
                    f"  wire $and$generated-src/Rocket.sv:{source_line}${first_id}_Y"
                ),
                (
                    f'  attribute \\src "generated-src/Rocket.sv:{source_line}.1-{source_line}.8"\n'
                    f"  cell {cell_type} $and$generated-src/Rocket.sv:{source_line}${first_id}\n"
                    f"    parameter \\Y_WIDTH {width}\n"
                    f"    connect \\A \\{input_name}\n"
                    f"    connect \\Y $and$generated-src/Rocket.sv:{source_line}${first_id}_Y\n"
                    "  end"
                ),
            ]
            if reverse:
                units.reverse()
            return "module \\Rocket\n" + "\n".join(units) + "\nend\n"

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            a_path, b_path = root / "a.rtlil", root / "b.rtlil"
            a_path.write_text(rocket_rtlil(101, reverse=False))
            b_path.write_text(rocket_rtlil(9021, reverse=True))
            a = load_rtlil_hierarchy(a_path)["modules"]["Rocket"]
            b = load_rtlil_hierarchy(b_path)["modules"]["Rocket"]
            drifts = []
            for index, kwargs in enumerate((
                {"width": 2},
                {"source_line": 11},
                {"cell_type": "$or"},
                {"input_name": "other_input"},
            )):
                drift_path = root / f"drift-{index}.rtlil"
                drift_path.write_text(rocket_rtlil(9021, reverse=True, **kwargs))
                drifts.append(
                    load_rtlil_hierarchy(drift_path)["modules"]["Rocket"]
                )
        self.assertNotEqual(a["rtlil_raw_sha256"], b["rtlil_raw_sha256"])
        self.assertEqual(a["rtlil_canonical_sha256"], b["rtlil_canonical_sha256"])
        for drift in drifts:
            self.assertNotEqual(
                a["rtlil_canonical_sha256"], drift["rtlil_canonical_sha256"]
            )

    def test_gated_clock_traces_only_approved_clock_root(self):
        document = flat_document()
        document["modules"]["ChipTop"]["cells"]["gate"] = {
            "type": "$and",
            "port_directions": {"A": "input", "B": "input", "Y": "output"},
            "connections": {"A": [1], "B": [5], "Y": [20]},
        }
        document["modules"]["ChipTop"]["cells"]["main_ff"]["connections"]["CLK"] = [20]
        report = analyze_clock_inventory(document)
        self.assertEqual(report["root_endpoint_counts"]["clock_uncore"], 1)
        self.assertEqual(report["derived_clock_bits"], ["20"])
        self.assertEqual(report["derived_clock_driver_cells"], ["gate"])

    @staticmethod
    def eicg_document():
        document = flat_document()
        document["modules"]["ChipTop"]["cells"].update({
            "eicg_latch": {
                "type": "$dlatch",
                "attributes": {
                    "src": "generated-src/ChipTop.sv:1.1-2.2|generated-src/EICG_wrapper.v:12.3-16.6",
                },
                "parameters": {
                    "WIDTH": "00000000000000000000000000000001",
                    "EN_POLARITY": "00000000000000000000000000000000",
                },
                "port_directions": {"D": "input", "EN": "input", "Q": "output"},
                "connections": {"D": [5], "EN": [1], "Q": [21]},
            },
            "eicg_gate": {
                "type": "$logic_and",
                "attributes": {
                    "src": "generated-src/ChipTop.sv:1.1-2.2|generated-src/EICG_wrapper.v:18.16-18.32",
                },
                "port_directions": {"A": "input", "B": "input", "Y": "output"},
                "connections": {"A": [21], "B": [1], "Y": [20]},
            },
        })
        document["modules"]["ChipTop"]["cells"]["main_ff"]["connections"]["CLK"] = [20]
        return document

    def test_exact_eicg_traces_raw_clock_not_control_latch(self):
        report = analyze_clock_inventory(self.eicg_document())
        self.assertEqual(report["eicg_clock_gate_cells"], ["eicg_gate"])
        self.assertEqual(report["eicg_control_latch_cells"], ["eicg_latch"])
        self.assertEqual(report["root_endpoint_counts"]["clock_uncore"], 2)

    def test_eicg_pattern_drift_fails_closed(self):
        mutations = (
            lambda d: d["modules"]["ChipTop"]["cells"]["eicg_latch"]["connections"].__setitem__("EN", [2]),
            lambda d: d["modules"]["ChipTop"]["cells"]["eicg_latch"]["parameters"].__setitem__(
                "EN_POLARITY", "00000000000000000000000000000001"
            ),
            lambda d: d["modules"]["ChipTop"]["cells"]["eicg_gate"]["attributes"].__setitem__(
                "src", "generated-src/NotEICG.v:18.16-18.32"
            ),
        )
        for mutate in mutations:
            document = self.eicg_document()
            mutate(document)
            with self.subTest(mutation=mutate), self.assertRaisesRegex(
                ValueError, "generated by sequential cell"
            ):
                analyze_clock_inventory(document)

    def test_malformed_sequential_clock_pin_fails_closed(self):
        document = flat_document()
        cell = document["modules"]["ChipTop"]["cells"]["main_ff"]
        cell["connections"].pop("CLK")
        with self.assertRaisesRegex(ValueError, "lacks CLK"):
            analyze_clock_inventory(document)
        document = flat_document()
        document["modules"]["ChipTop"]["cells"]["main_ff"]["port_directions"]["CLK"] = "output"
        with self.assertRaisesRegex(ValueError, "not an input"):
            analyze_clock_inventory(document)

    def test_unapproved_or_ambiguous_clock_fails(self):
        document = flat_document()
        document["modules"]["ChipTop"]["cells"]["main_ff"]["connections"]["CLK"] = [4]
        with self.assertRaisesRegex(ValueError, "unique external root"):
            analyze_clock_inventory(document)
        document = flat_document()
        document["modules"]["ChipTop"]["cells"]["gate"] = {
            "type": "$or",
            "port_directions": {"A": "input", "B": "input", "Y": "output"},
            "connections": {"A": [1], "B": [2], "Y": [20]},
        }
        document["modules"]["ChipTop"]["cells"]["main_ff"]["connections"]["CLK"] = [20]
        with self.assertRaisesRegex(ValueError, "unique external root"):
            analyze_clock_inventory(document)

    def test_unresolved_nonprimitive_clock_driver_fails(self):
        document = flat_document()
        document["modules"]["ChipTop"]["cells"]["mystery"] = {
            "type": "ClockMystery",
            "port_directions": {"in": "input", "out": "output"},
            "connections": {"in": [1], "out": [20]},
        }
        document["modules"]["ChipTop"]["cells"]["main_ff"]["connections"]["CLK"] = [20]
        with self.assertRaisesRegex(ValueError, "non-primitive"):
            analyze_clock_inventory(document)

    def test_export_is_self_contained_and_hash_bound(self):
        with tempfile.TemporaryDirectory() as temporary:
            export = Path(temporary)
            write_export(export, "integrated-static-graph-rocket")
            self.assertEqual(
                validate_export(export, "integrated-static-graph-rocket")["top"],
                "ChipTop",
            )
            (export / "generated-src/ChipTop.sv").write_text("changed\n")
            with self.assertRaisesRegex(ValueError, "RTL tree hash"):
                validate_export(export, "integrated-static-graph-rocket")

    def test_export_rejects_nonlocal_or_duplicate_filelist(self):
        with tempfile.TemporaryDirectory() as temporary:
            export = Path(temporary)
            write_export(export, "integrated-static-graph-rocket")
            (export / "ChipTop.top.f").write_text("/absolute/ChipTop.sv\n")
            with self.assertRaisesRegex(ValueError, "file lists differ"):
                validate_export(export, "integrated-static-graph-rocket")
            unsafe = "generated-src/../generated-src/ChipTop.sv\n"
            (export / "ChipTop.top.f").write_text(unsafe)
            (export / "rtl-files.txt").write_text(unsafe)
            metadata = json.loads((export / "export-metadata.json").read_text())
            metadata["rtl_filelist_sha256"] = hashlib.sha256(unsafe.encode()).hexdigest()
            (export / "export-metadata.json").write_text(json.dumps(metadata))
            with self.assertRaisesRegex(ValueError, "unsafe"):
                validate_export(export, "integrated-static-graph-rocket")
            (export / "ChipTop.top.f").write_text(
                "generated-src/ChipTop.sv\ngenerated-src/ChipTop.sv\n"
            )
            with self.assertRaisesRegex(ValueError, "duplicate"):
                validate_export(export, "integrated-static-graph-rocket")

    def test_analysis_and_comparison_bind_rocket_and_ports(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            a_export, b_export = root / "a", root / "b"
            write_export(a_export, "integrated-static-graph-rocket")
            write_export(b_export, "matched-rocket-system")
            a_hier, b_hier, flat = root / "a.json", root / "b.json", root / "flat.json"
            a_hier.write_text(json.dumps(hierarchy_document(graph=True)))
            b_hier.write_text(json.dumps(hierarchy_document(graph=False)))
            flat.write_text(json.dumps(flat_document()))
            a = analyze_export(a_export, a_hier, flat, "integrated-static-graph-rocket")
            b = analyze_export(b_export, b_hier, flat, "matched-rocket-system")
            self.assertTrue(compare_reports(a, b)["rocket_module_identity_equal"])
            b["hierarchy"]["port_signature"]["custom_boot"] = ("input", 2, 0, False, False)
            with self.assertRaisesRegex(ValueError, "port signatures"):
                compare_reports(a, b)

    def test_rocket_revision_and_byte_mismatch_fail(self):
        a = {
            "variant": "integrated-static-graph-rocket",
            "hierarchy": {
                "port_signature": {},
                "rocket_module_canonical_sha256": HEX,
                "rocket_module_raw_sha256": HEX,
                "config": "a",
            },
            "clock_inventory": {"allowed_roots": sorted(CLOCK_ROOTS)},
            "export": {"rocket_rtl_sha256": HEX, "rocket_revision": "x", "image_rootfs_sha256": HEX},
        }
        b = copy.deepcopy(a)
        b["variant"] = "matched-rocket-system"
        b["hierarchy"]["config"] = "b"
        b["export"]["rocket_revision"] = "y"
        with self.assertRaisesRegex(ValueError, "revisions"):
            compare_reports(a, b)
        b["export"]["rocket_revision"] = "x"
        b["export"]["rocket_rtl_sha256"] = "b" * 64
        with self.assertRaisesRegex(ValueError, "Rocket.sv"):
            compare_reports(a, b)

    def test_scripts_copy_closure_and_never_run_candidate_flow(self):
        export = (ROOT / "hardware/chisel/run-exp0011-rtl-export.sh").read_text()
        preflight = (ROOT / "hardware/chisel/run-exp0011-rtl-preflight.sh").read_text()
        for token in (
            "ENABLE_YOSYS_FLOW=1",
            "generated-src/$base",
            "ChipTop.top.f",
            "shared-elaboration-identical",
            "memory-macro-contract.txt",
            "RaveilRuntimeIntegratedGraphRocketConfig",
            "RaveilFixtureRepeatedMatchedRocketConfig",
            "--network none",
            "expected_image_id=sha256:9009a923ce829097efacd97fe62cbef79dfdcafc70dc435d4bf5e1a66fdaf822",
            "expected_rootfs_sha256=154dc63d7967ea4dce962f002ee10be12f598b5358f6b0ffc524a80d72bb8b9c",
            "umask 077",
            "unsafe physical RTL basename",
        ):
            self.assertIn(token, export)
        self.assertNotIn("docker build", export)
        for token in (
            'printf "read_verilog -sv %s\\n"',
            "hierarchy -generate memory_ext",
            "hierarchy -check -top ChipTop",
            "write_rtlil /out/%s-hierarchy.rtlil",
            "flatten\\nproc\\nopt_clean\\ncheck\\nwrite_json",
            "yosys -q -l",
            "--network none",
            "expected_image_id=sha256:7a0db885c100695626175931d3e053ba6a1602d949167b83e2ef60888eea7169",
            "expected_rootfs_sha256=21620b37d8c2f62d831d186304b2b32912e6f0d5d34ca14a8e659edbbdfbeac5",
            "validate-export",
            "unsafe RTL entry during preflight",
            'mkdir "$output_dir/raw" "$output_dir/derived"',
            'raw_manifest_sha256=$(shasum -a 256 "$raw_dir/sha256s.txt"',
            "umask 077",
        ):
            self.assertIn(token, preflight)
        self.assertNotIn("docker build", preflight)
        self.assertNotIn("bash -lc", preflight)
        for forbidden in ("synth -top", "abc -liberty", "stat -liberty", "sta "):
            self.assertNotIn(forbidden, preflight)
        self.assertNotIn('awk "{print \\\\$1}"', export)


if __name__ == "__main__":
    unittest.main()
