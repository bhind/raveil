#!/usr/bin/env python3
"""Actual foreground signal/deadline/cleanup/retry acceptance; no physical metrics."""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from raveil import project as p, project_array as a, project_array_workspace as w, project_dag_batch as b
from scripts.prepare_array_app import prepare


def inspect_resources(workspace):
    """Read-only absence audit; transport failure never means resource absence."""
    queries=[];remaining=[]
    def query(argv):
        result=subprocess.run(argv,capture_output=True,text=True,timeout=15)
        queries.append(dict(argv=argv,code=result.returncode,stdout=result.stdout,stderr=result.stderr))
        return result
    listing=query(['docker','ps','-a','--filter','name=raveil-fold-','--format','{{.ID}}'])
    if listing.returncode:raise RuntimeError('cannot list Docker resources: '+listing.stderr)
    for identity in listing.stdout.splitlines():
        inspected=query(['docker','inspect',identity])
        if inspected.returncode:
            if 'no such object' in inspected.stderr.lower():continue
            raise RuntimeError('cannot inspect Docker resource: '+inspected.stderr)
        info=json.loads(inspected.stdout)[0]
        if any(str(m.get('Source','')).startswith(str(workspace)+'/arrays/') for m in info['Mounts']):remaining.append(identity)
    processes=query(['ps','-axo','pid=,command='])
    if processes.returncode:raise RuntimeError('cannot list processes: '+processes.stderr)
    qemu=[line for line in processes.stdout.splitlines() if 'qemu-system-riscv64' in line and str(workspace)+'/arrays/' in line]
    return dict(containers=remaining,qemu=qemu,queries=queries)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('output','kernel','build'):parser.add_argument('--'+key,type=Path,required=True)
    args=parser.parse_args();root=args.output.absolute();root.mkdir(parents=True,exist_ok=False)
    app=root/'app';prepare(app,args.kernel,args.build)
    workspace=app/'workspace';source=workspace/'inputs/program.json';small=source.read_bytes()
    results=[];failed={};owned=[]
    def tree(path):return p.tree(path,max_bytes=b.MAX_BYTES,max_entries=b.MAX_ENTRIES)
    def run(label,extra=(),signum=None):
        argv=[str(app/'raveil'),'array-run',*extra]
        (root/(label+'.command.json')).write_bytes(p.encoded(dict(argv=argv,cwd=str(root),signal=signum)))
        start=time.monotonic();target=None;qemu_pids=[];signals=[]
        with (root/(label+'.stdout')).open('w') as out,(root/(label+'.stderr')).open('w') as err:
            proc=subprocess.Popen(argv,cwd=root,stdout=out,stderr=err,start_new_session=True)
            try:
                if signum is not None or label=='04-timeout':
                    end=time.monotonic()+90
                    while proc.poll() is None and time.monotonic()<end:
                        listing=subprocess.run(['docker','ps','--filter','name=raveil-fold-','--format','{{.ID}}'],capture_output=True,text=True,timeout=10)
                        assert listing.returncode==0,listing.stderr
                        for identity in listing.stdout.splitlines():
                            inspected=subprocess.run(['docker','inspect',identity],capture_output=True,text=True,timeout=10)
                            if inspected.returncode:continue  # A short job may have finished between calls.
                            info=json.loads(inspected.stdout)[0]
                            if info['State']['Running'] and any(str(m.get('Source','')).startswith(str(workspace)+'/arrays/') for m in info['Mounts']):
                                target=info['Id'];owned.append(target);break
                        if target:break
                        time.sleep(.01)
                    assert target is not None,'no live owned RTL container observed'
                    listing=subprocess.check_output(['ps','-axo','pid=,command='],text=True)
                    for line in listing.splitlines():
                        fields=line.strip().split(None,1)
                        if len(fields)==2 and 'qemu-system-riscv64' in fields[1] and str(workspace)+'/arrays/' in fields[1]:qemu_pids.append(int(fields[0]))
                    assert qemu_pids,'no owned QEMU observed during RTL execution'
                    if signum is not None:
                        for _ in range(2):
                            if proc.poll() is None:
                                os.killpg(proc.pid,signum);signals.append(int(signum));time.sleep(.02)
                code=proc.wait(timeout=600)
            finally:
                if proc.poll() is None:
                    os.killpg(proc.pid,signal.SIGTERM)
                    try:proc.wait(timeout=75)
                    except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=5)
        resources=inspect_resources(workspace)
        (root/(label+'.resources.json')).write_bytes(p.encoded(resources))
        assert not resources['containers'] and not resources['qemu'],'owned resources remain'
        stdout=(root/(label+'.stdout')).read_text();stderr=(root/(label+'.stderr')).read_text()
        assert 'Traceback' not in stderr,stderr
        if target:
            check=subprocess.run(['docker','inspect',target],capture_output=True,text=True,timeout=15)
            (root/(label+'.container-check.json')).write_bytes(p.encoded(dict(id=target,code=check.returncode,stdout=check.stdout,stderr=check.stderr)))
            assert check.returncode!=0 and 'no such' in check.stderr.lower(),check.stderr
            running=set(int(x) for x in subprocess.check_output(['ps','-axo','pid='],text=True).split())
            assert not running.intersection(qemu_pids),'owned QEMU remains'
        result=dict(label=label,code=code,elapsed_seconds=time.monotonic()-start,observed_live_container=target,
                    observed_qemu_pids=qemu_pids,signals=signals)
        if code==0:
            record=json.loads(stdout);assert record['status']=='succeeded';result['id']=record['id'];result['outputs']=record['outputs']
        else:
            assert stdout=='',stdout
            diagnostic=json.loads(stderr.splitlines()[-1]);assert diagnostic['outputs'] is None
            identity=diagnostic['attempt'];assert identity is not None
            assert not (workspace/'arrays'/identity/'record.json').exists()
            failed[identity]=tree(workspace/'arrays'/identity)
            result.update(id=identity,diagnostic=diagnostic)
        results.append(result);(root/(label+'.result.json')).write_bytes(p.encoded(result))
        print('PASS',label,'exit',code,flush=True)
        return result
    expected_small=[dict(name='first',rows=2,columns=3,words=[23,24,25,26,27,28]),dict(name='transpose',rows=3,columns=2,words=[23,26,24,27,25,28])]
    baseline=run('01-baseline');assert baseline['outputs']==expected_small
    preserved=tree(workspace/'arrays'/baseline['id'])
    large=p.REPOSITORY/'examples/array-program/fused-long-map.json';source.write_bytes(large.read_bytes())
    interrupted=run('02-interrupt',signum=signal.SIGINT);assert interrupted['code']==130
    terminated=run('03-terminate',signum=signal.SIGTERM);assert terminated['code']==143
    timed=run('04-timeout',['--timeout-seconds','8']);assert timed['code']==124
    assert timed['observed_live_container'] and timed['observed_qemu_pids']
    retry=run('05-large-retry',['--timeout-seconds','600'])
    words=json.loads(large.read_text())['stages'][0]['source']['inputs'][0]['words']
    expected=[dict(name='answer',rows=64,columns=64,words=[(x+23)&0xffffffff for x in words])]
    assert retry['outputs']==expected
    source.write_bytes(small);final=run('06-restored-input',['--timeout-seconds','300']);assert final['outputs']==expected_small
    assert tree(workspace/'arrays'/baseline['id'])==preserved
    for identity,before in failed.items():assert tree(workspace/'arrays'/identity)==before
    project=p.Project(workspace)
    with patch('subprocess.Popen',side_effect=AssertionError('saved inspection executed')):
        history=a.history(project);assert len(history)==6
        assert sum(row['status']=='unsealed' for row in history)==3
        for row in (baseline,retry,final):assert a.load(project,row['id'])['outputs']==row['outputs']
        assert a.compare(project,baseline['id'],final['id'])['changed_cells']==0
        assert json.loads(w.output(project))['id']==final['id']
    assert p.tree(app/'engine')==json.loads((app/'app.json').read_text())['engine']
    summary=dict(evidence_class='actual QEMU emulation and RTL functional simulation',results=results,
        failed_trees_preserved=list(failed),saved_inspection_without_processes=True,app=str(app),
        published_words=sum(len(o['words']) for row in (baseline,retry,final) for o in row['outputs']))
    (root/'summary.json').write_bytes(p.encoded(summary));print('PASS complete',flush=True)
    return 0

if __name__=='__main__':raise SystemExit(main())
