"""Actual combinational decision-block miter for tag_valid state qualification."""
from pathlib import Path
import argparse,hashlib,json,os,re,shlex,subprocess,time
r=Path(__file__).resolve().parents[3];d=r/'fpga/experiments/cu66-v71/direct-system/tag-feedback-cut-v002';p=r/'fpga/experiments/cu66-v71/direct-system/validpipe-v003/cu71_base_pipeline_math.sv';a=argparse.ArgumentParser();a.add_argument('--output',required=True);args=a.parse_args();o=Path(args.output).resolve();o.mkdir(parents=True,exist_ok=False);sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();lin=lambda f:'/mnt/'+f.resolve().drive[0].lower()+f.resolve().as_posix()[2:]
inputs={'fs':'[3:0]','abort_i':'','write_done':'','write_pending':'','write_error':'','e_error':'','e_code':'[7:0]','s_error':'','s_code':'[7:0]','dq_valid':'','dq_error':'','idct_valid':'','idct_error':'','recon_valid':'','recon_error':'','recon_id':'[31:0]','tid':'[31:0]','rows_error':'','rows_code':'[7:0]','rows_result_valid':'','hash_value':'[255:0]','wanted_tag':'[127:0]'}
ports=','.join('input '+w+' '+n for n,w in inputs.items());constants="localparam[3:0] IDLE=0,RUN_PLANE=3,HASH_WAIT=4,RESULT_HOLD=5,DRAIN=6;\n";modules=''
for kind,path in[('old',p),('new',d/'cu71_base_pipeline_math.sv')]:
 text=path.read_text();start=text.index('    always_comb begin\n        fail_now=0;');end=text.index('    always_ff @(posedge clk)begin',start);logic=text[start:end];tag=next(x.strip()for x in text.splitlines()if x.strip().startswith('assign tag_valid='));modules+='module logic_'+kind+'('+ports+',output tag_valid,output reg fail_now,output reg[7:0]fail_code,output reg kill);\n'+constants+('reg fail_without_tag;\n'if kind=='new'else'')+tag+'\n'+logic+'endmodule\n'
