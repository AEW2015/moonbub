#!/usr/bin/env python3
"""Small executable ownership/order contract for the next V91l live join.

This models protocol invariants only. It is not RTL evidence, an image decoder,
or a performance model. Run from the repository root; writes model-results.json.
"""
from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RESULT = Path(__file__).with_name("model-results.json")

@dataclass(frozen=True)
class Tag:
    epoch: int
    fid: int
    generation: int
    bank: int
    seq: int
    address: int
    def ack_identity(self): return (self.epoch, self.seq, self.bank, self.address)

@dataclass
class Tx:
    epoch: int
    fid: int
    refid: int
    generation: int
    bank: int
    expected_root: str
    status: str = "active"
    produced: bool = False
    hud_ok: bool = False
    hashes_ok: bool = False
    producer_done: bool = False
    failure: str = ""
    next_seq: int = 0
    outstanding: Tag | None = None

class Model:
    def __init__(self):
        self.accepted = {"fid": 10, "generation": 10, "root": "old-root", "hud": "old-hud", "seal": "old-seal", "bank": 0}
        self.front = {"fid": 10, "bank": 0}
        self.pending = None
        self.tx = None
        self.events = []
    def log(self, action, **fields): self.events.append({"action": action, **fields})
    def begin(self, epoch=7, fid=11, refid=10, generation=11):
        assert self.tx is None
        # Bank 1 is free: accepted/front own bank 0; pending is absent.
        self.tx = Tx(epoch, fid, refid, generation, 1, "new-root")
        self.log("begin", epoch=epoch, fid=fid, reference=refid, generation=generation, candidate_bank=1)
    def request_write(self):
        t = self.tx
        assert t and t.status == "active" and t.outstanding is None
        tag = Tag(t.epoch, t.fid, t.generation, t.bank, t.next_seq, t.next_seq)
        t.next_seq += 1
        t.outstanding = tag
        self.log("write_request", **tag.__dict__)
        return tag
    def ack(self, tag):
        t = self.tx
        assert t and t.outstanding is not None
        if tag.ack_identity() != t.outstanding.ack_identity():
            t.failure = "write_ack_tag_mismatch"
            t.status = "aborting"
            self.log("write_ack_rejected", received=tag.__dict__, expected=t.outstanding.__dict__, lease_held=True)
            return False
        t.outstanding = None
        self.log("write_ack_accepted", seq=tag.seq, lease_held=t.status == "aborting")
        if t.status == "aborting":
            t.status = "released"
            self.log("lease_released_after_drain", bank=t.bank)
        return True
    def mark_validated(self, producer_epoch=7, fail=""):
        t = self.tx; assert t
        if fail:
            t.failure = fail; t.status = "aborting"
            self.log("late_failure", reason=fail, accepted_unchanged=True)
            return
        if producer_epoch != t.epoch:
            t.failure = "producer_epoch_mismatch"; t.status = "aborting"
            self.log("producer_done_rejected", got_epoch=producer_epoch, expected_epoch=t.epoch)
            return
        t.produced = t.hud_ok = t.hashes_ok = t.producer_done = True
        self.log("producer_validated", epoch=producer_epoch, producer_done=True)
    def abort_or_reset(self, reason):
        t = self.tx; assert t
        t.failure = reason; t.status = "aborting"
        self.log(reason, outstanding=t.outstanding is not None, lease_held=True, accepted_unchanged=True)
        if t.outstanding is None:
            t.status = "released"
            self.log("lease_released_after_drain", bank=t.bank)
    def commit(self, writes_drained=True):
        t = self.tx; assert t
        ok = (t.status == "active" and t.produced and t.hud_ok and t.hashes_ok and
              t.producer_done and t.failure == "" and t.outstanding is None and writes_drained)
        if not ok:
            self.log("commit_blocked", reason=t.failure or "validation_or_write_drain_incomplete", accepted_unchanged=True)
            return False
        self.accepted = {"fid": t.fid, "generation": t.generation, "root": t.expected_root,
                         "hud": "new-hud", "seal": "new-seal", "bank": t.bank}
        self.pending = {"fid": t.fid, "bank": t.bank}
        t.status = "committed"
        self.log("atomic_accept", fid=t.fid, generation=t.generation, bank=t.bank, front_unchanged=True)
        return True
    def present(self, vblank, scanout_drained):
        if self.pending is None or not (vblank and scanout_drained):
            self.log("presentation_blocked", vblank=vblank, scanout_drained=scanout_drained,
                     front_fid=self.front["fid"])
            return False
        self.front = self.pending; self.pending = None
        self.log("present", fid=self.front["fid"], bank=self.front["bank"])
        return True

# V91l consumes one byte per token in plane, tile, byte-index order. Memory writes
# translate each token to raster address; the token stream itself is not raster order.
def canonical_token_at(ordinal):
    if ordinal < 5400*64: plane, local = 0, ordinal
    elif ordinal < (5400+1350)*64: plane, local = 1, ordinal-5400*64
    else: plane, local = 2, ordinal-(5400+1350)*64
    return plane, local//64, local%64

