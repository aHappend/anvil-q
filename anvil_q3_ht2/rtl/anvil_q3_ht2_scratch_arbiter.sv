module anvil_q3_ht2_scratch_arbiter #(
  parameter CLIENTS=5,
  localparam NC=CLIENTS>=1 && CLIENTS<=16 ? CLIENTS : 1,
  localparam CW=NC>1 ? $clog2(NC) : 1
) (
  input wire clk, rst_n, flush,
  input wire [NC-1:0] c_req_valid, c_req_write,
  output wire [NC-1:0] c_req_ready,
  input wire [NC*2-1:0] c_req_node,
  input wire [NC*4-1:0] c_req_mask,
  input wire [NC*32-1:0] c_req_slot, c_req_index, c_req_wdata,
  output wire [NC-1:0] c_rsp_valid, c_rsp_error,
  input wire [NC-1:0] c_rsp_ready,
  output wire [NC*2-1:0] c_rsp_node,
  output wire [NC*4-1:0] c_rsp_mask,
  output wire [NC*128-1:0] c_rsp_rdata,
  output wire req_valid,
  input wire req_ready,
  output wire req_write,
  output wire [1:0] req_node,
  output wire [3:0] req_mask,
  output wire [31:0] req_slot, req_index, req_wdata,
  input wire rsp_valid, rsp_error,
  output wire rsp_ready,
  input wire [1:0] rsp_node,
  input wire [3:0] rsp_mask,
  input wire [127:0] rsp_rdata,
  output wire idle, drain_done, fault
);
  generate if (CLIENTS!=NC) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q3_HT2 PARAMETER ERROR: scratch arbiter clients");
    assign c_req_ready=0; assign c_rsp_valid=0; assign c_rsp_error=0;
    assign c_rsp_node=0; assign c_rsp_mask=0; assign c_rsp_rdata=0;
    assign req_valid=0; assign req_write=0; assign req_node=0; assign req_mask=0;
    assign req_slot=0; assign req_index=0; assign req_wdata=0; assign rsp_ready=0;
    assign idle=0; assign drain_done=0; assign fault=0;
  end else begin: datapath
    localparam IDLE=0, OFFER=1, RETURN=2, CANCEL_RESPONSE=3;
    reg [1:0] state;
    reg failed, writing;
    reg [CW-1:0] pointer, owner;
    reg [1:0] node;
    reg [3:0] mask;
    reg [31:0] slot, index, data;
    integer selected, candidate;
    wire running=rst_n && !flush && !failed;
    wire request_fire=req_valid && req_ready;
    wire known=state==RETURN || request_fire;
    wire response_bad=rsp_valid && (!known || rsp_node!=node || rsp_mask!=mask);
    wire response_fire=rsp_valid && rsp_ready;

    always @* begin
      selected=-1; candidate=0;
      for (integer offset=0;offset<NC;offset=offset+1) begin
        candidate=32'(pointer)+offset;
        if (candidate>=NC) candidate=candidate-NC;
        if (selected<0 && c_req_valid[candidate]) selected=candidate;
      end
    end
    for (genvar c=0;c<NC;c=c+1) begin: clients
      assign c_req_ready[c]=running && state==IDLE && selected==c && !rsp_valid;
      // Cancellation is drained through the original producer, not swallowed.
      assign c_rsp_valid[c]=rst_n && !flush && owner==c &&
        ((rsp_valid && known) || state==CANCEL_RESPONSE);
      assign c_rsp_error[c]=c_rsp_valid[c] &&
        (state==CANCEL_RESPONSE || rsp_error || response_bad);
      assign c_rsp_node[c*2+:2]=!c_rsp_valid[c] ? 2'd0 :
        state==CANCEL_RESPONSE ? node : rsp_node;
      assign c_rsp_mask[c*4+:4]=!c_rsp_valid[c] ? 4'd0 :
        state==CANCEL_RESPONSE ? mask : rsp_mask;
      assign c_rsp_rdata[c*128+:128]=c_rsp_valid[c] && !c_rsp_error[c] ?
        rsp_rdata : 128'd0;
    end
    assign req_valid=running && state==OFFER;
    assign req_write=req_valid && writing;
    assign req_node=req_valid ? node : 2'd0;
    assign req_mask=req_valid ? mask : 4'd0;
    assign req_slot=req_valid ? slot : 32'd0;
    assign req_index=req_valid ? index : 32'd0;
    assign req_wdata=req_write ? data : 32'd0;
    assign rsp_ready=rst_n && !flush &&
      ((known && c_rsp_ready[owner]) || (failed && !known));
    assign idle=running && state==IDLE && !rsp_valid;
    assign drain_done=rst_n && !flush && state==IDLE && !rsp_valid;
    assign fault=rst_n && !flush && failed;

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        state<=IDLE; failed<=0; writing<=0; pointer<=0; owner<=0;
        node<=0; mask<=0; slot<=0; index<=0; data<=0;
      end else begin
        if (response_fire) state<=IDLE;
        if (flush) begin
          failed<=0; pointer<=0;
          if (state==OFFER || state==CANCEL_RESPONSE) state<=CANCEL_RESPONSE;
          else if (state!=RETURN) begin
            state<=IDLE; writing<=0; owner<=0; node<=0;
            mask<=0; slot<=0; index<=0; data<=0;
          end
        end else if (response_bad) failed<=1;
        else case (state)
          IDLE: if (running && selected>=0 && c_req_ready[selected]) begin
            owner<=CW'(selected); writing<=c_req_write[selected];
            node<=c_req_node[selected*2+:2]; mask<=c_req_mask[selected*4+:4];
            slot<=c_req_slot[selected*32+:32]; index<=c_req_index[selected*32+:32];
            data<=c_req_wdata[selected*32+:32]; state<=OFFER;
          end
          OFFER: if (request_fire) begin
            if (response_fire) state<=IDLE;
            else state<=RETURN;
          end
          RETURN: if (response_fire) begin
            pointer<=owner==NC-1 ? {CW{1'b0}} : owner+1'b1;
            writing<=0; node<=0; mask<=0; slot<=0; index<=0; data<=0;
            state<=IDLE;
          end
          CANCEL_RESPONSE: if (c_rsp_ready[owner]) begin
            writing<=0; node<=0; mask<=0; slot<=0; index<=0; data<=0;
            state<=IDLE;
          end
          default: begin failed<=1; state<=IDLE; end
        endcase
      end
    end
  end endgenerate
endmodule
