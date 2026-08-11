#ifndef SONATINE_PLATFORM_H
#define SONATINE_PLATFORM_H

#include <stdint.h>

#define RAVEIL_VERSION "0.0000000000003"

#define SONATINE_PLATFORM_NAME "qemu-virt-rv64-v1"
#define SONATINE_HART_COUNT 1u

#define QEMU_RAM_BASE 0x80000000UL
#define QEMU_RAM_SIZE (128UL * 1024UL * 1024UL)
#define QEMU_UART0_BASE 0x10000000UL
#define QEMU_TEST_FINISHER 0x00100000UL
#define QEMU_CLINT_MTIMECMP 0x02004000UL
#define QEMU_CLINT_MTIME 0x0200BFF8UL
#define QEMU_TIMEBASE_HZ 10000000UL
#define QEMU_GRAPH_REQUEST_BASE 0x87ff0000UL

_Static_assert(QEMU_RAM_BASE == 0x80000000UL, "linker RAM origin contract");
_Static_assert(QEMU_RAM_SIZE == 128UL * 1024UL * 1024UL,
               "QEMU_MEMORY contract");
_Static_assert(SONATINE_HART_COUNT == 1u, "single-hart kernel contract");
_Static_assert((QEMU_RAM_BASE & 0xfffUL) == 0u, "RAM must be page aligned");

static inline void csr_write_mtvec(uint64_t value) {
  __asm__ volatile("csrw mtvec, %0" : : "r"(value));
}

static inline void csr_set_mie(uint64_t bits) {
  __asm__ volatile("csrs mie, %0" : : "r"(bits));
}

static inline void csr_set_mstatus(uint64_t bits) {
  __asm__ volatile("csrs mstatus, %0" : : "r"(bits));
}

static inline void pmp_allow_user_ram(void) {
  /* 128 MiB naturally aligned NAPOT region at 0x80000000, R/W/X. Sv39 PTEs
     remain the finer-grained authority and do not expose MMIO to U-mode. */
  const uint64_t address = (QEMU_RAM_BASE >> 2) | (QEMU_RAM_SIZE / 2u - 1u);
  const uint64_t config = 0x1fu;
  __asm__ volatile("csrw pmpaddr0, %0\ncsrw pmpcfg0, %1" : : "r"(address), "r"(config));
}

static inline void cpu_relax(void) {
  __asm__ volatile("nop");
}

static inline void cpu_wait(void) {
  __asm__ volatile("wfi");
}

#endif
