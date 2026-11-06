#!/usr/bin/env python3
"""Independently check retained BR88 component counts, byte totals, and pins."""
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / "experiments/python-gamebub-v88/entropy"
ATTEMPT = AREA / "attempts/20261106T150638168868Z-fb236a5e"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    index = json.loads((AREA / "index.json").read_text(encoding="utf-8"))
    report = json.loads((ATTEMPT / "results.json").read_text(encoding="utf-8"))
    if index.get("schema") != "cu66-v88-bounded-rice-components-v1":
        raise ValueError("unexpected entropy component schema")
    if index.get("status") != "PASS_NATIVE_AND_INDEPENDENT_PYTHON_CHUNK_PARITY":
        raise ValueError("component parity status is not PASS")
    summary_keys = ("schema", "status", "physical_timing_proven", "scope",
                    "native_exit_code", "native_sources", "chunks",
                    "coefficient_values", "AB38_bytes", "BR88_bytes", "byte_delta",
                    "old_feedback_decisions", "old_renormalizations",
                    "BR88_bit_reads", "BR88_raw_chunks", "wall_seconds")
    if any(report.get(k) != index.get(k) for k in summary_keys):
        raise ValueError("selected result summary differs from pinned index summary")

    for name, expected in index["source_sha256"].items():
        path = ROOT / name
        if not path.is_file() or sha256(path) != expected:
            raise ValueError(f"source pin mismatch: {name}")
    for name, expected in index["artifacts_sha256"].items():
        path = ATTEMPT / name
        if not path.is_file() or sha256(path) != expected:
            raise ValueError(f"attempt artifact pin mismatch: {name}")

    spec = importlib.util.spec_from_file_location("v88_entropy_data", AREA / "data.py")
    data = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(data)
    frames = chunks = coefficients = old_bytes = new_bytes = 0
    old_decisions = old_renorm = br88_bits = raw_chunks = 0
    identities = set()
    for frame in data.iter_frames(verify=True):
        identity = (frame["cohort"], frame["fid"], frame["ordinal"])
        if identity in identities:
            raise ValueError(f"duplicate source identity {identity}")
        identities.add(identity)
        frames += 1
        planes = frame["variants"]["65536"]
        if len(planes) != 3:
            raise ValueError(f"source {identity}: expected 3 planes")
        for plane in planes:
            for chunk in plane:
                payload = chunk["br88"]
                if len(payload) != chunk["new_bytes"]:
                    raise ValueError("BR88 byte length mismatch")
                if hashlib.sha256(payload).hexdigest() != chunk["br88_sha256"]:
                    raise ValueError("BR88 chunk SHA mismatch")
                if len(chunk["data"]) != chunk["old_bytes"]:
                    raise ValueError("AB38 byte length mismatch")
                old_bytes += chunk["old_bytes"]
                new_bytes += chunk["new_bytes"]
                coefficients += chunk["blocks"] * 64
                chunks += 1
                old_decisions += sum(chunk["old_decisions"])
                old_renorm += sum(chunk["old_renorm"])
                if chunk["br88_bits"] != chunk["old_decisions"]:
                    raise ValueError("BR88 bit-read count differs from old decisions")
                br88_bits += sum(chunk["br88_bits"])
                raw_chunks += int(chunk["br88_raw"])

    want = {
        "native_sources": frames,
        "chunks": chunks,
        "coefficient_values": coefficients,
        "AB38_bytes": old_bytes,
        "BR88_bytes": new_bytes,
        "byte_delta": new_bytes - old_bytes,
        "old_feedback_decisions": old_decisions,
        "old_renormalizations": old_renorm,
        "BR88_bit_reads": br88_bits,
        "BR88_raw_chunks": raw_chunks,
    }
    for key, actual in want.items():
        if actual != index[key]:
            raise ValueError(f"{key}: recomputed {actual}, report says {index[key]}")
    if frames != 457 or chunks != 1371 or len(identities) != frames:
        raise ValueError("source/chunk/identity count mismatch")
    print("V88_ENTROPY_ACCOUNTING_PASS " + " ".join(f"{k}={v}" for k, v in want.items()))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError) as exc:
        raise SystemExit(f"V88_ENTROPY_ACCOUNTING_FAIL {exc}")
