import copy
import random
import unittest

from model import MAX_BLOCKS, PAYLOAD_BITS_PER_BANK, schedule, validate
from verify import validate_cohorts, validate_controls


class ScheduleTests(unittest.TestCase):
    def test_sequential_matches_measured_rtl_costs(self):
        result = schedule([0, 1, 2], 1)
        self.assertEqual(result['done_cycles'], 128 + 132 + 260)
        self.assertTrue(validate(result))

    def test_dense_and_zero_closed_forms(self):
        for banks in (2, 3):
            self.assertEqual(schedule([2] * 20, banks)['done_cycles'], 20 * 132 + 128)
            self.assertEqual(schedule([0] * 20, banks)['done_cycles'], 21 * 64)

    def test_seeded_schedules_and_no_bank_reuse_before_output(self):
        kinds = [random.Random(32 + i).randrange(3) for i in range(300)]
        values = [schedule(kinds, banks) for banks in (1, 2, 3)]
        for value in values:
            self.assertTrue(validate(value))
        self.assertLessEqual(values[1]['done_cycles'], values[0]['done_cycles'])
        broken = copy.deepcopy(values[1])
        broken['rows'][2]['load_start'] = 0
        with self.assertRaises(ValueError):
            validate(broken)

    def test_invalid_types_and_storage_bound(self):
        for kinds, banks in (([], 1), ([3], 1), ([True], 1), ([0], 0), ([0], 4)):
            with self.assertRaises(ValueError):
                schedule(kinds, banks)
        self.assertEqual(schedule([0], 2)['payload_storage_bits'], 2 * PAYLOAD_BITS_PER_BANK)
        self.assertEqual(schedule([0], 3)['payload_storage_bits'], 3 * PAYLOAD_BITS_PER_BANK)
        with self.assertRaises(ValueError):
            schedule([0] * (MAX_BLOCKS + 1), 1)

    def test_validate_rejects_four_banks_and_count_mismatches(self):
        result = schedule([0, 1], 3)
        four_bank_claim = copy.deepcopy(result)
        four_bank_claim['banks'] = 4
        four_bank_claim['payload_storage_bits'] = 4 * PAYLOAD_BITS_PER_BANK
        with self.assertRaises(ValueError):
            validate(four_bank_claim)

        bad_count = copy.deepcopy(result)
        bad_count['blocks'] += 1
        with self.assertRaises(ValueError):
            validate(bad_count)

        too_many = dict(blocks=MAX_BLOCKS + 1, banks=1, done_cycles=0,
                        payload_storage_bits=PAYLOAD_BITS_PER_BANK,
                        rows=[None] * (MAX_BLOCKS + 1))
        with self.assertRaises(ValueError):
            validate(too_many)

    def test_validate_rejects_malformed_rows_and_short_sample_services(self):
        valid = schedule([0], 1)
        for malformed in (None, [], {'rows': 'not rows'}):
            with self.assertRaises(ValueError):
                validate(malformed)
        bad_row = copy.deepcopy(valid)
        bad_row['rows'][0]['load_end'] = bad_row['rows'][0]['load_start'] + 63
        with self.assertRaises(ValueError):
            validate(bad_row)

    @staticmethod
    def _cohorts():
        source, output = [], []
        for scene in ('scene-a', 'scene-b'):
            for policy in ('control', 'strict', 'budget'):
                source_rows, output_rows = [], []
                for frame_id in range(48):
                    packet = dict(path=f'{scene}-{policy}-{frame_id}.zlib')
                    source_rows.append(dict(id=frame_id, base_packet=packet))
                    output_rows.append(dict(id=frame_id, base_packet=copy.deepcopy(packet),
                                            points=[dict(banks=b) for b in (1, 2, 3)]))
                source.append(dict(scene=scene, policy=policy, rows=source_rows))
                output.append(dict(scene=scene, policy=policy, rows=output_rows,
                                   summary={'1': {}, '2': {}, '3': {}}))
        return output, source

    def test_control_coverage_rejects_missing_or_duplicate_measured_frames(self):
        groups = [dict(scene=scene, frame_id=frame_id)
                  for scene in ('scene-a', 'scene-b') for frame_id in (0, 12)]
        controls = [dict(scene=group['scene'], frame_id=group['frame_id'],
                          points=[dict(banks=b) for b in (1, 2, 3)])
                    for group in groups]
        self.assertTrue(validate_controls(controls, groups))
        for malformed in (controls[:-1], controls + [copy.deepcopy(controls[0])]):
            with self.assertRaises(ValueError):
                validate_controls(malformed, groups)
        wrong_points = copy.deepcopy(controls)
        wrong_points[0]['points'].pop()
        with self.assertRaises(ValueError):
            validate_controls(wrong_points, groups)

    def test_cohort_lineage_rejects_duplicates_missing_frames_and_wrong_packets(self):
        output, source = self._cohorts()
        self.assertEqual(len(validate_cohorts(output, source)), 6)

        duplicate = copy.deepcopy(output)
        duplicate[-1] = copy.deepcopy(duplicate[0])
        with self.assertRaises(ValueError):
            validate_cohorts(duplicate, source)

        reordered = copy.deepcopy(output)
        reordered[0]['rows'][1]['id'] = 0
        with self.assertRaises(ValueError):
            validate_cohorts(reordered, source)

        wrong_packet = copy.deepcopy(output)
        wrong_packet[0]['rows'][0]['base_packet']['path'] = 'other.zlib'
        with self.assertRaises(ValueError):
            validate_cohorts(wrong_packet, source)


if __name__ == '__main__':
    unittest.main()
