#include "VGraphDeviceAxi4LiteTop.h"
#include "verilated.h"

#include "graph_device_axi4lite_aperture_generated.h"
#include "graph_device_runtime.h"
#include "graph_device_affine_runtime.h"
#include "graph_device_dag_runtime.h"

#include <cstdint>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>

namespace {
constexpr std::uint32_t kOkay = 0;
[[noreturn]] void fail(const char* message) { std::cerr << "AXI4-Lite request bridge: " << message << '\n'; std::exit(1); }

// This bridge deliberately contains no Graph selection logic.  It maps the
// pre-existing transport-neutral runtime interfaces onto the three already
// specified AXI4-Lite apertures and records every completed transaction.
class AxiBridge final : public raveil::graph_device::DeviceTransport,
                        public raveil::graph_device::AffineInstallTransport,
                        public raveil::graph_device::ProgramInstallTransport {
 public:
  AxiBridge(VGraphDeviceAxi4LiteTop& top, std::ostream& trace) : top_(top), trace_(trace) {
    idle(); top_.aresetn = 0; tick(); top_.aresetn = 1; tick();
  }
  raveil::graph_device::DeviceRead read_word(std::uint32_t word) override { return read(RAVEIL_AXI_EXEC_BASE + 4U * word); }
  bool write_word(std::uint32_t word, std::uint32_t value) override { return write(RAVEIL_AXI_EXEC_BASE + 4U * word, value); }
  raveil::graph_device::DeviceRead read_install_word(std::uint32_t word) override { return read(RAVEIL_AXI_CONFIG_BASE + 4U * word); }
  bool write_install_word(std::uint32_t word, std::uint32_t value) override { return write(RAVEIL_AXI_CONFIG_BASE + 4U * word, value); }
  raveil::graph_device::DeviceRead read_program_word(std::uint32_t word) override { return read(RAVEIL_AXI_PROGRAM_BASE + 4U * word); }
  bool write_program_word(std::uint32_t word, std::uint32_t value) override { return write(RAVEIL_AXI_PROGRAM_BASE + 4U * word, value); }
 private:
  VGraphDeviceAxi4LiteTop& top_; std::ostream& trace_; std::uint64_t sequence_ = 0;
  void idle() { top_.awvalid = top_.wvalid = top_.arvalid = 0; top_.bready = top_.rready = 0; top_.awaddr = top_.wdata = top_.wstrb = top_.araddr = 0; }
  void tick() { top_.aclk = 0; top_.eval(); top_.aclk = 1; top_.eval(); }
  void trace_write(std::uint32_t a, std::uint32_t d, std::uint32_t r) { trace_ << "AXI4LITE-TRACE-V1 seq=" << sequence_++ << " op=write address=0x" << std::hex << std::setw(8) << std::setfill('0') << a << " data=0x" << std::setw(8) << d << std::dec << " strobe=0xf response=" << r << " held_b=0\n"; }
  void trace_read(std::uint32_t a, std::uint32_t d, std::uint32_t r) { trace_ << "AXI4LITE-TRACE-V1 seq=" << sequence_++ << " op=read address=0x" << std::hex << std::setw(8) << std::setfill('0') << a << " data=0x" << std::setw(8) << d << std::dec << " response=" << r << " held_r=0\n"; }
  bool write(std::uint32_t address, std::uint32_t data) {
    top_.awaddr = address; top_.wdata = data; top_.wstrb = 0xf; top_.awvalid = top_.wvalid = 1; bool accepted = false;
    for (unsigned n = 0; n != 256; ++n) { top_.aclk = 0; top_.eval(); const bool fire = top_.awready && top_.wready; top_.aclk = 1; top_.eval(); if (fire) { accepted = true; break; } }
    top_.awvalid = top_.wvalid = 0; if (!accepted) fail("write admission timeout");
    for (unsigned n = 0; n != 256; ++n) { top_.aclk = 0; top_.eval(); if (top_.bvalid) { const auto r = static_cast<std::uint32_t>(top_.bresp); top_.bready = 1; top_.aclk = 1; top_.eval(); top_.bready = 0; trace_write(address, data, r); return r == kOkay; } top_.aclk = 1; top_.eval(); }
    fail("write response timeout");
  }
  raveil::graph_device::DeviceRead read(std::uint32_t address) {
    top_.araddr = address; top_.arvalid = 1; bool accepted = false;
    for (unsigned n = 0; n != 256; ++n) { top_.aclk = 0; top_.eval(); const bool fire = top_.arready; top_.aclk = 1; top_.eval(); if (fire) { accepted = true; break; } }
    top_.arvalid = 0; if (!accepted) fail("read admission timeout");
    for (unsigned n = 0; n != 256; ++n) { top_.aclk = 0; top_.eval(); if (top_.rvalid) { const auto r = static_cast<std::uint32_t>(top_.rresp); const auto d = static_cast<std::uint32_t>(top_.rdata); top_.rready = 1; top_.aclk = 1; top_.eval(); top_.rready = 0; trace_read(address, d, r); return {r == kOkay, d}; } top_.aclk = 1; top_.eval(); }
    fail("read response timeout");
  }
};
}  // namespace

int main(int argc, char** argv) {
  if (argc != 4) fail("usage: VGraphDeviceAxi4LiteTop EVIDENCE_ROOT GRAPH_ID SEED");
  char* end = nullptr; const unsigned long parsed = std::strtoul(argv[3], &end, 10);
  if (end == argv[3] || *end != '\0' || parsed > 0xffffffffUL) fail("seed must be uint32");
  Verilated::commandArgs(argc, argv);
  const std::filesystem::path evidence(argv[1]); std::ofstream trace(evidence / "axi-transcript.log", std::ios::trunc);
  if (!trace) fail("transcript open");
  VGraphDeviceAxi4LiteTop top; AxiBridge bridge(top, trace);
  const int result = raveil::graph_device::run_selected_dag(bridge, bridge, bridge, evidence, argv[2], static_cast<std::uint32_t>(parsed), std::cout, std::cerr);
  top.final(); return result;
}
