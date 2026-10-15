module tb;

reg clk=0; always #5 clk=~clk;
reg rst_n=0, cmd_valid=0; wire cmd_ready,done,error;
reg [31:0] cmd_layer=0,cmd_pos=0; reg [2:0] cmd_proj=0; reg [1:0] cmd_mode=0;
wire mem_req_valid,mem_req_write,mem_rsp_ready;
reg mem_req_ready=0,mem_rsp_valid=0,mem_rsp_error=0;
wire [3:0] mem_req_kind; wire [2:0] mem_req_proj;
wire [31:0] mem_req_layer,mem_req_row,mem_req_col,mem_req_wdata;
reg [31:0] mem_rsp_rdata=0;

reg new_sequence=1; wire logit_valid; reg logit_ready=1;
wire [31:0] logit_index; wire signed [31:0] logit_data;
integer cycles=0,scenario=0,checks=0,writes=0,acks=0,logits=0,requests=0,replies=0;
reg pending=0,injected=0,reply_error=0;
reg [31:0] reply=0; reg [31:0] scratch[0:119];
anvil_q1_top #(.NUM_LAYERS(1),.HIDDEN_SIZE(8),.INTERMEDIATE_SIZE(8),.NUM_Q_HEADS(2),.NUM_KV_HEADS(2),.HEAD_DIM(4),.GROUP_SIZE(8),.VOCAB_SIZE(2),.MAX_SEQ_LEN(1)) dut(
.clk(clk),.rst_n(rst_n),.token_valid(cmd_valid),.token_ready(cmd_ready),
.token_id(cmd_layer),.token_pos(cmd_pos),.done(done),.error(error),
.mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),
.mem_req_write(mem_req_write),.mem_req_kind(mem_req_kind),
.mem_req_layer(mem_req_layer),.mem_req_proj(mem_req_proj),
.mem_req_row(mem_req_row),.mem_req_col(mem_req_col),.mem_req_wdata(mem_req_wdata),
.mem_rsp_valid(mem_rsp_valid),.mem_rsp_ready(mem_rsp_ready),
.mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_error(mem_rsp_error)

,.new_sequence(new_sequence),.logit_valid(logit_valid),.logit_ready(logit_ready),
.logit_index(logit_index),.logit_data(logit_data));
always @(negedge clk) begin
 mem_req_ready=rst_n; mem_rsp_valid=rst_n && pending;
 mem_rsp_error=reply_error; mem_rsp_rdata=reply;
end
always @(posedge clk) if(rst_n) begin
 cycles=cycles+1; if(cycles>100000) $fatal(1,"TOP fault watchdog");
 if(logit_valid && logit_ready) begin
   if((scenario!=2 && scenario!=9) || logits!=0 ||
      logit_index!==0 || logit_data!==524288)
     $fatal(1,"PARTIAL logit mismatch/scenario");
   logits=logits+1;
 end
 if(mem_req_valid && mem_req_ready) begin
   if(pending || injected || mem_rsp_ready) $fatal(1,"TOP post-fault/overlap traffic");
   pending=1; requests=requests+1; reply_error=0;
   if(mem_req_write) begin
     if(mem_req_kind!=8 && mem_req_kind!=9 && mem_req_kind!=10)
       $fatal(1,"TOP illegal write");
     writes=writes+1;
     if(mem_req_kind==8) scratch[mem_req_row*8+mem_req_col]=mem_req_wdata;
     reply=0;
   end else case(mem_req_kind)
     0,3,5,6,7: reply=16'h3c00;
     1,2,4,9,10: reply=0;
     8: reply=scratch[mem_req_row*8+mem_req_col];
     11: reply=mem_req_col%2==0 ? 32'h40000000 : 0;
     default: $fatal(1,"TOP unknown kind");
   endcase
   if((scenario==1 && acks>0) || (scenario==2 && logits==1)) begin
     injected=1; reply_error=1;
   end
   if(scenario==3 && mem_req_kind==0) begin
     injected=1; reply=16'h7c00;
   end
   if((scenario==4 && mem_req_kind==4) ||
      (scenario==5 && mem_req_kind==3) ||
      (scenario==6 && mem_req_kind==5) ||
      (scenario==7 && mem_req_kind==6) ||
      (scenario==8 && mem_req_kind==7) ||
      (scenario==9 && logits==1 && mem_req_kind==0)) begin
     injected=1; reply=(scenario==5 ? 16'hbc00 : 16'h7e00);
   end
 end else if(mem_rsp_valid && mem_rsp_ready) begin
   pending=0; replies=replies+1;
   if(writes>0) acks=writes;
 end
end
task automatic launch(input ns);
begin
 @(negedge clk); if(cmd_ready!==1) $fatal(1,"TOP not idle");
 cmd_valid=1; new_sequence=ns;
 @(negedge clk); cmd_valid=0;
end endtask
task automatic retire_error;
begin
 while(done!==1) @(negedge clk);
 if(error!==1 || cmd_ready!==0 || pending) $fatal(1,"TOP missing fault completion");
 @(negedge clk);
 if(done!==0 || error!==0 || cmd_ready!==1) $fatal(1,"TOP fault retirement");
end endtask
initial begin
 repeat(3) @(negedge clk); rst_n=1;
 for(scenario=1;scenario<=9;scenario=scenario+1) begin
   writes=0; acks=0; logits=0; injected=0;
   launch(1); retire_error();
   if(!injected || (scenario==1 && acks==0) ||
      ((scenario==2 || scenario==9) && logits!=1))
     $fatal(1,"TOP missing directed fault event");
   checks=checks+1;
   // A fault must invalidate the sequence even though token position is zero.
   launch(0); retire_error(); checks=checks+1;
 end
 if(checks!=18 || requests!=replies) $fatal(1,"TOP fault coverage");
 $display("PASS top errors after_write=1 partial_logit=2 nonfinite_boundaries=7 invalidated=9");
 $finish;
end endmodule
