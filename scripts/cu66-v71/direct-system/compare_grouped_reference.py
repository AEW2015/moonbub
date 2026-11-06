"""Matched actual-reference-copy/LCD component comparison, source/fixture pinned."""
from pathlib import Path
import hashlib,json,re
r=Path(__file__).resolve().parents[3];d=r/'fpga/experiments/cu66-v71/direct-system/grouped-v001';out=d/'comparison-reference-v001.json';assert not out.exists();sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();dirs={'baseline':r/'fpga/experiments/cu66-v71/direct-display/evidence/direct-reference-base0-fast02','grouped':d/'evidence/reference-samebank-fast01'};rows={};proofs={};freezes={}
for name,p in dirs.items():
 freeze=json.loads((p/'source-freeze.json').read_text());freezes[name]=freeze
 for n,h in freeze.items():assert sha(p/n)==h,(name,n)
 res=json.loads((p/'result.json').read_text())
 assert res['front_bank']==0 and res['reference_bank']==0 and res['candidate_bank']==1 and res['hud_candidate_bank']==1 and res['background_reference_copy']and res['owner_variant']=='base'and res['corner']=='fast'
 text=(p/'simulation.log').read_text();fields=['ref_tiles','maxYpage','maxCpage','jobsY','jobsC','trace_events','trace_overflow','firstmiss','readBL8','write_beats','ACT','PRE','refresh','tile_busy','aux_busy','tiles','logical_words','HUDwords','active_cycles','pixels','black_lines','underruns','reads','maxwait'];vals={}
 for field in fields:
  matches=re.findall(r'\b'+re.escape(field)+r'(-?\d+)',text);assert matches,field;vals[field]=int(matches[-1])
 assert vals['pixels']==384000 and vals['trace_overflow']==0
 vals['physical_commands']=vals['readBL8']+vals['write_beats']//8
 vals['ACT_per_physical_command']=vals['ACT']/vals['physical_commands'];vals['PRE_per_physical_command']=vals['PRE']/vals['physical_commands']
 rows[name]=vals
 for f in [p/'result.json',p/'source-freeze.json',p/'simulation.log',p/'execution.json',p/'fixture-source-hashes.json',p/'trace.csv',p/'canonical.hex',p/'hud.hex',p/'gold.hex']:proofs[f.relative_to(r).as_posix()]=sha(f)
assert set(freezes['baseline'])==set(freezes['grouped']);changes=[n for n in freezes['baseline']if freezes['baseline'][n]!=freezes['grouped'][n]];assert changes==['cu71_word_bridge_direct.sv']
for n in ['canonical.hex','hud.hex','gold.hex','fixture-source-hashes.json']:assert sha(dirs['baseline']/n)==sha(dirs['grouped']/n),n
assert rows['baseline']['active_cycles']==rows['grouped']['active_cycles']and rows['baseline']['underruns']==669 and rows['grouped']['underruns']==0
proofs[Path(__file__).resolve().relative_to(r).as_posix()]=sha(Path(__file__).resolve())
out.write_text(json.dumps({'status':'MATCHED_SAME_BANK_REFERENCE_COPY_COMPONENT_GROUPED_ZERO_UNDERRUNS','only_changed_source':changes,'front_reference_bank':0,'candidate_and_HUD_bank':1,'unchanged_inputs':'Identicalcanonical/HUD/nativegoldfixtures,ownerRTL,controller,map,clock/modelcorner,producerdependency','rows':rows,'proofs':proofs,'interpretation':'GroupingservesmorecleanLCDworkandfewerbackgroundcopiesperfixedwindow;rowopensandmaxpagetimesfallbutworstLCDwaitrises. Deadlineimprovementnotaggregate-throughputor30fpsproof.','limits':['TestbenchpreloadsreferenceandHUD;noCU66decoderorESPproof','Candidatefinisheswindowwithoneownedpartialcanonicalread;noindependentcompleted-frameclaim','SparsecandidateHUDwritesarenotfull21120wordHUDpernewframe','NoPHY/mapchange,physicaltimingsignoff,orhardwaretest'],'hardware':False},indent=2)+'\n');print(json.dumps({'output':str(out),'sha256':sha(out),'rows':rows}))
