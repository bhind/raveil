"""Fail-closed structural checks for the EXP-0011 ChipTop RTL exports.

The module deliberately stops before synthesis, timing, area, or any candidate
decision.  Its inputs are Yosys JSON representations of the exported RTL plus
the immutable export metadata and copied source closure.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Iterable

from raveil.t0044_physical import tree_sha256


TOP = "ChipTop"
VARIANTS = {
    "integrated-static-graph-rocket":
        "chipyard.raveil.RaveilRuntimeIntegratedGraphRocketConfig",
    "matched-rocket-system":
        "chipyard.raveil.RaveilFixtureRepeatedMatchedRocketConfig",
}
CLOCK_ROOTS = frozenset({"clock_uncore", "jtag_TCK", "serial_tl_0_clock_in"})
REQUIRED_PORTS = CLOCK_ROOTS | {
    "reset_io",
    "custom_boot",
    "axi4_mem_0_clock",
    "clock_tap",
}
MEMORY_MACRO_CONTRACT = {
    "cc_dir_ext": "name cc_dir_ext depth 1024 width 128 ports mrw mask_gran 16",
    "cc_banks_0_ext": "name cc_banks_0_ext depth 16384 width 64 ports rw",
    "data_arrays_0_ext": "name data_arrays_0_ext depth 512 width 256 ports mrw mask_gran 8",
    "tag_array_ext": "name tag_array_ext depth 64 width 88 ports mrw mask_gran 22",
    "tag_array_0_ext": "name tag_array_0_ext depth 64 width 84 ports mrw mask_gran 21",
    "data_arrays_0_0_ext": "name data_arrays_0_0_ext depth 512 width 128 ports mrw mask_gran 32",
    "memory_ext": "name memory_ext depth 1024 width 32 ports mwrite,read mask_gran 8",
}
MEMORY_MACRO_COUNTS = {
    "cc_banks_0_ext": 4,
    "cc_dir_ext": 1,
    "data_arrays_0_0_ext": 2,
    "data_arrays_0_ext": 1,
    "memory_ext": 1,
    "tag_array_0_ext": 1,
    "tag_array_ext": 1,
}
MEMORY_MACRO_PORTS = {
    "cc_banks_0_ext": {
        "RW0_addr": ("input", 14), "RW0_en": ("input", 1),
        "RW0_clk": ("input", 1), "RW0_wmode": ("input", 1),
        "RW0_wdata": ("input", 64), "RW0_rdata": ("output", 64),
    },
    "cc_dir_ext": {
        "RW0_addr": ("input", 10), "RW0_en": ("input", 1),
        "RW0_clk": ("input", 1), "RW0_wmode": ("input", 1),
        "RW0_wdata": ("input", 128), "RW0_rdata": ("output", 128),
        "RW0_wmask": ("input", 8),
    },
    "data_arrays_0_ext": {
        "RW0_addr": ("input", 9), "RW0_en": ("input", 1),
        "RW0_clk": ("input", 1), "RW0_wmode": ("input", 1),
        "RW0_wdata": ("input", 256), "RW0_rdata": ("output", 256),
        "RW0_wmask": ("input", 32),
    },
    "tag_array_ext": {
        "RW0_addr": ("input", 6), "RW0_en": ("input", 1),
        "RW0_clk": ("input", 1), "RW0_wmode": ("input", 1),
        "RW0_wdata": ("input", 88), "RW0_rdata": ("output", 88),
        "RW0_wmask": ("input", 4),
    },
    "tag_array_0_ext": {
        "RW0_addr": ("input", 6), "RW0_en": ("input", 1),
        "RW0_clk": ("input", 1), "RW0_wmode": ("input", 1),
        "RW0_wdata": ("input", 84), "RW0_rdata": ("output", 84),
        "RW0_wmask": ("input", 4),
    },
    "data_arrays_0_0_ext": {
        "RW0_addr": ("input", 9), "RW0_en": ("input", 1),
        "RW0_clk": ("input", 1), "RW0_wmode": ("input", 1),
        "RW0_wdata": ("input", 128), "RW0_rdata": ("output", 128),
        "RW0_wmask": ("input", 4),
    },
    "memory_ext": {
        "R0_addr": ("input", 10), "R0_en": ("input", 1),
        "R0_clk": ("input", 1), "R0_data": ("output", 32),
        "W0_addr": ("input", 10), "W0_en": ("input", 1),
        "W0_clk": ("input", 1), "W0_data": ("input", 32),
        "W0_mask": ("input", 4),
    },
}
MEMORY_MACRO_CLOCK_PORTS = {
    name: ({"R0_clk", "W0_clk"} if name == "memory_ext" else {"RW0_clk"})
    for name in MEMORY_MACRO_CONTRACT
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    require(isinstance(value, dict), f"expected JSON object: {path}")
    return value


YOSYS_AUTO_ID = re.compile(
    r"(?<=\$)[0-9]+(?=_[A-Za-z0-9]|[ \t\[]|$)"
)


def canonical_rtlil_module_sha256(
    module_lines: list[str], module_attributes: dict[str, str]
) -> str:
    """Hash RTLIL semantics while excluding Yosys process-global numeric IDs.

    Yosys assigns the final ``$<number>`` component of generated identifiers
    from a process-global counter.  Adding an unrelated module can therefore
    renumber an otherwise byte-identical Rocket module and reorder its RTLIL
    declarations.  The canonical form changes only those numeric components,
    keeps attributes, source locations, types, parameters, and connections,
    and sorts complete top-level RTLIL units whose order has no semantics.
    """
    require(
        len(module_lines) >= 2
        and module_lines[0].startswith("module \\")
        and module_lines[-1] == "end",
        "malformed RTLIL module boundary",
    )

    def normalize(line: str) -> str:
        return YOSYS_AUTO_ID.sub("<yosys-auto-id>", line)

    units: list[tuple[str, ...]] = []
    pending_attributes: list[str] = []
    index = 1
    while index < len(module_lines) - 1:
        line = module_lines[index]
        require(line.startswith("  "), f"unexpected RTLIL module line: {line}")
        if line.startswith("  attribute "):
            pending_attributes.append(normalize(line))
            index += 1
            continue
        if line.startswith(("  wire ", "  memory ", "  connect ")):
            units.append(tuple(pending_attributes + [normalize(line)]))
            pending_attributes = []
            index += 1
            continue
        if line.startswith(("  cell ", "  process ")):
            block = pending_attributes + [normalize(line)]
            pending_attributes = []
            index += 1
            while index < len(module_lines) - 1:
                nested = module_lines[index]
                block.append(normalize(nested))
                index += 1
                if nested == "  end":
                    break
            else:
                raise ValueError("unterminated RTLIL cell or process")
            units.append(tuple(block))
            continue
        raise ValueError(f"unsupported RTLIL top-level unit: {line}")
    require(not pending_attributes, "orphan RTLIL module attributes")
    payload = {
        "module": normalize(module_lines[0]),
        "attributes": module_attributes,
        "units": sorted(units),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def load_rtlil_hierarchy(path: Path) -> dict[str, Any]:
    """Load only module, port, cell, and module-attribute structure from RTLIL."""
    parsed: dict[str, Any] = {"modules": {}}
    pending_attributes: dict[str, str] = {}
    current: dict[str, Any] | None = None
    current_name = ""
    module_lines: list[str] = []
    with path.open() as source:
        for raw in source:
            line = raw.rstrip("\n")
            if current is None:
                attribute = re.fullmatch(r"attribute \\([^ ]+) (.+)", line)
                if attribute:
                    pending_attributes[attribute.group(1)] = attribute.group(2)
                    continue
                module = re.fullmatch(r"module \\(.+)", line)
                if module:
                    current_name = module.group(1)
                    current = {
                        "attributes": pending_attributes,
                        "ports": {},
                        "cells": {},
                    }
                    pending_attributes = {}
                    module_lines = [line]
                continue
            module_lines.append(line)
            if line == "end":
                current["rtlil_raw_sha256"] = hashlib.sha256(
                    ("\n".join(module_lines) + "\n").encode()
                ).hexdigest()
                current["rtlil_canonical_sha256"] = canonical_rtlil_module_sha256(
                    module_lines, current["attributes"]
                )
                parsed["modules"][current_name] = current
                current = None
                current_name = ""
                module_lines = []
                continue
            port = re.fullmatch(
                r"  wire(?: width ([0-9]+))? (input|output|inout) [0-9]+ \\(.+)",
                line,
            )
            if port:
                width = int(port.group(1) or "1")
                current["ports"][port.group(3)] = {
                    "direction": port.group(2),
                    "bits": list(range(width)),
                }
                continue
            cell = re.fullmatch(r"  cell (?:\\([^ ]+)|(\$[^ ]+)) (.+)", line)
            if cell:
                cell_type = cell.group(1) or cell.group(2)
                current["cells"][cell.group(3)] = {"type": cell_type}
    require(current is None, f"unterminated RTLIL module: {current_name}")
    require(parsed["modules"], f"RTLIL lacks modules: {path}")
    return parsed


def modules(document: dict[str, Any]) -> dict[str, Any]:
    value = document.get("modules")
    require(isinstance(value, dict), "Yosys JSON lacks modules")
    require(TOP in value, f"Yosys JSON lacks {TOP}")
    return value


def attribute_true(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value != 0
    if isinstance(value, str):
        return value not in {"", "0", "false", "False", "00000000000000000000000000000000"}
    return bool(value)


def port_signature(module: dict[str, Any]) -> dict[str, tuple[Any, ...]]:
    return {
        name: (
            port.get("direction"),
            len(port.get("bits", [])),
            port.get("offset", 0),
            bool(port.get("upto", 0)),
            bool(port.get("signed", False)),
        )
        for name, port in sorted(module.get("ports", {}).items())
    }


def walk_hierarchy(
    all_modules: dict[str, Any],
    module_name: str = TOP,
    prefix: str = "",
    stack: tuple[str, ...] = (),
) -> Iterable[tuple[str, str, dict[str, Any]]]:
    require(module_name not in stack, f"recursive module hierarchy at {module_name}")
    module = all_modules[module_name]
    for instance_name, cell in sorted(module.get("cells", {}).items()):
        cell_type = cell.get("type", "")
        path = f"{prefix}/{instance_name}" if prefix else instance_name
        yield path, cell_type, cell
        if cell_type in all_modules:
            yield from walk_hierarchy(
                all_modules, cell_type, path, stack + (module_name,)
            )


def reachable_module_names(
    all_modules: dict[str, Any], instances: Iterable[tuple[str, str, dict[str, Any]]]
) -> set[str]:
    return {TOP} | {cell_type for _, cell_type, _ in instances if cell_type in all_modules}


def module_json_sha256(module: dict[str, Any]) -> str:
    encoded = json.dumps(module, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def analyze_hierarchy(document: dict[str, Any], variant: str) -> dict[str, Any]:
    require(variant in VARIANTS, f"unknown variant: {variant}")
    all_modules = modules(document)
    instances = list(walk_hierarchy(all_modules))
    reachable = reachable_module_names(all_modules, instances)
    reachable_blackboxes: set[str] = set()
    for module_name in sorted(reachable):
        attrs = all_modules[module_name].get("attributes", {})
        if attribute_true(attrs.get("blackbox", False)):
            require(
                module_name in MEMORY_MACRO_CONTRACT,
                f"unapproved reachable blackbox module: {module_name}",
            )
            reachable_blackboxes.add(module_name)

    typed_paths: dict[str, list[str]] = {}
    for path, cell_type, _ in instances:
        typed_paths.setdefault(cell_type, []).append(path)
    require(
        reachable_blackboxes == set(MEMORY_MACRO_CONTRACT),
        "reachable memory-macro blackbox set is incomplete or drifted",
    )
    memory_macro_paths = {
        name: typed_paths.get(name, []) for name in sorted(MEMORY_MACRO_CONTRACT)
    }
    for name, expected_count in MEMORY_MACRO_COUNTS.items():
        require(
            len(memory_macro_paths[name]) == expected_count,
            f"memory-macro instance count drift for {name}",
        )
        actual_ports = {
            port: (value[0], value[1])
            for port, value in port_signature(all_modules[name]).items()
        }
        require(
            actual_ports == MEMORY_MACRO_PORTS[name],
            f"memory-macro port contract drift for {name}",
        )

    rockets = typed_paths.get("Rocket", [])
    require(len(rockets) == 1, "hierarchy must contain exactly one Rocket instance")
    managers = typed_paths.get("RaveilOwnedTLMemory", [])
    fixtures = typed_paths.get("RaveilFixtureInputProvider", [])
    require(len(managers) == 1, "hierarchy must contain exactly one owned memory manager")
    require(len(fixtures) == 1, "hierarchy must contain exactly one fixture provider")
    require(
        any(name == "DCache" or name.endswith("DCache") for name in reachable),
        "hierarchy lacks a Rocket data cache",
    )
    require(
        any(name.startswith("TLXbar") or name.startswith("TLInterconnectCoupler")
            for name in reachable),
        "hierarchy lacks a TileLink interconnect",
    )

    graph_types = {
        "RaveilIntegratedGraphDigitalTop",
        "RaveilStaticStencilCore",
        "RaveilStaticStencilTLClient",
    }
    graph_paths = {
        name: typed_paths.get(name, [])
        for name in sorted(graph_types)
    }
    if variant == "integrated-static-graph-rocket":
        for name, paths in graph_paths.items():
            require(len(paths) == 1, f"integrated hierarchy requires one {name} instance")
    else:
        require(
            not any(graph_paths.values()),
            "matched Rocket baseline contains integrated Graph logic",
        )

    signature = port_signature(all_modules[TOP])
    missing_ports = sorted(REQUIRED_PORTS - signature.keys())
    require(not missing_ports, f"ChipTop lacks required ports: {missing_ports}")
    require(signature["axi4_mem_0_clock"][0] == "output", "AXI clock must be output")
    require(signature["clock_tap"][0] == "output", "clock tap must be output")
    for name in CLOCK_ROOTS | {"reset_io", "custom_boot"}:
        require(signature[name][0] == "input", f"{name} must be input")

    return {
        "top": TOP,
        "variant": variant,
        "config": VARIANTS[variant],
        "rocket_instance_path": rockets[0],
        "rocket_module_canonical_sha256": all_modules["Rocket"].get(
            "rtlil_canonical_sha256", module_json_sha256(all_modules["Rocket"])
        ),
        "rocket_module_raw_sha256": all_modules["Rocket"].get(
            "rtlil_raw_sha256", module_json_sha256(all_modules["Rocket"])
        ),
        "rocket_module_canonicalization":
            "rtlil-top-level-unit-sort-and-yosys-auto-id-elision-v1",
        "owned_memory_path": managers[0],
        "fixture_provider_path": fixtures[0],
        "graph_paths": graph_paths,
        "reachable_module_count": len(reachable),
        "port_signature": signature,
        "blackboxes": len(reachable_blackboxes),
        "blackbox_policy": "matched-memory-macros-only",
        "memory_macro_paths": memory_macro_paths,
        "memory_macro_port_signatures": {
            name: port_signature(all_modules[name])
            for name in sorted(MEMORY_MACRO_CONTRACT)
        },
    }


def is_constant(bit: Any) -> bool:
    return isinstance(bit, str) and bit.lower() in {"0", "1", "x", "z"}


def sequential_clock_ports(cell_type: str, cell: dict[str, Any]) -> set[str]:
    connections = cell.get("connections", {})
    if cell_type in MEMORY_MACRO_CLOCK_PORTS:
        pins = MEMORY_MACRO_CLOCK_PORTS[cell_type]
        require(pins <= connections.keys(), f"memory macro lacks clock pin: {cell_type}")
        return pins
    memory_types = ("$mem_v2", "$memrd", "$memwr")
    if cell_type.startswith(memory_types):
        pins = {name for name in connections if "CLK" in name.upper()}
        require(pins, f"clocked memory cell lacks a clock pin: {cell_type}")
        return pins
    if cell_type.startswith("$_DFF") or cell_type.startswith("$_SDFF"):
        require("C" in connections, f"sequential cell lacks C clock pin: {cell_type}")
        return {"C"}
    if cell_type.startswith(("$dff", "$adff", "$sdff", "$aldff")):
        require("CLK" in connections, f"sequential cell lacks CLK clock pin: {cell_type}")
        return {"CLK"}
    if cell_type.startswith(("$dlatch", "$_DLATCH")):
        pins = {"EN", "E"} & connections.keys()
        require(pins, f"latch cell lacks enable clock pin: {cell_type}")
        return pins
    require(
        not cell_type.startswith("$ff"),
        f"clockless sequential cell is unsupported: {cell_type}",
    )
    return set()


def is_sequential(cell_type: str, cell: dict[str, Any]) -> bool:
    return bool(sequential_clock_ports(cell_type, cell))


def analyze_clock_inventory(document: dict[str, Any]) -> dict[str, Any]:
    top = modules(document)[TOP]
    ports = top.get("ports", {})
    bit_sources: dict[str, list[tuple[str, ...]]] = {}
    for port_name, port in ports.items():
        if port.get("direction") == "input":
            for bit in port.get("bits", []):
                if not is_constant(bit):
                    bit_sources.setdefault(str(bit), []).append(("port", port_name))
    cells = top.get("cells", {})
    for cell_name, cell in cells.items():
        directions = cell.get("port_directions", {})
        for pin, bits in cell.get("connections", {}).items():
            if directions.get(pin) == "output":
                for bit in bits:
                    if not is_constant(bit):
                        bit_sources.setdefault(str(bit), []).append(
                            ("cell", cell_name, pin)
                        )

    memo: dict[str, frozenset[str]] = {}
    derived_clock_bits: set[str] = set()
    derived_clock_driver_cells: set[str] = set()
    eicg_clock_gate_cells: set[str] = set()
    eicg_control_latch_cells: set[str] = set()

    def parameter_int(cell: dict[str, Any], name: str) -> int | None:
        value = cell.get("parameters", {}).get(name)
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value and set(value) <= {"0", "1"}:
            return int(value, 2)
        return None

    def eicg_raw_clock_bit(cell_name: str, cell: dict[str, Any]) -> Any | None:
        """Recognize only the exact low-phase-latch EICG emitted by Chipyard."""
        if cell.get("type") not in {"$and", "$logic_and"}:
            return None
        gate_source = str(cell.get("attributes", {}).get("src", ""))
        if "|generated-src/EICG_wrapper.v:18." not in gate_source:
            return None
        if cell.get("port_directions") != {"A": "input", "B": "input", "Y": "output"}:
            return None
        connections = cell.get("connections", {})
        if set(connections) != {"A", "B", "Y"}:
            return None
        if any(len(connections[pin]) != 1 for pin in ("A", "B", "Y")):
            return None
        wrapper_source = gate_source.split("|generated-src/EICG_wrapper.v:", 1)[0]
        for latched_pin, raw_pin in (("A", "B"), ("B", "A")):
            latched_bit = connections[latched_pin][0]
            raw_bit = connections[raw_pin][0]
            sources = bit_sources.get(str(latched_bit), [])
            if len(sources) != 1 or sources[0][0] != "cell" or sources[0][2] != "Q":
                continue
            latch_name = sources[0][1]
            latch = cells[latch_name]
            if latch.get("type") != "$dlatch":
                continue
            latch_source = str(latch.get("attributes", {}).get("src", ""))
            if not latch_source.startswith(wrapper_source + "|generated-src/EICG_wrapper.v:12."):
                continue
            if latch.get("port_directions") != {"D": "input", "EN": "input", "Q": "output"}:
                continue
            latch_connections = latch.get("connections", {})
            if set(latch_connections) != {"D", "EN", "Q"}:
                continue
            if any(len(latch_connections[pin]) != 1 for pin in ("D", "EN", "Q")):
                continue
            if latch_connections["Q"][0] != latched_bit:
                continue
            if latch_connections["EN"][0] != raw_bit:
                continue
            if parameter_int(latch, "WIDTH") != 1:
                continue
            if parameter_int(latch, "EN_POLARITY") != 0:
                continue
            eicg_clock_gate_cells.add(cell_name)
            eicg_control_latch_cells.add(latch_name)
            return raw_bit
        return None

    def roots_for(bit: Any, visiting: frozenset[str] = frozenset()) -> frozenset[str]:
        if is_constant(bit):
            return frozenset()
        key = str(bit)
        if key in memo:
            return memo[key]
        require(key not in visiting, f"combinational clock-driver cycle at bit {key}")
        sources = bit_sources.get(key, [])
        require(sources, f"clock ancestry has no driver for bit {key}")
        require(len(sources) == 1, f"clock ancestry has multiple drivers for bit {key}")
        source = sources[0]
        if source[0] == "port":
            result = (
                frozenset({source[1]})
                if source[1] in CLOCK_ROOTS
                else frozenset()
            )
        else:
            cell_name = source[1]
            cell = cells[cell_name]
            cell_type = cell.get("type", "")
            derived_clock_bits.add(key)
            derived_clock_driver_cells.add(cell_name)
            eicg_clock = eicg_raw_clock_bit(cell_name, cell)
            if eicg_clock is not None:
                result = roots_for(eicg_clock, visiting | {key})
                memo[key] = result
                return result
            require(
                not is_sequential(cell_type, cell),
                f"clock for an endpoint is generated by sequential cell {cell_name}",
            )
            require(
                cell_type.startswith("$"),
                f"unresolved non-primitive clock driver {cell_name}:{cell_type}",
            )
            input_bits = [
                candidate
                for pin, bits in cell.get("connections", {}).items()
                if cell.get("port_directions", {}).get(pin) == "input"
                for candidate in bits
            ]
            require(input_bits, f"derived clock driver has no inputs: {cell_name}")
            roots: set[str] = set()
            for candidate in input_bits:
                roots.update(roots_for(candidate, visiting | {key}))
            result = frozenset(roots)
        memo[key] = result
        return result

    root_counts = {name: 0 for name in CLOCK_ROOTS}
    endpoints: list[dict[str, str]] = []
    for cell_name, cell in sorted(cells.items()):
        cell_type = cell.get("type", "")
        for pin in sorted(sequential_clock_ports(cell_type, cell)):
            require(
                cell.get("port_directions", {}).get(pin) == "input",
                f"sequential clock pin is not an input: {cell_name}.{pin}",
            )
            clock_bits = cell["connections"][pin]
            require(clock_bits, f"sequential clock pin is empty: {cell_name}.{pin}")
            for index, bit in enumerate(clock_bits):
                if is_constant(bit):
                    continue
                roots = roots_for(bit)
                require(
                    len(roots) == 1,
                    f"sequential clock lacks one unique external root: {cell_name}.{pin}[{index}]={sorted(roots)}",
                )
                root = next(iter(roots))
                require(root in CLOCK_ROOTS, f"unapproved clock root: {root}")
                root_counts[root] += 1
                endpoints.append({
                    "cell": cell_name,
                    "type": cell_type,
                    "pin": pin,
                    "root": root,
                })
    require(endpoints, "flattened RTL has no sequential or memory clock endpoints")
    missing_roots = sorted(name for name, count in root_counts.items() if count == 0)
    require(not missing_roots, f"declared clocks lack sequential endpoints: {missing_roots}")
    return {
        "allowed_roots": sorted(CLOCK_ROOTS),
        "root_endpoint_counts": dict(sorted(root_counts.items())),
        "sequential_endpoint_count": len(endpoints),
        "unconstrained_clock_endpoints": 0,
        "derived_clock_bits": sorted(derived_clock_bits),
        "derived_clock_driver_cells": sorted(derived_clock_driver_cells),
        "eicg_clock_gate_cells": sorted(eicg_clock_gate_cells),
        "eicg_control_latch_cells": sorted(eicg_control_latch_cells),
        "endpoints": endpoints,
    }


def validate_export(export_dir: Path, variant: str) -> dict[str, Any]:
    metadata = load_json(export_dir / "export-metadata.json")
    require(metadata.get("schema") == "raveil.exp-0011-rtl-export/v1", "bad export schema")
    require(metadata.get("variant") == variant, "export variant mismatch")
    require(metadata.get("config") == VARIANTS[variant], "export config mismatch")
    require(metadata.get("top") == TOP, "export top mismatch")
    require(metadata.get("performance") == "not-measured", "export contains a performance claim")
    for field in (
        "source_sha256", "input_sha256", "runner_sha256", "lock_sha256",
        "image_rootfs_sha256", "rtl_sha256", "rtl_filelist_sha256",
        "firrtl_sha256", "hierarchy_sha256", "lowering_provenance_sha256",
        "rocket_rtl_sha256", "memory_macro_contract_sha256",
    ):
        value = metadata.get(field, "")
        require(isinstance(value, str) and len(value) == 64, f"invalid export identity: {field}")
    require(
        re.fullmatch(r"sha256:[0-9a-f]{64}", metadata.get("image_id", "")) is not None,
        "invalid export image identity",
    )
    required_files = (
        "ChipTop.top.f", "rtl-files.txt", "pre-firtool.fir",
        "top-module-hierarchy.json", "lowering-provenance.txt",
        "memory-macro-contract.txt",
        "generated-src/ChipTop.sv", "generated-src/Rocket.sv",
    )
    for relative in required_files:
        require((export_dir / relative).is_file(), f"missing export file: {relative}")
    identity_files = {
        "rtl_filelist_sha256": "rtl-files.txt",
        "firrtl_sha256": "pre-firtool.fir",
        "hierarchy_sha256": "top-module-hierarchy.json",
        "lowering_provenance_sha256": "lowering-provenance.txt",
    }
    for field, relative in identity_files.items():
        require(
            sha256_file(export_dir / relative) == metadata[field],
            f"export artifact hash mismatch: {relative}",
        )
    require(
        tree_sha256(export_dir / "generated-src") == metadata["rtl_sha256"],
        "exported RTL tree hash mismatch",
    )
    require(
        sha256_file(export_dir / "generated-src/Rocket.sv") == metadata["rocket_rtl_sha256"],
        "Rocket RTL hash does not match export metadata",
    )
    macro_contract = {
        line.split()[1]: line.strip()
        for line in (export_dir / "memory-macro-contract.txt").read_text().splitlines()
        if line.strip()
    }
    require(macro_contract == MEMORY_MACRO_CONTRACT, "memory macro contract drift")
    require(
        sha256_file(export_dir / "memory-macro-contract.txt") ==
        metadata["memory_macro_contract_sha256"],
        "memory macro contract hash mismatch",
    )
    filelist = (export_dir / "ChipTop.top.f").read_text().splitlines()
    recorded_files = (export_dir / "rtl-files.txt").read_text().splitlines()
    require(filelist, "empty ChipTop RTL file list")
    require(len(filelist) == len(set(filelist)), "duplicate ChipTop RTL file-list entry")
    require(
        sorted(filelist) == sorted(recorded_files),
        "ChipTop and recorded RTL file lists differ",
    )
    safe_entry = re.compile(r"generated-src/[A-Za-z0-9_.-]+\.(?:sv|v)")
    for relative in filelist:
        require(safe_entry.fullmatch(relative) is not None, "unsafe RTL file-list entry")
        require((export_dir / relative).is_file(), f"missing copied RTL: {relative}")
    return metadata


def analyze_export(
    export_dir: Path,
    hierarchy_path: Path,
    flat_path: Path,
    variant: str,
) -> dict[str, Any]:
    metadata = validate_export(export_dir, variant)
    hierarchy_document = (
        load_rtlil_hierarchy(hierarchy_path)
        if hierarchy_path.suffix == ".rtlil"
        else load_json(hierarchy_path)
    )
    hierarchy = analyze_hierarchy(hierarchy_document, variant)
    clocks = analyze_clock_inventory(load_json(flat_path))
    return {
        "schema": "raveil.exp-0011-rtl-structural-report/v1",
        "variant": variant,
        "export": metadata,
        "hierarchy": hierarchy,
        "clock_inventory": clocks,
        "status": "structural-preflight-only",
        "performance": "not-measured",
    }


def compare_reports(integrated: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    require(integrated["variant"] == "integrated-static-graph-rocket", "wrong integrated report")
    require(baseline["variant"] == "matched-rocket-system", "wrong baseline report")
    a_hierarchy = integrated["hierarchy"]
    b_hierarchy = baseline["hierarchy"]
    require(
        a_hierarchy["port_signature"] == b_hierarchy["port_signature"],
        "external ChipTop port signatures differ",
    )
    require(
        a_hierarchy["rocket_module_canonical_sha256"] ==
        b_hierarchy["rocket_module_canonical_sha256"],
        "canonical Yosys-parsed Rocket module differs",
    )
    require(
        integrated["export"]["rocket_rtl_sha256"] == baseline["export"]["rocket_rtl_sha256"],
        "copied Rocket.sv differs",
    )
    require(
        integrated["export"]["rocket_revision"] == baseline["export"]["rocket_revision"],
        "Rocket source revisions differ",
    )
    require(
        integrated["export"]["image_rootfs_sha256"] == baseline["export"]["image_rootfs_sha256"],
        "generator toolchain root filesystems differ",
    )
    for field in (
        "image_id", "lock_sha256", "runner_sha256", "chipyard_revision",
        "normal_lowering", "physical_lowering",
    ):
        require(
            integrated["export"].get(field) == baseline["export"].get(field),
            f"export provenance differs: {field}",
        )
    require(
        integrated["export"]["memory_macro_contract_sha256"] ==
        baseline["export"]["memory_macro_contract_sha256"],
        "memory macro contracts differ",
    )
    require(
        a_hierarchy["memory_macro_paths"] == b_hierarchy["memory_macro_paths"],
        "memory macro instance paths differ",
    )
    require(
        a_hierarchy["memory_macro_port_signatures"] ==
        b_hierarchy["memory_macro_port_signatures"],
        "memory macro port signatures differ",
    )
    require(
        integrated["clock_inventory"]["allowed_roots"] ==
        baseline["clock_inventory"]["allowed_roots"] == sorted(CLOCK_ROOTS),
        "clock-root policies differ",
    )
    return {
        "schema": "raveil.exp-0011-rtl-preflight-comparison/v1",
        "top": TOP,
        "integrated_config": integrated["hierarchy"]["config"],
        "baseline_config": baseline["hierarchy"]["config"],
        "external_port_signature_equal": True,
        "rocket_instance_count": {"integrated": 1, "baseline": 1},
        "rocket_module_identity_equal": True,
        "rocket_module_canonical_sha256":
            a_hierarchy["rocket_module_canonical_sha256"],
        "rocket_module_raw_rtlil_equal":
            a_hierarchy["rocket_module_raw_sha256"] ==
            b_hierarchy["rocket_module_raw_sha256"],
        "rocket_module_raw_sha256": {
            "integrated": a_hierarchy["rocket_module_raw_sha256"],
            "baseline": b_hierarchy["rocket_module_raw_sha256"],
        },
        "rocket_rtl_sha256": integrated["export"]["rocket_rtl_sha256"],
        "common_clock_roots": sorted(CLOCK_ROOTS),
        "blackbox_policy": "matched-memory-macros-only",
        "memory_macro_contract_sha256":
            integrated["export"]["memory_macro_contract_sha256"],
        "memory_macro_paths": a_hierarchy["memory_macro_paths"],
        "blackbox_module_types": {
            "integrated": len(MEMORY_MACRO_CONTRACT),
            "baseline": len(MEMORY_MACRO_CONTRACT),
        },
        "blackbox_instances": {
            "integrated": sum(MEMORY_MACRO_COUNTS.values()),
            "baseline": sum(MEMORY_MACRO_COUNTS.values()),
        },
        "status": "eligible-for-pre-data-freeze-review",
        "performance": "not-measured",
        "nonclaim": "no synthesis, timing, area, energy, FPGA, ASIC, or silicon result",
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    analyze = subparsers.add_parser("analyze")
    analyze.add_argument("--export-dir", type=Path, required=True)
    analyze.add_argument("--hierarchy", type=Path, required=True)
    analyze.add_argument("--flat", type=Path, required=True)
    analyze.add_argument("--variant", choices=sorted(VARIANTS), required=True)
    validate = subparsers.add_parser("validate-export")
    validate.add_argument("--export-dir", type=Path, required=True)
    validate.add_argument("--variant", choices=sorted(VARIANTS), required=True)
    compare = subparsers.add_parser("compare")
    compare.add_argument("--integrated-report", type=Path, required=True)
    compare.add_argument("--baseline-report", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.command == "analyze":
        result = analyze_export(args.export_dir, args.hierarchy, args.flat, args.variant)
    elif args.command == "validate-export":
        result = validate_export(args.export_dir, args.variant)
    else:
        result = compare_reports(
            load_json(args.integrated_report), load_json(args.baseline_report)
        )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
