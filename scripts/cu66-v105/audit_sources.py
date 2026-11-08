#!/usr/bin/env python3
"""Offline V105 source and functional evidence audit.

This tool verifies pinned source provenance, exact edit-recipe recovery,
composable admission/memory edits, and retained functional receipts. It never
launches simulations, compilers, synthesis, or vendor tools. Missing planned
receipts remain PENDING; malformed or contradictory evidence is FAIL.
"""
from __future__ import annotations
import gzip
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[2]
BASELINE='afc073e36f813cbcedaec9b21b61cda239453a5b'
PROFILE='experiments/python-gamebub-v99/profile.json'
PROFILE_SHA='8e17b24afbefe32ca00b2606ee80a3a70dd06e9050e76d50c9698fd524e735be'
INVENTORY='experiments/python-gamebub-v100/inventory.json'
REGRESS='scripts/cu66-v105/regress.py'
COMPOSE='scripts/cu66-v105/compose.py'
OUT=ROOT/'experiments/python-gamebub-v105/source-audit.json'
DOC=ROOT/'docs/cu66-v105/source-audit.md'

LANES={
 'admission_fresh':('admission','fresh',24,52),
 'admission_canonical':('admission','canonical',88,84),
 'memory_fresh':('memory','fresh',24,52),
 'memory_canonical':('memory','canonical',88,84),
 'geometry_canonical':('geometry','canonical',88,84),
 'combined_canonical':('combined','canonical',88,84),
 'locality_fresh':('locality','fresh',24,52),
 'locality_canonical':('locality','canonical',88,84),
}
RECIPES={
 'admission':{'recipe':'fpga/experiments/cu66-v105-admission/edit-recipe.json','candidate':'fpga/experiments/cu66-v105-admission/cs88_admission_v91i2a.sv','module':'cs88_admission_v91i2a','adapter':'fpga/experiments/cu66-v105-admission/adapter.json','ports':'fpga/experiments/cu66-v105-admission/ports.json'},
 'memory':{'recipe':'fpga/experiments/cu66-v105-memory/edit-proof.json','candidate':'fpga/experiments/cu66-v105-memory/cs88_admission_v91i2a.sv','module':'cs88_admission_v91i2a'},
}
BASE_SOURCE='fpga/experiments/cu66-v102-memory/cs88_admission_v91i2a.sv'
BASELINE_OVERRIDES={'fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv':'fpga/experiments/cu66-v102-memory/cs88_admission_v91i2a.sv','fpga/experiments/cu66-v91k/cu66_reconstruct_stream_v91k.sv':'fpga/experiments/cu66-v102-predicate/cu66_reconstruct_stream_v91k.sv'}
V104_CONTROL='fpga/experiments/cu66-v104-control/cu66_reconstruct_stream_v91k.sv'
V104_DSP='fpga/experiments/cu66-v104-dsp/cu66_dequant.sv'
V102_PREDICATE='fpga/experiments/cu66-v102-predicate/cu66_reconstruct_stream_v91k.sv'
V69_DSP='fpga/experiments/cu66-v69/inverse/cu66_dequant.sv'

checks:list[dict[str,Any]]=[]; errors:list[str]=[]; pending:list[str]=[]; inputs:dict[str,str]={}
def sha(data:bytes)->str:return hashlib.sha256(data).hexdigest()
def record(path:str,data:bytes)->bytes:inputs[path]=sha(data);return data
def read(path:str)->bytes:return record(path,(ROOT/path).read_bytes())
def read_json(path:str)->Any:return json.loads(read(path))
def check(name:str,ok:bool,detail:Any=None)->None:
 checks.append({'name':name,'status':'PASS' if ok else 'FAIL','detail':detail})
 if not ok:errors.append(name)
