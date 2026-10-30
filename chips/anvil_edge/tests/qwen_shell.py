"""Official Qwen tables through autonomous boot and real minimum-geometry Q1.

The periodically repeated synthetic embedding tensor has sixteen distinct rows.
The numerical oracle evaluates each distinct output dot product once; repetition
cannot change the lowest-index argmax. Inactive physical rows are zero. This is
an exact synthetic-weight diagnostic, never a pretrained-model benchmark.
"""

import hashlib
import json
import re
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from numerics import Geometry, Reference
from official import ROOT, manifest
from qwen_integration import prepare, save, validate_table_source
from qwen_tables import VOCABULARY, require
from storage import BOOT, KINDS, synthetic_image, words


CAPACITY = 151936
SEQUENCE = 64
MAX_NEW = 8
PERIOD = 16


def build_inputs(directory, compact=False, physical_capacity=None, *, table_source=None):
    """Runs with the already installed, independently identified official oracle."""
    directory = Path(directory)
    if table_source is not None:
        require(not compact, "Complete table source is not a compact fixture")
        table_source = Path(table_source)
        require(not table_source.is_absolute() and ".." not in table_source.parts and
                table_source.parts[:3] == directory.parts[:3],
                "Complete tables must belong to the same fresh invocation")
        table_source = ROOT / table_source
        info = json.loads((table_source / "complete-table-fixture.json").read_bytes())
        validate_table_source(info, table_source / "tables.hex")
    elif not compact:
        prepare(directory)
    directory = ROOT / directory
    vocabulary, capacity = (257, 257) if compact else (VOCABULARY, CAPACITY)
    if physical_capacity is not None:
        require(compact and 257 <= physical_capacity <= 65537,
                "Capacity sweep is a bounded synthetic-shell diagnostic only")
        capacity = physical_capacity
    if compact:
        vectors = [
            {"input_utf8_hex": b"ABC".hex(), "token_ids": [256, 67]},
            {"input_utf8_hex": b"ABCD".hex(), "token_ids": [256, 67, 68]},
        ]
        payloads = None
    else:
        producer = table_source if table_source is not None else directory
        info = json.loads((producer / "complete-table-fixture.json").read_bytes())
        vectors = json.loads((producer / "official-vectors.json").read_bytes())[:5]
        payloads = {0x200: words(*info["metadata"])}
        for entry in info["tables"]:
            data = (producer / f"table-{entry['kind']:03x}.bin").read_bytes()
            require(hashlib.sha256(data).hexdigest() == entry["sha256"],
                    "Qwen table changed before shell image construction")
            payloads[entry["kind"]] = data
    build_shell_inputs(
        directory, vocabulary, capacity, vectors, payloads,
        scope=("Synthetic compact scoreboard regression, not official tables; "
               if compact else "Complete pinned Qwen tokenizer; "),
        tokenizer_identity=manifest()["bundle_sha256"],
        prompt_oracle=("Independent synthetic AB merge" if compact else
                       "Installed pinned official tokenizer, add_special_tokens=False"),
        piece_byte_offset=0 if compact else 33,
    )
    print(f"QWEN_SHELL_REFERENCE prompts={len(vectors)} max_new_tokens={MAX_NEW} "
          f"active={vocabulary} capacity={capacity} compact={compact}")


