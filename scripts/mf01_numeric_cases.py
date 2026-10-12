"""Owned signed-bit-pattern workloads; expectations use Python signed arithmetic."""
from scripts.mf01_grid_affine_cases import source,view

MASK=(1<<32)-1
EDGES=[-(1<<31),-(1<<31)+1,-1,0,1,(1<<31)-2,(1<<31)-1]


def grid(rows,columns,words):
    return dict(schema='raveil.grid-input/v2',rows=rows,columns=columns,words=[x&MASK for x in words])


def signed(word):
    return word if word<(1<<31) else word-(1<<32)


def pointwise(a,b,op='max_i32',tile=(4,4)):
    rows,cols=len(a),len(b)
    value=source([grid(rows,1,a),grid(1,cols,b)],(rows,cols),tile,
                 {'a':view(0,(1,0),(0,0)),'b':view(1,(0,0),(0,1))},
                 [dict(id='a',op='load',view='a'),dict(id='b',op='load',view='b'),dict(id='x',op=op,args=['a','b'])],'x')
    value['schema']='raveil.mf01-grid/v4'
    return value,[max(x,y)&MASK for x in a for y in b]


def cases():
    value,expected=pointwise(EDGES,EDGES)
    yield 'signed-max-edges',value,expected
    value,expected=pointwise(EDGES,EDGES,tile=(7,7))
    yield 'signed-max-one-tile',value,expected
    value,expected=pointwise(EDGES,EDGES,tile=(7,7))
    value['kernel']['nodes'].append(dict(id='y',op='relu_i32',args=['x']));value['kernel']['result']='y'
    yield 'shared-sign-and-relu',value,[max(0,signed(x)) for x in expected]
    value=source([grid(1,7,EDGES)],(1,7),(1,7),{'a':view(0,(0,0),(0,1))},[dict(id='a',op='load',view='a')],'a')
    value['schema']='raveil.mf01-grid/v4'
    value['post']=dict(nodes=[dict(id='r',op='load',view='reduced'),dict(id='x',op='relu_i32',args=['r'])],result='x')
    yield 'post-relu-edges',value,[max(0,x) for x in EDGES]
    value=source([grid(1,7,EDGES)],(1,7),(1,7),{'a':view(0,(0,0),(0,1))},
                 [dict(id='a',op='load',view='a'),dict(id='x',op='add',args=['a','a'])],'x',extent=3)
    value['schema']='raveil.mf01-grid/v4';value['post']=dict(nodes=[dict(id='r',op='load',view='reduced'),dict(id='x',op='relu_i32',args=['r'])],result='x')
    yield 'wrapped-reduction-before-relu',value,[max(0,signed((6*x)&MASK)) for x in EDGES]


def gemm_bias_relu():
    m,n,k=3,5,4;a=[-5,2,-3,7, 0,-2,4,-1, 6,3,-7,2];b=[(i*7)%17-8 for i in range(k*n)];bias=[-20,0,17,-3,30]
    first=source([grid(m,k,a),grid(k,n,b)],(m,n),(m,n),
        {'a':view(0,(1,0),(0,0),(0,1)),'b':view(1,(0,0),(0,1),(1,0))},
        [dict(id='a',op='load',view='a'),dict(id='b',op='load',view='b'),dict(id='x',op='mul',args=['a','b'])],'x',k)
    second=source([grid(m,n,[0]*(m*n)),grid(1,n,bias)],(m,n),(m,n),
        {'a':view(0,(1,0),(0,1)),'b':view(1,(0,0),(0,1))},
        [dict(id='a',op='load',view='a'),dict(id='b',op='load',view='b'),dict(id='x',op='add',args=['a','b']),dict(id='y',op='relu_i32',args=['x'])],'y')
    second['schema']='raveil.mf01-grid/v4';second['inputs'][0]={'from':'product'}
    expected=[max(0,sum(a[r*k+t]*b[t*n+c] for t in range(k))+bias[c]) for r in range(m) for c in range(n)]
    return dict(schema='raveil.mf01-flow/v1',stages=[dict(name='activation',source=second),dict(name='product',source=first)],outputs=['activation']),expected
