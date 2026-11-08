# Historical initial-template generator. Reproduce in an isolated copy only.
from pathlib import Path
import difflib,hashlib,json
root=Path(__file__).resolve().parents[3];dst=root/'fpga/experiments/cu66-v107-scale';hdr=root/'fpga/experiments/cu66-v107-header'
base=(hdr/'cs88_admission_v91i2a.sv').read_text();assert hashlib.sha256(base.encode()).hexdigest()=='7a417f9a647e77571e6d31d6780412bc62dda4bdc1ef879017266694df9763a9'
helper='''\n// Isolated common-clock TDP scale storage; no reset/initialization promise.
module cu66_scale_tdp_v107 (
    input wire clk,input wire a_write,input wire [10:0] a_addr,input wire [1:0] a_data,
    input wire b_write,b_read,input wire [10:0] b_addr,input wire [1:0] b_data,
    output reg [1:0] b_q
);
    (* ram_style="block" *) reg [1:0] words [0:1349];
    // Suppress only same-address simultaneous A writes: original Q_FILL wins.
    wire a_commit=a_write && !(b_write && a_addr==b_addr);
    always @(posedge clk)if(a_commit) words[a_addr]<=a_data;
    // A B-write must hold the previous lookup output (NO_CHANGE semantics).
    always @(posedge clk)begin
        if(b_write) words[b_addr]<=b_data;
        else if(b_read) b_q<=words[b_addr];
    end
endmodule
'''
newdecl='''    // V107: external writes on A, Q_FILL/registered lookup on B.
    wire scale_live=!reset&&!start&&!abort_packet;
    wire scale_fill=scale_live&&state==Q_FILL;
    wire scale_lookup=scale_live&&lookup_req&&state==FINISHED;
    cu66_scale_tdp_v107 scale_store(.clk(clk),.a_write(scale_live&&cache_write),
        .a_addr(cache_index),.a_data(cache_data),.b_write(scale_fill),.b_read(scale_lookup),
        .b_addr(scale_fill?q_runs[10:0]:lookup_cell),.b_data(q_value),.b_q(lookup_scale));'''
changes=[('    logic [1:0] scales [0:1349];',newdecl),('        if(cache_write&&!reset&&!start&&!abort_packet)scales[cache_index]<=cache_data;\n',''),('lookup_mode<=modes[lookup_tile];lookup_scale<=scales[lookup_cell];','lookup_mode<=modes[lookup_tile];'),('scales[q_runs[10:0]]<=q_value;q_runs<=q_runs+1;','q_runs<=q_runs+1;')]
def edit(s):
 for old,new in changes:assert s.count(old)==1,old;s=s.replace(old,new,1)
 return s+helper
candidate=edit(base);(dst/'cs88_admission_v91i2a.sv').write_text(candidate)
# Same instrumented HEADER body on BOTH sides, with unchanged public ports.
instrumented=(hdr/'admission_candidate.sv').read_text()
(dst/'admission_original.sv').write_text(instrumented.replace('module admission_candidate (','module admission_original (',1))
(dst/'admission_candidate.sv').write_text(edit(instrumented))
for file in ['admission_probe.sv','ports.json']:(dst/file).write_bytes((hdr/file).read_bytes())
adapter=json.loads((hdr/'adapter.json').read_text());adapter['assignments']['original']=adapter['assignments']['candidate'];(dst/'adapter.json').write_text(json.dumps(adapter,indent=2,sort_keys=True)+'\n')
recipe=dict(baseline=str((hdr/'cs88_admission_v91i2a.sv').relative_to(root)),baseline_sha256=hashlib.sha256(base.encode()).hexdigest(),candidate=str((dst/'cs88_admission_v91i2a.sv').relative_to(root)),candidate_sha256=hashlib.sha256(candidate.encode()).hexdigest(),changes=[dict(start=i,end=j,old=base[i:j],new=candidate[k:l]) for tag,i,j,k,l in difflib.SequenceMatcher(None,base,candidate,autojunk=False).get_opcodes() if tag!='equal'],note='Initial inferred template; physical A/B modes and UNISIM collisions not yet qualified.')
(dst/'edit-recipe.json').write_text(json.dumps(recipe,indent=2,sort_keys=True)+'\n')
# Historical bench uses invariant-consistent prepared header states; both old
# and new bodies now contain HEADER caches, so bind both private invariants.
s=(hdr/'tb_admission.cpp').read_text()
import re
for name in ('header_mode_start','header_residual_start','header_hud_tail','header_residual_end','header_packet_total'):
 s=re.sub(r'QNEW\('+name+r'\)=([^;]+);',r'QBOTH('+name+r',\1);',s)
(dst/'tb_admission.cpp').write_text(s)
print('PREPARED_INFERRED',recipe['candidate_sha256'])
