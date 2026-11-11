#!/usr/bin/env python3
"""Prepared, gated OOC synth-only experiment; no board or timing signoff."""
import argparse,datetime,hashlib,importlib.util,json,re,shutil,subprocess,sys,time,uuid
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3];AREA=ROOT/'experiments/python-gamebub-v130/active-prefetch/synth-only';BUILD=Path('/home/lori/gamebub-build/cu66-v69');FLOW=ROOT/'fpga/experiments/cu66-v120-flow'
BASELINE_LAUNCHER=ROOT/'scripts/cu66-v130/native/native.py';FOCUSED=ROOT/'experiments/python-gamebub-v130/active-prefetch/results.json';NEGATIVE=ROOT/'experiments/python-gamebub-v130/active-prefetch/negative/results.json';DER=ROOT/'fpga/experiments/cu66-v130-active-prefetch/derivation.json';CAND=ROOT/'fpga/experiments/cu66-v130-active-prefetch/cs88_admission_v91i2a.sv';ALIAS='fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv'
PREV=ROOT/'experiments/python-gamebub-v130/spec-read/native/20261111T024750249700Z/receipt.json';AUDITOR=Path(__file__).with_name('audit_preflight.py');IMAGE='sha256:dd51b5dd44148c23bb0059b929697243797022172d5efb01ffdd8b8dd7a89742';GIB=1024**3
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
load=lambda p:json.loads(Path(p).read_text())
rel=lambda p:str(Path(p).resolve().relative_to(ROOT))
pin=lambda p:{'path':rel(p),'sha256':sha(p)}
def need(x,msg):
 if not x:raise ValueError(msg)
def write(p,o):Path(p).write_text(json.dumps(o,indent=2,sort_keys=True)+'\n')
def memory():
 m={x.split(':')[0]:int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines()};q=next(x for x in Path('/proc/pressure/memory').read_text().splitlines() if x.startswith('full '))
 return {'available':m['MemAvailable'],'psi_full_avg10':float(q.split('avg10=')[1].split()[0]),'combined_used':(m['MemTotal']-m['MemAvailable']+m['SwapTotal']-m['SwapFree'])/(m['MemTotal']+m['SwapTotal'])}
def checked():
 spec=importlib.util.spec_from_file_location('v130_native_baseline',BASELINE_LAUNCHER);b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b);base=b.checked_proofs();d=load(DER);orig=ROOT/d['source'];s=orig.read_text();need(sha(orig)==d['source_sha256'] and sha(CAND)==d['candidate_sha256'],'candidate source drift')
 for e in d['edits']:
  need(s.count(e['old'])==1,'forward edit count');s=s.replace(e['old'],e['new'],1)
 need(s==CAND.read_text(),'candidate is not exact two-edit derivation')
 for e in reversed(d['edits']):
  need(s.count(e['new'])==1,'reverse edit count');s=s.replace(e['new'],e['old'],1)
 need(s==orig.read_text(),'reverse reconstruction failed')
 origins=dict(base['source_origins']);need(origins[ALIAS]==pin(orig) and len(origins)==18,'baseline alias mismatch');origins[ALIAS]=pin(CAND)
 pos=load(FOCUSED);pr=ROOT/pos['path'];need(pos['status']=='PASS' and sha(pr)==pos['sha256'],'positive selector');p=load(pr);need(p['status']=='PASS' and p['actual_RTL_run'] and p['source_snapshot_unchanged'],'positive proof')
 need(p['source_sha256'][rel(CAND)]==sha(CAND),'positive candidate pin')
 for path,h in p['source_sha256'].items():need(sha(ROOT/path)==h and sha(pr.parent/'sources'/path)==h,'positive source/snapshot '+path)
 for path,h in p['artifact_sha256'].items():need(sha(pr.parent/path)==h,'positive artifact '+path)
 need(len(p['runs'])==2,'two seeds');need({r[1]['seed'] for r in p['runs']}=={130301,130302},'seed mismatch')
 for r in p['runs']:
  need(r[0]['type']=='scan' and r[0]['status']=='PASS' and r[0]['cases']==6 and r[0]['cancellations']==15 and r[1]['status']=='PASS' and r[1]['same_epoch_retry'] and r[1]['invalid_databus_qualified'],'scenario mismatch')
 compiles=[c['argv'] for c in p['commands'] if 'verilator' in c['argv']];need(compiles and all('--assert' in c and '-Wall' in c and '-Wno-fatal' not in c and '-CFLAGS' in c and '-Werror' in c[c.index('-CFLAGS')+1] for c in compiles),'strict Verilator flags')
 neg=load(NEGATIVE);nr=ROOT/neg['path'];need(neg['status']=='PASS_EXPECTED_FAILURE_DETECTED' and sha(nr)==neg['sha256'],'negative selector');n=load(nr);need(n['status']==neg['status'] and n['actual_RTL_run'] and n['positive_receipt']==pos and n['binary_sha256']==p['binary_sha256'] and n['observed_exit_code'] not in (0,124,137) and n['stop_reason'] is None,'negative evidence');need(n['expected_detection'] in (nr.parent/'simulation.log').read_text() and sha(nr.parent/'simulation.log')==n['simulation_log_sha256'],'negative log')
 prior=load(PREV);need(prior['status']=='COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN' and prior['clock_period_ns']==8.0 and prior['source_contract']['source_origins']==base['source_origins'],'baseline V130 native identity')
 pins=dict(base['proof_pins']);pins.update({rel(x):sha(x) for x in (FOCUSED,pr,NEGATIVE,nr,DER,PREV,BASELINE_LAUNCHER)})
 return {'source_origins':origins,'source_order':base['source_order'],'baseline_component':pin(PREV),'positive':pin(pr),'negative':pin(nr),'proof_pins':pins,'changed_aliases':[ALIAS],'scope':'exploratory synthesis only; active scan and valid-qualified admission pair; full parent and external invalid bus unverified'}
