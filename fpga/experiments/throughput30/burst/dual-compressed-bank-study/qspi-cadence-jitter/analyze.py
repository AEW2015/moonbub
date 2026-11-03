#!/usr/bin/env python3
"""Strict accounting for the bounded jitter model; not a physical timing proof."""
import argparse, hashlib, json, math, pathlib, re
p=argparse.ArgumentParser();p.add_argument('run',type=pathlib.Path);p.add_argument('fixtures',type=pathlib.Path);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args()
text=(a.run/'run.log').read_text()
def rows(label):
 return [{k:int(v) for k,v in re.findall(r'(\w+)=(\d+)',line)} for line in text.splitlines() if line.startswith(label+' ')]
config=rows('CONFIG');arr=rows('ARRIVAL');drops=rows('DROP_BUSY');ad=rows('ADMITTED');pres=rows('PRESENT_PASS');scans=rows('SCAN_PASS');terminal=rows('CADENCE_RESULT')
if len(config)!=1 or len(terminal)!=1 or 'TEST_PASS_BANK_QSPI_CADENCE10' not in text or '%Fatal' in text:raise ValueError('incomplete/failed RTL run')
c=config[0];n=c['frames'];epoch=arr[0]['cycle'];manifest=json.loads((a.fixtures/'manifest.json').read_text());ids=list(range(n))
if len(manifest['frames'])<n:raise ValueError('insufficient fixture manifest')
hashes=[]
for i in ids:
 f=manifest['frames'][i];actual=hashlib.sha256((a.fixtures/f'{i:04}.jpg').read_bytes()).hexdigest()
 if f['id']!=i or f['jpeg_sha256']!=actual:raise ValueError('fixture hash mismatch')
 hashes.append(actual)
if len(set(hashes))!=n:raise ValueError('repeated input')
ai=[x['id'] for x in arr];di=[x['id'] for x in drops];adi=[x['id'] for x in ad];pi=[x['id'] for x in pres]
if ai!=ids or len(adi)!=len(set(adi)) or len(di)!=len(set(di)) or set(adi)&set(di) or set(adi)|set(di)!=set(ids) or pi!=adi:raise ValueError('input/accounting/order mismatch')
if terminal[0]['arrivals']!=n or terminal[0]['admitted']!=len(adi) or terminal[0]['busy_drops']!=len(di) or terminal[0]['presented']!=len(pi):raise ValueError('terminal mismatch')
for x in arr:
 i=x['id'];j= c['jitter_cycles'] if i%3==1 else (-c['jitter_cycles'] if i%3==2 else 0);expected=epoch+i*10000000//3+j
 if x['cycle']!=x['target'] or x['target']!=expected:raise ValueError('incorrect scheduled arrival')
if any(x['cycle']<arr[x['id']]['cycle'] for x in ad+drops):raise ValueError('action before arrival')
if [int(x.stem) for x in sorted((a.run/'dumps').glob('*.txt'))]!=sorted(adi):raise ValueError('missing/extra dumps')
records=[]
for x in pres:
 i=x['id'];commit=next(y['cycle'] for y in ad if y['id']==i)
 if x['cycle']<commit or x['writes']!=345600 or x['bursts']!=43200 or x['underruns']!=0:raise ValueError('presentation counters/order mismatch')
 result=json.loads((a.run/f'comparison{i:04}.json').read_text())
 if result['pixels']!=345600 or result['exact_rgb565_pixels']!=345600:raise ValueError('C model mismatch')
 records.append({'id':i,'arrival':arr[i]['cycle'],'present':x['cycle'],'arrival_age_cycles':x['cycle']-arr[i]['cycle'],'capture_age_cycles':x['cycle']-(epoch+i*10000000//3)})
if not set(adi)<=set(x['id'] for x in scans) or not all(x['pixels']==345600 for x in scans):raise ValueError('missing/invalid LCD scan')
ages=sorted(x['capture_age_cycles'] for x in records);gaps=[b['present']-x['present'] for x,b in zip(records,records[1:])]
def pct(a,p):return a[math.ceil(p*len(a))-1]/100000 if a else None
end=epoch+n*10000000//3
out={'scope':'behavioral QSPI/dual-bank/RTL; synthetic complete-frame arrivals; no CPU/Wi-Fi/physical timing', 'config':c,'capture_epoch_cycle':epoch,'window_end_cycle':end,'input_frames':n,'distinct_input_hashes':len(set(hashes)),'admitted':len(adi),'busy_drops':len(di),'dropped_ids':di,'presented':len(pi),'presented_within_capture_window':sum(x['present']<=end for x in records),'last_window_offset_ms':(records[-1]['present']-end)/100000,'capture_age_ms':{'p50':pct(ages,.5),'p95':pct(ages,.95),'p99':pct(ages,.99),'max':pct(ages,1)},'gap_ms':{'p50':pct(sorted(gaps),.5),'p95':pct(sorted(gaps),.95),'max':pct(sorted(gaps),1)},'exact_pixels':len(pi)*345600,'full_lcd_scans':len(scans),'per_frame':records}
a.output.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='per_frame'},sort_keys=True))
