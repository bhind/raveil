#ifndef SONATINE_VM_H
#define SONATINE_VM_H
#include <stdbool.h>
#include <stdint.h>
#define SONATINE_USER_BASE 0x40000000UL
enum vm_permission { VM_READ=1u, VM_WRITE=2u, VM_EXECUTE=4u, VM_USER=8u };
bool vm_init(uintptr_t user_page);
void vm_activate(void);
uintptr_t vm_root_address(void);
bool vm_resolve(uintptr_t virtual_address, uintptr_t *physical_address,
                uint32_t *permissions);
#endif
