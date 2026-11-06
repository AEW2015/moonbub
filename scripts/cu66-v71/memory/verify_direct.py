"""Source-bound four-full-BL8 tile-major component evidence, no board access."""
from pathlib import Path
import hashlib,json,re
r=Path(__file__).resolve().parents[3];p=r/'fpga/experiments/cu66-v71/memory';sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();parse=lambda s:{k:int(v)for k,v in re.findall(r'(\w+)=(\d+)',s)}
rtl=['cu71_memory_system_direct.sv','cu71_word_bridge_direct.sv','cu71_tile_memory_direct.sv','moonshine_sdram_burst.sv'];rows=[]
assert sha(p/'moonshine_sdram_burst.sv')=='05a9a9471f9c9eb61209c55579b82f9d228cc01328044589eec989b200d6f65a'
for name in ['direct-reference-fast01','direct-reference-slow01','direct-reference-crossbank-fast01','direct-reference-crossbank-slow01']:
 d=p/'evidence'/name;m=json.loads((d/'result.json').read_text());freeze=json.loads((d/'source-freeze.json').read_text())
 assert m['status']=='PASS_TILE_MAJOR_FOUR_FULL_BL8_CANONICAL_MEMORY_COMPONENT'
 for n,h in freeze.items():assert sha(d/n)==h,n
 for n in rtl:assert sha(p/n)==freeze[n],n
 assert all(x['returncode']==0 for x in json.loads((d/'execution.json').read_text()))
 log=(d/'simulation.log').read_text();assert 'FATAL'not in log
 assert 'CU71_DIRECT_TILE_COMMAND_PASS full_read_BL8=4 full_write_BL8=4 physical_words=32 logical_bytes=64 masked_write_bytes=0'in log
 assert 'CU71_DIRECT_ABORT_ALL_PASS write_positions=32 read_positions=32'in log
 metrics=parse(next(x for x in log.splitlines()if x.startswith('CU71_DIRECT_MEMORY_PASS')));ref=parse(next(x for x in log.splitlines()if x.startswith('CU71_DIRECT_REFERENCE_CONTENDED')))
 assert metrics['checks']==5346 and metrics['aborts']==94 and ref['tiles']==4 and ref['actual_BL8_reads']==16
 rows.append({'path':str(d.relative_to(r)),'slow':m['slow'],'map':'crossbank'if'crossbank'in name else'original','metrics':metrics,'reference':ref,'bindings':{n:sha(d/n)for n in ['result.json','execution.json','source-freeze.json','simulation.log']}})
(p/'direct-qualification.json').write_text(json.dumps({'status':'PASS_TILE_MAJOR_CANONICAL_FOUR_FULL_BL8_COMPONENT_ONLY','rtl':{n:sha(p/n)for n in rtl},'derivation_sha256':sha(p/'direct-derivation.json'),'runs':rows,'hardware':False,'routed_timing':False,'scope':'Unchangedlogical512pixel+identityAPI;actual4fullread/writeburstsper64Btile;allplanes/banks/mapedges/guards,32read+32writeacceptedbeataborts,concurrentaux/LCD128ownership. Notdecoder/directdisplay/30fpsqualification.'},indent=2)+'\n');print('PASS_TILE_MAJOR_CANONICAL_FOUR_FULL_BL8_COMPONENT_ONLY')
