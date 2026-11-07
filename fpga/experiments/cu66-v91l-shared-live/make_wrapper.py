"""Wire the frozen live producer and RGB reader to one physical SDRAM service."""
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[3];AREA=Path(__file__).resolve().parent
FABRIC=ROOT/'fpga/experiments/cu66-v91l-shared-service'
def ports(path):
 s=path.read_text();s=s[re.search(r'\)\s*\(',s).end():];s=s[:s.index(');')]
 result=[];direction=typ=width=''
 for part in s.split(','):
  part=part.strip()
  m=re.match(r'(input|output|inout)\s+(logic(?: signed)?|wire|integer)\s*(.*)',part,re.S)
  if m:direction,typ,part=m.groups();width=''
  m=re.match(r'(\[[^]]+\])\s*(.*)',part,re.S)
  if m:width,part=m.groups()
  m=re.fullmatch(r'(\w+)(\s*\[[^]]+\])?',part)
  assert m,(path,part)
  result.append((direction,typ,width,m[1],m[2] or ''))
 return result

def decl(p,name=None,direction=None):
 d,t,w,n,a=p;return f'{direction or d} {t} {w} {name or n}{a}'.replace('  ',' ')
rows=ports(ROOT/'fpga/experiments/cu66-v91l-rows/cs88_rows_v91l.sv')
rgb=ports(ROOT/'fpga/experiments/cu66-v91l-burst-converter/canonical_rgb565_tiled.sv')
fabric=ports(FABRIC/'shared_sdram_timed.sv')
connections={}
for p in fabric:
 n=p[3]
 if n in ('clk','power_on_reset'):connections[n]=n
 elif n=='wr_reset':connections[n]='reset'
 elif n=='wr_cancel':connections[n]='abort_packet||transaction_faulted'
 elif n.startswith(('wr_req_','wr_rsp_')):connections[n]='candidate_'+n[3:]
 elif n in ('rd_reset','rd_cancel'):connections[n]='rgb_'+n[3:]
 elif n.startswith(('rd_req_','rd_rsp_')):connections[n]='rgb_mem_'+n[3:]
 else:connections[n]='fabric_'+n
out=[decl(p,direction='output' if p[3].startswith('candidate_') else None) for p in rows]
for p in rgb:
 n=p[3]
 if n in ('clk','power_on_reset'):continue
 # Physical return fields are outputs of the joined top, never actor inputs.
 out.append(decl(p,'rgb_'+n,'output' if n.startswith('mem_') else None))
for p in fabric:
 if connections[p[3]].startswith('fabric_'):out.append(decl(p,connections[p[3]]))
s='`timescale 1ns/1ps\n`default_nettype none\nmodule shared_live #(parameter real T_AC_NS=2.0)(\n '+',\n '.join(out)+'\n);\n'
s+=' cs88_rows_v91l #(.ROW_WRITES(1\'b1)) live(\n '+',\n '.join('.'+p[3]+'('+p[3]+')' for p in rows)+'\n );\n'
s+=' canonical_rgb565_tiled #(.RETAIN_ROWS(1\'b1)) rgb(\n '+',\n '.join('.'+p[3]+'('+('' if p[3] in ('clk','power_on_reset') else 'rgb_')+p[3]+')' for p in rgb)+'\n );\n'
s+=' shared_sdram_timed #(.T_AC_NS(T_AC_NS)) memory(\n '+',\n '.join('.'+p[3]+'('+connections[p[3]]+')' for p in fabric)+'\n );\n'
s+='endmodule\n`default_nettype wire\n'
(AREA/'shared_live.sv').write_text(s)
print('SHARED_LIVE_WRAPPER_GENERATED')
