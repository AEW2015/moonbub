"""Seal finite functional and algebraic evidence without timing claims."""
from pathlib import Path
import hashlib,json
r=Path(__file__).resolve().parents[3];d=r/'fpga/experiments/cu66-v71/staging-timing';sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
checks=0
for width in [4,5,8]:
 modulus=1<<width
 for p in range(modulus):
  for w in range(modulus):
   rem=(p-w)%modulus;within=w<=p;cap=min(4,rem)
   for count in range(8):
    assert (1<=count<=4 and w+count<=p)==(1<=count<=4 and within and count<=cap);checks+=1
   nextwithin=w==modulus-1 or (within and rem!=0)
   nextcap=4 if rem>4 or rem==0 else rem-1
   nw=(w+1)%modulus
   assert nextwithin==(nw<=p) and nextcap==min(4,(p-nw)%modulus)
values=[0,1,2,3,4,5,7,8,15,17,49151,49152,65535,65536,0x7fffffff,0x80000000,0xfffffffa,0xfffffffb,0xfffffffc,0xfffffffd,0xfffffffe,0xffffffff]
for p in values:
 for w in values:
  rem=(p-w)&0xffffffff;within=w<=p;cap=min(4,rem)
  for count in range(8):assert(1<=count<=4 and w+count<=p)==(1<=count<=4 and within and count<=cap);checks+=1
  nw=(w+1)&0xffffffff;assert(w==0xffffffff or(within and rem!=0))==(nw<=p)
  assert(4 if rem>4 or rem==0 else rem-1)==min(4,(p-nw)&0xffffffff)
paths=[d/'evidence/functional08/result.json',d/'evidence/control01/result.json',d/'evidence/control-edge01/result.json']
for f in paths:assert f.exists()
sources={f.relative_to(r).as_posix():sha(f)for f in d.glob('*.sv')}
refs={}
for subdir in ['functional08','control01','control-edge01']:
 for f in(d/'evidence'/subdir).iterdir():
  if f.is_file():refs[f.relative_to(r).as_posix()]=sha(f)
for f in [r/'firmware/experiments/v36-dual-local-fixture-20261106/handheld/src/cu66/local.rs',r/'fpga/experiments/cu66-v71/system/cu71_packet_staging.sv',r/'fpga/experiments/cu66-v71/bus-split/dy71_local_control_split.sv',r/'fpga/experiments/cu66-v71/bus-split/cu71_local_control_split.sv',Path(__file__).resolve()]:refs[f.relative_to(r).as_posix()]=sha(f)
sourceproof={'sources_sha256':sources,'invariants':['remaining_bytes==(packet_bytes-written_bytes) mod2^32','within_packet==(written_bytes<=packet_bytes)','upload_capacity==min(4,remaining_bytes)'],'admission':'Original 33-bit sum inequality equals within_packet && upload_count<=upload_capacity, retaining original count1..4 gates','reset_begin_drain':'Reset remaining0/within1/cap0; accepted BEGIN remaining=begin_bytes/within1/cap=min4; actual byte drain decrements remaining modulo32, computes nextwithin=(oldwritten==ffffffff)||(oldwithin&&oldremaining!=0), nextcap=(oldremaining>4||oldremaining==0)?4:oldremaining-1','stale_empty':'No clearing added on discard/release/BEGIN; retained parent stale-held-count behavior is explicitly exercised','counter_domain':'Full32-bit counters preserved; no MAX_BYTES narrowing or untrusted input assumption','exhaustive_reduced_widths':[4,5,8],'algebra_boundary_checks':checks,'formal_tool_proof':False}
(d/'source-proof-v002.json').write_text(json.dumps(sourceproof,indent=2)+'\n')
refs[(d/'source-proof-v002.json').relative_to(r).as_posix()]=sha(d/'source-proof-v002.json')
q={'status':'PASS_FINITE_FUNCTIONAL_AND_ALGEBRA_GATE_TIMING_UNMEASURED','sources_sha256':sources,'proofs_sha256':refs,'random_cycles':900000,'MAX_BYTES_tested':[1,3,17,49152,65536],'actual_maximum_packet_readback_bytes':49152,'typed_profiles':['CU71','DY71'],'typed_phase_runs':4,'public_cycle_latency_changed':False,'safety_bug_fixed':False,'existing_stale_upload_bug_reproduced':True,'structural_goal':'CSR no longer subtracts32 bits; admission no longer sums/compares33 bits; new capacity/within flags are registers','timing':'UNMEASURED_NO_VIVADO_RUN','area':'UNMEASURED_EXPECT_EXTRA32BIT_REMAINING_AND4FLAG_BITS','no_selected_source_changes':True,'hardware':False,'BIT':False,'next_gates':['Independent review','Matched exact-part OOC under unchanged constraints when root permits','Actual native v36/HUD integration if selected','Full board timing/fit/CDC/DRC before any BIT eligibility']}
(d/'qualification-v001.json').write_text(json.dumps(q,indent=2)+'\n');print(json.dumps({'qualification_sha256':sha(d/'qualification-v001.json'),'sources':sources,'checks':checks},indent=2))
