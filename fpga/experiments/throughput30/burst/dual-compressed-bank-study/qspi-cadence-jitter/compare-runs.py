#!/usr/bin/env python3
"""Compare completed per-frame JSON results from matched synthetic inputs."""
import argparse,hashlib,json,pathlib
p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest',type=pathlib.Path);p.add_argument('analysis',nargs='+',type=pathlib.Path);a=p.parse_args()
raw=a.manifest.read_bytes();manifest=json.loads(raw);result=[]
for path in a.analysis:
 r=json.loads(path.read_text());n=r['input_frames'];records=r['per_frame']
 expected=hashlib.sha256(raw).hexdigest(); recorded=(path.parent/'fixture-manifest.sha256').read_text().split()[0]
 if recorded!=expected:raise ValueError('fixture manifest hash mismatch')
 if len(manifest['frames'])<n or r['distinct_input_hashes']!=n or len(records)!=r['presented']:
  raise ValueError('incomplete manifest or analysis')
 if any(row['id']>=n or row['capture_age_cycles']<0 for row in records):
  raise ValueError('invalid record')
 result.append({'run':str(path),'config':r['config'],'inputs':n,'admitted':r['admitted'],'busy_drops':r['busy_drops'],
  'presented_in_window':r['presented_within_capture_window'],'total_presented':r['presented'],
  'nominal_capture_age_ms':r['capture_age_ms'],'inter_presentation_ms':r['gap_ms'],
  'presented_older_than_1_over_30s':sum(3*row['capture_age_cycles']>10000000 for row in records),
  'last_window_offset_ms':r['last_window_offset_ms'],'exact_pixels':r['exact_pixels']})
if len({x['inputs'] for x in result})!=1:raise ValueError('input lengths differ')
print(json.dumps({'scope':'Descriptive simulation comparison for a shared fixture manifest; no hardware or 60-second proof.',
 'fixture_manifest_sha256':hashlib.sha256(raw).hexdigest(),'runs':result},indent=2))
