#!/usr/bin/env python3
"""Bind physically priced scratch, native correctness and retained control."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'experiments/python-gamebub-v91l-scratch-service'
SHARED=['docs/gamebub-application-specific-codec-plan.md','docs/gamebub-v91-v110-development-plan.md','docs/literature-review-2026-11-06/README.md']
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
    audit=read(AREA/'audit.json');assert audit['status']=='PASS_INDEPENDENT_PHYSICAL_SCRATCH_LIVE_VALIDATION_AND_NATIVE_RGB'
    assert audit['verifier_sha256']==sha(AREA/'verify_results.py') and audit['scratch_trace_sha256']==sha(AREA/'scratch_trace.py')
    for name,digest in {**audit['reviewed_source_sha256'],**audit['inherited_checker_sha256'],**audit['original_helper_sha256']}.items():assert sha(ROOT/name)==digest,name
    reports=[]
    for kind,alias in [('unit','fpga/experiments/cu66-v91l-scratch-service/results.json'),('live','fpga/experiments/cu66-v91l-scratch-live/results.json')]:
        path=ROOT/audit[kind+'_report'];report=read(path);assert sha(path)==audit[kind+'_report_sha256']
        assert read(ROOT/alias)==dict(report,selected_report=str(path.relative_to(ROOT)))
        fresh(path,report);reports.append((path,report))
    assert len(audit['unit_modes'])==2 and len(audit['live_modes'])==4
    assert len(audit['checker_negative_controls'])==54 and all(n['rejected'] for n in audit['checker_negative_controls'])
    assert audit['exact_native_RGB_outputs']==8 and audit['rtl_sha_jobs']==8200
    assert {(m['seed'],m['t_ac_ns']) for m in audit['live_modes']}=={(s,t) for s in (912901,912902) for t in (2,7)}
    assert all(m['checks']>=811 for m in audit['unit_modes'])
    subprocess.run(['python3',str(AREA/'scratch_model.py'),'--check'],cwd=ROOT,check=True)
    model=read(AREA/'model-results.json');assert model['status']=='PASS'
    generation=read(AREA/'generation-audit.json');assert generation['status']=='PASS_CAPTURE_ONLY_BYTE_IDENTICAL_GENERATION'
    assert generation['verifier_sha256']==sha(AREA/'verify_generation.py')
    for name,digest in {**generation['source_sha256'],**generation['outputs_sha256']}.items():assert sha(ROOT/name)==digest,name
    packaging=read(AREA/'packaging-check.json')
    assert packaging['status']=='PASS_EXACT_RAW_ARTIFACT_WHITESPACE_EXCEPTIONS' and not packaging['compiler_warning_waivers']
    for entry in packaging['exceptions']:assert sha(ROOT/entry['path'])==entry['sha256'],entry['path']
    baseline=ROOT/'experiments/python-gamebub-v91l-reference-reader/summary.json';control=read(baseline)
    assert control['status']=='PASS_PHYSICAL_REFERENCE_LIVE_VALIDATION_AND_NATIVE_RGB'
    samples=[];comparisons=[];live=reports[1][1]
    for mode in audit['live_modes']:
        assert mode['physical']['video_write_words']==560640 and mode['physical']['video_captured_words']==768192
        assert mode['physical']['require_prior_pin_write_for_every_native_read']
        assert mode['reference']['tile_requests']==mode['reference']['tile_responses']==7806
        assert mode['reference']['physical_BL8_reads']==31224 and mode['presented_fids']==[0,1]
        runner=next(m for m in live['modes'] if (m['seed'],m['t_ac_ns'])==(mode['seed'],mode['t_ac_ns']))
        for frame,actual in zip(runner['frames'],mode['frames']):
            assert all(actual[k]==v for k,v in frame.items()),frame['id']
            stats=mode['physical']['scratch_by_native_id'][actual['id']]
            assert stats['requests']==stats['responses']==stats['write_requests']+stats['read_requests'] and not stats['errors']
            sample=dict(seed=mode['seed'],t_ac_ns=mode['t_ac_ns'],scratch=stats,**actual);samples.append(sample)
            old=next(f for f in control['frames'] if (f['seed'],f['t_ac_ns'],f['fid'])==(mode['seed'],mode['t_ac_ns'],frame['fid']))
            comparisons.append(dict(seed=mode['seed'],t_ac_ns=mode['t_ac_ns'],fid=frame['fid'],control_live_cycles=old['live_cycles'],physical_scratch_live_cycles=actual['live_cycles'],control_serial_cycles=old['joint_serial_cycles'],physical_scratch_serial_cycles=actual['joint_serial_cycles']))
    ranges={}
    for fid in (0,1):
        selected=[f for f in samples if f['fid']==fid]
        ranges[str(fid)]={n:[min(f[n] for f in selected),max(f[n] for f in selected)] for n in ('live_cycles','rgb_cycles','joint_serial_cycles','packet_complete_to_commit_cycles')}
    assert all(f['joint_serial_cycles']*30>100000000 and f['live_cycles']>=1000000 for f in samples)
    summary=dict(schema='cu66-v91l-physical-scratch-summary-v1',status='PASS_PHYSICAL_SCRATCH_LIVE_VALIDATION_AND_NATIVE_RGB',
        plan_version='V91l partial; V91m not promoted',reports=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p,r in reports],
        control_summary=dict(path=str(baseline.relative_to(ROOT)),sha256=sha(baseline)),
        integrity={n:sha(AREA/n) for n in ('audit.json','verify_results.py','scratch_trace.py','scratch_model.py','model-results.json','model-contract.md','reviewed-source-hashes.json','verify_generation.py','generation-audit.json','audit-review.md','packaging-check.json')},
        frames=samples,cycle_ranges_by_fid=ranges,paired_control_comparisons=comparisons,assumed_source_clock_ns=10,modeled_memory_t_ac_ns=[2,7],seeds=[912901,912902],
        exact_native_base_RGB_outputs=8,distinct_native_source_images=2,rtl_SHA_jobs_checked=8200,
        directed_checks_total=sum(m['checks'] for m in audit['unit_modes']),checker_corruptions_rejected=len(audit['checker_negative_controls']),
        physical_scratch_service_qualified=True,all_external_memory_endpoints_rtl=True,shared_single_controller=True,
        no_canonical_or_pixel_SDRAM_preload=True,native_software_memory_responder=False,
        scratch_aperture=dict(bank=3,bytes=262144,address_bits=18,line_bytes=16,x16_write_commands_per_line=8,BL8_read_commands_per_line=1),
        serial_live_commit_then_RGB=True,native_overlap_qualified=False,full_RTL_HUD_decoder_overlay=False,
        common_all_client_service_complete=False,serial_nominal_30Hz_budget_met=False,achieved_clock_or_routed_timing=False,
        sustained_hardware_30fps_proven=False,complete_validated_decode_under10ms_proven=False,
        next='Qualify native bank-safe decode/display overlap and contention against this all-memory-clients serial control; close HUD, profile/source-cadence and actual ESP32/7-series hardware gates.')
    (AREA/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    lines=['# Physical scratch measured results','','All times below are cycle counters converted at an assumed 100 MHz; no hardware clock or complete-system latency claim.','',
        '| Source | Start → commit (ms) | Packet complete → commit (ms) | RGB stage (ms) | Serial start → RGB close (ms) |','|---|---:|---:|---:|---:|']
    def span(pair):return f'{pair[0]/100000:.5f}–{pair[1]/100000:.5f}'
    for fid in (0,1):
        row=ranges[str(fid)];lines.append('| '+('Key' if fid==0 else 'Delta')+' | '+' | '.join(span(row[k]) for k in ('live_cycles','packet_complete_to_commit_cycles','rgb_cycles','joint_serial_cycles'))+' |')
    lines += ['','| Source | Scratch WRITE lines | Scratch READ lines | WRITE x16 words | READ x16 words | Highest line start |','|---|---:|---:|---:|---:|---:|']
    for fid in (0,1):
        stats=[s['scratch'] for s in samples if s['fid']==fid]
        assert all(all(s[k]==stats[0][k] for k in ('write_requests','read_requests','max_address')) for s in stats)
        s=stats[0];lines.append(f'| {"Key" if fid==0 else "Delta"} | {s["write_requests"]:,} | {s["read_requests"]:,} | {8*s["write_requests"]:,} | {8*s["read_requests"]:,} | {s["max_address"]:,} |')
    lines += ['',f'{summary["directed_checks_total"]:,} directed check entries, 54 independently rejected corruptions, eight exact full base-RGB outputs and 8,200 actual RTL SHA jobs pass. This is two distinct native source images under two seeds and two memory-delay corners.',
        '', 'The prior control used a finite C++ scratch responder. The new result prices scratch traffic plus the added outer transaction arbiter; it is not a codec speedup comparison. Contention with the native display is still tested only in directed controls; native decode and RGB remain serial. Hardware 30 fps and complete validated decode below 10 ms remain open.','']
    (ROOT/'docs/cu66-v91l-scratch-service/results.md').write_text('\n'.join(lines))
    directories=[AREA,ROOT/'fpga/experiments/cu66-v91l-scratch-service',ROOT/'fpga/experiments/cu66-v91l-scratch-live',ROOT/'scripts/cu66-v91l-scratch-service',ROOT/'scripts/cu66-v91l-scratch-live',Path(__file__).resolve().parent,ROOT/'docs/cu66-v91l-scratch-service']
    files=[p for directory in directories for p in directory.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='bundle-manifest.json']
    files.extend(ROOT/n for n in SHARED)
    assert len(files)==len(set(files)) and all(p.stat().st_size<95*1024*1024 for p in files),'duplicate or oversized bundle artifact'
    (AREA/'bundle-manifest.json').write_text(json.dumps(dict(schema='cu66-v91l-physical-scratch-bundle-v1',files={str(p.relative_to(ROOT)):sha(p) for p in sorted(files)}),indent=2)+'\n')
    print(json.dumps(dict(status=summary['status'],files=len(files),ranges=ranges)))
if __name__=='__main__':main()
