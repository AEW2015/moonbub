#!/usr/bin/env python3
"""Bind the selected V91 software and clocked-component evidence."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'experiments/python-gamebub-v91'
RTL=ROOT/'fpga/experiments/cu66-v91'


def read(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    paths=[AREA/name for name in ('corpus-results.json','corpus-audit.json','test-results.json',
                                  'native-results.json','native-audit.json')]
    paths += [RTL/'results.json',RTL/'independent-audit.json']
    corpus,audit,checks,native,naudit,rtl,raudit=[read(p) for p in paths]
    assert all(d['status']=='PASS' for d in (corpus,audit,checks,native,naudit,raudit))
    assert rtl['status']=='PASS_COMPONENT_SIMULATION'
    assert corpus['counts']['frames']==audit['frames']==457
    assert corpus['counts']['chunks']==audit['chunks']==1371
    assert raudit['public_result_sha256']==sha(RTL/'results.json')
    assert checks['parser_sha256']==sha(AREA/'parser.py')
    assert checks['detail_sha256']==sha(AREA/checks['detail_file'])
    assert corpus['source_sha256']['experiments/python-gamebub-v91/parser.py']==checks['parser_sha256']
    actual=[r for r in rtl['population_comparisons'] if r['population']=='actual']
    no_stall=next(r for r in actual if r['word_bits']==32 and r['stalls']==0)
    seeds={}
    for path in sorted((RTL/'attempts').glob('*/results.json')):
        r=read(path)
        if r['status']=='PASS_COMPONENT_SIMULATION' and r['source_sha256']==rtl['source_sha256']:
            assert r['vectors_sha256']==rtl['vectors_sha256']
            assert all(c['exit_code']==0 for c in r['commands'])
            cmd=next(c['argv'] for c in r['commands'] if c['log']=='compile.log')
            assert '-Wall' in cmd and '--assert' in cmd and '-Wno-fatal' not in cmd
            seeds[str(r['seed'])]=dict(path=str(path.relative_to(ROOT)),sha256=sha(path),
                                      verdict=r['verdict'])
    assert set(seeds)=={'910032','910033'}
    result=dict(schema='cu66-v91-combined-evidence-v1',
                status='PASS_REPRESENTATION_AND_RTL_COMPONENT_WITH_CPU_REGRESSION',
                evidence_sha256={str(p.relative_to(ROOT)):sha(p) for p in paths},
                encoded_sources=457,encoded_chunks=1371,encoded_coefficient_values=86444480,
                canonical_coefficient_hash_matches=457,unchanged_residual_chunk_bytes=4805106,
                python_directed_checks=checks['checks_count'],
                software_operation_counters=corpus['counters'],
                python_instrumented_candidate_bit_over_word=corpus['cpu_benchmark']['median_bit_over_word32'],
                native_cases_per_optimized_and_sanitizer_run=1388,
                native_paired_bit_over_word=native['optimized']['median_bit_over_word32'],
                native_candidate_is_speed_improvement=False,
                rtl_real_streams=48,rtl_real_source_frames=4,rtl_real_symbols=147327,
                rtl_total_vectors=1520,rtl_symbols_per_configuration=173061,
                rtl_seed_runs=seeds,rtl_actual_comparisons=actual,
                rtl_32bit_ready_cycle_reduction_percent=100*(1-no_stall['fast_cycles']/no_stall['serial_cycles']),
                new_wire_format=False,new_quantization=False,
                complete_pixel_HUD_publication_endpoint_newly_run=False,
                target_implementation_or_routed_frequency_proven=False,
                physical_30fps_proven=False,validated_complete_under10ms_proven=False,
                deployed_firmware_or_bitstream=False,
                next_gate='BR88 packet/context/run/scatter integration with finite credits and causal full-path calibration; retain native bit control. V92 entropy selection and V100-V110 physical phase remain planned.')
    (AREA/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(result['status'],'RTL real cycle reduction',round(result['rtl_32bit_ready_cycle_reduction_percent'],4))


if __name__=='__main__':main()
