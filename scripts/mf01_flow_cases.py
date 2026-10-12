"""Owned whole-grid compositions with direct end-to-end uint32 formulas."""
import copy
from raveil import mf01_flow as flow
from scripts.mf01_grid_affine_cases import matmul,source,view
from scripts.mf01_grid_post_cases import with_post

MASK=(1<<32)-1


def product(a,b,m,n,k):
    return [sum(a[r*k+t]*b[t*n+c] for t in range(k))&MASK for r in range(m) for c in range(n)]


def pair():
    first,ab=matmul(5,6,7,(3,4));second,_=matmul(5,4,6,(3,3))
    c=second['inputs'][1]['words'];second['inputs'][0]={'from':'first'}
    value=dict(schema=flow.SCHEMA,stages=[dict(name='second',source=second),dict(name='first',source=first)],outputs=['second'])
    return value,[dict(name='second',rows=5,columns=4,words=product(ab,c,5,4,6))]


def diamond():
    first,ab=matmul(5,6,7,(3,4));link={'from':'product'}
    trans=source([link],(6,5),(3,3),{'a':view(0,(0,1),(1,0))},[dict(id='a',op='load',view='a')],'a')
    square=source([link],(5,6),(3,3),{'a':view(0,(1,0),(0,1))},
                  [dict(id='a',op='load',view='a'),dict(id='x',op='mul',args=['a','a'])],'x')
    join,_=matmul(6,6,5,(3,3));join['inputs']=[{'from':'transpose'},{'from':'square'}]
    stages=[dict(name=n,source=s) for n,s in [('join',join),('square',square),('transpose',trans),('product',first)]]
    value=dict(schema=flow.SCHEMA,stages=stages,outputs=['product','join'])
    left=[ab[c*6+r] for r in range(6) for c in range(5)];right=[(w*w)&MASK for w in ab]
    return value,[dict(name='product',rows=5,columns=6,words=ab),dict(name='join',rows=6,columns=6,words=product(left,right,6,6,5))]


def eight():
    value,_=matmul(1,1,1,(1,1));value['inputs'][0]['words']=[3];value['inputs'][1]['words']=[5]
    stages=[dict(name='stage-0',source=value)];word=15
    for i in range(1,8):
        stage=source([{'from':f'stage-{i-1}'}],(1,1),(1,1),{'a':view(0,(1,0),(0,1))},[dict(id='a',op='load',view='a')],'a')
        stage=with_post(stage);word=(word+7)&MASK;stages.append(dict(name=f'stage-{i}',source=stage))
    return dict(schema=flow.SCHEMA,stages=list(reversed(stages)),outputs=['stage-7']),[dict(name='stage-7',rows=1,columns=1,words=[word])]


def cases():
    for name,builder in [('two-products',pair),('branch-join',diamond),('eight-stages',eight)]:
        value,expected=builder();yield name,value,expected
