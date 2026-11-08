import copy, json, tempfile, unittest
from pathlib import Path
from types import SimpleNamespace
import lab_controller as c

ELF='a'*64
NOW=1000000000

def session():return {'event':'session','profile':'dy71-sequence-v3','sequence_count':12,'session':1,'source':[c.LOCAL,50000],'destination':[c.RECEIVER,5535],'started_unix_us':NOW,'initial_wait_seconds':600}

def ready():
    g=c.Gate(ELF);g.identify('diag: USB_D24 p=elf sdk_elf_sha256='+ELF);g.ack('log: MBLAB1 nonce=1234567890abcdef action=HOST33 result=OK','1234567890abcdef','HOST33','OK');return g

class GateTests(unittest.TestCase):
    def reject(self,g=None,row=None,**kw):
        sent=[];values=dict(row=row or session(),started_us=NOW,now_us=NOW,process_live=True,prerequisites=True,writer=sent.append);values.update(kw)
        with self.assertRaises(c.Refused):(g or ready()).arm(**values)
        self.assertEqual(sent,[])
    def test_valid_one_arm(self):
        g=ready();sent=[];g.arm(session(),NOW,NOW,True,True,sent.append);self.assertEqual(sent,[b'@']);self.reject(g)
    def test_dead_process(self):self.reject(process_live=False)
    def test_expired_sender(self):self.reject(now_us=NOW+601000000)
    def test_late_session(self):
        r=session();r['started_unix_us']=NOW-2000000;self.reject(row=r)
    def test_insufficient_wait(self):
        r=session();r['initial_wait_seconds']=20;self.reject(row=r)
    def test_elf_mismatch(self):
        g=c.Gate(ELF)
        with self.assertRaises(c.Refused):g.identify('p=elf sdk_elf_sha256='+'b'*64)
        self.reject(g)
    def test_serial_mismatch(self):
        with self.assertRaises(c.Refused):c.Gate(ELF,'WRONG')
    def test_bad_ack_no_arm(self):
        g=c.Gate(ELF);g.identify('p=elf sdk_elf_sha256='+ELF)
        with self.assertRaises(c.Refused):g.ack('MBLAB1 nonce=1234567890abcdef action=HOST33 result=BUSY','1234567890abcdef','HOST33','OK')
        self.reject(g)
    def test_foreign_nonce_ignored(self):
        g=c.Gate(ELF);self.assertFalse(g.ack('MBLAB1 nonce=aaaaaaaaaaaaaaaa action=HOST33 result=OK','1234567890abcdef','HOST33','OK'));self.reject(g)
    def test_bad_action_no_arm(self):
        g=c.Gate(ELF)
        with self.assertRaises(c.Refused):g.ack('MBLAB1 nonce=1234567890abcdef action=REBOOT result=OK','1234567890abcdef','HOST33','OK')
        self.reject(g)
    def test_wrong_destination_count_source_no_arm(self):
        for key,value in [('destination',[c.RECEIVER,5533]),('sequence_count',3),('source',['192.168.0.47',9999]),('session',0),('profile','JPEG')]:
            r=session();r[key]=value;self.reject(row=r)
    def test_missing_prerequisites(self):self.reject(prerequisites=False)
    def test_identity_missing(self):self.reject(c.Gate(ELF))

class MarkerTests(unittest.TestCase):
    def test_live_fresh_markers_required(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);program={'schema':'moonbub-program-receipt-v1','created_unix_us':NOW,'verified':True,'device_serial':c.SERIAL,'fpga_sha256':'b'*64};camera={'schema':'moonbub-camera-ready-v1','created_unix_us':NOW,'pid':123,'full_panel_verified':True,'coverage_until_unix_us':NOW+181000000}
            a=SimpleNamespace(program_receipt=p/'program.json',camera_ready=p/'camera.json',expected_fpga_sha256='b'*64,run_timeout=180,prereq_max_age=120)
            a.program_receipt.write_text(json.dumps(program));a.camera_ready.write_text(json.dumps(camera))
            self.assertTrue(c.prerequisites(a,NOW,lambda pid:pid==123))
            with self.assertRaises(c.Refused):c.prerequisites(a,NOW,lambda pid:False)
            with self.assertRaises(c.Refused):c.prerequisites(a,NOW+121000000,lambda pid:True)
            camera['coverage_until_unix_us']=NOW+179000000;a.camera_ready.write_text(json.dumps(camera))
            with self.assertRaises(c.Refused):c.prerequisites(a,NOW,lambda pid:True)
    def test_pin_mismatch(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x';p.write_text('source')
            with self.assertRaises(c.Refused):c.pinned(p,'0'*64)

if __name__=='__main__':unittest.main()
