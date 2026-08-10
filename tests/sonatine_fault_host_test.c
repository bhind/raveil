#include <assert.h>
#include <stdint.h>

#include "timer_guard.h"
#include "timer_dispatch.h"
#include "user.h"

void console_putc(char character) { (void)character; }
void console_write(const char *text) { (void)text; }
void console_write_dec(uint64_t value) { (void)value; }
void console_write_hex(uint64_t value) { (void)value; }

static uint64_t ticks;
static uint64_t selections;

static void fake_tick(void) { ++ticks; }

static uintptr_t fake_select(uintptr_t frame, uintptr_t pc,
                             uintptr_t *resume_pc) {
  ++selections;
  *resume_pc = pc + 4u;
  return frame + 8u;
}

int main(void) {
  const uint64_t pc = 0x1000u;
  assert(user_trap_dispatch(8u, pc, 'x', 1u) == pc + 4u);
  assert(user_trap_dispatch(8u, pc, 0u, 2u) == 1u);
  assert(user_trap_dispatch(8u, pc, 0u, 99u) == 1u);
  assert(user_trap_dispatch(2u, pc, 0u, 0u) == 1u);

  timer_guard_reset();
  uintptr_t selected = 0u;
  uintptr_t resume = 0u;
  assert(timer_guard_enter(0x100u, 0x200u, &selected, &resume));
  assert(!timer_guard_enter(0x300u, 0x400u, &selected, &resume));
  assert(selected == 0x300u);
  assert(resume == 0x400u);
  assert(timer_guard_reentry_count() == 1u);
  timer_guard_exit();
  assert(timer_guard_enter(0x500u, 0x600u, &selected, &resume));
  timer_guard_exit();
  assert(timer_guard_reentry_count() == 1u);

  const struct timer_dispatch_ops ops = {
      .on_tick = fake_tick,
      .select_context = fake_select,
  };
  timer_guard_reset();
  ticks = 0u;
  selections = 0u;
  assert(timer_guard_enter(0u, 0u, &selected, &resume));
  assert(timer_dispatch_tick(0x700u, 0x800u, &resume, &ops) == 0x700u);
  assert(resume == 0x800u);
  assert(ticks == 0u);
  assert(selections == 0u);
  assert(timer_guard_reentry_count() == 1u);
  timer_guard_exit();
  assert(timer_dispatch_tick(0x900u, 0xa00u, &resume, &ops) == 0x908u);
  assert(resume == 0xa04u);
  assert(ticks == 1u);
  assert(selections == 1u);
  return 0;
}
