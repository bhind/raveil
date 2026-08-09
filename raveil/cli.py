from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics
import sys

from . import __version__
from .backend import ToyDaphnis
from .experience import ExperienceStore
from .model import Context, seed_candidates
from .policy import NearestExperiencePolicy, Tuner, TuningResult
from .experiment_schema import BenchmarkManifest
from .policy_comparison import (
    generate_policy_selections,
    load_measurements,
    write_policy_selections,
)
from .experiment_runner import (
    analyze_bundle,
    find_bundle,
    preflight_experiment,
    run_experiment,
    seal_bundle,
)


def _tuner(store: ExperienceStore) -> Tuner:
    return Tuner(ToyDaphnis(), store, NearestExperiencePolicy(), seed_candidates())


def _print_result(label: str, result: TuningResult) -> None:
    print(
        f"{label}: shape={result.context.shape} memory={result.context.memory_budget_kib}KiB "
        f"best={result.best.candidate.candidate_id} cycles={result.best.metrics.cycles} "
        f"oracle={result.oracle.candidate.candidate_id} "
        f"HCR={result.headroom_capture:.1%}"
    )
    for index, trial in enumerate(result.trials, start=1):
        status = "ok" if trial.metrics.valid else f"rejected({trial.metrics.reason})"
        print(
            f"  {index}: {trial.candidate.candidate_id:<10} {status:<28} "
            f"cycles={trial.metrics.cycles if trial.metrics.valid else '-':>6}  {trial.reason}"
        )


def command_demo(args: argparse.Namespace) -> int:
    path = Path(args.experience)
    if args.reset and path.exists():
        path.unlink()
    store = ExperienceStore(path, active_limit=args.active_limit)
    tuner = _tuner(store)

    print(f"Raveil v{__version__}")
    print("closed loop: retrieve -> rank -> measure -> append -> consolidate")
    for shape in (256, 512, 1024, 2048):
        tuner.tune(Context("branching-mlp", shape, args.memory_kib), budget=3)

    target = Context("branching-mlp", args.target_shape, args.memory_kib)
    cold = _tuner(ExperienceStore(active_limit=args.active_limit)).tune(target, args.budget)
    warm = tuner.tune(target, args.budget)
    print()
    _print_result("cold", cold)
    _print_result("warm", warm)
    print(
        f"\nExperience: cold-evidence={store.cold_count} "
        f"active-memory={store.active_count}/{store.active_limit} path={path}"
    )
    return 0


def command_bench(args: argparse.Namespace) -> int:
    warm_store = ExperienceStore(active_limit=args.active_limit)
    warm_tuner = _tuner(warm_store)
    for memory in (8, 32):
        for shape in (256, 512, 1024, 2048):
            warm_tuner.tune(Context("branching-mlp", shape, memory), budget=5)

    cold_hcr: list[float] = []
    warm_hcr: list[float] = []
    print(f"Raveil v{__version__} transfer benchmark, budget={args.budget}")
    for memory in (8, 32):
        for shape in (384, 768, 1536, 3072):
            context = Context("branching-mlp", shape, memory)
            cold = _tuner(ExperienceStore(active_limit=args.active_limit)).tune(context, args.budget)
            warm = _tuner(warm_store.fork()).tune(context, args.budget)
            cold_hcr.append(cold.headroom_capture)
            warm_hcr.append(warm.headroom_capture)
            print(
                f"shape={shape:4} memory={memory:2}KiB "
                f"cold={cold.headroom_capture:6.1%} warm={warm.headroom_capture:6.1%} "
                f"warm-best={warm.best.candidate.candidate_id}"
            )
    print(
        f"mean HCR: cold={statistics.mean(cold_hcr):.1%} "
        f"warm={statistics.mean(warm_hcr):.1%} "
        f"delta={statistics.mean(warm_hcr) - statistics.mean(cold_hcr):+.1%}"
    )
    return 0


def command_inspect(args: argparse.Namespace) -> int:
    store = ExperienceStore(Path(args.experience), active_limit=args.active_limit)
    print(f"Raveil v{__version__}")
    print(f"cold-evidence={store.cold_count}")
    print(f"active-memory={store.active_count}/{store.active_limit}")
    for record in sorted(store.active_records(), key=lambda item: item.sequence):
        ratio = "invalid" if not record.metrics.valid else f"{record.relative_cycles:.3f}x"
        print(
            f"seq={record.sequence:4} n={record.samples:3} "
            f"shape={record.context.shape:5} memory={record.context.memory_budget_kib:3}KiB "
            f"candidate={record.candidate.candidate_id:<10} relative={ratio}"
        )
    return 0


def command_experiment_run(args: argparse.Namespace) -> int:
    bundle, valid = run_experiment(
        Path(args.manifest),
        Path(args.artifact_root),
        policy_selections_path=(
            Path(args.policy_selections) if args.policy_selections else None
        ),
    )
    print(f"RUN-ID={bundle.run_id}")
    print(f"local-bundle={bundle.path}")
    if not valid:
        print("run incomplete: fail-closed measurement failure")
        return 2
    print("run captured; analyze and seal before sync")
    return 0


