"""Automatically partitioned array captures; revalidated children and atomic outputs."""
from datetime import datetime,timezone
import os
from pathlib import Path
from uuid import uuid4
from . import project as p,project_fold as f,project_dag_batch as b,project_mf01_grid as a,array_program as array
from .fold_evidence import loads,same
from .workspace import NativeWorkspace

SCHEMA='raveil.project-array-program/v1'
PLAN='raveil.project-array-program-plan/v1'
CLASS='host-composed-QEMU-RTL-array-program-functional'


def _input(root,name):
    raw=NativeWorkspace(root).read_text(f._filename(name),maximum=b.INPUT_LIMIT).encode();value=loads(raw)
    return raw,value,array.compile(value)


def check(project,input_file):
    raw,value,compiled=_input(project.root/'inputs',input_file)
    return dict(schema='raveil.array-program-preview/v1',evidence_class='static-admission',source_sha256=p.digest(raw),**compiled)


def _capture_budget(raw,compiled,kernel_bytes,build):
    """Known duplicated captures plus reservation, not a future-log guarantee."""
    manifest=p.tree(build);workspace=NativeWorkspace(build)
    runtime=sum(workspace.stat(path).size for path,kind in manifest.items() if kind!='directory')
    passes=len(compiled['passes']);sessions=compiled['sessions']
    known=len(raw)+(1+passes+sessions)*runtime+(1+passes+sessions)*len(kernel_bytes)
    reservation=65536*passes+131072*sessions
    if known+reservation>b.MAX_BYTES or (1+passes+sessions)*len(manifest)+64*passes+32*sessions>b.MAX_ENTRIES:
        raise ValueError('array capture reservation exceeds inventory budget')
    return dict(known_bytes=known,reserved_bytes=reservation)


def _plan(identity,input_file,raw,compiled,kernel_sha,build_sha):
    return dict(schema=PLAN,id=identity,input_file=input_file,source_sha256=p.digest(raw),preview=compiled,
                kernel_sha256=kernel_sha,build_sha256=build_sha)


def _entry(index,name,root,child):
    return dict(index=index,name=name,id=child['id'],status=child['status'],record_sha256=p.digest(f._bytes(root,'record.json')))


def _bound_child(project,identity,source,kernel_sha,build_sha):
    identity=p.name(identity)
    if project.workspace.ls('grids')!=[identity]:raise ValueError('array requires one grid per stage')
    child=a.load(project,identity);child_root=project.root/'grids'/identity
    if f._bytes(child_root,'source.json')!=p.encoded(source):raise ValueError('array child source differs from producer binding')
    child_plan=loads(f._bytes(child_root/'child/batches'/child['batch_id'],'plan.json'))
    if child_plan['kernel_sha256']!=kernel_sha or child_plan['build_sha256']!=build_sha:
        raise ValueError('array child executables differ')
    return child,child_root


def _inspect(root,record):
    if (type(record) is not dict or set(record)!={'schema','id','evidence_class','status','children','outputs','files'} or
        record['schema']!=SCHEMA or record['id']!=root.name or record['evidence_class']!=CLASS or
        type(record['children']) is not list or not 1<=len(record['children'])<=array.MAX_PASSES or
        not same(record['files'],b._inventory(root))):raise ValueError('invalid array record/inventory')
    raw,value,compiled=_input(root,'source.json');plan=loads(f._bytes(root,'plan.json'))
    if type(plan) is not dict or type(plan.get('input_file')) is not str:raise ValueError('invalid array plan')
    kernel_sha=p.digest(f._bytes(root,'kernel.elf'));build_sha=f.verify_build(root/'runtime')
    _capture_budget(raw,compiled,f._bytes(root,'kernel.elf'),root/'runtime')
    if not same(plan,_plan(root.name,f._filename(plan['input_file']),raw,compiled,kernel_sha,build_sha)):
        raise ValueError('array source/plan/executables differ')
    count=len(record['children']);steps=compiled['passes']
    if count>len(steps) or NativeWorkspace(root/'children').ls('/')!=[f'{i:03d}' for i in range(count)]:
        raise ValueError('array children must be exact scheduled prefix')
    planes={};entries=[];complete=True
    for i,step in enumerate(steps[:count]):
        entry=record['children'][i]
        if type(entry) is not dict or type(entry.get('id')) is not str:raise ValueError('invalid array child')
        project=p.Project(root/'children'/f'{i:03d}')
        source=array.bind(value,step,planes)
        child,child_root=_bound_child(project,entry['id'],source,kernel_sha,build_sha)
        entries.append(_entry(i,step['id'],child_root,child))
        if child['status']!='succeeded':
            if i!=count-1:raise ValueError('array continued after incomplete pass')
            complete=False
        else:array.commit(planes,step,child['output'])
    if complete and count!=len(steps):raise ValueError('array ended before scheduled passes')
    expected=array.publish(compiled,planes) if complete else None
    if complete and not same(expected,array.reference(value)):raise ValueError('whole-array oracle mismatch')
    if (not same(record['children'],entries) or record['status']!=('succeeded' if complete else 'incomplete') or
        not same(record['outputs'],expected)):raise ValueError('array results/prefix differ')
    return record


