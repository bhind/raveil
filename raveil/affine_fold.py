"""Bounded affine map/fold contract v1. Independent of the stencil ABI.

Unsigned 32-bit arithmetic, two read-only inputs, affine views of (i,j,k).
This is a reference/compiler for a local RTL candidate, not a performance model.
"""
from __future__ import annotations

from collections.abc import Sequence
import argparse
import json
from pathlib import Path
from .fold_evidence import loads

MAGIC = 0x4D463031
MASK = (1 << 32) - 1
OPS = {"load": 1, "add": 2, "yield": 3, "max": 4, "mul": 5,
       "add_imm": 6, "ge_imm": 7}


def _int(x, low, high):
    if type(x) is not int or not low <= x <= high:
        raise ValueError(f"expected integer in [{low}, {high}], got {x!r}")
    return x


def validate_config(c):
    if not isinstance(c, list) or len(c) != 65:
        raise ValueError("configuration must contain exactly 65 words")
    for word in c:
        _int(word, 0, MASK)
    if c[0] != MAGIC:
        raise ValueError("unsupported affine-fold ABI")
    rows, cols, extent, fold, la, lb, nv, ni = c[1:9]
    for n in (rows, cols):
        _int(n, 1, 16)
    _int(extent, 1, 64)
    _int(fold, 0, 1)
    for n in (la, lb):
        _int(n, 0, 324)
    _int(nv, 1, 8)
    _int(ni, 2, 16)
    for v in range(8):
        b, base, si, sj, sk = c[9 + 5*v:14 + 5*v]
        if v >= nv:
            if any((b, base, si, sj, sk)):
                raise ValueError("nonzero unused view")
            continue
        _int(b, 0, 1)
        for n in (base, si, sj, sk):
            _int(n, 0, 323)
        last = base + si*(rows-1) + sj*(cols-1) + sk*(extent-1)
        if last >= (la, lb)[b]:
            raise ValueError("affine view exceeds input extent")
    defined = set()
    for pc, w in enumerate(c[49:]):
        if pc >= ni:
            if w:
                raise ValueError("nonzero unused instruction")
            continue
        op, d, a, b = w >> 28, (w >> 25) & 7, (w >> 22) & 7, (w >> 19) & 7
        if pc == ni-1:
            if op != 3 or d or w & ((1 << 22)-1) or a not in defined:
                raise ValueError("final instruction must yield a defined value")
        elif op == 1:
            if a >= nv or w & ((1 << 22)-1):
                raise ValueError("invalid load")
            defined.add(d)
        elif op in (2, 4, 5):
            if a not in defined or b not in defined or w & ((1 << 19)-1):
                raise ValueError("invalid binary operation")
            defined.add(d)
        elif op in (6, 7):
            if a not in defined:
                raise ValueError("undefined operand")
            defined.add(d)
        else:
            raise ValueError("unsupported instruction")
    return c


