#!/usr/bin/env python3
"""Source-pinned 1/2/4-lane resource and bottleneck bounds; no RTL or FPS prediction."""
import csv
import hashlib
import json
import re
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v113/lanes'
NATIVE = ROOT / 'experiments/python-gamebub-v112/native/20261108T195810929250Z'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def table_rows(path):
    return [[v.strip() for v in line.split('|')[1:-1]]
            for line in path.read_text().splitlines() if line.startswith('|')]

def ratio(n, d):
    q = Fraction(n, d)
    return {'numerator': q.numerator, 'denominator': q.denominator, 'decimal': float(q)}

def main():
    AREA.mkdir(parents=True, exist_ok=True)
    paths = [NATIVE / x for x in ('inputs.json', 'reports/route-utilization.rpt',
                                  'reports/route-capacity.rpt', 'reports/route-ram-config.tsv')]
    selected = ROOT / 'experiments/python-gamebub-v113/inverse/benchmark-selected.json'
    selection = json.loads(selected.read_text())
    bench_path = ROOT / selection['path']
    assert selection['status'] == 'PASS' and sha(bench_path) == selection['sha256']
    bench = json.loads(bench_path.read_text())
    assert bench['status'] == 'PASS' and bench['backend'] == 'Verilator'
    paths += [selected, bench_path, Path(__file__).resolve(), ROOT / 'fpga/rtl/moonshine_top.sv']
    for name, digest in bench['sources'].items():
        p = ROOT / name
        assert sha(p) == digest, name
        paths.append(p)
    inputs = json.loads(paths[0].read_text())
    origins = inputs['source_contract']['source_origins']
    logical = ['fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv',
               'fpga/experiments/cu66-v91h/br88_packet_ingress_sync_v91h.sv',
               'fpga/experiments/cu66-v91g2/packed_scratch_v91g2.sv',
               'fpga/experiments/cu66-v91k/cs88_pipeline_v91k.sv',
               'fpga/experiments/cu66-v91k/cu66_reconstruct_stream_v91k.sv']
    actual = {}
    for name in logical:
        origin = origins[name]
        p = ROOT / origin['path']
        assert sha(p) == origin['sha256']
        actual[name] = p
        paths.append(p)
    hierarchy = {r[0]: {'luts': int(r[2]), 'ffs': int(r[6]), 'ramb36': int(r[7]),
                         'ramb18': int(r[8]), 'dsp': int(r[9])}
                 for r in table_rows(NATIVE / 'reports/route-utilization.rpt')
                 if len(r) == 10 and r[2].isdigit()}
    capacity_rows = table_rows(NATIVE / 'reports/route-capacity.rpt')
    capacity = {}
    for label in ('DSPs', 'Slice LUTs', 'Slice Registers', 'Block RAM Tile', 'Slice'):
        r = next(r for r in capacity_rows if r and r[0] == label)
        capacity[label] = {'used': int(r[1]), 'available': int(r[4])}
    assert capacity['DSPs'] == {'used': 42, 'available': 240}
    assert hierarchy['coefficients']['dsp'] == 17
    assert hierarchy['(synchronous.ingress)']['dsp'] == 16 and hierarchy['context_decoder']['dsp'] == 1
    dq = hierarchy['dequant']['dsp']; idct = hierarchy['inverse']['dsp']
    shared = hierarchy['coefficients']['dsp']; lane_dsp = dq + idct
    assert (shared, dq, idct, lane_dsp) == (17, 8, 17, 25)
    assert shared + lane_dsp == hierarchy['cs88_pipeline_v91k']['dsp']
    assert hierarchy['transform']['ramb36'] == hierarchy['transform']['ramb18'] == 0
    with (NATIVE / 'reports/route-ram-config.tsv').open() as f:
        ram = list(csv.DictReader(f, delimiter='\t'))
    assert len(ram) == 36 and all(r['RAM_MODE'] == 'TDP' for r in ram)
    ram_groups = {}
    for r in ram:
        instance = r['instance']
        group = ('admission_packet' if instance.startswith('coefficients/admission/memory_reg') else
                 'ingress_packet' if '/memory_reg' in instance else
                 'mode_metadata' if '/mode_store/' in instance else
                 'scale_metadata' if '/scale_store/' in instance else 'context_geometry')
        key = (group, r['REF_NAME'], r['READ_WIDTH_A'], r['READ_WIDTH_B'],
               r['WRITE_WIDTH_A'], r['WRITE_WIDTH_B'], r['DOA_REG'], r['DOB_REG'])
        ram_groups[key] = ram_groups.get(key, 0) + 1
    assert ram_groups[('admission_packet', 'RAMB36E1', '1', '1', '1', '1', '0', '0')] == 16
    assert ram_groups[('ingress_packet', 'RAMB36E1', '1', '1', '1', '1', '0', '0')] == 16
    assert sum(v for k, v in ram_groups.items() if k[0] == 'context_geometry') == 2
    admission = actual[logical[0]].read_text(); scratch = actual[logical[2]].read_text()
    pipeline = actual[logical[3]].read_text(); reconstruct = actual[logical[4]].read_text()
    inverse_path = ROOT / 'fpga/experiments/cu66-v113-inverse/cu66_inverse_stream_v91j.sv'
    inverse = inverse_path.read_text(); top = (ROOT / 'fpga/rtl/moonshine_top.sv').read_text()
    assert "assign memory_read_enable=stage_read_req || (replay_req && replay_ready);" in admission
    assert "assign memory_read_address=stage_read_req ? fetch_addr[15:0] : replay_addr[15:0];" in admission
    assert 'wire scale_lookup=scale_live&&lookup_req&&state==FINISHED;' in admission
    assert 'logic outstanding=0' in scratch and '!outstanding' in scratch
    assert 'output logic [127:0] mem_req_data' in pipeline
    assert 'input logic [511:0] ref_rsp_pixels' in pipeline
    assert 'assign ref_rsp_ready=ref_pending;' in reconstruct
    assert 'inout wire[15:0]sdram_dq' in top
    assert 'A_EMPTY=0,A_VALIDATE=1,A_COMMIT=2' in inverse
    assert '(accept_state==A_EMPTY||accept_state==A_COMMIT)' in inverse
    assert 'logic [1535:0] result_payload [0:1];' in inverse
    assert 'identity_t accepted_meta, expected_meta, result_meta [0:1];' in inverse
    identity = inverse[inverse.index('    typedef struct packed {'):inverse.index('    } identity_t;')]
    widths = []
    for width, names in re.findall(r'logic \[(\d+):0\] ([^;]+);', identity):
        widths.extend([int(width) + 1] * len(names.split(',')))
    tag_bits = sum(widths)
    assert tag_bits == 140
    intake_ii = 2; coefficients_per_tile = 64; residuals_per_tile = 64
    batch_coefficients = 16 * coefficients_per_tile
    batch_input_span_floor = (batch_coefficients - 1) * intake_ii + 1
    assert batch_input_span_floor == 2047
    rows = []
    for variant in ('frozen', 'candidate'):
        for b in bench['runs'][variant]:
            assert b['tiles'] == 16
            item = dict(b, variant=variant)
            if variant == 'candidate':
                assert b['min_accept_gap'] == 2 and b['coefficient_span_cycles'] >= batch_input_span_floor
            if b['profile'] == 0:
                # Source keeps every held tile continuously valid through residual 63.
                # This is an observed average over 15 output-start intervals, not math service.
                item['observed_mean_tile_start_spacing_cycles'] = ratio(
                    b['last_output_offset'] - b['first_output_offset'] - 63, 15)
            rows.append(item)
    zero = next(r for r in rows if r['variant'] == 'candidate' and r['case'] == 'p0_q0_zero' and r['profile'] == 0)
    ac = next(r for r in rows if r['variant'] == 'candidate' and r['case'] == 'p0_q0_ac_pos_limit' and r['profile'] == 0)
    assert zero['coefficient_span_cycles'] == 2047 and zero['max_accept_gap'] == 2
    assert zero['observed_mean_tile_start_spacing_cycles']['decimal'] == 128
    assert ac['observed_mean_tile_start_spacing_cycles']['decimal'] == 140
    output_bounds = {'always_ready': ratio(64, 1), '83_ready_of_257': ratio(64 * 257, 83)}
    sweep = []
    legacy_top = hierarchy['cs88_pipeline_v91k']; legacy_lane = hierarchy['transform']
    for lanes in (1, 2, 4):
        cost = shared + lane_dsp * lanes
        sweep.append(dict(lanes=lanes,implemented_RTL=(lanes == 1),
            conditional_engine_dsp=cost, dsp_capacity=capacity['DSPs']['available'],
            conditional_dsp_percent=100 * cost / capacity['DSPs']['available'],
            dsp_count_only_within_capacity=cost <= capacity['DSPs']['available'],
            candidate_result_slots=2 * lanes, result_payload_bits=2 * lanes * 1536,
            result_identity_bits=2 * lanes * tag_bits,
            result_payload_plus_full_identity_bits=2 * lanes * (1536 + tag_bits),
            additional_result_state_bits=4 * lanes,
            shared_aggregate_intake_floor_cycles_per_tile=coefficients_per_tile * intake_ii,
            always_ready_shared_stage_floor_cycles_per_tile=128,
            bounded_output_shared_stage_floor_cycles_per_tile=output_bounds['83_ready_of_257'],
            conditional_old_V112_whole_transform_replication_LUTs=legacy_top['luts']+(lanes-1)*legacy_lane['luts'],
            conditional_old_replication_exceeds_LUT_capacity=(legacy_top['luts']+(lanes-1)*legacy_lane['luts'])>capacity['Slice LUTs']['available'],
            independent_math_service_cycles_per_tile=None,
            achieved_clock_MHz=None, predicted_FPS=None, complete_device_fit_qualified=False))
    # Meaningful ledger/capacity/conservation invariants, independent of source RTL simulation.
    assert [r['conditional_engine_dsp'] for r in sweep] == [42, 67, 117]
    assert all(r['shared_aggregate_intake_floor_cycles_per_tile'] == 128 for r in sweep)
    assert (16 * 64 - 1) * 2 + 1 == zero['coefficient_span_cycles']
    assert (capacity['DSPs']['available']-shared)//lane_dsp == 8
    assert shared+8*lane_dsp <= capacity['DSPs']['available'] < shared+9*lane_dsp
    def ready_slots(start, cycles):
        return sum((i % 257) < 83 for i in range(start, start + cycles))
    for phase in (0, 1, 82, 83, 128, 256):
        assert ready_slots(phase, 257) == 83
        assert ready_slots(phase, 514) == 166
        assert ready_slots(phase, 83) <= 83
    assert output_bounds['83_ready_of_257']['decimal'] > 128
    assert sum(r['candidate_result_slots'] for r in sweep) == 14
    source_pins = {str(p.relative_to(ROOT)): sha(p) for p in sorted(set(paths))}
    result = dict(schema='v113-lane-resource-bottleneck-ledger-v1', status='PASS',
        actual_RTL_run_by_this_study=False, source_sha256=source_pins,
        scope='1/2/4 compute-lane conditional resource replication and shared-service lower bounds. Two/four lanes are not implemented, simulated or routed. No FPS/clock prediction.',
        actual_V112_hierarchy=hierarchy, actual_part_capacity=capacity,
        DSP_formula='17 shared coefficient/context-path DSP + lanes*(8 dequant + 17 IDCT)',
        shared_DSP_breakdown={'ingress_own':16,'context_decoder':1},
        candidate_lane_result_storage={'slots':2,'payload_bits_per_slot':1536,'full_identity_bits_per_slot':tag_bits,'payload_plus_identity_bits_per_slot':1536+tag_bits,'state_bits_per_slot':2,'other_control_and_coefficient_storage_not_included':True},
        physical_BRAM_groups=[dict(group=k[0],primitive=k[1],count=v,read_width_A=int(k[2]),read_width_B=int(k[3]),write_width_A=int(k[4]),write_width_B=int(k[5]),DOA_REG=int(k[6]),DOB_REG=int(k[7])) for k,v in sorted(ram_groups.items())],
        port_constraints=['Shared single upstream coefficient stream; sweep retains aggregate acceptance at one coefficient per two decoder cycles. 64 coefficients impose 128 cycles/tile steady-state and 2047 cycles for the 1024-offer acceptance span.',
            'Both packet RAMs share each logical registered read port between parser/replay clients; physical bit/depth slices do not grant independent compute-lane reads.',
            'Mode and scale metadata expose one current lookup request/response interface; physical TDP modes do not establish spare independent lane lookup ports.',
            'Scratch has one 128-bit request/response channel and one outstanding physical transaction ledger; reconstruction has one 512-bit reference response channel and ref_pending owner.',
            'Board top has one physical 16-bit SDRAM DQ bus. A 128-bit scratch payload needs at least 8 data beats and a 512-bit reference payload at least 32, before protocol/refresh/arbitration/CDC; requests per tile and calibrated bus service are unknown.',
            'Candidate coefficient banks and two full-width result slots are fixed-word registers; V112 transform maps no RAMB36/RAMB18. No extra BRAM ports are allocated by this ledger.'],
        physical_minimum_payload_beats={'scratch_128bit_over_16bit':8,'reference_512bit_over_16bit':32},
        benchmark_rows=rows, observed_candidate_always_ready_average_cadence={'zero_cycles':128,'AC_positive_limit_cycles':140},
        compute_service_identifiable=False,
        missing_information='Benchmark receipt has whole 16-tile durations, intake/output endpoints and stalls, without per-job DQ-launch/IDCT-complete timestamps. First residual offset includes 64-coefficient intake, validation/commit, launch and result ownership; it cannot be labeled pure compute latency.',
        assumptions=['Shared aggregate coefficient acceptance remains II=2 for all lane counts. Alternating lane accepts to reach one coefficient/cycle would require a new dispatcher/ownership contract and is outside this sweep.',
                     'Residual output remains one value/cycle, with either always-ready or the actual bench ready pattern cycle%257<83.',
                     'DSP replication cost uses V112 mapped unchanged DQ/IDCT blocks and shared 17-DSP path conditionally; new lane control/metadata/dispatch storage and placement are not measured.',
                     'The legacy LUT replication column copies the OLD V112 whole transform linearly as a diagnostic cost only. It is not a V113 mapping estimate or a proof of fit/failure.'],
        sweep=sweep, invariants={'status':'PASS','all_8_benchmark_rows_bound':len(rows)==8,'1024_coefficient_acceptance_span_floor_matches_fast_row':True,'shared_intake_floor_does_not_shrink_with_lanes':True,'DSP_capacity_boundary_checked_at_8_and_9_lanes':True,'bounded_output_pattern_count_checked_across_phases':True,'result_slots_and_full_identity_counted':True},
        conclusion='Fast candidate zero workload already reaches the retained shared-intake floor; extra lanes cannot reduce that floor under this contract. AC observed end-to-end mean is 140 cycles/tile, but independent math service is unmeasured, so no two/four-lane speedup is assigned. The bounded consumer floor is 16448/83 cycles/tile for every lane count. DSP fit alone does not qualify complete device/port/timing fit.')
    assert source_pins == {str(p.relative_to(ROOT)):sha(p)for p in sorted(set(paths))}
    (AREA/'results.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    with (AREA/'sweep.csv').open('w',newline='')as f:
        keys=['lanes','conditional_engine_dsp','dsp_capacity','candidate_result_slots','result_payload_plus_full_identity_bits','shared_aggregate_intake_floor_cycles_per_tile','complete_device_fit_qualified']
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows({k:r[k]for k in keys}for r in sweep)
    print('V113_LANE_LEDGER_PASS',json.dumps({'lanes':[1,2,4],'conditional_DSP':[42,67,117],'shared_intake_floor':128,'bounded_output_floor':output_bounds['83_ready_of_257'],'independent_math_service_identified':False,'results_sha256':sha(AREA/'results.json')}))

if __name__ == '__main__':
    main()
