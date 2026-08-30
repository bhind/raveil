#include "VGraphDeviceAxi4LiteTop.h"
#include "verilated.h"

#include "graph_device_affine_generated.h"
#include "graph_device_axi4lite_aperture_generated.h"
#include "graph_device_dag_generated.h"

#include <cstdint>
#include <cstdlib>
#include <iostream>

namespace {
constexpr std::uint32_t Okay = 0;
constexpr std::uint32_t SlvErr = 2;
constexpr std::uint32_t DecErr = 3;
constexpr std::uint32_t ConfigControl = RAVEIL_AXI_CONFIG_BASE + 0x10;
constexpr std::uint32_t ConfigStatus = RAVEIL_AXI_CONFIG_BASE + 0x14;
constexpr std::uint32_t ConfigCount = RAVEIL_AXI_CONFIG_BASE + 0x18;
constexpr std::uint32_t ConfigDigest = RAVEIL_AXI_CONFIG_BASE + 0x40;
constexpr std::uint32_t ConfigPayload = RAVEIL_AXI_CONFIG_BASE + 0x400;
constexpr std::uint32_t ProgramControl = RAVEIL_AXI_PROGRAM_BASE + 0x10;
constexpr std::uint32_t ProgramStatus = RAVEIL_AXI_PROGRAM_BASE + 0x14;
constexpr std::uint32_t ProgramCount = RAVEIL_AXI_PROGRAM_BASE + 0x18;
constexpr std::uint32_t ProgramDigest = RAVEIL_AXI_PROGRAM_BASE + 0x40;
constexpr std::uint32_t ProgramPayload = RAVEIL_AXI_PROGRAM_BASE + 0x400;

[[noreturn]] void fail(const char* message) {
    std::cerr << "AXI4LITE install test failed: " << message << '\n';
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

std::uint32_t read(VGraphDeviceAxi4LiteTop& top, std::uint32_t address) {
    top.araddr = address;
    top.arvalid = 1;
    tick(top);
    top.arvalid = 0;
    for (unsigned cycle = 0; cycle != 8; ++cycle) {
        if (top.rvalid) {
            if (top.rresp != Okay) fail("read response");
            const auto value = static_cast<std::uint32_t>(top.rdata);
            top.rready = 1;
            tick(top);
            top.rready = 0;
            return value;
        }
        tick(top);
    }
    fail("read timeout");
}

void write(
    VGraphDeviceAxi4LiteTop& top,
    std::uint32_t address,
    std::uint32_t data,
    std::uint32_t strobe = 0xf,
    std::uint32_t expected = Okay
) {
    top.awaddr = address;
    top.awvalid = 1;
    top.wdata = data;
    top.wstrb = strobe;
    top.wvalid = 1;
    tick(top);
    top.awvalid = top.wvalid = 0;
    for (unsigned cycle = 0; cycle != 8; ++cycle) {
        if (top.bvalid) {
            if (top.bresp != expected) fail("write response");
            top.bready = 1;
            tick(top);
            top.bready = 0;
            tick(top);
            return;
        }
        tick(top);
    }
    fail("write timeout");
}

void hold_write_response(
    VGraphDeviceAxi4LiteTop& top,
    std::uint32_t address,
    std::uint32_t data
) {
    top.awaddr = address;
    top.awvalid = 1;
    top.wdata = data;
    top.wstrb = 0xf;
    top.wvalid = 1;
    tick(top);
    top.awvalid = top.wvalid = 0;
    for (unsigned cycle = 0; cycle != 8 && !top.bvalid; ++cycle) tick(top);
    if (!top.bvalid || top.bresp != Okay) fail("held write response");
    for (unsigned cycle = 0; cycle != 4; ++cycle) {
        if (top.awready || top.wready || top.arready) fail("response retention admission");
        tick(top);
        if (!top.bvalid) fail("write response was not retained");
    }
    top.bready = 1;
    tick(top);
    top.bready = 0;
    tick(top);
}

void complete_split_write(
    VGraphDeviceAxi4LiteTop& top,
    std::uint32_t address,
    std::uint32_t data
) {
    top.awaddr = address;
    top.awvalid = 1;
    tick(top);
    top.awvalid = 0;
    for (unsigned cycle = 0; cycle != 4; ++cycle) {
        if (top.arready || top.bvalid) fail("partial AW did not retain busy state");
        tick(top);
    }
    top.wdata = data;
    top.wstrb = 0xf;
    top.wvalid = 1;
    tick(top);
    top.wvalid = 0;
    for (unsigned cycle = 0; cycle != 8 && !top.bvalid; ++cycle) tick(top);
    if (!top.bvalid || top.bresp != Okay) fail("split write response");
    top.bready = 1;
    tick(top);
    top.bready = 0;
    tick(top);
}

void check_digest(
    VGraphDeviceAxi4LiteTop& top,
    std::uint32_t base,
    const std::uint32_t* expected
) {
    for (unsigned index = 0; index != 8; ++index) {
        if (read(top, base + 4 * index) != expected[index]) fail("digest mismatch");
    }
}
}  // namespace

int main(int argc, char** argv) {
    Verilated::commandArgs(argc, argv);
    VGraphDeviceAxi4LiteTop top;
    reset(top);

    const auto& baseline = raveil::graph_device::affine_generated::kProfiles[0];
    const auto& compact = raveil::graph_device::affine_generated::kProfiles[1];
    const auto& program = raveil::graph_device::dag_generated::kGraphs[1];
    if (read(top, ConfigStatus) != 2 || read(top, ConfigCount) != 16) fail("factory config status");
    if (read(top, ProgramStatus) != 2 || read(top, ProgramCount) != 0) fail("factory program status");
    check_digest(top, ConfigDigest, baseline.digest.data());

    // Transport rejection cannot mutate the installer.
    write(top, ConfigControl, 1, 1, SlvErr);
    write(top, ConfigControl + 2, 1, 0xf, DecErr);
    write(top, ConfigStatus, 1, 0xf, SlvErr);
    write(top, 0x4000, 1, 0xf, DecErr);
    write(top, ConfigControl, 3, 0xf, SlvErr);
    write(top, ConfigPayload + 16 * 4, 1, 0xf, SlvErr);
    write(top, ProgramPayload + 32 * 4, 1, 0xf, SlvErr);
    if (read(top, ConfigStatus) != 2) fail("partial write mutated config");

    // An accepted installer mutation retains B and blocks all admission until
    // the owner accepts the response. Only then may the queued clear pulse.
    complete_split_write(top, ConfigControl, 1);
    if (read(top, ConfigStatus) != 1 || read(top, ConfigCount) != 0) fail("config clear");
    for (unsigned index = 0; index != compact.payload.size(); ++index) {
        write(top, ConfigPayload + 4 * index, compact.payload[index]);
        if (read(top, ConfigCount) != index + 1) fail("config count");
    }
    write(top, ConfigControl, 2);
    if (read(top, ConfigStatus) != 2 || read(top, ConfigCount) != 16) fail("config commit");
    check_digest(top, ConfigDigest, compact.digest.data());

    hold_write_response(top, ProgramControl, 1);
    if (read(top, ProgramStatus) != 0 || read(top, ProgramCount) != 0) fail("program clear");
    for (unsigned index = 0; index != program.payload.size(); ++index) {
        write(top, ProgramPayload + 4 * index, program.payload[index]);
        if (read(top, ProgramCount) != index + 1) fail("program count");
    }
    write(top, ProgramControl, 2);
    if (read(top, ProgramStatus) != 2 || read(top, ProgramCount) != 32) fail("program commit");
    check_digest(top, ProgramDigest, program.payload.data() + 4);

    // Semantically wrong order reaches the owned installer and fails closed.
    write(top, ProgramControl, 1);
    write(top, ProgramPayload + 4, program.payload[1]);
    if (read(top, ProgramStatus) != 4) fail("wrong-order program did not fault");

    // Duplicate and premature-commit streams fail without becoming installed.
    write(top, RAVEIL_AXI_EXEC_BASE + 0x10, 4);
    write(top, ConfigControl, 1);
    write(top, ConfigPayload, compact.payload[0]);
    write(top, ConfigPayload, compact.payload[0]);
    if ((read(top, ConfigStatus) & 4) == 0 || read(top, ConfigCount) != 1) fail("duplicate config did not fault");
    write(top, RAVEIL_AXI_EXEC_BASE + 0x10, 4);
    write(top, ProgramControl, 1);
    write(top, ProgramControl, 2);
    if (read(top, ProgramStatus) != 4 || read(top, ProgramCount) != 0) fail("premature program commit did not fault");

    // Payload bytes sent through the other namespace cannot affect config.
    write(top, RAVEIL_AXI_EXEC_BASE + 0x10, 4);
    write(top, ProgramControl, 1);
    write(top, ProgramPayload, compact.payload[0]);
    if (read(top, ProgramStatus) != 1 || read(top, ProgramCount) != 1) fail("program namespace admission");
    if (read(top, ConfigStatus) != 2 || read(top, ConfigCount) != 16) fail("cross-namespace config mutation");
    check_digest(top, ConfigDigest, baseline.digest.data());

    // The existing core reset restores both factory installations.
    write(top, RAVEIL_AXI_EXEC_BASE + 0x10, 4);
    if (read(top, ConfigStatus) != 2 || read(top, ConfigCount) != 16) fail("config reset restore");
    if (read(top, ProgramStatus) != 2 || read(top, ProgramCount) != 0) fail("program reset restore");
    check_digest(top, ConfigDigest, baseline.digest.data());

    std::cout << "GraphDevice-AXI4LITE-INSTALL-V1 status=OK "
                 "evidence=rtl-simulation-functional performance=not-measured\n";
    return 0;
}
