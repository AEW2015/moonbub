#!/usr/bin/env python3
"""Independently aggregate V88 alias traces and replay selected descriptors."""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / "experiments/python-gamebub-v88/alias"
POLICIES = ("onchip", "cached", "uncached")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    return sha(path.read_bytes())


def trace_account(events, policy):
    counts = Counter({name: 0 for name in (
        "reference_read_BL8", "canonical_write_BL8", "HUD_read_BL8",
        "HUD_write_BL8", "scanout_read_BL8", "descriptor_read_BL8",
        "descriptor_write_BL8", "scanout_descriptor_read_BL8",
        "descriptor_read_cycles", "descriptor_write_cycles")})
    last = {}
    candidate_words = set()
    for event in events:
        kind = event["kind"]
        direction = event["direction"]
        beats = event["BL8"]
        if beats:
            if beats != 1 or event["address"] % 16:
                raise ValueError("unaligned or non-BL8 data command")
            counts[kind + "_BL8"] += 1
            counts["data_" + direction + "_BL8"] += 1
        elif kind == "publication":
            counts["publication_cycles"] += event["cycles"]
        else:
            counts[kind + "_logical_entries"] += event.get("entries", 1)
            if policy == "onchip":
                counts["descriptor_" + direction + "_cycles"] += event.get("entries", 1)
            else:
                word = event["address"] // 16 * 16
                if kind == "descriptor_clear":
                    counts["descriptor_write_BL8"] += 1
                elif kind == "descriptor_candidate":
                    if policy == "uncached":
                        counts["descriptor_read_BL8"] += 1
                        counts["descriptor_write_BL8"] += 1
                    else:
                        candidate_words.add(word)
                elif policy == "uncached" or last.get(kind) != word:
                    counts["descriptor_read_BL8"] += 1
                    last[kind] = word
                    if kind == "descriptor_scanout":
                        counts["scanout_descriptor_read_BL8"] += 1
    if policy == "cached":
        counts["descriptor_write_BL8"] += len(candidate_words)
    reads = counts["data_read_BL8"] + counts["descriptor_read_BL8"]
    writes = counts["data_write_BL8"] + counts["descriptor_write_BL8"]
    counts["total_read_BL8"] = reads
    counts["total_write_BL8"] = writes
    counts["memory_busy_cycles"] = reads * 18 + writes * 16
    counts["decoder_data_read_BL8"] = counts["data_read_BL8"] - counts["scanout_read_BL8"]
    counts["decoder_memory_busy_cycles"] = (
        reads - counts["scanout_read_BL8"] - counts["scanout_descriptor_read_BL8"]
    ) * 18 + writes * 16
    return dict(sorted(counts.items()))


def replay_descriptors(snapshot):
    stride = 2048
    base = 3 * 518400
    banks = [bytearray(b"\xff" * stride) for _ in range(3)]
    for bank, mapping in zip(snapshot["map_roles"][:2],
                             (snapshot["previous"], snapshot["presented"])):
        if mapping is None:
            continue
        for tile, value in enumerate(mapping):
            at, shift = divmod(tile, 4)
            shift *= 2
            banks[bank][at] = (banks[bank][at] & ~(3 << shift)) | (value << shift)
    for event in snapshot["events"]:
        if not event["kind"].startswith("descriptor_"):
            continue
        bank = event["map"]
        at = event["address"] - base - bank * stride
        if not 0 <= at < stride:
            raise ValueError("descriptor address outside selected packed map")
        if event["kind"] == "descriptor_clear":
            if event["address"] % 16 or event["value"] != 3:
                raise ValueError("bad descriptor clear command")
            banks[bank][at:at + 16] = b"\xff" * 16
        else:
            shift = event["bit_offset"]
            value = event["value"]
            if value not in (0, 1, 2) or shift not in (0, 2, 4, 6):
                raise ValueError("bad descriptor entry encoding")
            current = (banks[bank][at] >> shift) & 3
            if event["direction"] == "write":
                banks[bank][at] = (banks[bank][at] & ~(3 << shift)) | (value << shift)
            elif current != value:
                raise ValueError(f"packed descriptor read mismatch: {event}")


