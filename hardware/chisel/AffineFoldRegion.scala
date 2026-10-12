//> using scala 2.13.17
//> using dep org.chipsalliance::chisel:7.2.0
//> using plugin org.chipsalliance:::chisel-plugin:7.2.0

import chisel3._
import chisel3.util._
import _root_.circt.stage.ChiselStage

/** Standalone candidate ABI MF01. No dependency on the stencil installer.
  * One outstanding transaction; ready/valid has no latency promise.
  * Memory must remain private and inputs immutable until completion.
  * Reset requires the attached memory responder to be reset/drained too.
  */
class AffineFoldRegion extends Module {
  val io = IO(new Bundle {
    val cfg = Input(Vec(65, UInt(32.W)))
    val start = Input(Bool())
    val cancel = Input(Bool())
    val busy = Output(Bool())
    val done = Output(Bool())
    val success = Output(Bool())
    val fault = Output(Bool())
    val cancelled = Output(Bool())
    val req = Decoupled(new Bundle {
      val write = Bool()
      val address = UInt(10.W)
      val data = UInt(32.W)
    })
    val resp = Flipped(Decoupled(new Bundle {
      val data = UInt(32.W)
      val error = Bool()
    }))
  })
  val idle :: header :: validate :: execute :: request :: response :: Nil = Enum(6)
  val state = RegInit(idle)
  val cfg = Reg(Vec(65, UInt(32.W)))
  val pc = RegInit(0.U(5.W))
  val defined = RegInit(0.U(8.W))
  val values = RegInit(VecInit(Seq.fill(8)(0.U(32.W))))
  val i = RegInit(0.U(5.W))
  val j = RegInit(0.U(5.W))
  val k = RegInit(0.U(7.W))
  val acc = RegInit(0.U(32.W))
  val pendingCancel = RegInit(false.B)
  val done = RegInit(false.B)
  val success = RegInit(false.B)
  val fault = RegInit(false.B)
  val cancelled = RegInit(false.B)
  val reqWrite = RegInit(false.B)
  val reqAddress = RegInit(0.U(10.W))
  val reqData = RegInit(0.U(32.W))
  val loadDestination = RegInit(0.U(3.W))

  io.busy := state =/= idle
  io.done := done
  io.success := success
  io.fault := fault
  io.cancelled := cancelled
  io.req.valid := state === request
  io.req.bits.write := reqWrite
  io.req.bits.address := reqAddress
  io.req.bits.data := reqData
  io.resp.ready := state === response
  val abort = pendingCancel || io.cancel
  when(state =/= idle && io.cancel) { pendingCancel := true.B }

  def finish(ok: Bool, bad: Bool, stop: Bool): Unit = {
    state := idle
    done := true.B
    success := ok
    fault := bad
    cancelled := stop
  }
  val rows = cfg(1)
  val cols = cfg(2)
  val extent = cfg(3)
  val nviews = cfg(7)
  val ninst = cfg(8)
  val inst = cfg(49.U(7.W) + pc)
  val op = inst(31,28)
  val dst = inst(27,25)
  val a = inst(24,22)
  val b = inst(21,19)
  val immediate = inst(21,0)
  val sourceA = defined(a)
  val sourceB = defined(b)
  val isFinal = pc === ninst - 1.U
  val binary = op === 2.U || op === 4.U || op === 5.U
  val unary = op === 6.U || op === 7.U
  val instructionValid = Mux(isFinal,
    op === 3.U && dst === 0.U && immediate === 0.U && sourceA,
    (op === 1.U && a < nviews && immediate === 0.U) ||
    (binary && sourceA && sourceB && inst(18,0) === 0.U) ||
    (unary && sourceA))
  val viewsValid = (0 until 8).map { v =>
    val base = 9 + 5*v
    val buffer = cfg(base)
    val offset = cfg(base+1)
    val si = cfg(base+2)
    val sj = cfg(base+3)
    val sk = cfg(base+4)
    // Wide arithmetic before the extent check: no truncation can admit wrap.
    val last = offset.pad(64) + si.pad(64)*(rows-1.U) +
      sj.pad(64)*(cols-1.U) + sk.pad(64)*(extent-1.U)
    Mux(v.U < nviews,
      buffer <= 1.U && offset <= 323.U && si <= 323.U &&
      sj <= 323.U && sk <= 323.U &&
      last < Mux(buffer === 0.U, cfg(5), cfg(6)),
      (0 until 5).map(x => cfg(base+x) === 0.U).reduce(_ && _))
  }.reduce(_ && _)
  val unusedValid = (0 until 16).map { p =>
    p.U < ninst || cfg(49+p) === 0.U
  }.reduce(_ && _)
  val headerValid = cfg(0) === "h4d463031".U &&
    rows >= 1.U && rows <= 16.U && cols >= 1.U && cols <= 16.U &&
    extent >= 1.U && extent <= 64.U && cfg(4) <= 1.U &&
    cfg(5) <= 324.U && cfg(6) <= 324.U &&
    nviews >= 1.U && nviews <= 8.U && ninst >= 2.U && ninst <= 16.U &&
    viewsValid && unusedValid

