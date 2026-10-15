module anvil_q1_w4a16_gemv #(
  parameter NUM_LAYERS=24, HIDDEN_SIZE=896, INTERMEDIATE_SIZE=4864,
  NUM_Q_HEADS=14, NUM_KV_HEADS=2, HEAD_DIM=64, GROUP_SIZE=128,
  AWQ_BITS=4, MAX_SEQ_LEN=32768
)(
  input wire clk, rst_n, cmd_valid, output wire cmd_ready,
  input wire [31:0] cmd_layer, cmd_pos, input wire [2:0] cmd_proj,
  output wire done, error,
  output wire mem_req_valid, input wire mem_req_ready,
  output wire mem_req_write, output wire [3:0] mem_req_kind,
  output wire [31:0] mem_req_layer, output wire [2:0] mem_req_proj,
  output wire [31:0] mem_req_row, mem_req_col, mem_req_wdata,
  input wire mem_rsp_valid, output wire mem_rsp_ready,
  input wire [31:0] mem_rsp_rdata, input wire mem_rsp_error
);
  localparam SAFE_GROUP = GROUP_SIZE > 0 ? GROUP_SIZE : 1;
  reg [4:0] state;
  reg failed;
  reg [31:0] layer, pos, k, c, inputs, outputs, source_slot, target_slot;
  reg [2:0] projection;
  reg [31:0] qw, qz;
  reg [15:0] scale;
  reg signed [15:0] activation;
  wire signed [36:0] weight;
  wire invalid;
  wire signed [52:0] product;
  reg signed [95:0] accumulator;
  wire idle, complete, fault;
  wire [31:0] rd;
  wire signed [15:0] bias_value;
  assign bias_value = anvil_q1_pkg::f16_q8(rd[15:0]);
  anvil_q1_parameters #(
    NUM_LAYERS,HIDDEN_SIZE,INTERMEDIATE_SIZE,NUM_Q_HEADS,NUM_KV_HEADS,
    HEAD_DIM,GROUP_SIZE,AWQ_BITS,1,MAX_SEQ_LEN) parameters_ok();
  reg issue, wr;
  reg [3:0] kind;
  reg [31:0] row, col, wd, ml;
  reg [2:0] mp;
  anvil_q1_awq_dequant dequant(
    .qweight_word(qw),.qzero_word(qz),.scale_f16(scale),.lane(c[2:0]),
    .weight_q16_16(weight),.invalid(invalid));
  assign product = {{37{activation[15]}},activation} * {{16{weight[36]}},weight};
  assign cmd_ready = rst_n && state == 0;
  assign done = rst_n && state == 20;
  assign error = done && failed;
  anvil_q1_mem_port port(
    .clk(clk),.rst_n(rst_n),.issue(issue),.write(wr),.kind(kind),
    .layer(ml),.proj(mp),.row(row),.col(col),.wdata(wd),
    .idle(idle),.complete(complete),.rdata(rd),.fault(fault),
    .mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),
    .mem_req_write(mem_req_write),.mem_req_kind(mem_req_kind),
    .mem_req_layer(mem_req_layer),.mem_req_proj(mem_req_proj),
    .mem_req_row(mem_req_row),.mem_req_col(mem_req_col),.mem_req_wdata(mem_req_wdata),
    .mem_rsp_valid(mem_rsp_valid),.mem_rsp_ready(mem_rsp_ready),
    .mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_error(mem_rsp_error));
  always @* begin
    issue=0; wr=0; kind=0; row=0; col=0; wd=0; ml=0; mp=0;
    if (rst_n && idle) case(state)
      1: begin issue=1; kind=8; row=source_slot; col=k; end
      3: begin issue=1; kind=1; ml=layer; mp=projection; row=k; col=c/8; end
      5: begin issue=1; kind=2; ml=layer; mp=projection; row=k/SAFE_GROUP; col=c/8; end
      7: begin issue=1; kind=3; ml=layer; mp=projection; row=k/SAFE_GROUP; col=c; end
      11: begin issue=1; kind=4; ml=layer; mp=projection; col=c; end
      13: begin
        issue=1; wr=1; kind=8; row=target_slot; col=c;
        wd={16'd0,anvil_q1_pkg::sat16(anvil_q1_pkg::round_shift(accumulator,16))};
      end
      default: begin end
    endcase
  end
  always @(posedge clk) begin
    if (!rst_n) begin
      state<=0; failed<=0; layer<=0; pos<=0; k<=0; c<=0;
      inputs<=0; outputs<=0; source_slot<=0; target_slot<=0;
      projection<=0; qw<=0; qz<=0; scale<=0; activation<=0; accumulator<=0;
    end else if(fault) begin failed<=1; state<=20; end
    else case(state)
      0: if(cmd_valid) begin
        failed<=0; layer<=cmd_layer; pos<=cmd_pos; projection<=cmd_proj;
        k<=0; c<=0; accumulator<=0;
        if(cmd_layer>=NUM_LAYERS || cmd_pos>=MAX_SEQ_LEN || cmd_proj>6)
          begin failed<=1; state<=19; end
        else begin
          inputs<=cmd_proj==6 ? INTERMEDIATE_SIZE : HIDDEN_SIZE;
          case(cmd_proj)
            0: begin outputs<=HIDDEN_SIZE; source_slot<=1; target_slot<=2; end
            1: begin outputs<=NUM_KV_HEADS*HEAD_DIM; source_slot<=1; target_slot<=3; end
            2: begin outputs<=NUM_KV_HEADS*HEAD_DIM; source_slot<=1; target_slot<=4; end
            3: begin outputs<=HIDDEN_SIZE; source_slot<=5; target_slot<=6; end
            4: begin outputs<=INTERMEDIATE_SIZE; source_slot<=8; target_slot<=9; end
            5: begin outputs<=INTERMEDIATE_SIZE; source_slot<=8; target_slot<=10; end
            default: begin outputs<=HIDDEN_SIZE; source_slot<=11; target_slot<=12; end
          endcase
          state<=1;
        end
      end
      1: if(issue) state<=2;
      2: if(complete) begin activation<=rd[15:0]; state<=3; end
      3: if(issue) state<=4;
      4: if(complete) begin qw<=rd; state<=5; end
      5: if(issue) state<=6;
      6: if(complete) begin qz<=rd; state<=7; end
      7: if(issue) state<=8;
      8: if(complete) begin scale<=rd[15:0]; state<=9; end
      9: if(invalid) begin failed<=1; state<=20; end
         else begin accumulator<=accumulator+{{43{product[52]}},product}; state<=10; end
      10: if(k+1<inputs) begin k<=k+1; state<=1; end
          else if(projection<3) state<=11;
          else state<=13;
      11: if(issue) state<=12;
      12: if(complete) begin
        if(anvil_q1_pkg::f16_invalid(rd[15:0])) begin failed<=1; state<=20; end
        else begin
          accumulator<=accumulator+($signed({{80{bias_value[15]}},bias_value}) <<< 16);
          state<=13;
        end
      end
      13: if(issue) state<=14;
      14: if(complete) begin
        if(c+1<outputs) begin c<=c+1; k<=0; accumulator<=0; state<=1; end
        else state<=20;
      end
      19: state<=20;
      20: state<=0;
      default: state<=0;
    endcase
  end
endmodule
