"""Test registered SHA byte writes with the existing carry-save final sums."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,time
r=Path(__file__).resolve().parents[1]
p=r/'fpga/candidates/cp23-timing-tag-validation-20261105/core/compute/sha256_bytes.sv'
csa=r/'fpga/experiments/sha-csa-finalsum-20261105-v002/sha256_bytes.sv'
o=r/'fpga/experiments/sha-csa-byte-reservation-20261105-v001';o.mkdir(parents=True,exist_ok=False)
s=p.read_text();a=csa.read_text();start=a.index(' // Keep T1 in carry-save');end=a.index(' wire [31:0] wn0=',start)
old=' wire [31:0] an=t1^big0(a)^majority,ac=carry(t1,big0(a),majority);'
assert s.count(old)==1;s=s.replace(old,a[start:end].rstrip())
assert s.count(' wire [31:0] t1=t14+t15;')==1;s=s.replace(' wire [31:0] t1=t14+t15;','')
assert s.count('e<=d+t1;')==1;s=s.replace('e<=d+t1;','e<=en+ec;')
(o/'sha256_bytes.sv').write_text(s,newline='\n')
shutil.copyfile(r/'fpga/experiments/ar03-canonical-tag-20261104/tb_sha.sv',o/'tb_sha.sv')
shutil.copyfile(r/'fpga/candidates/cp23-timing-sha-count-v002-20261105/evidence/sha-suite01/sha-fixtures.hex',o/'sha-fixtures.hex')
env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin'+os.pathsep+env.get('PATH','');rows=[]
for label,cmd in [('compile',['C:/msys64/ucrt64/bin/iverilog.exe','-g2012','-s','tb_sha','-o','test.vvp','sha256_bytes.sv','tb_sha.sv']),('simulation',['C:/msys64/ucrt64/bin/vvp.exe','test.vvp'])]:
 t=time.monotonic()
 with(o/(label+'.log')).open('wb')as f:q=subprocess.run(cmd,cwd=o,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=900)
 rows.append(dict(label=label,command=cmd,returncode=q.returncode,seconds=time.monotonic()-t))
 (o/'execution.json').write_text(json.dumps(rows,indent=2)+'\n');assert q.returncode==0,(o/(label+'.log')).read_text()
log=(o/'simulation.log').read_text();assert 'PASS'in log
(o/'result.json').write_text(json.dumps(dict(status='PASS_DIRECTED_SHA_SUITE_ONLY',output=log,
 source_hashes={n:hashlib.sha256((o/n).read_bytes()).hexdigest()for n in ['sha256_bytes.sv','tb_sha.sv','sha-fixtures.hex']},
 latency_change='One COMP_FLUSH cycle per compressed 64-byte block; ingress/owner/cancel contract preserved',hardware=False),indent=2)+'\n')
print(log[-1000:])
