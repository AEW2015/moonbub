"""Replay every archived AB38 full/compact trial through a one-tile iterator."""
from pathlib import Path
import hashlib,json,struct,time,zlib
import decoder as new
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
INPUTS=('binary-v38','binary-full-v39','binary-qual-v40')
def digest(b):return hashlib.sha256(b).hexdigest()
def raw(folder,d):
 packed=(folder/d['path']).read_bytes();assert digest(packed)==d['stored_sha256'];obj=zlib.decompressobj();b=obj.decompress(packed,d['raw_bytes']+1);assert obj.eof and not obj.unused_data and not obj.unconsumed_tail and len(b)==d['raw_bytes'] and digest(b)==d['raw_sha256'];return b
def pins():
 paths={HERE/'decoder.py',HERE/'benchmark.py',HERE.parent/'python-game-binary-v38-study/decoder.py'}
 for name in INPUTS:
  p=HERE.parent/('python-game-'+name+'-study/results.json');d=json.loads(p.read_text());paths.add(p)
  for r in d.get('source_sha256',d.get('source_pins_sha256',{})):paths.add(ROOT/r)
 return{p.relative_to(ROOT).as_posix():digest(p.read_bytes()) for p in sorted(paths)}
def consume(packet,n,bw):
 r=new.TileReader(packet,n,bw);h=hashlib.sha256();count=0
 for tile in r:h.update(tile.astype('<i2',copy=False).tobytes());count+=1
 assert count==n and r.finished and not r.failed
 return h.hexdigest(),r.logical_workspace()
def main():
 before=pins();rows=[];target=HERE/'results.json'
 for cohort in INPUTS:
  folder=HERE.parent/('python-game-'+cohort+'-study');d=json.loads((folder/'results.json').read_text())
  for case in d['cases']:
   for frame in case['rows']:
    for plane in frame['attempts']:
     for trial in plane['trials']:
      packet=raw(folder,trial['packet']);header=new.frozen.FRAME.unpack_from(packet);n,bw=header[3:5]
      # Alternate order by retained trial index. One measured pair/trial is diagnostic.
      if len(rows)%2:
       start=time.perf_counter_ns();actual,work=consume(packet,n,bw);tile_ms=(time.perf_counter_ns()-start)/1e6
       start=time.perf_counter_ns();old=new.frozen.decode(packet,n,bw);array_ms=(time.perf_counter_ns()-start)/1e6
      else:
       start=time.perf_counter_ns();old=new.frozen.decode(packet,n,bw);array_ms=(time.perf_counter_ns()-start)/1e6
       start=time.perf_counter_ns();actual,work=consume(packet,n,bw);tile_ms=(time.perf_counter_ns()-start)/1e6
      expected=digest(old.astype('<i2',copy=False).tobytes());assert actual==expected
      rows.append(dict(cohort=cohort,scene=case['scene'],id=frame['id'],plane=plane['plane'],compact=trial['compact'],packet=trial['packet'],packet_folder=folder.relative_to(ROOT).as_posix(),blocks=n,blocks_w=bw,coefficient_sha256=actual,array_decode_ms=array_ms,tile_decode_and_digest_ms=tile_ms,workspace=work,raw=bool(header[2])))
    if frame['id']%24==0:print(json.dumps(dict(cohort=cohort,scene=case['scene'],frame=frame['id'],verified_trials=len(rows))),flush=True)
  assert pins()==before
  target.write_text(json.dumps(dict(schema='gamebub-block-rx-v44',source_sha256=before,rows=rows,complete=False,physical_30fps_proven=False),indent=2)+'\n')
 summary=dict(trials=len(rows),coefficient_tiles=sum(r['blocks'] for r in rows),full_trials=sum(not r['compact'] for r in rows),compact_trials=sum(r['compact'] for r in rows),raw_trials=sum(r['raw'] for r in rows),mean_array_decode_ms=sum(r['array_decode_ms'] for r in rows)/len(rows),mean_tile_decode_and_digest_ms=sum(r['tile_decode_and_digest_ms'] for r in rows)/len(rows),maximum_compressed_packet_bytes=max(r['workspace']['retained_compressed_input_bytes'] for r in rows),all_exact_coefficients=True)
 target.write_text(json.dumps(dict(schema='gamebub-block-rx-v44',source_sha256=before,rows=rows,summary=summary,complete=True,physical_30fps_proven=False,scope=['SameAB38wireandfrozenarithmeticprimitive;newfourstreamblockdeliveryonly.','One128Bcoefficienttilelogicalstaging;retainscompressedinput+4arithstates+3pendingevents;notPythonheap/wholedecoder/FPGAfit.','Singlealternatingpair/trial,iteratorhashpaidherebutoldarrayhashoutsideitsclock;notcontrolledspeeduporendtoendFPSproof.']),indent=2)+'\n');print(json.dumps(summary),flush=True)
if __name__=='__main__':main()
