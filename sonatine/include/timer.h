#ifndef SONATINE_TIMER_H
#define SONATINE_TIMER_H

#include <stdint.h>

void timer_init(void);
void timer_on_interrupt(void);
uint64_t timer_ticks(void);
uintptr_t trap_dispatch(uint64_t cause, uintptr_t frame);

#endif
