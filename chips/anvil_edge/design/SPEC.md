# Anvil-Edge v3.0.0-edge-standalone

## Authority and implementation status

The independently admitted ANVLEDG3 version-1 work order is normative. This
document records implementation decisions; it does not reduce its acceptance
matrix. The admitted tokenizer metadata-version-2 extension preserves the
flash format version 1 and metadata-version-1 behavior; `STORAGE.md` defines
the separate classification/special-property, normalization/combining-class
and regex case-folding version fields. The current source increment connects the production shell at
`anvil_edge_top`; the actual board wrapper/controller/pins remain unavailable.
No functional, synthesis, timing, model, or board acceptance is
claimed. The supplied `anvil_q1_reference/rtl/` is read-only provenance, not
validated production logic.

Design owns `rtl/*.sv`, `design/*.md`, and `fpga/*`. Independent verification
owns `tests/*.py` and `tests/data/*`. Production literally instantiates the
seven named shell modules and a timing-safe derived `anvil_q1_top`.

## Clock and reset

All new modules use `clk` and asynchronous active-low reset assertion. Reset
deassertion must be synchronized externally. Active reset suppresses all
handshakes, status pulses, and error outputs; UART TX is high. Data outputs
are zero during reset. There are no derived UART clocks.

The target is Intel Arria 10 GX 10AX115N2F45E1SG at a clock period no greater
than 10.0 ns. Static elaboration is not timing acceptance.

## Cycle & Degenerate-Boundary Table

| Boundary | Required implementation behavior |
| --- | --- |
| Transfer at E0 | Sample pre-edge `valid && ready`; state and occupancy change post-edge. |
| Empty FIFO push | No combinational fall-through; the registered head is available after E0. |
| Nonempty simultaneous pop/push | Consumer gets the old head; occupancy is unchanged. |
| Full simultaneous pop/push | Push is accepted when the old head is accepted. |
| FIFO depth 1 | One physical entry; pointer is held at zero; replacement follows the same old-head rule. |
| FIFO depth 3 | Explicit terminal wrap; binary overflow is not used as wrap. |
| Reset | Reset overrides transfer, completion, and error; no transfer is accepted. |
| First clock after reset | Only pre-edge admitted handshakes count; no invented request or completion. |
| One prompt token | `prompt_valid && prompt_ready && prompt_last` captures the entire prompt. |
| Prompt capacity 1 | The first nonfinal token reports capacity error; it cannot start prefill. |
| Final logit plus done | Register the winner at that edge; decide only at a later edge. |
| Generated-token stall | ID and last remain stable; no feedback request is launched. |
| Finish stall | Finish remains asserted; it cannot pass an older generated token. |
| UART FIFO overflow | Sticky explicit transport error; never silently claim successful input. |

## Error codes

Codes are stable unsigned bytes. Errors are sticky in standalone engines until
reset; integration must reset their transaction epoch on an admitted idle
reload. A successful `done` is never asserted with `error`.

| Code | Meaning |
| --- | --- |
| `00` | No error |
| `01` | Boot header/configuration |
| `02` | Boot descriptor/interval |
| `03` | Payload CRC |
| `04` | DDR request/response failure |
| `05` | Geometry/directory mismatch |
| `06` | Table semantics/metadata |
| `10` | Invalid UTF-8 |
| `11` | Token/table bounds |
| `12` | Malformed tokenizer profile |
| `13` | Enabled raw special rejected by the committed profile policy |
| `20` | Core-reported protocol/numerical error |
| `21` | Logit frame count/index/completion violation |
| `30` | Prompt byte/token capacity |
| `31` | Sequence position limit |
| `32` | Illegal controller configuration |
| `40` | UART framing |
| `41` | UART receive overflow |

Top-level first-error priority remains boot/memory, input/table, core,
sequence/capacity, then UART.

## Public tokenizer integration contract

The tokenizer's additional internal configuration ports are `config_valid`,
`cfg_table_bases[1023:0]`, `cfg_table_counts[511:0]` and
`cfg_metadata[1023:0]`. Table slot `i` denotes kind `0x200+i`, in the same
low-slot-first packing as the boot bundle; metadata words retain serialized
order. Configuration remains stable from start through completion.
Parameters `MAX_PROMPT_BYTES`, `MAX_PROMPT_TOKENS`, `MAX_PRETOKEN_BYTES`
default to 4096; `MAX_TAG_REGISTERS` defaults to 32. All capacities are
positive and tag capacity is at least 32.

The internal `anvil_edge_special_splitter` accepts a complete nonempty scalar
span with `in_valid/ready`, `in_scalar[31:0]`, `in_last` and `start`.
Its packed configuration is identical to the tokenizer's; `normalized_phase`
selects AddedToken flag bit 4. It returns held `out_valid/ready`,
`out_value[31:0]`, `out_special`, `out_boundary`, `out_last`.
An ordinary value is a scalar; a special value is a token ID.
`out_boundary` closes an ordinary run before a special or span end;
`out_last` closes the entire splitter result. The splitter retains the whole
span, classifies every scalar from Unicode tables, encodes its bytes and
walks the admitted special trie from each scalar boundary. Terminal matches
must end at a scalar boundary. Eligible terminals use longest byte match,
then lower special-record index. Stripping removes only adjacent whitespace
classified by the committed Unicode tables, never another special.
All table operations are serialized registered record reads, held request,
response wait and registered consume; no fixed DDR latency is assumed.

The public tokenizer validates the full raw UTF-8 prompt before processing
before-normalization specials. Each remaining ordinary run is normalized,
split for after-normalization specials, then sent through the ordinary span
engine with identity normalization. BOS is inserted once. All resulting
tokens are buffered before any public token becomes valid. Capacity counts
include BOS and specials. A single scalar/byte/token may simultaneously
be first and last; no separate trailing beat is required.

## Configuration, transaction admission and recovery

