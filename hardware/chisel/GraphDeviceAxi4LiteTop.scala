//> using scala 2.13.17
//> using dep org.chipsalliance::chisel:7.2.0
//> using plugin org.chipsalliance:::chisel-plugin:7.2.0

import chisel3._
import chisel3.util._
import _root_.circt.stage.ChiselStage

/** S01-only AXI4-Lite control shell: identity/status/reset, not graph I/O. */
class GraphDeviceAxi4LiteTop extends RawModule {
  val aclk = IO(Input(Clock()))
  val aresetn = IO(Input(Bool()))
  val awaddr = IO(Input(UInt(32.W))); val awvalid = IO(Input(Bool())); val awready = IO(Output(Bool()))
  val wdata = IO(Input(UInt(32.W))); val wstrb = IO(Input(UInt(4.W))); val wvalid = IO(Input(Bool())); val wready = IO(Output(Bool()))
  val bresp = IO(Output(UInt(2.W))); val bvalid = IO(Output(Bool())); val bready = IO(Input(Bool()))
  val araddr = IO(Input(UInt(32.W))); val arvalid = IO(Input(Bool())); val arready = IO(Output(Bool()))
  val rdata = IO(Output(UInt(32.W))); val rresp = IO(Output(UInt(2.W))); val rvalid = IO(Output(Bool())); val rready = IO(Input(Bool()))

  withClockAndReset(aclk, (!aresetn).asAsyncReset) {
    val haveAw = RegInit(false.B); val savedAw = Reg(UInt(32.W))
    val haveW = RegInit(false.B); val savedW = Reg(UInt(32.W)); val savedStrb = Reg(UInt(4.W))
    val haveB = RegInit(false.B); val savedBresp = RegInit(0.U(2.W))
    val haveR = RegInit(false.B); val savedRdata = RegInit(0.U(32.W)); val savedRresp = RegInit(0.U(2.W))
    val resetBarrier = RegInit(false.B)
    val core = withClockAndReset(aclk, (!aresetn || resetBarrier).asAsyncReset) { Module(new StaticStencilRegion) }
    core.io.inputStageValid := false.B; core.io.inputStageAddress := 0.U; core.io.inputStageData := 0.U; core.io.inputStageResponseReady := true.B
    core.io.fixtureStageStart := false.B; core.io.fixtureStageSeed := 0.U; core.io.start := false.B; core.io.cancel := false.B
    core.io.configClear := false.B; core.io.configWrite := false.B; core.io.configCommit := false.B; core.io.configAddress := 0.U; core.io.configData := 0.U
    core.io.programClear := false.B; core.io.programWrite := false.B; core.io.programCommit := false.B; core.io.programAddress := 0.U; core.io.programData := 0.U
    core.io.outputValidationValid := false.B; core.io.outputValidationAddress := 0.U; core.io.outputValidationResponseReady := true.B
    val busy = haveAw || haveW || haveB || haveR || resetBarrier
    awready := !haveAw && !haveB && !haveR && !resetBarrier
    wready := !haveW && !haveB && !haveR && !resetBarrier
    arready := !busy; bvalid := haveB; bresp := savedBresp; rvalid := haveR; rdata := savedRdata; rresp := savedRresp
    when(haveB && bready) { haveB := false.B }; when(haveR && rready) { haveR := false.B }; when(resetBarrier) { resetBarrier := false.B }
    when(awvalid && awready) { haveAw := true.B; savedAw := awaddr }
    when(wvalid && wready) { haveW := true.B; savedW := wdata; savedStrb := wstrb }
    when(haveAw && haveW && !haveB && !resetBarrier) {
      val aligned = savedAw(1, 0) === 0.U; val inAperture = savedAw < "h4000".U
      val reset = savedAw === "h0010".U && savedW === 4.U && savedStrb === "hf".U
      haveAw := false.B; haveW := false.B; haveB := true.B
      savedBresp := Mux(!aligned || !inAperture, 3.U, Mux(reset, 0.U, 2.U))
      when(reset) { resetBarrier := true.B }
    }
    when(arvalid && arready) {
      val aligned = araddr(1, 0); val exec = araddr < "h2000".U; val config = araddr >= "h2000".U && araddr < "h3000".U; val program = araddr >= "h3000".U && araddr < "h4000".U
      val inAperture = exec || config || program; val word = araddr(11, 2)
      val identity = Mux(exec, "h52560101".U, Mux(config, "h52564901".U, "h52565001".U))
      val status = Mux(exec, Cat(0.U(27.W), core.io.outputValid, false.B, core.io.cancelled, core.io.done, core.io.busy), Mux(config, Cat(0.U(27.W), core.io.configFault, false.B, core.io.configInstalled, core.io.configLoading, false.B), Cat(0.U(27.W), core.io.programFault, false.B, core.io.programInstalled, core.io.programLoading, false.B)))
      val count = Mux(exec, Mux(word === 6.U, 324.U, 256.U), Mux(config, core.io.configPayloadCount, core.io.programPayloadCount))
      val readable = word === 0.U || word === 1.U || word === 5.U || word === 6.U || (exec && word === 7.U)
      haveR := true.B; savedRresp := Mux(aligned =/= 0.U || !inAperture, 3.U, Mux(readable, 0.U, 2.U)); savedRdata := Mux(word === 0.U, identity, Mux(word === 1.U, 1.U, Mux(word === 5.U, status, count)))
    }
  }
}

object EmitGraphDeviceAxi4LiteTop extends App {
  val target = args.dropWhile(_ != "--target-dir").drop(1).headOption.getOrElse("generated_axi4lite")
  ChiselStage.emitSystemVerilogFile(new GraphDeviceAxi4LiteTop, args = Array("--target-dir", target), firtoolOpts = Array("-disable-all-randomization", "-strip-debug-info"))
}
