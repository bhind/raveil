import ctypes as C
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
import zlib
from raveil.fold_bridge import request_bytes,response_bytes,dispatch,injected_response,validate_transcript,verify_rtl_fault
from raveil import project_fold as f
from scripts.affine_fold_vectors import vectors
from tests import test_sonatine_fold as contract_tests


class BridgeResponseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        contract_tests.FoldContractTests.setUpClass.__func__(cls)
        cls.lib.raveil_fold_response_decode.argtypes=[
            C.c_void_p,C.c_size_t,C.c_uint64,C.c_uint64,C.c_uint64,C.c_void_p,C.c_uint32,C.c_void_p]
        cls.lib.raveil_fold_response_decode.restype=C.c_bool
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def binding(self,n):return dict(request_id=7,epoch=7,sequence=1,cookie="12"*16,count=n)
    def decode(self,blob,n):
        out=(C.c_uint32*256)(*([0xdeadbeef]*256))
        ok=self.lib.raveil_fold_response_decode(blob,len(blob),7,7,1,bytes.fromhex("12"*16),n,out)
        return ok,list(out)
    def test_all_output_capacities_and_max_frame(self):
        for n in (1,128,129,256):
            data=[0xffffffff-i for i in range(n)];blob=response_bytes(self.binding(n),data)
            ok,out=self.decode(blob,n);self.assertTrue(ok);self.assertEqual(out[:n],data)
            self.assertEqual(len(blob),60+4*n)
    def test_all_truncations_and_corruptions_leave_output_private(self):
        blob=response_bytes(self.binding(1),[5])
        bad=[blob[:i] for i in range(len(blob))]
        for i in range(len(blob)):
            m=bytearray(blob);m[i]^=1;bad.append(bytes(m))
        for m in bad:
            ok,out=self.decode(m,1);self.assertFalse(ok);self.assertEqual(out,[0xdeadbeef]*256)
    def test_valid_crc_stale_binding_or_fault_rejected(self):
        blob=response_bytes(self.binding(1),[5])
        for offset in (0,4,8,16,24,32,48,52):
            m=bytearray(blob);m[offset]^=1;struct.pack_into("<I",m,len(m)-4,zlib.crc32(m[:-4]))
            ok,out=self.decode(bytes(m),1);self.assertFalse(ok);self.assertEqual(out,[0xdeadbeef]*256)
    def test_injection_helper_does_not_mutate_input_binding(self):
        binding=self.binding(1);output=[5]
        for injection in ("none","wrong-word","stale-id","bad-crc","fault","invalid-char","no-response","truncated"):
            blob,wire=injected_response(binding,output,injection)
            self.assertEqual(binding,self.binding(1));self.assertEqual(output,[5])
            if injection=="no-response":self.assertEqual(wire,b"")
            elif injection=="truncated":self.assertEqual(wire,blob.hex().encode()[:-1])


class DispatchTests(unittest.TestCase):
    def test_guest_request_and_binding_must_match_frozen_boot_bytes(self):
        case=vectors()[0];blob=request_bytes(case["config"],case["inputs"],7)
        line=("RAVEIL-FOLD-DISPATCH-V1 request=0000000000000007 epoch=0000000000000007 "
              "sequence=0000000000000001 cookie="+"12"*16+" count=1 envelope="+blob.hex())
        self.assertEqual(dispatch(line,blob,7,1)["request_id"],7)
        for bad in (line[:-1],line+" x=1",line.replace("count=1","count=2"),
                    line.replace("epoch=0000000000000007","epoch=0000000000000008"),
                    line.replace("sequence=0000000000000001","sequence=0000000000000002"),
                    line.replace("cookie="+"12"*16,"cookie="+"0"*32)):
            with self.assertRaises(ValueError):dispatch(bad,blob,7,1)

    def test_phase_order_and_final_binding_on_success_and_fault(self):
        case=vectors()[0];request=request_bytes(case["config"],case["inputs"],7)
        first=("RAVEIL-FOLD-DISPATCH-V1 request=0000000000000007 epoch=0000000000000007 "
               "sequence=0000000000000001 cookie="+"12"*16+" count=1 envelope="+request.hex())
        for injection in ("none","wrong-word"):
            success=injection=="none"
            state=f"RAVEIL-FOLD-BRIDGE-STATE-V1 stable=1 objects=1 version={2 if success else 1} inflight=0 shadows=0 completions=0"
            last=("RAVEIL-FOLD-RESULT-V1 request=0000000000000007 "
                  f"status={1 if success else 4} approved={int(success)} epoch=7 sequence=1 cookie="+"12"*16+
                  (" chunks=1 version=2 count=1 output=00000005" if success else " chunks=0 version=0 count=0 output=-"))
            lines=[first,">>",state,last];stdout="boot\n"+"\n".join(lines)+"\n"
            validate_transcript(stdout,request,7,1,b"00",injection)
            corrupt=["\n".join([last,">>",state,first]),"\n".join([first,state,">>",last]),
                     stdout.replace(last,last.replace("cookie="+"12"*16,"cookie="+"34"*16)),
                     stdout.replace(last,last.replace("epoch=7","epoch=8")),
                     stdout.replace(last,last.replace("sequence=1","sequence=2"))]
            for bad in corrupt:
                with self.assertRaises(ValueError):validate_transcript(bad,request,7,1,b"00",injection)


class FaultEvidenceTests(unittest.TestCase):
    def test_incomplete_without_actual_drained_error_trace_is_not_rtl_fault(self):
        case=vectors()[0];options={"seed":213,"cancel_after":0,"fault_at":1}
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/"device").mkdir()
            (root/"plan.json").write_text(json.dumps(dict(options=options,build_sha256="fixture")))
            (root/"request.bin").write_bytes(f._request(case["descriptor"],case["inputs"],**options))
            device=dict(schema="raveil.fold-device/v1",success=0,fault=1,cancelled=0,
                        accepted=1,completed=1,writes=0,reads=1)
            (root/"device"/"device.json").write_text(json.dumps(device))
            trace=struct.pack("<12I",0,1,0,0,0,0,1,2,0,0,case["inputs"][0][0],1)
            (root/"device"/"trace.bin").write_bytes(trace)
            with patch.object(f,"verify_build",return_value="fixture"):
                verify_rtl_fault(root,case["descriptor"],case["inputs"])
                (root/"device"/"trace.bin").unlink()
                with self.assertRaises((ValueError,FileNotFoundError)):
                    verify_rtl_fault(root,case["descriptor"],case["inputs"])
                (root/"device"/"trace.bin").write_bytes(trace[:-24])
                with self.assertRaises(ValueError):
                    verify_rtl_fault(root,case["descriptor"],case["inputs"])
