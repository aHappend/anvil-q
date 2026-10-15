module tb;

reg clk=0; always #5 clk=~clk;
reg rst_n=0, cmd_valid=0; wire cmd_ready,done,error;
reg [31:0] cmd_layer=0,cmd_pos=0; reg [2:0] cmd_proj=0; reg [1:0] cmd_mode=0;
wire mem_req_valid,mem_req_write,mem_rsp_ready;
reg mem_req_ready=0,mem_rsp_valid=0,mem_rsp_error=0;
wire [3:0] mem_req_kind; wire [2:0] mem_req_proj;
wire [31:0] mem_req_layer,mem_req_row,mem_req_col,mem_req_wdata;
reg [31:0] mem_rsp_rdata=0;

reg new_sequence=0,logit_ready=0;
wire logit_valid; wire [31:0] logit_index; wire signed [31:0] logit_data;
anvil_q1_top #(.NUM_LAYERS(2),.HIDDEN_SIZE(8),.INTERMEDIATE_SIZE(8),.NUM_Q_HEADS(2),.NUM_KV_HEADS(2),.HEAD_DIM(4),.GROUP_SIZE(8),.VOCAB_SIZE(8),.MAX_SEQ_LEN(4)) dut(
.clk(clk),.rst_n(rst_n),.token_valid(cmd_valid),.token_ready(cmd_ready),
.token_id(cmd_layer),.token_pos(cmd_pos),.done(done),.error(error),
.mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),
.mem_req_write(mem_req_write),.mem_req_kind(mem_req_kind),
.mem_req_layer(mem_req_layer),.mem_req_proj(mem_req_proj),
.mem_req_row(mem_req_row),.mem_req_col(mem_req_col),.mem_req_wdata(mem_req_wdata),
.mem_rsp_valid(mem_rsp_valid),.mem_rsp_ready(mem_rsp_ready),
.mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_error(mem_rsp_error)
,.new_sequence(new_sequence),
 .logit_valid(logit_valid),.logit_ready(logit_ready),
 .logit_index(logit_index),.logit_data(logit_data));
integer observed_logits=0, accepted_tokens=0,final_transfers=0;
integer active_token=-1,start_edge=0,final_edge=0;
integer logit_stalls=0,response_stalls=0,request_stalls=0;
integer bin_index=0,pending_bin=0,index_init=0,print_index=0;
integer requests_by_address[0:1535],responses_by_address[0:1535];
reg [31:0] expected_logits[0:31];
reg logit_held=0; reg [63:0] logit_payload;
initial begin
 $readmemh("/data/sufeng/anvil-q-line5/workspace_phase2/project/evidence/preparation/verifier-phase2-final-integration-01/synthetic-file-backed-top-logits.hex",expected_logits);
 for(index_init=0;index_init<1536;index_init=index_init+1) begin
   requests_by_address[index_init]=0; responses_by_address[index_init]=0;
 end
end
always @(negedge clk) logit_ready=rst_n && cycles%5!=0;
function automatic integer counter_bin(input integer token,kind,write_access,layer,proj);
begin counter_bin=((((token*12+kind)*2+write_access)*2+layer)*8+proj); end
endfunction

integer cycles=0, writes=0, accepted=0, pending=0, delay_count=0;
integer stalls=0, responses=0, completions=0, busy_holds=0, bubbles=0;
reg [136:0] held; reg was_stalled=0;
reg [31:0] reply; reg [31:0] expected_value;

