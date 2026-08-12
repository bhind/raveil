//> using scala 2.13.17
//> using dep org.chipsalliance::chisel:7.2.0
//> using plugin org.chipsalliance:::chisel-plugin:7.2.0

import chisel3._
import chisel3.util._
import _root_.circt.stage.ChiselStage

object OwnedMemoryContract {
  val ContractVersion = 1
  val DataWidth = 32
  val InitiatorWidth = 2
  val PhaseWidth = 3
  val ResponseAvailabilityLatencyCycles = 1

  val InitiatorControl = 0
  val InitiatorCpu = 1
  val InitiatorGraph = 2

  val PhaseInstallation = 0
  val PhaseStaging = 1
  val PhaseExecution = 2
  val PhaseCompletion = 3
  val PhaseValidation = 4
  val PhasePublication = 5
  val PhaseFallback = 6
}

/**
  * Raveil-owned, single-client scratchpad transaction boundary.
  *
  * A request is accepted only on requestValid && requestReady. Exactly one
  * response becomes available on the following cycle and remains stable until
  * responseValid && responseReady. At most one transaction is outstanding.
  * The latency statement is local to this module; it is not a CPU-to-memory,
  * Graph-to-memory, performance, energy, area, FPGA, or silicon claim.
  */
class OwnedFixedLatencyScratchpad(
    val physicalWords: Int = 512,
    val validWords: Int = 324,
    val allowRead: Boolean = true,
    val allowWrite: Boolean = true
) extends Module {
  require(physicalWords > 0)
  require(validWords > 0 && validWords <= physicalWords)
  require(isPow2(physicalWords), "physicalWords must be a power of two")

  private val addressWidth = log2Ceil(physicalWords)

  val io = IO(new Bundle {
    val requestValid = Input(Bool())
    val requestReady = Output(Bool())
    val requestWrite = Input(Bool())
    val requestAddress = Input(UInt(addressWidth.W))
    val requestWriteData = Input(UInt(OwnedMemoryContract.DataWidth.W))
    val requestWriteMask = Input(UInt(4.W))
    val requestInitiator = Input(UInt(OwnedMemoryContract.InitiatorWidth.W))
    val requestPhase = Input(UInt(OwnedMemoryContract.PhaseWidth.W))

    val responseValid = Output(Bool())
    val responseReady = Input(Bool())
    val responseReadData = Output(UInt(OwnedMemoryContract.DataWidth.W))
    val responseError = Output(Bool())
    val responseWrite = Output(Bool())
    val responseInitiator = Output(UInt(OwnedMemoryContract.InitiatorWidth.W))
    val responsePhase = Output(UInt(OwnedMemoryContract.PhaseWidth.W))

    val acceptedCount = Output(UInt(32.W))
    val completedCount = Output(UInt(32.W))
    val requestStallCount = Output(UInt(32.W))
    val responseStallCount = Output(UInt(32.W))
    val pending = Output(Bool())
  })

  val storage = RegInit(VecInit(Seq.fill(physicalWords)(0.U(32.W))))
  val responseValidReg = RegInit(false.B)
  val responseReadDataReg = RegInit(0.U(32.W))
  val responseErrorReg = RegInit(false.B)
  val responseWriteReg = RegInit(false.B)
  val responseInitiatorReg = RegInit(0.U(OwnedMemoryContract.InitiatorWidth.W))
  val responsePhaseReg = RegInit(0.U(OwnedMemoryContract.PhaseWidth.W))
  val acceptedCountReg = RegInit(0.U(32.W))
  val completedCountReg = RegInit(0.U(32.W))
  val requestStallCountReg = RegInit(0.U(32.W))
  val responseStallCountReg = RegInit(0.U(32.W))

  io.requestReady := !responseValidReg
  val accept = io.requestValid && io.requestReady
  val retire = responseValidReg && io.responseReady
  val inRange = io.requestAddress < validWords.U
  val operationAllowed = Mux(io.requestWrite, allowWrite.B, allowRead.B)
  val requestError = !inRange || !operationAllowed

  when(io.requestValid && !io.requestReady) {
    requestStallCountReg := requestStallCountReg + 1.U
  }
  when(responseValidReg && !io.responseReady) {
    responseStallCountReg := responseStallCountReg + 1.U
  }

  when(retire) {
    responseValidReg := false.B
    completedCountReg := completedCountReg + 1.U
  }

  when(accept) {
    responseValidReg := true.B
    responseReadDataReg := 0.U
    responseErrorReg := requestError
    responseWriteReg := io.requestWrite
    responseInitiatorReg := io.requestInitiator
    responsePhaseReg := io.requestPhase
    acceptedCountReg := acceptedCountReg + 1.U

    when(!requestError) {
      when(io.requestWrite) {
        val oldWord = storage(io.requestAddress)
        val mergedBytes = Wire(Vec(4, UInt(8.W)))
        for (byte <- 0 until 4) {
          mergedBytes(byte) := Mux(
            io.requestWriteMask(byte),
            io.requestWriteData(8 * byte + 7, 8 * byte),
            oldWord(8 * byte + 7, 8 * byte)
          )
        }
        storage(io.requestAddress) := mergedBytes.asUInt
      }.otherwise {
        responseReadDataReg := storage(io.requestAddress)
      }
    }
  }

  val acceptedPreviousCycle = RegNext(accept, false.B)
  val responseWasStalled = RegNext(responseValidReg && !io.responseReady, false.B)
  val previousResponseReadData = RegNext(responseReadDataReg)
  val previousResponseError = RegNext(responseErrorReg)
  val previousResponseWrite = RegNext(responseWriteReg)
  val previousResponseInitiator = RegNext(responseInitiatorReg)
  val previousResponsePhase = RegNext(responsePhaseReg)
  when(!reset.asBool) {
    assert(acceptedCountReg === completedCountReg + responseValidReg.asUInt)
    assert(!(responseValidReg && io.requestReady))
    when(acceptedPreviousCycle) {
      assert(responseValidReg)
    }
    when(responseWasStalled) {
      assert(responseValidReg)
      assert(responseReadDataReg === previousResponseReadData)
      assert(responseErrorReg === previousResponseError)
      assert(responseWriteReg === previousResponseWrite)
      assert(responseInitiatorReg === previousResponseInitiator)
      assert(responsePhaseReg === previousResponsePhase)
    }
  }

  io.responseValid := responseValidReg
  io.responseReadData := responseReadDataReg
  io.responseError := responseErrorReg
  io.responseWrite := responseWriteReg
  io.responseInitiator := responseInitiatorReg
  io.responsePhase := responsePhaseReg
  io.acceptedCount := acceptedCountReg
  io.completedCount := completedCountReg
  io.requestStallCount := requestStallCountReg
  io.responseStallCount := responseStallCountReg
  io.pending := responseValidReg
}

object EmitOwnedFixedLatencyScratchpad extends App {
  ChiselStage.emitSystemVerilogFile(
    new OwnedFixedLatencyScratchpad,
    args = Array("--target-dir", "generated_owned_memory"),
    firtoolOpts = Array("-disable-all-randomization", "-strip-debug-info")
  )
}
