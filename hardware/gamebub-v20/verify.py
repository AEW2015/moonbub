#!/usr/bin/env python3
"""Read-only golden regeneration, native C arithmetic, and wire-layout checks."""
import json
from pathlib import Path
import acceptance,export_vectors,export_contract,reference as ref
HERE=Path(__file__).resolve().parent

def main():
    index=json.loads((HERE/'golden-index.json').read_text());assert export_vectors.build()==index
    contract=json.loads((HERE/'wire-contract.json').read_text());assert export_contract.build()==contract
    assert export_contract.header(contract)==(HERE/'include/gb_wire.h').read_text()
    recorded=json.loads((HERE/'results.json').read_text());fresh=acceptance.run()
    for k in ('source_sha256','golden_index_sha256','invalid_input_checks','datasets','blocks','exact_residual_samples','scope'):assert fresh[k]==recorded[k],k
    assert recorded['toolchain']['sanitized'] and fresh['toolchain']['sanitized']
    demo=json.loads((HERE/'vectors/rtl-smoke/slice.json').read_text());assert demo['source_index_sha256']==ref.sha(HERE/'golden-index.json')
    assert (demo['dataset'],demo['start_block'],demo['blocks'])==('signed-edges',0,6)
    dataset=next(r for r in index['datasets'] if r['name']=='signed-edges')
    for kind in ('dequantized','residual'):
        expected=''.join(f'{int(v)&0xffffffff:08x}\n' for v in acceptance.load_array(dataset['arrays'][kind]).flat)
        assert (HERE/('vectors/rtl-smoke/'+kind+'.mem')).read_text()==expected
    assert fresh['blocks']==101667 and fresh['exact_residual_samples']==6506688
    assert contract['limits']['max_data_udp_bytes']==1055
    assert contract['layouts']['AR03']['field_bytes']==61 and contract['layouts']['AF03']['total_header_or_message_bytes']==43
    assert contract['layouts']['FG19']['total_header_or_message_bytes']==36
    assert contract['layouts']['GF03']['field_bytes']==31
    assert contract['layouts']['PC18']['total_header_or_message_bytes']==29
    assert contract['layouts']['QC18']['total_header_or_message_bytes']==28
    print('PASS:101667exactC11inverseblocks/6506688residualsamples;UBSan/errorguards;wireoffsets/FG19goldencontrols;nohardwarequalification')
if __name__=='__main__':main()
