module anvil_q3_ht2_private_scratch #(
  parameter HIDDEN_SIZE=2048, INTERMEDIATE_SIZE=11008,
  parameter NUM_KV_HEADS=2, HEAD_DIM=128
) (
  input wire clk, rst_n, flush,
  input wire req_valid,
  output wire req_ready,
  input wire req_write,
  input wire [1:0] req_node,
  input wire [3:0] req_mask,
  input wire [31:0] req_slot, req_index,
  input wire signed [31:0] req_wdata,
  output wire rsp_valid,
  input wire rsp_ready,
  output wire rsp_error,
  output wire [1:0] rsp_node,
  output wire [3:0] rsp_mask,
  output wire [127:0] rsp_rdata,
  output wire idle, fault, drain_done
);
  localparam [127:0] KW=128'(NUM_KV_HEADS)*128'(HEAD_DIM);
  localparam [127:0] WW=10*128'(HIDDEN_SIZE)+3*128'(INTERMEDIATE_SIZE)+2*KW;
  localparam LEGAL=HIDDEN_SIZE>0 && INTERMEDIATE_SIZE>0 && NUM_KV_HEADS>0 &&
    HEAD_DIM>0 && KW<=128'hffffffff && WW>=1 && WW*16<=128'h3e000000;

  generate if (!LEGAL) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q3_HT2 PARAMETER ERROR: private scratch extent");
    assign req_ready=0;
    assign rsp_valid=0;
    assign rsp_error=0;
    assign rsp_node=0;
    assign rsp_mask=0;
    assign rsp_rdata=0;
    assign idle=0;
    assign fault=0;
    assign drain_done=0;
  end else begin: datapath
    localparam WORDS=32'(WW), KD=32'(KW);
    localparam AW=WORDS>1 ? $clog2(WORDS) : 1;
    localparam CLEAR=0, IDLE=1, ADDRESS=2, CHECK=3, ACCESS=4, RESPONSE=5;
    reg [2:0] state;
    reg failed, writing;
    reg [1:0] node;
    reg [3:0] mask;
    reg [31:0] slot, index, data, slot_offset, length;
    reg [32:0] physical;
    reg [AW-1:0] clear_address;
    wire [127:0] bank_data;
    wire [3:0] bank_initialized;
    wire running=rst_n && !flush;
    wire access=running && state==ACCESS && !failed;
    wire clearing=running && state==CLEAR;
    wire read_error=!writing && (bank_initialized&mask)!=mask;
    wire [31:0] safe_slot=slot<=14 ? slot : 32'd0;

    function automatic [31:0] slot_length(input reg [31:0] selected);
      slot_length=selected==3 || selected==4 ? KD :
        selected==9 || selected==10 || selected==11 ? INTERMEDIATE_SIZE : HIDDEN_SIZE;
    endfunction
    function automatic [31:0] slot_base(input reg [31:0] selected);
      case (selected)
        0: slot_base=0;
        1: slot_base=HIDDEN_SIZE;
        2: slot_base=2*HIDDEN_SIZE;
        3: slot_base=3*HIDDEN_SIZE;
        4: slot_base=3*HIDDEN_SIZE+KD;
        5: slot_base=3*HIDDEN_SIZE+2*KD;
        6: slot_base=4*HIDDEN_SIZE+2*KD;
        7: slot_base=5*HIDDEN_SIZE+2*KD;
        8: slot_base=6*HIDDEN_SIZE+2*KD;
        9: slot_base=7*HIDDEN_SIZE+2*KD;
        10: slot_base=7*HIDDEN_SIZE+2*KD+INTERMEDIATE_SIZE;
        11: slot_base=7*HIDDEN_SIZE+2*KD+2*INTERMEDIATE_SIZE;
        12: slot_base=7*HIDDEN_SIZE+2*KD+3*INTERMEDIATE_SIZE;
        13: slot_base=8*HIDDEN_SIZE+2*KD+3*INTERMEDIATE_SIZE;
        default: slot_base=9*HIDDEN_SIZE+2*KD+3*INTERMEDIATE_SIZE;
      endcase
    endfunction
    wire [31:0] selected_base=slot_base(safe_slot);
    wire [31:0] selected_length=slot_length(safe_slot);

    for (genvar b=0;b<4;b=b+1) begin: token_bank
      (* ramstyle="M20K", nomem2reg *) reg [31:0] words [0:WORDS-1];
      (* ramstyle="M20K", nomem2reg *) reg initialized [0:WORDS-1];
      reg [31:0] read_data;
      reg read_initialized;
      assign bank_data[b*32+:32]=read_data;
      assign bank_initialized[b]=read_initialized;
      always @(posedge clk) begin
        if (clearing) initialized[clear_address]<=0;
        if (access && mask[b]) begin
          if (writing && node==b) begin
            words[physical[AW-1:0]]<=data;
            initialized[physical[AW-1:0]]<=1;
          end else if (!writing) begin
            read_data<=words[physical[AW-1:0]];
            read_initialized<=initialized[physical[AW-1:0]];
          end
        end
      end
      assign rsp_rdata[b*32+:32]=rsp_valid && !rsp_error && !writing && mask[b] ?
        bank_data[b*32+:32] : 32'd0;
    end

    assign req_ready=running && state==IDLE;
    assign rsp_valid=running && state==RESPONSE;
    assign rsp_error=rsp_valid && (failed || read_error);
    assign rsp_node=rsp_valid ? node : 2'd0;
    assign rsp_mask=rsp_valid ? mask : 4'd0;
    assign idle=req_ready;
    assign fault=running && state==RESPONSE && (failed || read_error);
    assign drain_done=running && (state==IDLE || state==RESPONSE);

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        state<=CLEAR; failed<=0; writing<=0; node<=0; mask<=0;
        slot<=0; index<=0; data<=0; slot_offset<=0; length<=0;
        physical<=0; clear_address<=0;
      end else if (flush) begin
        state<=CLEAR; failed<=0; writing<=0; node<=0; mask<=0;
        slot<=0; index<=0; data<=0; slot_offset<=0; length<=0;
        physical<=0; clear_address<=0;
      end else case (state)
        CLEAR: begin
          if (clear_address==WORDS-1) state<=IDLE;
          else clear_address<=clear_address+1'b1;
        end
        IDLE: if (req_valid && req_ready) begin
          writing<=req_write; node<=req_node; mask<=req_mask;
          slot<=req_slot; index<=req_index; data<=req_wdata;
          failed<=req_mask==0 || (req_write && req_mask!=(4'b0001<<req_node));
          state<=ADDRESS;
        end
        ADDRESS: begin slot_offset<=selected_base; length<=selected_length; state<=CHECK; end
        CHECK: begin
          physical<={1'b0,slot_offset}+{1'b0,index};
          if (failed || slot>14 || index>=length ||
              {1'b0,slot_offset}+{1'b0,index}>=WORDS) begin
            failed<=1; state<=RESPONSE;
          end else state<=ACCESS;
        end
        ACCESS: state<=RESPONSE;
        RESPONSE: if (rsp_ready) begin
          failed<=0; mask<=0; data<=0; state<=IDLE;
        end
        default: begin failed<=1; state<=RESPONSE; end
      endcase
    end
  end endgenerate
endmodule