miter='module tagcut_miter('+ports+',output same);\nwire old_tag,new_tag,old_fail,new_fail,old_kill,new_kill;wire[7:0]old_code,new_code;\n'
for kind in['old','new']:miter+='logic_'+kind+' '+kind+'_logic('+','.join('.'+n+'('+n+')'for n in inputs)+',.tag_valid('+kind+'_tag),.fail_now('+kind+'_fail),.fail_code('+kind+'_code),.kill('+kind+'_kill));\n'
miter+='assign same=(old_tag==new_tag)&&(old_fail==new_fail)&&(old_code==new_code)&&(old_kill==new_kill);\nendmodule\n';(o/'miter.sv').write_text(modules+miter,newline='\n')
tb='`timescale 1ns/1ps\nmodule tb;\n'+''.join('reg '+w+' '+n+'=0;\n'for n,w in inputs.items())+'wire same;tagcut_miter dut(.*);integer checks=0,f,c,t,i,k;\n'
tb+='''function automatic bit4(input integer n);case(n)0:bit4=0;1:bit4=1;2:bit4=1'bx;3:bit4=1'bz;endcase endfunction
task check;begin #1;if(dut.old_tag!==dut.new_tag||dut.old_fail!==dut.new_fail||dut.old_code!==dut.new_code||dut.old_kill!==dut.new_kill)$fatal(1,"4state decision mismatch fs=%b",fs);checks++;end endtask
task clear_flags;begin write_done=0;write_pending=0;write_error=0;e_error=0;s_error=0;dq_valid=0;dq_error=0;idct_valid=0;idct_error=0;recon_valid=0;recon_error=0;rows_error=0;end endtask
initial begin
 e_code=8'h03;s_code=8'h04;rows_code=8'h05;recon_id=0;tid=0;
 // Every packed4state value, higher-error prefix context and tag/valid condition.
 for(f=0;f<256;f++)begin
  for(k=0;k<4;k++)fs[k]=bit4((f>>(2*k))&3);
  for(c=0;c<9;c++)begin
   clear_flags();case(c)1:begin write_done=1;write_pending=1;write_error=1;end
    2:e_error=1;3:s_error=1;4:begin dq_valid=1;dq_error=1;end
    5:begin idct_valid=1;idct_error=1;end6:begin recon_valid=1;recon_error=1;end
    7:rows_error=1;8:begin write_done=1;write_pending=1;write_error=1;e_error=1;s_error=1;rows_error=1;end endcase
   for(t=0;t<4;t++)begin rows_result_valid=bit4(t);hash_value=0;wanted_tag=1;check();wanted_tag=0;check();wanted_tag[17]=1'bx;check();end
  end
 end
 // Unknown higher-priority flags and metadata; compare actual procedural-if behavior.
 for(i=0;i<20000;i++)begin for(k=0;k<4;k++)fs[k]=bit4($unsigned($random)%4);abort_i=$random;write_done=bit4($unsigned($random)%4);write_pending=$random;write_error=bit4($unsigned($random)%4);e_error=bit4($unsigned($random)%4);s_error=bit4($unsigned($random)%4);dq_valid=$random;dq_error=bit4($unsigned($random)%4);idct_valid=$random;idct_error=bit4($unsigned($random)%4);recon_valid=$random;recon_error=bit4($unsigned($random)%4);rows_error=bit4($unsigned($random)%4);rows_result_valid=bit4($unsigned($random)%4);hash_value=0;wanted_tag=0;if(i%3==0)hash_value[128+i%128]=bit4(2+i%2);else wanted_tag[i%128]=1;check();end
 $display("TAG_FEEDBACK_CUT_FOURSTATE_PASS checks=%0d packed_fs4state=256",checks);$finish;
end endmodule
''';tb=tb.replace('end6:','end 6:');(o/'tb.sv').write_text(tb,newline='\n');pins={str(f):sha(f)for f in[p,d/'cu71_base_pipeline_math.sv',d/'derivation.json',Path(__file__).resolve()]};(o/'source-freeze.json').write_text(json.dumps({'originals':pins,'miter':'Exact original/new always_comb fail/code/kill blocks and tag_valid assignments, unchanged enum constants','packed_fs_constraint':'NONE: all4bits unconstrained in SAT; all256fourstate encodings simulated'},indent=2)+'\n');env=dict(os.environ,PATH='C:/msys64/ucrt64/bin;'+os.environ['PATH']);steps=[]
def run(label,cmd):
 with(o/(label+'.log')).open('w')as log:q=subprocess.run(cmd,cwd=o,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=180)
 steps.append({'label':label,'command':cmd,'returncode':q.returncode});(o/'execution.json').write_text(json.dumps(steps,indent=2)+'\n');print(label,q.returncode,flush=True);assert q.returncode==0,label
command='read_verilog -sv '+lin(o/'miter.sv')+'; prep -top tagcut_miter -flatten; sat -verify -prove same 1 -show-inputs -show-outputs';run('sat',['wsl.exe','-d','MRS-HDL-Research','--','bash','-lc','source /opt/gamebub-openxc7-20261021/oss-cad-suite/environment && yosys -p '+shlex.quote(command)]);assert 'SAT proof finished - no model found: SUCCESS'in(o/'sat.log').read_text()
run('compile',['C:/msys64/ucrt64/bin/iverilog.exe','-g2012','-s','tb','-o','test.vvp','miter.sv','tb.sv']);run('fourstate',['C:/msys64/ucrt64/bin/vvp.exe','test.vvp']);assert 'TAG_FEEDBACK_CUT_FOURSTATE_PASS'in(o/'fourstate.log').read_text();assert all(sha(Path(n))==h for n,h in pins.items());(o/'result.json').write_text(json.dumps({'status':'PASS_ACTUAL_DECISION_BLOCK_UNCONSTRAINED_BINARY_SAT_AND_PACKED_FOURSTATE','unchanged_outputs_proven':['tag_valid','fail_now','fail_code','kill'],'SAT_state_assumptions':'None, all16binaryfs values','fourstate_fs_values':256,'fourstate_checks':47648,'hardware':False,'scope':'Exact combinational decision blocks, not unbounded full sequential base proof','source_freeze_sha256':sha(o/'source-freeze.json')},indent=2)+'\n')
