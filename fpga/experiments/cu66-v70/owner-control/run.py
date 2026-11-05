#!/usr/bin/env python3
import hashlib,importlib.util,json,re,subprocess
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[3]
spec=importlib.util.spec_from_file_location('receiver_repro',R/'scripts/cu66-v70/run_receiver.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
files=[R/p for p in mod.REL]+[R/'fpga/experiments/cu66-v69/inverse/cu66_quant_rom.svh',R/'fpga/experiments/cu66-v69/packet/cu66_profile.svh',H/'test_owner.cpp',Path(__file__).resolve(),R/'scripts/cu66-v70/run_receiver.py']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();pins={str(p.relative_to(R)):sha(p)for p in files};commands=[]
def run(argv,name):
 with (H/name).open('w')as f:p=subprocess.run(argv,cwd=R,stdout=f,stderr=subprocess.STDOUT,timeout=300)
 commands.append(dict(argv=argv,log=name,exit_code=p.returncode,sha256=sha(H/name)));assert p.returncode==0,(name,p.returncode)
 return (H/name).read_text()
args=['docker','exec','gamebub-cu66-v69-build','verilator','--cc','--exe','--build','-j','1','--Wall','-Wno-PINCONNECTEMPTY','--top-module','cu70_receiver','-GWATCHDOG_CYCLES=512','--Mdir','/build/v70-owner-control','-CFLAGS','-O2 -std=c++17','-I'+str(R/'fpga/experiments/cu66-v69/inverse'),'-I'+str(R/'fpga/experiments/cu66-v69/packet'),*[str(R/p)for p in mod.REL],str(H/'test_owner.cpp')]
run(args,'build.log');log=run(['docker','exec','gamebub-cu66-v69-build','/build/v70-owner-control/Vcu70_receiver'],'run.log')
m=re.search(r'^OWNER_CONTROL_PASS (.+)$',log,re.M);assert m and 'FAIL'not in log
v={k:int(n)for k,n in re.findall(r'(\w+)=(\d+)',m[1])};assert v['watchdog_faults']==1 and v['stale_total']==10 and v['accepted_frames']==v['presented_frames']==0 and v['clocks']<2000
assert pins=={p:sha(R/p)for p in pins},'DUT/sourcechangedduringtest'
(H/'results.json').write_text(json.dumps(dict(status='PASS',scope='receiverownernegative/watchdog/drain/diagnosticscontrolonly;notfullframerun',source_sha256=pins,commands=commands,counts=v),indent=2)+'\n');print('OWNER_CONTROL_EVIDENCE_PASS source_stable=true')
