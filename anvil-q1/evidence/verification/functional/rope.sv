module tb;

reg clk=0; always #5 clk=~clk;
reg rst_n=0, cmd_valid=0; wire cmd_ready,done,error;
reg [31:0] cmd_layer=0,cmd_pos=0; reg [2:0] cmd_proj=0; reg [1:0] cmd_mode=0;
wire mem_req_valid,mem_req_write,mem_rsp_ready;
reg mem_req_ready=0,mem_rsp_valid=0,mem_rsp_error=0;
wire [3:0] mem_req_kind; wire [2:0] mem_req_proj;
wire [31:0] mem_req_layer,mem_req_row,mem_req_col,mem_req_wdata;
reg [31:0] mem_rsp_rdata=0;
anvil_q1_rope #(.NUM_LAYERS(1),.HIDDEN_SIZE(16),.NUM_Q_HEADS(4),.NUM_KV_HEADS(2),.HEAD_DIM(4),.MAX_SEQ_LEN(32768)) dut(
.clk(clk),.rst_n(rst_n),.cmd_valid(cmd_valid),.cmd_ready(cmd_ready),
.cmd_layer(cmd_layer),.cmd_pos(cmd_pos),.done(done),.error(error),
.mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),
.mem_req_write(mem_req_write),.mem_req_kind(mem_req_kind),
.mem_req_layer(mem_req_layer),.mem_req_proj(mem_req_proj),
.mem_req_row(mem_req_row),.mem_req_col(mem_req_col),.mem_req_wdata(mem_req_wdata),
.mem_rsp_valid(mem_rsp_valid),.mem_rsp_ready(mem_rsp_ready),
.mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_error(mem_rsp_error)
);
integer cycles=0, writes=0, accepted=0, pending=0, delay_count=0;
integer stalls=0, responses=0, completions=0, busy_holds=0, bubbles=0;
reg [136:0] held; reg was_stalled=0;
reg [31:0] reply; reg [31:0] expected_value;

reg [31:0] storage[0:3][0:15]; reg [71:0] expected[0:71];
initial begin storage[2][0]=32'h00001f00;
storage[2][1]=32'hffffd000;
storage[2][2]=32'h00004100;
storage[2][3]=32'hffffae00;
storage[2][4]=32'h00006300;
storage[2][5]=32'hffff8c00;
storage[2][6]=32'h00008500;
storage[2][7]=32'hffff6a00;
storage[2][8]=32'h0000a700;
storage[2][9]=32'hffff4800;
storage[2][10]=32'h0000c900;
storage[2][11]=32'hffff2600;
storage[2][12]=32'h0000eb00;
storage[2][13]=32'hffff0400;
storage[2][14]=32'h00010d00;
storage[2][15]=32'hfffee200;
storage[3][0]=32'h00001f00;
storage[3][1]=32'hffffd000;
storage[3][2]=32'h00004100;
storage[3][3]=32'hffffae00;
storage[3][4]=32'h00006300;
storage[3][5]=32'hffff8c00;
storage[3][6]=32'h00008500;
storage[3][7]=32'hffff6a00; $readmemh("/data/sufeng/anvil-q-line5/workspace_phase2/project/evidence/verification/functional/rope-expected.hex",expected); end
function automatic [31:0] read_memory(input [3:0] kind,input [2:0] proj,
 input [31:0] row,col);
begin
 if(proj!=0) $fatal(1,"RoPE unused projection");
 if(kind==8 && (row==2 || row==3) && col<(row==2 ? 16:8))
   read_memory=storage[row][col];
 else if(kind==11) case({row,col})
 64'h0000000100000000:read_memory=32'h2294501f;
64'h0000000100000001:read_memory=32'h35daa91e;
64'h0000000100000002:read_memory=32'h3ffffde7;
64'h0000000100000003:read_memory=32'h0010624e;
64'h0000000300000000:read_memory=32'hc0a3f683;
64'h0000000300000001:read_memory=32'h09081c37;
64'h0000000300000002:read_memory=32'h3fffed20;
64'h0000000300000003:read_memory=32'h003126e5;
64'h00007fff00000000:read_memory=32'h3edd671b;
64'h00007fff00000001:read_memory=32'h0c001b7d;
64'h00007fff00000002:read_memory=32'h0df30af7;
64'h00007fff00000003:read_memory=32'h3e761816;
 default: begin $fatal(1,"RoPE coefficient address"); read_memory=0; end
 endcase
 else begin $fatal(1,"RoPE illegal address"); read_memory=0; end
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

if(writes>=72 || mem_req_kind!==8 ||
 {mem_req_row[7:0],mem_req_col,mem_req_wdata} !== expected[writes])
 $fatal(1,"ROPE write mismatch %0d got row %0d col %0d data %h",
 writes,mem_req_row,mem_req_col,mem_req_wdata);
storage[mem_req_row][mem_req_col]=mem_req_wdata;

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
launch(0,1);
launch(0,3);
launch(0,32767);
if(writes!=72) $fatal(1,"RoPE write coverage");
 if(accepted!=responses || pending || writes==0 || stalls==0 ||
    busy_holds==0 || bubbles==0)
   $fatal(1,"COVERAGE missing transfer/write/stall");
 $display("PASS public writes=%0d transactions=%0d stalls=%0d busy_holds=%0d bubbles=%0d",
   writes,accepted,stalls,busy_holds,bubbles);
 $finish;
end endmodule
