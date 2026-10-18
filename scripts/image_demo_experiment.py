#!/usr/bin/env python3
"""Frozen EXP-0013 collection using existing executables; never tune after data."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import os
import signal
import shutil
import statistics
import subprocess
import sys
import time
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from raveil import project as p, project_array as a, project_fold as f, fold_dag as dag
from scripts.image_demo import cases, source, reference, trace_metrics, pgm
from scripts.image_demo_report import write as write_report
from scripts.array_program_acceptance import counts
from scripts.array_control_acceptance import inspect_resources
from scripts.prepare_array_app import prepare


def frozen_app(app):
    manifest=json.loads((app/'app.json').read_bytes())
    if p.tree(app/'engine')!=manifest['engine']:raise ValueError('prepared engine changed')
    launcher=p.digest((app/'raveil').read_bytes())
    if launcher!=manifest['launcher_sha256']:raise ValueError('prepared launcher changed')
    return dict(manifest_sha256=p.digest((app/'app.json').read_bytes()),launcher_sha256=launcher)


def command(argv,root,label,timeout):
    """Keep streamed logs even if the experiment observer is interrupted."""
    started=time.monotonic();failure=None;process=None
    outpath=root/(label+'.stdout');errpath=root/(label+'.stderr')
    record=dict(argv=argv,cwd=str(root),timeout_seconds=timeout)
    p.write_new(root/(label+'.command.json'),p.encoded(record))
    with outpath.open('xb') as out,errpath.open('xb') as err:
        try:
            process=subprocess.Popen(argv,cwd=root,stdout=out,stderr=err,start_new_session=True)
            code=process.wait(timeout=timeout)
        except BaseException as error:
            failure=error
            try:
                if process is not None and process.poll() is None:
                    try:os.killpg(process.pid,signal.SIGTERM)
                    except ProcessLookupError:pass
                    try:process.wait(timeout=75)
                    except subprocess.TimeoutExpired:
                        try:os.killpg(process.pid,signal.SIGKILL)
                        except ProcessLookupError:pass
                        process.wait(timeout=5)
            except BaseException as cleanup_error:
                record['cleanup_error']=str(cleanup_error)
            code=process.returncode if process is not None else None
    record.update(code=code,elapsed_seconds=time.monotonic()-started,
                  stdout=outpath.read_text(),stderr=errpath.read_text(),
                  failure=type(failure).__name__ if failure else None)
    p.write_new(root/(label+'.execution.json'),p.encoded(record))
    if failure:raise RuntimeError('collection interrupted; partial logs retained') from failure
    return record


def paired(selected):
    result=[]
    for repeat in range(3):
        pair=[r for r in selected if r['repeat']==repeat]
        if len(pair)!=2 or {r['variant'] for r in pair}!={'scalar','fused'}:raise ValueError('missing pair')
        values={r['variant']:r['elapsed_seconds'] for r in pair}
        result.append(dict(repeat=repeat,order=[r['variant'] for r in pair],
                           fused_over_scalar=values['fused']/values['scalar'],
                           fused_minus_scalar_seconds=values['fused']-values['scalar']))
    return result


def collect(project, identity):
    """Read only fully validated bound jobs; no glob-based duplicate counting."""
    with patch('subprocess.Popen',side_effect=AssertionError('saved metrics executed')):
        record=a.load(project,identity)
        if record['status']!='succeeded':raise ValueError('incomplete parent')
        sessions=counts(project,record)['receipts'];jobs=[]
        parent=project.root/'arrays'/identity
        plan=json.loads((parent/'plan.json').read_bytes())
        for row in sessions:
            root=Path(row['path']);receipt=dag.verify(root)
            for job in receipt['jobs']:
                if job['result']['approved'] is not True:raise ValueError('unapproved job')
                folded=root/'project/folds'/job['rtl_id']
                checked=f.load(p.Project(root/'project'),job['rtl_id'])
                if checked['status']!='succeeded':raise ValueError('incomplete RTL')
                device=json.loads((folded/'device/device.json').read_bytes());raw=(folded/'device/trace.bin').read_bytes()
                options=json.loads((folded/'plan.json').read_bytes())['options']
                if options!=dict(seed=213,cancel_after=0,fault_at=0):raise ValueError('unexpected stall policy')
                jobs.append(dict(path=str(folded.relative_to(project.root)),trace_sha256=p.digest(raw),
                                 **trace_metrics(raw,device)))
        if len({j['path'] for j in jobs})!=len(jobs):raise ValueError('duplicate job')
        totals={key:sum(job[key] for job in jobs) for key in
                ('rtl_active_cycles','reads','writes','transactions','interface_payload_bytes')}
        return dict(id=identity,outputs=record['outputs'],sessions=len(sessions),jobs=len(jobs),
                    build_sha256=plan['build_sha256'],kernel_sha256=plan['kernel_sha256'],
                    job_metrics=jobs,**totals)


def disposition(rows):
    # Predetermined thresholds are engineering usefulness criteria, not novelty.
    useful=all(row['cycle_reduction']>=.20 and row['transaction_reduction']>=.20 for row in rows)
    faster=all(row['fused']['median_wall_seconds']<row['scalar']['median_wall_seconds'] for row in rows)
    if useful and faster:return '融合を維持する。今回のシミュレーション運用は改善。新ハード開発の根拠にはしない。'
    if useful:return '融合はRTL内の処理を削減するが、実行基盤の負担が残る。機能拡張を止め、ホスト側の費用を優先して見直す。'
    return '事前に定めた削減基準を満たさない。この方式を理由に汎用化や新ハード開発を拡大しない。'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('output','kernel','build'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();root=args.output.absolute();root.mkdir(parents=True,exist_ok=False)
    try:return experiment(args,root)
    except BaseException as error:
        report=dict(error_type=type(error).__name__,error=str(error),claim_collection='failed; all attempts preserved')
        try:report['resources']=inspect_resources(root/'app/workspace')
        except BaseException as audit_error:report['resource_audit_error']=str(audit_error)
        p.write_new(root/'failure.json',p.encoded(report))
        raise


def experiment(args,root):
    images=dict(cases());app=root/'app';first=source(next(iter(images.values())))
    initial=root/'initial.json';initial.write_bytes(p.encoded(first));prepare(app,args.kernel,args.build,initial)
    workspace=app/'workspace';project=p.Project(workspace);input_hashes={}
    data=root/'data';data.mkdir()
    for name,image in images.items():
        (data/(name+'.pgm')).write_bytes(pgm(image))
        for variant in ('scalar','fused'):
            filename=f'{name}-{variant}.json';raw=p.encoded(source(image,variant=='fused'))
            p.write_new(workspace/'inputs'/filename,raw);input_hashes[filename]=p.digest(raw)
    clang=shutil.which('clang')
    if not clang:raise RuntimeError('existing clang required; do not install')
    cpu=root/'image-cpu';compile_argv=[clang,'-O3','-std=c11','-Wall','-Wextra','-Werror',str(p.REPOSITORY/'scripts/image_demo_cpu.c'),'-o',str(cpu)]
    built=subprocess.run(compile_argv,capture_output=True,text=True)
    (root/'cpu-build.json').write_bytes(p.encoded(dict(argv=compile_argv,code=built.returncode,stdout=built.stdout,stderr=built.stderr)))
    if built.returncode:raise RuntimeError(built.stderr)
    sources={str(path.relative_to(p.REPOSITORY)):p.digest(path.read_bytes()) for path in
             [*sorted((p.REPOSITORY/'raveil').glob('*.py')),*sorted((p.REPOSITORY/'scripts').glob('image_demo*')),
              p.REPOSITORY/'docs/experiments/EXP-0013-image-fusion-comparison.md',
              *[p.REPOSITORY/'scripts'/name for name in ('prepare_array_app.py','array_program_acceptance.py','array_control_acceptance.py')]] if path.is_file()}
    order=[dict(case=name,repeat=repeat,variant=variant) for index,name in enumerate(images)
           for repeat in range(3) for variant in (('scalar','fused') if (repeat+index)%2==0 else ('fused','scalar'))]
    freeze=dict(schema='raveil.image-experiment/v1',task='T-0241',experiment='EXP-0013',
                sources=sources,inputs=input_hashes,order=order,expected={n:reference(im) for n,im in images.items()},
                runtime_sha256=f.verify_build(args.build,current=True),kernel_sha256=p.digest(args.kernel.read_bytes()),
                app=frozen_app(app),cpu_sha256=p.digest(cpu.read_bytes()),cpu_iterations=50000,cpu_repeats=5,
                thresholds=dict(cycles_reduction=.20,transactions_reduction=.20),
                environment=dict(platform=platform.platform(),python=sys.version,
                    clang=subprocess.check_output([clang,'--version'],text=True),
                    qemu=subprocess.check_output(['qemu-system-riscv64','--version'],text=True),
                    docker=subprocess.check_output(['docker','--version'],text=True)),argv=sys.argv,
                restrictions='same RTL, seed213; no warmup exclusion, no tuning or reruns for a favorable result; no hardware inference')
    p.write_new(root/'frozen-experiment.md',(p.REPOSITORY/'docs/experiments/EXP-0013-image-fusion-comparison.md').read_bytes())
    package=root/'scripts';package.mkdir()
    p.write_new(package/'__init__.py',b'')
    for path in (p.REPOSITORY/'scripts').glob('image_demo*'):
        if path.is_file():shutil.copy2(path,package/path.name)
    p.write_new(root/'freeze.json',p.encoded(freeze));print('FROZEN',p.digest((root/'freeze.json').read_bytes()),flush=True)
    runs=[];cpu_rows={}
    for index,entry in enumerate(order):
        name=entry['case'];variant=entry['variant'];filename=f'{name}-{variant}.json'
        if sum(path.stat().st_size for path in root.rglob('*') if path.is_file())>2*1024**3:raise RuntimeError('experiment storage cap exceeded')
        if frozen_app(app)!=freeze['app']:raise ValueError('frozen application identity changed')
        if any(p.digest((p.REPOSITORY/key).read_bytes())!=sha for key,sha in sources.items()):raise ValueError('collection source changed')
        if p.digest((workspace/'inputs'/filename).read_bytes())!=input_hashes[filename]:raise ValueError('changed input')
        argv=[str(app/'raveil'),'array-run','--input',filename,'--timeout-seconds','900']
        result=command(argv,root,f'run-{index:02d}',975);elapsed=result['elapsed_seconds']
        evidence=dict(**entry,**result)
        p.write_new(root/f'run-{index:02d}.json',p.encoded(evidence))
        if result['code']:raise RuntimeError(f'collection failed at {index}: '+result['stderr'])
        actual=json.loads(result['stdout'])
        if actual['outputs']!=freeze['expected'][name]:raise ValueError('independent image oracle mismatch')
        measured=collect(project,actual['id'])
        if measured['outputs']!=actual['outputs'] or measured['build_sha256']!=freeze['runtime_sha256'] or measured['kernel_sha256']!=freeze['kernel_sha256']:
            raise ValueError('measurement identity mismatch')
        row=dict(**entry,elapsed_seconds=elapsed,**measured);runs.append(row)
        p.write_new(root/f'metrics-{index:02d}.json',p.encoded(row))
        print('PASS',index,name,variant,f'{elapsed:.2f}s',measured['rtl_active_cycles'],'cycles',measured['transactions'],'transactions',flush=True)
    for name,image in images.items():
        cpu_rows[name]=[]
        for repeat in range(freeze['cpu_repeats']):
            argv=[str(cpu),str(data/(name+'.pgm')),str(freeze['cpu_iterations'])]
            if p.digest(cpu.read_bytes())!=freeze['cpu_sha256']:raise ValueError('CPU binary changed')
            if (data/(name+'.pgm')).read_bytes()!=pgm(image):raise ValueError('CPU input changed')
            result=command(argv,root,f'cpu-{name}-{repeat}',30)
            p.write_new(root/f'cpu-{name}-{repeat}.json',p.encoded(result))
            if result['code']:raise ValueError('CPU baseline failed')
            value=json.loads(result['stdout'])
            if value['outputs']!=[x['words'] for x in freeze['expected'][name]]:raise ValueError('CPU oracle mismatch')
            cpu_rows[name].append(value['nanoseconds_per_image'])
    rows=[]
    for name,image in images.items():
        row=dict(name=name,outputs=freeze['expected'][name],cpu_median_ns=statistics.median(cpu_rows[name]),cpu_ns=cpu_rows[name])
        for variant in ('scalar','fused'):
            selected=[r for r in runs if r['case']==name and r['variant']==variant]
            fields=('rtl_active_cycles','reads','writes','transactions','interface_payload_bytes','sessions','jobs')
            if len(selected)!=3 or any(len({r[k] for r in selected})!=1 for k in fields):raise ValueError('deterministic RTL counts changed')
            row[variant]={k:selected[0][k] for k in fields}
            row[variant].update(median_wall_seconds=statistics.median(r['elapsed_seconds'] for r in selected),
                                wall_seconds=[r['elapsed_seconds'] for r in selected],ids=[r['id'] for r in selected])
        row['cycle_reduction']=1-row['fused']['rtl_active_cycles']/row['scalar']['rtl_active_cycles']
        row['transaction_reduction']=1-row['fused']['transactions']/row['scalar']['transactions']
        row['paired_wall']=paired([r for r in runs if r['case']==name])
        rows.append(row)
    if any(p.digest((p.REPOSITORY/name).read_bytes())!=sha for name,sha in sources.items()):raise ValueError('frozen source changed')
    if frozen_app(app)!=freeze['app']:raise ValueError('prepared application changed')
    resources=inspect_resources(workspace);p.write_new(root/'resources.json',p.encoded(resources))
    if resources['qemu'] or resources['containers']:raise ValueError('owned resources remain')
    summary=dict(schema='raveil.image-result/v1',freeze_sha256=p.digest((root/'freeze.json').read_bytes()),
                 evidence_class='RTL simulated cycles/port transactions; host wall runtime; separate native CPU compute-only timing',
                 cases=rows,disposition=disposition(rows),runs=len(runs),
                 sessions=sum(r['sessions'] for r in runs),jobs=sum(r['jobs'] for r in runs),
                 saved_validation_no_process=True,no_owned_resources=True,sources_unchanged=True)
    p.write_new(root/'summary.json',p.encoded(summary));write_report(root,summary,images)
    print('COMPLETE',summary['disposition'],flush=True)


if __name__=='__main__':main()
