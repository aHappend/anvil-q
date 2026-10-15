module tb;

reg clk=0; always #5 clk=~clk;
reg rst_n=0, cmd_valid=0; wire cmd_ready,done,error;
reg [31:0] cmd_layer=0,cmd_pos=0; reg [2:0] cmd_proj=0; reg [1:0] cmd_mode=0;
wire mem_req_valid,mem_req_write,mem_rsp_ready;
reg mem_req_ready=0,mem_rsp_valid=0,mem_rsp_error=0;
wire [3:0] mem_req_kind; wire [2:0] mem_req_proj;
wire [31:0] mem_req_layer,mem_req_row,mem_req_col,mem_req_wdata;
reg [31:0] mem_rsp_rdata=0;
anvil_q1_w4a16_gemv #(.NUM_LAYERS(24),.HIDDEN_SIZE(64),.INTERMEDIATE_SIZE(64),.NUM_Q_HEADS(2),.NUM_KV_HEADS(2),.HEAD_DIM(32),.GROUP_SIZE(64),.MAX_SEQ_LEN(1)) dut(
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

integer checkpoint_fd;
initial begin
 checkpoint_fd=$fopen("/data/sufeng/anvil-q-line5/workspace_phase2/project/hf_qwen25_05b_awq_spec/official_weights/qwen25_05b_awq_official_slice.safetensors","rb");
 if(checkpoint_fd==0) $fatal(1,"checkpoint open failed");
end
function automatic [31:0] checkpoint_read(input [3:0] kind,
 input [31:0] layer,input [2:0] proj,input [31:0] row,col);
reg [63:0] offset;
integer width,status,byte_index,octet;
begin
 offset=0; width=0;
 case({kind,layer,proj})
