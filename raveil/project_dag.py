"""Workspace capture/history for the existing bounded Sonatine/RTL DAG executor."""
from __future__ import annotations
from datetime import datetime,timezone
import os
from pathlib import Path
from uuid import uuid4
from . import project as p,project_fold as f,fold_dag as d
from .workspace import NativeWorkspace

SCHEMA='raveil.project-dag/v1'
PLAN='raveil.project-dag-plan/v1'
INPUT_LIMIT=1024*1024
CLASS='host-mediated-QEMU-RTL-dag-functional'


def _input(root,name):
    raw=NativeWorkspace(root).read_text(f._filename(name),maximum=INPUT_LIMIT).encode()
    session=f._json(raw);d.validate(session);return raw,session


def check(project,input_file):
    raw,session=_input(project.root/'inputs',input_file)
    return dict(schema='raveil.project-dag-preview/v1',input_file=input_file,
                input_sha256=p.digest(raw),**d.preview(session))


def _inventory(root):
    return {k:v for k,v in p.tree(root).items() if k not in {'/record.json','/record.sha256','/.record.pending'}}


def _typed_output(value):
    if (type(value) is not dict or set(value)!={'index','name','available','output','objects'} or
        type(value['index']) is not int or not 0<=value['index']<8 or type(value['name']) is not str or
        type(value['available']) is not bool or type(value['output']) is not list or
        any(type(v) is not int or not 0<=v<2**32 for v in value['output']) or
        type(value['objects']) is not list):return False
    if not value['available']:return value['output']==[] and value['objects']==[]
    if not 1<=len(value['output'])<=256 or len(value['objects'])!=(len(value['output'])+127)//128:return False
    return all(type(o) is dict and set(o)=={'object_id','generation','version'} and
               all(type(o[k]) is int for k in o) and 1<=o['object_id']<=8 and o['generation']==1 and o['version']>1
               for o in value['objects'])


def _inspect(root,record):
    if (type(record) is not dict or set(record)!={'schema','id','status','evidence_class','output','processed','planned','halted','files'} or
        record['schema']!=SCHEMA or record['id']!=root.name or record['evidence_class']!=CLASS or
        not _typed_output(record['output']) or record['files']!=_inventory(root)):raise ValueError('DAG record identity/inventory differs')
    plan=f._json(f._bytes(root,'plan.json'))
    if (set(plan)!={'schema','id','input_file','input_sha256','kernel_sha256','build_sha256','preview'} or
        plan['schema']!=PLAN or plan['id']!=root.name):raise ValueError('invalid DAG plan')
    f._filename(plan['input_file']);raw,session=_input(root,'input.json')
    if p.digest(raw)!=plan['input_sha256'] or p.encoded(d.preview(session))!=p.encoded(plan['preview']):raise ValueError('DAG snapshot differs')
    if (p.digest(f._bytes(root,'kernel.elf'))!=plan['kernel_sha256'] or
        f.verify_build(root/'runtime')!=plan['build_sha256']):raise ValueError('DAG frozen executable changed')
    child=d.verify(root/'execution')
    child_session=f._json(f._bytes(root/'execution','session.json'))
    child_plan=f._json(f._bytes(root/'execution','plan.json'))
    if (p.encoded(child_session)!=p.encoded(session) or child_plan['build_sha256']!=plan['build_sha256'] or
        p.digest(f._bytes(root/'execution','kernel.elf'))!=plan['kernel_sha256']):
        raise ValueError('DAG execution differs from captured input/executables')
    status='succeeded' if child['processed']==child['planned'] and child['halted']==0 and all(j['result']['approved'] for j in child['jobs']) else 'incomplete'
    if (record['status']!=status or p.encoded(record['output'])!=p.encoded(child['output']) or
        any(type(record[k]) is not int or p.encoded(record[k])!=p.encoded(child[k]) for k in ('processed','planned','halted'))):raise ValueError('DAG result differs')
    return record


