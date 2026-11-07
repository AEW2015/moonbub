"""Bind component receipts to the selected image inputs; no hardware access."""
from pathlib import Path
import argparse,hashlib,json,zlib
a=argparse.ArgumentParser();a.add_argument('--build',type=Path,required=True);v=a.parse_args();b=v.build;p=Path(__file__).resolve().parent;sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();freeze=json.loads((b/'source-freeze.json').read_text());assert all(sha(b/'inputs'/n)==h for n,h in freeze.items())
matched=[]
for case in ['pins05','legacy05']:
 assert json.loads((p/case/'result.json').read_text())['status'].startswith('PASS_')
 sf=json.loads((p/case/('source-freeze.json'if case=='pins05'else'result.json')).read_text())
 if case=='legacy05':sf=sf['source_sha256']
 for n,h in sf.items():
  f=Path(n);assert sha(f)==h,(case,n)
  if f.name.startswith('tb_')or f.name in ['dy71_local_control_balanced_v019.sv','cu71_bus_cdc_split.sv']:continue
  targets=[k for k in freeze if Path(k).name==f.name]
  assert len(targets)==1 and freeze[targets[0]]==h,(case,n,targets)
  matched.append((case,f.name,h))
 assert all(x['returncode']==0 for x in json.loads((p/case/'execution.json').read_text()))
fu=json.loads((p/'functional04/result.json').read_text());assert fu['status']=='PASS_CURRENT_BULK_ENGINE_AND_REAL_NATIVE_WORDS'
for n,h in fu['source_sha256'].items():assert sha(p/n)==h
for frame in json.loads((p/'native-gold/result.json').read_text())['frames']:
 words=(p/'native-gold'/('words'+str(frame['frame'])+'.hex')).read_text().split();raw=b''.join(int(w,16).to_bytes(2,'little')for w in words)
 assert len(raw)==frame['bytes'] and hashlib.sha256(raw).hexdigest()==frame['sha256'] and format(zlib.crc32(raw),'08x')==frame['crc32']
# Full-build export is identical in named physical cleanup children.
if 'dy71-v026-'in str(b):
 q=p.parent/'rows-idle-capture-v026/xsim-full-synth01'
else:q=p/'xsim-full-synth02'
x=json.loads((q/'result.json').read_text());assert x['status']=='PASS_XSIM_POST_SYNTH_BULK_NATIVE_WORDS' and x['netlist_sha256']==sha(b/'bulk-funcsim.v')
assert all(row['returncode']==0 for row in json.loads((q/'execution.json').read_text()))
for top,marker in [('tb_hud_bulk_v025','HUD_BULK_PASS'),('tb_native_bulk_v025','NATIVE_BULK_PASS')]:
 text=(q/(top+'-run.log')).read_text();assert marker in text and 'Fatal:'not in text and 'FATAL:'not in text
out=dict(status='PASS_COMPONENT_TESTS_BOUND_TO_SELECTED_IMAGE_INPUTS',build=str(b),source_freeze_sha256=sha(b/'source-freeze.json'),full_export_sha256=sha(b/'bulk-funcsim.v'),matched=matched,hardware=False)
(b/'component-binding-gates.json').write_text(json.dumps(out,indent=2)+'\n');print(out['status'],len(matched))
