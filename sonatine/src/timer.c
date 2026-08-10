#include "timer.h"

#include "console.h"
#include "context.h"
#include "platform.h"

#define MIE_MTIE (1UL << 7u)
#define MSTATUS_MIE (1UL << 3u)
#define MACHINE_TIMER_INTERRUPT 7u
#define INTERRUPT_BIT (1UL << 63u)
#define TICK_INTERVAL (QEMU_TIMEBASE_HZ / 100u)

extern void trap_entry(void);

static volatile uint64_t tick_count;

static volatile uint64_t *mtime(void) {
  return (volatile uint64_t *)QEMU_CLINT_MTIME;
}

static volatile uint64_t *mtimecmp(void) {
  return (volatile uint64_t *)QEMU_CLINT_MTIMECMP;
}

static void schedule_next_tick(void) {
  *mtimecmp() = *mtime() + TICK_INTERVAL;
}

void timer_init(void) {
  tick_count = 0u;
  csr_write_mtvec((uint64_t)(uintptr_t)&trap_entry);
  schedule_next_tick();
  csr_set_mie(MIE_MTIE);
  csr_set_mstatus(MSTATUS_MIE);
}

void timer_on_interrupt(void) {
  ++tick_count;
  schedule_next_tick();
}

uint64_t timer_ticks(void) {
  return tick_count;
}

uintptr_t trap_dispatch(uint64_t cause, uint64_t exception_pc,
                        uintptr_t frame, uintptr_t *resume_pc) {
  if ((cause & INTERRUPT_BIT) != 0u &&
      (cause & ~INTERRUPT_BIT) == MACHINE_TIMER_INTERRUPT) {
    timer_on_interrupt();
    return context_trap_select(frame, exception_pc, resume_pc);
  }
  console_write("\nFATAL: machine trap cause=");
  console_write_hex(cause);
  console_write(" mepc=");
  console_write_hex(exception_pc);
  console_write("\n");
  for (;;) {
    cpu_wait();
  }
}
