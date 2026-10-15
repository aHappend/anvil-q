module tb;

reg clk=0; always #5 clk=~clk;
reg rst_n=0, cmd_valid=0; wire cmd_ready,done,error;
reg [31:0] cmd_layer=0,cmd_pos=0; reg [2:0] cmd_proj=0; reg [1:0] cmd_mode=0;
wire mem_req_valid,mem_req_write,mem_rsp_ready;
reg mem_req_ready=0,mem_rsp_valid=0,mem_rsp_error=0;
wire [3:0] mem_req_kind; wire [2:0] mem_req_proj;
wire [31:0] mem_req_layer,mem_req_row,mem_req_col,mem_req_wdata;
reg [31:0] mem_rsp_rdata=0;
anvil_q1_gqa_attention #(.NUM_LAYERS(1),.HIDDEN_SIZE(112),.NUM_Q_HEADS(14),.NUM_KV_HEADS(2),.HEAD_DIM(8),.MAX_SEQ_LEN(4)) dut(
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

reg [103:0] expected[0:143];
reg [31:0] keys[0:15], vals[0:15];
initial $readmemh("/data/sufeng/anvil-q-line5/workspace_phase2/project/evidence/verification/functional/attention-expected.hex",expected);
function automatic [31:0] read_memory(input [3:0] kind,input [2:0] proj,
 input [31:0] row,col);
