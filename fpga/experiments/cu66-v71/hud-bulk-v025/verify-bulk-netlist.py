"""Structural gate complements (does not replace) post-synthesis native-word simulation."""
from pathlib import Path
import argparse,hashlib,json,re
a=argparse.ArgumentParser();a.add_argument('--netlist',type=Path,required=True);a.add_argument('--out',type=Path,required=True);v=a.parse_args()
t=v.netlist.read_text();rows=[]
for typ,param,name,pins in re.findall(r'(RAMB(?:18|36)E1)\s*#\((.*?)\)\s*(\\[^\r\n]+|[A-Za-z_0-9]+)\s*\((.*?)\);',t,re.S):
 if not any(x in name for x in ('payload_low','payload_high')):continue
 def pin(k):
  x=re.search(r'\.'+k+r'\(([^\r\n]*)\)',pins);assert x,k;return x[1]
 def zero(x):return not re.sub(r"1'b0|1'h0|1'd0|[,{}\s]",'',x)
 assert typ=='RAMB18E1'
 assert all(zero(pin(n)) for n in ['RSTRAMARSTRAM','RSTRAMB','RSTREGARSTREG','RSTREGB'])
 assert not zero(pin('WEA')) and not zero(pin('WEBWE'))
 assert all(re.search(r'\.'+n+r'\(0\)',param) for n in ['DOA_REG','DOB_REG'])
 assert all(re.search(r'\.'+n+r'\(18\)',param) for n in ['READ_WIDTH_A','READ_WIDTH_B','WRITE_WIDTH_A','WRITE_WIDTH_B'])
 rows.append(dict(instance=name.strip(),primitive=typ,address_A=pin('ADDRARDADDR'),address_B=pin('ADDRBWRADDR'),WEA=pin('WEA'),WEBWE=pin('WEBWE'),payload_resets=False))
assert len(rows)==2,rows
v.out.write_text(json.dumps(dict(status='PASS_TWO_WRITABLE_UNRESET_PAYLOAD_RAMB18',netlist=str(v.netlist),netlist_sha256=hashlib.sha256(v.netlist.read_bytes()).hexdigest(),rows=rows,scope='Structural complement only; CPU write-address mux semantics require executed XSim tests'),indent=2)+'\n')
print('PASS_TWO_WRITABLE_UNRESET_PAYLOAD_RAMB18')
