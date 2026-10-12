#!/usr/bin/env python3
"""Reread a completed local functional probe without executing the simulator."""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from raveil.affine_fold import reference, compile_region, validate_config


def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()


def verify(root):
    cases=json.loads((root/"vectors.json").read_text())
    by_name={c["name"]:c for c in cases}
    assert len(by_name)==len(cases)
    for c in cases:
        if c["mode"]==10:
            try: validate_config(c["config"])
            except ValueError: pass
            else: raise AssertionError("invalid case admitted")
        else:
            assert compile_region(c["descriptor"])==c["config"]
        assert reference(c["descriptor"],c["inputs"])==c["expected"]
    assert (root/"device.stderr").read_bytes()==b""
    rows=(root/"device.log").read_text().splitlines()
    assert rows[-1]==f"PASS total={3*len(cases)} evidence=RTL-functional-simulation"
    counts={}
    cells=0
    for row in rows[:-1]:
        m=re.fullmatch(r"PASS (1|73|991) (\S+) cells=(\d+) accepted=(\d+) completed=(\d+)",row)
        assert m,row
        seed,name,count,accepted,completed=m.groups()
        key=(int(seed),name)
        assert name in by_name and key not in counts
        c=by_name[name]
        assert int(count)==(len(c["expected"]) if c["mode"] in (0,8) else 0)
        assert accepted==completed
        counts[key]=int(accepted)
        cells+=int(count)
    assert set(counts)=={(s,c["name"]) for s in (1,73,991) for c in cases}
    observed={k:0 for k in counts}
    writes={k:{} for k in counts}
    pending=None
    previous_key=None
    previous_cycle=-1
    with (root/"transactions.txt").open() as f:
        for line in f:
            words=line.split()
            seed,name,kind,cycle=words[:4]
            key=(int(seed),name)
            assert key in counts
            c=by_name[name]
            if key!=previous_key:
                assert pending is None
                previous_key=key;previous_cycle=-1
            assert int(cycle)>previous_cycle
            previous_cycle=int(cycle)
            if kind=="req":
                assert len(words)==7 and pending is None
                write,address,data=map(int,words[4:])
                assert write in (0,1)
                if write:
                    assert 648<=address<648+len(c["expected"])
                else:
                    assert (0<=address<len(c["inputs"][0]) or
                            324<=address<324+len(c["inputs"][1]))
                    assert data==0
                pending=(key,write,address,data)
                observed[key]+=1
            else:
                assert kind=="resp" and len(words)==6 and pending and pending[0]==key
                data,error=map(int,words[4:])
                assert error in (0,1)
                _,write,address,value=pending
                if write:
                    assert data==0
                    if not error:
                        assert address not in writes[key]
                        writes[key][address]=value
                else:
                    buf=0 if address<324 else 1
                    assert data==c["inputs"][buf][address-(324 if buf else 0)]
                pending=None
    assert pending is None and counts==observed
    for key,outputs in writes.items():
        c=by_name[key[1]]
        if c["mode"] in (0,8):
            assert outputs=={648+i:v for i,v in enumerate(c["expected"])}
        if c["mode"] in (1,10):
            assert counts[key]==0
    bound={}
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.name!="verification.json":
            assert not path.is_symlink()
            bound[str(path.relative_to(root))]={"bytes":path.stat().st_size,"sha256":sha(path)}
    return {"evidence_class":"RTL-functional-simulation","executions":len(counts),
            "cell_comparisons":cells,"transactions":sum(counts.values()),"files":bound}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("evidence",type=Path)
    args=p.parse_args()
    print(json.dumps(verify(args.evidence),indent=2,sort_keys=True))
