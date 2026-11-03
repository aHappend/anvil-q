"""External-memory, public-logit decoder comparisons against the sequential model."""

from execution import ROOT, relative
from model import Decoder, Geometry, Image


TOP_BENCH = r"""
module top_tb;
  parameter H=8,I=8,QH=2,KH=1,D=8,V=8,M=16,N=1;
  localparam QD=QH*D,KD=KH*D;
  localparam MAX=(I>QD ? (I>H ? I:H) : (QD>H ? QD:H));
  localparam BLOCKS=(MAX+7)/8;
  reg clk=0,rst_n,cancel=0,token_valid=0,new_sequence=0,token_phase=0;
  always #5 clk=~clk;
  reg [31:0] token_id=0,token_pos=0;
  wire token_ready,logit_valid,done,error,cancel_done;
  reg logit_ready=0;
  wire [31:0] logit_index,logit_data;
  wire mem_req_valid,mem_req_write,mem_rsp_ready;
  reg mem_req_ready=0,mem_rsp_valid=0,mem_rsp_error=0;
  wire [3:0] mem_req_kind;
  wire [2:0] mem_req_proj;
  wire [31:0] mem_req_layer,mem_req_row,mem_req_col,mem_req_wdata;
  wire [63:0] mem_req_tag;
  reg [31:0] mem_rsp_rdata=0;
  reg [63:0] mem_rsp_tag=0;
  reg draft_valid=0;
  wire draft_ready,commit_valid,think_active;
  reg commit_ready=0;
  wire [2:0] commit_count;
  wire [159:0] commit_tokens;
  wire [31:0] commit_pos;
  wire csr_ready,csr_rsp_valid,csr_error;
  wire [31:0] csr_rdata;
  integer cycle=0,active_case=0,logit_count=0,commit_seen=0,completed=0;
  integer req_count=0,write_count=0,key_count=0,value_count=0,bias_count=0;
  integer tail=0,front=0,queued=0,queue_delay[0:63];
  reg [63:0] queue_tag[0:63];
  reg [31:0] queue_data[0:63];
  reg [31:0] embedding[0:V*H-1];
  reg [31:0] qweight[0:7*MAX*BLOCKS-1],zero_image[0:7*MAX*BLOCKS-1];
  reg [31:0] scale_image[0:7*MAX*MAX-1],gamma[0:16*MAX-1],rope[0:M*D-1];
  reg [31:0] scratch[0:15*MAX-1],keys[0:M*KD-1],values[0:M*KD-1];
  reg scratch_valid[0:15*MAX-1],key_valid[0:M*KD-1],value_valid[0:M*KD-1];
  reg [31:0] expected_scratch[0:N*15*MAX-1],expected_initial[0:N*H-1];
  reg [31:0] expected_keys[0:N*KD-1],expected_values[0:N*KD-1];
  reg [31:0] expected_logits[0:N*V-1],host_tokens[0:N-1],host_phases[0:N-1];
  reg [31:0] expected_tokens[0:N-1];
  integer writes[0:15*MAX-1];
  integer j,c,guard,address;
  reg [31:0] expected_write,read_data;
  reg held_request=0,held_logit=0,held_commit=0;
  reg [199:0] saved_request;
  reg [63:0] saved_logit;
  reg [194:0] saved_commit;
  integer last_logit_cycle=-1,last_commit_cycle=-1;
  reg [4095:0] prefix;
  reg [8191:0] filename;
  anvil_qn1_top #(.COMPACT(1),.NUM_LAYERS(1),.HIDDEN_SIZE(H),
    .INTERMEDIATE_SIZE(I),.NUM_Q_HEADS(QH),.NUM_KV_HEADS(KH),.HEAD_DIM(D),
    .VOCAB_SIZE(V),.MAX_SEQ_LEN(M),.GROUP_SIZE(8),.BANKS(1),.QUEUE_DEPTH(3)) dut(
    .clk(clk),.rst_n(rst_n),.cancel(cancel),.token_valid(token_valid),
    .new_sequence(new_sequence),.token_phase(token_phase),.logit_ready(logit_ready),
    .token_id(token_id),.token_pos(token_pos),.token_ready(token_ready),
    .logit_valid(logit_valid),.done(done),.error(error),.cancel_done(cancel_done),
    .logit_index(logit_index),.logit_data(logit_data),
    .mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),
    .mem_req_write(mem_req_write),.mem_req_kind(mem_req_kind),
    .mem_req_layer(mem_req_layer),.mem_req_proj(mem_req_proj),.mem_req_row(mem_req_row),
    .mem_req_col(mem_req_col),.mem_req_wdata(mem_req_wdata),.mem_req_tag(mem_req_tag),
    .mem_rsp_valid(mem_rsp_valid),.mem_rsp_error(mem_rsp_error),
    .mem_rsp_ready(mem_rsp_ready),.mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_tag(mem_rsp_tag),
    .draft_valid(draft_valid),.draft_ready(draft_ready),.draft_count(3'd0),
    .draft_tokens(128'd0),.draft_parents(12'd0),.commit_valid(commit_valid),
    .commit_ready(commit_ready),.commit_count(commit_count),.commit_tokens(commit_tokens),
    .commit_pos(commit_pos),.think_active(think_active),
    .csr_valid(1'b0),.csr_ready(csr_ready),.csr_write(1'b0),.csr_addr(12'd0),
    .csr_wdata(32'd0),.csr_wstrb(4'd0),.csr_rsp_valid(csr_rsp_valid),
    .csr_rsp_ready(1'b1),.csr_rdata(csr_rdata),.csr_error(csr_error));
  task reset_outputs;
    begin
      if ({token_ready,logit_valid,done,error,cancel_done,logit_index,logit_data,
           mem_req_valid,mem_req_write,mem_req_kind,mem_req_layer,mem_req_proj,
           mem_req_row,mem_req_col,mem_req_wdata,mem_req_tag,mem_rsp_ready,
           draft_ready,commit_valid,commit_count,commit_tokens,commit_pos,think_active,
           csr_ready,csr_rsp_valid,csr_rdata,csr_error}!==0)
        $fatal(1,"TOP_RESET_XZ_OR_NONZERO");
    end
  endtask
  always @(posedge clk or negedge clk) if (!rst_n) reset_outputs();
  always @(negedge clk) begin
    if (rst_n) begin
      mem_req_ready=(cycle%7!=3);
      logit_ready=(cycle%5!=1 && cycle%5!=2);
      commit_ready=(cycle%11>=5);
      mem_rsp_valid=queued>0 && queue_delay[front]<=cycle;
      mem_rsp_tag=mem_rsp_valid ? queue_tag[front] : 0;
      mem_rsp_rdata=mem_rsp_valid ? queue_data[front] : 0;
    end else begin mem_req_ready=0;logit_ready=0;commit_ready=0;mem_rsp_valid=0;end
  end
  always @(posedge clk) begin
    if (rst_n) begin
      cycle=cycle+1;
      if (error!==0 || cancel_done!==0 || think_active!==0 || draft_ready!==0)
        $fatal(1,"TOP_UNEXPECTED_STATUS case=%0d cycle=%0d error=%b cancel=%b think=%b draft=%b",
          active_case,cycle,error,cancel_done,think_active,draft_ready);
      if (held_request && (mem_req_valid!==1 ||
          {mem_req_write,mem_req_kind,mem_req_layer,mem_req_proj,mem_req_row,
           mem_req_col,mem_req_wdata,mem_req_tag}!==saved_request))
        $fatal(1,"TOP_REQUEST_STALL");
      if (held_logit && (logit_valid!==1 || {logit_index,logit_data}!==saved_logit))
        $fatal(1,"TOP_LOGIT_STALL");
      if (held_commit && (commit_valid!==1 ||
          {commit_count,commit_tokens,commit_pos}!==saved_commit))
        $fatal(1,"TOP_COMMIT_STALL");
      held_request=mem_req_valid && !mem_req_ready;
      saved_request={mem_req_write,mem_req_kind,mem_req_layer,mem_req_proj,
                     mem_req_row,mem_req_col,mem_req_wdata,mem_req_tag};
      held_logit=logit_valid && !logit_ready; saved_logit={logit_index,logit_data};
      held_commit=commit_valid && !commit_ready;
      saved_commit={commit_count,commit_tokens,commit_pos};
      if (mem_rsp_valid && mem_rsp_ready) begin
        if (queued<=0 || mem_rsp_tag!==queue_tag[front]) $fatal(1,"RESPONSE_SCOREBOARD");
        front=(front+1)%64; queued=queued-1;
      end
      if (mem_req_valid && mem_req_ready) begin
        if ((^{mem_req_kind,mem_req_layer,mem_req_proj,mem_req_row,mem_req_col,
              mem_req_wdata,mem_req_tag})===1'bx) $fatal(1,"ACTIVE_REQUEST_XZ");
        if (mem_req_layer!=0 || mem_req_col>=MAX) $fatal(1,"REQUEST_ADDRESS_BOUND");
        read_data=0;
        if (mem_req_write) begin
          if (mem_req_wdata[31:16]!==0) $fatal(1,"WRITE_RESERVED_BITS");
          if (mem_req_kind==8) begin
            if (mem_req_row>=15 || mem_req_row==13) $fatal(1,"SCRATCH_ADDRESS");
            address=mem_req_row*MAX+mem_req_col;
            expected_write=mem_req_row==0 && writes[address]==0 ?
              expected_initial[active_case*H+mem_req_col] :
              expected_scratch[active_case*15*MAX+address];
            if (mem_req_wdata!==expected_write)
              $fatal(1,"SCRATCH_COMPARE case=%0d slot=%0d coordinate=%0d write=%0d got=%h expected=%h",
                active_case,mem_req_row,mem_req_col,writes[address],mem_req_wdata,expected_write);
            if (writes[address]>=(mem_req_row==0 ? 2:1)) $fatal(1,"DUPLICATE_SCRATCH_WRITE");
            scratch[address]=mem_req_wdata; scratch_valid[address]=1;
            writes[address]=writes[address]+1;
          end else if (mem_req_kind==9 || mem_req_kind==10) begin
            if (mem_req_row!=active_case || mem_req_col>=KD) $fatal(1,"KV_ADDRESS");
            address=mem_req_row*KD+mem_req_col;
            if (mem_req_kind==9) begin
              if (key_valid[address]) $fatal(1,"DUPLICATE_KEY");
              if (mem_req_wdata!==expected_keys[active_case*KD+mem_req_col])
                $fatal(1,"KEY_COMPARE case=%0d coordinate=%0d got=%h expected=%h",
                  active_case,mem_req_col,mem_req_wdata,expected_keys[active_case*KD+mem_req_col]);
              keys[address]=mem_req_wdata;key_valid[address]=1;key_count=key_count+1;
            end else begin
              if (value_valid[address]) $fatal(1,"DUPLICATE_VALUE");
              if (mem_req_wdata!==expected_values[active_case*KD+mem_req_col])
                $fatal(1,"VALUE_COMPARE");
              values[address]=mem_req_wdata;value_valid[address]=1;value_count=value_count+1;
            end
          end else $fatal(1,"ILLEGAL_WRITE_KIND");
          write_count=write_count+1;
        end else case (mem_req_kind)
          0: begin
            if (mem_req_row>=V || mem_req_col>=H) $fatal(1,"EMBEDDING_EXTENT");
            read_data=embedding[mem_req_row*H+mem_req_col];
          end
          1: begin
            if (mem_req_proj>6 || mem_req_row>=MAX || mem_req_col>=BLOCKS)
              $fatal(1,"QWEIGHT_EXTENT");
            read_data=qweight[(mem_req_proj*MAX+mem_req_row)*BLOCKS+mem_req_col];
          end
          2: begin
            if (mem_req_proj>6 || mem_req_row>=MAX || mem_req_col>=BLOCKS)
              $fatal(1,"ZERO_EXTENT");
            read_data=zero_image[(mem_req_proj*MAX+mem_req_row)*BLOCKS+mem_req_col];
          end
          3: begin
            if (mem_req_proj>6 || mem_req_row>=MAX) $fatal(1,"SCALE_EXTENT");
            read_data=scale_image[(mem_req_proj*MAX+mem_req_row)*MAX+mem_req_col];
          end
          4: begin bias_count=bias_count+1;$fatal(1,"NATIVE_BIAS_REQUEST");end
          5,6,7,12,13: begin
            if (mem_req_row!=0) $fatal(1,"GAMMA_ADDRESS");
            read_data=gamma[mem_req_kind*MAX+mem_req_col];
          end
          8: begin
            if (mem_req_row>=15) $fatal(1,"SCRATCH_READ_ADDRESS");
            address=mem_req_row*MAX+mem_req_col;
            if (!scratch_valid[address]) $fatal(1,"UNINITIALIZED_SCRATCH_READ");
            read_data=scratch[address];
          end
          9,10: begin
            if (mem_req_row>active_case || mem_req_col>=KD) $fatal(1,"CAUSAL_KV_ADDRESS");
            address=mem_req_row*KD+mem_req_col;
            if (mem_req_kind==9) begin
              if (!key_valid[address]) $fatal(1,"UNINITIALIZED_KEY_READ");
              read_data=keys[address];
            end else begin
              if (!value_valid[address]) $fatal(1,"UNINITIALIZED_VALUE_READ");
              read_data=values[address];
            end
          end
          11: begin
            if (mem_req_row!=active_case || mem_req_col>=D) $fatal(1,"ROPE_ADDRESS");
            read_data=rope[mem_req_row*D+mem_req_col];
          end
          default: $fatal(1,"UNDEFINED_MEMORY_KIND");
        endcase
        if (queued>=64) $fatal(1,"QUEUE_OVERFLOW");
        for (j=0;j<queued;j=j+1)
          if (queue_tag[(front+j)%64]===mem_req_tag) $fatal(1,"DUPLICATE_TAG");
        queue_data[tail]=read_data; queue_tag[tail]=mem_req_tag;
        queue_delay[tail]=cycle+2+(req_count%3);
        tail=(tail+1)%64;queued=queued+1;req_count=req_count+1;
      end
      if (logit_valid && logit_ready) begin
        if (logit_count>=V || logit_index!==logit_count ||
            logit_data!==expected_logits[active_case*V+logit_count])
          $fatal(1,"LOGIT_COMPARE case=%0d index=%0d got_index=%0d got=%h expected=%h",
            active_case,logit_count,logit_index,logit_data,expected_logits[active_case*V+logit_count]);
        logit_count=logit_count+1;last_logit_cycle=cycle;
      end
      if (commit_valid) begin
        if (host_phases[active_case]!=1 || logit_count!=V || queued!=0 ||
            commit_count!==3'd1 || commit_pos!==active_case+1 ||
            commit_tokens!=={128'd0,expected_tokens[active_case]})
          $fatal(1,"COMMIT_COMPARE case=%0d logits=%0d count=%0d pos=%0d got=%h expected=%h",
            active_case,logit_count,commit_count,commit_pos,commit_tokens,expected_tokens[active_case]);
        if (commit_ready) begin
          if (commit_seen!=0) $fatal(1,"DUPLICATE_COMMIT");
          commit_seen=1;last_commit_cycle=cycle;
        end
      end
      if (done) begin
        if (logit_count!=V || queued!=0 || token_ready!==0 ||
            cycle<=last_logit_cycle || (host_phases[active_case]==1 &&
              (commit_seen!=1 || cycle<=last_commit_cycle))) $fatal(1,"DONE_ORDER");
        completed=completed+1;
      end
    end
  end
  initial begin
    rst_n=0;
    for (j=0;j<15*MAX;j=j+1) begin scratch_valid[j]=0;scratch[j]=0;writes[j]=0;end
    for (j=0;j<M*KD;j=j+1) begin key_valid[j]=0;value_valid[j]=0;keys[j]=0;values[j]=0;end
    #1;reset_outputs();
    if (!$value$plusargs("images=%s",prefix)) $fatal(1,"NO_IMAGES");
    filename={prefix,"/embedding.hex"};$readmemh(filename,embedding);
    filename={prefix,"/qweight.hex"};$readmemh(filename,qweight);
    filename={prefix,"/zero.hex"};$readmemh(filename,zero_image);
    filename={prefix,"/scale.hex"};$readmemh(filename,scale_image);
    filename={prefix,"/gamma.hex"};$readmemh(filename,gamma);
    filename={prefix,"/rope.hex"};$readmemh(filename,rope);
    filename={prefix,"/expected-scratch.hex"};$readmemh(filename,expected_scratch);
    filename={prefix,"/expected-initial.hex"};$readmemh(filename,expected_initial);
    filename={prefix,"/expected-key.hex"};$readmemh(filename,expected_keys);
    filename={prefix,"/expected-value.hex"};$readmemh(filename,expected_values);
    filename={prefix,"/expected-logits.hex"};$readmemh(filename,expected_logits);
    filename={prefix,"/host-token.hex"};$readmemh(filename,host_tokens);
    filename={prefix,"/host-phase.hex"};$readmemh(filename,host_phases);
    filename={prefix,"/expected-token.hex"};$readmemh(filename,expected_tokens);
    @(negedge clk);rst_n=1;
    for (c=0;c<N;c=c+1) begin
      @(negedge clk);active_case=c;logit_count=0;commit_seen=0;
      for (j=0;j<15*MAX;j=j+1) begin writes[j]=0;scratch_valid[j]=0;end
      guard=0;
      while (token_ready!==1 && guard<100) begin
        @(negedge clk);guard=guard+1;
      end
      if (token_ready!==1) $fatal(1,"TOKEN_NOT_READY");
      token_id=host_tokens[c];token_pos=c;token_phase=host_phases[c];
      new_sequence=(c==0);token_valid=1;
      @(posedge clk);
      if (token_ready!==1) $fatal(1,"TOKEN_HANDSHAKE");
      #1;if (token_ready!==0 || logit_valid!==0 || done!==0) $fatal(1,"TOKEN_ACCEPT_ORDER");
      @(negedge clk);token_valid=0;new_sequence=0;
      guard=0;
      while (completed<c+1 && guard<450000) begin @(negedge clk);guard=guard+1;end
      if (completed!=c+1) $fatal(1,"TOKEN_LIVENESS case=%0d",c);
      if (key_count!=(c+1)*KD || value_count!=(c+1)*KD) $fatal(1,"KV_COVERAGE");
    end
    $display("SUMMARY transactions=%0d logits=%0d key_writes=%0d value_writes=%0d memory_requests=%0d cycles=%0d",
      completed,completed*V,key_count,value_count,req_count,cycle);
    $finish;
  end
  initial begin repeat (500000) @(posedge clk);$fatal(1,"CYCLE_BOUND");end
endmodule
"""


