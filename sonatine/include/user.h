#ifndef SONATINE_USER_H
#define SONATINE_USER_H
#include <stdbool.h>
#include <stdint.h>
#include "trap.h"
bool user_init_prepare(uintptr_t code_page);
void user_init_enter(void);
void user_fault_probe_enter(void);
uint64_t user_trap_dispatch(uint64_t cause, uint64_t pc, uint64_t argument,
                            uint64_t syscall);
uintptr_t user_syscall_dispatch(struct trap_frame *frame);
uintptr_t user_fault_dispatch(uint64_t cause, struct trap_frame *frame);
void machine_fault_dispatch(uint64_t cause, const struct trap_frame *frame)
    __attribute__((noreturn));
uintptr_t user_shell_offset(void);
#endif
