#!/usr/bin/env python3
"""Lossless four-body adapters and independent packet-threshold proof benches."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];SRC=ROOT/'fpga/experiments/cu66-v107-count-threshold';BASE=ROOT/'fpga/experiments/cu66-v107-plan-prefix';OUT=SRC/'verification'
def main():
 OUT.mkdir(exist_ok=True)
 # Reuse the qualified prefix adapter generator with exact source-only changes.
 script=(ROOT/'scripts/cu66-v107/plan_prefix/verification.py').read_text()
 script=script.replace("SRC=ROOT/'fpga/experiments/cu66-v107-plan-prefix'", "SRC=ROOT/'fpga/experiments/cu66-v107-count-threshold'")
 script=script.replace("recipe=json.loads((SRC/'edit-recipe.json').read_text());adapters=[]", "raw=json.loads((SRC/'edit-recipe.json').read_text());recipe={'files':[dict(original=e['original'],candidate=str((SRC/n).relative_to(ROOT)),**{k:v for k,v in e.items() if k not in ('original',)}) for n,e in raw['production'].items()]};adapters=[]")
 script=script.replace('verify_prefix1,verify_prefix12,verify_prefix123\n','verify_prefix1,verify_prefix12,verify_prefix123,\n output logic [31:0] verify_threshold1,verify_threshold2,verify_threshold3\n')
 script=script.replace("('count1','count2','count3','prefix1','prefix12','prefix123')", "('count1','count2','count3','prefix1','prefix12','prefix123','threshold1','threshold2','threshold3')")
 script=script.replace('  ++metadata_edges;metadata_held', '''  require(d.verify_threshold1==d.verify_count1/5U+uint32_t(d.verify_count1%5U!=0),"independent threshold1 owner");
  require(d.verify_threshold2==d.verify_count2/15U+uint32_t(d.verify_count2%15U!=0),"independent threshold2 owner");
  require(d.verify_threshold3==d.verify_count3/43U+uint32_t(d.verify_count3%43U!=0),"independent threshold3 owner");
  ++metadata_edges;metadata_held''')
 exec(compile(script,'qualified_prefix_adapter_generator','exec'),{'__file__':str(ROOT/'scripts/cu66-v107/count_threshold/verification.py'),'__name__':'__main__'})
 old=(OUT/'ingress_original.sv').read_text();header=old.split(') (\n',1)[1].split('\n);',1)[0];ports=[];kind=prefix=None
 for item in header.split(','):
  item=item.strip();m=re.match(r'(input|output)\s+logic\s+(signed\s+)?(\[[^\]]+\]\s*)?(.*)',item,re.S)
  if m:kind=m[1];prefix='logic '+(m[2] or '')+(m[3] or '');item=m[4]
  m=re.match(r'(\w+)(.*)',item,re.S);assert m;ports.append(dict(direction=kind,prefix=prefix,name=m[1],tail=m[2]))
 body='module ingress_capture_probe (\n'+',\n'.join(' '+p['direction']+' '+p['prefix']+p['name']+p['tail'] for p in ports)+''',
 output logic mismatch,verify_capture,
 output logic [31:0] verify_a1,verify_a2,verify_a3,
 output logic [31:0] meta_threshold1,meta_threshold2,meta_threshold3,
 output logic [2:0] verify_threshold_live
);
'''
 for p in ports:
  if p['direction']=='output':body+=' '+p['prefix']+'old_'+p['name']+p['tail']+';\n'
 for v,label in [('original','old_dut'),('candidate','new_dut')]:
  args=['.'+p['name']+'('+('old_' if v=='original' and p['direction']=='output' else '')+p['name']+')' for p in ports]
  if v=='candidate':args+=['.meta_threshold1(meta_threshold1)','.meta_threshold2(meta_threshold2)','.meta_threshold3(meta_threshold3)']
  body+=' ingress_'+v+' '+label+'('+','.join(args)+');\n'
 body+=' assign mismatch=!('+'&&'.join('(old_'+p['name']+'=='+p['name']+')' for p in ports if p['direction']=='output')+');\n'
 body+=' assign verify_capture=new_dut.prefix_header_capture;\n assign verify_a1=new_dut.plan_align1;\n assign verify_a2=new_dut.plan_align2;\n assign verify_a3=new_dut.plan_align3;\n assign verify_threshold_live=new_dut.threshold_live;\nendmodule\n';(OUT/'ingress_capture_probe.sv').write_text(body)
 b=(BASE/'verification/tb_capture.cpp').read_text().replace('#include <vector>','#include <vector>\n#include <deque>')
 b=b.replace(' std::array<uint64_t,12>', ' std::array<uint64_t,12>') # no semantic edit
 b=b.replace(' Bench(unsigned seed', ''' std::array<std::deque<std::pair<uint64_t,uint32_t>>,3> threshold_queue;
 std::array<uint32_t,3> thresholds{};unsigned threshold_live=0;
 uint64_t threshold_commits=0,threshold_flush_commits=0,commit_abort_retries=0;
 static uint32_t ceil_count(uint32_t n,unsigned g){const unsigned d=g==0?5:g==1?15:43;return n/d+uint32_t(n%d!=0);}
 Bench(unsigned seed''',1)
 b=b.replace(' void check(){', ''' void check(){
  need(d.meta_threshold1==thresholds[0]&&d.meta_threshold2==thresholds[1]&&d.meta_threshold3==thresholds[2],"independent eight-edge threshold cache arithmetic/hold");
  need(d.verify_threshold_live==threshold_live,"independent threshold validity/flush ownership");''',1)
 needle='  d.clk=1;d.eval();p12=next12;p123=next123;check();'
 repl='''  const auto&r=*d.rootp;const bool flush=d.stage_cancel||(d.stage_context_active&&CTXN->done);
  for(unsigned g=0;g<3;++g){
   bool commit=!threshold_queue[g].empty()&&threshold_queue[g].front().first==edges;
   if(commit){thresholds[g]=ceil_count(threshold_queue[g].front().second,g);threshold_queue[g].pop_front();++threshold_commits;if(flush)++threshold_flush_commits;}
   if(flush){threshold_queue[g].clear();threshold_live&=~(1U<<g);}else if(commit)threshold_live|=1U<<g;
   if(expected_capture&&capture_index==int(g)&&!flush)threshold_queue[g].push_back({edges+8,count});
   need(threshold_queue[g].size()<=8,"threshold pipeline finite owner bound");
  }
  d.clk=1;d.eval();p12=next12;p123=next123;check();'''
 assert b.count(needle)==1;b=b.replace(needle,repl)
 b=b.replace("<<unsigned(d.error)<<'\\n'", "<<unsigned(d.error)<<','<<d.meta_threshold1<<','<<d.meta_threshold2<<','<<d.meta_threshold3<<','<<unsigned(d.verify_threshold_live)<<','<<flush<<'\\n'")
 b=b.replace('d.reset=d.start=d.abort_packet=0;}\n static std::vector', '''d.reset=d.start=d.abort_packet=0;
  auto&r=*d.rootp;BOTH(state,0U);BOTH(context_active,0U);BOTH(ram_valid,0U);
  for(unsigned quiet=0;quiet<8;++quiet)tick(false,-1,0);
 }
 static std::vector''',1)
 b=b.replace('tick(false,-1,0);tick(false,-1,0);BOTH(state,9U);','for(unsigned quiet=0;quiet<8;++quiet)tick(false,-1,0);BOTH(state,9U);')
 marker=' void high_metadata('
 extra=''' void flush_commit_retry(unsigned index,uint32_t n){
  clean();prepare(index,n,0);const unsigned slot=(index-33)/4;tick(true,int(slot),n);
  auto&r=*d.rootp;BOTH(state,0U);BOTH(context_active,0U);BOTH(ram_valid,0U);
  for(unsigned quiet=0;quiet<7;++quiet)tick(false,-1,0);
  d.abort_packet=1;tick(false,-1,0);d.abort_packet=0;need(threshold_live==0,"abort/commit collision retained live owner");
  raw(9000U+index,-1);++commit_abort_retries;
 }
'''
 assert b.count(marker)==1;b=b.replace(marker,extra+marker,1)
 b=b.replace(' for(int index:{33,37,41})', ' for(unsigned index:{33U,37U,41U})b.flush_commit_retry(index,0xffffffffU-uint32_t(b.rng()%128));\n for(int index:{33,37,41})',1)
 b=b.replace('b.raw_packets==4&&b.restarts==3&&b.held==2244','b.raw_packets==7&&b.restarts==3&&b.held==2295&&b.commit_abort_retries==3&&b.threshold_flush_commits>=3')
 b=b.replace('<<b.edges<<",\\\"positive_prepared_cases', '<<b.edges<<",\\\"threshold_commits\\\":"<<b.threshold_commits<<",\\\"threshold_flush_commits\\\":"<<b.threshold_flush_commits<<",\\\"commit_abort_retries\\\":"<<b.commit_abort_retries<<",\\\"positive_prepared_cases')
 (OUT/'tb_capture.cpp').write_text(b)
 # The exact production arithmetic block, with synthetic byte/selection plumbing.
 s=(SRC/'br88_packet_ingress_sync_v91h.sv').read_text();i=s.index('    // COUNT_THRESHOLD_PIPELINE_BEGIN');block=s[i:s.index('    // COUNT_THRESHOLD_PIPELINE_END',i)+len('    // COUNT_THRESHOLD_PIPELINE_END')]
 top='''module threshold_math_probe (
 input logic clk,reset,take,input logic [1:0] selected,
 input logic [31:0] numerator,input logic [16:0] blocks,
 output logic [31:0] meta_threshold1,meta_threshold2,meta_threshold3,
 output logic [2:0] live,output logic [2:0] bad
);
 logic [7:0] ram_data,fetch_bytes[0:45];logic [5:0] fetch_index;
 logic prefix_header_capture,cancelled,context_failure,context_active,ctx_done;
 logic [1:0] band;logic [16:0] context_blocks;logic [31:0] counts[0:3];
 assign ram_data=numerator[31:24];assign fetch_index=6'(33+4*32'(selected));
 assign prefix_header_capture=take&&!reset;assign cancelled=reset;
 assign context_failure=0;assign context_active=0;assign ctx_done=0;
 assign band=selected+2'd1;assign context_blocks=blocks;
 for(genvar g=0;g<46;g=g+1)begin:bytes_in
  if(g==30||g==34||g==38)begin: low assign fetch_bytes[g]=numerator[7:0];end
  else if(g==31||g==35||g==39)begin: middle assign fetch_bytes[g]=numerator[15:8];end
  else if(g==32||g==36||g==40)begin: high assign fetch_bytes[g]=numerator[23:16];end
  else begin: unused_byte assign fetch_bytes[g]=0;end
 end
 for(genvar g=0;g<4;g=g+1)begin: counts_in assign counts[g]=numerator;end
'''+block+'''
 assign live=threshold_live;
 assign bad={32'(blocks)<meta_threshold3,32'(blocks)<meta_threshold2,32'(blocks)<meta_threshold1};
endmodule
'''
 # descriptor_count_bad is a real block output; expose it instead of leaving it unused.
 top=top.replace('output logic [2:0] live,output logic [2:0] bad','output logic [2:0] live,output logic [2:0] bad,output logic selected_bad').replace(' assign live=threshold_live;',' assign selected_bad=descriptor_count_bad;\n assign live=threshold_live;')
 (OUT/'threshold_math_probe.sv').write_text(top)
 (OUT/'math-block.json').write_text(json.dumps(dict(production=str((SRC/'br88_packet_ingress_sync_v91h.sv').relative_to(ROOT)),extracted_sha256=hashlib.sha256(block.encode()).hexdigest(),exact_production_generate_block=True,limits='Arithmetic streaming probe only; synthetic byte plumbing. Full actual production capture/RAW proof is separate.'),indent=2)+'\n')
 print('THRESHOLD_VERIFICATION_PREPARED')
if __name__=='__main__':main()
