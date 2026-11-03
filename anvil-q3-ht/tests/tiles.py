"""Bank-interleaved tile storage checked solely at its public transfers."""


TILE_TB = r"""
module verify_tiles;
  localparam B=16, S=@SLOTS@, E=64;
  reg clk=0; always #5 clk=~clk;
  reg rst_n=0, flush=0, alloc_valid=0, write_valid=0, seal_valid=0, activate_valid=0;
  wire alloc_ready, write_ready, seal_ready, activate_ready, operand_valid, operand_last;
  wire [1:0] alloc_slot;
  reg [31:0] alloc_entries=0, write_entry=0;
  reg [159:0] alloc_meta=0, write_meta=0, seal_meta=0, activate_meta=0;
  reg [1:0] write_slot=0, seal_slot=0, activate_slot=0;
  reg [3:0] write_bank=0;
  reg [63:0] write_q=0, write_z=0;
  reg [255:0] write_scale=0;
  reg [15:0] write_mask=0;
  reg [511:0] write_activation=0;
  reg operand_ready=0;
  wire [B*64-1:0] operand_q, operand_z;
  wire [B*256-1:0] operand_scale;
  wire [B*16-1:0] operand_mask;
  wire [511:0] operand_activation;
  wire [159:0] operand_meta;
  wire [31:0] operand_entry;
  wire [S*2-1:0] slot_states;
  wire idle, fault;
  anvil_q3_ht_tile_buffers #(.TILE_SLOTS(S)) dut(.*);
  integer cycle=0, compared=0, completed=0, overlap=0, output_stalls=0;
  integer current_id=0, current_entry=0, activated_at=0, active_owner=0;
  integer cancellations=0, rejected=0, allocations=0, bank, lane;
  reg checking=0, random_consumer=0, held=0;
  reg [B*400+704:0] held_output;
  reg [31:0] rng=@SEED@;
  reg [1:0] owners [0:S-1];
  integer owner_ids [0:S-1];
  function automatic [31:0] next_random(input [31:0] x);
    reg [31:0] y;
    begin y=x^(x<<13); y=y^(y>>17); next_random=y^(y<<5); end
  endfunction
  function automatic [3:0] qvalue(input integer id, b, e, l);
    qvalue=4'(id+b*3+e+l);
  endfunction
  function automatic [3:0] zvalue(input integer id, b, e, l);
    zvalue=4'(id*3+b+e*5+l*7);
  endfunction
  function automatic [15:0] scale_value(input integer b, e, l);
    scale_value=16'h3000+16'(b+e+l);
  endfunction
  function automatic [31:0] activation_value(input integer id, e, l);
    activation_value=32'(id*100003+e*37-l*104729);
  endfunction
  task reset_check;
    begin
      if ({alloc_ready,alloc_slot,write_ready,seal_ready,activate_ready,operand_valid,
           operand_q,operand_z,operand_scale,operand_mask,operand_activation,operand_meta,
           operand_entry,operand_last,slot_states,idle,fault}
          !== (B*400+S*2+714)'(0)) $fatal(1,"TILE_RESET_XZ");
    end
  endtask
  always @(posedge clk) begin
    cycle=cycle+1;
    if (!rst_n) reset_check();
    else if (flush) begin checking=0; held=0; end
    else if (checking) begin
      if (cycle>100000) $fatal(1,"TILE_PROGRESS");
      if (fault!==0) $fatal(1,"TILE_UNEXPECTED_FAULT");
      if (held && {operand_q,operand_z,operand_scale,operand_mask,operand_activation,
                   operand_meta,operand_entry,operand_last} !== held_output)
        $fatal(1,"TILE_OPERAND_STABILITY");
      held=operand_valid && !operand_ready;
      held_output={operand_q,operand_z,operand_scale,operand_mask,operand_activation,
                   operand_meta,operand_entry,operand_last};
      if (held) output_stalls=output_stalls+1;
      if (operand_valid) begin
        if (cycle<activated_at+2 || operand_meta!==160'(current_id) ||
            operand_entry!==32'(current_entry) || operand_last!==(current_entry==E-1) ||
            slot_states[active_owner*2+:2]!==2'd3)
          $fatal(1,"TILE_REGISTERED_OWNERSHIP");
        for (bank=0;bank<B;bank=bank+1)
          for (lane=0;lane<16;lane=lane+1)
            if (operand_q[bank*64+lane*4+:4]!==qvalue(current_id,bank,current_entry,lane) ||
                operand_z[bank*64+lane*4+:4]!==zvalue(current_id,bank,current_entry,lane) ||
                operand_scale[bank*256+lane*16+:16]!==scale_value(bank,current_entry,lane) ||
                operand_mask[bank*16+lane]!==1'(lane%3!=0))
              $fatal(1,"TILE_BANK_LANE_DATA id=%0d slot=%0d bank=%0d lane=%0d entry=%0d q=%h/%h z=%h/%h scale=%h/%h mask=%b/%b bank0_q=%h bank0_scale=%h bank0_mask=%h",
                     current_id,active_owner,bank,lane,current_entry,
                     operand_q[bank*64+lane*4+:4],qvalue(current_id,bank,current_entry,lane),
                     operand_z[bank*64+lane*4+:4],zvalue(current_id,bank,current_entry,lane),
                     operand_scale[bank*256+lane*16+:16],scale_value(bank,current_entry,lane),
                     operand_mask[bank*16+lane],1'(lane%3!=0),
                     operand_q[0+:64],operand_scale[0+:256],operand_mask[0+:16]);
        for (lane=0;lane<16;lane=lane+1)
          if (operand_activation[lane*32+:32]!==activation_value(current_id,current_entry,lane))
            $fatal(1,"TILE_ACTIVATION_OWNERSHIP");
        if (operand_ready) begin
          compared=compared+B*16; current_entry=current_entry+1;
          if (write_valid && write_ready) overlap=overlap+1;
          if (operand_last) begin
            completed=completed+1; checking=0;
            #1;
            if (slot_states[active_owner*2+:2]!==2'd0)
              $fatal(1,"TILE_FINAL_RELEASE");
          end
        end
      end
    end
  end
  always @(negedge clk) begin
    if (!rst_n) reset_check();
    else if (random_consumer) begin
      rng=next_random(rng); operand_ready=rng[2:0]>=2;
    end
  end
  task automatic allocate(input integer id, input integer count, output integer slot);
    begin
      @(negedge clk); alloc_valid=1; alloc_entries=count; alloc_meta=160'(id);
      @(posedge clk); while (!alloc_ready) @(posedge clk);
      slot=alloc_slot;
      if (slot_states[slot*2+:2]!==0) $fatal(1,"TILE_ALLOCATE_OWNED");
      allocations=allocations+1;
      @(negedge clk); alloc_valid=0;
    end
  endtask
  task automatic write_word(input integer slot, id, b, e);
    integer l;
    reg [63:0] qword, zword;
    reg [255:0] scales;
    reg [15:0] mask;
    reg [511:0] activations;
    begin
      @(negedge clk);
      #1;
      write_valid=1; write_slot=2'(slot); write_meta=160'(id);
      write_bank=4'(b); write_entry=e;
      for (l=0;l<16;l=l+1) begin
        qword[l*4+:4]=qvalue(id,b,e,l); zword[l*4+:4]=zvalue(id,b,e,l);
        scales[l*16+:16]=scale_value(b,e,l); mask[l]=l%3!=0;
        activations[l*32+:32]=activation_value(id,e,l);
      end
      write_q=qword; write_z=zword; write_scale=scales; write_mask=mask;
      write_activation=activations;
      @(posedge clk); if (write_ready!==1) $fatal(1,"TILE_WRITE_NOT_READY");
      @(negedge clk); write_valid=0;
    end
  endtask
  task automatic fill(input integer id, output integer slot);
    integer e, b, l;
    begin
      allocate(id,E,slot);
      for (e=0;e<E;e=e+1)
        for (b=0;b<B;b=b+1) write_word(slot,id,b,e);
      @(negedge clk); seal_valid=1; seal_slot=2'(slot); seal_meta=160'(id);
      @(posedge clk); if (seal_ready!==1) $fatal(1,"TILE_SEAL_NOT_READY");
      #1; if (slot_states[slot*2+:2]!==2'd2) $fatal(1,"TILE_SEAL_PUBLICATION");
      @(negedge clk); seal_valid=0;
    end
  endtask
  task automatic activate(input integer id, slot);
    begin
      @(negedge clk);
      activate_valid=1; activate_slot=2'(slot); activate_meta=160'(id);
      current_id=id; current_entry=0; active_owner=slot; held=0;
      @(posedge clk); while (!activate_ready) @(posedge clk);
      if (operand_valid!==0) $fatal(1,"TILE_SAME_EDGE_OPERAND");
      activated_at=cycle; checking=1;
      @(negedge clk); activate_valid=0;
    end
  endtask
  task automatic consume(input integer id, slot);
    integer target;
    begin
      target=completed+1;
      activate(id,slot);
      @(posedge clk); while (completed!=target) @(posedge clk);
      @(negedge clk);
    end
  endtask
  task invalidate(input integer slot, state_id);
    begin
      @(negedge clk);
      if (slot_states[slot*2+:2]!==2'(state_id)) $fatal(1,"TILE_CANCEL_PRECONDITION");
      flush=1;
      @(posedge clk);
      @(negedge clk); flush=0;
      @(posedge clk); #1;
      if (slot_states!==0 || operand_valid!==0 || idle!==1 || fault!==0)
        $fatal(1,"TILE_CANCEL_OWNERSHIP");
      cancellations=cancellations+1;
    end
  endtask
  task reject_command;
    begin
      @(posedge clk); #1;
      if (fault!==1 || operand_valid!==0 || alloc_ready!==0)
        $fatal(1,"TILE_MALFORMED_NOT_REJECTED");
      rejected=rejected+1;
      @(negedge clk); flush=1;
      @(posedge clk);
      @(negedge clk); flush=0;
    end
  endtask
  integer s, slot, replacement;
  initial begin
    #1; reset_check();
    repeat(3) @(negedge clk); rst_n=1;
    for (s=0;s<S;s=s+1) begin
      fill(s+1,slot); owners[s]=2'(slot); owner_ids[s]=s+1;
    end
    if (alloc_ready!==0) $fatal(1,"TILE_FULL_OWNERSHIP");
    random_consumer=1;
    consume(1,owners[0]);
    fork
      fill(100,replacement);
      consume(2,owners[1]);
    join
    for (s=2;s<S;s=s+1) consume(s+1,owners[s]);
    consume(100,replacement);
    if (completed!=S+1 || compared!=(S+1)*E*B*16 || overlap==0 || output_stalls==0 ||
        idle!==1) $fatal(1,"TILE_DATA_COVERAGE");
    random_consumer=0; operand_ready=0;
    invalidate(0,0);
    allocate(200,E,slot); invalidate(slot,1);
    fill(201,slot); invalidate(slot,2);
    fill(202,slot); activate(202,slot);
    @(posedge clk); while (!operand_valid) @(posedge clk);
    invalidate(slot,3);
    // Explicit malformed descriptors, duplicate writes, early seal and stale epochs.
    allocate(300,0,slot); reject_command();
    allocate(301,1,slot); write_word(slot,301,0,0); write_word(slot,301,0,0); reject_command();
    allocate(302,1,slot); write_word(slot,303,0,0); reject_command();
    allocate(304,1,slot);
    @(negedge clk); seal_valid=1; seal_slot=2'(slot); seal_meta=304;
    @(posedge clk);
    @(negedge clk); seal_valid=0; reject_command();
    @(negedge clk); activate_valid=1; activate_slot=0; activate_meta=999;
    @(posedge clk);
    @(negedge clk); activate_valid=0; reject_command();
    if (cancellations!=4 || rejected!=5) $fatal(1,"TILE_FAULT_COVERAGE");
    $display("TILE_PASS slots=%0d banks=16 lanes=16 compared=%0d overlap=%0d stalled=%0d cancellations=%0d rejected=%0d allocations=%0d",
             S,compared,overlap,output_stalls,cancellations,rejected,allocations);
    $finish;
  end
endmodule
"""


def tile_bench(slots=3, seed=17, compact=False, compact_banks=1, compact_entries=1):
    bench = TILE_TB.replace("@SLOTS@", str(slots)).replace("@SEED@", str(seed))
    if compact:
        bench = bench.replace("B=16, S=", f"B={compact_banks}, S=")
        bench = bench.replace(", E=64;", f", E={compact_entries};")
        bench = bench.replace("#(.TILE_SLOTS(S))",
                              f"#(.BANKS(B),.TILE_K({128 if compact_entries == 64 else 16}),"
                              f".TILE_ROWS({8 if compact_entries == 64 else 1}),.TILE_SLOTS(S))")
        bench = bench.replace("consume(1,owners[0]);",
                              'consume(1,owners[0]); $display("TILE_FIRST_CONSUME_PASS"); $finish;')
    return bench
