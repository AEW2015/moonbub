#!/usr/bin/env python3
"""Validate finite V122-style edge wait traces; this is a schema checker only."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

SCHEMA = "v122-exclusive-wait-trace-v1"
MAX_EDGES = 4_000_000
MAX_BYTES = 1024 * 1024 * 1024
WAIT_OWNERS = ("producer_full", "software_hud_blocked", "physical_request_blocked",
               "hash_delivery_blocked", "physical_service_pending", "other_blocked")
OWNER_PRIORITY = WAIT_OWNERS
NON_OWNER_CONDITIONS = ("reconstruction_active", "validation_active")
CONDITIONS = WAIT_OWNERS + NON_OWNER_CONDITIONS
REQUIRED_FENCES = ("frame_start", "decode_start", "reconstruct_done",
                   "canonical_validated", "hud_validated", "root_validated",
                   "seal_validated", "commit_ready", "decode_end")


class TraceError(ValueError):
    pass


def need(test: bool, message: str) -> None:
    if not test:
        raise TraceError(message)


def condition_bits(header: dict) -> dict[str, int]:
    bits = header.get("condition_bits")
    need(isinstance(bits, dict) and set(bits) == set(CONDITIONS), "condition_bits must name every schema condition exactly")
    values = list(bits.values())
    need(all(type(v) is int and v > 0 and v & (v - 1) == 0 for v in values), "condition bits must be positive single-bit integers")
    need(len(set(values)) == len(values), "condition bits must be unique")
    return bits


def validate_trace(trace: dict) -> dict:
    need(isinstance(trace, dict) and trace.get("schema") == SCHEMA, "unsupported trace schema")
    h = trace.get("header")
    need(isinstance(h, dict), "missing header")
    need(set(trace) == {"schema", "header", "edges", "fences", "publication"}, "unknown trace/control fields")
    header_keys = {"trace_scope", "frame_outcome", "initial_outstanding", "frame_id", "epoch", "bank",
                   "transaction_token", "clock_hz", "timebase_assumption", "trace_start_cycle",
                   "trace_end_cycle", "max_outstanding_writes", "owner_priority", "condition_bits",
                   "declared_totals"}
    need(set(h) == header_keys, "unknown or missing header/control fields")
    need(h.get("trace_scope") == "full_frame_before_first_acceptance", "trace must cover full frame from before first write acceptance")
    need(h.get("frame_outcome") == "published_successfully", "schema supports successful single-epoch frames only")
    need(h.get("initial_outstanding") == [], "initial outstanding ledger must be explicitly empty for full-frame trace")
    need(type(h.get("frame_id")) is int and h["frame_id"] >= 0, "invalid frame_id")
    need(type(h.get("epoch")) is int and h["epoch"] >= 0, "invalid epoch")
    need(type(h.get("bank")) is int and h["bank"] >= 0, "invalid bank")
    need(isinstance(h.get("transaction_token"), str) and bool(h["transaction_token"]), "missing transaction_token")
    need(type(h.get("clock_hz")) is int and h["clock_hz"] > 0, "invalid assumed clock_hz")
    need(isinstance(h.get("timebase_assumption"), str) and h["timebase_assumption"].strip(), "missing timebase assumption")
    start, end = h.get("trace_start_cycle"), h.get("trace_end_cycle")
    need(type(start) is int and type(end) is int and start >= 0 and end > start, "invalid half-open trace interval")
    need(end - start <= MAX_EDGES, "trace edge limit exceeded")
    need(type(h.get("max_outstanding_writes")) is int and h["max_outstanding_writes"] == 1, "max_outstanding_writes must explicitly be 1 for the retained baseline contract")
    need(h.get("owner_priority") == list(OWNER_PRIORITY), "unknown exclusive-owner priority policy")
    bits = condition_bits(h)
    mask_limit = sum(bits.values())

    edges = trace.get("edges")
    need(isinstance(edges, list) and len(edges) == end - start, "edge count does not cover declared interval")
    # Fixed-size coverage plus cycle equality rejects both gaps and duplicates.
    for offset, edge in enumerate(edges):
        need(isinstance(edge, dict) and set(edge) == {"cycle", "wait_owner", "condition_mask", "accepted_writes", "acked_writes"}, "unknown or missing edge/control fields")
        need(type(edge.get("cycle")) is int and edge["cycle"] == start + offset, "missing, duplicate, or out-of-order edge")
        owner = edge.get("wait_owner")
        need(owner in WAIT_OWNERS or owner == "none", "invalid wait owner")
        mask = edge.get("condition_mask")
        need(type(mask) is int and mask >= 0 and mask & ~mask_limit == 0, "invalid condition mask")
        active_waits = [name for name in OWNER_PRIORITY if mask & bits[name]]
        expected_owner = active_waits[0] if active_waits else "none"
        need(owner == expected_owner, "wait owner does not follow declared priority for raw condition mask")
        for key in ("accepted_writes", "acked_writes"):
            need(isinstance(edge.get(key, []), list), key + " must be a list")

    fences = trace.get("fences")
    need(isinstance(fences, list), "missing fences")
    fence_map = {}
    for f in fences:
        need(isinstance(f, dict) and set(f) == {"name", "cycle", "frame_id", "epoch", "bank", "token"}, "malformed or unknown fence fields")
        name = f.get("name")
        need(name in REQUIRED_FENCES and name not in fence_map, "invalid or duplicate fence name")
        need(type(f.get("cycle")) is int and start <= f["cycle"] <= end, "fence outside trace interval")
        for key in ("frame_id", "epoch", "bank", "token"):
            expected = h["transaction_token"] if key == "token" else h[key]
            need(type(f.get(key)) is type(expected) and f.get(key) == expected, "fence frame/epoch/bank/token mismatch")
        fence_map[name] = f["cycle"]
    need(set(fence_map) == set(REQUIRED_FENCES), "required named fences missing")
    need(fence_map["frame_start"] == start and fence_map["decode_start"] < fence_map["decode_end"], "invalid frame/decode interval fences")
    validation_names = ("reconstruct_done", "canonical_validated", "hud_validated", "root_validated", "seal_validated")
    need(all(fence_map[n] <= fence_map["commit_ready"] for n in validation_names), "completion/validation fence follows commit_ready")

    publication = trace.get("publication")
    need(isinstance(publication, dict), "missing publication record")
    need(type(publication.get("frame_id")) is int and publication.get("frame_id") == h["frame_id"] and
         type(publication.get("epoch")) is int and publication.get("epoch") == h["epoch"] and
         type(publication.get("bank")) is int and publication.get("bank") == h["bank"] and
         isinstance(publication.get("token"), str) and publication.get("token") == h["transaction_token"],
         "publication frame/epoch/bank/token mismatch")
    pub_cycle = publication.get("cycle")
    need(type(pub_cycle) is int and fence_map["decode_end"] == pub_cycle and pub_cycle <= end, "decode_end must equal publication cycle")
    need(pub_cycle > fence_map["commit_ready"], "publication must follow commit_ready")

    need(set(publication) == {"cycle", "frame_id", "epoch", "bank", "token", "outstanding_writes"}, "unknown or missing publication/control fields")
    ledger = {}
    seen_tokens = set()
    accepted_count = acked_count = accepted_bytes = acked_bytes = 0
    peak = 0
    for edge in edges:
        if edge["cycle"] >= pub_cycle:
            need(not edge.get("accepted_writes") and not edge.get("acked_writes"), "write event occurs at or after publication")
            continue
        # A same-edge accept/ACK is ordered accept first, then ACK. This is
        # deliberate ledger ordering, not evidence of zero physical latency.
        for w in edge.get("accepted_writes", []):
            need(isinstance(w, dict) and set(w) == {"bank", "epoch", "token", "bytes"}, "malformed or unknown accepted-write fields")
            key = (w.get("bank"), w.get("epoch"), w.get("token"))
            nbytes = w.get("bytes")
            need(type(key[0]) is int and key[0] == h["bank"] and type(key[1]) is int and key[1] == h["epoch"] and isinstance(key[2], str) and key[2], "accepted write bank/epoch/token mismatch")
            need(type(nbytes) is int and nbytes > 0, "invalid accepted write bytes")
            need(key not in seen_tokens, "reused accepted write token")
            seen_tokens.add(key)
            ledger[key] = nbytes
            accepted_count += 1
            accepted_bytes += nbytes
            peak = max(peak, len(ledger))
            need(len(ledger) <= h["max_outstanding_writes"], "accepted write credit limit exceeded")
        for w in edge.get("acked_writes", []):
            need(isinstance(w, dict) and set(w) == {"bank", "epoch", "token", "bytes"}, "malformed or unknown ACK fields")
            key = (w.get("bank"), w.get("epoch"), w.get("token"))
            need(type(key[0]) is int and key[0] == h["bank"] and type(key[1]) is int and key[1] == h["epoch"] and
                 isinstance(key[2], str) and key[2], "ACK bank/epoch/token mismatch")
            need(key in ledger, "ACK has no matching accepted write")
            need(type(w.get("bytes")) is int and w.get("bytes") == ledger[key], "ACK byte count mismatch")
            del ledger[key]
            acked_count += 1
            acked_bytes += w["bytes"]

    need(not ledger, "frame ended with unpaid accepted-write debt")
    need(type(publication.get("outstanding_writes")) is int and publication.get("outstanding_writes") == 0 and not ledger, "publication with outstanding write debt")

    owner_counts = {o: 0 for o in (*WAIT_OWNERS, "none")}
    decode_owner_counts = {o: 0 for o in (*WAIT_OWNERS, "none")}
    condition_counts = {name: 0 for name in CONDITIONS}
    for edge in edges:
        owner_counts[edge["wait_owner"]] += 1
        if fence_map["decode_start"] <= edge["cycle"] < fence_map["decode_end"]:
            decode_owner_counts[edge["wait_owner"]] += 1
        for name, bit in bits.items():
            condition_counts[name] += bool(edge["condition_mask"] & bit)
    expected_totals = h.get("declared_totals")
    need(isinstance(expected_totals, dict), "missing declared_totals")
    need(expected_totals.get("trace_edge_count") == len(edges) and
         expected_totals.get("write_accept_count") == accepted_count and
         expected_totals.get("write_ack_count") == acked_count and
         expected_totals.get("accepted_write_bytes") == accepted_bytes and
         expected_totals.get("acked_write_bytes") == acked_bytes and
         expected_totals.get("wait_owner_edges") == owner_counts and
         expected_totals.get("decode_wait_owner_edges") == decode_owner_counts and
         expected_totals.get("raw_condition_edges") == condition_counts,
         "declared totals mismatch")
    return {"schema": SCHEMA, "status": "PASS", "frame_id": h["frame_id"], "epoch": h["epoch"],
            "trace_edge_count": len(edges), "decode_interval_cycles": fence_map["decode_end"] - fence_map["decode_start"],
            "accepted_write_count": accepted_count, "acked_write_count": acked_count,
            "accepted_write_bytes": accepted_bytes, "acked_write_bytes": acked_bytes,
            "peak_outstanding_writes": peak, "final_outstanding_writes": len(ledger),
            "wait_owner_edges": owner_counts, "decode_wait_owner_edges": decode_owner_counts,
            "raw_condition_edges": condition_counts,
            "owner_classification_is_causal": False,
            "time_conversion_is_hardware_measurement": False}


def make_trace() -> dict:
    bits = {name: 1 << i for i, name in enumerate(CONDITIONS)}
    edges = []
    for cycle in range(100, 107):
        mask, owner = 0, "none"
        if cycle == 101:
            mask = bits["producer_full"] | bits["software_hud_blocked"]
            owner = "producer_full"
        if cycle == 102:
            mask, owner = bits["physical_service_pending"], "physical_service_pending"
        accepted = ([{"bank": 0, "epoch": 7, "token": "w0", "bytes": 8}] if cycle == 101 else [])
        acked = ([{"bank": 0, "epoch": 7, "token": "w0", "bytes": 8}] if cycle == 103 else [])
        edges.append({"cycle": cycle, "wait_owner": owner, "condition_mask": mask,
                      "accepted_writes": accepted, "acked_writes": acked})
    fences = [{"name": name, "cycle": cycle, "frame_id": 4, "epoch": 7, "bank": 0, "token": "frame-4-e7"}
              for name, cycle in zip(REQUIRED_FENCES, (100, 101, 102, 103, 103, 104, 104, 104, 105))]
    h = {"trace_scope": "full_frame_before_first_acceptance", "frame_outcome": "published_successfully", "initial_outstanding": [],
         "frame_id": 4, "epoch": 7, "bank": 0, "transaction_token": "frame-4-e7",
         "clock_hz": 125_000_000, "timebase_assumption": "synthetic cycles; declared nominal clock only",
         "trace_start_cycle": 100, "trace_end_cycle": 107, "max_outstanding_writes": 1,
         "owner_priority": list(OWNER_PRIORITY), "condition_bits": bits}
    owners = {o: 0 for o in (*WAIT_OWNERS, "none")}
    decode_owners = dict(owners)
    raw = {n: 0 for n in CONDITIONS}
    for e in edges:
        owners[e["wait_owner"]] += 1
        if 101 <= e["cycle"] < 105:
            decode_owners[e["wait_owner"]] += 1
        for name, bit in bits.items():
            raw[name] += bool(e["condition_mask"] & bit)
    h["declared_totals"] = {"trace_edge_count": 7, "write_accept_count": 1, "write_ack_count": 1,
        "accepted_write_bytes": 8, "acked_write_bytes": 8, "wait_owner_edges": owners,
        "decode_wait_owner_edges": decode_owners, "raw_condition_edges": raw}
    return {"schema": SCHEMA, "header": h, "edges": edges, "fences": fences,
            "publication": {"cycle": 105, "frame_id": 4, "epoch": 7, "bank": 0,
                             "token": "frame-4-e7", "outstanding_writes": 0}}


def run_self_test(out: Path) -> dict:
    base = make_trace()
    tests = []
    def accepted(name: str, mutate=None):
        trace = json.loads(json.dumps(base))
        if mutate:
            mutate(trace)
        try:
            summary = validate_trace(trace)
            tests.append({"name": name, "accepted": True, "status": summary["status"]})
        except Exception as exc:
            tests.append({"name": name, "accepted": False, "error": str(exc)})
    def rejected(name: str, mutate):
        trace = json.loads(json.dumps(base)); mutate(trace)
        try:
            validate_trace(trace)
            tests.append({"name": name, "rejected": False, "error": "validator accepted malformed trace"})
        except TraceError as exc:
            tests.append({"name": name, "rejected": True, "error": str(exc)})
    accepted("valid_trace_with_overlapping_raw_conditions")
    def reorder_validation_fences(t):
        next(f for f in t["fences"] if f["name"] == "canonical_validated")["cycle"] = 102
        next(f for f in t["fences"] if f["name"] == "hud_validated")["cycle"] = 104
        next(f for f in t["fences"] if f["name"] == "root_validated")["cycle"] = 103
    accepted("valid_reordered_overlapping_validation_fences", reorder_validation_fences)
    rejected("missing_edge", lambda t: t["edges"].pop(2))
    rejected("duplicate_edge", lambda t: t["edges"].__setitem__(2, dict(t["edges"][1])))
    rejected("invalid_owner", lambda t: t["edges"][0].update(wait_owner="mystery"))
    rejected("invalid_condition_mask", lambda t: t["edges"][0].update(condition_mask=1 << 20))
    rejected("owner_priority_mismatch_on_overlap", lambda t: t["edges"][1].update(wait_owner="software_hud_blocked"))
    rejected("mismatched_epoch", lambda t: t["edges"][1]["accepted_writes"][0].update(epoch=8))
    rejected("mismatched_token", lambda t: t["fences"][3].update(token="wrong"))
    rejected("decode_end_not_publication", lambda t: next(f for f in t["fences"] if f["name"] == "decode_end").update(cycle=104))
    rejected("unpaid_accepted_write", lambda t: t["edges"][3].update(acked_writes=[]))
    rejected("premature_publication_with_debt", lambda t: (t["edges"][3].update(acked_writes=[]), t["publication"].update(outstanding_writes=1)))
    rejected("ACK_at_publication_edge", lambda t: (t["edges"][3].update(acked_writes=[]), t["edges"][5].update(acked_writes=[{"bank":0,"epoch":7,"token":"w0","bytes":8}])))
    rejected("reused_token_after_ACK", lambda t: (t["edges"][4].update(accepted_writes=[{"bank":0,"epoch":7,"token":"w0","bytes":8}], acked_writes=[{"bank":0,"epoch":7,"token":"w0","bytes":8}])))
    rejected("declared_totals_mismatch", lambda t: t["header"]["declared_totals"].update(write_ack_count=2))
    rejected("initial_ledger_not_empty", lambda t: t["header"].update(initial_outstanding=[{"token":"hidden"}]))
    rejected("unsupported_abort_control", lambda t: t["edges"][2].update(abort=True))
    need(all(t.get("accepted") is True or t.get("rejected") is True for t in tests), "self-test expectation failed")
    summary = validate_trace(base)
    result = {"schema": "v122-wait-trace-self-test-v1", "classification": "synthetic validator tests only; not actual RTL instrumentation, model validation, or hardware qualification",
              "validator_schema": SCHEMA, "test_count": len(tests), "all_expectations_passed": True,
              "tests": tests, "valid_synthetic_summary": summary,
              "scope_limit": "No existing retained aggregate counters were converted into causal cycle ownership."}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("trace", nargs="?", type=Path, help="JSON trace to validate")
    ap.add_argument("--self-test", action="store_true", help="run bounded synthetic validator tests and write the declared report")
    ap.add_argument("--output", type=Path, default=Path("experiments/python-gamebub-v122/memory-study/wait-trace-self-test.json"))
    args = ap.parse_args()
    try:
        if args.self_test:
            result = run_self_test(args.output)
        else:
            need(args.trace is not None, "provide trace JSON or --self-test")
            need(args.trace.stat().st_size <= MAX_BYTES, "trace byte limit exceeded")
            result = validate_trace(json.loads(args.trace.read_text()))
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except Exception as exc:
        print("WAIT_TRACE_FAIL: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
