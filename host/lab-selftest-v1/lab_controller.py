"""One bounded local MoonBub lab trial. Never invokes this controller automatically."""
from __future__ import annotations
import argparse, ctypes, hashlib, json, os, queue, re, secrets, subprocess, sys, threading, time
from pathlib import Path

SERIAL = '802C0E7A'
LOCAL = '192.168.0.33'
RECEIVER = '192.168.0.157'
SHA = re.compile(r'^[0-9a-f]{64}$')

class Refused(RuntimeError): pass

def require(ok, why):
    if not ok: raise Refused(why)

def pinned(path, expected):
    require(bool(SHA.fullmatch(expected)), 'full lowercase SHA256 required')
    require(hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, 'source hash mismatch: '+str(path))

def alive(pid):
    if type(pid) is not int or pid <= 0: return False
    if os.name == 'nt':
        k = ctypes.WinDLL('kernel32', use_last_error=True)
        k.OpenProcess.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_uint32]
        k.OpenProcess.restype = ctypes.c_void_p
        k.GetExitCodeProcess.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint32)]
        k.CloseHandle.argtypes = [ctypes.c_void_p]
        h = k.OpenProcess(0x1000, False, pid)
        if not h: return False
        try:
            code = ctypes.c_uint32()
            return bool(k.GetExitCodeProcess(h, ctypes.byref(code))) and code.value == 259
        finally: k.CloseHandle(h)
    try: os.kill(pid, 0); return True
    except OSError: return False

class Gate:
    """Pure admission state; arming is a one-shot side effect via supplied writer."""
    def __init__(self, expected_elf, serial=SERIAL):
        require(serial == SERIAL, 'wrong USB serial')
        require(bool(SHA.fullmatch(expected_elf)), 'exact full ELF hash required')
        self.elf = expected_elf; self.identity = False; self.host = False; self.armed = False
    def identify(self, line):
        m = re.search(r'\bp=elf sdk_elf_sha256=([0-9a-f]{64})(?:\s|$)', line)
        if not m: return False
        require(m[1] == self.elf, 'installed ELF mismatch')
        self.identity = True; return True
    def ack(self, line, nonce, action, success):
        m = re.search(r'\bMBLAB1 nonce=([0-9a-f]{16}) action=([A-Z0-9]+) result=([^\s]+)(?:\s|$)', line)
        if not m or m[1] != nonce: return False
        require(m[2] == action and m[3] == success, 'matching nonce has wrong action/result')
        if action == 'HOST33': self.host = True
        return True
    def arm(self, row, started_us, now_us, process_live, prerequisites, writer):
        require(self.identity and self.host, 'identity/HOST33 not established')
        require(not self.armed, 'already armed')
        require(process_live, 'sender process exited')
        require(prerequisites, 'camera/FPGA prerequisites missing')
        require(row.get('event') == 'session' and row.get('profile') == 'dy71-sequence-v3', 'invalid session profile')
        require(row.get('sequence_count') == 12 and type(row.get('session')) is int and row['session'] > 0, 'session/count invalid')
        require(row.get('source', [None])[0] == LOCAL, 'sender source is not local .33')
        source = row['source']; require(len(source) == 2 and type(source[1]) is int and 1 <= source[1] <= 65535, 'invalid source port')
        require(row.get('destination') == [RECEIVER, 5535], 'wrong receiver/port')
        ts = row.get('started_unix_us'); wait = row.get('initial_wait_seconds')
        require(type(ts) is int and started_us - 1000000 <= ts <= now_us + 1000000, 'stale/future session timestamp')
        require(type(wait) in (int, float) and 1 <= wait <= 1800, 'invalid wait')
        require(now_us - ts >= -1000000 and wait - (now_us-ts)/1000000 >= 30, 'sender wait expired or insufficient remaining wait')
        writer(b'@'); self.armed = True

