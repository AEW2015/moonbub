#!/usr/bin/env python3
"""Executable address and 8-byte write-ownership model for V91l rows.

This is a protocol/address model. It is not RTL, memory-controller, timing,
throughput, or hardware evidence.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RESULTS = Path(__file__).with_name("model-results.json")
ROW_BYTES = 8
PLANES = ((0, 720, 480, 5400), (345600, 360, 240, 1350),
          (432000, 360, 240, 1350))
CANONICAL_BYTES = 518400
HUD_BYTES = 42240


@dataclass(frozen=True)
class ByteToken:
    stream: str
    epoch: int
    fid: int
    generation: int
    bank: int
    plane: int
    tile: int
    byte_index: int
    address: int
    value: int

    @property
    def identity(self) -> tuple:
        return (self.stream, self.epoch, self.fid, self.generation,
                self.bank, self.plane, self.tile)


@dataclass(frozen=True)
class Row:
    identity: tuple
    address: int
    tokens: tuple[ByteToken, ...]
    request_token: int

    @property
    def values(self) -> bytes:
        return bytes(token.value for token in self.tokens)

    @property
    def ack_tag(self) -> tuple:
        first = self.tokens[0]
        return (first.epoch, self.request_token, first.bank, self.address)


def canonical_tokens() -> list[ByteToken]:
    """Enumerate every byte in V91l's plane/tile/index hash order."""
    out = []
    for plane, (base, width, _height, tile_count) in enumerate(PLANES):
        tiles_across = width // 8
        for tile in range(tile_count):
            tile_y, tile_x = divmod(tile, tiles_across)
            for byte_index in range(64):
                y, x = divmod(byte_index, 8)
                address = base + (tile_y * 8 + y) * width + tile_x * 8 + x
                # Deterministic markers make byte order observable without storing
                # or copying a raster corpus.
                value = (plane * 73 + tile * 19 + byte_index) & 0xFF
                out.append(ByteToken("canonical", 7, 11, 13, 1, plane, tile,
                                     byte_index, address, value))
    return out


def hud_tokens() -> list[ByteToken]:
    """Model the receipt-bound HUD stream as 5,280 aligned 8-byte rows."""
    out = []
    for index in range(HUD_BYTES):
        out.append(ByteToken("hud", 7, 11, 13, 1, 3, index // 64,
                             index % 64, 518400 + index,
                             (index * 29 + 17) & 0xFF))
    return out


def coalesce(tokens: list[ByteToken]) -> list[Row]:
    """Pack only eight consecutive, aligned, same-identity byte addresses."""
    rows: list[Row] = []
    pending: list[ByteToken] = []

    def flush() -> None:
        nonlocal pending
        if not pending:
            return
        if len(pending) != ROW_BYTES:
            raise ValueError("partial row at identity/end boundary")
        first = pending[0]
        if first.address % ROW_BYTES:
            raise ValueError("unaligned row start")
        if any(t.identity != first.identity for t in pending):
            raise ValueError("row crosses identity boundary")
        if [t.address for t in pending] != list(range(first.address, first.address + ROW_BYTES)):
            raise ValueError("noncontiguous row addresses")
        rows.append(Row(first.identity, first.address, tuple(pending), len(rows) + 1))
        pending = []

    for token in tokens:
        if pending and token.identity != pending[0].identity:
            flush()
        if pending and token.address != pending[-1].address + 1:
            flush()
        if not pending and token.address % ROW_BYTES:
            raise ValueError("unaligned row start")
        pending.append(token)
        if len(pending) == ROW_BYTES:
            flush()
    flush()
    return rows


def verify_full_bijection(tokens: list[ByteToken]) -> dict:
    """Check each plane's complete address set equals its full raster extent."""
    counts = []
    offset = 0
    for plane, (base, width, height, tile_count) in enumerate(PLANES):
        n = tile_count * 64
        addresses = [t.address for t in tokens[offset:offset + n]]
        expected = set(range(base, base + width * height))
        if len(addresses) != width * height or len(set(addresses)) != width * height:
            raise AssertionError(f"plane {plane}: duplicate or missing addresses")
        if set(addresses) != expected:
            raise AssertionError(f"plane {plane}: address set differs from raster")
        counts.append({"plane": plane, "bytes": len(addresses),
                       "unique_addresses": len(set(addresses)),
                       "raster_bytes": width * height})
        offset += n
    return {"planes": counts, "total_bytes": offset,
            "all_addresses_unique": True, "full_address_bijection": True}


