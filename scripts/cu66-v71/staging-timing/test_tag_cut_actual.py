from pathlib import Path
import argparse,ast,hashlib,json,os,re,shutil,subprocess
r=Path(__file__).resolve().parents[3];d=r/'fpga/experiments/cu66-v71/direct-system/tag-feedback-cut-v002';a=argparse.ArgumentParser();a.add_argument('--output',required=True);args=a.parse_args();o=Path(args.output).resolve();o.mkdir(parents=True,exist_ok=False);sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();helper=Path(__file__).with_name('test_tag_equality.py');tree=ast.parse(helper.read_text());forced_nets=ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(x,ast.Name)and x.id=='forced_nets'for x in n.targets)));node=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='force_compat');exec(compile(ast.Module(body=[node],type_ignores=[]),str(helper),'exec'),globals())
m=json.loads((d/'sources.json').read_text());base=d/'cu71_base_pipeline_math.sv';pins={}
for n,h in m['sources_sha256'].items():
 f=r/n;assert sha(f)==h;dest=o/'inputs'/n;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(force_compat(f.read_text()),newline='\n')if f==base else shutil.copyfile(f,dest);pins[n]=h
for inc in m['include_dirs']:
 for f in(r/inc).glob('*.svh'):
  n=f.relative_to(r).as_posix();dest=o/'inputs'/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,dest);pins[n]=sha(f)
prior=r/'fpga/experiments/cu66-v71/direct-system/tag-equality-v001/evidence/predicate03';shutil.copyfile(prior/'parent.sv',o/'parent.sv');tb=(prior/'tb_priority.sv').read_text();tb=tb.replace('reg[255:0]H=0;','reg[3:0]FS=4;integer fi,fk;function automatic bit4(input integer n);case(n)0:bit4=0;1:bit4=1;2:bit4=1\'bx;3:bit4=1\'bz;endcase endfunction\nreg[255:0]H=0;').replace("force dut.fs=4'd4;","force dut.fs=FS;").replace("force reference.fs=4'd4;","force reference.fs=FS;")
marker='$display("TAG_EQ_ACTUAL_BASE_PRIORITY_PASS checks=%0d",checks);';assert marker in tb;extension='''abort_i=0;H=0;T=1;
 for(fi=0;fi<256;fi++)begin
  for(fk=0;fk<4;fk++)FS[fk]=bit4((fi>>(fk*2))&3);
  for(n=0;n<64;n++)begin flags=n;write_done=flags[0];write_error=flags[0];compare();end
 end
 $display("TAG_CUT_ACTUAL_BASE_PRIORITY_PASS checks=%0d original322included=1 packed_fs4state=256",checks);''';tb=tb.replace(marker,extension);(o/'tb.sv').write_text(tb,newline='\n');(o/'source-freeze.json').write_text(json.dumps({'originals':pins,'prior_bench_sha256':sha(prior/'tb_priority.sv'),'parent_verification_copy_sha256':sha(o/'parent.sv'),'Icarus_force_compatibility':sorted(forced_nets),'compiled':{str(f.relative_to(o)):sha(f)for f in o.rglob('*.sv')},'helper_sha256':sha(helper),'runner_sha256':sha(Path(__file__))},indent=2)+'\n');env=dict(os.environ,PATH='C:/msys64/ucrt64/bin;'+os.environ['PATH']);steps=[]
commands=[('compile',['C:/msys64/ucrt64/bin/iverilog.exe','-g2012','-s','tb_priority',*['-I'+str(o/'inputs'/inc)for inc in m['include_dirs']],'-o','test.vvp','tb.sv','parent.sv',*[str(o/'inputs'/n)for n in m['sources']]]),('simulation',['C:/msys64/ucrt64/bin/vvp.exe','test.vvp'])]
for label,cmd in commands:
 with(o/(label+'.log')).open('w')as log:q=subprocess.run(cmd,cwd=o,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=180)
 steps.append({'label':label,'command':cmd,'returncode':q.returncode});(o/'execution.json').write_text(json.dumps(steps,indent=2)+'\n');print(label,q.returncode,flush=True);assert q.returncode==0
assert 'TAG_CUT_ACTUAL_BASE_PRIORITY_PASS checks=16706'in(o/'simulation.log').read_text();(o/'result.json').write_text(json.dumps({'status':'PASS_ACTUAL_ELABORATED_BASE_ORIGINAL322_PRIORITY_AND_ALL_PACKED_FOURSTATE_FSM','checks':16706,'packed_fs4state':256,'Icarus_force_net_compatibility':True,'no_DUT_functional_or_child_substitutions':True,'hardware':False},indent=2)+'\n')
