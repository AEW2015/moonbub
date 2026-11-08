"""Bounded offline STB1 KEY/P full selected RTL/SDRAM/native-HUD functional replay."""
from pathlib import Path
import ctypes as C,hashlib,json,os,signal,struct,subprocess,sys,time,zlib
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P.parent/'tools'))
from batch_driver_oracle import BatchDriver
ORACLE=Path('/mnt/c/moon/maintenance/v45-sequence/qualification')
DELAY_US=200000

def require(ok,msg):
 if not ok:raise RuntimeError(msg)

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def windows_path(s):return Path(s.replace('C:\\','/mnt/c/').replace('C:/','/mnt/c/').replace('\\','/'))

class Link:
 def __init__(self):
  self.stderr=(P/'rtl-stderr.log').open('xb');self.p=subprocess.Popen([str(P/'build/Vdy71_platform_sim'),'8'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=self.stderr);self.seq=0;self.now=0;self.calls=0;self.opcounts={}
 def request(self,op,address=0,value=0):
  self.seq+=1;self.calls+=1;self.opcounts[op]=self.opcounts.get(op,0)+1
  self.p.stdin.write(struct.pack('<5I',0x43535231,self.seq,op,address,value));self.p.stdin.flush();b=self.p.stdout.read(24)
  require(len(b)==24,'RTL RPC closed unexpectedly')
  magic,seq,status,data,lo,hi=struct.unpack('<6I',b);require((magic,seq,status)==(0x43535231,self.seq,0),'RTL RPC reply mismatch');self.now=lo|(hi<<32);return data
 def advance_us(self,us):
  cycles=us*100
  while cycles:
   n=min(cycles,1000000);self.request(3,n);cycles-=n
 def stop(self,graceful=False):
  if self.p.poll() is None:
   if graceful:self.request(0);self.p.wait(timeout=30)
   else:
    self.p.terminate()
    try:self.p.wait(timeout=10)
    except subprocess.TimeoutExpired:self.p.kill();self.p.wait(timeout=10)
  self.stderr.close()

class Native:
 def __init__(self):
  self.path=(P/'native/libhud.so').resolve();self.lib=C.CDLL(str(self.path))
  self.lib.v34_hud_create.argtypes=[C.c_size_t];self.lib.v34_hud_create.restype=C.c_void_p
  self.lib.v34_hud_destroy.argtypes=[C.c_void_p]
  self.lib.v34_hud_transact.argtypes=[C.c_void_p,C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)];self.lib.v34_hud_transact.restype=C.c_int
  self.lib.v34_hud_stats.argtypes=[C.c_void_p,C.POINTER(C.c_size_t)];self.lib.v34_hud_stats.restype=C.c_int
  self.p=self.lib.v34_hud_create(98304);require(bool(self.p),'native endpoint allocation');self.calls=0
 def call(self,op,g,f,r,arg=0,payload=b''):
  wire=b'HC70'+struct.pack('<BBHIQIII',1,op,0,len(payload),g,f,r,arg)+payload;wire+=struct.pack('<I',zlib.crc32(wire));src=C.create_string_buffer(wire);out=C.create_string_buffer(1060);n=C.c_size_t();self.calls+=1
  rc=self.lib.v34_hud_transact(self.p,src,len(wire),out,len(out),C.byref(n));require(rc==0 and 36<=n.value<=len(out),'native FFI failure')
  reply=out.raw[:n.value];require(reply[:4]==b'HR70' and struct.unpack_from('<I',reply,len(reply)-4)[0]==zlib.crc32(reply[:-4]),'native reply framing/CRC')
  version,rop,res,length,rg,rf,rr,result=struct.unpack_from('<BBHIQIII',reply,4)
  require((version,rop,res,length+36,rg,rf,rr,result)==(1,op,0,len(reply),g,f,r,0),'native rejected/mismatched request '+str((op,g,f,r,result)))
  return reply[32:-4]
 def stats(self):
  a=(C.c_size_t*6)();require(self.lib.v34_hud_stats(self.p,a)==0,'native stats');return list(a)
 def close(self):
  if self.p:self.lib.v34_hud_destroy(self.p);self.p=None

