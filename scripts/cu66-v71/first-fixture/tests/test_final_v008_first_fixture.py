"""Synthetic host-only parser/refusal tests. No serial, camera or device access."""
import importlib.util,io,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('first_fixture',Path(__file__).resolve().parents[1]/'final_v008_first_fixture.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def identity(c='1',sha=None,variant=None):
 p={'reset':'reason=1 up_us=100','variant':'name='+(variant or m.VARIANT),'memory':'free=180000 largest=100000 usb_stack=1234','elf':'sdk_elf_sha256='+(sha or m.ELF),'end':'g_after=0 e_after=0 sampled=true'}
 return [f'USB_D24 v=1 c={c} g=0 e=0 f=0 p={k} {v}'for k,v in p.items()]
def cpu():return ['USB_CU66_HUD frame=0 prepare_us=12 read_words=21120 read_crc=358486a6 allocator=[1,2,3,4,5,0]','USB_CU66_HUD frame=1 prepare_us=9 read_words=21120 read_crc=9b082f5c allocator=[1,2,3,4,5,0]','USB_CU66_HUD caught_allocation_failure=true allocator=[1024,0,512,512,3,1] heap_before_negative=170000 heap_before_throw=169000 heap_after_throw=168000 heap_after_drop=170000','USB_CU66_HUD result=Ok([1,2,3,4,5,0]) elapsed_us=100 stack_low=2048 hardware_access=false network_capability=false']
def local():return ['USB_CU71_LOCAL completed_profile=Dy71 success=true','USB_CU71_LOCAL result=completed report=Report { frames: 2, accepted: 2, presented: 2, rejected: 0, underruns: 0, words_written: 42240, words_verified: 42240, elapsed_us: 100, allocator: [1,2,3,4,5,0] } reads=5 writes=5 epoch=Some(1) heap_before=(180000,90000) heap_after=(30000,16000) stack_low=1234 throughput_claim=false','USB_CU71_LOCAL state=completed_held endpoint_retained=true lease_retained=true reconfigure_required=true']
class Tests(unittest.TestCase):
 def test_default_plan_imports_no_serial(self):
  with patch('sys.stdout',new_callable=io.StringIO)as out:self.assertEqual(m.main([]),0)
  self.assertEqual(json.loads(out.getvalue())['commands'],['?','W','Y','?'])
 def test_identity_complete_and_exact(self):self.assertEqual(m.parse_identity(identity())['elf']['sdk_elf_sha256'],m.ELF)
 def test_identity_wrong_hash_refuses(self):
  with self.assertRaises(m.Refusal):m.parse_identity(identity(sha='0'*64))
 def test_identity_no_cross_capture_splice(self):self.assertIsNone(m.parse_identity(identity()[:3]+identity('2')[3:]))
 def test_cpu_real_terminal_shape(self):self.assertEqual(m.parse_cpu(cpu())['stack_high_water_raw'],2048)
 def test_cpu_requires_caught_negative(self):
  with self.assertRaises(m.Refusal):m.parse_cpu([x for x in cpu()if 'caught_'not in x])
 def test_cpu_failure(self):
  with self.assertRaises(m.Refusal):m.parse_cpu(['USB_CU66_HUD result=Err("allocation") elapsed_us=20 stack_low=1024'])
 def test_local_success_requires_held(self):self.assertIsNone(m.parse_local(local()[:-1]));self.assertTrue(m.parse_local(local())['success'])
 def test_local_wrong_counters(self):
  with self.assertRaises(m.Refusal):m.parse_local([x.replace('presented: 2','presented: 1')for x in local()])
 def test_mutated_failure_waits_for_lease_record(self):
  row='USB_CU71_LOCAL result=failed reason=Deadline reads=123 writes=4 epoch=Some(1) heap_before=(1,2) heap_after=(1,2) stack_low=100 recovery=retain_endpoint_and_lease_after_mutation'
  self.assertIsNone(m.parse_local([row]));self.assertFalse(m.parse_local([row,'USB_CU71_LOCAL state=quarantined_held endpoint_retained=true lease_retained=true reconfigure_required=true'])['success'])
 def test_capture_only_allowlist(self):
  class Serial:
   def write(self,b):raise AssertionError('Unapproved write reached transport')
  with tempfile.TemporaryDirectory()as tmp:
   c=m.Capture(Serial(),Path(tmp))
   try:
    with self.assertRaises(m.Refusal):c.send('q')
   finally:c.close()
 def test_capture_reboot_no_retry(self):
  class Serial:
   def read(self,n):return b'USB_D24 v=1 p=boot name=v36\n'
  with tempfile.TemporaryDirectory()as tmp:
   c=m.Capture(Serial(),Path(tmp))
   try:
    with self.assertRaises(m.Refusal):c.read()
   finally:c.close()
 def test_qualification_fail_closed_and_hashes(self):
  with tempfile.TemporaryDirectory()as tmp:
   d=Path(tmp);src=d/'sources.json';src.write_text('{"top":"cu71_system_final_v008"}');elf=d/'app.elf';elf.write_bytes(b'syntheticELF');bit=d/'test.bit';bit.write_bytes(b'syntheticBIT');e=d/'gate.json';e.write_text('{"synthetic_host_test":true}')
   with patch.object(m,'SOURCE',m.digest(src)),patch.object(m,'ELF',m.digest(elf)):
    q={'schema':'MOONBUB_FINAL_V008_FIRST_FIXTURE_QUALIFICATION_V1','overall':'PASS','source_manifest_sha256':m.SOURCE,'bit_sha256':m.digest(bit),'artifacts':[{'path':str(p),'sha256':m.digest(p)}for p in [src,elf,bit,e]],'checks':{k:{'status':'PASS','evidence_sha256':m.digest(e)}for k in m.GATES}};qp=d/'qualification.json';qp.write_text(json.dumps(q));r={'schema':'MOONBUB_FIRST_FIXTURE_OPERATOR_RECEIPT_V1','qualification_manifest_sha256':m.digest(qp),'programmed_bit_sha256':m.digest(bit),'installed_elf_sha256':m.ELF,'profile':{'magic':'44593731','abi':'00010000','capabilities':'0000000f'},'programming_record_sha256':m.digest(e)}
    for k in ('separate_B50_25fps_test_complete','host_senders_stopped','hardware_exclusive','fresh_paired_app_and_fpga_state','camera_coverage_verified','no_held_or_quarantined_lease'):r[k]=True
    rp=d/'receipt.json';rp.write_text(json.dumps(r));m.verify_qualification(qp,rp)
    bit.write_bytes(b'changed')
    with self.assertRaises(m.Refusal):m.verify_qualification(qp,rp)
 def test_execute_without_gates_never_opens(self):
  with self.assertRaises(m.Refusal):m.main(['--execute','--port','FAKE'])
if __name__=='__main__':unittest.main()
