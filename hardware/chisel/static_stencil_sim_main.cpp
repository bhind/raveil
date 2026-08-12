#include "VStaticStencilRegion.h"
#include "verilated.h"

#include <array>
#include <cstdint>
#include <iomanip>
#include <iostream>

namespace {

constexpr std::uint64_t kConfigurationTag = 0xd4bf9395a510385fULL;
constexpr std::uint32_t kExpectedCycles = 256U * 6U;

void cycle(VStaticStencilRegion& top) {
    top.clock = 0;
    top.eval();
    top.clock = 1;
    top.eval();
}

std::array<std::uint32_t, 324> make_input(std::uint32_t seed) {
    std::array<std::uint32_t, 324> input{};
    for (std::uint32_t index = 0; index < input.size(); ++index) {
        input[index] = ((index + 1U) * (seed * 2654435761U))
            ^ (index << (seed & 7U)) ^ (seed * 17U);
    }
    return input;
}

std::array<std::uint32_t, 256> reference(
    const std::array<std::uint32_t, 324>& input
) {
    std::array<std::uint32_t, 256> output{};
    std::size_t output_index = 0;
    for (std::uint32_t y = 1; y <= 16; ++y) {
        for (std::uint32_t x = 1; x <= 16; ++x) {
            const std::uint32_t center = 18U * y + x;
            output[output_index++] =
                input[center]
                + input[center - 18U]
                + input[center + 18U]
                + input[center - 1U]
                + input[center + 1U];
        }
    }
    return output;
}

void load_input(
    VStaticStencilRegion& top,
    const std::array<std::uint32_t, 324>& input
) {
    top.io_inputWriteEnable = 1;
    for (std::uint32_t address = 0; address < input.size(); ++address) {
        top.io_inputWriteAddress = address;
        top.io_inputWriteData = input[address];
        cycle(top);
    }
    top.io_inputWriteEnable = 0;
}

bool run_to_completion(VStaticStencilRegion& top) {
    top.io_start = 1;
    cycle(top);
    top.io_start = 0;

    std::uint32_t guard = 0;
    while (!top.io_done) {
        cycle(top);
        if (++guard > 8192U) {
            std::cerr << "static stencil exceeded max_cycles\n";
            return false;
        }
    }
    if (!top.io_outputValid || top.io_busy) {
        std::cerr << "completion did not publish one valid private output\n";
        return false;
    }
    if (top.io_cycleCount != kExpectedCycles) {
        std::cerr << "fixed schedule cycle mismatch expected=" << kExpectedCycles
                  << " actual=" << top.io_cycleCount << '\n';
        return false;
    }
    return true;
}

bool check_output(
    VStaticStencilRegion& top,
    const std::array<std::uint32_t, 256>& expected
) {
    std::uint64_t checksum = 0;
    for (std::uint32_t address = 0; address < expected.size(); ++address) {
        top.io_outputReadAddress = address;
        top.eval();
        const std::uint32_t actual = top.io_outputReadData;
        if (actual != expected[address]) {
            std::cerr << "stencil mismatch address=" << address
                      << " expected=" << expected[address]
                      << " actual=" << actual << '\n';
            return false;
        }
        checksum += expected[address];
    }
    if (top.io_checksum != checksum) {
        std::cerr << "checksum mismatch expected=" << checksum
                  << " actual=" << top.io_checksum << '\n';
        return false;
    }
    return true;
}

}  // namespace

int main(int argc, char** argv) {
    Verilated::commandArgs(argc, argv);
    VStaticStencilRegion top;

    top.reset = 1;
    top.io_inputWriteEnable = 0;
    top.io_inputWriteAddress = 0;
    top.io_inputWriteData = 0;
    top.io_start = 0;
    top.io_cancel = 0;
    top.io_outputReadAddress = 0;
    cycle(top);
    top.reset = 0;

    if (top.io_configurationTag != kConfigurationTag) {
        std::cerr << "configuration tag mismatch\n";
        return 1;
    }

    const auto first_input = make_input(1);
    load_input(top, first_input);
    if (!run_to_completion(top) || !check_output(top, reference(first_input))) {
        return 1;
    }

    const auto cancelled_input = make_input(2);
    load_input(top, cancelled_input);
    top.io_start = 1;
    cycle(top);
    top.io_start = 0;
    for (unsigned index = 0; index < 17; ++index) {
        cycle(top);
    }
    top.io_cancel = 1;
    cycle(top);
    if (!top.io_cancelled || top.io_busy || top.io_outputValid) {
        std::cerr << "cancel did not invalidate the private output\n";
        return 1;
    }
    top.io_cancel = 0;

    const auto second_input = make_input(3);
    load_input(top, second_input);
    if (!run_to_completion(top) || !check_output(top, reference(second_input))) {
        return 1;
    }

    std::cout << "STATIC-STENCIL-RTL-V1 status=OK runs=2 cancelled=1 outputs=512"
              << " cycles_per_run=" << kExpectedCycles
              << " configuration_tag=" << std::hex << std::setw(16)
              << std::setfill('0') << kConfigurationTag << std::dec
              << " evidence=rtl-simulation-functional performance=not-measured"
              << std::endl;
    top.final();
    return 0;
}
