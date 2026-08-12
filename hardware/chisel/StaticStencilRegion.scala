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
  * Fixed six-cycle schedule for the RFC-0005 uint32 five-point stencil.
  *
  * This module has no runtime dependency scheduler, token store, rename state,
  * ROB, general LSU, commit frontier, or issue-mode switching. Input and output
  * arrays model disjoint scratchpad bindings. Output bytes have no authority
  * unless outputValid is asserted after all 256 points complete.
  */
class StaticStencilRegion extends Module {
  val io = IO(new Bundle {
    val inputWriteEnable = Input(Bool())
    val inputWriteAddress = Input(UInt(9.W))
    val inputWriteData = Input(UInt(32.W))

    val start = Input(Bool())
    val cancel = Input(Bool())

    val outputReadAddress = Input(UInt(8.W))
    val outputReadData = Output(UInt(32.W))
    val outputValid = Output(Bool())
    val busy = Output(Bool())
    val done = Output(Bool())
    val cancelled = Output(Bool())
    val cycleCount = Output(UInt(14.W))
    val checksum = Output(UInt(64.W))
    val configurationTag = Output(UInt(64.W))
  })

  val inputScratchpad = RegInit(VecInit(Seq.fill(324)(0.U(32.W))))
  val outputScratchpad = RegInit(VecInit(Seq.fill(256)(0.U(32.W))))

  val busyReg = RegInit(false.B)
  val outputValidReg = RegInit(false.B)
  val doneReg = RegInit(false.B)
  val cancelledReg = RegInit(false.B)
  val outputIndex = RegInit(0.U(8.W))
  val phase = RegInit(0.U(3.W))
  val accumulator = RegInit(0.U(32.W))
  val cycleCountReg = RegInit(0.U(14.W))
  val checksumReg = RegInit(0.U(64.W))

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

  when(io.inputWriteEnable && !busyReg) {
    when(io.inputWriteAddress < 324.U) {
      inputScratchpad(io.inputWriteAddress) := io.inputWriteData
    }
  }

  when(io.cancel && busyReg) {
    busyReg := false.B
    outputValidReg := false.B
    cancelledReg := true.B
  }.elsewhen(busyReg) {
    cycleCountReg := cycleCountReg + 1.U
    switch(phase) {
      is(0.U) {
        accumulator := inputScratchpad(center)
        phase := 1.U
      }
      is(1.U) {
        accumulator := accumulator + inputScratchpad(center - 18.U)
        phase := 2.U
      }
      is(2.U) {
        accumulator := accumulator + inputScratchpad(center + 18.U)
        phase := 3.U
      }
      is(3.U) {
        accumulator := accumulator + inputScratchpad(center - 1.U)
        phase := 4.U
      }
      is(4.U) {
        accumulator := accumulator + inputScratchpad(center + 1.U)
        phase := 5.U
      }
      is(5.U) {
        outputScratchpad(outputIndex) := accumulator
        checksumReg := checksumReg + accumulator
        phase := 0.U
        when(outputIndex === 255.U) {
          busyReg := false.B
          outputValidReg := true.B
          doneReg := true.B
        }.otherwise {
          outputIndex := outputIndex + 1.U
        }
      }
    }
  }.elsewhen(io.start) {
    busyReg := true.B
    outputValidReg := false.B
    outputIndex := 0.U
    phase := 0.U
    accumulator := 0.U
    cycleCountReg := 0.U
    checksumReg := 0.U
  }

  io.outputReadData := outputScratchpad(io.outputReadAddress)
  io.outputValid := outputValidReg
  io.busy := busyReg
  io.done := doneReg
  io.cancelled := cancelledReg
  io.cycleCount := cycleCountReg
  io.checksum := checksumReg
  io.configurationTag := StaticStencilRegionContract.ConfigurationTagValue.U(64.W)
}

object EmitStaticStencilRegion extends App {
  ChiselStage.emitSystemVerilogFile(
    new StaticStencilRegion,
    args = Array("--target-dir", "generated_static"),
    firtoolOpts = Array("-disable-all-randomization", "-strip-debug-info")
  )
}