`anvil_edge_config` is an internal single-outstanding register endpoint.
Its public-side ports match the top `cfg_*` channel. Additional inputs are
`status[3:0]`, `transaction_error_code[7:0]`, `write_allowed`,
`reload_allowed`, `publish`, and `committed_config_words[223:0]`.
Outputs are `reload_request`, `publish_error`, and active
`uart_divisor/eos_token_id/max_new_tokens/transport/profile_id/vocab_size/
uart_frame_bytes[31:0]`. Profile and vocabulary writes modify only staged
values; their reads return those staged values. `publish` accepts a completely
validated bundle, requiring any explicitly staged profile/vocabulary to match
the new image. A mismatch reports code 06 through `publish_error`; admission
remains withdrawn. A failed reload never reinstates the old bundle.
Other legal writes update the idle active register, not the flash image.
Reload rereads the flash image's complete configuration and replaces such
overrides; boot never requires a configuration write. Command reads return zero.
Illegal accesses produce held `cfg_rsp_error` without mutating any register.
The helper pulse `serial_update` accompanies a successful divisor, transport
or framing write. It withdraws reception while the UART latches its new idle
configuration; a held bypass valid cannot force reception in the old mode.

UART's additional parameter `FRAME_LOCK` defaults to zero for the standalone
transceiver and is one in the top. Additional helper inputs are
`receive_enable` (ignored when `FRAME_LOCK=0`) and `response_complete` (default
pulled low). A locked transceiver closes input immediately after accepting a frame's
last byte, reopening only on response completion. UART bytes arriving while
closed/disabled report overflow; bypass instead deasserts ready. Existing
`rx_idle/tx_idle` outputs include FIFO drain; `rx_line_idle` reports only
synchronized pin/framer quiescence, so explicit error recovery may discard a
failed buffered frame without pretending that it completed.

Memory subsystem helper `abort_inference` defaults low. On a transaction
failure, it rejects new inference requests, finishes an already captured typed
mapping/DDR operation, and retires its response without requiring a failed
client to remain alive. A captured table transaction is likewise drained to
its recorded owner. Boot responses are never discarded. Clients enter reset
only after abort is registered; memory itself remains live until `idle`.
An idle recovery requires physical RX idle, complete TX drain and memory idle,
then resets the UART/client epoch and starts a fresh external-image reload.
DDR requests accepted before failure are not annulled or rerouted.

The top serializes boot, publication, transport settling, idle, engine start,
prompt input, autonomous execution and physical-output drain. It prevents a
configuration write from racing prompt admission. Full prompt tokenization
precedes controller prefill. Successful `done` is a one-cycle pulse only after
controller finish, detokenizer completion and `tx_idle`; empty output follows
the same completion path without a fabricated byte. Simultaneous error
selection ranks DDR/boot, malformed input/table, core, capacity/sequence, UART,
and retains the first selected code until reset or accepted recovery.

## Standalone controller interface

`anvil_edge_autoregressive_fsm` implements the admitted public interface.
`MAX_PROMPT_TOKENS` defaults to 4096 and must be positive. At `start`, capture
`eos_token_id`, `max_new_tokens`, `vocab_size`, and `seq_limit`.
Standalone `vocab_size` is 1..262144, EOS is below that size, sequence limit is
1..16777215, and maximum selections cannot exceed that limit. The integrated
controller must receive only a fully committed byte-BPE image configuration.
Such an image requires 256..min(262144, physical core capacity) entries; sizes
1 and 255 cannot commit and are not valid tokenizer-image tests.

Capture and validate the entire prompt before the first core request. Prefill
positions start at zero. Intermediate prefill frames are validated but never
emitted. The final prefill winner is used directly; the last prompt token is
not replayed. Signed argmax starts with an invalid winner and uses the lowest
index on ties. All indices must arrive in ascending order. Completion before
the complete frame is an error; completion coincident with its final transfer
is permitted. Feedback occurs only after generated-token acceptance.

`max_new_tokens=0` still completes all prompt prefill. EOS counts as a selection
but is not emitted. A last allowed non-EOS selection is emitted without another
core operation. Finish is a separate held handshake, including empty output.
Controller done is not top-level done: detokenizer and physical TX drain must
also complete.

## FIFO interface

`anvil_edge_fifo` has parameters `WIDTH` and `DEPTH`, each positive. Input ports
are `in_valid`, `in_data[WIDTH-1:0]`; output admission is `in_ready`.
Output ports are `out_valid`, `out_data[WIDTH-1:0]`; consumption is `out_ready`.
`empty` and `full` expose occupancy, gated low during reset. No empty
combinational forwarding is permitted. These are internal implementation ports,
not changes to any public shell interface.

## UART interface and finite capacity

`anvil_edge_uart_io` uses the admitted public interface. `RX_FIFO_DEPTH` and
`TX_FIFO_DEPTH` default to 16 and must be positive. FIFO entries contain a byte
and its final marker. `divisor` is whole clock periods per bit and must be at
least 4; reset divisor is 868. The selected transport is captured only while
both serial engines and both FIFOs are idle. Configuration ownership must
prevent transport/divisor/frame-length changes during a transaction.

UART is idle-high, 8N1, LSB first. A two-register synchronizer precedes falling
edge detection. Validate the start after floor(divisor/2), sample each data bit
at one-divisor intervals, and validate a high stop bit. Transmit start, eight
data bits, and stop for exactly one divisor each.

The serial receive frame buffer holds one byte in addition to RX FIFO entries.
LF mode removes only terminating LF. Fixed-count mode preserves every byte,
including LF, and marks the specified final byte. LF with no preceding byte
is an explicit framing error. An LF-mode byte is held until its successor
establishes whether it is final. AXI bypass preserves raw bytes and input
`tlast`. Only the selected input accepts bytes.

There is no physical UART flow-control pin. In the absence of consumer progress,
the finite capacity is the RX FIFO depth plus the one pending frame byte.
Overflow is a sticky error; software must not interpret a subsequently drained
prefix as a successful transaction.

