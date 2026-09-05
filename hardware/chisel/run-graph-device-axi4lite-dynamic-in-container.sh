#!/bin/sh
set -eu
set -C
case "$#" in
  2) request_count=1; first=$1; second=; session_name=$2 ;;
  3) request_count=2; first=$1; second=$2; session_name=$3 ;;
  *) echo 'usage: ... REQUEST_ROOT [REQUEST_ROOT] SESSION_NAME' >&2; exit 2 ;;
esac
case "$first" in /session/*) ;; *) echo 'error: request root must be a /session child' >&2; exit 2;; esac
case "$session_name" in run.*) ;; *) echo 'error: retained session name is invalid' >&2; exit 2;; esac
test "$first" = /session/request-1 \
  || { echo 'error: first dynamic request must be /session/request-1' >&2; exit 2; }
if test "$request_count" = 2; then
  test "$second" = /session/request-2 || { echo 'error: second dynamic request must be /session/request-2' >&2; exit 2; }
fi
for root in "$first" ${second:+"$second"}; do
  for input in request.bin request-input.bin request-oracle.bin graph_device_abi_generated.h graph_device_affine_generated.h graph_device_dag_generated.h graph_device_axi4lite_aperture_generated.h; do
    test -f "$root/$input" && test ! -L "$root/$input" \
      || { echo "error: unsafe dynamic input $input" >&2; exit 2; }
  done
  test -d "$root/inputs" && test ! -L "$root/inputs" \
    || { echo 'error: unsafe dynamic input directory' >&2; exit 2; }
  for output in simulator.bin simulator.sha256 rtl.manifest source.manifest abi.manifest toolchain.txt device.log device.stderr axi-transcript.log dynamic-receipt.json; do
    test ! -e "$root/$output" && test ! -L "$root/$output" \
      || { echo "error: dynamic output already exists: $output" >&2; exit 2; }
  done
done
src=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
build=$(mktemp -d /tmp/raveil-axi4lite-dynamic.XXXXXX)
trap 'rm -rf "$build"' EXIT HUP INT TERM
mkdir -p "$build/chipyard-overlay"
for f in OwnedFixedLatencyScratchpad.scala StaticStencilRegion.scala GraphDeviceAffineConfigInstaller.scala GraphDeviceProgramInstaller.scala GraphDeviceAxi4LiteTop.scala graph_device_runtime.h graph_device_runtime.cpp graph_device_affine_runtime.h graph_device_affine_runtime.cpp graph_device_dag_runtime.h graph_device_dag_runtime.cpp graph_device_axi4lite_transport.h graph_device_axi4lite_dynamic_verilator.cpp; do cp "$src/$f" "$build/"; done
for f in RaveilFixtureInputProvider.scala RaveilStaticStencilCore.scala; do cp "$src/chipyard-overlay/$f" "$build/chipyard-overlay/"; done
cp /repo/linux/include/raveil_graph_device_dynamic_request.h /repo/linux/src/raveil_graph_device_dynamic_request.cpp "$build/"
for f in graph_device_abi_generated.h graph_device_affine_generated.h graph_device_dag_generated.h graph_device_axi4lite_aperture_generated.h; do cp "$first/$f" "$build/"; done
cd "$build"
{
  for file in GraphDeviceAxi4LiteTop.scala StaticStencilRegion.scala OwnedFixedLatencyScratchpad.scala GraphDeviceAffineConfigInstaller.scala GraphDeviceProgramInstaller.scala graph_device_runtime.h graph_device_runtime.cpp graph_device_affine_runtime.h graph_device_affine_runtime.cpp graph_device_dag_runtime.h graph_device_dag_runtime.cpp graph_device_axi4lite_transport.h graph_device_axi4lite_dynamic_verilator.cpp raveil_graph_device_dynamic_request.h raveil_graph_device_dynamic_request.cpp; do
    printf 'compiled/%s ' "$file"; sha256sum "$file" | awk '{print $1}'
  done
  for file in chipyard-overlay/RaveilFixtureInputProvider.scala chipyard-overlay/RaveilStaticStencilCore.scala; do
    printf 'compiled/%s ' "$file"; sha256sum "$file" | awk '{print $1}'
  done
  for file in graph_device_abi_generated.h graph_device_affine_generated.h graph_device_dag_generated.h graph_device_axi4lite_aperture_generated.h; do
    printf 'generated/%s ' "$file"; sha256sum "$file" | awk '{print $1}'
  done
  for file in hardware/chisel/Dockerfile hardware/chisel/run-graph-device-axi4lite-dynamic.sh hardware/chisel/run-graph-device-axi4lite-dynamic-in-container.sh contracts/graph_device_dynamic_request_v1.json contracts/graph_device_dynamic_request_v2.json contracts/graph_device_dynamic_request_v3.json contracts/graph_device_program_v2.json contracts/graph_device_program_v3.json contracts/graph_device_abi_v1.json contracts/graph_device_install_abi_v1.json contracts/graph_device_program_install_abi_v1.json raveil/graph_device_dynamic.py raveil/graph_device_dag.py raveil/graph_device_affine.py raveil/graph_device_mvp.py raveil/static_region.py raveil/riscv_stencil_signature.py; do
    printf 'orchestration/%s ' "$file"; sha256sum "/repo/$file" | awk '{print $1}'
  done
} | LC_ALL=C sort > /tmp/dynamic-source.manifest
for file in contracts/graph_device_abi_v1.json contracts/graph_device_install_abi_v1.json contracts/graph_device_program_install_abi_v1.json contracts/graph_device_dynamic_request_v1.json; do
  printf '%s ' "$file"; sha256sum "/repo/$file" | awk '{print $1}'
done | LC_ALL=C sort > /tmp/dynamic-abi.manifest
scala_sources='GraphDeviceAxi4LiteTop.scala StaticStencilRegion.scala OwnedFixedLatencyScratchpad.scala GraphDeviceAffineConfigInstaller.scala GraphDeviceProgramInstaller.scala chipyard-overlay/RaveilFixtureInputProvider.scala chipyard-overlay/RaveilStaticStencilCore.scala'
scala-cli run $scala_sources --server=false --main-class EmitGraphDeviceAxi4LiteTop > /tmp/dynamic-emit.stdout 2> /tmp/dynamic-emit.stderr
find generated_axi4lite -type f -name '*.sv' -print | LC_ALL=C sort | while read -r file; do
  printf '%s ' "${file#generated_axi4lite/}"; sha256sum "$file" | awk '{print $1}'
done > /tmp/dynamic-rtl.manifest
verilator --assert --cc generated_axi4lite/*.sv --exe graph_device_runtime.cpp graph_device_affine_runtime.cpp graph_device_dag_runtime.cpp raveil_graph_device_dynamic_request.cpp graph_device_axi4lite_dynamic_verilator.cpp --build --Mdir obj_graph_device_axi4lite_dynamic --top-module GraphDeviceAxi4LiteTop > /tmp/dynamic-verilator.stdout 2> /tmp/dynamic-verilator.stderr
simulator=obj_graph_device_axi4lite_dynamic/VGraphDeviceAxi4LiteTop
test -x "$simulator"
simulator_sha=$(sha256sum "$simulator" | awk '{print $1}')
for root in "$first" ${second:+"$second"}; do
  cp -n "$simulator" "$root/simulator.bin"; printf '%s\n' "$simulator_sha" > "$root/simulator.sha256"
  cp -n /tmp/dynamic-rtl.manifest "$root/rtl.manifest"
  cp -n /tmp/dynamic-source.manifest "$root/source.manifest"
  cp -n /tmp/dynamic-abi.manifest "$root/abi.manifest"
  { scala-cli version; java -version 2>&1; verilator --version; } > "$root/toolchain.txt"
done
for root in "$first" ${second:+"$second"}; do
  "$simulator" "$root" > "$root/device.log" 2> "$root/device.stderr"
  test ! -s "$root/device.stderr"
done
rejected=/session/rejected-request
mkdir "$rejected"; cp "$first/request.bin" "$first/request-input.bin" "$rejected/"; cp -R "$first/inputs" "$rejected/"
printf '\316' | dd of="$rejected/request.bin" bs=1 count=1 conv=notrunc status=none
rm -f "$rejected/axi-transcript.log"
if "$simulator" "$rejected" > "$rejected/device.log" 2> "$rejected/device.stderr"; then
  echo 'error: malformed dynamic request was accepted' >&2; exit 1
fi
test ! -e "$rejected/axi-transcript.log"
if test "$request_count" = 1; then invocation=once; else invocation=twice; fi
printf 'GraphDevice-AXI4LITE-DYNAMIC-EVIDENCE-V1 status=PASS requests=%s same_simulator=1 invoked_%s=1 rtl_emitted_once=1 simulator_built_once=1 rejected_before_axi=1 simulator_sha256=%s path=artifacts/graph_device_axi4lite_dynamic/%s evidence=rtl-simulation-functional performance=not-measured\n' "$request_count" "$invocation" "$simulator_sha" "$session_name"
