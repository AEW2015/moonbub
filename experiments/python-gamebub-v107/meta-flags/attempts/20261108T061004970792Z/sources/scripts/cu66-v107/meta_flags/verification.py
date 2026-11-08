#!/usr/bin/env python3
"""Generate transparent complete-module proof wrappers; no RTL execution."""
import re,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'fpga/experiments/cu66-v107-meta-flags/verification';OUT.mkdir(exist_ok=True)
def ports(text):
 header=text.split(');',1)[0]+');';pp=[];inherited=None
 for item in header.split('(',1)[1].rsplit(');',1)[0].split(','):
  item=item.strip();m=re.fullmatch(r'(input|output)\s+logic\s+(signed\s+)?(\[\d+:\d+\]\s+)?(.+)',item,re.S)
  if m:direction,signed,packed,item=m.groups();inherited=(direction,signed or '',packed or '')
  assert inherited,item
  m=re.fullmatch(r'(\w+)\s*(\[\d+:\d+\])?',item);assert m,item
  pp.append(dict(name=m[1],unpacked=m[2] or '',direction=inherited[0],signed=inherited[1],packed=inherited[2]))
 return header,pp

def main():
 stage=(OUT.parent/'cu66_coefficient_elastic.sv').read_text();h,sp=ports(stage)
 top=h.replace('module cu66_coefficient_elastic (','module meta_stage_probe (',1).replace(');',', output logic [10:0] probe_quant_cell);')
 top+='\ncu66_coefficient_elastic dut('+','.join('.'+p['name']+'('+p['name']+')' for p in sp)+');\nassign probe_quant_cell=dut.quant_cell(in_plane,in_tile);\nendmodule\n';(OUT/'meta_stage_probe.sv').write_text(top)
 bench=(ROOT/'fpga/experiments/cu66-v107-elastic/tb_elastic.cpp').read_text().replace('Vcu66_coefficient_elastic','Vmeta_stage_probe')
 bench=bench.replace('static void require(','''static unsigned independent_cell(unsigned p,unsigned t){
 const unsigned row=t/90,column=t%90;
 return p==0?(((row/2)*45+column/2)&2047U):(t&2047U);
}
static void require(''',1)
 bench=bench.replace('struct Event {bool push,pop,done;};','''static bool metadata_bad(const Token&t){return t.plane>2||t.tile>=(t.plane==0?5400U:1350U)||t.cell!=independent_cell(t.plane,t.tile);}
static bool domain_bad(const Token&t){const int value=int(t.value)-((t.value&32768U)?65536:0);return t.scale==3||value< -2048||value>2048;}
struct Event {bool push,pop,done;};''')
 bench=bench.replace('std::ofstream transcript;','bool static_mode=false;uint64_t static_edges=0,helper_cases=0,metadata_cases=0,domain_cases=0,flag_checks=0;unsigned flag_values=0,held_flag_values=0;\n std::ofstream transcript;')
 bench=bench.replace('if(d.out_valid)require(output()==queue.front(),"entire130-bit tuple mismatch");','''if(d.out_valid){require(output()==queue.front(),"entire130-bit tuple mismatch");
   require(bool(d.out_metadata_bad)==metadata_bad(queue.front()),"independent owned static metadata flag");
   require(bool(d.out_domain_bad)==domain_bad(queue.front()),"independent owned signed value/scale flag");++flag_checks;unsigned bits=unsigned(metadata_bad(queue.front()))*2U+unsigned(domain_bad(queue.front()));flag_values|=1U<<bits;if(!d.out_ready)held_flag_values|=1U<<bits;
  }''')
 bench=bench.replace('if(e.push||e.pop||kill||e.done)transcript','if(!static_mode&&(e.push||e.pop||kill||e.done))transcript')
 bench=bench.replace('++cycles;require(cycles<5000000,"finite clock watchdog");','++cycles;if(static_mode)++static_edges;require(static_edges<=67372000,"finite static-domain watchdog");require(cycles-static_edges<5000000,"finite clock watchdog");')
 add=''' void exhaustive(){
  begin();static_mode=true;d.in_valid=1;d.out_ready=1;d.input_done=0;
  Token t{11,12,0,1,65535,0,0,0,17};
  for(unsigned p=0;p<4;++p)for(unsigned tile=0;tile<8192;++tile){
   t.plane=p;t.tile=tile;t.cell=0;offer(t);d.eval();
   require(d.probe_quant_cell==independent_cell(p,tile),"full binary helper domain independent Cartesian oracle");++helper_cases;
   for(unsigned cell=0;cell<2048;++cell){t.cell=cell;offer(t);require(tick().push,"metadata exhaustive capture");++metadata_cases;}
  }
  t.plane=0;t.tile=0;t.cell=0;
  for(unsigned scale=0;scale<4;++scale)for(unsigned bits=0;bits<65536;++bits){t.scale=scale;t.value=bits;offer(t);require(tick().push,"domain exhaustive capture");++domain_cases;}
  d.in_valid=0;tick();require(queue.empty(),"exhaustive final tuple not delivered");static_mode=false;
  require(helper_cases==32768&&metadata_cases==67108864&&domain_cases==262144,"complete static domains");
 }
'''
 add+=''' void flag_transitions(){
  begin();
  for(unsigned bits=0;bits<4;++bits){
   Token a{100U+bits,200U+bits,0,1,65535,0,(bits&2U)?1U:0U,63,(bits&1U)?2049U:17U};
   Token b=a;b.epoch^=0xffffffffU;b.child^=0x55555555U;b.cell^=1;b.value=(bits&1U)?17U:2049U;
   offer(a);d.in_valid=1;d.out_ready=1;require(tick().push,"directed flag token capture");
   offer(b);d.out_ready=0;for(unsigned hold=0;hold<4;++hold){Event e=tick();require(!e.push&&!e.pop,"stalled differing flag offer overwrote owner");}
   d.out_ready=1;Event e=tick();require(e.push&&e.pop,"directed different flag replacement");
   d.in_valid=0;require(tick().pop,"directed replacement token missing");
  }
  d.input_done=1;tick();require(tick().done,"directed flag fence failed");d.input_done=0;
  require(flag_values==15&&held_flag_values==15,"all four flag combinations held and compared");
 }
'''
 bench=bench.replace(' void cancellation(',add+' void cancellation(',1)
 bench=bench.replace('require(argc==3,"seed transcript required");','require(argc==4,"seed transcript exhaustive-mode required");')
 bench=bench.replace('Bench b(seed,argv[2]);','Bench b(seed,argv[2]);if(std::stoul(argv[3]))b.exhaustive();b.flag_transitions();')
 bench=bench.replace('<<b.cycles<<",\\\"pushes', '<<b.cycles<<",\\\"static_edges\\\":"<<b.static_edges<<",\\\"helper_cases\\\":"<<b.helper_cases<<",\\\"metadata_cases\\\":"<<b.metadata_cases<<",\\\"domain_cases\\\":"<<b.domain_cases<<",\\\"flag_checks\\\":"<<b.flag_checks<<",\\\"pushes')
 (OUT/'tb_stage.cpp').write_text(bench)
 src=ROOT/'fpga/experiments/cu66-v107-value-check/cu66_inverse_stream_v91j.sv';old=src.read_text();new=(OUT.parent/'cu66_inverse_stream_v91j.sv').read_text();h,pp=ports(old)
 (OUT/'locality_original.sv').write_text(old.replace('module cu66_inverse_stream_v91j (','module locality_original (',1));(OUT/'locality_candidate.sv').write_text(new.replace('module cu66_inverse_stream_v91j (','module locality_candidate (',1))
 header=h.replace('module cu66_inverse_stream_v91j (','module locality_probe (',1).replace(');',', input logic verify_metadata_bad, verify_domain_bad, output logic probe_outputs_equal, probe_stores_equal, probe_state_equal, output logic [1023:0] probe_store0, probe_store1, output logic [5:0] probe_fill_index, output logic [31:0] probe_next_token, output logic [7:0] probe_fault);')
 lines=[header]
 for p in pp:
  if p['direction']=='output':lines.append(f"logic {p['signed']}{p['packed']} old_{p['name']}{p['unpacked']};")
 for module,inst,isold in [('locality_original','old_dut',True),('locality_candidate','new_dut',False)]:
  conns=['.'+p['name']+'('+('old_' if isold and p['direction']=='output' else '')+p['name']+')' for p in pp]
  if not isold:conns+=['.in_metadata_bad(verify_metadata_bad)','.in_domain_bad(verify_domain_bad)']
  lines.append(module+' '+inst+'('+','.join(conns)+');')
 lines.append('assign probe_outputs_equal = '+' && '.join('(old_'+p['name']+' == '+p['name']+')' for p in pp if p['direction']=='output')+';')
 internal=['running','finished_input','fill_index','emit_index','next_token','epochs','child_epochs','tokens','planes','scales','blocks','tiles','cells','input_metadata_bad','input_fault','dq_ready','dq_valid','dq_out_ready','dq_error','dq_id','dq_data','idct_ready','idct_valid','idct_out_ready','idct_error','idct_id','idct_data','unused_idct_cycles']
 lines.append('assign probe_state_equal = '+' && '.join('(old_dut.'+n+' == new_dut.'+n+')' for n in internal)+';')
 lines+=['assign probe_store0=new_dut.coefficients[0]; assign probe_store1=new_dut.coefficients[1];','assign probe_stores_equal=(old_dut.coefficients[0]==new_dut.coefficients[0])&&(old_dut.coefficients[1]==new_dut.coefficients[1]);','assign probe_fill_index=new_dut.fill_index; assign probe_next_token=new_dut.next_token; assign probe_fault=new_dut.input_fault;','endmodule'];(OUT/'locality_probe.sv').write_text('\n'.join(lines)+'\n')
 b=(ROOT/'fpga/experiments/cu66-v106-locality/tb_locality.cpp').read_text()
 b=b.replace('static void locality_pre(Vlocality_probe&d){','''static void locality_pre(Vlocality_probe&d){
 d.verify_metadata_bad=d.in_plane>2||d.in_tile>=(d.in_plane==0?5400U:1350U)||d.in_qcell!=qcell(d.in_plane,d.in_tile);
 const int signed_value=int(d.in_value)-((d.in_value&32768U)?65536:0);
 d.verify_domain_bad=d.in_qscale==3||signed_value< -2048||signed_value>2048;
 d.eval();need(d.probe_state_equal,"preedge all inverse control/owner/intermediate state comparison");''')
 b=b.replace('static void locality_post(Vlocality_probe&d){','static void locality_post(Vlocality_probe&d){\n need(d.probe_state_equal,"postedge all inverse control/owner/intermediate state comparison");')
 extra=r""" unsigned concurrent_math_cases=0;
 for(unsigned math:{2U,3U,4U})for(unsigned idx:{0U,1U,63U})for(unsigned kind=0;kind<7;++kind){
  if(kind==4&&idx!=0)continue;
  if(kind==5&&idx!=1)continue;
  Prepared c;c.index=idx;c.bank=0;run(c);
  d.reset=d.start=d.cancel=0;d.input_done=0;d.in_valid=1;d.in_index=idx;d.in_value=321;
  BOTH(running,1U);BOTH(finished_input,0U);BOTH(error,0U);BOTH(done,0U);BOTH(fill_bank,0U);BOTH(fill_index,idx);BOTH(bank_state[0],idx?1U:0U);BOTH(bank_state[1],3U);BOTH(math_bank,1U);BOTH(math_state,math);BOTH(tokens[1],99U);
  if(math==2){BOTH(dequant__DOT__state,2U);BOTH(dequant__DOT__out_id,98U);BOTH(dequant__DOT__out_error,0U);}
  else {BOTH(inverse__DOT__state,9U);BOTH(inverse__DOT__out_id,98U);BOTH(inverse__DOT__out_error,0U);}
  oracle.index=idx;oracle.meta[0]=input_meta(d);
  unsigned expected=math==2?5U:6U;
  if(kind==1){d.in_index=(idx+1)&63U;expected=1;}
  else if(kind==2){d.in_qcell^=1;expected=2;}
  else if(kind==3){d.in_value=2049;expected=3;}
  else if(kind==4){BOTH(next_token,0xffffffffU);oracle.token=0xffffffffU;expected=7;}
  else if(kind==5){d.input_done=1;expected=4;}
  else if(kind==6){d.in_qscale=3;expected=idx?2U:3U;}
  tick();need(d.error==expected,"exact input-vs-concurrent arithmetic fault priority");++concurrent_math_cases;
 }
"""
 marker=' const auto prepared_clocks=oracle.clocks'
 assert b.count(marker)==1;b=b.replace(marker,extra+marker,1)
 b=b.replace('<<seed<<",\\\"prepared_clocks', '<<seed<<",\\\"concurrent_math_cases\\\":"<<concurrent_math_cases<<",\\\"prepared_clocks')
 (OUT/'tb_inverse.cpp').write_text(b)
 historical=ROOT/'fpga/experiments/cu66-v91j/tb_inverse.cpp';h=historical.read_text().replace('Vcu66_inverse_stream_v91j','Vlocality_probe').replace('int main(int argc,char **argv)','int historical_inverse_main(int argc,char **argv)')
 before='d.clk=1;d.eval();++cycle;';assert h.count(before)==1;h=h.replace(before,'locality_pre(d);d.clk=1;d.eval();locality_post(d);++cycle;');(OUT/'historical_inverse.cpp').write_text(h)
 (OUT/'ports.json').write_text(json.dumps(dict(stage=sp,inverse=pp,state_comparisons=internal),indent=2)+'\n')
 print('PREPARED_WRAPPERS_AND_BENCHES')
if __name__=='__main__':main()