def recipe():
 # Preserve fixed V120 implementation byte-for-byte through the synthesis
 # reports. The only addition is post-synth read-only mapping inventory.
 text=(FLOW/'run.tcl').read_text();marker='v116_phase OPT_DESIGN';need(text.count(marker)==1,'cannot identify fixed synthesis boundary');prefix=text[:text.index(marker)]
 extra='''# Read-only active-cell mapping inventory. No source, property or timing edits.
set f [open [file join $build results active-cell-inventory.tsv] w]
puts $f "kind\\tinstance\\tprimitive"
foreach c [lsort [get_cells -quiet -hierarchical -filter {NAME =~ *active_cell* || NAME =~ *active_scan_value*}]] {
    puts $f "cell\\t$c\\t[get_property REF_NAME $c]"
}
set readers [get_cells -quiet -hierarchical -filter {NAME =~ *active_scan_value_reg*}]
foreach c $readers {
    set dp [get_pins -quiet -of_objects $c -filter {REF_PIN_NAME == D}]
    if {[llength $dp]} {
        foreach p [lsort [all_fanin -flat -startpoints_only $dp]] {
            set sc [get_cells -quiet -of_objects $p]
            if {[llength $sc]} {puts $f "fanin\\t$sc\\t[get_property REF_NAME $sc]"}
        }
    }
}
close $f
v116_phase SYNTH_COMPLETE
puts "V130_ACTIVE_SYNTH_ONLY_FINISHED; no route, hardware or signoff"
'''
 return prefix+extra