def run(project,input_file,kernel,build):
    # Shape/program/resource admission for every stage precedes any attempt.
    raw,value,compiled=_input(project.root/'inputs',input_file)
    kernel=Path(kernel).absolute();kernel_bytes=f._bytes(kernel.parent,kernel.name)
    build=Path(build).absolute();build_sha=f.verify_build(build,current=True)
    _capture_budget(raw,compiled,kernel_bytes,build)
    identity=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ-')+uuid4().hex[:12]
    if 'arrays' not in project.workspace.ls('/'):project.workspace.mkdir('arrays',mode=0o700)
    project.workspace.mkdir('arrays/'+identity,mode=0o700);root=project.root/'arrays'/identity
    p.write_new(root/'source.json',raw);p.write_new(root/'kernel.elf',kernel_bytes);p.tree(build,root/'runtime')
    (root/'runtime/simulator.bin').chmod(0o700)
    if f.verify_build(root/'runtime',current=True)!=build_sha:raise ValueError('array runtime changed during capture')
    p.write_new(root/'plan.json',p.encoded(_plan(identity,input_file,raw,compiled,p.digest(kernel_bytes),build_sha)))
    (root/'children').mkdir(mode=0o700);planes={};children=[];complete=True
    for i,step in enumerate(compiled['passes']):
        child_project=p.Project(p.init_project(root/'children'/f'{i:03d}'))
        source=array.bind(value,step,planes)
        p.write_new(child_project.root/'inputs/array-pass.json',p.encoded(source))
        child=a.run(child_project,'array-pass.json',root/'kernel.elf',root/'runtime')
        # A return value grants no authority; reload the captured child proof.
        child,child_root=_bound_child(child_project,child['id'],source,p.digest(kernel_bytes),build_sha)
        children.append(_entry(i,step['id'],child_root,child))
        b._inventory(root)  # Failure leaves the attempt unsealed, never partial success.
        if child['status']!='succeeded':complete=False;break
        array.commit(planes,step,child['output'])
    record=dict(schema=SCHEMA,id=identity,evidence_class=CLASS,status='succeeded' if complete else 'incomplete',children=children,
                outputs=array.publish(compiled,planes) if complete else None,files=b._inventory(root))
    _inspect(root,record);payload=p.encoded(record)
    try:
        p.write_new(root/'.record.pending',payload);p.write_new(root/'record.sha256',(p.digest(payload)+'\n').encode())
        os.link(root/'.record.pending',root/'record.json');(root/'.record.pending').unlink()
    except KeyboardInterrupt:
        if not (root/'record.json').exists():raise
    return load(project,identity)


def load(project,identity):
    if type(identity) is not str:raise ValueError('array id must be text')
    root=project.root/'arrays'/p.name(identity);raw=f._bytes(root,'record.json')
    if p.digest(raw)!=f._bytes(root,'record.sha256').decode().strip():raise ValueError('array record hash differs')
    return _inspect(root,loads(raw))


def history(project):
    if 'arrays' not in project.workspace.ls('/'):return []
    rows=[]
    for identity in project.workspace.ls('arrays'):
        p.name(identity);names=NativeWorkspace(project.root/'arrays'/identity).ls('/')
        if 'record.json' not in names:rows.append(dict(id=identity,status='unsealed'));continue
        r=load(project,identity);rows.append(dict(id=identity,status=r['status'],attempted=len(r['children'])))
    return rows


def compare(project,first,second):
    records=[load(project,i) for i in (first,second)]
    if any(r['status']!='succeeded' for r in records):raise ValueError('comparison requires complete arrays')
    plans=[loads(f._bytes(project.root/'arrays'/r['id'],'plan.json')) for r in records]
    if any(plans[0][key]!=plans[1][key] for key in ('kernel_sha256','build_sha256')):raise ValueError('array comparison requires same executables')
    old,new=[r['outputs'] for r in records]
    if not same([{k:o[k] for k in ('name','rows','columns')} for o in old],[{k:o[k] for k in ('name','rows','columns')} for o in new]):
        raise ValueError('array comparison requires same named output layout')
    items=[]
    for a,z in zip(old,new):
        changes=[i for i,(x,y) in enumerate(zip(a['words'],z['words'])) if x!=y]
        items.append(dict(name=a['name'],changed_cells=len(changes),first_index=changes[0] if changes else None))
    return dict(first=first,second=second,evidence_class='saved-functional-comparison',items=items,changed_cells=sum(x['changed_cells'] for x in items))
