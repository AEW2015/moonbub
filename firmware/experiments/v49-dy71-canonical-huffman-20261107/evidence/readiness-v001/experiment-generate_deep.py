from pathlib import Path
import json,random
root=Path('C:/moon/maintenance/v49-canonical-huffman');base=json.loads((root/'cases.json').read_text());rng=random.Random(49116);deep=[]
valid=[x for x in base if x['expected']is not None and x['name'].startswith(('tree','full','depth'))]
for c in valid:
 blob=bytes.fromhex(c['blob']);ns=int.from_bytes(blob[:2],'little');data=6+2*ns
 for mode in range(6):
  b=bytearray(blob)
  if mode==0:b[2+rng.randrange(4)]^=1<<rng.randrange(8)
  elif mode==1:b[6+2*rng.randrange(ns)]^=1<<rng.randrange(8)
  elif mode==2:b[7+2*rng.randrange(ns)]^=1<<rng.randrange(5)
  elif mode==3 and len(b)>data:b[data+rng.randrange(len(b)-data)]^=1<<rng.randrange(8)
  elif mode==4:del b[-rng.randrange(1,min(8,len(b)-1)+1):]
  else:b.extend(b'\x01')
  deep.append({'name':c['name']+'-mut'+str(mode),'count':c['count'],'maximum':c['maximum'],'blob':b.hex()})
(root/'deep-cases.tsv').write_text(''.join(f"{c['name']}\t{c['count']}\t{c['maximum']}\t{c['blob']}\t-\n"for c in deep))
print(len(deep))
