module tb;

reg clk=0; always #5 clk=~clk;
reg rst_n=0, cmd_valid=0; wire cmd_ready,done,error;
reg [31:0] cmd_layer=0,cmd_pos=0; reg [2:0] cmd_proj=0; reg [1:0] cmd_mode=0;
wire mem_req_valid,mem_req_write,mem_rsp_ready;
reg mem_req_ready=0,mem_rsp_valid=0,mem_rsp_error=0;
wire [3:0] mem_req_kind; wire [2:0] mem_req_proj;
wire [31:0] mem_req_layer,mem_req_row,mem_req_col,mem_req_wdata;
reg [31:0] mem_rsp_rdata=0;
anvil_q1_rmsnorm #(.NUM_LAYERS(1),.HIDDEN_SIZE(16)) dut(
.clk(clk),.rst_n(rst_n),.cmd_valid(cmd_valid),.cmd_ready(cmd_ready),
.cmd_layer(cmd_layer),.cmd_pos(cmd_pos),.done(done),.error(error),
.mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),
.mem_req_write(mem_req_write),.mem_req_kind(mem_req_kind),
.mem_req_layer(mem_req_layer),.mem_req_proj(mem_req_proj),
.mem_req_row(mem_req_row),.mem_req_col(mem_req_col),.mem_req_wdata(mem_req_wdata),
.mem_rsp_valid(mem_rsp_valid),.mem_rsp_ready(mem_rsp_ready),
.mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_error(mem_rsp_error)
,.cmd_mode(cmd_mode));
integer cycles=0, writes=0, accepted=0, pending=0, delay_count=0;
integer stalls=0, responses=0, completions=0, busy_holds=0, bubbles=0;
reg [136:0] held; reg was_stalled=0;
reg [31:0] reply; reg [31:0] expected_value;

reg [31:0] activation[0:15],exp_data[0:15]; reg [15:0] gamma[0:15];
initial begin activation[0]=32'hfffd9200; gamma[0]=16'h3c00; exp_data[0]=32'hfffe89d1;
activation[1]=32'hffff8d00; gamma[1]=16'hbc00; exp_data[1]=32'h0000452f;
activation[2]=32'hfffe6a00; gamma[2]=16'h3800; exp_data[2]=32'hffff85e1;
activation[3]=32'h0000f700; gamma[3]=16'h4000; exp_data[3]=32'h0001292f;
activation[4]=32'h00003900; gamma[4]=16'h0001; exp_data[4]=32'h00000000;
activation[5]=32'h0002a300; gamma[5]=16'h03ff; exp_data[5]=32'h00000006;
activation[6]=32'hfffe0900; gamma[6]=16'h8000; exp_data[6]=32'h00000000;
activation[7]=32'h0000e400; gamma[7]=16'h3bff; exp_data[7]=32'h00008918;
activation[8]=32'h00020e00; gamma[8]=16'h3c00; exp_data[8]=32'h00013c6f;
activation[9]=32'h00014000; gamma[9]=16'hbc00; exp_data[9]=32'hffff3f7e;
activation[10]=32'h00022300; gamma[10]=16'h3800; exp_data[10]=32'h0000a488;
activation[11]=32'hfffd6b00; gamma[11]=16'h4000; exp_data[11]=32'hfffce4b5;
activation[12]=32'h00016000; gamma[12]=16'h0001; exp_data[12]=32'h00000000;
activation[13]=32'h0000b900; gamma[13]=16'h03ff; exp_data[13]=32'h00000002;
activation[14]=32'h0001e000; gamma[14]=16'h8000; exp_data[14]=32'h00000000;
activation[15]=32'h00003e00; gamma[15]=16'h3bff; exp_data[15]=32'h00002548; end
function automatic [31:0] read_memory(input [3:0] kind,input [2:0] proj,
 input [31:0] row,col);
