"""Comparator SAT/4-state and actual elaborated-base priority proofs."""
from pathlib import Path
import argparse,ast,hashlib,json,os,re,shlex,shutil,subprocess,time
r=Path(__file__).resolve().parents[3];d=r/'fpga/experiments/cu66-v71/direct-system/tag-equality-v001';p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();o=Path(a.output).resolve();o.mkdir(parents=True,exist_ok=False);sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();lin=lambda f:'/mnt/'+f.resolve().drive[0].lower()+f.resolve().as_posix()[2:];logic=(d/'comparator-logic.txt').read_text()
(o/'miter.sv').write_text('module tag_miter(input[255:0]hash_value,input[127:0]wanted_tag,output same);\n'+logic+'\nassign same=(hash_value[255:128]!=wanted_tag)==(!tag_equal_balanced);endmodule\n')
four='''`timescale 1ns/1ps
module tb;reg[255:0]hash_value=0;reg[127:0]wanted_tag=0;
'''+logic+'''
wire old_bad=hash_value[255:128]!=wanted_tag;wire new_bad=!tag_equal_balanced;
reg[3:0]small_a,small_b;reg[1:0]lane_a,lane_b;integer checks=0,i,j,k,v;
function automatic bit4(input integer n);case(n)0:bit4=0;1:bit4=1;2:bit4=1'bx;3:bit4=1'bz;endcase endfunction
task check;begin #1;if(old_bad!==new_bad)$fatal(1,"full1284state mismatch");checks++;end endtask
initial begin
 // Exhaustive four-state four-bit comparison versus two grouped two-bit limbs.
 for(v=0;v<65536;v++)begin
  for(k=0;k<4;k++)begin small_a[k]=bit4((v>>(k*2))&3);small_b[k]=bit4((v>>(8+k*2))&3);end
  #1;if((small_a!=small_b)!==!((small_a[1:0]==small_b[1:0])&&(small_a[3:2]==small_b[3:2])))$fatal(1,"compositional4state mismatch");checks++;
 end
 for(i=0;i<128;i++)for(j=2;j<4;j++)begin
  hash_value=0;wanted_tag=0;hash_value[128+i]=bit4(j);check();
  wanted_tag[(i+17)%128]=1;check();
  wanted_tag=0;wanted_tag[i]=bit4(j);hash_value=0;check();
  hash_value[128+(i+1)%128]=1;check();
 end
 for(i=0;i<10000;i++)begin hash_value={$random,$random,$random,$random,$random,$random,$random,$random};wanted_tag=hash_value[255:128];check();wanted_tag[i%128]=~wanted_tag[i%128];check();end
 $display("TAG_EQ_FOURSTATE_PASS checks=%0d",checks);$finish;
end endmodule
''';(o/'tb_fourstate.sv').write_text(four)
helper=r/'scripts/cu66-v71/direct-system/board-math/prepare_shell_proposal.py';node=next(n for n in ast.parse(helper.read_text()).body if isinstance(n,ast.FunctionDef)and n.name=='ports');exec(compile(ast.Module(body=[node],type_ignores=[]),str(helper),'exec'),globals())
base=d/'cu71_base_pipeline_math.sv';parent=r/'fpga/experiments/cu66-v71/direct-system/validpipe-v003/cu71_base_pipeline_math.sv';ps=ports(base);outs=[n for n,(dr,_)in ps.items()if dr=='output'];decl='\n'.join(('reg'if dr=='input'else'wire')+' '+wd+' '+n+('=0'if dr=='input'else'')+';'for n,(dr,wd)in ps.items())+'\n'+''.join('wire '+ps[n][1]+' old_'+n+';\n'for n in outs)
tb='`timescale 1ns/1ps\nmodule tb_priority;\n'+decl+'\nalways #5 clk=~clk;\ncu71_base_pipeline_math dut('+','.join('.'+n+'('+n+')'for n in ps)+');\ncu71_base_pipeline_reference reference('+','.join('.'+n+'('+('old_'if n in outs else'')+n+')'for n in ps)+');\n'
tb+='reg[255:0]H=0;reg[127:0]T=0;reg[7:0]flags=0;integer checks=0,n,which;\ntask bind_state;begin\n'
for inst in['dut','reference']:
 tb+=f"force {inst}.fs=4'd4;force {inst}.hash_value=H;force {inst}.wanted_tag=T;force {inst}.rows_result_valid=1;force {inst}.write_pending=flags[0];\n"
 for flag,names in[(1,['s_error']),(2,['dq_valid','dq_error']),(3,['idct_valid','idct_error']),(4,['recon_valid','recon_error']),(5,['rows_error'])]:
  for name in names:tb+=f'force {inst}.{name}=flags[{flag}];\n'
 tb+=f"force {inst}.e_error=0;force {inst}.s_code=8'h03;force {inst}.rows_code=8'h04;force {inst}.recon_id=0;force {inst}.tid=0;\n"
