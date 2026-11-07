#!/usr/bin/env python3
"""Independent selected CS88 packet/BR88/QM87/C2 audit; no producer import."""
from __future__ import annotations
import argparse
from collections import Counter
import datetime as dt
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import sys
import zlib

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / "experiments/python-gamebub-v99"
BASELINE = "35949d6f41366cd5725b433a136fadb1b6ce95f6"
HIDDEN = "e08b9861ae9a170c913c6425a5773ff42042a0abfe2fef8cd756cb505a8a8fa5"
PREFIX = struct.Struct(">4sBBBBIIQHHHHIIIII")
DOMAIN = b"CU66V82C2\0"
CONTEXT = hashlib.sha256(b'{"geometry":[720,480,5400,1350,1350],"granularity":16,"profile_id":"CU66-V82-CONTENT-SHA256-TREE-2"}').digest()


def need(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def path(value):
    value = Path(value)
    return value.resolve() if value.is_absolute() else (ROOT / value).resolve()


class Reader:
    def __init__(self, raw):
        self.raw, self.at = raw, 0

    def take(self, size):
        need(size >= 0 and self.at + size <= len(self.raw), "truncated CS88 component")
        value = self.raw[self.at:self.at+size]
        self.at += size
        return value

    def u32(self):
        return int.from_bytes(self.take(4), "big")

    def end(self):
        need(self.at == len(self.raw), "trailing CS88 component")


def crc(raw):
    need(len(raw) >= 4 and zlib.crc32(raw[:-4]) == int.from_bytes(raw[-4:], "big"), "CS88/QM87 CRC mismatch")


def modes(body, key, method, hidden):
    if key:
        need(method == 0 and not body, "selected implicit key mode")
        return np.where(hidden, 1, 2).astype(np.uint8)
    need(method == 3, "selected P grouped mode")
    result = np.ones(8100, dtype=np.uint8)
    bitpos = 0

    def bit():
        nonlocal bitpos
        need(bitpos < len(body)*8, "grouped mode truncated")
        value = (body[bitpos//8] >> (7-bitpos % 8)) & 1
        bitpos += 1
        return value

    offset = 0
    for count in (5400, 1350, 1350):
        for start in range(0, count, 16):
            tag = 2*bit()+bit()
            indices = [offset+i for i in range(start, min(start+16, count)) if not hidden[offset+i]]
            if not indices:
                need(tag == 3, "grouped all-hidden tag")
            elif tag < 2:
                result[indices] = 2 if tag else 0
            else:
                need(tag == 2, "grouped reserved tag on visible group")
                bits = [bit() for _ in indices]
                need(0 < sum(bits) < len(indices), "noncanonical grouped mixed tag")
                result[indices] = np.asarray(bits, dtype=np.uint8)*2
        offset += count
    need((bitpos+7)//8 == len(body), "grouped mode exact bytes")
    while bitpos < len(body)*8:
        need(bit() == 0, "grouped mode nonzero padding")
    return result


def quantizers(raw, operations, previous, key):
    crc(raw)
    need(16 <= len(raw) <= 354, "QM87 bounds")
    magic, version, method, cells, length, required = struct.unpack(">4sBBHHH", raw[:12])
    need(magic == b"QM87" and version == 1 and method in (2, 6) and cells == 1350 and len(raw) == length+16,
         "selected QM87 header")
    active = set()
    for tile in np.flatnonzero(operations == 2):
        tile = int(tile)
        active.add(((tile//90)//2)*45+(tile % 90)//2 if tile < 5400 else (tile-5400) % 1350)
    need(required == len(active), "QM87 required cells")
    if method == 6:
        need(not key and previous is not None and length == 0, "QM87 inherited accepted state")
        return previous.copy(), method
    values = []
    for code in raw[12:-4]:
        value, count = code >> 6, (code & 63)+1
        need(value <= 2 and len(values)+count <= 1350, "QM87 run value/coverage")
        values.extend([value]*count)
    need(len(values) == 1350, "QM87 full 1350-cell coverage")
    return np.asarray(values, dtype=np.uint8), method


def c2_root(planes):
    leaves = []
    for axis, plane in enumerate(planes):
        height, width = plane.shape
        tiles = plane.reshape(height//8, 8, width//8, 8).transpose(0, 2, 1, 3).reshape(-1, 64)
        for start in range(0, len(tiles), 16):
            count = min(16, len(tiles)-start)
            message = DOMAIN+b"L\0"+CONTEXT+struct.pack(">BIH", axis, start, count)+tiles[start:start+count].tobytes()
            leaves.append(hashlib.sha256(message).digest())
    need(len(leaves) == 508, "C2 real leaves")
    for index in range(508, 512):
        leaves.append(hashlib.sha256(DOMAIN+b"E\0"+CONTEXT+struct.pack(">II", index, 512)).digest())
    level = 1
    while len(leaves) > 1:
        leaves = [hashlib.sha256(DOMAIN+b"N\0"+struct.pack(">HI", level, i//2)+leaves[i]+leaves[i+1]).digest()
                  for i in range(0, len(leaves), 2)]
        level += 1
    return leaves[0]


def hud_words(raw):
    need(len(raw) >= 5 and struct.unpack_from("<HH", raw) == (720, 480), "fresh HUD geometry")
    reader = Reader(raw[5:])
    words = bytearray()
    for _ in range(raw[4]):
        x, y, w, h = struct.unpack("<4H", reader.take(8))
        need(w and h and x+w <= 720 and y+h <= 480, "fresh HUD rectangle")
        words.extend(reader.take(2*w*h))
    reader.end()
    return sha(words)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=AREA / "audit-cs88.json")
    args = parser.parse_args()
    output = {"schema": "v99-independent-selected-cs88-audit-v1", "status": "FAIL",
              "auditor_source_path": str(Path(__file__).resolve().relative_to(ROOT)),
              "auditor_source_sha256": sha(Path(__file__).read_bytes()),
              "started_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "pins": {}, "frames": [],
              "limits": ["Source grammar subset and host native software parity only; no new RTL simulation.",
                         "Independent Python BR88 coefficient decode and C2 hashing; full pixel reconstruction authority remains pinned native receivers.",
                         "Numeric pixel audit is pinned separately; no subjective quality, FPGA timing, calibrated link, SRAM or physical30fps claim.",
                         "49152-byte eligibility requires every original frame in a causal chain, including any skipped CU66 input."]}
    pins, counts = output["pins"], Counter()

    def pin(name, expected=None):
        name = path(name)
        raw = name.read_bytes()
        hashed = sha(raw)
        need(expected is None or hashed == expected, f"file hash differs: {name}")
        pins[str(name)] = {"sha256": hashed, "bytes": len(raw)}
        counts["file_hash_checks"] += 1
        return raw

    def document(name, expected=None):
        return json.loads(pin(name, expected))

    try:
        selected = document(args.report)
        attempt = path(args.report).parent
        output["selected_report_path"] = str(path(args.report))
        need(selected["status"] == "PASS_FRESH_NATIVE_CS88_PARITY" and selected["profile"] == "v91-group3", "wrong selected CS88 report")
        need(selected["physical_packet_cap"] == 49152 and selected["native_research_packet_cap"] == 2097152,
             "CS88 cap scope")
        for source, expected in selected["source_sha256"].items():
            pin(source, expected)
            pin(attempt / "sources" / source, expected)
            counts["live_and_snapshot_source_pairs"] += 1
        for record in selected["inputs"]:
            pin(record["path"], record["sha256"])
        for name, expected in selected["artifacts_sha256"].items():
            pin(attempt / name, expected)
        for name, binary in selected["binaries"].items():
            need(binary["path"].startswith("/build/"), "unexpected external binary path")
            actual_path = Path("/home/lori/gamebub-build/cu66-v69") / binary["path"][len("/build/"):]
            pin(actual_path, binary["sha256"])
            counts["external_binary_hashes"] += 1
        codec_path = ROOT / "experiments/python-gamebub-v88/entropy/codec.py"
        baseline_codec = subprocess.check_output(["git", "show", f"{BASELINE}:experiments/python-gamebub-v88/entropy/codec.py"], cwd=ROOT)
        pin(codec_path, sha(baseline_codec))
        spec = importlib.util.spec_from_file_location("v99_audit_independent_br88", codec_path)
        codec = importlib.util.module_from_spec(spec)
        sys.dont_write_bytecode = True
        spec.loader.exec_module(codec)
        output["independent_BR88_reader"] = {"path": str(codec_path), "baseline_commit": BASELINE, "sha256": sha(baseline_codec)}
        fresh_index = document(AREA / "fresh/index.json")
        fresh = document(fresh_index["attempt_json"], fresh_index["sha256"])
        fresh_attempt = path(fresh["attempt"])
        native_audit = document(AREA / "audit-native.json")
        need(native_audit["status"] == "PASS_INDEPENDENT_NATIVE_PIXEL_AUDIT", "native pixel audit not passed")
        pin(native_audit["auditor_source_path"], native_audit["auditor_source_sha256"])
        native_receipt = document(native_audit["native_receipt_path"], native_audit["pins"][native_audit["native_receipt_path"]]["sha256"])
        native_obs_path = path(native_audit["native_receipt_path"]).parent / "observations.jsonl"
        native_obs = [json.loads(line) for line in pin(native_obs_path, native_receipt["observations_sha256"]).splitlines()]
        native_by_key = {(r["clip_id"], r["frame_id"]): r for r in native_obs}
        ledger = [json.loads(line) for line in pin(fresh["ledger_path"], fresh["ledger_sha256"]).splitlines()]
        fresh_by_key = {(r["clip_id"], r["frame_id"]): r for r in ledger}
        rows = [json.loads(line) for line in pin(attempt / "frames.jsonl").splitlines()]
        need(len(rows) == len(fresh_by_key) == len(native_by_key) == selected["received_packets"] == 360, "full CS88/native/fresh row count")
        skipped = [json.loads(line) for line in pin(attempt / "skipped.jsonl").splitlines()]
        need(not skipped and fresh["rejected_frames"] == selected["CU66_rejected_frames"] == 0, "unexpected skipped original input")
        states, chains, seen, oversize = {}, {}, set(), []

        def decode_packet(packet, hidden, previous_qmap):
            crc(packet)
            need(132 <= len(packet) <= 2097152, "CS88 diagnostic size")
            header = PREFIX.unpack(packet[:PREFIX.size])
            (magic, version, key, granularity, method, fid, rid, generation, width, height,
             block, reserved, cap, nm, nq, nh, nd) = header
            need((magic, version, granularity, width, height, block, reserved, cap) ==
                 (b"CS88", 1, 16, 720, 480, 32, 0, 65536) and key in (0, 1), "selected CS88 prefix")
            need(packet[116:128] == bytes(12), "CS88 reserved bytes")
            need(128+nm+nq+nd+nh+4 == len(packet) and nm <= 976 and 16 <= nq <= 354 and 110 <= nh <= 49152,
                 "CS88 component lengths")
            body = Reader(packet[128:-4])
            mode = body.take(nm)
            operations = modes(mode, bool(key), method, hidden)
            qraw = body.take(nq)
            scales, qmethod = quantizers(qraw, operations, previous_qmap, bool(key))
            residual = Reader(body.take(nd))
            dense = np.zeros((8100, 64), dtype="<i2")
            offset, payload_bytes, directory_bytes, chunk_count = 0, 0, 12, 0
            for count in (5400, 1350, 1350):
                selected_indices = np.flatnonzero(operations[offset:offset+count] == 2)+offset
                chunks = residual.u32()
                need(chunks == int(bool(len(selected_indices))), "selected chunk count")
                if chunks:
                    nblocks, length = residual.u32(), residual.u32()
                    need(nblocks == len(selected_indices) and 46 <= length <= 46+128*nblocks, "CS88 BR88 chunk binding")
                    payload = residual.take(length)
                    need(payload[:4] == b"BR88", "all-BR88 selected profile")
                    values = codec.decode(payload, nblocks, 1)
                    dense[selected_indices] = np.asarray(values, dtype="<i2").reshape(nblocks, 64)
                    payload_bytes += length
                    directory_bytes += 8
                    chunk_count += 1
                offset += count
            residual.end()
            hud = body.take(nh)
            body.end()
            counts["independent_BR88_chunks"] += chunk_count
            return dict(header=header, operations=operations, scales=scales, qraw=qraw, qmethod=qmethod,
                        dense=dense, hud=hud, root=packet[52:84], seal=packet[84:116],
                        components=dict(header=128, mode_body=nm, qmap=nq, chunk_directory=directory_bytes,
                                        BR88_payloads=payload_bytes, HUD=nh, outer_CRC=4))

        for number, row in enumerate(rows):
            key = (row["clip_id"], row["frame_id"])
            need(key not in seen and key in fresh_by_key and key in native_by_key, "duplicate/unknown CS88 frame")
            seen.add(key)
            entry, native_row = fresh_by_key[key], native_by_key[key]
            need(row["quant_scale"] == entry["quant_scale"] and row["source_rgb_sha256"] == entry["source_rgb_sha256"] and
                 row["CU66_wire_bytes"] == entry["bytes"], "CS88 source/quantization metadata differs from fresh input")
            state = states.get(row["chain"])
            component_path = path(row["fresh_components"]["path"])
            component_expected = fresh["artifact_sha256"][str(component_path.relative_to(fresh_attempt))]
            pin(component_path, component_expected)
            need(component_expected == row["fresh_components"]["sha256"] and component_path == path(entry["rtl_components_path"]), "fresh component authority")
            with np.load(component_path, allow_pickle=False) as archive:
                coefficients = np.concatenate([archive["coefficients_"+axis] for axis in "yuv"]).astype("<i2")
                planes = [archive["plane_"+axis].copy() for axis in "yuv"]
                expected_ops = archive["operations"].copy()
                packed_qmap = archive["qmap"].tobytes()
                hud_envelope = archive["hud"].tobytes()
                need(int(archive["frame_id"]) == key[1] and int(archive["reference_id"]) == entry["reference_id"] and
                     bool(archive["key"]) == entry["key"] and int(archive["block_size"]) == 32, "NPZ identity")
            hidden = expected_ops == 1
            need(expected_ops.shape == (8100,) and sha(hidden.astype(np.uint8).tobytes()) == HIDDEN,
                 "fixed independently checked hidden mask")
            need(coefficients.shape == (8100, 64) and np.all(np.abs(coefficients.astype(np.int32)) <= 2048) and not np.any(coefficients[hidden]),
                 "fresh coefficient shape/range/hidden-zero")
            canonical = b"".join(plane.tobytes() for plane in planes)
            need(sha(canonical) == entry["expected"]["canonical_sha256"] == native_row["canonical_sha256"], "canonical NPZ/native authority")
            for name in ("canonical_sha256", "hud_sha256", "rgb565_sha256", "canonical_tag"):
                need(entry["expected"][name] == native_row[name], "native fresh golden equality")
            actual_native_gzip = pin(native_row["display_rgb565_path"], native_row["display_rgb565_file_sha256"])
            actual_native_display = gzip.decompress(actual_native_gzip)
            need(len(actual_native_display) == 691200 and sha(actual_native_display) == entry["expected"]["rgb565_sha256"], "actual native display authority")
            hud_golden = path(entry["hud_path"])
            full_hud = pin(hud_golden, fresh["artifact_sha256"][str(hud_golden.relative_to(fresh_attempt))])
            full_hud = gzip.decompress(full_hud) if hud_golden.suffix == ".gz" else full_hud
            need(sha(full_hud) == entry["expected"]["hud_sha256"], "full geometry/rectangle HUD hash")
            words_sha = hud_words(full_hud)
            packet = pin(attempt / row["packet_path"], row["packet_sha256"])
            decoded = decode_packet(packet, hidden, None if state is None else state["scales"])
            h = decoded["header"]
            iskey, fid, rid, generation = bool(h[2]), h[5], h[6], h[7]
            need(iskey == row["key"] == entry["key"] and fid == key[1] and rid == row["reference_id"] == entry["reference_id"] and
                 generation == row["generation"] == (1 if state is None else state["generation"]+1), "CS88 causal identities")
            need((iskey and rid == 0xffffffff) or (state is not None and rid == state["fid"] and fid > state["fid"]), "CS88 reference state")
            need(np.array_equal(decoded["operations"], expected_ops) and sha(expected_ops.tobytes()) == row["operations_sha256"], "independent mode map differs")
            semantic_ops = np.where(hidden, 1, np.where((not iskey) & ~np.any(coefficients, axis=1), 0, 2)).astype(np.uint8)
            need(np.array_equal(semantic_ops, expected_ops), "fresh COPY/residual operation semantics")
            need(np.array_equal(decoded["dense"], coefficients), "independent BR88 all 8100 dense blocks differ")
            scales = np.asarray([(packed_qmap[i//4] >> (6-2*(i % 4))) & 3 for i in range(1352)], dtype=np.uint8)
            need(len(packed_qmap) == 338 and np.all(scales[:1350] <= 2) and not np.any(scales[1350:]) and
                 np.array_equal(scales[:1350], decoded["scales"]), "independent QM87 map differs")
            need(decoded["hud"] == hud_envelope and sha(decoded["qraw"]) == row["qmap_sha256"], "HUD envelope/QM87 payload differs")
            need(decoded["components"] == row["components"] and sum(decoded["components"].values()) == len(packet) == row["wire_bytes"], "component accounting differs")
            need(row["map_method"] == h[4] == (0 if iskey else 3) and row["qmap_method"] == decoded["qmethod"] and
                 row["block_size"] == 32 and row["chunk_profile_cap"] == 65536 and row["remaining_adaptive_decisions"] == 0,
                 "selected source subset metadata")
            root = c2_root(planes)
            previous = bytes(32) if iskey else state["root"]
            seal = hashlib.sha256(DOMAIN+b"S\0"+CONTEXT+struct.pack(">IIBQ", fid, rid, int(iskey), generation)+
                                  previous+bytes.fromhex(words_sha)+root).digest()
            need(root == decoded["root"] and seal == decoded["seal"], "independent C2 root/seal differs")
            native_decoded = row["decoded"]
            need(native_decoded["accepted"] is True and native_decoded["replayed"] is False and native_decoded["fid"] == fid and
                 native_decoded["generation"] == generation and native_decoded["wire_bytes"] == len(packet), "strict native receiver acceptance")
            expected_native = dict(canonical_sha256=sha(canonical), hud_sha256=words_sha, display_sha256=entry["expected"]["rgb565_sha256"],
                                   coefficient_sha256=sha(coefficients.tobytes()), root=root.hex(), seal=seal.hex())
            need(all(native_decoded[field] == expected for field, expected in expected_native.items()), "strict native receiver result hash differs")
            need(row["CU66_geometry_rectangles_HUD_sha256"] == entry["expected"]["hud_sha256"] and
                 row["CS88_words_HUD_sha256"] == words_sha, "distinct HUD semantic hashes")
            fits = len(packet) <= 49152
            prefix_ok = fits and (state is None or state["prefix_ok"])
            need(row["fits_49152"] is fits and row["entire_input_prefix_49152_eligible"] is prefix_ok,
                 "physical causal prefix eligibility differs")
            need(row["physical_candidate_admission"] == ("FITS_PACKET_CAP_DIAGNOSTIC_CHAIN" if fits else "REJECT_OVERSIZE"), "cap admission label")
            if not fits:
                oversize.append({"chain": row["chain"], "clip_id": key[0], "frame_id": fid, "bytes": len(packet)})
            states[row["chain"]] = dict(fid=fid, generation=generation, root=root, scales=decoded["scales"], prefix_ok=prefix_ok)
            chains.setdefault(row["chain"], []).append(row)
            output["frames"].append(dict(chain=row["chain"], clip_id=key[0], frame_id=fid, packet_sha256=sha(packet), wire_bytes=len(packet),
                                          independent_coefficient_sha256=sha(coefficients.tobytes()), independent_root=root.hex(), independent_seal=seal.hex(),
                                          map_method=h[4], qmap_method=decoded["qmethod"], fits_49152=fits))
            counts["packets_independently_parsed"] += 1
            counts["dense_blocks_compared"] += 8100
            counts["dense_coefficients_compared"] += 8100*64
            counts["mode_operations_compared"] += 8100
            counts["quantizer_cells_compared"] += 1350
            counts["C2_roots_and_seals_verified"] += 1
            if number % 60 == 0:
                print("CS88_AUDIT_PROGRESS", number+1, flush=True)
        need(len(oversize) == selected["oversize_packets_49152"] == 1 and selected["fit_packets_49152"] == 359,
             "359 fit / 1 oversize accounting")
        need(oversize[0] == dict(chain="chain06", clip_id="mass-effect-legendary-combat-20s-q8", frame_id=25, bytes=49654),
             "unexpected oversize packet")
        case_map = {case["case_id"]: case for case in fresh["cases"]}
        for summary in selected["chains"]:
            group = chains[summary["chain"]]
            case = case_map[summary["clip_id"]]
            eligible = len(group) == case["input_frames"] and case["rejected_frames"] == 0 and all(r["fits_49152"] for r in group)
            need(summary["input_frames"] == case["input_frames"] == 30 and summary["accepted_frames"] == len(group) and
                 summary["CU66_rejected_frames"] == case["rejected_frames"] == 0 and
                 summary["entire_sequence_49152_eligible"] is eligible and summary["accepted_subset_49152_eligible"] is eligible and
                 summary["total_bytes"] == sum(r["wire_bytes"] for r in group) and summary["max_bytes"] == max(r["wire_bytes"] for r in group) and
                 summary["fits_49152"] == sum(r["fits_49152"] for r in group) and summary["oversize_49152"] == sum(not r["fits_49152"] for r in group),
                 "entire original sequence eligibility/accounting")
        selected_q16 = [r for r in rows if r["quant_scale"] == 16]
        need(len(selected_q16) == 120 and len({r["clip_id"] for r in selected_q16}) == 4 and all(r["fits_49152"] for r in selected_q16),
             "q16 four complete physical-cap-fit cases")
        need(selected["input_frames"] == 360 and selected["total_wire_bytes"] == sum(r["wire_bytes"] for r in rows) and
             selected["all_sequences_49152_eligible"] is False and selected["accepted_subset_49152_eligible"] is False and
             selected["physical_30fps_proven"] is False and selected["validated_under10ms_proven"] is False, "global CS88 claims/accounting")
        # Re-run the retained strict receiver binary on the recorded mutation.
        tests = selected["adversarial"]
        need(len(tests) == 1 and tests[0]["status"] == "PASS_REJECT_UNCHANGED_GOOD_RECOVERY", "recorded negative/recovery status")
        mutation = attempt / "chain00/f000001-late-coefficient-valid-crc.cs88"
        corrupt = pin(mutation, tests[0]["corruption_sha256"])
        good0, good1 = (attempt / "chain00/f000000.cs88").read_bytes(), (attempt / "chain00/f000001.cs88").read_bytes()
        first_entry = fresh_by_key[("mass-effect-2600-q8", 0)]
        with np.load(first_entry["rtl_components_path"], allow_pickle=False) as archive:
            hidden = archive["operations"] == 1
        parsed0 = decode_packet(good0, hidden, None)
        parsed_bad = decode_packet(corrupt, hidden, parsed0["scales"])
        parsed_good = decode_packet(good1, hidden, parsed0["scales"])
        delta = np.flatnonzero(parsed_bad["dense"].ravel() != parsed_good["dense"].ravel())
        need(len(delta) == 1 and delta[0] % 64 == 0 and parsed_bad["root"] == parsed_good["root"] and
             parsed_bad["seal"] == parsed_good["seal"] and parsed_bad["hud"] == parsed_good["hud"] and
             np.array_equal(parsed_bad["operations"], parsed_good["operations"]) and np.array_equal(parsed_bad["scales"], parsed_good["scales"]),
             "valid-CRC mutation must change exactly one residual DC coefficient while retaining original root/seal")
        receiver = selected["binaries"]["receiver"]["path"]
        command = ["docker", "exec", "-i", selected["container"]["name"], receiver]
        transport = b"".join(struct.pack(">II", 0, len(packet))+packet for packet in (good0, corrupt, good1))
        result = subprocess.run(command, input=transport, capture_output=True, check=True)
        replies = [json.loads(line) for line in result.stdout.splitlines()]
        need(len(replies) == 3 and replies[0]["accepted"] is True and replies[0]["fid"] == 0 and
             replies[1] == {"accepted": False, "error": "CS88 reconstructed content root", "retained_fid": 0} and
             replies[2] == chains["chain00"][1]["decoded"] and tests[0]["good_recovery_fid"] == replies[2]["fid"] and
             tests[0]["good_recovery_root"] == replies[2]["root"] and tests[0]["good_recovery_seal"] == replies[2]["seal"],
             "re-executed strict native rejection/retained state/recovery differs")
        output["adversarial_reexecution"] = dict(command=command, mutation_path=str(mutation), mutation_sha256=sha(corrupt),
                                                   changed_dense_coefficient_index=int(delta[0]), replies=replies,
                                                   stdout_sha256=sha(result.stdout), stderr_sha256=sha(result.stderr))
        counts["valid_CRC_late_coefficient_native_rejection_recovery_tests"] = 1
        output["oversize_packets"] = oversize
        output["eligibility"] = dict(all_360_packets_fit_49152=False, fit_packets=359, oversize_packets=1,
                                      complete_q16_candidate_frames=120, complete_q16_cases=4,
                                      complete_q16_original_inputs_all_admitted_and_cap_fit=True, total_wire_bytes=selected["total_wire_bytes"])
        for filename, expected in pins.items():
            need(sha(Path(filename).read_bytes()) == expected["sha256"], "audit input/source changed")
        output["status"] = "PASS_INDEPENDENT_SELECTED_CS88_AUDIT"
        code = 0
    except Exception as error:
        output["error"] = type(error).__name__+": "+str(error)
        print(output["error"], file=sys.stderr)
        code = 1
    output["counts"] = dict(counts)
    output["finished_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True, allow_nan=False)+"\n")
    print(json.dumps(dict(status=output["status"], counts=output["counts"], output=str(args.output.resolve())), sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
