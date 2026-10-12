#!/usr/bin/env python3
"""Retained QEMU functional evidence, distinct from RTL and hardware evidence."""
import argparse
import copy
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import zlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from raveil.sonatine_fold import run,verify,encode,parse,command_for,digest
from scripts.affine_fold_vectors import vectors,region,load


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kernel",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    root=args.output.resolve();root.mkdir(parents=True,exist_ok=False)
    cases=[c for c in vectors() if c["mode"]==0]
    extra=copy.deepcopy(cases[0]);extra["name"]="maximum-input-envelope"
    extra["descriptor"]["lengths"]=[324,324]
    extra["inputs"]=[list(range(324)),list(range(324))]
    cases.append(extra)
    cases.append(dict(name="partial-second-output",descriptor=region([9,15],1,[135,0],
        {"a":[0,0,15,1,0]},[load("a","a")],"a"),inputs=[list(range(135)),[]]))
    words=0
    for case in cases:
        target=root/case["name"]
        receipt=run(case["descriptor"],case["inputs"],args.kernel,target)
        verify(target);words+=len(receipt["result"]["output"])
    rejected=[]
    baseline=next(c for c in vectors() if c["name"]=="mul-1x1")
    original=encode(baseline["config"],baseline["inputs"],7)
    for case in vectors():
        if case["mode"]!=10:continue
        bad=bytearray(original);struct.pack_into("<65I",bad,32,*case["config"])
        struct.pack_into("<I",bad,len(bad)-8,zlib.crc32(bad[:-8]))
        rejected.append((case["name"],bytes(bad)))
    rejected.extend([("truncated-footer",original[:-1]),("corrupt-input",
                     original[:292]+bytes([original[292]^1])+original[293:])])
    qemu=shutil.which("qemu-system-riscv64")
    for name,blob in rejected:
        target=root/name;target.mkdir()
        (target/"request.bin").write_bytes(blob);shutil.copyfile(args.kernel,target/"kernel.elf")
        command=command_for(qemu,target)
        (target/"command.json").write_text(json.dumps(command)+"\n")
        proc=subprocess.run(command,capture_output=True,timeout=15,check=True)
        (target/"stdout.log").write_bytes(proc.stdout);(target/"stderr.log").write_bytes(proc.stderr)
        result=parse(proc.stdout.decode(),7,1)
        assert result["status"]==2 and not result["approved"] and not result["output"],name
        (target/"rejection.json").write_text(json.dumps(result)+"\n")
    summary=dict(evidence_class="qemu-emulation-correctness",successful=len(cases),
                 rejected=len(rejected),checked_output_words=words,
                 kernel_sha256=digest(args.kernel))
    (root/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps(summary))


if __name__=="__main__":main()
