"""Pure fake-transport checks. No socket is created or datagram transmitted."""
import hashlib
import io
import json
from pathlib import Path
import struct
import unittest
from unittest.mock import patch
import zlib
import sequence_sender as sender

HERE = Path(__file__).resolve().parent
PEER = ('192.168.0.157', 5535)


class Fake:
    def __init__(self, fail_frame=None, wrong_count=False):
        self.reply = None
        self.fail_frame = fail_frame
        self.wrong_count = wrong_count
        self.sent = []
        self.receives = 0

    def sendto(self, body, peer):
        assert peer == PEER
        h = list(sender.core.HEADER.unpack(body[:48]))
        assert h[:4] == [b'DYN1', 3, 0, 48]
        assert 1 <= h[12] <= 12000
        assert zlib.crc32(body[:-4]) == struct.unpack_from('<I', body, len(body)-4)[0]
        self.sent.append((h[5], h[8], h[12]))
        h[0] = b'DYA1'
        h[2] = 3 if h[5] == self.fail_frame else (2 if h[8]+h[11] == h[7] else 0)
        h[8] += h[11]
        h[11] = 0
        if self.wrong_count:
            h[12] += 1
        wire = sender.core.HEADER.pack(*h)
        self.reply = wire + struct.pack('<I', zlib.crc32(wire))
        return len(body)

    def recvfrom(self, count):
        self.receives += 1
        return self.reply, PEER


class Clock:
    def __init__(self):
        self.value = 0

    def __call__(self):
        self.value += 0.01
        return self.value


class Tests(unittest.TestCase):
    def sequence(self, count=12):
        return sender.Sequence(HERE/'manifest.json', sender.PROFILE, count)

    def test_twelve_actual_frames_and_count_identity(self):
        seq = self.sequence()
        fake = Fake()
        log = io.StringIO()
        results = sender.upload(fake, PEER, seq, 7, log, 1)
        self.assertEqual([r['frame'] for r in results], list(range(12)))
        self.assertTrue(all(r['sequence_count'] == 12 for r in results))
        self.assertEqual(len(fake.sent), sum((len(seq.read(i))+1023)//1024 for i in range(12)))
        self.assertEqual([json.loads(row)['status'] for row in log.getvalue().splitlines()], ['presented']*12)

    def test_prefix_three_requires_echoed_count_three(self):
        seq = self.sequence(3)
        fake = Fake()
        results = sender.upload(fake, PEER, seq, 8, io.StringIO(), 1)
        self.assertEqual([r['frame'] for r in results], [0, 1, 2])
        self.assertEqual(len(fake.sent), 58)
        self.assertEqual({x[2] for x in fake.sent}, {3})

    def test_count_mismatched_ack_never_advances_storage(self):
        fake = Fake(wrong_count=True)
        with patch.object(sender.core.time, 'monotonic', Clock()):
            with self.assertRaisesRegex(TimeoutError, 'stored offset1024|stored offset 1024'):
                sender.upload(fake, PEER, self.sequence(3), 7, io.StringIO(), 1)
        self.assertGreater(fake.receives, 0)
        self.assertEqual({(f, o) for f, o, count in fake.sent}, {(0, 0)})

    def test_failure_stops_before_next_dependent_frame(self):
        fake = Fake(fail_frame=4)
        with self.assertRaisesRegex(RuntimeError, 'failed/retained'):
            sender.upload(fake, PEER, self.sequence(), 7, io.StringIO(), 1)
        self.assertNotIn(5, [f for f, offset, count in fake.sent])

    def test_explicit_profile_and_bounds(self):
        for profile, count in [('dy71-bounded3-v2', 3), (sender.PROFILE, 0), (sender.PROFILE, 12001), (sender.PROFILE, 13)]:
            with self.assertRaises(ValueError):
                sender.Sequence(HERE/'manifest.json', profile, count)
        for count in [0, 12001]:
            with self.assertRaises(ValueError):
                sender.core.datagram(self.sequence(1).read(0), 7, 11, 0, count)

    def test_packet_hash_change_refused(self):
        seq = self.sequence(1)
        seq.rows[0]['files']['cu66']['sha256'] = '00'*32
        with self.assertRaisesRegex(ValueError, 'length/hash'):
            seq.read(0)

    def test_valid_crc_old_versions_and_zero_count_refused(self):
        fake = Fake()
        fake.sendto(sender.core.datagram(self.sequence(1).read(0), 7, 11, 0, 1), PEER)
        for version, count in [(1, 1), (2, 1), (3, 0), (3, 12001)]:
            reply = bytearray(fake.reply)
            reply[4] = version
            struct.pack_into('<H', reply, 46, count)
            reply[-4:] = struct.pack('<I', zlib.crc32(reply[:-4]))
            with self.assertRaisesRegex(ValueError, 'header'):
                sender.core.decode_reply(bytes(reply))

    def test_all_published_vectors(self):
        records = json.loads((HERE/'golden-vectors.json').read_text())['vectors']
        for row in records:
            wire = (HERE/row['file']).read_bytes()
            self.assertEqual(hashlib.sha256(wire).hexdigest(), row['sha256'])
            self.assertEqual(len(wire), row['bytes'])
            self.assertEqual(wire[4], 3)
            self.assertEqual(struct.unpack_from('<H', wire, 46)[0], row['sequence_count'])
            self.assertEqual(zlib.crc32(wire[:-4]), struct.unpack_from('<I', wire, len(wire)-4)[0])
            if row['kind'] == 'reply':
                self.assertEqual(sender.core.decode_reply(wire)[2], row['status'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
