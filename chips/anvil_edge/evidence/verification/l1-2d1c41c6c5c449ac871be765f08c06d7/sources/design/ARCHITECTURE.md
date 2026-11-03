# Anvil-Edge implementation architecture

## Current increment

The design includes a non-fall-through elastic FIFO, a clock-enable UART
with streaming bypass, prompt-buffered autonomous controller, UTF-8 detokenizer,
ranked-merge pretoken engine, Unicode normalization and tagged-DFA ordinary-text
span engine, typed DDR mapper/arbiter and a derived sequential Q1 core with an
active-vocabulary adapter. These are connected production-source components,
not a verified SoC. The public boot loader connects CRC-checked
SPI-to-DDR staging, semantic validation and atomic configuration commit.
The public tokenizer adds two-phase special matching and BOS; configuration
and top-level control connect the full autonomous transaction. The actual
board-specific wrapper, installed DDR4 IP and pin/clock constraints remain
unavailable and must not be replaced by a behavioral RAM or guessed pins.

The literal production hierarchy is:

```
anvil_edge_top
  anvil_edge_uart_io
  anvil_edge_bpe_tokenizer
  anvil_edge_detokenizer
  anvil_edge_autoregressive_fsm
  anvil_edge_ddr4_boot_loader
  anvil_edge_core_adapter
    anvil_q1_top
  anvil_edge_memory_subsystem
```

No reference source is modified. Derived production core modules must be
compiled separately from the reference hierarchy to avoid duplicate names.

## Ownership and dependencies

| Producer | Consumer | Required guarantee |
| --- | --- | --- |
| UART/AXI receive | Tokenizer | Ordered accepted bytes and exact final marker; no silent overflow. |
| Boot validator | All inference clients | Entire checked bundle is atomically committed before admission. |
| Tokenizer | Controller | Complete prompt validated before any core sequence mutation. |
| Controller | Core adapter | One held request per prompt/feedback token; monotonic position. |
| Core adapter | Controller | Complete active-logit frame plus real physical-core completion. |
| Controller | Detokenizer | Non-EOS IDs only; finish cannot overtake generated IDs. |
| Detokenizer | UART/AXI transmit | Complete valid UTF-8, stable bytes and actual final marker. |
| Memory arbiter | DDR | One outstanding transaction with held owner through response acceptance. |
| Physical TX drain | Top completion | Final stop bit has finished before successful done. |

## Controller states

`IDLE -> CAPTURE -> ISSUE -> LOGITS -> DECIDE` is the prefill spine.
`DECIDE` either advances to the next buffered prompt token, initiates finish,
or presents a generated token. `GENERATED` holds the selected ID under stalls.
After acceptance it either finishes or issues precisely that ID at the next
position. `FINISH` waits for finish acceptance and pulses done only on success.
Any active error enters `FAILED`, preserving the first code until reset.

The winner is registered on every better accepted logit. Strict `>` retains
the earlier index on ties. DECIDE is a distinct state so same-edge final-logit
and done cannot use a stale winner. No combinational path searches a prompt or
vocabulary. Prompt memory has one write or one indexed read per controller
state. Buffer contents need not be reset; counters define validity.

## Serial buffering

RX uses a two-flop pin synchronizer, start/data/stop sampling FSM, one pending
framing byte, and the shared FIFO. Delaying LF-framed bytes by one successor
allows correct last-marker assignment without injecting a newline. Fixed-count
framing can release its final byte immediately. UART cannot backpressure the
wire, so a full pending/FIFO condition reports overflow explicitly.

TX captures an old FIFO head into a 10-bit start/data/stop shift frame, then
advances only at divisor terminal counts. The serial line is driven by that
registered frame, never by an AXI combinational path. Bypass exposes only the
selected FIFO output and keeps its byte/final fields stable during stalls.

## Derived arithmetic organization

The read-only reference package has combinational division/remainder, a
64-step root and wide arithmetic chains. Production does not instantiate it.
The derived hierarchy uses registered partial-product trees, unsigned restoring
dividers, a digit-pair root and explicitly sequenced exponential/SiLU units.
The numerical helper package contains only conversion, rounding and saturation.
Every derived leaf keeps the supplied command and typed-memory ports.

GEMV serializes lanes while retaining eight independent signed128 accumulators
and each lane's input order. Registered group-index/offset counters replace
runtime division. RMSNorm uses separate squared-sum and output passes.
Attention retains the reference max-score and weighted-context passes, with
registered query/KV head bases and a head-within-group counter. RoPE shares
one multiplier for its four pair products. Decoder and MLP retain the supplied
operation ordering; the top emits the entire physical vocabulary.

