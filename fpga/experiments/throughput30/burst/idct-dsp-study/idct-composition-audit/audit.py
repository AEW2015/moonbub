#!/usr/bin/env python3
"""Check elaborated IDCT connectivity and proof-bound source fingerprints."""
import hashlib,json,re,sys
from pathlib import Path
if len(sys.argv)!=2:raise SystemExit('usage: audit.py ELABORATED_JSON')
root=Path(__file__).resolve().parents[6];v=root/'fpga/vendor/core_jpeg/src_v';study=root/'fpga/experiments/throughput30/burst/idct-dsp-study'
hashes={'jpeg_idct.v':'f2a45496e29d43eb2b2f024921a5b96732ce57a3f74e4c856686cf00acacd0b6','jpeg_idct_x.v':'99b8681e002d948fa4ed5fbd3a29704634400c31c376b5e120c07d1392ef62c0','jpeg_idct_y.v':'df2bbd47864431354baa2dbc0160b809d94de624d5e16d1a45b313d4564bc9c8','jpeg_idct_ram.v':'b45d1f8663c290a27085ed595d633caec980410a1483f10a80be1bfad87a570a','jpeg_idct_ram_dp.v':'191622cc6447224294c1cfe98aef9fbb329b3a8b00932ed1b33920e90d2b61ea','jpeg_idct_transpose.v':'4b765d2227366e6cfd7953f0f17de3fbbd9f1bf2f55e8207bd5611a96a21e54c','jpeg_idct_transpose_ram.v':'833abadcd8fb585d08dddc7e1cc24cfd3e39a9eb728aa72a8d7b016694fc370b','jpeg_idct_fifo.v':'487d095dc70369d4bb7c9a27e6f27cc4db082b95e9bb6ce13292dc31fb2cf5e0','jpeg_core.v':'2258f5bec64b0477d30727b428548804ed94c7cc045f108fc203e3925c8c97d0'}
for name,h in hashes.items():
 if hashlib.sha256((v/name).read_bytes()).hexdigest()!=h:raise SystemExit(f'source hash mismatch: {name}')
for rel,h in [('narrow-x/jpeg_idct_x_narrow.v','d3cefd3651622c793ec92cff696a971a7e22bcdc694541960292d2b499880cde'),('narrow-y-coeff/jpeg_idct_y_coeff.v','e5ddd2d9392c597bbf5b2740bb7b09c9c8c8271c4a5cb732a4652971c2358cd8')]:
 if hashlib.sha256((study/rel).read_bytes()).hexdigest()!=h:raise SystemExit(f'candidate hash mismatch: {rel}')
for proof in ['narrow-x-proof','narrow-y-coeff']:
 for name,needle in [('operand.log','Induction step proven: SUCCESS!'),('operand-reset.log','SAT proof finished - no model found: SUCCESS!'),('product.log','SAT proof finished - no model found: SUCCESS!'),('state.log','Induction step proven: SUCCESS!'),('state-reset.log','SAT proof finished - no model found: SUCCESS!'),('operand-mutant.log','SAT proof finished - model found: FAIL!'),('state-mutant.log','SAT proof finished - model found: FAIL!')]:
  if needle not in (study/proof/'results'/name).read_text():raise SystemExit(f'missing proof marker: {proof}/{name}')
x=json.loads(Path(sys.argv[1]).read_text());mods=x['modules'];top=mods['jpeg_idct'];cells=top['cells'];ports=top['ports']
expected={'u_input':'jpeg_idct_ram','u_idct_x':'jpeg_idct_x','u_transpose':'jpeg_idct_transpose','u_idct_y':'jpeg_idct_y'}
for name,typ in expected.items():
 if cells[name]['type']!=typ or cells[name]['parameters']:raise SystemExit(f'unexpected instance or override: {name}')
for typ,names in [('jpeg_idct_x',['u_idct_x']),('jpeg_idct_y',['u_idct_y'])]:
 if [n for n,c in cells.items() if c['type']==typ]!=names:raise SystemExit('unexpected stage instance count')
for typ,params in [('jpeg_idct_x',{'INPUT_WIDTH':16,'OUT_SHIFT':11}),('jpeg_idct_y',{'INPUT_WIDTH':32,'OUT_SHIFT':15})]:
 if {k:int(v,2) for k,v in mods[typ]['parameter_default_values'].items()}!=params:raise SystemExit(f'default mismatch {typ}')
def same(a,ap,b,bp):
 if cells[a]['connections'][ap]!=cells[b]['connections'][bp]:raise SystemExit(f'net mismatch {a}.{ap} {b}.{bp}')
