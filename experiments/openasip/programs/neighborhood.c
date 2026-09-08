#include <stdint.h>

static volatile const uint32_t input[4][4] = {
    {1, 2, 3, 4},
    {5, 6, 7, 8},
    {9, 10, 11, 12},
    {13, 14, 15, 16},
};

volatile uint32_t result;

int main(void) {
    uint32_t sum = 0;
    for (uint32_t row = 1; row < 3; ++row) {
        for (uint32_t col = 1; col < 3; ++col) {
            sum += input[row][col];
            sum += input[row - 1][col];
            sum += input[row + 1][col];
            sum += input[row][col - 1];
            sum += input[row][col + 1];
        }
    }
    result = sum;
    return 0;
}
