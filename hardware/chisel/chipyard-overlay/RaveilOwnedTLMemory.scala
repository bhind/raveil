package chipyard.raveil

import chisel3._
import chisel3.util._
import org.chipsalliance.cde.config.{Config, Field, Parameters}
import freechips.rocketchip.diplomacy._
import freechips.rocketchip.subsystem._
import freechips.rocketchip.tilelink._
import freechips.rocketchip.util._
import chipyard.BuildSystem

case class RaveilOwnedMemoryParams(
  base: BigInt = 0x08000000L,
  size: BigInt = 64 * 1024,
  controlBase: BigInt = 0x08010000L,
  controlSize: BigInt = 4 * 1024,
  expectedClientSourceStart: Int = 0,
  expectedClientSourceEnd: Int = 1,
  validWords: Option[Int] = None,
  controlledRun: Boolean = false,
  repeatedControlledRun: Boolean = false,
  fateAuditAddress: Option[BigInt] = None,
  tokenAuditAddress: Option[BigInt] = None,
  // The first CPU adapter deliberately uses the uncached peripheral path so
  // mapped accesses are intended to reach the owned manager. CPU execution is
  // still unverified. Moving this boundary to a matched local-memory resource
  // is later work and must not be inferred from functional elaboration.
  busWhere: TLBusWrapperLocation = PBUS
)

case object RaveilOwnedMemoryKey
  extends Field[Option[RaveilOwnedMemoryParams]](None)

object RaveilOwnedMemoryPhase {
  val Installation = 0
  val Staging = 1
  val Execution = 2
  val Completion = 3
  val Validation = 4
  val Publication = 5
  val Fallback = 6
  val Count = 7
}

case object RaveilDCacheOrigin extends DataKey[Bool]("raveil_dcache_origin")

case class RaveilDCacheOriginField()
    extends SimpleBundleField[Bool](RaveilDCacheOrigin)(Output(Bool()), false.B)

/**
  * Owned 32-bit, maximum-one-outstanding TileLink manager.
  *
  * The manager accepts post-fragmenter Get, PutFull, and PutPartial requests
  * from the uncached peripheral path.
  * A response is available one manager-local cycle after acceptance and is
  * held until D-channel consumption. A separate idempotent control page lets
  * tracked CPU software label subsequent data requests with a lifecycle phase.
  * This adapter does not establish end-to-end CPU latency or resource matching.
  */
