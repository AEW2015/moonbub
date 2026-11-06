#!/usr/bin/env python3
"""Replay retained native residency evidence without importing its producer.

Uses the existing authenticated native SHA256 tile fingerprints and exact-byte
equality masks. No collector, native decoder, model or prototype is executed.
"""
import argparse
import datetime
import gzip
import hashlib
import json
import sys
import tarfile
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / "fpga/experiments/cu66-v81/residency-review"
DEFAULT = "fpga/experiments/cu66-v81/residency/attempt-20261106T044250131135Z-6caa860d/results.json"
COUNTS = {0: 119, 1: 119, 2: 119, 3: 100}
TILES = 8100
FRAME_BYTES = TILES * 32
INPUTS = {}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def path_for(rel):
    require(isinstance(rel, str) and not Path(rel).is_absolute(), "invalid repository path")
    path = (ROOT / rel).resolve()
    require(path.is_relative_to(ROOT) and path.is_file(), f"missing/outside input: {rel}")
    return path


def read_bytes(rel, expected=None):
    data = path_for(rel).read_bytes()
    pin = digest(data)
    require(expected is None or pin == expected, f"input hash mismatch: {rel}")
    require(rel not in INPUTS or INPUTS[rel] == pin, f"input changed during review: {rel}")
    INPUTS[rel] = pin
    return data


def read_json(rel, expected=None):
    return json.loads(read_bytes(rel, expected))


def bound_artifacts(value):
    if isinstance(value, dict):
        if "path" in value and "sha256" in value:
            read_bytes(value["path"], value["sha256"])
        for child in value.values():
            bound_artifacts(child)
    elif isinstance(value, list):
        for child in value:
            bound_artifacts(child)


def verify_source_snapshot(report):
    snap = report["source_snapshot"]
    read_bytes(snap["path"], snap["sha256"])
    with tarfile.open(path_for(snap["path"])) as archive:
        archived = {}
        for member in archive.getmembers():
            require(not Path(member.name).is_absolute() and ".." not in Path(member.name).parts,
                    "unsafe source snapshot member")
            if member.isfile():
                archived[member.name] = digest(archive.extractfile(member).read())
    for rel, pin in report["source_sha256"].items():
        if rel.startswith(("scripts/cu66-v81/", "fpga/experiments/cu66-v81/")):
            require(archived.get(rel) == pin, f"archived mutable source mismatch: {rel}")
        else:
            read_bytes(rel, pin)


