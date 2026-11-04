#!/usr/bin/env python3
"""Independent v21 source, replay-log and byte-accounting audit."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
REPO = HERE.parents[1]
DELTA = EXP / "python-game-hud-delta-study"
CACHE = EXP / "python-game-hud-cache-study"
COMPOSE = EXP / "python-game-display-compose-study"
OLD = EXP / "python-game-mandatory-hud-study"
FRAME_CAP = 49152
CB21_OVERHEAD = 57
HA21_BYTES = 54
IPV4_UDP_BYTES = 28
FRAGMENT_PAYLOAD = 1008
FRAGMENT_OVERHEAD = 31 + 16 + IPV4_UDP_BYTES
PC18_OVERHEAD = 29 + IPV4_UDP_BYTES
FG19_OVERHEAD = 36 + IPV4_UDP_BYTES
AF03_OVERHEAD = 43 + IPV4_UDP_BYTES


def sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text())


def assert_pins(folder: Path, base: Path, pins: dict[str, str]):
    for raw, expected in pins.items():
        path = (base / raw).resolve()
        if not path.is_file() or sha_file(path) != expected:
            raise AssertionError(f"source pin mismatch: {folder.name}:{raw}")


def parse_test_log(path: Path, expected: int) -> int:
    text = path.read_text()
    match = re.search(r"^Ran (\d+) tests? in ", text, re.M)
    if not match or int(match.group(1)) != expected or not text.rstrip().endswith("OK"):
        raise AssertionError(f"test log mismatch: {path}")
    return int(match.group(1))


def parse_verify_log(path: Path) -> dict:
    data = json.loads(path.read_text())
    if data.get("physical_30fps_proven") is not False:
        raise AssertionError(f"unsupported throughput claim in {path}")
    return data


def close(a, b, tol=1e-9):
    return math.isclose(float(a), float(b), rel_tol=tol, abs_tol=tol)


def transport(body_bytes: int, hud_ack: bool):
    fragments = math.ceil(body_bytes / FRAGMENT_PAYLOAD)
    return {
        "body_bytes": body_bytes,
        "fragments": fragments,
        "data_forward_bytes": body_bytes + fragments * FRAGMENT_OVERHEAD,
        "frame_forward_control_bytes": 2 * FG19_OVERHEAD,
        "frame_reverse_control_bytes": 3 * FG19_OVERHEAD,
        "packet_credit_reverse_bytes": fragments * PC18_OVERHEAD,
        "reference_ack_reverse_bytes": AF03_OVERHEAD,
        "hud_ack_reverse_bytes": HA21_BYTES + IPV4_UDP_BYTES if hud_ack else 0,
    }


def add_transport(rows, key):
    forward = sum(r[key]["data_forward_bytes"] + r[key]["frame_forward_control_bytes"] for r in rows)
    reverse_keys = ("frame_reverse_control_bytes", "packet_credit_reverse_bytes",
                    "reference_ack_reverse_bytes", "hud_ack_reverse_bytes")
    reverse = sum(sum(r[key][k] for k in reverse_keys) for r in rows)
    n = len(rows)
    return {
        "forward_ipv4_udp_bytes": forward,
        "reverse_ipv4_udp_bytes": reverse,
        "forward_Mbps_at30": forward / n * 30 * 8 / 1e6,
        "reverse_Mbps_at30": reverse / n * 30 * 8 / 1e6,
    }


def build_audit():
    delta = read_json(DELTA / "results.json")
    cache = read_json(CACHE / "results.json")
    compose = read_json(COMPOSE / "results.json")
    old = read_json(OLD / "results.json")
    if delta.get("schema") != "gamebub-hud-delta-v21-1":
        raise AssertionError("unexpected HD21 result schema")
    if cache.get("schema") != "gamebub-hud-cache-v21":
        raise AssertionError("unexpected HC21 result schema")
    if compose.get("schema") != "gamebub-display-compose-v21":
        raise AssertionError("unexpected CB21 result schema")

    assert_pins(DELTA, DELTA, delta["source_sha256"])
    assert_pins(CACHE, REPO, cache["source_sha256"])
    assert_pins(COMPOSE, REPO, compose["source_sha256"])

    delta_log = parse_verify_log(DELTA / "verify.log")
    cache_log = parse_verify_log(CACHE / "verify.log")
    compose_log = parse_verify_log(COMPOSE / "verify.log")
    delta_tests = parse_test_log(DELTA / "tests.log", 14)
    cache_tests = parse_test_log(CACHE / "tests.log", 15)
    compose_tests = parse_test_log(COMPOSE / "tests.log", 7)

    # Independent expected values for retained HD21 component controls.
    if (delta_log.get("vectors"), delta_log.get("independent_scalar_words"),
            delta_log.get("crc_negatives"), delta_log.get("complete_packet_bytes")) != (6, 36481, 6, 57932):
        raise AssertionError("HD21 independent replay totals changed")
    if delta.get("summary") != {"vectors": 6, "roundtrip_words": 36481, "complete_packet_bytes": 57932}:
        raise AssertionError("HD21 summary arithmetic mismatch")

    if (cache_log.get("decisions"), cache_log.get("exact_words"),
            cache_log.get("atomic_crc_negative_rejections")) != (132, 2787840, 132):
        raise AssertionError("HC21 sequence replay totals changed")
    if cache.get("counts") != {"native_frames": 96, "synthetic_frames": 36, "decisions": 132}:
        raise AssertionError("HC21 case counts mismatch")
    if (cache.get("header_bytes"), cache.get("crc_bytes"), cache.get("ack_bytes")) != (79, 4, 54):
        raise AssertionError("HC21 header/ACK fixed byte sizes mismatch")

    old_cases = {c["scene"]: c for c in old["cases"] if c["policy"] == "mandatory"}
    cache_cases = {c["name"]: c for c in cache["cases"]}
    composed = {c["scene"]: c for c in compose["budgets"]}
    budgets = []
    native_rows_checked = 0
    for scene in ("mass-effect-2600", "mass-effect-7200"):
        oc, cc, bc = old_cases[scene], cache_cases[scene], composed[scene]
        if not (len(oc["rows"]) == len(cc["rows"]) == len(bc["rows"]) == 48):
            raise AssertionError(f"expected 48 matched native rows for {scene}")
        rows = []
        for old_row, cache_row, budget_row in zip(oc["rows"], cc["rows"], bc["rows"]):
            frame = old_row["id"]
            if cache_row["frame"] != frame or budget_row["id"] != frame:
                raise AssertionError(f"frame identity mismatch: {scene}:{frame}")
            if cache_row["source_sha256"] != old_row["input_sha256"]:
                raise AssertionError(f"native source hash mismatch: {scene}:{frame}")
            if cache_row["source_sha256"] != cache_row["v20_input_sha256"]:
                raise AssertionError(f"HC21 pinned source mismatch: {scene}:{frame}")
            if cache_row["legacy_patch_bytes"] != old_row["patch_bytes"]:
                raise AssertionError(f"legacy patch-section bytes mismatch: {scene}:{frame}")
            original = old_row["packet_bytes"]
            sidecar = cache_row["sidecar_bytes"]
            complete = original - old_row["patch_bytes"] + sidecar + CB21_OVERHEAD
            if cache_row["accounting_only_replaced_total"] != original - old_row["patch_bytes"] + sidecar:
                raise AssertionError(f"HC21 accounting-only bytes mismatch: {scene}:{frame}")
            if complete != budget_row["cb21_complete_bytes"] or complete != budget_row["unchanged_base_bytes"] + sidecar + CB21_OVERHEAD:
                raise AssertionError(f"CB21 complete bytes mismatch: {scene}:{frame}")
            cap = complete <= FRAME_CAP
            if budget_row["complete_cap_fits"] is not cap or (complete > FRAME_CAP) != (not budget_row["complete_cap_fits"]):
                raise AssertionError(f"CB21 cap outcome mismatch: {scene}:{frame}")
            if len(cache_row["packet"]) == 0 or cache_row["ack_bytes"] != HA21_BYTES:
                raise AssertionError(f"missing retained HC21/HA21 size: {scene}:{frame}")

            legacy_counts = transport(original, False)
            new_counts = transport(complete, True)
            if budget_row["legacy_transport"] != legacy_counts or budget_row["proposed_transport"] != new_counts:
                raise AssertionError(f"transport packet/ACK bytes mismatch: {scene}:{frame}")
            # Independently check optimistic rate/delay arithmetic, without calling CB21 code.
            sweep = budget_row["network_bound_sweep"]
            if len(sweep) != 25:
                raise AssertionError(f"rate-bound sweep shape mismatch: {scene}:{frame}")
            for bound in sweep:
                fwd = new_counts["data_forward_bytes"] + new_counts["frame_forward_control_bytes"]
                rev = sum(new_counts[k] for k in ("frame_reverse_control_bytes", "packet_credit_reverse_bytes",
                                                   "reference_ack_reverse_bytes", "hud_ack_reverse_bytes"))
                fwd_ms = 8 * fwd / (bound["link_mbps"] * 1000)
                rev_ms = 8 * rev / (bound["link_mbps"] * 1000)
                stopwait = max(fwd_ms, rev_ms) + bound["feedback_delay_ms"]
                if not (close(bound["forward_serialization_ms"], fwd_ms)
                        and close(bound["reverse_serialization_ms"], rev_ms)
                        and close(bound["network_only_stop_wait_ms"], stopwait)
                        and close(bound["optimistic_network_only_fps_ceiling"], 1000 / stopwait)
                        and bound["necessary_30fps_condition"] is (stopwait <= 1000 / 30)):
                    raise AssertionError(f"network bound arithmetic mismatch: {scene}:{frame}")

            rows.append({"id": frame, "original_complete_bytes": original,
                         "cb21_complete_bytes": complete, "complete_cap_fits": cap,
                         "legacy_transport": legacy_counts, "proposed_transport": new_counts})
            native_rows_checked += 1

        old_total = sum(r["original_complete_bytes"] for r in rows)
        new_total = sum(r["cb21_complete_bytes"] for r in rows)
        fitted = sum(r["complete_cap_fits"] for r in rows)
        expected = {
            "scene": scene, "frames": 48, "original_complete_bytes": old_total,
            "cb21_complete_bytes": new_total,
            "complete_saving_percent": 100 * (old_total - new_total) / old_total,
            "complete_cap_fits": fitted,
            "maximum_complete_bytes": max(r["cb21_complete_bytes"] for r in rows),
            "minimum_complete_bytes": min(r["cb21_complete_bytes"] for r in rows),
            "transport": {"legacy_transport": add_transport(rows, "legacy_transport"),
                          "proposed_transport": add_transport(rows, "proposed_transport")},
        }
        for k, v in expected.items():
            actual = bc[k]
            if isinstance(v, float):
                if not close(actual, v): raise AssertionError(f"summary mismatch: {scene}:{k}")
            elif isinstance(v, dict) and k == "transport":
                for name in v:
                    for stat, val in v[name].items():
                        if not close(actual[name][stat], val):
                            raise AssertionError(f"transport summary mismatch: {scene}:{name}:{stat}")
            elif actual != v:
                raise AssertionError(f"summary mismatch: {scene}:{k}")
        budgets.append(expected)

    # Ten offline pair goldens independently preserve original YUV and exact full display.
    if (compose_log.get("golden_pairs"), compose_log.get("full_display_exact_words"),
            compose_log.get("unchanged_yuv_samples"), compose_log.get("repaired_outer_crc_negatives"),
            compose_log.get("admitted_golden_pairs_under_cap"), compose_log.get("native_budget_decisions")) != (
            10, 3456000, 5184000, 10, 10, 96):
        raise AssertionError("CB21 display/YUV replay totals changed")
    if compose.get("exact_display_words") != 3456000 or compose.get("exact_yuv_samples") != 5184000:
        raise AssertionError("CB21 replay totals mismatch")
    if compose_log.get("joint_publication_implemented") is not False:
        raise AssertionError("offline fixture overstates joint publication")

    # Keep the noise-regression fixture visible: exact cache coding is not always smaller.
    noise = next(c for c in cache["cases"] if c["name"] == "synthetic-noise")
    if len(noise["rows"]) != 12 or noise["summary"]["patch_forward_saving_fraction"] >= 0:
        raise AssertionError("synthetic noise overhead regression missing")

    return {
        "status": "verified",
        "source_pins_verified": {"HD21": len(delta["source_sha256"]),
                                  "HC21": len(cache["source_sha256"]),
                                  "CB21": len(compose["source_sha256"])},
        "tests_recorded": {"HD21": delta_tests, "HC21": cache_tests, "CB21": compose_tests},
        "component_replay": {
            "HD21_vectors": delta_log["vectors"],
            "HD21_exact_words": delta_log["independent_scalar_words"],
            "HC21_decisions": cache_log["decisions"],
            "HC21_exact_hud_words": cache_log["exact_words"],
            "HC21_atomic_crc_negatives": cache_log["atomic_crc_negative_rejections"],
            "CB21_golden_pairs": compose_log["golden_pairs"],
            "CB21_full_display_words": compose_log["full_display_exact_words"],
            "preserved_yuv_samples": compose_log["unchanged_yuv_samples"],
        },
        "native_budget_rows_recomputed": native_rows_checked,
        "native_scenes": budgets,
        "synthetic_noise_complete_patch_forward_saving_fraction": noise["summary"]["patch_forward_saving_fraction"],
        "cache_pixel_storage_model_bytes": cache["cases"][0]["summary"]["receiver_two_banks_plus_atomic_stage_bytes"],
        "CB21_overhead_bytes": CB21_OVERHEAD,
        "HA21_ack_bytes": HA21_BYTES,
        "ipv4_udp_overhead_per_control": IPV4_UDP_BYTES,
        "frame_cap_bytes": FRAME_CAP,
        "joint_base_hud_publication_implemented": False,
        "hardware_rtl_resource_fit_or_physical_30fps_proven": False,
        "rate_calculation_scope": "offline arithmetic only; no RF, target service, or live cadence claim",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="recompute and compare retained audit.json")
    args = parser.parse_args()
    result = build_audit()
    path = HERE / "audit.json"
    if args.check:
        if not path.is_file() or read_json(path) != result:
            raise SystemExit("audit.json does not match independent recomputation")
        print(json.dumps({"status": "verified", "audit": "audit.json"}, indent=2))
    else:
        path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
