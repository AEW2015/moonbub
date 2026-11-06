"""Compare matched synthesis evidence; do not infer a routed timing benefit."""
from pathlib import Path
import hashlib,json,re
r=Path(__file__).resolve().parents[1];c=r/'fpga/candidates/cp23-reset-tags-20261105-v001'
p=r/'fpga/candidates/cp23-sdram-capture274p5-csa-20261105-v001'
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
files=lambda root:{f.relative_to(root).as_posix():sha(f)for f in root.rglob('*')if f.is_file()}
before=files(p/'inputs');after=files(c/'inputs');assert before.keys()==after.keys()
changed=[n for n in before if before[n]!=after[n]]
assert changed==['core/parents/cp23_envelope.sv'],changed
def read(folder):
 d=c/'evidence'/folder;s=(d/'reset-summary.txt').read_text();u=(d/'utilization.rpt').read_text()
 out={k:int(re.search(r'^'+k+r'=(\d+)$',s,re.M)[1])for k in ['job_reset_direct_loads','job_reset_direct_reset_pins','job_reset_direct_enable_pins','outer_tag_registers']}
 for key,label in [('LUT','Slice LUTs*'),('registers','Slice Registers'),('control_sets','Unique Control Sets')]:
  out[key]=int(re.search(r'\| '+re.escape(label)+r'\s*\|\s*(\d+)',u)[1])
 return out
b=read('reset-audit-baseline-synth01');a=read('reset-audit-synth01')
result=dict(scope='MATCHED_SYNTHESIS_ONLY',changed_sources=changed,before=b,after=a,delta={k:a[k]-b[k]for k in a},
 source_hashes=dict(before=before[changed[0]],after=after[changed[0]]),routed_timing_benefit_proven=False,hardware=False)
out=c/'evidence/reset-reduction-synthesis-summary.json';assert not out.exists();out.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
