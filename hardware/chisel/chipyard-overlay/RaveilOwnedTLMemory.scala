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
  require(isPow2(params.size))
  require(isPow2(params.controlSize))
  require(params.base % params.size == 0)
  require(params.controlBase % params.controlSize == 0)
  require(params.base + params.size <= params.controlBase)
  require(params.expectedClientSourceStart >= 0)
  require(params.expectedClientSourceEnd > params.expectedClientSourceStart)

  private val beatBytes = 4
  private val words = (params.size / beatBytes).toInt
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
    requestKeys = Seq(RaveilDCacheOrigin)
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
    val responseIsData = RegInit(false.B)
    val responsePhase = RegInit(RaveilOwnedMemoryPhase.Installation.U(3.W))
    val responseExpectedClient = RegInit(false.B)
    val responseDcacheOrigin = RegInit(false.B)

    val phase = RegInit(RaveilOwnedMemoryPhase.Installation.U(3.W))
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
    val lastAcceptedSource = RegInit(0.U(32.W))
    val lastCompletedSource = RegInit(0.U(32.W))
    val lastAcceptedPhase = RegInit(RaveilOwnedMemoryPhase.Installation.U(3.W))
    val lastCompletedPhase = RegInit(RaveilOwnedMemoryPhase.Installation.U(3.W))

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
    val phaseWrite = controlRequest && put && controlOffset === 0.U
    val phaseValueValid = tl.a.bits.data(2, 0) < RaveilOwnedMemoryPhase.Count.U
    val phaseByteEnabled = tl.a.bits.mask(0)
    val requestError = !supported ||
      (phaseWrite && (!phaseByteEnabled || !phaseValueValid))
    val expectedClientRequest =
      tl.a.bits.source >= params.expectedClientSourceStart.U &&
      tl.a.bits.source < params.expectedClientSourceEnd.U
    val dcacheOriginRequest =
      tl.a.bits.user.lift(RaveilDCacheOrigin).getOrElse(false.B)
    val wordIndex = ((requestAddress - params.base.U) >> 2)(log2Ceil(words) - 1, 0)

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
    val freshResponseData = Mux(responseRead && !responseIsData,
      responseControlData, freshReadData)

    tl.a.ready := !busy
    when(tl.a.fire) {
      busy := true.B
      responseRead := get
      responseError := requestError
      responseSource := tl.a.bits.source
      responseSize := tl.a.bits.size
      responseIsData := dataRequest
      responsePhase := phase
      responseExpectedClient := expectedClientRequest
      responseDcacheOrigin := dcacheOriginRequest
      when(controlRequest && get) {
        responseControlData := controlReadData
      }

      when(dataRequest && !requestError) {
        acceptedCount := acceptedCount + 1.U
        lastAcceptedSource := tl.a.bits.source
        lastAcceptedPhase := phase
        when(expectedClientRequest) {
          expectedAcceptedCount := expectedAcceptedCount + 1.U
        }.otherwise {
          unexpectedAcceptedCount := unexpectedAcceptedCount + 1.U
        }
        when(dcacheOriginRequest) {
          dcacheOriginAcceptedCount := dcacheOriginAcceptedCount + 1.U
          lastDcacheOriginAcceptedSource := tl.a.bits.source
          lastDcacheOriginAcceptedPhase := phase
        }.otherwise {
          nonDcacheOriginAcceptedCount := nonDcacheOriginAcceptedCount + 1.U
        }
        when(get) {
          phaseReadCounts(phase) := phaseReadCounts(phase) + 1.U
        }.otherwise {
          phaseWriteCounts(phase) := phaseWriteCounts(phase) + 1.U
          val writeBytes = Wire(Vec(beatBytes, UInt(8.W)))
          for (byte <- 0 until beatBytes) {
            writeBytes(byte) := tl.a.bits.data(8 * byte + 7, 8 * byte)
          }
          memory.write(wordIndex, writeBytes, tl.a.bits.mask.asBools)
        }
      }
      when(phaseWrite && phaseByteEnabled && phaseValueValid) {
        phase := tl.a.bits.data(2, 0)
      }
    }

    val responseValid = responseDue || responseHeld
    val responseData = Mux(responseHeld, responseHeldData, freshResponseData)
    tl.d.valid := responseValid
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
      responseHeld := false.B
      busy := false.B
      when(responseIsData && !responseError) {
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
