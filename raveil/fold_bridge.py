"""One guest-issued MF01 job, host-brokered RTL execution, guest approval.

UART functional coupling, not a memory-mapped device or hardware measurement.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import selectors
import shutil
import struct
import subprocess
import time
import zlib
from . import project as p,project_fold as f
from .affine_fold import compile_region,reference
from .fold_evidence import loads,same
from .sonatine_fold import encode,parse,command_for,digest

FILES=("region.json","inputs.json","request.bin","kernel.elf","command.json",
       "qemu-version.txt","stdout.log","stderr.log","dispatch.json","response.bin","wire.txt")
INJECTIONS={"none","wrong-word","stale-id","bad-crc","fault","rtl-fault","invalid-char","no-response","truncated"}


def request_bytes(config,inputs,request_id):
    body=bytearray(encode(config,inputs,request_id))
    struct.pack_into("<I",body,0,0x51464632)
    struct.pack_into("<I",body,len(body)-8,zlib.crc32(body[:-8]))
    return bytes(body)


def dispatch(line,request,request_id,count,*,epoch=None,sequence=1):
    expected_epoch=request_id if epoch is None else epoch
    expected_sequence=sequence
    m=re.fullmatch(r"RAVEIL-FOLD-DISPATCH-V1 request=([0-9a-f]{16}) epoch=([0-9a-f]{16}) "
                   r"sequence=([0-9a-f]{16}) cookie=([0-9a-f]{32}) count=([0-9]+) envelope=([0-9a-f]+)",line)
    if not m:raise ValueError("malformed dispatch")
    rid,epoch,sequence,cookie,n,envelope=m.groups()
    if (int(rid,16)!=request_id or int(epoch,16)!=expected_epoch or int(sequence,16)!=expected_sequence or
        int(cookie,16)==0 or int(n)!=count or bytes.fromhex(envelope)!=request):
        raise ValueError("dispatch does not match admitted boot request")
    return dict(request_id=request_id,epoch=int(epoch,16),sequence=int(sequence,16),cookie=cookie,count=count)


def response_bytes(binding,output,*,status=0):
    if len(output)!=binding["count"]:raise ValueError("response extent mismatch")
    body=struct.pack("<IIQQQ16sII",0x46525231,1,binding["request_id"],
                     binding["epoch"],binding["sequence"],bytes.fromhex(binding["cookie"]),
                     binding["count"],status)
    body+=struct.pack(f"<{len(output)}I",*output)
    return body+struct.pack("<I",zlib.crc32(body))


def injected_response(binding,output,injection):
    output=list(output);binding=dict(binding)
    if injection=="wrong-word":output[-1]^=1
    if injection=="stale-id":binding["request_id"]^=1
    reply=response_bytes(binding,output,status=int(injection in {"fault","rtl-fault"}))
    if injection=="bad-crc":reply=reply[:-1]+bytes([reply[-1]^1])
    wire=reply.hex().encode()
    if injection=="invalid-char":wire=b"!"
    if injection=="no-response":wire=b""
    if injection=="truncated":wire=wire[:-1]
    return reply,wire


def validate_transcript(stdout,request,rid,count,wire,injection):
    lines=stdout.splitlines()
    indexes=[i for i,line in enumerate(lines) if line.startswith("RAVEIL-FOLD-DISPATCH")]
    if len(indexes)!=1:raise ValueError("missing/duplicate dispatch")
    index=indexes[0];tail=lines[index:]
    # Boot diagnostics precede dispatch. The protocol has exactly four phases.
    if len(tail)!=4 or sum(len(line) for line in lines[:index])>16384:
        raise ValueError("invalid UART phase order or boot bound")
    binding=dispatch(tail[0],request,rid,count)
    credits=len(wire)+int(injection in {"no-response","truncated"})
    if tail[1]!=">"*credits:raise ValueError("UART credit mismatch")
    success=injection=="none"
    state=(f"RAVEIL-FOLD-BRIDGE-STATE-V1 stable=1 objects={(count+127)//128} "
           f"version={2 if success else 1} inflight=0 shadows=0 completions=0")
    if tail[2]!=state or not tail[3].startswith("RAVEIL-FOLD-RESULT-V1 "):
        raise ValueError("publication state or UART phase mismatch")
    result=parse(stdout,rid,count)
    if any(result[key]!=binding[key] for key in ("epoch","sequence","cookie")):
        raise ValueError("completion does not match dispatch binding")
    return binding,result


def verify_rtl_fault(saved,descriptor,inputs):
    plan=loads((saved/"plan.json").read_text())
    if type(plan) is not dict or not same(plan.get("options"),{"seed":213,"cancel_after":0,"fault_at":1}):
        raise ValueError("unexpected RTL fault options")
    if f.verify_build(saved/"build")!=plan["build_sha256"]:
        raise ValueError("RTL fault build mismatch")
    if f._device(saved,descriptor,inputs,plan["options"]) is not None:
        raise ValueError("faulting RTL produced successful output")
    device=loads((saved/"device"/"device.json").read_text())
    if (device["fault"],device["success"],device["cancelled"])!=(1,0,0):
        raise ValueError("no verified injected RTL fault")


from . import run_control as control


class Reader:
    def __init__(self,proc,log,deadline,*,line_limit=8192):
        if type(line_limit) is not int or not 8192<=line_limit<=16384:raise ValueError("invalid UART line bound")
        self.line_limit=line_limit
        self.proc=proc;self.log=log;self.deadline=deadline;self.buffer=bytearray()
        self.selector=selectors.DefaultSelector();self.selector.register(proc.stdout,selectors.EVENT_READ)
    def chunk(self):
        while True:
            control.checkpoint()
            remaining=self.deadline-time.monotonic()
            if remaining<=0:
                if control.current() is not None:raise control.Stopped("UART timeout",124)
                raise TimeoutError("UART deadline")
            if self.selector.select(min(remaining, .1) if control.current() is not None else remaining):break
        chunk=os.read(self.proc.stdout.fileno(),8192)
        if chunk:self.log.write(chunk);self.log.flush();self.buffer.extend(chunk)
        return bool(chunk)
    def line(self):
        control.checkpoint()
        while b"\n" not in self.buffer:
            if len(self.buffer)>self.line_limit:raise ValueError("oversized UART line")
            if not self.chunk():raise ValueError("guest exited before dispatch")
        line,_,rest=self.buffer.partition(b"\n");self.buffer=bytearray(rest)
        if len(line)>self.line_limit:raise ValueError("oversized UART line")
        return line.rstrip(b"\r").decode("ascii")
    def credit(self):
        control.checkpoint()
        while not self.buffer:
            if not self.chunk():raise ValueError("guest exited during response")
        if self.buffer.pop(0)!=ord(">"):raise ValueError("missing UART credit")
    def drain(self):
        while self.chunk():pass
    def close(self):self.selector.close()


def run(descriptor,inputs,kernel,build,destination,*,injection="none",timeout=90):
    if type(injection) is not str or injection not in INJECTIONS:
        raise ValueError("unknown test injection")
    config=compile_region(descriptor);expected=reference(descriptor,inputs)
    f.verify_build(Path(build),current=True)
    rid=secrets.randbits(64) or 1;request=request_bytes(config,inputs,rid)
    root=Path(destination).resolve();root.mkdir(parents=True,exist_ok=False)
    (root/"region.json").write_bytes(p.encoded(descriptor))
    (root/"inputs.json").write_bytes(p.encoded(inputs))
    (root/"request.bin").write_bytes(request)
    shutil.copyfile(kernel,root/"kernel.elf")
    qemu=shutil.which("qemu-system-riscv64")
    if not qemu or "," in str(root):raise ValueError("QEMU/path unavailable")
    command=command_for(qemu,root)
    (root/"command.json").write_bytes(p.encoded(command))
    (root/"qemu-version.txt").write_text(subprocess.check_output([qemu,"--version"],text=True))
    proc=None;reader=None
    with (root/"stdout.log").open("wb") as out,(root/"stderr.log").open("wb") as err:
        try:
            proc=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err,bufsize=0)
            reader=Reader(proc,out,time.monotonic()+timeout)
            while True:
                line=reader.line()
                if line.startswith("RAVEIL-FOLD-DISPATCH"):
                    binding=dispatch(line,request,rid,len(expected));break
            (root/"dispatch.json").write_bytes(p.encoded(binding))
            project=p.Project(p.init_project(root/"project"))
            (project.root/"inputs"/"region.json").write_bytes(p.encoded(descriptor))
            (project.root/"inputs"/"input.json").write_bytes(p.encoded(
                {"schema":"raveil.fold-input/v1","buffers":inputs}))
            rtl=f.run(project,"region.json","input.json",build,seed=213,
                      fault_at=int(injection=="rtl-fault"))
            rtl=f.load(project,rtl["id"])
            if injection=="rtl-fault":
                if rtl["status"]!="incomplete" or rtl["output"] is not None:
                    raise ValueError("RTL fault injection did not fail")
                verify_rtl_fault(project.root/"folds"/rtl["id"],descriptor,inputs)
                reply_values=[0]*len(expected)
            else:
                if rtl["status"]!="succeeded":raise ValueError("RTL did not complete successfully")
                reply_values=rtl["output"]
            reply,wire=injected_response(binding,reply_values,injection)
            (root/"response.bin").write_bytes(reply)
            (root/"wire.txt").write_bytes(wire)
            for character in wire:
                reader.credit();os.write(proc.stdin.fileno(),bytes([character]))
            reader.drain()
            code=proc.wait(timeout=2)
            if code:raise ValueError(f"QEMU exit {code}")
        finally:
            if proc is not None:
                if proc.poll() is None:
                    proc.terminate()
                    try:proc.wait(timeout=2)
                    except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=2)
                if proc.stdin:proc.stdin.close()
                if proc.stdout:proc.stdout.close()
            if reader is not None:reader.close()
    result=parse((root/"stdout.log").read_text(),rid,len(expected))
    state_lines=[line for line in (root/"stdout.log").read_text().splitlines()
                 if line.startswith("RAVEIL-FOLD-BRIDGE-STATE")]
    state=(f"RAVEIL-FOLD-BRIDGE-STATE-V1 stable=1 objects={(len(expected)+127)//128} "
           f"version={2 if injection=='none' else 1} inflight=0 shadows=0 completions=0")
    if state_lines!=[state]:raise ValueError("guest publication/rollback state is inconsistent")
    if injection=="none":
        if not result["approved"] or result["output"]!=expected:raise ValueError("guest output mismatch")
    elif result["approved"] or result["status"]!=4:
        raise ValueError("injected response was not rejected")
    record=dict(schema="raveil.fold-bridge.v1",
                evidence_class="host-mediated-QEMU-RTL-functional-coupling",
                request_id=rid,injection=injection,rtl_id=rtl["id"],result=result,
                files={name:digest(root/name) for name in FILES})
    _verify_record(root,record)
    (root/"receipt.tmp").write_bytes(p.encoded(record))
    (root/"receipt.tmp").replace(root/"receipt.json")
    return record


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ("region","inputs","kernel","build","output","verify"):
        parser.add_argument("--"+name,type=Path)
    args=parser.parse_args()
    if args.verify:
        if any((args.region,args.inputs,args.kernel,args.build,args.output)):
            parser.error("--verify cannot execute")
        record=verify(args.verify)
    else:
        if not all((args.region,args.inputs,args.kernel,args.build,args.output)):
            parser.error("region, inputs, kernel, build and output are required")
        inputs=loads(args.inputs.read_text())
        if isinstance(inputs,dict):inputs=f._input(args.inputs.read_bytes())
        record=run(loads(args.region.read_text()),inputs,args.kernel,args.build,args.output)
    print(json.dumps(record["result"]))


def verify(root):
    root=Path(root);record=loads((root/"receipt.json").read_text())
    return _verify_record(root,record)


def _verify_record(root,record):
    fields={"schema","evidence_class","request_id","injection","rtl_id","result","files"}
    if (type(record) is not dict or set(record)!=fields or record["schema"]!="raveil.fold-bridge.v1" or
        record["evidence_class"]!="host-mediated-QEMU-RTL-functional-coupling" or
        type(record["injection"]) is not str or record["injection"] not in INJECTIONS or
        type(record["rtl_id"]) is not str or type(record["result"]) is not dict or
        type(record["request_id"]) is not int or not 0<record["request_id"]<1<<64 or
        type(record["files"]) is not dict or set(record["files"])!=set(FILES)):
        raise ValueError("invalid bridge receipt")
    for name in FILES:
        if digest(root/name)!=record["files"][name]:raise ValueError("modified bridge evidence")
    descriptor=loads((root/"region.json").read_text());inputs=loads((root/"inputs.json").read_text())
    expected=reference(descriptor,inputs);rid=record["request_id"]
    request=request_bytes(compile_region(descriptor),inputs,rid)
    if request!=(root/"request.bin").read_bytes():raise ValueError("request mismatch")
    command=loads((root/"command.json").read_text())
    if (type(command) is not list or len(command)!=16 or any(type(item) is not str for item in command) or not Path(command[0]).is_absolute() or
        not Path(command[13]).is_absolute() or command!=command_for(command[0],Path(command[13]).parent)):
        raise ValueError("invalid bridge QEMU command")
    stdout=(root/"stdout.log").read_text()
    lines=[line for line in stdout.splitlines() if line.startswith("RAVEIL-FOLD-DISPATCH")]
    if len(lines)!=1:raise ValueError("missing/duplicate dispatch")
    binding=dispatch(lines[0],request,rid,len(expected))
    if not same(binding,loads((root/"dispatch.json").read_text())):raise ValueError("binding mismatch")
    project=p.Project(root/"project");rtl=f.load(project,record["rtl_id"])
    saved=project.root/"folds"/record["rtl_id"]
    if (not same(loads((saved/"region.json").read_text()),descriptor) or
        not same(f._input((saved/"input.json").read_bytes()),inputs)):
        raise ValueError("RTL computation mismatch")
    if record["injection"]=="rtl-fault":
        if rtl["status"]!="incomplete" or rtl["output"] is not None:
            raise ValueError("RTL fault result mismatch")
        verify_rtl_fault(saved,descriptor,inputs)
        reply_values=[0]*len(expected)
    else:
        if rtl["status"]!="succeeded" or not same(rtl["output"],expected):
            raise ValueError("RTL result mismatch")
        reply_values=rtl["output"]
    reply,wire=injected_response(binding,reply_values,record["injection"])
    if reply!=(root/"response.bin").read_bytes() or wire!=(root/"wire.txt").read_bytes():
        raise ValueError("UART response mismatch")
    checked_binding,result=validate_transcript(stdout,request,rid,len(expected),wire,record["injection"])
    if not same(checked_binding,binding):raise ValueError("dispatch binding changed")
    if not same(result,record["result"]):raise ValueError("result mismatch")
    success=record["injection"]=="none"
    if ((success and (not result["approved"] or result["output"]!=expected)) or
        (not success and (result["approved"] or result["status"]!=4))):
        raise ValueError("unexpected bridge disposition")
    state=(f"RAVEIL-FOLD-BRIDGE-STATE-V1 stable=1 objects={(len(expected)+127)//128} "
           f"version={2 if success else 1} inflight=0 shadows=0 completions=0")
    if [line for line in stdout.splitlines() if line.startswith("RAVEIL-FOLD-BRIDGE-STATE")]!=[state]:
        raise ValueError("publication state mismatch")
    return record


if __name__=="__main__":
    main()
