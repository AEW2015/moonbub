#!/usr/bin/env python3
"""Compare retained output/event identity across two completed cadence runs."""
from pathlib import Path
import hashlib,json,sys
base,candidate=(Path(p) for p in sys.argv[1:3])
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
prefixes=('ARRIVAL ','ADMITTED ','DECODE ','PRESENT_PASS ','CADENCE_RESULT')
def events(path):
 return [x for x in (path/'run.log').read_text().splitlines() if x.startswith(prefixes)]
a,b=events(base),events(candidate)
frames=[]
for f in sorted((candidate/'dumps').glob('*.txt')):
 original=base/'dumps'/f.name
 x,y=digest(original),digest(f)
 frames.append({'id':f.stem,'original_sha256':x,'candidate_sha256':y,'match':x==y})
assert len(frames)==10 and all(f['match'] for f in frames) and len(a)==41 and a==b
print(json.dumps({'scope':'ten synthetic frames in behavioral Verilator; C model related to RTL; no hardware',
                  'events_identical':True,'event_count':len(a),'frames':frames},indent=2))
