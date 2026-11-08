import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest import mock
import dfu_vendor as d


def application(seed=0,size=256):
    b=bytearray((i+seed)%256 for i in range(size));b[0]=0xe9;b[1]=1
    struct.pack_into('<H',b,12,9);struct.pack_into('<I',b,32,0xabcd5432)
    return bytes(b)


def partition_table():
    entries=b''
    for label,kind,subtype,offset,size,flags in [('dfu',0,0x20,d.DFU,d.DFU_SIZE,0),('nvs',1,2,0x80000,0x20000,0),('factory',0,0,d.FACTORY,d.FACTORY_SIZE,0),('system_data',1,0x81,0x600000,0x200000,2)]:
        entries+=struct.pack('<HBBII16sI',0x50aa,kind,subtype,offset,size,label.encode(),flags)
    import hashlib
    return (entries+struct.pack('<H',0xebeb)+b'\xff'*14+hashlib.md5(entries).digest()).ljust(d.PARTITION_SIZE,b'\xff')


class Fake:
    def __init__(self,current=None):
        self.factory=bytearray(b'\xa5'*d.FACTORY_SIZE)
        current=application()if current is None else current
        self.factory[:len(current)]=current
        self.dfu=bytes((i%251)for i in range(d.DFU_SIZE))
        self.partition=partition_table()
        self.state=(0,0,0,False);self.out=[];self.events=[];self.pending=None
        self.input=b'';self.input_at=0;self.zlp=None;self.wrong_token=False
        self.short_read=False;self.fail_write=False;self.corrupt_readback=False
        self.serial=int(d.SERIAL,16);self.hardware=0x01040000;self.mutations=[]
    def region(self,offset,n):
        for base,data in [(d.FACTORY,self.factory),(d.DFU,self.dfu),(d.PARTITION_TABLE,self.partition)]:
            if base<=offset and offset+n<=base+len(data):return bytes(data[offset-base:offset-base+n])
        raise AssertionError('bad fake read')
    def control(self,request,value,length,out=False):
        self.events.append(('control',request,value,length,out))
        assert request!=0x50, 'write protection must never change'
        if request==0:return struct.pack('<III',0,self.serial,self.hardware)+bytes(12)
        assert request==0x42 and not out and length==16
        t,c,cmd,busy=self.state
        if self.wrong_token:t=(t+5)&0xffffffff
        return struct.pack('<IIBB6x',t,c,cmd,int(busy))
    def write(self,body):
        body=bytes(body);self.events.append(('write',len(body)))
        if self.zlp=='OUT':
            assert body==b'';self.zlp=None;return 0
        if self.pending is not None:
            if self.fail_write:raise OSError('injected write failure')
            offset,length,received=self.pending;assert len(body)==min(64,length-received)
            at=offset-d.FACTORY+received;self.factory[at:at+len(body)]=body;received+=len(body)
            if received==length:self.pending=None;self.state=(self.state[0],0,d.WRITE,False);self.zlp='IN'
            else:self.pending=(offset,length,received)
            return len(body)
        assert len(body)==32
        magic,t,cmd,size,reserved,transfer,args=struct.unpack('<IIBBHI16s',body)
        assert magic==d.MAGIC and size==8 and reserved==0
        offset,length=struct.unpack_from('<II',args);assert args[8:]==bytes(8)
        self.out.append((t,cmd,offset,length));self.state=(t,0,cmd,False)
        if cmd==d.READ:
            assert transfer==length;offset-=d.MAPPED_BASE;self.input=self.region(offset,length);self.input_at=0
            if self.corrupt_readback and self.mutations and offset==d.FACTORY:self.input=bytes([self.input[0]^1])+self.input[1:]
            self.zlp='READ_DATA'
        elif cmd==d.ERASE:
            assert transfer==0;d.write_range(offset,length,d.SECTOR)
            self.factory[offset-d.FACTORY:offset-d.FACTORY+length]=b'\xff'*length
            self.mutations.append((cmd,offset,length));self.zlp='IN'
        elif cmd==d.WRITE:
            assert transfer==length;offset-=d.MAPPED_BASE;d.write_range(offset,length,4)
            self.pending=(offset,length,0);self.state=(t,0,cmd,True);self.mutations.append((cmd,offset,length))
        else:raise AssertionError('unexpected command')
        return len(body)
    def read(self,n):
        self.events.append(('read',n))
        if self.zlp=='IN':assert n==64;self.zlp=None;return b''
        assert self.zlp=='READ_DATA';b=self.input[self.input_at:self.input_at+n]
        if self.short_read:return b[:-1]
        self.input_at+=len(b)
        if self.input_at==len(self.input):self.zlp='OUT'
        return b