After final normalization, the output head fills a synchronous, non-reset
`HIDDEN_SIZE`-by-32 buffer from the first vocabulary row's successful activation
reads. A resettable validity bit becomes set only after the last component
arrives. Later rows register a buffer read and then capture it in a separate
state before requesting the weight. No arithmetic or reduction ordering
changes. All physical head-weight reads and all physical logits remain;
output-head activation traffic becomes one vector per operation instead of
one vector per vocabulary row. The buffer occupies 28,672 data bits at the
default H=896, independent of vocabulary size. Reset, error, completion and
every new accepted token invalidate it. Thus feedback and prefill operations
cannot inherit earlier activations, and no buffer reset loop is required.

The adapter buffers only active logits but drains and validates every physical
index and waits for real core completion. It cannot certify non-Q1 arithmetic.
Retiming explicitly preserves intermediate low64/65/69/96/128 captures,
magnitude rounding, AWQ lane order and Q16.16 scaling. These are implementation
intent, not verified numerical or timing results. Nothing in this source
increment demonstrates default-core timing or numerics.

## Runtime DDR mapping and ownership

The memory subsystem instantiates the typed mapper and rotates priority among
its byte-address requests and the two table readers. Boot exclusively owns DDR
before commit. A captured request owns its downstream response through the
owner's acceptance; configuration withdrawal never reroutes that response.
Reload must wait for the subsystem's idle indication.

The mapper uses a fixed two-entry validated-descriptor cache, enough to retain
the alternating activation/embedding identities in the Q1 output head. Misses
scan sorted directory keys in DDR. Matching records are checked
against the requested core geometry, permissions, format, storage segment and
row-specific activation bounds. A registered multiplier computes the physical
row stride on a row-base miss; later states add the column, region offset and segment base and
check the DDR window. Invalid tuples cannot reach tensor-data issue.

Entries contain immutable directory metadata (complete kind/layer/projection
key, storage kind, offset, extent, shape, format and permissions), never tensor
values. Each slot also retains one row ID, its registered unsigned64
row-times-columns product and a separate valid bit (194 row-storage bits plus
one captured descriptor-slot bit).
A fill follows successful metadata and registered extent validation;
two alternating victims bound storage independently of vocabulary/model size.
Hits register metadata and retain all per-request legality, permission, index,
offset and DDR checks, skipping directory reads and the already validated
extent product. After those checks, a matching row in the same descriptor slot
can also skip index multiplication; its registered base still passes through
column addition and every offset/segment/physical-window check. A different
row computes and replaces that slot's row product. Every tensor access still
requires a real DDR response.

Reset, configuration withdrawal and directory/storage-bundle changes invalidate
both entries and their row products. Descriptor replacement clears its row-base
validity before a new product can fill. Withdrawal also disqualifies an in-flight
request from refilling either bank, so a same-address reload cannot reuse old
metadata or row products. Invalidation does
not cancel outstanding transactions or alter held responses. `SPEC.md` records
the cycle boundaries and hit/miss state transitions. This is an optimization
hypothesis, not a measured throughput result: independent verification must
compare numerical results, addresses, transaction counts, simulated cycles and
elapsed time against retained before-repair sources, exercise stalls,
errors/reset/eviction/reload (including withdrawal while outstanding), and kill
compiled functional mutations before any independently admitted complete-table
continuation within the unchanged 2700-second budget.

The bounded repair follows the incomplete bypass diagnostic at
`evidence/preparation/official-qwen-shell-general-bypass-712c10b7d55d402ea5765e7ba02b0280/receipt.json`
and the earlier UART/bypass timeout at
`evidence/preparation/official-qwen-shell-general-79870737978648f58850a61e30a567f0/receipt.json`.
Their failed receipts and before-repair source snapshots remain unchanged.
Progressing execution and timeout are not numerical mismatches, and the repair
does not establish that the complete-table case will finish within budget.

Table clients are read-only. The arbiter scans the sixteen committed table
ranges one per stage, permits exact raw-byte tail-word access only for kind
0x202, and returns held explicit errors for invalid addresses. Boot validates all segment relationships and the complete directory before commit;
runtime range checks are not a replacement for boot validation.

## Ranked BPE component

