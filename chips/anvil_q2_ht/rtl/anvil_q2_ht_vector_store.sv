module anvil_q2_ht_vector_store #(
  parameter WORDS=8960,
  parameter VECTORS=12
) (
  input wire clk, rst_n, annul,
  input wire wr_valid,
  input wire [3:0] wr_vector,
  input wire [31:0] wr_index,
  input wire [31:0] wr_data,
  input wire rd_valid,
  output wire rd_ready,
  input wire [3:0] rd_vector,
  input wire [31:0] rd_index,
  output wire rsp_valid,
  input wire rsp_ready,
  output wire [31:0] rsp_data,
  output wire rsp_error,
  input wire tile_valid,
  output wire tile_ready,
  input wire [3:0] tile_vector,
  input wire [31:0] tile_col,
  output wire tile_rsp_valid,
  input wire tile_rsp_ready,
  output wire [4095:0] tile_rsp_data,
  output wire tile_rsp_error
);
  localparam SAFE_WORDS=WORDS>0 ? WORDS : 1;
  localparam CHUNKS=(SAFE_WORDS+127) >> 7;
  localparam DEPTH=(VECTORS>0 ? VECTORS : 1)*CHUNKS;
  localparam AW=DEPTH<=1 ? 1 : $clog2(DEPTH);
  localparam LEGAL=WORDS>=8 && WORDS<=8960 && VECTORS>=1 && VECTORS<=16;
  generate if (!LEGAL) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q2_HT PARAMETER ERROR: vector store");
    assign rd_ready=0; assign rsp_valid=0; assign rsp_data=0; assign rsp_error=0;
    assign tile_ready=0; assign tile_rsp_valid=0;
    assign tile_rsp_data=0; assign tile_rsp_error=0;
  end else begin: implementation
    wire enabled=rst_n && !annul;
    reg scalar_busy, scalar_valid, scalar_error;
    reg [1:0] scalar_stage;
    reg [6:0] scalar_lane;
    reg [31:0] scalar_data;
    reg [31:0] bank_choice [0:15];
    reg tile_valid_reg, tile_error_reg;
    wire read=rd_valid && rd_ready;
    wire tile_read=tile_valid && tile_ready;
    wire bad_read=rd_vector>=VECTORS || rd_index>=WORDS;
    wire bad_tile=tile_vector>=VECTORS || tile_col>=WORDS || (|tile_col[6:0]);
    wire [AW-1:0] wr_address=AW'(wr_vector*CHUNKS+(wr_index >> 7));
    wire [AW-1:0] rd_address=AW'(rd_vector*CHUNKS+(rd_index >> 7));
    wire [AW-1:0] tile_address=AW'(tile_vector*CHUNKS+(tile_col >> 7));
    wire [31:0] scalar_slice [0:127];
    wire [31:0] tile_slice [0:127];
    genvar bank, slice;
    integer b;
    assign rd_ready=enabled && !scalar_busy && !scalar_valid &&
      (!tile_valid_reg || tile_rsp_ready);
    assign rsp_valid=enabled && scalar_valid;
    assign rsp_data=rsp_valid && !scalar_error ? scalar_data : 32'd0;
    assign rsp_error=rsp_valid && scalar_error;
    assign tile_ready=enabled && (!tile_valid_reg || tile_rsp_ready) && !read;
    assign tile_rsp_valid=enabled && tile_valid_reg;
    assign tile_rsp_error=tile_rsp_valid && tile_error_reg;
    for (bank=0; bank<16; bank=bank+1) begin: banks
      for (slice=0; slice<8; slice=slice+1) begin: slices
        localparam LANE=bank+16*slice;
        (* ramstyle = "M20K, no_rw_check" , nomem2reg *) reg [31:0] ram [0:DEPTH-1];
        reg [31:0] read_q;
        assign scalar_slice[LANE]=read_q;
        assign tile_slice[LANE]=read_q;
        assign tile_rsp_data[LANE*32+:32]=tile_rsp_valid && !tile_error_reg ?
          read_q : 32'd0;
        always @(posedge clk) begin
          if (enabled && wr_valid && wr_vector<VECTORS && wr_index<WORDS &&
              wr_index[6:0]==LANE) ram[wr_address]<=wr_data;
          if (enabled && read && !bad_read) read_q<=ram[rd_address];
          else if (enabled && tile_read && !bad_tile) read_q<=ram[tile_address];
        end
      end
    end
    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        scalar_busy<=0; scalar_valid<=0; scalar_error<=0; scalar_stage<=0;
        scalar_lane<=0; scalar_data<=0; tile_valid_reg<=0; tile_error_reg<=0;
        for (b=0; b<16; b=b+1) bank_choice[b]<=0;
      end else if (annul) begin
        scalar_busy<=0; scalar_valid<=0; tile_valid_reg<=0;
      end else begin
        if (scalar_valid && rsp_ready) scalar_valid<=0;
        if (read) begin
          scalar_busy<=1; scalar_stage<=0; scalar_lane<=rd_index[6:0];
          scalar_error<=bad_read;
        end
        if (scalar_busy) begin
          if (scalar_stage==0) begin
            for (b=0; b<16; b=b+1)
              bank_choice[b]<=scalar_slice[b+16*scalar_lane[6:4]];
            scalar_stage<=1;
          end else begin
            scalar_data<=scalar_error ? 32'd0 : bank_choice[scalar_lane[3:0]];
            scalar_valid<=1; scalar_busy<=0;
          end
        end
        if (tile_valid_reg && tile_rsp_ready) tile_valid_reg<=0;
        if (tile_read) begin
          tile_valid_reg<=1;
          tile_error_reg<=bad_tile;
        end
      end
    end
  end endgenerate
endmodule
