import copy
import ctypes as C
import json
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import zlib
from raveil.sonatine_fold import encode, parse, run, verify, digest
from scripts.affine_fold_vectors import vectors

ROOT=Path(__file__).resolve().parents[1]
class Request(C.Structure):
    _fields_=[("request_id",C.c_uint64),("config",C.c_uint32*65),("inputs",C.c_uint32*648)]


class FoldContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        library=Path(cls.tmp.name)/"fold.so"
        subprocess.run(["cc","-std=c11","-Wall","-Wextra","-Werror","-shared","-fPIC",
                        "-Icontracts/include","contracts/src/affine_fold.c","-o",str(library)],
                       cwd=ROOT,check=True)
        cls.lib=C.CDLL(str(library))
        cls.lib.raveil_fold_decode.argtypes=[C.c_void_p,C.c_size_t,C.POINTER(Request)]
        cls.lib.raveil_fold_decode.restype=C.c_bool
        cls.lib.raveil_fold_evaluate.argtypes=[C.POINTER(Request),C.POINTER(C.c_uint32)]
        cls.lib.raveil_fold_evaluate.restype=C.c_bool
        cls.lib.raveil_fold_validate.argtypes=[C.POINTER(C.c_uint32)]
        cls.lib.raveil_fold_validate.restype=C.c_bool

    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()

    def test_full_c_interpreter_against_direct_formula_vectors(self):
        for case in vectors():
            if case["mode"] != 0:continue
            with self.subTest(case=case["name"]):
                blob=encode(case["config"],case["inputs"],0xfedcba9876543210)
                request=Request();out=(C.c_uint32*256)()
                self.assertTrue(self.lib.raveil_fold_decode(blob,len(blob),C.byref(request)))
                self.assertTrue(self.lib.raveil_fold_evaluate(C.byref(request),out))
                self.assertEqual(list(out)[:len(case["expected"])],case["expected"])

    def test_all_invalid_configuration_vectors(self):
        for case in vectors():
            if case["mode"]==10:
                with self.subTest(case=case["name"]):
                    self.assertFalse(self.lib.raveil_fold_validate((C.c_uint32*65)(*case["config"])))

    def test_every_transport_truncation_and_single_byte_corruption(self):
        case=vectors()[0];blob=encode(case["config"],case["inputs"],7)
        request=Request()
        for size in range(len(blob)):
            self.assertFalse(self.lib.raveil_fold_decode(blob,size,C.byref(request)))
        for i in range(len(blob)):
            bad=bytearray(blob);bad[i]^=1;bad=bytes(bad)
            self.assertFalse(self.lib.raveil_fold_decode(bad,len(bad),C.byref(request)))

    def test_recomputed_crc_does_not_bypass_admission(self):
        case=vectors()[0];blob=encode(case["config"],case["inputs"],7)
        for offset,value in ((4,2),(8,len(blob)+4),(12,324),(20,1),(24,0),(32,0)):
            with self.subTest(offset=offset):
                bad=bytearray(blob);struct.pack_into("<I",bad,offset,value)
                struct.pack_into("<I",bad,len(bad)-8,zlib.crc32(bad[:-8]))
                request=Request()
                self.assertFalse(self.lib.raveil_fold_decode(bytes(bad),len(bad),C.byref(request)))

    def test_maximum_request_bytes(self):
        case=copy.deepcopy(vectors()[0]);case["config"][5:7]=[324,324]
        case["inputs"]=[list(range(324)),list(range(324))]
        blob=encode(case["config"],case["inputs"],7)
        self.assertEqual(len(blob),2892)
        request=Request()
        self.assertTrue(self.lib.raveil_fold_decode(blob,len(blob),C.byref(request)))


