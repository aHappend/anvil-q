module anvil_d2_bf16_to_q16 (
  input wire clk, rst_n, flush,
  input wire in_valid,
  output wire in_ready,
  input wire [15:0] in_bf16,
  output wire out_valid,
  input wire out_ready,
  output wire signed [31:0] out_q16,
  output wire out_error
);
  reg armed, valid, failed;
  reg signed [31:0] value;

  function automatic [32:0] convert(input [15:0] bits);
    reg [7:0] significand;
    reg [31:0] magnitude, result;
    reg invalid;
    integer shift;
    begin
      significand={bits[14:7]!=0,bits[6:0]};
      magnitude=0;
      result=0;
      invalid=bits[14:7]==8'hff;
      shift={24'd0,bits[14:7]}-118;
      if (!invalid && bits[14:7]!=0) begin
        if (shift>=25) magnitude=32'hffffffff;
        else if (shift>=0) magnitude={24'd0,significand}<<shift;
        else if (shift>=-8) begin
          magnitude={24'd0,significand}>>(-shift);
          if (significand[(-shift)-1]) magnitude=magnitude+1'b1;
        end
      end
      if (!invalid) begin
        if (bits[15]) begin
          if (magnitude>=32'h80000000) result=32'h80000000;
          else result=(~magnitude)+1'b1;
        end else begin
          if (magnitude>32'h7fffffff) result=32'h7fffffff;
          else result=magnitude;
        end
      end
      convert={invalid,result};
    end
  endfunction

  wire [32:0] converted=convert(in_bf16);
  wire enabled=rst_n && armed && !flush;
  assign in_ready=enabled && (!valid || out_ready);
  assign out_valid=enabled && valid;
  assign out_q16=out_valid ? value : 32'sd0;
  assign out_error=out_valid && failed;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin armed<=0; valid<=0; failed<=0; value<=0; end
    else begin
      armed<=1;
      if (flush) begin valid<=0; failed<=0; value<=0; end
      else if (in_ready) begin
        valid<=in_valid;
        if (in_valid) begin value<=converted[31:0]; failed<=converted[32]; end
      end
    end
  end
endmodule