def prepare(a):
 c=checked();stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');name='v130-active-synth-125-'+stamp+'-'+uuid.uuid4().hex[:6];build=BUILD/name;build.mkdir();out=AREA/'prepared'/name;out.mkdir(parents=True)
 for alias,meta in c['source_origins'].items():
  dst=build/'snapshot'/alias;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/meta['path'],dst)
 (build/'run.tcl').write_text(recipe());shutil.copyfile(FLOW/'report.tcl',build/'report.tcl');shutil.copyfile(FLOW/'clock-125.xdc',build/'component.xdc');mapped=Path('/build')/name
 def w(x):
  need(not any(z in str(x) for z in '{}\n\r'),'unsafe Tcl path');return '{'+str(x)+'}'
 order=c['source_order'];lines=['set part xc7a100tcsg324-1','set trial_id {active-synth-125}','set start_mode {rtl}','set expected_period_ns 8.0','set opt_directive {Default}','set place_directive {ExtraNetDelay_high}','set phys_directive {NONE}','set route_directive {Default}','set rtl_sources [list '+' '.join(w(mapped/'snapshot'/n) for n in order['rtl_read_order_aliases'])+']','set include_dirs [list '+' '.join(w(mapped/'snapshot'/n) for n in order['include_directory_aliases'])+']','set constraint_file '+w(mapped/'component.xdc')];(build/'inputs.tcl').write_text('\n'.join(lines)+'\n')
 card={'schema':'v130-active-synth-preflight-v1','status':'PREPARED_NOT_RUN','part':'xc7a100tcsg324-1','top':'cs88_pipeline_v91k','clock_period_ns':8.0,'start_mode':'rtl','build_external':str(build),'source_contract':c,'image_id':IMAGE,'timeout_seconds':3600,'cpus':2,'max_threads':2,'memory_limit_bytes':8*GIB,'memory_swap_limit_bytes':8*GIB,'max_heavy_jobs':2,'read_only_inventory_only':True,'synthesis_prefix_exact':True,'route_run':False,'hardware_contact':False,'full_parent_functional_pass':False,'timing_qualified':False,'recipe_sha256':{n:sha(build/n) for n in ('run.tcl','report.tcl','component.xdc','inputs.tcl')},'tooling_sha256':{rel(p):sha(p) for p in (Path(__file__),AUDITOR,FLOW/'run.tcl',FLOW/'report.tcl',FLOW/'clock-125.xdc')}}
 write(build/'inputs.json',card);write(out/'preflight.json',dict(card,inputs_sha256=sha(build/'inputs.json')));print(rel(out/'preflight.json'))

