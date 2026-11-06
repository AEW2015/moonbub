"""Same frozen DY71 RTL with verification-only bounded phase/failure taps."""
from pathlib import Path
script=Path(__file__).with_name('run.py');source=script.read_text()
def wrap(text):
 text=text.replace('output wire [31:0] rgb_completed_writes\n','output wire [31:0] rgb_completed_writes,\n    output wire [31:0] trace_flags,trace_line,trace_fill,trace_page,trace_prepare,trace_cookie,trace_lcdwait\n')
 bindings={
 'trace_flags':"{10'd0,hardware.scanout.result_held,hardware.scanout.switch_now,hardware.receiver.b_busy,hardware.receiver.write_pending,hardware.receiver.ref_pending,hardware.scanout.lcd.line_good,(hardware.scanout.lcd.fill==479&&hardware.scanout.lcd.receiving&&hardware.scanout.line_data_valid),hardware.scanout.dma_result_valid,hardware.lcd_rsp_ready,hardware.lcd_rsp_valid,hardware.lcd_req_ready,hardware.lcd_req_valid,hardware.scanout.inflight_front,hardware.scanout.render_active,hardware.scanout.p_active,hardware.scanout.f_active,hardware.scanout.request_next_c_ready,hardware.scanout.request_c_ready,hardware.scanout.request_y_ready,hardware.scanout.cache_ready,hardware.scanout.line_req_ready,hardware.scanout.line_req_valid}",
 'trace_line':"{11'd0,hardware.scanout.lcd.py,hardware.scanout.line_req_context,hardware.scanout.line_req_line}",
 'trace_fill':"{10'd0,hardware.scanout.lcd.selected,hardware.scanout.lcd.address_pending,hardware.scanout.lcd.receiving,hardware.scanout.lcd.captured_line,hardware.scanout.lcd.fill}",
 'trace_page':"{5'd0,hardware.scanout.front_next_u,hardware.scanout.f_chunk,hardware.scanout.f_tile_y,hardware.scanout.f_kind,hardware.scanout.f_group}",
 'trace_prepare':"{5'd0,hardware.scanout.p_slot,hardware.scanout.p_hud_offset,hardware.scanout.p_chunk,hardware.scanout.p_tile_y,hardware.scanout.p_phase}",
 'trace_cookie':'hardware.scanout.inflight_cookie',
 'trace_lcdwait':'hardware.memory.lcd_max_wait'}
 text=text.replace('endmodule','\n'+''.join(' assign '+key+'='+val+';\n'for key,val in bindings.items())+'endmodule')
 return text