TX FIFO acceptance is not serial completion. The internal additional output
`tx_idle` is true only when its FIFO and serializer are empty; the top
waits for it, including the final stop bit. Additional `rx_idle` indicates
no serial frame, pending byte, or RX FIFO content. Both are zero in reset.
They are integration/quiescence signals, not debug ports.

## Detokenizer internal configuration

`anvil_edge_detokenizer` retains the admitted token, byte, table and status
ports. Its additional internal configuration inputs are `config_valid`,
`cfg_vocab_size[31:0]`, `cfg_token_records_base[63:0]`,
`cfg_token_bytes_base[63:0]`, `cfg_token_bytes_count[63:0]`, and
`cfg_max_token_byte_length[31:0]`. The two bases identify segment headers, not
data areas. `config_valid` means the entire boot bundle has committed; it is
not a software bypass for structural boot validation. The engine captures
these values at `start`. Additional `finish_valid/finish_ready` inputs/outputs
close a response even when it contains no tokens. They are connected to the
controller finish handshake in the top.

Token admission is serialized. Capture ID/last, compute the record address
with extended precision, issue held aligned reads for its four words, consume
each response in a registered state, validate flags/length/extents, then read
aligned words from the byte segment. Every read has separate request-held,
response-wait, and registered-consume states. No fixed response latency is
assumed. No next token is accepted while its predecessor is being read.

The UTF-8 decoder buffers up to four bytes until an entire valid scalar is
known. It preserves an incomplete scalar between nonfinal tokens. It rejects
invalid leading/continuation bytes, overlong forms, surrogates, out-of-range
scalars and an incomplete final scalar. Output retains a one-byte tail until
a subsequent complete scalar or finish establishes finality. `out_last` is
asserted only with that final retained byte. Empty output completes without
a byte. A token with `in_last` also closes output; a later controller finish
can be acknowledged in the closed state without emitting a second done.

The first error is sticky until reset; `start` does not clear an error. A
nonfailed closed engine accepts a new `start` for a new response.

## Storage and remaining integration

### Typed-memory mapper and DDR arbiter internal ports

`anvil_edge_tensor_mapper` preserves the supplied typed `mem_req_*` and
`mem_rsp_*` field widths and directions at its upstream boundary. Its parameters
are the supplied core geometry, plus `DDR_BASE[63:0]` and `DDR_BYTES[63:0]`.
Its downstream byte-address channel is `ddr_req_*` / `ddr_rsp_*`, with the same
widths and response-for-every-write rule as the top DDR channel. Additional
inputs are `config_valid`, `cfg_directory_base[63:0]`,
`cfg_directory_count[31:0]`, `cfg_immutable_base[63:0]`,
`cfg_immutable_bytes[63:0]`, `cfg_writable_base[63:0]`, and
`cfg_writable_bytes[63:0]`. All bases identify segment headers except the two
opaque tensor-storage bases, which identify their data directly.

The mapper snapshots the committed bundle at typed-request capture. It searches
the sorted DDR directory one record at a time; it does not keep a model-sized
associative on-chip directory. It reads three key words first and only reads the
remaining nine words on a match. The boot validator remains responsible for
whole-directory validation before commit. Runtime mapping additionally checks
the matched shape, format, permissions, segment, row/column and region extent.
Activation slot 13 and row-specific padding are inaccessible. Bad requests
produce a held error response and no tensor-data transaction; malformed
directory records can have only bounded directory-validation reads.

Registered states separate request capture, configuration/window checks,
directory address calculation, held request, response capture, record consume,
key comparison, shape checks, index multiply, offset addition, segment/DDR
checks, data request and held typed response. Multiplication uses
`anvil_edge_signed_multiplier` with 64-bit operands padded from unsigned32
values. No runtime division or remainder computes an address.

`anvil_edge_memory_subsystem` instantiates this mapper. It has the same geometry
and DDR-window parameters and the same configuration ports. Its typed upstream
ports use the prefix `core_mem_` instead of `mem_`. Its two read-only table
channels use prefixes `tokenizer_tbl_` and `detokenizer_tbl_` with
`req_valid/ready/addr` and `rsp_valid/ready/data/error`. Its boot channel uses
`boot_req_*` and `boot_rsp_*` with the top DDR widths; `boot_enable` is required
for boot admission while `config_valid` is low. It forwards accepted boot
reads/writes without interpreting addresses; the boot validator owns their
validation. It exposes `idle`, which is low while either an arbiter transaction
or typed mapping operation is in progress, including a held response.

`cfg_table_bases[1023:0]` and `cfg_table_bytes[1023:0]` pack sixteen unsigned64
segment bases and lengths, entry `i` at `[64*i +: 64]`, corresponding exactly
to kinds `0x200+i`. These are atomically committed with the other configuration.
Runtime table requests must be aligned reads within one admitted segment;
only `0x202` permits its last aligned word to include up to three bytes past
its byte extent. All such words must still be wholly inside the DDR window.
The arbiter checks one range per clock rather than building an unbounded
combinational search. It never permits clients to write immutable tables.

Arbitration is rotating-priority among mapper, tokenizer and detokenizer, one
captured request at a time. Ownership survives all request/response stalls and
configuration withdrawal. A response is captured before it is exposed to the
recorded owner. No response can be accepted at its request-capture edge.
Boot is exclusive before commit; it cannot steal an outstanding runtime
transaction. Reload must wait for `idle` before withdrawing the bundle.
Invalid table addresses return held error responses without issuing DDR.
Transport errors propagate as explicit response errors; top-level first-error
capture remains responsible for sticky appliance status.

### Internal flash-reader interface

