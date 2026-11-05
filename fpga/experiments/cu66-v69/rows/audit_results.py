#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,re,zlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def records(path):
 text=path.read_text();assert 'TEST_FAIL'not in text and text.rstrip().splitlines()[-1].startswith('TEST_PASS ')and'CONTROL_PASS'in text,path
 rows=[]
 for line in text.splitlines():
  if line.startswith('CASE_PASS '):rows.append({k:(v if k=='name'else int(v))for k,v in re.findall(r'(\w+)=([^ ]+)',line)})
 assert len(rows)==19 and [r['mode']for r in rows]==[0]*7+list(range(1,9))+[0]*4
 return rows,text

def main():
 fixtures=[]
 for line in(HERE/'fixtures.tsv').read_text().splitlines():
  name,path,size,tag=line.split('\t');raw=zlib.decompress((HERE/path).read_bytes());assert len(raw)==int(size)==518404 and raw[:4]==bytes((208,2,224,1))and hashlib.sha256(raw).hexdigest()==tag;fixtures.append(name)
 assert len(fixtures)==7
 meta=json.loads((HERE/'fixture-evidence.json').read_text());assert meta['python67_model_checked_tiles']==56700
 for p,want in meta['source_sha256'].items():assert sha(ROOT/p)==want,p
 memory=json.loads((HERE/'memory-evidence.json').read_text())
 for p,want in memory['source_sha256'].items():assert sha(ROOT/p)==want,p
 assert all(c['parameters']['RD_PORTS']==c['parameters']['WR_PORTS']==c['parameters']['RD_CLK_ENABLE']==c['parameters']['WR_CLK_ENABLE']==1 for c in memory['cases'])
 runs=[];files=[HERE/p for p in('cu66_tile_rows.sv','cu66_rows_sha256.sv','tb_rows.cpp','export_fixtures.py','audit_results.py','audit_memory.py','run_regression.sh','fixture-evidence.json','fixtures.tsv','memory-evidence.json','environment.log')]
 files += [HERE.parent/'hash/cu66_sha256_bytes.sv']
 for strips,hashes in((1,0),(2,0),(1,1),(1,2),(2,1),(2,2)):
  label=f'rows{strips}'if not hashes else f'combined{strips}{hashes}'
  assert not re.search(r'%Warning|%Error',(HERE/f'build-{label}.log').read_text());files.append(HERE/f'build-{label}.log')
  for mode in('ideal','seed6901','seed6902','seed6903'):
   path=HERE/f'{label}-{mode}.log';rows,text=records(path);files.append(path)
   assert f'integrated_SHA256={int(hashes!=0)}'in text
   for fixture,r in zip(fixtures,rows[:7],strict=True):assert r['name']==fixture
   for r in rows:
    if r['mode']==0:
     assert r['error']==0 and r['bytes']==518404 and r['tiles']==8100 and r['writes']==r['reads']==64800
     assert r['first_byte']>=2 and r['first_y']>r['first_byte'] and r['last_byte']>=r['first_y']
     if mode=='ideal':assert r['first_byte']==2
     if hashes:assert r['first_result']>=r['last_byte']and r['cycles']>r['first_result']
     else:assert r['first_result']==0 and r['cycles']==r['last_byte']
    else:assert r['error']in(2,3)and r['first_result']==0
   for check in('wrong_frame','wrong_key','wrong_plane','wrong_index','early_last','duplicate','plane_boundary','missing_last','captured_bus_ownership','invalid_config','busy_start','key_zero_and_one','held_abort','reset','provisional_output_abort','retry'):assert check in text
   runs.append(dict(strip_banks=strips,hash_banks=hashes,mode=mode,full_messages=7,actual_source_keys=4,valid_retries=4,malformed_tile_cases=8,frames=rows[:7]))
 for banks in(1,2):
  path=HERE/f'yosys-rows{banks}.log';assert'Found and reported 0 problems.'in path.read_text();files.append(path)
 ideal={str(r['strip_banks'])+str(r['hash_banks']):r['frames'][0]for r in runs if r['mode']=='ideal'}
 assert ideal['10']['cycles']==591421 and ideal['20']['cycles']==519212
 assert ideal['11']['first_result']==1126148 and ideal['22']['first_result']==535538
 result=dict(schema='cu66-canonical-rows-sha-rtl-v69',backend='Verilator 5.020',unique_full_messages=7,actual_source_keys=4,
  runs=runs,ideal_cycles=ideal,main_full_stream_checks=168,integrated_main_full_SHA256_checks=112,valid_control_retries=96,
  main_checked_bytes=168*518404,source_sha256={p.relative_to(ROOT).as_posix():sha(p)for p in files},
  strip_payload_bytes=dict(single=5760,dual=11520),captured_tile_bytes=64,output_word_cache_bytes=8,metadata_and_SHA_buffers_additional=True,
  full_canonical_frame_staged=False,physical_LCD_scanout_or_rotation_implemented=False,decoder_DDR_HUD_publication_not_integrated=True,
  target_BRAM_mapping_or_routed_Fmax_proven=False,physical_30fps_proven=False)
 (HERE/'results.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(dict(full_stream_checks=168,main_bytes_compared=168*518404,integrated_full_SHA256_checks=112,valid_control_retries=96,
  unique_source_keys=4,standalone_strip_configs=2,integrated_buffer_configs=4,source_pins=len(files),memory_ports='one synchronous64-bit read/one write',physical_LCD_or_FPS_proven=False)))
if __name__=='__main__':main()
