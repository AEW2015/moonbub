import hashlib,pathlib,re,sys
base=pathlib.Path(sys.argv[1]);new=pathlib.Path(sys.argv[2])
def rows(p):
 return [line for line in (p/'run.log').read_text().splitlines() if line.startswith(('ARRIVAL ','ADMITTED ','DROP_BUSY ','DECODE ','PRESENT_PASS ','SCAN_PASS ','CADENCE_RESULT '))]
assert rows(base)==rows(new),'event or cycle mismatch'
for i in range(10):
 a=(base/'dumps'/f'{i:04}.txt').read_bytes();b=(new/'dumps'/f'{i:04}.txt').read_bytes()
 assert hashlib.sha256(a).digest()==hashlib.sha256(b).digest(),f'pixel hash mismatch {i}'
print('BASELINE_EQUAL_PASS frames=10 event_cycles=equal rgb565_dumps=sha256_equal')
