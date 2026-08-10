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
S_SOURCES := $(wildcard src/*.S)
OBJECTS := $(patsubst src/%.c,$(BUILD)/%.o,$(C_SOURCES)) \
           $(patsubst src/%.S,$(BUILD)/%.o,$(S_SOURCES))

CFLAGS := -std=c11 -march=rv64imac_zicsr -mabi=lp64 -mcmodel=medany \
          -ffreestanding -fno-builtin -fno-stack-protector -fno-pic \
          -Wall -Wextra -Werror $(COPT) -ffunction-sections -fdata-sections \
          -Iinclude
ASFLAGS := -march=rv64imac_zicsr -mabi=lp64 -mcmodel=medany $(ASDEBUG) -Iinclude
LDFLAGS := -march=rv64imac_zicsr -mabi=lp64 -mcmodel=medany -nostdlib -nostartfiles \
           -Wl,-T,link.ld -Wl,--gc-sections -Wl,--build-id=none

.PHONY: all run smoke debug debug-server gdb gdb-client check-debug clean check-toolchain

all: $(TARGET)

$(TARGET): $(OBJECTS) link.ld
	$(CC) $(LDFLAGS) $(OBJECTS) -o $@

$(BUILD)/%.o: src/%.c | $(BUILD)
	$(CC) $(CFLAGS) -c $< -o $@

$(BUILD)/%.o: src/%.S | $(BUILD)
	$(CC) $(ASFLAGS) -c $< -o $@

$(BUILD):
	mkdir -p $@

run: $(TARGET)
	$(QEMU) $(QEMU_PLATFORM_ARGS) -nographic -kernel $(TARGET)

smoke: $(TARGET)
	printf 'info\rmem\rps\rcaps\rticks\ripc\ralloc\rreboot\r' | \
	  $(QEMU) $(QEMU_PLATFORM_ARGS) -nographic -kernel $(TARGET) | \
	  tee $(BUILD)/smoke.log
	grep -q 'raveil>' $(BUILD)/smoke.log
	grep -q 'starting U-mode init: U-mode' $(BUILD)/smoke.log
	grep -q 'context switch: init -> idle -> init' $(BUILD)/smoke.log
	grep -q 'ipc: received' $(BUILD)/smoke.log

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
