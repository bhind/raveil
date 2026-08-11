//> using scala 2.13.17
//> using dep org.chipsalliance::chisel:7.2.0
//> using plugin org.chipsalliance:::chisel-plugin:7.2.0

import chisel3._
import _root_.circt.stage.ChiselStage

class Counter extends Module {
  val io = IO(new Bundle {
    val enable = Input(Bool())
    val value = Output(UInt(4.W))
  })

  val count = RegInit(0.U(4.W))
  when(io.enable) {
    count := count + 1.U
  }
  io.value := count
}

object EmitCounter extends App {
  ChiselStage.emitSystemVerilogFile(
    new Counter,
    args = Array("--target-dir", "generated"),
    firtoolOpts = Array("-disable-all-randomization", "-strip-debug-info")
  )
}
