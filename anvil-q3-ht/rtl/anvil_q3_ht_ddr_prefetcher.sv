module anvil_q3_ht_ddr_prefetcher #(
  parameter QUEUE_DEPTH=3, BURST_BEATS=16, OUTSTANDING=4, META_WIDTH=160,
  parameter RETURN_BEATS=OUTSTANDING*BURST_BEATS,
  localparam QD=(QUEUE_DEPTH>=1 && QUEUE_DEPTH<=16) ? QUEUE_DEPTH : 1,
  localparam OB=(OUTSTANDING>=1 && OUTSTANDING<=16) ? OUTSTANDING : 1,
  localparam RB=(RETURN_BEATS>=1 && RETURN_BEATS<=4096) ? RETURN_BEATS : 1,
  localparam MW=META_WIDTH>=1 ? META_WIDTH : 1,
  localparam QAW=QD>1 ? $clog2(QD) : 1,
  localparam BAW=OB>1 ? $clog2(OB) : 1,
  localparam RAW=RB>1 ? $clog2(RB) : 1
) (
  input wire clk, rst_n, flush,
  input wire cmd_valid,
  output wire cmd_ready,
  input wire [32:0] cmd_address,
  input wire [31:0] cmd_beats,
  input wire [MW-1:0] cmd_meta,
  output wire data_valid,
  input wire data_ready,
  output wire [511:0] data,
  output wire [MW-1:0] data_meta,
  output wire data_last, data_error,
  output wire idle, drain_done, fault,
  output wire [32:0] avm_address,
  output wire avm_read,
  output wire [7:0] avm_burstcount,
  input wire avm_waitrequest,
  input wire [511:0] avm_readdata,
  input wire avm_readdatavalid,
  input wire [1:0] avm_response
);
  localparam LEGAL=QD==QUEUE_DEPTH && OB==OUTSTANDING && MW==META_WIDTH &&
    (BURST_BEATS==1 || BURST_BEATS==2 || BURST_BEATS==4 ||
     BURST_BEATS==8 || BURST_BEATS==16) &&
    RETURN_BEATS>=OUTSTANDING*BURST_BEATS && RETURN_BEATS<=4096;
  generate if (!LEGAL) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q3_HT PARAMETER ERROR: DDR queue, burst or return capacity");
  end endgenerate

  reg failed, draining;
  reg [QAW-1:0] q_read, q_write;
  reg [31:0] q_count;
  (* nomem2reg *) reg [32:0] queue_address [0:QD-1];
  (* nomem2reg *) reg [31:0] queue_beats [0:QD-1];
  (* nomem2reg *) reg [MW-1:0] queue_meta [0:QD-1];
  reg pending;
  reg [32:0] pending_address;
  reg [7:0] pending_beats;
  reg [MW-1:0] pending_meta;
  reg pending_last;
  reg [BAW-1:0] b_read, b_write;
  reg [31:0] b_count;
  (* nomem2reg *) reg [7:0] burst_remaining [0:OB-1];
  (* nomem2reg *) reg [MW-1:0] burst_meta [0:OB-1];
  reg burst_last [0:OB-1];
  reg [RAW-1:0] r_read, r_write;
  reg [31:0] stored, reserved;
  reg output_valid;
  localparam RETURN_WIDTH=MW+514;
  (* ramstyle="M20K", nomem2reg *)
  reg [RETURN_WIDTH-1:0] return_memory [0:RB-1];
  reg [RETURN_WIDTH-1:0] output_word;

  wire aborting=flush || draining || failed;
  wire accepted_command=rst_n && pending && !avm_waitrequest;
  wire descriptor_accept=cmd_valid && cmd_ready;
  wire [64:0] descriptor_end={32'd0,cmd_address}+({33'd0,cmd_beats}<<6);
  wire invalid_descriptor=cmd_beats==0 || cmd_address[5:0]!=0 ||
    descriptor_end>65'h200000000;
  wire queue_push=descriptor_accept && !invalid_descriptor;
  wire [6:0] page_beats=7'd64-{1'b0,queue_address[q_read][11:6]};
  wire [31:0] burst_limit=queue_beats[q_read]<BURST_BEATS ?
    queue_beats[q_read] : BURST_BEATS;
  wire [7:0] issue_beats=burst_limit<page_beats ? burst_limit[7:0] :
    {1'b0,page_beats};
  wire reserve_burst=rst_n && LEGAL && !aborting && !pending &&
    q_count!=0 && b_count<OB && reserved+{24'd0,issue_beats}<=RB;
  wire queue_pop=reserve_burst && queue_beats[q_read]=={24'd0,issue_beats};
  wire returned=rst_n && avm_readdatavalid;
  wire known_return=b_count!=0 || accepted_command;
  wire [7:0] current_remaining=b_count!=0 ? burst_remaining[b_read] : pending_beats;
  wire [MW-1:0] current_meta=b_count!=0 ? burst_meta[b_read] : pending_meta;
  wire current_last=b_count!=0 ? burst_last[b_read] : pending_last;
  wire burst_pop=returned && known_return && current_remaining==1;
  wire return_fault=returned && (!known_return || avm_response!=0);
  wire return_store=returned && known_return && !aborting;
  wire return_discard=returned && known_return && aborting;
  wire output_transfer=data_valid && data_ready;
  wire read_memory=rst_n && !aborting && stored!=0 &&
    (!output_valid || data_ready);
  wire [31:0] abandoned_buffer=aborting ? stored+{31'd0,output_valid} : 32'd0;
  wire [RETURN_WIDTH-1:0] return_word={
    avm_response!=0,current_last && current_remaining==1,current_meta,avm_readdata};

  assign cmd_ready=rst_n && LEGAL && !aborting && q_count<QD;
  assign data_valid=rst_n && !aborting && output_valid;
  assign data=data_valid ? output_word[511:0] : 512'd0;
  assign data_meta=data_valid ? output_word[512+:MW] : {MW{1'b0}};
  assign data_last=data_valid && output_word[512+MW];
  assign data_error=data_valid && output_word[513+MW];
  assign fault=rst_n && failed;
  assign drain_done=rst_n && q_count==0 && !pending && b_count==0 &&
    reserved==0 && stored==0 && !output_valid;
  assign idle=drain_done && !aborting;
  // An offered command is irrevocable, including while cancellation drains.
  assign avm_read=rst_n && pending;
  assign avm_address=avm_read ? pending_address : 33'd0;
  assign avm_burstcount=avm_read ? pending_beats : 8'd0;

  always @(posedge clk) begin
    if (return_store) return_memory[r_write]<=return_word;
    if (read_memory) output_word<=return_memory[r_read];
    if (rst_n && !aborting) begin
      if (queue_push) begin
        queue_address[q_write]<=cmd_address;
        queue_beats[q_write]<=cmd_beats;
        queue_meta[q_write]<=cmd_meta;
      end
      if (reserve_burst && !queue_pop) begin
        queue_address[q_read]<=queue_address[q_read]+({25'd0,issue_beats}<<6);
        queue_beats[q_read]<=queue_beats[q_read]-{24'd0,issue_beats};
      end
    end
    if (rst_n) begin
      if (accepted_command) begin
        burst_remaining[b_write]<=
          (returned && b_count==0) ? pending_beats-1'b1 : pending_beats;
        burst_meta[b_write]<=pending_meta;
        burst_last[b_write]<=pending_last;
      end
      if (returned && b_count!=0 && !burst_pop)
        burst_remaining[b_read]<=burst_remaining[b_read]-1'b1;
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      failed<=0; draining<=0;
      q_read<=0; q_write<=0; q_count<=0;
      pending<=0; pending_address<=0; pending_beats<=0;
      pending_meta<=0; pending_last<=0;
      b_read<=0; b_write<=0; b_count<=0;
      r_read<=0; r_write<=0; stored<=0; reserved<=0; output_valid<=0;
    end else begin
      if (return_fault || (descriptor_accept && invalid_descriptor)) failed<=1;
      if (flush) begin
        failed<=0;
        draining<=1;
      end else if (draining && drain_done) draining<=0;

      if (aborting) begin
        q_read<=0; q_write<=0; q_count<=0;
      end else begin
        case ({queue_push,queue_pop})
          2'b10: q_count<=q_count+1'b1;
          2'b01: q_count<=q_count-1'b1;
          default: q_count<=q_count;
        endcase
        if (queue_push) q_write<=q_write==QD-1 ? 0 : q_write+1'b1;
        if (queue_pop) q_read<=q_read==QD-1 ? 0 : q_read+1'b1;
      end

      if (accepted_command) pending<=0;
      if (reserve_burst) begin
        pending<=1;
        pending_address<=queue_address[q_read];
        pending_beats<=issue_beats;
        pending_meta<=queue_meta[q_read];
        pending_last<=queue_pop;
      end

      case ({accepted_command,burst_pop})
        2'b10: b_count<=b_count+1'b1;
        2'b01: b_count<=b_count-1'b1;
        default: b_count<=b_count;
      endcase
      if (accepted_command) b_write<=b_write==OB-1 ? 0 : b_write+1'b1;
      if (burst_pop) b_read<=b_read==OB-1 ? 0 : b_read+1'b1;

      reserved<=reserved+(reserve_burst ? {24'd0,issue_beats} : 32'd0)-
        {31'd0,output_transfer}-abandoned_buffer-{31'd0,return_discard};
      if (aborting) begin
        r_read<=0; r_write<=0; stored<=0; output_valid<=0;
      end else begin
        case ({return_store,read_memory})
          2'b10: stored<=stored+1'b1;
          2'b01: stored<=stored-1'b1;
          default: stored<=stored;
        endcase
        if (return_store) r_write<=r_write==RB-1 ? 0 : r_write+1'b1;
        if (read_memory) begin
          r_read<=r_read==RB-1 ? 0 : r_read+1'b1;
          output_valid<=1;
        end else if (output_transfer) output_valid<=0;
      end
    end
  end
endmodule
