"""Defined error diagnostics, not perceptual flicker/SSIM/subjective ratings."""
import numpy as np
WIDTH,HEIGHT=720,480
class Diagnostics:
 def __init__(self,rectangles):
  self.previous=None;self.rows=[];active=np.zeros((HEIGHT,WIDTH),bool);active[37:442]=True;outside=active.copy()
  for x,y,w,h in rectangles:outside[y:y+h,x:x+w]=False
  self.active=active;self.xpairs=outside[:,1:]&outside[:,:-1];self.ypairs=outside[1:]&outside[:-1];self.xgrid=(np.arange(1,WIDTH)%8==0)[None,:];self.ygrid=(np.arange(1,HEIGHT)%8==0)[:,None]
 def add(self,original,decoded):
  if original.shape!=(480,720,3) or decoded.shape!=original.shape or original.dtype!=np.uint8 or decoded.dtype!=np.uint8:raise ValueError('expanded fixed RGB565 uint8 triples')
  error=decoded.astype(np.int32)-original.astype(np.int32);a=error[self.active].astype(np.int64);samples=a.size;SSE=int(np.square(a).sum());large=int(np.count_nonzero(np.max(np.abs(error),axis=2)[self.active]>=16))
  dx=np.square(error[:,1:].astype(np.int64)-error[:,:-1]).sum(axis=2);dy=np.square(error[1:].astype(np.int64)-error[:-1]).sum(axis=2)
  grid_SSE=int(dx[self.xpairs&self.xgrid].sum()+dy[self.ypairs&self.ygrid].sum());nongrid_SSE=int(dx[self.xpairs&~self.xgrid].sum()+dy[self.ypairs&~self.ygrid].sum());grid_samples=3*(int((self.xpairs&self.xgrid).sum())+int((self.ypairs&self.ygrid).sum()));nongrid_samples=3*(int((self.xpairs&~self.xgrid).sum())+int((self.ypairs&~self.ygrid).sum()))
  temporal_SSE=None if self.previous is None else int(np.square((error-self.previous)[self.active].astype(np.int64)).sum())
  row=dict(active_SSE=SSE,active_samples=samples,active_MSE=SSE/samples,active_large_error_pixels=large,active_pixels=int(self.active.sum()),grid8_error_jump_SSE=grid_SSE,grid8_error_jump_samples=grid_samples,nongrid_error_jump_SSE=nongrid_SSE,nongrid_error_jump_samples=nongrid_samples,coordinate_temporal_error_change_SSE=temporal_SSE,coordinate_temporal_error_change_samples=0 if temporal_SSE is None else samples)
  self.previous=error;self.rows.append(row);return row
 def summary(self):
  if not self.rows:raise ValueError('nonempty diagnostic stream')
  total={k:sum(r[k] for r in self.rows if r[k] is not None) for k in self.rows[0] if k not in('active_MSE',)}
  total.update(frames=len(self.rows),active_MSE=total['active_SSE']/total['active_samples'],large_error_pixel_fraction=total['active_large_error_pixels']/total['active_pixels'],grid8_error_jump_MSE=total['grid8_error_jump_SSE']/total['grid8_error_jump_samples'],nongrid_error_jump_MSE=total['nongrid_error_jump_SSE']/total['nongrid_error_jump_samples'],coordinate_temporal_error_change_MSE=None if total['coordinate_temporal_error_change_samples']==0 else total['coordinate_temporal_error_change_SSE']/total['coordinate_temporal_error_change_samples'])
  return total
