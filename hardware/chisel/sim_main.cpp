#include "VCounter.h"
#include "verilated.h"

#include <cstdint>
#include <iostream>

static void cycle(VCounter& top) {
    top.clock = 0;
    top.eval();
    top.clock = 1;
    top.eval();
}

int main(int argc, char** argv) {
    Verilated::commandArgs(argc, argv);
    VCounter top;

    top.reset = 1;
    top.io_enable = 0;
    cycle(top);
    top.reset = 0;

    for (std::uint32_t expected = 0; expected < 8; ++expected) {
        if (top.io_value != expected) {
            std::cerr << "counter mismatch expected=" << expected
                      << " actual=" << static_cast<unsigned>(top.io_value) << '\n';
            return 1;
        }
        top.io_enable = 1;
        cycle(top);
    }

    top.io_enable = 0;
    cycle(top);
    if (top.io_value != 8) {
        std::cerr << "counter hold mismatch actual="
                  << static_cast<unsigned>(top.io_value) << '\n';
        return 1;
    }

    std::cout << "CHISEL-SMOKE-V1 status=OK cycles=10 value=8" << std::endl;
    top.final();
    return 0;
}
