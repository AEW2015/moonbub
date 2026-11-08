from pathlib import Path
import json,hashlib,subprocess,os
p=Path('C:/moon/dev/experiments/staging-burst-v1-20261108');e=p/'integration-v001/wrap-limit-v001';e.mkdir(exist_ok=True)
s=(p/'tests/tb_staging_burst_pins_v1.sv').read_text();s=s[:s.index('integer i;initial begin')];s=s.replace('module tb_staging_burst_pins_v1 #','module tb_staging_burst_wrap_limit_v1 #')
s+='''integer wrapped_writes=0;
always @(posedge core_clk)if(!reset&&new_write&&new_address==0)wrapped_writes=wrapped_writes+1;
initial begin
 #300;reset=0;#200;in_start_ready=1;in_busy=1;
 command(1,1024,gold_crc(1024));setup(0,1024,1);
 // Deliberately outside the supported max256-u32 raw transaction contract.
 payload(0,1028);fence(1,1024);
 if(wrapped_writes!==1||new_quarantine||new_overflow||accepted_bytes!==1024||accepted_words!==256)$fatal(1,"wrap limitation observation differs");
 read_burst(32'he0000104,4);if(values[0]!==1024||values[2]!==gold_crc(1024)||values[3]!==0)$fatal(1,"supported prefix corrupted");
 $display("STAGING_BURST_WRAP_LIMITATION raw_words257 decoded_extra_CSR000_writes1 STB_fault0 quarantine0 accepted_prefix1024 extra_word_ignored OUTSIDE_SUPPORTED_CONTRACT NOT_FAILCLOSED_PASS");$finish;
end
initial begin #2000000;$fatal(1,"wrap diagnostic watchdog");end
endmodule
''';(e/'tb_wrap_limit.sv').write_text(s)
base=json.loads((p/'evidence/pins08/execution.json').read_text())[0]['argv'];cmd=[]
for a in base:
 if a=='tb_staging_burst_pins_v1':a='tb_staging_burst_wrap_limit_v1'
 a=a.replace('-Ptb_staging_burst_pins_v1.','-Ptb_staging_burst_wrap_limit_v1.')
 if a.endswith('/tests/tb_staging_burst_pins_v1.sv'):a=(e/'tb_wrap_limit.sv').as_posix()
 cmd.append(a)
cmd[cmd.index('-o')+1]=(e/'wrap.vvp').as_posix();env=dict(os.environ,PATH=str(Path('C:/msys64/ucrt64/bin'))+';'+os.environ['PATH'],TEMP=str(Path('C:/moon/tmp')),TMP=str(Path('C:/moon/tmp')));rows=[]
for label,command in [('compile',cmd),('run',['C:/msys64/ucrt64/bin/vvp.exe',(e/'wrap.vvp').as_posix()])]:
 r=subprocess.run(command,env=env,capture_output=True,text=True,timeout=90);(e/(label+'.log')).write_text(r.stdout+r.stderr);rows.append({'label':label,'command':command,'returncode':r.returncode});assert r.returncode==0,r.stdout+r.stderr
 assert label=='compile' or 'STAGING_BURST_WRAP_LIMITATION'in r.stdout
(e/'execution.json').write_text(json.dumps(rows,indent=2));files=[Path(a)for a in cmd if Path(a).is_file() and Path(a).suffix in ['.sv','.v']]+[p/'reference/cu70_memory_map.svh'];(e/'source-binding.json').write_text(json.dumps({str(f):hashlib.sha256(f.read_bytes()).hexdigest()for f in files},indent=2));(e/'result.json').write_text(json.dumps({'status':'LIMITATION_CONFIRMED_OVERSIZED_RAW_SPI_OUTSIDE_CONTRACT','raw_words':257,'allowed_raw_words':256,'decoded_wrapped_write_address':'0x000','STB_fault':0,'quarantine':0,'ignored_extra_words':1,'supported_prefix_correct':True,'failclosed_qualification':False,'physical_hardware':False},indent=2));print((e/'run.log').read_text())
