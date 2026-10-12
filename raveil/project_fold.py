"""Workspace adapter for the standalone MF01 functional RTL simulator.

Local cooperative files, not hostile-host authenticity or physical evidence.
"""
from __future__ import annotations
from datetime import datetime, timezone
import json
import os
import re
from pathlib import Path
import struct
import subprocess
from uuid import uuid4

from . import project as p
from .affine_fold import compile_region, reference
from .fold_evidence import loads
from .workspace import NativeWorkspace

IMAGE = "sha256:2efc059cf07eb054d93fc1fa32decd7a13c2cdb97069dac29138275b22e5c57c"
SOURCES = ("AffineFoldRegion.scala", "affine_fold_runtime.cpp", "fold_config.h",
           "build-affine-fold-runtime.sh")
SCHEMA = "raveil.project-fold/v1"

class CleanupUncertain(RuntimeError):
    """No final record may be sealed while a container writer may remain."""


def _container(cmd,*,stdout,stderr,timeout=240):
    container="raveil-fold-"+uuid4().hex
    process=subprocess.Popen([*cmd[:3],"--name",container,*cmd[3:]],
                             stdout=stdout,stderr=stderr,start_new_session=True)
    try:
        return process.wait(timeout=timeout)
    finally:
        try:
            try:
                if process.poll() is None:
                    process.kill();process.wait(timeout=30)
            finally:
                cleanup=subprocess.run(["docker","rm","-f",container],capture_output=True,timeout=30)
                if cleanup.returncode and b"No such container" not in cleanup.stderr:
                    raise CleanupUncertain("container removal failed")
        except BaseException as exc:
            raise CleanupUncertain(f"container cleanup could not be verified: {container}") from exc


def _json(raw):
    value=loads(raw)
    if type(value) is not dict:
        raise ValueError("expected JSON object")
    return value


def _bytes(root, name):
    ws=NativeWorkspace(root)
    info=ws.stat(name)
    if info.kind!="file" or info.size>p.MAX_BYTES:
        raise ValueError("expected bounded regular file")
    data=(root/name).read_bytes()
    if len(data)>p.MAX_BYTES: raise ValueError("file grew beyond limit")
    return data


def _read(root,name):
    return NativeWorkspace(root).read_text(name,maximum=64*1024).encode()


def _input(raw):
    value=_json(raw)
    if set(value)!={"schema","buffers"} or value["schema"]!="raveil.fold-input/v1":
        raise ValueError("invalid fold input")
    return value["buffers"]


def _filename(value):
    if type(value) is not str or not value.endswith(".json"):
        raise ValueError("expected JSON filename in inputs/")
    p.name(value[:-5])
    return value


def check(project,region_file,input_file):
    region=_read(project.root/"inputs",_filename(region_file))
    inputs=_read(project.root/"inputs",_filename(input_file))
    d=_json(region); data=_input(inputs)
    config=compile_region(d)
    expected=reference(d,data)
    return {"schema":"raveil.fold-preview/v1","shape":d["shape"],"extent":d["extent"],
            "instructions":config[8],"output_words":len(expected),
            "region_sha256":p.digest(region),"input_sha256":p.digest(inputs)}


def _inventory(root):
    return {k:v for k,v in p.tree(root).items() if k not in
            {"/record.json","/.record.pending"}}


def seal_build(root):
    """Bind a completed offline build; caller has already checked its exit code."""
    root=Path(root)
    if (root/"build.json").exists(): raise ValueError("build already sealed")
    inventory=p.tree(root)
    for n in (*("source/"+s for s in SOURCES),"simulator.bin","toolchain.txt"):
        if "/"+n not in inventory: raise ValueError("missing build artifact: "+n)
    if not any(k.startswith("/rtl/") and k.endswith(".sv") for k in inventory):
        raise ValueError("missing emitted RTL")
    manifest={"schema":"raveil.fold-build/v1","image":IMAGE,"files":inventory}
    p.write_new(root/"build.json",p.encoded(manifest))
    verify_build(root,current=True)
    return manifest


