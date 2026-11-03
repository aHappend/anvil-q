package anvil_q2_ht_int_pkg;
  localparam [3:0] M_ADD=0, M_MUL64=1, M_UDIV=2, M_RDIV=3,
    M_SQRT=4, M_ROUND=5, M_MUL32=6, M_SUB=7;

  function automatic signed [127:0] sx32(input [31:0] value);
    sx32={{96{value[31]}},value};
  endfunction

  function automatic signed [127:0] sx64(input [63:0] value);
    sx64={{64{value[63]}},value};
  endfunction

  function automatic [31:0] clamp32(input signed [127:0] value);
    begin
      if (!value[127] && (|value[126:31])) clamp32=32'h7fffffff;
      else if (value[127] && !(&value[126:31])) clamp32=32'h80000000;
      else clamp32=value[31:0];
    end
  endfunction
endpackage
