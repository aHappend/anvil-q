module anvil_qn1_bank_scheduler #(
  parameter BANKS=8, QUEUE_DEPTH=3
) (
  input wire clk, rst_n, cancel,
  input wire req_valid,
  output wire req_ready,
  input wire req_write,
  input wire [3:0] req_kind,
  input wire [31:0] req_layer, req_row, req_col, req_wdata, req_tag,
  input wire [2:0] req_proj,
  output wire rsp_valid,
  input wire rsp_ready,
  output wire [31:0] rsp_data, rsp_tag,
  output wire rsp_error, fault, drained,
  output wire [(BANKS>0 ? BANKS : 1)-1:0] mem_req_valid,
  input wire [(BANKS>0 ? BANKS : 1)-1:0] mem_req_ready,
  output wire [(BANKS>0 ? BANKS : 1)-1:0] mem_req_write,
  output wire [(BANKS>0 ? BANKS : 1)*4-1:0] mem_req_kind,
  output wire [(BANKS>0 ? BANKS : 1)*32-1:0] mem_req_layer, mem_req_row,
    mem_req_col, mem_req_wdata,
  output wire [(BANKS>0 ? BANKS : 1)*3-1:0] mem_req_proj,
  output wire [(BANKS>0 ? BANKS : 1)*64-1:0] mem_req_tag,
  input wire [(BANKS>0 ? BANKS : 1)-1:0] mem_rsp_valid, mem_rsp_error,
  output wire [(BANKS>0 ? BANKS : 1)-1:0] mem_rsp_ready,
  input wire [(BANKS>0 ? BANKS : 1)*32-1:0] mem_rsp_rdata,
  input wire [(BANKS>0 ? BANKS : 1)*64-1:0] mem_rsp_tag
);
  import anvil_qn1_pkg::*;
  generate if ((BANKS==1 || BANKS==2 || BANKS==4 || BANKS==8) &&
      QUEUE_DEPTH>=1 && QUEUE_DEPTH<=16) begin: legal
    localparam SLOTS=BANKS*QUEUE_DEPTH;
    localparam FREE=0, PENDING=1, WAITING=2, COMPLETE=3;
    reg [1:0] state [0:SLOTS-1];
    reg [3:0] kind [0:SLOTS-1];
    reg [2:0] projection [0:SLOTS-1];
    reg [31:0] layer [0:SLOTS-1], row [0:SLOTS-1], col [0:SLOTS-1];
    reg [31:0] wdata [0:SLOTS-1], client_tag [0:SLOTS-1], rdata [0:SLOTS-1];
    reg [63:0] tag [0:SLOTS-1];
    reg [SLOTS-1:0] writing, failed;
    // Host reset annuls ownership, but must not reuse a tag from before reset.
    reg [63:0] serial=64'd1;
    reg [2:0] next_bank;
    reg draining, fault_reg, output_valid, output_error;
    reg [31:0] output_data, output_tag;
    reg have_free, have_complete, any_owned, transaction_fault;
    integer free_slot, complete_slot;
    integer selected [0:BANKS-1], matched [0:BANKS-1];
    integer waiting_slot [0:BANKS-1];
    reg [BANKS-1:0] request_owned, waiting_request;
    reg [6:0] request_slot [0:BANKS-1];
    reg [BANKS-1:0] have_request, have_match;
    integer b, s, offset, candidate;
    always @* begin
      have_free=0; free_slot=0; have_complete=0; complete_slot=0;
      any_owned=0; transaction_fault=0;
      have_request=request_owned; have_match=0; waiting_request=0;
      for (b=0;b<BANKS;b=b+1) begin
        selected[b]=32'(request_slot[b]); matched[b]=0; waiting_slot[b]=0;
        for (s=0;s<QUEUE_DEPTH;s=s+1) begin
          if (!waiting_request[b] && state[b*QUEUE_DEPTH+s]==PENDING) begin
            waiting_slot[b]=b*QUEUE_DEPTH+s; waiting_request[b]=1;
          end
        end
      end
      for (offset=0;offset<BANKS;offset=offset+1) begin
        candidate=32'(next_bank)+offset;
        if (candidate>=BANKS) candidate=candidate-BANKS;
        for (s=0;s<QUEUE_DEPTH;s=s+1)
          if (!have_free && state[candidate*QUEUE_DEPTH+s]==FREE) begin
            have_free=1; free_slot=candidate*QUEUE_DEPTH+s;
          end
      end
      for (s=0;s<SLOTS;s=s+1) begin
        if (state[s]!=FREE) any_owned=1;
        if (!have_complete && state[s]==COMPLETE) begin
          have_complete=1; complete_slot=s;
        end
      end
      for (b=0;b<BANKS;b=b+1) begin
        for (s=0;s<QUEUE_DEPTH;s=s+1) begin
          if (tag[b*QUEUE_DEPTH+s]==mem_rsp_tag[b*64+:64] &&
              (state[b*QUEUE_DEPTH+s]==WAITING ||
               (!draining && !cancel && have_request[b] &&
                selected[b]==b*QUEUE_DEPTH+s && mem_req_ready[b]))) begin
            matched[b]=b*QUEUE_DEPTH+s; have_match[b]=1;
          end
        end
        if (rst_n && mem_rsp_valid[b] &&
            (!have_match[b] || mem_rsp_error[b])) transaction_fault=1;
      end
    end
    assign req_ready=rst_n && !cancel && !draining && !transaction_fault &&
      have_free && !(&serial);
    assign rsp_valid=rst_n && !cancel && !draining && !transaction_fault && output_valid;
    assign rsp_data=rsp_valid ? output_data : 32'd0;
    assign rsp_tag=rsp_valid ? output_tag : 32'd0;
    assign rsp_error=rsp_valid && output_error;
    assign fault=rst_n && (fault_reg || transaction_fault);
    assign drained=rst_n && !any_owned && !output_valid;
    genvar bank;
    for (bank=0;bank<BANKS;bank=bank+1) begin: banks
      wire issuing=rst_n && !cancel && !draining && !transaction_fault &&
        have_request[bank];
      assign mem_req_valid[bank]=issuing;
      assign mem_req_write[bank]=issuing && writing[selected[bank]];
      assign mem_req_kind[bank*4+:4]=issuing ? kind[selected[bank]] : 4'd0;
      assign mem_req_layer[bank*32+:32]=issuing ? layer[selected[bank]] : 32'd0;
      assign mem_req_proj[bank*3+:3]=issuing ? projection[selected[bank]] : 3'd0;
      assign mem_req_row[bank*32+:32]=issuing ? row[selected[bank]] : 32'd0;
      assign mem_req_col[bank*32+:32]=issuing ? col[selected[bank]] : 32'd0;
      assign mem_req_wdata[bank*32+:32]=issuing ? wdata[selected[bank]] : 32'd0;
      assign mem_req_tag[bank*64+:64]=issuing ? tag[selected[bank]] : 64'd0;
      assign mem_rsp_ready[bank]=rst_n;
    end
    integer index, bank_index;
    always @(posedge clk) begin
      if (rst_n && req_valid && req_ready) serial<=event_add64(serial,3'd1);
    end
    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        next_bank<=0; draining<=0; fault_reg<=0;
        output_valid<=0; output_error<=0; output_data<=0; output_tag<=0;
        writing<=0; failed<=0;
        request_owned<=0;
        for (bank_index=0;bank_index<BANKS;bank_index=bank_index+1)
          request_slot[bank_index]<=0;
        for (index=0;index<SLOTS;index=index+1) begin
          state[index]<=FREE; kind[index]<=0; projection[index]<=0;
          layer[index]<=0; row[index]<=0; col[index]<=0; wdata[index]<=0;
          client_tag[index]<=0; rdata[index]<=0; tag[index]<=0;
        end
      end else begin
        fault_reg<=0;
        if (cancel || transaction_fault || (req_valid && (&serial))) begin
          draining<=1; output_valid<=0; request_owned<=0;
          if (transaction_fault || (req_valid && (&serial))) fault_reg<=1;
          for (index=0;index<SLOTS;index=index+1)
            if (state[index]!=WAITING) state[index]<=FREE;
        end else if (draining) begin
          output_valid<=0;
          if (!any_owned) draining<=0;
        end else begin
          if (output_valid && rsp_ready) output_valid<=0;
          if ((!output_valid || rsp_ready) && have_complete) begin
            output_valid<=1; output_data<=rdata[complete_slot];
            output_tag<=client_tag[complete_slot]; output_error<=failed[complete_slot];
            state[complete_slot]<=FREE;
          end
          if (req_valid && req_ready) begin
            state[free_slot]<=PENDING; writing[free_slot]<=req_write;
            kind[free_slot]<=req_kind; projection[free_slot]<=req_proj;
            layer[free_slot]<=req_layer; row[free_slot]<=req_row;
            col[free_slot]<=req_col; wdata[free_slot]<=req_wdata;
            client_tag[free_slot]<=req_tag; tag[free_slot]<=serial;
            if (next_bank==BANKS-1) next_bank<=0;
            else next_bank<=next_bank+1'b1;
          end
          for (bank_index=0;bank_index<BANKS;bank_index=bank_index+1)
            if (mem_req_valid[bank_index] && mem_req_ready[bank_index]) begin
              state[selected[bank_index]]<=WAITING;
              request_owned[bank_index]<=0;
            end else if (!request_owned[bank_index] && waiting_request[bank_index]) begin
              request_owned[bank_index]<=1;
              request_slot[bank_index]<=7'(waiting_slot[bank_index]);
            end
        end
        for (bank_index=0;bank_index<BANKS;bank_index=bank_index+1) begin
          if (mem_rsp_valid[bank_index] && have_match[bank_index]) begin
            if (cancel || draining || transaction_fault)
              state[matched[bank_index]]<=FREE;
            else begin
              state[matched[bank_index]]<=COMPLETE;
              rdata[matched[bank_index]]<=mem_rsp_rdata[bank_index*32+:32];
              failed[matched[bank_index]]<=mem_rsp_error[bank_index];
            end
          end
        end
      end
    end
  end else begin: invalid
    initial $fatal(1,"ANVIL_QN1 PARAMETER ERROR: memory scheduler geometry");
    assign req_ready=0; assign rsp_valid=0; assign rsp_data=0;
    assign rsp_tag=0; assign rsp_error=0; assign fault=0; assign drained=0;
    assign mem_req_valid=0; assign mem_req_write=0; assign mem_req_kind=0;
    assign mem_req_layer=0; assign mem_req_proj=0; assign mem_req_row=0;
    assign mem_req_col=0; assign mem_req_wdata=0; assign mem_req_tag=0;
    assign mem_rsp_ready=0;
  end endgenerate
endmodule
