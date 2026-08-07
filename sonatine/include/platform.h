#ifndef SONATINE_PLATFORM_H
#define SONATINE_PLATFORM_H

#include <stdint.h>

#define RAVEIL_VERSION "0.0000000000001"

#define QEMU_RAM_BASE 0x80000000UL
#define QEMU_RAM_SIZE (128UL * 1024UL * 1024UL)
#define QEMU_UART0_BASE 0x10000000UL
#define QEMU_TEST_FINISHER 0x00100000UL
#define QEMU_CLINT_MTIMECMP 0x02004000UL
#define QEMU_CLINT_MTIME 0x0200BFF8UL
#define QEMU_TIMEBASE_HZ 10000000UL

static inline void csr_write_mtvec(uint64_t value) {
  __asm__ volatile("csrw mtvec, %0" : : "r"(value));
}

static inline void csr_set_mie(uint64_t bits) {
  __asm__ volatile("csrs mie, %0" : : "r"(bits));
}

static inline void csr_set_mstatus(uint64_t bits) {
  __asm__ volatile("csrs mstatus, %0" : : "r"(bits));
}

static inline void cpu_relax(void) {
  __asm__ volatile("nop");
}

static inline void cpu_wait(void) {
  __asm__ volatile("wfi");
}

#endif
