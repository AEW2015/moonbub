"""Bind frozen row-major address micro-pipeline without changing map/PHY/profile."""
from pathlib import Path
import hashlib,json,re

root=Path(__file__).resolve().parents[2]
out=root/'fpga/experiments/cu66-v71/codec/address-v003'
out.mkdir(parents=True,exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(root).as_posix()
tile=root/'fpga/experiments/cu66-v71/tile-address/cu71_tile_memory_address_pipe.sv'
assert sha(tile)=='fc88f5a4853665d41af22dbd68e4e30282bd3cdd138a5eb0cd03a2a43ec61e70'
parent=root/'fpga/experiments/cu66-v71/codec/resetlight-v002'
manifest=json.loads((parent/'sources.json').read_text())
for name,expected in manifest['sources_sha256'].items():assert sha(root/name)==expected,name
bindings=[];replacement={}
for source,target,modules in [
 (root/'fpga/experiments/cu66-v71/memory/cu71_memory_system_burst.sv',out/'cu71_memory_system_burst_address.sv',
  {'cu71_memory_system_burst':'cu71_memory_system_burst_address','cu71_tile_memory':'cu71_tile_memory_address_pipe'}),
 (parent/'cu71_system_resetlight.sv',out/'cu71_system_addresspipe.sv',
  {'cu71_system_resetlight':'cu71_system_addresspipe','cu71_memory_system_burst':'cu71_memory_system_burst_address'}),
]:
 text=source.read_text()
 for old,new in modules.items():
  assert len(re.findall(r'\b'+old+r'\b',text))==1,(source,old)
  text=re.sub(r'\b'+old+r'\b',new,text)
 target.write_text(text,newline='\n');replacement[rel(source)]=rel(target)
 bindings.append(dict(parent=rel(source),parent_sha256=sha(source),candidate=rel(target),candidate_sha256=sha(target),modules=modules))
replacement['fpga/experiments/cu66-v71/memory/cu71_tile_memory.sv']=rel(tile)
sources=[replacement.get(name,name)for name in manifest['sources']]
(out/'sources.json').write_text(json.dumps(dict(top='cu71_system_addresspipe',sources=sources,
 include_dirs=manifest['include_dirs'],sources_sha256={name:sha(root/name)for name in sources},SIMULATION=False,
 scope='Captured/bounded row-major tile addresses vs resetlight-v002; old-map/PHY/CSR/codec unchanged; integration/routed gates pending'),indent=2)+'\n')
(out/'derivation.json').write_text(json.dumps(dict(status='STRUCTURAL_ADDRESS_PIPE_INTEGRATION_PENDING',bindings=bindings,
 tile_source_sha256=sha(tile),parent_manifest_sha256=sha(parent/'sources.json'),
 address_latency='Adds ten setup clocks for valid tile operations; invalid fast result/drain contract retained',
 hardware=False,BIT=False),indent=2)+'\n')
print(out)
