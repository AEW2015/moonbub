"""One-owner, reconnecting diagnostic console; no automatic recovery or flash."""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import re
import time
import serial
from serial.tools import list_ports

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--query-file',type=Path,required=True)
    p.add_argument('--stop-file',type=Path,required=True)
    p.add_argument('--seconds',type=float,default=3600)
    a=p.parse_args()
    if not 0<a.seconds<=7200 or any(x.exists() for x in (a.output,a.query_file,a.stop_file)):
        p.error('Use fresh paths and a finite duration <=7200 seconds')
    a.output.parent.mkdir(parents=True,exist_ok=True)
    port=None;last_wait=None;panic_lines=0
    def stamp(): return datetime.now(timezone.utc).isoformat(timespec='milliseconds')
    with a.output.open('x',encoding='utf-8',buffering=1) as log:
        def emit(s):
            line=stamp()+' '+s
            log.write(line+'\n');print(line,flush=True)
        emit('# START reconnecting capture; no reconnect commands are automatic')
        deadline=time.monotonic()+a.seconds
        try:
            while time.monotonic()<deadline and not a.stop_file.exists():
                if port is None:
                    candidates=[d for d in list_ports.comports() if d.vid==0x1209 and d.pid==0xb010 and d.serial_number=='802C0E7A']
                    if len(candidates)!=1:
                        state=str([(d.device,d.serial_number) for d in candidates])
                        if state!=last_wait: emit('# WAIT matched_ports='+state);last_wait=state
                        time.sleep(.15);continue
                    try:
                        # Native CDC uses DTR for console availability. Flow
                        # control stays disabled, matching the proven recorder.
                        port=serial.Serial(candidates[0].device,115200,timeout=.1,write_timeout=1,dsrdtr=False,rtscts=False)
                        emit('# OPEN '+candidates[0].device);last_wait=None
                    except serial.SerialException as e:
                        port=None;state=type(e).__name__+str(e)
                        if state!=last_wait:emit('# OPEN_FAILED '+state);last_wait=state
                        time.sleep(.25);continue
                try:
                    if a.query_file.exists():
                        command=a.query_file.read_text(encoding='ascii').strip()
                        if len(command)!=1 or command not in 'stho8cxv[]?daby':
                            raise ValueError('Only one known status/setup command is allowed')
                        a.query_file.unlink()
                        if port.write(command.encode('ascii'))!=1:raise OSError('Short command write; do not retry automatically')
                        emit('# COMMAND '+command)
                    line=port.readline().decode('utf-8','replace').strip()
                    fatal=bool(re.search(r'Reset reason:|Guru Meditation|Backtrace:|abort\(\)|assert failed|panicked at|stack (overflow|canary)|task_wdt|brownout|Rebooting|Restarting|rst:',line,re.I))
                    if fatal:panic_lines=45
                    allowed=fatal or panic_lines>0 or any(t in line for t in ('USB_TEST','USB_TRACE','USB_D24','Streaming frame drop:','Streaming memory '))
                    if line and allowed:
                        if re.search(r'\b(ssid|password|passphrase|psk)\b',line,re.I):line='[credential-related line withheld]'
                        emit(line)
                        if panic_lines:panic_lines-=1
                except (serial.SerialException,OSError) as e:
                    emit('# DISCONNECT '+type(e).__name__+' '+str(e))
                    try:port.close()
                    except OSError:pass
                    port=None;time.sleep(.1)
        finally:
            if port is not None:port.close()
            emit('# FINISH capture')

if __name__=='__main__':main()
