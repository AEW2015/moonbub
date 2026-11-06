"""Exercise the new classification state and captured input metadata directly."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess
r=Path(__file__).resolve().parents[2]
out=r/'fpga/experiments/cu66-v71/dequant-validpipe/evidence/validation-cancel01';out.mkdir(parents=True,exist_ok=False)
src=r/'fpga/experiments/cu66-v71/dequant-validpipe/cu71_dequant_validpipe.sv'
header=r/'fpga/experiments/cu66-v69/inverse/cu66_quant_rom.svh'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
pins={p.relative_to(r).as_posix():sha(p)for p in[src,header]}
for p in[src,header]:shutil.copyfile(p,out/p.name)
tb='''module tb_cancel;
logic clk=0;always #5 clk=~clk;
logic rst=1,abort_i=0,in_valid=0,in_ready,out_valid,out_ready=0,out_error;
logic[31:0]in_id=0,out_id;logic[1023:0]in_coefficients=0;
logic in_chroma=0;logic[1:0]in_scale_code=1;logic[1279:0]out_dequantized;
cu71_dequant_validpipe dut(.*);
task automatic tick;begin @(posedge clk);#1;end endtask
task automatic accept(input integer kind,input integer ident);
begin
 @(negedge clk);if(!in_ready)$fatal(1,"not ready");
 in_coefficients=0;in_chroma=1;in_scale_code=2;in_id=ident;
 if(kind==1)in_coefficients[15:0]=16'sd2048;
 if(kind==2)in_coefficients[15:0]=16'sd2049;
 if(kind==3)in_scale_code=3;
 in_valid=1;tick();if(dut.state!==2'd3||out_valid)$fatal(1,"new state missing");
 @(negedge clk);in_valid=0;
end endtask
initial begin
 repeat(3)tick();if(!$isunknown(out_dequantized)||!$isunknown(dut.bad_group))$fatal(1,"payload initialized");
 @(negedge clk);rst=0;
 for(integer kind=0;kind<2;kind=kind+1)begin
  accept(1,100+kind);if(kind==0)rst=1;else abort_i=1;
  tick();if(out_valid)$fatal(1,"cancelled validation leaked");
  @(negedge clk);rst=0;abort_i=0;#1;
  if(!in_ready||!$isunknown(out_dequantized))$fatal(1,"cancelled payload exposed");
 end
 for(integer kind=0;kind<4;kind=kind+1)begin
  accept(kind,200+kind);
  // Change coefficient range, zero status, chroma and scale after acceptance.
  in_coefficients=~in_coefficients;in_chroma=0;in_scale_code=0;
  for(integer wait_cycles=0;!out_valid;wait_cycles=wait_cycles+1)begin
   tick();if(wait_cycles>15)$fatal(1,"output timeout");
  end
  if(out_id!==32'(200+kind)||out_error!==1'(kind>=2))$fatal(1,"captured classification failed");
  if(kind==1)begin
   if(out_dequantized[19:0]!==20'd69632||out_dequantized[1279:20]!==0)$fatal(1,"captured quantizer/chroma failed");
  end else if(out_dequantized!==0)$fatal(1,"zero/error publication failed");
  repeat(3)begin tick();if(!out_valid||out_id!==32'(200+kind))$fatal(1,"stalled result changed");end
  @(negedge clk);out_ready=1;tick();@(negedge clk);out_ready=0;
 end
 $display("DEQUANT_VALIDATION_CANCEL_PASS direct_abort=1 direct_reset=1 poisoned_metadata_replays=4 unknown_payload_retained=1");$finish;
end
initial begin #10000;$fatal(1,"watchdog");end
endmodule
'''
(out/'tb.sv').write_text(tb,newline='\n')
env=dict(os.environ,PATH='C:/msys64/ucrt64/bin;'+os.environ['PATH']);steps=[]
for name,cmd in [('compile',['C:/msys64/ucrt64/bin/iverilog.exe','-g2012','-I',str(out),'-s','tb_cancel','-o',str(out/'sim.vvp'),str(out/src.name),str(out/'tb.sv')]),
                 ('simulation',['C:/msys64/ucrt64/bin/vvp.exe',str(out/'sim.vvp')])]:
 with(out/(name+'.log')).open('wb')as f:p=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,env=env,timeout=60)
 steps.append(dict(label=name,command=cmd,returncode=p.returncode));(out/'execution.json').write_text(json.dumps(steps,indent=2)+'\n')
 assert p.returncode==0,(name,out)
assert pins=={n:sha(r/n)for n in pins}
assert 'DEQUANT_VALIDATION_CANCEL_PASS'in(out/'simulation.log').read_text()
(out/'result.json').write_text(json.dumps(dict(status='PASS_NEW_STATE_CANCEL_AND_CAPTURED_RANGE_ZERO_CHROMA_SCALE',
 source_sha256=pins,artifacts={p.name:sha(p)for p in out.iterdir()if p.is_file()and p.suffix in['.sv','.svh','.log','.json']},hardware=False),indent=2)+'\n')
print((out/'simulation.log').read_text())