The ranked-merge engine buffers one pretoken's base IDs, looks up every adjacent
pair using a serialized binary search of the sorted merge table, and applies
the globally smallest rank with leftmost ties. An explicit candidate-valid bit
makes rank 0xffffffff usable. One selected pair is replaced and the vector is
compacted one entry per clock before rescanning. This engine does not itself implement UTF-8 prompt validation, Unicode
normalization, AddedToken matching or tagged DFA boundaries.

## Unicode and ordinary-text spans

The UTF-8 decoder validates incoming scalars and retains half-open raw-byte
offsets. A malformed or incomplete scalar is not emitted. The reverse codec
encodes valid scalars without vocabulary-dependent byte remapping.
Both are registered ready/valid transducers. They do not by themselves provide
whole-prompt atomicity.

`anvil_edge_unicode_lookup` obtains all CCC, whitespace and word-boundary
classification from the pinned range table. The shared record-reader component
checks aligned table extents and indexes before serialized reads. Each DDR
word is captured before it updates a record. Read errors return explicit
diagnostics, not substitute classes or bytes.

The normalizer uses one scalar/CCC buffer. Fully expanded decomposition records
and the scalar pool produce candidates for stable insertion; previous entries
are fetched and shifted one per registered step. A CCC-zero scalar stops
reordering across its starter boundary. NFC/NFKC compact the ordered buffer
in place using a retained starter and last uncomposed CCC. Successful
composition changes the starter without changing the blocker. Leading marks
cannot invent a starter. Hangul decomposition uses the unsigned32 sequential
divider; composition uses registered constant shifts/additions and a
sequential remainder check. Identity bypasses normalization-table reads.

The tagged DFA first buffers each scalar's class and encoded byte end.
Every anchored scan clears tags serially, loads its starting state, consumes
one class transition, executes the listed operations serially and evaluates
the destination state's accepts. The best candidate retains unsigned priority,
extent policy and byte/scalar end positions. The synthetic end transition is
consumed at most once. Selected lookahead is rewound by restoring both end
positions; no byte search or scalar splitting is involved. Each real
transition advances a scalar, each tag/accept loop advances an admitted
record interval, and every emitted interval advances the anchor.

`anvil_edge_text_bpe_span` connects these components for nonempty ordinary-text
spans:

```
scalar input -> normalizer -> normalized scalar buffer
                              -> UTF-8 encoder -> normalized byte buffer
                              -> tagged DFA -> pretoken intervals
normalized byte interval -> byte-map reads -> ranked BPE -> token buffer
token buffer -> complete-span token output
```

The normalized byte buffer, not original raw byte offsets, is the source for
base-byte lookup. No token is exposed until the entire span has normalized,
pretokenized and merged successfully. The DFA keeps a boundary valid but
unaccepted throughout processing of that interval's BPE. This deliberately
serial schedule prevents next-anchor table reads from racing byte-map/merge
reads and keeps table-response ownership explicit under arbitrary stalls.

`anvil_edge_bpe_tokenizer` first captures and validates all raw UTF-8. The first
special splitter protects eligible before-normalization specials. Ordinary
runs pass through the normalizer and the second, normalized-phase splitter.
Remaining ordinary runs enter the span engine with identity normalization,
so text is never normalized twice. BOS and both phases' special tokens share
the complete-prompt token buffer. Only its final readout can reach prefill.

Each splitter classifies/scalar-encodes its entire input, retaining byte-to-
scalar end indexes. Trie walking begins only at scalar boundaries; terminals
inside a scalar are ineligible. Eligible longest terminals retain their ID,
record index and AddedToken flags. Left stripping rewinds only trailing
ordinary White_Space entries in the output plan; right stripping advances
the input scalar cursor. Word-boundary checks use pinned Unicode properties.
Plan output and public tokenizer output have registered load/hold stages.
These are design semantics, not demonstrated official-tokenizer equivalence.

## Image staging, semantic validation and commit

`anvil_edge_image_loader` reads the frozen header/configuration and records
each descriptor in a canonical twenty-segment bank. A separate order vector
retains original descriptor order for payload transfer. Extended end-address
calculations and one-prior-region-per-cycle comparisons reject header,
capacity, alignment and overlap violations before any DDR write.

Each payload byte is consumed into a little-endian word and eight registered
reflected-CRC steps. A word flush issues its exact lane strobes and waits for
a real DDR acknowledgment before reading subsequent bytes. All payload CRCs
and write acknowledgments must succeed before the staging `image_loaded`
status and gated staging fields become visible. Staging completion is not
boot_done and never enables a runtime client.

The public `anvil_edge_ddr4_boot_loader` waits for two-register-synchronized
calibration and serializes these stages:

