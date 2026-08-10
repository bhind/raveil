#include "timer_dispatch.h"

#include "timer_guard.h"

uintptr_t timer_dispatch_tick(uintptr_t frame, uintptr_t pc,
                              uintptr_t *resume_pc,
                              const struct timer_dispatch_ops *ops) {
  uintptr_t selected_frame;
  if (!timer_guard_enter(frame, pc, &selected_frame, resume_pc)) {
    return selected_frame;
  }
  ops->on_tick();
  selected_frame = ops->select_context(frame, pc, resume_pc);
  timer_guard_exit();
  return selected_frame;
}
