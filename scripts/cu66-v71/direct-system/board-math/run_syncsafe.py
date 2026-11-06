"""Whole actual pin-model KEY/P/P with explicit SYNCsafe binding/timeline."""
from pathlib import Path
import sys
timeline=Path(__file__).resolve().parents[1]/'run_timeline.py';s=timeline.read_text()
if '--grouped'not in sys.argv:sys.argv.insert(1,'--grouped')
s=s.replace("script=Path(__file__).with_name('run.py')","script=Path(__file__).resolve().parents[1]/'run.py'")
s=s.replace('source=script.read_text()',"source=script.read_text().replace('parents[3]','parents[4]').replace(' cu71_system_direct #(',' cu71_system_direct_syncsafe #(')")
s=s.replace("m=json.loads((d/'grouped-v001/sources.json').read_text())","m=json.loads((d/'syncsafe-math-v002/sources.json').read_text())")
s=s.replace("d/'sources.json',d/'grouped-v001/sources.json',script,Path(__file__).resolve()","d/'sources.json',d/'syncsafe-math-v002/sources.json',d/'syncsafe-math-v002/derivation.json',Path(__file__).resolve().parents[1]/'run_timeline.py',script,Path(__file__).resolve()")
exec(compile(s,str(timeline),'exec'),globals())
