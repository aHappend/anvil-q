module tb;

reg clk=0; always #5 clk=~clk;
reg rst_n=0, cmd_valid=0; wire cmd_ready,done,error;
reg [31:0] cmd_layer=0,cmd_pos=0; reg [2:0] cmd_proj=0; reg [1:0] cmd_mode=0;
wire mem_req_valid,mem_req_write,mem_rsp_ready;
reg mem_req_ready=0,mem_rsp_valid=0,mem_rsp_error=0;
wire [3:0] mem_req_kind; wire [2:0] mem_req_proj;
wire [31:0] mem_req_layer,mem_req_row,mem_req_col,mem_req_wdata;
reg [31:0] mem_rsp_rdata=0;

reg new_sequence=1; wire logit_valid; reg logit_ready=0;
wire [31:0] logit_index; wire signed [31:0] logit_data;
integer observed_logits=0, ordinal=0, output_stalls=0, residual_vectors=0;
integer progress_kind=0, progress_slot=0, progress_layer=0, progress_token=0;
integer active_gemv_proj=-1, active_gemv_layer=0;
integer gemv_reads=0, gemv_zeros=0, gemv_scales=0, gemv_weights=0;
integer gemv_inputs=0,gemv_outputs=0,gemv_biases=0,gemv_groups=0,gemv_tiles=0;
reg was_logit_stalled=0; reg [63:0] held_logit;
reg [31:0] expected_logits[0:84];
initial $readmemh("/data/sufeng/anvil-q-line5/workspace_phase2/project/evidence/verification/functional/mutation-layer-logits.hex",expected_logits);
anvil_q1_top #(.NUM_LAYERS(2),.HIDDEN_SIZE(16),.INTERMEDIATE_SIZE(32),.NUM_Q_HEADS(4),.NUM_KV_HEADS(2),.HEAD_DIM(4),.GROUP_SIZE(8),.VOCAB_SIZE(17),.MAX_SEQ_LEN(4)) dut(

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
always @(negedge clk) logit_ready=rst_n && cycles%5!=0;
always @(posedge clk) if(rst_n) begin
 if(was_logit_stalled && {logit_valid,logit_index,logit_data} !== {1'b1,held_logit})
   $fatal(1,"LOGIT stall instability");
 was_logit_stalled=logit_valid && !logit_ready;
 held_logit={logit_index,logit_data};
 if(was_logit_stalled) output_stalls=output_stalls+1;
 if(logit_valid && logit_ready) begin
   if(logit_index !== observed_logits%17 ||
      logit_data !== expected_logits[observed_logits])
     $fatal(1,"LOGIT mismatch index %0d expected %h got %h",
       observed_logits,expected_logits[observed_logits],logit_data);
   observed_logits=observed_logits+1;
 end
end

integer cycles=0, writes=0, accepted=0, pending=0, delay_count=0;
integer stalls=0, responses=0, completions=0, busy_holds=0, bubbles=0;
reg [136:0] held; reg was_stalled=0;
reg [31:0] reply; reg [31:0] expected_value;

localparam H=16,I=32,G=8,S=4,KV=8,D=4;
reg [31:0] storage[0:4879];
reg [131:0] expected[0:2959];
initial begin $readmemh("/data/sufeng/anvil-q-line5/workspace_phase2/project/evidence/verification/functional/mutation-layer-memory.hex",storage); $readmemh("/data/sufeng/anvil-q-line5/workspace_phase2/project/evidence/verification/functional/mutation-layer-writes.hex",expected); end
function automatic integer addr(input [3:0] kind,input [31:0] layer,
 input [2:0] proj,input [31:0] row,col);
integer ni,no;
begin
 ni=(proj==6 ? I : H);
 no=(proj==1 || proj==2 ? KV : (proj==4 || proj==5 ? I : H));
 if(kind>11 || layer>=2) $fatal(1,"ADDRESS kind/layer");
 if(kind==0 && (layer!=0 || proj!=0 || row>=17 || col>=H))
   $fatal(1,"ADDRESS embedding");
 if(kind>=1 && kind<=3 && (proj>6 ||
    row>=(kind==1 ? ni : ni/G) || col>=(kind==3 ? no : no/8)))
   $fatal(1,"ADDRESS AWQ");
 if(kind==4 && (proj>2 || row!=0 || col>=no))
   $fatal(1,"ADDRESS QKV bias");
 if(kind>=5 && kind<=7 && (proj!=0 || row!=0 || col>=H ||
    (kind==7 && layer!=0))) $fatal(1,"ADDRESS norm");
 if(kind==8 && (layer!=0 || proj!=0 || row>=15 || row==13 ||
    col>=((row==3 || row==4) ? KV : ((row>=9 && row<=11) ? I : H))))
   $fatal(1,"ADDRESS scratch");
 if((kind==9 || kind==10) && (proj!=0 || row>=S || col>=KV))
   $fatal(1,"ADDRESS cache");
 if(kind==11 && (layer!=0 || proj!=0 || row>=S || col>=D))
   $fatal(1,"ADDRESS RoPE");
 case(kind) 0: addr=0+row*H+col;
1: addr=272+((layer*7+proj)*I+row)*(I/8)+col;
2: addr=2064+((layer*7+proj)*(I/G)+row)*(I/8)+col;
3: addr=2288+((layer*7+proj)*(I/G)+row)*I+col;
4: addr=4080+(layer*3+proj)*H+col;
5: addr=4176+layer*H+col;
6: addr=4208+layer*H+col;
7: addr=4240+col;
8: addr=4256+row*I+col;
9: addr=4736+(layer*S+row)*KV+col;
10: addr=4800+(layer*S+row)*KV+col;
11: addr=4864+row*D+col;
default: begin $fatal(1,"invalid kind"); addr=0; end
endcase end endfunction
function automatic [31:0] read_memory(input [3:0] kind,input [2:0] proj,
 input [31:0] row,col);
begin
 if(kind==9 || kind==10) begin
   if(row>cmd_pos) $fatal(1,"CAUSAL future-cache read");
 end
 if(kind==4 && proj>=3) $fatal(1,"FORBIDDEN O/MLP bias");
 read_memory=storage[addr(kind,mem_req_layer,proj,row,col)];
 if(^read_memory === 1'bx) $fatal(1,"uninitialized/illegal memory read");
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
   if(mem_req_layer>=2) $fatal(1,"layer out of range");
   
if(!mem_req_write && mem_req_wdata!==0) $fatal(1,"ADDRESS read wdata");
if(!mem_req_write && mem_req_kind==2) begin
 if(active_gemv_proj==-1) begin
   active_gemv_proj=mem_req_proj; active_gemv_layer=mem_req_layer;
   gemv_inputs=(mem_req_proj==6 ? 32 : 16);
   gemv_outputs=((mem_req_proj==1 || mem_req_proj==2) ? 8 :
                  ((mem_req_proj==4 || mem_req_proj==5) ? 32 : 16));
   gemv_groups=gemv_inputs/8; gemv_tiles=gemv_outputs/8;
   gemv_zeros=0; gemv_scales=0; gemv_weights=0; gemv_reads=0; gemv_biases=0;
 end
 if(mem_req_proj!==active_gemv_proj || mem_req_layer!==active_gemv_layer ||
    mem_req_row!==(gemv_zeros%gemv_groups) ||
    mem_req_col!==(gemv_zeros/gemv_groups))
   $fatal(1,"GEMV group/block metadata reload");
 gemv_zeros=gemv_zeros+1;
end
if(active_gemv_proj!=-1 && !mem_req_write) begin
 if(mem_req_kind==8) gemv_reads=gemv_reads+1;
 if(mem_req_kind==1) begin
   if(mem_req_row!==(gemv_weights%gemv_inputs) ||
      mem_req_col!==(gemv_weights/gemv_inputs))
     $fatal(1,"GEMV packed weight reuse/order");
   gemv_weights=gemv_weights+1;
 end
 if(mem_req_kind==3) begin
   if(mem_req_row!==((gemv_scales/8)%gemv_groups) ||
      mem_req_col!==((gemv_scales/(8*gemv_groups))*8+gemv_scales%8))
     $fatal(1,"GEMV scale metadata reload/order");
   gemv_scales=gemv_scales+1;
 end
 if(mem_req_kind==4) gemv_biases=gemv_biases+1;
end
accepted=accepted+1; pending=1; delay_count=(accepted%127==0 ? 2 : 0);
   if(accepted%8192==0) begin
     $display("PROGRESS accepted=%0d compared_writes=%0d completed=%0d cycles=%0d",
       accepted,writes,completions,cycles);
     $fflush();
   end
   if(mem_req_write) begin

if(writes>=2960 ||
 {mem_req_kind,mem_req_layer,mem_req_row,mem_req_col,mem_req_wdata} !== expected[writes])
 $fatal(1,"STACK write mismatch %0d kind %0d layer %0d row %0d col %0d got %h expected %h",
 writes,mem_req_kind,mem_req_layer,mem_req_row,mem_req_col,mem_req_wdata,expected[writes]);
if(mem_req_kind<8 || mem_req_kind>10 || mem_req_proj!==0)
 $fatal(1,"illegal memory write");
storage[addr(mem_req_kind,mem_req_layer,mem_req_proj,mem_req_row,mem_req_col)]=mem_req_wdata;

     
     if(mem_req_kind==8 &&
        (((mem_req_row==2 && active_gemv_proj==0) ||
          (mem_req_row==3 && active_gemv_proj==1) ||
          (mem_req_row==4 && active_gemv_proj==2) ||
          (mem_req_row==6 && active_gemv_proj==3) ||
          (mem_req_row==9 && active_gemv_proj==4) ||
          (mem_req_row==10 && active_gemv_proj==5) ||
          (mem_req_row==12 && active_gemv_proj==6)) &&
         mem_req_col==((mem_req_row==3 || mem_req_row==4) ? 7 :
           ((mem_req_row==9 || mem_req_row==10) ? 31 : 15))))
       begin
         progress_kind=1; progress_slot=mem_req_row;
         progress_layer=active_gemv_layer; progress_token=completions;
       end
     if(mem_req_kind==8 && mem_req_row==0 && mem_req_col==15)
       begin
         if(residual_vectors%3==0)
           progress_kind=2;
         else
           progress_kind=3;
         progress_layer=residual_vectors%3-1; progress_token=completions;
       end
     writes=writes+1; reply=0;
   end else begin
     reply=read_memory(mem_req_kind,mem_req_proj,mem_req_row,mem_req_col);
   end
 end else if(pending && delay_count>0) delay_count=delay_count-1;
 if(mem_rsp_valid && mem_rsp_ready) begin
   if(!pending || delay_count!=0) $fatal(1,"UNEXPECTED response");
   
   pending=0; responses=responses+1;
   if(progress_kind!=0) begin
     if(progress_kind==1) begin
       if(gemv_zeros!=gemv_tiles*gemv_groups ||
          gemv_scales!=8*gemv_tiles*gemv_groups ||
          gemv_weights!=gemv_tiles*gemv_inputs ||
          gemv_reads!=gemv_tiles*gemv_inputs ||
          gemv_biases!=(active_gemv_proj<3 ? gemv_outputs : 0))
         $fatal(1,"GEMV exact public transaction counts/reuse");
       $display("PROJECTION_ACK token=%0d layer=%0d slot=%0d accepted=%0d cycles=%0d",
         progress_token,progress_layer,progress_slot,accepted,cycles);
       active_gemv_proj=-1;
     end
     else if(progress_kind==2)
       $display("EMBEDDING_ACK token=%0d accepted=%0d cycles=%0d",
         progress_token,accepted,cycles);
     else
       $display("LAYER_ACK token=%0d layer=%0d accepted=%0d cycles=%0d",
         progress_token,progress_layer,accepted,cycles);
     if(progress_kind==2 || progress_kind==3) residual_vectors=residual_vectors+1;
     progress_kind=0;
     $fflush();
   end

 end
 if(done) begin
   if(error !== 0 || pending) $fatal(1,"unexpected completion error/outstanding");
   completions=completions+1;
$display("TOKEN completed=%0d accepted=%0d cycles=%0d",completions,accepted,cycles);
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
cmd_layer=9; new_sequence=1; launch(0,0);
cmd_layer=10; new_sequence=0; launch(0,1);
cmd_layer=11; new_sequence=0; launch(0,2);
cmd_layer=12; new_sequence=0; launch(0,3);
cmd_layer=13; new_sequence=1; launch(0,0);
if(writes!=2960 || observed_logits!=85 ||
 completions!=5) $fatal(1,"STACK coverage");

 if(accepted!=responses || pending || writes==0 || stalls==0 ||
    busy_holds==0 || bubbles==0)
   $fatal(1,"COVERAGE missing transfer/write/stall");
 $display("PASS public writes=%0d transactions=%0d stalls=%0d busy_holds=%0d bubbles=%0d",
   writes,accepted,stalls,busy_holds,bubbles);
 $finish;
end endmodule
