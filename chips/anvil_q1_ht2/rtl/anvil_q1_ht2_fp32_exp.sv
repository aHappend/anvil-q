module anvil_q1_ht2_fp32_exp (
  input wire clk, rst_n, enable, req_valid,
  output wire req_ready,
  input wire [31:0] req_data,
  output wire rsp_valid,
  input wire rsp_ready,
  output wire [31:0] rsp_data
);
  import anvil_q1_ht2_fp_pkg::*;
  localparam IDLE = 3'd0, MUL_SEND = 3'd1, MUL_WAIT = 3'd2,
             ADD_SEND = 3'd3, ADD_WAIT = 3'd4, SCALE = 3'd5, RESPONSE = 3'd6;
  localparam [31:0] INV_LN2 = 32'h3fb8aa3b, LN2_HI = 32'h3f317200,
                    LN2_LO = 32'h35bfbe8e;
  wire run_n;
  reg [2:0] state, phase;
  reg [3:0] degree;
  reg [31:0] x, n_float, reduced, first_remainder, polynomial, temporary, response;
  reg signed [10:0] n;
  reg [31:0] mul_a, mul_b, add_a, add_b;
  wire mul_valid, add_valid;
  wire [31:0] mul_data, add_data;
  wire [63:0] n_magnitude = shift_rne64(
    {40'b0, (|mul_data[30:23]), mul_data[22:0]}, 150-int'({1'b0, mul_data[30:23]}));
  wire signed [10:0] next_n =
    mul_data[31] ? -$signed(n_magnitude[10:0]) : $signed(n_magnitude[10:0]);
  wire [31:0] next_n_float = pack32(next_n[10], n_magnitude, 0);
  wire [63:0] scale_significand = {40'b0, (|polynomial[30:23]), polynomial[22:0]};
  wire signed [10:0] polynomial_scale = polynomial[30:23] == 0 ? -11'sd149 :
                              $signed({3'b0, polynomial[30:23]}) - 11'sd150;
  wire [31:0] scaled = pack32(polynomial[31], scale_significand, int'(polynomial_scale+n));

  function automatic [31:0] coefficient(input [3:0] index);
    begin
      case (index)
        0, 1: coefficient = 32'h3f800000;
        2: coefficient = 32'h3f000000;
        3: coefficient = 32'h3e2aaaab;
        4: coefficient = 32'h3d2aaaab;
        5: coefficient = 32'h3c088889;
        6: coefficient = 32'h3ab60b61;
        7: coefficient = 32'h39500d01;
        8: coefficient = 32'h37d00d01;
        9: coefficient = 32'h3638ef1d;
        10: coefficient = 32'h3493f27e;
        11: coefficient = 32'h32d7322b;
        12: coefficient = 32'h310f76c7;
        default: coefficient = FP32_QNAN;
      endcase
    end
  endfunction

  anvil_q1_ht2_reset_sync u_reset(clk, rst_n, run_n);
  always @* begin
    mul_a = 0;
    mul_b = 0;
    add_a = 0;
    add_b = 0;
    case (phase)
      0: begin mul_a = x; mul_b = INV_LN2; end
      1: begin mul_a = n_float; mul_b = LN2_HI; end
      2: begin add_a = x; add_b = {~temporary[31], temporary[30:0]}; end
      3: begin mul_a = n_float; mul_b = LN2_LO; end
      4: begin add_a = first_remainder; add_b = {~temporary[31], temporary[30:0]}; end
      5: begin mul_a = polynomial; mul_b = reduced; end
      6: begin add_a = temporary; add_b = coefficient(degree); end
      default: begin end
    endcase
  end
  anvil_q1_ht2_fp32_mul u_multiply (
    .clk(clk), .rst_n(run_n), .enable(enable),
    .in_valid(run_n && state == MUL_SEND), .in_a(mul_a), .in_b(mul_b),
    .out_valid(mul_valid), .out_data(mul_data)
  );
  anvil_q1_ht2_fp32_add u_add (
    .clk(clk), .rst_n(run_n), .enable(enable),
    .in_valid(run_n && state == ADD_SEND), .in_a(add_a), .in_b(add_b),
    .out_valid(add_valid), .out_data(add_data)
  );
  assign req_ready = run_n && enable && state == IDLE;
  assign rsp_valid = run_n && state == RESPONSE;
  assign rsp_data = rsp_valid ? response : 32'b0;

  always @(posedge clk or negedge run_n) begin
    if (!run_n) begin
      state <= IDLE;
      phase <= 0;
      degree <= 0;
      x <= 0;
      n_float <= 0;
      reduced <= 0;
      first_remainder <= 0;
      polynomial <= 0;
      temporary <= 0;
      response <= 0;
      n <= 0;
    end else if (state == RESPONSE) begin
      if (rsp_valid && rsp_ready) state <= IDLE;
    end else if (enable) case (state)
      IDLE: if (req_valid && req_ready) begin
        x <= req_data;
        phase <= 0;
        if (fp32_nan(req_data)) begin
          response <= FP32_QNAN;
          state <= RESPONSE;
        end else if (req_data[31] && req_data[30:0] >= 31'h42d00000) begin
          response <= 0;
          state <= RESPONSE;
        end else if (!req_data[31] && req_data[30:0] >= 31'h42b20000) begin
          response <= 32'h7f800000;
          state <= RESPONSE;
        end else state <= MUL_SEND;
      end
      MUL_SEND: state <= MUL_WAIT;
      MUL_WAIT: if (mul_valid) case (phase)
        0: begin
          n <= next_n;
          n_float <= next_n_float;
          phase <= 1;
          state <= MUL_SEND;
        end
        1: begin
          temporary <= mul_data;
          phase <= 2;
          state <= ADD_SEND;
        end
        3: begin
          temporary <= mul_data;
          phase <= 4;
          state <= ADD_SEND;
        end
        5: begin
          temporary <= mul_data;
          phase <= 6;
          state <= ADD_SEND;
        end
        default: begin
          response <= FP32_QNAN;
          state <= RESPONSE;
        end
      endcase
      ADD_SEND: state <= ADD_WAIT;
      ADD_WAIT: if (add_valid) case (phase)
        2: begin
          first_remainder <= add_data;
          phase <= 3;
          state <= MUL_SEND;
        end
        4: begin
          reduced <= add_data;
          polynomial <= coefficient(12);
          degree <= 11;
          phase <= 5;
          state <= MUL_SEND;
        end
        6: begin
          polynomial <= add_data;
          if (degree == 0) state <= SCALE;
          else begin
            degree <= degree - 1'b1;
            phase <= 5;
            state <= MUL_SEND;
          end
        end
        default: begin
          response <= FP32_QNAN;
          state <= RESPONSE;
        end
      endcase
      SCALE: begin
        response <= scaled;
        state <= RESPONSE;
      end
      default: begin
        response <= FP32_QNAN;
        state <= RESPONSE;
      end
    endcase
  end
endmodule
