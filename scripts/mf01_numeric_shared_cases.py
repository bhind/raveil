"""Owned v5 sources with independent signed/modular expectations."""
import copy
from scripts.mf01_numeric_cases import pointwise,EDGES,MASK,signed,cases as legacy_cases,gemm_bias_relu


def chain(tile=(7,7)):
    value,_=pointwise(EDGES,EDGES,tile=tile);value['schema']='raveil.mf01-grid/v5'
    value['kernel']['nodes'] += [dict(id='second',op='max_i32',args=['x','a']),dict(id='activated',op='relu_i32',args=['second'])]
    value['kernel']['result']='activated'
    return value,[max(0,a,b) for a in EDGES for b in EDGES]


def branch_nodes():
    return [dict(id='a',op='load',view='a'),dict(id='b',op='load',view='b'),
            dict(id='x',op='max_i32',args=['a','b']),dict(id='positive',op='relu_i32',args=['a']),
            dict(id='product',op='mul',args=['x','positive']),dict(id='bias',op='add_imm',args=['product'],imm=1),
            dict(id='answer',op='mul',args=['bias','x'])]


def branch_expected(a,b):
    return ((max(a,b)*max(a,0)+1)*max(a,b))&MASK


def cases():
    value,expected=chain((4,4));yield 'chain-partitioned',value,expected
    value,expected=chain();yield 'chain-single',value,expected
    value,_=pointwise(EDGES,EDGES,tile=(7,7));value['schema']='raveil.mf01-grid/v5'
    value['kernel']['nodes']=branch_nodes();value['kernel']['result']='answer'
    yield 'shared-argument-modular-branch',value,[branch_expected(a,b) for a in EDGES for b in EDGES]
    value=copy.deepcopy(list(legacy_cases())[-1][1]);value['schema']='raveil.mf01-grid/v5'
    value['post']=dict(nodes=[dict(id='r',op='load',view='reduced'),dict(id='next',op='add_imm',args=['r'],imm=1),
        dict(id='x',op='max_i32',args=['r','next']),dict(id='second',op='max_i32',args=['x','r']),
        dict(id='activated',op='relu_i32',args=['second'])],result='activated')
    yield 'shared-post-after-wrap',value,[max(0,signed((6*x)&MASK),signed((6*x+1)&MASK)) for x in EDGES]


def branch_flow():
    value,_=gemm_bias_relu();stages={s['name']:s['source'] for s in value['stages']}
    activation=stages['activation'];activation['schema']='raveil.mf01-grid/v5'
    activation['kernel']['nodes']=branch_nodes();activation['kernel']['result']='answer'
    a,b=(x['words'] for x in stages['product']['inputs']);bias=activation['inputs'][1]['words']
    expected=[]
    for r in range(3):
        for c in range(5):
            product=sum(signed(a[r*4+k])*signed(b[k*5+c]) for k in range(4))&MASK
            expected.append(branch_expected(signed(product),signed(bias[c])))
    return value,expected
