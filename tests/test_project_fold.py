"""Host fixtures only: these tests do not produce RTL acceptance evidence."""
import copy
import json
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch

from raveil import project as p, project_fold as f
from scripts.affine_fold_vectors import region, binary


class FoldProjectTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.project=p.Project(p.init_project(self.root/"project"))
        self.d=region([1,3],1,[3,3],{"a":[0,0,0,1,0],"b":[1,0,0,1,0]},binary("add"),"x")
        self.data=[[1,2,3],[4,5,6]]
        self.save()
        self.build=self.root/"build";(self.build/"source").mkdir(parents=True)
        for n in f.SOURCES: shutil.copy2(p.REPOSITORY/"hardware/chisel"/n,self.build/"source"/n)
        (self.build/"simulator.bin").write_bytes(b"HOST FIXTURE NOT RTL")
        (self.build/"toolchain.txt").write_text("host fixture")
        (self.build/"rtl").mkdir();(self.build/"rtl"/"fixture.sv").write_text("host fixture")
        f.seal_build(self.build)

    def save(self):
        (self.project.root/"inputs"/"region.json").write_bytes(p.encoded(self.d))
        (self.project.root/"inputs"/"data.json").write_bytes(p.encoded({"schema":"raveil.fold-input/v1","buffers":self.data}))

    def fake(self,root):
        d=json.loads((root/"region.json").read_bytes());data=json.loads((root/"input.json").read_bytes())["buffers"]
        options=json.loads((root/"plan.json").read_bytes())["options"]
        trace=[];reads=writes=count=0;fault=cancel=0;outputs=[]
        for j in range(3):
            for write,address,value in [(0,j,0),(0,324+j,0),(1,648+j,(data[0][j]+data[1][j])&0xffffffff)]:
                count+=1
                error=int(options["fault_at"]==count)
                trace.extend([0,count*2,write,address,value,0])
                response=0 if write else data[0 if address<324 else 1][address%324]
                trace.extend([1,count*2+1,write,address,response,error])
                if write:writes+=1;outputs.append(value)
                else:reads+=1
                fault|=error
                cancel=int(options["cancel_after"]>0 and count>=options["cancel_after"])
                if fault or cancel: break
            if fault or cancel: break
        success=int(not fault and not cancel)
        if success:(root/"device"/"output.bin").write_bytes(struct.pack("<3I",*outputs))
        (root/"device"/"trace.bin").write_bytes(struct.pack("<"+"I"*len(trace),*trace))
        (root/"device"/"device.json").write_bytes(p.encoded(dict(schema="raveil.fold-device/v1",
            success=success,fault=fault,cancelled=cancel,accepted=count,completed=count,reads=reads,writes=writes)))
        return 0 if success else 130 if cancel else 2

    def run_fixture(self,**kwargs):
        with patch.object(f,"_execute",side_effect=self.fake):
            return f.run(self.project,"region.json","data.json",self.build,**kwargs)

    def reseal(self,r):
        root=self.project.root/"folds"/r["id"]
        r["files"]=f._inventory(root)
        (root/"record.json").write_bytes(p.encoded(r))

    def test_preview_no_writes(self):
        before=p.tree(self.project.root)
        self.assertEqual(f.check(self.project,"region.json","data.json")["shape"],[1,3])
        self.assertEqual(before,p.tree(self.project.root))

    def test_frozen_inputs_saved_read_and_diff(self):
        first=self.run_fixture()
        self.data[0][0]=11;self.save();second=self.run_fixture()
        with patch.object(f,"_execute",side_effect=AssertionError("must not run")):
            self.assertEqual(f.load(self.project,first["id"])["output"],[5,7,9])
            self.assertEqual(f.compare(self.project,first["id"],second["id"])["changed_cells"],1)
            self.assertEqual(len(f.history(self.project)),2)

    def test_live_edit_after_capture(self):
        def execute(root):
            (self.project.root/"inputs"/"data.json").write_text("invalid later input")
            return self.fake(root)
        with patch.object(f,"_execute",side_effect=execute):
            record=f.run(self.project,"region.json","data.json",self.build)
        self.assertEqual(record["output"],[5,7,9])

    def test_cancel_error_and_fresh_retry(self):
        for kwargs in (dict(cancel_after=1),dict(fault_at=1),dict(cancel_after=1,fault_at=1)):
            record=self.run_fixture(**kwargs)
            self.assertEqual(record["status"],"incomplete");self.assertIsNone(record["output"])
            self.assertEqual(f.load(self.project,record["id"]),record)
        self.assertEqual(self.run_fixture()["status"],"succeeded")

    def test_precancel_has_no_execution(self):
        with patch.object(f,"_execute",side_effect=AssertionError("must not run")):
            r=f.run(self.project,"region.json","data.json",self.build,cancelled=lambda:True)
        self.assertEqual(r["status"],"incomplete")
        self.assertFalse((self.project.root/"folds"/r["id"]/"device").exists())

    def test_invalid_input_does_not_create_run(self):
        self.data[0]=[True,2,3];self.save()
        with self.assertRaises(ValueError): self.run_fixture()
        self.assertFalse((self.project.root/"folds").exists())

    def test_paths_and_symlinks_rejected(self):
        for path in ("../region.json","/region.json","a/b.json","region.txt"):
            with self.assertRaises(ValueError): f.check(self.project,path,"data.json")
        file=self.project.root/"inputs"/"data.json";file.unlink();file.symlink_to(self.root/"outside")
        with self.assertRaises((ValueError,OSError)):f.check(self.project,"region.json","data.json")

    def test_build_tamper_rejected_before_execution(self):
        (self.build/"simulator.bin").write_bytes(b"changed")
        with self.assertRaises(ValueError):self.run_fixture()
        self.assertFalse((self.project.root/"folds").exists())

    def test_build_drift_during_run_withholds_output(self):
        def execute(root):
            code=self.fake(root);(root/"build"/"simulator.bin").write_bytes(b"changed");return code
        with patch.object(f,"_execute",side_effect=execute):
            r=f.run(self.project,"region.json","data.json",self.build)
        self.assertEqual(r["status"],"incomplete");self.assertIsNone(r["output"])

    def test_resealed_wrong_affine_trace_rejected(self):
        r=self.run_fixture();root=self.project.root/"folds"/r["id"]
        words=list(struct.unpack("<108I",(root/"device"/"trace.bin").read_bytes()))
        words[3]=1;words[9]=1;words[10]=2
        (root/"device"/"trace.bin").write_bytes(struct.pack("<108I",*words));self.reseal(r)
        with self.assertRaisesRegex(ValueError,"affine"):f.load(self.project,r["id"])

    def test_resealed_success_with_response_error_rejected(self):
        r=self.run_fixture();root=self.project.root/"folds"/r["id"]
        data=bytearray((root/"device"/"trace.bin").read_bytes());struct.pack_into("<I",data,44,1)
        (root/"device"/"trace.bin").write_bytes(data);self.reseal(r)
        with self.assertRaises(ValueError):f.load(self.project,r["id"])

    def test_resealed_request_output_and_flag_forgery(self):
        for target in ("request","output","bool","incomplete-device"):
            r=self.run_fixture();root=self.project.root/"folds"/r["id"]
            if target=="request":
                data=bytearray((root/"request.bin").read_bytes());data[-1]^=1;(root/"request.bin").write_bytes(data)
            if target=="output":(root/"device"/"output.bin").write_bytes(b"wrong")
            if target=="bool":r["output"][0]=True
            if target=="incomplete-device":
                device=json.loads((root/"device"/"device.json").read_bytes());device["success"]=0
                (root/"device"/"device.json").write_bytes(p.encoded(device));r["output"]=None
            self.reseal(r)
            with self.subTest(target=target):
                with self.assertRaises(ValueError):f.load(self.project,r["id"])

    def test_cleanup_uncertainty_never_seals_record(self):
        with patch.object(f,"_execute",side_effect=f.CleanupUncertain("test")):
            with self.assertRaises(f.CleanupUncertain):
                f.run(self.project,"region.json","data.json",self.build)
        self.assertEqual(list((self.project.root/"folds").glob("*/record.json")),[])
        self.assertEqual(f.history(self.project)[0]["status"],"unsealed")

    def test_cleanup_timeout_interrupt_and_oserror_are_uncertain(self):
        process=Mock();process.wait.return_value=0;process.poll.return_value=0
        for exc in (subprocess.TimeoutExpired("docker",30),KeyboardInterrupt(),OSError("offline")):
            with patch.object(f.subprocess,"Popen",return_value=process),patch.object(f.subprocess,"run",side_effect=exc):
                with self.assertRaisesRegex(f.CleanupUncertain,"raveil-fold-"):
                    f._container(["docker","run","--rm","image"],stdout=None,stderr=None)

    def test_timeout_removes_container_before_return(self):
        process=Mock();process.wait.side_effect=[subprocess.TimeoutExpired("docker",240),0];process.poll.return_value=None
        with patch.object(f.subprocess,"Popen",return_value=process),patch.object(f.subprocess,"run",return_value=Mock(returncode=0)) as cleanup:
            with self.assertRaises(subprocess.TimeoutExpired):
                f._container(["docker","run","--rm","image"],stdout=None,stderr=None)
        process.kill.assert_called_once();self.assertEqual(cleanup.call_args.args[0][:3],["docker","rm","-f"])

    def test_interrupt_after_publication_preserves_success(self):
        replace=f.os.replace
        def interrupted(src,dst):
            replace(src,dst);raise KeyboardInterrupt()
        with patch.object(f.os,"replace",side_effect=interrupted):
            r=self.run_fixture()
        self.assertEqual(r["status"],"succeeded")

    def test_interrupt_before_publication_leaves_no_success(self):
        with patch.object(f.os,"replace",side_effect=KeyboardInterrupt()):
            with self.assertRaises(KeyboardInterrupt):self.run_fixture()
        self.assertEqual(list((self.project.root/"folds").glob("*/record.json")),[])
        self.assertEqual(f.history(self.project)[0]["status"],"unsealed")

    def test_cli_parser_and_saved_inspection(self):
        import argparse
        parser=argparse.ArgumentParser();p.add_project_parser(parser.add_subparsers())
        args=parser.parse_args(["project","fold-check","--project",str(self.project.root),
                              "--region","region.json","--input","data.json"])
        self.assertEqual(args.project_action,"fold-check")
        r=self.run_fixture()
        args=parser.parse_args(["project","fold",r["id"],"--project",str(self.project.root)])
        with patch("builtins.print"),patch.object(f,"_execute",side_effect=AssertionError()):
            self.assertEqual(p.command_project(args),0)

if __name__=="__main__":unittest.main()
