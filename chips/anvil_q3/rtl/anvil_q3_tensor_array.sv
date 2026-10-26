module anvil_q3_tensor_array #(
  parameter BANKS=8, TILE_K=128, TILE_ROWS=8,
  parameter NUM_LAYERS=36, HIDDEN_SIZE=2048, INTERMEDIATE_SIZE=11008,
  parameter NUM_KV_HEADS=2, HEAD_DIM=128, GROUP_SIZE=128,
  localparam SB=(BANKS==1 || BANKS==2 || BANKS==4 || BANKS==8) ? BANKS : 1,
  localparam TR=TILE_ROWS>=1 && TILE_ROWS<=8 ? TILE_ROWS : 1,
  localparam MAX_INPUTS=(HIDDEN_SIZE>0 && INTERMEDIATE_SIZE>0) ?
    (HIDDEN_SIZE>INTERMEDIATE_SIZE ? HIDDEN_SIZE : INTERMEDIATE_SIZE) : 1
) (
  input wire clk, rst_n, flush, cmd_valid,
  output wire cmd_ready,
  input wire [31:0] cmd_epoch, cmd_layer,
  input wire [2:0] cmd_proj,
  input wire load_valid, load_last,
  output wire load_ready,
  input wire signed [31:0] load_data,
  output wire done, error,
  output wire [SB-1:0] result_valid,
  input wire [SB-1:0] result_ready,
  output wire [SB*32-1:0] result_row,
  output wire [SB*128-1:0] result_sum,
  output wire [SB-1:0] c_req_valid,
  input wire [SB-1:0] c_req_ready,
  output wire [SB-1:0] c_req_write,
  output wire [SB*4-1:0] c_req_kind,
  output wire [SB*32-1:0] c_req_layer,
  output wire [SB*3-1:0] c_req_proj,
  output wire [SB*32-1:0] c_req_row, c_req_col, c_req_wdata,
  input wire [SB-1:0] c_rsp_valid, c_rsp_error,
  output wire [SB-1:0] c_rsp_ready,
  input wire [SB*32-1:0] c_rsp_rdata
);
  localparam IDLE=0, LOAD=1, RUN=2, COMPLETE=3, FAULT_WAIT=4;
  localparam [63:0] KV_DIM=64'(NUM_KV_HEADS)*64'(HEAD_DIM);
  localparam LEGAL=(BANKS==1 || BANKS==2 || BANKS==4 || BANKS==8) &&
    SB==BANKS && TILE_ROWS>=1 && TILE_ROWS<=8 && TR==TILE_ROWS &&
    TILE_K>0 && TILE_K<=128 && TILE_K%8==0 &&
    HIDDEN_SIZE>0 && INTERMEDIATE_SIZE>0 && HIDDEN_SIZE%8==0 &&
    INTERMEDIATE_SIZE%8==0 && GROUP_SIZE>0 && NUM_LAYERS>0 &&
    NUM_KV_HEADS>0 && HEAD_DIM>0 && KV_DIM<=64'hffffffff &&
    MAX_INPUTS==(HIDDEN_SIZE>INTERMEDIATE_SIZE ? HIDDEN_SIZE : INTERMEDIATE_SIZE);
  generate if (!LEGAL) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q3 PARAMETER ERROR: tensor geometry");
  end endgenerate
  reg [2:0] state;
  reg failed;
  reg [31:0] epoch, layer, inputs, outputs, load_index;
  reg [2:0] projection;
  wire internal_flush=flush || failed;
  wire load_transfer=load_valid && load_ready;
  wire bad_load=load_transfer && (load_last!=(load_index+1==inputs));
  wire compute_start=load_transfer && !bad_load && load_index+1==inputs;
  wire [SB-1:0] bank_done, bank_fault, prefetch_fault;
  wire [SB-1:0] desc_valid, desc_ready, beat_valid, beat_ready;
  wire [SB*32-1:0] desc_epoch, desc_layer, desc_output_base, desc_input_base;
  wire [SB*32-1:0] desc_valid_rows, desc_valid_inputs;
  wire [SB*3-1:0] desc_proj;
  wire [SB*32-1:0] beat_q, beat_z, beat_epoch, beat_row, beat_input;
  wire [SB*128-1:0] beat_scale;
  wire [SB*8-1:0] beat_mask;
  wire [SB-1:0] beat_row_first, beat_row_last, beat_tile_last;
  assign cmd_ready=rst_n && !flush && state==IDLE;
  assign load_ready=rst_n && !flush && state==LOAD;
  assign done=rst_n && !flush && state==COMPLETE;
  assign error=done && failed;

  anvil_q3_weight_prefetcher #(
    .BANKS(BANKS),.TILE_K(TILE_K),.TILE_ROWS(TILE_ROWS),
    .NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),
    .INTERMEDIATE_SIZE(INTERMEDIATE_SIZE),.NUM_KV_HEADS(NUM_KV_HEADS),
    .HEAD_DIM(HEAD_DIM),.GROUP_SIZE(GROUP_SIZE)
  ) weight_prefetcher (
    .clk(clk),.rst_n(rst_n),.flush(internal_flush),
    .desc_valid(desc_valid),.desc_ready(desc_ready),.fault(prefetch_fault),
    .desc_epoch(desc_epoch),.desc_layer(desc_layer),.desc_proj(desc_proj),
    .desc_output_base(desc_output_base),.desc_input_base(desc_input_base),
    .desc_valid_rows(desc_valid_rows),.desc_valid_inputs(desc_valid_inputs),
    .beat_valid(beat_valid),.beat_ready(beat_ready),.beat_q(beat_q),.beat_z(beat_z),
    .beat_epoch(beat_epoch),.beat_row(beat_row),.beat_input(beat_input),
    .beat_scale(beat_scale),.beat_mask(beat_mask),
    .beat_row_first(beat_row_first),.beat_row_last(beat_row_last),
    .beat_tile_last(beat_tile_last),
    .c_req_valid(c_req_valid),.c_req_ready(c_req_ready),.c_req_write(c_req_write),
    .c_req_kind(c_req_kind),.c_req_layer(c_req_layer),.c_req_proj(c_req_proj),
    .c_req_row(c_req_row),.c_req_col(c_req_col),.c_req_wdata(c_req_wdata),
    .c_rsp_valid(c_rsp_valid),.c_rsp_error(c_rsp_error),
    .c_rsp_ready(c_rsp_ready),.c_rsp_rdata(c_rsp_rdata)
  );

  genvar g, a;
  generate for (g=0;g<SB;g=g+1) begin: engines
    reg active, completed, local_failed, local_fault, descriptors_finished;
    reg [31:0] output_base, next_input, rows_completed;
    wire [31:0] rows_left=outputs-output_base;
    wire [31:0] row_count=rows_left<TR ? rows_left : TR;
    wire [31:0] inputs_left=inputs-next_input;
    localparam ACTIVATION_WORDS=(MAX_INPUTS>>3)+((MAX_INPUTS&7)!=0);
    localparam ACTIVATION_AW=ACTIVATION_WORDS>1 ? $clog2(ACTIVATION_WORDS) : 1;
    wire [ACTIVATION_AW-1:0] activation_write_address=load_index>>3;
    wire [ACTIVATION_AW-1:0] activation_read_address=beat_input[g*32+:32]>>3;
    reg signed [127:0] sums [0:TR-1];
    reg operand_valid;
    reg [31:0] operand_q, operand_z, operand_row, operand_input;
    reg [127:0] operand_scale;
    wire [255:0] operand_activations;
    reg [7:0] operand_mask;
    reg [31:0] row_pipe [0:7];
    reg [7:0] first_pipe, last_pipe;
    wire dot_input_ready, dot_valid, dot_ready, dot_error;
    wire signed [71:0] dot_sum;
    wire add_input_ready, add_valid, add_ready, add_error;
    wire signed [127:0] added;
    wire [31:0] sum_index=row_pipe[7]-output_base;
    wire signed [127:0] base_sum=first_pipe[7] ? 128'sd0 :
      (add_valid && add_ready && addition_row==row_pipe[7]) ? added : sums[sum_index];
    wire add_launch=dot_valid && dot_ready && !dot_error;
    reg [31:0] addition_row;
    reg addition_last;
    reg result_pending;
    reg [31:0] result_index;
    reg signed [127:0] result_data;
    wire local_flush=internal_flush || local_failed;
    wire operand_ready=!operand_valid || dot_input_ready;
    wire bad_beat=beat_valid[g] &&
      (beat_epoch[g*32+:32]!=epoch ||
       beat_row[g*32+:32]<output_base ||
       {1'b0,beat_row[g*32+:32]}>={1'b0,output_base}+row_count ||
       beat_input[g*32+:32]>=inputs);
    wire activation_read=rst_n && !local_flush && !bad_beat &&
      !(dot_valid && dot_error) && !(add_valid && add_error) &&
      operand_ready && beat_valid[g] && active;
    integer i;

    for (a=0;a<8;a=a+1) begin: activation_lanes
      reg [31:0] activation_storage [0:ACTIVATION_WORDS-1];
      reg [31:0] read_data;
      assign operand_activations[a*32+:32]=operand_mask[a] ? read_data : 32'd0;

      always @(posedge clk) begin
        if (rst_n && !internal_flush && load_transfer && !bad_load &&
            load_index[2:0]==a)
          activation_storage[activation_write_address]<=load_data;
        if (activation_read && beat_mask[g*8+a])
          read_data<=activation_storage[activation_read_address];
      end
    end

    assign bank_done[g]=completed;
    assign bank_fault[g]=local_fault;
    assign desc_valid[g]=rst_n && !local_flush && active && !descriptors_finished;
    assign desc_epoch[g*32+:32]=desc_valid[g] ? epoch : 32'd0;
    assign desc_layer[g*32+:32]=desc_valid[g] ? layer : 32'd0;
    assign desc_proj[g*3+:3]=desc_valid[g] ? projection : 3'd0;
    assign desc_output_base[g*32+:32]=desc_valid[g] ? output_base : 32'd0;
    assign desc_input_base[g*32+:32]=desc_valid[g] ? next_input : 32'd0;
    assign desc_valid_rows[g*32+:32]=desc_valid[g] ? row_count : 32'd0;
    assign desc_valid_inputs[g*32+:32]=!desc_valid[g] ? 32'd0 :
      inputs_left<TILE_K ? inputs_left : TILE_K;
    assign beat_ready[g]=rst_n && !local_flush && active && operand_ready;
    assign dot_ready=add_input_ready && !local_flush;
    assign add_ready=!addition_last || !result_pending || result_ready[g];
    assign result_valid[g]=rst_n && !local_flush && result_pending;
    assign result_row[g*32+:32]=result_valid[g] ? result_index : 32'd0;
    assign result_sum[g*128+:128]=result_valid[g] ? result_data : 128'd0;

    anvil_q3_awq_dot8 dot8 (
      .clk(clk),.rst_n(rst_n),.flush(local_flush),
      .in_valid(operand_valid),.in_ready(dot_input_ready),
      .q_nibbles(operand_q),.z_nibbles(operand_z),.scale_f16(operand_scale),
      .activation_q16(operand_activations),.lane_mask(operand_mask),
      .out_valid(dot_valid),.out_ready(dot_ready),.out_error(dot_error),.out_dot(dot_sum)
    );
    anvil_q3_add128 accumulator (
      .clk(clk),.rst_n(rst_n),.flush(local_flush),
      .in_valid(dot_valid && !dot_error),.in_ready(add_input_ready),
      .in_a(base_sum),.in_b({{56{dot_sum[71]}},dot_sum}),
      .out_valid(add_valid),.out_ready(add_ready),.out_error(add_error),.out_sum(added)
    );

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        active<=0; completed<=0; local_failed<=0; local_fault<=0;
        descriptors_finished<=0; output_base<=0; next_input<=0; rows_completed<=0;
        operand_valid<=0; operand_q<=0; operand_z<=0; operand_scale<=0;
        operand_mask<=0; operand_row<=0; operand_input<=0;
        first_pipe<=0; last_pipe<=0; addition_row<=0; addition_last<=0;
        result_pending<=0; result_index<=0; result_data<=0;
        for (i=0;i<8;i=i+1) row_pipe[i]<=0;
      end else if (internal_flush) begin
        active<=0; completed<=0; local_failed<=0; local_fault<=0;
        operand_valid<=0; result_pending<=0;
        first_pipe<=0; last_pipe<=0;
      end else begin
        local_fault<=0;
        if (compute_start) begin
          active<=g*TR<outputs; completed<=g*TR>=outputs;
          output_base<=g*TR; next_input<=0; rows_completed<=0;
          descriptors_finished<=0; operand_valid<=0; result_pending<=0;
          local_failed<=0;
        end
        if (!local_failed) begin
          if (bad_beat || (dot_valid && dot_error) || (add_valid && add_error)) begin
            local_failed<=1; local_fault<=1; active<=0;
          end else begin
            if (desc_valid[g] && desc_ready[g]) begin
              if (next_input+TILE_K>=inputs) descriptors_finished<=1;
              else next_input<=next_input+TILE_K;
            end
            if (operand_ready) begin
              operand_valid<=beat_valid[g] && active;
              if (beat_valid[g] && active) begin
                operand_q<=beat_q[g*32+:32]; operand_z<=beat_z[g*32+:32];
                operand_scale<=beat_scale[g*128+:128];
                operand_mask<=beat_mask[g*8+:8]; operand_row<=beat_row[g*32+:32];
                operand_input<=beat_input[g*32+:32];
              end
            end
            if (dot_input_ready) begin
              row_pipe[0]<=operand_row;
              first_pipe<={first_pipe[6:0],operand_input==0};
              last_pipe<={last_pipe[6:0],operand_input+8>=inputs};
              for (i=1;i<8;i=i+1) row_pipe[i]<=row_pipe[i-1];
            end
            if (add_launch) begin
              addition_row<=row_pipe[7];
              addition_last<=last_pipe[7];
            end
            if (result_pending && result_ready[g]) begin
              result_pending<=0;
              if (rows_completed+1==row_count) begin
                rows_completed<=0;
                if ({1'b0,output_base}+SB*TR<outputs) begin
                  output_base<=output_base+SB*TR;
                  next_input<=0; descriptors_finished<=0;
                end else begin active<=0; completed<=1; end
              end else rows_completed<=rows_completed+1'b1;
            end
            if (add_valid && add_ready) begin
              sums[addition_row-output_base]<=added;
              if (addition_last) begin
                result_pending<=1;
                result_index<=addition_row;
                result_data<=added;
              end
            end
          end
        end
      end
    end
  end endgenerate

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; failed<=0; epoch<=0; layer<=0; projection<=0;
      inputs<=0; outputs<=0; load_index<=0;
    end else if (flush) begin
      state<=IDLE; failed<=0;
    end else if ((|prefetch_fault) || (|bank_fault) || bad_load) begin
      state<=COMPLETE;
      failed<=1;
    end else case (state)
      IDLE: if (cmd_valid) begin
        failed<=0; epoch<=cmd_epoch; layer<=cmd_layer; projection<=cmd_proj;
        inputs<=cmd_proj==6 ? INTERMEDIATE_SIZE : HIDDEN_SIZE;
        outputs<=(cmd_proj==1 || cmd_proj==2) ? KV_DIM[31:0] :
          (cmd_proj==4 || cmd_proj==5) ? INTERMEDIATE_SIZE : HIDDEN_SIZE;
        load_index<=0;
        if (cmd_layer>=NUM_LAYERS || cmd_proj>6) begin failed<=1; state<=COMPLETE; end
        else state<=LOAD;
      end
      LOAD: if (load_transfer) begin
        if (compute_start) state<=RUN;
        else load_index<=load_index+1'b1;
      end
      RUN: if (&bank_done) state<=COMPLETE;
      COMPLETE: if (failed) state<=FAULT_WAIT; else state<=IDLE;
      FAULT_WAIT: state<=FAULT_WAIT;
      default: begin failed<=1; state<=COMPLETE; end
    endcase
  end
endmodule
