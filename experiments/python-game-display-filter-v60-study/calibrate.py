"""Freeze one preset using only first24 fixed-zero source trajectories."""
from pathlib import Path
import hashlib,json,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def build():
 source=json.loads((HERE/'results.json').read_text());cases=[c for c in source['cases'] if c['kind']=='custom' and c['policy']=='zero'];assert len(cases)==4;rows=[]
 for index in range(4):
  presets=[c['presets'][index] for c in cases];assert all(p['preset']==presets[0]['preset'] for p in presets);sse=sum(p['summary']['active_SSE'] for p in presets);samples=sum(p['summary']['active_samples'] for p in presets);rows.append(dict(preset=presets[0]['preset'],active_SSE=sse,active_samples=samples,active_MSE=sse/samples))
 chosen=min(range(4),key=lambda i:rows[i]['active_SSE']);paths=(HERE/'model.py',HERE/'results.json',HERE/'calibrate.py')
 return dict(schema='gamebub-display-filter-v60-calibration',source_sha256={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},calibration_cohorts=[c['scene'] for c in cases],source_IDs=list(range(24)),objective='sum original RGB565 active SSE over ONLY fixed-zero first24 trajectories; tie fixed preset order',candidates=rows,selected_preset=rows[chosen]['preset'],scope=['Notchosennative/mixedresults;nodatafromsourceIDs24–47usedbyselector.','Presetfrozenbeforeadditionaltemporalfilterevaluation;notgloballyunseenmediacalibration.','Noencoder/referencechanges,encodedbytesavings,FPGAfit,subjectivequalityorphysicalFPSproof.'])
def main():
 d=build();p=HERE/'calibration.json'
 if '--check'in sys.argv:assert json.loads(p.read_text())==d
 else:p.write_text(json.dumps(d,indent=2)+'\n')
 print(json.dumps(dict(selected=d['selected_preset'],candidates=d['candidates'])),flush=True)
if __name__=='__main__':main()
