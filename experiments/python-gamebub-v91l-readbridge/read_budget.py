#!/usr/bin/env python3
"""Source-FSM work model for three SDRAM read schedules; no hardware claim."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = Path(__file__).resolve().parent
VECTOR = ROOT / 'experiments/python-gamebub-v91l-tiled/vectors/prefill-lines.hex.gz'
OUTPUT = AREA / 'read-budget-results.json'
SOURCES = [
    'fpga/experiments/cu66-v91l-writepipe/controller/moonshine_sdram.sv',
    'docs/cu66-v91l-writepipe/timing-contract.md',
    'experiments/python-gamebub-v91l-tiled/audit-models.json',
    'experiments/python-gamebub-v91l-tiled/prefill-results.json',
    'experiments/python-gamebub-v91l-tiled/prefill_model.py',
    'experiments/python-gamebub-v91l-tiled/verify_models.py',
]
INPUT = 'fpga/experiments/cu66-v91k-lines/comparison-attempts/20261106T223415479309Z-7a2603de/inputs/canonical_actual.tsv.gz'
PLANE = ((0, 720, 480), (345600, 360, 240), (432000, 360, 240))
FRAME_BYTES = 518400
REFRESH_CYCLES = 750


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def layout_addr(address):
    p = 0 if address < 345600 else 1 if address < 432000 else 2
    base, width, _height = PLANE[p]
    y, x = divmod(address - base, width)
    tile = (y // 8) * (width // 8) + x // 8
    return base + tile * 64 + (y % 8) * 8 + x % 8


def load_requests():
    raw = gzip.decompress(VECTOR.read_bytes())
    req = [int(v, 16) for v in raw.splitlines()]
    assert len(req) == 32400 and len(set(req)) == 32400
    assert all(0 <= a < FRAME_BYTES and a % 16 == 0 for a in req)
    return raw, req


def scenario_bursts(requests):
    # Raster control uses one physical 16-byte burst per aligned logical line.
    raster = list(requests)

    # Tile independent reproduces verify_models.cache's two 8-byte gathers per
    # 16-byte client line, with its shared 16-byte response scratch reset for
    # each client request. Each gathered byte maps through the tile8x8 layout.
    independent = []
    for a in requests:
        scratch = None
        for logical in (a, a + 8):
            burst = layout_addr(logical) & ~15
            if scratch != burst:
                independent.append(burst)
                scratch = burst

    # Retained mode mirrors verify_models.cache's future-fragment lifetime,
    # only emitting a physical read on a scratch miss. The older verifier checks
    # value equality against both canonical frame fixtures for this exact filter.
    tags = [None, None, None]
    fragments = [{}, {}, {}]
    scratch = None
    retained = []
    for a in requests:
        for logical in (a, a + 8):
            p = 0 if logical < 345600 else 1 if logical < 432000 else 2
            base, width, _height = PLANE[p]
            y, x = divmod(logical - base, width)
            burst = layout_addr(logical) & ~15
            if tags[p] == y and x in fragments[p]:
                continue
            if scratch != burst:
                retained.append(burst)
                scratch = burst
                if y % 2 == 0:
                    if tags[p] != y + 1:
                        fragments[p] = {}
                        tags[p] = y + 1
                    fragments[p][x] = True
    assert len(raster) == 32400
    assert len(independent) == 64800
    assert len(retained) == 32400
    return {'raster_control': raster, 'tile_independent': independent,
            'tile_retained': retained}


def run_source_fsm(bursts):
    """Run read-only controller state transitions after init, with requests always queued."""
    state, next_state, delay = 'IDLE', 'IDLE', 0
    refresh_count = 0
    open_rows = [None] * 4
    address = None
    beat = 0
    remaining = 0
    idx = 0
    cycles = reads = acts = pres = refreshes = responses = 0
    row_hits = conflicts = 0
    while idx < len(bursts) or state != 'IDLE':
        cycles += 1
        old_refresh = refresh_count
        refresh_count = min(65535, refresh_count + 1)
        if state == 'IDLE':
            if old_refresh >= REFRESH_CYCLES:
                state = 'REFRESH_PRE'
            elif idx < len(bursts):
                address = bursts[idx]
                idx += 1
                remaining += 1
                word_address = address >> 1
                bank = (word_address >> 22) & 3
                row = (word_address >> 9) & 0x1FFF
                if open_rows[bank] is not None and open_rows[bank] == row:
                    row_hits += 1
                    state = 'RW_CMD'
                elif open_rows[bank] is not None:
                    conflicts += 1
                    state = 'PRECHARGE'
                else:
                    state = 'ACTIVATE'
        elif state == 'PRECHARGE':
            pres += 1
            word_address = address >> 1
            bank = (word_address >> 22) & 3
            open_rows[bank] = None
            delay, next_state, state = 2, 'ACTIVATE', 'WAITING'
        elif state == 'ACTIVATE':
            acts += 1
            word_address = address >> 1
            bank = (word_address >> 22) & 3
            row = (word_address >> 9) & 0x1FFF
            open_rows[bank] = row
            delay, next_state, state = 2, 'RW_CMD', 'WAITING'
        elif state == 'RW_CMD':
            reads += 1
            delay, state, beat = 5, 'READ_WAIT', 0
        elif state == 'READ_WAIT':
            if delay == 0:
                responses += 1
                beat = 1
                state = 'READ_BURST'
            else:
                delay -= 1
        elif state == 'READ_BURST':
            responses += 1
            if beat == 7:
                state = 'IDLE'
            else:
                beat += 1
        elif state == 'REFRESH_PRE':
            pres += 1
            open_rows = [None] * 4
            delay, next_state, state = 2, 'REFRESH', 'WAITING'
        elif state == 'REFRESH':
            refreshes += 1
            refresh_count = 0
            delay, next_state, state = 8, 'IDLE', 'WAITING'
        elif state == 'WAITING':
            if delay == 0:
                state = next_state
            else:
                delay -= 1
        else:
            raise AssertionError(state)
    assert reads == len(bursts) and responses == reads * 8, (reads, len(bursts), responses)
    return dict(physical_bl8_reads=reads, useful_bytes=reads and 518400,
                fetched_bytes=reads * 16, overfetch_bytes=reads * 16 - 518400,
                response_word_beats=responses, row_activates=acts,
                row_precharges=pres, refresh_commands=refreshes,
                row_hits=row_hits, row_conflicts=conflicts,
                source_fsm_cycles_after_init=cycles,
                source_fsm_time_ns_at_10ns=cycles * 10,
                scope='serialized always-ready read-only source-state replay; initial power-up/init excluded')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()
    raw, requests = load_requests()
    schedules = scenario_bursts(requests)
    source = {p: sha(ROOT / p) for p in SOURCES}
    source[str(VECTOR.relative_to(ROOT))] = sha(VECTOR)
    source[INPUT] = sha(ROOT / INPUT)
    result = dict(
        schema='cu66-v91l-readbridge-work-v1',
        status='PASS_SOURCE_DERIVED_COMMAND_WORK_MODEL',
        provenance='Derived from the checked-in 32,400-entry client prefill vector and source-FSM/address mapping; not captured physical read events.',
        source_revision='b96944dd9897e2bf4e9ed2978bdbade79cdccb7b',
        source_sha256=source,
        generator_sha256=sha(Path(__file__).resolve()),
        vector=dict(path=str(VECTOR.relative_to(ROOT)), line_count=len(requests),
                    gzip_sha256=sha(VECTOR), raw_sha256=hashlib.sha256(raw).hexdigest(),
                    request_semantics='aligned logical canonical 16-byte client line misses in CHECK_ROWS chroma-prefill then raster-luma order'),
        assumptions=dict(source_clock_ns=10, logical_request_bytes=16,
                         physical_bl8_bytes=16, controller_mode='CAS3, BL8, x16, address in 16-bit words',
                         controller_start='IDLE after initialization; open rows initially closed',
                         startup_phase='idealized accounting phase with refresh_count=0; not the literal post-MRS controller count',
                         request_offer='next request continuously valid whenever source controller is IDLE',
                         read_responses_per_bl8=8, refresh_threshold_cycles=REFRESH_CYCLES,
                         hud_reads=0, hud_in_vector=False),
        frames={'actual_001': 'byte-exact fixture verified in upstream verify_models.py',
                'actual_006': 'byte-exact fixture verified in upstream verify_models.py'},
        scenarios={name: run_source_fsm(addrs) for name, addrs in schedules.items()},
        interpretation=dict(command_counts='Exact for this serialized event replay of the read-side FSM and these generated physical bursts.',
            timing='State waits and BL8 response beats follow moonshine_sdram.sv; excludes initial 20,000-cycle power-up and two init refreshes.',
            refresh='Every REFRESH_PRE/REFRESH command and all-bank precharge is modeled at the source threshold; threshold counter advances each source cycle.',
            no_full_frame_estimate=True,
            exclusions=['converter arithmetic', 'bridge/client scheduling or arbitration', 'hashes', 'scratch/shared traffic',
                        'board I/O and pin flight', 'initialization', 'HUD', 'write traffic']),
        limits=['This is a bounded prefill-work comparison, not an FPS/frame-time or complete-frame estimate.',
                'The raster control assumes canonical raster physical byte placement; the tile scenarios use 8x8 tile-major mapping.',
                'Retained fetch filter mirrors verify_models.cache; upstream verifier checks all 518,400 client bytes for actual_001 and actual_006.',
                'Always-valid serialized source-FSM replay excludes any bridge backpressure, concurrent traffic, arbitration, or board effects.'])
    data = json.dumps(result, indent=2) + '\n'
    if args.check:
        assert OUTPUT.read_text() == data, 'stale result JSON'
    else:
        OUTPUT.write_text(data)
    print(json.dumps(dict(status=result['status'], scenarios=len(schedules), requests=len(requests), output=str(OUTPUT))))


if __name__ == '__main__':
    main()
