#ifndef SONATINE_CONTEXT_H
#define SONATINE_CONTEXT_H
#include <stdbool.h>
#include <stdint.h>
#include "capability.h"
#include "trap.h"
bool context_switch_smoke(uint16_t init_task, uint16_t idle_task);
bool context_preemption_configure(uint16_t init_task, uint16_t idle_task,
                                  uintptr_t user_entry, uintptr_t user_stack,
                                  cap_handle_t console_cap,
                                  cap_handle_t clock_cap,
                                  cap_handle_t endpoint_cap,
                                  cap_handle_t wrong_owner_cap,
                                  cap_handle_t send_only_cap);
void context_start_user(void) __attribute__((noreturn));
uint64_t context_preemption_count(void);
uint16_t context_user_task(void);
uintptr_t context_trap_select(uintptr_t frame, uintptr_t pc,
                              uintptr_t *resume_pc);
#endif