def command_experiment_plan(args: argparse.Namespace) -> int:
    source = find_bundle(Path(args.artifact_root), args.source_run)
    source_verification = source.verify()
    source_manifest = BenchmarkManifest.from_dict(
        json.loads((source.path / "manifest.json").read_text(encoding="utf-8"))
    )
    target_manifest = BenchmarkManifest.load(Path(args.manifest))
    selections = generate_policy_selections(
        target_manifest,
        source_manifest,
        load_measurements(source.path / "measurement.jsonl"),
        source_verification["bundle_hash"],
    )
    output = Path(args.output)
    write_policy_selections(output, selections)
    print(f"policy selections={len(selections)} output={output}")
    return 0


def command_experiment_preflight(args: argparse.Namespace) -> int:
    result = preflight_experiment(Path(args.manifest))
    if result.cpu_power_mw is None:
        print("preflight ready; energy sampling is not required by this manifest")
    else:
        print(
            f"preflight ready; thermal={result.thermal_level} "
            f"cpu-power-mw={result.cpu_power_mw:.3f}"
        )
    return 0


def command_experiment_analyze(args: argparse.Namespace) -> int:
    bundle = find_bundle(Path(args.artifact_root), args.run)
    result = analyze_bundle(bundle)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def command_experiment_seal(args: argparse.Namespace) -> int:
    bundle = find_bundle(Path(args.artifact_root), args.run)
    result = seal_bundle(bundle)
    print(f"sealed RUN-ID={bundle.run_id} bundle-sha256={result['bundle_hash']}")
    return 0


def command_experiment_sync(args: argparse.Namespace) -> int:
    bundle = find_bundle(Path(args.artifact_root), args.run)
    remote = bundle.sync(
        args.remote_root,
        rclone=args.rclone,
        config=Path(args.rclone_config) if args.rclone_config else None,
    )
    print(f"complete RUN-ID={bundle.run_id} remote={remote}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Raveil minimum Experience-loop prototype")
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    demo = subparsers.add_parser("demo", help="compare cold and warm tuning")
    demo.add_argument("--experience", default="experience/local.jsonl")
    demo.add_argument("--active-limit", type=int, default=64)
    demo.add_argument("--memory-kib", type=int, default=32)
    demo.add_argument("--target-shape", type=int, default=1536)
    demo.add_argument("--budget", type=int, default=2)
    demo.add_argument("--reset", action="store_true")
    demo.set_defaults(handler=command_demo)

    bench = subparsers.add_parser("bench", help="run shape/memory holdout benchmark")
    bench.add_argument("--active-limit", type=int, default=64)
    bench.add_argument("--budget", type=int, default=2)
    bench.set_defaults(handler=command_bench)

    inspect = subparsers.add_parser("inspect", help="show bounded active Experience")
    inspect.add_argument("--experience", default="experience/local.jsonl")
    inspect.add_argument("--active-limit", type=int, default=64)
    inspect.set_defaults(handler=command_inspect)

    experiment = subparsers.add_parser("experiment", help="run and preserve Gate experiments")
    experiment_commands = experiment.add_subparsers(dest="experiment_command", required=True)

    experiment_preflight = experiment_commands.add_parser(
        "preflight", help="verify the least-privilege measurement helper"
    )
    experiment_preflight.add_argument("--manifest", required=True)
    experiment_preflight.set_defaults(handler=command_experiment_preflight)

    experiment_run = experiment_commands.add_parser("run", help="execute a versioned manifest")
    experiment_run.add_argument("--manifest", required=True)
    experiment_run.add_argument("--artifact-root", default="artifacts/research")
    experiment_run.add_argument("--policy-selections")
    experiment_run.set_defaults(handler=command_experiment_run)

    experiment_plan = experiment_commands.add_parser(
        "plan", help="pre-register policy candidate slates from a sealed source run"
    )
    experiment_plan.add_argument("--manifest", required=True)
    experiment_plan.add_argument("--source-run", required=True)
    experiment_plan.add_argument("--output", required=True)
    experiment_plan.add_argument("--artifact-root", default="artifacts/research")
    experiment_plan.set_defaults(handler=command_experiment_plan)

    experiment_analyze = experiment_commands.add_parser("analyze", help="analyze a local run")
    experiment_analyze.add_argument("--run", required=True)
    experiment_analyze.add_argument("--artifact-root", default="artifacts/research")
    experiment_analyze.set_defaults(handler=command_experiment_analyze)

    experiment_seal = experiment_commands.add_parser("seal", help="seal an analyzed run")
    experiment_seal.add_argument("--run", required=True)
    experiment_seal.add_argument("--artifact-root", default="artifacts/research")
    experiment_seal.set_defaults(handler=command_experiment_seal)

    experiment_sync = experiment_commands.add_parser("sync", help="immutably copy and verify a sealed run")
    experiment_sync.add_argument("--run", required=True)
    experiment_sync.add_argument("--artifact-root", default="artifacts/research")
    experiment_sync.add_argument("--remote-root", default="gdrive:Raveil/research-data")
    experiment_sync.add_argument("--rclone", default="rclone")
    experiment_sync.add_argument("--rclone-config")
    experiment_sync.set_defaults(handler=command_experiment_sync)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.handler(args)
    except (FileExistsError, FileNotFoundError, RuntimeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
