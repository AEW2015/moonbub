"""Explicit new SYNCsafe binding; preserve board-math-v001 unchanged."""
from pathlib import Path
import hashlib,json
r=Path(__file__).resolve().parents[4];root=r/'fpga/experiments/cu66-v71/direct-system';parent=root/'board-math-v001';d=root/'syncsafe-math-v002';d.mkdir(exist_ok=False);cdc=r/'fpga/experiments/cu66-v71/direct-display/cdc';sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();handoff=cdc/'handoff02/manifest.json';h=json.loads(handoff.read_text())
assert h['component_status']=='PASS_PROTOCOL_NATIVE_PIXELS_AND_TARGETED_CDC_LEAF_GATES'and h['selected_candidate']=='cu71_direct_scanout_syncsafe'
for a in h['artifacts']:assert sha(r/a['path'])==a['sha256'],a['path']
for name in ['cu71_direct_scanout_syncsafe.sv','cu71_lcd_lines_syncsafe.sv']:assert sha(cdc/name)==h['source_sha256'][name],name
fanout=cdc/'syncsafe-ooc02/first-stage-fanout.txt';lines=fanout.read_text().splitlines();assert len(lines)==6
for chain in ['request_sync0','request_sync1','frame_sync','done_sync0','done_sync1','valid_sync']:assert 'lcd/'+chain+'_reg[0] ENDPOINTS lcd/'+chain+'_reg[1]/D'in lines,chain
oldtop=parent/'cu71_system_direct_math.sv';top=d/'cu71_system_direct_syncsafe.sv';s=oldtop.read_text();assert s.count('module cu71_system_direct_math #(')==1 and s.count('    cu71_direct_scanout_pipe scanout(')==1;s=s.replace('module cu71_system_direct_math #(','module cu71_system_direct_syncsafe #(').replace('    cu71_direct_scanout_pipe scanout(','    cu71_direct_scanout_syncsafe scanout(');top.write_text(s,newline='\n')
m=json.loads((parent/'sources.json').read_text())
for n,v in m['sources_sha256'].items():assert sha(r/n)==v,n
swap={'cu71_system_direct_math.sv':top,'cu71_direct_scanout_pipe.sv':cdc/'cu71_direct_scanout_syncsafe.sv','cu71_lcd_lines_direct.sv':cdc/'cu71_lcd_lines_syncsafe.sv'}
sources=[swap.get(Path(n).name,r/n).relative_to(r).as_posix()for n in m['sources']];m.update(top='cu71_system_direct_syncsafe',sources=sources,sources_sha256={n:sha(r/n)for n in sources},scope='ExplicitSYNCsafeendpoint+PIPE/group/math; fixed4memclockframequalification and2quietidle; wholeintegrationpending, nohardwarequalification');(d/'sources.json').write_text(json.dumps(m,indent=2)+'\n')
(d/'derivation.json').write_text(json.dumps({'parent_manifest_sha256':sha(parent/'sources.json'),'parent_top_sha256':sha(oldtop),'candidate_top_sha256':sha(top),'handoff02_manifest_sha256':sha(handoff),'stage0_fanout_proof_sha256':sha(fanout),'selected_sources':{n:sha(f)for n,f in swap.items()},'expected_change':'4memoryclockqualifiedframewindow,2quietmemoryclocksinidle; skipbusyframepulse ratherthandefer','ports_panel_clocks_changed':False,'math_CSR_group_PHY_map_changes':False,'native_whole_system_gate':'Pending','hardware':False},indent=2)+'\n');print('PREPARED_SYNCsafe',sha(d/'sources.json'))
