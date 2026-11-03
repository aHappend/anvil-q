# ANVLEDG3 version-1 external storage contract

This is the independently admitted byte-level image ABI, not an image builder
or evidence that a loader has been implemented. The current implementation
status is in `SPEC.md`. Table conversion and verification assets belong to the
independent Verifier. Runtime inference must not use a software converter,
host-computed tensor addresses, or host-selected logits.

## Common encoding and bounds

All integers are little-endian and unsigned unless stated otherwise. Offsets
and lengths are bytes, except explicitly named record indices/counts. There
is no implicit C/ABI padding. Reserved fields are zero. All structures except
raw strings are four-byte aligned. Regions are half-open intervals. Evaluate
products, sums, end addresses and overlap tests at extended precision before
truncation; reject overflow. A reference fits only if its complete interval
is inside its declared extent. References may not enter table headers or
region padding.

Committed byte-BPE images have
`256 <= active_vocab_size <= min(262144, physical VOCAB_SIZE)`.
This is distinct from the standalone controller's legal logit-domain sizes
1..262144. Images declaring 1 or 255 entries are invalid. A physical core
capacity below 256 cannot admit an image.

DDR uses aligned byte addresses, four-byte words, and a response for every
accepted read or write. Full writes have strobe `1111`. For a raw-byte segment
tail, little-endian byte lanes use only the exact final strobes. Flash image
addresses are relative to the parameterized image base. The NOR mode is SPI
mode 0, command/address/data MSB first: opcode 03 with three address bytes or
explicitly parameterized opcode 13 with four address bytes. Bounds include
both the declared flash capacity and command address width; no wraparound.

## Flash header and configuration

| Byte offset | Type | Value |
| --- | --- | --- |
| 0 | 8 raw bytes | ASCII `ANVLEDG3` |
| 8 | u32 | Format version 1 |
| 12 | u32 | `header_bytes` |
| 16 | u32 | Accelerator contract profile ID |
| 20 | u32 | Segment count |
| 24 | u32 | Configuration record count, exactly 7 |
| 28 | u32 | Reserved zero |
| 32 | 7 records, 8 bytes each | Register offset u32, value u32 |
| 88 | `segment_count` records, 40 bytes each | Segment descriptors |

`header_bytes = 32 + 8*7 + 40*segment_count` exactly. Configuration has exactly
one record for each offset 04,08,0c,10,14,18,24 (hex), in any order. Duplicates,
missing/other offsets and illegal values are errors. Header profile equals
configuration 14. The profile is 1..4 for Q1..Q4 shell contracts, independently
of tokenizer family. Divisor is at least 4; EOS is below active vocabulary;
maximum selections are at most instantiated MAX_SEQ_LEN. Transport has only
bit 0 (AXI bypass); other bits are zero. Framing zero means LF termination;
nonzero is the exact UART raw-byte frame count. Vocabulary obeys the image
range above and cannot exceed physical capacity.

Each 40-byte descriptor is:

| Byte offset | Type | Meaning |
| --- | --- | --- |
| 0 | u32 | Segment kind |
| 4 | u32 | Flags zero |
| 8 | u64 | DDR destination byte address |
| 16 | u64 | Payload byte count, nonzero |
| 24 | u64 | Flash payload offset from image base |
| 32 | u32 | Payload CRC32 |
| 36 | u32 | Reserved zero |

All descriptors/flash and DDR intervals are checked before payload writes.
Flash intervals may not overlap the header or each other. DDR intervals may
not overlap each other and must fit the board DDR window. Segment count has
an explicit supported parameter limit of at least 32; excess is an error.
Version 1 has exactly the following twenty unique mandatory kinds; unknown,
duplicate and missing kinds are errors.

