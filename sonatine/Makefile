CROSS_COMPILE ?= riscv64-unknown-elf-
CC := $(CROSS_COMPILE)gcc
OBJCOPY := $(CROSS_COMPILE)objcopy
QEMU ?= qemu-system-riscv64

BUILD := build
TARGET := $(BUILD)/sonatine.elf
C_SOURCES := $(wildcard src/*.c)
S_SOURCES := $(wildcard src/*.S)
OBJECTS := $(patsubst src/%.c,$(BUILD)/%.o,$(C_SOURCES)) \
           $(patsubst src/%.S,$(BUILD)/%.o,$(S_SOURCES))

CFLAGS := -std=c11 -march=rv64imac_zicsr -mabi=lp64 -mcmodel=medany \
          -ffreestanding -fno-builtin -fno-stack-protector -fno-pic \
          -Wall -Wextra -Werror -Os -ffunction-sections -fdata-sections \
          -Iinclude
ASFLAGS := -march=rv64imac_zicsr -mabi=lp64 -mcmodel=medany -Iinclude
LDFLAGS := -march=rv64imac_zicsr -mabi=lp64 -mcmodel=medany -nostdlib -nostartfiles \
           -Wl,-T,link.ld -Wl,--gc-sections -Wl,--build-id=none

.PHONY: all run smoke debug clean check-toolchain

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
	$(QEMU) -machine virt -m 128M -smp 1 -bios none -nographic -kernel $(TARGET)

smoke: $(TARGET)
	printf 'info\rmem\rps\rcaps\rticks\ripc\ralloc\rreboot\r' | \
	  $(QEMU) -machine virt -m 128M -smp 1 -bios none -nographic -kernel $(TARGET) | \
	  tee $(BUILD)/smoke.log
	grep -q 'raveil>' $(BUILD)/smoke.log
	grep -q 'ipc: received' $(BUILD)/smoke.log

debug: $(TARGET)
	$(QEMU) -machine virt -m 128M -smp 1 -bios none -nographic -kernel $(TARGET) -S -s

check-toolchain:
	@command -v $(CC)
	@command -v $(QEMU)

clean:
	rm -rf $(BUILD)
