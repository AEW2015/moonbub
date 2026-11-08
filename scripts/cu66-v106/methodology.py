#!/usr/bin/env python3
"""Record resolved scope and open methodology obligations without waivers."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v106'
DOCS = ROOT / 'docs/cu66-v106'
BUILD_ROOT = Path('/home/lori/gamebub-build/cu66-v69')


def pin(path):
    return dict(path=str(path.relative_to(ROOT)),
                sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def internal_target(attempt):
    """Summarize the fixed 10 ns target from actual completed route evidence."""
    value = attempt.get('stages', {}).get('route', {})
    timing = value.get('timing', {})
    complete = bool(attempt.get('component_route_finished'))
    margins = ('WNS_ns', 'WHS_ns', 'WPWS_ns')
    failing = ('setup_failing', 'hold_failing', 'pulse_failing')
    checks = value.get('check_timing', {})
    reports_present = all(key in timing for key in margins + failing)
    timing_met = reports_present and all(timing[key] >= 0 for key in margins) and all(timing[key] == 0 for key in failing)
    internal_paths_qualified = all(checks.get(key) == 0 for key in ('no_clock', 'unconstrained_internal_endpoints', 'loops'))
    routing_legal = attempt.get('routing_legality', {}).get('reported_zero_errors_and_complete') is True
    capacity = value.get('capacity', {})
    resource_fit = bool(capacity) and all(row['used'] <= row['available'] for row in capacity.values())
    met = complete and timing_met and internal_paths_qualified and routing_legal and resource_fit
    return dict(variant=attempt['variant'], target_period_ns=10.0, target_clock_MHz=100,
                stage='route' if complete else 'no completed route',
                WNS_ns=timing.get('WNS_ns'), WHS_ns=timing.get('WHS_ns'), WPWS_ns=timing.get('WPWS_ns'),
                setup_failing=timing.get('setup_failing'), hold_failing=timing.get('hold_failing'),
                pulse_failing=timing.get('pulse_failing'), routing_legal=routing_legal,
                resource_fit=resource_fit,
                internal_paths_qualified=internal_paths_qualified,
                status='INTERNAL_TARGET_MET' if met else 'INTERNAL_TARGET_OPEN')


def report(attempts, audit):
    results = [internal_target(attempt) for attempt in attempts]
    routed = [row for row in results if row['stage'] == 'route']
    closure = max(routed, key=lambda row: (row['status'] == 'INTERNAL_TARGET_MET', row['WNS_ns'])) if routed else None
    if closure is None or closure['stage'] != 'route':
        current = 'No candidate has a completed routed result in this audited selection. Synthesis/placement estimates do not establish the 100 MHz internal target.'
    else:
        verdict = 'MET in this routed OOC component' if closure['status'] == 'INTERNAL_TARGET_MET' else 'OPEN'
        current = (f"Best measured internal-target candidate `{closure['variant']}` routed WNS is {closure['WNS_ns']:+.3f} ns at the unchanged 10 ns (100 MHz) target; "
                   f"the internal setup/hold/pulse/routing target is **{verdict}**. "
                   f"WHS {closure['WHS_ns']:+.3f} ns, WPWS {closure['WPWS_ns']:+.3f} ns; "
                   f"failing setup/hold/pulse endpoints: {closure['setup_failing']}/{closure['hold_failing']}/{closure['pulse_failing']}. "
                   'This is a target-period result, not an achieved-Fmax or board-throughput claim.')
    names = ', '.join('`' + attempt['variant'] + '`' for attempt in attempts)
    lines = ['# V106 methodology resolution report', '',
        '**Status: actual component evidence measured; methodology/board signoff OPEN.**', '', current, '',
        'Audited native variants in this report: ' + names + '. The names above are derived from actual audited native receipts; deferred candidates must not be presented as additional native measurements.', '',
        'Constraint source: `component.xdc`, line 4. The command is `create_clock -name component_clk -period 10.000 [get_ports clk]`: clock component_clk, period 10 ns, target input port clk. It is loaded before synthesis. Default implementation directives and two tool threads are retained. No relaxed comparison clock, exception, waiver, I/O delay or parent clock-source location was fabricated to clear findings.', '',
        '| Variant | Stage | WNS ns | No clock | Unconstrained internal endpoints | Missing input delays | Missing output delays |',
        '| --- | --- | ---: | ---: | ---: | ---: | ---: |']
    for attempt in attempts:
        for stage in ('synth', 'place', 'route'):
            if stage not in attempt.get('stages', {}):
                continue
            value = attempt['stages'][stage]
            checks = value['check_timing']
            label = {'synth': 'synthesis estimate', 'place': 'placed estimate', 'route': 'routed'}[stage]
            lines.append(f"| {attempt['variant']} | {label} | {value['timing']['WNS_ns']:+.3f} | {checks['no_clock']} | {checks['unconstrained_internal_endpoints']} | {checks['no_input_delay']} | {checks['no_output_delay']} |")
    lines += ['', 'The endpoint numbers above come from check_timing. Methodology rule counts below are tool-reported summary counts; per-rule enumeration limits have not been qualified. Nonnegative setup slack alone does not establish hold/pulse checks, routing completeness or the external boundary contract.', '',
        '| Variant | Stage | Report | Rule | Severity | Reported count |',
        '| --- | --- | --- | --- | --- | ---: |']
    for attempt in attempts:
        for stage in ('synth', 'place', 'route'):
            if stage not in attempt.get('stages', {}):
                continue
            value = attempt['stages'][stage]
            for kind in ('methodology_reported', 'DRC_reported'):
                for rule, finding in sorted(value[kind]['by_rule'].items()):
                    lines.append(f"| {attempt['variant']} | {stage} | {kind} | {rule} | {finding['severity']} | {finding['reported']} |")
    lines += ['', '## V106 targeted changes and measured follow-up', '',
        '- **Coefficient position/validation and storage:** the exact LUT tile-to-cell helpers replace the repeated constant-arithmetic validation evaluation; static bank/word coefficient storage targets the prior distributed-memory write-enable locality. Original invalid-metadata/error priorities and same-edge write ordering remain in the proof contract. Static source shape is not a primitive-mapping or timing verdict; inspect the native inventories, control sets, fanout and worst path for each actual variant.',
        '- **Scratch allocation:** the full32 carry-save PLAN change calculates each aligned allocation prefix independently. Its modulo-2^32 identities preserve overflow, stale-epoch priority, size/count guards and same-cycle owner initialization. The source edit does not authorize narrower addresses, removed validation or an extra allocation cycle.',
        '- **Sparse context position:** exact byte quotient/remainder tables, the combined correction/ZIGZAG table and parallel quotient correction selection target the routed position-to-block/index division cone. The proof covers the full32 position identity and fixed byte tables, including initial all-ones and invalid positions. The small correction bound follows from the table remainders; no unrestricted claim is made for unreachable standalone correction-table addresses.',
        '- **Rice parser remaining bits:** full32 remaining/load-remaining caches target the measured size-to-output control cone. Reset/start initialization and every existing guarded load/PREFIX/SUFFIX update preserve the original modular subtraction identities. This is redundant state with a clocked invariant and unchanged parser cycles, not a stream-size assumption or a removed bound check.',
        '- **Prefix and telemetry follow-up:** balanced first-one rank plus late window clamping replaces the serial scan without changing parser cycles. Static per-word 64-bit telemetry increments retain all public counters, wrap behavior, pre-edge sampling and reset/start/abort priority. Their focused probes and final paired lanes qualify behavior; native results decide whether the actual timing cones improve.',
        '- **Guard-specific suffix, actual IDCT operands and producer cache:** the guarded-suffix-idct-cache trial specializes suffix extraction independently of PREFIX work, prefetches signed IDCT operands within existing MUL/ACC slots, and mirrors every producer plane/tile assignment in a private quant-cell cache. Selected-state substitution, live operand/cache invariants and full paired public behavior are distinct evidence scopes. Read actual mapped DSP registers and routed paths; the producer transition model alone is not whole-controller RTL proof.',
        '- **TIMING-16 / setup and internal target:** the best measured routed result above is read dynamically from the selected native audit. If negative slack or any required setup/hold/pulse/routing check remains, read that actual final worst path and continue measured architectural/locality work. A cone removed from an earlier variant can expose another bottleneck; earlier path names do not identify the final selected limiter.',
        '- **TIMING-18 / parent boundaries and CDC:** missing external input/output delays, parent clocks, interface timing and boundary locations remain system-integration obligations. OOC reports and a positive internal target result do not establish those contracts. Inspect the actual CDC/check_timing scope; paths omitted for absent boundary clock/delay definitions are not validated crossings.',
        '- **SYNTH-6 / RAM pipeline advisory:** native RAM ledgers describe the actual optional primitive registers. The existing registered logical lookups and packet read-first semantics stay in force. An additional RAM output register requires an explicit latency/ownership contract and replay; it is not an attribute-only fix. Verify actual coefficient-storage FF/LUTRAM mapping rather than assuming it from static-word source.',
        '- **RTGT-1 / RAM retargeting advisory:** retain reported opportunities separately from measured primitive mapping. New banking/port/collision changes require behavioral proofs and matched native measurements.',
        '- **DPIP/DPOP / DSP advisories:** report actual AREG/BREG/MREG/PREG settings per primitive and variant. All measured variants retain the original dequantizer. The routed products_reg DSP-input path belongs to cu66_idct8x8 operand selection, not cu66_dequant; V104 dequantizer prefetch is not a direct fix for it. Coordinate tables, carry-save prefix logic and storage changes do not qualify every DSP path or establish a system clock gain.',
        '- **CFGBVS/configuration and OOC route/clock-source findings:** actual parent/board configuration and boundary contracts remain integration obligations. No board configuration value or HD.CLK_SRC/HD.PARTPIN_LOCS was guessed.', '',
        'The scope is exact same-cycle architectural RTL changes with bounded behavioral evidence and actual component native measurements. No finding was waived, downgraded or hidden by a timing cut. The 100 MHz internal target result is separate from methodology/DRC/CDC/boundary signoff, achieved-Fmax, sustained board 30 fps and complete validated under-10-ms decoding.', '',
        f"Native evidence audit: `{audit['path']}`, SHA-256 `{audit['sha256']}`.",
        'It pins source/constraint/recipe snapshots, retained reports and terminal outcomes. PASS_EVIDENCE authenticates evidence, including failed outcomes; it does not clear the findings above.', '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-external', action='store_true',
                        help='Also write the report in each actual design/build working directory.')
    args = parser.parse_args()
    path = AREA / 'native-audit.json'
    native = json.loads(path.read_text())
    assert native['status'] == 'PASS_EVIDENCE'
    audit = pin(path)
    attempts = [native['measured_variants'][name] for name in sorted(native['measured_variants'])]
    dest = DOCS / 'METHODOLOGY_RESOLUTION_REPORT.md'
    dest.write_text(report(attempts, audit))
    external = []
    if args.write_external:
        for attempt in attempts:
            receipt = json.loads((ROOT / attempt['path']).read_text())
            work = Path(receipt['build_external']).resolve()
            work.relative_to(BUILD_ROOT)
            assert work.is_dir()
            text = report([attempt], audit)
            # Write a relative report name in the actual design cwd, as required
            # by the methodology workflow. No vendor run or checkpoint is opened.
            subprocess.run([sys.executable, '-c',
                "from pathlib import Path; import sys; Path('METHODOLOGY_RESOLUTION_REPORT.md').write_text(sys.stdin.read())"],
                input=text, text=True, cwd=work, check=True)
            external.append(dict(build_external=str(work),
                report='METHODOLOGY_RESOLUTION_REPORT.md', sha256=hashlib.sha256(text.encode()).hexdigest()))
    result = dict(schema='v106-methodology-resolution-record-v1', status='SIGNOFF_OPEN',
                  native_audit=audit, generator=pin(Path(__file__)), report=pin(dest),
                  external_reports_written=external, internal_timing_targets=[internal_target(attempt) for attempt in attempts],
                  waivers_or_constraint_edits=False,
                  methodology_DRC_CDC_signed_off=False, hardware_qualified=False)
    (AREA / 'methodology-resolution.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print('V106_METHODOLOGY_RECORDED', len(attempts), 'variants', len(external), 'design cwd reports; SIGNOFF_OPEN')


if __name__ == '__main__':
    main()
