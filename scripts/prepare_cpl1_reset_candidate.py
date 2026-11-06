"""Remove only two write-before-use envelope tag resets; never programs hardware."""
from pathlib import Path
import hashlib,json,shutil
r=Path(__file__).resolve().parents[1]
p=r/'fpga/candidates/cp23-sdram-capture274p5-csa-20261105-v001'
c=r/'fpga/candidates/cp23-reset-tags-20261105-v001';c.mkdir(exist_ok=False)
shutil.copytree(p/'inputs',c/'inputs')
for n in ['key.cp23.hex','quantizers.hex']:shutil.copyfile(p/n,c/n)
name='core/parents/cp23_envelope.sv';f=c/'inputs'/name
s=f.read_text();before=hashlib.sha256(f.read_bytes()).hexdigest()
assert s.count('bh<=0;hh<=0;')==2
s=s.replace('bh<=0;hh<=0;','')
for line in ['      if(count>=21&&count<37)bh[127-(count-21)*8-:8]<=in_byte;\n',
             '      if(count>=37&&count<53)hh[127-(count-37)*8-:8]<=in_byte;\n']:
    assert s.count(line)==1;s=s.replace(line,'')
marker=' always @(posedge clk)begin\n'
assert s.count(marker)==1
s=s.replace(marker,''' // Private expected tags are initialized on every accepted job. They are
 // consumed only after the complete header; reset/abort invalidate control.
 // A separate process avoids inferring reset as a hold-enable on tag storage.
 always @(posedge clk)begin
  if(state==IDLE&&start_valid&&start_ready)begin bh<=0;hh<=0;end
  else if(state==HEADER&&in_valid&&in_ready&&in_last==(count==total-1))begin
   if(count>=21&&count<37)bh[127-(count-21)*8-:8]<=in_byte;
   if(count>=37&&count<53)hh[127-(count-37)*8-:8]<=in_byte;
  end
 end
'''+marker)
f.write_text(s,newline='\n')
m=json.loads((p/'candidate.json').read_text())
m['status']='RESET_TAGS_PENDING_EQUIVALENCE_FULL_MODEL_AND_ROUTING_NO_BIT'
m['changes'][name]=dict(parent_sha256=before,candidate_sha256=hashlib.sha256(f.read_bytes()).hexdigest())
m['reset_change']='256 private expected-tag bits: separate write-before-use storage; control/recovery reset unchanged'
(c/'candidate.json').write_text(json.dumps(m,indent=2)+'\n');print(c)
