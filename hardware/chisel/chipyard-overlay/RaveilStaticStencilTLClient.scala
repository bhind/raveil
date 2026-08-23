package chipyard.raveil

import chisel3._
import chisel3.util.log2Ceil
import org.chipsalliance.cde.config.{Config, Field, Parameters}
import freechips.rocketchip.diplomacy._
import freechips.rocketchip.regmapper._
import freechips.rocketchip.subsystem._
import freechips.rocketchip.tilelink._
import freechips.rocketchip.util._
import chipyard.BuildSystem

case class RaveilStaticStencilAttachmentParams(
    base: BigInt = 0x08000000L,
    activeOneShot: Boolean = false,
    runtimeControl: Boolean = false,
    controlBase: BigInt = 0x08011000L,
    controlBeatBytes: Int = 8)
case object RaveilStaticStencilAttachmentKey
  extends Field[Option[RaveilStaticStencilAttachmentParams]](None)

/**
 * G1c's one-shot integrated client. The first Graph Get starts the shared
 * fixture provider; execution then uses the unchanged fixed core schedule,
 * followed by private ordered validation reads at words 324..579.
  */
class RaveilStaticStencilTLClient(
    params: RaveilStaticStencilAttachmentParams
)(implicit p: Parameters) extends LazyModule {
  require(!(params.activeOneShot && params.runtimeControl))
  val node = TLClientNode(Seq(TLMasterPortParameters.v1(
    clients = Seq(TLMasterParameters.v1(
      name = "raveil-static-stencil-graph",
      sourceId = IdRange(0, 1),
      requestFifo = true
    )),
    requestFields = Seq(RaveilGraphOriginField())
  )))
  private val controlDevice = new SimpleDevice(
    "raveil-integrated-graph-control",
    Seq("raveil,integrated-graph-control-v1"))
  val controlNode = if (params.runtimeControl) {
    Some(TLRegisterNode(
      address = Seq(AddressSet(params.controlBase, 0xfff)),
      device = controlDevice,
      beatBytes = params.controlBeatBytes,
      concurrency = 1))
  } else None

  lazy val module = new LazyModuleImp(this) {
    val (tl, _) = node.out(0)
    val core = Module(new RaveilStaticStencilCore)
    val pending = RegInit(false.B)
    val startIssued = RegInit(false.B)
    val validationActive = RegInit(false.B)
    val validationIndex = RegInit(0.U(9.W))
    val validationAccepted = RegInit(0.U(9.W))
    val validationCompleted = RegInit(0.U(9.W))
    val responseWrite = RegInit(false.B)
    val clientBeatBytes = tl.a.bits.mask.getWidth
    val responseLaneOffset = RegInit(0.U(log2Ceil(clientBeatBytes).W))
    val responseInitiator = RegInit(0.U(2.W))
    val responsePhase = RegInit(0.U(3.W))
    val runtimeLaunch = if (params.runtimeControl) Some(RegInit(false.B)) else None
    val runtimeDone = if (params.runtimeControl) Some(RegInit(false.B)) else None
    val launchRequested = runtimeLaunch.getOrElse(false.B)

    core.io.start := (params.activeOneShot.B || launchRequested) && !startIssued
    core.io.cancel := false.B
    core.io.memory.pending := pending
    val validationRequest = validationActive && !pending
    val requestValid = Mux(validationActive, validationRequest,
      core.io.memory.request.valid)
    val requestWrite = Mux(validationActive, false.B,
      core.io.memory.request.bits.write)
    val requestAddress = Mux(validationActive,
      324.U(10.W) + validationIndex.pad(10),
      core.io.memory.request.bits.address)
    val requestByteAddress = params.base.U + (requestAddress << 2)
    val requestLaneOffset =
      requestByteAddress(log2Ceil(clientBeatBytes) - 1, 0)
    val requestWordData = Mux(validationActive, 0.U(32.W),
      core.io.memory.request.bits.writeData)
    val requestWordMask = Mux(requestWrite,
      core.io.memory.request.bits.writeMask, "hf".U)
    tl.a.valid := requestValid && !pending
    core.io.memory.request.ready := !validationActive && !pending && tl.a.ready
    tl.a.bits.opcode := Mux(requestWrite,
      TLMessages.PutFullData, TLMessages.Get)
    tl.a.bits.param := 0.U
    tl.a.bits.size := 2.U
    tl.a.bits.source := 0.U
    tl.a.bits.address := requestByteAddress
    tl.a.bits.mask := requestWordMask << requestLaneOffset
    tl.a.bits.data := requestWordData << (requestLaneOffset << 3)
    tl.a.bits.corrupt := false.B
    tl.a.bits.user(RaveilGraphOrigin) := true.B

    core.io.memory.response.valid := pending && tl.d.valid && !validationActive
    val responseWordData =
      (tl.d.bits.data >> (responseLaneOffset << 3))(31, 0)
    core.io.memory.response.bits.readData := responseWordData
    core.io.memory.response.bits.error := tl.d.bits.denied || tl.d.bits.corrupt
    core.io.memory.response.bits.write := responseWrite
    core.io.memory.response.bits.initiator := responseInitiator
    core.io.memory.response.bits.phase := responsePhase
    tl.d.ready := pending && Mux(validationActive, true.B,
      core.io.memory.response.ready)
    when(tl.a.fire) {
      pending := true.B
      responseWrite := requestWrite
      responseLaneOffset := requestLaneOffset
      responseInitiator := Mux(validationActive, 2.U,
        core.io.memory.request.bits.initiator)
      responsePhase := Mux(validationActive, 3.U,
        core.io.memory.request.bits.phase)
      when(validationActive) { validationAccepted := validationAccepted + 1.U }
    }
    when(tl.d.fire) {
      pending := false.B
      when(validationActive) {
        validationCompleted := validationCompleted + 1.U
        printf("RAVEIL-G1C-VALIDATION-V1 address=%d index=%d data=0x%x error=%d\n",
          requestAddress, validationIndex, responseWordData,
          tl.d.bits.denied || tl.d.bits.corrupt)
        when(validationIndex === 255.U) {
          validationActive := false.B
          runtimeDone.foreach(_ := true.B)
        }.otherwise { validationIndex := validationIndex + 1.U }
      }
    }
    when(!reset.asBool) {
      when(!startIssued && core.io.busy) { startIssued := true.B }
      when(core.io.completion) {
        validationActive := true.B
        validationIndex := 0.U
      }
      when(!validationActive && core.io.completion) {
        assert(core.io.graphInputReadsAccepted === 1280.U)
        assert(core.io.graphOutputWritesAccepted === 256.U)
      }
    }
    when(!reset.asBool) {
      assert(!(pending && tl.a.fire))
      when(tl.d.valid) {
        assert(pending)
        assert(tl.d.bits.source === 0.U)
        assert(tl.d.bits.size === 2.U)
        assert(tl.d.bits.opcode === Mux(responseWrite,
          TLMessages.AccessAck, TLMessages.AccessAckData))
      }
      when(tl.a.fire) {
        assert(tl.a.bits.user(RaveilGraphOrigin))
        when(validationActive) {
          assert(tl.a.bits.size === 2.U)
          assert(tl.a.bits.address === requestByteAddress)
        }.otherwise {
          assert(core.io.memory.request.bits.initiator === 2.U)
          assert(core.io.memory.request.bits.phase === 2.U)
        }
      }
    }
    controlNode.foreach { control =>
      control.regmap(
        0x00 -> Seq(RegField(1, runtimeLaunch.get)),
        0x04 -> Seq(RegField.r(1, runtimeDone.get)),
        0x08 -> Seq(RegField.r(1,
          core.io.busy || validationActive || pending)))
    }
    tl.b.ready := true.B
    tl.c.valid := false.B
    tl.e.valid := false.B
  }
}

