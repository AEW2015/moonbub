#!/usr/bin/env python3
"""Native oracle + conservative three-bank store-elision Python prototype.

No RTL, fixture, encoding, decoder, system bench, or existing reuse edits.
"""
import argparse
import datetime
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import tarfile
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / "fpga/experiments/cu66-v81/residency"
NATIVE = ROOT / "experiments/cu66-native-v69"
CONTAINER = "gamebub-cu66-v69-build"
TILES = 8100
FRAME_BYTES = TILES * 32
spec = importlib.util.spec_from_file_location("cu81_residency_model", AREA / "model.py")
model = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = model
spec.loader.exec_module(model)


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def relative(path):
    return str(path.relative_to(ROOT))


def stats(values):
    return dict(min=min(values), median=statistics.median(values), max=max(values)) if values else None


def hidden(plane, tile):
    x, y = tile % (90 if plane == 0 else 45), tile // (90 if plane == 0 else 45)
    return (((3 <= x < 22 and (7 <= y < 9 or 11 <= y < 13)) or
             (21 <= x < 61 and 45 <= y < 48) or (21 <= x < 51 and 49 <= y < 51))
            if plane == 0 else (11 <= x < 30 and y == 23))


HIDDEN = tuple(hidden(p, i) for p, n in enumerate((5400, 1350, 1350)) for i in range(n))
assert len(HIDDEN) == TILES and sum(HIDDEN) == 294


