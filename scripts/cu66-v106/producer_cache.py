#!/usr/bin/env python3
"""Build exact producer cache edits and exhaust their finite transition model."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
FPGA = ROOT / 'fpga/experiments/cu66-v106-producer-cache'
AREA = ROOT / 'experiments/python-gamebub-v106/producer-cache'
NAMES = ('cs88_coefficients_v91k.sv', 'cs88_pipeline_v91i2b.sv')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def pin(path):
    return dict(path=str(path.relative_to(ROOT)), sha256=digest(path.read_bytes()))


def edits():
    pairs = [
        ('private_cache', '    logic [10:0] mapped_cell;',
         '    logic [10:0] mapped_cell;\n    logic [10:0] producer_cell_cache;'),
        ('lookup_address', '    assign lookup_cell=quant_cell(plane,tile_cursor);',
         '    assign lookup_cell=producer_cell_cache;'),
        ('reset_abort', 'plane<=0;tile_cursor<=0;mapped_tile<=0;',
         'plane<=0;tile_cursor<=0;producer_cell_cache<=0;mapped_tile<=0;'),
        ('accepted_start', 'plane<=0;tile_cursor<=0;expected_block<=0;',
         'plane<=0;tile_cursor<=0;producer_cell_cache<=0;expected_block<=0;'),
        ('entropy_success_plane_zero', 'end else begin plane<=0;state<=PREP_PLANE;end',
         "end else begin plane<=0;producer_cell_cache<=quant_cell(0,tile_cursor);state<=PREP_PLANE;end"),
        ('prepare_tile_zero', 'tile_cursor<=0;expected_block<=0;refill_cursor<=0;',
         'tile_cursor<=0;producer_cell_cache<=0;expected_block<=0;refill_cursor<=0;'),
        ('capture_mapped_cell', 'mapped_cell<=quant_cell(plane,tile_cursor);',
         'mapped_cell<=producer_cell_cache;'),
        ('skip_tile', '                        end else begin tile_cursor<=tile_cursor+1;state<=MAP_REQ;end',
         "                        end else begin tile_cursor<=tile_cursor+1;producer_cell_cache<=quant_cell(plane,tile_cursor+13'd1);state<=MAP_REQ;end"),
        ('advance_tile', '                            else begin tile_cursor<=tile_cursor+1;state<=MAP_REQ;end',
         "                            else begin tile_cursor<=tile_cursor+1;producer_cell_cache<=quant_cell(plane,tile_cursor+13'd1);state<=MAP_REQ;end"),
        ('advance_plane', 'else begin plane<=plane+1;state<=PREP_PLANE;end',
         "else begin plane<=plane+1;producer_cell_cache<=quant_cell(plane+2'd1,tile_cursor);state<=PREP_PLANE;end"),
        ('live_invariant', '    always_ff @(posedge clk) if(!reset&&!abort_packet)begin',
         '    always_ff @(posedge clk) if(!reset&&!abort_packet)begin\n'
         '        assert(producer_cell_cache==quant_cell(plane,tile_cursor))else $fatal(1,"producer quant-cell cache mismatch");'),
    ]
    return [dict(name=n, before=b, after=a, expected_occurrences=1) for n, b, a in pairs]


def build(original):
    candidate = original
    recipe = edits()
    assert len(re.findall(r'\bplane\s*<=', original)) == 4
    assert len(re.findall(r'\btile_cursor\s*<=', original)) == 5
    for edit in recipe:
        assert candidate.count(edit['before']) == 1, edit['name']
        candidate = candidate.replace(edit['before'], edit['after'], 1)
    # Public header, every original guard/state transition and the original
    # plane/tile update stream stay byte-identical outside the recorded edits.
    assert original[:original.index(');') + 2] == candidate[:candidate.index(');') + 2]
    for variable in ('plane', 'tile_cursor'):
        pattern = r'\b' + variable + r'\s*<=([^;]+);'
        assert re.findall(pattern, original) == re.findall(pattern, candidate)
    return candidate, recipe


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    FPGA.mkdir(exist_ok=True)
    AREA.mkdir(exist_ok=True)
    helpers_path = ROOT / 'fpga/experiments/cu66-v106-math/helpers.json'
    helper = json.loads(helpers_path.read_text())['lut']
    banks = {}
    for bank, body in re.findall(r"6'd(\d+):begin(.*?)end", helper, re.S):
        banks[int(bank)] = {int(bit): int(value, 16)
            for bit, value in re.findall(r"lut(\d+)=64'h([0-9a-f]{16});", body)}
    assert set(banks) == set(range(64)) and all(set(v) == set(range(11)) for v in banks.values())

    def actual_helper(p, t):
        if p:
            return t & 2047
        return sum(((banks[t >> 7][bit] >> ((t & 127) >> 1)) & 1) << bit for bit in range(11))

    def oracle(p, t):
        y, x = divmod(t, 90)
        return ((y // 2) * 45 + x // 2 if p == 0 else t) & 2047

    production = []
    for name in NAMES:
        old = ROOT / 'fpga/experiments/cu66-v106-math/lut' / name
        new = FPGA / name
        original = old.read_text()
        assert helper in original
        candidate, recipe = build(original)
        recipe_path = new.with_suffix('.recipe.json')
        payload = dict(schema='v106-edit-recipe-v1', variant='producer-cache',
            original_path=str(old.relative_to(ROOT)), original_sha256=digest(original.encode()),
            candidate_path=str(new.relative_to(ROOT)), candidate_sha256=digest(candidate.encode()), edits=recipe)
        encoded = json.dumps(payload, indent=2, sort_keys=True) + '\n'
        if args.verify:
            assert new.read_text() == candidate and recipe_path.read_text() == encoded
        else:
            assert not new.exists() and not recipe_path.exists(), 'Use --verify for frozen files'
            new.write_text(candidate)
            recipe_path.write_text(encoded)
        production.append(dict(source=pin(new), recipe=pin(recipe_path), inherited=pin(old)))

    rows = bytearray()
    operations = ('hold', 'reset_or_abort', 'accepted_start', 'entropy_plane_zero',
                  'prepare_tile_zero', 'skip_tile', 'advance_tile', 'advance_plane')
    count = 0
    for p in range(4):
        for t in range(8192):
            assert actual_helper(p, t) == oracle(p, t)
            for op, role in enumerate(operations):
                np, nt = p, t
                if op in (1, 2):
                    np, nt = 0, 0
                elif op == 3:
                    np = 0
                elif op == 4:
                    nt = 0
                elif op in (5, 6):
                    nt = (t + 1) & 8191
                elif op == 7:
                    np = (p + 1) & 3
                cache = actual_helper(p, t) if op == 0 else actual_helper(np, nt)
                assert cache == oracle(np, nt), (p, t, role)
                rows.extend(f'{p}\t{t}\t{op}\t{np}\t{nt}\t{cache}\n'.encode())
                count += 1
    assert count == 262144
    trace = gzip.compress(bytes(rows), mtime=0)
    trace_path = AREA / 'transitions.tsv.gz'
    result = dict(schema='v106-producer-cache-transition-model-v1', status='PASS_MODEL_AND_EXACT_SOURCE_RECIPES',
        generator=pin(Path(__file__)), production=production, helper=pin(helpers_path),
        helper_domain_cases=32768, transition_model_rows=count, operations=list(operations),
        trace_sha256=digest(trace), raw_trace_sha256=digest(bytes(rows)),
        actual_RTL_run=False, integrated_RTL_required=True,
        induction='Reset/abort initializes cache=f(0,0). All four plane assignments and all five tile assignments have exact matching cache RHS; otherwise cache holds. The finite helper and all transition roles exhaust binary plane/tile domains including wraps. Original branch/guard bytes and public headers are preserved.',
        limits=['Python transition model and exact source edit recovery, not standalone whole-controller RTL simulation or reachability proof.',
                'Both actual production modules have a live cache invariant; final paired pipeline lanes must pass before selection.',
                'No formal/four-state/mapped-netlist, native timing or hardware qualification.'])
    path = AREA / 'results.json'
    encoded = json.dumps(result, indent=2, sort_keys=True) + '\n'
    if args.verify:
        assert trace_path.read_bytes() == trace and path.read_text() == encoded
    else:
        trace_path.write_bytes(trace)
        path.write_text(encoded)
    print('V106_PRODUCER_CACHE_MODEL_PASS', count, 'rows; actual pipeline RTL required')


if __name__ == '__main__':
    main()
