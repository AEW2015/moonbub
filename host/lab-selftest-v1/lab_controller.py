"""One bounded local MoonBub lab trial. Never invokes this controller automatically."""
from __future__ import annotations
import argparse, ctypes, hashlib, json, os, queue, re, secrets, subprocess, sys, threading, time
from pathlib import Path

SERIAL = '802C0E7A'
LOCAL = '192.168.0.33'
RECEIVER = '192.168.0.157'
SHA = re.compile(r'^[0-9a-f]{64}$')

class Refused(RuntimeError): pass
class PortOpenPending(OSError): pass

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
        self.lines=[]; self.lock=threading.Lock(); self.inbox=queue.Queue(); self.closed=False
        # Inactive states are configured BEFORE open. No log file is reserved until open succeeds.
        self.port=serial.Serial(port=None, baudrate=115200, timeout=0.2)
        try:
            self.port.dtr=False; self.port.rts=False; self.port.port=port; self.port.open()
        except OSError as exc:
            try:self.port.close()
            except Exception as cleanup:raise Refused('port-open cleanup failed: '+str(cleanup)) from exc
            raise PortOpenPending(type(exc).__name__+': '+str(exc)) from exc
        try:
            self.raw=(output/'serial.raw').open('xb')
            self.thread=threading.Thread(target=self._reader, daemon=True);self.thread.start()
        except Exception:
            self.closed=True;self.port.close()
            if hasattr(self,'raw'):self.raw.close()
            raise
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
        try:
            cancel=getattr(self.port,'cancel_read',None)
            if cancel is not None:
                try:cancel()
                except Exception:pass
            self.port.close()
        finally:
            self.thread.join(timeout=2)
            require(not self.thread.is_alive(),'serial reader did not stop; raw log left open')
            self.raw.close()