`anvil_edge_spi_reader` is a mode-0 NOR read transport, not a boot validator.
Parameters are `FLASH_ADDRESS_BYTES` (3 or 4), `FLASH_CAPACITY_BYTES` (positive,
at most 2^24 or 2^32 respectively), and `CLOCK_HALF_PERIOD` (positive integer
clock cycles, default 2). The standard read opcodes are 0x03 and 0x13,
respectively. No dummy byte is sent. Request ports are `req_valid/req_ready`,
`req_address[63:0]`, and `req_bytes[63:0]`. Response byte ports are
`data_valid/data_ready`, `data[7:0]`, and `data_last`. Status outputs are
`busy/done/error/error_code[7:0]`. Physical ports are
`spi_miso/spi_mosi/spi_sck/spi_cs_n`.

Capture and validate request range at E0. Reject zero length, overflow,
capacity violation and unsupported address width without asserting chip
select. Shift command/address MSB first, sampling NOR data on rising SCK.
Pause only with SCK low while a response byte is stalled. Completion occurs
after final-byte acceptance and chip-select release. Request errors are sticky
with code 02 until reset. The transport cannot detect absent/corrupted flash
content by itself; the boot loader must validate exact bytes and CRCs.

### Image-transfer staging engine

`anvil_edge_image_loader` is an internal SPI-to-DDR staging engine, not the
public boot loader and not a semantic-validation bypass. Parameters are
`VOCAB_SIZE` (default 151936, positive unsigned32 capacity), `MAX_SEQ_LEN`
(default 32768, 1..16777215), `MAX_SEGMENTS` (at least 32, default 32),
`FLASH_ADDRESS_BYTES`, `FLASH_CAPACITY_BYTES`, `SPI_CLOCK_HALF_PERIOD`,
`IMAGE_BASE[63:0]`, `DDR_BASE[63:0]`, and `DDR_BYTES[63:0]`. Image and DDR bases
are four-byte aligned. SPI defaults match
the flash reader; the default DDR window is [0,2**32). Its ports are `start`,
the admitted physical SPI and DDR channels, `busy/done/error/error_code[7:0]`,
`image_loaded`, `staged_config_words[223:0]`,
`staged_segment_bases[1279:0]`, and `staged_segment_bytes[1279:0]`.
It has `clk/rst_n` and accepts start only idle or after a successful load.
The enclosing loader must wait for synchronized calibration before starting.

Config words are packed at 32*i for offsets 04,08,0c,10,14,18,24 in that order.
The twenty base/length entries are packed at 64*i, with indices 0..3 for
kinds 100..103 and 4..19 for 200..20f. Staged outputs are zero until
`image_loaded`; this signal only means byte transfer and CRC checks succeeded.
It **does not** authorize inference. The public boot loader must independently
read/validate all loaded semantics and only then publish its atomic bundle.

The engine reads/checks the 32-byte header, parses the exact seven config
records and all twenty mandatory descriptors, checks every flash/DDR interval
and all pairwise overlaps before any write, then transfers payloads in flash
descriptor order. Each byte performs eight registered reflected-CRC steps.
Each full or partial word issues a held write and waits for its acknowledgment
before advancing. Raw 202 tails use exact lane strobes; other segment lengths
must be multiples of four. Bad write acknowledgment is code 04, CRC mismatch
03, header/config error 01 and descriptor/range/SPI request error 02.
Error is sticky. Reload withdraws `image_loaded` immediately when start is
accepted, and cannot reuse a failed/partially overwritten image. `done` is
one staging-completion pulse, not the appliance completion or boot_done.

### Internal arithmetic interfaces

`anvil_edge_unsigned_divider` has positive integer parameter `WIDTH`, default
128. Its request is `in_valid/in_ready`, `numerator[WIDTH-1:0]` and
`denominator[WIDTH-1:0]`; its response is `out_valid/out_ready`,
`quotient[WIDTH-1:0]`, `remainder[WIDTH-1:0]` and `divide_by_zero`.
Capture at E0, iterate E1..EW, publish E(W+1), then hold every response field.
Zero denominator follows the same latency with an asserted diagnostic; its
numeric fields are zero and must not be used as a valid division.

`anvil_edge_isqrt128` has request `in_valid/in_ready`, `radicand[127:0]`;
response `out_valid/out_ready`, `root[63:0]`. It captures E0, performs 64
digit-pair iterations and publishes E65. The response is floor(sqrt(radicand)).

`anvil_edge_signed_multiplier` has positive parameter `WIDTH`, default 128.
Request operands `operand_a` and `operand_b` are signed WIDTH-bit values.
`product` is a signed 2*WIDTH-bit response. Request and response handshakes are
`in_valid/in_ready` and `out_valid/out_ready`. Latency from capture to registered
result is 2+ceil(log2(ceil(WIDTH/16)^2)) clocks. Magnitudes are captured first,
16-bit unsigned partial products are registered, each binary-adder-tree level
is registered, and sign restoration is separately registered. These scalar
engines accept no second operation until the older response retires.

These helper ports are internal production arithmetic interfaces, not
alterations to the supplied core interface. The derived core below connects
them through variable-latency control states. Independent numerical and timing
acceptance of that retiming remains required.

`anvil_edge_exp_q24` has signed input `x[63:0]` and unsigned output
`value[31:0]`, with `in_valid/in_ready` and `out_valid/out_ready` handshakes.
Its `arithmetic_error` accompanies and is held with the output response.
It implements the source's negative-domain exponential approximation, including
the -1048576 cutoff, 11629080 quotient/remainder reduction and six signed,
toward-zero Taylor divisions. The loop counter is 1..6 and each multiplication
uses the 64-bit registered multiplier. The low signed64 product is captured
before magnitude division to preserve the original declared-width expression.
All division uses the unsigned64 iterative unit plus explicit sign restoration.

`anvil_edge_silu_q16` has signed input `x[31:0]` and signed output `value[31:0]`
with the same handshakes and response-associated `arithmetic_error`. It sequences
the exponential unit, unsigned64 sigmoid division, registered multiply and
separate registered rounding/saturation. It explicitly takes the low signed65
product before rounding, matching the reference assignment.

