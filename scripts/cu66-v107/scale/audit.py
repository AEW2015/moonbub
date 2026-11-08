#!/usr/bin/env python3
"""Audit the frozen SCALE-only admission/unit proof and routed lookup diagnostic."""
import gzip,hashlib,importlib.util,json,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];AREA=ROOT/'experiments/python-gamebub-v107/scale';FPGA=ROOT/'fpga/experiments/cu66-v107-scale'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 selection=json.loads((AREA/'results.json').read_text());report=ROOT/selection['selected_report'];r=json.loads(report.read_text());assert r['status']=='PASS' and r['actual_RTL_run']
 for name,h in r['artifacts_sha256'].items():assert sha(report.parent/name)==h,name
 for name,h in r['source_sha256'].items():assert sha(report.parent/'sources'/name)==h,name
 recipe=json.loads((FPGA/'edit-recipe.json').read_text());base=ROOT/recipe['baseline'];candidate=ROOT/recipe['candidate'];text=base.read_text();assert sha(base)==recipe['baseline_sha256'] and sha(candidate)==recipe['candidate_sha256']==r['candidate']['sha256']
 for e in reversed(recipe['changes']):assert text[e['start']:e['end']]==e['old'];text=text[:e['start']]+e['new']+text[e['end']:]
 assert text==candidate.read_text()
 pack=json.loads((FPGA/'packaging.json').read_text());data=candidate.read_bytes();at=pack['split_byte_offset'];assert sha(candidate)==pack['production_sha256'] and hashlib.sha256(data[:at]).hexdigest()==pack['main_sha256'] and hashlib.sha256(data[at:]).hexdigest()==pack['helper_sha256']
 spec=importlib.util.spec_from_file_location('scale_replay',ROOT/'scripts/cu66-v107/scale.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 for run in r['runs']:
  with tempfile.TemporaryDirectory() as temp:
   trace=Path(temp)/'ports.csv';trace.write_bytes(gzip.decompress((report.parent/f"scale-ports-{run['seed']}.csv.gz").read_bytes()));assert module.scale_replay(trace)==run['scale_port_replay']
 selected=json.loads((AREA/'unit/results.json').read_text());unit=ROOT/selected['selected_receipt'];assert sha(unit)==selected['sha256'];u=json.loads(unit.read_text());assert u['status']=='PASS_MAPPED_UNISIM_SCALE_COLLISIONS' and u['source']['sha256']==sha(candidate)
 for name,h in u['retained_sha256'].items():assert sha(unit.parent/name)==h,name
 rows=(unit.parent/'reports/ram-modes.tsv').read_text().splitlines()[1:];assert len(rows)==1 and rows[0].split('\t')[1:]==['RAMB18E1','TDP','9','9','9','9','READ_FIRST','READ_FIRST','0','0']
 log=(unit.parent/'reports/xsim.log').read_text();assert 'TEST_PASS_SCALE_UNIT clocks=27033 old_data_collisions=5400 distinct_dual_writes=1350 same_address_priority=5400 held_outputs=6782' in log
 diag=json.loads((AREA/'lookup-probe/results.json').read_text());dp=ROOT/diag['selected_receipt'];assert sha(dp)==diag['sha256'];d=json.loads(dp.read_text());assert d['status']=='PASS_READONLY_TIMING_EXTRACTION' and d['checkpoint_readonly'] and d['checkpoint_sha256_before']==d['checkpoint_sha256_after']
 for n,h in d['retained_sha256'].items():assert sha(dp.parent/n)==h,n
 result=dict(schema='v107-scale-portable-audit-v1',status='PASS_FOCUSED_SCALE_AND_ACTUAL_UNISIM',production_sha256=sha(candidate),baseline_HEADER_sha256=sha(base),source_recipe_exact=True,packaging_lossless=True,paired_seeds=[x['seed'] for x in r['runs']],historical_case_seed_runs=sum(x['terminal_verdict']['cases'] for x in r['runs']),directed_checks=sum(x['terminal_verdict']['directed_checks'] for x in r['runs']),total_clock_edges=sum(x['terminal_verdict']['clock_edges']+x['terminal_verdict']['prepared_edges']+x['terminal_verdict']['header_prepared_edges']+x['terminal_verdict']['scale_prepared_edges'] for x in r['runs']),native_unit_receipt=str(unit.relative_to(ROOT)),native_unit_receipt_sha256=sha(unit),physical_modes='TDP READ_FIRST/READ_FIRST, width9/9, DO_REG0/0 with actual inferred hold mux',readonly_routed_diagnostic_receipt=str(dp.relative_to(ROOT)),SCALE_only_global_canonical_or_native_route=False,scope='Complete admission parity and memory collision/hold scope only; no full decoder timing, CDC, I/O or hardware claim.',auditor_sha256=sha(Path(__file__)))
 (AREA/'audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(result['status'])
if __name__=='__main__':main()
