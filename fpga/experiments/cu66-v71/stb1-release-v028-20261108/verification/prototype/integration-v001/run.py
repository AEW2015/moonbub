from pathlib import Path
import json,hashlib,subprocess,shlex,time
p=Path('C:/moon/dev/experiments/staging-burst-v1-20261108/integration-v001');sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();b=json.loads((p/'source-binding.json').read_text())
for f in [p/'service_pair.py',p/'native/libhud.so',p.parent/'tools/batch_driver_oracle.py']+[f for f in (p/'native').glob('*')if f.is_file()]:b['files_sha256'][str(f)]=sha(f)
b['native_origin']='C:/moon/publish/firmware/experiments/v48-dy71-selftest-control-20261107/native';b['native_source_copies_match_origin']=all(sha(f)==sha(Path(b['native_origin'])/f.name)for f in (p/'native').glob('*')if f.suffix in ['.h','.hpp','.cpp']);assert b['native_source_copies_match_origin'];b['service_assumptions']={'prepare_delay_us':200000,'native_callback_virtual_time':'paused; explicit200ms advance then services SDRAM','RPC_CSR_cycles':8,'core_MHz':100,'SDRAM_read_clock_rise_ps':2625,'pixel_half_period_ps':17029,'POWERUP_CYCLES':20,'REFRESH_CYCLES':750,'watchdog_cycles':3000000000,'native_arena_cap':98304,'physical_heap_reserve_model':'not configured; host allocation model'}
(p/'source-binding.json').write_text(json.dumps(b,indent=2))
w=lambda f:Path(f).as_posix().replace('C:/','/mnt/c/');command=['wsl.exe','-d','MRS-HDL-Research','--','bash','-lc','source /opt/gamebub-openxc7-20261021/oss-cad-suite/environment && '+shlex.join(['python3',w(p/'service_pair.py')])]
(p/'run-command.json').write_text(json.dumps(command,indent=2));start=time.monotonic()
with(p/'native-run.log').open('x')as log:r=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,timeout=6000)
(p/'run-result.json').write_text(json.dumps({'returncode':r.returncode,'seconds':time.monotonic()-start,'command':command},indent=2));print('integration replay',r.returncode,flush=True)
