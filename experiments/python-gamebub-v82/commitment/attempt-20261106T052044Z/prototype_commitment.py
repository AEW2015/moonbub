#!/usr/bin/env python3
"""Opt-in V82 SHA256 content commitment. A semantic prototype, not sender authentication."""
from __future__ import annotations
import argparse
import copy
import hashlib
import heapq
import importlib.util
import json
from pathlib import Path
import struct
import time

PROFILE = "CU66-V82-CONTENT-SHA256-TREE-1"
CAPABILITY = "cu66-v82-content-tree-sha256"
GEOMETRY = (720, 480, 5400, 1350, 1350)
ZERO = bytes(32)
CONST128 = bytes([128]) * 64
DOMAIN = b"CU66/V82/CONTENT/1\x00"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def blocks(length):
    return (length + 9 + 63) // 64


def sha(message):
    return hashlib.sha256(message).digest()


def normalize_frame(frame):
    f = dict(frame)
    f.setdefault("profile_id", PROFILE)
    f.setdefault("capability", CAPABILITY)
    f.setdefault("geometry", GEOMETRY)
    f["geometry"] = tuple(f["geometry"])
    f.setdefault("generation", f.get("ordinal", f["fid"]))
    if "hud_digest" in f:
        digest = f["hud_digest"]
        f["hud_sha256"] = digest.hex() if isinstance(digest, bytes) else digest
    f.setdefault("hud_sha256", sha(f.get("hud", b"")).hex())
    if "tiles" not in f:
        f["tiles"] = [tile for plane in f["planes"] for tile in plane]
    f["tiles"] = list(f["tiles"])
    f.setdefault("hidden_mask", f.get("const_mask", bytes(len(f["tiles"]))))
    return f


def schedule_jobs(jobs, lanes):
    """Nonpreemptive deterministic list schedule, all payloads available at t=0."""
    if not jobs:
        return 0
    by_id = {j["id"]: j for j in jobs}
    remain = {j["id"]: len(j["deps"]) for j in jobs}
    outgoing = {j["id"]: [] for j in jobs}
    for j in jobs:
        for dep in j["deps"]:
            outgoing[dep].append(j["id"])
    ready = [j["id"] for j in jobs if not remain[j["id"]]]
    heapq.heapify(ready)
    active = []
    now = done = 0
    while ready or active:
        while ready and len(active) < lanes:
            ident = heapq.heappop(ready)
            heapq.heappush(active, (now + by_id[ident]["cycles"], ident))
        now = active[0][0]
        completed = []
        while active and active[0][0] == now:
            _, ident = heapq.heappop(active)
            completed.append(ident)
            done += 1
        for ident in completed:
            for child in outgoing[ident]:
                remain[child] -= 1
                if not remain[child]:
                    heapq.heappush(ready, child)
    if done != len(jobs):
        raise ValueError("cyclic hash jobs")
    return now


