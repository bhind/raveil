"""Bounded independent DAG composition over the existing coupled executor.

One immutable input/kernel/runtime snapshot; named outputs publish only together.
This does not make inter-child dependencies or an enlarged guest session.
"""
from datetime import datetime, timezone
import os
from pathlib import Path
from uuid import uuid4
from . import project as p, project_fold as f, fold_dag as d, project_dag as a
from .fold_evidence import loads, same
from .workspace import NativeWorkspace

INPUT='raveil.dag-batch.v1'
SCHEMA='raveil.project-dag-batch/v1'
PLAN='raveil.project-dag-batch-plan/v1'
CLASS='host-composed-QEMU-RTL-dag-functional'
INPUT_LIMIT=4*1024*1024
MAX_BYTES=128*1024*1024
MAX_ENTRIES=16384


def validate(value):
    if (type(value) is not dict or set(value)!={'schema','items'} or value['schema']!=INPUT or
        type(value['items']) is not list or not 1<=len(value['items'])<=16):
        raise ValueError('batch requires1..16 named independent DAGs')
    names=set()
    for item in value['items']:
        if type(item) is not dict or set(item)!={'name','dag'} or type(item['name']) is not str:
            raise ValueError('invalid batch item')
        p.name(item['name'])
        if item['name'] in names:raise ValueError('duplicate batch name')
        names.add(item['name']);d.validate(item['dag'])
    return value


def _input(root,name):
    raw=NativeWorkspace(root).read_text(f._filename(name),maximum=INPUT_LIMIT).encode()
    return raw,validate(loads(raw))


def preview(batch):
    validate(batch)
    return dict(evidence_class='static-admission',independent_sessions=len(batch['items']),
                jobs=sum(len(item['dag']['jobs']) for item in batch['items']),
                items=[dict(name=item['name'],**d.preview(item['dag'])) for item in batch['items']])


def check(project,input_file):
    raw,batch=_input(project.root/'inputs',input_file)
    return dict(schema='raveil.dag-batch-preview/v1',input_file=input_file,input_sha256=p.digest(raw),**preview(batch))


def _inventory(root):
    return p.tree(root,max_bytes=MAX_BYTES,max_entries=MAX_ENTRIES,
                  exclude_root_files=frozenset({'record.json','record.sha256','.record.pending'}))


def _complete(child):
    return (child['processed']==child['planned'] and child['halted']==0 and
            a._typed_output(child['output']) and child['output']['available'] and
            all(row['result']['approved'] is True for row in child['jobs']))


def _plan(root,run_id,input_file,raw,batch,kernel_sha,build_sha):
    return dict(schema=PLAN,id=run_id,input_file=input_file,input_sha256=p.digest(raw),
                kernel_sha256=kernel_sha,build_sha256=build_sha,preview=preview(batch))


def _entry(root,index,item,child):
    return dict(index=index,name=item['name'],receipt_sha256=p.digest(f._bytes(root,'receipt.json')),
                status='succeeded' if _complete(child) else 'incomplete',processed=child['processed'],
                planned=child['planned'],halted=child['halted'])


def _output(item,child):
    job=next(j for j in item['dag']['jobs'] if j['name']==item['dag']['output'])
    return dict(name=item['name'],output_name=child['output']['name'],shape=job['region']['shape'],words=child['output']['output'])


def _inspect(root,record):
    if (type(record) is not dict or set(record)!={'schema','id','status','evidence_class','attempted','planned','children','outputs','files'} or
        record['schema']!=SCHEMA or record['id']!=root.name or record['evidence_class']!=CLASS or
        type(record['children']) is not list or not 1<=len(record['children'])<=16 or
        not same(record['files'],_inventory(root))):raise ValueError('invalid batch record/inventory')
    raw,batch=_input(root,'input.json');plan=loads(f._bytes(root,'plan.json'))
    if type(plan) is not dict or type(plan.get('input_file')) is not str:raise ValueError('invalid batch plan')
    filename=f._filename(plan['input_file']);kernel_sha=p.digest(f._bytes(root,'kernel.elf'))
    build_sha=f.verify_build(root/'runtime')
    if not same(plan,_plan(root,root.name,filename,raw,batch,kernel_sha,build_sha)):
        raise ValueError('batch snapshot/plan differs')
    count=len(record['children']);items=batch['items']
    if count>len(items) or NativeWorkspace(root/'children').ls('/')!=[f'{i:02d}' for i in range(count)]:
        raise ValueError('children must be exact declared prefix')
    expected=[];outputs=[];complete=True
    for i,item in enumerate(items[:count]):
        child_root=root/'children'/f'{i:02d}'
        child=d.verify(child_root)
        if (not same(loads(f._bytes(child_root,'session.json')),item['dag']) or
            p.digest(f._bytes(child_root,'kernel.elf'))!=kernel_sha or
            loads(f._bytes(child_root,'plan.json'))['build_sha256']!=build_sha):
            raise ValueError('child differs from captured batch')
        entry=_entry(child_root,i,item,child);expected.append(entry)
        if not _complete(child):
            if i!=count-1:raise ValueError('child executed after incomplete predecessor')
            complete=False
        else:outputs.append(_output(item,child))
    if complete and count!=len(items):raise ValueError('batch ended before all independent children')
    if (not same(record['children'],expected) or not same(record['attempted'],count) or
        not same(record['planned'],len(items)) or record['status']!=('succeeded' if complete else 'incomplete') or
        not same(record['outputs'],outputs if complete else None)):
        raise ValueError('batch result/prefix differs')
    return record


