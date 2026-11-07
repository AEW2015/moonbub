#!/usr/bin/env python3
"""Pin native canonical SDRAM preloads and ordered logical16-byte requests."""
import gzip,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];AREA=Path(__file__).resolve().parent
CANON=ROOT/'fpga/experiments/cu66-v91k-lines/comparison-attempts/20261106T223415479309Z-7a2603de/inputs/canonical_actual.tsv.gz'
SCHEDULE=ROOT/'experiments/python-gamebub-v91l-tiled/vectors/prefill-lines.hex.gz'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def physical(a):
 base,width=(0,720) if a<345600 else (345600,360) if a<432000 else (432000,360)
 y,x=divmod(a-base,width)
 return base+((y//8)*(width//8)+x//8)*64+(y%8)*8+x%8
frames={}
with gzip.open(CANON,'rt') as f:
 for line in f:
  n,p,h=line.rstrip().split('\t')
  if p=='0' and n in ('actual_001','actual_006'):frames[n]=bytes.fromhex(h)
with gzip.open(SCHEDULE,'rt') as f:addresses=[int(x,16) for x in f]
assert len(frames)==2 and len(addresses)==32400 and len(set(addresses))==32400
preload=[];requests=[];metadata=[]
for bank,(name,data) in enumerate(frames.items()):
 assert len(data)==518400
 memory=bytearray(518400)
 for a,v in enumerate(data):memory[physical(a)]=v
 preload.append('@%06x\n'%(bank<<22))
 preload.extend('%04x\n'%int.from_bytes(memory[a:a+2],'little') for a in range(0,518400,2))
 for a in addresses:requests.append('%040x\n'%((bank<<147)|(a<<128)|int.from_bytes(data[a:a+16],'little')))
 metadata.append(dict(bank=bank,name=name,canonical_sha256=hashlib.sha256(data).hexdigest(),tile_sha256=hashlib.sha256(memory).hexdigest(),logical_lines=32400))
artifacts={}
for name,raw in (('preload.hex.gz',''.join(preload).encode()),('native-lines.hex.gz',''.join(requests).encode())):
 p=AREA/name;p.write_bytes(gzip.compress(raw,mtime=0));artifacts[name]=dict(gzip_sha256=sha(p),raw_sha256=hashlib.sha256(raw).hexdigest(),rows=len(raw.splitlines()))
result=dict(schema='cu66-v91l-readbridge-fixtures-v1',status='PASS_PINNED_NATIVE_PRELOAD_AND_LOGICAL_LINES',generator_sha256=sha(Path(__file__)),inputs={str(CANON.relative_to(ROOT)):sha(CANON),str(SCHEDULE.relative_to(ROOT)):sha(SCHEDULE)},frames=metadata,artifacts=artifacts,scope='Testbench direct SDRAM model preload outside frame fences, not physical write integration.')
(AREA/'fixtures.json').write_text(json.dumps(result,indent=2)+'\n');print(result['status'])
