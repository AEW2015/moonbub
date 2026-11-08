"""Prepare only the first N decoded local frames as explicit centered canvases."""
from pathlib import Path
import argparse, hashlib, json, sys
sys.dont_write_bytecode=True
import av
import numpy as np
from PIL import Image

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--count',type=int,default=3)
    a=p.parse_args()
    if not 1<=a.count<=12: raise ValueError('bounded count1..12')
    if a.output.exists() or a.output.with_suffix('.json').exists(): raise ValueError('fresh outputs required')
    source_hash=hashlib.sha256(a.input.read_bytes()).hexdigest()
    frames=[];records=[]
    with av.open(str(a.input)) as container:
        for frame in container.decode(video=0):
            rgb=frame.to_ndarray(format='rgb24')
            active=np.asarray(Image.fromarray(rgb).resize((720,405),Image.Resampling.BILINEAR))
            canvas=np.zeros((480,720,3),np.uint8);canvas[37:442]=active
            records.append(dict(decoded_ordinal=len(frames),pts=frame.pts,time_base=str(frame.time_base),original_width=frame.width,original_height=frame.height,canvas_rgb24_sha256=hashlib.sha256(canvas.tobytes()).hexdigest()))
            frames.append(canvas)
            if len(frames)==a.count: break
    if len(frames)!=a.count: raise ValueError('source too short; no looping')
    a.output.parent.mkdir(parents=True,exist_ok=True)
    np.save(a.output,np.stack(frames),allow_pickle=False)
    result=dict(source=str(a.input.resolve()),source_sha256=source_hash,count=a.count,selection='first decoded frames, offset0, no loop, no temporal resampling',canvas=[720,480],viewport=[0,37,720,405],resampler='Pillow bilinear',frames=records,array_sha256=hashlib.sha256(a.output.read_bytes()).hexdigest())
    a.output.with_suffix('.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
