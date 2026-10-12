#!/usr/bin/env python3
"""Generate reproducible contract vectors and independent direct-formula checks."""
from __future__ import annotations
import argparse
import copy
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from raveil.affine_fold import compile_region, reference, validate_config, MASK


def region(shape, extent, lengths, views, nodes, result, fold="sum"):
    return dict(schema="raveil.affine-fold.v1", shape=shape, extent=extent,
                lengths=lengths, views=views, nodes=nodes, result=result, fold=fold)


def load(name, view):
    return dict(id=name, op="load", view=view)


def binary(op):
    return [load("a", "a"), load("b", "b"),
            dict(id="x", op=op, args=["a", "b"])]


def vectors():
    rng = random.Random(210)
    cases = []
    def add(name, d, data, expected):
        actual = reference(d, data)
        assert actual == expected, name
        cases.append(dict(name=name, descriptor=d, config=compile_region(d),
                          inputs=data, expected=expected, mode=0))
    for rows, cols in ((1, 1), (2, 7), (7, 3), (16, 16)):
        a = [rng.getrandbits(32) for _ in range(rows*cols)]
        b = [rng.getrandbits(32) for _ in range(rows*cols)]
        for op in ("add", "mul", "max"):
            d = region([rows, cols], 1, [len(a), len(b)],
                       {"a":[0,0,cols,1,0], "b":[1,0,cols,1,0]}, binary(op), "x")
            expected = [(x+y)&MASK if op=="add" else (x*y)&MASK if op=="mul" else max(x,y)
                        for x,y in zip(a,b)]
            add(f"{op}-{rows}x{cols}", d, [a,b], expected)
        bias = b[:cols]
        d = region([rows,cols],1,[len(a),len(bias)],
                   {"a":[0,0,cols,1,0],"b":[1,0,0,1,0]}, binary("add"),"x")
        add(f"broadcast-{rows}x{cols}",d,[a,bias],
            [(a[i*cols+j]+bias[j])&MASK for i in range(rows) for j in range(cols)])
        d = region([cols,rows],1,[len(a),0],{"a":[0,0,1,cols,0]},[load("a","a")],"a")
        add(f"transpose-{rows}x{cols}",d,[a,[]],
            [a[j*cols+i] for i in range(cols) for j in range(rows)])
    for m,n,k in ((1,1,64),(2,3,4),(5,7,9),(16,16,16)):
        a = [rng.getrandbits(32) for _ in range(m*k)]
        b = [rng.getrandbits(32) for _ in range(k*n)]
        d = region([m,n],k,[len(a),len(b)],
                   {"a":[0,0,k,0,1],"b":[1,0,0,1,n]},binary("mul"),"x")
        expected = [sum(a[i*k+t]*b[t*n+j] for t in range(k))&MASK
                    for i in range(m) for j in range(n)]
        add(f"matmul-{m}x{n}x{k}",d,[a,b],expected)
    for fold in ("sum","max"):
        a = [rng.getrandbits(32) for _ in range(5*64)]
        d=region([5,1],64,[len(a),0],{"a":[0,0,64,0,1]},[load("a","a")],"a",fold)
        expected=[(sum(a[i*64:(i+1)*64])&MASK) if fold=="sum" else max(a[i*64:(i+1)*64])
                  for i in range(5)]
        add(f"row-{fold}",d,[a,[]],expected)
    # Multiple views of the same input, unsigned threshold and modular wrap.
    a=[MASK,0,1,3,7,9,1<<31,5,12]
    d=region([1,7],1,[9,0],{"a":[0,0,0,1,0],"b":[0,2,0,1,0]},
             binary("add")+[dict(id="bump",op="add_imm",args=["x"],imm=3),
                            dict(id="test",op="ge_imm",args=["bump"],imm=7)],"test")
    add("offset-threshold",d,[a,[]],[int(((a[j]+a[j+2]+3)&MASK)>=7) for j in range(7)])
    # All eight views and maximum sixteen instruction words.
    views={f"v{i}":[i%2,i,0,0,0] for i in range(8)}
    nodes=[load(f"l{i}",f"v{i}") for i in range(8)]
    previous="l0"
    for i in range(1,8):
        nodes.append(dict(id=f"s{i}",op="add",args=[previous,f"l{i}"]))
        previous=f"s{i}"
    add("all-views-max-program",region([1,1],1,[8,8],views,nodes,previous),
        [list(range(8)),list(range(10,18))],[sum(i+(10 if i%2 else 0) for i in range(8))])
    # Exact maximum legal affine address.
    add("last-input-word",region([1,1],1,[324,0],{"a":[0,323,0,0,0]},
                                [load("a","a")],"a"),[list(range(324)),[]],[323])
    add("last-B-word-and-stride",region([2,1],1,[0,324],{"a":[1,0,323,0,0]},
                                       [load("a","a")],"a"),[[],list(range(324))],[0,323])
    # Combined maxima: 256 outputs,64 folds,16 instructions. No per-case RTL.
    add("maximum-work",region([16,16],64,[1,0],{"a":[0,0,0,0,0]},
                              [load(f"l{i}","a") for i in range(15)],"l14"),
        [[MASK],[]],[(-64)&MASK]*256)
    # Independent direct formula for duplicate operands and dead map values.
    add("duplicate-dead",region([1,3],1,[3,0],{"a":[0,0,0,1,0]},
        [load("dead","a"),load("x","a"),dict(id="square",op="mul",args=["x","x"]),
         dict(id="twice",op="add",args=["square","square"])],"twice"),
        [[0,MASK,1<<31],[]],[0,2,0])
    baseline=copy.deepcopy(cases[1])
    for mode in [*range(1,10),11,12,13]:
        c=copy.deepcopy(baseline);c.update(name=f"protocol-{mode}",mode=mode);cases.append(c)
    # Hardware admission rejects the same malformed configurations as Python.
    mutations={0:0,1:0,2:17,3:65,4:2,5:325,7:0,8:17,9:2,
               10:MASK,11:MASK,14:2,24:1,49:0,50:0xf0000000,64:1}
    for pos,value in mutations.items():
        c=copy.deepcopy(baseline);c["config"][pos]=value
        try: validate_config(c["config"])
        except ValueError: pass
        else: raise AssertionError((pos,value))
        c.update(name=f"reject-word-{pos}",mode=10)
        cases.append(c)
    more=[(3,0),(7,9),(8,1),(49,1<<28|7<<22),(49,1<<28|1),
          (50,2<<28|7<<22),(51,5<<28|1),(52,3<<28|1),
          (52,3<<28|7<<22),(52,3<<28|1<<25),(51,3<<28)]
    for index,(pos,value) in enumerate(more):
        c=copy.deepcopy(baseline);c["config"][pos]=value
        try: validate_config(c["config"])
        except ValueError: pass
        else: raise AssertionError((pos,value))
        c.update(name=f"reject-instruction-{index}",mode=10)
        cases.append(c)
    return cases


