"""Validated prediction views only; no receiver/profile/global changes."""
import numpy as np
import helpers as h
SHAPES=((480,720),(240,360),(240,360))
_KEY=np.frombuffer(bytes((128,0)),dtype='<i2')
def key_prediction():
 return tuple(np.broadcast_to(_KEY.reshape(()),shape)for shape in SHAPES)
def predict(reference,vectors,block_size=16):
 if type(reference)is not tuple or len(reference)!=3:raise ValueError('published reference tuple')
 for image,shape in zip(reference,SHAPES,strict=True):
  if not isinstance(image,np.ndarray)or image.shape!=shape or image.dtype!=np.int16 or image.flags.writeable or np.any(image<0)or np.any(image>255):raise ValueError('readonly bounded int16 canonical bank')
 mw,mh=h.m.base._grid(720,480,block_size)
 if not isinstance(vectors,np.ndarray)or vectors.dtype!=np.int8 or vectors.shape!=(mh,mw,2)or np.any(np.abs(vectors.astype(np.int16))>h.m.base.LIMIT):raise ValueError('bounded int8 grid')
 if not np.any(vectors):return reference
 return h.m.predict(reference,vectors,block_size)
