"""Generate reviewed-source DY71 shell inputs only; never launch Vivado."""
from pathlib import Path
import argparse,ast,hashlib,json,re,shutil,tkinter
r=Path(__file__).resolve().parents[4];a=argparse.ArgumentParser();a.add_argument('--output',required=True);args=a.parse_args();d=r/'fpga/experiments/cu66-v71/direct-system/syncsafe-math-v002';o=(r/args.output).resolve();assert not o.exists();sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();manifest=d/'sources.json';spec=json.loads(manifest.read_text());qpath=d/'qualification-native-v002.json';q=json.loads(qpath.read_text());assert q['status']=='PASS_SYNCsafe_DY71_WHOLE_NATIVE_KEY_P_P_AND_FANOUT_REFERENCES'
for n,h in q['proofs'].items():assert sha(r/n)==h,n
for n,h in spec['sources_sha256'].items():assert sha(r/n)==h,n
cdc=r/'fpga/experiments/cu66-v71/direct-display/cdc';handoff=cdc/'handoff02/manifest.json';h=json.loads(handoff.read_text());assert h['remaining_manual_CDC']['CDC1']==2
for art in h['artifacts']:assert sha(r/art['path'])==art['sha256'],art['path']
csr=r/'fpga/experiments/cu66-v71/direct-system/local-control';control=csr/'dy71_local_control.sv';assert sha(control)=='a078678b9359ba06815727f2ddb14b3d7da963d279ca30352ebae7f7529165dc';csrproof=csr/'qualification-v001.json';assert json.loads(csrproof.read_text())['status']=='PASS_DY71_LOCAL_CSR_ACTUAL_V36_NATIVE_KEY_P_CORRECTNESS_ONLY'
assert "12'h000:bus_rdata=32'h44593731"in control.read_text()and"12'h008:bus_rdata=32'h0000000f"in control.read_text()
# Reuse the reviewed actual-port parser without executing the old generator.
helper=Path(__file__).with_name('prepare_shell_proposal.py');tree=ast.parse(helper.read_text());node=next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name=='ports');exec(compile(ast.Module(body=[node],type_ignores=[]),str(helper),'exec'),globals())
system=r/next(n for n in spec['sources']if Path(n).stem==spec['top']);sp,cp=ports(system),ports(control);assert len(sp)==140 and len(cp)==84
parent=r/'fpga/experiments/cu66-v71/board/source-v007';old=(parent/'moonshine_top_cu71.sv').read_text();header=old.split(' wire clk50',1)[0].replace('module moonshine_top_cu71(','module moonshine_top_dy71(');clocks=' wire clk50'+old.split(' wire clk50',1)[1].split(' // Both domains',1)[0];clocks=clocks.split(' (* ASYNC_REG="TRUE" *)reg[3:0]rst200',1)[0]
prepare=r/'scripts/cu66-v71/prepare_board.py';tree=ast.parse(prepare.read_text());literals={}
for n in tree.body:
 if isinstance(n,ast.Assign)and isinstance(n.value,ast.Constant)and isinstance(n.value.value,str):
  for target in n.targets:
   if isinstance(target,ast.Name):literals[target.id]=n.value.value
body,tail=literals['body'],literals['tail'];physical=set(re.findall(r'\b(sdram_\w+)\b',header));explicit=physical|{'clk','rst','read_clk','pixel_clk','pixel_reset_n','bus_write','bus_address','bus_wdata','bus_rdata','transport_fault'};union=dict(sp)
for name,sig in cp.items():
 if name in union:assert union[name][1]==sig[1]and(name in explicit or union[name][0]!=sig[0]),name
 union[name]=sig
for name,(direction,_)in sp.items():
 if direction=='input':assert name in explicit or name in cp and cp[name][0]=='output',name
for name,(direction,_)in cp.items():
 if direction=='input':assert name in explicit or name in sp and sp[name][0]=='output',name
