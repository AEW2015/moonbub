#!/usr/bin/env python3
"""Bounded column-bank cache model, independent of the service trace's LRU."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];AREA=ROOT/'fpga/experiments/cu66-v76'
RECTS=((22,54,160,24),(22,82,160,24),(168,360,320,24),(168,390,240,24))
BASE=(0x80000,0x80000+172800,0x80000+216000);HUD=0x100000
class Missing(Exception):pass
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def sample(p,x,y):return ((p+1)*37+x*11+y*19+(x^y)*3)&255
def hud_pixel(p,x,y):return ((p+1)*4099+x*97+y*13)&65535
def physical_word(a):
 for p,(base,n,w) in enumerate(zip(BASE,(172800,43200,43200),(720,360,360))):
  if base<=a<base+n:
   rel=a-base;tile,k=divmod(rel,32);ty,tx=divmod(tile,w//8);row,pair=divmod(k,4);x,y=tx*8+pair*2,ty*8+row
   return sample(p,x,y)|(sample(p,x+1,y)<<8)
 off=a-HUD
 for p,(x,y,w,h) in enumerate(RECTS):
  if 0<=off<w*h:return hud_pixel(p,off%w,off//w)
  off-=w*h
 raise ValueError(('unmapped',a))
class Model:
 def __init__(self,lookahead,hslots,cslots=None,yslots=None):
  self.lookahead=lookahead;self.hslots=hslots;self.y_slots=(1+lookahead)if yslots is None else yslots;self.c_slots=(3 if lookahead==2 else 2)if cslots is None else cslots
  self.ptags=[[-1]*self.y_slots,[-1]*self.c_slots,[-1]*self.c_slots]
  self.pdata=[[[0]*(60*32)for _ in range(self.y_slots)],[[0]*(30*32)for _ in range(self.c_slots)],[[0]*(30*32)for _ in range(self.c_slots)]]
  self.htags=[[-1]*hslots for _ in RECTS];self.hdata=[[[0]*(24*8)for _ in range(hslots)]for _ in RECTS]
  self.requests=[[]for _ in range(90)];self.word_checks=0;self.rgb_checks=0
 def plane_load(self,p,col,s):
  slots=self.y_slots if p==0 else self.c_slots;slot=col%slots
  if self.ptags[p][slot]==col:return
  w,rows=(720,60)if p==0 else(360,30)
  for ty in range(rows):
   for b in range(0,32,8):
    a=BASE[p]+(ty*(w//8)+col)*32+b;self.requests[s].append(a)
    for i in range(8):self.pdata[p][slot][ty*32+b+i]=physical_word(a+i)
  self.ptags[p][slot]=col
 def load(self,s):
  u=s*8;self.plane_load(0,s,s)
  for p in (1,2):
   for col in range((u//2)//8,min((u+7)//2+1,359)//8+1):self.plane_load(p,col,s)
  off=0
  for p,(x,y,w,h) in enumerate(RECTS):
   lo,hi=max(u,x),min(u+8,x+w)
   if lo<hi:
    for col in range((lo-x)//8,(hi-1-x)//8+1):
     slot=col%self.hslots
     if self.htags[p][slot]==col:continue
     for row in range(h):
      a=HUD+off+row*w+col*8;self.requests[s].append(a)
      for i in range(8):self.hdata[p][slot][row*8+i]=physical_word(a+i)
     self.htags[p][slot]=col
   off+=w*h
 def get(self,p,x,y):
  col=x//8;slot=col%(self.y_slots if p==0 else self.c_slots)
  if self.ptags[p][slot]!=col:raise Missing(('YUV',p,x,y,col,self.ptags[p][slot]))
  at=(y//8)*32+(y%8)*4+(x%8)//2;v=(self.pdata[p][slot][at]>>(8*(x%2)))&255
  assert v==sample(p,x,y),('sample',p,x,y,v);self.word_checks+=1;return v
 def gethud(self,p,x,y):
  col=x//8;slot=col%self.hslots
  if self.htags[p][slot]!=col:raise Missing(('HUD',p,x,y,col,self.htags[p][slot]))
  v=self.hdata[p][slot][y*8+x%8];assert v==hud_pixel(p,x,y);self.word_checks+=1;return v
 def pixel(self,u,v,cache):
  get=self.get if cache else sample
  def c(p):
   x,y=u//2,v//2;x1,y1=min(x+1,359),min(y+1,239);top=get(p,x,y)
   if u&1:top=(top+get(p,x1,y)+1)//2
   if v&1:
    bot=get(p,x,y1)
    if u&1:bot=(bot+get(p,x1,y1)+1)//2
    top=(top+bot+1)//2
   return top-128
  Y=get(0,u,v);cb,cr=c(1),c(2);clamp=lambda n:max(0,min(255,n))
  r=clamp(Y+(359*cr+128)//256);g=clamp(Y-(88*cb+183*cr+128)//256);b=clamp(Y+(454*cb+128)//256)
  val=((r>>3)<<11)|((g>>2)<<5)|(b>>3)
  for p,(x,y,w,h) in enumerate(RECTS):
   if x<=u<x+w and y<=v<y+h:val=self.gethud(p,u-x,v-y)if cache else hud_pixel(p,u-x,v-y)
  return val
 def verify(self,s):
  for u in range(s*8,s*8+8):
   for v in range(480):assert self.pixel(u,v,True)==self.pixel(u,v,False),('RGB',u,v);self.rgb_checks+=1
 def run(self):
  for s in range(min(90,self.lookahead+1)):self.load(s)
  for s in range(90):
   self.verify(s)
   nxt=s+self.lookahead+1
   if nxt<90:self.load(nxt)
  return dict(lookahead_strips=self.lookahead,Y_column_slots=self.y_slots,chroma_column_slots_per_plane=self.c_slots,HUD_block_columns_per_rectangle=self.hslots,
   cache_data_bytes=3840*self.y_slots+1920*self.c_slots*2+4*24*8*2*self.hslots,RGB_words_checked=self.rgb_checks,cache_sample_checks=self.word_checks,
   bursts=sum(map(len,self.requests)),requests=self.requests)
def main():
 trace=AREA/'service/trace.json';mem=AREA/'service/trace.mem';raw=[int(l,16)for l in mem.read_text().splitlines()];group=[[]for _ in range(90)]
 for value in raw:group[value>>24].append(value&0xffffff)
 d=json.loads(trace.read_text());assert len(raw)==35040 and d['wire_bytes']==560640
 results=[]
 for ahead,hs in ((0,2),(1,3),(2,4)):
  m=Model(ahead,hs);r=m.run();assert r['bursts']==35040 and r['RGB_words_checked']==345600
  assert all(sorted(x)==sorted(y)and len(x)==len(set(x))for x,y in zip(r['requests'],group,strict=True)),'structured miss set differs from independent LRU trace'
  r.pop('requests');r['per_strip_miss_sets_equal_independent_LRU_trace']=True;results.append(r)
 hazard=None
 try:Model(1,2).run()
 except Missing as e:hazard=e.args[0]
 assert hazard is not None and hazard[0]=='HUD','negative probe must expose overwritten live HUD column'
 extra=[]
 for name,kwargs,want in [('Y slots2',dict(yslots=2),'YUV'),('chroma slots2',dict(cslots=2),'YUV'),('HUD slots3',dict(hslots=3),'HUD')]:
  probe=dict(hslots=4);probe.update(kwargs);seen=None
  try:Model(2,**probe).run()
  except Missing as e:seen=e.args[0]
  assert seen is not None and seen[0]==want,(name,seen)
  extra.append(dict(configuration='three-live strips with '+name,expected_live_column_hazard=list(seen),status='EXPECTED_HAZARD_DETECTED'))
 result=dict(schema='cu76-structured-cache-v1',status='PASS_PYTHON_CACHE_AND_RENDER_MODEL',models=results,
  early_schedule_contract=dict(service_release='strip i at max(0,i-1)*P',cache_ready_deadline_and_consumer_start='strip i at (i+1)*P',initial_preroll_periods=1,max_live_strips=3,requires_model_lookahead_strips=2,required_data_bytes=29184),
  underbudget_probes=extra,negative_probe=dict(configuration='one-striplookahead withonlytwoHUDblockcolumns',expected_live_column_hazard=list(hazard),status='EXPECTED_HAZARD_DETECTED'),
  source_sha256={'scripts/cu66-v76/structured_cache.py':sha(Path(__file__).resolve())},input_sha256={str(p.relative_to(ROOT)):sha(p)for p in [trace,mem]},scope='Independent fixed-column softwarebank model versus independent LRUmemorymiss trace and mathematical fullframe RGB565 oracle; synthetic YUV/HUD pixels only',limitations=['Not RTLcache/renderer, port inference, cycle/compute-latency, CDC or physical proof','Prefetch moves require separate live tags/data for pending strip; generation switches and leases unmodeled','Oneword-perbeat streamedfill versus128-bit unpack/bankwrite timing must be implemented and measured','No target30fps or under10ms result'])
 (AREA/'structured/results.json').write_text(json.dumps(result,indent=2)+'\n');print('V76_STRUCTURED_CACHE_PASS RGB_words_per_model=345600 baseline_bytes=14592 two_live_bytes=19968 three_live_bytes=29184 expected_underbudget_hazards=true')
if __name__=='__main__':main()
