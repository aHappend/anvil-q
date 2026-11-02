module anvil_q4_descriptor #(
  parameter integer BANKS = 16
) (
  input wire clk,
  input wire rst_n,
  input wire cancel,
  input wire quiescent,
  input wire cfg_valid,
  input wire cfg_commit,
  input wire [5:0] cfg_index,
  input wire [31:0] cfg_wdata,
  output wire cfg_ready,
  output reg cfg_done,
  output reg cfg_error,
  output wire cfg_busy,
  output wire [1023:0] active_words
);
  localparam integer LEGAL_BANKS =
    BANKS == 1 || BANKS == 2 || BANKS == 4 || BANKS == 8 || BANKS == 16;

  generate
    if (!LEGAL_BANKS) begin : invalid_parameters
      initial $fatal(1, "PARAMETER ERROR: anvil_q4_descriptor BANKS must be 1/2/4/8/16");
      assign cfg_ready = 1'b0;
      assign cfg_busy = 1'b0;
      assign active_words = 1024'd0;
      always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin cfg_done <= 1'b0; cfg_error <= 1'b0; end
        else begin cfg_done <= 1'b0; cfg_error <= 1'b0; end
      end
    end else begin : legal
      localparam [2:0] IDLE = 0, DERIVE = 1, REMAINDER_INIT = 2,
        REMAINDER_STEP = 3, EVALUATE = 4, COMMIT_RESPONSE = 5, SETTLE = 6;

      function automatic [1023:0] reset_image;
        reg [1023:0] image;
        begin
          image = 1024'd0;
          image[0*32+:32] = 32'd1;
          image[1*32+:32] = 32'd4;
          image[2*32+:32] = 32'd0;
          image[3*32+:32] = 32'd1;
          image[4*32+:32] = 32'd0;
          image[5*32+:32] = 32'd0;
          image[6*32+:32] = BANKS;
          image[7*32+:32] = 32'd28;
          image[8*32+:32] = 32'd3584;
          image[9*32+:32] = 32'd18944;
          image[10*32+:32] = 32'd28;
          image[11*32+:32] = 32'd4;
          image[12*32+:32] = 32'd128;
          image[13*32+:32] = 32'd152064;
          image[14*32+:32] = 32'd32768;
          image[15*32+:32] = 32'd128;
          image[16*32+:32] = 32'd1;
          image[17*32+:32] = 32'h49742400;
          image[18*32+:32] = 32'h358637bd;
          image[19*32+:32] = 32'd32;
          image[20*32+:32] = 32'd1024;
          image[21*32+:32] = 32'd1;
          image[22*32+:32] = 32'd7;
          image[23*32+:32] = 32'd1;
          reset_image = image;
        end
      endfunction

      function automatic positive_finite(input [31:0] value);
        positive_finite = !value[31] && value[30:23] != 8'hff &&
          value[30:0] != 31'd0;
      endfunction

      function automatic power_of_two(input [31:0] value);
        power_of_two = value != 0 && (value & (value - 32'd1)) == 0;
      endfunction

      localparam [1023:0] RESET_IMAGE = reset_image();
      reg [1023:0] shadow, active;
      reg [2:0] state;
      reg write_fault, shadow_valid, commit_valid, scalar_valid;
      reg [15:0] hidden_numerator, intermediate_numerator;
      reg [8:0] hidden_remainder, intermediate_remainder;
      reg [4:0] remainder_bit;
      reg [16:0] computed_hidden, computed_kv_width;
      reg [15:0] computed_queries;
      reg [22:0] computed_page_capacity;
      reg [31:0] successful_commits;

      wire [31:0] version = shadow[0*32+:32];
      wire [31:0] mode = shadow[1*32+:32];
      wire [31:0] activation_format = shadow[2*32+:32];
      wire [31:0] weight_format = shadow[3*32+:32];
      wire [31:0] activation_quantization = shadow[4*32+:32];
      wire [31:0] cache_encoding = shadow[5*32+:32];
      wire [31:0] banks = shadow[6*32+:32];
      wire [31:0] layers = shadow[7*32+:32];
      wire [31:0] hidden = shadow[8*32+:32];
      wire [31:0] intermediate = shadow[9*32+:32];
      wire [31:0] query_heads = shadow[10*32+:32];
      wire [31:0] kv_heads = shadow[11*32+:32];
      wire [31:0] head_dim = shadow[12*32+:32];
      wire [31:0] vocabulary = shadow[13*32+:32];
      wire [31:0] context_capacity = shadow[14*32+:32];
      wire [31:0] group_size = shadow[15*32+:32];
      wire [31:0] bias_enable = shadow[16*32+:32];
      wire [31:0] theta = shadow[17*32+:32];
      wire [31:0] epsilon = shadow[18*32+:32];
      wire [31:0] page_tokens = shadow[19*32+:32];
      wire [31:0] physical_pages = shadow[20*32+:32];
      wire [31:0] zero_convention = shadow[21*32+:32];
      wire [31:0] ratio = shadow[22*32+:32];
      wire [31:0] cache_block = shadow[24*32+:32];

      wire common_valid =
        version == 1 && mode >= 1 && mode <= 4 &&
        power_of_two(banks) && banks <= BANKS &&
        layers >= 1 && layers <= 64 &&
        hidden >= 2 && hidden <= 8192 &&
        intermediate >= 1 && intermediate <= 32768 &&
        query_heads >= 1 && query_heads <= 128 &&
        kv_heads >= 1 && kv_heads <= 128 &&
        head_dim >= 2 && head_dim <= 256 && !head_dim[0] &&
        vocabulary >= 1 && vocabulary <= 262144 &&
        context_capacity >= 1 && context_capacity <= 131072 &&
        group_size >= 1 && group_size <= 128 &&
        (ratio == 1 || ratio == 3 || ratio == 6 || ratio == 7 || ratio == 8) &&
        positive_finite(theta) && positive_finite(epsilon) &&
        shadow[25*32+:224] == 224'd0;

      wire q4_valid =
        activation_format <= 1 && weight_format <= 2 &&
        activation_quantization <= 1 &&
        !(activation_quantization == 1 && weight_format == 0) &&
        cache_encoding <= 1 && bias_enable <= 1 &&
        zero_convention <= 1 && cache_block == 0 &&
        power_of_two(page_tokens) && page_tokens <= 32 &&
        physical_pages >= 1 && physical_pages <= 131072;

      wire legacy_block_valid =
        (cache_encoding == 0 && cache_block == 1) ||
        (mode == 2 && cache_encoding == 1 && power_of_two(cache_block) &&
          cache_block <= head_dim && (head_dim & (cache_block - 32'd1)) == 0) ||
        (mode == 3 && cache_encoding == 1 && cache_block == 32) ||
        (mode == 3 && (cache_encoding == 2 || cache_encoding == 3) && cache_block == 64);

      wire legacy_valid =
        activation_format == 1 && weight_format == 1 &&
        activation_quantization == 0 && bias_enable == 1 &&
        zero_convention == 1 && banks <= 8 &&
        hidden[2:0] == 0 && intermediate[2:0] == 0 &&
        context_capacity <= 32768 && page_tokens == 1 &&
        physical_pages == context_capacity && epsilon == 32'h358637bd &&
        (mode != 3 || ratio == 8) && legacy_block_valid;

      wire [8:0] shifted_hidden_remainder =
        {hidden_remainder[7:0], hidden_numerator[15]};
      wire [8:0] shifted_intermediate_remainder =
        {intermediate_remainder[7:0], intermediate_numerator[15]};
      wire [8:0] divisor = {1'b0, group_size[7:0]};
      wire [8:0] next_hidden_remainder = shifted_hidden_remainder >= divisor ?
        shifted_hidden_remainder - divisor : shifted_hidden_remainder;
      wire [8:0] next_intermediate_remainder = shifted_intermediate_remainder >= divisor ?
        shifted_intermediate_remainder - divisor : shifted_intermediate_remainder;

      assign active_words = rst_n ? active : 1024'd0;
      assign cfg_ready = rst_n && !cancel && quiescent && state == IDLE;
      assign cfg_busy = rst_n && state != IDLE;

      always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
          shadow <= RESET_IMAGE;
          active <= RESET_IMAGE;
          state <= IDLE;
          write_fault <= 1'b0;
          shadow_valid <= 1'b1;
          commit_valid <= 1'b0;
          scalar_valid <= 1'b0;
          hidden_numerator <= 0;
          intermediate_numerator <= 0;
          hidden_remainder <= 0;
          intermediate_remainder <= 0;
          remainder_bit <= 0;
          computed_hidden <= 0;
          computed_kv_width <= 0;
          computed_queries <= 0;
          computed_page_capacity <= 0;
          successful_commits <= 0;
          cfg_done <= 1'b0;
          cfg_error <= 1'b0;
        end else begin
          cfg_done <= 1'b0;
          cfg_error <= 1'b0;
          case (state)
            IDLE: if (cfg_valid && cfg_ready) begin
              if (cfg_commit) begin
                commit_valid <= shadow_valid && !write_fault &&
                  successful_commits!=32'hffffffff;
                state <= COMMIT_RESPONSE;
              end else if (cfg_index >= 32) begin
                write_fault <= 1'b1;
              end else begin
                shadow[cfg_index*32+:32] <= cfg_wdata;
                state <= DERIVE;
              end
            end
            DERIVE: begin
              scalar_valid <= common_valid && (mode == 4 ? q4_valid : legacy_valid);
              computed_hidden <= {9'd0, query_heads[7:0]} * {8'd0, head_dim[8:0]};
              computed_kv_width <= {9'd0, kv_heads[7:0]} * {8'd0, head_dim[8:0]};
              computed_queries <= {8'd0, kv_heads[7:0]} * {12'd0, ratio[3:0]};
              computed_page_capacity <=
                {5'd0, physical_pages[17:0]} * {17'd0, page_tokens[5:0]};
              state <= REMAINDER_INIT;
            end
            REMAINDER_INIT: begin
              hidden_numerator <= hidden[15:0];
              intermediate_numerator <= intermediate[15:0];
              hidden_remainder <= 0;
              intermediate_remainder <= 0;
              remainder_bit <= 15;
              state <= REMAINDER_STEP;
            end
            REMAINDER_STEP: begin
              hidden_numerator <= {hidden_numerator[14:0], 1'b0};
              intermediate_numerator <= {intermediate_numerator[14:0], 1'b0};
              hidden_remainder <= next_hidden_remainder;
              intermediate_remainder <= next_intermediate_remainder;
              if (remainder_bit == 0) state <= EVALUATE;
              else remainder_bit <= remainder_bit - 1'b1;
            end
            EVALUATE: begin
              shadow_valid <= scalar_valid &&
                hidden == {15'd0, computed_hidden} &&
                query_heads == {16'd0, computed_queries} &&
                (mode == 4 ?
                  {9'd0, computed_page_capacity} >= context_capacity :
                  (hidden_remainder == 0 && intermediate_remainder == 0 &&
                    (mode == 3 || computed_kv_width[2:0] == 0)));
              state <= IDLE;
            end
            COMMIT_RESPONSE: begin
              if (!cancel) begin
                cfg_done <= 1'b1;
                cfg_error <= !commit_valid;
                if (commit_valid) begin
                  active <= shadow;
                  successful_commits <= successful_commits+1'b1;
                end
                else write_fault <= 1'b0;
              end
              state <= SETTLE;
            end
            SETTLE: state <= IDLE;
            default: begin
              shadow_valid <= 1'b0;
              state <= IDLE;
            end
          endcase
        end
      end
    end
  endgenerate
endmodule
