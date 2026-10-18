"""Acceptance observer must not turn inspection failures into absence evidence."""
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch
from scripts.array_control_acceptance import inspect_resources


def result(stdout='',stderr='',code=0):return subprocess.CompletedProcess([],code,stdout,stderr)

class ResourceAuditTests(unittest.TestCase):
    def audit(self,results):
        with patch('scripts.array_control_acceptance.subprocess.run',side_effect=results):
            return inspect_resources(Path('/owned'))

    def test_empty_listing_and_raw_queries_are_preserved(self):
        value=self.audit([result(),result()]);self.assertEqual(value['containers'],[]);self.assertEqual(value['qemu'],[])
        self.assertEqual(len(value['queries']),2);self.assertEqual(value['queries'][0]['code'],0)

    def test_daemon_inspect_and_process_errors_fail_closed(self):
        cases=[[result(stderr='daemon unavailable',code=1)],
               [result('abc\n'),result(stderr='permission denied',code=1)],
               [result(),result(stderr='process listing denied',code=1)]]
        for case in cases:
            with self.subTest(case=case),self.assertRaises(RuntimeError):self.audit(case)

    def test_disappearing_container_is_distinct_from_transport_error(self):
        value=self.audit([result('abc\n'),result(stderr='error: no such object: abc',code=1),result()])
        self.assertEqual(value['containers'],[]);self.assertEqual(len(value['queries']),3)

    def test_live_owned_resources_and_other_workspaces_are_distinguished(self):
        own=result(json.dumps([dict(Mounts=[dict(Source='/owned/arrays/run/device')])]))
        other=result(json.dumps([dict(Mounts=[dict(Source='/other/arrays/run/device')])]))
        value=self.audit([result('one\ntwo\n'),own,other,result('4 qemu-system-riscv64 /owned/arrays/run/kernel.elf\n5 qemu-system-riscv64 /other/arrays/run/kernel.elf\n')])
        self.assertEqual(value['containers'],['one']);self.assertEqual(len(value['qemu']),1)

    def test_malformed_inspection_is_not_an_empty_result(self):
        with self.assertRaises(ValueError):self.audit([result('abc\n'),result('bad json')])

if __name__=='__main__':unittest.main()
