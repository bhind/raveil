package chipyard.raveil

import chisel3._
import chisel3.util._

object RaveilBoundedProgramContract {
  val PayloadWords = 32
  val ProgramCapacity = 16
  val ValueRegisters = 8
  val Magic = 0x52504731L
  val Version = 1
  val LoadOpcode = 1
  val AddOpcode = 2
  val StoreOpcode = 3
  val MaxU32Opcode = 4
  val EastAddress = 4
  val FactoryProgram = Seq(
    0x10000000L, 0x12400000L, 0x20080000L, 0x12800000L,
    0x20080000L, 0x12c00000L, 0x20080000L, 0x13000000L,
    0x20080000L, 0x30000000L)
  val FactoryDigestWords = Seq(
    0x8d87ba83L, 0x52b9dd2dL, 0x66938ad0L, 0xd640d6e3L,
    0x3746bc31L, 0x1c78b040L, 0x47bf4922L, 0xbd85e7e6L)
}

class RaveilStaticStencilMemoryRequest extends Bundle {
  val write = Bool()
  val address = UInt(10.W)
  val writeData = UInt(32.W)
  val writeMask = UInt(4.W)
  val initiator = UInt(2.W)
  val phase = UInt(3.W)
}

class RaveilStaticStencilMemoryResponse extends Bundle {
  val readData = UInt(32.W)
  val error = Bool()
  val write = Bool()
  val initiator = UInt(2.W)
  val phase = UInt(3.W)
}

class RaveilStaticStencilMemoryPort extends Bundle {
  val request = Decoupled(new RaveilStaticStencilMemoryRequest)
  val response = Flipped(Decoupled(new RaveilStaticStencilMemoryResponse))
  val pending = Input(Bool())
}

/**
  * Bounded sequential installed-program executor.
  *
  * The historical class name remains a source-compatibility seam. Runtime
  * behavior depends only on installed opcodes and affine parameters; Graph
  * identifiers and filenames are absent from this module. The owned memory
  * boundary admits at most one outstanding request.
  */
class RaveilStaticStencilCore extends Module {
  val io = IO(new Bundle {
    val start = Input(Bool())
    val cancel = Input(Bool())
    val rows = Input(UInt(5.W))
    val columns = Input(UInt(5.W))
    val inputStride = Input(UInt(9.W))
    val outputStride = Input(UInt(9.W))
    val activeOutputs = Input(UInt(9.W))
    val programVersion = Input(UInt(3.W))
    val programLength = Input(UInt(5.W))
    val program = Input(Vec(RaveilBoundedProgramContract.ProgramCapacity,
      UInt(32.W)))
    val memory = new RaveilStaticStencilMemoryPort

    val busy = Output(Bool())
    val completion = Output(Bool())
    val cancellation = Output(Bool())
    val cycleCount = Output(UInt(14.W))
    val checksum = Output(UInt(64.W))
    val graphInputReadsAccepted = Output(UInt(16.W))
    val graphOutputWritesAccepted = Output(UInt(16.W))
    val transactionTraceValid = Output(Bool())
    val transactionTraceWrite = Output(Bool())
    val transactionTraceAddress = Output(UInt(10.W))
    val transactionTraceWriteData = Output(UInt(32.W))
  })

  val busyReg = RegInit(false.B)
  val outputIndex = RegInit(0.U(8.W))
  val programCounter = RegInit(0.U(4.W))
  val values = RegInit(VecInit(Seq.fill(
    RaveilBoundedProgramContract.ValueRegisters)(0.U(32.W))))
  val cycleCountReg = RegInit(0.U(14.W))
  val checksumReg = RegInit(0.U(64.W))
  val graphInputReadsAcceptedReg = RegInit(0.U(16.W))
  val graphOutputWritesAcceptedReg = RegInit(0.U(16.W))
  val cancelRequestedReg = RegInit(false.B)

  val Seq(idle, fetch, loadRequest, loadResponse, storeRequest,
    storeResponse) = Enum(6)
  val state = RegInit(idle)

