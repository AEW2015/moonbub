from pathlib import Path
import argparse,json,hashlib,shutil,subprocess,shlex,time
r=Path(__file__).resolve().parents[4];d=r/'fpga/experiments/cu66-v71/owner-timing/tag-capture-v001';n=d/'native-binding';ref=r/'fpga/experiments/cu66-v71/direct-system/validpipe-v003/evidence/native-three01';p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();o=Path(a.output).resolve();o.mkdir(parents=True,exist_ok=False);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();lin=lambda p:'/mnt/'+p.resolve().drive[0].lower()+p.resolve().as_posix()[2:]
parent=r/'fpga/experiments/cu66-v71/direct-system/validpipe-v003/sources.json';candidate=n/'sources.json';pins={str(f):sha(f)for f in[parent,candidate,n/'tb-observed.cpp',n/'derivation.json',Path(__file__)]};steps=[];results={}
def run(label,args,timeout=1800):
 command=['wsl.exe','-d','MRS-HDL-Research','--','bash','-lc','source /opt/gamebub-openxc7-20261021/oss-cad-suite/environment && '+shlex.join(list(map(str,args)))];start=time.monotonic()
 with(o/(label+'.log')).open('wb')as out:q=subprocess.run(command,stdout=out,stderr=subprocess.STDOUT,timeout=timeout)
 steps.append(dict(label=label,command=command,returncode=q.returncode,seconds=time.monotonic()-start));(o/'execution.json').write_text(json.dumps(steps,indent=2)+'\n');print(label,q.returncode,flush=True);assert q.returncode==0,(label,o)
 return(o/(label+'.log')).read_text()
for label,selection,wrapper in[('parent',parent,ref/'cu71_direct_system_sim.sv'),('candidate',candidate,n/'cu71_direct_system_sim.sv')]:
 sub=o/label;sub.mkdir();m=json.loads(selection.read_text());assert all(sha(r/p)==h for p,h in m['sources_sha256'].items());compiled=[]
 for f in[r/p for p in m['sources']]+[wrapper,ref/'model-verilator.sv',r/'fpga/experiments/cu66-v71/memory/evidence/direct-fast01/primitives.sv']:
  target=sub/'inputs'/f.relative_to(r);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,target);compiled.append(target);pins[str(f)]=sha(f)
 shutil.copy2(n/'tb-observed.cpp',sub/'tb.cpp');includes=[r/p for p in m['include_dirs']];args=['verilator','--cc','--exe','--build','-j','2','--timing','--assert','--Wall','-Wno-fatal','-Wno-BLKSEQ','-Wno-PINCONNECTEMPTY','--top-module','cu71_direct_system_sim','--Mdir',lin(sub/'build'),'-CFLAGS','-O1 -std=c++20','-LDFLAGS','-lz']+['-I'+lin(p)for p in includes]+[lin(p)for p in compiled]+[lin(sub/'tb.cpp')]
 run(label+'-build',args);exe=sub/'build/Vcu71_direct_system_sim';native=r/'experiments/cu66-native-v69';index=native/'index.tsv';key=native/index.read_text().splitlines()[0].split('\t')[2]
 control=run(label+'-control',[lin(exe),'--control',lin(key)],600);assert'SYSTEM_CONTROL_PASS'in control and'early_HUD_drain_rejected=1'in control and'OWNER_CONTROL_SNAPSHOT'in control
 frames=run(label+'-frames',[lin(exe),'--frames',lin(index),'3'],1800);assert'SYSTEM_PASS complete_frames=3'in frames and'total_underruns=0'in frames
 results[label]=dict(control=control,frames=frames)
 for f in[native/'index.tsv',key,*native.glob('*.hpp'),r/'fpga/experiments/cu66-v69/hud-partition/hud_gate.hpp',r/'fpga/experiments/cu66-v70/memory/memory_map.hpp']:
  pins[str(f)]=sha(f)
assert results['parent']==results['candidate'],'cycle-exact native control/failure/fullframe traces differ'
assert all(sha(Path(p))==h for p,h in pins.items());(o/'source-freeze.json').write_text(json.dumps(pins,indent=2)+'\n');(o/'result.json').write_text(json.dumps(dict(status='PASS_ACTUAL_NATIVE_KEY_P_P_CONTROL_FAILURE_AND_ALL_OBSERVED_DIAG_TRACES_BYTE_IDENTICAL',candidate_sha256=sha(d/'cu71_receiver_tagcapture_v001.sv'),parent_sha256=sha(r/'fpga/experiments/cu66-v71/direct-system/board-math-v001/cu71_receiver_direct_math.sv'),native_frames=3,native_HUD_words_per_frame=21120,control_failure='Actual packet parsing, deniedwrites, abortdrain, incompleteHUDtransfer error71 and firstfault/eventring snapshots',comparison='Byteidentical entirecontrolincluding all144diag words+expected_hud_tag onstage/event/error transitions; entire chronologicalKEY/P/P traces inclpixels/canonical/HUD goldenchecks',hardware=False,timing=False,scope='Actualselectedvalidpipe owner/system/qualifiedDRAMpinmodel; actualnative semanticHUD. NativeCPUoutsideHDLtime; notSDKphysicalSPI/network orphysicalthroughput.',source_freeze_sha256=sha(o/'source-freeze.json')),indent=2)+'\n');print('PASS_NATIVE_OWNER_TRACES',sha(o/'result.json'))
