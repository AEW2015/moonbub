"""Correct isolated constraint coverage in a new source freeze; no hardware I/O."""
from pathlib import Path
import hashlib,json,shutil
r=Path(__file__).resolve().parents[1]
p=r/'fpga/exports/cpl1-timing-fsmcopy-source-20261105-v002'
a=r/'fpga/candidates/cp23-sdram-capture135-20261105-v001'
b=r/'fpga/candidates/cp23-sdram-capture135-20261105-v002'
b.mkdir(exist_ok=False);shutil.copytree(a/'inputs',b/'inputs')
for n in ['key.cp23.hex','quantizers.hex']:shutil.copyfile(a/n,b/n)
name='constraints/timing-cpl1-reviewed.tcl';original=(p/'inputs'/name).read_text()
common=original[original.index('# Preserve only asynchronous first-stage captures'):original.index('# Gray buses')]
target=b/'inputs'/name;s=target.read_text();assert s.count('# Gray buses')==1
target.write_text(s.replace('# Gray buses',common+'# Gray buses'),newline='\n')
# All unchanged common constraints must survive exactly, normalized only for EOL.
fixed=target.read_text();assert common in fixed
assert fixed[fixed.index('# Preserve only asynchronous first-stage captures'):]==original[original.index('# Preserve only asynchronous first-stage captures'):]
manifest=json.loads((a/'candidate.json').read_text())
manifest['status']='UNIMPLEMENTED_CORRECTED_CONSTRAINT_CANDIDATE_NO_BIT_NO_HARDWARE'
manifest['correction']='Restore all original synchronizer and QSPI bounds; v001 implementation remains invalid and rejected'
manifest['changes'][name]['candidate_sha256']=hashlib.sha256(target.read_bytes()).hexdigest()
(b/'candidate.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('CORRECTED_CONSTRAINT_CANDIDATE_PREPARED',b)
