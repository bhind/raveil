// Repository-owned, candidate-independent standard-cell memory realization.
//
// These seven synthesizable modules implement the exact macro interfaces emitted
// by the T-0044 integrated and matched-Rocket RTL exports. Storage is deliberately
// uninitialized. There is no reset behavior. A one-RW-port read is synchronous:
// RW0_rdata changes only at an enabled read edge and otherwise holds, including on
// writes. For memory_ext, read and byte-masked write clocks are independent;
// simultaneous same-address cross-clock read/write behavior is undefined.
`default_nettype none

module cc_dir_ext (
    input logic [9:0] RW0_addr, input logic RW0_en, input logic RW0_clk,
    input logic RW0_wmode, input logic [127:0] RW0_wdata,
    output logic [127:0] RW0_rdata, input logic [7:0] RW0_wmask
);
    logic [127:0] mem [0:1023];
    integer lane;
    always_ff @(posedge RW0_clk) begin
        if (RW0_en && RW0_wmode) begin
            for (lane = 0; lane < 8; lane = lane + 1)
                if (RW0_wmask[lane]) mem[RW0_addr][lane * 16 +: 16] <= RW0_wdata[lane * 16 +: 16];
        end else if (RW0_en) RW0_rdata <= mem[RW0_addr];
    end
endmodule

module cc_banks_0_ext (
    input logic [13:0] RW0_addr, input logic RW0_en, input logic RW0_clk,
    input logic RW0_wmode, input logic [63:0] RW0_wdata,
    output logic [63:0] RW0_rdata
);
    logic [63:0] mem [0:16383];
    always_ff @(posedge RW0_clk) begin
        if (RW0_en && RW0_wmode) mem[RW0_addr] <= RW0_wdata;
        else if (RW0_en) RW0_rdata <= mem[RW0_addr];
    end
endmodule

module data_arrays_0_ext (
    input logic [8:0] RW0_addr, input logic RW0_en, input logic RW0_clk,
    input logic RW0_wmode, input logic [255:0] RW0_wdata,
    output logic [255:0] RW0_rdata, input logic [31:0] RW0_wmask
);
    logic [255:0] mem [0:511];
    integer lane;
    always_ff @(posedge RW0_clk) begin
        if (RW0_en && RW0_wmode) begin
            for (lane = 0; lane < 32; lane = lane + 1)
                if (RW0_wmask[lane]) mem[RW0_addr][lane * 8 +: 8] <= RW0_wdata[lane * 8 +: 8];
        end else if (RW0_en) RW0_rdata <= mem[RW0_addr];
    end
endmodule

module tag_array_ext (
    input logic [5:0] RW0_addr, input logic RW0_en, input logic RW0_clk,
    input logic RW0_wmode, input logic [87:0] RW0_wdata,
    output logic [87:0] RW0_rdata, input logic [3:0] RW0_wmask
);
    logic [87:0] mem [0:63];
    integer lane;
    always_ff @(posedge RW0_clk) begin
        if (RW0_en && RW0_wmode) begin
            for (lane = 0; lane < 4; lane = lane + 1)
                if (RW0_wmask[lane]) mem[RW0_addr][lane * 22 +: 22] <= RW0_wdata[lane * 22 +: 22];
        end else if (RW0_en) RW0_rdata <= mem[RW0_addr];
    end
endmodule

module tag_array_0_ext (
    input logic [5:0] RW0_addr, input logic RW0_en, input logic RW0_clk,
    input logic RW0_wmode, input logic [83:0] RW0_wdata,
    output logic [83:0] RW0_rdata, input logic [3:0] RW0_wmask
);
    logic [83:0] mem [0:63];
    integer lane;
    always_ff @(posedge RW0_clk) begin
        if (RW0_en && RW0_wmode) begin
            for (lane = 0; lane < 4; lane = lane + 1)
                if (RW0_wmask[lane]) mem[RW0_addr][lane * 21 +: 21] <= RW0_wdata[lane * 21 +: 21];
        end else if (RW0_en) RW0_rdata <= mem[RW0_addr];
    end
endmodule

module data_arrays_0_0_ext (
    input logic [8:0] RW0_addr, input logic RW0_en, input logic RW0_clk,
    input logic RW0_wmode, input logic [127:0] RW0_wdata,
    output logic [127:0] RW0_rdata, input logic [3:0] RW0_wmask
);
    logic [127:0] mem [0:511];
    integer lane;
    always_ff @(posedge RW0_clk) begin
        if (RW0_en && RW0_wmode) begin
            for (lane = 0; lane < 4; lane = lane + 1)
                if (RW0_wmask[lane]) mem[RW0_addr][lane * 32 +: 32] <= RW0_wdata[lane * 32 +: 32];
        end else if (RW0_en) RW0_rdata <= mem[RW0_addr];
    end
endmodule

module memory_ext (
    input logic [9:0] R0_addr, input logic R0_en, input logic R0_clk,
    output logic [31:0] R0_data, input logic [9:0] W0_addr,
    input logic W0_en, input logic W0_clk, input logic [31:0] W0_data,
    input logic [3:0] W0_mask
);
    logic [31:0] mem [0:1023];
    integer lane;
    always_ff @(posedge W0_clk) begin
        if (W0_en) begin
            for (lane = 0; lane < 4; lane = lane + 1)
                if (W0_mask[lane]) mem[W0_addr][lane * 8 +: 8] <= W0_data[lane * 8 +: 8];
        end
    end
    always_ff @(posedge R0_clk) begin
        if (R0_en) R0_data <= mem[R0_addr];
    end
endmodule

`default_nettype wire
