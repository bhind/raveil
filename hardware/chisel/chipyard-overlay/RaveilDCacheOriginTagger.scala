package chipyard.raveil

import chisel3._
import org.chipsalliance.cde.config.{Config, Parameters}
import freechips.rocketchip.diplomacy._
import freechips.rocketchip.rocket.DCacheTLNodeTransformKey
import freechips.rocketchip.tilelink._
import freechips.rocketchip.util._
import chipyard.harness.{HarnessBinder, HasHarnessInstantiators}
import chipyard.iobinders.DMIPort

/**
  * Adds a structural request marker at the DCache-local TileLink boundary.
  * The marker uses TileLink request metadata. A pinned, ephemeral TLXbar patch
  * preserves negotiated request fields and initializes absent client fields to
  * their declared false default; the owned manager latches it for A/D accounting.
  *
  * The bit proves only that a request crossed this structural adapter. It does
  * not identify an instruction, PC, ELF, or semantic initiator.
  */
class RaveilDCacheOriginTagger(implicit p: Parameters) extends LazyModule {
  val node = TLAdapterNode(clientFn = { cp =>
    cp.v1copy(requestFields =
      BundleField.union(cp.requestFields :+ RaveilDCacheOriginField()))
  })

  lazy val module = new LazyModuleImp(this) {
    (node.in zip node.out).foreach { case ((in, _), (out, _)) =>
      out.a.valid := in.a.valid
      in.a.ready := out.a.ready
      Connectable.waiveUnmatched(out.a.bits, in.a.bits) match {
        case (sink, source) => sink.squeezeAll :<= source.squeezeAll
      }
      out.a.bits.user(RaveilDCacheOrigin) := true.B

      out.c.valid := in.c.valid
      in.c.ready := out.c.ready
      Connectable.waiveUnmatched(out.c.bits, in.c.bits) match {
        case (sink, source) => sink.squeezeAll :<= source.squeezeAll
      }
      out.c.bits.user(RaveilDCacheOrigin) := true.B

      in.b.valid := out.b.valid
      out.b.ready := in.b.ready
      Connectable.waiveUnmatched(in.b.bits, out.b.bits) match {
        case (sink, source) => sink.squeezeAll :<= source.squeezeAll
      }

      in.d.valid := out.d.valid
      out.d.ready := in.d.ready
      Connectable.waiveUnmatched(in.d.bits, out.d.bits) match {
        case (sink, source) => sink.squeezeAll :<= source.squeezeAll
      }

      out.e.valid := in.e.valid
      in.e.ready := out.e.ready
      Connectable.waiveUnmatched(out.e.bits, in.e.bits) match {
        case (sink, source) => sink.squeezeAll :<= source.squeezeAll
      }
    }
  }
}

class WithRaveilDCacheOriginTagger extends Config((site, here, up) => {
  case DCacheTLNodeTransformKey => (p: Parameters) => (upstream: TLNode) => {
    implicit val implicitParameters: Parameters = p
    val tagger = LazyModule(new RaveilDCacheOriginTagger()(p))
    tagger.node := upstream
    tagger.node
  }
})

class RaveilOwnedRocketConfig extends Config(
  new WithRaveilOwnedBuildSystem ++
  new WithRaveilOwnedMemorySourceRange(8224, 8256) ++
  new WithRaveilDCacheOriginTagger ++
  new testchipip.soc.WithNoScratchpads ++
  new chipyard.RocketConfig
)

class RaveilOwnedRocketFateConfig extends Config(
  new WithRaveilOwnedBuildSystem ++
  new WithRaveilOwnedMemorySourceRangeAndFateAudit(8224, 8256, 0x08000100L) ++
  new WithRaveilDCacheOriginTagger ++
  new testchipip.soc.WithNoScratchpads ++
  new chipyard.RocketConfig
)

class RaveilOwnedSmallBoomConfig extends Config(
  new WithRaveilOwnedBuildSystem ++
  new WithRaveilOwnedMemorySourceRange(8288, 8320) ++
  new WithRaveilDCacheOriginTagger ++
  new testchipip.soc.WithNoScratchpads ++
  new chipyard.SmallBoomConfig
)

class RaveilOwnedSmallBoomFateConfig extends Config(
  new WithRaveilOwnedBuildSystem ++
  new WithRaveilOwnedMemorySourceRangeAndFateAudit(8288, 8320, 0x08000100L) ++
  new WithRaveilDCacheOriginTagger ++
  new testchipip.soc.WithNoScratchpads ++
  new chipyard.SmallBoomConfig
)

/** Drives one bounded 8-bit Debug SBA write through the exported DMI port. */
class RaveilDebugSBADriver extends Module {
  val io = IO(new Bundle {
    val reqReady = Input(Bool())
    val reqValid = Output(Bool())
    val reqAddr = Output(UInt(7.W))
    val reqData = Output(UInt(32.W))
    val reqOp = Output(UInt(2.W))
    val respValid = Input(Bool())
    val respReady = Output(Bool())
    val respData = Input(UInt(32.W))
    val respCode = Input(UInt(2.W))
    val done = Output(Bool())
  })

