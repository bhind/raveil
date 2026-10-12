"""Owned finite-grid program fixtures for source-level compiler validation."""
import copy
from raveil.mf01_grid import SCHEMA


def make(rows=7,columns=11,tile=(4,8),boundary='zero',two=False):
    inputs=[dict(schema='raveil.grid-input/v2',rows=rows,columns=columns,words=[(0xffffffff-i*7919-j*19)&0xffffffff for i in range(rows*columns)]) for j in range(2 if two else 1)]
    return dict(schema=SCHEMA,inputs=inputs,tile=list(tile),boundary=boundary,kernel=dict(extent=1,fold='sum',
        views={'a':dict(input=0,offset=[0,0],step=[0,0])},nodes=[dict(id='a',op='load',view='a')],result='a'))


def cases():
    box=make(24,24,(8,8));box['kernel']=dict(extent=3,fold='sum',views={f'r{i}':dict(input=0,offset=[i-1,-1],step=[0,1]) for i in range(3)},
        nodes=[dict(id=f'r{i}',op='load',view=f'r{i}') for i in range(3)]+[dict(id='ab',op='add',args=['r0','r1']),dict(id='sum',op='add',args=['ab','r2'])],result='sum')
    yield 'box-sum',box
    maximum=make(9,13,(8,8),'clamp');maximum['kernel']['extent']=3;maximum['kernel']['fold']='max';maximum['kernel']['views']['a'].update(offset=[0,-1],step=[0,1])
    yield 'max-window',maximum
    join=make(two=True,boundary='wrap');join['kernel']['views']['b']=dict(input=1,offset=[-1,1],step=[0,0]);join['kernel']['nodes'] += [dict(id='b',op='load',view='b'),dict(id='m',op='mul',args=['a','b']),dict(id='x',op='max',args=['a','m']),dict(id='bias',op='add_imm',args=['x'],imm=7),dict(id='mask',op='ge_imm',args=['bias'],imm=100)]
    join['kernel']['result']='mask';yield 'two-input-program',join
    cross=make(3,5,(2,3),'wrap',True);cross['kernel']['extent']=3;cross['kernel']['views']={'a':dict(input=0,offset=[-1,0],step=[1,0]),'b':dict(input=1,offset=[0,-1],step=[0,1])};cross['kernel']['nodes']=[dict(id='a',op='load',view='a'),dict(id='b',op='load',view='b'),dict(id='x',op='mul',args=['a','b'])];cross['kernel']['result']='x';yield 'cross-input-fold',cross
    for mode in ['zero','clamp','wrap']:
        shifted=make(1,17,(1,8),mode);shifted['kernel']['views']['a']['offset']=[-1,2];yield 'one-row-'+mode,shifted
    wide=make(1,9,(1,9),'wrap');wide['kernel']['extent']=64;wide['kernel']['views']['a']['step']=[0,5];yield 'maximum324-halo',wide
