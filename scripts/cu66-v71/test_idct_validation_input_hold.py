"""Directed cancellation in the newly added validation state, four-state RTL."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess
r=Path(__file__).resolve().parents[2]
out=r/'fpga/experiments/cu66-v71/inverse-validpipe/evidence/validation-cancel02'
out.mkdir(parents=True,exist_ok=False)
src=r/'fpga/experiments/cu66-v71/inverse-validpipe/cu71_idct_validpipe.sv'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
frozen=sha(src);shutil.copyfile(src,out/src.name)
bench='''module tb_validation_cancel;
logic clk=0;always #5 clk=~clk;
logic rst=1,abort_frame=0,in_valid=0,in_ready,out_valid,out_ready=0,out_error;
logic[31:0]in_id=0,out_id,active_cycles;
logic[1279:0]in_tile=0;logic[1535:0]out_tile;
cu71_idct_validpipe dut(.*);
task automatic tick;begin @(posedge clk);#1;end endtask
task automatic accept(input bit bad,input integer ident);
begin
 @(negedge clk);if(!in_ready)$fatal(1,"not input-ready");
 in_id=ident;in_tile=0;if(bad)in_tile[19:0]=20'h7ffff;in_valid=1;
 tick();if(dut.state!==4'd10||out_valid)$fatal(1,"validation stage not entered exclusively");
 @(negedge clk);in_valid=0;
end endtask
initial begin
 repeat(3)tick();if(!$isunknown(out_tile)||!$isunknown(dut.bad_group))$fatal(1,"payload unexpectedly initialized");
 @(negedge clk);rst=0;
 for(integer mode=0;mode<2;mode=mode+1)begin
  accept(0,100+mode);
  if(mode==0)abort_frame=1;else rst=1;
  tick();if(out_valid)$fatal(1,"cancelled validation leaked");
  @(negedge clk);abort_frame=0;rst=0;#1;
  if(!in_ready||!$isunknown(out_tile))$fatal(1,"cancelled validation published payload");
 end
 for(integer bad=0;bad<2;bad=bad+1)begin
  accept(1'(bad),200+bad);in_tile=bad?1280'd0:{64{20'h7ffff}};tick();
  if(!out_valid||out_id!==32'(200+bad)||out_error!==1'(bad)||out_tile!==1536'd0||active_cycles!==32'd1)
    $fatal(1,"validation replay/zero/error publication mismatch");
  repeat(4)begin tick();if(!out_valid||out_tile!==0||active_cycles!==1)$fatal(1,"stalled validation output changed");end
  @(negedge clk);out_ready=1;tick();@(negedge clk);out_ready=0;
 end
 $display("IDCT_VALIDATION_CANCEL_PASS abort_new_state=1 reset_new_state=1 unknown_payload_retained=1 zero_bad_replays=2 stalls=8");$finish;
end
initial begin #10000;$fatal(1,"watchdog");end
endmodule
'''
(out/'tb.sv').write_text(bench,newline='\n')
env=dict(os.environ,PATH='C:/msys64/ucrt64/bin;'+os.environ['PATH']);steps=[]
for label,cmd in [('compile',['C:/msys64/ucrt64/bin/iverilog.exe','-g2012','-s','tb_validation_cancel','-o',str(out/'sim.vvp'),str(out/src.name),str(out/'tb.sv')]),
                  ('simulation',['C:/msys64/ucrt64/bin/vvp.exe',str(out/'sim.vvp')])]:
 with(out/(label+'.log')).open('wb')as f:p=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,env=env,timeout=60)
 steps.append(dict(label=label,command=cmd,returncode=p.returncode))
 (out/'execution.json').write_text(json.dumps(steps,indent=2)+'\n')
 assert p.returncode==0,(label,out)
assert frozen==sha(src)==sha(out/src.name)
assert 'IDCT_VALIDATION_CANCEL_PASS' in(out/'simulation.log').read_text()
(out/'result.json').write_text(json.dumps(dict(status='PASS_NEW_VALIDATION_STATE_ABORT_RESET_AND_ZERO_BAD_STALL_REPLAY',source_sha256=frozen,
 artifacts={p.name:sha(p)for p in out.iterdir()if p.is_file()and p.suffix in ['.sv','.log','.json']},hardware=False),indent=2)+'\n')
print((out/'simulation.log').read_text())
