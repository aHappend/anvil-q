module tb;

reg clk=0; always #5 clk=~clk;
reg rst_n=0, cmd_valid=0; wire cmd_ready,done,error;
reg [31:0] cmd_layer=0,cmd_pos=0; reg [2:0] cmd_proj=0; reg [1:0] cmd_mode=0;
wire mem_req_valid,mem_req_write,mem_rsp_ready;
reg mem_req_ready=0,mem_rsp_valid=0,mem_rsp_error=0;
wire [3:0] mem_req_kind; wire [2:0] mem_req_proj;
wire [31:0] mem_req_layer,mem_req_row,mem_req_col,mem_req_wdata;
reg [31:0] mem_rsp_rdata=0;
anvil_q1_w4a16_gemv #(.NUM_LAYERS(1),.HIDDEN_SIZE(8),.INTERMEDIATE_SIZE(8),.NUM_Q_HEADS(2),.NUM_KV_HEADS(2),.HEAD_DIM(4),.GROUP_SIZE(8),.MAX_SEQ_LEN(1)) dut(
.clk(clk),.rst_n(rst_n),.cmd_valid(cmd_valid),.cmd_ready(cmd_ready),
.cmd_layer(cmd_layer),.cmd_pos(cmd_pos),.done(done),.error(error),
.mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),
.mem_req_write(mem_req_write),.mem_req_kind(mem_req_kind),
.mem_req_layer(mem_req_layer),.mem_req_proj(mem_req_proj),
.mem_req_row(mem_req_row),.mem_req_col(mem_req_col),.mem_req_wdata(mem_req_wdata),
.mem_rsp_valid(mem_rsp_valid),.mem_rsp_ready(mem_rsp_ready),
.mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_error(mem_rsp_error)
,.cmd_proj(cmd_proj));
integer cycles=0, writes=0, accepted=0, pending=0, delay_count=0;
integer stalls=0, responses=0, completions=0, busy_holds=0, bubbles=0;
reg [136:0] held; reg was_stalled=0;
reg [31:0] reply; reg [31:0] expected_value;

function automatic [31:0] read_memory(input [3:0] kind,input [2:0] proj,
 input [31:0] row,col);
begin
 if(kind==8) begin
   if(proj!=0 || col>=8 || row!=(cmd_proj==4 ? 8:1))
     $fatal(1,"official activation address");
   case(col)
0:read_memory=32'hfffcff00;
1:read_memory=32'h0001ff00;
2:read_memory=32'hfffeff00;
3:read_memory=32'h00007f00;
4:read_memory=32'hffffe100;
5:read_memory=32'h00001100;
6:read_memory=32'hffffff00;
7:read_memory=32'h00000300;
   default:read_memory=0;
   endcase
 end else case({kind,proj,row,col})
