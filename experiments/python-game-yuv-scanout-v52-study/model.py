"""One-line RGB565 scanout from immutable YUV420 plus exact opaque HUD.

Preserves frozen horizontal-then-vertical rounding; host temporaries are not a
fitted line-buffer implementation. Reference/HUD arrays are caller-owned inputs.
"""
import numpy as np
WIDTH,HEIGHT=720,480
class Rows:
 def __init__(self,plane):self.plane=plane;self.cache={};self.loads=0
 def get(self,index):
  index=min(max(int(index),0),self.plane.shape[0]-1)
  if index not in self.cache:
   if len(self.cache)==2:self.cache.pop(min(self.cache))
   self.cache[index]=self.plane[index].astype(np.uint8,copy=True);self.loads+=1
  return self.cache[index]

def horizontal(row):
 p=row.astype(np.int32);right=np.concatenate((p[1:],p[-1:]));out=np.empty(WIDTH,np.int32);out[::2]=p;out[1::2]=(p+right+1)//2;return out
class Scanout:
 def __init__(self,planes,patches,declared_rectangles):
  if len(planes)!=3:raise ValueError('three immutable bounded YUV420 planes')
  self.planes=tuple(planes)
  for p,shape in zip(planes,((480,720),(240,360),(240,360)),strict=True):
   if not isinstance(p,np.ndarray) or p.shape!=shape or p.dtype!=np.uint8 or p.flags.writeable:raise ValueError('immutable fixed uint8 YUV420 sample domain')
  rects=tuple(tuple(r) for r in declared_rectangles)
  if len(patches)!=4 or len(rects)!=4 or sum(w*h for x,y,w,h in rects)!=21120:raise ValueError('four declared exact HUD rectangles')
  previous_rectangles=[]
  for patch,rect in zip(patches,rects,strict=True):
   if len(rect)!=4 or any(type(v)is not int for v in rect):raise ValueError('integer HUD rectangle')
   x,y,w,h=rect
   if min(x,y)<0 or min(w,h)<1 or x+w>WIDTH or y+h>HEIGHT or any(max(x,px)<min(x+w,px+pw) and max(y,py)<min(y+h,py+ph) for px,py,pw,ph in previous_rectangles):raise ValueError('nonoverlapping in-range HUD')
   previous_rectangles.append(rect);words=patch['words']
   if tuple(patch['rect'])!=rect or not isinstance(words,np.ndarray) or words.shape!=(h,w) or words.dtype!=np.uint16 or words.flags.writeable:raise ValueError('immutable exact RGB565 HUD words')
  # Rectangle validation uses pairwise bounds, no whole-frame geometry bitmap.
  self.patches=tuple(patches);self.rectangles=rects;self.cb=Rows(planes[1]);self.cr=Rows(planes[2]);self.y=0
  self.y_bytes=0;self.HUD_word_reads=0;self.rgb565_words=0
 def __iter__(self):return self
 def __next__(self):
  if self.y==HEIGHT:raise StopIteration
  y=self.y;self.y+=1;row=self.planes[0][y].astype(np.uint8,copy=True);self.y_bytes+=WIDTH;Y=row.astype(np.int32)
  def chroma(cache):
   upper=horizontal(cache.get(y//2))
   if y%2:upper=(upper+horizontal(cache.get(y//2+1))+1)//2
   return upper-128
  cb=chroma(self.cb);cr=chroma(self.cr)
  R=np.clip(Y+((359*cr+128)>>8),0,255).astype(np.uint16);G=np.clip(Y-((88*cb+183*cr+128)>>8),0,255).astype(np.uint16);B=np.clip(Y+((454*cb+128)>>8),0,255).astype(np.uint16)
  output=((R>>3)<<11)|((G>>2)<<5)|(B>>3)
  for patch,(x,top,w,h) in zip(self.patches,self.rectangles,strict=True):
   if top<=y<top+h:output[x:x+w]=patch['words'][y-top];self.HUD_word_reads+=w
  self.rgb565_words+=WIDTH;return output
 def work(self):
  return dict(lines=self.y,Y_unique_input_bytes=self.y_bytes,Cb_row_loads=self.cb.loads,Cr_row_loads=self.cr.loads,
              chroma_unique_input_bytes=(self.cb.loads+self.cr.loads)*360,HUD_word_reads=self.HUD_word_reads,RGB565_words_written=self.rgb565_words,
              retained_full_RGB_frame=False,maximum_cached_raw_chroma_rows_per_plane=2,
              logical_native_YUV_line_bytes=720+4*360,logical_native_RGB565_line_bytes=720*2,
              full_reference_and_HUD_inputs_excluded=True,Python_temporary_bytes_measured=False,target_fit_or_scanout_timing_proven=False)
