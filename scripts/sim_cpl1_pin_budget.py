"""Screen actual candidate burst alignment against implementation-derived delays."""
from pathlib import Path
import ast,hashlib,json,os,shutil,subprocess
from cpl1_sdram_models import strict_hold_text
r=Path(__file__).resolve().parents[1]
p=r/'fpga/exports/cpl1-timing-fsmcopy-source-20261105-v002'
c=r/'fpga/candidates/cp23-sdram-capture274p5-20261105-v001'
out=c/'evidence/pin-budget-unit01';out.mkdir(parents=True,exist_ok=False)
shutil.copyfile(c/'inputs/core/parents/moonshine_sdram_burst.sv',out/'controller.sv')
shutil.copyfile(p/'sim-inputs/sim/support-primitives.sv',out/'primitives.sv')
(out/'model.sv').write_text(strict_hold_text((p/'sim-inputs/core/parents/sdram_model_bounded.sv').read_text()))
tree=ast.parse((r/'scripts/sim_cpl1_sdram_alignment.py').read_text())
tb=next(node.value for node in ast.walk(tree)if isinstance(node,ast.Constant)and isinstance(node.value,str)and '`timescale 1ns/1ps\nmodule tb;'in node.value)
assert tb.count('.T_AC_NS(TAC)')==1
env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin'+os.pathsep+env.get('PATH','');results=[]
for name,flight,access,hold,expected_pass in [('fast',.757,2.223,2.223,True),('slow',3.768,8.489,2.223,True),('unbounded-zero-loop',0,2,2,False)]:
    file=out/(name+'.sv');file.write_text(tb.replace('.T_AC_NS(TAC)',f'.T_AC_NS(TAC),.T_OH_NS({hold})'))
    image=out/(name+'.vvp')
    cmd=['C:/msys64/ucrt64/bin/iverilog.exe','-g2012','-s','tb',f'-Ptb.TAC={access}','-o',str(image),
         str(out/'controller.sv'),str(out/'model.sv'),str(out/'primitives.sv'),str(file)]
    q=subprocess.run(cmd,env=env,capture_output=True,text=True);(out/(name+'-compile.log')).write_text(q.stdout+q.stderr);assert q.returncode==0,q.stderr
    q=subprocess.run(['C:/msys64/ucrt64/bin/vvp.exe',str(image),'+PHASE=7.625',f'+FLIGHT={flight}'],env=env,capture_output=True,text=True,timeout=15)
    log=q.stdout+q.stderr;(out/(name+'.log')).write_text(log)
    result=next(line for line in log.splitlines()if line.startswith('ALIGN_RESULT '))
    fields={k:int(v)for k,v in (token.split('=')for token in result.split()[1:])if k.endswith('errors')or k in ['writes','refreshes']}
    assert q.returncode==0 and fields['write_errors']==0 and fields['writes']==96
    assert (fields['read_errors']==0)==expected_pass,(name,fields)
    results.append(dict(name=name,clock_delay_assumption_ns=flight,access_assumption_ns=access,hold_assumption_ns=hold,expected_pass=expected_pass,**fields))
(out/'result.json').write_text(json.dumps(dict(scope='Pin-budget-derived functional model; no measured board delay or hardware proof',
    baseline_report='capture135-v001/evidence/io-window-screen03/input-setup.rpt and input-hold.rpt',
    derivation='slow: SCD-DCD=8.774-5.006=3.768, access=7+1.489; fast: 2.795-2.038=.757, hold/access=2+.223',
    source_sha256=hashlib.sha256((out/'controller.sv').read_bytes()).hexdigest(),cases=results),indent=2)+'\n')
print('PIN_BUDGET_UNIT_PASS realistic_pairs=2/2 required_outside-envelope_failure=1')
