"""Owned bounded subrange fixtures; standard range/liveness methods."""
import copy
import struct
import zlib
from scripts.fold_dag_cases import job, graph
from raveil.affine_fold import compile_region
from raveil import fold_bridge as bridge


def link(name,offset,length):return {'from':name,'offset':offset,'length':length}
def ranged(jobs,output=None):
    result=graph(jobs,output);result['schema']='raveil.fold-dag.v2';return result


def scenarios():
    merge=ranged([job('a',256),job('b',256),job('merge',128,[link('a',128,128),link('b',0,128)])])
    yield 'upper-lower-merge',merge,None
    yield 'overlapping-same-producer',ranged([job('a',256),job('merge',128,[link('a',0,128),link('a',64,128)])]),None
    yield 'one-word-boundary',ranged([job('a',256),job('merge',1,[link('a',127,1),link('a',128,1)])]),None
    yield 'last-word',ranged([job('a',256),job('merge',1,[link('a',255,1),[10]])]),None
    wide=job('outer',256,[link('a',128,128),link('b',0,128)])
    wide['region']['lengths']=[128,128];wide['region']['views']={'a':[0,0,0,1,0],'b':[1,0,1,0,0]}
    yield 'four-refs-wide-output',ranged([job('a',256),job('b',256),wide]),None
    delayed=ranged([job('a',256),job('temp'),job('left',128,[link('a',128,128),[7]*128]),
                    job('right',128,[link('a',0,128),[9]*128]),job('merge',128,[link('left',0,128),link('right',0,128)])])
    yield 'delayed-slices',delayed,None
    yield 'failed-producer',merge,['wrong-word','none','none']
    pinned=copy.deepcopy(merge);pinned['output']='a'
    yield 'rollback-pinned-producer',pinned,['none','none','wrong-word']
    maximum=ranged([job(f'j{i}',256) for i in range(8)])
    for j in maximum['jobs']:j['region']['lengths']=[324,324];j['inputs']=[list(range(324)),list(range(324))]
    yield 'maximum-v2-envelope',maximum,None
    from scripts.affine_fold_vectors import region,load
    empty=dict(name='literal-empty',region=region([1,1],1,[0,1],{'b':[1,0,0,0,0]},[load('b','b')],'b'),inputs=[[],[7]])
    yield 'empty-literal-valid',ranged([empty]),None
    from scripts.fold_dag_cases import scenarios as legacy
    yield 'legacy-v1-diamond',next(g for name,g,_ in legacy() if name=='diamond'),None


def rejected_graphs():
    base=next(scenarios())[1];result={}
    for name,offset,length in [('out-of-bounds',129,128),('overflow',0xffffffff,128),('zero-length',0,0),('extent-mismatch',0,127)]:
        g=copy.deepcopy(base);g['jobs'][2]['inputs'][0]=link('a',offset,length);result[name]=g
    from scripts.affine_fold_vectors import region,load
    for start in [0,128,256]:
        consumer=dict(name='unused-link',region=region([1,1],1,[0,1],{'b':[1,0,0,0,0]},[load('b','b')],'b'),inputs=[link('a',start,0),[7]])
        result[f'empty-linked-{start}']=ranged([job('a',256),consumer])
    result['five-touched-refs']=ranged([job('a',256),job('b',256),job('merge',128,[link('a',64,128),link('b',64,128)])])
    return result


def raw_encode(session,epoch=99):
    names={j['name']:i for i,j in enumerate(session['jobs'])};payload=b''
    for i,j in enumerate(session['jobs']):
        config=compile_region(j['region']);metadata=[];inputs=[]
        for b,operand in enumerate(j['inputs']):
            if isinstance(operand,dict):
                source=names[operand['from']];metadata.extend([source,operand.get('offset',0),operand.get('length',config[5+b])]);inputs.append([0]*config[5+b])
            else:metadata.extend([0xffffffff,0,config[5+b]]);inputs.append(operand)
        payload+=struct.pack('<6I',*metadata)+bridge.request_bytes(config,inputs,i+1)
    body=struct.pack('<4IQ2I',0x51444631,2,40+len(payload),len(session['jobs']),epoch,names[session['output']],0)+payload
    return body+struct.pack('<2I',zlib.crc32(body),0x44454e44)
