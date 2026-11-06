"""Derive bus-split DY71 shell, preserving every v001 physical constraint."""
from pathlib import Path
import hashlib,json,re,shutil,tkinter
r=Path(__file__).resolve().parents[4]
d=r/'fpga/experiments/cu66-v71/direct-system/syncsafe-math-v002'
p=d/'board-source-v001';o=d/'board-source-v002';assert not o.exists()
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
old=json.loads((p/'selection.json').read_text())
for key in ['sources_sha256','headers_sha256','constraints_sha256','native_guard_references']:
 for n,h in old[key].items():assert sha(r/n)==h,n
b=r/'fpga/experiments/cu66-v71/bus-split';proof=b/'qualification-v001.json';q=json.loads(proof.read_text());assert q['functional_runs']==6 and q['latency_change'] is False
expected={'cu71_bus_cdc_split.sv':'56628dc5d5b5f4ddb32257c4119e9c02a7a85848687feb89051c5a376409596b','dy71_local_control_split.sv':'84757d07c3de49aa4c4bba49130b9b86a4d88e26f84f660e618ef989d0d7d716'}
for n,h in expected.items():assert sha(b/n)==h
source=(p/'moonshine_top_dy71.sv').read_text()
changes=[('wire[11:0]bus_address;','wire[11:0]bus_address;wire[11:0]bus_read_address;'),('moonshine_bus_cdc bridge(','cu71_bus_cdc_split bridge('),('.core_address(bus_address),','.core_address(bus_address),.core_read_address(bus_read_address),'),('dy71_local_control control_plane(','dy71_local_control_split control_plane('),('.bus_address(bus_address),','.bus_address(bus_address),.bus_read_address(bus_read_address),')]
candidate=source
for before,after in changes:assert candidate.count(before)==1,before;candidate=candidate.replace(before,after)
reverse=candidate
for before,after in reversed(changes):reverse=reverse.replace(after,before)
assert reverse==source
o.mkdir();(o/'moonshine_top_dy71.sv').write_text(candidate,newline='\n')
shutil.copyfile(p/'moonshine_qspi_endpoint.sv',o/'moonshine_qspi_endpoint.sv')
shutil.copyfile(b/'cu71_bus_cdc_split.sv',o/'cu71_bus_cdc_split.sv')
shutil.copytree(p/'constraints',o/'constraints')
for f in(p/'constraints').iterdir():assert sha(f)==sha(o/'constraints'/f.name)
control=r/'fpga/experiments/cu66-v71/direct-system/local-control/dy71_local_control.sv'
newcontrol=b/'dy71_local_control_split.sv'
def portnames(path):
 text=path.read_text().split(');',1)[0]
 return re.findall(r'\b(?:input|output|inout)\s+(?:wire|reg)\s*(?:\[[^]]+\])?\s*(\w+)',text)
# Exact public CSR signature is the previous signature plus one read-address input.
oldheader=control.read_text().split(');',1)[0]
newheader=newcontrol.read_text().split(');',1)[0].replace('module dy71_local_control_split(','module dy71_local_control(').replace('input wire [11:0] bus_read_address,','')
assert newheader==oldheader
selection=dict(old)
oldprefix=p.relative_to(r).as_posix();newprefix=o.relative_to(r).as_posix()
newcontrolname=newcontrol.relative_to(r).as_posix();oldcontrolname=control.relative_to(r).as_posix()
selection['sources']=[n.replace(oldprefix,newprefix).replace('moonshine_bus_cdc.sv','cu71_bus_cdc_split.sv') if n!=oldcontrolname else newcontrolname for n in old['sources']]
selection['sources_sha256']={n:sha(r/n)for n in selection['sources']}
selection['constraints_sha256']={n.replace(oldprefix,newprefix):h for n,h in old['constraints_sha256'].items()}
selection['constraint_entry']=old['constraint_entry'].replace(oldprefix,newprefix)
selection['CSR_ports']=dict(old['CSR_ports'],bus_read_address=['input','[11:0]'])
selection['native_guard_references']=dict(old['native_guard_references'])
for f in [p/'selection.json',proof,b/'component-sources.json',Path(__file__).resolve()]:selection['native_guard_references'][f.relative_to(r).as_posix()]=sha(f)
selection['status']='SOURCE_FUNCTIONAL_GATES_PASS_SPLIT_COMPONENT_ROOT_BOARD_REVIEW_PENDING'
selection['bus_split']={'bridge':'cu71_bus_cdc_split','CSR':'dy71_local_control_split','read_address':'bridge.core_read_address -> control_plane.bus_read_address','new_wire':'bus_read_address[11:0]','latency_change':False,'physical_constraints_changed':False,'actual_split_SYNSAFE_math_native_CSR_gate':'PENDING_SEPARATE_SDF_PROOF'}
interpreter=tkinter.Tcl()
for f in(o/'constraints').glob('*.tcl'):assert int(interpreter.call('info','complete',f.read_text()))==1
derivation={'parent_selection_sha256':sha(p/'selection.json'),'reversible_exact_top_changes':changes,'old_system_ports':140,'new_system_ports':140,'old_CSR_ports':84,'new_CSR_ports':85,'constraint_files_byte_identical':True,'system_sources_unchanged':True,'Vivado_started':False,'hardware':False,'BIT':False}
(o/'derivation.json').write_text(json.dumps(derivation,indent=2)+'\n')
selection['native_guard_references'][(o/'derivation.json').relative_to(r).as_posix()]=sha(o/'derivation.json')
(o/'selection.json').write_text(json.dumps(selection,indent=2)+'\n')
(o/'source-freeze.json').write_text(json.dumps(dict(selection['sources_sha256'],**selection['headers_sha256'],**selection['constraints_sha256']),indent=2)+'\n')
print(json.dumps({'selection':str(o/'selection.json'),'selection_sha256':sha(o/'selection.json'),'top_sha256':sha(o/'moonshine_top_dy71.sv'),'derivation_sha256':sha(o/'derivation.json'),'Vivado_started':False},indent=2))
