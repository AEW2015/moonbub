#!/usr/bin/env python3
"""Exercise the V83 schedule audit verifier with controlled valid/invalid DAGs."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUDIT_PATH = ROOT / "experiments/python-gamebub-v83/audit.py"
OUT_PATH = ROOT / "experiments/python-gamebub-v83/audit-tests.json"
spec = importlib.util.spec_from_file_location("cu66_v83_audit", AUDIT_PATH)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def base_case():
    jobs = [
        {"id": "a", "duration": 2, "resource": "cpu", "deps": []},
        {"id": "m", "duration": 2, "resource": "memory", "deps": ["a"]},
        {"id": "b", "duration": 1, "resource": "cpu", "deps": ["m"]},
    ]
    timeline = [
        {"id": "a", "start": 0, "finish": 2, "resource": "cpu"},
        {"id": "m", "start": 2, "finish": 4, "resource": "memory"},
        {"id": "b", "start": 4, "finish": 5, "resource": "cpu"},
    ]
    return jobs, timeline, {"cpu": 1, "memory": 1}, {
        "period": 10, "blocked": [(6, 8)]
    }, [{"start": "a", "release": "b"}], 1


def halfopen_case():
    jobs = [
        {"id": "left", "duration": 2, "resource": "cpu", "deps": []},
        {"id": "right", "duration": 1, "resource": "cpu", "deps": []},
        {"id": "mem", "duration": 2, "resource": "memory", "deps": []},
    ]
    timeline = [
        {"id": "left", "start": 0, "finish": 2, "resource": "cpu"},
        {"id": "right", "start": 2, "finish": 3, "resource": "cpu"},
        {"id": "mem", "start": 0, "finish": 2, "resource": "memory"},
    ]
    groups = [
        {"start": "left", "release": "left"},
        {"start": "right", "release": "right"},
    ]
    return jobs, timeline, {"cpu": 1, "memory": 1}, {
        "period": 10, "blocked": [(2, 4)]
    }, groups, 1


def expect_reject(name, expected, mutate):
    jobs, timeline, capacities, windows, groups, slots = base_case()
    jobs, timeline = copy.deepcopy(jobs), copy.deepcopy(timeline)
    mutate(jobs, timeline)
    try:
        audit.verify(jobs, timeline, capacities, windows, groups, slots)
    except (AssertionError, KeyError, TypeError) as exc:
        message = str(exc)
        if expected == "AssertionError":
            if not isinstance(exc, AssertionError):
                raise AssertionError(f"{name}: expected AssertionError, got {type(exc).__name__}") from exc
        elif expected not in message:
            raise AssertionError(f"{name}: expected {expected!r}, got {message!r}") from exc
        return {"name": name, "result": "rejected_as_expected", "reason": message}
    raise AssertionError(f"{name}: malformed schedule was accepted")


def expect_accept(name, case):
    result = audit.verify(*case())
    return {"name": name, "result": "accepted_as_expected", "summary": result}


def main():
    checks = [expect_accept("valid_dependency_and_resource_schedule", base_case),
              expect_accept("halfopen_resource_group_and_reserved_window_boundaries", halfopen_case)]

    def bad_dependency(jobs, timeline):
        timeline[2].update(start=3, finish=4)

    def wrong_duration(jobs, timeline):
        timeline[0]["finish"] = 3

    def missing_job(jobs, timeline):
        timeline.pop()

    def duplicate_job(jobs, timeline):
        jobs.append(copy.deepcopy(jobs[0]))

    def wrong_resource(jobs, timeline):
        timeline[0]["resource"] = "memory"

    def overlap_capacity(jobs, timeline):
        jobs.append({"id": "x", "duration": 2, "resource": "cpu", "deps": []})
        timeline.append({"id": "x", "start": 1, "finish": 3, "resource": "cpu"})

    def reserved_window(jobs, timeline):
        timeline[1].update(start=5, finish=7)
        timeline[2].update(start=7, finish=8)

    checks.extend([
        expect_reject("bad_dependency_timing", "dependency", bad_dependency),
        expect_reject("wrong_duration", "duration", wrong_duration),
        expect_reject("missing_timeline_job", "timeline membership", missing_job),
        expect_reject("duplicate_job_id", "duplicate job", duplicate_job),
        expect_reject("wrong_resource", "AssertionError", wrong_resource),
        expect_reject("resource_capacity_overlap", "capacity", overlap_capacity),
        expect_reject("reserved_window_violation", "reserved-window", reserved_window),
    ])

    # The group intervals [a.start, b.finish) and [x.start, x.finish) overlap.
    jobs, timeline, capacities, windows, groups, slots = base_case()
    jobs.append({"id": "x", "duration": 2, "resource": None, "deps": []})
    timeline.append({"id": "x", "start": 1, "finish": 3, "resource": None})
    checks.append(expect_group_reject(jobs, timeline, capacities, windows,
                                      groups + [{"start": "x", "release": "x"}],
                                      slots, "group buffer capacity"))

    hashes = {
        "experiments/python-gamebub-v83/audit.py": hashlib.sha256(AUDIT_PATH.read_bytes()).hexdigest(),
        "scripts/cu66-v83/test_audit.py": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    report = {"schema": "cu66-v83-audit-tests-v1", "checks": checks,
              "passed": len(checks), "failed": 0, "source_sha256": hashes}
    OUT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"V83_AUDIT_TESTS_PASS checks={len(checks)}")


def expect_group_reject(jobs, timeline, capacities, windows, groups, slots, expected):
    try:
        audit.verify(jobs, timeline, capacities, windows, groups, slots)
    except AssertionError as exc:
        message = str(exc)
        if expected not in message:
            raise AssertionError(f"group_buffer_oversubscription: expected {expected!r}, got {message!r}") from exc
        return {"name": "group_buffer_oversubscription", "result": "rejected_as_expected",
                "reason": message}
    raise AssertionError("group_buffer_oversubscription: malformed schedule was accepted")


if __name__ == "__main__":
    main()
