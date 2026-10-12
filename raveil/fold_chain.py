"""Bounded MF01 result dependencies through guest capability snapshots."""
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
from .fold_session import rtl_values,reply,options,files_for,BASE_FILES,JOB_FILES,BROKEN_FRAME
from .affine_fold import compile_region,reference
from .sonatine_fold import command_for,digest

MAGIC=0x51434631
END=0x43454e44
CLASS="host-mediated-QEMU-RTL-chain-functional"
INJECTIONS=bridge.INJECTIONS|{"replay-previous"}
BROKEN_FRAME={"invalid-char","no-response","truncated"}
BASE_FILES={"session.json","plan.json","request.bin","kernel.elf","command.json",
            "qemu-version.txt","stdout.log","stderr.log"}
JOB_FILES={"request.bin","dispatch.json","response.bin","wire.txt"}


def validate(session):
    if type(session) is not dict or set(session)!={"schema","jobs"} or session["schema"]!="raveil.fold-chain.v1":
        raise ValueError("invalid chain schema")
    if type(session["jobs"]) is not list or not 1<=len(session["jobs"])<=8:
        raise ValueError("chain requires1..8 jobs")
    names={}
    for index,job in enumerate(session["jobs"]):
        if type(job) is not dict or set(job)!={"name","region","inputs"}:
            raise ValueError("invalid chain job")
        p.name(job["name"])
        if job["name"] in names:raise ValueError("duplicate chain name")
        config=compile_region(job["region"])
        if type(job["inputs"]) is not list or len(job["inputs"])!=2:raise ValueError("two inputs required")
        producer=None;literal=[]
        for operand,length in zip(job["inputs"],config[5:7]):
            if type(operand) is dict:
                if set(operand)!={"from"} or type(operand["from"]) is not str or operand["from"] not in names:
                    raise ValueError("link must name an earlier producer")
                source=names[operand["from"]]
                if producer is not None and source!=producer:raise ValueError("at most one distinct producer per job")
                producer=source;shape=session["jobs"][source]["region"]["shape"]
                if length!=shape[0]*shape[1]:raise ValueError("linked extent must equal producer logical output")
                literal.append([0]*length)
            else:literal.append(operand)
        reference(job["region"],literal);names[job["name"]]=index
    return session


def links(session,index):
    job=session["jobs"][index];source=0xffffffff;mask=0
    names={j["name"]:i for i,j in enumerate(session["jobs"])}
    for b,operand in enumerate(job["inputs"]):
        if type(operand) is dict:source=names[operand["from"]];mask|=1<<b
    return source,mask


def encode(session,epoch,request_ids):
    validate(session)
    if type(epoch) is not int or not 0<epoch<1<<64:raise ValueError("nonzero epoch required")
    if (type(request_ids) is not list or len(request_ids)!=len(session["jobs"]) or
        any(type(i) is not int or not 0<i<1<<64 for i in request_ids) or len(set(request_ids))!=len(request_ids)):
        raise ValueError("distinct nonzero request identities required")
    children=[];payload=b""
    for i,(job,rid) in enumerate(zip(session["jobs"],request_ids)):
        config=compile_region(job["region"]);source,mask=links(session,i)
        inputs=[[0]*config[5+b] if mask&(1<<b) else job["inputs"][b] for b in range(2)]
        child=bridge.request_bytes(config,inputs,rid);children.append(child)
        payload+=struct.pack("<2I",source,mask)+child
    body=struct.pack("<4IQ",MAGIC,1,32+len(payload),len(children),epoch)+payload
    return body+struct.pack("<2I",zlib.crc32(body),END),children


class State:
    """Independent host model; never used to grant guest input/publication authority."""
    def __init__(self,session):
        self.session=session;self.versions=[1,1];self.banks=[[0]*256,[0]*256]
        self.producers={};self.active=1
    def resolve(self,index):
        job=self.session["jobs"][index];source,mask=links(self.session,index)
        source_bank=0xffffffff;inputs=[]
        if mask:
            saved=self.producers.get(source)
            if saved is None or self.versions[saved[0]]!=saved[1]:return None
            source_bank=saved[0]
        for operand in job["inputs"]:
            inputs.append(self.producers[source][2][:] if type(operand) is dict else operand[:])
        return dict(name=job["name"],region=job["region"],inputs=inputs),source_bank,(source_bank if mask else self.active)^1
    def commit(self,index,destination,expected,success):
        if success:
            self.versions[destination]+=1;self.active=destination
            self.banks[destination]=expected+[0]*(256-len(expected))
            self.producers[index]=(destination,self.versions[destination],expected[:])
    def version_text(self):return ",".join(map(str,self.versions))