tb+='end endtask\ntask compare;begin bind_state();#1;if(dut.fail_now!==reference.fail_now||dut.fail_code!==reference.fail_code||tag_valid!==old_tag_valid)$fatal(1,"actual base failpriority mismatch");checks++;end endtask\n'
tb+='''initial begin
 rst=1;repeat(3)begin @(posedge clk);#1;end @(negedge clk);rst=0;
 // Actual fail_now and error publication from the complete elaborated bases.
 for(n=0;n<64;n++)begin
  flags=n;H=0;T=1;write_done=flags[0];write_error=flags[0];compare();
  if(dut.fail_code!== (flags[0]?8'h61:flags[1]?8'h23:flags[2]?8'h31:flags[3]?8'h32:flags[4]?8'h33:flags[5]?8'h44:8'h50))$fatal(1,"documented priority changed");
 end
 flags=0;write_done=0;write_error=0;
 for(which=0;which<128;which++)begin H=0;T=0;H[128+which]=1'bx;compare();T[(which+32)%128]=1;compare();end
 flags=0;H=0;T=0;compare();if(dut.fail_now!==0)$fatal(1,"equal tag failed");
 T=1;abort_i=1;compare();@(posedge clk);#1;if(!error||error_code!==8'h50||error!==old_error||error_code!==old_error_code)$fatal(1,"abort plus tag priority");
 $display("TAG_EQ_ACTUAL_BASE_PRIORITY_PASS checks=%0d",checks);$finish;
end
initial begin #100000;$fatal(1,"watchdog");end
endmodule
''';(o/'tb_priority.sv').write_text(tb)
m=json.loads((d/'sources.json').read_text());sources=[r/n for n in m['sources']];# Freeze actual DUT dependencies with complete include paths.
forced_nets={'hash_value','rows_result_valid','e_error','s_error','dq_valid','dq_error','idct_valid','idct_error','recon_valid','recon_error','recon_id','s_code','rows_error','rows_code'}
def force_compat(text):
 seen=set()
 def rewrite(match):
  width=match[1]or'';names=[x.strip()for x in match[2].split(',')]
  if not all(re.fullmatch(r'\w+',x)for x in names):return match[0]
  selected=[x for x in names if x in forced_nets];rest=[x for x in names if x not in forced_nets];seen.update(selected)
  if not selected:return match[0]
  return ('logic '+width+' '+','.join(rest)+'; 'if rest else'')+'wire '+width+' '+','.join(selected)+';'
 text=re.sub(r'\blogic(\s+\[[^\]]+\])?\s+([^;]+);',rewrite,text)
 assert seen==forced_nets,seen
 return text
for f in sources:
 dest=o/'inputs'/f.relative_to(r);dest.parent.mkdir(parents=True,exist_ok=True)
 if f==base:dest.write_text(force_compat(f.read_text()),newline='\n')
 else:shutil.copyfile(f,dest)
for inc in m['include_dirs']:
 for f in(r/inc).glob('*.svh'):
  dest=o/'inputs'/f.relative_to(r);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,dest)
(o/'parent.sv').write_text(force_compat(parent.read_text()).replace('module cu71_base_pipeline_math (','module cu71_base_pipeline_reference ('))
pins={str(f):sha(f)for f in sources+[parent,d/'sources.json',d/'comparator-logic.txt',Path(__file__).resolve()]};(o/'source-freeze.json').write_text(json.dumps({'originals':pins,'compiled':{str(f.relative_to(o)):sha(f)for f in o.rglob('*')if f.is_file()and f.suffix in['.sv','.svh']},'verification_parent_transform':'Parent module name only; both verification copies explicitly declare the listed single-child-driven parent signals as wire instead of logic for Icarus procedural force compatibility. No child or functional logic replaced. Exact unmodified DUT remains required for native KEY/P.','Icarus_force_net_qualifiers':sorted(forced_nets)},indent=2)+'\n');env=dict(os.environ,PATH='C:/msys64/ucrt64/bin;'+os.environ['PATH']);steps=[]
def run(label,cmd,timeout=180):
 start=time.monotonic()
 with(o/(label+'.log')).open('w')as log:q=subprocess.run(cmd,cwd=o,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=timeout)
 steps.append(dict(label=label,command=cmd,returncode=q.returncode,seconds=time.monotonic()-start));(o/'execution.json').write_text(json.dumps(steps,indent=2)+'\n');print(label,q.returncode,flush=True);assert q.returncode==0,label
sat='read_verilog -sv '+lin(o/'miter.sv')+'; prep -top tag_miter; sat -verify -prove same 1 -show-inputs -show-outputs';run('sat',['wsl.exe','-d','MRS-HDL-Research','--','bash','-lc','source /opt/gamebub-openxc7-20261021/oss-cad-suite/environment && yosys -p '+shlex.quote(sat)])
assert 'SAT proof finished - no model found: SUCCESS'in(o/'sat.log').read_text()
iv='C:/msys64/ucrt64/bin/iverilog.exe';vvp='C:/msys64/ucrt64/bin/vvp.exe';run('fourstate-compile',[iv,'-g2012','-s','tb','-o','fourstate.vvp','tb_fourstate.sv']);run('fourstate',[vvp,'fourstate.vvp']);assert 'TAG_EQ_FOURSTATE_PASS'in(o/'fourstate.log').read_text()
run('priority-compile',[iv,'-g2012','-s','tb_priority',*['-I'+str(o/'inputs'/n)for n in m['include_dirs']],'-o','priority.vvp','tb_priority.sv','parent.sv',*[str(o/'inputs'/f.relative_to(r))for f in sources]])
run('priority',[vvp,'priority.vvp']);assert 'TAG_EQ_ACTUAL_BASE_PRIORITY_PASS'in(o/'priority.log').read_text()
assert all(sha(Path(n))==h for n,h in pins.items());(o/'result.json').write_text(json.dumps({'status':'PASS_ALL_BINARY_COMPARATOR_INPUT_SAT_FOURSTATE_AND_ACTUAL_BASE_PRIORITY','SAT_scope':'Exact combinational predicate, all256compared input bits; not full sequential base equivalence','fourstate':'Exhaustive4-bit4state grouped identity plus full128-bit X/Z mismatch/unknown and20000random full-input cases','actual_base':'Elaborated selected DUT children;64simultaneous higher-priority flag masks,256X cases, abort+tag publication; fault injection by force, not full decoder malformed packet proof','cycles_or_error_priority_changed':False,'hardware':False,'source_freeze_sha256':sha(o/'source-freeze.json')},indent=2)+'\n')
