"""Independent semantic control review of two immutable RTL trees.

This is a compact representation of a manual source audit, not a similarity
classifier or a formal equivalence proof. The complete inventory and both trees
are fingerprinted before any grouped proof is expanded into individual records.
Changing either requires another source review, not automatic reclassification.
R/E claims cover shared command, scheduling and memory semantics in all three
precisions, allowing the specified arithmetic representation changes. The whole
GEMV module is conservatively uncredited because native matrix streaming replaces
its AWQ fetch schedule. Compatibility retention alone is not used to certify that
changed schedule. Added states never increase the original denominator.
"""

import hashlib
import json


TREE_SHA256 = "6e1b887ff0ce53a8d84f319bfb4f4bfc1521fc9a5739eec2791f7aad88b4ec16"
INVENTORY_SHA256 = "b731b0abddda6d6c85ac39035b9b52d0e0cce8695d8537164f94a78107d3dff9"
ORIGINAL_ITEMS = 1385

REVIEWED_RTL_SHA256 = {
    "rtl/anvil_q1_bus_mux.sv": "9b41a1c242c344871258f0ba9d861e669cb1688f4b5fb2a46818b729251c2af7",
    "rtl/anvil_q1_fp_00_pkg.sv": "d508af25e902f842439c5bd7c62dbc29e159de00a2155796ecbf759c40c023b1",
    "rtl/anvil_q1_fp_01_compat_pkg.sv": "316a81331458820566c2beb83fd5ce6d002078fb4cf8cff252eb6f8e8e9500e6",
    "rtl/anvil_q1_fp_awq_dequant.sv": "f714d3aa309c6dd13eadbd8390475c10b467aca3beeee62bf47ba92b32f9f157",
    "rtl/anvil_q1_fp_binary.sv": "b522d105c47c1f1810432d25de2f6d6f216044594e660be56fc95a179827cb7e",
    "rtl/anvil_q1_fp_compat_div.sv": "8343e2e3d22ae19b0a6d15b1782220ba4d3e990d5a1c98f24a71c827a923c8cf",
    "rtl/anvil_q1_fp_compat_exp.sv": "d5f1ff1c09dc76e08926474404d33d01f1858e247423622019c084b997c86ac4",
    "rtl/anvil_q1_fp_compat_round_div.sv": "ad0ddaa524f45e6aaaf70f69bec10bc8ea718141818143c31a0309d33429fd58",
    "rtl/anvil_q1_fp_compat_sqrt.sv": "19c75532bcae2881d880cf67bc1a83c1e494d33f0c8060598412b3400bc75bc4",
    "rtl/anvil_q1_fp_decoder_layer.sv": "4a338f16a4d5a96a348a214d7adb6f6a5f7a396cdd78e08b217c10b14b2667fc",
    "rtl/anvil_q1_fp_dot8.sv": "7bb12d8a0646c2a962d6ec3197f7062b10412bd5c4b5ef86c6102685e2fff25f",
    "rtl/anvil_q1_fp_dot8_mixed.sv": "49634a43f9b8fcbccc595be251f702d481e9f06717512a54a74dc34bafe87901",
    "rtl/anvil_q1_fp_elementwise.sv": "c3e5389120c5b004d84b343de9c1c15b887d9e3ab4d00121e407f03639106701",
    "rtl/anvil_q1_fp_exp.sv": "01d296faff3310a91875a0b2628e3b050e78be56cd19125eb28b4c44f5bc8d15",
    "rtl/anvil_q1_fp_gemv.sv": "51d671ac3d6a54034157124a89f61786d429301c1e5b7b8b4fa73b00cd12255e",
    "rtl/anvil_q1_fp_gqa_attention.sv": "fb7bc337a471c9ee73b1db61421a0d028537a984fbe037b70eb4d37035b4809a",
    "rtl/anvil_q1_fp_reciprocal.sv": "eb2d9fb3fba07cb10ff478106b14bac35ea45b9ec07da07edab1250da2838a3d",
    "rtl/anvil_q1_fp_reduce3.sv": "126eb4683cb774b2808a40f01cba48b9d4e7a665f1a82e30ebe6cc83f9e6cd3c",
    "rtl/anvil_q1_fp_rmsnorm.sv": "6516220e84a8afc64cdd3d9387bdf53b0e6235c97615f4d3349d17423c0545e0",
    "rtl/anvil_q1_fp_rope.sv": "aeacd351b43d4fe8386ae2adc18db163ddd9a2e1d20d3d3af8da6a9076630d5f",
    "rtl/anvil_q1_fp_rsqrt.sv": "f6674723d2c245eaba79128e05254a19243adde4f14ed696878fad6e72ff2170",
    "rtl/anvil_q1_fp_swiglu_mlp.sv": "f40f5879acf8c67f37e8c2bfb41ebf35e8f035c4dfc83c48d246f2d0bd55d948",
    "rtl/anvil_q1_fp_top.sv": "6616305950509eb4cdae94898f3282957bc2a3c12eb78f08e360826d30a35092",
    "rtl/anvil_q1_mem_port.sv": "fc0b18df80b47572561fd8c8018d465856405a224c03640137d791d0c90b4561",
    "rtl/anvil_q1_parameters.sv": "2d0f084668ac9ed561da2978c10eade6adf142c4ba9673f5bfc3d963755968f9",
}

