from pathlib import Path
import hashlib,json,os,subprocess
p=Path(__file__).resolve().parent;e=p/'reset01';e.mkdir();lib=Path('C:/Xilinx/2025.2/Vivado/data/verilog/src/unisims/BUFG.v');env=dict(os.environ,PATH='C:/msys64/ucrt64/bin;'+os.environ['PATH']);rows=[];sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
for label,cmd in [('compile',['C:/msys64/ucrt64/bin/iverilog.exe','-g2012','-s','tb_reset_bufg','-o',str(e/'test.vvp'),str(lib),str(p/'tb_reset_bufg.sv')]),('run',['C:/msys64/ucrt64/bin/vvp.exe',str(e/'test.vvp')])]:
 q=subprocess.run(cmd,env=env,capture_output=True,text=True);(e/(label+'.log')).write_text(q.stdout+q.stderr);rows.append(dict(label=label,cmd=cmd,returncode=q.returncode));(e/'execution.json').write_text(json.dumps(rows,indent=2));print(label,q.returncode,flush=True);assert q.returncode==0,q.stdout+q.stderr
assert 'RESET_BUFG_UNISIM_PASS'in(e/'run.log').read_text()
(e/'result.json').write_text(json.dumps(dict(status='PASS_ORIGINAL_RESET_STAGES_THROUGH_ACTUAL_BUFG_MODEL',sources_sha256={str(f):sha(f)for f in [lib,p/'tb_reset_bufg.sv',p/'moonshine_top_dy71.sv']},scope='Zero-delay UNISIM functional identity/assert/release sequence; routed reset timing/clock resources/DRC remain mandatory, no physical claim'),indent=2)+'\n')
