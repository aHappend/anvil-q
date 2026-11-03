module anvil_b1_isqrt (
  input wire clk, rst_n, flush, start,
  input wire [127:0] radicand,
  output wire ready, done,
  output wire [63:0] root
);
  localparam IDLE=0, PREPARE=1, SUBTRACT=2, COMMIT=3;
  reg [1:0] state;
  reg done_reg, borrow;
  reg [2:0] segment;
  reg [6:0] remaining;
  reg [127:0] source;
  reg [63:0] root_reg;
  reg [67:0] remainder_reg;
  reg [79:0] trial, divisor, difference;
  wire [16:0] delta={1'b0,trial[segment*16+:16]}-
    {1'b0,divisor[segment*16+:16]}-{16'd0,borrow};
  assign ready=rst_n && !flush && state==IDLE;
  assign done=rst_n && !flush && done_reg;
  assign root=rst_n && !flush ? root_reg : 64'd0;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; done_reg<=0; borrow<=0; segment<=0; remaining<=0;
      source<=0; root_reg<=0; remainder_reg<=0; trial<=0; divisor<=0; difference<=0;
    end else if (flush) begin state<=IDLE; done_reg<=0; root_reg<=0; end
    else begin
      done_reg<=0;
      case (state)
        IDLE: if (start && ready) begin
          source<=radicand; root_reg<=0; remainder_reg<=0;
          remaining<=64; state<=PREPARE;
        end
        PREPARE: begin
          trial<={12'd0,remainder_reg[65:0],source[127:126]};
          divisor<={14'd0,root_reg,2'b01};
          source<=source<<2; difference<=0; borrow<=0; segment<=0; state<=SUBTRACT;
        end
        SUBTRACT: begin
          difference[segment*16+:16]<=delta[15:0]; borrow<=delta[16];
          if (segment==4) state<=COMMIT;
          else segment<=segment+1'b1;
        end
        COMMIT: begin
          remainder_reg<=borrow ? trial[67:0] : difference[67:0];
          root_reg<={root_reg[62:0],!borrow};
          remaining<=remaining-1'b1;
          if (remaining==1) begin state<=IDLE; done_reg<=1; end
          else state<=PREPARE;
        end
      endcase
    end
  end
endmodule