def verify_build(root,*,current=False):
    root=Path(root)
    raw=_bytes(root,"build.json")
    m=_json(raw)
    inventory={k:v for k,v in p.tree(root).items() if k!="/build.json"}
    if set(m)!={"schema","image","files"} or m["schema"]!="raveil.fold-build/v1" or m["image"]!=IMAGE or m["files"]!=inventory:
        raise ValueError("build identity differs")
    for n in SOURCES:
        data=_bytes(root,"source/"+n)
        if current and data!=(p.REPOSITORY/"hardware/chisel"/n).read_bytes():
            raise ValueError("build source differs: "+n)
    _bytes(root,"simulator.bin")
    return p.digest(raw)


def build(directory):
    root=Path(directory).absolute()
    if root.exists(): raise ValueError("build needs a fresh directory")
    subprocess.run(["docker","image","inspect",IMAGE],check=True,stdout=subprocess.DEVNULL)
    subprocess.run(["docker","volume","inspect","raveil-chisel-scala-cache-v1"],check=True,stdout=subprocess.DEVNULL)
    root.mkdir(parents=True,mode=0o700)
    with (root/"build.log").open("xb") as log:
        code=_container(["docker","run","--rm","--pull=never","--network","none",
            "--platform","linux/amd64","--mount",f"type=bind,src={p.REPOSITORY},dst=/source,readonly",
            "--mount",f"type=bind,src={root},dst=/evidence",
            "--mount","type=volume,src=raveil-chisel-scala-cache-v1,dst=/root/.cache,readonly",
            IMAGE,"sh","/source/hardware/chisel/build-affine-fold-runtime.sh"],
            stdout=log,stderr=subprocess.STDOUT)
        if code: raise ValueError(f"build failed (exit {code})")
    return seal_build(root)


def _execute(root):
    """Drain/remove the named container before the caller can publish a record."""
    cmd=["docker","run","--rm","--pull=never","--network","none",
         "--platform","linux/amd64","--mount",f"type=bind,src={root/'build'},dst=/build,readonly",
         "--mount",f"type=bind,src={root/'request.bin'},dst=/request.bin,readonly",
         "--mount",f"type=bind,src={root/'device'},dst=/out",
         IMAGE,"/build/simulator.bin","/request.bin","/out"]
    with (root/"stdout.txt").open("xb") as out,(root/"stderr.txt").open("xb") as err:
        return _container(cmd,stdout=out,stderr=err)


def _request(d,data,seed,cancel_after,fault_at):
    for x in (seed,cancel_after,fault_at):
        if type(x) is not int or not 0<=x<2**32: raise ValueError("invalid execution option")
    c=compile_region(d)
    words=[0x4d465231,1,*d["lengths"],seed,cancel_after,fault_at,0,*c,*data[0],*data[1]]
    return struct.pack("<"+"I"*len(words),*words)


