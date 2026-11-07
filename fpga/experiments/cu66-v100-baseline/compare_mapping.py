#!/usr/bin/env python3
"""Compare complete mapped netlists/ports and fingerprints, not counts alone."""
import argparse
import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(build, dsp_stage=False):
    leaf = build / 'leaf-receipt.json'
    if leaf.exists():
        result = json.loads(leaf.read_text())
        if dsp_stage:
            checkpoint = result.get('dsp_stage', {})
            executed = 'Executing XILINX_DSP pass' in (build / 'mapping.log').read_text()
            return dict(build=str(build), kind='dsp_checkpoint', complete=bool(checkpoint) and executed,
                        source=result['converted_sha256'], recipe=result['recipe_sha256'],
                        tools=sha(build / 'tool-sha256.txt'), libraries=result.get('tool_library_catalog_sha256'),
                        original_inputs=result['original_source_manifest_sha256'], verification=result['verification_sha256'],
                        raw=checkpoint.get('raw_sha256'), semantic=checkpoint.get('canonical_sha256'),
                        ports=checkpoint.get('public_ports_preserved'), ports_ok=checkpoint.get('exact_port_names_directions_widths_preserved', False),
                        counts=checkpoint.get('cell_type_counts'), dsp=checkpoint.get('dsp48e1'),
                        report_sha256=sha(leaf), top=result['top'], actual_xilinx_dsp_pass_executed=executed)
        return dict(build=str(build), kind='leaf', complete=result['status'] == 'GENERIC_XC7_LEAF_MAPPED',
                    source=result['converted_sha256'], recipe=result['recipe_sha256'],
                    tools=sha(build / 'tool-sha256.txt'), libraries=result.get('tool_library_catalog_sha256'),
                    original_inputs=result['original_source_manifest_sha256'], verification=result['verification_sha256'],
                    raw=result.get('mapped_sha256'), semantic=result.get('canonical_netlist_sha256'),
                    ports=result.get('public_ports_preserved'), ports_ok=result.get('exact_port_names_directions_widths_preserved', False),
                    counts=result.get('primitive_counts'), dsp=result.get('dsp48e1'),
                    report_sha256=sha(leaf), top=result['top'])
    file = build / 'mapping.json'
    result = json.loads(file.read_text())
    summary = result.get('summary', {})
    conversion = json.loads((build / 'conversion.json').read_text())
    return dict(build=str(build), kind='component', complete=result['status'] == 'GENERIC_XC7_COMPONENT_MAPPED',
                source=result['converted_sha256'], recipe=result['recipe_sha256'],
                original_inputs=conversion['original_inputs_sha256'], verification=result['verification_receipt_sha256'],
                conversion_recipe=conversion['recipe_sha256'], tools=sha(build / 'tool-sha256.log'),
                libraries=sha(build / 'yosys-library-sha256.log'),
                raw=summary.get('mapped_netlist_sha256'), semantic=summary.get('provenance_normalized_sha256'),
                ports=summary.get('public_ports_verified'), ports_ok=summary.get('all_public_names_directions_widths_preserved', False),
                counts=summary.get('primitive_counts'), dsp=summary.get('dsp48e1'), report_sha256=sha(file), top='cs88_pipeline_v91k')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('a', type=Path)
    parser.add_argument('b', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--dsp-stage', action='store_true', help='Compare actual partial post-map_dsp checkpoints only')
    args = parser.parse_args()
    rows = [read(x, args.dsp_stage) for x in (args.a, args.b)]
    a, b = rows
    fingerprint_keys = ['source', 'original_inputs', 'recipe', 'tools', 'libraries', 'verification', 'top', 'kind']
    if a['kind'] == 'component' and b['kind'] == 'component':
        fingerprint_keys += ['conversion_recipe']
    matches = {key: a.get(key) == b.get(key) for key in fingerprint_keys}
    both_complete = all(x['complete'] for x in rows)
    semantic_equal = a['semantic'] is not None and a['semantic'] == b['semantic']
    ports_equal = a['ports_ok'] and b['ports_ok'] and a['ports'] == b['ports']
    counts_equal = a['counts'] is not None and a['counts'] == b['counts']
    qualified = both_complete and all(matches.values()) and semantic_equal and ports_equal and counts_equal
    success = 'REPEATABLE_PARTIAL_DSP_STAGE' if args.dsp_stage else 'REPEATABLE_GENERIC_XC7_MAPPING'
    result = dict(schema='v100-generic-xc7-mapping-repeatability-v1',
                  status=success if qualified else 'NOT_ESTABLISHED',
                  inputs=rows, fingerprint_matches=matches, both_mapping_complete=both_complete,
                  complete_semantic_netlists_equal=semantic_equal, raw_netlist_hashes_equal=a['raw'] is not None and a['raw'] == b['raw'],
                  full_public_port_contracts_preserved=ports_equal, primitive_counts_equal=counts_equal,
                  comparator_sha256=sha(Path(__file__)), exact_target_part_fit=False,
                  partial_DSP_checkpoint_only=args.dsp_stage, complete_leaf_technology_mapping_qualified=qualified and not args.dsp_stage,
                  physical_route_or_timing_qualified=False, hardware_cadence_qualified=False,
                  note='Success requires full netlist canonical equality including every cell parameter/connection and public port, plus tool/source/recipe hashes. Counts alone cannot qualify repeatability.')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(dict(status=result['status'], raw_equal=result['raw_netlist_hashes_equal'], semantic_equal=semantic_equal)))


if __name__ == '__main__':
    main()
