"""Derive an isolated RGB1 bank2 map with the frozen v70 generator checks."""
from pathlib import Path
import argparse,contextlib,hashlib,io,json
p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args()
r=Path(__file__).resolve().parents[3];old=r/'fpga/experiments/cu66-v70/memory/generate_map.py';out=Path(a.output).resolve();out.mkdir(parents=True,exist_ok=False)
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
text=old.read_text();assert text.count('(0x1800000,0x1900000)')==1
text=text.replace('(0x1800000,0x1900000)', '(0x1800000,0x1300000)')
assert text.count('H=Path(__file__).resolve().parent')==1
text=text.replace('H=Path(__file__).resolve().parent', 'H=Path('+repr(str(out))+')')
text=text.replace("schema='cu70-memory-map-v1'", "schema='cu71-memory-map-crossbank-v1'")
(out/'executed-generator.py').write_text(text,newline='\n')
log=io.StringIO()
with contextlib.redirect_stdout(log):exec(compile(text,str(out/'executed-generator.py'),'exec'),{'__file__':str(out/'executed-generator.py')})
(out/'generation.log').write_text(log.getvalue())
data=json.loads((out/'memory-map.json').read_text());rgb1=next(x for x in data['regions']if x['name']=='rgb1');assert rgb1['word_base']==0x980000
regions=data['regions']
for x in regions:
 assert x['word_base']%8==0 and x['word_count']%8==0
 assert x['word_base']+x['word_count']<=16777216
for x in regions:
 for y in regions:
  if x is not y:assert x['byte_base']+x['byte_size']<=y['byte_base']-32 or y['byte_base']+y['byte_size']<=x['byte_base']-32
(out/'derivation.json').write_text(json.dumps({'status':'PASS_GENERATED_GUARDS_CAPACITY_ALIGNMENT','parent_generator':str(old),'parent_sha256':sha(old),'executed_generator_sha256':sha(out/'executed-generator.py'),'artifacts':{n:sha(out/n)for n in ['cu70_memory_map.svh','memory_map.hpp','memory-map.json','generation.log']},'RGB0_physical_bank':3,'RGB1_physical_bank':2,'RGB1_word_base':'0x980000','tradeoff':'RGB1nowsharesphysicalbank2withcanonical2/HUD2; controlledA/Brequiredforeachactivebankworkload. Notuniversalfix.','hardware':False},indent=2)+'\n')
print('PASS_GENERATED_GUARDS_CAPACITY_ALIGNMENT',out)
