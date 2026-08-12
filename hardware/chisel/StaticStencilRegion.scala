//> using scala 2.13.17
//> using dep org.chipsalliance::chisel:7.2.0
//> using plugin org.chipsalliance:::chisel-plugin:7.2.0

import chisel3._
import chisel3.util._
import _root_.circt.stage.ChiselStage

object StaticStencilRegionContract {
  val ConfigurationTag = "d4bf9395a510385f"
  val ConfigurationTagValue: BigInt = BigInt(ConfigurationTag, 16)
  val ContractBoundary = "runtime_ready_slots=0"
}

/**
  * Fixed request/response schedule for the RFC-0005 uint32 five-point stencil.
  *
  * This module has no runtime dependency scheduler, token store, rename state,
  * ROB, general LSU, commit frontier, or issue-mode switching. Input and output
  * Two OwnedFixedLatencyScratchpad instances model disjoint input and private
  * output bindings. Control stages input and validates output through the same
  * owned transaction contract. Output bytes have no authority unless
  * outputValid is asserted after all 256 points complete.
  */
class StaticStencilRegion extends Module {
  val io = IO(new Bundle {
    val inputStageValid = Input(Bool())
    val inputStageReady = Output(Bool())
    val inputStageAddress = Input(UInt(9.W))
    val inputStageData = Input(UInt(32.W))
    val inputStageResponseValid = Output(Bool())
    val inputStageResponseReady = Input(Bool())
    val inputStageResponseError = Output(Bool())

    val start = Input(Bool())
    val cancel = Input(Bool())

    val outputValidationValid = Input(Bool())
    val outputValidationReady = Output(Bool())
    val outputValidationAddress = Input(UInt(8.W))
    val outputValidationResponseValid = Output(Bool())
    val outputValidationResponseReady = Input(Bool())
    val outputValidationReadData = Output(UInt(32.W))
    val outputValidationResponseError = Output(Bool())
    val outputValid = Output(Bool())
    val busy = Output(Bool())
    val done = Output(Bool())
    val cancelled = Output(Bool())
    val cycleCount = Output(UInt(14.W))
    val checksum = Output(UInt(64.W))
    val configurationTag = Output(UInt(64.W))
    val inputAcceptedCount = Output(UInt(32.W))
    val inputCompletedCount = Output(UInt(32.W))
    val outputAcceptedCount = Output(UInt(32.W))
    val outputCompletedCount = Output(UInt(32.W))
    val graphInputReadsAccepted = Output(UInt(16.W))
    val graphOutputWritesAccepted = Output(UInt(16.W))
    val memoryPending = Output(Bool())
  })

  val inputScratchpad = Module(new OwnedFixedLatencyScratchpad(512, 324))
  val outputScratchpad = Module(new OwnedFixedLatencyScratchpad(256, 256))

  val busyReg = RegInit(false.B)
  val outputValidReg = RegInit(false.B)
  val doneReg = RegInit(false.B)
  val cancelledReg = RegInit(false.B)
  val outputIndex = RegInit(0.U(8.W))
  val accumulator = RegInit(0.U(32.W))
  val cycleCountReg = RegInit(0.U(14.W))
  val checksumReg = RegInit(0.U(64.W))
  val graphInputReadsAcceptedReg = RegInit(0.U(16.W))
  val graphOutputWritesAcceptedReg = RegInit(0.U(16.W))
  val cancelRequestedReg = RegInit(false.B)

  val Seq(
    idle,
    loadCenterRequest,
    loadCenterResponse,
    loadNorthRequest,
    loadNorthResponse,
    loadSouthRequest,
    loadSouthResponse,
    loadWestRequest,
    loadWestResponse,
    loadEastRequest,
    loadEastResponse,
    storeRequest,
    storeResponse
  ) = Enum(13)
  val state = RegInit(idle)

  val y = Wire(UInt(5.W))
  val x = Wire(UInt(5.W))
  val scaledY = Wire(UInt(9.W))
  val center = Wire(UInt(9.W))
  y := outputIndex(7, 4).pad(5) + 1.U(5.W)
  x := outputIndex(3, 0).pad(5) + 1.U(5.W)
  scaledY := y * 18.U
  center := scaledY + x

  doneReg := false.B
  cancelledReg := false.B

  val cancelling = io.cancel || cancelRequestedReg
  val graphInputRequest = busyReg && !cancelling && (
    state === loadCenterRequest || state === loadNorthRequest ||
    state === loadSouthRequest || state === loadWestRequest ||
    state === loadEastRequest)
  val graphOutputRequest = busyReg && !cancelling && state === storeRequest

  val inputAddress = Wire(UInt(9.W))
  inputAddress := center
  when(state === loadNorthRequest) { inputAddress := center - 18.U }
  when(state === loadSouthRequest) { inputAddress := center + 18.U }
  when(state === loadWestRequest) { inputAddress := center - 1.U }
  when(state === loadEastRequest) { inputAddress := center + 1.U }

