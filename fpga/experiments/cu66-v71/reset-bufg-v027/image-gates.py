"""Hash-bound native audit / lab BIT emission. Never opens hardware."""
from pathlib import Path
import argparse,datetime,hashlib,importlib.util,json,os,re,runpy,shutil,subprocess,sys,time
p=argparse.ArgumentParser();p.add_argument('--mode',choices=('audit','emit'),required=True);p.add_argument('--build',type=Path,required=True);p.add_argument('--audit',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
root=Path('C:/mb70');r=Path(__file__).resolve().parent;parent=root/'dy71-v027-20261107-v001'; inherited=root/'fpga/experiments/cu66-v71/result-admission-system-v023';build=a.build.resolve();out=a.out.resolve();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert build in (parent.resolve(),(parent/'incremental01').resolve(),(parent/'postroute01').resolve(),(parent/'postroute02').resolve()),'Only frozen v003 named physical candidates may be qualified'
runpy.run_path(str(inherited/'check-source-binding.py'),run_name='__main__')

# Inherit only unchanged decoder/system sources, never new control/pin behavior.
oldfreeze=json.loads((root/'dy71-v023-20261106-v001/source-freeze.json').read_text())
newfreeze=json.loads((parent/'source-freeze.json').read_text())
subprocess.run([sys.executable,str(root/'fpga/experiments/cu66-v71/hud-bulk-v025/check-component-bindings.py'),'--build',str(build)],check=True)
assert json.loads((build/'source-freeze.json').read_text())==newfreeze
assert all(sha(build/'inputs'/n)==h for n,h in newfreeze.items())
if build!=parent.resolve():
 assert sha(build/'constrained.dcp')==sha(parent/'constrained.dcp'),'Different synthesis checkpoint'
 assert sha(build/'bulk-funcsim.v')==sha(parent/'bulk-funcsim.v'),'Different simulated cell'
added=set(newfreeze)-set(oldfreeze)
expected_added={'fpga/experiments/cu66-v71/hud-bulk-v025/'+n for n in ['dy71_hud_bulk_v025.sv','dy71_local_control_bulk_v025.sv','cu71_bus_cdc_bulk_v025.sv','moonshine_top_dy71.sv']}|{'fpga/experiments/cu66-v71/rows-idle-capture-v026/cu71_tile_rows.sv'}|{'fpga/experiments/cu66-v71/reset-bufg-v027/moonshine_top_dy71.sv'}
assert added==expected_added,(added,expected_added)
platform='fpga/experiments/cu66-v71/direct-system/syncsafe-math-v002/board-source-v004/constraints/platform.xdc'
assert all(oldfreeze[n]==h for n,h in newfreeze.items() if n in oldfreeze and n!=platform),'Existing source/constraint changed'
assert (parent/'inputs'/platform).read_text()==(root/'dy71-v023-20261106-v001/inputs'/platform).read_text().replace('4459373b','4459373f'),'Platform differs beyond image identity'
bulk=root/'fpga/experiments/cu66-v71/hud-bulk-v025'
for name in ['functional04','pins05','legacy05','xsim-vendor04']:
 report=json.loads((bulk/name/'result.json').read_text());assert report['status'].startswith('PASS_')
if a.mode=='emit':
 post=json.loads((r/'xsim-full-synth01/result.json').read_text());assert post['status']=='PASS_XSIM_POST_SYNTH_BULK_NATIVE_WORDS'
 assert post['netlist_sha256']==sha(parent/'bulk-funcsim.v')

oracle_helper_path=root/'scripts/cu66-v71/verify_json_native_oracles.py'
oracle_helper=runpy.run_path(str(oracle_helper_path))
native_oracle_recheck=oracle_helper['verify'](inherited,'83bf51618ad5f0c94278b777d1a2ba2293a121371ba5950e44463d30ecc3601a')
native_oracle_recheck.update(helper_path=str(oracle_helper_path),helper_sha256=sha(oracle_helper_path))
spec=importlib.util.spec_from_file_location('old_native_helpers',root/'scripts/cu66-v71/image_dy71_candidate.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
spec=importlib.util.spec_from_file_location('versioned_bit_parser',root/'fpga/experiments/cu66-v71/board-schedule-v015/lab_bit_parser.py');bp=importlib.util.module_from_spec(spec);spec.loader.exec_module(bp)
freeze=json.loads((parent/'source-freeze.json').read_text());assert all(sha(parent/'inputs'/n)==h for n,h in freeze.items())

subprocess.run([sys.executable,str(root/'fpga/experiments/cu66-v71/rows-idle-capture-v026/check-proof-bindings.py')],check=True)
proof=json.loads((root/'fpga/experiments/cu66-v71/rows-idle-capture-v026/proof02/result.json').read_text());assert proof['status']=='PASS_EXACT_CONTROL_PROJECTION_AND_OWNED_PAYLOAD_INDUCTION'
row='fpga/experiments/cu66-v71/rows-idle-capture-v026/cu71_tile_rows.sv'
assert proof['source_sha256']['cu71_tile_rows.sv']==sha(parent/'inputs'/row)
assert json.loads((root/'fpga/experiments/cu66-v71/rows-idle-capture-v026/pair01/result.json').read_text())['status']=='PASS_OBSERVED_OLD_NEW_ROWS_AND_AUTHORITATIVE_PAYLOAD'
for corner in ('fast','slow'):
 d=inherited/('integration-'+corner+'01');v=json.loads((d/'source-binding.json').read_text())
 assert v['row_source']==row and v['row_sha256']==sha(parent/'inputs'/row)
 assert all(sha(Path(n))==h for n,h in v['files_sha256'].items())
 assert '/mnt/c/'+(d/'inputs'/row).as_posix()[3:] in v['compile_command'][-1]
 assert json.loads((d/'comparison.json').read_text())['status']=='PASS_EXACT_NATIVE_RASTER'
 assert all(x['returncode']==0 for x in json.loads((d/'execution.json').read_text()))
 assert 'SDK_RTL_COSIM_PASS' in (d/'native-integration.log').read_text()
cache='fpga/experiments/cu66-v71/chroma-fullword-v018/cu71_direct_cache_fullword_v018.sv'
assert sha(parent/'inputs'/cache)==json.loads(Path('C:/cs18f02/execution.json').read_text())['source_sha256']
assert json.loads(Path('C:/vcs18f03/execution.json').read_text())['status']=='PASS'

subprocess.run([sys.executable,str(inherited/'check-components.py'),'--require-mapping','--require-host'],check=True)

for corner in ('fast','slow'):
    d=inherited/('integration-'+corner+'01');assert json.loads((d/'comparison.json').read_text())['status']=='PASS_EXACT_NATIVE_RASTER'
    assert all(x['returncode']==0 for x in json.loads((d/'execution.json').read_text()))
    s=(d/'native-integration.log').read_text();assert 'SDK_RTL_COSIM_PASS'in s and s.count('OBSERVER_NATIVE_CSR_PASS pattern=')==2

reset_test=json.loads((r/'reset01/result.json').read_text());assert reset_test['status']=='PASS_ORIGINAL_RESET_STAGES_THROUGH_ACTUAL_BUFG_MODEL'
assert all(sha(Path(n))==h for n,h in reset_test['sources_sha256'].items())
assert sha(parent/'inputs/fpga/experiments/cu66-v71/reset-bufg-v027/moonshine_top_dy71.sv')==sha(r/'moonshine_top_dy71.sv')

timing=m.timing_metrics((build/'timing-summary.rpt').read_text());routes=m.route_metrics((build/'route-status.rpt').read_text())
execution=build/('implementation-execution.json'if(build/'implementation-execution.json').exists()else'execution.json');e=json.loads(execution.read_text());assert e['returncode']==0 and e['completion_marker'] and not e['native_errors']
dcp=build/'routed.dcp';h=sha(dcp);m.checkpoint_profile(dcp)
extra='''
set cells [get_cells -quiet -hier -regexp {lcd_observer/(rgb_out_reg\[[0-9]+\]|hs_out_reg|vs_out_reg|de_out_reg)}]
if {[llength $cells]!=27} {error "Wrong LCD output register count"}
set f [open [file join $out lcd-iob-registers.tsv] w]
foreach c $cells {
 set loc [get_property LOC $c];set bel [get_property BEL $c]
 puts $f "$c\t$loc\t$bel"
 if {![string match OLOGIC_* $loc] || ![string match *.OUTFF $bel]} {error "LCD output FF outside IOB"}
}
close $f
set f [open [file join $out held-status-paths.tsv] w]
foreach bank {0 1} {
 set src [get_pins [format {system_core/scanout/lcd/completed_bad%d_reg/C} $bank]]
 set dst [get_pins [format {system_core/scanout/lcd/loaded%d_reg/D} $bank]]
 set path [get_timing_paths -from $src -to $dst -delay_type max -max_paths 1]
 if {[llength $path]!=1 || [get_property SLACK $path]<=0} {error "Held status max-delay check failed"}
 puts $f "$src\t$dst\t[get_property REQUIREMENT $path]\t[get_property SLACK $path]"
}
close $f
report_timing -delay_type max -from [get_pins -hier -regexp {lcd_observer/snapshot_pixel_reg\[[0-9]+\]/C}] -to [get_pins -hier -regexp {lcd_observer/snapshot_mem_reg\[[0-9]+\]/D}] -max_paths 128 -file [file join $out observer-held-data.rpt]
report_timing -delay_type max -to [get_ports {lcd_hsync lcd_vsync lcd_data_en lcd_data_r[*] lcd_data_g[*] lcd_data_b[*]}] -max_paths 64 -file [file join $out lcd-output-setup.rpt]
report_timing -delay_type min -to [get_ports {lcd_hsync lcd_vsync lcd_data_en lcd_data_r[*] lcd_data_g[*] lcd_data_b[*]}] -max_paths 64 -file [file join $out lcd-output-hold.rpt]
'''
extra += 'set reset [filter [get_cells -quiet -hier -regexp {.*joint_core_reset_reg\\[[0-3]\\]}] {REF_NAME =~ FD*}]\nif {[llength $reset]!=4} {error "Wrong original protected reset topology"}\nset f [open [file join $out reset-topology.tsv] w]\nforeach c $reset {\n if {[get_property ASYNC_REG $c] ne "1"} {error "Original reset stage protection missing"}\n set clocks [get_clocks -of_objects [get_pins $c/C]]\n if {[llength $clocks]!=1 || abs([get_property PERIOD $clocks]-10.0)>0.001} {error "Reset clock mismatch"}\n puts $f "protected\\t$c\\t[get_property REF_NAME $c]\\t[get_property ASYNC_REG $c]"\n}\nclose $f\n'

extra += '\nset c [get_cells -quiet core_reset_distribution]\nif {[llength $c]!=1 || [get_property REF_NAME $c] ni {BUFG BUFGCTRL}} {error "Missing reset global buffer"}\nreport_property $c -file [file join $out reset-buffer.rpt]\n'
extra += '\nset rst_source [get_pins {joint_core_reset_reg[3]/C}]\nset rst_targets [get_pins -quiet -hier -filter {NAME =~ system_core/* && REF_PIN_NAME == R}]\nif {[llength $rst_source]!=1 || [llength $rst_targets]<100} {error "Reset coverage endpoints missing"}\nset rst_paths [get_timing_paths -from $rst_source -to $rst_targets -delay_type max -max_paths 16]\nif {[llength $rst_paths]<1} {error "Buffered reset paths are not timed"}\nforeach path $rst_paths {if {[get_property SLACK $path]<=0} {error "Buffered reset path violates setup"}}\nreport_timing -from $rst_source -to $rst_targets -delay_type max -max_paths 16 -file [file join $out reset-distribution-timing.rpt]\n'
out.mkdir(exist_ok=False);(out/'native-oracle-verification.json').write_text(json.dumps(native_oracle_recheck,indent=2)+'\n');shutil.copyfile(dcp,out/'routed-input.dcp');assert sha(out/'routed-input.dcp')==h
binding=dict(schema='V027_NATIVE_LAB_IMAGE_V1',mode=a.mode,build=str(build),checkpoint_sha256=h,source_freeze=freeze,timing=timing,routes=routes,core='cu71_system_final_v023',USERID_USR_ACCESS='4459373f',signed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),hardware=False,full_release=False,inherited_scope='Unchanged V023 components inherited; changed V026 rows have exact control/payload induction, paired RAM-output simulation and new fast/slow native raster runs. Scalar CSR simulation platform and new ABI2 bulk/pins are separate scopes. V027 additionally has the actual UNISIM reset-buffer test; no added reset stage or changed clock period/phase.',open_gates=['Exact V027/V43 original KEY/P physical fixture and all-word readback remain untested.','External QSPI full setup/hold/turnaround and measured LCD PCB skew remain unqualified.','No sustained 30 fps/custom-network/AV claim follows from native fixtures.'],c_check_handoff='UNAVAILABLE_MANUAL_HASH_INTEGRITY_ONLY')
script=m.native_script(build,out,False).replace('cu71_system_final_v010','cu71_system_final_v023').replace('0x44593731','0x4459373f')
if a.mode=='emit':
    assert a.audit is not None;ad=a.audit.resolve();ae=json.loads((ad/'execution.json').read_text());ab=json.loads((ad/'binding.json').read_text())
    assert ae['returncode']==0 and ae['completion_marker'] and not ae['native_errors']and ae['checkpoint_unchanged']
    assert ab['checkpoint_sha256']==h and sha(ad/'routed-input.dcp')==h
    assert ab['schema']=='V027_NATIVE_LAB_IMAGE_V1' and ab['mode']=='audit' and Path(ab['build']).resolve()==build
    assert ab['core']=='cu71_system_final_v023' and ab['USERID_USR_ACCESS']=='4459373f' and ab['source_freeze']==freeze
    assert json.loads((ad/'chroma-write-gate.json').read_text())['status']=='PASS_ALL_CHROMA_RAM_WRITE_PORTS'
    assert json.loads((ad/'interval-storage-gate.json').read_text())['status']=='PASS_INTERVAL_STATE_IN_REGISTERS'
    assert len((ad/'reset-topology.tsv').read_text().splitlines())>=4
    lcd=json.loads((ad/'lcd-path-gates.json').read_text());assert lcd['status']=='PASS_LCD_OUTPUT_SETUP_HOLD_COVERAGE'and lcd['checker_sha256']==sha(inherited/'check-lcd-reports.py')
    assert 'ERROR_COUNT\t0'in(ad/'native-drc.tsv').read_text();assert 'VIOLATED'not in(ad/'bus-skew.rpt').read_text()
    binding['audit_artifacts_sha256']={str(p):sha(p)for p in ad.iterdir()if p.is_file()and p.suffix!='.dcp'}
    action='write_bitstream [file join $out moonbub-v027-lab.bit]';marker='V027_LAB_BIT_EMITTED_NO_HARDWARE'
else:
    action='write_verilog -cell [get_cells system_core/scanout/cache] -mode funcsim [file join $out cache-funcsim.v]\nwrite_verilog -cell [get_cells system_core/receiver/base/entropy] -mode funcsim [file join $out entropy-funcsim.v]';marker='V027_NATIVE_AUDIT_COMPLETE_NO_BIT'
script=script.replace('close_design',extra+'\n'+action+'\nclose_design').replace('DY71_NATIVE_READONLY_AUDIT_COMPLETE_NO_BIT',marker)
(out/'executed.tcl').write_text(script);(out/'binding.json').write_text(json.dumps(binding,indent=2)+'\n')
tmp=Path('C:/vtmp')/('v025-'+a.mode+'-'+str(time.time_ns()));tmp.mkdir(parents=True)
cmd=['C:/Xilinx/2025.2/Vivado/bin/vivado.bat','-mode','batch','-source',str(out/'executed.tcl'),'-log',str(out/'vivado.log'),'-journal',str(out/'vivado.jou')];start=time.monotonic()
with(out/'console.log').open('x')as f:q=subprocess.run(cmd,cwd=out,stdout=f,stderr=subprocess.STDOUT,env=dict(os.environ,TEMP=str(tmp),TMP=str(tmp)))
log=(out/'console.log').read_text(errors='replace');result=dict(command=cmd,returncode=q.returncode,seconds=time.monotonic()-start,completion_marker=any(x.strip()==marker for x in log.splitlines()),native_errors=re.findall(r'^ERROR:.*',log,re.M),checkpoint_unchanged=sha(dcp)==sha(out/'routed-input.dcp')==h,hardware=False)
(out/'execution.json').write_text(json.dumps(result,indent=2)+'\n');assert q.returncode==0 and result['completion_marker']and not result['native_errors']and result['checkpoint_unchanged']
m.timing_metrics((out/'timing-summary.rpt').read_text());m.route_metrics((out/'route-status.rpt').read_text());assert 'ERROR_COUNT\t0'in(out/'native-drc.tsv').read_text()
lcd_gate=runpy.run_path(str(inherited/'check-lcd-reports.py'))
(out/'lcd-path-gates.json').write_text(json.dumps(lcd_gate['verify_pair'](out),indent=2)+'\n')
paths=re.findall(r'^Slack \(MET\)\s*:\s*([\d.]+)ns',(out/'observer-held-data.rpt').read_text(),re.M);assert len(paths)==96 and min(map(float,paths))>0
if a.mode=='audit':
    text=(out/'cache-funcsim.v').read_text();rows=[]
    for typ,param,name,pins in re.findall(r'(RAMB(?:18|36)E1)\s*#\((.*?)\)\s*(\\[^\r\n]+|[A-Za-z_0-9]+)\s*\((.*?)\);',text,re.S):
        if not any(k in name for k in ('cb_top_mem','cb_bottom_mem','cr_top_mem','cr_bottom_mem')):continue
        def pin(k):return re.search(r'\.'+k+r'\(([^\r\n]*)\)',pins)[1]
        def zero(s):return not re.sub(r"1'b0|[,{}\s]",'',s)
        def active(port,en,we):return int(re.search(r'\.WRITE_WIDTH_'+port+r'\((\d+)\)',param)[1])>0 and not zero(pin(en))and not zero(pin(we))
        rows.append(dict(instance=name.strip(),can_write=active('A','ENARDEN','WEA')or active('B','ENBWREN','WEBWE')))
    assert len(rows)==8 and all(x['can_write']for x in rows),rows
    (out/'chroma-write-gate.json').write_text(json.dumps(dict(status='PASS_ALL_CHROMA_RAM_WRITE_PORTS',rows=rows),indent=2)+'\n')
    entropy=(out/'entropy-funcsim.v').read_text();interval=[]
    for typ,param,name,pins in re.findall(r'(RAM[A-Z0-9]+|FDRE|FDSE|FDCE|FDPE)\s*#\((.*?)\)\s*(\\[^\r\n]+|[A-Za-z_0-9]+)\s*\((.*?)\);',entropy,re.S):
        if re.match(r'^(low|high|code|stream_position|pending_index_storage|pending_index)_reg(?:\[|_|$)',name.strip().rsplit('/',1)[-1].lstrip('\\')):
            interval.append(dict(primitive=typ,instance=name.strip()))
    assert interval and not any(x['primitive'].startswith('RAM')for x in interval),interval
    assert all(any(k in x['instance']for x in interval)for k in ('low_reg','high_reg','code_reg','stream_position_reg','pending_index')),interval
    families={'low':64,'high':64,'code':64}
    families.update(stream_position=128,pending_index_storage=96)
    counts={key:sum(bool(re.match('^'+re.escape(key)+r'_reg(?:\[|_|$)',row['instance'].strip().rsplit('/',1)[-1].lstrip('\\')))for row in interval)for key in families}
    assert counts==families,(counts,families)
    assert len(interval)==sum(families.values()),len(interval)
    (out/'interval-storage-gate.json').write_text(json.dumps(dict(status='PASS_INTERVAL_STATE_IN_REGISTERS',rows=interval,family_counts=counts,scope='Exact routed cell export; timing and functional gates are separate'),indent=2)+'\n')
else:
    bit=out/'moonbub-v027-lab.bit';parsed=bp.parse(bit.read_bytes(),expected_identity=0x4459373f)
    (out/'bit-validation.json').write_text(json.dumps(dict(sha256=sha(bit),bytes=bit.stat().st_size,parsed=parsed,hardware=False),indent=2)+'\n')
print(json.dumps(dict(mode=a.mode,output=str(out),timing=timing,hardware=False)),flush=True)
