"""Mechanical allowed-delta proof; behavioral cycles are proved separately."""
from pathlib import Path
import hashlib,json,re
r=Path(__file__).resolve().parents[3];d=r/'fpga/experiments/cu66-v71/hash';parent=r/'fpga/experiments/cu66-v69/hash/cu66_sha256_bytes.sv';candidate=d/'cu71_sha256_bytes_lookahead.sv';old=parent.read_text();new=candidate.read_text();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
restored=new.replace('module cu71_sha256_bytes_lookahead #(','module cu66_sha256_bytes #(').replace('schedule_word, future_word, temp1, temp2','schedule_word, temp1, temp2')
for name in('add4_mod','add5_mod'):
    pattern=r'    function automatic logic \[31:0\] '+name+r'\(.*?    endfunction\n'
    restored,n=re.subn(pattern,'',restored,flags=re.S);assert n==1,name
start=restored.index('        future_word=add4_mod(');end=restored.index('        temp2=',start)
old_start=old.index('        if(round_index>=16)\n');old_end=old.index('        temp2=',old_start)
restored=restored[:start]+old[old_start:old_end]+restored[end:]
restored=restored.replace('if(round_index<48)words[process_bank][ring_index]<=future_word;','if(round_index>=16)words[process_bank][ring_index]<=schedule_word;')
normalize=lambda s:re.sub(r'\s+','',re.sub(r'/\*.*?\*/|//[^\n]*','',s,flags=re.S))
assert normalize(restored)==normalize(old),'Unexpected public/state/control/array-reset delta'
report=dict(status='PASS_ONLY_LOOKAHEAD_SCHEDULE_AND_MOD32_CSA_DELTAS',parent_sha256=sha(parent),candidate_sha256=sha(candidate),allowed_changes=['Module name/comments; add4/add5 carry-save combinational helpers','Expansion W[t] during round>=16 replaced by W[t+16] lookahead during rounds0..47','Compression consumes registered ring word every round; temp1 uses modulo32 CSA sum5'],unchanged='All public ports, FSMs, handshakes, byte filling/padding, bank ownership, error/abort/reset handling, digest updates and counters remain identical after reversing only the listed arithmetic deltas.',word_array_reset_added=False,round_cycles_per_block=64,induction='At roundt ring[i] containsW[t]. Live ring offsets14/9/1/i provideW[t+14],W[t+9],W[t+1],W[t], so writeW[t+16] after W[t] is consumed. Initial16words are fully filled before bank_full permits compression; stop lookahead after round47.',scope='Structural allowed-delta proof plus mathematical schedule invariant, not routed timing or standalone formal verification. Actual RTL golden/cycle comparisons are separate.',hardware=False)
(d/'source-proof.json').write_text(json.dumps(report,indent=2)+'\n');print(report['status'],sha(d/'source-proof.json'))