def compile_region(d):
    """Lower topologically ordered SSA nodes; reject rather than spill."""
    if not isinstance(d, dict) or set(d) != {"schema", "shape", "extent", "fold", "lengths", "views", "nodes", "result"}:
        raise ValueError("unexpected or missing region field")
    if d["schema"] != "raveil.affine-fold.v1":
        raise ValueError("unsupported schema")
    if (not isinstance(d["shape"], Sequence) or not isinstance(d["lengths"], Sequence) or
        len(d["shape"]) != 2 or len(d["lengths"]) != 2):
        raise ValueError("two dimensions and two input lengths required")
    if d["fold"] not in ("sum", "max"):
        raise ValueError("fold must be sum or max")
    views = d["views"]
    if not isinstance(views, dict) or not 1 <= len(views) <= 8:
        raise ValueError("one to eight views required")
    nodes = d["nodes"]
    if not isinstance(nodes, list) or not 1 <= len(nodes) <= 15:
        raise ValueError("one to fifteen map nodes required")
    seen = set()
    uses = {}
    for node in nodes:
        if not isinstance(node, dict):
            raise ValueError("invalid node")
        op = node.get("op")
        if type(op) is not str:
            raise ValueError("invalid operation")
        fields = {"id", "op"} | ({"view"} if op == "load" else
                 {"args", "imm"} if op in ("add_imm", "ge_imm") else {"args"})
        if set(node) != fields or op not in OPS or op == "yield":
            raise ValueError("invalid node")
        name = node["id"]
        if not isinstance(name, str) or not name or name in seen:
            raise ValueError("duplicate or invalid SSA identifier")
        args = node.get("args", [])
        if not isinstance(args, list) or len(args) != (0 if op == "load" else 1 if op in ("add_imm", "ge_imm") else 2):
            raise ValueError("incorrect arity")
        for arg in args:
            if type(arg) is not str or arg not in seen:
                raise ValueError("nodes must be in dependency order")
            uses[arg] = uses.get(arg, 0) + 1
        if op == "load" and (type(node["view"]) is not str or node["view"] not in views):
            raise ValueError("unknown view")
        if "imm" in node:
            _int(node["imm"], 0, (1 << 22)-1)
        seen.add(name)
    if type(d["result"]) is not str or d["result"] not in seen:
        raise ValueError("unknown result")
    uses[d["result"]] = uses.get(d["result"], 0) + 1
    live, free, words = {}, list(range(8)), []
    for node in nodes:
        args = node.get("args", [])
        regs = [live[arg] for arg in args]
        for arg in args:
            uses[arg] -= 1
            if uses[arg] == 0:
                free.append(live.pop(arg))
        if not free:
            raise ValueError("map needs more than eight live registers")
        free.sort()
        dst = free.pop(0)
        live[node["id"]] = dst
        op = node["op"]
        w = OPS[op] << 28 | dst << 25
        if op == "load":
            w |= list(views).index(node["view"]) << 22
        else:
            w |= regs[0] << 22
            w |= node["imm"] if "imm" in node else regs[1] << 19
        words.append(w)
        if uses.get(node["id"], 0) == 0:
            free.append(live.pop(node["id"]))
    words.append(3 << 28 | live[d["result"]] << 22)
    c = [MAGIC, *d["shape"], d["extent"], ("sum", "max").index(d["fold"]),
         *d["lengths"], len(views), len(words)]
    for view in views.values():
        if not isinstance(view, list) or len(view) != 5:
            raise ValueError("view is [buffer, offset, i stride, j stride, k stride]")
        c.extend(view)
    c.extend([0] * (40 - 5*len(views)))
    c.extend(words + [0]*(16-len(words)))
    return validate_config(c)


def reference(d, inputs):
    """SSA interpreter: independent of physical registers/instruction encoding."""
    compile_region(d)  # Admission only; never interpret emitted words.
    if not isinstance(inputs, list) or len(inputs) != 2:
        raise ValueError("exactly two input arrays required (unused may be empty)")
    for data, n in zip(inputs, d["lengths"]):
        if not isinstance(data, Sequence) or len(data) != n:
            raise ValueError("input length mismatch")
        for w in data:
            _int(w, 0, MASK)
    result = []
    for i in range(d["shape"][0]):
        for j in range(d["shape"][1]):
            acc = 0
            for k in range(d["extent"]):
                values = {}
                for node in d["nodes"]:
                    op = node["op"]
                    a = [values[x] for x in node.get("args", [])]
                    if op == "load":
                        b, base, si, sj, sk = d["views"][node["view"]]
                        v = inputs[b][base + si*i + sj*j + sk*k]
                    elif op == "add":
                        v = a[0] + a[1]
                    elif op == "mul":
                        v = a[0] * a[1]
                    elif op == "max":
                        v = max(a)
                    elif op == "add_imm":
                        v = a[0] + node["imm"]
                    else:
                        v = int(a[0] >= node["imm"])
                    values[node["id"]] = v & MASK
                v = values[d["result"]]
                acc = (acc + v) & MASK if d["fold"] == "sum" else max(acc, v)
            result.append(acc)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("region", type=Path)
    args = parser.parse_args()
    d = loads(args.region.read_text())
    print(json.dumps({"configuration": compile_region(d)}, indent=2))


if __name__ == "__main__":
    main()
