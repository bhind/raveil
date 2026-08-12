package chipyard.raveil

import chisel3._
import org.chipsalliance.cde.config.Parameters
import freechips.rocketchip.diplomacy._
import freechips.rocketchip.tilelink._
import freechips.rocketchip.util._

class RaveilRawTLClientIO extends Bundle {
  val requestValid = Input(Bool())
  val requestReady = Output(Bool())
  val requestOpcode = Input(UInt(3.W))
  val requestParam = Input(UInt(3.W))
  val requestSize = Input(UInt(4.W))
  val requestSource = Input(UInt(2.W))
  val requestAddress = Input(UInt(32.W))
  val requestMask = Input(UInt(4.W))
  val requestData = Input(UInt(32.W))

  val responseValid = Output(Bool())
  val responseReady = Input(Bool())
  val responseOpcode = Output(UInt(3.W))
  val responseParam = Output(UInt(2.W))
  val responseSize = Output(UInt(4.W))
  val responseSource = Output(UInt(2.W))
  val responseSink = Output(UInt())
  val responseDenied = Output(Bool())
  val responseData = Output(UInt(32.W))
  val responseCorrupt = Output(Bool())
}

class RaveilRawTLClient(implicit p: Parameters) extends LazyModule {
  val node = TLClientNode(Seq(TLMasterPortParameters.v1(Seq(
    TLMasterParameters.v1(
      name = "raveil-raw-tl-client",
      sourceId = IdRange(0, 4),
      requestFifo = true
    )
  ))))

  lazy val module = new RaveilRawTLClientModule(this)
}

/**
  * Test-only client that marks every request as structurally DCache-origin.
  * It is used only to prove that a downstream boundary which does not carry
  * the field fails closed to non-origin; it is not a CPU or loader model.
  */
class RaveilMarkedRawTLClient(implicit p: Parameters) extends LazyModule {
  val node = TLClientNode(Seq(TLMasterPortParameters.v1(
    clients = Seq(TLMasterParameters.v1(
      name = "raveil-marked-raw-tl-client",
      sourceId = IdRange(0, 4),
      requestFifo = true
    )),
    requestFields = Seq(RaveilDCacheOriginField())
  )))

  lazy val module = new RaveilMarkedRawTLClientModule(this)
}

class RaveilRawTLClientModule(outer: RaveilRawTLClient)
    extends LazyModuleImp(outer) {
    val (tl, _) = outer.node.out(0)
    val io = IO(new RaveilRawTLClientIO)

    tl.a.valid := io.requestValid
    io.requestReady := tl.a.ready
    tl.a.bits.opcode := io.requestOpcode
    tl.a.bits.param := io.requestParam
    tl.a.bits.size := io.requestSize
    tl.a.bits.source := io.requestSource
    tl.a.bits.address := io.requestAddress
    tl.a.bits.mask := io.requestMask
    tl.a.bits.data := io.requestData
    tl.a.bits.corrupt := false.B

    io.responseValid := tl.d.valid
    tl.d.ready := io.responseReady
    io.responseOpcode := tl.d.bits.opcode
    io.responseParam := tl.d.bits.param
    io.responseSize := tl.d.bits.size
    io.responseSource := tl.d.bits.source
    io.responseSink := tl.d.bits.sink
    io.responseDenied := tl.d.bits.denied
    io.responseData := tl.d.bits.data
    io.responseCorrupt := tl.d.bits.corrupt

    tl.b.ready := true.B
    tl.c.valid := false.B
    tl.e.valid := false.B
}

class RaveilMarkedRawTLClientModule(outer: RaveilMarkedRawTLClient)
    extends LazyModuleImp(outer) {
    val (tl, _) = outer.node.out(0)
    val io = IO(new RaveilRawTLClientIO)

    tl.a.valid := io.requestValid
    io.requestReady := tl.a.ready
    tl.a.bits.opcode := io.requestOpcode
    tl.a.bits.param := io.requestParam
    tl.a.bits.size := io.requestSize
    tl.a.bits.source := io.requestSource
    tl.a.bits.address := io.requestAddress
    tl.a.bits.mask := io.requestMask
    tl.a.bits.data := io.requestData
    tl.a.bits.corrupt := false.B
    tl.a.bits.user(RaveilDCacheOrigin) := true.B

    io.responseValid := tl.d.valid
    tl.d.ready := io.responseReady
    io.responseOpcode := tl.d.bits.opcode
    io.responseParam := tl.d.bits.param
    io.responseSize := tl.d.bits.size
    io.responseSource := tl.d.bits.source
    io.responseSink := tl.d.bits.sink
    io.responseDenied := tl.d.bits.denied
    io.responseData := tl.d.bits.data
    io.responseCorrupt := tl.d.bits.corrupt

    tl.b.ready := true.B
    tl.c.valid := false.B
    tl.e.valid := false.B
}

