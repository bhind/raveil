#include <stdint.h>

static volatile const uint32_t input[12] = {
    0xffffffffu, 1u, 2u, 3u, 5u, 8u,
    13u, 21u, 34u, 55u, 89u, 144u,
};
volatile uint32_t result;

int main(void) {
    uint32_t sum = 0;
    for (uint32_t index = 0; index < 12; ++index) {
        sum += input[index];
    }
    result = sum;
    return 0;
}
