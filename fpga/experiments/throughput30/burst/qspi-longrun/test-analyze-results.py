"""Checks status classification on synthetic records; not an RTL test."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT=Path(__file__).with_name('analyze-results.py')


class Classification(unittest.TestCase):
    def test_partial_is_not_pass(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);checked=root/'checked';checked.mkdir()
            row={'frame_id':1,'arrival_cycle':0,'commit_cycle':1,'present_cycle':2000000,
                 'arrival_to_present_cycles':2000000,'writes':345600,'bursts':43200,'underruns':0,
                 'rtl_dump_sha256':'x','jpeg_sha256':'a','cmodel_exact_pixels':345600,'upload_cycles':2}
            (checked/'verified.jsonl').write_text(json.dumps(row)+'\n');(checked/'simulation.log').write_text('FRAME_RESULT\n')
            result=subprocess.run([sys.executable,str(SCRIPT),str(root),'--output',str(root/'out.json')],capture_output=True)
            self.assertNotEqual(result.returncode,0)
            data=json.loads((root/'out.json').read_text());self.assertEqual(data['status'],'INCOMPLETE')
            self.assertIsNone(data['fps_60s_capture_window'])

    def test_fatal_is_never_pass(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);checked=root/'checked';checked.mkdir()
            row={'frame_id':1,'arrival_cycle':0,'commit_cycle':1,'present_cycle':2000000,
                 'arrival_to_present_cycles':2000000,'writes':345600,'bursts':43200,'underruns':0,
                 'rtl_dump_sha256':'x','jpeg_sha256':'a','cmodel_exact_pixels':345600,'upload_cycles':2}
            (checked/'verified.jsonl').write_text(json.dumps(row)+'\n');(checked/'simulation.log').write_text('%Fatal: error\n')
            result=subprocess.run([sys.executable,str(SCRIPT),str(root),'--output',str(root/'out.json')],capture_output=True)
            self.assertNotEqual(result.returncode,0)
            self.assertEqual(json.loads((root/'out.json').read_text())['status'],'FAIL_STRICT')

    def test_complete_records_still_fail_with_terminal_fatal(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);checked=root/'checked';checked.mkdir()
            rows=[]
            for i in range(1800):
                arrival=i*10000000//3
                rows.append({'frame_id':i+1,'arrival_cycle':arrival,'commit_cycle':arrival+1,
                             'present_cycle':arrival+2000000,'arrival_to_present_cycles':2000000,
                             'writes':345600,'bursts':43200,'underruns':0,'rtl_dump_sha256':str(i),
                             'jpeg_sha256':str(i),'cmodel_exact_pixels':345600,'upload_cycles':2})
            (checked/'verified.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
            (checked/'summary.json').write_text(json.dumps({'frames':1800,'pass_marker':True,
                                                           'window':{'strict':1,'elapsed_cycles':6000000000,'epoch':0,'end':6000000000}}))
            (checked/'simulation.log').write_text('TEST_PASS_JPEG720_60S frames=1800\n%Fatal: terminal\n')
            result=subprocess.run([sys.executable,str(SCRIPT),str(root),'--output',str(root/'out.json')],capture_output=True)
            self.assertNotEqual(result.returncode,0)
            data=json.loads((root/'out.json').read_text())
            self.assertEqual(data['verified_frames'],1800);self.assertEqual(data['status'],'FAIL_STRICT')

    def test_terminal_success_requires_marker_and_exact_window(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);checked=root/'checked';checked.mkdir();rows=[]
            for i in range(1800):
                arrival=i*10000000//3
                rows.append({'frame_id':i+1,'arrival_cycle':arrival,'commit_cycle':arrival+1,
                             'present_cycle':arrival+2000000,'arrival_to_present_cycles':2000000,
                             'writes':345600,'bursts':43200,'underruns':0,'rtl_dump_sha256':str(i),
                             'jpeg_sha256':str(i),'cmodel_exact_pixels':345600,'upload_cycles':2})
            # The upper boundary is inclusive: a presentation exactly at 60 s counts.
            rows[-1]['present_cycle']=6000000000
            rows[-1]['arrival_to_present_cycles']=rows[-1]['present_cycle']-rows[-1]['arrival_cycle']
            (checked/'verified.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
            (checked/'summary.json').write_text(json.dumps({'frames':1800,'pass_marker':True,
                                                           'window':{'strict':1,'elapsed_cycles':6000000000,'epoch':0,'end':6000000000}}))
            events=''.join('FRAME_RESULT '+f"id={r['frame_id']} "+' '.join(f"{k}={r[k]}" for k in ('arrival_cycle','commit_cycle','present_cycle','arrival_to_present_cycles','writes','bursts','underruns','upload_cycles'))+'\n' for r in rows)
            (checked/'simulation.log').write_text(events+'TEST_PASS_JPEG720_60S frames=1800\n')
            result=subprocess.run([sys.executable,str(SCRIPT),str(root),'--output',str(root/'out.json')],capture_output=True)
            self.assertEqual(result.returncode,0)
            data=json.loads((root/'out.json').read_text())
            self.assertEqual(data['status'],'PASS_STRICT');self.assertEqual(data['within_strict_window'],1800)
            self.assertEqual(data['first_frame_above_u32_cycle'],1289)
            # One cycle late cannot pass, even with an erroneous terminal PASS marker.
            rows[-1]['present_cycle']+=1
            rows[-1]['arrival_to_present_cycles']+=1
            (checked/'verified.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
            events=''.join('FRAME_RESULT '+f"id={r['frame_id']} "+' '.join(f"{k}={r[k]}" for k in ('arrival_cycle','commit_cycle','present_cycle','arrival_to_present_cycles','writes','bursts','underruns','upload_cycles'))+'\n' for r in rows)
            (checked/'simulation.log').write_text(events+'TEST_PASS_JPEG720_60S frames=1800\n')
            result=subprocess.run([sys.executable,str(SCRIPT),str(root),'--output',str(root/'out.json')],capture_output=True)
            self.assertNotEqual(result.returncode,0)
            data=json.loads((root/'out.json').read_text())
            self.assertNotEqual(data['status'],'PASS_STRICT');self.assertEqual(data['within_strict_window'],1799)

    def test_reject_duplicate_presentation_and_wrong_capture_cadence(self):
        for kind in ('duplicate_presentation','wrong_capture_cadence'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as d:
                root=Path(d);checked=root/'checked';checked.mkdir()
                rows=[]
                for i in range(2):
                    arrival=i*10000000//3
                    rows.append({'frame_id':i+1,'arrival_cycle':arrival,'commit_cycle':arrival+1,
                                 'present_cycle':arrival+4000000,'arrival_to_present_cycles':4000000,
                                 'writes':345600,'bursts':43200,'underruns':0,'rtl_dump_sha256':str(i),
                                 'jpeg_sha256':str(i),'cmodel_exact_pixels':345600,'upload_cycles':2})
                if kind=='duplicate_presentation':
                    rows[1]['present_cycle']=rows[0]['present_cycle']
                    rows[1]['arrival_to_present_cycles']=rows[1]['present_cycle']-rows[1]['arrival_cycle']
                else:
                    rows[1]['arrival_cycle']+=1;rows[1]['arrival_to_present_cycles']-=1
                (checked/'verified.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
                (checked/'simulation.log').write_text('')
                result=subprocess.run([sys.executable,str(SCRIPT),str(root),'--output',str(root/'out.json')],capture_output=True)
                self.assertNotEqual(result.returncode,0)
                self.assertFalse((root/'out.json').exists())

    def test_missing_frame_log_cannot_pass(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);checked=root/'checked';checked.mkdir();rows=[]
            for i in range(1800):
                arrival=i*10000000//3
                rows.append({'frame_id':i+1,'arrival_cycle':arrival,'commit_cycle':arrival+1,
                             'present_cycle':arrival+2000000,'arrival_to_present_cycles':2000000,
                             'writes':345600,'bursts':43200,'underruns':0,'rtl_dump_sha256':str(i),
                             'jpeg_sha256':str(i),'cmodel_exact_pixels':345600,'upload_cycles':2})
            (checked/'verified.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
            (checked/'summary.json').write_text(json.dumps({'frames':1800,'pass_marker':True,
                         'window':{'strict':1,'elapsed_cycles':6000000000,'epoch':0,'end':6000000000}}))
            (checked/'simulation.log').write_text('TEST_PASS_JPEG720_60S frames=1800\n')
            result=subprocess.run([sys.executable,str(SCRIPT),str(root),'--output',str(root/'out.json')],capture_output=True)
            self.assertNotEqual(result.returncode,0)
            data=json.loads((root/'out.json').read_text());self.assertFalse(data['frame_log_records_match'])
            self.assertEqual(data['status'],'INCOMPLETE')

if __name__=='__main__':unittest.main()
