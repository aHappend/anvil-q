"""ANVLEDG3 encodings derived from the admitted serialized contract only.

Synthetic tables below are representation fixtures, not official tokenizer/model
assets. They cannot qualify the official-profile or real-model benchmarks.
"""

import hashlib
from pathlib import Path
import struct
import zlib


KINDS = (*range(0x100, 0x104), *range(0x200, 0x210))

FAULT_CODES = {
    "wrong-geometry": 5, "duplicate-byte-map": 6, "bad-merge": 6,
    "reserved-token": 6, "crc": 3, "ddr-error": 4, "ddr-read-error": 4,
    "flash-truncation": 3,
    **{name: 1 for name in (
        "header-magic", "header-version", "header-length", "header-reserved",
        "config-duplicate", "config-readonly", "config-divisor", "config-eos", "missing-segment",
    )},
    **{name: 2 for name in (
        "duplicate-segment", "unknown-segment",
        "descriptor-flags", "descriptor-reserved", "zero-segment",
        "unaligned-ddr", "overlapping-ddr", "overflowing-ddr",
        "overlapping-flash", "out-of-capacity-flash",
    )},
    **{name: 5 for name in (
        "directory-duplicate", "directory-shape", "directory-format",
        "directory-permission", "directory-overlap", "directory-extent",
        "directory-outside", "nonzero-writable", "nonzero-immutable-hole",
        "nonzero-inactive-row",
    )},
    **{name: 6 for name in (
        "token-count", "token-offset", "token-length", "token-flags",
        "wrong-byte-map", "merge-order", "trie-cycle", "trie-terminal",
        "unicode-gap", "unicode-class", "dfa-next", "dfa-accept",
        "tag-register", "accept-register", "decomposition-extent",
        "scalar-pool", "composition-scalar", "metadata-reserved",
        "metadata-token-capacity", "metadata-pretoken-capacity",
        "metadata-tag-capacity", "metadata-class-capacity",
    )},
}


def words(*values):
    return struct.pack("<" + "I" * len(values), *values)


def table(record_bytes, records):
    data = b"".join(records)
    assert len(data) == record_bytes * len(records)
    return struct.pack("<IIIIQQ", 0x334C4254, 1, record_bytes, len(records),
                       len(data), 0) + data


