"""Exercise actual CSR/staging/read-arbiter and typed completion/identity guards."""
from pathlib import Path
import hashlib,json,os,re,shutil,subprocess,zlib
r=Path(__file__).resolve().parents[2];d=r/'fpga/experiments/cu66-v71/system'
o=d/'evidence/local-control03';o.mkdir(parents=True,exist_ok=False)
sources=[d/n for n in ['cu71_local_control.sv','cu71_packet_staging.sv','cu71_packet_arbiter.sv']]
header=sources[0].read_text().split('module cu71_local_control(',1)[1].split(');',1)[0]
decl=[];direction=None;width=''
for token in header.split(','):
 m=re.fullmatch(r'\s*(?:(input|output)\s+(?:wire|reg|logic)\s*)?(\[[^\]]+\])?\s*(\w+)\s*',token)
 assert m,token
 if m[1]:direction=m[1];width=m[2] or ''
 elif m[2]:width=m[2]
 decl.append(('reg ' if direction=='input' else 'wire ')+width+' '+m[3]+('=0;' if direction=='input' else ';'))
crc=zlib.crc32(bytes(range(8)))
tb='`timescale 1ns/1ps\nmodule tb;\n'+'\n'.join(decl)+r'''
always #5 clk=~clk;
cu71_local_control d(.*);
integer checks=0,start_count=0,result_count=0,drain_count=0,ack_count=0,abort_count=0,aux_count=0;
reg aux_pending=0;reg[15:0] memory_word=0;
always @(posedge clk)if(!rst)begin
 if(start_valid&&start_ready)start_count<=start_count+1;
 if(hud_result_valid&&hud_result_ready)result_count<=result_count+1;
 if(hud_drain_valid&&hud_drain_ready)drain_count<=drain_count+1;
 if(software_ack_valid&&software_ack_ready)ack_count<=ack_count+1;
 if(abort_i)abort_count<=abort_count+1;
 if(hud_aux_req_valid&&hud_aux_req_ready)begin
  aux_pending<=1;aux_count<=aux_count+1;
  if(hud_aux_req_write)memory_word<=hud_aux_req_data;
 end
 if(aux_pending)begin hud_aux_rsp_valid<=1;hud_aux_rsp_data<=memory_word;aux_pending<=0;end
 if(hud_aux_rsp_valid&&hud_aux_rsp_ready)hud_aux_rsp_valid<=0;
end
task tick;begin @(posedge clk);#1;end endtask
task require(input ok,input[767:0]message);begin checks=checks+1;if(ok!==1'b1)$fatal(1,"%0s",message);end endtask
task wr(input[11:0]a,input[31:0]v);begin @(negedge clk);bus_address=a;bus_wdata=v;bus_write=1;tick();@(negedge clk);bus_write=0;end endtask
task set_context(input[63:0]g,input[31:0]f,input[31:0]refid);begin wr('h040,g[31:0]);wr('h044,g[63:32]);wr('h048,f);wr('h04c,refid);end endtask
task cmd(input[31:0]seq,input[7:0]op,input[31:0]expected_status);
integer timeout;begin
 wr('h020,seq);wr('h024,{24'd0,op});bus_address='h028;#1;timeout=0;
 while(bus_rdata!=seq&&timeout<1000)begin tick();timeout=timeout+1;end
 require(timeout<1000,"bounded command completion");bus_address='h02c;#1;
 if(bus_rdata!==expected_status)$display("command seq=%0d op=%0d status=%h expected=%h",seq,op,bus_rdata,expected_status);
 require(bus_rdata===expected_status,"command status");
end endtask
initial begin
 rst=1;repeat(3)tick();@(negedge clk);rst=0;
 start_ready=1;hud_result_ready=1;hud_drain_ready=1;software_ack_ready=1;hud_aux_req_ready=1;packet_rsp_ready=1;
 bus_address=0;#1;require(bus_rdata==32'h43553731,"distinct CU71 identity");
 set_context(0,0,0);wr('h050,8);wr('h054,32'h@CRC@);cmd(1,1,32'h80000002);
 require(d.staging_begin_ready&&d.staged_generation==0,"invalid begin cannot mutate staging");
 set_context(1,10,0);cmd(2,1,0);require(d.upload_ready,"loader ready");
 wr('h100,32'h03020100);repeat(5)tick();wr('h100,32'h07060504);repeat(5)tick();
 bus_address='h104;#1;require(bus_rdata==8,"actual bytes stored");
 set_context(99,10,0);cmd(3,2,32'h80000003);require(!d.sealed_valid,"stale seal cannot mutate");
 set_context(1,10,0);cmd(4,2,0);require(d.sealed_valid,"sealed immutable packet");
 set_context(99,10,0);cmd(5,3,32'h80000004);require(start_count==0&&!d.staging_active,"stale start cannot activate");
 cmd(6,4,32'h80000005);require(d.sealed_valid,"stale discard cannot free");
 set_context(1,10,0);cmd(7,3,0);busy=1;repeat(3)tick();require(start_count==1&&d.staging_active,"one valid owner admission");
 wr('h050,0);cmd(8,21,0);bus_address='h030;#1;require(bus_rdata==32'h03020100,"actual staged word read");
 wr('h050,4);cmd(9,21,0);bus_address='h030;#1;require(bus_rdata==32'h07060504,"second staged word read");
 set_context(99,10,0);cmd(10,21,32'h8000000b);require(!quarantine&&d.staging_faults==0,"stale CPU read rejected before packet arbiter");
 set_context(1,10,0);active_generation=1;active_frame_id=10;active_reference_id=0;candidate_bank=0;hud_bytes=100;hud_address=12;
 expected_hud_tag=128'h00112233445566778899aabbccddeeff;hud_prepare_valid=1;tick();@(negedge clk);hud_prepare_valid=0;
 require(d.hud_pending&&d.hud_fid==10,"HUD request snapshot");
 wr('h050,1);wr('h054,21120);wr('h060,32'h00112233);wr('h064,32'h44556677);wr('h068,32'h8899aabb);wr('h06c,32'hccddeeff);
 set_context(99,10,0);cmd(11,16,32'h80000007);require(result_count==0,"stale HUD result cannot pulse");
 set_context(1,10,0);cmd(12,16,0);require(result_count==1,"matching HUD result completes");
 wr('h050,21120);cmd(13,17,32'h80000008);require(aux_count==0,"out of bounds AUX cannot become orphaned request");
 wr('h050,0);wr('h054,16'hbeef);cmd(14,17,0);require(aux_count==1&&memory_word==16'hbeef,"actual AUX completion");
 cmd(15,18,0);bus_address='h030;#1;require(bus_rdata==16'hbeef,"readback response not expected data injection");
 wr('h050,1);wr('h054,21120);wr('h058,0);cmd(16,19,0);require(drain_count==1,"matching drain forwarded after actual AUX responses");
 software_command_opcode=5;software_command_valid=1;tick();@(negedge clk);software_command_valid=0;
 require(d.soft_pending,"software command snapshot");
 wr('h050,5);wr('h054,1);set_context(1,10,99);cmd(17,20,32'h8000000a);require(ack_count==0,"stale reference cannot ACK COMMIT");
 set_context(1,10,0);cmd(18,20,0);require(ack_count==1&&!d.soft_pending,"matching COMMIT ACK");
 stage=10;cmd(19,5,32'h80000006);require(abort_count==0,"postcommit abort blocked");
 stage=5;cmd(20,5,0);require(abort_count==1,"precommit abort requested once");
 cmd(20,5,0);require(abort_count==1,"same sequence retry idempotent");
 busy=0;repeat(8)tick();require(d.staging_begin_ready&&!d.frame_active,"packet released only after observed owner completion");
 wr('h050,8);wr('h054,32'h@CRC@);cmd(21,1,32'h80000002);require(d.staging_begin_ready,"old generation rejected without allocation");
 set_context(2,11,10);transport_fault=1;cmd(22,1,32'h80000002);require(quarantine&&d.staging_begin_ready,"transport quarantine blocks new publication");
 $display("CU71_LOCAL_CONTROL_PASS checks=%0d starts=%0d aux=%0d results=%0d drains=%0d softacks=%0d",checks,start_count,aux_count,result_count,drain_count,ack_count);$finish;
end
initial begin #20000000;$fatal(1,"test watchdog");end
endmodule
'''.replace('@CRC@',f'{crc:08x}')
(o/'tb.sv').write_text(tb,newline='\n')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();pins={str(p.relative_to(r)):sha(p) for p in sources}
for p in sources:shutil.copyfile(p,o/p.name)
env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin'+os.pathsep+env.get('PATH','')
steps=[]
for name,cmd in [('compile',['C:/msys64/ucrt64/bin/iverilog.exe','-g2012','-I',str(r/'fpga/experiments/cu66-v70/memory'),'-s','tb','-o',str(o/'test.vvp'),*map(str,sources),str(o/'tb.sv')]),('run',['C:/msys64/ucrt64/bin/vvp.exe',str(o/'test.vvp')])]:
 with (o/(name+'.log')).open('wb')as log:p=subprocess.run(cmd,cwd=o,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=120)
 steps.append(dict(name=name,command=cmd,returncode=p.returncode));(o/'execution.json').write_text(json.dumps(steps,indent=2)+'\n');assert p.returncode==0,(name,o)
assert 'CU71_LOCAL_CONTROL_PASS' in (o/'run.log').read_text()
assert pins=={str(p.relative_to(r)):sha(p) for p in sources}
(o/'result.json').write_text(json.dumps(dict(status='PASS_ACTUAL_CONTROL_STAGING_ARBITER_TYPED_COMPLETION',source_sha256=pins,hardware=False,scope='Fake owner/AUX endpoints; actual local control+staging+read arbiter. Not complete CU66 decoder or physical QSPI.'),indent=2)+'\n')
print((o/'run.log').read_text())
