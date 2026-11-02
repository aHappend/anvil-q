"""Full-width streamed GEMV, tile-order oracle and accounted long-stream density."""

from fractions import Fraction
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fp2_probe import Probe, ROOT, SuiteDeadline, simulate
from fp2_reference import add, rounded, tensor


LENGTHS = (1, 127, 128, 129, 1536, 8960)
TB = r"""
module tb;
  reg clk=0; always #5 clk=~clk;
  reg rst_n,flush=0,cmd_valid=0,cmd_mx=0,row_ready=0;
  reg [31:0] cmd_inputs=0,cmd_outputs=3;
  wire cmd_ready,busy,row_valid,row_last,row_error,underflow,bubble;
  wire [31:0] row_data,row_index;
  wire act_read_valid;
  wire [31:0] act_read_column;
  reg act_data_valid=0;
  reg [2047:0] act_data=0;
  wire req_valid,rsp_ready;
  reg req_ready=0,rsp_valid=0,rsp_error=0;
  wire [3:0] req_kind;
  wire [31:0] req_layer,req_row,req_col,req_tag;
  wire [2:0] req_proj;
  wire [1:0] req_format;
  reg [511:0] rsp_data=0;
  reg [31:0] rsp_tag=0;
  wire tensor_flush,w_valid,w_ready,w_format,w_first,w_last,w_error;
  wire [511:0] w_data;
  wire [15:0] w_scale;
  wire [31:0] w_tag,in_tag,out_tag;
  wire in_valid,in_ready,in_first,in_last,out_valid,out_ready,out_first,out_last,out_error;
  wire [2047:0] in_a;
  wire [127:0] in_mask;
  wire [31:0] out_data;
  anvil_q2_fp2_gemv_stream stream(
    .clk(clk),.rst_n(rst_n),.flush(flush),.cmd_valid(cmd_valid),.cmd_ready(cmd_ready),
    .cmd_layer(32'd0),.cmd_inputs(cmd_inputs),.cmd_outputs(cmd_outputs),
    .cmd_projection(3'd0),.cmd_embedding(1'b0),.cmd_mx(cmd_mx),.busy(busy),
    .row_valid(row_valid),.row_ready(row_ready),.row_data(row_data),.row_index(row_index),
    .row_last(row_last),.row_error(row_error),.event_weight_underflow(underflow),
    .event_tensor_bubble(bubble),.act_read_valid(act_read_valid),
    .act_read_column(act_read_column),.act_data_valid(act_data_valid),.act_data(act_data),
    .req_valid(req_valid),.req_ready(req_ready),.req_kind(req_kind),.req_layer(req_layer),
    .req_row(req_row),.req_col(req_col),.req_tag(req_tag),.req_proj(req_proj),
    .req_format(req_format),.rsp_valid(rsp_valid),.rsp_ready(rsp_ready),
    .rsp_data(rsp_data),.rsp_tag(rsp_tag),.rsp_error(rsp_error),
    .tensor_flush(tensor_flush),.w_valid(w_valid),.w_ready(w_ready),.w_data(w_data),
    .w_scale(w_scale),.w_format(w_format),.w_first(w_first),.w_last(w_last),
    .w_error(w_error),.w_tag(w_tag),.in_valid(in_valid),.in_ready(in_ready),
    .in_a(in_a),.in_mask(in_mask),.in_first(in_first),.in_last(in_last),.in_tag(in_tag),
    .out_valid(out_valid),.out_ready(out_ready),.out_data(out_data),.out_tag(out_tag),
    .out_first(out_first),.out_last(out_last),.out_error(out_error));
  anvil_q2_fp2_bfp_tensor_array tensor_array(
    .clk(clk),.rst_n(rst_n),.flush(tensor_flush),.w_valid(w_valid),.w_ready(w_ready),
    .w_data(w_data),.w_scale(w_scale),.w_format(w_format),.w_first(w_first),
    .w_last(w_last),.w_tag(w_tag),.w_error(w_error),.in_valid(in_valid),.in_ready(in_ready),
    .in_a(in_a),.in_mask(in_mask),.in_first(in_first),.in_last(in_last),.in_tag(in_tag),
    .out_valid(out_valid),.out_ready(out_ready),.out_data(out_data),.out_first(out_first),
    .out_last(out_last),.out_tag(out_tag),.out_error(out_error));
  reg [15:0] activations[0:8959],scan_half;
  reg pending[0:15];
  reg [31:0] tags[0:15];
  reg [511:0] responses[0:15];
  integer due[0:15],issued[0:15];
  integer fd,n,i,lane,cycle=0,shape,mode,rows,slot,selected,active_response=-1;
  integer outstanding,payload_reads,scale_reads,response_count,tiles,lanes_used,overlap;
  integer weights_complete,weights_consumed,maximum_owned,weight_beats;
  integer underflow_cycles,bubble_cycles;
  reg [31:0] random_state=89;
  reg [31:0] lengths[0:5];
  reg held_req=0,held_row=0,accepted_rsp,accepted_activation;
  reg [31:0] accepted_activation_column;
  reg [104:0] saved_req;
  reg [65:0] saved_row;
  wire [104:0] req_payload={req_kind,req_row,req_col,req_tag,req_proj,req_format};
  wire [65:0] row_payload={row_data,row_index,row_last,row_error};
  wire reset_ok=({cmd_ready,busy,row_valid,row_data,row_index,row_last,row_error,
    underflow,bubble,act_read_valid,act_read_column,req_valid,req_kind,req_layer,
    req_row,req_col,req_tag,req_proj,req_format,rsp_ready,tensor_flush,
    w_valid,w_ready,w_data,w_scale,w_format,w_first,w_last,w_error,w_tag,
    in_valid,in_ready,in_a,in_mask,in_first,in_last,in_tag,out_ready,
    out_valid,out_data,out_first,out_last,out_tag,out_error}===0);
  string input_path;
  always @(posedge clk) if(!rst_n && reset_ok !== 1'b1) $fatal(1,"RESET posedge");
  always @(negedge clk) if(!rst_n && reset_ok !== 1'b1) $fatal(1,"RESET negedge");
  initial begin
    rst_n=0; #1; if(reset_ok !== 1'b1)
      $fatal(1,"RESET time0 cmd_ready=%b busy=%b row_valid=%b row_data=%h row_index=%h row_last=%b row_error=%b underflow=%b bubble=%b act_read_valid=%b req_valid=%b req_kind=%h rsp_ready=%b w_valid=%b w_scale=%h w_first=%b w_last=%b in_valid=%b in_first=%b in_last=%b out_valid=%b out_data=%h out_first=%b out_last=%b out_tag=%h out_error=%b",
        cmd_ready,busy,row_valid,row_data,row_index,row_last,row_error,underflow,bubble,
        act_read_valid,req_valid,req_kind,rsp_ready,w_valid,w_scale,w_first,w_last,
        in_valid,in_first,in_last,out_valid,out_data,
        out_first,out_last,out_tag,out_error);
    lengths[0]=1; lengths[1]=127; lengths[2]=128;
    lengths[3]=129; lengths[4]=1536; lengths[5]=8960;
    if(!$value$plusargs("INPUT=%s",input_path)) $fatal(1,"missing INPUT");
    fd=$fopen(input_path,"r"); if(!fd) $fatal(1,"input open");
    for(i=0;i<8960;i=i+1) begin
      n=$fscanf(fd,"%h\n",scan_half); if(n!=1) $fatal(1,"input length");
      activations[i]=scan_half;
    end
    $fclose(fd);
    repeat(2) @(negedge clk); rst_n=1;
    for(mode=0;mode<2;mode=mode+1) for(shape=0;shape<6;shape=shape+1) begin
      for(i=0;i<16;i=i+1) pending[i]=0;
      rows=0; outstanding=0; payload_reads=0; scale_reads=0; response_count=0;
      tiles=0; lanes_used=0; overlap=0; weight_beats=0;
      weights_complete=0; weights_consumed=0; maximum_owned=0;
      underflow_cycles=0; bubble_cycles=0;
      cmd_inputs=lengths[shape]; cmd_mx=mode; cmd_valid=1;
      @(posedge clk); if(cmd_ready !== 1'b1) $fatal(1,"COMMAND_NOT_READY");
      @(negedge clk); cmd_valid=0;
      while(rows<3 && cycle<500000) begin
        random_state=random_state^(random_state<<13);
        random_state=random_state^(random_state>>17);
        random_state=random_state^(random_state<<5);
        req_ready=random_state[2:0]!=0; row_ready=random_state[5:3]!=0;
        if(!rsp_valid) begin
          selected=-1;
          for(i=0;i<16;i=i+1) if(pending[i] && (selected==-1 || issued[i]<issued[selected]))
            selected=i;
          if(selected!=-1 && due[selected]<=cycle) begin
            active_response=selected; rsp_valid=1; rsp_data=responses[selected]; rsp_tag=tags[selected];
          end
        end
        @(posedge clk);
        if((^{cmd_ready,busy,req_valid,rsp_ready,row_valid,w_valid,w_ready,in_valid,
              in_ready,out_valid,out_ready,underflow,bubble}) === 1'bx) $fatal(1,"ACTIVE_CONTROL_X");
        if(held_req && (req_valid !== 1'b1 || req_payload !== saved_req)) $fatal(1,"REQUEST_STABILITY");
        if(held_row && (row_valid !== 1'b1 || row_payload !== saved_row)) $fatal(1,"ROW_STABILITY");
        held_req=req_valid && !req_ready; if(held_req) saved_req=req_payload;
        held_row=row_valid && !row_ready; if(held_row) saved_row=row_payload;
        accepted_activation=act_read_valid;
        if(accepted_activation) accepted_activation_column=act_read_column;
        accepted_rsp=rsp_valid && rsp_ready;
        if(accepted_rsp) begin
          if(active_response<0 || !pending[active_response]) $fatal(1,"RESPONSE_ASSOCIATION");
          pending[active_response]=0; outstanding=outstanding-1; response_count=response_count+1;
        end
        if(req_valid && req_ready) begin
          if((^req_payload) === 1'bx || req_row>=3 || req_layer!=0 ||
             req_proj!=0 || (req_kind!=1 && req_kind!=3)) $fatal(1,"REQUEST_RANGE_OR_X");
          slot=-1;
          for(i=0;i<16;i=i+1) begin
            if(pending[i] && tags[i]==req_tag) $fatal(1,"LIVE_TAG_REUSE");
            if(!pending[i]) slot=i;
          end
          if(slot<0) $fatal(1,"MEMORY_QUEUE_OVERFLOW");
          pending[slot]=1; tags[slot]=req_tag; issued[slot]=cycle;
          due[slot]=cycle+2+random_state[9:6]; responses[slot]=0;
          if(req_kind==3) begin
            if(req_format!=3 || !mode) $fatal(1,"SCALE_FORMAT");
            scale_reads=scale_reads+1;
            responses[slot]={64{8'd127}};
          end else begin
            payload_reads=payload_reads+1;
            if(req_format!=(mode ? 2 : 1) || req_col>=cmd_inputs) $fatal(1,"PAYLOAD_FORMAT_RANGE");
            for(lane=0;lane<(mode ? 64 : 32);lane=lane+1)
              if(req_col+lane<cmd_inputs) begin
                if(mode) responses[slot][8*lane+:8]=req_row[0] ? 8'h30 : 8'h38;
                else responses[slot][16*lane+:16]=req_row[0] ? 16'h3f00 : 16'h3f80;
              end
          end
          outstanding=outstanding+1;
        end
        if(w_valid && w_ready) begin
          weight_beats=weight_beats+1;
          if(weight_beats==(mode ? 2 : 4)) begin
            weights_complete=weights_complete+1; weight_beats=0;
          end
        end
        if(in_valid && in_ready) begin
          weights_consumed=weights_consumed+1; tiles=tiles+1;
          for(lane=0;lane<128;lane=lane+1) if(in_mask[lane]) lanes_used=lanes_used+1;
          if(w_valid && w_ready) overlap=overlap+1;
        end
        if(weights_complete-weights_consumed>maximum_owned)
          maximum_owned=weights_complete-weights_consumed;
        if(underflow) underflow_cycles=underflow_cycles+1;
        if(bubble) bubble_cycles=bubble_cycles+1;
        if(row_valid && row_ready) begin
          if(row_index!=rows || row_last !== (rows==2) || (^row_payload) === 1'bx)
            $fatal(1,"ROW_ORDER_OR_X");
          $display("ROW %0d %0d %0d %08h %0d",mode,cmd_inputs,row_index,row_data,row_error);
          rows=rows+1;
        end
        @(negedge clk);
        act_data_valid=accepted_activation;
        act_data=0;
        if(accepted_activation) for(lane=0;lane<128;lane=lane+1)
          if(accepted_activation_column+lane<cmd_inputs)
            act_data[16*lane+:16]=activations[accepted_activation_column+lane];
        if(accepted_rsp) begin rsp_valid=0; active_response=-1; end
        cycle=cycle+1;
      end
      if(rows!=3 || outstanding!=0 || rsp_valid || tiles==0 ||
         payload_reads+scale_reads!=response_count) $fatal(1,"INCOMPLETE_STREAM");
      $display("STREAM %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d",
        mode,cmd_inputs,payload_reads,scale_reads,response_count,tiles,lanes_used,
        overlap,maximum_owned,underflow_cycles,bubble_cycles);
      @(posedge clk); @(negedge clk); act_data_valid=0;
    end
    $display("SUMMARY 12"); $finish;
  end
endmodule
"""


