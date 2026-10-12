"""Frozen grid-source DAGs, dependent child captures and all-output publication."""
from datetime import datetime,timezone
import os
from pathlib import Path
from uuid import uuid4
from . import project as p,project_fold as f,project_dag_batch as b,project_mf01_grid as a,mf01_flow as flow
from .fold_evidence import loads,same
from .workspace import NativeWorkspace

SCHEMA='raveil.project-mf01-flow/v1'
PLAN='raveil.project-mf01-flow-plan/v1'
CLASS='host-composed-QEMU-RTL-grid-flow-functional'


def _input(root,name):
    raw=NativeWorkspace(root).read_text(f._filename(name),maximum=b.INPUT_LIMIT).encode();value=loads(raw)
    return raw,value,flow.compile(value)


def check(project,input_file):
    raw,value,compiled=_input(project.root/'inputs',input_file)
    return dict(schema='raveil.mf01-flow-preview/v1',evidence_class='static-admission',source_sha256=p.digest(raw),**compiled)


def _plan(identity,input_file,raw,compiled,kernel_sha,build_sha):
    return dict(schema=PLAN,id=identity,input_file=input_file,source_sha256=p.digest(raw),preview=compiled,
                kernel_sha256=kernel_sha,build_sha256=build_sha)


def _entry(index,name,root,child):
    return dict(index=index,name=name,id=child['id'],status=child['status'],record_sha256=p.digest(f._bytes(root,'record.json')))


def _bound_child(project,identity,source,kernel_sha,build_sha):
    identity=p.name(identity)
    if project.workspace.ls('grids')!=[identity]:raise ValueError('flow requires one grid per stage')
    child=a.load(project,identity);child_root=project.root/'grids'/identity
    if f._bytes(child_root,'source.json')!=p.encoded(source):raise ValueError('flow child source differs from producer binding')
    child_plan=loads(f._bytes(child_root/'child/batches'/child['batch_id'],'plan.json'))
    if child_plan['kernel_sha256']!=kernel_sha or child_plan['build_sha256']!=build_sha:
        raise ValueError('flow child executables differ')
    return child,child_root


def _inspect(root,record):
    if (type(record) is not dict or set(record)!={'schema','id','evidence_class','status','children','outputs','files'} or
        record['schema']!=SCHEMA or record['id']!=root.name or record['evidence_class']!=CLASS or
        type(record['children']) is not list or not 1<=len(record['children'])<=8 or
        not same(record['files'],b._inventory(root))):raise ValueError('invalid flow record/inventory')
    raw,value,compiled=_input(root,'source.json');plan=loads(f._bytes(root,'plan.json'))
    if type(plan) is not dict or type(plan.get('input_file')) is not str:raise ValueError('invalid flow plan')
    kernel_sha=p.digest(f._bytes(root,'kernel.elf'));build_sha=f.verify_build(root/'runtime')
    if not same(plan,_plan(root.name,f._filename(plan['input_file']),raw,compiled,kernel_sha,build_sha)):
        raise ValueError('flow source/plan/executables differ')
    count=len(record['children']);order=compiled['order']
    if count>len(order) or NativeWorkspace(root/'children').ls('/')!=[f'{i:02d}' for i in range(count)]:
        raise ValueError('flow children must be exact scheduled prefix')
    stages={s['name']:s['source'] for s in value['stages']};outputs={};entries=[];complete=True
    for i,name in enumerate(order[:count]):
        entry=record['children'][i]
        if type(entry) is not dict or type(entry.get('id')) is not str:raise ValueError('invalid flow child')
        project=p.Project(root/'children'/f'{i:02d}')
        source=flow.materialize(stages[name],outputs)
        child,child_root=_bound_child(project,entry['id'],source,kernel_sha,build_sha)
        entries.append(_entry(i,name,child_root,child))
        if child['status']!='succeeded':
            if i!=count-1:raise ValueError('flow continued after incomplete stage')
            complete=False
        else:outputs[name]=child['output']
    if complete and count!=len(order):raise ValueError('flow ended before scheduled stages')
    expected=[dict(name=name,**outputs[name]) for name in compiled['outputs']] if complete else None
    if (not same(record['children'],entries) or record['status']!=('succeeded' if complete else 'incomplete') or
        not same(record['outputs'],expected)):raise ValueError('flow results/prefix differ')
    return record


