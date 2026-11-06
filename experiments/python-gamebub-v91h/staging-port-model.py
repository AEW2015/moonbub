#!/usr/bin/env python3
"""Bounded abstract checks for V91h's on-chip 8-bit staging RAM ports.

This is an executable contract model, not RTL, cycle equivalence, synthesis
evidence, or a physical BRAM inference/fit/timing claim.
"""
from __future__ import annotations

import hashlib
import json
import random
import struct
import zlib
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RESULT = ROOT / "experiments/python-gamebub-v91h/staging-port-results.json"
SEED = 910438
MAX_STAGING = 192
HEADER_BYTES = 42
CRC_BYTES = 4
REGISTER_CACHE_BYTES = 46
DESCRIPTOR_BYTES = 6
DESCRIPTOR_TAIL_BYTES = 1
REPLAY_WORD_BYTES = 4
RAW_PAIR_BYTES = 2


def le(data: bytes, offset: int, size: int) -> int:
    """Independent little-endian oracle, using byte slices, never port state."""
    return int.from_bytes(data[offset:offset + size], "little")


def bits_msb(data: bytes, bit_count: int) -> list[int]:
    return [(data[i // 8] >> (7 - i % 8)) & 1 for i in range(bit_count)]


def make_packet(*, raw: bool, blocks: int = 1, replay_bits: int = 0,
                raw_words: list[int] | None = None) -> bytes:
    """Small BR88-like packet builder for staging semantics, not codec validity."""
    if raw:
        assert raw_words is not None and len(raw_words) == blocks * 64
        payloads = [b"".join(struct.pack("<h", x) for x in raw_words), b"", b"", b""]
        counts = [blocks, 0, 0, 0]
        mode = 1
    else:
        n = (replay_bits + 7) // 8
        # Deliberately non-palindromic pattern; unused low tail bits are zero.
        stream = bytes(((0xB3 + i * 0x35) & 0xFF) for i in range(n))
        if replay_bits & 7:
            stream = stream[:-1] + bytes([stream[-1] & (0xFF << (8 - (replay_bits & 7)) & 0xFF)])
        payloads = [stream, b"", b"", b""]
        counts = [blocks, 0, 0, 0]
        mode = 0
    body = bytearray()
    lengths = []
    for band, stream in enumerate(payloads):
        bits = len(stream) * 8 if raw else (replay_bits if band == 0 else 0)
        desc = bytes([0, 255 if band == 0 else 0]) + bits.to_bytes(4, "little")
        part = desc + stream
        lengths.append(len(part))
        body.extend(part)
    header = bytearray(HEADER_BYTES)
    header[0:4] = b"BR88"
    header[4] = 1
    header[5] = mode
    header[6:10] = blocks.to_bytes(4, "little")
    header[10:12] = (1).to_bytes(2, "little")
    for i, size in enumerate(lengths):
        header[14 + 4 * i:18 + 4 * i] = size.to_bytes(4, "little")
    # count[0] is implicit in blocks; explicit band counts occupy 30..41.
    for i in range(1, 4):
        header[26 + 4 * i:30 + 4 * i] = counts[i].to_bytes(4, "little")
    if raw:
        # RAW header requires all bytes in band 0 and no other band payload.
        header[14:18] = (blocks * 128).to_bytes(4, "little")
        for i in range(1, 4):
            header[14 + 4 * i:18 + 4 * i] = (0).to_bytes(4, "little")
        body = bytearray(payloads[0])
    packet = bytes(header) + bytes(body)
    return packet + (zlib.crc32(packet) & 0xFFFFFFFF).to_bytes(4, "little")


class SyncPort:
    """One independent 8-bit write and registered 8-bit read port."""
    def __init__(self, size: int = MAX_STAGING):
        self.mem = bytearray(size)
        self.pending: tuple[int, int, int] | None = None  # address, epoch, sampled byte
        self.epoch = 1
        self.cycles = 0
        self.events: Counter[str] = Counter()

    def edge(self, *, read: int | None = None, write: tuple[int, int] | None = None,
             start: bool = False, reset: bool = False, abort: bool = False,
             epoch: int | None = None) -> tuple[int, int] | None:
        """Return prior-edge response; cancellation priority is reset, abort, start."""
        assert read is None or write is None, "v91h scheduler excludes staging read/write overlap"
        self.cycles += 1
        if reset or abort or start:
            old = self.pending
            self.pending = None
            if reset or abort:
                self.epoch = 0
            else:
                self.epoch = (self.epoch + 1) if epoch is None else epoch
            self.events["reset" if reset else "abort" if abort else "start"] += 1
            if old is not None:
                self.events["cancelled_pending_read"] += 1
            return None
        response = None
        if self.pending is not None:
            addr, tag, value = self.pending
            self.events["read_response"] += 1
            if tag == self.epoch:
                response = (addr, value)
                self.events["read_consumed"] += 1
            else:
                self.events["stale_response_discarded"] += 1
        self.pending = None
        if write is not None:
            addr, value = write
            assert 0 <= addr < len(self.mem)
            self.mem[addr] = value & 0xFF
            self.events["write_accept"] += 1
        if read is not None:
            assert 0 <= read < len(self.mem)
            # Model the RAM's nonblocking assignment: data is sampled on the
            # request edge and becomes visible after that edge.
            self.pending = (read, self.epoch, self.mem[read])
            self.events["read_request"] += 1
        return response


def read_sync(port: SyncPort, addresses: list[int], *, epoch: int,
              stalls: list[int] | None = None) -> tuple[bytes, int]:
    """Serial FETCH_REQ/FETCH_WAIT: consume one registered byte before next request."""
    port.epoch = epoch
    cycle = 0
    stalls = stalls or []
    values = []
    for address in addresses:
        while cycle in stalls:
            port.edge()
            cycle += 1
        assert port.edge(read=address) is None
        cycle += 1
        rsp = port.edge()
        cycle += 1
        assert rsp is not None and rsp[0] == address
        values.append(rsp[1])
        assert cycle < 10000
    return bytes(values), cycle


def receive(port: SyncPort, packet: bytes, rng: random.Random, events: Counter[str]) -> int:
    """One accepted byte per edge; source holds the current byte through stalls."""
    assert len(packet) <= MAX_STAGING
    addr = 0
    cycle = 0
    while addr < len(packet):
        valid = True
        ready = rng.random() >= 0.18
        if valid and ready:
            port.edge(write=(addr, packet[addr]))
            addr += 1
            events["receive_accept"] += 1
        else:
            port.edge()
            events["receive_hold"] += 1
        cycle += 1
        assert cycle < MAX_STAGING * 4
    return cycle


def consume_held(words: list[tuple[int, int]], rng: random.Random,
                 events: Counter[str]) -> list[tuple[int, int]]:
    """Valid-ready output: payload remains unchanged while ready is low."""
    accepted = []
    held: tuple[int, int] | None = None
    i = 0
    cycles = 0
    while i < len(words) or held is not None:
        if held is None and i < len(words):
            held = words[i]
        ready = rng.random() >= 0.35
        if held is not None and not ready:
            events["consumer_hold"] += 1
        elif held is not None:
            accepted.append(held)
            events["consumer_accept"] += 1
            i += 1
            held = None
        cycles += 1
        assert cycles < 10000
    return accepted


def validate_packet(packet: bytes, cache: bytes) -> tuple[bool, list[int]]:
    """Small structural/CRC validation after the complete packet is received."""
    good = len(packet) >= 46 and len(cache) == REGISTER_CACHE_BYTES
    good &= cache[:4] == b"BR88" and cache[4] == 1
    good &= cache[5] <= 1 and le(cache, 6, 4) > 0
    good &= le(cache, 10, 2) == 1 and le(cache, 12, 2) == 0
    good &= zlib.crc32(packet[:-4]) & 0xFFFFFFFF == le(cache, 42, 4)
    good &= sum(le(cache, 14 + 4 * i, 4) for i in range(4)) == len(packet) - 46
    if cache[5] == 1:
        blocks = le(cache, 6, 4)
        good &= [le(cache, 14 + 4 * i, 4) for i in range(4)] == [blocks * 128, 0, 0, 0]
        good &= [le(cache, 26 + 4 * i, 4) for i in range(1, 4)] == [0, 0, 0]
    return bool(good), [le(cache, 14 + 4 * i, 4) for i in range(4)]


def replay_words(stream: bytes, nbits: int) -> list[tuple[int, int]]:
    """Assemble up to four bytes into high word bits; replay bits MSB first."""
    bits = bits_msb(stream, nbits)
    out = []
    for start in range(0, len(bits), 32):
        part = bits[start:start + 32]
        word = 0
        for bit in part:
            word = (word << 1) | bit
        word <<= 32 - len(part)
        out.append((word, len(part)))
    return out


def replay_words_by_byte_index(stream: bytes, nbits: int) -> list[tuple[int, int]]:
    """Independent MSB-aligned oracle using byte slicing and int.from_bytes."""
    expected = []
    remaining = nbits
    for offset in range(0, len(stream), REPLAY_WORD_BYTES):
        chunk = stream[offset:offset + REPLAY_WORD_BYTES]
        valid = min(remaining, len(chunk) * 8)
        expected.append((int.from_bytes(chunk.ljust(REPLAY_WORD_BYTES, b"\0"), "big"), valid))
        remaining -= valid
    assert remaining == 0
    return expected


def raw_pairs(raw: bytes) -> list[int]:
    assert len(raw) % RAW_PAIR_BYTES == 0
    return [int.from_bytes(raw[i:i + 2], "little", signed=True)
            for i in range(0, len(raw), 2)]


def run_vector(*, raw: bool, replay_bits_count: int = 0, seed: int) -> dict:
    rng = random.Random(seed)
    packet = make_packet(raw=raw, replay_bits=replay_bits_count,
                         raw_words=[((i * 73) % 4097) - 2048 for i in range(64)] if raw else None)
    assert len(packet) <= MAX_STAGING
    port = SyncPort()
    events: Counter[str] = Counter()
    receive_cycles = receive(port, packet, rng, events)
    assert port.events["read_request"] == 0
    assert port.events["write_accept"] == len(packet)
    events["full_receive_before_any_staging_read"] += 1
    # No packet writes are legal once receive completes; capture image for proof.
    frozen = bytes(port.mem[:len(packet)])
    assert frozen == packet

    # A registered read request issued at edge N is consumed at N+1.
    header_crc_addrs = list(range(HEADER_BYTES)) + list(range(len(packet) - CRC_BYTES, len(packet)))
    cache, read_cycles = read_sync(port, header_crc_addrs, epoch=port.epoch,
                                  stalls=[3, 8, 21])
    valid, lengths = validate_packet(packet, cache)
    assert valid, "header/CRC/length validation must wait for all 46 bytes"
    events["header_crc_validated_after_receive"] += 1
    assert cache[:HEADER_BYTES] == packet[:HEADER_BYTES]
    assert cache[42:46] == packet[-4:]
    assert le(cache, 6, 4) == 1
    assert cache[5] == (1 if raw else 0)

    if raw:
        # Header-only register cache is no longer needed; fetch each RAW pair.
        expected_tokens = []
        for base in range(42, 42 + 128, RAW_PAIR_BYTES):
            addresses = list(range(base, base + RAW_PAIR_BYTES))
            fetched, c = read_sync(port, addresses, epoch=port.epoch,
                                  stalls=[0] if base in (42, 74, 106) else [])
            read_cycles += c
            expected = packet[base:base + RAW_PAIR_BYTES]
            assert fetched == expected
            expected_tokens.extend(raw_pairs(expected))
        observed = consume_held([(v, 16) for v in expected_tokens], rng, events)
        assert [v for v, _ in observed] == expected_tokens
        events["raw_pair_assembly"] += len(expected_tokens)
    else:
        # Fetch all four descriptors into the 6+1 byte bounded overwrite cache.
        # The final byte is the stream's last byte, or the sixth descriptor
        # byte again when its extent is zero.
        cursor = 42
        stream_start = 48
        explicit_counts = [le(cache, 6, 4)] + [le(cache, 26 + 4 * i, 4) for i in range(1, 4)]
        for band in range(4):
            tail_addr = cursor + lengths[band] - 1
            desc7, c = read_sync(port, list(range(cursor, cursor + DESCRIPTOR_BYTES)) + [tail_addr],
                                epoch=port.epoch, stalls=[2] if band == 0 else [])
            read_cycles += c
            desc = desc7[:DESCRIPTOR_BYTES]
            tail_byte = desc7[DESCRIPTOR_BYTES]
            expected_bits = replay_bits_count if band == 0 else 0
            assert le(desc, 2, 4) == expected_bits
            assert lengths[band] >= DESCRIPTOR_BYTES
            assert (expected_bits + 7) // 8 == lengths[band] - DESCRIPTOR_BYTES
            assert expected_bits <= 8 * (len(packet) - 46)
            if band == 0:
                assert desc[0] <= 13 and desc[1] == 255
            else:
                assert desc[0] <= 19 and desc[1] <= 11
                assert explicit_counts[band] <= (5, 15, 43)[band - 1]
                assert explicit_counts[band] != 0 or expected_bits == 0
            events["descriptor6_read"] += 1
            events["descriptor_tail_read"] += 1
            extent = (expected_bits + 7) // 8
            if expected_bits & 7:
                assert tail_byte == packet[tail_addr]
                assert tail_byte & (0xFF >> (expected_bits & 7)) == 0
            if band == 0:
                stream_start = cursor + DESCRIPTOR_BYTES
            cursor += lengths[band]
        nbytes = (replay_bits_count + 7) // 8
        words = []
        remaining_bits = replay_bits_count
        for base in range(0, nbytes, REPLAY_WORD_BYTES):
            chunk_len = min(REPLAY_WORD_BYTES, nbytes - base)
            addresses = list(range(stream_start + base, stream_start + base + chunk_len))
            stream, c = read_sync(port, addresses, epoch=port.epoch,
                                  stalls=[1, 6, 11] if base == 0 else [])
            read_cycles += c
            # Independent byte-index oracle never consults port/cache state.
            expected_stream = packet[stream_start + base:stream_start + base + chunk_len]
            assert stream == expected_stream
            chunk_bits = min(remaining_bits, chunk_len * 8)
            bit_words = replay_words(expected_stream, chunk_bits)
            byte_words = replay_words_by_byte_index(expected_stream, chunk_bits)
            assert bit_words == byte_words
            words.extend(byte_words)
            remaining_bits -= chunk_bits
        assert remaining_bits == 0
        observed = consume_held(words, rng, events)
        assert observed == words
        events["replay_word_assembly"] += len(words)
        if nbytes % REPLAY_WORD_BYTES:
            events["partial_replay_word"] += 1
        if replay_bits_count == 0:
            events["zero_replay_bits"] += 1

    # Staging memory was immutable during parse/replay. This model does not own
    # the separate packed-store external bus or its retained physical requests.
    assert bytes(port.mem[:len(packet)]) == frozen
    events["packet_memory_immutable"] += 1
    return {"packet_bytes": len(packet), "receive_edges": receive_cycles,
            "read_edges": read_cycles, "read_accepts": port.events["read_request"],
            "read_responses": port.events["read_response"], "events": events,
            "outputs": len(observed)}


def directed_epoch_checks(events: Counter[str]) -> int:
    checks = 0
    # Response from an old epoch is returned by the simulated RAM but ignored.
    p = SyncPort(8)
    p.mem[3] = 0xA5
    p.epoch = 4
    assert p.edge(read=3) is None
    assert p.pending == (3, 4, 0xA5)
    p.edge(start=True, epoch=5)
    assert p.pending is None and p.epoch == 5
    assert p.edge() is None
    assert p.events["cancelled_pending_read"] == 1
    events["epoch_cancelled_pending_response"] += 1
    p.mem[0] = 0x5C
    p.edge(read=0)
    assert p.edge() == (0, 0x5C)
    events["restart_after_epoch_cancel"] += 1
    checks += 1
    # If the response is already pending across an externally advanced epoch,
    # the address tag prevents it from being consumed as new-epoch data.
    p = SyncPort(8)
    p.mem[2] = 0x71
    p.epoch = 7
    p.edge(read=2)
    p.epoch = 8
    assert p.edge() is None
    assert p.events["stale_response_discarded"] == 1
    events["epoch_stale_response_ignored"] += 1
    checks += 1
    # Registered output is a request-edge snapshot, unaffected by a later
    # change to the backing byte before the response is consumed.
    p = SyncPort(8)
    p.mem[5] = 0x19
    p.edge(read=5)
    p.mem[5] = 0xE4
    assert p.edge() == (5, 0x19)
    events["registered_request_edge_snapshot"] += 1
    checks += 1
    # Priority and no write-through leakage for simultaneous controls.
    p = SyncPort(8)
    p.edge(write=(1, 0x33), start=True, reset=True, abort=True, epoch=9)
    assert p.mem[1] == 0
    assert p.epoch == 0 and p.events["reset"] == 1
    events["reset_abort_over_start_priority"] += 1
    checks += 1
    # The physical interface has distinct 1R/1W ports, but the scheduler
    # deliberately serializes receive writes and later staging reads.
    p = SyncPort(8)
    try:
        p.edge(write=(4, 0xD2), read=4)
        raise AssertionError("overlap must be excluded by the scheduler")
    except AssertionError as exc:
        assert "excludes staging" in str(exc)
    p.edge(write=(4, 0xD2))
    p.edge(read=4)
    assert p.edge()[1] == 0xD2
    events["read_write_overlap_excluded"] += 1
    checks += 1
    # Child output remains valid and unchanged while the staging port fetches
    # the next word; sink backpressure never cancels the registered read.
    p = SyncPort(8)
    p.mem[6] = 0xC7
    held = (0x89ABCDEF, 32)
    p.edge(read=6)
    assert held == (0x89ABCDEF, 32)
    rsp = p.edge()
    assert rsp == (6, 0xC7) and held == (0x89ABCDEF, 32)
    events["held_output_stable_during_next_fetch"] += 1
    checks += 1
    return checks


def main() -> None:
    events: Counter[str] = Counter()
    directed = directed_epoch_checks(events)
    vectors = []
    stage_counts: Counter[str] = Counter()
    # Header/CRC cache, zero stream, unaligned fields, partial final 32-bit word,
    # plus deterministic randomized ready/valid stalls on the receive and sink.
    for i, bits in enumerate((0, 1, 7, 9, 31, 32, 33, 63)):
        row = run_vector(raw=False, replay_bits_count=bits, seed=SEED + i)
        assert row["read_accepts"] == row["read_responses"]
        vectors.append({"kind": "coded", "replay_bits": bits,
                        "packet_bytes": row["packet_bytes"], "receive_edges": row["receive_edges"],
                        "read_edges": row["read_edges"], "read_accepts": row["read_accepts"],
                        "read_responses": row["read_responses"], "outputs": row["outputs"]})
        events.update(row["events"])
        stage_counts["read_requests"] += row["read_accepts"]
        stage_counts["read_responses"] += row["read_responses"]
        stage_counts["receive_writes"] += row["events"]["receive_accept"]
    row = run_vector(raw=True, seed=SEED + 99)
    assert row["read_accepts"] == row["read_responses"]
    vectors.append({"kind": "raw", "packet_bytes": row["packet_bytes"],
                    "receive_edges": row["receive_edges"], "read_edges": row["read_edges"],
                    "read_accepts": row["read_accepts"], "read_responses": row["read_responses"],
                    "outputs": row["outputs"]})
    events.update(row["events"])
    stage_counts["read_requests"] += row["read_accepts"]
    stage_counts["read_responses"] += row["read_responses"]
    stage_counts["receive_writes"] += row["events"]["receive_accept"]
    required_event_types = [
        "receive_accept", "receive_hold", "header_crc_validated_after_receive",
        "full_receive_before_any_staging_read",
        "descriptor6_read", "descriptor_tail_read", "replay_word_assembly",
        "partial_replay_word", "raw_pair_assembly", "consumer_hold",
        "packet_memory_immutable", "epoch_cancelled_pending_response",
        "epoch_stale_response_ignored", "registered_request_edge_snapshot",
        "held_output_stable_during_next_fetch", "read_write_overlap_excluded",
        "restart_after_epoch_cancel",
    ]
    assert all(events[name] > 0 for name in required_event_types)
    source_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    payload = {
        "schema": "cu66-v91h-staging-port-model-v1",
        "scope": "abstract registered staging-port semantics only; not RTL proof, cycle equivalence, codec correctness, BRAM inference, fit, timing, or hardware evidence",
        "source": "experiments/python-gamebub-v91h/staging-port-model.py",
        "source_sha256": source_hash,
        "bounds": {"staging_bytes": MAX_STAGING, "header_cache_bytes": REGISTER_CACHE_BYTES,
                   "header_bytes": HEADER_BYTES, "crc_bytes": CRC_BYTES,
                   "descriptor_bytes": DESCRIPTOR_BYTES, "descriptor_tail_bytes": DESCRIPTOR_TAIL_BYTES,
                   "replay_word_bytes": REPLAY_WORD_BYTES, "raw_pair_bytes": RAW_PAIR_BYTES,
                   "blocks": 1, "registered_read_latency_edges": 1,
                   "read_ports": 1, "write_ports": 1},
        "buffer_highwater": {"staging_address": max(v["packet_bytes"] for v in vectors) - 1,
                              "header_crc_cache_bytes": REGISTER_CACHE_BYTES,
                              "descriptor_and_tail_bytes": DESCRIPTOR_BYTES + DESCRIPTOR_TAIL_BYTES,
                              "replay_bytes": min(REPLAY_WORD_BYTES, (63 + 7) // 8),
                              "raw_pair_bytes": RAW_PAIR_BYTES},
        "requested_scenarios": 9,
        "actual_scenarios": len(vectors),
        "directed_checks_requested": 6,
        "directed_checks_actual": directed,
        "restarts_requested": 1,
        "restarts_actual": events["restart_after_epoch_cancel"],
        "seed": SEED,
        "randomized_stall_policy": {"receive_ready_probability": 0.82,
                                    "consumer_ready_probability": 0.65,
                                    "fixed_read_stall_edges": "per-vector deterministic lists"},
        "requested_event_types": required_event_types,
        "actual_event_coverage": dict(sorted(events.items())),
        "staging_port_event_counts": dict(sorted(stage_counts.items())),
        "vectors": vectors,
        "limitations": [
            "Packet construction and validation cover only the selected BR88 header/CRC/descriptor staging subset.",
            "Replay bits and RAW words use independent byte slicing/indexing oracles; context coefficient decoding is not modeled.",
            "The outer packed-store external bus, its physical request retention, and concurrent tile-store hazards are outside this model.",
            "Simulated read latency is one edge by construction; the model does not establish a Vivado RAM primitive or physical latency.",
        ],
    }
    RESULT.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps({"result": str(RESULT), "source_sha256": source_hash,
                      "scenarios": len(vectors), "directed_checks": directed,
                      "event_coverage": dict(sorted(events.items()))}, indent=2))


if __name__ == "__main__":
    main()