def block_line(session,index):
    return f"RAVEIL-FOLD-CHAIN-BLOCK-V1 index={index} source={links(session,index)[0]} reason=unavailable"


def check_step(lines,index,request,rid,epoch,expected,wire,injection,state,source,destination):
    if len(lines)!=4:raise ValueError("invalid chain phases")
    binding=bridge.dispatch(lines[0],request,rid,len(expected),epoch=epoch,sequence=index+1)
    if lines[1]!=">"*(len(wire)+int(injection in {"no-response","truncated"})):
        raise ValueError("chain credit mismatch")
    success=injection=="none";state.commit(index,destination,expected,success)
    version=state.versions[destination]
    frame=(f"RAVEIL-FOLD-CHAIN-STATE-V1 index={index} stable=1 framed={int(injection not in BROKEN_FRAME)} "
           f"destination={destination} source={source} versions={state.version_text()} ledger={index+1} "
           "submissions=0 inflight=0 shadows=0 completions=0 content="+
           "".join(f"{word:08x}" for bank in state.banks for word in bank))
    if lines[2]!=frame:raise ValueError("chain bank, version, padding or rollback mismatch")
    result=(f"RAVEIL-FOLD-CHAIN-RESULT-V1 index={index} request={rid:016x} epoch={epoch:016x} "
            f"sequence={index+1} cookie={binding['cookie']} status={1 if success else 4} approved={int(success)} "
            f"version={version} count={len(expected) if success else 0} output="+
            ("".join(f"{word:08x}" for word in expected) if success else "-"))
    if lines[3]!=result:raise ValueError("chain result binding mismatch")
    return binding,dict(approved=success,status=1 if success else 4,destination=destination,
                        source=source,version=version,output=expected if success else [])


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
    plan=dict(schema="raveil.fold-chain-plan.v1",epoch=epoch,request_ids=ids,
              injections=injections,build_sha256=identity)
    (root/"session.json").write_bytes(p.encoded(session));(root/"plan.json").write_bytes(p.encoded(plan))
    (root/"request.bin").write_bytes(envelope);shutil.copyfile(kernel,root/"kernel.elf")
    qemu=shutil.which("qemu-system-riscv64")
    if not qemu or "," in str(root):raise ValueError("invalid QEMU/path")
    command=command_for(qemu,root);(root/"command.json").write_bytes(p.encoded(command))
    (root/"qemu-version.txt").write_text(subprocess.check_output([qemu,"--version"],text=True))
    project=p.Project(p.init_project(root/"project"))
    rows=[];state_model=State(session);old_reply=None;halted=0
    proc=None;reader=None
    with (root/"stdout.log").open("wb") as out,(root/"stderr.log").open("wb") as err:
        try:
            proc=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err,bufsize=0)
            reader=bridge.Reader(proc,out,time.monotonic()+timeout)
            boot=0
            while True:
                line=reader.line();boot+=len(line)
                if boot>16384:raise ValueError("oversized session boot")
                if line.startswith("RAVEIL-FOLD-CHAIN"):
                    if line!=f"RAVEIL-FOLD-CHAIN-START-V1 epoch={epoch:016x} jobs={len(ids)} versions=1,1":
                        raise ValueError("session not admitted")
                    break
            for index,(job,injection,request,rid) in enumerate(zip(session["jobs"],injections,requests,ids)):
                reader.deadline=time.monotonic()+timeout
                line=reader.line();resolved=state_model.resolve(index)
                if resolved is None:
                    if line!=block_line(session,index):raise ValueError("missing dependency halt")
                    halted=3;break
                job,source,destination_bank=resolved
                request=bridge.request_bytes(compile_region(job["region"]),job["inputs"],rid)
                expected=reference(job["region"],job["inputs"])
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
                checked,result=check_step(
                    [line,">"*(len(wire)+len(remainder)),state,result_line],
                    index,request,rid,epoch,expected,wire,injection,state_model,source,destination_bank)
                if checked!=binding:raise ValueError("dispatch binding changed")
                old_reply=response
                rows.append(dict(index=index,name=job["name"],rtl_id=record["id"],binding=binding,result=result))
                if injection in BROKEN_FRAME:halted=1;break
            end=reader.line()
            if end!=f"RAVEIL-FOLD-CHAIN-END-V1 epoch={epoch:016x} processed={len(rows)} total={len(ids)} halted={halted} versions={state_model.version_text()}":
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
    receipt=dict(schema="raveil.fold-chain-run.v1",evidence_class=CLASS,epoch=epoch,
                 processed=len(rows),planned=len(ids),halted=halted,versions=state_model.versions,jobs=rows,
                 files={name:digest(root/name) for name in sorted(files_for(len(rows)))})
    _verify(root,receipt)
    (root/"receipt.tmp").write_bytes(p.encoded(receipt));(root/"receipt.tmp").replace(root/"receipt.json")
    return receipt


