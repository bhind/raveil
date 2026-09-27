// Owned AXI4-Lite boundary. Absolute, aligned 16 KiB window; no authority from PROT.
module GraphDeviceBoardBridge #(
  parameter logic [31:0] BASE_ADDR = 32'h00000000
) (
  input wire aclk, input wire aresetn,
  input wire [31:0] s_axi_awaddr, input wire [2:0] s_axi_awprot,
  input wire s_axi_awvalid, output wire s_axi_awready,
  input wire [31:0] s_axi_wdata, input wire [3:0] s_axi_wstrb,
  input wire s_axi_wvalid, output wire s_axi_wready,
  output wire [1:0] s_axi_bresp, output wire s_axi_bvalid, input wire s_axi_bready,
  input wire [31:0] s_axi_araddr, input wire [2:0] s_axi_arprot,
  input wire s_axi_arvalid, output wire s_axi_arready,
  output wire [31:0] s_axi_rdata, output wire [1:0] s_axi_rresp,
  output wire s_axi_rvalid, input wire s_axi_rready
);
  // Invalid parameters leave an unresolved module. The synthesis recipe also
  // rejects any black boxes; simulation elaboration must reject this branch.
  generate if (BASE_ADDR[13:0] != 0) begin : invalid_base
    RAVEIL_BASE_ADDR_MUST_BE_16K_ALIGNED invalid_parameter();
  end endgenerate

  (* ASYNC_REG = "TRUE" *) reg [1:0] reset_pipe;
  always @(posedge aclk or negedge aresetn) begin
    if (!aresetn) reset_pipe <= 2'b00;
    else reset_pipe <= {reset_pipe[0], 1'b1};
  end
  wire ready_for_bus = aresetn && reset_pipe[1];
  wire [31:0] aw_relative = s_axi_awaddr[31:14] == BASE_ADDR[31:14]
      ? {18'b0, s_axi_awaddr[13:0]} : 32'hfffffffc;
  wire [31:0] ar_relative = s_axi_araddr[31:14] == BASE_ADDR[31:14]
      ? {18'b0, s_axi_araddr[13:0]} : 32'hfffffffc;
  wire awready, wready, arready, bvalid, rvalid;
  // PROT is deliberately unused. Access control belongs outside this module.
  assign s_axi_awready = ready_for_bus && awready;
  assign s_axi_wready = ready_for_bus && wready;
  assign s_axi_arready = ready_for_bus && arready;
  assign s_axi_bvalid = ready_for_bus && bvalid;
  assign s_axi_rvalid = ready_for_bus && rvalid;
  GraphDeviceAxi4LiteTop core (
    .aclk(aclk), .aresetn(ready_for_bus),
    .awaddr(aw_relative), .awvalid(ready_for_bus && s_axi_awvalid), .awready(awready),
    .wdata(s_axi_wdata), .wstrb(s_axi_wstrb),
    .wvalid(ready_for_bus && s_axi_wvalid), .wready(wready),
    .bresp(s_axi_bresp), .bvalid(bvalid), .bready(ready_for_bus && s_axi_bready),
    .araddr(ar_relative), .arvalid(ready_for_bus && s_axi_arvalid), .arready(arready),
    .rdata(s_axi_rdata), .rresp(s_axi_rresp), .rvalid(rvalid),
    .rready(ready_for_bus && s_axi_rready)
  );
endmodule