def run(project,input_file,kernel,build):
    # Admit EVERY child and freeze common sources before the first execution.
    raw,batch=_input(project.root/'inputs',input_file)
    kernel=Path(kernel).absolute();kernel_bytes=f._bytes(kernel.parent,kernel.name)
    build=Path(build).absolute();identity=f.verify_build(build,current=True)
    run_id=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ-')+uuid4().hex[:12]
    if 'batches' not in project.workspace.ls('/'):project.workspace.mkdir('batches',mode=0o700)
    project.workspace.mkdir('batches/'+run_id,mode=0o700);root=project.root/'batches'/run_id
    p.write_new(root/'input.json',raw);p.write_new(root/'kernel.elf',kernel_bytes)
    p.tree(build,root/'runtime');(root/'runtime/simulator.bin').chmod(0o700)
    if f.verify_build(root/'runtime',current=True)!=identity:raise ValueError('runtime changed during capture')
    plan=_plan(root,run_id,input_file,raw,batch,p.digest(kernel_bytes),identity)
    p.write_new(root/'plan.json',p.encoded(plan));(root/'children').mkdir(mode=0o700)
    children=[];outputs=[];complete=True
    for i,item in enumerate(batch['items']):
        child_root=root/'children'/f'{i:02d}'
        # Exceptions, interrupts and uncertain cleanup leave the parent unsealed.
        d.run(item['dag'],root/'kernel.elf',root/'runtime',child_root)
        child=d.verify(child_root);children.append(_entry(child_root,i,item,child))
        if not _complete(child):complete=False;break
        outputs.append(_output(item,child))
    record=dict(schema=SCHEMA,id=run_id,status='succeeded' if complete else 'incomplete',evidence_class=CLASS,
                attempted=len(children),planned=len(batch['items']),children=children,
                outputs=outputs if complete else None,files=_inventory(root))
    _inspect(root,record);payload=p.encoded(record)
    try:
        p.write_new(root/'.record.pending',payload);p.write_new(root/'record.sha256',(p.digest(payload)+'\n').encode())
        os.link(root/'.record.pending',root/'record.json');(root/'.record.pending').unlink()
    except KeyboardInterrupt:
        if not (root/'record.json').exists():raise
    return load(project,run_id)


def load(project,run_id):
    if type(run_id) is not str:raise ValueError('batch id must be text')
    root=project.root/'batches'/p.name(run_id);raw=f._bytes(root,'record.json')
    if p.digest(raw)!=f._bytes(root,'record.sha256').decode().strip():raise ValueError('batch record hash differs')
    return _inspect(root,loads(raw))


def history(project):
    if 'batches' not in project.workspace.ls('/'):return []
    rows=[]
    for run_id in project.workspace.ls('batches'):
        p.name(run_id);names=NativeWorkspace(project.root/'batches'/run_id).ls('/')
        if 'record.json' not in names:rows.append(dict(id=run_id,status='unsealed'));continue
        record=load(project,run_id);rows.append(dict(id=run_id,status=record['status'],attempted=record['attempted'],planned=record['planned']))
    return rows


def compare(project,first,second):
    records=[load(project,i) for i in (first,second)]
    if any(r['status']!='succeeded' for r in records):raise ValueError('comparison requires complete batches')
    plans=[loads(f._bytes(project.root/'batches'/r['id'],'plan.json')) for r in records]
    if any(plans[0][key]!=plans[1][key] for key in ('kernel_sha256','build_sha256')):
        raise ValueError('comparison requires same executables')
    a,b=(r['outputs'] for r in records)
    if not same([{k:o[k] for k in ('name','output_name','shape')} for o in a],
                [{k:o[k] for k in ('name','output_name','shape')} for o in b]):
        raise ValueError('comparison requires same named output layout')
    rows=[]
    for old,new in zip(a,b):
        changes=[i for i,(x,y) in enumerate(zip(old['words'],new['words'])) if x!=y]
        rows.append(dict(name=old['name'],shape=old['shape'],changed_cells=len(changes),
            first_change=dict(index=changes[0],before=old['words'][changes[0]],after=new['words'][changes[0]]) if changes else None))
    return dict(first=first,second=second,evidence_class='saved-functional-comparison',items=rows,
                changed_cells=sum(row['changed_cells'] for row in rows),input_changed=plans[0]['input_sha256']!=plans[1]['input_sha256'])
