import pathlib,subprocess,os,shutil,json,hashlib
R=pathlib.Path(__file__).resolve().parents[1];P=R/'fpga/exports/cpl1-timing-fsmcopy-source-20261105-v002';A=R/'fpga/candidates/cp23-timing-dispatch-20261105/evidence/controller-unit01';E=R/'evidence/hardware-cpl1-timing-20261105T195529Z/model-sensitivity';E.mkdir(exist_ok=False)
for src,name in [(P/'inputs/core/parents/moonshine_sdram_burst.sv','controller.sv'),(P/'sim-inputs/core/parents/sdram_model_bounded.sv','model.sv'),(P/'sim-inputs/sim/support-primitives.sv','primitives.sv')]:shutil.copy2(src,E/name)
tb=(A/'tb_burst.sv').read_text();assert tb.count('sdram_model_burst model(')==1
env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin'+os.pathsep+env.get('PATH','');rows=[]
for flight in [4.0,3.0,2.0,1.0,.5,0.0]:
 label=str(flight).replace('.','p');n=E/label;n.mkdir();s=tb.replace('sdram_model_burst model(',f'sdram_model_burst #(.CLOCK_FLIGHT_NS({flight}),.T_AC_NS(2.0)) model(');(n/'tb.sv').write_text(s)
 cmd=['C:/msys64/ucrt64/bin/iverilog.exe','-g2012','-s','tb_burst','-o',str(n/'test.vvp'),str(E/'controller.sv'),str(E/'model.sv'),str(E/'primitives.sv'),str(n/'tb.sv')]
 q=subprocess.run(cmd,env=env,cwd=n,capture_output=True,text=True);(n/'compile.log').write_text(q.stdout+q.stderr);assert q.returncode==0
 q=subprocess.run(['C:/msys64/ucrt64/bin/vvp.exe','-i',str(n/'test.vvp')],env=env,cwd=n,capture_output=True,text=True);(n/'simulation.log').write_text(q.stdout+q.stderr)
 row=dict(CLOCK_FLIGHT_NS=flight,T_AC_NS=2.0,returncode=q.returncode,log=(q.stdout+q.stderr)[-600:]);rows.append(row);print('MODEL_SENSITIVITY',flight,q.returncode,flush=True)
assert rows[0]['returncode']==0,'Original selected assumptions must still pass'
(E/'results.json').write_text(json.dumps(dict(scope='Isolated functional model timing sensitivity, no hardware timing measurement, no changed image/expectation',sources={p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in E.glob('*.sv')},cases=rows,limits='A sensitive model assumption is a lead, not proof of the hardware failure stage. External flight and device delays have not been measured.'),indent=2)+'\n')
