#!/usr/bin/env python3
"""EXP-0014: frozen paired host comparison with unchanged fused image programs."""
import argparse
import json
from pathlib import Path
import platform
import statistics
import subprocess
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from raveil import project as p, project_fold as f
from scripts.image_demo import cases, source, reference
from scripts.image_demo_experiment import command, collect, frozen_app
from scripts.array_control_acceptance import inspect_resources


def schedule(names, repeats=3):
    return [dict(case=name, repeat=repeat, variant=variant)
            for repeat in range(repeats) for index, name in enumerate(names)
            for variant in (('old', 'new') if (repeat+index)%2 == 0 else ('new', 'old'))]


def summarize(rows):
    summary = []
    for name in dict.fromkeys(row['case'] for row in rows):
        selected = [row for row in rows if row['case'] == name]
        if len(selected) != 6 or {(r['repeat'], r['variant']) for r in selected} != {
                (i, v) for i in range(3) for v in ('old', 'new')}:
            raise ValueError('missing or duplicate comparison attempt')
        medians = {v: statistics.median(r['elapsed_seconds'] for r in selected if r['variant'] == v)
                   for v in ('old', 'new')}
        pairs = []
        for repeat in range(3):
            pair = [r for r in selected if r['repeat'] == repeat]
            values = {r['variant']: r['elapsed_seconds'] for r in pair}
            pairs.append(dict(repeat=repeat, order=[r['variant'] for r in pair],
                              new_over_old=values['new']/values['old']))
        summary.append(dict(case=name, median_seconds=medians,
                            reduction=1-medians['new']/medians['old'], pairs=pairs))
    return summary


def require_equivalent(previous, metrics):
    identity = {key: metrics[key] for key in ('outputs','sessions','jobs',
        'rtl_active_cycles','reads','writes','transactions','interface_payload_bytes',
        'kernel_sha256','build_sha256')}
    identity['ordered_trace_sha256'] = [job['trace_sha256'] for job in metrics['job_metrics']]
    if previous is not None and previous != identity:
        raise ValueError('old/new functional, trace or RTL count mismatch')
    return identity


