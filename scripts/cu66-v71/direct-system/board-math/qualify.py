"""Bind exact native math-vs-PIPE/group cycle equality without timing claims."""
from pathlib import Path
import hashlib,json,re
r=Path(__file__).resolve().parents[4];d=r/'fpga/experiments/cu66-v71/direct-system/board-math-v001';run=d/'evidence/math-group-three01';parent=r/'fpga/experiments/cu66-v71/direct-system/pipe-v001';old=parent/'evidence/pipe-group-three-timeline01';o=d/'qualification-native-v001.json';assert not o.exists();sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
assert json.loads((run/'result.json').read_text())['frames']==3
for n,h in json.loads((run/'source-freeze.json').read_text()).items():assert sha(r/n)==h,n
assert(run/'frames.log').read_bytes()==(old/'frames.log').read_bytes(),'Math changed public native cycle/count/timeline'
assert(run/'control.log').read_bytes()==(old/'control.log').read_bytes(),'Bounded control behavior changed'
newtop=(d/'cu71_system_direct_math.sv').read_text().replace('module cu71_system_direct_math #(','module cu71_system_direct_pipe #(').replace('    cu71_receiver_direct_math #(','    cu71_receiver_direct #(');assert newtop==(parent/'cu71_system_direct_pipe.sv').read_text()
oldrx=r/'fpga/experiments/cu66-v71/direct-system/cu71_receiver_direct.sv';newrx=(d/'cu71_receiver_direct_math.sv').read_text().replace('module cu71_receiver_direct_math #(','module cu71_receiver_direct #(').replace('cu71_base_pipeline_math base(','cu71_base_pipeline_timing base(');assert newrx==oldrx.read_text()
m=json.loads((d/'sources.json').read_text());expected={'cu71_sha256_bytes_lookahead.sv':'f29332de9fe41ba679bef91fba71698e4efb4a05860221ab0ea3268e19c28006','cu71_idct_indexed.sv':'fe1d7f3684ac7e8c15bc80e5a9b4734863103510faa2087d75b00a6b94d2d41d','cu71_dequant_resetlight.sv':'e2abdd9ecfe74612ed1f4f495be5d760454aa7431d9c23e19fe919d02d8a891a'}
for name,h in expected.items():f=next(r/n for n in m['sources']if Path(n).name==name);assert sha(f)==h,name
text=(run/'frames.log').read_text();vals=lambda x:{k:int(v)for k,v in re.findall(r'(\w+)=(\d+)',x)};frames=[vals(x)for x in text.splitlines()if x.startswith('SYSTEM_FRAME_PASS')];summary=vals(next(x for x in text.splitlines()if x.startswith('SYSTEM_PASS')));assert summary['total_underruns']==0 and summary['black_lines']==0
proofs={}
for f in [d/'sources.json',d/'derivation.json',run/'result.json',run/'source-freeze.json',run/'execution.json',run/'frames.log',run/'control.log',run/'tb.cpp',run/'cu71_direct_system_sim.sv',old/'frames.log',parent/'qualification-three-v001.json',Path(__file__).resolve()]:proofs[f.relative_to(r).as_posix()]=sha(f)
for n in json.loads((d/'derivation.json').read_text())['component_proofs']:proofs[n]=sha(r/n)
o.write_text(json.dumps({'status':'PASS_DY71_MATH_BINDING_EXACT_NATIVE_THREE_FRAME_CYCLES','frames':frames,'summary':summary,'frames_log_sha256':sha(run/'frames.log'),'byte_identical_parent_timeline':True,'control_log_identical':True,'added_public_latency_cycles':0,'owner_COMMIT_lease_HUD_changes':False,'PHY_map_scheduler_policy_changes':False,'proofs':proofs,'hardware':False,'routed_timing':False,'CDC_qualified':False,'steady_30fps_proven':False,'physical_shell_gate':'CurrentlegacyLCDrequests_idlefunctionallyusesfirststages;SYNCsafeendpointbindingrequiredbeforeshellselection. Noexceptionsmayhideit.'},indent=2)+'\n');print(json.dumps({'qualification':str(o),'sha256':sha(o),'cycles':[f['cycles']for f in frames]}))
