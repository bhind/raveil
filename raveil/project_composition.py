"""Bounded host composition; existing child RTL validation remains authoritative."""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import struct
import subprocess
from uuid import uuid4

from . import project as p
from . import project_graph
from .graph_device_dag import graph_oracle
from .workspace import NativeWorkspace

PLAN = "raveil.project-composition-plan/v1"
RESULT = "raveil.project-composition-result/v1"
LABEL = re.compile(r"[a-z][a-z0-9_-]{0,30}\Z", re.ASCII)
CHILD_RECIPE = {"schema": p.GRAPH_SNAPSHOT_RECIPE_SCHEMA, "kind": "graph-device",
                "descriptor": "descriptor.json", "input": "input.json"}


def _labels(outputs):
    if type(outputs) is not list or not 1 <= len(outputs) <= 2:
        raise ValueError("composition requires one or two named outputs")
    names = []
    for pair in outputs:
        if not isinstance(pair, (tuple, list)) or len(pair) != 2:
            raise ValueError("output must be NAME=RECIPE")
        label, recipe = pair
        if type(label) is not str or not LABEL.fullmatch(label):
            raise ValueError("unsafe output name")
        if type(recipe) is not str:
            raise ValueError("recipe name must be text")
        p.name(recipe)
        names.append(label)
    if len(set(names)) != len(names):
        raise ValueError("duplicate output name")


def _read(root, path):
    return NativeWorkspace(root).read_text(path, maximum=p.MAX_BYTES).encode()


def _json(payload):
    value = json.loads(payload, object_pairs_hook=p._object)
    if type(value) is not dict:
        raise ValueError("expected composition object")
    return value


def _manifest(root):
    return {k: v for k, v in p.tree(root).items()
            if k not in {"/record.json", "/record.sha256", "/.record.pending"}}


def _plan(root):
    plan = _json(_read(root, "plan.json"))
    if set(plan) != {"schema", "composition_id", "input_file", "input_json_sha256", "input_sha256", "outputs"} or plan["schema"] != PLAN:
        raise ValueError("invalid composition plan")
    if plan["composition_id"] != root.name:
        raise ValueError("composition identity differs")
    entries = plan["outputs"]
    if type(entries) is not list or any(type(e) is not dict or set(e) != {"name", "recipe_name", "source_recipe", "descriptor_sha256"} for e in entries):
        raise ValueError("invalid composition outputs")
    _labels([(e["name"], e["recipe_name"]) for e in entries])
    raw = _read(root, "input.json")
    packed = project_graph.input_bytes(raw)
    if p.digest(raw) != plan["input_json_sha256"] or p.digest(packed) != plan["input_sha256"]:
        raise ValueError("frozen input differs")
    descriptors = []
    for slot, entry in enumerate(entries):
        payload = _read(root, f"descriptor-{slot}.json")
        if p.digest(payload) != entry["descriptor_sha256"]:
            raise ValueError("frozen descriptor differs")
        project_graph.compile_graph(_json(payload))
        descriptors.append(payload)
    return plan, raw, packed, descriptors


def _child(root, slot, run_id, plan, raw, packed, descriptor):
    child = p.Project(root / "children" / str(slot))
    record = child.load_run(run_id)
    if record["status"] != "succeeded" or record["backend"] != "rtl-sim" or record["recipe"] != CHILD_RECIPE:
        raise ValueError("child did not complete the expected Graph")
    if type(record.get("result")) is not dict or type(record["result"].get("receipt")) is not dict:
        raise ValueError("child result and receipt must be objects")
    prefix = f"runs/{p.name(run_id)}"
    if _read(child.root, prefix + "/inputs/input.json") != raw or _read(child.root, prefix + "/inputs/descriptor.json") != descriptor:
        raise ValueError("child snapshot differs from parent")
    program = project_graph.compile_graph(_json(descriptor))
    receipt = _json(_read(child.root, prefix + "/receipt.json"))
    output = (child.root / prefix / "workspace/output.bin").read_bytes()
    # load_run above checks symlinks/inventory; captured bytes are checked again.
    expected = struct.pack("<256I", *graph_oracle(_json(descriptor), struct.unpack("<324I", packed)))
    identities = {"descriptor_sha256": p.digest(descriptor), "program_sha256": program["program_sha256"],
                  "input_mode": "snapshot", "input_sha256": plan["input_sha256"],
                  "output_sha256": p.digest(output)}
    for key in ("simulator_sha256", "rtl_manifest_sha256", "source_manifest_sha256"):
        value = receipt.get(key)
        if type(value) is not str or not re.fullmatch(r"[0-9a-f]{64}", value):
            raise ValueError("child build identity is invalid")
        identities[key] = value
    if any(receipt.get(k) != v for k, v in identities.items()) or receipt != record["result"]["receipt"]:
        raise ValueError("child receipt differs from composition")
    if output != expected or record["outputs"].get("/output.bin") != p.digest(output):
        raise ValueError("child output differs from independent oracle")
    text = project_graph.output_text(output, program)
    if _read(child.root, prefix + "/workspace/output.txt") != text:
        raise ValueError("child displayed output differs")
    if child.load_run(run_id) != record:
        raise ValueError("child changed during capture")
    return {"name": plan["outputs"][slot]["name"], "slot": slot, "run_id": run_id,
            "record_sha256": p.digest(_read(child.root, prefix + "/record.json")),
            **identities}, text.decode()


