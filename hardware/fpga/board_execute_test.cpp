// Owned simulation adapter. Reuses the existing DAG runtime without changing it.
#include "VGraphDeviceBoardBridge.h"
#include "verilated.h"
#include "graph_device_abi_generated.h"
#include "graph_device_axi4lite_transport.h"
#include "graph_device_dag_runtime.h"
#include <cstdint>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>

namespace gd = raveil::graph_device;
static constexpr uint32_t Base = TEST_BASE;
[[noreturn]] static void fail(const char* message) {
  std::cerr << "board execution: " << message << '\n'; std::exit(1);
}
class BoardIo final : public gd::RegisterIo {
 public:
  BoardIo(VGraphDeviceBoardBridge& top, std::ostream& trace) : t(top), trace(trace) { reset(); }
  void reset() {
    t.s_axi_awvalid = t.s_axi_wvalid = t.s_axi_arvalid = 0;
    t.s_axi_bready = t.s_axi_rready = 0;
    t.s_axi_awaddr = t.s_axi_araddr = t.s_axi_wdata = t.s_axi_wstrb = 0;
    t.s_axi_awprot = t.s_axi_arprot = 0;
    t.aclk = 0; t.eval(); t.aresetn = 0; t.eval(); quiet(); tick(); quiet();
    t.aresetn = 1; t.eval(); quiet(); tick(); quiet(); tick();
    if (t.s_axi_bvalid || t.s_axi_rvalid) fail("stale response after reset");
    trace << "reset\n";
  }
  bool write32(uint32_t address, uint32_t value) override {
    check(address); t.s_axi_awaddr = Base + address;
    t.s_axi_wdata = value; t.s_axi_wstrb = 15;
    bool aw = false, w = false;
    for (unsigned n = 0; n < 256; ++n) {
      // Alternate AW-first, W-first and concurrent requests; capture separately.
      t.s_axi_awvalid = !aw && (sequence % 3 != 1 || n > 0);
      t.s_axi_wvalid = !w && (sequence % 3 != 0 || n > 0);
      t.aclk = 0; t.eval();
      bool af = t.s_axi_awvalid && t.s_axi_awready;
      bool wf = t.s_axi_wvalid && t.s_axi_wready;
      t.aclk = 1; t.eval(); aw |= af; w |= wf;
      if (aw && w) break;
    }
    t.s_axi_awvalid = t.s_axi_wvalid = 0;
    if (!aw || !w) fail("write handshake timeout");
    for (unsigned n = 0; n < 256; ++n) {
      t.aclk = 0; t.eval();
      if (t.s_axi_bvalid) {
        const uint32_t response = t.s_axi_bresp;
        const unsigned hold = 1 + sequence % 3;
        for (unsigned i = 0; i < hold; ++i) {
          tick();
          if (!t.s_axi_bvalid || t.s_axi_bresp != response) fail("held B changed");
        }
        t.s_axi_bready = 1; tick(); t.s_axi_bready = 0;
        record("write", address, value, response, hold); return response == 0;
      }
      t.aclk = 1; t.eval();
    }
    fail("write response timeout");
  }
  gd::DeviceRead read32(uint32_t address) override {
    check(address); t.s_axi_araddr = Base + address; t.s_axi_arvalid = 1;
    bool accepted = false;
    for (unsigned n = 0; n < 256; ++n) {
      t.aclk = 0; t.eval(); const bool fire = t.s_axi_arready;
      t.aclk = 1; t.eval(); if (fire) { accepted = true; break; }
    }
    t.s_axi_arvalid = 0; if (!accepted) fail("read handshake timeout");
    for (unsigned n = 0; n < 256; ++n) {
      t.aclk = 0; t.eval();
      if (t.s_axi_rvalid) {
        const uint32_t data = t.s_axi_rdata, response = t.s_axi_rresp;
        const unsigned hold = 1 + sequence % 3;
        for (unsigned i = 0; i < hold; ++i) {
          tick();
          if (!t.s_axi_rvalid || t.s_axi_rresp != response || t.s_axi_rdata != data) fail("held R changed");
        }
        t.s_axi_rready = 1; tick(); t.s_axi_rready = 0;
        record("read", address, data, response, hold); return {response == 0, data};
      }
      t.aclk = 1; t.eval();
    }
    fail("read response timeout");
  }
 private:
  VGraphDeviceBoardBridge& t; std::ostream& trace; unsigned sequence = 0;
  void tick() { t.aclk = 0; t.eval(); t.aclk = 1; t.eval(); }
  void quiet() {
    if (t.s_axi_awready || t.s_axi_wready || t.s_axi_arready || t.s_axi_bvalid || t.s_axi_rvalid) fail("reset handshake leak");
  }
  void check(uint32_t address) { if (address >= 0x4000 || (address & 3)) fail("relative address outside window"); }
  void record(const char* op, uint32_t address, uint32_t data, uint32_t response, unsigned hold) {
    trace << sequence++ << ' ' << op << ' ' << address << ' ' << (Base + address)
          << ' ' << data << ' ' << response << ' ' << hold << '\n';
    if (!trace) fail("trace write");
  }
};

int main(int argc, char** argv) {
  if (argc != 2) fail("expected output directory");
  Verilated::commandArgs(argc, argv);
  const std::filesystem::path root(argv[1]);
  std::ofstream trace(root / "transactions.log");
  if (!trace) fail("trace open");
  VGraphDeviceBoardBridge top; BoardIo io(top, trace);
  gd::Axi4LiteTransport transport(io, 0, 0x2000, 0x3000);
  if (gd::run_dag(transport, transport, transport, root / "matrix", std::cout, std::cerr)) fail("DAG matrix");
  // Interrupt a live factory-default run with the physical reset pin.
  if (!transport.write_word(gd::abi::kRegControl, gd::abi::kControlReset)) fail("reset setup");
  std::ifstream input(root / "matrix/inputs/seed-1.bin", std::ios::binary);
  for (unsigned index = 0; index < 324; ++index) {
    unsigned char bytes[4]; input.read(reinterpret_cast<char*>(bytes), 4);
    if (!input) fail("input read");
    uint32_t value = uint32_t(bytes[0]) | uint32_t(bytes[1]) << 8 | uint32_t(bytes[2]) << 16 | uint32_t(bytes[3]) << 24;
    if (!transport.write_word(gd::abi::kInputBase + index, value)) fail("reset input stage");
  }
  if (!transport.write_word(gd::abi::kRegControl, gd::abi::kControlStart)) fail("reset start");
  auto busy = transport.read_word(gd::abi::kRegStatus);
  if (!busy.ok || !(busy.value & gd::abi::kStatusBusy)) fail("external reset must interrupt BUSY");
  io.reset();
  auto cleared = transport.read_word(gd::abi::kRegStatus);
  if (!cleared.ok || cleared.value != 0 || transport.read_word(gd::abi::kOutputBase).ok) fail("reset published stale output");
  std::cout << "BoardReset-V1 busy=1 cleared=1 stale_output=denied\n";
  if (gd::run_selected_dag(transport, transport, transport, root / "recovery", "five-point", 1, std::cout, std::cerr)) fail("external reset recovery");
  top.final();
  std::cout << "BoardExecute-V1 status=OK model_instances=1 matrix_completed=4 cancelled=1 recovery_completed=1 evidence=rtl-simulation-functional performance=not-measured\n";
}
