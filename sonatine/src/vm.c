#include "vm.h"
#include <stddef.h>
#include "memory.h"
#include "platform.h"
#define PTE_COUNT 512u
#define PTE_V (1ULL<<0)
#define PTE_R (1ULL<<1)
#define PTE_W (1ULL<<2)
#define PTE_X (1ULL<<3)
#define PTE_U (1ULL<<4)
#define PTE_G (1ULL<<5)
#define PTE_A (1ULL<<6)
#define PTE_D (1ULL<<7)
#define SATP_MODE_SV39 (8ULL<<60)
static uint64_t root[PTE_COUNT] __attribute__((aligned(SONATINE_PAGE_SIZE)));
static uint64_t kernel_l1[PTE_COUNT] __attribute__((aligned(SONATINE_PAGE_SIZE)));
static uint64_t user_l1[PTE_COUNT] __attribute__((aligned(SONATINE_PAGE_SIZE)));
static uint64_t user_l0[PTE_COUNT] __attribute__((aligned(SONATINE_PAGE_SIZE)));
static uint64_t table_pte(const uint64_t *table) { return (((uintptr_t)table>>12)<<10)|PTE_V; }
static uint64_t leaf_pte(uintptr_t pa,uint64_t flags) { return ((pa>>12)<<10)|flags|PTE_V|PTE_A|PTE_D; }
static void clear(uint64_t *table) { for(size_t i=0;i<PTE_COUNT;++i)table[i]=0u; }
bool vm_init(uintptr_t user_page) {
  if ((user_page&(SONATINE_PAGE_SIZE-1u))!=0u || user_page<QEMU_RAM_BASE ||
      user_page>=QEMU_RAM_BASE+QEMU_RAM_SIZE) return false;
  clear(root); clear(kernel_l1); clear(user_l1); clear(user_l0);
  root[(QEMU_RAM_BASE>>30)&0x1ffu]=table_pte(kernel_l1);
  for(size_t i=0;i<QEMU_RAM_SIZE/(2u*1024u*1024u);++i) {
    uintptr_t pa=QEMU_RAM_BASE+i*2u*1024u*1024u;
    kernel_l1[i]=leaf_pte(pa,PTE_R|PTE_W|PTE_X|PTE_G);
  }
  size_t v2=(SONATINE_USER_BASE>>30)&0x1ffu;
  size_t v1=(SONATINE_USER_BASE>>21)&0x1ffu;
  size_t v0=(SONATINE_USER_BASE>>12)&0x1ffu;
  root[v2]=table_pte(user_l1); user_l1[v1]=table_pte(user_l0);
  user_l0[v0]=leaf_pte(user_page,PTE_R|PTE_W|PTE_U);
  return true;
}
void vm_activate(void) {
#ifdef __riscv
  uint64_t satp=SATP_MODE_SV39|(vm_root_address()>>12);
  __asm__ volatile("csrw satp, %0\nsfence.vma"::"r"(satp):"memory");
#endif
}
uintptr_t vm_root_address(void) { return (uintptr_t)root; }
bool vm_resolve(uintptr_t va,uintptr_t *pa,uint32_t *permissions) {
  size_t index[3]={(va>>12)&0x1ffu,(va>>21)&0x1ffu,(va>>30)&0x1ffu};
  const uint64_t *table=root;
  for(int level=2;level>=0;--level) {
    uint64_t pte=table[index[level]];
    if(!(pte&PTE_V)||((pte&PTE_W)&&!(pte&PTE_R))) return false;
    if(pte&(PTE_R|PTE_X)) {
      uintptr_t size=1ULL<<(12+9*level);
      uintptr_t base=((pte>>10)<<12)&~(size-1u);
      if(pa)*pa=base|(va&(size-1u));
      if(permissions)*permissions=((pte&PTE_R)?VM_READ:0u)|((pte&PTE_W)?VM_WRITE:0u)|
        ((pte&PTE_X)?VM_EXECUTE:0u)|((pte&PTE_U)?VM_USER:0u);
      return true;
    }
    table=(const uint64_t *)((pte>>10)<<12);
  }
  return false;
}
