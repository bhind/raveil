#include "user.h"
#include <stddef.h>
#include "console.h"
#include "memory.h"
#include "platform.h"
#include "vm.h"
extern const unsigned char user_payload_start[], user_payload_end[];
extern void user_trap_entry(void);
extern void user_enter(uintptr_t entry, uintptr_t stack);
static bool returned;
bool user_init_prepare(uintptr_t code_page) {
  size_t size=(size_t)(user_payload_end-user_payload_start);
  if(size>SONATINE_PAGE_SIZE) return false;
  unsigned char *out=(unsigned char *)code_page;
  for(size_t i=0;i<size;++i) out[i]=user_payload_start[i];
  returned=false; return true;
}
void user_init_enter(void) {
  pmp_allow_user_ram();
  csr_write_mtvec((uint64_t)(uintptr_t)&user_trap_entry);
  user_enter(SONATINE_USER_BASE,SONATINE_USER_BASE+2u*SONATINE_PAGE_SIZE);
  returned=true;
}
uint64_t user_trap_dispatch(uint64_t cause,uint64_t pc,uint64_t argument,uint64_t syscall) {
  if(cause!=8u) {
    console_write("\nU-mode trap cause="); console_write_hex(cause);
    console_write(" mepc="); console_write_hex(pc); console_write("\n");
    return 0u;
  }
  if(syscall==1u) { console_putc((char)argument); return pc+4u; }
  if(syscall==2u) return 1u;
  return 0u;
}