def _device(root,d,data,options):
    """Reconstruct transactions and oracle from frozen inputs, never rerun."""
    cfg=compile_region(d)
    expected=reference(d,data)
    def transactions():
        for i in range(d["shape"][0]):
            for j in range(d["shape"][1]):
                for k in range(d["extent"]):
                    for node in d["nodes"]:
                        if node["op"]=="load":
                            buf,base,si,sj,sk=d["views"][node["view"]]
                            yield (0,324*buf+base+si*i+sj*j+sk*k,0)
                yield (1,648+i*d["shape"][1]+j,expected[i*d["shape"][1]+j])
    expected_requests=iter(transactions())
    raw=_bytes(root,"request.bin")
    if raw!=_request(d,data,**options): raise ValueError("request differs from snapshot")
    r=_json(_read(root/"device","device.json"))
    fields={"schema","success","fault","cancelled","accepted","completed","writes","reads"}
    if set(r)!=fields or r["schema"]!="raveil.fold-device/v1":
        raise ValueError("invalid device receipt")
    if any(type(r[k]) is not int or r[k]<0 for k in fields-{"schema"}):
        raise ValueError("invalid device counts")
    if any(r[k] not in (0,1) for k in ("success","fault","cancelled")):
        raise ValueError("invalid completion flags")
    if r["success"] and (r["fault"] or r["cancelled"]):
        raise ValueError("contradictory device status")
    trace=_bytes(root/"device","trace.bin")
    if len(trace)%24: raise ValueError("truncated transaction trace")
    pending=None;last=-1;reads=writes=completed=0;outputs={};error_seen=False
    for kind,cycle,write,address,value,error in struct.iter_unpack("<6I",trace):
        if cycle<=last or write not in (0,1) or error not in (0,1):
            raise ValueError("invalid transaction ordering")
        last=cycle
        if kind==0:
            if pending is not None or error: raise ValueError("overlapping request")
            if next(expected_requests,None)!=(write,address,value):
                raise ValueError("request differs from affine computation")
            if write:
                if not 648<=address<648+d["shape"][0]*d["shape"][1]:
                    raise ValueError("write outside output")
                writes+=1
            else:
                if not (address<len(data[0]) or 324<=address<324+len(data[1])) or value:
                    raise ValueError("read outside input")
                reads+=1
            pending=(write,address,value)
        elif kind==1:
            if pending is None or pending[:2]!=(write,address):
                raise ValueError("orphan/mismatched response")
            if error!=int(options["fault_at"]>0 and completed+1==options["fault_at"]):
                raise ValueError("error response differs from execution options")
            if error_seen: raise ValueError("transaction after error")
            error_seen=bool(error)
            if write:
                if value: raise ValueError("unexpected write response payload")
                if not error:
                    if address in outputs: raise ValueError("duplicate output write")
                    outputs[address]=pending[2]
            else:
                buf=0 if address<324 else 1
                if value!=data[buf][address-(324 if buf else 0)]:
                    raise ValueError("response differs from immutable input")
            pending=None;completed+=1
        else: raise ValueError("unknown trace event")
    if pending is not None or r["accepted"]!=reads+writes or r["completed"]!=completed or completed!=reads+writes or r["reads"]!=reads or r["writes"]!=writes:
        raise ValueError("undrained or miscounted transactions")
    if r["fault"]!=int(error_seen) or (r["success"] and error_seen):
        raise ValueError("completion contradicts memory error")
    if r["cancelled"] and (not options["cancel_after"] or completed<options["cancel_after"]):
        raise ValueError("cancellation contradicts options")
    if r["success"] and options["cancel_after"] and completed>options["cancel_after"]:
        raise ValueError("success after requested cancellation")
    if r["success"]:
        if next(expected_requests,None) is not None: raise ValueError("incomplete successful trace")
        binary=struct.pack("<"+"I"*len(expected),*expected)
        loads=sum((w>>28)==1 for w in cfg[49:49+cfg[8]])
        if outputs!={648+i:v for i,v in enumerate(expected)} or _bytes(root/"device","output.bin")!=binary or reads!=len(expected)*d["extent"]*loads or writes!=len(expected):
            raise ValueError("output differs from independent reference")
        return expected
    return None


def run(project,region_file,input_file,build_root,*,seed=1,cancel_after=0,fault_at=0,cancelled=lambda:False):
    # All admission happens before a run directory or execution is created.
    region=_read(project.root/"inputs",_filename(region_file))
    inputs=_read(project.root/"inputs",_filename(input_file))
    d=_json(region);data=_input(inputs);reference(d,data)
    options=dict(seed=seed,cancel_after=cancel_after,fault_at=fault_at)
    request=_request(d,data,**options)
    build_root=Path(build_root).absolute()
    identity=verify_build(build_root,current=True)
    run_id=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ-")+uuid4().hex[:12]
    if "folds" not in project.workspace.ls("/"): project.workspace.mkdir("folds",mode=0o700)
    project.workspace.mkdir("folds/"+run_id,mode=0o700)
    root=project.root/"folds"/run_id
    p.write_new(root/"region.json",region);p.write_new(root/"input.json",inputs)
    p.write_new(root/"request.bin",request)
    p.write_new(root/"plan.json",p.encoded({"schema":"raveil.fold-plan/v1","id":run_id,
        "region_file":region_file,"input_file":input_file,"build_sha256":identity,"options":options}))
    record={"schema":SCHEMA,"id":run_id,"status":"incomplete","output":None,
            "error":"","evidence_class":"RTL-functional-simulation","files":{}}
    def checkpoint():
        if cancelled(): raise KeyboardInterrupt("fold cancelled")
    try:
        checkpoint()
        p.tree(build_root,root/"build")
        if verify_build(root/"build",current=True)!=identity: raise ValueError("build changed during snapshot")
        (root/"build"/"simulator.bin").chmod(0o700)
        (root/"device").mkdir(mode=0o700)
        code=_execute(root)
        checkpoint()
        output=_device(root,d,data,options)
        if verify_build(root/"build")!=identity: raise ValueError("build changed during execution")
        if code!=0 or output is None: raise ValueError(f"device incomplete (exit {code})")
        record.update(status="succeeded",output=output)
        checkpoint()
    except (Exception,KeyboardInterrupt) as exc:
        # Cleanup uncertainty must not be sealed while a writer may remain live.
        if isinstance(exc,CleanupUncertain): raise
        record.update(status="incomplete",output=None,error=f"{type(exc).__name__}: {exc}")
    record["files"]=_inventory(root)
    try:
        p.write_new(root/".record.pending",p.encoded(record))
        os.replace(root/".record.pending",root/"record.json")
    except KeyboardInterrupt:
        if (root/"record.json").exists(): return load(project,run_id)
        raise
    return load(project,run_id)


