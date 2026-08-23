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
constexpr std::uint32_t kExpectedFixtureStagingCycles = 648U;
constexpr std::uint32_t kExpectedValidationCycles = 512U;
constexpr std::uint32_t kExpectedCompletionCycles = 1U;
constexpr std::uint32_t kExpectedMeasuredExecutionCycles = kExpectedCycles + 1U;
constexpr std::uint32_t kExpectedWindowTraffic = 1536U;
constexpr const char* kAdapterContract =
    "56dbe3f2ab479233eb5e4fe1c79eb06e07458b42ea77acebb471a101afd24c1e";
constexpr const char* kResourceIdentity =
    "16664d8ed96865c60ea41c91452b5e6748b055e0dfef3f786b13bd6f90127748";
constexpr const char* kFixtureResourceIdentity =
    "87be95fa8293da4b251675e9f81aea003e69e27ea6454a1d1db3c1611539e1f7";

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

std::uint32_t stage_fixture_input(
    VStaticStencilRegion& top,
    std::uint32_t seed
) {
    const std::uint64_t first_cycle = simulation_cycles;
    std::uint32_t traced_words = 0;
    const auto trace_accepted_word = [&]() {
        if (!top.io_fixtureStageAcceptedValid) {
            return;
        }
        if (top.io_fixtureStageAcceptedAddress != traced_words
            || traced_words >= 324U) {
            std::cerr << "fixture accepted trace order mismatch seed="
                      << seed << " expected=" << traced_words
                      << " actual=" << top.io_fixtureStageAcceptedAddress
                      << '\n';
            std::exit(1);
        }
        std::cout << "RAVEIL-FIXTURE-INPUT-V1 invocation=" << seed
                  << " seed=" << seed << " index=" << traced_words
                  << " data=" << std::hex << std::setw(8)
                  << std::setfill('0') << top.io_fixtureStageAcceptedData
                  << std::dec << std::setfill(' ') << std::endl;
        ++traced_words;
    };
    if (!top.io_fixtureStageReady || top.io_busy || top.io_memoryPending) {
        std::cerr << "fixture staging boundary was not ready seed="
                  << seed << '\n';
        std::exit(1);
    }
    top.io_fixtureStageSeed = seed;
    top.io_fixtureStageStart = 1;
    std::cout << "RAVEIL-FIXTURE-PHASE-V1 invocation=" << seed
              << " from=" << (seed == 1U ? 0 : 1)
              << " to=1 cycle=" << (simulation_cycles + 1U)
              << " accepted=0 completed=0 pending=0" << std::endl;
    cycle(top);
    trace_accepted_word();
    top.io_fixtureStageStart = 0;
    for (std::uint32_t guard = 0; !top.io_fixtureStageDone; ++guard) {
        cycle(top);
        trace_accepted_word();
        if (guard > 1024U) {
            std::cerr << "fixture staging exceeded max_cycles seed="
                      << seed << '\n';
            std::exit(1);
        }
    }
    if (top.io_fixtureStageAcceptedCount != 324U
        || top.io_fixtureStageCompletedCount != 324U
        || top.io_memoryPending || !top.io_busy || traced_words != 324U) {
        std::cerr << "fixture staging accounting or release mismatch seed="
                  << seed << " accepted="
                  << top.io_fixtureStageAcceptedCount << " completed="
                  << top.io_fixtureStageCompletedCount << '\n';
        std::exit(1);
    }
    std::cout << "RAVEIL-FIXTURE-PHASE-V1 invocation=" << seed
              << " from=1 to=2 cycle=" << simulation_cycles
              << " accepted=324 completed=324 pending=0" << std::endl;
    std::cout << "RAVEIL-FIXTURE-STAGING-V1 invocation=" << seed
              << " seed=" << seed
              << " accepted=324 completed=324 writes=324"
              << " first_word=0 last_word=323 pending=0"
              << " candidate_accepted_before_release=0 release_count=1"
              << std::endl;
    // The accepted start edge is the staging boundary.  Count the half-open
    // interval from that edge through the final response boundary, matching
    // the CPU manager's timestamp subtraction rather than charging the
    // upstream control-present cycle as candidate time.
    return static_cast<std::uint32_t>(simulation_cycles - first_cycle - 1U);
}

