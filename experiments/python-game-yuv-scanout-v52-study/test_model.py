import importlib.util,sys,unittest
from pathlib import Path
import numpy as np
import model as m
P=Path(__file__).resolve().parents[1]
def module(n,p):
 s=importlib.util.spec_from_file_location(n,p);v=importlib.util.module_from_spec(s);sys.modules[n]=v;s.loader.exec_module(v);return v
ft=module('scanout52_test_ft',P/'python-transform-study/fixed_codec.py');corpus=module('scanout52_test_corpus',P/'python-codec-study/corpus.py')
RECTS=((0,0,160,32),(200,5,160,32),(0,400,160,32),(300,400,180,32))
def inputs(random=False):
 rng=np.random.default_rng(52);planes=tuple(rng.integers(0,256,shape,dtype=np.uint8) if random else np.full(shape,128,np.uint8) for shape in((480,720),(240,360),(240,360)))
 for p in planes:p.setflags(write=False)
 patches=[]
 for rect in RECTS:
  x,y,w,h=rect;a=rng.integers(0,65536,(h,w),dtype=np.uint16);a.setflags(write=False);patches.append(dict(rect=rect,words=a))
 return planes,tuple(patches)
def golden(planes,patches):
 a=corpus.rgb565(ft.planes_to_rgb(planes))
 for p in patches:
  x,y,w,h=p['rect'];a[y:y+h,x:x+w]=p['words']
 return a
class Scanline(unittest.TestCase):
 def test_random_exact_rounding_and_HUD(self):
  planes,patches=inputs(True);scan=m.Scanout(planes,patches,RECTS);actual=np.stack(list(scan));np.testing.assert_array_equal(actual,golden(planes,patches));w=scan.work();self.assertEqual(w['Y_unique_input_bytes']+w['chroma_unique_input_bytes'],518400);self.assertEqual(w['HUD_word_reads'],21120);self.assertEqual(w['Cb_row_loads'],240);self.assertEqual(w['Cr_row_loads'],240)
 def test_ownership_and_neutral(self):
  p,h=inputs();scan=m.Scanout(p,h,RECTS);a=next(scan);copy=a.copy();next(scan);np.testing.assert_array_equal(a,copy);self.assertFalse(scan.work()['retained_full_RGB_frame']);np.testing.assert_array_equal(np.vstack([a,*list(m.Scanout(p,h,RECTS))[1:]]),golden(p,h))
 def test_immutable_inputs_and_overlap(self):
  p,h=inputs();bad=list(p);bad[0]=bad[0].copy()
  with self.assertRaises(ValueError):m.Scanout(bad,h,RECTS)
  wrong=list(RECTS);wrong[1]=wrong[0]
  with self.assertRaises(ValueError):m.Scanout(p,h,wrong)
 def test_border_chroma_phase(self):
  p,h=inputs();p=[x.copy() for x in p];p[1][:]=0;p[2][:]=255;p[1][:,-1]=255;p[2][-1,:]=0
  for a in p:a.setflags(write=False)
  np.testing.assert_array_equal(np.stack(list(m.Scanout(p,h,RECTS))),golden(p,h))
if __name__=='__main__':unittest.main()
