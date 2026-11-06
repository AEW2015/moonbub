from pathlib import Path
import argparse,hashlib,json,re,shlex,shutil,struct,subprocess,time,zlib
r=Path(__file__).resolve().parents[3];d=r/'fpga/experiments/cu66-v71/entropy-headerpipe/review-v001';old=r/'fpga/experiments/cu66-v69/entropy'
p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();o=Path(a.output).resolve();o.mkdir(parents=True,exist_ok=False);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();lin=lambda p:'/mnt/'+p.resolve().drive[0].lower()+p.resolve().as_posix()[2:]
parent=r/'fpga/experiments/cu66-v71/entropy/cu71_ab38_decoder_arithpipe_v4.sv';candidate=r/'fpga/experiments/cu66-v71/entropy-headerpipe/cu71_ab38_decoder_headerpipe_v5.sv';assert sha(parent)=='93b79e7d074aa606b4461d7fcd73069e323739012d66963fa1a0d5fa6633763b';assert sha(candidate)=='8715c9f29c481d8a02bfa3e86eccb57efdea21b3fb1d4cc36110724a85d02893'
pins={str(p):sha(p)for p in[parent,candidate,d/'tb-template.cpp',d/'header_math_miter.sv',d/'math-derivation.json',old/'tb_entropy.cpp',old/'actual.tsv',old/'directed.tsv',Path(__file__)]}
rows=[];expected={};meta={};(o/'fixtures').mkdir()
def control(line,name):
 v=line.split('\t');packet=(old/v[1]).resolve();coeff=(old/v[2]).resolve();pins[str(packet)]=sha(packet);pins[str(coeff)]=sha(coeff);shutil.copy2(packet,o/'fixtures'/(name+'.ab38'));shutil.copy2(coeff,o/'fixtures'/(name+'.zlib'));rows.append(f'{name}\tfixtures/{name}.ab38\tfixtures/{name}.zlib\t'+ '\t'.join(v[3:6])+'\t0');expected[name]=0;return packet,tuple(map(int,v[3:6]))
directed=(old/'directed.tsv').read_text().splitlines();control(directed[0],'good_zero8');control(directed[1],'good_DC12');base,geometry=control((old/'actual.tsv').read_text().splitlines()[1],'actual_mass_effect_plane1');packet=base.read_bytes();n=len(packet);lengths=list(struct.unpack_from('<4I',packet,14));payload=n-46;counter=0
assert packet[:4]==b'AB38'and packet[5]==0 and 46+sum(lengths)==n

def add(name,q,code=None,flip=False,group='header'):
 q=bytearray(q);q[-4:]=struct.pack('<I',zlib.crc32(q[:-4]));
 if flip:q[-1]^=0x80
 f=o/'fixtures'/(name+'.ab38');f.write_bytes(q);rows.append(f'{name}\tfixtures/{name}.ab38\t-\t'+ '\t'.join(map(str,geometry))+'\t1');expected[name]=code;meta[name]=dict(group=group,total_mod32=(46+sum(struct.unpack_from('<4I',q,14)))&0xffffffff,CRC_valid=not flip)
values=[0,1,7,8,9,16,17,31,0x7fffffff,0x80000000,0xfffffff0,0xfffffff8,0xfffffff9,0xfffffffa,0xfffffffe,0xffffffff]
for stream in range(4):
 for value in values:
  if value==lengths[stream]:continue
  q=bytearray(packet);struct.pack_into('<I',q,14+4*stream,value);add(f'len_s{stream}_{value:08x}',q,4,group='length_width_edges')
for i in range(4):
 for j in range(i+1,4):
  for delta in[1,0x7fffffff,0x80000000,0xffffffff]:
   q=bytearray(packet);struct.pack_into('<I',q,14+4*i,(lengths[i]+delta)&0xffffffff);struct.pack_into('<I',q,14+4*j,(lengths[j]-delta)&0xffffffff);add(f'wrap_cancel_{i}_{j}_{delta:08x}',q,None,group='total_wrap_matches')
