CC ?= cc
CFLAGS ?= -std=c11 -O2 -Wall -Wextra -Werror
CPPFLAGS := -Iinclude -I../contracts/include
BUILD := build
.PHONY: all contracts-check smoke clean
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
clean:
	rm -rf $(BUILD)
