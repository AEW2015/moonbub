#!/usr/bin/env python3
"""Directed native HUD branch qualification with frozen Python packet builders."""
import importlib.util,json,struct,sys,types
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('native69_export_module',HERE/'export_fixtures.py');e=importlib.util.module_from_spec(s);sys.modules[s.name]=e;s.loader.exec_module(e)
h=e.h;hud=h.f.f.hud;hd=hud.h;hs32=hud.old
before={name:sys.modules.get(name)for name in('baseline','decoder')}
try:
 sys.modules['baseline']=types.SimpleNamespace(old=hs32,p=hud.p,h=hd);sys.modules['decoder']=hud
 hs33=h.module('native69_hs33_builder',HERE.parent/'python-game-hud-runs-v33-study/model.py')
finally:
 for name,value in before.items():
  if value is None:sys.modules.pop(name,None)
  else:sys.modules[name]=value
row=hud.p.ui.row;hp=hud.p.ui.hp

def main():
 rng=np.random.default_rng(6902);w,hh=32,24;rect=(22,54,w,hh);ref=rng.integers(0,65536,(hh,w),dtype=np.uint16);cur=rng.integers(0,65536,(hh,w),dtype=np.uint16);cases=[];lines=[]
 def add(name,kind,packet,current,reference=None):
  if kind==1:decoded=row.decode_any(packet,720,480)['words']
  elif kind==2:decoded=hd.decode(packet,reference)
  elif kind==3:decoded=hs32._decode_patch(packet,reference)
  else:decoded=hud.decode_patch(packet,reference)
  np.testing.assert_array_equal(decoded,current);p=e.put(packet,'.hud-patch');r=e.put(reference.astype('<u2').tobytes(),'.hud-ref')if reference is not None else None;expected=e.digest(current.astype('<u2').tobytes());cases.append(dict(name=name,kind=kind,packet=p,reference=r,rect=rect,expected_words_sha256=expected));lines.append('\t'.join(map(str,(name,kind,p['path'],'-'if r is None else r['path'],*rect,expected))))
 for mode in range(10):
  current=ref if mode==1 else cur
  if mode==0:payload=current.astype('<u2').tobytes()
  elif mode==1:payload=b''
  elif mode==2:payload=hd._span_encode(cur^ref)
  elif mode==3:payload=hd._planes_encode(cur^ref)
  elif mode in(6,7):
   words=cur.copy()
   if mode==7:words[:,1:]^=cur[:,:-1]
   payload=hd._planes_encode(words)
  elif mode in(8,9):payload=hd._rice_encode(cur,ref if mode==8 else None,left=mode==9)
  elif mode==4:
   pred=hd.predict(ref,-4,3);payload=struct.pack('<bb',-4,3)+hd._residual_encode(cur^pred,cur,pred)
  else:
   vectors=[(-4,4),(4,-4),(0,0),(-1,-2),(2,1),(0,4)];prefix=hd.TILE.pack(16,8,4,0,len(vectors))+struct.pack('<I',2*len(vectors))+b''.join(struct.pack('<bb',*v)for v in vectors);pred,_=hs32._motion_reference(ref,3,prefix,w,hh);payload=prefix+hd._residual_encode(cur^pred,cur,pred)
  independent=mode in(0,6,7,9);packet=hd._pack(mode,current,hd.ZERO if independent else hd._tag(ref),payload);add('HD25_mode'+str(mode),2,packet,current,None if independent else ref)
 for builder,kind,label in ((hs32,3,'HS32'),(hs33,4,'HS33')):
  for mode in(0,1,2,3,9,10,11):
   plain=mode&7;prefix=b'';pred=None
   if plain==1:pred=ref
   elif plain==2:prefix=struct.pack('<bb',-4,3);pred,_=hs32._motion_reference(ref,plain,prefix,w,hh)
   elif plain==3:
    vectors=[(-4,4),(4,-4),(0,0),(-1,-2),(2,1),(0,4)];prefix=hd.TILE.pack(16,8,4,1,len(vectors))+struct.pack('<I',4*len(vectors))+b''.join(hd.RUN.pack(1,*v)for v in vectors);pred,_=hs32._motion_reference(ref,plain,prefix,w,hh)
   payload,_=builder._encode_patch(cur,pred,mode,prefix);packet=builder._pack_patch(cur,ref,mode,payload);add(label+'_mode'+str(mode),kind,packet,cur,None if plain==0 else ref)
 # Full patch palette widths and both row-run units, all with exact RGB565.
 for colors in(2,4,16,256,768):
  words=(np.arange(w*hh,dtype=np.uint16)%colors).reshape(hh,w);rgb=np.zeros((480,720,3),np.uint8);rgb[54:54+hh,22:22+w]=h.m.C.corpus.expand565(words);packet=hp.encode_patch(rgb,rect);add('HP01_colors'+str(colors),1,packet,words)
 words=(np.arange(w*hh,dtype=np.uint16)%4).reshape(hh,w);palette,indices=np.unique(words,return_inverse=True);indices=indices.reshape(hh,w)
 for mode in(0,1,2):
  if mode==0:pal=b'';payload=words.astype('<u2').tobytes()
  else:
   pal=palette.astype('<u2').tobytes()if mode==2 else b'';payload=b''.join(struct.pack('<H',len(tokens))+tokens for tokens in(row._tokens(values,1 if mode==2 else 2)for values in(indices if mode==2 else words)))
  packet=row._seal(row.HEADER.pack(b'HR01',1,mode,*rect,len(pal)//2,w*hh,len(payload))+pal+payload);add('HR01_mode'+str(mode),1,packet,words)
 (HERE/'hud-directed.json').write_text(json.dumps(dict(schema='cu66-native-v69-hud-directed',seed=6902,cases=cases),indent=2)+'\n');(HERE/'hud-directed.tsv').write_text('\n'.join(lines)+'\n');print('HUD directed',len(cases))
if __name__=='__main__':main()
