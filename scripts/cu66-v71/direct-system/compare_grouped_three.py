"""Reconcile matched chronological three-frame native timelines without fps claims."""
from pathlib import Path
import hashlib,json,re
r=Path(__file__).resolve().parents[3];d=r/'fpga/experiments/cu66-v71/direct-system';out=d/'grouped-v001/comparison-three-v001.json';assert not out.exists();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
names={'base':d/'evidence/base-three-timeline01','grouped':d/'grouped-v001/evidence/group-three-timeline01'}
prior={'base':d/'evidence/full-pin02','grouped':d/'grouped-v001/evidence/full-key-P01'}
v=lambda line:{k:int(n)for k,n in re.findall(r'(\w+)=(\d+)',line)}
rows={};proofs={}
stage_names=['IDLE','PARSER_START','METADATA','WAIT_BANK','BASE_START','BASE_RUN','WAIT_CACHE','CACHE_PREPARE_START','CACHE_PREPARE_RUN','COMMIT_READY','COMMIT_ACK','DRAIN']
fields=['fid','key','generation','cycles','actual_writes','actual_read_bursts','ACT','PRE','REF','underruns','cache_prepare_cycles','processor_commit_calls']
for name,p in names.items():
 assert json.loads((p/'result.json').read_text())['frames']==3
 for n,h in json.loads((p/'source-freeze.json').read_text()).items():assert sha(r/n)==h,n
 lines=(p/'frames.log').read_text().splitlines();frames=[v(x)for x in lines if x.startswith('SYSTEM_FRAME_PASS')];old=[v(x)for x in (prior[name]/'frames.log').read_text().splitlines()if x.startswith('SYSTEM_FRAME_PASS')]
 assert len(frames)==3
 for a,b in zip(frames[:2],old):assert all(a[k]==b[k]for k in fields),'Observerchangedpriortransaction'
 stages=[v(x)for x in lines if x.startswith('DY71_STAGE')];durations={}
 for a,b in zip(stages,stages[1:]):
  if a['generation']and a['stage']!=0:durations.setdefault(str(a['generation']),{})[stage_names[a['stage']]]=b['cycle']-a['cycle']
 for f in frames:assert sum(durations[str(f['generation'])].values())+1==f['cycles'],'Missinglaunch/stageclock'
 presentations=[v(x)for x in lines if x.startswith('DY71_PRESENTED')];canvas=[v(x)for x in lines if x.startswith('DY71_FIRST_CANVAS')];rasters=[v(x)for x in lines if x.startswith('DY71_RASTER')]
 assert [x['generation']for x in presentations]==[1,2,3]and [x['generation']for x in canvas]==[1,2,3]
 clean=sorted(set(x['generation']for x in rasters if x['black_lines']==0))
 rows[name]={'frames':frames,'stage_cycles_by_generation':durations,'launch_edge_cycles_per_frame':1,'presentations':presentations,'first_canvas_pixels':canvas,'complete_rasters':rasters,'generations_with_complete_clean_raster':clean,'presentation_intervals_clocks':[b['cycle']-a['cycle']for a,b in zip(presentations,presentations[1:])],'summary':v(next(x for x in lines if x.startswith('SYSTEM_PASS'))),'first_two_transactions_reproduce_prior':True}
 for f in [p/'source-freeze.json',p/'result.json',p/'frames.log',p/'execution.json',p/'tb.cpp',p/'cu71_direct_system_sim.sv',prior[name]/'frames.log']:proofs[f.relative_to(r).as_posix()]=sha(f)
assert rows['base']['presentations']==rows['grouped']['presentations']and rows['base']['first_canvas_pixels']==rows['grouped']['first_canvas_pixels']
# Hardware module identities and bytes must match except the isolated bridge.
base=json.loads((d/'sources.json').read_text());group=json.loads((d/'grouped-v001/sources.json').read_text());bs={Path(n).name:r/n for n in base['sources']};gs={Path(n).name:r/n for n in group['sources']};assert bs.keys()==gs.keys()
changes=[n for n in bs if sha(bs[n])!=sha(gs[n])];assert changes==['cu71_word_bridge_direct.sv'],changes
out.write_text(json.dumps({'status':'MATCHED_NATIVE_FUNCTIONAL_COMPARISON_COMPLETE','only_changed_hardware_module':changes,'rows':rows,'proofs':proofs,'memory_clock_ns':10,'scope':'SamechronologicalKEY/P/P,nativeHUDserviceoutsideHDLtime,realpinmodel,BASEowner. NoPHY/map/codec changes. Positivefunctionalresultisnotboardtiming/CDCqualification.','interpretation':'Groupingremovesobservedblacklines/underrunswhilePtransactionsgetlonger;presentationtimesidenticalforthisthreeframecohort. Noste ady30fpsclaim.'.replace('Noste ady','Nosteady'),'timer_expiry_counter_caveat':'Registersincludeexpirywhilecontrollerbusy;reservedidlecountsareIDLE-qualified.','hardware':False},indent=2)+'\n');print(json.dumps({'output':str(out),'sha256':sha(out),'base_underruns':rows['base']['summary']['total_underruns'],'group_underruns':rows['grouped']['summary']['total_underruns'],'group_P2_cycles':rows['grouped']['frames'][2]['cycles']}))
