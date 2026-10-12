"""Source-preserving grid compilation and saved assembly over DAG batches."""
from datetime import datetime,timezone
import os
from pathlib import Path
from uuid import uuid4
from . import project as p,project_fold as f,project_dag_batch as b,mf01_grid as grid
from .fold_evidence import loads,same
from .grid_assembly import assemble
from .workspace import NativeWorkspace

SCHEMA='raveil.project-mf01-grid/v1'
PLAN='raveil.project-mf01-grid-plan/v1'
CLASS='host-tiled-QEMU-RTL-grid-functional'


def _input(root,name):
    raw=NativeWorkspace(root).read_text(f._filename(name),maximum=b.INPUT_LIMIT).encode();value=loads(raw)
    return raw,value,grid.compile(value)


def _plan(identity,filename,raw,compiled):
    return dict(schema=PLAN,id=identity,input_file=filename,source_sha256=p.digest(raw),
                batch_sha256=p.digest(p.encoded(compiled['batch'])),layout=compiled['layout'],
                rows=compiled['rows'],columns=compiled['columns'])


def check(project,input_file):
    raw,value,compiled=_input(project.root/'inputs',input_file)
    return dict(schema='raveil.mf01-grid-preview/v1',source_sha256=p.digest(raw),rows=compiled['rows'],columns=compiled['columns'],
                layout=compiled['layout'],batch=b.preview(compiled['batch']))


def _inspect(root,record):
    if (type(record) is not dict or set(record)!={'schema','id','evidence_class','status','batch_id','child_sha256','output','files'} or
        record['schema']!=SCHEMA or record['id']!=root.name or record['evidence_class']!=CLASS or
        type(record['batch_id']) is not str or not same(record['files'],b._inventory(root))):raise ValueError('invalid grid record/inventory')
    raw,value,compiled=_input(root,'source.json');plan=loads(f._bytes(root,'plan.json'))
    if type(plan) is not dict or type(plan.get('input_file')) is not str:raise ValueError('invalid grid plan')
    if not same(plan,_plan(root.name,f._filename(plan['input_file']),raw,compiled)) or f._bytes(root,'lowered.json')!=p.encoded(compiled['batch']):
        raise ValueError('saved grid lowering/plan differs')
    child_project=p.Project(root/'child');child_id=p.name(record['batch_id'])
    if child_project.workspace.ls('batches')!=[child_id]:raise ValueError('grid requires exactly one captured batch')
    child=b.load(child_project,child_id);child_root=child_project.root/'batches'/child_id
    if (f._bytes(child_root,'input.json')!=p.encoded(compiled['batch']) or
        record['child_sha256']!=p.digest(f._bytes(child_root,'record.json'))):raise ValueError('captured batch differs from source lowering')
    output=None
    if child['status']=='succeeded':
        words=assemble(child['outputs'],compiled['layout'],compiled['rows'],compiled['columns'])
        if words!=grid.reference(value):raise ValueError('full-grid oracle differs from assembled execution')
        output=dict(rows=compiled['rows'],columns=compiled['columns'],words=words)
    if record['status']!=child['status'] or not same(record['output'],output):raise ValueError('grid output differs')
    return record


def run(project,input_file,kernel,build):
    raw,value,compiled=_input(project.root/'inputs',input_file)
    identity=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ-')+uuid4().hex[:12]
    if 'grids' not in project.workspace.ls('/'):project.workspace.mkdir('grids',mode=0o700)
    project.workspace.mkdir('grids/'+identity,mode=0o700);root=project.root/'grids'/identity
    p.write_new(root/'source.json',raw);p.write_new(root/'lowered.json',p.encoded(compiled['batch']))
    p.write_new(root/'plan.json',p.encoded(_plan(identity,input_file,raw,compiled)))
    child_project=p.Project(p.init_project(root/'child'));p.write_new(child_project.root/'inputs/grid-batch.json',p.encoded(compiled['batch']))
    child=b.run(child_project,'grid-batch.json',kernel,build);output=None
    if child['status']=='succeeded':
        words=assemble(child['outputs'],compiled['layout'],compiled['rows'],compiled['columns'])
        if words!=grid.reference(value):raise ValueError('full-grid oracle mismatch')
        output=dict(rows=compiled['rows'],columns=compiled['columns'],words=words)
    record=dict(schema=SCHEMA,id=identity,evidence_class=CLASS,status=child['status'],batch_id=child['id'],
                child_sha256=p.digest(f._bytes(child_project.root/'batches'/child['id'],'record.json')),
                output=output,files=b._inventory(root))
    _inspect(root,record);payload=p.encoded(record)
    try:
        p.write_new(root/'.record.pending',payload);p.write_new(root/'record.sha256',(p.digest(payload)+'\n').encode())
        os.link(root/'.record.pending',root/'record.json');(root/'.record.pending').unlink()
    except KeyboardInterrupt:
        if not (root/'record.json').exists():raise
    return load(project,identity)


def load(project,identity):
    if type(identity) is not str:raise ValueError('grid id must be text')
    root=project.root/'grids'/p.name(identity);raw=f._bytes(root,'record.json')
    if p.digest(raw)!=f._bytes(root,'record.sha256').decode().strip():raise ValueError('grid record hash differs')
    return _inspect(root,loads(raw))


def history(project):
    if 'grids' not in project.workspace.ls('/'):return []
    rows=[]
    for identity in project.workspace.ls('grids'):
        p.name(identity);names=NativeWorkspace(project.root/'grids'/identity).ls('/')
        if 'record.json' not in names:rows.append(dict(id=identity,status='unsealed'));continue
        r=load(project,identity);rows.append(dict(id=identity,status=r['status'],shape=[r['output']['rows'],r['output']['columns']] if r['output'] else None))
    return rows


def compare(project,first,second):
    records=[load(project,i) for i in (first,second)]
    if any(r['status']!='succeeded' for r in records):raise ValueError('comparison requires complete grids')
    plans=[loads(f._bytes(project.root/'grids'/r['id']/'child/batches'/r['batch_id'],'plan.json')) for r in records]
    a,z=[r['output'] for r in records]
    if [a['rows'],a['columns']]!=[z['rows'],z['columns']] or any(plans[0][k]!=plans[1][k] for k in ('kernel_sha256','build_sha256')):
        raise ValueError('grid comparison needs same shape and executables')
    changes=[i for i,(x,y) in enumerate(zip(a['words'],z['words'])) if x!=y]
    return dict(first=first,second=second,evidence_class='saved-functional-comparison',rows=a['rows'],columns=a['columns'],changed_cells=len(changes),
                first_change=dict(row=changes[0]//a['columns'],column=changes[0]%a['columns'],before=a['words'][changes[0]],after=z['words'][changes[0]]) if changes else None)
