module anvil_q1_ht_descriptors #(
  parameter NUM_LAYERS = 24, HIDDEN_SIZE = 896, INTERMEDIATE_SIZE = 4864,
  parameter NUM_KV_HEADS = 2, HEAD_DIM = 64, GROUP_SIZE = 128,
  parameter VOCAB_SIZE = 151936, MAX_SEQ_LEN = 32768
) (
  input wire clk, rst_n,
  input wire csr_valid, csr_write,
  input wire [15:0] csr_address,
  input wire [31:0] csr_wdata,
  output wire csr_ready, csr_rsp_valid,
  input wire csr_rsp_ready,
  output wire [31:0] csr_rdata,
  output wire csr_error,
  input wire engine_busy, load_busy, load_failed, emif_initialized,
  input wire fault_event, image_modified, engine_ready,
  input wire [63:0] token_cycles, read_beats,
  output wire initialized, image_valid, storage_bf16, sticky_error,
  output wire clear_load_error, configuration_busy,
  input wire lookup_valid,
  output wire lookup_ready,
  input wire [31:0] lookup_index,
  output wire lookup_rsp_valid,
  input wire lookup_rsp_ready,
  output wire [32:0] lookup_base,
  output wire [31:0] lookup_length,
  output wire lookup_error
);
  localparam SAFE_GROUP = GROUP_SIZE > 0 ? GROUP_SIZE : 1;
  localparam KV_WIDTH = NUM_KV_HEADS*HEAD_DIM;
  localparam SCRATCH_WIDTH = HIDDEN_SIZE > INTERMEDIATE_SIZE ? HIDDEN_SIZE : INTERMEDIATE_SIZE;
  localparam GROUPS_H = HIDDEN_SIZE / SAFE_GROUP;
  localparam GROUPS_I = INTERMEDIATE_SIZE / SAFE_GROUP;
  localparam LEGAL = NUM_LAYERS >= 1 && NUM_LAYERS <= 24 &&
      HIDDEN_SIZE >= 8 && HIDDEN_SIZE <= 896 && (HIDDEN_SIZE & 7) == 0 &&
      INTERMEDIATE_SIZE >= 8 && INTERMEDIATE_SIZE <= 4864 && (INTERMEDIATE_SIZE & 7) == 0 &&
      NUM_KV_HEADS >= 1 && NUM_KV_HEADS <= 2 && HEAD_DIM >= 2 && HEAD_DIM <= 64 &&
      (HEAD_DIM & 1) == 0 && (KV_WIDTH & 7) == 0 &&
      GROUP_SIZE >= 1 && (HIDDEN_SIZE % SAFE_GROUP) == 0 &&
      (INTERMEDIATE_SIZE % SAFE_GROUP) == 0 &&
      VOCAB_SIZE >= 1 && VOCAB_SIZE <= 151936 && MAX_SEQ_LEN >= 1 && MAX_SEQ_LEN <= 32768;
  generate if (LEGAL) begin : g_legal
    localparam COUNT = NUM_LAYERS*96;
    localparam INDEX_BITS = COUNT > 1 ? $clog2(COUNT) : 1;
    localparam INITIALIZE = 4'd0, IDLE = 4'd1, RESPONSE = 4'd2,
               INSTALL_READ = 4'd3, INSTALL_CHECK = 4'd4,
               INSTALL_WRITE = 4'd5, COMMIT_READ = 4'd6, COMMIT_CHECK = 4'd7,
               CSR_DELAY = 4'd8;
    // Entry: {valid, layer[4:0], kind[3:0], proj[2:0], base[32:0], length[31:0]}.
    (* ramstyle = "M20K", ram_style = "block" *) reg [77:0] descriptors [0:COUNT-1];
    reg [3:0] state;
    reg init_done, committed, bf16, fault, clear_load, previous_load_failed;
    reg [31:0] selected_index;
    reg [31:0] stage_kind, stage_layer, stage_proj, stage_base_low, stage_base_high, stage_length;
    reg [INDEX_BITS-1:0] scan_index;
    reg [4:0] scan_layer;
    reg [3:0] scan_kind;
    reg [2:0] scan_proj;
    reg [77:0] scan_entry;
    reg [32:0] candidate_base;
    reg [33:0] candidate_end;
    reg pending_clear;
    reg [31:0] response_data;
    reg [31:0] token_high_snapshot, read_high_snapshot;
    reg token_snapshot_valid, read_snapshot_valid;
    reg response_error;
    reg lookup_pending, lookup_fault;
    reg [77:0] lookup_entry;
    wire busy = engine_busy || load_busy;
    wire [11:0] stage_index = ({7'b0, stage_layer[4:0]} << 6) +
                              ({7'b0, stage_layer[4:0]} << 5) +
                              ({8'b0, stage_kind[3:0]} << 3) +
                              {9'b0, stage_proj[2:0]};
    wire [32:0] stage_base = {stage_base_high[0], stage_base_low};
    wire [33:0] stage_end = {1'b0, stage_base} + {2'b0, stage_length};
    wire [33:0] scan_end = {1'b0, scan_entry[64:32]} + {2'b0, scan_entry[31:0]};
    wire [31:0] install_length = tensor_length(stage_kind, stage_layer, stage_proj, bf16);
    wire [31:0] required_length = tensor_length({28'b0, scan_kind},
                                                {27'b0, scan_layer},
                                                {29'b0, scan_proj}, bf16);
    wire stage_identity_legal = tensor_identity(stage_kind, stage_layer, stage_proj);
    wire readonly_address = csr_address == 16'h0000 || csr_address == 16'h0004 ||
                            (csr_address >= 16'h0030 && csr_address <= 16'h003c);
    wire mutation = csr_write && !readonly_address;

    function automatic tensor_identity(
      input [31:0] kind, input [31:0] tensor_layer, input [31:0] proj
    );
      begin
        tensor_identity = 0;
        if (tensor_layer < NUM_LAYERS) case (kind)
          0, 7, 8, 11: tensor_identity = tensor_layer == 0 && proj == 0;
          1, 2, 3: tensor_identity = proj < 7;
          4: tensor_identity = proj < 3;
          5, 6, 9, 10: tensor_identity = proj == 0;
          default: tensor_identity = 0;
        endcase
      end
    endfunction

    function automatic [31:0] tensor_length(
      input [31:0] kind, input [31:0] tensor_layer, input [31:0] proj,
      input mode_bf16
    );
      reg [31:0] bytes;
      begin
        bytes = 0;
        if (tensor_identity(kind, tensor_layer, proj)) case (kind)
          0: bytes = VOCAB_SIZE*HIDDEN_SIZE*2;
          1: case (proj)
            1, 2: bytes = mode_bf16 ? HIDDEN_SIZE*KV_WIDTH*2 : HIDDEN_SIZE*(KV_WIDTH >> 3)*4;
            4, 5: bytes = mode_bf16 ? HIDDEN_SIZE*INTERMEDIATE_SIZE*2 :
                                    HIDDEN_SIZE*(INTERMEDIATE_SIZE >> 3)*4;
            6: bytes = mode_bf16 ? INTERMEDIATE_SIZE*HIDDEN_SIZE*2 :
                                 INTERMEDIATE_SIZE*(HIDDEN_SIZE >> 3)*4;
            default: bytes = mode_bf16 ? HIDDEN_SIZE*HIDDEN_SIZE*2 :
                                       HIDDEN_SIZE*(HIDDEN_SIZE >> 3)*4;
          endcase
          2: if (!mode_bf16) case (proj)
            1, 2: bytes = GROUPS_H*(KV_WIDTH >> 3)*4;
            4, 5: bytes = GROUPS_H*(INTERMEDIATE_SIZE >> 3)*4;
            6: bytes = GROUPS_I*(HIDDEN_SIZE >> 3)*4;
            default: bytes = GROUPS_H*(HIDDEN_SIZE >> 3)*4;
          endcase
          3: if (!mode_bf16) case (proj)
            1, 2: bytes = GROUPS_H*KV_WIDTH*2;
            4, 5: bytes = GROUPS_H*INTERMEDIATE_SIZE*2;
            6: bytes = GROUPS_I*HIDDEN_SIZE*2;
            default: bytes = GROUPS_H*HIDDEN_SIZE*2;
          endcase
          4: bytes = (proj == 1 || proj == 2) ? KV_WIDTH*2 : HIDDEN_SIZE*2;
          5, 6, 7: bytes = HIDDEN_SIZE*2;
          8: bytes = 15*SCRATCH_WIDTH*4;
          9, 10: bytes = MAX_SEQ_LEN*KV_WIDTH*4;
          11: bytes = MAX_SEQ_LEN*HEAD_DIM*4;
          default: bytes = 0;
        endcase
        tensor_length = (bytes + 32'd63) & 32'hffffffc0;
      end
    endfunction

    assign initialized = rst_n && init_done;
    assign image_valid = rst_n && committed;
    assign storage_bf16 = rst_n && bf16;
    assign sticky_error = rst_n && fault;
    assign clear_load_error = rst_n && clear_load;
    assign configuration_busy = rst_n && state != IDLE && state != RESPONSE;
    assign csr_ready = rst_n && init_done && state == IDLE;
    assign csr_rsp_valid = rst_n && state == RESPONSE;
    assign csr_rdata = csr_rsp_valid ? response_data : 32'b0;
    assign csr_error = csr_rsp_valid && response_error;
    assign lookup_ready = rst_n && init_done && (!lookup_pending || lookup_rsp_ready);
    assign lookup_rsp_valid = rst_n && lookup_pending;
    assign lookup_base = lookup_rsp_valid && !lookup_fault ? lookup_entry[64:32] : 33'b0;
    assign lookup_length = lookup_rsp_valid && !lookup_fault ? lookup_entry[31:0] : 32'b0;
    assign lookup_error = lookup_rsp_valid && lookup_fault;

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        lookup_pending <= 0;
        lookup_fault <= 0;
        lookup_entry <= 0;
      end else if (lookup_ready) begin
        lookup_pending <= lookup_valid;
        if (lookup_valid) begin
          if (lookup_index >= COUNT) begin
            lookup_fault <= 1;
            lookup_entry <= 0;
          end else begin
            lookup_entry <= descriptors[lookup_index];
            lookup_fault <= !descriptors[lookup_index][77];
          end
        end
      end
    end

    always @(posedge clk) begin
      if (rst_n) begin
        if (state == INITIALIZE) descriptors[scan_index] <= 0;
        else if (state == INSTALL_WRITE) begin
          if (stage_length == 0) descriptors[selected_index] <= 0;
          else descriptors[selected_index] <=
            {1'b1, stage_layer[4:0], stage_kind[3:0], stage_proj[2:0], candidate_base, stage_length};
        end
        if (state == INSTALL_READ || state == COMMIT_READ) scan_entry <= descriptors[scan_index];
      end
    end

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        state <= INITIALIZE;
        init_done <= 0;
        committed <= 0;
        bf16 <= 0;
        fault <= 0;
        clear_load <= 0;
        previous_load_failed <= 0;
        selected_index <= 0;
        stage_kind <= 0;
        stage_layer <= 0;
        stage_proj <= 0;
        stage_base_low <= 0;
        stage_base_high <= 0;
        stage_length <= 0;
        scan_index <= 0;
        scan_layer <= 0;
        scan_kind <= 0;
        scan_proj <= 0;
        candidate_base <= 0;
        candidate_end <= 0;
        pending_clear <= 0;
        response_data <= 0;
        response_error <= 0;
        token_high_snapshot <= 0;
        read_high_snapshot <= 0;
        token_snapshot_valid <= 0;
        read_snapshot_valid <= 0;
      end else begin
        clear_load <= 0;
        previous_load_failed <= load_failed;
        case (state)
          INITIALIZE: begin
            if (scan_index == COUNT-1) begin
              init_done <= 1;
              state <= IDLE;
            end else scan_index <= scan_index + 1'b1;
          end
          IDLE: if (csr_valid) begin
            response_data <= 0;
            response_error <= 0;
            state <= CSR_DELAY;
            if (csr_address[1:0] != 0 || (mutation && busy)) begin
              response_error <= 1;
              fault <= 1;
            end else if (!csr_write) case (csr_address)
              16'h0000: response_data <= 32'h02000001;
              16'h0004: response_data <= {28'b0, fault, committed, busy, engine_ready};
              16'h0008: response_data <= 0;
              16'h000c: response_data <= {31'b0, bf16};
              16'h0010: response_data <= selected_index;
              16'h0014, 16'h0018, 16'h001c, 16'h0020, 16'h0024, 16'h0028: begin
                if (selected_index >= COUNT || !descriptors[selected_index][77]) begin
                  response_error <= 1;
                  fault <= 1;
                end else case (csr_address)
                  16'h0014: response_data <= {28'b0, descriptors[selected_index][71:68]};
                  16'h0018: response_data <= {27'b0, descriptors[selected_index][76:72]};
                  16'h001c: response_data <= {29'b0, descriptors[selected_index][67:65]};
                  16'h0020: response_data <= descriptors[selected_index][63:32];
                  16'h0024: response_data <= {31'b0, descriptors[selected_index][64]};
                  16'h0028: response_data <= descriptors[selected_index][31:0];
                  default: begin end
                endcase
              end
              16'h0030: begin
                response_data <= token_cycles[31:0];
                token_high_snapshot <= token_cycles[63:32];
                token_snapshot_valid <= 1;
              end
              16'h0034: begin
                response_data <= token_snapshot_valid ? token_high_snapshot : token_cycles[63:32];
                token_snapshot_valid <= 0;
              end
              16'h0038: begin
                response_data <= read_beats[31:0];
                read_high_snapshot <= read_beats[63:32];
                read_snapshot_valid <= 1;
              end
              16'h003c: begin
                response_data <= read_snapshot_valid ? read_high_snapshot : read_beats[63:32];
                read_snapshot_valid <= 0;
              end
              default: begin
                response_error <= 1;
                fault <= 1;
              end
            endcase
            else case (csr_address)
              16'h0008: begin
                if (busy || csr_wdata[31:3] != 0 || csr_wdata[1:0] == 3) begin
                  response_error <= 1;
                  fault <= 1;
                end else if (csr_wdata[1]) begin
                  if (load_failed || !emif_initialized) begin
                    response_error <= 1;
                    fault <= 1;
                  end else begin
                    pending_clear <= csr_wdata[2];
                    scan_index <= 0;
                    scan_layer <= 0;
                    scan_kind <= 0;
                    scan_proj <= 0;
                    state <= COMMIT_READ;
                  end
                end else begin
                  if (csr_wdata[0]) committed <= 0;
                  if (csr_wdata[2]) begin
                    fault <= 0;
                    clear_load <= 1;
                  end
                end
              end
              16'h000c: begin
                if (csr_wdata > 1) begin
                  response_error <= 1;
                  fault <= 1;
                end else begin
                  bf16 <= csr_wdata[0];
                  committed <= 0;
                end
              end
              16'h0010: begin
                if (csr_wdata >= COUNT) begin
                  response_error <= 1;
                  fault <= 1;
                end else selected_index <= csr_wdata;
              end
              16'h0014: begin
                if (csr_wdata > 11) begin response_error <= 1; fault <= 1; end
                else stage_kind <= csr_wdata;
              end
              16'h0018: begin
                if (csr_wdata >= NUM_LAYERS) begin response_error <= 1; fault <= 1; end
                else stage_layer <= csr_wdata;
              end
              16'h001c: begin
                if (csr_wdata > 7) begin response_error <= 1; fault <= 1; end
                else stage_proj <= csr_wdata;
              end
              16'h0020: stage_base_low <= csr_wdata;
              16'h0024: begin
                if (csr_wdata > 1) begin response_error <= 1; fault <= 1; end
                else stage_base_high <= csr_wdata;
              end
              16'h0028: stage_length <= csr_wdata;
              16'h002c: begin
                if (csr_wdata > 1) begin
                  response_error <= 1;
                  fault <= 1;
                end else if (csr_wdata[0]) begin
                  if (!stage_identity_legal || stage_index != selected_index ||
                      (stage_length != 0 &&
                       (install_length == 0 || stage_length != install_length ||
                        stage_base[5:0] != 0 || stage_end > 34'h200000000))) begin
                    response_error <= 1;
                    fault <= 1;
                  end else begin
                    candidate_base <= stage_base;
                    candidate_end <= stage_end;
                    scan_index <= 0;
                    if (stage_length == 0) state <= INSTALL_WRITE;
                    else state <= INSTALL_READ;
                  end
                end
              end
              default: begin
                response_error <= 1;
                fault <= 1;
              end
            endcase
          end
          CSR_DELAY: state <= RESPONSE;
          RESPONSE: if (csr_rsp_ready) state <= IDLE;
          INSTALL_READ: state <= INSTALL_CHECK;
          INSTALL_CHECK: begin
            if (scan_index != selected_index && scan_entry[77] &&
                {1'b0, candidate_base} < scan_end &&
                {1'b0, scan_entry[64:32]} < candidate_end) begin
              response_error <= 1;
              fault <= 1;
              state <= RESPONSE;
            end else if (scan_index == COUNT-1) state <= INSTALL_WRITE;
            else begin
              scan_index <= scan_index + 1'b1;
              state <= INSTALL_READ;
            end
          end
          INSTALL_WRITE: begin
            committed <= 0;
            state <= RESPONSE;
          end
          COMMIT_READ: state <= COMMIT_CHECK;
          COMMIT_CHECK: begin
            if ((required_length != 0 && (!scan_entry[77] ||
                  scan_entry[31:0] != required_length ||
                  scan_entry[76:72] != scan_layer || scan_entry[71:68] != scan_kind ||
                  scan_entry[67:65] != scan_proj ||
                  scan_entry[37:32] != 0 || scan_end > 34'h200000000)) ||
                (required_length == 0 && scan_entry[77]) ||
                load_busy || load_failed || !emif_initialized) begin
              response_error <= 1;
              fault <= 1;
              state <= RESPONSE;
            end else if (scan_index == COUNT-1) begin
              committed <= 1;
              if (pending_clear) begin
                fault <= 0;
                clear_load <= 1;
              end
              state <= RESPONSE;
            end else begin
              scan_index <= scan_index + 1'b1;
              if (scan_proj != 7) scan_proj <= scan_proj + 3'd1;
              else begin
                scan_proj <= 0;
                if (scan_kind != 11) scan_kind <= scan_kind + 4'd1;
                else begin
                  scan_kind <= 0;
                  scan_layer <= scan_layer + 5'd1;
                end
              end
              state <= COMMIT_READ;
            end
          end
          default: begin
            response_error <= 1;
            fault <= 1;
            state <= RESPONSE;
          end
        endcase
        if (fault_event || (load_failed && !previous_load_failed)) fault <= 1;
        if (image_modified) committed <= 0;
      end
    end
  end else begin : g_illegal
    initial $fatal(1, "ANVIL_Q1_HT PARAMETER ERROR: descriptor dimensions");
    assign csr_ready = 0;
    assign csr_rsp_valid = 0;
    assign csr_rdata = 0;
    assign csr_error = 0;
    assign initialized = 0;
    assign image_valid = 0;
    assign storage_bf16 = 0;
    assign sticky_error = 0;
    assign clear_load_error = 0;
    assign configuration_busy = 0;
    assign lookup_ready = 0;
    assign lookup_rsp_valid = 0;
    assign lookup_base = 0;
    assign lookup_length = 0;
    assign lookup_error = 0;
  end endgenerate
endmodule
