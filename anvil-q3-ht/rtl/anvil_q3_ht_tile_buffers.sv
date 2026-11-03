module anvil_q3_ht_tile_buffers #(
  parameter BANKS=16, TILE_K=128, TILE_ROWS=8, TILE_SLOTS=4,
  parameter META_WIDTH=160,
  localparam SB=(BANKS==1 || BANKS==2 || BANKS==4 ||
    BANKS==8 || BANKS==16) ? BANKS : 1,
  localparam TK=(TILE_K==16 || TILE_K==32 || TILE_K==64 ||
    TILE_K==128) ? TILE_K : 16,
  localparam TR=TILE_ROWS>=1 && TILE_ROWS<=8 ? TILE_ROWS : 1,
  localparam TS=TILE_SLOTS>=2 && TILE_SLOTS<=4 ? TILE_SLOTS : 2,
  localparam MW=META_WIDTH>=1 ? META_WIDTH : 1,
  localparam ENTRIES=TR*(TK>>4),
  localparam WORDS=TS*ENTRIES,
  localparam AW=WORDS>1 ? $clog2(WORDS) : 1
) (
  input wire clk, rst_n, flush,
  input wire alloc_valid,
  output wire alloc_ready,
  output wire [1:0] alloc_slot,
  input wire [31:0] alloc_entries,
  input wire [MW-1:0] alloc_meta,
  input wire write_valid,
  output wire write_ready,
  input wire [1:0] write_slot,
  input wire [3:0] write_bank,
  input wire [31:0] write_entry,
  input wire [MW-1:0] write_meta,
  input wire [63:0] write_q, write_z,
  input wire [255:0] write_scale,
  input wire [15:0] write_mask,
  input wire [511:0] write_activation,
  input wire seal_valid,
  output wire seal_ready,
  input wire [1:0] seal_slot,
  input wire [MW-1:0] seal_meta,
  input wire activate_valid,
  output wire activate_ready,
  input wire [1:0] activate_slot,
  input wire [MW-1:0] activate_meta,
  output wire operand_valid,
  input wire operand_ready,
  output wire [SB*64-1:0] operand_q, operand_z,
  output wire [SB*256-1:0] operand_scale,
  output wire [SB*16-1:0] operand_mask,
  output wire [511:0] operand_activation,
  output wire [MW-1:0] operand_meta,
  output wire [31:0] operand_entry,
  output wire operand_last,
  output wire [TS*2-1:0] slot_states,
  output wire idle, fault
);
  localparam LEGAL=SB==BANKS && TK==TILE_K && TR==TILE_ROWS &&
    TS==TILE_SLOTS && MW==META_WIDTH;
  localparam EMPTY=2'd0, FILLING=2'd1, READY=2'd2, ACTIVE=2'd3;
  reg [1:0] ownership [0:TS-1];
  reg [31:0] entry_count [0:TS-1], write_count [0:TS-1];
  (* nomem2reg *) reg [MW-1:0] metadata [0:TS-1];
  (* nomem2reg *) reg [ENTRIES-1:0] written [0:TS*SB-1];
  reg [1:0] allocation_pointer;
  reg failed, active, read_finished, output_valid;
  reg [1:0] active_slot;
  reg [31:0] read_index, output_entry;
  reg [MW-1:0] output_meta;
  reg output_last;
  integer offset, candidate, selected, i;
  reg any_owned;
  wire running=rst_n && LEGAL && !flush && !failed;
  wire alloc_transfer=alloc_valid && alloc_ready;
  wire write_transfer=write_valid && write_ready;
  wire seal_transfer=seal_valid && seal_ready;
  wire activate_transfer=activate_valid && activate_ready;
  wire invalid_allocation=alloc_entries==0 || alloc_entries>ENTRIES;
  wire valid_write_slot=write_slot<TS;
  wire [1:0] safe_write_slot=valid_write_slot ? write_slot : 2'd0;
  wire [3:0] safe_write_bank=write_bank<SB ? write_bank : 4'd0;
  wire valid_seal_slot=seal_slot<TS;
  wire [1:0] safe_seal_slot=valid_seal_slot ? seal_slot : 2'd0;
  wire valid_activate_slot=activate_slot<TS;
  wire [1:0] safe_activate_slot=valid_activate_slot ? activate_slot : 2'd0;
  wire invalid_write=!valid_write_slot || write_bank>=SB ||
    ownership[safe_write_slot]!=FILLING ||
    metadata[safe_write_slot]!=write_meta ||
    write_entry>=entry_count[safe_write_slot] || write_entry>=ENTRIES;
  wire [31:0] safe_write_entry=write_entry<ENTRIES ? write_entry : 32'd0;
  wire duplicate_write=written[safe_write_slot*SB+safe_write_bank][safe_write_entry];
  wire write_success=write_transfer && !invalid_write && !duplicate_write;
  wire [31:0] sealing_writes=write_count[safe_seal_slot]+
    ((write_success && write_slot==seal_slot) ? 32'd1 : 32'd0);
  wire invalid_seal=!valid_seal_slot || ownership[safe_seal_slot]!=FILLING ||
    metadata[safe_seal_slot]!=seal_meta ||
    sealing_writes!=entry_count[safe_seal_slot]*SB;
  wire invalid_activate=!valid_activate_slot ||
    ownership[safe_activate_slot]!=READY ||
    metadata[safe_activate_slot]!=activate_meta;
  wire read_memory=running && active && !read_finished &&
    (!output_valid || operand_ready);
  wire output_transfer=operand_valid && operand_ready;
  wire [AW-1:0] write_address=safe_write_slot*ENTRIES+safe_write_entry;
  wire [AW-1:0] read_address=active_slot*ENTRIES+read_index;

  generate if (!LEGAL) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q3_HT PARAMETER ERROR: tile banks, dimensions or slots");
  end endgenerate
  always @* begin
    selected=-1;
    candidate=0;
    any_owned=0;
    for (offset=0;offset<TS;offset=offset+1) begin
      candidate=allocation_pointer+offset;
      if (candidate>=TS) candidate=candidate-TS;
      if (ownership[candidate]!=EMPTY) any_owned=1;
      if (selected<0 && ownership[candidate]==EMPTY) selected=candidate;
    end
  end
  assign alloc_ready=running && selected>=0;
  assign alloc_slot=alloc_ready ? selected[1:0] : 2'd0;
  // Malformed write/seal/activate commands transfer once and raise fault.
  assign write_ready=running;
  assign seal_ready=running;
  assign activate_ready=running && !active && !output_valid;
  assign operand_valid=running && output_valid;
  assign operand_meta=operand_valid ? output_meta : {MW{1'b0}};
  assign operand_entry=operand_valid ? output_entry : 32'd0;
  assign operand_last=operand_valid && output_last;
  assign idle=running && !any_owned && !active && !output_valid;
  assign fault=rst_n && failed;

  genvar bank, lane, slot;
  generate for (slot=0;slot<TS;slot=slot+1) begin: owners
    assign slot_states[slot*2+:2]=rst_n ? ownership[slot] : EMPTY;
  end
  for (bank=0;bank<SB;bank=bank+1) begin: banks
    for (lane=0;lane<16;lane=lane+1) begin: lanes
      (* ramstyle="M20K", nomem2reg *) reg [24:0] storage [0:WORDS-1];
      reg [24:0] read_data;
      wire [24:0] write_data={write_mask[lane],write_scale[lane*16+:16],
        write_z[lane*4+:4],write_q[lane*4+:4]};
      assign operand_q[bank*64+lane*4+:4]=operand_valid ? read_data[3:0] : 4'd0;
      assign operand_z[bank*64+lane*4+:4]=operand_valid ? read_data[7:4] : 4'd0;
      assign operand_scale[bank*256+lane*16+:16]=
        operand_valid ? read_data[23:8] : 16'd0;
      assign operand_mask[bank*16+lane]=operand_valid && read_data[24];
      always @(posedge clk) begin
        if (write_success && write_bank==bank) storage[write_address]<=write_data;
        if (read_memory) read_data<=storage[read_address];
      end
    end
  end
  for (lane=0;lane<16;lane=lane+1) begin: activation_lanes
    (* ramstyle="M20K", nomem2reg *) reg [31:0] storage [0:WORDS-1];
    reg [31:0] read_data;
    assign operand_activation[lane*32+:32]=operand_valid ? read_data : 32'd0;
    always @(posedge clk) begin
      if (write_success && write_bank==0)
        storage[write_address]<=write_activation[lane*32+:32];
      if (read_memory) read_data<=storage[read_address];
    end
  end endgenerate

  always @(posedge clk) begin
    if (running) begin
      if (alloc_transfer && !invalid_allocation) begin
        metadata[alloc_slot]<=alloc_meta;
        entry_count[alloc_slot]<=alloc_entries;
        write_count[alloc_slot]<=0;
        for (i=0;i<SB;i=i+1) written[alloc_slot*SB+i]<=0;
      end
      if (write_success) begin
        write_count[write_slot]<=write_count[write_slot]+1'b1;
        written[write_slot*SB+write_bank][safe_write_entry]<=1;
      end
      if (read_memory) begin
        output_meta<=metadata[active_slot];
        output_entry<=read_index;
        output_last<=read_index+1==entry_count[active_slot];
      end
    end
  end

  integer owner_index;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      failed<=0; active<=0; active_slot<=0; read_finished<=0;
      output_valid<=0; read_index<=0; allocation_pointer<=0;
      for (owner_index=0;owner_index<TS;owner_index=owner_index+1)
        ownership[owner_index]<=EMPTY;
    end else if (flush) begin
      failed<=0; active<=0; read_finished<=0; output_valid<=0;
      read_index<=0; allocation_pointer<=0;
      for (owner_index=0;owner_index<TS;owner_index=owner_index+1)
        ownership[owner_index]<=EMPTY;
    end else if (!failed) begin
      if ((alloc_transfer && invalid_allocation) ||
          (write_transfer && (invalid_write || duplicate_write)) ||
          (seal_transfer && invalid_seal) ||
          (activate_transfer && invalid_activate)) begin
        failed<=1;
        output_valid<=0;
      end else begin
        if (alloc_transfer) begin
          ownership[alloc_slot]<=FILLING;
          allocation_pointer<=alloc_slot==TS-1 ? 0 : alloc_slot+1'b1;
        end
        if (seal_transfer) ownership[seal_slot]<=READY;
        if (activate_transfer) begin
          ownership[activate_slot]<=ACTIVE;
          active_slot<=activate_slot;
          active<=1;
          read_finished<=0;
          read_index<=0;
        end
        if (read_memory) begin
          output_valid<=1;
          if (read_index+1==entry_count[active_slot]) read_finished<=1;
          else read_index<=read_index+1'b1;
        end else if (output_transfer) output_valid<=0;
        if (output_transfer && output_last) begin
          ownership[active_slot]<=EMPTY;
          active<=0;
          read_finished<=0;
        end
      end
    end
  end
endmodule
