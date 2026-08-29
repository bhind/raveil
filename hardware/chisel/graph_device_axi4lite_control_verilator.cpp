#include "VGraphDeviceAxi4LiteTop.h"
#include "verilated.h"
#include <cstdint>
#include <cstdlib>
#include <iostream>

static constexpr uint32_t OKAY = 0, SLVERR = 2, DECERR = 3;
static void fail(const char* what) { std::cerr << "AXI4LITE test failed: " << what << "\n"; std::exit(1); }
static void tick(VGraphDeviceAxi4LiteTop& t) { t.aclk = 0; t.eval(); t.aclk = 1; t.eval(); }
static void idle(VGraphDeviceAxi4LiteTop& t) {
  t.awvalid = t.wvalid = t.arvalid = t.bready = t.rready = 0;
  t.awaddr = t.wdata = t.wstrb = t.araddr = 0;
}
static void reset(VGraphDeviceAxi4LiteTop& t) { idle(t); t.aresetn = 0; tick(t); if (t.bvalid || t.rvalid) fail("ARESETn did not clear responses"); t.aresetn = 1; tick(t); }
static void wait_b(VGraphDeviceAxi4LiteTop& t, uint32_t expected) {
  for (int n = 0; n != 8; ++n) { if (t.bvalid) { if (t.bresp != expected) fail("BRESP"); const auto held = t.bresp; tick(t); if (!t.bvalid || t.bresp != held) fail("B stability"); t.bready = 1; tick(t); t.bready = 0; return; } tick(t); } fail("B timeout");
}
static void write(VGraphDeviceAxi4LiteTop& t, uint32_t address, uint32_t data, uint32_t strb, int mode, uint32_t response) {
  if (mode == 0 || mode == 2) { t.awaddr = address; t.awvalid = 1; }
  if (mode == 1 || mode == 2) { t.wdata = data; t.wstrb = strb; t.wvalid = 1; }
  tick(t);
  if (mode == 0) { t.awvalid = 0; t.wdata = data; t.wstrb = strb; t.wvalid = 1; tick(t); }
  if (mode == 1) { t.wvalid = 0; t.awaddr = address; t.awvalid = 1; tick(t); }
  t.awvalid = t.wvalid = 0; tick(t); wait_b(t, response);
}
static void read(VGraphDeviceAxi4LiteTop& t, uint32_t address, uint32_t response, uint32_t data = 0) {
  t.araddr = address; t.arvalid = 1; tick(t); t.arvalid = 0;
  for (int n = 0; n != 8; ++n) { if (t.rvalid) { if (t.rresp != response || (response == OKAY && t.rdata != data)) { std::cerr << "read address=0x" << std::hex << address << " expected resp=" << response << " data=" << data << " got resp=" << uint32_t(t.rresp) << " data=" << t.rdata << "\n"; fail("R response/data"); } const uint32_t heldData = t.rdata; const uint32_t heldResp = t.rresp; tick(t); if (!t.rvalid || t.rdata != heldData || t.rresp != heldResp) fail("R stability"); t.rready = 1; tick(t); t.rready = 0; return; } tick(t); } fail("R timeout");
}
int main(int argc, char** argv) {
  Verilated::commandArgs(argc, argv); VGraphDeviceAxi4LiteTop top; reset(top);
  // All S01 identity/version/status/count words, each aperture separately.
  read(top, 0x0000, OKAY, 0x52560101); read(top, 0x0004, OKAY, 1); read(top, 0x0014, OKAY, 0); read(top, 0x0018, OKAY, 324); read(top, 0x001c, OKAY, 256);
  read(top, 0x2000, OKAY, 0x52564901); read(top, 0x2004, OKAY, 1); read(top, 0x2014, OKAY, 2); read(top, 0x2018, OKAY, 16);
  read(top, 0x3000, OKAY, 0x52565001); read(top, 0x3004, OKAY, 1); read(top, 0x3014, OKAY, 2); read(top, 0x3018, OKAY, 0);
  // AW-first, W-first and same-cycle capture; all non-reset writes fail closed.
  write(top, 0x0014, 0, 0xf, 0, SLVERR); write(top, 0x0014, 0, 0xf, 1, SLVERR); write(top, 0x0014, 0, 0xf, 2, SLVERR);
  // Decoded holes/RO/partial write are SLVERR; unaligned/outside are DECERR.
  read(top, 0x0008, SLVERR); read(top, 0x2008, SLVERR); read(top, 0x3008, SLVERR); read(top, 1, DECERR); read(top, 0x4000, DECERR);
  write(top, 0x0000, 0, 0xf, 2, SLVERR); write(top, 0x2000, 0, 0xf, 2, SLVERR); write(top, 0x3000, 0, 0xf, 2, SLVERR); write(top, 0x0010, 4, 1, 2, SLVERR); write(top, 1, 0, 0xf, 2, DECERR); write(top, 0x4000, 0, 0xf, 2, DECERR);
  // ARESETn clears partial AW/W, held R, and held B transactions, not merely core state.
  top.awaddr = 0x10; top.awvalid = 1; tick(top); if (top.arready) fail("partial AW did not gate AR"); reset(top);
  top.wdata = 0; top.wstrb = 0xf; top.wvalid = 1; tick(top); if (top.arready) fail("partial W did not gate AR"); reset(top);
  // When idle read and write are presented together, write has priority and
  // the target must not admit a second, concurrent read transaction.
  top.awaddr = 0x14; top.awvalid = 1; top.wdata = 0; top.wstrb = 0xf; top.wvalid = 1;
  top.araddr = 0; top.arvalid = 1; top.eval(); if (top.arready) fail("read admitted with write");
  tick(top); top.awvalid = top.wvalid = top.arvalid = 0; tick(top); wait_b(top, SLVERR);
  top.araddr = 0; top.arvalid = 1; tick(top); top.arvalid = 0; if (!top.rvalid) fail("held R setup"); reset(top);
  top.awaddr = 0; top.awvalid = 1; top.wdata = 0; top.wstrb = 0xf; top.wvalid = 1; tick(top); top.awvalid = top.wvalid = 0; tick(top); if (!top.bvalid) fail("held B setup"); reset(top);
  // CONTROL.reset blocks admission while retaining its OKAY B response until BREADY.
  top.awaddr = 0x10; top.awvalid = 1; top.wdata = 4; top.wstrb = 0xf; top.wvalid = 1; tick(top); top.awvalid = top.wvalid = 0; tick(top);
  if (!top.bvalid || top.bresp != OKAY || top.awready || top.wready || top.arready) fail("soft reset response/admission");
  tick(top); if (!top.bvalid || top.bresp != OKAY || top.awready || top.wready || top.arready) fail("soft reset B hold");
  tick(top); if (!top.bvalid || top.awready || top.wready || top.arready) fail("soft reset pre-handshake admission");
  top.bready = 1; tick(top); top.bready = 0;
  if (top.awready || top.wready || top.arready) fail("soft reset barrier after B handshake");
  tick(top);
  read(top, 0x0000, OKAY, 0x52560101); read(top, 0x0014, OKAY, 0);
  read(top, 0x2000, OKAY, 0x52564901); read(top, 0x2014, OKAY, 2);
  read(top, 0x3000, OKAY, 0x52565001); read(top, 0x3014, OKAY, 2);
  reset(top);
  std::cout << "GraphDevice-AXI4LITE-CONTROL-V1 status=OK evidence=rtl-simulation-functional performance=not-measured\n";
  return 0;
}
