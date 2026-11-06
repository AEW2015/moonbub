"""Source-bound same-group BASE/PIPE owner native comparison."""
from pathlib import Path
import hashlib,json,re
r=Path(__file__).resolve().parents[3];d=r/'fpga/experiments/cu66-v71/direct-system';p=d/'pipe-v001';out=p/'qualification-three-v001.json';assert not out.exists();sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();dirs={'base_owner':d/'grouped-v001/evidence/group-three-timeline01','pipe_owner':p/'evidence/pipe-group-three-timeline01'};rows={};proofs={};v=lambda line:{k:int(n)for k,n in re.findall(r'(\w+)=(\d+)',line)}
for name,run in dirs.items():
 result=json.loads((run/'result.json').read_text());assert result['frames']==3
 for n,h in json.loads((run/'source-freeze.json').read_text()).items():assert sha(r/n)==h,n
 lines=(run/'frames.log').read_text().splitlines();frames=[v(x)for x in lines if x.startswith('SYSTEM_FRAME_PASS')];present=[v(x)for x in lines if x.startswith('DY71_PRESENTED')];canvas=[v(x)for x in lines if x.startswith('DY71_FIRST_CANVAS')];rasters=[v(x)for x in lines if x.startswith('DY71_RASTER')];summary=v(next(x for x in lines if x.startswith('SYSTEM_PASS')))
 assert len(frames)==3 and [x['fid']for x in frames]==[0,1,2]and summary['total_underruns']==0 and summary['black_lines']==0
 assert sorted(set(x['generation']for x in rasters if x['black_lines']==0))==[1,2,3]
 for f in frames:assert f['actual_writes']==428160
 assert frames[1]['processor_commit_calls']>=2
 stages=[v(x)for x in lines if x.startswith('DY71_STAGE')];durations={}
 for a,b in zip(stages,stages[1:]):
  if a['generation']and a['stage']!=0:durations.setdefault(str(a['generation']),{})[str(a['stage'])]=b['cycle']-a['cycle']
 for f in frames:assert sum(durations[str(f['generation'])].values())+1==f['cycles']
 rows[name]={'frames':frames,'stage_cycles':durations,'presented':present,'first_canvas':canvas,'complete_rasters':rasters,'summary':summary}
 for f in [run/'frames.log',run/'result.json',run/'source-freeze.json',run/'execution.json',run/'tb.cpp',run/'cu71_direct_system_sim.sv']:proofs[f.relative_to(r).as_posix()]=sha(f)
assert rows['base_owner']['presented']==rows['pipe_owner']['presented']and rows['base_owner']['first_canvas']==rows['pipe_owner']['first_canvas']
base=d/'cu71_system_direct.sv';top=p/'cu71_system_direct_pipe.sv';normalized=top.read_text().replace('module cu71_system_direct_pipe #(','module cu71_system_direct #(').replace('    cu71_direct_scanout_pipe scanout(','    cu71_direct_scanout scanout(');assert normalized==base.read_text(),'Other topwiring changed'
bm=json.loads((d/'grouped-v001/sources.json').read_text());pm=json.loads((p/'sources.json').read_text());omit={'cu71_system_direct.sv','cu71_system_direct_pipe.sv','cu71_direct_scanout.sv','cu71_direct_scanout_pipe.sv'};bs={Path(n).name:sha(r/n)for n in bm['sources']if Path(n).name not in omit};ps={Path(n).name:sha(r/n)for n in pm['sources']if Path(n).name not in omit};assert bs==ps,'Nonowner hardware changed'
contract=r/'fpga/experiments/cu66-v71/direct-display/frozen-port-contract-pipe-v002.json';ct=json.loads(contract.read_text());display=contract.parent
for n,h in ct['sources'].items():assert sha(display/n)==h,n
for f in [p/'sources.json',p/'derivation.json',d/'grouped-v001/qualification-components-v001.json',contract,Path(__file__).resolve()]:proofs[f.relative_to(r).as_posix()]=sha(f)
out.write_text(json.dumps({'status':'PASS_NATIVE_PIPE_OWNER_WITH_GROUPED_BACKEND_THREE_FRAMES','only_behavioral_rebinding':'BASEdirectscanout→PIPEdirectscanout;topalpha-cloneonly','profile_magic':'0x44593731','profile_abi':'0x00010000','capabilities':'0x0f','rows':rows,'proofs':proofs,'cycle_deltas':[b['cycles']-a['cycles']for a,b in zip(rows['base_owner']['frames'],rows['pipe_owner']['frames'])],'hardware':False,'routed_timing':False,'CDC_qualified':False,'steady_30fps_proven':False,'scope':'Samegroupedbridge/controller/map/codec,realpinmodel,nativeHUDCPUoutsideHDLtime;all3generationscleanraster,lostCOMMITACKreconciled. PositiveleafPIPEsetupdoesnotqualifyfullboardsetup/hold/CDC.','limits':['OnlyKEYandtwoPtransactions','32bitDMAcookiefailsclosedbeforewrap;longdurationpolicyunqualified','Timerexpiryregistersincludecontrollerbusy;realreservedidlequalifiedseparately']},indent=2)+'\n');print(json.dumps({'qualification':str(out),'sha256':sha(out),'cycle_deltas':json.loads(out.read_text())['cycle_deltas']}))
