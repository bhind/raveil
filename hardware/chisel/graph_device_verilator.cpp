#include "VStaticStencilRegion.h"
#include "verilated.h"

#include "graph_device_abi_generated.h"
#include "graph_device_runtime.h"
#ifdef RAVEIL_DAG_RUNTIME
#include "graph_device_dag_runtime.h"
#elif defined(RAVEIL_AFFINE_RUNTIME)
#include "graph_device_affine_runtime.h"
#endif

#include <array>
#include <charconv>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <ostream>
#include <string>

namespace {
bool parse_seed(const char* text, std::uint32_t& value) {
    const std::string source(text);
    if (source.empty()) return false;
    const auto result = std::from_chars(source.data(), source.data() + source.size(), value);
    return result.ec == std::errc{} && result.ptr == source.data() + source.size();
}
}  // namespace

namespace raveil::graph_device {

class VerilatorDeviceTransport final : public DeviceTransport
#if defined(RAVEIL_AFFINE_RUNTIME) || defined(RAVEIL_DAG_RUNTIME)
    , public AffineInstallTransport
#endif
#ifdef RAVEIL_DAG_RUNTIME
    , public ProgramInstallTransport
#endif
{
public:
    explicit VerilatorDeviceTransport(VStaticStencilRegion& top) : top_(top) {
        clear_inputs();
        hard_reset();
    }

    void set_transaction_trace(std::ostream* trace) {
        transaction_trace_ = trace;
    }

    DeviceRead read_word(std::uint32_t offset) override {
        if (offset == abi::kRegIdentity) return {true, abi::kIdentity};
        if (offset == abi::kRegVersion) return {true, abi::kVersion};
        if (offset == abi::kRegInputCount) return {true, abi::kInputCount};
        if (offset == abi::kRegOutputCount) return {true, abi::kOutputCount};
        if (offset >= abi::kRegDescriptorBase && offset < abi::kRegDescriptorBase + 8U) {
            return {true, abi::kDescriptorWords[offset - abi::kRegDescriptorBase]};
        }
        if (offset >= abi::kRegConfigBase && offset < abi::kRegConfigBase + 8U) {
            return {true, abi::kConfigWords[offset - abi::kRegConfigBase]};
        }
        if (offset >= abi::kRegImplementationBase && offset < abi::kRegImplementationBase + 8U) {
            return {true, abi::kImplementationWords[offset - abi::kRegImplementationBase]};
        }
        if (offset == abi::kRegStatus) {
            cycle();
            return {true, status()};
        }
        if (offset == abi::kRegChecksumLow) {
            return {true, static_cast<std::uint32_t>(top_.io_checksum)};
        }
        if (offset == abi::kRegChecksumHigh) {
            return {true, static_cast<std::uint32_t>(top_.io_checksum >> 32U)};
        }
        if (offset >= abi::kOutputBase && offset < abi::kOutputBase + abi::kOutputCount) {
            return read_private_output(offset - abi::kOutputBase);
        }
        fault_ = true;
        return {false, 0U};
    }

    bool write_word(std::uint32_t offset, std::uint32_t value) override {
        if (offset == abi::kRegControl) {
            return control(value);
        }
        if (offset >= abi::kInputBase && offset < abi::kInputBase + abi::kInputCount) {
            return stage_input(offset - abi::kInputBase, value);
        }
        fault_ = true;
        return false;
    }

#if defined(RAVEIL_AFFINE_RUNTIME) || defined(RAVEIL_DAG_RUNTIME)
    DeviceRead read_install_word(std::uint32_t offset) override {
        if (offset == install_abi::kRegIdentity) {
            return {true, install_abi::kIdentity};
        }
        if (offset == install_abi::kRegVersion) {
            return {true, install_abi::kVersion};
        }
        if (offset == install_abi::kRegStatus) {
            std::uint32_t value = 0;
            if (top_.io_configLoading) value |= install_abi::kStatusLoading;
            if (top_.io_configInstalled) value |= install_abi::kStatusInstalled;
            if (top_.io_configFault) value |= install_abi::kStatusFault;
            return {true, value};
        }
        if (offset == install_abi::kRegPayloadCount) {
            return {true, top_.io_configPayloadCount};
        }
        if (offset >= install_abi::kRegDigestBase
            && offset < install_abi::kRegDigestBase + 8U) {
            const std::array<std::uint32_t, 8> digest = {
                top_.io_configLiveDigest_0,
                top_.io_configLiveDigest_1,
                top_.io_configLiveDigest_2,
                top_.io_configLiveDigest_3,
                top_.io_configLiveDigest_4,
                top_.io_configLiveDigest_5,
                top_.io_configLiveDigest_6,
                top_.io_configLiveDigest_7,
            };
            return {true, digest[offset - install_abi::kRegDigestBase]};
        }
        return {false, 0U};
    }

    bool write_install_word(
        std::uint32_t offset,
        std::uint32_t value
    ) override {
        if (offset == install_abi::kRegControl) {
            if (value != install_abi::kControlClear
                && value != install_abi::kControlCommit) {
                return false;
            }
            top_.io_configClear = value == install_abi::kControlClear;
            top_.io_configCommit = value == install_abi::kControlCommit;
            cycle();
            top_.io_configClear = 0;
            top_.io_configCommit = 0;
            top_.eval();
            return true;
        }
        if (offset >= install_abi::kPayloadBase
            && offset < install_abi::kPayloadBase + install_abi::kPayloadCount) {
            top_.io_configWrite = 1;
            top_.io_configAddress = offset - install_abi::kPayloadBase;
            top_.io_configData = value;
            cycle();
            top_.io_configWrite = 0;
            top_.eval();
            return true;
        }
        return false;
    }
#endif

#ifdef RAVEIL_DAG_RUNTIME
    DeviceRead read_program_word(std::uint32_t offset) override {
        if (offset == program_abi::kRegIdentity) {
            return {true, program_abi::kIdentity};
        }
        if (offset == program_abi::kRegVersion) {
            return {true, program_abi::kVersion};
        }
        if (offset == program_abi::kRegStatus) {
            std::uint32_t value = 0;
            if (top_.io_programLoading) value |= program_abi::kStatusLoading;
            if (top_.io_programInstalled) value |= program_abi::kStatusInstalled;
            if (top_.io_programFault) value |= program_abi::kStatusFault;
            return {true, value};
        }
        if (offset == program_abi::kRegPayloadCount) {
            return {true, top_.io_programPayloadCount};
        }
        if (offset >= program_abi::kRegDigestBase
            && offset < program_abi::kRegDigestBase + 8U) {
            const std::array<std::uint32_t, 8> digest = {
                top_.io_programLiveDigest_0,
                top_.io_programLiveDigest_1,
                top_.io_programLiveDigest_2,
                top_.io_programLiveDigest_3,
                top_.io_programLiveDigest_4,
                top_.io_programLiveDigest_5,
                top_.io_programLiveDigest_6,
                top_.io_programLiveDigest_7,
            };
            return {true, digest[offset - program_abi::kRegDigestBase]};
        }
        return {false, 0U};
    }

    bool write_program_word(
        std::uint32_t offset,
        std::uint32_t value
    ) override {
        if (offset == program_abi::kRegControl) {
            if (value != program_abi::kControlClear
                && value != program_abi::kControlCommit) return false;
            top_.io_programClear = value == program_abi::kControlClear;
            top_.io_programCommit = value == program_abi::kControlCommit;
            cycle();
            top_.io_programClear = 0;
            top_.io_programCommit = 0;
            top_.eval();
            return true;
        }
        if (offset >= program_abi::kPayloadBase
            && offset < program_abi::kPayloadBase + program_abi::kPayloadCount) {
            top_.io_programWrite = 1;
            top_.io_programAddress = offset - program_abi::kPayloadBase;
            top_.io_programData = value;
            cycle();
            top_.io_programWrite = 0;
            top_.eval();
            return true;
        }
        return false;
    }
#endif

private:
    VStaticStencilRegion& top_;
    std::uint32_t staged_words_ = 0;
    bool completed_ = false;
    bool cancelled_ = false;
    bool fault_ = false;
    bool rtl_configuration_matches_ = false;
    std::ostream* transaction_trace_ = nullptr;

    void trace_event(const char* event) {
        if (transaction_trace_ != nullptr) {
            *transaction_trace_ << "GraphDevice-TRACE-V1 event=" << event << '\n';
        }
    }

    void trace_transaction() {
        if (transaction_trace_ != nullptr && top_.io_transactionTraceValid) {
            *transaction_trace_ << "GraphDevice-TRACE-V1 event=transaction write="
                << static_cast<unsigned>(top_.io_transactionTraceWrite)
                << " address=" << top_.io_transactionTraceAddress
                << " data=" << std::hex << std::setw(8) << std::setfill('0')
                << static_cast<std::uint32_t>(top_.io_transactionTraceWriteData)
                << std::dec << std::setfill(' ') << '\n';
        }
    }

    void clear_inputs() {
        top_.io_inputStageValid = 0;
        top_.io_inputStageAddress = 0;
        top_.io_inputStageData = 0;
        top_.io_inputStageResponseReady = 0;
        top_.io_fixtureStageStart = 0;
        top_.io_fixtureStageSeed = 0;
        top_.io_start = 0;
        top_.io_cancel = 0;
        top_.io_configClear = 0;
        top_.io_configWrite = 0;
        top_.io_configCommit = 0;
        top_.io_configAddress = 0;
        top_.io_configData = 0;
        top_.io_programClear = 0;
        top_.io_programWrite = 0;
        top_.io_programCommit = 0;
        top_.io_programAddress = 0;
        top_.io_programData = 0;
        top_.io_outputValidationValid = 0;
        top_.io_outputValidationAddress = 0;
        top_.io_outputValidationResponseReady = 0;
    }

    void update_sticky() {
        completed_ = completed_ || top_.io_done;
        cancelled_ = cancelled_ || top_.io_cancelled;
    }

    void cycle() {
        top_.clock = 0;
        top_.eval();
        trace_transaction();
        top_.clock = 1;
        top_.eval();
        update_sticky();
    }

    void hard_reset() {
        clear_inputs();
        top_.reset = 1;
        cycle();
        top_.reset = 0;
        cycle();
        staged_words_ = 0;
        completed_ = false;
        cancelled_ = false;
        rtl_configuration_matches_ =
            top_.io_configurationTag == abi::kRtlConfigurationTag;
        fault_ = !rtl_configuration_matches_;
    }

    std::uint32_t status() const {
        std::uint32_t value = 0;
        if (top_.io_busy) value |= abi::kStatusBusy;
        if (completed_) value |= abi::kStatusCompleted;
        if (cancelled_) value |= abi::kStatusCancelled;
        if (fault_) value |= abi::kStatusFault;
        if (top_.io_outputValid) value |= abi::kStatusOutputValid;
#ifdef RAVEIL_DAG_RUNTIME
        if (top_.io_configFault || top_.io_programFault) value |= abi::kStatusFault;
#endif
        return value;
    }

    bool control(std::uint32_t value) {
        if (value == abi::kControlReset) {
            trace_event("reset");
            hard_reset();
            return true;
        }
        if (value == abi::kControlStart) {
            if (staged_words_ != abi::kInputCount || top_.io_busy || top_.io_memoryPending) {
                fault_ = true;
                return false;
            }
            completed_ = false;
            cancelled_ = false;
            fault_ = !rtl_configuration_matches_ || !top_.io_configInstalled
                || top_.io_configLoading || top_.io_configFault;
#ifdef RAVEIL_DAG_RUNTIME
            fault_ = fault_ || !top_.io_programInstalled
                || top_.io_programLoading || top_.io_programFault;
#endif
            if (fault_) {
                return false;
            }
            trace_event("start");
            top_.io_start = 1;
            cycle();
            top_.io_start = 0;
            top_.eval();
            staged_words_ = 0;
            return top_.io_busy;
        }
        if (value == abi::kControlCancel) {
            if (!top_.io_busy) {
                fault_ = true;
                return false;
            }
            trace_event("cancel");
            top_.io_cancel = 1;
            cycle();
            top_.io_cancel = 0;
            top_.eval();
            return true;
        }
        fault_ = true;
        return false;
    }

    bool stage_input(std::uint32_t index, std::uint32_t value) {
        if (top_.io_busy || top_.io_memoryPending || index != staged_words_
            || !top_.io_inputStageReady) {
            fault_ = true;
            return false;
        }
        top_.io_inputStageValid = 1;
        top_.io_inputStageAddress = index;
        top_.io_inputStageData = value;
        cycle();
        top_.io_inputStageValid = 0;
        top_.eval();
        if (!top_.io_inputStageResponseValid || top_.io_inputStageResponseError) {
            fault_ = true;
            return false;
        }
        top_.io_inputStageResponseReady = 1;
        cycle();
        top_.io_inputStageResponseReady = 0;
        top_.eval();
        ++staged_words_;
        return true;
    }

    DeviceRead read_private_output(std::uint32_t index) {
        if (top_.io_busy || top_.io_memoryPending || !top_.io_outputValid
            || !top_.io_outputValidationReady) {
            fault_ = true;
            return {false, 0U};
        }
        top_.io_outputValidationValid = 1;
        top_.io_outputValidationAddress = index;
        cycle();
        top_.io_outputValidationValid = 0;
        top_.eval();
        if (!top_.io_outputValidationResponseValid
            || top_.io_outputValidationResponseError) {
            fault_ = true;
            return {false, 0U};
        }
        const std::uint32_t value = top_.io_outputValidationReadData;
        top_.io_outputValidationResponseReady = 1;
        cycle();
        top_.io_outputValidationResponseReady = 0;
        top_.eval();
        return {true, value};
    }
};

}  // namespace raveil::graph_device

