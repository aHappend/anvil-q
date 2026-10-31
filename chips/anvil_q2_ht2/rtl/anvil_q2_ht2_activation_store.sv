module anvil_q2_ht2_activation_store #(
  parameter MAX_WORDS=8960,
  parameter VECTOR_COUNT=16
) (
  input wire clk, rst_n, annul,
  input wire w_valid, w_rsp_ready,
  input wire [1:0] w_slot,
  input wire [31:0] w_vector, w_tile,
  input wire [2047:0] w_data,
  input wire [127:0] w_keep,
  output wire w_ready, w_rsp_valid, w_rsp_error,
  input wire r_valid, m_ready,
  input wire [31:0] r_vector, r_tile,
  input wire [3:0] r_token_mask,
  input wire [511:0] r_keep,
  input wire [63:0] r_tag,
  output wire r_ready, m_valid, m_error,
  output wire [8191:0] m_data,
  output wire [511:0] m_keep,
  output wire [63:0] m_tag
);
  localparam LEGAL=MAX_WORDS>=1 && MAX_WORDS<=8960 &&
    VECTOR_COUNT>=1 && VECTOR_COUNT<=32;
  generate if (!LEGAL) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q2_HT2 PARAMETER ERROR: activation storage geometry");
    assign w_ready=0; assign w_rsp_valid=0; assign w_rsp_error=0;
    assign r_ready=0; assign m_valid=0; assign m_error=0;
    assign m_data=0; assign m_keep=0; assign m_tag=0;
  end else begin: implementation
    localparam TILES=(MAX_WORDS+127) >> 7;
    localparam DEPTH=TILES*VECTOR_COUNT;
    localparam AW=DEPTH<=1 ? 1 : $clog2(DEPTH);
    reg [1:0] state;
    reg write_response, write_error, response_error, read_error;
    reg [3:0] read_mask;
    reg [511:0] read_keep, response_keep;
    reg [63:0] read_tag, response_tag;
    reg [8191:0] response_data;
    wire [31:0] write_index=w_vector*TILES+w_tile;
    wire [31:0] read_index=r_vector*TILES+r_tile;
    wire write_range=w_vector<VECTOR_COUNT && w_tile<TILES;
    wire read_range=r_vector<VECTOR_COUNT && r_tile<TILES;
    reg [127:0] write_legal_keep, read_legal_keep;
    wire write_transfer=w_valid && w_ready;
    wire read_transfer=r_valid && r_ready;
    wire write_good=write_range && (w_keep & ~write_legal_keep)==0;
    wire [8703:0] memory_data;
    wire [3:0] memory_valid;
    wire [511:0] memory_keep;
    reg missing;
    integer j,t;
    genvar slot;

    always @* begin
      write_legal_keep=0;
      read_legal_keep=0;
      for (j=0;j<128;j=j+1) begin
        if (w_tile<(MAX_WORDS >> 7) ||
            (w_tile==(MAX_WORDS >> 7) && j<(MAX_WORDS & 127)))
          write_legal_keep[j]=1;
        if (r_tile<(MAX_WORDS >> 7) ||
            (r_tile==(MAX_WORDS >> 7) && j<(MAX_WORDS & 127)))
          read_legal_keep[j]=1;
      end
    end

    for (slot=0;slot<4;slot=slot+1) begin: token
      (* ramstyle = "M20K", nomem2reg *) reg [2175:0] data [0:DEPTH-1];
      reg [DEPTH-1:0] initialized;
      reg [2175:0] read_data;
      reg read_initialized;
      wire we=write_transfer && write_good && w_slot==slot;
      assign memory_data[2176*slot+:2176]=read_data;
      assign memory_keep[128*slot+:128]=read_data[2175:2048];
      assign memory_valid[slot]=read_initialized;

      always @(posedge clk) begin
        if (we) data[AW'(write_index)]<={w_keep,w_data};
        if (read_transfer && read_range) begin
          if (we && write_index==read_index)
            read_data<={w_keep,w_data};
          else read_data<=data[AW'(read_index)];
        end
      end
      always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin initialized<=0; read_initialized<=0; end
        else if (annul) begin initialized<=0; read_initialized<=0; end
        else begin
          if (we) initialized[AW'(write_index)]<=1;
          if (read_transfer) begin
            if (!read_range) read_initialized<=0;
            else read_initialized<=initialized[AW'(read_index)] ||
              (we && write_index==read_index);
          end
        end
      end
    end

    always @* begin
      missing=read_error;
      for (t=0;t<4;t=t+1)
        if (read_mask[t] && (|read_keep[128*t+:128]) &&
            (!memory_valid[t] ||
              (read_keep[128*t+:128] & ~memory_keep[128*t+:128])!=0))
          missing=1;
    end

    assign w_ready=rst_n && !annul && (!write_response || w_rsp_ready);
    assign w_rsp_valid=rst_n && !annul && write_response;
    assign w_rsp_error=w_rsp_valid && write_error;
    assign r_ready=rst_n && !annul && state==0;
    assign m_valid=rst_n && !annul && state==2;
    assign m_error=m_valid && response_error;
    assign m_data=m_valid && !response_error ? response_data : 8192'd0;
    assign m_keep=m_valid && !response_error ? response_keep : 512'd0;
    assign m_tag=m_valid ? response_tag : 64'd0;

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        state<=0; write_response<=0; write_error<=0;
        response_error<=0; read_error<=0; read_mask<=0;
        read_keep<=0; response_keep<=0; read_tag<=0;
        response_tag<=0; response_data<=0;
      end else if (annul) begin
        state<=0; write_response<=0;
      end else begin
        if (write_response && w_rsp_ready) write_response<=0;
        if (write_transfer) begin
          write_response<=1;
          write_error<=!write_good;
        end
        case (state)
          0: if (read_transfer) begin
            read_error<=!read_range;
            read_mask<=r_token_mask; read_tag<=r_tag;
            for (t=0;t<4;t=t+1) begin
              read_keep[128*t+:128]<=r_token_mask[t] ?
                r_keep[128*t+:128] : 128'd0;
              if (r_token_mask[t] &&
                  (r_keep[128*t+:128] & ~read_legal_keep)!=0)
                read_error<=1;
            end
            state<=1;
          end
          1: begin
            response_error<=missing;
            response_tag<=read_tag;
            response_keep<=read_keep;
            for (t=0;t<4;t=t+1)
              for (j=0;j<128;j=j+1)
                response_data[(128*t+j)*16+:16]<=read_keep[128*t+j] ?
                  memory_data[2176*t+16*j+:16] : 16'd0;
            state<=2;
          end
          2: if (m_ready) state<=0;
          default: begin
            response_error<=1; response_tag<=0; response_keep<=0;
            response_data<=0; state<=2;
          end
        endcase
      end
    end
  end endgenerate
endmodule
