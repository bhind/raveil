"""Bounded sequential MF01 jobs in one Sonatine boot, with persistent outputs.

Functional UART coupling only; sessions are predeclared and contain1..8 jobs.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import struct
import subprocess
import time
import zlib
from .fold_evidence import loads, same
from . import project as p,project_fold as f,fold_bridge as bridge
from .affine_fold import compile_region,reference
from .sonatine_fold import command_for,digest

MAGIC=0x51534631
END=0x53454e44
CLASS="host-mediated-QEMU-RTL-session-functional"
INJECTIONS=bridge.INJECTIONS|{"replay-previous"}
BROKEN_FRAME={"invalid-char","no-response","truncated"}
BASE_FILES={"session.json","plan.json","request.bin","kernel.elf","command.json",
            "qemu-version.txt","stdout.log","stderr.log"}
JOB_FILES={"request.bin","dispatch.json","response.bin","wire.txt"}


def validate(session):
    if type(session) is not dict or set(session)!={"schema","jobs"} or session["schema"]!="raveil.fold-session.v1":
        raise ValueError("invalid session schema")
    if type(session["jobs"]) is not list or not 1<=len(session["jobs"])<=8:
        raise ValueError("session requires1..8 jobs")
    names=set()
    for job in session["jobs"]:
        if type(job) is not dict or set(job)!={"name","region","inputs"}:
            raise ValueError("invalid session job")
        p.name(job["name"])
        if job["name"] in names:raise ValueError("duplicate session name")
        names.add(job["name"]);compile_region(job["region"]);reference(job["region"],job["inputs"])
    return session


def encode(session,epoch,request_ids):
    validate(session)
    if type(epoch) is not int or not 0<epoch<1<<64:
        raise ValueError("nonzero session epoch required")
    if (type(request_ids) is not list or len(request_ids)!=len(session["jobs"]) or
        any(type(i) is not int or not 0<i<1<<64 for i in request_ids) or
        len(set(request_ids))!=len(request_ids)):
        raise ValueError("distinct nonzero request identities required")
    requests=[bridge.request_bytes(compile_region(job["region"]),job["inputs"],rid)
              for job,rid in zip(session["jobs"],request_ids)]
    size=32+sum(map(len,requests))
    body=struct.pack("<4IQ",MAGIC,1,size,len(requests),epoch)+b"".join(requests)
    return body+struct.pack("<2I",zlib.crc32(body),END),requests


def options(session,injections):
    if injections is None:injections=["none"]*len(session["jobs"])
    if (type(injections) is not list or len(injections)!=len(session["jobs"]) or
        any(type(i) is not str or i not in INJECTIONS for i in injections)):
        raise ValueError("one known injection per job required")
    for i,injection in enumerate(injections):
        if injection=="replay-previous":
            if i==0 or injections[i-1]!="none":
                raise ValueError("replay needs a preceding successful response")
            shapes=[session["jobs"][n]["region"]["shape"] for n in (i-1,i)]
            if shapes[0][0]*shapes[0][1]!=shapes[1][0]*shapes[1][1]:
                raise ValueError("replayed frame must have the current bounded size")
    return injections


def reply(binding,values,injection,previous):
    if injection=="replay-previous":
        if previous is None:raise ValueError("no previous response")
        return previous,previous.hex().encode()
    return bridge.injected_response(binding,values,injection)


def check_step(lines,index,request,rid,epoch,expected,wire,injection,version,previous):
    if len(lines)!=4:raise ValueError("invalid session step phases")
    binding=bridge.dispatch(lines[0],request,rid,len(expected),epoch=epoch,sequence=index+1)
    credits=len(wire)+int(injection in {"no-response","truncated"})
    if lines[1]!=">"*credits:raise ValueError("session credit mismatch")
    success=injection=="none";version+=int(success)
    content=expected+[0]*(256-len(expected)) if success else previous
    state=(f"RAVEIL-FOLD-SESSION-STATE-V1 index={index} stable=1 "
           f"framed={int(injection not in BROKEN_FRAME)} version={version} ledger={index+1} "
           "submissions=0 inflight=0 shadows=0 completions=0 content="+
           "".join(f"{word:08x}" for word in content))
    if lines[2]!=state:raise ValueError("session state, padding or rollback mismatch")
    result=(f"RAVEIL-FOLD-SESSION-RESULT-V1 index={index} request={rid:016x} "
            f"epoch={epoch:016x} sequence={index+1} cookie={binding['cookie']} "
            f"status={1 if success else 4} approved={int(success)} version={version} "
            f"count={len(expected) if success else 0} output="+
            ("".join(f"{word:08x}" for word in expected) if success else "-"))
    if lines[3]!=result:raise ValueError("session result or completion binding mismatch")
    return binding,dict(approved=success,status=1 if success else 4,
                        version=version,output=expected if success else []),content


def rtl_values(project,record,job,injection,build_identity):
    saved=project.root/"folds"/record["id"]
    plan=loads((saved/"plan.json").read_text())
    if plan["build_sha256"]!=build_identity:raise ValueError("session RTL build changed")
    if not same(plan["options"],{"seed":213,"cancel_after":0,"fault_at":int(injection=="rtl-fault")}):
        raise ValueError("session RTL execution options changed")
    if (not same(loads((saved/"region.json").read_text()),job["region"]) or
        not same(f._input((saved/"input.json").read_bytes()),job["inputs"])):
        raise ValueError("session RTL computation changed")
    expected=reference(job["region"],job["inputs"])
    if injection=="rtl-fault":
        if record["status"]!="incomplete" or record["output"] is not None:
            raise ValueError("RTL fault did not occur")
        bridge.verify_rtl_fault(saved,job["region"],job["inputs"])
        return [0]*len(expected)
    if record["status"]!="succeeded" or not same(record["output"],expected):
        raise ValueError("session RTL did not complete correctly")
    return record["output"]


def files_for(processed):
    return BASE_FILES|{f"jobs/{i:02d}/{name}" for i in range(processed) for name in JOB_FILES}


def run(session,kernel,build,destination,*,injections=None,timeout=90):
    validate(session);injections=options(session,injections)
    identity=f.verify_build(Path(build),current=True)
    epoch=secrets.randbits(64) or 1;ids=[]
    while len(ids)<len(session["jobs"]):
        rid=secrets.randbits(64)
        if rid and rid!=epoch and rid not in ids:ids.append(rid)
    envelope,requests=encode(session,epoch,ids)
    root=Path(destination).resolve();root.mkdir(parents=True,exist_ok=False)
    plan=dict(schema="raveil.fold-session-plan.v1",epoch=epoch,request_ids=ids,
              injections=injections,build_sha256=identity)
    (root/"session.json").write_bytes(p.encoded(session));(root/"plan.json").write_bytes(p.encoded(plan))
    (root/"request.bin").write_bytes(envelope);shutil.copyfile(kernel,root/"kernel.elf")
    qemu=shutil.which("qemu-system-riscv64")
    if not qemu or "," in str(root):raise ValueError("invalid QEMU/path")
    command=command_for(qemu,root);(root/"command.json").write_bytes(p.encoded(command))
    (root/"qemu-version.txt").write_text(subprocess.check_output([qemu,"--version"],text=True))
    project=p.Project(p.init_project(root/"project"))
    rows=[];previous=[0]*256;version=1;old_reply=None;halted=0
    proc=None;reader=None
    with (root/"stdout.log").open("wb") as out,(root/"stderr.log").open("wb") as err:
        try:
            proc=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err,bufsize=0)
            reader=bridge.Reader(proc,out,time.monotonic()+timeout)
            boot=0
            while True:
                line=reader.line();boot+=len(line)
                if boot>16384:raise ValueError("oversized session boot")
                if line.startswith("RAVEIL-FOLD-SESSION"):
                    if line!=f"RAVEIL-FOLD-SESSION-START-V1 epoch={epoch:016x} jobs={len(ids)} version=1":
                        raise ValueError("session not admitted")
                    break
            for index,(job,injection,request,rid) in enumerate(zip(session["jobs"],injections,requests,ids)):
                reader.deadline=time.monotonic()+timeout
                line=reader.line();expected=reference(job["region"],job["inputs"])
                binding=bridge.dispatch(line,request,rid,len(expected),epoch=epoch,sequence=index+1)
                job_root=root/"jobs"/f"{index:02d}";job_root.mkdir(parents=True)
                (job_root/"request.bin").write_bytes(request)
                (job_root/"dispatch.json").write_bytes(p.encoded(binding))
                (project.root/"inputs"/"region.json").write_bytes(p.encoded(job["region"]))
                (project.root/"inputs"/"input.json").write_bytes(p.encoded(
                    {"schema":"raveil.fold-input/v1","buffers":job["inputs"]}))
                record=f.run(project,"region.json","input.json",build,seed=213,
                             fault_at=int(injection=="rtl-fault"))
                record=f.load(project,record["id"])
                values=rtl_values(project,record,job,injection,identity)
                response,wire=reply(binding,values,injection,old_reply)
                (job_root/"response.bin").write_bytes(response);(job_root/"wire.txt").write_bytes(wire)
                for character in wire:
                    reader.credit();os.write(proc.stdin.fileno(),bytes([character]))
                remainder=reader.line()
                if remainder!=(">" if injection in {"no-response","truncated"} else ""):
                    raise ValueError("unexpected post-response UART data")
                state=reader.line();result_line=reader.line()
                checked,result,previous=check_step(
                    [line,">"*(len(wire)+len(remainder)),state,result_line],
                    index,request,rid,epoch,expected,wire,injection,version,previous)
                if checked!=binding:raise ValueError("dispatch binding changed")
                version=result["version"];old_reply=response
                rows.append(dict(index=index,name=job["name"],rtl_id=record["id"],binding=binding,result=result))
                if injection in BROKEN_FRAME:halted=1;break
            end=reader.line()
            if end!=f"RAVEIL-FOLD-SESSION-END-V1 epoch={epoch:016x} processed={len(rows)} total={len(ids)} halted={halted} version={version}":
                raise ValueError("session final state mismatch")
            reader.drain()
            if proc.wait(timeout=2):raise ValueError("QEMU session failed")
        finally:
            if proc is not None:
                if proc.poll() is None:
                    proc.terminate()
                    try:proc.wait(timeout=2)
                    except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=2)
                if proc.stdin:proc.stdin.close()
                if proc.stdout:proc.stdout.close()
            if reader is not None:reader.close()
    receipt=dict(schema="raveil.fold-session-run.v1",evidence_class=CLASS,epoch=epoch,
                 processed=len(rows),planned=len(ids),halted=halted,version=version,jobs=rows,
                 files={name:digest(root/name) for name in sorted(files_for(len(rows)))})
    _verify(root,receipt)
    (root/"receipt.tmp").write_bytes(p.encoded(receipt));(root/"receipt.tmp").replace(root/"receipt.json")
    return receipt


def verify(root):
    root=Path(root);return _verify(root,loads((root/"receipt.json").read_text()))


def _verify(root,receipt):
    keys={"schema","evidence_class","epoch","processed","planned","halted","version","jobs","files"}
    if (type(receipt) is not dict or set(receipt)!=keys or receipt["schema"]!="raveil.fold-session-run.v1" or
        receipt["evidence_class"]!=CLASS or type(receipt["processed"]) is not int or
        not 1<=receipt["processed"]<=8 or type(receipt["jobs"]) is not list or len(receipt["jobs"])!=receipt["processed"] or
        type(receipt["files"]) is not dict or set(receipt["files"])!=files_for(receipt["processed"])):
        raise ValueError("invalid session receipt")
    for name in receipt["files"]:
        if digest(root/name)!=receipt["files"][name]:raise ValueError("changed session evidence")
    session=validate(loads((root/"session.json").read_text()))
    if receipt["processed"]>len(session["jobs"]):raise ValueError("processed count exceeds declared jobs")
    plan=loads((root/"plan.json").read_text())
    if (type(plan) is not dict or set(plan)!={"schema","epoch","request_ids","injections","build_sha256"} or
        plan["schema"]!="raveil.fold-session-plan.v1"):raise ValueError("invalid session plan")
    injections=options(session,plan["injections"]);epoch=plan["epoch"];ids=plan["request_ids"]
    envelope,requests=encode(session,epoch,ids)
    if envelope!=(root/"request.bin").read_bytes() or not same([receipt["epoch"],receipt["planned"]],[epoch,len(ids)]):
        raise ValueError("session request mismatch")
    command=loads((root/"command.json").read_text())
    if (type(command) is not list or len(command)!=16 or any(type(item) is not str for item in command) or not Path(command[0]).is_absolute() or
        not Path(command[13]).is_absolute() or command!=command_for(command[0],Path(command[13]).parent)):
        raise ValueError("changed session QEMU command")
    lines=(root/"stdout.log").read_text().splitlines()
    starts=[i for i,line in enumerate(lines) if line.startswith("RAVEIL-FOLD-SESSION-START")]
    if len(starts)!=1 or sum(len(line) for line in lines[:starts[0]])>16384:
        raise ValueError("invalid session start")
    lines=lines[starts[0]:]
    if (lines[0]!=f"RAVEIL-FOLD-SESSION-START-V1 epoch={epoch:016x} jobs={len(ids)} version=1" or
        len(lines)!=2+4*receipt["processed"]):raise ValueError("session phase count mismatch")
    project=p.Project(root/"project");previous=[0]*256;version=1;old_reply=None;rtl_ids=set();halted=0
    for i,row in enumerate(receipt["jobs"]):
        job=session["jobs"][i];inj=injections[i];job_root=root/"jobs"/f"{i:02d}"
        if (type(row) is not dict or set(row)!={"index","name","rtl_id","binding","result"} or not same(row["index"],i) or type(row["rtl_id"]) is not str or
            row["name"]!=job["name"] or row["rtl_id"] in rtl_ids):
            raise ValueError("invalid session job record")
        rtl_ids.add(row["rtl_id"])
        rtl=f.load(project,row["rtl_id"])
        values=rtl_values(project,rtl,job,inj,plan["build_sha256"])
        expected=reference(job["region"],job["inputs"]);step=lines[1+4*i:5+4*i]
        binding=bridge.dispatch(step[0],requests[i],ids[i],len(expected),epoch=epoch,sequence=i+1)
        response,wire=reply(binding,values,inj,old_reply)
        if (response!=(job_root/"response.bin").read_bytes() or wire!=(job_root/"wire.txt").read_bytes() or
            requests[i]!=(job_root/"request.bin").read_bytes() or
            not same(binding,loads((job_root/"dispatch.json").read_text()))):
            raise ValueError("changed session wire/binding")
        checked,result,previous=check_step(step,i,requests[i],ids[i],epoch,expected,wire,inj,version,previous)
        if not same(checked,row["binding"]) or not same(result,row["result"]):raise ValueError("session result changed")
        version=result["version"];old_reply=response
        if inj in BROKEN_FRAME:
            if i+1!=receipt["processed"]:raise ValueError("job ran after framing loss")
            halted=1
    if not halted and receipt["processed"]!=len(ids):raise ValueError("session ended early")
    if (not same([receipt["halted"],receipt["version"]],[halted,version]) or
        lines[-1]!=f"RAVEIL-FOLD-SESSION-END-V1 epoch={epoch:016x} processed={receipt['processed']} total={len(ids)} halted={halted} version={version}"):
        raise ValueError("session end mismatch")
    return receipt


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ("session","kernel","build","output","verify"):parser.add_argument("--"+name,type=Path)
    args=parser.parse_args()
    if args.verify:
        if any((args.session,args.kernel,args.build,args.output)):parser.error("--verify is read-only")
        receipt=verify(args.verify)
    else:
        if not all((args.session,args.kernel,args.build,args.output)):parser.error("session/kernel/build/output required")
        receipt=run(loads(args.session.read_text()),args.kernel,args.build,args.output)
    print(json.dumps({key:receipt[key] for key in ("epoch","processed","planned","halted","version")}))


if __name__=="__main__":main()