class WriteOwner:
    """Single-row fill/offer/ACK/delivery protocol model.

    Accepted physical writes survive abort/reset as leases. They retire only on
    a matching ACK. Producer/hash state is killed, so the drained ACK is not
    delivered after cancellation.
    """

    def __init__(self) -> None:
        self.fill: list[ByteToken] = []
        self.offered: Row | None = None
        self.lease: Row | None = None
        self.delivery: list[ByteToken] = []
        self.cancelled = False
        self.error = False
        self.delivered: list[ByteToken] = []
        self.next_token = 1

    def accept_byte(self, token: ByteToken) -> None:
        if self.cancelled or self.offered or self.lease or self.delivery:
            raise RuntimeError("owner is not available for producer input")
        if self.fill and (token.identity != self.fill[0].identity
                          or token.address != self.fill[-1].address + 1):
            raise ValueError("row fill identity/address discontinuity")
        if not self.fill and token.address % ROW_BYTES:
            raise ValueError("unaligned row fill")
        self.fill.append(token)
        if len(self.fill) == ROW_BYTES:
            self.offered = Row(self.fill[0].identity, self.fill[0].address,
                               tuple(self.fill), self.next_token)
            self.next_token += 1
            self.fill.clear()

    def memory_accept(self) -> None:
        if self.offered is None or self.lease is not None:
            raise RuntimeError("no row offer or lease already active")
        self.lease, self.offered = self.offered, None

    def cancel(self) -> None:
        self.cancelled = True
        self.fill.clear()
        self.offered = None
        self.delivery.clear()

    def ack(self, tag: tuple, *, bus_error: bool = False,
            kill_same_edge: bool = False) -> bool:
        if self.lease is None:
            return False
        row = self.lease
        if tag != row.ack_tag:
            self.error = True
            return False  # wrong ACK cannot release the true physical lease
        self.lease = None
        if kill_same_edge:
            self.cancel()
        if bus_error:
            self.error = True
            return True
        if self.cancelled or self.error:
            return True
        self.delivery = list(row.tokens)
        return True

    def deliver_one(self) -> ByteToken:
        if not self.delivery or self.cancelled:
            raise RuntimeError("no hash byte available")
        token = self.delivery.pop(0)
        self.delivered.append(token)
        return token


def publication_allowed(*, hashes_complete: bool, all_writes_acked: bool,
                        drained: bool, failed: bool) -> bool:
    return hashes_complete and all_writes_acked and drained and not failed


def token_row(tokens: list[ByteToken]) -> Row:
    rows = coalesce(tokens)
    if len(rows) != 1:
        raise AssertionError("expected one row")
    return rows[0]


def protocol_checks() -> dict:
    row = token_row(canonical_tokens()[:8])
    wrong = WriteOwner()
    for token in row.tokens:
        wrong.accept_byte(token)
    wrong.memory_accept()
    wrong_tag = (row.ack_tag[0], row.ack_tag[1] + 100, *row.ack_tag[2:])
    wrong.ack(wrong_tag)
    wrong_ack_retains_lease = wrong.lease is not None
    wrong.ack(row.ack_tag)
    wrong_ack_matching_drain_delivered_zero = not wrong.delivered

    success = WriteOwner()
    for token in row.tokens:
        success.accept_byte(token)
    success.memory_accept()
    success.ack(row.ack_tag)
    for _ in range(8):
        success.deliver_one()

    bus = WriteOwner()
    for token in row.tokens:
        bus.accept_byte(token)
    bus.memory_accept()
    bus.ack(row.ack_tag, bus_error=True)

    # Cancellation at each state: partial fill, full offered row, accepted
    # pending lease, and partial hash delivery. A pending lease drains after kill.
    cancel_states = {}
    for kind in ("warm_cancel", "warm_reset"):
      for stage in ("partial_fill", "offer", "pending_ack", "partial_delivery"):
        owner = WriteOwner()
        for token in row.tokens[:3 if stage == "partial_fill" else 8]:
            owner.accept_byte(token)
        if stage in ("pending_ack", "partial_delivery"):
            owner.memory_accept()
        if stage == "partial_delivery":
            owner.ack(row.ack_tag)
            owner.deliver_one()
        delivered_before_cancel = len(owner.delivered)
        owner.cancel()
        retained = owner.lease is not None
        if retained:
            owner.ack(row.ack_tag)
        cancel_states[f"{kind}_{stage}"] = {"cancelled": owner.cancelled,
                                             "lease_retained_until_matching_ack": retained,
                                             "delivered_before_cancel": delivered_before_cancel,
                                             "pending_delivery_discarded": not owner.delivery}

    simultaneous = WriteOwner()
    for token in row.tokens:
        simultaneous.accept_byte(token)
    simultaneous.memory_accept()
    simultaneous.ack(row.ack_tag, kill_same_edge=True)

    # Reject short rows, identity changes, and gaps at a boundary.
    rejected = {}
    for name, tokens in (
        ("partial_row", canonical_tokens()[:7]),
        ("identity_boundary", [*canonical_tokens()[:7], hud_tokens()[0]]),
        ("address_gap", [*canonical_tokens()[:7],
                         ByteToken("canonical", 7, 11, 13, 1, 0, 1, 0, 9, 0)]),
    ):
        try:
            coalesce(tokens)
        except ValueError:
            rejected[name] = True
        else:
            rejected[name] = False
    if not all(rejected.values()):
        raise AssertionError("invalid row case was accepted")

    publication_gate = {
        "pending_ack_blocks_publication": not publication_allowed(
            hashes_complete=False, all_writes_acked=False,
            drained=False, failed=False),
        "incomplete_hash_blocks_publication": not publication_allowed(
            hashes_complete=False, all_writes_acked=True,
            drained=True, failed=False),
        "failed_candidate_blocks_publication": not publication_allowed(
            hashes_complete=True, all_writes_acked=True,
            drained=True, failed=True),
        "complete_successful_drained_candidate_allows_publication": publication_allowed(
            hashes_complete=True, all_writes_acked=True,
            drained=True, failed=False),
    }
    return {
        "wrong_ack_retains_lease": wrong_ack_retains_lease,
        "matching_ack_after_wrong_ack_drains_without_delivery": wrong_ack_matching_drain_delivered_zero,
        "clean_matching_ack_delivers_exactly_8_ordered_hash_bytes": (
            len(success.delivered) == 8 and
            [t.byte_index for t in success.delivered] == list(range(8))),
        "matching_bus_error_retires_without_delivery": bus.lease is None and not bus.delivered and bus.error,
        "cancellation_states": cancel_states,
        "same_edge_matching_ack_and_kill_delivers_zero": simultaneous.lease is None and not simultaneous.delivered,
        "rejected_partial_or_invalid_rows": rejected,
        "publication_gate": publication_gate,
    }


