#!/usr/bin/env python3
"""Bind measured native concurrency to immutable serial control and exact bytes."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'experiments/python-gamebub-v91l-overlap'
SHARED=['docs/gamebub-application-specific-codec-plan.md','docs/gamebub-v91-v110-development-plan.md','docs/literature-review-2026-11-06/README.md']
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()
def read(p):return json.loads(p.read_text())
def fresh(path,report):
    for n,d in report['source_sha256'].items():assert sha(ROOT/n)==sha(path.parent/'sources'/n)==d,n
    for n,d in report['artifacts_sha256'].items():assert sha(path.parent/n)==d,n
    for n,d in report.get('inputs_sha256',{}).items():assert sha(ROOT/n)==sha(path.parent/'inputs'/Path(n).name)==d,n
    assert all(c['exit_code']==0 for c in report['commands'])
def main():
    audit=read(AREA/'audit.json');assert audit['status']=='PASS_INDEPENDENT_NATIVE_DECODE_DISPLAY_OVERLAP'
    assert audit['verifier_sha256']==sha(AREA/'verify_results.py') and audit['lease_verifier_sha256']==sha(AREA/'lease_trace.py')
    for n,d in {**audit['reviewed_source_sha256'],**audit['inherited_checker_sha256'],**audit['original_helper_sha256']}.items():assert sha(ROOT/n)==d,n
    assert audit['directed_checks']==147 and len(audit['checker_negative_controls'])==14 and all(e['rejected'] for e in audit['checker_negative_controls'])
    assert len(audit['live_modes'])==5 and audit['exact_native_RGB_outputs']==10 and audit['rtl_sha_jobs']==10250
    reports=[]
    for kind,alias in [('unit','fpga/experiments/cu66-v91l-overlap-lease/results.json'),('live','fpga/experiments/cu66-v91l-overlap-live/results.json')]:
        p=ROOT/audit[kind+'_report'];r=read(p);assert sha(p)==audit[kind+'_report_sha256']
        assert read(ROOT/alias)==dict(r,selected_report=str(p.relative_to(ROOT)))
        fresh(p,r);reports.append((p,r))
    generation=read(AREA/'generation-audit.json');assert generation['status']=='PASS_CAPTURE_ONLY_BYTE_IDENTICAL_GENERATION' and generation['verifier_sha256']==sha(AREA/'verify_generation.py')
    for n,d in {**generation['source_sha256'],**generation['outputs_sha256']}.items():assert sha(ROOT/n)==d,n
    streams=read(AREA/'stream-audit.json');assert streams['status']=='PASS_LOSSLESS_CHUNKS_AND_RAW_TERMINAL_VERDICTS'
    assert streams['verifier_sha256']==sha(AREA/'verify_streams.py') and streams['report']==audit['live_report'] and streams['report_sha256']==audit['live_report_sha256'] and len(streams['modes'])==5
    traffic=read(AREA/'pin-traffic-results.json');assert traffic['status']=='PASS_ACTUAL_PIN_COMMAND_COUNTS' and traffic['selection']['final_selected_overlap_natural_mode_available']
    assert traffic['pin_oracle_crosscheck']['available'] and traffic['pin_oracle_crosscheck']['equal']
    assert traffic['primary_overlap']['report_path']==audit['live_report'] and traffic['primary_overlap']['report_sha256']==audit['live_report_sha256']
    for entry in [traffic['baseline'],traffic['primary_overlap']]+([traffic['separate_bringup']] if traffic['separate_bringup'] else []):
        assert sha(ROOT/entry['report_path'])==entry['report_sha256']
        for n,d in entry['pin_log_sha256'].items():assert sha(ROOT/n)==d,n
    observed=next(m for m in audit['live_modes'] if m['seed']==912901 and m['t_ac_ns']==2 and not m['guard_mode'])
    command_map={'MRS':'mode_register','REFRESH':'refresh','PRECHARGE':'precharge','ACTIVATE':'activate','WRITE':'write','READ':'read'}
    assert all(traffic['primary_overlap']['scan']['commands'][n]==observed['physical']['pin_commands'][mapped] for n,mapped in command_map.items())
    subprocess.run(['python3',str(AREA/'overlap_model.py'),'--check'],cwd=ROOT,check=True)
    model=read(AREA/'model-results.json');assert model['status']=='PASS_ABSTRACT_BANK_LEASES_AND_IDEAL_OVERLAP_BOUNDS'
    packaging=read(AREA/'packaging-check.json');assert packaging['status']=='PASS_EXACT_RAW_ARTIFACT_WHITESPACE_EXCEPTIONS' and not packaging['compiler_warning_waivers']
    for e in packaging['exceptions']:assert sha(ROOT/e['path'])==e['sha256'],e['path']
    baseline=ROOT/'experiments/python-gamebub-v91l-scratch-service/summary.json';control=read(baseline)
    assert control['status']=='PASS_PHYSICAL_SCRATCH_LIVE_VALIDATION_AND_NATIVE_RGB'
    measured=[];guarded=[];samples=[];runner=reports[1][1]
    for mode in audit['live_modes']:
        assert mode['physical']['physical_write_words']==616872 and mode['physical']['physical_captured_words']==824424
        assert mode['physical']['require_prior_pin_write_for_every_native_read'] and mode['physical']['scratch_transactions']==14058
        assert mode['reference']['tile_requests']==mode['reference']['tile_responses']==7806 and mode['reference']['physical_BL8_reads']==31224
        assert mode['lease']['accepted']==mode['lease']['releases']==2 and mode['lease']['rejected']==0
        assert mode['presented_fids']==[0,1] and mode['native_overlap_cycles']>0
        actual=next(m for m in runner['modes'] if (m['seed'],m['t_ac_ns'],m['guard_mode'])==(mode['seed'],mode['t_ac_ns'],mode['guard_mode']))
        for f,r in zip(mode['frames'],actual['frames']):assert all(f[k]==v for k,v in r.items()),f['id']
        base=[f for f in control['frames'] if (f['seed'],f['t_ac_ns'])==(mode['seed'],mode['t_ac_ns'])];assert [f['fid'] for f in base]==[0,1]
        serial=base[1]['closed_cycle']-base[0]['native_start_cycle'];pair=mode['pair_start_to_final_rgb_cycles']
        comparison=dict(seed=mode['seed'],t_ac_ns=mode['t_ac_ns'],guard_mode=mode['guard_mode'],serial_control_pair_cycles=serial,overlap_pair_cycles=pair,pair_reduction_percent=(serial-pair)*100/serial,
                        delta_decode_cycles=mode['frames'][1]['decode_cycles'],control_delta_decode_cycles=base[1]['live_cycles'],overlap_interval_cycles=mode['native_overlap_cycles'],concurrent_handshakes=mode['concurrent_handshakes'])
        (guarded if mode['guard_mode'] else measured).append(comparison)
        samples.extend(dict(seed=mode['seed'],t_ac_ns=mode['t_ac_ns'],guard_mode=mode['guard_mode'],**f) for f in mode['frames'])
    assert len(measured)==4 and len(guarded)==1
    assert {(m['seed'],m['t_ac_ns']) for m in measured}=={(s,t) for s in (912901,912902) for t in (2,7)}
    ranges={}
    for n in ('serial_control_pair_cycles','overlap_pair_cycles','delta_decode_cycles','pair_reduction_percent','overlap_interval_cycles'):
        ranges[n]=[min(m[n] for m in measured),max(m[n] for m in measured)]
    assert all(m['overlap_pair_cycles']<m['serial_control_pair_cycles'] and m['delta_decode_cycles']>m['control_delta_decode_cycles'] and m['delta_decode_cycles']*30>100000000 for m in measured)
    summary=dict(schema='cu66-v91l-native-overlap-summary-v1',status='PASS_NATIVE_DECODE_DISPLAY_OVERLAP',plan_version='V91l partial; V91m not promoted',
        reports=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p,r in reports],control_summary=dict(path=str(baseline.relative_to(ROOT)),sha256=sha(baseline)),
        integrity={n:sha(AREA/n) for n in ('audit.json','verify_results.py','lease_trace.py','overlap_model.py','model-results.json','model-contract.md','reviewed-source-hashes.json','verify_generation.py','generation-audit.json','packaging-check.json','verify_streams.py','stream-audit.json','pin_traffic.py','pin-traffic-results.json','audit-review.md')},
        assumed_source_clock_ns=10,seeds=[912901,912902],modeled_memory_t_ac_ns=[2,7],natural_comparisons=measured,directed_guard_comparisons=guarded,natural_ranges=ranges,frames=samples,
        exact_native_base_RGB_outputs=10,distinct_native_source_images=2,rtl_SHA_jobs_checked=10250,directed_guard_checks=147,checker_corruptions_rejected=14,
        matched_pin_traffic_comparison=traffic['comparisons'][0],
        actual_native_shared_controller_overlap_qualified=True,directed_old_key_lease_after_delta_commit=True,all_external_memory_endpoints_rtl=True,canonical_or_pixel_preload=False,new_display_payload_memory_bytes=0,
        source_resolution=[720,480],codec_bytes_quality_changed=False,native_software_HUD_endpoint=True,full_RTL_HUD_decoder_overlay=False,hardware_overlap_qualified=False,
        fixed_source_30Hz_qualified=False,sustained_hardware_30fps_proven=False,complete_validated_decode_under10ms_proven=False,achieved_clock_or_routed_timing=False,
        next='Use actual contention/waits to qualify one bounded arbitration/reference-reuse/prefetch change with exact pixels and leases; close full HUD/profile/fixed source cadence/ESP32 and Series7 hardware gates.')
    (AREA/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    def ms(pair):return f'{pair[0]/100000:.5f}–{pair[1]/100000:.5f}'
    lines=['# Native overlap measured results','','Times use actual cycle fences converted at an assumed 100 MHz. These are behavioral/timed-model results, not an achieved hardware clock or fixed-source frame cadence.','',
        '| Metric | Four natural modes |','|---|---:|',f'| Serial control: key start → final delta RGB closure | {ms(ranges["serial_control_pair_cycles"])} ms |',f'| Overlap: same two-source completion interval | {ms(ranges["overlap_pair_cycles"])} ms |',f'| Pair interval reduction | {ranges["pair_reduction_percent"][0]:.2f}–{ranges["pair_reduction_percent"][1]:.2f}% |',f'| Delta start → validated commit with competing display | {ms(ranges["delta_decode_cycles"])} ms |',f'| Actual key-display/delta-decode overlap interval | {ms(ranges["overlap_interval_cycles"])} ms |','',
        'The lower pair interval comes with increased delta decoding latency under contention. The serial control delta took 33.460–33.465 ms; overlap alone does not satisfy a 33.333-ms source-frame slot. The independent Python zero-contention arithmetic is a lower bound and is not used as the measured result.','',
        'All five modes preserve two complete source RGB outputs each: ten byte-exact RGB files, 10,250 actual RTL SHA jobs, original canonical/HUD commitments and accepted quantizer history. Per key/delta pair, common memory performs 616,872 WRITE words and captures 824,424 READ words, including 14,058 scratch requests. The SDRAM oracle is populated only by observed pin writes; canonical/pixel preload is absent.','',
        'The separate native guard run holds the final key pixel across delta commit plus 17 clocks with external vblank/drain hints asserted. Actual display ownership keeps the old key front while accepted reference advances to the delta, then permits publication only after consumer/physical drain. Its timings are excluded from the natural table. Standalone tests pass 147 checks and independent replay rejects 14 deliberate lease-trace corruptions.','',
        'The corpus remains two distinct native source images. Full RTL HUD interpretation/composition, mixed entropy or explicit tested fallback, actual ESP32/transport timing, fixed-cadence V91m and whole-device physical/hardware qualification remain open. Hardware 30 fps and complete validated decoding strictly below 10 ms are not proven.','']
    locality=traffic['comparisons'][0]['comparison']['commands']
    lines += [f'For the matched seed 912901/tAC 2 case, actual ACTIVATE commands increase from {locality["ACTIVATE"]["baseline"]:,} to {locality["ACTIVATE"]["overlap"]:,} ({locality["ACTIVATE"]["percent"]:.2f}%), while READ/WRITE command counts stay identical. This points to row locality as a next experiment; frequencies alone do not attribute all elapsed time to one cause. Per-bank PRECHARGE counts refer to the pin bank field; A10 precharge-all affects multiple banks.','']
    (ROOT/'docs/cu66-v91l-overlap/results.md').write_text('\n'.join(lines))
    directories=[AREA,ROOT/'fpga/experiments/cu66-v91l-overlap-lease',ROOT/'fpga/experiments/cu66-v91l-overlap-live',ROOT/'scripts/cu66-v91l-overlap-lease',ROOT/'scripts/cu66-v91l-overlap-live',Path(__file__).resolve().parent,ROOT/'docs/cu66-v91l-overlap']
    files=[p for d in directories for p in d.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='bundle-manifest.json'];files.extend(ROOT/n for n in SHARED)
    assert len(files)==len(set(files)) and all(p.stat().st_size<95*1024*1024 for p in files)
    (AREA/'bundle-manifest.json').write_text(json.dumps(dict(schema='cu66-v91l-native-overlap-bundle-v1',files={str(p.relative_to(ROOT)):sha(p) for p in sorted(files)}),indent=2)+'\n')
    print(json.dumps(dict(status=summary['status'],files=len(files),natural_ranges=ranges)))
if __name__=='__main__':main()
