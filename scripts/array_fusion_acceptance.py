#!/usr/bin/env python3
"""Real QEMU/RTL functional validation of the versioned fusion policy."""
import argparse
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from raveil import project as p, project_array as a, array_program as compiler
from raveil import project_dag_batch as b, fold_dag as d
from scripts.array_fusion_cases import cases
from scripts.array_program_acceptance import counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('output', 'kernel', 'build'):
        parser.add_argument('--' + key, type=Path, required=True)
    parser.add_argument('--case', action='append', dest='selected')
    args = parser.parse_args(); root = args.output.absolute(); root.mkdir(parents=True, exist_ok=False)
    project = p.Project(p.init_project(root/'workspace')); rows = []; failures = []; positive = list(cases())
    if args.selected and not set(args.selected) <= {n for n, _, _ in positive}:
        raise ValueError('unknown fusion case')

    def record(label, actual, expected):
        assert actual['status'] == 'succeeded' and actual['outputs'] == expected
        row = dict(name=label, id=actual['id'], final_words=sum(len(o['words']) for o in expected), **counts(project, actual))
        rows.append(row); print('PASS', json.dumps({k: v for k, v in row.items() if k != 'receipts'}), flush=True)
        return row

    for name, value, expected in positive:
        if args.selected and name not in args.selected:
            continue
        p.write_new(project.root/'inputs'/f'{name}.json', p.encoded(value))
        preview = a.check(project, name + '.json'); assert compiler.reference(value) == expected
        command = [sys.executable, '-m', 'raveil', 'project', 'array-run', '--project', str(project.root),
                   '--input', name + '.json', '--kernel', str(args.kernel), '--build', str(args.build)]
        (root/(name+'.command.json')).write_bytes(p.encoded(command))
        result = subprocess.run(command, capture_output=True)
        (root/(name+'.stdout')).write_bytes(result.stdout); (root/(name+'.stderr')).write_bytes(result.stderr)
        assert result.returncode == 0, (name, result.stderr.decode(errors='replace'))
        row = record(name, json.loads(result.stdout), expected)
        assert (row['sessions'], row['jobs']) == (preview['sessions'], preview['jobs'])
        row['plan'] = {k: preview[k] for k in ('sessions', 'jobs', 'work_words', 'scalar_evaluations', 'peak_plane_words')}
        row['passes'] = len(preview['passes'])
    if not args.selected:
        # The post job, not the fold producer, fails in a real two-job session.
        name, value, expected = next(c for c in positive if c[0] == 'wrapped-fold-post')
        run = d.run
        for injection in ('wrong-word', 'rtl-fault'):
            calls = []
            def fail(session, kernel, build, destination):
                calls.append(str(destination))
                return run(session, kernel, build, destination, injections=['none', injection])
            with patch.object(d, 'run', side_effect=fail):
                failed = a.run(project, name + '.json', args.kernel, args.build)
            assert len(calls) == 1 and failed['status'] == 'incomplete' and failed['outputs'] is None
            failed_root = project.root/'arrays'/failed['id']
            before = p.tree(failed_root, max_bytes=b.MAX_BYTES, max_entries=b.MAX_ENTRIES)
            failures.append(dict(name=injection, id=failed['id'], **counts(project, failed)))
            retry = a.run(project, name + '.json', args.kernel, args.build); record(injection+'-retry', retry, expected)
            assert p.tree(failed_root, max_bytes=b.MAX_BYTES, max_entries=b.MAX_ENTRIES) == before
            print('PASS failure-and-retry', injection, flush=True)
    with patch('subprocess.Popen', side_effect=AssertionError('saved verification executed process')):
        for row in rows + failures:
            a.load(project, row['id'])
        assert len(a.history(project)) == len(rows) + len(failures)
    receipts = [receipt for row in rows + failures for receipt in row['receipts']]
    assert len({r['path'] for r in receipts}) == len(receipts)
    summary = dict(evidence_class=a.CLASS, positive=rows, failures=failures, sessions=len(receipts),
                   jobs=sum(r['processed'] for r in receipts), approved=sum(r['approved'] for r in receipts),
                   final_words=sum(r['final_words'] for r in rows), saved_validation_no_process=True,
                   full_failed_tree_preserved=True)
    (root/'summary.json').write_bytes(p.encoded(summary))
    print('COMPLETE', json.dumps({k: v for k, v in summary.items() if k not in ('positive', 'failures')}), flush=True)


if __name__ == '__main__':
    main()
