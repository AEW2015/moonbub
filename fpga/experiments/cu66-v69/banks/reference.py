"""Small independent sequential oracle for CU66 three-bank ownership."""
from dataclasses import dataclass, asdict

NO_ID = 0xFFFFFFFF


@dataclass
class Controller:
    active: bool = False
    aborting: bool = False
    write_bank: int = 0
    read_bank_valid: bool = False
    read_bank: int = 0
    ref_bank: int = 0
    ref_id: int = NO_ID
    ref_valid: bool = False
    front_bank: int = 0
    front_id: int = NO_ID
    front_valid: bool = False
    pending_bank: int = 0
    pending_id: int = NO_ID
    pending_valid: bool = False
    candidate_id: int = NO_ID
    accepted_count: int = 0
    presented_count: int = 0

    def _free_bank(self):
        occupied = set()
        for valid, bank in ((self.ref_valid, self.ref_bank),
                            (self.front_valid, self.front_bank),
                            (self.pending_valid, self.pending_bank),
                            (self.active, self.write_bank)):
            if valid:
                occupied.add(bank)
        return next((bank for bank in range(3) if bank not in occupied), None)

    def _levels(self, *, rst=False, abort_i=False, commit_ok=False):
        safe_swap = self.pending_valid and not rst
        safe_swap = bool(safe_swap and getattr(self, '_vblank', False)
                         and getattr(self, '_scanout_drained', False))
        return {
            'begin_ready': bool(not rst and not abort_i and not self.active
                                and self._free_bank() is not None),
            'commit_ready': bool(not rst and not abort_i and self.active
                                 and not self.aborting
                                 and (not commit_ok or not self.pending_valid or safe_swap)),
        }

    def _snapshot(self, pulses):
        values = {
            'active': self.active,
            'aborting': self.aborting,
            'write_bank': self.write_bank,
            'read_bank_valid': self.read_bank_valid,
            'read_bank': self.read_bank,
            'ref_valid': self.ref_valid,
            'ref_bank': self.ref_bank,
            'ref_id': self.ref_id,
            'front_valid': self.front_valid,
            'front_bank': self.front_bank,
            'front_id': self.front_id,
            'pending_valid': self.pending_valid,
            'pending_bank': self.pending_bank,
            'pending_id': self.pending_id,
            'accepted_count': self.accepted_count,
            'presented_count': self.presented_count,
        }
        values.update(pulses)
        return values

    def step(self, inputs):
        """Return (pre-edge ready signals, post-edge observable state/pulses)."""
        rst = bool(inputs.get('rst', 0))
        abort_i = bool(inputs.get('abort_i', 0))
        commit_ok = bool(inputs.get('commit_ok', 0))
        self._vblank = bool(inputs.get('vblank', 0))
        self._scanout_drained = bool(inputs.get('scanout_drained', 0))
        free_bank_pre = self._free_bank()
        pre = self._levels(rst=rst, abort_i=abort_i, commit_ok=commit_ok)
        pulses = dict(begin_accepted=False, frame_committed=False,
                      frame_presented=False, aborted=False, error=False,
                      error_code=0)

        if rst:
            self.active = self.aborting = False
            self.write_bank = self.read_bank = self.ref_bank = 0
            self.read_bank_valid = self.ref_valid = False
            self.ref_id = NO_ID
            self.front_valid = self.pending_valid = False
            self.front_bank = self.pending_bank = 0
            self.front_id = self.pending_id = NO_ID
            self.candidate_id = NO_ID
            self.accepted_count = self.presented_count = 0
            return pre, self._snapshot(pulses)

        safe_swap = bool(self.pending_valid and inputs.get('vblank', 0)
                         and inputs.get('scanout_drained', 0))
        if safe_swap:
            self.front_valid = True
            self.front_bank = self.pending_bank
            self.front_id = self.pending_id
            self.pending_valid = False
            self.pending_id = NO_ID
            self.presented_count += 1
            pulses['frame_presented'] = True

        if self.active and self.aborting:
            if inputs.get('drain_done', 0):
                self.active = False
                self.aborting = False
                self.read_bank_valid = False
                self.candidate_id = NO_ID
                pulses['aborted'] = True
        elif self.active and abort_i:
            self.aborting = True
        elif inputs.get('commit_valid', 0) and pre['commit_ready']:
            if not commit_ok:
                self.aborting = True
                pulses['error'] = True
                pulses['error_code'] = 4
            else:
                self.ref_valid = True
                self.ref_bank = self.write_bank
                self.ref_id = self.candidate_id
                self.pending_valid = True
                self.pending_bank = self.write_bank
                self.pending_id = self.candidate_id
                self.active = False
                self.read_bank_valid = False
                self.candidate_id = NO_ID
                self.accepted_count += 1
                pulses['frame_committed'] = True
        elif inputs.get('begin_valid', 0) and pre['begin_ready']:
            frame_id = inputs.get('begin_id', NO_ID) & NO_ID
            is_key = bool(inputs.get('begin_key', 0))
            reference_id = inputs.get('begin_reference_id', NO_ID) & NO_ID
            if frame_id == NO_ID or (self.ref_valid and frame_id <= self.ref_id) or (
                    is_key and reference_id != NO_ID):
                pulses['error'] = True
                pulses['error_code'] = 1
            elif not is_key and (not self.ref_valid or reference_id != self.ref_id):
                pulses['error'] = True
                pulses['error_code'] = 2
            else:
                # Bank selection is combinational from pre-edge leases. A
                # same-cycle safe swap cannot make its released bank available
                # to this begin handshake until the following cycle.
                free_bank = free_bank_pre
                assert free_bank is not None
                self.active = True
                self.aborting = False
                self.write_bank = free_bank
                self.candidate_id = frame_id
                self.read_bank_valid = not is_key
                self.read_bank = self.ref_bank
                pulses['begin_accepted'] = True

        self._assert_invariants()
        return pre, self._snapshot(pulses)

    def _assert_invariants(self):
        if self.active:
            assert self.candidate_id != NO_ID
            assert self.write_bank in range(3)
        else:
            assert self.candidate_id == NO_ID
        if self.aborting:
            assert self.active
        if self.ref_valid:
            assert self.ref_id != NO_ID and self.ref_bank in range(3)
        else:
            assert self.ref_id == NO_ID
        if self.front_valid:
            assert self.front_id != NO_ID and self.front_bank in range(3)
        else:
            assert self.front_id == NO_ID
        if self.pending_valid:
            assert self.pending_id != NO_ID and self.pending_bank in range(3)
        else:
            assert self.pending_id == NO_ID
        # A candidate is private. Committed roles may share a bank only where
        # the state machine deliberately holds both reference and display lease.
        if self.active:
            assert self.write_bank not in {
                b for valid, b in ((self.ref_valid, self.ref_bank),
                                   (self.front_valid, self.front_bank),
                                   (self.pending_valid, self.pending_bank)) if valid}
        if self.front_valid and self.pending_valid:
            assert self.front_bank != self.pending_bank
