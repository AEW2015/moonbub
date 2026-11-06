"""Prepare an intentionally blocked physical-shell draft, never build/program."""
from pathlib import Path
import argparse,ast,hashlib,json,re,shutil
r=Path(__file__).resolve().parents[4];a=argparse.ArgumentParser();a.add_argument('--output',required=True);args=a.parse_args();d=r/'fpga/experiments/cu66-v71/direct-system/board-math-v001';o=(r/args.output).resolve();o.mkdir(parents=True,exist_ok=False);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();parent=r/'fpga/experiments/cu66-v71/board/source-v007';manifest=d/'sources.json';spec=json.loads(manifest.read_text());system=r/next(n for n in spec['sources']if Path(n).stem==spec['top']);control=r/'fpga/experiments/cu66-v71/direct-system/local-control/dy71_local_control.sv'
for n,h in spec['sources_sha256'].items():assert sha(r/n)==h,n
assert sha(control)=='a078678b9359ba06815727f2ddb14b3d7da963d279ca30352ebae7f7529165dc'
assert "12'h000:bus_rdata=32'h44593731" in control.read_text() and "12'h008:bus_rdata=32'h0000000f" in control.read_text()
def ports(path):
 s=path.read_text();m=re.search(r'module\s+\w+(?:\s*#\(.*?\))?\s*\((.*?)\n\);',s,re.S);assert m,path
 out={};direction=None;width=''
 for token in m[1].split(','):
  t=re.fullmatch(r'\s*(?:(input|output|inout)\s+(?:wire|logic|reg)\s*)?(\[[^\]]+\])?\s*(\w+)\s*',token);assert t,token
  if t[1]:direction=t[1];width=t[2]or''
  elif t[2]:width=t[2]
  out[t[3]]=(direction,width)
 return out
sp,cp=ports(system),ports(control);old=(parent/'moonshine_top_cu71.sv').read_text();header=old.split(' wire clk50',1)[0].replace('module moonshine_top_cu71(','module moonshine_top_dy71(')
clocks=' wire clk50'+old.split(' wire clk50',1)[1].split(' // Both domains',1)[0]
# Omit only the legacy unused rst200/rst100/rstpixel chains, not joint recovery.
clocks=clocks.split(' (* ASYNC_REG="TRUE" *)reg[3:0]rst200',1)[0]
prepare=r/'scripts/cu66-v71/prepare_board.py';tree=ast.parse(prepare.read_text());literals={}
for node in tree.body:
 if isinstance(node,ast.Assign)and isinstance(node.value,ast.Constant)and isinstance(node.value.value,str):
  for target in node.targets:
   if isinstance(target,ast.Name):literals[target.id]=node.value.value
body,tail=literals['body'],literals['tail'];physical=set(re.findall(r'\b(sdram_\w+)\b',header));explicit=physical|{'clk','rst','read_clk','pixel_clk','pixel_reset_n','bus_write','bus_address','bus_wdata','bus_rdata','transport_fault'}
union=dict(sp)
for name,sig in cp.items():
 if name in union:
  assert union[name][1]==sig[1],name
  assert name in explicit or union[name][0]!=sig[0],('Two drivers or undriven common input',name)
 union[name]=sig
for name,(direction,_)in sp.items():
 if direction=='input':assert name in explicit or name in cp and cp[name][0]=='output',('Unbound system input',name)
for name,(direction,_)in cp.items():
 if direction=='input':assert name in explicit or name in sp and sp[name][0]=='output',('Unbound control input',name)
