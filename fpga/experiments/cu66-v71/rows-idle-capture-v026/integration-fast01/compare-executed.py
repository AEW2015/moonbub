"""Compare integrated simulation canonical SDRAM and LCD raster to native oracle."""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image
r=Path('C:/mb70/evidence/explore01-hardware-20261106-run01');o=Path('C:/mb70/fpga/experiments/cu66-v71/rows-idle-capture-v026/integration-fast01')
result={'scope':'OFFLINE_SIMULATION_ONLY; no physical canonical readback or optical pixel equality claim','canonical':[]}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for bank in range(3):
 p=o/f'canonical-bank{bank}.u16';actual=np.fromfile(p,dtype='<u2');assert actual.size==259200
 for frame in (0,1):
  ref=r/f'reference-canonical-frame{frame}.u16';expected=np.fromfile(ref,dtype='<u2');assert expected.size==259200
  row={'bank':bank,'reference_frame':frame,'actual_sha256':sha(p),'reference_sha256':sha(ref),'planes':[]}
  for plane,(start,end) in enumerate(((0,172800),(172800,216000),(216000,259200))):
   bad=np.flatnonzero(actual[start:end]!=expected[start:end])
   row['planes'].append(dict(plane=plane,mismatched_words=int(bad.size),total_words=end-start,first_relative_word=int(bad[0])if bad.size else None,actual_first=int(actual[start+bad[0]])if bad.size else None,expected_first=int(expected[start+bad[0]])if bad.size else None))
  result['canonical'].append(row)
actual=np.fromfile(o/'raster-portrait.u32',dtype='<u4');assert actual.size==384000 and not np.any(actual==0xffffffff)
actual=actual.reshape(480,800);canvas=actual[:,40:760]
rgb=np.stack(((canvas>>16)&255,(canvas>>8)&255,canvas&255),axis=-1).astype(np.uint8)
Image.fromarray(rgb).save(o/'simulated-lcd-frame1.png')
raw=np.array(Image.open(r/'reference-frame1.png'),dtype=np.uint16)
q=np.rint(raw*np.array([31,63,31])/255).astype(np.uint16)
expected=np.stack(((q[:,:,0]<<3)|(q[:,:,0]>>2),(q[:,:,1]<<2)|(q[:,:,1]>>4),(q[:,:,2]<<3)|(q[:,:,2]>>2)),axis=-1).astype(np.uint8)
bad=np.any(rgb!=expected,axis=-1)
result['raster']={'pixels':int(bad.size),'mismatched_pixels':int(np.count_nonzero(bad)),'first_yx':np.argwhere(bad)[0].tolist()if np.any(bad)else None,'actual_mean_rgb':rgb.mean(axis=(0,1)).tolist(),'expected_mean_rgb':expected.mean(axis=(0,1)).tolist(),'border_nonblack_pixels':int(np.count_nonzero(actual[:,:40]))+int(np.count_nonzero(actual[:,760:])),'simulation_raster_sha256':sha(o/'raster-portrait.u32')}
result['status']='PASS_EXACT_NATIVE_RASTER' if not np.any(bad) else 'FAIL_INTEGRATED_RASTER_MISMATCH'
(o/'comparison.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
