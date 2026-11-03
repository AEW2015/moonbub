"""Bit-exact GM01/HG01 reconstruction with zero/DC-only inverse bypass.

Frozen coefficient syntax, prediction, quantization and color arithmetic remain
unchanged. No new packet format, approximation or target throughput claim.
"""
from pathlib import Path
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
for folder in ('python-game-codec-study','python-game-hybrid-study'):
    sys.path.insert(0,str(HERE.parent/folder))
import game_codec as gm
import hybrid_codec as hybrid

TABLES=tuple(np.stack([gm.ft.qtable(scale,chroma) for scale in gm.roi.SCALES]) for chroma in (False,True))
for table in TABLES:table.setflags(write=False)


def dc_inverse(values):
    """Exact frozen two-pass Q14 rounding for dequantized DC values."""
    dc=np.asarray(values,dtype=np.int64)
    return (5793*((dc*5793+8192)>>14)+8192)>>14


def reconstruct(coefficients,prediction,scale_map,w,h,*,return_stats=False):
    gm.roi.check_map(scale_map,w,h)
    if len(coefficients)!=3 or len(prediction)!=3:raise ValueError('three coefficient/prediction planes')
    output=[];stats=[]
    for i,(c,pred) in enumerate(zip(coefficients,prediction)):
        pw,ph=(w,h) if i==0 else (w//2,h//2)
        bw,bh=(pw+7)//8,(ph+7)//8;n=bw*bh
        if c.dtype!=np.int16 or c.shape!=(n,8,8) or pred.shape!=(ph,pw):
            raise ValueError('coefficient/prediction geometry')
        flat=c.reshape(n,64)
        mixed=np.any(flat[:,1:]!=0,axis=1)
        dc_only=~mixed & (flat[:,0]!=0)
        zero=~mixed & ~dc_only
        scale_indices=np.searchsorted(gm.roi.SCALES,gm.roi.block_scales(scale_map,w,h,i))
        table=TABLES[0 if i==0 else 1]
        residual=np.zeros((n,8,8),np.int64)
        if np.any(dc_only):
            dc=c[dc_only,0,0].astype(np.int64)*table[scale_indices[dc_only],0,0]
            residual[dc_only]=dc_inverse(dc)[:,None,None]
        if np.any(mixed):
            residual[mixed]=gm.ft.inverse(c[mixed].astype(np.int64)*table[scale_indices[mixed]])
        samples=residual.reshape(bh,bw,8,8).transpose(0,2,1,3).reshape(bh*8,bw*8)[:ph,:pw]
        plane=np.clip(pred+samples,0,255).astype(np.int16);plane.setflags(write=False);output.append(plane)
        stats.append({'plane':i,'blocks':n,'zero':int(zero.sum()),'dc_only':int(dc_only.sum()),
                      'general_inverse':int(mixed.sum()),'baseline_inverse_blocks':n,
                      'bypass_blocks':int((zero|dc_only).sum())})
    result=tuple(output)
    return (result,stats) if return_stats else result


class Receiver:
    def __init__(self,epoch=1):
        if type(epoch) is not int or not 0<=epoch<gm.NO_REF:raise ValueError('GM01 receiver epoch')
        self.epoch=epoch;self.anchor_id,self._anchor=None,None;self.last_frame_id=-1;self.last_stats=None
    def receive(self,packet):
        p=gm.parse(packet,self.epoch);w,h=p['width'],p['height'];frame=p['frame_id']
        if frame<=self.last_frame_id:raise ValueError('GM01 replay/regression')
        if p['key']:prediction=tuple(np.full(shape,128,np.int16) for shape in ((h,w),(h//2,w//2),(h//2,w//2)))
        else:
            if p['reference_id']!=self.anchor_id or self._anchor is None or self._anchor[0].shape!=(h,w):
                raise ValueError('GM01 missing exact anchor')
            prediction=tuple(gm.mt.predict(self._anchor,p['dx'],p['dy']))
        planes,stats=reconstruct(p['coefficients'],prediction,p['scale_map'],w,h,return_stats=True)
        rgb=gm.ft.planes_to_rgb(planes)
        if p['key']:self.anchor_id,self._anchor=frame,planes
        self.last_frame_id=frame;self.last_stats=stats
        return rgb,{'epoch':self.epoch,'frame_id':frame,'key':p['key'],'reference_id':None if p['key'] else p['reference_id'],
            'anchor_id':self.anchor_id,'width':w,'height':h,'dx':p['dx'],'dy':p['dy'],'map_bytes':p['map_bytes'],
            'bytes':len(packet),'retained_reference_array_bytes':sum(x.nbytes for x in self._anchor),
            'inverse_blocks':stats,'scope':'ExactGM01 arithmetic withzero/DCbypass; no target throughput or fit proof'}


class HybridReceiver(hybrid.Decoder):
    def __init__(self,epoch=1,frame_cap=49152):
        super().__init__(epoch,frame_cap)
        self.base=Receiver(epoch)
