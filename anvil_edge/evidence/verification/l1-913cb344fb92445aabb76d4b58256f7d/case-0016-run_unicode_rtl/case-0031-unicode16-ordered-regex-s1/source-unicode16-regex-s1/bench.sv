
module bench;
  reg clk=0;
  reg rst_n;
  always #5 clk=~clk;
  reg start=0,in_valid=0,in_last=0,out_ready=0;
  reg [31:0] in_value=0;
  wire in_ready,out_valid,out_last,busy,done,error;
  wire [63:0] out_value;
  wire [7:0] error_code;
  wire tbl_req_valid,tbl_rsp_ready;
  wire [63:0] tbl_req_addr;
  reg tbl_req_ready=0,tbl_rsp_valid=0,tbl_rsp_error=0;
  reg [31:0] tbl_rsp_data=0;
  
  wire [31:0] span_start,span_end;
  assign out_value={span_start,span_end};
  anvil_edge_tagged_dfa #(.MAX_SPAN_BYTES(4096)) dut(
    .clk(clk),.rst_n(rst_n),.start(start),.config_valid(1'b1),
    .cfg_ranges_base(64'h1000),.cfg_states_base(64'h40000),
    .cfg_transitions_base(64'h50000),.cfg_tag_ops_base(64'h60000),
    .cfg_accepts_base(64'h70000),.cfg_range_count(32'd2292),
    .cfg_class_count(32'd16),.cfg_state_count(32'd17),
    .cfg_transition_count(32'd289),
    .cfg_tag_op_count(32'd166),
    .cfg_accept_count(32'd21),
    .cfg_start_state(32'd0),.cfg_dead_state(32'd1),
    .cfg_tag_register_count(32'd32),
    .in_valid(in_valid),.in_ready(in_ready),.in_scalar(in_value),.in_last(in_last),
    .out_valid(out_valid),.out_ready(out_ready),.out_start(span_start),
    .out_end(span_end),.out_last(out_last),.busy(busy),.done(done),
    .error(error),.error_code(error_code),.tbl_req_valid(tbl_req_valid),
    .tbl_req_ready(tbl_req_ready),.tbl_req_addr(tbl_req_addr),
    .tbl_rsp_valid(tbl_rsp_valid),.tbl_rsp_ready(tbl_rsp_ready),
    .tbl_rsp_data(tbl_rsp_data),.tbl_rsp_error(tbl_rsp_error));

  reg [63:0] expected[0:174];
  reg [31:0] rng=1;
  reg outstanding=0,req_held=0,out_held=0;
  reg [63:0] pending_addr=0,held_addr=0;
  reg [64:0] held_out=0;
  integer requests=0,responses=0,outputs=0,completions=0,cycle=0,delay_count=0;
  integer req_wait=0,out_wait=0,request_stalls=0,output_stalls=0,comparisons=0;
  integer inputs=0;
  reg [31:0] table_words[0:11139];
  initial $readmemh("evidence/verification/l1-913cb344fb92445aabb76d4b58256f7d/case-0016-run_unicode_rtl/case-0031-unicode16-ordered-regex-s1/source-unicode16-regex-s1-table.hex",table_words);
  function automatic [31:0] memory(input [63:0] address);
    begin
      if (address[1:0]!=0) $fatal(1,"TEXT_UNALIGNED_READ");
if (address>=64'h1020 && address<64'h9f60) memory=table_words[0+((address-64'h1020)>>2)];
else if (address>=64'h40020 && address<64'h40130) memory=table_words[9168+((address-64'h40020)>>2)];
else if (address>=64'h50020 && address<64'h51230) memory=table_words[9236+((address-64'h50020)>>2)];
else if (address>=64'h60020 && address<64'h60a80) memory=table_words[10392+((address-64'h60020)>>2)];
else if (address>=64'h70020 && address<64'h70170) memory=table_words[11056+((address-64'h70020)>>2)];
else $fatal(1,"TEXT_UNMAPPED_READ address=%h",address);
    end
  endfunction
  task automatic reset_check;
    begin
      if ({in_ready,out_valid,out_value,out_last,busy,done,error,error_code,
           tbl_req_valid,tbl_req_addr,tbl_rsp_ready} !== '0)
        $fatal(1,"TEXT_RESET t=%0t",$time);
    end
  endtask
  always @(posedge clk or negedge clk) if (!rst_n) reset_check();
  always @(negedge clk) begin
    if (rst_n) begin
      rng=rng ^ (rng<<13); rng=rng ^ (rng>>17); rng=rng ^ (rng<<5);
      tbl_req_ready=req_wait>=2 && rng[0] && cycle%5!=0;
      out_ready=out_wait>=3 && rng[1] && cycle%7!=0;
      if (outstanding && !tbl_rsp_valid) begin
        if (delay_count==0) begin
          tbl_rsp_valid<=1; tbl_rsp_data=memory(pending_addr);
          tbl_rsp_error=0;
        end else delay_count=delay_count-1;
      end
    end
  end
  always @(posedge clk) begin
    cycle=cycle+1;
    if (rst_n) begin
      if ((^{in_ready,out_valid,out_value,out_last,busy,done,error,error_code,
             tbl_req_valid,tbl_req_addr,tbl_rsp_ready})===1'bx)
        $fatal(1,"TEXT_XZ");
      if (req_held && (!tbl_req_valid || tbl_req_addr!==held_addr))
        $fatal(1,"TEXT_REQUEST_STABILITY");
      if (out_held && (!out_valid || {out_last,out_value}!==held_out))
        $fatal(1,"TEXT_OUTPUT_STABILITY");
      req_held=tbl_req_valid && !tbl_req_ready;
      out_held=out_valid && !out_ready;
      held_addr=tbl_req_addr; held_out={out_last,out_value};
      if (req_held) request_stalls=request_stalls+1;
      if (out_held) output_stalls=output_stalls+1;
      if (tbl_req_valid) req_wait=req_wait+1;
      if (out_valid) out_wait=out_wait+1;
      if (in_valid && in_ready) inputs=inputs+1;
      if (tbl_rsp_valid && tbl_rsp_ready) begin
        if (!outstanding) $fatal(1,"TEXT_ORPHAN_RESPONSE");
        outstanding=0; responses=responses+1; tbl_rsp_valid<=0;
      end
      if (tbl_req_valid && tbl_req_ready) begin
        if (outstanding || tbl_req_addr[1:0]!=0)
          $fatal(1,"TEXT_REQUEST_CONSERVATION");
        pending_addr=tbl_req_addr; outstanding=1; delay_count=1+rng[4:2];
        requests=requests+1; comparisons=comparisons+1; req_wait=0;
      end
      if (out_valid && out_ready) begin
        if (outputs>=175 || out_value!==expected[outputs] ||
            out_last!==(outputs==175-1))
          $fatal(1,"TEXT_VECTOR item=%0d expected=%h observed=%h last=%b",
                 outputs,expected[outputs],out_value,out_last);
        outputs=outputs+1; comparisons=comparisons+1; out_wait=0;
      end
      if (done) begin
        if (error || outputs!=175 || outstanding || completions!=0)
          $fatal(1,"TEXT_PREMATURE_DONE");
        completions=completions+1;
      end
    end
  end
  task automatic tick; begin @(posedge clk); #1; end endtask
  task automatic item(input [31:0] value,input bit last);
    begin
      if (!error) begin
        @(negedge clk); #1; in_valid=1; in_value=value; in_last=last;
        do begin @(posedge clk); end while (!in_ready && !error);
        #1; @(negedge clk); #1; in_valid=0;
      end
    end
  endtask
  initial begin
    rst_n=0; #0; reset_check();
    expected[0]=64'h1;
expected[1]=64'h100000003;
expected[2]=64'h300000006;
expected[3]=64'h600000009;
expected[4]=64'h90000000d;
expected[5]=64'hd0000000f;
expected[6]=64'hf00000013;
expected[7]=64'h1300000015;
expected[8]=64'h1500000018;
expected[9]=64'h180000001b;
expected[10]=64'h1b0000001f;
expected[11]=64'h1f00000022;
expected[12]=64'h2200000024;
expected[13]=64'h2400000026;
expected[14]=64'h2600000028;
expected[15]=64'h2800000029;
expected[16]=64'h290000002b;
expected[17]=64'h2b0000002c;
expected[18]=64'h2c0000002e;
expected[19]=64'h2e00000030;
expected[20]=64'h3000000032;
expected[21]=64'h3200000034;
expected[22]=64'h3400000036;
expected[23]=64'h3600000037;
expected[24]=64'h3700000039;
expected[25]=64'h390000003b;
expected[26]=64'h3b0000003d;
expected[27]=64'h3d0000003e;
expected[28]=64'h3e00000041;
expected[29]=64'h4100000045;
expected[30]=64'h4500000049;
expected[31]=64'h490000004b;
expected[32]=64'h4b0000004e;
expected[33]=64'h4e00000050;
expected[34]=64'h5000000052;
expected[35]=64'h5200000053;
expected[36]=64'h5300000054;
expected[37]=64'h5400000055;
expected[38]=64'h5500000056;
expected[39]=64'h5600000057;
expected[40]=64'h5700000059;
expected[41]=64'h590000005b;
expected[42]=64'h5b00000062;
expected[43]=64'h6200000064;
expected[44]=64'h6400000066;
expected[45]=64'h660000006b;
expected[46]=64'h6b00000074;
expected[47]=64'h7400000075;
expected[48]=64'h7500000077;
expected[49]=64'h7700000078;
expected[50]=64'h780000007a;
expected[51]=64'h7a0000007c;
expected[52]=64'h7c0000007e;
expected[53]=64'h7e00000081;
expected[54]=64'h8100000082;
expected[55]=64'h8200000084;
expected[56]=64'h8400000086;
expected[57]=64'h8600000089;
expected[58]=64'h890000008c;
expected[59]=64'h8c0000008f;
expected[60]=64'h8f00000092;
expected[61]=64'h9200000095;
expected[62]=64'h9500000098;
expected[63]=64'h980000009b;
expected[64]=64'h9b0000009e;
expected[65]=64'h9e000000a2;
expected[66]=64'ha2000000a6;
expected[67]=64'ha6000000aa;
expected[68]=64'haa000000ae;
expected[69]=64'hae000000b2;
expected[70]=64'hb2000000b6;
expected[71]=64'hb6000000ba;
expected[72]=64'hba000000be;
expected[73]=64'hbe000000c2;
expected[74]=64'hc2000000c6;
expected[75]=64'hc6000000ca;
expected[76]=64'hca000000ce;
expected[77]=64'hce000000d2;
expected[78]=64'hd2000000d6;
expected[79]=64'hd6000000da;
expected[80]=64'hda000000de;
expected[81]=64'hde000000e2;
expected[82]=64'he2000000e6;
expected[83]=64'he6000000ea;
expected[84]=64'hea000000ee;
expected[85]=64'hee000000f2;
expected[86]=64'hf2000000f6;
expected[87]=64'hf6000000fa;
expected[88]=64'hfa000000fe;
expected[89]=64'hfe00000102;
expected[90]=64'h10200000106;
expected[91]=64'h1060000010a;
expected[92]=64'h10a0000010e;
expected[93]=64'h10e00000112;
expected[94]=64'h11200000116;
expected[95]=64'h11600000117;
expected[96]=64'h1170000011a;
expected[97]=64'h11a0000011b;
expected[98]=64'h11b0000011e;
expected[99]=64'h11e00000122;
expected[100]=64'h12200000126;
expected[101]=64'h1260000012a;
expected[102]=64'h12a0000012e;
expected[103]=64'h12e00000132;
expected[104]=64'h13200000136;
expected[105]=64'h1360000013a;
expected[106]=64'h13a0000013e;
expected[107]=64'h13e00000142;
expected[108]=64'h14200000146;
expected[109]=64'h1460000014a;
expected[110]=64'h14a0000014e;
expected[111]=64'h14e00000152;
expected[112]=64'h15200000156;
expected[113]=64'h1560000015a;
expected[114]=64'h15a0000015e;
expected[115]=64'h15e00000162;
expected[116]=64'h16200000166;
expected[117]=64'h1660000016a;
expected[118]=64'h16a0000016e;
expected[119]=64'h16e00000172;
expected[120]=64'h17200000176;
expected[121]=64'h1760000017a;
expected[122]=64'h17a0000017f;
expected[123]=64'h17f00000184;
expected[124]=64'h18400000189;
expected[125]=64'h1890000018e;
expected[126]=64'h18e00000193;
expected[127]=64'h19300000194;
expected[128]=64'h19400000198;
expected[129]=64'h19800000199;
expected[130]=64'h1990000019d;
expected[131]=64'h19d000001a2;
expected[132]=64'h1a2000001a7;
expected[133]=64'h1a7000001ac;
expected[134]=64'h1ac000001b1;
expected[135]=64'h1b1000001b6;
expected[136]=64'h1b6000001bb;
expected[137]=64'h1bb000001c0;
expected[138]=64'h1c0000001c5;
expected[139]=64'h1c5000001ca;
expected[140]=64'h1ca000001cf;
expected[141]=64'h1cf000001d4;
expected[142]=64'h1d4000001d9;
expected[143]=64'h1d9000001de;
expected[144]=64'h1de000001e3;
expected[145]=64'h1e3000001e8;
expected[146]=64'h1e8000001ed;
expected[147]=64'h1ed000001f2;
expected[148]=64'h1f2000001f7;
expected[149]=64'h1f7000001fc;
expected[150]=64'h1fc00000201;
expected[151]=64'h20100000206;
expected[152]=64'h2060000020b;
expected[153]=64'h20b00000210;
expected[154]=64'h21000000215;
expected[155]=64'h2150000021a;
expected[156]=64'h21a0000021f;
expected[157]=64'h21f00000224;
expected[158]=64'h22400000229;
expected[159]=64'h2290000022e;
expected[160]=64'h22e00000233;
expected[161]=64'h23300000238;
expected[162]=64'h2380000023d;
expected[163]=64'h23d00000242;
expected[164]=64'h24200000247;
expected[165]=64'h2470000024c;
expected[166]=64'h24c00000251;
expected[167]=64'h25100000256;
expected[168]=64'h2560000025b;
expected[169]=64'h25b00000260;
expected[170]=64'h26000000265;
expected[171]=64'h2650000026a;
expected[172]=64'h26a0000026f;
expected[173]=64'h26f00000276;
expected[174]=64'h2760000027b;
    repeat (2) tick();
    @(negedge clk); #1; rst_n=1; start=1; tick();
    @(negedge clk); #1; start=0;
    item(32'h49,0);
item(32'h27,0);
item(32'h6d,0);
item(32'h20,0);
item(32'h57,0);
item(32'h45,0);
item(32'h27,0);
item(32'h52,0);
item(32'h45,0);
item(32'h20,0);
item(32'h73,0);
item(32'h68,0);
item(32'h65,0);
item(32'h27,0);
item(32'h64,0);
item(32'h20,0);
item(32'h63,0);
item(32'h61,0);
item(32'h6e,0);
item(32'h27,0);
item(32'h74,0);
item(32'h20,0);
item(32'h77,0);
item(32'h65,0);
item(32'h27,0);
item(32'h6c,0);
item(32'h6c,0);
item(32'h20,0);
item(32'h79,0);
item(32'h6f,0);
item(32'h75,0);
item(32'h27,0);
item(32'h76,0);
item(32'h65,0);
item(32'h20,0);
item(32'h27,0);
item(32'h17f,0);
item(32'h20,0);
item(32'h27,0);
item(32'h53,0);
item(32'h20,0);
item(32'h27,0);
item(32'h54,0);
item(32'h20,0);
item(32'h27,0);
item(32'h52,0);
item(32'h45,0);
item(32'h20,0);
item(32'h27,0);
item(32'h56,0);
item(32'h45,0);
item(32'h20,0);
item(32'h27,0);
item(32'h4d,0);
item(32'h20,0);
item(32'h27,0);
item(32'h4c,0);
item(32'h4c,0);
item(32'h20,0);
item(32'h27,0);
item(32'h44,0);
item(32'h20,0);
item(32'hdf,0);
item(32'h20,0);
item(32'hfb05,0);
item(32'h20,0);
item(32'hfb06,0);
item(32'h20,0);
item(32'h27,0);
item(32'h17f,0);
item(32'h54,0);
item(32'h20,0);
item(32'h27,0);
item(32'h73,0);
item(32'h54,0);
item(32'h20,0);
item(32'h31,0);
item(32'h32,0);
item(32'h33,0);
item(32'h20,0);
item(32'h661,0);
item(32'h662,0);
item(32'h20,0);
item(32'h4e2d,0);
item(32'h6587,0);
item(32'h20,0);
item(32'h65,0);
item(32'h301,0);
item(32'h20,0);
item(32'h1f600,0);
item(32'h20,0);
item(32'h11935,0);
item(32'h11930,0);
item(32'h20,0);
item(32'h20,0);
item(32'h61,0);
item(32'h20,0);
item(32'h20,0);
item(32'h21,0);
item(32'h20,0);
item(32'h9,0);
item(32'h20,0);
item(32'h78,0);
item(32'h20,0);
item(32'hd,0);
item(32'ha,0);
item(32'h0,0);
item(32'h20,0);
item(32'h8,0);
item(32'h20,0);
item(32'h74,0);
item(32'h20,0);
item(32'h301,0);
item(32'h20,0);
item(32'h315,0);
item(32'h20,0);
item(32'h380,0);
item(32'h20,0);
item(32'h385,0);
item(32'h20,0);
item(32'h5b0,0);
item(32'h20,0);
item(32'h64e,0);
item(32'h20,0);
item(32'h712,0);
item(32'h20,0);
item(32'h72f,0);
item(32'h20,0);
item(32'h816,0);
item(32'h20,0);
item(32'h819,0);
item(32'h20,0);
item(32'h900,0);
item(32'h20,0);
item(32'h903,0);
item(32'h20,0);
item(32'h9c7,0);
item(32'h20,0);
item(32'h9c8,0);
item(32'h20,0);
item(32'ha3a,0);
item(32'h20,0);
item(32'ha3b,0);
item(32'h20,0);
item(32'habe,0);
item(32'h20,0);
item(32'hac5,0);
item(32'h20,0);
item(32'hb4b,0);
item(32'h20,0);
item(32'hb4c,0);
item(32'h20,0);
item(32'hbc3,0);
item(32'h20,0);
item(32'hbc5,0);
item(32'h20,0);
item(32'hc60,0);
item(32'h20,0);
item(32'hc61,0);
item(32'h20,0);
item(32'hcf0,0);
item(32'h20,0);
item(32'hdbc,0);
item(32'h20,0);
item(32'he8c,0);
item(32'h20,0);
item(32'hea3,0);
item(32'h20,0);
item(32'hf48,0);
item(32'h20,0);
item(32'h1062,0);
item(32'h20,0);
item(32'h1064,0);
item(32'h20,0);
item(32'h12b2,0);
item(32'h20,0);
item(32'h12b5,0);
item(32'h20,0);
item(32'h1700,0);
item(32'h20,0);
item(32'h1711,0);
item(32'h20,0);
item(32'h1820,0);
item(32'h20,0);
item(32'h1878,0);
item(32'h20,0);
item(32'h1a5f,0);
item(32'h20,0);
item(32'h1bb0,0);
item(32'h20,0);
item(32'h1bb9,0);
item(32'h20,0);
item(32'h1c89,0);
item(32'h20,0);
item(32'h1c8a,0);
item(32'h20,0);
item(32'h1cf8,0);
item(32'h20,0);
item(32'h1cf9,0);
item(32'h20,0);
item(32'h1f7e,0);
item(32'h20,0);
item(32'h1f7f,0);
item(32'h20,0);
item(32'h207a,0);
item(32'h20,0);
item(32'h207e,0);
item(32'h20,0);
item(32'h2129,0);
item(32'h20,0);
item(32'h2d6f,0);
item(32'h20,0);
item(32'h3031,0);
item(32'h20,0);
item(32'h3035,0);
item(32'h20,0);
item(32'h4e00,0);
item(32'h20,0);
item(32'ha48c,0);
item(32'h20,0);
item(32'ha806,0);
item(32'h20,0);
item(32'ha97d,0);
item(32'h20,0);
item(32'ha97f,0);
item(32'h20,0);
item(32'haab9,0);
item(32'h20,0);
item(32'haabd,0);
item(32'h20,0);
item(32'hac00,0);
item(32'h20,0);
item(32'hd7a3,0);
item(32'h20,0);
item(32'hfdf0,0);
item(32'h20,0);
item(32'hfdfb,0);
item(32'h20,0);
item(32'h10027,0);
item(32'h20,0);
item(32'h10380,0);
item(32'h20,0);
item(32'h1039d,0);
item(32'h20,0);
item(32'h105f4,0);
item(32'h20,0);
item(32'h105ff,0);
item(32'h20,0);
item(32'h108fb,0);
item(32'h20,0);
item(32'h108ff,0);
item(32'h20,0);
item(32'h10a7f,0);
item(32'h20,0);
item(32'h10d4a,0);
item(32'h20,0);
item(32'h10d65,0);
item(32'h20,0);
item(32'h11047,0);
item(32'h20,0);
item(32'h11051,0);
item(32'h20,0);
item(32'h11183,0);
item(32'h20,0);
item(32'h111b2,0);
item(32'h20,0);
item(32'h1129f,0);
item(32'h20,0);
item(32'h112a8,0);
item(32'h20,0);
item(32'h1135d,0);
item(32'h20,0);
item(32'h11361,0);
item(32'h20,0);
item(32'h1144b,0);
item(32'h20,0);
item(32'h1144f,0);
item(32'h20,0);
item(32'h116b6,0);
item(32'h20,0);
item(32'h11930,0);
item(32'h20,0);
item(32'h11935,0);
item(32'h20,0);
item(32'h1193f,0);
item(32'h20,0);
item(32'h11be1,0);
item(32'h20,0);
item(32'h11bef,0);
item(32'h20,0);
item(32'h11d60,0);
item(32'h20,0);
item(32'h11d65,0);
item(32'h20,0);
item(32'h1246f,0);
item(32'h20,0);
item(32'h1247f,0);
item(32'h20,0);
item(32'h16b44,0);
item(32'h20,0);
item(32'h16b4f,0);
item(32'h20,0);
item(32'h18d09,0);
item(32'h20,0);
item(32'h1afef,0);
item(32'h20,0);
item(32'h1d167,0);
item(32'h20,0);
item(32'h1d169,0);
item(32'h20,0);
item(32'h1d4c4,0);
item(32'h20,0);
item(32'h1d78a,0);
item(32'h20,0);
item(32'h1d7a8,0);
item(32'h20,0);
item(32'h1e030,0);
item(32'h20,0);
item(32'h1e090,0);
item(32'h20,0);
item(32'h1e0ff,0);
item(32'h20,0);
item(32'h1e4d0,0);
item(32'h20,0);
item(32'h1e4ec,0);
item(32'h20,0);
item(32'h1e8d0,0);
item(32'h20,0);
item(32'h1e8d6,0);
item(32'h20,0);
item(32'h1ee42,0);
item(32'h20,0);
item(32'h1ee7f,0);
item(32'h20,0);
item(32'h1f600,0);
item(32'h20,0);
item(32'h10ffff,0);
item(32'hd,0);
item(32'ha,0);
item(32'h9,0);
item(32'ha0,0);
item(32'h20,0);
item(32'h20,1);
    if (8'h00!=0) begin
      while (!error && completions==0) tick();
      repeat (10) begin
        tick();
        if (error!==1 || error_code!==8'h00 || done!==0 ||
            out_valid!==0 || in_ready!==0)
          $fatal(1,"TEXT_ERROR expected=%h observed=%h",8'h00,error_code);
      end
      if (outputs!=175 || completions!=0 || outstanding)
        $fatal(1,"TEXT_ERROR_COUNTS");
    end else begin
      while (completions==0 && !error) tick();
      repeat (10) tick();
      if (error || completions!=1 || outputs!=175 ||
          responses!=requests || outstanding || busy || inputs!=343)
        $fatal(1,"TEXT_COUNTS inputs=%0d requests=%0d responses=%0d outputs=%0d error=%h",
               inputs,requests,responses,outputs,error_code);
    end
    if ((requests>0 && request_stalls==0) || (175>0 && output_stalls==0))
      $fatal(1,"TEXT_REQUIRED_STALLS");
    comparisons=comparisons+1;
    if (comparisons!=requests+175+1) $fatal(1,"TEXT_COMPARISONS");
    $display("TEXT_COUNTS inputs=%0d requests=%0d responses=%0d outputs=%0d",
             inputs,requests,responses,outputs);
    $display("COMPARED %0d",comparisons); $finish;
  end
  initial begin
    repeat (5000000) @(posedge clk); $fatal(1,"TEXT_CYCLE_BOUND");
  end
endmodule