`anvil_edge_numeric_pkg` supplies only finite FP16 conversion,
round-shift and saturation helpers; it contains no division, root, exponential
or multiplication datapath. Every use of a round/saturate expression occurs
after the associated arithmetic result is registered.

The derived `rtl/anvil_q1_mem_port.sv` keeps the supplied public typed-memory
interface and transaction timing, with asynchronous reset assertion.
The derived `rtl/anvil_q1_rmsnorm.sv` keeps its supplied command/typed-memory
ports and parameter defaults. It makes separate passes over source activation
elements: first squared reduction, then normalization and gamma multiplication.
One unsigned128 divider computes the scaled mean and reciprocal, one digit-pair
root unit computes the denominator, and one signed128 multiplier is reused
for square, x*gamma and that signed64 product times the unsigned64 reciprocal.
The epsilon remains 18446744073710, inserted after unsigned mean division.
Intermediate low64/low128 captures preserve declared reference truncation.
The final round-by-48/saturation is registered before the write request.
Layer, mode, sequence position and dimensions retain explicit rejection.
This implementation is not evidence that the complete core meets timing
or preserves numerics; those remain independent acceptance obligations.

Derived `anvil_q1_elementwise` preserves the supplied command/memory ports and
uses separate registered residual-add or SiLU/multiply/round states. Derived
`anvil_q1_rope` preserves its supplied command/memory ports and rotates pair
`(j,j+D/2)` using cosine/sine columns `(2*j,2*j+1)`. Its four signed32
products, signed65 add/subtract and rounding occupy distinct stages.
Registered head-base and pair-coordinate counters replace runtime head
multiplication. These leaves use the same source slots, destination slots,
finite FP16 conventions and explicit command rejection as the reference.

Derived `anvil_q1_w4a16_gemv` retains all supplied ports/parameters and eight
signed128 per-tile accumulators. A shared signed64 multiplier serializes
lane dequantization and activation products without changing each lane's
reduction order. Lane shifts remain `[0,16,4,20,8,24,12,28]`; dequantization
captures signed37 and activation multiplication captures signed69 before
sign-extension into the accumulator. Scale conversion and delta subtraction
are registered before multiplication. Packed output columns use `c>>3`.
Input-group index/offset counters replace `k/GROUP_SIZE` and its boundary test,
including non-power-of-two group sizes. Bias addition, magnitude rounding and
saturation are separate registered states before typed writes.

`anvil_edge_round_div` has signed128 `numerator`, unsigned64 `divisor`,
signed128 `value`, `divide_by_zero`, and request/response ready-valid pairs.
It captures signed magnitude in 129 bits, adds half the divisor in a registered
state, and uses the unsigned129 iterative divider. Sign restoration and low128
capture match the supplied magnitude-rounded division function, including
intermediate widths. Zero divisors produce an explicit held diagnostic.

Derived `anvil_q1_gqa_attention` keeps the supplied public ports/parameters and
the same two score passes, per-component weighted reduction and cache layout.
Digit-pair root computes `floor(sqrt(D<<32))`; sequential rounded division
scales signed96 dot products and normalizes signed96 weighted sums.
Dot and weighted products explicitly capture low64 and low65, respectively.
Score differences are signed97 before clamping the exponential argument.
Query-head base, KV-head base and head-within-group counters replace the
original `head/RATIO` and `head*D` expressions. Products, reductions,
division/root, exponential, saturation and DDR writes have distinct states.

The derived core keeps the supplied `anvil_q1_top`, `anvil_q1_decoder_layer`
and `anvil_q1_swiglu_mlp` interfaces and production defaults. The decoder
retains the original eleven-step norm/Q/K/V/RoPE/attention/O/residual/norm/
MLP/residual schedule. `anvil_q1_bus_mux` is an internal selected-client route;
each parent holds selection from command issue through child completion.
`N` is positive; invalid counts use diagnostic-only safe port widths.
The production top retains shared embedding/output kind 0, full physical
vocabulary logits and sequence validation. Embedding FP16 conversion, output
FP16 conversion, signed32 product, signed96 accumulation and logit rounding
are separate registered states.

`anvil_edge_core_adapter` preserves every supplied `anvil_q1_top` parameter
and public token/logit/done/error/typed-memory port. Additional inputs
`config_valid` and `cfg_active_vocab_size[31:0]` authorize a committed image;
additional `error_code[7:0]` reports 06 for invalid committed configuration,
20 for actual core failure or 21 for a physical logit-frame violation.
The adapter captures the request before issuing it to its literal
`anvil_q1_top` instance. It validates all V physical indices in order and
uses a one-entry elastic registered logit buffer for indices below the captured
active vocabulary. Inactive tail indices are drained, not forwarded or selected.
Successful completion waits for actual core done, the entire physical frame
and acceptance of every buffered active logit. Active sizes below 256,
above 262144 or above physical capacity cannot initiate core work.
No Q2/Q3/Q4 arithmetic implementation is supplied by this adapter.

ANVLEDG3 uses little-endian checked byte addresses, 32-byte table headers, and
the exact mandatory segment set `100..103,200..20f` in the admitted work order.
`STORAGE.md` records the complete external layout and worked synthetic binary/
address fragments; those fragments are not bootable images or official assets.
The published configuration/base bundle must commit atomically only after
CRC, semantic validation, directory checks, and DDR acknowledgements. No
partial-table inference is permitted. The 256 byte-map entries must reference
256 different ordinary tokens with their exact single-byte strings.

The SPI boot/validator, special-token-aware tokenizer, configuration registers
and top-level integration are saved RTL, without functional acceptance.
Real board integration remains a prerequisite; the portable bridge is not
an installed controller/PHY or pin map.
The saved memory mapper/arbiter, ranked-merge component and derived core are
not yet connected into an autonomous boot-to-text appliance.
Complete official tokenizer assets, quantized
weights, physical DDR controller/PHY and board constraints remain prerequisites,
not substitutes for those implementations. No behavioral core, canned text,
greedy-longest-match ordinary tokenizer, or host address oracle is authorized.

