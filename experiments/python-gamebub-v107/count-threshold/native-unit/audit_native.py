#!/usr/bin/env python3
"""Portable audit and connectivity-qualified correction of raw FF role heuristic."""
import argparse,collections,csv,hashlib,json,re,shutil
from pathlib import Path
ROOT=next((p for p in Path(__file__).resolve().parents if (p/'fpga/experiments').is_dir()),None);AREA=(ROOT/'experiments/python-gamebub-v107/count-threshold/native-unit') if ROOT else Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def main():
 global AREA
 parser=argparse.ArgumentParser();parser.add_argument('--area',type=Path,default=AREA);parser.add_argument('--retained-only',action='store_true');args=parser.parse_args();AREA=args.area.resolve()
 chosen=json.loads((AREA/'results.json').read_text());receipt=AREA/Path(chosen['selected_receipt']).parent.name/'receipt.json';assert sha(receipt)==chosen['sha256'];r=json.loads(receipt.read_text());out=receipt.parent;assert r['status']=='PASS_MEASURED_EXTRACTED_UNIT_MAPPING' and r['exit_code']==0 and r['source_unchanged']
 for rel,digest in r['retained_sha256'].items():assert sha(out/rel)==digest,rel
 for rel,digest in r['source_sha256'].items():
  assert sha(out/'sources'/rel)==digest,rel
  if not args.retained_only:assert ROOT and sha(ROOT/rel)==digest,rel
 src=out/'sources/fpga/experiments/cu66-v107-count-threshold/br88_packet_ingress_sync_v91h.sv';probe=out/'sources/fpga/experiments/cu66-v107-count-threshold/verification/threshold_math_probe.sv';s=src.read_text();a=s.index('    // COUNT_THRESHOLD_PIPELINE_BEGIN');b=s.index('    // COUNT_THRESHOLD_PIPELINE_END')+len('    // COUNT_THRESHOLD_PIPELINE_END');block=s[a:b];assert hashlib.sha256(block.encode()).hexdigest()==r['extracted_block_sha256'];assert probe.read_text().count(block)==1
 netlist=(out/'reports/mapped.v').read_text();pattern=re.compile(r'(?m)^  (FDRE|FDSE|SRL16E|LUT[1-6]|DSP48E1|CARRY4|VCC|GND)\s+(?:#\((.*?)\)\s*)?(\\\S+|\w+)\s*\((.*?)\);',re.S);cells={}
 for m in pattern.finditer(netlist):
  name=m[3].lstrip('\\');assert name not in cells;cells[name]=dict(primitive=m[1],parameters=m[2] or '',ports={k:v.strip() for k,v in re.findall(r'\.(\w+)\(([^()]*)\)',m[4])},text=m.group())
 def uses(net):return [(n,port) for n,c in cells.items() for port,value in c['ports'].items() if value==net and port not in ('Q','O','P','CO','ACOUT','BCOUT','CARRYCASCOUT','PCOUT')]
 helpers=['threshold_pipes_r']+[f'threshold_pipes_r_{i}' for i in range(6)];previous="1'b1";links=[]
 for i,name in enumerate(helpers):
  c=cells[name];assert c['primitive']=='FDRE' and c['ports']['C']=='clk' and c['ports']['CE']=="1'b1" and c['ports']['R']=='reset' and c['ports']['D']==previous
  links.append(dict(cell=name,**c));previous=c['ports']['Q']
  if i<6:assert uses(previous)==[(helpers[i+1],'D')]
 gates=['threshold_pipes_gate','threshold_pipes_gate__0','threshold_pipes_gate__1'];assert sorted(uses(previous))==sorted((x,'I1') for x in gates)
 for i,name in enumerate(gates):
  c=cells[name];assert c['primitive']=='LUT2' and ".INIT(4'h8)" in c['parameters'] and c['ports']['I1']==previous
  target=f'threshold_pipes[{i}].valid_pipe_reg[7]';assert uses(c['ports']['O'])==[(target,'D')];assert cells[target]['primitive']=='FDRE';links.append(dict(cell=name,valid_destination=target,**c))
 raw=list(csv.DictReader((out/'reports/ff-control-pins.tsv').open(),delimiter='\t'));qualified=[]
 for row in raw:
  q=dict(row);q['qualified_role']='control' if q['cell'] in helpers else q['role'];qualified.append(q)
 ff_counts=collections.Counter(x['qualified_role'] for x in qualified if x['pin']=='R');assert ff_counts==dict(data=469,control=16)
 data_reset=[x for x in qualified if x['qualified_role']=='data' and x['pin']=='R'];assert all(x['driver_types']=='GND' and not x['input_ports'] for x in data_reset)
 data_ce=[x for x in qualified if x['qualified_role']=='data' and x['pin']=='CE'];assert all(not x['input_ports'] for x in data_ce)
 ce_counts=collections.Counter('VCC' if x['driver_types']=='VCC' else x['drivers'] for x in data_ce);assert ce_counts=={'VCC':377,'threshold_pipes[0].valid_pipe_reg[7]/Q':32,'threshold_pipes[1].valid_pipe_reg[7]/Q':31,'threshold_pipes[2].valid_pipe_reg[7]/Q':29}
 dsps=list(csv.DictReader((out/'reports/dsp-registers.tsv').open(),delimiter='\t'));configs=collections.Counter((int(x['AREG']),int(x['BREG']),int(x['MREG']),int(x['PREG'])) for x in dsps);assert len(dsps)==16 and sum(int(x['PREG']) for x in dsps)==14
 dc=list(csv.DictReader((out/'reports/dsp-control-pins.tsv').open(),delimiter='\t'));resets=[x for x in dc if x['pin'].startswith('RST')];assert len(resets)==160 and all(x['driver_types']=='GND' for x in resets)
 srl=list(csv.DictReader((out/'reports/srls.tsv').open(),delimiter='\t'));assert len(srl)==124 and all(x['CE_driver_types']=='VCC' for x in srl);valid_srls=[x['cell'] for x in srl if 'valid_pipe' in x['cell']];assert len(valid_srls)==3
 timing=(out/'reports/timing.rpt').read_text();assert 'Source:                 partial_product_return/CLK' in timing and 'Destination:            threshold_pipes[0].cross_s1_reg/C[0]' in timing
 attribution=dict(schema='v107-qualified-native-control-attribution-v1',raw_receipt=chosen['selected_receipt'],raw_receipt_sha256=sha(receipt),status='PASS_CONNECTIVITY_QUALIFIED_RESET_MASK_ATTRIBUTION',raw_name_heuristic_misclassified_FFs=helpers,proof='Seven resettable FDREs form an unconditional constant1 fill chain, with no data fanouts; finalQ feeds only three AND gates that each drive a valid_pipe[7] D pin. These are shared SRL validity reset-mask controls, not arithmetic payload.',mapped_connections=links,qualified_data_FFs=469,qualified_control_FFs=16,qualified_data_reset_GND=469,qualified_data_CE_counts=dict(ce_counts),all_data_CE_input_port_fanin_empty=True,DSP_reset_pins_grounded=160,SRL16E=124,valid_control_SRLs=valid_srls,data_SRLs=121,all_SRL_CE_VCC=True)
 if args.retained_only:
  print('PASS_RETAINED_NATIVE_SNAPSHOTS_MAPPING_AND_CONTROL_ATTRIBUTION');return
 write(AREA/'connectivity-attribution.json',attribution)
 result=dict(schema='v107-native-threshold-portable-audit-v1',status='PASS_NATIVE_EVIDENCE_AND_CONTROL_ATTRIBUTION_WITH_OPEN_DSP_PIPELINING',raw_receipt=chosen['selected_receipt'],raw_receipt_sha256=sha(receipt),production_and_wrapper_source_unchanged=True,wrapper_sha256=r['wrapper_sha256'],DSP48E1=16,DSPs_with_PREG=14,DSPs_with_neither_MREG_nor_PREG=r['metrics']['DSPs_with_neither_MREG_nor_PREG'],DSP_config_counts=[dict(AREG=k[0],BREG=k[1],MREG=k[2],PREG=k[3],count=v) for k,v in sorted(configs.items())],qualified_data_FFs=469,qualified_control_FFs=16,raw_role_heuristic_preserved=True,connectivity_attribution_sha256=sha(AREA/'connectivity-attribution.json'),synth_only_worst_slack_ns=4.871,synth_only_worst_data_ns=4.812,synth_only_worst_logic_ns=4.009,synth_only_worst_estimated_route_ns=.803,synth_only_worst_source='partial_product_return/CLK',synth_only_worst_destination='threshold_pipes[0].cross_s1_reg/C[0]',synth_only_WHS_ns=.207,synth_only_pulse_slack_ns=4.020,open_DRC={'CFGBVS-1':1,'DPIP-1':5,'DPOP-1':2,'DPOP-2':6},methodology_TIMING18_missing_IO=139,limits=['Post-synthesis estimates only; no placement/route or board I/O qualification.','Synthetic wrapper shares one numerator across three pipelines; cross-pipe CSE/resource counts need not match full ingress.','Source operation/reg naming does not prove dedicated MREG/PREG; two AREG1 MREG0 PREG0 DSPs remain an open physical mapping finding.','No post-synthesis UNISIM equivalence or actual mapped E0-E8 cycle proof was run; behavioral arithmetic/owner proofs are separate.'])
 write(AREA/'audit.json',result)
 shutil.copyfile(Path(__file__),AREA/'audit_native.py')
 index=dict(schema='v107-threshold-native-evidence-index-v1',receipt=chosen['selected_receipt'],receipt_sha256=sha(receipt),portable_files={str((out/rel).relative_to(AREA)):digest for rel,digest in r['retained_sha256'].items()},separate_qualified_files={x:sha(AREA/x) for x in ('connectivity-attribution.json','audit.json','audit_native.py')},external_checkpoint_only=r['artifacts']['synth.dcp']);write(AREA/'evidence-index.json',index);print(result['status'])
if __name__=='__main__':main()
