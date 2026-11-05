#!/usr/bin/env python3
"""Bounded integrated control/real-memory guard smoke; not full frame qualification."""
import hashlib,json,re,subprocess
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[3];s=json.loads((H/'sources.json').read_text())
fixture=R/'experiments/cu66-native-v69'/((R/'experiments/cu66-native-v69/index.tsv').read_text().splitlines()[0].split('\t')[2])
files=[R/p for p in s['rtl_sources']]+[R/d/n for d,n in [('fpga/experiments/cu66-v70/memory','cu70_memory_map.svh'),('fpga/experiments/cu66-v69/inverse','cu66_quant_rom.svh'),('fpga/experiments/cu66-v69/packet','cu66_profile.svh')]]+[H/'test_control.cpp',H/'sources.json',Path(__file__).resolve(),fixture,R/'experiments/cu66-native-v69/index.tsv',R/'fpga/experiments/cu66-v70/memory/memory_map.hpp']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
pins={str(p.relative_to(R)):sha(p)for p in files};cmds=[]
def run(argv,name,timeout=300):
 with (H/name).open('w')as f:p=subprocess.run(argv,cwd=R,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
 cmds.append(dict(argv=argv,log=name,exit_code=p.returncode,sha256=sha(H/name)))
 assert p.returncode==0,(name,p.returncode)
 return (H/name).read_text()
args=['docker','exec','gamebub-cu66-v69-build','verilator','--cc','--exe','--build','-j','1',*s['verilator_options'],'-DSIMULATION','--top-module','cu72_system_sim','--Mdir','/build/v72-system-control','-CFLAGS','-O2 -std=c++17',*['-I'+str(R/p)for p in s['include_dirs']],*[str(R/p)for p in s['rtl_sources']],str(H/'test_control.cpp')]
run(args,'control-build.log')
log=run(['docker','exec','gamebub-cu66-v69-build','/build/v72-system-control/Vcu72_system_sim',str(fixture)],'control.log')
m=re.search(r'^SYSTEM_CONTROL_PASS (.+)$',log,re.M);assert m and 'FAIL'not in log
v={k:int(n)for k,n in re.findall(r'(\w+)=(\d+)',m[1])};assert v['actual_keys_parsed']==2 and v['completed_HUD_words']==2 and v['denied_writes']==7 and v['abort_drained']==2 and v['early_HUD_drain_rejected']==1 and v['accepted_frames']==0
assert pins=={p:sha(R/p)for p in pins},'sourceschanged'
result=dict(status='PASS',scope='integratedactualpacketmetadata/realmemoryHUDguards+partialtransactionabort/earlytransferclaimrejection;noacceptedcompleteframe/displayclaim',source_sha256=pins,commands=cmds,counts=v,not_proven=['completeHUDsemanticdecodeandtransfer','fullcanonicalRGBoutputs','successfulglobalcommit','panelcadence30fps','targetFmax/fit'])
(H/'control-results.json').write_text(json.dumps(result,indent=2)+'\n');print('SYSTEM_CONTROL_EVIDENCE_PASS source_stable=true')
