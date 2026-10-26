module anvil_q1_ht_transaction_mux #(
  parameter CLIENTS = 3, REQUEST_WIDTH = 32, RESPONSE_WIDTH = 32
) (
  input wire clk, rst_n,
  input wire [(CLIENTS > 0 ? CLIENTS : 1)-1:0] client_valid,
  output wire [(CLIENTS > 0 ? CLIENTS : 1)-1:0] client_ready,
  input wire [(CLIENTS > 0 ? CLIENTS : 1)*(REQUEST_WIDTH > 0 ? REQUEST_WIDTH : 1)-1:0] client_data,
  output wire [(CLIENTS > 0 ? CLIENTS : 1)-1:0] client_rsp_valid,
  input wire [(CLIENTS > 0 ? CLIENTS : 1)-1:0] client_rsp_ready,
  output wire [(CLIENTS > 0 ? CLIENTS : 1)*(RESPONSE_WIDTH > 0 ? RESPONSE_WIDTH : 1)-1:0] client_rsp_data,
  output wire request_valid,
  input wire request_ready,
  output wire [(REQUEST_WIDTH > 0 ? REQUEST_WIDTH : 1)-1:0] request_data,
  input wire response_valid,
  output wire response_ready,
  input wire [(RESPONSE_WIDTH > 0 ? RESPONSE_WIDTH : 1)-1:0] response_data
);
  generate if (CLIENTS > 0 && REQUEST_WIDTH > 0 && RESPONSE_WIDTH > 0) begin : g_legal
    localparam OWNER_BITS = CLIENTS > 1 ? $clog2(CLIENTS) : 1;
    localparam IDLE = 2'd0, ISSUE = 2'd1, RESPONSE = 2'd2;
    reg [1:0] state;
    reg [OWNER_BITS-1:0] owner, selected;
    reg found;
    integer i;
    genvar client;
    always @* begin
      found = 0;
      selected = 0;
      for (i = 0; i < CLIENTS; i = i + 1) begin
        if (!found && client_valid[i]) begin
          found = 1;
          selected = OWNER_BITS'(i);
        end
      end
    end
    assign request_valid = rst_n && state == ISSUE && client_valid[owner];
    assign request_data = request_valid ? client_data[REQUEST_WIDTH*owner+:REQUEST_WIDTH] :
                                         {REQUEST_WIDTH{1'b0}};
    assign response_ready = rst_n && client_rsp_ready[owner] &&
      (state == RESPONSE || (state == ISSUE && request_valid && request_ready));
    for (client = 0; client < CLIENTS; client = client + 1) begin : g_client
      assign client_ready[client] = rst_n && state == ISSUE && owner == client && request_ready;
      assign client_rsp_valid[client] = rst_n && response_valid && owner == client &&
        (state == RESPONSE || (state == ISSUE && request_valid && request_ready));
      assign client_rsp_data[RESPONSE_WIDTH*client+:RESPONSE_WIDTH] =
        client_rsp_valid[client] ? response_data : {RESPONSE_WIDTH{1'b0}};
    end
    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin state <= IDLE; owner <= 0; end
      else case (state)
        IDLE: if (found) begin owner <= selected; state <= ISSUE; end
        ISSUE: begin
          if (!client_valid[owner]) state <= IDLE;
          if (request_valid && request_ready) state <= RESPONSE;
          if (response_valid && response_ready) state <= IDLE;
        end
        RESPONSE: if (response_valid && response_ready) state <= IDLE;
        default: state <= IDLE;
      endcase
    end
  end else begin : g_illegal
    initial $fatal(1, "ANVIL_Q1_HT PARAMETER ERROR: transaction mux dimensions");
    assign client_ready = 0;
    assign client_rsp_valid = 0;
    assign client_rsp_data = 0;
    assign request_valid = 0;
    assign request_data = 0;
    assign response_ready = 0;
  end endgenerate
endmodule
