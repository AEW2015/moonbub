#!/usr/bin/env python3
"""Portable source, paired-oracle, packaging and mapped-UNISIM TABLES audit."""
import gzip,hashlib,importlib.util,json,re,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];FPGA=ROOT/'fpga/experiments/cu66-v107-tables';AREA=ROOT/'experiments/python-gamebub-v107/tables'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(b):return hashlib.sha256(b).hexdigest()
def mod(p,n):
 spec=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def main():
 selected=json.loads((AREA/'results.json').read_text());path=ROOT/selected['selected_report'];r=json.loads(path.read_text());assert r['status']=='PASS' and r['actual_RTL_run']
 for n,h in r['source_sha256'].items():assert sha(path.parent/'sources'/n)==h,n
 for n,h in r['artifacts_sha256'].items():assert sha(path.parent/n)==h,n
 recipe=json.loads((FPGA/'edit-recipe.json').read_text());base=ROOT/recipe['baseline'];candidate=ROOT/recipe['candidate'];a,b=base.read_text(),candidate.read_text();assert sha(base)==recipe['baseline_sha256'] and sha(candidate)==recipe['candidate_sha256']==r['candidate']['sha256']
 forward=a
 for e in reversed(recipe['changes']):assert forward[e['start']:e['end']]==e['old'];forward=forward[:e['start']]+e['new']+forward[e['end']:]
 assert forward==b
 backward=b
 for e in recipe['changes']:
  at=e['start'];assert backward[at:at+len(e['new'])]==e['new'];backward=backward[:at]+e['old']+backward[at+len(e['new']):]
 assert backward==a
 old_recipe=ROOT/'fpga/experiments/cu66-v105-memory/edit-proof.json';assert sha(old_recipe)==recipe['V105_mode_recipe_sha256']
 canonical=json.loads(old_recipe.read_text())['edits'][0]['after'].split('    // FINISHED lookups',1)[0]
 start=b.index('    // Canonical single mode-store write port.');end=b.index('    cu66_mode_store_v107 mode_store',start)
 assert b[start:end]==canonical and digest(canonical.encode())==recipe['canonical_mode_generator_sha256']
 assert re.findall(r'tile<=.*?;',a)==re.findall(r'tile<=.*?;',b)
 assert a.split('task automatic residual_tile;',1)[1].split('endtask',1)[0]==b.split('task automatic residual_tile;',1)[1].split('endtask',1)[0]
 assert a.split(');',1)[0]==b.split(');',1)[0]
 # Full-width arithmetic remains in the copied generator; truncation occurs only at the original13-bit port boundary.
 assert "13'((plane==0?0:plane==1?5400:6750)+tile)" in canonical
 rows=0
 for prefix in (0,0x2000,0x10000000,0x7fffe000,0x80000000,0xffffe000):
  for p in range(4):
   offset=0 if p==0 else 5400 if p==1 else 6750
   for low in range(8192):
    tile=(prefix+low)&0xffffffff;assert ((offset+tile)&0xffffffff)&8191==(offset+(tile&8191))&8191;rows+=1
 pack=json.loads((FPGA/'packaging.json').read_text());raw=candidate.read_bytes();x,y=pack['split_byte_offsets'];parts=[raw[:x],raw[x:y],raw[y:]];assert digest(raw)==pack['production_sha256']
 for fragment,data in zip(pack['fragments'],parts):assert digest(data)==fragment['sha256'] and len(data)==fragment['bytes']
 assert b''.join(parts)==raw and parts[1]==base.read_bytes()[base.read_bytes().index(b'module cu66_scale_tdp_v107 ('):]
 assert digest(parts[1])==pack['scale_helper_unchanged_sha256']
 adapter=json.loads((FPGA/'adapter.json').read_text())
 for name,production in [('original',a),('candidate',b)]:
  text=(FPGA/f'admission_{name}.sv').read_text().replace(' /* verilator public_flat_rw */','').replace('module admission_'+name+' (','module cs88_admission_v91i2a (',1).replace(adapter['extra_ports'],'\n);',1).replace(adapter['assignments'][name],'',1)
  assert text==production,name
 pkg=path.parent/'compile-package';assert (pkg/'admission_candidate.sv').read_bytes()+(pkg/'cu66_scale_tdp_v107.sv').read_bytes()+(pkg/'cu66_mode_store_v107.sv').read_bytes()==(path.parent/'sources'/FPGA.relative_to(ROOT)/'admission_candidate.sv').read_bytes()
 assert (pkg/'admission_original.sv').read_bytes()+(pkg/'cu66_scale_tdp_v107.sv').read_bytes()==(path.parent/'sources'/FPGA.relative_to(ROOT)/'admission_original.sv').read_bytes()
 assert '%Warning-' not in (path.parent/'compile.log').read_text()
 mode=mod(ROOT/'scripts/cu66-v107/tables/mode_replay.py','mode_oracle');scale=mod(ROOT/'scripts/cu66-v107/scale.py','scale_oracle');runs=[]
 for run in r['runs']:
  seed=run['seed']
  with tempfile.TemporaryDirectory() as tmp:
   modefile=Path(tmp)/'mode.jsonl';scalefile=Path(tmp)/'scale.csv'
   modefile.write_bytes(gzip.decompress((path.parent/f'mode-ports-{seed}.jsonl.gz').read_bytes()));scalefile.write_bytes(gzip.decompress((path.parent/f'scale-ports-{seed}.csv.gz').read_bytes()))
   mr=mode.mode_replay(modefile,seed);sr=scale.scale_replay(scalefile)
  assert mr==run['mode_port_replay'] and sr==run['scale_port_replay']
  v=run['terminal_verdict'];assert v['status']=='TEST_PASS' and v['cases']==86 and v['mode_prepared_edges']==158230 and v['scale_prepared_edges']==40585
  runs.append(dict(seed=seed,mode=mr,scale=sr,verdict=v))
 selection=json.loads((AREA/'unit/results.json').read_text());unit=ROOT/selection['selected_receipt'];assert sha(unit)==selection['sha256'];u=json.loads(unit.read_text());assert u['status']=='PASS_MAPPED_UNISIM_TABLES_COLLISIONS' and u['source']['sha256']==sha(candidate) and u['source_unchanged']
 for n,h in u['retained_sha256'].items():assert sha(unit.parent/n)==h,n
 modes=[s.split('\t') for s in (unit.parent/'reports/ram-modes.tsv').read_text().splitlines()[1:]];assert len(modes)==2
 native={z[0]:z[1:] for z in modes};assert native['modes/words_reg']==['RAMB18E1','TDP','2','2','2','2','READ_FIRST','WRITE_FIRST','0','0'];assert native['scales/words_reg']==['RAMB18E1','TDP','9','9','9','9','READ_FIRST','READ_FIRST','0','0']
 transcript=(unit.parent/'reports/xsim.log').read_text();assert 'TEST_PASS_TABLES_UNIT' in transcript and 'TEST_PASS_MODE_UNIT clocks=72947 held_outputs=32439 cancelled=7' in transcript and 'TEST_PASS_SCALE_UNIT clocks=27033' in transcript
 assert not re.search(r'ERROR:|FATAL|Error:|collision detected',transcript,re.I)
 ledger=[]
 for q in sorted((AREA/'attempts').glob('*/results.json')):
  z=json.loads(q.read_text());ledger.append(dict(attempt=q.parent.name,status=z['status'],error=z.get('error'),sha256=sha(q)))
 output=dict(schema='v107-tables-portable-audit-v1',status='PASS_TABLES_FOCUS_AND_ACTUAL_UNISIM',candidate_sha256=sha(candidate),baseline_SCALE_sha256=sha(base),reverse_exact_mode_edits_recovers_SCALE=True,V105_generator_byte_identical=True,scale_helper_byte_identical=True,full13_modular_address_model_rows=rows,compile_packaging_lossless=True,runs=runs,native_unit=dict(receipt=str(unit.relative_to(ROOT)),sha256=sha(unit),RAM_parameters=native,actual_mapped_netlist_UNISIM=True,SDF_timing=False),attempt_ledger=ledger,scope=['Full paired admission module, all1350scale/all8100mode valid words and every2-bit value; prepared states are not packet reachability.','Cold outputs/unwritten words and invalid lookup indices are unqualified; no fabricated zero contract.','Physical modes are actual READ_FIRST/WRITE_FIRST for mode and READ_FIRST/READ_FIRST for scale; public hold verified in the complete mapped primitive/hold-mux netlist.','No global pipeline, complete routed decoder, I/O, CDC or hardware claim from these focused scopes.'],audit_program_sha256=sha(Path(__file__)))
 (AREA/'audit.json').write_text(json.dumps(output,indent=2,sort_keys=True)+'\n');print(output['status'],sha(candidate))
if __name__=='__main__':main()