REVIEW_BASIS = {
    "method": "Complete fresh semantic source audit, 2026-10-29; not an incremental equivalence claim.",
    "superseded_tree_sha256": "582fac3b954edb1221175f6e99bcc8a33b7e10f23b942de3779ea93db527d56d",
    "historical_sources": (
        "No matching complete tree or per-file receipt inventory was recovered "
        "from retained project preparation snapshots/receipts. Some older fixture "
        "RTL directories are empty; available complete fixtures match the current "
        "tree or disposable mutations, not the superseded binding. Therefore no "
        "list of changes relative to that binding is asserted. All 25 current RTL "
        "files and all 13 immutable parent files were reviewed afresh."),
    "failure_receipt": "evidence/preparation/verifier-preservation-bcbt1uek/receipt.json",
    "scope": (
        "Manual control preservation, not formal/numerical equivalence or product "
        "acceptance. R retains an original action/event; E maps it through completed "
        "arithmetic and the selected representation. Native nonfinite data and "
        "arithmetic exceptions are newly specified fault events, not claims that "
        "the same raw word is valid fixed-point and floating-point data. New "
        "states/events earn no denominator credit. Entire GEMV remains C."),
    "source_reviews": {
        "top": (
            "Compared all parent states 0..15,30,31/default, reset/fault edges, "
            "request decode and every memory_port/decoder/final_norm/bus connection. "
            "Own requests remain 1/3/9/11, kind0 token/vocabulary rows and scratch "
            "0/14; child selection remains 5/6 and 7/8. Added waits 16..19 issue "
            "no memory requests and change no address/owner counters. State 19 "
            "tests fatal status before result commit. State 15 launches no work, "
            "holds vocabulary/sums until ready and completes only after last logit. "
            "Precision is latched only in idle admission. Original invalid-command "
            "items remain C because sequence invalidation/recovery changed."),
        "decoder_layer": (
            "Compared the whole eleven-step decode and all six bus slices, child "
            "parameters/ports, reset, acceptance, ready/finished/fault branches and "
            "3/4/default exits. Step advances only on selected completion, faults "
            "precede step==10, ownership remains unchanged during child waits. "
            "Precision is captured at command acceptance and forwarded to every child."),
        "swiglu_mlp": (
            "Compared every state and connection: gate4/up5/elementwise2/down6, "
            "bus selection 5/6 versus other states, projection update only after "
            "successful completion, child faults and terminal 14/15. Reset-gated "
            "command pins cannot cause acceptance under synchronous child reset."),
        "gqa_attention": (
            "Compared all original states, cache copy, causal two-pass traversal, "
            "context component/head progression, memory_port connections and added "
            "states 32..65. kv_head and group_offset advance only after final "
            "component write acknowledgement, proving head=kv_head*RATIO+offset. "
            "Maximum/context passes preserve time order; each component rebuilds "
            "denominator and weighted sum, each new head rebuilds maximum. Native "
            "fatal status and nonfinite read guards precede commit; wait-state "
            "decodes issue no memory. Final division now finishes before state16."),
        "rope": (
            "Compared all original states and connections: Q slot2 then K slot3, "
            "head*D+pair and +D/2, kind11 position row and 2*pair+(state==7), "
            "writes9/11 acknowledged10/12. Compatibility16/17 and native18..21 "
            "finish both outputs before first write. Four multiply valids and "
            "both add valids gate commit; fault priority suppresses writes. "
            "Pair/head/key progression remains solely at second acknowledgement."),
        "rmsnorm": (
            "Compared all original states, parameter diagnostics and connections: "
            "src0/7, dst1/8/14, gamma kinds5/6/7 and kind7 layer0. Sum/index "
            "advance only after accepted source arithmetic; reciprocal-H, mean, "
            "epsilon and rsqrt finish before index reset/second pass. Compatibility "
            "divider/sqrt waits40..45 preserve quotient/round/saturate order; "
            "native20..39 gate each dependency on valid. Gamma faults and native "
            "nonfinite reads cannot issue a destination write."),
        "elementwise": (
            "Compared all original states, diagnostics and memory connections: "
            "read pairs(0,6)/(7,12)/(9,10), write7/0/11 and H/I bounds. "
            "Compatibility7..11 and native16..29 complete arithmetic before write5. "
            "Native exp(-abs(a)) uses a negative-only exponential argument; the "
            "negative-a branch additionally multiplies sigmoid by exp before a "
            "and up products. Every dependent scalar waits for valid and checks "
            "fatal status before commit; index advances only on write acknowledgement."),
        "w4a16_gemv": (
            "Compared the entire original/current module, including direct "
            "request/response FSM, all seven dimensions/scratch assignments, AWQ "
            "nibble inputs, group counters and compatibility9->17->18 waits. "
            "Requests remain held until transfer; responses accepted only in "
            "following wait states; counters hold under stalls. Native21/22 "
            "streams eight kind12 weights,23/24 commits only all valid nonfatal "
            "dots,25/26 waits for bias. Native fetch schedule differs; all 194 "
            "original items remain uncredited, even shared/compatibility actions."),
        "shared_and_legality": (
            "mem_port, bus_mux and parameters are byte-identical to their immutable "
            "parents. Reviewed capture/request/outstanding states0/1/2, held "
            "fields, response-qualified fault, synchronous reset, all mux slices "
            "and full legality predicates. No owner changes until completion; "
            "unsolicited responses cannot generate complete."),
        "compatibility_leaves": (
            "Reviewed fp_01_compat_pkg, fp_awq_dequant, compat_div/round_div/sqrt/exp "
            "against parent pkg/dequant. Conversions, saturation, half-away rounding "
            "and lane shifts0,16,4,20,8,24,12,28 retain their expressions. Iterative "
            "division captures only ready launches; signed round_div captures sign "
            "with the same launch. Legal command operands fit its128-bit numerator. "
            "Digit sqrt uses sufficient66-bit trial/remainder. Exp retains six "
            "signed truncating terms and cutoffs; SiLU retains sign-dependent "
            "quotient. Wider intermediate products do not overflow the original "
            "bounded ranges. All busy/valid state clears synchronously."),
        "native_leaves": (
            "Reviewed fp_00_pkg, dot8/dot8_mixed/reduce3/binary and exp/reciprocal/"
            "rsqrt as integration dependencies. Dot/mixed/add/mul use the same "
            "three registered valid stages; masks suppress inactive terms/status. "
            "Scalar valid pipelines are8/16/24 stages and reset clears every valid. "
            "Results/status are masked unless valid. Operator launch states are "
            "single-cycle, wait states cannot relaunch, and each matching result "
            "is consumed only in its designated wait state. Fault exits cannot "
            "consume a later pipeline result. This checks control integration, "
            "not a replacement for numerical, synthesis or STA checks."),
    },
}

