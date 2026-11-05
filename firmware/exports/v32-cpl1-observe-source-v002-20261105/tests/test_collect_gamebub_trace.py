"""Focused validation of bounded v29 trace export records."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from collect_gamebub_trace import (  # noqa: E402
    EVENT_FIELDS, FAILURE_FIELDS, PREFIX, parse_records, valid_entry, validate, valid_summary,
)


def summary_pages(records=1, failures=1, epoch='7', pages=25, frozen='true'):
    first = {
        's': '0', 'epoch': epoch, 'pages': str(pages), 'records': str(records),
        'failures': str(failures), 'armed': 'false', 'frozen': frozen, 'bytes': '4000',
    }
    result={0:first}
    result[1]={'s':'1','epoch':epoch,'recorded':'1','overwritten':'0','lost_records':'0','lost_phase':'0'}
    result[2]={'s':'2','epoch':epoch,'queue_overflows':'0','lost_failures':'0','failure_overflow':'0','counters_valid':'true','ambiguous_tails':'0'}
    result[3]={'s':'3','epoch':epoch,'first':'1','last':'1','post':'0','triggered':'false','trigger_lost':'false'}
    result[4]={'s':'4','epoch':epoch,'first_overflow_us':'0','time_valid':'false'}
    for i in range(5,pages-4):result[i]={'s':str(i),'epoch':epoch,'phase':str(i-5),'max_us':'0'}
    for i in range(pages-4,pages):result[i]={'s':str(i),'epoch':epoch,'trigger_valid':'false'}
    return result


def event_page(index, page, epoch='7', seq='22'):
    common = {'e': str(index), 'p': str(page), 'epoch': epoch, 'seq': seq}
    if page == 0:
        return common | {'us': '100', 'kind': '2', 'phase': '3'}
    if page == 1:
        return common | {'in_id': '4', 'in_off': '512', 'in_v': '3', 'queued': '2', 'qv': 'true'}
    if page == 2:
        return common | {'active_id': '4', 'expected': '768', 'active_v': '3', 'since': '90', 'pv': 'true'}
    if page == 4:return common | {'consumer':'40','valid':'true'}
    return common | {'rx': '30', 'lock': '5', 'qspi': '9', 'detail': '1', 'clipped': 'false'}


def failure_page(index, page, epoch='7', seq='29'):
    common = {'f': str(index), 'p': str(page), 'epoch': epoch, 'seq': seq}
    if page == 0:
        return common | {'us': '100', 'in_id': '4', 'in_off': '512', 'in_v': '3'}
    if page == 3:return common | {'rx':'30','tail_ambiguous':'false'}
    if page == 2:return common | {'consumer':'40','valid':'true','clipped':'false'}
    return common | {'active_id': '4', 'expected': '768', 'active_v': '3',
                      'queued': '2', 'qv': 'true', 'detail': '6'}


class CollectGamebubTraceTests(unittest.TestCase):
    def test_valid_frozen_export_with_event_and_failure_pages(self):
        events = {0: {p: event_page(0, p) for p in range(5)}}
        failures = {0: {p: failure_page(0, p) for p in range(4)}}
        self.assertTrue(validate(summary_pages(), events, failures))

    def test_missing_event_page_is_rejected(self):
        events = {0: {p: event_page(0, p) for p in (0, 1, 3)}}
        with self.assertRaisesRegex(AssertionError, 'entry page missing'):
            validate(summary_pages(failures=0), events, {})

    def test_torn_sequence_across_event_pages_is_rejected(self):
        pages = {p: event_page(0, p) for p in range(5)}
        pages[2]['seq'] = '23'
        with self.assertRaisesRegex(AssertionError, 'torn entry sequence'):
            validate(summary_pages(failures=0), {0: pages}, {})

    def test_epoch_change_across_export_pages_is_rejected(self):
        summaries = summary_pages(failures=0)
        summaries[5] = {'s': '5', 'epoch': '8'}
        with self.assertRaisesRegex(AssertionError, 'summary epoch changed'):
            validate(summaries, {0: {p: event_page(0, p) for p in range(5)}}, {})

    def test_epoch_change_across_event_pages_is_rejected(self):
        events = {0: {p: event_page(0, p) for p in range(5)}}
        events[0][3]['epoch'] = '8'
        with self.assertRaisesRegex(AssertionError, 'entry epoch changed'):
            validate(summary_pages(failures=0), events, {})

    def test_truncated_boolean_and_non_numeric_values_are_rejected(self):
        truncated = event_page(0, 1) | {'qv': 'tru'}
        self.assertFalse(valid_entry(truncated, EVENT_FIELDS))
        non_numeric = event_page(0, 0) | {'us': '12x'}
        self.assertFalse(valid_entry(non_numeric, EVENT_FIELDS))
        truncated_failure = failure_page(0, 1) | {'qv': 'truee'}
        self.assertFalse(valid_entry(truncated_failure, FAILURE_FIELDS))

    def test_empty_but_frozen_export_is_valid(self):
        self.assertTrue(validate(summary_pages(records=0, failures=0), {}, {}))

    def test_negative_counts_and_timestamps_are_rejected(self):
        with self.assertRaisesRegex(AssertionError,'invalid summary page'):
            validate(summary_pages(records=-1, failures=0), {}, {})
        self.assertFalse(valid_entry(event_page(0,0) | {'us':'-1'}, EVENT_FIELDS))
        self.assertFalse(valid_entry(event_page(0,0) | {'seq':str(2**64)}, EVENT_FIELDS))

    def test_background_transfer_kind_is_valid_but_unknown_kind_is_rejected(self):
        self.assertTrue(valid_entry(event_page(0,0) | {'kind':'7'}, EVENT_FIELDS))
        self.assertFalse(valid_entry(event_page(0,0) | {'kind':'8'}, EVENT_FIELDS))

    def test_auto_frozen_but_still_armed_is_not_a_sealed_export(self):
        summaries=summary_pages(records=0,failures=0)
        summaries[0]['armed']='true'
        with self.assertRaisesRegex(AssertionError,'manually sealed'):
            validate(summaries,{}, {})

    def test_parser_handles_multiple_prefixes_on_one_line(self):
        line = (PREFIX + 'e=0 p=0 epoch=7 seq=22 us=100 kind=2 phase=3 ' +
                PREFIX + 'e=1 p=0 epoch=7 seq=23 us=101 kind=2 phase=3\n')
        records = parse_records(line)
        self.assertEqual(len(records), 2)
        self.assertEqual([r['e'] for r in records], ['0', '1'])

    def v2_summary(self):
        pages=summary_pages(records=0,failures=0)
        for r in pages.values():r['v']='2'
        pages[0]['pages']='33'
        for kind in range(8):
            i=25+kind;pages[i]={'v':'2','s':str(i),'epoch':'7','kind':str(kind),'lost':'0','loss_valid':'true'}
        return pages

    def test_v2_loss_pages_and_totals_are_required(self):
        pages=self.v2_summary();pages[25]['lost']='7';pages[30]['lost']='2';pages[1]['lost_records']='9'
        self.assertTrue(validate(pages,{},{}))
        pages[30]['lost']='3'
        with self.assertRaisesRegex(AssertionError,'loss totals mismatch'):validate(pages,{},{})
        del pages[32]
        with self.assertRaisesRegex(AssertionError,'summary pages missing'):validate(pages,{},{})

    def test_unknown_and_mixed_versions_are_rejected(self):
        pages=self.v2_summary();pages[0]['v']='3'
        with self.assertRaisesRegex(AssertionError,'unsupported schema'):validate(pages,{},{})
        pages=self.v2_summary();pages[1]['v']='1'
        with self.assertRaisesRegex(AssertionError,'mixed summary schema'):validate(pages,{},{})
        self.assertFalse(valid_entry(event_page(0,0)|{'v':'3'},EVENT_FIELDS))

    def test_v2_counter_kind_validity_and_limits_are_checked(self):
        pages=self.v2_summary();pages[25]['kind']='7'
        self.assertFalse(valid_summary(pages[25],33))
        pages=self.v2_summary();pages[25]['loss_valid']='false'
        with self.assertRaisesRegex(AssertionError,'validity mismatch'):validate(pages,{},{})
        pages=self.v2_summary();pages[25]['lost']=str(2**32)
        self.assertFalse(valid_summary(pages[25],33))

    def test_v2_parser_retains_version_and_v1_compatibility(self):
        records=parse_records(PREFIX+'s=0 epoch=7 pages=25\nUSB_TRACE rxdiag v=2 s=25 epoch=7 kind=0 lost=1 loss_valid=true\n')
        self.assertEqual([x['v'] for x in records],['1','2'])

    def test_v2_event_version_must_match_and_downgrade_is_rejected(self):
        pages=self.v2_summary();pages[0]['records']='1'
        events={0:{i:event_page(0,i)|{'v':'2'} for i in range(5)}}
        self.assertTrue(validate(pages,events,{}))
        events[0][2]['v']='1'
        with self.assertRaisesRegex(AssertionError,'mixed entry schema'):validate(pages,events,{})


if __name__ == '__main__':
    unittest.main()

