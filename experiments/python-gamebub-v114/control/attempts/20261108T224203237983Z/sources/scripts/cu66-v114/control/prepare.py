#!/usr/bin/env python3
"""Pin the sole V114 top-body edit and byte-exact reverse; no RTL execution."""
import pathlib,hashlib,json,difflib
R=pathlib.Path(__file__).resolve().parents[3];S=R/'fpga/experiments/cu66-v114-control'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 a=R/'fpga/experiments/cu66-v110-fault/cs88_pipeline_v91k.sv';b=S/a.name;x=a.read_text();y=b.read_text();assert x.count(x)==1 and y.count(y)==1;assert y.replace(y,x,1)==x and x.replace(x,y,1)==y
 (S/'production.diff').write_text(''.join(difflib.unified_diff(x.splitlines(True),y.splitlines(True),fromfile=str(a.relative_to(R)),tofile=str(b.relative_to(R)))))
 j=dict(schema='v114-reserved-command-registered-peer-kill-top-v1',contract='IV114.1',module_ports_unchanged=True,child_instance_names_unchanged=True,original=str(a.relative_to(R)),original_sha256=sha(a),candidate=str(b.relative_to(R)),candidate_sha256=sha(b),alias='fpga/experiments/cu66-v91k/cs88_pipeline_v91k.sv',reverse_verified=True,edits=[dict(before=x,after=y,expected_occurrences=1)],old_exact_checker_changed=False)
 (S/'edit-recipe.json').write_text(json.dumps(j,indent=2)+'\n');print('PASS_V114_REVERSIBLE_TOP_RECIPE_NOT_RTL')
if __name__=='__main__':main()
