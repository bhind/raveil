"""Owned affine-grid workloads with direct formulas independent of lowering."""
from raveil.mf01_grid import SCHEMA_V2


def grid(rows,columns,seed=1):
    return dict(schema='raveil.grid-input/v2',rows=rows,columns=columns,
                words=[(0xffffffff-i*7919-seed*19)&0xffffffff for i in range(rows*columns)])


def view(input,row,column,step=(0,0),offset=(0,0)):
    return dict(input=input,row=list(row),column=list(column),step=list(step),offset=list(offset))


def source(inputs,shape,tile,views,nodes,result,extent=1,boundary='zero'):
    return dict(schema=SCHEMA_V2,inputs=inputs,shape=list(shape),tile=list(tile),boundary=boundary,
                kernel=dict(extent=extent,fold='sum',views=views,nodes=nodes,result=result))


def matmul(m,n,k,tile=(8,8)):
    a,b=grid(m,k),grid(k,n,2)
    value=source([a,b],(m,n),tile,{'a':view(0,(1,0),(0,0),(0,1)),'b':view(1,(0,0),(0,1),(1,0))},
                 [dict(id='a',op='load',view='a'),dict(id='b',op='load',view='b'),dict(id='x',op='mul',args=['a','b'])],'x',k)
    expected=[sum(a['words'][r*k+t]*b['words'][t*n+c] for t in range(k))&0xffffffff for r in range(m) for c in range(n)]
    return value,expected


def cases():
    for name,m,n,k,tile in [('matmul',17,19,9,(8,8)),('thin-matmul',1,17,64,(1,4)),('maximum324-matmul',6,6,54,(6,6))]:
        value,expected=matmul(m,n,k,tile);yield name,value,expected
    a=grid(19,17)
    value=source([a],(17,19),(8,8),{'a':view(0,(0,1),(1,0))},[dict(id='a',op='load',view='a')],'a')
    yield 'transpose',value,[a['words'][c*17+r] for r in range(17) for c in range(19)]
    a,b=grid(1,7),grid(5,1,2)
    value=source([a,b],(5,7),(3,4),{'a':view(0,(0,0),(0,1)),'b':view(1,(1,0),(0,0))},
                 [dict(id='a',op='load',view='a'),dict(id='b',op='load',view='b'),dict(id='x',op='add',args=['a','b'])],'x')
    yield 'broadcast-sum',value,[(a['words'][c]+b['words'][r])&0xffffffff for r in range(5) for c in range(7)]
    for mode in ['zero','clamp','wrap']:
        a=grid(3,5);value=source([a],(4,6),(2,3),{'a':view(0,(2,0),(0,2),offset=(-1,2))},[dict(id='a',op='load',view='a')],'a',boundary=mode)
        expected=[]
        for r in range(4):
            for c in range(6):
                i,j=2*r-1,2*c+2
                if mode=='zero':word=a['words'][i*5+j] if 0<=i<3 and 0<=j<5 else 0
                elif mode=='clamp':word=a['words'][max(0,min(2,i))*5+max(0,min(4,j))]
                else:word=a['words'][(i%3)*5+j%5]
                expected.append(word)
        yield 'strided-'+mode,value,expected
