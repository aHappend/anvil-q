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

  (* mem2reg *) reg [2:0] stage [0:SLOTS-1];
  (* mem2reg *) reg [31:0] owner [0:SLOTS-1];
  (* mem2reg *) reg [63:0] tag [0:SLOTS-1];
  (* mem2reg *) reg wr [0:SLOTS-1], response_error [0:SLOTS-1];
  (* mem2reg *) reg [3:0] kind [0:SLOTS-1];
  (* mem2reg *) reg [2:0] proj [0:SLOTS-1];
  (* mem2reg *) reg [31:0] layer [0:SLOTS-1], row [0:SLOTS-1];
  (* mem2reg *) reg [31:0] col [0:SLOTS-1], wdata [0:SLOTS-1], rdata [0:SLOTS-1];
  reg [SB-1:0] holding;
  reg [31:0] held_slot [0:SB-1];
  reg [63:0] next_tag;
  reg wrap_pending, draining;
  reg [31:0] round_robin;
  integer free_slot [0:SB-1], dispatch_slot [0:SB-1], response_slot [0:SB-1];
  integer retire_slot [0:SC-1];
  integer live_count, ingress, ingress_slot, candidate, route;
  integer b, s, c, offset, i, j;
  reg bad_response;
  reg [34:0] address_hash;

  assign idle=rst_n && !flush && !draining && live_count==0;
  always @* begin
    live_count=0;
    for (b=0;b<SB;b=b+1) begin
      free_slot[b]=-1;
      dispatch_slot[b]=-1;
      response_slot[b]=-1;
      for (s=0;s<SQ;s=s+1) begin
        if (stage[b*SQ+s]==FREE && free_slot[b]<0) free_slot[b]=b*SQ+s;
        if (stage[b*SQ+s]!=FREE) live_count=live_count+1;
        if (stage[b*SQ+s]==QUEUED) begin
          if (dispatch_slot[b]<0) dispatch_slot[b]=b*SQ+s;
          else if (tag[b*SQ+s]<tag[dispatch_slot[b]]) dispatch_slot[b]=b*SQ+s;
        end
        if (stage[b*SQ+s]==SENT && tag[b*SQ+s]==mem_rsp_tag[b*64+:64])
          response_slot[b]=b*SQ+s;
      end
      if (holding[b] && !draining && mem_req_ready[b] &&
          tag[held_slot[b]]==mem_rsp_tag[b*64+:64])
        response_slot[b]=held_slot[b];
    end

    c_rsp_valid=0;
    c_rsp_error=0;
    c_rsp_rdata=0;
    for (c=0;c<SC;c=c+1) begin
      retire_slot[c]=-1;
      for (s=0;s<SLOTS;s=s+1) begin
        if (stage[s]!=FREE && owner[s]==c) begin
          if (retire_slot[c]<0) retire_slot[c]=s;
          else if (tag[s]<tag[retire_slot[c]]) retire_slot[c]=s;
        end
      end

      if (rst_n && !flush && !draining && retire_slot[c]>=0) begin
        if (stage[retire_slot[c]]==RETURNED) begin
          c_rsp_valid[c]=1;
          c_rsp_error[c]=response_error[retire_slot[c]];
          c_rsp_rdata[c*32+:32]=rdata[retire_slot[c]];
        end
      end
    end

    for (b=0;b<SB;b=b+1)
      for (s=0;s<SQ;s=s+1)
        if (free_slot[b]<0 && stage[b*SQ+s]==RETURNED &&
            c_rsp_valid[owner[b*SQ+s]] && c_rsp_ready[owner[b*SQ+s]] &&
            retire_slot[owner[b*SQ+s]]==b*SQ+s)
          free_slot[b]=b*SQ+s;
    ingress=-1;
    ingress_slot=-1;
    candidate=0;
    route=0;
    address_hash=0;
    c_req_ready=0;
    if (rst_n && !flush && !draining && !wrap_pending) begin
      for (offset=0;offset<SC;offset=offset+1) begin
        candidate=round_robin+offset;
        if (candidate>=SC) candidate=candidate-SC;
        address_hash={31'd0,c_req_kind[candidate*4+:4]}+
          {3'd0,c_req_layer[candidate*32+:32]}+
          {32'd0,c_req_proj[candidate*3+:3]}+
          {3'd0,c_req_row[candidate*32+:32]}+
          {3'd0,c_req_col[candidate*32+:32]};
        route=address_hash & (SB-1);
        if (ingress<0 && c_req_valid[candidate] && free_slot[route]>=0) begin
          ingress=candidate;
          ingress_slot=free_slot[route];
        end
      end
      if (ingress>=0) c_req_ready[ingress]=1;
    end

    mem_req_valid=0; mem_req_write=0; mem_req_kind=0; mem_req_layer=0;
    mem_req_proj=0; mem_req_row=0; mem_req_col=0; mem_req_wdata=0;
    mem_req_tag=0; mem_rsp_ready=0; bad_response=0;
    if (rst_n) begin
      for (b=0;b<SB;b=b+1) begin
        mem_rsp_ready[b]=1;
        if (mem_rsp_valid[b] && response_slot[b]<0) bad_response=1;
        if (holding[b] && !draining) begin
          mem_req_valid[b]=1;
          mem_req_write[b]=wr[held_slot[b]];
          mem_req_kind[b*4+:4]=kind[held_slot[b]];
          mem_req_layer[b*32+:32]=layer[held_slot[b]];
          mem_req_proj[b*3+:3]=proj[held_slot[b]];
          mem_req_row[b*32+:32]=row[held_slot[b]];
          mem_req_col[b*32+:32]=col[held_slot[b]];
          mem_req_wdata[b*32+:32]=wdata[held_slot[b]];
          mem_req_tag[b*64+:64]=tag[held_slot[b]];
        end
      end
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      holding<=0; next_tag<=0; wrap_pending<=0; draining<=0;
      round_robin<=0; drain_done<=0; fault<=0;
      for (i=0;i<SB;i=i+1) held_slot[i]<=0;
      for (i=0;i<SLOTS;i=i+1) begin
        stage[i]<=FREE; owner[i]<=0; tag[i]<=0; wr[i]<=0;
        response_error[i]<=0; kind[i]<=0; proj[i]<=0; layer[i]<=0;
        row[i]<=0; col[i]<=0; wdata[i]<=0; rdata[i]<=0;
      end
    end else begin
      drain_done<=0;
      fault<=0;
      if (flush || bad_response) begin
        draining<=1;
        holding<=0;
        if (bad_response) fault<=1;
        for (i=0;i<SLOTS;i=i+1) begin
          if (stage[i]!=SENT) begin
            stage[i]<=FREE;
            // A held request can transfer on the edge entering drain.
            for (j=0;j<SB;j=j+1)
              if (mem_req_valid[j] && mem_req_ready[j] && held_slot[j]==i)
                stage[i]<=SENT;
          end
        end
        for (i=0;i<SB;i=i+1)
          if (mem_rsp_valid[i] && response_slot[i]>=0) stage[response_slot[i]]<=FREE;
      end else if (draining) begin
        for (i=0;i<SB;i=i+1)
          if (mem_rsp_valid[i] && response_slot[i]>=0) stage[response_slot[i]]<=FREE;
        if (live_count==0) begin
          draining<=0;
          drain_done<=1;
        end
      end else begin
        if (wrap_pending && live_count==0) begin
          next_tag<=0;
          wrap_pending<=0;
        end
        if (ingress>=0) begin
          stage[ingress_slot]<=QUEUED;
          owner[ingress_slot]<=ingress;
          tag[ingress_slot]<=next_tag;
          wr[ingress_slot]<=c_req_write[ingress];
          kind[ingress_slot]<=c_req_kind[ingress*4+:4];
          layer[ingress_slot]<=c_req_layer[ingress*32+:32];
          proj[ingress_slot]<=c_req_proj[ingress*3+:3];
          row[ingress_slot]<=c_req_row[ingress*32+:32];
          col[ingress_slot]<=c_req_col[ingress*32+:32];
          wdata[ingress_slot]<=c_req_wdata[ingress*32+:32];
          if (next_tag==64'hffffffffffffffff) wrap_pending<=1;
          else next_tag<=next_tag+1'b1;
          if (ingress==SC-1) round_robin<=0;
          else round_robin<=ingress+1;
        end
        for (i=0;i<SB;i=i+1) begin
          if (!holding[i] && dispatch_slot[i]>=0) begin
            holding[i]<=1;
            held_slot[i]<=dispatch_slot[i];
            stage[dispatch_slot[i]]<=HELD;
          end
          if (mem_req_valid[i] && mem_req_ready[i]) begin
            holding[i]<=0;
            stage[held_slot[i]]<=SENT;
          end
        end
        for (i=0;i<SC;i=i+1)
          if (c_rsp_valid[i] && c_rsp_ready[i] && retire_slot[i]!=ingress_slot)
            stage[retire_slot[i]]<=FREE;
        for (i=0;i<SB;i=i+1)
          if (mem_rsp_valid[i] && response_slot[i]>=0) begin
            stage[response_slot[i]]<=RETURNED;
            rdata[response_slot[i]]<=mem_rsp_rdata[i*32+:32];
            response_error[response_slot[i]]<=mem_rsp_error[i];
          end
      end
    end
  end
endmodule
