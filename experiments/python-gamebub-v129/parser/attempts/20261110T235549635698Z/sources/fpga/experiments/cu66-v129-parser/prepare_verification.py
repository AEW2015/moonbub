#!/usr/bin/env python3
"""Build reversible adapters for paired V116/V129 parser verification."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
V = HERE / 'verification'
OLD = ROOT / 'fpga/experiments/cu66-v116-rice'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()
    recipe = json.loads((HERE/'edit-recipe.json').read_text())
    prior = ROOT / recipe['original']['path']
    candidate = ROOT / recipe['candidate']['path']
    assert sha(prior) == recipe['original']['sha256'] and sha(candidate) == recipe['candidate']['sha256']
    files = {}
    for src, name in ((prior,'rice_original.sv'),(candidate,'rice_candidate.sv')):
        text = src.read_text()
        assert text.count('module br88_rice_elastic (') == 1
        text = text.replace('module br88_rice_elastic (','module '+name[:-3]+' (',1)
        files[name] = text
    for name in ('rice_probe.sv','historical_rice.cpp','view_directed.cpp'):
        files[name] = (OLD/'verification'/name).read_text()
    tb = (OLD/'verification/tb_rice.cpp').read_text()
    old = ('OLD(out_value)=0U;NEW(output_zero)=1U;NEW(successful_payload)=0U;'
           'NEW(v116_check_seen)=0U;NEW(v116_owned)=0U;'
           'NEW(v116_expected_zero)=1U;NEW(v116_expected_value)=0U;')
    new = ('BOTH(output_zero,1U);BOTH(successful_payload,0U);'
           'BOTH(v116_check_seen,0U);BOTH(v116_owned,0U);'
           'BOTH(v116_expected_zero,1U);BOTH(v116_expected_value,0U);')
    assert tb.count(old) == 1
    files['tb_rice.cpp'] = tb.replace(old,new,1)
    # Every oracle body remains byte-identical. Only prepared-state setup is
    # adapted because BOTH V129 and its actual V116 baseline own a private
    # payload; the old V115 model had a directly writable output register.
    source_body = tb[tb.index('static void verify('):tb.index('static void rice_pre(')]
    adapted = files['tb_rice.cpp']
    assert source_body == adapted[adapted.index('static void verify('):adapted.index('static void rice_pre(')]
    assert adapted.replace(new,old,1) == tb
    outputs = {name:hashlib.sha256(text.encode()).hexdigest() for name,text in files.items()}
    metadata = dict(schema='v129-rice-paired-verification-adapter-v1',
                    status='PREPARED_NOT_EXECUTED',
                    source_original=dict(path=str(prior.relative_to(ROOT)),sha256=sha(prior)),
                    source_candidate=dict(path=str(candidate.relative_to(ROOT)),sha256=sha(candidate)),
                    preparer_sha256=sha(Path(__file__)),
                    inherited_probe_sha256=sha(OLD/'verification/rice_probe.sv'),
                    inherited_testbench_sha256=sha(OLD/'verification/tb_rice.cpp'),
                    inherited_historical_sha256=sha(OLD/'verification/historical_rice.cpp'),
                    inherited_view_directed_sha256=sha(OLD/'verification/view_directed.cpp'),
                    testbench_reversible_edit=dict(before=old,after=new,count=1),
                    probe_original_bytes_unchanged=True,historical_bytes_unchanged=True,
                    view_directed_bytes_unchanged=True,oracle_body_unchanged=True,
                    only_prepared_state_guard_initialization_changed=True,
                    declared_public_cycle_delta=0,original_assertions_retained=True,
                    outputs=outputs,scope='Actual paired real-interface and explicitly labeled prepared-state parser test, not full integration or physical timing.')
    if args.write:
        assert not V.exists()
        V.mkdir()
        for name, text in files.items():
            (V/name).write_text(text)
        (V/'adapters.json').write_text(json.dumps(metadata,indent=2,sort_keys=True)+'\n')
    else:
        for name, text in files.items():
            assert (V/name).read_text() == text
        assert json.loads((V/'adapters.json').read_text()) == metadata
    print(json.dumps(dict(status='PASS_SOURCE_ADAPTER_RECONSTRUCTION_NOT_RTL',files=outputs),sort_keys=True))


if __name__ == '__main__':
    main()
