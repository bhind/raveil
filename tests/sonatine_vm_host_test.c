#include <assert.h>
#include <stdint.h>
#include "platform.h"
#include "vm.h"
int main(void) {
  uintptr_t user=QEMU_RAM_BASE+0x200000u,pa=0u; uint32_t rights=0u;
  assert(vm_init(user)); assert((vm_root_address()&0xfffu)==0u);
  assert(vm_resolve(QEMU_RAM_BASE+0x1234u,&pa,&rights));
  assert(pa==QEMU_RAM_BASE+0x1234u); assert((rights&VM_USER)==0u);
  assert((rights&(VM_READ|VM_WRITE|VM_EXECUTE))==(VM_READ|VM_WRITE|VM_EXECUTE));
  assert(vm_resolve(SONATINE_USER_BASE,&pa,&rights)); assert(pa==user);
  assert((rights&(VM_READ|VM_WRITE|VM_USER))==(VM_READ|VM_WRITE|VM_USER));
  assert((rights&VM_EXECUTE)==0u); assert(!vm_resolve(SONATINE_USER_BASE+4096u,0,0));
  assert(!vm_init(user+1u)); return 0;
}