def main():
    p=argparse.ArgumentParser()
    p.add_argument("output",type=Path)
    args=p.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    cases=vectors()
    (args.output/"vectors.json").write_text(json.dumps(cases,indent=2)+"\n")
    def array(x): return "{"+",".join(str(n)+"u" for n in x)+"}"
    lines=['// Generated from owned descriptors; bound by evidence manifest.',
           'struct Case { const char* name; unsigned mode; std::vector<uint32_t> cfg,a,b,expected; };',
           'static const std::vector<Case> cases = {']
    for c in cases:
        lines.append('{'+json.dumps(c["name"])+','+str(c["mode"])+','+
                     ','.join(array(x) for x in [c["config"],*c["inputs"],c["expected"]])+'},')
    lines.append('};')
    (args.output/"fold_vectors.h").write_text("\n".join(lines)+"\n")
    setter=['static void configure(VAffineFoldRegion& top, const std::vector<uint32_t>& c) {']
    setter += [f'  top.io_cfg_{i} = c[{i}];' for i in range(65)]
    setter.append('}')
    (args.output/"fold_config.h").write_text("\n".join(setter)+"\n")
    print(json.dumps({"cases":len(cases),"successful_cells":sum(len(c["expected"]) for c in cases if c["mode"]==0)}))


if __name__=="__main__": main()
