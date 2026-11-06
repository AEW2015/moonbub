"""Explicit cycle-preserving math binding into isolated PIPE/grouped DY71."""
from pathlib import Path
import hashlib,json,re
r=Path(__file__).resolve().parents[4];d=r/'fpga/experiments/cu66-v71/direct-system/board-math-v001';d.mkdir(parents=True,exist_ok=False);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();parent=r/'fpga/experiments/cu66-v71/direct-system/pipe-v001';math=r/'fpga/experiments/cu66-v71/codec/math-v004';m=json.loads((parent/'sources.json').read_text());mm=json.loads((math/'sources.json').read_text())
for spec in [m,mm]:
 for n,h in spec['sources_sha256'].items():assert sha(r/n)==h,n
proofpaths=['fpga/experiments/cu66-v71/hash/evidence/banks2-02/result.json','fpga/experiments/cu66-v71/inverse-index/evidence/regression01/result.json','fpga/experiments/cu66-v71/inverse-reset/evidence/regression01/result.json']
for n in proofpaths:assert json.loads((r/n).read_text())['status'].startswith('PASS'),n
receiver=r/'fpga/experiments/cu66-v71/direct-system/cu71_receiver_direct.sv';newreceiver=d/'cu71_receiver_direct_math.sv';s=receiver.read_text();assert s.count('module cu71_receiver_direct #(')==1 and s.count('cu71_base_pipeline_timing base(')==1
s=s.replace('module cu71_receiver_direct #(','module cu71_receiver_direct_math #(').replace('cu71_base_pipeline_timing base(','cu71_base_pipeline_math base(');newreceiver.write_text(s,newline='\n')
top=parent/'cu71_system_direct_pipe.sv';newtop=d/'cu71_system_direct_math.sv';s=top.read_text();assert s.count('module cu71_system_direct_pipe #(')==1 and s.count('    cu71_receiver_direct #(')==1
s=s.replace('module cu71_system_direct_pipe #(','module cu71_system_direct_math #(').replace('    cu71_receiver_direct #(','    cu71_receiver_direct_math #(');newtop.write_text(s,newline='\n')
swap={
 'cu71_system_direct_pipe.sv':newtop,
 'cu71_receiver_direct.sv':newreceiver,
 'cu71_base_pipeline_timing.sv':math/'cu71_base_pipeline_math.sv',
 'cu71_rows_sha256_bram.sv':math/'cu71_rows_sha256_fast.sv',
 'cu66_sha256_bytes.sv':r/'fpga/experiments/cu66-v71/hash/cu71_sha256_bytes_lookahead.sv',
 'cu71_dequant_pipe.sv':r/'fpga/experiments/cu66-v71/inverse-reset/cu71_dequant_resetlight.sv',
 'cu66_idct8x8.sv':r/'fpga/experiments/cu66-v71/inverse-index/cu71_idct_indexed.sv',
 'cu66_reconstruct_tile.sv':r/'fpga/experiments/cu66-v71/inverse-reset/cu71_reconstruct_resetlight.sv'}
bindings=[];sources=[]
for n in m['sources']:
 f=swap.get(Path(n).name,r/n);sources.append(f.relative_to(r).as_posix())
 if f!=r/n:bindings.append({'parent':n,'parent_sha256':sha(r/n),'candidate':f.relative_to(r).as_posix(),'candidate_sha256':sha(f)})
for n in swap:assert any(Path(b['parent']).name==n for b in bindings),n
m.update(top='cu71_system_direct_math',sources=sources,sources_sha256={n:sha(r/n)for n in sources},scope='Explicitqualifiedcycle-preservinghash/indexedIDCT/resetlightmathintoDY71PIPE/grouped; noPHY/map/policychange; fullintegrationpending')
(d/'sources.json').write_text(json.dumps(m,indent=2)+'\n')
(d/'derivation.json').write_text(json.dumps({'parent_manifest':(parent/'sources.json').relative_to(r).as_posix(),'parent_manifest_sha256':sha(parent/'sources.json'),'math_reference_manifest':(math/'sources.json').relative_to(r).as_posix(),'math_reference_manifest_sha256':sha(math/'sources.json'),'bindings':bindings,'component_proofs':{n:sha(r/n)for n in proofpaths},'expected_added_public_latency_cycles':0,'owner_commit_lease_HUD_changes':False,'memory_address_map_PHY_policy_changes':False,'hardware':False},indent=2)+'\n');print('PREPARED_DY71_BOARD_MATH',sha(d/'sources.json'))
