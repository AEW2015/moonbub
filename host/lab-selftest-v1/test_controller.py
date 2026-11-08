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


class PresenceTests(unittest.TestCase):
    def test_fast_disappearance_is_retained_while_consumer_busy_and_com_changes(self):
        import time
        state={'armed':False,'gone':False}
        def ports():
            if not state['armed']:return ['COM4']
            if not state['gone']:state['gone']=True;return []
            return ['COM9']
        m=c.PresenceMonitor('COM4',ports,.005);m.start();m.mark_command();state['armed']=True
        try:
            # Model ACK wait + old-port close taking longer than the complete USB gap.
            time.sleep(.08)
            self.assertEqual(m.wait_return(.2),'COM9')
            e=m.snapshot()['events'];self.assertEqual([x['event'] for x in e],['initial','command','gone','returned'])
            self.assertLessEqual(e[1]['monotonic_us'],e[2]['monotonic_us']);self.assertLessEqual(e[2]['monotonic_us'],e[3]['monotonic_us'])
        finally:m.stop()
    def test_no_disappearance_no_reboot_acceptance(self):
        state={'changed':False}
        m=c.PresenceMonitor('COM4',lambda:['COM9'] if state['changed'] else ['COM4'],.005);m.start();m.mark_command();state['changed']=True
        try:
            with self.assertRaises(c.Refused):m.wait_return(.04)
            self.assertIsNone(m.snapshot()['return_port'])
        finally:m.stop()
    def test_missing_initial_port_refuses_before_command(self):
        m=c.PresenceMonitor('COM4',lambda:[],.005)
        try:
            with self.assertRaises(c.Refused):m.start()
            self.assertIsNone(m.command_us)
        finally:m.stop()
    def test_multiple_serial_interfaces_refuse(self):
        state={'many':False}
        m=c.PresenceMonitor('COM4',lambda:['COM4','COM9'] if state['many'] else ['COM4'],.005);m.start();m.mark_command();state['many']=True
        try:
            with self.assertRaises(c.Refused):m.wait_return(.2)
        finally:m.stop()

class ReaderLifetimeTests(unittest.TestCase):
    def test_sender_tail_is_drained_before_output_close(self):
        import io
        p=SimpleNamespace(stdout=io.StringIO('{"event":"session"}\n{"event":"complete"}\n'))
        output=io.StringIO();pump=c.SenderPump(p,output);pump.finish()
        self.assertIn('complete',output.getvalue());self.assertTrue(p.stdout.closed);self.assertFalse(pump.thread.is_alive())
    def test_late_sender_write_is_blocked_on_join_failure(self):
        import io,threading
        release=threading.Event()
        class Pipe:
            def __iter__(self):
                release.wait();yield 'late tail\n'
            def close(self):pass
        output=io.StringIO();pump=c.SenderPump(SimpleNamespace(stdout=Pipe()),output)
        with self.assertRaises(c.Refused):pump.finish(timeout=.01)
        output.close();release.set();pump.thread.join(timeout=1)
        self.assertFalse(pump.thread.is_alive());self.assertIsNone(pump.error)
    def test_serial_raw_not_closed_if_reader_still_live(self):
        import io
        s=c.SerialLog.__new__(c.SerialLog);s.raw=io.BytesIO();s.port=SimpleNamespace(cancel_read=lambda:None,close=lambda:None);s.thread=SimpleNamespace(join=lambda timeout:None,is_alive=lambda:True)
        with self.assertRaises(c.Refused):s.close()
        self.assertFalse(s.raw.closed);s.raw.close()


class OpenReadinessTests(unittest.TestCase):
    def test_enumerated_but_unopenable_then_ready_new_com(self):
        calls=[];attempts=[];now=[0.0]
        def factory(port,output):
            calls.append(port)
            if len(calls)==1:raise c.PortOpenPending('FileNotFoundError: COM not ready')
            return 'opened-log'
        def ports():return ['COM3'] if not calls else ['COM9']
        with tempfile.TemporaryDirectory() as d:
            result=c.open_returned_serial(Path(d),1.0,attempts,ports,factory,lambda:now[0],lambda dt:now.__setitem__(0,now[0]+dt))
        self.assertEqual(result,'opened-log');self.assertEqual(calls,['COM3','COM9'])
        self.assertEqual([x['result'] for x in attempts],['temporarily_unopenable','opened'])
    def test_repeated_open_failure_expires_without_new_reset(self):
        calls=[];attempts=[];now=[0.0]
        def factory(port,output):calls.append(port);raise c.PortOpenPending('FileNotFoundError')
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(c.Refused):c.open_returned_serial(Path(d),.25,attempts,lambda:['COM3'],factory,lambda:now[0],lambda dt:now.__setitem__(0,now[0]+dt))
        self.assertEqual(len(calls),3);self.assertTrue(all(x['result']=='temporarily_unopenable' for x in attempts));self.assertGreaterEqual(now[0],.25)
    def test_missing_port_is_reenumerated_each_attempt(self):
        calls=[];now=[0.0];attempts=[]
        def ports():calls.append(1);return [] if len(calls)==1 else ['COM7']
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(c.open_returned_serial(Path(d),1,attempts,ports,lambda port,out:port,lambda:now[0],lambda dt:now.__setitem__(0,now[0]+dt)),'COM7')
        self.assertEqual(attempts[0]['result'],'not_enumerated')
    def test_open_failure_closes_partial_port_without_reserving_raw(self):
        import sys
        from unittest.mock import patch
        class Port:
            closed=False
            def open(self):raise FileNotFoundError('enumerated COM not yet ready')
            def close(self):self.closed=True
        port=Port()
        with tempfile.TemporaryDirectory() as d,patch.dict(sys.modules,{'serial':SimpleNamespace(Serial=lambda **kw:port)}):
            output=Path(d)
            with self.assertRaises(c.PortOpenPending):c.SerialLog('COM3',output)
            self.assertFalse((output/'serial.raw').exists());self.assertTrue(port.closed);self.assertFalse(port.dtr);self.assertFalse(port.rts)
    def test_log_file_failure_closes_open_port_and_preserves_file(self):
        import sys
        from unittest.mock import patch
        class Port:
            closed=False
            def open(self):pass
            def close(self):self.closed=True
        port=Port()
        with tempfile.TemporaryDirectory() as d,patch.dict(sys.modules,{'serial':SimpleNamespace(Serial=lambda **kw:port)}):
            output=Path(d);(output/'serial.raw').write_bytes(b'preserved')
            with self.assertRaises(FileExistsError):c.SerialLog('COM3',output)
            self.assertTrue(port.closed);self.assertEqual((output/'serial.raw').read_bytes(),b'preserved')
    def test_post_open_file_error_is_not_retried(self):
        calls=[];attempts=[]
        def factory(port,output):calls.append(port);raise FileExistsError('evidence exists')
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(FileExistsError):c.open_returned_serial(Path(d),100,attempts,lambda:['COM3'],factory,lambda:0,lambda dt:None)
        self.assertEqual(calls,['COM3'])

if __name__=='__main__':unittest.main()
