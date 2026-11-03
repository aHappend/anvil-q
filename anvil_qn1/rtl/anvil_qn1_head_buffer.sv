module anvil_qn1_head_buffer #(
  parameter HEAD_DIM=128, MAX_SEQ_LEN=40960
) (
  input wire clk, rst_n, flush, start_valid,
  output wire start_ready,
  input wire start_is_key,
  input wire [5:0] start_heads,
  input wire [31:0] start_layer, start_pos,
  input wire [(HEAD_DIM>0 ? HEAD_DIM : 1)*16-1:0] start_gamma,
  input wire [(HEAD_DIM>1 ? HEAD_DIM/2 : 1)*16-1:0] start_cos, start_sin,
  input wire in_valid,
  output wire in_ready,
  input wire [31:0] in_index,
  input wire [15:0] in_data,
  output wire head_valid,
  input wire head_ready,
  output wire head_is_key,
  output wire [5:0] head_index,
  output wire [31:0] head_layer, head_pos,
  output wire [(HEAD_DIM>0 ? HEAD_DIM : 1)*16-1:0] head_data, head_gamma,
  output wire [(HEAD_DIM>1 ? HEAD_DIM/2 : 1)*16-1:0] head_cos, head_sin,
  output wire head_last, input_done, error
);
  generate if ((HEAD_DIM==8 || HEAD_DIM==16 || HEAD_DIM==32 ||
      HEAD_DIM==64 || HEAD_DIM==128) && MAX_SEQ_LEN>=1 && MAX_SEQ_LEN<=40960) begin: legal
    localparam DS=$clog2(HEAD_DIM);
    localparam FREE=0, CAPTURE=1, READY=2;
    reg [1:0] state [0:1];
    reg fill_slot, drain_slot, capturing, failed, done_reg, is_key;
    reg [5:0] heads;
    reg [31:0] layer, position, expected_index;
    reg [HEAD_DIM*16-1:0] gamma, data [0:1], gammas [0:1];
    reg [(HEAD_DIM/2)*16-1:0] cosine, sine, cosines [0:1], sines [0:1];
    reg [1:0] keys, lasts;
    reg [5:0] indices [0:1];
    reg [31:0] layers [0:1], positions [0:1];
    wire accepting=in_valid && in_ready;
    wire malformed=accepting && in_index!=expected_index;
    wire first_coordinate=expected_index[DS-1:0]==0;
    wire final_coordinate=&expected_index[DS-1:0];
    wire final_head=(expected_index >> DS)==({26'd0,heads}-1'b1);
    assign start_ready=rst_n && !flush && !failed && !capturing && !done_reg;
    assign in_ready=rst_n && !flush && !failed && capturing &&
      (state[fill_slot]==FREE || state[fill_slot]==CAPTURE);
    assign head_valid=rst_n && !flush && !failed && !malformed && state[drain_slot]==READY;
    assign head_is_key=head_valid && keys[drain_slot];
    assign head_index=head_valid ? indices[drain_slot] : 6'd0;
    assign head_layer=head_valid ? layers[drain_slot] : 32'd0;
    assign head_pos=head_valid ? positions[drain_slot] : 32'd0;
    assign head_data=head_valid ? data[drain_slot] : {HEAD_DIM*16{1'b0}};
    assign head_gamma=head_valid ? gammas[drain_slot] : {HEAD_DIM*16{1'b0}};
    assign head_cos=head_valid ? cosines[drain_slot] : {(HEAD_DIM/2)*16{1'b0}};
    assign head_sin=head_valid ? sines[drain_slot] : {(HEAD_DIM/2)*16{1'b0}};
    assign head_last=head_valid && lasts[drain_slot];
    assign input_done=rst_n && !flush && !failed && done_reg;
    assign error=rst_n && !flush && (failed || malformed);
    integer slot;
    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        fill_slot<=0; drain_slot<=0; capturing<=0; failed<=0; done_reg<=0; is_key<=0;
        heads<=0; layer<=0; position<=0; expected_index<=0;
        gamma<=0; cosine<=0; sine<=0; keys<=0; lasts<=0;
        for (slot=0;slot<2;slot=slot+1) begin
          state[slot]<=FREE; data[slot]<=0; gammas[slot]<=0;
          cosines[slot]<=0; sines[slot]<=0; indices[slot]<=0;
          layers[slot]<=0; positions[slot]<=0;
        end
      end else if (flush) begin
        fill_slot<=0; drain_slot<=0; capturing<=0; failed<=0; done_reg<=0;
        state[0]<=FREE; state[1]<=FREE;
      end else begin
        done_reg<=0;
        if (malformed) begin failed<=1; capturing<=0; state[0]<=FREE; state[1]<=FREE; end
        else begin
          if (start_valid && start_ready) begin
            is_key<=start_is_key; heads<=start_heads; layer<=start_layer;
            position<=start_pos; gamma<=start_gamma; cosine<=start_cos; sine<=start_sin;
            expected_index<=0;
            if (start_heads<1 || start_heads>32 || (start_is_key && start_heads>8) ||
                start_pos>=MAX_SEQ_LEN) failed<=1;
            else capturing<=1;
          end
          if (accepting) begin
            data[fill_slot][expected_index[DS-1:0]*16+:16]<=in_data;
            expected_index<=expected_index+1'b1;
            if (first_coordinate) begin
              state[fill_slot]<=CAPTURE; gammas[fill_slot]<=gamma;
              cosines[fill_slot]<=cosine; sines[fill_slot]<=sine;
              indices[fill_slot]<=6'(expected_index >> DS);
              layers[fill_slot]<=layer; positions[fill_slot]<=position;
              keys[fill_slot]<=is_key; lasts[fill_slot]<=final_head;
            end
            if (final_coordinate) begin
              state[fill_slot]<=READY; fill_slot<=~fill_slot;
              if (final_head) begin capturing<=0; done_reg<=1; end
            end
          end
          if (head_valid && head_ready) begin state[drain_slot]<=FREE; drain_slot<=~drain_slot; end
        end
      end
    end
  end else begin: invalid
    initial $fatal(1,"ANVIL_QN1 PARAMETER ERROR: projected-head buffer geometry");
    assign start_ready=0; assign in_ready=0; assign head_valid=0; assign head_is_key=0;
    assign head_index=0; assign head_layer=0; assign head_pos=0; assign head_data=0;
    assign head_gamma=0; assign head_cos=0; assign head_sin=0;
    assign head_last=0; assign input_done=0; assign error=0;
  end endgenerate
endmodule
