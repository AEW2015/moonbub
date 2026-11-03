#!/usr/bin/env python3
"""Generate instrumented proof-only copies from hash-pinned DUT sources."""
import hashlib,sys
from pathlib import Path
if len(sys.argv)!=4:raise SystemExit('usage: generate.py ORIGINAL CANDIDATE NEW_DIRECTORY')
original,candidate,out=map(Path,sys.argv[1:]);out.mkdir(parents=True,exist_ok=False)
expect=['99b8681e002d948fa4ed5fbd3a29704634400c31c376b5e120c07d1392ef62c0','d3cefd3651622c793ec92cff696a971a7e22bcdc694541960292d2b499880cde']
raw=[]
for p,h in zip([original,candidate],expect):
 b=p.read_bytes()
 if hashlib.sha256(b).hexdigest()!=h:raise SystemExit(f'hash mismatch: {p}')
 raw.append(b.decode().replace('\r\n','\n'))
# Check the only semantic differences are the specified operand widths/name.
norm=raw[0].replace('module jpeg_idct_x\n','module jpeg_idct_x_narrow\n',1)
for i in range(5):
 for suffix in ('a','b'):
  name=f'mul{i}_{suffix}';width=(16 if i==4 else 15) if suffix=='a' else 12
  old=f'reg signed [31:0] {name};';new=f'reg signed [{width}:0] {name};'
  if norm.count(old)!=1:raise SystemExit(f'unexpected declaration: {name}')
  norm=norm.replace(old,new,1)
if norm!=raw[1]:raise SystemExit('candidate contains unexpected source changes')
state=[(f'mul{i}_q',32) for i in range(5)]+[(f'mul{i}',32) for i in range(5)]+[(f'out_stg{i}_valid_q',1) for i in range(4)]+[(f'out_stg{i}_idx_q',3) for i in range(4)]+[(n,32) for n in ['o_s5','o_s6','o_s7','o_t0','o_t1','o_t2','o_t3','o_t4','o_t5','o_t6','o_t7','o_t6_5','o_t5_6']]+[(f'block_out[{i}]',32) for i in range(8)]+[('block_out_tmp',32),('valid_q',8),('ptr_q',6)]
if sum(w for _,w in state)!=1054:raise SystemExit('bad state map')
for s,which in zip(raw,['original','candidate']):
 port='    ,output [  5:0]  outport_idx_o\n'
 if s.count(port)!=1 or s.count('\nendmodule')!=1:raise SystemExit('unexpected source structure')
 terms=['i0']
 for i in range(5):
  for suffix in ('a','b'):
   name=f'mul{i}_{suffix}';width=32 if which=='original' else (17 if i==4 and suffix=='a' else 16 if suffix=='a' else 13)
   terms.append(name if width==32 else f'{{{{{32-width}{{{name}[{width-1}]}}}}, {name}}}')
 o=s.replace(port,port+'    ,output [351:0] proof_operand_state\n').replace('\nendmodule','\nassign proof_operand_state = {'+', '.join(terms)+'};\n\nendmodule')
 (out/f'operand-{which}.v').write_text(o)
 a=s.replace(port,port+f'    ,output [1053:0] proof_state\n'+''.join(f'    ,input [31:0] proof_product{i}\n' for i in range(5)))
 for i in range(5):
  old=f'mul{i}_q <= mul{i}_a * mul{i}_b;';new=f'mul{i}_q <= proof_product{i};'
  if a.count(old)!=1:raise SystemExit(f'unexpected product: {i}')
  a=a.replace(old,new)
 a=a.replace('\nendmodule','\nassign proof_state = {'+', '.join(n for n,_ in state)+'};\n\nendmodule')
 (out/f'state-{which}.v').write_text(a)
# Negative controls change only isolated copies, never source.
for src,dst,old,new in [('operand-candidate.v','operand-mutant.v','mul0_a <= block_in_2_3;','mul0_a <= ~block_in_2_3;'),('state-candidate.v','state-mutant.v','mul0 <= mul0_q;','mul0 <= ~mul0_q;')]:
 s=(out/src).read_text()
 if old not in s:raise SystemExit('mutant anchor missing')
 (out/dst).write_text(s.replace(old,new,1))
print('instrumented files and mutants generated; source delta and hashes verified')
