#include "VOwnedFixedLatencyScratchpad.h"
#include "verilated.h"

#include <cstdint>
#include <iostream>

namespace {

std::uint64_t cycle_number = 0;

void cycle(VOwnedFixedLatencyScratchpad& top) {
    top.clock = 0;
    top.eval();
    top.clock = 1;
    top.eval();
    ++cycle_number;
}

void clear_request(VOwnedFixedLatencyScratchpad& top) {
    top.io_requestValid = 0;
    top.io_requestWrite = 0;
    top.io_requestAddress = 0;
    top.io_requestWriteData = 0;
    top.io_requestWriteMask = 0;
    top.io_requestInitiator = 0;
    top.io_requestPhase = 0;
}

bool issue(
    VOwnedFixedLatencyScratchpad& top,
    bool write,
    std::uint32_t address,
    std::uint32_t data,
    std::uint32_t mask,
    std::uint32_t initiator,
    std::uint32_t phase
) {
    if (!top.io_requestReady || top.io_responseValid) {
        std::cerr << "request boundary was not idle\n";
        return false;
    }
    top.io_requestValid = 1;
    top.io_requestWrite = write;
    top.io_requestAddress = address;
    top.io_requestWriteData = data;
    top.io_requestWriteMask = mask;
    top.io_requestInitiator = initiator;
    top.io_requestPhase = phase;
    const auto accept_cycle = cycle_number + 1;
    cycle(top);
    clear_request(top);
    top.eval();

    if (!top.io_responseValid || !top.io_pending) {
        std::cerr << "response was not available one cycle after acceptance\n";
        return false;
    }
    if (cycle_number != accept_cycle) {
        std::cerr << "cycle accounting mismatch\n";
        return false;
    }
    if (top.io_responseWrite != write
        || top.io_responseInitiator != initiator
        || top.io_responsePhase != phase) {
        std::cerr << "response attribution mismatch\n";
        return false;
    }
    return true;
}

bool retire(VOwnedFixedLatencyScratchpad& top) {
    if (!top.io_responseValid) {
        std::cerr << "attempted to retire a missing response\n";
        return false;
    }
    top.io_responseReady = 1;
    cycle(top);
    top.io_responseReady = 0;
    top.eval();
    if (top.io_responseValid || top.io_pending) {
        std::cerr << "response did not retire\n";
        return false;
    }
    return true;
}

}  // namespace

int main(int argc, char** argv) {
    Verilated::commandArgs(argc, argv);
    VOwnedFixedLatencyScratchpad top;

    clear_request(top);
    top.io_responseReady = 0;
    top.reset = 1;
    cycle(top);
    cycle(top);
    top.reset = 0;
    top.eval();

    if (!top.io_requestReady || top.io_pending) {
        std::cerr << "reset did not produce an idle boundary\n";
        return 1;
    }

    if (!issue(top, false, 7, 0, 0, 2, 2)) {
        return 1;
    }
    if (top.io_responseError || top.io_responseReadData != 0) {
        std::cerr << "zero-initialized read mismatch\n";
        return 1;
    }

    const auto held_data = top.io_responseReadData;
    const auto held_initiator = top.io_responseInitiator;
    const auto held_phase = top.io_responsePhase;
    top.io_requestValid = 1;
    top.io_requestWrite = 0;
    top.io_requestAddress = 8;
    top.io_requestInitiator = 1;
    top.io_requestPhase = 2;
    cycle(top);
    clear_request(top);
    if (top.io_requestReady || top.io_requestStallCount != 1
        || top.io_acceptedCount != 1) {
        std::cerr << "request backpressure accounting mismatch\n";
        return 1;
    }
    for (unsigned stall = 0; stall < 3; ++stall) {
        cycle(top);
        if (!top.io_responseValid || top.io_responseReadData != held_data
            || top.io_responseInitiator != held_initiator
            || top.io_responsePhase != held_phase) {
            std::cerr << "response changed under backpressure\n";
            return 1;
        }
    }
    if (top.io_responseStallCount != 4 || !retire(top)) {
        std::cerr << "response stall accounting mismatch\n";
        return 1;
    }

    if (!issue(top, true, 7, 0x11223344U, 0xfU, 1, 1)
        || top.io_responseError || !retire(top)) {
        return 1;
    }
    if (!issue(top, false, 7, 0, 0, 1, 4)) {
        return 1;
    }
    if (top.io_responseError || top.io_responseReadData != 0x11223344U
        || !retire(top)) {
        std::cerr << "full-word write/read mismatch\n";
        return 1;
    }

    if (!issue(top, true, 7, 0xaabbccddU, 0x5U, 2, 2)
        || top.io_responseError || !retire(top)) {
        return 1;
    }
    if (!issue(top, false, 7, 0, 0, 2, 2)) {
        return 1;
    }
    if (top.io_responseError || top.io_responseReadData != 0x11bb33ddU
        || !retire(top)) {
        std::cerr << "byte-mask merge mismatch\n";
        return 1;
    }

    if (!issue(top, false, 511, 0, 0, 0, 0)) {
        return 1;
    }
    if (!top.io_responseError || !retire(top)) {
        std::cerr << "out-of-range request was not rejected deterministically\n";
        return 1;
    }

    if (top.io_acceptedCount != 6 || top.io_completedCount != 6
        || top.io_pending || top.io_requestStallCount != 1) {
        std::cerr << "transaction accounting mismatch accepted="
                  << top.io_acceptedCount << " completed="
                  << top.io_completedCount << '\n';
        return 1;
    }

    std::cout
        << "OWNED-FIXED-LATENCY-SCRATCHPAD-V1 status=OK"
        << " accepted=6 completed=6 pending=0"
        << " response_availability_latency_cycles=1"
        << " initiator_attribution=1 phase_attribution=1"
        << " read_covered=1 write_covered=1 byte_mask_covered=1"
        << " request_backpressure_covered=1 response_backpressure_covered=1"
        << " range_rejection_covered=1"
        << " memory_model=owned-fixed-latency-scratchpad-local"
        << " resource_match_verified=0 matched_comparison_ready=0"
        << " fixed_end_to_end_latency_claim=0"
        << " evidence=rtl-simulation-functional performance=not-measured"
        << std::endl;
    top.final();
    return 0;
}
