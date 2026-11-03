import json
import unittest
from analyze import analyze, HZ

def row(i, age, present=None):
    a = (i-1)*HZ
    p = a+age if present is None else present
    return dict(id=i, frame_id=i, arrival_cycle=a, commit_cycle=a, present_cycle=p,
                arrival_to_present_cycles=p-a, jpeg_sha256='a'*64, rtl_dump_sha256='b'*64,
                writes=345600, bursts=43200, cmodel_exact_pixels=345600, underruns=0)
def run(rows, tail=b''):
    data = b''.join(json.dumps(r).encode()+b'\n' for r in rows)+tail
    return analyze(data, {'frames':[dict(id=i,jpeg_sha256='a'*64) for i in range(len(rows))]})
class Tests(unittest.TestCase):
    def test_threshold_and_partial(self):
        r = run([row(1, HZ//30), row(2, HZ//30+1)], b'{partial')
        self.assertEqual(r['arrival_to_presentation_deadline']['misses'], 1)
        self.assertEqual(r['trailing_partial_bytes_ignored'], 8)
        self.assertEqual(r['arrival_to_presentation']['p50_ms'], (HZ//30)*1000/HZ)
    def test_one_frame(self):
        r = run([row(1, 0)])
        self.assertIsNone(r['presentation_fps_first_to_last'])
        self.assertIsNone(r['presentation_intervals'])
    def test_bad_records(self):
        a = row(1, 20); a['arrival_to_present_cycles'] = 21
        with self.assertRaises(ValueError): run([a])
        with self.assertRaises(ValueError): run([row(2, 1)])
        with self.assertRaises(ValueError): run([])
if __name__ == '__main__': unittest.main()
