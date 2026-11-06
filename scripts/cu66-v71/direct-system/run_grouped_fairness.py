"""Synthetic-controller policy/fairness test; actual pin/abort proof is separate."""
from pathlib import Path
import hashlib,json,shlex,subprocess,time
r=Path(__file__).resolve().parents[3];d=r/'fpga/experiments/cu66-v71/direct-system/grouped-v001';o=d/'evidence/fairness01';o.mkdir(parents=True,exist_ok=False);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();lin=lambda p:'/mnt/'+p.drive[0].lower()+p.as_posix()[2:];src=d/'source/cu71_word_bridge_direct.sv';tb=d/'tb_grouped.cpp';mapfile=d/'source/cu70_memory_map.svh';pins={str(p.relative_to(r)):sha(p)for p in [src,tb,mapfile]}
for p in [src,tb,mapfile]:(o/p.name).write_bytes(p.read_bytes())
b='/tmp/dy71-grouped-'+str(time.time_ns());args=['verilator','--cc','--exe','--build','-j','2','--Wall','-Wno-fatal','--top-module',src.stem,'--Mdir',b,'-I'+lin(o),'-CFLAGS','-O2 -std=c++17',lin(o/src.name),lin(o/tb.name)];cmd=['wsl','-d','MRS-HDL-Research','--','bash','-lc','source /opt/gamebub-openxc7-20261021/oss-cad-suite/environment; '+shlex.join(args)+' && '+b+'/V'+src.stem];start=time.monotonic();q=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True);(o/'executed.log').write_text(q.stdout)
(o/'execution.json').write_text(json.dumps({'command':cmd,'returncode':q.returncode,'seconds':time.monotonic()-start,'source_pins':pins,'scope':'Syntheticcontrolleronlypolicy/dataownership/contendedfairness;notphysicalSDRAMproof','hardware':False},indent=2)+'\n');print(q.stdout[-2000:]);assert q.returncode==0 and 'GROUPED_FAIRNESS_PASS' in q.stdout
for n,h in pins.items():assert sha(r/n)==h
(o/'result.json').write_text(json.dumps({'status':'PASS_GROUPED_CONTINUOUS_QUOTA_LOCALS_AND_RESPONSE_ISOLATION','source_pins':pins,'hardware':False},indent=2)+'\n')