71'h080000000000000000:read_memory=32'h97585367;
71'h080000000100000000:read_memory=32'hb6774256;
71'h080000000200000000:read_memory=32'hc54b3399;
71'h080000000300000000:read_memory=32'hb56a34aa;
71'h080000000400000000:read_memory=32'h96a75378;
71'h080000000500000000:read_memory=32'hb64c3396;
71'h080000000600000000:read_memory=32'hb5753388;
71'h080000000700000000:read_memory=32'ha5654357;
71'h100000000000000000:read_memory=32'hb6674377;
71'h180000000000000000:read_memory=32'h00001a8a;
71'h200000000000000000:read_memory=32'h0000a3a8;
71'h180000000000000001:read_memory=32'h00001c4f;
71'h200000000000000001:read_memory=32'h00002688;
71'h180000000000000002:read_memory=32'h0000203c;
71'h200000000000000002:read_memory=32'h0000aea0;
71'h180000000000000003:read_memory=32'h00001e40;
71'h200000000000000003:read_memory=32'h0000b058;
71'h180000000000000004:read_memory=32'h00002c3f;
71'h200000000000000004:read_memory=32'h0000cb38;
71'h180000000000000005:read_memory=32'h00002089;
71'h200000000000000005:read_memory=32'h00003440;
71'h180000000000000006:read_memory=32'h00002103;
71'h200000000000000006:read_memory=32'h00003530;
71'h180000000000000007:read_memory=32'h0000207a;
71'h200000000000000007:read_memory=32'h00002ff0;
71'h090000000000000000:read_memory=32'h557398a8;
71'h090000000100000000:read_memory=32'h57749995;
71'h090000000200000000:read_memory=32'h46748887;
71'h090000000300000000:read_memory=32'h99534c97;
71'h090000000400000000:read_memory=32'h4974b627;
71'h090000000500000000:read_memory=32'h67557a75;
71'h090000000600000000:read_memory=32'h57739927;
71'h090000000700000000:read_memory=32'h35768ac7;
71'h110000000000000000:read_memory=32'h57749977;
71'h190000000000000000:read_memory=32'h000027cc;
71'h210000000000000000:read_memory=32'h0000c868;
71'h190000000000000001:read_memory=32'h00002575;
71'h210000000000000001:read_memory=32'h0000c2a8;
71'h190000000000000002:read_memory=32'h0000202b;
71'h210000000000000002:read_memory=32'h0000c650;
71'h190000000000000003:read_memory=32'h000025a4;
71'h210000000000000003:read_memory=32'h000038f0;
71'h190000000000000004:read_memory=32'h0000209c;
71'h210000000000000004:read_memory=32'h0000b1a0;
71'h190000000000000005:read_memory=32'h00002206;
71'h210000000000000005:read_memory=32'h000048b0;
71'h190000000000000006:read_memory=32'h00002563;
71'h210000000000000006:read_memory=32'h00004810;
71'h190000000000000007:read_memory=32'h0000219e;
71'h210000000000000007:read_memory=32'h0000bd30;
71'h0c0000000000000000:read_memory=32'h56975bb4;
71'h0c0000000100000000:read_memory=32'h947ad379;
71'h0c0000000200000000:read_memory=32'h4b5a6676;
71'h0c0000000300000000:read_memory=32'h879cabb9;
71'h0c0000000400000000:read_memory=32'h87a64568;
71'h0c0000000500000000:read_memory=32'h4bc897ba;
71'h0c0000000600000000:read_memory=32'h28b98889;
71'h0c0000000700000000:read_memory=32'h42835797;
71'h140000000000000000:read_memory=32'h78898787;
71'h1c0000000000000000:read_memory=32'h00001db3;
71'h1c0000000000000001:read_memory=32'h00001e95;
71'h1c0000000000000002:read_memory=32'h00001950;
71'h1c0000000000000003:read_memory=32'h00001c1f;
71'h1c0000000000000004:read_memory=32'h00001bf1;
71'h1c0000000000000005:read_memory=32'h00001b09;
71'h1c0000000000000006:read_memory=32'h000019ed;
71'h1c0000000000000007:read_memory=32'h00001d1a;
 default: begin $fatal(1,"official tensor address"); read_memory=0; end
 endcase
end endfunction

reg [95:0] expected[0:23];
initial $readmemh("/data/sufeng/anvil-q-line5/workspace_phase2/project/evidence/verification/functional/official-gemv-writes.hex",expected);

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

if(writes>=24 || mem_req_kind!==8 || mem_req_proj!==0 ||
 {mem_req_row,mem_req_col,mem_req_wdata} !== expected[writes])
 $fatal(1,"OFFICIAL GEMV write mismatch %0d",writes);

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

launch(0,0); if(accepted!=41) $fatal(1,"GEMV Q transaction count");
launch(1,0); if(accepted!=82) $fatal(1,"GEMV K transaction count");
launch(4,0); if(accepted!=115) $fatal(1,"GEMV gate forbidden bias/count");
if(writes!=24) $fatal(1,"official outputs missing");
 if(accepted!=responses || pending || writes==0 || stalls==0 ||
    busy_holds==0 || bubbles==0)
   $fatal(1,"COVERAGE missing transfer/write/stall");
 $display("PASS public writes=%0d transactions=%0d stalls=%0d busy_holds=%0d bubbles=%0d",
   writes,accepted,stalls,busy_holds,bubbles);
 $finish;
end endmodule
