#include <stdint.h>

extern uint32_t input_words[324];
extern uint32_t output_words[256];

int stencil_main(void) {
    const uint32_t seed = 1U;
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
    return output_index == 256U ? 0 : 1;
}
