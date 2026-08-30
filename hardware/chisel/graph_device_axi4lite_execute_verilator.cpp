#include "VGraphDeviceAxi4LiteTop.h"
#include "verilated.h"

#include "graph_device_abi_generated.h"
#include "graph_device_axi4lite_aperture_generated.h"
#include "graph_device_axi4lite_execute_vectors.h"

#include <array>
#include <cstdint>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>

namespace {
namespace abi = raveil::graph_device::abi;
namespace vectors = raveil::graph_device::axi_execute_vectors;
constexpr std::uint32_t Okay = 0;
constexpr std::uint32_t SlvErr = 2;
constexpr std::uint32_t DecErr = 3;
std::ofstream transcript;
std::uint64_t transaction_sequence = 0;

[[noreturn]] void fail(const char* message) {
    std::cerr << "AXI4LITE execute test failed: " << message << '\n';
    std::exit(1);
}

void tick(VGraphDeviceAxi4LiteTop& top) {
    top.aclk = 0;
    top.eval();
    top.aclk = 1;
    top.eval();
}

void idle(VGraphDeviceAxi4LiteTop& top) {
    top.awvalid = top.wvalid = top.arvalid = 0;
    top.bready = top.rready = 0;
    top.awaddr = top.wdata = top.wstrb = top.araddr = 0;
}

void reset(VGraphDeviceAxi4LiteTop& top) {
    idle(top);
    top.aresetn = 0;
    tick(top);
    top.aresetn = 1;
    tick(top);
}

void trace_write(
    std::uint32_t address,
    std::uint32_t data,
    std::uint32_t strobe,
    std::uint32_t response,
    unsigned held
) {
    transcript << "AXI4LITE-TRACE-V1 seq=" << transaction_sequence++
               << " op=write address=0x" << std::hex << std::setw(8)
               << std::setfill('0') << address << " data=0x" << std::setw(8)
               << data << " strobe=0x" << strobe << std::dec
               << " response=" << response << " held_b=" << held << '\n';
    if (!transcript) fail("AXI transcript write");
}

void trace_read(
    std::uint32_t address,
    std::uint32_t data,
    std::uint32_t response,
    unsigned held
) {
    transcript << "AXI4LITE-TRACE-V1 seq=" << transaction_sequence++
               << " op=read address=0x" << std::hex << std::setw(8)
               << std::setfill('0') << address << " data=0x" << std::setw(8)
               << data << std::dec << " response=" << response
               << " held_r=" << held << '\n';
    if (!transcript) fail("AXI transcript write");
}

void write(
    VGraphDeviceAxi4LiteTop& top,
    std::uint32_t address,
    std::uint32_t data,
    std::uint32_t expected = Okay,
    std::uint32_t strobe = 0xf,
    unsigned hold_response = 0
) {
    top.awaddr = address;
    top.awvalid = 1;
    top.wdata = data;
    top.wstrb = strobe;
    top.wvalid = 1;
    bool accepted = false;
    for (unsigned cycle = 0; cycle != 64; ++cycle) {
        top.aclk = 0;
        top.eval();
        const bool fire = top.awready && top.wready;
        top.aclk = 1;
        top.eval();
        if (fire) {
            accepted = true;
            break;
        }
    }
    if (!accepted) fail("write address/data admission timeout");
    top.awvalid = top.wvalid = 0;
    for (unsigned cycle = 0; cycle != 64; ++cycle) {
        top.aclk = 0;
        top.eval();
        if (top.bvalid) {
            if (top.bresp != expected) fail("write response");
            for (unsigned held = 0; held != hold_response; ++held) {
                if (top.awready || top.wready || top.arready) fail("held B admitted request");
                top.aclk = 1;
                top.eval();
                top.aclk = 0;
                top.eval();
                if (!top.bvalid) fail("B response was not retained");
            }
            top.bready = 1;
            top.aclk = 1;
            top.eval();
            top.bready = 0;
            trace_write(address, data, strobe, top.bresp, hold_response);
            return;
        }
        top.aclk = 1;
        top.eval();
    }
    fail("write response timeout");
}

std::uint32_t read(
    VGraphDeviceAxi4LiteTop& top,
    std::uint32_t address,
    std::uint32_t expected = Okay,
    unsigned hold_response = 0
) {
    top.araddr = address;
    top.arvalid = 1;
    bool accepted = false;
    for (unsigned cycle = 0; cycle != 64; ++cycle) {
        top.aclk = 0;
        top.eval();
        const bool fire = top.arready;
        top.aclk = 1;
        top.eval();
        if (fire) {
            accepted = true;
            break;
        }
    }
    if (!accepted) fail("read address admission timeout");
    top.arvalid = 0;
    for (unsigned cycle = 0; cycle != 64; ++cycle) {
        top.aclk = 0;
        top.eval();
        if (top.rvalid) {
            if (top.rresp != expected) fail("read response");
            const auto value = static_cast<std::uint32_t>(top.rdata);
            const auto response = static_cast<std::uint32_t>(top.rresp);
            for (unsigned held = 0; held != hold_response; ++held) {
                if (top.awready || top.wready || top.arready) fail("held R admitted request");
                top.aclk = 1;
                top.eval();
                top.aclk = 0;
                top.eval();
                if (!top.rvalid || top.rresp != response || top.rdata != value) {
                    fail("R response was not retained");
                }
            }
            top.rready = 1;
            top.aclk = 1;
            top.eval();
            top.rready = 0;
            trace_read(address, value, response, hold_response);
            return value;
        }
        top.aclk = 1;
        top.eval();
    }
    fail("read response timeout");
}

constexpr std::uint32_t address(std::uint32_t word) {
    return RAVEIL_AXI_EXEC_BASE + 4 * word;
}

void stage(VGraphDeviceAxi4LiteTop& top, const std::array<std::uint32_t, 324>& input) {
    for (unsigned index = 0; index != input.size(); ++index) {
        write(top, address(abi::kInputBase + index), input[index]);
    }
}

std::uint32_t poll_terminal(VGraphDeviceAxi4LiteTop& top) {
    for (unsigned poll = 0; poll != abi::kMaxStatusPolls; ++poll) {
        const auto status = read(top, address(abi::kRegStatus));
        if ((status & abi::kStatusBusy) == 0 &&
            (status & (abi::kStatusCompleted | abi::kStatusCancelled)) != 0) {
            return status;
        }
    }
    fail("terminal status timeout");
}

void save_output(
    const std::filesystem::path& path,
    const std::array<std::uint32_t, 256>& output
) {
    std::ofstream stream(path, std::ios::binary | std::ios::trunc);
    if (!stream) fail("output file open");
    for (const auto word : output) {
        const std::array<unsigned char, 4> bytes = {
            static_cast<unsigned char>(word),
            static_cast<unsigned char>(word >> 8),
            static_cast<unsigned char>(word >> 16),
            static_cast<unsigned char>(word >> 24),
        };
        stream.write(reinterpret_cast<const char*>(bytes.data()), bytes.size());
    }
    if (!stream) fail("output file write");
}

void run_complete(
    VGraphDeviceAxi4LiteTop& top,
    const std::array<std::uint32_t, 324>& input,
    const std::array<std::uint32_t, 256>& oracle,
    std::uint64_t checksum,
    const std::filesystem::path& output_path,
    bool hold_start = false
) {
    stage(top, input);
    write(top, address(abi::kRegControl), abi::kControlStart, Okay, 0xf,
          hold_start ? 4 : 0);
    const auto status = poll_terminal(top);
    if ((status & (abi::kStatusCompleted | abi::kStatusOutputValid)) !=
            (abi::kStatusCompleted | abi::kStatusOutputValid) ||
        (status & (abi::kStatusBusy | abi::kStatusCancelled | abi::kStatusFault)) != 0) {
        fail("complete terminal status");
    }
    const auto checksum_low = read(top, address(abi::kRegChecksumLow));
    const auto checksum_high = read(top, address(abi::kRegChecksumHigh));
    if ((static_cast<std::uint64_t>(checksum_high) << 32 | checksum_low) != checksum) {
        fail("checksum mismatch");
    }
    std::array<std::uint32_t, 256> output{};
    for (unsigned index = 0; index != output.size(); ++index) {
        output[index] = read(top, address(abi::kOutputBase + index), Okay,
                             hold_start && index == 0 ? 4 : 0);
        if (output[index] != oracle[index]) fail("oracle mismatch");
    }
    save_output(output_path, output);
}
}  // namespace

