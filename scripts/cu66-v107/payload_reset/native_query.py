#!/usr/bin/env python3
"""Read-only DCP fanin query correcting empty get_ports -of_objects columns."""
import datetime,hashlib,json,shutil,subprocess,time
from pathlib import Path
from native import memory
ROOT=Path(__file__).resolve().parents[3];AREA=ROOT/'experiments/python-gamebub-v107/payload-reset/native'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 selected=json.loads((AREA/'results.json').read_text());prior=ROOT/selected['selected_receipt'];receipt=json.loads(prior.read_text());assert receipt['exit_code']==0
 frozen=Path(receipt['build_external']);stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'query'/stamp;out.mkdir(parents=True);build=frozen.parent/('v107-dequant-query-'+stamp);build.mkdir();mapped='/build/'+build.name
 tcl=r'''set build [file normalize [lindex $argv 0]]
set_param general.maxThreads 2
proc input_starts {pin} {
 set names {}
 foreach obj [all_fanin -flat -startpoints_only -to $pin] {
  if {[get_property CLASS $obj] eq "port"} {lappend names $obj}
 }
 return [lsort -unique $names]
}
file mkdir [file join $build results]
foreach variant {original candidate} {
 open_checkpoint /frozen/results/$variant/synth.dcp
 set f [open [file join $build results ${variant}.tsv] w]
 puts $f "cell\treset_ground\treset_ports\tce_ports\tce_register_starts"
 set payload [get_cells -hierarchical -regexp {(^|.*/)(coefficients_reg\[[0-9]+\]|chroma_reg|scale_code_reg\[[0-9]+\])}]
 if {[llength $payload]!=1027} {error "expected1027"}
 foreach c [lsort $payload] {
  set reset [get_pins $c/R];set ce [get_pins $c/CE]
  set ground 0
  foreach p [get_pins -of_objects [get_nets -of_objects $reset] -filter {DIRECTION == OUT}] {if {[get_property REF_NAME [get_cells -of_objects $p]] eq "GND"} {set ground 1}}
  set regstarts {}
  foreach p [all_fanin -flat -startpoints_only -to $ce] {if {[get_property CLASS $p] eq "pin"} {lappend regstarts $p}}
  puts $f [join [list $c $ground [input_starts $reset] [input_starts $ce] [lsort -unique $regstarts]] \t]
 }
 close $f
 close_design
}
puts DEQUANT_EXACT_FANIN_QUERY_PASS
'''
 (build/'query.tcl').write_text(tcl);shutil.copyfile(build/'query.tcl',out/'query.tcl');shutil.copyfile(Path(__file__),out/'native_query.py');dcps=[frozen/'results'/v/'synth.dcp' for v in ('original','candidate')];before={str(x):sha(x) for x in dcps}
 gate=memory();assert gate['available_bytes']>=8*1024**3 and gate['psi_full_avg10']<1,gate
 name='gamebub-v107-dequant-query-'+stamp.lower();command=['docker','run','--rm','--init','--name',name,'--memory','8g','--memory-swap','8g','--cpus','2','--pids-limit','2048','--network','host','--ulimit','core=0','--mount','type=bind,src=/home/lori/acorn-nexys4-ddr/tools,dst=/opt/amd-tools,readonly','--mount','type=bind,src=/home/lori/acorn-nexys4-ddr/cache/vivado.lic,dst=/root/.Xilinx/license.dat,readonly','--mount',f'type=bind,src={frozen},dst=/frozen,readonly','--mount',f'type=bind,src={build},dst={mapped}','-e','LD_PRELOAD=/lib/x86_64-linux-gnu/libudev.so.1','-e','XILINXD_LICENSE_FILE=/root/.Xilinx/license.dat','-w',mapped,'acorn-nexys4-ddr:2026.1','timeout','--signal=TERM','--kill-after=15s','180s','/opt/amd-tools/2026.1/Vivado/bin/vivado','-mode','batch','-nojournal','-nolog','-notrace','-source','query.tcl','-tclargs',mapped]
 r=dict(schema='v107-dequant-exact-port-fanin-query-v1',status='RUNNING',prior_receipt=str(prior.relative_to(ROOT)),prior_receipt_sha256=sha(prior),candidate_sha256=receipt['candidate_sha256'],dcp_sha256_before=before,command=command,resource_before=gate,correction='Historical get_ports -of_objects returned empty columns for both variants; classify actual all_fanin startpoints by CLASS port instead.',memory_samples=[]);start=time.monotonic();stop=None;code=None;last=-5
 try:
  with (out/'tool.log').open('w') as log:
   proc=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT)
   while proc.poll() is None:
    elapsed=time.monotonic()-start
    if elapsed-last>=5:
     sample=dict(elapsed_seconds=elapsed,**memory());r['memory_samples'].append(sample);last=elapsed
     if sample['available_bytes']<4*1024**3 or sample['psi_full_avg10']>=5:stop='HOST_MEMORY_GATE'
    if elapsed>220:stop='HOST_TIMEOUT'
    if stop:subprocess.run(['docker','stop','--time','10',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=20);break
    time.sleep(.5)
   code=proc.wait(timeout=30)
  assert code==0,(code,stop)
  import csv
  metrics={}
  for variant in ('original','candidate'):
   rows=list(csv.DictReader((build/'results'/f'{variant}.tsv').open(),delimiter='\t'));assert len(rows)==1027
   metrics[variant]=dict(cells=len(rows),ground_reset=sum(int(x['reset_ground']) for x in rows),reset_ports=sorted(set(x['reset_ports'] for x in rows)),ce_ports=sorted(set(x['ce_ports'] for x in rows)),ce_register_starts=sorted(set(x['ce_register_starts'] for x in rows)))
  assert metrics['original']['ground_reset']==0 and metrics['candidate']['ground_reset']==1027
  assert metrics['original']['reset_ports']==['abort_i rst'] and metrics['original']['ce_ports']==['abort_i in_valid rst']
  assert metrics['candidate']['reset_ports']==[''] and metrics['candidate']['ce_ports']==[''] and metrics['candidate']['ce_register_starts']!=['']
  r.update(status='PASS_EXACT_MAPPED_PAYLOAD_RESET_AND_CE_FANIN',metrics=metrics)
 except BaseException as e:r.update(status='FAIL',error=repr(e));raise
 finally:
  r.update(exit_code=code,stop_reason=stop,wall_seconds=time.monotonic()-start,dcp_sha256_after={str(x):sha(x) for x in dcps});assert before==r['dcp_sha256_after']
  for p in (build/'results').glob('*.tsv'):shutil.copyfile(p,out/p.name)
  r['artifacts_sha256']={str(p.relative_to(out)):sha(p) for p in out.iterdir() if p.is_file() and p.name!='receipt.json'};(out/'receipt.json').write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');(AREA/'query-results.json').write_text(json.dumps(dict(status=r['status'],selected_receipt=str((out/'receipt.json').relative_to(ROOT)),sha256=sha(out/'receipt.json')),indent=2)+'\n');print(r['status'],flush=True)
if __name__=='__main__':main()
