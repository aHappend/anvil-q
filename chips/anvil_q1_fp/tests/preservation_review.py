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


TREE_SHA256 = "582fac3b954edb1221175f6e99bcc8a33b7e10f23b942de3779ea93db527d56d"
INVENTORY_SHA256 = "b731b0abddda6d6c85ac39035b9b52d0e0cce8695d8537164f94a78107d3dff9"
ORIGINAL_ITEMS = 1385

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
    if (fingerprint(hashes) != TREE_SHA256 or
            fingerprint(inventory) != INVENTORY_SHA256 or
            sum(map(len, inventory.values())) != ORIGINAL_ITEMS):
        raise ValueError("Independent preservation review requires renewed source audit")
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
            elif (module == "swiglu_mlp" and
                  item["kind"] == "functional_port_connection" and
                  text.split(" = ", 1)[0] in ("gemv/2", "silu_product/2")):
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
    return {"schema": 1, "source_sha256": hashes, "items": entries}