for k,lens in enumerate([[0xffffffff,1,0,payload],[0x80000000,0x80000000,payload,0],[0xfffffff0,0x10,0,payload],[0,payload,0,0],[9,9,9,(payload-27)&0xffffffff]]):
 q=bytearray(packet);struct.pack_into('<4I',q,14,*lens);add(f'wrap_quad_{k}',q,7 if k==3 else None,group='total_wrap_matches')
for kind in['magic','version','mode','blocks_high','width_high','reserved','blocks_zero']:
 q=bytearray(packet)
 if kind=='magic':q[0]^=1
 elif kind=='version':q[4]=2
 elif kind=='mode':q[5]=2
 elif kind=='blocks_high':struct.pack_into('<I',q,6,0x80000000|geometry[0])
 elif kind=='width_high':struct.pack_into('<H',q,10,0x8000|geometry[1])
 elif kind=='reserved':struct.pack_into('<H',q,12,0x8000)
 elif kind=='blocks_zero':struct.pack_into('<I',q,6,0)
 add('header_'+kind,q,3,group='fixed_header')
 struct.pack_into('<I',q,14,0xfffffffe);add('priority_header_len_'+kind,q,3,group='header_before_length');add('priority_crc_header_len_'+kind,q,2,True,group='CRC_before_header_length')
