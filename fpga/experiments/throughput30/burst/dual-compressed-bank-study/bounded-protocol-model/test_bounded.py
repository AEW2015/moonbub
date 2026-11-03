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
        retained = p.last
        self.assertEqual(p.request(3, 0, 'BEGIN', frame_id=2, length=2, crc=0).outcome, 'REQUEST_ID_CONFLICT')
        self.assertEqual(p.next_seq, 1)
        self.assertIs(p.last, retained)
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

    def test_out_of_order_does_not_consume_id_and_old_retry_expires(self):
        p = BoundedProtocol(21)
        token = p.request(21, 0, 'BEGIN', frame_id=1, length=1,
                          crc=zlib.crc32(b'a')).token
        first = p.request(21, 1, 'UNKNOWN', token=token)
        self.assertEqual(first.outcome, 'UNKNOWN_OP')
        self.assertEqual(p.request(21, 3, 'UNKNOWN', token=token).outcome, 'OUT_OF_ORDER')
        self.assertEqual(p.next_seq, 2)
        second = p.request(21, 2, 'UNKNOWN', token=token)
        self.assertEqual(second.outcome, 'UNKNOWN_OP')
        self.assertEqual(p.next_seq, 3)
        # Only the immediately preceding ID is replayable under stop-and-wait.
        self.assertEqual(p.request(21, 1, 'UNKNOWN', token=token).outcome, 'OUT_OF_ORDER')
        self.assertEqual(p.request(21, 2, 'UNKNOWN', token=token), second)

    def test_reset_discards_cache_and_failed_reset_preserves_it(self):
        p = BoundedProtocol(30)
        original = p.request(30, 0, 'BEGIN', frame_id=8, length=1,
                             crc=zlib.crc32(b'x'))
        with self.assertRaises(ValueError):
            p.reset(30)
        self.assertEqual(p.request(30, 0, 'BEGIN', frame_id=8, length=1,
                                  crc=zlib.crc32(b'x')), original)
        p.reset(31)
        # An old-epoch retry cannot recover the ACK once reset discarded cache.
        self.assertEqual(p.request(30, 0, 'BEGIN', frame_id=8, length=1,
                                  crc=zlib.crc32(b'x')).outcome, 'STALE_EPOCH')
        fresh = p.request(31, 0, 'BEGIN', frame_id=9, length=1,
                          crc=zlib.crc32(b'y'))
        self.assertEqual(fresh.outcome, 'BEGIN_OK')
        self.assertEqual(p.next_seq, 1)

    def test_request_history_stays_empty_and_only_last_body_is_retained(self):
        p = BoundedProtocol(40)
        token = p.request(40, 0, 'BEGIN', frame_id=1, length=1,
                          crc=zlib.crc32(b'a')).token
        old_body = p.last
        ack = None
        for seq in range(1, 5001):
            ack = p.request(40, seq, 'UNKNOWN', token=token, offset=seq)
            self.assertEqual(ack.outcome, 'UNKNOWN_OP')
            self.assertEqual(len(p.core.history), 0)
            self.assertIsNotNone(p.last)
        self.assertEqual(p.next_seq, 5001)
        self.assertNotEqual(p.last, old_body)
        self.assertEqual(p.request(40, 5000, 'UNKNOWN', token=token, offset=5000), ack)

    def test_payload_limit_rejects_without_core_cache_or_sequence_effect(self):
        p = BoundedProtocol(50, capacity=2048)
        begin = p.request(50, 0, 'BEGIN', frame_id=1, length=1024,
                          crc=zlib.crc32(b'a' * 1024))
        self.assertEqual(begin.outcome, 'BEGIN_OK')
        retained = p.last
        bank = p.core.banks[begin.token.bank]
        before = (bank.state, bank.frame_id, bank.expected_length, bytes(bank.data))
        original_core_request = p.core.request
        p.core.request = lambda *args, **kwargs: self.fail('oversized request reached core')
        too_large = b'z' * 1025
        ack = p.request(50, 1, 'DATA', token=begin.token, offset=0,
                        payload=too_large)
        p.core.request = original_core_request
        self.assertEqual(ack.outcome, 'REQUEST_TOO_LARGE')
        self.assertEqual(p.next_seq, 1)
        self.assertIs(p.last, retained)
        self.assertEqual(len(p.core.history), 0)
        self.assertEqual((bank.state, bank.frame_id, bank.expected_length, bytes(bank.data)), before)
        exact_limit = b'a' * 1024
        accepted = p.request(50, 1, 'DATA', token=begin.token, offset=0,
                             payload=exact_limit)
        self.assertEqual(accepted.outcome, 'DATA_OK')
        self.assertEqual(accepted.count, 1024)
        self.assertLessEqual(len(dict(p.last[0][1])['payload']), 1024)

    def test_mutable_or_non_wire_values_do_not_consume_id_or_mutate_state(self):
        p = BoundedProtocol(60, capacity=8)
        initial_last = p.last
        invalid = p.request(60, 0, 'BEGIN', frame_id=[], length=1,
                             crc=zlib.crc32(b'a'))
        self.assertEqual(invalid.outcome, 'INVALID_REQUEST')
        self.assertEqual(p.next_seq, 0)
        self.assertIs(p.last, initial_last)
        self.assertEqual([b.state for b in p.core.banks], ['FREE', 'FREE'])
        self.assertEqual(len(p.core.history), 0)
        begin = p.request(60, 0, 'BEGIN', frame_id=2, length=1,
                          crc=zlib.crc32(b'a'))
        self.assertEqual(begin.outcome, 'BEGIN_OK')
        retained = p.last
        bad_data = p.request(60, 1, 'DATA', token=begin.token, offset=0,
                             payload=bytearray(b'a'))
        self.assertEqual(bad_data.outcome, 'INVALID_REQUEST')
        self.assertEqual(p.next_seq, 1)
        self.assertIs(p.last, retained)
        self.assertEqual(len(p.core.banks[begin.token.bank].data), 0)
        self.assertEqual(len(p.core.history), 0)
        good_data = p.request(60, 1, 'DATA', token=begin.token, offset=0,
                              payload=b'a')
        self.assertEqual(good_data.outcome, 'DATA_OK')

    def test_envelope_and_oversized_opcode_are_rejected(self):
        p = BoundedProtocol(70)
        for bad_epoch, bad_op in ((True, 'BEGIN'), (70, 'x' * 17), (70, 'é')):
            ack = p.request(bad_epoch, 0, bad_op, frame_id=1, length=1, crc=0)
            self.assertEqual(ack.outcome, 'INVALID_REQUEST')
            self.assertEqual(p.next_seq, 0)
            self.assertIsNone(p.last)
        with self.assertRaises(ValueError):
            p.request(70, True, 'BEGIN', frame_id=1, length=1, crc=0)
        self.assertEqual(p.next_seq, 0)
        self.assertIsNone(p.last)


if __name__ == '__main__':
    unittest.main()
