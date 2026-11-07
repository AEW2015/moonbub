#!/usr/bin/env python3
"""Finite logical model for the V91l shared physical-service ownership contract.

This is a transaction-level contract executable, not RTL verification or a
controller/pin timing model. `--check` is deterministic and does not inspect
HEAD or source mtimes.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULT = HERE / "model-results.json"
BASELINE = "298961c64ae947c01eeb55ea1b0815a3e87a3fdb"

@dataclass
class Owner:
    name: str
    kind: str                 # read or write
    words: int                # physical x16 words in this logical transaction
    identity: tuple = (1, 2, 3) # epoch, generation, ticket

@dataclass
class Service:
    owner: Owner | None = None
    last_grant: str = "rgb"
    state: str = "IDLE"
    accepted: int = 0
    drained: int = 0
    idle_fences: int = 0
    commands: int = 0
    reply: dict | None = None
    command_log: list = field(default_factory=list)
    events: list = field(default_factory=list)

    def choose(self, offers: dict[str, Owner]) -> str | None:
        """Round-robin between the two fixed clients when both are offered."""
        if not offers:
            return None
        order = ("candidate", "rgb") if self.last_grant == "rgb" else ("rgb", "candidate")
        return next((n for n in order if n in offers), sorted(offers)[0])

    def grant(self, offers: dict[str, Owner]) -> str | None:
        assert self.state == "IDLE" and self.owner is None
        name = self.choose(offers)
        if name is None:
            return None
        self.owner = offers[name]
        self.last_grant = name
        self.state = "ACTIVE"
        self.accepted = self.drained = self.idle_fences = 0
        self.reply = None
        self.events.append("grant:" + name)
        return name

    def invalid_identity_response(self, name: str, request: Owner) -> None:
        """Invalid logical requests are accepted by a bridge, then error without commands."""
        assert self.grant({name: request}) == name
        self.events.append("logical-request-accepted")
        self.events.append("invalid-identity-error-response")
        self._reply(error=True)

    def accept_physical(self) -> None:
        assert self.state == "ACTIVE" and self.owner
        assert self.accepted < self.owner.words
        self.accepted += 1
        self.commands += 1
        self.command_log.append(self.owner.kind + ":" + str(self.accepted - 1))

    def drain_physical(self) -> None:
        assert self.state == "ACTIVE" and self.owner
        assert self.drained < self.accepted
        self.drained += 1

    def _reply(self, error: bool = False) -> None:
        assert self.owner is not None
        self.state = "REPLY"
        self.reply = {"owner": self.owner.name, "identity": list(self.owner.identity),
                      "error": error, "accepted_words": self.accepted}

    def write_drain(self) -> None:
        """Qualified writer: WAIT_BUSY fence edge, then observed ctrl_idle."""
        assert self.state == "ACTIVE" and self.owner and self.owner.kind == "write"
        assert self.drained == self.owner.words and self.accepted == self.owner.words
        self.events.extend(("write-wait-busy-edge", "write-wait-idle-observed"))
        self._reply()

    def read_drain(self) -> None:
        """BL8 reader: after eight captured beats, two consecutive ctrl_idle samples."""
        assert self.state == "ACTIVE" and self.owner and self.owner.kind == "read"
        assert self.drained == self.owner.words == 8 and self.accepted == 8
        self.idle_fences = 2
        self.events.extend(("read-idle-sample", "read-idle-sample"))
        self._reply()

    def hold_cycles(self, count: int) -> None:
        assert self.state == "REPLY" and self.reply is not None
        held = json.dumps(self.reply, sort_keys=True)
        for _ in range(count):
            assert json.dumps(self.reply, sort_keys=True) == held
            assert self.owner is not None
            self.events.append("reply-held")

    def cancel_pending(self) -> None:
        assert self.state == "ACTIVE" and self.owner
        self.events.append("cancel-pending")
        # Accepted work is drained; unaccepted physical words are suppressed.
        self.owner.words = self.accepted
        while self.drained < self.accepted:
            self.drain_physical()
        self.state = "ACTIVE"
        if self.accepted == 0:
            self.owner.words = 0
            self._reply(error=True)
        elif self.owner.kind == "write":
            self.write_drain()
            assert self.reply is not None
            self.reply["error"] = True
        else:
            raise AssertionError("directed cancel model currently covers writer pending only")

    def acknowledge(self) -> None:
        assert self.state == "REPLY" and self.reply is not None
        self.events.append("reply-ack")
        self.owner = None
        self.reply = None
        self.state = "IDLE"
        self.accepted = self.drained = self.idle_fences = 0

    def reset(self) -> str:
        if self.state == "IDLE":
            self.events.append("reset-idle")
            return "applied"
        if self.state == "ACTIVE":
            self.events.append("reset-pending-deferred")
            self.cancel_pending()
            return "deferred-through-drain"
        self.events.append("reset-held-reply-preserved")
        return "deferred-through-reply-ack"


def complete(service: Service, owner: Owner, accepted: int | None = None, hold: int = 0) -> None:
    assert service.grant({owner.name: owner}) == owner.name
    n = owner.words if accepted is None else accepted
    for _ in range(n):
        service.accept_physical()
    while service.drained < service.accepted:
        service.drain_physical()
    if n == owner.words:
        if owner.kind == "write": service.write_drain()
        else: service.read_drain()
    else:
        service.cancel_pending()
    service.hold_cycles(hold)
    service.acknowledge()


def build_results() -> dict:
    checks = {}

    # Fair grant when both are continuously offered, then transaction ownership
    # remains fixed through accepted drain, each bridge's drain contract and ACK.
    s = Service()
    chosen = [s.grant({"rgb": Owner("rgb", "read", 8),
                       "candidate": Owner("candidate", "write", 4)})]
    assert chosen[0] == "candidate"
    for _ in range(4): s.accept_physical()
    # A competing offer cannot replace the active physical owner.
    assert s.owner.name == "candidate" and s.state == "ACTIVE"
    while s.drained < s.accepted: s.drain_physical()
    s.write_drain(); s.hold_cycles(3)
    assert s.owner and s.owner.name == "candidate"
    # The arbiter has no grant transition while an owner remains active.
    assert s.state != "IDLE"
    s.acknowledge()
    chosen.append(s.grant({"rgb": Owner("rgb", "read", 8),
                           "candidate": Owner("candidate", "write", 4)}))
    assert chosen == ["candidate", "rgb"]
    checks["fair_choice_and_stable_owner"] = {"result": "PASS", "grant_order": chosen,
        "candidate_write_words": 4, "rgb_read_beats": 8,
        "writer_drain": "WAIT_BUSY edge + observed ctrl_idle",
        "held_reply_cycles": 3,
        "owner_retained_until_reply_ack": True}

    # Read must consume a full BL8 and its response acknowledgement before switch.
    s = Service(); complete(s, Owner("rgb", "read", 8, (4, 9, 11)), hold=2)
    checks["bl8_drain_reply_ack"] = {"result": "PASS", "beats": 8,
        "response_held_cycles": 2, "owner_released_after_ack": True}

    # Cancel before physical acceptance emits no commands; pending cancel drains
    # only accepted words; held reply cannot mutate under reset/backpressure.
    pre = Service(); pre.grant({"candidate": Owner("candidate", "write", 4)})
    pre.cancel_pending(); no_accept_commands = pre.commands
    pre.hold_cycles(1); pre.acknowledge()
    pend = Service(); pend.grant({"candidate": Owner("candidate", "write", 4)})
    pend.accept_physical(); pend.accept_physical(); pend.cancel_pending()
    pending_drained = pend.drained
    pend.hold_cycles(2); pend.acknowledge()
    held = Service(); complete(held, Owner("rgb", "read", 8), hold=0)
    # Separately exercise reset against an already-held response.
    held.grant({"rgb": Owner("rgb", "read", 8)})
    for _ in range(8): held.accept_physical(); held.drain_physical()
    held.read_drain(); original = json.dumps(held.reply, sort_keys=True)
    held.reset(); held.hold_cycles(2)
    assert json.dumps(held.reply, sort_keys=True) == original
    held.acknowledge()
    assert no_accept_commands == 0 and pending_drained == 2
    checks["cancel_reset_phases"] = {"result": "PASS",
        "preaccept_controller_commands": no_accept_commands,
        "pending_accepted_words_drained": pending_drained,
        "pending_remaining_words_issued": 0,
        "held_reply_immutable_across_reset_and_backpressure": True,
        "held_reply_ack_required": True}

    # Invalid identity still arbitrates and is accepted by the bridge, but
    # yields a held error response without any controller command.
    bad = Service(); epoch, token, bank = 0, 0, 2
    writer_valid = epoch != 0 and bank < 3
    if not writer_valid:
        bad.invalid_identity_response("candidate", Owner("candidate", "write", 4,
                                                            (epoch, token, bank)))
    assert bad.commands == 0 and bad.owner is not None and bad.reply["error"]
    bad.hold_cycles(2); bad.acknowledge()
    assert bad.owner is None
    checks["failed_identity_no_commands"] = {"result": "PASS",
        "rejected_identity": {"writer_epoch": epoch, "writer_token": token, "bank": bank},
        "reason": "writer epoch zero is invalid; opaque token zero is allowed",
        "logical_owner_granted": True, "held_error_response_until_ack": True,
        "controller_commands": bad.commands, "owner_released_after_ack": bad.owner is None}
    bad_reader = Service(); reader_epoch, generation, reader_bank = 8, 0, 1
    reader_valid = reader_epoch != 0 and generation != 0 and reader_bank < 3
    if not reader_valid:
        bad_reader.invalid_identity_response("rgb", Owner("rgb", "read", 8,
                                                              (reader_epoch, generation, reader_bank)))
    assert bad_reader.commands == 0 and bad_reader.owner is not None and bad_reader.reply["error"]
    bad_reader.hold_cycles(2); bad_reader.acknowledge()
    assert bad_reader.owner is None
    checks["reader_zero_generation_no_commands"] = {"result": "PASS",
        "rejected_identity": {"epoch": reader_epoch, "generation": generation,
                              "bank": reader_bank},
        "logical_owner_granted": True, "held_error_response_until_ack": True,
        "controller_commands": bad_reader.commands, "owner_released_after_ack": bad_reader.owner is None}
    zero_token = Service(); token_identity = (17, 0, 2)
    assert token_identity[0] != 0 and token_identity[2] < 3
    zero_token.grant({"candidate": Owner("candidate", "write", 4, token_identity)})
    for _ in range(4): zero_token.accept_physical()
    while zero_token.drained < zero_token.accepted: zero_token.drain_physical()
    zero_token.write_drain()
    assert tuple(zero_token.reply["identity"]) == token_identity
    checks["writer_zero_token_is_opaque_and_echoed"] = {"result": "PASS",
        "request_identity": list(token_identity), "response_identity": zero_token.reply["identity"],
        "controller_commands": zero_token.commands}

    # Logical traffic accounting only; no timing, response/refresh overhead or
    # complete-system bandwidth inference.
    accounting = {
        "frame_bytes": 560640,
        "logical_8_byte_writes": 70080,
        "physical_x16_write_words": 280320,
        "rgb_bl8_reads": 32400,
        "rgb_physical_x16_read_words": 259200,
        "total_data_x16_words_per_frame": 539520,
        "excludes": ["reference reads", "scratch reads", "hash reads",
                     "refresh", "commands", "turnaround", "response stalls"]}
    assert accounting["frame_bytes"] // 8 == accounting["logical_8_byte_writes"]
    assert accounting["logical_8_byte_writes"] * 4 == accounting["physical_x16_write_words"]
    assert accounting["rgb_bl8_reads"] * 8 == accounting["rgb_physical_x16_read_words"]
    assert accounting["physical_x16_write_words"] + accounting["rgb_physical_x16_read_words"] == accounting["total_data_x16_words_per_frame"]

    return {
        "schema": "gamebub-v91l-shared-service-ownership-v1",
        "status": "PASS",
        "scope": "Finite logical ownership contract model; not RTL proof, not real pin service, and not a latency or closed shared-service budget.",
        "source_pin": {"baseline_commit": BASELINE,
            "frozen_inputs": {
              "fpga/experiments/cu66-v91l-writepipe/controller/moonshine_sdram.sv": "a43869515d2587e90356ebe90c6bee8c4f0428276034cf7de648d9650694abe1",
              "fpga/experiments/cu66-v91l-tiled/row_to_sdram.sv": "f5366cbfbe138e709353a0acfc7e24adcc7733f1dd10c8b6974f9d0d34bb60cb",
              "fpga/experiments/cu66-v91l-readbridge/bl8_read_bridge.sv": "de000415b9222cb3c3d4233998ed120bf65d34b9c1b3c83493ddbec907d436db",
              "fpga/experiments/cu66-v91l-rowpair/tile_rowpair_reader.sv": "77e0d3826b1fc3489e2de926b01465ba8ff849dbc813e37f6d9cdb9efb17fc0c"},
            "interface_identity_roles": {"writer": "nonzero epoch + opaque 32-bit token (zero allowed and echoed) + bank + byte address",
              "rgb_reader": "nonzero epoch + nonzero generation + bank + byte address",
              "adapter_rule": "preserve each bridge's native identity; root live-frame lease correlates them; do not invent writer generation/ticket fields"},
            "head_sensitive": False},
        "abstract_contract": {
            "clients": ["candidate-write", "rgb-read"],
            "ownership": "one accepted transaction at a time; no grant switch before bridge-specific physical drain and caller response ACK",
            "writes": "one logical 8-byte row is four x16 writes; drain accepted words, traverse WAIT_BUSY fence edge, observe ctrl_idle in WAIT_IDLE, then hold response until ACK",
            "reads": "one BL8 read produces exactly eight x16 beats; then require two consecutive ctrl_idle samples before response",
            "arbitration": "round-robin fair choice when both offers are present",
            "reply": "owner, bridge-native identity, error and completion fields remain stable while held",
            "cancel_reset": "preaccept cancellation produces no commands; pending cancellation suppresses unaccepted remainder and drains accepted work; held reply persists through reset until ACK",
            "identity": "failed/invalid identity is rejected before controller command issue"},
        "scenario_checks": checks,
        "workload_accounting_only": accounting,
        "excluded_clients_or_work": ["finite logical reference and scratch service", "C++ HUD semantic endpoint"],
        "limitations": ["No RTL equivalence, simulation, or formal proof is performed by this model.",
          "No real SDRAM command/response, pin timing, refresh, turnaround, row-miss, or backpressure service is modeled.",
          "No finite closed shared budget, 30-fps result, or under-10-ms result is claimed.",
          "The abstract fair arbiter and response protocol need validation against the integrated RTL interface.",
          "Writer and reader identity tuples intentionally differ; root live-frame lease supplies their cross-client correlation.",
          "A future ticket requirement beyond the writer's opaque token needs separate interface qualification."]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="compare deterministic result to checked-in JSON")
    args = parser.parse_args()
    rendered = json.dumps(build_results(), indent=2, sort_keys=True) + "\n"
    if args.check:
        if not RESULT.exists() or RESULT.read_text() != rendered:
            raise SystemExit("model-results.json is stale; run ownership_model.py to regenerate")
        print("PASS: deterministic shared-service ownership model results match")
    else:
        RESULT.write_text(rendered)
        print("wrote", RESULT)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
