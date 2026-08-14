module PhysicalProxySmoke (
    input  logic        clock,
    input  logic        reset,
    input  logic        enable,
    input  logic [31:0] input_word,
    output logic [31:0] output_word
);
  logic [31:0] state;

  always_ff @(posedge clock) begin
    if (reset) begin
      state <= 32'h0000_0000;
    end else if (enable) begin
      state <= state + input_word;
    end
  end

  assign output_word = state ^ 32'h5a5a_a5a5;
endmodule
