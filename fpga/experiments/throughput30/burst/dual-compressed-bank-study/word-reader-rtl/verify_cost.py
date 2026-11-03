#!/usr/bin/env python3
import re, sys
s = open(sys.argv[1], encoding='utf-8').read()
assert s.count('TEST_PASS_WORD_COST') == 1
first = {int(a): int(b) for a,b in re.findall(r'WORD_FIRST bytes=(\d+) cycle=(\d+)', s)}
tail = {int(a): (int(b),int(c)) for a,b,c in re.findall(r'WORD_TAIL bytes=(\d+) strobe=(\d+) cycle=(\d+)', s)}
lines = re.findall(r'^WORD_COST (.*)$',s,re.M)
assert len(lines)==2 and set(first)==set(tail)=={26159,49152}
for line in lines:
 d={k:int(v) for k,v in re.findall(r'(\w+)=(\d+)',line)}
 n=d['bytes']; assert n in first
 assert d['requests']==d['responses']==n and d['words']==(n+3)//4
 assert first[n]-d['start_cycle']==13
 assert d['last_cycle']-d['start_cycle']==d['total_cycles']
 assert tail[n]==((1<<(n%4 or 4))-1,d['last_cycle'])
 assert d['total_cycles']==(85017 if n==26159 else 159744)
 assert d['min_gap']==(10 if n==26159 else 13) and d['max_gap']==13
 assert d['final_gap']==(10 if n==26159 else 13)
print('COST_CHECK_PASS')
