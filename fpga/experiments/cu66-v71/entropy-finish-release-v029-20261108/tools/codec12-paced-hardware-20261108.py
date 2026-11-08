"""One existing count12 DYN1 session, at most one frame start per2s. No new wire contract."""
from pathlib import Path
import sys,socket,secrets,time,json,hashlib
root=Path('C:/moon/publish/host/dy71-sequence-v3');sys.path.insert(0,str(root))
import sequence_sender as sender
r=Path('C:/moon/dev/evidence/v55-v029-hardware-20261108-run01')
sequence=sender.Sequence(root/'manifest.json',sender.PROFILE,12)
for i in range(12):sequence.read(i)
session=secrets.randbits(64) or 1;dest=('192.168.0.157',5535)
with (r/'sender.jsonl').open('x') as log,socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as sock:
 sock.bind(('192.168.0.33',0));sock.settimeout(.1)
 row={'event':'session','session':session,'source':sock.getsockname(),'destination':dest,'sequence_count':12,'minimum_start_interval_seconds':2,'source_scope':'Original packaged twelve distinct frames, not20seconds of source footage','manifest_sha256':hashlib.sha256((root/'manifest.json').read_bytes()).hexdigest(),'source_pins':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [root/'sequence_sender.py',root/'dyn1_sequence_core.py']},'started_unix_us':time.time_ns()//1000}
 log.write(json.dumps(row)+'\n');log.flush();print(json.dumps(row),flush=True)
 first=None;next_start=None;outcomes=[]
 try:
  for i in range(12):
   if next_start is not None:time.sleep(max(0,next_start-time.monotonic()))
   started=time.monotonic()
   result=sender.core.send_frame(sock,dest,sequence.read(i),session,log,12,600 if i==0 else 10)
   if first is None:first=time.monotonic()
   next_start=time.monotonic()+2
   assert result['status']=='presented'
   outcomes.append(result);print(json.dumps({'ordinal':i,'outcome':result,'elapsed_since_first_presentation':time.monotonic()-first}),flush=True)
  last=time.monotonic();assert last-first>=22
  row={'event':'complete','presented':len(outcomes),'seconds_from_first_presentation':last-first,'first_presentation_monotonic':first,'last_presentation_monotonic':last,'whole_run_retry':False}
  log.write(json.dumps(row)+'\n');log.flush();print(json.dumps(row),flush=True)
 except Exception as e:
  log.write(json.dumps({'event':'failed','error':repr(e),'whole_run_retry':False})+'\n');log.flush();raise
