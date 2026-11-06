#!/usr/bin/env python3
"""Independent small-case checks for the V84 credit schedule audit."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUDIT_PATH = ROOT / "experiments/python-gamebub-v84/audit.py"
OUT_PATH = ROOT / "experiments/python-gamebub-v84/audit-tests.json"
spec = importlib.util.spec_from_file_location("cu66_v84_audit", AUDIT_PATH)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def case(inverse_tiles=(0, 1)):
    jobs = []

    def add(ident, kind, deps=(), tile=None, group=0):
        resource = "entropy" if kind == "entropy_tile" else kind
        job = {"id": ident, "kind": kind, "resource": resource, "duration": 1,
               "deps": list(deps)}
        if tile is not None:
            job.update(tile=tile, group=group)
        jobs.append(job)
        return ident

    start = add("group-start", "group_start")
    prior_entropy = prior_inverse = prior_reconstruct = None
    for tile in range(2):
        ref_deps = [start]
        if prior_reconstruct:
            ref_deps.append(prior_reconstruct)  # one reference slot
        ref = add(f"ref-{tile}", "reference_read", ref_deps, tile)
        entropy_deps = [start]
        if prior_entropy:
            entropy_deps.append(prior_entropy)
        if prior_inverse:
            entropy_deps.append(prior_inverse)  # one coefficient slot
        entropy = add(f"entropy-{tile}", "entropy_tile", entropy_deps, tile)
        mapped = add(f"map-{tile}", "map_lookup", [start, entropy], tile)
        if tile in inverse_tiles:
            inverse_deps = [mapped, ref]
            if prior_reconstruct:
                inverse_deps.append(prior_reconstruct)  # one inverse slot
            inverse = add(f"inverse-{tile}", "inverse", inverse_deps, tile)
            prior_inverse = inverse
            output_deps = [inverse]
            out_kind = "reconstruct"
        else:
            output_deps = [mapped]
            out_kind = "copy_ready"
        output_deps.append(ref)
        output = add(f"output-{tile}", out_kind, output_deps, tile)
        prior_entropy = entropy
        prior_reconstruct = output
    complete = add("complete", "complete", [j["id"] for j in jobs])
    work = {"jobs": jobs, "complete": complete,
            "groups": [{"start": start, "release": complete}]}
    # A simple serial list schedule is a valid realization of this small DAG.
    timeline, clock = [], 0
    remaining = {j["id"]: j for j in jobs}
    finished = set()
    while remaining:
        ready = next((j for j in jobs if j["id"] in remaining
                      and set(j["deps"]) <= finished), None)
        if ready is None:
            raise AssertionError("test fixture DAG has a cycle")
        timeline.append({"id": ready["id"], "start": clock,
                         "finish": clock + ready["duration"]})
        clock += ready["duration"]
        finished.add(ready["id"])
        del remaining[ready["id"]]
    return work, timeline


def run_verify(work, timeline, capacities=(1, 1, 1)):
    return audit.verify(work, timeline, ref_slots=capacities[0],
                        inverse_slots=capacities[1], coefficient_slots=capacities[2],
                        tile_count=2)


def expect_accept(name, work=None, timeline=None):
    if work is None:
        work, timeline = case()
    summary = run_verify(work, timeline)
    return {"name": name, "result": "accepted_as_expected", "summary": summary}


def expect_reject(name, mutate, capacities=(1, 1, 1)):
    work, timeline = case()
    work, timeline = copy.deepcopy(work), copy.deepcopy(timeline)
    mutate(work, timeline)
    try:
        run_verify(work, timeline, capacities)
    except (AssertionError, KeyError, TypeError) as exc:
        return {"name": name, "result": "rejected_as_expected",
                "reason": str(exc) or type(exc).__name__}
    raise AssertionError(f"{name}: malformed work was accepted")


def by_id(work, ident):
    return next(job for job in work["jobs"] if job["id"] == ident)


def main():
    checks = [
        expect_accept("valid_two_tile_lifetimes"),
        expect_accept("exact_slot_release_boundary"),
        expect_accept("hidden_inverse_skip_proper", *case(inverse_tiles=(0,))),
    ]

    def oversubscribe(work, timeline):
        row = next(r for r in timeline if r["id"] == "output-0")
        row["finish"] = 15  # keep first slot live over the second producer

    checks.append(expect_reject("negative_capacity_oversubscription", oversubscribe))

    def remove_entropy_map(work, timeline):
        by_id(work, "map-0")["deps"].remove("entropy-0")

    def remove_entropy_sequence(work, timeline):
        by_id(work, "entropy-1")["deps"].remove("entropy-0")

    def remove_group_start(work, timeline):
        by_id(work, "entropy-0")["deps"].remove("group-start")

    def remove_credit_reuse(work, timeline):
        by_id(work, "entropy-1")["deps"].remove("inverse-0")

    def premature_fence(work, timeline):
        by_id(work, "complete")["deps"].remove("output-1")

    checks.extend([
        expect_reject("missing_entropy_to_map_fence", remove_entropy_map),
        expect_reject("missing_sequential_entropy_edge", remove_entropy_sequence),
        expect_reject("missing_group_start_dependency", remove_group_start),
        expect_reject("missing_credit_reuse_edge", remove_credit_reuse),
        expect_reject("premature_final_fence", premature_fence),
    ])
    hashes = {
        "experiments/python-gamebub-v84/audit.py": hashlib.sha256(AUDIT_PATH.read_bytes()).hexdigest(),
        "scripts/cu66-v84/test_audit.py": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    report = {"schema": "cu66-v84-audit-tests-v1", "checks": checks,
              "passed": len(checks), "failed": 0, "source_sha256": hashes}
    OUT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"V84_AUDIT_TESTS_PASS checks={len(checks)}")


if __name__ == "__main__":
    main()
