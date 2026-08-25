`timescale 1ns/1ps
`default_nettype none

module exp0011_common_stdcell_memory_tb;
    logic clk = 1'b0;
    logic read_clk = 1'b0;
    logic write_clk = 1'b0;
    always #5 clk = ~clk;
    always #7 read_clk = ~read_clk;
    always #11 write_clk = ~write_clk;

    logic [9:0] d_addr; logic d_en, d_wmode; logic [127:0] d_wdata, d_rdata; logic [7:0] d_mask;
    logic [13:0] b_addr; logic b_en, b_wmode; logic [63:0] b_wdata, b_rdata;
    logic [8:0] da_addr; logic da_en, da_wmode; logic [255:0] da_wdata, da_rdata; logic [31:0] da_mask;
    logic [5:0] t_addr; logic t_en, t_wmode; logic [87:0] t_wdata, t_rdata; logic [3:0] t_mask;
    logic [5:0] t0_addr; logic t0_en, t0_wmode; logic [83:0] t0_wdata, t0_rdata; logic [3:0] t0_mask;
    logic [8:0] da0_addr; logic da0_en, da0_wmode; logic [127:0] da0_wdata, da0_rdata; logic [3:0] da0_mask;
    logic [9:0] m_raddr, m_waddr; logic m_ren, m_wen; logic [31:0] m_rdata, m_wdata; logic [3:0] m_mask;

    logic [127:0] d_expected;
    logic [255:0] da_expected;
    logic [87:0] t_expected;
    logic [83:0] t0_expected;
    logic [127:0] da0_expected;
    integer checks = 0;

    cc_dir_ext u_dir(.RW0_addr(d_addr), .RW0_en(d_en), .RW0_clk(clk), .RW0_wmode(d_wmode), .RW0_wdata(d_wdata), .RW0_rdata(d_rdata), .RW0_wmask(d_mask));
    cc_banks_0_ext u_banks(.RW0_addr(b_addr), .RW0_en(b_en), .RW0_clk(clk), .RW0_wmode(b_wmode), .RW0_wdata(b_wdata), .RW0_rdata(b_rdata));
    data_arrays_0_ext u_data(.RW0_addr(da_addr), .RW0_en(da_en), .RW0_clk(clk), .RW0_wmode(da_wmode), .RW0_wdata(da_wdata), .RW0_rdata(da_rdata), .RW0_wmask(da_mask));
    tag_array_ext u_tag(.RW0_addr(t_addr), .RW0_en(t_en), .RW0_clk(clk), .RW0_wmode(t_wmode), .RW0_wdata(t_wdata), .RW0_rdata(t_rdata), .RW0_wmask(t_mask));
    tag_array_0_ext u_tag0(.RW0_addr(t0_addr), .RW0_en(t0_en), .RW0_clk(clk), .RW0_wmode(t0_wmode), .RW0_wdata(t0_wdata), .RW0_rdata(t0_rdata), .RW0_wmask(t0_mask));
    data_arrays_0_0_ext u_data0(.RW0_addr(da0_addr), .RW0_en(da0_en), .RW0_clk(clk), .RW0_wmode(da0_wmode), .RW0_wdata(da0_wdata), .RW0_rdata(da0_rdata), .RW0_wmask(da0_mask));
    memory_ext u_memory(.R0_addr(m_raddr), .R0_en(m_ren), .R0_clk(read_clk), .R0_data(m_rdata), .W0_addr(m_waddr), .W0_en(m_wen), .W0_clk(write_clk), .W0_data(m_wdata), .W0_mask(m_mask));

    task automatic tick;
        @(posedge clk); #1;
    endtask
    task automatic check_value(input logic condition, input string label);
        if (!condition) $fatal(1, "FAILED: %s", label);
        checks = checks + 1;
    endtask

    initial begin
        d_en=0; d_wmode=0; d_addr='0; d_wdata='0; d_mask='0;
        b_en=0; b_wmode=0; b_addr='0; b_wdata='0;
        da_en=0; da_wmode=0; da_addr='0; da_wdata='0; da_mask='0;
        t_en=0; t_wmode=0; t_addr='0; t_wdata='0; t_mask='0;
        t0_en=0; t0_wmode=0; t0_addr='0; t0_wdata='0; t0_mask='0;
        da0_en=0; da0_wmode=0; da0_addr='0; da0_wdata='0; da0_mask='0;
        m_ren=0; m_wen=0; m_raddr='0; m_waddr='0; m_wdata='0; m_mask='0;

        // cc_dir_ext: full write/read, disabled hold, masked write, write hold.
        @(negedge clk); d_addr=10'd3; d_en=1; d_wmode=1; d_wdata=128'h00112233445566778899aabbccddeeff; d_mask='1; tick();
        @(negedge clk); d_wmode=0; tick(); check_value(d_rdata===128'h00112233445566778899aabbccddeeff, "cc_dir full read");
        @(negedge clk); d_en=0; d_addr=10'd4; tick(); check_value(d_rdata===128'h00112233445566778899aabbccddeeff, "cc_dir disabled hold");
        d_expected=128'h00112233445566778899aabbccddeeff; d_expected[47:32]=16'h5aa5;
        @(negedge clk); d_addr=10'd3; d_en=1; d_wmode=1; d_wdata='0; d_wdata[47:32]=16'h5aa5; d_mask=8'b00000100; tick();
        check_value(d_rdata===128'h00112233445566778899aabbccddeeff, "cc_dir write hold");
        @(negedge clk); d_wmode=0; tick(); check_value(d_rdata===d_expected, "cc_dir masked read"); d_en=0;

        // cc_banks_0_ext: full write/read and both hold cases.
        @(negedge clk); b_addr=14'd9000; b_en=1; b_wmode=1; b_wdata=64'h0123456789abcdef; tick();
        @(negedge clk); b_wmode=0; tick(); check_value(b_rdata===64'h0123456789abcdef, "cc_banks full read");
        @(negedge clk); b_en=0; tick(); check_value(b_rdata===64'h0123456789abcdef, "cc_banks disabled hold");
        @(negedge clk); b_en=1; b_wmode=1; b_addr=14'd9001; b_wdata=64'hfedcba9876543210; tick();
        check_value(b_rdata===64'h0123456789abcdef, "cc_banks write hold"); b_en=0;

        // data_arrays_0_ext: byte-mask behavior plus synchronous/hold behavior.
        @(negedge clk); da_addr=9'd17; da_en=1; da_wmode=1; da_wdata={8{32'h10203040}}; da_mask='1; tick();
        @(negedge clk); da_wmode=0; tick(); check_value(da_rdata==={8{32'h10203040}}, "data_arrays full read");
        da_expected={8{32'h10203040}}; da_expected[79:72]=8'ha5;
        @(negedge clk); da_wmode=1; da_wdata='0; da_wdata[79:72]=8'ha5; da_mask=32'h00000200; tick();
        check_value(da_rdata==={8{32'h10203040}}, "data_arrays write hold");
        @(negedge clk); da_wmode=0; tick(); check_value(da_rdata===da_expected, "data_arrays masked read");
        @(negedge clk); da_en=0; tick(); check_value(da_rdata===da_expected, "data_arrays disabled hold");

        // tag_array_ext: four 22-bit lanes.
        @(negedge clk); t_addr=6'd9; t_en=1; t_wmode=1; t_wdata=88'h123456789abcdef0123456; t_mask='1; tick();
        @(negedge clk); t_wmode=0; tick(); check_value(t_rdata===88'h123456789abcdef0123456, "tag full read");
        t_expected=88'h123456789abcdef0123456; t_expected[65:44]=22'h2a55aa;
        @(negedge clk); t_wmode=1; t_wdata='0; t_wdata[65:44]=22'h2a55aa; t_mask=4'b0100; tick();
        check_value(t_rdata===88'h123456789abcdef0123456, "tag write hold");
        @(negedge clk); t_wmode=0; tick(); check_value(t_rdata===t_expected, "tag masked read");
        @(negedge clk); t_en=0; tick(); check_value(t_rdata===t_expected, "tag disabled hold");

        // tag_array_0_ext: four 21-bit lanes.
        @(negedge clk); t0_addr=6'd11; t0_en=1; t0_wmode=1; t0_wdata=84'h123456789abcdef012345; t0_mask='1; tick();
        @(negedge clk); t0_wmode=0; tick(); check_value(t0_rdata===84'h123456789abcdef012345, "tag0 full read");
        t0_expected=84'h123456789abcdef012345; t0_expected[41:21]=21'h155aaa;
        @(negedge clk); t0_wmode=1; t0_wdata='0; t0_wdata[41:21]=21'h155aaa; t0_mask=4'b0010; tick();
        check_value(t0_rdata===84'h123456789abcdef012345, "tag0 write hold");
        @(negedge clk); t0_wmode=0; tick(); check_value(t0_rdata===t0_expected, "tag0 masked read");
        @(negedge clk); t0_en=0; tick(); check_value(t0_rdata===t0_expected, "tag0 disabled hold");

        // data_arrays_0_0_ext: four 32-bit lanes.
        @(negedge clk); da0_addr=9'd23; da0_en=1; da0_wmode=1; da0_wdata=128'h00112233445566778899aabbccddeeff; da0_mask='1; tick();
        @(negedge clk); da0_wmode=0; tick(); check_value(da0_rdata===128'h00112233445566778899aabbccddeeff, "data0 full read");
        da0_expected=128'h00112233445566778899aabbccddeeff; da0_expected[127:96]=32'hdeadbeef;
        @(negedge clk); da0_wmode=1; da0_wdata='0; da0_wdata[127:96]=32'hdeadbeef; da0_mask=4'b1000; tick();
        check_value(da0_rdata===128'h00112233445566778899aabbccddeeff, "data0 write hold");
        @(negedge clk); da0_wmode=0; tick(); check_value(da0_rdata===da0_expected, "data0 masked read");
        @(negedge clk); da0_en=0; tick(); check_value(da0_rdata===da0_expected, "data0 disabled hold");

        // memory_ext: separate clocks, full and byte-masked writes, read hold.
        @(negedge write_clk); m_waddr=10'd41; m_wen=1; m_wdata=32'h11223344; m_mask=4'b1111;
        @(posedge write_clk); #1; @(negedge write_clk); m_wen=0;
        @(negedge read_clk); m_raddr=10'd41; m_ren=1; @(posedge read_clk); #1;
        check_value(m_rdata===32'h11223344, "memory_ext full read");
        @(negedge read_clk); m_ren=0; m_raddr=10'd42; @(posedge read_clk); #1;
        check_value(m_rdata===32'h11223344, "memory_ext disabled hold");
        @(negedge write_clk); m_waddr=10'd41; m_wen=1; m_wdata=32'haa00cc00; m_mask=4'b1010;
        @(posedge write_clk); #1; check_value(m_rdata===32'h11223344, "memory_ext write hold");
        @(negedge write_clk); m_wen=0;
        @(negedge read_clk); m_raddr=10'd41; m_ren=1; @(posedge read_clk); #1;
        check_value(m_rdata===32'haa22cc44, "memory_ext masked read");
        @(negedge read_clk); m_ren=0;
        @(negedge write_clk); m_wen=1; m_wdata=32'hffffffff; m_mask=4'b0000;
        @(posedge write_clk); #1; @(negedge write_clk); m_wen=0;
        @(negedge read_clk); m_ren=1; @(posedge read_clk); #1;
        check_value(m_rdata===32'haa22cc44, "memory_ext zero mask preserves data");

        if (checks != 28) $fatal(1, "FAILED: check-count drift: %0d", checks);
        $display("EXP0011_COMMON_STDCELL_MEMORY_FUNCTIONAL_OK checks=%0d modules=7", checks);
        $finish;
    end
endmodule

`default_nettype wire
