module anvil_q1_fp2_ddr_pingpong (
  input wire clk, rst_n,
  input wire cmd_valid,
  output wire cmd_ready,
  input wire cmd_write, cmd_scale,
  input wire [3:0] cmd_kind,
  input wire [31:0] cmd_layer,
  input wire [2:0] cmd_proj,
  input wire [31:0] cmd_row, cmd_col, cmd_tag,
  input wire [511:0] cmd_wdata,
  input wire [63:0] cmd_wstrb,
  output wire out_valid,
  input wire out_ready,
  output wire [31:0] out_tag,
  output wire out_write, out_error,
  output wire [511:0] out_data,
  input wire work_active, result_needed,
  output wire stall_event,
  output wire ddr_req_valid,
  input wire ddr_req_ready,
  output wire ddr_req_write, ddr_req_id, ddr_req_scale,
  output wire [3:0] ddr_req_kind,
  output wire [31:0] ddr_req_layer,
  output wire [2:0] ddr_req_proj,
  output wire [31:0] ddr_req_row, ddr_req_col,
  output wire [511:0] ddr_req_wdata,
  output wire [63:0] ddr_req_wstrb,
  input wire ddr_rsp_valid,
  output wire ddr_rsp_ready,
  input wire ddr_rsp_id, ddr_rsp_error,
  input wire [511:0] ddr_rsp_rdata
);
  localparam [1:0] FREE=0, QUEUED=1, INFLIGHT=2, RETURNED=3;
  reg [1:0] ownership [0:1];
  reg head, tail;
  reg [1:0] occupied;
  reg writes [0:1], scales [0:1], faults [0:1];
  reg [3:0] kinds [0:1];
  reg [2:0] projections [0:1];
  reg [31:0] layers [0:1], rows [0:1], columns [0:1], tags [0:1];
  reg [511:0] write_data [0:1], response_data [0:1];
  reg [63:0] strobes [0:1];
  wire issue_slot=ownership[head]==QUEUED ? head : !head;
  wire pop=out_valid && out_ready;
  wire push=cmd_valid && cmd_ready;
  wire issue=ddr_req_valid && ddr_req_ready;
  wire response=ddr_rsp_valid && ddr_rsp_ready;
  assign cmd_ready=rst_n && (occupied<2 || pop);
  assign out_valid=rst_n && occupied!=0 && ownership[head]==RETURNED;
  assign out_tag=out_valid ? tags[head] : 32'd0;
  assign out_write=out_valid && writes[head];
  assign out_error=out_valid && faults[head];
  assign out_data=out_valid ? response_data[head] : 512'd0;
  assign ddr_req_valid=rst_n && ownership[issue_slot]==QUEUED;
  assign ddr_req_write=ddr_req_valid && writes[issue_slot];
  assign ddr_req_id=ddr_req_valid && issue_slot;
  assign ddr_req_scale=ddr_req_valid && scales[issue_slot];
  assign ddr_req_kind=ddr_req_valid ? kinds[issue_slot] : 4'd0;
  assign ddr_req_layer=ddr_req_valid ? layers[issue_slot] : 32'd0;
  assign ddr_req_proj=ddr_req_valid ? projections[issue_slot] : 3'd0;
  assign ddr_req_row=ddr_req_valid ? rows[issue_slot] : 32'd0;
  assign ddr_req_col=ddr_req_valid ? columns[issue_slot] : 32'd0;
  assign ddr_req_wdata=ddr_req_valid ? write_data[issue_slot] : 512'd0;
  assign ddr_req_wstrb=ddr_req_valid ? strobes[issue_slot] : 64'd0;
  assign ddr_rsp_ready=rst_n && (ownership[ddr_rsp_id]==INFLIGHT ||
    (issue && issue_slot==ddr_rsp_id));
  assign stall_event=rst_n && work_active &&
    ((ddr_req_valid && !ddr_req_ready) ||
     (result_needed && occupied!=0 && ownership[head]==INFLIGHT));
  integer i;
  always @(posedge clk) begin
    if (!rst_n) begin
      head<=0; tail<=0; occupied<=0;
      for (i=0;i<2;i=i+1) ownership[i]<=FREE;
    end else begin
      case ({push,pop})
        2'b10: occupied<=occupied+1'b1;
        2'b01: occupied<=occupied-1'b1;
        default: begin end
      endcase
      if (pop) begin ownership[head]<=FREE; head<=!head; end
      if (push) begin
        ownership[tail]<=QUEUED; tail<=!tail;
        writes[tail]<=cmd_write; scales[tail]<=cmd_scale;
        kinds[tail]<=cmd_kind; layers[tail]<=cmd_layer; projections[tail]<=cmd_proj;
        rows[tail]<=cmd_row; columns[tail]<=cmd_col; tags[tail]<=cmd_tag;
        write_data[tail]<=cmd_wdata; strobes[tail]<=cmd_wstrb;
      end
      if (issue) ownership[issue_slot]<=INFLIGHT;
      if (response) begin
        ownership[ddr_rsp_id]<=RETURNED;
        response_data[ddr_rsp_id]<=ddr_rsp_rdata;
        faults[ddr_rsp_id]<=ddr_rsp_error;
      end
    end
  end
endmodule
