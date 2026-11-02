package anvil_q1_ht3_layout_pkg;
  // These functions are for elaboration constants, not runtime address generation.
  function automatic integer exact_groups(input integer extent, input integer size);
    reg [32:0] remainder_value;
    reg [31:0] quotient;
    integer bit_index;
    begin
      remainder_value = 0;
      quotient = 0;
      if (extent > 0 && size > 0) begin
        for (bit_index = 31; bit_index >= 0; bit_index = bit_index - 1) begin
          remainder_value = {remainder_value[31:0], extent[bit_index]};
          if (remainder_value >= size) begin
            remainder_value = remainder_value - size;
            quotient[bit_index] = 1;
          end
        end
      end
      exact_groups = quotient;
    end
  endfunction

  function automatic integer integral_head_ratio(input integer q, input integer k);
    integer n;
    begin
      integral_head_ratio = 0;
      for (n = 1; n <= 14; n = n + 1)
        if (n*k == q) integral_head_ratio = n;
    end
  endfunction

  function automatic geometry_legal(
    input integer layers, hidden_size, intermediate_size, q_heads, kv_heads,
    input integer head_dim, group_size, vocab_size, sequence_length
  );
    begin
      geometry_legal = layers >= 1 && layers <= 24 &&
        hidden_size >= 8 && hidden_size <= 896 && (hidden_size & 7) == 0 &&
        intermediate_size >= 8 && intermediate_size <= 4864 &&
        (intermediate_size & 7) == 0 && q_heads >= 1 && q_heads <= 14 &&
        kv_heads >= 1 && kv_heads <= 2 &&
        integral_head_ratio(q_heads, kv_heads) != 0 &&
        head_dim >= 2 && head_dim <= 64 && (head_dim & 1) == 0 &&
        hidden_size == q_heads*head_dim && ((kv_heads*head_dim) & 7) == 0 &&
        group_size >= 1 && group_size <= hidden_size &&
        exact_groups(hidden_size, group_size)*group_size == hidden_size &&
        exact_groups(intermediate_size, group_size)*group_size == intermediate_size &&
        vocab_size >= 1 && vocab_size <= 151936 &&
        sequence_length >= 1 && sequence_length <= 32768;
    end
  endfunction

  function automatic integer projection_scale_entries(
    input integer projection, hidden_size, intermediate_size, kv_columns, group_size
  );
    integer rows, inputs;
    begin
      rows = hidden_size;
      inputs = hidden_size;
      case (projection)
        1, 2: rows = kv_columns;
        4, 5: rows = intermediate_size;
        6: inputs = intermediate_size;
        default: begin end
      endcase
      projection_scale_entries = projection >= 0 && projection < 7 ?
        rows*exact_groups(inputs, group_size) : 0;
    end
  endfunction

  function automatic integer layer_scale_entries(
    input integer hidden_size, intermediate_size, kv_columns, group_size
  );
    integer projection, entries;
    begin
      entries = 0;
      for (projection = 0; projection < 7; projection = projection + 1)
        entries = entries + projection_scale_entries(projection, hidden_size,
          intermediate_size, kv_columns, group_size);
      layer_scale_entries = entries;
    end
  endfunction

  function automatic integer projection_scale_offset(
    input integer projection, hidden_size, intermediate_size, kv_columns, group_size
  );
    integer p, entries;
    begin
      entries = 0;
      for (p = 0; p < 7; p = p + 1)
        if (p < projection) entries = entries +
          projection_scale_entries(p, hidden_size, intermediate_size, kv_columns, group_size);
      projection_scale_offset = entries*4;
    end
  endfunction
endpackage
