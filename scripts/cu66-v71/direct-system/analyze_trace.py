"""Bind the retained first DY71 cadence failure to unchanged base/native runs."""
from pathlib import Path
import hashlib,json,re
r=Path(__file__).resolve().parents[3];d=r/'fpga/experiments/cu66-v71/direct-system';run=d/'evidence/full-trace01';control=d/'evidence/full-pin02';o=d/'first-failure-trace-v001.json';assert not o.exists();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name,h in json.loads((run/'source-freeze.json').read_text()).items():assert sha(r/name)==h,name
lines=(run/'frames.log').read_text().splitlines();base=(control/'frames.log').read_text().splitlines()
assert [x for x in lines if x.startswith('SYSTEM_')]==[x for x in base if x.startswith('SYSTEM_')],'Observerchangedoutcomes'
def values(line):return{k:int(v)for k,v in re.findall(r'(\w+)=(\d+)',line)}
events=[]
for line in lines:
 if line.startswith('DY71_TRACE cycle='):
  v=values(line);v['event']=re.search(r'event=(\w+)',line).group(1);v['requested_line']=v['line']&1023;v['raw_panel_line']=(v['line']>>11)&1023;v['captured_line']=(v['fill']>>9)&1023;v['page_group']=v['page']&127;v['page_kind']=(v['page']>>7)&3;v['page_tile_y']=(v['page']>>9)&63;v['page_chunk']=(v['page']>>15)&3;events.append(v)
failure=next(e for e in events if e['event']=='underrun_counter');line=failure['raw_panel_line'];generation=failure['front_gen'];before=[e for e in events if e['cycle']<=failure['cycle']]
deadline=next(e for e in before if e['event']=='active_missed'and e['raw_panel_line']==line and e['front_gen']==generation)
request=max((e for e in before if e['event']=='line_request'and e['requested_line']==line and e['front_gen']==generation),key=lambda e:e['cycle'])
admit=next(e for e in events if e['cycle']>=request['cycle']and e['event']=='line_admit'and e['requested_line']==line and e['front_gen']==generation)
fill=next(e for e in events if e['cycle']>=admit['cycle']and e['event']=='line_fill_done'and e['captured_line']==line and e['front_gen']==generation)
job=lambda kind,group:max((e for e in before if e['event']=='phase_or_page'and e['page_kind']==kind and e['page_group']==group and e['page_tile_y']==0 and e['page_chunk']==0 and e['flags']&64),key=lambda e:e['cycle'])
jobs=[job(1,3),job(2,3),job(0,6)];summary=values(next(x for x in lines if x.startswith('DY71_TRACE_SUMMARY')))
flag_names=['line_valid','line_ready','cache_ready','Y_ready','C_ready','halo_ready','front_page_active','prepare_active','render_active','inflight_front','LCD_req_valid','LCD_req_ready','LCD_rsp_valid','LCD_rsp_ready','DMA_result','LCD_fill_done','pixel_line_good','reference_pending','write_pending','base_busy','switch_now','prepared_result_held']
proofs={str(p.relative_to(r)):sha(p)for p in [run/'result.json',run/'source-freeze.json',run/'execution.json',run/'frames.log',run/'tb.cpp',run/'cu71_direct_system_sim.sv',control/'frames.log',Path(__file__).resolve()]}
data={'status':'REPRODUCED_BASE_CADENCE_FAILURE_RETAINED_FIRST_WINDOW','same_system_outcome_lines_as_base':True,'proofs':proofs,'first_failure':failure,'decoded_first_flags':{n:bool(failure['flags']&(1<<i))for i,n in enumerate(flag_names)},'first_line_timeline':{'request':request,'active_deadline':deadline,'admitted':admit,'LCD_fill_complete_offer':fill,'request_to_admit_clocks':admit['cycle']-request['cycle'],'request_to_fill_clocks':fill['cycle']-request['cycle'],'fill_after_deadline_clocks':fill['cycle']-deadline['cycle'],'Y_page_start_to_admit_clocks':admit['cycle']-jobs[2]['cycle'],'Y_page_start_deadline_budget_clocks':deadline['cycle']-jobs[2]['cycle']},'preceding_front_page_starts':jobs,'aggregate_observers':summary,'measured_clock_ns':10,'interpretation':'FirstmissoccursduringPBASE_RUN,PREPAREinactive,Ygroup6notready,C+haloREADY. EarlierCb/Crgroup3frontpageworkdelaysYgroup6start; actualreference-read/write contentionisconcurrent, butitscausalcostversusjob-schedulingneedsmatchedmeasurement. Nofixselected.','limits':['Alltimestampslocalnativeclock;cyclequantizedoffers/readinesshaveapproximatelyoneclockedgeuncertainty','First512pre/2048posteventwindowonly;notall596missesindividuallyretained','Aggregate request/fill maxima arenotindependently pairedpixeldeadlineproof for everyline','Two-statepinmodeland1psmonitorcompatibility;notphysicalSDRAMtimingsignoff','NoESP/liveQSPI/network/HWplaybackor30fpsclaim'],'hardware':False}
o.write_text(json.dumps(data,indent=2)+'\n');print(json.dumps({'path':str(o),'sha256':sha(o),'line':line,'request_to_admit':admit['cycle']-request['cycle'],'fill_after_deadline':fill['cycle']-deadline['cycle']}))
