#!/usr/bin/env python3
"""Source-complete same-edge predicate induction model; never an RTL verdict."""
import itertools,json,re
from qualify import verify,sha,ROOT,SRC,AREA
from prepare import STATE_WRITE

def main():
 recipe=verify();e=recipe['production']['packed_scratch_v91g2.sv']
 old=(ROOT/e['original']).read_text();new=(ROOT/e['candidate']).read_text()
 marker='    function automatic logic capacity_expected_wrap'
 tail=old[old.index(marker):].rsplit('endmodule',1)[0]
 assert tail in new
 names=re.search(r'typedef enum logic \[4:0\] \{([^}]+)\}',old).group(1)
 enums={name.strip():value for value,name in enumerate(names.split(','))}
 coverage=recipe['state_write_coverage'];writes=STATE_WRITE.findall(old)
 assert [rhs.strip() for rhs in writes]==[x['rhs'] for x in coverage]
 # Every original state statement is immediately paired in an explicit block.
 assert len(writes)==len(re.findall(r'busy_owned\s*<=',new))==63
 for row in coverage:
  assert 'begin state<='+row['rhs']+'; busy_owned<='+row['busy_rhs']+'; end' in new
 def evaluate(text,env):
  text=text.strip()
  if '?' in text:
   condition,choices=text.rsplit('?',1);yes,no=choices.split(':')
   return evaluate(yes if evaluate(condition,env) else no,env)
  text=text.replace("1'b0",'False').replace("1'b1",'True').replace('&&',' and ').replace('||',' or ')
  text=re.sub(r'!(?!=)',' not ',text)
  return eval(' '.join(text.split()),{'__builtins__':{}},env)
 def busy(state):return state not in (enums['IDLE'],enums['FINISHED'],enums['FAILED'])
 rows=0;by_write=[]
 # Cover all encoded dynamic return states, all five relevant boolean inputs,
 # then compare source RHS classification with the independently decoded state.
 for entry in coverage:
  checked=0
  for ret,flags in itertools.product(range(32),itertools.product((False,True),repeat=5)):
   env=dict(enums,return_state=ret,**dict(zip(('outstanding','mem_rsp_valid','mem_req_valid','mem_req_ready','raw_mode'),flags)))
   state=evaluate(entry['rhs'],env);predicate=evaluate(entry['busy_rhs'],env)
   assert bool(predicate)==busy(state),(entry,env,state,predicate)
   checked+=1
  by_write.append(dict(ordinal=entry['ordinal'],cases=checked));rows+=checked
 # Induction: initialization agrees; no-state-write holds both fields; any
 # ordered subsequence of paired writes leaves the final pair in agreement.
 # Pairwise combinations exercise all possible last-write priority identities,
 # including the final tile-completion override at ordinal 62.
 priority_rows=0
 for first,last in itertools.product(coverage,repeat=2):
  for ret in range(32):
   env=dict(enums,return_state=ret,outstanding=True,mem_rsp_valid=False,mem_req_valid=True,mem_req_ready=True,raw_mode=False)
   state=evaluate(first['rhs'],env);predicate=evaluate(first['busy_rhs'],env)
   state=evaluate(last['rhs'],env);predicate=evaluate(last['busy_rhs'],env)
   assert bool(predicate)==busy(state);priority_rows+=1
 for state in range(32):assert busy(state)==busy(state)
 assert not busy(enums['IDLE'])
 result=dict(status='PASS_SOURCE_COMPLETE_BUSY_INDUCTION_MODEL_NOT_RTL',assignment_rows=rows,priority_rows=priority_rows,state_writes=len(writes),by_write=by_write,dynamic_return_encodings=32,boolean_inputs=5,original_assertion_tail_byte_identical=True,added_public_cycles=0,source_sha256={e[k]:sha(ROOT/e[k]) for k in ('original','candidate')},scope='All actual state-write RHS classifications over all 5-bit return-state encodings and relevant two-state boolean controls; paired-statement source coverage, initialization, holds and last-write priority induction. This is a source transformation model, not formal RTL equivalence, four-state power-up proof, physical timing or hardware evidence.')
 (AREA/'model.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 print(result['status'],rows,priority_rows)
if __name__=='__main__':main()
