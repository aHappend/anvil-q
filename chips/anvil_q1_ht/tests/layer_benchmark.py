"""Connected default-width decoder-layer comparisons, not full-model acceptance.

The actual HT decoder, projection, nonlinear kernels and 64-lane tensor array
execute two causal tokens. Public logical-memory and packed-block interfaces
have independently modeled service; DDR, KV residency and board speed are not
inferred from this experiment. Layer count and vocabulary are reduced explicitly.
"""

import hashlib
import re

from experiments import CLOCK
from reference import EngineeringModel, Shape


def layer_default(evidence, seed, mode):
    if mode not in ("AWQ", "BF16"):
        raise ValueError("layer benchmark requires AWQ or BF16")
    shape = Shape(1, 896, 4864, 14, 2, 64, 128, 8, 3, 256, 3)
    model = EngineeringModel(shape, seed, mode)
    # Exact Q2.30 rotations exercise cross-half sign and rounded products.
    model.rope[1] = [value for pair in range(32)
                     for value in ((858993459, 644245094) if pair % 2 == 0
                                   else (644245094, -858993459))]
    model.add(11, 0, 0, model.words([x for row in model.rope for x in row], 4))

    memory, regions = [], []
    for (kind, layer, proj), data in sorted(model.tensors.items()):
        if kind in (1, 2, 3, 4):
            continue
        if kind == 0:
            rows, cols = shape.vocab, shape.hidden
            values = [value for row in model.embedding for value in row]
        else:
            rows = 15 if kind == 8 else shape.max_seq if kind in (9, 10, 11) else 1
            cols = (shape.intermediate if kind == 8 else shape.kv if kind in (9, 10)
                    else shape.head_dim if kind == 11 else shape.hidden)
            size = 4 if kind >= 8 else 2
            values = [int.from_bytes(data[offset:offset + size], "little")
                      for offset in range(0, len(data), size)]
        if len(values) != rows * cols:
            raise AssertionError("layer scalar fixture shape mismatch")
        regions.append((kind, len(memory), rows, cols))
        memory.extend(values)
    locations = {kind: (base, cols) for kind, base, _, cols in regions}
    expected_writes, tokens = {}, []
    for position in range(2):
        token = (seed + position * 3) % shape.vocab
        logits = model.token(token, position, position == 0)
        tokens.append((token, logits))
        for kind, layer, row, col, value in model.last_writes:
            if layer != 0:
                raise AssertionError("unexpected layer in one-layer reference")
            base, cols = locations[kind]
            expected_writes.setdefault(base + row * cols + col, []).append(value)
    depth = max(map(len, expected_writes.values()))
    block_image, block_regions = bytearray(), []
    for (kind, layer, proj), data in sorted(model.tensors.items()):
        if kind not in (0, 1, 2, 3, 4):
            continue
        block_regions.append((kind * 8 + proj, len(block_image), len(data)))
        block_image.extend(data)

    def fixture(name, text):
        path = evidence.folder / ("layer-" + mode.lower() + "-" + name + ".hex")
        path.write_text(text)
        evidence.record.setdefault("runtime_input_sha256", {})[evidence.relative(path)] = (
            hashlib.sha256(path.read_bytes()).hexdigest())
        return evidence.relative(path)

    image = fixture("scalar", "".join(f"{word & 0xffffffff:08x}\n" for word in memory))
    writes = fixture("writes", "".join(
        f"{(expected_writes.get(address, []) + [0] * depth)[index] & 0xffffffff:08x}\n"
        for address in range(len(memory)) for index in range(depth)))
    counts = fixture("counts", "".join(
        f"{len(expected_writes.get(address, [])):08x}\n" for address in range(len(memory))))
    blocks = fixture("blocks", "".join(f"{byte:02x}\n" for byte in block_image))
    logits = fixture("logits", "".join(
        f"{value & 0xffffffff:08x}\n" for _, vector in tokens for value in vector))
    evidence.record["simulation_geometry"] = vars(shape)
    evidence.record["layer_reference"] = {
        "scope": "D4_connected_default_width_layer_not_default_24_layer_model_or_DDR",
        "shape": vars(shape), "mode": mode, "seed": seed,
        "token_ids": [token for token, _ in tokens],
        "expected_writes": sum(map(len, expected_writes.values())),
        "expected_logits": 2 * shape.vocab,
        "reference": "independent integer network equations in tests/reference.py",
        "memory_service": "scalar one-outstanding delayed response; packed blocks with periodic stalls",
        "rotations": {"position0": "identity", "position1": model.rope[1]},
    }
    evidence.flush()
    bench = CLOCK + r"""
localparam WORDS=@WORDS@,DEPTH=@DEPTH@,BLOCK_BYTES=@BLOCK_BYTES@;
reg token_valid=0,new_sequence=0,logit_ready=0;
reg [31:0] token_id=0,token_pos=0;
wire token_ready,logit_valid,done,error,busy,cache_new_sequence;
wire [31:0] logit_index;
wire signed [31:0] logit_data;
wire [63:0] token_cycles;
wire mem_req_valid,mem_req_write,mem_rsp_ready;
wire [3:0] mem_req_kind;
wire [2:0] mem_req_proj;
wire [31:0] mem_req_layer,mem_req_row,mem_req_col,mem_req_wdata;
reg mem_req_ready=0,mem_rsp_valid=0;
reg [31:0] mem_rsp_rdata=0;
wire block_valid,packet_ready;
wire [3:0] block_kind;
wire [2:0] block_proj;
wire [31:0] block_layer,block_offset,block_bytes;
wire [7:0] block_packet_bytes;
reg block_ready=0,packet_valid=0,packet_last=0,block_done=0;
reg [1023:0] packet_data=0;
wire tensor_in_valid,tensor_in_ready,tensor_in_first,tensor_in_last;
wire signed [31:0] tensor_in_activation;
wire [2367:0] tensor_in_weight_q16;
wire [63:0] tensor_in_mask,tensor_out_mask;
wire tensor_out_valid,tensor_out_ready,tensor_protocol_error;
wire [2047:0] tensor_out_data;
reg [31:0] memory [0:WORDS-1];
reg [31:0] expected_writes [0:WORDS*DEPTH-1];
reg [31:0] wanted [0:WORDS-1];
integer seen [0:WORDS-1];
reg [7:0] block_memory [0:BLOCK_BYTES-1];
reg [31:0] expected_logits [0:15];
integer cycles=0,requests=0,writes=0,compared=0,completed=0;
integer pending=0,delay_left=0,address=0,held=0;
integer cursor=0,remaining=0,packet_size=0,block_active=0,block_count=0;
integer packet_compares=0,packet_stalls=0,tensor_vectors=0,tensor_dots=0;
integer final_stalls=0,i,j,quiet=0;
reg held_logit=0,held_packet=0;
reg [63:0] held_logit_payload;
reg [1024:0] held_packet_payload;
reg [135:0] held_payload;
wire [135:0] payload={mem_req_write,mem_req_kind,mem_req_layer,mem_req_proj,
                     mem_req_row,mem_req_col,mem_req_wdata};
anvil_q1_ht_decoder #(
 .NUM_LAYERS(1),.HIDDEN_SIZE(896),.INTERMEDIATE_SIZE(4864),
 .NUM_Q_HEADS(14),.NUM_KV_HEADS(2),.HEAD_DIM(64),.GROUP_SIZE(128),
 .VOCAB_SIZE(8),.MAX_SEQ_LEN(3)) product(
 .clk(clk),.rst_n(rst_n),.engine_enable(1'b1),.storage_bf16(1'b@BF16@),
 .execution_fault(1'b0),.token_valid(token_valid),.token_ready(token_ready),
 .token_id(token_id),.token_pos(token_pos),.new_sequence(new_sequence),
 .logit_valid(logit_valid),.logit_ready(logit_ready),.logit_index(logit_index),
 .logit_data(logit_data),.done(done),.error(error),.busy(busy),
 .token_cycles(token_cycles),.cache_new_sequence(cache_new_sequence),.cache_initialized(1'b1),
 .mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),.mem_req_write(mem_req_write),
 .mem_req_kind(mem_req_kind),.mem_req_layer(mem_req_layer),.mem_req_proj(mem_req_proj),
 .mem_req_row(mem_req_row),.mem_req_col(mem_req_col),.mem_req_wdata(mem_req_wdata),
 .mem_rsp_valid(mem_rsp_valid),.mem_rsp_ready(mem_rsp_ready),
 .mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_error(1'b0),
 .block_valid(block_valid),.block_ready(block_ready),.block_kind(block_kind),
 .block_layer(block_layer),.block_proj(block_proj),.block_offset(block_offset),
 .block_bytes(block_bytes),.block_packet_bytes(block_packet_bytes),
 .packet_valid(packet_valid),.packet_ready(packet_ready),.packet_data(packet_data),
 .packet_last(packet_last),.block_done(block_done),.block_error(1'b0),
 .tensor_in_valid(tensor_in_valid),.tensor_in_ready(tensor_in_ready),
 .tensor_in_first(tensor_in_first),.tensor_in_last(tensor_in_last),
 .tensor_in_activation(tensor_in_activation),.tensor_in_weight_q16(tensor_in_weight_q16),
 .tensor_in_mask(tensor_in_mask),.tensor_out_valid(tensor_out_valid),
 .tensor_out_ready(tensor_out_ready),.tensor_out_data(tensor_out_data),
 .tensor_out_mask(tensor_out_mask),.tensor_protocol_error(tensor_protocol_error));
anvil_q1_ht_tensor_array tensor(
 .clk(clk),.rst_n(rst_n),.in_valid(tensor_in_valid),.in_ready(tensor_in_ready),
 .in_first(tensor_in_first),.in_last(tensor_in_last),.in_activation(tensor_in_activation),
 .in_weight_q16(tensor_in_weight_q16),.in_mask(tensor_in_mask),
 .out_valid(tensor_out_valid),.out_ready(tensor_out_ready),.out_data(tensor_out_data),
 .out_mask(tensor_out_mask),.protocol_error(tensor_protocol_error));
function automatic integer location(input integer kind,layer,proj,row,col);
 integer base,rows,cols;
 begin
  base=-1;rows=0;cols=0;
  case(kind)
   @REGIONS@
  endcase
  if(layer!=0 || proj!=0 || base<0 || row<0 || row>=rows || col<0 || col>=cols)
   $fatal(1,"LAYER_SCALAR_ADDRESS kind=%0d layer=%0d proj=%0d row=%0d col=%0d",
          kind,layer,proj,row,col);
  location=base+row*cols+col;
 end
endfunction
task reset_check;
 begin
  if({token_ready,logit_valid,logit_index,logit_data,done,error,busy,
      token_cycles,cache_new_sequence,mem_req_valid,mem_req_write,mem_req_kind,
      mem_req_layer,mem_req_proj,mem_req_row,mem_req_col,mem_req_wdata,
      mem_rsp_ready,block_valid,block_kind,block_layer,block_proj,
      block_offset,block_bytes,block_packet_bytes,packet_ready,tensor_in_valid,
      tensor_in_first,tensor_in_last,tensor_in_activation,tensor_in_weight_q16,
      tensor_in_mask,tensor_out_ready} !== '0)
   $fatal(1,"LAYER_RESET_XZ_OR_NONZERO");
 end
endtask
always @(posedge clk or negedge clk) if(!rst_n) reset_check();
always @(posedge clk) begin
 if(!rst_n) begin
  mem_rsp_valid<=0;pending=0;held=0;block_active=0;
  packet_valid<=0;block_done<=0;held_logit=0;held_packet=0;
 end else begin
  cycles=cycles+1;
  if((^{token_ready,logit_valid,done,error,busy,mem_req_valid,mem_rsp_ready,
         block_valid,packet_ready,tensor_in_valid,tensor_out_ready,tensor_protocol_error})===1'bx)
   $fatal(1,"LAYER_ACTIVE_CONTROL_XZ");
  if(tensor_protocol_error!==0 || error!==0) $fatal(1,"LAYER_UNEXPECTED_ERROR");
  if(held && (!mem_req_valid || payload!==held_payload))
   $fatal(1,"LAYER_SCALAR_REQUEST_STALL");
  held=mem_req_valid && !mem_req_ready;
  if(held) held_payload=payload;
  if(mem_rsp_valid && mem_rsp_ready) begin mem_rsp_valid<=0;pending=0;end
  if(pending && !mem_rsp_valid) begin
   if(delay_left==0) mem_rsp_valid<=1;
   else delay_left=delay_left-1;
  end
  if(mem_req_valid && mem_req_ready) begin
   if(pending) $fatal(1,"LAYER_SCALAR_OUTSTANDING");
   address=location(mem_req_kind,mem_req_layer,mem_req_proj,mem_req_row,mem_req_col);
   if(mem_req_write) begin
    if(seen[address]>=wanted[address] ||
       mem_req_wdata!==expected_writes[address*DEPTH+seen[address]])
     $fatal(1,"LAYER_WRITE_MISMATCH kind=%0d row=%0d col=%0d ordinal=%0d actual=%h expected=%h",
            mem_req_kind,mem_req_row,mem_req_col,seen[address],mem_req_wdata,
            expected_writes[address*DEPTH+seen[address]]);
    seen[address]=seen[address]+1;memory[address]=mem_req_wdata;writes=writes+1;
   end
   mem_rsp_rdata<=mem_req_write ? 0 : memory[address];
   pending=1;delay_left=requests%3;requests=requests+1;
  end
  block_done<=0;
  if(held_packet && (packet_valid!==1 || {packet_last,packet_data}!==held_packet_payload))
   $fatal(1,"LAYER_PACKET_STALL");
  held_packet=packet_valid && !packet_ready;
  if(held_packet) begin
   held_packet_payload={packet_last,packet_data};packet_stalls=packet_stalls+1;
  end
  if(packet_valid && packet_ready) begin
   cursor=cursor+packet_size;remaining=remaining-packet_size;
   packet_compares=packet_compares+1;packet_valid<=0;
   if(remaining==0) begin block_active=0;block_done<=1;end
  end
  if(block_active && !packet_valid && cycles%7>1) begin
   packet_data<=0;
   for(j=0;j<packet_size;j=j+1) packet_data[j*8+:8]<=block_memory[cursor+j];
   packet_valid<=1;packet_last<=remaining==packet_size;
  end
  if(block_valid && block_ready) begin
   if(block_active || packet_valid || block_layer!=0)
    $fatal(1,"LAYER_BLOCK_OVERLAP_OR_LAYER");
   case(block_kind*8+block_proj)
    @BLOCK_REGIONS@
    default:$fatal(1,"LAYER_BLOCK_IDENTITY");
   endcase
   if(block_bytes==0 || block_packet_bytes==0 || block_packet_bytes>128 ||
      block_bytes%block_packet_bytes!=0)
    $fatal(1,"LAYER_BLOCK_PACKET_SHAPE");
   remaining=block_bytes;packet_size=block_packet_bytes;
   block_active=1;block_count=block_count+1;
  end
  if(tensor_in_valid && tensor_in_ready) tensor_vectors=tensor_vectors+1;
  if(tensor_out_valid && tensor_out_ready) tensor_dots=tensor_dots+1;
  if(held_logit && (logit_valid!==1 || {logit_index,logit_data}!==held_logit_payload || done!==0))
   $fatal(1,"LAYER_LOGIT_STALL");
  held_logit=logit_valid && !logit_ready;
  if(held_logit) held_logit_payload={logit_index,logit_data};
  if(logit_valid && logit_index==7 && !logit_ready) final_stalls=final_stalls+1;
  if(logit_valid && logit_ready) begin
   if(logit_index!==compared%8 || logit_data!==expected_logits[compared])
    $fatal(1,"LAYER_LOGIT_MISMATCH index=%0d actual=%h expected=%h",
           logit_index,logit_data,expected_logits[compared]);
   compared=compared+1;
  end
  if((mem_req_valid && mem_req_ready) || (mem_rsp_valid && mem_rsp_ready) ||
     (packet_valid && packet_ready) || (tensor_in_valid && tensor_in_ready) ||
     logit_valid || token_ready || done) quiet=0;
  else quiet=quiet+1;
  if(quiet>100000) $fatal(1,"LAYER_NO_PUBLIC_PROGRESS");
 end
end
always @(negedge clk) begin
 mem_req_ready=rst_n && !pending && cycles%11>3;
 block_ready=rst_n && !block_active && !packet_valid && !block_done && cycles%5!=0;
 logit_ready=rst_n && cycles%11>3 && !(logit_index==7 && final_stalls<31);
end
task run(input integer id,position);
 integer started,before_logits,before_writes,before_requests,before_vectors;
 begin
  @(negedge clk);token_id=id;token_pos=position;new_sequence=position==0;token_valid=1;
  if(token_ready!==1) $fatal(1,"LAYER_TOKEN_NOT_READY");
  started=cycles;before_logits=compared;before_writes=writes;
  before_requests=requests;before_vectors=tensor_vectors;final_stalls=0;
  edge_tick();
  if(token_ready!==0 || done!==0 || logit_valid!==0) $fatal(1,"LAYER_ACCEPT_EDGE");
  @(negedge clk);token_valid=0;
  while(done!==1) edge_tick();
  if(error!==0 || compared-before_logits!=8 || final_stalls<31 || pending ||
     block_active || packet_valid || writes==before_writes || tensor_vectors==before_vectors)
   $fatal(1,"LAYER_COMPLETION_OR_MISSING_ACTIVITY");
  $display("MEASURED_LAYER mode=@MODE@ position=%0d core_cycles=%0d token_counter=%0d writes=%0d requests=%0d tensor_vectors=%0d logits=%0d",
           position,cycles-started,token_cycles,writes-before_writes,
           requests-before_requests,tensor_vectors-before_vectors,compared-before_logits);
  completed=completed+1;
  edge_tick();
  if(done!==0 || error!==0 || token_ready!==1) $fatal(1,"LAYER_COMPLETION_PULSE");
 end
endtask
initial begin
 rst_n=0;`RESET_DELTA reset_check();
 $readmemh("@IMAGE@",memory);$readmemh("@WRITES@",expected_writes);
 $readmemh("@COUNTS@",wanted);$readmemh("@BLOCKS@",block_memory);
 $readmemh("@LOGITS@",expected_logits);
 for(i=0;i<WORDS;i=i+1) seen[i]=0;
 repeat(6) edge_tick();
 @(negedge clk);rst_n=1;
 repeat(6) edge_tick();
 run(@TOKEN0@,0);run(@TOKEN1@,1);
 for(i=0;i<WORDS;i=i+1)
  if(seen[i]!==wanted[i]) $fatal(1,"LAYER_MISSING_WRITE address=%0d",i);
 if(completed!=2 || compared!=16 || writes!=@EXPECTED_WRITES@ ||
    packet_compares==0 || tensor_dots==0 || tensor_vectors==0)
  $fatal(1,"LAYER_MISSING_COMPARISONS");
 $display("CHECKS_PASSED layer_default mode=@MODE@ tokens=%0d logits=%0d writes=%0d blocks=%0d packets=%0d tensor_dots=%0d tensor_vectors=%0d packet_stalls=%0d",
          completed,compared,writes,block_count,packet_compares,tensor_dots,tensor_vectors,packet_stalls);
 $finish;
end
endmodule
"""
    replacements = {
        "WORDS": len(memory), "DEPTH": depth, "BLOCK_BYTES": len(block_image),
        "BF16": int(mode == "BF16"), "MODE": mode, "IMAGE": image, "WRITES": writes,
        "COUNTS": counts, "BLOCKS": blocks, "LOGITS": logits,
        "TOKEN0": tokens[0][0], "TOKEN1": tokens[1][0],
        "EXPECTED_WRITES": sum(map(len, expected_writes.values())),
        "REGIONS": "\n".join(
            f"{kind}:begin base={base};rows={rows};cols={cols};end"
            for kind, base, rows, cols in regions),
        "BLOCK_REGIONS": "\n".join(
            f"{key}:begin if({{1'b0,block_offset}}+{{1'b0,block_bytes}}>{length}) "
            f'$fatal(1,"LAYER_BLOCK_RANGE");cursor={base}+block_offset;end'
            for key, base, length in block_regions),
    }
    for key, value in replacements.items():
        bench = bench.replace("@" + key + "@", str(value))
    if re.search(r"@[A-Z_0-9]+@", bench):
        raise AssertionError("unresolved layer testbench substitution")
    text = evidence.simulate("layer-" + mode.lower(), bench, simulator="verilator",
                             timeout=14400)
    rows = []
    for line in text.splitlines():
        if line.startswith("MEASURED_LAYER "):
            row = dict(re.findall(r"(\w+)=(\w+)", line))
            rows.append({key: int(value) if value.isdecimal() else value
                         for key, value in row.items()})
    if len(rows) != 2 or [row["position"] for row in rows] != [0, 1]:
        raise AssertionError("missing full-layer causal-token measurements")
    evidence.record["layer_measurements"] = rows
    evidence.flush()