class Tests(unittest.TestCase):
    def client(self,fake=None):
        fake=Fake()if fake is None else fake;fake.journal=[];c=d.Client(fake,timeout=1,journal=fake.journal.append);c.info();return c,fake
    def files(self,root,new_size=256):
        current=root/'current.bin';current.write_bytes(application())
        new=root/'new.bin';new.write_bytes(application(3,new_size));return current,new
    def backup_plan(self,root,fake=None,new_size=256):
        old,new=self.files(root,new_size);c,fake=self.client(fake)
        d.backup(c,old,d.sha(old.read_bytes()),root/'saved')
        plan=d.make_plan(root/'saved/backup.json',new,d.sha(new.read_bytes()));p=root/'plan.json';p.write_text(json.dumps(plan))
        return c,fake,p,new
    def test_read_is_mapped_and_ack_is_out_zero_length(self):
        c,f=self.client();self.assertEqual(c.read(d.FACTORY,68),f.region(d.FACTORY,68))
        self.assertEqual(f.out[-1][1:],(d.READ,d.MAPPED_BASE+d.FACTORY,68));self.assertEqual(f.events[-1],('write',0))
    def test_erase_offset_write_mapped_and_ack_is_in_zero_length(self):
        c,f=self.client();c.mutation_started=True;c.erase(d.FACTORY,4096);c.write(d.FACTORY,b'abcd')
        self.assertEqual(f.out[0][1:],(d.ERASE,d.FACTORY,4096));self.assertEqual(f.out[1][1:],(d.WRITE,d.MAPPED_BASE+d.FACTORY,4))
        self.assertEqual(f.events[-1],('read',64));self.assertEqual(f.factory[:4],b'abcd')
    def test_direct_mutation_without_apply_gate_refused(self):
        c,f=self.client()
        for op in [lambda:c.erase(d.FACTORY,4096),lambda:c.write(d.FACTORY,b'abcd')]:
            with self.assertRaises(d.Refused):op()
        self.assertEqual(f.out,[])
    def test_all_bad_ranges_refused_before_usb(self):
        c,f=self.client();c.mutation_started=True
        for offset,length in [(0,4096),(d.DFU,4096),(d.FACTORY-4,4096),(d.FACTORY_END,4096),(d.FACTORY_END-4096,8192),(d.FACTORY,-1),(d.FACTORY,0),(d.FACTORY,2**64),(d.FACTORY+1,4096),(d.FACTORY,1)]:
            with self.assertRaises(d.Refused):c.erase(offset,length)
        self.assertEqual(f.out,[])
    def test_read_cannot_touch_efuse_or_arbitrary_flash(self):
        c,f=self.client()
        for offset,length in [(0,4),(0x6000702c,4),(d.FACTORY_END,4),(d.FACTORY,3),(d.PARTITION_TABLE,8192)]:
            with self.assertRaises(d.Refused):c.read(offset,length)
        self.assertEqual(f.out,[])
    def test_identity_mismatch_refuses_before_bulk(self):
        for attr,value in [('serial',0),('hardware',0x01030000),('hardware',0x00040000)]:
            f=Fake();setattr(f,attr,value)
            with self.assertRaises(d.Refused):d.Client(f).info()
            self.assertEqual(f.out,[])
    def test_wrong_token_never_sends_read_ack(self):
        c,f=self.client();old=f.write
        def changed(b):
            n=old(b)
            if len(b)==32:f.wrong_token=True
            return n
        f.write=changed
        with self.assertRaisesRegex(d.Refused,'token mismatch'):c.read(d.FACTORY,64)
        self.assertNotIn(('write',0),f.events)
    def test_short_read_refuses_without_ack(self):
        c,f=self.client();f.short_read=True
        with self.assertRaisesRegex(d.Refused,'short/oversized'):c.read(d.FACTORY,64)
        self.assertNotIn(('write',0),f.events)
    def test_command_error_never_expects_success_zlp(self):
        c,f=self.client();old=f.write
        def rejected(body):
            n=old(body)
            if len(body)==32:f.state=(f.state[0],10,f.state[2],False)
            return n
        f.write=rejected;c.mutation_started=True
        with self.assertRaisesRegex(d.Refused,'command error 10'):c.erase(d.FACTORY,4096)
        self.assertNotIn(('read',64),f.events)
    def test_prefix_probe_is_read_only(self):
        with tempfile.TemporaryDirectory()as name:
            root=Path(name);old,_=self.files(root);c,f=self.client();report=c.probe(old,d.sha(old.read_bytes()))
            self.assertIsNone(report['installed_updater_source_binding']);self.assertEqual(f.mutations,[])
    def test_corrupt_or_wrong_partition_layout_refused_before_mutation(self):
        with tempfile.TemporaryDirectory()as name:
            root=Path(name);old,_=self.files(root);c,f=self.client();bad=bytearray(f.partition);bad[0]^=1;f.partition=bytes(bad)
            with self.assertRaises(d.Refused):c.probe(old,d.sha(old.read_bytes()))
            self.assertEqual(f.mutations,[])
    def test_partition_shape_and_checksum_are_required(self):
        table=partition_table();self.assertEqual(len(d.partitions(table)),4)
        bad=bytearray(table);bad[128+16]^=1
        with self.assertRaisesRegex(d.Refused,'MD5'):d.partitions(bytes(bad))
        with self.assertRaises(d.Refused):d.partitions(table[:128])
    def test_hash_chip_and_size_errors_refuse_offline(self):
        with tempfile.TemporaryDirectory()as name:
            p=Path(name)/'bad.bin';p.write_bytes(application())
            with self.assertRaises(d.Refused):d.image(p,'0'*64)
            x=bytearray(p.read_bytes());x[12]=0;p.write_bytes(x)
            with self.assertRaises(d.Refused):d.image(p,d.sha(x))
    def test_plan_apply_requires_backup_exact_hash_and_explicit_flag(self):
        with tempfile.TemporaryDirectory()as name:
            c,f,p,new=self.backup_plan(Path(name))
            with self.assertRaises(d.Refused):d.apply(c,p,new)
            self.assertEqual(f.mutations,[])
            x=bytearray(new.read_bytes());x[-1]^=1;new.write_bytes(x)
            with self.assertRaises(d.Refused):d.apply(c,p,new,True)
            self.assertEqual(f.mutations,[])
    def test_modified_plan_and_backup_refused_before_erase(self):
        with tempfile.TemporaryDirectory()as name:
            c,f,p,new=self.backup_plan(Path(name));plan=json.loads(p.read_text());plan['factory_offset']=d.DFU;p.write_text(json.dumps(plan))
            with self.assertRaises(d.Refused):d.apply(c,p,new,True)
            self.assertEqual(f.mutations,[])
    def test_full_apply_verifies_partition_tail_and_updater_no_reboot(self):
        with tempfile.TemporaryDirectory()as name:
            c,f,p,new=self.backup_plan(Path(name),new_size=259);original_tail=bytes(f.factory[4096:]);report=d.apply(c,p,new,True)
            self.assertEqual(report['result'],'VERIFIED_NO_REBOOT');self.assertTrue(report['dfu_preserved']);self.assertEqual(bytes(f.factory[4096:]),original_tail)
            self.assertEqual(f.factory[259:4096],b'\xff'*(4096-259));self.assertEqual(f.events[-1],('write',0))
            self.assertFalse(any(e[0]=='control'and e[1]in(1,0x50)for e in f.events))
            with self.assertRaises(d.Refused):d.apply(c,p,new,True)
    def test_changed_flash_since_backup_refuses_before_erase(self):
        with tempfile.TemporaryDirectory()as name:
            c,f,p,new=self.backup_plan(Path(name));f.factory[-1]^=1
            with self.assertRaisesRegex(d.Refused,'factory changed'):d.apply(c,p,new,True)
            self.assertEqual(f.mutations,[])
    def test_write_io_error_does_not_retry_or_reboot(self):
        with tempfile.TemporaryDirectory()as name:
            c,f,p,new=self.backup_plan(Path(name));f.fail_write=True
            with self.assertRaises(OSError):d.apply(c,p,new,True)
            self.assertEqual(len([x for x in f.mutations if x[0]==d.ERASE]),1)
            self.assertFalse(any(e[0]=='control'and e[1]==1 for e in f.events))
    def test_readback_mismatch_does_not_reboot_or_auto_retry(self):
        with tempfile.TemporaryDirectory()as name:
            c,f,p,new=self.backup_plan(Path(name));f.corrupt_readback=True
            with self.assertRaisesRegex(d.Refused,'readback mismatch'):d.apply(c,p,new,True)
            self.assertEqual(len([x for x in f.mutations if x[0]==d.ERASE]),1)
            self.assertFalse(any(e[0]=='control'and e[1]==1 for e in f.events))
            self.assertEqual(f.journal[-1]['event'],'apply_error');self.assertTrue(f.journal[-1]['sync'])
    def test_mutating_header_has_fsynced_intent_before_usb_write(self):
        c,f=self.client();c.mutation_started=True;original=f.write
        def checked(body):
            if len(body)==32:
                self.assertEqual(f.journal[-1]['event'],'before_header');self.assertTrue(f.journal[-1]['sync'])
                self.assertEqual(f.journal[-1]['command'],body[8])
            return original(body)
        f.write=checked;c.erase(d.FACTORY,4096);c.write(d.FACTORY,b'abcd')
        self.assertTrue(any(x['event']=='write_complete'for x in f.journal))
    def test_failed_write_is_recorded_and_journal_failure_prevents_erase(self):
        c,f=self.client();c.mutation_started=True;c.erase(d.FACTORY,4096);f.fail_write=True
        with self.assertRaises(OSError):c.write(d.FACTORY,b'abcd')
        self.assertEqual(f.journal[-1]['event'],'write_error');self.assertTrue(f.journal[-1]['sync'])
        c,f=self.client();c.mutation_started=True
        def broken(_):raise OSError('disk full')
        c.journal=broken
        with self.assertRaises(OSError):c.erase(d.FACTORY,4096)
        self.assertEqual(f.mutations,[])
    def test_disk_journal_is_unique_and_flushes_mutation_intents(self):
        with tempfile.TemporaryDirectory()as name:
            p=Path(name)/'events';j=d.Journal(p)
            with mock.patch.object(d.os,'fsync')as fsync:
                j({'event':'before_header','sync':True,'command':3});fsync.assert_called_once()
            self.assertEqual(json.loads(p.read_text())['event'],'before_header')
            with self.assertRaises(FileExistsError):d.Journal(p)
            j.close()
    def test_data_transfer_deadline_aborts_without_success_ack(self):
        c,f=self.client();original=f.read
        def delayed(n):
            data=original(n);c.command_deadline=0;return data
        f.read=delayed
        with self.assertRaisesRegex(d.Refused,'transfer deadline'):c.read(d.FACTORY,64)
        self.assertNotIn(('write',0),f.events)


if __name__=='__main__':unittest.main()
