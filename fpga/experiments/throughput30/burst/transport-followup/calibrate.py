#!/usr/bin/env python3
"""Compare analytical payload-only replay with ten real RTL simulation swaps."""
import argparse,json,re
from pathlib import Path
from model import ROOT,Scenario,load_fixtures,read_timings,run
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--fixtures',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
t=read_timings(ROOT/'fpga/experiments/throughput30/burst/cadence-study/verilator-65hz.log')
j=load_fixtures(a.fixtures)
records=run(j,t,Scenario(rate_bps=8_000_000,payload_only_service=True),10,True)['presented_records']
log=ROOT/'fpga/experiments/throughput30/burst/link-study/link8-verilator.log'
rtl=[{k:int(v) for k,v in re.findall(r'(\w+)=(\d+)',x)} for x in log.read_text().splitlines() if x.startswith('FRAME_RESULT ')]
if len(records)!=10 or len(rtl)!=10:raise SystemExit('incomplete calibration run')
epoch=rtl[0]['arrival_cycle'];errors=[]
for m,r in zip(records,rtl):
 if m['id']!=r['id']-1:raise SystemExit('frame ID mismatch')
 errors.append(m['cycle']-(r['present_cycle']-epoch))
result={'scope':'10-frame payload-only event model compared to RTL finite-link Verilator replay',
        'zero_or_one_cycle_matches':sum(abs(x)<=1 for x in errors),'frame_error_cycles':errors,
        'maximum_absolute_error_cycles':max(abs(x) for x in errors),'cycle_ns':10,
        'caveat':'Analytical service durations depend on timing/contention; mismatch shows limits, not an RTL failure.'}
a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
