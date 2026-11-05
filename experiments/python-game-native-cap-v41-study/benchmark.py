"""Targeted peak-rate controls after the v40 combat quality-grid cap misses."""
from pathlib import Path
from fractions import Fraction
import hashlib,importlib.util,json,sys,time,zlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def module(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
q=module('native_cap41_qual40',HERE.parent/'python-game-native-qual-v40-study/benchmark.py');std=q.std;av=std.av
CONTROL=q.CONTROL;SOURCE=q.SOURCE
def blob(data):
 stored=zlib.compress(data,9);p='objects/'+q.digest(stored)+'.zlib';(HERE/'objects').mkdir(exist_ok=True);(HERE/p).write_bytes(stored)
 return dict(path=p,raw_bytes=len(data),raw_sha256=q.digest(data),stored_sha256=q.digest(stored))
def pins():
 out=q.pins();out.update({p.relative_to(ROOT).as_posix():q.sha(p) for p in (HERE/'benchmark.py',q.HERE/'results.json',ROOT/'experiments/python-game-binary-qual-v40-study/results.json')});return out
def encode(planes,name,parameter,extra,bitrate):
 h,w=planes[0][0].shape;enc=av.CodecContext.create(name,'w');enc.width=w;enc.height=h;enc.pix_fmt='yuv420p';enc.time_base=std.TB;enc.framerate=Fraction(30);enc.thread_count=1;enc.gop_size=24;enc.max_b_frames=0;enc.color_range=2
 requested=std.options(name,parameter);paramkey='x265-params' if name=='libx265' else 'svtav1-params'
 if bitrate is not None:requested.pop('crf');enc.bit_rate=bitrate
 requested[paramkey]+=':'+extra;enc.options=requested.copy();start=time.perf_counter_ns();enc.open();open_ms=(time.perf_counter_ns()-start)/1e6
 assert not enc.options,enc.options
 packets=[];calls=[]
 for i,source in enumerate(planes):
  frame=std.frame_from_planes(source,i);start=time.perf_counter_ns();emitted=enc.encode(frame);ms=(time.perf_counter_ns()-start)/1e6
  packets.extend(dict(pts=p.pts,dts=p.dts,is_key=bool(p.is_keyframe),data=bytes(p)) for p in emitted)
  calls.append(dict(id=i,encode_ms=ms,emitted_pts=[p.pts for p in emitted]))
 tail=enc.encode(None);assert not tail
 return packets,bytes(enc.extradata or b''),dict(requested_options=requested,requested_bit_rate=bitrate,unconsumed_options=dict(enc.options),encoder_open_ms=open_ms,frame_calls=calls,packets_only_at_flush=0,library_versions={k:list(v) for k,v in av.library_versions.items()})
def configs():
 out=[]
 for crf in (22,24,26):
  for buf in (160,200,240):out.append(('libx265',crf,f'vbv-maxrate=4000:vbv-bufsize={buf}:vbv-init=1',None))
 for crf in (34,37):
  for rate in (3000,4000,5000):out.append(('libsvtav1',crf,f'mbr={rate}:mbr-overshoot-pct=0',None))
 for rate in (3000,4000,5000):
  for buf in (40,60):out.append(('libsvtav1',34,f'rc=2:tbr={rate}:buf-sz={buf}:buf-initial-sz={buf}:buf-optimal-sz={buf}:overshoot-pct=0',rate*1000))
 return out
def run(name,parameter,extra,bitrate,source,control,prepared):
 planes,words,parts,hud,tags=prepared;packets,extradata,enc=encode(planes,name,parameter,extra,bitrate);outputs,dec=std.decode(packets,extradata,name);n=len(planes)
 assert [p['pts'] for p in packets]==[p['dts'] for p in packets]==list(range(n));assert [p['pts'] for p in packets if p['is_key']]==list(range(0,n,24))
 assert all(c['emitted_pts']==[c['id']] for c in enc['frame_calls']) and all(c['output_pts']==[c['packet_pts']] for c in dec['decode_calls']) and not dec['frames_only_at_decode_flush']
 rows=[]
 for p,original,patches,hu,tag,src in zip(packets,words,parts,hud,tags,source['frames'],strict=True):
  fid=p['pts'];display=std.overlay(outputs[fid],patches);metric=std.metric(original,display);once=len(extradata) if fid==0 else 0;complete=len(p['data'])+len(hu)+80+once
  rows.append(dict(id=fid,pts=fid,dts=p['dts'],key=p['is_key'],source_pts=src['pts'],source_time_base=src['time_base'],source_sha256=tag,access_unit=blob(p['data']),access_unit_bytes=len(p['data']),extradata_bytes_charged=once,hud_bytes=len(hu),binding_bytes=80,complete_bytes=complete,cap_fit=complete<=49152,metric=metric,display_sha256=std.digest(display)))
 sse=sum(r['metric']['active_squared_error'] for r in rows);samples=sum(r['metric']['active_channel_samples'] for r in rows)
 summary=dict(frames=n,complete_bytes=sum(r['complete_bytes'] for r in rows),maximum_complete_bytes=max(r['complete_bytes'] for r in rows),cap_failures=sum(not r['cap_fit'] for r in rows),active_mse=sse/samples,peak_frame_mse=max(r['metric']['active_mse'] for r in rows),all_HUD_errors=sum(r['metric']['hud_word_errors'] for r in rows))
 return dict(codec=name,parameter=parameter,extra_options=extra,bitrate=bitrate,supported=True,rows=rows,summary=summary,extradata=blob(extradata),encode=enc,decode=dec)
def main():
 before=pins();source=q.load(SOURCE/'manifest.json')['cases'][-1];control=q.load(CONTROL/'results.json')['cases'][-1];assert len(source['frames'])==100;prepared=q.inputs(source,control);target=HERE/'results.json';cases=q.load(target)['cases'] if '--resume' in sys.argv and target.exists() else [];done={(c['codec'],c['parameter'],c['extra_options'],c['bitrate']) for c in cases}
 print(json.dumps(dict(maximum_HUD_bytes=max(map(len,prepared[3])),frame_count=100)),flush=True)
 for name,parameter,extra,bitrate in configs():
  if (name,parameter,extra,bitrate) in done:continue
  try:item=run(name,parameter,extra,bitrate,source,control,prepared)
  except Exception as exc:item=dict(codec=name,parameter=parameter,extra_options=extra,bitrate=bitrate,supported=False,error=repr(exc))
  cases.append(item);assert pins()==before
  target.write_text(json.dumps(dict(schema='gamebub-native-cap-v41',source_sha256=before,cases=cases,source_scene=control['scene'],physical_30fps_proven=False,scope=['Targetedpost-gridcombatpeak-rateexperiment; noheld-outcalibrationclaim.','Same100sourceframes,YUV,HX33HUD,80Bbindingaccountingandactualextradata;allfailedcap/qualitysettingsretained.','Ratecontrolparametersareencoderrequests;onlyactualAUsmeasurethecompletecap.','ImmediateoneAU/frameandoneoutput/AUwithkeys24,bframes0,lookahead0areasserted;notphysicalendpointproof.']),indent=2)+'\n')
  print(json.dumps({k:v for k,v in item.items() if k not in ('rows','extradata','encode','decode')}),flush=True)
if __name__=='__main__':main()
