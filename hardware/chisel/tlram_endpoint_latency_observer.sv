// Functional-only request/response observer for the inherited ScratchpadBank.
//
// This binds to the single-beat TileLink boundary below the bank-local
// fragmenter.  It does not alter traffic and it does not establish a fixed
// latency, matched resources, or performance.  The source-ID table is only a
// diagnostic consistency check for the pinned functional simulation.
module RaveilTlramEndpointLatencyObserver (
  input logic       clock,
  input logic       reset,
  input logic       a_valid,
  input logic       a_ready,
  input logic [2:0] a_opcode,
  input logic [7:0] a_source,
  input logic [27:0] a_address,
  input logic       d_valid,
  input logic       d_ready,
  input logic [7:0] d_source
);
  logic [63:0] cycle_count;
  logic [63:0] accepted_cycle [0:255];
  logic [2:0]  accepted_opcode [0:255];
  logic [27:0] accepted_address [0:255];
  logic        outstanding [0:255];
  logic [63:0] transaction_count;
  logic [63:0] read_count;
  logic [63:0] write_count;
  logic [63:0] other_count;
  logic [63:0] input_region_count;
  logic [63:0] output_region_count;
  logic [63:0] other_region_count;
  logic [63:0] minimum_latency;
  logic [63:0] maximum_latency;
  logic [63:0] unmatched_response_count;
  logic [63:0] source_reuse_count;
  logic [63:0] pending_count;
  logic [63:0] response_latency;
  integer index;

  wire a_fire = a_valid && a_ready;
  wire d_fire = d_valid && d_ready;

  always @(posedge clock) begin
    if (reset) begin
      cycle_count <= 64'd0;
      transaction_count <= 64'd0;
      read_count <= 64'd0;
      write_count <= 64'd0;
      other_count <= 64'd0;
      input_region_count <= 64'd0;
      output_region_count <= 64'd0;
      other_region_count <= 64'd0;
      minimum_latency <= {64{1'b1}};
      maximum_latency <= 64'd0;
      unmatched_response_count <= 64'd0;
      source_reuse_count <= 64'd0;
      pending_count <= 64'd0;
      response_latency <= 64'd0;
      for (index = 0; index < 256; index = index + 1) begin
        accepted_cycle[index] = 64'd0;
        accepted_opcode[index] = 3'd0;
        accepted_address[index] = 28'd0;
        outstanding[index] = 1'b0;
      end
    end else begin
      cycle_count <= cycle_count + 64'd1;

      // Complete the old request before admitting same-cycle source reuse.
      if (d_fire) begin
        if (!outstanding[d_source]) begin
          unmatched_response_count <= unmatched_response_count + 64'd1;
        end else begin
          response_latency <= cycle_count - accepted_cycle[d_source];
          transaction_count <= transaction_count + 64'd1;
          if ((cycle_count - accepted_cycle[d_source]) < minimum_latency)
            minimum_latency <= cycle_count - accepted_cycle[d_source];
          if ((cycle_count - accepted_cycle[d_source]) > maximum_latency)
            maximum_latency <= cycle_count - accepted_cycle[d_source];
          case (accepted_opcode[d_source])
            3'd4: read_count <= read_count + 64'd1;
            3'd0, 3'd1: write_count <= write_count + 64'd1;
            default: other_count <= other_count + 64'd1;
          endcase
          if ((accepted_address[d_source] >= 28'h8000000) &&
              (accepted_address[d_source] < 28'h8000510))
            input_region_count <= input_region_count + 64'd1;
          else if ((accepted_address[d_source] >= 28'h8000510) &&
                   (accepted_address[d_source] < 28'h8000910))
            output_region_count <= output_region_count + 64'd1;
          else
            other_region_count <= other_region_count + 64'd1;
          outstanding[d_source] <= 1'b0;
        end
      end

      if (a_fire) begin
        if (outstanding[a_source] && !(d_fire && (d_source == a_source)))
          source_reuse_count <= source_reuse_count + 64'd1;
        accepted_cycle[a_source] <= cycle_count;
        accepted_opcode[a_source] <= a_opcode;
        accepted_address[a_source] <= a_address;
        outstanding[a_source] <= 1'b1;
      end

      // One accepted request and one matched response may occur together.
      // Apply their net effect once so nonblocking assignment ordering cannot
      // inflate the diagnostic count.
      case ({a_fire, (d_fire && outstanding[d_source])})
        2'b10: pending_count <= pending_count + 64'd1;
        2'b01: pending_count <= pending_count - 64'd1;
        default: pending_count <= pending_count;
      endcase
    end
  end

  final begin
    $display(
      "TLRAM-ENDPOINT-LATENCY-OBSERVER-V1 instance=%m transactions=%0d reads=%0d writes=%0d other=%0d input_region=%0d output_region=%0d other_region=%0d min_cycles=%0d max_cycles=%0d variable=%0d unmatched=%0d source_reuse=%0d pending=%0d evidence=rtl-simulation-functional-diagnostic performance=not-measured fixed_latency_claim=0 resource_match_verified=0",
      transaction_count,
      read_count,
      write_count,
      other_count,
      input_region_count,
      output_region_count,
      other_region_count,
      transaction_count == 0 ? 64'd0 : minimum_latency,
      maximum_latency,
      transaction_count == 0 ? 1'd0 : (minimum_latency != maximum_latency),
      unmatched_response_count,
      source_reuse_count,
      pending_count
    );
  end
endmodule

bind TLRAM RaveilTlramEndpointLatencyObserver
  raveil_tlram_endpoint_latency_observer (
    .clock(clock),
    .reset(reset),
    .a_valid(auto_in_a_valid),
    .a_ready(auto_in_a_ready),
    .a_opcode(auto_in_a_bits_opcode),
    .a_source(auto_in_a_bits_source),
    .a_address(auto_in_a_bits_address),
    .d_valid(auto_in_d_valid),
    .d_ready(auto_in_d_ready),
    .d_source(auto_in_d_bits_source)
  );
