#!/usr/bin/env python3
"""Pair every frozen V108 scratch state write with its same-edge busy class."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
OLD=ROOT/'fpga/experiments/cu66-v108-capacity/packed_scratch_v91g2.sv'
SRC=ROOT/'fpga/experiments/cu66-v110-busy';AREA=ROOT/'experiments/python-gamebub-v110/busy'
HASH='5c4e6fc665c81920a2f907bb87d34e78f0eac22a114f75633a1f1dc2ddd33676'
STATE_WRITE=re.compile(r'(?<![A-Za-z0-9_])state\s*<=\s*([^;]+);')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,j):p.write_text(json.dumps(j,indent=2,sort_keys=True)+'\n')
def classify(rhs):
 rhs=rhs.strip()
 if rhs in ('IDLE','FINISHED','FAILED'):return "1'b0"
 if rhs=='return_state':return '(return_state!=IDLE && return_state!=FINISHED && return_state!=FAILED)'
 if '?' in rhs:
  condition,choices=rhs.rsplit('?',1);yes,no=map(str.strip,choices.split(':'))
  if (yes,no)==('DRAIN','FAILED'):return '('+condition.strip()+')'
  assert (yes,no)==('RAW_FETCH','CLEAR_TILE'),rhs
 return "1'b1"
def main():
 assert sha(OLD)==HASH
 original=OLD.read_text();s=original;edits=[]
 def edit(before,after):
  nonlocal s
  assert s.count(before)==1,(before,s.count(before));s=s.replace(before,after,1)
  edits.append(dict(before=before,after=after,expected_occurrences=1))
 edit('    state_t state=IDLE, return_state;', '''    state_t state=IDLE, return_state;
    // Same-edge redundant quiescence predicate. Every original state write
    // below carries its own sibling update, including final override priority.
    logic busy_owned=0;''')
 edit('        busy=state!=IDLE && state!=FINISHED && state!=FAILED;','        busy=busy_owned;')
 # One whole-region edit avoids ambiguous repeated statements in the recipe.
 body=s[s.index('    always_ff @(posedge clk) begin'):s.index('`ifndef SYNTHESIS')]
 coverage=[]
 def pair(m):
  rhs=m.group(1).strip();predicate=classify(rhs)
  coverage.append(dict(ordinal=len(coverage),original_line=original[:original.index('    always_ff @(posedge clk) begin')].count('\n')+1+body[:m.start()].count('\n'),rhs=rhs,busy_rhs=predicate))
  # Nested blocks preserve existing unbraced if/else and case-item ownership.
  return 'begin '+m.group(0)+' busy_owned<='+predicate+'; end'
 paired=STATE_WRITE.sub(pair,body)
 edit(body,paired)
 assertion='''`ifndef SYNTHESIS
    logic busy_predicate_initialized=0;
    always_ff @(posedge clk)begin
        busy_predicate_initialized<=1;
        // Unconditional after the first clock, including reset, abort, DRAIN,
        // invalid cycles, error branches and final physical-response retirement.
        if(busy_predicate_initialized)
            assert(busy_owned==(state!=IDLE && state!=FINISHED && state!=FAILED))
                else $fatal(1,"scratch same-edge busy predicate mismatch");
    end
`endif
'''
 edit('endmodule',assertion+'endmodule')
 path=SRC/'packed_scratch_v91g2.sv';path.write_text(s)
 reverse=s
 for e in reversed(edits):assert reverse.count(e['after'])==1;reverse=reverse.replace(e['after'],e['before'],1)
 assert reverse==original
 assert len(STATE_WRITE.findall(original))==len(STATE_WRITE.findall(s))==len(re.findall(r'busy_owned\s*<=',s))==len(coverage)
 entry=dict(original=str(OLD.relative_to(ROOT)),original_sha256=HASH,candidate=str(path.relative_to(ROOT)),candidate_sha256=sha(path),edits=edits)
 write(SRC/'edit-recipe.json',dict(schema='v110-same-edge-scratch-busy-v1',status='PREPARED_NOT_RTL_QUALIFIED',production={path.name:entry},state_write_coverage=coverage,added_public_cycles=0,priority='Each state write is nested together with its busy write. Original branch/procedural order and final override retained.',initialization='busy_owned=0 paired with original state=IDLE; invariant unconditional after initialized clock.'))
 obs=json.loads((ROOT/'fpga/experiments/cu66-v106-scratch/adapter.json').read_text());adapters=[]
 for variant,source in [('original',OLD),('candidate',path)]:
  text=source.read_text();changes=[('module packed_scratch_v91g2 ','module observed_'+variant+' '),('\n);',obs['extra_ports']),('\nendmodule',obs['assignments']['candidate']+'\nendmodule')]
  for before,after in changes:assert text.count(before)==1;text=text.replace(before,after,1)
  dest=SRC/'verification'/('observed_'+variant+'.sv');dest.write_text(text)
  adapters.append(dict(source=str(source.relative_to(ROOT)),path=str(dest.relative_to(ROOT)),source_sha256=sha(source),sha256=sha(dest),renames=changes))
 previous=ROOT/'fpga/experiments/cu66-v109-bank/verification';fixtures={}
 for name in ('scratch_probe.sv','tb_scratch.cpp','historical_hazards.cpp','tb_bank.cpp'):
  p=previous/name;q=SRC/'verification'/name;q.write_bytes(p.read_bytes());fixtures[str(p.relative_to(ROOT))]=sha(p)
 write(SRC/'verification/adapters.json',dict(schema='v110-busy-lossless-complete-scratch-adapters-v1',adapters=adapters,unchanged_fixtures=fixtures,all_baseline_assertions_and_oracles_retained=True))
 write(AREA/'preparation.json',dict(status='PASS_PREPARATION_NOT_RTL',production_sha256=sha(path),original_sha256=HASH,recipe_sha256=sha(SRC/'edit-recipe.json'),assignments_paired=len(coverage),full_original_new_body=True,added_public_cycles=0))
 print('BUSY_PREPARED_NOT_RUN',len(coverage),sha(path))
if __name__=='__main__':main()