  val command = RegInit(0.U(3.W))
  val waiting = RegInit(false.B)
  val finished = RegInit(false.B)
  val announced = RegInit(false.B)
  val watchdog = RegInit(0.U(16.W))

  // DMCONTROL reads report dmactive only after the inner-domain acknowledgement.
  // Wait for that synchronization before touching the SBA register block, then
  // read SBCS back so the selected 8-bit access width is itself checked.
  val commandAddr = VecInit(Seq(
    0x10.U, 0x10.U, 0x38.U, 0x38.U, 0x39.U, 0x3c.U, 0x38.U))
  val commandData = VecInit(Seq(
    1.U, 0.U, 0.U, 0.U, 0x08000000.U, 0xa5.U, 0.U))
  val commandOp = VecInit(Seq(2.U, 1.U, 2.U, 1.U, 2.U, 2.U, 1.U))

  io.reqValid := !waiting && !finished
  io.reqAddr := commandAddr(command)
  io.reqData := commandData(command)
  io.reqOp := commandOp(command)
  // Keep the DMI response channel ready before request acceptance. DMIToTL
  // may propagate D readiness into A readiness through its TL buffering, so
  // waiting-gated readiness can deadlock the first request.
  io.respReady := true.B
  io.done := finished

  when(!finished) {
    watchdog := watchdog + 1.U
    assert(watchdog =/= ((1 << 16) - 1).U, "Debug SBA DMI driver timed out")
  }

  val requestFire = io.reqValid && io.reqReady
  when(requestFire) {
    printf("RAVEIL-DEBUG-SBA-DMI-V1 event=request command=%d\n", command)
    waiting := true.B
  }
  when(io.respValid && io.respReady) {
    // DMIToTL can return a response in the request-acceptance cycle. Accept
    // that zero-latency case while still rejecting every unpaired response.
    assert(waiting || requestFire, "Debug SBA received an unexpected DMI response")
    printf("RAVEIL-DEBUG-SBA-DMI-V1 event=response command=%d code=%d data=0x%x\n",
      command, io.respCode, io.respData)
    assert(io.respCode === 0.U, "Debug SBA DMI response failed")
    waiting := false.B
    when(command === 1.U && !io.respData(0)) {
      // Retry the DMCONTROL read until dmactive has crossed to the inner domain.
    }.elsewhen(command === 3.U) {
      assert(io.respData(19, 17) === 0.U, "Debug SBA access width is not 8-bit")
      command := command + 1.U
    }.elsewhen(command === 6.U) {
      assert(!io.respData(22), "Debug SBA busy error")
      assert(io.respData(14, 12) === 0.U, "Debug SBA system bus error")
      when(!io.respData(21)) {
        finished := true.B
      }
    }.otherwise {
      command := command + 1.U
    }
  }
  when(finished && !announced) {
    printf("RAVEIL-DEBUG-SBA-DRIVER-V1 status=OK access=write8 address=0x08000000 data=0xa5 evidence=rtl-simulation-functional semantic_initiator=not-proven performance=not-measured\n")
    announced := true.B
  }
}

class WithRaveilDebugSBAHarness extends HarnessBinder({
  case (th: HasHarnessInstantiators, port: DMIPort, chipId: Int) => {
    val driver = withClockAndReset(th.harnessBinderClock, th.harnessBinderReset) {
      Module(new RaveilDebugSBADriver)
    }
    port.io.dmi.req.valid := driver.io.reqValid
    port.io.dmi.req.bits.addr := driver.io.reqAddr
    port.io.dmi.req.bits.data := driver.io.reqData
    port.io.dmi.req.bits.op := driver.io.reqOp
    driver.io.reqReady := port.io.dmi.req.ready
    driver.io.respValid := port.io.dmi.resp.valid
    driver.io.respData := port.io.dmi.resp.bits.data
    driver.io.respCode := port.io.dmi.resp.bits.resp
    port.io.dmi.resp.ready := driver.io.respReady
    port.io.dmiClock := th.harnessBinderClock
    port.io.dmiReset := th.harnessBinderReset
  }
})

class RaveilOwnedDebugSBARocketConfig extends Config(
  new WithRaveilDebugSBAHarness ++
  new chipyard.config.WithDMIDTM ++
  new freechips.rocketchip.subsystem.WithDebugSBA ++
  new WithRaveilOwnedBuildSystem ++
  new WithRaveilOwnedMemorySourceRange(16416, 16448) ++
  new WithRaveilDCacheOriginTagger ++
  new testchipip.soc.WithNoScratchpads ++
  new chipyard.RocketConfig
)

class RaveilOwnedDebugSBASmallBoomConfig extends Config(
  new WithRaveilDebugSBAHarness ++
  new chipyard.config.WithDMIDTM ++
  new freechips.rocketchip.subsystem.WithDebugSBA ++
  new WithRaveilOwnedBuildSystem ++
  new WithRaveilOwnedMemorySourceRange(16480, 16512) ++
  new WithRaveilDCacheOriginTagger ++
  new testchipip.soc.WithNoScratchpads ++
  new chipyard.SmallBoomConfig
)