  val instruction = io.program(programCounter)
  val opcode = instruction(31, 28)
  val destination = instruction(27, 25)
  val sourceA = instruction(24, 22)
  val sourceB = instruction(21, 19)
  val selector = instruction(24, 22)
  val logicalRow = Wire(UInt(5.W))
  val logicalColumn = Wire(UInt(5.W))
  logicalRow := outputIndex / io.columns
  logicalColumn := outputIndex % io.columns
  val center = Wire(UInt(10.W))
  val outputRowBase = Wire(UInt(10.W))
  val outputAddress = Wire(UInt(10.W))
  center := (logicalRow + 1.U) * io.inputStride + logicalColumn + 1.U
  outputRowBase := logicalRow * io.outputStride
  outputAddress := 324.U + outputRowBase + logicalColumn
  val legacyInputAddress = Wire(UInt(10.W))
  legacyInputAddress := center
  switch(selector) {
    is(1.U) { legacyInputAddress := center - io.inputStride }
    is(2.U) { legacyInputAddress := center + io.inputStride }
    is(3.U) { legacyInputAddress := center - 1.U }
    is(4.U) { legacyInputAddress := center + 1.U }
  }
  val relativeRow = instruction(24, 20).asSInt
  val relativeColumn = instruction(19, 15).asSInt
  val relativeInputAddress = Wire(SInt(16.W))
  relativeInputAddress := center.zext +
    (relativeRow * io.inputStride.zext) + relativeColumn
  val relativeInputAddressUInt = relativeInputAddress.asUInt
  val inputAddress = Mux(
    io.programVersion >= 3.U,
    relativeInputAddressUInt(9, 0),
    legacyInputAddress)
  val storeData = values(destination)

  val cancelling = io.cancel || cancelRequestedReg
  val graphInputRequest = busyReg && !cancelling && state === loadRequest
  val graphOutputRequest = busyReg && !cancelling && state === storeRequest
  io.memory.request.valid := graphInputRequest || graphOutputRequest
  io.memory.request.bits.write := graphOutputRequest
  io.memory.request.bits.address := Mux(
    graphOutputRequest, outputAddress, inputAddress)
  io.memory.request.bits.writeData := storeData
  io.memory.request.bits.writeMask := Mux(graphOutputRequest, "hf".U, 0.U)
  io.memory.request.bits.initiator := 2.U
  io.memory.request.bits.phase := 2.U
  io.memory.response.ready := state === loadResponse || state === storeResponse

  val requestFire = io.memory.request.valid && io.memory.request.ready
  val responseFire = io.memory.response.valid && io.memory.response.ready
  val finalInstruction = programCounter.pad(5) === io.programLength - 1.U
  val lastOutput = outputIndex.pad(9) === io.activeOutputs - 1.U
  val completion = busyReg && !cancelling && state === storeResponse &&
    finalInstruction && lastOutput && responseFire &&
    !io.memory.response.bits.error
  val storeFailure = busyReg && state === storeResponse && responseFire &&
    io.memory.response.bits.error
  val cancellation = busyReg && cancelling && !io.memory.pending

  when(io.cancel && busyReg) { cancelRequestedReg := true.B }