| Kind | Payload |
| --- | --- |
| 100 | Fixed geometry |
| 101 | Tensor directory |
| 102 | Immutable core tensor data, opaque |
| 103 | Writable activation/cache initialization, opaque |
| 200 | Fixed tokenizer metadata |
| 201 | Token offset/length/flags |
| 202 | Decoded token byte strings |
| 203 | Raw-byte to ordinary-token map |
| 204 | Ranked merges |
| 205 | Special trie nodes |
| 206 | Special trie edges |
| 207 | Unicode classification ranges |
| 208 | Pretokenization DFA states |
| 209 | DFA transitions |
| 20a | Special token policies |
| 20b | DFA tag operations |
| 20c | DFA accepting records |
| 20d | Normalization decomposition records |
| 20e | Normalization scalar pool |
| 20f | Normalization composition records |

Kinds in this document are hexadecimal. Tables with no records still contain
their nonempty headers. CRC is reflected IEEE CRC32, polynomial edb88320,
initial/final XOR ffffffff. It covers every stored payload byte including a
table header, not word padding beyond a raw-byte tail. CRC detects corruption,
not authenticity. All segment lengths are multiples of four except 202.

## Geometry, tensors and typed addressing

Geometry 100 is exactly 64 bytes: sixteen u32 words in order:

```
1, L, H, I, Q, K, D, G, 4, V, S, max(H,I), accelerator_profile_id, 0, 0, 0
```

Every geometry field matches the instantiated core. Production defaults are
L=24,H=896,I=4864,Q=14,K=2,D=64,G=128,V=151936,S=32768. Shapes must satisfy
the core parameter constraints in `SPEC.md` and the admitted work order.
The active vocabulary may be smaller than V, but inactive embedding/output
rows in the immutable payload are zero. The adapter still drains and validates
all V physical logits, forwarding only active IDs.

Except geometry, metadata and opaque 102/103, every segment begins with this
exact 32-byte header:

| Byte offset | Type | Meaning |
| --- | --- | --- |
| 0 | u32 | Magic 334c4254 |
| 4 | u32 | Version 1 |
| 8 | u32 | Record byte size |
| 12 | u32 | Record count |
| 16 | u64 | `record_bytes * record_count` |
| 24 | u64 | Reserved zero |

Segment length is exactly `32 + data_bytes`. Record i begins at
`segment_base + 32 + i*record_bytes`. Segment 202 uses record size 1 and its
byte count as record count. All token offsets refer to the 202 **data area**.

Directory 101 uses 48-byte records:

| Offset | Type | Field |
| --- | --- | --- |
| 0 | u32 | Kind |
| 4 | u32 | Layer |
| 8 | u32 | Projection |
| 12 | u32 | Storage segment kind |
| 16 | u64 | Offset into that opaque storage segment |
| 24 | u32 | Rows |
| 28 | u32 | Columns |
| 32 | u32 | Format |
| 36 | u32 | Permissions |
| 40 | u64 | Extent bytes, exactly rows*columns*4 |

Keys (kind,layer,projection) are unique and lexicographically sorted. Permission
1 means read-only in 102; 3 means read/write in 103; no other values are legal.
Formats are 1=FP16 in low16 with high16 zero, 2=packed AWQ4 word,
3=signed Q16.16 int32, 4=signed Q2.30 int32. All elements occupy four bytes.
Regions are aligned, nonoverlapping and wholly inside their named storage
segment. Unused holes are zero and grant no access. All bytes of 103,
including padding, are zero at initialization.

Let T=K*D and A=max(H,I). Projection p uses (inputs,outputs):

| p | Projection | Inputs | Outputs |
| --- | --- | --- | --- |
| 0 | Q | H | H |
| 1 | K | H | T |
| 2 | V | H | T |
| 3 | O | H | H |
| 4 | Gate | H | I |
| 5 | Up | H | I |
| 6 | Down | I | H |

Every mandatory region occurs once, with no additional key:

