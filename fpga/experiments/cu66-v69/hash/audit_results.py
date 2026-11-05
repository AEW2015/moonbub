#!/usr/bin/env python3
"""Audit full SHA digests, actual work/cycles and both bounded buffer configs."""
from pathlib import Path
import hashlib,json,re,zlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def parse(path):
 text=path.read_text();assert 'TEST_FAIL'not in text and text.rstrip().splitlines()[-1].startswith('TEST_PASS ')and 'CONTROL_PASS'in text,path
 rows=[]
 for line in text.splitlines():
  if line.startswith('CASE_PASS '):rows.append({k:(v if k=='name'else int(v))for k,v in re.findall(r'(\w+)=([^ ]+)',line)})
 return rows,text

def main():
 fixtures=[]
 for line in(HERE/'fixtures.tsv').read_text().splitlines():
  name,path,length,digest=line.split('\t');stored=HERE/path;data=zlib.decompress(stored.read_bytes());assert len(data)==int(length)and hashlib.sha256(data).hexdigest()==digest
  assert stored.name.split('.')[0]==sha(stored);fixtures.append((name,int(length),digest))
 assert len(fixtures)==98;metadata=json.loads((HERE/'fixture-evidence.json').read_text())
 for p,want in metadata['source_sha256'].items():assert sha(ROOT/p)==want,p
 runs=[];logs=[]
 for banks in(1,2):
  assert not re.search(r'%Warning|%Error',(HERE/f'build-banks{banks}.log').read_text())
  yosys=(HERE/f'yosys-banks{banks}.log').read_text();assert 'Found and reported 0 problems.'in yosys
  for mode,seed in(('ideal',6901),('seed6901',6901),('seed6902',6902),('seed6903',6903)):
   path=HERE/f'banks{banks}-{mode}.log';rows,text=parse(path);assert len(rows)==106
   for (name,size,digest),r in zip(fixtures,rows[:98],strict=True):
    assert r['name']==name and r['bytes']==size
    blocks=(size+9+63)//64;assert r['blocks']==blocks and r['rounds']==blocks*64 and r['padding']==blocks*64-size
    assert r['result_accept']==r['cycles']and r['result_first']<r['result_accept']
    if size:assert 0<r['first_byte']<=r['last_byte']<r['result_first']
    else:assert r['first_byte']==r['last_byte']==0
    if mode=='ideal':
     assert r['source_bubbles']==r['output_stalls']==0
     expected=130*blocks+2 if banks==1 else (132 if blocks==1 else 66*blocks+65)
     assert r['result_first']==expected,(banks,name,r['result_first'],expected)
   for r in rows[98:]:assert r['name']=='NIST_abc'and r['bytes']==3 and r['blocks']==1 and r['rounds']==64
   for control in('early_last','missing_last','overlong_last','partial_pause_abort','held_abort','round_abort','reset','result_stability','busy_start','extra_unaccepted_byte','valid_retry'):assert control in text
   assert f'seed={seed}'in text and f'randomized={int(mode!="ideal")}'in text
   canonical=[r for r in rows[:98]if r['name'].startswith('canonical_')];assert len(canonical)==6 and all(r['bytes']==518404 for r in canonical)
   runs.append(dict(buffer_blocks=banks,mode=mode,seed=seed,fixture_messages=98,valid_retries=8,canonical_messages=canonical));logs.append(path)
 ideal={r['buffer_blocks']:r['canonical_messages'][0]for r in runs if r['mode']=='ideal'}
 paths=[HERE/p for p in('cu66_sha256_bytes.sv','tb_hash.cpp','export_fixtures.py','audit_results.py','run_regression.sh','fixtures.tsv','fixture-evidence.json','environment.log','build-banks1.log','build-banks2.log','yosys-banks1.log','yosys-banks2.log')]+logs
 result=dict(schema='cu66-sha256-rtl-v69',backend='Verilator 5.020',implementation='original SHA256, one chained iterative core, 64 active round clocks per padded block',
  unique_fixture_messages=98,actual_canonical_source_keys=4,full_size_messages=6,full_size_bytes=518404,
  runs=runs,source_sha256={p.relative_to(ROOT).as_posix():sha(p)for p in paths},
  canonical_ideal=dict(single_bank_first_result_cycles=ideal[1]['result_first'],dual_bank_first_result_cycles=ideal[2]['result_first'],
   single_bank_input_backpressure=ideal[1]['input_stalls'],dual_bank_input_backpressure=ideal[2]['input_stalls'],
   padded_blocks=8101,active_round_cycles=518464,conditional_ms_at_assumed_100MHz=dict(single=ideal[1]['result_first']/100000,dual=ideal[2]['result_first']/100000)),
  input_schedule_storage_bytes=dict(single=64,dual=128),SHA_state_and_controls_additional=True,
  full_digest_256_checked=True,last_checked_on_accepted_bytes=True,whole_canonical_frame_staged=False,
  FIPS_validation_or_authentication_claim=False,routed_clock_or_target_fit_proven=False,whole_frame_decoder_or_physical_30fps_proven=False)
 (HERE/'results.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(dict(configurations=2,fixture_messages_per_run=98,runs=8,checked_fixture_digests=784,valid_control_retries=64,
  actual_source_keys=4,full_message_bytes=518404,single_bank_first_result_cycles=ideal[1]['result_first'],dual_bank_first_result_cycles=ideal[2]['result_first'],
  full_SHA256_exact=True,source_pins=len(paths),routed_clock_or_physical_FPS_proven=False)))
if __name__=='__main__':main()
