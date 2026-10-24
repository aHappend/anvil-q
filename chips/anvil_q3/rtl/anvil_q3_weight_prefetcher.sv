module anvil_q3_weight_prefetcher #(
  parameter BANKS=8, TILE_K=128, TILE_ROWS=8,
  parameter NUM_LAYERS=36, HIDDEN_SIZE=2048, INTERMEDIATE_SIZE=11008,
  parameter NUM_KV_HEADS=2, HEAD_DIM=128, GROUP_SIZE=128,
  localparam SB=(BANKS==1 || BANKS==2 || BANKS==4 || BANKS==8) ? BANKS : 1
) (
  input wire clk, rst_n, flush,
  input wire [SB-1:0] desc_valid,
  output wire [SB-1:0] desc_ready, fault,
  input wire [SB*32-1:0] desc_epoch, desc_layer, desc_output_base, desc_input_base,
  input wire [SB*32-1:0] desc_valid_rows, desc_valid_inputs,
  input wire [SB*3-1:0] desc_proj,
  output wire [SB-1:0] beat_valid,
  input wire [SB-1:0] beat_ready,
  output wire [SB*32-1:0] beat_q, beat_z, beat_epoch, beat_row, beat_input,
  output wire [SB*128-1:0] beat_scale,
  output wire [SB*8-1:0] beat_mask,
  output wire [SB-1:0] beat_row_first, beat_row_last, beat_tile_last,
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
  generate if (!((BANKS==1 || BANKS==2 || BANKS==4 || BANKS==8) && SB==BANKS))
    begin: invalid_parameters
      initial $fatal(1,"ANVIL_Q3 PARAMETER ERROR: prefetch bank count");
    end
  endgenerate
  genvar g;
  generate for (g=0;g<SB;g=g+1) begin: banks
    anvil_q3_weight_prefetch_bank #(
      .TILE_K(TILE_K),.TILE_ROWS(TILE_ROWS),.NUM_LAYERS(NUM_LAYERS),
      .HIDDEN_SIZE(HIDDEN_SIZE),.INTERMEDIATE_SIZE(INTERMEDIATE_SIZE),
      .NUM_KV_HEADS(NUM_KV_HEADS),.HEAD_DIM(HEAD_DIM),.GROUP_SIZE(GROUP_SIZE)
    ) storage (
      .clk(clk),.rst_n(rst_n),.flush(flush),
      .desc_valid(desc_valid[g]),.desc_ready(desc_ready[g]),.fault(fault[g]),
      .desc_epoch(desc_epoch[g*32+:32]),.desc_layer(desc_layer[g*32+:32]),
      .desc_output_base(desc_output_base[g*32+:32]),
      .desc_input_base(desc_input_base[g*32+:32]),
      .desc_valid_rows(desc_valid_rows[g*32+:32]),
      .desc_valid_inputs(desc_valid_inputs[g*32+:32]),.desc_proj(desc_proj[g*3+:3]),
      .beat_valid(beat_valid[g]),.beat_ready(beat_ready[g]),
      .beat_q(beat_q[g*32+:32]),.beat_z(beat_z[g*32+:32]),
      .beat_epoch(beat_epoch[g*32+:32]),.beat_row(beat_row[g*32+:32]),
      .beat_input(beat_input[g*32+:32]),.beat_scale(beat_scale[g*128+:128]),
      .beat_mask(beat_mask[g*8+:8]),.beat_row_first(beat_row_first[g]),
      .beat_row_last(beat_row_last[g]),.beat_tile_last(beat_tile_last[g]),
      .c_req_valid(c_req_valid[g]),.c_req_ready(c_req_ready[g]),
      .c_req_write(c_req_write[g]),.c_req_kind(c_req_kind[g*4+:4]),
      .c_req_layer(c_req_layer[g*32+:32]),.c_req_proj(c_req_proj[g*3+:3]),
      .c_req_row(c_req_row[g*32+:32]),.c_req_col(c_req_col[g*32+:32]),
      .c_req_wdata(c_req_wdata[g*32+:32]),
      .c_rsp_valid(c_rsp_valid[g]),.c_rsp_error(c_rsp_error[g]),
      .c_rsp_ready(c_rsp_ready[g]),.c_rsp_rdata(c_rsp_rdata[g*32+:32])
    );
  end endgenerate
endmodule