| Kind | Keys | Rows | Columns | Format/permission |
| --- | --- | --- | --- | --- |
| 0 | (0,0,0) | V | H | 1/1, shared embedding/output |
| 1 | Every layer,p=0..6 | inputs | outputs/8 | 2/1 qweights |
| 2 | Every layer,p=0..6 | inputs/G | outputs/8 | 2/1 qzeros |
| 3 | Every layer,p=0..6 | inputs/G | outputs | 1/1 scales |
| 4 | Every layer,p=0..2 only | 1 | outputs | 1/1 biases |
| 5,6 | Every layer,p=0 | 1 | H | 1/1 norm gamma |
| 7 | (7,0,0) | 1 | H | 1/1 final gamma |
| 8 | (8,0,0) | 15 | A | 3/3 activation slots |
| 9,10 | Every layer,p=0 | S | T | 3/3 K/V caches |
| 11 | (11,0,0) | S | D | 4/1 RoPE |

There are exactly `28*L + 4` records. Slot rows 0,1,2,5,6,7,8,12,14 permit
H columns; rows 3,4 permit T; rows 9,10,11 permit I; row 13 is inaccessible.
The physical activation stride is A even for shorter rows. Slot names are
current hidden, input norm, Q,K,V,attention context,O projection,first
residual,post-attention norm,gate,up,SiLU(gate)*up,down,reserved,final norm.
For caches, row is sequence position and column is kv_head*D+component.
Query head q selects kv_head=floor(q/(Q/K)), implemented by bounded sequential
logic rather than a combinational divider. RoPE columns 2*j and 2*j+1 are
cosine/sine for rotating components (j,j+D/2).

Logical AWQ output lanes 0..7 occupy nibble shifts
`[0,16,4,20,8,24,12,28]` in weights and zero points. Packed column is c>>3;
scale column is c. Dequantization is `(unsigned_w - unsigned_z)*scale`,
without implicit zero-point +1.

A typed request validates the exact key, row, column, permissions, format and
all region/DDR bounds, then computes
`storage_base + data_offset + 4*(row*columns + col)`.
Layer is not collapsed into row; kind 8 is not an embedding request. Invalid
requests produce held error responses without a tensor-data DDR request.
Directory-validation reads, if needed, remain bounded to the directory.

## Tokenizer metadata

Metadata 200 is exactly 128 bytes, thirty-two u32 words:
Its metadata version is independent of the flash format and table-header
versions, which remain 1.

| Word | Field |
| --- | --- |
| 0 | Metadata version 1 or 2; reject all other values |
| 1 | Family 1=Qwen2.5 text BPE,2=DeepSeek-V3 text BPE,3=Llama-3.2 text BPE |
| 2 | Active vocabulary, equal to config 18 |
| 3 | Normalization 0=identity,1=NFC,2=NFKC,3=NFD,4=NFKD |
| 4 | Raw special policy 0=ordinary text,1=recognize enabled,2=reject enabled |
| 5 | Add BOS, 0 or 1 |
| 6 | BOS ID, in range when enabled, zero when disabled |
| 7 | EOS ID, equal to config 08 and in range |
| 8 | Unicode version for classification and special-token properties; version 1 also uses this version for normalization and regex case folding |
| 9 | Unicode class count C |
| 10,11 | DFA start/dead state |
| 12 | Tag register count R |
| 13 | Special trie root |
| 14 | Maximum token byte length |
| 15 | Maximum pretoken byte length |
| 16..23 | 32 SHA-256 bytes in digest byte order |
| 24 | Version 1: reserved zero. Version 2: Unicode version for normalization and canonical combining classes |
| 25 | Version 1: reserved zero. Version 2: Unicode version for regex case-folding semantics |
| 26..31 | Reserved zeros in both versions |

The digest pins the official asset bundle in manifest file order. It is not
an authenticated-boot claim. All profile counts/limits must fit declared
hardware capacities, never be clamped. R capacity is at least 32. Accelerator
profile ID is independent of tokenizer family.