class RaveilOwnedTLMemory(params: RaveilOwnedMemoryParams)(implicit p: Parameters)
    extends LazyModule {
  private val beatBytes = 4

  require(isPow2(params.size))
  require(isPow2(params.controlSize))
  require(params.base % params.size == 0)
  require(params.controlBase % params.controlSize == 0)
  require(params.base + params.size <= params.controlBase)
  require(params.expectedClientSourceStart >= 0)
  require(params.expectedClientSourceEnd > params.expectedClientSourceStart)
  require(!params.repeatedControlledRun || params.controlledRun)
  params.fateAuditAddress.foreach { address =>
    require(address >= params.base && address < params.base + params.size)
    require(address % beatBytes == 0)
  }
  params.tokenAuditAddress.foreach { address =>
    require(address >= params.base && address < params.base + params.size)
    require(address % beatBytes == 0)
  }

  private val words = (params.size / beatBytes).toInt
  private val validWords = params.validWords.getOrElse(words)
  require(validWords > 0 && validWords <= words)
  private val device = new SimpleDevice(
    "raveil-owned-memory",
    Seq("raveil,owned-local-memory-v1")
  )

  val node = TLManagerNode(Seq(TLSlavePortParameters.v1(
    managers = Seq(TLSlaveParameters.v1(
      address = Seq(
        AddressSet(params.base, params.size - 1),
        AddressSet(params.controlBase, params.controlSize - 1)
      ),
      resources = device.reg,
      regionType = RegionType.IDEMPOTENT,
      executable = false,
      supportsGet = TransferSizes(1, beatBytes),
      supportsPutPartial = TransferSizes(1, beatBytes),
      supportsPutFull = TransferSizes(1, beatBytes),
      mayDenyPut = true,
      fifoId = Some(0)
    )),
    beatBytes = beatBytes,
    minLatency = 1,
    requestKeys = Seq(
      RaveilDCacheOrigin,
      RaveilCpuTokenValid,
      RaveilCpuTokenEpoch,
      RaveilCpuTokenSequence)
  )))

  lazy val module = new LazyModuleImp(this) {
    val (tl, _) = node.in(0)
    val memory = SyncReadMem(words, Vec(beatBytes, UInt(8.W)))

    val busy = RegInit(false.B)
    val responseDue = RegNext(tl.a.fire, false.B)
    val responseHeld = RegInit(false.B)
    val responseHeldData = RegInit(0.U(32.W))
    val responseControlData = RegInit(0.U(32.W))
    val responseRead = RegInit(false.B)
    val responseError = RegInit(false.B)
    val responseSource = RegInit(0.U(tl.d.bits.source.getWidth.W))
    val responseSize = RegInit(0.U(tl.d.bits.size.getWidth.W))
    val responseWordIndex = RegInit(0.U(log2Ceil(words).W))
    val responseIsData = RegInit(false.B)
    val responsePhase = RegInit(RaveilOwnedMemoryPhase.Installation.U(3.W))
    val responseExpectedClient = RegInit(false.B)
    val responseDcacheOrigin = RegInit(false.B)
    val responseFateAudit = RegInit(false.B)
    val responseFateAuditSequence = RegInit(0.U(16.W))
    val responseFateAuditOpcode = RegInit(0.U(tl.a.bits.opcode.getWidth.W))
    val responseTokenAudit = RegInit(false.B)
    val responseTokenValid = RegInit(false.B)
    val responseTokenEpoch = RegInit(0.U(16.W))
    val responseTokenSequence = RegInit(0.U(32.W))

    val phase = RegInit(RaveilOwnedMemoryPhase.Installation.U(3.W))
    val globalCycle = RegInit(0.U(64.W))
    val phaseCycleCounts = RegInit(
      VecInit(Seq.fill(RaveilOwnedMemoryPhase.Count)(0.U(64.W))))
    val acceptedCount = RegInit(0.U(32.W))
    val completedCount = RegInit(0.U(32.W))
    val phaseReadCounts = RegInit(VecInit(Seq.fill(RaveilOwnedMemoryPhase.Count)(0.U(32.W))))
    val phaseWriteCounts = RegInit(VecInit(Seq.fill(RaveilOwnedMemoryPhase.Count)(0.U(32.W))))
    val expectedAcceptedCount = RegInit(0.U(32.W))
    val expectedCompletedCount = RegInit(0.U(32.W))
    val unexpectedAcceptedCount = RegInit(0.U(32.W))
    val unexpectedCompletedCount = RegInit(0.U(32.W))
    val dcacheOriginAcceptedCount = RegInit(0.U(32.W))
    val dcacheOriginCompletedCount = RegInit(0.U(32.W))
    val nonDcacheOriginAcceptedCount = RegInit(0.U(32.W))
    val nonDcacheOriginCompletedCount = RegInit(0.U(32.W))
    val lastDcacheOriginAcceptedSource = RegInit(0.U(32.W))
    val lastDcacheOriginCompletedSource = RegInit(0.U(32.W))
    val lastDcacheOriginAcceptedPhase =
      RegInit(RaveilOwnedMemoryPhase.Installation.U(3.W))
    val lastDcacheOriginCompletedPhase =
      RegInit(RaveilOwnedMemoryPhase.Installation.U(3.W))
    val lastNonDcacheOriginAcceptedSource = RegInit(0.U(32.W))
    val lastNonDcacheOriginCompletedSource = RegInit(0.U(32.W))
    val lastNonDcacheOriginAcceptedPhase =
      RegInit(RaveilOwnedMemoryPhase.Installation.U(3.W))
    val lastNonDcacheOriginCompletedPhase =
      RegInit(RaveilOwnedMemoryPhase.Installation.U(3.W))
    val lastAcceptedSource = RegInit(0.U(32.W))
    val lastCompletedSource = RegInit(0.U(32.W))
    val lastAcceptedPhase = RegInit(RaveilOwnedMemoryPhase.Installation.U(3.W))
    val lastCompletedPhase = RegInit(RaveilOwnedMemoryPhase.Installation.U(3.W))
    val fateAuditNextSequence = RegInit(1.U(16.W))
    val executionStartCycle = RegInit(0.U(64.W))
    val executionStartAccepted = RegInit(0.U(32.W))
    val executionStartCompleted = RegInit(0.U(32.W))
    val executionStartExpectedAccepted = RegInit(0.U(32.W))
    val executionStartExpectedCompleted = RegInit(0.U(32.W))
    val executionStartUnexpectedAccepted = RegInit(0.U(32.W))
    val executionStartUnexpectedCompleted = RegInit(0.U(32.W))
    val executionStartOriginAccepted = RegInit(0.U(32.W))
    val executionStartOriginCompleted = RegInit(0.U(32.W))
    val executionStartNonOriginAccepted = RegInit(0.U(32.W))
    val executionStartNonOriginCompleted = RegInit(0.U(32.W))
    val stagingStartCycle = RegInit(0.U(64.W))
    val completionStartCycle = RegInit(0.U(64.W))
    val validationStartCycle = RegInit(0.U(64.W))
    val executionRequestStallCycles = RegInit(0.U(64.W))
    val executionResponseBackpressureCycles = RegInit(0.U(64.W))
    val invocationPhaseReadCounts = RegInit(
      VecInit(Seq.fill(RaveilOwnedMemoryPhase.Count)(0.U(32.W))))
    val invocationPhaseWriteCounts = RegInit(
      VecInit(Seq.fill(RaveilOwnedMemoryPhase.Count)(0.U(32.W))))
    val controlledInvocation = RegInit(1.U(32.W))
    val invocationStartCycle = RegInit(0.U(64.W))
    val invocationStartAccepted = RegInit(0.U(32.W))
    val invocationStartCompleted = RegInit(0.U(32.W))
    val activePhaseReadCounts = if (params.repeatedControlledRun) {
      invocationPhaseReadCounts
    } else {
      phaseReadCounts
    }
    val activePhaseWriteCounts = if (params.repeatedControlledRun) {
      invocationPhaseWriteCounts
    } else {
      phaseWriteCounts
    }

    globalCycle := globalCycle + 1.U
    phaseCycleCounts(phase) := phaseCycleCounts(phase) + 1.U

    val requestAddress = tl.a.bits.address
    val dataRequest = requestAddress >= params.base.U &&
      requestAddress < (params.base + params.size).U
    val controlRequest = requestAddress >= params.controlBase.U &&
      requestAddress < (params.controlBase + params.controlSize).U
    val controlOffset = requestAddress - params.controlBase.U
    val get = tl.a.bits.opcode === TLMessages.Get
    val put = tl.a.bits.opcode === TLMessages.PutFullData ||
      tl.a.bits.opcode === TLMessages.PutPartialData
    val supported = (dataRequest || controlRequest) && (get || put)
    val controlledWordRequest = if (params.controlledRun) {
      tl.a.bits.size === log2Ceil(beatBytes).U
    } else {
      true.B
    }
    val phaseWrite = controlRequest && put && controlOffset === 0.U
    val phaseValueValid = tl.a.bits.data(2, 0) < RaveilOwnedMemoryPhase.Count.U
    val phaseByteEnabled = tl.a.bits.mask(0)
    val wordIndex = ((requestAddress - params.base.U) >> 2)(log2Ceil(words) - 1, 0)
    val requestError = !supported ||
      (dataRequest && wordIndex >= validWords.U) ||
      (dataRequest && !controlledWordRequest) ||
      (phaseWrite && (!phaseByteEnabled || !phaseValueValid))
    val expectedClientRequest =
      tl.a.bits.source >= params.expectedClientSourceStart.U &&
      tl.a.bits.source < params.expectedClientSourceEnd.U
    val dcacheOriginRequest =
      tl.a.bits.user.lift(RaveilDCacheOrigin).getOrElse(false.B)
    val accountingPhase = WireDefault(phase)
    if (params.controlledRun) {
      when(dataRequest && dcacheOriginRequest &&
          phase === RaveilOwnedMemoryPhase.Installation.U) {
        accountingPhase := RaveilOwnedMemoryPhase.Staging.U
      }
      when(dataRequest && get && !requestError && wordIndex === 324.U &&
          phase === RaveilOwnedMemoryPhase.Completion.U) {
        accountingPhase := RaveilOwnedMemoryPhase.Validation.U
      }
    }

    val memoryRead = tl.a.fire && dataRequest && get && !requestError
    val readBytes = memory.read(wordIndex, memoryRead)
    val freshReadData = readBytes.asUInt

    val controlReadData = WireDefault(0.U(32.W))
    when(controlOffset === 0.U) { controlReadData := phase }
    when(controlOffset === 4.U) { controlReadData := acceptedCount }
    when(controlOffset === 8.U) { controlReadData := completedCount }
    when(controlOffset === 12.U) { controlReadData := busy }
    for (index <- 0 until RaveilOwnedMemoryPhase.Count) {
      when(controlOffset === (0x10 + index * 8).U) {
        controlReadData := phaseReadCounts(index)
      }
      when(controlOffset === (0x14 + index * 8).U) {
        controlReadData := phaseWriteCounts(index)
      }
    }
    when(controlOffset === 0x50.U) { controlReadData := params.expectedClientSourceStart.U }
    when(controlOffset === 0x54.U) { controlReadData := params.expectedClientSourceEnd.U }
    when(controlOffset === 0x58.U) { controlReadData := expectedAcceptedCount }
    when(controlOffset === 0x5c.U) { controlReadData := expectedCompletedCount }
    when(controlOffset === 0x60.U) { controlReadData := unexpectedAcceptedCount }
    when(controlOffset === 0x64.U) { controlReadData := unexpectedCompletedCount }
    when(controlOffset === 0x68.U) { controlReadData := lastAcceptedSource }
    when(controlOffset === 0x6c.U) { controlReadData := lastCompletedSource }
    when(controlOffset === 0x70.U) { controlReadData := lastAcceptedPhase }
    when(controlOffset === 0x74.U) { controlReadData := lastCompletedPhase }
    when(controlOffset === 0x78.U) { controlReadData := dcacheOriginAcceptedCount }
    when(controlOffset === 0x7c.U) { controlReadData := dcacheOriginCompletedCount }
    when(controlOffset === 0x80.U) { controlReadData := nonDcacheOriginAcceptedCount }
    when(controlOffset === 0x84.U) { controlReadData := nonDcacheOriginCompletedCount }
    when(controlOffset === 0x88.U) { controlReadData := lastDcacheOriginAcceptedSource }
    when(controlOffset === 0x8c.U) { controlReadData := lastDcacheOriginCompletedSource }
    when(controlOffset === 0x90.U) { controlReadData := lastDcacheOriginAcceptedPhase }
    when(controlOffset === 0x94.U) { controlReadData := lastDcacheOriginCompletedPhase }
    when(controlOffset === 0x98.U) { controlReadData := lastNonDcacheOriginAcceptedSource }
    when(controlOffset === 0x9c.U) { controlReadData := lastNonDcacheOriginCompletedSource }
    when(controlOffset === 0xa0.U) { controlReadData := lastNonDcacheOriginAcceptedPhase }
    when(controlOffset === 0xa4.U) { controlReadData := lastNonDcacheOriginCompletedPhase }
    val freshResponseData = Mux(responseRead && !responseIsData,
      responseControlData, freshReadData)

    tl.a.ready := !busy
    if (params.controlledRun) {
      when(phase === RaveilOwnedMemoryPhase.Execution.U &&
          tl.a.valid && !tl.a.ready) {
        executionRequestStallCycles := executionRequestStallCycles + 1.U
      }
    }
    when(tl.a.fire) {
      if (params.controlledRun) {
        when(phase === RaveilOwnedMemoryPhase.Execution.U) {
          val admittedExecutionRequest = dataRequest && !requestError &&
            dcacheOriginRequest && expectedClientRequest &&
            ((get && wordIndex < 324.U) ||
              (put && wordIndex >= 324.U && wordIndex < 580.U))
          when(!admittedExecutionRequest) {
            printf("RAVEIL-CONTROLLED-MIXED-TRAFFIC-V1 phase=%d cycle=%d address=0x%x source=%d opcode=%d dcache_origin=%d expected_source=%d request_error=%d data_request=%d execution_reads=%d execution_writes=%d accepted=%d completed=%d\n",
              phase, globalCycle, requestAddress, tl.a.bits.source,
              tl.a.bits.opcode, dcacheOriginRequest, expectedClientRequest,
              requestError, dataRequest,
              activePhaseReadCounts(RaveilOwnedMemoryPhase.Execution),
              activePhaseWriteCounts(RaveilOwnedMemoryPhase.Execution),
              acceptedCount, completedCount)
          }
          assert(admittedExecutionRequest,
            "Raveil controlled execution admitted unaccounted traffic")
        }
        when(phase === RaveilOwnedMemoryPhase.Validation.U) {
          val admittedValidationRequest = dataRequest && !requestError && get &&
            wordIndex === 324.U +
              activePhaseReadCounts(RaveilOwnedMemoryPhase.Validation)
          when(!admittedValidationRequest) {
            printf("RAVEIL-CONTROLLED-VALIDATION-TRAFFIC-V1 phase=%d cycle=%d address=0x%x source=%d opcode=%d dcache_origin=%d expected_source=%d request_error=%d validation_reads=%d accepted=%d completed=%d\n",
              phase, globalCycle, requestAddress, tl.a.bits.source,
              tl.a.bits.opcode, dcacheOriginRequest, expectedClientRequest,
              requestError,
              phaseReadCounts(RaveilOwnedMemoryPhase.Validation),
              acceptedCount, completedCount)
          }
          assert(admittedValidationRequest,
            "Raveil controlled validation admitted unaccounted traffic")
        }
        when(phase === RaveilOwnedMemoryPhase.Publication.U) {
          assert(false.B,
            "Raveil controlled publication admitted request traffic")
        }
      }
      busy := true.B
      responseRead := get
      responseError := requestError
      responseSource := tl.a.bits.source
      responseSize := tl.a.bits.size
      responseWordIndex := wordIndex
      responseIsData := dataRequest
      responsePhase := accountingPhase
      responseExpectedClient := expectedClientRequest
      responseDcacheOrigin := dcacheOriginRequest
      responseFateAudit := false.B
      responseTokenAudit := false.B
      params.fateAuditAddress.foreach { address =>
        when(requestAddress === address.U) {
          assert(fateAuditNextSequence =/= "hffff".U,
            "Raveil owned-memory fate audit sequence exhausted")
          responseFateAudit := true.B
          responseFateAuditSequence := fateAuditNextSequence
          responseFateAuditOpcode := tl.a.bits.opcode
          fateAuditNextSequence := fateAuditNextSequence + 1.U
          printf("RAVEIL-OWNED-TL-FATE-V1 event=a manager_sequence=%d address=0x%x source=%d opcode=%d size=%d dcache_origin=%d expected_source=%d phase=%d\n",
            fateAuditNextSequence, requestAddress, tl.a.bits.source,
            tl.a.bits.opcode, tl.a.bits.size, dcacheOriginRequest,
            expectedClientRequest, phase)
        }
      }
      params.tokenAuditAddress.foreach { address =>
        val tokenValid = tl.a.bits.user(RaveilCpuTokenValid)
        val tokenEpoch = tl.a.bits.user(RaveilCpuTokenEpoch)
        val tokenSequence = tl.a.bits.user(RaveilCpuTokenSequence)
        val tokenWellFormed = tokenValid && tokenEpoch =/= 0.U &&
          tokenSequence =/= 0.U
        when(dataRequest && put && requestAddress === address.U) {
          responseTokenAudit := true.B
          responseTokenValid := tokenWellFormed
          responseTokenEpoch := tokenEpoch
          responseTokenSequence := tokenSequence
          printf("RAVEIL-OWNED-TL-TOKEN-V1 event=a valid=%d epoch=%d sequence=%d address=0x%x source=%d opcode=%d size=%d dcache_origin=%d classification=%d\n",
            tokenWellFormed, tokenEpoch, tokenSequence, requestAddress,
            tl.a.bits.source, tl.a.bits.opcode, tl.a.bits.size,
            dcacheOriginRequest, Mux(tokenWellFormed, 1.U, 0.U))
        }
      }
      when(controlRequest && get) {
        responseControlData := controlReadData
      }

      when(dataRequest && !requestError) {
        if (params.controlledRun) {
          when(accountingPhase === RaveilOwnedMemoryPhase.Staging.U) {
            assert(dcacheOriginRequest && expectedClientRequest && put,
              "Raveil controlled staging traffic changed")
            assert(wordIndex === activePhaseWriteCounts(RaveilOwnedMemoryPhase.Staging),
              "Raveil controlled staging address order changed")
            assert(activePhaseWriteCounts(RaveilOwnedMemoryPhase.Staging) < 324.U,
              "Raveil controlled staging traffic exceeded 324 words")
          }
          when(accountingPhase === RaveilOwnedMemoryPhase.Execution.U) {
            when(!(dcacheOriginRequest && expectedClientRequest)) {
              printf("RAVEIL-CONTROLLED-MIXED-TRAFFIC-V1 phase=%d cycle=%d address=0x%x source=%d opcode=%d dcache_origin=%d expected_source=%d execution_reads=%d execution_writes=%d accepted=%d completed=%d\n",
                accountingPhase, globalCycle, requestAddress, tl.a.bits.source,
                tl.a.bits.opcode, dcacheOriginRequest, expectedClientRequest,
                activePhaseReadCounts(RaveilOwnedMemoryPhase.Execution),
                activePhaseWriteCounts(RaveilOwnedMemoryPhase.Execution),
                acceptedCount, completedCount)
            }
            assert(dcacheOriginRequest && expectedClientRequest,
              "Raveil controlled execution admitted mixed traffic")
            assert(
              (get && wordIndex < 324.U) ||
              (put && wordIndex >= 324.U && wordIndex < 580.U),
              "Raveil controlled execution operation or region changed")
            assert(
              activePhaseReadCounts(RaveilOwnedMemoryPhase.Execution) +
                activePhaseWriteCounts(RaveilOwnedMemoryPhase.Execution) < 1056.U,
              "Raveil controlled execution traffic exceeded the frozen workload")
          }
          when(accountingPhase === RaveilOwnedMemoryPhase.Validation.U) {
            when(!get) {
              printf("RAVEIL-CONTROLLED-VALIDATION-TRAFFIC-V1 phase=%d cycle=%d address=0x%x source=%d opcode=%d dcache_origin=%d expected_source=%d request_error=%d validation_reads=%d accepted=%d completed=%d\n",
                accountingPhase, globalCycle, requestAddress, tl.a.bits.source,
                tl.a.bits.opcode, dcacheOriginRequest, expectedClientRequest,
                requestError,
                activePhaseReadCounts(RaveilOwnedMemoryPhase.Validation),
                acceptedCount, completedCount)
            }
            assert(get,
              "Raveil controlled validation traffic changed")
            assert(
              wordIndex === 324.U +
                activePhaseReadCounts(RaveilOwnedMemoryPhase.Validation),
              "Raveil controlled validation address order changed")
            assert(activePhaseReadCounts(RaveilOwnedMemoryPhase.Validation) < 256.U,
              "Raveil controlled validation traffic exceeded 256 words")
          }
          when(phase === RaveilOwnedMemoryPhase.Publication.U) {
            assert(false.B,
              "Raveil controlled publication admitted data traffic")
          }
        }
        acceptedCount := acceptedCount + 1.U
        lastAcceptedSource := tl.a.bits.source
        lastAcceptedPhase := accountingPhase
        when(expectedClientRequest) {
          expectedAcceptedCount := expectedAcceptedCount + 1.U
        }.otherwise {
          unexpectedAcceptedCount := unexpectedAcceptedCount + 1.U
        }
        when(dcacheOriginRequest) {
          dcacheOriginAcceptedCount := dcacheOriginAcceptedCount + 1.U
          lastDcacheOriginAcceptedSource := tl.a.bits.source
          lastDcacheOriginAcceptedPhase := accountingPhase
        }.otherwise {
          nonDcacheOriginAcceptedCount := nonDcacheOriginAcceptedCount + 1.U
          lastNonDcacheOriginAcceptedSource := tl.a.bits.source
          lastNonDcacheOriginAcceptedPhase := accountingPhase
        }
        when(get) {
          phaseReadCounts(accountingPhase) := phaseReadCounts(accountingPhase) + 1.U
          if (params.repeatedControlledRun) {
            invocationPhaseReadCounts(accountingPhase) :=
              invocationPhaseReadCounts(accountingPhase) + 1.U
          }
        }.otherwise {
          phaseWriteCounts(accountingPhase) := phaseWriteCounts(accountingPhase) + 1.U
          if (params.repeatedControlledRun) {
            invocationPhaseWriteCounts(accountingPhase) :=
              invocationPhaseWriteCounts(accountingPhase) + 1.U
          }
          val writeBytes = Wire(Vec(beatBytes, UInt(8.W)))
          for (byte <- 0 until beatBytes) {
            writeBytes(byte) := tl.a.bits.data(8 * byte + 7, 8 * byte)
          }
          memory.write(wordIndex, writeBytes, tl.a.bits.mask.asBools)
        }
      }
      if (params.controlledRun) {
        assert(!phaseWrite,
          "Raveil controlled run uses structural boundaries, not software phase writes")
        when(dataRequest && !requestError && dcacheOriginRequest &&
            phase === RaveilOwnedMemoryPhase.Installation.U) {
          phase := RaveilOwnedMemoryPhase.Staging.U
          stagingStartCycle := globalCycle
          if (params.repeatedControlledRun) {
            printf("RAVEIL-REPEATED-PHASE-V1 invocation=1 from=0 to=1 cycle=%d accepted=%d completed=%d busy_before=%d publication_cycles=0\n",
              globalCycle, acceptedCount, completedCount, busy)
          } else {
            printf("RAVEIL-CONTROLLED-PHASE-V1 from=0 to=1 cycle=%d accepted=%d completed=%d busy_before=%d\n",
              globalCycle, acceptedCount, completedCount, busy)
          }
        }
        when(phase === RaveilOwnedMemoryPhase.Completion.U) {
          assert(dataRequest && !requestError && get && wordIndex === 324.U,
            "Raveil controlled validation did not start at the exact output base")
        }
        when(dataRequest && !requestError && get && wordIndex === 324.U &&
            phase === RaveilOwnedMemoryPhase.Completion.U) {
          phase := RaveilOwnedMemoryPhase.Validation.U
          validationStartCycle := globalCycle
          if (params.repeatedControlledRun) {
            printf("RAVEIL-REPEATED-PHASE-V1 invocation=%d from=3 to=4 cycle=%d accepted=%d completed=%d busy_before=%d publication_cycles=0\n",
              controlledInvocation, globalCycle, acceptedCount, completedCount, busy)
          } else {
            printf("RAVEIL-CONTROLLED-PHASE-V1 from=3 to=4 cycle=%d accepted=%d completed=%d busy_before=%d\n",
              globalCycle, acceptedCount, completedCount, busy)
          }
        }
      }
      when(phaseWrite && phaseByteEnabled && phaseValueValid) {
        phase := tl.a.bits.data(2, 0)
      }
    }

    val responseValid = responseDue || responseHeld
    val responseData = Mux(responseHeld, responseHeldData, freshResponseData)
    tl.d.valid := responseValid
    if (params.controlledRun) {
      when(responsePhase === RaveilOwnedMemoryPhase.Execution.U &&
          responseValid && !tl.d.ready) {
        executionResponseBackpressureCycles :=
          executionResponseBackpressureCycles + 1.U
      }
    }
    tl.d.bits.opcode := Mux(responseRead, TLMessages.AccessAckData, TLMessages.AccessAck)
    tl.d.bits.param := 0.U
    tl.d.bits.size := responseSize
    tl.d.bits.source := responseSource
    tl.d.bits.sink := 0.U
    tl.d.bits.denied := responseError
    tl.d.bits.data := Mux(responseRead, responseData, 0.U)
    tl.d.bits.corrupt := responseError && responseRead
    when(responseDue && !tl.d.ready) {
      responseHeld := true.B
      responseHeldData := freshResponseData
    }
    when(tl.d.fire) {
      when(responseTokenAudit) {
        printf("RAVEIL-OWNED-TL-TOKEN-V1 event=d valid=%d epoch=%d sequence=%d source=%d opcode=%d size=%d denied=%d corrupt=%d classification=%d\n",
          responseTokenValid, responseTokenEpoch, responseTokenSequence,
          tl.d.bits.source, tl.d.bits.opcode, tl.d.bits.size,
          tl.d.bits.denied, tl.d.bits.corrupt,
          Mux(responseTokenValid && !tl.d.bits.denied && !tl.d.bits.corrupt,
            1.U, 0.U))
      }
      when(responseFateAudit) {
        printf("RAVEIL-OWNED-TL-FATE-V1 event=d manager_sequence=%d source=%d opcode=%d size=%d denied=%d corrupt=%d request_opcode=%d phase=%d\n",
          responseFateAuditSequence, tl.d.bits.source, tl.d.bits.opcode,
          tl.d.bits.size, tl.d.bits.denied, tl.d.bits.corrupt,
          responseFateAuditOpcode, responsePhase)
      }
      responseFateAudit := false.B
      responseTokenAudit := false.B
      responseHeld := false.B
      busy := false.B
      when(responseIsData && !responseError) {
        if (params.controlledRun) {
          when(responsePhase === RaveilOwnedMemoryPhase.Staging.U &&
              activePhaseWriteCounts(RaveilOwnedMemoryPhase.Staging) === 324.U) {
            assert(acceptedCount === completedCount + 1.U,
              "Raveil controlled execution did not start quiescent")
            phase := RaveilOwnedMemoryPhase.Execution.U
            executionStartCycle := globalCycle
            executionStartAccepted := acceptedCount
            executionStartCompleted := completedCount + 1.U
            executionStartExpectedAccepted := expectedAcceptedCount
            executionStartExpectedCompleted := expectedCompletedCount + 1.U
            executionStartUnexpectedAccepted := unexpectedAcceptedCount
            executionStartUnexpectedCompleted := unexpectedCompletedCount
            executionStartOriginAccepted := dcacheOriginAcceptedCount
            executionStartOriginCompleted := dcacheOriginCompletedCount + 1.U
            executionStartNonOriginAccepted := nonDcacheOriginAcceptedCount
            executionStartNonOriginCompleted := nonDcacheOriginCompletedCount
            executionRequestStallCycles := 0.U
            executionResponseBackpressureCycles := 0.U
            if (params.repeatedControlledRun) {
              printf("RAVEIL-REPEATED-PHASE-V1 invocation=%d from=1 to=2 cycle=%d accepted=%d completed=%d busy_before=%d publication_cycles=0\n",
                controlledInvocation, globalCycle, acceptedCount,
                completedCount + 1.U, busy)
              printf("RAVEIL-REPEATED-RESOURCE-V1 invocation=%d resource_sha256=16664d8ed96865c60ea41c91452b5e6748b055e0dfef3f786b13bd6f90127748 data_width_bits=32 operation_width_bytes=4 request_ports=1 response_ports=1 maximum_outstanding_requests=1 request_buffer_depth=0 response_buffer_depth=1 physical_banks=1 physical_words=1024 valid_words=580 arbitration=none-at-owned-contract-ingress accepted_operations=read,write-byte-mask response_rule=one-module-local-cycle-after-acceptance response_hold=stable-until-consumed\n",
                controlledInvocation)
            } else {
              printf("RAVEIL-CONTROLLED-PHASE-V1 from=1 to=2 cycle=%d accepted=%d completed=%d busy_before=%d\n",
                globalCycle, acceptedCount, completedCount + 1.U, busy)
              printf("RAVEIL-CONTROLLED-RESOURCE-V1 resource_sha256=16664d8ed96865c60ea41c91452b5e6748b055e0dfef3f786b13bd6f90127748 data_width_bits=32 operation_width_bytes=4 request_ports=1 response_ports=1 maximum_outstanding_requests=1 request_buffer_depth=0 response_buffer_depth=1 physical_banks=1 physical_words=1024 valid_words=580 arbitration=none-at-owned-contract-ingress accepted_operations=read,write-byte-mask response_rule=one-module-local-cycle-after-acceptance response_hold=stable-until-consumed\n")
            }
          }
          when(responsePhase === RaveilOwnedMemoryPhase.Execution.U &&
              activePhaseReadCounts(RaveilOwnedMemoryPhase.Execution) === 800.U &&
              activePhaseWriteCounts(RaveilOwnedMemoryPhase.Execution) === 256.U) {
            assert(acceptedCount === completedCount + 1.U,
              "Raveil controlled execution did not end quiescent")
            phase := RaveilOwnedMemoryPhase.Completion.U
            completionStartCycle := globalCycle
            if (params.repeatedControlledRun) {
              printf("RAVEIL-REPEATED-PHASE-V1 invocation=%d from=2 to=3 cycle=%d accepted=%d completed=%d busy_before=%d publication_cycles=0\n",
                controlledInvocation, globalCycle, acceptedCount,
                completedCount + 1.U, busy)
            } else {
              printf("RAVEIL-CONTROLLED-PHASE-V1 from=2 to=3 cycle=%d accepted=%d completed=%d busy_before=%d\n",
                globalCycle, acceptedCount, completedCount + 1.U, busy)
            }
            if (params.repeatedControlledRun) {
              printf("RAVEIL-REPEATED-WINDOW-V1 invocation=%d start_cycle=%d end_cycle=%d cycles=%d accepted=%d completed=%d reads=%d writes=%d expected_accepted=%d expected_completed=%d unexpected_accepted=%d unexpected_completed=%d origin_accepted=%d origin_completed=%d nonorigin_accepted=%d nonorigin_completed=%d pending=0 quiescence_before=1 quiescence_after=1\n",
              controlledInvocation,
              executionStartCycle, globalCycle,
              globalCycle - executionStartCycle,
              acceptedCount - executionStartAccepted,
              completedCount + 1.U - executionStartCompleted,
              activePhaseReadCounts(RaveilOwnedMemoryPhase.Execution),
              activePhaseWriteCounts(RaveilOwnedMemoryPhase.Execution),
              expectedAcceptedCount - executionStartExpectedAccepted,
              expectedCompletedCount + 1.U - executionStartExpectedCompleted,
              unexpectedAcceptedCount - executionStartUnexpectedAccepted,
              unexpectedCompletedCount - executionStartUnexpectedCompleted,
              dcacheOriginAcceptedCount - executionStartOriginAccepted,
              dcacheOriginCompletedCount + 1.U - executionStartOriginCompleted,
              nonDcacheOriginAcceptedCount - executionStartNonOriginAccepted,
              nonDcacheOriginCompletedCount - executionStartNonOriginCompleted)
              printf("T0044-REPEATED-CPU-ACTIVITY-V1 invocation=%d request_stall_cycles=%d response_backpressure_cycles=%d read_transactions=800 write_transactions=256 read_bytes=3200 write_bytes=1024 useful_loads=1280 useful_adds=1024 useful_stores=256 outputs=256 frontend_activity=unavailable rename_rob_issue_lsu=unavailable\n",
                controlledInvocation, executionRequestStallCycles,
                executionResponseBackpressureCycles)
            } else {
              printf("RAVEIL-CONTROLLED-WINDOW-V1 start_cycle=%d end_cycle=%d cycles=%d accepted=%d completed=%d reads=%d writes=%d expected_accepted=%d expected_completed=%d unexpected_accepted=%d unexpected_completed=%d origin_accepted=%d origin_completed=%d nonorigin_accepted=%d nonorigin_completed=%d pending=0 quiescence_before=1 quiescence_after=1\n",
                executionStartCycle, globalCycle,
                globalCycle - executionStartCycle,
                acceptedCount - executionStartAccepted,
                completedCount + 1.U - executionStartCompleted,
                activePhaseReadCounts(RaveilOwnedMemoryPhase.Execution),
                activePhaseWriteCounts(RaveilOwnedMemoryPhase.Execution),
                expectedAcceptedCount - executionStartExpectedAccepted,
                expectedCompletedCount + 1.U - executionStartExpectedCompleted,
                unexpectedAcceptedCount - executionStartUnexpectedAccepted,
                unexpectedCompletedCount - executionStartUnexpectedCompleted,
                dcacheOriginAcceptedCount - executionStartOriginAccepted,
                dcacheOriginCompletedCount + 1.U - executionStartOriginCompleted,
                nonDcacheOriginAcceptedCount - executionStartNonOriginAccepted,
                nonDcacheOriginCompletedCount - executionStartNonOriginCompleted)
              printf("T0044-CPU-ACTIVITY-V1 request_stall_cycles=%d response_backpressure_cycles=%d read_transactions=800 write_transactions=256 read_bytes=3200 write_bytes=1024 useful_loads=1280 useful_adds=1024 useful_stores=256 outputs=256 frontend_activity=unavailable rename_rob_issue_lsu=unavailable\n",
                executionRequestStallCycles,
                executionResponseBackpressureCycles)
            }
          }
          if (params.repeatedControlledRun) {
            when(responsePhase === RaveilOwnedMemoryPhase.Validation.U) {
              printf("RAVEIL-CONTROLLED-OUTPUT-V1 invocation=%d index=%d value=%x\n",
                controlledInvocation, responseWordIndex - 324.U, responseData)
            }
          }
          when(responsePhase === RaveilOwnedMemoryPhase.Validation.U &&
              activePhaseReadCounts(RaveilOwnedMemoryPhase.Validation) === 256.U) {
            if (params.repeatedControlledRun) {
              phase := RaveilOwnedMemoryPhase.Staging.U
              printf("RAVEIL-REPEATED-PHASE-V1 invocation=%d from=4 to=1 cycle=%d accepted=%d completed=%d busy_before=%d publication_cycles=0\n",
                controlledInvocation, globalCycle, acceptedCount,
                completedCount + 1.U, busy)
              printf("RAVEIL-REPEATED-CPU-COMPLETE-V1 invocation=%d installation_cycles=%d staging_cycles=%d execution_cycles=%d completion_cycles=%d validation_cycles=%d publication_cycles=0 total_cycles=%d accepted=%d completed=%d installation_reads=%d installation_writes=%d staging_writes=%d execution_reads=%d execution_writes=%d validation_reads=%d\n",
                controlledInvocation,
                Mux(controlledInvocation === 1.U, stagingStartCycle, 0.U),
                executionStartCycle - stagingStartCycle,
                completionStartCycle - executionStartCycle,
                validationStartCycle - completionStartCycle,
                globalCycle - validationStartCycle,
                globalCycle - invocationStartCycle,
                acceptedCount - invocationStartAccepted,
                completedCount + 1.U - invocationStartCompleted,
                Mux(controlledInvocation === 1.U,
                  phaseReadCounts(RaveilOwnedMemoryPhase.Installation), 0.U),
                Mux(controlledInvocation === 1.U,
                  phaseWriteCounts(RaveilOwnedMemoryPhase.Installation), 0.U),
                activePhaseWriteCounts(RaveilOwnedMemoryPhase.Staging),
                activePhaseReadCounts(RaveilOwnedMemoryPhase.Execution),
                activePhaseWriteCounts(RaveilOwnedMemoryPhase.Execution),
                activePhaseReadCounts(RaveilOwnedMemoryPhase.Validation))
              controlledInvocation := controlledInvocation + 1.U
              invocationStartCycle := globalCycle
              invocationStartAccepted := acceptedCount
              invocationStartCompleted := completedCount + 1.U
              stagingStartCycle := globalCycle
              for (index <- 0 until RaveilOwnedMemoryPhase.Count) {
                invocationPhaseReadCounts(index) := 0.U
                invocationPhaseWriteCounts(index) := 0.U
              }
            } else {
              phase := RaveilOwnedMemoryPhase.Publication.U
              printf("RAVEIL-CONTROLLED-PHASE-V1 from=4 to=5 cycle=%d accepted=%d completed=%d busy_before=%d\n",
                globalCycle, acceptedCount, completedCount + 1.U, busy)
              printf("RAVEIL-CONTROLLED-CPU-COMPLETE-V1 installation_cycles=%d staging_cycles=%d execution_cycles=%d completion_cycles=%d validation_cycles=%d publication_cycles=0 total_cycles=%d accepted=%d completed=%d staging_writes=%d execution_reads=%d execution_writes=%d validation_reads=%d\n",
                stagingStartCycle,
                executionStartCycle - stagingStartCycle,
                completionStartCycle - executionStartCycle,
                validationStartCycle - completionStartCycle,
                globalCycle - validationStartCycle,
                globalCycle,
                acceptedCount, completedCount + 1.U,
                activePhaseWriteCounts(RaveilOwnedMemoryPhase.Staging),
                activePhaseReadCounts(RaveilOwnedMemoryPhase.Execution),
                activePhaseWriteCounts(RaveilOwnedMemoryPhase.Execution),
                activePhaseReadCounts(RaveilOwnedMemoryPhase.Validation))
            }
          }
        }
        completedCount := completedCount + 1.U
        lastCompletedSource := responseSource
        lastCompletedPhase := responsePhase
        when(responseExpectedClient) {
          expectedCompletedCount := expectedCompletedCount + 1.U
        }.otherwise {
          unexpectedCompletedCount := unexpectedCompletedCount + 1.U
        }
        when(responseDcacheOrigin) {
          dcacheOriginCompletedCount := dcacheOriginCompletedCount + 1.U
          lastDcacheOriginCompletedSource := responseSource
          lastDcacheOriginCompletedPhase := responsePhase
        }.otherwise {
          nonDcacheOriginCompletedCount := nonDcacheOriginCompletedCount + 1.U
          lastNonDcacheOriginCompletedSource := responseSource
          lastNonDcacheOriginCompletedPhase := responsePhase
        }
      }
    }

    when(!reset.asBool) {
      assert(acceptedCount === completedCount +
        (busy && responseIsData && !responseError).asUInt)
      assert(expectedAcceptedCount === expectedCompletedCount +
        (busy && responseIsData && !responseError && responseExpectedClient).asUInt)
      assert(unexpectedAcceptedCount === unexpectedCompletedCount +
        (busy && responseIsData && !responseError && !responseExpectedClient).asUInt)
      assert(dcacheOriginAcceptedCount === dcacheOriginCompletedCount +
        (busy && responseIsData && !responseError && responseDcacheOrigin).asUInt)
      assert(nonDcacheOriginAcceptedCount === nonDcacheOriginCompletedCount +
        (busy && responseIsData && !responseError && !responseDcacheOrigin).asUInt)
      when(responseHeld) {
        assert(tl.d.valid)
      }
    }

    tl.b.valid := false.B
    tl.c.ready := true.B
    tl.e.ready := true.B
  }
}

