"""Host-only packaging and relocated launcher acceptance; no device mocks as evidence."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import unittest
from unittest.mock import patch

from raveil import project as p
from scripts.prepare_array_app import prepare
from tests import test_project_array_workspace as workspace_tests
from tests import test_project_dag_batch as fixtures


class LocalAppTests(unittest.TestCase):
    save = fixtures.BatchTests.save

    def setUp(self):
        workspace_tests.PreparedWorkspaceTests.setUp(self)
        self.output = self.root/'app'

    def test_relocated_launcher_uses_own_engine_and_workspace_from_other_cwd(self):
        manifest = prepare(self.output, self.kernel, self.build, self.source)
        moved = self.root/'relocated app'; self.output.rename(moved)
        self.kernel.unlink(); self.source.unlink(); shutil.rmtree(self.build)
        env = dict(os.environ, PYTHONPATH='')
        for args in (['--help'], ['array-check'], ['arrays']):
            result = subprocess.run([str(moved/'raveil'), *args], cwd=self.root, env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            if args == ['array-check']: self.assertEqual(json.loads(result.stdout)['sessions'],1)
            if args == ['arrays']: self.assertEqual(json.loads(result.stdout),[])
        self.assertEqual(manifest['engine'], p.tree(moved/'engine', exclude_root_files=frozenset()))
        self.assertNotIn(str(self.root), (moved/'app.json').read_text())

    def test_no_overwrite_or_incomplete_launcher(self):
        prepare(self.output, self.kernel, self.build, self.source)
        before = p.tree(self.output)
        with self.assertRaises(FileExistsError): prepare(self.output, self.kernel, self.build, self.source)
        self.assertEqual(before, p.tree(self.output))
        (self.output/'app.json').unlink()
        result = subprocess.run([str(self.output/'raveil'),'array-run'], capture_output=True, text=True)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('Incomplete application',result.stderr)
        self.assertFalse((self.output/'workspace/arrays').exists())
        (self.output/'app.json').write_text('{"schema":')
        result = subprocess.run([str(self.output/'raveil'),'array-run'], capture_output=True, text=True)
        self.assertNotEqual(result.returncode,0); self.assertIn('Invalid application marker',result.stderr)
        self.assertFalse((self.output/'workspace/arrays').exists())

    def test_bad_backend_never_commits_app(self):
        (self.build/'simulator.bin').write_bytes(b'bad')
        with self.assertRaises(ValueError): prepare(self.output, self.kernel, self.build, self.source)
        self.assertFalse((self.output/'app.json').exists())

    def test_partial_final_write_never_publishes_application_marker(self):
        original = p.write_new
        def interrupted(path, data, *args, **kwargs):
            if path.name == '.app.pending':
                original(path, data[:12]); raise KeyboardInterrupt()
            return original(path, data, *args, **kwargs)
        with patch.object(p, 'write_new', side_effect=interrupted), self.assertRaises(KeyboardInterrupt):
            prepare(self.output, self.kernel, self.build, self.source)
        self.assertTrue((self.output/'.app.pending').is_file())
        self.assertFalse((self.output/'app.json').exists())
        result = subprocess.run([str(self.output/'raveil'),'array-run'],capture_output=True,text=True)
        self.assertNotEqual(result.returncode,0); self.assertIn('Incomplete application',result.stderr)
        self.assertFalse((self.output/'workspace/arrays').exists())


if __name__ == '__main__':
    unittest.main()