def run(project,input_file,kernel,build):
    # Shape/program/resource admission for every stage precedes any attempt.
    raw,value,compiled=_input(project.root/'inputs',input_file)
    kernel=Path(kernel).absolute();kernel_bytes=f._bytes(kernel.parent,kernel.name)
    build=Path(build).absolute();build_sha=f.verify_build(build,current=True)
    identity=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ-')+uuid4().hex[:12]
    if 'flows' not in project.workspace.ls('/'):project.workspace.mkdir('flows',mode=0o700)
    project.workspace.mkdir('flows/'+identity,mode=0o700);root=project.root/'flows'/identity
    p.write_new(root/'source.json',raw);p.write_new(root/'kernel.elf',kernel_bytes);p.tree(build,root/'runtime')
    (root/'runtime/simulator.bin').chmod(0o700)
    if f.verify_build(root/'runtime',current=True)!=build_sha:raise ValueError('flow runtime changed during capture')
    p.write_new(root/'plan.json',p.encoded(_plan(identity,input_file,raw,compiled,p.digest(kernel_bytes),build_sha)))
    (root/'children').mkdir(mode=0o700);stages={s['name']:s['source'] for s in value['stages']};outputs={};children=[];complete=True
    for i,name in enumerate(compiled['order']):
        child_project=p.Project(p.init_project(root/'children'/f'{i:02d}'))
        source=flow.materialize(stages[name],outputs)
        p.write_new(child_project.root/'inputs/flow-stage.json',p.encoded(source))
        child=a.run(child_project,'flow-stage.json',root/'kernel.elf',root/'runtime')
        # A return value is not evidence authority: reload captured child proof.
        child,child_root=_bound_child(child_project,child['id'],source,p.digest(kernel_bytes),build_sha)
        children.append(_entry(i,name,child_root,child))
        if child['status']!='succeeded':complete=False;break
        outputs[name]=child['output']
    record=dict(schema=SCHEMA,id=identity,evidence_class=CLASS,status='succeeded' if complete else 'incomplete',children=children,
                outputs=[dict(name=name,**outputs[name]) for name in compiled['outputs']] if complete else None,files=b._inventory(root))
    _inspect(root,record);payload=p.encoded(record)
    try:
        p.write_new(root/'.record.pending',payload);p.write_new(root/'record.sha256',(p.digest(payload)+'\n').encode())
        os.link(root/'.record.pending',root/'record.json');(root/'.record.pending').unlink()
    except KeyboardInterrupt:
        if not (root/'record.json').exists():raise
    return load(project,identity)


def load(project,identity):
    if type(identity) is not str:raise ValueError('flow id must be text')
    root=project.root/'flows'/p.name(identity);raw=f._bytes(root,'record.json')
    if p.digest(raw)!=f._bytes(root,'record.sha256').decode().strip():raise ValueError('flow record hash differs')
    return _inspect(root,loads(raw))


def history(project):
    if 'flows' not in project.workspace.ls('/'):return []
    rows=[]
    for identity in project.workspace.ls('flows'):
        p.name(identity);names=NativeWorkspace(project.root/'flows'/identity).ls('/')
        if 'record.json' not in names:rows.append(dict(id=identity,status='unsealed'));continue
        r=load(project,identity);rows.append(dict(id=identity,status=r['status'],attempted=len(r['children'])))
    return rows


def compare(project,first,second):
    records=[load(project,i) for i in (first,second)]
    if any(r['status']!='succeeded' for r in records):raise ValueError('comparison requires complete flows')
    plans=[loads(f._bytes(project.root/'flows'/r['id'],'plan.json')) for r in records]
    if any(plans[0][key]!=plans[1][key] for key in ('kernel_sha256','build_sha256')):raise ValueError('flow comparison requires same executables')
    old,new=[r['outputs'] for r in records]
    if not same([{k:o[k] for k in ('name','rows','columns')} for o in old],[{k:o[k] for k in ('name','rows','columns')} for o in new]):
        raise ValueError('flow comparison requires same named output layout')
    items=[]
    for a,z in zip(old,new):
        changes=[i for i,(x,y) in enumerate(zip(a['words'],z['words'])) if x!=y]
        items.append(dict(name=a['name'],changed_cells=len(changes),first_index=changes[0] if changes else None))
    return dict(first=first,second=second,evidence_class='saved-functional-comparison',items=items,changed_cells=sum(x['changed_cells'] for x in items))
