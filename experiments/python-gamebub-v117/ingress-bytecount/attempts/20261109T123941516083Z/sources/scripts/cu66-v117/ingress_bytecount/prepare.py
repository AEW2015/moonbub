#!/usr/bin/env python3
"""Preserve exact ceil-byte predicate while removing its carry from commit CE."""
from pathlib import Path
import hashlib,json,re,shutil
R=Path(__file__).resolve().parents[3];S=R/'fpga/experiments/cu66-v117-ingress-bytecount';V=S/'verification';BASE=R/'fpga/experiments/cu66-v117-ingress'
CAUSE=R/'experiments/python-gamebub-v117/throughput-study/native/20261109T121229166037Z/receipt.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return str(p.relative_to(R))
def derive(p,q,edits):
 t=p.read_text()
 for e in edits:assert t.count(e['before'])==1,e['before'][:80];t=t.replace(e['before'],e['after'],1)
 q.write_text(t);return dict(original=rel(p),original_sha256=sha(p),candidate=rel(q),candidate_sha256=sha(q),edits=edits)
new='''    // V117 bytecount: a full32 algebraic comparison, not a narrowed byte
    // counter or a changed private ceil view. u=floor(bits/8) fits29 bits;
    // u+frac==L iff u==(L-frac) modulo32, including L==0 and max bits.
    logic [31:0] active_length_minus7;
    logic descriptor_bytecount_bad;
    assign descriptor_bytecount_bad=descriptor_bits[2:0]==0 ?
        (descriptor_bits>>3)!=active_length_minus6 :
        (descriptor_bits>>3)!=active_length_minus7;
`ifndef SYNTHESIS
    always_ff @(posedge clk)if(!cancelled&&!context_failure&&!(context_active&&ctx_done)&&state==DESCRIPTOR)begin
        assert(active_length_minus7==active_length-7)
            else $fatal(1,"V117 bytecount selected minus7 owner/wrap mismatch");
        assert(descriptor_bytes==((descriptor_bits>>3)+32'(descriptor_bits[2:0]!=0)))
            else $fatal(1,"V117 bytecount original private ceil view changed");
        assert(descriptor_bytecount_bad==(descriptor_bytes!=active_length_minus6))
            else $fatal(1,"V117 bytecount algebra changed original full32 ceil predicate");
    end
`endif
'''
edits=[dict(before='    function automatic logic [31:0] cached32(input integer at);',after=new+'\n    function automatic logic [31:0] cached32(input integer at);'),
 dict(before='                    active_length_minus6<=lengths[band]-6;',after='                    active_length_minus6<=lengths[band]-6;\n                    active_length_minus7<=lengths[band]-7;'),
 dict(before='                        if(descriptor_bytes!=active_length_minus6 || descriptor_bits>packet_bit_limit) fail_packet(4);',after='                        if(descriptor_bytecount_bad || descriptor_bits>packet_bit_limit) fail_packet(4);')]
production=[derive(BASE/'br88_packet_ingress_sync_v91h.sv',S/'br88_packet_ingress_sync_v91h.sv',edits)]
for b in re.findall(r'`ifndef SYNTHESIS(.*?)`endif',(BASE/'br88_packet_ingress_sync_v91h.sv').read_text(),re.S):assert b in(S/'br88_packet_ingress_sync_v91h.sv').read_text()
for p in(BASE/'verification').iterdir():
 if p.is_file():shutil.copyfile(p,V/p.name)
adapters=[]
adapters.append(derive(BASE/'br88_packet_ingress_sync_v91h.sv',V/'br88_packet_ingress_sync_v91h_reference.sv',[dict(before='module br88_packet_ingress_sync_v91h #(',after='module br88_packet_ingress_sync_v91h_reference #(')]))
adapters.append(derive(BASE/'verification/tb_extents.cpp',V/'extents_base.cpp',[dict(before='int main(int argc,char**argv)',after='int inherited_extents_main(int argc,char**argv)')]))
manifest=dict(schema='v117-full32-ceil-bytecount-equality-cut-v1',production=production,adapters=adapters,unchanged_verification={rel(p):sha(p)for p in(BASE/'verification').iterdir()if p.is_file()and p.name!='br88_packet_ingress_sync_v91h_reference.sv'},baseline_selector='experiments/python-gamebub-v117/ingress/results.json',actual_routed_cause=rel(CAUSE),declared_public_cycle_delta=0,private_descriptor_bytes_expression_unchanged=True)
(S/'edit-recipes.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n');print('V117_BYTECOUNT_DRAFT',production[0]['candidate_sha256'])
