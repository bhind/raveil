package chipyard.raveil

import chisel3._
import chisel3.util._

/**
  * The explicit owned-memory client seam for the fixed static stencil.
  *
  * This is deliberately a plain Chisel request/response interface rather than
  * a TileLink interface. A later attachment may translate this one-client,
  * maximum-one-outstanding boundary to a system fabric without changing the
  * fixed schedule below.
  */
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
  * Exact fixed 13-state execution schedule for the RFC-0005 stencil.
  *
  * Staging, validation, fixture lifecycle, and public result ownership remain
  * in the compatibility wrapper. This core owns only execution state and its
  * single explicit memory client port.
  */
class RaveilStaticStencilCore extends Module {
  val io = IO(new Bundle {
    val start = Input(Bool())
    val cancel = Input(Bool())
    val memory = new RaveilStaticStencilMemoryPort

    val busy = Output(Bool())
    val completion = Output(Bool())
    val cancellation = Output(Bool())
    val cycleCount = Output(UInt(14.W))
    val checksum = Output(UInt(64.W))
    val graphInputReadsAccepted = Output(UInt(16.W))
    val graphOutputWritesAccepted = Output(UInt(16.W))
  })

  val busyReg = RegInit(false.B)
  val outputIndex = RegInit(0.U(8.W))
  val accumulator = RegInit(0.U(32.W))
  val cycleCountReg = RegInit(0.U(14.W))
  val checksumReg = RegInit(0.U(64.W))
  val graphInputReadsAcceptedReg = RegInit(0.U(16.W))
  val graphOutputWritesAcceptedReg = RegInit(0.U(16.W))
  val cancelRequestedReg = RegInit(false.B)

  val Seq(
    idle,
    loadCenterRequest,
    loadCenterResponse,
    loadNorthRequest,
    loadNorthResponse,
    loadSouthRequest,
    loadSouthResponse,
    loadWestRequest,
    loadWestResponse,
    loadEastRequest,
    loadEastResponse,
    storeRequest,
    storeResponse
  ) = Enum(13)
  val state = RegInit(idle)

  val y = Wire(UInt(5.W))
  val x = Wire(UInt(5.W))
  val scaledY = Wire(UInt(9.W))
  val center = Wire(UInt(9.W))
  y := outputIndex(7, 4).pad(5) + 1.U(5.W)
  x := outputIndex(3, 0).pad(5) + 1.U(5.W)
  scaledY := y * 18.U
  center := scaledY + x

  val cancelling = io.cancel || cancelRequestedReg
  val graphInputRequest = busyReg && !cancelling && (
    state === loadCenterRequest || state === loadNorthRequest ||
    state === loadSouthRequest || state === loadWestRequest ||
    state === loadEastRequest)
  val graphOutputRequest = busyReg && !cancelling && state === storeRequest
  val graphInputResponseState = busyReg && (
    state === loadCenterResponse || state === loadNorthResponse ||
    state === loadSouthResponse || state === loadWestResponse ||
    state === loadEastResponse)

  val inputAddress = Wire(UInt(9.W))
  inputAddress := center
  when(state === loadNorthRequest) { inputAddress := center - 18.U }
  when(state === loadSouthRequest) { inputAddress := center + 18.U }
  when(state === loadWestRequest) { inputAddress := center - 1.U }
  when(state === loadEastRequest) { inputAddress := center + 1.U }

  io.memory.request.valid := graphInputRequest || graphOutputRequest
  io.memory.request.bits.write := graphOutputRequest
  io.memory.request.bits.address := Mux(graphOutputRequest,
    324.U(10.W) + outputIndex.pad(10), inputAddress.pad(10))
  io.memory.request.bits.writeData := accumulator
  io.memory.request.bits.writeMask := Mux(graphOutputRequest, "hf".U, 0.U)
  io.memory.request.bits.initiator := 2.U // Graph
  io.memory.request.bits.phase := 2.U // Execution
  io.memory.response.ready := graphInputResponseState || state === storeResponse

  val requestFire = io.memory.request.valid && io.memory.request.ready
  val responseFire = io.memory.response.valid && io.memory.response.ready

  val completion = busyReg && !cancelling && state === storeResponse &&
    outputIndex === 255.U && responseFire &&
    !io.memory.response.bits.error
  val storeFailure = busyReg && state === storeResponse &&
    responseFire &&
    io.memory.response.bits.error
  val cancellation = busyReg && cancelling && !io.memory.pending

  when(io.cancel && busyReg) {
    cancelRequestedReg := true.B
  }

  when(cancelling && busyReg) {
    when(!io.memory.pending) {
      busyReg := false.B
      cancelRequestedReg := false.B
      state := idle
    }
  }.elsewhen(busyReg) {
    cycleCountReg := cycleCountReg + 1.U
    switch(state) {
      is(loadCenterRequest) {
        when(requestFire) {
          graphInputReadsAcceptedReg := graphInputReadsAcceptedReg + 1.U
          state := loadCenterResponse
        }
      }
      is(loadCenterResponse) {
        when(responseFire) {
          accumulator := io.memory.response.bits.readData
          state := loadNorthRequest
        }
      }
      is(loadNorthRequest) {
        when(requestFire) {
          graphInputReadsAcceptedReg := graphInputReadsAcceptedReg + 1.U
          state := loadNorthResponse
        }
      }
      is(loadNorthResponse) {
        when(responseFire) {
          accumulator := accumulator + io.memory.response.bits.readData
          state := loadSouthRequest
        }
      }
      is(loadSouthRequest) {
        when(requestFire) {
          graphInputReadsAcceptedReg := graphInputReadsAcceptedReg + 1.U
          state := loadSouthResponse
        }
      }
      is(loadSouthResponse) {
        when(responseFire) {
          accumulator := accumulator + io.memory.response.bits.readData
          state := loadWestRequest
        }
      }
      is(loadWestRequest) {
        when(requestFire) {
          graphInputReadsAcceptedReg := graphInputReadsAcceptedReg + 1.U
          state := loadWestResponse
        }
      }
      is(loadWestResponse) {
        when(responseFire) {
          accumulator := accumulator + io.memory.response.bits.readData
          state := loadEastRequest
        }
      }
      is(loadEastRequest) {
        when(requestFire) {
          graphInputReadsAcceptedReg := graphInputReadsAcceptedReg + 1.U
          state := loadEastResponse
        }
      }
      is(loadEastResponse) {
        when(responseFire) {
          accumulator := accumulator + io.memory.response.bits.readData
          state := storeRequest
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
          when(io.memory.response.bits.error) {
            busyReg := false.B
            state := idle
          }.otherwise {
            checksumReg := checksumReg + accumulator
            when(outputIndex === 255.U) {
              busyReg := false.B
              state := idle
            }.otherwise {
              outputIndex := outputIndex + 1.U
              state := loadCenterRequest
            }
          }
        }
      }
    }
  }.elsewhen(io.start) {
    busyReg := true.B
    outputIndex := 0.U
    state := loadCenterRequest
    accumulator := 0.U
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

  when(!reset.asBool) {
    when(graphInputResponseState && io.memory.response.valid) {
      assert(!io.memory.response.bits.error)
      assert(!io.memory.response.bits.write)
      assert(io.memory.response.bits.initiator === 2.U)
      assert(io.memory.response.bits.phase === 2.U)
    }
    when(busyReg && state === storeResponse && io.memory.response.valid) {
      assert(io.memory.response.bits.write)
      assert(io.memory.response.bits.initiator === 2.U)
      assert(io.memory.response.bits.phase === 2.U)
    }
  }
}
