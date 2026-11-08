"""Bounded raw USB evidence; no reset, programming, or automatic reconnect."""
import argparse
import base64
import datetime
import hashlib
import json
from pathlib import Path
import time

import serial
import serial.tools.list_ports
import re

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--output', required=True, type=Path)
p.add_argument('--port', default='COM3')
p.add_argument('--seconds', type=int, default=1800)
p.add_argument('--commands', required=True, type=Path)
a = p.parse_args()
assert 0 < a.seconds <= 3600
assert not a.output.exists() and not a.commands.exists()
a.output.mkdir(parents=True)
recorder_source = Path(__file__).read_bytes()
(a.output / 'executed-recorder.py').write_bytes(recorder_source)
recorder_sha256 = hashlib.sha256(recorder_source).hexdigest()
s = serial.Serial()
s.port, s.baudrate, s.timeout = a.port, 115200, 0.1
s.dtr = s.rts = False
started = time.monotonic()
count = 0
fixture_issued = False
outcome = 'complete'
with (a.output / 'serial.raw').open('xb') as raw, (a.output / 'events.jsonl').open('x') as events:
    def event(kind, **fields):
        events.write(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                                    monotonic_ns=time.monotonic_ns(), kind=kind, **fields)) + '\n')
        events.flush()
    try:
        deadline = time.monotonic() + 180
        while True:
            ports = [x for x in serial.tools.list_ports.comports()
                     if re.sub('[^0-9A-F]', '', str(x.serial_number).upper()) == '802C0E7A']
            if len(ports) == 1:
                s.port = ports[0].device
                break
            if time.monotonic() >= deadline:
                raise RuntimeError('Expected Game Bub serial802C0E7A did not enumerate')
            time.sleep(0.1)
        while True:
            try:
                s.open()
                break
            except serial.SerialException:
                if time.monotonic() >= deadline:
                    raise
                time.sleep(0.2)
        event('opened', port=a.port, dtr=False, rts=False, recorder_sha256=recorder_sha256)
        print('RAW_USB_OPENED', a.output, flush=True)
        while time.monotonic() - started < a.seconds:
            if (a.output / 'stop').exists():
                outcome = 'operator_stop'
                break
            if a.commands.exists():
                try:
                    command = a.commands.read_text(encoding='ascii').strip()
                    if not command:
                        continue
                    assert command in ('?', 's', 'v', '(', ')', 'W', 'I', 'N', 'O', 'E', '~', '@', '^', '&', '$') or re.fullmatch(r'!MBLAB1 [0-9a-f]{16} (PING|HOST33|HOST47|REBOOT|DFU)',command)
                    a.commands.unlink()
                except (PermissionError, FileNotFoundError):
                    continue
                if command in ('~', '@', '^', '&'):
                    assert not fixture_issued, 'Never repeat a one-shot network fixture'
                    fixture_issued = True
                event('command', ascii=command)
                wire=(command+'\n' if command.startswith('!MBLAB1 ') else command).encode(); assert s.write(wire) == len(wire)
            chunk = s.read(8192)
            if chunk:
                count += len(chunk)
                assert count <= 32 * 1024 * 1024, 'Capture bound reached'
                raw.write(chunk)
                raw.flush()
                event('receive', bytes=len(chunk), base64=base64.b64encode(chunk).decode())
    except Exception as error:
        outcome = 'interrupted_or_failed'
        event('error', exception=type(error).__name__, detail=str(error))
        print('RAW_USB_FAILED', type(error).__name__, str(error), flush=True)
        raise
    finally:
        s.close()
        event('finished', outcome=outcome, bytes=count)
        (a.output / 'result.json').write_text(json.dumps(dict(outcome=outcome, bytes=count,
            seconds=time.monotonic()-started, automatic_reconnect=False), indent=2)+'\n')

