"""Observation-only frame-pulse/idle audit; --prior selects pre-SYNCsafe math."""
from pathlib import Path
import sys
prior='--prior'in sys.argv
if prior:sys.argv.remove('--prior')
if '--grouped'not in sys.argv:sys.argv.insert(1,'--grouped')
timeline=Path(__file__).resolve().parents[1]/'run_timeline.py';s=timeline.read_text()
def fence_instrument(text):
 at=text.index(' void pixel_check(){')
 methods=r'''
 bool fence_last_idle=false;uint64_t fence_idle_changed=0,fence_idle_transitions=0,fence_idle_cycles=0;unsigned fence_pending_logs=0,fence_pulses=0;
 void fence_cycle(){
  if(d.lcd_scanout_drained)fence_idle_cycles++;
  if(bool(d.lcd_scanout_drained)!=fence_last_idle){fence_idle_changed=cycles;fence_idle_transitions++;fence_last_idle=d.lcd_scanout_drained;
   if(d.lcd_pending&&fence_pending_logs<64){std::cout<<"DY71_IDLE_FENCE cycle="<<cycles<<" idle="<<unsigned(d.lcd_scanout_drained)<<" pending="<<unsigned(d.lcd_pending)<<" active_generation="<<d.active_generation<<" front_generation="<<d.lcd_front_generation<<std::endl;fence_pending_logs++;}}
  if(d.lcd_frame_boundary){fence_pulses++;std::cout<<"DY71_FRAME_FENCE cycle="<<cycles<<" idle="<<unsigned(d.lcd_scanout_drained)<<" last_idle_change="<<fence_idle_changed<<" pending="<<unsigned(d.lcd_pending)<<" active_generation="<<d.active_generation<<" front_generation="<<d.lcd_front_generation<<std::endl;}
 }
'''
 text=text[:at]+methods+text[at:];text=text.replace('cycles++;timeline_cycle();','cycles++;timeline_cycle();fence_cycle();')
 text=text.replace(' std::cout<<"SYSTEM_PASS complete_frames=', ' std::cout<<"DY71_FENCE_SUMMARY pulses="<<s.fence_pulses<<" idle_transitions="<<s.fence_idle_transitions<<" idle_cycles="<<s.fence_idle_cycles<<" pending_transition_logs="<<s.fence_pending_logs<<std::endl;\n std::cout<<"SYSTEM_PASS complete_frames=')
 return text
s=s.replace("script=Path(__file__).with_name('run.py')","script=Path(__file__).resolve().parents[1]/'run.py'")
target='cu71_system_direct_math'if prior else'cu71_system_direct_syncsafe';selection='board-math-v001'if prior else'syncsafe-math-v002'
s=s.replace('source=script.read_text()',"source=script.read_text().replace('parents[3]','parents[4]').replace(' cu71_system_direct #(',' "+target+" #(')")
s=s.replace("m=json.loads((d/'grouped-v001/sources.json').read_text())","m=json.loads((d/'"+selection+"/sources.json').read_text())")
s=s.replace("d/'sources.json',d/'grouped-v001/sources.json',script,Path(__file__).resolve()","d/'sources.json',d/'"+selection+"/sources.json',Path(__file__).resolve().parents[1]/'run_timeline.py',script,Path(__file__).resolve()")
s=s.replace("if kind=='frames':s=instrument(s)","if kind=='frames':s=fence_instrument(instrument(s))")
exec(compile(s,str(timeline),'exec'),globals())
