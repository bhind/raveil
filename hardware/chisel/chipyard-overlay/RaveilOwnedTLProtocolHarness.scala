package chipyard.raveil

import chisel3._
import org.chipsalliance.cde.config.Parameters
import freechips.rocketchip.diplomacy._
import freechips.rocketchip.tilelink._

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

class RaveilOwnedTLProtocolHarness(implicit p: Parameters) extends LazyModule {
  val client = LazyModule(new RaveilRawTLClient)
  val memory = LazyModule(new RaveilOwnedTLMemory(RaveilOwnedMemoryParams()))
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