def prerequisites(args, now_us, is_alive=alive):
    program = json.loads(args.program_receipt.read_text()); camera = json.loads(args.camera_ready.read_text())
    for marker in (program, camera):
        ts = marker.get('created_unix_us')
        require(type(ts) is int and 0 <= now_us-ts <= args.prereq_max_age*1000000, 'prerequisite stale/future')
    require(program.get('schema') == 'moonbub-program-receipt-v1' and program.get('verified') is True, 'program receipt unverified')
    require(program.get('device_serial') == SERIAL and program.get('fpga_sha256') == args.expected_fpga_sha256, 'program device/FPGA mismatch')
    require(camera.get('schema') == 'moonbub-camera-ready-v1' and camera.get('full_panel_verified') is True, 'camera coverage not verified')
    require(type(camera.get('coverage_until_unix_us')) is int and camera['coverage_until_unix_us'] >= now_us+args.run_timeout*1000000, 'camera coverage too short')
    require(is_alive(camera.get('pid')), 'camera process not live')
    return True

class SerialLog:
    def __init__(self, port, output):
        import serial
        self.raw = (output/'serial.raw').open('xb'); self.lines=[]; self.lock=threading.Lock(); self.inbox=queue.Queue(); self.closed=False
        # Set inactive states BEFORE open; never toggle DTR/RTS or use them to reset.
        self.port=serial.Serial(port=None, baudrate=115200, timeout=0.2)
        self.port.dtr=False; self.port.rts=False; self.port.port=port; self.port.open()
        self.thread=threading.Thread(target=self._reader, daemon=True); self.thread.start()
    def _reader(self):
        pending=b''
        try:
            while not self.closed:
                b=self.port.read(4096)
                if not b: continue
                self.raw.write(b); self.raw.flush(); pending+=b
                require(len(pending) <= 65536, 'unterminated oversized serial line')
                while b'\n' in pending:
                    line,pending=pending.split(b'\n',1); line=line.rstrip(b'\r').decode('utf-8',errors='replace')
                    with self.lock: self.lines.append(line)
                    self.inbox.put(line)
        except Exception as exc: self.inbox.put(exc)
    def checkpoint(self):
        with self.lock: return len(self.lines)
    def after(self, n):
        with self.lock: return '\n'.join(self.lines[n:])+'\n'
    def write(self, b): self.port.write(b); self.port.flush()
    def wait(self, predicate, seconds):
        deadline=time.monotonic()+seconds
        while time.monotonic()<deadline:
            try: item=self.inbox.get(timeout=min(0.2,max(.001,deadline-time.monotonic())))
            except queue.Empty: continue
            if isinstance(item,Exception): raise Refused('serial reader failed: '+str(item))
            if predicate(item): return item
        raise Refused('serial observation timed out')
    def close(self):
        self.closed=True
        try: self.port.close()
        finally: self.thread.join(timeout=2); self.raw.close()

def find_port(requested=None):
    from serial.tools import list_ports
    ports=[p.device for p in list_ports.comports() if p.serial_number == SERIAL and (requested is None or p.device == requested)]
    require(len(ports)==1, 'need exactly one matching USB serial/port')
    return ports[0]

def fresh_identity(serial, gate):
    # Wait only for observations received after this explicit query.
    while True:
        try: serial.inbox.get_nowait()
        except queue.Empty: break
    serial.write(b'?'); serial.wait(gate.identify,15)

def control(serial, gate, action, success):
    nonce=secrets.token_hex(8)
    serial.write(f'!MBLAB1 {nonce} {action}\n'.encode('ascii'))
    serial.wait(lambda line:gate.ack(line,nonce,action,success),15)
    return nonce

def stop_owned(p):
    if p is not None and p.poll() is None:
        p.terminate()
        try: p.wait(timeout=5)
        except subprocess.TimeoutExpired: p.kill(); p.wait(timeout=5)