trait CanHaveRaveilStaticStencilAttachment { this: BaseSubsystem =>
  p(RaveilStaticStencilAttachmentKey).foreach { params =>
    val bus = locateTLBusWrapper(PBUS)
    val domain = bus.generateSynchronousDomain
      .suggestName("raveil_static_stencil_graph_domain")
    val graph = domain { LazyModule(new RaveilStaticStencilTLClient(params)) }
    bus.coupleFrom("raveil-static-stencil-graph") { _ := graph.node }
    graph.controlNode.foreach { control =>
      bus.coupleTo("raveil-static-stencil-control") {
        control := TLFragmenter(bus.beatBytes, bus.blockBytes) := _
      }
    }
  }
}

class RaveilIntegratedGraphDigitalTop(implicit p: Parameters)
    extends chipyard.DigitalTop
    with CanHaveRaveilOwnedMemory
    with CanHaveRaveilStaticStencilAttachment

class WithRaveilIntegratedGraphBuildSystem
    extends Config((site, here, up) => {
  case BuildSystem =>
    (p: Parameters) => new RaveilIntegratedGraphDigitalTop()(p)
})

class WithRaveilStaticStencilAttachment extends Config((site, here, up) => {
  case RaveilStaticStencilAttachmentKey => Some(RaveilStaticStencilAttachmentParams())
})

class WithRaveilActiveStaticStencilAttachment extends Config((site, here, up) => {
  case RaveilStaticStencilAttachmentKey =>
    Some(RaveilStaticStencilAttachmentParams(activeOneShot = true))
})

class WithRaveilRuntimeStaticStencilAttachment extends Config((site, here, up) => {
  case RaveilStaticStencilAttachmentKey =>
    Some(RaveilStaticStencilAttachmentParams(runtimeControl = true))
})
