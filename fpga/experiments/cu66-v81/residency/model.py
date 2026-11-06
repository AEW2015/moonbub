"""Transactional bank residency prototype; tokens are bytes or native tile digests.

There is no aliasing: each committed candidate contains all canonical tiles.
Oracle equality/fingerprints are validation inputs, not a proposed hardware gate.
"""
from dataclasses import dataclass


class Rejected(Exception):
    pass


def require(condition, reason):
    if not condition:
        raise Rejected(reason)


@dataclass
class Transaction:
    fid: int
    identity: str
    candidate: int
    key: bool
    decoded: tuple
    same: tuple
    shadow: list
    cursor: int = 0
    writes: int = 0
    elisions: int = 0
    unchanged_misses: int = 0
    changed_writes: int = 0


class Residency:
    def __init__(self, tiles):
        self.tiles = tiles
        self.banks = [[None] * tiles for _ in range(3)]
        self.accepted = None
        self.masks = [0] * tiles
        self.reference = None
        self.front = None
        self.draining = set()
        self.accepted_fid = None
        self.last_identity = None
        self.tx = None
        self.total_writes = self.total_elisions = self.certificates = 0
        self.commits = self.aborts = self.replays = 0

    def leased(self):
        return self.draining | {b for b in (self.reference, self.front) if b is not None}

    def check(self):
        """Every residency certificate names actual bytes of CURRENT reference."""
        if self.accepted is None:
            require(not any(self.masks), "unbound certificates")
            return
        require(self.banks[self.reference] == list(self.accepted), "reference physical image")
        for tile, mask in enumerate(self.masks):
            require(mask & (1 << self.reference), "reference certificate absent")
            require(0 <= mask < 8, "three-bit mask")
            for bank in range(3):
                if mask & (1 << bank):
                    require(self.banks[bank][tile] == self.accepted[tile], "corrupt accepted certificate")

    def begin(self, fid, identity, candidate, key, decoded, same):
        require(self.tx is None, "transaction active")
        require(len(decoded) == len(same) == self.tiles, "tile coverage")
        require(0 <= candidate < 3 and candidate not in self.leased(), "candidate leased")
        require(key or self.accepted is not None, "delta without accepted reference")
        require(self.accepted_fid is None or fid > self.accepted_fid, "nonmonotonic identity")
        self.check()
        # Independent native byte mask must agree with the fingerprint oracle.
        # Synthetic cases use full byte strings, including exact mismatch cases.
        if self.accepted is not None:
            require(all(bool(same[i]) == (decoded[i] == self.accepted[i]) for i in range(self.tiles)),
                    "decoded/reference equality certificate mismatch")
        else:
            require(not any(same), "equality without reference")
        self.tx = Transaction(fid, identity, candidate, key, tuple(decoded), tuple(same), [0] * self.tiles)

    def step(self, count=None):
        tx = self.tx
        require(tx is not None, "no transaction")
        require(tx.candidate not in self.leased(), "candidate lease changed")
        end = self.tiles if count is None else min(self.tiles, tx.cursor + count)
        bit = 1 << tx.candidate
        for tile in range(tx.cursor, end):
            token = tx.decoded[tile]
            if not tx.key and tx.same[tile] and self.masks[tile] & bit:
                # Assert actual physical fingerprint for EVERY claimed elision.
                require(self.banks[tx.candidate][tile] == self.accepted[tile] == token,
                        "elision physical-byte certificate rejected")
                tx.elisions += 1
                self.total_elisions += 1
                self.certificates += 1
                tx.shadow[tile] = self.masks[tile]
            else:
                # Clear OLD accepted certificate BEFORE first physical mutation.
                # This mutation intentionally survives transaction abort.
                self.masks[tile] &= ~bit
                self.banks[tx.candidate][tile] = token
                tx.writes += 1
                self.total_writes += 1
                tx.unchanged_misses += int(not tx.key and tx.same[tile])
                tx.changed_writes += int(not tx.key and not tx.same[tile])
                tx.shadow[tile] = (self.masks[tile] if not tx.key and tx.same[tile] else 0) | bit
            tx.cursor = tile + 1

    def commit(self, authenticated=True):
        tx = self.tx
        require(tx is not None and tx.cursor == self.tiles, "incomplete candidate")
        require(authenticated, "canonical/HUD/display authentication failure")
        require(self.banks[tx.candidate] == list(tx.decoded), "commit physical canonical image mismatch")
        for tile, mask in enumerate(tx.shadow):
            require(mask & (1 << tx.candidate), "candidate certificate absent")
            for bank in range(3):
                if mask & (1 << bank):
                    require(self.banks[bank][tile] == tx.decoded[tile], "commit shadow certificate mismatch")
        # Atomic accepted-reference + shadow-map publication only here.
        self.accepted, self.masks, self.reference = tx.decoded, tx.shadow, tx.candidate
        self.accepted_fid, self.last_identity = tx.fid, tx.identity
        self.tx = None
        self.commits += 1
        self.check()
        return tx

    def abort(self):
        require(self.tx is not None, "no transaction")
        self.tx = None
        self.aborts += 1
        self.check()

    def replay_ack(self, fid, identity):
        require(self.tx is None and fid == self.accepted_fid and identity == self.last_identity,
                "replay identity mismatch")
        self.check()
        self.replays += 1
        return self.reference

    def present(self, hold_old_drain=False):
        require(self.reference is not None, "nothing to present")
        old = self.front
        self.front = self.reference
        if hold_old_drain and old is not None and old != self.front:
            self.draining.add(old)

    def reset(self):
        # Display/front/drain leases survive a decode reset until actual release.
        self.tx = None
        self.accepted = self.reference = self.accepted_fid = self.last_identity = None
        self.masks = [0] * self.tiles
        self.check()


