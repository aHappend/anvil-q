`ifndef QUESTA
    `default_nettype none
`endif

`ifndef YOSYS
import ShellTypes::*;
`endif

module Role #(
    parameter int NUM_LAYERS        = 2,
    parameter int HIDDEN_SIZE       = 56,
    parameter int INTERMEDIATE_SIZE = 56,
    parameter int NUM_Q_HEADS       = 14,
    parameter int NUM_KV_HEADS      = 2,
    parameter int HEAD_DIM          = 4,
    parameter int GROUP_SIZE        = 56,
    parameter int VOCAB_SIZE        = 64,
    parameter int MAX_SEQ_LEN       = 8,
    parameter int P_INTMSI_W        = 11,
    parameter int P_INTMAX_W        = 12,
    parameter int P_INTAUX_W        = 64,
    parameter int P_BYTES_W         = 26,
    parameter int P_ADDR_W          = 64,
    parameter int P_DATA_W          = 256
) (
    input  wire                        pcie_refclk,
    input  wire                        pcie_pinrst_n,
    input  wire                        nic_refclk,
    input  wire                        tor_refclk,

    input  wire                        clk_100,
    input  wire                        rst_100,

    output wire [31:0]                 role_id_out,
    output wire [31:0]                 role_version_out,
    output wire [31:0]                 role_status_out,

    input  wire                        softreg_read_in,
    input  wire                        softreg_write_in,
    input  wire [15:0]                 softreg_addr_in,
    input  wire [63:0]                 softreg_wrdata_in,
    output reg  [63:0]                 softreg_rddata_out,
    output reg                         softreg_rdvalid_out,

    input  wire                        pcieA_clk,
    input  wire                        pcieA_rst,

    output wire                        pcieA_intreq_out,
    output wire [P_INTMSI_W-1:0]       pcieA_intmsi_out,
    input  wire                        pcieA_intack_in,
    input  wire [P_INTMAX_W-1:0]       pcieA_intmax_in,
    output wire [P_INTAUX_W-1:0]       pcieA_intaux_out,
    input  wire                        pcieA_intaux_read_in,

    output wire                        pcieA_wrreq_out,
    input  wire                        pcieA_wrack_in,
    output wire [P_BYTES_W-1:0]        pcieA_wrbytes_out,
    output wire [P_ADDR_W-1:0]         pcieA_wraddr_out,
    output wire [P_DATA_W-1:0]         pcieA_wrdata_out,
    input  wire                        pcieA_wrdata_rden_in,
    input  wire                        pcieA_wrdone_in,

    output wire                        pcieA_rdreq_out,
    input  wire                        pcieA_rdack_in,
    output wire [P_BYTES_W-1:0]        pcieA_rdbytes_out,
    output wire [P_ADDR_W-1:0]         pcieA_rdaddr_out,
    input  wire [P_DATA_W-1:0]         pcieA_rddata_in,
    input  wire                        pcieA_rddata_wren_in,
    output wire                        pcieA_rddata_afull_out,

    input  wire                        pcieB_clk,
    input  wire                        pcieB_rst,

    output wire                        pcieB_intreq_out,
    output wire [P_INTMSI_W-1:0]       pcieB_intmsi_out,
    input  wire                        pcieB_intack_in,
    input  wire [P_INTMAX_W-1:0]       pcieB_intmax_in,
    output wire [P_INTAUX_W-1:0]       pcieB_intaux_out,
    input  wire                        pcieB_intaux_read_in,

    output wire                        pcieB_wrreq_out,
    input  wire                        pcieB_wrack_in,
    output wire [P_BYTES_W-1:0]        pcieB_wrbytes_out,
    output wire [P_ADDR_W-1:0]         pcieB_wraddr_out,
    output wire [P_DATA_W-1:0]         pcieB_wrdata_out,
    input  wire                        pcieB_wrdata_rden_in,
    input  wire                        pcieB_wrdone_in,

    output wire                        pcieB_rdreq_out,
    input  wire                        pcieB_rdack_in,
    output wire [P_BYTES_W-1:0]        pcieB_rdbytes_out,
    output wire [P_ADDR_W-1:0]         pcieB_rdaddr_out,
    input  wire [P_DATA_W-1:0]         pcieB_rddata_in,
    input  wire                        pcieB_rddata_wren_in,
    output wire                        pcieB_rddata_afull_out
);

    assign pcieA_intreq_out       = 1'b0;
    assign pcieA_intmsi_out       = {P_INTMSI_W{1'b0}};
    assign pcieA_intaux_out       = {P_INTAUX_W{1'b0}};
    assign pcieA_wrreq_out        = 1'b0;
    assign pcieA_wrbytes_out      = {P_BYTES_W{1'b0}};
    assign pcieA_wraddr_out       = {P_ADDR_W{1'b0}};
    assign pcieA_wrdata_out       = {P_DATA_W{1'b0}};
    assign pcieA_rdreq_out        = 1'b0;
    assign pcieA_rdbytes_out      = {P_BYTES_W{1'b0}};
    assign pcieA_rdaddr_out       = {P_ADDR_W{1'b0}};
    assign pcieA_rddata_afull_out = 1'b0;

    assign pcieB_intreq_out       = 1'b0;
    assign pcieB_intmsi_out       = {P_INTMSI_W{1'b0}};
    assign pcieB_intaux_out       = {P_INTAUX_W{1'b0}};
    assign pcieB_wrreq_out        = 1'b0;
    assign pcieB_wrbytes_out      = {P_BYTES_W{1'b0}};
    assign pcieB_wraddr_out       = {P_ADDR_W{1'b0}};
    assign pcieB_wrdata_out       = {P_DATA_W{1'b0}};
    assign pcieB_rdreq_out        = 1'b0;
    assign pcieB_rdbytes_out      = {P_BYTES_W{1'b0}};
    assign pcieB_rdaddr_out       = {P_ADDR_W{1'b0}};
    assign pcieB_rddata_afull_out = 1'b0;

    localparam [63:0] MAGIC_ANVIL_Q1 = 64'h414E_5649_4C5F_5131; // "ANVIL_Q1"
    localparam [31:0] ROLE_ID        = 32'h0000_A151;
    localparam [31:0] ROLE_VERSION   = 32'h0002_0000; // v2.0 Dynamic 24-Layer Host-Streamed BRAM Windowing

    reg [3:0] soft_rst_cnt;
    wire      soft_rst_active = (soft_rst_cnt != 4'd0);
    wire      dut_rst_n       = (~rst_100) & (~soft_rst_active);

    // 25 MHz divided clock promoted to global clock tree
    reg [1:0] clk_div = 2'd0;
    always @(posedge clk_100) begin
        clk_div <= clk_div + 2'd1;
    end
    wire dut_clk = clk_div[1];

    // Handshake flags between clk_100 SoftReg and 25 MHz dut_clk domain
    reg        job_launch_req;
    reg        job_launch_ack;
    reg        clear_sticky_req;
    reg        clear_sticky_ack;
    reg        cmd_interactive_100;
    reg [13:0] host_bram_addr_100;
    reg        host_bram_we_100;
    reg [31:0] host_bram_wdata_100;
    reg [31:0] cmd_token_id_100;
    reg [31:0] cmd_token_pos_100;
    reg        cmd_new_seq_100;

    // DUT ports
    reg                token_valid;
    wire               token_ready;
    reg  [31:0]        token_id;
    reg  [31:0]        token_pos;
    reg                new_sequence;
    wire               logit_valid;
    wire               logit_ready = 1'b1;
    wire [31:0]        logit_index;
    wire signed [31:0] logit_data;
    wire               done;
    wire               error;

    wire               mem_req_valid;
    wire               mem_req_ready;
    wire               mem_req_write;
    wire [3:0]         mem_req_kind;
    wire [31:0]        mem_req_layer;
    wire [2:0]         mem_req_proj;
    wire [31:0]        mem_req_row;
    wire [31:0]        mem_req_col;
    wire [31:0]        mem_req_wdata;
    reg                mem_rsp_valid;
    wire               mem_rsp_ready;
    reg  [31:0]        mem_rsp_rdata;
    reg                mem_rsp_error;

    anvil_q1_top #(
        .NUM_LAYERS       (NUM_LAYERS),
        .HIDDEN_SIZE      (HIDDEN_SIZE),
        .INTERMEDIATE_SIZE(INTERMEDIATE_SIZE),
        .NUM_Q_HEADS      (NUM_Q_HEADS),
        .NUM_KV_HEADS     (NUM_KV_HEADS),
        .HEAD_DIM         (HEAD_DIM),
        .GROUP_SIZE       (GROUP_SIZE),
        .VOCAB_SIZE        (VOCAB_SIZE),
        .MAX_SEQ_LEN      (MAX_SEQ_LEN)
    ) u_anvil_q1_top (
        .clk           (dut_clk),
        .rst_n         (dut_rst_n),
        .token_valid   (token_valid),
        .token_ready   (token_ready),
        .token_id      (token_id),
        .token_pos     (token_pos),
        .new_sequence  (new_sequence),
        .logit_valid   (logit_valid),
        .logit_ready   (logit_ready),
        .logit_index   (logit_index),
        .logit_data    (logit_data),
        .done          (done),
        .error         (error),
        .mem_req_valid (mem_req_valid),
        .mem_req_ready (mem_req_ready),
        .mem_req_write (mem_req_write),
        .mem_req_kind  (mem_req_kind),
        .mem_req_layer (mem_req_layer),
        .mem_req_proj  (mem_req_proj),
        .mem_req_row   (mem_req_row),
        .mem_req_col   (mem_req_col),
        .mem_req_wdata (mem_req_wdata),
        .mem_rsp_valid (mem_rsp_valid),
        .mem_rsp_ready (mem_rsp_ready),
        .mem_rsp_rdata (mem_rsp_rdata),
        .mem_rsp_error (mem_rsp_error)
    );

    // Pure shift-add address mapping for 16384 x 32-bit M20K BRAM
    function automatic [13:0] mul56(input [13:0] x);
        mul56 = (x << 6) - (x << 3);
    endfunction
    function automatic [13:0] mul7(input [13:0] x);
        mul7 = (x << 3) - x;
    endfunction
    function automatic [13:0] mul3(input [13:0] x);
        mul3 = (x << 1) + x;
    endfunction

    reg [13:0] mapped_bram_addr;
    reg [13:0] lp7;
    reg [13:0] lp3;
    always @(*) begin
        lp7 = mul7({13'd0, mem_req_layer[0]}) + {11'd0, mem_req_proj};
        lp3 = mul3({13'd0, mem_req_layer[0]}) + {11'd0, mem_req_proj};
        case (mem_req_kind)
            4'd0:  mapped_bram_addr = 14'd0     + mul56(mem_req_row[13:0]) + mem_req_col[13:0];
            4'd1:  mapped_bram_addr = 14'd3584  + mul7(mul56(lp7) + mem_req_row[13:0]) + mem_req_col[13:0];
            4'd2:  mapped_bram_addr = 14'd9072  + mul7(lp7) + mem_req_col[13:0];
            4'd3:  mapped_bram_addr = 14'd9170  + mul56(lp7) + mem_req_col[13:0];
            4'd4:  mapped_bram_addr = 14'd9954  + mul56(lp3) + mem_req_col[13:0];
            4'd5:  mapped_bram_addr = 14'd10290 + mul56({13'd0, mem_req_layer[0]}) + mem_req_col[13:0];
            4'd6:  mapped_bram_addr = 14'd10402 + mul56({13'd0, mem_req_layer[0]}) + mem_req_col[13:0];
            4'd7:  mapped_bram_addr = 14'd10514 + mem_req_col[13:0];
            4'd11: mapped_bram_addr = 14'd10570 + (mem_req_row[13:0] << 2) + mem_req_col[13:0];
            4'd8:  mapped_bram_addr = 14'd10602 + mul56(mem_req_row[13:0]) + mem_req_col[13:0];
            4'd9:  mapped_bram_addr = 14'd11442 + (({10'd0, mem_req_layer[0], mem_req_row[2:0]}) << 3) + mem_req_col[13:0];
            4'd10: mapped_bram_addr = 14'd11570 + (({10'd0, mem_req_layer[0], mem_req_row[2:0]}) << 3) + mem_req_col[13:0];
            default: mapped_bram_addr = 14'd0;
        endcase
    end

    (* ramstyle = "M20K" *) reg [31:0] bram [0:16383];
    reg  [31:0] bram_rdata;

    initial begin
        $readmemh("official_bram.hex", bram);
    end

    reg mem_rd_stage;
    reg mem_wr_stage;
    assign mem_req_ready = (~mem_rsp_valid) & (~mem_rd_stage) & (~mem_wr_stage);

    wire dut_req_fire = dut_rst_n & mem_req_valid & mem_req_ready;
    wire [13:0] bram_addr  = mapped_bram_addr;
    wire        bram_we    = dut_req_fire & mem_req_write;
    wire [31:0] bram_wdata = mem_req_wdata;

    always @(posedge dut_clk) begin
        if (bram_we) begin
            bram[bram_addr] <= bram_wdata;
        end else if (host_bram_we_100 && !busy) begin
            bram[host_bram_addr_100] <= host_bram_wdata_100;
        end
        bram_rdata <= bram[bram_addr];
    end

    always @(posedge dut_clk) begin
        if (!dut_rst_n) begin
            mem_rd_stage  <= 1'b0;
            mem_wr_stage  <= 1'b0;
            mem_rsp_valid <= 1'b0;
            mem_rsp_rdata <= 32'd0;
            mem_rsp_error <= 1'b0;
        end else begin
            if (mem_rsp_valid && mem_rsp_ready) begin
                mem_rsp_valid <= 1'b0;
                mem_rsp_rdata <= 32'd0;
                mem_rsp_error <= 1'b0;
            end

            if (mem_rd_stage || mem_wr_stage) begin
                mem_rsp_valid <= 1'b1;
                mem_rsp_rdata <= mem_wr_stage ? 32'd0 : bram_rdata;
                mem_rsp_error <= 1'b0;
                mem_rd_stage  <= 1'b0;
                mem_wr_stage  <= 1'b0;
            end else if (dut_req_fire) begin
                mem_rd_stage <= ~mem_req_write;
                mem_wr_stage <= mem_req_write;
            end
        end
    end

    // Sequencer state machine on 25 MHz dut_clk
    reg [2:0]  seq_state;
    reg        seq_interactive;
    reg [2:0]  seq_idx;
    reg [2:0]  seq_total;
    reg        busy;
    reg        done_sticky;
    reg [3:0]  done_error_sticky;
    reg        emb_captured_valid;
    reg [7:0]  emb_count;
    reg [7:0]  last_preset_id;
    reg [31:0] total_jobs_done;
    reg [63:0] last_job_cycles;
    reg [31:0] job_mem_reads;
    reg [31:0] job_mem_writes;
    reg signed [31:0] captured_logits [0:63];
    reg signed [31:0] best_logit;
    reg [5:0]         best_token;
    reg [15:0]        gen_tokens [0:3];
    integer j;

    wire job_ready = (seq_state == 3'd0) && !busy;
    assign role_id_out      = ROLE_ID;
    assign role_version_out = ROLE_VERSION;
    assign role_status_out  = {16'd0, emb_count, done_error_sticky, emb_captured_valid, done_sticky, job_ready, busy};

    always @(posedge dut_clk) begin
        if (!dut_rst_n) begin
            seq_state          <= 3'd0;
            seq_interactive    <= 1'b0;
            seq_idx            <= 3'd0;
            seq_total          <= 3'd4;
            token_valid        <= 1'b0;
            token_id           <= 32'd0;
            token_pos          <= 32'd0;
            new_sequence       <= 1'b0;
            job_launch_ack     <= 1'b0;
            clear_sticky_ack   <= 1'b0;
            busy               <= 1'b0;
            done_sticky        <= 1'b0;
            done_error_sticky  <= 4'd0;
            emb_captured_valid <= 1'b0;
            emb_count          <= 8'd0;
            total_jobs_done    <= 32'd0;
            last_job_cycles    <= 64'd0;
            job_mem_reads      <= 32'd0;
            job_mem_writes     <= 32'd0;
            best_logit         <= 32'sh80000000;
            best_token         <= 6'd0;
            for (j = 0; j < 4; j = j + 1) gen_tokens[j] <= 16'd0;
            for (j = 0; j < 64; j = j + 1) captured_logits[j] <= 32'sd0;
        end else begin
            token_valid <= 1'b0;
            if (!job_launch_req) job_launch_ack <= 1'b0;
            if (!clear_sticky_req) begin
                clear_sticky_ack <= 1'b0;
            end else if (clear_sticky_req && !clear_sticky_ack) begin
                clear_sticky_ack   <= 1'b1;
                done_sticky        <= 1'b0;
                done_error_sticky  <= 4'd0;
                emb_captured_valid <= 1'b0;
            end

            if (busy) begin
                last_job_cycles <= last_job_cycles + 64'd1;
                if (dut_req_fire) begin
                    if (mem_req_write)
                        job_mem_writes <= job_mem_writes + 32'd1;
                    else
                        job_mem_reads  <= job_mem_reads + 32'd1;
                end
                if (logit_valid && logit_ready) begin
                    if (logit_index < 32'd64) begin
                        captured_logits[logit_index[5:0]] <= logit_data;
                        if (logit_index == 32'd0 || logit_data > best_logit) begin
                            best_logit <= logit_data;
                            best_token <= logit_index[5:0];
                        end
                    end
                    emb_count <= logit_index[7:0] + 8'd1;
                    if (logit_index == 32'd63) begin
                        emb_captured_valid <= 1'b1;
                    end
                end
            end

            case (seq_state)
                3'd0: begin
                    if (job_launch_req && !job_launch_ack && !busy) begin
                        job_launch_ack     <= 1'b1;
                        busy               <= 1'b1;
                        done_sticky        <= 1'b0;
                        done_error_sticky  <= 4'd0;
                        emb_captured_valid <= 1'b0;
                        emb_count          <= 8'd0;
                        last_job_cycles    <= 64'd0;
                        job_mem_reads      <= 32'd0;
                        job_mem_writes     <= 32'd0;
                        seq_interactive    <= cmd_interactive_100;
                        seq_idx            <= 3'd0;
                        seq_total          <= cmd_interactive_100 ? 3'd1 : 3'd4;
                        seq_state          <= 3'd1;
                    end
                end
                3'd1: begin
                    if (token_ready) begin
                        token_valid <= 1'b1;
                        best_logit  <= 32'sh80000000;
                        best_token  <= 6'd0;
                        if (seq_interactive) begin
                            token_id     <= cmd_token_id_100;
                            token_pos    <= cmd_token_pos_100;
                            new_sequence <= cmd_new_seq_100;
                        end else begin
                            case (seq_idx)
                                3'd0: begin token_id <= 32'd0;  token_pos <= 32'd0; new_sequence <= 1'b1; end
                                3'd1: begin token_id <= 32'd1;  token_pos <= 32'd1; new_sequence <= 1'b0; end
                                3'd2: begin token_id <= 32'd59; token_pos <= 32'd2; new_sequence <= 1'b0; end
                                default: begin token_id <= 32'd59; token_pos <= 32'd3; new_sequence <= 1'b0; end
                            endcase
                        end
                        seq_state <= 3'd2;
                    end
                end
                3'd2: begin
                    if (done) begin
                        if (error) done_error_sticky <= 4'd1;
                        seq_state <= 3'd3;
                    end
                end
                3'd3: begin
                    gen_tokens[seq_idx[1:0]] <= {10'd0, best_token};
                    if (seq_idx + 3'd1 < seq_total && done_error_sticky == 4'd0) begin
                        seq_idx   <= seq_idx + 3'd1;
                        seq_state <= 3'd1;
                    end else begin
                        busy            <= 1'b0;
                        done_sticky     <= 1'b1;
                        total_jobs_done <= total_jobs_done + 32'd1;
                        seq_state       <= 3'd0;
                    end
                end
                default: seq_state <= 3'd0;
            endcase
        end
    end

    always @(posedge clk_100) begin
        if (rst_100) begin
            soft_rst_cnt        <= 4'd0;
            job_launch_req      <= 1'b0;
            clear_sticky_req    <= 1'b0;
            cmd_interactive_100 <= 1'b0;
            cmd_token_id_100    <= 32'd0;
            cmd_token_pos_100   <= 32'd0;
            cmd_new_seq_100     <= 1'b1;
            last_preset_id      <= 8'hFE;
            softreg_rddata_out  <= 64'd0;
            softreg_rdvalid_out <= 1'b0;
            host_bram_we_100    <= 1'b0;
        end else begin
            softreg_rdvalid_out <= 1'b0;
            host_bram_we_100    <= 1'b0;

            if (soft_rst_cnt != 4'd0)
                soft_rst_cnt <= soft_rst_cnt - 4'd1;
            if (job_launch_req && job_launch_ack)
                job_launch_req <= 1'b0;
            if (clear_sticky_req && clear_sticky_ack)
                clear_sticky_req <= 1'b0;

            if (softreg_write_in) begin
                case (softreg_addr_in)
                    16'h0003: begin
                        if (softreg_wrdata_in[1]) begin
                            soft_rst_cnt     <= 4'd12;
                            job_launch_req   <= 1'b0;
                            clear_sticky_req <= 1'b0;
                        end else if (softreg_wrdata_in[2]) begin
                            clear_sticky_req <= 1'b1;
                        end else if (softreg_wrdata_in[9] && job_ready && !busy && !job_launch_req) begin
                            // Interactive single-token chat command!
                            // bit[9]=1, bit[63]=new_sequence, bits[39:32]=token_pos, bits[31:16]=token_id
                            cmd_interactive_100 <= 1'b1;
                            cmd_new_seq_100     <= softreg_wrdata_in[63];
                            cmd_token_pos_100   <= {24'd0, softreg_wrdata_in[39:32]};
                            cmd_token_id_100    <= {16'd0, softreg_wrdata_in[31:16]};
                            last_preset_id      <= softreg_wrdata_in[23:16];
                            job_launch_req      <= 1'b1;
                        end else if ((softreg_wrdata_in[0] || softreg_wrdata_in[8]) && job_ready && !busy && !job_launch_req) begin
                            cmd_interactive_100 <= 1'b0;
                            last_preset_id      <= 8'hFE;
                            job_launch_req      <= 1'b1;
                        end
                    end
                    16'h0004: begin
                        host_bram_addr_100 <= softreg_wrdata_in[13:0];
                    end
                    16'h0005: begin
                        host_bram_we_100    <= 1'b1;
                        host_bram_wdata_100 <= softreg_wrdata_in[31:0];
                        host_bram_addr_100  <= host_bram_addr_100 + 14'd1;
                    end
                    default: ;
                endcase
            end

            if (softreg_read_in) begin
                softreg_rdvalid_out <= 1'b1;
                if (softreg_addr_in >= 16'h0040 && softreg_addr_in < 16'h0080) begin
                    softreg_rddata_out <= {{32{captured_logits[softreg_addr_in[5:0]][31]}},
                                           captured_logits[softreg_addr_in[5:0]]};
                end else begin
                    case (softreg_addr_in)
                        16'h0000: softreg_rddata_out <= MAGIC_ANVIL_Q1;
                        16'h0001: softreg_rddata_out <= {ROLE_VERSION, ROLE_ID};
                        16'h0002: softreg_rddata_out <= {
                            total_jobs_done,
                            8'd0,
                            last_preset_id,
                            emb_count,
                            done_error_sticky,
                            emb_captured_valid,
                            done_sticky,
                            job_ready,
                            busy
                        };
                        16'h000B: softreg_rddata_out <= last_job_cycles;
                        16'h000C: softreg_rddata_out <= {job_mem_writes, job_mem_reads};
                        16'h000D: softreg_rddata_out <= {gen_tokens[3], gen_tokens[2], gen_tokens[1], gen_tokens[0]};
                        16'h000F: softreg_rddata_out <= {26'd0, best_token, best_logit[31:0]};
                        16'h0010: softreg_rddata_out <= {{32{captured_logits[0][31]}}, captured_logits[0]};
                        16'h0011: softreg_rddata_out <= {{32{captured_logits[1][31]}}, captured_logits[1]};
                        16'h0012: softreg_rddata_out <= {{32{captured_logits[2][31]}}, captured_logits[2]};
                        16'h0013: softreg_rddata_out <= {{32{captured_logits[3][31]}}, captured_logits[3]};
                        16'h0014: softreg_rddata_out <= {{32{captured_logits[4][31]}}, captured_logits[4]};
                        16'h0015: softreg_rddata_out <= {{32{captured_logits[5][31]}}, captured_logits[5]};
                        default:  softreg_rddata_out <= 64'd0;
                    endcase
                end
            end
        end
    end

endmodule

`default_nettype wire
