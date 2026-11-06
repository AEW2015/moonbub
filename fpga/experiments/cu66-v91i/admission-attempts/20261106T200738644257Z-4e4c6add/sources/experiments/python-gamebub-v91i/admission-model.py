#!/usr/bin/env python3
"""Independent CS88 V91i1 outer-admission model and vector exporter.

This model validates the restricted packet envelope and emits bounded structural
plane descriptors. It does not decode AB38/BR88 payloads or publish a frame.
"""
from __future__ import annotations

import hashlib
import json
import re
import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = Path(__file__).resolve().parent
VECTORS = AREA / "vectors"
CAP = 49152
KEY_REF = 0xFFFFFFFF
ERRORS = {
    0: "accepted structural receipt", 1: "size", 2: "input framing",
    3: "outer CRC", 4: "unsupported native profile", 5: "header bounds",
    6: "identity/stale", 7: "reference/cache", 8: "mode map",
    9: "QM CRC", 10: "QM format/run", 11: "QM required count",
    12: "chunk count", 13: "chunk span/coverage", 14: "unknown chunk magic",
}
PLANE_TILES = (5400, 1350, 1350)
VISIBLE_TILES = 7806
FIXED_MASK_SHA = "e08b9861ae9a170c913c6425a5773ff42042a0abfe2fef8cd756cb505a8a8fa5"


class Reject(Exception):
    def __init__(self, code: int, detail: str):
        super().__init__(detail)
        self.code = code
        self.detail = detail


def crc32(data: bytes) -> int:
    return zlib.crc32(data) & 0xFFFFFFFF


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_sha(path: Path) -> str:
    return sha(path.read_bytes())


def fixed_hidden_mask() -> tuple[int, ...]:
    """Read the frozen safety data as data; do not import a codec/receiver."""
    header = (ROOT / "experiments/cu66-native-v69/generated_constants.hpp").read_text()
    arrays = []
    for name, expected in (("SAFE0", 5400), ("SAFE1", 1350), ("SAFE2", 1350)):
        match = re.search(rf"{name}\[{expected}\]=\{{([^}}]+)\}};", header)
        if not match:
            raise ValueError(f"missing frozen {name} profile")
        row = tuple(int(v) for v in match.group(1).split(","))
        if len(row) != expected or any(v not in (0, 1) for v in row):
            raise ValueError(f"invalid frozen {name} profile")
        arrays.append(row)
    mask = tuple(v for row in arrays for v in row)
    if len(mask) != 8100 or sha(bytes(mask)) != FIXED_MASK_SHA:
        raise ValueError("fixed hidden profile digest mismatch")
    return mask


