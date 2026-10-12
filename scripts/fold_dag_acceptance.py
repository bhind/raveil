#!/usr/bin/env python3
"""Functional DAG execution/admission acceptance with existing offline tools."""
import argparse,json,shutil,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from raveil.fold_dag import run,verify
from raveil.sonatine_fold import command_for,digest
from scripts.fold_dag_cases import scenarios,rejected_graphs,raw_encode


def main(*, cases=scenarios, rejections=rejected_graphs, encoder=raw_encode):
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['kernel','build','output']:p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();root=a.output.resolve();root.mkdir(parents=True,exist_ok=False);rows=[]
    for name,g,injections in cases():
        r=run(g,a.kernel,a.build,root/name,injections=injections);verify(root/name)
        row=dict(name=name,processed=r['processed'],planned=r['planned'],halted=r['halted'],versions=r['versions'],
                 final_available=r['output']['available'],successes=sum(j['result']['approved'] for j in r['jobs']),words=sum(len(j['result']['output']) for j in r['jobs']))
        rows.append(row);print('PASS',json.dumps(row),flush=True)
    rejected=[]
    for name,g in rejections().items():
        target=root/name;target.mkdir();(target/'request.bin').write_bytes(encoder(g));shutil.copyfile(a.kernel,target/'kernel.elf')
        cmd=command_for(shutil.which('qemu-system-riscv64'),target);(target/'command.json').write_text(json.dumps(cmd)+'\n')
        proc=subprocess.run(cmd,capture_output=True,timeout=15,check=True)
        (target/'stdout.log').write_bytes(proc.stdout);(target/'stderr.log').write_bytes(proc.stderr)
        lines=[l for l in proc.stdout.decode().splitlines() if l.startswith('RAVEIL-FOLD')]
        if lines!=['RAVEIL-FOLD-DAG-REJECT-V1 reason=admission-or-initialization']:raise AssertionError((name,lines))
        rejected.append(dict(name=name,no_dispatch=True,request_sha256=digest(target/'request.bin')))
        print('PASS admission',name,flush=True)
    (root/'summary.json').write_text(json.dumps(dict(evidence_class='host-mediated-QEMU-RTL-dag-functional',sessions=rows,rejected=rejected),indent=2)+'\n')


if __name__=='__main__':main()
