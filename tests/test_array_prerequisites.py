"""Read-only tool diagnosis; fixtures never count as build/runtime evidence."""
import contextlib
import io
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from scripts import check_array_prerequisites as pre


class PrerequisiteTests(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.missing = set()
        self.overrides = {}
        self.addCleanup(patch.stopall)
        patch.dict(os.environ, {}, clear=True).start()
        patch.object(pre.shutil, 'which', side_effect=lambda name: None if name in self.missing else name).start()
        patch.object(pre.subprocess, 'run', side_effect=self.query).start()

    def query(self, argv, **kwargs):
        self.calls.append(argv)
        self.assertEqual(kwargs, dict(capture_output=True,text=True,timeout=15))
        key = tuple(argv)
        if key in self.overrides:
            value = self.overrides[key]
            if isinstance(value, Exception): raise value
            return subprocess.CompletedProcess(argv, *value)
        if '-dumpmachine' in argv: text = 'riscv64-unknown-elf'
        elif '-print-prog-name=as' in argv: text = '/existing/riscv-as'
        elif '-print-prog-name=ld' in argv: text = '/existing/riscv-ld'
        elif argv[0] == 'make': text = 'GNU Make 3.81'
        elif argv[1:3] == ['image','inspect']: text = pre.IMAGE+' linux/amd64'
        elif argv[1:3] == ['volume','inspect']: text = pre.CACHE
        else: text = 'existing tool version'
        return subprocess.CompletedProcess(argv, 0, text+'\n', '')

    def test_build_mode_matches_preferred_compiler_and_readonly_commands(self):
        with tempfile.TemporaryDirectory() as directory:
            before = list(Path(directory).iterdir())
            result = pre.inspect()
            self.assertEqual(before, list(Path(directory).iterdir()))
        self.assertTrue(result['tools_ready'])
        self.assertEqual(result['cross_compile'], 'riscv64-unknown-elf-')
        self.assertTrue(all(cmd[1] in ('--version','-dumpmachine','-print-prog-name=as','-print-prog-name=ld','image','volume') for cmd in self.calls))
        for cmd in self.calls:
            if cmd[0] == 'docker': self.assertEqual(cmd[2], 'inspect')

    def test_fallback_compiler_and_explicit_prefix_are_not_conflated(self):
        self.missing.add('riscv64-unknown-elf-gcc')
        self.assertEqual(pre.inspect()['cross_compile'], 'riscv64-elf-')
        os.environ['CROSS_COMPILE'] = '/custom/riscv-'
        self.assertTrue(pre.inspect()['tools_ready'])
        self.assertIn(['/custom/riscv-gcc','-dumpmachine'], self.calls)
        self.missing.add('/custom/riscv-gcc')
        self.assertFalse(pre.inspect()['tools_ready'])
        self.assertEqual(pre.inspect()['cross_compile'], '/custom/riscv-')

    def test_empty_prefix_native_compiler_rejects(self):
        os.environ['CROSS_COMPILE'] = ''
        self.overrides[('gcc','-dumpmachine')] = (0,'arm64-apple-darwin','')
        result = pre.inspect()
        self.assertEqual(result['cross_compile'], '')
        self.assertFalse(result['tools_ready'])
        self.assertFalse(any('-print-prog-name=as' in cmd for cmd in self.calls))

    def test_missing_build_tools_do_not_block_runtime_tool_inspection(self):
        self.missing.update({'make','riscv64-unknown-elf-gcc','riscv64-elf-gcc'})
        self.assertTrue(pre.inspect(run_only=True)['tools_ready'])
        self.assertFalse(any('volume' in cmd for cmd in self.calls))
        self.assertFalse(pre.inspect()['tools_ready'])

    def test_missing_assembler_or_linker_rejects(self):
        for name in ('/existing/riscv-as','/existing/riscv-ld'):
            self.missing = {name}
            self.assertFalse(pre.inspect()['tools_ready'])

    def test_non_gnu_make_wrong_image_and_cache_reject(self):
        cases = [(('make','--version'), (0,'BSD make','')),
                 (('docker','image','inspect','--format','{{.Id}} {{.Os}}/{{.Architecture}}',pre.IMAGE), (0,'wrong linux/arm64','')),
                 (('docker','volume','inspect','--format','{{.Name}}',pre.CACHE), (1,'','No such volume'))]
        for key,value in cases:
            self.overrides = {key:value}
            self.assertFalse(pre.inspect()['tools_ready'])

    def test_missing_runtime_tool_failed_probe_and_timeout_are_diagnostics(self):
        self.missing.add('docker')
        self.assertFalse(pre.inspect(run_only=True)['tools_ready'])
        self.missing.clear()
        for error in (OSError('unavailable'),subprocess.TimeoutExpired(['qemu'],15)):
            self.overrides[('qemu-system-riscv64','--version')] = error
            self.assertFalse(pre.inspect(run_only=True)['tools_ready'])

    def test_cli_status_and_mode(self):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(pre.main(['--run-only']),0)
        self.assertIn('run-tools',output.getvalue())
        self.missing.add('docker')
        with contextlib.redirect_stdout(io.StringIO()): self.assertEqual(pre.main([]),2)


if __name__ == '__main__': unittest.main()
