from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import statistics
import sys
import tempfile

from . import __version__
from .backend import ToyDaphnis
from .experience import ExperienceStore
from .completion_telemetry import CompletionTelemetryStore
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
from .graph_mvp import GraphProgram, run_graph_mvp
from .graph_directory import materialize as materialize_graph_directory
from .native_backend import NativeCBackend
from .sonatine_backend import SonatineQEMUBackend
from .sonatine_demo import MAX_TIMEOUT_SECONDS, run_sonatine_demo
from .iree_import import PinnedIreeImporter
from .interactive_shell import NativeInteractiveSession, run_interactive_shell
from .workspace import NativeWorkspace
from .command_showcase import list_showcases, mutate_showcase, prepare_showcase, run_showcase
from .project import add_project_parser
from .garden import (
    load_garden_view, render_empty, render_error, render_key_session,
    run_interactive, validate_render_width,
)
from .graph_device_submit import render_submission
from .graph_device_run import run as run_graph_device
from .graph_device_runtime_pair import run_pair as run_graph_device_pair
from .kv260_preflight import Kv260PreflightError, render_preflight
from .graph_device_dynamic import GraphDeviceDynamicError, run_dynamic, run_dynamic_pair
from .graph_device_dynamic_sealed import GraphDeviceDynamicSealError, run_sealed, seal as seal_dynamic
from .graph_device_uio_dry_run import plan as uio_dry_run_plan


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


def command_completion_ingest(args: argparse.Namespace) -> int:
    store = CompletionTelemetryStore(Path(args.store))
    appended = store.ingest_qemu_log(Path(args.input), args.run_id)
    print(f"completion-telemetry appended={appended} total={len(store.load())}")
    return 0


def command_completion_inspect(args: argparse.Namespace) -> int:
    records = CompletionTelemetryStore(Path(args.store)).load()
    print(f"completion-telemetry total={len(records)}")
    for record in records:
        print(
            f"seq={record.sequence} run={record.run_id} job={record.job_id} "
            f"execution={record.execution_epoch}:{record.execution_sequence} "
            f"status={record.observed_status} evidence={record.evidence_class}"
        )
    return 0