class CommitmentTree:
    def __init__(self, profile_id=PROFILE, geometry=GEOMETRY, granularity=1):
        if profile_id != PROFILE or granularity not in (1, 4, 16, 64):
            raise ValueError("unsupported distinct V82 profile or granularity")
        self.profile_id, self.geometry, self.granularity = profile_id, tuple(geometry), granularity
        self.header = canonical(dict(profile_id=profile_id, geometry=self.geometry, granularity=granularity))
        self.groups = []
        offset = 0
        for plane, count in enumerate(self.geometry[2:]):
            for start in range(0, count, granularity):
                n = min(granularity, count - start)
                self.groups.append((plane, start, n, offset + start))
            offset += count
        self.leaf_count = len(self.groups)
        self.L = 1 << (self.leaf_count - 1).bit_length()
        self.nodes = None
        self.accepted = None
        self.root = ZERO
        self.seal = ZERO
        self.revision = 0

    def memory(self):
        return dict(real_leaves=self.leaf_count, padded_leaves=self.L,
                    tree_buffers_bytes=2 * (2 * self.L - 1) * 32,
                    v81_maps_bytes=6075,
                    total_tree_and_maps_bytes=2 * (2 * self.L - 1) * 32 + 6075,
                    extra_control_and_hash_lane_state_unpriced=True,
                    prototype_pixel_bytes_excluded_from_tree_metadata=True)

    def _leaf_message(self, index, tiles):
        plane, start, count, offset = self.groups[index]
        return DOMAIN + b"LEAF\x00" + struct.pack(">I", len(self.header)) + self.header + struct.pack(">III", plane, start, count) + b"".join(tiles[offset:offset + count])

    def _empty_message(self, index):
        return DOMAIN + b"EMPTY\x00" + struct.pack(">I", len(self.header)) + self.header + struct.pack(">II", index, self.L)

    def _internal_message(self, level, index, left, right):
        return DOMAIN + b"NODE\x00" + struct.pack(">II", level, index) + left + right

    def _seal_message(self, f, previous_root, content_root):
        hud = bytes.fromhex(f["hud_sha256"])
        if len(hud) != 32:
            raise ValueError("HUD digest length")
        metadata = canonical(dict(profile_id=f["profile_id"], capability=f["capability"],
                                  geometry=f["geometry"], granularity=self.granularity,
                                  fid=f["fid"], refid=f["refid"], key=bool(f["key"]),
                                  generation=f["generation"]))
        return DOMAIN + b"SEAL\x00" + struct.pack(">I", len(metadata)) + metadata + previous_root + hud + content_root

    def _validate_frame(self, f):
        if f["profile_id"] != self.profile_id or f["capability"] != CAPABILITY:
            raise ValueError("profile/capability mismatch: old CU66 tags cannot opt in")
        if f["geometry"] != self.geometry or len(f["tiles"]) != sum(self.geometry[2:]):
            raise ValueError("geometry mismatch")
        if any(not isinstance(t, bytes) or len(t) != 64 for t in f["tiles"]):
            raise ValueError("tile payload length")
        if len(f["hidden_mask"]) != len(f["tiles"]):
            raise ValueError("CONST mask length")
        if any(t != CONST128 for t, h in zip(f["tiles"], f["hidden_mask"]) if h):
            raise ValueError("CONST must generate 128")
        if self.accepted is not None and (f["generation"] <= self.accepted["generation"] or f["fid"] <= self.accepted["fid"]):
            raise ValueError("stale frame/key generation/order")
        if not f["key"]:
            if self.accepted is None or f["refid"] != self.accepted["fid"]:
                raise ValueError("missing/stale reference")
        elif f["refid"] != 0xffffffff:
            raise ValueError("key reference sentinel")

    def plan(self, frame, copy_mask=None):
        f = normalize_frame(frame)
        self._validate_frame(f)
        mask = bytes(copy_mask if copy_mask is not None else f.get("copy_ref_mask", bytes(len(f["tiles"]))))
        if len(mask) != len(f["tiles"]) or any(v not in (0, 1) for v in mask):
            raise ValueError("COPY mask shape")
        if f["key"] and any(mask):
            raise ValueError("COPY on key")
        fresh = f["key"] or self.nodes is None
        nodes = [None] * (2 * self.L) if fresh else list(self.nodes)
        jobs, recomputed = [], []
        changed, producers, frontier = set(), {}, {}

        def hash_node(node, message, kind, deps=()):
            digest = sha(message)
            ident = len(jobs)
            jobs.append(dict(id=ident, node=node, kind=kind, deps=list(deps),
                             message_bytes=len(message), blocks=blocks(len(message)),
                             cycles=64 * blocks(len(message))))
            producers[node] = ident
            frontier[node] = [ident]
            if fresh or nodes[node] != digest:
                changed.add(node)
            nodes[node] = digest

        for i, (plane, start, count, offset) in enumerate(self.groups):
            indices = range(offset, offset + count)
            # CONST can reuse only when the accepted bytes were already CONST128.
            reusable = not fresh and all(mask[t] or (f["hidden_mask"][t] and self.accepted["tiles"][t] == CONST128) for t in indices)
            if not reusable:
                recomputed.append(dict(leaf=i, plane=plane, start=start, count=count,
                                       tile_indices=list(indices), copied_tiles=[t for t in indices if mask[t]],
                                       const_tiles=[t for t in indices if f["hidden_mask"][t]]))
                hash_node(self.L + i, self._leaf_message(i, f["tiles"]), "leaf")
        if fresh:
            for i in range(self.leaf_count, self.L):
                hash_node(self.L + i, self._empty_message(i), "empty")
        level = 1
        width = self.L // 2
        while width:
            for i in range(width):
                node = width + i
                left, right = node * 2, node * 2 + 1
                if fresh or left in changed or right in changed:
                    deps = sorted(set(frontier.get(left, []) + frontier.get(right, [])))
                    hash_node(node, self._internal_message(level, i, nodes[left], nodes[right]), "internal", deps)
                else:
                    frontier[node] = sorted(set(frontier.get(left, []) + frontier.get(right, [])))
            level += 1
            width //= 2
        previous = ZERO if f["key"] else self.root
        seal_message = self._seal_message(f, previous, nodes[1])
        seal = sha(seal_message)
        deps = frontier.get(1, [])
        jobs.append(dict(id=len(jobs), node=0, kind="seal", deps=deps,
                         message_bytes=len(seal_message), blocks=blocks(len(seal_message)),
                         cycles=64 * blocks(len(seal_message))))
        return dict(frame=f, copy_mask=mask, root=nodes[1], seal=seal, nodes=nodes,
                    previous_root=previous, recomputed_groups=recomputed, jobs=jobs,
                    compression_blocks=sum(j["blocks"] for j in jobs),
                    lane_cycles={n: schedule_jobs(jobs, n) for n in (1, 2, 4)},
                    memory=self.memory(), base_root=self.root, base_seal=self.seal, base_revision=self.revision)

    def full(self, frame, previous_root=None):
        """Independent host rebuild: no incremental nodes, masks, or plan() calls."""
        f = normalize_frame(frame)
        leaves = [sha(self._leaf_message(i, f["tiles"])) for i in range(self.leaf_count)]
        leaves += [sha(self._empty_message(i)) for i in range(self.leaf_count, self.L)]
        level = 1
        while len(leaves) > 1:
            leaves = [sha(self._internal_message(level, i // 2, leaves[i], leaves[i + 1])) for i in range(0, len(leaves), 2)]
            level += 1
        previous = ZERO if f["key"] else (self.root if previous_root is None else previous_root)
        return dict(root=leaves[0], seal=sha(self._seal_message(f, previous, leaves[0])))

    def commit(self, plan):
        if plan["base_revision"] != self.revision or plan["base_root"] != self.root or plan["base_seal"] != self.seal:
            raise ValueError("late commit / generation rollback")
        self.nodes, self.accepted = list(plan["nodes"]), plan["frame"]
        self.root, self.seal = plan["root"], plan["seal"]
        self.revision += 1
        return self.seal.hex()

    def reset(self):
        self.nodes = self.accepted = None
        self.root = self.seal = ZERO
        self.revision += 1


class Decoder:
    """Atomic accepted/candidate state, explicit negotiation and host-root validation."""
    def __init__(self, granularity=1, geometry=GEOMETRY, capabilities=()):
        self.tree = CommitmentTree(geometry=geometry, granularity=granularity)
        self.enabled = CAPABILITY in capabilities
        self.pending = None

    def stage(self, frame, records, expected_root, expected_seal):
        if not self.enabled:
            raise ValueError("explicit V82 capability opt-in required")
        self.pending = None
        f = normalize_frame(frame)
        self.tree._validate_frame(f)
        if len(records) != len(f["tiles"]):
            raise ValueError("truncated record stream")
        decoded, mask = [], bytearray(len(records))
        for index, record in enumerate(records):
            if record["index"] != index:
                raise ValueError("index/order/duplicate")
            op, payload = record["op"], record.get("payload", b"")
            if op == "COPY":
                if f["key"] or self.tree.accepted is None or payload:
                    raise ValueError("invalid COPY")
                decoded.append(self.tree.accepted["tiles"][index]); mask[index] = 1
            elif op == "CONST128":
                if not f["hidden_mask"][index] or payload:
                    raise ValueError("invalid CONST")
                decoded.append(CONST128)
            elif op == "DATA":
                if len(payload) != 64 or f["hidden_mask"][index]:
                    raise ValueError("DATA payload/hidden mode")
                decoded.append(payload)
            else:
                raise ValueError("unknown tile mode")
        f["tiles"] = decoded
        plan = self.tree.plan(f, mask)
        # Full decoder tree independently catches a false semantic COPY claim.
        host = self.tree.full(f)
        if plan["root"] != host["root"] or plan["seal"] != host["seal"]:
            raise ValueError("incremental/full disagreement")
        if host["root"] != expected_root or host["seal"] != expected_seal:
            raise ValueError("commitment mismatch")
        self.pending = plan
        return plan

    def abort(self):
        self.pending = None

    def accept(self, seal):
        if seal == self.tree.seal and self.tree.accepted is not None:
            return seal.hex()  # Idempotent ACK of the already accepted seal.
        if self.pending is None or seal != self.pending["seal"]:
            raise ValueError("missing candidate / stale ACK")
        result = self.tree.commit(self.pending)
        self.pending = None
        return result

    def reset(self):
        self.abort(); self.tree.reset()


def records_for(frame, mask):
    f = normalize_frame(frame)
    return [dict(index=i, op="CONST128" if f["hidden_mask"][i] else "COPY" if mask[i] else "DATA",
                 payload=b"" if f["hidden_mask"][i] or mask[i] else tile)
            for i, tile in enumerate(f["tiles"])]


def selftest():
    geometry = (40, 8, 5, 3, 2)
    tiles = [bytes([i + 1]) * 64 for i in range(10)]
    hidden = bytes(int(i in (4, 7, 9)) for i in range(10))
    for i, bit in enumerate(hidden):
        if bit:
            tiles[i] = CONST128
    key = dict(fid=10, refid=0xffffffff, key=True, generation=1, geometry=geometry,
               tiles=tiles, hidden_mask=hidden, hud=b"HUD-A", profile_id=PROFILE, capability=CAPABILITY)
    delta = dict(key, fid=11, refid=10, key=False, generation=2, tiles=list(tiles), hud=b"HUD-B")
    delta["tiles"][1] = bytes([33]) * 64
    mask = bytes(int(not hidden[i] and i != 1) for i in range(10))
    results = []

    def reject(name, operation, decoder=None):
        before = None if decoder is None else (decoder.tree.root, decoder.tree.seal, decoder.tree.revision)
        try:
            operation()
        except (ValueError, KeyError, IndexError, TypeError):
            if decoder is not None:
                assert before == (decoder.tree.root, decoder.tree.seal, decoder.tree.revision)
            results.append(dict(test=name, status="PASS"))
        else:
            raise AssertionError("fault accepted: " + name)

    for g in (1, 4, 16, 64):
        host = CommitmentTree(geometry=geometry, granularity=g)
        decoder = Decoder(g, geometry, [CAPABILITY])
        p0 = host.plan(key)
        oracle0 = host.full(key)
        assert (p0["root"], p0["seal"]) == (oracle0["root"], oracle0["seal"])
        decoder.stage(key, records_for(key, bytes(10)), **dict(expected_root=p0["root"], expected_seal=p0["seal"]))
        decoder.accept(p0["seal"]); host.commit(p0)
        assert decoder.accept(p0["seal"]) == p0["seal"].hex()
        results.append(dict(test=f"g{g}:key+idempotent-ACK", status="PASS"))
        p1, full1 = host.plan(delta, mask), host.full(delta)
        assert p1["root"] == full1["root"] and p1["seal"] == full1["seal"]
        assert p1["compression_blocks"] == sum(blocks(j["message_bytes"]) for j in p1["jobs"])
        assert p1["lane_cycles"][1] == p1["compression_blocks"] * 64
        assert p1["lane_cycles"][4] <= p1["lane_cycles"][2] <= p1["lane_cycles"][1]
        for group in p1["recomputed_groups"]:
            plane, start, count, _ = host.groups[group["leaf"]]
            assert start + count <= geometry[plane + 2]
        records = records_for(delta, mask)
        expected = dict(expected_root=full1["root"], expected_seal=full1["seal"])
        prefix = f"g{g}:"
        reject(prefix + "missing-opt-in", lambda: Decoder(g, geometry).stage(key, records_for(key, bytes(10)), p0["root"], p0["seal"]))
        reject(prefix + "missing-reference", lambda: Decoder(g, geometry, [CAPABILITY]).stage(delta, records, **expected))
        for label, changes in (("stale-reference", {"refid": 9}), ("profile", {"profile_id": "CU66-OLD-FLAT-SHA256"}),
                               ("capability", {"capability": "old-cu66"}), ("geometry", {"geometry": (40, 8, 6, 2, 2)}),
                               ("generation", {"generation": 1}), ("frame-id", {"fid": 10}),
                               ("HUD", {"hud": b"tampered"}), ("key-flag", {"key": True})):
            reject(prefix + label, lambda c=changes: decoder.stage(dict(delta, **c), records, **expected), decoder)
        for label, mutate in (
            ("index", lambda r: r[0].update(index=99)),
            ("order", lambda r: r.reverse()),
            ("duplicate", lambda r: r.__setitem__(1, dict(r[0]))),
            ("payload", lambda r: r[1].update(payload=bytes([2]) * 64)),
            ("payload-truncation", lambda r: r[1].update(payload=b"x")),
            ("wrong-COPY-changed-tile", lambda r: r[1].update(op="COPY", payload=b"")),
            ("CONST-payload", lambda r: r[4].update(payload=b"x")),
            ("record-truncation", lambda r: r.pop()),
        ):
            bad = copy.deepcopy(records); mutate(bad)
            reject(prefix + label, lambda b=bad: decoder.stage(delta, b, **expected), decoder)
        reject(prefix + "stale-key", lambda: decoder.stage(key, records_for(key, bytes(10)), p0["root"], p0["seal"]), decoder)
        reject(prefix + "root", lambda: decoder.stage(delta, records, bytes([1]) * 32, full1["seal"]), decoder)
        reject(prefix + "seal", lambda: decoder.stage(delta, records, full1["root"], bytes([1]) * 32), decoder)
        # Even if an untrusted sender labels changed bytes COPY, independent full rebuild disagrees.
        false = bytearray(mask); false[1] = 1
        false_plan = host.plan(delta, false)
        assert false_plan["root"] != full1["root"]
        decoder.stage(delta, records, **expected)
        decoder.abort()
        reject(prefix + "abort-rollback", lambda: decoder.accept(full1["seal"]), decoder)
        decoder.stage(delta, records, **expected)
        # A subsequent malformed partial candidate invalidates the staged transaction.
        reject(prefix + "partial-rollback", lambda: decoder.stage(delta, records[:-1], **expected), decoder)
        reject(prefix + "partial-late-ACK", lambda: decoder.accept(full1["seal"]), decoder)
        decoder.stage(delta, records, **expected); decoder.accept(full1["seal"]); host.commit(p1)
        assert decoder.tree.root == host.root
        reject(prefix + "late-commit", lambda: host.commit(p1))
        # DATA can be semantically unchanged: recompute leaf, but stop propagation at equal digest.
        same = dict(delta, fid=12, refid=11, generation=3)
        same_plan = host.plan(same, bytes(10))
        assert same_plan["root"] == host.root
        assert not any(j["kind"] == "internal" for j in same_plan["jobs"])
        assert len(same_plan["recomputed_groups"]) > 0
        fresh = dict(key, fid=13, generation=4)
        fresh_plan = host.plan(fresh)
        assert sum(j["kind"] != "seal" for j in fresh_plan["jobs"]) == 2 * host.L - 1
        host.reset()
        reject(prefix + "late-plan-after-reset", lambda: host.commit(fresh_plan))
        decoder.reset()
        fresh_oracle = decoder.tree.full(fresh)
        decoder.stage(fresh, records_for(fresh, bytes(10)), fresh_oracle["root"], fresh_oracle["seal"])
        decoder.accept(fresh_oracle["seal"])
        results.append(dict(test=prefix + "reset-key/fresh-tree/unchanged-digest-stop/padding-boundaries", status="PASS"))
    # SHA-256 boundary cases include mandatory one-bit marker and 64-bit message length.
    assert [blocks(n) for n in (0, 55, 56, 63, 64, 119, 120)] == [1, 1, 2, 2, 2, 2, 3]
    results.append(dict(test="SHA256-padding-boundaries", status="PASS"))
    return results


def run_native(output):
    repo = Path(__file__).resolve().parents[2]
    loader_path = repo / "experiments/python-gamebub-v82/native/data.py"
    spec = importlib.util.spec_from_file_location("v82_native_data", loader_path)
    native = importlib.util.module_from_spec(spec); spec.loader.exec_module(native)
    trees = {}
    aggregates = {}
    count, histories = 0, set()
    with (output / "frames.jsonl").open("x") as log:
        for native_frame in native.iter_frames():
            frame = dict(native_frame, profile_id=PROFILE, capability=CAPABILITY,
                         generation=native_frame["ordinal"] + 1, geometry=GEOMETRY)
            cohort = frame["cohort"]; histories.add(cohort); count += 1
            for g in (1, 4, 16, 64):
                for policy in ("conservative-zero-coefficient", "optimistic-byte-equality"):
                    key = (cohort, g, policy)
                    tree = trees.setdefault(key, CommitmentTree(granularity=g))
                    mask = frame["copy_ref_mask"] if policy.startswith("conservative") else bytes(
                        int(not frame["key"] and not frame["hidden_mask"][i] and bit)
                        for i, bit in enumerate(frame["same_mask"]))
                    plan = tree.plan(frame, mask)
                    full = tree.full(frame)
                    assert plan["root"] == full["root"] and plan["seal"] == full["seal"], (cohort, frame["fid"], g, policy)
                    tile_reads = sum(group["count"] for group in plan["recomputed_groups"])
                    copy_reads = sum(len(group["copied_tiles"]) for group in plan["recomputed_groups"])
                    by_kind = {kind: sum(j["kind"] == kind for j in plan["jobs"]) for kind in ("leaf", "empty", "internal", "seal")}
                    row = dict(cohort=cohort, ordinal=frame["ordinal"], fid=frame["fid"], key=frame["key"],
                               granularity=g, policy=policy, content_root=plan["root"].hex(), seal=plan["seal"].hex(),
                               full_rebuild_match=True, blocks=plan["compression_blocks"], lane_cycles=plan["lane_cycles"],
                               hash_jobs=by_kind, hashed_tile_bytes=tile_reads * 64,
                               copied_tiles_in_recomputed_groups=copy_reads, copy_tiles=sum(mask))
                    log.write(json.dumps(row, sort_keys=True) + "\n")
                    aggregate = aggregates.setdefault((g, policy), dict(frames=0, keys=0, blocks=0, hash_jobs=0,
                                                                         hashed_tile_bytes=0, copied_tiles_in_recomputed_groups=0,
                                                                         lane_cycles={1: 0, 2: 0, 4: 0}, memory=tree.memory()))
                    aggregate["frames"] += 1; aggregate["keys"] += bool(frame["key"])
                    aggregate["blocks"] += plan["compression_blocks"]
                    aggregate["hash_jobs"] += len(plan["jobs"])
                    aggregate["hashed_tile_bytes"] += tile_reads * 64
                    aggregate["copied_tiles_in_recomputed_groups"] += copy_reads
                    for lane in (1, 2, 4):
                        aggregate["lane_cycles"][lane] += plan["lane_cycles"][lane]
                    tree.commit(plan)
    assert count == 457 and len(histories) == 4, (count, histories)
    return dict(frames=count, histories=sorted(histories), full_rebuilds=count * 8,
                rows=[dict(granularity=g, policy=p, **r) for (g, p), r in sorted(aggregates.items())])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--native", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[2]
    output = args.output or repo / "experiments/python-gamebub-v82/commitment" / ("attempt-" + time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()))
    output.mkdir(parents=True, exist_ok=False)
    source = Path(__file__).read_bytes()
    (output / "prototype_commitment.py").write_bytes(source)
    report = dict(profile_id=PROFILE, capability=CAPABILITY, status="RUNNING",
                  claims=dict(sender_authentication=False, rtl_or_hls=False, measured_hardware_cycles=False,
                              validated_decode_Fmax_throughput=False),
                  assumptions=dict(hash_rounds_per_block=64, rounds_per_cycle=1, hash_lanes=[1, 2, 4],
                                   idealized_scheduler=True, all_hash_input_bytes_available_at_t0=True,
                                   dma_decode_copy_and_payload_availability_unmodeled=True))
    try:
        report["synthetic_tests"] = selftest()
        if args.native:
            report["native"] = run_native(output)
        report["status"] = "PASS"
    except BaseException as error:
        report["status"] = "FAIL"; report["error"] = repr(error)
        raise
    finally:
        (output / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        manifest = {p.name: sha(p.read_bytes()).hex() for p in output.iterdir() if p.is_file()}
        (output / "sha256.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        print(json.dumps(dict(attempt=str(output), status=report["status"], synthetic_tests=len(report.get("synthetic_tests", [])),
                              native_frames=report.get("native", {}).get("frames", 0))))


if __name__ == "__main__":
    main()