begin
 if(proj!=0 || row!=0 || col>=16) $fatal(1,"RMS address");
 if(kind==8) read_memory=activation[col];
 else if(kind==5) read_memory={16'd0,gamma[col]};
 else begin $fatal(1,"RMS illegal kind"); read_memory=0; end
end endfunction

task automatic reset_check;
begin
 if(cmd_ready !== 0 || done !== 0 || error !== 0 ||
    mem_req_valid !== 0 || mem_rsp_ready !== 0 ||
    {mem_req_write,mem_req_kind,mem_req_layer,mem_req_proj,
     mem_req_row,mem_req_col,mem_req_wdata} !== 136'd0)
   $fatal(1,"RESET public output leakage");
end endtask
always @(negedge clk) begin
 if(!rst_n) reset_check();
 else begin
 if(^{cmd_ready,done,error,mem_req_valid,mem_rsp_ready} === 1'bx)
   $fatal(1,"ACTIVE unknown handshake at rising edge");
 if(mem_req_valid && ^{mem_req_write,mem_req_kind,mem_req_layer,
    mem_req_proj,mem_req_row,mem_req_col,mem_req_wdata} === 1'bx)
   $fatal(1,"ACTIVE unknown request payload at rising edge");
 if(^{cmd_ready,done,error,mem_req_valid,mem_rsp_ready} === 1'bx)
   $fatal(1,"ACTIVE unknown handshake");
 if(mem_req_valid && ^{mem_req_write,mem_req_kind,mem_req_layer,
    mem_req_proj,mem_req_row,mem_req_col,mem_req_wdata} === 1'bx)
   $fatal(1,"ACTIVE unknown request payload");
   mem_req_ready = cycles%31 != 0;
   mem_rsp_valid = pending && delay_count==0;
   mem_rsp_rdata = reply;
 end
end
always @(posedge clk) begin
 cycles=cycles+1;
 if(!rst_n) reset_check();
 else begin
 if(cycles>120000000) $fatal(1,"WATCHDOG");
 if(was_stalled && {mem_req_valid,mem_req_write,mem_req_kind,mem_req_layer,
      mem_req_proj,mem_req_row,mem_req_col,mem_req_wdata} !== held)
   $fatal(1,"REQUEST payload changed under backpressure");
 was_stalled=mem_req_valid && !mem_req_ready;
 held={mem_req_valid,mem_req_write,mem_req_kind,mem_req_layer,
       mem_req_proj,mem_req_row,mem_req_col,mem_req_wdata};
 if(was_stalled) stalls=stalls+1;
 if(mem_req_valid && mem_req_ready) begin
   if(pending || mem_rsp_ready) $fatal(1,"OUTSTANDING or request/response overlap");
   if(mem_req_layer!==0) $fatal(1,"unexpected layer");
   accepted=accepted+1; pending=1; delay_count=(accepted%127==0 ? 2 : 0);
   if(accepted%262144==0) begin
     $display("PROGRESS accepted=%0d compared_writes=%0d completed=%0d cycles=%0d",
       accepted,writes,completions,cycles);
     $fflush();
   end
   if(mem_req_write) begin

if(mem_req_kind!==8 || mem_req_proj!==0 || mem_req_row!==1 ||
   mem_req_col!==writes || mem_req_wdata!==exp_data[writes])
 $fatal(1,"RMS write mismatch %0d got %h",writes,mem_req_wdata);

     writes=writes+1; reply=0;
   end else begin
     reply=read_memory(mem_req_kind,mem_req_proj,mem_req_row,mem_req_col);
   end
 end else if(pending && delay_count>0) delay_count=delay_count-1;
 if(mem_rsp_valid && mem_rsp_ready) begin
   if(!pending || delay_count!=0) $fatal(1,"UNEXPECTED response");
   pending=0; responses=responses+1;
 end
 if(done) begin
   if(error !== 0 || pending) $fatal(1,"unexpected completion error/outstanding");
   completions=completions+1;
 end
 if(cmd_valid && !cmd_ready && !done) busy_holds=busy_holds+1;
 if(!cmd_valid && cmd_ready) begin
   if(mem_req_valid || done || error) $fatal(1,"IDLE bubble produced work");
   bubbles=bubbles+1;
 end
 end
end
task automatic launch(input integer projection, input integer position);
begin
 @(negedge clk); while(cmd_ready !== 1) @(negedge clk);
 cmd_proj=projection; cmd_pos=position; cmd_valid=1;
 repeat(3) begin
   @(negedge clk);
   if(cmd_ready!==0) $fatal(1,"BUSY accepted held valid");
 end
 cmd_valid=0;
 while(done !== 1) @(negedge clk);
 @(negedge clk);
 repeat(2) @(negedge clk);
end endtask
initial begin
 #0; reset_check(); #1; reset_check(); repeat(3) @(negedge clk); rst_n=1;
launch(0,0); if(writes!=16) $fatal(1,"RMS missing outputs");
 if(accepted!=responses || pending || writes==0 || stalls==0 ||
    busy_holds==0 || bubbles==0)
   $fatal(1,"COVERAGE missing transfer/write/stall");
 $display("PASS public writes=%0d transactions=%0d stalls=%0d busy_holds=%0d bubbles=%0d",
   writes,accepted,stalls,busy_holds,bubbles);
 $finish;
end endmodule
