"""Bind RGB burst/mask/drain/reference evidence to both map variants."""
from pathlib import Path
import hashlib,json,re
r=Path(__file__).resolve().parents[3];p=r/'fpga/experiments/cu66-v71/memory';sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
rtl=['cu71_memory_system_burst.sv','cu71_word_bridge_burst.sv','cu71_tile_memory.sv','moonshine_sdram_burst.sv']
assert sha(p/'moonshine_sdram_burst.sv')=='05a9a9471f9c9eb61209c55579b82f9d228cc01328044589eec989b200d6f65a'
parse=lambda s:{k:int(v)for k,v in re.findall(r'(\w+)=(\d+)',s)}
rows=[]
for name in ['rgb-reference-fast01','rgb-reference-slow01','rgb-reference-crossbank-fast01','rgb-reference-crossbank-slow01']:
 d=p/'evidence'/name;result=json.loads((d/'result.json').read_text());freeze=json.loads((d/'source-freeze.json').read_text())
 assert result['status']=='PASS_EXPLICIT_RGB_BL8_ACTUAL_DRAIN_MASKS_ABORT_ISOLATION'
 for n,h in freeze.items():assert sha(d/n)==h,n
 for n in rtl:assert sha(p/n)==freeze[n],n
 selected=p/'maps/crossbank-v001/cu70_memory_map.svh'if'crossbank'in name else r/'fpga/experiments/cu66-v70/memory/cu70_memory_map.svh'
 assert sha(d/'cu70_memory_map.svh')==sha(selected)
 executions=json.loads((d/'execution.json').read_text());assert all(x['returncode']==0 for x in executions)
 log=(d/'simulation.log').read_text();assert 'FATAL'not in log
 metrics=parse(next(x for x in log.splitlines()if x.startswith('CU71_MEMORY_RGB_BURST_PASS')))
 rgb=parse(next(x for x in log.splitlines()if x.startswith('CU71_RGB_BURST_COVERAGE')))
 ref=parse(next(x for x in log.splitlines()if x.startswith('CU71_CONTENDED_REFERENCE_READ')))
 assert metrics['checks']==5168 and metrics['aborts']==42 and rgb['rgb_operations']==52
 assert ref['tiles']==4 and ref['actual_BL8_reads']==32 and ref['private_cache_hits']==96
 rows.append({'path':str(d.relative_to(r)),'map':'crossbank'if'crossbank'in name else'original','slow':result['slow'],'metrics':metrics,'RGB':rgb,'reference':ref,'bindings':{n:sha(d/n)for n in ['result.json','source-freeze.json','execution.json','simulation.log']}})
(p/'burst-qualification.json').write_text(json.dumps({'status':'PASS_RGB_BURST_AND_CONTENDED_REFERENCE_COMPONENT_ONLY','rtl':{n:sha(p/n)for n in rtl},'runs':rows,'map_derivation_sha256':sha(p/'maps/crossbank-v001/derivation.json'),'hardware':False,'routed_timing':False,'scope':'LogicalRGBdata/masks/cachecoherence/mapguards,actualrecoveryresponses,all8acceptedabortbeatpositions,4clientisolation,andcontendedreferencecachework. NotLCDCdeadlineorwholeframe30fps.'},indent=2)+'\n')
print('PASS_RGB_BURST_AND_CONTENDED_REFERENCE_COMPONENT_ONLY')
