"""Review-only qualification of independent private-cache hit responses."""
from pathlib import Path
import hashlib,json,re
r=Path(__file__).resolve().parents[3];p=r/'fpga/experiments/cu66-v71/memory';sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
rtl=['cu71_memory_system_burst_cache.sv','cu71_word_bridge_burst_cache.sv','cu71_tile_memory.sv','moonshine_sdram_burst.sv'];parse=lambda s:{k:int(v)for k,v in re.findall(r'(\w+)=(\d+)',s)}
rows=[]
for name in ['cache-alias-fast01','cache-alias-slow01','cache-alias-crossbank-fast01','cache-alias-crossbank-slow01']:
 d=p/'evidence'/name;m=json.loads((d/'result.json').read_text());freeze=json.loads((d/'source-freeze.json').read_text())
 assert m['status']=='PASS_EXPLICIT_RGB_BL8_ACTUAL_DRAIN_MASKS_ABORT_ISOLATION'
 for n,h in freeze.items():assert sha(d/n)==h,n
 for n in rtl:assert sha(p/n)==freeze[n],n
 assert all(x['returncode']==0 for x in json.loads((d/'execution.json').read_text()))
 log=(d/'simulation.log').read_text();assert 'CU71_CACHE_ACTIVE_ALIAS_PASS RGBaux=1 AUXcanonical=1 accepted_prime_abort=1'in log and 'FATAL'not in log
 metrics=parse(next(x for x in log.splitlines()if x.startswith('CU71_MEMORY_RGB_BURST_PASS')));ref=parse(next(x for x in log.splitlines()if x.startswith('CU71_CONTENDED_REFERENCE_READ')))
 assert metrics['checks']==5175 and metrics['aborts']==43 and ref['actual_BL8_reads']==32 and ref['private_cache_hits']==96
 rows.append({'path':str(d.relative_to(r)),'map':'crossbank'if'crossbank'in name else'original','slow':m['slow'],'metrics':metrics,'reference':ref,'bindings':{n:sha(d/n)for n in ['source-freeze.json','execution.json','simulation.log','result.json']}})
(p/'cache-qualification.json').write_text(json.dumps({'status':'PASS_PRIVATE_CACHE_HIT_ISOLATION_AND_ACTIVE_ALIAS_COMPONENT_ONLY','rtl':{n:sha(p/n)for n in rtl},'runs':rows,'derivation_sha256':sha(p/'cache-derivation.json'),'hardware':False,'routed_timing':False,'not_selected_automatically':True,'scope':'Fourclients/masks/guards/all8beataborts/readbacksplusactiveRGB-to-auxandaux-to-canonicalcachealiaschecks. NoFmaxorwholeframe30fpsqualification.'},indent=2)+'\n');print('PASS_PRIVATE_CACHE_HIT_ISOLATION_AND_ACTIVE_ALIAS_COMPONENT_ONLY')