def compose(project, input_file, outputs, *, cancelled=lambda: False):
    """Capture first, execute ordered private children, publish one parent last."""
    _labels(outputs)
    if type(input_file) is not str or not input_file.endswith(".json") or "/" in input_file or "\\" in input_file:
        raise ValueError("composition input must be a JSON filename inside inputs/")
    p.name(input_file[:-5])
    raw = _read(project.root / "inputs", input_file)
    packed = project_graph.input_bytes(raw)
    descriptors, entries = [], []
    for label, recipe_name in outputs:
        recipe = project.recipe(recipe_name)
        if recipe["kind"] != "graph-device":
            raise ValueError("composition children must be Graph recipes")
        descriptor = _read(project.root / "inputs", recipe["descriptor"])
        project_graph.compile_graph(_json(descriptor))
        descriptors.append(descriptor)
        entries.append({"name": label, "recipe_name": recipe_name, "source_recipe": recipe,
                        "descriptor_sha256": p.digest(descriptor)})
    if len(raw) + sum(map(len, descriptors)) > p.MAX_BYTES // 4:
        raise ValueError("composition snapshot exceeds byte budget")
    identity = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ-") + uuid4().hex[:12]
    if "compositions" not in project.workspace.ls("/"):
        project.workspace.mkdir("compositions", mode=0o700)
    project.workspace.mkdir(f"compositions/{identity}", mode=0o700)
    root = project.root / "compositions" / identity
    plan = {"schema": PLAN, "composition_id": identity, "input_file": input_file,
            "input_json_sha256": p.digest(raw), "input_sha256": p.digest(packed), "outputs": entries}
    p.write_new(root / "plan.json", p.encoded(plan)); p.write_new(root / "input.json", raw)
    for slot, descriptor in enumerate(descriptors):
        p.write_new(root / f"descriptor-{slot}.json", descriptor)
    (root / "children").mkdir(mode=0o700)
    result = {"schema": RESULT, "composition_id": identity, "plan_sha256": p.digest(p.encoded(plan)),
              "status": "incomplete", "error": "", "children": [], "evidence_class": "rtl-simulation-functional"}
    def checkpoint():
        if cancelled():
            raise KeyboardInterrupt("composition cancelled")
    try:
        for slot, descriptor in enumerate(descriptors):
            checkpoint()
            _plan(root)
            child_root = root / "children" / str(slot)
            child_root.mkdir(mode=0o700)
            for directory in ("inputs", "recipes", "runs"):
                (child_root / directory).mkdir(mode=0o700)
            p.write_new(child_root / "project.json", p.encoded(p.CONFIG))
            p.write_new(child_root / "recipes/child.json", p.encoded(CHILD_RECIPE))
            p.write_new(child_root / "inputs/input.json", raw)
            p.write_new(child_root / "inputs/descriptor.json", descriptor)
            child = p.Project(child_root)
            record = child.run("child", "rtl-sim", kernel=Path("unused"), qemu="unused", compiler="unused")
            if record["status"] != "succeeded":
                raise ValueError(f"child {slot} failed: {record['error']}")
            evidence, _ = _child(root, slot, record["run_id"], plan, raw, packed, descriptor)
            result["children"].append(evidence)
        checkpoint()
        if _plan(root)[0] != plan:
            raise ValueError("plan changed during execution")
        for slot, entry in enumerate(result["children"]):
            if _child(root, slot, entry["run_id"], plan, raw, packed, descriptors[slot])[0] != entry:
                raise ValueError("child changed before publication")
        if any(any(entry[key] != result["children"][0][key] for key in
                   ("simulator_sha256", "rtl_manifest_sha256", "source_manifest_sha256"))
               for entry in result["children"]):
            raise ValueError("children did not use the same RTL build")
        checkpoint()
        result["status"] = "succeeded"
    except KeyboardInterrupt:
        result["error"] = "cancelled; parent incomplete"
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        result["error"] = str(error)
    result["artifacts"] = _manifest(root)
    # No-overwrite atomic final record is the publication point.
    def seal():
        payload = p.encoded(result)
        p.write_new(root / ".record.pending", payload)
        p.write_new(root / "record.sha256", (p.digest(payload) + "\n").encode())
        if result["status"] == "succeeded":
            checkpoint()
        os.link(root / ".record.pending", root / "record.json")
        (root / ".record.pending").unlink()
    try:
        seal()
    except KeyboardInterrupt:
        if not (root / "record.json").exists():
            # No success is published. Retain interrupted seal for diagnosis.
            result["status"] = "incomplete"
            result["error"] = "cancelled before publication; unsealed parent"
    return result


