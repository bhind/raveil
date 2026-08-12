package chipyard.raveil

import chisel3._
import chisel3.util._
import org.chipsalliance.cde.config.Parameters
import freechips.rocketchip.diplomacy._
import freechips.rocketchip.tilelink._

object RaveilOwnedContract {
  val DataWidth = 32
  val InitiatorWidth = 2
  val PhaseWidth = 3

  val InitiatorControl = 0
  val InitiatorCpu = 1
  val InitiatorGraph = 2
}

class RaveilOwnedRequest(addressWidth: Int) extends Bundle {
  val write = Bool()
  val address = UInt(addressWidth.W)
  val writeData = UInt(RaveilOwnedContract.DataWidth.W)
  val writeMask = UInt(4.W)
  val initiator = UInt(RaveilOwnedContract.InitiatorWidth.W)
  val phase = UInt(RaveilOwnedContract.PhaseWidth.W)
}

class RaveilOwnedResponse extends Bundle {
  val readData = UInt(RaveilOwnedContract.DataWidth.W)
  val error = Bool()
  val write = Bool()
  val initiator = UInt(RaveilOwnedContract.InitiatorWidth.W)
  val phase = UInt(RaveilOwnedContract.PhaseWidth.W)
}

/**
  * Test target for the ADR-0043 owned request/response boundary.
  *
  * It is deliberately independent of TileLink. Exactly one response becomes
  * available after each accepted request and remains stable until consumed.
  * The target permits at most one outstanding request.
  */
class RaveilOwnedContractScratchpad(
    physicalWords: Int = 16,
    validWords: Int = 12
) extends Module {
  require(physicalWords > 0 && isPow2(physicalWords))
  require(validWords > 0 && validWords <= physicalWords)

  private val addressWidth = log2Ceil(physicalWords)

  val io = IO(new Bundle {
    val request = Flipped(Decoupled(new RaveilOwnedRequest(addressWidth)))
    val response = Decoupled(new RaveilOwnedResponse)
    val acceptedCount = Output(UInt(32.W))
    val completedCount = Output(UInt(32.W))
    val requestStallCount = Output(UInt(32.W))
    val responseStallCount = Output(UInt(32.W))
    val lastAcceptedInitiator = Output(UInt(RaveilOwnedContract.InitiatorWidth.W))
    val lastAcceptedPhase = Output(UInt(RaveilOwnedContract.PhaseWidth.W))
    val lastCompletedInitiator = Output(UInt(RaveilOwnedContract.InitiatorWidth.W))
    val lastCompletedPhase = Output(UInt(RaveilOwnedContract.PhaseWidth.W))
  })

  val storage = RegInit(VecInit(Seq.fill(physicalWords)(0.U(32.W))))
  val responseValid = RegInit(false.B)
  val responseBits = RegInit(0.U.asTypeOf(new RaveilOwnedResponse))
  val acceptedCount = RegInit(0.U(32.W))
  val completedCount = RegInit(0.U(32.W))
  val requestStallCount = RegInit(0.U(32.W))
  val responseStallCount = RegInit(0.U(32.W))
  val lastAcceptedInitiator = RegInit(0.U(RaveilOwnedContract.InitiatorWidth.W))
  val lastAcceptedPhase = RegInit(0.U(RaveilOwnedContract.PhaseWidth.W))
  val lastCompletedInitiator = RegInit(0.U(RaveilOwnedContract.InitiatorWidth.W))
  val lastCompletedPhase = RegInit(0.U(RaveilOwnedContract.PhaseWidth.W))

  io.request.ready := !responseValid
  val accept = io.request.fire
  val retire = io.response.fire
  val requestError = io.request.bits.address >= validWords.U

  when(io.request.valid && !io.request.ready) {
    requestStallCount := requestStallCount + 1.U
  }
  when(io.response.valid && !io.response.ready) {
    responseStallCount := responseStallCount + 1.U
  }

  when(retire) {
    responseValid := false.B
    completedCount := completedCount + 1.U
    lastCompletedInitiator := responseBits.initiator
    lastCompletedPhase := responseBits.phase
  }

  when(accept) {
    responseValid := true.B
    responseBits.readData := 0.U
    responseBits.error := requestError
    responseBits.write := io.request.bits.write
    responseBits.initiator := io.request.bits.initiator
    responseBits.phase := io.request.bits.phase
    acceptedCount := acceptedCount + 1.U
    lastAcceptedInitiator := io.request.bits.initiator
    lastAcceptedPhase := io.request.bits.phase

    when(!requestError) {
      when(io.request.bits.write) {
        val oldWord = storage(io.request.bits.address)
        val mergedBytes = Wire(Vec(4, UInt(8.W)))
        for (byte <- 0 until 4) {
          mergedBytes(byte) := Mux(
            io.request.bits.writeMask(byte),
            io.request.bits.writeData(8 * byte + 7, 8 * byte),
            oldWord(8 * byte + 7, 8 * byte)
          )
        }
        storage(io.request.bits.address) := mergedBytes.asUInt
      }.otherwise {
        responseBits.readData := storage(io.request.bits.address)
      }
    }
  }

  io.response.valid := responseValid
  io.response.bits := responseBits
  io.acceptedCount := acceptedCount
  io.completedCount := completedCount
  io.requestStallCount := requestStallCount
  io.responseStallCount := responseStallCount
  io.lastAcceptedInitiator := lastAcceptedInitiator
  io.lastAcceptedPhase := lastAcceptedPhase
  io.lastCompletedInitiator := lastCompletedInitiator
  io.lastCompletedPhase := lastCompletedPhase

  val responseWasStalled = RegNext(io.response.valid && !io.response.ready, false.B)
  val previousResponseBits = RegNext(responseBits)
  when(!reset.asBool) {
    assert(acceptedCount === completedCount + responseValid.asUInt)
    when(responseWasStalled) {
      assert(io.response.valid)
      assert(responseBits.asUInt === previousResponseBits.asUInt)
    }
  }
}

