"""Image command orchestration with sealed host fixtures, not runtime evidence."""
import contextlib
import io
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import unittest
from unittest.mock import patch
from raveil import project as p, project_array as a, fold_dag as d, run_control
from scripts import image_demo_cli as cli, image_demo as image
from tests import test_project_dag_batch as fixtures


class ImageCommandTests(unittest.TestCase):
    save = fixtures.BatchTests.save
    fake = fixtures.BatchTests.fake

    def setUp(self):
        fixtures.BatchTests.setUp(self)
        self.pixels = [[10,20,5,0],[0,0,255,255]]
        self.image = self.root/'input.pgm'
        self.image.write_bytes(image.pgm(self.pixels))
        self.output = self.root/'image app'

    def invoke(self, output=None, extra=()):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = cli.main(['run', '--image', str(self.image), '--output', str(output or self.output),
                             '--kernel', str(self.kernel), '--build', str(self.build), *extra])
        return code, stdout.getvalue(), stderr.getvalue()

    def successful(self, output=None):
        with patch.object(d, 'run', side_effect=self.fake):
            code, out, err = self.invoke(output)
        self.assertEqual(code, 0, err)
        result = json.loads(out)
        project = p.Project(Path(result['directory'])/'app/workspace')
        self.assertEqual(a.load(project, result['id'])['outputs'], image.reference(self.pixels))
        self.assertEqual(Path(result['report']).read_text().count('<svg '), 3)
        return result, project

    def test_successful_saved_output_and_no_process_view(self):
        result, project = self.successful()
        engine = p.tree(self.output/'app/engine')
        with patch('subprocess.Popen', side_effect=AssertionError('saved read launched process')):
            cli.view(project, result['id'], self.output/'second.html')
        self.assertEqual(engine, p.tree(self.output/'app/engine'))
        self.assertEqual((self.output/'report.html').read_bytes(), (self.output/'second.html').read_bytes())

    def test_malformed_images_fail_before_destination_or_dispatch(self):
        for raw in (b'', b'x'*8193, image.pgm(self.pixels)[:-1], image.pgm(self.pixels)+b'x'):
            self.image.write_bytes(raw)
            with patch.object(a, 'run', side_effect=AssertionError('invalid input dispatched')):
                self.assertEqual(self.invoke()[0], 2)
            self.assertFalse(self.output.exists())

    def test_symlink_fifo_and_directory_image_reject_without_blocking(self):
        raw = self.image.read_bytes(); self.image.unlink()
        target = self.root/'real.pgm'; target.write_bytes(raw)
        self.image.symlink_to(target)
        self.assertEqual(self.invoke()[0], 2)
        self.image.unlink(); os.mkfifo(self.image)
        self.assertEqual(self.invoke()[0], 2)
        self.image.unlink(); self.image.mkdir()
        self.assertEqual(self.invoke()[0], 2)
        self.assertFalse(self.output.exists())

    def test_missing_runtime_and_invalid_deadline_do_not_create_output(self):
        for timeout in ('nan', '-1', '0', 'inf'):
            self.assertEqual(self.invoke(extra=('--timeout-seconds', timeout))[0], 2)
        self.kernel.unlink()
        self.assertEqual(self.invoke()[0], 2)
        self.assertFalse(self.output.exists())

    def test_destination_collision_preserves_existing_work(self):
        self.output.mkdir(); (self.output/'mine').write_text('unchanged')
        before = p.tree(self.output)
        with patch.object(a, 'run', side_effect=AssertionError('collision dispatched')):
            self.assertEqual(self.invoke()[0], 2)
        self.assertEqual(before, p.tree(self.output))

    def test_preparation_interrupt_and_fresh_retry(self):
        from scripts import prepare_array_app
        with patch.object(prepare_array_app, 'prepare', side_effect=KeyboardInterrupt):
            self.assertEqual(self.invoke()[0], 130)
        self.assertFalse((self.output/'report.html').exists())
        before = p.tree(self.output)
        self.successful(self.root/'retry')
        self.assertEqual(before, p.tree(self.output))

    def test_stops_restore_handlers_and_never_report_uncommitted_run(self):
        previous = {sig: signal.getsignal(sig) for sig in (signal.SIGINT, signal.SIGTERM)}
        for code in (130,143,124):
            destination = self.root/str(code)
            with patch.object(a, 'run', side_effect=run_control.Stopped('injected stop', code)):
                result = self.invoke(destination)
            self.assertEqual(result[0], code)
            self.assertFalse((destination/'report.html').exists())
            self.assertEqual(previous, {sig: signal.getsignal(sig) for sig in previous})

    def test_forged_success_return_cannot_publish_without_saved_proof(self):
        with patch.object(a, 'run', return_value={'status':'succeeded','id':'forged'}):
            self.assertEqual(self.invoke()[0], 2)
        self.assertFalse((self.output/'report.html').exists())

    def test_incomplete_run_cannot_publish(self):
        with patch.object(d, 'run', side_effect=lambda *args: self.fake(*args, failed=0)):
            self.assertEqual(self.invoke()[0], 2)
        self.assertFalse((self.output/'report.html').exists())

    def test_report_failure_preserves_committed_id_and_view_recovers(self):
        original = cli.publish
        def fail_report(path, raw):
            if Path(path).name == 'report.html': raise OSError('presentation failure')
            return original(path, raw)
        with patch.object(d, 'run', side_effect=self.fake), patch.object(cli, 'publish', side_effect=fail_report):
            code, out, err = self.invoke()
        self.assertEqual(code, 2); self.assertEqual(out, '')
        diagnostic = json.loads(err.splitlines()[-1])
        self.assertTrue(diagnostic['array_committed'])
        self.assertEqual(diagnostic['status'], 'report-failed')
        project = p.Project(self.output/'app/workspace')
        with patch('subprocess.Popen', side_effect=AssertionError('saved read executed')):
            cli.view(project, diagnostic['attempt'], self.output/'recovered.html')

    def test_stop_after_array_commit_keeps_successful_report(self):
        original = a.run
        def committed_then_stopped(*args):
            record = original(*args)
            control = run_control.current()
            self.assertTrue(control.committed)
            control.request(signal.SIGINT)
            return record
        with patch.object(a, 'run', side_effect=committed_then_stopped):
            self.successful()

    def test_atomic_publication_collision_and_interrupt_boundaries(self):
        report = self.root/'view.html'; report.write_bytes(b'previous')
        with self.assertRaises(FileExistsError): cli.publish(report, b'new')
        self.assertEqual(report.read_bytes(), b'previous')
        report.unlink()
        with patch.object(cli.os, 'link', side_effect=KeyboardInterrupt), self.assertRaises(KeyboardInterrupt):
            cli.publish(report, b'complete')
        self.assertFalse(report.exists()); self.assertEqual(list(self.root.glob('.image-pending-*')), [])
        link = os.link
        def after_link(*args):
            link(*args); raise KeyboardInterrupt
        with patch.object(cli.os, 'link', side_effect=after_link), self.assertRaises(KeyboardInterrupt):
            cli.publish(report, b'complete')
        self.assertEqual(report.read_bytes(), b'complete')
        self.assertEqual(list(self.root.glob('.image-pending-*')), [])

    def test_relocated_helpers_prepare_and_repackage_without_original_artifacts(self):
        cli.package(self.output, self.image, self.kernel, self.build)
        moved = self.root/'relocated image'; self.output.rename(moved)
        self.kernel.unlink(); shutil.rmtree(self.build)
        environment = dict(os.environ, PYTHONPATH='')
        engine = p.tree(moved/'app/engine')
        result = subprocess.run([sys.executable, str(moved/'scripts/image_demo_cli.py'), 'prepare',
                                 '--image', str(self.image), '--output', str(moved/'edited.json')],
                                cwd='/tmp', env=environment, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads((moved/'edited.json').read_bytes()), image.source(self.pixels))
        code = ('import sys;from pathlib import Path;sys.path.insert(0,sys.argv[1]);'
                'from scripts.image_demo_cli import package;'
                'package(Path(sys.argv[2]),Path(sys.argv[3]),Path(sys.argv[1])/"app/workspace/array-runtime/kernel.elf",'
                'Path(sys.argv[1])/"app/workspace/array-runtime/runtime")')
        result = subprocess.run([sys.executable, '-B', '-c', code, str(moved), str(self.root/'repacked'), str(self.image)],
                                cwd='/tmp', env=environment, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(engine, p.tree(moved/'app/engine'))
        guide = (self.root/'repacked/IMAGE_GUIDE.md').read_text()
        self.assertIn('(app/engine/docs/guides/ARRAY_WORKSPACE.md)', guide)
        self.assertNotIn('(../experiments/', guide)


if __name__ == '__main__':
    unittest.main()
