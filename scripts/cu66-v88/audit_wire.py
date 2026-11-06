#!/usr/bin/env python3
"""Independently audit CS88 policy choices, accounting, pins, and parity."""
import hashlib
import json
from pathlib import Path
import zlib

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / "experiments/python-gamebub-v88/wire"
POLICIES = ("AB38_control", "byte_min", "feedback_overhead5",
            "feedback_overhead15", "all_BR88")
PARITY_KEYS = ("canonical_sha256", "hud_sha256", "display_sha256",
               "coefficient_sha256", "root", "seal", "generation", "fid")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    return sha(path.read_bytes())


def selected(candidates, policy):
    if policy == "AB38_control":
        return next(row for row in candidates if row["mask"] == 0)
    if policy == "all_BR88":
        return max(candidates, key=lambda row: row["mask"])
    if policy == "byte_min":
        return min(candidates, key=lambda row: (row["wire_bytes"],
                                                row["remaining_decisions"], row["mask"]))
    baseline = next(row for row in candidates if row["mask"] == 0)
    percent = 105 if policy == "feedback_overhead5" else 115
    budget = min(49152, baseline["wire_bytes"] * percent // 100)
    feasible = [row for row in candidates if row["wire_bytes"] <= budget]
    if not feasible:
        raise ValueError(f"{policy}: no candidate fits budget")
    return min(feasible, key=lambda row: (row["remaining_decisions"],
                                         row["wire_bytes"], row["mask"]))


def verify_fixture(path, expected_sha):
    packet = path.read_bytes()
    if sha(packet) != expected_sha:
        raise ValueError(f"fixture SHA mismatch: {path.name}")
    if len(packet) < 132 or packet[:4] != b"CS88":
        raise ValueError(f"bad CS88 fixture: {path.name}")
    if zlib.crc32(packet[:-4]) != int.from_bytes(packet[-4:], "big"):
        raise ValueError(f"outer CRC mismatch: {path.name}")
    map_bytes = int.from_bytes(packet[36:40], "big")
    q_bytes = int.from_bytes(packet[40:44], "big")
    hud_bytes = int.from_bytes(packet[44:48], "big")
    data_bytes = int.from_bytes(packet[48:52], "big")
    if 128 + map_bytes + q_bytes + hud_bytes + data_bytes + 4 != len(packet):
        raise ValueError(f"component lengths mismatch: {path.name}")
    qmap_at = 128 + map_bytes
    qmap = packet[qmap_at:qmap_at + q_bytes]
    if len(qmap) < 16 or qmap[:4] != b"QM87":
        raise ValueError(f"bad QM87 fixture section: {path.name}")
    if zlib.crc32(qmap[:-4]) != int.from_bytes(qmap[-4:], "big"):
        raise ValueError(f"QM87 CRC mismatch: {path.name}")
    residual_at = qmap_at + q_bytes
    residual = packet[residual_at:residual_at + data_bytes]
    at = 0
    for _axis in range(3):
        if at + 4 > len(residual):
            raise ValueError(f"truncated chunk directory: {path.name}")
        count = int.from_bytes(residual[at:at + 4], "big"); at += 4
        for _ in range(count):
            if at + 8 > len(residual):
                raise ValueError(f"truncated chunk header: {path.name}")
            length = int.from_bytes(residual[at + 4:at + 8], "big"); at += 8
            chunk = residual[at:at + length]; at += length
            if len(chunk) != length or length < 4:
                raise ValueError(f"truncated chunk payload: {path.name}")
            if chunk[:4] in (b"AB38", b"BR88"):
                if length < 8:
                    raise ValueError(f"short chunk payload: {path.name}")
                actual = zlib.crc32(chunk[:-4])
                stored = int.from_bytes(chunk[-4:], "little")
                if actual != stored:
                    raise ValueError(f"inner {chunk[:4].decode()} CRC mismatch: {path.name}")
            else:
                raise ValueError(f"unknown chunk profile: {path.name}")
    if at != len(residual):
        raise ValueError(f"residual directory length mismatch: {path.name}")


def main():
    selected_path = AREA / "results.json"
    selected_report = json.loads(selected_path.read_text(encoding="utf-8"))
    attempt_path = ROOT / selected_report["selected_report"]
    attempt = json.loads(attempt_path.read_text(encoding="utf-8"))
    attempt_dir = attempt_path.parent
    if attempt.get("status") != "PASS_FULL_NATIVE_MIXED_CODEC_PARITY":
        raise ValueError("selected wire attempt is not a full PASS")
    if attempt["native_sources"] != 457 or attempt["received_packets"] != 457 * len(POLICIES):
        raise ValueError("selected wire attempt source/packet count mismatch")
    if selected_report.get("selected_report") != str(attempt_path.relative_to(ROOT)):
        raise ValueError("selected report path mismatch")
    if any(selected_report.get(k) != v for k, v in attempt.items()):
        raise ValueError("selected summary differs from retained attempt")
    for name, expected in attempt["source_sha256"].items():
        path = ROOT / name
        if not path.is_file() or file_sha(path) != expected:
            raise ValueError(f"source pin mismatch: {name}")
    for name, expected in attempt["artifacts_sha256"].items():
        path = attempt_dir / name
        if not path.is_file() or file_sha(path) != expected:
            raise ValueError(f"attempt artifact pin mismatch: {name}")

    candidate_rows = [json.loads(line) for line in (attempt_dir / "candidates.jsonl").read_text().splitlines()]
    frame_rows = [json.loads(line) for line in (attempt_dir / "frames.jsonl").read_text().splitlines()]
    candidate_groups = {}
    for row in candidate_rows:
        candidate_groups.setdefault((row["cohort"], row["fid"]), []).append(row)
        if sum(row["components"].values()) != row["wire_bytes"]:
            raise ValueError("candidate component accounting mismatch")
    if len(candidate_groups) != 457 or any(len(rows) != 8 for rows in candidate_groups.values()):
        raise ValueError("expected 457 sources with eight candidates each")
    if len(frame_rows) != 457 * len(POLICIES):
        raise ValueError("selected policy row count mismatch")

    v87 = json.loads((ROOT / "experiments/python-gamebub-v87/quantizers/results.json").read_text())
    qualified = ROOT / v87["selected_report"]
    baseline = {}
    for line in qualified.with_name("frames.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row["configuration"] == "copy_group_cap65536":
            baseline[(row["cohort"], row["fid"])] = row
    if len(baseline) != 457:
        raise ValueError("qualified V87 baseline frame count mismatch")

    summaries = {row["policy"]: row for row in attempt["summaries"]}
    audit_summaries = {}
    for policy in POLICIES:
        rows = [row for row in frame_rows if row["policy"] == policy]
        if len(rows) != 457:
            raise ValueError(f"{policy}: expected 457 selected rows")
        byte_values = []; remaining = br_bits = br_chunks = remaining_renorm = 0
        fits = 0; source_component_sums = {}
        for row in rows:
            ident = (row["cohort"], row["fid"])
            options = candidate_groups[ident]
            chosen = selected(options, policy)
            for key in ("mask", "wire_bytes", "components", "packet_sha256", "remaining_decisions",
                        "remaining_renorm", "BR88_bits", "BR88_chunks", "BR88_rice_values", "BR88_events"):
                if row[key] != chosen[key]:
                    raise ValueError(f"{policy} {ident}: selected {key} violates policy argmin")
            if row["wire_bytes"] != row["decoded"]["wire_bytes"]:
                raise ValueError(f"{policy} {ident}: receiver packet length mismatch")
            base = baseline[ident]
            if row["CS87_wire_bytes"] != base["wire_bytes"] or row["packet_sha256"] != row["decoded"].get("packet_sha256", row["packet_sha256"]):
                raise ValueError(f"{policy} {ident}: CS87 byte baseline mismatch")
            for key in PARITY_KEYS:
                if row["decoded"].get(key) != base["decoded"].get(key):
                    raise ValueError(f"{policy} {ident}: qualified V87 parity mismatch at {key}")
            if row["remaining_decisions"] + row["BR88_bits"] != row["CS87_decisions"]:
                raise ValueError(f"{policy} {ident}: adaptive decision / BR88 bit accounting mismatch")
            byte_values.append(row["wire_bytes"])
            remaining += row["remaining_decisions"]
            remaining_renorm += row["remaining_renorm"]
            br_bits += row["BR88_bits"]
            br_chunks += row["BR88_chunks"]
            fits += int(row["fits_49152"])
            for key, value in row["components"].items():
                source_component_sums[key] = source_component_sums.get(key, 0) + value
        summary = summaries[policy]
        computed = {
            "sources": len(rows), "wire_total": sum(byte_values), "wire_min": min(byte_values),
            "wire_max": max(byte_values), "wire_median": sorted(byte_values)[228],
            "wire_delta_vs_CS87": sum(r["wire_bytes"] - r["CS87_wire_bytes"] for r in rows),
            "remaining_adaptive_decisions": remaining, "remaining_renorm": remaining_renorm,
            "BR88_bits": br_bits, "BR88_chunks": br_chunks, "fits_49152": fits,
            "component_totals": source_component_sums,
        }
        expected = {
            "sources": summary["sources"], "wire_total": summary["wire_bytes"]["total"],
            "wire_min": summary["wire_bytes"]["min"], "wire_max": summary["wire_bytes"]["max"],
            "wire_median": summary["wire_bytes"]["median"],
            "wire_delta_vs_CS87": summary["wire_delta_vs_CS87"],
            "remaining_adaptive_decisions": summary["remaining_adaptive_decisions"],
            "remaining_renorm": summary["remaining_renorm"], "BR88_bits": summary["BR88_bits"],
            "BR88_chunks": summary["BR88_chunks"], "fits_49152": summary["fits_49152"],
        }
        if any(computed[k] != v for k, v in expected.items()):
            raise ValueError(f"{policy}: independently recomputed summary differs")
        audit_summaries[policy] = computed

    frame_lookup = {(row["cohort"], row["fid"], row["policy"]): row for row in frame_rows}
    fixture_count = 0
    for path in sorted(attempt_dir.glob("*.cs88")):
        verify_fixture(path, attempt["artifacts_sha256"][path.name])
        stem = path.stem
        pieces = stem.split("-")
        cohort, fid, policy = int(pieces[0][1:]), int(pieces[1][1:]), "-".join(pieces[2:])
        row = frame_lookup[(cohort, fid, policy)]
        packet = path.read_bytes()
        if sha(packet) != row["packet_sha256"] or len(packet) != row["wire_bytes"]:
            raise ValueError(f"fixture does not match selected row: {path.name}")
        fixture_count += 1
    if fixture_count != 35:
        raise ValueError(f"expected 35 selected packet fixtures, got {fixture_count}")
    audit = {
        "schema": "cu66-v88-independent-wire-accounting-v1",
        "status": "PASS",
        "command": "python3 scripts/cu66-v88/audit_wire.py",
        "observed_exit_code": 0,
        "attempt_report": str(attempt_path.relative_to(ROOT)),
        "counts": {"sources": 457, "candidates": len(candidate_rows),
                   "selected_packets": len(frame_rows), "fixtures": fixture_count},
        "policy_totals": audit_summaries,
        "checks": [
            "Source and attempt artifact SHA-256 pins matched.",
            "All 3,656 candidate component sums equaled their complete packet byte counts.",
            "All 2,285 selected rows matched an independently recomputed policy argmin and tie break.",
            "Policy packet bytes, residual adaptive decisions, renormalizations, BR88 bit reads and chunks, and 49,152-byte fit counts were recomputed.",
            "Every selected packet retained V87 qualified canonical, HUD, display, coefficient, root, seal, generation, and frame identity parity.",
            "All 35 retained packet fixtures matched their selected row SHA and length and passed CS88 outer, QM87, and every AB38/BR88 chunk CRC check."
        ],
        "scope": "Independent policy-selection, component accounting, integrity, and selected-fixture checks. Timing remains outside this report."
    }
    (AREA.parent / "wire-audit.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print("V88_WIRE_ACCOUNTING_PASS sources=457 candidates=3656 selected_packets=2285 fixtures=35 " +
          " ".join(f"{name}:{audit_summaries[name]['wire_total']}B/{audit_summaries[name]['BR88_bits']}bits"
                   for name in POLICIES))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, IndexError) as exc:
        raise SystemExit(f"V88_WIRE_ACCOUNTING_FAIL {exc}")
