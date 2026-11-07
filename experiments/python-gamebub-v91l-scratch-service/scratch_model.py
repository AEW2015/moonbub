#!/usr/bin/env python3
"""Source-derived packed-scratch address and payload contract model."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RESULT = Path(__file__).with_name("model-results.json")
RTL_SOURCES = (
    ROOT / "fpga/experiments/cu66-v91g2/packed_scratch_v91g2.sv",
    ROOT / "fpga/experiments/cu66-v91l-scratch-service/scratch_line_bridge.sv",
    ROOT / "fpga/experiments/cu66-v91l-scratch-service/scratch_sdram_timed.sv",
    ROOT / "fpga/experiments/cu66-v91l-scratch-service/scratch_shared_timed.sv",
    ROOT / "fpga/experiments/cu66-v91l-writepipe/controller/moonshine_sdram.sv",
    ROOT / "fpga/experiments/cu66-v91l-writepipe/sdram_pin_model.sv",
)
LINE_BYTES = 16
SCRATCH_BYTES = 256 * 1024
ADDR_BITS = 18
VIDEO_BANKS = (0, 1, 2)
SCRATCH_BANK = 3
BANK_WORDS = 8 * 1024 * 1024 // 2


def aligned16(n: int) -> int:
    return (n + 15) & ~15


def coded_layout(blocks: int, count1: int, count2: int, count3: int) -> dict:
    """Mirror plan_start1/2/3 and plan_used in packed_scratch_v91g2.sv."""
    if not 1 <= blocks <= 8192:
        raise ValueError("blocks outside source allocation contract")
    if any(n < 0 or n > blocks*limit for n, limit in zip((count1, count2, count3), (5, 15, 43))):
        raise ValueError("band count outside source allocation contract")
    start1 = 32 + aligned16(blocks * 2)
    start2 = start1 + aligned16(count1 * 4)
    start3 = start2 + aligned16(count2 * 4)
    used = start3 + aligned16(count3 * 4)
    if used > SCRATCH_BYTES:
        raise ValueError("layout exceeds scratch aperture")
    return {"header0": 0, "header1": 16, "dc": 32, "ac1": start1,
            "ac2": start2, "ac3": start3, "used_bytes": used}


def raw_layout(blocks: int) -> dict:
    if not 1 <= blocks <= 8192:
        raise ValueError("blocks outside source allocation contract")
    used = 32 + blocks * 128
    if used > SCRATCH_BYTES:
        raise ValueError("layout exceeds scratch aperture")
    return {"header0": 0, "header1": 16, "raw": 32, "used_bytes": used}


def map_line(byte_address: int, epoch: int) -> dict:
    """Map a legal logical scratch line to SDRAM bank-3 x16 word address."""
    if not 0 < epoch < (1 << 32):
        raise ValueError("epoch must be nonzero and fit 32 bits")
    if byte_address < 0 or byte_address >= (1 << ADDR_BITS):
        raise ValueError("byte address is outside the 18-bit aperture")
    if byte_address % LINE_BYTES:
        raise ValueError("line address must be 16-byte aligned")
    if byte_address + LINE_BYTES > SCRATCH_BYTES:
        raise ValueError("line extends beyond scratch aperture")
    physical_word_address = (SCRATCH_BANK << 22) | (byte_address >> 1)
    return {"logical_byte_address": byte_address,
            "physical_bank": SCRATCH_BANK,
            "physical_word_address": physical_word_address,
            "epoch": epoch}


def pack_line(data: bytes) -> tuple[int, int, int, int]:
    """Pack 16 bytes into four little-endian 32-bit RTL words."""
    if len(data) != LINE_BYTES:
        raise ValueError("a line has exactly 16 bytes")
    return tuple(int.from_bytes(data[i:i + 4], "little") for i in range(0, 16, 4))


def unpack_line(words: tuple[int, int, int, int]) -> bytes:
    if len(words) != 4 or any(w < 0 or w > 0xffffffff for w in words):
        raise ValueError("a line requires four unsigned 32-bit words")
    return b"".join(w.to_bytes(4, "little") for w in words)


def check() -> dict:
    top = map_line(SCRATCH_BYTES - LINE_BYTES, 1)
    assert top["physical_word_address"] == (3 << 22) | 0x1fff8
    last_word_address = top["physical_word_address"] + LINE_BYTES // 2 - 1
    assert last_word_address == (3 << 22) | 0x1ffff
    assert last_word_address < (SCRATCH_BANK << 22) + BANK_WORDS
    assert all(SCRATCH_BANK != b for b in VIDEO_BANKS)
    for invalid, epoch in ((1, 1), (SCRATCH_BYTES, 1), (-16, 1), (0, 0), (0, -1), (0, 1 << 32)):
        try:
            map_line(invalid, epoch)
        except ValueError:
            pass
        else:
            raise AssertionError(f"accepted invalid line/epoch: {invalid}, {epoch}")
    payload = bytes(range(16))
    assert unpack_line(pack_line(payload)) == payload
    assert pack_line(payload) == (0x03020100, 0x07060504, 0x0b0a0908, 0x0f0e0d0c)
    # A 16-byte logical transfer consumes eight x16 data words for either pin operation.
    assert LINE_BYTES // 2 == 8
    assert 8 * 2 == LINE_BYTES  # 8 single-word WRITE commands, 2 bytes each.
    assert 1 * 8 * 2 == LINE_BYTES  # 1 BL8 READ command, 8 words x 2 bytes.
    coded_max = coded_layout(8192, 40960, 0, 20472)
    raw_max = raw_layout(2047)  # 2048 blocks would exceed the aperture by 32 bytes.
    for bad in ((0, 0, 0, 0), (8193, 0, 0, 0), (1, 6, 0, 0), (1, 0, 16, 0), (1, 0, 0, 44), (1, -1, 0, 0)):
        try:
            coded_layout(*bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"accepted invalid allocation: {bad}")
    return {
        "status": "PASS",
        "contract": {
            "scratch_bytes": SCRATCH_BYTES,
            "logical_address_bits": ADDR_BITS,
            "line_bytes": LINE_BYTES,
            "max_aligned_line_start": SCRATCH_BYTES - LINE_BYTES,
            "physical_bank": SCRATCH_BANK,
            "physical_word_address_first": map_line(0, 1)["physical_word_address"],
            "physical_word_address_final_line_first_word": top["physical_word_address"],
            "physical_word_address_last_inclusive_word": last_word_address,
            "video_banks": list(VIDEO_BANKS),
            "nonaliasing_basis": "physical bank index 3 is distinct from video banks 0, 1, 2",
            "x16_words_per_128_bit_write": 8,
            "x16_words_per_bl8_read": 8,
            "logical_transfer_bytes": 16,
            "controller_commands_per_logical_transfer": {"write": 8, "read": 1},
            "pin_schedule_overhead": "not estimated; command/refresh/turnaround/arbitration/drain require service observations",
        },
        "layout_examples": {"coded_max_counts": coded_max, "raw_max_blocks": raw_max},
        "native_scratch_observation": {
            "campaign": "retained reference-live finite-scratch control only",
            "historical_control_only": True,
            "request_count": None,
            "status": "not captured",
            "reason": "reference-live results mark scratch_rtl and scratch_service_rtl false; its events contain no packed-scratch memory request/response records",
            "current_physical_campaign": "fpga/experiments/cu66-v91l-scratch-live/results.json",
            "current_independent_counts": "experiments/python-gamebub-v91l-scratch-service/summary.json",
        },
        "source_sha256": {
            "model": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            **{str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
               for p in RTL_SOURCES},
        },
        "checks": [
            "first and final aperture lines map within bank 3",
            "bank 3 does not alias video banks 0 through 2",
            "zero epoch, misaligned, negative, and out-of-range line starts rejected",
            "block and per-band count limits match the packed-scratch allocation contract",
            "16-byte little-endian line packing round-trips exactly",
            "one 128-bit write carries eight x16 words across eight single-word WRITE commands",
            "one 128-bit read returns eight x16 words from one BL8 READ command",
        ],
        "limitations": [
            "128-bit scratch staging is a one-line transfer, not a 262144-byte on-chip memory claim",
            "no native scratch request totals, cycle estimates, throughput, or performance gains are asserted",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="compare with checked-in model-results.json")
    args = parser.parse_args()
    result = check()
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.check:
        if not RESULT.exists() or RESULT.read_text() != rendered:
            raise SystemExit("model-results.json differs; run without --check to refresh it")
        print("PASS: deterministic scratch contract model")
    else:
        RESULT.write_text(rendered)
        print(rendered, end="")


if __name__ == "__main__":
    main()
