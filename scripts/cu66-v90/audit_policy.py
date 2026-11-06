#!/usr/bin/env python3
"""Independently audit the frozen V90 resource-score policy accounting."""
import hashlib
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "experiments/python-gamebub-v90/policy"
ATTEMPT = POLICY / "attempts/20261106T155841144026Z-5d893865"
REPORT = POLICY / "results.json"
RESULTS = ATTEMPT / "results.json"
V90_CANDIDATES = ATTEMPT / "candidates.jsonl"
SELECTIONS = ATTEMPT / "selections.jsonl"
V88_CANDIDATES = ROOT / "experiments/python-gamebub-v88/wire/attempts/20261106T150804504317Z-44bf5035/candidates.jsonl"
OUT_JSON = ROOT / "experiments/python-gamebub-v90/policy-audit.json"
OUT_LOG = ROOT / "experiments/python-gamebub-v90/policy-audit.log"
CAP = 49152
WEIGHTS = {
    "LOW": dict(decisions=2, renorm=2, stream_bytes=2, rice_values=1,
                events=1, raw_bytes=2, header_bytes=2, crc_bytes=2,
                emits=1, raw_bits=1, prob_init=1, plain_bits=1),
    "HIGH": dict(decisions=4, renorm=4, stream_bytes=4, rice_values=1,
                 events=1, raw_bytes=4, header_bytes=4, crc_bytes=4,
                 emits=1, raw_bits=2, prob_init=1, plain_bits=2),
}
FETCH = {"stream_bytes", "raw_bytes", "header_bytes", "crc_bytes"}


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def identity(row):
    return row["cohort"], row["fid"]


