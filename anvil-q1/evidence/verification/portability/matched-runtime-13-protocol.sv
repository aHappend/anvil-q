module tb;

reg clk=0; always #5 clk=~clk;
reg rst_n=0, cmd_valid=0; wire cmd_ready,done,error;
reg [31:0] cmd_layer=0,cmd_pos=0; reg [2:0] cmd_proj=0; reg [1:0] cmd_mode=0;
wire mem_req_valid,mem_req_write,mem_rsp_ready;
reg mem_req_ready=0,mem_rsp_valid=0,mem_rsp_error=0;
wire [3:0] mem_req_kind; wire [2:0] mem_req_proj;
wire [31:0] mem_req_layer,mem_req_row,mem_req_col,mem_req_wdata;
reg [31:0] mem_rsp_rdata=0;

reg new_sequence=0; wire logit_valid; wire [31:0] logit_index;
wire signed [31:0] logit_data;
integer failures=0, aborts=0, cycle=0;
anvil_q1_top #(.NUM_LAYERS(1),.HIDDEN_SIZE(8),.INTERMEDIATE_SIZE(8),.NUM_Q_HEADS(2),.NUM_KV_HEADS(2),.HEAD_DIM(4),.GROUP_SIZE(8),.VOCAB_SIZE(1),.MAX_SEQ_LEN(1)) dut(
.clk(clk),.rst_n(rst_n),.token_valid(cmd_valid),.token_ready(cmd_ready),
.token_id(cmd_layer),.token_pos(cmd_pos),.done(done),.error(error),
.mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),
.mem_req_write(mem_req_write),.mem_req_kind(mem_req_kind),
.mem_req_layer(mem_req_layer),.mem_req_proj(mem_req_proj),
.mem_req_row(mem_req_row),.mem_req_col(mem_req_col),.mem_req_wdata(mem_req_wdata),
.mem_rsp_valid(mem_rsp_valid),.mem_rsp_ready(mem_rsp_ready),
.mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_error(mem_rsp_error)

,.new_sequence(new_sequence),.logit_valid(logit_valid),.logit_ready(1'b0),
.logit_index(logit_index),.logit_data(logit_data));
task automatic zero_outputs;
begin
 if({cmd_ready,done,error,logit_valid,logit_index,logit_data,
     mem_req_valid,mem_rsp_ready,mem_req_write,mem_req_kind,mem_req_layer,
     mem_req_proj,mem_req_row,mem_req_col,mem_req_wdata} !== 206'd0)
   $fatal(1,"RESET public output leakage");
end endtask
always @(posedge clk) begin
 cycle=cycle+1;
 if(cycle>1000) $fatal(1,"PROTOCOL watchdog");
 if(!rst_n) zero_outputs();
end
always @(negedge clk) if(!rst_n) zero_outputs();
task automatic accept(input [31:0] token,position,input ns);
begin
 @(negedge clk); if(cmd_ready!==1) $fatal(1,"not idle");
 cmd_layer=token; cmd_pos=position; new_sequence=ns; cmd_valid=1;
 @(posedge clk);
 if(mem_req_valid!==0 || mem_rsp_ready!==0)
   $fatal(1,"request accepted on E0");
 @(negedge clk); cmd_valid=0;
 if(cmd_ready!==0 || done!==0 || error!==0)
   $fatal(1,"post E0 busy contract");
end endtask
task automatic rejected(input [31:0] token,position,input ns);
begin
 accept(token,position,ns);
 while(done!==1) begin
   if(mem_req_valid!==0 || logit_valid!==0)
     $fatal(1,"INVALID token produced memory/logits");
   @(negedge clk);
 end
 if(error!==1 || cmd_ready!==0) $fatal(1,"INVALID completion");
 failures=failures+1;
 @(negedge clk);
 if(done!==0 || error!==0 || cmd_ready!==1)
   $fatal(1,"completion pulse/retire contract");
end endtask
task automatic wait_request;
begin
 while(mem_req_valid!==1) @(negedge clk);
 if(mem_req_write!==0 || mem_req_kind!==0 ||
    mem_req_layer!==0 || mem_req_proj!==0 || mem_req_row!==0 || mem_req_col!==0)
   $fatal(1,"first embedding request address");
end endtask
task automatic reset_now;
begin
 rst_n=0; #1; zero_outputs(); @(negedge clk);
 mem_rsp_valid=0; mem_rsp_error=0; mem_req_ready=0; rst_n=1;
 @(negedge clk); if(cmd_ready!==1) $fatal(1,"reset recovery");
 aborts=aborts+1;
end endtask
initial begin
 #0; #1; zero_outputs(); repeat(3) @(negedge clk); rst_n=1;
 rejected(1,0,0); rejected(0,1,0); rejected(0,1,1);
 // Invalid submissions must leave the initial committed position unchanged.
 accept(0,0,0); wait_request();
 repeat(3) begin
   @(negedge clk);
   if(mem_req_valid!==1 || mem_rsp_ready!==0)
     $fatal(1,"stalled request handshake");
 end
 reset_now();
 accept(0,0,1); wait_request(); mem_req_ready=1;
 @(negedge clk); mem_req_ready=0;
 if(mem_req_valid!==0 || mem_rsp_ready!==1)
   $fatal(1,"post R response phase");
 reset_now();
 accept(0,0,0); wait_request(); mem_req_ready=1;
 @(negedge clk); mem_req_ready=0;
 mem_rsp_rdata=0; mem_rsp_error=1; mem_rsp_valid=1;
 @(negedge clk); mem_rsp_valid=0; mem_rsp_error=0;
 while(done!==1) begin
   if(mem_req_valid!==0 || logit_valid!==0)
     $fatal(1,"ERROR generated subsequent traffic");
   @(negedge clk);
 end
 if(error!==1) $fatal(1,"memory error not reported");
 @(negedge clk);
 rejected(0,0,0);
 accept(0,0,1); wait_request(); reset_now();
 if(failures!=4 || aborts!=3) $fatal(1,"PROTOCOL coverage");
 $display("PASS protocol invalid=%0d reset_aborts=%0d memory_errors=1",failures,aborts);
 $finish;
end endmodule
