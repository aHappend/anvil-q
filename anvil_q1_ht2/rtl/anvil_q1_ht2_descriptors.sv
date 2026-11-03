module anvil_q1_ht2_descriptors #(
  parameter NUM_LAYERS = 24, HIDDEN_SIZE = 896, INTERMEDIATE_SIZE = 4864,
  parameter NUM_KV_HEADS = 2, HEAD_DIM = 64, GROUP_SIZE = 128,
  parameter VOCAB_SIZE = 151936, MAX_SEQ_LEN = 32768
) (
  input wire clk, rst_n,
  input wire [1:0] format,
  input wire invalidate_image,
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
  output wire initialized, image_valid, finite_image, sticky_error,
  output wire clear_load_error, configuration_busy, invalidate_prefix,
  input wire lookup_valid,
  output wire lookup_ready,
  input wire [31:0] lookup_index,
  output wire lookup_rsp_valid,
  input wire lookup_rsp_ready,
  output wire [32:0] lookup_base,
  output wire [31:0] lookup_length,
  output wire lookup_error,
  output wire dma_valid,
  input wire dma_ready,
  output wire [32:0] dma_address,
  output wire [7:0] dma_burstcount,
  input wire dma_data_valid,
  output wire dma_data_ready,
  input wire [511:0] dma_data,
  input wire dma_error
);
  localparam SG = GROUP_SIZE > 0 ? GROUP_SIZE : 1;
  localparam LEGAL = NUM_LAYERS >= 1 && NUM_LAYERS <= 24 &&
    HIDDEN_SIZE >= 8 && HIDDEN_SIZE <= 896 && (HIDDEN_SIZE & 7) == 0 &&
    INTERMEDIATE_SIZE >= 8 && INTERMEDIATE_SIZE <= 4864 &&
    (INTERMEDIATE_SIZE & 7) == 0 && NUM_KV_HEADS >= 1 && NUM_KV_HEADS <= 2 &&
    HEAD_DIM >= 2 && HEAD_DIM <= 64 && (HEAD_DIM & 1) == 0 &&
    ((NUM_KV_HEADS*HEAD_DIM) & 7) == 0 && GROUP_SIZE >= 1 &&
    GROUP_SIZE <= HIDDEN_SIZE && HIDDEN_SIZE % SG == 0 && INTERMEDIATE_SIZE % SG == 0 &&
    VOCAB_SIZE >= 1 && VOCAB_SIZE <= 151936 &&
    MAX_SEQ_LEN >= 1 && MAX_SEQ_LEN <= 32768;
  localparam L = LEGAL ? NUM_LAYERS : 1, H = LEGAL ? HIDDEN_SIZE : 8;
  localparam I = LEGAL ? INTERMEDIATE_SIZE : 8;
  localparam C = LEGAL ? NUM_KV_HEADS*HEAD_DIM : 8;
  localparam D = LEGAL ? HEAD_DIM : 8, G = LEGAL ? GROUP_SIZE : 1;
  localparam V = LEGAL ? VOCAB_SIZE : 1, S = LEGAL ? MAX_SEQ_LEN : 1;
  localparam COUNT = 96*L, INDEX_BITS = $clog2(COUNT);
  localparam INITIALIZE = 5'd0, IDLE = 5'd1, RESPONSE = 5'd2,
    CSR_READ = 5'd3, CSR_VALUE = 5'd4, INSTALL_READ = 5'd5,
    INSTALL_CHECK = 5'd6, INSTALL_WRITE = 5'd7,
    COMMIT_READ = 5'd8, COMMIT_CHECK = 5'd9,
    VALIDATE_SEND = 5'd10, VALIDATE_WAIT = 5'd11,
    COMMIT_NEXT = 5'd12;
  wire run_n;
  reg [4:0] state;
  reg init_done, committed, fault, clear_load, prefix_pulse, previous_load_failed;
  reg [1:0] image_format;
  reg [31:0] selected_index;
  reg [31:0] stage_kind, stage_layer, stage_projection, stage_base_low, stage_base_high;
  reg [31:0] stage_length, response_data;
  reg [15:0] read_address;
  reg response_error, pending_clear, validation_invalidated;
  reg [INDEX_BITS-1:0] scan_index;
  reg [4:0] scan_layer;
  reg [3:0] scan_kind;
  reg [2:0] scan_projection;
  reg [77:0] scan_entry, lookup_entry;
  reg lookup_pending, lookup_fault;
  reg [32:0] validation_address;
  reg [31:0] validation_remaining;
  reg [31:0] token_high, read_high;
  reg token_snapshot_valid, read_snapshot_valid;
  (* ramstyle = "M20K", ram_style = "block", nomem2reg *)
  reg [77:0] descriptors [0:COUNT-1];
  wire mutation_busy = engine_busy || load_busy;
  wire readonly_address = csr_address == 0 || csr_address == 4 ||
    (csr_address >= 16'h0030 && csr_address <= 16'h003c);
  wire [31:0] stage_index = (stage_layer << 6) + (stage_layer << 5) +
    (stage_kind << 3) + stage_projection;
  wire [32:0] stage_base = {stage_base_high[0], stage_base_low};
  wire [33:0] stage_end = {1'b0, stage_base} + {2'b0, stage_length};
  wire [33:0] scan_end = {1'b0, scan_entry[64:32]} + {2'b0, scan_entry[31:0]};
  wire [31:0] install_length = tensor_length(stage_kind, stage_layer, stage_projection, format);
  wire [31:0] required_length = tensor_length({28'b0, scan_kind},
    {27'b0, scan_layer}, {29'b0, scan_projection}, image_format);
  wire model_tensor = scan_kind == 0 || scan_kind == 1 || scan_kind == 2 ||
    scan_kind == 3 || scan_kind == 4 || scan_kind == 5 || scan_kind == 6 || scan_kind == 7;
  wire validate_numeric = scan_kind != 2 && !(scan_kind == 1 && image_format == 2);
  wire validation_fp16 = scan_kind == 3 || image_format == 1;
  wire validation_changed = validation_invalidated || invalidate_image || image_modified;
  wire validation_unavailable = validation_changed || load_busy || load_failed ||
    !emif_initialized || image_format != format;
  wire validating = state == COMMIT_READ || state == COMMIT_CHECK ||
    state == VALIDATE_SEND || state == VALIDATE_WAIT || state == COMMIT_NEXT;
  wire reader_ready, reader_valid, reader_error;
  wire [1023:0] reader_data;
  reg numeric_bad;
  integer halfword;

  function automatic tensor_identity(
    input [31:0] kind, input [31:0] tensor_layer, input [31:0] projection
  );
    begin
      tensor_identity = 0;
      if (tensor_layer < L) case (kind)
        0, 7, 8, 11: tensor_identity = tensor_layer == 0 && projection == 0;
        1, 2, 3: tensor_identity = projection < 7;
        4: tensor_identity = projection < 3;
        5, 6, 9, 10: tensor_identity = projection == 0;
        default: tensor_identity = 0;
      endcase
    end
  endfunction

  function automatic [31:0] tensor_length(
    input [31:0] kind, input [31:0] tensor_layer, input [31:0] projection,
    input [1:0] selected_format
  );
    reg [31:0] bytes, panels, inputs, groups;
    begin
      bytes = 0;
      panels = (H+63)/64;
      inputs = H;
      groups = H/G;
      case (projection)
        1, 2: panels = (C+63)/64;
        4, 5: panels = (I+63)/64;
        6: begin inputs = I; groups = I/G; end
        default: begin end
      endcase
      if (selected_format != 3 && tensor_identity(kind, tensor_layer, projection))
        case (kind)
          0: bytes = ((V+63)/64)*H*128;
          1: bytes = panels*inputs*(selected_format == 2 ? 64 : 128);
          2: if (selected_format == 2) bytes = panels*groups*64;
          3: if (selected_format == 2) bytes = panels*groups*128;
          4: bytes = projection == 0 ? H*2 : C*2;
          5, 6, 7: bytes = H*2;
          8: bytes = 15*(H > I ? H : I)*4;
          9, 10: bytes = S*((2*C+63)/64)*64;
          11: bytes = S*D*4;
          default: bytes = 0;
        endcase
      tensor_length = (bytes+32'd63) & 32'hffffffc0;
    end
  endfunction

  initial begin
    if (!LEGAL) $fatal(1, "PARAMETER ERROR: native descriptor geometry");
  end
  anvil_q1_ht2_reset_sync u_reset(clk, rst_n, run_n);
  anvil_q1_ht2_burst_reader u_validator (
    .clk(clk), .rst_n(run_n),
    .cmd_valid(state == VALIDATE_SEND && !validation_unavailable), .cmd_ready(reader_ready),
    .cmd_address(validation_address), .cmd_burstcount(8'd1),
    .mem_valid(dma_valid), .mem_ready(dma_ready), .mem_address(dma_address),
    .mem_burstcount(dma_burstcount), .mem_data_valid(dma_data_valid),
    .mem_data_ready(dma_data_ready), .mem_data(dma_data), .mem_error(dma_error),
    .rsp_valid(reader_valid), .rsp_ready(state == VALIDATE_WAIT),
    .rsp_data(reader_data), .rsp_error(reader_error)
  );
  always @* begin
    numeric_bad = 0;
    for (halfword = 0; halfword < 32; halfword = halfword + 1) begin
      if (validate_numeric) begin
        if (validation_fp16) begin
          if (reader_data[16*halfword+10+:5] == 5'h1f) numeric_bad = 1;
        end else if (reader_data[16*halfword+7+:8] == 8'hff) numeric_bad = 1;
        if (scan_kind == 3 && reader_data[16*halfword+15] &&
            reader_data[16*halfword+:15] != 0) numeric_bad = 1;
      end
    end
  end
  assign initialized = run_n && init_done;
  assign image_valid = run_n && committed;
  assign finite_image = image_valid;
  assign sticky_error = run_n && fault;
  assign clear_load_error = run_n && clear_load;
  assign invalidate_prefix = run_n && prefix_pulse;
  assign configuration_busy = run_n && state != IDLE && state != RESPONSE;
  assign csr_ready = run_n && init_done && state == IDLE;
  assign csr_rsp_valid = run_n && state == RESPONSE;
  assign csr_rdata = csr_rsp_valid ? response_data : 32'b0;
  assign csr_error = csr_rsp_valid && response_error;
  assign lookup_ready = run_n && init_done && (!lookup_pending || lookup_rsp_ready);
  assign lookup_rsp_valid = run_n && lookup_pending;
  assign lookup_error = lookup_rsp_valid && (lookup_fault || !lookup_entry[77]);
  assign lookup_base = lookup_rsp_valid && !lookup_error ? lookup_entry[64:32] : 33'b0;
  assign lookup_length = lookup_rsp_valid && !lookup_error ? lookup_entry[31:0] : 32'b0;

  always @(posedge clk) begin
    if (run_n) begin
      if (state == INITIALIZE) descriptors[scan_index] <= 0;
      if (state == INSTALL_WRITE) begin
        if (stage_length == 0) descriptors[selected_index] <= 0;
        else descriptors[selected_index] <= {1'b1, stage_layer[4:0], stage_kind[3:0],
          stage_projection[2:0], stage_base, stage_length};
      end
      if (state == CSR_READ) scan_entry <= descriptors[selected_index];
      if (state == INSTALL_READ || state == COMMIT_READ) scan_entry <= descriptors[scan_index];
      if (lookup_valid && lookup_ready && lookup_index < COUNT)
        lookup_entry <= descriptors[lookup_index];
    end
  end
  always @(posedge clk or negedge run_n) begin
    if (!run_n) begin
      lookup_pending <= 0;
      lookup_fault <= 0;
    end else if (lookup_ready) begin
      lookup_pending <= lookup_valid;
      if (lookup_valid) lookup_fault <= lookup_index >= COUNT;
    end
  end
  always @(posedge clk or negedge run_n) begin
    if (!run_n) begin
      state <= INITIALIZE;
      init_done <= 0;
      committed <= 0;
      fault <= 0;
      clear_load <= 0;
      prefix_pulse <= 0;
      previous_load_failed <= 0;
      image_format <= 0;
      selected_index <= 0;
      stage_kind <= 0;
      stage_layer <= 0;
      stage_projection <= 0;
      stage_base_low <= 0;
      stage_base_high <= 0;
      stage_length <= 0;
      response_data <= 0;
      read_address <= 0;
      response_error <= 0;
      pending_clear <= 0;
      validation_invalidated <= 0;
      scan_index <= 0;
      scan_layer <= 0;
      scan_kind <= 0;
      scan_projection <= 0;
      validation_address <= 0;
      validation_remaining <= 0;
      token_high <= 0;
      read_high <= 0;
      token_snapshot_valid <= 0;
      read_snapshot_valid <= 0;
    end else begin
      clear_load <= 0;
      prefix_pulse <= 0;
      previous_load_failed <= load_failed;
      case (state)
        INITIALIZE: begin
          if (scan_index + 1 == COUNT) begin init_done <= 1; state <= IDLE; end
          else scan_index <= scan_index + 1'b1;
        end
        IDLE: if (csr_valid && csr_ready) begin
          response_data <= 0;
          response_error <= 0;
          state <= RESPONSE;
          if (csr_address[1:0] != 0 || (csr_write && !readonly_address && mutation_busy)) begin
            response_error <= 1;
            fault <= 1;
          end else if (!csr_write) case (csr_address)
            16'h0000: response_data <= 32'h02000001;
            16'h0004: response_data <= {28'b0, fault, committed, mutation_busy, engine_ready};
            16'h0008: response_data <= 0;
            16'h000c: response_data <= {31'b0, format != 2};
            16'h0010: response_data <= selected_index;
            16'h0014, 16'h0018, 16'h001c, 16'h0020, 16'h0024, 16'h0028: begin
              if (selected_index >= COUNT) begin response_error <= 1; fault <= 1; end
              else begin read_address <= csr_address; state <= CSR_READ; end
            end
            16'h0030: begin
              response_data <= token_cycles[31:0];
              token_high <= token_cycles[63:32];
              token_snapshot_valid <= 1;
            end
            16'h0034: begin
              response_data <= token_snapshot_valid ? token_high : token_cycles[63:32];
              token_snapshot_valid <= 0;
            end
            16'h0038: begin
              response_data <= read_beats[31:0];
              read_high <= read_beats[63:32];
              read_snapshot_valid <= 1;
            end
            16'h003c: begin
              response_data <= read_snapshot_valid ? read_high : read_beats[63:32];
              read_snapshot_valid <= 0;
            end
            default: begin response_error <= 1; fault <= 1; end
          endcase
          else case (csr_address)
            16'h0008: begin
              if (csr_wdata[31:3] != 0 || csr_wdata[1:0] == 3) begin
                response_error <= 1;
                fault <= 1;
              end else if (csr_wdata[1]) begin
                if (load_failed || !emif_initialized || format == 3) begin
                  response_error <= 1;
                  fault <= 1;
                end else begin
                  committed <= 0;
                  prefix_pulse <= 1;
                  pending_clear <= csr_wdata[2];
                  validation_invalidated <= 0;
                  image_format <= format;
                  scan_index <= 0;
                  scan_layer <= 0;
                  scan_kind <= 0;
                  scan_projection <= 0;
                  state <= COMMIT_READ;
                end
              end else begin
                if (csr_wdata[0]) begin committed <= 0; prefix_pulse <= 1; end
                if (csr_wdata[2]) begin fault <= 0; clear_load <= 1; end
              end
            end
            16'h0010: begin
              if (csr_wdata >= COUNT) begin response_error <= 1; fault <= 1; end
              else selected_index <= csr_wdata;
            end
            16'h0014: begin
              if (csr_wdata > 11) begin response_error <= 1; fault <= 1; end
              else stage_kind <= csr_wdata;
            end
            16'h0018: begin
              if (csr_wdata >= L) begin response_error <= 1; fault <= 1; end
              else stage_layer <= csr_wdata;
            end
            16'h001c: begin
              if (csr_wdata > 7) begin response_error <= 1; fault <= 1; end
              else stage_projection <= csr_wdata;
            end
            16'h0020: stage_base_low <= csr_wdata;
            16'h0024: begin
              if (csr_wdata > 1) begin response_error <= 1; fault <= 1; end
              else stage_base_high <= csr_wdata;
            end
            16'h0028: stage_length <= csr_wdata;
            16'h002c: begin
              if (csr_wdata > 1) begin response_error <= 1; fault <= 1; end
              else if (csr_wdata[0]) begin
                if (!tensor_identity(stage_kind, stage_layer, stage_projection) ||
                    stage_index != selected_index ||
                    (stage_length != 0 && (install_length == 0 ||
                      stage_length != install_length || (|stage_base[5:0]) ||
                      stage_end > 34'h200000000))) begin
                  response_error <= 1;
                  fault <= 1;
                end else begin
                  scan_index <= 0;
                  if (stage_length == 0) state <= INSTALL_WRITE;
                  else state <= INSTALL_READ;
                end
              end
            end
            default: begin response_error <= 1; fault <= 1; end
          endcase
        end
        CSR_READ: state <= CSR_VALUE;
        CSR_VALUE: begin
          if (!scan_entry[77]) begin response_error <= 1; fault <= 1; end
          else case (read_address)
            16'h0014: response_data <= {28'b0, scan_entry[71:68]};
            16'h0018: response_data <= {27'b0, scan_entry[76:72]};
            16'h001c: response_data <= {29'b0, scan_entry[67:65]};
            16'h0020: response_data <= scan_entry[63:32];
            16'h0024: response_data <= {31'b0, scan_entry[64]};
            16'h0028: response_data <= scan_entry[31:0];
            default: begin response_error <= 1; fault <= 1; end
          endcase
          state <= RESPONSE;
        end
        INSTALL_READ: state <= INSTALL_CHECK;
        INSTALL_CHECK: begin
          if (scan_index != selected_index && scan_entry[77] &&
              {1'b0, stage_base} < scan_end && {1'b0, scan_entry[64:32]} < stage_end) begin
            response_error <= 1;
            fault <= 1;
            state <= RESPONSE;
          end else if (scan_index + 1 == COUNT) state <= INSTALL_WRITE;
          else begin scan_index <= scan_index + 1'b1; state <= INSTALL_READ; end
        end
        INSTALL_WRITE: begin
          committed <= 0;
          prefix_pulse <= 1;
          state <= RESPONSE;
        end
        COMMIT_READ: state <= COMMIT_CHECK;
        COMMIT_CHECK: begin
          if ((required_length != 0 && (!scan_entry[77] ||
                scan_entry[31:0] != required_length || scan_entry[76:72] != scan_layer ||
                scan_entry[71:68] != scan_kind || scan_entry[67:65] != scan_projection ||
                (|scan_entry[37:32]) || scan_end > 34'h200000000)) ||
              (required_length == 0 && scan_entry[77]) ||
              load_busy || load_failed || !emif_initialized || image_format != format ||
              validation_changed) begin
            response_error <= 1;
            fault <= 1;
            state <= RESPONSE;
          end else if (required_length != 0 && model_tensor) begin
            validation_address <= scan_entry[64:32];
            validation_remaining <= required_length;
            state <= VALIDATE_SEND;
          end else state <= COMMIT_NEXT;
        end
        VALIDATE_SEND: begin
          if (validation_unavailable) begin response_error <= 1; fault <= 1; state <= RESPONSE; end
          else if (reader_ready) state <= VALIDATE_WAIT;
        end
        VALIDATE_WAIT: if (reader_valid) begin
          if (reader_error || numeric_bad || load_busy || load_failed ||
              !emif_initialized || image_format != format || validation_changed) begin
            response_error <= 1;
            fault <= 1;
            state <= RESPONSE;
          end else if (validation_remaining == 64) state <= COMMIT_NEXT;
          else begin
            validation_remaining <= validation_remaining - 32'd64;
            validation_address <= validation_address + 33'd64;
            state <= VALIDATE_SEND;
          end
        end
        COMMIT_NEXT: begin
          if (validation_changed || load_busy || load_failed ||
              !emif_initialized || image_format != format) begin
            response_error <= 1;
            fault <= 1;
            state <= RESPONSE;
          end else if (scan_index + 1 == COUNT) begin
            committed <= 1;
            if (pending_clear) begin fault <= 0; clear_load <= 1; end
            state <= RESPONSE;
          end else begin
            scan_index <= scan_index + 1'b1;
            if (scan_projection != 7) scan_projection <= scan_projection + 1'b1;
            else begin
              scan_projection <= 0;
              if (scan_kind != 11) scan_kind <= scan_kind + 1'b1;
              else begin scan_kind <= 0; scan_layer <= scan_layer + 1'b1; end
            end
            state <= COMMIT_READ;
          end
        end
        RESPONSE: if (csr_rsp_ready) state <= IDLE;
        default: begin response_error <= 1; fault <= 1; committed <= 0; state <= RESPONSE; end
      endcase
      if (fault_event || (load_failed && !previous_load_failed)) fault <= 1;
      if (invalidate_image || image_modified) begin
        committed <= 0;
        prefix_pulse <= 1;
        if (validating) validation_invalidated <= 1;
      end
    end
  end
endmodule
