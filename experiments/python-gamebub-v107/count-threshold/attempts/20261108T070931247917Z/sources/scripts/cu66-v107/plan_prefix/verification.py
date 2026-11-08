#!/usr/bin/env python3
"""Prepare lossless whole-four-body paired adapters and public-interface bench."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];SRC=ROOT/'fpga/experiments/cu66-v107-plan-prefix';OUT=SRC/'verification'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 OUT.mkdir(exist_ok=True);recipe=json.loads((SRC/'edit-recipe.json').read_text());adapters=[]
 modules={'br88_packet_ingress_sync_v91h.sv':'ingress','br88_packet_ingress_v91h.sv':'packet','br88_pipeline_v91h.sv':'pipeline','packed_scratch_v91g2.sv':'scratch'}
 for file in recipe['files']:
  name=Path(file['candidate']).name;module=name[:-3];kind=modules[name]
  for variant,key in [('original','original'),('candidate','candidate')]:
   p=ROOT/file[key];s=p.read_text();edits=[(f'module {module} ',f'module {kind}_{variant} ')]
   if kind=='packet':edits.append(('br88_packet_ingress_sync_v91h #(',f'ingress_{variant} #('))
   if kind=='pipeline':edits.extend([('br88_packet_ingress_v91h #(',f'packet_{variant} #('),('packed_scratch_v91g2 scratch (',f'scratch_{variant} scratch (')])
   for before,after in edits:assert s.count(before)==1;s=s.replace(before,after,1)
   q=OUT/f'{kind}_{variant}.sv';q.write_text(s);adapters.append(dict(path=str(q.relative_to(ROOT)),source=str(p.relative_to(ROOT)),source_sha256=sha(p),sha256=sha(q),renames=edits))
 parent=(ROOT/'fpga/experiments/cu66-v106-telemetry/br88_pipeline_v91h.sv').read_text();header=parent.split(') (\n',1)[1].split('\n);',1)[0];parts=header.split(',');ports=[];prefix=None
 for item in parts:
  item=item.strip();m=re.match(r'(input|output)\s+logic\s+(signed\s+)?(\[[^\]]+\]\s*)?(.*)',item,re.S)
  if m:direction=m[1];prefix='logic '+(m[2] or '')+(m[3] or '');tail=m[4]
  else:tail=item
  name=re.match(r'(\w+)(.*)',tail,re.S);assert name,(item,prefix);ports.append(dict(direction=direction,prefix=prefix,name=name[1],tail=name[2]))
 probe='module prefix_probe #(parameter integer SYNC_STAGING=1) (\n'+',\n'.join('    '+p['direction']+' '+p['prefix']+p['name']+p['tail'] for p in ports)+''',
 output logic mismatch,
 output logic [31:0] verify_count1,verify_count2,verify_count3,
 output logic [31:0] verify_prefix1,verify_prefix12,verify_prefix123
);
'''
 for p in ports:
  if p['direction']=='output':probe+='    '+p['prefix']+'old_'+p['name']+p['tail']+';\n'
 for variant in ('original','candidate'):
  probe+=f'    pipeline_{variant} #(.SYNC_STAGING(SYNC_STAGING)) {"old_dut" if variant=="original" else "new_dut"} (\n'+',\n'.join('        .'+p['name']+'('+('old_' if variant=='original' and p['direction']=='output' else '')+p['name']+')' for p in ports)+'\n    );\n'
 probe+='    assign mismatch=!('+ '&&'.join(f'(old_{p["name"]}=={p["name"]})' for p in ports if p['direction']=='output')+');\n'
 for n in ('count1','count2','count3','prefix1','prefix12','prefix123'):probe+=f'    assign verify_{n}=new_dut.meta_{n};\n'
 probe+='endmodule\n';(OUT/'prefix_probe.sv').write_text(probe)
 baseline=ROOT/'fpga/experiments/cu66-v91h/tb_pipeline.cpp';body=baseline.read_text().replace('Vbr88_pipeline_v91h','Vprefix_probe');before='d.clk=1;d.eval();d.clk=0;d.eval();';after='prefix_pre(d);d.clk=1;d.eval();prefix_post(d);d.clk=0;d.eval();';assert body.count(before)==1;body=body.replace(before,after,1)
 body='#include "Vprefix_probe.h"\nstatic void prefix_pre(Vprefix_probe&);\nstatic void prefix_post(Vprefix_probe&);\nstatic unsigned long long prefix_edges=0,metadata_edges=0,metadata_held=0;\n'+body
 old='        return 0;';new='''        require(prefix_edges>1000&&metadata_edges>0,"prefix wholepipeline coverage floor");
        std::cout<<"{\\"type\\":\\"prefix_pair_verdict\\",\\"status\\":\\"TEST_PASS\\",\\"public_cycle_edges\\":"<<prefix_edges<<",\\"metadata_edges\\":"<<metadata_edges<<",\\"metadata_held_edges\\":"<<metadata_held<<"}\\n";
        return 0;''';assert body.count(old)==1;body=body.replace(old,new,1)
 body+='''
static void prefix_pre(Vprefix_probe&d){
 require(!d.mismatch,"complete4-body public outputs differ including invalid/debug/counters");
 if(d.dbg_meta_valid){
  const auto aligned=[](uint32_t x){return (uint32_t(x*4U+15U)&0xfffffff0U);};
  const uint32_t a=aligned(d.verify_count1),b=aligned(d.verify_count2),c=aligned(d.verify_count3);
  require(d.verify_prefix1==a&&d.verify_prefix12==uint32_t(a+b)&&d.verify_prefix123==uint32_t(a+b+c),"independent actual metadata count-prefix owner");
  ++metadata_edges;metadata_held+=!d.dbg_meta_ready;
 }
}
static void prefix_post(Vprefix_probe&d){require(!d.mismatch,"complete4-body public outputs changed after edge");++prefix_edges;}
'''
 (OUT/'tb_prefix.cpp').write_text(body);(OUT/'adapters.json').write_text(json.dumps(dict(adapters=adapters,original_header_ports=ports,original_bench=str(baseline.relative_to(ROOT)),original_bench_sha256=sha(baseline),bench_hooks=[dict(before=before,after=after)],scope='Complete original/candidate four production bodies; module/type renames only; no production hierarchy references. Verification probe observes new internal count/prefix wires only.'),indent=2,sort_keys=True)+'\n');print('PREFIX_PAIRED_ADAPTERS_PREPARED',len(adapters),len(ports))
if __name__=='__main__':main()
