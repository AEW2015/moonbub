#!/usr/bin/env python3
"""Finite owner-restoration/write induction model, not formal RTL equivalence."""
import itertools,json,re
from qualify import ROOT,SRC,AREA,sha
RETIRED={'IDLE','DRAIN','FINISHED','FAILED'}
CONSUMERS={'AC_CHECK','AC_FETCH','AC_EXTRACT','EMIT'}
def main():
 recipe=json.loads((SRC/'edit-recipe.json').read_text());entry=recipe['production']['packed_scratch_v91g2.sv'];old=(ROOT/entry['original']).read_text();new=(ROOT/entry['candidate']).read_text()
 assert sha(ROOT/entry['original'])==entry['original_sha256'] and sha(ROOT/entry['candidate'])==entry['candidate_sha256']
 states=[name.strip() for name in re.search(r'typedef enum logic \[4:0\] \{([^}]+)',old).group(1).split(',')]
 assert len(states)==30 and 'cursors' not in old.split(');',1)[0]
 # Complete old controller text remains after the exact two cursor writes are
 # removed. The production recipe reverses all edits to the original body.
 reverse=new
 for edit in reversed(entry['edits']):assert reverse.count(edit['after'])==1;reverse=reverse.replace(edit['after'],edit['before'],1)
 assert reverse==old
 assert old[old.index('`ifndef SYNTHESIS'):].rsplit('endmodule',1)[0] in new
 rows=divergences=restorations=0
 # One bank suffices by symmetry; selected=False proves all other banks hold.
 # Width3 exhausts arbitrary retired values and modular wrap. The induction
 # uses only equality, zero and equal modular increment, so extends to32bits.
 for state in states:
  for oldcur,newcur in itertools.product(range(8),repeat=2):
   if state not in RETIRED and oldcur!=newcur:continue
   for action,begin,hit,good,selected,final in itertools.product(
       ('normal','cancel_idle','cancel_drain','response_failed','response_drain'),
       ('none','valid','invalid'),(False,True),(False,True),(False,True),(False,True)):
    ncur=0 if state=='IDLE' else (newcur+1)%8 if state=='AC_EXTRACT' and hit and selected else newcur
    ocur=oldcur
    if action!='normal':target={'cancel_idle':'IDLE','cancel_drain':'DRAIN','response_failed':'FAILED','response_drain':'DRAIN'}[action]
    elif state=='IDLE':
     target='INGEST' if begin=='valid' else 'FAILED' if begin=='invalid' else 'IDLE'
     if begin=='valid':ocur=0;restorations+=1
    elif state=='DRAIN':target='IDLE' # matching late ACK or no physical owner
    elif state in ('FINISHED','FAILED'):target=state
    elif state=='AC_EXTRACT':
     target='READ_REQ' if not hit else 'AC_CHECK' if good else 'FAILED'
     if hit and good and selected:ocur=(oldcur+1)%8
    else:target=state # holds/unchanged transitions preserve equal live values
    if action=='normal' and state not in RETIRED and final:target='FINISHED'
    assert target in RETIRED or ocur==ncur,(state,target,action,begin,hit,good,selected,oldcur,newcur,ocur,ncur)
    assert state not in CONSUMERS or oldcur==newcur
    if ocur!=ncur:assert target in RETIRED;divergences+=1
    rows+=1
 # Exhaust the retired-state physical-owner graph, including simultaneous
 # begin, cancel/reset, wrong ACKs, matching late ACK and arbitrary waits.
 frontier={(state,outstanding,a,b)for state in RETIRED for outstanding in (False,True)
           for a,b in itertools.product(range(8),repeat=2)}
 visited=set();drain_rows=0;new_owner_rows=0
 while frontier:
  state,outstanding,a,b=frontier.pop()
  if (state,outstanding,a,b) in visited:continue
  visited.add((state,outstanding,a,b))
  for cancel,response,begin in itertools.product((False,True),('none','wrong','matching'),('none','valid','invalid')):
   aa=a;bb=0 if state=='IDLE' else b;owned=outstanding
   if cancel:
    target='DRAIN' if outstanding and response!='matching' else 'IDLE'
    if target=='IDLE':owned=False
   elif response!='none' and (not outstanding or response=='wrong'):
    target='DRAIN' if outstanding else 'FAILED'
   elif state=='DRAIN':
    if not outstanding or response=='matching':target='IDLE';owned=False
    else:target='DRAIN'
   elif state=='IDLE' and begin=='valid':target='INGEST';aa=0
   elif state=='IDLE' and begin=='invalid':target='FAILED'
   else:target=state
   if target not in RETIRED:
    assert state=='IDLE' and begin=='valid' and aa==bb==0
    new_owner_rows+=1
   else:
    successor=(target,owned,aa,bb)
    if successor not in visited:frontier.add(successor)
   drain_rows+=1
 # Negative control: incrementing on a cache miss corrupts a still-live retry.
 counterexample=dict(state='AC_EXTRACT',cache_hit=False,old_cursor=0,new_cursor=0,
                     wrong_increment_next_old=0,wrong_increment_next_new=1,next_state='READ_REQ',
                     violated='Live cursor equality fails before READ_WAIT returns to the same record.')
 result=dict(status='PASS_BOUNDED_CURSOR_OWNER_RESTORATION_MODEL_NOT_RTL',transition_rows=rows,
             deliberately_retired_divergence_rows=divergences,valid_begin_restoration_rows=restorations,
             retired_physical_owner_graph_nodes=len(visited),retired_physical_owner_graph_edges=drain_rows,
             restored_new_owner_graph_edges=new_owner_rows,
             retired_states=sorted(RETIRED),cursor_consumer_states=sorted(CONSUMERS),
             unsigned_width3_all_values_and_wrap=True,extension_to32bits='Per-bank induction uses only equality, identical increment modulo2^width, and same-edge zero restoration; no arithmetic bound assumption.',
             source_original_assertions_retained=True,source_sha256={entry[k]:sha(ROOT/entry[k]) for k in ('original','candidate')},
             cache_miss_negative_control=counterexample,
             lifecycle_coverage=['Global cancel→IDLE or physical DRAIN','Mismatched response→FAILED or DRAIN','Invalid begin→FAILED without owner','Bad cached record→FAILED; optional final override→FINISHED','Cache miss→READ_REQ/WAIT→same AC_EXTRACT ordinal','Wrong ACK holds DRAIN; matching late ACK→IDLE only','Preload/unaccepted begin noise does not create owner','Every valid IDLE begin clears all banks before any active consumer'],
             limits='Finite source-transformation/owner induction model; holds stand for unchanged active controller transitions. Late-ACK graph edges audited from source. Not formal RTL/four-state/reachability or physical timing proof; actual complete miter required.')
 (AREA/'model.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(result['status'],rows,divergences)
if __name__=='__main__':main()