case class RaveilOwnedTLContractBridgeParams(
    base: BigInt = 0x08000000L,
    size: BigInt = 64
)

/**
  * Maximum-one-outstanding post-fragmenter TileLink to owned-contract bridge.
  *
  * TileLink source and size are retained for the D response. Initiator and
  * lifecycle phase are explicit adapter inputs and are carried through the
  * owned request and response; they are not inferred from TileLink source IDs.
  */
class RaveilOwnedTLContractBridge(
    val params: RaveilOwnedTLContractBridgeParams
)(implicit p: Parameters) extends LazyModule {
  require(isPow2(params.size))
  require(params.size >= 8)
  require(params.base % params.size == 0)

  private val beatBytes = 4
  private val words = (params.size / beatBytes).toInt
  val addressWidth = log2Ceil(words)
  private val device = new SimpleDevice(
    "raveil-owned-contract-bridge",
    Seq("raveil,owned-contract-bridge-v1")
  )

  val node = TLManagerNode(Seq(TLSlavePortParameters.v1(
    managers = Seq(TLSlaveParameters.v1(
      address = Seq(AddressSet(params.base, params.size - 1)),
      resources = device.reg,
      regionType = RegionType.IDEMPOTENT,
      executable = false,
      supportsGet = TransferSizes(1, beatBytes),
      supportsPutPartial = TransferSizes(1, beatBytes),
      supportsPutFull = TransferSizes(1, beatBytes),
      mayDenyGet = true,
      mayDenyPut = true,
      fifoId = Some(0)
    )),
    beatBytes = beatBytes,
    minLatency = 1
  )))

  lazy val module = new RaveilOwnedTLContractBridgeModule(this)
}

