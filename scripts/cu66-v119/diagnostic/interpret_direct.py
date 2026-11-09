#!/usr/bin/env python3
"""Interpret actual V119 A125 carry INIT/wiring; never launches Vivado or modifies RTL."""
import collections
import functools
import hashlib
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[3]
AREA = ROOT / 'experiments/python-gamebub-v119/checkpoint-diagnostic'
SELECTOR = AREA / 'results-direct.json'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
selector = json.loads(SELECTOR.read_text())
p = ROOT / selector['receipt']
receipt = json.loads(p.read_text())
assert sha(p) == selector['receipt_sha256']
assert receipt['observed_exit_code'] == 0 and receipt['checkpoint_unchanged'] and receipt['diagnostic_tcl_unchanged']
assert receipt['elapsed_seconds'] < 240 and receipt['complete_marker'] and receipt['stop_reason'] is None
for name, value in receipt['artifacts_sha256'].items():
    assert sha(p.parent / name) == value, name
rows = [line.split('\t') for line in (p.parent / 'operands.tsv').read_text().splitlines()[1:]]
# Record repeated queries but insist that duplicate answers agree.
records = collections.defaultdict(set)
for kind, obj, key, value in rows:
    records[kind, obj, key].add(value)
assert all(len(values) == 1 for values in records.values())
def field(kind, obj, key):
    return next(iter(records[kind, obj, key]))
net_drivers = {obj: next(iter(values)).split(';') for (kind, obj, key), values in records.items() if kind == 'NET' and key == 'DRIVER_PINS' and next(iter(values))}
pin_nets = {obj: next(iter(values)) for (kind, obj, key), values in records.items() if kind == 'PIN' and key == 'NETS'}
carry_nets = {obj: next(iter(values)) for (kind, obj, key), values in records.items() if kind == 'CARRY_PIN' and key == 'NETS'}
refnames = {obj: next(iter(values)) for (kind, obj, key), values in records.items() if kind == 'CELL' and key == 'REF_NAME'}
inits = {obj: next(iter(values)) for (kind, obj, key), values in records.items() if kind == 'CELL' and key == 'INIT'}
base = 'coefficients/child/packet_decoder/synchronous.ingress/'
low = base + 'dbg_coef_valid_INST_0_i_11'
high = base + 'dbg_coef_valid_INST_0_i_4'
targets = [low, high]
operand_plan = {}
used_luts = set()
used_inputs = set()

def expression(net):
    drivers = net_drivers[net]
    assert len(drivers) == 1, (net, drivers)
    driver = drivers[0]
    raw = re.fullmatch(re.escape(base) + r'raw_coefficient_reg\[(\d+)\]/Q', driver)
    if raw:
        used_inputs.add(int(raw.group(1)))
        return ('raw_bit', int(raw.group(1)))
    if driver == base + 'GND/G':
        return ('constant', 0)
    if driver == low + '/CO[3]':
        return ('low_carry_CO3',)
    cell, pin = driver.rsplit('/', 1)
    assert refnames[cell] == 'LUT2' and pin == 'O', (cell, pin, refnames.get(cell))
    used_luts.add(cell)
    init = int(re.fullmatch(r"4'h([0-9a-fA-F]+)", inits[cell]).group(1), 16)
    return ('LUT2', cell, init, expression(pin_nets[cell + '/I0']), expression(pin_nets[cell + '/I1']))

for cell in targets:
    for pin in ['CI', 'CYINIT'] + [f'{part}[{i}]' for part in ['DI', 'S'] for i in range(4)]:
        operand_plan[cell + '/' + pin] = expression(carry_nets[cell + '/' + pin])
assert used_inputs == set(range(16))
assert len(used_luts) == 15

def eval_expr(expr, word, low_out):
    if expr[0] == 'raw_bit':
        return (word >> expr[1]) & 1
    if expr[0] == 'constant':
        return expr[1]
    if expr[0] == 'low_carry_CO3':
        return low_out
    assert expr[0] == 'LUT2'
    address = eval_expr(expr[3], word, low_out) | (eval_expr(expr[4], word, low_out) << 1)
    return (expr[2] >> address) & 1

def carry_outputs(cell, word, low_out):
    value = lambda pin: eval_expr(operand_plan[cell + '/' + pin], word, low_out)
    prev = value('CI') | value('CYINIT')
    result = []
    # Exact installed CARRY4 model: CO = (S & CO_fb) | (~S & DI).
    for bit in range(4):
        select = value(f'S[{bit}]')
        prev = prev if select else value(f'DI[{bit}]')
        result.append(prev)
    return result

