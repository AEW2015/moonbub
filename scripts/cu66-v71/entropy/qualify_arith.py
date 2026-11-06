"""Bind completed arithmetic candidate tests to unchanged selected RTL and OOC setup."""
from pathlib import Path
import hashlib,json,re
r=Path(__file__).resolve().parents[3];d=r/'fpga/experiments/cu66-v71/entropy';ev=d/'evidence';o=d/'arith-qualification.json'
assert not o.exists(),'Preserve previous qualification; choose a new version instead'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
der=json.loads((d/'arith-v4-derivation.json').read_text());src=r/der['candidate']
assert sha(src)==der['candidate_sha256']
reg=ev/'arith-regression04';oc=ev/'arith-ooc04'
mal=ev/'arith-malformed03';mr=json.loads((mal/'result.json').read_text());assert mr['status']=='PASS_FROZEN_RTL_MALFORMED_ERROR_PRIORITY_DIFFERENTIAL' and mr['cases']==116
cfg=ev/'arith-cfg-v4-02';cr=json.loads((cfg/'result.json').read_text());assert cr['status']=='PASS_SELECTED_V4_EXHAUSTIVE_CFG' and cr['checks']==2073600 and cr['abort_positions']==17 and cr['source_sha256']==sha(src)
for name,h in mr['source_pins'].items():
 # Comparison rebuilt its own frozen RTL/harness. Parent campaign execution
 # metadata was still growing, so those metadata hashes are historical only.
 if Path(name).name!='execution.json':assert sha(r/name)==h,name
rr=json.loads((reg/'result.json').read_text());ex=json.loads((oc/'execution.json').read_text())
assert rr['status']=='PASS_ARITHMETIC_MICROPIPE_ACTUAL_COEFFICIENTS_AND_ABORTS'
assert ex['returncode']==0 and ex['source_sha256']==sha(src)
pins=json.loads((reg/'source-freeze.json').read_text())
for name,h in pins.items():assert sha(r/name)==h,name
assert sha(oc/src.name)==sha(src) and sha(reg/src.name)==sha(src)
tim=(oc/'timing.rpt').read_text();h=tim.index('WNS(ns)');numbers=tim[h:].splitlines()[2].split()
wns,tns=float(numbers[0]),float(numbers[1]);assert wns>0 and tns==0 and int(numbers[2])==0
proofs={}
for q in [Path(__file__),Path(__file__).with_name('prepare_arith.py'),Path(__file__).with_name('prepare_band.py'),Path(__file__).with_name('prepare_limits.py'),Path(__file__).with_name('prepare_params.py'),Path(__file__).with_name('run_arith.py'),Path(__file__).with_name('synth_arith.py'),Path(__file__).with_name('verify_malformed.py'),Path(__file__).with_name('verify_cfg.py')]:
 proofs[q.relative_to(r).as_posix()]=sha(q)
for q in [d/'arith-v4-derivation.json',reg/'result.json',reg/'source-freeze.json',reg/'tb.cpp',reg/'build.log',reg/'directed.log',reg/'stress.log',reg/'actual.log',oc/'execution.json',oc/'executed.tcl',oc/'timing.rpt',oc/'setup-paths.rpt',oc/'utilization.rpt']:
 proofs[q.relative_to(r).as_posix()]=sha(q)
for campaign in ['directed','stress']:
 log=(reg/(campaign+'.log')).read_text();assert 'ARITHMETIC_MICRO_ABORT_PASS appended_states=11 probability_writes_on_abort=0 valid_retry=11' in log
for q in [mal/'result.json',mal/'baseline.log',mal/'candidate.log',mal/'fixtures.tsv']:
 proofs[q.relative_to(r).as_posix()]=sha(q)
for q in [cfg/'result.json',cfg/'cfg.cpp',cfg/'executed.log']:
 proofs[q.relative_to(r).as_posix()]=sha(q)
for label,original in [('baseline',ev/'regression03'),('candidate',reg)]:
 for q in (mal/label).glob('*'):
  if q.suffix in ['.sv','.cpp']:assert sha(q)==sha(original/q.name)
  proofs[q.relative_to(r).as_posix()]=sha(q)
sel={'status':'PASS_NATIVE_COEFFICIENT_REGRESSION_AND_SYNTHESIZED_SETUP_DIAGNOSTIC_ONLY','selected_sources':[{'path':src.relative_to(r).as_posix(),'sha256':sha(src)}],'proofs':proofs,'campaigns':rr['campaigns'],'new_states':der['new_states'],'setup_diagnostic':{'part':'xc7a100tcsg324-1','clock_ns':10,'io_max_ns':1,'wns_ns':wns,'tns_ns':tns,'failing_setup_endpoints':int(numbers[2]),'unplaced_whs_ns':float(numbers[4]),'overall_timing_pass':False},'arithmetic':'17x8 product exact25bits thenfloor/256; partition1..65535; band17x6 exact23bits; signed32pending comparisons; exact32bitwrapped parameter arithmetic; errorpriorities retained','latency_changed':True,'wire_or_probability_rounding_changed':False,'hardware_tested':False,'routed_timing':False,'scope':'1371actual coefficient oracles +31directed malformed/valid +120stress; all11newstate abortprobabilityRAM/counterchecks plusvalidretry. Unplaced hold estimates remain negative; parent full-board routed setup/hold gates required.'}
o.write_text(json.dumps(sel,indent=2)+'\n');print(json.dumps({'qualification':str(o),'source_sha256':sha(src),'wns_ns':wns,'actual':rr['campaigns']['actual']}))
