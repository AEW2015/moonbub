"""Select proven BRAM canonical hierarchy and pipelined exact-output painter."""
from pathlib import Path
import hashlib,json
r=Path(__file__).resolve().parents[2];d=r/'fpga/experiments/cu66-v71/system'
p=d/'cu71_system.sv';f=d/'cu71_system_bram.sv';assert not f.exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
codec=r/'fpga/experiments/cu66-v71/codec';m=json.loads((codec/'derivation.json').read_text())
for b in m['bindings']:assert sha(codec/b['candidate'])==b['candidate_sha256']
painter=r/'fpga/experiments/cu66-v71/display/cu71_painter_strip_pipe.sv'
assert sha(painter)=='9544e09f9fa22dac3332e0b46f07d38c29a2da1d702b9f0923c18de4d40c2f03'
s=p.read_text();changes={'module cu71_system #(':'module cu71_system_bram #(', '    cu70_receiver #(':'    cu71_receiver_bram #(', '    cu70_painter_strip painter(':'    cu71_painter_strip_pipe painter('}
for a,b in changes.items():assert s.count(a)==1,a;s=s.replace(a,b)
f.write_text(s,newline='\n')
(d/'derivation-bram.json').write_text(json.dumps(dict(parent_sha256=sha(p),candidate_sha256=sha(f),painter_sha256=sha(painter),codec_derivation_sha256=sha(codec/'derivation.json'),scope='Same transaction controls/ports; BRAM canonical rows and pipelined exact-output painter. Whole-system regression and board timing pending.'),indent=2)+'\n')
print(f)