def active_cells(ops: tuple[int, ...]) -> int:
    active = bytearray(1350)
    for tile, mode in enumerate(ops):
        if mode != 2:
            continue
        if tile < 5400:
            cell = (tile // 90 // 2) * 45 + (tile % 90 // 2)
        else:
            cell = (tile - 5400) % 1350
        active[cell] = 1
    return sum(active)


def decode_modes(packet: bytes, off: int, size: int, key: bool, method: int,
                 hidden: tuple[int, ...]) -> tuple[int, ...]:
    body = packet[off:off + size]
    if key:
        if method != 0 or size != 0:
            raise Reject(8, "key requires implicit method 0 and empty body")
        return tuple(1 if h else 2 for h in hidden)
    if method != 3:
        # Methods 1/2 are valid native CS88 modes, but outside the frozen V91i1 subset.
        raise Reject(4, "V91i1 delta profile requires grouped method 3")
    at = 0
    out = [1] * 8100
    covered = 0
    for plane, plane_n in enumerate(PLANE_TILES):
        base = sum(PLANE_TILES[:plane])
        for begin in range(0, plane_n, 16):
            if at + 2 > size * 8:
                raise Reject(8, "group tag truncation")
            high = (body[at // 8] >> (7 - at % 8)) & 1
            at += 1
            low = (body[at // 8] >> (7 - at % 8)) & 1
            at += 1
            tag = (high << 1) | low
            indices = [base + t for t in range(begin, min(begin + 16, plane_n))
                       if not hidden[base + t]]
            if not indices:
                if tag != 3:
                    raise Reject(8, "empty hidden-only group must use tag 3")
                continue
            if tag == 3:
                raise Reject(8, "tag 3 on group containing visible tiles")
            covered += len(indices)
            if tag < 2:
                value = 2 if tag else 0
                for index in indices:
                    out[index] = value
            else:
                values = []
                for index in indices:
                    if at >= size * 8:
                        raise Reject(8, "mixed group bits truncated")
                    value = (body[at // 8] >> (7 - at % 8)) & 1
                    at += 1
                    values.append(value)
                    out[index] = 2 if value else 0
                if not any(values) or all(values):
                    raise Reject(8, "mixed group tag is noncanonical")
    if covered != VISIBLE_TILES or (at + 7) // 8 != size:
        raise Reject(8, "group body exact coverage/length")
    while at < size * 8:
        if (body[at // 8] >> (7 - at % 8)) & 1:
            raise Reject(8, "nonzero group padding")
        at += 1
    return tuple(out)


def parse_qmap(packet: bytes, off: int, size: int, ops: tuple[int, ...],
               key: bool, ref: dict) -> tuple[int, int]:
    if size < 16 or size > 354:
        raise Reject(10, "QM87 block length")
    block = packet[off:off + size]
    if crc32(block[:-4]) != int.from_bytes(block[-4:], "big"):
        raise Reject(9, "QM87 CRC32 mismatch")
    magic, version, method, cells, body_n, required = struct.unpack_from(">4sBBHHH", block)
    if magic != b"QM87" or version != 1 or cells != 1350 or len(block) != 16 + body_n:
        raise Reject(10, "QM87 header or exact body length")
    # The RTL checks supported method after CRC and generic QM header shape.
    if method not in (2, 6):
        raise Reject(4, "V91i1 accepts QM87 methods 2 and 6 only")
    actual_required = active_cells(ops)
    if required != actual_required:
        raise Reject(11, "QM87 required active-cell count mismatch")
    body = block[12:-4]
    if method == 6:
        # RTL binds required cells before checking cache eligibility.
        if key or not ref["valid"] or not ref["qcache_valid"]:
            raise Reject(7, "QM87 inherited map requires delta and accepted qcache")
        if body_n != 0:
            raise Reject(10, "QM87 method 6 must be bodyless")
    else:
        values = []
        for byte in body:
            value, run = byte >> 6, (byte & 63) + 1
            if value == 3 or len(values) + run > 1350:
                raise Reject(10, "QM87 run value/overrun")
            values.extend([value] * run)
        if len(values) != 1350:
            raise Reject(10, "QM87 run underrun")
    return method, required


def admit(packet: bytes, ref: dict, hidden: tuple[int, ...]) -> dict:
    """Return a structural receipt or raise Reject(code, detail)."""
    if len(packet) < 132 or len(packet) > CAP:
        raise Reject(1, "packet outside V91i1 132..49152 byte budget")
    trailer = int.from_bytes(packet[-4:], "big")
    if crc32(packet[:-4]) != trailer:
        raise Reject(3, "outer CRC32 mismatch")
    if len(packet) < 128:
        raise Reject(5, "short fixed header")
    if packet[:4] != b"CS88" or packet[4] != 1 or packet[6] != 16:
        raise Reject(4, "CS88 profile/version/group")
    flags = packet[5]
    method = packet[7]
    if flags > 1:
        raise Reject(5, "flags")
    key = bool(flags)
    fid, refid = struct.unpack_from(">II", packet, 8)
    generation = struct.unpack_from(">Q", packet, 16)[0]
    width, height, block_size, reserved = struct.unpack_from(">HHHH", packet, 24)
    cap, mode_n, q_n, hud_n, data_n = struct.unpack_from(">IIIII", packet, 32)
    # Native-supported but deliberately excluded V91i1 profiles reject before receipt.
    if block_size != 32 or cap != 65536 or (key and method != 0) or (not key and method != 3):
        raise Reject(4, "V91i1 requires block32/cap65536/key0/delta3")
    if width != 720 or height != 480 or reserved != 0 or mode_n > 976 or q_n < 16 or q_n > 354 or hud_n < 110 or hud_n > CAP:
        raise Reject(5, "geometry/reserved/component bounds")
    if 128 + mode_n + q_n + data_n + hud_n + 4 != len(packet):
        raise Reject(5, "exact packet body length")
    if packet[116:128] != bytes(12):
        raise Reject(5, "reserved header padding")
    if fid == KEY_REF or generation == 0:
        raise Reject(6, "invalid identity or zero generation")
    if ref["valid"] and (fid <= ref["fid"] or generation <= ref["generation"]):
        raise Reject(6, "frame id/generation are not newer than accepted snapshot")
    if key:
        if refid != KEY_REF:
            raise Reject(7, "key frame reference sentinel")
    elif not ref["valid"] or refid != ref["fid"]:
        raise Reject(7, "delta reference does not match accepted snapshot")
    mode_off = 128
    q_off = mode_off + mode_n
    data_off = q_off + q_n
    hud_off = data_off + data_n
    ops = decode_modes(packet, mode_off, mode_n, key, method, hidden)
    q_method, required = parse_qmap(packet, q_off, q_n, ops, key, ref)
    cursor = data_off
    planes = []
    for axis, tiles in enumerate(PLANE_TILES):
        need_blocks = sum(op == 2 for op in ops[sum(PLANE_TILES[:axis]):sum(PLANE_TILES[:axis + 1])])
        if cursor + 4 > data_off + data_n:
            raise Reject(13, "plane chunk-count field crosses residual span")
        n_chunks = int.from_bytes(packet[cursor:cursor + 4], "big")
        cursor += 4
        expected_chunks = (need_blocks + 65535) // 65536
        if n_chunks != expected_chunks:
            raise Reject(12, "plane chunk count does not cover active residuals")
        for chunk_i in range(n_chunks):
            if cursor + 8 > data_off + data_n:
                raise Reject(13, "chunk directory crosses residual span")
            blocks, length = struct.unpack_from(">II", packet, cursor)
            cursor += 8
            want = min(65536, need_blocks - chunk_i * 65536)
            if blocks != want or blocks == 0 or length < 46 or length > 46 + 128 * blocks:
                raise Reject(13, "chunk count/length bound")
            if cursor + length > data_off + data_n:
                raise Reject(13, "chunk payload crosses residual span")
            magic = packet[cursor:cursor + 4]
            if magic == b"AB38":
                entropy_type = 1
            elif magic == b"BR88":
                entropy_type = 2
            else:
                raise Reject(14, "unknown residual chunk magic")
            planes.append(dict(axis=axis, blocks=blocks, offset=cursor, length=length, entropy_type=entropy_type))
            cursor += length
    if cursor != data_off + data_n:
        raise Reject(13, "residual bytes not exactly covered by three plane directories")
    return dict(fid=fid, refid=refid, generation=generation, key=key,
                mode_bytes=mode_n, qmap_bytes=q_n, qmap_method=q_method,
                qmap_required=required, hud_bytes=hud_n, data_bytes=data_n,
                hud_offset=hud_off, planes=planes)


def load_lines(path: Path):
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def fixture_sources():
    v88_result = json.loads((ROOT / "experiments/python-gamebub-v88/wire/results.json").read_text())
    v88_run = ROOT / v88_result["selected_report"]
    v88_dir = v88_run.parent
    v88_rows = load_lines(v88_dir / "frames.jsonl")
    history = {(row["cohort"], row["fid"], row["policy"]): row for row in v88_rows}
    v90_dir = ROOT / "experiments/python-gamebub-v90/native/attempts/20261106T160439132762Z-32bde2e1"
    v90_rows = load_lines(v90_dir / "frames.jsonl")
    found = []
    for path in sorted(v88_dir.glob("*.cs88")):
        m = re.match(r"c(\d+)-f(\d+)-(.+)\.cs88$", path.name)
        if not m:
            raise ValueError(path)
        cohort, fid = int(m.group(1)), int(m.group(2))
        policy = m.group(3)
        found.append(("v88", cohort, fid, path, history[(cohort, fid, policy)],
                      history.get((cohort, fid - 1, policy))))
    for path in sorted(v90_dir.glob("*.cs88")):
        m = re.match(r"c(\d+)-f(\d+)-(.+)\.cs88$", path.name)
        if not m:
            raise ValueError(path)
        cohort, fid = int(m.group(1)), int(m.group(2))
        policy = m.group(3)
        row = next(r for r in v90_rows if r["cohort"] == cohort and r["fid"] == fid and r["policy"] == policy)
        prior = next((r for r in v90_rows if r["cohort"] == cohort and r["fid"] == fid - 1 and r["policy"] == policy), None)
        found.append(("v90", cohort, fid, path, row, prior))
    if len([x for x in found if x[0] == "v88"]) != 35 or len([x for x in found if x[0] == "v90"]) != 16:
        raise ValueError("retained packet fixture population changed")
    return found


def accepted_snapshot(cohort: int, fid: int, row: dict, prior_row: dict | None, origin: str) -> tuple[dict, dict]:
    """Use previous accepted row in same frozen 100-frame cohort history."""
    if fid == 0:
        return dict(valid=False, fid=0, generation=0, qcache_valid=False), dict(kind="initial_cohort_state", source="receiver history begins at fid 0")
    decoded = row["decoded"]
    if prior_row is None:
        raise ValueError(f"missing actual prior accepted row for {origin} c{cohort} f{fid}")
    prior_decoded = prior_row["decoded"]
    previous = prior_decoded["fid"]
    generation = prior_decoded["generation"]
    if (decoded["generation"] <= generation or decoded["fid"] != fid or previous != fid - 1 or
            prior_decoded.get("accepted") is not True):
        raise ValueError("source row identity/generation mismatch")
    return dict(valid=True, fid=previous, generation=generation, qcache_valid=True), dict(
        kind="actual_prior_accepted_history", source=f"V{origin[1:]} selected native receiver history",
        receiver_history_policy=prior_row["policy"],
        receiver_history_packet_sha256=prior_row["packet_sha256"],
        cohort=cohort, accepted_fid=previous, accepted_generation=generation,
        current_generation=decoded["generation"],
        prior_acceptance=prior_decoded["accepted"],
        qcache_evidence="prior accepted frame supplied persistent QM87 map")


def parse_expected(packet: bytes, ref: dict, hidden: tuple[int, ...]) -> tuple[int, dict | None, str | None]:
    try:
        return 0, admit(packet, ref, hidden), None
    except Reject as error:
        return error.code, None, error.detail


def mutate_crc(packet: bytearray) -> None:
    packet[-4:] = struct.pack(">I", crc32(packet[:-4]))


def negative_cases(base_path: Path, packet: bytes, ref: dict, hidden: tuple[int, ...]):
    """Directed recomputed-CRC semantic negatives plus one transport-text error."""
    cases = []
    def add(name, data, state=None, reason="", recomputed=False):
        code, receipt, detail = parse_expected(bytes(data), state or ref, hidden)
        cases.append(dict(id=name, class_="negative", packet=bytes(data), ref=state or ref,
                          expected_error=code, expected=receipt, negative_reason=reason,
                          mutation=dict(base_packet=str(base_path.relative_to(ROOT)), base_sha256=sha(packet),
                                        changed=reason, outer_crc_recomputed=recomputed),
                          error_detail=detail))
    # Outer integrity and unsupported/native profile branches.
    b = bytearray(packet); b[-1] ^= 1; add("bad_outer_crc", b, reason="flip outer CRC trailer")
    b = bytearray(packet); b[28:30] = struct.pack(">H", 16); mutate_crc(b); add("unsupported_block16", b, reason="block size 32 to 16", recomputed=True)
    b = bytearray(packet); b[32:36] = struct.pack(">I", 256); mutate_crc(b); add("unsupported_cap256", b, reason="chunk cap 65536 to 256", recomputed=True)
    b = bytearray(packet); b[7] = 2; mutate_crc(b); add("unsupported_delta_mode2", b, reason="delta mode method 3 to native method 2", recomputed=True)
    # Header, identity, reference, mode-map and qmap checks.
    b = bytearray(packet); b[24:26] = struct.pack(">H", 719); mutate_crc(b); add("bad_geometry", b, reason="width 720 to 719", recomputed=True)
    b = bytearray(packet); b[127] = 1; mutate_crc(b); add("bad_reserved", b, reason="nonzero reserved header padding", recomputed=True)
    b = bytearray(packet); b[48:52] = struct.pack(">I", 0xFFFFFFFF); mutate_crc(b)
    add("header_length_u32_max", b, reason="declared residual length set to maximum u32", recomputed=True)
    b = bytearray(packet); b[8:12] = struct.pack(">I", ref["fid"]); mutate_crc(b); add("stale_identity", b, reason="fid equals accepted fid", recomputed=True)
    b = bytearray(packet); b[8:12] = struct.pack(">I", KEY_REF); mutate_crc(b); add("fid_reserved_all_ones", b, reason="fid set to reserved FFFFFFFF", recomputed=True)
    b = bytearray(packet); b[16:24] = bytes(8); mutate_crc(b); add("generation_zero", b, reason="generation set to zero", recomputed=True)
    b = bytearray(packet); b[8:12] = struct.pack(">I", ref["fid"] + 1); b[16:24] = struct.pack(">Q", ref["generation"]); mutate_crc(b)
    add("stale_generation_fresh_fid", b, reason="fresh fid with generation equal to accepted generation", recomputed=True)
    if not packet[5]:
        b = bytearray(packet); b[12:16] = struct.pack(">I", ref["fid"] + 7); mutate_crc(b); add("wrong_reference", b, reason="delta refid differs from accepted fid", recomputed=True)
        missing = dict(valid=False, fid=0, generation=0, qcache_valid=False)
        add("missing_accepted_reference", packet, missing, "delta packet presented without accepted reference")
    elif ref["valid"]:
        b = bytearray(packet); b[12:16] = struct.pack(">I", 0); mutate_crc(b)
        add("key_bad_reference_sentinel", b, reason="key refid changed from FFFFFFFF", recomputed=True)
    mode_n = int.from_bytes(packet[36:40], "big")
    mode_off = 128
    if mode_n:
        b = bytearray(packet); b[36:40] = struct.pack(">I", mode_n - 1); mutate_crc(b); add("short_group_map", b, reason="declared grouped mode length minus one", recomputed=True)
    qoff = 128 + mode_n
    qlen = int.from_bytes(packet[40:44], "big")
    b = bytearray(packet); b[qoff + 5] = 4; b[-1] ^= 1
    add("bad_outer_crc_and_unsupported_qm", b,
        reason="set unsupported QM method and corrupt outer CRC", recomputed=False)
    if packet[7] == 3 and mode_n:
        b = bytearray(packet); b[mode_off] |= 0xC0; mutate_crc(b); add("bad_group_tag", b, reason="rewrite first populated group tag to forbidden tag 3", recomputed=True)
    b = bytearray(packet); b[qoff + qlen - 1] ^= 1; mutate_crc(b); add("bad_qm_crc", b, reason="flip QM87 CRC only; refresh outer CRC", recomputed=True)
    if qlen >= 17 and packet[qoff + 5] == 2:
        b = bytearray(packet); b[qoff + 12] = 0xC0 | (b[qoff + 12] & 0x3F)
        b[qoff + qlen - 4:qoff + qlen] = struct.pack(">I", crc32(b[qoff:qoff + qlen - 4])); mutate_crc(b)
        add("bad_qm_run_value", b, reason="set first QM2 run value to reserved 3", recomputed=True)
        b = bytearray(packet); b[qoff + 10:qoff + 12] = struct.pack(">H", int.from_bytes(b[qoff + 10:qoff + 12], "big") ^ 1)
        b[qoff + qlen - 4:qoff + qlen] = struct.pack(">I", crc32(b[qoff:qoff + qlen - 4])); mutate_crc(b)
        add("bad_qm_required", b, reason="alter QM required-count field", recomputed=True)
    if qlen >= 16 and packet[qoff + 5] == 6:
        absent = dict(valid=ref["valid"], fid=ref["fid"], generation=ref["generation"], qcache_valid=False)
        add("qm6_missing_cache", packet, absent, "accepted reference has no qcache")
        b = bytearray(packet); b[qoff + 10:qoff + 12] = struct.pack(">H", int.from_bytes(b[qoff + 10:qoff + 12], "big") ^ 1)
        b[qoff + qlen - 4:qoff + qlen] = struct.pack(">I", crc32(b[qoff:qoff + qlen - 4])); mutate_crc(b)
        add("bad_qm6_required", b, reason="alter QM6 required-cell count", recomputed=True)
        absent_and_wrong = dict(valid=ref["valid"], fid=ref["fid"], generation=ref["generation"], qcache_valid=False)
        add("bad_qm6_required_missing_cache", b, absent_and_wrong,
            "required-cell mismatch precedes QM6 cache eligibility")
    b = bytearray(packet); b[qoff + 5] = 4
    b[qoff + qlen - 4:qoff + qlen] = struct.pack(">I", crc32(b[qoff:qoff + qlen - 4])); mutate_crc(b)
    add("unsupported_qm_method4", b, reason="QM method 2/6 profile changed to method 4", recomputed=True)
    b = bytearray(packet); b[qoff + 5] = 4; mutate_crc(b)
    add("bad_qm_crc_and_unsupported_method", b,
        reason="change QM method to unsupported 4 without repairing inner CRC; refresh outer CRC", recomputed=True)
    # Residual chunk structure. Packet data starts after map/qmap.
    dataoff = 128 + mode_n + qlen
    datan = int.from_bytes(packet[48:52], "big")
    first_count = dataoff
    b = bytearray(packet); b[first_count:first_count + 4] = struct.pack(">I", int.from_bytes(b[first_count:first_count + 4], "big") + 1); mutate_crc(b)
    add("bad_chunk_count", b, reason="increment first plane chunk count", recomputed=True)
    b = bytearray(packet); b[first_count + 4:first_count + 8] = struct.pack(">I", 1); mutate_crc(b)
    add("bad_chunk_blocks", b, reason="first plane chunk blocks changed to 1", recomputed=True)
    # Locate first payload using its first directory entry.
    payload = first_count + 12
    first_len = int.from_bytes(packet[first_count + 8:first_count + 12], "big")
    b = bytearray(packet); b[payload:payload + 4] = b"ZZZZ"; mutate_crc(b)
    add("unknown_chunk_magic", b, reason="replace first entropy magic with ZZZZ", recomputed=True)
    b = bytearray(packet); b[first_count + 8:first_count + 12] = struct.pack(">I", first_len + datan + 1); mutate_crc(b)
    add("chunk_payload_overflow", b, reason="first chunk length crosses declared residual span", recomputed=True)
    b = bytearray(packet); b[first_count + 8:first_count + 12] = struct.pack(">I", 0xFFFFFFFF); mutate_crc(b)
    add("chunk_length_u32_max", b, reason="first chunk length set to maximum u32", recomputed=True)
    b = bytearray(packet); b[48:52] = struct.pack(">I", datan - 1); mutate_crc(b)
    add("residual_trailing_byte", b, reason="shrink data span while leaving packet bytes", recomputed=True)
    b = bytearray(packet); b[48:52] = struct.pack(">I", datan - 4); del b[-int.from_bytes(packet[44:48], "big")-4:-int.from_bytes(packet[44:48], "big")]
    mutate_crc(b); add("truncated_third_plane", b, reason="remove final four bytes from residual span", recomputed=True)
    # Absolute application budget boundary: make a padded but consistently framed packet.
    if len(packet) < CAP:
        b = bytearray(packet[:-4]); addn = CAP + 1 - len(packet)
        b.extend(bytes(addn)); b[44:48] = struct.pack(">I", int.from_bytes(packet[44:48], "big") + addn)
        b.extend(struct.pack(">I", crc32(b)))
        add("over_budget_49153", b, reason="append HUD padding above 49152-byte admission cap", recomputed=True)
    return cases


def vector_line(vector: dict) -> str:
    receipt = vector.get("expected") or {}
    planes = receipt.get("planes", [])
    flat = []
    for axis in range(3):
        p = next((p for p in planes if p["axis"] == axis), None)
        flat.extend([p["blocks"], p["offset"], p["length"], p["entropy_type"]] if p else [0, 0, 0, 0])
    ref = vector["accepted_ref"]
    packet_hex = vector.get("packet_hex")
    if packet_hex is None:
        packet_hex = (ROOT / vector["packet_path"]).read_bytes().hex()
    vals = [vector["id"], vector["expected_error"], packet_hex,
            int(ref["valid"]), ref["fid"], ref["generation"], int(ref["qcache_valid"]),
            receipt.get("fid", 0), receipt.get("refid", 0), receipt.get("generation", 0),
            int(receipt.get("key", False)), receipt.get("mode_bytes", 0), receipt.get("qmap_bytes", 0),
            receipt.get("hud_bytes", 0), receipt.get("data_bytes", 0), *flat,
            receipt.get("qmap_required", 0)]
    return "\t".join(str(v) for v in vals)


def build_vectors(hidden: tuple[int, ...]):
    pos_dir = VECTORS / "positive"
    neg_dir = VECTORS / "negative"
    pos_dir.mkdir(parents=True, exist_ok=True)
    neg_dir.mkdir(parents=True, exist_ok=True)
    for directory in (pos_dir, neg_dir):
        for stale in directory.iterdir():
            if stale.is_file():
                stale.unlink()
    entries = []
    fixture_rows = fixture_sources()
    actual_entries = []
    for serial, (origin, cohort, fid, source_path, source_row, prior_row) in enumerate(fixture_rows):
        packet = source_path.read_bytes()
        ref, ref_evidence = accepted_snapshot(cohort, fid, source_row, prior_row, origin)
        code, receipt, detail = parse_expected(packet, ref, hidden)
        target = (pos_dir if code == 0 else neg_dir) / f"fixture-{serial:03d}-{origin}-c{cohort}-f{fid}-{source_path.stem.split('-', 2)[2]}.bin"
        target.write_bytes(packet)
        actual_entries.append(dict(id=f"actual_{serial:03d}", class_="retained_actual_fixture", origin=origin,
                                   cohort=cohort, fid=fid, source_fixture_path=str(source_path.relative_to(ROOT)),
                                   source_sha256=source_sha(source_path), packet_path=str(target.relative_to(ROOT)),
                                   packet_bytes=len(packet), packet_sha256=sha(packet), accepted_ref=ref,
                                   accepted_ref_evidence=ref_evidence, expected_error=code,
                                   expected_error_name=ERRORS[code], expected=receipt, error_detail=detail,
                                   packet_policy_disposition="within_49152" if len(packet) <= CAP else "over_49152"))
    if len(actual_entries) != 51 or any(e["packet_policy_disposition"] != "within_49152" for e in actual_entries):
        raise ValueError("retained actual fixtures must remain the 35+16 within-cap inventory")
    entries.extend(actual_entries)
    # Directed negatives on a retained delta/QM6 packet, plus QM2 run negatives on a key packet.
    delta = next(e for e in actual_entries if e["expected_error"] == 0 and not e["expected"]["key"] and e["expected"]["qmap_method"] == 6)
    delta_path = ROOT / delta["packet_path"]
    delta_packet = delta_path.read_bytes()
    negs = negative_cases(delta_path, delta_packet, delta["accepted_ref"], hidden)
    for qm2 in (e for e in actual_entries if e["expected_error"] == 0 and e["expected"]["qmap_method"] == 2):
        qp = ROOT / qm2["packet_path"]
        qpacket = qp.read_bytes()
        negs.extend(c for c in negative_cases(qp, qpacket, qm2["accepted_ref"], hidden)
                    if c["id"] in ("bad_qm_run_value", "bad_qm_required"))
        break
    for i, item in enumerate(negs):
        data = item.pop("packet")
        if item["expected_error"] == 0:
            raise ValueError(f"negative mutation unexpectedly admitted: {item['id']}")
        base_path = ROOT / item["mutation"]["base_packet"]
        base_packet = base_path.read_bytes()
        path = neg_dir / f"neg-{i:02d}-{item['id']}.bin"
        path.write_bytes(data)
        source_entry = next(e for e in actual_entries if ROOT / e["packet_path"] == base_path)
        entries.append({**item, "class_": "negative", "origin": "directed_mutation",
                        "packet_path": str(path.relative_to(ROOT)), "packet_bytes": len(data),
                        "packet_sha256": sha(data), "source_fixture_path": source_entry["source_fixture_path"],
                        "source_sha256": source_entry["source_sha256"], "cohort": source_entry["cohort"],
                        "fid": source_entry["fid"], "accepted_ref": item["ref"],
                        "accepted_ref_evidence": source_entry["accepted_ref_evidence"],
                        "expected_error_name": ERRORS[item["expected_error"]]})
    # A malformed textual-hex row is a harness framing concern, not a packet vector;
    # RTL integration exercises error 2 separately before asserting a receipt.
    # Structural-only all-COPY delta with QM6(required=0) and exactly three empty planes.
    base = next(e for e in actual_entries if e["expected_error"] == 0 and not e["expected"]["key"])
    base_path = ROOT / base["packet_path"]
    base_packet = base_path.read_bytes()
    bitbuf = []
    for plane, plane_n in enumerate(PLANE_TILES):
        base_index = sum(PLANE_TILES[:plane])
        for begin in range(0, plane_n, 16):
            visible = any(not hidden[base_index + t] for t in range(begin, min(begin + 16, plane_n)))
            bitbuf.extend([0, 0] if visible else [1, 1])
    mode = bytearray()
    for i in range(0, len(bitbuf), 8):
        value = 0
        for j, bit in enumerate(bitbuf[i:i + 8]):
            value |= bit << (7 - j)
        mode.append(value)
    qm = bytearray(struct.pack(">4sBBHHH", b"QM87", 1, 6, 1350, 0, 0))
    qm.extend(struct.pack(">I", crc32(qm)))
    data = bytes(12)
    hud_n = int.from_bytes(base_packet[44:48], "big")
    hud_off = len(base_packet) - hud_n - 4
    hud = base_packet[hud_off:hud_off + hud_n]
    fid, refid, generation = base["accepted_ref"]["fid"] + 1, base["accepted_ref"]["fid"], base["accepted_ref"]["generation"] + 1
    header = bytearray(base_packet[:128])
    struct.pack_into(">IIQ", header, 8, fid, refid, generation)
    struct.pack_into(">IIII", header, 36, len(mode), len(qm), hud_n, len(data))
    structural = bytes(header) + bytes(mode) + bytes(qm) + data + hud
    structural += struct.pack(">I", crc32(structural))
    structural_ref = dict(valid=True, fid=refid, generation=generation - 1, qcache_valid=True)
    code, receipt, detail = parse_expected(structural, structural_ref, hidden)
    if code != 0 or receipt["planes"]:
        raise ValueError(f"structural zero-residual packet rejected: {code} {detail}")
    spath = pos_dir / "structural-only-all-copy-delta-qm6-zero-residual.bin"
    spath.write_bytes(structural)
    entries.append(dict(id="structural_all_copy_zero_residual", class_="synthetic_structural_only",
                        origin="constructed packet; inherited HUD/root/seal not validated", cohort=base["cohort"],
                        fid=fid, source_fixture_path=base["source_fixture_path"], source_sha256=base["source_sha256"],
                        packet_path=str(spath.relative_to(ROOT)), packet_bytes=len(structural), packet_sha256=sha(structural),
                        accepted_ref=structural_ref, accepted_ref_evidence=dict(kind="synthetic_external_snapshot"),
                        expected_error=0, expected_error_name=ERRORS[0], expected=receipt, error_detail=None,
                        packet_policy_disposition="within_49152", claims="structural admission only; not full native-valid packet"))
    # Native key QM6 is unsupported because no prior map can be inherited.
    key = next(e for e in actual_entries if e["expected_error"] == 0 and e["expected"]["key"])
    key_path = ROOT / key["packet_path"]
    key_packet = key_path.read_bytes()
    mode_n = int.from_bytes(key_packet[36:40], "big")
    qoff = 128 + mode_n
    qlen = int.from_bytes(key_packet[40:44], "big")
    old_q = key_packet[qoff:qoff + qlen]
    required = int.from_bytes(old_q[10:12], "big")
    qm6 = bytearray(struct.pack(">4sBBHHH", b"QM87", 1, 6, 1350, 0, required))
    qm6.extend(struct.pack(">I", crc32(qm6)))
    kheader = bytearray(key_packet[:128])
    struct.pack_into(">I", kheader, 40, len(qm6))
    key_mutation = bytes(kheader) + key_packet[128:qoff] + bytes(qm6) + key_packet[qoff + qlen:-4]
    key_mutation += struct.pack(">I", crc32(key_mutation))
    key_ref = key["accepted_ref"]
    kcode, kreceipt, kdetail = parse_expected(key_mutation, key_ref, hidden)
    if kcode != 7:
        raise ValueError(f"key QM6 negative expected reference/cache error, got {kcode}:{kdetail}")
    kpath = neg_dir / "key-qm6-without-prior-cache.bin"
    kpath.write_bytes(key_mutation)
    entries.append(dict(id="key_qm6_no_inheritance", class_="negative", origin="directed_mutation",
                        cohort=key["cohort"], fid=key["fid"], source_fixture_path=key["source_fixture_path"],
                        source_sha256=key["source_sha256"], packet_path=str(kpath.relative_to(ROOT)),
                        packet_bytes=len(key_mutation), packet_sha256=sha(key_mutation), accepted_ref=key_ref,
                        accepted_ref_evidence=key["accepted_ref_evidence"], expected_error=kcode,
                        expected_error_name=ERRORS[kcode], expected=None, error_detail=kdetail,
                        negative_reason="change retained key qmap to bodyless QM6", mutation=dict(
                            base_packet=str(key_path.relative_to(ROOT)), base_sha256=sha(key_packet),
                            changed="replace QM2 with QM6 and repair both CRCs", outer_crc_recomputed=True)))
    # Stale-key identity check is meaningful with an already accepted external snapshot.
    stale_key_ref = dict(valid=True, fid=key["fid"] + 1, generation=key["expected"]["generation"] + 1, qcache_valid=True)
    scode, sreceipt, sdetail = parse_expected(key_packet, stale_key_ref, hidden)
    if scode != 6:
        raise ValueError(f"stale key expected identity error, got {scode}:{sdetail}")
    entries.append(dict(id="stale_key_snapshot", class_="negative", origin="external_snapshot_mutation",
                        cohort=key["cohort"], fid=key["fid"], source_fixture_path=key["source_fixture_path"],
                        source_sha256=key["source_sha256"], packet_path=key["packet_path"],
                        packet_bytes=key["packet_bytes"], packet_sha256=key["packet_sha256"],
                        accepted_ref=stale_key_ref, accepted_ref_evidence=dict(kind="synthetic_stale_snapshot",
                        source="same retained key packet, accepted snapshot fid/generation exceed header"),
                        expected_error=scode, expected_error_name=ERRORS[scode], expected=None,
                        error_detail=sdetail, negative_reason="present retained key packet under newer accepted snapshot",
                        mutation=dict(base_packet=key["source_fixture_path"], changed="external snapshot only",
                                      outer_crc_recomputed=False)))
    v88_result = json.loads((ROOT / "experiments/python-gamebub-v88/wire/results.json").read_text())
    v88_attempt = ROOT / v88_result["selected_report"]
    pinned = [ROOT / "experiments/python-gamebub-v88/wire/receiver.cpp",
              ROOT / "scripts/cu66-v88/verify_packets.py", ROOT / "scripts/cu66-v87/quantizer_codec.py",
              ROOT / "experiments/cu66-native-v69/generated_constants.hpp",
              ROOT / "experiments/python-gamebub-v88/entropy/data.py",
              ROOT / "experiments/python-gamebub-v88/entropy/index.json",
              ROOT / "experiments/python-gamebub-v85/residual/data.py",
              ROOT / "experiments/python-gamebub-v88/wire/results.json",
              v88_attempt, v88_attempt.with_name("frames.jsonl"),
              ROOT / "experiments/python-gamebub-v90/native/results.json",
              ROOT / "experiments/python-gamebub-v90/native/attempts/20261106T160439132762Z-32bde2e1/frames.jsonl"]
    source_pins = {str(p.relative_to(ROOT)): source_sha(p) for p in pinned}
    (VECTORS / "index.json").write_text(json.dumps(dict(schema="cu66-v91i1-admission-vectors-v1",
        source_inventory=dict(v88_actual_fixtures=35, v90_actual_fixtures=16, retained_fixture_rows=len(actual_entries),
                             unique_source_identities=len({(e["cohort"], e["fid"]) for e in actual_entries}),
                             admitted=sum(e["expected_error"] == 0 for e in actual_entries),
                             rejected=sum(e["expected_error"] != 0 for e in actual_entries)),
        error_codes={str(k): v for k, v in ERRORS.items()},
        scope="Outer CS88 admission only; no AB38/BR88 payload grammar/CRC, decode, pixel/HUD/hash verification, publication or timing claim.",
        source_pins=source_pins, entries=entries), indent=2) + "\n")
    with (VECTORS / "vectors.txt").open("w") as output:
        for vector in entries:
            output.write(vector_line(vector) + "\n")
    return entries


def main():
    hidden = fixed_hidden_mask()
    entries = build_vectors(hidden)
    counts = {}
    for e in entries:
        key = str(e["expected_error"])
        counts[key] = counts.get(key, 0) + 1
    result = dict(schema="cu66-v91i1-admission-model-results-v1", status="PASS_MODEL_FIXTURE_EXPORT",
                  model="independent Python byte-index/struct outer-admission parser",
                  model_sha256=source_sha(Path(__file__).resolve()),
                  vector_manifest="experiments/python-gamebub-v91i/vectors/index.json",
                  rtl_rows="experiments/python-gamebub-v91i/vectors/vectors.txt",
                  vector_manifest_sha256=source_sha(VECTORS / "index.json"),
                  rtl_rows_sha256=source_sha(VECTORS / "vectors.txt"),
                  fixture_rows=sum(e["class_"] == "retained_actual_fixture" for e in entries),
                  directed_negative_rows=sum(e["class_"] == "negative" for e in entries),
                  rows_by_expected_error=counts,
                  admitted_actual_fixtures=sum(e["class_"] == "retained_actual_fixture" and e["expected_error"] == 0 for e in entries),
                  over_budget_actual_fixtures=sum(e["class_"] == "retained_actual_fixture" and e["expected_error"] == 1 for e in entries),
                  unsupported_actual_profiles=sum(e["class_"] == "retained_actual_fixture" and e["expected_error"] == 4 for e in entries),
                  claims=["emits bounded structural descriptors only", "no entropy decode or inner CRC validation",
                          "no accepted-state mutation or publication", "no timing/performance qualification"])
    (AREA / "admission-results.json").write_text(json.dumps(result, indent=2) + "\n")
    print(result["status"], "fixtures", result["fixture_rows"], "negative", result["directed_negative_rows"],
          "codes", json.dumps(counts, sort_keys=True))


if __name__ == "__main__":
    main()
