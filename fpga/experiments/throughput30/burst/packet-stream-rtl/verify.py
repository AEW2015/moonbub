#!/usr/bin/env python3
"""Check the incremental replay's observable timing and queue invariants."""
import re,sys
from pathlib import Path
lines=Path(sys.argv[1]).read_text().splitlines()
assert 'TEST_PASS_PACKET_STREAM' in lines
found=[x for x in lines if x.startswith('PACKET_STREAM_RESULT ')]
assert len(found)==1
r={k:int(v) for k,v in re.findall(r'(\w+)=(\d+)',found[0])}
trace=Path(sys.argv[2]).read_text().splitlines()
assert r['packets']==int(trace[0])==26
assert r['bytes']==26159 and r['queue_drops']==0 and r['queue_high_bytes']<=5320
assert r['capture_cycle']<r['first_arrival']<=r['first_send']<r['last_arrival']<=r['last_send']<=r['commit_cycle']<r['present_cycle']
assert r['first_arrival']-r['capture_cycle']==int(trace[1].split()[0])
assert r['last_arrival']-r['capture_cycle']==int(trace[-1].split()[0])
assert r['writes']==345600 and r['bursts']==43200 and r['underruns']==0 and r['credit_reads']>0
print('STREAM_TIMING_PASS first payload sent before EOF arrival; bounded queue and publication checked')
