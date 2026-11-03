module anvil_q3_ht_image_map #(
  parameter NUM_LAYERS=36, HIDDEN_SIZE=2048, INTERMEDIATE_SIZE=11008,
  parameter NUM_Q_HEADS=16, NUM_KV_HEADS=2, HEAD_DIM=128,
  parameter GROUP_SIZE=128, VOCAB_SIZE=151936, MAX_SEQ_LEN=32768
) (
  input wire clk, rst_n, flush,
  input wire req_valid,
  output wire req_ready,
  input wire req_write,
  input wire [3:0] req_kind,
  input wire [31:0] req_layer, req_row, req_col,
  input wire [2:0] req_proj,
  output wire rsp_valid,
  input wire rsp_ready,
  output wire rsp_error, rsp_scratch,
  output wire [32:0] rsp_address,
  output wire [2:0] rsp_bytes,
  output wire [31:0] rsp_inputs, rsp_outputs,
  output wire [32:0] rsp_qweight_base, rsp_qzeros_base, rsp_scales_base
);
  localparam GS=GROUP_SIZE>=8 && GROUP_SIZE<=128 &&
    (GROUP_SIZE&(GROUP_SIZE-1))==0 ? GROUP_SIZE : 8;
  localparam GSHIFT=$clog2(GS);
  localparam [63:0] H=64'(HIDDEN_SIZE), I=64'(INTERMEDIATE_SIZE);
  localparam [63:0] KD=64'(NUM_KV_HEADS)*64'(HEAD_DIM);
  function automatic [63:0] inputs_for(input integer projection);
    inputs_for=projection==6 ? I : H;
  endfunction
  function automatic [63:0] outputs_for(input integer projection);
    outputs_for=projection==1 || projection==2 ? KD :
      projection==4 || projection==5 ? I : H;
  endfunction
  function automatic [63:0] align64(input reg [63:0] value);
    align64=(value+64'd63)&64'hffffffffffffffc0;
  endfunction
  function automatic [63:0] matrix_bytes(input integer kind, projection);
    reg [63:0] n, m, rows, groups;
    begin
      n=inputs_for(projection);
      m=outputs_for(projection);
      rows=(m+7)>>3;
      groups=(n+GS-1)>>GSHIFT;
      case (kind)
        1: matrix_bytes=align64(n*rows*4);
        2: matrix_bytes=align64(groups*rows*4);
        default: matrix_bytes=align64(groups*m*2);
      endcase
    end
  endfunction
  function automatic [63:0] matrix_offset(input integer kind, projection);
    integer p;
    reg [63:0] total;
    begin
      total=0;
      for (p=0;p<7;p=p+1)
        if (p<projection) total=total+matrix_bytes(kind,p);
      matrix_offset=total;
    end
  endfunction
  localparam [63:0] QW_LAYER=matrix_offset(1,7);
  localparam [63:0] QZ_LAYER=matrix_offset(2,7);
  localparam [63:0] SC_LAYER=matrix_offset(3,7);
  localparam [63:0] BIAS_LAYER=(H+2*KD)*2;
  localparam [63:0] NORM_TOTAL=(2*64'(NUM_LAYERS)+1)*H*2;
  localparam [63:0] ROPE_TOTAL=64'(MAX_SEQ_LEN)*64'(HEAD_DIM)*4;
  localparam [63:0] EMBED_TOTAL=64'(VOCAB_SIZE)*H*2;
  localparam LEGAL=NUM_LAYERS>0 && HIDDEN_SIZE>0 && INTERMEDIATE_SIZE>0 &&
    NUM_KV_HEADS>0 && NUM_Q_HEADS==8*NUM_KV_HEADS &&
    HEAD_DIM>0 && (HEAD_DIM&1)==0 && H==64'(NUM_Q_HEADS)*64'(HEAD_DIM) &&
    GROUP_SIZE==GS && (H&(GS-1))==0 && (I&(GS-1))==0 &&
    (H&7)==0 && (I&7)==0 && VOCAB_SIZE>0 &&
    MAX_SEQ_LEN>=1 && MAX_SEQ_LEN<=32768 &&
    64'(NUM_LAYERS)*QW_LAYER<=64'h60000000 &&
    64'(NUM_LAYERS)*QZ_LAYER<=64'h04000000 &&
    64'(NUM_LAYERS)*SC_LAYER<=64'h08000000 &&
    64'(NUM_LAYERS)*BIAS_LAYER<=64'h01000000 &&
    NORM_TOTAL<=64'h01000000 && ROPE_TOTAL<=64'h12000000 &&
    EMBED_TOTAL<=64'h40000000 && H<=64'hffffffff && I<=64'hffffffff;
  reg valid, failed, scratch;
  reg [32:0] address, qw_base, qz_base, sc_base;
  reg [2:0] bytes;
  reg [31:0] n_count, m_count;
  reg [63:0] mapped_address, region_limit, n, m, packed_rows;
  reg [63:0] qw, qz, sc;
  reg bad, is_scratch;
  reg [2:0] element_bytes;
  wire enabled=rst_n && LEGAL && !flush;

  generate if (!LEGAL) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q3_HT PARAMETER ERROR: geometry or persistent image region extent");
  end endgenerate

  always @* begin
    n=inputs_for(req_proj);
    m=outputs_for(req_proj);
    packed_rows=(m+7)>>3;
    qw=64'(req_layer)*QW_LAYER+matrix_offset(1,req_proj);
    qz=64'h60000000+64'(req_layer)*QZ_LAYER+matrix_offset(2,req_proj);
    sc=64'h64000000+64'(req_layer)*SC_LAYER+matrix_offset(3,req_proj);
    mapped_address=0;
    region_limit=0;
    element_bytes=0;
    is_scratch=0;
    bad=!LEGAL;
    case (req_kind)
      0: begin
        mapped_address=64'h80000000+(64'(req_row)*H+64'(req_col))*2;
        region_limit=64'hc0000000;
        element_bytes=2;
        bad=bad || req_row>=VOCAB_SIZE || req_col>=HIDDEN_SIZE ||
          req_layer!=0 || req_proj!=0;
      end
      1: begin
        mapped_address=qw+(64'(req_col)*packed_rows+64'(req_row))*4;
        region_limit=64'h60000000;
        element_bytes=4;
        bad=bad || req_row>=packed_rows || req_col>=n;
      end
      2: begin
        mapped_address=qz+(64'(req_col)*packed_rows+64'(req_row))*4;
        region_limit=64'h64000000;
        element_bytes=4;
        bad=bad || req_row>=packed_rows || req_col>=((n+GS-1)>>GSHIFT);
      end
      3: begin
        mapped_address=sc+(64'(req_col)*m+64'(req_row))*2;
        region_limit=64'h6c000000;
        element_bytes=2;
        bad=bad || req_row>=m || req_col>=((n+GS-1)>>GSHIFT);
      end
      4: begin
        mapped_address=64'h6c000000+64'(req_layer)*BIAS_LAYER+
          (req_proj==0 ? 64'd0 : req_proj==1 ? H*2 : (H+KD)*2)+64'(req_col)*2;
        region_limit=64'h6d000000;
        element_bytes=2;
        bad=bad || req_proj>2 || req_row!=0 || req_col>=m;
      end
      5,6,7: begin
        mapped_address=64'h6d000000+
          (req_kind==7 ? 2*64'(NUM_LAYERS)*H :
           (2*64'(req_layer)+(req_kind==6 ? 1 : 0))*H)*2+64'(req_col)*2;
        region_limit=64'h6e000000;
        element_bytes=2;
        bad=bad || req_row!=0 || req_col>=H || req_proj!=0 ||
          (req_kind==7 && req_layer!=0);
      end
      8: begin
        is_scratch=1;
        element_bytes=4;
        bad=bad || req_layer!=0 || req_proj!=0 || req_row>14;
      end
      11: begin
        mapped_address=64'h6e000000+
          (64'(req_row)*64'(HEAD_DIM)+64'(req_col))*4;
        region_limit=64'h80000000;
        element_bytes=4;
        bad=bad || req_row>=MAX_SEQ_LEN || req_col>=HEAD_DIM ||
          req_layer!=0 || req_proj!=0;
      end
      default: bad=1;
    endcase
    if (req_kind>=1 && req_kind<=6)
      bad=bad || req_layer>=NUM_LAYERS;
    if (req_kind>=1 && req_kind<=4) bad=bad || req_proj>6;
    if (!is_scratch)
      bad=bad || req_write || mapped_address+element_bytes>region_limit ||
        mapped_address>=64'h200000000;
  end

  assign req_ready=enabled && (!valid || rsp_ready);
  assign rsp_valid=enabled && valid;
  assign rsp_error=rsp_valid && failed;
  assign rsp_scratch=rsp_valid && !failed && scratch;
  assign rsp_address=rsp_valid && !failed ? address : 33'd0;
  assign rsp_bytes=rsp_valid && !failed ? bytes : 3'd0;
  assign rsp_inputs=rsp_valid && !failed ? n_count : 32'd0;
  assign rsp_outputs=rsp_valid && !failed ? m_count : 32'd0;
  assign rsp_qweight_base=rsp_valid && !failed ? qw_base : 33'd0;
  assign rsp_qzeros_base=rsp_valid && !failed ? qz_base : 33'd0;
  assign rsp_scales_base=rsp_valid && !failed ? sc_base : 33'd0;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      valid<=0; failed<=0; scratch<=0; address<=0; bytes<=0;
      n_count<=0; m_count<=0; qw_base<=0; qz_base<=0; sc_base<=0;
    end else if (flush) valid<=0;
    else if (req_ready) begin
      valid<=req_valid;
      if (req_valid) begin
        failed<=bad;
        scratch<=is_scratch;
        address<=mapped_address[32:0];
        bytes<=element_bytes;
        n_count<=n[31:0]; m_count<=m[31:0];
        qw_base<=qw[32:0]; qz_base<=qz[32:0]; sc_base<=sc[32:0];
      end
    end
  end
endmodule