def build_shell_inputs(directory, vocabulary, capacity, vectors, payloads, *,
                       scope, tokenizer_identity, prompt_oracle,
                       piece_byte_offset=None, provenance=None):
    """Serialize shared real-core fixtures without selecting tokenizer semantics."""
    directory = ROOT / directory
    reference = Reference(Geometry(vocabulary=PERIOD, sequence=SEQUENCE), 17)
    initial = dict(reference.initial)

    def tensor_word(kind, layer, projection, row, column):
        if kind == 0:
            return (initial[kind, layer, projection, row % PERIOD, column]
                    if row < vocabulary else 0)
        # The serialized activation slot has padded/unused rows; keep them zero.
        return initial.get((kind, layer, projection, row, column), 0)

    fixtures = []
    for bypass in (0, 1):
        fixture = synthetic_image(
            vocabulary, capacity=capacity, table_payloads=payloads,
            geometry={"sequence": SEQUENCE}, max_pretoken=4096,
            tensor_word=tensor_word, config_values={12: MAX_NEW, 16: bypass},
        )
        path = directory / f"shell-flash-{bypass}.hex"
        with path.open("x", encoding="ascii") as output:
            for value in fixture["image"]:
                output.write(f"{value:02x}\n")
        fixtures.append(fixture)
    fixture = fixtures[0]
    eos = struct.unpack_from("<I", fixture["segments"][0x200], 28)[0]
    require(fixtures[1]["regions"] == fixture["regions"] and
            fixtures[1]["destinations"] == fixture["destinations"],
            "Transport-only images changed the tensor layout")
    regions = {record[:3]: record for record in fixture["regions"]}

    def address(key):
        kind, layer, projection, row, column = key
        record = regions[kind, layer, projection]
        _, _, _, storage, offset, rows, columns, _, _, _ = record
        require(0 <= row < rows and 0 <= column < columns, "Oracle tensor bounds")
        return fixture["destinations"][storage] + offset + 4 * (row * columns + column)

    # Vocabulary pieces are read from the independently converted official input.
    records, pieces = fixture["segments"][0x201][32:], fixture["segments"][0x202][32:]
    cases = []
    for case, vector in enumerate(vectors):
        ref = Reference(Geometry(vocabulary=PERIOD, sequence=SEQUENCE), 17)
        operations, generated = list(vector["token_ids"]), []
        require(1 < len(operations) and len(operations) + MAX_NEW <= SEQUENCE,
                "Prompt must exercise multi-token prefill without sequence truncation")
        prompt_count = len(operations)
        position = 0
        winners, write_operations = [], []
        while position < len(operations):
            previous_writes = len(ref.trace)
            logits = ref.token(operations[position] % PERIOD, position)
            write_operations.extend([position] * (len(ref.trace) - previous_writes))
            winner = max(range(PERIOD), key=lambda token: (logits[token], -token))
            winners.append({"position": position, "logits_period": logits,
                            "selected": winner, "active_logit_count": vocabulary,
                            "physical_logit_count": capacity})
            if position >= prompt_count - 1:
                require(winner != eos, "Synthetic output unexpectedly selected EOS")
                generated.append(winner)
                if len(generated) < MAX_NEW:
                    operations.append(winner)
            position += 1
        require(len(generated) == MAX_NEW and len(operations) == prompt_count + MAX_NEW - 1,
                "Reference stopping/feedback count")
        output = bytearray()
        for token in generated:
            offset, length, flags = struct.unpack_from("<QII", records, 16 * token)
            require(flags == 1, "Synthetic argmax selected a special/malformed piece")
            output.extend(pieces[offset:offset + length])
        output.decode("utf-8", errors="strict")
        if piece_byte_offset is not None:
            require(bytes(output) == bytes(token + piece_byte_offset for token in generated),
                    "Periodic head must emit independently checked vocabulary pieces")
        trace = [(address(tuple(row["key"])), row["word"]) for row in ref.trace]
        inputs = list(bytes.fromhex(vector["input_utf8_hex"]))
        fields = {"input": inputs, "tokens": operations, "output": list(output),
                  "write-address": [row[0] for row in trace],
                  "write-data": [row[1] for row in trace],
                  "write-operation": write_operations}
        files = {}
        for name, values in fields.items():
            path = directory / f"shell-case-{case}-{name}.hex"
            with path.open("x", encoding="ascii") as stream:
                for value in values:
                    stream.write(f"{value:016x}\n" if name == "write-address" else f"{value:08x}\n")
            files[name] = {"path": str(path.relative_to(ROOT)),
                           "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                           "count": len(values)}
        cases.append({
            "case": case, "prompt_utf8_hex": vector["input_utf8_hex"],
            "expected_prompt_ids": vector["token_ids"], "core_operation_ids": operations,
            "generated_ids": generated, "output_utf8_hex": output.hex(),
            "winners": winners, "activation_write_count": len(trace), "files": files,
        })
    segments, cursor = [], 32 + 7 * 8 + len(KINDS) * 40
    for kind in KINDS:
        data = fixture["segments"][kind]
        segments.append({"kind": kind, "base": fixture["destinations"][kind],
                         "bytes": len(data), "flash_offset": cursor,
                         "sha256": hashlib.sha256(data).hexdigest()})
        cursor += len(data) + (-len(data) % 4)
    end = max(row["base"] + row["bytes"] + 4 for row in segments)
    extent = 1 << (max(end, cursor) - 1).bit_length()
    require(extent <= 1 << 24 and cursor == len(fixture["image"]),
            "Image must fit standard 24-bit SPI NOR")
    save(directory / "shell-reference.json", {
        "scope": scope +
                 "real production H8/L1 core, "
                 "independent synthetic periodic tensors; not pretrained inference, "
                 "default geometry, other tokenizer families, STA or physical acceptance",
        "tokenizer_bundle_sha256": tokenizer_identity,
        "prompt_oracle": prompt_oracle,
        "tokenizer_provenance": provenance,
        "active_vocabulary": vocabulary, "physical_capacity": capacity,
        "embedding_period": PERIOD, "synthetic_weight_seed": 17,
        "numerical_equivalence": "All active embedding/head rows repeat the sixteen "
                                 "oracle rows. Other tensors are identical. Inactive "
                                 "physical rows are zero and filtered by the adapter. "
                                 "Argmax ties choose the earliest repeated row.",
        "sequence": SEQUENCE, "max_new_tokens": MAX_NEW,
        "flash_bytes": len(fixture["image"]), "extent": extent,
        "images": [{"bypass": index, "sha256": hashlib.sha256(item["image"]).hexdigest(),
                    "hex_sha256": hashlib.sha256(
                        (directory / f"shell-flash-{index}.hex").read_bytes()).hexdigest(),
                    "path": str((directory / f"shell-flash-{index}.hex").relative_to(ROOT))}
                   for index, item in enumerate(fixtures)],
        "segments": segments, "cases": cases,
        "observable_limits": "Top exposes DDR and byte pins, not token/logit channels. "
                             "Every prompt/feedback embedding fetch, complete ordered "
                             "physical head row traversal, exact intermediate activation "
                             "write and cache position is compared. Internal logit "
                             "handshakes are not claimed observed; their independent "
                             "public adapter/controller suites remain mandatory.",
    })


SHELL = r"""
module bench;
  reg clk=0,rst_n;
  always #5 clk=~clk;
  reg ddr_cal_done=0,spi_miso=0,uart_rx=1;
  reg s_axis_tvalid=0,s_axis_tlast=0,m_axis_tready=0;
  reg [7:0] s_axis_tdata=0;
  wire uart_tx,s_axis_tready,m_axis_tvalid,m_axis_tlast;
  wire [7:0] m_axis_tdata;
  wire spi_mosi,spi_sck,spi_cs_n;
  wire ddr_req_valid,ddr_req_write,ddr_rsp_ready,boot_done,busy,done,error;
  wire [63:0] ddr_req_addr;
  wire [31:0] ddr_req_wdata;
  wire [3:0] ddr_req_wstrb;
  wire [7:0] error_code;
  reg ddr_req_ready=0,ddr_rsp_valid=0,ddr_rsp_error=0;
  reg [31:0] ddr_rsp_rdata=0;
  reg cfg_valid=0,cfg_write=0,cfg_rsp_ready=0;
  reg [31:0] cfg_addr=0,cfg_wdata=0;
  wire cfg_ready,cfg_rsp_valid,cfg_rsp_error;
  wire [31:0] cfg_rdata;
  anvil_edge_top #(
    .NUM_LAYERS(1),.HIDDEN_SIZE(8),.INTERMEDIATE_SIZE(8),
    .NUM_Q_HEADS(1),.NUM_KV_HEADS(1),.HEAD_DIM(8),.GROUP_SIZE(8),
    .VOCAB_SIZE(@CAPACITY@),.MAX_SEQ_LEN(64),.SPI_CLOCK_HALF_PERIOD(1),
    .MAX_PROMPT_BYTES(4096),.MAX_PROMPT_TOKENS(4096),
    .RX_FIFO_DEPTH(16),.TX_FIFO_DEPTH(3),.DDR_BYTES(@EXTENT@)
  ) dut(.*);
  localparam EXTENT=@EXTENT@,BYPASS=@BYPASS@,FRAMES=@FRAMES@;
  reg [7:0] flash[0:EXTENT-1];
  reg [31:0] ddr[0:EXTENT/4-1];
  reg [63:0] segment_base[0:19];
  integer segment_length[0:19],segment_flash[0:19];
  @SPI@
  reg [31:0] rng=@SEED@;
  reg pending=0,held=0,running=0,out_held=0,loading=1;
  reg [100:0] held_payload;
  reg [8:0] held_output;
  reg [63:0] pending_address=0;
  integer delay_count=0,writes=0,reads=0,acknowledgements=0;
  integer boot_segment=0,boot_offset=0,request_stalls=0,output_stalls=0;
  integer comparisons=0,frame=0,outputs=0,completions=0,reloads=0;
  integer frame_done=0,input_count=0,embedding_reads=0,activation_writes=0;
  integer total_activation_writes=0,prompt_count=0,matched_write=-1,active_operation=-1;
  integer operation_index=0,embedding_index=0,inference_reads=0;
  reg [31:0] input_bytes[0:4095],expected_tokens[0:63],output_bytes[0:4095];
  reg [63:0] operation_cycles[0:63];
  reg [63:0] expected_write_address[0:65535];
  reg [31:0] expected_write_data[0:65535];
  reg [31:0] expected_write_operation[0:65535];
  integer expected_write_next[0:65535];
  integer write_head[bit [95:0]];
  reg write_seen[0:65535];
  integer scoreboard_fault=0;
  reg fault_injected=0;
  integer input_length=0,output_length=0,operation_count=0,write_count=0;
  reg [63:0] cycles=0;
  reg [63:0] next_progress=64'd16777216;
  integer observed_input=0,observed_output=0;
  reg final_head_pending=0,input_finished=0;
  function automatic bit within_segment(input [63:0] address);
    begin
      within_segment=0;
      for (integer k=0;k<20;k=k+1)
        if (address>=segment_base[k] &&
            address<segment_base[k]+segment_length[k] && address[1:0]==0)
          within_segment=1;
    end
  endfunction
  task automatic reset_check;
    begin
      if ({spi_mosi,spi_sck,ddr_req_valid,ddr_req_write,ddr_req_addr,
           ddr_req_wdata,ddr_req_wstrb,ddr_rsp_ready,boot_done,busy,error,error_code,
           done,s_axis_tready,m_axis_tvalid,m_axis_tdata,m_axis_tlast,
           cfg_ready,cfg_rsp_valid,cfg_rsp_error,cfg_rdata}!==0 ||
          spi_cs_n!==1 || uart_tx!==1) $fatal(1,"QWEN_SHELL_RESET");
    end
  endtask
  task automatic check_write(input [63:0] address,input [31:0] value,
                            input [3:0] strobe,input integer operation);
    reg [95:0] key;
    begin
      key={32'(operation),address};
      matched_write=write_head.exists(key) ? write_head[key] : -1;
      if (matched_write<0 || activation_writes>=write_count || strobe!==4'hf)
        $fatal(1,"QWEN_SHELL_UNEXPECTED_WRITE frame=%0d op=%0d address=%h",
               frame,operation,address);
      if (write_seen[matched_write] || address!==expected_write_address[matched_write] ||
          operation!=expected_write_operation[matched_write])
        $fatal(1,"QWEN_SHELL_WRITE_INDEX");
      if (value!==expected_write_data[matched_write])
        $fatal(1,"QWEN_SHELL_NUMERICAL_WRITE frame=%0d item=%0d address=%h got=%h expected=%h",
               frame,matched_write,address,value,expected_write_data[matched_write]);
      write_seen[matched_write]=1;
      write_head[key]=expected_write_next[matched_write];
      activation_writes=activation_writes+1;
      total_activation_writes=total_activation_writes+1;
    end
  endtask
  always @(posedge clk or negedge clk) if (!rst_n) reset_check();
  always @(negedge clk) if (rst_n) begin
    rng=rng^(rng<<13); rng=rng^(rng>>17); rng=rng^(rng<<5);
    ddr_req_ready=rng[0] || rng[1];
    m_axis_tready=rng[2] && rng[3];
    if (pending && !ddr_rsp_valid) begin
      if (delay_count==0) begin
        ddr_rsp_valid<=1;
        ddr_rsp_rdata=ddr[pending_address>>2];
      end else delay_count=delay_count-1;
    end
  end
  always @(posedge clk) begin
    cycles=cycles+1;
    if (cycles>=64'd@CYCLES@)
      $fatal(1,"QWEN_SHELL_CYCLE_BOUND frame=%0d embedding=%0d writes=%0d",
             frame,embedding_reads,activation_writes);
    if (rst_n) begin
      if ((^{spi_mosi,spi_sck,spi_cs_n,ddr_req_valid,ddr_req_write,
             ddr_req_addr,ddr_req_wdata,ddr_req_wstrb,ddr_rsp_ready,
             boot_done,busy,done,error,error_code,uart_tx,s_axis_tready,
             m_axis_tvalid,m_axis_tlast,m_axis_tdata,cfg_ready,cfg_rsp_valid,
             cfg_rsp_error,cfg_rdata})===1'bx) $fatal(1,"QWEN_SHELL_XZ");
      if (error) $fatal(1,"QWEN_SHELL_ERROR frame=%0d code=%h cycles=%0d embedding=%0d activation=%0d outputs=%0d",
                           frame,error_code,cycles,embedding_reads,activation_writes,outputs);
      if (held && (!ddr_req_valid ||
          {ddr_req_write,ddr_req_addr,ddr_req_wdata,ddr_req_wstrb}!==held_payload))
        $fatal(1,"QWEN_SHELL_REQUEST_STABILITY");
      held=ddr_req_valid && !ddr_req_ready;
      held_payload={ddr_req_write,ddr_req_addr,ddr_req_wdata,ddr_req_wstrb};
      if (held) request_stalls=request_stalls+1;
      if (ddr_rsp_valid && ddr_rsp_ready) begin
        if (!pending) $fatal(1,"QWEN_SHELL_ORPHAN_RESPONSE");
        if (final_head_pending) begin
          $display("QWEN_SHELL_PHASE phase=head_ack frame=%0d operation=%0d cycles=%0d",
                   frame,operation_index,cycles);
          $fflush();
          final_head_pending=0;
        end
        pending=0; ddr_rsp_valid<=0; acknowledgements=acknowledgements+1;
      end
      if (ddr_req_valid && ddr_req_ready) begin
        if (pending || !ddr_cal_done || ddr_req_addr>=EXTENT ||
            ddr_req_addr[1:0]!==0 || !within_segment(ddr_req_addr))
          $fatal(1,"QWEN_SHELL_DDR_PROTOCOL address=%h",ddr_req_addr);
        if (ddr_req_write) begin
          if (!running) begin
            if (!loading || boot_segment>=20 ||
                ddr_req_addr!==segment_base[boot_segment]+boot_offset ||
                ddr_req_wstrb!==((segment_length[boot_segment]-boot_offset>=4) ?
                                 4'hf : (4'h1<<(segment_length[boot_segment]-boot_offset))-1))
              $fatal(1,"QWEN_SHELL_BOOT_WRITE_ORDER segment=%0d offset=%0d",
                     boot_segment,boot_offset);
            for (integer lane=0;lane<4;lane=lane+1) if (ddr_req_wstrb[lane]) begin
              if (ddr_req_wdata[lane*8+:8]!==
                  flash[segment_flash[boot_segment]+boot_offset+lane])
                $fatal(1,"QWEN_SHELL_BOOT_SOURCE_BYTE");
              ddr[ddr_req_addr>>2][lane*8+:8]=ddr_req_wdata[lane*8+:8];
            end
            boot_offset=boot_offset+4; writes=writes+1;
            if (boot_offset>=segment_length[boot_segment]) begin
              $display("QWEN_SHELL_BOOT_SEGMENT segment=%0d cycles=%0d",
                       boot_segment,cycles);
              $fflush();
              boot_segment=boot_segment+1; boot_offset=0;
            end
          end else begin
            active_operation=(embedding_reads-1)/@EMBEDDING_READS_PER_OPERATION@;
            if (scoreboard_fault==3 && !fault_injected && activation_writes==write_count-1) begin
              fault_injected=1;
              $display("SCOREBOARD_INJECT missing address=%h",ddr_req_addr);
            end else begin
              if (scoreboard_fault==1 && !fault_injected) begin
                fault_injected=1;
                $display("SCOREBOARD_INJECT wrong-value address=%h",ddr_req_addr);
                check_write(ddr_req_addr,ddr_req_wdata^32'd1,ddr_req_wstrb,active_operation);
              end else check_write(ddr_req_addr,ddr_req_wdata,ddr_req_wstrb,active_operation);
              if (scoreboard_fault==2 && !fault_injected &&
                  expected_write_next[matched_write]<0) begin
                fault_injected=1;
                $display("SCOREBOARD_INJECT duplicate address=%h",ddr_req_addr);
                check_write(ddr_req_addr,ddr_req_wdata,ddr_req_wstrb,active_operation);
              end
            end
            ddr[ddr_req_addr>>2]=ddr_req_wdata;
          end
        end else begin
          if (ddr_req_wstrb!==0 || boot_segment!=20)
            $fatal(1,"QWEN_SHELL_READ_BEFORE_BOOT_WRITES");
          loading=0; reads=reads+1;
          if (running) begin
            inference_reads=inference_reads+1;
            if (ddr_req_addr>=segment_base[2] &&
                ddr_req_addr<segment_base[2]+64'd@EMBEDDING_BYTES@) begin
              if (input_count!=input_length) $fatal(1,"QWEN_SHELL_PARTIAL_PREFILL");
              operation_index=embedding_reads/@EMBEDDING_READS_PER_OPERATION@;
              embedding_index=embedding_reads%@EMBEDDING_READS_PER_OPERATION@;
              if (operation_index>=operation_count)
                $fatal(1,"QWEN_SHELL_EXTRA_CORE_OPERATION");
              if (embedding_index<8) begin
                if (ddr_req_addr!==segment_base[2]+
                    64'd32*expected_tokens[operation_index]+4*embedding_index)
                  $fatal(1,"QWEN_SHELL_PREFILL_FEEDBACK frame=%0d op=%0d token=%0d address=%h",
                         frame,operation_index,expected_tokens[operation_index],ddr_req_addr);
                if (embedding_index==0) begin
                  operation_cycles[operation_index]=cycles;
                  $display("QWEN_SHELL_PHASE phase=core_begin frame=%0d operation=%0d cycles=%0d",
                           frame,operation_index,cycles);
                  $fflush();
                end
              end else if (ddr_req_addr!==segment_base[2]+4*(embedding_index-8))
                $fatal(1,"QWEN_SHELL_HEAD_FRAME_ORDER");
              if (embedding_index==8) begin
                $display("QWEN_SHELL_PHASE phase=head_begin frame=%0d operation=%0d cycles=%0d",
                         frame,operation_index,cycles);
                $fflush();
              end
              if (embedding_index==@EMBEDDING_READS_PER_OPERATION@-1)
                final_head_pending=1;
              embedding_reads=embedding_reads+1;
            end
          end
        end
        pending_address=ddr_req_addr; pending=1; delay_count=rng[5:4];
        comparisons=comparisons+1;
      end
      if (running) begin
        if (input_finished && observed_input==0) begin
          observed_input=1;
          $display("QWEN_SHELL_PHASE phase=input_sent frame=%0d cycles=%0d",
                   frame,cycles);
          $fflush();
        end
        if (outputs!=observed_output) begin
          if (observed_output==0 || outputs==output_length) begin
            $display("QWEN_SHELL_PHASE phase=output_progress frame=%0d bytes=%0d cycles=%0d",
                     frame,outputs,cycles);
            $fflush();
          end
          observed_output=outputs;
        end
        if (cfg_valid || cfg_write || !boot_done || !spi_cs_n)
          $fatal(1,"QWEN_SHELL_HOST_INTERVENTION_OR_BOOT_REENTRY");
        if (out_held && (!m_axis_tvalid || {m_axis_tlast,m_axis_tdata}!==held_output))
          $fatal(1,"QWEN_SHELL_OUTPUT_STABILITY");
        out_held=m_axis_tvalid && !m_axis_tready;
        held_output={m_axis_tlast,m_axis_tdata};
        if (out_held) output_stalls=output_stalls+1;
        if (!BYPASS && m_axis_tvalid) $fatal(1,"QWEN_SHELL_UNSELECTED_OUTPUT");
        if (BYPASS && m_axis_tvalid && m_axis_tready) begin
          if (embedding_reads<prompt_count*@EMBEDDING_READS_PER_OPERATION@)
            $fatal(1,"QWEN_SHELL_INTERMEDIATE_PREFILL_OUTPUT");
          if (outputs>=output_length || m_axis_tdata!==output_bytes[outputs][7:0] ||
              m_axis_tlast!==(outputs==output_length-1))
            $fatal(1,"QWEN_SHELL_OUTPUT_BYTE frame=%0d item=%0d got=%h expected=%h",
                   frame,outputs,m_axis_tdata,output_bytes[outputs]);
          outputs=outputs+1; comparisons=comparisons+1;
        end
        if (s_axis_tvalid && s_axis_tready) begin
          if (!BYPASS || input_count>=input_length ||
              s_axis_tdata!==input_bytes[input_count][7:0] ||
              s_axis_tlast!==(input_count==input_length-1))
            $fatal(1,"QWEN_SHELL_INPUT_BINDING");
          input_count=input_count+1;
        end
        if (done) begin
          if (frame_done!=0 || outputs!=output_length || pending || ddr_req_valid ||
              m_axis_tvalid || uart_tx!==1 || activation_writes!=write_count ||
              embedding_reads!=operation_count*@EMBEDDING_READS_PER_OPERATION@ ||
              acknowledgements!=writes+reads+total_activation_writes)
            $fatal(1,"QWEN_SHELL_DRAIN frame=%0d output=%0d writes=%0d embedding=%0d",
                   frame,outputs,activation_writes,embedding_reads);
          for (integer item=0;item<write_count;item=item+1)
            if (!write_seen[item]) $fatal(1,"QWEN_SHELL_MISSING_WRITE item=%0d",item);
          frame_done=frame_done+1; completions=completions+1; comparisons=comparisons+1;
          $display("QWEN_SHELL_COMPLETION frame=%0d cycles=%0d",frame,cycles);
          $fflush();
        end
      end
      if (cycles>=next_progress) begin
        $display("QWEN_SHELL_PROGRESS frame=%0d running=%0d input=%0d embedding=%0d activation=%0d output=%0d reads=%0d acknowledgements=%0d cycles=%0d",
                 frame,running,input_count,embedding_reads,activation_writes,outputs,
                 reads,acknowledgements,cycles);
        $fflush();
        next_progress=next_progress+64'd16777216;
      end
    end
  end
  task automatic tick; begin @(posedge clk); #1; end endtask
  task automatic send_axis(input [7:0] value,input bit last);
    begin
      @(negedge clk); #1; s_axis_tvalid=1; s_axis_tdata=value; s_axis_tlast=last;
      do begin @(posedge clk); end while (!s_axis_tready);
      #1; @(negedge clk); #1; s_axis_tvalid=0;
    end
  endtask
  task automatic serial_bit(input bit value);
    begin uart_rx=value; repeat (5) begin @(negedge clk); #1; end end
  endtask
  task automatic send_serial(input [7:0] value);
    begin
      serial_bit(0);
      for (integer bit_index=0;bit_index<8;bit_index=bit_index+1)
        serial_bit(value[bit_index]);
      serial_bit(1);
    end
  endtask
  task automatic decode_serial;
    reg [9:0] expected_frame;
    begin
      while (outputs<output_length) begin
        expected_frame={1'b1,output_bytes[outputs][7:0],1'b0};
        wait (uart_tx===0); #1;
        if (embedding_reads<prompt_count*@EMBEDDING_READS_PER_OPERATION@)
          $fatal(1,"QWEN_SHELL_UART_INTERMEDIATE_PREFILL_OUTPUT");
        for (integer bit_index=0;bit_index<10;bit_index=bit_index+1)
          repeat (5) begin
            if (uart_tx!==expected_frame[bit_index] || done!==0)
              $fatal(1,"QWEN_SHELL_UART_BIT frame=%0d byte=%0d bit=%0d",
                     frame,outputs,bit_index);
            tick();
          end
        outputs=outputs+1; comparisons=comparisons+1;
      end
    end
  endtask
  task automatic wait_boot;
    begin
      wait (boot_done);
      @(negedge clk); #1;
      wait (!busy);
      if (boot_segment!=20 || pending || ddr_rsp_valid || loading ||
          writes!=@BOOT_WRITES@ || reads==0 || spi_reads<22 ||
          acknowledgements!=writes+reads)
        $fatal(1,"QWEN_SHELL_BOOT_CONSERVATION");
      $display("QWEN_SHELL_BOOT writes=%0d reads=%0d acknowledgements=%0d cycles=%0d",
               writes,reads,acknowledgements,cycles);
      $fflush();
      comparisons=comparisons+1;
    end
  endtask
  task automatic reload_image;
    begin
      if (running || busy || pending || ddr_rsp_valid || ddr_req_valid || spi_cs_n!==1)
        $fatal(1,"QWEN_SHELL_RELOAD_NOT_IDLE");
      @(negedge clk); #1;
      writes=0; reads=0; acknowledgements=0; boot_segment=0; boot_offset=0;
      total_activation_writes=0;
      loading=1; spi_reads=0;
      cfg_valid=1; cfg_write=1; cfg_addr=32'h1c; cfg_wdata=1;
      do begin @(posedge clk); end while (!cfg_ready);
      #1; @(negedge clk); #1; cfg_valid=0; cfg_write=0;
      while (!cfg_rsp_valid) tick();
      repeat (3) begin
        if (!cfg_rsp_valid || cfg_rsp_error || cfg_rdata!==0)
          $fatal(1,"QWEN_SHELL_RELOAD_RESPONSE");
        tick();
      end
      @(negedge clk); #1; cfg_rsp_ready=1; tick();
      @(negedge clk); #1; cfg_rsp_ready=0;
      if (boot_done) $fatal(1,"QWEN_SHELL_RELOAD_NOT_WITHDRAWN");
      wait_boot(); reloads=reloads+1;
    end
  endtask
  initial begin
    rst_n=0; #0; reset_check();
    if (!$value$plusargs("scoreboard_fault=%d",scoreboard_fault)) scoreboard_fault=0;
    if (scoreboard_fault<0 || scoreboard_fault>3) $fatal(1,"INVALID_SCOREBOARD_FAULT");
    $readmemh("@FLASH@",flash,0,@FLASH_BYTES@-1);
    @SEGMENTS@
    repeat (2) tick(); @(negedge clk); #1; rst_n=1;
    repeat (20) begin
      tick();
      if (spi_cs_n!==1 || ddr_req_valid!==0 || boot_done!==0)
        $fatal(1,"QWEN_SHELL_DELAYED_CALIBRATION");
    end
    @(negedge clk); #1; ddr_cal_done=1;
    $display("QWEN_SHELL_START transport=%0d cycles=%0d",BYPASS,cycles);
    $fflush();
    wait_boot();
    for (frame=0;frame<FRAMES;frame=frame+1) begin
      @LOAD_CASE@
      outputs=0; frame_done=0; input_count=0; embedding_reads=0;
      activation_writes=0; inference_reads=0; out_held=0;
      observed_input=0; observed_output=0; final_head_pending=0; input_finished=0;
      write_head.delete();
      for (integer item=write_count-1;item>=0;item=item-1) begin
        write_seen[item]=0;
        expected_write_next[item]=
          write_head.exists({expected_write_operation[item],expected_write_address[item]}) ?
          write_head[{expected_write_operation[item],expected_write_address[item]}] : -1;
        write_head[{expected_write_operation[item],expected_write_address[item]}]=item;
      end
      running=1;
      $display("QWEN_SHELL_PHASE phase=input_begin frame=%0d cycles=%0d",
               frame,cycles);
      $fflush();
      if (BYPASS) begin
        for (integer item=0;item<input_length;item=item+1)
          send_axis(input_bytes[item][7:0],item==input_length-1);
        input_finished=1;
      end else begin
        fork
          begin
            @(negedge clk); #1;
            for (integer item=0;item<input_length;item=item+1)
              send_serial(input_bytes[item][7:0]);
            input_count=input_length;
            send_serial(10);
            input_finished=1;
          end
          decode_serial();
        join
      end
      wait (frame_done!=0);
      repeat (20) tick();
      if (frame_done!=1 || busy || pending || ddr_req_valid || m_axis_tvalid ||
          outputs!=output_length || input_count!=input_length || inference_reads==0)
        $fatal(1,"QWEN_SHELL_FINAL_COUNTS");
      for (integer operation=0;operation<operation_count;operation=operation+1)
        $display("QWEN_SHELL_OPERATION frame=%0d position=%0d token=%0d cycles=%0d",
                 frame,operation,expected_tokens[operation],operation_cycles[operation]);
      $display("QWEN_SHELL_FRAME frame=%0d transport=%0d prompt_bytes=%0d operations=%0d output_bytes=%0d embedding_reads=%0d activation_writes=%0d cycles=%0d",
               frame,BYPASS,input_count,operation_count,outputs,embedding_reads,
               activation_writes,cycles);
      $fflush();
      running=0;
      if (frame==0 && FRAMES>1) reload_image();
    end
    if (completions!=FRAMES || request_stalls==0 ||
        (BYPASS && output_stalls==0) || reloads!=(FRAMES>1 ? 1 : 0))
      $fatal(1,"QWEN_SHELL_COVERAGE");
    $display("QWEN_SHELL_COUNTS frames=%0d reloads=%0d request_stalls=%0d output_stalls=%0d",
             completions,reloads,request_stalls,output_stalls);
    $display("COMPARED %0d",comparisons); $fflush(); $finish;
  end
endmodule
"""

PUBLIC_TRACE = r"""
  integer verification_trace_fd;
  longint unsigned verification_trace_cycle=0,verification_trace_count=0;
  reg [7:0] verification_previous_pins=0;
  reg [11:0] verification_previous_status=0;
  wire [7:0] verification_pins=
    {2'b0,spi_miso,spi_mosi,spi_sck,spi_cs_n,uart_rx,uart_tx};
  wire [11:0] verification_status={boot_done,busy,done,error,error_code};
  initial begin
    string trace_path;
    if (!$value$plusargs("verification_trace_file=%s",trace_path))
      $fatal(1,"QWEN_SHELL_MISSING_TRACE_PATH");
    verification_trace_fd=$fopen(trace_path,"wb");
    if (!verification_trace_fd) $fatal(1,"QWEN_SHELL_TRACE_OPEN");
  end
  task automatic verification_trace_event(input [31:0] kind,input [191:0] payload);
    begin
      $fwrite(verification_trace_fd,"%u",{verification_trace_cycle,kind,payload});
      verification_trace_count=verification_trace_count+1;
    end
  endtask
  always @(posedge clk) begin
    verification_trace_cycle=verification_trace_cycle+1;
    if (verification_pins!==verification_previous_pins)
      verification_trace_event(0,{184'd0,verification_pins});
    verification_previous_pins=verification_pins;
    if (verification_status!==verification_previous_status)
      verification_trace_event(7,{180'd0,verification_status});
    verification_previous_status=verification_status;
    if (rst_n) begin
      if (ddr_req_valid && ddr_req_ready)
        verification_trace_event(1,{91'd0,ddr_req_write,ddr_req_addr,
                                     ddr_req_wdata,ddr_req_wstrb});
      if (ddr_rsp_valid && ddr_rsp_ready)
        verification_trace_event(2,{159'd0,ddr_rsp_error,ddr_rsp_rdata});
      if (s_axis_tvalid && s_axis_tready)
        verification_trace_event(3,{183'd0,s_axis_tlast,s_axis_tdata});
      if (m_axis_tvalid && m_axis_tready)
        verification_trace_event(4,{183'd0,m_axis_tlast,m_axis_tdata});
      if (cfg_valid && cfg_ready)
        verification_trace_event(5,{127'd0,cfg_write,cfg_addr,cfg_wdata});
      if (cfg_rsp_valid && cfg_rsp_ready)
        verification_trace_event(6,{159'd0,cfg_rsp_error,cfg_rdata});
    end
  end
"""


def shell_case(evidence, info, seed, bypass, general_only, *, family="qwen",
               bind_transport=True):
    require(bypass in (0, 1), "Shell transport must be UART or bypass")
    cases = info["cases"][:1] if general_only else info["cases"]
    loads = []
    for frame, case in enumerate(cases):
        fields = case["files"]
        lines = [f"      {frame}: begin",
                 f"        input_length={fields['input']['count']};",
                 f"        output_length={fields['output']['count']};",
                 f"        operation_count={fields['tokens']['count']};",
                 f"        prompt_count={len(case['expected_prompt_ids'])};",
                 f"        write_count={fields['write-data']['count']};"]
        for name, array in (("input", "input_bytes"), ("tokens", "expected_tokens"),
                            ("output", "output_bytes"), ("write-address", "expected_write_address"),
                            ("write-data", "expected_write_data"),
                            ("write-operation", "expected_write_operation")):
            source = fields[name]
            require(hashlib.sha256((ROOT / source["path"]).read_bytes()).hexdigest()
                    == source["sha256"], "Shell reference vector changed")
            lines.append(f'        $readmemh("{source["path"]}",{array},0,{source["count"]-1});')
        lines.append("      end")
        loads.extend(lines)
    image = info["images"][bypass]
    require(hashlib.sha256((ROOT / image["path"]).read_bytes()).hexdigest()
            == image["hex_sha256"], "Shell SPI image changed")
    spi = BOOT[BOOT.index("  reg [31:0] command_shift=0;"):
               BOOT.index("  reg [31:0] rng=")]
    spi = spi.replace("65536", "EXTENT").replace("@FLASH_EXTENT@", str(info["flash_bytes"]))
    segments = "\n".join(
        f"    segment_base[{index}]=64'd{entry['base']}; "
        f"segment_length[{index}]={entry['bytes']}; "
        f"segment_flash[{index}]={entry['flash_offset']};"
        for index, entry in enumerate(info["segments"])
    )
    cycles = (info["flash_bytes"] * 100 + 5000000000) * (2 if len(cases) > 1 else 1)
    cycles += sum(len(case["core_operation_ids"]) for case in cases) * 1000000000
    values = {
        "EXTENT": info["extent"], "BYPASS": bypass, "FRAMES": len(cases),
        "CAPACITY": info["physical_capacity"],
        "EMBEDDING_BYTES": info["physical_capacity"] * 32,
        "EMBEDDING_READS_PER_OPERATION": info["physical_capacity"] * 8 + 8,
        "SPI": spi, "SEED": seed, "FLASH": image["path"],
        "FLASH_BYTES": info["flash_bytes"], "SEGMENTS": segments,
        "BOOT_WRITES": sum((entry["bytes"] + 3) // 4 for entry in info["segments"]),
        "LOAD_CASE": "case (frame)\n" + "\n".join(loads) +
                     '\n      default: $fatal(1,"QWEN_SHELL_UNKNOWN_FRAME");\n    endcase',
        "CYCLES": cycles,
    }
    bench = SHELL
    for key, value in values.items():
        bench = bench.replace(f"@{key}@", str(value))
    runtime_arguments = ()
    if bind_transport:
        declaration = (f"  localparam EXTENT={info['extent']},BYPASS={bypass},"
                       f"FRAMES={len(cases)};")
        require(bench.count(declaration) == 1, "Missing unique shell transport declaration")
        bench = bench.replace(declaration, f"""  localparam EXTENT={info['extent']},FRAMES={len(cases)};
  integer BYPASS;
  initial begin
    if (!$value$plusargs("verification_bypass=%d",BYPASS) ||
        (BYPASS!=0 && BYPASS!=1)) $fatal(1,"QWEN_SHELL_INVALID_TRANSPORT");
  end""", 1)
        runtime_arguments = (f"+verification_bypass={bypass}",)
    trace_path = None
    if getattr(evidence, "capture_public_trace", False) is True:
        # This is compact paired-driver telemetry only, never production L1 I/O.
        trace_path = evidence.path / f"{evidence.name_prefix}{family}-b{bypass}-s{seed}.bin"
        require(not trace_path.exists(), "Public trace output already exists")
        bench = bench.replace("module bench;", "module bench;\n" + PUBLIC_TRACE, 1)
        anchor = '    $display("COMPARED %0d",comparisons);'
        require(bench.count(anchor) == 1, "Missing unique final shell comparison")
        bench = bench.replace(anchor, """    $fclose(verification_trace_fd);
    $display("QWEN_SHELL_TRACE records=%0d",verification_trace_count);
""" + anchor, 1)
        runtime_arguments += (f"+verification_trace_file={evidence.relative(trace_path)}",)
    require(re.fullmatch(r"[a-z][a-z0-9-]*", family), "Invalid shell diagnostic family")
    bench = bench.replace("QWEN_SHELL_", family.upper().replace("-", "_") + "_SHELL_")
    require(not re.search(r"@[A-Z_]+@", bench), "Unexpanded shell bench placeholder")
    sources = ["rtl/anvil_edge_numeric_pkg.sv"] + [
        str(path.relative_to(ROOT)) for path in sorted((ROOT / "rtl").glob("*.sv"))
        if path.name != "anvil_edge_numeric_pkg.sv"
    ]
    result = evidence.simulate(f"{family}-shell-b{bypass}-s{seed}", bench, sources,
                               None, simulator="verilator", optimize=True,
                               explicit_clock=True, runtime_arguments=runtime_arguments,
                               compiled_workload=True)
    if trace_path is not None:
        size = trace_path.stat().st_size
        prefix = family.upper().replace("-", "_") + "_SHELL"
        text = (ROOT / result["simulation_receipt"]["stdout"]).read_text()
        counts = re.findall(r"^" + prefix + r"_TRACE records=(\d+)$", text, re.MULTILINE)
        require(len(counts) == 1 and int(counts[0]) > 0 and
                size == int(counts[0]) * 36,
                "Public trace must contain every fixed-width emitted record")
        with trace_path.open("rb") as stream:
            checksum = hashlib.file_digest(stream, "sha256").hexdigest()
        result["public_trace"] = {
            "path": evidence.relative(trace_path), "bytes": size, "records": int(counts[0]),
            "sha256": checksum,
            "record_bytes": 36,
            "scope": "Pre-edge accepted DDR/config/AXI transactions, status and "
                     "SPI/UART pin transitions, with independent rising-edge counter",
        }
    return result


def shell_workers(evidence):
    """Keep shell concurrency within the measured three-child resource envelope."""
    return min(3, evidence._limits["workers"])


def run_qwen_shell(evidence, general_only=False, *, bypass_only=False):
    from table_artifacts import complete_tables

    require(not bypass_only or general_only, "Bypass diagnostic requires one general prompt")
    evidence.tools(("python3", "verilator", "g++", "make"))
    producer, _ = complete_tables(evidence, "qwen")
    evidence.child(["./.venv/bin/python", "tests/qwen_shell.py",
                    evidence.relative(evidence.path), "--table-source",
                    evidence.relative(producer)], "qwen-shell-reference")
    info = json.loads((evidence.path / "shell-reference.json").read_bytes())
    # Initial bounded integration uses the general-knowledge prompt on both pins.
    # The complete L1 branch retains all prompts, reload and all admitted seeds.
    cases = [
        (f"qwen-shell-b{bypass}-s{seed}",
         lambda scope, seed=seed, bypass=bypass:
         shell_case(scope, info, seed, bypass, general_only))
        for seed in ((17,) if general_only else (1, 17, 89))
        for bypass in ((1,) if bypass_only else (0, 1))
    ]
    if bypass_only:
        require([name for name, _ in cases] == ["qwen-shell-b1-s17"],
                "Diagnostic batch must contain only bypass seed17")
        evidence.record["diagnostic_selection"] = {
            "prompt": "What is the capital of France?",
            "seed": 17, "bypass": 1, "planned_cases": [name for name, _ in cases],
            "scope": info["scope"], "mandatory_l1_matrix_changed": False,
        }
    try:
        evidence.run_cases(cases, workers=shell_workers(evidence))
    finally:
        if bypass_only:
            progress = []
            for child in evidence.record["children"]:
                if child["argv"][0].endswith("/simulation"):
                    lines = (ROOT / child["stdout"]).read_text().splitlines()
                    events = [line for line in lines if line.startswith("QWEN_SHELL_")]
                    progress.append({
                        "receipt": str(Path(child["stdout"]).parent / "receipt.json"),
                        "duration_s": child["duration_s"],
                        "timed_out": child["timed_out"], "exit_code": child["exit_code"],
                        "child_settled": child["child_settled"],
                        "process_group_settled": child["process_group_settled"],
                        "events": events,
                        "last_reported_cycle": max(
                            (int(value) for line in events
                             for value in re.findall(r"\bcycles=(\d+)", line)), default=0),
                        "interpretation": ("Incomplete execution, not a numerical mismatch"
                                           if child["timed_out"] else
                                           "See original assertions and comparison totals"),
                    })
            evidence.record["diagnostic_progress"] = progress


def run_shell_scoreboard(evidence):
    evidence.tools(("python3", "verilator", "g++", "make"))
    evidence.child(["./.venv/bin/python", "tests/qwen_shell.py",
                    evidence.relative(evidence.path), "--compact"],
                   "compact-shell-reference")
    info = json.loads((evidence.path / "shell-reference.json").read_bytes())
    evidence.run_cases([
        (f"compact-shell-b{bypass}-s{seed}",
         lambda scope, seed=seed, bypass=bypass:
         shell_case(scope, info, seed, bypass, False))
        for seed in (1, 17, 89) for bypass in (0, 1)
    ])
    rows = list(evidence.record["coverage"])
    require(len(rows) == 6 and all(row["status"] == "passed" for row in rows),
            "All compact transports/seeds must complete before scoreboard controls")
    # These are monitor diagnostics, not production RTL mutation coverage.
    # Reuse the compiled, unmodified bench and alter only its observed-write stream.
    baseline = next(row for row in rows if row["name"] == "qwen-shell-b1-s17")
    result = baseline["simulation_receipt"]
    controls = []
    for mode, name, assertion in (
        (1, "wrong-value", "QWEN_SHELL_NUMERICAL_WRITE"),
        (2, "duplicate", "QWEN_SHELL_UNEXPECTED_WRITE"),
        (3, "missing", "QWEN_SHELL_DRAIN"),
    ):
        child = evidence.child(
            [*result["argv"], f"+scoreboard_fault={mode}"],
            "scoreboard-control-" + name, allow_failure=True)
        output = (ROOT / child["stdout"]).read_text() + (ROOT / child["stderr"]).read_text()
        require(child["exit_code"] != 0 and not child["timed_out"] and
                child["child_settled"] and child["process_group_settled"] and
                f"SCOREBOARD_INJECT {name}" in output and assertion in output and
                "%Error:" in output,
                f"Indexed scoreboard failed to reject {name} via {assertion}")
        controls.append({"fault": name, "assertion": assertion, "receipt": child})
    evidence.record["indexed_scoreboard_controls"] = controls
    evidence.record["shell_execution_measurement"] = {
        "scope": "Compact diagnostic only; not complete official tables or pretrained inference",
        "transports": [0, 1], "seeds": [1, 17, 89],
        "simulation_seconds": [row["simulation_receipt"]["duration_s"] for row in rows],
        "comparisons_per_case": [row["actual_comparisons"] for row in rows],
        "optimizations": ["per-operation/address indexed ordered queues",
                          "event waits instead of idle coroutine polling",
                          "C++ OPT_FAST=-O3 OPT_SLOW=-O3"],
    }


if __name__ == "__main__":
    from_producer = len(sys.argv) == 4 and sys.argv[2] == "--table-source"
    require(len(sys.argv) in (2, 3, 4) and (from_producer or
            ((len(sys.argv) == 2 or sys.argv[2] == "--compact") and
             (len(sys.argv) != 4 or sys.argv[3].isdigit()))),
            "Usage: ./.venv/bin/python tests/qwen_shell.py EVIDENCE_DIRECTORY "
            "[--compact [PHYSICAL_CAPACITY] | --table-source PRODUCER_DIRECTORY]")
    destination = Path(sys.argv[1])
    require(not destination.is_absolute() and ".." not in destination.parts
            and destination.is_dir() and destination.parts[:2] in (
                ("evidence", "preparation"), ("evidence", "verification")),
            "Shell inputs require a fresh project evidence directory")
    producer = Path(sys.argv[3]) if from_producer else None
    if producer is not None:
        require(not producer.is_absolute() and ".." not in producer.parts and
                producer.is_dir() and producer.parts[:2] in (
                    ("evidence", "preparation"), ("evidence", "verification")),
                "Complete tables require an explicit project evidence producer")
    build_inputs(destination, compact=not from_producer and len(sys.argv) >= 3,
                 physical_capacity=int(sys.argv[3]) if len(sys.argv) == 4
                 and not from_producer else None, table_source=producer)
