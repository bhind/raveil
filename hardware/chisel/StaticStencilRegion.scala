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
  * ROB, general LSU, commit frontier, or issue-mode switching. One single-port
  * OwnedFixedLatencyScratchpad contains disjoint input words [0,324) and private
  * output words [324,580), matching the frozen CPU address layout. Control
  * stages input and validates output through the same owned transaction
  * contract. Output bytes have no authority unless outputValid is asserted
  * after all 256 points complete.
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

  val scratchpad = Module(new OwnedFixedLatencyScratchpad(1024, 580))

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

  val graphInputResponseState = busyReg && (
    state === loadCenterResponse || state === loadNorthResponse ||
    state === loadSouthResponse || state === loadWestResponse ||
    state === loadEastResponse)
  val controlStageSelected = !busyReg && io.inputStageValid
  val controlValidationSelected = !busyReg && !io.inputStageValid &&
    io.outputValidationValid && outputValidReg
  val controlResponseIsValidation = RegInit(false.B)

  scratchpad.io.requestValid := Mux(
    busyReg,
    graphInputRequest || graphOutputRequest,
    controlStageSelected || controlValidationSelected
  )
  scratchpad.io.requestWrite := Mux(busyReg, graphOutputRequest, controlStageSelected)
  scratchpad.io.requestAddress := Mux(
    busyReg,
    Mux(graphOutputRequest, 324.U + outputIndex, inputAddress),
    Mux(controlStageSelected, io.inputStageAddress, 324.U + io.outputValidationAddress)
  )
  scratchpad.io.requestWriteData := Mux(busyReg, accumulator, io.inputStageData)
  scratchpad.io.requestWriteMask := Mux(scratchpad.io.requestWrite, "hf".U, 0.U)
  scratchpad.io.requestInitiator := Mux(
    busyReg,
    OwnedMemoryContract.InitiatorGraph.U,
    OwnedMemoryContract.InitiatorControl.U
  )
  scratchpad.io.requestPhase := Mux(
    busyReg,
    OwnedMemoryContract.PhaseExecution.U,
    Mux(controlStageSelected,
      OwnedMemoryContract.PhaseStaging.U,
      OwnedMemoryContract.PhaseValidation.U)
  )
  when(!busyReg && scratchpad.io.requestValid && scratchpad.io.requestReady) {
    controlResponseIsValidation := controlValidationSelected
  }
  scratchpad.io.responseReady := Mux(
    busyReg,
    graphInputResponseState || state === storeResponse,
    Mux(controlResponseIsValidation,
      io.outputValidationResponseReady,
      io.inputStageResponseReady)
  )

  io.inputStageReady := !busyReg && scratchpad.io.requestReady
  io.inputStageResponseValid := !busyReg && scratchpad.io.responseValid &&
    !controlResponseIsValidation
  io.inputStageResponseError := scratchpad.io.responseError
  io.outputValidationReady := !busyReg && !io.inputStageValid && outputValidReg &&
    scratchpad.io.requestReady
  io.outputValidationResponseValid := !busyReg && scratchpad.io.responseValid &&
    controlResponseIsValidation
  io.outputValidationReadData := scratchpad.io.responseReadData
  io.outputValidationResponseError := scratchpad.io.responseError

  when(io.cancel && busyReg) {
    cancelRequestedReg := true.B
  }

  when(cancelling && busyReg) {
    outputValidReg := false.B
    when(!scratchpad.io.pending) {
      busyReg := false.B
      cancelledReg := true.B
      cancelRequestedReg := false.B
      state := idle
    }
  }.elsewhen(busyReg) {
    cycleCountReg := cycleCountReg + 1.U
    switch(state) {
      is(loadCenterRequest) {
        when(scratchpad.io.requestReady) {
          graphInputReadsAcceptedReg := graphInputReadsAcceptedReg + 1.U
          state := loadCenterResponse
        }
      }
      is(loadCenterResponse) {
        when(scratchpad.io.responseValid) {
          accumulator := scratchpad.io.responseReadData
          state := loadNorthRequest
        }
      }
      is(loadNorthRequest) {
        when(scratchpad.io.requestReady) {
          graphInputReadsAcceptedReg := graphInputReadsAcceptedReg + 1.U
          state := loadNorthResponse
        }
      }
      is(loadNorthResponse) {
        when(scratchpad.io.responseValid) {
          accumulator := accumulator + scratchpad.io.responseReadData
          state := loadSouthRequest
        }
      }
      is(loadSouthRequest) {
        when(scratchpad.io.requestReady) {
          graphInputReadsAcceptedReg := graphInputReadsAcceptedReg + 1.U
          state := loadSouthResponse
        }
      }
      is(loadSouthResponse) {
        when(scratchpad.io.responseValid) {
          accumulator := accumulator + scratchpad.io.responseReadData
          state := loadWestRequest
        }
      }
      is(loadWestRequest) {
        when(scratchpad.io.requestReady) {
          graphInputReadsAcceptedReg := graphInputReadsAcceptedReg + 1.U
          state := loadWestResponse
        }
      }
      is(loadWestResponse) {
        when(scratchpad.io.responseValid) {
          accumulator := accumulator + scratchpad.io.responseReadData
          state := loadEastRequest
        }
      }
      is(loadEastRequest) {
        when(scratchpad.io.requestReady) {
          graphInputReadsAcceptedReg := graphInputReadsAcceptedReg + 1.U
          state := loadEastResponse
        }
      }
      is(loadEastResponse) {
        when(scratchpad.io.responseValid) {
          accumulator := accumulator + scratchpad.io.responseReadData
          state := storeRequest
        }
      }
      is(storeRequest) {
        when(scratchpad.io.requestReady) {
          graphOutputWritesAcceptedReg := graphOutputWritesAcceptedReg + 1.U
          state := storeResponse
        }
      }
      is(storeResponse) {
        when(scratchpad.io.responseValid) {
          when(scratchpad.io.responseError) {
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
  }.elsewhen(io.start && !scratchpad.io.pending) {
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
  io.inputAcceptedCount := scratchpad.io.acceptedCount
  io.inputCompletedCount := scratchpad.io.completedCount
  io.outputAcceptedCount := 0.U
  io.outputCompletedCount := 0.U
  io.graphInputReadsAccepted := graphInputReadsAcceptedReg
  io.graphOutputWritesAccepted := graphOutputWritesAcceptedReg
  io.memoryPending := scratchpad.io.pending

  when(!reset.asBool) {
    when(graphInputResponseState && scratchpad.io.responseValid) {
      assert(!scratchpad.io.responseError)
      assert(!scratchpad.io.responseWrite)
      assert(scratchpad.io.responseInitiator === OwnedMemoryContract.InitiatorGraph.U)
      assert(scratchpad.io.responsePhase === OwnedMemoryContract.PhaseExecution.U)
    }
    when(busyReg && state === storeResponse && scratchpad.io.responseValid) {
      assert(!scratchpad.io.responseError)
      assert(scratchpad.io.responseWrite)
      assert(scratchpad.io.responseInitiator === OwnedMemoryContract.InitiatorGraph.U)
      assert(scratchpad.io.responsePhase === OwnedMemoryContract.PhaseExecution.U)
    }
    when(io.inputStageResponseValid) {
      assert(scratchpad.io.responseWrite)
      assert(scratchpad.io.responseInitiator === OwnedMemoryContract.InitiatorControl.U)
      assert(scratchpad.io.responsePhase === OwnedMemoryContract.PhaseStaging.U)
    }
    when(io.outputValidationResponseValid) {
      assert(!scratchpad.io.responseWrite)
      assert(scratchpad.io.responseInitiator === OwnedMemoryContract.InitiatorControl.U)
      assert(scratchpad.io.responsePhase === OwnedMemoryContract.PhaseValidation.U)
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
