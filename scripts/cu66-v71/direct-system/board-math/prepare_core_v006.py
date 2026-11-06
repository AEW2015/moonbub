"""Explicit new combined codec/parser binding; exact reversible token changes."""
from pathlib import Path
import hashlib,json,re
r=Path(__file__).resolve().parents[4];d=r/'fpga/experiments/cu66-v71/direct-system/core-integration-v006';base=r/'fpga/experiments/cu66-v71/direct-system/syncsafe-math-v002/sources.json';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(base)=='8451653672247a3bad012c3bb90b0d76fdee4802768b5964d6a0a0bf61783b9f'
m=json.loads(base.read_text())
for n,h in m['sources_sha256'].items():assert sha(r/n)==h,n
chosen={
 'base':('fpga/experiments/cu66-v71/direct-system/tag-phase-cut-v003/cu71_base_pipeline_math.sv','4159cb208180f94245ed451118aa034e84ba0895f040562aa4df114a8f47f55d'),
 'dequant':('fpga/experiments/cu66-v71/dequant-validpipe/cu71_dequant_validpipe.sv','a5caee1e60e24b5b2b8927344b751272a587b20dfaaa1d62c7c17bdd9729e612'),
 'entropy':('fpga/experiments/cu66-v71/entropy-dcpipe/cu71_ab38_decoder_dcpipe_v6.sv','cb8573f9f467305dd66754d82005dd23df01bbf505a7623cc78f198765f1b777'),
 'parser':('fpga/experiments/cu66-v71/packet-prefix-v003/cu71_packet_hudsum.sv','aae2623f41459b064b99f05404b0796c84dae5ab7871c2d4a7bddb5c8b10f3c3'),
 'idct':('fpga/experiments/cu66-v71/inverse-validpipe/cu71_idct_validpipe.sv','817c1b60b26c022c112c0a048418cd4867905210f1e91cc47afe1eb4ee49dba1')}
for n,(path,h)in chosen.items():assert sha(r/path)==h,(n,path)
def ports(p):
 s=p.read_text();s=s[s.index('module '):s.index(');')+2];s=re.sub(r'\bmodule\s+\w+','module __same',s);return re.sub(r'\s+','',s)
for old,new in [('fpga/experiments/cu66-v71/inverse-reset/cu71_dequant_resetlight.sv','dequant'),('fpga/experiments/cu66-v71/entropy/cu71_ab38_decoder_arithpipe_v4.sv','entropy'),('fpga/experiments/cu66-v69/packet/cu66_packet_control.sv','parser')]:assert ports(r/old)==ports(r/chosen[new][0]),('PORT_MISMATCH',old,new)
records=[]
def derive(parent,name,swaps):
 s=(r/parent).read_text();t=s
 for old,new in swaps:assert t.count(old)==1,(name,old,t.count(old));t=t.replace(old,new)
 back=t
 for old,new in reversed(swaps):assert back.count(new)==1;back=back.replace(new,old)
 assert back==s,name
 p=d/name;assert not p.exists(),p;p.write_text(t,newline='\n');records.append(dict(parent=parent,parent_sha256=sha(r/parent),output=str(p.relative_to(r)).replace('\\','/'),sha256=sha(p),token_changes=swaps,reversal_exact=True));return p
bp=derive(chosen['base'][0],'cu71_base_core_v006.sv',[('module cu71_base_pipeline_math (','module cu71_base_core_v006 ('),('cu71_dequant_resetlight dequant(','cu71_dequant_validpipe dequant('),('cu71_ab38_decoder_arithpipe_v4 entropy(','cu71_ab38_decoder_dcpipe_v6 entropy(')])
rp=derive('fpga/experiments/cu66-v71/direct-system/board-math-v001/cu71_receiver_direct_math.sv','cu71_receiver_core_v006.sv',[('module cu71_receiver_direct_math #(','module cu71_receiver_core_v006 #('),('cu66_packet_control parser(','cu71_packet_hudsum parser('),('cu71_base_pipeline_math base(','cu71_base_core_v006 base(')])
sp=derive('fpga/experiments/cu66-v71/direct-system/syncsafe-math-v002/cu71_system_direct_syncsafe.sv','cu71_system_core_v006.sv',[('module cu71_system_direct_syncsafe #(','module cu71_system_core_v006 #('),('cu71_receiver_direct_math #(','cu71_receiver_core_v006 #(')])
swap={'cu71_system_direct_syncsafe.sv':sp,'cu71_receiver_direct_math.sv':rp,'cu71_base_pipeline_math.sv':bp,'cu71_dequant_resetlight.sv':r/chosen['dequant'][0],'cu71_ab38_decoder_arithpipe_v4.sv':r/chosen['entropy'][0],'cu66_packet_control.sv':r/chosen['parser'][0],'cu71_idct_indexed.sv':r/chosen['idct'][0]}
sources=[str(swap.get(Path(n).name,r/n).relative_to(r)).replace('\\','/')for n in m['sources']]
assert len(set(sources))==len(m['sources'])==23
m.update(top='cu71_system_core_v006',sources=sources,sources_sha256={n:sha(r/n)for n in sources},scope='Explicit isolatedcombinedtagphasecut+IDCTvalidpipe+DQvalidpipe+entropyDCv6+parserHUDsumv3; unchangedownerlogic/SYNCsafe/groupedPHY/map/clocks; nohardwarequalification')
(d/'sources.json').write_text(json.dumps(m,indent=2)+'\n')
(d/'derivation.json').write_text(json.dumps(dict(parent_manifest=str(base.relative_to(r)).replace('\\','/'),parent_manifest_sha256=sha(base),selected_sources=chosen,derived_files=records,ports_matched=True,golden_bytes_in_DUT=False,PHY_map_quota_clock_owner_logic_changed=False,whole_system_proof='PENDING',hardware=False),indent=2)+'\n')
print('PREPARED_CORE_V006',sha(d/'sources.json'))
