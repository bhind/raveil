#include "VRaveilOwnedTLProtocolHarness.h"
#include "verilated.h"

#include <cstdint>
#include <cstdio>
#include <cstdlib>

double sc_time_stamp() { return 0.0; }

static void fail(const char* message) {
  std::fprintf(stderr, "owned TL protocol failure: %s\n", message);
  std::exit(1);
}

static void tick(VRaveilOwnedTLProtocolHarness& dut) {
  dut.clock = 0;
  dut.eval();
  dut.clock = 1;
  dut.eval();
}

struct Response {
  uint32_t opcode;
  uint32_t param;
  uint32_t size;
  uint32_t source;
  uint32_t sink;
  uint32_t denied;
  uint32_t data;
  uint32_t corrupt;
};

static Response transact(VRaveilOwnedTLProtocolHarness& dut,
                         uint32_t opcode,
                         uint32_t address,
                         uint32_t data,
                         uint32_t mask,
                         uint32_t size,
                         uint32_t source,
                         int hold_response_cycles = 0) {
  dut.io_requestOpcode = opcode;
  dut.io_requestParam = 0;
  dut.io_requestSize = size;
  dut.io_requestSource = source;
  dut.io_requestAddress = address;
  dut.io_requestMask = mask;
  dut.io_requestData = data;
  dut.io_requestValid = 1;
  dut.io_responseReady = 0;

  int timeout = 64;
  while (!dut.io_requestReady && --timeout > 0) tick(dut);
  if (timeout == 0) fail("request did not become ready");
  tick(dut);
  dut.io_requestValid = 0;

  timeout = 64;
  while (!dut.io_responseValid && --timeout > 0) tick(dut);
  if (timeout == 0) fail("response did not become valid");

  const Response first = {
      dut.io_responseOpcode,
      dut.io_responseParam,
      dut.io_responseSize,
      dut.io_responseSource,
      dut.io_responseSink,
      dut.io_responseDenied,
      static_cast<uint32_t>(dut.io_responseData),
      dut.io_responseCorrupt,
  };
  for (int cycle = 0; cycle < hold_response_cycles; ++cycle) {
    dut.io_requestSource = source;
    dut.io_requestValid = 1;
    dut.eval();
    if (dut.io_requestReady)
      fail("same-source request accepted while response pending");
    dut.io_requestValid = 0;
    dut.eval();
    if (!dut.io_responseValid || dut.io_responseOpcode != first.opcode ||
        dut.io_responseParam != first.param ||
        dut.io_responseSize != first.size ||
        dut.io_responseSource != first.source ||
        dut.io_responseSink != first.sink ||
        dut.io_responseDenied != first.denied ||
        static_cast<uint32_t>(dut.io_responseData) != first.data ||
        dut.io_responseCorrupt != first.corrupt) {
      fail("response changed under D-channel backpressure");
    }
    tick(dut);
  }
  dut.io_responseReady = 1;
  tick(dut);
  dut.io_responseReady = 0;
  if (dut.io_responseValid) fail("response remained valid after consumption");
  return first;
}

static void expect_ack(const Response& response, uint32_t size,
                       uint32_t source, bool denied) {
  if (response.opcode != 0 || response.param != 0 || response.size != size ||
      response.source != source || response.denied != denied ||
      response.sink != 0 || response.data != 0 || response.corrupt != 0) {
    fail("write acknowledgement mismatch");
  }
}

static uint32_t expect_data(const Response& response, uint32_t size,
                            uint32_t source) {
  if (response.opcode != 1 || response.param != 0 || response.size != size ||
      response.source != source || response.denied || response.corrupt) {
    fail("read response mismatch");
  }
  return response.data;
}