### Ranked-merge pretoken engine

`anvil_edge_ranked_bpe` is an internal tokenizer component, not a replacement
for the required UTF-8/normalization/special/tagged-DFA front end.
`MAX_PRETOKEN_BYTES` is positive, default 4096. `start` captures
`config_valid`, `cfg_vocab_size[31:0]`, `cfg_merge_base[63:0]` (segment header),
and `cfg_merge_count[31:0]`. Its token input is
`in_valid/in_ready/in_token_id[31:0]/in_last`; its token output is
`out_valid/out_ready/out_token_id[31:0]/out_last`. Each input frame contains the
already validated base-byte IDs for exactly one pretoken, not the full prompt.
The caller owns byte-map lookup, boundary formation, BOS and special insertion,
and collection/validation of the entire prompt before controller admission.
Table ports are the admitted read-only `tbl_req_*`/`tbl_rsp_*` interface.
Status ports are `busy/done/error/error_code[7:0]`.

Capture the complete pretoken, scan adjacent pairs left to right, binary-search
the sorted merge table for each pair, and retain the legal smallest unsigned
rank with an explicit validity bit. Equal ranks retain the leftmost pair;
`0xffffffff` is an ordinary legal rank. Apply one selected merge, shift the
remaining token vector one location per clock, then rescan from the beginning.
Every application decreases token count, so no wall-clock heuristic chooses
termination. With no matching pair, emit the complete resulting vector under
backpressure. No search crosses the caller's pretoken boundary. Table
request/response/consume states are separate and addresses use checked
extended arithmetic. Structural/result-byte validation remains part of boot;
this component additionally rejects out-of-vocabulary IDs and propagates
table-response errors. A nonmatching pair key advances the binary search.

### Unicode/tokenizer front-end internal contracts

The following production helpers do not change the public tokenizer interface.
They operate on nonempty spans; the special-token dispatcher skips
empty spans rather than manufacturing a scalar. No helper's partial output
authorizes prompt prefill. The tokenizer must collect and validate the complete
prompt token vector before exposing it to the controller.

`anvil_edge_table_record_reader` has parameter `LOG2_RECORD_BYTES` in 2..6.
One record has `2**LOG2_RECORD_BYTES` bytes, serialized little-endian. Its request
is `in_valid/in_ready`, `segment_base[63:0]` (the table-header address),
`record_count[31:0]`, and `record_index[31:0]`. Its held response is
`out_valid/out_ready`, `record_data[8*2**LOG2_RECORD_BYTES-1:0]`,
`response_error`, and `response_error_code[7:0]`. Word zero occupies the low
32 bits. The read-only table channel uses the admitted `tbl_req_*` and
`tbl_rsp_*` fields. The helper checks alignment, the entire declared table
extent, and index bounds, then reads one aligned word at a time. It does not
replace boot validation of the table header. Address offset, header addition,
record addition, request hold, response wait, word consumption and result hold
are distinct registered stages. Diagnostic responses use code 11 for bounds
and code 04 for a failed DDR response; numeric result fields are zero on error.
An error accompanies one response; the transaction-owning engine makes it
sticky.

`anvil_edge_unicode_lookup` accepts `in_valid/in_ready/in_scalar[31:0]`.
Additional configuration inputs are `config_valid`, `cfg_ranges_base[63:0]`,
`cfg_range_count[31:0]`, and `cfg_class_count[31:0]`, captured with each query.
Its held `out_valid/out_ready` response contains `out_class_id[31:0]`,
`out_properties[31:0]`, `response_error`, and `response_error_code[7:0]`.
It binary-searches the normative 0x207 ranges using the record reader. It
rejects invalid scalars, missing coverage, illegal properties and class IDs.
The table port is the admitted read-only channel. A failed query returns an
explicit diagnostic, never an ASCII class or zero-class fallback.

`anvil_edge_utf8_decoder` has positive `MAX_BYTES`, default 4096. Ports are
`start`, `in_valid/in_ready/in_data[7:0]/in_last`, and
`out_valid/out_ready/out_scalar[31:0]/out_start[31:0]/out_end[31:0]/out_last`,
plus `busy/done/error/error_code[7:0]`. Byte offsets are half-open offsets
within the span. Each scalar is emitted only after all its bytes validate.
The decoder rejects overlong encodings, surrogates, values above U+10FFFF,
bad continuations and incomplete final scalars. It consumes no subsequent byte
while a scalar output is stalled. `MAX_BYTES=1` permits one final ASCII byte;
a nonfinal byte at capacity is a capacity error, not a truncated success.

`anvil_edge_utf8_encoder` has `start`,
`in_valid/in_ready/in_scalar[31:0]/in_last`,
`out_valid/out_ready/out_data[7:0]/out_last`, and
`busy/done/error/error_code[7:0]`. It validates each scalar and emits its exact
canonical UTF-8 bytes. Last accompanies only the last byte of the last scalar.
Both codec engines hold all output fields under stall, complete after the
final output transfer, accept a new start only when idle/closed, and retain
errors until reset. Offset/count arithmetic does not wrap.

`anvil_edge_normalizer` buffers one span as Unicode scalars. Positive parameter
`MAX_SCALARS` (default 4096) bounds the fully decomposed scalar vector, not only
the input size. It uses `start`, scalar input/output ready-valid channels with
`in_last/out_last`, and the standard busy/done/error/error_code and table
channels. Configuration is `config_valid`, `cfg_normalization[31:0]` (0..4),
`cfg_ranges_base/cfg_decomposition_base/cfg_scalar_pool_base/
cfg_composition_base[63:0]`, and
`cfg_range_count/cfg_class_count/cfg_decomposition_count/
cfg_scalar_pool_count/cfg_composition_count[31:0]`. It snapshots configuration
at start. Identity preserves scalars without reading normalization tables.
Other modes perform fully expanded canonical/compatibility decomposition,
algorithmic Hangul decomposition, stable CCC insertion, and, for NFC/NFKC,
blocked canonical composition and algorithmic Hangul composition. Decomposition
records/pool entries and composition pairs use the exact frozen layouts.
There is no output until the entire span is captured and normalized.
Reordering and compaction move at most one scalar per clock. The unsigned32
iterative divider implements Hangul quotient/remainder; there is no
combinational division or remainder.

