//> using scala 2.13.17
//> using dep org.chipsalliance::chisel:7.2.0
//> using plugin org.chipsalliance:::chisel-plugin:7.2.0

import chisel3._
import chisel3.util._
import _root_.circt.stage.ChiselStage

object RocketLifecycleEvent {
  val Allocate = 0
  val CoreAttempt = 1
  val CoreReplay = 2
  val DcacheRetry = 3
  val AAccept = 4
  val DComplete = 5
  val DError = 6
  val Retire = 7
  val StoreAuthorize = 8
  val Kill = 9
  val Exception = 10
  val Redirect = 11
  val Rollback = 12
  val ResetInvalidate = 13
  val Count = 14
}

object RocketLifecycleClassification {
  val None = 0
  val CommittedLoad = 1
  val CommittedStore = 2
  val NonCommitted = 3
  val Unknown = 4
  val Violation = 5
}

object RocketLifecycleViolation {
  val None = 0
  val MissingMetadata = 1
  val UnexpectedEvent = 2
  val TokenMismatch = 3
  val DuplicateToken = 4
  val DuplicateOutcome = 5
  val InvalidTransition = 6
  val PostTerminalSideEffect = 7
  val SequenceExhausted = 8
  val EpochExhausted = 9
  val StaleEpoch = 10
}

/**
  * Repository-owned ADR-0045 lifecycle ledger.
  *
  * This module consumes synthetic CPU-lifecycle events. It does not observe a
  * Rocket core yet and cannot prove instruction, ELF, or semantic initiator
  * identity. It fixes the fail-closed token/epoch state machine before a later
  * pinned-core hook is allowed to supply real events.
  */
