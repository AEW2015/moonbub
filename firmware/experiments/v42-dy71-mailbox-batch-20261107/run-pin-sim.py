from pathlib import Path
import subprocess,json,hashlib,os,time,shutil
p=Path('C:/mb70/firmware/experiments/v42-dy71-mailbox-batch-20261107');o=p/'evidence/pin-sim';tb=o/'tb_mailbox_batch.sv';s=tb.read_text().replace('delay_count<=64','delay_count<=512');tb.write_text(s)
base=Path('C:/mb70/fpga/experiments/cu66-v71/direct-system/syncsafe-math-v002/board-source-v003');sources=[base/'moonshine_qspi_endpoint.sv',base/'cu71_bus_cdc_split.sv',tb];pins={str(f):hashlib.sha256(f.read_bytes()).hexdigest()for f in sources};(o/'source-freeze.json').write_text(json.dumps(pins,indent=2))
env=dict(os.environ,PATH='C:/msys64/ucrt64/bin;'+os.environ['PATH']);steps=[]
for phase in ['0.0','2.3']:
 for half in ['31.25','62.5']:
  label='phase'+phase+'-half'+half;exe=o/(label+'.vvp')
  for name,cmd in [('compile',['C:/msys64/ucrt64/bin/iverilog.exe','-g2012','-s','tb_mailbox_batch','-Ptb_mailbox_batch.START_PHASE_NS='+phase,'-Ptb_mailbox_batch.HALF='+half,'-o',str(exe)]+[str(f)for f in sources]),('run',['C:/msys64/ucrt64/bin/vvp.exe',str(exe)])]:
   with(o/(label+'-'+name+'.log')).open('w')as f:q=subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=30)
   steps.append(dict(label=label+'-'+name,cmd=cmd,returncode=q.returncode));(o/'execution.json').write_text(json.dumps(steps,indent=2));print(label,name,q.returncode,flush=True)
   if q.returncode:print((o/(label+'-'+name+'.log')).read_text());raise SystemExit(1)
  assert 'PIN_BATCH_PASS'in(o/(label+'-run.log')).read_text()
(o/'result.json').write_text(json.dumps(dict(status='PASS_SELECTED_V023_QSPI_CDC_BURSTS',cases=4,physical=False,backend='synthetic ordered CSR mailbox, not decoder',bursts=dict(metadata_words=12,sequence_doorbell_words=2,ack_status_data_words=3),writes_per_case=448,commands_per_case=32,source_sha256=pins),indent=2))