# Each scope covers the complete original module, not a selected favorable FSM.
SCOPES = {
    "top": (
        "Embedding kind-0 reads and residual-slot-0 writes retain token/component "
        "ordering. Decoder ownership is selected in states 5/6 and final_norm in "
        "7/8. Layer advancement, final-norm handoff, slot-14 reads, vocabulary "
        "iteration, held state-15 logits, next_position update and states 30/31 "
        "retain their original guards and actions. Reset and memory/child faults "
        "retain synchronous priority and completion routing. Command-rejection "
        "recovery changes are explicitly uncredited below."),
    "decoder_layer": (
        "The step decoder retains all eleven operations: norm0, Q, K, V, RoPE, "
        "attention, O, residual0, norm1, MLP, residual1. Selections, projections, "
        "norm/element modes, six bus slices and child ports retain their original "
        "indices. States 0/1/2/3/4 retain capture, ready wait, finished/fault "
        "priority, step==10 completion, increment, rejection and return-to-idle "
        "actions. Added precision capture/forwarding and precision==3 rejection "
        "do not change any original mode-00 guard."),
    "swiglu_mlp": (
        "The original gate projection 4, up projection 5, mode-2 silu_product "
        "and down projection 6 remain ordered by states 1..8. Ready/finished "
        "waits, fault priority, terminal states 14/15, selected bus ownership "
        "and both port slices are retained. Added rst_n gating on child command "
        "connections is equivalent: reset already masks child ready and takes "
        "priority over command capture; when rst_n=1 the predicates are identical."),
    "w4a16_gemv": (
        "Projection 0..6 retains original input/output dimensions and source/"
        "target scratch slots. Packed weight, zero, scale, activation, bias and "
        "acknowledged output requests keep their state ordering and ownership. "
        "States 1..8, 11..14, 16, 19/20 retain request/response separation, "
        "lane iteration, scale validation, output-tile advancement, clearing "
        "and error completion. Precision zero selects these original paths."),
    "gqa_attention": (
        "Key then value copying retains kinds 9/10, layer/position/index and "
        "acknowledged writes. Query traversal, causal time_index<=position, "
        "dimension traversal, maximum pass then context pass, output component "
        "and head advancement retain their original ordering and guards. "
        "Context slot 5, query slot 2 and cache ownership are retained. Reset, "
        "memory-fault priority, terminal states 30/31 and request/response waits "
        "are retained. Group-counter and arithmetic-wait obligations are separate."),
    "rope": (
        "Q scratch slot 2 then K slot 3, split-half component addresses, "
        "position-indexed kind-11 coefficient reads, two acknowledged writes "
        "per pair, pair/head advancement and Q-to-K handoff are retained. "
        "Command bounds, memory-fault priority, reset and terminal states "
        "14/15 retain original semantics."),
    "rmsnorm": (
        "Modes retain source slots 0/7, target slots 1/8/14 and norm kinds "
        "5/6/7, including final-norm layer zero. The first complete source "
        "reduction precedes the second source/gamma/write pass. Index bounds, "
        "memory request/response waits, invalid-gamma failure, reset, fault "
        "priority and terminal states 14/15 are retained."),
    "elementwise": (
        "Modes retain source pairs (0,6), (7,12), (9,10) and destinations "
        "7,0,11. Two acknowledged reads precede each acknowledged write; "
        "mode 2 uses INTERMEDIATE_SIZE and other modes use HIDDEN_SIZE. "
        "Command validation, index iteration, reset, fault priority and "
        "terminal states 14/15 are retained."),
}