int main(int argc, char** argv) {
  Verilated::commandArgs(argc, argv);
  VRaveilOwnedTLProtocolHarness dut;
  dut.io_requestValid = 0;
  dut.io_responseReady = 0;
  dut.reset = 1;
  for (int cycle = 0; cycle < 5; ++cycle) tick(dut);
  dut.reset = 0;
  tick(dut);

  constexpr uint32_t data_base = 0x08000000;
  constexpr uint32_t control_base = 0x08010000;
  constexpr uint32_t put_full = 0;
  constexpr uint32_t put_partial = 1;
  constexpr uint32_t get = 4;

  if (expect_data(transact(dut, get, control_base, 0, 0xf, 2, 0), 2, 0) != 0)
    fail("reset phase was not zero");

  expect_ack(transact(dut, put_full, data_base, 0x11223344, 0xf, 2, 1),
             2, 1, false);
  if (expect_data(transact(dut, get, data_base, 0, 0xf, 2, 2), 2, 2) !=
      0x11223344) fail("full-write readback mismatch");

  expect_ack(transact(dut, put_partial, data_base, 0xaa00bbcc, 0x5, 2, 3),
             2, 3, false);
  if (expect_data(transact(dut, get, data_base, 0, 0xf, 2, 0), 2, 0) !=
      0x110033cc) fail("partial-write readback mismatch");

  expect_ack(transact(dut, put_partial, data_base, 0x55ee6677, 0xa, 2, 0),
             2, 0, false);
  if (expect_data(transact(dut, get, data_base, 0, 0xf, 2, 1), 2, 1) !=
      0x550066cc) fail("alternate partial-write readback mismatch");

  expect_ack(transact(dut, put_partial, control_base, 2, 0x1, 0, 1),
             0, 1, false);
  if (expect_data(transact(dut, get, control_base, 0, 0xf, 2, 2), 2, 2) != 2)
    fail("phase register readback mismatch");

  expect_ack(transact(dut, put_partial, control_base, 7, 0x1, 0, 3),
             0, 3, true);
  expect_ack(transact(dut, put_partial, control_base, 1, 0x2, 1, 0),
             1, 0, true);
  if (expect_data(transact(dut, get, control_base, 0, 0xf, 2, 1), 2, 1) != 2)
    fail("denied write changed phase");

  if (expect_data(transact(dut, get, control_base + 4, 0, 0xf, 2, 2), 2, 2) != 6)
    fail("accepted data counter mismatch");
  if (expect_data(transact(dut, get, control_base + 8, 0, 0xf, 2, 3), 2, 3) != 6)
    fail("completed data counter mismatch");

  if (expect_data(transact(dut, get, data_base, 0, 0xf, 2, 3, 3), 2, 3) !=
      0x550066cc) fail("backpressured read data mismatch");
  if (expect_data(transact(dut, get, control_base + 0x20, 0, 0xf, 2, 0), 2, 0) != 1)
    fail("execution-phase read counter mismatch");

  if (expect_data(transact(dut, get, control_base + 0x50, 0, 0xf, 2, 0), 2, 0) != 1)
    fail("expected source start mismatch");
  if (expect_data(transact(dut, get, control_base + 0x54, 0, 0xf, 2, 0), 2, 0) != 3)
    fail("expected source end mismatch");
  if (expect_data(transact(dut, get, control_base + 0x58, 0, 0xf, 2, 0), 2, 0) != 3)
    fail("expected-source accepted counter mismatch");
  if (expect_data(transact(dut, get, control_base + 0x5c, 0, 0xf, 2, 0), 2, 0) != 3)
    fail("expected-source completed counter mismatch");
  if (expect_data(transact(dut, get, control_base + 0x60, 0, 0xf, 2, 0), 2, 0) != 4)
    fail("unexpected-source accepted counter mismatch");
  if (expect_data(transact(dut, get, control_base + 0x64, 0, 0xf, 2, 0), 2, 0) != 4)
    fail("unexpected-source completed counter mismatch");
  if (expect_data(transact(dut, get, control_base + 0x68, 0, 0xf, 2, 0), 2, 0) != 3)
    fail("last accepted source mismatch");
  if (expect_data(transact(dut, get, control_base + 0x6c, 0, 0xf, 2, 0), 2, 0) != 3)
    fail("last completed source mismatch");
  if (expect_data(transact(dut, get, control_base + 0x70, 0, 0xf, 2, 0), 2, 0) != 2)
    fail("last accepted phase mismatch");
  if (expect_data(transact(dut, get, control_base + 0x74, 0, 0xf, 2, 0), 2, 0) != 2)
    fail("last completed phase mismatch");
  if (expect_data(transact(dut, get, control_base + 0x78, 0, 0xf, 2, 0), 2, 0) != 0)
    fail("raw client was misclassified as DCache-origin at acceptance");
  if (expect_data(transact(dut, get, control_base + 0x7c, 0, 0xf, 2, 0), 2, 0) != 0)
    fail("raw client was misclassified as DCache-origin at completion");
  if (expect_data(transact(dut, get, control_base + 0x80, 0, 0xf, 2, 0), 2, 0) != 7)
    fail("non-DCache-origin accepted counter mismatch");
  if (expect_data(transact(dut, get, control_base + 0x84, 0, 0xf, 2, 0), 2, 0) != 7)
    fail("non-DCache-origin completed counter mismatch");

  std::printf("OWNED-TL-PROTOCOL-V4 status=OK transactions=30 put_full=1 put_partial=5 get=24 byte_masks=0x5,0xa invalid_phase_denial=covered response_backpressure=covered max_one_outstanding=covered same_source_reuse_blocking=covered response_metadata=param,size,source,sink,denied,corrupt reset_phase=covered counter_scope=aggregate-data,execution-read,source-class,request-response-phase,dcache-origin-sideband source_classifier_range=1:3 unexpected_boundary_sources=0,3 expected_source_accepted=3 expected_source_completed=3 unexpected_source_accepted=4 unexpected_source_completed=4 dcache_origin_accepted=0 dcache_origin_completed=0 non_dcache_origin_accepted=7 non_dcache_origin_completed=7 last_source=3 last_phase=2 cpu_execution=not-run source_client_class=harness-range-only dcache_origin_negative=raw-client-without-sideband semantic_initiator=not-proven resource_match_verified=0 matched_comparison_ready=0 evidence=rtl-simulation-functional performance=not-measured\n");
  return 0;
}
