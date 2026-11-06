from pathlib import Path
import hashlib,json
r=Path(__file__).resolve().parents[4];d=r/'fpga/experiments/cu66-v71/direct-system/event-retime-v001';p=r/'fpga/experiments/cu66-v71/direct-system/syncsafe-math-v002';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();m=json.loads((p/'sources.json').read_text())
for n,h in m['sources_sha256'].items():assert sha(r/n)==h,n
s=(p/'cu71_system_direct_syncsafe.sv').read_text();t=s.replace('module cu71_system_direct_syncsafe #(','module cu71_system_eventpipe #(').replace('cu71_receiver_direct_math #(','cu71_receiver_eventpipe #(')
assert t.replace('module cu71_system_eventpipe #(','module cu71_system_direct_syncsafe #(').replace('cu71_receiver_eventpipe #(','cu71_receiver_direct_math #(')==s
out=d/'cu71_system_eventpipe.sv';assert not out.exists();out.write_text(t,newline='\n')
swap={'cu71_system_direct_syncsafe.sv':out,'cu71_receiver_direct_math.sv':d/'cu71_receiver_eventpipe.sv'};sources=[swap.get(Path(n).name,r/n).relative_to(r).as_posix()for n in m['sources']]
m.update(top='cu71_system_eventpipe',sources=sources,sources_sha256={n:sha(r/n)for n in sources},scope='Eventringphysicalretimeonly; unchangedoriginalowner/producer/codec/SYNCsafe/PHY/map/quota/clocks')
(d/'sources.json').write_text(json.dumps(m,indent=2)+'\n');print(sha(d/'sources.json'))
