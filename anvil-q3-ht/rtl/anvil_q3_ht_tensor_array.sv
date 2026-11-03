module anvil_q3_ht_tensor_array #(
  parameter BANKS=16, LANES_PER_BANK=16, TILE_ROWS=8,
  localparam SB=(BANKS==1 || BANKS==2 || BANKS==4 ||
    BANKS==8 || BANKS==16) ? BANKS : 1,
  localparam ROWS=(TILE_ROWS>=1 && TILE_ROWS<=8) ? TILE_ROWS : 1
) (
  input wire clk, rst_n, flush,
  input wire [SB-1:0] operand_valid,
  output wire [SB-1:0] operand_ready,
  input wire [SB*64-1:0] operand_q, operand_z,
  input wire [SB*256-1:0] operand_scale,
  input wire [SB*512-1:0] operand_activation,
  input wire [SB*16-1:0] operand_mask,
  input wire [SB*160-1:0] operand_meta,
  output wire [SB-1:0] result_valid,
  input wire [SB-1:0] result_ready,
  output wire [SB*128-1:0] result_sum,
  output wire [SB*160-1:0] result_meta,
  output wire idle, fault
);
  localparam LEGAL=SB==BANKS && LANES_PER_BANK==16 && ROWS==TILE_ROWS;
  wire [SB-1:0] bank_idle, bank_fault;
  assign idle=rst_n && !flush && (&bank_idle);
  assign fault=rst_n && !flush && (|bank_fault);

  generate if (!LEGAL) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q3_HT PARAMETER ERROR: tensor banks, lanes or rows");
  end
    genvar g;
    for (g=0;g<SB;g=g+1) begin: banks
      reg failed;
      reg [ROWS-1:0] context_valid, context_busy;
      (* nomem2reg *) reg signed [127:0] sums [0:ROWS-1];
      (* nomem2reg *) reg [98:0] identity [0:ROWS-1];
      (* nomem2reg *) reg [31:0] next_input [0:ROWS-1];
      wire [159:0] incoming=operand_meta[g*160+:160];
      wire [2:0] context_index=incoming[133:131];
      wire [2:0] safe_context=context_index<ROWS ? context_index : 3'd0;
      wire [31:0] input_base=incoming[130:99];
      wire first_input=incoming[134];
      wire bad_operand=context_index>=ROWS || incoming[159:136]!=0 ||
        incoming[66:64]>6 || input_base[3:0]!=0 ||
        input_base>32'hfffffff0 ||
        (first_input ? (input_base!=0 || context_valid[safe_context]) :
          (!context_valid[safe_context] ||
           identity[safe_context]!=incoming[98:0] ||
           next_input[safe_context]!=input_base));
      wire local_flush=flush || failed;
      wire mac_ready, mac_valid, mac_error, mac_out_ready;
      wire signed [72:0] mac_sum;
      wire [159:0] mac_meta;
      wire [2:0] mac_context=mac_meta[133:131];
      wire add_ready, add_valid, add_error, add_out_ready;
      wire signed [127:0] added;
      reg [159:0] addition_meta;
      wire [2:0] addition_context=addition_meta[133:131];
      wire accept=operand_valid[g] && operand_ready[g];
      wire add_accept=mac_valid && mac_out_ready && !mac_error;
      wire commit=add_valid && add_out_ready && !add_error;
      wire signed [127:0] base_sum=mac_meta[134] ? 128'sd0 : sums[mac_context];
      wire signed [127:0] extended_dot={{55{mac_sum[72]}},mac_sum};

      assign bank_fault[g]=failed;
      assign bank_idle[g]=!failed && context_busy==0 && context_valid==0;
      assign operand_ready[g]=rst_n && !local_flush &&
        !context_busy[safe_context] && mac_ready;
      assign mac_out_ready=add_ready && !local_flush;
      assign add_out_ready=!addition_meta[135] || result_ready[g];
      assign result_valid[g]=rst_n && !local_flush && add_valid &&
        !add_error && addition_meta[135];
      assign result_sum[g*128+:128]=result_valid[g] ? added : 128'd0;
      assign result_meta[g*160+:160]=result_valid[g] ? addition_meta : 160'd0;

      anvil_q3_ht_mac16 mac16 (
        .clk(clk),.rst_n(rst_n),.flush(local_flush),
        .in_valid(operand_valid[g] && !context_busy[safe_context] && !bad_operand),
        .in_ready(mac_ready),.q_nibbles(operand_q[g*64+:64]),
        .z_nibbles(operand_z[g*64+:64]),.scale_f16(operand_scale[g*256+:256]),
        .activation_q16(operand_activation[g*512+:512]),
        .lane_mask(operand_mask[g*16+:16]),.in_meta(incoming),
        .out_valid(mac_valid),.out_ready(mac_out_ready),
        .out_error(mac_error),.out_sum(mac_sum),.out_meta(mac_meta)
      );
      anvil_q3_add128 accumulator (
        .clk(clk),.rst_n(rst_n),.flush(local_flush),
        .in_valid(mac_valid && !mac_error),.in_ready(add_ready),
        .in_a(base_sum),.in_b(extended_dot),
        .out_valid(add_valid),.out_ready(add_out_ready),
        .out_error(add_error),.out_sum(added)
      );

      always @(posedge clk) begin
        if (rst_n && !local_flush) begin
          if (accept && !bad_operand) begin
            identity[safe_context]<=incoming[98:0];
          end
          if (add_accept) addition_meta<=mac_meta;
          if (commit) begin
            sums[addition_context]<=added;
            next_input[addition_context]<=addition_meta[130:99]+32'd16;
          end
        end
      end

      always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
          failed<=0;
          context_valid<=0;
          context_busy<=0;
        end else if (flush) begin
          failed<=0;
          context_valid<=0;
          context_busy<=0;
        end else if (!failed) begin
          if ((accept && bad_operand) || (mac_valid && mac_error) ||
              (add_valid && add_error)) begin
            failed<=1;
          end else begin
            if (accept) begin
              context_valid[safe_context]<=1;
              context_busy[safe_context]<=1;
            end
            if (commit) begin
              context_busy[addition_context]<=0;
              if (addition_meta[135]) context_valid[addition_context]<=0;
            end
          end
        end
      end
    end
  endgenerate
endmodule
