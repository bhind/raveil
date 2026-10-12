#!/usr/bin/env python3
"""Compare separately executed QEMU interpreter and RTL with the SSA oracle.

This is host-orchestrated differential testing, not QEMU/RTL co-simulation.
"""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from raveil import project as p,project_fold as f
from raveil.sonatine_fold import verify,digest


def verify_report(root):
    root=Path(root)
    report=json.loads((root/"report.json").read_text())
    if (set(report)!={"schema","evidence_classes","cases","checked_output_words","pairs"} or
        report["schema"]!="raveil.fold-differential.v1" or
        report["evidence_classes"]!=["qemu-emulation-correctness","RTL-functional-simulation"]):
        raise ValueError("invalid differential schema/class")
    project=p.Project(root/"project")
    words=0;names=set();ids=set()
    for pair in report["pairs"]:
        if set(pair)!={"case","qemu_receipt","qemu_receipt_sha256","rtl_id","words"}:
            raise ValueError("invalid differential pair")
        if pair["case"] in names or pair["rtl_id"] in ids:raise ValueError("duplicate pair")
        names.add(pair["case"]);ids.add(pair["rtl_id"])
        path=Path(pair["qemu_receipt"])
        if path.name!="receipt.json" or digest(path)!=pair["qemu_receipt_sha256"]:
            raise ValueError("changed QEMU receipt")
        qemu=verify(path.parent);rtl=f.load(project,pair["rtl_id"])
        saved=project.root/"folds"/pair["rtl_id"]
        if (json.loads((saved/"region.json").read_text())!=json.loads((path.parent/"region.json").read_text()) or
            f._input((saved/"input.json").read_bytes())!=json.loads((path.parent/"inputs.json").read_text()) or
            rtl["status"]!="succeeded" or rtl["output"]!=qemu["result"]["output"] or
            pair["words"]!=len(rtl["output"])):
            raise ValueError("different computation or output")
        words+=pair["words"]
    if not names or report["cases"]!=len(names) or report["checked_output_words"]!=words:
        raise ValueError("differential count mismatch")
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qemu-evidence",type=Path)
    parser.add_argument("--rtl-build",type=Path)
    parser.add_argument("--output",type=Path)
    parser.add_argument("--verify",type=Path)
    args=parser.parse_args()
    if args.verify:
        if any((args.qemu_evidence,args.rtl_build,args.output)):parser.error("verify is read-only")
        report=verify_report(args.verify)
        print(json.dumps({k:v for k,v in report.items() if k!="pairs"}));return
    if not all((args.qemu_evidence,args.rtl_build,args.output)):
        parser.error("qemu-evidence, rtl-build and output required")
    root=args.output.resolve();root.mkdir(parents=True,exist_ok=False)
    project=p.Project(p.init_project(root/"project"))
    pairs=[];words=0
    for n,path in enumerate(sorted(args.qemu_evidence.glob("*/receipt.json"))):
        qemu=verify(path.parent)
        descriptor=json.loads((path.parent/"region.json").read_text())
        inputs=json.loads((path.parent/"inputs.json").read_text())
        (project.root/"inputs"/"region.json").write_bytes(p.encoded(descriptor))
        (project.root/"inputs"/"input.json").write_bytes(p.encoded(
            {"schema":"raveil.fold-input/v1","buffers":inputs}))
        rtl=f.run(project,"region.json","input.json",args.rtl_build,seed=212+n)
        assert rtl["status"]=="succeeded",path.parent.name
        # load revalidates captured program/input/trace, without execution.
        saved=f.load(project,rtl["id"])
        assert saved["output"]==qemu["result"]["output"],path.parent.name
        words+=len(saved["output"])
        pairs.append(dict(case=path.parent.name,qemu_receipt=str(path.resolve()),
                          qemu_receipt_sha256=digest(path),rtl_id=rtl["id"],
                          words=len(saved["output"])))
        print("PASS",path.parent.name,len(saved["output"]),flush=True)
    if not pairs:raise ValueError("no QEMU receipts")
    report=dict(schema="raveil.fold-differential.v1",
                evidence_classes=["qemu-emulation-correctness","RTL-functional-simulation"],
                cases=len(pairs),checked_output_words=words,pairs=pairs)
    (root/"report.json").write_text(json.dumps(report,indent=2)+"\n")
    verify_report(root)
    print(json.dumps({k:v for k,v in report.items() if k!="pairs"}))


if __name__=="__main__":main()
