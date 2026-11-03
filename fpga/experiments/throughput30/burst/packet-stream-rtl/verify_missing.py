#!/usr/bin/env python3
"""Check missing-middle-packet abort after real partial QSPI transfer."""
import re,sys
from pathlib import Path
lines=Path(sys.argv[1]).read_text().splitlines()
assert 'TEST_PASS_MISSING_PACKET_ABORT' in lines
assert 'TEST_PASS_PACKET_STREAM' not in lines
results=[x for x in lines if x.startswith('MISSING_PACKET_RESULT ')]
assert len(results)==1
r={k:int(v) for k,v in re.findall(r'(\w+)=(\d+)',results[0])}
trace=Path(sys.argv[2]).read_text().splitlines();rows=[list(map(int,x.split())) for x in trace[1:]]
assert len(rows)==int(trace[0]) and r['dropped_index']==5
assert r['forwarded_packets']==5 and r['forwarded_bytes']==sum(x[2] for x in rows[:5])
assert r['gap_expected']==rows[5][1] and r['gap_actual']==rows[6][1]
assert r['gap_cycle']<=r['abort_cycle']<r['check_cycle']
assert r['frame_boundaries']==2 and r['presented']==r['pixels']==r['writes']==0
print('MISSING_PACKET_CHECK_PASS: abort after partial transfer, no publication across two boundaries')
