//> using scala 2.13.17
//> using dep org.chipsalliance::chisel:7.2.0
//> using plugin org.chipsalliance:::chisel-plugin:7.2.0

import chisel3._
import chisel3.util._
import _root_.circt.stage.ChiselStage
import chipyard.raveil.{RaveilFixtureInputProvider, RaveilStaticStencilCore}

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

    val fixtureStageStart = Input(Bool())
    val fixtureStageSeed = Input(UInt(32.W))
    val fixtureStageReady = Output(Bool())
    val fixtureStageDone = Output(Bool())
    val fixtureStageAcceptedCount = Output(UInt(10.W))
    val fixtureStageCompletedCount = Output(UInt(10.W))
    val fixtureStageAcceptedValid = Output(Bool())
    val fixtureStageAcceptedAddress = Output(UInt(9.W))
    val fixtureStageAcceptedData = Output(UInt(32.W))

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
    // Simulation-functional observation only; excluded from graph-device ABI.
    val transactionTraceValid = Output(Bool())
    val transactionTraceWrite = Output(Bool())
    val transactionTraceAddress = Output(UInt(10.W))
    val transactionTraceWriteData = Output(UInt(32.W))
    val memoryPending = Output(Bool())
  })

  val scratchpad = Module(new OwnedFixedLatencyScratchpad(1024, 580))
  val fixtureProvider = Module(new RaveilFixtureInputProvider)
  val core = Module(new RaveilStaticStencilCore)

  val outputValidReg = RegInit(false.B)
  val doneReg = RegInit(false.B)
  val cancelledReg = RegInit(false.B)
  val fixtureModeReg = RegInit(false.B)
  val legacyModeReg = RegInit(false.B)
  val fixtureCanStageReg = RegInit(true.B)
  val fixtureValidationResponsesReg = RegInit(0.U(9.W))
  val fixtureAcceptedValidReg = RegInit(false.B)
  val fixtureAcceptedAddressReg = RegInit(0.U(9.W))
  val fixtureAcceptedDataReg = RegInit(0.U(32.W))

  doneReg := false.B
  cancelledReg := false.B

  val fixtureSelected = !core.io.busy && fixtureProvider.io.active
  val controlStageSelected = !core.io.busy && !fixtureSelected && io.inputStageValid
  val controlValidationSelected = !core.io.busy && !fixtureSelected &&
    !io.inputStageValid &&
    io.outputValidationValid && outputValidReg
  val controlResponseIsValidation = RegInit(false.B)

  val directStart = io.start && !core.io.busy && !scratchpad.io.pending &&
    !fixtureProvider.io.active
  val graphStart = fixtureProvider.io.release || directStart
  core.io.start := graphStart
  core.io.cancel := io.cancel
  core.io.memory.pending := scratchpad.io.pending

  scratchpad.io.requestValid := Mux(
    core.io.busy,
    core.io.memory.request.valid,
    fixtureProvider.io.requestValid || controlStageSelected ||
      controlValidationSelected
  )
  scratchpad.io.requestWrite := Mux(
    core.io.busy, core.io.memory.request.bits.write,
    fixtureSelected || controlStageSelected)
  scratchpad.io.requestAddress := Mux(
    core.io.busy, core.io.memory.request.bits.address,
      Mux(fixtureSelected, fixtureProvider.io.requestAddress,
      Mux(controlStageSelected, io.inputStageAddress,
        324.U(10.W) + io.outputValidationAddress.pad(10))))
  scratchpad.io.requestWriteData := Mux(
    core.io.busy, core.io.memory.request.bits.writeData,
    Mux(fixtureSelected, fixtureProvider.io.requestData, io.inputStageData))
  scratchpad.io.requestWriteMask := Mux(
    core.io.busy, core.io.memory.request.bits.writeMask,
    Mux(scratchpad.io.requestWrite, "hf".U, 0.U))
  scratchpad.io.requestInitiator := Mux(
    core.io.busy, core.io.memory.request.bits.initiator,
    Mux(fixtureSelected, OwnedMemoryContract.InitiatorFixture.U,
      OwnedMemoryContract.InitiatorControl.U))
  scratchpad.io.requestPhase := Mux(
    core.io.busy, core.io.memory.request.bits.phase,
    Mux(fixtureSelected || controlStageSelected,
      OwnedMemoryContract.PhaseStaging.U,
      OwnedMemoryContract.PhaseValidation.U))
  core.io.memory.request.ready := scratchpad.io.requestReady
  core.io.memory.response.valid := scratchpad.io.responseValid
  core.io.memory.response.bits.readData := scratchpad.io.responseReadData
  core.io.memory.response.bits.error := scratchpad.io.responseError
  core.io.memory.response.bits.write := scratchpad.io.responseWrite
  core.io.memory.response.bits.initiator := scratchpad.io.responseInitiator
  core.io.memory.response.bits.phase := scratchpad.io.responsePhase

  when(!core.io.busy && scratchpad.io.requestValid && scratchpad.io.requestReady) {
    controlResponseIsValidation := controlValidationSelected
  }
  scratchpad.io.responseReady := Mux(
    core.io.busy,
    core.io.memory.response.ready,
    Mux(fixtureSelected,
      fixtureProvider.io.responseReady,
      Mux(controlResponseIsValidation,
      io.outputValidationResponseReady,
      io.inputStageResponseReady))
  )

  fixtureProvider.io.start := io.fixtureStageStart && io.fixtureStageReady
  fixtureProvider.io.seed := io.fixtureStageSeed
  fixtureProvider.io.requestReady := fixtureSelected && scratchpad.io.requestReady
  fixtureProvider.io.responseValid := fixtureSelected && scratchpad.io.responseValid
  fixtureProvider.io.responseError := scratchpad.io.responseError

  io.inputStageReady := !fixtureModeReg && !core.io.busy &&
    !fixtureProvider.io.active &&
    scratchpad.io.requestReady
  io.inputStageResponseValid := !core.io.busy && !fixtureProvider.io.active &&
    scratchpad.io.responseValid &&
    !controlResponseIsValidation
  io.inputStageResponseError := scratchpad.io.responseError
  io.outputValidationReady := !core.io.busy && !fixtureProvider.io.active &&
    !io.inputStageValid && outputValidReg && scratchpad.io.requestReady
  io.outputValidationResponseValid := !core.io.busy && !fixtureProvider.io.active &&
    scratchpad.io.responseValid && controlResponseIsValidation
  io.outputValidationReadData := scratchpad.io.responseReadData
  io.outputValidationResponseError := scratchpad.io.responseError
  io.fixtureStageReady := !legacyModeReg && fixtureCanStageReg &&
    !core.io.busy && !scratchpad.io.pending &&
    fixtureProvider.io.ready && !io.inputStageValid &&
    !io.outputValidationValid
  io.fixtureStageDone := fixtureProvider.io.done
  io.fixtureStageAcceptedCount := fixtureProvider.io.acceptedCount
  io.fixtureStageCompletedCount := fixtureProvider.io.completedCount
  io.fixtureStageAcceptedValid := fixtureAcceptedValidReg
  io.fixtureStageAcceptedAddress := fixtureAcceptedAddressReg
  io.fixtureStageAcceptedData := fixtureAcceptedDataReg

  fixtureAcceptedValidReg := false.B
  when(fixtureProvider.io.requestValid && fixtureProvider.io.requestReady) {
    fixtureAcceptedValidReg := true.B
    fixtureAcceptedAddressReg := fixtureProvider.io.requestAddress
    fixtureAcceptedDataReg := fixtureProvider.io.requestData
  }

  when(io.inputStageValid && io.inputStageReady) {
    legacyModeReg := true.B
  }
  when(io.start && !core.io.busy && !fixtureProvider.io.active) {
    legacyModeReg := true.B
  }
  when(io.fixtureStageStart && io.fixtureStageReady) {
    fixtureModeReg := true.B
    fixtureCanStageReg := false.B
    fixtureValidationResponsesReg := 0.U
  }
  when(fixtureModeReg && io.outputValidationValid &&
      io.outputValidationReady) {
    assert(io.outputValidationAddress === fixtureValidationResponsesReg)
  }
  when(fixtureModeReg && io.outputValidationResponseValid &&
      io.outputValidationResponseReady) {
    assert(fixtureValidationResponsesReg < 256.U)
    when(fixtureValidationResponsesReg === 255.U) {
      fixtureValidationResponsesReg := 0.U
      fixtureCanStageReg := true.B
    }.otherwise {
      fixtureValidationResponsesReg := fixtureValidationResponsesReg + 1.U
    }
  }

  when(graphStart) {
    outputValidReg := false.B
  }.elsewhen(io.inputStageValid && io.inputStageReady) {
    outputValidReg := false.B
  }
  when(core.io.completion) {
    outputValidReg := true.B
    doneReg := true.B
  }
  when(core.io.cancellation) {
    outputValidReg := false.B
    cancelledReg := true.B
  }

  io.outputValid := outputValidReg
  io.busy := core.io.busy
  io.done := doneReg
  io.cancelled := cancelledReg
  io.cycleCount := core.io.cycleCount
  io.checksum := core.io.checksum
  io.configurationTag := StaticStencilRegionContract.ConfigurationTagValue.U(64.W)
  io.inputAcceptedCount := scratchpad.io.acceptedCount
  io.inputCompletedCount := scratchpad.io.completedCount
  io.outputAcceptedCount := 0.U
  io.outputCompletedCount := 0.U
  io.graphInputReadsAccepted := core.io.graphInputReadsAccepted
  io.graphOutputWritesAccepted := core.io.graphOutputWritesAccepted
  io.transactionTraceValid := core.io.transactionTraceValid
  io.transactionTraceWrite := core.io.transactionTraceWrite
  io.transactionTraceAddress := core.io.transactionTraceAddress
  io.transactionTraceWriteData := core.io.transactionTraceWriteData
  io.memoryPending := scratchpad.io.pending

  when(!reset.asBool) {
    when(core.io.busy && scratchpad.io.requestValid) {
      assert(scratchpad.io.requestInitiator === OwnedMemoryContract.InitiatorGraph.U)
      assert(scratchpad.io.requestPhase === OwnedMemoryContract.PhaseExecution.U)
    }
    when(core.io.busy && scratchpad.io.responseValid) {
      assert(scratchpad.io.responseInitiator === OwnedMemoryContract.InitiatorGraph.U)
      assert(scratchpad.io.responsePhase === OwnedMemoryContract.PhaseExecution.U)
    }
    when(io.inputStageResponseValid) {
      assert(scratchpad.io.responseWrite)
      assert(scratchpad.io.responseInitiator === OwnedMemoryContract.InitiatorControl.U)
      assert(scratchpad.io.responsePhase === OwnedMemoryContract.PhaseStaging.U)
    }
    when(fixtureProvider.io.active && scratchpad.io.requestValid) {
      assert(!core.io.busy)
      assert(scratchpad.io.requestWrite)
      assert(scratchpad.io.requestAddress < 324.U)
      assert(scratchpad.io.requestInitiator === OwnedMemoryContract.InitiatorFixture.U)
      assert(scratchpad.io.requestPhase === OwnedMemoryContract.PhaseStaging.U)
    }
    when(fixtureProvider.io.active && scratchpad.io.responseValid) {
      assert(scratchpad.io.responseInitiator ===
        OwnedMemoryContract.InitiatorFixture.U)
      assert(scratchpad.io.responsePhase === OwnedMemoryContract.PhaseStaging.U)
    }
    when(fixtureProvider.io.release) {
      assert(!core.io.busy)
      assert(!io.inputStageReady)
      assert(fixtureProvider.io.acceptedCount === 324.U)
      assert(fixtureProvider.io.completedCount === 323.U)
    }
    when(fixtureModeReg) {
      assert(!io.inputStageReady)
      assert(!(io.start && !core.io.busy))
      when(!fixtureCanStageReg && !core.io.busy && !fixtureProvider.io.active) {
        assert(fixtureValidationResponsesReg =/= 0.U || outputValidReg)
      }
    }
    when(io.outputValidationResponseValid) {
      assert(!scratchpad.io.responseWrite)
      assert(scratchpad.io.responseInitiator === OwnedMemoryContract.InitiatorControl.U)
      assert(scratchpad.io.responsePhase === OwnedMemoryContract.PhaseValidation.U)
    }
    assert(!(outputValidReg && core.io.busy))
  }
}

object EmitStaticStencilRegion extends App {
  ChiselStage.emitSystemVerilogFile(
    new StaticStencilRegion,
    args = Array("--target-dir", "generated_static"),
    firtoolOpts = Array("-disable-all-randomization", "-strip-debug-info")
  )
}

object EmitPhysicalStaticStencilRegion extends App {
  ChiselStage.emitSystemVerilogFile(
    new StaticStencilRegion,
    args = Array("--target-dir", "generated_physical_static"),
    firtoolOpts = Array(
      "-disable-all-randomization",
      "-strip-debug-info",
      "--lowering-options=disallowLocalVariables,disallowPackedArrays"
    )
  )
}
