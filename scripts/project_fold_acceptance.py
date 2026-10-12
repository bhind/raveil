#!/usr/bin/env python3
"""Owned functional acceptance: same prebuilt RTL, runtime-file inputs."""
import argparse
import json
from pathlib import Path
import sys
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from raveil import project as p, project_fold as f
from scripts.affine_fold_vectors import vectors


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("build",type=Path)
    parser.add_argument("evidence",type=Path)
    args=parser.parse_args()
    args.evidence.mkdir(parents=True,exist_ok=False)
    project=p.Project(p.init_project(args.evidence/"project"))
    selected=[c for c in vectors() if c["mode"]==0]
    records=[];cells=0
    def save(case):
        (project.root/"inputs"/"region.json").write_bytes(p.encoded(case["descriptor"]))
        (project.root/"inputs"/"data.json").write_bytes(p.encoded(
            {"schema":"raveil.fold-input/v1","buffers":case["inputs"]}))
    for n,case in enumerate(selected):
        save(case)
        preview=f.check(project,"region.json","data.json")
        record=f.run(project,"region.json","data.json",args.build,seed=73+n)
        assert record["status"]=="succeeded" and record["output"]==case["expected"]
        cells+=len(record["output"])
        records.append({"case":case["name"],"id":record["id"],"cells":len(record["output"])})
        print("PASS",case["name"],preview["shape"],flush=True)
    case=selected[0];save(case)
    original=records[0]["id"]
    case["inputs"][0][0]^=0x12345
    save(case)
    edited=f.run(project,"region.json","data.json",args.build,seed=991)
    assert edited["status"]=="succeeded"
    delta=f.compare(project,original,edited["id"])
    assert delta["inputs_changed"] and delta["changed_cells"]==1
    records.append({"case":"edited-input","id":edited["id"],"cells":1});cells+=1
    # Freeze before execution: editing live files while the child runs cannot
    # affect the already captured request or future saved reads.
    saved=edited["output"].copy()
    execute=f._execute
    def edit_then_execute(root):
        (project.root/"inputs"/"data.json").write_text("invalid later edit")
        return execute(root)
    with patch.object(f,"_execute",edit_then_execute):
        frozen=f.run(project,"region.json","data.json",args.build)
    assert frozen["status"]=="succeeded" and frozen["output"]==saved
    records.append({"case":"edit-after-capture","id":frozen["id"],"cells":1});cells+=1
    save(case)
    for label,kwargs in (("cancel",{"cancel_after":1}),("memory-error",{"fault_at":1})):
        failed=f.run(project,"region.json","data.json",args.build,**kwargs)
        assert failed["status"]=="incomplete" and failed["output"] is None
        records.append({"case":label,"id":failed["id"],"cells":0})
    retry=f.run(project,"region.json","data.json",args.build)
    assert retry["status"]=="succeeded" and retry["output"]==saved
    records.append({"case":"fresh-retry","id":retry["id"],"cells":1});cells+=1
    with patch.object(f,"_execute",side_effect=AssertionError("saved read executed RTL")):
        for record in records: f.load(project,record["id"])
        assert len(f.history(project))==len(records)
        f.compare(project,original,edited["id"])
    receipt={"schema":"raveil.fold-acceptance/v1","evidence_class":"RTL-functional-simulation",
             "build_sha256":f.verify_build(args.build),"runs":records,"cells":cells,"diff":delta}
    (args.evidence/"receipt.json").write_bytes(p.encoded(receipt))
    print(json.dumps({"runs":len(records),"cells":cells}),flush=True)

if __name__=="__main__": main()