  inputScratchpad.io.requestValid := Mux(
    busyReg,
    graphInputRequest,
    io.inputStageValid
  )
  inputScratchpad.io.requestWrite := !busyReg
  inputScratchpad.io.requestAddress := Mux(
    busyReg,
    inputAddress,
    io.inputStageAddress
  )
  inputScratchpad.io.requestWriteData := io.inputStageData
  inputScratchpad.io.requestWriteMask := Mux(busyReg, 0.U, "hf".U)
  inputScratchpad.io.requestInitiator := Mux(
    busyReg,
    OwnedMemoryContract.InitiatorGraph.U,
    OwnedMemoryContract.InitiatorControl.U
  )
  inputScratchpad.io.requestPhase := Mux(
    busyReg,
    OwnedMemoryContract.PhaseExecution.U,
    OwnedMemoryContract.PhaseStaging.U
  )
  val graphInputResponseState = busyReg && (
    state === loadCenterResponse || state === loadNorthResponse ||
    state === loadSouthResponse || state === loadWestResponse ||
    state === loadEastResponse)
  inputScratchpad.io.responseReady := Mux(
    busyReg,
    graphInputResponseState,
    io.inputStageResponseReady
  )

  outputScratchpad.io.requestValid := Mux(
    busyReg,
    graphOutputRequest,
    io.outputValidationValid && outputValidReg
  )
  outputScratchpad.io.requestWrite := busyReg
  outputScratchpad.io.requestAddress := Mux(
    busyReg,
    outputIndex,
    io.outputValidationAddress
  )
  outputScratchpad.io.requestWriteData := accumulator
  outputScratchpad.io.requestWriteMask := Mux(busyReg, "hf".U, 0.U)
  outputScratchpad.io.requestInitiator := Mux(
    busyReg,
    OwnedMemoryContract.InitiatorGraph.U,
    OwnedMemoryContract.InitiatorControl.U
  )
  outputScratchpad.io.requestPhase := Mux(
    busyReg,
    OwnedMemoryContract.PhaseExecution.U,
    OwnedMemoryContract.PhaseValidation.U
  )
  outputScratchpad.io.responseReady := Mux(
    busyReg,
    state === storeResponse,
    io.outputValidationResponseReady
  )

  io.inputStageReady := !busyReg && inputScratchpad.io.requestReady
  io.inputStageResponseValid := !busyReg && inputScratchpad.io.responseValid
  io.inputStageResponseError := inputScratchpad.io.responseError
  io.outputValidationReady := !busyReg && outputValidReg &&
    outputScratchpad.io.requestReady
  io.outputValidationResponseValid := !busyReg &&
    outputScratchpad.io.responseValid
  io.outputValidationReadData := outputScratchpad.io.responseReadData
  io.outputValidationResponseError := outputScratchpad.io.responseError

  when(io.cancel && busyReg) {
    cancelRequestedReg := true.B
  }

