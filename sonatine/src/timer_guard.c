#include "timer_guard.h"

static bool active;
static uint64_t rejected_reentries;

void timer_guard_reset(void) {
  active = false;
  rejected_reentries = 0u;
}

bool timer_guard_enter(uintptr_t frame, uintptr_t pc,
                       uintptr_t *selected_frame, uintptr_t *resume_pc) {
  if (active) {
    ++rejected_reentries;
    *selected_frame = frame;
    *resume_pc = pc;
    return false;
  }
  active = true;
  return true;
}

void timer_guard_exit(void) {
  active = false;
}

uint64_t timer_guard_reentry_count(void) {
  return rejected_reentries;
}
