import hashlib,pathlib,re,sys
base,new=map(pathlib.Path,sys.argv[1:])
def rows(p,prefix):
 return [{k:int(v) for k,v in re.findall(r'(\w+)=(\d+)',line)} for line in (p/'run.log').read_text().splitlines() if line.startswith(prefix+' ')]
def report(p):
 arrivals={r['id']:r['cycle'] for r in rows(p,'ARRIVAL')}; presentations=rows(p,'PRESENT_PASS'); admitted=[r['id'] for r in rows(p,'ADMITTED')];dropped=[r['id'] for r in rows(p,'DROP_BUSY')]
 assert len(presentations)>1
 ids=[r['id'] for r in presentations]; assert ids==admitted
 ages=[(r['id'],r['cycle']-arrivals[r['id']]) for r in presentations]
 fps=(len(presentations)-1)*100_000_000/(presentations[-1]['cycle']-presentations[0]['cycle'])
 return ids,dropped,ages,fps
b=report(base);n=report(new)
for i in set(b[0])&set(n[0]):
 assert hashlib.sha256((base/'dumps'/f'{i:04}.txt').read_bytes()).digest()==hashlib.sha256((new/'dumps'/f'{i:04}.txt').read_bytes()).digest()
for label,r in [('baseline',b),('lcd60',n)]:
 print(label, 'presented',r[0], 'dropped',r[1], 'age_cycles',r[2], 'first_last_interval_fps',f'{r[3]:.6f}')
print('TIMING_COMPARE_PASS identical_common_dump_hashes')