```
reset boot epoch -> calibration -> SPI staging
  -> manifest -> directory/tensor initialization -> tokens/map/merges
  -> Unicode/DFA/normalization records -> special trie -> atomic commit
```

`anvil_edge_boot_segment_reader` captures one bounded aligned read range and
holds each DDR request and response independently of downstream pacing.
Header, metadata and directory-record reads use the same sequencer. Raw token
bytes alone permit a rounded final physical word, with byte indexes checked
against the exact unrounded data count.

The manifest stage checks the exact geometry/configuration, metadata capacities
and every table header/extent. Metadata versions 1 and 2 share the existing
128-byte staged/committed bundle. Version 1 reserves words 24..31 as zero;
version 2 assigns normalization/combining-class provenance to word 24 and
regex case-folding provenance to word 25, retaining reserved-zero words 26..31.
Word 8 identifies classification/special-property provenance. These labels
describe the tables executed by the existing lookup, normalizer and DFA, not
hardwired Unicode behavior. Unsupported metadata versions or nonzero reserved
fields fail before commit; reload admission and atomic publication are unchanged.
The directory stage validates a strictly sorted
legal key set with exactly the mandated cardinality. This establishes key
completeness without a model-sized on-chip directory. It checks each region
against all earlier regions, then validates all FP16 tensor words, inactive
embedding/output rows, all writable initialization and immutable holes.
Finding each next immutable interval uses a serial directory scan rather than
a combinational associative search.

The token stage validates all records, then dereferences each byte-map entry
and compares its actual one-byte string. This proves distinct base IDs without
a second 256-entry membership store. Every merge fetches its three ordinary
tokens and compares the full concatenation byte by byte. Unsigned ranks,
including 0xffffffff and ties, remain legal.

The profile stage checks complete Unicode scalar coverage, state/transition/
tag/accept intervals, dead-state behavior, accept-policy consistency, sorted
normalization keys and scalar-pool validity. Official Unicode semantics and
asset fidelity still require independent pinned-reference comparisons;
structural validation is not an authenticated boot claim.

The special-trie stage checks all special records and unique IDs. It clears
its visited bitmap serially, then uses a bounded depth-first stack to check
edge order, unique parentage, cycles, reachability and terminal byte strings.
Node and edge visit counts must equal the table counts. No data-memory contents
are assumed initialized at power-on; counters and explicit bitmap clearing
establish validity before use.

Only the selected stage can issue or consume a DDR transaction. Stage success
is observed after its final response has retired. Once all stages are valid,
one edge registers the complete bundle and asserts `boot_done`; no individual
base or metadata word becomes independently visible. Idle recovery withdraws
admission and resets a registered subordinate epoch before rereading flash.
The epoch reset is not decoded from a multi-bit FSM state. Failure aborts that
epoch, leaves `boot_done` low and retains the first stage diagnostic.

The runtime mapper and arbiter use this atomic bundle. Tables and immutable
tensors are read-only after commit; only activation/cache storage is writable.
The top connects that ownership boundary and rejects nonquiescent reloads.
The saved boot path has not been functionally or synthesis verified.
`design/STORAGE.md` ships the exact storage ABI and worked byte/address
fragments without claiming that those fragments form complete boot images.

The default geometry requires external storage, not inferred on-chip model RAM.
Capacity, address-window, flash command width and real board pin/PHY choices
remain explicit integration prerequisites. Q2/Q3/Q4 compatibility denotes
the frozen shell contract, not unsupplied arithmetic implementations.

## Transaction control and failure drain

The top publishes boot configuration before opening reception and serializes
engine start, prompt reception, autonomous execution and TX drain. The UART's
integrated frame lock closes reception at the first accepted last marker,
not at a later tokenizer handoff. Its finite wire-input overflow diagnostic
remains active while reception is closed.

Configuration responses are registered and held. Profile/vocabulary changes
are staged until the next completely validated image matches them. Illegal
writes never alter either staged or active values. Serial setting writes
withdraw input for a settling interval rather than racing an incoming bypass
beat against the UART's idle configuration latch.

An observed failure registers the first selected diagnostic and abort request.
Clients reset on the following edge; memory does not reset. Already accepted
mapping/table/DDR transactions finish and are drained to their recorded owner,
including a write acknowledgement. The arbiter can complete a captured typed
request even after its originating core has reset. Explicit recovery is
permitted only after memory and physical serial paths are quiescent, then
withdraws all admission and rereads external flash.
