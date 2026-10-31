module anvil_q2_ht2_ddr_fabric #(
  parameter READ_OUTSTANDING=8
) (
  input wire clk, rst_n, annul, ddr_ready, ddr_fault,
  input wire weight_valid,
  output wire weight_ready,
  input wire [32:0] weight_address,
  input wire [6:0] weight_beats,
  output wire fill_valid, fill_error, fill_last,
  input wire fill_ready,
  output wire [511:0] fill_data,
  input wire [2:0] c_req_valid, c_req_write,
  output wire [2:0] c_req_ready,
  input wire [98:0] c_req_address,
  input wire [1535:0] c_req_wdata,
  input wire [191:0] c_req_be,
  output wire [2:0] c_rsp_valid, c_rsp_error,
  input wire [2:0] c_rsp_ready,
  output wire [1535:0] c_rsp_data,
  output wire idle, fault,
  output wire [63:0] accepted_read_beats, accepted_write_beats,
  output wire [32:0] avm_address,
  output wire avm_read, avm_write,
  output wire [511:0] avm_writedata,
  output wire [63:0] avm_byteenable,
  output wire [4:0] avm_burstcount,
  input wire avm_waitrequest,
  input wire [511:0] avm_readdata,
  input wire avm_readdatavalid, avm_writeresponsevalid,
  input wire [1:0] avm_response
);
  localparam LEGAL=READ_OUTSTANDING>=1 && READ_OUTSTANDING<=16;
  generate if (!LEGAL) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q2_HT2 PARAMETER ERROR: native DDR outstanding count");
    assign weight_ready=0; assign fill_valid=0; assign fill_error=0;
    assign fill_last=0; assign fill_data=0; assign c_req_ready=0;
    assign c_rsp_valid=0; assign c_rsp_error=0; assign c_rsp_data=0;
    assign idle=0; assign fault=0; assign accepted_read_beats=0;
    assign accepted_write_beats=0; assign avm_address=0;
    assign avm_read=0; assign avm_write=0; assign avm_writedata=0;
    assign avm_byteenable=0; assign avm_burstcount=0;
  end else begin: implementation
    localparam [1:0] IDLE=0, SEND=1, WAIT_RESPONSE=2, ERROR_RESPONSE=3;
    reg [1:0] state;
    reg [32:0] address;
    reg [6:0] remaining;
    reg malformed_pulse;
    reg [63:0] read_beats, write_beats;
    wire [3:0] request_ready, response_valid, response_error;
    wire [2047:0] response_data;
    wire [3:0] response_ready={c_rsp_ready,
      (rst_n && state==WAIT_RESPONSE && fill_ready)};
    wire [33:0] requested_end={1'b0,weight_address}+
      {21'd0,weight_beats,6'd0};
    wire malformed=(|weight_address[5:0]) || weight_beats==0 ||
      requested_end>34'h200000000;
    wire parent_idle, parent_fault;

    // A captured burst remains owned through annul, including its unissued suffix.
    anvil_q2_ht_ddr_fabric #(
      .CLIENTS(4),.READ_OUTSTANDING(READ_OUTSTANDING)
    ) arbitration (
      .clk(clk),.rst_n(rst_n),.ddr_ready(ddr_ready),.ddr_fault(ddr_fault),
      .p_address(33'd0),.p_read(1'b0),.p_burstcount(5'd0),
      .p_waitrequest(),.p_readdata(),.p_readdatavalid(),.p_response(),
      .k_address(33'd0),.k_read(1'b0),.k_burstcount(5'd0),
      .k_waitrequest(),.k_readdata(),.k_readdatavalid(),.k_response(),
      .c_req_valid({(c_req_valid & {3{!annul}}),
        (rst_n && state==SEND)}),
      .c_req_write({c_req_write,1'b0}),.c_req_ready(request_ready),
      .c_req_addr({c_req_address,address}),
      .c_req_wdata({c_req_wdata,512'd0}),
      .c_req_be({c_req_be,64'hffffffffffffffff}),
      .c_rsp_valid(response_valid),.c_rsp_ready(response_ready),
      .c_rsp_rdata(response_data),.c_rsp_error(response_error),
      .idle(parent_idle),.fault(parent_fault),
      .avm_address(avm_address),.avm_read(avm_read),.avm_write(avm_write),
      .avm_writedata(avm_writedata),.avm_byteenable(avm_byteenable),
      .avm_burstcount(avm_burstcount),.avm_waitrequest(avm_waitrequest),
      .avm_readdata(avm_readdata),.avm_readdatavalid(avm_readdatavalid),
      .avm_writeresponsevalid(avm_writeresponsevalid),.avm_response(avm_response)
    );

    assign weight_ready=rst_n && !annul && state==IDLE && ddr_ready;
    assign fill_valid=rst_n &&
      ((state==WAIT_RESPONSE && response_valid[0]) || state==ERROR_RESPONSE);
    assign fill_error=fill_valid && (state==ERROR_RESPONSE || response_error[0]);
    assign fill_last=fill_valid && (state==ERROR_RESPONSE || remaining==1);
    assign fill_data=fill_valid && !fill_error ? response_data[511:0] : 512'd0;
    assign c_req_ready=rst_n && !annul ? request_ready[3:1] : 3'd0;
    assign c_rsp_valid=response_valid[3:1];
    assign c_rsp_error=response_error[3:1];
    assign c_rsp_data=response_data[2047:512];
    assign idle=rst_n && state==IDLE && parent_idle;
    assign fault=rst_n && (parent_fault || malformed_pulse);
    assign accepted_read_beats=rst_n ? read_beats : 64'd0;
    assign accepted_write_beats=rst_n ? write_beats : 64'd0;

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        state<=IDLE; address<=0; remaining<=0; malformed_pulse<=0;
        read_beats<=0; write_beats<=0;
      end else begin
        malformed_pulse<=0;
        if (avm_read && !avm_waitrequest)
          read_beats<=read_beats+{59'd0,avm_burstcount};
        if (avm_write && !avm_waitrequest)
          write_beats<=write_beats+{59'd0,avm_burstcount};
        case (state)
          IDLE: if (weight_valid && weight_ready) begin
            address<=weight_address; remaining<=weight_beats;
            if (malformed) begin state<=ERROR_RESPONSE; malformed_pulse<=1; end
            else state<=SEND;
          end
          SEND: if (request_ready[0]) state<=WAIT_RESPONSE;
          WAIT_RESPONSE: if (response_valid[0] && fill_ready) begin
            if (remaining==1) begin state<=IDLE; remaining<=0; end
            else begin
              address<=address+33'd64; remaining<=remaining-7'd1; state<=SEND;
            end
          end
          ERROR_RESPONSE: if (fill_ready) state<=IDLE;
          default: begin state<=ERROR_RESPONSE; malformed_pulse<=1; end
        endcase
      end
    end
  end endgenerate
endmodule
