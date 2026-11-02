module anvil_d1_isqrt (
  input wire clk, rst_n, flush, in_valid,
  output wire in_ready,
  input wire [127:0] radicand,
  output wire out_valid,
  input wire out_ready,
  output wire [63:0] root,
  output wire [64:0] remainder
);
  localparam IDLE=0, ITERATE=1, REGISTER=2;
  reg [1:0] state;
  reg armed, valid;
  reg [5:0] count;
  reg [127:0] input_shift;
  reg [65:0] rem_work;
  reg [63:0] root_work, result_root;
  reg [64:0] result_rem;
  wire [67:0] shifted={rem_work,input_shift[127:126]};
  wire [67:0] trial={2'd0,root_work,2'b01};
  wire [67:0] difference;
  wire borrow;
  anvil_d1_sub_unsigned #(.WIDTH(68)) subtract (
    .a(shifted),.b(trial),.difference(difference),.borrow(borrow)
  );
  assign in_ready=rst_n && armed && !flush && state==IDLE && !valid;
  assign out_valid=rst_n && !flush && valid;
  assign root=rst_n && !flush ? result_root : 64'd0;
  assign remainder=rst_n && !flush ? result_rem : 65'd0;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; armed<=0; valid<=0; count<=0; input_shift<=0;
      rem_work<=0; root_work<=0; result_root<=0; result_rem<=0;
    end else begin
      armed<=1;
      if (flush) begin state<=IDLE; valid<=0; result_root<=0; result_rem<=0; end
      else begin
        if (out_valid && out_ready) valid<=0;
        case (state)
          IDLE: if (in_valid && in_ready) begin
            input_shift<=radicand; rem_work<=0; root_work<=0; count<=0; state<=ITERATE;
          end
          ITERATE: begin
            input_shift<=input_shift<<2;
            root_work<={root_work[62:0],!borrow};
            rem_work<=borrow ? shifted[65:0] : difference[65:0];
            if (count==63) state<=REGISTER;
            else count<=count+1'b1;
          end
          REGISTER: begin
            result_root<=root_work; result_rem<=rem_work[64:0]; valid<=1; state<=IDLE;
          end
          default: state<=IDLE;
        endcase
      end
    end
  end
endmodule
