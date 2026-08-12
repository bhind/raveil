#include "VRaveilRocketLifecycleObserver.h"
#include "verilated.h"

#include <cstdint>
#include <cstdio>
#include <cstdlib>

double sc_time_stamp() { return 0.0; }

namespace {

enum Event : uint32_t {
  kAllocate = 0,
  kCoreAttempt = 1,
  kCoreReplay = 2,
  kDcacheRetry = 3,
  kAAccept = 4,
  kDComplete = 5,
  kDError = 6,
  kRetire = 7,
  kStoreAuthorize = 8,
  kKill = 9,
  kException = 10,
  kResetInvalidate = 13,
};

void fail(const char* message) {
  std::fprintf(stderr, "Rocket lifecycle observer failure: %s\n", message);
  std::exit(1);
}

void tick(VRaveilRocketLifecycleObserver& dut) {
  dut.clock = 0;
  dut.eval();
  dut.clock = 1;
  dut.eval();
}

void event(VRaveilRocketLifecycleObserver& dut, Event kind, uint32_t epoch,
           uint32_t sequence, bool present = true, bool store = false,
           uint64_t pc = 0) {
  dut.io_eventKind = kind;
  dut.io_eventEpoch = epoch;
  dut.io_eventSequence = sequence;
  dut.io_metadataPresent = present;
  dut.io_eventStore = store;
  dut.io_eventPc = pc;
  dut.io_eventValid = 1;
  tick(dut);
  dut.io_eventValid = 0;
  dut.eval();
}

void allocate(VRaveilRocketLifecycleObserver& dut, uint32_t epoch,
              uint32_t sequence, bool store, uint64_t pc) {
  event(dut, kAllocate, epoch, sequence, true, store, pc);
  if (!dut.io_active) fail("allocation did not create a live token");
}

void commit_load(VRaveilRocketLifecycleObserver& dut, uint32_t epoch,
                 uint32_t sequence, uint64_t pc) {
  allocate(dut, epoch, sequence, false, pc);
  event(dut, kCoreAttempt, epoch, sequence);
  event(dut, kAAccept, epoch, sequence);
  event(dut, kDComplete, epoch, sequence);
  event(dut, kRetire, epoch, sequence);
  if (dut.io_active) fail("committed load remained active");
}

void kill_without_request(VRaveilRocketLifecycleObserver& dut, uint32_t epoch,
                          uint32_t sequence, uint64_t pc) {
  allocate(dut, epoch, sequence, false, pc);
  event(dut, kKill, epoch, sequence);
  if (dut.io_active) fail("killed token remained active");
}

}  // namespace

