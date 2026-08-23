#include <stdint.h>

#define RAVEIL_GRAPH_CONTROL_BASE ((uintptr_t)0x08011000U)

int stencil_repeated_main(void) {
    volatile uint32_t *const control =
        (volatile uint32_t *)RAVEIL_GRAPH_CONTROL_BASE;

    control[0] = 1U;
    while ((control[1] & 1U) == 0U) {
        __asm__ volatile ("" ::: "memory");
    }
    return 0;
}
