"""Bind grouped scheduler component gates; performance remains a separate gate."""
from pathlib import Path
import hashlib,json,re
r=Path(__file__).resolve().parents[3];d=r/'fpga/experiments/cu66-v71/direct-system/grouped-v001';o=d/'qualification-components-v001.json';assert not o.exists();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();proofs={};rows={}
for name in ['component-fast01','component-slow01']:
 p=d/'evidence'/name;res=json.loads((p/'result.json').read_text());assert res['status']=='PASS_GROUPED_ACTUAL_CONTROLLER_COMPONENT_AND_ABORTS'
 for n,h in json.loads((p/'source-freeze.json').read_text()).items():assert sha(p/n)==h,(name,n)
 assert sha(p/'cu71_word_bridge_direct.sv')==sha(d/'source/cu71_word_bridge_direct.sv')
 text=(p/'simulation.log').read_text();rows[name]=[x for x in text.splitlines()if x.startswith('CU71_GROUPED_ACCOUNTING_PASS')or x.startswith('CU71_DIRECT_MEMORY_PASS')]
 assert 'aborts=94' in text and 'write_positions=32 read_positions=32' in text
 for f in [p/'result.json',p/'source-freeze.json',p/'simulation.log',p/'execution.json']:proofs[f.relative_to(r).as_posix()]=sha(f)
p=d/'evidence/fairness01';res=json.loads((p/'result.json').read_text());assert res['status']=='PASS_GROUPED_CONTINUOUS_QUOTA_LOCALS_AND_RESPONSE_ISOLATION'
for n,h in res['source_pins'].items():assert sha(r/n)==h,n
text=(p/'executed.log').read_text();assert 'GROUPED_FAIRNESS_PASS checks=24157' in text
rows['fairness']=[x for x in text.splitlines()if x.startswith('GROUPED_FAIRNESS')]
for f in [p/'result.json',p/'execution.json',p/'executed.log',d/'derivation.json',Path(__file__).resolve()]:proofs[f.relative_to(r).as_posix()]=sha(f)
baseline=r/'fpga/experiments/cu66-v71/memory/evidence/direct-fast01'
for n in ['cu71_memory_system_direct.sv','cu71_tile_memory_direct.sv','moonshine_sdram_burst.sv','cu70_memory_map.svh','model.sv','primitives.sv']:assert sha(d/'source'/n)==sha(baseline/n),n
o.write_text(json.dumps({'status':'PASS_COMPONENT_FUNCTIONAL_ABORT_FAIRNESS_AND_RESPONSE_ISOLATION','bridge_sha256':sha(d/'source/cu71_word_bridge_direct.sv'),'nominal_contended_physical_command_ratio':'8LCD:4BG (2:1)','grace_cycles':{'LCD':18,'BG':4},'quota_accounting':'Onlyacceptedcontrollercommands;localcachehits/errorsuncharged,notgraceextensions','work_conservation':'Absent/held/cancelledclientreservationexpiresboundedly;observedratio maydifferwhenoneclassunavailable','unchanged':['PHY/controller/map','tileadapter','memorywrapper','codec/baseowner'],'results':rows,'proofs':proofs,'hardware':False,'routed_timing':False,'matched_performance_gate':'Pending;notuniversallatencyimprovement','full_system_gate':'Pending'},indent=2)+'\n');print(json.dumps({'qualification':str(o),'sha256':sha(o)}))
