#!/usr/bin/env python3
"""Bounded abstract bridge/controller model for the frozen SDRAM RTL.

This is a protocol and source-FSM model only. It does not model pins, memory
contents, timing closure, or throughput. Run it to regenerate model-results.json.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "fpga/rtl/moonshine_sdram.sv"
RESULTS = Path(__file__).with_name("model-results.json")
BANK_BYTES = 560_640
BYTE_ADDR_LIMIT = 560_640
ROW_BYTES = 8


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def physical_word_address(bank: int, byte_addr: int, word_index: int = 0) -> int:
    if bank not in range(3):
        raise ValueError("candidate bank must be 0..2; bank 3 is reserved")
    if byte_addr < 0 or byte_addr + ROW_BYTES > BYTE_ADDR_LIMIT or byte_addr % ROW_BYTES:
        raise ValueError("byte address must be an in-range, 8-byte-aligned row")
    if word_index not in range(4):
        raise ValueError("word index must be 0..3")
    return (bank << 22) | (byte_addr // 2) | word_index


def decode_controller_address(word_addr: int) -> dict:
    if not 0 <= word_addr < (1 << 24):
        raise ValueError("controller word address must fit 24 bits")
    return {"bank": (word_addr >> 22) & 3,
            "row": (word_addr >> 9) & 0x1FFF,
            "column": word_addr & 0x1FF}


@dataclass
class Controller:
    """Relevant controller FSM service behavior; one transition per clock edge."""
    refresh_period: int = 750
    cycle: int = 0
    state: str = "IDLE"
    delay: int = 0
    next_state: str = "IDLE"
    refresh_count: int = 0
    open_rows: dict[int, int] | None = None
    commands: list[dict] | None = None
    responses: list[dict] | None = None

    def __post_init__(self):
        self.open_rows = {} if self.open_rows is None else self.open_rows
        self.commands = [] if self.commands is None else self.commands
        self.responses = [] if self.responses is None else self.responses

    @property
    def ready(self) -> bool:
        return self.state == "IDLE" and self.refresh_count < self.refresh_period

    def _wait(self, n: int, after: str) -> None:
        self.delay, self.next_state, self.state = n, after, "WAITING"

    def step(self, request: tuple[bool, int, int] | None = None) -> bool:
        """Advance one posedge; request=(is_write, word_addr, data) if offered.

        Returns whether the controller accepted the request on this edge.
        A read acceptance emits eight response beats, matching READ_WAIT and
        READ_BURST. Data values are abstract placeholders.
        """
        accepted = False
        old_state = self.state
        refresh_reset = False
        if old_state == "IDLE":
            if self.refresh_count >= self.refresh_period:
                self.state = "REFRESH_PRE"
            elif request is not None:
                accepted = True
                write, addr, _data = request
                dec = decode_controller_address(addr)
                self._active_request = (write, addr, dec)
                if dec["bank"] in self.open_rows:
                    if self.open_rows[dec["bank"]] == dec["row"]:
                        self.state = "RW_CMD"
                    else:
                        self.state = "PRECHARGE"
                else:
                    self.state = "ACTIVATE"
        elif old_state == "PRECHARGE":
            _, _, dec = self._active_request
            self.commands.append({"cycle": self.cycle, "command": "PRECHARGE", **dec})
            self.open_rows.pop(dec["bank"], None)
            self._wait(2, "ACTIVATE")
        elif old_state == "ACTIVATE":
            _, _, dec = self._active_request
            self.commands.append({"cycle": self.cycle, "command": "ACTIVATE", **dec})
            self.open_rows[dec["bank"]] = dec["row"]
            self._wait(2, "RW_CMD")
        elif old_state == "RW_CMD":
            write, addr, dec = self._active_request
            self.commands.append({"cycle": self.cycle,
                                  "command": "WRITE" if write else "READ", **dec})
            if write:
                self._wait(3, "IDLE")
            else:
                self.delay, self.state = 5, "READ_WAIT"
                self._read_addr = addr
        elif old_state == "WAITING":
            if self.delay == 0:
                self.state = self.next_state
            else:
                self.delay -= 1
        elif old_state == "READ_WAIT":
            if self.delay == 0:
                for i in range(8):
                    self.responses.append({"cycle": self.cycle + i,
                                           "word_address": self._read_addr + i,
                                           "beat": i})
                self.state = "READ_BURST"
                self.beat = 1
            else:
                self.delay -= 1
        elif old_state == "READ_BURST":
            if self.beat == 7:
                self.state = "IDLE"
            self.beat = (self.beat + 1) & 7
        elif old_state == "REFRESH_PRE":
            self.commands.append({"cycle": self.cycle, "command": "PRECHARGE_ALL"})
            self.open_rows.clear()
            self._wait(2, "REFRESH")
        elif old_state == "REFRESH":
            self.commands.append({"cycle": self.cycle, "command": "AUTO_REFRESH"})
            self.refresh_count = 0
            refresh_reset = True
            self._wait(8, "IDLE")
        else:
            raise AssertionError(f"unsupported controller state {old_state}")
        if not refresh_reset:
            self.refresh_count = min(65535, self.refresh_count + 1)
        self.cycle += 1
        return accepted

    def transact(self, write: bool, address: int, data: int = 0) -> tuple[int, int]:
        accepted_at = None
        for _ in range(20_000):
            if self.step((write, address, data)):
                accepted_at = self.cycle - 1
                break
            # Keep request_valid asserted and advance exactly one edge per
            # iteration, including the edge that first returns to IDLE.
        if accepted_at is None:
            raise RuntimeError("controller transaction watchdog")
        # Requests are held valid through request_ready; after acceptance, run
        # until the controller is idle (the RTL's physical owner drain point).
        while not (self.state == "IDLE" and self.cycle > accepted_at + 1):
            self.step(None)
        return accepted_at, self.cycle


def byte_rmw(initial: bytes, byte_offset: int, value: int) -> dict:
    """Abstract single-byte update using one BL8 read and one x16 write."""
    if len(initial) != 16 or byte_offset not in range(16) or value not in range(256):
        raise ValueError("RMW requires 16 bytes, offset 0..15, and byte value")
    before = bytes(initial)
    after = bytearray(before)
    after[byte_offset] = value
    target_word = byte_offset // 2
    return {"read_words": 8, "write_words": 1, "target_word_index": target_word,
            "before_hex": before.hex(), "after_hex": bytes(after).hex(),
            "preserved_offsets": [i for i in range(16) if i != byte_offset],
            "neighbor_byte_preserved": after[byte_offset ^ 1] == before[byte_offset ^ 1]}


def bridge_job(bank: int, byte_addr: int, cancel_after_accept: bool = False) -> dict:
    """Four-word row job with a single physical owner and warm-cancel drain."""
    ctrl = Controller()
    words = [physical_word_address(bank, byte_addr, i) for i in range(4)]
    epoch, token = 17, 0xCAFE0001
    accepted, drained = [], []
    cancel_seen = False
    for i, word in enumerate(words):
        a, d = ctrl.transact(True, word, 0x1200 + i)
        accepted.append({"word_index": i, "word_address": word, "cycle": a})
        drained.append({"word_index": i, "cycle": d})
        if cancel_after_accept and not cancel_seen:
            # Cancellation takes effect after this accepted word drains. The
            # logical owner retains its epoch/token until then; no later word
            # may be issued and an error completion is held for caller accept.
            cancel_seen = True
            break
    return {"epoch": epoch, "token": token, "logical_bank": bank,
            "logical_byte_addr": byte_addr, "physical_words": words,
            "accepted_words": accepted, "drained_words": drained,
            "cancelled": cancel_seen,
            "cancel_requested_cycle": accepted[0]["cycle"] if cancel_seen else None,
            "completion_error": cancel_seen,
            "owner_released_after_word_drain": bool(drained),
            "epoch_token_candidate_bank_lease_held_until_drain":
                bool(cancel_seen and accepted and drained and
                     accepted[0]["cycle"] < drained[0]["cycle"]),
            "lease_release_cycle": drained[0]["cycle"] if cancel_seen and drained else None,
            "remaining_words_issued_after_cancel": 0,
            "completion_waits_for_caller_accept": cancel_seen}


def main() -> None:
    source = SOURCE.read_bytes()
    src = source.decode("ascii")
    required = ["assign request_ready=state==IDLE && refresh_count<REFRESH_CYCLES",
                "if(is_write)begin sdram_we_n<=0;wait_cycles(3,IDLE);end",
                "else begin delay<=5;state<=READ_WAIT;beat<=0;end",
                "READ_WAIT:if(delay==0)begin", "if(beat==7)state<=IDLE;"]
    for fragment in required:
        if fragment not in src:
            raise AssertionError(f"frozen controller source changed: missing {fragment}")

    mappings = []
    for bank in range(3):
        words = [physical_word_address(bank, 0, i) for i in range(4)]
        mappings.append({"logical_bank": bank, "logical_byte_addr": 0,
                         "controller_word_addresses": words,
                         "decoded": [decode_controller_address(x) for x in words]})
    row_job = bridge_job(2, 560_624)
    cancelled = bridge_job(1, 8, cancel_after_accept=True)
    rmw = byte_rmw(bytes(range(16)), 5, 0xA5)

    # Bounded source-FSM probes: one cold write followed by three same-row
    # word writes. The model's service loop includes source waits and refresh.
    ctrl = Controller()
    probe = [physical_word_address(0, 0, i) for i in range(4)]
    probe_times = [ctrl.transact(True, a, i)[0] for i, a in enumerate(probe)]
    write_commands = [c for c in ctrl.commands if c["command"] == "WRITE"]
    if len(write_commands) != 4 or any(b <= a for a, b in zip(probe_times, probe_times[1:])):
        raise AssertionError("bounded FSM write probe failed")
    if not rmw["neighbor_byte_preserved"] or rmw["write_words"] != 1:
        raise AssertionError("byte RMW neighbor preservation failed")
    if len(cancelled["accepted_words"]) != 1 or cancelled["remaining_words_issued_after_cancel"] != 0:
        raise AssertionError("warm-cancel physical drain contract failed")
    if not cancelled["epoch_token_candidate_bank_lease_held_until_drain"]:
        raise AssertionError("warm cancellation released physical ownership before drain")

    rowmiss_ctrl = Controller()
    rowmiss_ctrl.transact(True, physical_word_address(0, 0), 0x1111)
    rowmiss_ctrl.transact(True, physical_word_address(0, 1024), 0x2222)
    rowmiss_commands = [c["command"] for c in rowmiss_ctrl.commands]
    if "PRECHARGE" not in rowmiss_commands or rowmiss_commands.count("ACTIVATE") != 2:
        raise AssertionError("row-miss PRECHARGE/ACTIVATE sequence missing")

    read_ctrl = Controller()
    read_ctrl.transact(False, physical_word_address(0, 0))
    if len(read_ctrl.responses) != 8:
        raise AssertionError("source-FSM read probe did not produce eight BL8 beats")

    refresh_ctrl = Controller(refresh_count=750)
    refresh_accept, refresh_drain = refresh_ctrl.transact(
        True, physical_word_address(0, 0), 0x3333)
    refresh_commands = [c["command"] for c in refresh_ctrl.commands]
    if refresh_commands[:2] != ["PRECHARGE_ALL", "AUTO_REFRESH"] or refresh_accept < 10:
        raise AssertionError("refresh priority / recovery sequence missing")

    result = {
        "schema": "cu66-v91l-sdram-model-v1",
        "status": "PASS",
        "scope": "Bounded abstract protocol and source-FSM model only; no RTL proof, implementation, pin-level, throughput, or performance claim.",
        "source": {"path": "fpga/rtl/moonshine_sdram.sv", "sha256": sha(source),
                   "interface": "24-bit x16 word address, 16-bit data",
                   "request_ready": "IDLE and refresh_count < REFRESH_CYCLES",
                   "read": "BL8, CAS3 mode 13'h233, delay 5 then eight response beats",
                   "write": "single-word WRITE; wait_cycles(3,IDLE)",
                   "response": "read response_valid only; no write ACK, error, or byte mask",
                   "refresh_cycles": 750},
        "mapping": {"formula": "controller_word=(candidate_bank << 22) | (byte_addr >> 1) | word_index; word_index=0..3",
                    "controller_address_fields": {"bank": "[23:22]", "row": "[21:9]", "column": "[8:0]"},
                    "aperture": "8 MiB word-address aperture per controller bank; only byte offsets 0..560639 populated; candidate bank 3 reserved",
                    "rejected_alternative": "(logical_bank*560640 + byte_addr)/2 packed ranges into controller bank 0; retained in planning notes only",
                    "rows": mappings},
        "row_write_probe": row_job,
        "warm_cancel_probe": cancelled,
        "byte_control_policy": {"status": "abstract policy only; not the row-only bridge implementation",
                                "rule": "read 8 x16 words, replace selected byte in its x16 word, write exactly that one x16 word",
                                "probe": rmw},
        "fsm_probe": {"open_row_word_write_acceptance_cycles": probe_times,
                      "commands": ctrl.commands,
                      "note": "Cycle schedule follows the source state/wait transitions; refresh may preempt requests at IDLE."},
        "row_miss_probe": {"commands": rowmiss_ctrl.commands},
        "read_bl8_probe": {"commands": read_ctrl.commands,
                            "response_count": len(read_ctrl.responses),
                            "response_cycles": [r["cycle"] for r in read_ctrl.responses]},
        "refresh_probe": {"starting_refresh_count": 750,
                          "commands": refresh_ctrl.commands,
                          "request_accept_cycle": refresh_accept,
                          "physical_drain_cycle": refresh_drain},
        "ownership_contract": [
            "One logical request owns the controller until each accepted physical word request returns to IDLE.",
            "A warm cancel retains epoch/token and logical 8-byte lease until the accepted physical word drains.",
            "After warm cancel, stop issuing remaining words and hold the cancellation completion until caller acceptance.",
            "Cold power reset requires external quiescence; resetting with an accepted physical owner is illegal.",
            "Do not change accepted data or front metadata while physical ownership is outstanding.",
            "Controller has no physical write ACK/error; wrapper completion and cancellation error are abstract protocol signals."],
        "limitations": ["Model does not prove RTL behavior or reset safety.",
                       "Read response data and memory contents are abstract; no pin-level timing is modeled.",
                       "The byte RMW policy is modeled separately and is not claimed implemented by the row-only bridge.",
                       "No measured parallel service or concurrency gain is claimed for the bank-spaced mapping."]
    }
    RESULTS.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
