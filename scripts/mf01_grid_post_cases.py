"""Owned post-reduction programs and direct arithmetic expectations."""
import copy
from raveil.mf01_grid import SCHEMA,SCHEMA_V3
from scripts.mf01_grid_affine_cases import matmul
from scripts.mf01_grid_cases import make,cases as old_cases


def with_post(value,nodes=None,result='biased'):
    value=copy.deepcopy(value)
    if value['schema']==SCHEMA:
        value['shape']=[value['inputs'][0]['rows'],value['inputs'][0]['columns']]
        for v in value['kernel']['views'].values():v.update(row=[1,0],column=[0,1])
    value['schema']=SCHEMA_V3
    value['post']=dict(nodes=nodes or [dict(id='x',op='load',view='reduced'),dict(id='biased',op='add_imm',args=['x'],imm=7)],result=result)
    return value


def cases():
    value,expected=matmul(17,19,9);yield 'matmul-bias',with_post(value),[(v+7)&0xffffffff for v in expected]
    value,_=matmul(3,5,4,(2,3))
    for grid in value['inputs']:grid['words']=[i%9 for i in range(len(grid['words']))]
    a,b=[x['words'] for x in value['inputs']]
    expected=[int(sum(a[r*4+k]*b[k*5+c] for k in range(4))+7>=100) for r in range(3) for c in range(5)]
    post=with_post(value);post['post']['nodes'].append(dict(id='flag',op='ge_imm',args=['biased'],imm=100));post['post']['result']='flag'
    yield 'matmul-bias-threshold',post,expected
    value=next(v for n,v in old_cases() if n=='max-window');words=value['inputs'][0]['words']
    expected=[(max(words[r*13+max(0,min(12,c+k))] for k in [-1,0,1])**2+7)&0xffffffff for r in range(9) for c in range(13)]
    nodes=[dict(id='x',op='load',view='reduced'),dict(id='square',op='mul',args=['x','x']),dict(id='biased',op='add_imm',args=['square'],imm=7)]
    yield 'max-then-square',with_post(value,nodes),expected
    value=make(1,1,(1,1));value['inputs'][0]['words']=[0xffffffff];value['kernel']['extent']=2
    nodes=[dict(id='x',op='load',view='reduced'),dict(id='wrap',op='add_imm',args=['x'],imm=2),dict(id='flag',op='ge_imm',args=['wrap'],imm=1)]
    yield 'wrap-before-threshold',with_post(value,nodes,'flag'),[0]
    for rows,columns in [(8,16),(13,10),(16,16)]:
        value=make(rows,columns,(rows,columns));expected=[(v+7)&0xffffffff for v in value['inputs'][0]['words']]
        yield 'words-'+str(rows*columns),with_post(value),expected
