"""Unmodified-parent pin adapter with byte-accounted, tagged common service."""

from model import BASES, Geometry, Image, Inference, image_layout


POLICY = dict(service_policy_id="byte-budget-64-latency12-rr-v1",
              clock_hz=100_000_000, aggregate_bytes_per_cycle=64,
              read_latency_cycles=12, service_queue_capacity=64,
              arbitration_policy="round-robin-read-write-endpoints-explicit-wrap",
              scalar_transfer_bytes=4, ht_transfer_bytes=64)


PARENT_TB = r"""
module verify_parent;
  localparam BANKS=@BANKS@, H=@H@, I=@I@, D=@D@, LAYERS=@LAYERS@, CONTEXT=@CONTEXT@;
  localparam IMAGE_RECORDS=@IMAGE_RECORDS@, VOCAB=@VOCAB@, N=@N@;
  reg clk=0; always #5 clk=~clk;
  reg rst_n=0, cancel=0, token_valid=0, new_sequence=0, token_phase=0, logit_ready=0;
  reg [31:0] token_id=0, token_pos=0;
  wire token_ready, logit_valid, done, error, cancel_done;
  wire [31:0] logit_index;
  wire signed [31:0] logit_data;
  wire [BANKS-1:0] mem_req_valid, mem_req_write, mem_rsp_ready;
  reg [BANKS-1:0] mem_req_ready=0, mem_rsp_valid=0, mem_rsp_error=0;
  wire [BANKS*4-1:0] mem_req_kind;
  wire [BANKS*32-1:0] mem_req_layer, mem_req_row, mem_req_col, mem_req_wdata;
  wire [BANKS*3-1:0] mem_req_proj;
  wire [BANKS*64-1:0] mem_req_tag;
  reg [BANKS*32-1:0] mem_rsp_rdata=0;
  reg [BANKS*64-1:0] mem_rsp_tag=0;
  anvil_q3_top #(@PARAMETERS@) dut(.*);
  reg [32:0] image_address [0:IMAGE_RECORDS-1];
  reg [511:0] image_data [0:IMAGE_RECORDS-1];
  reg [99:0] sparse_keys [0:32767];
  reg [31:0] sparse_values [0:32767];
  integer stored=0;
  reg [31:0] expected [0:N-1];
  integer cycle=0, compared=0, tokens=0, accepted=0, serviced=0, completed=0;
  integer read_bytes=0, write_bytes=0, bytes_by_kind [0:15];
  integer first_service=-1, last_service=-1, maximum_queued=0, rr=0, budget;
  integer qh [0:BANKS-1], qt [0:BANKS-1], qc [0:BANKS-1];
  reg [31:0] qlayer [0:BANKS-1][0:63], qrow [0:BANKS-1][0:63];
  reg [31:0] qcol [0:BANKS-1][0:63], qdata [0:BANKS-1][0:63];
  reg [2:0] qproj [0:BANKS-1][0:63];
  reg [3:0] qkind [0:BANKS-1][0:63];
  reg qwrite [0:BANKS-1][0:63];
  reg [63:0] qtag [0:BANKS-1][0:63];
  integer qdue [0:BANKS-1][0:63];
  reg [BANKS-1:0] holding=0, bank_granted;
  reg [BANKS*32-1:0] held_data=0;
  reg [BANKS*64-1:0] held_tag=0;
  reg [BANKS-1:0] request_blocked=0;
  reg [200:0] held_request [0:BANKS-1];
  integer b, c, k, endpoint, pointer, last_grant, queued, found;
  reg [99:0] key;
  reg [31:0] rng=@SEED@;
  function automatic [31:0] next_random(input [31:0] x);
    reg [31:0] y;
    begin y=x^(x<<13); y=y^(y>>17); next_random=y^(y<<5); end
  endfunction
  function automatic [32:0] matrix_base(input integer layer_id, input integer proj_id,
                                       input integer kind_id);
    begin
      matrix_base=0;
      case (layer_id*7+proj_id)
        @MATRIX_BASES@
        default: $fatal(1,"PARENT_ILLEGAL_MATRIX_IDENTITY");
      endcase
    end
  endfunction
  function automatic [31:0] read_image(input [32:0] address, input integer size);
    integer index, match_index;
    reg [511:0] beat;
    begin
      match_index=-1;
      for (index=0;index<IMAGE_RECORDS;index=index+1)
        if (image_address[index]==(address&33'h1ffffffc0)) match_index=index;
      if (match_index<0 || 32'(address[5:0])+size>64)
        $fatal(1,"PARENT_IMAGE_MISSING_OR_BOUNDARY address=%h",address);
      beat=image_data[match_index]>>{address[5:0],3'd0};
      read_image=size==2 ? {16'd0,beat[15:0]} : beat[31:0];
    end
  endfunction
  function automatic [31:0] read_logical(input integer kind_id, input integer layer_id,
                                        input integer proj_id, input integer row_id,
                                        input integer col_id);
    integer outputs, words, index, match_index, norm_index, before_bias;
    reg [32:0] address;
    reg [99:0] wanted;
    begin
      read_logical=0;
      outputs=proj_id==1 || proj_id==2 ? @KV_HEADS@*D :
        proj_id==4 || proj_id==5 ? I : H;
      words=(outputs+7)/8;
      if (kind_id==0) read_logical=read_image(33'h80000000+33'((row_id*H+col_id)*2),2);
      else if (kind_id==1 || kind_id==2)
        read_logical=read_image(matrix_base(layer_id,proj_id,kind_id)+
                               33'((row_id*words+col_id)*4),4);
      else if (kind_id==3)
        read_logical=read_image(matrix_base(layer_id,proj_id,kind_id)+
                               33'((row_id*outputs+col_id)*2),2);
      else if (kind_id==4) begin
        before_bias=proj_id==0 ? 0 : proj_id==1 ? H : H+@KV_HEADS@*D;
        read_logical=read_image(33'h6c000000+
          33'((layer_id*(H+2*@KV_HEADS@*D)+before_bias+col_id)*2),2);
      end else if (kind_id>=5 && kind_id<=7) begin
        norm_index=kind_id==7 ? 2*LAYERS : 2*layer_id+(kind_id==6);
        read_logical=read_image(33'h6d000000+33'((norm_index*H+col_id)*2),2);
      end else if (kind_id==11)
        read_logical=read_image(33'h6e000000+33'((row_id*D+col_id)*4),4);
      else begin
        wanted={4'(kind_id),32'(layer_id),32'(row_id),32'(col_id)};
        match_index=-1;
        for (index=0;index<stored;index=index+1)
          if (sparse_keys[index]==wanted) match_index=index;
        if (match_index<0)
          $fatal(1,"PARENT_READ_UNWRITTEN kind=%0d layer=%0d row=%0d col=%0d",
                 kind_id,layer_id,row_id,col_id);
        read_logical=sparse_values[match_index];
      end
    end
  endfunction
  always @(posedge clk) begin
    cycle=cycle+1;
    if (!rst_n) begin
      if ({token_ready,logit_valid,done,error,cancel_done,mem_req_valid} !== (5+BANKS)'(0))
        $fatal(1,"PARENT_RESET_STATUS");
    end else begin
      if (cycle>10000000) $fatal(1,"PARENT_PROGRESS");
      budget=64; bank_granted=0; last_grant=-1;
      for (b=0;b<BANKS;b=b+1) begin
        if (request_blocked[b] &&
            {mem_req_valid[b],mem_req_write[b],mem_req_kind[b*4+:4],
             mem_req_layer[b*32+:32],mem_req_proj[b*3+:3],mem_req_row[b*32+:32],
             mem_req_col[b*32+:32],mem_req_wdata[b*32+:32],mem_req_tag[b*64+:64]}
            !== held_request[b]) $fatal(1,"PARENT_REQUEST_STABILITY");
        request_blocked[b]=mem_req_valid[b] && !mem_req_ready[b];
        held_request[b]={mem_req_valid[b],mem_req_write[b],mem_req_kind[b*4+:4],
          mem_req_layer[b*32+:32],mem_req_proj[b*3+:3],mem_req_row[b*32+:32],
          mem_req_col[b*32+:32],mem_req_wdata[b*32+:32],mem_req_tag[b*64+:64]};
        if (mem_rsp_valid[b] && mem_rsp_ready[b]) begin
          if (!holding[b] || mem_rsp_tag[b*64+:64]!==held_tag[b*64+:64] ||
              mem_rsp_rdata[b*32+:32]!==held_data[b*32+:32])
            $fatal(1,"PARENT_RETAINED_RESPONSE");
          holding[b]=0; completed=completed+1;
        end
        if (mem_req_valid[b] && mem_req_ready[b]) begin
          if (qc[b]==64) $fatal(1,"PARENT_SERVICE_QUEUE_OVERFLOW");
          for (c=0;c<BANKS;c=c+1) begin
            if (holding[c] && held_tag[c*64+:64]===mem_req_tag[b*64+:64])
              $fatal(1,"PARENT_DUPLICATE_HELD_TAG");
            for (k=0;k<qc[c];k=k+1) begin
              pointer=qh[c]+k; if (pointer>=64) pointer=pointer-64;
              if (qtag[c][pointer]===mem_req_tag[b*64+:64])
                $fatal(1,"PARENT_DUPLICATE_QUEUED_TAG");
            end
          end
          qlayer[b][qt[b]]=mem_req_layer[b*32+:32];
          qproj[b][qt[b]]=mem_req_proj[b*3+:3];
          qrow[b][qt[b]]=mem_req_row[b*32+:32]; qcol[b][qt[b]]=mem_req_col[b*32+:32];
          qkind[b][qt[b]]=mem_req_kind[b*4+:4]; qwrite[b][qt[b]]=mem_req_write[b];
          qdata[b][qt[b]]=mem_req_wdata[b*32+:32]; qtag[b][qt[b]]=mem_req_tag[b*64+:64];
          qdue[b][qt[b]]=cycle+12;
          qt[b]=qt[b]==63 ? 0 : qt[b]+1; qc[b]=qc[b]+1; accepted=accepted+1;
        end
      end
      // Separate read and write endpoints, at most one four-byte grant per bank.
      for (k=0;k<2*BANKS;k=k+1) begin
        endpoint=rr+k; if (endpoint>=2*BANKS) endpoint=endpoint-2*BANKS;
        b=endpoint/2;
        if (!bank_granted[b] && !holding[b] && qc[b]>0 && cycle>=qdue[b][qh[b]] &&
            qwrite[b][qh[b]]==1'(endpoint&1) && budget>=4) begin
          c=qh[b];
          held_tag[b*64+:64]=qtag[b][c]; held_data[b*32+:32]=0;
          if (qwrite[b][c]) begin
            if (!(qkind[b][c]==8 || qkind[b][c]>=9 && qkind[b][c]!=11))
              $fatal(1,"PARENT_WRITE_PERSISTENT_IMAGE");
            key={qkind[b][c],qlayer[b][c],qrow[b][c],qcol[b][c]};
            found=-1;
            for (pointer=0;pointer<stored;pointer=pointer+1)
              if (sparse_keys[pointer]==key) found=pointer;
            if (found<0) begin
              if (stored==32768) $fatal(1,"PARENT_LOGICAL_MEMORY_CAPACITY");
              found=stored; stored=stored+1; sparse_keys[found]=key;
            end
            sparse_values[found]=qdata[b][c]; write_bytes=write_bytes+4;
          end else begin
            held_data[b*32+:32]=read_logical(qkind[b][c],qlayer[b][c],qproj[b][c],
                                            qrow[b][c],qcol[b][c]);
            read_bytes=read_bytes+4;
          end
          bytes_by_kind[qkind[b][c]]=bytes_by_kind[qkind[b][c]]+4;
          holding[b]=1; bank_granted[b]=1; budget=budget-4; last_grant=endpoint;
          qh[b]=qh[b]==63 ? 0 : qh[b]+1; qc[b]=qc[b]-1;
          serviced=serviced+1;
          if (first_service<0) first_service=cycle;
          last_service=cycle;
        end
      end
      if (budget<0 || budget>64) $fatal(1,"PARENT_BYTE_BUDGET");
      if (last_grant>=0) rr=last_grant==2*BANKS-1 ? 0 : last_grant+1;
      queued=0;
      for (b=0;b<BANKS;b=b+1) queued=queued+qc[b]+32'(holding[b]);
      if (queued>maximum_queued) maximum_queued=queued;
      mem_rsp_valid<=holding; mem_rsp_rdata<=held_data; mem_rsp_tag<=held_tag;
    end
  end
  always @(negedge clk) begin
    if (rst_n) begin
      rng=next_random(rng);
      c=0;
      for (b=0;b<BANKS;b=b+1) c=c+qc[b];
      for (b=0;b<BANKS;b=b+1) begin
        mem_req_ready[b]=(c<64);
        if (mem_req_ready[b]) c=c+1;
      end
    end
  end
  task run_token(input integer id, input integer pos, input integer fresh,
                 input integer phase, input integer offset);
    integer started, row, start_read, start_write;
    reg blocked;
    reg [63:0] previous_logit;
    begin
      @(negedge clk); token_valid=1; token_id=id; token_pos=pos;
      new_sequence=1'(fresh); token_phase=1'(phase); logit_ready=1;
      @(posedge clk); while (!token_ready) @(posedge clk);
      started=cycle; start_read=read_bytes; start_write=write_bytes; row=0; blocked=0;
      if (logit_valid!==0) $fatal(1,"PARENT_SAME_EDGE_LOGIT");
      @(negedge clk); token_valid=0;
      @(posedge clk);
      while (!done) begin
        if (error!==0 || token_ready!==0) $fatal(1,"PARENT_TOKEN_ERROR");
        if (blocked && {logit_index,logit_data}!==previous_logit)
          $fatal(1,"PARENT_LOGIT_STABILITY");
        blocked=logit_valid && !logit_ready; previous_logit={logit_index,logit_data};
        if (logit_valid && logit_ready) begin
          if (row>=VOCAB || logit_index!==32'(row) || logit_data!==expected[offset+row])
            $fatal(1,"PARENT_LOGIT_MISMATCH row=%0d actual=%0d expected=%0d",
                   row,logit_data,$signed(expected[offset+row]));
          row=row+1; compared=compared+1;
        end
        @(posedge clk);
      end
      if (error!==0 || row!=VOCAB) $fatal(1,"PARENT_LOGIT_COUNT_OR_ERROR");
      tokens=tokens+1;
      $display("PARENT_TOKEN id=%0d pos=%0d cycles=%0d read_bytes=%0d write_bytes=%0d",
               id,pos,cycle-started,read_bytes-start_read,write_bytes-start_write);
      @(posedge clk); #1;
      if (done!==0) $fatal(1,"PARENT_DONE_PULSE");
    end
  endtask
  initial begin
    for (b=0;b<BANKS;b=b+1) begin qh[b]=0; qt[b]=0; qc[b]=0; end
    for (k=0;k<16;k=k+1) bytes_by_kind[k]=0;
    $readmemh("@ADDRESSES@",image_address); $readmemh("@DATA@",image_data);
    $readmemh("@EXPECTED@",expected);
    repeat(3) @(negedge clk); rst_n=1;
    @TOKENS@
    repeat(10) @(posedge clk);
    if (compared!=N || tokens!=@TOKEN_COUNT@ || accepted!=serviced ||
        accepted!=completed || holding!==0)
      $fatal(1,"PARENT_CONSERVATION accepted=%0d serviced=%0d completed=%0d",
             accepted,serviced,completed);
    for (b=0;b<BANKS;b=b+1) if (qc[b]!=0) $fatal(1,"PARENT_DRAIN");
    $display("PARENT_PASS banks=%0d profile=3 mode=@MODE@ seed=@SEED@ tokens=%0d compared=%0d commands=%0d read_bytes=%0d write_bytes=%0d max_queued=%0d first=%0d last=%0d",
             BANKS,tokens,compared,accepted,read_bytes,write_bytes,maximum_queued,
             first_service,last_service);
    for (k=0;k<16;k=k+1)
      if (bytes_by_kind[k]!=0) $display("PARENT_TRAFFIC kind=%0d bytes=%0d",k,bytes_by_kind[k]);
    $finish;
  end
endmodule
"""


