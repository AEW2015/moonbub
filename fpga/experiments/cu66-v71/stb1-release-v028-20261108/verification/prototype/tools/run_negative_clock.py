from pathlib import Path
import json,subprocess,os,hashlib
p=Path('C:/moon/dev/experiments/staging-burst-v1-20261108');e=p/'evidence/negative-clock01';e.mkdir(exist_ok=True);argv=json.loads((p/'evidence/pins08/execution.json').read_text())[0]['argv'];cmd=list(argv);cmd=[x.replace('COREHALF=5.0','COREHALF=50.0')for x in cmd];cmd[cmd.index('-o')+1]=(e/'invalid.vvp').as_posix();env=dict(os.environ,PATH=str(Path('C:/msys64/ucrt64/bin'))+';'+os.environ['PATH'],TEMP=str(Path('C:/moon/tmp')),TMP=str(Path('C:/moon/tmp')));rows=[]
for label,command in [('compile',cmd),('run',['C:/msys64/ucrt64/bin/vvp.exe',(e/'invalid.vvp').as_posix()])]:
 r=subprocess.run(command,env=env,capture_output=True,text=True,timeout=60);(e/(label+'.log')).write_text(r.stdout+r.stderr);rows.append({'label':label,'argv':command,'returncode':r.returncode})
 if label=='compile':assert r.returncode==0
 else:assert r.returncode!=0 and 'strict ABI3/capability'in r.stdout and 'STAGING_BURST_PINS_PASS'not in r.stdout
(e/'execution.json').write_text(json.dumps(rows,indent=2));(e/'result.json').write_text(json.dumps({'status':'EXPECTED_FAILURE_UNSUPPORTED_READ_CLOCK_ENVELOPE','SPI_MHz':16,'core_MHz':10,'functional_pass':False,'selected_board_core_MHz':100,'no_timing_constraints_changed':True},indent=2))
print((e/'run.log').read_text())