def verify(root):
    root=Path(root);return _verify(root,loads((root/"receipt.json").read_text()))


def _verify(root,receipt):
    keys={"schema","evidence_class","epoch","processed","planned","halted","versions","jobs","files"}
    if (type(receipt) is not dict or set(receipt)!=keys or receipt["schema"]!="raveil.fold-chain-run.v1" or
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
        plan["schema"]!="raveil.fold-chain-plan.v1"):raise ValueError("invalid session plan")
    injections=options(session,plan["injections"]);epoch=plan["epoch"];ids=plan["request_ids"]
    envelope,requests=encode(session,epoch,ids)
    if envelope!=(root/"request.bin").read_bytes() or not same([receipt["epoch"],receipt["planned"]],[epoch,len(ids)]):
        raise ValueError("session request mismatch")
    command=loads((root/"command.json").read_text())
    if (type(command) is not list or len(command)!=16 or any(type(item) is not str for item in command) or not Path(command[0]).is_absolute() or
        not Path(command[13]).is_absolute() or command!=command_for(command[0],Path(command[13]).parent)):
        raise ValueError("changed session QEMU command")
    lines=(root/"stdout.log").read_text().splitlines()
    starts=[i for i,line in enumerate(lines) if line.startswith("RAVEIL-FOLD-CHAIN-START")]
    if len(starts)!=1 or sum(len(line) for line in lines[:starts[0]])>16384:
        raise ValueError("invalid session start")
    lines=lines[starts[0]:]
    if (lines[0]!=f"RAVEIL-FOLD-CHAIN-START-V1 epoch={epoch:016x} jobs={len(ids)} versions=1,1" or
        len(lines)!=2+4*receipt["processed"]+int(receipt["halted"]==3)):raise ValueError("session phase count mismatch")
    project=p.Project(root/"project");state_model=State(session);old_reply=None;rtl_ids=set();halted=0
    for i,row in enumerate(receipt["jobs"]):
        resolved=state_model.resolve(i)
        if resolved is None:raise ValueError("job ran with unavailable producer")
        job,source,destination_bank=resolved
        request=bridge.request_bytes(compile_region(job["region"]),job["inputs"],ids[i])
        inj=injections[i];job_root=root/"jobs"/f"{i:02d}"
        if (type(row) is not dict or set(row)!={"index","name","rtl_id","binding","result"} or not same(row["index"],i) or type(row["rtl_id"]) is not str or
            row["name"]!=job["name"] or row["rtl_id"] in rtl_ids):
            raise ValueError("invalid session job record")
        rtl_ids.add(row["rtl_id"])
        rtl=f.load(project,row["rtl_id"])
        values=rtl_values(project,rtl,job,inj,plan["build_sha256"])
        expected=reference(job["region"],job["inputs"]);step=lines[1+4*i:5+4*i]
        binding=bridge.dispatch(step[0],request,ids[i],len(expected),epoch=epoch,sequence=i+1)
        response,wire=reply(binding,values,inj,old_reply)
        if (response!=(job_root/"response.bin").read_bytes() or wire!=(job_root/"wire.txt").read_bytes() or
            request!=(job_root/"request.bin").read_bytes() or
            not same(binding,loads((job_root/"dispatch.json").read_text()))):
            raise ValueError("changed session wire/binding")
        checked,result=check_step(step,i,request,ids[i],epoch,expected,wire,inj,state_model,source,destination_bank)
        if not same(checked,row["binding"]) or not same(result,row["result"]):raise ValueError("session result changed")
        old_reply=response
        if inj in BROKEN_FRAME:
            if i+1!=receipt["processed"]:raise ValueError("job ran after framing loss")
            halted=1
    if not halted and receipt["processed"]!=len(ids):
        index=receipt["processed"]
        if state_model.resolve(index) is not None or lines[-2]!=block_line(session,index):
            raise ValueError("chain ended without unavailable dependency")
        halted=3
    if (not same([receipt["halted"],receipt["versions"]],[halted,state_model.versions]) or
        lines[-1]!=f"RAVEIL-FOLD-CHAIN-END-V1 epoch={epoch:016x} processed={receipt['processed']} total={len(ids)} halted={halted} versions={state_model.version_text()}"):
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
    print(json.dumps({key:receipt[key] for key in ("epoch","processed","planned","halted","versions")}))


if __name__=="__main__":main()