def read_session(p, stdout, output, timeout):
    q=queue.Queue()
    def reader():
        try:
            for line in p.stdout:
                stdout.write(line); stdout.flush()
                try: q.put(json.loads(line))
                except json.JSONDecodeError: pass
        except Exception as exc:q.put(exc)
    threading.Thread(target=reader,daemon=True).start()
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        require(p.poll() is None, 'sender exited before session readiness')
        try: row=q.get(timeout=.1)
        except queue.Empty:continue
        if isinstance(row,Exception):raise Refused('sender stdout failed')
        if isinstance(row,dict) and row.get('event')=='session':return row
    raise Refused('sender session readiness timed out')

def run_trial(args, serial, gate, output):
    pinned(args.sender,args.sender_sha256); pinned(args.sender.with_name('dyn1_sequence_core.py'),args.core_sha256); pinned(args.manifest,args.manifest_sha256); pinned(args.validator,args.validator_sha256)
    require(args.sender.name=='sequence_sender.py', 'use pinned sequence_sender.py')
    require(bool(SHA.fullmatch(args.expected_fpga_sha256)), 'full FPGA SHA required')
    prerequisites(args,time.time_ns()//1000)
    control(serial,gate,'HOST33',args.ack_success)
    command=[sys.executable,str(args.sender),'--profile','dy71-sequence-v3','--count','12','--manifest',str(args.manifest),'--receiver',RECEIVER,'--bind',LOCAL,'--initial-wait-seconds','600','--log',str(output/'sender.jsonl')]
    (output/'command.json').write_text(json.dumps(command,indent=2))
    p=None; export_complete=False
    with (output/'sender.stdout').open('x',encoding='utf-8') as out,(output/'sender.stderr').open('x',encoding='utf-8') as err:
        try:
            started=time.time_ns()//1000
            p=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=err,text=True,bufsize=1)
            (output/'owned-sender.json').write_text(json.dumps({'pid':p.pid,'started_unix_us':started}))
            row=read_session(p,out,output,20)
            require(row.get('manifest_sha256')==args.manifest_sha256, 'sender manifest differs')
            ready=prerequisites(args,time.time_ns()//1000)
            beginning=serial.checkpoint()
            gate.arm(row,started,time.time_ns()//1000,p.poll() is None,ready,serial.write)
            (output/'armed.json').write_text(json.dumps({'session':row,'armed_unix_us':time.time_ns()//1000,'one_arm':True}))
            serial.wait(lambda line:bool(re.search(r'\bDY45 END e=\d+ a=\d+ n=\d+ hash=[0-9a-f]{8} tx_loss=unknown$',line)),args.run_timeout)
            export=serial.after(beginning); (output/'export.raw').write_bytes(export.encode('utf-8'))
            validation=subprocess.run([sys.executable,str(args.validator),str(output/'export.raw'),'--output',str(output/'validation.json')],capture_output=True,text=True,timeout=30)
            (output/'validator.stdout').write_text(validation.stdout);(output/'validator.stderr').write_text(validation.stderr)
            require(validation.returncode==0, 'telemetry export validation failed')
            validated=json.loads((output/'validation.json').read_text());require(len(validated.get('valid_attempts',[]))==1 and len(validated.get('exports',[]))==1,'need exactly one complete fresh export');export_complete=True
            require('summary ok=1 frames=12 completed=12 cache=true' in export, 'receiver incomplete/negative outcome')
            require('counters accepted=12 presented=12 rejected=0 underruns=0' in export, 'receiver counts do not pass')
            p.wait(timeout=20);require(p.returncode==0,'sender failed')
            rows=[json.loads(x) for x in (output/'sender.jsonl').read_text().splitlines()]
            require(any(x.get('event')=='complete' and x.get('presented')==12 and x.get('sequence_count')==12 for x in rows), 'sender lacks complete12 result')
            result={'status':'pass','sender_stopped':True,'sender_pid':p.pid,'export_complete':True,'elf':args.expected_elf,'serial':SERIAL,'one_arm':True}
            (output/'result.json').write_text(json.dumps(result,indent=2));return result
        finally:
            stop_owned(p)
            (output/'quiescence.json').write_text(json.dumps({'sender_stopped':p is None or p.poll() is not None,'sender_pid':p.pid if p else None,'export_complete':export_complete,'elf':args.expected_elf,'serial':SERIAL},indent=2))

def parser():
    p=argparse.ArgumentParser(__doc__);p.add_argument('action',choices=['run','ping','reboot','dfu']);p.add_argument('--expected-elf',required=True);p.add_argument('--serial',default=SERIAL);p.add_argument('--port');p.add_argument('--output',type=Path,required=True);p.add_argument('--ack-success',default='OK')
    p.add_argument('--sender',type=Path);p.add_argument('--sender-sha256');p.add_argument('--core-sha256');p.add_argument('--manifest',type=Path);p.add_argument('--manifest-sha256');p.add_argument('--validator',type=Path);p.add_argument('--validator-sha256');p.add_argument('--program-receipt',type=Path);p.add_argument('--expected-fpga-sha256');p.add_argument('--camera-ready',type=Path);p.add_argument('--prereq-max-age',type=int,default=120);p.add_argument('--run-timeout',type=int,default=180);p.add_argument('--completed-run',type=Path)
    return p

def main():
    args=parser().parse_args();gate=Gate(args.expected_elf,args.serial);require(30<=args.run_timeout<=1800,'bounded run timeout required');require(1<=args.prereq_max_age<=300,'bounded marker age required')
    args.output=args.output.resolve();require(args.output.is_relative_to(Path('C:/moon').resolve()),'evidence must stay under C:/moon');require(not args.output.exists(),'unique evidence output required');args.output.mkdir(parents=True)
    (args.output/'arguments.json').write_text(json.dumps(vars(args),default=str,indent=2));serial=None
    try:
        serial=SerialLog(find_port(args.port),args.output);control(serial,gate,'PING',args.ack_success);fresh_identity(serial,gate)
        if args.action=='run':run_trial(args,serial,gate,args.output)
        else:
            if args.action in ('reboot','dfu'):
                require(args.completed_run is not None,'explicit completed-run receipt required')
                prior=json.loads(args.completed_run.read_text());require(prior.get('sender_stopped') is True and prior.get('export_complete') is True,'sender/export not complete')
                require(not alive(prior.get('sender_pid')),'previous sender PID still live')
                require(prior.get('elf')==args.expected_elf and prior.get('serial')==SERIAL,'receipt identity mismatch')
            nonce=control(serial,gate,args.action.upper(),args.ack_success)
            if args.action=='reboot':
                serial.close();serial=None;deadline=time.monotonic()+90
                reboot_output=args.output/'reboot';reboot_output.mkdir()
                # Require an observed disappearance; never issue a second reset.
                gone=False
                while time.monotonic()<deadline-60:
                    try: find_port(args.port)
                    except Refused:gone=True;break
                    time.sleep(.05)
                require(gone,'USB disappearance not observed; reboot remains unverified')
                while time.monotonic()<deadline:
                    try: port=find_port(args.port)
                    except Refused:time.sleep(.5);continue
                    serial=SerialLog(port,reboot_output);break
                require(serial is not None,'device did not reenumerate');reboot_gate=Gate(args.expected_elf,args.serial);control(serial,reboot_gate,'PING',args.ack_success);fresh_identity(serial,reboot_gate)
            (args.output/'result.json').write_text(json.dumps({'status':'acknowledged','action':args.action,'nonce':nonce,'rail_power_cycle':False}))
    except Exception as exc:
        (args.output/'failure.json').write_text(json.dumps({'error':str(exc),'automatic_retry':False,'automatic_reset':False},indent=2));raise
    finally:
        if serial is not None:serial.close()

if __name__=='__main__':main()
