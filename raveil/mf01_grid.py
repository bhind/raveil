"""Bounded neighborhood/fold source lowering into existing independent DAGs."""
import copy
from . import grid_kernel as g,project as p,fold_dag as d
from .affine_fold import compile_region,MASK
from .mf01_numeric import lower as lower_numeric

SCHEMA='raveil.mf01-grid/v1'
SCHEMA_V2='raveil.mf01-grid/v2'
SCHEMA_V3='raveil.mf01-grid/v3'
SCHEMA_V4='raveil.mf01-grid/v4'
SCHEMA_V5='raveil.mf01-grid/v5'


def integer(value,low,high):
    if type(value) is not int or not low<=value<=high:raise ValueError(f'expected integer {low}..{high}')
    return value


def source(value):
    if type(value) is not dict or value.get('schema') not in (SCHEMA,SCHEMA_V2,SCHEMA_V3,SCHEMA_V4,SCHEMA_V5):
        raise ValueError('invalid MF01 grid source')
    v2=value['schema']!=SCHEMA;v3=value['schema']==SCHEMA_V3 or (value['schema'] in (SCHEMA_V4,SCHEMA_V5) and 'post' in value)
    fields={'schema','inputs','tile','boundary','kernel'}|({'shape'} if v2 else set())|({'post'} if v3 else set())
    if set(value)!=fields:
        raise ValueError('invalid MF01 grid source fields')
    if v3 and (type(value['post']) is not dict or set(value['post'])!={'nodes','result'}):raise ValueError('invalid post map')
    if type(value['inputs']) is not list or not 1<=len(value['inputs'])<=2:raise ValueError('one or two grids required')
    grids=[g.read_input(p.encoded(grid)) for grid in value['inputs']]
    if not v2 and any((grid['rows'],grid['columns'])!=(grids[0]['rows'],grids[0]['columns']) for grid in grids):raise ValueError('grid dimensions must agree')
    shape=value['shape'] if v2 else [grids[0]['rows'],grids[0]['columns']]
    if type(shape) is not list or len(shape)!=2:raise ValueError('two output dimensions required')
    for extent in shape:integer(extent,1,64)
    tile=value['tile']
    if type(tile) is not list or len(tile)!=2:raise ValueError('two tile dimensions required')
    for extent in tile:integer(extent,1,16)
    if ((shape[0]+tile[0]-1)//tile[0])*((shape[1]+tile[1]-1)//tile[1])>16:
        raise ValueError('grid needs more than sixteen independent tiles')
    g.boundary(value['boundary']);kernel=value['kernel']
    if type(kernel) is not dict or set(kernel)!={'extent','fold','views','nodes','result'}:raise ValueError('invalid grid kernel')
    integer(kernel['extent'],1,64)
    if type(kernel['fold']) is not str or kernel['fold'] not in ('sum','max'):raise ValueError('invalid fold')
    if type(kernel['views']) is not dict or not 1<=len(kernel['views'])<=8:raise ValueError('one to eight named views required')
    for name,view in kernel['views'].items():
        fields={'input','offset','step','row','column'} if v2 else {'input','offset','step'}
        if type(name) is not str or not name or type(view) is not dict or set(view)!=fields:raise ValueError('invalid grid view')
        integer(view['input'],0,len(grids)-1)
        for key,low in [('offset',-63),('step',0)]+([('row',0),('column',0)] if v2 else []):
            pair=view[key]
            if type(pair) is not list or len(pair)!=2:raise ValueError('view needs two coordinates')
            for item in pair:integer(item,low,63)
    kernel=copy.deepcopy(kernel)
    if not v2:
        for view in kernel['views'].values():view.update(row=[1,0],column=[0,1])
    return grids,kernel,shape


def compile(value):
    grids,kernel,(rows,columns)=source(value);tr,tc=value['tile'];items=[];layout=[]
    nodes=lower_numeric(kernel['nodes'],kernel['result'],share_transforms=value['schema']==SCHEMA_V5) if value['schema'] in (SCHEMA_V4,SCHEMA_V5) else kernel['nodes']
    post_nodes=None
    if 'post' in value:
        post_nodes=lower_numeric(value['post']['nodes'],value['post']['result'],share_transforms=value['schema']==SCHEMA_V5) if value['schema'] in (SCHEMA_V4,SCHEMA_V5) else value['post']['nodes']
    for row in range(0,rows,tr):
        for col in range(0,columns,tc):
            height,width=min(tr,rows-row),min(tc,columns-col);buffers=[];rectangles=[]
            origins={name:[v['offset'][axis]+row*v['row'][axis]+col*v['column'][axis] for axis in range(2)] for name,v in kernel['views'].items()}
            for index in range(2):
                views=[(name,v) for name,v in kernel['views'].items() if v['input']==index]
                if not views:buffers.append([]);rectangles.append(None);continue
                low=[min(origins[name][axis] for name,v in views) for axis in range(2)]
                high=[max(origins[name][axis]+(height-1)*v['row'][axis]+(width-1)*v['column'][axis]+(kernel['extent']-1)*v['step'][axis] for name,v in views) for axis in range(2)]
                rmin,cmin=low;h=high[0]-rmin+1;w=high[1]-cmin+1
                if h*w>324:raise ValueError('tile input rectangle exceeds324 words')
                buffers.append([g.sample(grids[index],rmin+r,cmin+c,value['boundary']) for r in range(h) for c in range(w)])
                rectangles.append((rmin,cmin,w))
            views={}
            for name,v in kernel['views'].items():
                rmin,cmin,stride=rectangles[v['input']]
                views[name]=[v['input'],(origins[name][0]-rmin)*stride+origins[name][1]-cmin,
                             v['row'][0]*stride+v['row'][1] if height>1 else 0,
                             v['column'][0]*stride+v['column'][1] if width>1 else 0,
                             v['step'][0]*stride+v['step'][1] if kernel['extent']>1 else 0]
            region=dict(schema='raveil.affine-fold.v1',shape=[height,width],extent=kernel['extent'],fold=kernel['fold'],
                        lengths=[len(b) for b in buffers],views=views,nodes=copy.deepcopy(nodes),result=kernel['result'])
            try:compile_region(region)
            except (TypeError,KeyError,IndexError,AttributeError) as exc:raise ValueError('malformed MF01 map program') from exc
            name=f'tile-{len(items):02d}'
            jobs=[dict(name='result',region=region,inputs=buffers)]
            if 'post' in value:
                jobs[0]['name']='reduce'
                post=dict(schema='raveil.affine-fold.v1',shape=[height,width],extent=1,fold='sum',lengths=[height*width,0],
                          views={'reduced':[0,0,width if height>1 else 0,1 if width>1 else 0,0]},
                          nodes=copy.deepcopy(post_nodes),result=value['post']['result'])
                try:compile_region(post)
                except (TypeError,KeyError,IndexError,AttributeError) as exc:raise ValueError('malformed post map') from exc
                jobs.append(dict(name='result',region=post,inputs=[{'from':'reduce'},[]]))
            dag=dict(schema='raveil.fold-dag.v1',jobs=jobs,output='result');d.validate(dag)
            items.append(dict(name=name,dag=dag));layout.append(dict(name=name,row=row,column=col,rows=height,columns=width))
    return dict(batch=dict(schema='raveil.dag-batch.v1',items=items),layout=layout,rows=rows,columns=columns)


def reference(value):
    """Untiled global-coordinate oracle; no halo buffers or encoded instructions."""
    compile(value)  # Admission only. The calculation below does not consume lowering.
    grids,kernel,(rows,columns)=source(value);result=[]
    for row in range(rows):
        for col in range(columns):
            acc=0
            for k in range(kernel['extent']):
                values={}
                for node in kernel['nodes']:
                    op=node['op'];args=[values[x] for x in node.get('args',[])]
                    if op=='load':
                        view=kernel['views'][node['view']];grid=grids[view['input']]
                        r=view['offset'][0]+row*view['row'][0]+col*view['column'][0]+k*view['step'][0]
                        c=view['offset'][1]+row*view['row'][1]+col*view['column'][1]+k*view['step'][1]
                        input_rows,input_columns=grid['rows'],grid['columns']
                        if value['boundary']=='zero' and not(0<=r<input_rows and 0<=c<input_columns):word=0
                        else:
                            if value['boundary']=='clamp':r,c=max(0,min(r,input_rows-1)),max(0,min(c,input_columns-1))
                            elif value['boundary']=='wrap':r,c=r%input_rows,c%input_columns
                            word=grid['words'][r*input_columns+c]
                    elif op=='add':word=args[0]+args[1]
                    elif op=='mul':word=args[0]*args[1]
                    elif op=='max':word=max(args)
                    elif op=='max_i32':word=max(x if x<(1<<31) else x-(1<<32) for x in args)
                    elif op=='relu_i32':word=max(0,args[0] if args[0]<(1<<31) else args[0]-(1<<32))
                    elif op=='add_imm':word=args[0]+node['imm']
                    else:word=int(args[0]>=node['imm'])
                    values[node['id']]=word&MASK
                value_at=values[kernel['result']];acc=(acc+value_at)&MASK if kernel['fold']=='sum' else max(acc,value_at)
            if 'post' in value:
                post_values={}
                for node in value['post']['nodes']:
                    op=node['op'];args=[post_values[x] for x in node.get('args',[])]
                    if op=='load':word=acc
                    elif op=='add':word=args[0]+args[1]
                    elif op=='mul':word=args[0]*args[1]
                    elif op=='max':word=max(args)
                    elif op=='max_i32':word=max(x if x<(1<<31) else x-(1<<32) for x in args)
                    elif op=='relu_i32':word=max(0,args[0] if args[0]<(1<<31) else args[0]-(1<<32))
                    elif op=='add_imm':word=args[0]+node['imm']
                    else:word=int(args[0]>=node['imm'])
                    post_values[node['id']]=word&MASK
                acc=post_values[value['post']['result']]
            result.append(acc)
    return result
