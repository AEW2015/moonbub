#!/usr/bin/env python3
"""Verified JPEG byte-size percentiles, cap losses and BRAM capacity arithmetic."""
import argparse,hashlib,json,math,re
from pathlib import Path
CAPS=(32768,49152,65536)

def nearest_rank(values,percent):
 if not values or not 0<percent<=100:raise ValueError('empty sample/invalid percentile')
 return sorted(values)[math.ceil(len(values)*percent/100)-1]

def inspect(manifest):
 raw=manifest.read_bytes();d=json.loads(raw);rows=d.get('frames')
 if not isinstance(rows,list) or not rows:raise ValueError('missing frames')
 ids=set();sizes=[];hashes=set();by_id=[]
 for row in rows:
  fid=row['id'];size=row['jpeg_bytes'];digest=row['jpeg_sha256']
  if type(fid)!=int or fid<0 or fid in ids or type(size)!=int or size<1 or not isinstance(digest,str) or not re.fullmatch(r'[0-9a-f]{64}',digest):raise ValueError('invalid frame metadata')
  content=(manifest.parent/f'{fid:04d}.jpg').read_bytes()
  if len(content)!=size or hashlib.sha256(content).hexdigest()!=digest:raise ValueError(f'fixture hash or length mismatch: frame {fid}')
  ids.add(fid);sizes.append(size);hashes.add(digest);by_id.append((fid,size))
 return {'manifest_sha256':hashlib.sha256(raw).hexdigest(),'frames':len(rows),'unique_jpeg_sha256':len(hashes),
  'metadata':{k:d[k] for k in ('source','width','height','fps','source_sampling_fps','start_s','quality','sampling','profile','transformation','pillow_version') if k in d},
  'min_bytes':min(sizes),'max_bytes':max(sizes),'p95_nearest_rank_bytes':nearest_rank(sizes,95),'p99_nearest_rank_bytes':nearest_rank(sizes,99),
  'caps':{str(c):{'capacity_bytes':c,'oversize_count':sum(size>c for _,size in by_id),'oversize_frame_ids':[fid for fid,size in by_id if size>c]} for c in CAPS}}

def bram(c):
 # Conventional 32-data-bit mapping: 4 KiB usable payload per RAMB36.
 return {'capacity_bytes_per_bank':c,'estimated_ramb36_per_bank':math.ceil(c/4096),
         'estimated_ramb36_pair':2*math.ceil(c/4096),'device_ramb36':135,
         'pair_percent_of_135':round(100*2*math.ceil(c/4096)/135,2)}

def main():
 p=argparse.ArgumentParser();p.add_argument('--gameplay-manifest',type=Path,required=True);p.add_argument('--synthetic-manifest',type=Path,required=True);p.add_argument('--combat-manifest',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 result={'scope':'verified local JPEG file sizes, no gameplay or image bytes redistributed','percentile':'nearest-rank: ceil(p*N/100), 1-based','oversize_rule':'size > capacity; equal fits','bram_assumption':'32 data bits per RAMB36, 4096 payload bytes, excludes parity packing and all other RAM',
 'gameplay_300':inspect(a.gameplay_manifest),'combat_90_accelerated':inspect(a.combat_manifest),'synthetic_longrun':inspect(a.synthetic_manifest),'two_bank_bram_estimates':[bram(c) for c in CAPS]}
 a.output.write_text(json.dumps(result,indent=2)+'\n')
 for name in ('gameplay_300','combat_90_accelerated','synthetic_longrun'):
  r=result[name];print(name,'frames',r['frames'],'max/p95/p99',r['max_bytes'],r['p95_nearest_rank_bytes'],r['p99_nearest_rank_bytes'],'oversize',[r['caps'][str(c)]['oversize_count'] for c in CAPS])
if __name__=='__main__':main()
