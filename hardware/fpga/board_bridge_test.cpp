#include "VGraphDeviceBoardBridge.h"
#include "verilated.h"
#include <cstdint>
#include <cstdlib>
#include <iostream>

static constexpr uint32_t BASE = TEST_BASE;
static constexpr uint32_t OKAY = 0, SLVERR = 2, DECERR = 3;
static void fail(const char* what) { std::cerr << "AXI4LITE test failed: " << what << "\n"; std::exit(1); }
static void tick(VGraphDeviceBoardBridge& t) { t.aclk = 0; t.eval(); t.aclk = 1; t.eval(); }
static void idle(VGraphDeviceBoardBridge& t) {
  t.s_axi_awvalid = t.s_axi_wvalid = t.s_axi_arvalid = t.s_axi_bready = t.s_axi_rready = 0;
  t.s_axi_awaddr = t.s_axi_wdata = t.s_axi_wstrb = t.s_axi_araddr = 0;
  t.s_axi_awprot = t.s_axi_arprot = 0;
}
static void quiet(VGraphDeviceBoardBridge& t) {
  if (t.s_axi_awready || t.s_axi_wready || t.s_axi_arready || t.s_axi_bvalid || t.s_axi_rvalid)
    fail("bus active during reset/release");
}
static void reset(VGraphDeviceBoardBridge& t) {
  // Assert between clock edges: externally visible responses/ready must vanish.
  t.aclk = 0; t.eval(); t.aresetn = 0; t.eval(); quiet(t);
  idle(t); tick(t); quiet(t); t.aresetn = 1; t.eval(); quiet(t);
  tick(t); quiet(t); tick(t);
  if (t.s_axi_bvalid || t.s_axi_rvalid) fail("stale response survived reset");
}
static void wait_b(VGraphDeviceBoardBridge& t, uint32_t expected) {
  for (int n = 0; n != 8; ++n) { if (t.s_axi_bvalid) { if (t.s_axi_bresp != expected) fail("BRESP"); const auto held = t.s_axi_bresp; tick(t); if (!t.s_axi_bvalid || t.s_axi_bresp != held) fail("B stability"); t.s_axi_bready = 1; tick(t); t.s_axi_bready = 0; return; } tick(t); } fail("B timeout");
}
static void write(VGraphDeviceBoardBridge& t, uint32_t address, uint32_t data, uint32_t strb, int mode, uint32_t response) {
  if (mode == 0 || mode == 2) { t.s_axi_awaddr = BASE + address; t.s_axi_awvalid = 1; }
  if (mode == 1 || mode == 2) { t.s_axi_wdata = data; t.s_axi_wstrb = strb; t.s_axi_wvalid = 1; }
  tick(t);
  if (mode == 0) { t.s_axi_awvalid = 0; t.s_axi_wdata = data; t.s_axi_wstrb = strb; t.s_axi_wvalid = 1; tick(t); }
  if (mode == 1) { t.s_axi_wvalid = 0; t.s_axi_awaddr = BASE + address; t.s_axi_awvalid = 1; tick(t); }
  t.s_axi_awvalid = t.s_axi_wvalid = 0; tick(t); wait_b(t, response);
}
static void read(VGraphDeviceBoardBridge& t, uint32_t address, uint32_t response, uint32_t data = 0) {
  t.s_axi_araddr = BASE + address; t.s_axi_arvalid = 1; tick(t); t.s_axi_arvalid = 0;
  for (int n = 0; n != 8; ++n) { if (t.s_axi_rvalid) { if (t.s_axi_rresp != response || (response == OKAY && t.s_axi_rdata != data)) { std::cerr << "read address=0x" << std::hex << address << " expected resp=" << response << " data=" << data << " got resp=" << uint32_t(t.s_axi_rresp) << " data=" << t.s_axi_rdata << "\n"; fail("R response/data"); } const uint32_t heldData = t.s_axi_rdata; const uint32_t heldResp = t.s_axi_rresp; tick(t); if (!t.s_axi_rvalid || t.s_axi_rdata != heldData || t.s_axi_rresp != heldResp) fail("R stability"); t.s_axi_rready = 1; tick(t); t.s_axi_rready = 0; return; } tick(t); } fail("R timeout");
}
int main(int argc, char** argv) {
  Verilated::commandArgs(argc, argv); VGraphDeviceBoardBridge top; reset(top);
  // All S01 identity/version/status/count words, each aperture separately.
  read(top, 0x0000, OKAY, 0x52560101); read(top, 0x0004, OKAY, 1); read(top, 0x0014, OKAY, 0); read(top, 0x0018, OKAY, 324); read(top, 0x001c, OKAY, 256);
  read(top, 0x2000, OKAY, 0x52564901); read(top, 0x2004, OKAY, 1); read(top, 0x2014, OKAY, 2); read(top, 0x2018, OKAY, 16);
  read(top, 0x3000, OKAY, 0x52565001); read(top, 0x3004, OKAY, 1); read(top, 0x3014, OKAY, 2); read(top, 0x3018, OKAY, 0);
  // AW-first, W-first and same-cycle capture; all non-reset writes fail closed.
  write(top, 0x0014, 0, 0xf, 0, SLVERR); write(top, 0x0014, 0, 0xf, 1, SLVERR); write(top, 0x0014, 0, 0xf, 2, SLVERR);
  // Decoded holes/RO/partial write are SLVERR; unaligned/outside are DECERR.
  read(top, 0x0008, SLVERR); read(top, 0x2008, SLVERR); read(top, 0x3008, SLVERR); read(top, 1, DECERR); read(top, 0x4000, DECERR);
  write(top, 0x0000, 0, 0xf, 2, SLVERR); write(top, 0x2000, 0, 0xf, 2, SLVERR); write(top, 0x3000, 0, 0xf, 2, SLVERR); write(top, 0x0010, 4, 1, 2, SLVERR); write(top, 1, 0, 0xf, 2, DECERR); write(top, 0x4000, 0, 0xf, 2, DECERR);
  // Full address decode, not truncation: lower/upper boundaries and high aliases.
  read(top, 0x3ffc, SLVERR); read(top, 0x3fff, DECERR); read(top, uint32_t(-4), DECERR);
  read(top, 0x40000000, DECERR);
  write(top, 0x40000010, 4, 0xf, 0, DECERR);
  write(top, 0x40000010, 4, 0xf, 1, DECERR);
  read(top, 0, OKAY, 0x52560101);
  // VALIDs held through release cannot be accepted before the third edge.
  reset(top); top.aresetn = 0; top.eval(); quiet(top);
  top.s_axi_araddr = BASE; top.s_axi_arvalid = 1;
  top.aresetn = 1; top.eval(); quiet(top); tick(top); quiet(top); tick(top);
  if (top.s_axi_rvalid) fail("read accepted during reset release");
  tick(top); top.s_axi_arvalid = 0;
  if (!top.s_axi_rvalid || top.s_axi_rdata != 0x52560101) fail("held read lost after release");
  reset(top);
  // ARESETn clears partial AW/W, held R, and held B transactions, not merely core state.
  top.s_axi_awaddr = BASE + 0x10; top.s_axi_awvalid = 1; tick(top); if (top.s_axi_arready) fail("partial AW did not gate AR"); reset(top);
  top.s_axi_wdata = 0; top.s_axi_wstrb = 0xf; top.s_axi_wvalid = 1; tick(top); if (top.s_axi_arready) fail("partial W did not gate AR"); reset(top);
  // Reset discards each captured half: the complementary half alone cannot reply.
  for (int first = 0; first < 2; ++first) {
    reset(top);
    top.s_axi_awaddr = BASE + 0x14; top.s_axi_wdata = 0; top.s_axi_wstrb = 0xf;
    top.s_axi_awvalid = first == 0; top.s_axi_wvalid = first == 1; tick(top);
    reset(top);
    top.s_axi_awaddr = BASE + 0x14; top.s_axi_wdata = 0; top.s_axi_wstrb = 0xf;
    top.s_axi_awvalid = first == 1; top.s_axi_wvalid = first == 0; tick(top);
    top.s_axi_awvalid = top.s_axi_wvalid = 0;
    for (int n = 0; n < 4; ++n) { tick(top); if (top.s_axi_bvalid) fail("pre-reset half reused"); }
    top.s_axi_awvalid = first == 0; top.s_axi_wvalid = first == 1; tick(top);
    top.s_axi_awvalid = top.s_axi_wvalid = 0; tick(top); wait_b(top, SLVERR);
  }
  // AW/W held throughout release are admitted only after both release edges.
  reset(top); top.aresetn = 0; top.eval(); quiet(top);
  top.s_axi_awaddr = BASE + 0x14; top.s_axi_awvalid = 1;
  top.s_axi_wdata = 0; top.s_axi_wstrb = 0xf; top.s_axi_wvalid = 1;
  top.aresetn = 1; top.eval(); quiet(top); tick(top); quiet(top); tick(top);
  if (top.s_axi_bvalid || !top.s_axi_awready || !top.s_axi_wready) fail("write release boundary");
  tick(top); top.s_axi_awvalid = top.s_axi_wvalid = 0; tick(top); wait_b(top, SLVERR);
  // When idle read and write are presented together, write has priority and
  // the target must not admit a second, concurrent read transaction.
  top.s_axi_awaddr = BASE + 0x14; top.s_axi_awvalid = 1; top.s_axi_wdata = 0; top.s_axi_wstrb = 0xf; top.s_axi_wvalid = 1;
  top.s_axi_araddr = BASE + 0; top.s_axi_arvalid = 1; top.eval(); if (top.s_axi_arready) fail("read admitted with write");
  tick(top); top.s_axi_awvalid = top.s_axi_wvalid = top.s_axi_arvalid = 0; tick(top); wait_b(top, SLVERR);
  top.s_axi_araddr = BASE + 0; top.s_axi_arvalid = 1; tick(top); top.s_axi_arvalid = 0; if (!top.s_axi_rvalid) fail("held R setup"); reset(top);
  top.s_axi_awaddr = BASE + 0; top.s_axi_awvalid = 1; top.s_axi_wdata = 0; top.s_axi_wstrb = 0xf; top.s_axi_wvalid = 1; tick(top); top.s_axi_awvalid = top.s_axi_wvalid = 0; tick(top); if (!top.s_axi_bvalid) fail("held B setup"); reset(top);
  // CONTROL.reset blocks admission while retaining its OKAY B response until BREADY.
  top.s_axi_awaddr = BASE + 0x10; top.s_axi_awvalid = 1; top.s_axi_wdata = 4; top.s_axi_wstrb = 0xf; top.s_axi_wvalid = 1; tick(top); top.s_axi_awvalid = top.s_axi_wvalid = 0; tick(top);
  if (!top.s_axi_bvalid || top.s_axi_bresp != OKAY || top.s_axi_awready || top.s_axi_wready || top.s_axi_arready) fail("soft reset response/admission");
  tick(top); if (!top.s_axi_bvalid || top.s_axi_bresp != OKAY || top.s_axi_awready || top.s_axi_wready || top.s_axi_arready) fail("soft reset B hold");
  tick(top); if (!top.s_axi_bvalid || top.s_axi_awready || top.s_axi_wready || top.s_axi_arready) fail("soft reset pre-handshake admission");
  top.s_axi_bready = 1; tick(top); top.s_axi_bready = 0;
  if (top.s_axi_awready || top.s_axi_wready || top.s_axi_arready) fail("soft reset barrier after B handshake");
  tick(top);
  read(top, 0x0000, OKAY, 0x52560101); read(top, 0x0014, OKAY, 0);
  read(top, 0x2000, OKAY, 0x52564901); read(top, 0x2014, OKAY, 2);
  read(top, 0x3000, OKAY, 0x52565001); read(top, 0x3014, OKAY, 2);
  reset(top);
  std::cout << "GraphDevice-BOARD-BRIDGE-V1 status=OK evidence=rtl-simulation-functional performance=not-measured\n";
  return 0;
}
