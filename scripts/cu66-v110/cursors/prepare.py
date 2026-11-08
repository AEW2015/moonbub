#!/usr/bin/env python3
"""Separate private cursor payload writes from global controller validation."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
OLD=ROOT/'fpga/experiments/cu66-v110-busy/packed_scratch_v91g2.sv'
SRC=ROOT/'fpga/experiments/cu66-v110-cursors';AREA=ROOT/'experiments/python-gamebub-v110/cursors'
HASH='e9a70463b78c0afbbded2358fd9b4ca7f600c695d9251b0cf3d202a74ad21478'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,value):p.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
def main():
 assert sha(OLD)==HASH;s=OLD.read_text();edits=[]
 def edit(before,after):
  nonlocal s
  assert s.count(before)==1;s=s.replace(before,after,1);edits.append(dict(before=before,after=after,expected_occurrences=1))
 edit('                        for(integer b=1;b<=3;b=b+1) cursors[b]<=0;','                        // Private cursor payload clears on every original IDLE edge below.')
 edit('                            cursors[read_band]<=cursors[read_band]+1; head_valid[read_band]<=1;', '                            head_valid[read_band]<=1;')
 edit('    always_ff @(posedge clk) begin\n        // A reset is cancellation, not permission to discard an accepted write.', '''    // Cursor payload is unowned in IDLE/DRAIN/FINISHED/FAILED. Every new
    // owner enters through an IDLE edge, restoring all cursors before use.
    // A cache miss must hold: the matching read returns to this same ordinal.
    // Malformed/cancelled hit increments retire with the owner and cannot
    // change any later live use. Public/controller/head updates stay guarded.
    for(genvar cursor_bank=1;cursor_bank<=3;cursor_bank=cursor_bank+1)begin: cursor_payload
        always_ff @(posedge clk)begin
            if(state==IDLE)cursors[cursor_bank]<=0;
            else if(state==AC_EXTRACT && read_band==2'(cursor_bank) &&
                cache_valid[read_segment] &&
                cache_address[read_segment]==18'(read_address & 32'hfffffff0))
                cursors[cursor_bank]<=cursors[cursor_bank]+1;
        end
    end

    always_ff @(posedge clk) begin
        // A reset is cancellation, not permission to discard an accepted write.''')
 path=SRC/'packed_scratch_v91g2.sv';path.write_text(s);reverse=s
 for edit in reversed(edits):assert reverse.count(edit['after'])==1;reverse=reverse.replace(edit['after'],edit['before'],1)
 assert reverse==OLD.read_text()
 entry=dict(original=str(OLD.relative_to(ROOT)),original_sha256=HASH,candidate=str(path.relative_to(ROOT)),candidate_sha256=sha(path),edits=edits)
 write(SRC/'edit-recipe.json',dict(schema='v110-private-cursor-owner-scope-v1',status='PREPARED_NOT_RTL_QUALIFIED',production={path.name:entry},added_public_cycles=0,scope='Every production public/invalid/debug/memory output and noncursor stored state exact; cursors equal whenever either DUT has a live owner. Only retired/unowned cursor payload may differ. Cache misses hold. No all-private-state equivalence claim.'))
 observation=json.loads((ROOT/'fpga/experiments/cu66-v106-scratch/adapter.json').read_text());adapters=[]
 for variant,source in [('original',OLD),('candidate',path)]:
  text=source.read_text();changes=[('module packed_scratch_v91g2 ','module observed_'+variant+' '),('\n);',observation['extra_ports']),('\nendmodule',observation['assignments']['candidate']+'\nendmodule')]
  for before,after in changes:assert text.count(before)==1;text=text.replace(before,after,1)
  dest=SRC/'verification'/('observed_'+variant+'.sv');dest.write_text(text);adapters.append(dict(source=str(source.relative_to(ROOT)),path=str(dest.relative_to(ROOT)),source_sha256=sha(source),sha256=sha(dest),renames=changes))
 previous=ROOT/'fpga/experiments/cu66-v110-busy/verification';fixtures={}
 for name in ('tb_scratch.cpp','historical_hazards.cpp','tb_bank.cpp'):
  p=previous/name;(SRC/'verification'/name).write_bytes(p.read_bytes());fixtures[str(p.relative_to(ROOT))]=sha(p)
 probe=(previous/'scratch_probe.sv').read_text();probe_edits=[
  ('    output logic mismatch,','    output logic mismatch,\n    output logic verify_cursor_equal, verify_cursor_owner_live,\n    output logic [95:0] verify_reference_cursors,'),
  ('        (old_verify_cursors==verify_cursors) &&','        (!(old_cursor_live || new_cursor_live) || old_verify_cursors==verify_cursors) &&'),
  ('    assign mismatch=!', '''    logic old_cursor_live,new_cursor_live;
    assign old_cursor_live=old_debug_state!=0 && old_debug_state!=23 && old_debug_state!=24 && old_debug_state!=25;
    assign new_cursor_live=debug_state!=0 && debug_state!=23 && debug_state!=24 && debug_state!=25;
    assign verify_cursor_equal=old_verify_cursors==verify_cursors;
    assign verify_cursor_owner_live=old_cursor_live || new_cursor_live;
    assign verify_reference_cursors=old_verify_cursors;
    // States and every noncursor observation remain equal before owner masking.
    always_ff @(posedge clk)begin
        assert(old_debug_state==debug_state)else $fatal(1,"cursor state mismatch before owner scope");
        assert(old_verify_positions==verify_positions && old_verify_head_positions==verify_head_positions &&
            old_verify_read_position==verify_read_position)else $fatal(1,"cursor changed noncursor raw payload");
    end
    assign mismatch=!''')]
 for before,after in probe_edits:assert probe.count(before)==1;probe=probe.replace(before,after,1)
 (SRC/'verification/scratch_probe.sv').write_text(probe)
 inherited=(previous/'tb_bank.cpp').read_text();assert inherited.count('int main(')==1
 (SRC/'verification/inherited_bank.cpp').write_text(inherited.replace('int main(','int inherited_bank_main(',1))
 write(SRC/'verification/adapters.json',dict(schema='v110-cursor-complete-scratch-owner-scoped-adapters-v1',adapters=adapters,unchanged_fixtures=fixtures,probe_original=str((previous/'scratch_probe.sv').relative_to(ROOT)),probe_original_sha256=sha(previous/'scratch_probe.sv'),probe_edits=probe_edits,original_assertions_and_oracles_retained=True,only_new_equivalence_exception='Raw verify_cursors equality is scoped by OR of both raw-state live predicates; raw states always compared before masking. Actual public ports, invalid values and every other raw observation retain equality.'))
 write(AREA/'preparation.json',dict(status='PASS_PREPARATION_NOT_RTL',production_sha256=sha(path),original_sha256=HASH,recipe_sha256=sha(SRC/'edit-recipe.json'),added_public_cycles=0,all_private_state_exact=False,all_public_invalid_debug_memory_exact_required=True,live_cursor_equality_required=True))
 print('CURSORS_PREPARED_NOT_RUN',sha(path))
if __name__=='__main__':main()
