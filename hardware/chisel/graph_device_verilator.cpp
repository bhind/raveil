#include "VStaticStencilRegion.h"
#include "verilated.h"

#include "graph_device_abi_generated.h"
#include "graph_device_runtime.h"

#include <array>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <ostream>

namespace raveil::graph_device {

class VerilatorDeviceTransport final : public DeviceTransport {
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
            fault_ = !rtl_configuration_matches_;
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
    if (argc != 2 && argc != 3) {
        std::cerr << "usage: VStaticStencilRegion EVIDENCE_ROOT [TRACE_PATH]\n";
        return 2;
    }
    VStaticStencilRegion top;
    raveil::graph_device::VerilatorDeviceTransport device(top);
    std::ofstream trace;
    if (argc == 3) {
        trace.open(argv[2], std::ios::out | std::ios::trunc);
        if (!trace) {
            std::cerr << "transaction trace could not be opened\n";
            return 2;
        }
        device.set_transaction_trace(&trace);
    }
    const int result = raveil::graph_device::run_mvp(
        device, std::filesystem::path(argv[1]), std::cout, std::cerr
    );
    top.final();
    return result;
}
