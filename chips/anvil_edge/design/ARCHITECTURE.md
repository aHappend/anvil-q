# Anvil-Edge implementation architecture

## Current increment

The design includes a non-fall-through elastic FIFO, a clock-enable UART
with streaming bypass, prompt-buffered autonomous controller, UTF-8 detokenizer,
ranked-merge pretoken engine, Unicode normalization and tagged-DFA ordinary-text
span engine, typed DDR mapper/arbiter and a derived sequential Q1 core with an
active-vocabulary adapter. These are saved production-source components, not
an integrated or verified SoC. The image staging engine now covers header/
descriptor validation and CRC-checked SPI-to-DDR transfer. Semantic boot
validation/commit, special-token-aware tokenizer
integration, configuration/top-level control and physical board integration
are still missing.

The intended production hierarchy remains:

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

The mapper scans sorted directory keys in DDR. Matching records are checked
against the requested core geometry, permissions, format, storage segment and
row-specific activation bounds. A registered multiplier computes the physical
row stride; later states add the column, region offset and segment base and
check the DDR window. Invalid tuples cannot reach tensor-data issue.

Table clients are read-only. The arbiter scans the sixteen committed table
ranges one per stage, permits exact raw-byte tail-word access only for kind
0x202, and returns held explicit errors for invalid addresses. Boot still must
validate all segment relationships and the complete directory before commit;
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

This does not complete the public tokenizer. Its enclosing engine still must
capture/validate the complete UTF-8 prompt, protect before-normalization
specials, apply normalized special matching and AddedToken stripping/word
policies, add BOS, collect all span/special tokens and only then admit prefill.
An ordinary-text span result is not evidence of those missing policies.

## Image staging and storage work still required

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

The public boot loader still must wait for synchronized calibration, invoke
this transfer engine, read and validate every geometry/directory/table semantic
relationship from DDR, and only then publish the atomic committed bundle.
The runtime mapper and arbiter rely on that missing semantic commit. Tables
and immutable tensors are read-only after commit; only activation/cache
storage is writable. No incomplete image is authorized to enter these clients.
`design/STORAGE.md` ships the exact storage ABI and worked byte/address
fragments without claiming that those fragments form complete boot images.

The default geometry requires external storage, not inferred on-chip model RAM.
Capacity, address-window, flash command width and real board pin/PHY choices
remain explicit integration prerequisites. Q2/Q3/Q4 compatibility denotes
the frozen shell contract, not unsupplied arithmetic implementations.