  when(cancelling && busyReg) {
    when(!io.memory.pending) {
      busyReg := false.B
      cancelRequestedReg := false.B
      state := idle
    }
  }.elsewhen(busyReg) {
    cycleCountReg := cycleCountReg + 1.U
    switch(state) {
      is(fetch) {
        when(opcode === RaveilBoundedProgramContract.LoadOpcode.U) {
          state := loadRequest
        }.elsewhen(opcode === RaveilBoundedProgramContract.AddOpcode.U) {
          values(destination) := (values(sourceA) +& values(sourceB))(31, 0)
          programCounter := programCounter + 1.U
        }.elsewhen(opcode === RaveilBoundedProgramContract.MaxU32Opcode.U) {
          values(destination) := Mux(values(sourceA) >= values(sourceB), values(sourceA), values(sourceB))
          programCounter := programCounter + 1.U
        }.elsewhen(opcode === 5.U && io.programVersion === 4.U) {
          values(destination) := (values(sourceA) * values(sourceB))(31, 0)
          programCounter := programCounter + 1.U
        }.elsewhen(opcode === RaveilBoundedProgramContract.StoreOpcode.U) {
          state := storeRequest
        }.otherwise {
          busyReg := false.B
          state := idle
        }
      }
      is(loadRequest) {
        when(requestFire) {
          graphInputReadsAcceptedReg := graphInputReadsAcceptedReg + 1.U
          state := loadResponse
        }
      }
      is(loadResponse) {
        when(responseFire) {
          when(io.memory.response.bits.error) {
            busyReg := false.B
            state := idle
          }.otherwise {
            values(destination) := io.memory.response.bits.readData
            programCounter := programCounter + 1.U
            state := fetch
          }
        }
      }
      is(storeRequest) {
        when(requestFire) {
          graphOutputWritesAcceptedReg := graphOutputWritesAcceptedReg + 1.U
          state := storeResponse
        }
      }
      is(storeResponse) {
        when(responseFire) {
          when(io.memory.response.bits.error || !finalInstruction) {
            busyReg := false.B
            state := idle
          }.otherwise {
            checksumReg := checksumReg + storeData
            for (index <- 0 until RaveilBoundedProgramContract.ValueRegisters) {
              values(index) := 0.U
            }
            when(lastOutput) {
              busyReg := false.B
              state := idle
            }.otherwise {
              outputIndex := outputIndex + 1.U
              programCounter := 0.U
              state := fetch
            }
          }
        }
      }
    }
  }.elsewhen(io.start) {
    busyReg := true.B
    outputIndex := 0.U
    programCounter := 0.U
    for (index <- 0 until RaveilBoundedProgramContract.ValueRegisters) {
      values(index) := 0.U
    }
    // Every admitted program starts with LOAD_U32; expose that request on the
    // first execution cycle so cancellation and busy-mutation evidence retain
    // the existing nonempty-prefix boundary.
    state := loadRequest
    cycleCountReg := 0.U
    checksumReg := 0.U
    cancelRequestedReg := false.B
    graphInputReadsAcceptedReg := 0.U
    graphOutputWritesAcceptedReg := 0.U
  }

  io.busy := busyReg
  io.completion := completion
  io.cancellation := cancellation || storeFailure
  io.cycleCount := cycleCountReg
  io.checksum := checksumReg
  io.graphInputReadsAccepted := graphInputReadsAcceptedReg
  io.graphOutputWritesAccepted := graphOutputWritesAcceptedReg
  io.transactionTraceValid := requestFire
  io.transactionTraceWrite := io.memory.request.bits.write
  io.transactionTraceAddress := io.memory.request.bits.address
  io.transactionTraceWriteData := io.memory.request.bits.writeData

  when(!reset.asBool) {
    assert(io.rows >= 1.U && io.rows <= 16.U)
    assert(io.columns >= 1.U && io.columns <= 16.U)
    assert(io.activeOutputs === io.rows * io.columns)
    assert(io.programLength >= 2.U &&
      io.programLength <= RaveilBoundedProgramContract.ProgramCapacity.U)
    assert(io.programVersion >= 1.U && io.programVersion <= 4.U)
    when(state === loadRequest && busyReg && io.programVersion >= 3.U) {
      assert(relativeInputAddress >= 0.S)
      assert(relativeInputAddress < 324.S)
    }
    when(state === fetch && busyReg) {
      assert(opcode === RaveilBoundedProgramContract.LoadOpcode.U ||
        opcode === RaveilBoundedProgramContract.AddOpcode.U ||
        opcode === RaveilBoundedProgramContract.MaxU32Opcode.U ||
        (opcode === 5.U && io.programVersion === 4.U) ||
        opcode === RaveilBoundedProgramContract.StoreOpcode.U)
    }
    when(state === loadResponse && io.memory.response.valid) {
      assert(!io.memory.response.bits.write)
      assert(io.memory.response.bits.initiator === 2.U)
      assert(io.memory.response.bits.phase === 2.U)
    }
    when(state === storeResponse && io.memory.response.valid) {
      assert(io.memory.response.bits.write)
      assert(io.memory.response.bits.initiator === 2.U)
      assert(io.memory.response.bits.phase === 2.U)
    }
  }
}
