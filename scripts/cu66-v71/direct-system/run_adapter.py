"""Source-frozen native ownership-adapter control checks; no simulated SDRAM claim."""
from pathlib import Path
import hashlib,json,shlex,subprocess,time
r=Path(__file__).resolve().parents[3];d=r/'fpga/experiments/cu66-v71/direct-system';o=d/'evidence/adapter01';o.mkdir(parents=True,exist_ok=False);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();lin=lambda p:'/mnt/'+p.drive[0].lower()+p.as_posix()[2:];src=d/'cu71_direct_prepare_adapter.sv';tb=d/'tb_prepare_adapter.cpp';pins={str(p.relative_to(r)):sha(p)for p in [src,tb]}
for p in [src,tb]:(o/p.name).write_bytes(p.read_bytes())
b='/tmp/dy71-adapter-'+str(time.time_ns());cmd=['wsl','-d','MRS-HDL-Research','--','bash','-lc','source /opt/gamebub-openxc7-20261021/oss-cad-suite/environment; '+shlex.join(['verilator','--cc','--exe','--build','-j','2','--Wall','--top-module',src.stem,'--Mdir',b,'-CFLAGS','-O2 -std=c++17',lin(o/src.name),lin(o/tb.name)])+' && '+b+'/V'+src.stem];start=time.monotonic();q=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True);(o/'executed.log').write_text(q.stdout)
for n,h in pins.items():assert sha(r/n)==h
(o/'execution.json').write_text(json.dumps({'command':cmd,'returncode':q.returncode,'seconds':time.monotonic()-start,'source_pins':pins,'hardware':False,'scope':'Syntheticpublicfencecontrol;doesnotproverealowner/backendintegration'},indent=2)+'\n');print(q.stdout[-2000:]);assert q.returncode==0 and 'DY71_PREPARE_ADAPTER_PASS' in q.stdout
(o/'result.json').write_text(json.dumps({'status':'PASS_DY71_PREPARE_ADAPTER_CONTROLS','source_pins':pins,'log_sha256':sha(o/'executed.log'),'hardware':False},indent=2)+'\n')