def raster_token_at(ordinal):
    if ordinal < 720*480: plane, local = 0, ordinal
    elif ordinal < 720*480 + 360*240: plane, local = 1, ordinal-720*480
    else: plane, local = 2, ordinal-720*480-360*240
    width = (720, 360, 360)[plane]
    tiles_across = width // 8
    raster_y, raster_x = divmod(local, width)
    tile = (raster_y//8)*tiles_across + raster_x//8
    index = (raster_y%8)*8 + raster_x%8
    return plane, tile, index

def address_of(plane, tile, index):
    width, height = ((720,480),(360,240),(360,240))[plane]
    base = (0, 720*480, 720*480+360*240)[plane]
    x = (tile % (width//8))*8 + index%8
    y = (tile // (width//8))*8 + index//8
    return base + y*width + x

def check(name, condition, notes=""):
    if not condition: raise AssertionError(name)
    return {"name": name, "result": "PASS", "notes": notes}

def main():
    checks=[]
    # Geometric/order contract and exact reversible mapping into raster memory.
    expected_prefix = [(0,0,i) for i in range(64)] + [(0,1,i) for i in range(8)]
    stream_prefix = [canonical_token_at(i) for i in range(len(expected_prefix))]
    checks.append(check("tile_stream_order", stream_prefix == expected_prefix,
                        "plane-major, tile-major, byte-major; raster address is separately computed"))
    checks.append(check("raster_order_is_not_tile_order", raster_token_at(8) != expected_prefix[8],
                        "a row-major raster producer must be tiled/reordered before the V91l hash input"))
    address_checks=[]
    for p,t,i in ((0,0,0),(0,1,0),(0,89,63),(1,0,0),(2,1349,63)):
        a=address_of(p,t,i); width=(720,360,360)[p]; base=(0,345600,432000)[p]
        local=a-base; y,x=divmod(local,width)
        address_checks.append((p,t,i,a,(y//8)*(width//8)+x//8,(y%8)*8+x%8))
    checks.append(check("tile_to_raster_address", all((t,i)==(t2,i2) for p,t,i,_,t2,i2 in address_checks),
                        "selected edge coordinates round-trip, including plane boundaries"))

    # Wrong epoch completion cannot authorize publication.
    m=Model(); m.begin(); tag=m.request_write(); m.ack(tag); m.mark_validated(producer_epoch=8)
    before=dict(m.accepted); allowed=m.commit()
    checks.append(check("wrong_producer_epoch_rejected", not allowed and m.accepted==before and m.tx.status=="aborting"))

    # ACKs are finite, exact-owner replies; wrong tags poison but do not retire the lease.
    m=Model(); m.begin(); tag=m.request_write(); wrong=Tag(tag.epoch+1,tag.fid,tag.generation,tag.bank,tag.seq,tag.address)
    accepted=m.ack(wrong)
    held=m.tx.outstanding==tag and m.tx.status=="aborting"
    before=dict(m.accepted); allowed=m.commit()
    checks.append(check("wrong_epoch_write_ack_keeps_lease", not accepted and held and not allowed and m.accepted==before))

    # Warm reset/abort cannot recycle a candidate bank with a request in flight.
    m=Model(); m.begin(); tag=m.request_write(); m.abort_or_reset("warm_reset")
    held=m.tx.status=="aborting" and m.tx.outstanding==tag
    m.ack(tag)
    checks.append(check("reset_pending_write_lease", held and m.tx.status=="released" and m.accepted["fid"]==10))

    # A late producer failure after all other checks still blocks atomic metadata update.
    m=Model(); m.begin(); tag=m.request_write(); m.ack(tag); m.mark_validated(fail="late_canonical_failure")
    before=dict(m.accepted); allowed=m.commit()
    checks.append(check("late_failure_rolls_back", not allowed and m.accepted==before and m.pending is None))

    # Validation may finish before outstanding memory write ACK; commit waits.
    m=Model(); m.begin(); tag=m.request_write(); m.mark_validated(); before=dict(m.accepted)
    blocked=m.commit(writes_drained=False); unchanged=m.accepted==before
    m.ack(tag); committed=m.commit()
    checks.append(check("commit_waits_for_write_ack", not blocked and unchanged and committed and m.accepted["fid"]==11))

    # Accepted reference may move at commit, while display front waits for both fences.
    m=Model(); m.begin(); tag=m.request_write(); m.ack(tag); m.mark_validated(); m.commit()
    pending=m.pending is not None and m.accepted["fid"]==11 and m.front["fid"]==10
    no_vblank=not m.present(False,True) and m.front["fid"]==10
    no_drain=not m.present(True,False) and m.front["fid"]==10
    presented=m.present(True,True) and m.front["fid"]==11
    checks.append(check("vblank_and_scandrain_gate_front", pending and no_vblank and no_drain and presented))

    result={"schema":"cu66-v91l-live-python-contract-v1", "status":"PASS_PROTOCOL_MODEL_ONLY",
            "claim_scope":"Independent abstract protocol model; no RTL, decoder, physical memory, or performance evidence.",
            "canonical_stream":{"bytes":518400,"order":"plane, tile, byte-index","plane_tiles":[5400,1350,1350],"bytes_per_tile":64},
            "write_ack":{"outstanding_capacity":1,"ack_match_fields":["epoch","token","bank","address"],
                         "wrapper_owned_transaction_fields":["fid","generation"],
                         "mismatch":"reject, fail transaction, retain lease until matching owner ACK drains"},
            "checks":checks,"check_count":len(checks)}
    RESULT.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({"status":result["status"],"checks":len(checks),"result":str(RESULT.relative_to(ROOT))},indent=2))
if __name__=="__main__": main()
