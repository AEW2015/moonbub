"""Generate ROM-only HC70 Prepare fixtures and independent golden HUD CRCs. Read-only inputs."""
from pathlib import Path
import json,hashlib,struct,zlib,argparse
p=Path(__file__).resolve().parents[1]
a=argparse.ArgumentParser();a.add_argument('--packets',type=Path,required=True);a.add_argument('--goldens',type=Path,required=True);args=a.parse_args()
m=json.loads((args.packets/'manifest.json').read_text());out=p/'handheld/src/cu66/fixtures/prepare12';out.mkdir(exist_ok=True)
rows=[]
for i in range(12):
 f=m['frames'][i];b=(args.packets/f'frame{i}.cu66').read_bytes();assert hashlib.sha256(b).hexdigest()==f['files']['cu66']['sha256']
 fid,ref=struct.unpack_from('<II',b,8);nb,nh=struct.unpack_from('<II',b,68);hu=b[76+nb:76+nb+nh];assert fid==i and len(hu)==nh and len(b)==80+nb+nh
 h=bytearray(32);h[:4]=b'HC70';h[4:6]=bytes([1,1]);struct.pack_into('<IQIII',h,8,nh,i+1,fid,ref,b[5]&1);wire=h+hu;wire+=struct.pack('<I',zlib.crc32(wire));(out/f'prepare{i}.bin').write_bytes(wire)
 g=(args.goldens/f'frame{i}.hud').read_bytes();assert len(g)==42240
 rows.append({'id':i,'wire_bytes':len(wire),'wire_sha256':hashlib.sha256(wire).hexdigest(),'packet_sha256':hashlib.sha256(b).hexdigest(),'hud_sha256':hashlib.sha256(g).hexdigest(),'crc32':zlib.crc32(g)})
(out/'manifest.json').write_text(json.dumps({'origin':'packaged dy71-sequence-v3; independent fresh-reference HUD words','frames':rows},indent=2)+'\n')
(out/'cases.rs').write_text('const CASES:[(&[u8],u32);12]=[\n'+''.join(f'(include_bytes!("prepare{i}.bin"),{r["crc32"]}),\n' for i,r in enumerate(rows))+'];\n')
print('PREPARE12_GENERATED',len(rows),'ROM_BYTES',sum(r['wire_bytes'] for r in rows))
