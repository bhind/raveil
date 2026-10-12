"""Finite uniform-tile advice, always checked by the existing grid compiler."""
import copy
from . import mf01_grid as g,project as p,project_fold as f,project_dag_batch as b
from .fold_evidence import loads
from .workspace import NativeWorkspace

SCHEMA='raveil.mf01-grid-tile-proposal/v1'


def plan(value):
    if type(value) is not dict:raise ValueError('grid source must be an object')
    tile=value.get('tile')
    if type(tile) is not list or len(tile)!=2:raise ValueError('two requested tile dimensions required')
    for size in tile:g.integer(size,1,16)
    # The largest nominal tile fits the tile-count bound for any valid shape.
    # This checks the source schema independently of the requested partition.
    g.source({**value,'tile':[16,16]})
    best=None;admitted=0;rejections={}
    for rows in range(1,17):
        for columns in range(1,17):
            candidate={**value,'tile':[rows,columns]}
            try:compiled=g.compile(candidate)
            except ValueError as error:
                reason=str(error);rejections[reason]=rejections.get(reason,0)+1;continue
            admitted+=1
            sessions=len(compiled['layout'])
            words=sum(sum(item['dag']['jobs'][0]['region']['lengths']) for item in compiled['batch']['items'])
            score=(sessions,words,rows*columns,rows,columns)
            if best is None or score<best[0]:best=(score,candidate)
    if best is None:raise ValueError('no admitted uniform tile among 256 candidates: '+ '; '.join(sorted(rejections)))
    score,selected=best;selected=copy.deepcopy(selected)
    return dict(schema=SCHEMA,evidence_class='host-admission-proposal',input_sha256=p.digest(p.encoded(value)),
                selected_sha256=p.digest(p.encoded(selected)),requested_tile=list(tile),searched=256,admitted=admitted,
                objective='sessions-then-packed-words-then-nominal-area/v1',
                selected=dict(tile=selected['tile'],sessions=score[0],packed_input_words=score[1]),
                rejected=dict(sorted(rejections.items())),source=selected)


def propose(project,input_file,output_file=None):
    inputs=NativeWorkspace(project.root/'inputs')
    raw=inputs.read_text(f._filename(input_file),maximum=b.INPUT_LIMIT).encode()
    result=plan(loads(raw));result['input_sha256']=p.digest(raw);result['input_file']=input_file
    if output_file is not None:
        filename=f._filename(output_file);payload=p.encoded(result['source'])
        if len(payload)>b.INPUT_LIMIT:raise ValueError('selected source exceeds input limit')
        _,root=inputs.existing_host_path('/')
        p.write_new(root/filename,payload)
        result['output_file']=filename
    return result
