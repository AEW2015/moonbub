from pathlib import Path
import shutil
p=Path(__file__).resolve().parent
d=p/'history-full-export-v002';d.mkdir();shutil.copyfile(p/'run-xsim-full-synth-executed.py',d/'run-xsim-full-synth-executed.py')
for name in ['run-xsim-full-synth.py','finish-offline-flow.py','prepare-image-gates.py','stage-publication.py']:
 f=p/name;s=f.read_text().replace('dy71-v025-20261107-v002','dy71-v025-20261107-v003').replace('xsim-full-synth01','xsim-full-synth02').replace('board-source-v002','board-source-v003')
 s=s.replace("'pins04'","'pins05'").replace("'legacy04'","'legacy05'")
 f.write_text(s)
for script,folder in [('pin-tests','pins'),('legacy','legacy')]:
 (p/('run-'+script+'-v005.py')).write_text((p/('run-'+script+'-v004.py')).read_text(encoding='utf-8-sig').replace(folder+'04',folder+'05'))
print('PREPARED_V003_POST_SYNTH_AND_CONTROL_GATES')
