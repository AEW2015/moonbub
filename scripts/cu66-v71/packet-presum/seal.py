"""Manual source/hash/content audit; no unavailable c_check_handoff claim."""
from pathlib import Path
import hashlib,json,re
r=Path(__file__).resolve().parents[3];d=r/'fpga/experiments/cu66-v71/packet-prefix-v002';o=d/'evidence';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(d/'cu71_packet_presum.sv')=='9ab9f4abd82d130cd627a952f78efe841a0fc3505a832e40348f64d82d3ad7e2'
assert sha(r/'fpga/experiments/cu66-v69/packet/cu66_packet_control.sv')=='20d761a514073e8e5212eb70861f843441bc8d8f32b81bf7f02925cd202ae5a2'
for gate in ['focused01','controls01','ooc01']:assert json.loads((o/gate/'result.json').read_text())['status'].startswith('PASS_')
timing={}
for label in ['baseline','candidate']:
 b=o/'ooc01'/label;t=(b/'console.log').read_text();wns=float(re.search(r'OOC_WNS (-?\d+\.\d+)',t).group(1));u=(b/'utilization.rpt').read_text();row=[x for x in u.splitlines()if '(top)'in x][0];numbers=[int(x.strip())for x in row.split('|')[3:-1]]
 timing[label]=dict(wns_ns=wns,total_lut=numbers[0],logic_lut=numbers[1],lutram=numbers[2],srl=numbers[3],ff=numbers[4],ramb36=numbers[5],ramb18=numbers[6],dsp=numbers[7])
 # Parser source in each completed synth job is the actual frozen binding.
 expected=(r/'fpga/experiments/cu66-v69/packet/cu66_packet_control.sv').read_text().replace('module cu66_packet_control (','module cu71_packet_presum (')if label=='baseline'else(d/'cu71_packet_presum.sv').read_text()
 assert (b/'parser.sv').read_text()==expected
assert (o/'focused01'/'cu71_packet_presum.sv').read_bytes()==(d/'cu71_packet_presum.sv').read_bytes()
assert (o/'controls01'/'candidate'/'cu71_packet_presum.sv').read_bytes()==(d/'cu71_packet_presum.sv').read_bytes()
(o/'summary.json').write_text(json.dumps(dict(timing=timing,scope='Unplaced exact-part OOC estimates only; no board/routed/hardware qualification',canonical_goldens='Parent-owned whole-system integration not asserted by parser component',c_check_handoff='Unavailable in this session; manual hash/content audit only'),indent=2)+'\n')
files=[d/'cu71_packet_presum.sv',d/'tb_prefix.sv',d/'derivation.json',d/'README.md',o/'summary.json',*sorted((r/'scripts/cu66-v71/packet-presum').glob('*.py'))]
for p in o.rglob('*'):
 if p.is_file()and p.stat().st_size and 'obj'not in p.parts and p.name!='handoff.json'and p.suffix in ['.json','.sv','.svh','.cpp','.py','.tcl','.sh','.log','.rpt','.dcp','.hex','.tsv','.cu66','.meta','.qmap','.vvp']:files.append(p)
files=sorted(set(files));artifacts=[dict(role='evidence'if'/evidence/'in str(p).replace('\\','/')else'source',path=str(p.relative_to(r)).replace('\\','/'),sha256=sha(p))for p in files]
checks=dict(focused=dict(status='pass',evidence=str((o/'focused01/result.json').relative_to(r)).replace('\\','/')),native_metadata_qmap_codes=dict(status='pass',evidence=str((o/'controls01/result.json').relative_to(r)).replace('\\','/')),unplaced_setup=dict(status='pass'if timing['candidate']['wns_ns']>=0 else'fail',evidence=str((o/'ooc01/candidate/setup-paths.rpt').relative_to(r)).replace('\\','/')),canonical_hud_pixel_integration=dict(status='incomplete',note='Parent-owned prospective full-system replay; no component claim'),routed_board_hardware=dict(status='incomplete',note='Not built or tested in this scope'))
(o/'handoff.json').write_text(json.dumps(dict(overall='INCOMPLETE',scope='Source-bound parser successor; unplaced component evidence only',artifacts=artifacts,checks=checks),indent=2)+'\n')
assert all((r/a['path']).is_file()and sha(r/a['path'])==a['sha256']for a in artifacts)
print(json.dumps(dict(timing=timing,artifacts=len(artifacts),overall='INCOMPLETE'),indent=2))
