#include "shell.h"

#include "console.h"
#include "ipc.h"
#include "memory.h"
#include "platform.h"
#include "task.h"
#include "timer.h"
#include "util.h"

#define SHELL_LINE_SIZE 96u

static void print_help(void) {
  console_write("help       show commands\n");
  console_write("info       show kernel identity\n");
  console_write("mem        show physical page allocator\n");
  console_write("ps         show kernel tasks\n");
  console_write("caps       show capability table\n");
  console_write("ticks      show 100 Hz timer ticks\n");
  console_write("ipc        capability-checked loopback\n");
  console_write("alloc      allocate and release one page\n");
  console_write("reboot     exit QEMU through test finisher\n");
}

static void print_info(void) {
  console_write("Raveil ");
  console_write(RAVEIL_VERSION);
  console_write(" / Sonatine RV64 / QEMU virt / M-mode\n");
  console_write("authority: one hart; paging: off; user isolation: not yet\n");
}

static void print_memory(void) {
  console_write("RAM pages total=");
  console_write_dec(phys_total_pages());
  console_write(" free=");
  console_write_dec(phys_free_pages());
  console_write(" first-free=");
  console_write_hex(phys_first_free_address());
  console_write("\n");
}

static void ipc_loopback(uint16_t task, cap_handle_t endpoint) {
  const struct ipc_message outbound = {
      .sender = task,
      .tag = 0x52u,
      .words = {0x52415645494cUL, timer_ticks(), 0u, 0u},
  };
  struct ipc_message inbound;
  if (ipc_send(task, endpoint, &outbound) != IPC_OK) {
    console_write("ipc: send denied or queue full\n");
    return;
  }
  if (ipc_receive(task, endpoint, &inbound) != IPC_OK) {
    console_write("ipc: receive denied or queue empty\n");
    return;
  }
  console_write("ipc: received tag=");
  console_write_hex(inbound.tag);
  console_write(" sender=");
  console_write_dec(inbound.sender);
  console_write(" word0=");
  console_write_hex(inbound.words[0]);
  console_write("\n");
}

static void alloc_once(void) {
  const size_t before = phys_free_pages();
  void *page = phys_alloc_page();
  if (page == NULL) {
    console_write("alloc: out of physical pages\n");
    return;
  }
  console_write("alloc: page=");
  console_write_hex((uintptr_t)page);
  console_write(" free ");
  console_write_dec(before);
  console_write(" -> ");
  console_write_dec(phys_free_pages());
  if (phys_free_page(page)) {
    console_write(" -> ");
    console_write_dec(phys_free_pages());
    console_write(" (released)\n");
  } else {
    console_write(" release failed\n");
  }
}

void shell_run(uint16_t init_task, cap_handle_t init_endpoint) {
  char line[SHELL_LINE_SIZE];
  console_write("\nRaveil shell v" RAVEIL_VERSION "\n");
  console_write("type 'help' for commands\n\n");
  for (;;) {
    console_write("raveil> ");
    console_readline(line, sizeof(line));
    if (line[0] == '\0') {
      continue;
    }
    if (rv_strcmp(line, "help") == 0) {
      print_help();
    } else if (rv_strcmp(line, "info") == 0) {
      print_info();
    } else if (rv_strcmp(line, "mem") == 0) {
      print_memory();
    } else if (rv_strcmp(line, "ps") == 0) {
      task_dump();
    } else if (rv_strcmp(line, "caps") == 0) {
      cap_dump();
    } else if (rv_strcmp(line, "ticks") == 0) {
      console_write_dec(timer_ticks());
      console_write("\n");
    } else if (rv_strcmp(line, "ipc") == 0) {
      ipc_loopback(init_task, init_endpoint);
    } else if (rv_strcmp(line, "alloc") == 0) {
      alloc_once();
    } else if (rv_strcmp(line, "reboot") == 0) {
      console_write("leaving QEMU\n");
      *(volatile uint32_t *)QEMU_TEST_FINISHER = 0x5555u;
    } else {
      console_write("unknown command: ");
      console_write(line);
      console_write("\n");
    }
  }
}
