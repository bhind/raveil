"""Owned DAG acceptance fixtures; no novel scheduling claim."""
import copy,struct,zlib
from scripts.affine_fold_vectors import region,load,binary,vectors
from raveil import fold_bridge as bridge
from raveil.affine_fold import compile_region


def job(name,words=128,inputs=None):
    rows=1 if words==1 else words//16;cols=1 if words==1 else 16
    return dict(name=name,region=region([rows,cols],1,[words,words],
        {'a':[0,0,cols,1,0],'b':[1,0,cols,1,0]},binary('add'),'x'),
        inputs=inputs if inputs is not None else [list(range(words)),[3]*words])


def linked(a,b=None):return [{'from':a},{'from':a if b is None else b}]


def graph(jobs,output=None):return dict(schema='raveil.fold-dag.v1',jobs=jobs,output=output or jobs[-1]['name'])


def scenarios():
    normal=[v for v in vectors() if v['mode']==0]
    for i in range(0,len(normal),8):
        yield f'normal-{i//8}',graph([dict(name=f'j{k}',region=copy.deepcopy(v['descriptor']),inputs=copy.deepcopy(v['inputs'])) for k,v in enumerate(normal[i:i+8])]),None
    # Root remains live for both branches; merge reads two distinct generated arrays.
    diamond=graph([job('root'),job('left',inputs=linked('root')),job('right',inputs=linked('root')),job('merge',inputs=linked('left','right'))])
    yield 'diamond',diamond,None
    outer=job('outer',256,linked('left','right'));outer['region']['lengths']=[128,128]
    outer['region']['views']={'a':[0,0,0,1,0],'b':[1,0,1,0,0]}
    yield 'four-refs-small-small-large',graph([job('left'),job('right'),outer]),None
    merge=job('merge',128,linked('large','small'));merge['region']['lengths']=[256,128]
    yield 'four-refs-large-small-small',graph([job('large',256),job('small'),merge]),None
    yield 'unequal-versions-pinned-output',graph([job('old'),job('replacement'),job('wide',256),job('later')],'wide'),None
    delayed=graph([job('root'),job('temporary'),job('left',inputs=linked('root')),job('more'),job('right',inputs=linked('root')),
                   job('merge',inputs=linked('left','right')),job('end',inputs=linked('merge')),job('last',inputs=linked('end'))])
    yield 'delayed-fanout-eight',delayed,None
    yield 'failed-producer',diamond,['none','wrong-word','none','none']
    yield 'merge-rtl-fault',diamond,['none','none','none','rtl-fault']
    yield 'lost-frame',diamond,['none','invalid-char','none','none']
    # Earlier designated result remains live even when later independent work faults.
    yield 'pinned-output-later-fault',graph([job('answer'),job('later')],'answer'),['none','wrong-word']


def rejected_graphs():
    merge=job('merge',1,linked('a','b'));merge['region']['lengths']=[256,256]
    five=graph([job('a',256),job('b',256),merge])
    jobs=[job(f'large{i}',256) for i in range(4)]+[job('extra',1)]
    for i in range(3):
        j=job(f'consumer{i}',1,linked(f'large{i}'));j['region']['lengths']=[256,256];jobs.append(j)
    return {'five-refs':five,'live-capacity':graph(jobs,'large3')}


def raw_encode(session,epoch=99):
    """Encode without lifetime/ref admission, solely for rejection probes."""
    names={j['name']:i for i,j in enumerate(session['jobs'])};payload=b''
    for i,j in enumerate(session['jobs']):
        c=compile_region(j['region']);sources=[];inputs=[]
        for b,operand in enumerate(j['inputs']):
            if isinstance(operand,dict):sources.append(names[operand['from']]);inputs.append([0]*c[5+b])
            else:sources.append(0xffffffff);inputs.append(operand)
        payload+=struct.pack('<2I',*sources)+bridge.request_bytes(c,inputs,i+1)
    body=struct.pack('<4IQ2I',0x51444631,1,40+len(payload),len(session['jobs']),epoch,names[session['output']],0)+payload
    return body+struct.pack('<2I',zlib.crc32(body),0x44454e44)
