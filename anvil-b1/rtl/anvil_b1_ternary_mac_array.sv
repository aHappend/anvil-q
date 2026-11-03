(* multstyle = "logic", use_dsp = "no" *)
module anvil_b1_ternary_mac_array #(
  parameter integer LANES=512,
  localparam integer RADIX_BYTES=(LANES+4)/5,
  localparam integer WEIGHT_BITS=(2*LANES > 8*RADIX_BYTES) ? 2*LANES : 8*RADIX_BYTES,
  localparam integer SL=(LANES>=1 && LANES<=512) ? LANES : 1,
  localparam integer SW=(WEIGHT_BITS>0) ? WEIGHT_BITS : 8
) (
  input wire clk, rst_n, flush, in_valid, out_ready,
  output wire in_ready, out_valid,
  input wire [8*SL-1:0] in_act,
  input wire [SW-1:0] in_weights,
  input wire [SL-1:0] in_mask,
  input wire in_packing, in_first, in_last,
  input wire [31:0] in_tag,
  output wire signed [31:0] out_sum,
  output wire out_error, out_first, out_last,
  output wire [31:0] out_tag
);
  localparam integer LEGAL=LANES>=1 && LANES<=512 && (LANES & (LANES-1))==0;
  generate if (!LEGAL) begin: invalid_parameters
    assign in_ready=0;
    assign out_valid=0;
    assign out_sum=0;
    assign out_error=0;
    assign out_first=0;
    assign out_last=0;
    assign out_tag=0;
    initial $fatal(1,"B1 PARAMETER ERROR: MAC LANES");
  end else begin: implementation
    localparam integer LEVELS=$clog2(LANES);
    reg [8*LANES-1:0] act;
    reg [WEIGHT_BITS-1:0] weights;
    reg [LANES-1:0] mask;
    reg packing;
    reg [LEVELS+1:0] valid_pipe, first_pipe, last_pipe;
    reg [31:0] tag_pipe [0:LEVELS+1];
    wire advance=!valid_pipe[LEVELS+1] || out_ready;
    wire active=rst_n && !flush;
    wire [LANES-1:0] lane_error;
    wire level_error [0:LEVELS];
    wire signed [31:0] level_sum [0:LEVELS];

    // Each table returns all five trits as signed two-bit codes, low digit first.
    function automatic [9:0] radix_codes(input [7:0] byte_value);
      integer d0, d1, d2, d3, d4;
      integer rest_value;
      reg [1:0] c0, c1, c2, c3, c4;
      begin
        // The loop is fully constant at elaboration; no runtime div/mod exists.
        radix_codes=0;
        for (d4=0;d4<3;d4=d4+1)
          for (d3=0;d3<3;d3=d3+1)
            for (d2=0;d2<3;d2=d2+1)
              for (d1=0;d1<3;d1=d1+1)
                for (d0=0;d0<3;d0=d0+1) begin
                  rest_value=d0+3*d1+9*d2+27*d3+81*d4;
                  c0=d0==0 ? 2'b11 : d0==1 ? 2'b00 : 2'b01;
                  c1=d1==0 ? 2'b11 : d1==1 ? 2'b00 : 2'b01;
                  c2=d2==0 ? 2'b11 : d2==1 ? 2'b00 : 2'b01;
                  c3=d3==0 ? 2'b11 : d3==1 ? 2'b00 : 2'b01;
                  c4=d4==0 ? 2'b11 : d4==1 ? 2'b00 : 2'b01;
                  radix_codes=radix_codes |
                    ({10{byte_value==rest_value}} & {c4,c3,c2,c1,c0});
                end
      end
    endfunction

    assign in_ready=active && advance;
    assign out_valid=active && valid_pipe[LEVELS+1];
    assign out_sum=active ? level_sum[LEVELS] : 32'sd0;
    assign out_error=out_valid && level_error[LEVELS];
    assign out_first=out_valid && first_pipe[LEVELS+1];
    assign out_last=out_valid && last_pipe[LEVELS+1];
    assign out_tag=active ? tag_pipe[LEVELS+1] : 32'd0;

    integer p;
    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        act<=0; weights<=0; mask<=0; packing<=0;
        valid_pipe<=0; first_pipe<=0; last_pipe<=0;
        for (p=0;p<LEVELS+2;p=p+1) tag_pipe[p]<=0;
      end else if (flush) begin
        valid_pipe<=0; first_pipe<=0; last_pipe<=0;
      end else if (advance) begin
        valid_pipe[0]<=in_valid;
        first_pipe[0]<=in_first;
        last_pipe[0]<=in_last;
        tag_pipe[0]<=in_tag;
        if (in_valid) begin
          act<=in_act; weights<=in_weights; mask<=in_mask; packing<=in_packing;
        end
        for (p=1;p<LEVELS+2;p=p+1) begin
          valid_pipe[p]<=valid_pipe[p-1];
          first_pipe[p]<=first_pipe[p-1];
          last_pipe[p]<=last_pipe[p-1];
          tag_pipe[p]<=tag_pipe[p-1];
        end
      end
    end

    wire [9:0] decoded [0:RADIX_BYTES-1];
    genvar b, lane, lev, node;
    for (b=0;b<RADIX_BYTES;b=b+1) begin: radix_lookup
      assign decoded[b]=radix_codes(weights[b*8+:8]);
    end
    wire signed [8:0] terms [0:LANES-1];
    for (lane=0;lane<LANES;lane=lane+1) begin: lanes
      localparam integer BYTE_INDEX=lane/5;
      localparam integer DIGIT_INDEX=lane-BYTE_INDEX*5;
      wire [1:0] code=packing ? weights[2*lane+:2] :
        decoded[BYTE_INDEX][2*DIGIT_INDEX+:2];
      wire signed [8:0] operand={act[8*lane+7],act[8*lane+:8]};
      reg signed [8:0] term;
      reg bad;
      assign terms[lane]=term;
      assign lane_error[lane]=bad;
      always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin term<=0; bad<=0; end
        else if (flush) begin term<=0; bad<=0; end
        else if (advance) begin
          bad<=mask[lane] && (packing ? code==2'b10 :
            weights[BYTE_INDEX*8+:8]>=8'd243);
          if (!mask[lane]) term<=0;
          else case (code)
            2'b01: term<=operand;
            2'b11: term<=-operand;
            default: term<=0;
          endcase
        end
      end
    end
    for (lev=0;lev<=LEVELS;lev=lev+1) begin: tree
      localparam integer COUNT=LANES>>lev;
      localparam integer WIDTH=9+lev;
      wire signed [WIDTH-1:0] value [0:COUNT-1];
      wire bad [0:COUNT-1];
      if (lev==0) begin: leaves
        for (node=0;node<COUNT;node=node+1) begin: leaf
          assign value[node]=terms[node];
          assign bad[node]=lane_error[node];
        end
      end else begin: reduction
        for (node=0;node<COUNT;node=node+1) begin: pair
          reg signed [WIDTH-1:0] sum;
          reg pair_bad;
          wire signed [WIDTH-1:0] left=$signed(tree[lev-1].value[2*node]);
          wire signed [WIDTH-1:0] right=$signed(tree[lev-1].value[2*node+1]);
          assign value[node]=sum;
          assign bad[node]=pair_bad;
          always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin sum<=0; pair_bad<=0; end
            else if (flush) begin sum<=0; pair_bad<=0; end
            else if (advance) begin
              sum<=left+right;
              pair_bad<=tree[lev-1].bad[2*node] || tree[lev-1].bad[2*node+1];
            end
          end
        end
      end
      assign level_sum[lev]=$signed(value[0]);
      assign level_error[lev]=bad[0];
    end
  end endgenerate
endmodule
