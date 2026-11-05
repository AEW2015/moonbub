from pathlib import Path
import subprocess,sys,datetime
p=Path(__file__).resolve().parent
label='physical-'+datetime.datetime.now().strftime('%Y%m%d%H%M%S')
subprocess.run([sys.executable,str(p/'run.py'),'--label',label,'--abort-mode','1'],cwd=p,check=True)
print('SHORT_PHYSICAL_ABORT_PASS')
