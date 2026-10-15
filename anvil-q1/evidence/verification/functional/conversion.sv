module tb;

reg clk=0; always #5 clk=~clk;
reg rst_n=0, cmd_valid=0; wire cmd_ready,done,error;
reg [31:0] cmd_layer=0,cmd_pos=0; reg [2:0] cmd_proj=0; reg [1:0] cmd_mode=0;
wire mem_req_valid,mem_req_write,mem_rsp_ready;
reg mem_req_ready=0,mem_rsp_valid=0,mem_rsp_error=0;
wire [3:0] mem_req_kind; wire [2:0] mem_req_proj;
wire [31:0] mem_req_layer,mem_req_row,mem_req_col,mem_req_wdata;
reg [31:0] mem_rsp_rdata=0;

reg [47:0] vectors[0:495];
integer block_index=0,writes=0,reads=0,cycles=0;
reg pending=0; reg [31:0] reply=0;
wire logit_valid; wire [31:0] logit_index; wire signed [31:0] logit_data;
initial $readmemh("/data/sufeng/anvil-q-line5/workspace_phase2/project/evidence/verification/functional/conversion.hex",vectors);
anvil_q1_top #(.NUM_LAYERS(1),.HIDDEN_SIZE(8),.INTERMEDIATE_SIZE(8),.NUM_Q_HEADS(2),.NUM_KV_HEADS(2),.HEAD_DIM(4),.GROUP_SIZE(8),.VOCAB_SIZE(62),.MAX_SEQ_LEN(1)) dut(
.clk(clk),.rst_n(rst_n),.token_valid(cmd_valid),.token_ready(cmd_ready),
.token_id(cmd_layer),.token_pos(cmd_pos),.done(done),.error(error),
.mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),
.mem_req_write(mem_req_write),.mem_req_kind(mem_req_kind),
.mem_req_layer(mem_req_layer),.mem_req_proj(mem_req_proj),
.mem_req_row(mem_req_row),.mem_req_col(mem_req_col),.mem_req_wdata(mem_req_wdata),
.mem_rsp_valid(mem_rsp_valid),.mem_rsp_ready(mem_rsp_ready),
.mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_error(mem_rsp_error)

,.new_sequence(1'b1),.logit_valid(logit_valid),.logit_ready(1'b0),
.logit_index(logit_index),.logit_data(logit_data));
always @(negedge clk) begin
 mem_req_ready=rst_n; mem_rsp_valid=rst_n && pending; mem_rsp_rdata=reply;
end
always @(posedge clk) if(rst_n) begin
 cycles=cycles+1; if(cycles>100000) $fatal(1,"CONVERSION watchdog");
 if(done || error || logit_valid) $fatal(1,"CONVERSION unexpected completion");
 if(mem_req_valid && mem_req_ready) begin
   if(pending || mem_rsp_ready || mem_req_layer!==0 || mem_req_proj!==0 ||
      mem_req_col>=8) $fatal(1,"CONVERSION protocol/address");
   pending=1;
   if(mem_req_write) begin
     if(mem_req_kind!==8 || mem_req_row!==0 || mem_req_col!==(writes%8) ||
        mem_req_wdata!==vectors[writes][31:0])
       $fatal(1,"F16 conversion mismatch %0d got %h expected %h",
         writes,mem_req_wdata,vectors[writes][31:0]);
     writes=writes+1; reply=0;
   end else begin
     if(mem_req_kind!==0 || mem_req_row!==block_index ||
        mem_req_col!==(reads%8) || mem_req_wdata!==0)
       $fatal(1,"CONVERSION unexpected model request");
     reply={16'd0,vectors[reads][47:32]}; reads=reads+1;
   end
 end else if(mem_rsp_valid && mem_rsp_ready) pending=0;
end
initial begin
 #0; #1; repeat(3) @(negedge clk);

 for(block_index=0;block_index<62;block_index=block_index+1) begin
   rst_n=1; cmd_layer=block_index;
   @(negedge clk); if(cmd_ready!==1) $fatal(1,"CONVERSION not idle");
   cmd_valid=1; @(negedge clk); cmd_valid=0;
   while(writes<(block_index+1)*8) @(negedge clk);
   // Abort after the observed final embedding write, before decoder work.
   rst_n=0; pending=0; mem_rsp_valid=0; repeat(2) @(negedge clk);
 end
 if(writes!=496 || reads!=496) $fatal(1,"CONVERSION coverage");
 $display("PASS ordinary F16 conversions=%0d",writes); $finish;
end endmodule
