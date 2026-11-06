"""Preserve first control proof and strengthen held-window observations only."""
from pathlib import Path
r=Path(__file__).resolve().parents[3];old=r/'fpga/experiments/cu66-v71/direct-system/grouped-v001/tb_grouped.cpp';new=old.with_name('tb_grouped_v2.cpp');assert not new.exists()
s=old.read_text().replace('hold_start=0,held_LCD=0;','hold_start=0,held_LCD=0,held_BG=0;').replace('hold_start=cycle;held_LCD=LCD;','hold_start=cycle;held_LCD=LCD;held_BG=BG;')
needle='  for(unsigned i=0;i<4;i++)if(rsp[i]){';assert s.count(needle)==1
s=s.replace(needle,'''  if(mode==2&&hold_start&&cycle<hold_start+100){
   need(d.p0_rsp_valid&&!d.p0_rsp_error&&d.p0_rsp_data==0,"held valid/data/error did not persist");
   if(cycle==hold_start+99)need(LCD>held_LCD&&BG>held_BG,"unrelated progress occurred only after held response release");
  }
'''+needle).replace('GROUPED_FAIRNESS_PASS checks=','GROUPED_FAIRNESS_V2_PASS held_window_progress_checked=1 checks=')
new.write_text(s,newline='\n');runner=Path(__file__).with_name('run_grouped_fairness.py');nr=runner.with_name('run_grouped_fairness_v2.py');assert not nr.exists()
q=runner.read_text().replace('evidence/fairness01','evidence/fairness02').replace('tb_grouped.cpp','tb_grouped_v2.cpp').replace("'GROUPED_FAIRNESS_PASS'","'GROUPED_FAIRNESS_V2_PASS'").replace('PASS_GROUPED_CONTINUOUS_QUOTA_LOCALS_AND_RESPONSE_ISOLATION','PASS_GROUPED_V2_EXPLICIT_HELD_WINDOW_PROGRESS');nr.write_text(q,newline='\n')
