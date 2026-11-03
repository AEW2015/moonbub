#!/usr/bin/env python3
"""Prepare local gameplay-derived restricted JPEGs; source video is not distributed."""
import argparse, hashlib, json, subprocess, sys
from pathlib import Path
from PIL import Image, __version__ as pillow_version
root=Path(__file__).resolve().parents[5]
sys.path.insert(0,str(root/'host'))
from moonshine.encoding import encode,validate_jpeg
p=argparse.ArgumentParser();p.add_argument('video',type=Path);p.add_argument('output',type=Path);p.add_argument('--ffmpeg',required=True);p.add_argument('--frames',type=int,default=10);p.add_argument('--start',type=float,default=1.0);p.add_argument('--quality',type=int,default=65);p.add_argument('--sample-fps',type=int,default=30);a=p.parse_args()
if not 1<=a.frames<=1800 or a.start<0 or not 1<=a.quality<=95 or not 1<=a.sample_fps<=120:p.error('invalid bounds')
if a.output.exists() and any(a.output.iterdir()):p.error('output must be empty')
a.output.mkdir(parents=True,exist_ok=True)
cmd=[a.ffmpeg,'-v','error','-ss',str(a.start),'-i',str(a.video),'-vf',f'fps={a.sample_fps},scale=720:405:flags=lanczos,pad=720:480:0:37:black','-frames:v',str(a.frames),'-f','rawvideo','-pix_fmt','rgb24','pipe:1']
proc=subprocess.Popen(cmd,stdout=subprocess.PIPE)
rows=[];size=720*480*3
try:
 for i in range(a.frames):
  raw=proc.stdout.read(size)
  if len(raw)!=size:raise RuntimeError(f'short decoded frame {i}: {len(raw)} bytes')
  jpeg=encode(Image.frombytes('RGB',(720,480),raw),quality=a.quality,subsampling='420');validate_jpeg(jpeg)
  digest=hashlib.sha256(jpeg).hexdigest();(a.output/f'{i:04}.jpg').write_bytes(jpeg)
  rows.append({'id':i,'jpeg_bytes':len(jpeg),'jpeg_sha256':digest,'pts_num':i,'pts_den':30})
 rc=proc.wait()
 if rc:raise RuntimeError(f'ffmpeg exit {rc}')
finally:
 if proc.poll() is None:proc.kill();proc.wait()
manifest={'format_version':1,'frames':rows,'pillow_version':pillow_version,'source':'local gameplay clip, not redistributed','video_sha256':hashlib.sha256(a.video.read_bytes()).hexdigest(),'start_s':a.start,'fps':30,'source_sampling_fps':a.sample_fps,'width':720,'height':480,'quality':a.quality,'sampling':'420','transformation':f'ffmpeg fps={a.sample_fps}, scale=720x405, centered vertical pad to 720x480; replay at 30 Hz'}
(a.output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'count':len(rows),'min_bytes':min(r['jpeg_bytes'] for r in rows),'max_bytes':max(r['jpeg_bytes'] for r in rows),'distinct_jpegs':len({r['jpeg_sha256'] for r in rows})}))