def generate_images(path, geometry, seed, cases):
    path.mkdir(exist_ok=False)
    image = Image(geometry, seed)
    model = Decoder(image)
    tables = image.memory_tables()
    tables.update({name: [] for name in
                   ("expected-scratch", "expected-initial", "expected-key",
                    "expected-value", "expected-logits", "host-token", "host-phase",
                    "expected-token")})
    token = 3 % geometry.vocabulary
    records = []
    for position in range(cases):
        if position == 1:
            token = 4 % geometry.vocabulary
        result = model.evaluate(token, position)
        tables["host-token"].append(token)
        tables["host-phase"].append(int(position != 0))
        tables["expected-token"].append(result["argmax"])
        tables["expected-initial"].extend(result["initial"])
        tables["expected-key"].extend(result["keys"][0])
        tables["expected-value"].extend(result["values"][0])
        tables["expected-logits"].extend(result["logits"])
        scratch = [0] * (15 * geometry.maximum)
        for slot, values in result["stages"][0].items():
            scratch[slot * geometry.maximum:slot * geometry.maximum + len(values)] = values
        tables["expected-scratch"].extend(scratch)
        records.append({"position": position, "input_token": token,
                        "argmax": result["argmax"]})
        token = result["argmax"]
    for name, values in tables.items():
        with (path / f"{name}.hex").open("x") as file:
            file.writelines(f"{value:08x}\n" for value in values)
    return records


