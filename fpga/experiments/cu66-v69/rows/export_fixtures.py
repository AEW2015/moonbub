#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,os,struct,zlib,importlib.util
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];HASH=HERE.parent/'hash'
def main():
 rows=[]
 spec=importlib.util.spec_from_file_location('rows69_frozen_hash67',ROOT/'experiments/python-game-hash-stream-v67-study/model.py');oracle=importlib.util.module_from_spec(spec);spec.loader.exec_module(oracle)
 for line in(HASH/'fixtures.tsv').read_text().splitlines():
  name,path,size,tag=line.split('\t')
  if name.startswith('canonical_'):
   rows.append((name,os.path.relpath(HASH/path,HERE),size,tag))
 data=bytearray(struct.pack('<HH',720,480))
 for plane,(height,width)in enumerate(((480,720),(240,360),(240,360))):
  yy,xx=np.indices((height,width));data.extend(((plane*73+yy*17+xx*3)%256).astype(np.uint8).tobytes())
 packed=zlib.compress(bytes(data),9);folder=HERE/'fixtures';folder.mkdir(exist_ok=True);path=folder/(hashlib.sha256(packed).hexdigest()+'.zlib');path.write_bytes(packed)
 rows.append(('canonical_coordinate_pattern','fixtures/'+path.name,str(len(data)),hashlib.sha256(data).hexdigest()))
 assert len(rows)==7
 for name,path,size,tag in rows:
  raw=zlib.decompress((HERE/path).read_bytes());assert len(raw)==int(size)==518404 and raw[:4]==bytes((208,2,224,1))and hashlib.sha256(raw).hexdigest()==tag
  ctx=oracle.TileHash('CU66_u8');pos=4
  for plane,(height,width)in enumerate(((480,720),(240,360),(240,360))):
   image=np.frombuffer(raw[pos:pos+height*width],np.uint8).reshape(height,width);pos+=height*width
   for y in range(0,height,8):
    for x in range(0,width,8):ctx.feed(plane,y,x,image[y:y+8,x:x+8])
  assert ctx.finish().hex()==tag[:32]and ctx.work()['tiles']==8100
 (HERE/'fixtures.tsv').write_text('\n'.join('\t'.join(r)for r in rows)+'\n')
 inputs=[HASH/'fixtures.tsv',HASH/'fixture-evidence.json',HERE/'export_fixtures.py',ROOT/'experiments/python-game-hash-stream-v67-study/model.py']
 (HERE/'fixture-evidence.json').write_text(json.dumps(dict(schema='cu66-tile-rows-v69-fixtures',full_messages=7,actual_source_keys=4,
  source_sha256={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()for p in inputs},expected_message_bytes=518404,expected_full_grid_tiles=8100,python67_model_checked_tiles=56700),indent=2)+'\n')
 print(json.dumps(dict(full_messages=7,actual_source_keys=4,message_bytes=518404)))
if __name__=='__main__':main()
