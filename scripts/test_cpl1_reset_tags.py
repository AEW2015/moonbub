"""Original/candidate envelope comparison with real fixture and reset/abort recovery."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,time,zlib
parser=argparse.ArgumentParser();parser.add_argument('--extended',action='store_true');parser.add_argument('--candidate',default='fpga/candidates/cp23-reset-tags-20261105-v001');args=parser.parse_args()
r=Path(__file__).resolve().parents[1];c=(r/args.candidate).resolve()
p=r/'fpga/candidates/cp23-sdram-capture274p5-csa-20261105-v001'
o=c/('evidence/envelope-equivalence02' if args.extended else 'evidence/envelope-equivalence01');o.mkdir(parents=True,exist_ok=False)
for tag,root in [('reference',p),('candidate',c)]:
 s=(root/'inputs/core/parents/cp23_envelope.sv').read_text().replace('module cp23_envelope(',f'module {tag}(')
 (o/(tag+'.sv')).write_text(s,newline='\n')
shutil.copyfile(c/'inputs/core/compute/sha256_bytes.sv',o/'sha256_bytes.sv')
shutil.copyfile(c/'key.cp23.hex',o/'fixture.hex')
b=bytes(int(x,16)for x in (c/'key.cp23.hex').read_text().split());n=len(b)
epoch=int.from_bytes(b[5:9],'little');frame=int.from_bytes(b[9:13],'little')
bad=bytearray(b);bad[21]^=1;bad[-4:]=zlib.crc32(bad[:-4]).to_bytes(4,'little')
(o/'badtag.hex').write_text(''.join(f'{x:02x}\n'for x in bad))
tb='''`timescale 1ns/1ps
module tb;
reg clk=0;always #5 clk=~clk;
reg reset=1,start_valid=0,in_valid=0,in_last=0,abort_valid=0,result_ready=0;
reg[63:0]start_owner=64'h1234,abort_owner=64'h1234;
reg[31:0]start_epoch=EPOCH,start_frame=FRAME,start_bytes=SIZE;
reg[31:0]abort_epoch=EPOCH,abort_frame=FRAME;reg[7:0]in_byte=0;
reg[7:0]fixture[0:SIZE-1];integer checks=0,results=0,seed=23,i,t,early_last=-1;
reference refdut(CONNECTIONS);
candidate candut(CONNECTIONS);
always @(posedge clk)begin #1;
 if({refdut.start_ready,refdut.in_ready,refdut.abort_rejected,refdut.result_valid,
 refdut.result_code,refdut.envelope_checked,refdut.payload_supported,refdut.component_magic_known,
 refdut.result_owner,refdut.result_epoch,refdut.result_frame,refdut.base_bytes,refdut.hud_bytes,refdut.received_bytes}
 !=={candut.start_ready,candut.in_ready,candut.abort_rejected,candut.result_valid,
 candut.result_code,candut.envelope_checked,candut.payload_supported,candut.component_magic_known,
 candut.result_owner,candut.result_epoch,candut.result_frame,candut.base_bytes,candut.hud_bytes,candut.received_bytes})
 $fatal(1,"Public output mismatch cycle %0d",checks);
 checks=checks+1;
end
task clear;begin @(negedge clk);reset=1;start_valid=0;in_valid=0;abort_valid=0;
 repeat(3)@(negedge clk);reset=0;end endtask
task launch;begin @(negedge clk);start_valid=1;while(!refdut.start_ready)@(negedge clk);
 @(negedge clk);start_valid=0;end endtask
task sendbytes(input integer count);integer j,guard;begin
 for(j=0;j<count;j=j+1)begin
  repeat(($random(seed)&3)==0?1:0)@(negedge clk);
  in_valid=1;in_byte=fixture[j];in_last=(j==SIZE-1||j==early_last);guard=0;
  @(posedge clk);while(!refdut.in_ready)begin @(posedge clk);guard=guard+1;if(guard>100000)$fatal(1,"stuck byte");end
  @(negedge clk);in_valid=0;
 end
end endtask
task expect_error(input integer code);integer guard;begin guard=0;
 while(!refdut.result_valid)begin @(negedge clk);guard=guard+1;if(guard>100000)$fatal(1,"missing error");end
 if(refdut.result_code!=code||refdut.envelope_checked)$fatal(1,"wrong error expected=%0d actual=%0d",code,refdut.result_code);
 repeat(3)@(negedge clk);result_ready=1;@(negedge clk);result_ready=0;
end endtask
task complete;integer guard;begin launch;sendbytes(SIZE);guard=0;
 while(!refdut.result_valid)begin @(negedge clk);guard=guard+1;if(guard>100000)$fatal(1,"stuck result");end
 if(refdut.result_code!=9||!refdut.envelope_checked)$fatal(1,"fixture rejected");
 results=results+1;repeat(7)@(negedge clk);result_ready=1;@(negedge clk);result_ready=0;
end endtask
initial begin $readmemh("fixture.hex",fixture);clear;complete;
 for(t=0;t<4;t=t+1)begin
  launch;case(t)0:sendbytes(25);1:sendbytes(45);2:sendbytes(53);3:sendbytes(170);endcase
  clear;repeat(11)@(negedge clk);complete;
 end
 launch;sendbytes(45);abort_valid=1;@(negedge clk);abort_valid=0;
 repeat(5)@(negedge clk);if(!refdut.result_valid||refdut.result_code!=8)$fatal(1,"abort missing");
 result_ready=1;@(negedge clk);result_ready=0;complete;
 launch;sendbytes(45);abort_owner=64'h9999;abort_valid=1;@(negedge clk);
 if(!refdut.abort_rejected)$fatal(1,"stale abort accepted");abort_valid=0;abort_owner=64'h1234;
 clear;complete;
 EXTENDED
 $display("RESET_TAG_EQUIVALENCE_PASS cycles=%0d valid_fixtures=%0d resets_in_header_body=4 matched_abort=1 stale_abort=1",checks,results);$finish;
end
initial begin #100000000;$fatal(1,"watchdog");end
endmodule
'''
names='clk reset start_valid start_owner start_epoch start_frame start_bytes in_valid in_byte in_last abort_valid abort_owner abort_epoch abort_frame result_ready'.split()
tb=tb.replace('EXTENDED','''
 start_owner=0;launch;expect_error(1);start_owner=64'h1234;
 fixture[4]=2;launch;sendbytes(53);expect_error(2);$readmemh("fixture.hex",fixture);
 fixture[5]=fixture[5]^1;launch;sendbytes(53);expect_error(3);$readmemh("fixture.hex",fixture);
 fixture[100]=fixture[100]^1;launch;sendbytes(SIZE);expect_error(4);$readmemh("fixture.hex",fixture);
 $readmemh("badtag.hex",fixture);launch;sendbytes(SIZE);expect_error(5);$readmemh("fixture.hex",fixture);
 early_last=21;launch;sendbytes(22);expect_error(6);early_last=-1;
 complete;
 // Reset with a completed result held under backpressure, then recover.
 launch;sendbytes(SIZE);wait(refdut.result_valid);clear;complete;
 $display("RESET_TAG_NEGATIVE_RECOVERY_PASS reasons=1,2,3,4,5,6 held_result_reset=1");
''' if args.extended else '')
tb=tb.replace('CONNECTIONS',','.join('.'+x+'('+x+')'for x in names))
import re
for k,v in [('SIZE',n),('EPOCH',epoch),('FRAME',frame)]:tb=re.sub(r'\b'+k+r'\b',str(v),tb)
(o/'tb.sv').write_text(tb,newline='\n')
env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin'+os.pathsep+env.get('PATH','')
steps=[]
for label,cmd in [('compile',['C:/msys64/ucrt64/bin/iverilog.exe','-g2012','-s','tb','-o','test.vvp','reference.sv','candidate.sv','sha256_bytes.sv','tb.sv']),('simulation',['C:/msys64/ucrt64/bin/vvp.exe','test.vvp'])]:
 t=time.monotonic()
 with(o/(label+'.log')).open('wb')as f:q=subprocess.run(cmd,cwd=o,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=900)
 steps.append(dict(command=cmd,returncode=q.returncode,seconds=time.monotonic()-t))
 (o/'execution.json').write_text(json.dumps(steps,indent=2)+'\n')
 assert q.returncode==0,(o/(label+'.log')).read_text()
log=(o/'simulation.log').read_text();assert 'RESET_TAG_EQUIVALENCE_PASS' in log
(o/'result.json').write_text(json.dumps(dict(status='PASS_DIRECTED_PUBLIC_OUTPUT_COMPARISON',output=log,
 sources={f.name:hashlib.sha256(f.read_bytes()).hexdigest()for f in o.iterdir()if f.suffix in ['.sv','.hex']},hardware=False),indent=2)+'\n')
print(log)