def run(project,input_file,kernel,build):
    # Complete admission and source reads precede allocation. Literal values are frozen once.
    raw,session=_input(project.root/'inputs',input_file)
    kernel=Path(kernel).absolute();kernel_bytes=f._bytes(kernel.parent,kernel.name)
    build=Path(build).absolute();identity=f.verify_build(build,current=True)
    run_id=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ-')+uuid4().hex[:12]
    if 'dags' not in project.workspace.ls('/'):project.workspace.mkdir('dags',mode=0o700)
    project.workspace.mkdir('dags/'+run_id,mode=0o700);root=project.root/'dags'/run_id
    p.write_new(root/'input.json',raw);p.write_new(root/'kernel.elf',kernel_bytes)
    plan=dict(schema=PLAN,id=run_id,input_file=input_file,input_sha256=p.digest(raw),
              kernel_sha256=p.digest(kernel_bytes),build_sha256=identity,preview=d.preview(session))
    p.write_new(root/'plan.json',p.encoded(plan))
    p.tree(build,root/'runtime')
    if f.verify_build(root/'runtime',current=True)!=identity:raise ValueError('runtime changed during capture')
    (root/'runtime/simulator.bin').chmod(0o700)
    # Exceptions, SIGINT and cleanup uncertainty retain an unsealed attempt. No invented receipt.
    d.run(session,root/'kernel.elf',root/'runtime',root/'execution')
    child=d.verify(root/'execution')
    status='succeeded' if child['processed']==child['planned'] and child['halted']==0 and all(j['result']['approved'] for j in child['jobs']) else 'incomplete'
    record=dict(schema=SCHEMA,id=run_id,status=status,evidence_class=CLASS,output=child['output'],
                processed=child['processed'],planned=child['planned'],halted=child['halted'],files=_inventory(root))
    _inspect(root,record)
    payload=p.encoded(record)
    try:
        p.write_new(root/'.record.pending',payload)
        p.write_new(root/'record.sha256',(p.digest(payload)+'\n').encode())
        os.link(root/'.record.pending',root/'record.json')
        (root/'.record.pending').unlink()
    except KeyboardInterrupt:
        if not (root/'record.json').exists():raise
    return load(project,run_id)


def load(project,run_id):
    root=project.root/'dags'/p.name(run_id);raw=f._bytes(root,'record.json')
    if p.digest(raw)!=f._bytes(root,'record.sha256').decode().strip():raise ValueError('DAG record hash differs')
    return _inspect(root,f._json(raw))


def history(project):
    if 'dags' not in project.workspace.ls('/'):return []
    rows=[]
    for run_id in project.workspace.ls('dags'):
        p.name(run_id);names=NativeWorkspace(project.root/'dags'/run_id).ls('/')
        if 'record.json' not in names:rows.append(dict(id=run_id,status='unsealed',output_available=False));continue
        record=load(project,run_id)
        rows.append(dict(id=run_id,status=record['status'],output_available=record['output']['available'],output_name=record['output']['name']))
    return rows


def compare(project,first,second):
    records=[load(project,i) for i in (first,second)]
    if not all(r['output']['available'] for r in records):raise ValueError('comparison needs two verified available outputs')
    roots=[project.root/'dags'/r['id'] for r in records]
    plans=[f._json(f._bytes(root,'plan.json')) for root in roots]
    sessions=[_input(root,'input.json')[1] for root in roots]
    output_jobs=[next(j for j in s['jobs'] if j['name']==s['output']) for s in sessions]
    if (any(plans[0][k]!=plans[1][k] for k in ('kernel_sha256','build_sha256')) or
        records[0]['output']['name']!=records[1]['output']['name'] or
        output_jobs[0]['region']['shape']!=output_jobs[1]['region']['shape']):
        raise ValueError('comparison needs same kernel/runtime/output name/shape')
    a,b=(r['output']['output'] for r in records);shape=output_jobs[0]['region']['shape']
    changed=[i for i,(x,y) in enumerate(zip(a,b)) if x!=y]
    return dict(first=first,second=second,evidence_class='saved-functional-comparison',
        statuses=[r['status'] for r in records],output_name=records[0]['output']['name'],shape=shape,
        changed_cells=len(changed),first_change=(dict(row=changed[0]//shape[1],column=changed[0]%shape[1],
            before=a[changed[0]],after=b[changed[0]]) if changed else None),
        input_changed=plans[0]['input_sha256']!=plans[1]['input_sha256'],
        kernel_sha256=plans[0]['kernel_sha256'],build_sha256=plans[0]['build_sha256'])