int main(int argc, char** argv) {
    if (argc != 2) fail("usage requires evidence directory");
    Verilated::commandArgs(argc, argv);
    const std::filesystem::path evidence = argv[1];
    transcript.open(evidence / "axi-transcript.log", std::ios::out | std::ios::trunc);
    if (!transcript) fail("AXI transcript open");
    VGraphDeviceAxi4LiteTop top;
    reset(top);

    // Transport and semantic negatives must not create execution authority.
    write(top, address(abi::kInputBase), vectors::kSeed1Input[0], SlvErr, 1);
    write(top, address(abi::kInputBase) + 2, vectors::kSeed1Input[0], DecErr);
    write(top, 0x4000, 0, DecErr);
    read(top, address(abi::kInputBase), SlvErr);
    write(top, address(abi::kOutputBase), 0, SlvErr);
    read(top, address(abi::kRegDescriptorBase), SlvErr);
    write(top, address(abi::kInputBase + 1), vectors::kSeed1Input[1], SlvErr);
    read(top, address(abi::kOutputBase), SlvErr);
    write(top, address(abi::kRegControl), abi::kControlStart, SlvErr);
    write(top, address(abi::kRegControl), abi::kControlCancel, SlvErr);

    write(top, address(abi::kRegControl), abi::kControlReset);
    run_complete(top, vectors::kSeed1Input, vectors::kSeed1Oracle,
                 vectors::kSeed1Checksum, evidence / "output-seed-1.bin", true);

    write(top, address(abi::kRegControl), abi::kControlReset);
    stage(top, vectors::kSeed3Input);
    write(top, address(abi::kRegControl), abi::kControlStart);
    for (unsigned poll = 0; poll != 17; ++poll) {
        const auto status = read(top, address(abi::kRegStatus));
        if ((status & abi::kStatusBusy) == 0 ||
            (status & (abi::kStatusCompleted | abi::kStatusCancelled | abi::kStatusFault)) != 0) {
            fail("cancel precondition");
        }
    }
    write(top, address(abi::kInputBase), vectors::kSeed3Input[0], SlvErr);
    read(top, address(abi::kOutputBase), SlvErr);
    // Hold the accepted cancel B long enough for the core to finish. Cancel is
    // applied only after B acceptance and must still revoke the now-ready output.
    write(top, address(abi::kRegControl), abi::kControlCancel, Okay, 0xf, 4096);
    const auto cancelled = poll_terminal(top);
    if ((cancelled & abi::kStatusCancelled) == 0 ||
        (cancelled & (abi::kStatusBusy | abi::kStatusCompleted |
                      abi::kStatusOutputValid | abi::kStatusFault)) != 0) {
        fail("cancel terminal status");
    }
    read(top, address(abi::kOutputBase), SlvErr);

    write(top, address(abi::kRegControl), abi::kControlReset);
    run_complete(top, vectors::kSeed2Input, vectors::kSeed2Oracle,
                 vectors::kSeed2Checksum, evidence / "output-seed-2.bin");

    std::cout << "GraphDevice-AXI4LITE-EXECUTE-V1 status=OK inputs=324 "
                 "outputs=256 oracle=match cancel=denied-output restart=match "
                 "evidence=rtl-simulation-functional performance=not-measured\n";
    return 0;
}
