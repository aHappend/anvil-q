module anvil_q2_fp2_ddr_engine #(
  parameter QUEUE_DEPTH=3,
  parameter SLOTS=(QUEUE_DEPTH>=2 && QUEUE_DEPTH<=16) ? QUEUE_DEPTH : 2
) (
  input wire clk, rst_n, flush,
  input wire req_valid,
  output wire req_ready,
  input wire req_write,
  input wire [3:0] req_kind,
  input wire [31:0] req_layer,
  input wire [2:0] req_proj,
  input wire [31:0] req_row, req_col,
  input wire [1:0] req_format,
  input wire [31:0] req_tag,
  input wire [511:0] req_wdata,
  input wire [63:0] req_wstrb,
  output wire rsp_valid,
  input wire rsp_ready,
  output wire [511:0] rsp_rdata,
  output wire [31:0] rsp_tag,
  output wire rsp_error,
  output wire idle, draining,
  output wire drain_done, fault,
  output wire ddr_req_valid,
  input wire ddr_req_ready,
  output wire ddr_req_write,
  output wire [3:0] ddr_req_kind,
  output wire [31:0] ddr_req_layer,
  output wire [2:0] ddr_req_proj,
  output wire [31:0] ddr_req_row, ddr_req_col,
  output wire [1:0] ddr_req_format,
  output wire [63:0] ddr_req_tag,
  output wire [511:0] ddr_req_wdata,
  output wire [63:0] ddr_req_wstrb,
  input wire ddr_rsp_valid, ddr_rsp_error,
  output wire ddr_rsp_ready,
  input wire [63:0] ddr_rsp_tag,
  input wire [511:0] ddr_rsp_rdata
);
  localparam N=(SLOTS>=2 && SLOTS<=16) ? SLOTS : 2;
  generate if (QUEUE_DEPTH<1 || QUEUE_DEPTH>16 || SLOTS!=((QUEUE_DEPTH<2) ? 2 : QUEUE_DEPTH)) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q2_FP2 PARAMETER ERROR: DDR queue depth");
    assign req_ready=0;
    assign rsp_valid=0; assign rsp_rdata=0; assign rsp_tag=0; assign rsp_error=0;
    assign idle=0; assign draining=0; assign drain_done=0; assign fault=0;
    assign ddr_req_valid=0; assign ddr_req_write=0; assign ddr_req_kind=0;
    assign ddr_req_layer=0; assign ddr_req_proj=0; assign ddr_req_row=0;
    assign ddr_req_col=0; assign ddr_req_format=0; assign ddr_req_tag=0;
    assign ddr_req_wdata=0; assign ddr_req_wstrb=0; assign ddr_rsp_ready=0;
  end else begin: transport
    localparam FREE=0, QUEUED=1, SENT=2, COMPLETE=3;
    localparam P=$clog2(N);
    reg [P-1:0] allocate_cursor, issue_cursor, retire_cursor;
    reg [1:0] ownership [0:N-1];
    reg [63:0] transaction_tag [0:N-1];
    reg [31:0] client_tag [0:N-1];
    reg write_bit [0:N-1], response_error [0:N-1];
    reg [3:0] kind [0:N-1];
    reg [31:0] layer [0:N-1], row [0:N-1], column [0:N-1];
    reg [2:0] projection [0:N-1];
    reg [1:0] format [0:N-1];
    (* nomem2reg *) reg [511:0] write_data [0:N-1], response_data [0:N-1];
    reg [63:0] write_strobe [0:N-1];
    reg [63:0] next_tag;
    reg drain_active, drain_pulse, protocol_fault;
    wire [N-1:0] occupied, sent, tag_match, collision;
    genvar slot;
    for (slot=0;slot<N;slot=slot+1) begin: ownership_match
      assign occupied[slot]=ownership[slot]!=FREE;
      assign sent[slot]=ownership[slot]==SENT;
      assign tag_match[slot]=sent[slot] && transaction_tag[slot]==ddr_rsp_tag;
      assign collision[slot]=occupied[slot] && transaction_tag[slot]==next_tag;
    end
    wire accept=req_valid && req_ready;
    wire send=ddr_req_valid && ddr_req_ready;
    wire receive=ddr_rsp_valid && ddr_rsp_ready;
    wire retire=rsp_valid && rsp_ready;
    assign req_ready=rst_n && !flush && !drain_active &&
      ownership[allocate_cursor]==FREE && !(|collision);
    assign rsp_valid=rst_n && !flush && !drain_active &&
      ownership[retire_cursor]==COMPLETE;
    assign rsp_rdata=rsp_valid ? response_data[retire_cursor] : 512'd0;
    assign rsp_tag=rsp_valid ? client_tag[retire_cursor] : 32'd0;
    assign rsp_error=rsp_valid && response_error[retire_cursor];
    assign idle=rst_n && !drain_active && !(|occupied);
    assign draining=rst_n && drain_active;
    assign drain_done=rst_n && drain_pulse;
    assign fault=rst_n && protocol_fault;
    assign ddr_req_valid=rst_n && !flush && !drain_active &&
      ownership[issue_cursor]==QUEUED;
    assign ddr_req_write=ddr_req_valid && write_bit[issue_cursor];
    assign ddr_req_kind=ddr_req_valid ? kind[issue_cursor] : 4'd0;
    assign ddr_req_layer=ddr_req_valid ? layer[issue_cursor] : 32'd0;
    assign ddr_req_proj=ddr_req_valid ? projection[issue_cursor] : 3'd0;
    assign ddr_req_row=ddr_req_valid ? row[issue_cursor] : 32'd0;
    assign ddr_req_col=ddr_req_valid ? column[issue_cursor] : 32'd0;
    assign ddr_req_format=ddr_req_valid ? format[issue_cursor] : 2'd0;
    assign ddr_req_tag=ddr_req_valid ? transaction_tag[issue_cursor] : 64'd0;
    assign ddr_req_wdata=ddr_req_valid ? write_data[issue_cursor] : 512'd0;
    assign ddr_req_wstrb=ddr_req_valid ? write_strobe[issue_cursor] : 64'd0;
    assign ddr_rsp_ready=rst_n;
    integer i;
    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        allocate_cursor<=0; issue_cursor<=0; retire_cursor<=0;
        next_tag<=0; drain_active<=0; drain_pulse<=0; protocol_fault<=0;
        for (i=0;i<N;i=i+1) ownership[i]<=FREE;
      end else begin
        drain_pulse<=0;
        protocol_fault<=0;
        if (receive && !(|tag_match)) protocol_fault<=1;
        if (flush || drain_active) begin
          allocate_cursor<=0; issue_cursor<=0; retire_cursor<=0;
          if (flush) drain_active<=1;
          else if (!(|sent)) begin drain_active<=0; drain_pulse<=1; end
          for (i=0;i<N;i=i+1) begin
            if (ownership[i]!=SENT || (receive && tag_match[i])) ownership[i]<=FREE;
          end
        end else begin
          if (accept) begin
            ownership[allocate_cursor]<=QUEUED;
            transaction_tag[allocate_cursor]<=next_tag;
            client_tag[allocate_cursor]<=req_tag;
            write_bit[allocate_cursor]<=req_write;
            kind[allocate_cursor]<=req_kind;
            layer[allocate_cursor]<=req_layer;
            projection[allocate_cursor]<=req_proj;
            row[allocate_cursor]<=req_row;
            column[allocate_cursor]<=req_col;
            format[allocate_cursor]<=req_format;
            write_data[allocate_cursor]<=req_wdata;
            write_strobe[allocate_cursor]<=req_wstrb;
            next_tag<=next_tag+64'd1;
            allocate_cursor<=(allocate_cursor==N-1) ? {P{1'b0}} : allocate_cursor+1'b1;
          end
          if (send) begin
            ownership[issue_cursor]<=SENT;
            issue_cursor<=(issue_cursor==N-1) ? {P{1'b0}} : issue_cursor+1'b1;
          end
          if (receive) begin
            for (i=0;i<N;i=i+1) if (tag_match[i]) begin
              ownership[i]<=COMPLETE;
              response_data[i]<=ddr_rsp_rdata;
              response_error[i]<=ddr_rsp_error;
            end
          end
          if (retire) begin
            ownership[retire_cursor]<=FREE;
            retire_cursor<=(retire_cursor==N-1) ? {P{1'b0}} : retire_cursor+1'b1;
          end
        end
      end
    end
  end endgenerate
endmodule
