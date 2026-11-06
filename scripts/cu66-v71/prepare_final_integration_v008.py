"""Compose frozen, reversible owner/event patches with the proven v006 core."""
from pathlib import Path
import hashlib,json,re
r=Path(__file__).resolve().parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(r).as_posix()
d=r/'fpga/experiments/cu66-v71/direct-system'
core_path=d/'core-integration-v006/sources.json'
assert sha(core_path)=='826c979a19ad460090636453c1fd2ba239df61ee55d61fe55569bd3ed96055c3'
core=json.loads(core_path.read_text())
for n,h in core['sources_sha256'].items():assert sha(r/n)==h,n
owner=r/'fpga/experiments/cu66-v71/owner-timing/meta-payload-v003/cu71_receiver_metapayload_v003.sv'
assert sha(owner)=='1b3be7c9779d4c5c61712c177173a235f1ddbb68737f7687059789325b510f32'
event=d/'event-retime-v001/patch.json';patch=json.loads(event.read_text())
assert patch['parent_sha256']=='7991bfc59ddf2942080185196b103e9af0b72b94857460f5570b92d035bd71d3'
event_source=d/'event-retime-v001/cu71_receiver_eventpipe.sv'
assert sha(event_source)=='54f31ee41412e0ed63a7658427320202f03640f5418f033c18a0a7f66ea12532'
out=d/'final-integration-v008';out.mkdir(exist_ok=False)
text=owner.read_text();before_events=text;event_swaps=patch['swaps'][1:]
for old,new in event_swaps:
 assert text.count(old)==1,('event compose anchor',old[:80])
 text=text.replace(old,new)
reverse=text
for old,new in reversed(event_swaps):
 assert reverse.count(new)==1;reverse=reverse.replace(new,old)
assert reverse==before_events,'Event patch changes owner metadata qualifier'
receiver_swaps=[('module cu71_receiver_metapayload_v003 #(','module cu71_receiver_final_v008 #('),
 ('cu66_packet_control parser(','cu71_packet_hudsum parser('),
 ('cu71_base_pipeline_math base(','cu71_base_core_v006 base(')]
for old,new in receiver_swaps:
 assert text.count(old)==1,(old,text.count(old));text=text.replace(old,new)
receiver=out/'cu71_receiver_final_v008.sv';receiver.write_text(text,newline='\n')
sys_parent=d/'core-integration-v006/cu71_system_core_v006.sv'
t=sys_parent.read_text();system_swaps=[('module cu71_system_core_v006 #(','module cu71_system_final_v008 #('),
 ('cu71_receiver_core_v006 #(','cu71_receiver_final_v008 #(')]
for old,new in system_swaps:
 assert t.count(old)==1,(old,t.count(old));t=t.replace(old,new)
system=out/'cu71_system_final_v008.sv';system.write_text(t,newline='\n')
replacements={rel(d/'core-integration-v006/cu71_receiver_core_v006.sv'):rel(receiver),rel(sys_parent):rel(system)}
s=dict(core);s['top']='cu71_system_final_v008'
s['sources']=[replacements.get(n,n)for n in core['sources']]
s['sources_sha256']={n:sha(r/n)for n in s['sources']}
s['parent_manifest_sha256']=sha(core_path)
s['scope']='Explicit combined core plus proved metadata guard and diagnostic physical-write retime. Whole final pairing/timing pending.'
(out/'sources.json').write_text(json.dumps(s,indent=2)+'\n')
derivation=dict(parent_core_manifest=rel(core_path),parent_core_manifest_sha256=sha(core_path),
 owner_source=rel(owner),owner_source_sha256=sha(owner),event_patch=rel(event),event_patch_sha256=sha(event),
 event_source_sha256=sha(event_source),event_swaps=event_swaps,event_reverse_exact=True,
 receiver_binding_swaps=receiver_swaps,system_binding_swaps=system_swaps,
 PHY_map_quota_clocks_SYNCsafe_unchanged=True,whole_combined_pending=True,hardware=False)
(out/'derivation.json').write_text(json.dumps(derivation,indent=2)+'\n')

bp=d/'syncsafe-math-v002/board-source-v005/selection.json';b=json.loads(bp.read_text())
assert sha(bp)=='84cc0f1e93f03f870207c68df2c33aac6a4a7a3cee8da87deab7900ec69daf76'
top_parent=r/'fpga/experiments/cu66-v71/transport-nonzero/samecycle-v001/moonshine_top_dy71.sv'
assert sha(top_parent)=='c530e2376ad3ac93d8fac31ac60ab3eb545b8fe528b4332b4f1359ef3b79401f'
bo=d/'syncsafe-math-v002/board-source-v008';bo.mkdir(exist_ok=False)
t=top_parent.read_text();old='cu71_system_direct_syncsafe #(';new='cu71_system_final_v008 #('
assert t.count(old)==1;t=t.replace(old,new)
top=bo/'moonshine_top_dy71.sv';top.write_text(t,newline='\n')
extras=['fpga/experiments/cu66-v71/bus-split/dy71_local_control_split.sv']
# Copy ONLY the explicitly selected safe control/stager/arbiter and wire endpoint.
extras=[n for n in b['sources']if n not in json.loads((d/'syncsafe-math-v002/sources.json').read_text())['sources']
        and not n.endswith('moonshine_top_dy71.sv')]
# Old core and old math sources are replaced as one complete explicit graph.
core_old=set(json.loads((d/'syncsafe-math-v002/sources.json').read_text())['sources'])
extras=[n for n in extras if not n.endswith(('cu71_base_pipeline_math.sv','cu71_idct_validpipe.sv'))]
assert any('dy71_local_control_safe.sv'in n for n in extras),extras
assert not any('cu71_local_control.sv' in n for n in extras)
b['sources']=list(dict.fromkeys(s['sources']+extras+[rel(top)]))
b['sources_sha256']={n:sha(r/n)for n in b['sources']}
b['system_module']=s['top']
b['status']='FINAL_COMPOSITION_FUNCTIONAL_AND_BOARD_REVIEW_PENDING_NO_IMAGE'
b['native_guard_references'].update({rel(core_path):sha(core_path),rel(out/'sources.json'):sha(out/'sources.json'),
 rel(out/'derivation.json'):sha(out/'derivation.json'),rel(event):sha(event),rel(owner):sha(owner),
 'fpga/experiments/cu66-v71/transport-nonzero/samecycle-v001/qualification-v001.json':
 sha(r/'fpga/experiments/cu66-v71/transport-nonzero/samecycle-v001/qualification-v001.json')})
b['root_pending_gates']=['Independent final composition/source-port review','Actual final KEY/P/P and v36/native safe-CSR pairing',
 'Clean short-private-temp full-board implementation and routed setup/hold/pulse/route/DRC/CDC/IO gates','Final BIT/hash and morning physical test after baseline25fps']
(bo/'selection.json').write_text(json.dumps(b,indent=2)+'\n')
(bo/'derivation.json').write_text(json.dumps(dict(parent_selection_sha256=sha(bp),core_manifest_sha256=sha(out/'sources.json'),
 transport_parent_sha256=sha(top_parent),top_binding_swap=[old,new],constraints_byte_identical=True,
 BIT=False,hardware=False,Vivado_started=False),indent=2)+'\n')
print(json.dumps(dict(core_manifest_sha256=sha(out/'sources.json'),board_selection_sha256=sha(bo/'selection.json'),
 receiver_sha256=sha(receiver),system_sha256=sha(system),top_sha256=sha(top),board_sources=len(b['sources']))))
