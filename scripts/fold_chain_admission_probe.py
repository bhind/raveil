#!/usr/bin/env python3
"""Actual QEMU chain-envelope admission failures before any execution."""
import argparse,json,shutil,struct,subprocess,sys,zlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from raveil import fold_chain as c,fold_bridge as b
from raveil.sonatine_fold import command_for,digest
from scripts.affine_fold_vectors import vectors


def bundle(parts):
    body=struct.pack('<4IQ',c.MAGIC,1,32+sum(map(len,parts)),len(parts),99)+b''.join(parts)
    return body+struct.pack('<2I',zlib.crc32(body),c.END)


def invalid_cases():
    v=vectors()[0];request=lambda rid:b.request_bytes(v['config'],v['inputs'],rid)
    first=struct.pack('<2I',0xffffffff,0)+request(1)
    zero=b.request_bytes(v['config'],[[0],[0]],2)
    valid=struct.pack('<2I',0,3)+zero
    bad=bytearray(zero);struct.pack_into('<I',bad,292,1);struct.pack_into('<I',bad,len(bad)-8,zlib.crc32(bad[:-8]))
    large=next(v for v in vectors() if v['name']=='add-16x16')
    large_first=struct.pack('<2I',0xffffffff,0)+b.request_bytes(large['config'],large['inputs'],1)
    return {'forward-link':bundle([first,struct.pack('<2I',1,3)+zero]),
            'bad-mask':bundle([first,struct.pack('<2I',0,4)+zero]),
            'unlinked-source':bundle([first,struct.pack('<2I',0,0)+zero]),
            'nonzero-placeholder':bundle([first,struct.pack('<2I',0,3)+bad]),
            'logical-length':bundle([large_first,valid]),
            'duplicate-id':bundle([first,first]),
            'ninth-job':bundle([struct.pack('<2I',0xffffffff,0)+request(i+1) for i in range(9)]),
            'truncated-footer':bundle([first,valid])[:-1]}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['kernel','output']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();root=a.output.resolve();root.mkdir(parents=True,exist_ok=False);rows=[]
    for name,blob in invalid_cases().items():
        target=root/name;target.mkdir();(target/'request.bin').write_bytes(blob);shutil.copyfile(a.kernel,target/'kernel.elf')
        command=command_for(shutil.which('qemu-system-riscv64'),target);(target/'command.json').write_text(json.dumps(command)+'\n')
        proc=subprocess.run(command,capture_output=True,timeout=15,check=True)
        (target/'stdout.log').write_bytes(proc.stdout);(target/'stderr.log').write_bytes(proc.stderr)
        lines=[l for l in proc.stdout.decode().splitlines() if l.startswith('RAVEIL-FOLD')]
        if lines!=['RAVEIL-FOLD-CHAIN-REJECT-V1 reason=admission-or-initialization']:raise AssertionError((name,lines))
        rows.append(dict(case=name,request_sha256=digest(target/'request.bin'),no_dispatch=True))
    (root/'report.json').write_text(json.dumps(dict(evidence_class='qemu-emulation-correctness',cases=rows),indent=2)+'\n');print(json.dumps(rows))


if __name__=='__main__':main()