class ResultTests(unittest.TestCase):
    def line(self,count=1):
        return ("RAVEIL-FOLD-RESULT-V1 request=0000000000000007 status=1 approved=1 "
                "epoch=7 sequence=1 cookie=00000000000000000000000000000001 "
                f"chunks={(count+127)//128} version=2 count={count} output="+"ffffffff"*count)

    def test_full_output_and_chunk_boundary(self):
        for n in (1,128,129,256):
            self.assertEqual(parse(self.line(n),7,n)["output"],[0xffffffff]*n)

    def test_missing_duplicate_stale_partial_and_contradictory_frames(self):
        line=self.line()
        variants=["",line+"\n"+line,line[:-1],line.replace("epoch=7","epoch=8"),
                  line.replace("sequence=1","sequence=2"),line.replace("chunks=1","chunks=2"),
                  line.replace("version=2","version=0"),line.replace("approved=1","approved=0"),
                  line.replace("status=1","status=2"),line+" unexpected=1",
                  line.replace("0000000000000007","0000000000000008"),
                  line.replace("00000000000000000000000000000001","0"*32)]
        for bad in variants:
            with self.subTest(frame=bad):
                with self.assertRaises(ValueError):parse(bad,7,1)

    def test_rejection_is_never_a_success(self):
        line=("RAVEIL-FOLD-RESULT-V1 request=0000000000000007 status=2 approved=0 "
              "epoch=0 sequence=0 cookie="+"0"*32+" chunks=0 version=0 count=0 output=-")
        self.assertFalse(parse(line,7,1)["approved"])
        with self.assertRaises(ValueError):parse(line.replace("output=-","output=00000000"),7,1)


class ReceiptTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.kernel=self.root/"source.elf"
        self.kernel.write_bytes(b"host fixture, not real QEMU evidence")
        self.case=vectors()[0]

    def fake_run(self,command,**kwargs):
        directory=Path(command[command.index("-kernel")+1]).parent
        request_id=struct.unpack_from("<Q",(directory/"request.bin").read_bytes(),24)[0]
        output=self.case["expected"]
        line=(f"RAVEIL-FOLD-RESULT-V1 request={request_id:016x} status=1 approved=1 "
              f"epoch={request_id} sequence=1 cookie="+"1"*32+
              f" chunks=1 version=2 count=1 output={output[0]:08x}\n")
        return subprocess.CompletedProcess(command,0,line.encode(),b"")

    def fixture(self):
        target=self.root/"run"
        with patch("raveil.sonatine_fold.shutil.which",return_value="/fixture/qemu"),\
             patch("raveil.sonatine_fold.subprocess.check_output",return_value="fixture version\n"),\
             patch("raveil.sonatine_fold.subprocess.run",side_effect=self.fake_run):
            run(self.case["descriptor"],self.case["inputs"],self.kernel,target)
        verify(target)
        return target

    def test_no_relabeling_or_extra_claims(self):
        target=self.fixture();original=(target/"receipt.json").read_text()
        for key,value in (("evidence_class","fpga"),("qemu_version","fiction"),("extra_claim",True)):
            receipt=json.loads(original);receipt[key]=value
            (target/"receipt.json").write_text(json.dumps(receipt))
            with self.assertRaises(ValueError):verify(target)

    def test_changed_command_even_if_rehashed_is_rejected(self):
        target=self.fixture()
        command=json.loads((target/"command.json").read_text())
        command[command.index("128M")]="256M"
        (target/"command.json").write_text(json.dumps(command))
        receipt=json.loads((target/"receipt.json").read_text())
        receipt["files"]["command.json"]=digest(target/"command.json")
        (target/"receipt.json").write_text(json.dumps(receipt))
        with self.assertRaises(ValueError):verify(target)

    def test_modified_inputs_and_kernel_rejected(self):
        target=self.fixture()
        for name in ("inputs.json","kernel.elf","stdout.log"):
            original=(target/name).read_bytes();(target/name).write_bytes(original+b"x")
            with self.assertRaises(ValueError):verify(target)
            (target/name).write_bytes(original)

    def test_timeout_retains_partial_output_without_receipt(self):
        target=self.root/"timeout"
        with patch("raveil.sonatine_fold.shutil.which",return_value="/fixture/qemu"),\
             patch("raveil.sonatine_fold.subprocess.check_output",return_value="fixture version\n"),\
             patch("raveil.sonatine_fold.subprocess.run",
                   side_effect=subprocess.TimeoutExpired("fixture",1,output=b"partial",stderr=b"err")):
            with self.assertRaises(subprocess.TimeoutExpired):
                run(self.case["descriptor"],self.case["inputs"],self.kernel,target)
        self.assertFalse((target/"receipt.json").exists())
        self.assertEqual((target/"stdout.log").read_bytes(),b"partial")
