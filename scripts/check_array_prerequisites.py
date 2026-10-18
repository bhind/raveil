#!/usr/bin/env python3
"""Inspect existing tools for generic array build/use; never install or execute jobs."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from raveil.project_fold import IMAGE

CACHE = 'raveil-chisel-scala-cache-v1'


def inspect(*, run_only=False):
    checks = []
    def add(name, ok, detail):
        checks.append(dict(name=name, ok=bool(ok), detail=str(detail)[:1024]))
    def probe(name, executable, arguments, expected=None):
        path = shutil.which(executable)
        if not path:
            add(name, False, 'Missing existing executable on PATH: '+executable)
            return None
        try:
            result = subprocess.run([path, *arguments], capture_output=True, text=True, timeout=15)
            text = result.stdout.strip()
            ok = result.returncode == 0 and (expected is None or expected(text))
            add(name, ok, text if ok else 'Probe failed or unexpected tool identity: '+(result.stderr.strip() or text))
            return text if ok else None
        except (OSError, subprocess.TimeoutExpired) as error:
            add(name, False, error)
            return None
    add('python', sys.version_info >= (3,11), sys.version.split()[0]+'; requires Python >=3.11')
    add('platform', os.name == 'posix', 'Requires POSIX filesystem APIs; native Windows unsupported')
    probe('qemu', 'qemu-system-riscv64', ['--version'])
    probe('docker-image', 'docker', ['image','inspect','--format','{{.Id}} {{.Os}}/{{.Architecture}}', IMAGE],
          lambda text: text == IMAGE+' linux/amd64')
    prefix = None
    if not run_only:
        location = str(Path(__file__).resolve().parents[1])
        add('build-source-path', not any(c in location for c in ' \t\n,'),
            'Use a checkout path without whitespace or commas for the unchanged Makefile/Docker build commands')
        probe('make', 'make', ['--version'], lambda text: 'GNU Make' in text)
        # Match Makefile origin semantics: an explicitly empty prefix is meaningful.
        if 'CROSS_COMPILE' in os.environ:
            prefix = os.environ['CROSS_COMPILE']
        else:
            prefix = 'riscv64-unknown-elf-'
            if not shutil.which(prefix+'gcc') and shutil.which('riscv64-elf-gcc'):
                prefix = 'riscv64-elf-'
        compiler = prefix+'gcc'
        target = probe('riscv-gcc', compiler, ['-dumpmachine'], lambda text: text.startswith('riscv64-'))
        if target:
            for tool in ('as','ld'):
                selected = probe('gcc-'+tool+'-selection', compiler, ['-print-prog-name='+tool], bool)
                if selected:
                    probe('gcc-'+tool, selected, ['--version'])
        probe('scala-cache', 'docker', ['volume','inspect','--format','{{.Name}}', CACHE], lambda text: text == CACHE)
    return dict(schema='raveil.array-prerequisites/v1', mode='run-tools' if run_only else 'build-and-run-tools',
                tools_ready=all(item['ok'] for item in checks), cross_compile=prefix, checks=checks,
                evidence_class='read-only external prerequisite inspection; no build or job execution',
                next_action='Use ARRAY_WORKSPACE.md; successful fresh build/run and prepared array-doctor remain required. No tools are installed by this command.')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-only', action='store_true', help='inspect runtime tools only; prepared artifact checks remain array-doctor')
    args = parser.parse_args(argv)
    result = inspect(run_only=args.run_only)
    print(json.dumps(result, indent=2))
    return 0 if result['tools_ready'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