Every Unicode version field uses `major<<16 | minor<<8 | patch`. Version 1
retains its single-version semantics and requires all words 24..31 to be
zero. Version 2 assigns words 24 and 25 explicitly; they do not inherit word 8.
Words 1..23, metadata size, table record layouts and flash format are unchanged.
The version labels describe the loaded tables, not a selection of hardwired
Unicode implementations; RTL executes the same table-driven operations for
both versions. Structural boot validation does not establish that a declared
version matches its table contents.

The asset provenance manifest must pin exact implementation/dependency
identities, revisions and cryptographic hashes for classification, special
properties, normalization and regex case folding, including the converter
and compiled tables. Version numbers alone do not prove official equivalence.
Different v2 versions may represent independently established profile semantics,
but candidate dependency behavior alone cannot select an official profile:
comparison against an executed pinned official implementation remains required.

## Token strings, byte map and ranked merges

201 records are 16 bytes: u64 byte_offset, u32 byte_length, u32 flags. Exactly
active-vocabulary records exist and token ID directly indexes them. Flags
bit0 ordinary, bit1 special, other bits zero; at least one bit is set.
Ordinary lengths are nonzero. Every offset/length is in the 202 data area
and length is at most metadata maximum. Overlapping string substrings are
allowed. Zero-length specials cannot match raw text.

The 202 bytes are already inverse-byte-map-decoded official token bytes, not
the printed byte-map glyph spellings. Detokenization performs no extra byte
mapping. Ordinary pieces may split code points; the output UTF-8 validator
retains incomplete scalars across tokens and rejects an incomplete finish.

203 has exactly 256 four-byte records. Record b is the ordinary token ID whose
string is exactly the single byte b. All 256 IDs are necessarily distinct;
aliases, substitute tokens, incorrect strings and missing bytes are errors.

204 records are sixteen bytes: left_id,right_id,result_id,rank (all u32).
Pairs are unique and sorted by unsigned (left,right). All IDs designate
ordinary tokens. Result bytes are exactly the concatenation of left/right
and fit the maximum length. Unsigned rank ffffffff is legal, not a missing
sentinel. For every pretoken, repeatedly merge the legal adjacent pair with
the smallest rank, breaking ties leftmost. Never merge across pretoken or
special boundaries. Ordinary longest-string matching is not BPE.

## Specials and Unicode

205 nodes are sixteen bytes: first_edge,edge_count,terminal_special_index,
reserved zero (all u32). Terminal ffffffff means nonterminal.
206 edges are eight bytes: byte_value,next_node (u32). Values are 0..255;
each node's edge interval is sorted by unique byte value and index-valid.
The rooted trie is acyclic, every reachable nonroot node has one parent,
and all nodes/edges are reachable. A terminal's path bytes equal its referenced
special's string. Trie walking chooses the longest eligible match, ties by
lower special record index.

20a special records are sixteen bytes: token_id,flags,reserved0,reserved1.
IDs are unique and point to special-flagged tokens. Flag bits are enabled=0,
lstrip=1,rstrip=2,single_word=3,match-after-normalization=4; higher bits are zero.
Strip only adjacent Unicode White_Space; single_word requires neighboring
scalars outside Letter/Mark/Number/Connector_Punctuation. Find and protect
before-normalization matches first, then find normalized matches within the
remaining normalized spans. Policy 0 ignores raw matching; policy 1 emits
IDs; policy 2 rejects matches. Preserve official AddedToken behavior, with
no global whitespace stripping. BOS, when enabled, occurs exactly once
before content and counts toward prompt-token capacity.

207 ranges are sixteen bytes: first_scalar,last_scalar,class_id,properties.
Ranges are sorted/disjoint and cover all Unicode scalars except surrogates.
class_id<C. Properties bits 0..7 are canonical combining class, bit8 is
White_Space and bit9 is the single_word class; higher bits are zero. Every
classification comes from these pinned tables, not an ASCII heuristic.