def activations():
    return [rounded(Fraction(((column * 7) % 31) - 15, 16), fraction_bits=7)
            for column in range(8960)]


def expected(length, row, values):
    accumulator = 0
    for column in range(0, length, 128):
        count = min(128, length - column)
        a = values[column:column + count] + [0] * (128 - count)
        b = [0x3F00 if row & 1 else 0x3F80] * count + [0] * (128 - count)
        partial, failed = tensor(a, b, (1 << count) - 1)
        if failed:
            raise ArithmeticError("finite streamed fixture overflow")
        accumulator = partial if column == 0 else add(accumulator, partial)
    return accumulator


def run(probe):
    values = activations()
    source = probe.directory / "tb.sv"
    source.write_text(TB)
    images = probe.directory / "checkpoint-images"
    images.mkdir()
    inputs = images / "activations.hex"
    inputs.write_text("".join(f"{value:04x}\n" for value in values))
    sources = [ROOT / "rtl" / name for name in (
        "anvil_q2_fp2_arithmetic.sv", "anvil_q2_fp2_mx_decode.sv",
        "anvil_q2_fp2_ping_pong_prefetch.sv", "anvil_q2_fp2_bfp_tensor_array.sv",
        "anvil_q2_fp2_gemv_stream.sv")]
    output = simulate(probe, source, sources, "verilator", [f"+INPUT={inputs.relative_to(ROOT)}"])
    rows, streams, summaries = set(), {}, []
    for line in output.read_text().splitlines():
        words = line.split()
        if words[:1] == ["ROW"]:
            mode, length, row, bits, failed = (int(words[1]), int(words[2]), int(words[3]),
                                              int(words[4], 16), int(words[5]))
            key = (mode, length, row)
            if key in rows or mode not in (0, 1) or length not in LENGTHS or not 0 <= row < 3:
                raise AssertionError("unexpected/duplicate streamed row")
            rows.add(key)
            probe.compare("ascending-tile-fp32-accumulation", expected(length, row, values),
                          bits, {"mode": mode, "length": length, "row": row})
            probe.compare("streamed-row-error", 0, failed, {"mode": mode, "length": length})
        elif words[:1] == ["STREAM"]:
            mode, length, *data = map(int, words[1:])
            if (mode, length) in streams or len(data) != 9:
                raise AssertionError("duplicate/malformed stream accounting")
            streams[mode, length] = dict(zip(
                ("payload_beats", "scale_beats", "responses", "tiles", "active_lanes",
                 "overlap", "maximum_completed_weights_owned", "underflow_cycles", "bubble_cycles"),
                data, strict=True))
        elif words[:1] == ["SUMMARY"]:
            summaries.append(int(words[1]))
    probe.compare("stream-summary", [12], summaries, {})
    probe.compare("stream-row-count", 36, len(rows), {})
    probe.compare("stream-configuration-count", 12, len(streams), {})
    for (mode, length), data in streams.items():
        probe.compare("stream-active-lane-accounting", length * 3, data["active_lanes"],
                      {"mode": mode, "length": length})
        probe.compare("stream-tile-accounting", 3 * ((length + 127) // 128), data["tiles"],
                      {"mode": mode, "length": length})
        probe.compare("stream-response-conservation", data["payload_beats"] + data["scale_beats"],
                      data["responses"], {"mode": mode, "length": length})
    density = []
    for length in (1536, 8960):
        native, mx = streams[0, length], streams[1, length]
        probe.compare("exact-twofold-payload-density", native["payload_beats"],
                      2 * mx["payload_beats"], {"length": length})
        probe.compare("accounted-scale-fetches", True, mx["scale_beats"] > 0, {"length": length})
        density.append({
            "length": length, "rows": 3, "native": native, "mx": mx,
            "observed_payload_density_gain": native["payload_beats"] / mx["payload_beats"],
            "observed_bus_density_gain": native["payload_beats"] /
                                        (mx["payload_beats"] + mx["scale_beats"]),
            "ideal_unpadded_group32_storage_density": 64 / 33,
            "physical_tensor_lanes": 128,
        })
    probe.summary["stream_density"] = density
    probe.summary["streams"] = [{"mode": mode, "length": length, **data}
                                for (mode, length), data in sorted(streams.items())]


def main():
    probe = Probe("gemv-stream")
    probe.receipt["diagnostic_of"] = "evidence/preparation/fp2-gemv-stream-20261102T190441Z-ec4cfcca/receipt.json"
    try:
        with SuiteDeadline():
            run(probe)
        return probe.settle()
    except Exception as error:
        return probe.settle(f"{type(error).__name__}: {error}")


if __name__ == "__main__":
    raise SystemExit(main())