class RaveilRocketLifecycleObserver(
    val epochWidth: Int = 4,
    val sequenceWidth: Int = 12
) extends Module {
  require(epochWidth >= 2)
  require(sequenceWidth >= 2)

  val io = IO(new Bundle {
    val eventValid = Input(Bool())
    val eventKind = Input(UInt(4.W))
    val metadataPresent = Input(Bool())
    val eventEpoch = Input(UInt(epochWidth.W))
    val eventSequence = Input(UInt(sequenceWidth.W))
    val eventStore = Input(Bool())
    val eventPc = Input(UInt(64.W))

    val active = Output(Bool())
    val currentEpoch = Output(UInt(epochWidth.W))
    val nextSequence = Output(UInt(sequenceWidth.W))
    val sequenceExhausted = Output(Bool())
    val epochExhausted = Output(Bool())

    val allocatedCount = Output(UInt(32.W))
    val coreAttemptCount = Output(UInt(32.W))
    val coreReplayCount = Output(UInt(32.W))
    val dcacheRetryCount = Output(UInt(32.W))
    val aAcceptedCount = Output(UInt(32.W))
    val dCompletedCount = Output(UInt(32.W))
    val retireCount = Output(UInt(32.W))
    val storeAuthorizedCount = Output(UInt(32.W))
    val committedLoadCount = Output(UInt(32.W))
    val committedStoreCount = Output(UInt(32.W))
    val nonCommittedCount = Output(UInt(32.W))
    val unknownCount = Output(UInt(32.W))
    val violationCount = Output(UInt(32.W))

    val lastClassification = Output(UInt(3.W))
    val lastViolation = Output(UInt(4.W))
    val lastEpoch = Output(UInt(epochWidth.W))
    val lastSequence = Output(UInt(sequenceWidth.W))
    val lastPc = Output(UInt(64.W))
  })

  val currentEpoch = RegInit(1.U(epochWidth.W))
  val nextSequence = RegInit(1.U(sequenceWidth.W))
  val sequenceExhausted = RegInit(false.B)
  val epochExhausted = RegInit(false.B)

  val active = RegInit(false.B)
  val activeEpoch = RegInit(0.U(epochWidth.W))
  val activeSequence = RegInit(0.U(sequenceWidth.W))
  val activeStore = RegInit(false.B)
  val activePc = RegInit(0.U(64.W))
  val activeCoreAttempt = RegInit(false.B)
  val activeAAccepted = RegInit(false.B)
  val activeDCompleted = RegInit(false.B)
  val activeRetired = RegInit(false.B)
  val activeStoreAuthorized = RegInit(false.B)

  val terminalValid = RegInit(false.B)
  val terminalEpoch = RegInit(0.U(epochWidth.W))
  val terminalSequence = RegInit(0.U(sequenceWidth.W))
  val terminalAAccepted = RegInit(false.B)
  val terminalFatal = RegInit(false.B)

  val allocatedCount = RegInit(0.U(32.W))
  val coreAttemptCount = RegInit(0.U(32.W))
  val coreReplayCount = RegInit(0.U(32.W))
  val dcacheRetryCount = RegInit(0.U(32.W))
  val aAcceptedCount = RegInit(0.U(32.W))
  val dCompletedCount = RegInit(0.U(32.W))
  val retireCount = RegInit(0.U(32.W))
  val storeAuthorizedCount = RegInit(0.U(32.W))
  val committedLoadCount = RegInit(0.U(32.W))
  val committedStoreCount = RegInit(0.U(32.W))
  val nonCommittedCount = RegInit(0.U(32.W))
  val unknownCount = RegInit(0.U(32.W))
  val violationCount = RegInit(0.U(32.W))

  val lastClassification = RegInit(RocketLifecycleClassification.None.U(3.W))
  val lastViolation = RegInit(RocketLifecycleViolation.None.U(4.W))
  val lastEpoch = RegInit(0.U(epochWidth.W))
  val lastSequence = RegInit(0.U(sequenceWidth.W))
  val lastPc = RegInit(0.U(64.W))

  val eventMatchesActive = active && io.metadataPresent &&
    io.eventEpoch === activeEpoch && io.eventSequence === activeSequence
  val eventMatchesTerminal = terminalValid && io.metadataPresent &&
    io.eventEpoch === terminalEpoch && io.eventSequence === terminalSequence
  val maximumEpoch = ((BigInt(1) << epochWidth) - 1).U(epochWidth.W)
  val maximumSequence = ((BigInt(1) << sequenceWidth) - 1).U(sequenceWidth.W)

  def recordViolation(code: UInt, unknown: Bool = false.B): Unit = {
    violationCount := violationCount + 1.U
    when(unknown) {
      unknownCount := unknownCount + 1.U
      lastClassification := RocketLifecycleClassification.Unknown.U
    }.otherwise {
      lastClassification := RocketLifecycleClassification.Violation.U
    }
    lastViolation := code
    lastEpoch := io.eventEpoch
    lastSequence := io.eventSequence
  }

  def terminalize(fatal: Bool): Unit = {
    active := false.B
    terminalValid := true.B
    terminalEpoch := activeEpoch
    terminalSequence := activeSequence
    terminalAAccepted := activeAAccepted
    terminalFatal := fatal
    nonCommittedCount := nonCommittedCount + 1.U
    lastClassification := RocketLifecycleClassification.NonCommitted.U
    lastViolation := RocketLifecycleViolation.None.U
    lastEpoch := activeEpoch
    lastSequence := activeSequence
    lastPc := activePc
  }

  when(io.eventValid) {
    when(io.eventKind >= RocketLifecycleEvent.Count.U) {
      recordViolation(RocketLifecycleViolation.UnexpectedEvent.U)
    }.elsewhen(io.eventKind === RocketLifecycleEvent.Allocate.U) {
      when(!io.metadataPresent) {
        recordViolation(RocketLifecycleViolation.MissingMetadata.U, true.B)
      }.elsewhen(active) {
        recordViolation(RocketLifecycleViolation.DuplicateToken.U)
      }.elsewhen(sequenceExhausted) {
        recordViolation(RocketLifecycleViolation.SequenceExhausted.U)
      }.elsewhen(epochExhausted) {
        recordViolation(RocketLifecycleViolation.EpochExhausted.U)
      }.elsewhen(io.eventEpoch =/= currentEpoch) {
        recordViolation(RocketLifecycleViolation.StaleEpoch.U)
      }.elsewhen(io.eventSequence =/= nextSequence) {
        recordViolation(RocketLifecycleViolation.DuplicateToken.U)
      }.otherwise {
        active := true.B
        activeEpoch := io.eventEpoch
        activeSequence := io.eventSequence
        activeStore := io.eventStore
        activePc := io.eventPc
        activeCoreAttempt := false.B
        activeAAccepted := false.B
        activeDCompleted := false.B
        activeRetired := false.B
        activeStoreAuthorized := false.B
        allocatedCount := allocatedCount + 1.U
        lastClassification := RocketLifecycleClassification.None.U
        lastViolation := RocketLifecycleViolation.None.U
        lastEpoch := io.eventEpoch
        lastSequence := io.eventSequence
        lastPc := io.eventPc
        when(io.eventSequence === maximumSequence) {
          sequenceExhausted := true.B
        }.otherwise {
          nextSequence := io.eventSequence + 1.U
        }
      }
    }.elsewhen(!io.metadataPresent) {
      recordViolation(RocketLifecycleViolation.MissingMetadata.U, true.B)
    }.elsewhen(eventMatchesActive) {
      val validDCompletion =
        io.eventKind === RocketLifecycleEvent.DComplete.U &&
          activeAAccepted && !activeDCompleted
      val validRetirement =
        io.eventKind === RocketLifecycleEvent.Retire.U && !activeRetired
      val validStoreAuthorization =
        io.eventKind === RocketLifecycleEvent.StoreAuthorize.U &&
          activeStore && !activeStoreAuthorized
      val commitEligibleEvent =
        validDCompletion || validRetirement || validStoreAuthorization
      val loadWillCommit = !activeStore &&
        (activeDCompleted || validDCompletion) &&
        (activeRetired || validRetirement) &&
        commitEligibleEvent
      val storeWillCommit = activeStore &&
        (activeDCompleted || validDCompletion) &&
        (activeRetired || validRetirement) &&
        (activeStoreAuthorized || validStoreAuthorization) &&
        commitEligibleEvent

      switch(io.eventKind) {
        is(RocketLifecycleEvent.CoreAttempt.U) {
          when(activeCoreAttempt) {
            recordViolation(RocketLifecycleViolation.InvalidTransition.U)
          }.otherwise {
            activeCoreAttempt := true.B
            coreAttemptCount := coreAttemptCount + 1.U
          }
        }
        is(RocketLifecycleEvent.CoreReplay.U) {
          when(!activeCoreAttempt) {
            recordViolation(RocketLifecycleViolation.InvalidTransition.U)
          }.otherwise {
            coreReplayCount := coreReplayCount + 1.U
          }
        }
        is(RocketLifecycleEvent.DcacheRetry.U) {
          when(!activeCoreAttempt || activeDCompleted) {
            recordViolation(RocketLifecycleViolation.InvalidTransition.U)
          }.otherwise {
            dcacheRetryCount := dcacheRetryCount + 1.U
          }
        }
        is(RocketLifecycleEvent.AAccept.U) {
          when(!activeCoreAttempt || activeAAccepted) {
            recordViolation(RocketLifecycleViolation.InvalidTransition.U)
          }.otherwise {
            activeAAccepted := true.B
            aAcceptedCount := aAcceptedCount + 1.U
          }
        }
        is(RocketLifecycleEvent.DComplete.U) {
          when(!activeAAccepted || activeDCompleted) {
            recordViolation(RocketLifecycleViolation.InvalidTransition.U)
          }.otherwise {
            activeDCompleted := true.B
            dCompletedCount := dCompletedCount + 1.U
          }
        }
        is(RocketLifecycleEvent.DError.U) {
          when(!activeAAccepted || activeDCompleted) {
            recordViolation(RocketLifecycleViolation.InvalidTransition.U)
          }.otherwise {
            activeDCompleted := true.B
            dCompletedCount := dCompletedCount + 1.U
            terminalize(true.B)
          }
        }
        is(RocketLifecycleEvent.Retire.U) {
          when(activeRetired) {
            recordViolation(RocketLifecycleViolation.DuplicateOutcome.U)
          }.otherwise {
            activeRetired := true.B
            retireCount := retireCount + 1.U
          }
        }
        is(RocketLifecycleEvent.StoreAuthorize.U) {
          when(!activeStore || activeStoreAuthorized) {
            recordViolation(RocketLifecycleViolation.InvalidTransition.U)
          }.otherwise {
            activeStoreAuthorized := true.B
            storeAuthorizedCount := storeAuthorizedCount + 1.U
          }
        }
        is(RocketLifecycleEvent.Kill.U) {
          terminalize(false.B)
        }
        is(RocketLifecycleEvent.Exception.U) {
          terminalize(true.B)
        }
        is(RocketLifecycleEvent.Rollback.U) {
          terminalize(true.B)
        }
        is(RocketLifecycleEvent.Redirect.U) {
          terminalize(true.B)
          when(currentEpoch === maximumEpoch) {
            epochExhausted := true.B
            recordViolation(RocketLifecycleViolation.EpochExhausted.U)
          }.otherwise {
            currentEpoch := currentEpoch + 1.U
            nextSequence := 1.U
            sequenceExhausted := false.B
          }
        }
        is(RocketLifecycleEvent.ResetInvalidate.U) {
          terminalize(true.B)
          when(currentEpoch === maximumEpoch) {
            epochExhausted := true.B
            recordViolation(RocketLifecycleViolation.EpochExhausted.U)
          }.otherwise {
            currentEpoch := currentEpoch + 1.U
            nextSequence := 1.U
            sequenceExhausted := false.B
          }
        }
      }

      when(loadWillCommit || storeWillCommit) {
        active := false.B
        terminalValid := true.B
        terminalEpoch := activeEpoch
        terminalSequence := activeSequence
        terminalAAccepted := activeAAccepted
        terminalFatal := false.B
        when(loadWillCommit) {
          committedLoadCount := committedLoadCount + 1.U
          lastClassification := RocketLifecycleClassification.CommittedLoad.U
        }.otherwise {
          committedStoreCount := committedStoreCount + 1.U
          lastClassification := RocketLifecycleClassification.CommittedStore.U
        }
        lastViolation := RocketLifecycleViolation.None.U
        lastEpoch := activeEpoch
        lastSequence := activeSequence
        lastPc := activePc
      }
    }.elsewhen(io.eventEpoch =/= currentEpoch) {
      recordViolation(RocketLifecycleViolation.StaleEpoch.U)
      when(io.eventKind === RocketLifecycleEvent.DComplete.U ||
          io.eventKind === RocketLifecycleEvent.DError.U) {
        dCompletedCount := dCompletedCount + 1.U
      }
    }.elsewhen(eventMatchesTerminal) {
      when(
        (io.eventKind === RocketLifecycleEvent.DComplete.U ||
          io.eventKind === RocketLifecycleEvent.DError.U) &&
          terminalAAccepted && terminalFatal
      ) {
        dCompletedCount := dCompletedCount + 1.U
        recordViolation(RocketLifecycleViolation.PostTerminalSideEffect.U)
      }.otherwise {
        recordViolation(RocketLifecycleViolation.DuplicateOutcome.U)
      }
    }.otherwise {
      recordViolation(RocketLifecycleViolation.TokenMismatch.U)
    }
  }

  when(!reset.asBool) {
    assert(committedLoadCount + committedStoreCount <= retireCount)
    assert(committedLoadCount + committedStoreCount <= dCompletedCount)
    assert(committedStoreCount <= storeAuthorizedCount)
    assert(allocatedCount === committedLoadCount + committedStoreCount +
      nonCommittedCount + active.asUInt)
    when(active) {
      assert(activeEpoch === currentEpoch)
    }
  }

  io.active := active
  io.currentEpoch := currentEpoch
  io.nextSequence := nextSequence
  io.sequenceExhausted := sequenceExhausted
  io.epochExhausted := epochExhausted
  io.allocatedCount := allocatedCount
  io.coreAttemptCount := coreAttemptCount
  io.coreReplayCount := coreReplayCount
  io.dcacheRetryCount := dcacheRetryCount
  io.aAcceptedCount := aAcceptedCount
  io.dCompletedCount := dCompletedCount
  io.retireCount := retireCount
  io.storeAuthorizedCount := storeAuthorizedCount
  io.committedLoadCount := committedLoadCount
  io.committedStoreCount := committedStoreCount
  io.nonCommittedCount := nonCommittedCount
  io.unknownCount := unknownCount
  io.violationCount := violationCount
  io.lastClassification := lastClassification
  io.lastViolation := lastViolation
  io.lastEpoch := lastEpoch
  io.lastSequence := lastSequence
  io.lastPc := lastPc
}

object EmitRaveilRocketLifecycleObserver extends App {
  ChiselStage.emitSystemVerilogFile(
    new RaveilRocketLifecycleObserver(epochWidth = 4, sequenceWidth = 4),
    args = Array("--target-dir", "generated_rocket_lifecycle_observer"),
    firtoolOpts = Array("-disable-all-randomization", "-strip-debug-info")
  )
}
