import unittest
import zlib
from model import Model

class TaggedProtocol(unittest.TestCase):
 def setUp(self): self.m=Model(7, 8)
 def call(self, rid, op, **kwargs): return self.m.request(7,rid,op,**kwargs)
 def begin(self,rid,content=b'ab'):
  ack=self.call(rid,'BEGIN',frame_id=rid,length=len(content),crc=zlib.crc32(content))
  self.assertEqual(ack.outcome,'BEGIN_OK');return ack.token
 def test_stale_after_reuse_cannot_touch_new_receive(self):
  old=self.begin(1);self.assertEqual(self.call(2,'ABORT',token=old).outcome,'ABORT_OK')
  new=self.begin(3);self.assertEqual(new.bank,old.bank);self.assertNotEqual(new.generation,old.generation)
  for rid,op,extra in [(4,'DATA',dict(offset=0,payload=b'ab')),(5,'COMMIT',{}),(6,'ABORT',{})]:
   self.assertEqual(self.call(rid,op,token=old,**extra).outcome,'STALE_TOKEN')
  self.assertEqual(self.call(7,'DATA',token=new,offset=0,payload=b'ab').count,2)
  self.assertEqual(self.call(8,'COMMIT',token=new).outcome,'COMMIT_OK')
 def test_lost_ack_retry_is_identical_and_has_no_side_effect(self):
  first=self.call(1,'BEGIN',frame_id=42,length=2,crc=zlib.crc32(b'ab'))
  self.assertEqual(first,self.call(1,'BEGIN',frame_id=42,length=2,crc=zlib.crc32(b'ab')))
  t=first.token
  a=self.call(2,'DATA',token=t,offset=0,payload=b'ab')
  self.assertEqual(a,self.call(2,'DATA',token=t,offset=0,payload=b'ab'))
  self.assertEqual(self.call(2,'DATA',token=t,offset=0,payload=b'xx').outcome,'REQUEST_ID_CONFLICT')
  c=self.call(3,'COMMIT',token=t);self.assertEqual(c,self.call(3,'COMMIT',token=t))
  self.assertEqual(bytes(self.m.banks[t.bank].data),b'ab')
 def test_abort_ack_duplicate_after_reuse_preserves_new_bank(self):
  t=self.begin(1);a=self.call(2,'ABORT',token=t);new=self.begin(3)
  self.assertEqual(a,self.call(2,'ABORT',token=t))
  self.assertEqual(self.m.banks[new.bank].state,'RECEIVING')
 def test_reset_epoch_invalidates_tokens_and_ack_namespace(self):
  t=self.begin(1);self.m.reset(8)
  self.assertEqual(self.m.request(7,2,'ABORT',token=t).outcome,'STALE_EPOCH')
  self.assertEqual(self.m.request(8,2,'ABORT',token=t).outcome,'STALE_TOKEN')
  self.assertEqual(self.m.request(8,1,'BEGIN',frame_id=1,length=1,crc=zlib.crc32(b'x')).outcome,'BEGIN_OK')
  with self.assertRaises(ValueError):self.m.reset(8)
 def test_two_banks_abort_isolated_and_release(self):
  a=self.begin(1,b'a');b=self.begin(2,b'b')
  self.call(3,'DATA',token=a,offset=0,payload=b'a');self.call(4,'COMMIT',token=a)
  self.call(5,'ABORT',token=b);self.assertEqual(self.m.banks[a.bank].state,'READY')
  self.assertEqual(self.call(6,'ABORT',token=a).outcome,'WRONG_STATE')
  self.assertEqual(self.call(7,'RELEASE',token=a).outcome,'RELEASE_OK')
 def test_bad_data_and_crc_reject_without_publication(self):
  t=self.begin(1);self.assertEqual(self.call(2,'DATA',token=t,offset=1,payload=b'x').outcome,'BAD_DATA')
  self.assertEqual(self.call(3,'DATA',token=t,offset=0,payload=b'xx').outcome,'DATA_OK')
  self.assertEqual(self.call(4,'COMMIT',token=t).outcome,'COMMIT_REJECTED')
  self.assertEqual(self.m.banks[t.bank].state,'FREE')

if __name__=='__main__':unittest.main(verbosity=2)
