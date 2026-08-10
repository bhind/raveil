#include "timer.h"

#include "console.h"
#include "context.h"
#include "platform.h"
#include "timer_dispatch.h"
#include "timer_guard.h"
#include "trap.h"
#include "user.h"

#define MIE_MTIE (1UL << 7u)
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
  timer_guard_reset();
  csr_write_mtvec((uint64_t)(uintptr_t)&trap_entry);
  schedule_next_tick();
  csr_set_mie(MIE_MTIE);
}

void timer_on_interrupt(void) {
  ++tick_count;
  schedule_next_tick();
}

uint64_t timer_ticks(void) {
  return tick_count;
}

uintptr_t trap_dispatch(uint64_t cause, uintptr_t frame) {
  struct trap_frame *trap=(struct trap_frame *)frame;
  if ((cause & INTERRUPT_BIT) != 0u &&
      (cause & ~INTERRUPT_BIT) == MACHINE_TIMER_INTERRUPT) {
    const struct timer_dispatch_ops ops = {
        .on_tick = timer_on_interrupt,
        .select_context = context_trap_select,
    };
    uintptr_t resume_pc=(uintptr_t)trap->mepc;
    const uintptr_t selected=
        timer_dispatch_tick(frame,resume_pc,&resume_pc,&ops);
    trap->mepc=resume_pc;
    return selected;
  }
  if ((trap->mstatus & TRAP_MSTATUS_MPP_MASK) == 0u) {
    if (cause == 8u) return user_syscall_dispatch(trap);
    return user_fault_dispatch(cause, trap);
  }
  machine_fault_dispatch(cause, trap);
  /* Unreachable: the fault dispatcher stops or terminates the current task. */
#if 0
  console_write("\nFATAL: machine trap cause=");
  console_write_hex(cause);
  console_write(" mepc=");
  console_write_hex(exception_pc);
  console_write("\n");
  for (;;) {
    cpu_wait();
  }
#endif
}