  when(cancelling && busyReg) {
    outputValidReg := false.B
    when(!inputScratchpad.io.pending && !outputScratchpad.io.pending) {
      busyReg := false.B
      cancelledReg := true.B
      cancelRequestedReg := false.B
      state := idle
    }
  }.elsewhen(busyReg) {
    cycleCountReg := cycleCountReg + 1.U
    switch(state) {
      is(loadCenterRequest) {
        when(inputScratchpad.io.requestReady) {
          graphInputReadsAcceptedReg := graphInputReadsAcceptedReg + 1.U
          state := loadCenterResponse
        }
      }
      is(loadCenterResponse) {
        when(inputScratchpad.io.responseValid) {
          accumulator := inputScratchpad.io.responseReadData
          state := loadNorthRequest
        }
      }
      is(loadNorthRequest) {
        when(inputScratchpad.io.requestReady) {
          graphInputReadsAcceptedReg := graphInputReadsAcceptedReg + 1.U
          state := loadNorthResponse
        }
      }
      is(loadNorthResponse) {
        when(inputScratchpad.io.responseValid) {
          accumulator := accumulator + inputScratchpad.io.responseReadData
          state := loadSouthRequest
        }
      }
      is(loadSouthRequest) {
        when(inputScratchpad.io.requestReady) {
          graphInputReadsAcceptedReg := graphInputReadsAcceptedReg + 1.U
          state := loadSouthResponse
        }
      }
      is(loadSouthResponse) {
        when(inputScratchpad.io.responseValid) {
          accumulator := accumulator + inputScratchpad.io.responseReadData
          state := loadWestRequest
        }
      }
      is(loadWestRequest) {
        when(inputScratchpad.io.requestReady) {
          graphInputReadsAcceptedReg := graphInputReadsAcceptedReg + 1.U
          state := loadWestResponse
        }
      }
      is(loadWestResponse) {
        when(inputScratchpad.io.responseValid) {
          accumulator := accumulator + inputScratchpad.io.responseReadData
          state := loadEastRequest
        }
      }
      is(loadEastRequest) {
        when(inputScratchpad.io.requestReady) {
          graphInputReadsAcceptedReg := graphInputReadsAcceptedReg + 1.U
          state := loadEastResponse
        }
      }
      is(loadEastResponse) {
        when(inputScratchpad.io.responseValid) {
          accumulator := accumulator + inputScratchpad.io.responseReadData
          state := storeRequest
        }
      }
      is(storeRequest) {
        when(outputScratchpad.io.requestReady) {
          graphOutputWritesAcceptedReg := graphOutputWritesAcceptedReg + 1.U
          state := storeResponse
        }
      }
      is(storeResponse) {
        when(outputScratchpad.io.responseValid) {
          when(inputScratchpad.io.responseError || outputScratchpad.io.responseError) {
            busyReg := false.B
            outputValidReg := false.B
            cancelledReg := true.B
            state := idle
          }.otherwise {
            checksumReg := checksumReg + accumulator
            when(outputIndex === 255.U) {
              busyReg := false.B
              outputValidReg := true.B
              doneReg := true.B
              state := idle
            }.otherwise {
              outputIndex := outputIndex + 1.U
              state := loadCenterRequest
            }
          }
        }
      }
    }
  }.elsewhen(io.start && !inputScratchpad.io.pending &&
      !outputScratchpad.io.pending) {
    busyReg := true.B
    outputValidReg := false.B
    outputIndex := 0.U
    state := loadCenterRequest
    accumulator := 0.U
    cycleCountReg := 0.U
    checksumReg := 0.U
    cancelRequestedReg := false.B
    graphInputReadsAcceptedReg := 0.U
    graphOutputWritesAcceptedReg := 0.U
  }.elsewhen(io.inputStageValid && io.inputStageReady) {
    outputValidReg := false.B
  }

  io.outputValid := outputValidReg
  io.busy := busyReg
  io.done := doneReg
  io.cancelled := cancelledReg
  io.cycleCount := cycleCountReg
  io.checksum := checksumReg
  io.configurationTag := StaticStencilRegionContract.ConfigurationTagValue.U(64.W)
  io.inputAcceptedCount := inputScratchpad.io.acceptedCount
  io.inputCompletedCount := inputScratchpad.io.completedCount
  io.outputAcceptedCount := outputScratchpad.io.acceptedCount
  io.outputCompletedCount := outputScratchpad.io.completedCount
  io.graphInputReadsAccepted := graphInputReadsAcceptedReg
  io.graphOutputWritesAccepted := graphOutputWritesAcceptedReg
  io.memoryPending := inputScratchpad.io.pending || outputScratchpad.io.pending

  when(!reset.asBool) {
    when(graphInputResponseState && inputScratchpad.io.responseValid) {
      assert(!inputScratchpad.io.responseError)
      assert(!inputScratchpad.io.responseWrite)
      assert(inputScratchpad.io.responseInitiator === OwnedMemoryContract.InitiatorGraph.U)
      assert(inputScratchpad.io.responsePhase === OwnedMemoryContract.PhaseExecution.U)
    }
    when(busyReg && state === storeResponse && outputScratchpad.io.responseValid) {
      assert(!outputScratchpad.io.responseError)
      assert(outputScratchpad.io.responseWrite)
      assert(outputScratchpad.io.responseInitiator === OwnedMemoryContract.InitiatorGraph.U)
      assert(outputScratchpad.io.responsePhase === OwnedMemoryContract.PhaseExecution.U)
    }
    when(io.inputStageResponseValid) {
      assert(inputScratchpad.io.responseWrite)
      assert(inputScratchpad.io.responseInitiator === OwnedMemoryContract.InitiatorControl.U)
      assert(inputScratchpad.io.responsePhase === OwnedMemoryContract.PhaseStaging.U)
    }
    when(io.outputValidationResponseValid) {
      assert(!outputScratchpad.io.responseWrite)
      assert(outputScratchpad.io.responseInitiator === OwnedMemoryContract.InitiatorControl.U)
      assert(outputScratchpad.io.responsePhase === OwnedMemoryContract.PhaseValidation.U)
    }
    assert(!(outputValidReg && busyReg))
  }
}

object EmitStaticStencilRegion extends App {
  ChiselStage.emitSystemVerilogFile(
    new StaticStencilRegion,
    args = Array("--target-dir", "generated_static"),
    firtoolOpts = Array("-disable-all-randomization", "-strip-debug-info")
  )
}