39'h0000000000: begin
 if(row>=64 || col>=896)
   $fatal(1,"UNCOVERED model.embed_tokens.weight coordinate row=%0d col=%0d",row,col);
 offset=5576+(2*(64'd896*row+col));
 width=2;
end
39'h3800000000: begin
 if(row>=1 || col>=896)
   $fatal(1,"UNCOVERED model.norm.weight coordinate row=%0d col=%0d",row,col);
 offset=120264+(2*(64'd896*row+col));
 width=2;
end
39'h2800000000: begin
 if(row>=1 || col>=896)
   $fatal(1,"UNCOVERED model.layers.0.input_layernorm.weight coordinate row=%0d col=%0d",row,col);
 offset=122056+(2*(64'd896*row+col));
 width=2;
end
39'h3000000000: begin
 if(row>=1 || col>=896)
   $fatal(1,"UNCOVERED model.layers.0.post_attention_layernorm.weight coordinate row=%0d col=%0d",row,col);
 offset=123848+(2*(64'd896*row+col));
 width=2;
end
39'h2000000000: begin
 if(row>=1 || col>=896)
   $fatal(1,"UNCOVERED model.layers.0.self_attn.q_proj.bias coordinate row=%0d col=%0d",row,col);
 offset=125640+(2*(64'd896*row+col));
 width=2;
end
39'h2000000001: begin
 if(row>=1 || col>=128)
   $fatal(1,"UNCOVERED model.layers.0.self_attn.k_proj.bias coordinate row=%0d col=%0d",row,col);
 offset=127432+(2*(64'd128*row+col));
 width=2;
end
39'h2000000002: begin
 if(row>=1 || col>=128)
   $fatal(1,"UNCOVERED model.layers.0.self_attn.v_proj.bias coordinate row=%0d col=%0d",row,col);
 offset=127688+(2*(64'd128*row+col));
 width=2;
end
39'h0800000000: begin
 if(row>=64 || col>=112)
   $fatal(1,"UNCOVERED model.layers.0.self_attn.q_proj.qweight coordinate row=%0d col=%0d",row,col);
 offset=127944+(4*(64'd112*row+col));
 width=4;
end
39'h1000000000: begin
 if(row>=7 || col>=112)
   $fatal(1,"UNCOVERED model.layers.0.self_attn.q_proj.qzeros coordinate row=%0d col=%0d",row,col);
 offset=156616+(4*(64'd112*row+col));
 width=4;
end
39'h1800000000: begin
 if(row>=7 || col>=896)
   $fatal(1,"UNCOVERED model.layers.0.self_attn.q_proj.scales coordinate row=%0d col=%0d",row,col);
 offset=159752+(2*(64'd896*row+col));
 width=2;
end
39'h0800000001: begin
 if(row>=64 || col>=16)
   $fatal(1,"UNCOVERED model.layers.0.self_attn.k_proj.qweight coordinate row=%0d col=%0d",row,col);
 offset=172296+(4*(64'd16*row+col));
 width=4;
end
39'h1000000001: begin
 if(row>=7 || col>=16)
   $fatal(1,"UNCOVERED model.layers.0.self_attn.k_proj.qzeros coordinate row=%0d col=%0d",row,col);
 offset=176392+(4*(64'd16*row+col));
 width=4;
end
39'h1800000001: begin
 if(row>=7 || col>=128)
   $fatal(1,"UNCOVERED model.layers.0.self_attn.k_proj.scales coordinate row=%0d col=%0d",row,col);
 offset=176840+(2*(64'd128*row+col));
 width=2;
end
39'h0800000002: begin
 if(row>=64 || col>=16)
   $fatal(1,"UNCOVERED model.layers.0.self_attn.v_proj.qweight coordinate row=%0d col=%0d",row,col);
 offset=178632+(4*(64'd16*row+col));
 width=4;
end
39'h1000000002: begin
 if(row>=7 || col>=16)
   $fatal(1,"UNCOVERED model.layers.0.self_attn.v_proj.qzeros coordinate row=%0d col=%0d",row,col);
 offset=182728+(4*(64'd16*row+col));
 width=4;
end
39'h1800000002: begin
 if(row>=7 || col>=128)
   $fatal(1,"UNCOVERED model.layers.0.self_attn.v_proj.scales coordinate row=%0d col=%0d",row,col);
 offset=183176+(2*(64'd128*row+col));
 width=2;
end
39'h0800000003: begin
 if(row>=64 || col>=112)
   $fatal(1,"UNCOVERED model.layers.0.self_attn.o_proj.qweight coordinate row=%0d col=%0d",row,col);
 offset=184968+(4*(64'd112*row+col));
 width=4;
end
39'h1000000003: begin
 if(row>=7 || col>=112)
   $fatal(1,"UNCOVERED model.layers.0.self_attn.o_proj.qzeros coordinate row=%0d col=%0d",row,col);
 offset=213640+(4*(64'd112*row+col));
 width=4;
end
39'h1800000003: begin
 if(row>=7 || col>=896)
   $fatal(1,"UNCOVERED model.layers.0.self_attn.o_proj.scales coordinate row=%0d col=%0d",row,col);
 offset=216776+(2*(64'd896*row+col));
 width=2;
end
39'h0800000004: begin
 if(row>=64 || col>=608)
   $fatal(1,"UNCOVERED model.layers.0.mlp.gate_proj.qweight coordinate row=%0d col=%0d",row,col);
 offset=229320+(4*(64'd608*row+col));
 width=4;
end
39'h1000000004: begin
 if(row>=7 || col>=608)
   $fatal(1,"UNCOVERED model.layers.0.mlp.gate_proj.qzeros coordinate row=%0d col=%0d",row,col);
 offset=384968+(4*(64'd608*row+col));
 width=4;
end
39'h1800000004: begin
 if(row>=7 || col>=4864)
   $fatal(1,"UNCOVERED model.layers.0.mlp.gate_proj.scales coordinate row=%0d col=%0d",row,col);
 offset=401992+(2*(64'd4864*row+col));
 width=2;
end
39'h0800000005: begin
 if(row>=64 || col>=608)
   $fatal(1,"UNCOVERED model.layers.0.mlp.up_proj.qweight coordinate row=%0d col=%0d",row,col);
 offset=470088+(4*(64'd608*row+col));
 width=4;
end
39'h1000000005: begin
 if(row>=7 || col>=608)
   $fatal(1,"UNCOVERED model.layers.0.mlp.up_proj.qzeros coordinate row=%0d col=%0d",row,col);
 offset=625736+(4*(64'd608*row+col));
 width=4;
end
39'h1800000005: begin
 if(row>=7 || col>=4864)
   $fatal(1,"UNCOVERED model.layers.0.mlp.up_proj.scales coordinate row=%0d col=%0d",row,col);
 offset=642760+(2*(64'd4864*row+col));
 width=2;
end
39'h0800000006: begin
 if(row>=64 || col>=112)
   $fatal(1,"UNCOVERED model.layers.0.mlp.down_proj.qweight coordinate row=%0d col=%0d",row,col);
 offset=710856+(4*(64'd112*row+col));
 width=4;
end
39'h1000000006: begin
 if(row>=38 || col>=112)
   $fatal(1,"UNCOVERED model.layers.0.mlp.down_proj.qzeros coordinate row=%0d col=%0d",row,col);
 offset=739528+(4*(64'd112*row+col));
 width=4;
end
39'h1800000006: begin
 if(row>=38 || col>=896)
   $fatal(1,"UNCOVERED model.layers.0.mlp.down_proj.scales coordinate row=%0d col=%0d",row,col);
 offset=756552+(2*(64'd896*row+col));
 width=2;
end
39'h28000000b8: begin
 if(row>=1 || col>=896)
   $fatal(1,"UNCOVERED model.layers.23.input_layernorm.weight coordinate row=%0d col=%0d",row,col);
 offset=824648+(2*(64'd896*row+col));
 width=2;
end
39'h30000000b8: begin
 if(row>=1 || col>=896)
   $fatal(1,"UNCOVERED model.layers.23.post_attention_layernorm.weight coordinate row=%0d col=%0d",row,col);
 offset=826440+(2*(64'd896*row+col));
 width=2;
end
39'h20000000b8: begin
 if(row>=1 || col>=896)
   $fatal(1,"UNCOVERED model.layers.23.self_attn.q_proj.bias coordinate row=%0d col=%0d",row,col);
 offset=828232+(2*(64'd896*row+col));
 width=2;
end
39'h20000000b9: begin
 if(row>=1 || col>=128)
   $fatal(1,"UNCOVERED model.layers.23.self_attn.k_proj.bias coordinate row=%0d col=%0d",row,col);
 offset=830024+(2*(64'd128*row+col));
 width=2;
end
39'h20000000ba: begin
 if(row>=1 || col>=128)
   $fatal(1,"UNCOVERED model.layers.23.self_attn.v_proj.bias coordinate row=%0d col=%0d",row,col);
 offset=830280+(2*(64'd128*row+col));
 width=2;
end
39'h08000000b8: begin
 if(row>=64 || col>=112)
   $fatal(1,"UNCOVERED model.layers.23.self_attn.q_proj.qweight coordinate row=%0d col=%0d",row,col);
 offset=830536+(4*(64'd112*row+col));
 width=4;
end
39'h10000000b8: begin
 if(row>=7 || col>=112)
   $fatal(1,"UNCOVERED model.layers.23.self_attn.q_proj.qzeros coordinate row=%0d col=%0d",row,col);
 offset=859208+(4*(64'd112*row+col));
 width=4;
end
39'h18000000b8: begin
 if(row>=7 || col>=896)
   $fatal(1,"UNCOVERED model.layers.23.self_attn.q_proj.scales coordinate row=%0d col=%0d",row,col);
 offset=862344+(2*(64'd896*row+col));
 width=2;
end
39'h08000000b9: begin
 if(row>=64 || col>=16)
   $fatal(1,"UNCOVERED model.layers.23.self_attn.k_proj.qweight coordinate row=%0d col=%0d",row,col);
 offset=874888+(4*(64'd16*row+col));
 width=4;
end
39'h10000000b9: begin
 if(row>=7 || col>=16)
   $fatal(1,"UNCOVERED model.layers.23.self_attn.k_proj.qzeros coordinate row=%0d col=%0d",row,col);
 offset=878984+(4*(64'd16*row+col));
 width=4;
end
39'h18000000b9: begin
 if(row>=7 || col>=128)
   $fatal(1,"UNCOVERED model.layers.23.self_attn.k_proj.scales coordinate row=%0d col=%0d",row,col);
 offset=879432+(2*(64'd128*row+col));
 width=2;
end
39'h08000000ba: begin
 if(row>=64 || col>=16)
   $fatal(1,"UNCOVERED model.layers.23.self_attn.v_proj.qweight coordinate row=%0d col=%0d",row,col);
 offset=881224+(4*(64'd16*row+col));
 width=4;
end
39'h10000000ba: begin
 if(row>=7 || col>=16)
   $fatal(1,"UNCOVERED model.layers.23.self_attn.v_proj.qzeros coordinate row=%0d col=%0d",row,col);
 offset=885320+(4*(64'd16*row+col));
 width=4;
end
39'h18000000ba: begin
 if(row>=7 || col>=128)
   $fatal(1,"UNCOVERED model.layers.23.self_attn.v_proj.scales coordinate row=%0d col=%0d",row,col);
 offset=885768+(2*(64'd128*row+col));
 width=2;
end
39'h08000000bb: begin
 if(row>=64 || col>=112)
   $fatal(1,"UNCOVERED model.layers.23.self_attn.o_proj.qweight coordinate row=%0d col=%0d",row,col);
 offset=887560+(4*(64'd112*row+col));
 width=4;
end
39'h10000000bb: begin
 if(row>=7 || col>=112)
   $fatal(1,"UNCOVERED model.layers.23.self_attn.o_proj.qzeros coordinate row=%0d col=%0d",row,col);
 offset=916232+(4*(64'd112*row+col));
 width=4;
end
39'h18000000bb: begin
 if(row>=7 || col>=896)
   $fatal(1,"UNCOVERED model.layers.23.self_attn.o_proj.scales coordinate row=%0d col=%0d",row,col);
 offset=919368+(2*(64'd896*row+col));
 width=2;
end
39'h08000000bc: begin
 if(row>=64 || col>=608)
   $fatal(1,"UNCOVERED model.layers.23.mlp.gate_proj.qweight coordinate row=%0d col=%0d",row,col);
 offset=931912+(4*(64'd608*row+col));
 width=4;
end
39'h10000000bc: begin
 if(row>=7 || col>=608)
   $fatal(1,"UNCOVERED model.layers.23.mlp.gate_proj.qzeros coordinate row=%0d col=%0d",row,col);
 offset=1087560+(4*(64'd608*row+col));
 width=4;
end
39'h18000000bc: begin
 if(row>=7 || col>=4864)
   $fatal(1,"UNCOVERED model.layers.23.mlp.gate_proj.scales coordinate row=%0d col=%0d",row,col);
 offset=1104584+(2*(64'd4864*row+col));
 width=2;
end
39'h08000000bd: begin
 if(row>=64 || col>=608)
   $fatal(1,"UNCOVERED model.layers.23.mlp.up_proj.qweight coordinate row=%0d col=%0d",row,col);
 offset=1172680+(4*(64'd608*row+col));
 width=4;
end
39'h10000000bd: begin
 if(row>=7 || col>=608)
   $fatal(1,"UNCOVERED model.layers.23.mlp.up_proj.qzeros coordinate row=%0d col=%0d",row,col);
 offset=1328328+(4*(64'd608*row+col));
 width=4;
end
39'h18000000bd: begin
 if(row>=7 || col>=4864)
   $fatal(1,"UNCOVERED model.layers.23.mlp.up_proj.scales coordinate row=%0d col=%0d",row,col);
 offset=1345352+(2*(64'd4864*row+col));
 width=2;
end
39'h08000000be: begin
 if(row>=64 || col>=112)
   $fatal(1,"UNCOVERED model.layers.23.mlp.down_proj.qweight coordinate row=%0d col=%0d",row,col);
 offset=1413448+(4*(64'd112*row+col));
 width=4;
end
39'h10000000be: begin
 if(row>=38 || col>=112)
   $fatal(1,"UNCOVERED model.layers.23.mlp.down_proj.qzeros coordinate row=%0d col=%0d",row,col);
 offset=1442120+(4*(64'd112*row+col));
 width=4;
end
39'h18000000be: begin
 if(row>=38 || col>=896)
   $fatal(1,"UNCOVERED model.layers.23.mlp.down_proj.scales coordinate row=%0d col=%0d",row,col);
 offset=1459144+(2*(64'd896*row+col));
 width=2;
end
 default: $fatal(1,"UNCOVERED model address kind=%0d layer=%0d proj=%0d row=%0d col=%0d",
                  kind,layer,proj,row,col);
 endcase
 status=$fseek(checkpoint_fd,offset,0);
 if(status!=0) $fatal(1,"checkpoint seek failure");
 checkpoint_read=0;
 for(byte_index=0;byte_index<width;byte_index=byte_index+1) begin
   octet=$fgetc(checkpoint_fd);
   if(octet<0) $fatal(1,"checkpoint truncated payload");
   checkpoint_read=checkpoint_read | (octet << (8*byte_index));
 end
end endfunction

reg [95:0] expected[0:895];
initial $readmemh("/data/sufeng/anvil-q-line5/workspace_phase2/project/evidence/preparation/verifier-phase2-raw-integration-03/raw-official-submatrix-writes.hex",expected);
function automatic [31:0] read_memory(input [3:0] kind,input [2:0] proj,
 input [31:0] row,col);
begin
 if(kind==8) begin
   if(proj!=0 || col>=64 ||
      row!=(cmd_proj==3 ? 5 : (cmd_proj==6 ? 11 : (cmd_proj>=4 ? 8 : 1))))
     $fatal(1,"RAW SUBMATRIX activation address");
   read_memory=((col*67)%509-254)*256;
 end else begin
   if(kind<1 || kind>4 || proj!==cmd_proj ||
      (mem_req_layer!=0 && mem_req_layer!=23) ||
      row>=(kind==1 ? 64 : 1) || col>=(kind==1 || kind==2 ? 8 : 64))
     $fatal(1,"RAW SUBMATRIX model address");
   read_memory=checkpoint_read(kind,mem_req_layer,proj,row,col);
 end
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
   if(mem_req_layer!==(mem_req_kind==8 ? 32'd0 : cmd_layer)) $fatal(1,"literal official layer/unused scratch layer mismatch");
   accepted=accepted+1; pending=1; delay_count=(accepted%127==0 ? 2 : 0);
   if(accepted%262144==0) begin
     $display("PROGRESS accepted=%0d compared_writes=%0d completed=%0d cycles=%0d",
       accepted,writes,completions,cycles);
     $fflush();
   end
   if(mem_req_write) begin

if(writes>=896 || mem_req_kind!==8 || mem_req_proj!==0 ||
   {mem_req_row,mem_req_col,mem_req_wdata} !== expected[writes])
 $fatal(1,"RAW OFFICIAL SUBMATRIX write mismatch %0d",writes);

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
cmd_layer=0; launch(0,0);
cmd_layer=0; launch(1,0);
cmd_layer=0; launch(2,0);
cmd_layer=0; launch(3,0);
cmd_layer=0; launch(4,0);
cmd_layer=0; launch(5,0);
cmd_layer=0; launch(6,0);
cmd_layer=23; launch(0,0);
cmd_layer=23; launch(1,0);
cmd_layer=23; launch(2,0);
cmd_layer=23; launch(3,0);
cmd_layer=23; launch(4,0);
cmd_layer=23; launch(5,0);
cmd_layer=23; launch(6,0);
if(writes!=896 || completions!=14)
 $fatal(1,"RAW OFFICIAL SUBMATRIX incomplete commands");

 if(accepted!=responses || pending || writes==0 || stalls==0 ||
    busy_holds==0 || bubbles==0)
   $fatal(1,"COVERAGE missing transfer/write/stall");
 $display("PASS public writes=%0d transactions=%0d stalls=%0d busy_holds=%0d bubbles=%0d",
   writes,accepted,stalls,busy_holds,bubbles);
 $finish;
end endmodule
