"""Fail-closed app-only client for the inspected Game Bub vendor DFU protocol.

Offline by default: importing this module never opens a device. CLI probe/backup
are read-only; apply needs a source-bound plan, exact backup and --apply. No retry
or write-protect-disable command exists. Installed updater source is NOT assumed.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import struct
import time

SERIAL = '802C0E7A'
MAGIC = 0x431FD10B
MAPPED_BASE = 0x3C000000
FACTORY = 0x100000
FACTORY_END = 0x600000
FACTORY_SIZE = FACTORY_END - FACTORY
DFU = 0x10000
DFU_SIZE = 0x30000
PARTITION_TABLE = 0x8000
PARTITION_SIZE = 0x1000
SECTOR = 4096
PACKET = 64
COMMAND_CHUNK = 4096
READ, WRITE, ERASE = 0x84, 0x05, 0x03


class Refused(RuntimeError): pass


def need(ok, message):
    if not ok: raise Refused(message)


def sha(data): return hashlib.sha256(data).hexdigest()


class Journal:
    """New append-only evidence file; mutation intents fsync before USB writes."""
    def __init__(self,path):self.file=Path(path).open('x',encoding='utf-8')
    def __call__(self,event):
        self.file.write(json.dumps(dict(unix_ns=time.time_ns(),**event),sort_keys=True)+'\n')
        self.file.flush()
        if event.get('sync'):os.fsync(self.file.fileno())
    def close(self):self.file.close()


def digest(value):
    need(isinstance(value, str) and len(value) == 64 and all(x in '0123456789abcdef' for x in value), 'full lowercase SHA256 required')
    return value


def image(path, expected_sha):
    data = Path(path).read_bytes()
    need(sha(data) == digest(expected_sha), 'BIN hash mismatch')
    need(64 <= len(data) <= FACTORY_SIZE, 'invalid application size')
    need(data[0] == 0xe9 and 1 <= data[1] <= 16, 'ESP image header required')
    need(struct.unpack_from('<H', data, 12)[0] == 9, 'ESP32-S3 image required')
    need(len(data) >= 36 and struct.unpack_from('<I', data, 32)[0] == 0xabcd5432, 'application descriptor required')
    return data


def write_range(offset, length, alignment):
    need(type(offset) is int and type(length) is int, 'integer range required')
    need(FACTORY <= offset < FACTORY_END and length > 0, 'factory-only mutation')
    need(length <= FACTORY_END - offset, 'factory range overflow')
    need(offset % alignment == 0 and length % alignment == 0, 'mutation alignment')


def read_range(offset, length):
    need(type(offset) is int and type(length) is int and length > 0, 'bounded read required')
    allowed = [(FACTORY, FACTORY_END), (DFU, DFU + DFU_SIZE), (PARTITION_TABLE, PARTITION_TABLE + PARTITION_SIZE)]
    need(any(a <= offset < b and length <= b - offset for a,b in allowed), 'read outside preservation regions')
    need(offset % 4 == 0 and length % 4 == 0, 'read word alignment')


def partitions(raw):
    need(len(raw)==PARTITION_SIZE,'partition table size')
    rows=[];footer=False
    for at in range(0,len(raw),32):
        magic=struct.unpack_from('<H',raw,at)[0]
        if magic==0xffff:break
        if magic==0xebeb:
            need(raw[at+2:at+16]==b'\xff'*14 and raw[at+16:at+32]==hashlib.md5(raw[:at]).digest(),'partition MD5 mismatch')
            footer=True;break
        need(magic==0x50aa,'partition entry magic')
        _,kind,subtype,offset,size,label,flags=struct.unpack_from('<HBBII16sI',raw,at)
        label=label.split(b'\0',1)[0].decode('ascii')
        need(label and 0<size<=0x800000-offset and offset>=0x9000,'partition bounds')
        need(not any(x['label']==label or not(offset+size<=x['offset']or x['offset']+x['size']<=offset)for x in rows),'duplicate/overlapping partition')
        rows.append({'label':label,'type':kind,'subtype':subtype,'offset':offset,'size':size,'flags':flags})
    need(footer,'checksummed partition table required')
    expected={'factory':(0,0,FACTORY,FACTORY_SIZE,0),'dfu':(0,0x20,DFU,DFU_SIZE,0)}
    for label,fields in expected.items():
        matches=[x for x in rows if x['label']==label]
        need(len(matches)==1 and tuple(matches[0][k]for k in ['type','subtype','offset','size','flags'])==fields,'unsupported installed '+label+' partition')
    return rows


class UsbBackend:
    """Explicitly selected WinUSB/libusb device; never changes configuration/driver."""
    def __init__(self,libusb_dll):
        import usb.core
        import usb.util
        import usb.backend.libusb1
        path=Path(libusb_dll).resolve()
        need(path.is_file(),'explicit libusb DLL not found')
        backend=usb.backend.libusb1.get_backend(find_library=lambda _:str(path))
        need(backend is not None,'explicit libusb backend unavailable')
        devices = []
        for device in usb.core.find(find_all=True, idVendor=0x1209, idProduct=0xb010,backend=backend):
            if device.serial_number.upper() == SERIAL: devices.append(device)
        need(len(devices) == 1, 'exactly one expected serial required')
        self.device = devices[0]
        configuration = self.device.get_active_configuration()
        interfaces = [i for i in configuration if i.bInterfaceNumber == 0 and i.bAlternateSetting == 0]
        need(len(interfaces) == 1 and interfaces[0].bInterfaceClass == 0xff, 'vendor interface0 required')
        endpoints = list(interfaces[0])
        need(len(endpoints) == 2 and all(e.bmAttributes & 3 == 2 and e.wMaxPacketSize == 64 for e in endpoints), 'DFU bulk pair required; app control interface is not updater')
        ins = [e.bEndpointAddress for e in endpoints if e.bEndpointAddress & 0x80]
        outs = [e.bEndpointAddress for e in endpoints if not e.bEndpointAddress & 0x80]
        need(len(ins) == len(outs) == 1, 'one IN and one OUT bulk endpoint required')
        self.ep_in, self.ep_out = ins[0], outs[0]
        self.usb_util = usb.util
        usb.util.claim_interface(self.device, 0)

    def control(self, request, value, length, out=False):
        return self.device.ctrl_transfer(0x41 if out else 0xc1, request, wValue=value, wIndex=0, data_or_wLength=b'' if out else length, timeout=2000)

    def write(self, body): return self.device.write(self.ep_out, body, timeout=3000)
    def read(self, length): return bytes(self.device.read(self.ep_in, length, timeout=3000))
    def close(self): self.usb_util.dispose_resources(self.device)


class Client:
    def __init__(self, backend, timeout=10.0,journal=None):
        need(0 < timeout <= 60, 'bounded command timeout')
        self.io, self.timeout = backend, timeout
        self.token = secrets.randbits(32) or 1
        self.previous = None
        self.identity = None
        self.mutation_started = False
        self.journal=journal
        self.command_deadline=None

    def event(self,kind,sync=False,**fields):
        if self.journal is not None:self.journal(dict(event=kind,sync=sync,**fields))

    def budget(self):
        need(self.command_deadline is not None and time.monotonic()<self.command_deadline,'command transfer deadline')

    def info(self):
        raw = bytes(self.io.control(0, 0, 24))
        need(len(raw) == 24, 'short GET_INFO')
        reserved, serial, hardware = struct.unpack_from('<III', raw)
        need(reserved == 0 and f'{serial:08X}' == SERIAL, 'GET_INFO serial mismatch')
        need((hardware >> 24) == 1 and (hardware >> 16) & 0xff == 4, 'Rev4 product1 required')
        value = {'serial': SERIAL, 'hardware': hardware, 'firmware_metadata': raw[12:].hex()}
        if self.identity is not None: need(value == self.identity, 'device identity changed')
        self.identity = value
        self.event('identity',**value)
        return value

    def status(self):
        raw = bytes(self.io.control(0x42, 0, 16))
        need(len(raw) == 16 and raw[9] in (0,1) and raw[10:] == bytes(6), 'bad command status')
        token, code = struct.unpack_from('<II', raw)
        return token, code, raw[8], bool(raw[9])

    def _wait(self, token, command, complete):
        need(self.command_deadline is not None,'command deadline not initialized')
        deadline = self.command_deadline
        while True:
            observed, code, cmd, busy = self.status()
            if observed == token:
                need(cmd == command, 'command ID mismatch')
                need(code == 0, f'updater command error {code}')
                if not complete or not busy:
                    self.budget();return
            else:
                need(not complete and observed == self.previous, 'command token mismatch')
            need(time.monotonic() < deadline, 'command status deadline')
            time.sleep(0.001)

    def _header(self, command, offset, length):
        need(self.identity is not None, 'GET_INFO required before commands')
        previous, code, _, busy = self.status()
        need(code == 0 and not busy, 'previous command not idle/healthy')
        self.previous = previous
        self.token = self.token % 0xffffffff + 1
        need(self.token != self.previous, 'token collision; stop rather than retry')
        args = struct.pack('<II', offset, length) + bytes(8)
        transfer = 0 if command == ERASE else length
        wire = struct.pack('<IIBBHI16s', MAGIC, self.token, command, 8, 0, transfer, args)
        meta={'token':self.token,'command':command,'address_argument':offset,'flash_offset':offset if command==ERASE else offset-MAPPED_BASE,'length':length}
        self.event('before_header',sync=command in(ERASE,WRITE),**meta)
        self.command_deadline=time.monotonic()+self.timeout
        try:
            need(self.io.write(wire) == 32, 'short command header write')
            self._wait(self.token, command, False)
        except Exception as exc:
            self.event('header_error',sync=True,error=type(exc).__name__,detail=str(exc),**meta)
            raise

    def read(self, offset, length):
        read_range(offset, length)
        output = bytearray()
        while len(output) < length:
            amount = min(COMMAND_CHUNK, length - len(output))
            self._header(READ, MAPPED_BASE + offset + len(output), amount)
            chunk = bytearray()
            while len(chunk) < amount:
                expected = min(PACKET, amount - len(chunk))
                self.budget()
                data = self.io.read(expected)
                self.budget()
                need(len(data) == expected, 'short/oversized bulk READ')
                chunk.extend(data)
            self._wait(self.token, READ, True)
            # IN command success requires host OUT ZLP, not an extra IN read.
            need(self.io.write(b'') == 0, 'READ acknowledgement ZLP failed')
            output.extend(chunk)
            self.event('read_complete',token=self.token,flash_offset=offset+len(output)-amount,length=amount)
        return bytes(output)

    def erase(self, offset, length):
        need(self.mutation_started, 'mutation requires validated apply plan')
        need(self.journal is not None,'write-ahead journal required')
        write_range(offset, length, SECTOR)
        try:
            self._header(ERASE, offset, length)
            self._wait(self.token, ERASE, True)
            need(self.io.read(PACKET) == b'', 'ERASE acknowledgement must be IN ZLP')
        except Exception as exc:
            self.event('erase_error',sync=True,token=self.token,flash_offset=offset,length=length,error=type(exc).__name__,detail=str(exc));raise
        self.event('erase_complete',sync=True,token=self.token,flash_offset=offset,length=length)

    def write(self, offset, body):
        need(self.mutation_started, 'mutation requires validated apply plan')
        need(self.journal is not None,'write-ahead journal required')
        write_range(offset, len(body), 4)
        cursor = 0
        while cursor < len(body):
            chunk = body[cursor:cursor + COMMAND_CHUNK]
            self._header(WRITE, MAPPED_BASE + offset + cursor, len(chunk))
            try:
                self.event('before_payload',sync=True,token=self.token,flash_offset=offset+cursor,length=len(chunk))
                for at in range(0, len(chunk), PACKET):
                    self.budget()
                    part = chunk[at:at + PACKET]
                    need(self.io.write(part) == len(part), 'short bulk WRITE')
                    self.budget()
                self._wait(self.token, WRITE, True)
                need(self.io.read(PACKET) == b'', 'WRITE acknowledgement must be IN ZLP')
            except Exception as exc:
                self.event('write_error',sync=True,token=self.token,flash_offset=offset+cursor,length=len(chunk),error=type(exc).__name__,detail=str(exc));raise
            self.event('write_complete',sync=True,token=self.token,flash_offset=offset+cursor,length=len(chunk))
            cursor += len(chunk)

    def probe(self, expected_current_bin, expected_sha):
        known = image(expected_current_bin, expected_sha)
        identity = self.info()
        _, code, _, busy = self.status()
        need(code == 0 and not busy, 'updater not idle/healthy')
        layout=partitions(self.read(PARTITION_TABLE,PARTITION_SIZE))
        sample = self.read(FACTORY, 64)
        need(sample == known[:64], 'installed image prefix mismatch')
        self.event('probe_complete',sync=True,current_bin_sha256=sha(known),current_bin_bytes=len(known),mutations=False)
        return {'schema': 'moonbub-dfu-probe-v1', 'identity': identity, 'current_bin_sha256': sha(known), 'current_bin_bytes': len(known), 'sample_sha256': sha(sample), 'installed_partition_layout':layout, 'installed_updater_source_binding': None}


def backup(client, current_bin, current_sha, directory):
    directory = Path(directory)
    need(not directory.exists(), 'unique backup directory required')
    probe = client.probe(current_bin, current_sha)
    factory = client.read(FACTORY, FACTORY_SIZE)
    need(sha(factory[:probe['current_bin_bytes']]) == current_sha, 'installed full image mismatch')
    updater = client.read(DFU, DFU_SIZE)
    partition = client.read(PARTITION_TABLE, PARTITION_SIZE)
    directory.mkdir(parents=True)
    entries = {}
    for label, data, offset in [('factory',factory,FACTORY),('dfu',updater,DFU),('partition',partition,PARTITION_TABLE)]:
        path = directory / (label + '.bin')
        with path.open('xb') as file: file.write(data)
        entries[label] = {'path': str(path.resolve()), 'sha256': sha(data), 'bytes': len(data), 'offset': offset}
    record = {'schema':'moonbub-dfu-backup-v1', 'probe':probe, 'files':entries, 'writes_performed':False}
    (directory/'backup.json').write_text(json.dumps(record,indent=2)+'\n')
    client.event('backup_complete',sync=True,manifest_path=str(directory/'backup.json'),manifest_sha256=sha((directory/'backup.json').read_bytes()),mutations=False)
    return record


def checked_backup(path):
    record = json.loads(Path(path).read_text())
    need(record.get('schema') == 'moonbub-dfu-backup-v1' and record.get('writes_performed') is False, 'backup schema')
    need(record['probe']['identity']['serial'] == SERIAL, 'backup identity')
    data = {}
    for label, offset, length in [('factory',FACTORY,FACTORY_SIZE),('dfu',DFU,DFU_SIZE),('partition',PARTITION_TABLE,PARTITION_SIZE)]:
        row=record['files'][label]; blob=Path(row['path']).read_bytes()
        need(row['offset']==offset and row['bytes']==length and len(blob)==length and sha(blob)==digest(row['sha256']), 'backup binding mismatch: '+label)
        data[label]=blob
    count=record['probe']['current_bin_bytes'];need(type(count)is int and 64<=count<=FACTORY_SIZE,'backup image size')
    need(partitions(data['partition'])==record['probe']['installed_partition_layout'],'backup partition layout mismatch')
    need(sha(data['factory'][:count])==digest(record['probe']['current_bin_sha256']),'backup current image hash')
    return record,data


def make_plan(backup_path, new_bin, expected_sha):
    old, data = checked_backup(backup_path)
    new = image(new_bin, expected_sha)
    write_bytes = (len(new)+3)//4*4
    erase_bytes = (write_bytes+SECTOR-1)//SECTOR*SECTOR
    write_range(FACTORY,erase_bytes,SECTOR)
    expected=bytearray(data['factory']);expected[:erase_bytes]=b'\xff'*erase_bytes;expected[:len(new)]=new
    return {'schema':'moonbub-app-only-plan-v1','backup_path':str(Path(backup_path).resolve()),'backup_manifest_sha256':sha(Path(backup_path).read_bytes()),'new_bin_sha256':sha(new),'new_bin_bytes':len(new),'factory_offset':FACTORY,'write_bytes':write_bytes,'erase_bytes':erase_bytes,'expected_factory_sha256':sha(expected),'identity':old['probe']['identity'],'automatic_retry':False,'partitions_changed':False,'updater_source_binding':None}


def _apply_inner(client, plan_path, new_bin, execute=False):
    need(execute is True, 'explicit --apply required')
    plan=json.loads(Path(plan_path).read_text())
    need(plan.get('schema')=='moonbub-app-only-plan-v1','plan schema')
    expected=make_plan(plan['backup_path'],new_bin,plan['new_bin_sha256'])
    need(plan==expected,'plan changed or inconsistent')
    need(not client.mutation_started,'one application per client; no retry')
    current,old=checked_backup(plan['backup_path']);new=image(new_bin,plan['new_bin_sha256'])
    need(client.info()==plan['identity'],'current identity mismatch')
    need(sha(client.read(FACTORY,FACTORY_SIZE))==current['files']['factory']['sha256'],'factory changed since backup')
    need(sha(client.read(DFU,DFU_SIZE))==current['files']['dfu']['sha256'],'updater changed since backup')
    need(sha(client.read(PARTITION_TABLE,PARTITION_SIZE))==current['files']['partition']['sha256'],'partition table changed since backup')
    need(client.journal is not None,'write-ahead journal required before apply')
    client.event('apply_validated',sync=True,plan_sha256=sha(Path(plan_path).read_bytes()),new_bin_sha256=sha(new),erase_offset=FACTORY,erase_bytes=plan['erase_bytes'])
    client.mutation_started=True
    client.erase(FACTORY,plan['erase_bytes'])
    padded=new+b'\xff'*(plan['write_bytes']-len(new))
    client.write(FACTORY,padded)
    observed=client.read(FACTORY,FACTORY_SIZE)
    need(observed[:len(new)]==new and sha(observed)==plan['expected_factory_sha256'],'full factory readback mismatch; do not reboot/retry')
    need(sha(client.read(DFU,DFU_SIZE))==current['files']['dfu']['sha256'],'updater preservation check failed')
    need(sha(client.read(PARTITION_TABLE,PARTITION_SIZE))==current['files']['partition']['sha256'],'partition preservation check failed')
    client.event('readback_verified',sync=True,factory_sha256=sha(observed),new_bin_sha256=sha(new),dfu_preserved=True,partition_preserved=True)
    return {'schema':'moonbub-app-only-verified-v1','result':'VERIFIED_NO_REBOOT','identity':plan['identity'],'plan_sha256':sha(Path(plan_path).read_bytes()),'new_bin_sha256':sha(new),'factory_sha256':sha(observed),'dfu_preserved':True,'partition_table_preserved':True,'automatic_retry':False,'post_reboot_ELF_verified':False}


def apply(client,plan_path,new_bin,execute=False):
    try:return _apply_inner(client,plan_path,new_bin,execute)
    except Exception as exc:
        client.event('apply_error',sync=True,error=type(exc).__name__,detail=str(exc),mutation_started=client.mutation_started,reboot_requested=False,automatic_retry=False)
        raise


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--libusb-dll',type=Path,default=Path('C:/msys64/ucrt64/bin/libusb-1.0.dll'))
    sub=p.add_subparsers(dest='action',required=True)
    for action in ['probe','backup']:
        s=sub.add_parser(action);s.add_argument('--current-bin',type=Path,required=True);s.add_argument('--current-sha256',required=True);s.add_argument('--output',type=Path,required=True)
    s=sub.add_parser('plan');s.add_argument('--backup',type=Path,required=True);s.add_argument('--new-bin',type=Path,required=True);s.add_argument('--new-sha256',required=True);s.add_argument('--output',type=Path,required=True)
    s=sub.add_parser('apply');s.add_argument('--plan',type=Path,required=True);s.add_argument('--new-bin',type=Path,required=True);s.add_argument('--apply',action='store_true');s.add_argument('--output',type=Path,required=True)
    a=p.parse_args();a.output=a.output.resolve();need(a.output.is_relative_to(Path('C:/moon').resolve()),'outputs must remain under C:/moon');need(not a.output.exists(),'unique output required')
    a.output.parent.mkdir(parents=True,exist_ok=True)
    if a.action=='plan': result=make_plan(a.backup,a.new_bin,a.new_sha256)
    else:
        if a.action=='apply':need(a.apply,'explicit --apply required')
        journal=Journal(str(a.output)+'.events.jsonl');backend=None;client=None
        try:
            journal({'event':'operation_start','action':a.action,'sync':True})
            backend=UsbBackend(a.libusb_dll);client=Client(backend,journal=journal)
            if a.action=='probe':result=client.probe(a.current_bin,a.current_sha256)
            elif a.action=='backup':backup(client,a.current_bin,a.current_sha256,a.output);return
            else:result=apply(client,a.plan,a.new_bin,execute=a.apply)
        except Exception as exc:
            journal({'event':'operation_failed','action':a.action,'error':type(exc).__name__,'detail':str(exc),'mutation_started':bool(client and client.mutation_started),'sync':True})
            raise
        finally:
            if backend is not None:backend.close()
            journal.close()
    with a.output.open('x')as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result),flush=True)


if __name__=='__main__':main()
