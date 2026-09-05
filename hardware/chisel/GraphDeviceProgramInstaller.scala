//> using scala 2.13.17
//> using dep org.chipsalliance::chisel:7.2.0
//> using plugin org.chipsalliance:::chisel-plugin:7.2.0

import chisel3._
import chisel3.util._
import chipyard.raveil.RaveilBoundedProgramContract

/**
  * Task-neutral installer for one bounded executor program.
  *
  * The transport is intentionally separate from both execution control and
  * affine configuration. Writes are ordered, idle-only, and fail closed.
  */
class GraphDeviceProgramInstaller extends Module {
  val io = IO(new Bundle {
    val clear = Input(Bool())
    val write = Input(Bool())
    val commit = Input(Bool())
    val address = Input(UInt(6.W))
    val data = Input(UInt(32.W))
    val busy = Input(Bool())

    val installed = Output(Bool())
    val loading = Output(Bool())
    val fault = Output(Bool())
    val payloadCount = Output(UInt(6.W))
    val liveDigest = Output(Vec(8, UInt(32.W)))
    val programVersion = Output(UInt(3.W))
    val programLength = Output(UInt(5.W))
    val program = Output(Vec(RaveilBoundedProgramContract.ProgramCapacity,
      UInt(32.W)))
  })

  val payload = RegInit(VecInit(Seq.fill(
    RaveilBoundedProgramContract.PayloadWords)(0.U(32.W))))
  val payloadCountReg = RegInit(0.U(6.W))
  val installedReg = RegInit(true.B)
  val faultReg = RegInit(false.B)
  val programLengthReg = RegInit(
    RaveilBoundedProgramContract.FactoryProgram.length.U(5.W))
  val programVersionReg = RegInit(RaveilBoundedProgramContract.Version.U(3.W))
  val programReg = RegInit(VecInit(
    RaveilBoundedProgramContract.FactoryProgram.map(_.U(32.W)) ++
      Seq.fill(RaveilBoundedProgramContract.ProgramCapacity -
        RaveilBoundedProgramContract.FactoryProgram.length)(0.U(32.W))))
  val digestReg = RegInit(VecInit(
    RaveilBoundedProgramContract.FactoryDigestWords.map(_.U(32.W))))

  var programValid = true.B
  var defined = 0.U(RaveilBoundedProgramContract.ValueRegisters.W)
  var storeCount = 0.U(5.W)
  val instructionCount = payload(2)(4, 0)
  val payloadVersion = payload(1)
  for (index <- 0 until RaveilBoundedProgramContract.ProgramCapacity) {
    val instruction = payload(12 + index)
    val active = index.U < instructionCount
    val opcode = instruction(31, 28)
    val destination = instruction(27, 25)
    val sourceA = instruction(24, 22)
    val sourceB = instruction(21, 19)
    val selector = instruction(24, 22)
    val legacyLoadValid = opcode === RaveilBoundedProgramContract.LoadOpcode.U &&
      payloadVersion =/= 3.U && payloadVersion =/= 4.U &&
      selector <= RaveilBoundedProgramContract.EastAddress.U &&
      instruction(21, 0) === 0.U
    val relativeRow = instruction(24, 20)
    val relativeColumn = instruction(19, 15)
    val relativeRowValid = relativeRow === 0.U || relativeRow === 1.U ||
      relativeRow === "h1f".U
    val relativeColumnValid = relativeColumn === 0.U ||
      relativeColumn === 1.U || relativeColumn === "h1f".U
    val relativeLoadValid = opcode === RaveilBoundedProgramContract.LoadOpcode.U &&
      (payloadVersion === 3.U || payloadVersion === 4.U) && relativeRowValid && relativeColumnValid &&
      instruction(14, 0) === 0.U
    val loadValid = legacyLoadValid || relativeLoadValid
    val addValid = opcode === RaveilBoundedProgramContract.AddOpcode.U &&
      instruction(18, 0) === 0.U && defined(sourceA) && defined(sourceB)
    val maxValid = opcode === RaveilBoundedProgramContract.MaxU32Opcode.U &&
      (payloadVersion === 2.U || payloadVersion === 3.U || payloadVersion === 4.U) &&
      instruction(18, 0) === 0.U && defined(sourceA) && defined(sourceB)
    val mulValid = opcode === 5.U && payloadVersion === 4.U &&
      instruction(18, 0) === 0.U && defined(sourceA) && defined(sourceB)
    val storeValid = opcode === RaveilBoundedProgramContract.StoreOpcode.U &&
      instruction(24, 0) === 0.U && defined(destination) &&
      index.U === instructionCount - 1.U
    val valid = loadValid || addValid || maxValid || mulValid || storeValid
    programValid = programValid && Mux(active, valid, instruction === 0.U)
    val writesValue = active && (loadValid || addValid || maxValid || mulValid)
    defined = Mux(writesValue, defined | (1.U << destination), defined)
    storeCount = storeCount + Mux(active && storeValid, 1.U, 0.U)
  }
  var reservedZero = true.B
  for (index <- 28 until RaveilBoundedProgramContract.PayloadWords) {
    reservedZero = reservedZero && payload(index) === 0.U
  }
  val payloadValid =
    payloadCountReg === RaveilBoundedProgramContract.PayloadWords.U &&
    payload(0) === RaveilBoundedProgramContract.Magic.U &&
    (payloadVersion === RaveilBoundedProgramContract.Version.U ||
      payloadVersion === 2.U || payloadVersion === 3.U || payloadVersion === 4.U) &&
    instructionCount >= 2.U &&
    instructionCount <= RaveilBoundedProgramContract.ProgramCapacity.U &&
    payload(3) === RaveilBoundedProgramContract.ValueRegisters.U &&
    payload(12)(31, 28) === RaveilBoundedProgramContract.LoadOpcode.U &&
    storeCount === 1.U && programValid && reservedZero

  val mutation = io.clear || io.write || io.commit
  when(mutation && io.busy) {
    faultReg := true.B
    installedReg := false.B
  }.elsewhen(io.clear) {
    payloadCountReg := 0.U
    installedReg := false.B
    faultReg := false.B
  }.elsewhen(io.write) {
    when(!installedReg && !faultReg &&
        payloadCountReg < RaveilBoundedProgramContract.PayloadWords.U &&
        io.address === payloadCountReg) {
      payload(io.address(4, 0)) := io.data
      payloadCountReg := payloadCountReg + 1.U
    }.otherwise {
      faultReg := true.B
      installedReg := false.B
    }
  }.elsewhen(io.commit) {
    when(!faultReg && payloadValid) {
      programLengthReg := instructionCount
      programVersionReg := payloadVersion(2, 0)
      for (index <- 0 until RaveilBoundedProgramContract.ProgramCapacity) {
        programReg(index) := payload(12 + index)
      }
      for (index <- 0 until 8) { digestReg(index) := payload(4 + index) }
      installedReg := true.B
    }.otherwise {
      faultReg := true.B
      installedReg := false.B
    }
  }

  io.installed := installedReg
  io.loading := payloadCountReg =/= 0.U && !installedReg && !faultReg
  io.fault := faultReg
  io.payloadCount := payloadCountReg
  io.liveDigest := digestReg
  io.programVersion := programVersionReg
  io.programLength := programLengthReg
  io.program := programReg

  when(!reset.asBool) {
    assert(!(installedReg && faultReg))
    when(io.busy) { assert(!io.loading || !installedReg) }
    when(io.write && !io.busy && !installedReg && !faultReg) {
      assert(io.address === payloadCountReg)
    }
  }
}
