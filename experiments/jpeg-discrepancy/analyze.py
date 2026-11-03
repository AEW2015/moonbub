#!/usr/bin/env python3
"""Characterize one coordinate-tagged RGB565 RTL frame against Pillow JPEG decodes."""
import argparse, hashlib, json
from pathlib import Path
import numpy as np
from PIL import Image, __version__ as pillow_version, features

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def q565(a):
 a=a.astype(np.int16)
 return np.stack((a[:,:,0]>>3,a[:,:,1]>>2,a[:,:,2]>>3),axis=2)
def metrics(actual, ref):
 d=np.abs(actual-ref); pix=d.max(axis=2)
 return dict(exact_pixels=int(np.count_nonzero(pix==0)),channel_max=d.max(axis=(0,1)).tolist(),
             channel_mean=d.mean(axis=(0,1)).tolist(),pixels_at_least_2=int(np.count_nonzero(pix>=2)),
             pixels_at_least_5=int(np.count_nonzero(pix>=5)),component_total=int(d.size))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('jpeg',type=Path);ap.add_argument('dump',type=Path);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
 with Image.open(args.jpeg) as im: ref=np.array(im.convert('RGB')); w,h=im.size
 with Image.open(args.jpeg) as im: im.decoderconfig=(1,1); fast=np.array(im.convert('RGB'))
 actual=np.empty((h,w,3),np.int16);seen=np.zeros((h,w),bool)
 for line in args.dump.open():
  xx,yy,word=line.split();x,y,v=int(xx),int(yy),int(word,16)
  if not (0<=x<w and 0<=y<h and 0<=v<=65535) or seen[y,x]:raise ValueError('duplicate/out-of-range pixel')
  seen[y,x]=True;actual[y,x]=[(v>>11)&31,(v>>5)&63,v&31]
 if not seen.all():raise ValueError('incomplete pixel coverage')
 standard=q565(ref); nearest=q565(fast);delta=np.abs(actual-standard);maxerr=delta.max(axis=2)
 # A simple image-space chroma-edge proxy, not raw JPEG coefficient data.
 chroma=np.array(Image.fromarray(ref).convert('YCbCr'),dtype=np.int16)[:,:,1:]
 edge=np.zeros((h,w),np.int16)
 diff=np.max(np.abs(chroma[:,1:]-chroma[:,:-1]),axis=2);edge[:,1:]=np.maximum(edge[:,1:],diff);edge[:,:-1]=np.maximum(edge[:,:-1],diff)
 diff=np.max(np.abs(chroma[1:]-chroma[:-1]),axis=2);edge[1:]=np.maximum(edge[1:],diff);edge[:-1]=np.maximum(edge[:-1],diff)
 points=np.argwhere(maxerr==maxerr.max())
 examples=[{'x':int(x),'y':int(y),'rtl_rgb565_codes':actual[y,x].tolist(),'pillow_codes':standard[y,x].tolist(),'nearest_codes':nearest[y,x].tolist(),'chroma_edge_proxy':int(edge[y,x])} for y,x in points[:10]]
 classes={}
 for threshold in (2,5,10):
  mask=maxerr>=threshold
  classes[str(threshold)]={'pixels':int(mask.sum()),'on_chroma_edge_ge_20':int(np.count_nonzero(mask & (edge>=20))),'chroma_edge_proxy_mean':float(edge[mask].mean()) if mask.any() else None}
 out={'inputs':{'jpeg_sha256':sha(args.jpeg),'dump_sha256':sha(args.dump)},'width':w,'height':h,'pillow_version':pillow_version,'jpeg_library':features.version('jpg'),
      'standard':metrics(actual,standard),'pillow_fast_nearest':metrics(actual,nearest),'fast_setting':'decoderconfig=(1,1), requests fast IDCT and no fancy upsampling; not equivalent to changing upsampling alone',
      'frame_chroma_edge_proxy_ge_20_pixels':int((edge>=20).sum()),'error_classes':classes,'worst_pixels':examples}
 args.output.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