`anvil_edge_tagged_dfa` has positive `MAX_SPAN_BYTES` (default 4096) and
`MAX_TAG_REGISTERS>=32` (default 32). It accepts one normalized scalar span on
`in_valid/in_ready/in_scalar[31:0]/in_last`, and emits pretoken intervals on
`out_valid/out_ready/out_start[31:0]/out_end[31:0]/out_last`. Intervals index the
normalized span's UTF-8 bytes, not its original pre-normalization byte offsets.
It has `start`, standard status/table channels, and configuration inputs
`config_valid`, `cfg_ranges_base/cfg_states_base/cfg_transitions_base/
cfg_tag_ops_base/cfg_accepts_base[63:0]` and
`cfg_range_count/cfg_class_count/cfg_state_count/cfg_transition_count/
cfg_tag_op_count/cfg_accept_count/cfg_start_state/cfg_dead_state/
cfg_tag_register_count[31:0]`. Configuration is snapshotted at start.
Capture/classification precedes all DFA scans. The engine buffers class IDs
and scalar-end byte offsets, clears one tag per cycle at each anchor, executes
transition tag operations in listed order, then evaluates the destination
state's accepting records. Tags retain byte and scalar indices so rewinding
cannot split a scalar. Only one synthetic end symbol is consumed per anchor.
The lowest unsigned rule priority wins, then its declared longest/shortest
policy. A selected interval must make progress. Last marks the interval ending
at the complete span end. Missing candidates, bad indices, inconsistent
equal-priority policies and malformed records report code 12; failed table
reads report 04. Finite span length and table interval counts bound every scan;
no timeout substitutes for candidate selection.

| Front-end boundary | Registered behavior |
| --- | --- |
| Final input scalar plus `in_last` | Finish its decomposition/classification before scanning or publishing output. |
| Invalid final UTF-8 byte | Report error, never emit that scalar or successful done. |
| Tag copy to itself | Preserve pre-edge validity/value, including invalidity. |
| Several operations targeting one tag | Later listed operations observe earlier completed operations. |
| Synthetic end symbol | Before/after byte and scalar positions both equal span end. |
| Zero decomposition/composition records | No match; no out-of-range table request is issued. |
| Leading combining marks | Preserve stable CCC order; do not invent a starter. |
| Successful composition | Replace the retained starter without adding a blocking mark. |
| Equal CCC | Preserve input order; a retained equal-class mark blocks composition. |
| Rewound trailing lookahead | Reset tags, restart at selected tagged end, reprocess the lookahead. |
| Boundary output stall | Hold interval and last; do not advance the next anchor. |

`anvil_edge_text_bpe_span` connects the normalizer, UTF-8 encoder, tagged DFA,
byte-map record reader and ranked BPE for one nonempty ordinary-text span.
This is an internal component of the special-token-aware tokenizer,
not an alternative public tokenizer. Its scalar input/output token channels
are `in_valid/in_ready/in_scalar[31:0]/in_last` and
`out_valid/out_ready/out_token_id[31:0]/out_last`; it has `start`, standard
status/table channels and positive parameters `MAX_SPAN_BYTES`,
`MAX_SPAN_TOKENS`, `MAX_PRETOKEN_BYTES` (each default 4096) and
`MAX_TAG_REGISTERS>=32` (default 32). Configuration includes the combined
normalizer/DFA fields above plus `cfg_vocab_size[31:0]`,
`cfg_byte_map_base/cfg_merge_base[63:0]`, `cfg_merge_count[31:0]`, and
`cfg_max_pretoken_bytes[31:0]`. Its caller holds the committed configuration
bundle stable from start through completion; this is an internal ownership
requirement, not a runtime host action. The child engines snapshot their
respective fields at their starts.

The span engine collects normalized scalars, encodes their exact bytes,
obtains complete DFA intervals, maps each interval's bytes through 0x203 and
performs ranked merges. It buffers the entire resulting token vector before
exposing any token. Normalized bytes, decomposed scalars, each pretoken and
output tokens have explicit finite capacities; overflow reports 30.
A DFA boundary is held unaccepted while its BPE runs. Only after all tokens
for that interval are captured is the boundary acknowledged, so the DFA cannot
issue a next-anchor table request concurrently with the BPE client. Table
ownership therefore follows registered phases and does not depend on an
assumed DDR latency. Byte-map indices use unsigned raw bytes, with no extra
vocabulary byte remapping. BOS insertion, before/after-normalization
AddedToken matching, metadata/boot admission and whole-prompt collection
remain the enclosing tokenizer's responsibilities.

### Boot validation readers and staged manifest

`anvil_edge_boot_segment_reader` is an internal single-outstanding, read-only
DDR client. Its input transaction contains `segment_base[63:0]`,
`segment_bytes[63:0]`, aligned `byte_offset[63:0]`, and `word_count[5:0]`
(1..32). Capture, extent calculation, bounds check, held request, response
wait, registered consume and held return are separate states. The response
contains `data[1023:0]`, with the first word in bits 31:0, and associated
`response_error/error_code`. It never reads a word outside the declared
segment, never forwards a response on the capture edge, and never issues
writes. A memory error is code 04; invalid read bounds are code 06.

`anvil_edge_manifest_validator` consumes the loader's stable staged config and
twenty canonical segment base/length pairs. `start` begins validation, and
`valid_manifest` is only an intermediate structural result, not boot commit.
It checks the exact geometry, legal configuration, metadata capacities and all
table headers. Its staged outputs are the 32 metadata words and sixteen
table counts, indexed by kind minus 0x200 (count zero for metadata itself).
The staged bundle must remain unchanged throughout validation. It uses the
same held DDR read channel as the segment reader. Errors are sticky until
reset; successful validation can be started again. Neither a header pass nor
a staged manifest authorizes any tokenizer/core request. Cross-record,
tensor-region and complete table semantic validation remain additional
prerequisites of the public boot commit.

