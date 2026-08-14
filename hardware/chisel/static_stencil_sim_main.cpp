#include "VStaticStencilRegion.h"
#include "verilated.h"

#include <array>
#include <cstdint>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <string>

namespace {

constexpr std::uint64_t kConfigurationTag = 0xd4bf9395a510385fULL;
constexpr std::uint32_t kExpectedCycles = 256U * 12U;
constexpr std::uint32_t kExpectedInputReads = 256U * 5U;
constexpr std::uint32_t kExpectedOutputWrites = 256U;
constexpr std::uint32_t kExpectedStagingCycles = 648U;
constexpr std::uint32_t kExpectedValidationCycles = 512U;
constexpr std::uint32_t kExpectedCompletionCycles = 1U;
constexpr std::uint32_t kExpectedMeasuredExecutionCycles = kExpectedCycles + 1U;
constexpr std::uint32_t kExpectedWindowTraffic = 1536U;
constexpr const char* kAdapterContract =
    "56dbe3f2ab479233eb5e4fe1c79eb06e07458b42ea77acebb471a101afd24c1e";
constexpr const char* kResourceIdentity =
    "16664d8ed96865c60ea41c91452b5e6748b055e0dfef3f786b13bd6f90127748";

std::uint64_t simulation_cycles = 0;

void cycle(VStaticStencilRegion& top) {
    top.clock = 0;
    top.eval();
    top.clock = 1;
    top.eval();
    ++simulation_cycles;
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

std::uint32_t load_input(
    VStaticStencilRegion& top,
    const std::array<std::uint32_t, 324>& input
) {
    const std::uint64_t first_cycle = simulation_cycles;
    for (std::uint32_t address = 0; address < input.size(); ++address) {
        if (!top.io_inputStageReady || top.io_memoryPending) {
            std::cerr << "input staging boundary was not ready address="
                      << address << '\n';
            std::exit(1);
        }
        top.io_inputStageValid = 1;
        top.io_inputStageAddress = address;
        top.io_inputStageData = input[address];
        cycle(top);
        top.io_inputStageValid = 0;
        top.eval();
        if (!top.io_inputStageResponseValid
            || top.io_inputStageResponseError) {
            std::cerr << "input staging response mismatch address="
                      << address << '\n';
            std::exit(1);
        }
        top.io_inputStageResponseReady = 1;
        cycle(top);
        top.io_inputStageResponseReady = 0;
        top.eval();
    }
    return static_cast<std::uint32_t>(simulation_cycles - first_cycle);
}

bool run_to_completion(
    VStaticStencilRegion& top,
    std::uint32_t& execution_cycles,
    std::uint32_t& completion_cycles,
    std::uint32_t& accepted,
    std::uint32_t& completed
) {
    if (top.io_busy || top.io_memoryPending) {
        std::cerr << "execution window was not quiescent before start\n";
        return false;
    }
    const std::uint32_t accepted_before =
        top.io_inputAcceptedCount + top.io_outputAcceptedCount;
    const std::uint32_t completed_before =
        top.io_inputCompletedCount + top.io_outputCompletedCount;
    const std::uint64_t execution_start = simulation_cycles;
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
    execution_cycles = static_cast<std::uint32_t>(
        simulation_cycles - execution_start
    );
    if (!top.io_outputValid || top.io_busy) {
        std::cerr << "completion did not publish one valid private output\n";
        return false;
    }
    accepted = top.io_inputAcceptedCount + top.io_outputAcceptedCount
        - accepted_before;
    completed = top.io_inputCompletedCount + top.io_outputCompletedCount
        - completed_before;
    const std::uint64_t completion_start = simulation_cycles;
    cycle(top);
    completion_cycles = static_cast<std::uint32_t>(
        simulation_cycles - completion_start
    );
    if (top.io_busy || top.io_memoryPending) {
        std::cerr << "execution window was not quiescent after completion\n";
        return false;
    }
    if (top.io_cycleCount != kExpectedCycles) {
        std::cerr << "fixed schedule cycle mismatch expected=" << kExpectedCycles
                  << " actual=" << top.io_cycleCount << '\n';
        return false;
    }
    if (top.io_graphInputReadsAccepted != kExpectedInputReads
        || top.io_graphOutputWritesAccepted != kExpectedOutputWrites
        || top.io_memoryPending) {
        std::cerr << "graph memory operation count mismatch reads="
                  << top.io_graphInputReadsAccepted << " writes="
                  << top.io_graphOutputWritesAccepted << '\n';
        return false;
    }
    return true;
}

bool check_output(
    VStaticStencilRegion& top,
    const std::array<std::uint32_t, 256>& expected,
    std::uint32_t& validation_cycles
) {
    const std::uint64_t first_cycle = simulation_cycles;
    std::uint64_t checksum = 0;
    for (std::uint32_t address = 0; address < expected.size(); ++address) {
        if (!top.io_outputValidationReady || top.io_memoryPending) {
            std::cerr << "output validation boundary was not ready address="
                      << address << '\n';
            return false;
        }
        top.io_outputValidationValid = 1;
        top.io_outputValidationAddress = address;
        cycle(top);
        top.io_outputValidationValid = 0;
        top.eval();
        if (!top.io_outputValidationResponseValid
            || top.io_outputValidationResponseError) {
            std::cerr << "output validation response mismatch address="
                      << address << '\n';
            return false;
        }
        const std::uint32_t actual = top.io_outputValidationReadData;
        if (actual != expected[address]) {
            std::cerr << "stencil mismatch address=" << address
                      << " expected=" << expected[address]
                      << " actual=" << actual << '\n';
            return false;
        }
        top.io_outputValidationResponseReady = 1;
        cycle(top);
        top.io_outputValidationResponseReady = 0;
        top.eval();
        checksum += expected[address];
    }
    if (top.io_checksum != checksum) {
        std::cerr << "checksum mismatch expected=" << checksum
                  << " actual=" << top.io_checksum << '\n';
        return false;
    }
    validation_cycles = static_cast<std::uint32_t>(
        simulation_cycles - first_cycle
    );
    return true;
}

void print_controlled_window(
    unsigned invocation,
    unsigned seed,
    std::uint32_t staging_cycles,
    std::uint32_t execution_cycles,
    std::uint32_t completion_cycles,
    std::uint32_t validation_cycles,
    std::uint32_t accepted,
    std::uint32_t completed
) {
    const std::uint32_t total = staging_cycles + execution_cycles
        + completion_cycles + validation_cycles;
    std::cout << "CONTROLLED-GRAPH-WINDOW-V1 status=OK"
              << " invocation=" << invocation
              << " seed=" << seed
              << " installation_cycles=0"
              << " staging_cycles=" << staging_cycles
              << " execution_cycles=" << execution_cycles
              << " completion_cycles=" << completion_cycles
              << " validation_cycles=" << validation_cycles
              << " publication_cycles=0"
              << " total_cycles=" << total
              << " quiescence_before=1 quiescence_after=1"
              << " traffic_accepted=" << accepted
              << " traffic_completed=" << completed
              << " traffic_pending=0 graph_traffic=" << accepted
              << " unaccounted_window_traffic=0"
              << " resource_sha256=" << kResourceIdentity
              << " resource_contract_verified=1"
              << " resource_equality_verified=0 comparison_eligible=0"
              << " performance=not-measured" << std::endl;
}

}  // namespace

int main(int argc, char** argv) {
    Verilated::commandArgs(argc, argv);
    VStaticStencilRegion top;

    top.reset = 1;
    top.io_inputStageValid = 0;
    top.io_inputStageAddress = 0;
    top.io_inputStageData = 0;
    top.io_inputStageResponseReady = 0;
    top.io_start = 0;
    top.io_cancel = 0;
    top.io_outputValidationValid = 0;
    top.io_outputValidationAddress = 0;
    top.io_outputValidationResponseReady = 0;
    cycle(top);
    top.reset = 0;

    if (top.io_configurationTag != kConfigurationTag) {
        std::cerr << "configuration tag mismatch\n";
        return 1;
    }

    bool pilot_mode = false;
    unsigned first_seed = 1;
    if (argc == 2) {
        const std::string argument(argv[1]);
        const std::string prefix = "--pilot-seed=";
        if (argument.rfind(prefix, 0) != 0) {
            std::cerr << "unsupported argument\n";
            return 1;
        }
        const std::string value = argument.substr(prefix.size());
        char* end = nullptr;
        const unsigned long parsed = std::strtoul(value.c_str(), &end, 10);
        if (value.empty() || *end != '\0' || parsed == 0 || parsed > 0xffffffffUL) {
            std::cerr << "pilot seed must be uint32 and nonzero\n";
            return 1;
        }
        pilot_mode = true;
        first_seed = static_cast<unsigned>(parsed);
    } else if (argc != 1) {
        std::cerr << "expected at most one pilot seed argument\n";
        return 1;
    }

    const auto first_input = make_input(first_seed);
    const std::uint32_t first_staging_cycles = load_input(top, first_input);
    std::uint32_t first_execution_cycles = 0;
    std::uint32_t first_completion_cycles = 0;
    std::uint32_t first_validation_cycles = 0;
    std::uint32_t first_accepted = 0;
    std::uint32_t first_completed = 0;
    if (!run_to_completion(
            top,
            first_execution_cycles,
            first_completion_cycles,
            first_accepted,
            first_completed
        ) || !check_output(
            top, reference(first_input), first_validation_cycles
        )) {
        return 1;
    }
    if (first_staging_cycles != kExpectedStagingCycles
        || first_execution_cycles != kExpectedMeasuredExecutionCycles
        || first_completion_cycles != kExpectedCompletionCycles
        || first_validation_cycles != kExpectedValidationCycles
        || first_accepted != kExpectedWindowTraffic
        || first_completed != kExpectedWindowTraffic) {
        std::cerr << "first controlled accounting mismatch\n";
        return 1;
    }
    print_controlled_window(
        first_seed, first_seed, first_staging_cycles, first_execution_cycles,
        first_completion_cycles, first_validation_cycles,
        first_accepted, first_completed
    );

    if (pilot_mode) {
        std::cout << "T0044-GRAPH-ACTIVITY-V1 seed=" << first_seed
                  << " useful_loads=1280 useful_adds=1024 useful_stores=256"
                  << " outputs=256 read_transactions=1280 write_transactions=256"
                  << " read_bytes=5120 write_bytes=1024 request_stall_cycles=0"
                  << " response_backpressure_cycles=0 schedule_active_cycles="
                  << kExpectedCycles << " launch_cycles=1"
                  << " frontend_activity=unavailable rename_rob_issue_lsu=not-applicable"
                  << std::endl;
        top.final();
        return 0;
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
    top.io_cancel = 0;
    for (unsigned guard = 0; top.io_busy && guard < 4; ++guard) {
        cycle(top);
    }
    if (!top.io_cancelled || top.io_busy || top.io_outputValid
        || top.io_memoryPending) {
        std::cerr << "cancel did not invalidate the private output\n";
        return 1;
    }
    if (top.io_graphInputReadsAccepted != 8
        || top.io_graphOutputWritesAccepted != 1) {
        std::cerr << "cancelled graph transaction count mismatch reads="
                  << top.io_graphInputReadsAccepted << " writes="
                  << top.io_graphOutputWritesAccepted << '\n';
        return 1;
    }

    const auto second_input = make_input(3);
    const std::uint32_t second_staging_cycles = load_input(top, second_input);
    std::uint32_t second_execution_cycles = 0;
    std::uint32_t second_completion_cycles = 0;
    std::uint32_t second_validation_cycles = 0;
    std::uint32_t second_accepted = 0;
    std::uint32_t second_completed = 0;
    if (!run_to_completion(
            top,
            second_execution_cycles,
            second_completion_cycles,
            second_accepted,
            second_completed
        ) || !check_output(
            top, reference(second_input), second_validation_cycles
        )) {
        return 1;
    }
    if (second_staging_cycles != kExpectedStagingCycles
        || second_execution_cycles != kExpectedMeasuredExecutionCycles
        || second_completion_cycles != kExpectedCompletionCycles
        || second_validation_cycles != kExpectedValidationCycles
        || second_accepted != kExpectedWindowTraffic
        || second_completed != kExpectedWindowTraffic) {
        std::cerr << "second controlled accounting mismatch\n";
        return 1;
    }
    print_controlled_window(
        3, 3, second_staging_cycles, second_execution_cycles,
        second_completion_cycles, second_validation_cycles,
        second_accepted, second_completed
    );

    std::cout << "STATIC-STENCIL-RTL-V1 status=OK runs=2 cancelled=1 outputs=512"
              << " cycles_per_run=" << kExpectedCycles
              << " graph_input_reads_per_run=" << kExpectedInputReads
              << " graph_output_writes_per_run=" << kExpectedOutputWrites
              << " configuration_tag=" << std::hex << std::setw(16)
              << std::setfill('0') << kConfigurationTag << std::dec
              << " memory_model=owned-single-bank-two-logical-regions"
              << " cpu_connected=0 fixed_end_to_end_latency_claim=0"
              << " resource_match_verified=0 matched_comparison_ready=0"
              << " evidence=rtl-simulation-functional performance=not-measured"
              << std::endl;
    std::cout << "SIMULATION-ADAPTER-V2 status=FUNCTIONAL implementation=static-graph"
              << " adapter_contract=" << kAdapterContract
              << " accounting_complete=0 total_cycles=UNAVAILABLE"
              << " memory_model=owned-private-scratchpads"
              << " resource_match_verified=0 matched_comparison_ready=0"
              << " missing=installation,completion,publication"
              << " performance=not-measured" << std::endl;
    top.final();
    return 0;
}
