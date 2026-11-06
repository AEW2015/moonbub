"""Explicit isolated PIPE owner + unchanged grouped backend A/B selection."""
from pathlib import Path
import hashlib,json,sys
r=Path(__file__).resolve().parents[3];d=r/'fpga/experiments/cu66-v71/direct-system';p=d/'pipe-v001';p.mkdir(exist_ok=True);sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();display=r/'fpga/experiments/cu66-v71/direct-display';contract=display/'frozen-port-contract-pipe-v002.json';c=json.loads(contract.read_text())
for n,h in c['sources'].items():assert sha(display/n)==h,n
for name in ['direct-owner-pipe02','direct-pipe-pin-fast01','direct-pipe-pin-slow01']:assert (display/'evidence'/name/'result.json').exists(),name
top=p/'cu71_system_direct_pipe.sv';base=d/'cu71_system_direct.sv'
if not top.exists():
 text=base.read_text();assert text.count('module cu71_system_direct #(')==1 and text.count('    cu71_direct_scanout scanout(')==1
 text=text.replace('module cu71_system_direct #(','module cu71_system_direct_pipe #(').replace('    cu71_direct_scanout scanout(','    cu71_direct_scanout_pipe scanout(');top.write_text(text,newline='\n')
 (p/'derivation.json').write_text(json.dumps({'parent_top':base.relative_to(r).as_posix(),'parent_sha256':sha(base),'candidate_top':top.relative_to(r).as_posix(),'candidate_sha256':sha(top),'only_behavioral_rebinding':'cu71_direct_scanout→cu71_direct_scanout_pipe','owner_source_sha256':sha(display/'cu71_direct_scanout_pipe.sv'),'contract_sha256':sha(contract),'grouped_bridge_unchanged':True,'hardware':False},indent=2)+'\n')
manifest=p/'sources.json'
if not manifest.exists():
 m=json.loads((d/'grouped-v001/sources.json').read_text());m['sources']=[top.relative_to(r).as_posix()if Path(n).name=='cu71_system_direct.sv'else(display/'cu71_direct_scanout_pipe.sv').relative_to(r).as_posix()if Path(n).name=='cu71_direct_scanout.sv'else n for n in m['sources']];m['top']='cu71_system_direct_pipe';m['sources_sha256']={n:sha(r/n)for n in m['sources']};m['scope']='ExplicitPIPEownerwithunchanged8:4groupbackend;nativeA/Bonly,boardtiming/CDCunqualified';manifest.write_text(json.dumps(m,indent=2)+'\n')
if '--grouped'not in sys.argv:sys.argv.insert(1,'--grouped')
timeline=Path(__file__).with_name('run_timeline.py');s=timeline.read_text()
s=s.replace('source=script.read_text()',"source=script.read_text().replace(' cu71_system_direct #(',' cu71_system_direct_pipe #(')")
s=s.replace("m=json.loads((d/'grouped-v001/sources.json').read_text())","m=json.loads((d/'pipe-v001/sources.json').read_text())")
s=s.replace("d/'sources.json',d/'grouped-v001/sources.json',script,Path(__file__).resolve()","d/'sources.json',d/'grouped-v001/sources.json',d/'pipe-v001/sources.json',d/'pipe-v001/derivation.json',Path(__file__).with_name('run_timeline.py'),script,Path(__file__).resolve()")
exec(compile(s,str(timeline),'exec'),globals())
