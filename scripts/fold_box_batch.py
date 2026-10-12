"""Owned box-sum workload lowered to independent MF01 DAG tiles.

The scalar full-grid oracle below does not use the MF01 interpreter.
"""
from scripts.affine_fold_vectors import region,load
from scripts.fold_dag_cases import graph
from raveil.project_dag_batch import validate,INPUT


def full_reference(words,rows,columns):
    return [sum(words[rr*columns+cc] for rr in range(r-1,r+2) for cc in range(c-1,c+2)
                if 0<=rr<rows and 0<=cc<columns)&0xffffffff for r in range(rows) for c in range(columns)]


def lower(words,rows,columns,tile=8):
    if (type(rows) is not int or type(columns) is not int or not 1<=rows<=64 or not 1<=columns<=64 or
        type(tile) is not int or not 1<=tile<=16 or type(words) is not list or len(words)!=rows*columns or
        any(type(w) is not int or not 0<=w<2**32 for w in words)):raise ValueError('invalid box workload')
    items=[];layout=[]
    for row in range(0,rows,tile):
        for col in range(0,columns,tile):
            height=min(tile,rows-row);width=min(tile,columns-col);stride=width+2
            halo=[words[r*columns+c] if 0<=r<rows and 0<=c<columns else 0
                  for r in range(row-1,row+height+1) for c in range(col-1,col+width+1)]
            views={f'r{i}':[0,i*stride,stride,1,1] for i in range(3)}
            nodes=[load(f'r{i}',f'r{i}') for i in range(3)]+[dict(id='ab',op='add',args=['r0','r1']),dict(id='sum',op='add',args=['ab','r2'])]
            desc=region([height,width],3,[len(halo),0],views,nodes,'sum')
            name=f'tile-{len(items):02d}';items.append(dict(name=name,dag=graph([dict(name='box',region=desc,inputs=[halo,[]])])))
            layout.append(dict(name=name,row=row,column=col,rows=height,columns=width))
    return validate(dict(schema=INPUT,items=items)),layout


from raveil.grid_assembly import assemble
