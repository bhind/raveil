#include <stdint.h>

extern uint32_t input_words[324];
extern uint32_t output_words[256];

#ifndef RAVEIL_REPEAT_ACCOUNT
#error "RAVEIL_REPEAT_ACCOUNT must be defined"
#endif

#if RAVEIL_REPEAT_ACCOUNT < 1 || RAVEIL_REPEAT_ACCOUNT > 256
#error "RAVEIL_REPEAT_ACCOUNT must be in [1,256]"
#endif

volatile uint64_t validation_sink;

static int stencil_once(void) {
    uint32_t output_index = 0U;
    for (uint32_t y = 1U; y <= 16U; ++y) {
        for (uint32_t x = 1U; x <= 16U; ++x) {
            const uint32_t center = 18U * y + x;
            output_words[output_index++] =
                input_words[center]
                + input_words[center - 18U]
                + input_words[center + 18U]
                + input_words[center - 1U]
                + input_words[center + 1U];
        }
    }
    if (output_index != 256U) {
        return 1;
    }

    uint64_t checksum = 0U;
    volatile uint32_t *validation = (volatile uint32_t *)output_words;
    for (uint32_t index = 0; index < 256U; ++index) {
        checksum += validation[index];
    }
    validation_sink ^= checksum;
    return 0;
}

int stencil_repeated_main(void) {
    validation_sink = 0U;
    for (uint32_t invocation = 1U;
         invocation <= (uint32_t)RAVEIL_REPEAT_ACCOUNT;
         ++invocation) {
        /*
         * The fixture changes owned input memory between invocations.  The
         * compiler barrier prevents cross-invocation load reuse without
         * making input volatile or suppressing lawful reuse inside one
         * stencil execution.  The held first load is the hardware ordering
         * boundary, so no CPU-only runtime fence belongs in common staging.
         */
        __asm__ volatile ("" ::: "memory");
        if (stencil_once() != 0) {
            return 1;
        }
    }
    return 0;
}
