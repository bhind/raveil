#ifndef SONATINE_CONTEXT_H
#define SONATINE_CONTEXT_H
#include <stdbool.h>
#include <stdint.h>
bool context_switch_smoke(uint16_t init_task, uint16_t idle_task);
void context_preemption_enable(void);
uint64_t context_preemption_count(void);
uintptr_t context_trap_select(uintptr_t frame, uintptr_t pc,
                              uintptr_t *resume_pc);
#endif