def load(project, identity):
    p.name(identity)
    project.workspace.stat(f"compositions/{identity}")
    root = project.root / "compositions" / identity
    plan, raw, packed, descriptors = _plan(root)
    payload = _read(root, "record.json")
    if p.digest(payload) != _read(root, "record.sha256").decode().strip():
        raise ValueError("parent record checksum differs")
    record = _json(payload)
    if set(record) != {"schema", "composition_id", "plan_sha256", "status", "error", "children", "evidence_class", "artifacts"} or record["schema"] != RESULT or record["composition_id"] != identity:
        raise ValueError("invalid composition result")
    if record["plan_sha256"] != p.digest(_read(root, "plan.json")) or record["artifacts"] != _manifest(root):
        raise ValueError("saved composition artifacts differ")
    if record["status"] not in ("succeeded", "incomplete") or type(record["children"]) is not list or len(record["children"]) > len(plan["outputs"]):
        raise ValueError("invalid parent status or children")
    if any(type(e) is not dict or type(e.get("run_id")) is not str for e in record["children"]):
        raise ValueError("invalid child reference")
    if record["status"] == "succeeded" and (len(record["children"]) != len(plan["outputs"]) or record["error"]):
        raise ValueError("partial parent cannot succeed")
    if record["evidence_class"] != "rtl-simulation-functional" or type(record["error"]) is not str:
        raise ValueError("invalid composition evidence or error")
    if record["status"] == "succeeded" and any(any(e.get(k) != record["children"][0].get(k) for k in
            ("simulator_sha256", "rtl_manifest_sha256", "source_manifest_sha256")) for e in record["children"]):
        raise ValueError("children build identities differ")
    texts = []
    for slot, entry in enumerate(record["children"]):
        expected, text = _child(root, slot, entry["run_id"], plan, raw, packed, descriptors[slot])
        if entry != expected:
            raise ValueError("child reference differs")
        texts.append(text)
    if _read(root, "record.json") != payload or _manifest(root) != record["artifacts"]:
        raise ValueError("composition changed during capture")
    return record, texts


def inspect(project, identity):
    record, texts = load(project, identity)
    lines = [f"composition={identity} status={record['status']} evidence={record['evidence_class']}"]
    if record["status"] != "succeeded":
        return "\n".join(lines + ["No complete result set. " + record["error"]]) + "\n"
    for entry, text in zip(record["children"], texts):
        lines += [f"output={entry['name']} child={entry['run_id']}", text.rstrip()]
    return "\n".join(lines) + "\n"


def history(project):
    if "compositions" not in project.workspace.ls("/"):
        return "No composition attempts."
    lines = []
    for identity in project.workspace.ls("compositions"):
        try:
            record, _ = load(project, identity)
            lines.append(f"{identity} {record['status']} children={len(record['children'])}")
        except (OSError, ValueError, KeyError, TypeError) as error:
            lines.append(f"{identity} incomplete/unverified: {error}")
    return "\n".join(lines)
