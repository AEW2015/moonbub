"""Four-state cycle-equivalence and maximum loader proofs, no Vivado."""
from pathlib import Path
import argparse,ast,hashlib,json,os,re,shutil,subprocess,time
r=Path(__file__).resolve().parents[4];d=r/'fpga/experiments/cu66-v71/staging-timing';a=argparse.ArgumentParser();a.add_argument('--output',required=True);args=a.parse_args();o=Path(args.output).resolve();o.mkdir(parents=True,exist_ok=False);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
helper=Path(__file__).with_name('prepare_shell_proposal.py');tree=ast.parse(helper.read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='ports');exec(compile(ast.Module(body=[node],type_ignores=[]),str(helper),'exec'),globals())
parent=r/'fpga/experiments/cu66-v71/system/cu71_packet_staging.sv';candidate=d/'cu71_packet_staging_credit.sv';ps=ports(parent);outs=[n for n,(direction,_)in ps.items()if direction=='output'];ins=[n for n,(direction,_)in ps.items()if direction=='input'];common='\nwire[2:0]upload_capacity;\n'+''.join('wire '+ps[n][1]+' old_'+n+';\n'for n in outs)
common+='cu71_packet_staging #(.MAX_BYTES(LIMIT)) old('+','.join('.'+n+'('+('old_'if n in outs else'')+n+')'for n in ps)+');\n'
common+='cu71_packet_staging_credit #(.MAX_BYTES(LIMIT)) newer('+','.join('.'+n+'('+n+')'for n in ps)+',.upload_capacity(upload_capacity));\n'
common+='integer comparisons=0; always @(negedge clk) if(!rst)begin\n'
for n in outs:common+=f'if({n}!==old_{n})$fatal(1,"MISMATCH {n} at %0t",$time);\n'
common+='if(newer.remaining_bytes!==packet_bytes-written_bytes || newer.within_packet!==(written_bytes<=packet_bytes) || upload_capacity!==((packet_bytes-written_bytes)>=4?3\'d4:(packet_bytes-written_bytes)))$fatal(1,"credit invariant rem=%h packet=%h written=%h cap=%h state=%d held=%d",newer.remaining_bytes,packet_bytes,written_bytes,upload_capacity,newer.state,newer.held_count);comparisons=comparisons+1;end\n'
maxtb=(r/'fpga/experiments/cu66-v71/system/evidence/staging01/tb.sv').read_text().replace('cu71_packet_staging d(.*);','localparam LIMIT=49152;'+common)
(o/'tb_max.sv').write_text(maxtb,newline='\n')
decl='\n'.join(('reg'if dr=='input'else'wire')+' '+wd+' '+name+('=0'if dr=='input'else'')+';'for name,(dr,wd)in ps.items())
randomtb='''`timescale 1ns/1ps
module tb_random;
parameter integer LIMIT=49152;
'''+decl+'\nalways #5 clk=~clk;\n'+common+'''
integer i,j,n;reg[31:0]seed=32'h10ade321;reg[31:0]rv;
task step;begin @(posedge clk);#1;@(negedge clk);#1;end endtask
task clear_inputs;begin begin_valid=0;upload_valid=0;seal_valid=0;activate_valid=0;release_valid=0;discard_valid=0;packet_req_valid=0;packet_rsp_ready=0;end endtask
initial begin
 rst=1;repeat(3)step();rst=0;clear_inputs();
 // Every accepted length modulo4 and every raw count0..7, including overflow.
 for(n=1;n<=17;n=n+1)begin
  begin_valid=1;begin_bytes=n;begin_generation=n;begin_crc=0;step();begin_valid=0;
  for(j=0;j<8;j=j+1)begin upload_count=j;upload_word=32'hff00a511;upload_valid=1;step();upload_valid=0;repeat(5)step();end
  discard_valid=1;step();discard_valid=0;
 end
 // Preserve parent malformed-input behavior: accepted upload concurrent discard.
 rst=1;step();rst=0;clear_inputs();begin_valid=1;begin_bytes=3;begin_generation=99;step();begin_valid=0;
 upload_count=2;upload_valid=1;discard_valid=1;step();upload_valid=0;discard_valid=0;
 if(newer.state!=0 || newer.held_count!=2)$fatal(1,"reproducer empty retains count");
 begin_valid=1;begin_bytes=1;begin_generation=100;step();begin_valid=0;repeat(2)step();
 if(written_bytes!=2 || packet_bytes!=1 || newer.within_packet!=0 || upload_capacity!=4)$fatal(1,"reproducer overshoot");
 upload_valid=1;upload_count=1;step();upload_valid=0;if(!faults[1]||newer.held_count!=0)$fatal(1,"overshoot reject");
 $display("PARENT_STALE_UPLOAD_REPRODUCED limit=%0d written=%0d packet=%0d",LIMIT,written_bytes,packet_bytes);
 rst=1;step();rst=0;clear_inputs();
 // Full arbitrary32-bit begins/requests and simultaneous invalid commands.
 for(i=0;i<180000;i=i+1)begin
  rv=$random(seed);rst=(rv[15:0]==0);
  begin_valid=(rv[5:0]==0);upload_valid=rv[6];seal_valid=(rv[10:7]==0);activate_valid=(rv[14:11]==0);
  release_valid=(rv[18:15]==0);discard_valid=(rv[22:19]==0);packet_req_valid=rv[23];packet_rsp_ready=rv[24];
  begin_generation={$random(seed),$random(seed)};begin_bytes=(rv[25]?$random(seed):($unsigned($random(seed))%23));begin_crc=$random(seed);
  upload_word=$random(seed);upload_count=rv[28:26];packet_req_address=$random(seed);packet_req_generation=$random(seed);packet_req_sequence=$random(seed);
  step();
 end
 $display("STAGING_CREDIT_DIFFERENTIAL_PASS limit=%0d comparisons=%0d",LIMIT,comparisons);$finish;
end
initial begin #3000000;$fatal(1,"watchdog");end
endmodule
'''
(o/'tb_random.sv').write_text(randomtb,newline='\n')
sources=[parent,candidate,Path(__file__).resolve()]
for f in sources:shutil.copyfile(f,o/f.name)
(o/'source-freeze.json').write_text(json.dumps({str(f):sha(f)for f in sources},indent=2)+'\n')
env=dict(os.environ,PATH='C:/msys64/ucrt64/bin;'+os.environ['PATH']);steps=[]
def run(label,cmd,timeout=180):
 start=time.monotonic()
 with(o/(label+'.log')).open('w')as log:p=subprocess.run(cmd,cwd=o,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=timeout)
 steps.append(dict(label=label,returncode=p.returncode,seconds=time.monotonic()-start,command=cmd));(o/'execution.json').write_text(json.dumps(steps,indent=2)+'\n');print(label,p.returncode,flush=True);assert p.returncode==0,label