def need(name:str,detail:Any=None)->None:checks.append({'name':name,'status':'PENDING','detail':detail});pending.append(name)
def git_blob(rev:str,path:str)->bytes|None:
 p=subprocess.run(['git','-C',str(ROOT),'show',f'{rev}:{path}'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
 if p.returncode:return None
 return record(f'git/{rev}/{path}',p.stdout)
def git_ok(*args:str)->bool:return subprocess.run(['git','-C',str(ROOT),*args],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=False).returncode==0
def mod_header(src:bytes,module:str)->bytes:
 pos=src.find(('module '+module).encode()); end=src.find(b');',pos)
 if pos<0 or end<0:raise ValueError('module header missing: '+module)
 return src[pos:end+2]
def apply_recipe(source:bytes,recipe:dict[str,Any])->tuple[bytes,list[dict[str,Any]]]:
 out=source;ledger=[]
 for n,row in enumerate(recipe.get('edits',[])):
  before=row['before'].encode();after=row['after'].encode();expected=row.get('expected_occurrences',row.get('occurrences',1));actual=out.count(before)
  if actual!=expected:raise ValueError(f"edit {n}/{row.get('name')} occurrence mismatch {actual}!={expected}")
  out=out.replace(before,after,expected);ledger.append({'name':row.get('name'), 'expected_occurrences':expected,'actual_occurrences':actual})
 return out,ledger

def audit_baseline()->dict[str,Any]:
 exists=git_ok('cat-file','-e',f'{BASELINE}^{{commit}}');ancestor=exists and git_ok('merge-base','--is-ancestor',BASELINE,'HEAD')
 check('baseline_exists_and_is_ancestor',exists and ancestor,{'baseline':BASELINE,'exists':exists,'ancestor_of_HEAD':ancestor})
 try:
  profile=json.loads(read(PROFILE));raw=read(PROFILE);blob=git_blob(BASELINE,PROFILE);geometry=profile.get('geometry',{});cap=profile.get('parameters',{}).get('complete_packet_cap_bytes_including_outer_CRC')
  contract=(geometry.get('coded_width')==720 and geometry.get('coded_height')==480 and cap==49152)
  check('v99_profile_frozen',sha(raw)==PROFILE_SHA and raw==blob and contract,{'sha256':sha(raw),'expected':PROFILE_SHA,'baseline_blob_equal':raw==blob,'coded_width':geometry.get('coded_width'),'coded_height':geometry.get('coded_height'),'packet_cap_bytes':cap})
 except Exception as e:check('v99_profile_frozen',False,{'error':str(e)})
 try:
  inv=read_json(INVENTORY);mismatch=[];missing=[];diff=[]
  for r in inv.get('source_files',[]):
   p=r.get('path','')
   try:d=read(p)
   except Exception:missing.append(p);continue
   if sha(d)!=r.get('sha256'):mismatch.append(p)
   if git_blob(BASELINE,p)!=d:diff.append(p)
  check('historical_v100_source_inventory_unchanged',bool(inv.get('source_files')) and not(mismatch or missing or diff),{'count':len(inv.get('source_files',[])),'hash_mismatches':mismatch,'missing':missing,'baseline_blob_differences':diff})
 except Exception as e:check('historical_v100_source_inventory_unchanged',False,{'error':str(e)})
 try:
  selection=read_json('experiments/python-gamebub-v104/selection.json');pins=[]
  for path,expected in selection['source_sha256'].items():
   data=read(path);blob=git_blob(BASELINE,path);pins.append({'path':path,'sha256':sha(data),'expected':expected,'matches_selection':sha(data)==expected,'matches_baseline':data==blob})
  check('selected_v102_baseline_source_pins',all(x['matches_selection'] and x['matches_baseline'] for x in pins),{'selection_path':'experiments/python-gamebub-v104/selection.json','selected_variant':selection.get('selected_variant'),'source_pins':pins})
 except Exception as e:check('selected_v102_baseline_source_pins',False,{'error':str(e)})
 try:
  sa=read_json('experiments/python-gamebub-v104/source-audit.json');na=read_json('experiments/python-gamebub-v104/native-audit.json')
  source_pass=sum(c.get('status')=='PASS' for c in sa.get('checks',[]));native_pass=sum(c.get('status')=='PASS' for c in na.get('checks',[]))
  ok=(sa.get('status')=='PASS_EVIDENCE' and source_pass==22 and len(sa.get('checks',[]))==22 and na.get('status')=='PASS_EVIDENCE' and native_pass==4 and len(na.get('checks',[]))==4 and not na.get('pending_variants'))
  check('retained_v104_source_and_native_evidence',ok,{'source_status':sa.get('status'),'source_checks_pass':source_pass,'source_checks_total':len(sa.get('checks',[])),'native_status':na.get('status'),'native_checks_pass':native_pass,'native_checks_total':len(na.get('checks',[])),'native_pending_variants':na.get('pending_variants')})
 except Exception as e:check('retained_v104_source_and_native_evidence',False,{'error':str(e)})
 return {'baseline':BASELINE,'profile':PROFILE,'inventory':INVENTORY}

def audit_recipe(kind:str)->dict[str,Any]|None:
 cfg=RECIPES[kind];rp=cfg['recipe']
 try:
  rec=read_json(rp); candidate=read(cfg['candidate'])
  if kind=='admission':
   op=rec.get('originalpath');cp=rec.get('candidatepath');oh=rec.get('originalhash');ch=rec.get('candidatehash')
  else:
   op=rec.get('original_path');cp=rec.get('candidate_path');oh=rec.get('original_sha256');ch=rec.get('candidate_sha256')
  original=read(op);baseline=git_blob(BASELINE,op);recovered,ledger=apply_recipe(original,rec)
  expected_edits=13 if kind=='admission' else 7
  required_names=({'cached_coordinate_declarations','helper_insert','residual_index','kill_invalidate','qualified_header_initialize','key_plane_reset','key_advance','mixed_advance','empty_group_jump','copy_or_hidden_advance','all_residual_advance','predictive_plane_reset','mode_end_invalidate'} if kind=='admission' else {'canonical-mode-write-read-port','move-only-mode-lookup','extract-clear','extract-key','extract-mixed','extract-group-hidden-copy','extract-group-residual'})
  edit_names={e.get('name') for e in rec.get('edits',[])}
  ok=(op==BASE_SOURCE and cp==cfg['candidate'] and sha(original)==oh and original==baseline and sha(candidate)==ch and recovered==candidate and rec.get('schema')=='v105-edit-recipe-v1' and len(rec.get('edits',[]))==expected_edits and edit_names==required_names)
  check(f'{kind}_recipe_exact_recovery_and_baseline',ok,{'recipe':rp,'candidate':cfg['candidate'],'original':op,'candidate_sha256':sha(candidate),'recipe_candidate_sha256':ch,'original_sha256':sha(original),'baseline_original_equal':original==baseline,'reconstructed_candidate_equal':recovered==candidate,'edit_ledger':ledger})
  headok=mod_header(candidate,cfg['module'])==mod_header(original,cfg['module'])
  if kind=='admission':
   ports=read_json(cfg['ports']);port_names=[x.get('name') for x in ports]
   check('admission_public_header_and_port_ledger_unchanged',headok and len(port_names)==64 and len(set(port_names))==64,{'header_unchanged':headok,'production_port_count':len(port_names),'unique_names':len(set(port_names))})
   am=read_json(cfg['adapter']);adapter_results=[]
   for fl in ('original','candidate'):
    p=f"fpga/experiments/cu66-v105-admission/admission_{fl}.sv";a=read(p)
    a=a.replace(f'module admission_{fl} ('.encode(),f'module {cfg["module"]} ('.encode(),1)
    a=a.replace(am['extra_ports'].encode(),b'\n);',1)
    a=a.replace(am['assignments'][fl].encode(),b'',1)
    target=original if fl=='original' else candidate
    adapter_results.append({'path':p,'exact_after_probe_removal':a==target})
   check('admission_verification_adapters_exact',all(x['exact_after_probe_removal'] for x in adapter_results),{'adapters':adapter_results})
  else:
   check('memory_public_header_unchanged',headok,{'header_unchanged':headok})
  return {'candidate':candidate,'original':original,'recipe':rec,'recipe_path':rp,'candidate_path':cfg['candidate'],'original_path':op,'candidate_sha256':sha(candidate),'original_sha256':sha(original)}
 except Exception as e:
  check(f'{kind}_recipe_exact_recovery_and_baseline',False,{'recipe':rp,'error':str(e)});return None

def audit_composition(recipes:dict[str,Any])->dict[str,Any]:
 if not all(k in recipes for k in ('admission','memory')):
  need('admission_memory_both_order_composition',{'reason':'both exact recipes must pass first'});return {}
 try:
  base=recipes['admission']['original'];ra=recipes['admission']['recipe'];rm=recipes['memory']['recipe']
  am,_=apply_recipe(base,ra); am,_=apply_recipe(am,rm)
  ma,_=apply_recipe(base,rm); ma,_=apply_recipe(ma,ra)
  ok=am==ma
  check('admission_memory_both_order_composition',ok,{'admission_then_memory_sha256':sha(am),'memory_then_admission_sha256':sha(ma),'byte_identical':ok})
  # When the root composition artifact exists, require exact match to both independently derived orders.
  proofpath='experiments/python-gamebub-v105/composition.json'
  if not (ROOT/proofpath).is_file():need('composition_emitted_source_matches_both_orders',{'expected_proof':proofpath,'expected_sha256':sha(am)})
  else:
   proof=read_json(proofpath);source_path=proof.get('candidate')
   if not source_path or not (ROOT/source_path).is_file():need('composition_emitted_source_matches_both_orders',{'proof':proofpath,'source_path':source_path})
   else:
    emitted=read(source_path);order_rows=proof.get('orders',[]);order_hashes={tuple(r.get('order',[])):r.get('sha256') for r in order_rows}
    proof_orders=(order_hashes.get(('admission','memory'))==sha(am) and order_hashes.get(('memory','admission'))==sha(ma))
    passed=(proof.get('schema')=='v105-both-order-composition-v1' and proof.get('status')=='PASS' and proof.get('both_orders_identical') is True and proof.get('module_header_byte_identical') is True and proof_orders and proof.get('candidate_sha256')==sha(emitted) and mod_header(emitted,'cs88_admission_v91i2a')==mod_header(base,'cs88_admission_v91i2a') and emitted==am and source_path=='fpga/experiments/cu66-v105-composed/cs88_admission_v91i2a.sv')
    check('composition_emitted_source_matches_both_orders',passed,{'proof':proofpath,'source':source_path,'source_sha256':sha(emitted),'independent_sha256':sha(am),'proof_order_hashes':{str(k):v for k,v in order_hashes.items()},'proof_orders_match':proof_orders})
  return {'integrated_bytes_sha256':sha(am),'orders_byte_identical':ok}
 except Exception as e:check('admission_memory_both_order_composition',False,{'error':str(e)});return {}

def audit_v104_candidates()->None:
 # Retained, already audited V104 building blocks used by geometry/combined/locality.
 for name,candidate,original,module,manifest in [
  ('geometry',V104_CONTROL,V102_PREDICATE,'cu66_reconstruct_stream_v91k','fpga/experiments/cu66-v104-control/change.json'),
  ('dsp',V104_DSP,V69_DSP,'cu66_dequant','fpga/experiments/cu66-v104-dsp/change.json')]:
  try:
   cand=read(candidate);orig=read(original);m=read_json(manifest);blob=git_blob(BASELINE,original)
   ok=sha(cand)==m.get('candidate_sha256') and sha(orig)==m.get('original_sha256') and orig==blob and mod_header(cand,module)==mod_header(orig,module)
   check(f'v104_{name}_candidate_pins_and_public_header',ok,{'candidate':candidate,'candidate_sha256':sha(cand),'manifest_candidate_sha256':m.get('candidate_sha256'),'original_sha256':sha(orig),'original_baseline_equal':orig==blob,'public_header_equal':mod_header(cand,module)==mod_header(orig,module)})
  except Exception as e:check(f'v104_{name}_candidate_pins_and_public_header',False,{'error':str(e)})

def audit_focused_receipt(kind:str)->None:
 if kind=='admission':
  summary_path='experiments/python-gamebub-v105/admission/results.json';schema='v105-admission-clocked-coordinate-v1';sidecar='experiments/python-gamebub-v105/admission/trace-audit.json'
 elif kind=='memory':
  summary_path='experiments/python-gamebub-v105/memory/probe-results.json';schema='v105-modes-probe-selection-v1';sidecar='experiments/python-gamebub-v105/memory/trace-audit.json'
 if not (ROOT/summary_path).is_file():need(f'focused_{kind}_receipt',{'expected':summary_path});return
 try:
  summary=read_json(summary_path)
  if kind=='memory':
   selected=summary['selected_receipt'];expected_sha=summary.get('sha256')
  else:
   selected=summary.get('selected_report') or summary_path;expected_sha=summary.get('selected_report_sha256')
  if not (ROOT/selected).is_file():need(f'focused_{kind}_selected_receipt',{'selected':selected});return
  attempt=read_json(selected);errors_local=[];attempt_dir=(ROOT/selected).parent
  expected_attempt_schema='v105-modes-clocked-probe-v1' if kind=='memory' else 'v105-admission-clocked-coordinate-v1'
  expected_summary_schema='v105-modes-probe-selection-v1' if kind=='memory' else expected_attempt_schema
  if attempt.get('schema')!=expected_attempt_schema or summary.get('schema')!=expected_summary_schema:errors_local.append('schema')
  if attempt.get('status') not in (('PASS_ACTUAL_CLOCKED_MODE_EQUIVALENCE',) if kind=='memory' else ('PASS', 'PASS_ACTUAL_CLOCKED_COORDINATE')):errors_local.append('status')
  if attempt.get('baseline')!=BASELINE and attempt.get('baseline_revision')!=BASELINE:errors_local.append('baseline')
  for src,h in attempt.get('source_sha256',{}).items():
   try:
    if sha(read(src))!=h:errors_local.append('source:'+src)
   except Exception:errors_local.append('missing-source:'+src)
  artifacts=attempt.get('artifacts_sha256',{});bad=[]
  for rel,h in artifacts.items():
   try:d=record(str((attempt_dir/rel).relative_to(ROOT)),(attempt_dir/rel).read_bytes())
   except Exception:bad.append({'path':rel,'reason':'missing'});continue
   if sha(d)!=h:bad.append({'path':rel,'reason':'sha256'})
  if bad:errors_local.append('artifacts')
  if kind=='memory':
   if expected_sha and sha(read(selected))!=expected_sha:errors_local.append('selected_receipt_sha256')
   if attempt.get('candidate',{}).get('path')!=RECIPES['memory']['candidate'] or attempt.get('candidate',{}).get('sha256')!=sha(read(RECIPES['memory']['candidate'])):errors_local.append('candidate-pin')
   if attempt.get('original',{}).get('path')!=BASE_SOURCE or attempt.get('original',{}).get('sha256')!=sha(read(BASE_SOURCE)):errors_local.append('original-pin')
   if [r.get('seed') for r in attempt.get('runs',[])]!=[105401,105402] or any(r.get('status')!='TEST_PASS' for r in attempt.get('runs',[])):errors_local.append('runs')
   if attempt.get('total_cases')!=316440 or attempt.get('total_clock_edges')!=316442 or attempt.get('output_names')!=42 or attempt.get('port_names')!=64:errors_local.append('coverage')
   compile_rows=[c for c in attempt.get('commands',[]) if '--build' in c.get('argv',[]) and '--cc' in c.get('argv',[])]
   strict=len(compile_rows)==1 and all(c.get('exit_code')==0 and '--assert' in c.get('argv',[]) and '-Wall' in c.get('argv',[]) and '-Werror' in ' '.join(c.get('argv',[])) for c in compile_rows)
   for c in compile_rows:
    lp=attempt_dir/c.get('log','')
    try:
     logbytes=lp.read_bytes();record(str(lp.relative_to(ROOT)),logbytes)
     if b'%Warning-' in logbytes:strict=False
    except Exception:strict=False
   if not strict:errors_local.append('strict-compile')
  else:
   cand=attempt.get('candidate',{});orig=attempt.get('original',{})
   if cand.get('path')!=RECIPES['admission']['candidate'] or cand.get('sha256')!=sha(read(RECIPES['admission']['candidate'])):errors_local.append('candidate-pin')
   if attempt.get('source_sha256',{}).get(BASE_SOURCE)!=sha(read(BASE_SOURCE)):errors_local.append('original-source-pin')
   verdict=attempt.get('terminal_verdict',{});replay=attempt.get('trace_replay',{})
   if attempt.get('actual_RTL_run') is not True or verdict.get('status')!='TEST_PASS' or attempt.get('strict_warnings') is not True or attempt.get('assertions_disabled_or_downgraded') is not False or attempt.get('complete_production_body_preserved_by_adapters') is not True or verdict.get('cases')!=86 or verdict.get('positive_cases')!=52 or verdict.get('negative_cases')!=34 or verdict.get('directed_checks')!=22 or replay.get('status')!='PASS' or replay.get('rows')!=1352010 or replay.get('active_bits_compared')!=116100:errors_local.append('functional-verdict')
   compile_rows=[c for c in attempt.get('commands',[]) if '--cc' in c.get('argv',[]) and '--build' in c.get('argv',[])]
   strict=len(compile_rows)==1 and all(c.get('exit_code')==0 and '--assert' in c.get('argv',[]) and '-Wall' in c.get('argv',[]) and '-Werror' in ' '.join(c.get('argv',[])) for c in compile_rows)
   for c in compile_rows:
    logname=c.get('log') or ('compile.log' if kind=='admission' else '')
    lp=attempt_dir/logname if logname else None
    try:
     if lp is None:raise FileNotFoundError('compile log path absent')
     logbytes=lp.read_bytes();record(str(lp.relative_to(ROOT)),logbytes)
     if b'%Warning-' in logbytes:strict=False
    except Exception:strict=False
   if not strict:errors_local.append('strict-compile')
   trace=attempt_dir/'trace.jsonl.gz'
   try:
    tgz=trace.read_bytes();raw=gzip.decompress(tgz)
    if sha(raw)!=attempt.get('raw_trace_sha256') or sha(tgz)!=artifacts.get('trace.jsonl.gz'):errors_local.append('trace-digest')
   except Exception:errors_local.append('trace-missing-or-invalid')
  if not (ROOT/sidecar).is_file():need(f'focused_{kind}_independent_trace_audit',{'expected':sidecar,'selected_receipt':selected})
  else:
   aud=read_json(sidecar); auditor=aud.get('auditor',{});ap=auditor.get('path');expected=auditor.get('sha256')
   if not ap or not expected or sha(read(ap))!=expected:errors_local.append('trace-auditor-pin')
   if kind=='memory':
    aruns=aud.get('runs',[]);rruns=attempt.get('runs',[])
    sidecar_bound=(aud.get('receipt')==selected and aud.get('receipt_sha256')==sha(read(selected)) and aud.get('status')=='PASS_INDEPENDENT_MODE_REPLAY' and len(aud.get('checks',[]))==4 and all(c.get('status')=='PASS' for c in aud.get('checks',[])) and [x.get('seed') for x in aruns]==[105401,105402] and len(rruns)==2 and all(x.get('status')=='PASS' and x.get('all_valid_read_addresses')==8100 and x.get('final_store_entries')==8100 for x in aruns) and [x.get('trace_sha256') for x in aruns]==[attempt.get('artifacts_sha256',{}).get('seed-%d.jsonl.gz'%x.get('seed')) for x in aruns])
   else:
    sr=aud.get('selected_receipt',{});ss=aud.get('selected_summary',{});tr=attempt_dir/'trace.jsonl.gz'
    try:trace_gz=tr.read_bytes();trace_raw=gzip.decompress(trace_gz)
    except Exception:trace_gz=trace_raw=b''
    sidecar_bound=(sr.get('path')==selected and sr.get('sha256')==sha(read(selected)) and ss.get('path')==summary_path and ss.get('sha256')==sha(read(summary_path)) and aud.get('status')=='PASS' and aud.get('trace_sha256')==sha(trace_gz) and aud.get('raw_trace_sha256')==sha(trace_raw) and aud.get('rows')==1352010 and aud.get('residual_marks')==530288 and aud.get('active_bits_compared')==116100 and aud.get('end_sentinels')==473 and aud.get('group_jumps')==300)
   if not sidecar_bound:errors_local.append('trace-audit-sidecar')
  check(f'focused_{kind}_receipt_and_independent_trace_audit',not errors_local,{'summary':summary_path,'selected_receipt':selected,'attempt_schema':attempt.get('schema'),'attempt_status':attempt.get('status'),'source_and_artifact_errors':errors_local,'artifact_count':len(artifacts)})
 except Exception as e:check(f'focused_{kind}_receipt_and_independent_trace_audit',False,{'error':str(e)})

def audit_lanes()->None:
 for name,(variant,mode,cases,directed) in LANES.items():
  summary_path=f'experiments/python-gamebub-v105/regression/{variant}/{mode}/results.json'
  if not (ROOT/summary_path).is_file():need(f'lane_{name}',{'expected':summary_path,'case_profile_runs':cases,'directed_checks':directed,'seeds':[105401,105402]});continue
  try:
   summary=read_json(summary_path);selected=summary.get('selected_report')
   if not selected or not (ROOT/selected).is_file():need(f'lane_{name}_selected_attempt',{'summary':summary_path,'selected_report':selected});continue
   attempt=read_json(selected);ad=(ROOT/selected).parent;bad_art=[];bad_src=[]
   for rel,h in attempt.get('artifacts_sha256',{}).items():
    p=ad/rel
    try:d=p.read_bytes();record(str(p.relative_to(ROOT)),d)
    except Exception:bad_art.append({'path':rel,'reason':'missing'});continue
    if sha(d)!=h:bad_art.append({'path':rel,'reason':'sha256'})
   source_rows=attempt.get('source_sha256',{})
   expected_candidates={
    'admission':{'fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv':'fpga/experiments/cu66-v105-admission/cs88_admission_v91i2a.sv'},
    'memory':{'fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv':'fpga/experiments/cu66-v105-memory/cs88_admission_v91i2a.sv'},
    'geometry':{'fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv':'fpga/experiments/cu66-v105-admission/cs88_admission_v91i2a.sv','fpga/experiments/cu66-v91k/cu66_reconstruct_stream_v91k.sv':V104_CONTROL},
    'combined':{'fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv':'fpga/experiments/cu66-v105-admission/cs88_admission_v91i2a.sv','fpga/experiments/cu66-v91k/cu66_reconstruct_stream_v91k.sv':V104_CONTROL,'fpga/experiments/cu66-v69/inverse/cu66_dequant.sv':V104_DSP},
    'locality':{'fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv':'fpga/experiments/cu66-v105-composed/cs88_admission_v91i2a.sv','fpga/experiments/cu66-v91k/cu66_reconstruct_stream_v91k.sv':V104_CONTROL,'fpga/experiments/cu66-v69/inverse/cu66_dequant.sv':V104_DSP},
   }[variant]
   candidate_rows={r.get('original'):r.get('path') for r in attempt.get('candidates',[])}
   candidate_map_ok=candidate_rows==expected_candidates
   for src,h in source_rows.items():
    try:
     if sha(read(src))!=h:bad_src.append({'path':src,'reason':'sha256'})
    except Exception:bad_src.append({'path':src,'reason':'missing'})
   runs=attempt.get('runs',[]);seeds=[r.get('seed') for r in runs];equal=True;verdicts=[]
   for r in runs:
    seed=r.get('seed');eq=r.get('equalities',{});equal &= eq.get('stdout') is True and eq.get('events') is True and (mode!='canonical' or eq.get('canonical') is True)
    for suffix in ('simulation.jsonl',):
     pa=ad/f'baseline-{seed}-{suffix}';pb=ad/f'candidate-{seed}-{suffix}'
     try:
      aa=pa.read_bytes();bb=pb.read_bytes();record(str(pa.relative_to(ROOT)),aa);record(str(pb.relative_to(ROOT)),bb);equal &= aa==bb
     except Exception:equal=False
    for field in ('events',)+(('canonical_actual',) if mode=='canonical' else ()):
     field_bytes={}
     for side in ('baseline','candidate'):
      meta=r.get('variants',{}).get(side,{}).get(field)
      if mode=='canonical' and field=='canonical_actual' and not meta:equal=False
      if meta:
       p=ad/meta.get('path','')
       try:
        z=p.read_bytes();raw=gzip.decompress(z);record(str(p.relative_to(ROOT)),z);field_bytes[side]=(z,raw)
        equal &= sha(z)==meta.get('sha256') and sha(raw)==meta.get('raw_sha256')
       except Exception:equal=False
     if len(field_bytes)==2:equal &= field_bytes['baseline']==field_bytes['candidate']
    for side in ('baseline','candidate'):
     v=r.get('variants',{}).get(side,{}).get('verdict',{});verdicts.append({'seed':seed,'side':side,'status':v.get('status'),'cases':v.get('cases'),'directed_checks':v.get('directed_checks')})
     equal &= v.get('status')=='TEST_PASS' and v.get('cases')==(6 if mode=='fresh' else 22) and v.get('directed_checks')==(13 if mode=='fresh' else 21)
   strict_rows=[c for c in attempt.get('commands',[]) if '--cc' in c.get('argv',[]) and '--build' in c.get('argv',[])]
   strict=len(strict_rows)==2 and all(c.get('exit_code')==0 and '--assert' in c.get('argv',[]) and '-Wall' in c.get('argv',[]) and '-Werror' in ' '.join(c.get('argv',[])) for c in strict_rows) and attempt.get('assertions_disabled_or_downgraded') is False
   for c in strict_rows:
    lp=ad/c.get('log','')
    try:
     lb=lp.read_bytes();record(str(lp.relative_to(ROOT)),lb)
     if b'%Warning-' in lb:strict=False
    except Exception:strict=False
   for row in attempt.get('candidates',[]):
    path=row.get('path');expected=row.get('sha256')
    if not path or source_rows.get(path)!=expected:candidate_map_ok=False
   ok=(summary.get('status')=='PASS' and attempt.get('status')=='PASS' and attempt.get('baseline_revision')==BASELINE and attempt.get('baseline_overrides')==BASELINE_OVERRIDES and attempt.get('variant')==variant and attempt.get('mode')==mode and attempt.get('case_profile_runs')==cases and attempt.get('directed_checks')==directed and attempt.get('actual_RTL_run') is True and seeds==[105401,105402] and equal and strict and candidate_map_ok and not bad_art and not bad_src)
   if attempt.get('status') in ('FAIL','ERROR'):errors.append(f'lane_{name}_terminal_failure')
   check(f'lane_{name}_paired_exact_receipt',ok,{'summary':summary_path,'selected_attempt':selected,'case_profile_runs':attempt.get('case_profile_runs'),'directed_checks':attempt.get('directed_checks'),'seeds':seeds,'paired_equalities':equal,'terminal_verdicts':verdicts,'strict_compile':strict,'baseline_overrides':attempt.get('baseline_overrides'),'baseline_overrides_match':attempt.get('baseline_overrides')==BASELINE_OVERRIDES,'candidate_source_map':candidate_rows,'expected_candidate_source_map':expected_candidates,'candidate_map_matches':candidate_map_ok,'source_mismatches':bad_src,'artifact_mismatches':bad_art})
  except Exception as e:check(f'lane_{name}_paired_exact_receipt',False,{'error':str(e)})

def main()->int:
 meta=audit_baseline();recipes={k:audit_recipe(k) for k in RECIPES};composition=audit_composition({k:v for k,v in recipes.items() if v});audit_v104_candidates()
 audit_focused_receipt('admission');audit_focused_receipt('memory');audit_lanes()
 status='FAIL' if errors else ('PENDING' if pending else 'PASS_EVIDENCE')
 auditor='scripts/cu66-v105/audit_sources.py';auditor_sha=sha(read(auditor))
 out={'schema':'v105-source-functional-audit-v1','status':status,'baseline_revision':BASELINE,'auditor':{'path':auditor,'sha256':auditor_sha},'checks':checks,'errors':sorted(set(errors)),'pending':pending,'composition':composition,'candidate_sources':{k:{'path':v['candidate_path'],'sha256':v['candidate_sha256'],'original':v['original_path'],'original_sha256':v['original_sha256']} for k,v in recipes.items() if v},'input_sha256':dict(sorted(inputs.items())),'scope':'Independent source provenance, exact-recipe composition, and retained component-functional evidence. Does not prove full formal equivalence, mapped timing, board service, hardware frame rate, or product qualification.'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
 lines=['# V105 source and functional audit','',f'**Status: `{status}`.** This offline audit does not compile or simulate RTL and does not run vendor flows.','', '## Verified contract','',f'- Baseline `{BASELINE}` is checked as an existing ancestor of HEAD.','- V99 q16 profile and V100 historical RTL inventory are pinned to their baseline Git contents.','- Both admission and memory candidates must be reconstructed byte-for-byte from exact edit recipes over the selected V102 memory source.','- The auditor independently applies admission then memory edits and memory then admission edits; both orders must produce identical source bytes and match the emitted integration source.','- Candidate headers/ports, verification adapters, selected V104 geometry/DSP source pins, focused receipts, and all eight required pipeline lanes are checked.','- The required matrix is admission fresh/canonical, memory fresh/canonical, geometry canonical, combined canonical, and locality fresh/canonical at seeds 105401 and 105402. Missing evidence remains PENDING.','', '## Results','']
 if status=='PASS_EVIDENCE':lines += ['The eight paired lanes total 512 case-profile runs and 576 directed checks. Each same-seed transcript and event stream is compared byte-for-byte; canonical lanes also compare canonical artifacts. This establishes the listed component-level behavioral evidence only.','']
 for c in checks:lines.append(f"- `{c['status']}` `{c['name']}`")
 if pending:lines += ['', '## Pending evidence','']+[f'- {x}' for x in pending]
 if errors:lines += ['', '## Audit failures','']+[f'- {x}' for x in sorted(set(errors))]
 lines += ['', 'PASS_EVIDENCE does not mean full formal state-space equivalence, board-service proof, routed timing closure, parent-clock/I/O signoff, hardware 30 fps qualification, or under-10-ms decode qualification. The focused memory probe uses explicitly prepared internal states and does not establish packet-admission protocol reachability. The coordinate trace is a clocked reachable-state check with a bounded oracle, not a complete formal proof. Detailed hashes and receipt metadata are in `experiments/python-gamebub-v105/source-audit.json`.','']
 DOC.parent.mkdir(parents=True,exist_ok=True);DOC.write_text('\n'.join(lines))
 print(json.dumps({'status':status,'checks':len(checks),'errors':sorted(set(errors)),'pending':pending,'output':str(OUT.relative_to(ROOT))},indent=2))
 return 1 if status=='FAIL' else (2 if status=='PENDING' else 0)
if __name__=='__main__':raise SystemExit(main())