/**
  * Test-only metadata stripping boundary. The upstream client advertises and
  * drives the structural marker, while the downstream port deliberately omits
  * it from negotiation. The owned manager must therefore observe its declared
  * false default. This models metadata loss only, not a real loader/debug path.
  */
class RaveilOriginStrippingAdapter(implicit p: Parameters) extends LazyModule {
  val node = TLAdapterNode(clientFn = { cp =>
    cp.v1copy(requestFields =
      cp.requestFields.filterNot(_.key == RaveilDCacheOrigin))
  })

  lazy val module = new LazyModuleImp(this) {
    (node.in zip node.out).foreach { case ((in, _), (out, _)) =>
      out.a.valid := in.a.valid
      in.a.ready := out.a.ready
      Connectable.waiveUnmatched(out.a.bits, in.a.bits) match {
        case (sink, source) => sink.squeezeAll :<= source.squeezeAll
      }

      out.c.valid := in.c.valid
      in.c.ready := out.c.ready
      Connectable.waiveUnmatched(out.c.bits, in.c.bits) match {
        case (sink, source) => sink.squeezeAll :<= source.squeezeAll
      }

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

class RaveilOwnedTLProtocolHarness(implicit p: Parameters) extends LazyModule {
  val client = LazyModule(new RaveilRawTLClient)
  val memory = LazyModule(new RaveilOwnedTLMemory(RaveilOwnedMemoryParams(
    expectedClientSourceStart = 1,
    expectedClientSourceEnd = 3
  )))
  memory.node := client.node

  lazy val module = new LazyModuleImp(this) {
    val io = IO(new RaveilRawTLClientIO)
    client.module.io.requestValid := io.requestValid
    io.requestReady := client.module.io.requestReady
    client.module.io.requestOpcode := io.requestOpcode
    client.module.io.requestParam := io.requestParam
    client.module.io.requestSize := io.requestSize
    client.module.io.requestSource := io.requestSource
    client.module.io.requestAddress := io.requestAddress
    client.module.io.requestMask := io.requestMask
    client.module.io.requestData := io.requestData

    io.responseValid := client.module.io.responseValid
    client.module.io.responseReady := io.responseReady
    io.responseOpcode := client.module.io.responseOpcode
    io.responseParam := client.module.io.responseParam
    io.responseSize := client.module.io.responseSize
    io.responseSource := client.module.io.responseSource
    io.responseSink := client.module.io.responseSink
    io.responseDenied := client.module.io.responseDenied
    io.responseData := client.module.io.responseData
    io.responseCorrupt := client.module.io.responseCorrupt
  }
}

class RaveilOwnedTLOriginStripHarness(implicit p: Parameters) extends LazyModule {
  val client = LazyModule(new RaveilMarkedRawTLClient)
  val stripper = LazyModule(new RaveilOriginStrippingAdapter)
  val memory = LazyModule(new RaveilOwnedTLMemory(RaveilOwnedMemoryParams(
    expectedClientSourceStart = 1,
    expectedClientSourceEnd = 3
  )))
  memory.node := stripper.node := client.node

  lazy val module = new LazyModuleImp(this) {
    val io = IO(new RaveilRawTLClientIO)
    client.module.io.requestValid := io.requestValid
    io.requestReady := client.module.io.requestReady
    client.module.io.requestOpcode := io.requestOpcode
    client.module.io.requestParam := io.requestParam
    client.module.io.requestSize := io.requestSize
    client.module.io.requestSource := io.requestSource
    client.module.io.requestAddress := io.requestAddress
    client.module.io.requestMask := io.requestMask
    client.module.io.requestData := io.requestData

    io.responseValid := client.module.io.responseValid
    client.module.io.responseReady := io.responseReady
    io.responseOpcode := client.module.io.responseOpcode
    io.responseParam := client.module.io.responseParam
    io.responseSize := client.module.io.responseSize
    io.responseSource := client.module.io.responseSource
    io.responseSink := client.module.io.responseSink
    io.responseDenied := client.module.io.responseDenied
    io.responseData := client.module.io.responseData
    io.responseCorrupt := client.module.io.responseCorrupt
  }
}
