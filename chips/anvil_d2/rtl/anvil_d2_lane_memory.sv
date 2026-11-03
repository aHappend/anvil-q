module anvil_d2_lane_memory #(
  parameter integer CLIENTS=7, HIDDEN_SIZE=2048, INTERMEDIATE_SIZE=10944,
  parameter integer NUM_Q_HEADS=16, KV_LORA_RANK=512,
  parameter integer QK_ROPE_HEAD_DIM=64, MOE_INTERMEDIATE_SIZE=1408,
  parameter integer ROUTED_EXPERTS=64,
  localparam integer SC=CLIENTS>=1 && CLIENTS<=8 ? CLIENTS : 1
) (
  input wire clk, rst_n, flush,
  output wire idle,
  input wire [SC-1:0] s_req_valid, s_req_write,
  output wire [SC-1:0] s_req_ready,
  input wire [SC*4-1:0] s_req_kind,
  input wire [SC*32-1:0] s_req_layer,
  input wire [SC*3-1:0] s_req_proj,
  input wire [SC*32-1:0] s_req_row, s_req_col, s_req_wdata,
  output wire [SC-1:0] s_rsp_valid, s_rsp_error,
  input wire [SC-1:0] s_rsp_ready,
  output wire [SC*32-1:0] s_rsp_rdata,
  output wire [SC-1:0] c_req_valid, c_req_write,
  input wire [SC-1:0] c_req_ready,
  output wire [SC*4-1:0] c_req_kind,
  output wire [SC*32-1:0] c_req_layer,
  output wire [SC*3-1:0] c_req_proj,
  output wire [SC*32-1:0] c_req_row, c_req_col, c_req_wdata,
  input wire [SC-1:0] c_rsp_valid, c_rsp_error,
  output wire [SC-1:0] c_rsp_ready,
  input wire [SC*32-1:0] c_rsp_rdata
);
  generate
    if (CLIENTS<1 || CLIENTS>8 || HIDDEN_SIZE<8 || HIDDEN_SIZE>2048 ||
        (HIDDEN_SIZE & 7)!=0 || INTERMEDIATE_SIZE<8 || INTERMEDIATE_SIZE>11008 ||
        (INTERMEDIATE_SIZE & 7)!=0 || NUM_Q_HEADS<1 || NUM_Q_HEADS>16 ||
        KV_LORA_RANK<1 || KV_LORA_RANK>512 ||
        QK_ROPE_HEAD_DIM<2 || QK_ROPE_HEAD_DIM>64 ||
        (QK_ROPE_HEAD_DIM & 1)!=0 || MOE_INTERMEDIATE_SIZE<8 ||
        MOE_INTERMEDIATE_SIZE>1408 || (MOE_INTERMEDIATE_SIZE & 7)!=0 ||
        ROUTED_EXPERTS<1 || ROUTED_EXPERTS>64) begin: invalid_parameters
      initial $fatal(1,"ANVIL_D2 PARAMETER ERROR: lane scratch geometry");
      assign idle=0;
      assign s_req_ready=0;
      assign s_rsp_valid=0;
      assign s_rsp_error=0;
      assign s_rsp_rdata=0;
      assign c_req_valid=0;
      assign c_req_write=0;
      assign c_req_kind=0;
      assign c_req_layer=0;
      assign c_req_proj=0;
      assign c_req_row=0;
      assign c_req_col=0;
      assign c_req_wdata=0;
      assign c_rsp_ready=0;
    end else begin: scratch
      localparam integer CW=SC==1 ? 1 : $clog2(SC);
      localparam integer QR=NUM_Q_HEADS*KV_LORA_RANK;
      localparam integer QP=NUM_Q_HEADS*QK_ROPE_HEAD_DIM;
      localparam integer F0=INTERMEDIATE_SIZE>MOE_INTERMEDIATE_SIZE+HIDDEN_SIZE ?
        INTERMEDIATE_SIZE : MOE_INTERMEDIATE_SIZE+HIDDEN_SIZE;
      localparam integer FW=F0>ROUTED_EXPERTS ? F0 : ROUTED_EXPERTS;
      localparam integer B3=5*HIDDEN_SIZE, B4=B3+HIDDEN_SIZE;
      localparam integer B5=B4+HIDDEN_SIZE, B6=B5+QR;
      localparam integer B7=B6+QP, B8=B7+QR, WORDS=B8+FW;
      localparam integer AW=$clog2(WORDS);
      reg armed, pending, response_error, response_write;
      reg [CW-1:0] owner, cursor;
      reg [SC-1:0] external_owned;
      reg [SC-1:0] local_address, local_legal, local_ready;
      reg [SC-1:0] response_valids, response_errors;
      reg [SC*32-1:0] response_words;
      (* nomem2reg *) reg [AW-1:0] addresses [0:SC-1];
      reg found;
      reg [CW-1:0] selected;
      reg [31:0] mapped, bound, row_value, col_value;
      reg [3:0] kind_value;
      reg [2:0] proj_value;
      integer n, offset, candidate;
      (* ramstyle="M20K", nomem2reg *) reg [31:0] words [0:WORDS-1];
      reg [31:0] read_word;
      wire enabled=rst_n && armed && !flush;
      wire local_transfer=enabled && found && s_req_valid[selected] && local_ready[selected];
      assign idle=enabled && !pending && external_owned==0;

      always @* begin
        local_address=0;
        local_legal=0;
        mapped=0; bound=0; row_value=0; col_value=0; kind_value=0; proj_value=0;
        for (n=0;n<SC;n=n+1) begin
          row_value=s_req_row[n*32+:32];
          col_value=s_req_col[n*32+:32];
          kind_value=s_req_kind[n*4+:4];
          proj_value=s_req_proj[n*3+:3];
          local_address[n]=kind_value==8 || (kind_value==15 && proj_value==7);
          mapped=0; bound=0;
          if (kind_value==8) begin
            case (row_value)
              0: begin mapped=0; bound=HIDDEN_SIZE; end
              1: begin mapped=HIDDEN_SIZE; bound=HIDDEN_SIZE; end
              7: begin mapped=2*HIDDEN_SIZE; bound=HIDDEN_SIZE; end
              8: begin mapped=3*HIDDEN_SIZE; bound=HIDDEN_SIZE; end
              14: begin mapped=4*HIDDEN_SIZE; bound=HIDDEN_SIZE; end
              default: begin mapped=0; bound=0; end
            endcase
          end else if (kind_value==15 && proj_value==7) begin
            case (row_value)
              3: begin mapped=B3; bound=HIDDEN_SIZE; end
              4: begin mapped=B4; bound=HIDDEN_SIZE; end
              5: begin mapped=B5; bound=QR; end
              6: begin mapped=B6; bound=QP; end
              7: begin mapped=B7; bound=QR; end
              8: begin mapped=B8; bound=FW; end
              default: begin mapped=0; bound=0; end
            endcase
          end
          addresses[n]=AW'(mapped+col_value);
          local_legal[n]=col_value<bound && s_req_proj[n*3+:3]==
            (kind_value==8 ? 3'd0 : 3'd7) &&
            (kind_value!=8 || s_req_layer[n*32+:32]==0);
        end
      end

      always @* begin
        found=0; selected=0; candidate=0; local_ready=0;
        if (enabled && !pending) begin
          for (offset=0;offset<SC;offset=offset+1) begin
            candidate=32'(cursor)+offset;
            if (candidate>=SC) candidate=candidate-SC;
            if (!found && s_req_valid[candidate] && local_address[candidate] &&
                !external_owned[candidate]) begin
              found=1;
              selected=CW'(candidate);
            end
          end
          if (found) local_ready[selected]=1;
        end
        response_valids=0; response_errors=0; response_words=0;
        if (enabled) begin
          for (integer r=0;r<SC;r=r+1) begin
            if (external_owned[r]) begin
              response_valids[r]=c_rsp_valid[r];
              response_errors[r]=c_rsp_valid[r] && c_rsp_error[r];
              response_words[r*32+:32]=c_rsp_valid[r] ? c_rsp_rdata[r*32+:32] : 32'd0;
            end
          end
          if (pending) begin
            response_valids[owner]=1;
            response_errors[owner]=response_error;
            response_words[owner*32+:32]=response_error || response_write ? 32'd0 : read_word;
          end
        end
      end
      assign s_rsp_valid=response_valids;
      assign s_rsp_error=response_errors;
      assign s_rsp_rdata=response_words;

      for (genvar c=0;c<SC;c=c+1) begin: external_port
        wire owned_local=pending && owner==c;
        wire passthrough=enabled && !external_owned[c] && !owned_local && !local_address[c];
        assign s_req_ready[c]=enabled && !external_owned[c] && !owned_local &&
          (local_address[c] ? local_ready[c] : c_req_ready[c]);
        assign c_req_valid[c]=passthrough && s_req_valid[c];
        assign c_req_write[c]=c_req_valid[c] && s_req_write[c];
        assign c_req_kind[c*4+:4]=c_req_valid[c] ? s_req_kind[c*4+:4] : 4'd0;
        assign c_req_layer[c*32+:32]=c_req_valid[c] ? s_req_layer[c*32+:32] : 32'd0;
        assign c_req_proj[c*3+:3]=c_req_valid[c] ? s_req_proj[c*3+:3] : 3'd0;
        assign c_req_row[c*32+:32]=c_req_valid[c] ? s_req_row[c*32+:32] : 32'd0;
        assign c_req_col[c*32+:32]=c_req_valid[c] ? s_req_col[c*32+:32] : 32'd0;
        assign c_req_wdata[c*32+:32]=c_req_valid[c] ? s_req_wdata[c*32+:32] : 32'd0;
        assign c_rsp_ready[c]=enabled && external_owned[c] && s_rsp_ready[c];
      end

      always @(posedge clk) begin
        if (local_transfer && local_legal[selected]) begin
          if (s_req_write[selected]) words[addresses[selected]]<=s_req_wdata[selected*32+:32];
          else read_word<=words[addresses[selected]];
        end
      end
      always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
          armed<=0; pending<=0; response_error<=0; response_write<=0;
          owner<=0; cursor<=0; external_owned<=0;
        end else begin
          armed<=1;
          if (flush) begin
            pending<=0; response_error<=0; response_write<=0;
            owner<=0; cursor<=0; external_owned<=0;
          end else begin
            for (integer c=0;c<SC;c=c+1) begin
              if (c_rsp_valid[c] && c_rsp_ready[c]) external_owned[c]<=0;
              if (c_req_valid[c] && c_req_ready[c]) external_owned[c]<=1;
            end
            if (pending && s_rsp_ready[owner]) pending<=0;
            if (local_transfer) begin
              pending<=1; owner<=selected;
              response_error<=!local_legal[selected];
              response_write<=s_req_write[selected];
              if (selected==SC-1) cursor<=0;
              else cursor<=selected+1'b1;
            end
          end
        end
      end
    end
  endgenerate
endmodule