begin
 if(proj!=0 || ((kind==9 || kind==10) && row>2))
   $fatal(1,"CAUSAL future-cache read or projection");
 if(kind==9 && row==2 && col<16) read_memory=keys[col];
 else if(kind==10 && row==2 && col<16) read_memory=vals[col];
 else case({4'd0,kind,row,col})
 72'h080000000200000000:read_memory=32'hfffe5f00;
72'h080000000200000001:read_memory=32'h00011e00;
72'h080000000200000002:read_memory=32'h00007900;
72'h080000000200000003:read_memory=32'h0000dc00;
72'h080000000200000004:read_memory=32'hffff1500;
72'h080000000200000005:read_memory=32'hfffe9b00;
72'h080000000200000006:read_memory=32'hffff6c00;
72'h080000000200000007:read_memory=32'h00017400;
72'h080000000200000008:read_memory=32'hfffe4e00;
72'h080000000200000009:read_memory=32'hfffea500;
72'h08000000020000000a:read_memory=32'h00016f00;
72'h08000000020000000b:read_memory=32'hffffb600;
72'h08000000020000000c:read_memory=32'hffff6200;
72'h08000000020000000d:read_memory=32'h0001a100;
72'h08000000020000000e:read_memory=32'hfffee300;
72'h08000000020000000f:read_memory=32'hffff3e00;
72'h080000000200000010:read_memory=32'h0000d200;
72'h080000000200000011:read_memory=32'h0000c500;
72'h080000000200000012:read_memory=32'hffff6200;
72'h080000000200000013:read_memory=32'hfffe5a00;
72'h080000000200000014:read_memory=32'h00005400;
72'h080000000200000015:read_memory=32'h00017d00;
72'h080000000200000016:read_memory=32'hfffeba00;
72'h080000000200000017:read_memory=32'hffffea00;
72'h080000000200000018:read_memory=32'h00008600;
72'h080000000200000019:read_memory=32'hfffe0f00;
72'h08000000020000001a:read_memory=32'hfffef000;
72'h08000000020000001b:read_memory=32'hfffea000;
72'h08000000020000001c:read_memory=32'h00006200;
72'h08000000020000001d:read_memory=32'hffffe400;
72'h08000000020000001e:read_memory=32'h00017500;
72'h08000000020000001f:read_memory=32'h00013000;
72'h080000000200000020:read_memory=32'hfffe4200;
72'h080000000200000021:read_memory=32'h00004700;
72'h080000000200000022:read_memory=32'hffff5700;
72'h080000000200000023:read_memory=32'h0001f100;
72'h080000000200000024:read_memory=32'h0000f500;
72'h080000000200000025:read_memory=32'hfffe6900;
72'h080000000200000026:read_memory=32'hfffe5400;
72'h080000000200000027:read_memory=32'hffffb200;
72'h080000000200000028:read_memory=32'hfffff300;
72'h080000000200000029:read_memory=32'hfffe6000;
72'h08000000020000002a:read_memory=32'hffffaa00;
72'h08000000020000002b:read_memory=32'h00016500;
72'h08000000020000002c:read_memory=32'hffff2800;
72'h08000000020000002d:read_memory=32'h0000ff00;
72'h08000000020000002e:read_memory=32'hffff6300;
72'h08000000020000002f:read_memory=32'hfffe9800;
72'h080000000200000030:read_memory=32'hfffe1200;
72'h080000000200000031:read_memory=32'hfffe2100;
72'h080000000200000032:read_memory=32'h00019600;
72'h080000000200000033:read_memory=32'h0001ef00;
72'h080000000200000034:read_memory=32'hfffea000;
72'h080000000200000035:read_memory=32'h00000c00;
72'h080000000200000036:read_memory=32'hfffef200;
72'h080000000200000037:read_memory=32'h0000db00;
72'h080000000200000038:read_memory=32'hfffe6b00;
72'h080000000200000039:read_memory=32'hfffea100;
72'h08000000020000003a:read_memory=32'hffff6a00;
72'h08000000020000003b:read_memory=32'hfffe1200;
72'h08000000020000003c:read_memory=32'h00013300;
72'h08000000020000003d:read_memory=32'h00009600;
72'h08000000020000003e:read_memory=32'hffff7100;
72'h08000000020000003f:read_memory=32'h00007e00;
72'h080000000200000040:read_memory=32'h00004b00;
72'h080000000200000041:read_memory=32'hfffeaf00;
72'h080000000200000042:read_memory=32'h0000ed00;
72'h080000000200000043:read_memory=32'h0000c100;
72'h080000000200000044:read_memory=32'h00016600;
72'h080000000200000045:read_memory=32'hffff4a00;
72'h080000000200000046:read_memory=32'h00004700;
72'h080000000200000047:read_memory=32'hfffebd00;
72'h080000000200000048:read_memory=32'h00003300;
72'h080000000200000049:read_memory=32'hfffffc00;
72'h08000000020000004a:read_memory=32'hffffa300;
72'h08000000020000004b:read_memory=32'h00010d00;
72'h08000000020000004c:read_memory=32'h0000b400;
72'h08000000020000004d:read_memory=32'hffffee00;
72'h08000000020000004e:read_memory=32'hffff6a00;
72'h08000000020000004f:read_memory=32'h0001ec00;
72'h080000000200000050:read_memory=32'h00004400;
72'h080000000200000051:read_memory=32'h0001bf00;
72'h080000000200000052:read_memory=32'h00002300;
72'h080000000200000053:read_memory=32'hffff3200;
72'h080000000200000054:read_memory=32'h0000b400;
72'h080000000200000055:read_memory=32'hfffedf00;
72'h080000000200000056:read_memory=32'h0001bd00;
72'h080000000200000057:read_memory=32'h00017600;
72'h080000000200000058:read_memory=32'h00004700;
72'h080000000200000059:read_memory=32'h00018900;
72'h08000000020000005a:read_memory=32'h0001a700;
72'h08000000020000005b:read_memory=32'h00001200;
72'h08000000020000005c:read_memory=32'hffff4b00;
72'h08000000020000005d:read_memory=32'h00019d00;
72'h08000000020000005e:read_memory=32'h00001900;
72'h08000000020000005f:read_memory=32'h0000a900;
72'h080000000200000060:read_memory=32'h00007c00;
72'h080000000200000061:read_memory=32'h00014a00;
72'h080000000200000062:read_memory=32'hffff0000;
72'h080000000200000063:read_memory=32'h00009300;
72'h080000000200000064:read_memory=32'h00014200;
72'h080000000200000065:read_memory=32'h00005600;
72'h080000000200000066:read_memory=32'h00011700;
72'h080000000200000067:read_memory=32'h00007200;
72'h080000000200000068:read_memory=32'hffff7900;
72'h080000000200000069:read_memory=32'hffffca00;
72'h08000000020000006a:read_memory=32'hffff1b00;
72'h08000000020000006b:read_memory=32'hfffeb400;
72'h08000000020000006c:read_memory=32'h00014200;
72'h08000000020000006d:read_memory=32'h00001000;
72'h08000000020000006e:read_memory=32'hffff4200;
72'h08000000020000006f:read_memory=32'h0000af00;
72'h080000000300000000:read_memory=32'hffff0300;
72'h080000000300000001:read_memory=32'hffff8400;
72'h080000000300000002:read_memory=32'h00003c00;
72'h080000000300000003:read_memory=32'h00004700;
72'h080000000300000004:read_memory=32'hfffe3a00;
72'h080000000300000005:read_memory=32'hffffd900;
72'h080000000300000006:read_memory=32'hfffe9400;
72'h080000000300000007:read_memory=32'h0001ab00;
72'h080000000300000008:read_memory=32'hffff4900;
72'h080000000300000009:read_memory=32'hffff4100;
72'h08000000030000000a:read_memory=32'h00005f00;
72'h08000000030000000b:read_memory=32'h00006000;
72'h08000000030000000c:read_memory=32'h00018b00;
72'h08000000030000000d:read_memory=32'hffff3700;
72'h08000000030000000e:read_memory=32'hfffe5300;
72'h08000000030000000f:read_memory=32'h00004300;
72'h080000000400000000:read_memory=32'h0001a400;
72'h080000000400000001:read_memory=32'h0000d300;
72'h080000000400000002:read_memory=32'hffffc200;
72'h080000000400000003:read_memory=32'h0001dd00;
72'h080000000400000004:read_memory=32'hfffecc00;
72'h080000000400000005:read_memory=32'hffffc800;
72'h080000000400000006:read_memory=32'h00007000;
72'h080000000400000007:read_memory=32'h00018500;
72'h080000000400000008:read_memory=32'h0000ee00;
72'h080000000400000009:read_memory=32'hffffcc00;
72'h08000000040000000a:read_memory=32'h0000cd00;
72'h08000000040000000b:read_memory=32'h0000a700;
72'h08000000040000000c:read_memory=32'hfffe3c00;
72'h08000000040000000d:read_memory=32'h00009900;
72'h08000000040000000e:read_memory=32'h00017a00;
72'h08000000040000000f:read_memory=32'h0000f200;
72'h090000000000000000:read_memory=32'hfffeaa00;
72'h090000000000000001:read_memory=32'hffff8e00;
72'h090000000000000002:read_memory=32'h00002600;
72'h090000000000000003:read_memory=32'h00015c00;
72'h090000000000000004:read_memory=32'hfffdb200;
72'h090000000000000005:read_memory=32'h0001d900;
72'h090000000000000006:read_memory=32'hfffe2600;
72'h090000000000000007:read_memory=32'h00013300;
72'h090000000000000008:read_memory=32'hffff6000;
72'h090000000000000009:read_memory=32'hffffad00;
72'h09000000000000000a:read_memory=32'h0000b300;
72'h09000000000000000b:read_memory=32'h00004f00;
72'h09000000000000000c:read_memory=32'hfffe2700;
72'h09000000000000000d:read_memory=32'hffffb500;
72'h09000000000000000e:read_memory=32'hfffe9a00;
72'h09000000000000000f:read_memory=32'h0000f900;
72'h090000000100000000:read_memory=32'hfffdb400;
72'h090000000100000001:read_memory=32'h00022900;
72'h090000000100000002:read_memory=32'hfffe7d00;
72'h090000000100000003:read_memory=32'h0001b800;
72'h090000000100000004:read_memory=32'h0001ad00;
72'h090000000100000005:read_memory=32'h0000a900;
72'h090000000100000006:read_memory=32'hfffe0d00;
72'h090000000100000007:read_memory=32'hfffe5800;
72'h090000000100000008:read_memory=32'hfffec200;
72'h090000000100000009:read_memory=32'hfffee000;
72'h09000000010000000a:read_memory=32'hffffd800;
72'h09000000010000000b:read_memory=32'hfffde300;
72'h09000000010000000c:read_memory=32'h00012700;
72'h09000000010000000d:read_memory=32'hffffb000;
72'h09000000010000000e:read_memory=32'hffff9c00;
72'h09000000010000000f:read_memory=32'hffff5200;
72'h090000000200000000:read_memory=32'hfffebb00;
72'h090000000200000001:read_memory=32'h00025600;
72'h090000000200000002:read_memory=32'h00025000;
72'h090000000200000003:read_memory=32'hfffe0c00;
72'h090000000200000004:read_memory=32'hfffdf700;
72'h090000000200000005:read_memory=32'hfffdcc00;
72'h090000000200000006:read_memory=32'hffffdf00;
72'h090000000200000007:read_memory=32'h00004400;
72'h090000000200000008:read_memory=32'h0000c800;
72'h090000000200000009:read_memory=32'h0000ed00;
72'h09000000020000000a:read_memory=32'hfffffb00;
72'h09000000020000000b:read_memory=32'h00011500;
72'h09000000020000000c:read_memory=32'h00016a00;
72'h09000000020000000d:read_memory=32'h00012d00;
72'h09000000020000000e:read_memory=32'hfffeb100;
72'h09000000020000000f:read_memory=32'h00002500;
72'h090000000300000000:read_memory=32'h00753000;
72'h090000000300000001:read_memory=32'h00753000;
72'h090000000300000002:read_memory=32'h00753000;
72'h090000000300000003:read_memory=32'h00753000;
72'h090000000300000004:read_memory=32'h00753000;
72'h090000000300000005:read_memory=32'h00753000;
72'h090000000300000006:read_memory=32'h00753000;
72'h090000000300000007:read_memory=32'h00753000;
72'h090000000300000008:read_memory=32'h00753000;
72'h090000000300000009:read_memory=32'h00753000;
72'h09000000030000000a:read_memory=32'h00753000;
72'h09000000030000000b:read_memory=32'h00753000;
72'h09000000030000000c:read_memory=32'h00753000;
72'h09000000030000000d:read_memory=32'h00753000;
72'h09000000030000000e:read_memory=32'h00753000;
72'h09000000030000000f:read_memory=32'h00753000;
72'h0a0000000000000000:read_memory=32'h00010800;
72'h0a0000000000000001:read_memory=32'hfffdf900;
72'h0a0000000000000002:read_memory=32'h00004400;
72'h0a0000000000000003:read_memory=32'h0001c900;
72'h0a0000000000000004:read_memory=32'hfffe7300;
72'h0a0000000000000005:read_memory=32'h00010100;
72'h0a0000000000000006:read_memory=32'h00017900;
72'h0a0000000000000007:read_memory=32'h00014a00;
72'h0a0000000000000008:read_memory=32'h0001c600;
72'h0a0000000000000009:read_memory=32'hfffef300;
72'h0a000000000000000a:read_memory=32'hffff6500;
72'h0a000000000000000b:read_memory=32'h00020200;
72'h0a000000000000000c:read_memory=32'hffff1e00;
72'h0a000000000000000d:read_memory=32'hfffeb700;
72'h0a000000000000000e:read_memory=32'hffffbf00;
72'h0a000000000000000f:read_memory=32'hffff0900;
72'h0a0000000100000000:read_memory=32'h0001bc00;
72'h0a0000000100000001:read_memory=32'h0000e900;
72'h0a0000000100000002:read_memory=32'hffff7e00;
72'h0a0000000100000003:read_memory=32'hfffdab00;
72'h0a0000000100000004:read_memory=32'h0000ff00;
72'h0a0000000100000005:read_memory=32'h00001500;
72'h0a0000000100000006:read_memory=32'h00004f00;
72'h0a0000000100000007:read_memory=32'hfffeab00;
72'h0a0000000100000008:read_memory=32'h00004a00;
72'h0a0000000100000009:read_memory=32'h00010400;
72'h0a000000010000000a:read_memory=32'hffff8700;
72'h0a000000010000000b:read_memory=32'h0000d300;
72'h0a000000010000000c:read_memory=32'hfffe3900;
72'h0a000000010000000d:read_memory=32'hffffd500;
72'h0a000000010000000e:read_memory=32'hffff4f00;
72'h0a000000010000000f:read_memory=32'h00011100;
72'h0a0000000200000000:read_memory=32'hfffe1200;
72'h0a0000000200000001:read_memory=32'h00024d00;
72'h0a0000000200000002:read_memory=32'h0000de00;
72'h0a0000000200000003:read_memory=32'h00003d00;
72'h0a0000000200000004:read_memory=32'h00019100;
72'h0a0000000200000005:read_memory=32'h00020500;
72'h0a0000000200000006:read_memory=32'hfffe0d00;
72'h0a0000000200000007:read_memory=32'hffff5500;
72'h0a0000000200000008:read_memory=32'h00011900;
72'h0a0000000200000009:read_memory=32'hffff3c00;
72'h0a000000020000000a:read_memory=32'hffff1d00;
72'h0a000000020000000b:read_memory=32'hfffe8600;
72'h0a000000020000000c:read_memory=32'h0000bc00;
72'h0a000000020000000d:read_memory=32'h00014200;
72'h0a000000020000000e:read_memory=32'hffff5200;
72'h0a000000020000000f:read_memory=32'h0001b200;
72'h0a0000000300000000:read_memory=32'h00753000;
72'h0a0000000300000001:read_memory=32'h00753000;
72'h0a0000000300000002:read_memory=32'h00753000;
72'h0a0000000300000003:read_memory=32'h00753000;
72'h0a0000000300000004:read_memory=32'h00753000;
72'h0a0000000300000005:read_memory=32'h00753000;
72'h0a0000000300000006:read_memory=32'h00753000;
72'h0a0000000300000007:read_memory=32'h00753000;
72'h0a0000000300000008:read_memory=32'h00753000;
72'h0a0000000300000009:read_memory=32'h00753000;
72'h0a000000030000000a:read_memory=32'h00753000;
72'h0a000000030000000b:read_memory=32'h00753000;
72'h0a000000030000000c:read_memory=32'h00753000;
72'h0a000000030000000d:read_memory=32'h00753000;
72'h0a000000030000000e:read_memory=32'h00753000;
72'h0a000000030000000f:read_memory=32'h00753000;
 default: begin $fatal(1,"attention illegal address"); read_memory=0; end
 endcase
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

if(writes>=144 || mem_req_proj!==0 ||
 {4'd0,mem_req_kind,mem_req_row,mem_req_col,mem_req_wdata} !== expected[writes])
 $fatal(1,"ATTENTION write mismatch %0d",writes);
if(mem_req_kind==9) keys[mem_req_col]=mem_req_wdata;
if(mem_req_kind==10) vals[mem_req_col]=mem_req_wdata;

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
launch(0,2); if(writes!=144) $fatal(1,"attention coverage");
 if(accepted!=responses || pending || writes==0 || stalls==0 ||
    busy_holds==0 || bubbles==0)
   $fatal(1,"COVERAGE missing transfer/write/stall");
 $display("PASS public writes=%0d transactions=%0d stalls=%0d busy_holds=%0d bubbles=%0d",
   writes,accepted,stalls,busy_holds,bubbles);
 $finish;
end endmodule
