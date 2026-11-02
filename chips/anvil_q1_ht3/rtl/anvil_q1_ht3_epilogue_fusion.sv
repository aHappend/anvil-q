module anvil_q1_ht3_epilogue_fusion #(
  parameter MAX_VECTOR = 4864,
  parameter HEAD_DIM = 64
) (
  input wire clk, rst_n, abort_error, cmd_valid,
  output wire cmd_ready,
  input wire [2:0] cmd_op,
  input wire [3:0] cmd_slots,
  input wire cmd_fp16,
  input wire [12:0] cmd_length,
  input wire [127:0] cmd_positions,
  input wire in_valid,
  input wire [127:0] in_data, in_aux,
  input wire [15:0] in_gamma,
  output wire in_ready,
  output wire out_valid,
  output wire [31:0] out_index,
  output wire [127:0] out_data,
  output wire [63:0] out_encoded,
  output wire [3:0] out_slots,
  output wire busy, done, error,
  input wire out_ready
);
  import anvil_q1_ht3_fp_pkg::*;
  localparam LEGAL = MAX_VECTOR >= 1 && MAX_VECTOR <= 4864 &&
    HEAD_DIM >= 2 && HEAD_DIM <= 64 && (HEAD_DIM & 1) == 0;
  initial begin
    if (!LEGAL) $fatal(1, "PARAMETER ERROR: HT3 epilogue geometry");
  end
  generate if (!LEGAL) begin: g_invalid
    assign cmd_ready = 0;
    assign in_ready = 0;
    assign out_valid = 0;
    assign out_index = 0;
    assign out_data = 0;
    assign out_encoded = 0;
    assign out_slots = 0;
    assign busy = 0;
    assign done = 0;
    assign error = 0;
  end else begin: g_legal
    localparam IDLE = 5'd0, VALIDATE = 5'd1, ACQUIRE = 5'd2,
      SETUP = 5'd3, READ_X = 5'd4, LOAD_X = 5'd5,
      READ_PARTNER = 5'd6, LOAD_PARTNER = 5'd7,
      ISSUE = 5'd8, WAIT_ARITH = 5'd9, WRITE_X = 5'd10,
      WRITE_LOW = 5'd11, WRITE_HIGH = 5'd12,
      OUTPUT_READ = 5'd13, OUTPUT_LOAD = 5'd14,
      OUTPUT_HOLD = 5'd15, FAIL = 5'd16;
    localparam PASS_RESIDUAL = 3'd0, PASS_SUM = 3'd1,
      PASS_NORMALIZE = 3'd2, PASS_SWIGLU = 3'd3, PASS_ROPE = 3'd4;
    localparam RES_ADD = 5'd0, SUM_SQUARE = 5'd1, SUM_ADD = 5'd2,
      MEAN_DIV = 5'd3, EPS_ADD = 5'd4, ROOT = 5'd5, INVERSE = 5'd6,
      NORM_MUL = 5'd7, GAMMA_MUL = 5'd8, SILU_EXP = 5'd9,
      SILU_DEN = 5'd10, SILU_NUM = 5'd11, SILU_DIV = 5'd12,
      SWIGLU_MUL = 5'd13, ROPE_TRIG = 5'd14, ROPE_AC = 5'd15,
      ROPE_BS = 5'd16, ROPE_LOW = 5'd17, ROPE_AS = 5'd18,
      ROPE_BC = 5'd19, ROPE_HIGH = 5'd20;
    localparam KIND_ADD = 3'd0, KIND_MUL = 3'd1, KIND_DIV = 3'd2,
      KIND_SQRT = 3'd3, KIND_EXP = 3'd4, KIND_TRIG = 3'd5;
    wire run_n;
    reg [4:0] state, phase;
    reg [2:0] op_q, pass;
    reg [3:0] slots_q;
    reg fp16_q, annul, done_q, error_q;
    reg [12:0] length_q, index_q, validation_remaining;
    reg [4:0] pair_q;
    reg [127:0] positions_q;
    reg [127:0] x_q, aux_q, partner_q, temporary, sums, inverse;
    reg [127:0] exponential, denominator, numerator, sine, cosine;
    reg [127:0] low_result, write_data;
    reg [31:0] gamma_q, length_float;
    reg [64:0] phase_q [0:3];
    reg [127:0] output_q;
    reg [63:0] encoded_q;
    (* ramstyle = "M20K", nomem2reg *) reg [127:0] data_mem [0:MAX_VECTOR-1];
    (* ramstyle = "M20K", nomem2reg *) reg [127:0] aux_mem [0:MAX_VECTOR-1];
    (* ramstyle = "M20K", nomem2reg *) reg [15:0] gamma_mem [0:MAX_VECTOR-1];
    reg [127:0] data_read, aux_read;
    reg [15:0] gamma_read;
    reg [12:0] read_address, write_address;
    reg memory_write;
    reg [127:0] memory_data;
    reg [2:0] kind;
    reg [127:0] operand_a, operand_b;
    wire [127:0] add_data, mul_data, div_data, exp_data, trig_sin, trig_cos;
    wire [3:0] add_valid, mul_valid, div_valid, div_ready;
    wire [3:0] exp_valid, trig_valid, trig_error;
    reg [127:0] arithmetic_data;
    reg arithmetic_done, arithmetic_ready, arithmetic_error;
    reg input_error, output_error, position_error;
    reg [127:0] masked_input, masked_aux;
    reg [63:0] narrowed_output;
    wire uses_norm = op_q == 1 || op_q == 5 || op_q == 6;
    wire uses_aux = op_q == 3 || op_q == 4 || op_q == 6;
    wire uses_rope = op_q == 2 || op_q == 5;
    wire [31:0] expanded_gamma = expand16(gamma_read, fp16_q);
    wire [31:0] next_length_float = pack32(1'b0, {51'b0, cmd_length}, 0);
    wire [56:0] frequency;
    wire issue = run_n && state == ISSUE && !annul && !abort_error &&
      arithmetic_ready;
    integer k;

    anvil_q1_ht3_reset_sync u_reset(clk, rst_n, run_n);
    anvil_q1_ht3_rope_frequency #(.HEAD_DIM(HEAD_DIM)) u_frequency (
      .rst_n(rst_n), .index(pair_q), .frequency(frequency)
    );
    assign cmd_ready = run_n && state == IDLE && !abort_error;
    assign in_ready = run_n && state == ACQUIRE && !annul && !abort_error;
    assign out_valid = run_n && state == OUTPUT_HOLD;
    assign out_index = out_valid ? {19'b0, index_q} : 32'b0;
    assign out_data = out_valid ? output_q : 128'b0;
    assign out_encoded = out_valid ? encoded_q : 64'b0;
    assign out_slots = out_valid ? slots_q : 4'b0;
    assign busy = run_n && state != IDLE;
    assign done = run_n && done_q;
    assign error = run_n && error_q;

    always @* begin
      input_error = 0;
      output_error = 0;
      position_error = 0;
      masked_input = 0;
      masked_aux = 0;
      narrowed_output = 0;
      for (k = 0; k < 4; k = k + 1) begin
        if (slots_q[k]) begin
          masked_input[32*k+:32] = in_data[32*k+:32];
          masked_aux[32*k+:32] = in_aux[32*k+:32];
          if (fp32_nonfinite(in_data[32*k+:32]) ||
              (uses_aux && fp32_nonfinite(in_aux[32*k+:32])))
            input_error = 1;
          if (positions_q[32*k+:32] >= 32768) position_error = 1;
          narrowed_output[16*k+:16] = narrow32(data_read[32*k+:32], fp16_q);
          if (fp32_nonfinite(data_read[32*k+:32]) ||
              fp32_nonfinite(expand16(narrowed_output[16*k+:16], fp16_q)))
            output_error = 1;
        end
      end
      if (uses_norm && fp32_nonfinite(expand16(in_gamma, fp16_q)))
        input_error = 1;
    end

    always @* begin
      read_address = index_q;
      write_address = index_q;
      memory_write = 0;
      memory_data = write_data;
      if (state == READ_PARTNER || state == LOAD_PARTNER ||
          state == WRITE_HIGH) begin
        read_address = index_q + (HEAD_DIM >> 1);
        write_address = index_q + (HEAD_DIM >> 1);
      end
      if (run_n) begin
        if (state == ACQUIRE && in_valid && in_ready && !input_error) begin
          memory_write = 1;
          memory_data = masked_input;
        end
        if (state == WRITE_X || state == WRITE_HIGH) memory_write = 1;
        if (state == WRITE_LOW) begin
          memory_write = 1;
          memory_data = low_result;
        end
      end
    end
    always @(posedge clk) begin
      if (memory_write) data_mem[write_address] <= memory_data;
      if (run_n && state == ACQUIRE && in_valid && in_ready && !input_error) begin
        aux_mem[index_q] <= masked_aux;
        gamma_mem[index_q] <= in_gamma;
      end
      data_read <= data_mem[read_address];
      aux_read <= aux_mem[read_address];
      gamma_read <= gamma_mem[read_address];
    end

    always @* begin
      kind = KIND_MUL;
      operand_a = x_q;
      operand_b = temporary;
      case (phase)
        RES_ADD: begin kind = KIND_ADD; operand_b = aux_q; end
        SUM_SQUARE: operand_b = x_q;
        SUM_ADD: begin kind = KIND_ADD; operand_a = sums; end
        MEAN_DIV: begin
          kind = KIND_DIV;
          operand_a = sums;
          operand_b = {4{length_float}};
        end
        EPS_ADD: begin
          kind = KIND_ADD;
          operand_a = temporary;
          operand_b = {4{32'h358637bd}};
        end
        ROOT: begin kind = KIND_SQRT; operand_a = temporary; end
        INVERSE: begin
          kind = KIND_DIV;
          operand_a = {4{32'h3f800000}};
          operand_b = temporary;
        end
        NORM_MUL: operand_b = inverse;
        GAMMA_MUL: begin operand_a = temporary; operand_b = {4{gamma_q}}; end
        SILU_EXP: begin
          kind = KIND_EXP;
          for (integer s = 0; s < 4; s = s + 1)
            operand_a[32*s+:32] = {1'b1, x_q[32*s+:31]};
        end
        SILU_DEN: begin
          kind = KIND_ADD;
          operand_a = {4{32'h3f800000}};
          operand_b = exponential;
        end
        SILU_NUM: begin
          for (integer s = 0; s < 4; s = s + 1)
            operand_b[32*s+:32] = x_q[32*s+31] ?
              exponential[32*s+:32] : 32'h3f800000;
        end
        SILU_DIV: begin
          kind = KIND_DIV;
          operand_a = numerator;
          operand_b = denominator;
        end
        SWIGLU_MUL: begin operand_a = temporary; operand_b = aux_q; end
        ROPE_TRIG: kind = KIND_TRIG;
        ROPE_AC: operand_b = cosine;
        ROPE_BS: begin operand_a = partner_q; operand_b = sine; end
        ROPE_LOW: begin
          kind = KIND_ADD;
          operand_a = numerator;
          for (integer s = 0; s < 4; s = s + 1)
            operand_b[32*s+:32] = {~temporary[32*s+31], temporary[32*s+:31]};
        end
        ROPE_AS: operand_b = sine;
        ROPE_BC: begin operand_a = partner_q; operand_b = cosine; end
        ROPE_HIGH: begin kind = KIND_ADD; operand_a = numerator; end
        default: begin end
      endcase
      arithmetic_data = 0;
      arithmetic_ready = 1;
      arithmetic_done = 1;
      arithmetic_error = 0;
      for (integer s = 0; s < 4; s = s + 1) begin
        if (slots_q[s]) begin
          case (kind)
            KIND_ADD: begin
              arithmetic_data[32*s+:32] = add_data[32*s+:32];
              arithmetic_done = arithmetic_done && add_valid[s];
            end
            KIND_MUL: begin
              arithmetic_data[32*s+:32] = mul_data[32*s+:32];
              arithmetic_done = arithmetic_done && mul_valid[s];
            end
            KIND_DIV, KIND_SQRT: begin
              arithmetic_data[32*s+:32] = div_data[32*s+:32];
              arithmetic_done = arithmetic_done && div_valid[s];
              arithmetic_ready = arithmetic_ready && div_ready[s];
            end
            KIND_EXP: begin
              arithmetic_data[32*s+:32] = exp_data[32*s+:32];
              arithmetic_done = arithmetic_done && exp_valid[s];
            end
            KIND_TRIG: begin
              arithmetic_data[32*s+:32] = trig_sin[32*s+:32];
              arithmetic_done = arithmetic_done && trig_valid[s];
              arithmetic_error = arithmetic_error || trig_error[s] ||
                fp32_nonfinite(trig_cos[32*s+:32]);
            end
            default: arithmetic_error = 1;
          endcase
          if (fp32_nonfinite(arithmetic_data[32*s+:32])) arithmetic_error = 1;
        end
      end
    end

    for (genvar s = 0; s < 4; s = s + 1) begin: g_slot
      wire [88:0] angle_product = positions_q[32*s+:32] * frequency;
      anvil_q1_ht3_fp32_add u_add (
        .clk(clk), .rst_n(rst_n), .enable(1'b1),
        .in_valid(issue && slots_q[s] && kind == KIND_ADD),
        .in_a(operand_a[32*s+:32]), .in_b(operand_b[32*s+:32]),
        .out_valid(add_valid[s]), .out_data(add_data[32*s+:32])
      );
      anvil_q1_ht3_fp32_mul u_mul (
        .clk(clk), .rst_n(rst_n), .enable(1'b1),
        .in_valid(issue && slots_q[s] && kind == KIND_MUL),
        .in_a(operand_a[32*s+:32]), .in_b(operand_b[32*s+:32]),
        .out_valid(mul_valid[s]), .out_data(mul_data[32*s+:32])
      );
      anvil_q1_ht3_fp32_divsqrt u_divsqrt (
        .clk(clk), .rst_n(rst_n), .enable(1'b1),
        .req_valid(issue && slots_q[s] && (kind == KIND_DIV || kind == KIND_SQRT)),
        .req_ready(div_ready[s]), .req_sqrt(kind == KIND_SQRT),
        .req_a(operand_a[32*s+:32]), .req_b(operand_b[32*s+:32]),
        .rsp_valid(div_valid[s]), .rsp_ready(state == WAIT_ARITH),
        .rsp_data(div_data[32*s+:32])
      );
      anvil_q1_ht3_fp32_exp u_exp (
        .clk(clk), .rst_n(rst_n), .enable(1'b1),
        .in_valid(issue && slots_q[s] && kind == KIND_EXP),
        .in_data(operand_a[32*s+:32]), .out_valid(exp_valid[s]),
        .out_data(exp_data[32*s+:32])
      );
      anvil_q1_ht3_sincos_phase u_sincos (
        .clk(clk), .rst_n(rst_n), .enable(1'b1),
        .in_valid(issue && slots_q[s] && kind == KIND_TRIG),
        .in_phase(phase_q[s]), .in_negative(1'b0),
        .in_zero(positions_q[32*s+:32] == 0), .in_error(1'b0),
        .out_valid(trig_valid[s]), .out_sin(trig_sin[32*s+:32]),
        .out_cos(trig_cos[32*s+:32]), .out_error(trig_error[s])
      );
      always @(posedge clk or negedge rst_n) begin
        if (!rst_n) phase_q[s] <= 0;
        else if (run_n && state == LOAD_PARTNER)
          phase_q[s] <= angle_product[72:8];
      end
    end

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        state <= IDLE;
        phase <= 0;
        op_q <= 0;
        pass <= 0;
        slots_q <= 0;
        fp16_q <= 0;
        annul <= 0;
        done_q <= 0;
        error_q <= 0;
        length_q <= 0;
        index_q <= 0;
        validation_remaining <= 0;
        pair_q <= 0;
        positions_q <= 0;
        x_q <= 0;
        aux_q <= 0;
        partner_q <= 0;
        temporary <= 0;
        sums <= 0;
        inverse <= 0;
        exponential <= 0;
        denominator <= 0;
        numerator <= 0;
        sine <= 0;
        cosine <= 0;
        low_result <= 0;
        write_data <= 0;
        gamma_q <= 0;
        length_float <= 0;
        output_q <= 0;
        encoded_q <= 0;
      end else if (run_n) begin
        done_q <= 0;
        if (state != IDLE && abort_error) annul <= 1;
        case (state)
          IDLE: if (cmd_valid && cmd_ready) begin
            op_q <= cmd_op;
            slots_q <= cmd_slots;
            fp16_q <= cmd_fp16;
            length_q <= cmd_length;
            positions_q <= cmd_positions;
            length_float <= next_length_float;
            validation_remaining <= cmd_length;
            index_q <= 0;
            pair_q <= 0;
            sums <= 0;
            annul <= 0;
            error_q <= 0;
            if (cmd_op == 7 || cmd_slots == 0 || cmd_length == 0 ||
                cmd_length > MAX_VECTOR) state <= FAIL;
            else state <= VALIDATE;
          end
          VALIDATE: begin
            if (uses_rope && position_error) state <= FAIL;
            else if (!uses_rope || validation_remaining == 0) state <= ACQUIRE;
            else if (validation_remaining < HEAD_DIM) state <= FAIL;
            else validation_remaining <= validation_remaining - HEAD_DIM;
          end
          ACQUIRE: if (in_valid && in_ready) begin
            if (input_error) state <= FAIL;
            else if (index_q == length_q-1'b1) begin
              index_q <= 0;
              state <= SETUP;
            end else index_q <= index_q + 1'b1;
          end
          SETUP: begin
            if (op_q == 0) state <= OUTPUT_READ;
            else begin
              state <= READ_X;
              if (op_q == 4 || op_q == 6) pass <= PASS_RESIDUAL;
              else if (uses_norm) pass <= PASS_SUM;
              else if (op_q == 3) pass <= PASS_SWIGLU;
              else pass <= PASS_ROPE;
            end
          end
          READ_X: state <= LOAD_X;
          LOAD_X: begin
            x_q <= data_read;
            aux_q <= aux_read;
            gamma_q <= expanded_gamma;
            state <= ISSUE;
            case (pass)
              PASS_RESIDUAL: phase <= RES_ADD;
              PASS_SUM: phase <= SUM_SQUARE;
              PASS_NORMALIZE: phase <= NORM_MUL;
              PASS_SWIGLU: phase <= SILU_EXP;
              PASS_ROPE: state <= READ_PARTNER;
              default: state <= FAIL;
            endcase
          end
          READ_PARTNER: state <= LOAD_PARTNER;
          LOAD_PARTNER: begin
            partner_q <= data_read;
            phase <= ROPE_TRIG;
            state <= ISSUE;
          end
          ISSUE: if (issue) state <= WAIT_ARITH;
          WAIT_ARITH: if (arithmetic_done) begin
            temporary <= arithmetic_data;
            state <= ISSUE;
            if (arithmetic_error || annul || abort_error) state <= FAIL;
            else case (phase)
              RES_ADD, GAMMA_MUL, SWIGLU_MUL: begin
                write_data <= arithmetic_data;
                state <= WRITE_X;
              end
              SUM_SQUARE: phase <= SUM_ADD;
              SUM_ADD: begin
                sums <= arithmetic_data;
                if (index_q == length_q-1'b1) phase <= MEAN_DIV;
                else begin index_q <= index_q + 1'b1; state <= READ_X; end
              end
              MEAN_DIV: phase <= EPS_ADD;
              EPS_ADD: phase <= ROOT;
              ROOT: phase <= INVERSE;
              INVERSE: begin
                inverse <= arithmetic_data;
                index_q <= 0;
                pass <= PASS_NORMALIZE;
                state <= READ_X;
              end
              NORM_MUL: phase <= GAMMA_MUL;
              SILU_EXP: begin exponential <= arithmetic_data; phase <= SILU_DEN; end
              SILU_DEN: begin denominator <= arithmetic_data; phase <= SILU_NUM; end
              SILU_NUM: begin numerator <= arithmetic_data; phase <= SILU_DIV; end
              SILU_DIV: phase <= SWIGLU_MUL;
              ROPE_TRIG: begin
                sine <= arithmetic_data;
                cosine <= trig_cos;
                phase <= ROPE_AC;
              end
              ROPE_AC: begin numerator <= arithmetic_data; phase <= ROPE_BS; end
              ROPE_BS: phase <= ROPE_LOW;
              ROPE_LOW: begin low_result <= arithmetic_data; phase <= ROPE_AS; end
              ROPE_AS: begin numerator <= arithmetic_data; phase <= ROPE_BC; end
              ROPE_BC: phase <= ROPE_HIGH;
              ROPE_HIGH: begin write_data <= arithmetic_data; state <= WRITE_LOW; end
              default: state <= FAIL;
            endcase
          end
          WRITE_X: begin
            state <= READ_X;
            if (index_q != length_q-1'b1) index_q <= index_q + 1'b1;
            else begin
              index_q <= 0;
              if (pass == PASS_RESIDUAL && op_q == 6) begin
                pass <= PASS_SUM;
                sums <= 0;
              end else if (pass == PASS_NORMALIZE && op_q == 5) begin
                pass <= PASS_ROPE;
                pair_q <= 0;
              end else state <= OUTPUT_READ;
            end
          end
          WRITE_LOW: state <= WRITE_HIGH;
          WRITE_HIGH: begin
            if (index_q + (HEAD_DIM >> 1) + 1 >= length_q) begin
              index_q <= 0;
              state <= OUTPUT_READ;
            end else begin
              if (pair_q == (HEAD_DIM >> 1)-1) begin
                pair_q <= 0;
                index_q <= index_q + (HEAD_DIM >> 1) + 1;
              end else begin
                pair_q <= pair_q + 1'b1;
                index_q <= index_q + 1'b1;
              end
              state <= READ_X;
            end
          end
          OUTPUT_READ: state <= OUTPUT_LOAD;
          OUTPUT_LOAD: begin
            if (output_error) state <= FAIL;
            else begin
              output_q <= data_read;
              encoded_q <= narrowed_output;
              state <= OUTPUT_HOLD;
            end
          end
          OUTPUT_HOLD: if (out_ready) begin
            if (annul || abort_error) state <= FAIL;
            else if (index_q == length_q-1'b1) begin
              done_q <= 1;
              state <= IDLE;
            end else begin
              index_q <= index_q + 1'b1;
              state <= OUTPUT_READ;
            end
          end
          FAIL: begin
            done_q <= 1;
            error_q <= 1;
            state <= IDLE;
          end
          default: state <= FAIL;
        endcase
        if ((annul || abort_error) && state != IDLE &&
            state != WAIT_ARITH && state != OUTPUT_HOLD && state != FAIL)
          state <= FAIL;
      end
    end
  end endgenerate
endmodule
