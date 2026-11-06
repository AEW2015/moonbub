#!/usr/bin/env python3
"""Independent audit of the retained standalone V91l row RTL trace."""
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / "fpga/experiments/cu66-v91l-rows"
RESULTS = AREA / "row-results.json"
OUT = Path(__file__).with_name("row-audit.json")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def expected_row(n: int) -> dict:
    """Recompute independent tile raster coordinates and generated payload."""
    hud = n >= 192
    if hud:
        address = 518400 + (n - 192) * 8
        plane = tile = index = 0
    else:
        plane, rem = divmod(n, 64)
        tile, row_in_tile = divmod(rem, 8)
        index = row_in_tile * 8
        width = 720 if plane == 0 else 360
        base = (0, 345600, 432000)[plane]
        x = (tile % (width // 8)) * 8 + index % 8
        y = (tile // (width // 8)) * 8 + index // 8
        address = base + y * width + x
    data = [((n * 17 + j * 37 + 11) & 255) for j in range(8)]
    return {"hud": int(hud), "address": address, "plane": plane,
            "tile": tile, "index": index, "data": data,
            "last": int(n == 255)}


def audit_one(report_path: Path) -> dict:
    report = json.loads(report_path.read_text())
    attempt = report_path.parent
    trace_path = attempt / report["simulation_trace"]["path"]
    packed = trace_path.read_bytes()
    raw = gzip.decompress(packed)
    if sha(packed) != report["simulation_trace"]["gzip_sha256"]:
        raise AssertionError("gzip trace hash differs from run report")
    if sha(raw) != report["simulation_trace"]["raw_sha256"]:
        raise AssertionError("raw trace hash differs from run report")
    if len(raw.splitlines()) != report["simulation_trace"]["rows"]:
        raise AssertionError("trace row count differs from report")

    for rel, expected_hash in report["source_sha256"].items():
        snapshot = attempt / "sources" / rel
        if sha(snapshot.read_bytes()) != expected_hash:
            raise AssertionError(f"source snapshot hash mismatch: {rel}")
    for rel, expected_hash in report["artifacts_sha256"].items():
        artifact = attempt / rel
        if sha(artifact.read_bytes()) != expected_hash:
            raise AssertionError(f"artifact hash mismatch: {rel}")

    events = [json.loads(line) for line in raw.splitlines()]
    samples = [e for e in events if e.get("type") == "sample"]
    directed = [e["name"] for e in events if e.get("type") == "directed"]
    verdict = [e for e in events if e.get("type") == "verdict"]
    if len(samples) != 4096 or len(directed) != 32 or len(verdict) != 1:
        raise AssertionError("expected 4096 output samples, 32 directed cases, one verdict")

    by_profile: dict[int, list[dict]] = {0: [], 1: []}
    for sample in samples:
        by_profile[sample["profile"]].append(sample)
    profile_summary = {}
    for profile, rows in by_profile.items():
        if len(rows) != 2048:
            raise AssertionError(f"profile {profile}: wrong sample count")
        rows.sort(key=lambda e: (e["row"], e["byte"]))
        if [(e["row"], e["byte"]) for e in rows] != [
                (r, b) for r in range(256) for b in range(8)]:
            raise AssertionError(f"profile {profile}: output sample order mismatch")
        epoch = profile + 2
        for row in range(256):
            exp = expected_row(row)
            batch = rows[row * 8:(row + 1) * 8]
            token = 1 + profile * 256 + row
            for byte, event in enumerate(batch):
                expected = {
                    "epoch": epoch, "token": token, "bank": 2,
                    "addr": exp["address"] + byte,
                    "data": exp["data"][byte], "hud": exp["hud"],
                    "fid": 31, "plane": exp["plane"], "tile": exp["tile"],
                    "index": 0 if exp["hud"] else exp["index"] + byte,
                    "last": int(exp["last"] and byte == 7),
                }
                for key, value in expected.items():
                    if event[key] != value:
                        raise AssertionError(
                            f"profile {profile}, row {row}, byte {byte}: "
                            f"{key} expected {value}, got {event[key]}")
            if any(batch[j]["addr"] != batch[0]["addr"] + j for j in range(8)):
                raise AssertionError("sampled row is not contiguous")
            if batch[0]["addr"] % 8:
                raise AssertionError("sampled row is not aligned")
        profile_summary[str(profile)] = {
            "rows": 256, "ordered_bytes": len(rows),
            "independently_recomputed_data_and_address_tuples": True,
            "all_tags_stable_per_row": True,
        }

    required_directed = {
        "cancel_partial_fill", "cancel_unaccepted_offer", "cancel_partial_hash_delivery",
        "cancel_pending_row_ack_drain", "cancel_matching_ack_same_edge",
        "reset_partial_fill", "reset_unaccepted_offer", "reset_partial_hash_delivery",
        "reset_pending_row_ack_drain", "reset_matching_ack_same_edge",
        "wrong_epoch_ack_retains_row", "wrong_token_ack_retains_row",
        "wrong_bank_ack_retains_row", "wrong_addr_ack_retains_row",
        "matching_bus_error_drains_without_hash", "clean_row_retry_after_faults",
        "first_zero_epoch", "first_unaligned_address", "first_unaligned_index",
        "first_invalid_plane", "first_early_last", "fill_epoch_mismatch",
        "fill_fid_mismatch", "fill_bank_mismatch", "fill_plane_mismatch",
        "fill_tile_mismatch", "fill_index_mismatch", "fill_address_mismatch",
        "fill_kind_mismatch", "fill_early_last_mismatch",
    }
    missing = sorted(required_directed - set(directed))
    if missing:
        raise AssertionError(f"directed checks missing: {missing}")
    if verdict[0]["status"] != "TEST_PASS" or verdict[0]["seed"] != report["seed"]:
        raise AssertionError("trace verdict mismatch")

    return {
        "schema": "cu66-v91l-row-independent-audit-v1",
        "status": "PASS",
        "selected_report": str(report_path.relative_to(ROOT)),
        "source_revision": report["source_revision"],
        "seed": report["seed"],
        "trace_sha256": sha(packed),
        "trace_samples": len(samples),
        "directed_checks": len(directed),
        "profiles": profile_summary,
        "checked_directed_protocol_cases": sorted(required_directed),
        "scope": "Independent output/address/tuple and retained-artifact audit of standalone RTL simulation; not full-frame integration or hardware/performance evidence.",
        "limitations": [
            "Stimulus covers 256 generated rows per profile, not the entire canonical/HUD address domain.",
            "The address oracle checks sampled rows from producer tuple formulas; this standalone adapter does not reconstruct gameplay frames or measure SDRAM timing.",
        ],
    }


def main() -> None:
    selected = json.loads(RESULTS.read_text())
    report_paths = sorted((AREA / "row-attempts").glob("*/results.json"))
    audits = [audit_one(path) for path in report_paths]
    if {audit["seed"] for audit in audits} != {912101, 912102}:
        raise AssertionError("expected independent traces for seeds 912101 and 912102")
    if selected["selected_report"] not in {
            audit["selected_report"] for audit in audits}:
        raise AssertionError("row-results.json does not select one audited report")
    result = {
        "schema": "cu66-v91l-row-independent-audit-v1",
        "status": "PASS",
        "audited_seeds": [audit["seed"] for audit in audits],
        "attempts": audits,
        "scope": "Independent output/address/tuple and retained-artifact audit of both standalone RTL simulation seeds; not full-frame integration or hardware/performance evidence.",
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