def run(a):
 p=load(a.preflight);need(p['status']=='PREPARED_NOT_RUN' and p['source_contract']==checked(),'preflight or proof drift');build=Path(p['build_external']).resolve();build.relative_to(BUILD);need(p==dict(load(build/'inputs.json'),inputs_sha256=sha(build/'inputs.json')),'prepared input drift')
 for name,h in p['recipe_sha256'].items():need(sha(build/name)==h,'recipe drift '+name)
 for name,h in p['tooling_sha256'].items():need(sha(ROOT/name)==h,'tooling drift '+name)
 for alias,meta in p['source_contract']['source_origins'].items():need(sha(build/'snapshot'/alias)==meta['sha256'],'snapshot drift '+alias)
 audit=load(a.audit);need(audit['status']=='PASS_ACTIVE_SYNTH_PREFLIGHT_AUDIT' and audit['preflight_sha256']==sha(a.preflight) and audit['auditor_sha256']==sha(AUDITOR) and audit['native_sha256']==sha(Path(__file__)),'independent preflight audit')
 need(a.license_file.is_file(),'license path unavailable');actual=subprocess.check_output(['docker','image','inspect','--format','{{.Id}}','acorn-nexys4-ddr:2026.1'],text=True).strip();need(actual==IMAGE,'tool image drift')
 before=memory();need(before['available']>=8*GIB and before['psi_full_avg10']<1 and before['combined_used']<.85,'launch gate');names=subprocess.check_output(['docker','ps','--format','{{.Names}}'],text=True).splitlines();need(sum(bool(re.match(r'^gamebub-v\d+-',n)) for n in names)<2,'heavy slot limit')
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'native'/stamp;out.mkdir(parents=True);name='gamebub-v130-active-synth-'+stamp.lower();mapped=Path('/build')/build.name
 cmd=['docker','run','--rm','--init','--name',name,'--memory','8g','--memory-swap','8g','--cpus','2','--pids-limit','2048','--network','host','--ulimit','core=0','--mount','type=bind,src=/home/lori/acorn-nexys4-ddr/tools,dst=/opt/amd-tools,readonly','--mount',f'type=bind,src={build},dst={mapped}','--mount',f'type=bind,src={build / "snapshot"},dst={mapped / "snapshot"},readonly','--mount',f'type=bind,src={a.license_file.resolve()},dst=/root/.Xilinx/license.dat,readonly','-e','LD_PRELOAD=/lib/x86_64-linux-gnu/libudev.so.1','-e','XILINXD_LICENSE_FILE=/root/.Xilinx/license.dat','-w',str(mapped),IMAGE,'timeout','--kill-after=15s','3600s','/opt/amd-tools/2026.1/Vivado/bin/vivado','-mode','batch','-nojournal','-nolog','-notrace','-source',str(mapped/'run.tcl'),'-tclargs',str(mapped)]
 shutil.copytree(build/'snapshot',out/'source-snapshot');(out/'recipe-snapshot').mkdir()
 for n in p['recipe_sha256']:shutil.copyfile(build/n,out/'recipe-snapshot'/n)
 shutil.copyfile(a.preflight,out/'preflight.json');shutil.copyfile(a.audit,out/'audit.json');shutil.copyfile(Path(__file__),out/'native.py');shutil.copyfile(AUDITOR,out/'audit_preflight.py')
 rec=dict(p,status='RUNNING',command=cmd,memory_samples=[],source_snapshot_readonly_mount=True);write(out/'receipt.json',rec);print('ACTIVE_SYNTH_STARTED',rel(out),flush=True)
 t=time.monotonic();last=-15;high=0;stop=None
 with (out/'vivado.log').open('w') as log:
  proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT)
  while proc.poll() is None:
   age=time.monotonic()-t
   if age-last>=15:
    x=memory();rec['memory_samples'].append(dict(elapsed=age,**x));last=age;high=high+1 if x['psi_full_avg10']>=5 else 0
    if x['available']<4*GIB or high>=2 or x['combined_used']>=.90:stop='HOST_MEMORY_PRESSURE'
   if age>3645:stop='HOST_WALL_TIMEOUT'
   if stop:subprocess.run(['docker','stop','--time','10',name],capture_output=True,timeout=20);break
   time.sleep(1)
  code=proc.wait(timeout=30)
 text=(out/'vivado.log').read_text(errors='replace');reports=out/'reports';reports.mkdir()
 for x in (build/'results').glob('*'):
  if x.is_file() and x.suffix in ('.rpt','.txt','.tsv','.json','.xdc','.log'):shutil.copyfile(x,reports/x.name)
 commands=re.findall(r'^Command:\s*(synth_design[^\n]*)',text,re.M);expected='synth_design -top cs88_pipeline_v91k -part xc7a100tcsg324-1 -mode out_of_context -flatten_hierarchy rebuilt';complete=code==0 and 'V130_ACTIVE_SYNTH_ONLY_FINISHED' in text and commands==[expected]
 rec.update(status='SYNTH_COMPLETE_EXPLORATORY' if complete else ('STOPPED_RESOURCE_OR_TIME_GATE' if stop else 'TOOL_OR_BUILD_FAILED'),observed_exit_code=code,monitor_stop_reason=stop,wall_seconds=time.monotonic()-t,synthesis_command_lines=commands,actual_synth_complete=complete,checkpoint_read=False,route_run=False,hardware_contact=False,physical_timing_qualified=False,hardware_30fps=False,complete_validated_decode_under10ms=False,source_snapshot_unchanged=all(sha(build/'snapshot'/n)==m['sha256'] for n,m in p['source_contract']['source_origins'].items()),recipe_unchanged=all(sha(build/n)==h for n,h in p['recipe_sha256'].items()),log_sha256=sha(out/'vivado.log'))
 if not rec['source_snapshot_unchanged'] or not rec['recipe_unchanged']:rec['status']='FAIL_INPUT_DRIFT'
 rec['retained_artifact_sha256']={str(x.relative_to(out)):sha(x) for x in sorted(out.rglob('*')) if x.is_file() and x.name!='receipt.json'};write(out/'receipt.json',rec);print('ACTIVE_SYNTH_FINISHED',rec['status'],rel(out/'receipt.json'),flush=True)
 if rec['status']!='SYNTH_COMPLETE_EXPLORATORY':raise SystemExit(1)

def main():
 p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='action',required=True);sub.add_parser('prepare');r=sub.add_parser('run');r.add_argument('--preflight',type=Path,required=True);r.add_argument('--audit',type=Path,required=True);r.add_argument('--license-file',type=Path,required=True);a=p.parse_args();(prepare if a.action=='prepare' else run)(a)
if __name__=='__main__':main()