def synthetic_cases():
    """Independent small full-byte examples, before any real fixture is read."""
    results = []
    A, B, C, D = (bytes([value]) * 64 for value in (11, 22, 33, 44))

    def reject(name, operation):
        try:
            operation()
        except Rejected as exc:
            results.append(dict(case=name, status="PASS_EXPECTED_REJECTION", reason=str(exc)))
        else:
            raise AssertionError(name + " unexpectedly accepted")

    def frame(m, fid, bank, pixels, key=False, present=True):
        same = tuple(v == old for v, old in zip(pixels, m.accepted)) if m.accepted else (False,) * m.tiles
        m.begin(fid, str(fid), bank, key, pixels, same)
        m.step()
        tx = m.commit()
        if present:
            m.present()
        return tx

    m = Residency(4)
    reject("cold_delta_rejected", lambda: m.begin(0, "0", 0, False, (A,) * 4, (False,) * 4))
    assert frame(m, 0, 0, (A, B, C, D), True).writes == 4
    reject("reference_front_write_rejected", lambda: m.begin(1, "1", 0, False, m.accepted, (True,) * 4))
    assert frame(m, 1, 2, m.accepted).writes == 4  # deliberately non-round-robin
    assert frame(m, 2, 1, m.accepted).writes == 4
    assert all(mask == 7 for mask in m.masks)
    tx = frame(m, 3, 0, m.accepted)
    assert (tx.writes, tx.elisions) == (0, 4)
    results.append(dict(case="three_bank_warmup_nontrivial_selection", status="PASS", elisions=tx.elisions))
    before = (m.total_writes, m.total_elisions, list(m.masks), m.reference)
    assert m.replay_ack(3, "3") == 0
    assert before == (m.total_writes, m.total_elisions, list(m.masks), m.reference)
    reject("lost_ack_changed_identity_rejected", lambda: m.replay_ack(3, "altered"))
    results.append(dict(case="lost_ack_idempotent_no_decode_or_store", status="PASS"))

    old = m.accepted
    m.begin(4, "4", 2, False, (D, B, C, D), (False, True, True, True))
    m.step(1)
    assert not m.masks[0] & 4 and m.banks[2][0] == D
    m.abort()
    assert m.accepted == old and m.masks[0] == 3 and all(mask == 7 for mask in m.masks[1:])
    tx = frame(m, 4, 2, old)
    assert (tx.writes, tx.elisions, tx.unchanged_misses) == (1, 3, 1)
    results.append(dict(case="abort_does_not_restore_stale_old_mask_retry_rewrites", status="PASS",
                        retry_writes=tx.writes, retry_elisions=tx.elisions))

    # A fully produced but unauthenticated frame cannot replace the reference.
    m.begin(5, "5", 0, False, (A, D, C, D), (True, False, True, True))
    m.step()
    reject("authentication_failure_no_commit", lambda: m.commit(authenticated=False))
    m.abort()
    assert m.accepted == old and m.reference == 2 and not m.masks[1] & 1
    results.append(dict(case="late_authentication_abort_retains_reference", status="PASS"))

    # Fault injection: forged equality is rejected against actual decoded bytes.
    reject("forged_unchanged_flag_rejected", lambda: m.begin(5, "5", 0, False, (D, B, C, D), (True,) * 4))
    # Post-begin corruption reaches the per-elision physical certificate gate.
    m.begin(5, "5", 1, False, old, (True,) * 4)
    m.banks[1][0] = D
    reject("corrupt_resident_physical_tile_rejected", lambda: m.step(1))
    m.banks[1][0] = A  # repair the deliberately injected test-only oracle fault
    m.abort()
    # Forged residency bit pointing to physically stale contents is rejected.
    m.masks[1] |= 1
    reject("forged_residency_bit_rejected", m.check)
    m.masks[1] &= ~1
    m.check()

    # Pending presentation means reference and front can lease different banks.
    frame(m, 5, 1, old, present=False)
    assert (m.front, m.reference) == (2, 1)
    reject("old_front_lease_rejected", lambda: m.begin(6, "6", 2, False, old, (True,) * 4))
    frame(m, 6, 0, old, present=False)
    assert (m.front, m.reference) == (2, 0)
    m.draining.add(1)
    reject("all_banks_leased_stall", lambda: m.begin(7, "7", 1, False, old, (True,) * 4))
    m.draining.remove(1)
    m.present(hold_old_drain=True)
    assert m.front == 0 and m.draining == {2}
    reject("old_scanout_drain_lease_rejected", lambda: m.begin(7, "7", 2, False, old, (True,) * 4))
    frame(m, 7, 1, old)
    m.draining.clear()
    results.append(dict(case="front_reference_and_scanout_drain_leases", status="PASS"))

    # Even byte-identical keys must write every tile and throw away old bits.
    tx = frame(m, 8, 2, old, key=True)
    assert tx.writes == 4 and tx.elisions == 0 and m.masks == [4] * 4
    m.reset()
    assert m.front == 2 and m.reference is None and not any(m.masks)
    reject("reset_preserves_front_lease", lambda: m.begin(0, "0", 2, True, old, (False,) * 4))
    reject("reset_requires_key", lambda: m.begin(0, "0", 0, False, old, (False,) * 4))
    tx = frame(m, 0, 0, old, key=True)
    assert tx.writes == 4 and m.masks == [1] * 4
    results.append(dict(case="full_write_key_and_reset_key_recovery", status="PASS"))

    # A key aborted after a partial store also invalidates old certificates.
    frame(m, 1, 1, old)
    m.begin(2, "2", 0, True, (D, B, C, D), (False, True, True, True))
    m.step(1)
    m.abort()
    assert not m.masks[0] & 1 and m.accepted == old
    tx = frame(m, 2, 0, old)
    assert tx.unchanged_misses == 1 and tx.elisions == 3
    results.append(dict(case="aborted_key_keeps_old_reference_invalidations", status="PASS"))
    return results
