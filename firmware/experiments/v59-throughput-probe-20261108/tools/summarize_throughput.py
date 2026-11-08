"""Summarize a complete checksummed DY45 throughput export; no hardware access."""
from pathlib import Path
import argparse, json, re
from validate_telemetry import validate

def summarize(raw):
    attempts=validate(raw)
    good=[a for a in attempts if a['complete']]
    if not good:
        raise ValueError('No complete indexed/checksummed telemetry export')
    chosen=good[-1]
    pattern=rf'DY45 e={chosen["epoch"]} a={chosen["attempt"]} i=\d+ n=\d+ (.*)'
    rows=re.findall(pattern,raw.decode(errors='replace'))
    def fields(prefix):
        line=next((x for x in rows if x.startswith(prefix)),None)
        if line is None:raise ValueError('Missing '+prefix)
        return dict(re.findall(r'(\w+)=([^\s]+)',line))
    summary=fields('summary '); counters=fields('counters '); totals=fields('totals ')
    if summary.get('ok')!='1':raise ValueError('Failed run; successful throughput is unavailable')
    frames=int(summary['completed']);elapsed=int(totals['elapsed_us'])
    evidence=fields('evidence ')
    stages={}
    for line in rows:
        if not line.startswith('aggregate '):continue
        values=dict(re.findall(r'(\w+)=([^\s]+)',line));name=values.pop('stage')
        if name in stages:raise ValueError('Duplicate aggregate')
        t={k:int(v) for k,v in values.items()}
        if t['count']<0 or t['total_us']<t['max_us'] or t['bytes']<0:raise ValueError('Invalid aggregate')
        t['mean_us']=t['total_us']/t['count'] if t['count'] else None
        stages[name]=t
    expected={'ingress','decoder','native','hud_write','hud_readback','commit_to_owner','owner_interval'}
    if set(stages)!=expected:raise ValueError('Missing throughput stages')
    for name in expected-{'owner_interval','hud_readback'}:
        if stages[name]['count']!=frames:raise ValueError('Incomplete stage '+name)
    if stages['owner_interval']['count']!=max(0,frames-1):raise ValueError('Invalid interval count')
    readback=evidence.get('readback_enabled')=='true'
    if stages['hud_readback']['count']!=(frames if readback else 0):raise ValueError('Readback evidence mismatch')
    if not readback and int(totals['words_verified'])!=0:raise ValueError('Performance mode claims verification')
    intervals=stages['owner_interval']
    return dict(scope='measured unique owner-matched LCD scanout starts; complete panel raster unmeasured',
        epoch=chosen['epoch'],attempt=chosen['attempt'],completed=frames,counters=counters,evidence=evidence,
        elapsed_us=elapsed,trial_scanout_starts_per_second=frames*1e6/elapsed if elapsed else None,
        between_scanout_starts_per_second=intervals['count']*1e6/intervals['total_us'] if intervals['total_us'] else None,
        stages=stages,notes=['No host/receiver clock subtraction.','Diagnostic stop-and-wait limit, not production codec ceiling.','Aggregate means/maxima do not provide percentiles.','Ingress includes source.header waiting.'])

if __name__=='__main__':
    p=argparse.ArgumentParser(__doc__);p.add_argument('capture',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=summarize(a.capture.read_bytes());a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