int main(int argc, char** argv) {
  Verilated::commandArgs(argc, argv);
  VRaveilRocketLifecycleObserver dut;
  dut.io_eventValid = 0;
  dut.io_metadataPresent = 0;
  dut.io_eventKind = 0;
  dut.io_eventEpoch = 0;
  dut.io_eventSequence = 0;
  dut.io_eventStore = 0;
  dut.io_eventPc = 0;
  dut.reset = 1;
  for (int cycle = 0; cycle < 5; ++cycle) tick(dut);
  dut.reset = 0;
  tick(dut);

  commit_load(dut, 1, 1, 0x1000);

  allocate(dut, 1, 2, true, 0x1004);
  event(dut, kCoreAttempt, 1, 2);
  event(dut, kAAccept, 1, 2);
  event(dut, kRetire, 1, 2);
  event(dut, kStoreAuthorize, 1, 2);
  event(dut, kDComplete, 1, 2);
  if (dut.io_active) fail("committed store remained active");

  allocate(dut, 1, 3, false, 0x1008);
  event(dut, kCoreAttempt, 1, 3);
  event(dut, kCoreReplay, 1, 3);
  event(dut, kDcacheRetry, 1, 3);
  event(dut, kAAccept, 1, 3);
  event(dut, kDComplete, 1, 3);
  event(dut, kRetire, 1, 3);

  allocate(dut, 1, 4, false, 0x100c);
  event(dut, kCoreAttempt, 1, 4);
  event(dut, kKill, 1, 4);

  allocate(dut, 1, 5, true, 0x1010);
  event(dut, kCoreAttempt, 1, 5);
  event(dut, kAAccept, 1, 5);
  event(dut, kException, 1, 5);
  event(dut, kDComplete, 1, 5);
  if (dut.io_lastViolation != 7)
    fail("post-A exception did not report side-effect violation");

  allocate(dut, 1, 6, false, 0x1014);
  event(dut, kCoreAttempt, 1, 6);
  event(dut, kAAccept, 1, 6);
  event(dut, kResetInvalidate, 1, 6);
  if (dut.io_currentEpoch != 2 || dut.io_nextSequence != 1)
    fail("reset invalidation did not advance epoch and restart sequence");
  event(dut, kDComplete, 1, 6);
  if (dut.io_lastViolation != 10)
    fail("old-epoch completion did not fail stale");

  allocate(dut, 2, 1, false, 0x2000);
  event(dut, kAAccept, 2, 1, false);
  if (dut.io_lastViolation != 1 || dut.io_lastClassification != 4)
    fail("stripped metadata did not fail unknown");
  event(dut, kKill, 2, 1);

  event(dut, kAllocate, 2, 1, true, false, 0x2000);
  if (dut.io_lastViolation != 4)
    fail("duplicate token did not fail closed");
  commit_load(dut, 2, 2, 0x2004);
  event(dut, kRetire, 2, 2);
  if (dut.io_lastViolation != 5)
    fail("duplicate outcome did not fail closed");

  event(dut, kAllocate, 2, 3, false, false, 0x2008);
  if (dut.io_lastViolation != 1 || dut.io_lastClassification != 4)
    fail("untagged allocation did not fail unknown");
  allocate(dut, 2, 3, false, 0x2008);
  event(dut, kCoreAttempt, 2, 3);
  event(dut, kAAccept, 2, 3);
  event(dut, kDError, 2, 3);

  allocate(dut, 2, 4, false, 0x200c);
  event(dut, kRetire, 2, 4);
  event(dut, kDComplete, 2, 4);
  if (!dut.io_active || dut.io_lastViolation != 6)
    fail("invalid completion promoted a retired load");
  event(dut, kKill, 2, 4);

  for (uint32_t sequence = 5; sequence <= 15; ++sequence) {
    kill_without_request(dut, 2, sequence, 0x2000 + sequence * 4);
  }
  if (!dut.io_sequenceExhausted) fail("sequence exhaustion was not latched");
  event(dut, kAllocate, 2, 0, true, false, 0x3000);

  if (dut.io_active) fail("observer ended with a live token");
  if (dut.io_currentEpoch != 2 || dut.io_epochExhausted)
    fail("epoch state mismatch");
  if (dut.io_allocatedCount != 21 || dut.io_committedLoadCount != 3 ||
      dut.io_committedStoreCount != 1 || dut.io_nonCommittedCount != 17)
    fail("terminal outcome accounting mismatch");
  if (dut.io_coreAttemptCount != 8 || dut.io_coreReplayCount != 1 ||
      dut.io_dcacheRetryCount != 1)
    fail("attempt accounting mismatch");
  if (dut.io_aAcceptedCount != 7 || dut.io_dCompletedCount != 7 ||
      dut.io_retireCount != 5 || dut.io_storeAuthorizedCount != 1)
    fail("transport/retirement accounting mismatch");
  if (dut.io_unknownCount != 2 || dut.io_violationCount != 8)
    fail("fail-closed accounting mismatch");
  if (dut.io_lastClassification != 5 || dut.io_lastViolation != 8)
    fail("final exhaustion violation mismatch");

  std::printf(
      "ROCKET-LIFECYCLE-OBSERVER-V1 status=OK allocated=21 "
      "committed_load=3 committed_store=1 noncommitted=17 "
      "core_attempts=8 core_replays=1 dcache_retries=1 "
      "a_accepted=7 d_completed=7 retired=5 store_authorized=1 "
      "unknown=2 violations=8 load_positive=covered store_positive=covered "
      "pre_a_kill=covered post_a_exception=covered reset_outstanding=covered "
      "stale_epoch=covered stripped_metadata=covered duplicate_token=covered "
      "duplicate_outcome=covered invalid_completion=covered "
      "untagged_event=covered d_error=covered "
      "sequence_exhaustion=covered event_source=synthetic cpu_execution=not-run "
      "semantic_initiator=not-proven resource_match_verified=0 "
      "matched_comparison_ready=0 evidence=rtl-simulation-functional "
      "performance=not-measured\n");
  return 0;
}
