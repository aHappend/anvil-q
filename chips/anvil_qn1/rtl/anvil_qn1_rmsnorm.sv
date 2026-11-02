module anvil_qn1_rmsnorm #(
  parameter EXTENT=2560
) (
  input wire clk, rst_n, flush, start_valid,
  output wire start_ready,
  input wire in_valid,
  output wire in_ready,
  input wire [15:0] in_data, in_gamma,
  output wire out_valid,
  input wire out_ready,
  output wire [31:0] out_index,
  output wire [15:0] out_data,
  output wire out_error, done
);
  import anvil_qn1_pkg::*;
  generate if (EXTENT>=1 && EXTENT<=2560) begin: legal
    localparam PADDED=1 << $clog2(EXTENT);
    localparam AW=PADDED==1 ? 1 : $clog2(PADDED);
    localparam TW=$clog2(2*PADDED);
    localparam IDLE=0, CAPTURE=1, PAD=2, SQUARE_READ=3, SQUARE=4;
    localparam REDUCE_READ=5, REDUCE=6, MEAN=7, EPSILON=8, ROOT=9;
    localparam RECIPROCAL=10, SCALE_READ=11, SCALE=12, ROUND_U=13;
    localparam GAMMA=14, ROUND_Y=15, OUTPUT=16, FINISH=17;
    reg [4:0] state;
    reg waiting, failed, done_reg;
    reg [31:0] cursor, parent;
    reg [31:0] sum, mean, variance, root, reciprocal, product;
    reg [15:0] u, result;
    (* ramstyle="M20K", nomem2reg *) reg [15:0] raw [0:PADDED-1];
    (* ramstyle="M20K", nomem2reg *) reg [15:0] gamma [0:PADDED-1];
    (* ramstyle="M20K", nomem2reg *) reg [31:0] tree [0:2*PADDED-1];
    reg [15:0] raw_q, gamma_q;
    reg [31:0] left_q, right_q;
    wire [TW-1:0] left_address=TW'(parent << 1);
    wire [TW-1:0] right_address=TW'((parent << 1)+1);
    wire capture=rst_n && !flush && state==CAPTURE && in_valid;
    wire arithmetic_state=state==SQUARE || state==REDUCE || state==MEAN ||
      state==EPSILON || state==ROOT || state==RECIPROCAL || state==SCALE || state==GAMMA;
    reg [2:0] op;
    reg [31:0] a, b;
    wire alu_ready, alu_valid, alu_error;
    wire [31:0] alu_data;
    wire completed=alu_valid && waiting;
    wire [16:0] rounded=round_bf16(product);
    localparam [31:0] EXTENT32=unsigned32_to_fp32(32'(EXTENT));
    always @* begin
      op=0; a=0; b=0;
      case (state)
        SQUARE: begin op=2; a={raw_q,16'd0}; b={raw_q,16'd0}; end
        REDUCE: begin op=0; a=left_q; b=right_q; end
        MEAN: begin op=3; a=sum; b=EXTENT32; end
        EPSILON: begin op=0; a=mean; b=EPSILON32; end
        ROOT: begin op=4; a=variance; end
        RECIPROCAL: begin op=3; a=32'h3f800000; b=root; end
        SCALE: begin op=2; a={raw_q,16'd0}; b=reciprocal; end
        GAMMA: begin op=2; a={u,16'd0}; b={gamma_q,16'd0}; end
        default: begin end
      endcase
    end
    anvil_qn1_scalar arithmetic (
      .clk(clk),.rst_n(rst_n),.flush(flush),
      .in_valid(arithmetic_state && !waiting),.in_ready(alu_ready),
      .in_op(op),.in_a(a),.in_b(b),.in_error(failed),
      .out_valid(alu_valid),.out_ready(waiting),.out_data(alu_data),.out_error(alu_error)
    );
    always @(posedge clk) begin
      raw_q<=raw[cursor[AW-1:0]]; gamma_q<=gamma[cursor[AW-1:0]];
      left_q<=tree[left_address]; right_q<=tree[right_address];
      if (capture) begin raw[cursor[AW-1:0]]<=in_data; gamma[cursor[AW-1:0]]<=in_gamma; end
      if (rst_n && !flush) begin
        if (state==PAD) tree[TW'(PADDED+cursor)]<=0;
        else if (completed && state==SQUARE) tree[TW'(PADDED+cursor)]<=alu_data;
        else if (completed && state==REDUCE) tree[parent[TW-1:0]]<=alu_data;
      end
    end
    assign start_ready=rst_n && !flush && state==IDLE && !done_reg;
    assign in_ready=rst_n && !flush && state==CAPTURE;
    assign out_valid=rst_n && !flush && state==OUTPUT;
    assign out_index=out_valid ? cursor : 32'd0;
    assign out_data=out_valid && !failed ? result : 16'd0;
    assign out_error=out_valid && failed;
    assign done=rst_n && !flush && done_reg;
    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        state<=IDLE; waiting<=0; failed<=0; done_reg<=0; cursor<=0; parent<=0;
        sum<=0; mean<=0; variance<=0; root<=0; reciprocal<=0; product<=0;
        u<=0; result<=0;
      end else if (flush) begin
        state<=IDLE; waiting<=0; failed<=0; done_reg<=0; result<=0;
      end else begin
        done_reg<=0;
        if (arithmetic_state && !waiting && alu_ready) waiting<=1;
        if (completed) begin
          waiting<=0;
          if (alu_error) failed<=1;
          case (state)
            SQUARE: begin
              if (cursor==EXTENT-1) begin
                if (PADDED==1) begin sum<=alu_data; state<=MEAN; end
                else begin parent<=PADDED-1; state<=REDUCE_READ; end
              end else begin cursor<=cursor+1'b1; state<=SQUARE_READ; end
            end
            REDUCE: begin
              if (parent==1) begin sum<=alu_data; state<=MEAN; end
              else begin parent<=parent-1'b1; state<=REDUCE_READ; end
            end
            MEAN: begin mean<=alu_data; state<=EPSILON; end
            EPSILON: begin variance<=alu_data; state<=ROOT; end
            ROOT: begin root<=alu_data; state<=RECIPROCAL; end
            RECIPROCAL: begin reciprocal<=alu_data; cursor<=0; state<=SCALE_READ; end
            SCALE: begin product<=alu_data; state<=ROUND_U; end
            GAMMA: begin product<=alu_data; state<=ROUND_Y; end
            default: begin failed<=1; state<=FINISH; end
          endcase
        end else case (state)
          IDLE: if (start_valid && start_ready) begin
            cursor<=0; failed<=0; waiting<=0; state<=CAPTURE;
          end
          CAPTURE: if (capture) begin
            if (bf16_invalid(in_data) || bf16_invalid(in_gamma)) failed<=1;
            if (cursor==EXTENT-1) begin
              if (EXTENT<PADDED) begin cursor<=EXTENT; state<=PAD; end
              else begin cursor<=0; state<=SQUARE_READ; end
            end else cursor<=cursor+1'b1;
          end
          PAD: begin
            if (cursor==PADDED-1) begin cursor<=0; state<=SQUARE_READ; end
            else cursor<=cursor+1'b1;
          end
          SQUARE_READ: state<=SQUARE;
          REDUCE_READ: state<=REDUCE;
          SCALE_READ: state<=SCALE;
          ROUND_U: begin
            u<=rounded[16] ? 16'd0 : rounded[15:0];
            if (rounded[16]) failed<=1;
            state<=GAMMA;
          end
          ROUND_Y: begin
            result<=rounded[16] ? 16'd0 : rounded[15:0];
            if (rounded[16]) failed<=1;
            state<=OUTPUT;
          end
          OUTPUT: if (out_ready) begin
            if (cursor==EXTENT-1) state<=FINISH;
            else begin cursor<=cursor+1'b1; state<=SCALE_READ; end
          end
          FINISH: begin done_reg<=1; state<=IDLE; end
          default: begin end
        endcase
      end
    end
  end else begin: invalid
    initial $fatal(1,"ANVIL_QN1 PARAMETER ERROR: ordinary norm extent");
    assign start_ready=0; assign in_ready=0; assign out_valid=0;
    assign out_index=0; assign out_data=0; assign out_error=0; assign done=0;
  end endgenerate
endmodule
