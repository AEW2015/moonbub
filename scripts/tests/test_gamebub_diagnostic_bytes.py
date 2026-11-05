"""Reproduce partial-read, merged-line and credential-boundary capture failures."""
import hashlib
import io
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gamebub_diagnostic_bytes import DiagnosticBytes, LineFramer


class DiagnosticByteTests(unittest.TestCase):
    def test_every_split_preserves_utf8_and_crlf_bytes(self):
        source = 'I diag USB_D24 c=1 p=begin λ\r\nI diag USB_D24 c=1 p=end\r\n'.encode()
        for cut in range(len(source) + 1):
            framer = LineFramer()
            records = []
            for chunk in (source[:cut], source[cut:]):
                lines, discarded = framer.feed(chunk)
                self.assertEqual(discarded, [])
                records.extend(lines)
            self.assertEqual(b''.join(records), source)
            self.assertEqual(framer.finish(), ([], []))

    def test_partial_line_is_not_merged_across_disconnect(self):
        framer = LineFramer()
        self.assertEqual(framer.feed(b'USB_D24 partial'), ([], []))
        self.assertEqual(framer.finish(), ([b'USB_D24 partial'], []))
        self.assertEqual(framer.feed(b'USB_TEST fresh\r\n'), ([b'USB_TEST fresh\r\n'], []))

    def test_oversize_drop_is_explicit_and_next_record_survives(self):
        source = b'USB_D24 ' + b'x' * 100 + b'\r\n'
        framer = LineFramer(24)
        self.assertEqual(framer.feed(source[:40]), ([], []))
        self.assertEqual(framer.feed(source[40:] + b'USB_TEST ok\n'),
                         ([b'USB_TEST ok\n'], [len(source)]))
        self.assertEqual(framer.finish(), ([], []))
        framer.feed(b'z' * 30)
        self.assertEqual(framer.finish(), ([], [30]))

    def test_index_hashes_and_offsets_are_byte_based_not_text_offsets(self):
        raw, index = io.BytesIO(), io.StringIO()
        capture = DiagnosticBytes(raw, index)
        records = ['USB_D24 λ\r\n'.encode(), b'USB_D24 second\n', b'USB_TRACE partial']
        for record in records:
            capture.select(record, 'test-time')
        self.assertEqual(raw.getvalue(), b''.join(records))
        events = [json.loads(line) for line in index.getvalue().splitlines()]
        self.assertEqual([e['offset'] for e in events], [0, len(records[0]), len(records[0] + records[1])])
        self.assertEqual([e['partial'] for e in events], [False, False, True])
        for event, record in zip(events, records):
            self.assertEqual(event['sha256'], hashlib.sha256(record).hexdigest())

    def test_merged_records_are_preserved_and_counted(self):
        merged = b'USB_D24 p=fd1 brokenI diag USB_D24 p=fd5\r\n'
        raw, index = io.BytesIO(), io.StringIO()
        capture = DiagnosticBytes(raw, index)
        capture.select(merged, 'test-time')
        self.assertEqual(raw.getvalue(), merged)
        self.assertEqual(json.loads(index.getvalue())['d24_markers'], 2)

    def test_split_credential_record_is_withheld_before_storage(self):
        for cut in range(1, 37):
            source = b'USB_TRACE password=do-not-retain-this\r\n'
            raw, index = io.BytesIO(), io.StringIO()
            capture, framer = DiagnosticBytes(raw, index), LineFramer()
            for chunk in (source[:cut], source[cut:]):
                records, _ = framer.feed(chunk)
                for record in records:
                    capture.select(record, 'test-time')
            self.assertNotIn(b'do-not-retain-this', raw.getvalue())
            self.assertNotIn('do-not-retain-this', index.getvalue())
            self.assertTrue(json.loads(index.getvalue())['redacted'])

    def test_panic_context_is_bounded_and_credentials_still_redacted(self):
        raw, index = io.BytesIO(), io.StringIO()
        capture = DiagnosticBytes(raw, index)
        self.assertIsNone(capture.select(b'ordinary unrelated log\n', 'test-time'))
        capture.select(b'Guru Meditation\n', 'test-time')
        capture.select(b'password=private\n', 'test-time')
        for _ in range(60):
            capture.select(b'panic detail\n', 'test-time')
        self.assertEqual(capture.records, 45)
        self.assertNotIn(b'private', raw.getvalue())


if __name__ == '__main__':
    unittest.main()