def parent_bench(directory, relative, seed=17, banks=1, mode=0, tokens=3,
                 geometry=Geometry()):
    if banks not in (1, 2, 4, 8):
        raise ValueError("unmodified parent supports only BANKS=1,2,4,8")
    image = Image(geometry, seed)
    oracle = Inference(image, mode)
    sequence = [(0, 0, True, 0), (1, 1, False, 1), (2, 0, True, 0)][:tokens]
    expected = [value for token, pos, fresh, _ in sequence
                for value in oracle.token(token, pos, fresh)]
    label = f"parent-l{geometry.layers}-b{banks}-m{mode}-s{seed}"
    images = directory / "checkpoint-images"
    images.mkdir(exist_ok=True)
    paths = {}
    records = image.records()
    for name, values, width in (
            ("addresses", [address for address, _ in records], 33),
            ("data", [int.from_bytes(data, "little") for _, data in records], 512),
            ("expected", expected, 32)):
        path = images / f"{label}-{name}.hex"
        path.write_text("".join(f"{value & ((1 << width) - 1):0{(width + 3) // 4}x}\n"
                                for value in values))
        paths[name.upper()] = relative(path)
    bases = []
    for (layer, projection), matrix in image_layout(geometry)["matrices"].items():
        bases.append(f"{layer * 7 + projection}: case (kind_id)\n"
                     f"1: matrix_base=33'h{matrix['qweight']:x};\n"
                     f"2: matrix_base=33'h{matrix['qzeros']:x};\n"
                     f"3: matrix_base=33'h{matrix['scales']:x};\n"
                     'default: $fatal(1,"PARENT_MATRIX_KIND"); endcase')
    params = geometry.parameters() | dict(PROFILE=3, BANKS=banks, CACHE_MODE=mode,
                                          INT4_ASYM=0, QUEUE_DEPTH=3, TILE_K=16,
                                          TILE_ROWS=1)
    substitutions = dict(BANKS=banks, H=geometry.hidden, I=geometry.intermediate,
                         D=geometry.head_dim, LAYERS=geometry.layers, CONTEXT=geometry.context,
                         VOCAB=geometry.vocab, KV_HEADS=geometry.kv_heads, SEED=seed, MODE=mode,
                         IMAGE_RECORDS=len(records), N=len(expected), TOKEN_COUNT=len(sequence),
                         MATRIX_BASES="\n".join(bases),
                         PARAMETERS=",".join(f".{key}({value})" for key, value in params.items()),
                         TOKENS="\n".join(f"run_token({token},{pos},{int(fresh)},{phase},"
                                          f"{index * geometry.vocab});"
                                          for index, (token, pos, fresh, phase) in enumerate(sequence)),
                         **paths)
    bench = PARENT_TB
    for key, value in substitutions.items():
        bench = bench.replace(f"@{key}@", str(value))
    return bench, dict(geometry=geometry.__dict__, image_sha256=image.digest,
                       expected_logits=expected, parameters=params, **POLICY)
