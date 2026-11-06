"""Focused fail-closed tests; synthetic inputs, no Vivado or hardware access."""
from pathlib import Path
import importlib.util,json,struct,tempfile,unittest,tkinter
spec=importlib.util.spec_from_file_location('image_dy71_candidate',Path(__file__).with_name('image_dy71_candidate.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Gates(unittest.TestCase):
 def test_timing_global(self):
  def report(a,b,c):return f'Design State : Fully Routed\n {a} 0.000 0 100 {b} 0.000 0 100 {c} 0.000 0 100\n'
  self.assertEqual(m.timing_metrics(report('.001','.002','.003'))['whs_ns'],.002)
  for args in [('-0.001','.1','.1'),('0','.1','.1'),('.1','-.1','.1'),('.1','.1','0')]:
   with self.assertRaises(ValueError):m.timing_metrics(report(*args))
  with self.assertRaises(ValueError):m.timing_metrics(report('.1','.1','.1').replace('Fully Routed','Synthesized'))
  with self.assertRaises(ValueError):m.timing_metrics(report('.1','.1','.1').replace('0 100','1 100',1))
 def test_routes(self):
  text='# of routable nets.... : 10 :\n# of fully routed nets.... : 10 :\n# of nets with routing errors.... : 0 :\n'
  self.assertEqual(m.route_metrics(text)['fully_routed'],10)
  for bad in[text.replace('fully routed nets.... : 10','fully routed nets.... : 9'),text.replace('errors.... : 0','errors.... : 1'),'unrecognized']:
   with self.assertRaises(ValueError):m.route_metrics(bad)
 def test_native_scripts_readonly_or_one_write(self):
  audit=m.native_script(Path('C:/fixture/build'),Path('C:/fixture/audit'),False)
  emit=m.native_script(Path('C:/fixture/build'),Path('C:/fixture/image'),True)
  self.assertNotIn('write_bitstream',audit);self.assertEqual(emit.count('write_bitstream'),1)
  for text in[audit,emit]:
   self.assertTrue(tkinter.Tcl().call('info','complete',text))
   for forbidden in['open_hw','program_hw','write_cfgmem','write_checkpoint','set_false_path','create_clock','route_design']:
    self.assertNotIn(forbidden,text)
   self.assertIn('report_drc -no_waivers',text);self.assertIn('get_drc_violations',text)
 def bit(self,uid=m.IDENTITY,usr=m.IDENTITY,idcode=0x03631093,part='7a100tcsg324'):
  def field(k,v):return k+len(v).to_bytes(2,'big')+v
  words=[0xaa995566,0x20000000,0x3001a001,usr,0x30018001,idcode,0x30004000,0x50000001,0]
  payload=struct.pack('>'+str(len(words))+'I',*words)
  return b'\0\x09'+bytes.fromhex('0ff00ff00ff00ff000')+b'\0\x01'+field(b'a',f'moonshine_top_dy71;COMPRESS=TRUE;UserID={uid:08X};Version=2025.2\0'.encode())+field(b'b',(part+'\0').encode())+field(b'c',b'2026/11/06\0')+field(b'd',b'00:00:00\0')+b'e'+len(payload).to_bytes(4,'big')+payload
 def test_bit_identity(self):
  with tempfile.TemporaryDirectory(prefix='dy71-image-gates-')as tmp:
   p=Path(tmp)/'fixture.bit';p.write_bytes(self.bit());self.assertEqual(m.parse_bit(p)['USR_ACCESS_hex'],'44593731')
   for kwargs in[dict(uid=1),dict(usr=1),dict(idcode=1),dict(part='7a200tfbg484')]:
    p.write_bytes(self.bit(**kwargs))
    with self.assertRaises(ValueError):m.parse_bit(p)
   p.write_bytes(self.bit()[:-1])
   with self.assertRaises(ValueError):m.parse_bit(p)
 def test_manual_review_must_be_signed_and_exact(self):
  with tempfile.TemporaryDirectory(prefix='dy71-review-gates-')as tmp:
   p=Path(tmp)/'review.json';p.write_text(json.dumps(dict(schema='DY71_FINAL_IMAGE_REVIEW_V1',reviewer=dict(identity='UNSIGNED',role='root-integration',signed_utc=None))))
   with self.assertRaises(ValueError):m.root_review(p,m.sha(p),{},Path(tmp),{})
   with self.assertRaises(ValueError):m.root_review(p,'0'*64,{},Path(tmp),{})
if __name__=='__main__':unittest.main(verbosity=2)
