"""Target the new pending-write and COMP_FLUSH cancellation states explicitly."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess
r=Path(__file__).resolve().parents[1];p=r/'fpga/experiments/sha-csa-byte-reservation-20261105-v001'
o=p/'flush-cancel01';o.mkdir(exist_ok=False);shutil.copyfile(p/'sha256_bytes.sv',o/'sha256_bytes.sv')
tb=(p/'tb_sha.sv').read_text().split(' initial begin',1)[0]+'''
 initial begin
  repeat(3)@(negedge clk);reset=0;
  for(j=0;j<2;j=j+1)begin
   launch(64,6100+j);put(8'h88,0);in_valid=0;
   if(!dut.block_write_valid)$fatal(1,"pending write not covered");flush(j);
   launch(64,6200+j);for(i=0;i<64;i=i+1)put(i,i==63);in_valid=0;
   if(dut.state!=11||!dut.block_write_valid)$fatal(1,"final-byte flush not covered");flush(j);
   launch(3,6300+j);put(8'h61,0);put(8'h62,0);put(8'h63,1);in_valid=0;
   finish(256'hba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad);
  end
  $display("SHA_RESERVATION_CANCEL_PASS pending_reset_abort=2 final_flush_reset_abort=2 recovery_hashes=2 cycles=%0d",cycles);$finish;
 end
endmodule
'''
(o/'tb.sv').write_text(tb,newline='\n');env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin'+os.pathsep+env.get('PATH','');rows=[]
for label,cmd in [('compile',['C:/msys64/ucrt64/bin/iverilog.exe','-g2012','-s','tb_sha','-o','test.vvp','sha256_bytes.sv','tb.sv']),('simulation',['C:/msys64/ucrt64/bin/vvp.exe','test.vvp'])]:
 q=subprocess.run(cmd,cwd=o,env=env,capture_output=True,text=True,timeout=90);(o/(label+'.log')).write_text(q.stdout+q.stderr)
 rows.append(dict(command=cmd,returncode=q.returncode));assert q.returncode==0,q.stdout+q.stderr
log=(o/'simulation.log').read_text();assert 'SHA_RESERVATION_CANCEL_PASS'in log
(o/'result.json').write_text(json.dumps(dict(status='PASS_TARGETED_RESERVATION_CANCEL',output=log,execution=rows,
 sources={n:hashlib.sha256((o/n).read_bytes()).hexdigest()for n in ['sha256_bytes.sv','tb.sv']},hardware=False),indent=2)+'\n');print(log)
