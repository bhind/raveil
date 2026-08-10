CROSS_COMPILE ?= riscv64-unknown-elf-
CC := $(CROSS_COMPILE)gcc
OBJCOPY := $(CROSS_COMPILE)objcopy
READELF := $(CROSS_COMPILE)readelf
GDB := $(CROSS_COMPILE)gdb
QEMU ?= qemu-system-riscv64
DEBUG ?= 0

# T-0010 deliberately constrains the supported machine instead of accepting an
# arbitrary QEMU virt DTB. Keep these values synchronized with platform.h and
# link.ld; tests enforce the contract until a real DTB parser replaces it.
QEMU_MACHINE := virt
QEMU_CPU := rv64
QEMU_MEMORY := 128M
QEMU_HARTS := 1
QEMU_PLATFORM_ARGS := -machine $(QEMU_MACHINE) -cpu $(QEMU_CPU) \
                      -m $(QEMU_MEMORY) -smp $(QEMU_HARTS) -bios none

BUILD_ROOT := build
ifeq ($(DEBUG),1)
BUILD := $(BUILD_ROOT)/debug
COPT := -Og -g3
ASDEBUG := -g3
else
BUILD := $(BUILD_ROOT)
COPT := -Os
ASDEBUG :=
endif

TARGET := $(BUILD)/sonatine.elf
C_SOURCES := $(wildcard src/*.c)
CONTRACT_SOURCES := ../contracts/src/job_contract.c ../contracts/src/object_manifest.c
S_SOURCES := $(wildcard src/*.S)
OBJECTS := $(patsubst src/%.c,$(BUILD)/%.o,$(C_SOURCES)) \
           $(patsubst ../contracts/src/%.c,$(BUILD)/contract_%.o,$(CONTRACT_SOURCES)) \
           $(patsubst src/%.S,$(BUILD)/%.o,$(S_SOURCES))

CFLAGS := -std=c11 -march=rv64imac_zicsr -mabi=lp64 -mcmodel=medany \
          -ffreestanding -fno-builtin -fno-stack-protector -fno-pic \
          -Wall -Wextra -Werror $(COPT) -ffunction-sections -fdata-sections \
          -Iinclude -I../contracts/include
ASFLAGS := -march=rv64imac_zicsr -mabi=lp64 -mcmodel=medany $(ASDEBUG) -Iinclude
LDFLAGS := -march=rv64imac_zicsr -mabi=lp64 -mcmodel=medany -nostdlib -nostartfiles \
           -Wl,-T,link.ld -Wl,--gc-sections -Wl,--build-id=none

.PHONY: all run smoke debug debug-server gdb gdb-client check-debug clean check-toolchain

all: $(TARGET)

$(TARGET): $(OBJECTS) link.ld
	$(CC) $(LDFLAGS) $(OBJECTS) -o $@

$(BUILD)/%.o: src/%.c | $(BUILD)
	$(CC) $(CFLAGS) -c $< -o $@

$(BUILD)/contract_%.o: ../contracts/src/%.c | $(BUILD)
	$(CC) $(CFLAGS) -c $< -o $@

$(BUILD)/%.o: src/%.S | $(BUILD)
	$(CC) $(ASFLAGS) -c $< -o $@

$(BUILD):
	mkdir -p $@

run: $(TARGET)
	$(QEMU) $(QEMU_PLATFORM_ARGS) -nographic -kernel $(TARGET)

smoke: $(TARGET)
	printf 'i\rf\rs\rf\rc\rt\rx\r' | \
	  $(QEMU) $(QEMU_PLATFORM_ARGS) -nographic -kernel $(TARGET) | \
	  tee $(BUILD)/smoke.log
	grep -q 'starting U-mode init: U-mode' $(BUILD)/smoke.log
	grep -q 'U-mode fault contained cause=0x2' $(BUILD)/smoke.log
	grep -q '\[ok\] U-mode fault / contained return to kernel' $(BUILD)/smoke.log
	grep -q 'context switch: init -> idle -> init' $(BUILD)/smoke.log
	grep -q '\[ok\] persistent U-mode shell / current-task syscall identity' $(BUILD)/smoke.log
	grep -q 'u-cmd info=ok' $(BUILD)/smoke.log
	grep -q 'clint-preempt from=1 to=2' $(BUILD)/smoke.log
	grep -q 'clint-preempt from=2 to=1' $(BUILD)/smoke.log
	grep -q 'u-context register-frame=ok task=1' $(BUILD)/smoke.log
	grep -q 'u-shell resumed task=1' $(BUILD)/smoke.log
	grep -q '\[ok\] VFS / immutable initramfs + bounded RamFS' $(BUILD)/smoke.log
	grep -q '\[ok\] Daphnis contract / object table + bounded rings + replay guard' $(BUILD)/smoke.log
	test "$$(grep -c '^RAVEIL-COMPLETION-V1 ' $(BUILD)/smoke.log)" -eq 1
	test "$$(grep -c 'u-vfs read=hello write-readback=OK' $(BUILD)/smoke.log)" -eq 2
	grep -q 'kernel-file initramfs=DENIED' $(BUILD)/smoke.log
	grep -q 'kernel-file rights=DENIED' $(BUILD)/smoke.log
	grep -q 'kernel-cap forged=DENIED' $(BUILD)/smoke.log
	grep -q 'kernel-cap wrong-owner=DENIED' $(BUILD)/smoke.log
	grep -q 'kernel-cap escalation=DENIED' $(BUILD)/smoke.log
	grep -q 'u-ipc send=OK receive=OK' $(BUILD)/smoke.log
	grep -q 'u-cmd ticks=ok' $(BUILD)/smoke.log
	grep -q 'u-shell exit task=1' $(BUILD)/smoke.log
	rm -f $(BUILD)/completion-telemetry.jsonl
	cd .. && python3 -m raveil experience ingest-completions \
	  --input sonatine/$(BUILD)/smoke.log \
	  --store sonatine/$(BUILD)/completion-telemetry.jsonl --run-id qemu-smoke
	cd .. && python3 -m raveil experience ingest-completions \
	  --input sonatine/$(BUILD)/smoke.log \
	  --store sonatine/$(BUILD)/completion-telemetry.jsonl --run-id qemu-smoke | \
	  grep -q 'appended=0'

debug:
	$(MAKE) DEBUG=1 debug-server

debug-server: $(TARGET)
	$(QEMU) $(QEMU_PLATFORM_ARGS) -nographic -kernel $(TARGET) -S -s

gdb:
	$(MAKE) DEBUG=1 gdb-client

gdb-client: $(TARGET)
	$(GDB) $(TARGET) -ex 'target remote 127.0.0.1:1234' -ex 'break kmain'

check-debug:
	$(MAKE) DEBUG=1 all
	$(READELF) -S $(BUILD_ROOT)/debug/sonatine.elf | grep -q '\.debug_info'
	$(READELF) -S $(BUILD_ROOT)/debug/sonatine.elf | grep -q '\.debug_line'

check-toolchain:
	@command -v $(CC)
	@command -v $(READELF)
	@command -v $(GDB)
	@command -v $(QEMU)

clean:
	rm -rf $(BUILD_ROOT)
