#!/usr/bin/env python3
"""Bind independent read/capture/base-RGB evidence and keep milestone scopes explicit."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'experiments/python-gamebub-v91l-readbridge'
SHARED=['docs/gamebub-application-specific-codec-plan.md','docs/gamebub-v91-v110-development-plan.md','docs/literature-review-2026-11-06/README.md']

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())

def bind(audit,script):
    need=audit['verifier_sha256']==sha(AREA/script)
    assert need,'stale verifier: '+script
    path=ROOT/audit['selected_report']
    assert sha(path)==audit['report_sha256']
    report=read(path)
    for n,h in report['source_sha256'].items():assert sha(ROOT/n)==sha(path.parent/'sources'/n)==h,n
    for n,h in report['artifacts_sha256'].items():assert sha(path.parent/n)==h,n
    for n,h in report['inputs_sha256'].items():assert sha(ROOT/n)==sha(path.parent/'inputs'/Path(n).name)==h,n
    assert all(c['exit_code']==0 for c in report['commands'])
    return path,report

def main():
    bridge=read(AREA/'audit-readbridge.json')
    assert bridge['status']=='PASS_TIMED_READBRIDGE_PIN_CAPTURE_FENCE_AND_NATIVE_OUTPUT_AUDIT'
    bp,br=bind(bridge,'verify_readbridge.py')
    assert len(bridge['modes'])==8 and sum(m['verdict']['checks'] for m in bridge['modes'])==132
    assert sum(m['verdict']['read_words'] for m in bridge['modes'])==3111744
    assert len(bridge['checker_negative_controls'])==32 and all(c['rejected'] for c in bridge['checker_negative_controls'])
    rgb=read(AREA/'audit-converter.json')
    assert rgb['status']=='PASS_INDEPENDENT_NATIVE_RGB565_JOIN_AUDIT'
    cp,cr=bind(rgb,'verify_converter.py')
    assert len(rgb['modes'])==4 and len(rgb['checker_negative_controls'])==32
    assert all(c['rejected'] for c in rgb['checker_negative_controls'])
    assert len(cr['modes'])==4 and sum(m['verdict']['checks'] for m in cr['modes'])==52
    timed_pins=read(AREA/'audit-timed-pins.json')
    assert timed_pins['status']=='PASS_INDEPENDENT_TIME_MERGED_RGB_SDRAM_PIN_AUDIT'
    tp,tr=bind(timed_pins,'verify_timed_pins.py')
    joined=rgb['timed_rgb']
    assert joined['status']=='PASS_INDEPENDENT_TIMED_BASE_RGB_FILES_AND_CONTROLLER_WORDS'
    assert joined['selected_report']==str(tp.relative_to(ROOT)) and joined['report_sha256']==sha(tp)
    assert len(joined['modes'])==4 and len(timed_pins['modes'])==4
    assert all(c['rejected'] for c in timed_pins['checker_negative_controls'])
    assert all(c['rejected'] for c in joined['checker_negative_controls'])
    assert tr['status']=='PASS_NATIVE_RGB565_ACTUAL_TIMED_SDRAM'
    assert tr['actual_converter_rtl_join'] and tr['physical_sdram_controller_join']
    assert len(tr['modes'])==4 and tr['seeds']==[912701,912702] and tr['t_ac_ns']==[2,7]
    assert sum(m['verdict']['checks'] for m in tr['modes'])==28
    for k in ('shared_service_complete','physical_hardware_tested','sustained_hardware_30fps_proven','validated_full_frame_decode_under10ms_proven'):
        assert tr[k] is False,k
    budget=read(AREA/'audit-budget.json')
    assert budget['verifier_sha256']==sha(AREA/'verify_budget.py') and budget['report_sha256']==sha(AREA/'read-budget-results.json')
    model=read(AREA/'read-budget-results.json')
    assert model['generator_sha256']==sha(AREA/'read_budget.py')
    for name,h in model['source_sha256'].items():assert sha(ROOT/name)==h
    timed=[]
    for mode in tr['modes']:
        assert len(mode['frames'])==2
        for frame in mode['frames']:
            assert frame['pixels']==345600 and frame['bytes']==691200
            assert frame['logical_reads']==frame['physical_reads']==32400
            timed.append(dict(seed=mode['seed'],t_ac_ns=mode['t_ac_ns'],**frame))
    result=dict(schema='cu66-v91l-physical-read-and-base-rgb-summary-v1',status='PASS_PHYSICAL_READ_AND_BASE_RGB_COMPONENT_JOINS',
                plan_version='V91l partial; not promoted to V91m',
                selected_reports=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in (bp,cp,tp)],
                readbridge_comparisons=bridge['comparisons'],actor_rgb_comparisons=cr['comparisons'],timed_base_rgb_frames=timed,
                integrity={n:sha(AREA/n) for n in ('audit-readbridge.json','audit-converter.json','audit-timed-pins.json','audit-budget.json','verify_readbridge.py','verify_converter.py','verify_timed_pins.py','verify_budget.py','read_budget.py','read-budget-results.json')},
                readbridge_checks=132,readbridge_pin_capture_word_comparisons=3111744,
                actor_rgb_checks=52,actor_exact_base_rgb_outputs=8,timed_rgb_checks=28,timed_exact_base_rgb_outputs=8,
                nominal_source_clock_ns=10,retained_data_bytes=1472,retained_metadata_included=False,
                actual_controller_base_rgb_join=True,initial_canonical_preload_outside_fences=True,
                live_codec_physical_writer_join=False,semantic_hud_decode_overlay_qualified=False,common_physical_service_complete=False,
                achieved_clock_or_board_timing_qualified=False,sustained_hardware_30fps_proven=False,validated_complete_decode_under10ms=False,
                next='Preserve this scalar timed control; compare direct canonical-burst consumption using state/wait evidence, then join live producer/validation and all physical-memory clients with explicit ownership and deadlines.')
    (AREA/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    paths=[]
    for directory in (AREA,ROOT/'fpga/experiments/cu66-v91l-readbridge',ROOT/'fpga/experiments/cu66-v91l-converter',ROOT/'scripts/cu66-v91l-readbridge',ROOT/'scripts/cu66-v91l-converter',ROOT/'docs/cu66-v91l-readbridge'):
        paths.extend(p for p in directory.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='bundle-manifest.json')
    paths.extend(ROOT/n for n in SHARED)
    (AREA/'bundle-manifest.json').write_text(json.dumps(dict(schema='cu66-v91l-readbridge-bundle-v1',files={str(p.relative_to(ROOT)):sha(p) for p in sorted(paths)}),indent=2)+'\n')
    print(result['status'],len(paths),'manifest files')
if __name__=='__main__':main()