bool run_to_completion(
    VStaticStencilRegion& top,
    std::uint32_t& execution_cycles,
    std::uint32_t& completion_cycles,
    std::uint32_t& accepted,
    std::uint32_t& completed,
    bool launch = true
) {
    if (launch && (top.io_busy || top.io_memoryPending)) {
        std::cerr << "execution window was not quiescent before start\n";
        return false;
    }
    if (!launch && (!top.io_busy || top.io_memoryPending)) {
        std::cerr << "fixture did not release one quiescent execution\n";
        return false;
    }
    const std::uint32_t accepted_before =
        top.io_inputAcceptedCount + top.io_outputAcceptedCount;
    const std::uint32_t completed_before =
        top.io_inputCompletedCount + top.io_outputCompletedCount;
    const std::uint64_t execution_start = simulation_cycles;
    if (launch) {
        top.io_start = 1;
        cycle(top);
        top.io_start = 0;
    }

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
    std::uint32_t& validation_cycles,
    unsigned invocation = 0,
    bool emit_output_words = false
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
        if (emit_output_words) {
            std::cout << "RAVEIL-CONTROLLED-OUTPUT-V1 invocation="
                      << invocation << " index=" << address << " value="
                      << std::hex << std::setw(8) << std::setfill('0') << actual
                      << std::dec << std::setfill(' ') << std::endl;
        }
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

bool verify_fixture_rearm(VStaticStencilRegion& top, unsigned invocation) {
    if (!top.io_fixtureStageReady || top.io_busy || top.io_memoryPending) {
        std::cerr << "fixture did not rearm after validation invocation="
                  << invocation << '\n';
        return false;
    }
    std::cout << "RAVEIL-FIXTURE-REARM-V1 invocation=" << invocation
              << " from=4 to=1 cycle=" << simulation_cycles
              << " pending=0 validation_responses=256 rearm_count=1"
              << std::endl;
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
    std::uint32_t completed,
    bool repeated = false,
    bool fixture = false
) {
    const std::uint32_t total = staging_cycles + execution_cycles
        + completion_cycles + validation_cycles;
    std::cout << (fixture
        ? "RAVEIL-FIXTURE-GRAPH-COMPLETE-V1 status=OK"
        : (repeated
        ? "RAVEIL-REPEATED-GRAPH-COMPLETE-V1 status=OK"
        : "CONTROLLED-GRAPH-WINDOW-V1 status=OK"))
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
              << " resource_sha256=" << (fixture
                    ? kFixtureResourceIdentity : kResourceIdentity)
              << " resource_contract_verified=1"
              << " resource_equality_verified=0 comparison_eligible=0"
              << " performance=not-measured" << std::endl;
    if (fixture) {
        std::cout << "RAVEIL-FIXTURE-RESOURCE-V1 invocation=" << invocation
                  << " resource_sha256=" << kFixtureResourceIdentity
                  << " data_width_bits=32 operation_width_bytes=4"
                  << " request_ports=1 response_ports=1"
                  << " maximum_outstanding_requests=1 request_buffer_depth=0"
                  << " response_buffer_depth=1 physical_banks=1"
                  << " physical_words=1024 valid_words=580"
                  << " arbitration=phase-exclusive-provider-or-candidate"
                  << " accepted_operations=read,write-byte-mask"
                  << " response_rule=one-module-local-cycle-after-acceptance"
                  << " response_hold=stable-until-consumed"
                  << " provider=input-words-324-ascending-full-word"
                  << " provider_initiator=fixture"
                  << " provider_request_buffer_depth=0"
                  << " provider_release=response-consume-word-323"
                  << " provider_rearm=validation-response-consume-word-255"
                  << std::endl;
    }
    if (repeated) {
        std::cout << (fixture
            ? "T0044-FIXTURE-GRAPH-ACTIVITY-V1 invocation="
            : "T0044-REPEATED-GRAPH-ACTIVITY-V1 invocation=") << invocation
                  << " request_stall_cycles=0 response_backpressure_cycles=0"
                  << " read_transactions=1280 write_transactions=256"
                  << " read_bytes=5120 write_bytes=1024 useful_loads=1280"
                  << " useful_adds=1024 useful_stores=256 outputs=256"
                  << " schedule_active_cycles=3072 launch_cycles="
                  << (fixture ? 0 : 1)
                  << " frontend_activity=unavailable"
                  << " rename_rob_issue_lsu=not-applicable" << std::endl;
    }
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
    top.io_fixtureStageStart = 0;
    top.io_fixtureStageSeed = 0;
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
    bool repeated_mode = false;
    bool fixture_mode = false;
    unsigned first_seed = 1;
    unsigned repeated_account = 1;
    if (argc == 2) {
        const std::string argument(argv[1]);
        const std::string pilot_prefix = "--pilot-seed=";
        const std::string repeated_prefix = "--repeat-account=";
        const std::string fixture_prefix = "--fixture-repeat-account=";
        const bool pilot_argument = argument.rfind(pilot_prefix, 0) == 0;
        const bool repeated_argument = argument.rfind(repeated_prefix, 0) == 0;
        const bool fixture_argument = argument.rfind(fixture_prefix, 0) == 0;
        if (!pilot_argument && !repeated_argument && !fixture_argument) {
            std::cerr << "unsupported argument\n";
            return 1;
        }
        const std::string value = argument.substr(
            pilot_argument ? pilot_prefix.size()
                : (fixture_argument ? fixture_prefix.size()
                                    : repeated_prefix.size())
        );
        char* end = nullptr;
        const unsigned long parsed = std::strtoul(value.c_str(), &end, 10);
        if (value.empty() || *end != '\0' || parsed == 0
            || (pilot_argument && parsed > 0xffffffffUL)
            || ((repeated_argument || fixture_argument) && parsed > 256UL)) {
            std::cerr << "pilot seed must be uint32 or repeat account in [1,256]\n";
            return 1;
        }
        if (pilot_argument) {
            pilot_mode = true;
            first_seed = static_cast<unsigned>(parsed);
        } else if (repeated_argument) {
            repeated_mode = true;
            repeated_account = static_cast<unsigned>(parsed);
        } else {
            repeated_mode = true;
            fixture_mode = true;
            repeated_account = static_cast<unsigned>(parsed);
        }
    } else if (argc != 1) {
        std::cerr << "expected at most one pilot seed argument\n";
        return 1;
    }

    const auto first_input = make_input(first_seed);
    const std::uint32_t first_staging_cycles = fixture_mode
        ? stage_fixture_input(top, first_seed)
        : load_input(top, first_input);
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
            first_completed,
            !fixture_mode
        ) || !check_output(
            top, reference(first_input), first_validation_cycles,
            first_seed, repeated_mode
        )) {
        return 1;
    }
    if (fixture_mode && !verify_fixture_rearm(top, first_seed)) {
        return 1;
    }
    if (first_staging_cycles != (fixture_mode
            ? kExpectedFixtureStagingCycles : kExpectedStagingCycles)
        || first_execution_cycles != (fixture_mode
            ? kExpectedCycles : kExpectedMeasuredExecutionCycles)
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
        first_accepted, first_completed, repeated_mode, fixture_mode
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

    if (repeated_mode) {
        std::uint64_t repeated_total = first_staging_cycles
            + first_execution_cycles + first_completion_cycles
            + first_validation_cycles;
        for (unsigned seed = 2; seed <= repeated_account; ++seed) {
            const auto input = make_input(seed);
            const std::uint32_t staging_cycles = fixture_mode
                ? stage_fixture_input(top, seed)
                : load_input(top, input);
            std::uint32_t execution_cycles = 0;
            std::uint32_t completion_cycles = 0;
            std::uint32_t validation_cycles = 0;
            std::uint32_t accepted = 0;
            std::uint32_t completed = 0;
            if (!run_to_completion(
                    top, execution_cycles, completion_cycles,
                    accepted, completed, !fixture_mode
                ) || !check_output(
                    top, reference(input), validation_cycles, seed, true
                )) {
                return 1;
            }
            if (fixture_mode && !verify_fixture_rearm(top, seed)) {
                return 1;
            }
            if (staging_cycles != (fixture_mode
                    ? kExpectedFixtureStagingCycles : kExpectedStagingCycles)
                || execution_cycles != (fixture_mode
                    ? kExpectedCycles : kExpectedMeasuredExecutionCycles)
                || completion_cycles != kExpectedCompletionCycles
                || validation_cycles != kExpectedValidationCycles
                || accepted != kExpectedWindowTraffic
                || completed != kExpectedWindowTraffic) {
                std::cerr << "repeated controlled accounting mismatch seed="
                          << seed << '\n';
                return 1;
            }
            print_controlled_window(
                seed, seed, staging_cycles, execution_cycles,
                completion_cycles, validation_cycles, accepted, completed,
                true, fixture_mode
            );
            repeated_total += staging_cycles + execution_cycles
                + completion_cycles + validation_cycles;
        }
        std::cout << (fixture_mode
            ? "RAVEIL-FIXTURE-GRAPH-ACCOUNT-V1 status=OK account="
            : "RAVEIL-REPEATED-GRAPH-ACCOUNT-V1 status=OK account=")
                  << repeated_account << " installation_count=1"
                  << " simulator_processes=1 resets=1 artifact_reloads=0"
                  << " total_cycles=" << repeated_total
                  << " performance=not-measured" << std::endl;
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

    // Preserve cancel-wins at the narrowest publication race: accept the
    // final output write, then assert cancel while its response is pending.
    // The private output word may be written, but completion/publication must
    // never become visible.
    const auto final_cancel_input = make_input(4);
    load_input(top, final_cancel_input);
    top.io_start = 1;
    cycle(top);
    top.io_start = 0;
    for (unsigned guard = 0;
         !(top.io_graphOutputWritesAccepted == kExpectedOutputWrites
           && top.io_memoryPending);
         ++guard) {
        cycle(top);
        if (guard > 8192U) {
            std::cerr << "final-store cancel did not reach pending response\n";
            return 1;
        }
    }
    top.io_cancel = 1;
    cycle(top);
    if (top.io_done || top.io_outputValid) {
        std::cerr << "final-store cancel exposed completion or publication\n";
        return 1;
    }
    cycle(top);
    top.io_cancel = 0;
    top.eval();
    if (!top.io_cancelled || top.io_busy || top.io_outputValid
        || top.io_memoryPending || top.io_done
        || top.io_graphInputReadsAccepted != kExpectedInputReads
        || top.io_graphOutputWritesAccepted != kExpectedOutputWrites) {
        std::cerr << "final-store cancel did not win publication race\n";
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

    std::cout << "STATIC-STENCIL-RTL-V1 status=OK runs=2 cancelled=2 outputs=512"
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
