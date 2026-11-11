#!/usr/bin/env python3
"""Freeze exact source derivation and lossless three-module packaging for parent integration."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[3]
AREA=ROOT/'experiments/python-gamebub-v130/spec-read'
SRC=ROOT/'fpga/experiments/cu66-v130-spec-read'
PARENT=ROOT/'experiments/python-gamebub-v129/integration/results.json'
SELECT=AREA/'results.json'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
rel=lambda p:str(Path(p).relative_to(ROOT))
def load(p):return json.loads(p.read_text())
def main():
 p=load(PARENT);der=load(SRC/'derivation.json');r=load(SELECT);receipt=ROOT/r['path'];assert r['status']=='PASS' and sha(receipt)==r['sha256'] and load(receipt)['actual_RTL_run']
 original=ROOT/der['parent'];candidate=SRC/'cs88_admission_v91i2a.sv';assert sha(original)==der['parent_sha256'] and sha(candidate)==der['candidate_sha256'];old=original.read_text();new=candidate.read_text();assert old.count(der['old_block'])==1 and new.count(der['new_block'])==1 and old.replace(der['old_block'],der['new_block'])==new and new.replace(der['new_block'],der['old_block'])==old
 origins=p['source_origins'];alias='fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv';assert len(origins)==18 and origins[alias]=={'path':rel(original),'sha256':sha(original)}
 for v in origins.values():assert sha(ROOT/v['path'])==v['sha256']
 neworigins=dict(origins);neworigins[alias]={'path':rel(candidate),'sha256':sha(candidate)}
 raw=candidate.read_bytes();split1=raw.index(b'module cu66_scale_tdp_v107');split2=raw.index(b'module cu66_mode_store_v107');assert 0<split1<split2
 pkg=AREA/'compile-packaging';pkg.mkdir(exist_ok=True)
 chunks=[raw[:split1],raw[split1:split2],raw[split2:]];names=['cs88_admission_v91i2a.sv','cu66_scale_tdp_v107.sv','cu66_mode_store_v107.sv']
 for n,c in zip(names,chunks):(pkg/n).write_bytes(c)
 assert b''.join((pkg/n).read_bytes() for n in names)==raw
 result={'schema':'v130-spec-read-candidate-composition-v1','status':'PREPARED_NOT_INTEGRATED',
 'v129_functional_parent':{'path':rel(PARENT),'sha256':sha(PARENT)},'focused_pair':{'path':rel(receipt),'sha256':sha(receipt)},
 'source_origins':neworigins,'changed_aliases':[alias], 'source_order':p['rtl_source_order'],
 'new_actual_order':[rel(candidate) if x==rel(original) else x for x in p['rtl_source_order']],
 'packaging':{'production_sha256':sha(candidate),'lossless_concat':True,'split_byte_offsets':[split1,split2],
 'fragments':[{'path':rel(pkg/n),'sha256':sha(pkg/n),'bytes':len(c)} for n,c in zip(names,chunks)]},
 'contract':'All non-data public outputs compared; replay and stage data only when their original response-valid is asserted. Invalid data values may differ.',
 'full_parent_functional_pass':False,'physical_timing_pass':False,'hardware_qualification':False}
 (AREA/'composition.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 print('PASS_SOURCE_DERIVATION_AND_PACKAGING_NOT_INTEGRATED',sha(AREA/'composition.json'))
if __name__=='__main__':main()
