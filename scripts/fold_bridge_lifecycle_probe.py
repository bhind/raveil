#!/usr/bin/env python3
"""Actual new-boot replay and host deadline cleanup; no success receipt forged."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from raveil import fold_bridge as bridge
from raveil.sonatine_fold import digest


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source",type=Path,required=True)
    parser.add_argument("--kernel",type=Path,required=True)
    parser.add_argument("--build",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args();root=args.output.resolve();root.mkdir(parents=True,exist_ok=False)
    previous=bridge.verify(args.source)
    if not previous["result"]["approved"]:raise ValueError("successful old session required")
    descriptor=json.loads((args.source/"region.json").read_text())
    inputs=json.loads((args.source/"inputs.json").read_text())
    old_response=(args.source/"response.bin").read_bytes()
    target=root/"replay"
    # Wire substitution is an adversarial test hook. The normal receipt verifier
    # must reject it; independently inspect the actual guest rejection.
    response_function=bridge.injected_response;calls=0
    def replay_once(*a,**kw):
        nonlocal calls
        calls+=1
        if calls==1:return old_response,old_response.hex().encode()
        return response_function(*a,**kw)
    with patch.object(bridge,"injected_response",side_effect=replay_once):
        try:bridge.run(descriptor,inputs,args.kernel,args.build,target,injection="stale-id")
        except ValueError as exc:
            if str(exc)!="UART response mismatch":raise
        else:raise AssertionError("unexpected success receipt")
    if (target/"receipt.json").exists():raise AssertionError("replay sealed a receipt")
    binding=json.loads((target/"dispatch.json").read_text())
    if binding["request_id"]==previous["request_id"]:raise AssertionError("boot identity reused")
    _,result=bridge.validate_transcript((target/"stdout.log").read_text(),
        (target/"request.bin").read_bytes(),binding["request_id"],binding["count"],
        old_response.hex().encode(),"stale-id")
    if result["approved"] or result["status"]!=4:raise AssertionError("old session response accepted")
    # Exercise a real host-side deadline and verify subprocess termination.
    processes=[];original=subprocess.Popen
    def capture(*a,**kw):
        process=original(*a,**kw);processes.append(process);return process
    target=root/"deadline"
    with patch.object(bridge.subprocess,"Popen",side_effect=capture):
        try:bridge.run(descriptor,inputs,args.kernel,args.build,target,timeout=0.000001)
        except TimeoutError:pass
        else:raise AssertionError("deadline did not expire")
    if (target/"receipt.json").exists():raise AssertionError("timeout sealed a receipt")
    guests=[process for process in processes if "-machine" in process.args]
    if len(guests)!=1 or any(process.poll() is None for process in processes):
        raise AssertionError("unreaped guest process")
    report=dict(evidence_class="host-mediated-QEMU-RTL-functional-coupling",
                old_receipt=str((args.source/"receipt.json").resolve()),
                old_receipt_sha256=digest(args.source/"receipt.json"),
                old_request_id=previous["request_id"],new_request_id=binding["request_id"],
                replay_rejected=True,guest_output=result["output"],
                deadline_guest_returncode=guests[0].returncode,
                no_success_receipts=True)
    (root/"probe.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report))


if __name__=="__main__":main()
