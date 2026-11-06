#!/usr/bin/env python3
"""Bounded source-backed physical-layout locality study; no RTL/perf claim."""
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = Path(__file__).resolve().parent
TRAFFIC = AREA / "traffic-results.json"
FIXTURE = AREA / "vectors/native-rows.hex.gz"
OUT = AREA / "layout-results.json"
FRAME_BYTES = 560_640
CANONICAL_BYTES = 518_400
HUD_BYTES = 42_240
Y_BASE, CB_BASE, CR_BASE = 0, 345_600, 432_000
HUD_BASE = CANONICAL_BYTES
PLANES = (("Y", 0, 720, 480), ("Cb", CB_BASE, 360, 240),
          ("Cr", CR_BASE, 360, 240))


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def pixel_plane(offset: int) -> tuple[str, int, int, int, int, int]:
    for name, base, width, height in PLANES:
        size = width * height
        if base <= offset < base + size:
            rel = offset - base
            y, x = divmod(rel, width)
            return name, base, width, height, x, y
    raise ValueError(f"logical byte offset outside frame: {offset}")


def physical_offset(layout: str, logical_offset: int) -> int:
    if not 0 <= logical_offset < FRAME_BYTES:
        raise ValueError("logical byte offset outside frame")
    if logical_offset >= CANONICAL_BYTES:
        hud_index = logical_offset - HUD_BASE
        if layout == "micro16x8":
            return CANONICAL_BYTES + 3_840 + hud_index
        return CANONICAL_BYTES + hud_index
    name, base, width, height, x, y = pixel_plane(logical_offset)
    if layout == "raster":
        return logical_offset
    if layout == "tile8x8":
        tiles_x = width // 8
        tile_id = (y // 8) * tiles_x + x // 8
        return base + tile_id * 64 + (y % 8) * 8 + x % 8
    if layout == "micro16x8":
        blocks_x = (width + 15) // 16
        phys_base = {"Y": 0, "Cb": 345_600, "Cr": 433_920}[name]
        block_id = (y // 8) * blocks_x + x // 16
        return phys_base + block_id * 128 + (y % 8) * 16 + x % 16
    raise ValueError(f"unknown layout: {layout}")


def extent(layout: str) -> dict:
    if layout == "micro16x8":
        return {"y": 345_600, "cb": 88_320, "cr": 88_320,
                "canonical": 522_240, "hud": 42_240, "total": 564_480,
                "padding": 3_840}
    return {"y": 345_600, "cb": 86_400, "cr": 86_400,
            "canonical": 518_400, "hud": 42_240, "total": 560_640,
            "padding": 0}


def read_frames(traffic: dict) -> list[dict]:
    frames = traffic["frames"]
    result = []
    expected_rows = FRAME_BYTES // 8
    raw_sha = hashlib.sha256()
    for idx, meta in enumerate(frames):
        frame = bytearray(FRAME_BYTES)
        seen = bytearray(FRAME_BYTES)
        starts = []
        raw = gzip.decompress(FIXTURE.read_bytes()) if idx == 0 else None
        if raw is not None:
            raw_sha.update(raw)
            lines = raw.splitlines()
        else:
            lines = cached_lines
        frame_rows = lines[idx * expected_rows:(idx + 1) * expected_rows]
        if len(frame_rows) != expected_rows:
            raise AssertionError("fixture frame row count mismatch")
        for line in frame_rows:
            packed = int(line, 16)
            data = (packed & ((1 << 64) - 1)).to_bytes(8, "little")
            addr = (packed >> 64) & ((1 << 20) - 1)
            bank = (packed >> 84) & 3
            if bank != meta["bank"] or addr % 8 or addr + 8 > FRAME_BYTES:
                raise AssertionError("source-backed row bank/alignment/range invalid")
            if any(seen[addr:addr + 8]):
                raise AssertionError("source frame has duplicate logical bytes")
            frame[addr:addr + 8] = data
            seen[addr:addr + 8] = b"\x01" * 8
            starts.append(addr)
        if not all(seen):
            raise AssertionError("source frame does not cover all logical bytes")
        if sha(bytes(frame)) != meta["accepted_bank_sha256"]:
            raise AssertionError("decoded fixture payload differs from accepted bank digest")
        result.append({"meta": meta, "bytes": bytes(frame), "request_starts": starts})
    if sum(len(x["request_starts"]) for x in result) != 140_160:
        raise AssertionError("native request fixture count mismatch")
    if sha(gzip.decompress(FIXTURE.read_bytes())) != traffic["fixture"]["raw_sha256"]:
        raise AssertionError("fixture raw digest differs from traffic results")
    if sha(FIXTURE.read_bytes()) != traffic["fixture"]["gzip_sha256"]:
        raise AssertionError("fixture gzip digest differs from traffic results")
    return result


def map_and_check(layout: str, frame: bytes, starts: list[int], candidate_bank: int) -> dict:
    mapping = [physical_offset(layout, i) for i in range(FRAME_BYTES)]
    e = extent(layout)
    if max(mapping) >= e["total"] or min(mapping) < 0:
        raise AssertionError(f"{layout}: mapping outside allocated physical extent")
    if len(set(mapping)) != FRAME_BYTES:
        raise AssertionError(f"{layout}: logical byte map is not injective")
    inverse = {p: i for i, p in enumerate(mapping)}
    if len(inverse) != FRAME_BYTES:
        raise AssertionError(f"{layout}: inverse map is not total on logical bytes")

    physical = bytearray(e["total"])
    for logical, phys in enumerate(mapping):
        physical[phys] = frame[logical]
    reconstructed_buf = bytearray(FRAME_BYTES)
    for phys, logical in inverse.items():
        reconstructed_buf[logical] = physical[phys]
    reconstructed = bytes(reconstructed_buf)
    if reconstructed != frame:
        raise AssertionError(f"{layout}: inverse reconstruction changed source bytes")
    request_physical_starts = []
    request_word_addresses = []
    for start in starts:
        mapped = [mapping[start + i] for i in range(8)]
        if mapped != list(range(mapped[0], mapped[0] + 8)) or mapped[0] % 8:
            raise AssertionError(f"{layout}: row payload not contiguous/aligned at {start}")
        request_physical_starts.append(mapped[0])
        word0 = (candidate_bank << 22) | (mapped[0] >> 1)
        # Fixed-width lowercase hex record: 5 digits each for logical and
        # physical byte offsets, then 6 digits for each of the four word addrs.
        request_word_addresses.append(
            f"{start:05x}{mapped[0]:05x}{word0:06x}{word0 + 1:06x}"
            f"{word0 + 2:06x}{word0 + 3:06x}")

    row_ids = [p // 1024 for p in request_physical_starts]
    transitions = 0
    previous = None
    for row in row_ids:
        if row != previous:
            transitions += 1
            previous = row
    return {"allocated_physical_extent_bytes": e["total"],
            "logical_frame_bytes": FRAME_BYTES,
            "padding_bytes": e["padding"],
            "plane_extents_bytes": {k: e[k] for k in ("y", "cb", "cr", "hud")},
            "all_request_payloads_8bytes_contiguous_and_aligned": True,
            "per_request_word_address_log_encoding": "one fixed-width lowercase hex record per request: logical byte offset (5 hex digits), physical byte offset (5), controller word addresses 0..3 (6 each); total 34 hex digits plus newline",
            "all_logical_bytes_injective": True,
            "inverse_reconstruction_sha256": sha(reconstructed),
            "source_frame_sha256": sha(frame),
            "reconstruction_exact": reconstructed == frame,
            "request_count": len(starts),
            "physical_row_transitions": transitions,
            "ideal_activate_count_closed_first_row": transitions,
            "_word_records": request_word_addresses}


def main() -> None:
    global cached_lines
    traffic = json.loads(TRAFFIC.read_text())
    if traffic["status"] != "PASS_SOURCE_BACKED_NATIVE_TRAFFIC":
        raise AssertionError("native traffic prerequisite is not qualified")
    raw = gzip.decompress(FIXTURE.read_bytes())
    cached_lines = raw.splitlines()
    frames = read_frames(traffic)
    layouts = ("raster", "tile8x8", "micro16x8")
    outputs = {}
    for layout in layouts:
        frame_results = []
        for f in frames:
            out = map_and_check(layout, f["bytes"], f["request_starts"], f["meta"]["bank"])
            out["frame_id"] = f["meta"]["id"]
            out["candidate_bank"] = f["meta"]["bank"]
            records = out.pop("_word_records")
            raw_trace = ("\n".join(records) + "\n").encode("ascii")
            trace_name = f"layout-{layout}-{f['meta']['id']}.hex.gz"
            trace_path = AREA / "vectors" / trace_name
            trace_path.write_bytes(gzip.compress(raw_trace, compresslevel=9, mtime=0))
            out["word_address_trace"] = {
                "path": str(trace_path.relative_to(ROOT)),
                "gzip_sha256": sha(trace_path.read_bytes()),
                "raw_sha256": sha(raw_trace),
                "raw_bytes": len(raw_trace),
                "rows": len(records),
                "format": "each line is 34 lowercase hex digits: logical_byte_addr[5], physical_byte_addr[5], controller_word_addr[0..3][6 each]"}
            frame_results.append(out)
        outputs[layout] = frame_results

    totals = {name: sum(x["physical_row_transitions"] for x in outputs[name])
              for name in layouts}
    if any(not all(f["reconstruction_exact"] for f in outputs[name]) for name in layouts):
        raise AssertionError("layout round-trip proof failed")
    # 16x8 padding is limited to two chroma planes: 8 unused columns x 240 rows
    # x one byte, for Cb and Cr. Y is exactly divisible by 16.
    micro = extent("micro16x8")
    if micro["padding"] != 3_840 or micro["canonical"] != 522_240 or micro["total"] != 564_480:
        raise AssertionError("microtile extent arithmetic mismatch")

    result = {
        "schema": "cu66-v91l-sdram-layout-study-v1",
        "status": "PASS_BOUNDED_LAYOUT_BIJECTION_AND_LOCALITY",
        "scope": "Source-backed address/data layout study and ideal SDRAM row-transition count only. Does not alter RTL, claim performance, or model refresh/commands/clock cycles.",
        "inputs": {"traffic_results": str(TRAFFIC.relative_to(ROOT)),
                   "traffic_status": traffic["status"],
                   "native_fixture": traffic["fixture"]["path"],
                   "fixture_sha256": traffic["fixture"]["gzip_sha256"],
                   "native_rows": traffic["fixture"]["rows"],
                   "frames": [f["id"] for f in traffic["frames"]]},
        "assumptions": {"candidate_bank_mapping": "word=(candidate_bank<<22)|(physical_byte_offset>>1); bank 0..2",
                        "controller_sdram_row_bytes": 1024,
                        "row_transition_rule": "one ideal ACT for first access to a bank and another after each physical row change in that bank; all rows initially closed; no refresh or command timing",
                        "logical_layout": "Y 720x480 bytes, Cb 360x240, Cr 360x240, then 42,240 HUD bytes",
                        "native_order": "source-backed 8-byte requests arrive in the existing 8x8 tile-major candidate order; baseline physical byte offsets are raster/canonical addresses",
                        "payload_roundtrip": "all actual fixture payload bytes are reconstructed at their canonical source offsets, remapped, then inverse reconstructed byte-for-byte"},
        "layouts": {"raster": {"description": "Current canonical raster physical byte placement.",
                                "per_frame": outputs["raster"], "two_frame_ideal_activates": totals["raster"]},
                    "tile8x8": {"description": "Physical plane placement in 8x8 tile-major order; no plane padding.",
                                "per_frame": outputs["tile8x8"], "two_frame_ideal_activates": totals["tile8x8"]},
                    "micro16x8": {"description": "Physical plane placement in 16x8 microtiles; HUD starts after padded physical canonical planes.",
                                  "per_frame": outputs["micro16x8"], "two_frame_ideal_activates": totals["micro16x8"],
                                  "physical_arithmetic": {"y_bytes": 345_600,
                                                          "cb_bytes": 88_320,
                                                          "cr_bytes": 88_320,
                                                          "padded_canonical_bytes": 522_240,
                                                          "hud_bytes": 42_240,
                                                          "total_allocated_bytes": 564_480,
                                                          "padding_bytes": 3_840}}},
        "comparison": {"ideal_activate_savings_vs_raster": {
                            name: totals["raster"] - totals[name] for name in layouts},
                        "fraction_of_raster_activates": {
                            name: totals[name] / totals["raster"] for name in layouts}},
        "limitations": ["No RTL promotion or source traffic change is included.",
                        "ACT counts are ideal bank-local row transitions only; refresh and physical command scheduling are excluded.",
                        "No write bandwidth, shared read/display service, frame-time, or FPS claim is made.",
                        "Micro16x8 needs later validation against read/reference schedules and its padded-plane address contract."]}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "activates": totals,
                      "savings_vs_raster": result["comparison"]["ideal_activate_savings_vs_raster"]}, indent=2))


if __name__ == "__main__":
    main()
