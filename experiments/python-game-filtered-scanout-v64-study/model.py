"""Streaming row proof of frozen60 luma filter plus frozen52 color/HUD path."""
from pathlib import Path
import importlib.util,sys
from types import MappingProxyType
import numpy as np
HERE=Path(__file__).resolve().parent

def module(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
old=module('filtered64_frozen_scan52',HERE.parent/'python-game-yuv-scanout-v52-study/model.py')
full=module('filtered64_frozen_filter60',HERE.parent/'python-game-display-filter-v60-study/model.py')

class FilteredRows:
 def __init__(self,plane,excluded,preset):
  if not isinstance(plane,np.ndarray) or plane.shape!=(480,720) or plane.dtype!=np.uint8 or plane.flags.writeable:raise ValueError('immutable fixed uint8 luma')
  if not isinstance(excluded,np.ndarray) or excluded.shape!=plane.shape or excluded.dtype!=bool or excluded.flags.writeable or preset not in full.PRESETS:raise ValueError('fixed exclusion/profile')
  self.source=plane;self.excluded=excluded;self.preset=MappingProxyType(dict(preset));self.cache={};self.pending={};self.y=0;self.loads=0;self.peak_cache=0;self.peak_pending=0;self.lookahead=0;self.vertical=0;self.horizontal=0;self.changed=0
 def _get(self,row):
  if row not in self.cache:
   if not 0<=row<480:raise ValueError('out of range row prefetch')
   a=self.source[row].astype(np.int16);p=self.preset
   if p['strength']:
    x=np.arange(8,720,8);p1=a[x-2].copy();p0=a[x-1].copy();q0=a[x].copy();q1=a[x+1].copy();mask=self.excluded[row];blocked=mask[x-2]|mask[x-1]|mask[x]|mask[x+1];good=(~blocked)&(np.abs(q0-p0)<=p['alpha'])&(np.abs(p0-p1)<=p['beta'])&(np.abs(q1-q0)<=p['beta']);delta=np.where(good,np.clip((3*(q0-p0)+p1-q1+4)//8,-p['strength'],p['strength']),0);a[x-1]=np.clip(p0+delta,0,255);a[x]=np.clip(q0-delta,0,255);self.vertical+=int(np.count_nonzero(delta))
   self.cache[row]=a.astype(np.uint8);self.cache[row].setflags(write=False);self.loads+=1;self.peak_cache=max(self.peak_cache,len(self.cache));self.lookahead=max(self.lookahead,row-self.y)
   if len(self.cache)>4:raise AssertionError('more than4 vertical rows retained')
  return self.cache[row]
 def __iter__(self):return self
 def __next__(self):
  if self.y==480:raise StopIteration
  y=self.y
  for k in tuple(self.cache):
   if k<y-1:del self.cache[k]
  if y in self.pending:out=self.pending.pop(y)
  elif y%8==7 and y+1<480 and self.preset['strength']:
   rows=[self._get(k).astype(np.int16) for k in range(y-1,y+3)];p1,p0,q0,q1=rows;p=self.preset;blocked=np.logical_or.reduce(self.excluded[y-1:y+3]);good=(~blocked)&(np.abs(q0-p0)<=p['alpha'])&(np.abs(p0-p1)<=p['beta'])&(np.abs(q1-q0)<=p['beta']);delta=np.where(good,np.clip((3*(q0-p0)+p1-q1+4)//8,-p['strength'],p['strength']),0);self.horizontal+=int(np.count_nonzero(delta));out=np.clip(p0+delta,0,255).astype(np.uint8);self.pending[y+1]=np.clip(q0-delta,0,255).astype(np.uint8);self.pending[y+1].setflags(write=False);self.peak_pending=max(self.peak_pending,len(self.pending))
  else:out=self._get(y).copy()
  self.changed+=int(np.count_nonzero(out!=self.source[y]));self.y+=1;out.setflags(write=False);return out
 def work(self):
  return dict(lines=self.y,Y_rows_loaded=self.loads,peak_cached_vertical_rows=self.peak_cache,peak_pending_rows=self.peak_pending,maximum_lookahead_rows=self.lookahead,vertical_changed_edges=self.vertical,horizontal_changed_edges=self.horizontal,changed_luma_samples=self.changed,retained_full_filtered_luma=False,logical_cached_vertical_bytes=self.peak_cache*720,logical_pending_luma_bytes=self.peak_pending*720,returned_luma_line_bytes=720)

class Scanout(old.Scanout):
 def __init__(self,planes,patches,declared_rectangles,excluded,preset):
  super().__init__(planes,patches,declared_rectangles);self.patches=tuple(MappingProxyType(dict(p)) for p in self.patches);self.luma=FilteredRows(planes[0],excluded,preset)
 def __next__(self):
  if self.y==480:raise StopIteration
  y=self.y;assert self.luma.y==y;row=next(self.luma);self.y+=1;self.y_bytes+=720;Y=row.astype(np.int32)
  def chroma(cache):
   upper=old.horizontal(cache.get(y//2))
   if y%2:upper=(upper+old.horizontal(cache.get(y//2+1))+1)//2
   return upper-128
  cb=chroma(self.cb);cr=chroma(self.cr);R=np.clip(Y+((359*cr+128)>>8),0,255).astype(np.uint16);G=np.clip(Y-((88*cb+183*cr+128)>>8),0,255).astype(np.uint16);B=np.clip(Y+((454*cb+128)>>8),0,255).astype(np.uint16);out=((R>>3)<<11)|((G>>2)<<5)|(B>>3)
  for patch,(x,top,w,hh) in zip(self.patches,self.rectangles,strict=True):
   if top<=y<top+hh:out[x:x+w]=patch['words'][y-top];self.HUD_word_reads+=w
  self.rgb565_words+=720;out.setflags(write=False);return row,out
 def work(self):
  d=super().work();d.update(luma=self.luma.work(),retained_full_filtered_luma=False,logical_conservative_row_data_bytes=7200,static_exclusion_geometry_and_HUD_and_reference_inputs_excluded=True,Python_temporaries_not_target_fit=True);return d