mismatch_low = []
mismatch_signed_gt = []
mismatch_full_prefix = []
ones = 0
boundaries = {}
for word in range(65536):
    low_out = carry_outputs(low, word, 0)[3]
    high_out = carry_outputs(high, word, low_out)[2]
    signed = word if word < 32768 else word - 65536
    if low_out != int((word & 1023) != 0):
        mismatch_low.append(word)
    if high_out != int(signed > 2048):
        mismatch_signed_gt.append(word)
    prefix_valid = (word >> 11) in (0, 31) or word == 0x0800
    if prefix_valid != (-2048 <= signed <= 2048):
        mismatch_full_prefix.append(word)
    ones += high_out
    if signed in [-32768, -2049, -2048, -1, 0, 2047, 2048, 2049, 32767]:
        boundaries[str(signed)] = dict(word_hex=f'{word:04x}', actual_high_CO2=high_out, actual_low_CO3=low_out, signed_gt_2048=int(signed > 2048), complete_range_valid=prefix_valid)
assert not mismatch_low and not mismatch_signed_gt and not mismatch_full_prefix
assert ones == 30719
unresolved = [row for row in rows if row[0] == 'UNRESOLVED']
assert len(unresolved) == 9
assert {row[1] for row in unresolved} == {'coefficients/admission/mode_store/abort_packet', 'coefficients/child/packet_decoder/synchronous.ingress/context_decoder/parser/reset', 'coefficients/child/scratch/reset'}
assert not any(row[1].startswith(base + 'dbg_coef_valid_INST_0_i_') for row in unresolved)
loads = {obj: int(next(iter(values))) for (kind, obj, key), values in records.items() if kind == 'CONTROL_NET' and key == 'LOAD_PIN_COUNT'}
assert len(loads) == 12 and all(v > 0 for v in loads.values())
assert loads[base + 'context_decoder/parser/limit0_2[0]'] == 1031
models = {name: pathlib.Path('/home/lori/acorn-nexys4-ddr/tools/2026.1/Vivado/data/verilog/src/xeclib') / name for name in ['CARRY4.v', 'LUT2.v']}
assert 'assign CO = (S_in & CO_fb) | (~S_in & DI_in);' in models['CARRY4.v'].read_text()
assert 'assign O = INIT[{I1,I0}];' in models['LUT2.v'].read_text()
out = dict(schema='v119-actual-carry-operand-interpretation-v1', status='PASS_SPECIFIC_CARRY_EQUATIONS_GENERAL_CONNECTIVITY_PARTIAL', selector=str(SELECTOR.relative_to(ROOT)), selector_sha256=sha(SELECTOR), receipt=str(p.relative_to(ROOT)), receipt_sha256=sha(p), operands_sha256=sha(p.parent / 'operands.tsv'), interpreter_path=str(pathlib.Path(__file__).relative_to(ROOT)), interpreter_sha256=sha(pathlib.Path(__file__)), actual_diagnostic_status=receipt['status'], checkpoint_unchanged=receipt['checkpoint_unchanged'], checkpoint_sha256=receipt['checkpoint_sha256'], elapsed_seconds=receipt['elapsed_seconds'], vendor_model_pins={name: dict(path=str(path), sha256=sha(path)) for name, path in models.items()}, operand_plan=operand_plan, used_raw_bits=sorted(used_inputs), used_LUT2_cells={cell: inits[cell] for cell in sorted(used_luts)}, exhaustive_values=65536, actual_low_carry_CO3_expression='OR(raw_coefficient[9:0])', actual_high_carry_CO2_expression='signed16(raw_coefficient) > 2048', actual_high_CO2_ones=ones, low_CO3_mismatches=len(mismatch_low), high_CO2_mismatches=len(mismatch_signed_gt), candidate_full_range_prefix='raw[15:11] == 0 OR raw[15:11] == 31 OR raw == 0x0800', candidate_full_range_prefix_mismatches=len(mismatch_full_prefix), boundary_values=boundaries, actual_control_leaf_load_counts=loads, general_unresolved_rows=unresolved, unresolved_scope='Three reset/abort hierarchical aliases have no local leaf driver; all target CARRY inputs have complete single-driver/LUT2/GND connectivity. Those nine repeated misses do not participate in either resolved carry operand cone.', native_physical_trial=False, positive_repeat=False, new_RTL=False, improved_timing_claim=False)
path = ROOT / 'experiments/python-gamebub-v119/audit/checkpoint-diagnostic-direct-results.json'
path.write_text(json.dumps(out, indent=2) + '\n')
print(out['status'])
print('65536 values; lower OR10 and upper signed>2048 mismatches=0; prefix range mismatches=0')
print('12 actual control leaf counts:', loads)