for name in expected:
 for port in ('clk_i','rst_i','img_start_i','img_end_i'):
  if cells[name]['connections'][port]!=ports[port]['bits']:raise SystemExit(f'common port mismatch {name}.{port}')
for pin,port in [('inport_valid_i','inport_valid_i'),('inport_data_i','inport_data_i'),('inport_idx_i','inport_idx_i'),('inport_eob_i','inport_eob_i'),('inport_accept_o','inport_accept_o'),('outport_ready_i','outport_accept_i')]:
 if cells['u_input']['connections'][pin]!=ports[port]['bits']:raise SystemExit(f'input buffer port mismatch: {pin}')
ram=mods['jpeg_idct_transpose_ram'];reset_bits=set(ram['ports']['rst0_i']['bits']+ram['ports']['rst1_i']['bits'])
if any(reset_bits.intersection(bits) for c in ram['cells'].values() for bits in c['connections'].values()):raise SystemExit('transpose RAM reset ports unexpectedly used')
for i in range(4):
 same('u_input',f'outport_data{i}_o','u_idct_x',f'inport_data{i}_i')
 same('u_transpose',f'outport_data{i}_o','u_idct_y',f'inport_data{i}_i')
for field in ('valid','idx'):
 same('u_input',f'outport_{field}_o','u_idct_x',f'inport_{field}_i')
 same('u_transpose',f'outport_{field}_o','u_idct_y',f'inport_{field}_i')
for field in ('data','idx','valid'):same('u_idct_x',f'outport_{field}_o','u_transpose',f'inport_{field}_i')
if cells['u_transpose']['connections']['outport_ready_i']!=['1']:raise SystemExit('transpose ready not tied high')
for field in ('data','idx','valid'):
 if cells['u_idct_y']['connections'][f'outport_{field}_o']!=ports[f'outport_{field}_o']['bits']:raise SystemExit('Y output mismatch')
fifo_type=cells['u_id_fifo']['type']
if not fifo_type.endswith('\\jpeg_idct_fifo'):raise SystemExit('unexpected FIFO module')
if {k:int(v,2) for k,v in mods[fifo_type]['parameter_default_values'].items()}!={'WIDTH':32,'DEPTH':8,'ADDR_W':3}:raise SystemExit('FIFO parameter mismatch')
if not re.search(r'(?m)^jpeg_idct\s+u_jpeg_idct\s*\(', (v/'jpeg_core.v').read_text()):raise SystemExit('core instance override or structure changed')
fifo=cells['u_id_fifo']['connections']
for pin,port in [('clk_i','clk_i'),('rst_i','rst_i'),('flush_i','img_start_i'),('push_i','inport_eob_i'),('data_in_i','inport_id_i'),('data_out_o','outport_id_o')]:
 if fifo[pin]!=ports[port]['bits']:raise SystemExit(f'FIFO port mismatch {pin}')
eqs=[c for c in cells.values() if c['type']=='$eq' and c['connections']['A']==ports['outport_idx_o']['bits'] and c['connections']['B']==['1']*6]
if len(eqs)!=1:raise SystemExit('FIFO index comparator mismatch')
ands=[c for c in cells.values() if c['type']=='$logic_and' and c['connections']['A']==ports['outport_valid_o']['bits'] and c['connections']['B']==eqs[0]['connections']['Y'] and c['connections']['Y']==fifo['pop_i']]
if len(ands)!=1:raise SystemExit('FIFO pop mismatch')
pattern=re.compile(r'^\s*(jpeg_idct(?:_x|_y)?)\s*(?:#\s*\([^;]*?\)\s*)?\s+(\w+)\s*\(',re.M|re.S)
found=[]
for path in sorted(v.glob('*.v')):
 for m in pattern.finditer(path.read_text()):found.append((path.name,m.group(1),m.group(2)))
if sorted(found)!=sorted([('jpeg_core.v','jpeg_idct','u_jpeg_idct'),('jpeg_idct.v','jpeg_idct_x','u_idct_x'),('jpeg_idct.v','jpeg_idct_y','u_idct_y')]):raise SystemExit(f'unexpected vendor instances: {found}')
print('STRUCTURAL_AUDIT_PASS vendor stage instances=1+1 defaults X=(16,11) Y=(32,15)')
print('input->X->transpose->Y->output and ID FIFO connectivity verified; clock/reset/start/end shared')
print('stage source hashes, candidate hashes and proof markers verified; composition inference is manual')
