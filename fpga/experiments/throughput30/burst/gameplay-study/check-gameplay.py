#!/usr/bin/env python3
"""Run bounded RTL and compare/retire only completed, verified generated frames."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import tempfile

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--binary',type=Path,required=True)
p.add_argument('--fixtures',type=Path,required=True)
p.add_argument('--work',type=Path,required=True)
p.add_argument('--cmodel',type=Path,required=True)
p.add_argument('--compare',type=Path,required=True)
p.add_argument('--frames',type=int,default=1800)
p.add_argument('--timeout',type=int,default=18000)
p.add_argument('--origin',type=int,default=0)
p.add_argument('--strict',type=int,choices=(0,1),default=1)
a=p.parse_args()
if not 1<=a.frames<=1800 or a.timeout<1 or a.origin<0:p.error('bad bounds')
if a.work.exists() and any(a.work.iterdir()):p.error('work directory must be new or empty')
a.work.mkdir(parents=True,exist_ok=True);work=a.work.resolve();dumps=work/'dumps';dumps.mkdir()
fixtures=a.fixtures.resolve();manifest=json.loads((fixtures/'manifest.json').read_text());entries=manifest['frames']
if len(entries)!=a.frames or [e['id'] for e in entries]!=list(range(a.frames)): raise SystemExit('fixture manifest count/order mismatch')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for e in entries:
 f=fixtures/f"{e['id']:04}.jpg"
 if f.is_symlink() or not f.is_file() or sha(f)!=e['jpeg_sha256']:raise SystemExit(f'fixture integrity failure {f.name}')
cmd=['timeout',str(a.timeout),str(a.binary.resolve()),f'+FIXTURE_DIR={fixtures}',f'+DUMP_DIR={dumps}',f'+FRAMES={a.frames}',f'+CYCLE_ORIGIN={a.origin}',f'+STRICT_WINDOW={a.strict}']
pass_seen=False; window=None; verified=0;first=None;last=None;max_age=0
proc=None
try:
 with (work/'simulation.log').open('w',buffering=1) as log, (work/'verified.jsonl').open('w',buffering=1) as records:
  proc=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1,start_new_session=True)
  assert proc.stdout is not None
  for line in proc.stdout:
   log.write(line)
   if line.startswith('FRAME_RESULT '):
    f={k:int(v) for k,v in re.findall(r'(\w+)=(\d+)',line)}
    expected=verified+1
    if f.get('id')!=expected:raise RuntimeError(f'frame ordering: {f.get("id")} vs {expected}')
    if f.get('writes')!=345600 or f.get('bursts')!=43200 or f.get('underruns')!=0:raise RuntimeError(f'bad frame counters: {f}')
    idx=expected-1;stem=f'{idx:04d}'; dump=dumps/f'{stem}-rgb565.txt'; jpeg=fixtures/f'{stem}.jpg'; ppm=work/f'{stem}-oracle.ppm'
    if dump.is_symlink() or not dump.is_file() or ppm.exists():raise RuntimeError(f'invalid generated files for frame {idx}')
    digest=sha(dump)
    c=subprocess.run([str(a.cmodel.resolve()),str(jpeg),str(ppm)],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True)
    if c.returncode:raise RuntimeError(f'C model failed frame {idx}: {c.stderr[-500:]}')
    c=subprocess.run([sys.executable,str(a.compare.resolve()),str(ppm),str(dump),'--exact'],capture_output=True,text=True)
    if c.returncode:raise RuntimeError(f'oracle failed frame {idx}: {c.stderr[-500:]} {c.stdout[-500:]}')
    compare=json.loads(c.stdout)
    if compare.get('pixels')!=345600 or compare.get('exact_rgb565_pixels')!=345600:raise RuntimeError('incomplete comparison')
    record={'frame_id':expected,'jpeg_sha256':entries[idx]['jpeg_sha256'],'rtl_dump_sha256':digest,
            'cmodel_exact_pixels':compare['exact_rgb565_pixels'],'cmodel_shared_algorithms':True,**f}
    records.write(json.dumps(record,sort_keys=True)+'\n');records.flush();os.fsync(records.fileno())
    # Only these two newly generated, already verified files under our new work directory are removed.
    if dump.parent!=dumps or ppm.parent!=work or dump.is_symlink() or ppm.is_symlink():raise RuntimeError('unsafe cleanup path')
    dump.unlink();ppm.unlink();verified+=1
    first=f['present_cycle'] if first is None else first;last=f['present_cycle'];max_age=max(max_age,f['arrival_to_present_cycles'])
    print(f'VERIFIED_FRAME {verified}/{a.frames} present_cycle={last}',flush=True)
   elif line.startswith('WINDOW_RESULT '):
    window={k:int(v) for k,v in re.findall(r'(\w+)=(\d+)',line)}
   elif line.startswith('TEST_PASS_JPEG720_60S '):pass_seen=True
   elif '%Fatal' in line:print(line,end='',file=sys.stderr,flush=True)
  rc=proc.wait()
 if rc!=0:raise RuntimeError(f'simulator exit={rc}; verified={verified}/{a.frames}')
 if verified!=a.frames or not pass_seen or not window:raise RuntimeError(f'incomplete verified={verified} pass={pass_seen} window={window}')
 expected_window=a.frames*10000000//3
 if a.strict and (window.get('strict')!=1 or window.get('elapsed_cycles') not in (expected_window,expected_window+1)):
  raise RuntimeError(f'bad strict capture window: {window}, expected={expected_window}')
 result={'frames':verified,'pass_marker':pass_seen,'window':window,'first_present_cycle':first,'last_present_cycle':last,
         'presentation_fps_first_last':(verified-1)*100000000/(last-first) if verified>1 else None,
         'max_arrival_to_present_ms':max_age/100000,'scope':'behavioral FPGA with JPEGs from a precompressed gameplay clip (source-frame repeats possible), instantaneous compressed arrivals, abstract one-frame external queue and modeled pin-level QSPI; no ESP32/Wi-Fi/physical timing',
         'reference':'related fixed-color C model, exact RGB565; not an independent algorithm'}
 (work/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
 print('STREAM_CHECK_PASS '+json.dumps(result,sort_keys=True),flush=True)
except BaseException:
 if proc and proc.poll() is None:
  os.killpg(proc.pid,signal.SIGTERM)
  try:proc.wait(timeout=10)
  except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait()
 raise
