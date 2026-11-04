"""Native UBSan tests for the bounded FG19 receiver ownership ledger."""
import argparse
import ctypes as C
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
import zlib

HERE = Path(__file__).resolve().parent
FG = struct.Struct('!4sBBHIIQII')


class Frame(C.Structure):
    _fields_ = [('epoch', C.c_uint32), ('frame', C.c_uint32), ('total', C.c_uint32),
                ('body_crc', C.c_uint32), ('nonce', C.c_uint64), ('slot', C.c_uint16),
                ('kind', C.c_uint8)]


class Route(C.Structure):
    _fields_ = [(n, C.c_uint32) for n in
                ('epoch', 'frame', 'total', 'complete_crc', 'body_crc', 'token_header_crc')]
    _fields_ += [('sequence', C.c_uint64)] + [(n, C.c_uint16) for n in
                 ('packet_slot', 'index', 'count', 'payload_bytes')]


class Owner(C.Structure):
    _fields_ = [('occupied', C.c_uint8), ('finished', C.c_uint8),
                ('physically_drained', C.c_uint8), ('grant', Frame),
                ('observed_fragments', C.c_uint64)]


class Ledger(C.Structure):
    _fields_ = [('slots', Owner * 2), ('last_request_sequence', C.c_uint64),
                ('released_sequence', C.c_uint64), ('safe_stop', C.c_uint8),
                ('finish_ack', C.c_uint8)]


def seal(fields):
    body = FG.pack(*fields)
    return body + struct.pack('!I', zlib.crc32(body))


