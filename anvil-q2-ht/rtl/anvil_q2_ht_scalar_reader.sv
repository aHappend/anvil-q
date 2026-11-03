module anvil_q2_ht_scalar_reader (
  input wire clk, rst_n, invalidate,
  input wire cmd_valid,
  output wire cmd_ready,
  input wire [32:0] cmd_address,
  input wire cmd_word32,
  output wire rsp_valid,
  input wire rsp_ready,
  output wire [31:0] rsp_data,
  output wire rsp_error,
  output wire idle,
  output wire mem_req_valid,
  input wire mem_req_ready,
  output wire [32:0] mem_req_addr,
  input wire mem_rsp_valid,
  output wire mem_rsp_ready,
  input wire [511:0] mem_rsp_rdata,
  input wire mem_rsp_error
);
  localparam [2:0] IDLE=0, REQUEST=1, WAIT_RESPONSE=2, EXTRACT=3,
    RESPONSE=4;
  reg [2:0] state;
  reg canceled, failed, word32, target, replacement;
  reg [1:0] cached;
  reg [32:0] address;
  reg [26:0] cached_line [0:1];
  reg [511:0] line_data [0:1];
  reg [31:0] result;
  wire available=rst_n && !invalidate && !canceled;
  wire hit0=cached[0] && cmd_address[32:6]==cached_line[0];
  wire hit1=cached[1] && cmd_address[32:6]==cached_line[1];
  wire hit=hit0 || hit1;
  assign cmd_ready=available && state==IDLE;
  assign rsp_valid=available && state==RESPONSE;
  assign rsp_data=rsp_valid ? result : 32'd0;
  assign rsp_error=rsp_valid && failed;
  assign idle=available && state==IDLE;
  // An invalidation annuls use of a result, not a previously held command.
  assign mem_req_valid=rst_n && state==REQUEST;
  assign mem_req_addr=mem_req_valid ? {address[32:6],6'd0} : 33'd0;
  assign mem_rsp_ready=rst_n && state==WAIT_RESPONSE;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; canceled<=0; failed<=0; word32<=0; cached<=0;
      address<=0; target<=0; replacement<=0; result<=0;
      cached_line[0]<=0; cached_line[1]<=0; line_data[0]<=0; line_data[1]<=0;
    end else if (invalidate || canceled) begin
      cached<=0;
      if (state==REQUEST) begin
        canceled<=1;
        if (mem_req_ready) state<=WAIT_RESPONSE;
      end else if (state==WAIT_RESPONSE) begin
        if (mem_rsp_valid) begin state<=IDLE; canceled<=0; end
        else canceled<=1;
      end else begin state<=IDLE; canceled<=0; end
    end else case (state)
      IDLE: if (cmd_valid && cmd_ready) begin
        address<=cmd_address;
        word32<=cmd_word32;
        target<=hit ? !hit0 : replacement;
        failed<=0; result<=0;
        if (cmd_address[0] || (cmd_word32 && cmd_address[1])) begin
          failed<=1; state<=RESPONSE;
        end else if (hit) state<=EXTRACT;
        else state<=REQUEST;
      end
      REQUEST: if (mem_req_ready) state<=WAIT_RESPONSE;
      WAIT_RESPONSE: if (mem_rsp_valid) begin
        if (mem_rsp_error) begin
          cached<=0; failed<=1; state<=RESPONSE;
        end else begin
          line_data[target]<=mem_rsp_rdata;
          cached_line[target]<=address[32:6];
          cached[target]<=1; replacement<=!target; state<=EXTRACT;
        end
      end
      EXTRACT: begin
        if (word32) result<=line_data[target][address[5:2]*32+:32];
        else result<={16'd0,line_data[target][address[5:1]*16+:16]};
        state<=RESPONSE;
      end
      RESPONSE: if (rsp_ready) state<=IDLE;
      default: begin cached<=0; failed<=1; result<=0; state<=RESPONSE; end
    endcase
  end
endmodule
