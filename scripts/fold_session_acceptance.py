#!/usr/bin/env python3
"""Functional session capacity, failure recovery and framing-loss acceptance."""
import argparse
import copy
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from raveil.fold_session import run,verify
from scripts.affine_fold_vectors import vectors,region,load


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kernel",type=Path,required=True)
    parser.add_argument("--build",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args();root=args.output.resolve();root.mkdir(parents=True,exist_ok=False)
    cases=[v for v in vectors() if v["mode"]==0]
    extra=copy.deepcopy(cases[0]);extra["name"]="maximum-input-envelope"
    extra["descriptor"]["lengths"]=[324,324];extra["inputs"]=[list(range(324)),list(range(324))]
    cases.append(extra)
    cases.append(dict(name="partial-second-output",descriptor=region([9,15],1,[135,0],
        {"a":[0,0,15,1,0]},[load("a","a")],"a"),inputs=[list(range(135)),[]]))
    def make(selected):
        return dict(schema="raveil.fold-session.v1",jobs=[
            dict(name=f"job-{i}-{case['name']}",region=case["descriptor"],inputs=case["inputs"])
            for i,case in enumerate(selected)])
    receipts=[]
    def execute(name,selected,injections=None):
        record=run(make(selected),args.kernel,args.build,root/name,injections=injections)
        verify(root/name)
        receipts.append(dict(name=name,processed=record["processed"],planned=record["planned"],
            halted=record["halted"],version=record["version"],
            successes=sum(row["result"]["approved"] for row in record["jobs"]),
            words=sum(len(row["result"]["output"]) for row in record["jobs"])))
        print("PASS",json.dumps(receipts[-1]),flush=True)
    for start in range(0,len(cases),8):execute(f"normal-{start//8}",cases[start:start+8])
    by_name={case["name"]:case for case in cases}
    execute("recovery-eight",[by_name[name] for name in
        ["add-16x16","add-16x16","mul-1x1","mul-1x1","row-sum","row-sum","matmul-16x16x16","matmul-16x16x16"]],
        ["none","replay-previous","none","wrong-word","none","bad-crc","rtl-fault","none"])
    for injection in ("invalid-char","no-response","truncated"):
        execute("halt-"+injection,[by_name["add-16x16"],by_name["mul-1x1"],by_name["matmul-16x16x16"]],
                ["none",injection,"none"])
    summary=dict(evidence_class="host-mediated-QEMU-RTL-session-functional",sessions=receipts)
    (root/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")


if __name__=="__main__":main()