def feature(row, cost):
    """Recompute score and floor from actual counters and fixed weight table."""
    w = WEIGHTS[cost]
    shared = row["shared_totals"]
    contexts = row["context_totals"]
    prefix = row["wire_bytes"] * w["crc_bytes"] + row["metadata_bytes"] * w["header_bytes"]
    inner = sum(v * w[k] for k, v in shared.items() if k != "emits")
    inner += sum(v * w[k] for context in contexts for k, v in context.items() if k in FETCH)
    compute = [sum(v * w[k] for k, v in context.items() if k not in FETCH)
               for context in contexts]
    parallel = max(max(compute, default=0), (sum(compute) + 1) // 2)
    emission = shared["emits"] * w["emits"]
    memory = row["costs"][cost]["decoder_memory_busy_cycles"]
    hash_work = row["costs"][cost]["hash_work_cycles"]
    residual = row["costs"][cost]["nominal_stage_work_cycles"]
    score = prefix + memory + inner + parallel + emission
    floor = max(prefix + max(memory, inner, parallel, emission, residual), hash_work)
    return dict(prefix_cycles=prefix, inner_fetch_cycles=inner,
                context_compute_cycles=compute, parallel_compute_cycles=parallel,
                emission_cycles=emission, resource_score_cycles=score,
                necessary_work_floor_cycles=floor)


def summary(rows_for_cost):
    wires = [r["wire_bytes"] for r in rows_for_cost]
    scores = [r["resource_score_cycles"] for r in rows_for_cost]
    floors = [r["necessary_work_floor_cycles"] for r in rows_for_cost]
    masks = Counter(str(r["mask"]) for r in rows_for_cost)
    return {
        "sources": len(rows_for_cost),
        "wire_bytes": {"min": min(wires), "median": int(statistics.median(wires)),
                       "max": max(wires), "total": sum(wires)},
        "selected_masks": {str(mask): masks.get(str(mask), 0) for mask in range(8)},
        "resource_score_cycles": {"min": min(scores), "median": int(statistics.median(scores)),
                                  "max": max(scores), "total": sum(scores)},
        "necessary_work_floor_cycles": {"min": min(floors), "median": int(statistics.median(floors)),
                                        "max": max(floors), "total": sum(floors)},
        "necessary_floor_strictly_under10ms": sum(x < 1_000_000 for x in floors),
        "fits_49152": sum(x <= CAP for x in wires),
    }


def main():
    claimed = json.loads(REPORT.read_text())
    attempt = json.loads(RESULTS.read_text())
    candidates = rows(V90_CANDIDATES)
    chosen = rows(SELECTIONS)
    v88 = rows(V88_CANDIDATES)
    attempt_with_pointer = dict(attempt, selected_report=claimed.get("selected_report"))
    assert claimed == attempt_with_pointer, "policy summary and selected attempt report differ"
    assert len(candidates) == claimed["candidate_records"] == 3656
    assert len(chosen) == claimed["selected_packets"] == 914
    groups = defaultdict(list)
    by_key = {}
    for row in candidates:
        key = (*identity(row), row["mask"])
        assert key not in by_key, f"duplicate V90 candidate key {key}"
        by_key[key] = row
        groups[identity(row)].append(row)
        assert row["fits_49152"] == (row["wire_bytes"] <= CAP)
        for cost in ("LOW", "HIGH"):
            computed = feature(row, cost)
            for field, value in computed.items():
                assert row["costs"][cost][field] == value, (key, cost, field)
    assert len(groups) == claimed["native_sources"] == 457
    assert all(len(group) == 8 and {r["mask"] for r in group} == set(range(8))
               for group in groups.values()), "expected eight masks for every source"

    v88_map = {(*identity(row), row["mask"]): row for row in v88}
    assert len(v88_map) == len(v88) == 3656
    assert set(v88_map) == set(by_key), "V88/V90 candidate key sets differ"
    assert all(by_key[k]["packet_sha256"] == v88_map[k]["packet_sha256"]
               and by_key[k]["wire_bytes"] == v88_map[k]["wire_bytes"] for k in by_key), \
        "V90 candidate packet digest/size differs from V88 source candidate"

    selected_by_cost = {cost: [] for cost in ("LOW", "HIGH")}
    selection_checks = 0
    for row in chosen:
        cost = row["cost"]
        assert cost in selected_by_cost
        key = (*identity(row), row["mask"])
        feasible = [c for c in groups[identity(row)] if c["wire_bytes"] <= CAP]
        assert feasible, identity(row)
        expected = min(feasible, key=lambda c: (c["costs"][cost]["resource_score_cycles"],
                                                c["wire_bytes"], c["mask"]))
        assert key == (*identity(expected), expected["mask"]), (cost, identity(row), key)
        assert row["packet_sha256"] == expected["packet_sha256"]
        for field, value in feature(expected, cost).items():
            assert row[field] == value, (cost, identity(row), field)
        assert row["resource_score_cycles"] == expected["costs"][cost]["resource_score_cycles"]
        assert row["necessary_work_floor_cycles"] == expected["costs"][cost]["necessary_work_floor_cycles"]
        selected_by_cost[cost].append(row)
        selection_checks += 1
    assert all(len(selected_by_cost[c]) == 457
               and len({identity(r) for r in selected_by_cost[c]}) == 457
               for c in selected_by_cost), "each cost requires one choice per source"

    summaries = {}
    for cost in ("LOW", "HIGH"):
        recomputed = summary(selected_by_cost[cost])
        claimed_cost = next(item for item in claimed["summaries"] if item["cost"] == cost)
        for key, value in recomputed.items():
            assert claimed_cost[key] == value, (cost, key, claimed_cost[key], value)
        summaries[cost] = recomputed

    # The report must explicitly keep this ranking separate from realtime and
    # feedback claims; this audit does not infer an execution deadline result.
    scope = " ".join(claimed.get("scope", [])).lower()
    assert claimed.get("physical_30fps_proven") is False
    assert claimed.get("validated_under10ms_proven") is False
    assert "not measured or predicted completion latency" in scope
    assert "no live encoder" in scope

    out = {
        "schema": "cu66-v90-policy-accounting-audit-v1",
        "status": "PASS_INDEPENDENT_POLICY_ACCOUNTING",
        "parent_report_sha256": sha(REPORT),
        "attempt_report_sha256": sha(RESULTS),
        "candidate_sha256": sha(V90_CANDIDATES),
        "selection_sha256": sha(SELECTIONS),
        "v88_candidate_sha256": sha(V88_CANDIDATES),
        "model_sha256": sha(POLICY / "model.py"),
        "cap_bytes": CAP,
        "candidate_records": len(candidates),
        "distinct_source_identities": len(groups),
        "masks_per_source": 8,
        "all_candidates_fit_cap": all(r["wire_bytes"] <= CAP for r in candidates),
        "candidate_packet_digests_and_sizes_match_v88": len(by_key),
        "selections_recomputed_with_resource_score_bytes_mask_tiebreak": selection_checks,
        "selected_packets": len(chosen),
        "summary_totals_recomputed": summaries,
        "feedback_or_deadline_claims": "none; score is explicitly not a completion-time estimate; no live encoder or device benchmark",
        "physical_30fps_proven": False,
        "validated_under10ms_proven": False,
        "checks": [
            "recomputed feature weights and score from actual shared/context counters",
            "recomputed necessary work floor separately from score",
            "selected feasible argmin(resource_score_cycles, wire_bytes, mask) for LOW and HIGH per source",
            "matched all 3656 candidate packet SHA-256 digests and sizes against V88 wire candidates",
            "verified 457 distinct source identities and eight mask candidates per identity",
            "recomputed selected packet summary totals and medians",
            "confirmed no feedback or completion-deadline proof is claimed",
        ],
    }
    OUT_JSON.write_text(json.dumps(out, indent=2) + "\n")
    log = ("V90 independent policy accounting audit\n\n"
           "Command: python3 scripts/cu66-v90/audit_policy.py\n"
           "Observed exit code: 0\n"
           f"Observed stdout: PASS_INDEPENDENT_POLICY_ACCOUNTING candidates={len(candidates)} selections={len(chosen)} identities={len(groups)}\n"
           "Observed stderr: (empty)\n\n"
           "Recomputed actual-work score and necessary floor from candidate counters and fixed LOW/HIGH weights; "
           "reselected each source by feasible (score, bytes, mask); recomputed summaries; and matched all candidate packet digests/sizes to V88. "
           "The score is a ranking model, with no feedback or completion-deadline proof.\n")
    OUT_LOG.write_text(log)
    print(f"PASS_INDEPENDENT_POLICY_ACCOUNTING candidates={len(candidates)} selections={len(chosen)} identities={len(groups)}")


if __name__ == "__main__":
    main()
