#include <stdint.h>

static volatile const uint32_t input[8] = {3, 5, 8, 13, 21, 34, 55, 89};
volatile uint32_t result;

int main(void) {
    uint32_t checksum = 0;
    for (uint32_t index = 0; index < 8; ++index) {
        checksum += input[index] * 3u + 7u;
    }
    result = checksum;
    return 0;
}
