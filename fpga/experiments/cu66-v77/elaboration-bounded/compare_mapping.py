#!/usr/bin/env python3
"""Same-function finite-regression and unplaced family-map comparison."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];BASE=ROOT/'fpga/experiments/cu66-v77'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 paths=[BASE/'elaboration/results.json',BASE/'elaboration-bounded/results.json',BASE/'render/results.json',BASE/'render/bounded/results.json'];old,new,native,bounded=[json.loads(p.read_text())for p in paths]
 assert old['status']==new['status']=='PASS_GENERIC_AND_CONVERTED_SIMULATION'
 assert old['logical_data_bytes']==new['logical_data_bytes']==29184
 assert native['runs']==bounded['runs'] and bounded['base_native_case_counters_identical']
 assert old['converted_simulation']==new['converted_simulation'] and old['converted_native_case_counters_identical'] and new['converted_native_case_counters_identical']
 a,b=[d['family_map']['statistics']['design']for d in(old,new)];assert all(d['family_map']['status']=='PASS_UNPLACED_FAMILY_MAPPING'for d in(old,new))
 assert a['num_cells_by_type']['RAMB18E1']==b['num_cells_by_type']['RAMB18E1']==11 and a['num_cells_by_type']['RAMB36E1']==b['num_cells_by_type']['RAMB36E1']==3
 result=dict(schema='cu77-address-map-comparison-v1',status='PASS_FINITE_EQUIVALENT_RENDER_AND_UNPLACED_MAP',base_statistics=a,bounded_statistics=b,logical_data_bytes=29184,resource_scope='Cache + converter + minimalrenderguard ONLY; excludes frozenSDRAMcontroller, LCDlinebuffers, rootaddressadapter and compressedvideodecoder',native_case_counters_identical=True,converted_case_counters_identical=True,total_mapped_cell_reduction_percent=100*(a['num_cells']-b['num_cells'])/a['num_cells'],CARRY4_reduction_percent=100*(a['num_cells_by_type']['CARRY4']-b['num_cells_by_type']['CARRY4'])/a['num_cells_by_type']['CARRY4'],input_sha256={str(p.relative_to(ROOT)):sha(p)for p in paths},source_sha256={str(Path(__file__).resolve().relative_to(ROOT)):sha(Path(__file__).resolve())},scope='Same exact native/converted39activeframe+4fault case counters and cycles; bounded7bitmodulo-three address variant, unplacedXC7familymap only',limitations=['Finite native/converted counter parity is not formal equivalence or mapped-netlist simulation','Mapped cells are not LUT utilization or exact-device fit','No targetFmax/route/CDC/physical30fps/sub10ms proof'])
 (BASE/'elaboration-bounded/comparison.json').write_text(json.dumps(result,indent=2)+'\n');print(f"V77_BOUNDED_MAP_COMPARISON_PASS cells={a['num_cells']}->{b['num_cells']} reduction={result['total_mapped_cell_reduction_percent']:.5f}%")
if __name__=='__main__':main()
