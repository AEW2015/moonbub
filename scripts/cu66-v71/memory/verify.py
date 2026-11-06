"""Bind final component results to current sources; no tools or hardware launched."""
from pathlib import Path
import hashlib,json,re
r=Path(__file__).resolve().parents[3];p=r/'fpga/experiments/cu66-v71/memory'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rtl=['cu71_memory_system.sv','cu71_word_bridge.sv','cu71_tile_memory.sv','moonshine_sdram_burst.sv']
assert sha(p/'moonshine_sdram_burst.sv')=='05a9a9471f9c9eb61209c55579b82f9d228cc01328044589eec989b200d6f65a'
rows=[]
for name in ['lookahead-fast01','lookahead-slow01']:
 d=p/'evidence'/name;m=json.loads((d/'result.json').read_text());freeze=json.loads((d/'source-freeze.json').read_text())
 assert m['status']=='PASS_COMPONENT_CANONICAL_AUX_LCD_QUALIFIED_CONTROLLER' and not m['SIMULATION_define']
 for n,h in freeze.items():assert sha(d/n)==h,n
 for n in rtl:assert sha(p/n)==freeze[n],n
 execution=json.loads((d/'execution.json').read_text());assert all(x['returncode']==0 for x in execution)
 log=(d/'simulation.log').read_text();match=re.search(r'CU71_MEMORY_PASS seed=(\d+) checks=(\d+) tiles=(\d+) aux=(\d+) aborts=(\d+) cycles=(\d+)',log)
 assert match and int(match[2])==4543 and int(match[5])==34
 rows.append({'path':str(d.relative_to(r)),'metrics':dict(zip(['seed','checks','tiles','aux','aborts','cycles'],map(int,match.groups()))),'result_sha256':sha(d/'result.json'),'source_freeze_sha256':sha(d/'source-freeze.json'),'simulation_log_sha256':sha(d/'simulation.log')})
sources={str((p/n).relative_to(r)):sha(p/n)for n in rtl}
for f in (r/'scripts/cu66-v71/memory').glob('*.py'):sources[f.relative_to(r).as_posix()]=sha(f)
for f in (p/'verification').glob('*.sv'):sources[f.relative_to(r).as_posix()]=sha(f)
(p/'qualification.json').write_text(json.dumps({'status':'PASS_QUALIFIED_CONTROLLER_COMPONENT_FUNCTIONAL_ONLY','sources':sources,'runs':rows,'hardware':False,'routed_timing':False,'line_deadline':'NOT_QUALIFIED; componentstressincludesexplicitresponseholds; actualprefetchintegrationseparate','scope':'Allbanks/guards/masks/readback/responseisolation andall8beatabortpositions. Doesnotqualifytargetfit/reset/PVT/30fps.'},indent=2)+'\n')
print('PASS_QUALIFIED_CONTROLLER_COMPONENT_FUNCTIONAL_ONLY')
