#!/usr/bin/env python3
"""Render source-qualified V107 evidence; this never turns a negative WNS into a pass."""
import csv
import hashlib
import io
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v107'
DOCS = ROOT / 'docs/cu66-v107'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True)+'\n')


def main():
    audit_path = AREA/'audit/baseline-audit.json'
    audit = json.loads(audit_path.read_text())
    assert audit['status'] not in ('AUDIT_ERRORS', 'PENDING_REQUIRED_EVIDENCE'), audit['status']
    attempts = audit['native_builds']['attempts']
    rows = []
    for item in attempts:
        if 'route' not in item or not item['route']:
            status=item['status']
            if item['variant'] in ('header','guard'):
                stop_path=AREA/('coordination/'+item['variant']+'-scheduling-cancellation.json')
                if stop_path.is_file():
                    stop=json.loads(stop_path.read_text())
                    assert stop['receipt']==item['path']+'/receipt.json'
                    assert sha(ROOT/stop['receipt'])==stop['terminal_receipt_sha256']
                    assert stop['terminal_observed_exit_code']==143 and not stop['synthesis_checkpoint_written']
                    status='SCHEDULING_CANCELLED_NO_TIMING_RESULT'
            rows.append(dict(variant=item['variant'], status=status, recorded_audit_status=item['status'], receipt=item['path']+'/receipt.json'))
            continue
        route = item['route']
        assert item['artifact_hashes_match'] and all(v for k,v in item['checks'].items() if k!='setup_hold_pulse_all_pass'), item['variant']
        capacity=(ROOT/item['path']/'reports/route-capacity.rpt').read_text()
        utilization={}
        for label in ('Slice LUTs','LUT as Logic','LUT as Memory','Slice Registers','Slice','Unique Control Sets','RAMB36/FIFO*','RAMB18','DSPs'):
            match=re.search(r'^\|\s*'+re.escape(label)+r'\*?\s*\|\s*(\d+)\s*\|',capacity,re.M)
            if match:utilization[label]=int(match[1])
        t = route['summary']
        checks = route['check_timing']
        passed = (min(t['WNS_ns'], t['WHS_ns'], t['WPWS_ns']) >= 0
                  and all(t[k] == 0 for k in ('setup_failing','hold_failing','pulse_failing'))
                  and all(checks[k] == 0 for k in ('no_clock','unconstrained_internal_endpoints','loops','latch_loops'))
                  and route['routing']['all_routable_nets_routed']
                  and route['routing']['zero_routing_errors'])
        rows.append(dict(variant=item['variant'], status=item['status'], receipt=item['path']+'/receipt.json',
            receipt_sha256=item['receipt_sha256'], source_count=item['source_count'],
            timing=t, resources=utilization, routing=route['routing'], worst_setup_path=route['worst_setup_path'],
            component_internal_100MHz_pass=passed, board_IO_signoff=False,
            full_custom_top_qualified=False, hardware_30fps=False,
            complete_validated_decode_under10ms=False))
    completed = [r for r in rows if 'timing' in r]
    assert completed
    best = max(completed, key=lambda r:r['timing']['WNS_ns'])
    receipt = json.loads((ROOT/best['receipt']).read_text())
    inputs_path = ROOT/best['receipt']
    inputs_path = inputs_path.parent/'inputs.json'
    inputs = json.loads(inputs_path.read_text())
    selection = dict(schema='v107-selected-source-qualified-routed-frontier-v1',
        selection_basis='Largest WNS among source-qualified completed fixed-clock native decoder routes; the explicitly labeled runtime probe has a different synthesis directive. Not a target pass or robustness proof.',
        variant=best['variant'], receipt=best['receipt'], receipt_sha256=sha(ROOT/best['receipt']),
        source_overrides=inputs['source_overrides'], baseline_overrides=inputs['baseline_overrides'],
        additional_sources=inputs['additional_sources'], source_origins=inputs['source_origins'],
        source_sha256=inputs['source_sha256'], closure_files=len(inputs['source_sha256']),
        flow_strategy=inputs.get('strategy',dict(synth='Default',opt='Default',place='Default',route='Default')),
        native_recipe={name:dict(path=str((inputs_path.parent/'recipe-snapshot'/name).relative_to(ROOT)),sha256=sha(inputs_path.parent/'recipe-snapshot'/name)) for name in ('run.tcl','report.tcl','component.xdc','inputs.tcl')},
        clock_period_ns=10.0, part='xc7a100tcsg324-1',
        component_internal_100MHz_pass=best['component_internal_100MHz_pass'],
        full_custom_top_qualified=False, hardware_30fps=False, complete_validated_decode_under10ms=False,
        achieved_Fmax_MHz=None, behavioral_boundary='Exact canonical pixels; coefficient-boundary latency is explicitly changed versus V106.')
    write(AREA/'selection.json',selection)
    result=dict(schema='v107-study-summary-v1', audit=dict(path=str(audit_path.relative_to(ROOT)),sha256=sha(audit_path),status=audit['status']),
        native_decoder_trials=rows, selected=selection,
        prior_V106_selected_WNS_ns=-4.034,
        selected_WNS_delta_from_V106_ns=round(best['timing']['WNS_ns']+4.034,3),
        new_cycle_exact_matrix_case_profiles=336,new_cycle_exact_matrix_directed_checks=408,
        elastic_paired_case_profiles=88,elastic_paired_directed_checks=84,
        header_fresh_candidate_case_profiles=44,header_fresh_candidate_directed_checks=42,
        architectural_scope='720x480 CS88 q16/all-BR88, 49152-byte cap, unchanged intended canonical/reference pixels; no new codec/quality/bitrate claim.',
        parent_integration='OPEN: production moonshine_top still instantiates legacy JPEG core, with unimplemented CU66 protocol/reference/memory/display adapters.',
        decoder_100MHz=best['component_internal_100MHz_pass'],sustained_hardware_30fps=False,complete_validated_under10ms=False)
    if (AREA/'tables-pipeline/results.json').is_file():
        tables=json.loads((AREA/'tables-pipeline/results.json').read_text())
        result['tables_fresh_candidate_case_profiles']=tables['newly_executed_candidate_case_profiles']
        result['tables_fresh_candidate_directed_checks']=tables['newly_executed_candidate_directed_checks']
    if (AREA/'payload-pipeline/results.json').is_file():
        payload=json.loads((AREA/'payload-pipeline/results.json').read_text())
        assert payload['status']=='PASS_EXACT_PAYLOAD_CANONICAL'
        result['payload_fresh_candidate_case_profiles']=payload['newly_executed_candidate_case_profiles']
        result['payload_fresh_candidate_directed_checks']=payload['newly_executed_candidate_directed_checks']
        result['isolated_component_payload_reset_pins_grounded']=2307
        result['payload_public_cycle_contract']='Exact versus retained elastic control; only unowned private payload contents may differ.'
    for label,expected_status in [('guard','PASS_EXACT_GUARD_CANONICAL'),('meta','PASS_EXACT_META_CANONICAL'),('threshold','PASS_EXACT_THRESHOLD_CANONICAL')]:
        qpath=AREA/(label+'-pipeline/results.json')
        if qpath.is_file():
            q=json.loads(qpath.read_text());assert q['status']==expected_status
            result[label+'_fresh_candidate_case_profiles']=q['newly_executed_candidate_case_profiles']
            result[label+'_fresh_candidate_directed_checks']=q['newly_executed_candidate_directed_checks']
    write(AREA/'summary.json',result)
    fields=['variant','status','WNS_ns','TNS_ns','setup_failing','WHS_ns','hold_failing','WPWS_ns','pulse_failing','component_internal_100MHz_pass','receipt']
    buf=io.StringIO();writer=csv.DictWriter(buf,fieldnames=fields);writer.writeheader()
    for row in rows:
        writer.writerow({k:row.get('timing',{}).get(k,row.get(k,'')) for k in fields})
    (AREA/'native-comparison.csv').write_text(buf.getvalue())
    lines=['# V107 native decoder comparison','',
        'Fresh variants use Vivado 2026.1 build 6511674, `xc7a100tcsg324-1`, the same **10.000 ns** clock loaded before synthesis and two tool threads. All use Default synthesis/opt/place/route except the explicitly labeled `threshold-runtime` probe, which changes only synthesis to RuntimeOptimized. Its same eighteen RTL/header files and Default placement/routing are hash-bound; different synthesis strategies are not a single-edit RTL-only comparison. The native watchdog is 3,600 seconds versus V106’s 1,800 seconds; runtime is not a matched comparison. No decoder clock relaxation, false path, multicycle exception or invented I/O delay was added.','',
        '| Variant | Routed WNS (ns) | Failing setup endpoints | Hold (ns) | Pulse (ns) | Internal 100 MHz |',
        '| --- | ---: | ---: | ---: | ---: | --- |',
        '| V106 selected closure | −4.034 | 44,630 | +0.122 | +3.750 | FAIL |']
    for row in rows:
        if 'timing' in row:
            t=row['timing'];lines.append(f"| {row['variant']} | {t['WNS_ns']:+.3f} | {t['setup_failing']:,} | {t['WHS_ns']:+.3f} | {t['WPWS_ns']:+.3f} | {'PASS' if row['component_internal_100MHz_pass'] else 'FAIL'} |")
        else:lines.append(f"| {row['variant']} | {row['status']} | — | — | — | OPEN |")
    lines += ['',f"The selected routed frontier is **{best['variant']}**, WNS **{best['timing']['WNS_ns']:+.3f} ns**. A selected negative slack remains a timing failure. A single completed route does not establish reproducibility across clean builds or strategies.",'',
        'The earlier V106 sixth-checkpoint continuation completed routing at −4.428 ns. It reused a read-only synthesis checkpoint and is retained separately from fresh synthesis trials. SCALE-only native routing was deferred after targeted routed probes found mode[0] −2.508 ns and scale[0] −2.587 ns; TABLES combines both repairs instead. No deferred run is counted as measured.',
        'The HEADER-only job was deliberately stopped for scheduling at 1,831.615 seconds (exit143) before any synthesis checkpoint/report; its unchanged3,600-second watchdog was not reached. The retained cancellation record distinguishes this from a tool timeout or measured timing failure. The sixth source trial is motivated by an actual read-only TABLES route probe of a constant×43 DSP control path at−2.497 ns, with its original checkpoint hash unchanged.','',
        'See [summary JSON](../../experiments/python-gamebub-v107/summary.json), [selected source map](../../experiments/python-gamebub-v107/selection.json), [CSV](../../experiments/python-gamebub-v107/native-comparison.csv), and [independent audit](../../experiments/python-gamebub-v107/audit/baseline-audit.json). The native receipts retain complete source snapshots, exact commands, recipes, hashes, logs and reports. Large checkpoints remain at their documented external paths and are not required for portable report auditing.','',
        '## Functional comparison scopes','',
        '- Six cycle-exact fresh/canonical lanes: **336 case-profile runs and 408 directed checks**, including both implementations, seeds, profiles and expected rejects. These are not unique displayed frames.',
        '- The complete coefficient tuple register and done fence use a separate latency-aware canonical comparison: **88 case-profile runs and 84 directed checks**, with exact canonical pixels and ordered semantic streams, explicit accepted/delivered/discarded conservation, ownership, error/cancel checks. Public cycle equality against V106 is not claimed.',
        '- HEADER runs **44 new candidate case-profile runs and 42 directed checks**, requiring exact stdout, cycles, events and canonical bytes versus the retained actual elastic control. The control is reused, not reexecuted or recounted.',
        '- TABLES uses the same fresh-candidate-only comparison and control reuse. Component-level RAM proofs are separate from full decoder timing.',
        '- PAYLOAD separately removes resets/control dependence from 1,027 dequant and 1,280 IDCT private payload bits. It requires another 44/42 fresh candidate-only exact comparison and an actual native route; unit mapping is not full decoder timing.',
        '- CDC experiments use separate tops and clocks. Their positive slack never substitutes for decoder timing or parent-board CDC signoff.','',
        '## Further qualified control experiments', '',
        'META captures two pure geometry/domain flags alongside the existing130-bit coefficient payload, with no added public cycles. Its unit and exact full canonical tests pass, but its completed combined route is slower than the selected PAYLOAD route. It remains unselected. The table above retains that negative result. The additional live count-limit path requires another measured control cut.', '',
        'The four-file header prefix/count-threshold unit passes31,856,723 paired controller edges across both SYNC modes/two seeds. The combined complete pixel decoder additionally passes44 fresh candidate case-profile runs and42 directed checks, requiring exact canonical pixels, events and cycles against the retained actual elastic control. Source-bound native routing is listed above; neither model-only preparation nor the isolated extracted pipeline synthesis margin substitutes for that result. See [count thresholds](count-threshold.md) and [actual extracted mapping](count-threshold-native.md).', '',
        'The single bounded post-route physical optimization diagnostic crashed in Vivado (exit139) and produced no completed timing result or candidate checkpoint. Its intermediate slack is excluded from selection. Parent checkpoints/sources stayed unchanged; the [failure evidence](postroute-probe.md) is audited separately. No retry or extra strategy sweep was launched.', '',
        '## Selected closure','',
        'Apply the selected manifest’s baseline/source overrides to the frozen V100 source list, then append its additional coefficient-stage source. Compile exactly one implementation of each module. Reproduce both the selected flow_strategy and pinned native recipes alongside the RTL source map. Standalone verification adapters are not production inputs. The native source closure includes the embedded admission helpers; strict Verilator compilation may split the exact same bytes into correctly named helper files. See per-run packaging manifests.','',
        'This is component OOC evidence. Board I/O, reset recovery/removal, real CDC integration, transport service, full custom top fit, sustained hardware 30 fps and complete validated decoding below 10 ms remain open. No achieved Fmax is inferred from one WNS result.']
    lines += ['', '## Routed resources', '',
        '| Variant | LUTs | LUTRAM | FFs | Slices | Control sets | RAMB36 | RAMB18 | DSPs |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for row in completed:
        u=row['resources']
        values=[u.get(k,'unavailable') for k in ('Slice LUTs','LUT as Memory','Slice Registers','Slice','Unique Control Sets','RAMB36/FIFO*','RAMB18','DSPs')]
        lines.append('| '+row['variant']+' | '+' | '.join(str(v) for v in values)+' |')
    lines += ['', 'These are component routed resources, not complete board-fit evidence. Slice occupancy and control-set packing can be much tighter than LUT utilization alone suggests.']
    (DOCS/'vendor-comparison.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(dict(selected=best['variant'],WNS_ns=best['timing']['WNS_ns'],component_internal_100MHz_pass=best['component_internal_100MHz_pass'],audit=audit['status'])))


if __name__=='__main__':
    main()