assert 'USE_STRIP'not in sp and 'front_cache_slot'in sp and 'profile_magic'in sp
wires='\n'.join(' wire '+width+' '+name+';'for name,(_,width)in sorted(union.items())if name not in explicit)
instances=' dy71_local_control control_plane('+','.join('.'+n+'('+n+')'for n in cp)+');\n'
instances+=' '+spec['top']+' #(.WATCHDOG_CYCLES(32\'d3000000000)) system_core('+','.join('.'+n+'('+n+')'for n in sp)+');\n'
top=o/'moonshine_top_dy71.sv';top.write_text(header+clocks+body+wires+'\n'+instances+tail,newline='\n')
for n in ['moonshine_qspi_endpoint.sv','moonshine_bus_cdc.sv']:shutil.copyfile(parent/n,o/n)
(o/'constraints').mkdir()
for n in ['buttons.xdc','lcd_pins_rev4.xdc','sdram_pins_rev4.xdc']:shutil.copyfile(parent/'constraints'/n,o/'constraints'/n)
platform=(parent/'constraints/platform.xdc').read_text();assert platform.count('0x43553731')==2;platform=platform.replace('0x43553731','0x44593731');(o/'constraints/platform.xdc').write_text(platform,newline='\n')
t=(parent/'constraints/timing-cu71-reviewed.tcl').read_text().replace('CPL1','DY71')
assert 'set_input_delay -clock sdram_forwarded -max 7.0' in t and 'set_input_delay -clock sdram_forwarded -min 2.0'in t and 'set_multicycle_path 2 -setup'in t
t='''# BLOCKED DRAFT: parent root must select/prove SYNCsafe LCD and reviewed DY71 CSR.
error "DY71 physical draft blocked: SYNCsafe endpoint/CDC and local CSR integration gates pending"
'''+t+'''
# Direct-only held completion flags: add an actual payload bound, not a cut.
set direct_bad [required_cells direct_completed_bad {system_core/scanout/lcd/completed_bad[01]_reg}]
set direct_loaded [required_cells direct_loaded {system_core/scanout/lcd/loaded[01]_reg}]
if {[llength $direct_bad]!=2 || [llength $direct_loaded]!=2} {error "DY71 expects two held completion flags and two capture registers"}
foreach i {0 1} {
 set src [required_cells direct_bad_$i "system_core/scanout/lcd/completed_bad${i}_reg"]
 set dst [required_cells direct_loaded_$i "system_core/scanout/lcd/loaded${i}_reg"]
 set_max_delay -datapath_only 10.0 -from $src -to $dst
}
puts "DY71_COMPLETION_PAYLOAD_MAX10NS_REQUIRES_ROUTED_CDC_REVIEW=2"
'''
(o/'constraints/timing-dy71-DRAFT.tcl').write_text(t,newline='\n')
pins={str(f.relative_to(o)).replace('\\','/'):sha(f)for f in o.rglob('*')if f.is_file()}
(o/'proposal.json').write_text(json.dumps({'status':'BLOCKED_PHYSICAL_SOURCE_PROPOSAL_NOT_BUILD_SELECTION','top':'moonshine_top_dy71','part':'xc7a100tcsg324-1','system_module':spec['top'],'system_manifest_sha256':sha(manifest),'system_ports':sp,'control_module':'dy71_local_control','control_source_sha256':sha(control),'control_ports':cp,'shared_ports':sorted(set(sp)&set(cp)),'system_only_observation_outputs':sorted(n for n,(direction,_)in sp.items()if direction=='output'and n not in cp and n not in physical),'profile_magic_UID_USR_ACCESS':'0x44593731','ABI':'0x00010000','capabilities':'0x0f','source_files':pins,'clock_reset_pin_numeric_changes':False,'unused_legacy_reset_chains_omitted':True,'new_bundle_constraint_proposal':'2heldcompleted_bad flags→correspondingloadedFFs;10nsdatapathmax,exactobjectcountguards,nofunctionalfalsepaths','blockers':['CurrentselectedLCDrequests_idlefunctionallyusesmetastabilityfirststages;explicitSYNCsafebindingrequired','DY71CSR/fullphysicalbusadapterqualificationpending','Nativeobjectbinding/fit/fullroutedsetuphold/CDC/PVTandhardwarepending','QSPIexternalholdnotprovenbyinheritedbounds'],'inherited_analog_budget_status':'Provisionalqualifiedlabmodel/pinbudgets,notindependentPVTsignoff','hardware':False,'Vivado_started':False,'BIT':False,'parent_sources':{str(parent/'moonshine_top_cu71.sv'):sha(parent/'moonshine_top_cu71.sv'),str(prepare):sha(prepare)}},indent=2)+'\n');print('PREPARED_BLOCKED_DY71_PHYSICAL_PROPOSAL',len(sp),len(cp),sha(top))
