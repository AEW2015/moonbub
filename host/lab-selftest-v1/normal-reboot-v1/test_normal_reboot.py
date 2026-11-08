from pathlib import Path
import importlib.util,json,sys,tempfile,unittest
from unittest import mock
import normal_reboot as n
d=n.library()
spec=importlib.util.spec_from_file_location('existing_dfu_fake',Path(d.__file__).with_name('test_dfu_vendor.py'));fixtures=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixtures)
class Fake(fixtures.Fake):
 def __init__(self):super().__init__();self.reboots=0;self.answer=0;self.reboot_error=None;self.closed=0
 def control(self,request,value,length,out=False):
  if request==1:
   assert(value,length,out)==(1,0,True);self.reboots+=1
   if self.reboot_error:raise self.reboot_error
   return self.answer
  return super().control(request,value,length,out)
 def close(self):self.closed+=1
class Tests(unittest.TestCase):
 def setUp(self):
  (n.P/'test-tmp').mkdir(exist_ok=True);self.tmp=tempfile.TemporaryDirectory(dir=n.P/'test-tmp');self.p=Path(self.tmp.name);self.claims=self.p/'claims';self.f=Fake();current=self.p/'old.bin';current.write_bytes(fixtures.application());self.new=self.p/'new.bin';self.new.write_bytes(fixtures.application(3));j=[];client=d.Client(self.f,journal=j.append);d.backup(client,current,n.sha(current),self.p/'backup');self.plan=self.p/'plan.json';self.plan.write_text(json.dumps(d.make_plan(self.p/'backup/backup.json',self.new,n.sha(self.new))));j=[{'event':'operation_start','action':'apply','sync':True}];client.journal=j.append;receipt=d.apply(client,self.plan,self.new,True);self.receipt=self.p/'receipt.json';self.receipt.write_text(json.dumps(receipt));self.journal=self.p/'apply.jsonl';self.journal.write_text('\n'.join(json.dumps(x)for x in j)+'\n');self.before=list(self.f.mutations)
 def tearDown(self):self.tmp.cleanup()
 def validated(self):return n.validate(d,self.receipt,n.sha(self.receipt),self.plan,n.sha(self.plan),self.new,n.sha(self.new),self.journal,n.sha(self.journal),'a'*64)
 def run_send(self,**kw):return n.run(d,self.validated(),self.receipt,True,lambda:self.f,lambda e:None,claim_root=self.claims,**kw)
 def test_default_dryrun_never_opens_USB(self):
  factory=mock.Mock(side_effect=AssertionError('USB forbidden'));r=n.run(d,self.validated(),self.receipt,backend_factory=factory);self.assertEqual(r['result'],'DRY_RUN_NO_USB');factory.assert_not_called();self.assertEqual(self.f.reboots,0)
 def test_exact_single_normal_request_ack_is_not_reset(self):
  r=self.run_send();self.assertEqual(r['result'],'SENT_UNCONFIRMED');self.assertFalse(r['reset_verified']);self.assertFalse(r['post_reboot_ELF_verified']);self.assertEqual(self.f.reboots,1);self.assertEqual(self.f.mutations,self.before);self.assertEqual(self.f.closed,1)
 def test_same_receipt_consumed_even_with_new_invocation(self):
  self.run_send()
  with self.assertRaises(n.Refused):self.run_send()
  self.assertEqual(self.f.reboots,1)
 def test_timeout_ambiguous_never_retries(self):
  self.f.reboot_error=TimeoutError('lost ACK');r=self.run_send();self.assertEqual(r['result'],'ATTEMPT_UNCONFIRMED');self.assertEqual(self.f.reboots,1)
  with self.assertRaises(n.Refused):self.run_send()
  self.assertEqual(self.f.reboots,1)
 def test_nonzero_control_result_not_success(self):
  self.f.answer=1;self.assertEqual(self.run_send()['result'],'ATTEMPT_UNCONFIRMED');self.assertEqual(self.f.reboots,1)
 def test_full_factory_changed_outside_prefix_prevents_send(self):
  self.f.factory[-1]^=1
  with self.assertRaises(n.Refused):self.run_send()
  self.assertEqual(self.f.reboots,0)
 def test_updater_preservation_changed_prevents_send(self):
  self.f.dfu=b'X'+self.f.dfu[1:]
  with self.assertRaises(n.Refused):self.run_send()
  self.assertEqual(self.f.reboots,0)
 def test_wrong_serial_prevents_send(self):
  self.f.serial=0
  with self.assertRaises(d.Refused):self.run_send()
  self.assertEqual(self.f.reboots,0)
 def test_busy_prevents_send(self):
  self.f.state=(0,0,d.READ,True)
  with self.assertRaises(n.Refused):self.run_send()
  self.assertEqual(self.f.reboots,0)
 def test_apply_error_journal_refused_offline(self):
  self.journal.write_text(self.journal.read_text()+json.dumps({'event':'apply_error'})+'\n')
  with self.assertRaises(n.Refused):self.validated()
 def test_duplicate_terminal_readback_refused(self):
  lines=self.journal.read_text().splitlines();self.journal.write_text('\n'.join(lines+[lines[-1]])+'\n')
  with self.assertRaises(n.Refused):self.validated()
 def test_receipt_missing_preservation_refused(self):
  r=json.loads(self.receipt.read_text());r['dfu_preserved']=False;self.receipt.write_text(json.dumps(r))
  with self.assertRaises(n.Refused):self.validated()
 def test_receipt_duplicate_JSON_key_refused(self):
  self.receipt.write_text('{"schema":"x","schema":"y"}')
  with self.assertRaises(n.Refused):self.validated()
 def test_expected_hash_mismatch_refused(self):
  with self.assertRaises(n.Refused):n.validate(d,self.receipt,'b'*64,self.plan,n.sha(self.plan),self.new,n.sha(self.new),self.journal,n.sha(self.journal),'a'*64)
 def test_changed_evidence_during_live_probe_prevents_send(self):
  v=self.validated();self.plan.write_text(self.plan.read_text()+' ')
  with self.assertRaises(n.Refused):n.run(d,v,self.receipt,True,lambda:self.f,lambda e:None,claim_root=self.claims)
  self.assertEqual(self.f.reboots,0)
 def test_journal_intent_failure_prevents_send_and_claim_stays(self):
  def fail(e):
   if e['event']=='normal_reboot_intent':raise OSError('disk full')
  with self.assertRaises(OSError):n.run(d,self.validated(),self.receipt,True,lambda:self.f,fail,claim_root=self.claims)
  self.assertEqual(self.f.reboots,0);self.assertTrue(n.claim_path(self.validated(),n.sha(self.receipt),self.claims).exists())
 def test_transport_rejects_flash_write_and_DFU_mode(self):
  io=n.ReadOnlyTransport(self.f,lambda:0,10)
  for request,value in[(1,2),(0x50,0)]:
   with self.assertRaises(n.Refused):io.control(request,value,0,True)
  import struct
  bad=struct.pack('<IIBBHI16s',d.MAGIC,1,d.WRITE,8,0,4,bytes(16))
  with self.assertRaises(n.Refused):io.write(bad)
  self.assertEqual(self.f.reboots,0)
 def test_deadline_refuses_without_action(self):
  with self.assertRaises(n.Refused):n.run(d,self.validated(),self.receipt,True,lambda:self.f,lambda e:None,clock=iter([0,200]).__next__,seconds=1,claim_root=self.claims)
  self.assertEqual(self.f.reboots,0)
 def test_copied_identical_receipt_cannot_bypass_once(self):
  self.run_send();copied=self.p/'copied-receipt.json';copied.write_bytes(self.receipt.read_bytes())
  with self.assertRaises(n.Refused):n.run(d,self.validated(),copied,True,lambda:self.f,lambda e:None,claim_root=self.claims)
  self.assertEqual(self.f.reboots,1)
 def test_atomic_concurrent_claim_has_exactly_one_winner(self):
  import concurrent.futures,threading
  barrier=threading.Barrier(2);path=n.claim_path(self.validated(),n.sha(self.receipt),self.claims)
  def worker():
   barrier.wait()
   try:n.reserve_attempt(path,{'stage':'ATTEMPT_RESERVED'});return True
   except n.Refused:return False
  with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:out=list(pool.map(lambda _:worker(),range(2)))
  self.assertEqual(sorted(out),[False,True]);self.assertEqual(json.loads(path.read_text()),{'stage':'ATTEMPT_RESERVED'})
if __name__=='__main__':unittest.main()
