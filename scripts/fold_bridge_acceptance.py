#!/usr/bin/env python3
"""Run all MF01 functional cases through guest dispatch and host-brokered RTL."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from raveil.fold_bridge import run,verify
from scripts.affine_fold_vectors import vectors,region,load


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kernel",type=Path,required=True)
    parser.add_argument("--build",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args();root=args.output.resolve();root.mkdir(parents=True,exist_ok=False)
    cases=[v for v in vectors() if v["mode"]==0]
    extra=vectors()[0];extra["name"]="maximum-input-envelope"
    extra["descriptor"]["lengths"]=[324,324];extra["inputs"]=[list(range(324)),list(range(324))]
    cases.append(extra)
    cases.append(dict(name="partial-second-output",descriptor=region([9,15],1,[135,0],
        {"a":[0,0,15,1,0]},[load("a","a")],"a"),inputs=[list(range(135)),[]]))
    records=[]
    for case,injection in [*[(v,"none") for v in cases],*[(cases[0],inj) for inj in
        ("wrong-word","stale-id","bad-crc","fault","rtl-fault","invalid-char","no-response","truncated")]]:
        target=root/(case["name"]+"-"+injection)
        record=run(case["descriptor"],case["inputs"],args.kernel,args.build,target,injection=injection)
        verify(target);records.append(dict(case=case["name"],injection=injection,
            approved=record["result"]["approved"],words=len(record["result"]["output"])))
        print("PASS",case["name"],injection,flush=True)
    summary=dict(evidence_class="host-mediated-QEMU-RTL-functional-coupling",records=records,
        successful=sum(r["approved"] for r in records),rejected=sum(not r["approved"] for r in records),
        output_words=sum(r["words"] for r in records))
    (root/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")


if __name__=="__main__":main()
