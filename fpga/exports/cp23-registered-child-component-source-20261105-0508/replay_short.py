from pathlib import Path
import subprocess,sys,datetime
p=Path(__file__).resolve().parent
label=datetime.datetime.now().strftime('%Y%m%d%H%M%S')
for helper,args in [('run.py',['--abort-mode','1']),('run_probe.py',['--private-error','4'])]:
 subprocess.run([sys.executable,str(p/helper),'--label',label+'-'+helper.replace('.py',''),*args],cwd=p,check=True)
print('SHORT_PHYSICAL_ABORT_AND_DRAIN_PASS')
