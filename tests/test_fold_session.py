import copy
import ctypes as C
import struct
import unittest
import zlib
from raveil import fold_bridge as bridge,fold_session as s
from scripts.affine_fold_vectors import vectors
from tests import test_sonatine_fold as contract_tests


def session(count=1):
    v=vectors()[0]
    return {"schema":"raveil.fold-session.v1","jobs":[
        {"name":f"job-{i}","region":copy.deepcopy(v["descriptor"]),"inputs":copy.deepcopy(v["inputs"])}
        for i in range(count)]}


class Session(C.Structure):
    _fields_=[("epoch",C.c_uint64),("count",C.c_uint32),
              ("offsets",C.c_uint32*8),("lengths",C.c_uint32*8)]


class SessionCodecTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        contract_tests.FoldContractTests.setUpClass.__func__(cls)
        cls.lib.raveil_fold_session_decode.argtypes=[C.c_void_p,C.c_size_t,C.POINTER(Session)]
        cls.lib.raveil_fold_session_decode.restype=C.c_bool
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def decode(self,blob):
        value=Session()
        return self.lib.raveil_fold_session_decode(blob,len(blob),C.byref(value)),value
    def test_one_through_eight_jobs_and_maximum_envelope(self):
        for count in range(1,9):
            d=session(count)
            for job in d["jobs"]:
                job["region"]["lengths"]=[324,324];job["inputs"]=[list(range(324)),list(range(324))]
            blob,children=s.encode(d,99,list(range(1,count+1)))
            ok,value=self.decode(blob);self.assertTrue(ok);self.assertEqual(value.count,count)
            self.assertEqual(value.epoch,99);offset=24
            for i,child in enumerate(children):
                self.assertEqual(value.offsets[i],offset);self.assertEqual(value.lengths[i],len(child));offset+=len(child)
            self.assertEqual(len(blob),32+count*2892)
    def test_every_truncation_and_single_byte_corruption(self):
        blob,_=s.encode(session(),99,[1])
        for n in range(len(blob)):
            self.assertFalse(self.decode(blob[:n])[0])
        for i in range(len(blob)):
            bad=bytearray(blob);bad[i]^=1
            self.assertFalse(self.decode(bytes(bad))[0])
    def test_recomputed_outer_crc_does_not_bypass_admission(self):
        blob,children=s.encode(session(2),99,[1,2])
        for offset,value in ((4,2),(12,0),(12,9),(16,0),(24,0),(32,2892)):
            bad=bytearray(blob);struct.pack_into("<I",bad,offset,value)
            struct.pack_into("<I",bad,len(bad)-8,zlib.crc32(bad[:-8]))
            self.assertFalse(self.decode(bytes(bad))[0],offset)
        # Duplicate a valid complete request, including its valid inner CRC.
        bad=bytearray(blob);start=24+len(children[0]);bad[start:start+len(children[1])]=children[0]
        struct.pack_into("<I",bad,len(bad)-8,zlib.crc32(bad[:-8]))
        self.assertFalse(self.decode(bytes(bad))[0])
    def test_host_rejects_ninth_duplicate_or_invalid_job(self):
        for d in (session(0),session(9)):
            with self.assertRaises(ValueError):s.validate(d)
        d=session(2);d["jobs"][1]["name"]=d["jobs"][0]["name"]
        with self.assertRaises(ValueError):s.validate(d)
        with self.assertRaises(ValueError):s.encode(session(2),99,[1,1])
        with self.assertRaises(ValueError):s.encode(session(),True,[1])
    def test_replay_requires_previous_success_and_equal_response_extent(self):
        with self.assertRaises(ValueError):s.options(session(),["replay-previous"])
        with self.assertRaises(ValueError):s.options(session(2),["fault","replay-previous"])
        self.assertEqual(s.options(session(2),["none","replay-previous"]),["none","replay-previous"])
        d=session(2);v=next(v for v in vectors() if v["name"]=="mul-16x16")
        d["jobs"][1]["region"]=v["descriptor"];d["jobs"][1]["inputs"]=v["inputs"]
        with self.assertRaises(ValueError):s.options(d,["none","replay-previous"])


class SessionTranscriptTests(unittest.TestCase):
    def step(self,*,index=1,success=True,previous=None):
        d=session()["jobs"][0];request=bridge.request_bytes(s.compile_region(d["region"]),d["inputs"],2)
        expected=[5];inj="none" if success else "wrong-word";previous=previous or [7]*256
        first=("RAVEIL-FOLD-DISPATCH-V1 request=0000000000000002 epoch=0000000000000063 "
               f"sequence={index+1:016x} cookie="+"12"*16+" count=1 envelope="+request.hex())
        version=3 if success else 2;content=([5]+[0]*255) if success else previous
        state=(f"RAVEIL-FOLD-SESSION-STATE-V1 index={index} stable=1 framed=1 version={version} "
               f"ledger={index+1} submissions=0 inflight=0 shadows=0 completions=0 content="+
               "".join(f"{v:08x}" for v in content))
        result=(f"RAVEIL-FOLD-SESSION-RESULT-V1 index={index} request=0000000000000002 "
                f"epoch=0000000000000063 sequence={index+1} cookie="+"12"*16+
                f" status={1 if success else 4} approved={int(success)} version={version} "+
                ("count=1 output=00000005" if success else "count=0 output=-"))
        return [first,">>",state,result],(index,request,2,99,expected,b"aa",inj,2,previous)
    def test_success_padding_and_failure_preserve_all_previous_words(self):
        for success in (True,False):
            lines,args=self.step(success=success)
            _,result,content=s.check_step(lines,*args)
            self.assertEqual(result["approved"],success)
            self.assertEqual(content,[5]+[0]*255 if success else [7]*256)
            bad=lines.copy();bad[2]=bad[2][:-8]+"00000009"
            with self.assertRaises(ValueError):s.check_step(bad,*args)
    def test_reordered_binding_version_ledger_and_pending_state_rejected(self):
        for success in (True,False):
            lines,args=self.step(success=success)
            edits=[(0,"sequence=0000000000000002","sequence=0000000000000001"),
                   (3,"cookie="+"12"*16,"cookie="+"34"*16),
                   (2,"ledger=2","ledger=1"),(2,"inflight=0","inflight=1"),
                   (3,"version=3" if success else "version=2","version=9")]
            for pos,old,new in edits:
                bad=lines.copy();bad[pos]=bad[pos].replace(old,new)
                with self.assertRaises(ValueError):s.check_step(bad,*args)
            with self.assertRaises(ValueError):s.check_step([lines[0],lines[2],lines[1],lines[3]],*args)
