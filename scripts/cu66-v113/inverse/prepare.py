#!/usr/bin/env python3
"""Record and verify exact reversible source substitution; no simulation."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
SRC=ROOT/'fpga/experiments/cu66-v113-inverse'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 old=ROOT/'fpga/experiments/cu66-v110-fault/cu66_inverse_stream_v91j.sv';new=SRC/old.name
 a=old.read_text();b=new.read_text();marker='    task automatic fail';ap,at=a.split(marker,1);bp,bt=b.split('    logic [63:0] count_commits',1)
 before='M_IDCT_WAIT=3, M_EMIT=4;';after='M_IDCT_WAIT=3;';assert ap.replace(before,after)==bp
 edits=[dict(before=before,after=after),dict(before=marker+at,after='    logic [63:0] count_commits'+bt)]
 s=a
 for e in edits:assert s.count(e['before'])==1;s=s.replace(e['before'],e['after'],1)
 assert s==b
 for e in reversed(edits):assert s.count(e['after'])==1;s=s.replace(e['after'],e['before'],1)
 assert s==a
 recipe=dict(schema='v113-inverse-owned-accept-two-result-v1',contract='IV113.1',module_interface_unchanged=True,alias='fpga/experiments/cu66-v91j/cu66_inverse_stream_v91j.sv',original=str(old.relative_to(ROOT)),original_sha256=sha(old),candidate=str(new.relative_to(ROOT)),candidate_sha256=sha(new),edits=edits,reverse_verified=True,old_exact_checker_changed=False,source_sha256={str(p.relative_to(ROOT)):sha(p) for p in [old,new,SRC/'tb_inverse.cpp',SRC/'tb_throughput.cpp',Path(__file__)]})
 (SRC/'edit-recipe.json').write_text(json.dumps(recipe,indent=2)+'\n');print('PASS_REVERSIBLE_RECIPE_NOT_RTL')
if __name__=='__main__':main()
