#!/usr/bin/env python3
"""Existing-edge operand owner/quantizer model; not an RTL qualification."""
import json,random,re
from qualify import verify,sha,ROOT,SRC,AREA

def main():
 recipe=verify();entry=recipe['production']['cu66_dequant.sv']
 old=(ROOT/entry['original']).read_text();new=(ROOT/entry['candidate']).read_text()
 comb=old[old.index('    always_comb begin'):old.index('    assign in_ready=')]
 assert comb in new
 capture=old[old.index('    always_ff @(posedge clk)if(state==IDLE)'):old.index('    always_ff @(posedge clk)begin')]
 assert capture in new
 table_path=ROOT/'fpga/experiments/cu66-v69/inverse/cu66_quant_rom.svh'
 table={int(i):int(q) for i,q in re.findall(r"7'd(\d+): base_quant=8'd(\d+);",table_path.read_text())}
 assert len(table)==128
 def quant(chr,sc,pos):
  base=table[chr*64+pos]
  scaled=((base+1)>>1) if sc==0 else base if sc==1 else base*2 if sc==2 else 0
  return min(scaled,255)
 arithmetic_rows=0
 for chr in range(2):
  for sc in range(4):
   for pos in range(64):
    for c in (-32768,-2049,-2048,-1,0,1,2048,2049,32767):
     q=quant(chr,sc,pos);legacy=c*q
     # Explicit signed16 coefficient and zero-extended nonnegative9 quantizer.
     registered_c=(c&65535)-65536 if c&32768 else c&65535
     registered_q=q&255
     product=registered_c*registered_q
     assert product==legacy and product&0xfffff==legacy&0xfffff
     arithmetic_rows+=1
 rng=random.Random(110900);state=0;group=0;owned=[0]*64;chr=sc=0;prepared_c=[0]*8;prepared_q=[0]*8;rows=0;captures=0;group_checks=[0]*8;kills=0;fast=0;held=0
 for edge in range(30000):
  values=[rng.randint(-2048,2048) for _ in range(64)]
  if edge%17==0:values=[0]*64
  if edge%23==0:values[rng.randrange(64)]=2049
  live_chr=rng.randrange(2);live_sc=rng.randrange(4);valid=rng.randrange(2);ready=rng.randrange(2)
  kill=edge%31==0 or edge%37==0
  oldstate=state;oldgroup=group
  if state==1 and not kill:
   for lane in range(8):
    assert prepared_c[lane]==owned[group*8+lane]
    assert prepared_q[lane]==quant(chr,sc,group*8+lane)
    assert prepared_c[lane]*prepared_q[lane]==owned[group*8+lane]*quant(chr,sc,group*8+lane)
    rows+=1
   group_checks[group]+=1
  # Operand capture uses the original pre-edge state and original owned RFs.
  if oldstate==0:
   prepared_c=values[:8];prepared_q=[quant(live_chr,live_sc,lane) for lane in range(8)];captures+=1
  elif oldstate==1 and oldgroup<7:
   prepared_c=owned[(oldgroup+1)*8:(oldgroup+2)*8]
   prepared_q=[quant(chr,sc,(oldgroup+1)*8+lane) for lane in range(8)];captures+=1
  if oldstate==0:owned=values[:];chr=live_chr;sc=live_sc
  if kill:state=0;group=0;kills+=1
  elif oldstate==0 and valid:
   group=0
   if sc==3 or any(v < -2048 or v > 2048 for v in owned) or not any(owned):state=2;fast+=1
   else:state=1
  elif oldstate==1:
   if group==7:state=2
   else:group+=1
  elif oldstate==2:
   if ready:state=0
   else:held+=1
 assert min(group_checks)>100 and kills>100 and fast>100 and held>100
 result=dict(status='PASS_EXISTING_EDGE_OPERAND_MODEL_NOT_RTL',arithmetic_rows=arithmetic_rows,scheduled_edges=30000,owned_lane_checks=rows,group_checks=group_checks,operand_capture_edges=captures,kill_edges=kills,fast_exit_edges=fast,held_edges=held,original_quantizer_selection_product_block_byte_identical=True,original_private_RF_capture_byte_identical=True,added_public_cycles=0,source_sha256={entry[k]:sha(ROOT/entry[k]) for k in ('original','candidate')},quantizer_header_sha256=sha(table_path),scope='Source-recipe/adapter reversibility; independent table/arithmetic and existing-edge operand-owner induction across every group, bad/allzero, kill and held schedules. Not RTL simulation, formal four-state equivalence, full pipeline, DSP packing or physical timing evidence.')
 (AREA/'model.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 print(result['status'],arithmetic_rows,rows,sha(AREA/'model.json'))
if __name__=='__main__':main()