class Bus:
 def __init__(self,link):self.l=link;self.seq=0;self.id=None;self.fields=[None]*12;self.commands={};self.alias_words=0
 def read(self,o):return self.l.request(1,o)
 def write(self,o,v):
  if 0xc00<=o<=0xffc:self.alias_words+=1
  self.l.request(2,o,v)
 def read_words(self,o,n):return[self.read(o+4*i)for i in range(n)]
 def write_words(self,o,words):
  for i,v in enumerate(words):self.write(o+4*i,v)
 def command(self,op,args=(0,0,0,0),tag=bytes(16)):
  g,f,r=self.id;require(self.read(0xc)&1,'command not idle');values=[g&0xffffffff,g>>32,f,r,*args,*struct.unpack('>4I',tag)]
  for i,v in enumerate(values):
   if self.fields[i]!=v:self.write(0x40+4*i,v);self.fields[i]=v
  self.seq+=1;self.write_words(0x20,[self.seq,op]);self.commands[op]=self.commands.get(op,0)+1;deadline=self.l.now+250000
  while self.l.now<=deadline:
   ack,status,data=self.read_words(0x28,3)
   if ack==self.seq:
    if status==0:return data
    require(status==1,'mailbox rejection '+str((op,status)))
   else:require(ack<self.seq,'mailbox sequence ahead')
   self.l.request(3,1000)
  raise RuntimeError('mailbox timeout '+str(op))
 def begin_packet(self,g,n,crc):require(self.id[0]==g,'generation mismatch');self.command(1,[n,crc,0,0])
 def seal_packet(self,g,crc):require(self.id[0]==g,'generation mismatch');self.command(2,[0,crc,0,0])
 def owner(self):
  w=self.read(0x350);return bool(w&1),(w>>1)&255,(w>>9)&255
 def wait_hud(self,g,f,r,packet):
  deadline=self.l.now+1000000
  while not self.read(0xc)&32:
   require(not self.owner()[2],'owner error while awaiting HUD');require(self.l.now<deadline,'HUD request deadline');self.l.request(3,1000)
  ticket=self.read(0x300);lo,hi,fid,ref,span,flags=self.read_words(0x304,6);tag=b''.join(struct.pack('>I',v)for v in self.read_words(0x31c,4))
  offset=span&65535;length=span>>16;bank=flags&3
  require(ticket and ticket==self.read(0x300),'unstable HUD ticket')
  require((lo|(hi<<32),fid,ref)==(g,f,r),'typed HUD identity')
  require(offset==76+struct.unpack_from('<I',packet,68)[0] and length==struct.unpack_from('<I',packet,72)[0] and bank<3 and bool(flags&4)==bool(packet[5]&1),'HUD metadata mismatch')
  hu=packet[offset:offset+length];require(tag==hu[38:54],'FPGA HUD tag mismatch');return ticket,bank,tag,hu
 def check_bulk(self,ticket,off,n,read):
  flags=self.read(0x608)
  require(flags&19==0 and bool(flags&8)==read,'HBU flags invalid')
  require(self.read(0x610)==n and self.read(0x614)==((n<<16)|off) and self.read(0x618)==ticket,'HBU result identity/span mismatch')

