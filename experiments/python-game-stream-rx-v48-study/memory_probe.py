"""Fresh-process tracemalloc call increments, not target RAM or total process RSS."""
from pathlib import Path
import argparse,gc,hashlib,json,subprocess,sys,tracemalloc
import receiver as subject
h=subject.h;HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def load_direct():
 before=sys.modules.get('helpers')
 try:sys.modules['helpers']=h.old;return h.module('stream48_memory_frozen43',HERE.parent/'python-game-direct-rx-v43-study/receiver.py')
 finally:
  if before is None:sys.modules.pop('helpers',None)
  else:sys.modules['helpers']=before

def child(kind,scene,frame):
 data=h.load(HERE.parent/'python-game-binary-qual-v40-study/results.json');case=next(c for c in data['cases'] if c['scene']==scene);folder=HERE.parent/'python-game-binary-qual-v40-study';rx=subject.Receiver() if kind=='stream' else load_direct().Receiver()
 for row in case['rows'][:frame]:rx.receive(h.raw(row['packet'],folder))
 row=case['rows'][frame];packet=h.raw(row['packet'],folder);gc.collect();tracemalloc.start();tracemalloc.reset_peak();a,p,meta,_=rx.receive(packet);current,peak=tracemalloc.get_traced_memory();tracemalloc.stop();assert h.m.C.reference_tag(a).hex()==row['normalized_tag']
 return dict(kind=kind,scene=scene,frame=frame,traced_current_bytes=current,traced_peak_bytes=peak,normalized_output_bytes=sum(x.nbytes for x in a),HUD_words_bytes=sum(x['words'].nbytes for x in p),coefficient_array_bytes=meta['decode_work'].get('coefficient_array_bytes',meta['decode_work'].get('full_coefficient_array_bytes')),existing_reference_state_excluded_from_tracing=bool(frame),whole_process_RSS_measured=False,target_memory_fit_proven=False)

def main():
 p=argparse.ArgumentParser();p.add_argument('--child',choices=['stream','direct']);p.add_argument('--scene');p.add_argument('--frame',type=int);a=p.parse_args()
 if a.child:print(json.dumps(child(a.child,a.scene,a.frame)));return
 rows=[]
 for scene in('mass-effect-10000','mass-effect-4500','mass-effect-1600','mass-effect-combat'):
  for frame in(0,1):
   for kind in('direct','stream'):
    r=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--child',kind,'--scene',scene,'--frame',str(frame)],capture_output=True,text=True,check=True);rows.append(json.loads(r.stdout))
 paths=[Path(__file__),HERE/'receiver.py',HERE/'envelope.py',HERE/'helpers.py',HERE.parent/'python-game-direct-rx-v43-study/receiver.py',HERE.parent/'python-game-binary-qual-v40-study/results.json',HERE.parent/'python-game-block-rx-v44-study/decoder.py',HERE.parent/'python-game-symmetric-inverse-v45-study/model.py']
 out=dict(schema='gamebub-stream-rx-v48-memory-probe',source_sha256={q.relative_to(ROOT).as_posix():hashlib.sha256(q.read_bytes()).hexdigest() for q in paths},rows=rows,scope=['Freshprocessperpoint,8sourcepackets×2implementations;not16uniquesourceframes.','tracemallocstartafterimports/packetI/O/priorreferenceboot;callincrementonly,notRSSorallnativeallocations.','Instrumentationchangesruntime;noFPScomparisonfromthisprobe.','Fullreference/outputplanesremainexternal-memorymodels;PythontrackedallocationisnotFPGA/ESP32memoryfit.'])
 (HERE/'memory-probe.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(dict(points=len(rows),rows=rows)),flush=True)
if __name__=='__main__':main()