def masks(row):
    same = []
    for plane, n in enumerate((5400, 1350, 1350)):
        entry = row["planes"][plane]
        assert entry["plane"] == plane and entry["tiles"] == n
        raw = bytes.fromhex(entry["same_mask_u8_lsb_hex"])
        assert len(raw) == (n + 7) // 8
        assert all(not (raw[i // 8] >> (i % 8) & 1) for i in range(n, len(raw) * 8))
        bits = tuple(bool(raw[i // 8] >> (i % 8) & 1) for i in range(n))
        assert sum(hidden(plane, i) and b for i, b in enumerate(bits)) == entry["same_hidden"]
        assert sum(not hidden(plane, i) and b for i, b in enumerate(bits)) == entry["same_visible"]
        same.extend(bits)
    assert row["comparable"] or not any(same)
    return tuple(same)


def replay(rows, oracle_dir, mode="round_robin"):
    """All 457 native frames; alternate schedule exercises legal bank choices."""
    frames = []
    same_total = 0
    mm = None
    streams = {}
    stream_hashes = {}
    try:
        for row in rows:
            cohort = row["cohort"]
            if row["ordinal"] == 0:
                mm = model.Residency(TILES)
                streams[cohort] = gzip.open(oracle_dir / f"tiles-cohort-{cohort}.bin.gz", "rb")
                stream_hashes[cohort] = hashlib.sha256()
                cursor = 0
            raw = streams[cohort].read(FRAME_BYTES)
            assert len(raw) == FRAME_BYTES
            stream_hashes[cohort].update(raw)
            pixels = tuple(raw[i:i+32] for i in range(0, FRAME_BYTES, 32))
            same = masks(row)
            if not row["key"]:
                same_total += sum(same)
            if mode == "round_robin":
                candidate = next((cursor + offset) % 3 for offset in range(3)
                                 if (cursor + offset) % 3 not in mm.leased())
            else:
                available = sorted(set(range(3)) - mm.leased())
                candidate = available[(row["ordinal"] // 3) % len(available)]
            oldmasks = tuple(mm.masks)
            oldref = mm.reference
            oldfront = mm.front
            elisions = tuple(not row["key"] and same[i] and bool(oldmasks[i] & (1 << candidate))
                             for i in range(TILES))
            assert candidate not in mm.leased()
            mm.begin(row["fid"], row["packet_sha256"], candidate, row["key"], pixels, same)
            mm.step()
            tx = mm.commit()  # collector already checked native authentication/digests
            assert tx.elisions == sum(elisions) and tx.writes + tx.elisions == TILES
            assert not row["key"] or (tx.writes == TILES and tx.elisions == 0 and
                                       mm.masks == [1 << candidate] * TILES)
            # Every 17th source: retry the lost ACK and require exact zero mutation.
            if row["ordinal"] % 17 == 0:
                before = (mm.total_writes, mm.total_elisions, tuple(mm.masks), mm.commits)
                mm.replay_ack(row["fid"], row["packet_sha256"])
                assert before == (mm.total_writes, mm.total_elisions, tuple(mm.masks), mm.commits)
            mm.present()
            cursor = (candidate + 1) % 3
            hidden_elisions = sum(e and HIDDEN[i] for i, e in enumerate(elisions))
            frames.append(dict(cohort=cohort, ordinal=row["ordinal"], fid=row["fid"], key=row["key"],
                candidate_bank=candidate, old_reference_bank=oldref, old_front_bank=oldfront,
                same_tiles=sum(same), resident_elided_tiles=tx.elisions,
                resident_elided_hidden_tiles=hidden_elisions,
                resident_elided_visible_tiles=tx.elisions-hidden_elisions,
                physical_written_tiles=tx.writes, unchanged_residency_miss_writes=tx.unchanged_misses,
                changed_tile_writes=tx.changed_writes,
                hypothetical_canonical_BL8_writes=tx.writes*4,
                hypothetical_data_BL8_writes=tx.writes*4+2640,
                unchanged_reference_BL8_reads=0 if row["key"] else 32400,
                unchanged_HUD_BL8_reads=2640, unchanged_HUD_BL8_writes=2640,
                baseline_canonical_BL8_writes=32400, baseline_data_BL8_writes=35040,
                metadata_commands_priced=False, latency_savings_claimed=False))
        assert len(rows) == 457 and sum(not r["key"] for r in rows) == 437
        assert same_total == 2345125, "must match exact previous-reference equality screen"
        for cohort, stream in streams.items():
            assert not stream.read(1), "extra fingerprints"
        groups = []
        for cohort in range(4):
            for key in (True, False):
                ff = [f for f in frames if f["cohort"] == cohort and f["key"] == key]
                groups.append(dict(cohort=cohort, key=key, sources=len(ff),
                    resident_elided_tiles_total=sum(f["resident_elided_tiles"] for f in ff),
                    resident_elided_hidden_tiles_total=sum(f["resident_elided_hidden_tiles"] for f in ff),
                    resident_elided_visible_tiles_total=sum(f["resident_elided_visible_tiles"] for f in ff),
                    resident_elided_tiles_per_source=stats([f["resident_elided_tiles"] for f in ff]),
                    physical_written_tiles_total=sum(f["physical_written_tiles"] for f in ff),
                    unchanged_residency_miss_writes_total=sum(f["unchanged_residency_miss_writes"] for f in ff)))
        elided = sum(f["resident_elided_tiles"] for f in frames)
        written = sum(f["physical_written_tiles"] for f in frames)
        return dict(status="PASS", mode=mode, sources=457, keys=20, deltas=437, groups=groups,
            per_frame=frames, oracle_raw_stream_sha256={str(c): h.hexdigest() for c, h in stream_hashes.items()},
            hypothetical=dict(resident_elided_tiles=elided, physical_written_tiles=written,
                exact_previous_reference_equal_delta_tiles=same_total,
                unchanged_delta_tiles_missing_candidate_residency=same_total-elided,
                elidable_canonical_BL8_writes=elided*4,
                baseline_all_source_canonical_BL8_writes=457*32400,
                baseline_all_source_data_BL8_writes=457*35040,
                remaining_canonical_BL8_writes=written*4,
                remaining_data_BL8_writes=written*4+457*2640,
                unchanged_reference_BL8_reads=437*32400, unchanged_HUD_BL8_reads=457*2640,
                unchanged_HUD_BL8_writes=457*2640,
                baseline_counted_BL8_commands=457*35040+437*32400+457*2640,
                remaining_counted_BL8_commands=written*4+457*2640+437*32400+457*2640,
                metadata_commands_priced=False, display_scanout_commands_counted=False,
                logical_decode_or_authentication_removed=False, latency_savings_claimed=False))
    finally:
        for stream in streams.values():
            stream.close()


def native_fault_cases(rows, oracle_dir):
    """Native canonical tiles with directed partial/late-auth abort and retry.

    Counts include retries and are verification evidence, not savings estimates.
    """
    events = []
    total_writes = total_elisions = replays = accepted = 0
    streams = {}
    try:
        for row in rows:
            cohort = row["cohort"]
            if row["ordinal"] == 0:
                mm = model.Residency(TILES)
                streams[cohort] = gzip.open(oracle_dir/f"tiles-cohort-{cohort}.bin.gz", "rb")
            raw = streams[cohort].read(FRAME_BYTES)
            assert len(raw) == FRAME_BYTES
            pixels = tuple(raw[i:i+32] for i in range(0, FRAME_BYTES, 32))
            same = masks(row)
            available = sorted(set(range(3))-mm.leased())
            bank = available[(row["ordinal"] // 5) % len(available)]
            identity = row["packet_sha256"]
            oldaccepted, oldref, oldfront = mm.accepted, mm.reference, mm.front
            if row["ordinal"] % 31 == 0:
                before = tuple(mm.masks)
                mm.begin(row["fid"], identity, bank, row["key"], pixels, same)
                mm.step(4137)
                tx = mm.tx
                rewritten = {i for i in range(tx.cursor)
                             if row["key"] or not same[i] or not before[i] & (1 << bank)}
                assert len(rewritten) == tx.writes
                cleared = sum(bool(before[i] & (1 << bank)) for i in rewritten)
                mm.abort()
                assert (mm.accepted, mm.reference, mm.front) == (oldaccepted, oldref, oldfront)
                assert mm.masks == [mask & ~(1 << bank) if i in rewritten else mask
                                    for i, mask in enumerate(before)]
                events.append(dict(case="native_partial_abort_and_same_bank_retry", cohort=cohort,
                    fid=row["fid"], candidate_bank=bank, processed_tiles=4137,
                    abandoned_physical_writes=tx.writes, invalidated_old_certificate_bits=cleared,
                    accepted_reference_unchanged=True, invalidations_survived_abort=True))
            if row["ordinal"] % 37 == 0:
                mm.begin(row["fid"], identity, bank, row["key"], pixels, same)
                mm.step()
                tx = mm.tx
                try:
                    mm.commit(authenticated=False)
                except model.Rejected as exc:
                    assert str(exc) == "canonical/HUD/display authentication failure"
                else:
                    raise AssertionError("native authentication fault accepted")
                mm.abort()
                assert (mm.accepted, mm.reference, mm.front) == (oldaccepted, oldref, oldfront)
                events.append(dict(case="native_late_authentication_abort_and_retry", cohort=cohort,
                    fid=row["fid"], candidate_bank=bank, abandoned_physical_writes=tx.writes,
                    accepted_reference_unchanged=True, invalidations_survived_abort=True))
            mm.begin(row["fid"], identity, bank, row["key"], pixels, same)
            mm.step()
            mm.commit()
            accepted += 1
            before = (mm.total_writes, mm.total_elisions, tuple(mm.masks), mm.commits)
            mm.replay_ack(row["fid"], identity)  # every native frame gets lost-ACK replay
            assert before == (mm.total_writes, mm.total_elisions, tuple(mm.masks), mm.commits)
            replays += 1
            mm.present()
            if row["ordinal"] == (118 if cohort < 3 else 99):
                total_writes += mm.total_writes
                total_elisions += mm.total_elisions
        assert accepted == replays == 457
        assert any(e["invalidated_old_certificate_bits"] for e in events
                   if e["case"] == "native_partial_abort_and_same_bank_retry")
        return dict(status="PASS", sources=accepted, delta_sources=437, lost_ack_replays=replays,
            events=events, partial_aborts=sum(e["case"].startswith("native_partial") for e in events),
            late_authentication_aborts=sum(e["case"].startswith("native_late") for e in events),
            total_physical_writes_including_abandoned_attempts=total_writes,
            total_verified_elisions_including_abandoned_attempts=total_elisions,
            savings_estimate=False)
    finally:
        for stream in streams.values():
            stream.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--synthetic-only", action="store_true")
    parser.add_argument("--replay-oracle", type=Path, help="read an existing residency attempt instead of recollecting")
    args = parser.parse_args()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    out = AREA / f"attempt-{stamp}-{uuid.uuid4().hex[:8]}"
    out.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    report = dict(schema="cu81-bank-resident-elision-prototype-v1", status="FAIL", native_only=True,
                  rtl_or_encoding_or_protocol_changed=False, commands=[], failed_attempts=[])

    def write(name, value):
        path = out / name
        path.write_text(json.dumps(value, indent=2) + "\n")
        return dict(path=relative(path), sha256=sha(path))

    def run(argv, name, timeout):
        entry = dict(argv=argv, log=relative(out/name), exit_code=None, timed_out=False, timeout_seconds=timeout)
        report["commands"].append(entry)
        begin = time.monotonic()
        try:
            with (out/name).open("w") as stream:
                result = subprocess.run(argv, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, timeout=timeout)
            entry["exit_code"] = result.returncode
        except subprocess.TimeoutExpired:
            entry["timed_out"] = True
        finally:
            entry.update(wall_seconds=time.monotonic()-begin, sha256=sha(out/name))
        assert entry["exit_code"] == 0 and not entry["timed_out"], f"{name}: retained failed command"
        return (out/name).read_text()

    try:
        # Explicit ordering: independent exact-byte abstract cases before native access.
        cases = model.synthetic_cases()
        report["synthetic"] = write("synthetic.json", dict(status="PASS", cases=cases, count=len(cases),
            execution_order="before native collector or replay", full_tile_bytes=True))
        report["development_attempts"] = dict(path=relative(AREA/"development-attempts.json"),
                                               sha256=sha(AREA/"development-attempts.json"))
        if args.synthetic_only:
            report["status"] = "PASS_SYNTHETIC_ONLY"
            return
        index = NATIVE / "index.tsv"
        fields = [line.split("\t") for line in index.read_text().splitlines()]
        files = sorted(set([Path(__file__).resolve(), AREA/"model.py", AREA/"collect_tiles.cpp", index,
                            NATIVE/"manifest.json", *NATIVE.glob("*.hpp"), *[NATIVE/f[2] for f in fields]]))
        pins = {relative(p): sha(p) for p in files}
        report["source_sha256"] = pins
        for field in fields:
            assert sha(NATIVE/field[2]) == Path(field[2]).stem
        with tarfile.open(out/"sources.tar.gz", "w:gz") as archive:
            for p in files:
                if "cu66-v81" in p.parts:
                    archive.add(p, arcname=relative(p), recursive=False)
        report["source_snapshot"] = dict(path=relative(out/"sources.tar.gz"), sha256=sha(out/"sources.tar.gz"))
        if args.replay_oracle:
            oracle_dir = args.replay_oracle.resolve()
            old = json.loads((oracle_dir/"results.json").read_text())
            assert old["status"] == "PASS_NATIVE_BANK_RESIDENT_ELISION_PROTOTYPE"
            assert all(old["source_sha256"][relative(p)] == sha(p) for p in files
                       if "cu66-native-v69" in p.parts)
            report["reused_oracle"] = dict(path=relative(oracle_dir), results_sha256=sha(oracle_dir/"results.json"))
            body = (oracle_dir/"collector.log").read_text()
        else:
            oracle_dir = out
            builddir = "/build/v81-residency-" + uuid.uuid4().hex
            binary = builddir + "/collect_tiles"
            # One CPU, low priority, independent directory; no campaign state changes.
            cpu = str(max(os.sched_getaffinity(0)))
            prefix = ["docker", "exec", CONTAINER, "nice", "-n", "10", "taskset", "-c", cpu]
            run(["docker", "exec", CONTAINER, "mkdir", "-p", builddir], "mkdir.log", 30)
            run(prefix+["g++", "--version"], "compiler.log", 30)
            run(prefix+["g++", "-std=c++17", "-O2", "-Wall", "-Wextra", "-Werror",
                        str(AREA/"collect_tiles.cpp"), "-o", binary], "build.log", 120)
            report["binary_sha256"] = run(["docker", "exec", CONTAINER, "sha256sum", binary], "binary.log", 30).split()[0]
            body = run(prefix+["timeout", "--signal=TERM", "--kill-after=5s", "300s", binary,
                               str(index), str(out/"tiles-cohort-")], "collector.log", 310)
            streams = []
            for cohort, count in enumerate((119, 119, 119, 100)):
                raw = out/f"tiles-cohort-{cohort}.bin"
                assert raw.stat().st_size == count*FRAME_BYTES
                item = dict(cohort=cohort, frames=count, tile_fingerprints=count*TILES,
                    raw_bytes=raw.stat().st_size, raw_sha256=sha(raw),
                    ordering="frame ordinal; plane 0,1,2; row-major 8x8 tile; SHA256 of 64 raster bytes")
                compressed = raw.with_suffix(".bin.gz")
                with raw.open("rb") as source, compressed.open("wb") as destination:
                    with gzip.GzipFile(fileobj=destination, mode="wb", mtime=0, compresslevel=6) as target:
                        for chunk in iter(lambda: source.read(1 << 20), b""):
                            target.write(chunk)
                item.update(path=relative(compressed), bytes=compressed.stat().st_size, sha256=sha(compressed),
                            raw_temporary_file_retained=False)
                assert compressed.stat().st_size < 50*1024*1024
                raw.unlink()
                streams.append(item)
            report["oracle_streams"] = streams
        assert body.count("RESIDENCY_NATIVE_ORACLE_PASS ") == 1 and "FAIL" not in body
        rows = [json.loads(line) for line in body.splitlines() if line.startswith("{")]
        assert len(rows) == 457
        assert [sum(r["cohort"] == c for r in rows) for c in range(4)] == [119,119,119,100]
        # Bind every exported identity/digest back to the frozen native index.
        for row, field in zip(rows, fields):
            assert (row["cohort"], row["fid"], row["packet_sha256"], row["canonical_sha256"],
                    row["hud_sha256"], row["display_sha256"]) == (
                    int(field[0]), int(field[1]), Path(field[2]).stem, field[3], field[4], field[5])
        prior_runs = sorted((ROOT/"fpga/experiments/cu66-v81/tile-reuse").glob("attempt-*/run.log"))
        matching = []
        for path in prior_runs:
            old_rows = [json.loads(line) for line in path.read_text().splitlines() if line.startswith("{")]
            if len(old_rows) == len(rows):
                assert all((a["cohort"], a["fid"], a["key"], a["planes"]) ==
                           (b["cohort"], b["fid"], b["key"], b["planes"]) for a,b in zip(rows, old_rows))
                matching.append(dict(path=relative(path), sha256=sha(path), exact_masks_match=True))
        assert matching, "existing native equality screen must remain reproducible"
        report["prior_read_only_equality_crosscheck"] = matching
        report["oracle_rows"] = write("oracle-frames.json", rows)
        for mode in ("round_robin", "alternate_legal"):
            result = replay(rows, oracle_dir, mode)
            per_frame = result.pop("per_frame")
            result["frames"] = write(mode+"-frames.json", per_frame)
            if not args.replay_oracle:
                assert all(result["oracle_raw_stream_sha256"][str(s["cohort"])] == s["raw_sha256"]
                           for s in report["oracle_streams"])
            report[mode] = result
        report["native_directed_fault_cases"] = write("native-fault-cases.json", native_fault_cases(rows, oracle_dir))
        assert pins == {rel: sha(ROOT/rel) for rel in pins}, "screening input changed during attempt"
        report.update(status="PASS_NATIVE_BANK_RESIDENT_ELISION_PROTOTYPE",
            logical_metadata=dict(tile_count=8100, banks=3, maps=2, mask_bits=48600,
                packed_bytes=6075, additional_control_unpriced=True, target_fit_claimed=False),
            constraints=[
                "Native/Python prototype only; no RTL, encoding or system integration changes.",
                "Every claimed elision checked against actual native per-tile SHA256 fingerprints; synthetic cases use full 64-byte tiles.",
                "Native exact byte comparison exports unchanged masks; hardware must derive equality from decoded pixels and leased reference, never trust a host skip bit.",
                "Fingerprint/equality oracles validate the prototype only and are not an implemented FPGA integrity gate.",
                "Keys always write all tiles and reset each accepted mask to only the candidate bit.",
                "Accepted-reference bank, front bank and undrained scanout banks cannot be candidates.",
                "Old accepted-map candidate bits clear before physical stores and remain cleared after abort; only authenticated commit publishes shadow map.",
                "Physical candidate bank equals complete decoded canonical frame at every commit; no alias/refcount chains.",
                "All 20 keys and 437 deltas use frozen native packet/canonical/HUD/display digest checks; decoding and authentication work remain.",
                "BL8 command arithmetic preserves reference reads and HUD reads/writes; metadata and scanout traffic not priced.",
                "No physical traffic, latency, 30fps, under-10ms or FPGA fit claim; corpus is four histories from one walkthrough family."])
    except Exception as exc:
        report["failure"] = str(exc)
        report["failed_attempts"].append(dict(error=type(exc).__name__, reason=str(exc)))
        raise
    finally:
        report["wall_seconds"] = time.monotonic()-started
        (out/"results.json").write_text(json.dumps(report, indent=2)+"\n")
        print(json.dumps(dict(status=report["status"], results_path=str(out/"results.json"))), flush=True)


if __name__ == "__main__":
    main()
