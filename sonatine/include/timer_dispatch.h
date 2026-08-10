#ifndef SONATINE_TIMER_DISPATCH_H
#define SONATINE_TIMER_DISPATCH_H

#include <stdint.h>

struct timer_dispatch_ops {
  void (*on_tick)(void);
  uintptr_t (*select_context)(uintptr_t frame, uintptr_t pc,
                              uintptr_t *resume_pc);
};

uintptr_t timer_dispatch_tick(uintptr_t frame, uintptr_t pc,
                              uintptr_t *resume_pc,
                              const struct timer_dispatch_ops *ops);

#endif
