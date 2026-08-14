package chipyard.raveil

import chisel3._
import chisel3.util._

object RaveilFixtureInputContract {
  val Version = 1
  val InputWords = 324
  val InputAddressBits = 9
  val FormulaMultiplier = 2654435761L
  val FormulaSeedAddend = 17
}

/**
  * Candidate-external deterministic input provider for EXP-0007.
  *
  * The provider owns no memory.  It presents one ordered write at a time to
  * the candidate's existing owned-memory ingress and waits for that write's
  * response before presenting the next one.  The final response is the sole
  * release edge.  The same module is instantiated by the Graph and CPU
  * fixtures so input generation is not candidate-local work.
  */
class RaveilFixtureInputProvider extends Module {
  val io = IO(new Bundle {
    val start = Input(Bool())
    val seed = Input(UInt(32.W))

    val requestValid = Output(Bool())
    val requestReady = Input(Bool())
    val requestAddress = Output(UInt(RaveilFixtureInputContract.InputAddressBits.W))
    val requestData = Output(UInt(32.W))
    val responseValid = Input(Bool())
    val responseReady = Output(Bool())
    val responseError = Input(Bool())

    val ready = Output(Bool())
    val active = Output(Bool())
    val release = Output(Bool())
    val done = Output(Bool())
    val acceptedCount = Output(UInt(10.W))
    val completedCount = Output(UInt(10.W))
    val pending = Output(Bool())
  })

  val activeReg = RegInit(false.B)
  val waitingForResponse = RegInit(false.B)
  val seedReg = RegInit(0.U(32.W))
  val indexReg = RegInit(0.U(9.W))
  val acceptedReg = RegInit(0.U(10.W))
  val completedReg = RegInit(0.U(10.W))
  val doneReg = RegInit(false.B)

  val seedProduct = (seedReg *
    RaveilFixtureInputContract.FormulaMultiplier.U(32.W))(31, 0)
  val indexedProduct = (((indexReg +& 1.U).pad(32)) * seedProduct)(31, 0)
  val shiftedIndex = (indexReg.pad(32) << seedReg(2, 0))(31, 0)
  val seedAddend = (seedReg *
    RaveilFixtureInputContract.FormulaSeedAddend.U(32.W))(31, 0)

  val requestFire = activeReg && !waitingForResponse && io.requestReady
  val responseFire = activeReg && waitingForResponse &&
    io.responseValid && !io.responseError
  val finalResponse = responseFire &&
    indexReg === (RaveilFixtureInputContract.InputWords - 1).U

  doneReg := false.B
  when(io.start) {
    assert(!activeReg && !waitingForResponse,
      "fixture input provider restarted while active")
    activeReg := true.B
    waitingForResponse := false.B
    seedReg := io.seed
    indexReg := 0.U
    acceptedReg := 0.U
    completedReg := 0.U
  }
  when(requestFire) {
    waitingForResponse := true.B
    acceptedReg := acceptedReg + 1.U
  }
  when(activeReg && waitingForResponse && io.responseValid) {
    assert(!io.responseError, "fixture input staging response failed")
  }
  when(responseFire) {
    waitingForResponse := false.B
    completedReg := completedReg + 1.U
    when(finalResponse) {
      activeReg := false.B
      doneReg := true.B
    }.otherwise {
      indexReg := indexReg + 1.U
    }
  }

  io.requestValid := activeReg && !waitingForResponse
  io.requestAddress := indexReg
  io.requestData := indexedProduct ^ shiftedIndex ^ seedAddend
  io.responseReady := activeReg && waitingForResponse
  io.ready := !activeReg && !waitingForResponse
  io.active := activeReg
  io.release := finalResponse
  io.done := doneReg
  io.acceptedCount := acceptedReg
  io.completedCount := completedReg
  io.pending := waitingForResponse

  when(!reset.asBool) {
    assert(acceptedReg === completedReg + waitingForResponse.asUInt)
    assert(acceptedReg <= RaveilFixtureInputContract.InputWords.U)
    assert(completedReg <= RaveilFixtureInputContract.InputWords.U)
    assert(!(io.requestValid && waitingForResponse))
    when(io.release) {
      assert(acceptedReg === RaveilFixtureInputContract.InputWords.U)
      assert(completedReg ===
        (RaveilFixtureInputContract.InputWords - 1).U)
      assert(waitingForResponse)
    }
  }
}