module anvil_q3_weight_prefetch_bank #(
  parameter TILE_K=128, TILE_ROWS=8,
  parameter NUM_LAYERS=36, HIDDEN_SIZE=2048, INTERMEDIATE_SIZE=11008,
  parameter NUM_KV_HEADS=2, HEAD_DIM=128, GROUP_SIZE=128,
  localparam TK=TILE_K>0 && TILE_K<=128 && TILE_K%8==0 ? TILE_K : 8,
  localparam TR=TILE_ROWS>=1 && TILE_ROWS<=8 ? TILE_ROWS : 1
) (
  input wire clk, rst_n, flush, desc_valid,
  output wire desc_ready, fault,
  input wire [31:0] desc_epoch, desc_layer, desc_output_base, desc_input_base,
  input wire [31:0] desc_valid_rows, desc_valid_inputs,
  input wire [2:0] desc_proj,
  output wire beat_valid,
  input wire beat_ready,
  output wire [31:0] beat_q, beat_z, beat_epoch, beat_row, beat_input,
  output wire [127:0] beat_scale,
  output wire [7:0] beat_mask,
  output wire beat_row_first, beat_row_last, beat_tile_last,
  output wire c_req_valid,
  input wire c_req_ready,
  output wire c_req_write,
  output wire [3:0] c_req_kind,
  output wire [31:0] c_req_layer,
  output wire [2:0] c_req_proj,
  output wire [31:0] c_req_row, c_req_col, c_req_wdata,
  input wire c_rsp_valid, c_rsp_error,
  output wire c_rsp_ready,
  input wire [31:0] c_rsp_rdata
);
  localparam CELLS=TK*TR;
  localparam EMPTY=0, FILLING=1, READY=2, ACTIVE=3;
  localparam F_IDLE=0, F_GROUP=1, F_Q_REQ=2, F_Q_RSP=3;
  localparam F_Z_REQ=4, F_Z_RSP=5, F_S_REQ=6, F_S_RSP=7;
  localparam [63:0] KV_DIM=64'(NUM_KV_HEADS)*64'(HEAD_DIM);
  localparam LEGAL=TILE_K>0 && TILE_K<=128 && TILE_K%8==0 &&
    TILE_ROWS>=1 && TILE_ROWS<=8 && TK==TILE_K && TR==TILE_ROWS &&
    NUM_LAYERS>0 && HIDDEN_SIZE>0 && INTERMEDIATE_SIZE>0 &&
    NUM_KV_HEADS>0 && HEAD_DIM>0 && GROUP_SIZE>0 && KV_DIM<=64'hffffffff;
  generate if (!LEGAL) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q3 PARAMETER ERROR: prefetch tile geometry");
  end endgenerate

  reg [1:0] tile_state [0:1];
  reg [31:0] epoch [0:1], layer [0:1], output_base [0:1], input_base [0:1];
  reg [31:0] valid_rows [0:1], valid_inputs [0:1], output_limit [0:1];
  reg [2:0] projection [0:1];
  reg [3:0] q_storage [0:2*CELLS-1], z_storage [0:2*CELLS-1];
  reg [15:0] scale_storage [0:2*CELLS-1];
  reg head, tail, fill_select, failed, fault_pulse;
  reg [2:0] fill_state;
  reg [31:0] fill_row, fill_input, group_index, group_offset;
  reg [31:0] base_group, base_offset, group_work;
  reg [31:0] read_row, read_input;
  reg all_read, read_valid;
  reg [31:0] read_q, read_z, read_epoch, read_global_row, read_global_input;
  reg [127:0] read_scale;
  reg [7:0] read_mask;
  reg read_first, read_last, read_final;
  integer i, lane;
  wire [31:0] incoming_inputs=desc_proj==6 ? INTERMEDIATE_SIZE : HIDDEN_SIZE;
  wire [31:0] incoming_outputs=(desc_proj==1 || desc_proj==2) ? KV_DIM[31:0] :
    (desc_proj==4 || desc_proj==5) ? INTERMEDIATE_SIZE : HIDDEN_SIZE;
  wire bad_descriptor=desc_layer>=NUM_LAYERS || desc_proj>6 ||
    desc_valid_rows==0 || desc_valid_rows>TR ||
    desc_valid_inputs==0 || desc_valid_inputs>TK ||
    ({1'b0,desc_output_base}+{1'b0,desc_valid_rows})>{1'b0,incoming_outputs} ||
    ({1'b0,desc_input_base}+{1'b0,desc_valid_inputs})>{1'b0,incoming_inputs};
  wire request_state=fill_state==F_Q_REQ || fill_state==F_Z_REQ || fill_state==F_S_REQ;
  wire response_state=fill_state==F_Q_RSP || fill_state==F_Z_RSP || fill_state==F_S_RSP;
  wire [31:0] fill_global_row=output_base[fill_select]+fill_row;
  wire [31:0] fill_global_input=input_base[fill_select]+fill_input;
  wire [31:0] fill_address=(fill_select ? CELLS : 0)+fill_row*TK+fill_input;
  wire load_read=tile_state[head]==ACTIVE && !all_read && (!read_valid || beat_ready);
  wire final_load=(read_row+1==valid_rows[head]) && (read_input+8>=valid_inputs[head]);
  wire bad_fill=(c_rsp_valid && !response_state) ||
    (c_rsp_valid && response_state && c_rsp_error) ||
    (c_rsp_valid && fill_state==F_S_RSP &&
      (c_rsp_rdata[31:16]!=0 ||
       anvil_q3_pkg::f16_scale_invalid(c_rsp_rdata[15:0]))) ||
    (c_rsp_valid && (fill_state==F_Q_RSP || fill_state==F_Z_RSP) &&
      bad_packed_padding(c_rsp_rdata,fill_global_row & 32'hfffffff8,
                         output_limit[fill_select]));

  function automatic bad_packed_padding(
    input reg [31:0] word_value, input reg [31:0] packed_base, limit_value
  );
    integer p;
    begin
      bad_packed_padding=0;
      for (p=0;p<8;p=p+1)
        if ({1'b0,packed_base}+p>={1'b0,limit_value} &&
            ((word_value>>anvil_q3_pkg::awq_lane_shift(3'(p))) & 32'hf)!=0)
          bad_packed_padding=1;
    end
  endfunction

  assign desc_ready=rst_n && !flush && !failed && tile_state[tail]==EMPTY;
  assign fault=rst_n && !flush && fault_pulse;
  assign beat_valid=rst_n && !flush && !failed && read_valid;
  assign beat_q=beat_valid ? read_q : 32'd0;
  assign beat_z=beat_valid ? read_z : 32'd0;
  assign beat_scale=beat_valid ? read_scale : 128'd0;
  assign beat_mask=beat_valid ? read_mask : 8'd0;
  assign beat_epoch=beat_valid ? read_epoch : 32'd0;
  assign beat_row=beat_valid ? read_global_row : 32'd0;
  assign beat_input=beat_valid ? read_global_input : 32'd0;
  assign beat_row_first=beat_valid && read_first;
  assign beat_row_last=beat_valid && read_last;
  assign beat_tile_last=beat_valid && read_final;
  assign c_req_valid=rst_n && !flush && !failed && request_state;
  assign c_req_write=1'b0;
  assign c_req_kind=!c_req_valid ? 4'd0 : fill_state==F_Q_REQ ? 4'd1 :
    fill_state==F_Z_REQ ? 4'd2 : 4'd3;
  assign c_req_layer=c_req_valid ? layer[fill_select] : 32'd0;
  assign c_req_proj=c_req_valid ? projection[fill_select] : 3'd0;
  assign c_req_row=!c_req_valid ? 32'd0 : fill_state==F_Q_REQ ? fill_global_input : group_index;
  assign c_req_col=!c_req_valid ? 32'd0 :
    fill_state==F_S_REQ ? fill_global_row : fill_global_row>>3;
  assign c_req_wdata=32'd0;
  assign c_rsp_ready=rst_n && !flush && !failed;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      head<=0; tail<=0; fill_select<=0; failed<=0; fault_pulse<=0;
      fill_state<=F_IDLE; fill_row<=0; fill_input<=0;
      group_index<=0; group_offset<=0; base_group<=0; base_offset<=0; group_work<=0;
      read_row<=0; read_input<=0; all_read<=0; read_valid<=0;
      read_q<=0; read_z<=0; read_scale<=0; read_mask<=0;
      read_epoch<=0; read_global_row<=0; read_global_input<=0;
      read_first<=0; read_last<=0; read_final<=0;
      for (i=0;i<2;i=i+1) begin
        tile_state[i]<=EMPTY; epoch[i]<=0; layer[i]<=0;
        output_base[i]<=0; input_base[i]<=0; valid_rows[i]<=0; valid_inputs[i]<=0;
        output_limit[i]<=0; projection[i]<=0;
      end
    end else if (flush) begin
      head<=0; tail<=0; fill_state<=F_IDLE; failed<=0; fault_pulse<=0;
      tile_state[0]<=EMPTY; tile_state[1]<=EMPTY;
      read_valid<=0; all_read<=0;
    end else begin
      fault_pulse<=0;
      if (!failed) begin
        if ((desc_valid && desc_ready && bad_descriptor) || bad_fill) begin
          failed<=1;
          fault_pulse<=1;
          read_valid<=0;
        end else begin
          if (desc_valid && desc_ready) begin
            tile_state[tail]<=FILLING;
            epoch[tail]<=desc_epoch; layer[tail]<=desc_layer;
            output_base[tail]<=desc_output_base; input_base[tail]<=desc_input_base;
            valid_rows[tail]<=desc_valid_rows; valid_inputs[tail]<=desc_valid_inputs;
            output_limit[tail]<=incoming_outputs; projection[tail]<=desc_proj;
            tail<=!tail;
          end
          case (fill_state)
            F_IDLE: begin
              if (tile_state[head]==FILLING || tile_state[!head]==FILLING) begin
                fill_select<=tile_state[head]==FILLING ? head : !head;
                group_work<=tile_state[head]==FILLING ? input_base[head] : input_base[!head];
                group_index<=0; fill_row<=0; fill_input<=0;
                fill_state<=F_GROUP;
              end
            end
            F_GROUP: begin
              if (group_work>=GROUP_SIZE) begin
                group_work<=group_work-GROUP_SIZE;
                group_index<=group_index+1'b1;
              end else begin
                base_group<=group_index; base_offset<=group_work;
                group_offset<=group_work;
                fill_state<=F_Q_REQ;
              end
            end
            F_Q_REQ: if (c_req_ready) fill_state<=F_Q_RSP;
            F_Q_RSP: if (c_rsp_valid) begin
              q_storage[fill_address]<=c_rsp_rdata>>
                anvil_q3_pkg::awq_lane_shift(fill_global_row[2:0]);
              fill_state<=F_Z_REQ;
            end
            F_Z_REQ: if (c_req_ready) fill_state<=F_Z_RSP;
            F_Z_RSP: if (c_rsp_valid) begin
              z_storage[fill_address]<=c_rsp_rdata>>
                anvil_q3_pkg::awq_lane_shift(fill_global_row[2:0]);
              fill_state<=F_S_REQ;
            end
            F_S_REQ: if (c_req_ready) fill_state<=F_S_RSP;
            F_S_RSP: if (c_rsp_valid) begin
              scale_storage[fill_address]<=c_rsp_rdata[15:0];
              if (fill_input+1==valid_inputs[fill_select]) begin
                fill_input<=0; group_index<=base_group; group_offset<=base_offset;
                if (fill_row+1==valid_rows[fill_select]) begin
                  tile_state[fill_select]<=READY;
                  fill_state<=F_IDLE;
                end else begin
                  fill_row<=fill_row+1'b1;
                  fill_state<=F_Q_REQ;
                end
              end else begin
                fill_input<=fill_input+1'b1;
                if (group_offset+1==GROUP_SIZE) begin
                  group_offset<=0;
                  group_index<=group_index+1'b1;
                end else group_offset<=group_offset+1'b1;
                fill_state<=F_Q_REQ;
              end
            end
            default: begin failed<=1; fault_pulse<=1; end
          endcase

          if (tile_state[head]==READY) begin
            tile_state[head]<=ACTIVE;
            read_row<=0; read_input<=0; all_read<=0;
          end
          if (read_valid && beat_ready) begin
            read_valid<=0;
            if (read_final) begin
              tile_state[head]<=EMPTY;
              head<=!head;
            end
          end
          if (load_read) begin
            read_valid<=1;
            read_epoch<=epoch[head];
            read_global_row<=output_base[head]+read_row;
            read_global_input<=input_base[head]+read_input;
            read_first<=read_input==0;
            read_last<=read_input+8>=valid_inputs[head];
            read_final<=final_load;
            for (lane=0;lane<8;lane=lane+1) begin
              read_mask[lane]<=read_input+lane<valid_inputs[head];
              if (read_input+lane<valid_inputs[head]) begin
                read_q[lane*4+:4]<=q_storage[(head ? CELLS : 0)+read_row*TK+read_input+lane];
                read_z[lane*4+:4]<=z_storage[(head ? CELLS : 0)+read_row*TK+read_input+lane];
                read_scale[lane*16+:16]<=scale_storage[(head ? CELLS : 0)+read_row*TK+read_input+lane];
              end else begin
                read_q[lane*4+:4]<=0; read_z[lane*4+:4]<=0; read_scale[lane*16+:16]<=0;
              end
            end
            if (final_load) all_read<=1;
            else if (read_input+8>=valid_inputs[head]) begin
              read_input<=0;
              read_row<=read_row+1'b1;
            end else read_input<=read_input+8;
          end
        end
      end
    end
  end
endmodule
