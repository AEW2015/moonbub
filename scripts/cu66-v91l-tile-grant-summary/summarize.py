#!/usr/bin/env python3
"""Bind one bounded grant-policy experiment to its frozen matched workload."""
import hashlib
import json
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[2];AREA=ROOT/'experiments/python-gamebub-v91l-tile-grant'
SHARED=['docs/gamebub-application-specific-codec-plan.md','docs/gamebub-v91-v110-development-plan.md','docs/literature-review-2026-11-06/README.md']
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()
def read(p):return json.loads(p.read_text())
def fresh(p,r):
    for n,d in r['source_sha256'].items():assert sha(ROOT/n)==sha(p.parent/'sources'/n)==d,n
    for n,d in r['artifacts_sha256'].items():assert sha(p.parent/n)==d,n
    for n,d in r.get('inputs_sha256',{}).items():assert sha(ROOT/n)==sha(p.parent/'inputs'/Path(n).name)==d,n
    assert all(c['exit_code']==0 for c in r['commands'])
def main():
    a=read(AREA/'audit.json');assert a['status']=='PASS_INDEPENDENT_BOUNDED_REFERENCE_GRANTS'
    assert a['verifier_sha256']==sha(AREA/'verify_results.py') and a['grant_verifier_sha256']==sha(AREA/'grant_trace.py')
    for n,d in {**a['reviewed_source_sha256'],**a['inherited_checker_sha256'],**a['original_helper_sha256']}.items():assert sha(ROOT/n)==d,n
    assert a['directed_checks']==2056 and len(a['checker_negative_controls'])==18 and all(n['rejected'] for n in a['checker_negative_controls'])
    assert a['exact_native_RGB_outputs']==10 and a['rtl_sha_jobs']==10250 and len(a['live_modes'])==5
    reports=[]
    for kind,alias in [('unit','fpga/experiments/cu66-v91l-tile-grant/results.json'),('live','fpga/experiments/cu66-v91l-tile-grant-live/results.json')]:
        p=ROOT/a[kind+'_report'];r=read(p);assert sha(p)==a[kind+'_report_sha256'] and read(ROOT/alias)==dict(r,selected_report=str(p.relative_to(ROOT)))
        fresh(p,r);reports.append((p,r))
    streams=read(AREA/'stream-audit.json');assert streams['status']=='PASS_LOSSLESS_CHUNKS_AND_RAW_TERMINAL_VERDICTS' and streams['verifier_sha256']==sha(AREA/'verify_streams.py')
    assert streams['report']==a['live_report'] and streams['report_sha256']==a['live_report_sha256'] and len(streams['modes'])==5
    generation=read(AREA/'generation-audit.json');assert generation['status']=='PASS_CAPTURE_ONLY_BYTE_IDENTICAL_GENERATION' and generation['verifier_sha256']==sha(AREA/'verify_generation.py')
    for n,d in {**generation['source_sha256'],**generation['outputs_sha256']}.items():assert sha(ROOT/n)==d,n
    source=ROOT/'fpga/experiments/cu66-v91l-overlap-live/tb_overlap_live.cpp';candidate=ROOT/'fpga/experiments/cu66-v91l-tile-grant-live/tb_tile_grant_live.cpp'
    assert candidate.read_bytes()==source.read_bytes().replace(b'Voverlap_live',b'Vtile_grant_live'),'workload or PRNG changed'
    subprocess.run(['python3',str(AREA/'grant_model.py'),'--check'],cwd=ROOT,check=True)
    model=read(AREA/'model-results.json');assert model['status']=='PASS_TILE_GRANT_CONTRACT_MODEL'
    packaging=read(AREA/'packaging-check.json');assert packaging['status']=='PASS_EXACT_RAW_ARTIFACT_WHITESPACE_EXCEPTIONS' and not packaging['compiler_warning_waivers']
    for e in packaging['exceptions']:assert sha(ROOT/e['path'])==e['sha256'],e['path']
    baseline=ROOT/'experiments/python-gamebub-v91l-overlap/summary.json';control=read(baseline);assert control['status']=='PASS_NATIVE_DECODE_DISPLAY_OVERLAP'
    baseline_audit_path=ROOT/'experiments/python-gamebub-v91l-overlap/audit.json'
    assert sha(baseline_audit_path)==control['integrity']['audit.json'],'frozen comparison audit drifted'
    assert baseline.read_bytes()==subprocess.check_output(['git','show','4d6872f428beb902498d2cee4c509e643cd5aa78:'+str(baseline.relative_to(ROOT))],cwd=ROOT)
    baseline_audit=read(baseline_audit_path)
    comparisons=[];guards=[];frames=[]
    for mode in a['live_modes']:
        policy=mode['physical']['reference_grant_policy'];assert policy['limit']==4 and policy['groups_started']==7806 and policy['continuations']==23418
        assert policy['group_request_histogram']=={'4':7806} and policy['yield_reasons']=={'0':7806} and policy['max_reference_lines_per_grant']==4
        assert policy['display_wait_canceled']==0 and policy['display_wait_intervals']==policy['display_requests']==64800,'native display wait metadata claims cancellation or omits a request'
        assert mode['physical']['physical_write_words']==616872 and mode['physical']['physical_captured_words']==824424
        assert mode['physical']['require_prior_pin_write_for_every_native_read'] and mode['presented_fids']==[0,1]
        base=next(m for m in baseline_audit['live_modes'] if (m['seed'],m['t_ac_ns'],m['guard_mode'])==(mode['seed'],mode['t_ac_ns'],mode['guard_mode']))
        assert [f['fid'] for f in base['frames']]==[0,1]
        original_pair=base['pair_start_to_final_rgb_cycles'];new_pair=mode['pair_start_to_final_rgb_cycles']
        commands={n:dict(control=base['physical']['pin_commands'][n],candidate=mode['physical']['pin_commands'][n],delta=mode['physical']['pin_commands'][n]-base['physical']['pin_commands'][n]) for n in ('activate','precharge','refresh','write','read','mode_register')}
        assert commands['write']['delta']==commands['read']['delta']==0
        row=dict(seed=mode['seed'],t_ac_ns=mode['t_ac_ns'],guard_mode=mode['guard_mode'],control_pair_cycles=original_pair,candidate_pair_cycles=new_pair,pair_reduction_percent=(original_pair-new_pair)*100/original_pair,
            control_delta_decode_cycles=base['frames'][1]['decode_cycles'],candidate_delta_decode_cycles=mode['frames'][1]['decode_cycles'],
            control_key_RGB_cycles=base['frames'][0]['rgb_cycles'],candidate_key_RGB_cycles=mode['frames'][0]['rgb_cycles'],
            display_eligible_offer_wait_max_cycles=policy['display_eligible_wait_max_cycles'],pin_commands=commands)
        (guards if mode['guard_mode'] else comparisons).append(row)
        for f in mode['frames']:frames.append(dict(seed=mode['seed'],t_ac_ns=mode['t_ac_ns'],guard_mode=mode['guard_mode'],**f))
        actual=next(m for m in reports[1][1]['modes'] if (m['seed'],m['t_ac_ns'],m['guard_mode'])==(mode['seed'],mode['t_ac_ns'],mode['guard_mode']))
        for f,r in zip(mode['frames'],actual['frames']):assert all(f[k]==v for k,v in r.items()),f['id']
    assert len(comparisons)==4 and len(guards)==1
    ranges={n:[min(m[n] for m in comparisons),max(m[n] for m in comparisons)] for n in ('control_pair_cycles','candidate_pair_cycles','pair_reduction_percent','control_delta_decode_cycles','candidate_delta_decode_cycles','control_key_RGB_cycles','candidate_key_RGB_cycles','display_eligible_offer_wait_max_cycles')}
    changes=[m['candidate_pair_cycles']<m['control_pair_cycles'] and m['candidate_delta_decode_cycles']<m['control_delta_decode_cycles'] for m in comparisons]
    decision='Measured experimental improvement to pair/decode; retain display-latency and read-credit-weighting tradeoff.' if all(changes) else 'Tradeoff/inconclusive candidate; preserve prior control and use individual paired measurements.'
    summary=dict(schema='cu66-v91l-bounded-tile-grant-summary-v1',status='PASS_BOUNDED_REFERENCE_TILE_GRANTS',plan_version='V91l partial; V91m not promoted',reports=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p,r in reports],
        control_summary=dict(path=str(baseline.relative_to(ROOT)),sha256=sha(baseline)),assumed_source_clock_ns=10,seeds=[912901,912902],modeled_memory_t_ac_ns=[2,7],
        natural_comparisons=comparisons,directed_guard_comparisons=guards,natural_ranges=ranges,frames=frames,recommendation=decision,
        integrity={n:sha(AREA/n) for n in ('audit.json','verify_results.py','grant_trace.py','grant_model.py','model-results.json','model-contract.md','reviewed-source-hashes.json','verify_generation.py','generation-audit.json','verify_streams.py','stream-audit.json','packaging-check.json')},
        exact_native_RGB_outputs=10,distinct_native_source_images=2,rtl_SHA_jobs_checked=10250,directed_checks=2056,checker_corruptions_rejected=18,grant_credit_limit=4,idle_gap_limit_cycles=8,
        no_added_payload_buffer=True,codec_bytes_or_quality_changed=False,native_CPP_identical_except_top_type=True,
        fairness_scope='At most four completed reference chunks per grant; wall-clock wait assumes lower service and held responses eventually progress. Up to4:1 reference/display read credits change weighting as well as locality.',
        display_wait_scope='New observed eligible-offer to request-accept clock count; no same-instrument baseline maximum is available; not full pixel/frame latency.',
        source_resolution=[720,480],hardware_cadence_proven=False,complete_validated_decode_under10ms_proven=False,full_RTL_HUD=False,actual_ESP32_transport_qualified=False,
        next='Compare weighted service separately from locality (for example equal-byte/quantum scheduling), then choose a bounded policy; preserve exact bytes, leases and fixed-cadence/full-HUD/ESP32/Series7 hardware gates.')
    (AREA/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    def ms(x):return f'{x[0]/100000:.5f}–{x[1]/100000:.5f}'
    lines=['# Bounded reference-tile grant results','','All times use actual counters converted at an assumed 100 MHz. The control and candidate use the same C++ workload, seeds, memory corners, original native images and output readiness rules. These are simulation measurements.','',
        '| Natural workload metric | Per-line control | Four-line reference grant |','|---|---:|---:|',
        f'| Key start → final delta RGB close | {ms(ranges["control_pair_cycles"])} ms | {ms(ranges["candidate_pair_cycles"])} ms |',
        f'| Delta start → validated commit | {ms(ranges["control_delta_decode_cycles"])} ms | {ms(ranges["candidate_delta_decode_cycles"])} ms |',
        f'| Key RGB start → consumer lease closure | {ms(ranges["control_key_RGB_cycles"])} ms | {ms(ranges["candidate_key_RGB_cycles"])} ms |','',
        f'Paired completion-interval change: {ranges["pair_reduction_percent"][0]:.3f}–{ranges["pair_reduction_percent"][1]:.3f}% lower. Recommendation: {decision}','',
        'The grant limit changes both locality and read-credit weighting (up to four reference lines per display line under continuous contention). It is not an isolated attribution of timing to row activation. The separate directed guard is excluded from performance comparisons.','',
        '| Pin command, seed 912901/tAC 2 | Control | Candidate |','|---|---:|---:|']
    for n in ('activate','precharge','refresh','write','read'):
        p=comparisons[0]['pin_commands'][n];lines.append(f'| {n} | {p["control"]:,} | {p["candidate"]:,} |')
    lines += ['',f'New eligible display-offer maximum: {ranges["display_eligible_offer_wait_max_cycles"][0]}–{ranges["display_eligible_offer_wait_max_cycles"][1]} clocks. This measures request acceptance only, with no same-instrument control maximum. Held responses or downstream backpressure can extend wall-clock wait; the fairness guarantee is bounded reference credit under eventual progress.','',
        '2,056 directed check entries and 18 causal policy-corruption rejections pass. REF_LINES=1 ordinary outputs match the frozen mux cycle by cycle. Five native modes preserve ten complete RGB outputs (two distinct source images) and all 10,250 RTL SHA jobs, canonical/HUD commitments, physical SDRAM data, accepted quantizer history, immutable display leases and publication. Each delta still uses 7,806 reference tiles /31,224 BL8 reads; no payload buffering or codec syntax/quality changes were introduced.','',
        'Unit memory is an explicit behavioral responder. Actual controller/timed pins are covered by native tAC 2/7 runs. Cancel/immediate-mismatch stimulus is source-reviewed in the directed bench; raw yield records alone do not independently reconstruct every unaccepted input. Full RTL HUD, mixed entropy/fallback, actual ESP32/transport timing, fixed-cadence V91m and Series7 mapping/physical/hardware qualification remain open. Hardware 30 fps and complete validated decoding strictly below 10 ms are not proven.','']
    (ROOT/'docs/cu66-v91l-tile-grant/results.md').write_text('\n'.join(lines))
    dirs=[AREA,ROOT/'fpga/experiments/cu66-v91l-tile-grant',ROOT/'fpga/experiments/cu66-v91l-tile-grant-live',ROOT/'scripts/cu66-v91l-tile-grant',ROOT/'scripts/cu66-v91l-tile-grant-live',Path(__file__).resolve().parent,ROOT/'docs/cu66-v91l-tile-grant']
    files=[p for d in dirs for p in d.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='bundle-manifest.json'];files.extend(ROOT/n for n in SHARED)
    assert len(files)==len(set(files)) and all(p.stat().st_size<95*1024*1024 for p in files)
    (AREA/'bundle-manifest.json').write_text(json.dumps(dict(schema='cu66-v91l-bounded-tile-grant-bundle-v1',files={str(p.relative_to(ROOT)):sha(p) for p in sorted(files)}),indent=2)+'\n')
    print(json.dumps(dict(status=summary['status'],files=len(files),natural_ranges=ranges,recommendation=decision)))
if __name__=='__main__':main()
