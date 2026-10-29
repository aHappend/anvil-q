"""D2 default-width projections against immutable parent and integer equations."""

import hashlib
from experiments import CLOCK
from reference import AWQ_SHIFTS, bf16, fp16, pack_awq, round_shift, sat32


def projection_default(evidence, seed, projections=range(7), simulator="verilator"):
    failures = []
    for projection in projections:
        record = projection_case(evidence, seed, projection, simulator)
        if not record["threshold_met"]:
            failures.append(
                f"projection {projection}: {record['service_inclusive_speedup']:.6f}x")
    if failures:
        raise AssertionError(
            "default AWQ service-inclusive speedup below required 8.0x: " +
            "; ".join(failures) + "; all numerical comparisons and cycle counts retained")
    if tuple(projections) == tuple(range(7)):
        from arithmetic_benchmark import arithmetic_default
        arithmetic_default(evidence, seed)


def projection_case(evidence, seed, projection, simulator, mode="AWQ"):
    if mode not in ("AWQ", "BF16") or projection not in range(8):
        raise ValueError("unsupported default projection benchmark")
    has_parent = mode == "AWQ" and projection < 7
    inputs = 4864 if projection == 6 else 896
    outputs = (151936 if projection == 7 else 128 if projection in (1, 2)
               else 4864 if projection in (4, 5) else 896)
    source_slot = (1, 1, 1, 5, 8, 8, 11, 14)[projection]
    target_slot = (2, 3, 4, 6, 9, 10, 12, 0)[projection]

    def activation(row):
        return ((row * 997 + seed * 53) % 131071) - 65535

    def qweight(row, col):
        return (row * 7 + col * 11 + (row >> 3) + seed) & 15

    def qzero(group, col):
        return (group * 3 + col * 5 + seed) & 15

    def scale(group, col):
        return 0x2400 + 0x400 * ((group + col + seed) % 3)

    def bias(col):
        return 0x3000 | ((col * 17 + seed) & 0x3ff) | ((col & 1) << 15)

    def dense_bits(row, col):
        if projection == 7:
            return (0x2800 + (((row * 3 + col * 7 + seed) & 31) << 5)
                    + (((row + col) & 1) << 15))
        return (0x3d00, 0xbd00, 0x3e00, 0xbe00, 0x0001, 0x8000, 0x0000, 0x3f00)[
            (row * 3 + col * 5 + seed) & 7]

    expected = []
    for col in range(outputs):
        if has_parent:
            total = sum(activation(row) * (qweight(row, col) - qzero(row // 128, col)) *
                        fp16(scale(row // 128, col)) for row in range(inputs))
        elif projection == 7 and col >= 32:
            expected.append(expected[col % 32])
            continue
        else:
            convert = fp16 if projection == 7 else bf16
            total = sum(activation(row) * convert(dense_bits(row, col)) for row in range(inputs))
        if projection < 3:
            total += fp16(bias(col)) << 16
        expected.append(sat32(round_shift(total, 16)))

    image = bytearray()
    regions = {}
    kinds = (0,) if projection == 7 else (1, 2, 3, 4) if has_parent else (1, 4)
    for kind in kinds:
        start = len(image)
        if kind == 0:
            panel = b"".join(dense_bits(row, col).to_bytes(2, "little")
                             for row in range(inputs) for col in range(64))
            image.extend(panel * (outputs // 64))
        elif kind == 1 and mode == "BF16":
            for panel in range(0, outputs, 64):
                for row in range(inputs):
                    for col in range(panel, panel + 64):
                        image.extend(dense_bits(row, col).to_bytes(2, "little"))
        elif kind in (1, 2):
            rows = inputs if kind == 1 else inputs // 128
            for panel in range(0, outputs, 64):
                for row in range(rows):
                    function = qweight if kind == 1 else qzero
                    for word in pack_awq([function(row, col) for col in range(panel, panel + 64)]):
                        image.extend(word.to_bytes(4, "little"))
        elif kind == 3:
            for panel in range(0, outputs, 64):
                for group in range(inputs // 128):
                    for col in range(panel, panel + 64):
                        image.extend(scale(group, col).to_bytes(2, "little"))
        elif projection < 3:
            for col in range(outputs):
                image.extend(bias(col).to_bytes(2, "little"))
        length = len(image) - start
        regions[kind] = (start, length)
        image.extend(bytes((-len(image)) % 64))
    image_path = evidence.folder / f"projection-{mode.lower()}-{projection}-image.hex"
    image_path.write_text("".join(
        f"{int.from_bytes(image[offset:offset+64], 'little'):0128x}\n"
        for offset in range(0, len(image), 64)))
    expected_path = evidence.folder / f"projection-{mode.lower()}-{projection}-expected.hex"
    expected_path.write_text("".join(f"{value & 0xffffffff:08x}\n" for value in expected))

    bench = CLOCK + r"""
reg ddr_clk=0;
always #1.875 ddr_clk=!ddr_clk;
reg command=0;
wire ht_ready,ht_done,ht_error,parent_ready,parent_done,parent_error;
integer core_cycles=0,ddr_cycles=0,ht_cycles=0,parent_cycles=0;
integer ht_start=0,parent_start=0,ht_compares=0,parent_compares=0;
integer ht_requests=0,parent_requests=0,read_beats=0,bursts=0;
integer tensor_vectors=0,tensor_dots=0,tensor_first_edge=0,tensor_elapsed=0;
integer outstanding=0,cursor=0;
reg [31:0] expected [0:OUTPUTS-1];
reg [511:0] memory [0:IMAGE_LAST];
wire [1:0] m_valid,m_ready,m_write,m_rsp_ready;
wire [3:0] m_kind [0:1];
wire [31:0] m_layer [0:1],m_row [0:1],m_col [0:1],m_wdata [0:1];
wire [2:0] m_proj [0:1];
reg [1:0] m_rsp_valid=0;
reg [31:0] m_rdata [0:1];
wire block_valid,block_ready,packet_valid,packet_ready,packet_last,block_done,block_error;
wire [3:0] block_kind;
wire [31:0] block_layer,block_offset,block_bytes;
wire [2:0] block_proj;
wire [7:0] block_packet_bytes;
wire [1023:0] packet_data;
wire lookup_valid,lookup_rsp_ready;
wire [31:0] lookup_index;
reg lookup_rsp_valid=0;
reg [32:0] lookup_base=0;
reg [31:0] lookup_length=0;
wire dma_valid,dma_ready,dma_abort,dma_done,dma_done_ready,dma_error;
wire [32:0] dma_address;
wire [31:0] dma_bytes;
wire [26:0] dma_tiles;
wire fill_valid,fill_ready,fill_bank,fill_data_valid,fill_data_ready,fill_last,fill_abort,fill_error;
wire [8:0] fill_beats,tile_beats;
wire [63:0] fill_tail,tile_tail;
wire [511:0] fill_data,read_data;
wire tile_valid,tile_ready,tile_bank,release_valid,release_ready;
wire read_valid,read_ready,read_rsp_valid,read_rsp_ready,compute_error;
wire [7:0] read_address;
wire [63:0] read_mask,accepted_beats;
wire [32:0] avm_address;
wire [7:0] avm_burstcount;
wire avm_read,avm_write;
wire [511:0] avm_writedata;
wire [63:0] avm_byteenable;
reg [511:0] avm_readdata=0;
reg avm_readdatavalid=0;
wire dma_protocol_error;
wire tensor_in_valid,tensor_in_ready,tensor_in_first,tensor_in_last;
wire signed [31:0] tensor_in_activation;
wire [2367:0] tensor_in_weights;
wire [63:0] tensor_in_mask,tensor_out_mask;
wire tensor_out_valid,tensor_out_ready,tensor_protocol_error;
wire [2047:0] tensor_out_data;
wire logit_valid,logit_ready;
wire [31:0] logit_index,logit_data;
integer port_index;
integer logit_stalls=0;
reg held_logit=0;
reg [63:0] held_logit_payload;
assign logit_ready=core_cycles%11>3 &&
                   !(logit_index==OUTPUTS-1 && logit_stalls<31);

function automatic [31:0] activation(input integer row);
 activation=((row*997+SEED*53)%131071)-65535;
endfunction
function automatic [3:0] qweight(input integer row,col);
 qweight=(row*7+col*11+(row>>3)+SEED)&15;
endfunction
function automatic [3:0] qzero(input integer row,col);
 qzero=(row*3+col*5+SEED)&15;
endfunction
function automatic integer shift_for(input integer lane);
 case(lane)
  0:shift_for=0;1:shift_for=16;2:shift_for=4;3:shift_for=20;
  4:shift_for=8;5:shift_for=24;6:shift_for=12;7:shift_for=28;
 endcase
endfunction
function automatic [31:0] logical_read(input integer kind,row,col);
 integer lane;
 begin
  logical_read=0;
  case(kind)
   1,2:for(lane=0;lane<8;lane=lane+1)
    logical_read=logical_read |
      ((kind==1 ? 32'(qweight(row,col*8+lane)) : 32'(qzero(row,col*8+lane)))<<shift_for(lane));
   3:logical_read=32'h2400+32'h400*((row+col+SEED)%3);
   4:logical_read=32'h3000|((col*17+SEED)&1023)|((col&1)<<15);
   8:logical_read=activation(col);
   default:$fatal(1,"BENCH_UNEXPECTED_MEMORY_KIND %0d",kind);
  endcase
 end
endfunction
always @(posedge clk) begin
 if(!rst_n) begin
  core_cycles<=0;m_rsp_valid<=0;lookup_rsp_valid<=0;
 end else begin
  core_cycles<=core_cycles+1;
  if(command && ht_ready) ht_start=core_cycles;
  if(HAS_PARENT && command && parent_ready) parent_start=core_cycles;
  if(ht_done && ht_cycles==0) begin
   if(ht_error!==0 || ht_compares!=OUTPUTS) $fatal(1,"HT_PROJECTION_ERROR_OR_MISSING_OUTPUT");
   ht_cycles=core_cycles-ht_start;
  end
  if(HAS_PARENT && parent_done && parent_cycles==0) begin
   if(parent_error!==0 || parent_compares!=OUTPUTS) $fatal(1,"PARENT_PROJECTION_ERROR_OR_MISSING_OUTPUT");
   parent_cycles=core_cycles-parent_start;
  end
  if(tensor_in_valid && tensor_in_ready) begin
   tensor_vectors=tensor_vectors+1;
   if(tensor_in_first) tensor_first_edge=core_cycles;
  end
  if(tensor_out_valid && tensor_out_ready) begin
   tensor_dots=tensor_dots+1;
   tensor_elapsed=tensor_elapsed+core_cycles-tensor_first_edge;
  end
  if(PROJECTION==7) begin
   if(held_logit && (logit_valid!==1 || {logit_index,logit_data}!==held_logit_payload))
    $fatal(1,"VOCABULARY_STALLED_LOGIT_CHANGED");
   held_logit=logit_valid && !logit_ready;
   if(held_logit) held_logit_payload={logit_index,logit_data};
   if(logit_valid && logit_index==OUTPUTS-1 && !logit_ready) logit_stalls=logit_stalls+1;
   if(logit_valid && logit_ready) begin
    if(logit_index!==ht_compares || logit_data!==expected[ht_compares])
     $fatal(1,"VOCABULARY_NUMERICAL_OR_ORDER_MISMATCH index=%0d actual=%h expected=%h",
            logit_index,logit_data,expected[ht_compares]);
    ht_compares=ht_compares+1;
   end
  end
  for(port_index=0;port_index<2;port_index=port_index+1) begin
   if(m_rsp_valid[port_index] && !m_rsp_ready[port_index])
    $fatal(1,"LOGICAL_MEMORY_RESPONSE_NOT_ACCEPTED");
   m_rsp_valid[port_index]<=m_valid[port_index] && m_ready[port_index];
   if(m_valid[port_index] && m_ready[port_index]) begin
    if(m_kind[port_index]==8 && m_write[port_index]) begin
     if(m_row[port_index]!==TARGET_SLOT || m_col[port_index]>=OUTPUTS ||
        m_wdata[port_index]!==expected[m_col[port_index]] ||
        m_col[port_index] !== (port_index==0 ? ht_compares : parent_compares))
      $fatal(1,"PROJECTION_NUMERICAL_MISMATCH port=%0d index=%0d actual=%h expected=%h",
             port_index,m_col[port_index],m_wdata[port_index],expected[m_col[port_index]]);
     if(port_index==0) ht_compares=ht_compares+1;
     else parent_compares=parent_compares+1;
     m_rdata[port_index]<=0;
    end else begin
     if(m_write[port_index] || (m_kind[port_index]==8 && m_row[port_index]!==SOURCE_SLOT))
      $fatal(1,"PROJECTION_BAD_LOGICAL_ACCESS");
     m_rdata[port_index]<=logical_read(m_kind[port_index],m_row[port_index],m_col[port_index]);
    end
    if(port_index==0) ht_requests=ht_requests+1;
    else parent_requests=parent_requests+1;
   end
  end
  lookup_rsp_valid<=lookup_valid;
  if(lookup_valid) begin
   if((PROJECTION==7 && lookup_index!==0) ||
      (PROJECTION!=7 && (lookup_index[2:0]!==3'dPROJECTION || lookup_index<8 || lookup_index>=40)))
    $fatal(1,"PROJECTION_WRONG_DESCRIPTOR_INDEX");
   case(lookup_index>>3)
    REGION_CASES
    default:$fatal(1,"BENCH_UNEXPECTED_BLOCK_KIND");
   endcase
  end
  if(tensor_protocol_error!==0 || compute_error!==0 || dma_protocol_error!==0 ||
     (PROJECTION!=7 && logit_valid!==0)) $fatal(1,"HT_PROJECTION_PROTOCOL_ERROR");
 end
end
assign m_ready=2'b11;
always @(posedge ddr_clk) begin
 if(!rst_n) begin
  avm_readdatavalid<=0;outstanding<=0;ddr_cycles<=0;
 end else begin
  ddr_cycles<=ddr_cycles+1;
  avm_readdatavalid<=0;
  if(avm_readdatavalid) read_beats=read_beats+1;
  if(avm_read) begin
   if(outstanding!=0 || avm_burstcount<1 || avm_burstcount>16 ||
      avm_address[5:0]!==0 || avm_write!==0 ||
      avm_byteenable!==64'hffffffffffffffff ||
      avm_address[11:0]+avm_burstcount*64>4096)
    $fatal(1,"BENCH_AVALON_COMMAND_ERROR");
   outstanding<=avm_burstcount;cursor<=avm_address>>6;bursts=bursts+1;
   avm_readdatavalid<=1;avm_readdata<=memory[avm_address>>6];
   outstanding<=avm_burstcount-1;cursor<=(avm_address>>6)+1;
  end else if(outstanding>0) begin
   avm_readdatavalid<=1;avm_readdata<=memory[cursor];
   outstanding<=outstanding-1;cursor<=cursor+1;
  end
 end
end

anvil_q1_ht_projection ht(
 .clk(clk),.rst_n(rst_n),.abort_error(1'b0),
 .cmd_valid(command),.cmd_ready(ht_ready),.cmd_layer(32'd0),.cmd_pos(32'd0),
 .cmd_proj(4'dPROJECTION),.storage_bf16(1'bBF16_MODE),.done(ht_done),.error(ht_error),
 .mem_req_valid(m_valid[0]),.mem_req_ready(m_ready[0]),.mem_req_write(m_write[0]),
 .mem_req_kind(m_kind[0]),.mem_req_layer(m_layer[0]),.mem_req_proj(m_proj[0]),
 .mem_req_row(m_row[0]),.mem_req_col(m_col[0]),.mem_req_wdata(m_wdata[0]),
 .mem_rsp_valid(m_rsp_valid[0]),.mem_rsp_ready(m_rsp_ready[0]),
 .mem_rsp_rdata(m_rdata[0]),.mem_rsp_error(1'b0),
 .block_valid(block_valid),.block_ready(block_ready),.block_kind(block_kind),
 .block_layer(block_layer),.block_proj(block_proj),.block_offset(block_offset),
 .block_bytes(block_bytes),.block_packet_bytes(block_packet_bytes),
 .packet_valid(packet_valid),.packet_ready(packet_ready),.packet_data(packet_data),
 .packet_last(packet_last),.block_done(block_done),.block_error(block_error),
 .tensor_in_valid(tensor_in_valid),.tensor_in_ready(tensor_in_ready),
 .tensor_in_first(tensor_in_first),.tensor_in_last(tensor_in_last),
 .tensor_in_activation(tensor_in_activation),.tensor_in_weight_q16(tensor_in_weights),
 .tensor_in_mask(tensor_in_mask),.tensor_out_valid(tensor_out_valid),
 .tensor_out_ready(tensor_out_ready),.tensor_out_data(tensor_out_data),
 .tensor_out_mask(tensor_out_mask),.tensor_protocol_error(tensor_protocol_error),
 .logit_valid(logit_valid),.logit_ready(logit_ready),.logit_index(logit_index),.logit_data(logit_data));
anvil_q1_ht_tensor_array tensor(
 .clk(clk),.rst_n(rst_n),.in_valid(tensor_in_valid),.in_ready(tensor_in_ready),
 .in_first(tensor_in_first),.in_last(tensor_in_last),.in_activation(tensor_in_activation),
 .in_weight_q16(tensor_in_weights),.in_mask(tensor_in_mask),
 .out_valid(tensor_out_valid),.out_ready(tensor_out_ready),.out_data(tensor_out_data),
 .out_mask(tensor_out_mask),.protocol_error(tensor_protocol_error));
anvil_q1_ht_weight_stream stream(
 .clk(clk),.rst_n(rst_n),.abort_error(1'b0),.command_valid(block_valid),
 .command_ready(block_ready),.command_kind(block_kind),.command_layer(block_layer),
 .command_proj(block_proj),.command_offset(block_offset),.command_bytes(block_bytes),
 .command_packet_bytes(block_packet_bytes),.packet_valid(packet_valid),
 .packet_ready(packet_ready),.packet_data(packet_data),.packet_last(packet_last),
 .done(block_done),.error(block_error),.lookup_valid(lookup_valid),.lookup_ready(1'b1),
 .lookup_index(lookup_index),.lookup_rsp_valid(lookup_rsp_valid),
 .lookup_rsp_ready(lookup_rsp_ready),.lookup_base(lookup_base),.lookup_length(lookup_length),
 .lookup_error(1'b0),.dma_valid(dma_valid),.dma_ready(dma_ready),.dma_address(dma_address),
 .dma_bytes(dma_bytes),.dma_abort(dma_abort),.dma_done(dma_done),
 .dma_done_ready(dma_done_ready),.dma_error(dma_error),.dma_tiles(dma_tiles),
 .tile_valid(tile_valid),.tile_ready(tile_ready),.tile_beats(tile_beats),
 .release_valid(release_valid),.release_ready(release_ready),.read_valid(read_valid),
 .read_ready(read_ready),.read_address(read_address),.read_rsp_valid(read_rsp_valid),
 .read_rsp_ready(read_rsp_ready),.read_data(read_data),.read_mask(read_mask),.tile_error(compute_error));
anvil_q1_ht_weight_dma dma(
 .clk(clk),.ddr_clk(ddr_clk),.rst_n(rst_n),
 .request_valid(dma_valid),.request_ready(dma_ready),.request_address(dma_address),
 .request_bytes(dma_bytes),.request_abort(dma_abort),
 .completion_valid(dma_done),.completion_ready(dma_done_ready),
 .completion_error(dma_error),.completion_tiles(dma_tiles),
 .load_enable(1'b0),.load_clear(1'b0),.load_valid(1'b0),.load_ready(),
 .load_address(33'b0),.load_data(512'b0),.load_byteenable(64'b0),.load_last(1'b0),
 .load_done(),.load_error(),.load_idle(),
 .fill_valid(fill_valid),.fill_ready(fill_ready),.fill_beats(fill_beats),.fill_tail(fill_tail),
 .fill_data_valid(fill_data_valid),.fill_data_ready(fill_data_ready),.fill_data(fill_data),
 .fill_last(fill_last),.fill_abort(fill_abort),.fill_error(fill_error),
 .avm_address(avm_address),.avm_burstcount(avm_burstcount),.avm_read(avm_read),
 .avm_write(avm_write),.avm_writedata(avm_writedata),.avm_byteenable(avm_byteenable),
 .avm_waitrequest(1'b0),.avm_readdata(avm_readdata),.avm_readdatavalid(avm_readdatavalid),
 .avm_response(2'b00),.avm_writeresponsevalid(1'b0),
 .accepted_read_beats(accepted_beats),.protocol_error(dma_protocol_error));
anvil_q1_ht_weight_tiles tiles(
 .clk(clk),.ddr_clk(ddr_clk),.rst_n(rst_n),
 .fill_valid(fill_valid),.fill_ready(fill_ready),.fill_bank(fill_bank),
 .fill_beats(fill_beats),.fill_tail(fill_tail),.fill_data_valid(fill_data_valid),
 .fill_data_ready(fill_data_ready),.fill_data(fill_data),.fill_last(fill_last),
 .fill_abort(fill_abort),.fill_error(fill_error),
 .tile_valid(tile_valid),.tile_ready(tile_ready),.tile_bank(tile_bank),.tile_beats(tile_beats),
 .tile_tail(tile_tail),.release_valid(release_valid),.release_ready(release_ready),
 .read_valid(read_valid),.read_ready(read_ready),.read_address(read_address),
 .read_rsp_valid(read_rsp_valid),.read_rsp_ready(read_rsp_ready),
 .read_data(read_data),.read_mask(read_mask),.compute_error(compute_error));
generate if(HAS_PARENT) begin: g_parent
anvil_q1_w4a16_gemv parent(
 .clk(clk),.rst_n(rst_n),.cmd_valid(command),.cmd_ready(parent_ready),
 .cmd_layer(32'd0),.cmd_pos(32'd0),.cmd_proj(3'dPROJECTION),
 .done(parent_done),.error(parent_error),
 .mem_req_valid(m_valid[1]),.mem_req_ready(m_ready[1]),.mem_req_write(m_write[1]),
 .mem_req_kind(m_kind[1]),.mem_req_layer(m_layer[1]),.mem_req_proj(m_proj[1]),
 .mem_req_row(m_row[1]),.mem_req_col(m_col[1]),.mem_req_wdata(m_wdata[1]),
 .mem_rsp_valid(m_rsp_valid[1]),.mem_rsp_ready(m_rsp_ready[1]),
 .mem_rsp_rdata(m_rdata[1]),.mem_rsp_error(1'b0));
end else begin: g_no_parent
 assign parent_ready=1'b1;
 assign parent_done=1'b0;
 assign parent_error=1'b0;
 assign m_valid[1]=1'b0;
 assign m_write[1]=1'b0;
 assign m_kind[1]=4'b0;
 assign m_layer[1]=32'b0;
 assign m_proj[1]=3'b0;
 assign m_row[1]=32'b0;
 assign m_col[1]=32'b0;
 assign m_wdata[1]=32'b0;
 assign m_rsp_ready[1]=1'b1;
end endgenerate
initial begin
 rst_n=0;
 $readmemh("IMAGE_PATH",memory);
 $readmemh("EXPECTED_PATH",expected);
 repeat(6) edge_tick();
 @(negedge clk);rst_n=1;
 repeat(6) edge_tick();
 @(negedge clk);command=1;
 if(ht_ready!==1 || parent_ready!==1) $fatal(1,"BENCH_COMMAND_NOT_ACCEPTED");
 edge_tick();
 @(negedge clk);command=0;
 wait(ht_cycles>0 && (!HAS_PARENT || parent_cycles>0));
 edge_tick();
 if(read_beats==0 || accepted_beats!==read_beats || tensor_vectors==0 ||
    tensor_dots!=OUTPUTS/64 || outstanding!=0) $fatal(1,"BENCH_MISSING_REAL_ACTIVITY");
 if(PROJECTION==7 && logit_stalls<31) $fatal(1,"VOCABULARY_MISSING_FINAL_STALL");
 $display("MEASURED projection=PROJECTION inputs=INPUTS outputs=OUTPUTS ht_cycles=%0d parent_cycles=%0d ht_compares=%0d parent_compares=%0d read_beats=%0d bursts=%0d ht_requests=%0d parent_requests=%0d tensor_vectors=%0d tensor_elapsed=%0d",
          ht_cycles,parent_cycles,ht_compares,parent_compares,read_beats,bursts,
          ht_requests,parent_requests,tensor_vectors,tensor_elapsed);
 $display("CHECKS_PASSED projection=PROJECTION comparisons=%0d",ht_compares+parent_compares);
 $finish;
end
endmodule
"""
    cases = "\n".join(
        f"4'd{kind}:begin lookup_base<=33'd{base};lookup_length<=32'd{length};end"
        for kind, (base, length) in regions.items())
    substitutions = {
        "REGION_CASES": cases, "IMAGE_LAST": len(image) // 64 - 1,
        "IMAGE_PATH": evidence.relative(image_path),
        "EXPECTED_PATH": evidence.relative(expected_path), "SOURCE_SLOT": source_slot,
        "TARGET_SLOT": target_slot, "PROJECTION": projection, "OUTPUTS": outputs,
        "INPUTS": inputs, "SEED": seed, "HAS_PARENT": int(has_parent),
        "BF16_MODE": int(mode == "BF16"),
    }
    for key, value in substitutions.items():
        bench = bench.replace(key, str(value))
    root = evidence.folder / "sources"
    sources = sorted((root / "rtl").glob("*.sv"))
    sources += [root / "anvil_q1_reference/rtl" / name for name in (
        "anvil_q1_00_pkg.sv", "anvil_q1_awq_dequant.sv",
        "anvil_q1_parameters.sv", "anvil_q1_w4a16_gemv.sv")]
    record = {
        "scope": "D2_default_projection_not_full_model",
        "mode": mode, "projection": projection, "seed": seed, "inputs": inputs, "outputs": outputs,
        "simulator": simulator,
        "image_sha256": hashlib.sha256(image).hexdigest(), "regions": regions,
        "expected_sha256": hashlib.sha256(expected_path.read_bytes()).hexdigest(),
        "compute_period_ns": 10, "ddr_period_ns": 3.75,
        "warmup": "reset plus six idle core cycles; no warmup inference",
        "measurement": "accepted command edge to first rising edge sampling public done high",
        "service": "logical requests always accepted, response consumed following core edge; "
                   "DDR commands unstalled, first response consumed following DDR edge, consecutive beats",
        "limitations": ["synthetic mathematical tensors, not checkpoint inference",
                        "logical activation/scratch service, not a full decoder DDR path",
                        "tensor_elapsed includes integration feed gaps, not isolated MAC compute"],
    }
    if has_parent:
        record["required_service_inclusive_speedup"] = 8.0
    else:
        record["parent_comparison"] = "not applicable; no parent BF16 projection mode or standalone vocabulary GEMV"
    evidence.record.setdefault("projection_benchmarks", []).append(record)
    evidence.flush()
    transcript = evidence.simulate(f"projection-{mode.lower()}-{projection}", bench, sources=sources,
                                   timeout=14400, simulator=simulator)
    lines = [line for line in transcript.splitlines() if line.startswith("MEASURED ")]
    if len(lines) != 1:
        raise AssertionError("projection benchmark missing unique measured cycle record")
    counters = dict(field.split("=") for field in lines[0].split()[1:])
    record["observed"] = {key: int(value) for key, value in counters.items()}
    if int(counters["ht_compares"]) != outputs or int(counters["parent_compares"]) != (
            outputs if has_parent else 0):
        raise AssertionError("missing complete default-width projection comparisons")
    if has_parent:
        record["service_inclusive_speedup"] = int(counters["parent_cycles"]) / int(counters["ht_cycles"])
        record["threshold_met"] = record["service_inclusive_speedup"] >= 8.0
    evidence.flush()
    return record


def dense_default(evidence, seed, vocabulary=False):
    simulator = "verilator"
    for mode in (("AWQ", "BF16") if vocabulary else ("BF16",)):
        for projection in ((7,) if vocabulary else range(7)):
            projection_case(evidence, seed, projection, simulator, mode=mode)
