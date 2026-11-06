"""Add only the directed-tested SHA write reservation to the reset-tag candidate."""
from pathlib import Path
import hashlib,json,shutil
r=Path(__file__).resolve().parents[1];p=r/'fpga/candidates/cp23-reset-tags-20261105-v001'
e=r/'fpga/experiments/sha-csa-byte-reservation-20261105-v001'
assert json.loads((e/'result.json').read_text())['status']=='PASS_DIRECTED_SHA_SUITE_ONLY'
assert json.loads((e/'flush-cancel01/result.json').read_text())['status']=='PASS_TARGETED_RESERVATION_CANCEL'
c=r/'fpga/candidates/cp23-reset-tags-bytewrite-20261105-v001';c.mkdir(exist_ok=False)
shutil.copytree(p/'inputs',c/'inputs')
for n in ['key.cp23.hex','quantizers.hex']:shutil.copyfile(p/n,c/n)
name='core/compute/sha256_bytes.sv';f=c/'inputs'/name
before=hashlib.sha256(f.read_bytes()).hexdigest();shutil.copyfile(e/'sha256_bytes.sv',f)
m=json.loads((p/'candidate.json').read_text());m['status']='RESET_TAGS_SHA_BYTE_RESERVATION_PENDING_FULL_MODELS_AND_ROUTING_NO_BIT'
m['changes'][name]=dict(parent_sha256=before,candidate_sha256=hashlib.sha256(f.read_bytes()).hexdigest())
m['sha_byte_reservation']=dict(sha_suite=str(e/'result.json'),cancel_suite=str(e/'flush-cancel01/result.json'),
 latency_delta='One flush cycle per 64-byte SHA compression block; no added stream-level ACK or protocol change')
(c/'candidate.json').write_text(json.dumps(m,indent=2)+'\n');print(c)
