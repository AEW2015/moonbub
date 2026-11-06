"""Event-only actual pin replay, old-record shadow and immediate public diag reads."""
from pathlib import Path
import ast
here=Path(__file__).resolve();root=here.parents[4];scripts=here.parents[1];grouped=True
# Reuse exact baseline observation functions without executing their runners.
for path,names in [(scripts/'run_timeline.py',['wrap','instrument']),(scripts/'board-math/run_fence_timeline.py',['fence_instrument'])]:
 text=path.read_text();tree=ast.parse(text)
 for node in tree.body:
  if isinstance(node,ast.FunctionDef)and node.name in names:exec(compile(ast.get_source_segment(text,node),str(path),'exec'),globals())
def event_wrap(text):
 end=text.index(');');text=text[:end].rstrip()+',\n output wire[255:0] event_probe_record,output wire[7:0]event_probe_code,output wire[31:0]event_probe_sequence,event_probe_overwrites\n'+text[end:]
 rec="{8'd0,hardware.receiver.last_address,hardware.receiver.stage,hardware.receiver.event_code,hardware.receiver.fatal_code,8'd0,hardware.receiver.event_fid,hardware.receiver.event_generation[63:32],hardware.receiver.event_generation[31:0],hardware.receiver.clock_count[63:32],hardware.receiver.clock_count[31:0],hardware.receiver.event_sequence}"
 return text.replace('endmodule','assign event_probe_record='+rec+';\nassign event_probe_code=hardware.receiver.event_code;assign event_probe_sequence=hardware.receiver.event_sequence;assign event_probe_overwrites=hardware.receiver.event_overwrites;\nendmodule')
def event_cpp(text):
 methods=r'''
 uint32_t event_shadow[8][8]{};uint32_t event_expected_sequence=0,event_expected_overwrites=0;
 bool event_check_now=false,event_flush=false;unsigned event_checks=0,event_traces=0;
 void event_before(){
  event_check_now=d.rst||d.event_probe_code||event_flush;event_flush=d.event_probe_code&&!d.rst;
  if(d.rst){for(auto &slot:event_shadow)for(auto &word:slot)word=0;event_expected_sequence=event_expected_overwrites=0;}
  else if(d.event_probe_code){
   for(unsigned word=0;word<8;word++)event_shadow[event_expected_sequence&7][word]=d.event_probe_record[word];
   if(event_traces<128){std::cout<<"EVENT_TRACE cycle="<<cycles<<" sequence="<<event_expected_sequence<<" code="<<unsigned(d.event_probe_code)<<" fid="<<d.event_probe_record[5]<<" generation_lo="<<d.event_probe_record[3]<<" clock_lo="<<d.event_probe_record[1]<<" stage_code_reason="<<d.event_probe_record[6]<<" address="<<d.event_probe_record[7]<<std::endl;event_traces++;}
   if(event_expected_sequence>=8)event_expected_overwrites++;event_expected_sequence++;
  }
 }
 void event_after(){
  need(d.event_probe_sequence==event_expected_sequence&&d.event_probe_overwrites==event_expected_overwrites,"originaledgeeventlogicalcounter");
  if(!event_check_now)return;
  unsigned saved=d.diag_address;
  for(unsigned slot=0;slot<8;slot++)for(unsigned word=0;word<8;word++){
   d.diag_address=0x100+slot*32+word*4;d.eval();need(d.diag_data==event_shadow[slot][word],"actualpubliceventdiagoldedgeexact");event_checks++;
  }
  d.diag_address=0x058;d.eval();need(d.diag_data==event_expected_sequence,"publiceventsequence");
  d.diag_address=0x05c;d.eval();need(d.diag_data==event_expected_overwrites,"publiceventoverwrites");
  d.diag_address=saved;d.eval();
 }
'''
 text=text.replace('struct Sim{','struct Sim{\n'+methods)
 old='d.clk=1;d.eval();';assert text.count(old)==1;text=text.replace(old,'event_before();d.clk=1;d.eval();event_after();')
 text=text.replace('std::cout<<"SYSTEM_CONTROL_PASS','std::cout<<"EVENT_DIAG_CHECKS checks="<<s.event_checks<<" traces="<<s.event_traces<<std::endl;\n std::cout<<"SYSTEM_CONTROL_PASS')
 text=text.replace(' std::cout<<"SYSTEM_PASS',' std::cout<<"EVENT_DIAG_CHECKS checks="<<s.event_checks<<" traces="<<s.event_traces<<std::endl;\n std::cout<<"SYSTEM_PASS')
 return text
script=scripts/'run.py';source=script.read_text().replace('parents[3]','parents[4]').replace(' cu71_system_direct #(',' cu71_system_eventpipe #(')
source=source.replace("m=json.loads((d/'sources.json').read_text())","m=json.loads((d/'event-retime-v001/sources.json').read_text())")
source=source.replace("(o/'cu71_direct_system_sim.sv').write_text(header+body,newline='\\n')","(o/'cu71_direct_system_sim.sv').write_text(event_wrap(wrap(header+body)),newline='\\n')")
source=source.replace(" s=s.replace('int main(','int run(')"," if kind=='frames':s=fence_instrument(instrument(s))\n s=event_cpp(s)\n s=s.replace('int main(','int run(')")
source=source.replace("d/'sources.json',Path(__file__).resolve()","d/'sources.json',d/'event-retime-v001/sources.json',d/'event-retime-v001/patch.json',scripts/'run_timeline.py',scripts/'board-math/run_fence_timeline.py',script,Path(__file__).resolve()")
exec(compile(source,str(script),'exec'),globals())
