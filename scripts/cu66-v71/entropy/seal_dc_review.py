"""Seal independent DC-stage source, focused proofs and matched clean OOC."""
from pathlib import Path
import hashlib,json,re
r=Path(__file__).resolve().parents[3];d=r/'fpga/experiments/cu66-v71/entropy-dcpipe'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=Path('C:/vtmp/mbdc1106b');new=Path('C:/vtmp/mbdc1106a')
def metrics(p):
 e=json.loads((p/'execution.json').read_text());assert e['returncode']==0
 log=(p/'vivado.log').read_text();assert not re.search(r'^ERROR:',log,re.M)
 text=(p/'timing.rpt').read_text();row=re.search(r'\n\s+(-?[\d.]+)\s+(-?[\d.]+)\s+\d+\s+\d+\s+(-?[\d.]+)\s+(-?[\d.]+)\s+\d+\s+\d+\s+(-?[\d.]+)',text)
 assert row
 utilization=(p/'utilization.rpt').read_text();u=next(x for x in utilization.splitlines()if '(top)'in x)
 fields=[x.strip()for x in u.split('|')[1:-1]]
 return dict(wns_ns=float(row[1]),whs_ns=float(row[3]),wpws_ns=float(row[5]),luts=int(fields[2]),ffs=int(fields[6]),ramb36=int(fields[7]),ramb18=int(fields[8]),dsp=int(fields[9]),native_errors=0,scope='Unplaced OOC100MHz max1ns/min0ns input/output budget; no board/route/hold signoff')
a=(old/'executed.tcl').read_text().replace('cu71_ab38_decoder_headerpipe_v5','TOP')
b=(new/'executed.tcl').read_text().replace('cu71_ab38_decoder_dcpipe_v6','TOP')
assert a==b,'Matched Tcl differs beyond exact source/top name'
for f in[d/'evidence/independent-review01/result.json',d/'evidence/reset-native01/result.json']:assert json.loads(f.read_text())['status'].startswith('PASS')
artifacts={}
for base in[old,new,d/'evidence/independent-review01',d/'evidence/reset-native01']:
 for p in base.rglob('*'):
  if p.is_file()and '.Xil'not in p.parts and 'tmp'not in p.parts:
   artifacts[str(p)]=sha(p)
sources=[d/'cu71_ab38_decoder_dcpipe_v6.sv',r/'fpga/experiments/cu66-v71/entropy-headerpipe/cu71_ab38_decoder_headerpipe_v5.sv']
parent_text=sources[1].read_text();candidate_text=sources[0].read_text()
old_body=re.search(r'                DC_VALUE:begin.*?(?=                DC_COMMIT:begin)',parent_text,re.S).group()
new_body=re.search(r'                DC_VALUE:begin.*?(?=                DC_COMMIT:begin)',candidate_text,re.S).group()
reverse=candidate_text.replace('module cu71_ab38_decoder_dcpipe_v6 #(','module cu71_ab38_decoder_headerpipe_v5 #(').replace('PARAM_VALIDATE, HEADER_SUM, HEADER_INSTALL, DC_CHECK','PARAM_VALIDATE, HEADER_SUM, HEADER_INSTALL').replace('    // Private signed32-bit payload; DC_VALUE always writes before DC_CHECK.\n    logic signed [31:0] dc_prediction;\n','').replace(new_body,old_body)
assert reverse==parent_text,'Unexpected source change outside module, enum, private register, DC-state split'
out=dict(status='PASS_INDEPENDENT_FOCUSED_AND_MATCHED_UNPLACED_OOC',sources={str(p.relative_to(r)):sha(p)for p in sources},parent_ooc=metrics(old),candidate_ooc=metrics(new),matched_tcl_except_top_source=True,artifacts=artifacts,
 findings=['Original32-bit signed wrapped sum, signed inclusive bounds[-2048,2048] and16-bit storage preserved; unconstrained algebra SAT and actual-parent differential2048cases pass.',
 'Appended DC_CHECK56 adds one workcycle per reached nonraw DC block; error12 is correspondingly deferred one cycle. New abort/reset opportunity has priority and cannot commit the staged value.',
 'New32-bit payload intentionally unreset and fenced by state. Direct reset56 with dirty7fffffff retains352 probability bytes, reset beats abort, and subsequent actual full packet/golden retry passes in directed and stress campaigns.',
 'No probability update, raw path, suffix, wire, modulo, scaling or reset fanout change. Existing parent state debug IDs preserved;56 appended.',
 'Existing parent OOC default min1 IO was not used as matched hold comparator: both new runs use explicit max1/min0. Native warnings about declaration ordering and unspecified OOC HD.CLK_SRC retained.',
 'Full1371 packet campaign is root-owned and not duplicated or implied by focused qualification. No hardware or board release selection.'],hardware=False,routed_timing=False)
p=d/'qualification-independent-v001.json';assert not p.exists();p.write_text(json.dumps(out,indent=2)+'\n');print(p,sha(p));print(json.dumps({k:out[k]for k in('parent_ooc','candidate_ooc')},indent=2))
