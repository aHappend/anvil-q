module anvil_q3_bank_scheduler #(
  parameter BANKS=8, CLIENTS=BANKS+1, QUEUE_DEPTH=3,
  localparam SB=(BANKS==1 || BANKS==2 || BANKS==4 || BANKS==8) ? BANKS : 1,
  localparam SC=CLIENTS>0 && CLIENTS<=32 ? CLIENTS : 1,
  localparam SQ=QUEUE_DEPTH>=1 && QUEUE_DEPTH<=16 ? QUEUE_DEPTH : 1
) (
  input wire clk, rst_n, flush,
  output wire idle,
  output reg drain_done, fault,
  input wire [SC-1:0] c_req_valid,
  output reg [SC-1:0] c_req_ready,
  input wire [SC-1:0] c_req_write,
  input wire [SC*4-1:0] c_req_kind,
  input wire [SC*32-1:0] c_req_layer,
  input wire [SC*3-1:0] c_req_proj,
  input wire [SC*32-1:0] c_req_row, c_req_col, c_req_wdata,
  output reg [SC-1:0] c_rsp_valid,
  input wire [SC-1:0] c_rsp_ready,
  output reg [SC*32-1:0] c_rsp_rdata,
  output reg [SC-1:0] c_rsp_error,
  output reg [SB-1:0] mem_req_valid,
  input wire [SB-1:0] mem_req_ready,
  output reg [SB-1:0] mem_req_write,
  output reg [SB*4-1:0] mem_req_kind,
  output reg [SB*32-1:0] mem_req_layer,
  output reg [SB*3-1:0] mem_req_proj,
  output reg [SB*32-1:0] mem_req_row, mem_req_col, mem_req_wdata,
  output reg [SB*64-1:0] mem_req_tag,
  input wire [SB-1:0] mem_rsp_valid, mem_rsp_error,
  output reg [SB-1:0] mem_rsp_ready,
  input wire [SB*32-1:0] mem_rsp_rdata,
  input wire [SB*64-1:0] mem_rsp_tag
);
  localparam SLOTS=SB*SQ;
  localparam FREE=0, QUEUED=1, HELD=2, SENT=3, RETURNED=4;
  localparam LEGAL=(BANKS==1 || BANKS==2 || BANKS==4 || BANKS==8) &&
    CLIENTS>=1 && CLIENTS<=32 && QUEUE_DEPTH>=1 && QUEUE_DEPTH<=16 &&
    SB==BANKS && SC==CLIENTS && SQ==QUEUE_DEPTH;
  generate if (!LEGAL) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q3 PARAMETER ERROR: scheduler geometry");
  end endgenerate

  localparam SIW=SLOTS>1 ? $clog2(SLOTS) : 1;
  localparam CIW=SC>1 ? $clog2(SC) : 1;
  localparam BIW=SB>1 ? $clog2(SB) : 1;
  localparam QIW=SQ>1 ? $clog2(SQ) : 1;
  localparam QCW=$clog2(SQ+1);
  localparam CCW=$clog2(SLOTS+1);
  localparam CT=2**$clog2(SC), QT=2**$clog2(SQ);
  (* mem2reg *) reg [2:0] stage [0:SLOTS-1];
  (* mem2reg *) reg [CIW-1:0] owner [0:SLOTS-1];
  (* mem2reg *) reg [63:0] tag [0:SLOTS-1];
  (* mem2reg *) reg wr [0:SLOTS-1], response_error [0:SLOTS-1];
  (* mem2reg *) reg [3:0] kind [0:SLOTS-1];
  (* mem2reg *) reg [2:0] proj [0:SLOTS-1];
  (* mem2reg *) reg [31:0] layer [0:SLOTS-1], row [0:SLOTS-1];
  (* mem2reg *) reg [31:0] col [0:SLOTS-1], wdata [0:SLOTS-1], rdata [0:SLOTS-1];
  reg [SB-1:0] holding;
  reg [SIW-1:0] held_slot [0:SB-1];
  (* mem2reg *) reg [SIW-1:0] successor [0:SLOTS-1];
  reg [SIW-1:0] client_head [0:SC-1], client_tail [0:SC-1];
  reg [CCW-1:0] client_count [0:SC-1];
  (* mem2reg *) reg [SIW-1:0] dispatch_queue [0:SLOTS-1];
  reg [QIW-1:0] queue_read [0:SB-1], queue_write [0:SB-1];
  reg [QCW-1:0] queue_count [0:SB-1];
  reg [63:0] next_tag;
  reg wrap_pending, draining;
  reg [CIW-1:0] round_robin;
  wire [SLOTS-1:0] live, retiring, dispatching, issuing, returning, append_link;
  wire [SC-1:0] retire_client;
  wire [SB-1:0] dequeue, enqueue, bad_bank_response;
  wire [SIW-1:0] dispatch_slot [0:SB-1];
  wire signed [SIW:0] response_slot [0:SB-1];
  wire [SIW-1:0] free_slot [0:SB-1];
  wire [SB-1:0] free_valid;
  wire request_valid [1:2*CT-1];
  wire [CIW:0] request_rank [1:2*CT-1];
  wire [CIW-1:0] request_client [1:2*CT-1];
  wire [SIW-1:0] request_slot [1:2*CT-1];
  wire [BIW-1:0] request_bank [1:2*CT-1];
  wire [135:0] request_data [1:2*CT-1];
  wire accept_enable=rst_n && !flush && !draining && !wrap_pending;
  wire ingress_valid=accept_enable && request_valid[1];
  wire [CIW-1:0] ingress=request_client[1];
  wire [SIW-1:0] ingress_slot=request_slot[1];
  wire [BIW-1:0] ingress_bank=request_bank[1];
  wire bad_response=rst_n && |bad_bank_response;
  integer i;

  assign idle=rst_n && !flush && !draining && !(|live);
  genvar b, s, c, n;
  generate
    for (c=0;c<SC;c=c+1) begin: clients
      reg response_valid, response_failed;
      reg [31:0] response_data;
      wire responding=rst_n && !flush && !draining &&
        response_valid;
      always @* begin
        c_rsp_valid[c]=responding;
        c_rsp_error[c]=responding && response_failed;
        c_rsp_rdata[c*32+:32]=responding ? response_data : 32'd0;
        c_req_ready[c]=ingress_valid && ingress==c;
      end
      assign retire_client[c]=responding && c_rsp_ready[c];
      always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
          response_valid<=0; response_failed<=0; response_data<=0;
        end else if (flush || bad_response || draining) begin
          response_valid<=0;
        end else if (retire_client[c]) begin
          response_valid<=0;
        end else if (!response_valid && client_count[c]!=0 &&
                     stage[client_head[c]]==RETURNED) begin
          response_valid<=1;
          response_failed<=response_error[client_head[c]];
          response_data<=rdata[client_head[c]];
        end
      end
    end
    for (s=0;s<SLOTS;s=s+1) begin: slots
      localparam BANK=s/SQ;
      wire [SC-1:0] retire_match, append_match;
      for (c=0;c<SC;c=c+1) begin: client_match
        assign retire_match[c]=retire_client[c] && client_head[c]==s;
        assign append_match[c]=ingress_valid && ingress==c &&
          client_count[c]!=0 && !(client_count[c]==1 && retire_client[c]) &&
          client_tail[c]==s;
      end
      assign retiring[s]=|retire_match;
      assign append_link[s]=|append_match;
      assign dispatching[s]=dequeue[BANK] && dispatch_slot[BANK]==s;
      assign issuing[s]=mem_req_valid[BANK] && mem_req_ready[BANK] &&
        held_slot[BANK]==s;
      assign returning[s]=mem_rsp_valid[BANK] && response_slot[BANK]==s;
      assign live[s]=stage[s]!=FREE;
    end
    for (b=0;b<SB;b=b+1) begin: banks
      wire available [1:2*QT-1];
      wire [SIW-1:0] available_slot [1:2*QT-1];
      wire matched [1:2*QT-1];
      wire [SIW-1:0] matched_slot [1:2*QT-1];
      for (s=0;s<QT;s=s+1) begin: leaves
        if (s<SQ) begin: real_slot
          localparam INDEX=b*SQ+s;
          assign available[QT+s]=stage[INDEX]==FREE || retiring[INDEX];
          assign available_slot[QT+s]=SIW'(INDEX);
          assign matched[QT+s]=
            (stage[INDEX]==SENT ||
             (stage[INDEX]==HELD && holding[b] && held_slot[b]==INDEX &&
              !draining && mem_req_ready[b])) &&
            tag[INDEX]==mem_rsp_tag[b*64+:64];
          assign matched_slot[QT+s]=SIW'(INDEX);
        end else begin: padding
          assign available[QT+s]=0;
          assign available_slot[QT+s]=0;
          assign matched[QT+s]=0;
          assign matched_slot[QT+s]=0;
        end
      end
      for (n=1;n<QT;n=n+1) begin: selection
        assign available[n]=available[2*n] || available[2*n+1];
        assign available_slot[n]=available[2*n] ?
          available_slot[2*n] : available_slot[2*n+1];
        assign matched[n]=matched[2*n] || matched[2*n+1];
        assign matched_slot[n]=matched[2*n] ?
          matched_slot[2*n] : matched_slot[2*n+1];
      end
      assign free_valid[b]=available[1];
      assign free_slot[b]=available_slot[1];
      assign response_slot[b]=matched[1] ? $signed({1'b0,matched_slot[1]}) :
        { (SIW+1){1'b1} };
      assign bad_bank_response[b]=mem_rsp_valid[b] && !matched[1];
      assign dispatch_slot[b]=dispatch_queue[b*SQ+queue_read[b]];
      assign dequeue[b]=!holding[b] && queue_count[b]!=0;
      assign enqueue[b]=ingress_valid && ingress_bank==b;
      always @* begin
        mem_rsp_ready[b]=rst_n;
        mem_req_valid[b]=rst_n && holding[b] && !draining;
        mem_req_write[b]=mem_req_valid[b] && wr[held_slot[b]];
        mem_req_kind[b*4+:4]=mem_req_valid[b] ? kind[held_slot[b]] : 4'd0;
        mem_req_layer[b*32+:32]=mem_req_valid[b] ? layer[held_slot[b]] : 32'd0;
        mem_req_proj[b*3+:3]=mem_req_valid[b] ? proj[held_slot[b]] : 3'd0;
        mem_req_row[b*32+:32]=mem_req_valid[b] ? row[held_slot[b]] : 32'd0;
        mem_req_col[b*32+:32]=mem_req_valid[b] ? col[held_slot[b]] : 32'd0;
        mem_req_wdata[b*32+:32]=mem_req_valid[b] ? wdata[held_slot[b]] : 32'd0;
        mem_req_tag[b*64+:64]=mem_req_valid[b] ? tag[held_slot[b]] : 64'd0;
      end
    end
    for (c=0;c<CT;c=c+1) begin: ingress_leaves
      if (c<SC) begin: real_client
        // Only the low bank-address bits affect the power-of-two route.
        wire [BIW-1:0] route=SB==1 ? BIW'(0) :
          BIW'(c_req_kind[c*4+:4])+BIW'(c_req_layer[c*32+:32])+
          BIW'(c_req_proj[c*3+:3])+BIW'(c_req_row[c*32+:32])+
          BIW'(c_req_col[c*32+:32]);
        assign request_valid[CT+c]=c_req_valid[c] && free_valid[route];
        assign request_rank[CT+c]=c>=round_robin ?
          (CIW+1)'(c)-{1'b0,round_robin} :
          (CIW+1)'(c+SC)-{1'b0,round_robin};
        assign request_client[CT+c]=CIW'(c);
        assign request_slot[CT+c]=free_slot[route];
        assign request_bank[CT+c]=route;
        assign request_data[CT+c]={c_req_write[c],c_req_kind[c*4+:4],
          c_req_layer[c*32+:32],c_req_proj[c*3+:3],c_req_row[c*32+:32],
          c_req_col[c*32+:32],c_req_wdata[c*32+:32]};
      end else begin: padding
        assign request_valid[CT+c]=0;
        assign request_rank[CT+c]=0;
        assign request_client[CT+c]=0;
        assign request_slot[CT+c]=0;
        assign request_bank[CT+c]=0;
        assign request_data[CT+c]=0;
      end
    end
    for (n=1;n<CT;n=n+1) begin: ingress_selection
      wire left_wins=request_valid[2*n] && (!request_valid[2*n+1] ||
        request_rank[2*n]<=request_rank[2*n+1]);
      assign request_valid[n]=request_valid[2*n] || request_valid[2*n+1];
      assign request_rank[n]=left_wins ? request_rank[2*n] : request_rank[2*n+1];
      assign request_client[n]=left_wins ? request_client[2*n] : request_client[2*n+1];
      assign request_slot[n]=left_wins ? request_slot[2*n] : request_slot[2*n+1];
      assign request_bank[n]=left_wins ? request_bank[2*n] : request_bank[2*n+1];
      assign request_data[n]=left_wins ? request_data[2*n] : request_data[2*n+1];
    end
  endgenerate

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      holding<=0; next_tag<=0; wrap_pending<=0; draining<=0;
      round_robin<=0; drain_done<=0; fault<=0;
    end else begin
      drain_done<=0;
      fault<=0;
      if (flush || bad_response) begin
        draining<=1;
        holding<=0;
        if (bad_response) fault<=1;
      end else if (draining) begin
        if (!(|live)) begin
          draining<=0;
          drain_done<=1;
        end
      end else begin
        if (wrap_pending && !(|live)) begin
          next_tag<=0;
          wrap_pending<=0;
        end
        if (ingress_valid) begin
          if (next_tag==64'hffffffffffffffff) wrap_pending<=1;
          else next_tag<=next_tag+1'b1;
          if (ingress==SC-1) round_robin<=0;
          else round_robin<=ingress+1'b1;
        end
      end
    end
    for (i=0;i<SLOTS;i=i+1) begin
      if (!rst_n) begin
        stage[i]<=FREE; owner[i]<=0; tag[i]<=0; wr[i]<=0;
        response_error[i]<=0; kind[i]<=0; proj[i]<=0; layer[i]<=0;
        row[i]<=0; col[i]<=0; wdata[i]<=0; rdata[i]<=0; successor[i]<=0;
        dispatch_queue[i]<=0;
      end else if (flush || bad_response) begin
        if (returning[i]) stage[i]<=FREE;
        else if (stage[i]==SENT || issuing[i]) stage[i]<=SENT;
        else stage[i]<=FREE;
      end else if (draining) begin
        if (returning[i]) stage[i]<=FREE;
      end else begin
        if (returning[i]) stage[i]<=RETURNED;
        else if (issuing[i]) stage[i]<=SENT;
        else if (dispatching[i]) stage[i]<=HELD;
        else if (ingress_valid && ingress_slot==i) stage[i]<=QUEUED;
        else if (retiring[i]) stage[i]<=FREE;
        if (ingress_valid && ingress_slot==i) begin
          owner[i]<=ingress; tag[i]<=next_tag;
          {wr[i],kind[i],layer[i],proj[i],row[i],col[i],wdata[i]}<=request_data[1];
        end
        if (append_link[i]) successor[i]<=ingress_slot;
      end
    end
    for (i=0;i<SC;i=i+1) begin
      if (!rst_n) begin
        client_head[i]<=0; client_tail[i]<=0; client_count[i]<=0;
      end else if (flush || bad_response) begin
        client_count[i]<=0;
      end else if (!draining) begin
        case ({(ingress_valid && ingress==i),retire_client[i]})
          2'b10: client_count[i]<=client_count[i]+1'b1;
          2'b01: client_count[i]<=client_count[i]-1'b1;
          default: begin end
        endcase
        if (retire_client[i] && client_count[i]>1)
          client_head[i]<=successor[client_head[i]];
        if (ingress_valid && ingress==i) begin
          client_tail[i]<=ingress_slot;
          if (client_count[i]==0 || (client_count[i]==1 && retire_client[i]))
            client_head[i]<=ingress_slot;
        end
      end
    end
    for (i=0;i<SB;i=i+1) begin
      if (!rst_n) begin
        held_slot[i]<=0; queue_read[i]<=0; queue_write[i]<=0; queue_count[i]<=0;
      end else if (flush || bad_response) begin
        queue_read[i]<=0; queue_write[i]<=0; queue_count[i]<=0;
      end else if (!draining) begin
        case ({enqueue[i],dequeue[i]})
          2'b10: queue_count[i]<=queue_count[i]+1'b1;
          2'b01: queue_count[i]<=queue_count[i]-1'b1;
          default: begin end
        endcase
        if (enqueue[i]) begin
          dispatch_queue[i*SQ+queue_write[i]]<=ingress_slot;
          if (queue_write[i]==SQ-1) queue_write[i]<=0;
          else queue_write[i]<=queue_write[i]+1'b1;
        end
        if (dequeue[i]) begin
          holding[i]<=1;
          held_slot[i]<=dispatch_slot[i];
          if (queue_read[i]==SQ-1) queue_read[i]<=0;
          else queue_read[i]<=queue_read[i]+1'b1;
        end
        if (mem_req_valid[i] && mem_req_ready[i]) begin
          holding[i]<=0;
        end
        if (mem_rsp_valid[i] && response_slot[i]>=0) begin
          rdata[response_slot[i]]<=mem_rsp_rdata[i*32+:32];
          response_error[response_slot[i]]<=mem_rsp_error[i];
        end
      end
    end
  end
endmodule
