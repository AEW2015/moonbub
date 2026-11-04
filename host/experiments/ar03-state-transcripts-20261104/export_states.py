"""Export explicit lab receiver-state transcripts against pinned Python and C.

Drain is a supplied model event, never inferred from a packet log or time.
This is not a whole network/DMA/publication proof or live recovery protocol.
"""
import argparse
import ctypes as C
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import zlib

HERE = Path(__file__).resolve().parent
NATIVE = HERE.parent / 'ar03-gateway-contract-20261104'
PIN = '27a4dde6a7e2ea4fab09d892551ef542f05c8965'
FMT = struct.Struct('!4sBBHIIQII')
GF = struct.Struct('!4sBIIIHHHII')


class Frame(C.Structure):
    _fields_ = [(n, C.c_uint32) for n in ('epoch', 'frame', 'total', 'body_crc')] + [
        ('nonce', C.c_uint64), ('slot', C.c_uint16), ('kind', C.c_uint8)]


class Route(C.Structure):
    _fields_ = [(n, C.c_uint32) for n in ('epoch', 'frame', 'total', 'complete_crc', 'body_crc', 'token_header_crc')] + [
        ('sequence', C.c_uint64)] + [(n, C.c_uint16) for n in ('packet_slot', 'index', 'count', 'payload_bytes')]


class Owner(C.Structure):
    _fields_ = [(n, C.c_uint8) for n in ('occupied', 'finished', 'physically_drained', 'finish_reply_issued')] + [
        ('grant', Frame), ('observed_fragments', C.c_uint64)]


class Ledger(C.Structure):
    _fields_ = [('slots', Owner * 2), ('last_request_sequence', C.c_uint64),
                ('released_sequence', C.c_uint64), ('safe_stop', C.c_uint8), ('finish_ack', C.c_uint8)]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def source_git(source, *args):
    # Windows worktree metadata contains Windows absolute paths. GNU git inside
    # WSL cannot interpret those pointers; use the owning Git installation.
    pointer = source / '.git'
    if sys.platform == 'linux' and pointer.is_file() and ':/' in pointer.read_text():
        git = shutil.which('git.exe') or '/mnt/c/Program Files/Git/cmd/git.exe'
        path = subprocess.check_output(['wslpath', '-w', str(source)], text=True).strip()
        return subprocess.check_output([git, '-C', path, *args])
    return subprocess.check_output(['git', '-C', str(source), *args])