trait CanHaveRaveilOwnedMemory { this: BaseSubsystem =>
  p(RaveilOwnedMemoryKey).foreach { params =>
    val bus = locateTLBusWrapper(params.busWhere)
    val domain = bus.generateSynchronousDomain
      .suggestName("raveil_owned_memory_domain")
    val memory = domain { LazyModule(new RaveilOwnedTLMemory(params)) }
    bus.coupleTo("raveil-owned-memory") {
      domain {
        memory.node :=
          TLFragmenter(4, bus.blockBytes) :=
          TLWidthWidget(bus.beatBytes)
      } := _
    }
  }
}

class RaveilOwnedDigitalTop(implicit p: Parameters)
    extends chipyard.DigitalTop
    with CanHaveRaveilOwnedMemory

class WithRaveilOwnedBuildSystem extends Config((site, here, up) => {
  case BuildSystem => (p: Parameters) => new RaveilOwnedDigitalTop()(p)
})

class WithRaveilOwnedMemory extends Config((site, here, up) => {
  case RaveilOwnedMemoryKey => Some(RaveilOwnedMemoryParams())
})

class WithRaveilOwnedMemorySourceRange(start: Int, end: Int)
    extends Config((site, here, up) => {
  case RaveilOwnedMemoryKey => Some(RaveilOwnedMemoryParams(
    expectedClientSourceStart = start,
    expectedClientSourceEnd = end
  ))
})