class Tests(unittest.TestCase):
    def parsed_control(self, fields):
        wire = seal(fields)
        out = Frame()
        buf = C.create_string_buffer(wire)
        self.assertEqual(self.lib.gb_parse_fg19(buf, len(wire), 1, C.byref(out)), 0)
        return out

    def request(self, frame, seq, slot, total=1008, crc=0x12345678):
        return self.parsed_control((b'FG19', 1, 1, slot, 1, frame, seq, total, crc))

    def apply(self, ledger, control):
        reply = Frame()
        rc = self.lib.gb_ownership_control(C.byref(ledger), C.byref(control), C.byref(reply))
        return rc, reply

    def test_all_1725_serialized_history_messages_parse_and_bound_retention(self):
        seen = 0
        for profile in self.contract['frame_control_sequences']:
            ledger = Ledger()
            kinds = {e['parsed']['kind'] for e in profile['events']}
            self.lib.gb_ownership_init(C.byref(ledger), int(8 in kinds))
            for event in profile['events']:
                wire = bytes.fromhex(event['wire_hex'])
                self.assertEqual(zlib.crc32(wire[:-4]), struct.unpack('!I', wire[-4:])[0])
                out = Frame()
                buf = C.create_string_buffer(wire)
                self.assertEqual(self.lib.gb_parse_fg19(buf, len(wire), 1, C.byref(out)), 0)
                parsed = event['parsed']
                self.assertEqual((out.kind, out.slot, out.epoch, out.frame, out.nonce,
                                  out.total, out.body_crc),
                                 (parsed['kind'], parsed['slot'], parsed['epoch'], parsed['frame'],
                                  parsed['seq'], parsed['total'], parsed['crc']))
                if event['event'] in ('sender_request', 'sender_cancel', 'sender_finish'):
                    rc, reply = self.apply(ledger, out)
                    self.assertIn(rc, (0, 1, 2))
                    if out.kind == 7 and rc in (0, 2):
                        # No serialized history event proves physical drain.
                        self.assertLessEqual(self.lib.gb_ownership_count(C.byref(ledger)), 2)
                        self.assertNotEqual(reply.kind, 5)
                elif event['event'] == 'receiver_reply':
                    reply = Frame()
                    before = bytes(reply)
                    # GRANT/BUSY/CANCELED/FINISHED/RELEASE are sender-side replies.
                    self.assertEqual(self.lib.gb_ownership_control(
                        C.byref(ledger), C.byref(out), C.byref(reply)), -1)
                    self.assertEqual(bytes(reply), before)
                self.assertLessEqual(self.lib.gb_ownership_count(C.byref(ledger)), 2)
                seen += 1
        self.assertEqual(seen, 1725)

    def test_duplicate_grant_same_slot_cancel_before_data_and_stale_reject(self):
        ledger = Ledger(); self.lib.gb_ownership_init(C.byref(ledger), 1)
        req = self.request(7, 1, 0)
        rc, first = self.apply(ledger, req)
        self.assertEqual((rc, first.kind, first.slot), (0, 3, 0))
        rc, again = self.apply(ledger, req)
        self.assertEqual((rc, again.kind, again.slot), (0, 3, 0))
        other_slot = self.request(8, 3, 0)
        rc, busy = self.apply(ledger, other_slot)
        self.assertEqual((rc, busy.kind, busy.slot), (1, 4, 0xffff))
        stale_new_frame = self.request(9, 2, 1)
        rc, busy = self.apply(ledger, stale_new_frame)
        self.assertEqual((rc, busy.kind, self.lib.gb_ownership_count(C.byref(ledger))),
                         (1, 4, 1))
        wrong = Frame.from_buffer_copy(req); wrong.body_crc ^= 1; wrong.kind = 2
        rc, busy = self.apply(ledger, wrong)
        self.assertEqual((rc, busy.kind, self.lib.gb_ownership_count(C.byref(ledger))),
                         (1, 4, 1))
        cancel = Frame.from_buffer_copy(req); cancel.kind = 2
        rc, canceled = self.apply(ledger, cancel)
        self.assertEqual((rc, canceled.kind, self.lib.gb_ownership_count(C.byref(ledger))),
                         (0, 6, 0))
        self.assertEqual(self.apply(ledger, req)[0], 1)  # released sequence cannot replay

    def test_observed_route_requires_finish_and_drain_lost_finish_has_no_recovery(self):
        packet = bytes.fromhex(self.contract['packet_example']['wrapped_first_gf03_hex'])
        route = Route(); buf = C.create_string_buffer(packet)
        self.assertEqual(self.lib.gb_parse_data(buf, len(packet), 1, C.byref(route)), 0)
        ledger = Ledger(); self.lib.gb_ownership_init(C.byref(ledger), 1)
        req = self.request(route.frame, 1, 0, route.total, route.body_crc)
        self.assertEqual(self.apply(ledger, req)[0], 0)
        self.assertEqual(self.lib.gb_ownership_observe_data(C.byref(ledger), C.byref(route)), 1)
        self.assertEqual(self.lib.gb_ownership_observe_data(C.byref(ledger), C.byref(route)), 1)
        self.assertEqual(ledger.slots[0].observed_fragments, 1)
        cancel = Frame.from_buffer_copy(req); cancel.kind = 2
        self.assertEqual(self.apply(ledger, cancel)[0], 1)
        finish = Frame.from_buffer_copy(req); finish.kind = 7
        rc, finished = self.apply(ledger, finish)
        self.assertEqual((rc, finished.kind, self.lib.gb_ownership_count(C.byref(ledger))),
                         (0, 8, 1))
        drain_id = Frame.from_buffer_copy(req); drain_id.kind = 3
        wrong = Frame.from_buffer_copy(drain_id); wrong.body_crc ^= 1
        self.assertEqual(self.lib.gb_ownership_physical_drain(
            C.byref(ledger), C.byref(wrong)), 0)
        self.assertEqual(self.lib.gb_ownership_count(C.byref(ledger)), 1)
        release = Frame()
        self.assertEqual(self.lib.gb_ownership_take_release(
            C.byref(ledger), C.byref(finished), C.byref(release)), 0)
        self.assertEqual(self.lib.gb_ownership_physical_drain(
            C.byref(ledger), C.byref(drain_id)), 1)
        self.assertEqual(self.lib.gb_ownership_observe_data(
            C.byref(ledger), C.byref(route)), 0)
        self.assertEqual(ledger.slots[0].observed_fragments, 1)
        self.assertEqual(self.lib.gb_ownership_take_release(
            C.byref(ledger), C.byref(finished), C.byref(release)), 1)
        self.assertEqual((release.kind, release.slot, self.lib.gb_ownership_count(C.byref(ledger))),
                         (5, 0, 0))
        rc, busy = self.apply(ledger, req)
        self.assertEqual((rc, busy.kind, self.lib.gb_ownership_count(C.byref(ledger))), (1, 4, 0))

    def test_drain_before_finish_is_remembered_but_not_freed(self):
        ledger = Ledger(); self.lib.gb_ownership_init(C.byref(ledger), 0)
        req = self.request(10, 1, 1)
        self.assertEqual(self.apply(ledger, req)[0], 0)
        drain_id = Frame.from_buffer_copy(req); drain_id.kind = 3
        self.assertEqual(self.lib.gb_ownership_physical_drain(
            C.byref(ledger), C.byref(drain_id)), 1)
        release = Frame(); before = bytes(release)
        owner_id = Frame.from_buffer_copy(req); owner_id.kind = 3
        self.assertEqual(self.lib.gb_ownership_take_release(
            C.byref(ledger), C.byref(owner_id), C.byref(release)), 0)
        self.assertEqual(bytes(release), before)
        finish = Frame.from_buffer_copy(req); finish.kind = 7
        rc, release = self.apply(ledger, finish)
        self.assertEqual((rc, self.lib.gb_ownership_count(C.byref(ledger))), (2, 1))
        self.assertEqual(self.lib.gb_ownership_take_release(
            C.byref(ledger), C.byref(owner_id), C.byref(release)), 1)
        self.assertEqual((release.kind, self.lib.gb_ownership_count(C.byref(ledger))), (5, 0))

    def test_unknown_outcome_safe_stop_retains_both_owners(self):
        ledger = Ledger(); self.lib.gb_ownership_init(C.byref(ledger), 1)
        self.assertEqual(self.apply(ledger, self.request(11, 1, 0))[0], 0)
        self.assertEqual(self.apply(ledger, self.request(12, 2, 1))[0], 0)
        self.lib.gb_ownership_safe_stop(C.byref(ledger))
        self.assertEqual(self.lib.gb_ownership_count(C.byref(ledger)), 2)
        out = Frame(); before = bytes(out)
        blocked = self.request(13, 3, 0)
        rc = self.lib.gb_ownership_control(C.byref(ledger), C.byref(blocked), C.byref(out))
        self.assertEqual((rc, self.lib.gb_ownership_count(C.byref(ledger))), (3, 2))
        self.assertEqual(bytes(out), before)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--result', type=Path, required=True)
    args = p.parse_args()
    contract_path = args.source / 'hardware/gamebub-v20/wire-contract.json'
    Tests.contract = json.loads(contract_path.read_text())
    with tempfile.TemporaryDirectory(prefix='ar03-ownership-') as tmp:
        library = Path(tmp) / 'ownership.so'
        command = ['gcc', '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror', '-shared', '-fPIC',
                   '-fsanitize=undefined', '-fno-sanitize-recover=all', str(HERE / 'gb_gateway.c'),
                   str(HERE / 'gb_ownership.c'), '-o', str(library)]
        subprocess.run(command, check=True)
        Tests.lib = C.CDLL(str(library))
        Tests.lib.gb_parse_fg19.argtypes = [C.c_void_p, C.c_size_t, C.c_uint32, C.c_void_p]
        Tests.lib.gb_parse_fg19.restype = C.c_int
        Tests.lib.gb_parse_data.argtypes = [C.c_void_p, C.c_size_t, C.c_uint32, C.c_void_p]
        Tests.lib.gb_parse_data.restype = C.c_int
        Tests.lib.gb_ownership_init.argtypes = [C.c_void_p, C.c_int]
        Tests.lib.gb_ownership_control.argtypes = [C.c_void_p, C.c_void_p, C.c_void_p]
        Tests.lib.gb_ownership_control.restype = C.c_int
        Tests.lib.gb_ownership_observe_data.argtypes = [C.c_void_p, C.c_void_p]
        Tests.lib.gb_ownership_observe_data.restype = C.c_int
        Tests.lib.gb_ownership_physical_drain.argtypes = [C.c_void_p, C.c_void_p]
        Tests.lib.gb_ownership_physical_drain.restype = C.c_int
        Tests.lib.gb_ownership_take_release.argtypes = [C.c_void_p, C.c_void_p, C.c_void_p]
        Tests.lib.gb_ownership_take_release.restype = C.c_int
        Tests.lib.gb_ownership_safe_stop.argtypes = [C.c_void_p]
        Tests.lib.gb_ownership_count.argtypes = [C.c_void_p]
        Tests.lib.gb_ownership_count.restype = C.c_uint
        result = unittest.TextTestRunner(verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
        row = dict(passed=result.wasSuccessful(), tests=result.testsRun, failures=len(result.failures),
                   errors=len(result.errors), serialized_controls_exercised=1725,
                   wire_contract_sha256=hashlib.sha256(contract_path.read_bytes()).hexdigest(),
                   source_sha256={name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
                                  for name in ('gb_gateway.c', 'gb_gateway.h',
                                               'gb_ownership.c', 'gb_ownership.h', 'test_ownership.py')},
                   compile=command,
                   scope='Native host ledger only; explicit physical-drain calls in targeted tests; no packet permits/FIFO admission/network/hardware')
        args.result.parent.mkdir(parents=True, exist_ok=True)
        args.result.write_text(json.dumps(row, indent=2) + '\n')
        raise SystemExit(0 if result.wasSuccessful() else 1)


if __name__ == '__main__':
    main()
