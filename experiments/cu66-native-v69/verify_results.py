#!/usr/bin/env python3
"""Audit retained native/Python paired observations and qualification logs."""
from pathlib import Path
import hashlib,json,math,statistics
HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def same(a,b):assert math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-12),(a,b)
def summary(rows):
 means={name:statistics.mean(r['median_ms'][name]for r in rows)for name in('python','native')}
 return dict(frames=len(rows),keys=sum(r['key']for r in rows),mean_paired_median_complete_presentation_ms=means,native_to_python_ratio=means['native']/means['python'],native_peak_per_frame_median_ms=max(r['median_ms']['native']for r in rows),native_median_over_33_333ms=sum(r['median_ms']['native']>1000/30 for r in rows))
def compare(expected,actual):
 assert expected.keys()==actual.keys()
 for key,value in expected.items():
  if isinstance(value,dict):compare(value,actual[key])
  elif isinstance(value,float):same(value,actual[key])
  else:assert value==actual[key],(key,value,actual[key])
def main():
 r=json.loads((HERE/'results.json').read_text());m=json.loads((HERE/'manifest.json').read_text());assert r['schema']=='cu66-native-v69-paired'and sha(HERE/'manifest.json')==r['manifest_sha256']
 for name,digest in r['producer_source_sha256'].items():assert sha(HERE/name)==digest,name
 flat=[]
 for case,source in zip(r['cases'],m['cases'],strict=True):
  assert case['scene']==source['scene']and len(case['rows'])==len(source['rows'])
  for row,original in zip(case['rows'],source['rows'],strict=True):
   for key in('id','key','canonical_tag','canonical_yuv_u8_sha256','hud_words_u16le_sha256','display_rgb565_u16le_sha256'):assert row[key]==original[key]
   assert row['packet_sha256']==original['packet']['sha256'];assert row['paired_order']==[(['python','native']if(row['id']+rep)%2==0 else['native','python'])for rep in range(3)]
   for name in('python','native'):
    values=row['complete_presentation_ms'][name];assert len(values)==3 and all(type(x)is float and math.isfinite(x)and x>0 for x in values);same(statistics.median(values),row['median_ms'][name])
   flat.append(row)
  compare(summary(case['rows']),case['summary'])
 compare(summary(flat),r['summary']);assert len(flat)==457 and sum(x['key']for x in flat)==20
 for log in('tests-sanitized.log','fuzz-sanitized.log','full-sanitized.log'):
  text=(HERE/log).read_text();assert 'ERROR:'not in text and'runtime error:'not in text and'AddressSanitizer'not in text
 full=[json.loads(line)for line in(HERE/'full-sanitized.log').read_text().splitlines()];assert full[-1]['frames']==457 and full[-1]['keys']==20 and len(full)==458
 for log,countkey,count in(('hud-directed.log','native_directed_HUD_cases',32),('entropy-directed.log','directed_rejected_entropy_packets',25),('ab38-check.log','exact_coefficient_tiles',3586687),('tests-sanitized.log','malformed_or_unsupported_packets_rejected',28),('fuzz-sanitized.log','mutation_trials',512)):
  result=json.loads((HERE/log).read_text().splitlines()[-1]);assert result[countkey]==count
 print(json.dumps(dict(frames=457,paired_trials_per_path=1371,source_pins=len(r['producer_source_sha256']),timing_math_exact=True,full_presentation_hashes_bound=True,sanitizer_and_directed_logs_checked=True,native_to_python_ratio=r['summary']['native_to_python_ratio'],physical_30fps_proven=False)))
if __name__=='__main__':main()
