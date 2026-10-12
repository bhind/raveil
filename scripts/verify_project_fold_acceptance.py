#!/usr/bin/env python3
"""Reread a fold acceptance directory without executing any subprocess."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from raveil import project as p, project_fold as f


def verify(root):
    receipt=json.loads((root/"receipt.json").read_bytes())
    if receipt["schema"]!="raveil.fold-acceptance/v1":raise ValueError("wrong acceptance schema")
    project=p.Project(root/"project")
    ids=[row["id"] for row in receipt["runs"]]
    if len(set(ids))!=len(ids) or set(ids)!={r["id"] for r in f.history(project)}:
        raise ValueError("acceptance history differs")
    cells=complete=0;bindings=[]
    for row in receipt["runs"]:
        record=f.load(project,row["id"])
        count=len(record["output"]) if record["status"]=="succeeded" else 0
        if count!=row["cells"]:raise ValueError("acceptance cell count differs")
        plan=f._json(f._read(project.root/"folds"/row["id"],"plan.json"))
        if plan["build_sha256"]!=receipt["build_sha256"]:raise ValueError("mixed builds")
        cells+=count;complete+=record["status"]=="succeeded"
        bindings.append({"id":row["id"],"record_sha256":p.digest(
            (project.root/"folds"/row["id"]/"record.json").read_bytes())})
    if cells!=receipt["cells"] or f.compare(project,receipt["diff"]["first"],receipt["diff"]["second"])!=receipt["diff"]:
        raise ValueError("acceptance summary differs")
    return {"evidence_class":"RTL-functional-simulation","runs":len(ids),"complete":complete,
            "incomplete":len(ids)-complete,"cells":cells,"bindings":bindings}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence",type=Path)
    print(p.encoded(verify(parser.parse_args().evidence)).decode(),end="")
