"""Owned, independently specified end-to-end array workloads (not compiler cases)."""
import copy
from raveil import array_program as a


def literal(r,c,words):return dict(schema='raveil.grid-input/v2',rows=r,columns=c,words=list(words))
def view(index=0,offset=(0,0),row=(1,0),column=(0,1),step=(0,0)):
    return dict(input=index,offset=list(offset),row=list(row),column=list(column),step=list(step))
def load(name='x',v='v'):return dict(id=name,op='load',view=v)
def src(r,c,words,nodes=None):
    nodes=nodes or [load()]
    return dict(inputs=[literal(r,c,words)],shape=[r,c],boundary='zero',kernel=dict(extent=1,fold='sum',views={'v':view()},nodes=nodes,result=nodes[-1]['id']))
def program(s):return dict(schema=a.SCHEMA,stages=[dict(name='answer',source=s)],outputs=['answer'])
def output(name,r,c,words):return dict(name=name,rows=r,columns=c,words=list(words))
def signed(w):return w if w<0x80000000 else w-0x100000000


def cases():
    words=[0,0xffffffff,0x7fffffff,0x80000000,3,7]
    nodes=[load()];previous='x'
    for i in range(23):
        name=f'n{i}';nodes.append(dict(id=name,op='add_imm',args=[previous],imm=1));previous=name
    yield 'long-expression',program(src(2,3,words,nodes)),[output('answer',2,3,[(x+23)&a.MASK for x in words])]
    nodes=[load(f'x{i}') for i in range(9)];previous='x0'
    for i in range(1,9):
        name=f's{i}';nodes.append(dict(id=name,op='add',args=[previous,f'x{i}']));previous=name
    yield 'nine-live-values',program(src(2,3,words,nodes)),[output('answer',2,3,[(x*9)&a.MASK for x in words])]
    for r,c in [(1,3),(17,19)]:
        words=[(i*123457)&a.MASK for i in range(r*c)];s=src(r,c,words,[load(),dict(id='z',op='add_imm',args=['x'],imm=7)])
        yield f'pointwise-{r}-{c}',program(s),[output('answer',r,c,[(x+7)&a.MASK for x in words])]
    for m,n,k in [(3,5,3),(4,3,2)]:
        left=[(i-4)&a.MASK for i in range(m*k)];right=[(3*i-5)&a.MASK for i in range(k*n)]
        s=src(m,n,[0]*(m*n));s['inputs']=[literal(m,k,left),literal(k,n,right)]
        s['kernel']=dict(extent=k,fold='sum',views={'a':view(0,column=(0,0),step=(0,1)),'b':view(1,row=(0,0),column=(0,1),step=(1,0))},
                         nodes=[load('a','a'),load('b','b'),dict(id='z',op='mul',args=['a','b'])],result='z')
        expected=[sum(left[r*k+t]*right[t*n+c] for t in range(k))&a.MASK for r in range(m) for c in range(n)]
        yield f'gemm-{m}-{n}-{k}',program(s),[output('answer',m,n,expected)]
    for mode in ['zero','clamp','wrap']:
        words=list(range(12));s=src(3,4,words);s['boundary']=mode;s['kernel']['extent']=3;s['kernel']['views']['v']=view(offset=(0,-1),step=(0,1))
        expected=[]
        for r in range(3):
            for c in range(4):
                acc=0
                for x in (c-1,c,c+1):
                    if mode=='zero' and not 0<=x<4:continue
                    col=min(3,max(0,x)) if mode=='clamp' else x%4 if mode=='wrap' else x
                    acc+=words[r*4+col]
                expected.append(acc)
        yield 'stencil-'+mode,program(s),[output('answer',3,4,expected)]
    s=src(1,1,[0]);s['inputs']=[literal(1,2,[0xffffffff,2])];s['kernel']['extent']=2;s['kernel']['views']['v']=view(step=(0,1))
    s['post']=dict(nodes=[load('r','reduced'),dict(id='z',op='relu_i32',args=['r'])],result='z')
    yield 'wrapped-fold-post',program(s),[output('answer',1,1,[1])]
    s=copy.deepcopy(s);s.pop('post');s['kernel']['fold']='max'
    yield 'unsigned-max-fold',program(s),[output('answer',1,1,[0xffffffff])]
    words=[0xffffffff,0x80000000,0x7fffffff,0,3,1];rhs=[1,0xffffffff,0x80000000,2,0,5]
    s=src(2,3,words);s['inputs'].append(literal(2,3,rhs));s['kernel']['views']['w']=view(1)
    s['kernel'].update(nodes=[load(),load('y','w'),dict(id='m',op='max_i32',args=['x','y']),dict(id='r',op='relu_i32',args=['m']),dict(id='p',op='mul',args=['r','y']),dict(id='z',op='ge_imm',args=['p'],imm=3)],result='z')
    expected=[int(((max(0,signed(x),signed(y))*y)&a.MASK)>=3) for x,y in zip(words,rhs)]
    yield 'signed-modular-threshold',program(s),[output('answer',2,3,expected)]
    s=src(3,2,[0]*6);s['inputs']=[literal(2,3,range(6))];s['kernel']['views']['v']=view(row=(0,1),column=(1,0))
    yield 'transpose',program(s),[output('answer',3,2,[0,3,1,4,2,5])]
    s=src(2,3,range(6),[load(),dict(id='z',op='add_imm',args=['x'],imm=3)])
    stages=[dict(name='base',source=s)]
    for name,bias in [('left',2),('right',7)]:
        child=copy.deepcopy(s);child['inputs']=[{'from':'base'}];child['kernel']['nodes'][-1]['imm']=bias;stages.append(dict(name=name,source=child))
    child=copy.deepcopy(s);child['inputs']=[{'from':'left'},{'from':'right'}];child['kernel']['views']['w']=view(1)
    child['kernel'].update(nodes=[load(),load('y','w'),dict(id='z',op='add',args=['x','y'])],result='z');stages.append(dict(name='join',source=child))
    yield 'fanout-join',dict(schema=a.SCHEMA,stages=list(reversed(stages)),outputs=['join','base']),[output('join',2,3,[15+2*i for i in range(6)]),output('base',2,3,[3+i for i in range(6)])]
