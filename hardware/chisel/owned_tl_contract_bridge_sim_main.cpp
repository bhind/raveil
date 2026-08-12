#include "VRaveilOwnedTLContractBridgeHarness.h"
#include "verilated.h"

#include <cstdint>
#include <cstdio>
#include <cstdlib>

double sc_time_stamp() { return 0.0; }

static void fail(const char* message) {
  std::fprintf(stderr, "owned TL contract bridge failure: %s\n", message);
  std::exit(1);
}

static void tick(VRaveilOwnedTLContractBridgeHarness& dut) {
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

static Response transact(VRaveilOwnedTLContractBridgeHarness& dut,
                         uint32_t opcode,
                         uint32_t address,
                         uint32_t data,
                         uint32_t mask,
                         uint32_t size,
                         uint32_t source,
                         uint32_t initiator,
                         uint32_t phase,
                         int hold_response_cycles = 0) {
  dut.io_requestOpcode = opcode;
  dut.io_requestParam = 0;
  dut.io_requestSize = size;
  dut.io_requestSource = source;
  dut.io_requestAddress = address;
  dut.io_requestMask = mask;
  dut.io_requestData = data;
  dut.io_requestInitiator = initiator;
  dut.io_requestPhase = phase;
  dut.io_requestValid = 1;
  dut.io_responseReady = 0;

  int timeout = 64;
  while (!dut.io_requestReady && --timeout > 0) tick(dut);
  if (timeout == 0) fail("request did not become ready");
  tick(dut);
  dut.io_requestValid = 0;
  dut.io_requestInitiator = 0;
  dut.io_requestPhase = 0;

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
    dut.io_requestValid = 1;
    dut.eval();
    if (dut.io_requestReady) fail("second request accepted while response pending");
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
                            uint32_t source, bool denied = false) {
  if (response.opcode != 1 || response.param != 0 || response.size != size ||
      response.source != source || response.denied != denied ||
      response.corrupt != denied) {
    fail("read response mismatch");
  }
  return response.data;
}

int main(int argc, char** argv) {
  Verilated::commandArgs(argc, argv);
  VRaveilOwnedTLContractBridgeHarness dut;
  dut.io_requestValid = 0;
  dut.io_responseReady = 0;
  dut.io_requestInitiator = 0;
  dut.io_requestPhase = 0;
  dut.reset = 1;
  for (int cycle = 0; cycle < 5; ++cycle) tick(dut);
  dut.reset = 0;
  tick(dut);

  constexpr uint32_t data_base = 0x08000000;
  constexpr uint32_t put_full = 0;
  constexpr uint32_t put_partial = 1;
  constexpr uint32_t get = 4;
  constexpr uint32_t initiator_cpu = 1;
  constexpr uint32_t phase_execution = 2;
  constexpr uint32_t phase_validation = 4;

  expect_ack(transact(dut, put_full, data_base, 0x11223344, 0xf, 2, 1,
                      initiator_cpu, phase_execution), 2, 1, false);
  if (expect_data(transact(dut, get, data_base, 0, 0xf, 2, 2,
                           initiator_cpu, phase_execution), 2, 2) != 0x11223344)
    fail("full-write readback mismatch");

  expect_ack(transact(dut, put_partial, data_base, 0xaa00bbcc, 0x5, 2, 3,
                      initiator_cpu, phase_execution), 2, 3, false);
  expect_ack(transact(dut, put_partial, data_base, 0x55ee6677, 0xa, 2, 0,
                      initiator_cpu, phase_execution), 2, 0, false);
  if (expect_data(transact(dut, get, data_base, 0, 0xf, 2, 3,
                           initiator_cpu, phase_validation, 3), 2, 3) !=
      0x550066cc) fail("partial-write readback mismatch");

  if (expect_data(transact(dut, get, data_base + 15 * 4, 0, 0xf, 2, 0,
                           initiator_cpu, phase_validation), 2, 0, true) != 0)
    fail("range-error read returned data");

  if (dut.io_ownedAcceptedCount != 6 || dut.io_ownedCompletedCount != 6)
    fail("owned request/response conservation mismatch");
  if (dut.io_ownedRequestStallCount != 0)
    fail("bridge leaked a blocked TileLink request into the owned target");
  if (dut.io_ownedResponseStallCount < 3)
    fail("owned response backpressure count mismatch");
  if (dut.io_lastAcceptedInitiator != initiator_cpu ||
      dut.io_lastCompletedInitiator != initiator_cpu ||
      dut.io_lastAcceptedPhase != phase_validation ||
      dut.io_lastCompletedPhase != phase_validation) {
    fail("owned initiator/phase correlation mismatch");
  }

  std::printf("OWNED-TL-CONTRACT-BRIDGE-V1 status=OK tl_transactions=6 owned_accepted=6 owned_completed=6 put_full=1 put_partial=2 get=3 byte_masks=0x5,0xa range_rejection=covered single_outstanding_request_blocking=covered response_backpressure=covered max_one_outstanding=covered tl_metadata=source,size owned_metadata=initiator,phase attribution=adapter-input-only semantic_initiator=not-proven cpu_execution=not-run resource_match_verified=0 matched_comparison_ready=0 evidence=rtl-simulation-functional performance=not-measured\n");
  return 0;
}
