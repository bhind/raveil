#!/bin/sh
# Structural, pre-data preflight for the shared Option-B memory source.
# Runs seven fresh Yosys processes and deliberately stops before storage expansion,
# candidate export, synthesis mapping, P&R, timing, area, or energy collection.
set -eu
umask 077

fail() { printf 'error: %s\n' "$*" >&2; exit 1; }
sha256_file() { shasum -a 256 "$1" | awk '{print $1}'; }

[ "$#" -eq 1 ] || fail 'usage: run-exp0011-stdcell-memory-preflight.sh APPEND_ONLY_OUTPUT_DIR'
output_dir=$1
[ ! -e "$output_dir" ] || fail "append-only output path already exists: $output_dir"

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
source_rel=hardware/chisel/exp0011_common_stdcell_memories.sv
runner_rel=hardware/chisel/run-exp0011-stdcell-memory-preflight.sh
receipt_rel=docs/experiments/receipts/T-0044-EXP-0011-physical-input-readiness.json
inventory_rel=hardware/chisel/check-exp0011-macro-views.sh
[ -s "$repo_root/$source_rel" ] || fail 'shared memory source is missing'
[ -s "$repo_root/$receipt_rel" ] || fail 'physical-input readiness receipt is missing'
command -v docker >/dev/null 2>&1 || fail 'docker is required'

image=raveil-physical-proxy-toolchain:v1
platform=linux/amd64
expected_image_id=sha256:7a0db885c100695626175931d3e053ba6a1602d949167b83e2ef60888eea7169
expected_rootfs_sha256=21620b37d8c2f62d831d186304b2b32912e6f0d5d34ca14a8e659edbbdfbeac5
expected_receipt_sha256=0c64aa343b6801c0846744364f2d5dece7af00e26648d53b437de51ea74f3945
expected_inventory_runner_sha256=9ff24ece4f418edb706857048507b8c63bd05ad6b4901a242bfbec3199583d18

[ "$(sha256_file "$repo_root/$receipt_rel")" = "$expected_receipt_sha256" ] ||
    fail 'merged physical-input readiness receipt drift'
[ "$(sha256_file "$repo_root/$inventory_rel")" = "$expected_inventory_runner_sha256" ] ||
    fail 'merged physical-input inventory runner drift'

image_id=$(docker image inspect --format '{{.Id}}' "$image")
rootfs_sha256=$(docker image inspect --format '{{json .RootFS.Layers}}' "$image" |
    shasum -a 256 | awk '{print $1}')
[ "$image_id" = "$expected_image_id" ] || fail "physical toolchain image ID drift: $image_id"
[ "$rootfs_sha256" = "$expected_rootfs_sha256" ] || fail "physical toolchain RootFS drift: $rootfs_sha256"

mkdir "$output_dir"
output_dir=$(CDPATH= cd -- "$output_dir" && pwd)
mkdir "$output_dir/raw" "$output_dir/derived"
raw_dir=$output_dir/raw
derived_dir=$output_dir/derived

# The file identities come from the merged readiness receipt, but this run also
# recomputes them from the exact files inside the pinned image.
docker run --rm --platform "$platform" --network none \
    --security-opt no-new-privileges=true \
    --mount "type=bind,source=$repo_root,target=/repo,readonly" \
    --mount "type=bind,source=$raw_dir,target=/out" \
    "$image" sh -c 'set -eu
