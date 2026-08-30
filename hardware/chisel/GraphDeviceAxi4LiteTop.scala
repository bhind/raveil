//> using scala 2.13.17
//> using dep org.chipsalliance::chisel:7.2.0
//> using plugin org.chipsalliance:::chisel-plugin:7.2.0

import chisel3._
import chisel3.util._
import _root_.circt.stage.ChiselStage

/** S03 AXI4-Lite shell: control, installers, and one bounded execution path. */
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
    val mutationKind = RegInit(0.U(4.W))
    val mutationAddress = RegInit(0.U(9.W))
    val mutationData = RegInit(0.U(32.W))
    val inputActive = RegInit(false.B)
    val inputIssued = RegInit(false.B)
    val stagedWords = RegInit(0.U(10.W))
    val outputActive = RegInit(false.B)
    val outputIssued = RegInit(false.B)
    val outputAddress = RegInit(0.U(8.W))
    val completedSticky = RegInit(false.B)
    val cancelledSticky = RegInit(false.B)
    val transportFault = RegInit(false.B)
    val outputSuppressed = RegInit(false.B)
    val core = withClockAndReset(aclk, (!aresetn || resetBarrier).asAsyncReset) { Module(new StaticStencilRegion) }
    core.io.inputStageValid := inputActive && !inputIssued
    core.io.inputStageAddress := mutationAddress
    core.io.inputStageData := mutationData
    core.io.inputStageResponseReady := inputActive && inputIssued
    core.io.fixtureStageStart := false.B; core.io.fixtureStageSeed := 0.U
    core.io.start := mutationApply && mutationKind === 8.U
    core.io.cancel := mutationApply && mutationKind === 9.U
    core.io.configClear := mutationApply && mutationKind === 1.U
    core.io.configWrite := mutationApply && mutationKind === 2.U
    core.io.configCommit := mutationApply && mutationKind === 3.U
    core.io.configAddress := mutationAddress(4, 0); core.io.configData := mutationData
    core.io.programClear := mutationApply && mutationKind === 4.U
    core.io.programWrite := mutationApply && mutationKind === 5.U
    core.io.programCommit := mutationApply && mutationKind === 6.U
    core.io.programAddress := mutationAddress(5, 0); core.io.programData := mutationData
    core.io.outputValidationValid := outputActive && !outputIssued
    core.io.outputValidationAddress := outputAddress
    core.io.outputValidationResponseReady := outputActive && outputIssued
    val busy = haveAw || haveW || haveB || haveR || pendingReset ||
      pendingMutation || resetBarrier || mutationApply || mutationBarrier ||
      inputActive || outputActive
    awready := !haveAw && !haveB && !haveR && !pendingReset && !pendingMutation &&
      !resetBarrier && !mutationApply && !mutationBarrier && !inputActive && !outputActive
    wready := !haveW && !haveB && !haveR && !pendingReset && !pendingMutation &&
      !resetBarrier && !mutationApply && !mutationBarrier && !inputActive && !outputActive
    // Give either write channel priority over AR when an idle target sees both
    // classes in one cycle. This keeps the target at one total transaction,
    // rather than one read plus one write.
    arready := !busy && !awvalid && !wvalid
    bvalid := haveB; bresp := savedBresp; rvalid := haveR; rdata := savedRdata; rresp := savedRresp
    when(haveB && bready) {
      haveB := false.B
      when(pendingReset) { pendingReset := false.B; resetBarrier := true.B }
      when(pendingMutation) {
        pendingMutation := false.B
        when(mutationKind === 7.U) {
          inputActive := true.B; inputIssued := false.B
        }.otherwise {
          mutationApply := true.B; mutationBarrier := true.B
        }
      }
    }
    when(haveR && rready) { haveR := false.B }
    when(resetBarrier) { resetBarrier := false.B }
    when(mutationApply) { mutationApply := false.B }
    when(mutationBarrier) { mutationBarrier := false.B }
    when(inputActive && !inputIssued && core.io.inputStageReady) {
      inputIssued := true.B
    }
    when(inputActive && inputIssued && core.io.inputStageResponseValid) {
      inputActive := false.B; inputIssued := false.B
      when(core.io.inputStageResponseError) { transportFault := true.B }
        .otherwise { stagedWords := stagedWords + 1.U }
    }
    when(outputActive && !outputIssued && core.io.outputValidationReady) {
      outputIssued := true.B
    }
    when(outputActive && outputIssued && core.io.outputValidationResponseValid) {
      outputActive := false.B; outputIssued := false.B; haveR := true.B
      savedRdata := core.io.outputValidationReadData
      savedRresp := Mux(core.io.outputValidationResponseError, 2.U, 0.U)
      when(core.io.outputValidationResponseError) { transportFault := true.B }
    }
    when(core.io.done) { completedSticky := true.B }
    when(core.io.cancelled) { cancelledSticky := true.B }
    when(mutationApply && mutationKind === 8.U) {
      stagedWords := 0.U; completedSticky := false.B; cancelledSticky := false.B
      outputSuppressed := false.B; transportFault := false.B
    }
    when(mutationApply && mutationKind === 9.U) {
      outputSuppressed := true.B; completedSticky := false.B
      when(!core.io.busy) { cancelledSticky := true.B }
    }
    when(awvalid && awready) { haveAw := true.B; savedAw := awaddr }
    when(wvalid && wready) { haveW := true.B; savedW := wdata; savedStrb := wstrb }
    when(haveAw && haveW && !haveB && !resetBarrier) {
      val aligned = savedAw(1, 0) === 0.U; val inAperture = savedAw < "h4000".U
      val reset = savedAw === "h0010".U && savedW === 4.U && savedStrb === "hf".U
      val exec = savedAw < "h2000".U
      val config = savedAw >= "h2000".U && savedAw < "h3000".U
      val program = savedAw >= "h3000".U && savedAw < "h4000".U
      // Execution spans 8 KiB and needs bit 12; each install namespace is a
      // separate 4 KiB window and uses only its namespace-relative low word.
      val word = Mux(exec, savedAw(12, 2), savedAw(11, 2).pad(11))
      val full = savedStrb === "hf".U
      val inputPayload = exec && word >= 256.U && word < 580.U &&
        (word - 256.U) === stagedWords && !core.io.busy
      val executionStart = exec && word === 4.U && savedW === 1.U &&
        stagedWords === 324.U && !core.io.busy && core.io.configInstalled &&
        !core.io.configLoading && !core.io.configFault &&
        core.io.programInstalled && !core.io.programLoading &&
        !core.io.programFault
      val executionCancel = exec && word === 4.U && savedW === 2.U && core.io.busy
      val configControl = config && word === 4.U && (savedW === 1.U || savedW === 2.U)
      val configPayload = config && word >= 256.U && word < 272.U
      val programControl = program && word === 4.U && (savedW === 1.U || savedW === 2.U)
      val programPayload = program && word >= 256.U && word < 288.U
      val mutation = full && (configControl || configPayload || programControl ||
        programPayload || inputPayload || executionStart || executionCancel)
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
          Mux(programControl, Mux(savedW === 1.U, 4.U, 6.U),
          Mux(programPayload, 5.U, Mux(inputPayload, 7.U,
          Mux(executionStart, 8.U, 9.U))))))
        mutationAddress := (word - 256.U)(8, 0)
        mutationData := savedW
      }
      when(aligned && inAperture && full && exec && word === 4.U &&
          !reset && !executionStart && !executionCancel) {
        transportFault := true.B
      }
    }
    when(arvalid && arready) {
      val aligned = araddr(1, 0); val exec = araddr < "h2000".U; val config = araddr >= "h2000".U && araddr < "h3000".U; val program = araddr >= "h3000".U && araddr < "h4000".U
      val inAperture = exec || config || program
      val word = Mux(exec, araddr(12, 2), araddr(11, 2).pad(11))
      val identity = Mux(exec, "h52560101".U, Mux(config, "h52564901".U, "h52565001".U))
      val executionFault = transportFault || core.io.configFault || core.io.programFault
      val authorizedOutput = core.io.outputValid && !outputSuppressed
      val status = Mux(exec,
        Cat(0.U(27.W), authorizedOutput, executionFault,
          cancelledSticky || core.io.cancelled,
          completedSticky || core.io.done, core.io.busy),
        Mux(config,
          Cat(0.U(29.W), core.io.configFault, core.io.configInstalled, core.io.configLoading),
          Cat(0.U(29.W), core.io.programFault, core.io.programInstalled, core.io.programLoading)))
      val count = Mux(exec, Mux(word === 6.U, 324.U, 256.U), Mux(config, core.io.configPayloadCount, core.io.programPayloadCount))
      val digest = (config || program) && word >= 16.U && word < 24.U
      val checksum = exec && authorizedOutput && (word === 40.U || word === 41.U)
      val output = exec && word >= 1024.U && word < 1280.U
      val readable = word === 0.U || word === 1.U || word === 5.U || word === 6.U ||
        (exec && word === 7.U) || digest || checksum
      val digestData = Mux(config, core.io.configLiveDigest((word - 16.U)(2, 0)), core.io.programLiveDigest((word - 16.U)(2, 0)))
      when(aligned === 0.U && output && authorizedOutput && !core.io.busy) {
        outputActive := true.B; outputIssued := false.B
        outputAddress := (word - 1024.U)(7, 0)
      }.otherwise {
        haveR := true.B
        savedRresp := Mux(aligned =/= 0.U || !inAperture, 3.U, Mux(readable, 0.U, 2.U))
        savedRdata := Mux(word === 0.U, identity,
          Mux(word === 1.U, 1.U,
          Mux(word === 5.U, status,
          Mux(word === 6.U || (exec && word === 7.U), count,
          Mux(checksum, Mux(word === 40.U, core.io.checksum(31, 0), core.io.checksum(63, 32)), digestData)))))
      }
    }
    when(resetBarrier) {
      stagedWords := 0.U; inputActive := false.B; inputIssued := false.B
      outputActive := false.B; outputIssued := false.B
      completedSticky := false.B; cancelledSticky := false.B
      transportFault := false.B; outputSuppressed := false.B
    }
  }
}

object EmitGraphDeviceAxi4LiteTop extends App {
  val target = args.dropWhile(_ != "--target-dir").drop(1).headOption.getOrElse("generated_axi4lite")
  ChiselStage.emitSystemVerilogFile(new GraphDeviceAxi4LiteTop, args = Array("--target-dir", target), firtoolOpts = Array("-disable-all-randomization", "-strip-debug-info"))
}
