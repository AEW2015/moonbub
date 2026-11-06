#!/usr/bin/env python3
"""Independently audit retained BR primitives and all selected mixed-policy totals."""
from array import array
import gzip,hashlib,importlib.util,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];AREA=Path(__file__).resolve().parent
FIELDS=('decisions','renorm','stream_bytes','rice_values','events','raw_bytes','header_bytes','crc_bytes','emits','raw_bits','prob_init','plain_bits')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
def records(area,fields):
 index=json.loads((area/'index.json').read_text());p=area/index['data']['path'];assert sha(p)==index['data']['gzip_sha256'];digest=hashlib.sha256();count=0
 with gzip.open(p,'rb') as stream:
  while True:
   prefix=stream.read(4)
   if not prefix:break
   assert len(prefix)==4;n,=struct.unpack('<I',prefix);assert 0<n<=262144
   meta=stream.read(n);payload=stream.read(8100*5*fields*4);assert len(meta)==n and len(payload)==8100*5*fields*4
   digest.update(prefix);digest.update(meta);digest.update(payload);frame=json.loads(meta)
   assert frame['work_sha256']==hashlib.sha256(payload).hexdigest()
   assert all(frame[k]==index['frames'][count][k] for k in ('cohort','fid','ordinal','cap','work_sha256'))
   words=array('I');words.frombytes(payload)
   if sys.byteorder!='little':words.byteswap()
   count+=1;yield frame,words
 assert count==index['record_count'] and digest.hexdigest()==index['data']['raw_sha256']
def totals(words,fields,begin,end):
 stride=fields*5
 return [[sum(words[(begin*stride+part*fields+i):end*stride:stride]) for i in range(fields)] for part in range(5)]
def main():
 index=json.loads((AREA/'index.json').read_text());source=load('obs89_entropy',ROOT/'experiments/python-gamebub-v88/entropy/data.py')
 selected=json.loads((ROOT/'experiments/python-gamebub-v88/wire/results.json').read_text());rows={(r['policy'],r['cohort'],r['fid']):r for r in map(json.loads,(ROOT/selected['selected_report']).with_name('frames.jsonl').read_text().splitlines())}
 old=((f,w) for f,w in records(ROOT/'experiments/python-gamebub-v86/contexts',11) if f['cap']==65536)
 policies=('AB38_control','byte_min','feedback_overhead5','feedback_overhead15','all_BR88');global_work={p:[[0]*12 for _ in range(5)] for p in policies};mixed=[]
 count=chunks=0
 for (br,bw),(ab,aw),actual in zip(records(AREA,12),old,source.iter_frames(),strict=True):
  ident=br['cohort'],br['fid'];assert ident==(ab['cohort'],ab['fid'])==(actual['cohort'],actual['fid'])
  assert br['canonical_coefficients_sha256']==ab['canonical_coefficients_sha256']==actual['canonical_coefficients_sha256']
  btotal=totals(bw,12,0,8100)
  assert btotal[0]==[br['shared_totals'][k] for k in FIELDS]
  assert btotal[1:]==[[part[k] for k in FIELDS] for part in br['context_totals']]
  assert btotal[0][8]==8100 and btotal[0][7]==sum(len(c['br88']) for plane in actual['variants']['65536'] for c in plane)
  for c in range(4):
   assert all(btotal[c+1][i]==0 for i in (0,1,8,9,10))
   assert btotal[c+1][11]==sum(chunk['br88_bits'][c] for plane in actual['variants']['65536'] for chunk in plane)
   assert btotal[c+1][3]==sum(chunk['rice_values'][c] for plane in actual['variants']['65536'] for chunk in plane)
   assert btotal[c+1][4]==sum(chunk['events'][c] for plane in actual['variants']['65536'] for chunk in plane)
  bplanes=[];aplanes=[];begin=0
  for n in (5400,1350,1350):
   bplanes.append(totals(bw,12,begin,begin+n));aplanes.append([part+[0] for part in totals(aw,11,begin,begin+n)]);begin+=n
  assert all(len(p)==1 for p in actual['variants']['65536'])
  for policy in policies:
   row=rows[policy,*ident];merged=[[0]*12 for _ in range(5)]
   for axis in range(3):
    src=bplanes[axis] if row['mask']&(1<<axis) else aplanes[axis]
    for part in range(5):
     for k in range(12):merged[part][k]+=src[part][k]
   assert sum(p[0] for p in merged[1:])==row['remaining_decisions']
   assert sum(p[1] for p in merged[1:])==row['remaining_renorm']
   assert sum(p[11] for p in merged[1:])==row['BR88_bits']
   assert merged[0][7]==row['components']['chunk_payloads'] and merged[0][8]==8100
   for part in range(5):
    for k in range(12):global_work[policy][part][k]+=merged[part][k]
   mixed.append(dict(policy=policy,cohort=ident[0],fid=ident[1],mask=row['mask'],packet_sha256=row['packet_sha256'],shared=dict(zip(FIELDS,merged[0])),contexts=[dict(zip(FIELDS,p)) for p in merged[1:]]))
  count+=1;chunks+=len(br['chunks'])
 assert count==457 and chunks==1371 and len(mixed)==2285
 # Exercise the public array interface independently on all four selected
 # causal sources, including restoration of old-elided CONST stores.
 api=load('obs89_public_data',AREA/'data.py');seen=0
 for frames in api.iter_policies(only={(0,0),(0,1),(0,3),(3,50)}):
  for frame in frames:
   t=next(r for r in mixed if (r['policy'],r['cohort'],r['fid'])==(frame['policy'],frame['cohort'],frame['fid']))
   actual_shared={k:sum(w[k] for w in frame['shared_work']) for k in FIELDS}
   actual_contexts=[{k:sum(w[c][k] for w in frame['context_work']) for k in FIELDS} for c in range(4)]
   assert actual_shared==t['shared'] and actual_contexts==t['contexts'];seen+=1
 assert seen==16
 pins={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__).resolve(),AREA/'data.py',AREA/'index.json',ROOT/'experiments/python-gamebub-v86/contexts/index.json',ROOT/'experiments/python-gamebub-v88/entropy/index.json',ROOT/selected['selected_report']]}
 (AREA/'mixed-totals.jsonl').write_text(''.join(json.dumps(row,separators=(',',':'))+'\n' for row in mixed))
 report=dict(schema='cu66-v89-observation-independent-audit-v1',status='PASS_ACTUAL_BR_AND_ALL_MIXED_POLICY_TOTALS',native_sources=457,chunks=1371,mixed_policy_records=2285,public_interface_records=seen,source_sha256=pins,mixed_totals_sha256=sha(AREA/'mixed-totals.jsonl'),policy_totals={p:dict(shared=dict(zip(FIELDS,v[0])),contexts=[dict(zip(FIELDS,c)) for c in v[1:]]) for p,v in global_work.items()},scope='Actual primitive observations and independent plane-wise policy mixing. No elapsed FPGA timing or target-memory proof.')
 (AREA/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(report['status'],'sources=457 chunks=1371 mixed_records=2285 public_records=16')
if __name__=='__main__':main()
