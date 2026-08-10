#ifndef SONATINE_TIMER_GUARD_H
#define SONATINE_TIMER_GUARD_H

#include <stdbool.h>
#include <stdint.h>

void timer_guard_reset(void);
bool timer_guard_enter(uintptr_t frame, uintptr_t pc,
                       uintptr_t *selected_frame, uintptr_t *resume_pc);
void timer_guard_exit(void);
uint64_t timer_guard_reentry_count(void);

#endif