def load(project,run_id):
    root=project.root/"folds"/p.name(run_id)
    record=_json(_bytes(root,"record.json"))
    if set(record)!={"schema","id","status","output","error","evidence_class","files"} or record["schema"]!=SCHEMA or record["id"]!=run_id or record["evidence_class"]!="RTL-functional-simulation" or record["files"]!=_inventory(root):
        raise ValueError("fold record identity/inventory differs")
    plan=_json(_read(root,"plan.json"))
    if set(plan)!={"schema","id","region_file","input_file","build_sha256","options"} or plan["schema"]!="raveil.fold-plan/v1" or plan["id"]!=run_id or type(plan["options"]) is not dict or set(plan["options"])!={"seed","cancel_after","fault_at"}:
        raise ValueError("invalid fold plan")
    if type(plan["build_sha256"]) is not str or not re.fullmatch(r"[0-9a-f]{64}",plan["build_sha256"]):
        raise ValueError("invalid fold build identity")
    _filename(plan["region_file"]);_filename(plan["input_file"])
    d=_json(_read(root,"region.json"));data=_input(_read(root,"input.json"))
    reference(d,data)
    if _bytes(root,"request.bin")!=_request(d,data,**plan["options"]): raise ValueError("snapshot request mismatch")
    if type(record["error"]) is not str: raise ValueError("invalid error")
    if record["status"]=="succeeded":
        expected=_device(root,d,data,plan["options"])
        if expected is None or type(record["output"]) is not list or any(type(x) is not int for x in record["output"]) or record["error"] or verify_build(root/"build")!=plan["build_sha256"] or record["output"]!=expected:
            raise ValueError("invalid successful fold")
    elif record["status"]!="incomplete" or record["output"] is not None:
        raise ValueError("invalid incomplete fold")
    return record


def history(project):
    if "folds" not in project.workspace.ls("/"): return []
    result=[]
    for i in project.workspace.ls("folds"):
        p.name(i)
        files=NativeWorkspace(project.root/"folds"/i).ls("/")
        result.append({"id":i,"status":load(project,i)["status"] if "record.json" in files else "unsealed"})
    return result


def compare(project,first,second):
    a,b=load(project,first),load(project,second)
    if a["status"]!="succeeded" or b["status"]!="succeeded": raise ValueError("need two successful folds")
    roots=[project.root/"folds"/x for x in (first,second)]
    plans=[_json(_read(r,"plan.json")) for r in roots]
    descriptors=[_json(_read(r,"region.json")) for r in roots]
    if plans[0]["build_sha256"]!=plans[1]["build_sha256"] or descriptors[0]["shape"]!=descriptors[1]["shape"]:
        raise ValueError("comparison requires same build and output shape")
    return {"first":first,"second":second,"changed_cells":sum(x!=y for x,y in zip(a["output"],b["output"])),
            "region_changed":_read(roots[0],"region.json")!=_read(roots[1],"region.json"),
            "inputs_changed":_read(roots[0],"input.json")!=_read(roots[1],"input.json")}