def experiment(args, root):
    images = dict(cases()); order = schedule(images)
    initial = root/'initial.json'; p.write_new(initial, p.encoded(source(next(iter(images.values())))))
    apps = {}; inputs = {}
    for variant, engine in (('old', args.baseline), ('new', p.REPOSITORY)):
        app = root/variant; apps[variant] = app
        row = command([sys.executable, '-B', str(engine/'scripts/prepare_array_app.py'),
                       '--output', str(app), '--kernel', str(args.kernel), '--build', str(args.build),
                       '--source', str(initial)], root, 'prepare-'+variant, 180)
        if row['code'] != 0: raise ValueError('application preparation failed')
        for name, image in images.items():
            raw = p.encoded(source(image)); inputs[name] = p.digest(raw)
            p.write_new(app/'workspace/inputs'/(name+'.json'), raw)
    paths = [*sorted((p.REPOSITORY/'raveil').glob('*.py')),
             *[p.REPOSITORY/'scripts'/name for name in ('inventory_experiment.py','inventory_probe.py',
                'image_demo.py','image_demo_experiment.py','array_program_acceptance.py',
                'array_control_acceptance.py','prepare_array_app.py')],
             p.REPOSITORY/'docs/experiments/EXP-0014-host-inventory.md']
    hashes = {str(path.relative_to(p.REPOSITORY)): p.digest(path.read_bytes()) for path in paths}
    freeze = dict(schema='raveil.inventory-comparison-freeze/v1', order=order,
                  sources=hashes, applications={v: frozen_app(app) for v,app in apps.items()},
                  inputs=inputs, python=sys.version, platform=platform.platform(),
                  protocol=p.digest(paths[-1].read_bytes()),
                  kernel_sha256=p.digest(args.kernel.read_bytes()),runtime_sha256=f.verify_build(args.build,current=True),
                  versions={tool:subprocess.check_output([tool,'--version'],text=True) for tool in ('qemu-system-riscv64','docker')},
                  evidence_class='host wall time; QEMU/RTL functional and simulated counters')
    p.write_new(root/'freeze.json', p.encoded(freeze))
    p.write_new(root/'frozen-protocol.md', paths[-1].read_bytes())
    runs=[]; saved=[]; captures={}; metrics_by_case={}
    for i, spec in enumerate(order):
        name=spec['case']; app=apps[spec['variant']]
        if frozen_app(app)!=freeze['applications'][spec['variant']]:raise ValueError('engine changed')
        if p.digest((app/'workspace/inputs'/(name+'.json')).read_bytes())!=inputs[name]:raise ValueError('input changed')
        if sum(path.stat().st_size for path in root.rglob('*') if path.is_file())>2*1024**3:
            raise ValueError('collection storage cap exceeded')
        result=command([str(app/'raveil'), 'array-run', '--input', name+'.json',
                        '--timeout-seconds', '900'], root, f'run-{i:02}', 1020)
        if result['code'] != 0: raise ValueError('run failed; do not exclude or rerun')
        printed=json.loads(result['stdout']); metrics=collect(p.Project(app/'workspace'),printed['id'])
        expected=reference(images[name])
        if metrics['outputs'] != expected or printed['outputs'] != expected:
            raise ValueError('independent image oracle mismatch')
        if (metrics['kernel_sha256'] != freeze['kernel_sha256'] or
                metrics['build_sha256'] != freeze['runtime_sha256']):
            raise ValueError('frozen executable identity mismatch')
        metrics_by_case[name]=require_equivalent(metrics_by_case.get(name),metrics)
        row={**spec, **result, **metrics}; p.write_new(root/f'run-{i:02}.json',p.encoded(row));runs.append(row)
        captures.setdefault(name,(app/'workspace', printed['id']))
        print('RUN',i,name,spec['variant'],round(result['elapsed_seconds'],3),flush=True)
    probe=p.REPOSITORY/'scripts/inventory_probe.py'
    for i,spec in enumerate(order):
        workspace,identity=captures[spec['case']]
        result=command([sys.executable,'-B',str(probe),'--engine',str(apps[spec['variant']]/'engine'),
                        '--workspace',str(workspace),'--identity',identity],root,f'saved-{i:02}',120)
        if result['code'] != 0:raise ValueError('saved validation failed')
        row={**spec,**result};p.write_new(root/f'saved-{i:02}.json',p.encoded(row));saved.append(row)
    for name in images:
        records={json.loads(r['stdout'])['record_sha256'] for r in saved if r['case']==name}
        if len(records)!=1:raise ValueError('saved validators disagree')
    if any(p.digest((p.REPOSITORY/name).read_bytes())!=sha for name,sha in hashes.items()):
        raise ValueError('frozen source changed')
    for variant,app in apps.items():
        if frozen_app(app)!=freeze['applications'][variant]:raise ValueError('engine changed')
        for name,sha in inputs.items():
            if p.digest((app/'workspace/inputs'/(name+'.json')).read_bytes())!=sha:raise ValueError('input changed')
    resources={v:inspect_resources(app/'workspace') for v,app in apps.items()}
    p.write_new(root/'resources.json',p.encoded(resources))
    if any(r['qemu'] or r['containers'] for r in resources.values()):raise ValueError('owned resource remains')
    live_summary=summarize(runs);saved_summary=summarize(saved)
    useful=all(r['reduction']>=.20 for r in saved_summary) and all(r['reduction']>=-.10 for r in live_summary)
    summary=dict(schema='raveil.inventory-comparison-result/v1',freeze_sha256=p.digest((root/'freeze.json').read_bytes()),
                 run=live_summary,saved=saved_summary,keep=useful,runs=len(runs),saved_reads=len(saved),
                 sessions=sum(r['sessions'] for r in runs),jobs=sum(r['jobs'] for r in runs),
                 words=sum(len(o['words']) for r in runs for o in r['outputs']),
                 identical_results_and_rtl_counts=True,sources_unchanged=True,no_owned_resources=True)
    p.write_new(root/'summary.json',p.encoded(summary));print(json.dumps(summary,indent=2),flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('output','baseline','kernel','build'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();args.baseline=args.baseline.absolute();root=args.output.absolute();root.mkdir(parents=True)
    try:experiment(args,root)
    except BaseException as error:
        p.write_new(root/'failure.json',p.encoded(dict(type=type(error).__name__,error=str(error),all_attempts_retained=True)))
        raise


if __name__=='__main__':main()