class RaveilOwnedTLContractBridgeModule(outer: RaveilOwnedTLContractBridge)
    extends LazyModuleImp(outer) {
  val (tl, _) = outer.node.in(0)
  val requestInitiator = IO(Input(UInt(RaveilOwnedContract.InitiatorWidth.W)))
  val requestPhase = IO(Input(UInt(RaveilOwnedContract.PhaseWidth.W)))
  val ownedRequest = IO(Decoupled(new RaveilOwnedRequest(outer.addressWidth)))
  val ownedResponse = IO(Flipped(Decoupled(new RaveilOwnedResponse)))

  val busy = RegInit(false.B)
  val localDenied = RegInit(false.B)
  val responseRead = RegInit(false.B)
  val responseSource = RegInit(0.U(tl.d.bits.source.getWidth.W))
  val responseSize = RegInit(0.U(tl.d.bits.size.getWidth.W))
  val responseInitiator = RegInit(0.U(RaveilOwnedContract.InitiatorWidth.W))
  val responsePhase = RegInit(0.U(RaveilOwnedContract.PhaseWidth.W))
  val acceptedCount = RegInit(0.U(32.W))
  val completedCount = RegInit(0.U(32.W))

  val get = tl.a.bits.opcode === TLMessages.Get
  val put = tl.a.bits.opcode === TLMessages.PutFullData ||
    tl.a.bits.opcode === TLMessages.PutPartialData
  val addressInRange = tl.a.bits.address >= outer.params.base.U &&
    tl.a.bits.address < (outer.params.base + outer.params.size).U
  val supported = addressInRange && (get || put)

  ownedRequest.valid := tl.a.valid && !busy && supported
  ownedRequest.bits.write := put
  ownedRequest.bits.address :=
    ((tl.a.bits.address - outer.params.base.U) >> 2)(outer.addressWidth - 1, 0)
  ownedRequest.bits.writeData := tl.a.bits.data
  ownedRequest.bits.writeMask := tl.a.bits.mask
  ownedRequest.bits.initiator := requestInitiator
  ownedRequest.bits.phase := requestPhase
  tl.a.ready := !busy && Mux(supported, ownedRequest.ready, true.B)

  when(tl.a.fire) {
    busy := true.B
    localDenied := !supported
    responseRead := get
    responseSource := tl.a.bits.source
    responseSize := tl.a.bits.size
    responseInitiator := requestInitiator
    responsePhase := requestPhase
    acceptedCount := acceptedCount + 1.U
  }

  tl.d.valid := busy && Mux(localDenied, true.B, ownedResponse.valid)
  tl.d.bits.opcode := Mux(responseRead, TLMessages.AccessAckData, TLMessages.AccessAck)
  tl.d.bits.param := 0.U
  tl.d.bits.size := responseSize
  tl.d.bits.source := responseSource
  tl.d.bits.sink := 0.U
  tl.d.bits.denied := localDenied || ownedResponse.bits.error
  tl.d.bits.data := Mux(responseRead && !localDenied, ownedResponse.bits.readData, 0.U)
  tl.d.bits.corrupt := responseRead && (localDenied || ownedResponse.bits.error)
  ownedResponse.ready := busy && !localDenied && tl.d.ready

  when(tl.d.fire) {
    busy := false.B
    localDenied := false.B
    completedCount := completedCount + 1.U
  }

  when(!reset.asBool) {
    assert(acceptedCount === completedCount + busy.asUInt)
    when(busy && !localDenied && ownedResponse.valid) {
      assert(ownedResponse.bits.write === !responseRead)
      assert(ownedResponse.bits.initiator === responseInitiator)
      assert(ownedResponse.bits.phase === responsePhase)
    }
  }

  tl.b.valid := false.B
  tl.c.ready := true.B
  tl.e.ready := true.B
}

class RaveilOwnedContractRawTLClientIO extends Bundle {
  val requestValid = Input(Bool())
  val requestReady = Output(Bool())
  val requestOpcode = Input(UInt(3.W))
  val requestParam = Input(UInt(3.W))
  val requestSize = Input(UInt(4.W))
  val requestSource = Input(UInt(2.W))
  val requestAddress = Input(UInt(32.W))
  val requestMask = Input(UInt(4.W))
  val requestData = Input(UInt(32.W))
  val requestInitiator = Input(UInt(RaveilOwnedContract.InitiatorWidth.W))
  val requestPhase = Input(UInt(RaveilOwnedContract.PhaseWidth.W))

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

