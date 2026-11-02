module anvil_qn1_csr_perf #(
  parameter PROFILE=3
) (
  input wire clk, rst_n,
  input wire csr_valid,
  output wire csr_ready,
  input wire csr_write,
  input wire [11:0] csr_addr,
  input wire [31:0] csr_wdata,
  input wire [3:0] csr_wstrb,
  output wire csr_rsp_valid,
  input wire csr_rsp_ready,
  output wire [31:0] csr_rdata,
  output wire csr_error,
  input wire busy, think_active, qk_busy, qk_blocked,
  input wire arith_error, mem_error, sequence_done,
  input wire [2:0] direct_tokens, think_tokens, draft_nodes,
  input wire [2:0] verified_nodes, accepted_nodes, rejected_nodes,
  input wire score_valid,
  input wire [31:0] score_fp32,
  output wire mode_valid, mode_value
);
  import anvil_qn1_pkg::*;
  localparam COUNTERS=13;
  reg [63:0] live [0:COUNTERS-1], snapshot [0:COUNTERS-1];
  wire [63:0] incremented [0:COUNTERS-1];
  wire [2:0] increment [0:COUNTERS-1];
  reg [31:0] max_score, snapshot_max_score, arithmetic_errors, snapshot_arithmetic_errors;
  reg [31:0] snapshot_sequence;
  reg sticky_error, desired_mode;
  reg reference_valid;
  reg [63:0] reference_cycles, reference_tokens;
  reg [31:0] reference_profile;
  reg pending, response_valid, response_error, mode_pulse, mode_bit;
  reg request_write, request_busy, request_mode;
  reg [11:0] request_addr;
  reg [31:0] request_data, response_data;
  reg [3:0] request_strobes;
  reg access_error, take_snapshot, clear_counters, write_mode;
  reg write_reference_valid, write_reference_cycles_low, write_reference_cycles_high;
  reg write_reference_tokens_low, write_reference_tokens_high, write_reference_profile;
  reg [31:0] read_value;
  wire [63:0] incremented_errors=event_add64({32'd0,arithmetic_errors},
    {2'd0,arith_error});
  wire accepted=csr_valid && csr_ready;
  assign csr_ready=rst_n && !pending && !response_valid;
  assign csr_rsp_valid=rst_n && response_valid;
  assign csr_rdata=csr_rsp_valid ? response_data : 32'd0;
  assign csr_error=csr_rsp_valid && response_error;
  assign mode_valid=rst_n && mode_pulse;
  assign mode_value=mode_valid && mode_bit;
  assign increment[0]={2'd0,busy};
  assign increment[1]={2'd0,busy && think_active};
  assign increment[2]={2'd0,busy && !think_active};
  assign increment[3]=think_tokens;
  assign increment[4]=direct_tokens;
  assign increment[5]={2'd0,qk_busy};
  assign increment[6]={2'd0,qk_blocked};
  assign increment[7]=draft_nodes;
  assign increment[8]=verified_nodes;
  assign increment[9]=accepted_nodes;
  assign increment[10]=rejected_nodes;
  assign increment[11]={2'd0,mem_error};
  assign increment[12]={2'd0,sequence_done};
  genvar index;
  generate
    if (PROFILE<1 || PROFILE>3) begin: invalid_parameters
      initial $fatal(1,"ANVIL_QN1 PARAMETER ERROR: CSR profile");
    end
    for (index=0;index<COUNTERS;index=index+1) begin: counters
      assign incremented[index]=event_add64(live[index],increment[index]);
      always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin live[index]<=0; snapshot[index]<=0; end
        else begin
          if (take_snapshot) snapshot[index]<=live[index];
          if (clear_counters) live[index]<=0;
          else live[index]<=incremented[index];
        end
      end
    end
  endgenerate

  always @* begin
    access_error=0; take_snapshot=0; clear_counters=0; write_mode=0;
    write_reference_valid=0; write_reference_cycles_low=0; write_reference_cycles_high=0;
    write_reference_tokens_low=0; write_reference_tokens_high=0; write_reference_profile=0;
    read_value=0;
    if (rst_n && pending) begin
      if (request_addr[1:0]!=0 || (request_write && request_strobes!=4'hf))
        access_error=1;
      else if (request_write) begin
        case (request_addr)
          12'h008: begin
            if ((|request_data[31:3]) ||
                (request_busy && (request_data[0]!=request_mode || request_data[2:1]==0)))
              access_error=1;
            else begin
              take_snapshot=request_data[1];
              clear_counters=request_data[2];
              write_mode=!request_busy;
            end
          end
          12'h084: begin
            if (request_busy || (|request_data[31:1])) access_error=1;
            else write_reference_valid=1;
          end
          12'h088: begin
            if (request_busy) access_error=1; else write_reference_cycles_low=1;
          end
          12'h08c: begin
            if (request_busy) access_error=1; else write_reference_cycles_high=1;
          end
          12'h090: begin
            if (request_busy) access_error=1; else write_reference_tokens_low=1;
          end
          12'h094: begin
            if (request_busy) access_error=1; else write_reference_tokens_high=1;
          end
          12'h098: begin
            if (request_busy || request_data<1 || request_data>3) access_error=1;
            else write_reference_profile=1;
          end
          default: access_error=1;
        endcase
      end else begin
        case (request_addr)
          12'h000: read_value=32'h01000001;
          12'h004: read_value=32'(PROFILE);
          12'h008: read_value={31'd0,desired_mode};
          12'h00c: read_value={29'd0,sticky_error,think_active,busy};
          12'h010: read_value=snapshot[0][31:0];
          12'h014: read_value=snapshot[0][63:32];
          12'h018: read_value=snapshot[1][31:0];
          12'h01c: read_value=snapshot[1][63:32];
          12'h020: read_value=snapshot[2][31:0];
          12'h024: read_value=snapshot[2][63:32];
          12'h028: read_value=snapshot[3][31:0];
          12'h02c: read_value=snapshot[3][63:32];
          12'h030: read_value=snapshot[4][31:0];
          12'h034: read_value=snapshot[4][63:32];
          12'h038: read_value=snapshot[5][31:0];
          12'h03c: read_value=snapshot[5][63:32];
          12'h040: read_value=snapshot[6][31:0];
          12'h044: read_value=snapshot[6][63:32];
          12'h048: read_value=snapshot_max_score;
          12'h04c: read_value=snapshot_arithmetic_errors;
          12'h050: read_value=snapshot[7][31:0];
          12'h054: read_value=snapshot[7][63:32];
          12'h058: read_value=snapshot[8][31:0];
          12'h05c: read_value=snapshot[8][63:32];
          12'h060: read_value=snapshot[9][31:0];
          12'h064: read_value=snapshot[9][63:32];
          12'h068: read_value=snapshot[10][31:0];
          12'h06c: read_value=snapshot[10][63:32];
          12'h070: read_value=snapshot[11][31:0];
          12'h074: read_value=snapshot[11][63:32];
          12'h078: read_value=snapshot[12][31:0];
          12'h07c: read_value=snapshot[12][63:32];
          12'h080: read_value=snapshot_sequence;
          12'h084: read_value={31'd0,reference_valid};
          12'h088: read_value=reference_cycles[31:0];
          12'h08c: read_value=reference_cycles[63:32];
          12'h090: read_value=reference_tokens[31:0];
          12'h094: read_value=reference_tokens[63:32];
          12'h098: read_value=reference_profile;
          default: access_error=1;
        endcase
      end
    end
  end
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      pending<=0; response_valid<=0; response_error<=0; response_data<=0;
      request_write<=0; request_busy<=0; request_mode<=0; request_addr<=0;
      request_data<=0; request_strobes<=0; mode_pulse<=0; mode_bit<=0;
      desired_mode<=0; sticky_error<=0;
      max_score<=0; snapshot_max_score<=0; arithmetic_errors<=0;
      snapshot_arithmetic_errors<=0; snapshot_sequence<=0;
      reference_valid<=0; reference_cycles<=0; reference_tokens<=0; reference_profile<=0;
    end else begin
      mode_pulse<=0;
      if (response_valid && csr_rsp_ready) response_valid<=0;
      if (accepted) begin
        pending<=1;
        request_write<=csr_write; request_addr<=csr_addr;
        request_data<=csr_wdata; request_strobes<=csr_wstrb;
        request_busy<=busy; request_mode<=think_active;
      end
      if (pending) begin
        pending<=0; response_valid<=1;
        response_error<=access_error;
        response_data<=request_write || access_error ? 32'd0 : read_value;
      end
      if (take_snapshot) begin
        snapshot_max_score<=max_score;
        snapshot_arithmetic_errors<=arithmetic_errors;
        snapshot_sequence<=snapshot_sequence+1'b1;
      end
      if (clear_counters) begin
        max_score<=0; arithmetic_errors<=0; sticky_error<=0;
      end else begin
        arithmetic_errors<=incremented_errors[31:0];
        if (arith_error || mem_error) sticky_error<=1;
        if (score_valid && !fp32_invalid(score_fp32) && score_fp32[30:0]>max_score[30:0])
          max_score<={1'b0,score_fp32[30:0]};
      end
      if (write_mode) begin
        desired_mode<=request_data[0]; mode_pulse<=1; mode_bit<=request_data[0];
      end
      if (write_reference_valid) reference_valid<=request_data[0];
      if (write_reference_cycles_low) reference_cycles[31:0]<=request_data;
      if (write_reference_cycles_high) reference_cycles[63:32]<=request_data;
      if (write_reference_tokens_low) reference_tokens[31:0]<=request_data;
      if (write_reference_tokens_high) reference_tokens[63:32]<=request_data;
      if (write_reference_profile) reference_profile<=request_data;
    end
  end
endmodule
