#!/usr/bin/env python3
"""Prepare actual extracted forwarding/prefix pipeline and original/new plan math."""
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];SRC=ROOT/'fpga/experiments/cu66-v107-plan-prefix';OUT=SRC/'verification'
def main():
 ingress=(SRC/'br88_packet_ingress_sync_v91h.sv').read_text();old=(ROOT/'fpga/experiments/cu66-v107-guard-dsp/packed_scratch_v91g2.sv').read_text()
 function=lambda name,body:re.search(r'    function automatic logic \[31:0\] '+name+r'\(.*?    endfunction',body,re.S).group()
 fn=function('count_aligned',ingress)+'\n'+ '\n'.join(function(n,old) for n in ('aligned','sum3','sum4','sum5'))
 cache=ingress[ingress.index('    always_ff @(posedge clk)begin'):ingress.index('    function automatic logic [31:0] cached32')].rstrip()
 text='''module prefix_math_probe (
 input logic clk,prefix_header_capture,
 input logic [5:0] fetch_index,
 input logic [7:0] ram_data,
 input logic [95:0] prior_header,
 input logic [31:0] begin_count1,begin_count2,begin_count3,
 input logic [16:0] begin_blocks,
 output logic [31:0] meta_prefix1,meta_prefix12,meta_prefix123,
 output logic [23:0] verify_ignored_high,
 output logic [31:0] old_plan2,old_plan3,old_used,new_plan2,new_plan3,new_used
);
 logic [7:0] fetch_bytes[0:45];
 logic [31:0] plan_align1,plan_align2,plan_align3,plan_prefix12,plan_prefix123;
 always_comb begin
  for(integer i=0;i<46;i=i+1)fetch_bytes[i]=0;
  for(integer i=0;i<12;i=i+1)fetch_bytes[30+i]=prior_header[8*i+:8];
 end
 assign verify_ignored_high={fetch_bytes[41],fetch_bytes[37],fetch_bytes[33]};
 assign meta_prefix1=plan_align1;
 assign meta_prefix12=plan_prefix12;
 assign meta_prefix123=plan_prefix123;
'''+fn+'\n'+cache+'''
 assign old_plan2=sum3(32,aligned(32'(begin_blocks)*2),aligned(begin_count1*4));
 assign old_plan3=sum4(32,aligned(32'(begin_blocks)*2),aligned(begin_count1*4),aligned(begin_count2*4));
 assign old_used=sum5(32,aligned(32'(begin_blocks)*2),aligned(begin_count1*4),aligned(begin_count2*4),aligned(begin_count3*4));
 assign new_plan2=(32+aligned(32'(begin_blocks)*2))+meta_prefix1;
 assign new_plan3=(32+aligned(32'(begin_blocks)*2))+meta_prefix12;
 assign new_used=(32+aligned(32'(begin_blocks)*2))+meta_prefix123;
endmodule
''';(OUT/'prefix_math_probe.sv').write_text(text)
 print('PREFIX_EXTRACTED_MATH_AND_CACHE_PREPARED')
if __name__=='__main__':main()