def command_experiment_run(args: argparse.Namespace) -> int:
    bundle, valid = run_experiment(
        Path(args.manifest),
        Path(args.artifact_root),
        policy_selections_path=(
            Path(args.policy_selections) if args.policy_selections else None
        ),
        cooldown_seconds=args.cooldown_seconds,
        cooldown_max_seconds=args.cooldown_max_seconds,
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


def command_graph_mvp(args: argparse.Namespace) -> int:
    imported = None
    if args.import_manifest:
        if not args.output:
            raise ValueError("--import-manifest requires --output for segregated provenance")
        requested_output = Path(args.output)
        requested_import_output = requested_output.with_name(
            requested_output.name + ".import.json"
        )
        if os.path.lexists(requested_output) or os.path.lexists(requested_import_output):
            raise FileExistsError("graph result or import provenance target already exists")
        imported = PinnedIreeImporter(
            Path(args.iree_compile), timeout_seconds=args.timeout_seconds
        ).import_program(Path(args.import_manifest))
        program = imported.program
    else:
        program = GraphProgram.create(args.family, args.m, args.n, args.k)
    with tempfile.TemporaryDirectory(prefix="raveil-graph-mvp-") as directory:
        if args.backend == "native":
            backend = NativeCBackend(
                Path(args.source), Path(directory) / "raveil-native",
                compiler=args.compiler,
                compiler_flags=(
                    "-O3", "-std=c11", "-Wall", "-Wextra", "-Werror",
                    "-D_POSIX_C_SOURCE=200809L",
                ),
                timeout_seconds=args.timeout_seconds, warmups=args.warmups,
            )
            compile_command = backend.compile()
        else:
            backend = SonatineQEMUBackend(
                Path(args.sonatine_kernel), qemu=args.qemu,
                timeout_seconds=args.timeout_seconds,
            )
            compile_command = ()
        result = run_graph_mvp(
            program,
            backend,
            minimum_predicted_improvement=args.minimum_predicted_improvement,
            inner_iterations=args.inner_iterations,
        ).to_dict()
    if args.backend == "native":
        result["backend"] = "native-c-posix-userspace"
        result["compile_command"] = [*compile_command[:-1], "<temporary>/raveil-native"]
        result["compile_command_kind"] = "logical-portable"
    else:
        result["backend"] = "sonatine-qemu-v1"
        result["evidence_class"] = "qemu-emulation-correctness"
        result["compile_command"] = []
        result["compile_command_kind"] = "prebuilt-kernel"
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        message = f"graph MVP outcome={result['outcome']} output={output}"
        if imported is not None:
            import_output = output.with_name(output.name + ".import.json")
            with import_output.open("x", encoding="utf-8") as stream:
                json.dump(imported.record.to_dict(), stream, indent=2, sort_keys=True)
                stream.write("\n")
            message += f" import-record={import_output}"
        with output.open("x", encoding="utf-8") as stream:
            stream.write(encoded)
        print(message)
    else:
        print(encoded, end="")
    return 2 if result["outcome"] == "failed-closed" else 0


def command_sonatine_demo(args: argparse.Namespace) -> int:
    result = run_sonatine_demo(
        Path(args.sonatine_kernel), Path(args.output), qemu=args.qemu,
        timeout_seconds=args.timeout_seconds,
    )
    print(
        f"sonatine demo evidence={result.evidence_class} "
        f"output={args.output} final-state={result.final_job_state}"
    )
    return 0


def command_shell(args: argparse.Namespace) -> int:
    return run_interactive_shell(NativeInteractiveSession(
        source=Path(args.source), compiler=args.compiler,
        workspace=NativeWorkspace(Path(args.workspace)),
        timeout_seconds=args.timeout_seconds, warmups=args.warmups,
        inner_iterations=args.inner_iterations,
        minimum_predicted_improvement=args.minimum_predicted_improvement,
    ))


def command_showcase_list(args: argparse.Namespace) -> int:
    print(list_showcases())
    return 0


def command_showcase_prepare(args: argparse.Namespace) -> int:
    print(prepare_showcase(NativeWorkspace(Path(args.workspace)), args.scenario, args.nodes))
    return 0


def command_showcase_run(args: argparse.Namespace) -> int:
    print(run_showcase(NativeWorkspace(Path(args.workspace)), args.scenario, args.nodes))
    return 0


def command_showcase_mutate(args: argparse.Namespace) -> int:
    print(mutate_showcase(NativeWorkspace(Path(args.workspace)), args.scenario, args.node, args.nodes))
    return 0


def command_garden(args: argparse.Namespace) -> int:
    validate_render_width(args.width)
    if args.empty:
        if args.keys is not None:
            print(render_error("--keys cannot be used with --empty"), file=sys.stderr)
            return 2
        print(render_empty())
        return 0
    try:
        snapshot = load_garden_view(args.fixture)
        if args.keys is not None:
            print(render_key_session(snapshot, args.keys, args.width))
            return 0
        return run_interactive(snapshot, sys.stdin, sys.stdout, args.width)
    except (FileNotFoundError, OSError, ValueError) as error:
        print(render_error(str(error)), file=sys.stderr)
        return 2


def command_graph_directory(args: argparse.Namespace) -> int:
    try:
        manifest_sha256 = materialize_graph_directory(
            Path(args.program), Path(args.result), Path(args.output)
        )
    except (OSError, ValueError) as error:
        print(f"graph-directory: {error}", file=sys.stderr)
        return 2
    print(f"graph-directory manifest_sha256={manifest_sha256}")
    return 0


def command_graph_device_submit(args: argparse.Namespace) -> int:
    print(render_submission(args.graph, args.seed))
    return 0


def command_graph_device_run(args: argparse.Namespace) -> int:
    print(run_graph_device(args.graph, args.seed, transport=args.transport))
    return 0


def command_graph_device_run_pair(args: argparse.Namespace) -> int:
    print(run_graph_device_pair(args.graph, args.seed))
    return 0


def command_graph_device_dynamic_run_pair(args: argparse.Namespace) -> int:
    print(run_dynamic_pair(args.graph, args.seed))
    return 0


def command_graph_device_dynamic_run(args: argparse.Namespace) -> int:
    print(run_dynamic(args.graph, args.seed))
    return 0


def command_graph_device_dynamic_seal(args: argparse.Namespace) -> int:
    print(json.dumps(seal_dynamic(args.graph, args.seed, Path.cwd()), sort_keys=True))
    return 0


def command_graph_device_dynamic_uio_dry_run(args: argparse.Namespace) -> int:
    print(json.dumps(uio_dry_run_plan(Path(args.sealed), args.device, Path.cwd()), sort_keys=True))
    return 0


def command_graph_device_dynamic_replay(args: argparse.Namespace) -> int:
    print(json.dumps(run_sealed(Path(args.sealed), Path.cwd()), sort_keys=True))
    return 0


def command_kv260_preflight(args: argparse.Namespace) -> int:
    try:
        print(render_preflight(args.device))
    except (Kv260PreflightError, OSError) as error:
        print(f"kv260-preflight: {error}", file=sys.stderr)
        return 2
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Raveil minimum Experience-loop prototype")
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    add_project_parser(subparsers)

    garden = subparsers.add_parser("garden", help="browse one validated graph snapshot read-only")
    garden_source = garden.add_mutually_exclusive_group(required=True)
    garden_source.add_argument("--fixture", help="strict versioned Garden snapshot JSON")
    garden_source.add_argument("--empty", action="store_true", help="render the explicit empty state")
    garden.add_argument(
        "--keys",
        help="deterministic bounded navigation transcript using j, k, g, G, q",
    )
    garden.add_argument(
        "--width", type=int, default=150,
        help="deterministic render width from 72 to 240 (default: 150)",
    )
    garden.set_defaults(handler=command_garden)

    graph_directory = subparsers.add_parser(
        "graph-directory", help="materialize one strict Graph MVP snapshot for read-only inspection"
    )
    graph_directory.add_argument("--program", required=True, help="strict existing-v1 graph program JSON")
    graph_directory.add_argument("--result", required=True, help="strict existing-v1 Graph MVP result JSON")
    graph_directory.add_argument("--output", required=True, help="existing empty output directory")
    graph_directory.set_defaults(handler=command_graph_directory)

    shell = subparsers.add_parser("shell", help="open the Native userspace graph session")
    shell.add_argument(
        "--workspace", default=".",
        help="existing host directory exposed as virtual / (default: current directory)",
    )
    shell.add_argument("--compiler", default="cc")
    shell.add_argument("--source", default="benchmarks/native/benchmark.c")
    shell.add_argument("--timeout-seconds", type=float, default=30.0)
    shell.add_argument("--warmups", type=int, default=1)
    shell.add_argument("--inner-iterations", type=int, default=1)
    shell.add_argument("--minimum-predicted-improvement", type=float, default=0.05)
    shell.set_defaults(handler=command_shell)

    showcase = subparsers.add_parser("showcase", help="run the synthetic Native Command Graph walkthrough")
    showcase_commands = showcase.add_subparsers(dest="showcase_command", required=True)
    showcase_list = showcase_commands.add_parser("list", help="list synthetic non-claim showcases")
    showcase_list.set_defaults(handler=command_showcase_list)
    for name, handler, help_text in (
        ("prepare", command_showcase_prepare, "create deterministic inputs exclusively"),
        ("run", command_showcase_run, "run baseline-first synthetic comparison"),
        ("mutate", command_showcase_mutate, "add one deterministic changed input"),
    ):
        command = showcase_commands.add_parser(name, help=help_text)
        command.add_argument("--workspace", required=True, help="existing empty-or-prepared host directory")
        command.add_argument("--scenario", choices=("showcase-parallel", "showcase-incremental", "control-small"),
                             default="showcase-parallel")
        if name != "mutate":
            command.add_argument("--nodes", type=int, choices=(16, 32, 64))
        else:
            command.add_argument("--nodes", type=int, choices=(16, 32, 64))
            command.add_argument("--node", type=int, default=0)
        command.set_defaults(handler=handler)

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

    experience = subparsers.add_parser(
        "experience", help="manage segregated append-only Experience evidence"
    )
    experience_commands = experience.add_subparsers(
        dest="experience_command", required=True
    )
    completion_ingest = experience_commands.add_parser(
        "ingest-completions", help="ingest Sonatine QEMU completion telemetry"
    )
    completion_ingest.add_argument("--input", required=True)
    completion_ingest.add_argument("--store", required=True)
    completion_ingest.add_argument("--run-id", required=True)
    completion_ingest.set_defaults(handler=command_completion_ingest)
    completion_inspect = experience_commands.add_parser(
        "inspect-completions", help="inspect completion cold evidence"
    )
    completion_inspect.add_argument("--store", required=True)
    completion_inspect.set_defaults(handler=command_completion_inspect)

    graph_mvp = subparsers.add_parser(
        "graph-mvp", help="run one owned userspace graph through the guarded MVP loop"
    )
    graph_mvp.add_argument(
        "--family", choices=("gemm", "gemm_bias_relu"), default="gemm_bias_relu"
    )
    graph_mvp.add_argument("--backend", choices=("native", "sonatine-qemu"), default="native")
    graph_mvp.add_argument("--m", type=int, default=64)
    graph_mvp.add_argument("--n", type=int, default=64)
    graph_mvp.add_argument("--k", type=int, default=64)
    graph_mvp.add_argument("--inner-iterations", type=int, default=1)
    graph_mvp.add_argument("--warmups", type=int, default=1)
    graph_mvp.add_argument("--timeout-seconds", type=float, default=30.0)
    graph_mvp.add_argument("--minimum-predicted-improvement", type=float, default=0.05)
    graph_mvp.add_argument("--compiler", default="cc")
    graph_mvp.add_argument("--source", default="benchmarks/native/benchmark.c")
    graph_mvp.add_argument("--sonatine-kernel", default="sonatine/build/sonatine.elf")
    graph_mvp.add_argument("--qemu", default="qemu-system-riscv64")
    graph_mvp.add_argument(
        "--import-manifest",
        help="validate one pinned MLIR fixture and run its Raveil-owned graph",
    )
    graph_mvp.add_argument("--iree-compile", default="iree-compile")
    graph_mvp.add_argument("--output")
    graph_mvp.set_defaults(handler=command_graph_mvp)

    graph_device = subparsers.add_parser(
        "graph-device", help="admit or run one accepted Graph-device descriptor"
    )
    graph_device_commands = graph_device.add_subparsers(
        dest="graph_device_command", required=True
    )
    graph_device_submit = graph_device_commands.add_parser(
        "submit", help="bind one canonical descriptor to a non-executing submission"
    )
    graph_device_submit.add_argument("--graph", required=True)
    graph_device_submit.add_argument("--seed", type=int, required=True)
    graph_device_submit.set_defaults(handler=command_graph_device_submit)
    graph_device_run = graph_device_commands.add_parser(
        "run", help="run one accepted descriptor through the selected RTL simulator"
    )
    graph_device_run.add_argument("--graph", required=True)
    graph_device_run.add_argument("--seed", type=int, required=True)
    graph_device_run.add_argument(
        "--transport", choices=("selected-rtl", "axi4lite-sim", "axi4lite-catalogue-sim"), default="selected-rtl",
        help=("selected-rtl preserves the default single-Graph path; "
              "axi4lite-sim executes the admitted request through AXI4-Lite; "
              "axi4lite-catalogue-sim preserves the S04 full-catalogue regression"),
    )
    graph_device_run.set_defaults(handler=command_graph_device_run)
    graph_device_pair = graph_device_commands.add_parser(
        "run-pair",
        help="run exactly two admitted requests through one AXI4-Lite simulator build",
    )
    graph_device_pair.add_argument("--graph", action="append", required=True)
    graph_device_pair.add_argument("--seed", action="append", type=int, required=True)
    graph_device_pair.set_defaults(handler=command_graph_device_run_pair)
    dynamic_pair = graph_device_commands.add_parser(
        "dynamic-run-pair",
        help="compile exactly two bounded requests and run one shared RTL simulator twice",
    )
    dynamic_pair.add_argument("--descriptor", dest="graph", action="append", required=True)
    dynamic_pair.add_argument("--seed", action="append", type=int, required=True)
    dynamic_pair.set_defaults(handler=command_graph_device_dynamic_run_pair)
    dynamic_run = graph_device_commands.add_parser(
        "dynamic-run",
        help="compile one non-catalogue bounded request and run one shared RTL simulator",
    )
    dynamic_run.add_argument("--descriptor", dest="graph", required=True)
    dynamic_run.add_argument("--seed", type=int, required=True)
    dynamic_run.set_defaults(handler=command_graph_device_dynamic_run)
    dynamic_seal = graph_device_commands.add_parser(
        "dynamic-seal", help="compile once and exclusively seal one non-catalogue request",
    )
    dynamic_seal.add_argument("--descriptor", dest="graph", required=True)
    dynamic_seal.add_argument("--seed", type=int, required=True)
    dynamic_seal.set_defaults(handler=command_graph_device_dynamic_seal)
    dynamic_replay = graph_device_commands.add_parser(
        "dynamic-replay", help="materialize verified sealed payloads without descriptor reparse",
    )
    dynamic_replay.add_argument("--sealed", required=True)
    dynamic_replay.set_defaults(handler=command_graph_device_dynamic_replay)
    dynamic_uio = graph_device_commands.add_parser(
        "dynamic-uio-dry-run", help="plan verified sealed payload transport without opening UIO",
    )
    dynamic_uio.add_argument("--sealed", required=True)
    dynamic_uio.add_argument("--device", required=True)
    dynamic_uio.set_defaults(handler=command_graph_device_dynamic_uio_dry_run)
    kv260_preflight = graph_device_commands.add_parser(
        "kv260-preflight",
        help="check KV260 Linux/UIO readiness without opening the device",
    )
    kv260_preflight.add_argument(
        "--device", required=True, help="canonical UIO character device path /dev/uioN"
    )
    kv260_preflight.set_defaults(handler=command_kv260_preflight)

    sonatine_demo = subparsers.add_parser(
        "sonatine-demo", help="run the fixed Sonatine operator demo under QEMU"
    )
    sonatine_demo.add_argument("--sonatine-kernel", default="sonatine/build/sonatine.elf")
    sonatine_demo.add_argument("--qemu", default="qemu-system-riscv64")
    sonatine_demo.add_argument(
        "--timeout-seconds", type=float, default=30.0,
        help=f"finite QEMU timeout in seconds (maximum {MAX_TIMEOUT_SECONDS:g})",
    )
    sonatine_demo.add_argument("--output", required=True)
    sonatine_demo.set_defaults(handler=command_sonatine_demo)

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
    experiment_run.add_argument("--cooldown-seconds", type=float, default=0)
    experiment_run.add_argument("--cooldown-max-seconds", type=float, default=1800)
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
    except (FileExistsError, FileNotFoundError, OSError, RuntimeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
