"""Compare frozen CFG baseline and selected v4 RTL on resealed parameter overflow/errors."""
from pathlib import Path
import hashlib,json,re,struct,subprocess,time,zlib
r=Path(__file__).resolve().parents[3];d=r/'fpga/experiments/cu66-v71/entropy';o=d/'evidence/arith-malformed03';o.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
base=d/'evidence/regression03';candidate=d/'evidence/arith-regression04'
original=r/'fpga/experiments/cu66-v69/entropy/fixtures/9e92a98e088206e1cb56910bb33cdfcae8a78a62d2cb4da2410be192eea7a998.ab38'
packet=original.read_bytes();lengths=struct.unpack_from('<4I',packet,14);rows=[];expected={};pins={str(original.relative_to(r)):sha(original)}
values=[0,1,7,16,17,33,0x7fffffff,0x80000000,0xfffffff0,0xfffffff8,0xfffffff9,0xfffffffa,0xfffffffe,0xffffffff]
for stream in range(4):
 offset=42+sum(lengths[:stream])
 for bits in values:
  for secondary in [False,True]:
   q=bytearray(packet);struct.pack_into('<I',q,offset+2,bits)
   if secondary:q[offset]=255;q[offset+1]=254
   q[-4:]=struct.pack('<I',zlib.crc32(q[:-4]));name=f's{stream}_bits{bits:08x}_multi{int(secondary)}';f=o/(name+'.ab38');f.write_bytes(q)
   rows.append(f'{name}\t{f.name}\t-\t8\t4\t5\t1');expected[name]=8;pins[str(f.relative_to(r))]=sha(f)
 # A valid bit count but invalid k tests lower-priority errors separately.
 q=bytearray(packet);q[offset]=255;q[offset+1]=254;q[-4:]=struct.pack('<I',zlib.crc32(q[:-4]));name=f's{stream}_bad_k_only';f=o/(name+'.ab38');f.write_bytes(q)
 rows.append(f'{name}\t{f.name}\t-\t8\t4\t5\t1');expected[name]=9 if stream==0 else 10;pins[str(f.relative_to(r))]=sha(f)
index=o/'fixtures.tsv';index.write_text('\n'.join(rows)+'\n',newline='\n');pins[str(index.relative_to(r))]=sha(index)
lin=lambda p:'/mnt/'+p.drive[0].lower()+p.as_posix()[2:]
executions=[];results=[];exes=[]
for label,run in zip(['baseline','candidate'],[base,candidate]):
 src=next(run.glob('*.sv'));top=src.stem;sub=o/label;sub.mkdir();(sub/src.name).write_bytes(src.read_bytes());(sub/'tb.cpp').write_bytes((run/'tb.cpp').read_bytes())
 build='/tmp/cu71-malformed-'+label+'-'+str(time.time_ns())
 command=f'source /opt/gamebub-openxc7-20261021/oss-cad-suite/environment; verilator --cc --exe --build -j 2 --Wall --public-flat-rw --top-module {top} --Mdir {build} -CFLAGS "-O2 -std=c++17" -LDFLAGS -lz {lin(sub/src.name)} {lin(sub/"tb.cpp")}'
 cmd=['wsl','-d','MRS-HDL-Research','--','bash','-lc',command];start=time.monotonic();q=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True);(sub/'build.log').write_text(q.stdout);executions.append({'label':label+'_build','command':cmd,'returncode':q.returncode,'seconds':time.monotonic()-start});assert q.returncode==0,q.stdout[-2000:];exes.append(build+'/V'+top)
for label,binary in zip(['baseline','candidate'],exes):
 cmd=['wsl','-d','MRS-HDL-Research','--','bash','-lc',f'source /opt/gamebub-openxc7-20261021/oss-cad-suite/environment; {binary} {lin(index)} 7104 {len(rows)}']
 start=time.monotonic();q=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True);(o/(label+'.log')).write_text(q.stdout)
 executions.append({'label':label,'command':cmd,'returncode':q.returncode,'seconds':time.monotonic()-start});assert q.returncode==0,q.stdout[-2000:]
 errors={name:int(error)for name,error in re.findall(r'CASE_PASS name=(\S+).*? error=(\d+)',q.stdout)};assert errors==expected,(label,errors);results.append(errors)
assert results[0]==results[1]
for run in [base,candidate]:
 for f in run.glob('*.sv'):pins[str(f.relative_to(r))]=sha(f)
 pins[str((run/'execution.json').relative_to(r))]=sha(run/'execution.json')
(o/'result.json').write_text(json.dumps({'status':'PASS_FROZEN_RTL_MALFORMED_ERROR_PRIORITY_DIFFERENTIAL','cases':len(rows),'expected_error08':112,'expected_error09':1,'expected_error0a':3,'executions':executions,'source_pins':pins,'scope':'Resealed real packets, all4streams,32bitbitcountwrapedges withandwithout simultaneousinvalidk; baseline andv4 mustmatch exacterrorcodes. Noexhaustiveallmalformedclaim.','hardware':False},indent=2)+'\n');print('PASS_MALFORMED_PRIORITY',len(rows))