In version 1 all these fields use metadata word 8. In version 2, `class_id`
is derived from word 8's classification semantics and word 25's regex
case-folding semantics when compiling case-insensitive regex predicates.
Properties bits 8 and 9 use word 8's special-token property semantics;
bits 0..7 use word 24's normalization/combining-class semantics. Range
boundaries partition the combined fields, so no field is implicitly assigned
another field's Unicode release.

## Tagged DFA

208 states are sixteen bytes: first_transition,first_accept,accept_count,
reserved zero. Each state has exactly C+1 transitions in 209; class C is
synthetic end-of-span. Metadata start/dead states are valid; dead has no
accepts and self-transitions without actions.

209 transitions are sixteen bytes: next_state,first_tag_op,tag_op_count,
reserved zero. Their intervals address 20b. A 20b operation is sixteen bytes:
opcode,destination_register,source_register,reserved zero. Opcodes are
0=clear invalid,1=set before current scalar,2=set after current scalar,
3=copy source. Registers are <R; unused sources are zero. Execute operations
in listed order. Before/after are normalized UTF-8 byte offsets; at synthetic
end both equal span end. Invalid copied tags remain invalid.

20c accepts are sixteen bytes: rule_priority,end_register,extent_policy,
reserved zero. Register<R; extent 0=longest,1=shortest. All records of one
priority have the same policy. At each new anchor clear all tags, start from
the start state, consume transitions/actions and evaluate destination accepts.
A candidate requires a valid tagged end greater than anchor and no greater
than consumed cursor. Scan until dead or one consumed synthetic end. Choose
lowest unsigned priority, then the declared end policy. Rewind trailing
lookahead to that end, emit the interval, reset and repeat. No candidate is
a malformed-profile error. Every interval must progress.

An official-asset converter must compile ordered regex alternatives,
lookahead and quantifier policies into this language. A synthetic simple
DFA, including the example below, is not an official-profile substitute.
Case-insensitive predicates use metadata word 8 for version 1, or word 25
for version 2. Folding is compiled into the 207 classes and DFA transitions;
it does not rewrite prompt bytes or perform additional runtime normalization.

## Normalization

20d decomposition records are sixteen bytes: scalar,scalar_pool_index,
scalar_count,flags. They are sorted by unique scalar; flag bit0 marks
compatibility, higher bits zero. Sequences are nonempty, fully recursively
expanded, scalar-valid and wholly inside 20e. Pool 20e uses four-byte scalars.
20f compositions are sixteen bytes: starter,combining_scalar,composite,
reserved zero, sorted by unique pair, with valid scalars and the normalization
Unicode version's composition exclusions applied. That version is metadata
word 8 in version 1 and word 24 in version 2; it governs decomposition,
composition, scalar-pool contents and the 207 canonical combining classes.

NFC/NFD ignore compatibility-only decompositions; NFKC/NFKD include them.
Implement UAX #15 stable CCC ordering, composition blocking and algorithmic
Hangul. Identity preserves bytes. All three normalization tables still have
headers when their record counts are zero. Official nonidentity behavior
must not be replaced with identity.

## Atomic boot and reload

The loader automatically starts after reset and synchronized DDR calibration.
It exclusively owns memory until every CRC, DDR write acknowledgment,
geometry/directory key/shape/permission, table header, record/reference bound,
byte-map distinctness/string, merge concatenation, special trie and Unicode/
DFA/normalization relationship is validated. Only one event publishes the
entire register/geometry/base/count bundle and boot_done. No inference client
can observe partial state. Error leaves boot_done low and inference stopped.

Immutable tables/tensors are read-only after commit; only 103 is core-writable.
Reload requires idle/quiescent clients, withdraws admission and rereads flash
at the configured image base. Failed reload cannot expose overwritten tables
as a valid previous image. Staged profile/vocabulary writes cannot reinterpret
old tables. All memory responses remain with the owner of the accepted
request through response acceptance, regardless of stalls or reload intent.

