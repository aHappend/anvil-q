module anvil_q4_fp_bank_scheduler #(
  parameter integer BANKS = 16,
  parameter integer CLIENTS = 17,
  parameter integer QUEUE_DEPTH = 3,
  localparam integer SB =
    (BANKS == 1 || BANKS == 2 || BANKS == 4 || BANKS == 8 || BANKS == 16) ? BANKS : 1,
  localparam integer SC = (CLIENTS >= 1 && CLIENTS <= 64) ? CLIENTS : 1,
  localparam integer SQ = (QUEUE_DEPTH >= 1 && QUEUE_DEPTH <= 16) ? QUEUE_DEPTH : 1
) (
  input wire clk, rst_n, flush,
  input wire legacy_mode,
  input wire [4:0] active_banks,
  output wire idle, drain_done, fault,
  input wire [SC-1:0] c_req_valid,
  output wire [SC-1:0] c_req_ready,
  input wire [SC-1:0] c_req_write,
  input wire [SC*4-1:0] c_req_kind,
  input wire [SC*32-1:0] c_req_layer,
  input wire [SC*3-1:0] c_req_proj,
  input wire [SC*32-1:0] c_req_row, c_req_col, c_req_wdata,
  input wire [SC*32-1:0] c_req_stride,
  output wire [SC-1:0] c_rsp_valid,
  input wire [SC-1:0] c_rsp_ready,
  output wire [SC*32-1:0] c_rsp_rdata,
  output wire [SC-1:0] c_rsp_error,
  output wire [SB-1:0] mem_req_valid,
  input wire [SB-1:0] mem_req_ready,
  output wire [SB-1:0] mem_req_write,
  output wire [SB*4-1:0] mem_req_kind,
  output wire [SB*32-1:0] mem_req_layer,
  output wire [SB*3-1:0] mem_req_proj,
  output wire [SB*32-1:0] mem_req_row, mem_req_col, mem_req_wdata,
  output wire [SB*64-1:0] mem_req_tag,
  input wire [SB-1:0] mem_rsp_valid, mem_rsp_error,
  output wire [SB-1:0] mem_rsp_ready,
  input wire [SB*32-1:0] mem_rsp_rdata,
  input wire [SB*64-1:0] mem_rsp_tag
);
  localparam integer LEGAL =
    BANKS == SB && CLIENTS == SC && QUEUE_DEPTH == SQ;

  generate
    if (!LEGAL) begin : invalid_parameters
      initial $fatal(1, "PARAMETER ERROR: anvil_q4_fp_bank_scheduler geometry");
      assign idle = 1'b0;
      assign drain_done = 1'b0;
      assign fault = 1'b0;
      assign c_req_ready = 0;
      assign c_rsp_valid = 0;
      assign c_rsp_rdata = 0;
      assign c_rsp_error = 0;
      assign mem_req_valid = 0;
      assign mem_req_write = 0;
      assign mem_req_kind = 0;
      assign mem_req_layer = 0;
      assign mem_req_proj = 0;
      assign mem_req_row = 0;
      assign mem_req_col = 0;
      assign mem_req_wdata = 0;
      assign mem_req_tag = 0;
      assign mem_rsp_ready = 0;
    end else begin : legal
      localparam integer CIW = SC > 1 ? $clog2(SC) : 1;
      localparam integer QIW = SQ > 1 ? $clog2(SQ) : 1;
      localparam integer CT = 2 ** $clog2(SC);
      localparam integer QT = 2 ** $clog2(SQ);
      localparam [2:0] C_FREE = 0, C_ROUTE1 = 1, C_ROUTE2 = 2,
        C_WAIT_SLOT = 3, C_OWNED = 4, C_RESPONSE = 5;
      localparam [2:0] S_FREE = 0, S_QUEUED = 1, S_HELD = 2,
        S_SENT = 3, S_RETURNED = 4;

      reg draining, fault_latched, drain_pulse, wrap_pending, identity_exhausted;
      reg [31:0] epoch;
      reg [2:0] client_state [0:SC-1];
      reg [3:0] client_bank [0:SC-1];
      reg [3:0] route_left [0:SC-1], route_right [0:SC-1];
      reg [3:0] route_sum [0:SC-1], route_col [0:SC-1];
      reg client_write [0:SC-1];
      reg [3:0] client_kind [0:SC-1];
      reg [31:0] client_layer [0:SC-1];
      reg [2:0] client_proj [0:SC-1];
      reg [31:0] client_row [0:SC-1], client_col [0:SC-1];
      reg [31:0] client_wdata [0:SC-1], client_rdata [0:SC-1];
      reg client_error [0:SC-1];

      wire [SC-1:0] client_live, retire;
      wire [SB-1:0] bank_live, bad_bank_response, allocation, returning;
      wire [SB-1:0] serial_exhausted;
      wire [CIW-1:0] allocation_client [0:SB-1];
      wire [CIW-1:0] response_client [0:SB-1];
      wire [QIW-1:0] allocation_slot [0:SB-1];
      wire configuration_valid =
        (active_banks == 1 || active_banks == 2 || active_banks == 4 ||
          active_banks == 8 || active_banks == 16) &&
        active_banks <= BANKS && (!legacy_mode || active_banks <= 8);
      wire bad_response = rst_n && |bad_bank_response;
      wire bad_configuration = rst_n && !configuration_valid;
      wire abort_now = bad_response || bad_configuration || identity_exhausted;
      wire accept_enable = rst_n && !flush && !draining &&
        !fault_latched && !wrap_pending && configuration_valid;
      wire allocate_enable = accept_enable;
      wire wrap_release = rst_n && wrap_pending && !(|bank_live) && !draining &&
        !flush && !abort_now;
      wire [4:0] bank_mask = active_banks - 5'd1;

      assign idle = rst_n && !flush && !draining && !fault_latched &&
        !wrap_pending && configuration_valid && !(|client_live) && !(|bank_live);
      assign drain_done = rst_n && drain_pulse;
      assign fault = rst_n && fault_latched;

      always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
          draining <= 1'b0;
          fault_latched <= 1'b0;
          drain_pulse <= 1'b0;
          wrap_pending <= 1'b0;
          identity_exhausted <= 1'b0;
          epoch <= 0;
        end else begin
          drain_pulse <= 1'b0;
          if (abort_now) begin
            fault_latched <= 1'b1;
            draining <= 1'b1;
          end else if (flush) begin
            fault_latched <= 1'b0;
            draining <= 1'b1;
          end else if (draining && !(|bank_live)) begin
            draining <= 1'b0;
            drain_pulse <= 1'b1;
          end else if (wrap_release) begin
            if (epoch == 32'hffffffff) identity_exhausted <= 1'b1;
            else begin
              epoch <= epoch + 1'b1;
              wrap_pending <= 1'b0;
            end
          end else if (|serial_exhausted) begin
            wrap_pending <= 1'b1;
          end
        end
      end

      genvar c, b, q, n;
      for (c = 0; c < SC; c = c + 1) begin : clients
        wire [SB-1:0] allocated_here, returned_here;
        for (b = 0; b < SB; b = b + 1) begin : bank_matches
          assign allocated_here[b] = allocation[b] && allocation_client[b] == c;
          assign returned_here[b] = returning[b] && response_client[b] == c;
        end
        wire client_allocated = |allocated_here;
        wire client_returned = |returned_here;
        assign client_live[c] = client_state[c] != C_FREE;
        assign c_req_ready[c] = accept_enable && client_state[c] == C_FREE;
        assign c_rsp_valid[c] = rst_n && !flush && !draining && !fault_latched &&
          client_state[c] == C_RESPONSE;
        assign c_rsp_rdata[c*32+:32] = c_rsp_valid[c] ? client_rdata[c] : 32'd0;
        assign c_rsp_error[c] = c_rsp_valid[c] && client_error[c];
        assign retire[c] = c_rsp_valid[c] && c_rsp_ready[c];

        always @(posedge clk or negedge rst_n) begin
          if (!rst_n) begin
            client_state[c] <= C_FREE;
            client_bank[c] <= 0;
            route_left[c] <= 0;
            route_right[c] <= 0;
            route_sum[c] <= 0;
            route_col[c] <= 0;
            client_write[c] <= 0;
            client_kind[c] <= 0;
            client_layer[c] <= 0;
            client_proj[c] <= 0;
            client_row[c] <= 0;
            client_col[c] <= 0;
            client_wdata[c] <= 0;
            client_rdata[c] <= 0;
            client_error[c] <= 0;
          end else if (flush || abort_now || draining) begin
            client_state[c] <= C_FREE;
          end else begin
            case (client_state[c])
              C_FREE: if (c_req_valid[c] && c_req_ready[c]) begin
                client_write[c] <= c_req_write[c];
                client_kind[c] <= c_req_kind[c*4+:4];
                client_layer[c] <= c_req_layer[c*32+:32];
                client_proj[c] <= c_req_proj[c*3+:3];
                client_row[c] <= c_req_row[c*32+:32];
                client_col[c] <= c_req_col[c*32+:32];
                client_wdata[c] <= c_req_wdata[c*32+:32];
                route_col[c] <= c_req_col[c*32+:4];
                if (legacy_mode) begin
                  route_left[c] <= c_req_kind[c*4+:4] + c_req_layer[c*32+:4];
                  route_right[c] <= {1'b0, c_req_proj[c*3+:3]} + c_req_row[c*32+:4];
                end else begin
                  route_left[c] <= c_req_row[c*32+:4];
                  route_right[c] <= 0;
                end
                client_state[c] <= C_ROUTE1;
              end
              C_ROUTE1: begin
                route_sum[c] <= route_left[c] + route_right[c];
                client_state[c] <= C_ROUTE2;
              end
              C_ROUTE2: begin
                client_bank[c] <= (route_sum[c] + route_col[c]) & bank_mask[3:0];
                client_state[c] <= C_WAIT_SLOT;
              end
              C_WAIT_SLOT: if (client_allocated) client_state[c] <= C_OWNED;
              C_OWNED: if (client_returned) begin
                client_rdata[c] <= mem_rsp_rdata[client_bank[c]*32+:32];
                client_error[c] <= mem_rsp_error[client_bank[c]];
                client_state[c] <= C_RESPONSE;
              end
              C_RESPONSE: if (retire[c]) client_state[c] <= C_FREE;
              default: client_state[c] <= C_FREE;
            endcase
          end
        end
      end

      for (b = 0; b < SB; b = b + 1) begin : banks
        reg [2:0] slot_state [0:SQ-1];
        reg [CIW-1:0] slot_owner [0:SQ-1];
        reg [63:0] slot_tag [0:SQ-1];
        reg slot_write [0:SQ-1];
        reg [3:0] slot_kind [0:SQ-1];
        reg [31:0] slot_layer [0:SQ-1];
        reg [2:0] slot_proj [0:SQ-1];
        reg [31:0] slot_row [0:SQ-1], slot_col [0:SQ-1], slot_wdata [0:SQ-1];
        reg [23:0] next_serial;
        reg [CIW-1:0] client_cursor;
        reg [QIW-1:0] dispatch_cursor, held_slot;
        reg holding;

        wire [SQ-1:0] slot_live, slot_sent, slot_returning;
        wire client_candidate [1:2*CT-1];
        wire [CIW:0] client_rank [1:2*CT-1];
        wire [CIW-1:0] selected_client [1:2*CT-1];
        wire free_candidate [1:2*QT-1];
        wire [QIW-1:0] selected_free [1:2*QT-1];
        wire dispatch_candidate [1:2*QT-1];
        wire [QIW:0] dispatch_rank [1:2*QT-1];
        wire [QIW-1:0] selected_dispatch [1:2*QT-1];
        wire response_candidate [1:2*QT-1];
        wire [QIW-1:0] selected_response [1:2*QT-1];

        for (c = 0; c < CT; c = c + 1) begin : client_leaves
          if (c < SC) begin : real_client
            assign client_candidate[CT+c] =
              client_state[c] == C_WAIT_SLOT && client_bank[c] == b;
            assign client_rank[CT+c] = c >= client_cursor ?
              (CIW+1)'(c) - {1'b0, client_cursor} :
              (CIW+1)'(c+SC) - {1'b0, client_cursor};
            assign selected_client[CT+c] = CIW'(c);
          end else begin : padding
            assign client_candidate[CT+c] = 1'b0;
            assign client_rank[CT+c] = 0;
            assign selected_client[CT+c] = 0;
          end
        end
        for (n = 1; n < CT; n = n + 1) begin : client_selection
          wire choose_left = client_candidate[2*n] &&
            (!client_candidate[2*n+1] || client_rank[2*n] <= client_rank[2*n+1]);
          assign client_candidate[n] = client_candidate[2*n] || client_candidate[2*n+1];
          assign client_rank[n] = choose_left ? client_rank[2*n] : client_rank[2*n+1];
          assign selected_client[n] = choose_left ?
            selected_client[2*n] : selected_client[2*n+1];
        end

        for (q = 0; q < QT; q = q + 1) begin : slot_leaves
          if (q < SQ) begin : real_slot
            wire same_edge_issue = holding && held_slot == q &&
              mem_req_valid[b] && mem_req_ready[b];
            assign free_candidate[QT+q] = slot_state[q] == S_FREE;
            assign selected_free[QT+q] = QIW'(q);
            assign dispatch_candidate[QT+q] = slot_state[q] == S_QUEUED;
            assign dispatch_rank[QT+q] = q >= dispatch_cursor ?
              (QIW+1)'(q) - {1'b0, dispatch_cursor} :
              (QIW+1)'(q+SQ) - {1'b0, dispatch_cursor};
            assign selected_dispatch[QT+q] = QIW'(q);
            assign response_candidate[QT+q] = mem_rsp_valid[b] &&
              (slot_state[q] == S_SENT || same_edge_issue) &&
              slot_tag[q] == mem_rsp_tag[b*64+:64];
            assign selected_response[QT+q] = QIW'(q);
          end else begin : padding
            assign free_candidate[QT+q] = 1'b0;
            assign selected_free[QT+q] = 0;
            assign dispatch_candidate[QT+q] = 1'b0;
            assign dispatch_rank[QT+q] = 0;
            assign selected_dispatch[QT+q] = 0;
            assign response_candidate[QT+q] = 1'b0;
            assign selected_response[QT+q] = 0;
          end
        end
        for (n = 1; n < QT; n = n + 1) begin : slot_selection
          wire choose_dispatch_left = dispatch_candidate[2*n] &&
            (!dispatch_candidate[2*n+1] || dispatch_rank[2*n] <= dispatch_rank[2*n+1]);
          assign free_candidate[n] = free_candidate[2*n] || free_candidate[2*n+1];
          assign selected_free[n] = free_candidate[2*n] ?
            selected_free[2*n] : selected_free[2*n+1];
          assign dispatch_candidate[n] = dispatch_candidate[2*n] || dispatch_candidate[2*n+1];
          assign dispatch_rank[n] = choose_dispatch_left ?
            dispatch_rank[2*n] : dispatch_rank[2*n+1];
          assign selected_dispatch[n] = choose_dispatch_left ?
            selected_dispatch[2*n] : selected_dispatch[2*n+1];
          assign response_candidate[n] = response_candidate[2*n] || response_candidate[2*n+1];
          assign selected_response[n] = response_candidate[2*n] ?
            selected_response[2*n] : selected_response[2*n+1];
        end

        wire dispatch = rst_n && !flush && !draining && !fault_latched &&
          !holding && dispatch_candidate[1];
        wire issue = mem_req_valid[b] && mem_req_ready[b];
        assign bank_live[b] = |slot_live;
        assign allocation[b] = allocate_enable && b < active_banks &&
          client_candidate[1] && free_candidate[1];
        assign allocation_client[b] = selected_client[1];
        assign allocation_slot[b] = selected_free[1];
        assign serial_exhausted[b] = allocation[b] && next_serial == 24'hffffff;
        assign mem_rsp_ready[b] = rst_n &&
          (b < active_banks || (|slot_sent) || mem_rsp_valid[b]);
        assign returning[b] = rst_n && mem_rsp_valid[b] && mem_rsp_ready[b] &&
          response_candidate[1];
        assign response_client[b] = slot_owner[selected_response[1]];
        assign bad_bank_response[b] = mem_rsp_valid[b] && !response_candidate[1];

        // Presentation transfers ownership to the external handshake even on flush.
        assign mem_req_valid[b] = rst_n && holding;
        assign mem_req_write[b] = mem_req_valid[b] && slot_write[held_slot];
        assign mem_req_kind[b*4+:4] = mem_req_valid[b] ? slot_kind[held_slot] : 4'd0;
        assign mem_req_layer[b*32+:32] = mem_req_valid[b] ? slot_layer[held_slot] : 32'd0;
        assign mem_req_proj[b*3+:3] = mem_req_valid[b] ? slot_proj[held_slot] : 3'd0;
        assign mem_req_row[b*32+:32] = mem_req_valid[b] ? slot_row[held_slot] : 32'd0;
        assign mem_req_col[b*32+:32] = mem_req_valid[b] ? slot_col[held_slot] : 32'd0;
        assign mem_req_wdata[b*32+:32] = mem_req_valid[b] ? slot_wdata[held_slot] : 32'd0;
        assign mem_req_tag[b*64+:64] = mem_req_valid[b] ? slot_tag[held_slot] : 64'd0;

        always @(posedge clk or negedge rst_n) begin
          if (!rst_n) begin
            next_serial <= 0;
            client_cursor <= 0;
            dispatch_cursor <= 0;
            held_slot <= 0;
            holding <= 1'b0;
          end else begin
            if (wrap_release && epoch != 32'hffffffff)
              next_serial <= 0;
            else if (allocation[b] && !abort_now)
              next_serial <= next_serial + 1'b1;
            if (flush || abort_now || draining) begin
              if (issue) holding <= 1'b0;
            end else begin
              if (allocation[b]) begin
                if (selected_client[1] == SC-1) client_cursor <= 0;
                else client_cursor <= selected_client[1] + 1'b1;
              end
              if (issue) holding <= 1'b0;
              else if (dispatch) begin
                holding <= 1'b1;
                held_slot <= selected_dispatch[1];
                if (selected_dispatch[1] == SQ-1) dispatch_cursor <= 0;
                else dispatch_cursor <= selected_dispatch[1] + 1'b1;
              end
            end
          end
        end

        for (q = 0; q < SQ; q = q + 1) begin : slots
          assign slot_live[q] = slot_state[q] != S_FREE;
          assign slot_sent[q] = slot_state[q] == S_SENT;
          assign slot_returning[q] = returning[b] && selected_response[1] == q;
          wire slot_issuing = issue && held_slot == q;
          wire slot_allocating = allocation[b] && selected_free[1] == q;
          wire slot_dispatching = dispatch && selected_dispatch[1] == q;
          wire slot_retiring = slot_state[q] == S_RETURNED && retire[slot_owner[q]];
          wire [63:0] allocated_tag = {epoch, next_serial, 4'(b), 4'(q)};

          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
              slot_state[q] <= S_FREE;
              slot_owner[q] <= 0;
              slot_tag[q] <= 0;
              slot_write[q] <= 0;
              slot_kind[q] <= 0;
              slot_layer[q] <= 0;
              slot_proj[q] <= 0;
              slot_row[q] <= 0;
              slot_col[q] <= 0;
              slot_wdata[q] <= 0;
            end else if (flush || abort_now) begin
              if (slot_returning[q]) slot_state[q] <= S_FREE;
              else if (slot_issuing || slot_state[q] == S_SENT) slot_state[q] <= S_SENT;
              else if (slot_state[q] == S_HELD) slot_state[q] <= S_HELD;
              else slot_state[q] <= S_FREE;
            end else if (draining) begin
              if (slot_returning[q]) slot_state[q] <= S_FREE;
              else if (slot_issuing) slot_state[q] <= S_SENT;
              else if (slot_state[q] != S_SENT && slot_state[q] != S_HELD)
                slot_state[q] <= S_FREE;
            end else begin
              if (slot_returning[q]) slot_state[q] <= S_RETURNED;
              else if (slot_issuing) slot_state[q] <= S_SENT;
              else if (slot_dispatching) slot_state[q] <= S_HELD;
              else if (slot_allocating) slot_state[q] <= S_QUEUED;
              else if (slot_retiring) slot_state[q] <= S_FREE;
              if (slot_allocating) begin
                slot_owner[q] <= selected_client[1];
                slot_tag[q] <= allocated_tag;
                slot_write[q] <= client_write[selected_client[1]];
                slot_kind[q] <= client_kind[selected_client[1]];
                slot_layer[q] <= client_layer[selected_client[1]];
                slot_proj[q] <= client_proj[selected_client[1]];
                slot_row[q] <= client_row[selected_client[1]];
                slot_col[q] <= client_col[selected_client[1]];
                slot_wdata[q] <= client_wdata[selected_client[1]];
              end
            end
          end
        end
      end
    end
  endgenerate
endmodule
