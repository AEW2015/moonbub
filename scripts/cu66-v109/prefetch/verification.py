#!/usr/bin/env python3
"""Lossless complete-body adapters using existing stricter V108/V106 oracles."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];SRC=ROOT/'fpga/experiments/cu66-v109-prefetch';OUT=SRC/'verification';BASE=ROOT/'fpga/experiments/cu66-v108-capacity';OLD=ROOT/'fpga/experiments/cu66-v106-scratch'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 adapters=[]
 def adapt(source,path,replacements):
  text=source.read_text()
  for before,after in replacements:assert text.count(before)==1,(str(source),before);text=text.replace(before,after,1)
  path.write_text(text);adapters.append(dict(source=str(source.relative_to(ROOT)),path=str(path.relative_to(ROOT)),source_sha256=sha(source),sha256=sha(path),renames=replacements))
 kinds={'br88_packet_ingress_sync_v91h.sv':'ingress','br88_packet_ingress_v91h.sv':'packet','br88_pipeline_v91h.sv':'pipeline','packed_scratch_v91g2.sv':'scratch'}
 for name,kind in kinds.items():
  for variant in ('original','candidate'):
   source=SRC/name if kind=='scratch' and variant=='candidate' else BASE/name
   replacements=[('module '+name[:-3]+' ','module '+kind+'_'+variant+' ')]
   if kind=='packet':replacements += [('br88_packet_ingress_sync_v91h #(',f'ingress_{variant} #(')]
   if kind=='pipeline':replacements += [('br88_packet_ingress_v91h #(',f'packet_{variant} #('),('packed_scratch_v91g2 scratch (',f'scratch_{variant} scratch (')]
   adapt(source,OUT/(kind+'_'+variant+'.sv'),replacements)
 # Scratch-specific observation adapters append the exact existing visibility.
 a=json.loads((OLD/'adapter.json').read_text())
 for variant in ('original','candidate'):
  source=SRC/'packed_scratch_v91g2.sv' if variant=='candidate' else BASE/'packed_scratch_v91g2.sv'
  replacements=[('module packed_scratch_v91g2 ','module observed_'+variant+' '),('\n);',a['extra_ports']),('\nendmodule',a['assignments']['candidate']+'\nendmodule')]
  adapt(source,OUT/('observed_'+variant+'.sv'),replacements)
 probe=(OLD/'scratch_probe.sv').read_text().replace('scratch_original original (','observed_original original (').replace('scratch_candidate candidate (','observed_candidate candidate (')
 needle='        .coef_valid(coef_valid),'
 assert probe.count(needle)==2
 args='''        .begin_prefix1(aligned1),.begin_prefix12(aligned12),.begin_prefix123(aligned123),
        .begin_threshold1(threshold1),.begin_threshold2(threshold2),.begin_threshold3(threshold3),
        .begin_capacity_upper(capacity_upper),.begin_capacity_lower(capacity_lower),.begin_capacity_wrap(capacity_wrap),
'''
 probe=probe.replace(needle,args+needle)
 needle='    logic  old_begin_ready;'
 wire='''    logic [31:0] aligned1,aligned12,aligned123,threshold1,threshold2,threshold3,capacity_upper,capacity_lower;
    logic [27:0] capacity_a;logic capacity_wrap;
    assign aligned1=(begin_count1*4+32'd15)&32'hfffffff0;
    assign aligned12=aligned1+((begin_count2*4+32'd15)&32'hfffffff0);
    assign aligned123=aligned12+((begin_count3*4+32'd15)&32'hfffffff0);
    assign threshold1=begin_count1/5+32'(begin_count1%5!=0);
    assign threshold2=begin_count2/15+32'(begin_count2%15!=0);
    assign threshold3=begin_count3/43+32'(begin_count3%43!=0);
    assign capacity_a=aligned123[31:4]+28'd2;
    assign capacity_upper={1'b0,(28'd16384-capacity_a),3'd0};
    assign capacity_lower={1'b0,(~capacity_a),3'd0};
    assign capacity_wrap=capacity_a>28'd16384;
'''
 assert probe.count(needle)==1;probe=probe.replace(needle,wire+needle)
 (OUT/'scratch_probe.sv').write_text(probe)
 for name in ('tb_scratch.cpp','historical_hazards.cpp'):(OUT/name).write_bytes((OLD/name).read_bytes())
 for name in ('prefix_probe.sv','tb_prefix.cpp'):(OUT/name).write_bytes((BASE/'verification'/name).read_bytes())
 manifest=dict(schema='v109-prefetch-lossless-adapters-v1',adapters=adapters,fixtures={str(p.relative_to(ROOT)):sha(p) for p in [OLD/'scratch_probe.sv',OLD/'tb_scratch.cpp',OLD/'historical_hazards.cpp',BASE/'verification/prefix_probe.sv',BASE/'verification/tb_prefix.cpp']},all_original_checks_retained=True,extra_scratch_plumbing='coherent V108 prefix/threshold/capacity inputs derived in wrapper; original V106 bench and hazard oracle byte-identical')
 (OUT/'adapters.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n');print('PREFETCH_VERIFICATION_PREPARED',len(adapters))
if __name__=='__main__':main()
