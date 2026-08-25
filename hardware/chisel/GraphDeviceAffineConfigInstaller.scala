import chisel3._
import chisel3.util._

/**
  * Atomic, idle-only installation of a bounded affine stencil configuration.
  *
  * The execution ABI remains separate. A transaction must clear, write each
  * of the 16 payload words exactly once, and commit an admitted payload. Any
  * protocol or payload error is sticky until a later idle clear.
  */
class GraphDeviceAffineConfigInstaller extends Module {
  val io = IO(new Bundle {
    val clear = Input(Bool())
    val write = Input(Bool())
    val commit = Input(Bool())
    val address = Input(UInt(5.W))
    val data = Input(UInt(32.W))
    val busy = Input(Bool())

    val installed = Output(Bool())
    val loading = Output(Bool())
    val fault = Output(Bool())
    val payloadCount = Output(UInt(5.W))
    val rows = Output(UInt(5.W))
    val columns = Output(UInt(5.W))
    val inputStride = Output(UInt(9.W))
    val outputStride = Output(UInt(9.W))
    val activeOutputs = Output(UInt(9.W))
    val liveDigest = Output(Vec(8, UInt(32.W)))
  })

  private val baselineShape = Seq(16, 16, 18, 16, 256, 6)
  private val compactShape = Seq(8, 8, 10, 8, 64, 6)
  private val baselineDigestWords = Seq(
    2251327940L, 4185756549L, 4023038733L, 100796969L,
    1276851761L, 1857035043L, 1205398712L, 262225231L
  )
  private val compactDigestWords = Seq(
    1417482093L, 2721426421L, 408689994L, 2452827674L,
    3784938229L, 2858933455L, 600553447L, 266570466L
  )

  val payload = RegInit(VecInit(Seq.fill(16)(0.U(32.W))))
  val seen = RegInit("hffff".U(16.W))
  val nextIndex = RegInit(16.U(5.W))
  val loadingReg = RegInit(false.B)
  val installedReg = RegInit(true.B)
  val faultReg = RegInit(false.B)
  val rowsReg = RegInit(16.U(5.W))
  val columnsReg = RegInit(16.U(5.W))
  val inputStrideReg = RegInit(18.U(9.W))
  val outputStrideReg = RegInit(16.U(9.W))
  val activeOutputsReg = RegInit(256.U(9.W))
  val digestReg = RegInit(VecInit(baselineDigestWords.map(_.U(32.W))))

  def matchesPayload(shape: Seq[Int], digest: Seq[Long]): Bool = {
    val header = Seq(
      payload(0) === "h52414631".U(32.W),
      payload(1) === 1.U,
      payload(2) === shape(0).U,
      payload(3) === shape(1).U,
      payload(4) === shape(2).U,
      payload(5) === shape(3).U,
      payload(6) === shape(4).U,
      payload(7) === shape(5).U
    )
    val identity = (0 until 8).map { index =>
      payload(8 + index) === digest(index).U(32.W)
    }
    (header ++ identity).reduce(_ && _)
  }

  val validPayload = matchesPayload(baselineShape, baselineDigestWords) ||
    matchesPayload(compactShape, compactDigestWords)
  val commandCount = io.clear.asUInt +& io.write.asUInt +& io.commit.asUInt

  when(commandCount > 1.U) {
    faultReg := true.B
  }.elsewhen(io.clear) {
    when(io.busy) {
      faultReg := true.B
    }.otherwise {
      loadingReg := true.B
      installedReg := false.B
      faultReg := false.B
      seen := 0.U
      nextIndex := 0.U
    }
  }.elsewhen(io.write) {
    when(
      io.busy || !loadingReg || faultReg || io.address >= 16.U ||
        io.address =/= nextIndex || seen(io.address(3, 0))
    ) {
      faultReg := true.B
    }.otherwise {
      payload(io.address(3, 0)) := io.data
      seen := seen | (1.U(16.W) << io.address(3, 0))
      nextIndex := nextIndex + 1.U
    }
  }.elsewhen(io.commit) {
    when(
      io.busy || !loadingReg || faultReg || nextIndex =/= 16.U ||
        seen =/= "hffff".U ||
        !validPayload
    ) {
      faultReg := true.B
    }.otherwise {
      installedReg := true.B
      loadingReg := false.B
      rowsReg := payload(2)(4, 0)
      columnsReg := payload(3)(4, 0)
      inputStrideReg := payload(4)(8, 0)
      outputStrideReg := payload(5)(8, 0)
      activeOutputsReg := payload(6)(8, 0)
      for (index <- 0 until 8) {
        digestReg(index) := payload(8 + index)
      }
    }
  }

  io.installed := installedReg
  io.loading := loadingReg
  io.fault := faultReg
  io.payloadCount := nextIndex
  io.rows := rowsReg
  io.columns := columnsReg
  io.inputStride := inputStrideReg
  io.outputStride := outputStrideReg
  io.activeOutputs := activeOutputsReg
  io.liveDigest := digestReg

  when(!reset.asBool) {
    when(installedReg) {
      assert(!loadingReg)
      assert(activeOutputsReg === rowsReg * columnsReg)
      assert(rowsReg <= 16.U && columnsReg <= 16.U)
    }
  }
}
