#!/usr/bin/env python3
"""Prepare the exact original-edge V111 header arithmetic pipeline and adapters."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
SRC=ROOT/'fpga/experiments/cu66-v111-header';V=SRC/'verification';AREA=ROOT/'experiments/python-gamebub-v111/header'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def main():
 old=ROOT/'fpga/experiments/cu66-v110-count-domain/br88_packet_ingress_sync_v91h.sv';s=old.read_text()
 assert sha(old)=='38c524b52d40c1a7764ac7219582af974b8f973d94d8cff03f23c7088b2bcf28'
 pipeline='''    // V111_HEADER_PIPELINE_BEGIN: private payload, never a new owner/enable.
    // Length bytes 14..29 are stable before sixteen further header reads.
    // No reset or cancel fanout; consume only at the original HEADER edge.
    logic [32:0] header_length_pair01_s1, header_length_pair23_s1;
    logic [33:0] header_length_target_s1, header_length_target_s2;
    logic [33:0] header_length_total_s2;
    logic header_length_match_s3;
    always_ff @(posedge clk)begin
        header_length_pair01_s1<={1'b0,cached32(14)}+{1'b0,cached32(18)};
        header_length_pair23_s1<={1'b0,cached32(22)}+{1'b0,cached32(26)};
        header_length_target_s1<={2'd0,size_bytes}-34'd46;
        header_length_total_s2<={1'b0,header_length_pair01_s1}+{1'b0,header_length_pair23_s1};
        header_length_target_s2<=header_length_target_s1;
        header_length_match_s3<=header_length_total_s2==header_length_target_s2;
    end
    // V111_HEADER_PIPELINE_END

'''
 assertion='''    // Independent widened original predicate, checked at actual consumption.
    always_ff @(posedge clk)if(!cancelled&&!context_failure&&
        !(context_active&&ctx_done)&&state==HEADER)begin
        assert(header_length_match_s3 ==
            (({32'd0,cached32(14)}+{32'd0,cached32(18)}+
              {32'd0,cached32(22)}+{32'd0,cached32(26)}) ==
             {30'd0,({2'd0,size_bytes}-34'd46)}))
            else $fatal(1,"prepared header length predicate owner mismatch");
    end
'''
 edits=[('    task automatic fail_packet',pipeline+'    task automatic fail_packet'),
 ('else if({2\'d0,cached32(14)}+{2\'d0,cached32(18)}+{2\'d0,cached32(22)}+{2\'d0,cached32(26)}!=({2\'d0,size_bytes}-34\'d46)) fail_packet(4);','else if(!header_length_match_s3) fail_packet(4);'),
 ('`ifndef SYNTHESIS\n    // Independent mathematical caller contract','`ifndef SYNTHESIS\n'+assertion+'    // Independent mathematical caller contract')]
 for a,b in edits:assert s.count(a)==1;s=s.replace(a,b,1)
 dest=SRC/old.name;dest.write_text(s)
 write(SRC/'edit-recipe.json',dict(schema='v111-header-existing-edge-pipeline-v1',original=str(old.relative_to(ROOT)),original_sha256=sha(old),candidate=str(dest.relative_to(ROOT)),candidate_sha256=sha(dest),edits=[dict(before=a,after=b,expected_occurrences=1)for a,b in edits],added_public_cycles=0,private_payload_register_bits=169,all_original_assertions_retained=True,scope='Only original HEADER length-sum branch predicate changes; exact public invalid/error/counter/memory cycles; private preparation owned only on uncancelled HEADER consumption.'))
 adapters=[]
 def adapt(p,n,edits):
  t=p.read_text()
  for a,b in edits:assert t.count(a)==1;t=t.replace(a,b,1)
  q=V/n;q.write_text(t);adapters.append(dict(source=str(p.relative_to(ROOT)),source_sha256=sha(p),path=str(q.relative_to(ROOT)),sha256=sha(q),edits=edits))
 ctx=ROOT/'fpga/experiments/cu66-v110-count-domain/br88_context.sv'
 adapt(ctx,'br88_context_reference.sv',[('module br88_context','module br88_context_reference')])
 adapt(old,'ingress_original.sv',[('module br88_packet_ingress_sync_v91h ','module ingress_original '),("br88_context #(.PREVALIDATED_EVENT_COUNT(1'b1)) context_decoder", "br88_context_reference #(.PREVALIDATED_EVENT_COUNT(1'b1)) context_decoder")])
 adapt(dest,'ingress_candidate.sv',[('module br88_packet_ingress_sync_v91h ','module ingress_candidate ')])
 prev=ROOT/'fpga/experiments/cu66-v110-count-domain/verification'
 for n in ['ingress_capture_probe.sv','tb_capture.cpp']:
  adapt(prev/n,n,[])
 adapt(prev/'tb_fetch.cpp','inherited_fetch.cpp',[('int main(','int inherited_fetch_main(')])
 write(V/'adapters.json',dict(schema='v111-header-actual-ingress-adapters-v1',adapters=adapters,all_original_assertions_and_goldens_retained=True,old_reference_is_count_ingress=True,both_context_specializations_identical=True,all_public_ports_including_invalid_and_counters=True))
 write(AREA/'preparation.json',dict(status='PREPARED_NOT_RTL_QUALIFIED',candidate_sha256=sha(dest),source_recipe_sha256=sha(SRC/'edit-recipe.json'),adapter_sha256=sha(V/'adapters.json')))
 print('HEADER_PREPARED',sha(dest))
if __name__=='__main__':main()
