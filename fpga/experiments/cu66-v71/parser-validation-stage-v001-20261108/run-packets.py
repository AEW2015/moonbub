from pathlib import Path
import argparse,json,hashlib,subprocess,os,time,re,zlib
p=Path(__file__).resolve().parent
a=argparse.ArgumentParser();a.add_argument('--out',required=True);args=a.parse_args()
e=p/'evidence'/args.out;e.mkdir(parents=True,exist_ok=False)
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
bind=json.loads((p/'source-bindings.json').read_text())
for label in ['control','candidate']:assert sha(p/label/'cu71_packet_rxstage_v001.sv')==bind[label+'_sha256']
packets=[(p/f'fixtures/packet{i}.cu66').read_bytes()for i in range(3)]
cases=[]
def add(name,b,want=0,stall=False,last=False):
    cases.append(dict(name=name,bytes=bytes(b),want=want,stall=stall,last=last))
def repair(b):
    b=bytearray(b);n=int.from_bytes(b[68:72],'little');off=76+n
    b[off-4:off]=zlib.crc32(b[76:off-4]).to_bytes(4,'little')
    b[-8:-4]=zlib.crc32(b[off:-8]).to_bytes(4,'little');b[-4:]=zlib.crc32(b[:-4]).to_bytes(4,'little');return b
for stall in [False,True]:
    for i,b in enumerate(packets):add(f'fixture{i}-stall{int(stall)}',b,stall=stall)
for at in [0,4,5,6,10,14,18,20,22,23,24,39]:
    b=bytearray(packets[0]);b[76+at]^=1
    if at==22:b[76+at]=17
    add(f'bad-inner-header-{at}',repair(b),6,True)
for plane in range(3):
    for value in [0,46,49152,49153,65535,65536,0xFFFFFFFF,0x80000000]:
        b=bytearray(packets[0]);off=76+48+4*plane;b[off:off+4]=value.to_bytes(4,'little')
        add(f'bad-length-p{plane}-{value}',repair(b),7,bool(plane%2))
for header in [0,24]:
    b=bytearray(packets[0]);b[76+header]^=1;b[124:128]=(0xFFFFFFFF).to_bytes(4,'little');add(f'priority6-before7-{header}',repair(b),6,True)
for at,value in [(40,337),(44,1)]:
    b=bytearray(packets[0]);b[76+at:80+at]=value.to_bytes(4,'little');add(f'inner-grammar-length-{at}',repair(b),7,True)
b=bytearray(packets[0]);b[136]=0xC0;add('bad-qmap',repair(b),8,True)
b=bytearray(packets[1]);b[474]=7;add('bad-vector',repair(b),9,True)
b=bytearray(packets[0]);b[474]=7;add('bad-dispatch',repair(b),10,True)
b=bytearray(packets[0]);off=76+int.from_bytes(b[68:72],'little');b[off]=0;add('bad-hud-schema',repair(b),11,True)
b=bytearray(packets[0]);b[-1]^=1;add('outer-crc',b,13,True)
b=bytearray(packets[0]);off=76+int.from_bytes(b[68:72],'little');b[off-1]^=1;b[-4:]=zlib.crc32(b[:-4]).to_bytes(4,'little');add('inner-crc',b,14,True)
b=bytearray(packets[0]);b[-8]^=1;b[-4:]=zlib.crc32(b[:-4]).to_bytes(4,'little');add('hud-crc',b,15,True)
add('stale-frame-cfg',packets[1],3,True,True)
# Good snapshots after failures, without a reset between cases.
for i,b in enumerate(packets):add(f'fresh-owner-after-errors-{i}',b,stall=True)
lines=[];metadata=[]
for i,c in enumerate(cases):
    b=c.pop('bytes');f=e/f'packet-{i:03}.hex';f.write_text('\n'.join(f'{v:02x}'for v in b)+'\n')
    refid=int.from_bytes(b[12:16],'little');tag=b[36:52].hex();fid=int.from_bytes(b[8:12],'little')
    lines.append(f'run_case({i},"{f.as_posix()}",{len(b)},{int(c["stall"])},{int(not (b[5]&1))},32\'h{refid:08x},128\'h{tag},{c["want"]},{int(c["last"])},32\'h{fid:08x});')
    metadata.append(dict(id=i,**c,packet_sha256=hashlib.sha256(b).hexdigest(),length=len(b),hex_sha256=sha(f)))
(e/'packet-cases.svh').write_text('\n'.join(lines)+'\n');(e/'cases.json').write_text(json.dumps(metadata,indent=2)+'\n')
env=dict(os.environ,PATH='C:/msys64/ucrt64/bin;'+os.environ['PATH'],TEMP='C:/moon/tmp',TMP='C:/moon/tmp');env.pop('NoDefaultCurrentDirectoryInExePath',None)
records=[];observations={}
for label in ['control','candidate']:
    compile=['C:/msys64/ucrt64/bin/iverilog.exe','-g2012','-I',str(p/'fixtures'),'-I',str(e),'-s','tb_packets','-o',str(e/(label+'.vvp')),str(p/label/'cu71_packet_rxstage_v001.sv'),str(p/'tests/tb_packets.sv')]
    for phase,cmd in [('compile',compile),('run',['C:/msys64/ucrt64/bin/vvp.exe',str(e/(label+'.vvp'))])]:
        t=time.monotonic();r=subprocess.run(cmd,cwd=e,env=env,capture_output=True,text=True,timeout=360)
        (e/f'{label}-{phase}.log').write_text(r.stdout+r.stderr);records.append(dict(label=label,phase=phase,command=cmd,returncode=r.returncode,seconds=time.monotonic()-t));(e/'execution.json').write_text(json.dumps(records,indent=2)+'\n');print(label,phase,r.returncode,flush=True)
        if r.returncode:print(r.stdout[-2500:]+r.stderr[-1500:]);raise SystemExit(1)
    observations[label]=[dict(id=int(m[0]),code=int(m[1]),reads=int(m[2]),req=m[3],meta=m[4],qmap=m[5],cycles=int(m[6]))for m in re.findall(r'CASE (\d+) code=(\d+) reads=(\d+) req=(\w+) meta=(\w+) qmap=(\w+) cycles=(\d+)',(e/f'{label}-run.log').read_text())]
assert len(observations['control'])==len(cases)==len(observations['candidate'])
for old,new,c in zip(observations['control'],observations['candidate'],metadata):
    assert {k:v for k,v in old.items()if k!='cycles'}=={k:v for k,v in new.items()if k!='cycles'},(c,old,new)
    if not c['stall']:assert new['cycles']-old['cycles']==(0 if c['want']==6 else 1),(c,old,new)
result={'status':'PASS','case_count':len(cases),'metadata_qmap_readstream_error_equivalent':True,'no_stall_latency_extra_cycles':1,'stall_cycles_may_change_with_handshake_alignment':True,'observations':observations,'cases':metadata,'scope':'two exact parser sources, byte request/response RTL; no full-system, native CPU, radio or hardware'}
(e/'result.json').write_text(json.dumps(result,indent=2)+'\n');(e/'bindings.json').write_text(json.dumps({str(f):sha(f)for f in[Path(__file__),p/'tests/tb_packets.sv',p/'source-bindings.json',p/'control/cu71_packet_rxstage_v001.sv',p/'candidate/cu71_packet_rxstage_v001.sv',p/'fixtures/cu66_profile.svh',e/'packet-cases.svh',e/'cases.json']},indent=2)+'\n');print('PACKET_DIFFERENTIAL_PASS',len(cases),flush=True)