integer checkpoint_fd;
initial begin
 checkpoint_fd=$fopen("/data/sufeng/anvil-q-line5/workspace_phase2/project/evidence/preparation/verifier-phase2-final-integration-01/SYNTHETIC-NOT-OFFICIAL-path-fixture.safetensors","rb");
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
 if(row>=8 || col>=8)
   $fatal(1,"UNCOVERED model.embed_tokens.weight coordinate row=%0d col=%0d",row,col);
 offset=5096+(2*(64'd8*row+col));
 width=2;
end
39'h3800000000: begin
 if(row>=1 || col>=8)
   $fatal(1,"UNCOVERED model.norm.weight coordinate row=%0d col=%0d",row,col);
 offset=5224+(2*(64'd8*row+col));
 width=2;
end
39'h2800000000: begin
 if(row>=1 || col>=8)
   $fatal(1,"UNCOVERED model.layers.0.input_layernorm.weight coordinate row=%0d col=%0d",row,col);
 offset=5240+(2*(64'd8*row+col));
 width=2;
end
39'h3000000000: begin
 if(row>=1 || col>=8)
   $fatal(1,"UNCOVERED model.layers.0.post_attention_layernorm.weight coordinate row=%0d col=%0d",row,col);
 offset=5256+(2*(64'd8*row+col));
 width=2;
end
39'h0800000000: begin
 if(row>=8 || col>=1)
   $fatal(1,"UNCOVERED model.layers.0.self_attn.q_proj.qweight coordinate row=%0d col=%0d",row,col);
 offset=5272+(4*(64'd1*row+col));
 width=4;
end
39'h1000000000: begin
 if(row>=1 || col>=1)
   $fatal(1,"UNCOVERED model.layers.0.self_attn.q_proj.qzeros coordinate row=%0d col=%0d",row,col);
 offset=5304+(4*(64'd1*row+col));
 width=4;
end
39'h1800000000: begin
 if(row>=1 || col>=8)
   $fatal(1,"UNCOVERED model.layers.0.self_attn.q_proj.scales coordinate row=%0d col=%0d",row,col);
 offset=5308+(2*(64'd8*row+col));
 width=2;
end
39'h2000000000: begin
 if(row>=1 || col>=8)
   $fatal(1,"UNCOVERED model.layers.0.self_attn.q_proj.bias coordinate row=%0d col=%0d",row,col);
 offset=5324+(2*(64'd8*row+col));
 width=2;
end
39'h0800000001: begin
 if(row>=8 || col>=1)
   $fatal(1,"UNCOVERED model.layers.0.self_attn.k_proj.qweight coordinate row=%0d col=%0d",row,col);
 offset=5340+(4*(64'd1*row+col));
 width=4;
end
39'h1000000001: begin
 if(row>=1 || col>=1)
   $fatal(1,"UNCOVERED model.layers.0.self_attn.k_proj.qzeros coordinate row=%0d col=%0d",row,col);
 offset=5372+(4*(64'd1*row+col));
 width=4;
end
39'h1800000001: begin
 if(row>=1 || col>=8)
   $fatal(1,"UNCOVERED model.layers.0.self_attn.k_proj.scales coordinate row=%0d col=%0d",row,col);
 offset=5376+(2*(64'd8*row+col));
 width=2;
end
39'h2000000001: begin
 if(row>=1 || col>=8)
   $fatal(1,"UNCOVERED model.layers.0.self_attn.k_proj.bias coordinate row=%0d col=%0d",row,col);
 offset=5392+(2*(64'd8*row+col));
 width=2;
end
39'h0800000002: begin
 if(row>=8 || col>=1)
   $fatal(1,"UNCOVERED model.layers.0.self_attn.v_proj.qweight coordinate row=%0d col=%0d",row,col);
 offset=5408+(4*(64'd1*row+col));
 width=4;
end
39'h1000000002: begin
 if(row>=1 || col>=1)
   $fatal(1,"UNCOVERED model.layers.0.self_attn.v_proj.qzeros coordinate row=%0d col=%0d",row,col);
 offset=5440+(4*(64'd1*row+col));
 width=4;
end
39'h1800000002: begin
 if(row>=1 || col>=8)
   $fatal(1,"UNCOVERED model.layers.0.self_attn.v_proj.scales coordinate row=%0d col=%0d",row,col);
 offset=5444+(2*(64'd8*row+col));
 width=2;
end
39'h2000000002: begin
 if(row>=1 || col>=8)
   $fatal(1,"UNCOVERED model.layers.0.self_attn.v_proj.bias coordinate row=%0d col=%0d",row,col);
 offset=5460+(2*(64'd8*row+col));
 width=2;
end
39'h0800000003: begin
 if(row>=8 || col>=1)
   $fatal(1,"UNCOVERED model.layers.0.self_attn.o_proj.qweight coordinate row=%0d col=%0d",row,col);
 offset=5476+(4*(64'd1*row+col));
 width=4;
end
39'h1000000003: begin
 if(row>=1 || col>=1)
   $fatal(1,"UNCOVERED model.layers.0.self_attn.o_proj.qzeros coordinate row=%0d col=%0d",row,col);
 offset=5508+(4*(64'd1*row+col));
 width=4;
end
39'h1800000003: begin
 if(row>=1 || col>=8)
   $fatal(1,"UNCOVERED model.layers.0.self_attn.o_proj.scales coordinate row=%0d col=%0d",row,col);
 offset=5512+(2*(64'd8*row+col));
 width=2;
end
39'h0800000004: begin
 if(row>=8 || col>=1)
   $fatal(1,"UNCOVERED model.layers.0.mlp.gate_proj.qweight coordinate row=%0d col=%0d",row,col);
 offset=5528+(4*(64'd1*row+col));
 width=4;
end
39'h1000000004: begin
 if(row>=1 || col>=1)
   $fatal(1,"UNCOVERED model.layers.0.mlp.gate_proj.qzeros coordinate row=%0d col=%0d",row,col);
 offset=5560+(4*(64'd1*row+col));
 width=4;
end
39'h1800000004: begin
 if(row>=1 || col>=8)
   $fatal(1,"UNCOVERED model.layers.0.mlp.gate_proj.scales coordinate row=%0d col=%0d",row,col);
 offset=5564+(2*(64'd8*row+col));
 width=2;
end
39'h0800000005: begin
 if(row>=8 || col>=1)
   $fatal(1,"UNCOVERED model.layers.0.mlp.up_proj.qweight coordinate row=%0d col=%0d",row,col);
 offset=5580+(4*(64'd1*row+col));
 width=4;
end
39'h1000000005: begin
 if(row>=1 || col>=1)
   $fatal(1,"UNCOVERED model.layers.0.mlp.up_proj.qzeros coordinate row=%0d col=%0d",row,col);
 offset=5612+(4*(64'd1*row+col));
 width=4;
end
39'h1800000005: begin
 if(row>=1 || col>=8)
   $fatal(1,"UNCOVERED model.layers.0.mlp.up_proj.scales coordinate row=%0d col=%0d",row,col);
 offset=5616+(2*(64'd8*row+col));
 width=2;
end
39'h0800000006: begin
 if(row>=8 || col>=1)
   $fatal(1,"UNCOVERED model.layers.0.mlp.down_proj.qweight coordinate row=%0d col=%0d",row,col);
 offset=5632+(4*(64'd1*row+col));
 width=4;
end
39'h1000000006: begin
 if(row>=1 || col>=1)
   $fatal(1,"UNCOVERED model.layers.0.mlp.down_proj.qzeros coordinate row=%0d col=%0d",row,col);
 offset=5664+(4*(64'd1*row+col));
 width=4;
end
39'h1800000006: begin
 if(row>=1 || col>=8)
   $fatal(1,"UNCOVERED model.layers.0.mlp.down_proj.scales coordinate row=%0d col=%0d",row,col);
 offset=5668+(2*(64'd8*row+col));
 width=2;
end
39'h2800000008: begin
 if(row>=1 || col>=8)
   $fatal(1,"UNCOVERED model.layers.1.input_layernorm.weight coordinate row=%0d col=%0d",row,col);
 offset=5684+(2*(64'd8*row+col));
 width=2;
end
39'h3000000008: begin
 if(row>=1 || col>=8)
   $fatal(1,"UNCOVERED model.layers.1.post_attention_layernorm.weight coordinate row=%0d col=%0d",row,col);
 offset=5700+(2*(64'd8*row+col));
 width=2;
end
39'h0800000008: begin
 if(row>=8 || col>=1)
   $fatal(1,"UNCOVERED model.layers.1.self_attn.q_proj.qweight coordinate row=%0d col=%0d",row,col);
 offset=5716+(4*(64'd1*row+col));
 width=4;
end
39'h1000000008: begin
 if(row>=1 || col>=1)
   $fatal(1,"UNCOVERED model.layers.1.self_attn.q_proj.qzeros coordinate row=%0d col=%0d",row,col);
 offset=5748+(4*(64'd1*row+col));
 width=4;
end
39'h1800000008: begin
 if(row>=1 || col>=8)
   $fatal(1,"UNCOVERED model.layers.1.self_attn.q_proj.scales coordinate row=%0d col=%0d",row,col);
 offset=5752+(2*(64'd8*row+col));
 width=2;
end
39'h2000000008: begin
 if(row>=1 || col>=8)
   $fatal(1,"UNCOVERED model.layers.1.self_attn.q_proj.bias coordinate row=%0d col=%0d",row,col);
 offset=5768+(2*(64'd8*row+col));
 width=2;
end
39'h0800000009: begin
 if(row>=8 || col>=1)
   $fatal(1,"UNCOVERED model.layers.1.self_attn.k_proj.qweight coordinate row=%0d col=%0d",row,col);
 offset=5784+(4*(64'd1*row+col));
 width=4;
end
39'h1000000009: begin
 if(row>=1 || col>=1)
   $fatal(1,"UNCOVERED model.layers.1.self_attn.k_proj.qzeros coordinate row=%0d col=%0d",row,col);
 offset=5816+(4*(64'd1*row+col));
 width=4;
end
39'h1800000009: begin
 if(row>=1 || col>=8)
   $fatal(1,"UNCOVERED model.layers.1.self_attn.k_proj.scales coordinate row=%0d col=%0d",row,col);
 offset=5820+(2*(64'd8*row+col));
 width=2;
end
39'h2000000009: begin
 if(row>=1 || col>=8)
   $fatal(1,"UNCOVERED model.layers.1.self_attn.k_proj.bias coordinate row=%0d col=%0d",row,col);
 offset=5836+(2*(64'd8*row+col));
 width=2;
end
39'h080000000a: begin
 if(row>=8 || col>=1)
   $fatal(1,"UNCOVERED model.layers.1.self_attn.v_proj.qweight coordinate row=%0d col=%0d",row,col);
 offset=5852+(4*(64'd1*row+col));
 width=4;
end
39'h100000000a: begin
 if(row>=1 || col>=1)
   $fatal(1,"UNCOVERED model.layers.1.self_attn.v_proj.qzeros coordinate row=%0d col=%0d",row,col);
 offset=5884+(4*(64'd1*row+col));
 width=4;
end
39'h180000000a: begin
 if(row>=1 || col>=8)
   $fatal(1,"UNCOVERED model.layers.1.self_attn.v_proj.scales coordinate row=%0d col=%0d",row,col);
 offset=5888+(2*(64'd8*row+col));
 width=2;
end
39'h200000000a: begin
 if(row>=1 || col>=8)
   $fatal(1,"UNCOVERED model.layers.1.self_attn.v_proj.bias coordinate row=%0d col=%0d",row,col);
 offset=5904+(2*(64'd8*row+col));
 width=2;
end
39'h080000000b: begin
 if(row>=8 || col>=1)
   $fatal(1,"UNCOVERED model.layers.1.self_attn.o_proj.qweight coordinate row=%0d col=%0d",row,col);
 offset=5920+(4*(64'd1*row+col));
 width=4;
end
39'h100000000b: begin
 if(row>=1 || col>=1)
   $fatal(1,"UNCOVERED model.layers.1.self_attn.o_proj.qzeros coordinate row=%0d col=%0d",row,col);
 offset=5952+(4*(64'd1*row+col));
 width=4;
end
39'h180000000b: begin
 if(row>=1 || col>=8)
   $fatal(1,"UNCOVERED model.layers.1.self_attn.o_proj.scales coordinate row=%0d col=%0d",row,col);
 offset=5956+(2*(64'd8*row+col));
 width=2;
end
39'h080000000c: begin
 if(row>=8 || col>=1)
   $fatal(1,"UNCOVERED model.layers.1.mlp.gate_proj.qweight coordinate row=%0d col=%0d",row,col);
 offset=5972+(4*(64'd1*row+col));
 width=4;
end
39'h100000000c: begin
 if(row>=1 || col>=1)
   $fatal(1,"UNCOVERED model.layers.1.mlp.gate_proj.qzeros coordinate row=%0d col=%0d",row,col);
 offset=6004+(4*(64'd1*row+col));
 width=4;
end
39'h180000000c: begin
 if(row>=1 || col>=8)
   $fatal(1,"UNCOVERED model.layers.1.mlp.gate_proj.scales coordinate row=%0d col=%0d",row,col);
 offset=6008+(2*(64'd8*row+col));
 width=2;
end
39'h080000000d: begin
 if(row>=8 || col>=1)
   $fatal(1,"UNCOVERED model.layers.1.mlp.up_proj.qweight coordinate row=%0d col=%0d",row,col);
 offset=6024+(4*(64'd1*row+col));
 width=4;
end
39'h100000000d: begin
 if(row>=1 || col>=1)
   $fatal(1,"UNCOVERED model.layers.1.mlp.up_proj.qzeros coordinate row=%0d col=%0d",row,col);
 offset=6056+(4*(64'd1*row+col));
 width=4;
end
39'h180000000d: begin
 if(row>=1 || col>=8)
   $fatal(1,"UNCOVERED model.layers.1.mlp.up_proj.scales coordinate row=%0d col=%0d",row,col);
 offset=6060+(2*(64'd8*row+col));
 width=2;
end
39'h080000000e: begin
 if(row>=8 || col>=1)
   $fatal(1,"UNCOVERED model.layers.1.mlp.down_proj.qweight coordinate row=%0d col=%0d",row,col);
 offset=6076+(4*(64'd1*row+col));
 width=4;
end
39'h100000000e: begin
 if(row>=1 || col>=1)
   $fatal(1,"UNCOVERED model.layers.1.mlp.down_proj.qzeros coordinate row=%0d col=%0d",row,col);
 offset=6108+(4*(64'd1*row+col));
 width=4;
end
39'h180000000e: begin
 if(row>=1 || col>=8)
   $fatal(1,"UNCOVERED model.layers.1.mlp.down_proj.scales coordinate row=%0d col=%0d",row,col);
 offset=6112+(2*(64'd8*row+col));
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

reg [31:0] scratch[0:119];
reg [31:0] kcache[0:63],vcache[0:63];
reg [131:0] expected_writes[0:1151];
reg [31:0] rope_values[0:15];
integer cache_init;
initial begin
 $readmemh("/data/sufeng/anvil-q-line5/workspace_phase2/project/evidence/preparation/verifier-phase2-final-integration-01/synthetic-file-backed-top-writes.hex",expected_writes);
 for(cache_init=0;cache_init<64;cache_init=cache_init+1) begin
   kcache[cache_init]=32'h70000000; vcache[cache_init]=32'h71000000;
 end
 rope_values[0]=32'h40000000;
 rope_values[1]=32'h00000000;
 rope_values[2]=32'h40000000;
 rope_values[3]=32'h00000000;
 rope_values[4]=32'h2294501f;
 rope_values[5]=32'h35daa91e;
 rope_values[6]=32'h3ffffde7;
 rope_values[7]=32'h0010624e;
 rope_values[8]=32'he55dd9a9;
 rope_values[9]=32'h3a31edd6;
 rope_values[10]=32'h3ffff79d;
 rope_values[11]=32'h0020c49a;
 rope_values[12]=32'hc0a3f683;
 rope_values[13]=32'h09081c37;
 rope_values[14]=32'h3fffed20;
 rope_values[15]=32'h003126e5;

end
task automatic validate_address(input [3:0] kind,input [31:0] layer,
 input [2:0] proj,input [31:0] row,col);
integer limit;
begin
 if(kind>11 || layer>=2) $fatal(1,"OFFICIAL kind/layer address");
 if(kind==8) begin
   limit=(row==3 || row==4 ? 8 : (row>=9 && row<=11 ? 8 : 8));
   if(layer!=0 || proj!=0 || row>=15 || row==13 || col>=limit)
     $fatal(1,"OFFICIAL scratch address");
 end
 if(kind==9 || kind==10) begin
   if(proj!=0 || row>cmd_pos || row>=4 || col>=8)
     $fatal(1,"OFFICIAL CAUSAL cache address");
 end
 if(kind==11 && (layer!=0 || proj!=0 || row>=4 || col>=4))
   $fatal(1,"OFFICIAL RoPE address");
end endtask
function automatic [31:0] read_memory(input [3:0] kind,input [2:0] proj,
 input [31:0] row,col);
begin
 if(kind<=7) read_memory=checkpoint_read(kind,mem_req_layer,proj,row,col);
 else if(kind==8) read_memory=scratch[row*8+col];
 else if(kind==9) read_memory=kcache[(mem_req_layer*4+row)*8+col];
 else if(kind==10) read_memory=vcache[(mem_req_layer*4+row)*8+col];
 else if(kind==11) read_memory=rope_values[row*4+col];
 else begin $fatal(1,"OFFICIAL invalid read kind"); read_memory=0; end
 if(^read_memory===1'bx) $fatal(1,"OFFICIAL active unknown memory data");
end endfunction

task automatic reset_check;
begin
 
if(logit_valid!==0 || logit_index!==0 || logit_data!==0)
 $fatal(1,"OFFICIAL reset logit leakage");
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
 
if(^{logit_valid,logit_index,logit_data}===1'bx)
 $fatal(1,"OFFICIAL active unknown logit");
if(cmd_valid && cmd_ready) begin
 active_token=accepted_tokens; accepted_tokens=accepted_tokens+1;
 start_edge=cycles; logit_stalls=0; request_stalls=0; response_stalls=0;
 $display("OFFICIAL_ACCEPT token=%0d edge=%0d",active_token,cycles);
end
if(logit_held && {logit_valid,logit_index,logit_data} !== {1'b1,logit_payload})
 $fatal(1,"OFFICIAL stalled logit changed");
logit_held=logit_valid && !logit_ready;
logit_payload={logit_index,logit_data};
if(logit_held) logit_stalls=logit_stalls+1;
if(mem_req_valid && !mem_req_ready) request_stalls=request_stalls+1;
if(mem_rsp_valid && !mem_rsp_ready) response_stalls=response_stalls+1;
if(logit_valid && logit_ready) begin
 if(observed_logits>=32 || logit_index!==observed_logits%8 ||
    logit_data!==expected_logits[observed_logits])
   $fatal(1,"OFFICIAL LOGIT mismatch %0d",observed_logits);
 $display("OFFICIAL_LOGIT token=%0d index=%0d value=%0d",active_token,logit_index,logit_data);
 observed_logits=observed_logits+1;
 if(logit_index==7) begin
   final_edge=cycles; final_transfers=final_transfers+1;
   $display("OFFICIAL_FINAL token=%0d edge=%0d latency=%0d",
      active_token,cycles,cycles-start_edge);
 end
end

 if(was_stalled && {mem_req_valid,mem_req_write,mem_req_kind,mem_req_layer,
      mem_req_proj,mem_req_row,mem_req_col,mem_req_wdata} !== held)
   $fatal(1,"REQUEST payload changed under backpressure");
 was_stalled=mem_req_valid && !mem_req_ready;
 held={mem_req_valid,mem_req_write,mem_req_kind,mem_req_layer,
       mem_req_proj,mem_req_row,mem_req_col,mem_req_wdata};
 if(was_stalled) stalls=stalls+1;
 if(mem_req_valid && mem_req_ready) begin
   if(pending || mem_rsp_ready) $fatal(1,"OUTSTANDING or request/response overlap");
   
validate_address(mem_req_kind,mem_req_layer,mem_req_proj,mem_req_row,mem_req_col);
if(!mem_req_write && mem_req_wdata!==0) $fatal(1,"OFFICIAL nonzero read wdata");
if(mem_req_write && (mem_req_kind<8 || mem_req_kind>10))
 $fatal(1,"OFFICIAL forbidden write");
bin_index=counter_bin(active_token,mem_req_kind,mem_req_write,mem_req_layer,mem_req_proj);
requests_by_address[bin_index]=requests_by_address[bin_index]+1;
pending_bin=bin_index;

   accepted=accepted+1; pending=1; delay_count=(accepted%127==0 ? 2 : 0);
   if(accepted%262144==0) begin
     $display("PROGRESS accepted=%0d compared_writes=%0d completed=%0d cycles=%0d",
       accepted,writes,completions,cycles);
     $fflush();
   end
   if(mem_req_write) begin

if(writes>=1152 || mem_req_proj!==0 ||
 {mem_req_kind,mem_req_layer,mem_req_row,mem_req_col,mem_req_wdata} !== expected_writes[writes])
 $fatal(1,"OFFICIAL STACK ordered write mismatch %0d",writes);
if(mem_req_kind==8) scratch[mem_req_row*8+mem_req_col]=mem_req_wdata;
else if(mem_req_kind==9)
 kcache[(mem_req_layer*4+mem_req_row)*8+mem_req_col]=mem_req_wdata;
else if(mem_req_kind==10)
 vcache[(mem_req_layer*4+mem_req_row)*8+mem_req_col]=mem_req_wdata;
else $fatal(1,"OFFICIAL forbidden model write");

     writes=writes+1; reply=0;
   end else begin
     reply=read_memory(mem_req_kind,mem_req_proj,mem_req_row,mem_req_col);
   end
 end else if(pending && delay_count>0) delay_count=delay_count-1;
 if(mem_rsp_valid && mem_rsp_ready) begin
   if(!pending || delay_count!=0) $fatal(1,"UNEXPECTED response");
   
pending=0; responses=responses+1;
responses_by_address[pending_bin]=responses_by_address[pending_bin]+1;

 end
 if(done) begin
   if(error !== 0 || pending) $fatal(1,"unexpected completion error/outstanding");
   
if(final_transfers!=completions+1 || cycles!=final_edge+1 || cmd_ready!==0)
 $fatal(1,"OFFICIAL completion/retirement contract");
$display("OFFICIAL_RETIRE token=%0d edge=%0d latency=%0d request_stalls=%0d response_stalls=%0d logit_stalls=%0d",
 active_token,cycles,cycles-start_edge,request_stalls,response_stalls,logit_stalls);
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
cmd_layer=0;new_sequence=1;launch(0,0);
cmd_layer=1;new_sequence=0;launch(0,1);
cmd_layer=1;new_sequence=0;launch(0,2);
cmd_layer=1;new_sequence=0;launch(0,3);
if(accepted_tokens!=4 || completions!=4 || final_transfers!=4 ||
 observed_logits!=32 || writes!=1152)
 $fatal(1,"OFFICIAL incomplete tokens or comparisons");
for(print_index=0;print_index<1536;print_index=print_index+1)
 if(requests_by_address[print_index]!=0) begin
   if(requests_by_address[print_index]!=responses_by_address[print_index])
     $fatal(1,"OFFICIAL unacknowledged memory operation");
   $display("OFFICIAL_MEM bin=%0d requests=%0d responses=%0d",
     print_index,requests_by_address[print_index],responses_by_address[print_index]);
 end
$display("OFFICIAL_COUNTS writes=%0d logits=%0d completed=%0d",writes,observed_logits,completions);
$fclose(checkpoint_fd);

 if(accepted!=responses || pending || writes==0 || stalls==0 ||
    busy_holds==0 || bubbles==0)
   $fatal(1,"COVERAGE missing transfer/write/stall");
 $display("PASS public writes=%0d transactions=%0d stalls=%0d busy_holds=%0d bubbles=%0d",
   writes,accepted,stalls,busy_holds,bubbles);
 $finish;
end endmodule
