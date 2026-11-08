from pathlib import Path
import numpy as np,hashlib,json,shutil
P=Path(__file__).resolve().parent.parent;O=P/'layout-v2';sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest();DIMS=[(720,480),(360,240),(360,240)]
def tile_std(data):
 assert len(data)==518400
 out=bytearray();base=0
 for w,h in DIMS:
  plane=data[base:base+w*h]
  for ty in range(0,h,8):
   for tx in range(0,w,8):
    for y in range(8):out.extend(plane[(ty+y)*w+tx:(ty+y)*w+tx+8])
  base+=w*h
 assert len(out)==518400;return bytes(out)
def tile_numpy(data):
 out=[];base=0
 for w,h in DIMS:
  a=np.frombuffer(data[base:base+w*h],dtype=np.uint8).reshape(h,w);out.append(a.reshape(h//8,8,w//8,8).transpose(0,2,1,3).tobytes());base+=w*h
 return b''.join(out)
def untile(data):
 out=bytearray(518400);base=0
 for w,h in DIMS:
  for y in range(h):
   for x in range(w):out[base+y*w+x]=data[base+(((y//8)*(w//8)+x//8)*64+(y%8)*8+x%8)]
  base+=w*h
 return bytes(out)
known=Path('C:/moon/maintenance/v45-sequence/qualification');known_rows=[]
for i in [0,1]:
 row=(known/f'frame{i}.yuv').read_bytes();want=(known/f'frame{i}.canonical.u16').read_bytes();assert tile_std(row)==tile_numpy(row)==want;assert untile(want)==row;known_rows.append({'id':i,'planar_sha256':sha(known/f'frame{i}.yuv'),'tiled_sha256':sha(known/f'frame{i}.canonical.u16'),'both_independent_converters_match_prequalified_actual_bank_golden':True})
probe=hashlib.shake_256(b'STB1-independent-bank-layout-20261108').digest(518400);assert tile_std(probe)==tile_numpy(probe);assert untile(tile_std(probe))==probe
pack=Path('C:/moon/dev/experiments/cu66-source-bridge-20261108/package12');m=json.loads((pack/'manifest.json').read_text());out=O/'goldens';out.mkdir(exist_ok=False);rows=[]
for i,r in enumerate(m['frames']):
 planar=(P/'goldens'/f'frame{i}.canonical.u16').read_bytes();assert hashlib.sha256(planar).hexdigest()==r['canonical_yuv_u8_sha256'];a=tile_std(planar);assert a==tile_numpy(planar);assert untile(a)==planar
 (out/f'frame{i}.yuv').write_bytes(planar);(out/f'frame{i}.canonical.u16').write_bytes(a)
 for ext,key in [('hud','hud_words_u16le_sha256'),('rgb565','display_rgb565_u16le_sha256')]:
  src=P/'goldens'/f'frame{i}.{ext}';assert sha(src)==r[key];shutil.copy2(src,out/src.name)
 rows.append({'id':i,'planar_sha256':r['canonical_yuv_u8_sha256'],'tile_major_sha256':hashlib.sha256(a).hexdigest(),'two_converter_agreement':True,'inverse_roundtrip_exact':True})
rtl=Path('C:/moon/builds/stb1-v001/inputs/fpga/experiments/cu66-v71/direct-system/grouped-v001/source/cu71_tile_memory_direct.sv');mapfile=Path('C:/moon/builds/stb1-v001/inputs/fpga/experiments/cu66-v70/memory/cu70_memory_map.svh');sources=[Path(__file__),known/'prepare.py',known/'manifest.json',rtl,mapfile]
(O/'independent-layout-proof.json').write_text(json.dumps({'status':'PASS_PREQUALIFIED_PAIR_AND_TWO_INDEPENDENT_SERIALIZERS_NEW12','formula':'Y720x480/U360x240/V360x240; tile-major8x8, tile=(y//8)*(width//8)+x//8, byte=plane_base+tile*64+(y%8)*8+x%8; u16 low/high adjacentx bytes','selected_memory_map':'plane word offsets0/172800/216000,32words/tile','DUT_outputs_read':False,'prequalified_pair':known_rows,'new_frames':rows,'random_coordinate_roundtrip_bytes':518400,'package_manifest_sha256':sha(pack/'manifest.json'),'source_sha256':{str(f):sha(f)for f in sources},'goldens_sha256':{str(f.relative_to(P)):sha(f)for f in out.iterdir()}},indent=2));print('PASS independently proved bank serialization; original planar goldens unchanged')
