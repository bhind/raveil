#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>

extern int t0191_program_main(void);
extern volatile uint32_t result;

int main(void) {
    if (t0191_program_main() != 0) {
        return 2;
    }
    printf("%" PRIu32 "\n", result);
    return 0;
}
