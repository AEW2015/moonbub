#!/usr/bin/env python3
"""Same-canvas complete-presentation CPU calls, balanced three-pair replay."""
from pathlib import Path
import hashlib,importlib.util,json,os,platform,statistics,subprocess,sys,time
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
s=importlib.util.spec_from_file_location('native69_paired_fixture_helpers',HERE/'export_fixtures.py');e=importlib.util.module_from_spec(s);sys.modules[s.name]=e;s.loader.exec_module(e)
h=e.h
r66=h.bound('native69_paired_frozen66_receiver',HERE.parent/'python-game-canonical-tag-v66-study/receiver.py',h)
SOURCE_FILES=('bytes.hpp','entropy.hpp','hud.hpp','decoder.hpp','generated_constants.hpp','main.cpp','native_worker.cpp','test_native.cpp','test_entropy_directed.cpp','test_hud_directed.cpp','fuzz_native.cpp','ab38_check.cpp','export_fixtures.py','make_negative_fixtures.py','import_entropy_directed.py','export_hud_directed.py','verify_fixtures.py','paired_benchmark.py','CMakeLists.txt')
def pins():return {name:hashlib.sha256((HERE/name).read_bytes()).hexdigest()for name in SOURCE_FILES}
def sha(data):return hashlib.sha256(data).hexdigest()
def summary(rows):
 means={name:statistics.mean(r['median_ms'][name]for r in rows)for name in('python','native')}
 return dict(frames=len(rows),keys=sum(r['key']for r in rows),mean_paired_median_complete_presentation_ms=means,native_to_python_ratio=means['native']/means['python'],native_peak_per_frame_median_ms=max(r['median_ms']['native']for r in rows),native_median_over_33_333ms=sum(r['median_ms']['native']>1000/30 for r in rows))
def main():
 before=pins();cpu_model=next((line.split(':',1)[1].strip()for line in Path('/proc/cpuinfo').read_text().splitlines()if line.startswith('model name')),'unknown');cpu_pressure_before=Path('/proc/pressure/cpu').read_text();manifest=h.load(HERE/'manifest.json');command=['docker','exec','-i','gamebub-cu66-v69-build','/build/native/native_worker'];worker=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
 def request(line):
  worker.stdin.write(line+'\n');worker.stdin.flush();reply=worker.stdout.readline()
  if not reply:raise RuntimeError('worker stopped: '+worker.stderr.read())
  return json.loads(reply)
 cases=[]
 try:
  for case in manifest['cases']:
   assert request('RESET')['reset'];rx=r66.Receiver('CU66');rows=[]
   for original in case['rows']:
    path=HERE/original['packet']['path'];packet=path.read_bytes();assert sha(packet)==original['packet']['sha256'];assert request('PREPARE '+str(path))['prepared_bytes']==len(packet);clocks={'python':[],'native':[]};orders=[]
    for rep in range(3):
     order=['python','native']if (original['id']+rep)%2==0 else['native','python'];orders.append(order);fork=r66.Receiver('CU66');fork.ref,fork.rid,fork.hud,fork.last=rx.ref,rx.rid,rx.hud,rx.last;fork._cached_tag=rx.cached_tag
     for name in order:
      if name=='native':
       native=request('TRIAL');clocks['native'].append(native['receive_and_render_ms'])
      else:
       started=time.perf_counter_ns();out=fork.receive(packet);display=h.f.f.n.overlay(h.m.C.corpus.rgb565(h.m.ft.planes_to_rgb(out[0])),tuple(p['words']for p in out[1]));clocks['python'].append((time.perf_counter_ns()-started)/1e6)
     assert native['id']==original['id']and native['key']==original['key']and native['canonical_tag']==original['canonical_tag']
     for key in('canonical_yuv_u8_sha256','hud_words_u16le_sha256','display_rgb565_u16le_sha256'):assert native[key]==original[key]
     assert sha(b''.join(p.astype(np.uint8).tobytes()for p in out[0]))==original['canonical_yuv_u8_sha256'];assert sha(b''.join(p['words'].astype('<u2').tobytes()for p in out[1]))==original['hud_words_u16le_sha256'];assert sha(display.astype('<u2').tobytes())==original['display_rgb565_u16le_sha256'];assert out[2]['output_tag'].hex()==original['canonical_tag']
    assert request('COMMIT')['committed']==original['id'];rx=fork;rows.append(dict(id=original['id'],key=original['key'],packet_sha256=original['packet']['sha256'],canonical_tag=original['canonical_tag'],canonical_yuv_u8_sha256=original['canonical_yuv_u8_sha256'],hud_words_u16le_sha256=original['hud_words_u16le_sha256'],display_rgb565_u16le_sha256=original['display_rgb565_u16le_sha256'],complete_presentation_ms=clocks,paired_order=orders,median_ms={n:statistics.median(values)for n,values in clocks.items()}))
    if original['id']%24==0:print(json.dumps(dict(scene=case['scene'],id=original['id'])),flush=True)
   cases.append(dict(scene=case['scene'],rows=rows,summary=summary(rows)))
  assert request('QUIT')['quit'];worker.wait(timeout=10);assert worker.returncode==0
 finally:
  if worker.poll()is None:worker.kill();worker.wait()
 rows=[r for c in cases for r in c['rows']];assert len(rows)==457 and pins()==before
 result=dict(schema='cu66-native-v69-paired',producer_source_sha256=before,manifest_sha256=sha((HERE/'manifest.json').read_bytes()),cases=cases,summary=summary(rows),environment=dict(python=platform.python_version(),numpy=np.__version__,native_worker_command=command,cpu_model=cpu_model,cpu_pressure_before=cpu_pressure_before,cpu_pressure_after=Path('/proc/pressure/cpu').read_text(),thread_environment={name:os.environ.get(name)for name in('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS')},native_compile_command='g++ -std=c++17 -O3 -Wall -Wextra -Wconversion -Werror native_worker.cpp',native_binary_sha256=sha(Path('/home/lori/gamebub-build/cu66-v69/native/native_worker').read_bytes())),physical_30fps_proven=False,new_FPGA_implementation=False,live_deployment=False,
  scope=['457 retained CU66 source40 packets, 20 keys/437 P across four independent own decoded histories; original per-frame canonical/HUD/fullRGB565 hashes checked on BOTH paths every repeat.','Three alternating paired complete-presentation calls by(frameid+repeat)%2. Python frozen66 CU66 receive plus exact RGB565/HUDcomposition; C++ Decoder::receive includes same observable presentation work.','Native trial clock is C++ steady_clock aroundreceive; host IPC/fileprepare/forks/reportserialization/goldenhashes excluded. Python perf_counter wrapsreceive+render; frozen helper imports/fixtureloads/forks/goldenhashes excluded. No Python inside native decode clock.','Shared non-isolated host; native Ubuntu24 GCC13.3 container with4CPU/4GiB resourcecap, Pythonhostvenv. No FPGA/ESP32/RF/physicaldisplay/FPS claim. Native calls supportzero-motion/arithmetic5/6 only; other grammars rejected.','No native FFmpeg head-to-head measured here; decode-only FFmpeg or older Python66 receive excluding display is not this complete-presentation denominator.'])
 (HERE/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['summary']),flush=True)
if __name__=='__main__':main()
