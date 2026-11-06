from pathlib import Path
import hashlib,json,re
r=Path(__file__).resolve().parents[4];d=r/'fpga/experiments/cu66-v71/direct-system/validpipe-local-v001';c=d/'evidence/control01';n=d/'evidence/v36-native01';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not(d/'qualification-v001.json').exists()
cr=json.loads((c/'result.json').read_text());nr=json.loads((n/'result.json').read_text());assert cr['status']=='PASS_ACTUAL_DY71_LOCAL_CSR_STAGING_ABORT_AND_SDRAM_HUD_READBACK';assert nr['status']=='PASS_ACTUAL_V36_DY71_LOCAL_CORE_NATIVE_HU_REAL_CSR_SDRAM_KEY_P'
for evidence in(c,n):assert all(x['returncode']==0 for x in json.loads((evidence/'execution.json').read_text()))
f=json.loads((c/'source-freeze.json').read_text())
for name,h in f['originals'].items():assert sha(Path(name))==h,name
for k in('compiled','headers'):
 for name,h in f[k].items():assert sha(c/name)==h,name
nf=json.loads((n/'source-freeze.json').read_text())
for name,h in nf['bindings'].items():assert sha(Path(name))==h,name
report=nr['report'];stats=re.search(r'PLATFORM_STATS reads=(\d+) writes=(\d+) refreshes=(\d+) virtual_us=(\d+) RPC_calls=(\d+)',report);assert stats
stats=dict(zip(('reads','writes','refreshes','virtual_us','RPC_calls'),map(int,stats.groups())))
assert 'accepted: 2, presented: 2, rejected: 0, underruns: 0'in report and 'HUD_words_written=42240 HUD_words_verified=42240'in report
summary='\n\n## Completed native integration\n\nActual frozen v36/native KEY and P completed: accepted/presented 2/2, rejected and\nLCD underruns 0; all 42,240 HUD words written and independently read back through\nactual SDRAM/CSR responses. Actual native PREPARE/COMMIT completed.\nVirtual RTL elapsed '+str(stats['virtual_us'])+' us and '+str(stats['RPC_calls'])+' scalar RPC calls are not ESP32 performance.\nThe completed result and exact source/model/binary bindings are retained in\n`evidence/v36-native01`; qualification-v001.json records the explicit selected\nSYNCsafe/validpipe plus safe control/stager binding. No hardware or physical timing gate\nis added by this functional proof.\n'
p=d/'README.md';p.write_text(p.read_text()+summary,newline='\n')
artifacts={}
for evidence in(c,n):
 for file in evidence.rglob('*'):
  if file.is_file():artifacts[str(file)]=sha(file)
for file in d.glob('*'):
 if file.is_file():artifacts[str(file)]=sha(file)
for file in(r/'scripts/cu66-v71/direct-system/validpipe-local').glob('*.py'):artifacts[str(file)]=sha(file)
for file in[r/'fpga/experiments/cu66-v71/direct-system/syncsafe-math-v002/board-source-v005/selection.json',r/'fpga/experiments/cu66-v71/staging-timing/safety-v002/qualification-v001.json']:artifacts[str(file)]=sha(file)
q=dict(status='PASS_ACTUAL_V36_NATIVE_SAFE_DY71_CSR_STAGER_SYNCsafe_VALIDPIPE_KEY_P',profile=dict(magic='44593731',ABI='10000',capabilities='0f'),selected_system_manifest_sha256=sha(r/'fpga/experiments/cu66-v71/direct-system/validpipe-v003/sources.json'),safe_control_sha256=sha(r/'fpga/experiments/cu66-v71/staging-timing/safety-v002/dy71_local_control_safe.sv'),safe_stager_sha256=sha(r/'fpga/experiments/cu66-v71/staging-timing/safety-v002/cu71_packet_staging_safe.sv'),selected_board_manifest_sha256=sha(r/'fpga/experiments/cu66-v71/direct-system/syncsafe-math-v002/board-source-v005/selection.json'),wrapper_sha256=sha(d/'dy71_platform_sim.sv'),model_sha256=sha(d/'model-verilator.sv'),control_checks=83,frames=2,accepted=2,presented=2,rejected=0,lcd_underruns=0,HUD_words_written=42240,HUD_words_verified=42240,model_stats=stats,virtual_RTL_clocks=stats['virtual_us']*100,virtual_clock_rounding='microsecond elapsed is truncated; exact clock count retained in rtl-stderr.log',owner_watchdog_clocks=3000000000,CSR_clocks_per_call=8,native_CPU_outside_HDL_clock=True,physical_SPI=False,hardware=False,board_timing='INCOMPLETE',scope='Actual frozen v36 Rust and nativeHU endpoint, explicitly selected SYNCsafe/validpipe/PIPE/grouped owner, actual safe typedCSR/stager, original arbiter, qualified SDRAM pin model. Native CPU wall time, target FreeRTOS, physicalSPI/CDC/vendorPLL/board behavior not modeled. No30fpsorhardwareclaim.',artifacts=artifacts)
q['virtual_RTL_clocks']=int(re.search(r'clocks=(\d+)',(n/'rtl-stderr.log').read_text().split('PLATFORM_SERVER_COMPLETE')[-1]).group(1))
(d/'qualification-v001.json').write_text(json.dumps(q,indent=2)+'\n')
entries=[];empty=[]
for name,h in artifacts.items():
 f=Path(name);assert f.is_file()and sha(f)==h
 if not f.stat().st_size:empty.append(name);continue
 entries.append(dict(role='rtl'if f.suffix=='.sv'else'rebuild'if f.suffix=='.py'else'evidence',path=name,sha256=h))
entries.append(dict(role='qualification',path=str(d/'qualification-v001.json'),sha256=sha(d/'qualification-v001.json')))
m=dict(overall='INCOMPLETE',scope='Actual native/RTL functional integration gates pass; board physical timing and hardware remain incomplete',artifacts=entries,expected_empty_success_logs=empty,checks=dict(actual_native_integration=dict(status='pass',evidence=str(n/'result.json')),source_hash_integrity=dict(status='pass',evidence=str(n/'source-freeze.json')),actual_control_regression=dict(status='pass',evidence=str(c/'result.json')),board_timing=dict(status='incomplete',evidence=str(d/'qualification-v001.json'))))
for e in entries:assert Path(e['path']).stat().st_size>0 and sha(Path(e['path']))==e['sha256']
(d/'manifest-v001.json').write_text(json.dumps(m,indent=2)+'\n');print(json.dumps(dict(qualification_sha256=sha(d/'qualification-v001.json'),manifest_sha256=sha(d/'manifest-v001.json'),artifacts=len(entries),stats=stats),indent=2))
