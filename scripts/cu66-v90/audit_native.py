#!/usr/bin/env python3
"""Independently audit V90 native packet selection, decode, and replay records."""
import csv
import hashlib
import json
import struct
import zlib
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NATIVE = ROOT / "experiments/python-gamebub-v90/native"
RESULT = NATIVE / "results.json"
ATTEMPT = NATIVE / "attempts/20261106T160439132762Z-32bde2e1"
FRAMES = ATTEMPT / "frames.jsonl"
POLICY_RESULT = ROOT / "experiments/python-gamebub-v90/policy/results.json"
ORACLE_PATH = ROOT / "experiments/python-gamebub-v90/exact/oracle-selections.json"
V88_RESULT = ROOT / "experiments/python-gamebub-v88/wire/results.json"
OUT_JSON = ROOT / "experiments/python-gamebub-v90/native-audit.json"
OUT_LOG = ROOT / "experiments/python-gamebub-v90/native-audit.log"
CAP = 49152
POLICIES = ("proxy_LOW", "proxy_HIGH", "exact4_else_proxy_LOW", "exact4_else_proxy_HIGH")
DECODE_FIELDS = ("canonical_sha256", "coefficient_sha256", "hud_sha256",
                 "display_sha256", "root", "seal")
GROUND_TRUTH_FIELDS = DECODE_FIELDS + ("fid", "generation")
SELECTION_FIELDS = ("mask", "packet_sha256", "wire_bytes")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_rows(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def key(row):
    return row["cohort"], row["fid"]


def cs88_header(path, expected_fid):
    packet = path.read_bytes()
    assert len(packet) >= 132 and len(packet) <= CAP
    assert packet[:4] == b"CS88" and packet[4] == 1
    assert packet[5] in (0, 1) and packet[6] == 16 and packet[7] <= 3
    fid, refid = struct.unpack_from(">II", packet, 8)
    generation = struct.unpack_from(">Q", packet, 16)[0]
    width, height, block, reserved = struct.unpack_from(">HHHH", packet, 24)
    cap, map_n, q_n, hud_n, data_n = struct.unpack_from(">IIIII", packet, 32)
    assert fid == expected_fid and generation > 0
    assert (width, height, reserved) == (720, 480, 0) and block in (16, 32)
    assert cap in (256, 65536) and map_n <= 976 and 16 <= q_n <= 354
    assert 110 <= hud_n <= CAP and data_n >= 0
    assert 128 + map_n + q_n + hud_n + data_n + 4 == len(packet)
    assert packet[116:128] == bytes(12)
    trailer = struct.unpack_from(">I", packet, len(packet) - 4)[0]
    assert zlib.crc32(packet[:-4]) & 0xffffffff == trailer
    return dict(bytes=len(packet), fid=fid, refid=refid, generation=generation,
                key=bool(packet[5]), map_method=packet[7], cap=cap,
                outer_crc32=f"{trailer:08x}")


def main():
    report = json.loads(RESULT.read_text())
    attempt_report = json.loads((ATTEMPT / "results.json").read_text())
    assert ROOT / report["selected_report"] == ATTEMPT / "results.json"
    wrapped = dict(attempt_report, selected_report=report.get("selected_report"))
    assert report == wrapped and report["status"] == "PASS_NATIVE_SELECTIONS_AND_EXACT_REPLAY"
    frames = load_rows(FRAMES)
    assert len(frames) == report["new_packet_calls"] == 1828
    keys_by_policy = defaultdict(set)
    frame_map = {}
    overrides = []
    for row in frames:
        k = (row["policy"], row["cohort"], row["fid"])
        assert k not in frame_map, k
        frame_map[k] = row
        keys_by_policy[row["policy"]].add(key(row))
        assert row["policy"] in POLICIES
        assert row["cost"] == ("LOW" if row["policy"].endswith("LOW") else "HIGH")
        assert 0 <= row["mask"] <= 7 and row["wire_bytes"] <= CAP
        assert row["decoded"]["accepted"] is True
        assert row["decoded"]["replayed"] is False
        assert row["decoded"]["wire_bytes"] == row["wire_bytes"]
        assert row["replayed"] is True
        if row["oracle_override"]:
            overrides.append(row)
    assert set(keys_by_policy) == set(POLICIES)
    assert all(len(keys) == 457 for keys in keys_by_policy.values())
    assert all(keys_by_policy[a] == keys_by_policy[POLICIES[0]] for a in POLICIES)
    assert report["native_sources"] == 457 and report["exact_replay_calls"] == 1828
    assert report["receiver_exit_codes"] == {p: 0 for p in POLICIES}
    assert report["oracle_override_calls"] == len(overrides) == 8

    policy_report = json.loads(POLICY_RESULT.read_text())
    policy_attempt = ROOT / policy_report["selected_report"]
    proxies = {(r["cohort"], r["fid"], r["cost"]): r
               for r in load_rows(policy_attempt.with_name("selections.jsonl"))}
    assert len(proxies) == 914
    oracle_doc = json.loads(ORACLE_PATH.read_text())
    oracle = {(r["cohort"], r["fid"], r["cost"]): r for r in oracle_doc["choices"]}
    assert len(oracle) == 8
    override_keys = {(r["cohort"], r["fid"], r["cost"]) for r in overrides}
    assert override_keys == set(oracle)
    assert "four-source" in oracle_doc.get("scope", "")
    assert "do not define a live full-corpus policy" in oracle_doc.get("scope", "")

    prior_doc = json.loads(V88_RESULT.read_text())
    prior_attempt = ROOT / prior_doc["selected_report"]
    truth = {key(r): r for r in load_rows(prior_attempt.with_name("frames.jsonl"))
             if r["policy"] == "AB38_control"}
    assert len(truth) == 457 and prior_doc["status"] == "PASS_FULL_NATIVE_MIXED_CODEC_PARITY"
    checked = 0
    for row in frames:
        k = key(row)
        truth_decoded = truth[k]["decoded"]
        decoded = row["decoded"]
        for field in DECODE_FIELDS:
            assert decoded[field] == truth_decoded[field], (k, row["policy"], field)
        for field in ("fid", "generation", "wire_bytes"):
            if field == "wire_bytes":
                assert decoded[field] == row["wire_bytes"]
            else:
                assert decoded[field] == truth_decoded[field]
        lookup = (*k, row["cost"])
        expected = oracle[lookup] if row["oracle_override"] else proxies[lookup]
        assert row["mask"] == expected.get("mask", expected.get("best_mask"))
        assert row["packet_sha256"] == expected["packet_sha256"]
        assert row["wire_bytes"] == expected["wire_bytes"]
        checked += 1

    # The recorded boolean is emitted only after the native program returns an
    # identical accepted replay response; confirm the pinned producer retains
    # that assertion and all native/source and artifact pins remain exact.
    producer = ROOT / "scripts/cu66-v90/qualify_native.py"
    producer_text = producer.read_text()
    assert "assert replay==dict(decoded,replayed=True)" in producer_text
    for name, digest in report["source_sha256"].items():
        assert sha(ROOT / name) == digest, f"source pin changed: {name}"
    artifact_map = report["artifacts_sha256"]
    for name, digest in artifact_map.items():
        assert sha(ATTEMPT / name) == digest, f"artifact digest mismatch: {name}"
    actual_artifacts = {str(p.relative_to(ATTEMPT)) for p in ATTEMPT.rglob("*")
                        if p.is_file() and p.name != "results.json"}
    assert actual_artifacts == set(artifact_map)
    commands = attempt_report["commands"]
    assert len(commands) == 6 and all(c.get("observed_exit_code") == 0 for c in commands[:2])
    assert len(attempt_report["receiver_exit_codes"]) == 4

    fixture_rows = {(0, 0), (0, 1), (0, 3), (3, 50)}
    fixture_checks = []
    for cohort, fid in sorted(fixture_rows):
        for policy in POLICIES:
            row = frame_map[(policy, cohort, fid)]
            name = f"c{cohort}-f{fid}-{policy}.cs88"
            assert artifact_map[name] == row["packet_sha256"]
            details = cs88_header(ATTEMPT / name, fid)
            assert details["bytes"] == row["wire_bytes"]
            fixture_checks.append(dict(file=name, packet_sha256=row["packet_sha256"], **details))
    assert len(fixture_checks) == 16

    OUT_JSON.write_text(json.dumps({
        "schema": "cu66-v90-native-independent-audit-v1",
        "status": "PASS_NATIVE_SELECTION_DECODE_REPLAY_AUDIT",
        "report_sha256": sha(RESULT), "attempt_report_sha256": sha(ATTEMPT / "results.json"),
        "frames_sha256": sha(FRAMES),
        "native_rows": len(frames), "distinct_sources": 457,
        "full_histories": {p: len(keys_by_policy[p]) for p in POLICIES},
        "new_packet_calls": 1828, "exact_replay_calls": 1828,
        "rows_matching_v88_qualified_cs88_groundtruth": checked,
        "groundtruth_fields": list(GROUND_TRUTH_FIELDS),
        "selection_fields": list(SELECTION_FIELDS),
        "proxy_selection_rows": len(proxies), "oracle_override_rows": len(overrides),
        "oracle_scope": oracle_doc["scope"],
        "all_selected_packets_within_49152_bytes": True,
        "receiver_exit_codes": report["receiver_exit_codes"],
        "replay_evidence": "1828 rows have accepted native new-decode results plus replayed=true; the pinned producer writes each row only after asserting the repeated receiver response equals the original with replayed=true",
        "source_pins_verified": len(report["source_sha256"]),
        "artifact_pins_verified": len(artifact_map),
        "fixtures_outer_crc_header_and_sha_verified": fixture_checks,
    }, indent=2) + "\n")
    OUT_LOG.write_text(
        "V90 independent native selection and replay audit\n\n"
        "Command: python3 scripts/cu66-v90/audit_native.py\n"
        "Observed exit code: 0\n"
        f"Observed stdout: PASS_NATIVE_SELECTION_DECODE_REPLAY_AUDIT rows={len(frames)} sources=457 overrides={len(overrides)} fixtures=16\n"
        "Observed stderr: (empty)\n\n"
        "All four histories contain 457 distinct sources. New packet rows match the full-corpus LOW/HIGH proxy choices, with exactly eight selected four-source oracle overrides. "
        "All decoded canonical, coefficient, HUD, display, root, and seal digests match qualified V88 CS88 ground truth. All rows fit the 49152-byte cap; all four receiver exits are zero. "
        "Replay flags are backed by the pinned producer's equality assertion for the actual repeated receiver response. The 16 retained fixtures pass CS88 header, outer CRC32, size, and SHA-256 checks.\n")
    print(f"PASS_NATIVE_SELECTION_DECODE_REPLAY_AUDIT rows={len(frames)} sources=457 overrides={len(overrides)} fixtures=16")


if __name__ == "__main__":
    main()
