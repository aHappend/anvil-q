module anvil_q3_signed_divider (
  input wire clk, rst_n, flush, start,
  input wire signed [127:0] numerator,
  input wire [63:0] denominator,
  output wire ready, done, error,
  output wire signed [127:0] quotient
);
  localparam IDLE=0, ABSOLUTE=1, ROUND=2, DIVIDE=3, WAIT=4, SIGN=5;
  reg [2:0] state;
  reg [3:0] segment;
  reg negative, carry, done_reg, error_reg;
  reg [127:0] operand, magnitude, result;
  reg [143:0] rounded;
  reg [63:0] divisor;
  reg [128:0] unsigned_quotient;
  wire [143:0] magnitude_padded={16'd0,magnitude};
  wire [143:0] rounding_padded={80'd0,divisor>>1};
  wire [16:0] absolute_segment={1'b0,~operand[segment*16+:16]}+{16'd0,carry};
  wire [16:0] round_segment={1'b0,magnitude_padded[segment*16+:16]}+
    {1'b0,rounding_padded[segment*16+:16]}+{16'd0,carry};
  wire [16:0] sign_segment={1'b0,~unsigned_quotient[segment*16+:16]}+{16'd0,carry};
  wire divide_ready, divide_done, divide_error;
  wire [128:0] divided;
  wire [63:0] remainder;

  assign ready=rst_n && !flush && state==IDLE && divide_ready;
  assign done=rst_n && !flush && done_reg;
  assign error=done && error_reg;
  assign quotient=rst_n && !flush ? $signed(result) : 128'sd0;
  anvil_q3_divider #(.NUM_W(129),.DEN_W(64)) divider (
    .clk(clk),.rst_n(rst_n),.flush(flush),.start(state==DIVIDE),
    .numerator(rounded[128:0]),.denominator(divisor),
    .ready(divide_ready),.done(divide_done),.error(divide_error),
    .quotient(divided),.remainder(remainder)
  );
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; segment<=0; negative<=0; carry<=0; done_reg<=0; error_reg<=0;
      operand<=0; magnitude<=0; result<=0; rounded<=0; divisor<=0; unsigned_quotient<=0;
    end else if (flush) begin
      state<=IDLE; done_reg<=0; error_reg<=0; result<=0;
    end else begin
      done_reg<=0; error_reg<=0;
      case (state)
        IDLE: if (start && ready) begin
          operand<=numerator; negative<=numerator[127]; divisor<=denominator;
          segment<=0; carry<=1; magnitude<=0; rounded<=0;
          if (denominator==0) begin done_reg<=1; error_reg<=1; result<=0; end
          else state<=ABSOLUTE;
        end
        ABSOLUTE: begin
          magnitude[segment*16+:16]<=negative ? absolute_segment[15:0] : operand[segment*16+:16];
          carry<=absolute_segment[16];
          if (segment==7) begin segment<=0; carry<=0; state<=ROUND; end
          else segment<=segment+1'b1;
        end
        ROUND: begin
          rounded[segment*16+:16]<=round_segment[15:0];
          carry<=round_segment[16];
          if (segment==8) begin segment<=0; state<=DIVIDE; end
          else segment<=segment+1'b1;
        end
        DIVIDE: if (divide_ready) state<=WAIT;
        WAIT: if (divide_done) begin
          if (divide_error || divided[128] ||
              (!negative && divided[127]) ||
              (negative && divided>(129'd1<<127))) begin
            state<=IDLE; done_reg<=1; error_reg<=1; result<=0;
          end else begin unsigned_quotient<=divided; segment<=0; carry<=1; state<=SIGN; end
        end
        SIGN: begin
          result[segment*16+:16]<=negative ? sign_segment[15:0] : unsigned_quotient[segment*16+:16];
          carry<=sign_segment[16];
          if (segment==7) begin state<=IDLE; done_reg<=1; end
          else segment<=segment+1'b1;
        end
        default: begin state<=IDLE; done_reg<=1; error_reg<=1; result<=0; end
      endcase
    end
  end
endmodule
