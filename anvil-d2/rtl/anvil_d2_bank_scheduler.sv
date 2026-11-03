module anvil_d2_bank_scheduler #(
  parameter integer BANKS=8, CLIENTS=7, QUEUE_DEPTH=3,
  localparam integer SB=(BANKS==1 || BANKS==2 || BANKS==4 || BANKS==8) ? BANKS : 1,
  localparam integer SC=(CLIENTS>=1 && CLIENTS<=32) ? CLIENTS : 1
) (
  input wire clk, rst_n, flush,
  output wire idle, drain_done, fault,
  input wire [SC-1:0] c_req_valid, c_req_write,
  output wire [SC-1:0] c_req_ready,
  input wire [SC*4-1:0] c_req_kind,
  input wire [SC*32-1:0] c_req_layer,
  input wire [SC*3-1:0] c_req_proj,
  input wire [SC*32-1:0] c_req_row, c_req_col, c_req_wdata,
  output wire [SC-1:0] c_rsp_valid, c_rsp_error,
  input wire [SC-1:0] c_rsp_ready,
  output wire [SC*32-1:0] c_rsp_rdata,
  output wire [SB-1:0] mem_req_valid, mem_req_write,
  input wire [SB-1:0] mem_req_ready,
  output wire [SB*4-1:0] mem_req_kind,
  output wire [SB*32-1:0] mem_req_layer,
  output wire [SB*3-1:0] mem_req_proj,
  output wire [SB*32-1:0] mem_req_row, mem_req_col, mem_req_wdata,
  output wire [SB*64-1:0] mem_req_tag,
  input wire [SB-1:0] mem_rsp_valid, mem_rsp_error,
  output wire [SB-1:0] mem_rsp_ready,
  input wire [SB*32-1:0] mem_rsp_rdata,
  input wire [SB*64-1:0] mem_rsp_tag
);
  generate
    if ((BANKS!=1 && BANKS!=2 && BANKS!=4 && BANKS!=8) ||
        CLIENTS<1 || CLIENTS>32 || QUEUE_DEPTH<1 || QUEUE_DEPTH>16) begin: invalid_parameters
      initial $fatal(1,"ANVIL_D2 PARAMETER ERROR: bank scheduler geometry");
      assign idle=0;
      assign drain_done=0;
      assign fault=0;
      assign c_req_ready=0;
      assign c_rsp_valid=0;
      assign c_rsp_error=0;
      assign c_rsp_rdata=0;
      assign mem_req_valid=0;
      assign mem_req_write=0;
      assign mem_req_kind=0;
      assign mem_req_layer=0;
      assign mem_req_proj=0;
      assign mem_req_row=0;
      assign mem_req_col=0;
      assign mem_req_wdata=0;
      assign mem_req_tag=0;
      assign mem_rsp_ready=0;
    end else begin: transport
      localparam integer CW=SC==1 ? 1 : $clog2(SC);
      localparam integer SW=QUEUE_DEPTH==1 ? 1 : $clog2(QUEUE_DEPTH);
      localparam FREE=0, QUEUED=1, ISSUED=2, RETURNED=3;
      reg armed, draining;
      wire [SB-1:0] bank_empty, bank_fault;
      wire [SC-1:0] occupied_by_bank [0:SB-1];
      wire [SC-1:0] ready_by_bank [0:SB-1];
      wire [SC-1:0] valid_by_bank [0:SB-1];
      wire [SC-1:0] error_by_bank [0:SB-1];
      wire [SC*32-1:0] data_by_bank [0:SB-1];
      reg [SC-1:0] occupied, request_ready, response_valid, response_error;
      reg [SC*32-1:0] response_data;
      integer k, ob;
      wire enabled=rst_n && armed;
      wire issue_enabled=enabled && !flush && !draining && !fault;
      assign fault=enabled && |bank_fault;
      assign drain_done=enabled && &bank_empty;
      assign idle=issue_enabled && &bank_empty;
      assign c_req_ready=request_ready;
      assign c_rsp_valid=response_valid;
      assign c_rsp_error=response_error;
      assign c_rsp_rdata=response_data;

      always @* begin
        occupied=0;
        for (ob=0;ob<SB;ob=ob+1) occupied=occupied | occupied_by_bank[ob];
      end

      always @* begin
        request_ready=0;
        response_valid=0;
        response_error=0;
        response_data=0;
        for (k=0;k<SB;k=k+1) begin
          request_ready=request_ready | ready_by_bank[k];
          response_valid=response_valid | valid_by_bank[k];
          response_error=response_error | error_by_bank[k];
          response_data=response_data | data_by_bank[k];
        end
      end

      always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin armed<=0; draining<=0; end
        else begin
          armed<=1;
          if (flush) draining<=1;
          else if (draining && &bank_empty) draining<=0;
        end
      end

      for (genvar b=0;b<SB;b=b+1) begin: bank
        reg [1:0] slot_state [0:QUEUE_DEPTH-1];
        reg [CW-1:0] slot_owner [0:QUEUE_DEPTH-1];
        reg slot_write [0:QUEUE_DEPTH-1];
        reg [3:0] slot_kind [0:QUEUE_DEPTH-1];
        reg [2:0] slot_proj [0:QUEUE_DEPTH-1];
        reg [31:0] slot_layer [0:QUEUE_DEPTH-1];
        reg [31:0] slot_row [0:QUEUE_DEPTH-1];
        reg [31:0] slot_col [0:QUEUE_DEPTH-1];
        reg [31:0] slot_wdata [0:QUEUE_DEPTH-1];
        reg [63:0] slot_tag [0:QUEUE_DEPTH-1];
        reg [31:0] slot_rdata [0:QUEUE_DEPTH-1];
        reg slot_error [0:QUEUE_DEPTH-1];
        reg [CW-1:0] cursor;
        reg [SW-1:0] issue_slot, issue_cursor;
        reg issue_active, failed, tag_exhausted;
        reg [63:0] next_tag;
        reg free_found, queued_found, client_found, response_found, empty;
        reg [SW-1:0] free_slot, queued_slot, response_slot;
        reg [CW-1:0] client;
        reg [SC-1:0] occupied_clients, ready_clients, valid_clients, error_clients;
        reg [SC*32-1:0] result_data;
        integer s, issue_offset, issue_candidate, offset, candidate;
        reg [31:0] bank_hash;
        wire request_transfer=mem_req_valid[b] && mem_req_ready[b];
        wire response_transfer=mem_rsp_valid[b] && mem_rsp_ready[b];
        wire enqueue=issue_enabled && !tag_exhausted && free_found && client_found;

        assign occupied_by_bank[b]=occupied_clients;
        assign ready_by_bank[b]=ready_clients;
        assign valid_by_bank[b]=valid_clients;
        assign error_by_bank[b]=error_clients;
        assign data_by_bank[b]=result_data;
        assign bank_empty[b]=empty && !issue_active;
        assign bank_fault[b]=failed;
        assign mem_req_valid[b]=enabled && !flush && !draining && issue_active;
        assign mem_req_write[b]=mem_req_valid[b] && slot_write[issue_slot];
        assign mem_req_kind[b*4+:4]=mem_req_valid[b] ? slot_kind[issue_slot] : 4'd0;
        assign mem_req_layer[b*32+:32]=mem_req_valid[b] ? slot_layer[issue_slot] : 32'd0;
        assign mem_req_proj[b*3+:3]=mem_req_valid[b] ? slot_proj[issue_slot] : 3'd0;
        assign mem_req_row[b*32+:32]=mem_req_valid[b] ? slot_row[issue_slot] : 32'd0;
        assign mem_req_col[b*32+:32]=mem_req_valid[b] ? slot_col[issue_slot] : 32'd0;
        assign mem_req_wdata[b*32+:32]=mem_req_valid[b] ? slot_wdata[issue_slot] : 32'd0;
        assign mem_req_tag[b*64+:64]=mem_req_valid[b] ? slot_tag[issue_slot] : 64'd0;
        assign mem_rsp_ready[b]=enabled;

        always @* begin
          occupied_clients=0;
          valid_clients=0;
          error_clients=0;
          result_data=0;
          free_found=0;
          queued_found=0;
          response_found=0;
          free_slot=0;
          queued_slot=0;
          response_slot=0;
          issue_candidate=0;
          empty=1;
          for (s=0;s<QUEUE_DEPTH;s=s+1) begin
            if (slot_state[s]!=FREE) begin
              empty=0;
              occupied_clients[slot_owner[s]]=1;
            end
            if (!free_found && slot_state[s]==FREE) begin
              free_found=1;
              free_slot=s;
            end
            if (slot_state[s]==RETURNED && enabled && !flush && !draining) begin
              valid_clients[slot_owner[s]]=1;
              error_clients[slot_owner[s]]=slot_error[s];
              result_data[slot_owner[s]*32+:32]=slot_rdata[s];
            end
            if ((slot_state[s]==ISSUED ||
                (slot_state[s]==QUEUED && issue_active && issue_slot==s &&
                  request_transfer)) && slot_tag[s]==mem_rsp_tag[b*64+:64]) begin
              response_found=1;
              response_slot=s;
            end
          end
          for (issue_offset=0;issue_offset<QUEUE_DEPTH;issue_offset=issue_offset+1) begin
            issue_candidate=issue_cursor+issue_offset;
            if (issue_candidate>=QUEUE_DEPTH) issue_candidate=issue_candidate-QUEUE_DEPTH;
            if (!queued_found && slot_state[issue_candidate]==QUEUED) begin
              queued_found=1;
              queued_slot=issue_candidate;
            end
          end
        end

        always @* begin
          ready_clients=0;
          client_found=0;
          client=0;
          candidate=0;
          bank_hash=0;
          for (offset=0;offset<SC;offset=offset+1) begin
            candidate=cursor+offset;
            if (candidate>=SC) candidate=candidate-SC;
            bank_hash=c_req_col[candidate*32+:32] ^ c_req_row[candidate*32+:32] ^
              c_req_layer[candidate*32+:32] ^ {28'd0,c_req_kind[candidate*4+:4]} ^
              {29'd0,c_req_proj[candidate*3+:3]};
            if (!client_found && !occupied[candidate] && c_req_valid[candidate] &&
                ((bank_hash & (SB-1))==b)) begin
              client_found=1;
              client=candidate;
            end
          end
          if (enqueue) ready_clients[client]=1;
        end

        integer n;
        always @(posedge clk or negedge rst_n) begin
          if (!rst_n) begin
            cursor<=0; issue_slot<=0; issue_cursor<=0; issue_active<=0; failed<=0;
            next_tag<=b+1; tag_exhausted<=0;
            for (n=0;n<QUEUE_DEPTH;n=n+1) begin
              slot_state[n]<=FREE; slot_owner[n]<=0; slot_write[n]<=0;
              slot_kind[n]<=0; slot_proj[n]<=0; slot_layer[n]<=0;
              slot_row[n]<=0; slot_col[n]<=0; slot_wdata[n]<=0;
              slot_tag[n]<=0; slot_rdata[n]<=0; slot_error[n]<=0;
            end
          end else begin
            if (flush || draining) begin
              issue_active<=0;
              if (flush) failed<=tag_exhausted;
              for (n=0;n<QUEUE_DEPTH;n=n+1)
                if (slot_state[n]!=ISSUED) slot_state[n]<=FREE;
            end else begin
              for (n=0;n<QUEUE_DEPTH;n=n+1)
                if (slot_state[n]==RETURNED && valid_clients[slot_owner[n]] &&
                    c_rsp_ready[slot_owner[n]]) slot_state[n]<=FREE;
              if (enqueue) begin
                slot_state[free_slot]<=QUEUED;
                slot_owner[free_slot]<=client;
                slot_write[free_slot]<=c_req_write[client];
                slot_kind[free_slot]<=c_req_kind[client*4+:4];
                slot_proj[free_slot]<=c_req_proj[client*3+:3];
                slot_layer[free_slot]<=c_req_layer[client*32+:32];
                slot_row[free_slot]<=c_req_row[client*32+:32];
                slot_col[free_slot]<=c_req_col[client*32+:32];
                slot_wdata[free_slot]<=c_req_wdata[client*32+:32];
                slot_tag[free_slot]<=next_tag;
                slot_rdata[free_slot]<=0;
                slot_error[free_slot]<=0;
                if (client==SC-1) cursor<=0;
                else cursor<=client+1'b1;
                if (next_tag>64'hffffffffffffffff-SB) tag_exhausted<=1;
                else next_tag<=next_tag+SB;
              end
              if (issue_enabled && !issue_active && queued_found) begin
                issue_slot<=queued_slot;
                issue_active<=1;
              end
              if (request_transfer) begin
                slot_state[issue_slot]<=ISSUED;
                issue_active<=0;
                if (issue_slot==QUEUE_DEPTH-1) issue_cursor<=0;
                else issue_cursor<=issue_slot+1'b1;
              end
              if (tag_exhausted && client_found) failed<=1;
            end
            if (response_transfer) begin
              if (response_found) begin
                if (flush || draining) slot_state[response_slot]<=FREE;
                else begin
                  slot_state[response_slot]<=RETURNED;
                  slot_rdata[response_slot]<=mem_rsp_rdata[b*32+:32];
                  slot_error[response_slot]<=mem_rsp_error[b];
                  if (mem_rsp_error[b]) failed<=1;
                end
              end else if (!flush && !draining) failed<=1;
            end
          end
        end
      end
    end
  endgenerate
endmodule
