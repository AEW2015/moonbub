"""Explicit count-bound CU66 v3 finite sequence uploader. No live encoding or FPS claim."""
import argparse
import hashlib
import json
from pathlib import Path
import secrets
import socket
import struct
import time
import dyn1_sequence_core as core

PROFILE = 'dy71-sequence-v3'
MAX_FRAMES = 12000


class Sequence:
    """Keep only manifest metadata; read/validate one bounded packet at a time."""
    def __init__(self, manifest_path, profile, count):
        if profile != PROFILE:
            raise ValueError('requires explicit dy71-sequence-v3 profile')
        if type(count) is not int or not 1 <= count <= MAX_FRAMES:
            raise ValueError('sequence count must be1..12000')
        self.path = Path(manifest_path).resolve()
        self.manifest = json.loads(self.path.read_text())
        rows = self.manifest['frames']
        if self.manifest.get('schema') != 'dy71-sequence-manifest-v3' or self.manifest.get('profile') != PROFILE or self.manifest.get('status') != 'PASS_FRESH_SOFTWARE_REFERENCE_AND_FAULTS':
            raise ValueError('requires qualified v3 sequence manifest')
        if self.manifest.get('qualified_frame_count') != len(rows) or self.manifest.get('dimensions') != [720, 480]:
            raise ValueError('manifest count/canvas binding')
        if not count <= len(rows) <= MAX_FRAMES:
            raise ValueError('requested count exceeds qualified sequence')
        self.rows = rows[:count]
        prior = None
        for i, row in enumerate(self.rows):
            fid, rid, key = row['id'], row['reference_id'], row['key']
            if type(fid) is not int or not 0 <= fid < 0xffffffff or type(rid) is not int or type(key) is not bool:
                raise ValueError('frame ID outside supported range')
            if i == 0:
                if not key or rid != 0xffffffff:
                    raise ValueError('finite sequence must begin with independent KEY')
            elif key or fid <= prior or rid != prior:
                raise ValueError('requires strictly increasing exact prior-frame P chain')
            prior = fid
            item = row['files']['cu66']
            path = (self.path.parent / item['path']).resolve()
            if path.parent != self.path.parent:
                raise ValueError('packet must be adjacent to manifest')
            if not 80 <= item['bytes'] <= 49152:
                raise ValueError('manifest packet cap')

    def __len__(self):
        return len(self.rows)

    def read(self, index):
        row = self.rows[index]
        item = row['files']['cu66']
        body = (self.path.parent / item['path']).read_bytes()
        core.validate(body)
        if len(body) != item['bytes'] or hashlib.sha256(body).hexdigest() != item['sha256']:
            raise ValueError('packet manifest length/hash')
        frame, reference = struct.unpack_from('<II', body, 8)
        if (frame, reference, bool(body[5] & 1)) != (row['id'], row['reference_id'], row['key']):
            raise ValueError('packet manifest identity')
        if body[5] not in (2, 3) or struct.unpack_from('<H', body, 6)[0] != 25:
            raise ValueError('explicit CU66 epoch/flags')
        if body[20:36].hex() != '16c998527276c7c5249e96c75931494b':
            raise ValueError('explicit CU66 profile')
        return body


def upload(sock, receiver, sequence, session, log, initial_wait_seconds):
    if not 1 <= len(sequence) <= MAX_FRAMES or session == 0:
        raise ValueError('finite sequence and nonzero session required')
    results = []
    for index in range(len(sequence)):
        result = core.send_frame(sock, receiver, sequence.read(index), session, log,
                                 len(sequence), initial_wait_seconds if index == 0 else 10)
        if result['status'] != 'presented':
            raise RuntimeError('must observe actual presentation before next dependent frame')
        results.append(result)
    return results


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--profile', required=True, choices=[PROFILE])
    p.add_argument('--count', required=True, type=int)
    p.add_argument('--manifest', type=Path, default=Path(__file__).with_name('manifest.json'))
    p.add_argument('--receiver', required=True)
    p.add_argument('--bind', required=True)
    p.add_argument('--port', type=int, default=5535)
    p.add_argument('--initial-wait-seconds', type=float, default=600)
    p.add_argument('--log', type=Path, required=True)
    a = p.parse_args()
    if not 1 <= a.initial_wait_seconds <= 1800:
        p.error('initial wait must be1..1800seconds')
    if a.port != 5535:
        p.error('finite v3 profile is explicitly port5535')
    sequence = Sequence(a.manifest, a.profile, a.count)
    # Preflight all selected packets before opening a socket or reserving a log.
    for i in range(len(sequence)):
        sequence.read(i)
    session = secrets.randbits(64) or 1
    receiver = (socket.gethostbyname(a.receiver), a.port)
    with a.log.open('x') as log, socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind((a.bind, 0))
        sock.settimeout(0.1)
        row = {'event': 'session', 'profile': PROFILE, 'wire': 'DYN1/DYA1 v3 count-bound; explicit selection',
               'sequence_count': len(sequence), 'session': session, 'source': sock.getsockname(),
               'destination': receiver, 'manifest_sha256': hashlib.sha256(a.manifest.read_bytes()).hexdigest(),
               'source_kind': sequence.manifest['source_kind'], 'initial_wait_seconds': a.initial_wait_seconds,
               'started_unix_us': time.time_ns() // 1000}
        log.write(json.dumps(row) + '\n')
        log.flush()
        print(json.dumps(row), flush=True)
        try:
            results = upload(sock, receiver, sequence, session, log, a.initial_wait_seconds)
        except Exception as exc:
            failure = {'event': 'failed', 'error': str(exc), 'whole_run_retry': False,
                       'receiver_state': 'unknown_or_retained; do not auto-reset'}
            log.write(json.dumps(failure) + '\n')
            log.flush()
            raise
        result = {'event': 'complete', 'profile': PROFILE, 'presented': len(results),
                  'sequence_count': len(sequence), 'whole_run_retry': False}
        log.write(json.dumps(result) + '\n')
        log.flush()
        print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
