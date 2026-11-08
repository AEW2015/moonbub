#!/usr/bin/env python3
"""Summarize derived phase intervals from one validated structured NETWORK-RESULT.json.

This parser does not read USB/serial data and does not validate DY45 CRCs. It requires
an existing validated receipt in the input and preserves one run/session per output.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path

KV = re.compile(r"(?:^|\s)([A-Za-z_][A-Za-z0-9_]*)=([^\s]+)")
FRAME_TAGS = {
    "frame": "frame", "ingress": "ingress", "request": "request",
    "hu_ingress_span": "hu", "hu_scalar_fetch": "hu",
    "native": "native", "hud": "hud", "final": "final",
}

class InputError(ValueError):
    pass


def parse_line(line: str):
    head, sep, rest = line.partition(" ")
    if not sep or head not in FRAME_TAGS:
        return None
    values = {k: v for k, v in KV.findall(" " + rest)}
    # The success export also contains diagnostic lines beginning with the word
    # "native" that are not per-frame stage rows.
    if "ordinal" not in values:
        return None
    try:
        values["ordinal"] = int(values["ordinal"])
    except ValueError as exc:
        raise InputError("invalid_ordinal") from exc
    values["_tag"] = head
    return FRAME_TAGS[head], values


def number(row, key):
    if row is None:
        return None
    value = row.get(key)
    if value is None:
        return None
    try:
        n = int(value)
    except (ValueError, TypeError):
        return None
    return n if n >= 0 else None


def interval(name, start_row, start_key, end_row, end_key, unit="us"):
    if start_row is None or end_row is None:
        return {"name": name, "value": None, "unit": unit, "status": "unknown", "reason": "missing_stage"}
    a, b = number(start_row, start_key), number(end_row, end_key)
    if a is None or b is None:
        return {"name": name, "value": None, "unit": unit, "status": "unknown", "reason": "missing_invalid_or_negative_timestamp"}
    if b < a:
        return {"name": name, "value": None, "unit": unit, "status": "unknown", "reason": "negative_interval"}
    return {"name": name, "value": b - a, "unit": unit, "status": "known"}


def summarize_doc(doc, path: Path, input_sha: str):
    if not isinstance(doc, dict):
        raise InputError("network_result_must_be_object")
    # This receipt is supplied by the pre-existing validator; this tool does not
    # re-implement its CRC or capture checks.
    usb = doc.get("USB") or {}
    scope = doc.get("evidence_kind")
    if scope is None:
        if doc.get("result") != "PASS_LOCAL_BOUNDED12_HARDWARE":
            raise InputError("unrecognized_evidence_scope")
        scope = "physical"
    if scope not in ("physical", "model"):
        raise InputError("unrecognized_evidence_scope")
    if doc.get("result") != "PASS_LOCAL_BOUNDED12_HARDWARE" or usb.get("both_independently_validated") is not True:
        raise InputError("validated_physical_receipt_required")
    if not re.fullmatch(r"[0-9a-fA-F]{8}", str(usb.get("checksum", ""))):
        raise InputError("validated_export_checksum_receipt_missing")
    if usb.get("export1_records") != usb.get("export2_records"):
        raise InputError("independent_export_record_counts_disagree")
    session = doc.get("session") or {}
    manifest = session.get("manifest_sha256")
    identity = {
        "execution_scope": scope,
        "result": doc.get("result"),
        "elf_sha256": doc.get("ELF"),
        "fpga_bit_sha256": (doc.get("FPGA") or {}).get("BIT_SHA256"),
        "manifest_sha256": manifest,
        "session_id": session.get("session"),
        "source": session.get("source"),
        "destination": session.get("destination"),
        "sequence_count": session.get("sequence_count"),
    }
    required = ("elf_sha256", "fpga_bit_sha256", "manifest_sha256")
    if any(not isinstance(identity[k], str) or not re.fullmatch(r"[0-9a-fA-F]{64}", identity[k]) for k in required):
        raise InputError("source_and_session_identity_required")
    if not isinstance(identity["session_id"], int) or identity["session_id"] <= 0:
        raise InputError("source_and_session_identity_required")
    if identity["sequence_count"] != 12:
        raise InputError("expected_twelve_frame_sequence")
    rows = doc.get("raw_rows")
    if not isinstance(rows, dict):
        raise InputError("structured_raw_rows_required")
    try:
        indexed = sorted((int(k), v) for k, v in rows.items())
    except (TypeError, ValueError) as exc:
        raise InputError("invalid_raw_row_index") from exc
    if not indexed or [i for i, _ in indexed] != list(range(len(indexed))):
        raise InputError("truncated_or_noncontiguous_export_rows")
    if len(indexed) != usb.get("export2_records"):
        raise InputError("raw_rows_do_not_match_validated_export_count")

    parsed = {}
    for _, line in indexed:
        item = parse_line(line)
        if item is None:
            continue
        kind, values = item
        ordinal = values["ordinal"]
        bucket = parsed.setdefault(ordinal, {})
        if kind in bucket:
            raise InputError(f"duplicate_ordinal_stage:{ordinal}:{kind}")
        bucket[kind] = values
    ring = next((v for _, v in indexed if isinstance(v, str) and v.startswith("ring ")), None)
    ringkv = {k: v for k, v in KV.findall(" " + (ring or ""))}
    try:
        first, retained = int(ringkv["first"]), int(ringkv["retained"])
    except (KeyError, ValueError) as exc:
        raise InputError("ring_identity_required") from exc
    expected_ordinals = list(range(first, first + retained))
    if sorted(parsed) != expected_ordinals:
        raise InputError("ring_ordinals_missing_or_unexpected")

    summaries = []
    for ordinal in expected_ordinals:
        p = parsed[ordinal]
        def get(kind): return p.get(kind)
        native = interval("native_wall_us", get("native"), "start", get("native"), "done")
        cpu = number(get("native"), "cpu_us")
        if native["status"] == "known" and cpu != native["value"]:
            native = {"name": "native_wall_us", "value": None, "unit": "us", "status": "unknown", "reason": "reported_cpu_us_mismatch"}
        hu = get("hu")
        hu_i = interval("hu_extract_wall_us", hu, "start", hu, "done")
        intervals = [
            interval("admission_wait_us", get("ingress"), "packet", get("ingress"), "admit"),
            interval("hud_pending_wait_us", get("ingress"), "pending", get("request"), "snapshot"),
            hu_i, native,
            interval("native_response_validation_us", get("native"), "done", get("hud"), "valid"),
            interval("sdram_write_wall_us", get("hud"), "valid", get("hud"), "write_done"),
            interval("sdram_readback_wall_us", get("hud"), "write_done", get("hud"), "readback_done"),
            interval("drain_ack_wall_us", get("hud"), "readback_done", get("final"), "drained"),
            interval("software_commit_wait_us", get("final"), "drained", get("final"), "software_ack"),
            interval("fpga_presentation_observation_wait_us", get("final"), "software_ack", get("final"), "presentation"),
            interval("packet_to_presentation_observation_us", get("ingress"), "packet", get("final"), "presentation"),
        ]
        slot = get("frame")
        frame_id = number(slot, "id")
        generation = number(slot, "generation")
        summaries.append({
            "ordinal": ordinal, "frame_id": frame_id, "generation": generation,
            "mode": "cached" if (doc.get("raw_rows") or {}).get("0", "").endswith("cache=true") else "unknown",
            "hu_scalar_commands": number(hu, "commands") if hu and hu.get("_tag") == "hu_scalar_fetch" else number(hu, "scalar_commands"),
            "intervals": intervals,
        })
    return {
        "schema": "receiver-phase-summary-v1",
        "input_path": str(path.resolve()), "input_sha256": input_sha,
        "identity": identity,
        "validated_receipt": {"result": doc["result"], "both_independently_validated": True,
                              "export2_records": usb["export2_records"], "checksum": usb["checksum"]},
        "timing_semantics": {
            "clock": "source-reported ESP monotonic clock in microseconds; derived only within this one session",
            "native_wall": "native_wall_us is wall duration around FFI call; not CPU-exclusive",
            "qspi": "No per-stage QSPI duration inferred; hu_extract interval is a broader observed stage wall span.",
            "crc": "No CRC recomputation performed; validation receipt is required and preserved.",
            "model_tag": "evidence_kind=model forces scope=model; model rows are never labeled physical.",
        },
        "frames": summaries,
        "cross_session_join": False,
    }


def summarize(path: Path, expected_sha256: str):
    raw = path.read_bytes()
    input_sha = hashlib.sha256(raw).hexdigest()
    if input_sha.lower() != expected_sha256.lower():
        raise InputError("input_sha256_does_not_match_validation_binding")
    return summarize_doc(json.loads(raw), path, input_sha)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("input", type=Path, help="one validated structured NETWORK-RESULT.json")
    p.add_argument("--expected-input-sha256", required=True, help="hash from trusted source-hash-pins.json")
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    try:
        out = summarize(a.input, a.expected_input_sha256)
    except (InputError, OSError, json.JSONDecodeError) as exc:
        p.error(str(exc))
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS_SUMMARIZED_ONE_VALIDATED_SESSION", "input_sha256": out["input_sha256"], "frames": len(out["frames"]), "scope": out["identity"]["execution_scope"]}))

if __name__ == "__main__":
    main()