def service_hud(bus,native,packet,ordinal):
 g,f,r=bus.id;ticket,bank,tag,hu=bus.wait_hud(g,f,r,packet);begin=bus.l.now;host=time.monotonic_ns();reply=native.call(1,g,f,r,int(bool(packet[5]&1)),hu);host_us=(time.monotonic_ns()-host)//1000
 # Explicit modeled target service wait. The host native callback is not a CPU throughput model.
 bus.l.advance_us(DELAY_US)
 require(len(reply)==72 and reply[0]==1 and reply[1]&5==5 and struct.unpack_from('<I',reply,4)[0]==21120 and reply[8:16]==struct.pack('<Q',g) and struct.unpack_from('<II',reply,16)==(f,r) and reply[24:40]==tag,'native candidate mismatch')
 bus.command(16,[1,21120,0,0],tag);written=verified=0
 for mode in [0,1]:
  for off in range(0,21120,256):
   n=min(256,21120-off);expected=native.call(3,g,f,r,0,struct.pack('<II',off,n));require(len(expected)==n*2,'native READ length')
   bus.command(22,[off,n,mode,0])
   if not mode:
    padded=expected+bytes((-len(expected))%4);bus.write_words(0x400,struct.unpack('<'+'I'*(len(padded)//4),padded))
   require(bus.command(23,[off,n,mode,0])==n,'real HBU completion count');bus.check_bulk(ticket,off,n,bool(mode))
   if mode:
    actual=b''.join(struct.pack('<I',v)for v in bus.read_words(0x400,(n+1)//2))[:len(expected)]
    require(actual==expected,'actual HUD SDRAM readback mismatch');verified+=n
   else:written+=n
 require(written==verified==21120,'HUD comparisons incomplete')
 native.call(4,g,f,r,1,struct.pack('<I',21120)+tag);bus.command(19,[1,21120,bank,0],tag)
 deadline=bus.l.now+1000000;soft_ack=False
 while bus.l.now<deadline:
  if bus.read(0xc)&64:
   st=bus.read(0x330);op=bus.read(0x334);lo,hi,fid,ref=bus.read_words(0x338,4)
   require(st and st==bus.read(0x330) and op==5 and (lo|(hi<<32),fid,ref)==(g,f,r),'actual software request identity')
   committed=native.call(5,g,f,r);require(committed[0]==3 and committed[1]&28==16 and committed[40:48]==struct.pack('<Q',g) and struct.unpack_from('<II',committed,48)==(f,r) and committed[56:72]==tag,'actual native commit rejected')
   bus.command(20,[op,1,0,0]);soft_ack=True
  busy,stage,reason=bus.owner();require(reason==0,'FPGA owner fault')
  if not busy and bus.read(0xc)==1 and bus.read(0x358)==ordinal+1:break
  bus.l.request(3,1000)
 else:raise RuntimeError('presentation deadline')
 require(soft_ack,'no real software commit/ACK occurred')
 require(bus.read(0x354)==ordinal+1 and bus.read(0x35c)==0 and bus.read(0x360)==0,'FPGA final counters')
 canonical_tag=bytearray(16)
 for i in range(4):bus.write(0x200,0x98+4*i);canonical_tag[(3-i)*4:(4-i)*4]=struct.pack('>I',bus.read(0x204))
 require(canonical_tag==packet[52:68],'canonical hardware tag mismatch')
 front=bus.l.request(6,ordinal);print(f'ACTUAL_FRAME_PRESENTED frame={ordinal} bank={front}',flush=True)
 return {'frame':f,'reference':r,'generation':g,'HUD_bank':bank,'HUD_ticket':ticket,'written_words':written,'compared_words':verified,'prepare_model_start_us':begin,'prepare_model_delay_us':DELAY_US,'native_host_callback_us':host_us,'presentation_model_us':bus.l.now,'front_bank':front}

def main():
 start=time.monotonic();binding=json.loads((P/'source-binding.json').read_text())
 for f,h in binding['files_sha256'].items():require(sha(windows_path(f))==h,'bound source drift: '+f)
 link=native=None
 try:
  link=Link();native=Native();bus=Bus(link);batch=BatchDriver(bus,max_polls=512);frames=[]
  print('ACTUAL_NATIVE_MODULE',native.path,sha(native.path),flush=True)
  for i in range(2):
   packet=(ORACLE/f'frame{i}.cu66').read_bytes();fid,ref=struct.unpack_from('<II',packet,8);bus.id=(i+1,fid,ref)
   require(fid==i and ref==(0xffffffff if i==0 else i-1),'fixture chain')
   receipt=batch.stage(packet,i+1);print('ACTUAL_STB1_STAGED',i,json.dumps(receipt),flush=True);bus.command(3)
   frames.append(service_hud(bus,native,packet,i))
  counts=[bus.read(o)for o in [0x354,0x358,0x35c,0x360,0x110]];require(counts==[2,2,0,0,0],'final exact counters')
  stats=[link.request(4,i)for i in range(4)];require(all(v>0 for v in stats[:3]) and stats[3]==0,'SDRAM model activity/refresh/underrun gate')
  result={'status':'PASS_STB1_KEY_P_SELECTED_SYSTEM_NATIVE_HUD_PENDING_PIXEL_COMPARE','frames':frames,'counts':counts,'HUD_words_written_compared':42240,'native_stats':native.stats(),'native_calls':native.calls,'native_library_sha256':sha(native.path),'model_memory_reads_writes_refresh_underruns':stats,'model_us':link.now,'RPC_calls':link.calls,'commands':bus.commands,'alias_u32_writes':bus.alias_words,'wall_seconds':time.monotonic()-start,'modeled_prepare_delay_us_per_frame':DELAY_US,'target_CPU_throughput':'NOT_MEASURED','physical_SPI_CDC_PLL':'NOT_IN_THIS_FULL_SYSTEM_HARNESS_SEPARATE_PIN_GATE','scanout_capture_adds_interframe_delay':True}
  link.stop(True);require(link.p.returncode==0,'RTL server exit failure');(P/'native-result.json').write_text(json.dumps(result,indent=2));print('STB1_KEY_P_SYSTEM_PASS',json.dumps(counts),flush=True)
 except Exception as exc:
  (P/'failure.json').write_text(json.dumps({'error':str(exc),'wall_seconds':time.monotonic()-start,'model_us':link.now if link else None},indent=2));raise
 finally:
  if link:link.stop()
  if native:native.close()

if __name__=='__main__':
 signal.signal(signal.SIGALRM,lambda *a:(_ for _ in ()).throw(TimeoutError('integration wall watchdog')));signal.alarm(5400);main()
