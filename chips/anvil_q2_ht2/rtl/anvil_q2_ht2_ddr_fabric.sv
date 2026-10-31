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
    localparam [1:0] IDLE=0, ACTIVE=1, ERROR_RESPONSE=2;
    reg [1:0] state;
    reg [32:0] address;
    reg [6:0] remaining, unissued;
    reg [7:0] pending_returns, stored;
    reg [6:0] read_pointer, write_pointer;
    reg output_valid;
    reg [512:0] output_data;
    (* ramstyle="M20K", nomem2reg *) reg [512:0] returned [0:127];
    reg malformed_pulse;
    reg [63:0] read_beats, write_beats;
    wire [2:0] request_ready, response_valid, response_error;
    wire [1535:0] response_data;
    wire stream_wait, stream_valid;
    wire [511:0] stream_data;
    wire [1:0] stream_response;
    wire [6:0] page_beats=7'd64-{1'b0,address[11:6]};
    wire [6:0] bounded_beats=unissued>16 ? 7'd16 : unissued;
    wire [4:0] burst_length=bounded_beats>page_beats ?
      page_beats[4:0] : bounded_beats[4:0];
    wire stream_request=rst_n && state==ACTIVE && unissued!=0;
    wire stream_accept=stream_request && !stream_wait;
    wire store_return=stream_valid && state==ACTIVE && pending_returns!=0;
    wire take_stored=rst_n && state==ACTIVE && stored!=0 &&
      (!output_valid || fill_ready);
    wire [33:0] requested_end={1'b0,weight_address}+
      {21'd0,weight_beats,6'd0};
    wire malformed=(|weight_address[5:0]) || weight_beats==0 ||
      requested_end>34'h200000000;
    wire parent_idle, parent_fault;

    // Reserve room for the entire owner before issuing unbackpressurable bursts.
    always @(posedge clk) begin
      if (rst_n && store_return)
        returned[write_pointer]<={stream_response!=0,stream_data};
      if (take_stored) output_data<=returned[read_pointer];
    end

    // Annul preserves the captured owner's unissued suffix and return reservation.
    anvil_q2_ht_ddr_fabric #(
      .CLIENTS(3),.READ_OUTSTANDING(READ_OUTSTANDING)
    ) arbitration (
      .clk(clk),.rst_n(rst_n),.ddr_ready(ddr_ready),.ddr_fault(ddr_fault),
      .p_address(address),.p_read(stream_request),.p_burstcount(burst_length),
      .p_waitrequest(stream_wait),.p_readdata(stream_data),
      .p_readdatavalid(stream_valid),.p_response(stream_response),
      .k_address(33'd0),.k_read(1'b0),.k_burstcount(5'd0),
      .k_waitrequest(),.k_readdata(),.k_readdatavalid(),.k_response(),
      .c_req_valid(c_req_valid & {3{!annul}}),
      .c_req_write(c_req_write),.c_req_ready(request_ready),
      .c_req_addr(c_req_address),
      .c_req_wdata(c_req_wdata),
      .c_req_be(c_req_be),
      .c_rsp_valid(response_valid),.c_rsp_ready(c_rsp_ready),
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
      ((state==ACTIVE && output_valid) || state==ERROR_RESPONSE);
    assign fill_error=fill_valid && (state==ERROR_RESPONSE || output_data[512]);
    assign fill_last=fill_valid && (state==ERROR_RESPONSE || remaining==1);
    assign fill_data=fill_valid && !fill_error ? output_data[511:0] : 512'd0;
    assign c_req_ready=rst_n && !annul ? request_ready : 3'd0;
    assign c_rsp_valid=response_valid;
    assign c_rsp_error=response_error;
    assign c_rsp_data=response_data;
    assign idle=rst_n && state==IDLE && parent_idle;
    assign fault=rst_n && (parent_fault || malformed_pulse);
    assign accepted_read_beats=rst_n ? read_beats : 64'd0;
    assign accepted_write_beats=rst_n ? write_beats : 64'd0;

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        state<=IDLE; address<=0; remaining<=0; unissued<=0;
        pending_returns<=0; stored<=0; read_pointer<=0; write_pointer<=0;
        output_valid<=0; malformed_pulse<=0;
        read_beats<=0; write_beats<=0;
      end else begin
        malformed_pulse<=0;
        if (stream_valid && !store_return) malformed_pulse<=1;
        if (stream_accept) begin
          address<=address+{22'd0,burst_length,6'd0};
          unissued<=unissued-{2'd0,burst_length};
        end
        case ({stream_accept,store_return})
          2'b10: pending_returns<=pending_returns+{3'd0,burst_length};
          2'b01: pending_returns<=pending_returns-8'd1;
          2'b11: pending_returns<=pending_returns+{3'd0,burst_length}-8'd1;
          default: begin end
        endcase
        if (store_return) write_pointer<=write_pointer+7'd1;
        if (take_stored) begin
          read_pointer<=read_pointer+7'd1; output_valid<=1;
        end else if (state==ACTIVE && output_valid && fill_ready) output_valid<=0;
        case ({store_return,take_stored})
          2'b10: stored<=stored+8'd1;
          2'b01: stored<=stored-8'd1;
          default: begin end
        endcase
        if (avm_read && !avm_waitrequest)
          read_beats<=read_beats+{59'd0,avm_burstcount};
        if (avm_write && !avm_waitrequest)
          write_beats<=write_beats+{59'd0,avm_burstcount};
        case (state)
          IDLE: if (weight_valid && weight_ready) begin
            address<=weight_address; remaining<=weight_beats; unissued<=weight_beats;
            pending_returns<=0; stored<=0; read_pointer<=0; write_pointer<=0;
            output_valid<=0;
            if (malformed) begin state<=ERROR_RESPONSE; malformed_pulse<=1; end
            else state<=ACTIVE;
          end
          ACTIVE: if (fill_valid && fill_ready) begin
            if (remaining==1) begin state<=IDLE; remaining<=0; end
            else remaining<=remaining-7'd1;
          end
          ERROR_RESPONSE: if (fill_ready) state<=IDLE;
          default: begin state<=ERROR_RESPONSE; malformed_pulse<=1; end
        endcase
      end
    end
  end endgenerate
endmodule
