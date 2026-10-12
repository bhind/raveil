#!/usr/bin/env python3
"""Actual QEMU/RTL dependency-chain acceptance; functional evidence only."""
import argparse,copy,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from raveil.fold_chain import run,verify
from scripts.affine_fold_vectors import vectors,region,load


def make(cases):
    return dict(schema='raveil.fold-chain.v1',jobs=[
        dict(name=f'job-{i}',region=copy.deepcopy(v['descriptor']),inputs=copy.deepcopy(v['inputs'])) for i,v in enumerate(cases)])


def link(session,index,source,mask=3):
    for b in range(2):
        if mask&(1<<b):session['jobs'][index]['inputs'][b]={'from':f'job-{source}'}
    return session


def scenarios():
    normal=[v for v in vectors() if v['mode']==0];by={v['name']:v for v in normal}
    for i in range(0,len(normal),8):yield f'normal-{i//8}',make(normal[i:i+8]),None
    add=by['add-16x16'];small=by['mul-1x1']
    chain=make([add,by['transpose-16x16'],by['mul-16x16'],by['matmul-16x16x16'],by['broadcast-16x16']])
    link(chain,1,0,1);link(chain,2,1);link(chain,3,2);link(chain,4,3,1)
    for name,length,shape,extent,stride in [('rows',256,[16,1],16,16),('sum',16,[1,1],16,16)]:
        i=len(chain['jobs']);chain['jobs'].append(dict(name=f'job-{i}',region=region(shape,extent,[length,0],
            {'a':[0,0,stride,0,1]},[load('a','a')],'a'),inputs=[{'from':f'job-{i-1}'},[]]))
    chain['jobs'].append(dict(name='job-7',region=small['descriptor'],inputs=[{'from':'job-6'},{'from':'job-6'}]))
    yield 'heterogeneous-eight',chain,None
    # Only B linked; A is literal. Then both logical inputs alias the same producer.
    d=make([add,by['max-16x16'],by['mul-16x16']]);link(d,1,0,2);link(d,2,1)
    yield 'input-b-and-alias',d,None
    # A failed named producer must not bind the last successful result.
    d=make([add,add,add]);link(d,1,0);link(d,2,1)
    yield 'failed-producer',d,['none','wrong-word','none']
    # Reading overwritten job0 is unavailable even though same bank has newer bytes.
    d=make([add,add,add,add]);link(d,1,0);link(d,2,1);link(d,3,0)
    yield 'stale-producer',d,None
    # Earlier non-latest bank remains available; writing the other bank is safe.
    d=make([add,add,add]);link(d,1,0);link(d,2,0)
    yield 'older-live-producer',d,None
    # Consumer fault does not invalidate its unchanged source; explicit retry names source0.
    for injection in ['rtl-fault','replay-previous','bad-crc']:
        d=make([add,add,add]);link(d,1,0);link(d,2,0)
        yield 'recovery-'+injection,d,['none',injection,'none']
    d=make([add,add,add]);link(d,1,0);link(d,2,0)
    yield 'lost-frame',d,['none','invalid-char','none']


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['kernel','build','output']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False);rows=[]
    for name,session,injections in scenarios():
        r=run(session,a.kernel,a.build,a.output/name,injections=injections);verify(a.output/name)
        row=dict(name=name,processed=r['processed'],planned=r['planned'],halted=r['halted'],versions=r['versions'],
            successes=sum(j['result']['approved'] for j in r['jobs']),words=sum(len(j['result']['output']) for j in r['jobs']))
        rows.append(row);print('PASS',json.dumps(row),flush=True)
    (a.output/'summary.json').write_text(json.dumps(dict(evidence_class='host-mediated-QEMU-RTL-chain-functional',sessions=rows),indent=2)+'\n')


if __name__=='__main__':main()
