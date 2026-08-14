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

static int stencil_once(uint32_t seed) {
    for (uint32_t index = 0; index < 324U; ++index) {
        input_words[index] = ((index + 1U) * (seed * 2654435761U))
            ^ (index << (seed & 7U)) ^ (seed * 17U);
    }

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
    for (uint32_t seed = 1U; seed <= (uint32_t)RAVEIL_REPEAT_ACCOUNT; ++seed) {
        if (stencil_once(seed) != 0) {
            return 1;
        }
    }
    return 0;
}