class WithRaveilMatchedMemorySourceRange(start: Int, end: Int)
    extends Config((site, here, up) => {
  case RaveilOwnedMemoryKey => Some(RaveilOwnedMemoryParams(
    size = 4 * 1024,
    expectedClientSourceStart = start,
    expectedClientSourceEnd = end,
    validWords = Some(580),
    controlledRun = true
  ))
})

class WithRaveilRepeatedMatchedMemorySourceRange(start: Int, end: Int)
    extends Config((site, here, up) => {
  case RaveilOwnedMemoryKey => Some(RaveilOwnedMemoryParams(
    size = 4 * 1024,
    expectedClientSourceStart = start,
    expectedClientSourceEnd = end,
    validWords = Some(580),
    controlledRun = true,
    repeatedControlledRun = true
  ))
})

class WithRaveilOwnedMemorySourceRangeAndFateAudit(
    start: Int,
    end: Int,
    auditAddress: BigInt)
    extends Config((site, here, up) => {
  case RaveilOwnedMemoryKey => Some(RaveilOwnedMemoryParams(
    expectedClientSourceStart = start,
    expectedClientSourceEnd = end,
    fateAuditAddress = Some(auditAddress)
  ))
})

class WithRaveilOwnedMemorySourceRangeAndTokenAudit(
    start: Int,
    end: Int,
    auditAddress: BigInt)
    extends Config((site, here, up) => {
  case RaveilOwnedMemoryKey => Some(RaveilOwnedMemoryParams(
    expectedClientSourceStart = start,
    expectedClientSourceEnd = end,
    fateAuditAddress = Some(auditAddress),
    tokenAuditAddress = Some(auditAddress)
  ))
})