def equal_mask(row):
    bits = []
    for plane in row["planes"]:
        raw = bytes.fromhex(plane["same_mask_u8_lsb_hex"])
        bits.extend(bool(raw[i // 8] >> (i % 8) & 1) for i in range(plane["tiles"]))
    require(len(bits) == TILES, "equality mask tile coverage mismatch")
    return bits


class Banks:
    """Independent physical-token image plus accepted-reference certificates."""
    def __init__(self):
        self.banks = [[None] * TILES for _ in range(3)]
        self.known = [0] * TILES
        self.reference = self.front = self.accepted = None
        self.writes = self.elisions = 0

    def available(self):
        return sorted(set(range(3)) - {self.reference, self.front})

    def check(self):
        if self.accepted is None:
            require(not any(self.known), "certificate without accepted frame")
            return
        require(self.banks[self.reference] == self.accepted, "accepted reference image changed")
        for i, mask in enumerate(self.known):
            require(mask >> self.reference & 1, "reference certificate absent")
            for bank in range(3):
                if mask >> bank & 1:
                    require(self.banks[bank][i] == self.accepted[i], "stale certificate")

    def step(self, pixels, same, key, bank, count):
        require(bank in self.available(), "candidate bank leased")
        expected = [a == b for a, b in zip(pixels, self.accepted)] if self.accepted else [False] * TILES
        require(same == expected, "exact-byte mask disagrees with native fingerprints")
        self.check()
        bit = 1 << bank
        shadow = []
        writes = elisions = misses = 0
        for i in range(count):
            skip = not key and same[i] and self.known[i] & bit
            if skip:
                require(self.banks[bank][i] == pixels[i] == self.accepted[i], "unsafe elision")
                elisions += 1
            else:
                self.known[i] &= ~bit
                self.banks[bank][i] = pixels[i]
                writes += 1
                misses += int(not key and same[i])
            shadow.append((self.known[i] if not key and same[i] else 0) | bit)
        self.writes += writes
        self.elisions += elisions
        return writes, elisions, misses, shadow

    def publish(self, pixels, shadow, bank):
        require(len(shadow) == TILES and self.banks[bank] == pixels,
                "candidate is not a complete native canonical frame")
        self.accepted, self.known, self.reference = pixels, shadow, bank
        self.front = bank
        self.check()


def pixels_for(streams, row):
    ordinal = row["ordinal"]
    raw = streams[row["cohort"]][ordinal * FRAME_BYTES:(ordinal + 1) * FRAME_BYTES]
    require(len(raw) == FRAME_BYTES, "native fingerprint frame length mismatch")
    return [raw[i:i + 32] for i in range(0, len(raw), 32)]


def positive_replay(rows, streams, report, mode):
    frames = read_json(report[mode]["frames"]["path"], report[mode]["frames"]["sha256"])
    require(len(frames) == len(rows), "positive replay frame count mismatch")
    total = misses = 0
    for row, recorded in zip(rows, frames):
        if row["ordinal"] == 0:
            state, cursor = Banks(), 0
        available = state.available()
        bank = (next((cursor + i) % 3 for i in range(3) if (cursor + i) % 3 in available)
                if mode == "round_robin" else available[(row["ordinal"] // 3) % len(available)])
        require(bank == recorded["candidate_bank"]
                and state.reference == recorded["old_reference_bank"] == recorded["old_front_bank"],
                "positive replay bank selection mismatch")
        pixels = pixels_for(streams, row)
        written, elided, miss, shadow = state.step(pixels, equal_mask(row), row["key"], bank, TILES)
        require(elided == recorded["resident_elided_tiles"] and written == recorded["physical_written_tiles"]
                and miss == recorded["unchanged_residency_miss_writes"], "positive source arithmetic mismatch")
        if row["key"]:
            require(elided == 0 and written == TILES and shadow == [1 << bank] * TILES,
                    "key did not fully write/reset certificates")
        state.publish(pixels, shadow, bank)
        cursor = (bank + 1) % 3
        total += elided
        misses += miss
    require(total * 4 == report[mode]["hypothetical"]["elidable_canonical_BL8_writes"],
            "positive aggregate elision mismatch")
    return dict(mode=mode, sources=len(rows), elided_canonical_BL8_writes=total * 4,
                unchanged_delta_tiles_missing_candidate_residency=misses)


def fault_replay(rows, streams, report):
    binding = report["native_directed_fault_cases"]
    recorded = read_json(binding["path"], binding["sha256"])
    events = []
    total_writes = total_elisions = 0
    for row in rows:
        cohort, ordinal = row["cohort"], row["ordinal"]
        if ordinal == 0:
            state = Banks()
        available = state.available()
        bank = available[(ordinal // 5) % len(available)]
        bit = 1 << bank
        pixels, same = pixels_for(streams, row), equal_mask(row)
        if ordinal % 31 == 0:
            before = state.known.copy()
            written, _, _, _ = state.step(pixels, same, row["key"], bank, 4137)
            rewritten = {i for i in range(4137) if row["key"] or not same[i] or not before[i] & bit}
            require(len(rewritten) == written and state.known == [mask & ~bit if i in rewritten else mask
                    for i, mask in enumerate(before)], "abort restored invalidated certificates")
            state.check()  # no publication: old accepted image and surviving bits remain valid
            events.append(dict(case="native_partial_abort_and_same_bank_retry", cohort=cohort,
                fid=row["fid"], candidate_bank=bank, processed_tiles=4137,
                abandoned_physical_writes=written,
                invalidated_old_certificate_bits=sum(bool(before[i] & bit) for i in rewritten),
                accepted_reference_unchanged=True, invalidations_survived_abort=True))
        if ordinal % 37 == 0:
            written, _, _, _ = state.step(pixels, same, row["key"], bank, TILES)
            require(state.banks[bank] == pixels, "late-auth candidate image mismatch")
            state.check()  # authentication failed, so the produced shadow is discarded
            events.append(dict(case="native_late_authentication_abort_and_retry", cohort=cohort,
                fid=row["fid"], candidate_bank=bank, abandoned_physical_writes=written,
                accepted_reference_unchanged=True, invalidations_survived_abort=True))
        _, _, _, shadow = state.step(pixels, same, row["key"], bank, TILES)
        state.publish(pixels, shadow, bank)
        if ordinal == COUNTS[cohort] - 1:
            total_writes += state.writes
            total_elisions += state.elisions
    require(events == recorded["events"], "directed native abort event mismatch")
    require(total_writes == recorded["total_physical_writes_including_abandoned_attempts"]
            and total_elisions == recorded["total_verified_elisions_including_abandoned_attempts"],
            "directed native fault aggregate mismatch")
    return dict(sources=len(rows), partial_frame_aborts=16, late_authentication_aborts=15,
        invalidated_old_certificate_bits=sum(e.get("invalidated_old_certificate_bits", 0) for e in events),
        writes_including_abandoned_attempts=total_writes,
        elisions_including_abandoned_attempts=total_elisions,
        producer_recorded_lost_ack_replays=recorded["lost_ack_replays"])


def review(final_rel):
    final = read_json(final_rel)
    original_rel = final["reused_oracle"]["path"] + "/results.json"
    original = read_json(original_rel, final["reused_oracle"]["results_sha256"])
    for report in (original, final):
        require(report["status"] == "PASS_NATIVE_BANK_RESIDENT_ELISION_PROTOTYPE"
                and report["native_only"] is True and report["rtl_or_encoding_or_protocol_changed"] is False,
                "producer status/scope mismatch")
        verify_source_snapshot(report)
        bound_artifacts(report)
        for command in report["commands"]:
            require(command["exit_code"] == 0 and command["timed_out"] is False,
                    "producer command failed/timed out")
            read_bytes(command["log"], command["sha256"])
    collector_rel = final["reused_oracle"]["path"] + "/collector.log"
    body = read_bytes(collector_rel).decode()
    require(body.count("RESIDENCY_NATIVE_ORACLE_PASS ") == 1 and "FAIL" not in body,
            "native oracle terminal failure")
    rows = read_json(final["oracle_rows"]["path"], final["oracle_rows"]["sha256"])
    require(rows == read_json(original["oracle_rows"]["path"], original["oracle_rows"]["sha256"])
            == [json.loads(line) for line in body.splitlines() if line.startswith("{")],
            "native oracle rows disagree")
    require(len(rows) == 457 and {c: sum(r["cohort"] == c for r in rows) for c in COUNTS} == COUNTS,
            "native corpus cardinality mismatch")
    index = [line.split("\t") for line in read_bytes("experiments/cu66-native-v69/index.tsv").decode().splitlines()]
    require(len(index) == len(rows), "frozen native index count mismatch")
    for row, field in zip(rows, index):
        require((row["cohort"], row["fid"], row["packet_sha256"], row["canonical_sha256"],
                 row["hud_sha256"], row["display_sha256"]) ==
                (int(field[0]), int(field[1]), Path(field[2]).stem, field[3], field[4], field[5]),
                "native digest identity disagrees with frozen index")
    for prior in final["prior_read_only_equality_crosscheck"]:
        prior_rows = [json.loads(line) for line in read_bytes(prior["path"], prior["sha256"]).decode().splitlines()
                      if line.startswith("{")]
        require(len(prior_rows) == len(rows) and all((a["cohort"], a["fid"], a["key"], a["planes"]) ==
                (b["cohort"], b["fid"], b["key"], b["planes"]) for a, b in zip(rows, prior_rows)),
                "prior native exact-byte mask crosscheck differs")
    streams = {}
    for stream in original["oracle_streams"]:
        compressed = read_bytes(stream["path"], stream["sha256"])
        raw = gzip.decompress(compressed)
        require(len(compressed) == stream["bytes"] and len(raw) == stream["raw_bytes"]
                and digest(raw) == stream["raw_sha256"], "native fingerprint stream mismatch")
        streams[stream["cohort"]] = raw
    positive = []
    for mode in ("round_robin", "alternate_legal"):
        require(final[mode]["hypothetical"] == original[mode]["hypothetical"]
                and read_json(final[mode]["frames"]["path"]) == read_json(original[mode]["frames"]["path"]),
                "positive replay changed from original reviewed attempt")
        positive.append(positive_replay(rows, streams, final, mode))
    return dict(positive_schedules=positive, directed_native_fault_replay=fault_replay(rows, streams, final))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", default=DEFAULT, help="repository-relative final residency results JSON")
    args = parser.parse_args()
    started = time.monotonic()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    out = AREA / f"attempt-{stamp}-{uuid.uuid4().hex[:8]}"
    out.mkdir(parents=True, exist_ok=False)
    script = Path(__file__).resolve()
    script_bytes = script.read_bytes()
    (out / "verifier.py").write_bytes(script_bytes)
    report = dict(schema="cu81-independent-native-residency-review-v1", status="FAIL",
        evidence=args.evidence, native_only=True, producer_modules_imported=False,
        verifier=dict(path=str(script.relative_to(ROOT)), sha256=digest(script_bytes)),
        verifier_snapshot=dict(path=str((out / "verifier.py").relative_to(ROOT)), sha256=digest(script_bytes)),
        limitations=["Existing native SHA256 tile fingerprints and exact-byte masks are trusted validation inputs, not FPGA gates.",
            "Independent replay covers both positive schedules and 31 retained native abort events; it does not execute producer modules.",
            "The 19 synthetic cases and 457 lost-ACK replays are bound producer evidence, not separately reimplemented cases here.",
            "Abstract whole-tile mutation; no individual partial BL8 beat, RTL, latency, physical throughput or target-fit proof."])
    lines = []
    exit_code = 1
    try:
        report.update(review(args.evidence))
        # Detect mutation of every read-only evidence input during this review.
        for rel, pin in list(INPUTS.items()):
            read_bytes(rel, pin)
        require(script.read_bytes() == script_bytes, "independent verifier changed during run")
        report["status"] = "PASS_INDEPENDENT_NATIVE_RESIDENCY_REPLAY"
        lines.append("V81_RESIDENCY_INDEPENDENT_PASS")
        lines.append(json.dumps({k: report[k] for k in ("positive_schedules", "directed_native_fault_replay")}, sort_keys=True))
        exit_code = 0
    except Exception as exc:
        report["failure"] = str(exc)
        lines.append("V81_RESIDENCY_INDEPENDENT_FAIL " + str(exc))
    log = out / "run.log"
    log.write_text("\n".join(lines) + "\n")
    report.update(source_sha256={**INPUTS, str(script.relative_to(ROOT)): digest(script_bytes)},
        wall_seconds=time.monotonic() - started,
        commands=[dict(argv=["python3", str(script.relative_to(ROOT)), "--evidence", args.evidence],
            log=str(log.relative_to(ROOT)), sha256=digest(log.read_bytes()), exit_code=exit_code,
            timed_out=False)])
    (out / "results.json").write_text(json.dumps(report, indent=2) + "\n")
    print("\n".join(lines))
    print(json.dumps(dict(status=report["status"], results_path=str((out / "results.json").relative_to(ROOT)))))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