def main() -> None:
    canonical = canonical_tokens()
    hud = hud_tokens()
    bijection = verify_full_bijection(canonical)
    all_rows = coalesce(canonical + hud)
    canonical_rows = [row for row in all_rows if row.identity[0] == "canonical"]
    hud_rows = [row for row in all_rows if row.identity[0] == "hud"]
    if len(canonical) != CANONICAL_BYTES or len(hud) != HUD_BYTES:
        raise AssertionError("stream extent mismatch")
    if any(len(row.tokens) != ROW_BYTES or row.address % ROW_BYTES
           or len(set(t.address for t in row.tokens)) != ROW_BYTES
           for row in canonical_rows + hud_rows):
        raise AssertionError("row contiguity/alignment proof failed")
    if len(canonical_rows) != 64800 or len(hud_rows) != 5280:
        raise AssertionError("row request count mismatch")
    result = {
        "schema": "cu66-v91l-rows-model-results-v1",
        "status": "PASS",
        "scope": "Independent executable address/coalescing and write-ownership protocol model only; no RTL, hardware, or performance evidence.",
        "address_bijection": bijection,
        "stream_counts": {
            "canonical_bytes": len(canonical), "hud_bytes": len(hud),
            "ordered_bytes": len(canonical) + len(hud),
            "canonical_row_requests": len(canonical_rows),
            "hud_row_requests": len(hud_rows),
            "total_row_requests": len(canonical_rows) + len(hud_rows),
            "row_bytes": ROW_BYTES,
            "all_rows_contiguous_and_aligned": True,
            "byte_beat_count": len(canonical) + len(hud),
            "x16_payload_row_beats": (len(canonical) + len(hud)) // 2,
            "service_price_model": {
                "assumption": "FAST: byte request costs 1 payload beat + 1 overhead; row request costs 4 x16 payload beats + 1 overhead. SLOW: respective payload beats + 2..7 seeded overhead per request.",
                "fast_byte_service_units": (len(canonical) + len(hud)) * 2,
                "fast_row_service_units": (len(canonical_rows) + len(hud_rows)) * 5,
                "slow_byte_service_unit_range": [
                    (len(canonical) + len(hud)) * 3,
                    (len(canonical) + len(hud)) * 8],
                "slow_row_service_unit_range": [
                    (len(canonical) + len(hud)) // 2 + 2 * (len(canonical_rows) + len(hud_rows)),
                    (len(canonical) + len(hud)) // 2 + 7 * (len(canonical_rows) + len(hud_rows))],
                "interpretation": "deterministic service-price arithmetic only; not measured latency or throughput",
            },
            "structural_storage": {
                "row_payload_bytes": ROW_BYTES,
                "row_metadata": "one epoch/token/bank/plane/tile identity, start address, 4-bit fill count and 3-bit delivery index; no second payload copy",
                "concurrent_owned_rows": 1,
            },
        },
        "protocol_checks": protocol_checks(),
    }
    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    RESULTS.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