  val ownedAcceptedCount = Output(UInt(32.W))
  val ownedCompletedCount = Output(UInt(32.W))
  val ownedRequestStallCount = Output(UInt(32.W))
  val ownedResponseStallCount = Output(UInt(32.W))
  val lastAcceptedInitiator = Output(UInt(RaveilOwnedContract.InitiatorWidth.W))
  val lastAcceptedPhase = Output(UInt(RaveilOwnedContract.PhaseWidth.W))
  val lastCompletedInitiator = Output(UInt(RaveilOwnedContract.InitiatorWidth.W))
  val lastCompletedPhase = Output(UInt(RaveilOwnedContract.PhaseWidth.W))
}

class RaveilOwnedContractRawTLClient(implicit p: Parameters) extends LazyModule {
  val node = TLClientNode(Seq(TLMasterPortParameters.v1(Seq(
    TLMasterParameters.v1(
      name = "raveil-owned-contract-raw-client",
      sourceId = IdRange(0, 4),
      requestFifo = true
    )
  ))))

  lazy val module = new RaveilOwnedContractRawTLClientModule(this)
}

class RaveilOwnedContractRawTLClientModule(
    outer: RaveilOwnedContractRawTLClient
) extends LazyModuleImp(outer) {
  val (tl, _) = outer.node.out(0)
  val io = IO(new RaveilOwnedContractRawTLClientIO)

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

  io.ownedAcceptedCount := 0.U
  io.ownedCompletedCount := 0.U
  io.ownedRequestStallCount := 0.U
  io.ownedResponseStallCount := 0.U
  io.lastAcceptedInitiator := 0.U
  io.lastAcceptedPhase := 0.U
  io.lastCompletedInitiator := 0.U
  io.lastCompletedPhase := 0.U
}

class RaveilOwnedTLContractBridgeHarness(implicit p: Parameters) extends LazyModule {
  val client = LazyModule(new RaveilOwnedContractRawTLClient)
  val bridge = LazyModule(new RaveilOwnedTLContractBridge(
    RaveilOwnedTLContractBridgeParams()
  ))
  bridge.node := client.node

  lazy val module = new LazyModuleImp(this) {
    val io = IO(new RaveilOwnedContractRawTLClientIO)
    val target = Module(new RaveilOwnedContractScratchpad())

    bridge.module.ownedRequest <> target.io.request
    bridge.module.ownedResponse <> target.io.response
    bridge.module.requestInitiator := io.requestInitiator
    bridge.module.requestPhase := io.requestPhase

    client.module.io.requestValid := io.requestValid
    io.requestReady := client.module.io.requestReady
    client.module.io.requestOpcode := io.requestOpcode
    client.module.io.requestParam := io.requestParam
    client.module.io.requestSize := io.requestSize
    client.module.io.requestSource := io.requestSource
    client.module.io.requestAddress := io.requestAddress
    client.module.io.requestMask := io.requestMask
    client.module.io.requestData := io.requestData
    client.module.io.requestInitiator := io.requestInitiator
    client.module.io.requestPhase := io.requestPhase

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

    io.ownedAcceptedCount := target.io.acceptedCount
    io.ownedCompletedCount := target.io.completedCount
    io.ownedRequestStallCount := target.io.requestStallCount
    io.ownedResponseStallCount := target.io.responseStallCount
    io.lastAcceptedInitiator := target.io.lastAcceptedInitiator
    io.lastAcceptedPhase := target.io.lastAcceptedPhase
    io.lastCompletedInitiator := target.io.lastCompletedInitiator
    io.lastCompletedPhase := target.io.lastCompletedPhase
  }
}
