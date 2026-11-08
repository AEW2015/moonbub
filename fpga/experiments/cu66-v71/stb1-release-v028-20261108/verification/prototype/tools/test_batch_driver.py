import random,struct,unittest,zlib
from batch_driver_oracle import BatchDriver,Rejected
class Bus:
 def __init__(self):self.data=bytearray();self.queue=[];self.ops=[];self.ticket=0;self.flags=0;self.abi=0x30000;self.dead=False;self.bad_crc=False;self.publish_busy=False;self.reject=False;self.sealed=False;self.native_faults=0
 def begin_packet(self,g,n,crc):
  if hasattr(self,'g') and g<=self.g:raise Rejected('generation must increase')
  self.g=g;self.n=n;self.expected=crc;self.data=bytearray();self.queue=[];self.sealed=False
 def write_words(self,a,words):
  self.ops.append((a,list(words)))
  if a==0x720:
   lo,hi,off,n,t=words
   if (lo|(hi<<32))!=self.g or off!=len(self.data) or n>1024 or t<=self.ticket:raise Rejected('model descriptor error')
   self.off=off;self.count=n;self.ticket=t
  elif a==0xc00:
   wire=b''.join(struct.pack('<I',w)for w in words);assert len(wire)==(self.count+3)//4*4
   self.queue=[wire[i:i+4]for i in range(0,self.count,4)]
 def read_words(self,a,n):
  if a==0:return[0x44593731,self.abi,0x3f]
  if a==0x700:return[0x53544231,0x10000]
  if a==0x114:return[self.g&0xffffffff,self.g>>32]
  if a==0x718:return[self.ticket]
  if a==0x104:return[len(self.data),self.n,zlib.crc32(self.data),self.native_faults]
  if self.reject:return[1,0,0,0,self.ticket,1][:n]
  if self.queue or self.dead:
   if self.queue and not self.dead:self.data.extend(self.queue.pop(0)[:self.count-len(self.data)+self.off])
   return[2,0,123 if self.publish_busy else 0,0,self.ticket,0][:n]
  return[4,256,len(self.data),zlib.crc32(self.data)^(1 if self.bad_crc and self.data else 0),self.ticket,0][:n]
 def seal_packet(self,g,c):
  if len(self.data)!=self.n or zlib.crc32(self.data)!=c:raise Rejected('seal mismatch')
  self.sealed=True
class DriverTests(unittest.TestCase):
 def test_seeded_lengths_and_partial_tails(self):
  rng=random.Random(20261108)
  for n in [1,2,3,4,1023,1024,1025,4099,49152]:
   packet=bytes(rng.randrange(256)for _ in range(n));b=Bus();d=BatchDriver(b,max_polls=258);r=d.stage(packet,2**40+5)
   self.assertEqual(b.data,packet);self.assertTrue(b.sealed);self.assertEqual(r['descriptors'],(n+1023)//1024)
   self.assertEqual(len(b.ops),2*((n+1023)//1024));self.assertFalse(r['whole_run_retry'])
 def test_multiple_frames_keep_monotonic_tickets(self):
  b=Bus();d=BatchDriver(b)
  for g,n in enumerate([15,1027,4096],1):
   packet=bytes((i*g)%256 for i in range(n));d.stage(packet,g);self.assertEqual(b.data,packet);self.assertTrue(b.sealed)
  self.assertEqual(d.ticket,7)
 def test_rejects_old_ABI(self):
  b=Bus();b.abi=0x20000
  with self.assertRaises(Rejected):BatchDriver(b).stage(b'a',1)
  self.assertFalse(b.ops)
 def test_bounded_wait_no_retries(self):
  b=Bus();b.dead=True
  with self.assertRaises(Rejected):BatchDriver(b,max_polls=3).stage(b'abcd',1)
  self.assertFalse(b.sealed)
 def test_crc_mismatch(self):
  b=Bus();b.bad_crc=True
  with self.assertRaises(Rejected):BatchDriver(b).stage(b'abcd',1)
  self.assertFalse(b.sealed)
 def test_busy_first_flags_ignore_later_published_fields(self):
  b=Bus();b.publish_busy=True;BatchDriver(b).stage(b'abcd',1);self.assertTrue(b.sealed)
 def test_fault_stops_before_any_transfer(self):
  b=Bus();b.reject=True
  with self.assertRaises(Rejected):BatchDriver(b).stage(b'abcd',1)
  self.assertFalse(b.ops)
 def test_actual_sequential_read_completion_between_beats(self):
  class SequentialBus(Bus):
   crossed=False
   def read_words(self,a,n):
    if a==0x708 and n==6 and self.queue:
     # First beat sees busy. Native commits before the subsequent data beats.
     while self.queue:self.data.extend(self.queue.pop(0)[:self.count-len(self.data)+self.off])
     self.crossed=True
     return[2,256,len(self.data),zlib.crc32(self.data),self.ticket,0]
    return super().read_words(a,n)
  b=SequentialBus();BatchDriver(b).stage(b'abc',9);self.assertTrue(b.crossed);self.assertTrue(b.sealed)
 def test_confirmed_generation_change_refuses(self):
  class ChangedBus(Bus):
   def read_words(self,a,n):return [0,0] if a==0x114 else super().read_words(a,n)
  b=ChangedBus()
  with self.assertRaises(Rejected):BatchDriver(b).stage(b'abc',9)
  self.assertFalse(b.sealed)
 def test_native_stage_fault_prevents_seal(self):
  b=Bus();b.native_faults=1
  with self.assertRaises(Rejected):BatchDriver(b).stage(b'abc',9)
  self.assertFalse(b.sealed)
if __name__=='__main__':unittest.main()
