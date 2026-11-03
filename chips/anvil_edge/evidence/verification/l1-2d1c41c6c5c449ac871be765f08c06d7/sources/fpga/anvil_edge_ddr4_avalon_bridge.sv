module anvil_edge_ddr4_avalon_bridge #(
  parameter integer AV_DATA_WIDTH=512,
  parameter integer AV_ADDRESS_WIDTH=26,
  parameter [63:0] DDR_BASE=0,
  parameter [63:0] DDR_BYTES=64'h0000000100000000
) (
  input wire clk, rst_n, calibration_done, memory_fault,
  input wire ddr_req_valid,
  output wire ddr_req_ready,
  input wire ddr_req_write,
  input wire [63:0] ddr_req_addr,
  input wire [31:0] ddr_req_wdata,
  input wire [3:0] ddr_req_wstrb,
  output wire ddr_rsp_valid,
  input wire ddr_rsp_ready,
  output wire [31:0] ddr_rsp_rdata,
  output wire ddr_rsp_error,
  output wire avm_read, avm_write,
  output wire [(AV_ADDRESS_WIDTH>0 ? AV_ADDRESS_WIDTH : 1)-1:0] avm_address,
  output wire [(AV_DATA_WIDTH>0 ? AV_DATA_WIDTH : 32)-1:0] avm_writedata,
  output wire [(AV_DATA_WIDTH>0 ? (AV_DATA_WIDTH>>3) : 4)-1:0] avm_byteenable,
  output wire avm_burstcount,
  input wire avm_waitrequest,
  input wire [(AV_DATA_WIDTH>0 ? AV_DATA_WIDTH : 32)-1:0] avm_readdata,
  input wire avm_readdatavalid,
  input wire [1:0] avm_response
);
  localparam integer SAFE_DATA=AV_DATA_WIDTH>=32 ? AV_DATA_WIDTH : 32;
  localparam integer BYTE_BITS=$clog2(SAFE_DATA>>3);
  localparam integer LANE_WIDTH=BYTE_BITS>2 ? BYTE_BITS-2 : 1;
  localparam [64:0] WINDOW_END={1'b0,DDR_BASE}+{1'b0,DDR_BYTES};
  generate if (AV_DATA_WIDTH<32 || AV_DATA_WIDTH>1024 ||
      (AV_DATA_WIDTH & (AV_DATA_WIDTH-1))!=0 || AV_ADDRESS_WIDTH<1 ||
      AV_ADDRESS_WIDTH>64-BYTE_BITS || DDR_BYTES==0 || DDR_BASE[1:0]!=0 ||
      DDR_BYTES[1:0]!=0 || WINDOW_END[64] ||
      (DDR_BASE & ((64'd1<<BYTE_BITS)-1))!=0 ||
      (DDR_BYTES & ((64'd1<<BYTE_BITS)-1))!=0 ||
      {1'b0,DDR_BYTES}>(65'd1<<(AV_ADDRESS_WIDTH+BYTE_BITS))) begin : invalid_parameters
    initial $fatal(1,"ANVIL_EDGE_DDR_BRIDGE PARAMETER ERROR: invalid bus geometry or DDR window");
    assign ddr_req_ready=0; assign ddr_rsp_valid=0;
    assign ddr_rsp_rdata=0; assign ddr_rsp_error=0;
    assign avm_read=0; assign avm_write=0; assign avm_address=0;
    assign avm_writedata=0; assign avm_byteenable=0; assign avm_burstcount=0;
  end else begin : bridge
    localparam [3:0] IDLE=0, END_ADDRESS=1, RANGE_CHECK=2,
      OFFSET_CHECK=3, ISSUE=4, READ_WAIT=5, UNPACK=6, RETURN=7;
    reg [3:0] state;
    reg request_write, failed;
    reg [63:0] request_address;
    reg [64:0] request_end, offset;
    reg [31:0] write_word, response_word;
    reg [3:0] write_strobes;
    reg [LANE_WIDTH-1:0] lane;
    reg [AV_ADDRESS_WIDTH-1:0] address;
    reg [AV_DATA_WIDTH-1:0] write_data, read_data;
    reg [(AV_DATA_WIDTH>>3)-1:0] byte_enable;
    wire [63:0] lane_value=offset[63:0]>>2;
    assign ddr_req_ready=rst_n && state==IDLE && calibration_done;
    assign ddr_rsp_valid=rst_n && state==RETURN;
    assign ddr_rsp_rdata=ddr_rsp_valid && !failed ? response_word : 0;
    assign ddr_rsp_error=ddr_rsp_valid && failed;
    assign avm_read=rst_n && state==ISSUE && !request_write;
    assign avm_write=rst_n && state==ISSUE && request_write;
    assign avm_address=rst_n ? address : 0;
    assign avm_writedata=rst_n ? write_data : 0;
    assign avm_byteenable=rst_n ? byte_enable : 0;
    assign avm_burstcount=rst_n && state==ISSUE;
    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        state<=IDLE; request_write<=0; failed<=0; request_address<=0;
        request_end<=0; offset<=0; write_word<=0; response_word<=0;
        write_strobes<=0; lane<=0; address<=0; write_data<=0;
        read_data<=0; byte_enable<=0;
      end else begin
        if (state!=IDLE && state!=RETURN && (memory_fault || !calibration_done))
          failed<=1;
        case (state)
          IDLE: if (ddr_req_valid && ddr_req_ready) begin
            request_write<=ddr_req_write; request_address<=ddr_req_addr;
            write_word<=ddr_req_wdata; write_strobes<=ddr_req_wstrb;
            response_word<=0; failed<=memory_fault; state<=END_ADDRESS;
          end
          END_ADDRESS: begin
            request_end<={1'b0,request_address}+65'd4;
            offset<={1'b0,request_address}-{1'b0,DDR_BASE};
            state<=RANGE_CHECK;
          end
          RANGE_CHECK: begin
            if (request_address[1:0]!=0 || request_address<DDR_BASE ||
                request_end[64] || request_end>WINDOW_END ||
                (request_write && write_strobes==0)) begin
              failed<=1; state<=RETURN;
            end else begin
              lane<=lane_value & ((AV_DATA_WIDTH>>5)-1);
              state<=OFFSET_CHECK;
            end
          end
          OFFSET_CHECK: begin
            if ((offset>>(AV_ADDRESS_WIDTH+BYTE_BITS))!=0) begin
              failed<=1; state<=RETURN;
            end else begin
              address<=offset>>BYTE_BITS;
              write_data<={{(AV_DATA_WIDTH-32){1'b0}},write_word} << {lane,5'b00000};
              byte_enable<={{((AV_DATA_WIDTH>>3)-4){1'b0}},
                (request_write ? write_strobes : 4'b1111)} << {lane,2'b00};
              state<=ISSUE;
            end
          end
          ISSUE: if (!avm_waitrequest) begin
            if (request_write) begin
              if (avm_response!=0) failed<=1;
              state<=RETURN;
            end else if (avm_readdatavalid) begin
              read_data<=avm_readdata;
              if (avm_response!=0) failed<=1;
              state<=UNPACK;
            end else state<=READ_WAIT;
          end
          READ_WAIT: if (avm_readdatavalid) begin
            read_data<=avm_readdata;
            if (avm_response!=0) failed<=1;
            state<=UNPACK;
          end
          UNPACK: begin response_word<=read_data>>{lane,5'b00000}; state<=RETURN; end
          RETURN: if (ddr_rsp_valid && ddr_rsp_ready) state<=IDLE;
          default: begin failed<=1; state<=RETURN; end
        endcase
      end
    end
  end endgenerate
endmodule