def instrument(text):
 text=text.replace('#include <memory>','#include <memory>\n#include <deque>\n#include <sstream>\n#include <array>')
 at=text.index(' void pixel_check(){')
 methods=r'''
 std::deque<std::string> trace_ring;
 unsigned trace_old_flags=0,trace_old_line=0,trace_old_page=0,trace_old_pre=0,trace_old_stage=999,trace_old_underruns=0;
 uint64_t trace_phase_cycles[32]{},trace_first_failure=0,trace_req_at=0,trace_line_at=0;
 uint64_t trace_cmd_latency_max[2]{},trace_cmd_count[2]{},trace_cmd_sum[2]{},trace_line_wait_max=0,trace_line_fill_max=0;
 bool trace_request_owned=false,trace_request_front=false,trace_line_owned=false;
 unsigned trace_pending_line=0,trace_pending_cookie=0,trace_post_left=0;
 void trace_note(const char*event){
  std::ostringstream out;out<<"DY71_TRACE cycle="<<cycles<<" event="<<event<<" stage="<<unsigned(d.stage)<<" active_gen="<<d.active_generation<<" active_fid="<<d.active_frame_id<<" front_gen="<<d.lcd_front_generation<<" front_fid="<<d.lcd_front_frame_id<<" flags="<<d.trace_flags<<" line="<<d.trace_line<<" fill="<<d.trace_fill<<" page="<<d.trace_page<<" prepare="<<d.trace_prepare<<" cookie="<<d.trace_cookie<<" backend_wait="<<d.trace_lcdwait<<" underruns="<<d.lcd_underruns;
  if(trace_first_failure){if(trace_post_left){std::cout<<out.str()<<'\n';--trace_post_left;}}
  else{trace_ring.push_back(out.str());if(trace_ring.size()>512)trace_ring.pop_front();}
 }
 void trace_cycle(){
  unsigned f=d.trace_flags;trace_phase_cycles[unsigned(d.stage)&31]++;
  if(d.stage!=trace_old_stage||d.trace_prepare!=trace_old_pre&&(f&(1u<<7))||((d.trace_page^trace_old_page)&511))trace_note("phase_or_page");
  if((f&1)&&(!trace_line_owned||(d.trace_line&1023)!=trace_pending_line)){trace_line_owned=true;trace_pending_line=d.trace_line&1023;trace_line_at=cycles;trace_note("line_request");}
  if((f&3)==3&&trace_line_owned){trace_line_wait_max=std::max(trace_line_wait_max,cycles-trace_line_at);trace_note("line_admit");}
  if((f&(1u<<15))&&!(trace_old_flags&(1u<<15))){trace_line_fill_max=std::max(trace_line_fill_max,cycles-trace_line_at);trace_note("line_fill_done");trace_line_owned=false;}
  if((f&(1u<<10))&&(f&(1u<<11))&&!trace_request_owned){trace_request_owned=true;trace_request_front=f&(1u<<9);trace_req_at=cycles;trace_pending_cookie=d.trace_cookie;}
  if((f&(1u<<14))&&!(trace_old_flags&(1u<<14))&&trace_request_owned){unsigned owner=trace_request_front?1:0;uint64_t elapsed=cycles-trace_req_at;trace_cmd_latency_max[owner]=std::max(trace_cmd_latency_max[owner],elapsed);trace_cmd_sum[owner]+=elapsed;trace_cmd_count[owner]++;if(elapsed>80)trace_note("long_dma_completion");trace_request_owned=false;}
  if(d.lcd_underruns!=trace_old_underruns){
   if(!trace_first_failure){for(auto&s:trace_ring)std::cout<<s<<'\n';trace_first_failure=cycles;trace_post_left=2048;}
   trace_note("underrun_counter");
  }
  trace_old_flags=f;trace_old_line=d.trace_line;trace_old_page=d.trace_page;trace_old_pre=d.trace_prepare;trace_old_stage=d.stage;trace_old_underruns=d.lcd_underruns;
 }
 void trace_summary(){
  std::cout<<"DY71_TRACE_SUMMARY first_underrun_cycle="<<trace_first_failure<<" request_to_admit_max="<<trace_line_wait_max<<" request_to_fill_max="<<trace_line_fill_max<<" front_dma_commands="<<trace_cmd_count[1]<<" front_dma_cycles="<<trace_cmd_sum[1]<<" front_dma_max="<<trace_cmd_latency_max[1]<<" prepare_dma_commands="<<trace_cmd_count[0]<<" prepare_dma_cycles="<<trace_cmd_sum[0]<<" prepare_dma_max="<<trace_cmd_latency_max[0]<<" backend_wait_max="<<d.trace_lcdwait<<" bounded_ring=512 bounded_post=2048"<<std::endl;
  for(unsigned i=0;i<32;i++)if(trace_phase_cycles[i])std::cout<<"DY71_PHASE stage="<<i<<" cycles="<<trace_phase_cycles[i]<<std::endl;
 }
'''
 text=text[:at]+methods+text[at:]
 text=text.replace('  if(x==0){line_matches=', '  if(x==0){if(y>=40&&y<760)trace_note((d.trace_flags&(1u<<16))?"active_good":"active_missed");line_matches=')
 text=text.replace('cycles++;\n  if(e.packet_rsp)', 'cycles++;trace_cycle();\n  if(e.packet_rsp)')
 text=text.replace(' std::cout<<"SYSTEM_PASS complete_frames=', ' s.trace_summary();\n std::cout<<"SYSTEM_PASS complete_frames=')
 return text
source=source.replace("(o/'cu71_direct_system_sim.sv').write_text(header+body,newline='\\n')","(o/'cu71_direct_system_sim.sv').write_text(wrap(header+body),newline='\\n')")
source=source.replace(" s=s.replace('int main(','int run(')"," if kind=='frames':s=instrument(s)\n s=s.replace('int main(','int run(')")
source=source.replace("d/'sources.json',Path(__file__).resolve()","d/'sources.json',script,Path(__file__).resolve()")
exec(compile(source,str(script),'exec'),globals())
