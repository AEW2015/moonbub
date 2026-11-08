from pathlib import Path
import json,hashlib,subprocess,time
r=Path('C:/moon/dev/evidence/v57-v029-hardware-20261108-run01');host=Path('C:/moon/publish/host/dy71-sequence-v3');fixture=Path('C:/moon/dev/experiments/cu66-clip40-rgb444-q32-20261108-v003/package40')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(fixture/'manifest.json')=='76b37ca8245b8ed657c6caabbbd9d416de3dd4c775b1626ed466699559623034'
assert sha(host/'sequence_sender.py')=='f6675d96dcb1c8f0bcbd49efa0d5b678c7016f5d50848755332fe555a20a271e'
assert sha(host/'dyn1_sequence_core.py')=='da8c1bc9c7c000c0c8583f55305dd658afaad2b3a469ba5349cb3b3d74858b26'
assert json.loads((r/'program01/execution.json').read_text())['completion_marker']
assert 'USERCODE\t44593741' in (r/'program-receipt.tsv').read_text()
raw=(r/'usb01/serial.raw').read_text(errors='replace');assert 'sdk_elf_sha256=c2f4fbef591d85409aed7908e90ab132f1b4348c72379881fd1067dc66fc8ae0' in raw and 'HOST33 result=OK' in raw
assert (r/'camera01/preview.png').is_file() and not (r/'camera01/result.json').exists()
cmd=['python',str(host/'sequence_sender.py'),'--profile','dy71-sequence-v3','--count','40','--manifest',str(fixture/'manifest.json'),'--receiver','192.168.0.157','--bind','192.168.0.33','--initial-wait-seconds','120','--log',str(r/'sender.jsonl')]
started=time.monotonic()
with (r/'sender-console.log').open('x') as f:
 p=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT)
 (r/'sender-launch.json').write_text(json.dumps({'pid':p.pid,'command':cmd,'started_unix_us':time.time_ns()//1000,'manifest_sha256':sha(fixture/'manifest.json'),'intentional_inter_frame_delay_seconds':0,'overall_timeout_seconds':300},indent=2))
 try:code=p.wait(timeout=300)
 except subprocess.TimeoutExpired:p.terminate();code=p.wait(timeout=10)
result={'returncode':code,'seconds':time.monotonic()-started,'sender_stopped':True,'whole_run_retry':False}
(r/'sender-execution.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
assert code==0