int main(int argc, char** argv) {
    Verilated::commandArgs(argc, argv);
#ifdef RAVEIL_DAG_RUNTIME
    const bool dag = argc >= 2 && std::string(argv[1]) == "--dag";
    const bool selected = argc >= 2 && std::string(argv[1]) == "--dag-selected";
    if ((!dag && !selected) || (dag && argc != 3 && argc != 4)
        || (selected && argc != 5 && argc != 6)) {
        std::cerr << "usage: VStaticStencilRegion --dag EVIDENCE_ROOT [TRACE_PATH]"
            " | --dag-selected EVIDENCE_ROOT GRAPH_ID SEED [TRACE_PATH]\n";
        return 2;
    }
#elif defined(RAVEIL_AFFINE_RUNTIME)
    const bool affine = argc >= 2 && std::string(argv[1]) == "--affine";
    if (affine && argc != 3 && argc != 4) {
        std::cerr << "usage: VStaticStencilRegion --affine EVIDENCE_ROOT [TRACE_PATH]\n";
        return 2;
    }
    if (!affine && argc != 2 && argc != 3) {
        std::cerr << "usage: VStaticStencilRegion EVIDENCE_ROOT [TRACE_PATH]\n";
        return 2;
    }
#else
    if (argc != 2 && argc != 3) {
        std::cerr << "usage: VStaticStencilRegion EVIDENCE_ROOT [TRACE_PATH]\n";
        return 2;
    }
#endif
    VStaticStencilRegion top;
    raveil::graph_device::VerilatorDeviceTransport device(top);
    std::ofstream trace;
    const int evidenceIndex =
#ifdef RAVEIL_DAG_RUNTIME
        2;
#elif defined(RAVEIL_AFFINE_RUNTIME)
        affine ? 2 : 1;
#else
        1;
#endif
    const int traceIndex = evidenceIndex + 1
#ifdef RAVEIL_DAG_RUNTIME
        + (selected ? 2 : 0)
#endif
        ;
    if (argc > traceIndex) {
        trace.open(argv[traceIndex], std::ios::out | std::ios::trunc);
        if (!trace) {
            std::cerr << "transaction trace could not be opened\n";
            return 2;
        }
        device.set_transaction_trace(&trace);
    }
    const std::filesystem::path evidence(argv[evidenceIndex]);
    std::uint32_t selected_seed = 0U;
#ifdef RAVEIL_DAG_RUNTIME
    if (selected && !parse_seed(argv[4], selected_seed)) {
        std::cerr << "selected seed must be a uint32 decimal\n";
        return 2;
    }
#endif
    const int result =
#ifdef RAVEIL_DAG_RUNTIME
        selected
            ? raveil::graph_device::run_selected_dag(
                device, device, device, evidence, argv[3],
                selected_seed, std::cout, std::cerr
            )
            : raveil::graph_device::run_dag(
                device, device, device, evidence, std::cout, std::cerr
            );
#elif defined(RAVEIL_AFFINE_RUNTIME)
        affine
            ? raveil::graph_device::run_affine(
                device, device, evidence, std::cout, std::cerr
            )
            : raveil::graph_device::run_mvp(
                device, evidence, std::cout, std::cerr
            );
#else
        raveil::graph_device::run_mvp(
            device, evidence, std::cout, std::cerr
        );
#endif
    top.final();
    return result;
}
