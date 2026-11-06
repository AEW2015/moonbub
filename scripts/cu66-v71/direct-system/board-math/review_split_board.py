"""Static independent binding/builder review; no Vivado or hardware."""
from pathlib import Path
import ast,hashlib,json,re
r=Path(__file__).resolve().parents[4];d=r/'fpga/experiments/cu66-v71/direct-system/syncsafe-math-v002';p=d/'board-source-v001';n=d/'board-source-v002';sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
s=json.loads((n/'selection.json').read_text());b=r/'scripts/cu66-v71/build_selected_board.py';text=b.read_text();ast.parse(text)
for category in ['sources_sha256','headers_sha256','constraints_sha256','native_guard_references']:
 for name,h in s[category].items():assert sha(r/name)==h,(category,name)
for f in(p/'constraints').iterdir():assert sha(f)==sha(n/'constraints'/f.name)
assert s['UID_USR_ACCESS']==s['CSR_magic']=='0x44593731' and s['capabilities']=='0x0f'
assert s['part']=='xc7a100tcsg324-1' and not s['BIT_ALLOWED'] and not s['PROGRAM_ALLOWED']
assert s['constraint_entry'] in s['constraints_sha256']
for f in s['XDC_order']:assert str(Path(s['constraint_entry']).parent/f).replace('\\','/')in s['constraints_sha256']
for forbidden in ['write_bitstream','program_hw_devices','open_hw_manager','connect_hw_server']:assert forbidden not in text,forbidden
for marker in ['required_reports_present','completion_marker','INCOMPLETE_NATIVE_IMPLEMENTATION','Frozen copied inputs changed','Live selected inputs changed']:assert marker in text,marker
top=(n/'moonshine_top_dy71.sv').read_text()
assert top.count('.core_read_address(bus_read_address)')==1 and top.count('.bus_read_address(bus_read_address)')==1
assert 'cu71_bus_cdc_split bridge(' in top and 'dy71_local_control_split control_plane(' in top
result={'status':'PASS_STATIC_SOURCE_AND_REPORT_ONLY_BUILDER_REVIEW','selection_sha256':sha(n/'selection.json'),'builder_sha256':sha(b),'derivation_sha256':sha(n/'derivation.json'),'all_selected_hashes_verified':True,'constraints_byte_identical_to_v001':True,'identity':'DY71/44593731 ABI10000 cap0f','no_BIT_or_hardware_commands':True,'builder_completion_marker_and_nonempty_reports_required':True,'remaining_limits':['Static review only, no elaboration or Vivado object queries executed','Native split CSR plus SYNCsafe/math co-simulation remains separately owned by SDF agent','Full-board timing/fit/CDC/DRC/pin constraints and physical QSPI remain unqualified','Builder report completion is explicitly not timing qualification','Guard references are verified live, not archived with copied source inputs; parent should preserve qualification evidence'],'hardware':False,'Vivado_started':False}
o=n/'review-v001.json';assert not o.exists();o.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'review':str(o),'review_sha256':sha(o),'builder_sha256':sha(b)},indent=2))