add('crc_only',packet,2,True,group='CRC_only');q=bytearray(packet);struct.pack_into('<I',q,14,0xfffffffe);add('crc_before_len',q,2,True,group='CRC_before_length')
q=bytearray(packet);q[5]=1;add('raw_mode_length_valid',q,5,group='raw_mode');struct.pack_into('<I',q,14,0xfffffffe);add('length_before_raw_mode',q,4,group='length_before_raw_mode')
q=bytearray(packet);struct.pack_into('<3I',q,30,*([0xffffffff]*3));add('events_max',q,None,group='events_later_validation');struct.pack_into('<I',q,14,0xfffffffe);add('length_before_events',q,4,group='length_before_events')
index=o/'fixtures.tsv';index.write_text('\n'.join(rows)+'\n',newline='\n');(o/'expected.json').write_text(json.dumps(dict(expected_error=expected,metadata=meta,source_packet=str(base),source_packet_sha256=sha(base),geometry=geometry,lengths=lengths,packet_bytes=n),indent=2)+'\n')
for f in(o/'fixtures').iterdir():pins[str(f)]=sha(f)
pins[str(index)]=sha(index);shutil.copy2(d/'header_math_miter.sv',o/'header_math_miter.sv');steps=[]
def run(label,args,timeout=900):
 start=time.monotonic()
 with(o/(label+'.log')).open('wb')as f:q=subprocess.run(args,cwd=o,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
 steps.append(dict(label=label,command=args,returncode=q.returncode,seconds=time.monotonic()-start));(o/'execution.json').write_text(json.dumps(steps,indent=2)+'\n');print(label,q.returncode,flush=True);assert q.returncode==0,(label,o)
 return(o/(label+'.log')).read_text()
def wsl(cmd):return ['wsl.exe','-d','MRS-HDL-Research','--','bash','-lc','source /opt/gamebub-openxc7-20261021/oss-cad-suite/environment && '+cmd]
formal='read_verilog -sv '+lin(o/'header_math_miter.sv')+'; prep -top header_math_miter; alumacc; opt; techmap; opt; sat -prove mismatch 0 -show-inputs -show-outputs'
log=run('all32-sums-prefixes',wsl('yosys -Q -T -p '+shlex.quote(formal)),180);assert'SUCCESS!'in log and'FAIL!'not in log
reports={}
for label,source in [('parent',parent),('candidate',candidate)]:
 sub=o/label;sub.mkdir();shutil.copy2(source,sub/source.name);top=source.stem;tb=(d/'tb-template.cpp').read_text().replace('@TOP@',top);(sub/'tb.cpp').write_text(tb,newline='\n');pins[str(sub/source.name)]=sha(sub/source.name);pins[str(sub/'tb.cpp')]=sha(sub/'tb.cpp')
 cmd=['verilator','--cc','--exe','--build','-j','2','--Wall','-Wno-fatal','--public-flat-rw','--x-initial','unique','--x-assign','unique','--top-module',top,'--Mdir',lin(sub/'build'),'-CFLAGS','-O2 -std=c++17'+(' -DCANDIDATE=1'if label=='candidate'else''),'-LDFLAGS','-lz',lin(sub/source.name),lin(sub/'tb.cpp')]
 run(label+'-build',wsl(shlex.join(cmd)))
 reports[label]={}
 for seed in[7107,7108]:
  text=run(label+'-seed'+str(seed),wsl(shlex.join([lin(sub/'build'/('V'+top)),lin(index),str(seed)])),1200);assert'HEADER_REVIEW_PASS'in text and'HEADER_REVIEW_FAIL'not in text
  data={}
  for line in text.splitlines():
   if not line.startswith('DIFF '):continue
   entry=dict(re.findall(r'(\w+)=(\S+)',line));name=entry.pop('name');entry={k:int(v)for k,v in entry.items()};entry.pop('cycles');data[name]=entry
  assert set(data)==set(expected)
  for name,code in expected.items():
   if code is not None:assert data[name]['error']==code,(label,seed,name,data[name],code)
   elif meta[name]['group']=='total_wrap_matches':assert data[name]['error']!=4,(label,seed,name,'modulo contract changed')
  if label=='candidate':assert all(f'HEADER_DIRECT_RESET_PASS state={state}'in text for state in(54,55))
  reports[label][seed]=data
for seed in[7107,7108]:assert reports['parent'][seed]==reports['candidate'][seed],('differential',seed)
assert all(sha(Path(f))==h for f,h in pins.items())
(o/'source-freeze.json').write_text(json.dumps(dict(originals=pins,parent_sha256=sha(parent),candidate_sha256=sha(candidate),math_source_sha256=sha(d/'header_math_miter.sv'),selected_sources_changed=False),indent=2)+'\n')
(o/'result.json').write_text(json.dumps(dict(status='PASS_INDEPENDENT_HEADER_MOD32_MATH_REAL_PACKET_ERROR_DIFFERENTIAL_AND_NEW_STATE_DIRECT_RESET',cases=len(rows),seeds=[7107,7108],differential_fields=['error','done','tiles','tile_crc','decisions','renorm','reads'],known_expected_error_cases=sum(c is not None for c in expected.values()),wrapped_total_cases=sum(x['group']=='total_wrap_matches'for x in meta.values()),new_state_direct_reset=[54,55],probability_RAM='352bytes retained across direct rst in bothnewstates, randomized initialization and dirty valid history; nozero assumption, not4stateproof',new_private_payload='six32bit regs retained across rst then alternate valid golden retry',priority='CRC02 > fixedheader03 > modular length04; preserves later parser behavior',all32='SAT_EXHAUSTIVE_EXTRACTED_MODULAR_SUMS_PREFIXES_AND_16BIT_PACKET_COMPARISON',scope='Actual original v4 vs frozen candidate v5; additional two headercycles allowed. Private early length/events not asserted equal on reject; no coeff/prob work beforeheader validation. Notallmalformed enumeration, fourstateX equivalence, routedtimingorhardware.',source_freeze_sha256=sha(o/'source-freeze.json'),hardware=False,routed_timing=False,reports=reports),indent=2)+'\n');print(json.dumps(dict(status='PASS_HEADER_INDEPENDENT_REVIEW',cases=len(rows),result_sha256=sha(o/'result.json')),indent=2))
