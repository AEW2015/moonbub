"""Execute exact staging RTL at its real49,152byte bound and fault boundaries."""
from pathlib import Path
import hashlib,json,os,subprocess,zlib
r=Path(__file__).resolve().parents[2];src=r/'fpga/experiments/cu66-v71/system/cu71_packet_staging.sv'
o=r/'fpga/experiments/cu66-v71/system/evidence/staging01';o.mkdir(parents=True,exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
data=bytes((i*13+7)&255 for i in range(49152));crc=zlib.crc32(data)
tb=r'''`timescale 1ns/1ps
module tb;
reg clk=0;always #5 clk=~clk;reg rst=1;
reg begin_valid=0,upload_valid=0,seal_valid=0,activate_valid=0,release_valid=0,discard_valid=0;
wire begin_ready,upload_ready,sealed_valid,active;reg[63:0]begin_generation=64'h123456789abcdef0;
reg[31:0]begin_bytes=49152,begin_crc=32'h@CRC@,upload_word=0;reg[2:0]upload_count=4;
wire[63:0]generation;wire[31:0]packet_bytes,written_bytes,actual_crc,faults;
reg packet_req_valid=0,packet_rsp_ready=0;wire packet_req_ready,packet_rsp_valid;
reg[15:0]packet_req_address=0;reg[63:0]packet_req_generation=64'h123456789abcdef0;
reg[31:0]packet_req_sequence=0;wire[15:0]packet_rsp_address;wire[63:0]packet_rsp_generation;
wire[31:0]packet_rsp_sequence;wire[7:0]packet_rsp_data;
cu71_packet_staging d(.*);
integer checks=0,i,j;reg[31:0]word_value;reg[7:0]expected;
task tick;begin @(posedge clk);#1;end endtask
task require(input ok,input[511:0]message);begin checks=checks+1;if(ok!==1'b1)$fatal(1,"%0s",message);end endtask
task request(input[15:0]addr,input[31:0]seq,input[7:0]want);
begin
 @(negedge clk);packet_req_address=addr;packet_req_sequence=seq;packet_req_valid=1;
 require(packet_req_ready,"request ready");tick();@(negedge clk);packet_req_valid=0;
 while(!packet_rsp_valid)tick();
 require(packet_rsp_address==addr&&packet_rsp_generation==packet_req_generation&&packet_rsp_sequence==seq,"response identity");
 require(packet_rsp_data==want,"byte data");
 repeat(2)begin tick();require(packet_rsp_valid&&packet_rsp_data==want&&packet_rsp_sequence==seq,"stable held response");end
 @(negedge clk);packet_rsp_ready=1;tick();@(negedge clk);packet_rsp_ready=0;
end endtask
initial begin
 repeat(3)tick();@(negedge clk);rst=0;
 begin_bytes=0;begin_valid=1;tick();@(negedge clk);begin_valid=0;require(begin_ready&&faults[0],"reject empty");
 begin_bytes=49153;begin_valid=1;tick();@(negedge clk);begin_valid=0;require(begin_ready,"reject oversized before allocation");
 begin_bytes=49152;begin_generation=0;begin_valid=1;tick();@(negedge clk);begin_valid=0;require(begin_ready,"reject zero generation");
 begin_generation=64'h123456789abcdef0;begin_valid=1;tick();@(negedge clk);begin_valid=0;
 require(!begin_ready&&upload_ready&&packet_bytes==49152,"bounded allocation");
 seal_valid=1;tick();@(negedge clk);seal_valid=0;require(!sealed_valid&&faults[2],"reject incomplete seal");
 for(i=0;i<49152;i=i+4)begin
  while(!upload_ready)tick();word_value=0;
  for(j=0;j<4;j=j+1)word_value=word_value|((((i+j)*13+7)&255)<<(8*j));
  @(negedge clk);upload_word=word_value;upload_valid=1;tick();@(negedge clk);upload_valid=0;
 end
 while(!upload_ready)tick();require(written_bytes==49152&&actual_crc==32'h@CRC@,"whole maximum packet crc");
 @(negedge clk);seal_valid=1;tick();@(negedge clk);seal_valid=0;require(sealed_valid,"seal exact whole packet");
 begin_valid=1;upload_valid=1;tick();@(negedge clk);begin_valid=0;upload_valid=0;
 require(sealed_valid&&written_bytes==49152&&faults[1],"sealed immutable");
 activate_valid=1;tick();@(negedge clk);activate_valid=0;require(active&&!upload_ready,"activate immutable");
 discard_valid=1;tick();@(negedge clk);discard_valid=0;require(active&&faults[6],"cannot discard active");
 for(i=0;i<49152;i=i+1)request(i[15:0],i,(i*13+7)&255);
 packet_req_generation=9;request(16'd17,32'd50000,8'd0);require(faults[4],"stale generation retained as fault");
 packet_req_generation=64'h123456789abcdef0;request(16'd49152,32'd50001,8'd0);
 @(negedge clk);packet_req_valid=1;packet_req_address=0;packet_req_sequence=50002;release_valid=1;
 tick();@(negedge clk);packet_req_valid=0;release_valid=0;require(active&&faults[5],"release cannot race accepted request");
 while(!packet_rsp_valid)tick();packet_rsp_ready=1;tick();@(negedge clk);packet_rsp_ready=0;
 release_valid=1;tick();@(negedge clk);release_valid=0;require(begin_ready&&!active,"explicit drained release");
 begin_bytes=3;begin_crc=0;begin_valid=1;tick();@(negedge clk);begin_valid=0;
 upload_count=3;upload_word=32'h00abcdef;upload_valid=1;tick();@(negedge clk);upload_valid=0;
 while(!upload_ready)tick();seal_valid=1;tick();@(negedge clk);seal_valid=0;require(!sealed_valid,"reject corrupt CRC");
 discard_valid=1;tick();@(negedge clk);discard_valid=0;require(begin_ready,"discard unowned corrupt upload");
 $display("CU71_STAGING_PASS checks=%0d bytes=49152 crc=@CRC@",checks);$finish;
end
initial begin #20000000;$fatal(1,"test watchdog");end
endmodule
'''.replace('@CRC@',f'{crc:08x}')
(o/'tb.sv').write_text(tb,newline='\n')
env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin'+os.pathsep+env.get('PATH','')
steps=[]
for name,cmd in [('compile',['C:/msys64/ucrt64/bin/iverilog.exe','-g2012','-s','tb','-o',str(o/'test.vvp'),str(src),str(o/'tb.sv')]),('run',['C:/msys64/ucrt64/bin/vvp.exe',str(o/'test.vvp')])]:
 with (o/(name+'.log')).open('wb') as log:p=subprocess.run(cmd,cwd=o,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=120)
 steps.append(dict(name=name,command=cmd,returncode=p.returncode));assert p.returncode==0,(name,o)
assert 'CU71_STAGING_PASS' in (o/'run.log').read_text()
(o/'result.json').write_text(json.dumps(dict(status='PASS_EXACT_STAGING_RTL_MAXIMUM_AND_FAILURE_TESTS',hardware=False,source_sha256=sha(src),fixture_crc32=f'{crc:08x}',bytes=len(data),steps=steps),indent=2)+'\n')
print((o/'run.log').read_text())
