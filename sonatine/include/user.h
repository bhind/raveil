#ifndef SONATINE_USER_H
#define SONATINE_USER_H
#include <stdbool.h>
#include <stdint.h>
bool user_init_prepare(uintptr_t code_page);
void user_init_enter(void);
uint64_t user_trap_dispatch(uint64_t cause, uint64_t pc, uint64_t argument,
                            uint64_t syscall);
#endif