  switch(state) {
    is(idle) {
      when(io.start) {
        cfg := io.cfg
        done := false.B
        success := false.B
        fault := false.B
        cancelled := false.B
        pendingCancel := io.cancel
        pc := 0.U
        defined := 0.U
        i := 0.U
        j := 0.U
        k := 0.U
        acc := 0.U
        values.foreach(_ := 0.U)
        state := header
      }
    }
    is(header) {
      when(abort) { finish(false.B, false.B, true.B) }
        .elsewhen(!headerValid) { finish(false.B, true.B, false.B) }
        .otherwise { state := validate }
    }
    is(validate) {
      when(abort) { finish(false.B, false.B, true.B) }
        .elsewhen(!instructionValid) { finish(false.B, true.B, false.B) }
        .elsewhen(isFinal) { pc := 0.U; state := execute }
        .otherwise {
          defined := defined | (1.U(8.W) << dst)
          pc := pc + 1.U
        }
    }
    is(execute) {
      when(abort) { finish(false.B, false.B, true.B) }
        .elsewhen(op === 1.U) {
          val viewBase = 9.U(7.W) + a * 5.U
          val buffer = cfg(viewBase)
          val address = cfg(viewBase+1.U).pad(64) +
            cfg(viewBase+2.U).pad(64)*i +
            cfg(viewBase+3.U).pad(64)*j +
            cfg(viewBase+4.U).pad(64)*k
          when(address >= Mux(buffer === 0.U, cfg(5), cfg(6))) {
            finish(false.B, true.B, false.B)
          }.otherwise {
            reqAddress := address + Mux(buffer === 0.U, 0.U, 324.U)
            reqData := 0.U
            reqWrite := false.B
            loadDestination := dst
            state := request
          }
        }.elsewhen(op === 3.U) {
          val next = Mux(cfg(4) === 0.U, acc + values(a), Mux(acc > values(a), acc, values(a)))
          when(k + 1.U === extent) {
            reqAddress := 648.U + i*cols + j
            reqData := next
            reqWrite := true.B
            state := request
          }.otherwise {
            acc := next
            k := k + 1.U
            pc := 0.U
            values.foreach(_ := 0.U)
          }
        }.otherwise {
          val result = WireDefault(0.U(32.W))
          switch(op) {
            is(2.U) { result := values(a) + values(b) }
            is(4.U) { result := Mux(values(a) > values(b), values(a), values(b)) }
            is(5.U) { result := values(a) * values(b) }
            is(6.U) { result := values(a) + immediate }
            is(7.U) { result := (values(a) >= immediate).asUInt }
          }
          values(dst) := result
          pc := pc + 1.U
        }
    }
    is(request) {
      // Even after cancel, a held offer cannot be withdrawn or modified.
      when(io.req.fire) { state := response }
    }
    is(response) {
      when(io.resp.fire) {
        when(abort || io.resp.bits.error) {
          finish(false.B, io.resp.bits.error, abort)
        }.elsewhen(!reqWrite) {
          values(loadDestination) := io.resp.bits.data
          pc := pc + 1.U
          state := execute
        }.elsewhen(i + 1.U === rows && j + 1.U === cols) {
          finish(true.B, false.B, false.B)
        }.otherwise {
          when(j + 1.U === cols) { i := i + 1.U; j := 0.U }
            .otherwise { j := j + 1.U }
          k := 0.U
          pc := 0.U
          acc := 0.U
          values.foreach(_ := 0.U)
          state := execute
        }
      }
    }
  }
  assert(!(success && io.busy))
  assert(!(success && (fault || cancelled)))
  when(io.req.valid) {
    assert(Mux(io.req.bits.write,
      io.req.bits.address >= 648.U && io.req.bits.address < 904.U,
      io.req.bits.address < 648.U))
  }
}

object EmitAffineFoldRegion extends App {
  ChiselStage.emitSystemVerilogFile(new AffineFoldRegion,
    args = Array("--target-dir", "generated_fold"),
    firtoolOpts = Array("-disable-all-randomization", "-strip-debug-info"))
}
