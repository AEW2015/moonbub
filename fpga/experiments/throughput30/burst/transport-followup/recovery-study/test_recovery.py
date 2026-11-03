#!/usr/bin/env python3
import os
from pathlib import Path
import unittest
from study import xor_packets,strict_receiver,staged_receiver,window_receiver,window_presof_receiver,simulate_link,rust_compare
from moonshine.protocol import packets

DATA=bytes(range(256))*12

def events(drop=(), reorder=None, parity=False):
 seq=list(packets(DATA,0,0));items=[]
 for i,packet in enumerate(seq):
  if i not in drop:
   items.append({'at':(i+1)*1000,'fid':0,'kind':'data','index':i,'payload':packet,
                 'capture':0,'count':len(seq),'length':len(DATA),'jpeg':DATA})
 if reorder is not None:
  items[reorder],items[reorder+1]=items[reorder+1],items[reorder]
  for i,item in enumerate(items):item['at']=(i+1)*1000
 if parity:
  items.append({'at':10000,'fid':0,'kind':'parity','index':0,'payload':xor_packets(seq),
                'capture':0,'count':len(seq),'length':len(DATA),'jpeg':DATA})
 return items

class RecoveryTests(unittest.TestCase):
 def test_clean_actual_receiver(self):
  result,out,ev=strict_receiver(events(),1,100)
  self.assertEqual(result['complete'],1);self.assertEqual(out[-1],'done')
  if os.environ.get('REPLAY_EXE'):
   self.assertEqual(rust_compare(Path(os.environ['REPLAY_EXE']),out,ev)['mismatch_count'],0)
 def test_out_of_order_strict_fails_and_full_frame_stage_recovers(self):
  e=events(reorder=1)
  self.assertEqual(strict_receiver(e,1,100)[0]['complete'],0)
  result,out,ev=staged_receiver(e,1,100,False)
  self.assertEqual(result['complete'],1);self.assertGreater(result['max_buffered_bytes'],len(DATA))
  if os.environ.get('REPLAY_EXE'):
   self.assertEqual(rust_compare(Path(os.environ['REPLAY_EXE']),out,ev)['mismatch_count'],0)
 def test_bounded_window_repairs_one_adjacent_reordering(self):
  e=events(reorder=1)
  result,out,ev=window_receiver(e,1,100,slots=4,gap_ms=2)
  self.assertEqual(result['complete'],1);self.assertGreater(result['max_buffered_datagram_bytes'],0)
  self.assertLessEqual(result['max_buffered_datagram_bytes'],4*(1024+40))
  if os.environ.get('REPLAY_EXE'):
   self.assertEqual(rust_compare(Path(os.environ['REPLAY_EXE']),out,ev)['mismatch_count'],0)
 def test_bounded_window_cannot_repair_missing_sof(self):
  r=window_receiver(events(drop=(0,)),1,100)[0]
  self.assertEqual(r['complete'],0);self.assertEqual(r['frame_ids_seen_without_active_receiver'],1)
 def test_pre_sof_reordering_is_not_supported_by_window(self):
  e=events(reorder=0)
  result,out,ev=window_receiver(e,1,100,slots=4,gap_ms=2)
  self.assertEqual(result['complete'],0);self.assertEqual(result['frame_ids_seen_without_active_receiver'],1)
  self.assertEqual(staged_receiver(e,1,100,False)[0]['complete'],1)
  if os.environ.get('REPLAY_EXE'):
   self.assertEqual(rust_compare(Path(os.environ['REPLAY_EXE']),out,ev)['mismatch_count'],0)
 def test_presof_slot_repairs_prestart_reordering_but_not_sof_loss(self):
  e=events(reorder=0)
  result,out,ev=window_presof_receiver(e,1,100)
  self.assertEqual(result['complete'],1);self.assertEqual(result['pre_sof_accepted'],1)
  self.assertLessEqual(result['max_buffered_datagram_bytes'],5*(1024+40))
  if os.environ.get('REPLAY_EXE'):
   self.assertEqual(rust_compare(Path(os.environ['REPLAY_EXE']),out,ev)['mismatch_count'],0)
  self.assertEqual(window_presof_receiver(events(drop=(0,)),1,100)[0]['complete'],0)
 def test_presof_expiration_discards_stale_fragment(self):
  e=events(reorder=0)
  for item in e:
   if item['index']==0:item['at']=300000
   elif item['index']>1:item['at']=300000+item['index']
  result,_,_=window_presof_receiver(e,1,100)
  self.assertEqual(result['complete'],0);self.assertEqual(result['pre_sof_expired'],1)
 def test_gap_timeout_sends_real_receiver_abort(self):
  e=events(reorder=1)
  for item in e:
   if item['index'] in (1,3):item['at']=300000+item['index']
  result,out,ev=window_receiver(e,1,100,slots=4,gap_ms=2)
  self.assertEqual(result['complete'],0);self.assertEqual(result['gap_timeouts'],1)
  self.assertIn('abort',out)
  if os.environ.get('REPLAY_EXE'):
   self.assertEqual(rust_compare(Path(os.environ['REPLAY_EXE']),out,ev)['mismatch_count'],0)
 def test_out_of_window_aborts(self):
  src=bytes(range(256))*32;seq=list(packets(src,0,0))
  e=[{'at':(i+1)*1000,'fid':0,'kind':'data','index':idx,'payload':seq[idx],
      'capture':0,'count':len(seq),'length':len(src),'jpeg':src} for i,idx in enumerate((0,6))]
  result,out,ev=window_receiver(e,1,100,slots=4,gap_ms=2)
  self.assertEqual(result['window_overflows'],1);self.assertIn('abort',out)
  if os.environ.get('REPLAY_EXE'):
   self.assertEqual(rust_compare(Path(os.environ['REPLAY_EXE']),out,ev)['mismatch_count'],0)
 def test_fec_repairs_missing_start_packet_and_real_receiver_accepts(self):
  e=events(drop=(0,),parity=True)
  result,out,ev=staged_receiver(e,1,100,True)
  self.assertEqual(result['complete'],1);self.assertEqual(result['packets_reconstructed'],1)
  if os.environ.get('REPLAY_EXE'):
   self.assertEqual(rust_compare(Path(os.environ['REPLAY_EXE']),out,ev)['mismatch_count'],0)
 def test_two_losses_in_one_group_are_not_recovered(self):
  result,_,_=staged_receiver(events(drop=(0,1),parity=True),1,100,True)
  self.assertEqual(result['complete'],0);self.assertEqual(result['packets_reconstructed'],0)
 def test_timeout_drops_late_packets(self):
  e=events()
  for x in e:x['at']=200000
  self.assertEqual(strict_receiver(e,1,1)[0]['complete'],0)
  self.assertEqual(staged_receiver(e,1,1,False)[0]['complete'],0)
 def test_corrupt_payload_never_produces_valid_frame(self):
  e=events();p=bytearray(e[1]['payload']);p[-1]^=1;e[1]['payload']=bytes(p)
  strict,out,ev=strict_receiver(e,1,100);self.assertEqual(strict['complete'],0)
  if os.environ.get('REPLAY_EXE'):
   self.assertEqual(rust_compare(Path(os.environ['REPLAY_EXE']),out,ev)['mismatch_count'],0)
  with self.assertRaises(AssertionError):staged_receiver(e,1,100,False)
 def test_sender_slot_replaces_under_overload(self):
  _,s=simulate_link([DATA]*10,30,100_000,1,'none',False,0)
  self.assertGreater(s['sender_replaced'],0);self.assertLessEqual(s['sender_wait_highwater_bytes'],len(DATA))
 def test_payload_xor_roundtrip_unequal_lengths(self):
  arr=[b'12345',b'012',b'hello'];p=xor_packets(arr)
  recovered=xor_packets([p,arr[0],arr[2]])
  self.assertEqual(recovered[:3],arr[1]);self.assertEqual(recovered[3:],b'\0\0')

if __name__=='__main__':unittest.main()
