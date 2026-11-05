"""Independent error equations plus frozen-decoder/archived-native plane loader."""
from pathlib import Path
import hashlib,importlib.util,json,sys
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];SOURCE=HERE.parent/'python-game-source-v40-study'
def module(n,p):
 s=importlib.util.spec_from_file_location(n,p);v=importlib.util.module_from_spec(s);sys.modules[n]=v;s.loader.exec_module(v);return v
h=module('error57_verify_direct43_helpers',HERE.parent/'python-game-direct-rx-v43-study/helpers.py');before=sys.modules.get('helpers')
try:sys.modules['helpers']=h;direct=module('error57_verify_direct43',HERE.parent/'python-game-direct-rx-v43-study/receiver.py')
finally:
 if before is None:sys.modules.pop('helpers',None)
 else:sys.modules['helpers']=before
std=module('error57_verify_native24',HERE.parent/'python-game-standard-v24-study/model.py')
def digest(b):return hashlib.sha256(b).hexdigest()
def originals(scene):
 c=next(c for c in h.load(SOURCE/'manifest.json')['cases'] if Path(c['media_file']).stem==scene);words=[];rgb=[]
 for f in c['frames'][:24]:
  canvas=np.frombuffer(h.raw(f['canvas_rgb24'],SOURCE),np.uint8).reshape(480,720,3);a=h.m.C.corpus.rgb565(canvas);assert digest(a.astype('<u2').tobytes())==f['rgb565_sha256'];words.append(a);rgb.append(h.m.C.corpus.expand565(a))
 return words,rgb

def presentations(case,words):
 if case['kind']=='custom':
  folder=HERE.parent/case['source_folder'];d=h.load(folder/'results.json');c=next(c for c in d['cases'] if c['scene']==case['scene'] and c.get('policy','quantized_mixed_guard')==case['policy']);rx=direct.Receiver()
  for f in c['rows']:
   out,patches,meta,_=rx.receive(h.raw(f['packet'],folder));planes=tuple(p.astype(np.uint8) for p in out)
   for p in planes:p.setflags(write=False)
   display=h.f.f.n.overlay(h.m.C.corpus.rgb565(h.m.ft.planes_to_rgb(planes)),tuple(p['words'] for p in patches));assert h.f.f.n.digest(display)==f['display_sha256'];yield f['id'],planes,patches,display
 else:
  folder=(ROOT/case['source']).parent;d=h.load(ROOT/case['source']);c=next(c for c in d['cases'] if c['codec']==case['codec'] and c['parameter']==case['parameter'] and c.get('extra_options')==case['extra_options'] and c.get('scene','mass-effect-combat')==case['scene']);codec=std.av.CodecContext.create('hevc' if c['codec']=='libx265' else 'libdav1d','r');codec.thread_count=1;extra=h.raw(c['extradata'],folder)
  if extra:codec.extradata=extra
  for fid,f in enumerate(c['rows'][:24]):
   pkt=std.av.Packet(h.raw(f['access_unit'],folder));pkt.pts,pkt.dts,pkt.time_base=f['pts'],f['dts'],std.TB;frames=codec.decode(pkt);assert len(frames)==1 and frames[0].pts==fid;planes=std.planes_from_frame(frames[0]);patches=[]
   for p in planes:p.setflags(write=False)
   for rect in h.f.f.n.RECTS:
    x,y,w,hh=rect;view=words[fid][y:y+hh,x:x+w].view();view.setflags(write=False);patches.append(dict(rect=rect,words=view))
   display=std.overlay(std.C.corpus.rgb565(std.C.gm.ft.planes_to_rgb(planes)),tuple(p['words'] for p in patches));assert std.digest(display)==f['display_sha256'];yield fid,planes,tuple(patches),display
  assert not codec.decode(None)

def equations(original,decoded,previous):
 e=decoded.astype(np.int16)-original.astype(np.int16);active=np.zeros((480,720),bool);active[37:442]=True;outside=active.copy()
 for x,y,w,hh in h.f.f.n.RECTS:outside[y:y+hh,x:x+w]=False
 pairsx=outside[:,1:]&outside[:,:-1];pairsy=outside[1:]&outside[:-1];gridx=(np.arange(1,720)%8==0)[None,:];gridy=(np.arange(1,480)%8==0)[:,None];ex=e[:,1:].astype(np.int64)-e[:,:-1];ey=e[1:].astype(np.int64)-e[:-1];sx=np.square(ex).sum(2);sy=np.square(ey).sum(2);grid=int(sx[pairsx&gridx].sum()+sy[pairsy&gridy].sum());rest=int(sx[pairsx&~gridx].sum()+sy[pairsy&~gridy].sum());ns=405*720*3;sse=int(np.square(e[37:442].astype(np.int64)).sum());temporal=None if previous is None else int(np.square(e[37:442].astype(np.int32)-previous[37:442]).astype(np.int64).sum())
 return e,dict(active_SSE=sse,active_samples=ns,active_MSE=sse/ns,active_large_error_pixels=int(np.count_nonzero(np.max(np.abs(e[37:442]),axis=2)>=16)),active_pixels=405*720,grid8_error_jump_SSE=grid,grid8_error_jump_samples=3*(int((pairsx&gridx).sum())+int((pairsy&gridy).sum())),nongrid_error_jump_SSE=rest,nongrid_error_jump_samples=3*(int((pairsx&~gridx).sum())+int((pairsy&~gridy).sum())),coordinate_temporal_error_change_SSE=temporal,coordinate_temporal_error_change_samples=0 if temporal is None else ns)

def summarize(rows):
 s={k:sum(r[k] for r in rows if r[k] is not None) for k in rows[0] if k!='active_MSE'};s.update(frames=len(rows),active_MSE=s['active_SSE']/s['active_samples'],large_error_pixel_fraction=s['active_large_error_pixels']/s['active_pixels'],grid8_error_jump_MSE=s['grid8_error_jump_SSE']/s['grid8_error_jump_samples'],nongrid_error_jump_MSE=s['nongrid_error_jump_SSE']/s['nongrid_error_jump_samples'],coordinate_temporal_error_change_MSE=s['coordinate_temporal_error_change_SSE']/s['coordinate_temporal_error_change_samples']);return s

def main():
 d=h.load(HERE/'results.json');assert len(d['cases'])==20;frames=0;cache={}
 for p,s in d['source_sha256'].items():assert h.sha(ROOT/p)==s,p
 for c in d['cases']:
  if c['scene'] not in cache:cache[c['scene']]=originals(c['scene'])
  words,rgb=cache[c['scene']];prev=None;rows=[]
  for r,(fid,planes,patches,display),original in zip(c['rows'],presentations(c,words),rgb,strict=True):
   assert r['id']==fid and digest(display.astype('<u2').tobytes())==r['display_sha256'];prev,expected=equations(original,h.m.C.corpus.expand565(display),prev);assert r['diagnostic']==expected;rows.append(expected);frames+=1
  assert summarize(rows)==c['summary'];assert c['complete_bytes']==sum(r['complete_bytes'] for r in c['rows']) and c['cap_failures']==sum(not r['cap_fit'] for r in c['rows'])
 assert frames==480;print(json.dumps(dict(policy_anchor_cases=20,decoded_presentations=frames,source_canvases=96,all_error_equations_rederived=True,actual_decoded_native_planes_checked=True,encoding_called=False,subjective_flicker_or_hardware_FPS_proven=False)))
if __name__=='__main__':main()
