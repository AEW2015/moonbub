"""One-owner, reconnecting diagnostic console; no automatic recovery or flash."""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import re
import time
import serial
from serial.tools import list_ports
from contextlib import ExitStack
from gamebub_diagnostic_bytes import DiagnosticBytes, LineFramer

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--query-file',type=Path,required=True)
    p.add_argument('--stop-file',type=Path,required=True)
    p.add_argument('--seconds',type=float,default=3600)
    p.add_argument('--raw-output',type=Path,help='Byte-exact selected diagnostics, credential records redacted; not full UART')
    p.add_argument('--raw-index',type=Path,help='JSONL byte offsets/hashes; requires --raw-output')
    p.add_argument('--max-received-bytes',type=int,default=64*1024*1024)
    p.add_argument('--max-records',type=int,default=100000)
    a=p.parse_args()
    paths=[x for x in (a.output,a.query_file,a.stop_file,a.raw_output,a.raw_index) if x is not None]
    if (not 0<a.seconds<=7200 or any(x.exists() for x in paths)
            or len({x.resolve() for x in paths}) != len(paths)):
        p.error('Use fresh paths and a finite duration <=7200 seconds')
    if bool(a.raw_output) != bool(a.raw_index):
        p.error('--raw-output and --raw-index must be supplied together')
    if not 1<=a.max_received_bytes<=256*1024*1024 or not 1<=a.max_records<=1000000:
        p.error('Capture budgets out of bounds')
    a.output.parent.mkdir(parents=True,exist_ok=True)
    port=None;last_wait=None;received=0;framer=LineFramer()
    def stamp(): return datetime.now(timezone.utc).isoformat(timespec='milliseconds')
    with ExitStack() as files:
        log=files.enter_context(a.output.open('x',encoding='utf-8',buffering=1))
        binary=index=None
        if a.raw_output:
            a.raw_output.parent.mkdir(parents=True,exist_ok=True)
            a.raw_index.parent.mkdir(parents=True,exist_ok=True)
            binary=files.enter_context(a.raw_output.open('xb'))
            index=files.enter_context(a.raw_index.open('x',encoding='utf-8'))
        capture=DiagnosticBytes(binary,index)
        def emit(s):
            line=stamp()+' '+s
            log.write(line+'\n');print(line,flush=True)
        emit('# START reconnecting capture; no reconnect commands are automatic')
        emit('# BYTE_SCOPE selected diagnostics; credential records redacted; not full UART')
        def consume(records,discarded):
            for count in discarded:
                emit('# OVERSIZE_RECORD_DROPPED bytes='+str(count))
            for raw in records:
                if capture.records>=a.max_records:
                    emit('# CAPTURE_RECORD_BUDGET_REACHED');break
                selected=capture.select(raw,stamp())
                if selected is not None:emit(selected)
        deadline=time.monotonic()+a.seconds
        try:
            while time.monotonic()<deadline and not a.stop_file.exists():
                if received>=a.max_received_bytes or capture.records>=a.max_records:
                    emit('# CAPTURE_BUDGET_REACHED received='+str(received)+' records='+str(capture.records));break
                if port is None:
                    candidates=[d for d in list_ports.comports() if d.vid==0x1209 and d.pid==0xb010 and d.serial_number=='802C0E7A']
                    if len(candidates)!=1:
                        state=str([(d.device,d.serial_number) for d in candidates])
                        if state!=last_wait: emit('# WAIT matched_ports='+state);last_wait=state
                        time.sleep(.15);continue
                    try:
                        # Native CDC uses DTR for console availability. Flow
                        # control stays disabled, matching the proven recorder.
                        port=serial.Serial(candidates[0].device,115200,timeout=.02,write_timeout=1,dsrdtr=False,rtscts=False)
                        emit('# OPEN '+candidates[0].device);last_wait=None
                    except serial.SerialException as e:
                        port=None;state=type(e).__name__+str(e)
                        if state!=last_wait:emit('# OPEN_FAILED '+state);last_wait=state
                        time.sleep(.25);continue
                try:
                    if a.query_file.exists():
                        command=a.query_file.read_text(encoding='ascii').strip()
                        if len(command)!=1 or command not in 'stho8cxv[]?dabyie':
                            raise ValueError('Only one known status/setup command is allowed')
                        a.query_file.unlink()
                        if port.write(command.encode('ascii'))!=1:raise OSError('Short command write; do not retry automatically')
                        emit('# COMMAND '+command)
                    remaining=a.max_received_bytes-received
                    if remaining<=0 or capture.records>=a.max_records:
                        emit('# CAPTURE_BUDGET_REACHED received='+str(received)+' records='+str(capture.records));break
                    chunk=port.read(min(4096,max(1,port.in_waiting),remaining))
                    received+=len(chunk)
                    consume(*framer.feed(chunk))
                except (serial.SerialException,OSError) as e:
                    emit('# DISCONNECT '+type(e).__name__+' '+str(e))
                    consume(*framer.finish())
                    try:port.close()
                    except OSError:pass
                    port=None;time.sleep(.1)
        finally:
            consume(*framer.finish())
            if port is not None:port.close()
            emit('# FINISH capture received='+str(received)+' selected_records='+str(capture.records))

if __name__=='__main__':main()
