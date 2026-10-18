"""Host fixtures for prepared workspaces; actual relocation is a separate check."""
import contextlib
import csv
import io
import json
from pathlib import Path
import shutil
import subprocess
import unittest
from unittest.mock import patch

from raveil import project as p, project_array as a, project_array_workspace as w
from raveil import fold_dag as d, project_fold as f
from raveil.cli import main
from tests import test_project_dag_batch as fixtures
from tests.test_array_program import program


class PreparedWorkspaceTests(unittest.TestCase):
    save = fixtures.BatchTests.save
    fake = fixtures.BatchTests.fake

    def setUp(self):
        fixtures.BatchTests.setUp(self)
        self.source = self.root/'source.json'
        value = program(); value['schema'] = 'raveil.array-program/v2'
        self.source.write_bytes(p.encoded(value))
        self.destination = self.root/'prepared'

    def prepare(self):
        w.prepare(self.destination, self.kernel, self.build, self.source)
        return p.Project(self.destination)

    def execute(self, project, failed=False):
        kernel, build = w.resolve(project)
        with patch.object(d, 'run', side_effect=lambda *args: self.fake(*args, failed=0 if failed else None)):
            return a.run(project, 'program.json', kernel, build)

    def test_snapshot_relocates_and_original_paths_are_unnecessary(self):
        project = self.prepare(); snapshot = p.tree(project.root)
        moved = self.root/'moved workspace'; project.root.rename(moved)
        self.kernel.unlink(); self.source.unlink(); shutil.rmtree(self.build)
        project = p.Project(moved)
        self.assertEqual(snapshot, p.tree(project.root))
        kernel, build = w.resolve(project)
        self.assertTrue(kernel.is_relative_to(moved.resolve())); self.assertTrue(build.is_relative_to(moved.resolve()))
        self.assertNotIn(str(self.root), (moved/w.FOLDER/'environment.json').read_text())
        record = self.execute(project)
        self.assertEqual(record['outputs'][0]['words'], [3, 4, 5, 6, 7, 8])

    def test_kernel_or_runtime_damage_rejects_before_attempt(self):
        project = self.prepare()
        for name in ('kernel.elf', 'runtime/simulator.bin', 'runtime/source/'+f.SOURCES[0]):
            path = project.root/w.FOLDER/name; raw = path.read_bytes(); path.write_bytes(raw+b'changed')
            with patch.object(a, 'run', side_effect=AssertionError('damaged backend dispatched')):
                with contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(main(['project', 'array-run', '--project', str(project.root)]), 2)
            self.assertNotIn('arrays', project.workspace.ls('/')); path.write_bytes(raw)

    def test_manifest_fields_and_symlinks_reject(self):
        project = self.prepare(); root = project.root/w.FOLDER
        manifest = root/'environment.json'; raw = manifest.read_bytes()
        for value in ([], dict(json.loads(raw), kernel='/outside'), {'schema': w.SCHEMA}):
            manifest.write_bytes(p.encoded(value))
            with self.assertRaises(ValueError): w.backend(project)
        manifest.write_bytes(raw)
        kernel = root/'kernel.elf'; kernel.unlink(); kernel.symlink_to(self.kernel)
        with self.assertRaises(ValueError): w.backend(project)
        kernel.unlink(); kernel.write_bytes(self.kernel.read_bytes())
        saved = self.root/'backend'; root.rename(saved); root.symlink_to(saved, target_is_directory=True)
        with self.assertRaises(ValueError): w.backend(project)

    def test_preparation_rejects_bad_input_or_build_without_creating_workspace(self):
        raw = self.source.read_bytes(); self.source.write_text('{"schema":null}')
        with self.assertRaises(ValueError): self.prepare()
        self.assertFalse(self.destination.exists()); self.source.write_bytes(raw)
        (self.build/'simulator.bin').write_bytes(b'bad')
        with self.assertRaises(ValueError): self.prepare()
        self.assertFalse(self.destination.exists())

    def test_no_overwrite_and_comma_path_rejected(self):
        project = self.prepare(); before = p.tree(project.root)
        with self.assertRaises(ValueError): self.prepare()
        self.assertEqual(before, p.tree(project.root))
        target = self.root/'bad,path'
        with self.assertRaisesRegex(ValueError, 'comma'):
            w.prepare(target, self.kernel, self.build, self.source)
        self.assertFalse(target.exists())

    def test_interrupted_preparation_has_no_environment_commit(self):
        original = p.write_new
        def interrupt(path, data, *args, **kwargs):
            if path.name == 'environment.json': raise KeyboardInterrupt()
            return original(path, data, *args, **kwargs)
        with patch.object(p, 'write_new', side_effect=interrupt), self.assertRaises(KeyboardInterrupt):
            self.prepare()
        project = p.Project(self.destination)
        self.assertFalse((project.root/w.FOLDER/'environment.json').exists())
        with self.assertRaises(ValueError): w.backend(project)
        with self.assertRaises(ValueError): self.prepare()

    def test_changed_copy_is_rejected_before_manifest(self):
        original = p.tree
        def changed(root, destination=None, **kwargs):
            result = original(root, destination, **kwargs)
            if destination is not None:
                (destination/'simulator.bin').write_bytes(b'changed during copy')
            return result
        with patch.object(p, 'tree', side_effect=changed), self.assertRaises(ValueError): self.prepare()
        self.assertFalse((self.destination/w.FOLDER/'environment.json').exists())

    def test_explicit_pair_preserved_and_mixed_selection_rejected(self):
        self.assertEqual(w.resolve(self.project, 'a', 'b'), (Path('a'), Path('b')))
        for kernel, build in [('a', None), (None, 'b')]:
            with self.assertRaisesRegex(ValueError, 'both'): w.resolve(self.project, kernel, build)
        with self.assertRaisesRegex(ValueError, 'array-prepare'): w.resolve(self.project)

    def test_doctor_readonly_success_missing_tools_and_timeout(self):
        project = self.prepare(); before = p.tree(project.root)
        def run(command, **kwargs):
            self.assertEqual(kwargs['timeout'], 15)
            text = f.IMAGE+'\n' if command[0].endswith('docker') else 'QEMU version fixture\n'
            return subprocess.CompletedProcess(command, 0, text, '')
        with patch.object(w.shutil, 'which', side_effect=lambda n: '/tools/'+n), patch.object(w.subprocess, 'run', side_effect=run) as calls:
            self.assertTrue(w.doctor(project)['ready'])
            self.assertEqual(calls.call_args_list[1].args[0][1:], ['image', 'inspect', '--format', '{{.Id}}', f.IMAGE])
        with patch.object(w.shutil, 'which', return_value=None), patch.object(w.subprocess, 'run', side_effect=AssertionError('missing tool executed')):
            result = w.doctor(project); self.assertFalse(result['ready'])
            self.assertEqual(sum(not row['ok'] for row in result['checks']), 2)
        with patch.object(w.shutil, 'which', return_value='/tools/fake'), patch.object(w.subprocess, 'run', side_effect=subprocess.TimeoutExpired('probe', 15)):
            self.assertFalse(w.doctor(project)['ready'])
        self.assertEqual(before, p.tree(project.root))

    def test_doctor_missing_runtime_and_wrong_image(self):
        with patch.object(w.shutil, 'which', return_value='/tools/fake'), patch.object(w.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, 'wrong image', '')):
            result = w.doctor(self.project)
        self.assertFalse(result['ready'])
        self.assertFalse(next(x for x in result['checks'] if x['name'] == 'prepared-runtime')['ok'])
        self.assertFalse(next(x for x in result['checks'] if x['name'] == 'docker')['ok'])

    def test_verified_json_csv_after_runtime_removed_and_relocation(self):
        project = self.prepare(); record = self.execute(project); identity = record['id']
        saved = p.tree(project.root/'arrays'/identity)
        shutil.rmtree(project.root/w.FOLDER)
        moved = self.root/'after execution'; project.root.rename(moved); project = p.Project(moved)
        with patch('subprocess.Popen', side_effect=AssertionError('saved output executed')):
            value = json.loads(w.output(project)); self.assertEqual(value['outputs'], record['outputs'])
            rows = list(csv.DictReader(io.StringIO(w.output(project, identity, 'answer', 'csv'))))
            self.assertEqual([int(r['value']) for r in rows], [3, 4, 5, 6, 7, 8])
            self.assertEqual([(int(r['row']), int(r['column'])) for r in rows], [(0,0),(0,1),(0,2),(1,0),(1,1),(1,2)])
            with self.assertRaises(ValueError): w.output(project, identity, 'missing')
            with self.assertRaises(ValueError): w.output(project, identity, format='xml')
        self.assertEqual(saved, p.tree(project.root/'arrays'/identity))

    def test_incomplete_tampered_unsealed_and_ambiguous_latest_never_export(self):
        project = self.prepare()
        with self.assertRaisesRegex(ValueError, 'no array'): w.output(project)
        failed = self.execute(project, failed=True)
        with self.assertRaisesRegex(ValueError, 'incomplete'): w.output(project, failed['id'])
        with self.assertRaisesRegex(ValueError, 'incomplete'): w.output(project)
        peer = failed['id'].split('-', 1)[0]+'-unsealed'; (project.root/'arrays'/peer).mkdir()
        with self.assertRaisesRegex(ValueError, 'multiple attempts'): w.output(project)
        with self.assertRaises(ValueError): w.output(project, peer)
        record = self.execute(project); path = project.root/'arrays'/record['id']/'record.json'
        path.write_bytes(path.read_bytes()+b' ')
        with self.assertRaises(ValueError): w.output(project, record['id'])

    def test_cli_prepare_defaults_run_output_and_failure_codes(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(main(['project','array-prepare',str(self.destination),'--kernel',str(self.kernel),'--build',str(self.build),'--source',str(self.source)]),0)
        self.assertEqual(json.loads(out.getvalue())['input'], 'program.json')
        argv = ['--project', str(self.destination)]
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(main(['project','array-check',*argv]),0)
        with patch.object(d, 'run', side_effect=self.fake), contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(main(['project','array-run',*argv,'--summary']),0)
        self.assertEqual(set(json.loads(out.getvalue())), {'id','status','evidence_class','outputs'})
        identity = json.loads(out.getvalue())['id']
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(main(['project','array-output',identity,*argv,'--format','csv']),0)
        self.assertTrue(out.getvalue().startswith('output,row,column,value\n'))
        with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(main(['project','array-output',identity,*argv,'--name','missing']),2)
        self.assertEqual(out.getvalue(),'')
        with patch.object(w.shutil, 'which', return_value=None), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(['project','array-doctor',*argv]),2)


if __name__ == '__main__':
    unittest.main()
