from __future__ import annotations

import argparse
from pathlib import Path
import statistics

from . import __version__
from .backend import ToyDaphnis
from .experience import ExperienceStore
from .model import Context, seed_candidates
from .policy import NearestExperiencePolicy, Tuner, TuningResult


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
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.handler(args)
