import unittest
import zlib
from bounded import BoundedProtocol


class StopAndWaitTests(unittest.TestCase):
    def test_retry_is_idempotent_and_old_requests_cannot_mutate(self):
        p = BoundedProtocol(3, capacity=8)
        begin = dict(frame_id=1, length=2, crc=zlib.crc32(b'ab'))
        a = p.request(3, 0, 'BEGIN', **begin)
        self.assertEqual(a.outcome, 'BEGIN_OK')
        self.assertEqual(p.request(3, 0, 'BEGIN', **begin), a)
        self.assertEqual(p.request(3, 0, 'BEGIN', frame_id=2, length=2, crc=0).outcome, 'REQUEST_ID_CONFLICT')
        data = dict(token=a.token, offset=0, payload=b'ab')
        first = p.request(3, 1, 'DATA', **data)
        self.assertEqual(p.request(3, 1, 'DATA', **data), first)
        self.assertEqual(p.request(3, 0, 'BEGIN', **begin).outcome, 'OUT_OF_ORDER')
        self.assertEqual(p.request(3, 3, 'COMMIT', token=a.token).outcome, 'OUT_OF_ORDER')
        self.assertEqual(p.request(3, 2, 'COMMIT', token=a.token).outcome, 'COMMIT_OK')
        self.assertEqual(bytes(p.core.banks[a.token.bank].data), b'ab')
        self.assertEqual(len(p.core.history), 0)

    def test_abort_reuse_reset_and_epoch(self):
        p = BoundedProtocol(9)
        old = p.request(9, 0, 'BEGIN', frame_id=1, length=1, crc=zlib.crc32(b'a')).token
        self.assertEqual(p.request(9, 1, 'ABORT', token=old).outcome, 'ABORT_OK')
        new = p.request(9, 2, 'BEGIN', frame_id=2, length=1, crc=zlib.crc32(b'b')).token
        self.assertNotEqual(new, old)
        self.assertEqual(p.request(9, 3, 'ABORT', token=old).outcome, 'STALE_TOKEN')
        self.assertEqual(p.core.banks[new.bank].state, 'RECEIVING')
        p.reset(10)
        self.assertEqual(p.request(9, 4, 'ABORT', token=new).outcome, 'STALE_EPOCH')
        self.assertEqual(p.request(10, 0, 'ABORT', token=new).outcome, 'STALE_TOKEN')
        with self.assertRaises(ValueError):
            p.reset(10)

    def test_rejected_response_is_cached_and_consumes_sequence(self):
        p = BoundedProtocol(1, capacity=1)
        a = p.request(1, 0, 'BEGIN', frame_id=5, length=2, crc=0)
        self.assertEqual(a.outcome, 'INVALID_BEGIN')
        self.assertEqual(p.request(1, 0, 'BEGIN', frame_id=5, length=2, crc=0), a)
        self.assertEqual(p.request(1, 2, 'BEGIN', frame_id=5, length=1, crc=0).outcome, 'OUT_OF_ORDER')
        self.assertEqual(p.request(1, 1, 'BEGIN', frame_id=5, length=1, crc=0).outcome, 'BEGIN_OK')


if __name__ == '__main__':
    unittest.main()
