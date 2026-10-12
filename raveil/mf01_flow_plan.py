"""Separable finite tile advice for whole-grid source flows; never execution authority."""
import copy
from . import mf01_flow as flow,mf01_grid_plan as tiles,mf01_grid as grid
from . import project as p,project_fold as f,project_dag_batch as b
from .fold_evidence import loads
from .workspace import NativeWorkspace

SCHEMA='raveil.mf01-flow-tile-proposal/v1'


def plan(value):
    stages,dependencies,order=flow.structure(value)
    selected=copy.deepcopy(value);by_name={stage['name']:stage for stage in selected['stages']}
    placeholders={};rows=[]
    for name in order:
        resolved=flow.materialize(stages[name],placeholders);proposal=tiles.plan(resolved)
        # Preserve every link, inline word, program and authoring-order choice.
        # The materialized zero-input source is only an admission probe.
        by_name[name]['source']['tile']=list(proposal['selected']['tile'])
        _,_,shape=grid.source(proposal['source']);r,c=shape
        placeholders[name]=dict(rows=r,columns=c,words=[0]*(r*c))
        rows.append(dict(name=name,requested_tile=proposal['requested_tile'],searched=proposal['searched'],
                         admitted=proposal['admitted'],**proposal['selected']))
    compiled=flow.compile(selected)
    return dict(schema=SCHEMA,evidence_class='host-admission-proposal',input_sha256=p.digest(p.encoded(value)),
                selected_sha256=p.digest(p.encoded(selected)),
                objective='total-sessions-then-initial-packed-words/v1',
                sessions=compiled['sessions'],jobs=compiled['jobs'],packed_input_words=sum(row['packed_input_words'] for row in rows),
                stages=rows,source=selected)


def propose(project,input_file,output_file=None):
    inputs=NativeWorkspace(project.root/'inputs')
    raw=inputs.read_text(f._filename(input_file),maximum=b.INPUT_LIMIT).encode()
    result=plan(loads(raw));result['input_sha256']=p.digest(raw);result['input_file']=input_file
    if output_file is not None:
        filename=f._filename(output_file);payload=p.encoded(result['source'])
        if len(payload)>b.INPUT_LIMIT:raise ValueError('selected flow exceeds input limit')
        _,root=inputs.existing_host_path('/');p.write_new(root/filename,payload);result['output_file']=filename
    return result
