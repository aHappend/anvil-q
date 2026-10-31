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
    reg [32:0] addresses [0:7];
    reg [6:0] remaining [0:7], unissued [0:7];
    reg [7:0] invalid_request;
    reg [2:0] tail, issue_head, delivery_head;
    reg [3:0] owners, to_issue;
    reg [8:0] reserved;
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
    wire [32:0] address=addresses[issue_head];
    wire [6:0] issue_remaining=unissued[issue_head];
    wire [6:0] page_beats=7'd64-{1'b0,address[11:6]};
    wire [6:0] bounded_beats=issue_remaining>16 ? 7'd16 : issue_remaining;
    wire [4:0] burst_length=bounded_beats>page_beats ?
      page_beats[4:0] : bounded_beats[4:0];
    wire stream_request=rst_n && to_issue!=0 && !invalid_request[issue_head];
    wire stream_accept=stream_request && !stream_wait;
    wire issue_complete=rst_n && to_issue!=0 &&
      (invalid_request[issue_head] ||
        (stream_accept && issue_remaining=={2'd0,burst_length}));
    wire store_return=stream_valid && pending_returns!=0;
    wire take_stored=rst_n && owners!=0 &&
      !invalid_request[delivery_head] && stored!=0 &&
      (!output_valid || fill_ready);
    wire [33:0] requested_end={1'b0,weight_address}+
      {21'd0,weight_beats,6'd0};
    wire malformed=(|weight_address[5:0]) || weight_beats==0 ||
      requested_end>34'h200000000;
    wire accept_request=weight_valid && weight_ready;
    wire deliver=fill_valid && fill_ready;
    wire deliver_data=deliver && !invalid_request[delivery_head];
    wire deliver_complete=deliver && fill_last;
    wire [8:0] reservation=malformed ? 9'd0 : {2'd0,weight_beats};
    wire parent_idle, parent_fault;
    integer q;

    // Reserve every accepted owner's complete return footprint before issue.
    always @(posedge clk) begin
      if (rst_n && store_return)
        returned[write_pointer]<={stream_response!=0,stream_data};
      if (take_stored) output_data<=returned[read_pointer];
    end

    // Annul drains accepted owners, including their captured unissued suffixes.
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

    assign weight_ready=rst_n && !annul && owners<8 && ddr_ready &&
      reserved+reservation<=9'd128;
    assign fill_valid=rst_n && owners!=0 &&
      (invalid_request[delivery_head] || output_valid);
    assign fill_error=fill_valid && (invalid_request[delivery_head] || output_data[512]);
    assign fill_last=fill_valid &&
      (invalid_request[delivery_head] || remaining[delivery_head]==1);
    assign fill_data=fill_valid && !fill_error ? output_data[511:0] : 512'd0;
    assign c_req_ready=rst_n && !annul ? request_ready : 3'd0;
    assign c_rsp_valid=response_valid;
    assign c_rsp_error=response_error;
    assign c_rsp_data=response_data;
    assign idle=rst_n && owners==0 && to_issue==0 && pending_returns==0 &&
      stored==0 && !output_valid && parent_idle;
    assign fault=rst_n && (parent_fault || malformed_pulse);
    assign accepted_read_beats=rst_n ? read_beats : 64'd0;
    assign accepted_write_beats=rst_n ? write_beats : 64'd0;

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        tail<=0; issue_head<=0; delivery_head<=0; owners<=0; to_issue<=0;
        reserved<=0; invalid_request<=0;
        for (q=0;q<8;q=q+1) begin addresses[q]<=0; remaining[q]<=0; unissued[q]<=0; end
        pending_returns<=0; stored<=0; read_pointer<=0; write_pointer<=0;
        output_valid<=0; malformed_pulse<=0;
        read_beats<=0; write_beats<=0;
      end else begin
        malformed_pulse<=0;
        if (stream_valid && !store_return) malformed_pulse<=1;
        if (stream_accept) begin
          addresses[issue_head]<=address+{22'd0,burst_length,6'd0};
          unissued[issue_head]<=issue_remaining-{2'd0,burst_length};
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
        end else if (deliver_data) output_valid<=0;
        case ({store_return,take_stored})
          2'b10: stored<=stored+8'd1;
          2'b01: stored<=stored-8'd1;
          default: begin end
        endcase
        if (avm_read && !avm_waitrequest)
          read_beats<=read_beats+{59'd0,avm_burstcount};
        if (avm_write && !avm_waitrequest)
          write_beats<=write_beats+{59'd0,avm_burstcount};
        if (accept_request) begin
          addresses[tail]<=weight_address;
          remaining[tail]<=weight_beats; unissued[tail]<=weight_beats;
          invalid_request[tail]<=malformed; tail<=tail+3'd1;
          if (malformed) malformed_pulse<=1;
        end
        if (issue_complete) issue_head<=issue_head+3'd1;
        if (deliver_complete) delivery_head<=delivery_head+3'd1;
        else if (deliver_data)
          remaining[delivery_head]<=remaining[delivery_head]-7'd1;
        case ({accept_request,deliver_complete})
          2'b10: owners<=owners+4'd1;
          2'b01: owners<=owners-4'd1;
          default: begin end
        endcase
        case ({accept_request,issue_complete})
          2'b10: to_issue<=to_issue+4'd1;
          2'b01: to_issue<=to_issue-4'd1;
          default: begin end
        endcase
        case ({accept_request,deliver_data})
          2'b10: reserved<=reserved+reservation;
          2'b01: reserved<=reserved-9'd1;
          2'b11: reserved<=reserved+reservation-9'd1;
          default: begin end
        endcase
      end
    end
  end endgenerate
endmodule
