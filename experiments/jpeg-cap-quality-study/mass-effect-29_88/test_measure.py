"""Consistency checks for the second native-rate clip study output."""
import csv
import json
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent


class GeneratedStudyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.results = json.loads((HERE / 'results.json').read_text())
        with (HERE / 'per-frame.csv').open(newline='') as stream:
            cls.rows = list(csv.DictReader(stream))

    def test_native_clip_metadata_and_all_quality_rows(self):
        self.assertEqual(self.results['source_video']['average_rate'], '747/25')
        self.assertEqual(self.results['source_video']['decoded_frame_count'], len(self.rows))
        self.assertEqual(len(self.rows), 360)
        self.assertEqual(set(self.results['qualities']), {'75', '80', '85', '90'})
        for q in ('75', '80', '85', '90'):
            self.assertEqual(self.results['qualities'][q]['jpeg_bytes']['count'], len(self.rows))

    def test_overflow_and_retry_summary_match_csv(self):
        cap = self.results['cap_bytes']
        for q in ('75', '80', '85', '90'):
            self.assertEqual(
                sum(int(row[f'q{q}_bytes']) > cap for row in self.rows),
                self.results['qualities'][q]['over_cap_count'],
            )
        retry = self.results['q90_then_q80_retry']
        self.assertEqual(sum(row['retry_action'] == 'send_q90' for row in self.rows), retry['q90_count'])
        self.assertEqual(sum(row['retry_action'] == 'retry_q80' for row in self.rows), retry['q80_retry_count'])
        self.assertEqual(sum(row['retry_action'] == 'drop_after_retry' for row in self.rows), retry['dropped_count'])
        self.assertTrue(all(int(row['retry_bytes']) <= cap for row in self.rows if row['retry_bytes']))

    def test_source_and_offline_scope_are_recorded(self):
        self.assertEqual(len(self.results['source_sha256']), 64)
        self.assertTrue(any('offline sequential' in note.lower() for note in self.results['caveats']))
        self.assertTrue(any('prerecorded' in note.lower() for note in self.results['caveats']))


if __name__ == '__main__':
    unittest.main()
