#!/usr/bin/env python3
"""Summarize a separately C-checked prefix of an incomplete RTL run."""
import hashlib,json,pathlib,re,sys
run,checks,fixtures,out=map(pathlib.Path,sys.argv[1:]);n=30
log=run/'run.log'
if not log.exists():log=run/'log-snapshot.txt'
s=log.read_text()
def rows(prefix):return [{k:int(v) for k,v in re.findall(r'(\w+)=(\d+)',line)} for line in s.splitlines() if line.startswith(prefix+' ')]
cfg=rows('CONFIG');arr=rows('ARRIVAL');p=rows('PRESENT_PASS');scans=rows('SCAN_PASS');manifest=json.loads((fixtures/'manifest.json').read_text())
if len(cfg)!=1 or cfg[0]!={'frames':300,'jitter_cycles':200000,'pclk_half_ps':18470,'capture_phase_cycles':833333}:raise ValueError('wrong test config')
if [x['id'] for x in arr[:n]]!=list(range(n)) or [x['id'] for x in p[:n]]!=list(range(n)):raise ValueError('prefix ordering')
epoch=arr[0]['cycle'];ages=[];gaps=[]
for i in range(n):
 jitter=200000 if i%3==1 else (-200000 if i%3==2 else 0)
 if arr[i]['cycle']!=arr[i]['target'] or arr[i]['cycle']!=epoch+i*10000000//3+jitter or p[i]['cycle']<arr[i]['cycle']:raise ValueError('arrival schedule/order')
 if hashlib.sha256((fixtures/f'{i:04}.jpg').read_bytes()).hexdigest()!=manifest['frames'][i]['jpeg_sha256']:raise ValueError('fixture hash')
 v=json.loads((checks/f'{i:04}.json').read_text())
 if v['pixels']!=345600 or v['exact_rgb565_pixels']!=345600:raise ValueError('pixel check')
 if p[i]['writes']!=345600 or p[i]['bursts']!=43200 or p[i]['underruns']!=0:raise ValueError('counters')
 if not any(x['id']==i and x['pixels']==345600 for x in scans):raise ValueError('missing scan')
 ages.append((p[i]['cycle']-(epoch+i*10000000//3))/100000)
 if i:gaps.append((p[i]['cycle']-p[i-1]['cycle'])/100000)
result={'scope':'Checkpoint of first 30 frames only; run continued, no claim about final 300 or 10 second window. Behavioral RTL, no ESP32/Wi-Fi/hardware timing.', 'config':cfg[0], 'frames_checked':n, 'input_manifest_sha256':hashlib.sha256((fixtures/'manifest.json').read_bytes()).hexdigest(), 'exact_cmodel_pixels':n*345600, 'capture_age_ms':{'min':min(ages),'max':max(ages)},'gap_ms':{'min':min(gaps),'max':max(gaps)},'presented_ids':list(range(n))}
out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
