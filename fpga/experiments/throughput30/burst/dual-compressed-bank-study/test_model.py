#!/usr/bin/env python3
import struct,unittest,zlib
import model

class BankTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.events=model.source.assign(model.source.load_events())
 def test_actual_capture_admits_corrupt_intermediate_without_destroying_prior(self):
  one=model.source.simulate(self.events,3397969);two=model.two_bank(self.events)
  self.assertEqual([x['id'] for x in one['presented']],[0,2]);self.assertEqual([x['id'] for x in two['presented']],[0,2])
  self.assertEqual([(x['id'],x['reason']) for x in one['dropped']],[(1,'busy_begin')]);self.assertEqual([(x['id'],x['reason']) for x in two['dropped']],[(1,'recorded_guest_abort')])
  self.assertLess(two['dropped'][0]['cycle'],two['presented'][0]['present_cycle']);self.assertEqual([x['crc32'] for x in two['presented']],['eceeb9c5','1ea3e1d5'])
 def test_over_capacity_rejected(self):
  r=model.two_bank(self.events,bank_bytes=26000);self.assertEqual(r['presented'],[]);self.assertEqual([x['reason'] for x in r['dropped']],['oversized_frame']*3)
 def test_crc_corruption_blocks_commit(self):
  e=[dict(x) for x in self.events];x=next(x for x in e if x['id']==0 and x['type']=='D');body=bytearray(x['body']);body[-1]^=1;x['body']=bytes(body)
  with self.assertRaisesRegex(ValueError,'commit CRC/length'):model.two_bank(e)
 def test_both_banks_occupied_drops_new_begin_and_preserves_order(self):
  # Directed synthetic one-byte payloads; not captured guest data.
  e=[];seq=0
  for fid,start in ((0,0),(1,10000),(2,20000)):
   data=bytes([fid+10]);crc=zlib.crc32(data)
   for kind,at,body in [(b'B',start,struct.pack('>II',1,crc)),(b'D',start+3000,struct.pack('>IH',0,1)+data),(b'C',start+6000,b'')]:
    raw=kind+struct.pack('>II',seq,fid)+body;e.append({'seq':seq,'id':fid,'type':kind.decode(),'at':at,'body':raw});seq+=1
  r=model.two_bank(e,release_cycles=100000)
  self.assertEqual([x['id'] for x in r['presented']],[0,1]);self.assertEqual([(x['id'],x['reason']) for x in r['dropped']],[(2,'no_free_bank')])
 def test_queue_overflow_is_bounded(self):
  r=model.two_bank(self.events,service_us_per_kib=2000)
  self.assertLessEqual(r['event_fifo_highwater_slots'],5);self.assertLessEqual(r['event_fifo_highwater_bytes'],5195)
  self.assertEqual({x['id'] for x in r['presented']}|{x['id'] for x in r['dropped']},{0,1,2})
if __name__=='__main__':unittest.main()
