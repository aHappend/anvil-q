module tb;

reg clk=0; always #5 clk=~clk;
reg rst_n=0, cmd_valid=0; wire cmd_ready,done,error;
reg [31:0] cmd_layer=0,cmd_pos=0; reg [2:0] cmd_proj=0; reg [1:0] cmd_mode=0;
wire mem_req_valid,mem_req_write,mem_rsp_ready;
reg mem_req_ready=0,mem_rsp_valid=0,mem_rsp_error=0;
wire [3:0] mem_req_kind; wire [2:0] mem_req_proj;
wire [31:0] mem_req_layer,mem_req_row,mem_req_col,mem_req_wdata;
reg [31:0] mem_rsp_rdata=0;

anvil_q1_rmsnorm #(.NUM_LAYERS(1),.HIDDEN_SIZE(8),.MAX_SEQ_LEN(1)) dut(
.clk(clk),.rst_n(rst_n),.cmd_valid(cmd_valid),.cmd_ready(cmd_ready),
.cmd_layer(cmd_layer),.cmd_pos(cmd_pos),.done(done),.error(error),
.mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),
.mem_req_write(mem_req_write),.mem_req_kind(mem_req_kind),
.mem_req_layer(mem_req_layer),.mem_req_proj(mem_req_proj),
.mem_req_row(mem_req_row),.mem_req_col(mem_req_col),.mem_req_wdata(mem_req_wdata),
.mem_rsp_valid(mem_rsp_valid),.mem_rsp_ready(mem_rsp_ready),
.mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_error(mem_rsp_error)
,.cmd_mode(cmd_mode));
integer cycles=0, checks=0, requests=0, replies=0, writes=0;
integer target=-1; reg [15:0] bad=0; reg pending=0, injected=0;
reg [31:0] reply;
always @(negedge clk) begin
 mem_req_ready=rst_n;
 mem_rsp_valid=rst_n && pending;
 mem_rsp_rdata=reply;
end
always @(posedge clk) if(rst_n) begin
 cycles=cycles+1; if(cycles>200000) $fatal(1,"CHILD watchdog");
 if(mem_req_valid && mem_req_ready) begin
   if(pending || injected || mem_rsp_ready) $fatal(1,"CHILD traffic after fault/overlap");
   if(target==-1) $fatal(1,"INVALID child command memory effect");
   requests=requests+1; pending=1;
   if(mem_req_write) writes=writes+1;
   reply=(mem_req_kind==8 ? 65536 :
          (mem_req_kind==1 ? 32'h99999999 :
           (mem_req_kind==2 ? 32'h88888888 :
            (mem_req_kind==4 ? 0 : 16'h3c00))));
   if(target==-2 || mem_req_kind==target) begin
     injected=1; reply={16'd0,bad}; mem_rsp_error=(target==-2);
   end
 end else if(mem_rsp_valid && mem_rsp_ready) begin
   if(!pending) $fatal(1,"CHILD unexpected response");
   pending=0; replies=replies+1;
 end
end
task automatic check_error(input integer l,p,proj,mode,kind,input [15:0] raw);
integer start_requests,start_writes;
begin
 @(negedge clk); if(cmd_ready!==1) $fatal(1,"CHILD not idle");
 start_requests=requests; start_writes=writes;
 target=kind; bad=raw; injected=0; mem_rsp_error=0;
 cmd_layer=l; cmd_pos=p; cmd_proj=proj; cmd_mode=mode; cmd_valid=1;
 @(negedge clk); cmd_valid=0;
 while(done!==1) @(negedge clk);
 if(error!==1 || cmd_ready!==0 || pending || (kind==-1 && writes!=start_writes))
   $fatal(1,"CHILD error propagation/no-write failure");
 if(kind!=-1 && (!injected || requests==start_requests))
   $fatal(1,"CHILD fault not reached");
 checks=checks+1;
 @(negedge clk);
 if(done!==0 || error!==0 || cmd_ready!==1) $fatal(1,"CHILD error retirement");
 mem_rsp_error=0;
end endtask
initial begin
 #1; if({cmd_ready,done,error,mem_req_valid,mem_rsp_ready}!==5'd0)
   $fatal(1,"CHILD reset");
 repeat(3) @(negedge clk); rst_n=1;
check_error(1,0,0,0,-1,16'h0000);
check_error(0,1,0,0,-1,16'h0000);
check_error(0,0,0,3,-1,16'h0000);
check_error(0,0,0,0,-2,16'h0000);
check_error(0,0,0,0,5,16'h7c00);
check_error(0,0,0,0,5,16'h7e00);
check_error(0,0,0,1,6,16'h7c00);
check_error(0,0,0,1,6,16'h7e00);
check_error(0,0,0,2,7,16'h7c00);
check_error(0,0,0,2,7,16'h7e00);
 if(checks!=10 || requests!=replies) $fatal(1,"CHILD coverage");
 $display("PASS child rmsnorm errors=%0d requests=%0d",checks,requests);
 $finish;
end endmodule
