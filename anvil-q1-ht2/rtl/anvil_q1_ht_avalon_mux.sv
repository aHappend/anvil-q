module anvil_q1_ht_avalon_mux (
  input wire ddr_clk, rst_n,
  input wire [65:0] client_address,
  input wire [15:0] client_burstcount,
  input wire [1:0] client_read, client_write,
  input wire [1023:0] client_writedata,
  input wire [127:0] client_byteenable,
  output wire [1:0] client_waitrequest,
  output wire [1023:0] client_readdata,
  output wire [1:0] client_readdatavalid,
  output wire [3:0] client_response,
  output wire [1:0] client_writeresponsevalid,
  output wire [32:0] avm_address,
  output wire [7:0] avm_burstcount,
  output wire avm_read, avm_write,
  output wire [511:0] avm_writedata,
  output wire [63:0] avm_byteenable,
  input wire avm_waitrequest,
  input wire [511:0] avm_readdata,
  input wire avm_readdatavalid,
  input wire [1:0] avm_response,
  input wire avm_writeresponsevalid,
  output wire protocol_error
);
  localparam IDLE = 2'd0, COMMAND = 2'd1, RESPONSE = 2'd2;
  reg [1:0] state;
  reg owner, last_owner, response_write, failed;
  reg [7:0] remaining;
  wire [1:0] requesting = client_read | client_write;
  wire issue = rst_n && state == COMMAND;
  wire accepted = issue && (avm_read || avm_write) && !avm_waitrequest;
  wire read_allowed = (state == RESPONSE && !response_write) || (accepted && avm_read);
  wire write_allowed = (state == RESPONSE && response_write) || (accepted && avm_write);
  wire read_response = rst_n && read_allowed && avm_readdatavalid;
  wire write_response = rst_n && write_allowed && avm_writeresponsevalid;
  wire [7:0] response_count = state == COMMAND ? avm_burstcount : remaining;
  genvar client;
  assign avm_read = issue && client_read[owner];
  assign avm_write = issue && client_write[owner];
  assign avm_address = issue ? client_address[33*owner+:33] : 33'b0;
  assign avm_burstcount = issue ? client_burstcount[8*owner+:8] : 8'b0;
  assign avm_writedata = avm_write ? client_writedata[512*owner+:512] : 512'b0;
  assign avm_byteenable = issue ? client_byteenable[64*owner+:64] : 64'b0;
  assign protocol_error = rst_n && failed;
  for (client = 0; client < 2; client = client + 1) begin : g_client
    assign client_waitrequest[client] =
      rst_n && (!issue || owner != client || avm_waitrequest);
    assign client_readdatavalid[client] = read_response && owner == client;
    assign client_readdata[512*client+:512] = client_readdatavalid[client] ? avm_readdata : 512'b0;
    assign client_writeresponsevalid[client] = write_response && owner == client;
    assign client_response[2*client+:2] =
      (client_readdatavalid[client] || client_writeresponsevalid[client]) ? avm_response : 2'b0;
  end
  always @(posedge ddr_clk or negedge rst_n) begin
    if (!rst_n) begin
      state <= IDLE;
      owner <= 0;
      last_owner <= 1;
      response_write <= 0;
      failed <= 0;
      remaining <= 0;
    end else begin
      if ((avm_readdatavalid && !read_allowed) || (avm_writeresponsevalid && !write_allowed))
        failed <= 1;
      case (state)
        IDLE: if (|requesting) begin
          if (requesting == 2'b11) owner <= !last_owner;
          else owner <= requesting[1];
          state <= COMMAND;
        end
        COMMAND: if (accepted) begin
          remaining <= avm_burstcount;
          response_write <= avm_write;
          last_owner <= owner;
          state <= RESPONSE;
          if ((avm_read && avm_write) || avm_burstcount == 0 || avm_burstcount > 16)
            failed <= 1;
        end
        RESPONSE: begin end
        default: begin failed <= 1; state <= IDLE; end
      endcase
      if (read_response) begin
        remaining <= response_count - 8'd1;
        if (response_count == 1) state <= IDLE;
      end
      if (write_response) state <= IDLE;
    end
  end
endmodule