def synthetic_image(vocabulary=256, capacity=257, *, fault=None, max_pretoken=4096,
                    transport=1, geometry=None, tokenizer=None, metadata_words=None,
                    table_payloads=None):
    """Complete image bytes and independently calculated public DDR tuples."""
    dimensions = {
        "layers": 1, "hidden": 8, "intermediate": 8, "query_heads": 1,
        "kv_heads": 1, "head_dim": 8, "group": 8, "sequence": 4,
    }
    if geometry:
        if geometry.keys() - dimensions.keys():
            raise ValueError("Unknown synthetic geometry field")
        dimensions.update(geometry)
    layers, hidden, intermediate, seq = (
        dimensions[name] for name in ("layers", "hidden", "intermediate", "sequence"))
    q, k, d, group = (dimensions[name] for name in ("query_heads", "kv_heads", "head_dim", "group"))
    kv_size = k * d
    regions = []
    immutable = bytearray()
    writable = bytearray()

    def region(kind, layer, projection, rows, columns, fmt, rw=False, value=0):
        payload = writable if rw else immutable
        offset = len(payload)
        payload.extend(words(value) * (rows * columns))
        regions.append((kind, layer, projection, 0x103 if rw else 0x102,
                        offset, rows, columns, fmt, 3 if rw else 1,
                        rows * columns * 4))

    region(0, 0, 0, capacity, hidden, 1)
    for layer in range(layers):
        for projection in range(7):
            inputs = intermediate if projection == 6 else hidden
            outputs = (intermediate if projection in (4, 5) else
                       kv_size if projection in (1, 2) else hidden)
            region(1, layer, projection, inputs, outputs // 8, 2)
            region(2, layer, projection, inputs // group, outputs // 8, 2)
            region(3, layer, projection, inputs // group, outputs, 1, value=0x3C00)
            if projection < 3:
                region(4, layer, projection, 1, outputs, 1)
        for kind in (5, 6):
            region(kind, layer, 0, 1, hidden, 1, value=0x3C00)
        for kind in (9, 10):
            region(kind, layer, 0, seq, kv_size, 3, rw=True)
    region(7, 0, 0, 1, hidden, 1, value=0x3C00)
    region(8, 0, 0, 15, max(hidden, intermediate), 3, rw=True)
    region(11, 0, 0, seq, d, 4)
    regions.sort(key=lambda record: record[:3])
    assert len(regions) == 28 * layers + 4
    directory = [struct.pack("<IIIIQIIIIQ", *record) for record in regions]
    pieces = [bytes([byte]) for byte in range(min(vocabulary, 256))]
    pieces.extend([b"AB"] * max(0, vocabulary - 256))
    token_bytes = b"".join(pieces)
    offset = 0
    tokens = []
    for piece in pieces:
        tokens.append(struct.pack("<QII", offset, len(piece), 1))
        offset += len(piece)
    metadata = [
        1, 1, vocabulary, 0, 0, 0, 0, min(vocabulary - 1, 255),
        0x000F0100, 1, 0, 2, 32, 0, 2, max_pretoken,
    ]
    metadata_bytes = words(*metadata)
    metadata_bytes += hashlib.sha256(b"ANVLEDG3 independent synthetic fixture v1").digest()
    metadata_bytes += bytes(32)
    segments = {
        0x100: words(1, layers, hidden, intermediate, q, k, d, group, 4,
                     capacity, seq, max(hidden, intermediate), 1, 0, 0, 0),
        0x101: table(48, directory),
        0x102: bytes(immutable),
        0x103: bytes(writable),
        0x200: metadata_bytes,
        0x201: table(16, tokens),
        0x202: table(1, [bytes([byte]) for byte in token_bytes]),
        0x203: table(4, [words(byte % max(1, vocabulary)) for byte in range(256)]),
        0x204: table(16, [words(65, 66, 256, 0)] if vocabulary == 257 else []),
        0x205: table(16, [words(0, 0, 0xFFFFFFFF, 0)]),
        0x206: table(8, []),
        0x207: table(16, [words(0, 0xD7FF, 0, 0), words(0xE000, 0x10FFFF, 0, 0)]),
        0x208: table(16, [words(0, 0, 0, 0), words(2, 0, 1, 0), words(4, 1, 0, 0)]),
        0x209: table(16, [
            words(1, 0, 1, 0), words(2, 0, 0, 0),
            words(1, 0, 1, 0), words(2, 0, 0, 0),
            words(2, 0, 0, 0), words(2, 0, 0, 0),
        ]),
        0x20A: table(16, []),
        0x20B: table(16, [words(2, 0, 0, 0)]),
        0x20C: table(16, [words(0, 0, 0, 0)]),
        0x20D: table(16, []),
        0x20E: table(4, []),
        0x20F: table(16, []),
    }
    if tokenizer is not None:
        memory, bases, counts, profile_metadata, _, _ = tokenizer
        if profile_metadata[2] != vocabulary:
            raise ValueError("Synthetic profile/image vocabulary mismatch")
        profile_metadata = list(profile_metadata)
        profile_metadata[15] = max_pretoken
        profile_metadata[16:24] = struct.unpack(
            "<8I", hashlib.sha256(b"ANVLEDG3 independent text integration v1").digest())
        segments[0x200] = words(*profile_metadata)
        widths = (0, 16, 1, 4, 16, 16, 8, 16, 16, 16, 16, 16, 16, 16, 4, 16)
        for index in range(1, 16):
            length = counts[index] * widths[index]
            data = b"".join(words(memory[bases[index] + 32 + offset])
                            for offset in range(0, length, 4))[:length]
            segments[0x200 + index] = table(
                widths[index],
                [data[offset:offset + widths[index]]
                 for offset in range(0, length, widths[index])])
    if metadata_words is not None:
        data = bytearray(segments[0x200])
        for index, value in metadata_words.items():
            if not isinstance(index, int) or not 0 <= index < 32:
                raise ValueError("Metadata override must name a u32 word in the 128-byte record")
            struct.pack_into("<I", data, index * 4, value)
        segments[0x200] = bytes(data)
    if table_payloads is not None:
        if set(table_payloads) != set(range(0x200, 0x210)) or tokenizer is not None:
            raise ValueError("Supply exactly metadata and fifteen tables, without a second profile")
        for kind, data in table_payloads.items():
            if not isinstance(data, bytes) or not data:
                raise ValueError("Complete table payloads must be nonempty serialized bytes")
            segments[kind] = data
    if fault in ("zero-immutable-hole", "nonzero-immutable-hole"):
        segments[0x102] += words(int(fault == "nonzero-immutable-hole"), 0)
    if fault == "nonzero-inactive-row":
        if vocabulary >= capacity:
            raise ValueError("Inactive-row fixture requires spare physical vocabulary")
        data = bytearray(segments[0x102])
        struct.pack_into("<I", data, vocabulary * hidden * 4, 0x3C00)
        segments[0x102] = bytes(data)
    if fault == "wrong-geometry":
        segments[0x100] = segments[0x100][:8] + words(16) + segments[0x100][12:]
    elif fault == "duplicate-byte-map":
        segment = bytearray(segments[0x203])
        segment[36:40] = words(0)
        segments[0x203] = bytes(segment)
    elif fault == "bad-merge":
        segments[0x204] = table(16, [words(65, 65, 256, 0)])
    elif fault == "reserved-token":
        segment = bytearray(segments[0x201])
        segment[44:48] = words(4)
        segments[0x201] = bytes(segment)
    payload_faults = {
        "directory-duplicate": (0x101, 32 + 48, "<III", (0, 0, 0)),
        "directory-shape": (0x101, 32 + 24, "<I", (capacity - 1,)),
        "directory-format": (0x101, 32 + 32, "<I", (3,)),
        "directory-permission": (0x101, 32 + 36, "<I", (3,)),
        "directory-overlap": (0x101, 32 + 48 + 16, "<Q", (0,)),
        "directory-extent": (0x101, 32 + 40, "<Q", (4,)),
        "directory-outside": (0x101, 32 + 16, "<Q", (0xFFFFFFFFFFFFFFFC,)),
        "nonzero-writable": (0x103, 0, "<I", (1,)),
        "token-count": (0x201, 12, "<I", (vocabulary - 1,)),
        "token-offset": (0x201, 32, "<Q", (0xFFFFFFFFFFFFFFFF,)),
        "token-length": (0x201, 40, "<I", (3,)),
        "token-flags": (0x201, 44, "<I", (0,)),
        "wrong-byte-map": (0x203, 32, "<I", (1,)),
        "unicode-gap": (0x207, 32, "<I", (1,)),
        "unicode-class": (0x207, 40, "<I", (1,)),
        "dfa-next": (0x209, 32, "<I", (3,)),
        "dfa-accept": (0x208, 32 + 16 + 4, "<II", (1, 1)),
        "tag-register": (0x20B, 36, "<I", (32,)),
        "accept-register": (0x20C, 36, "<I", (32,)),
        "metadata-reserved": (0x200, 124, "<I", (1,)),
        "metadata-token-capacity": (0x200, 14 * 4, "<I", (4097,)),
        "metadata-pretoken-capacity": (0x200, 15 * 4, "<I", (4097,)),
        "metadata-tag-capacity": (0x200, 12 * 4, "<I", (33,)),
        "metadata-class-capacity": (0x200, 9 * 4, "<I", (4097,)),
    }
    if fault in payload_faults:
        kind, offset, encoding, values = payload_faults[fault]
        data = bytearray(segments[kind])
        struct.pack_into(encoding, data, offset, *values)
        segments[kind] = bytes(data)
    elif fault == "merge-order":
        segments[0x204] = table(16, [words(65, 66, 256, 0), words(65, 66, 256, 1)])
    elif fault == "trie-cycle":
        segments[0x205] = table(16, [words(0, 1, 0xFFFFFFFF, 0)])
        segments[0x206] = table(8, [words(65, 0)])
    elif fault == "trie-terminal":
        segments[0x205] = table(16, [words(0, 0, 0, 0)])
    elif fault == "decomposition-extent":
        segments[0x20D] = table(16, [words(0xE9, 0, 1, 0)])
    elif fault == "scalar-pool":
        segments[0x20E] = table(4, [words(0xD800)])
    elif fault == "composition-scalar":
        segments[0x20F] = table(16, [words(0x65, 0x301, 0x110000, 0)])
    eos = struct.unpack_from("<I", segments[0x200], 28)[0]
    config = [5, eos, 2, transport, 1, vocabulary, 0]
    config_bytes = b"".join(words(address, value) for address, value in
                            zip((4, 8, 12, 16, 20, 24, 36), config))
    header_bytes = 32 + len(config_bytes) + 40 * len(segments)
    header = b"ANVLEDG3" + words(1, header_bytes, 1, len(segments), 7, 0)
    destinations, flash_offsets = {}, {}
    ddr_cursor, flash_cursor = 0x1000, header_bytes
    descriptors, payload, writes = [], bytearray(), []
    for kind, data in segments.items():
        destinations[kind] = ddr_cursor
        flash_offsets[kind] = flash_cursor
        descriptors.append(struct.pack("<IIQQQII", kind, 0, ddr_cursor, len(data),
                                       flash_cursor, zlib.crc32(data), 0))
        payload.extend(data)
        for offset in range(0, len(data), 4):
            part = data[offset:offset + 4]
            writes.append((ddr_cursor + offset, int.from_bytes(part, "little"),
                           (1 << len(part)) - 1))
        flash_cursor += len(data)
        padding = -flash_cursor % 4
        payload.extend(bytes(padding))
        flash_cursor += padding
        ddr_cursor += len(data) + (-len(data) % 4)
    image = header + config_bytes + b"".join(descriptors) + bytes(payload)
    header_faults = {
        "header-magic": (0, "<I", (0,)),
        "header-version": (8, "<I", (2,)),
        "header-length": (12, "<I", (header_bytes - 4,)),
        "header-reserved": (28, "<I", (1,)),
        "config-duplicate": (32 + 8, "<I", (4,)),
        "config-readonly": (32, "<I", (0,)),
        "config-divisor": (36, "<I", (3,)),
        "config-eos": (32 + 8 + 4, "<I", (vocabulary,)),
        "missing-segment": (12, "<III", (header_bytes - 40, 1, len(segments) - 1)),
    }
    descriptor_start = 32 + len(config_bytes)
    descriptor_faults = {
        "duplicate-segment": (descriptor_start + 40, "<I", (0x100,)),
        "unknown-segment": (descriptor_start, "<I", (0x300,)),
        "descriptor-flags": (descriptor_start + 4, "<I", (1,)),
        "descriptor-reserved": (descriptor_start + 36, "<I", (1,)),
        "zero-segment": (descriptor_start + 16, "<Q", (0,)),
        "unaligned-ddr": (descriptor_start + 8, "<Q", (0x1001,)),
        "overlapping-ddr": (descriptor_start + 40 + 8, "<Q", (0x1000,)),
        "overflowing-ddr": (descriptor_start + 8, "<Q", (0xFFFFFFFFFFFFFFFC,)),
        "overlapping-flash": (descriptor_start + 40 + 24, "<Q", (header_bytes,)),
        "out-of-capacity-flash": (descriptor_start + 24, "<Q", (1 << 24,)),
    }
    for faults in (header_faults, descriptor_faults):
        if fault in faults:
            offset, encoding, values = faults[fault]
            modified = bytearray(image)
            struct.pack_into(encoding, modified, offset, *values)
            image = bytes(modified)
    if fault == "crc":
        image = bytearray(image)
        image[flash_offsets[0x102]] ^= 1
        image = bytes(image)
        address = destinations[0x102]
        writes = [(a, data ^ 1 if a == address else data, strobe)
                  for a, data, strobe in writes]
    if fault == "flash-truncation":
        image = image[:-4]
        writes = []
        for kind, data in segments.items():
            for offset in range(0, len(data), 4):
                count = min(4, len(data) - offset)
                begin = flash_offsets[kind] + offset
                actual = image[begin:begin + count].ljust(count, b"\xff")
                writes.append((destinations[kind] + offset, int.from_bytes(actual, "little"),
                               (1 << count) - 1))
    else:
        assert len(image) == flash_cursor
    return {
        "image": image, "segments": segments, "destinations": destinations,
        "writes": writes, "config": config, "regions": regions,
        "capacity": capacity, "vocabulary": vocabulary, "fault": fault,
        "geometry": dimensions,
    }


BOOT = r"""
module bench;
  reg clk=0;
  reg rst_n;
  always #5 clk=~clk;
  reg start=0,ddr_cal_done=0,spi_miso=0;
  wire spi_mosi,spi_sck,spi_cs_n;
  wire ddr_req_valid,ddr_req_write,ddr_rsp_ready,boot_done,busy,error;
  wire [63:0] ddr_req_addr;
  wire [31:0] ddr_req_wdata;
  wire [3:0] ddr_req_wstrb;
  wire [7:0] error_code;
  reg ddr_req_ready=0,ddr_rsp_valid=0,ddr_rsp_error=0;
  reg [31:0] ddr_rsp_rdata=0;
  wire [223:0] committed_config_words;
  wire [1279:0] committed_segment_bases,committed_segment_bytes;
  wire [1023:0] committed_metadata;
  wire [511:0] committed_table_counts;
  anvil_edge_ddr4_boot_loader #(
    .NUM_LAYERS(1),.HIDDEN_SIZE(8),.INTERMEDIATE_SIZE(8),
    .NUM_Q_HEADS(1),.NUM_KV_HEADS(1),.HEAD_DIM(8),.GROUP_SIZE(8),
    .VOCAB_SIZE(257),.MAX_SEQ_LEN(4),.SPI_CLOCK_HALF_PERIOD(1),
    .DDR_BYTES(65536)
  ) dut(.*);
  reg [7:0] flash[0:65535],ddr[0:65535];
  reg [63:0] write_address[0:8191],segment_base[0:19],segment_length[0:19];
  reg [31:0] write_data[0:8191];
  reg [3:0] write_strobe[0:8191];
  reg [31:0] command_shift=0;
  integer spi_command_bits=0,flash_address=0,flash_bit=0,spi_reads=0;
  always @(negedge spi_cs_n) begin
    spi_command_bits=0; command_shift=0; flash_bit=0; spi_miso=0;
  end
  always @(posedge spi_sck) if (!spi_cs_n) begin
    if (spi_command_bits<32) begin
      command_shift={command_shift[30:0],spi_mosi};
      spi_command_bits=spi_command_bits+1;
      if (spi_command_bits==32) begin
        if (command_shift[31:24]!==8'h03 || command_shift[23:0]>=65536)
          $fatal(1,"BOOT_SPI_COMMAND %h",command_shift);
        flash_address=command_shift[23:0]; spi_reads=spi_reads+1;
      end
    end else begin
      if (flash_bit==7) begin flash_bit=0; flash_address=flash_address+1; end
      else flash_bit=flash_bit+1;
    end
  end
  always @(negedge spi_sck) if (!spi_cs_n && spi_command_bits==32) begin
    if (flash_address>=@FLASH_EXTENT@) spi_miso=1;
    else spi_miso=flash[flash_address][7-flash_bit];
  end
  reg [31:0] rng=@SEED@;
  reg pending=0,held=0,loading=1;
  reg [100:0] held_payload;
  reg [63:0] pending_address=0;
  integer cycle=0,writes=0,reads=0,acknowledgements=0,delay_count=0;
  integer request_stalls=0,response_stalls=0,comparisons=0,phase=0;
  function automatic bit readable(input [63:0] address);
    integer k;
    begin
      readable=0;
      for (k=0;k<20;k=k+1)
        if (address>=segment_base[k] &&
            address<segment_base[k]+segment_length[k] && address[1:0]==0)
          readable=1;
    end
  endfunction
  task automatic reset_check;
    begin
      if ({spi_mosi,spi_sck,ddr_req_valid,ddr_req_write,ddr_req_addr,
           ddr_req_wdata,ddr_req_wstrb,ddr_rsp_ready,boot_done,busy,error,error_code,
           committed_config_words,committed_segment_bases,committed_segment_bytes,
           committed_metadata,committed_table_counts}!==4433'd0 || spi_cs_n!==1)
        $fatal(1,"BOOT_RESET t=%0t",$time);
    end
  endtask
  always @(posedge clk or negedge clk) if (!rst_n) reset_check();
  always @(negedge clk) if (rst_n) begin
    rng=rng ^ (rng<<13); rng=rng ^ (rng>>17); rng=rng ^ (rng<<5);
    ddr_req_ready=rng[0] && cycle%7!=0;
    if (pending && !ddr_rsp_valid) begin
      if (delay_count==0) begin
        ddr_rsp_valid<=1;
        ddr_rsp_rdata={ddr[pending_address+3],ddr[pending_address+2],
                       ddr[pending_address+1],ddr[pending_address]};
        ddr_rsp_error=@DDR_ERROR@ && acknowledgements==2;
      end else delay_count=delay_count-1;
    end
  end
  always @(posedge clk) begin
    cycle=cycle+1;
    if (rst_n) begin
      if ((^{spi_mosi,spi_sck,spi_cs_n,ddr_req_valid,ddr_req_write,
             ddr_req_addr,ddr_req_wdata,ddr_req_wstrb,ddr_rsp_ready,
             boot_done,busy,error,error_code,committed_config_words,
             committed_segment_bases,committed_segment_bytes,committed_metadata,
             committed_table_counts})===1'bx) $fatal(1,"BOOT_XZ");
      if (!boot_done && {committed_config_words,committed_segment_bases,
          committed_segment_bytes,committed_metadata,committed_table_counts}!==0)
        $fatal(1,"BOOT_PARTIAL_PUBLICATION");
      if (held && (!ddr_req_valid ||
          {ddr_req_write,ddr_req_addr,ddr_req_wdata,ddr_req_wstrb}!==held_payload))
        $fatal(1,"BOOT_DDR_STABILITY");
      held=ddr_req_valid && !ddr_req_ready;
      held_payload={ddr_req_write,ddr_req_addr,ddr_req_wdata,ddr_req_wstrb};
      if (held) request_stalls=request_stalls+1;
      if (ddr_rsp_valid && !ddr_rsp_ready) response_stalls=response_stalls+1;
      if (ddr_rsp_valid && ddr_rsp_ready) begin
        if (!pending) $fatal(1,"BOOT_ORPHAN_RESPONSE");
        pending=0; acknowledgements=acknowledgements+1; ddr_rsp_valid<=0;
      end
      if (ddr_req_valid && ddr_req_ready) begin
        if (pending || !ddr_cal_done || ddr_req_addr>=65532)
          $fatal(1,"BOOT_DDR_OUTSTANDING_OR_BOUNDS");
        if (ddr_req_write) begin
          if (!loading || phase!=0 || writes>=@WRITES@ ||
              ddr_req_addr!==write_address[writes] ||
              ddr_req_wstrb!==write_strobe[writes])
            $fatal(1,"BOOT_WRITE_TUPLE item=%0d addr=%h strobe=%h",
                   writes,ddr_req_addr,ddr_req_wstrb);
          for (integer lane=0;lane<4;lane=lane+1) if (ddr_req_wstrb[lane]) begin
            if (ddr_req_wdata[lane*8+:8]!==write_data[writes][lane*8+:8])
              $fatal(1,"BOOT_WRITE_DATA item=%0d expected=%h observed=%h",
                     writes,write_data[writes],ddr_req_wdata);
            ddr[ddr_req_addr+lane]=ddr_req_wdata[lane*8+:8];
          end
          writes=writes+1;
        end else begin
          loading=0;
          if (writes!=@WRITES@ || !readable(ddr_req_addr) || ddr_req_wstrb!==0)
            $fatal(1,"BOOT_VALIDATION_READ address=%h",ddr_req_addr);
          reads=reads+1;
        end
        pending_address=ddr_req_addr; pending=1; delay_count=1+rng[4:2];
        comparisons=comparisons+1;
      end
    end
  end
  task automatic tick; begin @(posedge clk); #1; end endtask
  task automatic wait_result(input [7:0] code);
    begin
      while (!boot_done && !error) tick();
      if (code==0) begin
        if (error || !boot_done || writes!=@WRITES@ || pending ||
            acknowledgements!=writes+reads || reads==0 || spi_reads<22 ||
            committed_config_words!==224'h@CONFIG@ ||
            committed_segment_bases!==1280'h@BASES@ ||
            committed_segment_bytes!==1280'h@LENGTHS@ ||
            committed_metadata!==expected_metadata ||
            committed_table_counts!==512'h@COUNTS@)
          $fatal(1,"BOOT_COMMIT code=%h writes=%0d reads=%0d ack=%0d spi=%0d",
                 error_code,writes,reads,acknowledgements,spi_reads);
      end else begin
        repeat (10) begin
          tick();
          if (error!==1 || error_code!==code || boot_done!==0 || pending ||
              ddr_req_valid!==0 || spi_cs_n!==1)
            $fatal(1,"BOOT_REJECTION expected=%h observed=%h",code,error_code);
        end
      end
      comparisons=comparisons+1;
    end
  endtask
  integer i;
  reg [1023:0] expected_metadata=1024'h@METADATA@;
  initial begin
    rst_n=0; #0; reset_check();
    for (i=0;i<65536;i=i+1) begin flash[i]=8'hff; ddr[i]=0; end
    $readmemh("@FLASH@",flash,0,@FLASH_EXTENT@-1);
    @VECTORS@
    repeat (2) tick(); @(negedge clk); #1; rst_n=1;
    repeat (20) begin
      tick();
      if (spi_cs_n!==1 || ddr_req_valid!==0 || boot_done!==0)
        $fatal(1,"BOOT_DELAYED_CALIBRATION");
    end
    @(negedge clk); #1; ddr_cal_done=1;
    wait_result(@EXPECTED_ERROR@);
    @RELOAD@
    $display("BOOT_TRANSACTIONS writes=%0d reads=%0d acknowledgements=%0d",
             writes,reads,acknowledgements);
    $display("COMPARED %0d",comparisons);
    $finish;
  end
  initial begin
    repeat (30000000) @(posedge clk); $fatal(1,"BOOT_CYCLE_BOUND writes=%0d reads=%0d",writes,reads);
  end
endmodule
"""


def packed(values, width):
    return f"{sum(value << (width * i) for i, value in enumerate(values)):x}"


def wide_cycle_guard(bound):
    return f"""
  initial begin : bounded_cycles
    reg [63:0] watchdog_cycles;
    watchdog_cycles=0;
    while (watchdog_cycles<64'd{bound}) begin
      @(posedge clk); watchdog_cycles=watchdog_cycles+1'b1;
    end
    $fatal(1,"BOOT_CYCLE_BOUND writes=%0d reads=%0d",writes,reads);
  end
"""


def run_watchdog_width(evidence):
    bench = """
module bench;
  reg clk=0;
  always #5 clk=~clk;
  integer writes=0,reads=0,comparisons=0;
  initial begin
    repeat (4) begin
      @(posedge clk); #1; comparisons=comparisons+1;
    end
    if (comparisons!=4 || $time!=36) $fatal(1,"WATCHDOG_CLOCK_PROGRESS");
    $display("COMPARED %0d",comparisons); $finish;
  end
""" + wide_cycle_guard(3700482320) + "\nendmodule\n"
    for simulator in ("iverilog", "verilator"):
        evidence.simulate("watchdog-width-" + simulator, bench, [], 4, simulator=simulator)


def boot_test(evidence, vocabulary, seed, fault=None, reload=False, *, capacity=257,
              metadata_words=None, reload_metadata=None, label=None, fixture=None):
    if fixture is None:
        fixture = synthetic_image(vocabulary, capacity=capacity, fault=fault,
                                  metadata_words=metadata_words)
    elif (fixture["vocabulary"] != vocabulary or fixture["capacity"] != capacity
          or fixture["fault"] != fault or metadata_words is not None or reload
          or reload_metadata is not None):
        raise ValueError("External boot fixture identity/options do not match test invocation")
    name = f"boot-v{vocabulary}-s{seed}-{fault or ('reload' if reload else 'valid')}"
    if label:
        name += "-" + label
    directory = evidence.path / (name + "-input")
    directory.mkdir()
    flash = directory / "flash.hex"
    flash.write_text("".join(f"{byte:02x}\n" for byte in fixture["image"]), encoding="ascii")
    manifest = {
        "synthetic_only": fixture.get("synthetic_only", True),
        "input_provenance": fixture.get("input_provenance", "Independent synthetic representation fixture"),
        "vocabulary": vocabulary, "physical_capacity": capacity,
        "metadata_words": metadata_words,
        "metadata_reload_epochs": reload_metadata,
        "image_sha256": hashlib.sha256(fixture["image"]).hexdigest(),
        "segments": [{"kind": kind, "base": fixture["destinations"][kind],
                      "length": len(payload), "crc32": zlib.crc32(payload)}
                     for kind, payload in fixture["segments"].items()],
        "validation_reads": "Aligned word reads wholly within a declared segment's padded final word; all payload writes and their acknowledgements precede reads.",
    }
    vectors = []
    large = len(fixture["writes"]) > 8192
    if large:
        manifest["expected_write_tuple_count"] = len(fixture["writes"])
        manifest["expected_write_files"] = []
        for field, width, index in (("address", 16, 0), ("data", 8, 1), ("strobe", 1, 2)):
            output = directory / (field + ".hex")
            checksum = hashlib.sha256()
            with output.open("x", encoding="ascii") as stream:
                for values in fixture["writes"]:
                    line = f"{values[index]:0{width}x}\n"
                    stream.write(line)
                    checksum.update(line.encode())
            manifest["expected_write_files"].append({
                "field": field, "path": evidence.relative(output), "sha256": checksum.hexdigest(),
            })
            vectors.append(f'$readmemh("{evidence.relative(output)}",write_{field},0,'
                           f'{len(fixture["writes"])-1});')
    else:
        manifest["expected_write_tuples"] = fixture["writes"]
        for index, (address, data, strobe) in enumerate(fixture["writes"]):
            vectors.append(f"write_address[{index}]=64'h{address:x}; "
                           f"write_data[{index}]=32'h{data:x}; write_strobe[{index}]=4'h{strobe:x};")
    import json
    (directory / "expected.json").write_text(json.dumps(manifest, indent=2) + "\n")
    for index, kind in enumerate(KINDS):
        vectors.append(f"segment_base[{index}]=64'h{fixture['destinations'][kind]:x}; "
                       f"segment_length[{index}]={len(fixture['segments'][kind])};")
    counts = []
    for kind in range(0x200, 0x210):
        counts.append(0 if kind == 0x200 else
                      struct.unpack_from("<I", fixture["segments"][kind], 12)[0])
    error = (1 if vocabulary < 256 or vocabulary > min(262144, capacity)
             else FAULT_CODES.get(fault, 0))
    reload_code = ""
    if reload:
        second = directory / "undersized.hex"
        image = synthetic_image(255)["image"]
        second.write_text("".join(f"{byte:02x}\n" for byte in image), encoding="ascii")
        reload_code = f"""
    repeat (5) tick();
    @(negedge clk); #1; phase=1;
    $readmemh("{evidence.relative(second)}",flash,0,{len(image)-1});
    start=1; tick();
    if (boot_done!==0) $fatal(1,"BOOT_RELOAD_NOT_WITHDRAWN");
    @(negedge clk); #1; start=0;
    wait_result(8'h01);
"""
    if reload_metadata is not None:
        if reload:
            raise ValueError("Choose either the original undersized reload or metadata reload")
        reload_code = """
    $display("BOOT_METADATA_EPOCH 0 code=0 writes=%0d reads=%0d acknowledgements=%0d",
             writes,reads,acknowledgements);
"""
        for epoch, (overrides, expected_error) in enumerate(reload_metadata, 1):
            second = synthetic_image(vocabulary, capacity=capacity, metadata_words=overrides)
            if (second["destinations"] != fixture["destinations"] or
                    len(second["image"]) != len(fixture["image"]) or
                    len(second["writes"]) != len(fixture["writes"])):
                raise ValueError("Metadata-only reload changed image layout")
            image_file = directory / f"metadata-reload-{epoch}.hex"
            image_file.write_text("".join(f"{byte:02x}\n" for byte in second["image"]),
                                  encoding="ascii")
            # Restore every expected word, including ones changed by an earlier epoch.
            updates = "\n".join(
                f"    write_data[{index}]=32'h{new[1]:x};"
                for index, new in enumerate(second["writes"])
                if (fixture["destinations"][0x200] <= new[0] <
                    fixture["destinations"][0x200] + 128))
            reload_code += f"""
    repeat (5) tick();
    if (pending || ddr_rsp_valid || ddr_req_valid)
      $fatal(1,"BOOT_METADATA_RELOAD_NOT_QUIESCENT");
    @(negedge clk); #1;
    $readmemh("{evidence.relative(image_file)}",flash,0,{len(second['image'])-1});
{updates}
    expected_metadata=1024'h{int.from_bytes(second['segments'][0x200], 'little'):x};
    writes=0; reads=0; acknowledgements=0; spi_reads=0; loading=1;
    start=1; tick();
    if (boot_done!==0 || committed_metadata!==0)
      $fatal(1,"BOOT_METADATA_RELOAD_NOT_WITHDRAWN");
    @(negedge clk); #1; start=0;
    wait_result(8'h{expected_error:02x});
    if (writes!={len(second['writes'])} || reads==0)
      $fatal(1,"BOOT_METADATA_RELOAD_TRAFFIC");
    $display("BOOT_METADATA_EPOCH {epoch} code={expected_error} writes=%0d reads=%0d acknowledgements=%0d",
             writes,reads,acknowledgements);
"""
    parameters = {
        "FLASH": evidence.relative(flash), "FLASH_EXTENT": str(len(fixture["image"])),
        "SEED": str(seed), "WRITES": str(len(fixture["writes"])),
        "DDR_ERROR": ("!loading" if fault == "ddr-read-error" else
                      str(int(fault == "ddr-error"))),
        "EXPECTED_ERROR": f"8'h{error:02x}",
        "VECTORS": "\n".join(vectors), "RELOAD": reload_code,
        "CONFIG": packed(fixture["config"], 32),
        "BASES": packed([fixture["destinations"][kind] for kind in KINDS], 64),
        "LENGTHS": packed([len(fixture["segments"][kind]) for kind in KINDS], 64),
        "METADATA": f"{int.from_bytes(fixture['segments'][0x200], 'little'):x}",
        "COUNTS": packed(counts, 32),
    }
    bench = BOOT
    bench = bench.replace(".VOCAB_SIZE(257)", f".VOCAB_SIZE({capacity})")
    if large:
        end = max(len(fixture["image"]), *(
            fixture["destinations"][kind] + len(data)
            for kind, data in fixture["segments"].items()))
        extent = 1 << max(16, (end + 4).bit_length())
        assert extent <= 1 << 24, "Synthetic large fixture must fit declared 24-bit SPI capacity"
        bench = bench.replace("65536", str(extent)).replace("65535", str(extent - 1))
        bench = bench.replace("65532", str(extent - 4))
        bench = bench.replace("[0:8191]", f'[0:{len(fixture["writes"])-1}]')
        cycle_bound = len(fixture["image"]) * 80 + vocabulary * 10000 + 30000000
        original_guard = """
  initial begin
    repeat (30000000) @(posedge clk); $fatal(1,"BOOT_CYCLE_BOUND writes=%0d reads=%0d",writes,reads);
  end
"""
        if bench.count(original_guard) != 1:
            raise RuntimeError("Missing unique large-image cycle watchdog")
        bench = bench.replace(original_guard, wide_cycle_guard(cycle_bound))
    for key, value in parameters.items():
        bench = bench.replace(f"@{key}@", value)
    if fault == "ddr-read-error":
        bench = bench.replace("ddr_rsp_error=!loading && acknowledgements==2;",
                              "ddr_rsp_error=!loading;")
    if error in (1, 2):
        bench = bench.replace("    $display(\"BOOT_TRANSACTIONS",
                              '    if (writes!=0 || reads!=0) $fatal(1,"BOOT_INVALID_HEADER_TRAFFIC");\n'
                              '    $display("BOOT_TRANSACTIONS')
    if error in (5, 6):
        bench = bench.replace("    $display(\"BOOT_TRANSACTIONS",
                              '    if (writes!=@TOTAL@ || reads==0) $fatal(1,"BOOT_SEMANTIC_COUNTS");\n'
                              '    $display("BOOT_TRANSACTIONS').replace("@TOTAL@", str(len(fixture["writes"])))
    # The validation scan count is implementation-independent, so its observed
    # total is checked separately instead of predicting an internal scan schedule.
    root = Path(__file__).resolve().parent.parent
    evidence.simulate(name, bench, [
        "rtl/anvil_edge_numeric_pkg.sv",
        *[str(path.relative_to(root)) for path in sorted((root / "rtl").glob("*.sv"))
          if path.name != "anvil_edge_numeric_pkg.sv"],
    ], None)


def run_boot(evidence):
    evidence.tools(("iverilog", "vvp"))
    evidence.run_cases([
        (f"boot-{vocabulary}-{seed}",
         lambda scope, vocabulary=vocabulary, seed=seed:
         boot_test(scope, vocabulary, seed, reload=vocabulary == 257))
        for seed in (1, 17, 89) for vocabulary in (256, 257, 1, 255)
    ] + [
        ("boot-fault-" + fault, lambda scope, fault=fault: boot_test(scope, 257, 17, fault))
        for fault in ("wrong-geometry", "duplicate-byte-map", "bad-merge",
                      "reserved-token", "crc", "ddr-error")
    ])
    run_storage_faults(evidence)
    run_large_images(evidence)
    run_storage_edges(evidence)


def run_storage_faults(evidence):
    evidence.tools(("iverilog", "vvp"))
    previous = {"wrong-geometry", "duplicate-byte-map", "bad-merge",
                "reserved-token", "crc", "ddr-error", "nonzero-inactive-row"}
    evidence.run_cases([
        ("storage-fault-" + fault,
         lambda scope, fault=fault: boot_test(scope, 257, 17, fault))
        for fault in sorted(FAULT_CODES.keys() - previous)
    ])


def run_storage_edges(evidence):
    evidence.run_cases([
        (f"storage-edge-{seed}-{vocabulary}-{fault}",
         lambda scope, seed=seed, vocabulary=vocabulary, fault=fault:
         boot_test(scope, vocabulary, seed, fault, capacity=257))
        for seed in (1, 17, 89) for vocabulary, fault in (
            (256, "nonzero-inactive-row"), (257, "zero-immutable-hole"), (258, None))
    ])
    run_image_upper(evidence)


def run_image_upper(evidence):
    boot_test(evidence, 262145, 17, capacity=262145)


def run_boot_boundaries(evidence):
    evidence.tools(("iverilog", "vvp"))
    for vocabulary in (256, 257, 1, 255):
        boot_test(evidence, vocabulary, 17, reload=vocabulary == 257)


def run_large_images(evidence):
    evidence.tools(("iverilog", "vvp"))
    run_watchdog_width(evidence)
    evidence.run_cases([
        (f"large-image-{vocabulary}", lambda scope, vocabulary=vocabulary:
         boot_test(scope, vocabulary, 17, capacity=vocabulary))
        for vocabulary in (128256, 151936, 262144)
    ])


CONFIG = r"""
module bench;
  reg clk=0;
  reg rst_n;
  always #5 clk=~clk;
  reg cfg_valid=0,cfg_write=0,cfg_rsp_ready=0;
  reg [31:0] cfg_addr=0,cfg_wdata=0;
  wire cfg_ready,cfg_rsp_valid,cfg_rsp_error;
  wire [31:0] cfg_rdata;
  reg [3:0] status=1;
  reg [7:0] transaction_error_code=0;
  reg write_allowed=1,reload_allowed=1,publish=0;
  reg [223:0] committed_config_words=0;
  wire reload_request,publish_error,serial_update;
  wire [31:0] uart_divisor,eos_token_id,max_new_tokens,transport,profile_id,vocab_size,uart_frame_bytes;
  anvil_edge_config #(.VOCAB_SIZE(@CAPACITY@),.MAX_SEQ_LEN(16)) dut(.*);
  integer comparisons=0,reloads=0,serial_updates=0,requests=0,responses=0;
  task automatic reset_check;
    begin
      if ({cfg_ready,cfg_rsp_valid,cfg_rsp_error,cfg_rdata,reload_request,
           publish_error,serial_update,uart_divisor,eos_token_id,max_new_tokens,
           transport,profile_id,vocab_size,uart_frame_bytes}!==262'd0)
        $fatal(1,"CONFIG_RESET");
    end
  endtask
  always @(posedge clk or negedge clk) if (!rst_n) reset_check();
  always @(posedge clk) if (rst_n) begin
    if ((^{cfg_ready,cfg_rsp_valid,cfg_rsp_error,cfg_rdata,reload_request,
           publish_error,serial_update,uart_divisor,eos_token_id,max_new_tokens,
           transport,profile_id,vocab_size,uart_frame_bytes})===1'bx)
      $fatal(1,"CONFIG_XZ");
    if (cfg_valid && cfg_ready) requests=requests+1;
    if (cfg_rsp_valid && cfg_rsp_ready) responses=responses+1;
    if (reload_request) reloads=reloads+1;
    if (serial_update) serial_updates=serial_updates+1;
  end
  task automatic tick; begin @(posedge clk); #1; end endtask
  task automatic transact(input bit wr,input [31:0] address,input [31:0] data,
                          input bit expected_error,input [31:0] expected_data);
    begin
      @(negedge clk); #1; cfg_valid=1; cfg_write=wr; cfg_addr=address; cfg_wdata=data;
      do begin @(posedge clk); end while (!cfg_ready);
      #1; @(negedge clk); #1; cfg_valid=0;
      while (!cfg_rsp_valid) tick();
      repeat (5) begin
        if (cfg_rsp_valid!==1 || cfg_rsp_error!==expected_error ||
            cfg_rdata!==expected_data || cfg_ready!==0)
          $fatal(1,"CONFIG_RESPONSE address=%h error=%b data=%h expected=%h",
                 address,cfg_rsp_error,cfg_rdata,expected_data);
        tick();
      end
      @(negedge clk); #1; cfg_rsp_ready=1; tick();
      @(negedge clk); #1; cfg_rsp_ready=0;
      if (cfg_rsp_valid!==0) $fatal(1,"CONFIG_DUPLICATE_RESPONSE");
      comparisons=comparisons+1;
    end
  endtask
  task automatic publication(input integer vocabulary,input integer profile,
                             input bit expected_error);
    begin
      @(negedge clk); #1;
      committed_config_words={32'd0,32'(vocabulary),32'(profile),32'd1,32'd8,32'd255,32'd5};
      publish=1; tick();
      @(negedge clk); #1; publish=0;
      if (publish_error!==expected_error) $fatal(1,"CONFIG_PUBLICATION");
      comparisons=comparisons+1;
    end
  endtask
  initial begin
    rst_n=0; #0; reset_check(); repeat (2) tick();
    @(negedge clk); #1; rst_n=1;
    publication(256,1,0);
    transact(0,24,0,0,256);
    @CASES@
    transact(1,24,257,0,0);
    transact(0,24,0,0,257);
    if (vocab_size!==256) $fatal(1,"CONFIG_EARLY_REINTERPRETATION");
    comparisons=comparisons+1;
    publication(257,1,0);
    if (vocab_size!==257) $fatal(1,"CONFIG_COMMIT");
    comparisons=comparisons+1;
    write_allowed=0;
    transact(1,24,256,1,0); transact(0,24,0,0,257);
    write_allowed=1;
    transact(1,0,1,1,0); transact(1,32,1,1,0);
    transact(1,25,256,1,0); transact(0,40,0,1,0);
    transact(1,4,3,1,0); transact(0,4,0,0,5);
    transact(1,8,257,1,0); transact(0,8,0,0,255);
    transact(1,12,17,1,0); transact(0,12,0,0,8);
    transact(1,16,2,1,0); transact(0,16,0,0,1);
    transact(1,20,0,1,0); transact(0,20,0,0,1);
    transact(1,28,3,1,0);
    reload_allowed=0; transact(1,28,1,1,0);
    reload_allowed=1; transact(1,28,1,0,0);
    if (reloads!=1 || serial_updates!=0) $fatal(1,"CONFIG_COMMAND_SIDE_EFFECTS");
    comparisons=comparisons+1;
    transact(1,24,256,0,0);
    publication(257,1,1);
    if (vocab_size!==257) $fatal(1,"CONFIG_FAILED_PUBLICATION_MUTATION");
    comparisons=comparisons+1;
    transact(0,24,0,0,256);
    publication(256,1,0);
    if (vocab_size!==256 || publish_error) $fatal(1,"CONFIG_RECOVERY");
    comparisons=comparisons+1;
    if (requests!=responses || requests==0) $fatal(1,"CONFIG_COUNTS");
    if (comparisons!=@COMPARISONS@) $fatal(1,"CONFIG_COMPARISONS %0d",comparisons);
    $display("COMPARED %0d",comparisons); $finish;
  end
endmodule
"""


def run_config(evidence):
    evidence.tools(("iverilog", "vvp"))
    for capacity in (257, 262144):
        cases = []
        staged = 256
        for value in (1, 255, 0, 262145, capacity + 1, 257, 151936, 128256, 262144):
            legal = 256 <= value <= min(262144, capacity)
            if legal:
                staged = value
            cases.extend([
                f"transact(1,24,{value},{int(not legal)},0);",
                f"transact(0,24,0,0,{staged});",
                'if (vocab_size!==256) $fatal(1,"CONFIG_ILLEGAL_ACTIVE_MUTATION");',
                "comparisons=comparisons+1;",
            ])
        # One publication, one read, 27 boundary comparisons, then 31 fixed checks.
        bench = CONFIG.replace("@CAPACITY@", str(capacity)).replace("@CASES@", "\n".join(cases))
        bench = bench.replace("@COMPARISONS@", "60")
        evidence.simulate(f"config-v{capacity}", bench, ["rtl/anvil_edge_config.sv"], 60)


MAPPER = r"""
module bench;
  reg clk=0;
  reg rst_n;
  always #5 clk=~clk;
  reg config_valid=1;
  reg [63:0] cfg_directory_base=@DIRECTORY@,cfg_immutable_base=@IMMUTABLE@;
  reg [63:0] cfg_writable_base=@WRITABLE@;
  reg [31:0] cfg_directory_count=32;
  reg [63:0] cfg_immutable_bytes=@IMMUTABLE_BYTES@,cfg_writable_bytes=@WRITABLE_BYTES@;
  reg mem_req_valid=0,mem_req_write=0,mem_rsp_ready=0;
  reg [3:0] mem_req_kind=0;
  reg [31:0] mem_req_layer=0,mem_req_row=0,mem_req_col=0,mem_req_wdata=0;
  reg [2:0] mem_req_proj=0;
  wire mem_req_ready,mem_rsp_valid,mem_rsp_error,idle;
  wire [31:0] mem_rsp_rdata;
  wire ddr_req_valid,ddr_req_write,ddr_rsp_ready;
  wire [63:0] ddr_req_addr;
  wire [31:0] ddr_req_wdata;
  wire [3:0] ddr_req_wstrb;
  reg ddr_req_ready=0,ddr_rsp_valid=0,ddr_rsp_error=0;
  reg [31:0] ddr_rsp_rdata=0;
  anvil_edge_tensor_mapper #(
    .NUM_LAYERS(1),.HIDDEN_SIZE(8),.INTERMEDIATE_SIZE(8),
    .NUM_Q_HEADS(1),.NUM_KV_HEADS(1),.HEAD_DIM(8),.GROUP_SIZE(8),
    .VOCAB_SIZE(257),.MAX_SEQ_LEN(4),.DDR_BYTES(65536)
  ) dut(.*);
  reg [31:0] directory[0:391];
  reg [31:0] rng=@SEED@;
  reg outstanding=0,held=0,expected_error=0,expected_write=0,inject_error=0;
  reg [63:0] held_addr=0,pending_address=0,expected_address=0;
  reg [36:0] held_fields=0;
  reg pending_data=0;
  integer cycle=0,delay_count=0,data_requests=0,all_requests=0,comparisons=0;
  integer request_stalls=0;
  function automatic [31:0] value_at(input [63:0] address);
    begin
      if (address>=cfg_directory_base && address<cfg_directory_base+1568)
        value_at=directory[(address-cfg_directory_base)>>2];
      else value_at=32'(address*32'h9e3779b9)^32'ha5c31927;
    end
  endfunction
  task automatic reset_check;
    begin
      if ({mem_req_ready,mem_rsp_valid,mem_rsp_error,mem_rsp_rdata,idle,
           ddr_req_valid,ddr_req_write,ddr_req_addr,ddr_req_wdata,ddr_req_wstrb,
           ddr_rsp_ready}!==139'd0) $fatal(1,"MAPPER_RESET");
    end
  endtask
  always @(posedge clk or negedge clk) if (!rst_n) reset_check();
  always @(negedge clk) if (rst_n) begin
    rng=rng ^ (rng<<13); rng=rng ^ (rng>>17); rng=rng ^ (rng<<5);
    ddr_req_ready=rng[0] && cycle%5!=0;
    if (outstanding && !ddr_rsp_valid) begin
      if (delay_count==0) begin
        ddr_rsp_valid<=1; ddr_rsp_rdata=value_at(pending_address);
        ddr_rsp_error=pending_data && inject_error;
      end else delay_count=delay_count-1;
    end
  end
  always @(posedge clk) begin
    cycle=cycle+1;
    if (rst_n) begin
      if ((^{mem_req_ready,mem_rsp_valid,mem_rsp_error,mem_rsp_rdata,idle,
             ddr_req_valid,ddr_req_write,ddr_req_addr,ddr_req_wdata,ddr_req_wstrb,
             ddr_rsp_ready})===1'bx) $fatal(1,"MAPPER_XZ");
      if (held && (!ddr_req_valid || ddr_req_addr!==held_addr ||
          {ddr_req_write,ddr_req_wdata,ddr_req_wstrb}!==held_fields))
        $fatal(1,"MAPPER_REQUEST_STABILITY");
      held=ddr_req_valid && !ddr_req_ready;
      held_addr=ddr_req_addr; held_fields={ddr_req_write,ddr_req_wdata,ddr_req_wstrb};
      if (held) request_stalls=request_stalls+1;
      if (ddr_rsp_valid && ddr_rsp_ready) begin
        if (!outstanding) $fatal(1,"MAPPER_ORPHAN_RESPONSE");
        outstanding=0; ddr_rsp_valid<=0;
      end
      if (ddr_req_valid && ddr_req_ready) begin
        if (outstanding || (expected_error && !inject_error) || ddr_req_addr[1:0]!=0)
          $fatal(1,"MAPPER_FORBIDDEN_REQUEST kind=%0d row=%0d col=%0d",
                 mem_req_kind,mem_req_row,mem_req_col);
        all_requests=all_requests+1;
        pending_data=!(ddr_req_addr>=cfg_directory_base &&
                       ddr_req_addr<cfg_directory_base+1568);
        if (pending_data) begin
          if (data_requests!=0 || ddr_req_addr!==expected_address ||
              ddr_req_write!==expected_write ||
              ddr_req_wstrb!==(expected_write ? 4'hf : 4'h0) ||
              (expected_write && ddr_req_wdata!==mem_req_wdata))
            $fatal(1,"MAPPER_DATA_ADDRESS expected=%h observed=%h",
                   expected_address,ddr_req_addr);
          data_requests=data_requests+1;
        end else if (ddr_req_write || ddr_req_wstrb!==0)
          $fatal(1,"MAPPER_DIRECTORY_WRITE");
        outstanding=1; pending_address=ddr_req_addr; delay_count=1+rng[4:2];
      end
    end
  end
  task automatic tick; begin @(posedge clk); #1; end endtask
  task automatic transaction(input bit wr,input integer kind,input integer layer,
                             input integer projection,input integer row,input integer col,
                             input [63:0] address,input bit bad,input bit bus_error);
    integer previous_requests;
    begin
      @(negedge clk); #1;
      expected_error=bad; expected_write=wr; expected_address=address;
      inject_error=bus_error; data_requests=0; previous_requests=all_requests;
      mem_req_valid=1; mem_req_write=wr; mem_req_kind=kind; mem_req_layer=layer;
      mem_req_proj=projection; mem_req_row=row; mem_req_col=col;
      mem_req_wdata=32'h81478521;
      do begin @(posedge clk); end while (!mem_req_ready);
      #1; @(negedge clk); #1; mem_req_valid=0;
      while (!mem_rsp_valid) tick();
      repeat (5) begin
        if (mem_rsp_valid!==1 || mem_rsp_error!==bad ||
            mem_rsp_rdata!==(bad ? 32'd0 : value_at(address)) || mem_req_ready!==0)
          $fatal(1,"MAPPER_RESPONSE kind=%0d row=%0d col=%0d error=%b data=%h",
                 kind,row,col,mem_rsp_error,mem_rsp_rdata);
        tick();
      end
      if (outstanding || data_requests!=(bad && !bus_error ? 0 : 1) ||
          (bad && !bus_error && all_requests!=previous_requests))
        $fatal(1,"MAPPER_COUNTS");
      @(negedge clk); #1; mem_rsp_ready=1; tick();
      @(negedge clk); #1; mem_rsp_ready=0;
      if (mem_rsp_valid || !idle) $fatal(1,"MAPPER_RETIREMENT");
      comparisons=comparisons+1;
    end
  endtask
  initial begin
    rst_n=0; #0; reset_check();
    $readmemh("@DIRECTORY_FILE@",directory);
    repeat (2) tick(); @(negedge clk); #1; rst_n=1;
    @TRANSACTIONS@
    if (comparisons!=@COMPARISONS@ || request_stalls==0)
      $fatal(1,"MAPPER_REQUIRED_COUNTS comparisons=%0d",comparisons);
    $display("MAPPER_DDR_REQUESTS %0d",all_requests);
    $display("COMPARED %0d",comparisons); $finish;
  end
  initial begin
    repeat (1000000) @(posedge clk); $fatal(1,"MAPPER_CYCLE_BOUND");
  end
endmodule
"""


def mapper_test(evidence, fixture):
    geometry = fixture["geometry"]
    h, i = geometry["hidden"], geometry["intermediate"]
    t = geometry["kv_heads"] * geometry["head_dim"]
    lengths = {0: h, 1: h, 2: h, 3: t, 4: t, 5: h, 6: h, 7: h,
               8: h, 9: i, 10: i, 11: i, 12: h, 14: h}
    suffix = "" if h == i == 8 and geometry["layers"] == 1 else f"-h{h}-l{geometry['layers']}"
    for seed in (1, 17, 89):
        directory = evidence.path / f"mapper{suffix}-s{seed}-input"
        directory.mkdir()
        source = directory / "directory.hex"
        data = fixture["segments"][0x101]
        source.write_text("".join(f"{int.from_bytes(data[i:i+4], 'little'):08x}\n"
                                  for i in range(0, len(data), 4)), encoding="ascii")
        transactions = []
        for record in fixture["regions"]:
            kind, layer, projection, storage, offset, rows, columns, _, permissions, _ = record
            coordinates = ([(row, column) for row, length in lengths.items()
                            for column in (0, length - 1)] if kind == 8 else
                           [(0, 0), (rows - 1, columns - 1)])
            for row, column in coordinates:
                base = fixture["destinations"][storage]
                address = base + offset + 4 * (row * columns + column)
                transactions.append((0, kind, layer, projection, row, column, address, 0, 0))
                if permissions == 3:
                    transactions.append((1, kind, layer, projection, row, column, address, 0, 0))
            transactions.extend([
                (0, kind, layer, projection, rows, 0, 0, 1, 0),
                (0, kind, layer, projection, 0, columns, 0, 1, 0),
            ])
            if permissions == 1:
                transactions.append((1, kind, layer, projection, 0, 0, 0, 1, 0))
            if kind == 8:
                transactions.extend((0, kind, layer, projection, row, length, 0, 1, 0)
                                    for row, length in lengths.items())
        transactions.extend([
            (0, 8, 0, 0, 13, 0, 0, 1, 0),
            (0, 4, 0, 3, 0, 0, 0, 1, 0),
            (0, 9, geometry["layers"], 0, 0, 0, 0, 1, 0),
            (0, 0, 1, 0, 0, 0, 0, 1, 0),
            (0, 5, 0, 1, 0, 0, 0, 1, 0),
            (0, 9, 0, 1, 0, 0, 0, 1, 0),
            (0, 15, 0, 0, 0, 0, 0, 1, 0),
            (0, 0, 0, 0, 0, 0, fixture["destinations"][0x102], 1, 1),
        ])
        parameters = {
            "SEED": str(seed), "DIRECTORY": str(fixture["destinations"][0x101]),
            "IMMUTABLE": str(fixture["destinations"][0x102]),
            "WRITABLE": str(fixture["destinations"][0x103]),
            "IMMUTABLE_BYTES": str(len(fixture["segments"][0x102])),
            "WRITABLE_BYTES": str(len(fixture["segments"][0x103])),
            "DIRECTORY_FILE": evidence.relative(source),
            "TRANSACTIONS": "\n".join("transaction(" + ",".join(map(str, row)) + ");"
                                      for row in transactions),
            "COMPARISONS": str(len(transactions)),
        }
        bench = MAPPER
        substitutions = {
            ".NUM_LAYERS(1)": f".NUM_LAYERS({geometry['layers']})",
            ".HIDDEN_SIZE(8)": f".HIDDEN_SIZE({h})",
            ".INTERMEDIATE_SIZE(8)": f".INTERMEDIATE_SIZE({i})",
            ".NUM_Q_HEADS(1)": f".NUM_Q_HEADS({geometry['query_heads']})",
            ".NUM_KV_HEADS(1)": f".NUM_KV_HEADS({geometry['kv_heads']})",
            ".HEAD_DIM(8)": f".HEAD_DIM({geometry['head_dim']})",
            ".GROUP_SIZE(8)": f".GROUP_SIZE({geometry['group']})",
            ".MAX_SEQ_LEN(4)": f".MAX_SEQ_LEN({geometry['sequence']})",
            "cfg_directory_count=32": f"cfg_directory_count={len(fixture['regions'])}",
            "directory[0:391]": f"directory[0:{len(data)//4-1}]",
            "+1568": f"+{len(data)}",
        }
        for before, after in substitutions.items():
            bench = bench.replace(before, after)
        for key, value in parameters.items():
            bench = bench.replace(f"@{key}@", value)
        evidence.simulate(f"mapper{suffix}-s{seed}", bench, [
            "rtl/anvil_edge_parameters.sv", "rtl/anvil_edge_signed_multiplier.sv",
            "rtl/anvil_edge_tensor_mapper.sv",
        ], len(transactions))


def run_mapper(evidence):
    evidence.tools(("iverilog", "vvp"))
    mapper_test(evidence, synthetic_image(257))
    mapper_test(evidence, synthetic_image(257, geometry={
        "layers": 2, "hidden": 16, "intermediate": 24, "query_heads": 2,
    }))


def top_test(evidence, seed=17, uart=False, *, reset_phase=None, startup_only=False,
             text_profile=None, input_fault=None, reload_after=False,
             reload_profile=False, interaction=None):
    """Real minimum-geometry Q1; zero tensors have independently exact zero logits."""
    raw_prompt = b"ABC"
    # The base fixture has the AB merge, so ABC prefills [256,67].
    expected_prompt = [256, 67]
    if reload_profile:
        if text_profile is not None or input_fault or reset_phase:
            raise ValueError("Profile reload requires its dedicated fixture")
        text_profile = ("nfc-bos-to-nfd", "e\u0301", {"mode": 1, "bos": True})
        reload_after = True
    fixture = synthetic_image(257, max_pretoken=16, transport=int(not uart))
    name = f"top-synthetic-q1-{'uart-' if uart else ''}s{seed}"
    if text_profile is not None:
        from text import tokenizer_fixture, tokenizer_reference
        label, text, options = text_profile
        profile = tokenizer_fixture(text, **options)
        _, _, _, metadata, specials, merges = profile
        expected_prompt = tokenizer_reference(
            text, specials, options.get("mode", 0), options.get("policy", 0),
            options.get("bos", False), merges, options.get("dfa_kind", "longest"))
        raw_prompt = text.encode("utf-8")
        fixture = synthetic_image(
            metadata[2], capacity=metadata[2], max_pretoken=16,
            transport=int(not uart), geometry={"sequence": 16}, tokenizer=profile)
        name += "-" + label
    expected_error = 0
    fault_prompt = None
    if input_fault is not None:
        malformed = {
            "overlong": (b"ABC\xc0\x80", 0x10),
            "surrogate": (b"ABC\xed\xa0\x80", 0x10),
            "range": (b"ABC\xf4\x90\x80\x80", 0x10),
            "incomplete": (b"ABC\xe2\x82", 0x10),
            "byte-capacity": (b"x" * 17, 0x30),
            "token-capacity": (b"ABC", 0x30),
            "empty-uart": (b"", 0x40),
            "stop-uart": (b"A", 0x40),
            "closed-uart": (b"ABC", 0x41),
        }
        fault_prompt, expected_error = malformed[input_fault]
        if input_fault.endswith("-uart") and not uart:
            raise ValueError("Serial fault requires UART transport")
        name += "-" + input_fault
    if reload_after:
        name += "-reload"
    if reset_phase:
        if reset_phase not in ("boot", "prefill", "tx"):
            raise ValueError("Unknown top reset phase")
        name += "-reset-" + reset_phase
    if startup_only:
        name += "-startup"
    if interaction is not None:
        if reset_phase or startup_only or text_profile or input_fault or reload_after:
            raise ValueError("Top interactions require their dedicated fixture")
        name += "-" + interaction
    directory = evidence.path / (name + "-input")
    directory.mkdir()
    reload_updates = ""
    if reload_profile:
        second_profile = tokenizer_fixture(text, mode=3)
        _, _, _, second_metadata, second_specials, second_merges = second_profile
        second_prompt = tokenizer_reference(
            text, second_specials, 3, 0, False, second_merges, "longest")
        if len(second_prompt) != len(expected_prompt) or second_prompt == expected_prompt:
            raise ValueError("Profile reload must distinguish equal-length token vectors")
        second_fixture = synthetic_image(
            second_metadata[2], capacity=second_metadata[2], max_pretoken=16,
            transport=int(not uart), geometry={"sequence": 16}, tokenizer=second_profile)
        if (second_fixture["destinations"] != fixture["destinations"]
                or len(second_fixture["writes"]) != len(fixture["writes"])):
            raise ValueError("Unexpected layout change in fixed-layout profile reload")
        second_flash = directory / "second-flash.hex"
        second_flash.write_text(
            "".join(f"{byte:02x}\n" for byte in second_fixture["image"]), encoding="ascii")
        reload_updates = f"""
    running=0;
    control(1,32'h14,1,0,0);
    control(1,32'h18,{fixture['vocabulary']},0,0);
    control(0,32'h18,0,0,{fixture['vocabulary']});
    $readmemh("{evidence.relative(second_flash)}",flash,0,{len(second_fixture['image'])-1});
"""
        for index, (old, new) in enumerate(zip(fixture["writes"], second_fixture["writes"])):
            if old[0] != new[0] or old[2] != new[2]:
                raise ValueError("Unexpected address/strobe change in fixed-layout reload")
            if old[1] != new[1]:
                reload_updates += f"    write_data[{index}]=32'h{new[1]:x};\n"
        for index, token in enumerate(second_prompt + [0]):
            reload_updates += f"    expected_tokens[{index}]=32'd{token};\n"
        import json
        (directory / "second-reference.json").write_text(json.dumps({
            "scope": "Synthetic profile-only reload; not official assets",
            "image_sha256": hashlib.sha256(second_fixture["image"]).hexdigest(),
            "expected_prompt_tokens": second_prompt, "expected_feedback_tokens": [0],
            "normalization": "NFD", "bos": False,
        }, indent=2) + "\n", encoding="ascii")
    import json
    (directory / "reference.json").write_text(json.dumps({
        "scope": "synthetic zero-tensor real-Q1 integration, not official assets",
        "raw_prompt_hex": (fault_prompt if input_fault else raw_prompt).hex(),
        "input_fault": input_fault, "expected_error": expected_error,
        "expected_prompt_tokens": [] if input_fault else expected_prompt,
        "expected_feedback_tokens": [] if input_fault else [0],
        "expected_output_hex": "" if input_fault else "0000",
        "recovery_transaction": {
            "raw_prompt_hex": raw_prompt.hex(),
            "expected_prompt_tokens": expected_prompt,
            "expected_feedback_tokens": [0], "expected_output_hex": "0000",
        } if reload_after and not reload_profile else None,
        "image_sha256": hashlib.sha256(fixture["image"]).hexdigest(),
    }, indent=2) + "\n", encoding="ascii")
    flash = directory / "flash.hex"
    flash.write_text("".join(f"{byte:02x}\n" for byte in fixture["image"]), encoding="ascii")
    vectors = []
    for index, (address, data, strobe) in enumerate(fixture["writes"]):
        vectors.append(f"write_address[{index}]=64'h{address:x}; "
                       f"write_data[{index}]=32'h{data:x}; write_strobe[{index}]=4'h{strobe:x};")
    for index, kind in enumerate(KINDS):
        vectors.append(f"segment_base[{index}]=64'h{fixture['destinations'][kind]:x}; "
                       f"segment_length[{index}]={len(fixture['segments'][kind])};")
    writable_base = fixture["destinations"][0x103]
    cache_bases = [
        writable_base + region[4] for region in fixture["regions"] if region[0] in (9, 10)
    ]
    bench = BOOT.replace("anvil_edge_ddr4_boot_loader #(", "anvil_edge_top #(")
    bench = bench.replace(".VOCAB_SIZE(257)", f".VOCAB_SIZE({fixture['capacity']})")
    bench = bench.replace(".MAX_SEQ_LEN(4)", f".MAX_SEQ_LEN({fixture['geometry']['sequence']})")
    bench = bench.replace(".DDR_BYTES(65536)", """
    .MAX_PROMPT_BYTES(16),.MAX_PROMPT_TOKENS(16),.MAX_PRETOKEN_BYTES(16),
    .MAX_TOKEN_BYTES(16),.RX_FIFO_DEPTH(3),.TX_FIFO_DEPTH(3),
    .DDR_BYTES(65536)""")
    if input_fault == "token-capacity":
        bench = bench.replace(".MAX_PROMPT_TOKENS(16)", ".MAX_PROMPT_TOKENS(1)")
    bench = bench.replace("reg start=0,ddr_cal_done=0,spi_miso=0;", """
  reg ddr_cal_done=0,spi_miso=0;
  reg uart_rx=1,s_axis_tvalid=0,s_axis_tlast=0,m_axis_tready=0;
  reg [7:0] s_axis_tdata=0;
  wire uart_tx,s_axis_tready,m_axis_tvalid,m_axis_tlast,done;
  wire [7:0] m_axis_tdata;
  reg cfg_valid=0,cfg_write=0,cfg_rsp_ready=0;
  reg [31:0] cfg_addr=0,cfg_wdata=0;
  wire cfg_ready,cfg_rsp_valid,cfg_rsp_error;
  wire [31:0] cfg_rdata;
  reg running=0,out_held=0;
  reg [8:0] held_output=0;
  integer outputs=0,completions=0,cache_k_writes=0,cache_v_writes=0;
  integer inference_reads=0,inference_writes=0;
  integer request_cycle=0;
  reg [63:0] inference_address=0;
  reg inference_write=0;
  always @(negedge clk) if (rst_n) m_axis_tready=rng[3] && cycle%7!=0;
  always @(posedge clk) if (rst_n && running) begin
    if ((^{done,error,m_axis_tvalid,m_axis_tlast,m_axis_tdata,s_axis_tready,
           uart_tx,cfg_rsp_valid,cfg_rsp_error,cfg_rdata})===1'bx)
      $fatal(1,"TOP_XZ");
    if (cfg_valid || cfg_write) $fatal(1,"TOP_HOST_INTERVENTION");
    if (error) $fatal(1,"TOP_INFERENCE_ERROR code=%h",error_code);
    if (out_held && (!m_axis_tvalid || {m_axis_tlast,m_axis_tdata}!==held_output))
      $fatal(1,"TOP_OUTPUT_STABILITY");
    out_held=m_axis_tvalid && !m_axis_tready;
    held_output={m_axis_tlast,m_axis_tdata};
    if (m_axis_tvalid && m_axis_tready) begin
      if (outputs>=2 || m_axis_tdata!==0 || m_axis_tlast!==(outputs==1))
        $fatal(1,"TOP_FIXED_POINT_OUTPUT item=%0d byte=%h last=%b",
               outputs,m_axis_tdata,m_axis_tlast);
      outputs=outputs+1; comparisons=comparisons+1;
    end
    if (done) begin
      if (outputs!=2 || completions!=0 || pending || m_axis_tvalid)
        $fatal(1,"TOP_OUTPUT_DRAIN");
      completions=completions+1;
    end
  end
  task automatic send_byte(input [7:0] value,input bit last);
    begin
      @(negedge clk); #1; s_axis_tvalid=1; s_axis_tdata=value; s_axis_tlast=last;
      do begin @(posedge clk); end while (!s_axis_tready);
      #1; @(negedge clk); #1; s_axis_tvalid=0;
    end
  endtask
""")
    bench = bench.replace(
        '$fatal(1,"BOOT_CYCLE_BOUND writes=%0d reads=%0d",writes,reads);',
        '$fatal(1,"TOP_CYCLE_BOUND cycle=%0d writes=%0d reads=%0d embedding=%0d '
        'cache_k=%0d cache_v=%0d outputs=%0d done=%0d error=%b code=%h busy=%b '
        'cfg_valid=%b cfg_ready=%b cfg_response=%b",cycle,writes,reads,embedding_reads,'
        'cache_k_writes,cache_v_writes,outputs,completions,error,error_code,busy,'
        'cfg_valid,cfg_ready,cfg_rsp_valid);')
    if reload_after or interaction == "semantic-failed-reload":
        # Two complete boot/inference epochs retain the one-epoch cycle budget each.
        bench = bench.replace("repeat (30000000)", "repeat (60000000)")
    # Committed loader bundle is not a public top port. Top is observed solely at
    # the declared public pins; boot loading remains byte/transaction checked.
    begin = bench.index("  wire [223:0] committed_config_words;")
    end = bench.index("  anvil_edge_top #(", begin)
    bench = bench[:begin] + bench[end:]
    begin = bench.index("  task automatic reset_check;")
    end = bench.index("  always @(posedge clk or negedge clk)", begin)
    bench = bench[:begin] + r"""
  task automatic reset_check;
    begin
      if ({spi_mosi,spi_sck,ddr_req_valid,ddr_req_write,ddr_req_addr,
           ddr_req_wdata,ddr_req_wstrb,ddr_rsp_ready,boot_done,busy,error,error_code,
           done,s_axis_tready,m_axis_tvalid,m_axis_tdata,m_axis_tlast,
           cfg_ready,cfg_rsp_valid,cfg_rsp_error,cfg_rdata}!==0 ||
          spi_cs_n!==1 || uart_tx!==1) $fatal(1,"TOP_RESET");
    end
  endtask
""" + bench[end:]
    bench = bench.replace("""             boot_done,busy,error,error_code,committed_config_words,
             committed_segment_bases,committed_segment_bytes,committed_metadata,
             committed_table_counts""", "             boot_done,busy,error,error_code")
    begin = bench.index("      if (!boot_done && {committed_config_words")
    end = bench.index("      if (held", begin)
    bench = bench[:begin] + bench[end:]
    bench = bench.replace("        if (ddr_req_write) begin", """
        if (running) begin
          if (!readable(ddr_req_addr)) $fatal(1,"TOP_MEMORY_BOUNDS");
          if (ddr_req_write) begin
            if (ddr_req_addr<segment_base[3] ||
                ddr_req_addr>=segment_base[3]+segment_length[3] ||
                ddr_req_wstrb!==4'hf)
              $fatal(1,"TOP_IMMUTABLE_WRITE");
            if (ddr_req_wdata!==0) $fatal(1,"TOP_ZERO_MODEL_ACTIVATION");
            if (ddr_req_addr>=@CACHE_K@ && ddr_req_addr<@CACHE_K@+128) begin
              if (ddr_req_addr!==@CACHE_K@+4*cache_k_writes)
                $fatal(1,"TOP_CACHE_K_POSITION");
              cache_k_writes=cache_k_writes+1;
            end
            if (ddr_req_addr>=@CACHE_V@ && ddr_req_addr<@CACHE_V@+128) begin
              if (ddr_req_addr!==@CACHE_V@+4*cache_v_writes)
                $fatal(1,"TOP_CACHE_V_POSITION");
              cache_v_writes=cache_v_writes+1;
            end
            for (integer lane=0;lane<4;lane=lane+1)
              ddr[ddr_req_addr+lane]=ddr_req_wdata[lane*8+:8];
            inference_writes=inference_writes+1;
          end else inference_reads=inference_reads+1;
        end else if (ddr_req_write) begin""")
    begin = bench.index("  task automatic wait_result(")
    end = bench.index("  integer i;", begin)
    bench = bench[:begin] + bench[end:]
    bench = bench.replace("    wait_result(@EXPECTED_ERROR@);\n    @RELOAD@", """
    while (!boot_done && !error) tick();
    if (error || writes!=@WRITES@ || pending || reads==0)
      $fatal(1,"TOP_BOOT_ERROR code=%h",error_code);
    while (busy) tick();
    running=1;
    send_byte(65,0); send_byte(66,0); send_byte(67,1);
    while (completions==0 && !error) tick();
    repeat (20) tick();
    if (completions!=1 || outputs!=2 || error || cache_k_writes!=24 ||
        cache_v_writes!=24 || inference_reads==0 || inference_writes==0)
      $fatal(1,"TOP_COUNTS done=%0d out=%0d k=%0d v=%0d",
             completions,outputs,cache_k_writes,cache_v_writes);
    comparisons=comparisons+1;
    $display("TOP_SYNTHETIC_REAL_Q1 output_bytes=%0d k_writes=%0d v_writes=%0d reads=%0d writes=%0d",
             outputs,cache_k_writes,cache_v_writes,inference_reads,inference_writes);
""")
    operations = len(expected_prompt) + 1
    expected_tokens = expected_prompt + [0]
    embedding_base = fixture["destinations"][0x102]
    embedding_words = fixture["capacity"] * 8
    bench = bench.replace("integer inference_reads=0,inference_writes=0;", f"""
  integer inference_reads=0,inference_writes=0;
  integer embedding_reads=0,operation_index=0,embedding_index=0;
  reg [31:0] expected_tokens[0:{operations-1}];
""")
    anchor = '          if (!readable(ddr_req_addr)) $fatal(1,"TOP_MEMORY_BOUNDS");'
    assert bench.count(anchor) == 1
    bench = bench.replace(anchor, anchor + f"""
          if (!ddr_req_write && ddr_req_addr>={embedding_base} &&
              ddr_req_addr<{embedding_base + embedding_words*4}) begin
            operation_index=embedding_reads/({embedding_words}+8);
            embedding_index=embedding_reads%({embedding_words}+8);
            if (operation_index>={operations})
              $fatal(1,"TOP_EXTRA_CORE_OPERATION");
            if (embedding_index<8) begin
              if (ddr_req_addr!==64'd{embedding_base}+
                  32*expected_tokens[operation_index]+4*embedding_index)
                $fatal(1,"TOP_PREFILL_TOKEN operation=%0d column=%0d address=%h token=%0d",
                       operation_index,embedding_index,ddr_req_addr,
                       expected_tokens[operation_index]);
            end else if (ddr_req_addr!==64'd{embedding_base}+4*(embedding_index-8))
              $fatal(1,"TOP_PROJECTION_ORDER");
            embedding_reads=embedding_reads+1;
            comparisons=comparisons+1;
          end
""")
    bench = bench.replace("cache_k_writes!=24", f"cache_k_writes!={operations*8}")
    bench = bench.replace("cache_v_writes!=24", f"cache_v_writes!={operations*8}")
    bench = bench.replace("inference_reads==0 || inference_writes==0)",
                          f"inference_reads==0 || inference_writes==0 || "
                          f"embedding_reads!={operations*(embedding_words+8)})")
    for token_index, token in enumerate(expected_tokens):
        vectors.append(f"expected_tokens[{token_index}]=32'd{token};")
    bench = bench.replace(
        "    send_byte(65,0); send_byte(66,0); send_byte(67,1);",
        "\n".join(f"    send_byte(8'h{value:02x},{int(index==len(raw_prompt)-1)});"
                  for index, value in enumerate(raw_prompt)))
    # Keep the fixed UART stimulus replacement below applicable to all profiles.
    serial_prompt_anchor = "\n".join(
        f"    send_byte(8'h{value:02x},{int(index==len(raw_prompt)-1)});"
        for index, value in enumerate(raw_prompt))
    parameters = {
        "FLASH": evidence.relative(flash), "FLASH_EXTENT": str(len(fixture["image"])),
        "SEED": str(seed), "WRITES": str(len(fixture["writes"])), "DDR_ERROR": "0",
        "VECTORS": "\n".join(vectors),
        "CACHE_K": str(cache_bases[0]), "CACHE_V": str(cache_bases[1]),
    }
    for key, value in parameters.items():
        bench = bench.replace(f"@{key}@", value)
    bench = bench.replace(f"+128)", f"+{fixture['geometry']['sequence']*32})")
    if uart:
        bench = bench.replace(
            "    if (m_axis_tvalid && m_axis_tready) begin",
            '    if (m_axis_tvalid) $fatal(1,"TOP_UART_BYPASS_LEAK");\n'
            "    if (m_axis_tvalid && m_axis_tready) begin",
        )
        begin = bench.index("  task automatic send_byte(")
        end = bench.index("  endtask", begin) + len("  endtask")
        bench = bench[:begin] + r"""
  task automatic serial_bit(input bit value);
    begin
      uart_rx=value;
      repeat (5) begin @(negedge clk); #1; end
    end
  endtask
  task automatic send_serial(input [7:0] value);
    begin
      serial_bit(0);
      for (integer bit_index=0;bit_index<8;bit_index=bit_index+1)
        serial_bit(value[bit_index]);
      serial_bit(1);
    end
  endtask
  task automatic decode_serial;
    reg [9:0] expected_frame;
    begin
      expected_frame=10'b1000000000;
      while (uart_tx!==0) tick();
      for (integer bit_index=0;bit_index<10;bit_index=bit_index+1)
        repeat (5) begin
          if (uart_tx!==expected_frame[bit_index] || done!==0)
            $fatal(1,"TOP_UART_EXACT_FRAME byte=%0d bit=%0d tx=%b done=%b",
                   outputs,bit_index,uart_tx,done);
          tick();
        end
      outputs=outputs+1; comparisons=comparisons+1;
    end
  endtask
""" + bench[end:]
        serial_stimulus = " ".join(f"send_serial(8'h{byte:02x});" for byte in raw_prompt)
        bench = bench.replace(serial_prompt_anchor, """
    fork
      begin
        @(negedge clk); #1;
        @SERIAL_STIMULUS@ send_serial(10);
      end
      begin decode_serial(); decode_serial(); end
    join
""".replace("@SERIAL_STIMULUS@", serial_stimulus))
    if reset_phase:
        bench = bench.replace("  reg running=0,out_held=0;", """
  reg running=0,out_held=0;
  reg block_output=0;
  integer reset_events=0;
""")
        bench = bench.replace(
            "m_axis_tready=rng[3] && cycle%7!=0;",
            "m_axis_tready=!block_output && rng[3] && cycle%7!=0;")
        reset_task = """
  task automatic reset_epoch;
    begin
      @(negedge clk); #1; running=0; rst_n=0;
      #0; reset_check();
      if (done!==0 || boot_done!==0 || error!==0)
        $fatal(1,"TOP_RESET_ABORT_STATUS");
      pending=0; ddr_rsp_valid<=0; ddr_rsp_error=0; held=0; out_held=0;
      writes=0; reads=0; acknowledgements=0; loading=1;
      outputs=0; completions=0; cache_k_writes=0; cache_v_writes=0;
      inference_reads=0; inference_writes=0; block_output=0;
      embedding_reads=0;
      s_axis_tvalid=0; uart_rx=1;
      repeat (3) tick();
      @(negedge clk); #1; rst_n=1;
      reset_events=reset_events+1; comparisons=comparisons+1;
    end
  endtask
"""
        position = bench.index("  integer i;")
        bench = bench[:position] + reset_task + bench[position:]
        boot_wait = "    while (!boot_done && !error) tick();"
        assert boot_wait in bench
        if reset_phase == "boot":
            prefix = """
    while (writes<10 && !error) tick();
    if (error || boot_done || writes!=10 || !pending || done)
      $fatal(1,"TOP_RESET_BOOT_EVENT");
    reset_epoch();
"""
        else:
            prompt = ("""
    @(negedge clk); #1;
    send_serial(65); send_serial(66); send_serial(67); send_serial(10);
""" if uart else "    send_byte(65,0); send_byte(66,0); send_byte(67,1);\n")
            wait_event = ("""
    while (cache_k_writes==0 && !error) tick();
    if (cache_k_writes!=1 || outputs || completions || done || error || !busy)
      $fatal(1,"TOP_RESET_PREFILL_EVENT");
""" if reset_phase == "prefill" else (
                """
    while (uart_tx!==0 && !error) tick();
    repeat (7) tick();
    if (uart_tx!==0 || outputs || completions || done || error || !busy)
      $fatal(1,"TOP_RESET_UART_TX_EVENT");
""" if uart else """
    while (!m_axis_tvalid && !error) tick();
    repeat (5) tick();
    if (!m_axis_tvalid || m_axis_tdata!==0 || m_axis_tready ||
        outputs || completions || done || error || !busy || s_axis_tready)
      $fatal(1,"TOP_RESET_TX_STALL_EVENT");
"""))
            prefix = boot_wait + """
    if (error || writes!=@WRITES@ || pending) $fatal(1,"TOP_RESET_FIRST_BOOT");
    while (busy) tick();
    running=1; block_output=1;
""" + prompt + wait_event + "    reset_epoch();\n"
            prefix = prefix.replace("@WRITES@", str(len(fixture["writes"])))
        bench = bench.replace(boot_wait, prefix + boot_wait, 1)
        position = bench.index('    $display("BOOT_TRANSACTIONS')
        bench = (bench[:position] +
                 '    if (reset_events!=1) $fatal(1,"TOP_RESET_EVENT_COUNT");\n' +
                 bench[position:])
    if startup_only:
        anchor = "    @(negedge clk); #1; ddr_cal_done=1;"
        if bench.count(anchor) != 1:
            raise RuntimeError("Missing unique top startup boundary")
        bench = bench.replace(anchor, """
    if (spi_cs_n!==1 || ddr_req_valid!==0 || boot_done!==0)
      $fatal(1,"TOP_STARTUP_CALIBRATION");
    $display("COMPARED 20");
    $finish;
""" + anchor)
    if input_fault or reload_after:
        bench = top_control_scenario(
            bench, fixture, raw_prompt, fault_prompt, expected_error,
            input_fault, reload_after, uart, operations, reload_updates)
    if interaction is not None:
        from interactions import top_interaction_bench
        bench = top_interaction_bench(
            evidence, bench, fixture, raw_prompt, operations, interaction, uart)
    root = Path(__file__).resolve().parent.parent
    evidence.simulate(name, bench, [
        "rtl/anvil_edge_numeric_pkg.sv",
        *[str(path.relative_to(root)) for path in sorted((root / "rtl").glob("*.sv"))
          if path.name != "anvil_edge_numeric_pkg.sv"],
    ], 20 if startup_only else None,
       simulator="iverilog" if startup_only else "verilator")


def top_control_scenario(bench, fixture, prompt, faulty_prompt, expected_error,
                         fault, reload_after, uart, operations, reload_updates):
    """Public CSR recovery and rejected-frame conservation, without DUT hierarchy."""
    def send(raw):
        if uart:
            return ("@(negedge clk); #1; " +
                    " ".join(f"send_serial(8'h{value:02x});" for value in raw) +
                    " send_serial(10);")
        return "\n".join(
            f"send_byte(8'h{value:02x},{int(index==len(raw)-1)});"
            for index, value in enumerate(raw))

    def exchange(raw):
        if uart:
            return f"""
    fork
      begin {send(raw)} end
      begin decode_serial(); decode_serial(); end
    join
"""
        return send(raw)
    bench = bench.replace("integer outputs=0,completions=0", """
  reg expect_rejection=0;
  integer observed_errors=0,control_requests=0,control_responses=0,reload_events=0;
  integer outputs=0,completions=0""")
    bench = bench.replace(
        '    if (error) $fatal(1,"TOP_INFERENCE_ERROR code=%h",error_code);',
        f"""    if (error && !expect_rejection)
      $fatal(1,"TOP_INFERENCE_ERROR code=%h",error_code);
    if (expect_rejection && (embedding_reads!=0 || inference_writes!=0 ||
                            m_axis_tvalid || done || uart_tx!==1))
      $fatal(1,"TOP_REJECTED_FRAME_PREFILL_OR_OUTPUT");""")
    bench = bench.replace(
        "do begin @(posedge clk); end while (!s_axis_tready);",
        "do begin @(posedge clk); end while (!s_axis_tready && !error);")
    # Do not keep trying to send after the capacity fault has closed admission.
    bench = bench.replace(
        "@(negedge clk); #1; s_axis_tvalid=1; s_axis_tdata=value; s_axis_tlast=last;",
        """if (!error) begin
      @(negedge clk); #1; s_axis_tvalid=1; s_axis_tdata=value; s_axis_tlast=last;""")
    bench = bench.replace(
        "#1; @(negedge clk); #1; s_axis_tvalid=0;",
        "#1; @(negedge clk); #1; s_axis_tvalid=0;\n      end")
    tasks = r"""
  task automatic control(input bit write,input [31:0] address,value,
                         input bit expect_error,input [31:0] expect_data);
    reg [32:0] response;
    begin
      @(negedge clk); #1;
      cfg_valid=1; cfg_write=write; cfg_addr=address; cfg_wdata=value;
      do begin @(posedge clk); end while (!cfg_ready);
      control_requests=control_requests+1;
      #1; @(negedge clk); #1; cfg_valid=0; cfg_write=0;
      while (!cfg_rsp_valid) tick();
      response={cfg_rsp_error,cfg_rdata};
      repeat (4) begin
        tick();
        if (!cfg_rsp_valid || {cfg_rsp_error,cfg_rdata}!==response)
          $fatal(1,"TOP_CONTROL_HELD_RESPONSE");
      end
      if (response!=={expect_error,expect_data})
        $fatal(1,"TOP_CONTROL_RESPONSE address=%h expected=%h observed=%h",
               address,{expect_error,expect_data},response);
      @(negedge clk); #1; cfg_rsp_ready=1; tick();
      control_responses=control_responses+1;
      @(negedge clk); #1; cfg_rsp_ready=0;
      comparisons=comparisons+1;
    end
  endtask
  task automatic reload_epoch;
    begin
      if (pending || ddr_rsp_valid || cfg_valid || cfg_rsp_valid)
        $fatal(1,"TOP_RELOAD_NOT_QUIESCENT");
      running=0; out_held=0;
      writes=0; reads=0; acknowledgements=0; loading=1;
      outputs=0; completions=0; cache_k_writes=0; cache_v_writes=0;
      inference_reads=0; inference_writes=0; embedding_reads=0;
      control(1,32'h1c,1,0,0);
      if (boot_done || error || s_axis_tready || done)
        $fatal(1,"TOP_RELOAD_ADMISSION_NOT_WITHDRAWN");
      reload_events=reload_events+1;
      while (!boot_done && !error) tick();
      if (error || pending || writes!=@RELOAD_WRITES@ || reads==0 ||
          acknowledgements!=writes+reads)
        $fatal(1,"TOP_RELOAD_COMMIT");
      while (busy) tick();
      control(0,0,0,0,1);
      expect_rejection=0; running=1;
      comparisons=comparisons+1;
    end
  endtask
""".replace("@RELOAD_WRITES@", str(len(fixture["writes"])))
    position = bench.index("  integer i;")
    bench = bench[:position] + tasks + bench[position:]
    first = bench.index("    running=1;\n", bench.index("  initial begin\n    rst_n=0;"))
    terminal = bench.index('    $display("BOOT_TRANSACTIONS', first)
    success = f"""
    while (completions==0 && !error) tick();
    repeat (20) tick();
    if (completions!=1 || outputs!=2 || error || pending ||
        cache_k_writes!={operations*8} || cache_v_writes!={operations*8} ||
        embedding_reads!={operations*(fixture['capacity']*8+8)} ||
        inference_writes==0)
      $fatal(1,"TOP_CONTROL_SUCCESS_COUNTS");
    comparisons=comparisons+1;
"""
    scenario = "    running=1;\n"
    if fault:
        stimulus = send(faulty_prompt)
        if fault == "stop-uart":
            stimulus = """
    @(negedge clk); #1; serial_bit(0);
    for (integer n=0;n<8;n=n+1) serial_bit(n==0);
    serial_bit(0); serial_bit(1);
"""
        elif fault == "closed-uart":
            stimulus += "\n    send_serial(90);"
        scenario += "    expect_rejection=1;\n" + stimulus + f"""
    while (!error && !done) tick();
    repeat (20) begin
      tick();
      if (error!==1 || error_code!==8'h{expected_error:02x} ||
          done || busy || s_axis_tready || m_axis_tvalid || uart_tx!==1 ||
          outputs || completions || embedding_reads || inference_writes)
        $fatal(1,"TOP_FRAME_REJECTION expected=%h observed=%h",
               8'h{expected_error:02x},error_code);
    end
    if (pending) $fatal(1,"TOP_REJECTION_UNSETTLED");
    observed_errors=observed_errors+1; comparisons=comparisons+1;
    running=0;
    control(0,32'h20,0,0,32'h{expected_error:02x});
    control(0,0,0,0,9);
    control(1,32'h18,255,1,0);
    control(0,32'h20,0,0,32'h{expected_error:02x});
"""
    else:
        scenario += exchange(prompt) + success
    if reload_after:
        scenario += reload_updates + "    reload_epoch();\n" + exchange(prompt)
        scenario += success + """
    if (reload_events!=1) $fatal(1,"TOP_RELOAD_EVENT_COUNT");
"""
    scenario += f"""
    if (control_requests!=control_responses ||
        observed_errors!={int(fault is not None)})
      $fatal(1,"TOP_CONTROL_CONSERVATION");
    $display("TOP_CONTROL errors=%0d reloads=%0d controls=%0d",
             observed_errors,reload_events,control_responses);
"""
    return bench[:first] + scenario + bench[terminal:]


def run_top(evidence):
    evidence.tools(("iverilog", "vvp"))
    top_test(evidence, 89, uart=True, startup_only=True)
    evidence.run_cases([
        (f"top-{seed}-uart-{uart}",
         lambda scope, seed=seed, uart=uart: top_test(scope, seed, uart=uart))
        for seed in (1, 17, 89) for uart in (False, True)
    ])
    run_top_profiles(evidence)
    run_top_errors(evidence)
    run_top_reload(evidence)
    from interactions import run_top_interactions
    run_top_interactions(evidence)


def run_top_profiles(evidence):
    examples = (
        ("nfc-bos", "e\u0301", {"mode": 1, "bos": True}),
        ("nfkc", "\uff21B", {"mode": 2}),
        ("tagged-shortest", "AB", {"dfa_kind": "shortest"}),
        ("tagged-lookahead", "A\u00e9", {"dfa_kind": "lookahead-rewind"}),
        ("raw-special-bos", "<X>", {"policy": 1, "bos": True,
                                   "special_options": (("<X>", 1),)}),
        ("normalized-special", "e\u0301", {"mode": 1, "policy": 1,
                                         "special_options": (("\u00e9", 17),)}),
    )
    evidence.run_cases([
        (f"top-profile-{seed}-{profile[0]}",
         lambda scope, seed=seed, profile=profile: top_test(scope, seed, text_profile=profile))
        for seed in (1, 17, 89) for profile in examples
    ])
    run_top_profile_uart(evidence)


def run_top_profile_uart(evidence):
    top_test(evidence, 17, uart=True,
             text_profile=("nfc-bos", "e\u0301", {"mode": 1, "bos": True}))


def run_top_errors(evidence):
    evidence.run_cases([
        (f"top-error-{seed}-{fault}",
         lambda scope, seed=seed, fault=fault, uart=uart:
         top_test(scope, seed, uart=uart, input_fault=fault))
        for seed in (1, 17, 89) for uart, faults in (
            (False, ("overlong", "surrogate", "range", "incomplete", "byte-capacity")),
            (True, ("empty-uart", "stop-uart", "closed-uart")))
        for fault in faults
    ])
    from interactions import run_top_token_capacity
    run_top_token_capacity(evidence)


def run_top_reload(evidence):
    evidence.run_cases([
        (f"top-reload-{seed}-{fault}",
         lambda scope, seed=seed, fault=fault:
         top_test(scope, seed, input_fault=fault, reload_after=True))
        for seed in (1, 17, 89) for fault in (None, "overlong")
    ])
    run_top_profile_reload(evidence)
    top_test(evidence, 17, uart=True, reload_after=True)


def run_top_profile_reload(evidence):
    evidence.run_cases([
        (f"top-profile-reload-{seed}",
         lambda scope, seed=seed: top_test(scope, seed, reload_profile=True))
        for seed in (1, 17, 89)
    ])


def run_top_uart(evidence):
    evidence.tools(("iverilog", "vvp"))
    top_test(evidence, 17, uart=True)


def run_top_resets(evidence):
    evidence.tools(("iverilog", "vvp"))
    evidence.run_cases([
        (f"top-reset-{seed}-{phase}-uart-{uart}",
         lambda scope, seed=seed, phase=phase, uart=uart:
         top_test(scope, seed, uart=uart, reset_phase=phase))
        for seed in (1, 17, 89) for phase, uart in (
            ("boot", False), ("prefill", False), ("tx", False), ("tx", True))
    ])