## Worked binary fragments and address calculations

These are independent ABI illustrations, **not complete bootable images or
official assets**. A full image additionally needs all twenty segments, valid
tensor contents, semantic validation and actual payload CRCs.

For twenty segments and seven config records, header length is
32+56+800=888=378 hex. A synthetic size-256 header prefix with profile 1,
divisor 868, EOS 255, maximum 8, bypass 1 and LF framing is:

```
0000: 41 4e 56 4c 45 44 47 33 01 00 00 00 78 03 00 00
0010: 01 00 00 00 14 00 00 00 07 00 00 00 00 00 00 00
0020: 04 00 00 00 64 03 00 00 08 00 00 00 ff 00 00 00
0030: 0c 00 00 00 08 00 00 00 10 00 00 00 01 00 00 00
0040: 14 00 00 00 01 00 00 00 18 00 00 00 00 01 00 00
0050: 24 00 00 00 00 00 00 00
```

Descriptors begin at 58 hex; no payload can begin below 378. The value
config18=256 is a representation boundary, not a size claim for any official
tokenizer.

For a synthetic 256-byte string pool, the 202 header is:

```
54 42 4c 33 01 00 00 00 01 00 00 00 00 01 00 00
00 01 00 00 00 00 00 00 00 00 00 00 00 00 00 00
```

Its segment length is 32+256=288. Suppose token records base=0x10000,
byte pool base=0x20000 and byte-map base=0x30000, with token b representing
raw byte b. Token 97 (`a`) has this 16-byte record at
`0x10000+0x20+97*16=0x10630`:

```
61 00 00 00 00 00 00 00 01 00 00 00 01 00 00 00
```

Its raw byte is at `0x20000+0x20+0x61=0x20081`. The aligned DDR read is
0x20080, lane 1. The byte-map entry is at
`0x30000+0x20+0x61*4=0x301a4` and contains
`61 00 00 00`. No host resolves these addresses during inference.

For a separate size-257 illustration, token 256 can contain bytes `61 62`.
A legal merge fragment (97,98,256,rank ffffffff) is:

```
61 00 00 00 62 00 00 00 00 01 00 00 ff ff ff ff
```

This fragment requires the corresponding token record and an adequately sized
byte pool; it is not part of the preceding size-256 example.

For a synthetic C=1 whole-span DFA, states (first_transition,first_accept,
accept_count,reserved) are `(0,0,0,0)`, `(2,0,1,0)`, `(4,1,0,0)`.
Start=0,dead=2,R=1. The six transitions are `(1,0,1,0)`, `(2,0,0,0)`,
`(1,0,1,0)`, `(2,0,0,0)`, `(2,0,0,0)`, `(2,0,0,0)`.
Tag operation 0 is `(2,0,0,0)` and accept 0 is `(0,0,0,0)`.
Each real scalar updates tag0 to its end; longest policy chooses the complete
span. All state transitions include synthetic class 1. This only illustrates
serialization/execution; official profiles require their exact compiled rules.

For an H=8,I=8,D=8,G=8 projection, qweight rows=8,columns=1. With immutable
base=0x400000 and region offset=0x2000, row7,col0 maps to
`0x400000+0x2000+4*(7*1)=0x40201c`. For a layer-1 cache with S=4,T=8,
writable base=0x800000 and its own region offset=0x1000, row3,col7 maps to
`0x800000+0x1000+4*(3*8+7)=0x80107c`. The directory key includes layer 1;
row remains 3. For a separate H=8,I=16 activation example, A=16. At
offset0x400, slot11,col15 maps to
`0x800000+0x400+4*(11*16+15)=0x8006fc`. Slot3,col8 is
illegal even though physical stride 16 would contain it: K/V slots permit
only T=8 columns. RoPE pair j=2 reads columns4,5 and rotates components2,6
when D=8.
