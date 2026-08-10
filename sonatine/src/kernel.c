#include "capability.h"
#include "console.h"
#include "context.h"
#include "ipc.h"
#include "memory.h"
#include "platform.h"
#include "shell.h"
#include "task.h"
#include "timer.h"
#include "vm.h"
#include "user.h"

static void boot_ok(const char *subsystem) {
  console_write("  [ok] ");
  console_write(subsystem);
  console_write("\n");
}

static void boot_fail(const char *subsystem) {
  console_write("  [fail] ");
  console_write(subsystem);
  console_write("\nSonatine halted\n");
  for (;;) {
    cpu_wait();
  }
}

void kmain(void) {
  console_init();
  console_write("\nRaveil boot v" RAVEIL_VERSION "\n");
  console_write("Sonatine kernel (RV64 QEMU virt)\n");
  console_write("platform contract: " SONATINE_PLATFORM_NAME "\n");
  boot_ok("console / ns16550a polled UART");

  phys_init();
  if (phys_free_pages() == 0u) {
    boot_fail("physical memory");
  }
  boot_ok("physical memory / 4 KiB bitmap allocator");

  void *user_code = phys_alloc_page();
  void *user_stack = phys_alloc_page();
  if (user_code == NULL || user_stack == NULL ||
      !vm_init((uintptr_t)user_code, (uintptr_t)user_stack) ||
      !user_init_prepare((uintptr_t)user_code)) {
    boot_fail("Sv39 address space");
  }
  vm_activate();
  boot_ok("Sv39 / supervisor kernel map + user window");

  console_write("starting U-mode init: ");
  user_init_enter();
  boot_ok("U-mode init / ecall boundary");

  cap_init();
  boot_ok("capability / generation-checked fixed table");

  task_init();
  const uint16_t init_task = task_create("init", TASK_READY);
  const uint16_t idle_task = task_create("idle", TASK_READY);
  if (init_task == 0u || idle_task == 0u || !task_set_current(init_task)) {
    boot_fail("task");
  }
  boot_ok("task / init + idle kernel tasks");
  if (!context_switch_smoke(init_task, idle_task)) {
    boot_fail("context switch");
  }
  boot_ok("context switch / independent idle stack");

  ipc_init();
  const uint32_t endpoint = ipc_endpoint_create(init_task);
  const cap_handle_t endpoint_cap = cap_create(
      init_task, CAP_OBJECT_ENDPOINT, endpoint,
      CAP_RIGHT_SEND | CAP_RIGHT_RECEIVE | CAP_RIGHT_CONTROL);
  const cap_handle_t task_cap = cap_create(
      init_task, CAP_OBJECT_TASK, init_task, CAP_RIGHT_READ | CAP_RIGHT_CONTROL);
  if (endpoint == 0u || endpoint_cap == 0u || task_cap == 0u) {
    boot_fail("IPC");
  }
  boot_ok("IPC / bounded mailbox protected by capabilities");

  timer_init();
  boot_ok("timer / CLINT machine timer at 100 Hz");
  context_preemption_enable();
  while (context_preemption_count() < 2u) {
    cpu_relax();
  }
  console_write("timer preemption: init -> idle -> init count=");
  console_write_dec(context_preemption_count());
  console_write("\n");
  boot_ok("preemption / CLINT-driven context switch");

  console_write("starting init task id=");
  console_write_dec(init_task);
  console_write("\n");
  shell_run(init_task, endpoint_cap);
  boot_fail("init returned");
}
