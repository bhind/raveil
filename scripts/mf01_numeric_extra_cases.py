"""Signed ordering at register/instruction and modular-accumulation boundaries."""
from scripts.mf01_numeric_cases import EDGES,MASK,pointwise,gemm_bias_relu,signed


def shared_sign_live_input():
    value,_=pointwise(EDGES,EDGES,tile=(7,7))
    value['kernel']['nodes'].extend([
        dict(id='second',op='max_i32',args=['x','a']),
        dict(id='answer',op='add',args=['second','a'])])
    value['kernel']['result']='answer'
    return value,[(max(a,b)+a)&MASK for a in EDGES for b in EDGES]


def wrapped_gemm_bias_relu():
    value,_=gemm_bias_relu();stages={x['name']:x['source'] for x in value['stages']}
    a=[EDGES[i%len(EDGES)] for i in range(12)]
    b=[EDGES[(3*i+1)%len(EDGES)] for i in range(20)]
    bias=[(1<<31)-1,1,-1,-(1<<31),17]
    stages['product']['inputs'][0]['words']=[x&MASK for x in a]
    stages['product']['inputs'][1]['words']=[x&MASK for x in b]
    stages['activation']['inputs'][1]['words']=[x&MASK for x in bias]
    unbounded=[sum(a[r*4+k]*b[k*5+c] for k in range(4))+bias[c] for r in range(3) for c in range(5)]
    expected=[max(0,signed(x&MASK)) for x in unbounded]
    assert expected!=[max(0,x) for x in unbounded]
    assert 0 in expected and any(x>0 for x in expected)
    return value,expected