iv='C:/msys64/ucrt64/bin/iverilog.exe';vvp='C:/msys64/ucrt64/bin/vvp.exe'
for limit in [1,3,17,49152,65536]:
 label='random-'+str(limit);run(label+'-compile',[iv,'-g2012','-s','tb_random','-Ptb_random.LIMIT='+str(limit),'-o',label+'.vvp','tb_random.sv',parent.name,candidate.name]);run(label,[vvp,label+'.vvp']);assert 'DIFFERENTIAL_PASS'in(o/(label+'.log')).read_text()
run('maximum-compile',[iv,'-g2012','-s','tb','-o','maximum.vvp','tb_max.sv',parent.name,candidate.name]);run('maximum',[vvp,'maximum.vvp']);assert 'CU71_STAGING_PASS'in(o/'maximum.log').read_text()
assert all(sha(f)==json.loads((o/'source-freeze.json').read_text())[str(f)]for f in sources)
(o/'result.json').write_text(json.dumps({'status':'PASS_FOUR_STATE_CYCLE_DIFFERENTIAL_AND_MAXIMUM_PACKET_READBACK','limits':[1,3,17,49152,65536],'random_cycles_per_limit':180000,'exact_public_outputs':outs,'asserted_redundant_counter_invariant':True,'maximum_bytes':49152,'hardware':False,'Vivado':False,'formal_equivalence':False,'source_freeze_sha256':sha(o/'source-freeze.json')},indent=2)+'\n')
