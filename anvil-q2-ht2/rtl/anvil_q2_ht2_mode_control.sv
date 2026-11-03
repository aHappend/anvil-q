module anvil_q2_ht2_mode_control (
  input wire clk, rst_n, annul,
  input wire operation_busy, quiescent, cache_valid, sticky_fault,
  input wire cfg_valid, cfg_write,
  input wire [15:0] cfg_addr,
  input wire [31:0] cfg_wdata,
  output wire cfg_ready, cfg_rsp_valid,
  input wire cfg_rsp_ready,
  output wire [31:0] cfg_rdata,
  output wire cfg_error,
  output wire [5:0] ht2_mode, mode_change_mask,
  output wire [2:0] ht2_k,
  output wire k_changed,
  output wire legacy_cfg_valid, legacy_cfg_write,
  output wire [15:0] legacy_cfg_addr,
  output wire [31:0] legacy_cfg_wdata,
  input wire legacy_cfg_ready, legacy_cfg_rsp_valid,
  output wire legacy_cfg_rsp_ready,
  input wire [31:0] legacy_cfg_rdata,
  input wire legacy_cfg_error
);
  localparam [2:0] IDLE=0, RESPONSE=1, FORWARD_REQUEST=2,
    FORWARD_RESPONSE=3, DRAIN=4;
  reg [2:0] state;
  reg [5:0] mode, changed_mask;
  reg [2:0] width;
  reg changed_k, response_error, request_write;
  reg [31:0] response_data, request_data;
  reg [15:0] request_address;
  wire mode_legal=(cfg_wdata & 32'hffffffc0)==0 &&
    cfg_wdata[1:0]!=3 && cfg_wdata[3:2]!=3;
  wire k_legal=cfg_wdata==1 || cfg_wdata==2 || cfg_wdata==4;
  wire writable=quiescent && !operation_busy;

  assign cfg_ready=rst_n && !annul && state==IDLE;
  assign cfg_rsp_valid=rst_n && !annul && state==RESPONSE;
  assign cfg_rdata=cfg_rsp_valid ? response_data : 32'd0;
  assign cfg_error=cfg_rsp_valid && response_error;
  assign ht2_mode=rst_n ? mode : 6'd0;
  assign ht2_k=rst_n ? width : 3'd0;
  assign mode_change_mask=rst_n && !annul ? changed_mask : 6'd0;
  assign k_changed=rst_n && !annul && changed_k;
  assign legacy_cfg_valid=rst_n && !annul && state==FORWARD_REQUEST;
  assign legacy_cfg_write=legacy_cfg_valid && request_write;
  assign legacy_cfg_addr=legacy_cfg_valid ? request_address : 16'd0;
  assign legacy_cfg_wdata=legacy_cfg_valid ? request_data : 32'd0;
  assign legacy_cfg_rsp_ready=rst_n && (state==FORWARD_RESPONSE || state==DRAIN);

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; mode<=1; width<=1; changed_mask<=0; changed_k<=0;
      response_error<=0; request_write<=0; response_data<=0;
      request_data<=0; request_address<=0;
    end else if (annul) begin
      changed_mask<=0; changed_k<=0;
      if ((state==FORWARD_RESPONSE || state==DRAIN) && !legacy_cfg_rsp_valid)
        state<=DRAIN;
      else state<=IDLE;
    end else begin
      changed_mask<=0; changed_k<=0;
      case (state)
        IDLE: if (cfg_valid && cfg_ready) begin
          response_data<=0; response_error<=0;
          if (cfg_addr[1:0]!=0) begin
            response_error<=1; state<=RESPONSE;
          end else case (cfg_addr)
            16'h0040: begin
              state<=RESPONSE;
              if (!cfg_write) response_data<={26'd0,mode};
              else if (!writable || !mode_legal) response_error<=1;
              else begin
                mode<=cfg_wdata[5:0];
                changed_mask<=mode ^ cfg_wdata[5:0];
              end
            end
            16'h0044: begin
              state<=RESPONSE;
              if (!cfg_write) response_data<={29'd0,width};
              else if (!writable || !k_legal) response_error<=1;
              else begin width<=cfg_wdata[2:0]; changed_k<=width!=cfg_wdata[2:0]; end
            end
            16'h0048: begin
              state<=RESPONSE;
              if (cfg_write) response_error<=1;
              else response_data<={28'd0,sticky_fault,cache_valid,quiescent,operation_busy};
            end
            default: begin
              request_write<=cfg_write; request_address<=cfg_addr;
              request_data<=cfg_wdata; state<=FORWARD_REQUEST;
            end
          endcase
        end
        RESPONSE: if (cfg_rsp_ready) state<=IDLE;
        FORWARD_REQUEST: if (legacy_cfg_ready) state<=FORWARD_RESPONSE;
        FORWARD_RESPONSE: if (legacy_cfg_rsp_valid) begin
          response_data<=legacy_cfg_rdata;
          response_error<=legacy_cfg_error;
          state<=RESPONSE;
        end
        DRAIN: if (legacy_cfg_rsp_valid) state<=IDLE;
        default: begin response_data<=0; response_error<=1; state<=RESPONSE; end
      endcase
    end
  end
endmodule
