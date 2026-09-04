CC ?= cc
CXX ?= c++
CFLAGS ?= -std=c11 -O2 -Wall -Wextra -Werror
CXXFLAGS ?= -std=c++17 -O2 -Wall -Wextra -Werror
CPPFLAGS := -Iinclude -I../contracts/include
BUILD := build
.PHONY: all contracts-check smoke graph-device-uio clean
all: $(BUILD)/raveil-linuxd $(BUILD)/raveilctl
$(BUILD):
	mkdir -p $@
$(BUILD)/raveil-linuxd: src/raveil-linuxd.c src/raveil_driver_core.c | $(BUILD)
	$(CC) $(CPPFLAGS) $(CFLAGS) $^ -o $@
$(BUILD)/raveilctl: src/raveilctl.c | $(BUILD)
	$(CC) $(CPPFLAGS) $(CFLAGS) $< -o $@
contracts-check: | $(BUILD)
	$(CC) $(CPPFLAGS) $(CFLAGS) -c ../contracts/src/job_contract.c \
	  -o $(BUILD)/job_contract.o
	$(CC) $(CPPFLAGS) $(CFLAGS) -c ../contracts/src/object_manifest.c \
	  -o $(BUILD)/object_manifest.o
smoke: all
	test -n "$$XDG_RUNTIME_DIR"
	$(BUILD)/raveil-linuxd & daemon=$$!; \
	  trap 'kill $$daemon 2>/dev/null || true' EXIT; \
	  for attempt in 1 2 3 4 5; do \
	    test -S "$$XDG_RUNTIME_DIR/raveil-driver.sock" && break; sleep 1; \
	  done; \
	  test "$$(stat -c %a "$$XDG_RUNTIME_DIR/raveil-driver.sock")" = 600; \
	  $(BUILD)/raveilctl; wait $$daemon; \
	  test ! -e "$$XDG_RUNTIME_DIR/raveil-driver.sock"
graph-device-uio: $(BUILD)/raveil-graph-device-uio-run
$(BUILD)/raveil-graph-device-uio-run: src/raveil-graph-device-uio-run.cpp src/raveil_graph_device_uio.cpp src/raveil_graph_device_request.cpp ../hardware/chisel/graph_device_runtime.cpp ../hardware/chisel/graph_device_affine_runtime.cpp ../hardware/chisel/graph_device_dag_runtime.cpp | $(BUILD)
	test -n "$(GENERATED_DIR)"
	test -f "$(GENERATED_DIR)/graph_device_abi_generated.h"
	test -f "$(GENERATED_DIR)/graph_device_affine_generated.h"
	test -f "$(GENERATED_DIR)/graph_device_dag_generated.h"
	PYTHONPATH=.. python3 -c 'from pathlib import Path; import sys; from raveil.graph_device_dag import _generated_header, compile_artifact; sys.exit(0 if Path(sys.argv[1]).read_bytes() == _generated_header(compile_artifact()) else 1)' "$(GENERATED_DIR)/graph_device_dag_generated.h"
	$(CXX) -Iinclude -I../hardware/chisel -I"$(GENERATED_DIR)" $(CXXFLAGS) $^ -o $@

graph-device-dynamic-uio: $(BUILD)/raveil-graph-device-dynamic-uio-run
$(BUILD)/raveil-graph-device-dynamic-uio-run: src/raveil-graph-device-dynamic-uio-run.cpp src/raveil_graph_device_uio.cpp src/raveil_graph_device_dynamic_request.cpp ../hardware/chisel/graph_device_runtime.cpp ../hardware/chisel/graph_device_affine_runtime.cpp ../hardware/chisel/graph_device_dag_runtime.cpp | $(BUILD)
	test -n "$(GENERATED_DIR)"
	test -f "$(GENERATED_DIR)/graph_device_abi_generated.h"
	test -f "$(GENERATED_DIR)/graph_device_affine_generated.h"
	test -f "$(GENERATED_DIR)/graph_device_dag_generated.h"
	$(CXX) -Iinclude -I../hardware/chisel -I"$(GENERATED_DIR)" $(CXXFLAGS) $^ -o $@
clean:
	rm -rf $(BUILD)
