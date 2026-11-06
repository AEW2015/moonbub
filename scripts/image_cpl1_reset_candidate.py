"""Generate CPL1 reset-candidate BIT only after exact-source functional/routed gates."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,sys,time
r=Path(__file__).resolve().parents[1]
a=argparse.ArgumentParser();a.add_argument('--candidate',default='fpga/candidates/cp23-reset-tags-20261105-v001');a.add_argument('--result',default='implementation02');a.add_argument('--output',required=True);args=a.parse_args()
c=(r/args.candidate).resolve();origin=c/'implementation02';p=c/args.result
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
gatecmd=[sys.executable,str(r/'scripts/check_cpl1_capture_build.py'),str(origin),'--result',str(p)]
subprocess.run(gatecmd,cwd=r,check=True)
gate=json.loads((p/'timing-gate.json').read_text());assert gate['status']=='PASS_DECLARED_ROUTED_TIMING'
assert 'ERROR:' not in (origin/'vivado.log').read_text()
assert 'ERROR:' not in (p/'vivado.log').read_text()
run=json.loads((p/'execution.json').read_text());assert run['returncode']==0
if p!=origin:
 assert run['RTL_changed'] is False and run['constraints_changed'] is False and run['parent_unchanged']
 # Every optimization must retain a hash-bound chain back to the source build.
 seen=set();current=p
 while current!=origin:
  assert str(current)not in seen;seen.add(str(current))
  m=json.loads((current/'execution.json').read_text())
  parent=Path(m['parent_checkpoint']);assert sha(parent)==m['parent_sha256']
  assert m['parent_unchanged'] and not m['RTL_changed'] and not m['constraints_changed']
  current=parent.parent
for n in ['full-budget-fast01','full-budget-slow01']:
 d=c/'evidence'/n;m=json.loads((d/'result.json').read_text())
 assert m['status']=='PASS_MODELED_DIGITAL_BOARD_ONLY' and m['CRC']=='4c5725e5'
 snap=json.loads((d/'source-snapshot.json').read_text())
 for name,h in snap['sources'].items():
  assert sha(d/'inputs'/name)==h
  f=origin/'inputs'/name
  if f.exists():assert sha(f)==h,('simulation/implementation mismatch',name)
 for name,h in snap['assets'].items():
  assert sha(d/name)==h
  if (origin/name).exists():assert sha(origin/name)==h,('asset mismatch',name)
assert json.loads((c/'evidence/envelope-equivalence02/result.json').read_text())['status']=='PASS_DIRECTED_PUBLIC_OUTPUT_COMPARISON'
compare=c/'evidence/envelope-equivalence02/candidate.sv'
assert compare.read_text().replace('module candidate(', 'module cp23_envelope(')==(origin/'inputs/core/parents/cp23_envelope.sv').read_text()
reservation=json.loads((c/'candidate.json').read_text()).get('sha_byte_reservation')
reservation_bindings={}
if reservation:
 for key,status in [('sha_suite','PASS_DIRECTED_SHA_SUITE_ONLY'),('cancel_suite','PASS_TARGETED_RESERVATION_CANCEL')]:
  proof=Path(reservation[key]);m=json.loads(proof.read_text());assert m['status']==status
  assert sha(proof.parent/'sha256_bytes.sv')==sha(origin/'inputs/core/compute/sha256_bytes.sv')
  assert (m.get('source_hashes')or m['sources'])['sha256_bytes.sv']==sha(proof.parent/'sha256_bytes.sv')
  reservation_bindings[key]=dict(path=str(proof),sha256=sha(proof))
 cut=c/'evidence/sha-write-cut01/result.json';m=json.loads(cut.read_text())
 assert m['status']=='PASS_CHECKED_SYNTHESIZED_STORAGE_CONE'and m['after_remote_sources']==0
 for name,h in m['artifacts'].items():assert sha(r/name)==h,name
 reservation_bindings['synthesized_storage_cut']=dict(path=str(cut),sha256=sha(cut))
o=Path(args.output).resolve();o.mkdir(parents=True,exist_ok=False);(o/'tmp').mkdir()
source=r/'fpga/exports/cpl1-timing-fsmcopy-source-20261105-v002/image/write-image.tcl'
shutil.copyfile(source,o/'executed-write-image.tcl')
bindings=dict(status='PASS_PRE_IMAGE_GATES_NOT_HARDWARE',candidate=str(c),result=str(p),checkpoint_sha256=sha(p/'routed.dcp'),
 source_freeze_sha256=sha(origin/'source-freeze.json'),timing_gate_sha256=sha(p/'timing-gate.json'),
 functional={n:sha(c/'evidence'/n/'result.json')for n in ['full-budget-fast01','full-budget-slow01','envelope-equivalence02']},
 writer_sha256=sha(o/'executed-write-image.tcl'),hardware=False)
bindings['sha_reservation_evidence']=reservation_bindings
(o/'source-binding.json').write_text(json.dumps(bindings,indent=2)+'\n')
env=dict(os.environ);env['TEMP']=str(o/'tmp');env['TMP']=str(o/'tmp')
cmd=['C:/Xilinx/2025.2/Vivado/bin/vivado.bat','-mode','batch','-source',str(o/'executed-write-image.tcl'),'-log',str(o/'vivado.log'),'-journal',str(o/'vivado.jou'),'-tclargs',str(p/'routed.dcp'),str(o)]
t=time.monotonic();q=subprocess.run(cmd,cwd=o,env=env)
(o/'execution.json').write_text(json.dumps(dict(command=cmd,returncode=q.returncode,seconds=time.monotonic()-t,hardware=False),indent=2)+'\n')
assert q.returncode==0
assert sha(p/'routed.dcp')==bindings['checkpoint_sha256']
assert 'ERROR:' not in (o/'vivado.log').read_text()
(o/'image-hashes.json').write_text(json.dumps({n:sha(o/n)for n in ['moonbub-cpl1-timing-rev4.1.bit','source-binding.json','executed-write-image.tcl','drc-native-inventory.txt','final-timing-summary.rpt','final-route-status.rpt']},indent=2)+'\n')
print('CPL1_RESET_CANDIDATE_BIT_GENERATED_NOT_PROGRAMMED',o)