RETIME = {
    "top": {
        "2": "Embedding completion preserves mode-00 invalid-FP16 rejection and "
             "the successful state-3 handoff. Native data is decoded in captured "
             "precision and rejects nonzero upper bits or nonfinite tensors "
             "before scratch issue. No new request precedes validation.",
        "10": "Final-norm scratch completion preserves mode-00 state-11 handoff. "
              "Native FP32 nonfinite data faults before the tied-weight request; "
              "finite data uses the identical component and vocabulary addresses.",
        "12": "A valid weight response traverses 12->16->17->13 in compatibility "
              "mode or 12->18->19->13 in native modes. Product/accumulation "
              "completion precedes the original component decision; invalid "
              "tensors still fail without issuing another request.",
    },
    "gqa_attention": {
        "0": "Legal HEAD_DIM is positive, so floor(sqrt(HEAD_DIM*2^32))>0. "
             "The original sqrt_dim==0 rejection is unreachable for legal "
             "parameters. The valid command now waits 62->63 for that same "
             "constant (native modes wait 64->65 for its reciprocal square "
             "root) before the original first request; invalid commands "
             "still take state 30. No cache transaction precedes initialization.",
        "9": "After the key response, compatibility 9->36->37->39 or native "
             "9->32->33->34->35->39 completes multiply/reduction before the "
             "original dimension increment or score-scaling decision.",
        "10": "10->38 waits for the signed rounded quotient before state 11. "
              "Native 40->41 instead multiplies by the completed reciprocal "
              "square root before state 11. The positive dimension constant "
              "prevents division by zero.",
        "11": "The maximum pass factors its identical dim/dot resets and "
              "state-6 transition outside the time-index branch, preserving "
              "both original branch actions. The context pass uses 11->42->43 "
              "and waits for exp before state 12; native 44->45->46->47 "
              "does the same with registered subtraction/exp. No memory "
              "request occurs while waiting.",
        "12": "Compatibility advances directly to state 13 after denominator "
              "addition; native 48->49 waits for its FP32 addition before the "
              "same next value request. No time/component counter advances early.",
        "14": "Compatibility 14->50->51 or native 14->52->53->54->55 completes "
              "the accepted value's weighted accumulation before the original "
              "state-15 time/denominator decision.",
        "15": "More-time and zero-denominator branches retain their actions. "
              "Otherwise 15->56->57 computes and stores the original rounded/"
              "saturated quotient; native 58->59->60->61 waits for reciprocal "
              "and multiply. Both reach state 16 only with a completed result.",
    },
    "rope": {
        "8": "The sine response now traverses 8->16->17->9. Signed products "
             "and the two rounded/saturated results are registered before "
             "either original write. Native 18->19->20->21 waits for all four "
             "multipliers and both adders before the same state-9 write. "
             "Pair/head/key counters remain unchanged "
             "until both write acknowledgements.",
    },
    "rmsnorm": {
        "2": "2->16->17->18 registers square/reduction before the original "
             "index increment or mean computation. Native 20->21->22->23->24 "
             "waits for FP32 square/add before the same index decision; no "
             "intervening request is enabled.",
        "3": "3->40 waits for (sum<<32)/HIDDEN_SIZE and adds the original "
             "epsilon before state 4. Native 26..31 waits for reciprocal-H, "
             "multiply and epsilon addition. Legal HIDDEN_SIZE is positive.",
        "4": "4->41 waits for the original integer square root before state 5. "
             "Native 32->33 combines square-root/reciprocal arithmetic in rsqrt.",
        "5": "5->42 waits for 2^64/denominator before the original index reset "
             "and state-6 second pass. Native 33 performs that same index reset "
             "and handoff only after rsqrt is valid. Positive epsilon makes "
             "the normalization denominator nonzero.",
        "9": "Invalid gamma still faults on its response. Otherwise "
             "9->43->44->45 registers the signed products and original round/"
             "saturation; native 36->37->38->39 waits for both FP32 multipliers. "
             "Only then can state 10 issue the original destination write.",
    },
    "elementwise": {
        "4": "After the second response, residual modes use 4->7->5; "
             "mode 2 uses 4->8->9->10->11->5 and waits for compatibility "
             "SiLU before its product. Native residual modes wait 16->17; "
             "native SiLU waits 18..29 for exp/add/reciprocal and the required "
             "products. In all modes the destination request is disabled "
             "until the corresponding result register is complete.",
    },
}