wires='\n'.join(' wire '+width+' '+name+';'for name,(_,width)in sorted(union.items())if name not in explicit)
instances=' dy71_local_control control_plane('+','.join('.'+n+'('+n+')'for n in cp)+');\n'+spec['top']+' #(.WATCHDOG_CYCLES(32\'d3000000000)) system_core('+','.join('.'+n+'('+n+')'for n in sp)+');\n'
o.mkdir(parents=True);(o/'moonshine_top_dy71.sv').write_text(header+clocks+body+wires+'\n'+instances+tail,newline='\n')
for name in ['moonshine_qspi_endpoint.sv','moonshine_bus_cdc.sv']:shutil.copyfile(parent/name,o/name)
c=o/'constraints';c.mkdir()
for name in ['buttons.xdc','lcd_pins_rev4.xdc','sdram_pins_rev4.xdc']:shutil.copyfile(parent/'constraints'/name,c/name)
platform=(parent/'constraints/platform.xdc').read_text();assert platform.count('0x43553731')==2;(c/'platform.xdc').write_text(platform.replace('0x43553731','0x44593731'),newline='\n')
t=(parent/'constraints/timing-cu71-reviewed.tcl').read_text()
# Remove only obsolete LCD constraints. Leaving their false paths would override
# the corrected legal C-start endpoint bounds from the selected CDC candidate.
lines=t.splitlines(True);cut=[x for x in lines if x.startswith('first_stage lcd_tokens ')];assert len(cut)==1;t=t.replace(cut[0],'')
start=t.index('set ugray ');end=t.index('# Bundled payloads',start);t=t[:start]+t[end:]
start=t.index('set request_lines ');end=t.index('set reset_cells ',start);removed=t[start:end];assert 'set line_address 'in removed and '-from $request_lines -to $line_address'in removed;t=t[:start]+t[end:]
assert 'first_stage lcd_tokens'not in t and 'set ugray 'not in t and 'set request_lines 'not in t
t=t.replace('CPL1','DY71')
for text in ['set_input_delay -clock sdram_forwarded -max 7.0','set_input_delay -clock sdram_forwarded -min 2.0','set_output_delay -clock sdram_forwarded -min -1.3','set_multicycle_path 2 -setup','set_false_path -fall_from $sdr_command_clock -through $sdr_q']:assert text in t,text
t+='''
# Exact selected direct-display C-start constraints and topology audit.
set DIRECT_DISPLAY_ROOT "system_core/scanout"
source [file join [file dirname [info script]] direct_cdc_candidate.tcl]
source [file join [file dirname [info script]] lcd-first-stage-guards.tcl]
puts "DY71_INTERNAL_CDC_BOUNDS_REQUIRE_ROOT_OBJECT_REPORT_REVIEW=1"
'''
(c/'timing-dy71-reviewed.tcl').write_text(t,newline='\n');candidate=cdc/'direct_cdc_candidate.tcl';assert 'set start [direct_pins $source C]'in candidate.read_text();shutil.copyfile(candidate,c/candidate.name)
guard=r/'fpga/experiments/cu66-v71/direct-system/board-math-v001/lcd-first-stage-guard-DRAFT.tcl';shutil.copyfile(guard,c/'lcd-first-stage-guards.tcl')
interpreter=tkinter.Tcl()
for f in c.glob('*.tcl'):assert int(interpreter.call('info','complete',f.read_text()))==1,f
sources=list(spec['sources']);sources.extend(f.relative_to(r).as_posix()for f in [control,r/'fpga/experiments/cu66-v71/system/cu71_packet_staging.sv',r/'fpga/experiments/cu66-v71/system/cu71_packet_arbiter.sv',o/'moonshine_top_dy71.sv',o/'moonshine_qspi_endpoint.sv',o/'moonshine_bus_cdc.sv']);assert len(sources)==len(set(sources));pins={n:sha(r/n)for n in sources};headers={}
for inc in spec['include_dirs']:
 for f in(r/inc).glob('*.svh'):headers[f.relative_to(r).as_posix()]=sha(f)
constraints={f.relative_to(r).as_posix():sha(f)for f in c.iterdir()};refs={f.relative_to(r).as_posix():sha(f)for f in [manifest,qpath,handoff,cdc/'syncsafe-ooc02/first-stage-fanout.txt',csrproof,csr/'control-sources.json',candidate,guard,prepare,helper,Path(__file__).resolve()]}
selection={'status':'SOURCE_FUNCTIONAL_GATES_PASS_ROOT_BOARD_REVIEW_PENDING','BUILD_ALLOWED':True,'BUILD_ALLOWED_SCOPE':'Synthesis/place/route/object-binding only after root review; not image/program qualification','BIT_ALLOWED':False,'PROGRAM_ALLOWED':False,'top':'moonshine_top_dy71','part':'xc7a100tcsg324-1','system_module':spec['top'],'sources':sources,'sources_sha256':pins,'include_dirs':spec['include_dirs'],'headers_sha256':headers,'constraints_sha256':constraints,'constraint_entry':(c/'timing-dy71-reviewed.tcl').relative_to(r).as_posix(),'XDC_order':['lcd_pins_rev4.xdc','sdram_pins_rev4.xdc','buttons.xdc','platform.xdc'],'SIMULATION':False,'UID_USR_ACCESS':'0x44593731','CSR_magic':'0x44593731','ABI':'0x00010000','capabilities':'0x0f','watchdog_clocks':3000000000,'system_ports':sp,'CSR_ports':cp,'native_guard_references':refs,'remaining_manual_CDC':h['remaining_manual_CDC'],'clock_IO_SDRAM_budget_changes':False,'removed_obsolete_LCD_exceptions':True,'legal_C_start_CDC_bounds':True,'stage0_fanout_guards':6,'root_pending_gates':['Exact full-board object counts, fanout and exception coverage','No path segmentation or empty bus-skew coverage','Resource/route/DRC/setup/hold/pulse and CDC reports','SYNCsafe/math CSR co-simulation retarget and physical QSPI hold','Controlled app-only/volatile hardware test and rollback'],'hardware':False,'Vivado_started':False}
(o/'selection.json').write_text(json.dumps(selection,indent=2)+'\n');(o/'source-freeze.json').write_text(json.dumps(dict(pins,**headers,**constraints),indent=2)+'\n');print(json.dumps({'source':str(o),'selection_sha256':sha(o/'selection.json'),'top_sha256':sha(o/'moonshine_top_dy71.sv'),'ports':[len(sp),len(cp)],'Vivado_started':False}))
