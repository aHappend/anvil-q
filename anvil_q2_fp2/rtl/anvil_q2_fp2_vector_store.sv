module anvil_q2_fp2_scalar_store #(
  parameter WIDTH=32, LENGTH=1536,
  parameter A=(LENGTH>1) ? $clog2(LENGTH) : 1
) (
  input wire clk, rst_n,
  input wire write_valid,
  input wire [31:0] write_index,
  input wire [WIDTH-1:0] write_data,
  input wire read_valid,
  input wire [31:0] read_index,
  output wire [WIDTH-1:0] read_data
);
  (* ramstyle = "M20K", nomem2reg *) reg [WIDTH-1:0] storage [0:LENGTH-1];
  reg [WIDTH-1:0] captured;
  always @(posedge clk) begin
    if (rst_n) begin
      if (write_valid && write_index<LENGTH)
        storage[write_index[A-1:0]]<=write_data;
      if (read_valid && read_index<LENGTH)
        captured<=storage[read_index[A-1:0]];
    end
  end
  assign read_data=rst_n ? captured : {WIDTH{1'b0}};
endmodule

module anvil_q2_fp2_vector_store #(
  parameter LENGTH=1536,
  parameter TILES=(LENGTH+127) >> 7,
  parameter A=(TILES>1) ? $clog2(TILES) : 1
) (
  input wire clk, rst_n,
  input wire write_valid,
  input wire [31:0] write_index,
  input wire [15:0] write_data,
  input wire read_valid,
  input wire [31:0] read_column,
  output wire out_valid,
  output wire [2047:0] out_data
);
  reg pending;
  wire [31:0] write_tile=write_index >> 7;
  wire [31:0] read_tile=read_column >> 7;
  genvar lane;
  generate for (lane=0;lane<128;lane=lane+1) begin: banks
    (* ramstyle = "M20K", nomem2reg *) reg [15:0] storage [0:TILES-1];
    reg [15:0] captured;
    always @(posedge clk) begin
      if (rst_n) begin
        if (write_valid && write_index<LENGTH && write_index[6:0]==lane)
          storage[write_tile[A-1:0]]<=write_data;
        if (read_valid)
          if (read_column+lane<LENGTH) captured<=storage[read_tile[A-1:0]];
          else captured<=0;
      end
    end
    assign out_data[16*lane+:16]=rst_n && pending ? captured : 16'd0;
  end endgenerate
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) pending<=0;
    else pending<=read_valid;
  end
  assign out_valid=rst_n && pending;
endmodule