`anvil_edge_directory_validator` consumes the same frozen staging bundle.
It independently checks the directory header, exact legal sorted key set,
geometry-specific shapes/formats/permissions, extended extents and pairwise
region disjointness. It serially checks every FP16 tensor word, rejects
nonfinite encodings, nonzero high lanes and negative nonzero scales, checks
inactive physical embedding/output rows are zero, and checks every immutable
storage hole and every writable initialization word is zero. It performs no
writes. Region sizes and the active embedding boundary use the registered
multiplier; directory addressing uses registered shifts/additions. Only one
directory record or data word is read at a time. Directory failures use code
05, transport failures code 04. `valid_directory` remains an intermediate
result, never inference admission.

`anvil_edge_token_table_validator` starts only with `manifest_valid` and a
stable manifest/staging bundle. It checks every token record, all 256 byte-map
records and every sorted merge record. Merges fetch three ordinary token
records and compare every result byte with the exact left/right concatenation;
rank 0xffffffff and rank ties are not rejected. Byte-map validation compares
the referenced one-byte string with its unsigned map index. This also proves
the 256 IDs are distinct: one immutable token record cannot contain two
different one-byte strings. Raw-string reads are word aligned with an explicitly
bounded final partial word; they do not treat alignment padding as token data.
`valid_tokens` is another intermediate result. Special trie, Unicode,
tagged-DFA and normalization semantic validation are still separate commit
prerequisites. Malformed token/merge/map semantics use code 06; DDR errors use
04.

`anvil_edge_profile_table_validator` scans the committed-image candidate's
Unicode ranges, all DFA states/transitions/tag operations/accepts and all
normalization records/scalars. It verifies full scalar-range coverage excluding
surrogates, class/property bounds, every table reference and reserved field,
the dead state's transition semantics, consistent accept policy for each
unsigned priority, unique sorted decomposition/composition keys and valid
scalar-pool extents. It assumes the structurally checked manifest remains
stable, uses only serialized bounded DDR reads and returns
`valid_profile_tables` as an intermediate result. It does not replace official
asset provenance or independent Unicode/tokenizer comparisons.

`anvil_edge_special_trie_validator` checks every special record, unique token
IDs and special-token flags, then traverses the entire trie with a bounded
depth-first stack. It clears a visited-node bitmap serially, rejects revisits
(including cycles, multiple parents and edges back to the root), checks each
node's edge interval and strict byte ordering, and compares each terminal's
complete path against its referenced token bytes. Requiring node and edge
visit totals to match their headers excludes disconnected data and unused or
multiply referenced edges. Its explicit capacities default to 1,048,576 nodes,
262,144 special records and 4096 path bytes; larger images fail code 06 before
traversal. These are hardware storage capacities, not a change to official
profile coverage. This stage requires both manifest and token validation and
returns `valid_special_trie`, not `boot_done`.

### Public boot-loader commit and recovery

`anvil_edge_ddr4_boot_loader` has the admitted SPI and single-outstanding DDR
channels, `start`, `ddr_cal_done`, `boot_done/busy/error/error_code`, and these
additional internal committed outputs: `committed_config_words[223:0]`,
`committed_segment_bases[1279:0]`, `committed_segment_bytes[1279:0]`,
`committed_metadata[1023:0]`, `committed_table_counts[511:0]`. Config words are
ordered by offsets 04,08,0c,10,14,18,24; canonical segment slots are
100,101,102,103,200..20f; metadata/count packing is described above. All outputs
are gated to zero until atomic commit. The wrapper forwards no inferred model
or table state from an initial block.

After reset the loader automatically waits for two-register-synchronized
calibration, transfers the SPI image, and runs manifest, directory, token,
profile and trie validators in that order. The final commit edge publishes all
five packed fields and `boot_done` together. The selected stage owns the held
DDR transaction and response; no stage switch occurs with an outstanding
request. A validator error leaves admission withdrawn and preserves its code.

While ready or failed, `start` requests an idle recovery/reload. Its caller must
first establish quiescent I/O, no active inference, and memory-subsystem idle;
this is an internal ownership precondition, not a new external register.
Reload withdraws `boot_done`, clears committed outputs and resets the subordinate
boot epoch before rereading the parameterized flash base. It cannot keep a
partially overwritten old image admitted. Active boot ignores `start`; the
top/configuration controller rejects illegal active reload writes
instead of presenting them to this internal control.

| Boot-validation boundary | Behavior |
| --- | --- |
| Segment-reader request E0 | Capture all fields; no DDR response or result may retire at E0. |
| Reader word count 1 | Read exactly one aligned word and return it in the low 32 bits. |
| Reader word count 32 | Explicit terminal count; no six-bit counter wrap. |
| Held DDR request/return | Valid, address, packed data and diagnostic remain stable until acceptance. |
| Reset during a scan | Withdraw valid/status; discard the incomplete staged result. |
| Empty table | Validate its nonempty 32-byte header and exact zero data length. |
| Vocabularies 1/255 | Reject before admitting any byte-map/table configuration. |
| Manifest success | Structural intermediate only; no inference or `boot_done` side effect. |

## Independent acceptance

The mandatory commands remain:

```
python3 tests/verify.py --check l1
python3 tests/verify.py --check clean-reproduction
vulcan hardware fpga rtl-timing-lint
vulcan hardware fpga quartus-sta
vulcan hardware fpga board-hil
```

Their verification sources and execution belong to the independent Verifier
and shared runtime. The current increment does not supply those sources or
claim those commands have run. Product PDF authoring follows independent
engineering acceptance; no design check depends on the final report.