lib=/home/mambauser/physical-mamba/envs/toolchain/share/pdk/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib
cell_lef=/home/mambauser/physical-mamba/envs/toolchain/share/pdk/sky130A/libs.ref/sky130_fd_sc_hd/lef/sky130_fd_sc_hd.lef
tech_lef=/home/mambauser/physical-mamba/envs/toolchain/share/pdk/sky130A/libs.ref/sky130_fd_sc_hd/techlef/sky130_fd_sc_hd__nom.tlef
rcx=/home/mambauser/physical-mamba/envs/toolchain/share/pdk/sky130A/libs.tech/openlane/rules.openrcx.sky130A.nom.spef_extractor
yosys_bin=$(command -v yosys)
test "$(sha256sum "$lib" | cut -d" " -f1)" = e66aab4e0a3eef8d0b13eb5b75aaadb725ba78b032203342eb1e419a2c111baf
test "$(sha256sum "$cell_lef" | cut -d" " -f1)" = cf8bcac8e831cff18c22a80999af3a97c8247028cd7dbbcdd8e3b73f725069ec
test "$(sha256sum "$tech_lef" | cut -d" " -f1)" = 1a18b353fb5457caf0eca5b3cb28b2c0c9bbacdbbdeee7c4fc64a115932066c2
test "$(sha256sum "$rcx" | cut -d" " -f1)" = 682de2d5ceba1fffbdd58ee3033b2ab89ac81ced4ad3f51406f77a05ec4bca8b
test "$(sha256sum "$yosys_bin" | cut -d" " -f1)" = a078aea6eafafcfe9ed4b1d343acdc612f74ad078efb7b930ed1333968ce7508
test "$(yosys -V)" = "Yosys 0.27+3 (git sha1 b58664d44, x86_64-conda-linux-gnu-cc 11.2.0 -fvisibility-inlines-hidden -fmessage-length=0 -march=nocona -mtune=haswell -ftree-vectorize -fPIC -fstack-protector-strong -fno-plt -O2 -ffunction-sections -fdebug-prefix-map=/root/conda-eda/conda-eda/workdir/conda-env/conda-bld/yosys_1678231241446/work=/usr/local/src/conda/yosys-0.27_4_gb58664d44 -fdebug-prefix-map=/home/mambauser/physical-mamba/envs/toolchain=/usr/local/src/conda-prefix -fPIC -Os -fno-merge-constants)"
{
  printf "standard_cell_liberty_sha256=e66aab4e0a3eef8d0b13eb5b75aaadb725ba78b032203342eb1e419a2c111baf\n"
  printf "standard_cell_lef_sha256=cf8bcac8e831cff18c22a80999af3a97c8247028cd7dbbcdd8e3b73f725069ec\n"
  printf "technology_lef_sha256=1a18b353fb5457caf0eca5b3cb28b2c0c9bbacdbbdeee7c4fc64a115932066c2\n"
  printf "openrcx_rule_sha256=682de2d5ceba1fffbdd58ee3033b2ab89ac81ced4ad3f51406f77a05ec4bca8b\n"
  printf "yosys_sha256=a078aea6eafafcfe9ed4b1d343acdc612f74ad078efb7b930ed1333968ce7508\n"
  printf "yosys_version=0.27+3\n"
  printf "yosys_revision=b58664d44\n"
} > /out/physical-input-identities.txt

cd /repo
tops="cc_dir_ext cc_banks_0_ext data_arrays_0_ext tag_array_ext tag_array_0_ext data_arrays_0_0_ext memory_ext"
for top in $tops; do
  script=/tmp/$top.ys
  {
    printf "read_verilog -sv hardware/chisel/exp0011_common_stdcell_memories.sv\n"
    printf "hierarchy -check -top %s\n" "$top"
    printf "proc\n"
    printf "memory_collect\n"
    printf "check -assert\n"
    printf "select -assert-none a:blackbox=1\n"
    printf "select -assert-count 1 t:\$mem_v2\n"
    printf "tee -o /out/%s-stat.txt stat\n" "$top"
    printf "write_json /out/%s-memory.json\n" "$top"
  } > "$script"
  cp "$script" "/out/$top-yosys.ys"
  # This invocation is intentionally inside the loop: every top receives a
  # fresh, unpruned Yosys design and process.
  yosys -Q -T -l "/out/$top-yosys.log" -s "$script"
done
'

# Validate the exact collected-memory organization and emit a readable derived
# report. This does not map the memories into 4,631,296 DFF storage bits.
python3 - "$raw_dir" "$derived_dir/memory-structure.json" <<'PY'
import json
import pathlib
import sys

raw = pathlib.Path(sys.argv[1])
out = pathlib.Path(sys.argv[2])
expected = {
    "cc_dir_ext": (1024, 128, 1, 8, "one-rw-synchronous-read-masked-write-16"),
    "cc_banks_0_ext": (16384, 64, 1, 1, "one-rw-synchronous-read-full-write"),
    "data_arrays_0_ext": (512, 256, 1, 32, "one-rw-synchronous-read-masked-write-8"),
    "tag_array_ext": (64, 88, 1, 4, "one-rw-synchronous-read-masked-write-22"),
    "tag_array_0_ext": (64, 84, 1, 4, "one-rw-synchronous-read-masked-write-21"),
    "data_arrays_0_0_ext": (512, 128, 1, 4, "one-rw-synchronous-read-masked-write-32"),
    "memory_ext": (1024, 32, 1, 4, "separate-read-write-clocks-synchronous-read-byte-write"),
}

