#!/usr/bin/env python3
"""Directed consistency and negative controls for the bounded queue model."""
import json, os, shutil, subprocess, tempfile, unittest, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[5]/"host"))
from moonshine.protocol import packets
from queue_model import simulate
HERE=Path(__file__).resolve().parent
FIXTURES=Path(os.environ['FIXTURE_DIR'])

def run(fixtures=FIXTURES, extra=()):
    return subprocess.run(['python3',str(HERE/'queue_model.py'),'--fixtures',str(fixtures),*extra],capture_output=True,text=True)

class ModelTests(unittest.TestCase):
    def test_bounded_cases(self):
        r=run(); self.assertEqual(r.returncode,0,r.stderr);cases=json.loads(r.stdout)['cases']
        for case in cases:
            self.assertLessEqual(case['max_staged_bytes'],case['capacity_bytes'])
            ids=[x['id'] for x in case['completed']]+[x['id'] for x in case['dropped']]
            self.assertEqual(sorted(ids),list(range(10)))
        self.assertEqual([x['id'] for x in cases[0]['completed']],[0,2,4,6,8])
        self.assertTrue(all(x['reason']=='busy_sof' for x in cases[0]['dropped']))
        self.assertEqual([x['id'] for x in cases[1]['dropped']],[4,9])
    def test_larger_buffer_has_fewer_drops_but_older_frames(self):
        r=run(extra=('--large-bytes','262144'));self.assertEqual(r.returncode,0,r.stderr)
        case=json.loads(r.stdout)['cases'][1]
        self.assertEqual(len(case['completed']),10);self.assertEqual(case['dropped'],[])
        self.assertGreater(case['max_staged_bytes'],32768);self.assertGreater(case['max_age_ms'],100)
    def test_corrupt_fixture_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            d=Path(t)
            for source in FIXTURES.glob('*.jpg'):shutil.copy(source,d/source.name)
            f=d/'0000.jpg';v=bytearray(f.read_bytes());v[100]^=1;f.write_bytes(v)
            r=run(d);self.assertNotEqual(r.returncode,0);self.assertIn('datagram hash mismatch',r.stderr)
def evt(fid, body, offset, at, chunk=5, capture=0):
    wire=list(packets(body,fid,capture//100,payload_size=chunk))[offset]
    return {'id':fid,'wire':wire,'arrival_cycle':at,'capture_cycle':capture}

class FreshnessTests(unittest.TestCase):
    def test_replacement_keeps_prior_pending_and_newest_order(self):
        e=[evt(0,b'abc',0,0),evt(1,b'def',0,20),evt(2,b'ghi',0,30)]
        r=simulate(e,1000,'fresh',1024,100,1000,1000)
        self.assertEqual([x['id'] for x in r['completed']],[0,2])
        self.assertEqual([(x['id'],x['reason']) for x in r['dropped']],[(1,'superseded_waiting')])
    def test_new_sof_cannot_abort_incomplete_active_frame(self):
        e=[evt(0,b'abcdefghij',0,0),evt(1,b'xyz',0,10),evt(0,b'abcdefghij',1,20)]
        r=simulate(e,1000,'fresh',1024,100,1000,1000)
        self.assertEqual([x['id'] for x in r['completed']],[0])
        self.assertEqual([(x['id'],x['reason']) for x in r['dropped']],[(1,'active_in_progress')])
    def test_truncated_frame_times_out_without_commit(self):
        e=[evt(0,b'abcdefghij',0,0)]
        r=simulate(e,1000,'fresh',1024,100,1000,100)
        self.assertEqual(r['completed'],[])
        self.assertEqual(r['dropped'][0]['reason'],'receive_timeout')
    def test_out_of_order_packet_is_rejected_without_commit(self):
        e=[evt(0,b'abcdefghijklmno',0,0),evt(0,b'abcdefghijklmno',2,20),evt(0,b'abcdefghijklmno',1,40)]
        r=simulate(e,1000,'fresh',1024,100,1000,1000)
        self.assertEqual(r['completed'],[])
        self.assertEqual(r['dropped'][0]['reason'],'receiver_rejected')
    def test_overflow_discards_frame_not_prior_pending(self):
        e=[evt(0,b'abc',0,0),evt(1,b'abcdefghij',0,20),evt(1,b'abcdefghij',1,30)]
        r=simulate(e,50,'fresh',1024,1000,10000,10000)
        self.assertEqual([x['id'] for x in r['completed']],[0])
        self.assertEqual(r['dropped'][0]['reason'],'queue_full')
        self.assertLessEqual(r['max_staged_bytes'],50)
    def test_overflow_of_active_frame_never_commits_partial(self):
        e=[evt(0,b'abcdefghij',0,0),evt(0,b'abcdefghij',1,1)]
        r=simulate(e,50,'fresh',1024000,1000,100000,100000)
        self.assertEqual(r['completed'],[])
        self.assertEqual(r['dropped'][0]['reason'],'queue_full')
        self.assertLessEqual(r['max_staged_bytes'],50)
    def test_stale_waiting_frame_is_not_begun(self):
        e=[evt(0,b'abc',0,0),evt(1,b'xyz',0,20)]
        r=simulate(e,1000,'fresh',1024,1000,100,10000)
        self.assertEqual([x['id'] for x in r['completed']],[0])
        self.assertEqual(r['dropped'][0]['reason'],'begin_deadline')

if __name__=='__main__':unittest.main()
