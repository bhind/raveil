//> using scala 2.13.17
//> using dep org.chipsalliance::chisel:7.2.0
//> using plugin org.chipsalliance:::chisel-plugin:7.2.0

import chisel3._
import chisel3.util._
import _root_.circt.stage.ChiselStage

/** S02 AXI4-Lite shell: control plus bounded installers, never graph I/O. */
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
    val pendingReset = RegInit(false.B)
    val resetBarrier = RegInit(false.B)
    val pendingMutation = RegInit(false.B)
    val mutationApply = RegInit(false.B)
    val mutationBarrier = RegInit(false.B)
    val mutationKind = RegInit(0.U(3.W))
    val mutationAddress = RegInit(0.U(6.W))
    val mutationData = RegInit(0.U(32.W))
    val core = withClockAndReset(aclk, (!aresetn || resetBarrier).asAsyncReset) { Module(new StaticStencilRegion) }
    core.io.inputStageValid := false.B; core.io.inputStageAddress := 0.U; core.io.inputStageData := 0.U; core.io.inputStageResponseReady := true.B
    core.io.fixtureStageStart := false.B; core.io.fixtureStageSeed := 0.U; core.io.start := false.B; core.io.cancel := false.B
    core.io.configClear := mutationApply && mutationKind === 1.U
    core.io.configWrite := mutationApply && mutationKind === 2.U
    core.io.configCommit := mutationApply && mutationKind === 3.U
    core.io.configAddress := mutationAddress(4, 0); core.io.configData := mutationData
    core.io.programClear := mutationApply && mutationKind === 4.U
    core.io.programWrite := mutationApply && mutationKind === 5.U
    core.io.programCommit := mutationApply && mutationKind === 6.U
    core.io.programAddress := mutationAddress; core.io.programData := mutationData
    core.io.outputValidationValid := false.B; core.io.outputValidationAddress := 0.U; core.io.outputValidationResponseReady := true.B
    val busy = haveAw || haveW || haveB || haveR || pendingReset ||
      pendingMutation || resetBarrier || mutationApply || mutationBarrier
    awready := !haveAw && !haveB && !haveR && !resetBarrier && !mutationApply && !mutationBarrier
    wready := !haveW && !haveB && !haveR && !resetBarrier && !mutationApply && !mutationBarrier
    // Give either write channel priority over AR when an idle target sees both
    // classes in one cycle. This keeps the target at one total transaction,
    // rather than one read plus one write.
    arready := !busy && !awvalid && !wvalid
    bvalid := haveB; bresp := savedBresp; rvalid := haveR; rdata := savedRdata; rresp := savedRresp
    when(haveB && bready) {
      haveB := false.B
      when(pendingReset) { pendingReset := false.B; resetBarrier := true.B }
      when(pendingMutation) {
        pendingMutation := false.B; mutationApply := true.B; mutationBarrier := true.B
      }
    }
    when(haveR && rready) { haveR := false.B }
    when(resetBarrier) { resetBarrier := false.B }
    when(mutationApply) { mutationApply := false.B }
    when(mutationBarrier) { mutationBarrier := false.B }
    when(awvalid && awready) { haveAw := true.B; savedAw := awaddr }
    when(wvalid && wready) { haveW := true.B; savedW := wdata; savedStrb := wstrb }
    when(haveAw && haveW && !haveB && !resetBarrier) {
      val aligned = savedAw(1, 0) === 0.U; val inAperture = savedAw < "h4000".U
      val reset = savedAw === "h0010".U && savedW === 4.U && savedStrb === "hf".U
      val config = savedAw >= "h2000".U && savedAw < "h3000".U
      val program = savedAw >= "h3000".U && savedAw < "h4000".U
      val word = savedAw(11, 2)
      val full = savedStrb === "hf".U
      val configControl = config && word === 4.U && (savedW === 1.U || savedW === 2.U)
      val configPayload = config && word >= 256.U && word < 272.U
      val programControl = program && word === 4.U && (savedW === 1.U || savedW === 2.U)
      val programPayload = program && word >= 256.U && word < 288.U
      val mutation = full && (configControl || configPayload || programControl || programPayload)
      val acceptedReset = aligned && inAperture && reset
      val acceptedMutation = aligned && inAperture && mutation
      haveAw := false.B; haveW := false.B; haveB := true.B
      savedBresp := Mux(!aligned || !inAperture, 3.U, Mux(acceptedReset || acceptedMutation, 0.U, 2.U))
      // Preserve the accepted write response. The core-only reset begins only
      // after the owner accepts B, then blocks one complete admission cycle.
      when(acceptedReset) { pendingReset := true.B }
      when(acceptedMutation) {
        pendingMutation := true.B
        mutationKind := Mux(configControl, Mux(savedW === 1.U, 1.U, 3.U),
          Mux(configPayload, 2.U,
          Mux(programControl, Mux(savedW === 1.U, 4.U, 6.U), 5.U)))
        mutationAddress := (word - 256.U)(5, 0)
        mutationData := savedW
      }
    }
    when(arvalid && arready) {
      val aligned = araddr(1, 0); val exec = araddr < "h2000".U; val config = araddr >= "h2000".U && araddr < "h3000".U; val program = araddr >= "h3000".U && araddr < "h4000".U
      val inAperture = exec || config || program; val word = araddr(11, 2)
      val identity = Mux(exec, "h52560101".U, Mux(config, "h52564901".U, "h52565001".U))
      val status = Mux(exec,
        Cat(0.U(27.W), core.io.outputValid, false.B, core.io.cancelled, core.io.done, core.io.busy),
        Mux(config,
          Cat(0.U(29.W), core.io.configFault, core.io.configInstalled, core.io.configLoading),
          Cat(0.U(29.W), core.io.programFault, core.io.programInstalled, core.io.programLoading)))
      val count = Mux(exec, Mux(word === 6.U, 324.U, 256.U), Mux(config, core.io.configPayloadCount, core.io.programPayloadCount))
      val digest = (config || program) && word >= 16.U && word < 24.U
      val readable = word === 0.U || word === 1.U || word === 5.U || word === 6.U || (exec && word === 7.U) || digest
      val digestData = Mux(config, core.io.configLiveDigest((word - 16.U)(2, 0)), core.io.programLiveDigest((word - 16.U)(2, 0)))
      haveR := true.B; savedRresp := Mux(aligned =/= 0.U || !inAperture, 3.U, Mux(readable, 0.U, 2.U)); savedRdata := Mux(word === 0.U, identity, Mux(word === 1.U, 1.U, Mux(word === 5.U, status, Mux(word === 6.U || (exec && word === 7.U), count, digestData))))
    }
  }
}

object EmitGraphDeviceAxi4LiteTop extends App {
  val target = args.dropWhile(_ != "--target-dir").drop(1).headOption.getOrElse("generated_axi4lite")
  ChiselStage.emitSystemVerilogFile(new GraphDeviceAxi4LiteTop, args = Array("--target-dir", target), firtoolOpts = Array("-disable-all-randomization", "-strip-debug-info"))
}