def run_top(run, simulator="icarus", cases=1, geometry=Geometry(), seed=17):
    images = run.path / "checkpoint-images"
    records = generate_images(images, geometry, seed, cases)
    bench = run.path / "top_tb.sv"
    bench.write_text(TOP_BENCH)
    sources = [str(path.relative_to(ROOT)) for path in sorted((ROOT / "rtl").glob("anvil_qn1_*.sv"))]
    parameters = {"H": geometry.hidden, "I": geometry.intermediate,
                  "QH": geometry.q_heads, "KH": geometry.kv_heads,
                  "D": geometry.head_dim, "V": geometry.vocabulary,
                  "M": geometry.max_sequence, "N": cases}
    if simulator == "icarus":
        binary = run.path / "top.vvp"
        run.execute(["iverilog", "-g2012", "-Wall", "-s", "top_tb",
                     *[f"-Ptop_tb.{key}={value}" for key, value in parameters.items()],
                     "-o", relative(binary), *sources, relative(bench)], "top-compile")
        text = run.execute(["vvp", relative(binary), f"+images={relative(images)}"],
                           "top-simulation", timeout=600)
    else:
        objects = run.path / "obj-top"
        run.execute(["verilator", "--binary", "--timing", "-Wno-fatal", "-j", "2",
                     "--top-module", "top_tb",
                     *[f"-G{key}={value}" for key, value in parameters.items()],
                     "--Mdir", relative(objects), "-o", "simulate", *sources,
                     relative(bench)], "top-compile")
        text = run.execute([relative(objects / "simulate"), f"+images={relative(images)}"],
                           "top-simulation")
        for pattern in ("*.o", "*.a", "*.gch"):
            for file in objects.glob(pattern):
                file.unlink()
    summary = (f"SUMMARY transactions={cases} logits={cases*geometry.vocabulary} "
               f"key_writes={cases*geometry.kv_dimension} value_writes={cases*geometry.kv_dimension}")
    if text.count(summary) != 1:
        raise AssertionError("missing full-frame/KV comparisons")
    return {"transactions": records, "simulator": simulator, "seed": seed,
            "geometry": vars(geometry), "raw_summary": text[-1000:]}
