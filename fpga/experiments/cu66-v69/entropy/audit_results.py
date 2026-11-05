#!/usr/bin/env python3
"""Check actual RTL transcripts against frozen selected AB38 work and fixtures."""
from pathlib import Path
import hashlib,json,re,zlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def records(path):
 text=path.read_text();assert 'TEST_FAIL'not in text and text.rstrip().splitlines()[-1].startswith('TEST_PASS '),path
 rows=[]
 for line in text.splitlines():
  if line.startswith('CASE_PASS '):rows.append({k:(v if k=='name'else int(v))for k,v in re.findall(r'(\w+)=([^ ]+)',line)})
 final={k:(v if k=='backend'else int(v))for k,v in re.findall(r'(\w+)=([^ ]+)',text.rstrip().splitlines()[-1])}
 assert final['cases']==len(rows)and final['valid']==sum(r['error']==0 for r in rows)and final['rejected']==sum(r['error']!=0 for r in rows)
 for key in ('cycles','decisions','renorm'):
  assert final[key]==sum(r[key]for r in rows)
 assert final['external_reads']==sum(r['reads']for r in rows)and final['output_stalls']==sum(r['stalls']for r in rows)
 assert final['minimum']==min(r['cycles']for r in rows)and final['maximum']==max(r['cycles']for r in rows)
 return rows,final

def main():
 native_path=ROOT/'experiments/cu66-native-v69/manifest.json';native=json.loads(native_path.read_text())
 old_path=ROOT/'experiments/python-game-binary-qual-v40-study/results.json';old=json.loads(old_path.read_text());expected={};tilecount=0
 for c,n in zip(old['cases'],native['cases'],strict=True):
  assert c['scene']==n['scene']
  for r,nr in zip(c['rows'],n['rows'],strict=True):
   assert r['id']==nr['id']
   for axis,(attempt,p)in enumerate(zip(r['attempts'],nr['planes'],strict=True)):
    selected=attempt['trials'][attempt['selected']-1];assert attempt['selected']in(1,2)
    data=(native_path.parent/p['packet']['path']).read_bytes();assert hashlib.sha256(data).hexdigest()==selected['packet']['raw_sha256']==p['packet']['sha256']
    packed=(native_path.parent/p['expected_coefficients']['path']).read_bytes();plain=zlib.decompress(packed)
    assert hashlib.sha256(packed).hexdigest()==p['expected_coefficients']['sha256']and hashlib.sha256(plain).hexdigest()==p['expected_coefficients_raw_sha256']and len(plain)==p['blocks']*128
    assert p['dispatch']==(6 if selected['compact']else 5)
    raw=data[5]==1;decisions=0 if raw else selected['work']['probability_products'];renorm=0 if raw else selected['work']['renorm_steps']
    reads=2*len(data)-(46 if raw else 42);name=c['scene']+'_'+str(r['id'])+'_'+str(axis)
    expected[name]=dict(decisions=decisions,renorm=renorm,reads=reads,tiles=p['blocks']);tilecount+=p['blocks']
 runs=[];lognames=[]
 for seed in(6901,6902):
  path=HERE/('actual-seed'+str(seed)+'.log');rr,total=records(path);assert len(rr)==len(expected)==1371
  frames={};cohorts={}
  for row in rr:
   assert row['seed']==seed and row['error']==0
   for k,want in expected[row['name']].items():assert row[k]==want,(row['name'],k,row[k],want)
   name=row['name'].rsplit('_',1)[0];frames[name]=frames.get(name,0)+row['cycles']
  assert len(frames)==457
  for name,value in frames.items():
   cohort=name.rsplit('_',1)[0];cohorts.setdefault(cohort,[]).append(value)
  runs.append(dict(seed=seed,planes=1371,frames=457,clock_counts=total,
   frame_cycles=dict(minimum=min(frames.values()),maximum=max(frames.values()),mean=sum(frames.values())/457),
   cohorts={k:dict(frames=len(v),minimum=min(v),maximum=max(v),mean=sum(v)/len(v))for k,v in cohorts.items()}));lognames.append(path)
 for kind,seeds,count in(('directed',(6901,6902,6903),31),('stress',(6901,6902,6903),120)):
  for seed in seeds:
   path=HERE/(kind+'-seed'+str(seed)+'.log');rr,total=records(path);assert len(rr)==count and 'ABORT_RESET_PASS'in path.read_text()
   fixture=(HERE/(kind+'.tsv')).read_text().splitlines();assert len(fixture)==len(rr)
   for line,row in zip(fixture,rr,strict=True):
    fields=line.split('\t');assert row['name']==fields[0]and(row['error']!=0)==(fields[6]=='1')
    if fields[6]=='0':assert row['tiles']==int(fields[3])
   runs.append(dict(kind=kind,seed=seed,clock_counts=total));lognames.append(path)
 assert not re.search(r'%Warning|%Error', (HERE/'build.log').read_text())
 assert 'Found and reported 0 problems.'in(HERE/'yosys-proc.log').read_text()
 paths=[HERE/p for p in('cu66_ab38_decoder.sv','tb_entropy.cpp','export_fixtures.py','audit_results.py','run_regression.sh','fixture-evidence.json','actual.tsv','directed.tsv','stress.tsv','build.log','yosys-proc.log','environment.log')]+lognames+[native_path,old_path]
 result=dict(schema='cu66-ab38-entropy-rtl-v69',backend='Verilator 5.020',implementation='one shared arithmetic engine; four independent adaptive contexts',
  actual_planes_per_seed=1371,actual_frames_per_seed=457,actual_coefficient_tiles_per_seed=tilecount,actual_coefficient_samples_per_seed=tilecount*64,
  runs=runs,source_sha256={p.relative_to(ROOT).as_posix():sha(p)for p in paths},
  all_actual_coefficients_bit_exact=True,all_actual_decisions_renorm_reads_match_frozen_source=True,
  cycle_scope='actual clock edges with 0..7-cycle external byte response delay, 80% request ready and75% tile ready; one outstanding read; includes CRC preflight and all decoder work',
  crc_preflight_then_immutable_byte_bank=True,compact_hidden_scatter_external=True,
  routed_clock_or_target_fit_proven=False,full_frame_decode_or_physical_30fps_proven=False)
 (HERE/'results.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(dict(actual_planes_per_seed=1371,frames_per_seed=457,actual_tiles_per_seed=tilecount,actual_samples_per_seed=tilecount*64,
  full_seeds=2,directed_seeds=3,stress_seeds=3,per_plane_frozen_work_parity=True,source_pins=len(paths),routed_clock_or_physical_FPS_proven=False)))
if __name__=='__main__':main()
