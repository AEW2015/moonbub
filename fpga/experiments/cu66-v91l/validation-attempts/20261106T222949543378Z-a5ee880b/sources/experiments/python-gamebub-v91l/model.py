#!/usr/bin/env python3
"""V91l independent C2 hash oracle and retained actual-frame vector exporter.

Canonical bytes come from the digest-verified V82 native archive.  CS88 packet
bytes are retained V90 proxy_LOW selections.  HUD semantic words come from the
accepted V69 native history decode and are rehashed here with hashlib; the RTL
checkpoint consumes the original current HUD packet and must decode it itself.
"""
from __future__ import annotations

import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import sys
import zlib

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / "experiments/python-gamebub-v91l"
VECTORS = AREA / "vectors"
V82 = ROOT / "experiments/python-gamebub-v82/native"
V69 = ROOT / "experiments/cu66-native-v69"
V90 = ROOT / "experiments/python-gamebub-v90/native/attempts/20261106T160439132762Z-32bde2e1"
V90_ROWS = V90 / "frames.jsonl"
V69_HEADER = struct.Struct("<4sBBHIIHH16s16s16sII")
TILES = (5400, 1350, 1350)
WIDTHS = (720, 360, 360)
HEIGHTS = (480, 240, 240)
NO_REF = 0xFFFFFFFF
CONTEXT = hashlib.sha256(
    b'{"geometry":[720,480,5400,1350,1350],"granularity":16,'
    b'"profile_id":"CU66-V82-CONTENT-SHA256-TREE-2"}'
).digest()
DOMAIN = b"CU66V82C2\x00"
CASE_ORDER = ((0, 0), (0, 1), (0, 2), (0, 3), (3, 48), (3, 49), (3, 50))
PRIMARY = {(0, 0), (0, 1), (0, 3), (3, 50)}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    return sha(path.read_bytes())


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load source archive module {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def le_u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def be_u32(data: bytes, offset: int) -> int:
    return struct.unpack_from(">I", data, offset)[0]


def extract_cs88(packet: bytes) -> dict:
    if len(packet) < 132 or packet[:4] != b"CS88":
        raise ValueError("CS88 framing")
    if zlib.crc32(packet[:-4]) & 0xFFFFFFFF != be_u32(packet, len(packet) - 4):
        raise ValueError("CS88 outer CRC")
    flags, group, mode = packet[5], packet[6], packet[7]
    fid, refid = be_u32(packet, 8), be_u32(packet, 12)
    generation = struct.unpack_from(">Q", packet, 16)[0]
    width, height, block, reserved = struct.unpack_from(">HHHH", packet, 24)
    cap, mode_n, qm_n, hud_n, residual_n = struct.unpack_from(">IIIII", packet, 32)
    if (flags not in (0, 1) or group != 16 or width != 720 or height != 480
            or block != 32 or reserved != 0 or cap != 65536):
        raise ValueError("CS88 fixed V90 profile")
    if packet[116:128] != bytes(12):
        raise ValueError("CS88 reserved bytes")
    hud_at = 128 + mode_n + qm_n + residual_n
    if hud_at + hud_n + 4 != len(packet):
        raise ValueError("CS88 exact body lengths")
    return dict(fid=fid, refid=refid, generation=generation, key=bool(flags),
                group=group, mode=mode, width=width, height=height,
                mode_bytes=mode_n, qm_bytes=qm_n, residual_bytes=residual_n,
                hud_bytes=hud_n, hud_at=hud_at, hud=packet[hud_at:hud_at + hud_n],
                root=packet[52:84], seal=packet[84:116])


def extract_v69_hud(packet_path: Path, cohort: int, fid: int, refid: int,
                    is_key: bool) -> bytes:
    packet = packet_path.read_bytes()
    if len(packet) < V69_HEADER.size + 4:
        raise ValueError("V69 history packet short")
    fields = V69_HEADER.unpack_from(packet)
    magic, version, flags, epoch, got_fid, got_refid, width, height = fields[:8]
    body_n, hud_n = fields[-2:]
    if (magic, version, epoch, got_fid, got_refid, width, height) != (
            b"CU66", 1, 25, fid, refid, 720, 480):
        raise ValueError("V69 accepted history identity")
    if bool(flags & 1) != is_key or V69_HEADER.size + body_n + hud_n + 4 != len(packet):
        raise ValueError("V69 history framing")
    start = V69_HEADER.size + body_n
    return packet[start:start + hud_n]


def raster_planes(tiles: tuple[bytes, ...]) -> tuple[bytes, bytes, bytes]:
    if len(tiles) != sum(TILES) or any(len(tile) != 64 for tile in tiles):
        raise ValueError("actual canonical tile shape")
    output = []
    base = 0
    for axis, (count, width, height) in enumerate(zip(TILES, WIDTHS, HEIGHTS, strict=True)):
        plane = bytearray(width * height)
        tile_w = width // 8
        for index in range(count):
            tile = tiles[base + index]
            by, bx = divmod(index, tile_w)
            for y in range(8):
                dst = (by * 8 + y) * width + bx * 8
                plane[dst:dst + 8] = tile[y * 8:y * 8 + 8]
        output.append(bytes(plane))
        base += count
    return tuple(output)


def c2_root(tiles: tuple[bytes, ...]) -> bytes:
    nodes: list[bytes | None] = [None] * 1024
    leaf = 0
    base = 0
    for axis, count in enumerate(TILES):
        for start in range(0, count, 16):
            number = min(16, count - start)
            payload = b"".join(tiles[base + t] for t in range(start, start + number))
            msg = DOMAIN + b"L\x00" + CONTEXT + struct.pack(">BIH", axis, start, number) + payload
            nodes[512 + leaf] = hashlib.sha256(msg).digest()
            leaf += 1
        base += count
    if leaf != 508:
        raise ValueError("C2 profile leaf count")
    for index in range(leaf, 512):
        nodes[512 + index] = hashlib.sha256(
            DOMAIN + b"E\x00" + CONTEXT + struct.pack(">II", index, 512)
        ).digest()
    level = 1
    width = 256
    while width:
        for index in range(width):
            left = nodes[2 * (width + index)]
            right = nodes[2 * (width + index) + 1]
            assert left is not None and right is not None
            msg = DOMAIN + b"N\x00" + struct.pack(">HI", level, index) + left + right
            nodes[width + index] = hashlib.sha256(msg).digest()
        width //= 2
        level += 1
    assert nodes[1] is not None
    return nodes[1]


def c2_seal(header: dict, previous_root: bytes, hud_sha: bytes,
            root: bytes) -> bytes:
    message = (DOMAIN + b"S\x00" + CONTEXT
               + struct.pack(">IIBQ", header["fid"], header["refid"],
                             int(header["key"]), header["generation"])
               + previous_root + hud_sha + root)
    if len(message) != 157:
        raise ValueError("C2 seal message shape")
    return hashlib.sha256(message).digest()


def native_rows() -> dict[tuple[int, int], dict]:
    rows = {}
    with V90_ROWS.open() as stream:
        for line in stream:
            row = json.loads(line)
            if row["policy"] == "proxy_LOW":
                key = (row["cohort"], row["fid"])
                rows[key] = row
    return rows


def v69_rows() -> dict[tuple[int, int], tuple[Path, str, str]]:
    result = {}
    for line in (V69 / "index.tsv").read_text().splitlines():
        case, fid, path, canonical, hud, _display = line.split("\t")
        result[(int(case), int(fid))] = (V69 / path, canonical, hud)
    return result


def actual_frames() -> dict[tuple[int, int], dict]:
    data = load_module("v91l_v82_native_data", V82 / "data.py")
    return {(frame["cohort"], frame["fid"]): frame for frame in data.iter_frames()}


def check_packet_mutation(packet: bytes, at: int, xor: int = 1) -> bytes:
    changed = bytearray(packet)
    changed[at] ^= xor
    changed[-4:] = struct.pack(">I", zlib.crc32(changed[:-4]) & 0xFFFFFFFF)
    return bytes(changed)


def write_vectors(frames: dict, native: dict, v69: dict) -> dict:
    rows = []
    computed = {}
    previous_roots: dict[int, bytes] = {}
    for cohort, fid in CASE_ORDER:
        ident = (cohort, fid)
        data = frames[ident]
        packet_path = VECTORS / "packets" / f"c{cohort}-f{fid}.cs88"
        hud_path = VECTORS / "hud-history" / f"c{cohort}-f{fid}.u16le"
        packet, hud_words = packet_path.read_bytes(), hud_path.read_bytes()
        header = extract_cs88(packet)
        if (header["fid"], header["refid"], header["key"]) != (
                fid, data["refid"], data["key"]):
            raise ValueError(f"packet/archive identity mismatch {ident}")
        if header["generation"] == 0:
            raise ValueError(f"zero generation {ident}")
        native_row = native[ident]
        if sha(packet) != native_row["packet_sha256"]:
            raise ValueError(f"packet differs from retained V90 selection {ident}")
        if len(hud_words) != 21120 * 2:
            raise ValueError(f"semantic HUD word byte count {ident}")
        hud_sha = hashlib.sha256(hud_words).digest()
        if hud_sha.hex() != data["hud_sha256"] or hud_sha.hex() != native_row["decoded"]["hud_sha256"]:
            raise ValueError(f"accepted-history HUD words mismatch {ident}")
        old_path, _old_canonical_sha, old_hud_sha = v69[ident]
        old_hud = extract_v69_hud(old_path, cohort, fid, data["refid"], data["key"])
        if old_hud != header["hud"] or sha(old_hud) != sha(header["hud"]):
            raise ValueError(f"actual CS88 HUD bytes differ from V69 source history {ident}")
        if old_hud_sha != data["hud_sha256"]:
            raise ValueError(f"V69 accepted-history HUD digest mismatch {ident}")
        tiles = tuple(data["tiles"])
        planes = raster_planes(tiles)
        raster = b"".join(planes)
        raster_sha = sha(raster)
        if raster_sha != data["canonical_sha256"] or raster_sha != native_row["decoded"]["canonical_sha256"]:
            raise ValueError(f"actual canonical raster mismatch {ident}")
        root = c2_root(tiles)
        if header["key"]:
            previous = bytes(32)
        else:
            if header["refid"] not in previous_roots:
                raise ValueError(f"missing actual accepted C2 predecessor {ident}")
            previous = previous_roots[header["refid"]]
        seal = c2_seal(header, previous, hud_sha, root)
        if root != header["root"] or seal != header["seal"]:
            raise ValueError(f"independent C2 computation disagrees with actual packet {ident}")
        if root.hex() != native_row["decoded"]["root"] or seal.hex() != native_row["decoded"]["seal"]:
            raise ValueError(f"V90 full-history C2 replay mismatch {ident}")
        previous_roots[fid] = root
        computed[ident] = dict(header=header, tiles=tiles, hud_words=hud_words,
                               root=root, seal=seal)
        role = "primary" if ident in PRIMARY else "historical_reference_bootstrap"
        row_id = f"c{cohort}_f{fid}"
        rows.append((row_id, cohort, role, packet.hex(), b"".join(tiles).hex(),
                     hud_words.hex(), raster_sha, hud_sha.hex(), root.hex(), seal.hex()))

    output = VECTORS / "validation.tsv.gz"
    header = ("id", "cohort", "role", "packet_hex", "canonical_tiles_hex",
              "hud_words_le_hex", "canonical_raster_sha256", "hud_semantic_sha256",
              "computed_root_hex", "computed_seal_hex")
    with output.open("wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0, filename="") as stream:
            stream.write(("\t".join(header) + "\n").encode())
            for row in rows:
                stream.write(("\t".join(map(str, row)) + "\n").encode())

    negatives = []
    source = (VECTORS / "packets" / "c0-f0.cs88").read_bytes()
    packet_info = extract_cs88(source)
    mutations = {
        "bad_hud_payload_crc": packet_info["hud_at"] + 112,
        "bad_packet_fid": 8,
        "bad_reference_id": 12,
        "bad_generation": 16,
        "bad_expected_root": 52,
        "bad_expected_seal": 84,
    }
    negative_dir = VECTORS / "negative"
    negative_dir.mkdir(parents=True, exist_ok=True)
    for name, offset in mutations.items():
        damaged = check_packet_mutation(source, offset)
        damaged_info = extract_cs88(damaged)
        if name == "bad_hud_payload_crc":
            body = damaged_info["hud"]
            if zlib.crc32(body[:-4]) & 0xFFFFFFFF == struct.unpack_from("<I", body, len(body) - 4)[0]:
                raise AssertionError("HUD payload mutation did not break its inner CRC")
        elif name == "bad_expected_root":
            if damaged_info["root"] == computed[(0, 0)]["root"]:
                raise AssertionError("root mutation did not diverge from computed root")
        elif name == "bad_expected_seal":
            if damaged_info["seal"] == computed[(0, 0)]["seal"]:
                raise AssertionError("seal mutation did not diverge from computed seal")
        elif name == "bad_packet_fid" and damaged_info["fid"] == 0:
            raise AssertionError("frame identity mutation did not change fid")
        elif name == "bad_reference_id" and damaged_info["refid"] == NO_REF:
            raise AssertionError("reference identity mutation did not change refid")
        elif name == "bad_generation" and damaged_info["generation"] == computed[(0, 0)]["header"]["generation"]:
            raise AssertionError("generation mutation did not change generation")
        dest = negative_dir / f"{name}.cs88"
        dest.write_bytes(damaged)
        negatives.append(dict(name=name, path=str(dest.relative_to(ROOT)),
                              mutation_offset=offset, expected="reject",
                              sha256=sha(damaged)))
    hud_epoch = bytearray(source)
    hud_at = packet_info["hud_at"]
    hud_epoch[hud_at + 6] ^= 1
    # HUD CRC32 is little endian; outer CS88 CRC32 is big endian.
    hud_end = hud_at + packet_info["hud_bytes"]
    hud_epoch[hud_end - 4:hud_end] = struct.pack("<I", zlib.crc32(hud_epoch[hud_at:hud_end - 4]))
    hud_epoch[-4:] = struct.pack(">I", zlib.crc32(hud_epoch[:-4]) & 0xFFFFFFFF)
    if struct.unpack_from("<I", hud_epoch, hud_at + 6)[0] == 25:
        raise AssertionError("HUD epoch mutation did not change epoch")
    dest = negative_dir / "bad_hud_epoch.cs88"
    dest.write_bytes(hud_epoch)
    negatives.append(dict(name="bad_hud_epoch", path=str(dest.relative_to(ROOT)),
                          mutation_offset=hud_at + 6, expected="reject", sha256=sha(bytes(hud_epoch))))
    semantic = bytearray((VECTORS / "hud-history" / "c0-f0.u16le").read_bytes())
    semantic[0] ^= 1
    changed_hud_sha = hashlib.sha256(semantic).digest()
    if c2_seal(computed[(0, 0)]["header"], bytes(32), changed_hud_sha,
               computed[(0, 0)]["root"]) == computed[(0, 0)]["seal"]:
        raise AssertionError("semantic HUD mutation did not change computed seal")
    dest = negative_dir / "bad_semantic_hud_word.u16le"
    dest.write_bytes(semantic)
    negatives.append(dict(name="bad_semantic_hud_word", path=str(dest.relative_to(ROOT)),
                          mutation_offset=0, expected="root/seal mismatch", sha256=sha(bytes(semantic))))
    canonical = bytearray(b"".join(computed[(0, 0)]["tiles"]))
    canonical[0] ^= 1
    changed_tiles = (bytes(canonical[:64]),) + computed[(0, 0)]["tiles"][1:]
    if c2_root(changed_tiles) == computed[(0, 0)]["root"]:
        raise AssertionError("canonical tile mutation did not change computed root")
    dest = negative_dir / "bad_canonical_tile_byte.bin"
    dest.write_bytes(canonical)
    negatives.append(dict(name="bad_canonical_tile_byte", path=str(dest.relative_to(ROOT)),
                          mutation_offset=0, expected="root mismatch", sha256=sha(bytes(canonical))))
    negative_index = VECTORS / "negative" / "index.json"
    negative_index.write_text(json.dumps(dict(schema="cu66-v91l-negative-vectors-v1", cases=negatives), indent=2) + "\n")
    return dict(vector_file=str(output.relative_to(ROOT)), vector_sha256=sha_file(output),
                vector_bytes=output.stat().st_size, rows=len(rows), columns=len(header),
                row_ids=[r[0] for r in rows], roles={role: sum(r[2] == role for r in rows)
                                                     for role in ("primary", "historical_reference_bootstrap")},
                negative_cases=negatives, negative_index_sha256=sha_file(negative_index))


def main() -> None:
    frames, native, v69 = actual_frames(), native_rows(), v69_rows()
    result = write_vectors(frames, native, v69)
    source_paths = [
        Path(__file__), V82 / "data.py", V82 / "index.json",
        V90_ROWS, V69 / "index.tsv", V69 / "decoder.hpp", V69 / "hud.hpp",
        ROOT / "experiments/python-gamebub-v88/wire/receiver.cpp",
        VECTORS / "source-export/v91l_v69_hud_export.cpp",
        VECTORS / "source-export/v91l_make_packets.py",
    ]
    for cohort, fid in CASE_ORDER:
        source_paths.extend((VECTORS / "packets" / f"c{cohort}-f{fid}.cs88",
                             VECTORS / "hud-history" / f"c{cohort}-f{fid}.u16le"))
        source_paths.append(v69[(cohort, fid)][0])
    sources = {str(path.relative_to(ROOT)): sha_file(path) for path in sorted(set(source_paths))}
    report = dict(schema="cu66-v91l-python-hash-oracle-v1", status="PASS_ACTUAL_FRAME_HASH_ORACLE",
                  baseline_revision="1e974dcaab4b86646b0480f8987d3469316c06b3",
                  source_sha256=sources, **result,
                  c2_profile=dict(context_sha256=CONTEXT.hex(), leaf_count=508, tree_leaves=512,
                                  group_tiles=16, hash="SHA-256", byte_order="big-endian metadata"),
                  scope=["Seven actual CS88 history rows: four V91k identities, c0-f2 bridge, and c3 key48/f49 accepted-reference bootstrap.",
                         "Canonical bytes are digest-verified actual V82 archived tiles; direct C2 roots and seals are computed with Python hashlib/struct.",
                         "HUD semantic word bytes are actual accepted V69 history decode outputs; current HUD packet bodies are byte-compared to accepted V69 source history.",
                         "This is an independent software hash oracle and source-backed fixture exporter. It does not claim RTL HUD decode, full-frame RTL publication, hardware timing or 30 fps."],
                  actual_history_rows=len(native), unique_actual_source_frames=7,
                  physical_30fps_proven=False, full_frame_RTL_publication_proven=False)
    (AREA / "model-results.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("status", "rows", "columns", "vector_bytes", "negative_cases")}, indent=2))


if __name__ == "__main__":
    main()