def fingerprint(value):
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def manual_audit(root, modules, hashes):
    inventory = {name: value["items"] for name, value in modules.items()}
    rtl_hashes = {path: value for path, value in hashes.items()
                  if path.startswith("rtl/")}
    if rtl_hashes != REVIEWED_RTL_SHA256 or fingerprint(hashes) != TREE_SHA256:
        changed = sorted(path for path in rtl_hashes.keys() | REVIEWED_RTL_SHA256.keys()
                         if rtl_hashes.get(path) != REVIEWED_RTL_SHA256.get(path))
        raise ValueError("Independent preservation review requires renewed source audit; "
                         "changed RTL paths: " + ", ".join(changed))
    if (fingerprint(inventory) != INVENTORY_SHA256 or
            sum(map(len, inventory.values())) != ORIGINAL_ITEMS):
        raise ValueError("Independent preservation review requires renewed inventory audit")
    entries = []
    for module, record in modules.items():
        if record["byte_identical"]:
            continue
        scope = SCOPES[module]
        target = record["revised_file"]
        lines = [1, len((root / target).read_text().splitlines())]
        for item in record["items"]:
            classification, proof = "R", scope
            state_case = any(g.startswith("state in {") for g in item["guards"])
            state = item["state"] if state_case else None
            text = item["text"]
            if module == "w4a16_gemv":
                classification = "C"
                proof = (
                    "Conservatively uncredited as part of the changed GEMV "
                    "microarchitecture: native kind-12 streaming replaces the "
                    "original packed-weight/zero/scale fetch schedule. Mode-00 "
                    "retention and shared counters are not used to claim "
                    "cross-precision preservation for any item in this module. "
                    + scope)
            elif module == "top" and state == "0" and any(
                    "token_id" in guard for guard in item["guards"]):
                classification = "C"
                proof = (
                    "Not credited: invalid commands now invalidate continuation, "
                    "and precision-sensitive sequence validation extends the "
                    "original admission predicate. A valid position-zero new "
                    "sequence is required for recovery. This is an intentional "
                    "fault/precision contract change, not wait-only equivalence.")
            elif (item["kind"] != "request_routing_decode_action" and
                  state in RETIME.get(module, {})):
                classification, proof = "E", RETIME[module][state]
            elif (module in ("top", "swiglu_mlp") and
                  item["kind"] == "functional_port_connection" and
                  text.split(" = ", 1)[0] in (
                      "decoder/2", "final_norm/2", "gemv/2", "silu_product/2")):
                classification = "E"
                proof = (
                    "Added rst_n gating changes the internal command pin only "
                    "during reset, when child ready is zero and synchronous "
                    "reset has priority over command capture. Outside reset "
                    "the original acceptance predicate and bus owner are identical.")
            elif module == "gqa_attention" and "head / RATIO" in text:
                classification = "E"
                proof = (
                    "kv_head=floor(head/RATIO), group_offset=head%RATIO. "
                    "All initialize to zero; only acknowledged completion of "
                    "the last component advances head and the offset, with "
                    "offset wrap advancing kv_head. Component/time traversals "
                    "do not change them. Thus both key/value column formulas "
                    "and layer/position ownership are identical for every "
                    "legal grouping, including 7:1.")
            elif (text.startswith("wd =") and text != "wd = 0") or (
                    module == "top" and text.startswith("logit_data =")):
                classification = "E"
                proof = (
                    "The completed arithmetic result uses the command's selected "
                    "encoding (original compatibility bits or native FP32). "
                    "Write/logit issue, address/index, ownership, stall stability "
                    "and acknowledgement remain the original command's in all "
                    "precisions; added arithmetic waits finish before issue. "
                    "Encoding is selected only by captured precision. " + scope)
            entries.append({
                "id": item["id"], "classification": classification,
                "proof": proof, "revised_file": target, "revised_lines": lines,
            })
    return {"schema": 1, "source_sha256": hashes, "items": entries,
            "review_basis": REVIEW_BASIS}
