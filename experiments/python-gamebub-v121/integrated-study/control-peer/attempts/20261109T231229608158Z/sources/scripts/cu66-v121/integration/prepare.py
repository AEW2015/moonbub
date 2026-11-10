#!/usr/bin/env python3
"""Derive V121 integration adapters reversibly; no simulation or source edits."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
AREA = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def derive():
    records = []
    pins = {
        'spatial.py': '5034d6e2ab6ce6bdf2d9de57199a438a69da6e9f50fb9cb4b1628f507fd274ab',
        'peer.py': '42f963d12c9dfc1d8717ffbbe75b4b6fa0c8494b33866fb36f88c45cfcb1372f',
        'live_guard/qualify.py': '871d4a09782e9b6333cad55a81b89430cdc362c890680dac41f1d629786a529d'}
    for name, expected in pins.items():
        old = ROOT/'scripts/cu66-v120/admission_repair'/name
        assert sha(old) == expected
        text = old.read_text()
        edits = []

        def edit(before, after, count=1):
            nonlocal text
            assert text.count(before) == count, (name, before, text.count(before), count)
            text = text.replace(before, after)
            edits.append(dict(before=before, after=after, count=count))

        edit('experiments/python-gamebub-v120/repair-study/', 'experiments/python-gamebub-v121/integrated-study/', 1 if name != 'live_guard/qualify.py' else 2)
        edit('v120-admission-repair-', 'v121-request-', 5 if name == 'spatial.py' else 2)
        if name == 'spatial.py':
            edit('from pathlib import Path', 'from pathlib import Path\nimport sys\nsys.dont_write_bytecode=True')
            edit("B_CANONICAL=ROOT/'experiments/python-gamebub-v119/integrated-study/spatial/results.json'", "B_CANONICAL=ROOT/'experiments/python-gamebub-v120/repair-study/spatial/results.json'")
            edit("OVERRIDES={", "OVERRIDES={\n 'byte_refill_queue_v91i2b.sv':ROOT/'fpga/experiments/cu66-v121-request/byte_refill_queue_v91i2b.sv',")
            edit("FOCUSED={", "FOCUSED={\n 'experiments/python-gamebub-v121/request/results.json':['byte_refill_queue_v91i2b.sv'],")
            edit('len(replacements)==9', 'len(replacements)==10')
            edit("b['status']=='PASS_V119_FINAL_SPATIAL_CANONICAL'", "b['status']=='PASS_V120_FINAL_SPATIAL_CANONICAL'")
            edit("'PASS_V120_FINAL_SPATIAL_CANONICAL'", "'PASS_V121_FINAL_SPATIAL_CANONICAL'", 2)
            # The previous edit also touches the selected frozen B status; undo
            # that one expected input token, retaining the new output status.
            edit("b['status']=='PASS_V121_FINAL_SPATIAL_CANONICAL'", "b['status']=='PASS_V120_FINAL_SPATIAL_CANONICAL'")
            edit('V120_SPATIAL_PREPARED_NOT_RUN', 'V121_SPATIAL_PREPARED_NOT_RUN')
            edit("print('V120_SPATIAL'", "print('V121_SPATIAL'")
            edit(" proofs=[ROOT/name for name in FOCUSED]", " import runpy\n contract=runpy.run_path(str(ROOT/'scripts/cu66-v121/integration/contract.py'))\n contract['verify']()\n contract['source_map'](sources,origins)\n proofs=[ROOT/name for name in FOCUSED]")
            edit(' files=set(sources+[', " files=set(contract['files']()+sources+[")
            edit("contract='V120 range prefix plus phase-local full35 admission packet-total equality payload; exact V119 public values/events/cycles, error priority, owners and physical debt. New focused prepared HEADER_CHECK fixtures prime one coherent real predecessor edge in both models; natural packets gain no public edges. All other selected bodies remain V119.'", "contract='V121 full32 accepted-request cursor; only refill queue changes from qualified Source B. All public values, ordering, event cycles, canonical hashes, error priority and physical debt are exact to Source B; declared cycle delta is zero.'")
        elif name == 'peer.py':
            edit('scripts/cu66-v120/admission_repair/spatial.py', 'scripts/cu66-v121/integration/spatial.py')
            edit('len(replacements)==9', 'len(replacements)==10')
            edit(" files=sorted(set(files+[", " import runpy\n contract=runpy.run_path(str(R/'scripts/cu66-v121/integration/contract.py'));contract['verify']()\n bpath,baseline=contract['baseline']('control-peer');files+=contract['files']()+[bpath]\n files=sorted(set(files+[")
            edit("   r['runs'].append(v[0])", "   oldlines=[json.loads(x) for x in (bpath.parent/(prefix+'-simulation.jsonl')).read_text().splitlines()]\n   assert lines==oldlines,'V121 peer stdout/event cycles changed from Source B'\n   for suffix in ('events.jsonl','canonical.tsv'):\n    assert (build/(prefix+'-'+suffix)).read_bytes()==gzip.decompress((bpath.parent/(prefix+'-'+suffix+'.gz')).read_bytes()),suffix\n   r['runs'].append(v[0])")
            edit("print('V120_CONTROL_PEER'", "print('V121_CONTROL_PEER'")
            edit('V120_CONTROL_PEER_PREPARED_NOT_RUN', 'V121_CONTROL_PEER_PREPARED_NOT_RUN')
        else:
            edit('scripts/cu66-v120/admission_repair/spatial.py', 'scripts/cu66-v121/integration/spatial.py', 2)
            edit("selected['status'] == 'PASS_V120_FINAL_SPATIAL_CANONICAL'", "selected['status'] == 'PASS_V121_FINAL_SPATIAL_CANONICAL'")
            edit('experiments/python-gamebub-v119/integrated-study/live-guard/results.json', 'experiments/python-gamebub-v120/repair-study/live-guard/results.json')
            edit("baseline_B['status']=='PASS_V119_SELECTED_COMPONENT_BYTE_ROW_ACK_C2_HUD_ABSTRACT_PUBLICATION'", "baseline_B['status']=='PASS_V120_SELECTED_COMPONENT_BYTE_ROW_ACK_C2_HUD_ABSTRACT_PUBLICATION'")
            edit("'PASS_V120_SELECTED_COMPONENT_'", "'PASS_V121_SELECTED_COMPONENT_'")
            edit('V120_LIVE_PARENT_PREPARED_NOT_RUN', 'V121_LIVE_PARENT_PREPARED_NOT_RUN')
            edit("print('V120_LIVE_PARENT'", "print('V121_LIVE_PARENT'")
            edit("    derivation = verify_derivation()", "    import runpy\n    contract=runpy.run_path(str(ROOT/'scripts/cu66-v121/integration/contract.py'));contract['verify']()\n    derivation = verify_derivation()")
            edit('    proof_files = []', "    proof_files = contract['files']()")
        records.append(dict(original=str(old.relative_to(ROOT)), original_sha256=expected,
                            candidate=str((AREA/name).relative_to(ROOT)),
                            candidate_sha256=hashlib.sha256(text.encode()).hexdigest(), edits=edits, text=text))
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    records = derive()
    data = dict(schema='v121-integration-adapters-v1', old_oracle_checks_removed=0,
                exact_source_B_cycle_delta=0, sources=[{k:v for k,v in record.items() if k != 'text'} for record in records])
    for record in records:
        path = ROOT/record['candidate']
        if args.write:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(record['text'])
        else:
            assert path.read_text() == record['text']
    path = AREA/'derivation.json'
    if args.write:
        path.write_text(json.dumps(data, indent=2, sort_keys=True)+'\n')
    else:
        assert json.loads(path.read_text()) == data
    print('V121_INTEGRATION_ADAPTERS_PREPARED_NOT_RUN', len(records))


if __name__ == '__main__':
    main()