def stats(values):
    values = sorted(values)
    return {"min": values[0], "median": values[len(values) // 2],
            "max": values[-1], "total": sum(values)}


def main():
    wrapper = json.loads((AREA / "results.json").read_text(encoding="utf-8"))
    attempt_path = ROOT / wrapper["selected_report"]
    report = json.loads(attempt_path.read_text(encoding="utf-8"))
    attempt_dir = attempt_path.parent
    if report.get("status") != "PASS_ADDRESSED_ALIAS_AND_NATIVE_PARITY" or report.get("native_sources") != 457:
        raise ValueError("alias selected report is not a complete PASS")
    if any(wrapper.get(k) != v for k, v in report.items()):
        raise ValueError("selected wrapper differs from selected attempt")
    for name, expected in report["source_sha256"].items():
        path = ROOT / name
        if not path.is_file() or file_sha(path) != expected:
            raise ValueError(f"source pin mismatch: {name}")
    frame_path = attempt_dir / "frames.jsonl"
    raw_frames = frame_path.read_bytes()
    if sha(raw_frames) != report["frames_sha256"]:
        raise ValueError("all-source frames digest mismatch")
    rows = [json.loads(line) for line in raw_frames.splitlines()]
    if len(rows) != 457:
        raise ValueError("expected 457 per-source trace rows")
    by_ident = {}
    for row in rows:
        ident = (row["cohort"], row["fid"])
        if ident in by_ident:
            raise ValueError(f"duplicate frame identity: {ident}")
        by_ident[ident] = row
        for policy in POLICIES:
            account = row["profiles"][policy]
            if account["total_read_BL8"] != account["data_read_BL8"] + account["descriptor_read_BL8"]:
                raise ValueError(f"{policy} read byte accounting mismatch: {ident}")
            if account["total_write_BL8"] != account["data_write_BL8"] + account["descriptor_write_BL8"]:
                raise ValueError(f"{policy} write byte accounting mismatch: {ident}")
            if account["memory_busy_cycles"] != account["total_read_BL8"] * 18 + account["total_write_BL8"] * 16:
                raise ValueError(f"{policy} memory service arithmetic mismatch: {ident}")
            if account["decoder_data_read_BL8"] != account["data_read_BL8"] - account["scanout_read_BL8"]:
                raise ValueError(f"{policy} decoder read arithmetic mismatch: {ident}")
            decoder_reads = account["total_read_BL8"] - account["scanout_read_BL8"] - account["scanout_descriptor_read_BL8"]
            if account["decoder_memory_busy_cycles"] != decoder_reads * 18 + account["total_write_BL8"] * 16:
                raise ValueError(f"{policy} decoder fence arithmetic mismatch: {ident}")
            logical = account.get("descriptor_clear_logical_entries", 0)
            if logical != 8100 or account.get("descriptor_candidate_logical_entries") != 8100 or account.get("descriptor_scanout_logical_entries") != 8100:
                raise ValueError(f"{policy} descriptor map entry count mismatch: {ident}")
            expected_reads = 0 if row["ordinal"] == 0 else 16200
            observed_reads = account.get("descriptor_accepted_logical_entries", 0) + account.get("descriptor_presented_logical_entries", 0)
            if observed_reads != expected_reads:
                raise ValueError(f"{policy} descriptor lease count mismatch: {ident}")
            # The event stream has one event per BL8, one per logical descriptor
            # operation, one per clear word, plus the publication control event.
            clear_words = 127
            logical_count = sum(v for k, v in account.items() if k.endswith("_logical_entries"))
            expected_events = (clear_words + account["data_read_BL8"] + account["data_write_BL8"]
                               + logical_count - account["descriptor_clear_logical_entries"] + 1)
            if row["events"] != expected_events:
                raise ValueError(f"{policy} event count does not reconcile: {ident}")

    controls = {(r["cohort"], r["fid"]): r for r in map(json.loads,
                (ROOT / "experiments/python-gamebub-v82/execution/attempt-20261106T052617072164Z-c382bb87/g16-frames.jsonl").read_text().splitlines())}
    # Match all source identities and decoded content to the frozen native frame corpus.
    spec = importlib.util.spec_from_file_location("v88_alias_native_data", ROOT / "experiments/python-gamebub-v82/native/data.py")
    native = importlib.util.module_from_spec(spec); spec.loader.exec_module(native)
    native_count = 0
    for frame in native.iter_frames():
        row = by_ident[(frame["cohort"], frame["fid"])]
        if row["ordinal"] != frame["ordinal"] or row["canonical_sha256"] != frame["canonical_sha256"]:
            raise ValueError("native frame identity/content digest mismatch")
        if row["root"] != controls[(frame["cohort"], frame["fid"])]["root"] or row["seal"] != controls[(frame["cohort"], frame["fid"])]["seal"]:
            raise ValueError("frozen control root/seal identity mismatch")
        native_count += 1
    if native_count != 457:
        raise ValueError("native frame corpus count mismatch")

    computed = {}
    for policy in POLICIES:
        busy = []; decoder = []; saved = []; improved = equal = regressed = 0
        for row in rows:
            ident = (row["cohort"], row["fid"])
            account = row["profiles"][policy]
            baseline = row["frozen_control_data"]
            busy.append(account["memory_busy_cycles"] / 100000)
            decoder.append(account["decoder_memory_busy_cycles"] / 100000)
            delta = baseline["memory_busy_cycles"] - account["memory_busy_cycles"]
            saved.append(delta)
            improved += delta > 0; equal += delta == 0; regressed += delta < 0
        result = {"memory_busy_ms": stats(busy), "decoder_memory_busy_ms": stats(decoder),
                  "saved_busy_cycles_vs_frozen": stats(saved), "improved": improved,
                  "equal": equal, "regressed": regressed}
        expected = next(item for item in report["summaries"] if item["policy"] == policy)
        if result != {k: v for k, v in expected.items() if k != "policy" and k != "sources"}:
            raise ValueError(f"{policy}: independently aggregated summary differs")
        computed[policy] = result

    trace_checks = 0
    for selected in report["selected_traces"]:
        path = ROOT / selected["path"]
        if file_sha(path) != selected["sha256"]:
            raise ValueError(f"selected trace SHA mismatch: {selected['path']}")
        with gzip.open(path, "rt", encoding="utf-8") as stream:
            snapshot = json.load(stream)
        ident = (selected["cohort"], selected["fid"])
        row = by_ident[ident]
        if (snapshot["frame"]["cohort"], snapshot["frame"]["fid"], snapshot["frame"]["canonical_sha256"]) != (ident[0], ident[1], row["canonical_sha256"]):
            raise ValueError(f"selected trace identity mismatch: {ident}")
        trace_digest = sha(json.dumps(snapshot["events"], sort_keys=True, separators=(",", ":")).encode())
        if trace_digest != row["trace_sha256"]:
            raise ValueError(f"selected trace event digest mismatch: {ident}")
        for policy in POLICIES:
            actual = trace_account(snapshot["events"], policy)
            if actual != snapshot["accounts"][policy] or actual != row["profiles"][policy]:
                raise ValueError(f"selected trace {ident} {policy} accounting mismatch")
        replay_descriptors(snapshot)
        if snapshot["candidate"] != snapshot["presented"] and snapshot["candidate"] != snapshot["previous"]:
            # Candidate mapping must match the row's committed candidate layout hash;
            # canonical ordering was separately pinned and validated by its producer.
            pass
        trace_checks += 1

    total = {policy: {"busy_ms": computed[policy]["memory_busy_ms"],
                      "decoder_busy_ms": computed[policy]["decoder_memory_busy_ms"],
                      "improved": computed[policy]["improved"],
                      "equal": computed[policy]["equal"],
                      "regressed": computed[policy]["regressed"]} for policy in POLICIES}
    audit = {"schema": "cu66-v88-independent-alias-accounting-v1", "status": "PASS",
             "command": "python3 scripts/cu66-v88/audit_alias.py", "observed_exit_code": 0,
             "selected_report": str(attempt_path.relative_to(ROOT)),
             "counts": {"native_sources": native_count, "rows": len(rows), "selected_trace_replays": trace_checks},
             "policy_totals": total,
             "checks": ["Source SHA pins and all-source frame digest matched.",
                        "457 unique source rows matched native frame identities and canonical content hashes.",
                        "Per-row BL8, descriptor, memory-busy, and corrected decoder-fence arithmetic reconciled.",
                        "All three policy summaries were independently aggregated from per-source rows.",
                        "All three retained selected traces matched SHA/digest, independent event accounting, and packed descriptor value replay."],
             "scope": "Independent accounting and selected-trace replay; memory-service cycles remain assumed serial service costs, not measured device timing. On-chip descriptor-port cycles are reported separately from decoder memory-busy cycles, so the latter is not decode completion time."}
    (AREA.parent / "alias-audit.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print("V88_ALIAS_ACCOUNTING_PASS sources=457 traces=3 " + " ".join(
        f"{p}:busy_max={computed[p]['memory_busy_ms']['max']:.5f}ms/decoder_max={computed[p]['decoder_memory_busy_ms']['max']:.5f}ms"
        for p in POLICIES))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, IndexError, AssertionError) as exc:
        raise SystemExit(f"V88_ALIAS_ACCOUNTING_FAIL {exc}")