class PresenceMonitor:
    """Observe exact-serial disappearance/return concurrently with ACK/serial close."""
    def __init__(self, initial_port, enumerate_ports=None, interval=.025):
        require(0 < interval <= .05, 'presence polling must be at most50ms')
        self.initial_port=initial_port;self.enumerate=enumerate_ports or matching_ports;self.interval=interval
        self.stop_event=threading.Event();self.ready=threading.Event();self.returned=threading.Event();self.lock=threading.Lock()
        self.events=[];self.error=None;self.command_us=None;self.return_port=None;self.samples=0;self.max_gap_us=0;self.thread=None
    def _record(self,kind,ports,now):
        self.events.append({'event':kind,'ports':ports,'monotonic_us':now,'unix_us':time.time_ns()//1000})
    def _watch(self):
        last=None;gone=False
        try:
            while not self.stop_event.is_set():
                ports=sorted(self.enumerate());now=time.monotonic_ns()//1000
                with self.lock:
                    self.samples+=1
                    if last is not None:self.max_gap_us=max(self.max_gap_us,now-last)
                    last=now
                    if self.samples==1:
                        require(ports==[self.initial_port], 'initial exact-serial presence changed')
                        self._record('initial',ports,now);self.ready.set()
                    elif self.command_us is not None:
                        require(len(ports)<=1,'multiple exact-serial interfaces during reboot')
                        if not ports and not gone:
                            gone=True;self._record('gone',ports,now)
                        elif ports and gone:
                            self.return_port=ports[0];self._record('returned',ports,now);self.returned.set();return
                self.stop_event.wait(self.interval)
        except Exception as exc:
            with self.lock:self.error=str(exc)
            self.ready.set();self.returned.set()
    def start(self):
        self.thread=threading.Thread(target=self._watch,daemon=True);self.thread.start()
        require(self.ready.wait(5),'presence monitor failed to start')
        require(self.error is None,self.error or 'presence monitor failed')
    def mark_command(self):
        with self.lock:
            require(self.command_us is None,'reboot command already marked')
            self.command_us=time.monotonic_ns()//1000;self._record('command',[],self.command_us)
    def wait_return(self,timeout=90):
        require(self.returned.wait(timeout),'USB disappearance/return not observed; no reset retry')
        with self.lock:
            require(self.error is None,self.error or 'presence monitor failed')
            require(self.return_port is not None,'USB return unverified')
            return self.return_port
    def snapshot(self):
        with self.lock:return {'serial':SERIAL,'events':list(self.events),'samples':self.samples,'max_sample_gap_us':self.max_gap_us,'error':self.error,'return_port':self.return_port}
    def stop(self):
        self.stop_event.set()
        if self.thread is not None:
            self.thread.join(timeout=2);require(not self.thread.is_alive(),'presence monitor did not stop')

def matching_ports():
    from serial.tools import list_ports
    return [p.device for p in list_ports.comports() if p.serial_number==SERIAL]

def open_returned_serial(output,deadline,attempts,enumerate_ports=None,open_log=None,clock=time.monotonic,sleep=time.sleep):
    """Retry only opening the exact returned serial; never send a reset or reuse stale COM."""
    require(output.is_dir(),'reboot evidence directory must already exist')
    enumerate_ports=enumerate_ports or matching_ports;open_log=open_log or SerialLog
    while clock()<deadline:
        row={'attempt':len(attempts)+1,'unix_us':time.time_ns()//1000,'monotonic_us':int(clock()*1000000),'remaining_ms':max(0,int((deadline-clock())*1000))}
        attempts.append(row)
        try:
            ports=sorted(enumerate_ports());row['ports']=ports
            require(len(ports)<=1,'multiple exact-serial interfaces while opening')
            if not ports:row['result']='not_enumerated'
            else:
                row['port']=ports[0]
                try:
                    log=open_log(ports[0],output);row['result']='opened';return log
                except PortOpenPending as exc:row['result']='temporarily_unopenable';row['error']=str(exc)
        except Refused:row['result']='refused';raise
        sleep(min(.1,max(0,deadline-clock())))
    raise Refused('returned serial remained unopenable before existing reboot deadline; no reset retry')

def find_port(requested=None):
    ports=[p for p in matching_ports() if requested is None or p==requested]
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

class SenderPump:
    def __init__(self, process, output):
        self.process=process;self.output=output;self.inbox=queue.Queue();self.lock=threading.Lock();self.discard=threading.Event();self.error=None
        self.thread=threading.Thread(target=self._reader,daemon=True);self.thread.start()
    def _reader(self):
        try:
            for line in self.process.stdout:
                with self.lock:
                    if self.discard.is_set():return
                    self.output.write(line);self.output.flush()
                try:self.inbox.put(json.loads(line))
                except json.JSONDecodeError:pass
        except Exception as exc:self.error=str(exc);self.inbox.put(exc)
    def finish(self,timeout=5):
        self.thread.join(timeout=timeout)
        if self.thread.is_alive():
            # Block late writes before caller closes the evidence file.
            with self.lock:self.discard.set()
            raise Refused('sender stdout reader did not stop; tail incomplete')
        require(self.error is None,'sender stdout reader failed: '+str(self.error))
        self.process.stdout.close()

def read_session(p,pump,timeout):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        require(p.poll() is None, 'sender exited before session readiness')
        try:row=pump.inbox.get(timeout=.1)
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
    p=None; pump=None; export_complete=False; result=None
    with (output/'sender.stdout').open('x',encoding='utf-8') as out,(output/'sender.stderr').open('x',encoding='utf-8') as err:
        try:
            started=time.time_ns()//1000
            p=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=err,text=True,bufsize=1)
            (output/'owned-sender.json').write_text(json.dumps({'pid':p.pid,'started_unix_us':started}))
            pump=SenderPump(p,out)
            row=read_session(p,pump,20)
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
            return result
        finally:
            stop_owned(p)
            if pump is not None:pump.finish()
            (output/'quiescence.json').write_text(json.dumps({'sender_stopped':p is None or p.poll() is not None,'sender_pid':p.pid if p else None,'export_complete':export_complete,'elf':args.expected_elf,'serial':SERIAL},indent=2))
            if result is not None:(output/'result.json').write_text(json.dumps(result,indent=2))

def parser():
    p=argparse.ArgumentParser(__doc__);p.add_argument('action',choices=['run','ping','reboot','dfu']);p.add_argument('--expected-elf',required=True);p.add_argument('--serial',default=SERIAL);p.add_argument('--port');p.add_argument('--output',type=Path,required=True);p.add_argument('--ack-success',default='OK')
    p.add_argument('--sender',type=Path);p.add_argument('--sender-sha256');p.add_argument('--core-sha256');p.add_argument('--manifest',type=Path);p.add_argument('--manifest-sha256');p.add_argument('--validator',type=Path);p.add_argument('--validator-sha256');p.add_argument('--program-receipt',type=Path);p.add_argument('--expected-fpga-sha256');p.add_argument('--camera-ready',type=Path);p.add_argument('--prereq-max-age',type=int,default=120);p.add_argument('--run-timeout',type=int,default=180);p.add_argument('--completed-run',type=Path)
    return p

def main():
    args=parser().parse_args();gate=Gate(args.expected_elf,args.serial);require(30<=args.run_timeout<=1800,'bounded run timeout required');require(1<=args.prereq_max_age<=300,'bounded marker age required')
    args.output=args.output.resolve();require(args.output.is_relative_to(Path('C:/moon').resolve()),'evidence must stay under C:/moon');require(not args.output.exists(),'unique evidence output required');args.output.mkdir(parents=True)
    (args.output/'arguments.json').write_text(json.dumps(vars(args),default=str,indent=2));serial=None
    source=Path(__file__).read_bytes()
    (args.output/'executed-controller.py').write_bytes(source)
    (args.output/'controller-source-sha256.txt').write_text(hashlib.sha256(source).hexdigest()+'\n')
    try:
        serial=SerialLog(find_port(args.port),args.output);control(serial,gate,'PING',args.ack_success);fresh_identity(serial,gate)
        if args.action=='run':run_trial(args,serial,gate,args.output)
        else:
            if args.action in ('reboot','dfu'):
                require(args.completed_run is not None,'explicit completed-run receipt required')
                prior=json.loads(args.completed_run.read_text());require(prior.get('sender_stopped') is True and prior.get('export_complete') is True,'sender/export not complete')
                require(not alive(prior.get('sender_pid')),'previous sender PID still live')
                require(prior.get('elf')==args.expected_elf and prior.get('serial')==SERIAL,'receipt identity mismatch')
            monitor=None;open_attempts=[];reboot_deadline=None
            try:
                if args.action=='reboot':
                    monitor=PresenceMonitor(serial.port.port);monitor.start();reboot_deadline=time.monotonic()+90;monitor.mark_command()
                nonce=control(serial,gate,args.action.upper(),args.ack_success)
                if args.action=='reboot':
                    serial.close();serial=None
                    # Exact serial alone after reboot; COM numbers may change.
                    monitor.wait_return(max(.001,reboot_deadline-time.monotonic()))
                    reboot_output=args.output/'reboot';reboot_output.mkdir()
                    serial=open_returned_serial(reboot_output,reboot_deadline,open_attempts)
                    reboot_gate=Gate(args.expected_elf,args.serial);control(serial,reboot_gate,'PING',args.ack_success);fresh_identity(serial,reboot_gate)
            finally:
                if monitor is not None:
                    try:monitor.stop()
                    finally:
                        (args.output/'reboot-presence.json').write_text(json.dumps(monitor.snapshot(),indent=2))
                        (args.output/'reboot-open-attempts.json').write_text(json.dumps(open_attempts,indent=2))
            (args.output/'result.json').write_text(json.dumps({'status':'acknowledged','action':args.action,'nonce':nonce,'rail_power_cycle':False}))
    except Exception as exc:
        (args.output/'failure.json').write_text(json.dumps({'error':str(exc),'automatic_retry':False,'automatic_reset':False},indent=2));raise
    finally:
        if serial is not None:serial.close()

if __name__=='__main__':main()
