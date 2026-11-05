"""CS38 arithmetic-only experimental receiver, one coefficient/inverse tile.

Keeps full external-model reference/reconstruction planes; no whole coefficient
or prediction planes. Returned state publishes only after all frame checks pass.
"""
import hashlib,time
import numpy as np
import helpers as h
import envelope
TABLES={(axis,scale):h.m.ft.qtable(scale,axis!=0) for axis in(0,1) for scale in(8,16,32)}
def prediction_tile(reference,vectors,block_size,axis,by,bx):
 if reference is None:return np.full((8,8),128,np.int16),0
 image=reference[axis];ph,pw=image.shape;den=2 if axis==0 else 4;mbs=block_size if axis==0 else block_size//2
 qx,qy=map(int,vectors[by*8//mbs,bx*8//mbs]);ix,fx=divmod(qx,den);iy,fy=divmod(qy,den)
 yy=np.arange(by*8,by*8+8,dtype=np.int32)[:,None]+iy;xx=np.arange(bx*8,bx*8+8,dtype=np.int32)[None,:]+ix
 y0=np.clip(yy,0,ph-1);x0=np.clip(xx,0,pw-1)
 if not fx and not fy:return image[y0,x0].copy(),64
 total=(den-fx)*(den-fy)*image[y0,x0].astype(np.int32)
 if fx:total+=fx*(den-fy)*image[y0,np.clip(xx+1,0,pw-1)]
 if fy:total+=(den-fx)*fy*image[np.clip(yy+1,0,ph-1),x0]
 if fx and fy:total+=fx*fy*image[np.clip(yy+1,0,ph-1),np.clip(xx+1,0,pw-1)]
 return ((total+den*den//2)//(den*den)).astype(np.int16),64*(1+bool(fx))*(1+bool(fy))

def inverse_tile(a):
 n=np.count_nonzero(a)
 if not n:return np.zeros((8,8),np.int64),'zero'
 if n==1 and a[0,0]:
  mid=(int(a[0,0])*5793+8192)>>14;v=(mid*5793+8192)>>14;return np.full((8,8),v,np.int64),'DC'
 return h.sym.inverse(a),'complex'

class Receiver:
 def __init__(self):self.ref=None;self.rid=h.m.NO_REF;self.hud=None;self.last=-1
 def receive(self,packet):
  start=time.perf_counter_ns();meta=envelope.parse_envelope(packet);key=meta['key'];fid=meta['frame_id'];m=h.m
  if fid<=self.last:raise ValueError('stream48 monotonic publication')
  if key:reference=None
  else:
   if self.ref is None or self.rid!=meta['reference_id'] or m.C.reference_tag(self.ref)!=meta['reference_tag']:raise ValueError('stream48 actual committed reference')
   reference=m.base.old._planes(self.ref,(720,480))
  reconstructed=[];hashes=[];work=[]
  for axis,(payload,safe) in enumerate(zip(meta['plane_payloads'],h.f.f.safe_blocks(),strict=True)):
   ph,pw=((480,720) if axis==0 else (240,360));bw=pw//8;bh=ph//8;mask=safe.reshape(-1);compact=payload[0]==6;count=int((~mask).sum()) if compact else len(mask)
   reader=h.block.TileReader(payload[1:],count,1 if compact else bw);output=np.empty((ph,pw),np.int16);coefficient_hash=hashlib.sha256();fetches=0;classes=dict(zero=0,DC=0,complex=0);consumed=0
   for block_index in range(bh*bw):
    by,bx=divmod(block_index,bw)
    if compact and mask[block_index]:coeff=np.zeros((8,8),np.int16)
    else:coeff=next(reader);consumed+=1
    if mask[block_index] and np.any(coeff):raise ValueError('stream48 hidden nonzero coefficients')
    coefficient_hash.update(coeff.astype('<i2',copy=False).tobytes());scale=int(meta['qmap'][by//2,bx//2] if axis==0 else meta['qmap'][by,bx]);quant=TABLES[(0 if axis==0 else 1,scale)]
    a=coeff.astype(np.int64)*quant;inverse,kind=inverse_tile(a);classes[kind]+=1;prediction,taps=prediction_tile(reference,meta['vectors'],meta['block_size'],axis,by,bx);fetches+=taps
    output[by*8:by*8+8,bx*8:bx*8+8]=np.clip(inverse+prediction,0,255).astype(np.int16)
   if not reader.finished or reader.failed or consumed!=count:raise ValueError('stream48 complete entropy consumption')
   try:next(reader)
   except StopIteration:pass
   else:raise ValueError('stream48 extra tile')
   reconstructed.append(output);hashes.append(coefficient_hash.hexdigest());work.append(dict(plane=axis,blocks=bh*bw,consumed_blocks=consumed,dispatch=payload[0],prediction_reference_sample_fetches=fetches,inverse_classes=classes,coefficient_tile_bytes=128,full_coefficient_array_staged=False,full_prediction_array_staged=False,retained_AB38_bytes=len(payload)-1))
  rebuilt=tuple(reconstructed)
  if m.C.reference_tag(rebuilt)!=meta['base_tag']:raise ValueError('stream48 pre-normalization tag')
  normalized=h.f.f.normalize(rebuilt)
  if m.C.reference_tag(normalized)!=meta['output_tag']:raise ValueError('stream48 normalized tag')
  patches,_=h.f.f.hud.decode_hud(meta['hud'],None if key else self.hud,expected_epoch=25,expected_reference_id=None if key else self.rid)
  owned=[]
  for patch in patches:
   words=patch['words'].copy();words.setflags(write=False);owned.append(dict(patch,words=words))
  for plane in normalized:plane.setflags(write=False)
  patches=tuple(owned);meta.update(coefficient_sha256=hashes,decode_work=dict(planes=work,receive_ms=(time.perf_counter_ns()-start)/1e6,entropy_reencode_calls=0,full_coefficient_array_bytes=0,full_prediction_array_bytes=0,external_model_reference_bytes=0 if reference is None else sum(p.nbytes for p in reference),reconstruction_plane_bytes=sum(p.nbytes for p in rebuilt),normalized_plane_bytes=sum(p.nbytes for p in normalized),complete_checks_before_publication=True))
  self.ref,self.rid,self.hud,self.last=normalized,fid,patches,fid
  return normalized,patches,meta,3
