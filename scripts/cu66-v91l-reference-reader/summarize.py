#!/usr/bin/env python3
"""Bind physical reference reader, native validation/RGB and model evidence."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'experiments/python-gamebub-v91l-reference-reader'
SHARED=['docs/gamebub-application-specific-codec-plan.md','docs/gamebub-v91-v110-development-plan.md',
        'docs/literature-review-2026-11-06/README.md']
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()
def read(path):return json.loads(path.read_text())
def fresh(path,report):
    for name,digest in report['source_sha256'].items():assert sha(ROOT/name)==sha(path.parent/'sources'/name)==digest,name
    for name,digest in report['artifacts_sha256'].items():assert sha(path.parent/name)==digest,name
    for name,digest in report.get('inputs_sha256',{}).items():assert sha(ROOT/name)==sha(path.parent/'inputs'/Path(name).name)==digest,name
    assert all(c['exit_code']==0 for c in report['commands'])
def main():
    audit=read(AREA/'audit.json')
    assert audit['status']=='PASS_INDEPENDENT_PHYSICAL_REFERENCE_LIVE_VALIDATION_AND_NATIVE_RGB'
    assert audit['verifier_sha256']==sha(AREA/'verify_results.py')
    assert audit['reference_verifier_sha256']==sha(AREA/'reference_trace.py')
    assert audit['unit_verifier_sha256']==sha(AREA/'unit_trace.py')
    prior=ROOT/'experiments/python-gamebub-v91l-shared-service'
    for name,digest in audit['prior_checker_sha256'].items():assert sha(prior/name)==digest,name
    for name,digest in {**audit['original_helper_sha256'],**audit['reviewed_source_sha256']}.items():assert sha(ROOT/name)==digest,name
    reports=[]
    for kind,alias in [('unit','fpga/experiments/cu66-v91l-reference-reader/results.json'),('live','fpga/experiments/cu66-v91l-reference-live/results.json')]:
        path=ROOT/audit[kind+'_report'];report=read(path)
        assert sha(path)==audit[kind+'_report_sha256']
        assert read(ROOT/alias)==dict(report,selected_report=str(path.relative_to(ROOT)))
        fresh(path,report);reports.append((path,report))
    up,unit=reports[0];lp,live=reports[1]
    assert len(unit['modes'])==3 and sum(m['verdict']['checks'] for m in unit['modes'])==1920
    assert len(audit['checker_negative_controls'])==28 and all(n['rejected'] for n in audit['checker_negative_controls'])
    assert len(audit['live_modes'])==4 and audit['exact_native_RGB_outputs']==8 and audit['rtl_sha_jobs']==8200
    assert {(m['seed'],m['t_ac_ns']) for m in audit['live_modes']}=={(s,t) for s in (912901,912902) for t in (2,7)}
    samples=[]
    for mode in audit['live_modes']:
        assert len(mode['frames'])==2 and mode['rtl_sha_jobs']==2050 and mode['presented_fids']==[0,1]
        assert mode['physical']['physical_write_words']==560640 and mode['physical']['physical_captured_words']==768192
        assert mode['physical']['require_prior_pin_write_for_every_native_read']
        assert mode['reference']['tile_requests']==mode['reference']['tile_responses']==7806
        assert mode['reference']['physical_BL8_reads']==31224 and mode['reference']['captured_x16_words']==249792
        assert mode['reference']['all_tiles_byte_exact'] and mode['reference']['full64_reference_identity_checked']
        runner=next(m for m in live['modes'] if (m['seed'],m['t_ac_ns'])==(mode['seed'],mode['t_ac_ns']))
        for frame,actual in zip(runner['frames'],mode['frames']):
            assert all(actual[k]==v for k,v in frame.items()),frame['id']
            samples.append(dict(seed=mode['seed'],t_ac_ns=mode['t_ac_ns'],**actual))
        assert runner['reference_tile_requests']==runner['reference_tile_responses']==7806
        assert runner['reference_bl8_requests']==runner['reference_bl8_responses']==31224
    model=read(AREA/'model-results.json');assert model['status']=='PASS_SOURCE_DERIVED_TRAFFIC_AND_BYTE_ASSEMBLY'
    for name,digest in model['frozen_inputs'].items():assert sha(ROOT/name)==digest,name
    assert model['physical_layout']['physical_address_bits']==19 and model['physical_layout']['physical_ticket_bits']==32
    assert model['physical_layout']['reference_generation_bits']==64
    subprocess.run(['python3',str(AREA/'reference_model.py'),'--check'],cwd=ROOT,check=True)
    generation=read(AREA/'generation-audit.json')
    assert generation['status']=='PASS_CAPTURE_ONLY_BYTE_IDENTICAL_GENERATION' and generation['verifier_sha256']==sha(AREA/'verify_generation.py')
    for name,digest in {**generation['source_sha256'],**generation['outputs_sha256']}.items():assert sha(ROOT/name)==digest,name
    ranges={}
    for fid in (0,1):
        selected=[f for f in samples if f['fid']==fid]
        ranges[str(fid)]={n:[min(f[n] for f in selected),max(f[n] for f in selected)] for n in
                         ('live_cycles','rgb_cycles','joint_serial_cycles','packet_complete_to_commit_cycles')}
    assert all(f['joint_serial_cycles']*30>100000000 for f in samples)
    summary=dict(schema='cu66-v91l-physical-reference-summary-v1',status='PASS_PHYSICAL_REFERENCE_LIVE_VALIDATION_AND_NATIVE_RGB',
        plan_version='V91l partial; V91m not promoted',reports=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p,r in reports],
        integrity={n:sha(AREA/n) for n in ('audit.json','verify_results.py','reference_trace.py','unit_trace.py','reference_model.py','model-results.json','verify_generation.py','generation-audit.json')},
        frames=samples,cycle_ranges_by_fid=ranges,assumed_source_clock_ns=10,modeled_memory_t_ac_ns=[2,7],seeds=[912901,912902],
        exact_native_base_RGB_outputs=8,distinct_native_source_images=2,rtl_SHA_jobs_checked=8200,
        directed_adapter_checks=698,directed_pin_checks_per_t_ac=611,directed_checks_total=1920,checker_corruptions_rejected=28,
        reference_tiles_per_delta=7806,reference_BL8_reads_per_delta=31224,reference_words_per_delta=249792,
        reference_bytes_per_delta=499584,additional_reference_buffer_bytes=64,
        candidate_pin_write_words_per_frame=280320,display_BL8_reads_per_frame=32400,display_captured_words_per_frame=259200,
        key_total_payload_words=539520,delta_total_payload_words=789312,
        full64_reference_identity_preserved=True,physical_address_bits=19,physical_ticket_bits=32,
        actual_reference_service_RTL=True,actual_live_producer_to_physical_writes=True,actual_RGB_from_same_pin_memory=True,
        no_canonical_or_pixel_SDRAM_preload=True,source_bank_lifetime_and_publication_checked=True,
        serial_live_commit_then_RGB=True,native_overlap_qualified=False,physical_scratch_service_qualified=False,
        full_RTL_HUD_decoder_overlay=False,common_all_client_service_complete=False,
        serial_nominal_30Hz_budget_met=False,achieved_clock_or_routed_timing=False,
        sustained_hardware_30fps_proven=False,complete_validated_decode_under10ms_proven=False,
        next='Move bounded packed-scratch service onto the same controller, then qualify native bank-safe overlap and full HUD/profile/source-cadence gates; preserve current reference-inclusive serial control for comparisons.')
    (AREA/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    directories=[AREA,ROOT/'fpga/experiments/cu66-v91l-reference-reader',ROOT/'fpga/experiments/cu66-v91l-reference-live',
                 ROOT/'scripts/cu66-v91l-reference-reader',ROOT/'scripts/cu66-v91l-reference-live',ROOT/'docs/cu66-v91l-reference-reader']
    files=[p for directory in directories for p in directory.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='bundle-manifest.json']
    files.extend(ROOT/n for n in SHARED)
    assert len(files)==len(set(files)) and all(p.stat().st_size<95*1024*1024 for p in files),'duplicate or oversized bundle artifact'
    (AREA/'bundle-manifest.json').write_text(json.dumps(dict(schema='cu66-v91l-physical-reference-bundle-v1',files={str(p.relative_to(ROOT)):sha(p) for p in sorted(files)}),indent=2)+'\n')
    print(json.dumps(dict(status=summary['status'],files=len(files),ranges=ranges)))
if __name__=='__main__':main()
