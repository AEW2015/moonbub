"""First six v40 frames of each cohort, both AB38 representations, actual streams."""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys,time,zlib
import numpy as np
import model as m
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];SOURCE=HERE.parent/'python-game-binary-qual-v40-study'
def mod(n,p):
 s=importlib.util.spec_from_file_location(n,p);v=importlib.util.module_from_spec(s);sys.modules[n]=v;s.loader.exec_module(v);return v
dec=mod('rice46_frozen_decode',HERE.parent/'python-game-binary-v38-study/decoder.py')
def digest(b):return hashlib.sha256(b).hexdigest()
def raw(folder,d):
 stored=(folder/d['path']).read_bytes();assert digest(stored)==d['stored_sha256'];z=zlib.decompressobj();b=z.decompress(stored,d['raw_bytes']+1);assert z.eof and not z.unused_data and not z.unconsumed_tail and len(b)==d['raw_bytes'] and digest(b)==d['raw_sha256'];return b
def blob(b):
 stored=zlib.compress(b,9);p='objects/'+digest(stored)+'.zlib';(HERE/'objects').mkdir(exist_ok=True);(HERE/p).write_bytes(stored);return dict(path=p,raw_bytes=len(b),raw_sha256=digest(b),stored_sha256=digest(stored))
def pins():
 d=json.loads((SOURCE/'results.json').read_text());paths={ROOT/p for p in d['source_pins_sha256']};paths|={SOURCE/'results.json',HERE/'model.py',HERE/'benchmark.py',HERE/'test_model.py',HERE.parent/'python-game-binary-v38-study/model.py',HERE.parent/'python-game-binary-v38-study/decoder.py'};return{p.relative_to(ROOT).as_posix():digest(p.read_bytes()) for p in sorted(paths)}
def main():
 before=pins();source=json.loads((SOURCE/'results.json').read_text());cases=[]
 for case in source['cases']:
  rows=[]
  for frame in case['rows'][:6]:
   planes=[]
   for plane in frame['attempts']:
    alternatives=[]
    for trial in plane['trials']:
     original=raw(SOURCE,trial['packet']);header=dec.FRAME.unpack_from(original);n,bw=header[3:5];coeff=dec.decode(original,n,bw);packet,baseline,trials,work=m.encode(coeff,bw);assert baseline==original;np.testing.assert_array_equal(dec.decode(packet,n,bw),coeff)
     for t in trials:
      for c in t['candidates']:c['packet']=blob(c['packet'])
     alternatives.append(dict(compact=trial['compact'],source_packet=trial['packet'],packet=blob(packet),old_bytes=len(original),bytes=len(packet),blocks=n,blocks_w=bw,coefficient_sha256=digest(coeff.astype('<i2').tobytes()),trials=trials,work=work))
    planes.append(dict(plane=plane['plane'],alternatives=alternatives))
   rows.append(dict(id=frame['id'],planes=planes));print(json.dumps(dict(scene=case['scene'],frame=frame['id'],bytes_saved=sum(a['old_bytes']-a['bytes'] for p in planes for a in p['alternatives']))),flush=True)
  cases.append(dict(scene=case['scene'],rows=rows))
 assert pins()==before
 summary=dict(frames=sum(len(c['rows']) for c in cases),AB38_packets=sum(len(p['alternatives']) for c in cases for r in c['rows'] for p in r['planes']),old_component_bytes=sum(a['old_bytes'] for c in cases for r in c['rows'] for p in r['planes'] for a in p['alternatives']),searched_component_bytes=sum(a['bytes'] for c in cases for r in c['rows'] for p in r['planes'] for a in p['alternatives']),attempted_stream_encodes=sum(a['work']['attempted_stream_encodes'] for c in cases for r in c['rows'] for p in r['planes'] for a in p['alternatives']),changed_streams=sum(a['work']['stream_changes'] for c in cases for r in c['rows'] for p in r['planes'] for a in p['alternatives']))
 (HERE/'results.json').write_text(json.dumps(dict(schema='gamebub-rice-search-v46',source_sha256=before,cases=cases,summary=summary,scope=['Fixedfirst6frames/cohort,notunseenorfullhistoryqualification.','SameAB38syntax/decoder,exactcoefficients,baselinefirstonbyte-ties;actualstreamlengthsearchwithin±1ofuncodedRicek.','Allattemptedstreamencodeworkpaid/archived;notwholeframesenderorFPGA30fpsproof.','ComponenttotalsincludeBOTHfull/compactlosers;completeframeselectionmustbemeasuredseparatelybeforeclaimingstreambytesavings.']),indent=2)+'\n');print(json.dumps(summary),flush=True)
if __name__=='__main__':main()