def number(value):
    if isinstance(value, int):
        return value
    if not isinstance(value, str) or any(ch not in "01" for ch in value):
        raise SystemExit("unexpected Yosys numeric parameter encoding")
    return int(value, 2)

report = {}
for top, (depth, width, reads, writes, organization) in expected.items():
    design = json.loads((raw / f"{top}-memory.json").read_text())
    module = design["modules"].get(top)
    if module is None:
        raise SystemExit(f"missing selected top in Yosys JSON: {top}")
    if any(number(m.get("attributes", {}).get("blackbox", 0)) for m in design["modules"].values()):
        raise SystemExit(f"reachable blackbox in {top}")
    memories = [cell for cell in module["cells"].values() if cell["type"] == "$mem_v2"]
    if len(memories) != 1:
        raise SystemExit(f"{top}: expected exactly one collected memory")
    params = memories[0]["parameters"]
    actual = tuple(number(params[key]) for key in ("SIZE", "WIDTH", "RD_PORTS", "WR_PORTS"))
    if actual != (depth, width, reads, writes):
        raise SystemExit(f"{top}: memory organization drift: {actual}")
    report[top] = {
        "depth": depth, "width": width, "read_ports": reads,
        "yosys_write_fragments": writes, "organization": organization,
        "collected_memories": 1, "reachable_blackboxes": 0,
    }
(out).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
PY

find "$raw_dir" -type f ! -name sha256s.txt -print | LC_ALL=C sort |
    while IFS= read -r file; do
        printf '%s  %s\n' "$(sha256_file "$file")" "$(basename "$file")"
    done > "$raw_dir/sha256s.txt"
raw_manifest_sha256=$(sha256_file "$raw_dir/sha256s.txt")
source_sha256=$(sha256_file "$repo_root/$source_rel")
runner_sha256=$(sha256_file "$repo_root/$runner_rel")

python3 - "$derived_dir/preflight-metadata.json" <<PY
import json
import pathlib
record = {
    "schema": "raveil.exp-0011-common-stdcell-memory-preflight/v2",
    "task_id": "T-0044",
    "authority_commit": "$(git -C "$repo_root" rev-parse HEAD)",
    "image": "$image", "image_id": "$image_id",
    "image_rootfs_sha256": "$rootfs_sha256", "platform": "$platform",
    "source_sha256": "$source_sha256", "runner_sha256": "$runner_sha256",
    "readiness_receipt_sha256": "$expected_receipt_sha256",
    "inventory_runner_sha256": "$expected_inventory_runner_sha256",
    "yosys_sha256": "a078aea6eafafcfe9ed4b1d343acdc612f74ad078efb7b930ed1333968ce7508",
    "yosys_version": "0.27+3", "yosys_revision": "b58664d44",
    "raw_manifest_sha256": "$raw_manifest_sha256",
    "tops": ["cc_dir_ext", "cc_banks_0_ext", "data_arrays_0_ext", "tag_array_ext", "tag_array_0_ext", "data_arrays_0_0_ext", "memory_ext"],
    "fresh_yosys_processes": 7, "total_storage_bits": 4631296,
    "commands": ["read_verilog -sv", "hierarchy -check -top <one top>", "proc", "memory_collect", "check -assert", "assert one memory and zero reachable blackboxes", "stat"],
    "evidence_class": "physical-input-readiness-no-candidate-data",
    "experiment_id": None, "manifest_frozen": False,
    "preflight_evidence_collected": True,
    "claim_bearing_candidate_data_collected": False,
    "candidate_synthesis": False, "pnr": False,
    "nonclaims": ["no synthesis mapping", "no placement or routing", "no area, timing, energy, FPGA, ASIC, or silicon claim"],
}
pathlib.Path("$derived_dir/preflight-metadata.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
PY

find "$derived_dir" -type f ! -name sha256s.txt -print | LC_ALL=C sort |
    while IFS= read -r file; do
        printf '%s  %s\n' "$(sha256_file "$file")" "$(basename "$file")"
    done > "$derived_dir/sha256s.txt"
metadata_sha256=$(sha256_file "$derived_dir/preflight-metadata.json")
printf 'EXP0011-COMMON-STDCELL-MEMORY-PREFLIGHT-V2 status=OK tops=7 memories=7 total_storage_bits=4631296 blackboxes=0 candidate_data=false metadata_sha256=%s evidence=physical-input-readiness-no-candidate-data\n' "$metadata_sha256"
