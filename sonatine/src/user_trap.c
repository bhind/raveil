#include "user.h"

#include "console.h"

#define USER_ECALL_CAUSE 8u
#define USER_SYSCALL_WRITE 1u
#define USER_SYSCALL_EXIT 2u
#define USER_TRAP_RETURN_TO_KERNEL 1u

uint64_t user_trap_dispatch(uint64_t cause, uint64_t pc, uint64_t argument,
                            uint64_t syscall) {
  if (cause != USER_ECALL_CAUSE) {
    console_write("\nU-mode fault contained cause=");
    console_write_hex(cause);
    console_write(" mepc=");
    console_write_hex(pc);
    console_write("\n");
    return USER_TRAP_RETURN_TO_KERNEL;
  }
  if (syscall == USER_SYSCALL_WRITE) {
    console_putc((char)argument);
    return pc + 4u;
  }
  if (syscall == USER_SYSCALL_EXIT) {
    return USER_TRAP_RETURN_TO_KERNEL;
  }
  console_write("\nU-mode syscall rejected number=");
  console_write_dec(syscall);
  console_write("\n");
  return USER_TRAP_RETURN_TO_KERNEL;
}