def load(path):
    spec = importlib.util.spec_from_file_location('state_trace_reference', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def identity(x):
    return tuple(x[k] for k in ('epoch', 'frame', 'seq', 'total', 'crc', 'slot'))


def from_c(x):
    return dict(epoch=x.epoch, frame=x.frame, seq=x.nonce, total=x.total,
                crc=x.body_crc, slot=x.slot, kind=x.kind)


def as_c(x):
    return Frame(epoch=x['epoch'], frame=x['frame'], nonce=x['seq'], total=x['total'],
                 body_crc=x['crc'], slot=x['slot'], kind=x['kind'])


def wire(x):
    data = FMT.pack(b'FG19', 1, x['kind'], x['slot'], x['epoch'], x['frame'],
                    x['seq'], x['total'], x['crc'])
    return data + struct.pack('!I', zlib.crc32(data))


def req(frame=0, seq=1, slot=0, total=1008, crc=0x12345678, **extra):
    return dict(epoch=1, frame=frame, seq=seq, slot=slot, total=total, crc=crc, kind=1, **extra)


def action(op, x=None, **extra):
    return dict(op=op, **({'identity': x} if x is not None else {}), **extra)


def cases(example):
    a = req(); b = req(frame=1, seq=2, slot=1)
    real = GF.unpack_from(bytes.fromhex(example), 16)
    r = req(frame=real[3], total=real[4], crc=real[9])
    return [
        dict(name='normal-drain-and-stale-completion', events=[
            action('control', r), action('data', wire_hex=example),
            action('control', dict(r, kind=2)), action('control', dict(r, kind=7)),
            action('poll'), action('drain', r), action('poll'),
            action('control', req(frame=r['frame'] + 1, seq=2)),
            action('drain', r), action('control', dict(r, kind=7)), action('poll')]),
        dict(name='drain-before-finish-still-needs-finished', events=[
            action('control', a), action('drain', a), action('poll'),
            action('control', dict(a, kind=7)), action('poll')]),
        dict(name='two-owners-busy-consumes-request-serial', events=[
            action('control', a), action('control', b),
            action('control', req(frame=2, seq=3, slot=0)),
            action('control', dict(b, kind=2)),
            action('control', req(frame=3, seq=2, slot=1)),
            action('control', req(frame=3, seq=4, slot=1)),
            action('control', dict(a, kind=7)), action('drain', a), action('poll')]),
        dict(name='duplicate-request-same-slot', events=[
            action('control', a), action('control', a), action('control', dict(a, kind=2)),
            action('control', a)]),
        dict(name='duplicate-request-different-slot', expected_policy_difference=True, events=[
            action('control', a), action('control', dict(a, slot=1)), action('poll')]),
        dict(name='wrong-identity-cannot-release', events=[
            action('control', a), action('control', dict(a, slot=1, kind=7)),
            action('control', dict(a, crc=2, kind=2)),
            action('drain', dict(a, seq=2)), action('poll'), action('control', dict(a, kind=2))]),
        dict(name='reply-kind-is-not-a-request', events=[
            action('control', a), action('control', dict(a, kind=5)), action('poll')]),
        dict(name='unknown-grant-outcome-retains-owner', events=[
            action('control', a, deliver_reply=False), action('safe_stop'),
            action('control', dict(a, kind=2)), action('poll')]),
        dict(name='nonce-exhaustion-does-not-invent-new-epoch', events=[
            action('control', req(seq=2**64 - 1)),
            action('control', dict(req(seq=2**64 - 1), kind=2)),
            action('control', req(frame=1, seq=1, slot=1))]),
        dict(name='wrong-epoch-rejected-before-state-change', events=[
            action('control', a), action('control', dict(a, epoch=2, kind=7)), action('poll')]),
    ]


class Runner:
    def __init__(self, ref, lib):
        self.module = ref
        self.lib = lib
        self.now = 0
        self.replies = []
        self.drained = set()
        cfg = SimpleNamespace(frame_finish_ack=True, lose_first_frame_grant=False,
                              lose_first_frame_release=False, duplicate_frame_release=False,
                              frame_control_timeout_ms=200)
        self.ref = ref.Protocol(cfg, lambda *args: None,
                                lambda stage, fid, fn: (fn(), dict(done_ms=self.now)))
        self.ref.engine = SimpleNamespace(reverse=self.reverse, reverse_free=0, frames={})
        self.native = Ledger()
        lib.gb_ownership_init(C.byref(self.native), 1)

    def reverse(self, data, *args, **kwargs):
        self.replies.append(data.hex())
        # Explicit synchronous model reverse-worker completion; no radio/host ACK.
        self.ref.feedback_owned -= 1

    def reference_state(self):
        owners = []
        for x in self.ref.receiver:
            owners.append(None if x is None else dict(
                identity=list(identity(x)), finished=bool(x['finished']), seen=sorted(x['seen'])))
        return dict(owners=owners, last_request=self.ref.last_request_seq,
                    released=self.ref.released_seq, safe_stop=self.ref.stopped)

    def native_state(self):
        owners = []
        for x in self.native.slots:
            owners.append(None if not x.occupied else dict(
                identity=list(identity(from_c(x.grant))), finished=bool(x.finished),
                seen=[i for i in range(49) if x.observed_fragments & (1 << i)]))
        return dict(owners=owners, last_request=self.native.last_request_sequence,
                    released=self.native.released_sequence, safe_stop=bool(self.native.safe_stop))

    def emit_c(self, frame):
        out = C.create_string_buffer(36)
        assert self.lib.gb_write_fg19(C.byref(frame), out, 36) == 36
        return out.raw.hex()

    def step(self, event):
        self.now += 1
        self.replies = []
        native_replies = []
        outcome = 'applied'
        op = event['op']
        if op == 'safe_stop':
            self.ref.stop('explicit model unknown outcome', self.now)
            self.lib.gb_ownership_safe_stop(C.byref(self.native))
        elif self.ref.stopped:
            # The enclosing endpoint dispatcher stops new admission. The frozen
            # receive() helper alone does not provide this dispatcher gate.
            outcome = 'safe_stop_retained'
            if op == 'control':
                out = Frame(); x = as_c(event['identity'])
                assert self.lib.gb_ownership_control(C.byref(self.native), C.byref(x), C.byref(out)) == 3
        elif op == 'control':
            packet = wire(event['identity'])
            out = Frame(); parsed = Frame(); buf = C.create_string_buffer(packet)
            c_parse = self.lib.gb_parse_fg19(buf, len(packet), 1, C.byref(parsed))
            try:
                fields = self.module.parse(packet)
            except ValueError:
                assert c_parse == -1
                outcome = 'invalid_wire'
            else:
                assert c_parse == 0
                try:
                    self.ref.receive(fields, self.now)
                except ValueError:
                    outcome = 'invalid_direction'
                rc = self.lib.gb_ownership_control(C.byref(self.native), C.byref(parsed), C.byref(out))
                if outcome == 'invalid_direction':
                    assert rc == -1
                elif rc in (0, 1):
                    native_replies.append(self.emit_c(out))
                else:
                    raise AssertionError(('unexpected C control result', rc))
        elif op == 'data':
            packet = bytes.fromhex(event['wire_hex']); fields = GF.unpack_from(packet, 16)
            self.ref.consumed(fields)
            route = Route(); buf = C.create_string_buffer(packet)
            assert self.lib.gb_parse_data(buf, len(packet), 1, C.byref(route)) == 0
            assert self.lib.gb_ownership_observe_data(C.byref(self.native), C.byref(route)) == 1
        elif op == 'drain':
            x = dict(event['identity'], kind=3)
            valid = any(r is not None and identity(r) == identity(x) for r in self.ref.receiver)
            if valid:
                self.drained.add(identity(x))
            c = as_c(x)
            assert self.lib.gb_ownership_physical_drain(C.byref(self.native), C.byref(c)) == int(valid)
        elif op == 'poll':
            ready = {r['frame'] for r in self.ref.receiver
                     if r is not None and identity(r) in self.drained}
            self.ref.release_ready(self.now, lambda frame: frame in ready)
            for owner in list(self.native.slots):
                if owner.occupied:
                    x = Frame.from_buffer_copy(owner.grant); out = Frame()
                    rc = self.lib.gb_ownership_take_release(C.byref(self.native), C.byref(x), C.byref(out))
                    assert rc in (0, 1)
                    if rc == 1:
                        native_replies.append(self.emit_c(out))
        else:
            raise ValueError(op)
        r, c = self.reference_state(), self.native_state()
        assert r == c, ('owner state mismatch', event, r, c)
        assert sum(x is not None for x in r['owners']) <= 2
        return dict(event=event, model_step=self.now, outcome=outcome,
                    expected_receiver_state=r, expected_reply_hex=self.replies,
                    native_c_reply_hex=native_replies,
                    reply_matches=self.replies == native_replies)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    assert source_git(args.source, 'rev-parse', 'HEAD').decode().strip() == PIN
    ref_path = args.source / 'experiments/python-game-frame-grant-study/frame_credit.py'
    assert ref_path.read_bytes() == source_git(args.source, 'show',
                                              PIN + ':experiments/python-game-frame-grant-study/frame_credit.py')
    ref = load(ref_path)
    contract = json.loads((args.source / 'hardware/gamebub-v20/wire-contract.json').read_text())
    with tempfile.TemporaryDirectory(prefix='ar03-states-') as tmp:
        tmp = Path(tmp)
        glue = tmp / 'sizes.c'
        glue.write_text('#include "gb_ownership.h"\nsize_t ledger_size(void){return sizeof(gb_ownership);}\n')
        library = tmp / 'owners.so'
        command = ['gcc', '-std=c11', '-Wall', '-Wextra', '-Werror', '-O2', '-fPIC', '-shared',
                   '-fsanitize=undefined', '-fno-sanitize-recover=all', '-I', str(NATIVE),
                   str(NATIVE / 'gb_gateway.c'), str(NATIVE / 'gb_ownership.c'), str(glue), '-o', str(library)]
        subprocess.run(command, check=True)
        lib = C.CDLL(str(library)); lib.ledger_size.restype = C.c_size_t
        assert lib.ledger_size() == C.sizeof(Ledger)
        lib.gb_ownership_init.argtypes = [C.c_void_p, C.c_int]
        lib.gb_ownership_control.argtypes = [C.c_void_p] * 3
        lib.gb_parse_fg19.argtypes = [C.c_void_p, C.c_size_t, C.c_uint32, C.c_void_p]
        lib.gb_parse_data.argtypes = [C.c_void_p, C.c_size_t, C.c_uint32, C.c_void_p]
        lib.gb_write_fg19.argtypes = [C.c_void_p, C.c_void_p, C.c_size_t]
        lib.gb_ownership_observe_data.argtypes = [C.c_void_p] * 2
        lib.gb_ownership_physical_drain.argtypes = [C.c_void_p] * 2
        lib.gb_ownership_take_release.argtypes = [C.c_void_p] * 3
        lib.gb_ownership_safe_stop.argtypes = [C.c_void_p]
        output = []
        for case in cases(contract['packet_example']['wrapped_first_gf03_hex']):
            runner = Runner(ref, lib)
            rows = [runner.step(e) for e in case['events']]
            differences = [i for i, row in enumerate(rows) if not row['reply_matches']]
            expected = [1] if case.get('expected_policy_difference') else []
            assert differences == expected, (case['name'], differences, expected)
            output.append(dict(name=case['name'], steps=rows,
                               policy_differences=differences,
                               expected_final_receiver_state=runner.reference_state()))
    args.output.mkdir(parents=True, exist_ok=True)
    trace = args.output / 'receiver-state-transcripts.json'
    trace.write_text(json.dumps(dict(schema='ar03-receiver-state-lab-v1', source_commit=PIN,
        scope='Scripted model drain/reverse-worker events, not radio or physical DMA evidence', cases=output), indent=2) + '\n')
    sources = [ref_path, NATIVE / 'gb_gateway.c', NATIVE / 'gb_gateway.h', NATIVE / 'gb_ownership.c', NATIVE / 'gb_ownership.h', Path(__file__)]
    result = dict(cases=len(output), steps=sum(len(c['steps']) for c in output),
                  receiver_states_match=True, known_reply_policy_differences=1,
                  difference='Duplicate REQUEST with changed slot: frozen Python GRANT original slot; older C helper BUSY.',
                  compiler=subprocess.check_output(['gcc', '--version'], text=True).splitlines()[0],
                  transcript_sha256=digest(trace.read_bytes()),
                  sources={str(f): digest(f.read_bytes()) for f in sources},
                  exclusions=['live negotiation/reset', 'packet permit/FIFO ownership', 'real DMA/read drain',
                              'sender reference publication', 'full 1725-history expected-state replay', 'hardware performance'])
    (args.output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
