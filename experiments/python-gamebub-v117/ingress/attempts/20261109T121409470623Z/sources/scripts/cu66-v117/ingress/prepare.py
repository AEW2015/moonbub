#!/usr/bin/env python3
"""Derive owned descriptor extents from the actual V117 A routed ingress cause."""
from pathlib import Path
import hashlib,json,shutil,re
R=Path(__file__).resolve().parents[3];S=R/'fpga/experiments/cu66-v117-ingress';V=S/'verification';OLD=R/'fpga/experiments/cu66-v115-final-ingress';AC=R/'fpga/experiments/cu66-v117-ac'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return str(p.relative_to(R))
def derive(p,q,edits):
 text=p.read_text()
 for e in edits:
  assert text.count(e['before'])==1,e['before'][:90];text=text.replace(e['before'],e['after'],1)
 q.write_text(text);return dict(original=rel(p),original_sha256=sha(p),candidate=rel(q),candidate_sha256=sha(q),edits=edits)
new='''    // V117: stable packet-size arithmetic matures before descriptor selection.
    // No accepted-input combinational shortcut, reset or global payload CE.
    logic [31:0] packet_payload_end, packet_bit_limit;
    logic [31:0] active_remaining, active_length_minus6;
    logic active_cursor_bad;
    always_ff @(posedge clk)begin
        packet_payload_end<=size_bytes-4;
        packet_bit_limit<=8*(size_bytes-46);
    end
`ifndef SYNTHESIS
    // Verification-only ownership certificates. Hardware already retains the
    // packet size/epoch and selected band/length in its original owner tuple.
    logic packet_extent_warm=0,descriptor_extent_live=0;
    logic [31:0] packet_extent_size,packet_extent_epoch;
    logic [31:0] descriptor_extent_cursor,descriptor_extent_epoch;
    logic [1:0] descriptor_extent_band;
    always_ff @(posedge clk)begin
        packet_extent_size<=size_bytes;packet_extent_epoch<=context_epoch;
        if(cancelled||context_failure||(context_active&&ctx_done))begin
            packet_extent_warm<=0;descriptor_extent_live<=0;
        end else begin
            packet_extent_warm<=1;
            if(state==SELECT_BAND)begin
                descriptor_extent_live<=!selection_context;
                descriptor_extent_cursor<=cursor;descriptor_extent_epoch<=context_epoch;
                descriptor_extent_band<=band;
            end
        end
        if(!cancelled&&!context_failure&&!(context_active&&ctx_done)&&state==SELECT_BAND&&!selection_context)begin
            assert(packet_extent_warm&&packet_extent_size==size_bytes&&packet_extent_epoch==context_epoch)
                else $fatal(1,"V117 packet extents lack stable current packet owner");
            assert(packet_payload_end==size_bytes-4&&packet_bit_limit==8*(size_bytes-46))
                else $fatal(1,"V117 packet extent differs from literal full32 arithmetic");
        end
        if(!cancelled&&!context_failure&&!(context_active&&ctx_done)&&state==DESCRIPTOR)begin
            assert(descriptor_extent_live&&descriptor_extent_cursor==cursor&&
                descriptor_extent_epoch==context_epoch&&descriptor_extent_band==band)
                else $fatal(1,"V117 descriptor extents mixed owner/frontier");
            assert(active_cursor_bad==(cursor>size_bytes-4)&&active_remaining==size_bytes-4-cursor&&
                active_length_minus6==active_length-6&&packet_bit_limit==8*(size_bytes-46))
                else $fatal(1,"V117 descriptor extent changed uint32 wrap semantics");
            assert((active_length<6||active_cursor_bad||active_length>active_remaining)==
                (active_length<6||cursor>size_bytes-4||active_length>size_bytes-4-cursor))
                else $fatal(1,"V117 initial descriptor bound predicate mismatch");
            assert((descriptor_bytes!=active_length_minus6||descriptor_bits>packet_bit_limit)==
                (descriptor_bytes!=active_length-6||descriptor_bits>8*(size_bytes-46)))
                else $fatal(1,"V117 completed descriptor bound predicate mismatch");
        end
    end
`endif
'''
edits=[dict(before='    function automatic logic [31:0] cached32(input integer at);',after=new+'\n    function automatic logic [31:0] cached32(input integer at);'),
 dict(before='                    active_length_minus1<=lengths[band]-1;',after='                    active_length_minus1<=lengths[band]-1;\n                    active_length_minus6<=lengths[band]-6;\n                    active_remaining<=packet_payload_end-cursor;\n                    active_cursor_bad<=cursor>packet_payload_end;'),
 dict(before='                        if(active_length<6 || cursor>size_bytes-4 || active_length>size_bytes-4-cursor) fail_packet(4);',after='                        if(active_length<6 || active_cursor_bad || active_length>active_remaining) fail_packet(4);'),
 dict(before='                        if(descriptor_bytes!=active_length-6 || descriptor_bits>8*(size_bytes-46)) fail_packet(4);',after='                        if(descriptor_bytes!=active_length_minus6 || descriptor_bits>packet_bit_limit) fail_packet(4);')]
recipe=derive(OLD/'br88_packet_ingress_sync_v91h.sv',S/'br88_packet_ingress_sync_v91h.sv',edits)
for block in re.findall(r'`ifndef SYNTHESIS(.*?)`endif',(OLD/'br88_packet_ingress_sync_v91h.sv').read_text(),re.S):assert block in (S/'br88_packet_ingress_sync_v91h.sv').read_text()
adapters=[]
adapters.append(derive(OLD/'br88_packet_ingress_sync_v91h.sv',V/'br88_packet_ingress_sync_v91h_reference.sv',[dict(before='module br88_packet_ingress_sync_v91h #(',after='module br88_packet_ingress_sync_v91h_reference #(')]))
for name in ('ingress_probe.sv','tb_ingress.cpp'):shutil.copyfile(OLD/'verification'/name,V/name)
adapters.append(derive(OLD/'verification/tb_ingress.cpp',V/'ingress_base.cpp',[dict(before='int main(int argc,char**argv)',after='int inherited_ingress_main(int argc,char**argv)')]))
# Actual caller pair differs only in the synchronous ingress under test.
for name in ('tb_pipeline.cpp','caller_prepare.cpp','pair_adapter.hpp','br88_pipeline_pair.sv','br88_pipeline_candidate.sv'):
 shutil.copyfile(AC/'verification'/name,V/name)
caller=R/'fpga/experiments/cu66-v116b-control/br88_pipeline_v91h.sv'
adapters.append(derive(caller,V/'br88_pipeline_reference.sv',[dict(before='module br88_pipeline_v91h #(',after='module br88_pipeline_reference #('),dict(before='    packed_scratch_v91g2 scratch (',after='    packed_scratch_reference scratch ('),dict(before='    br88_packet_ingress_v91h #(',after='    br88_packet_ingress_v91h_reference #(')]))
adapters.append(derive(AC/'packed_scratch_v91g2.sv',V/'packed_scratch_reference.sv',[dict(before='module packed_scratch_v91g2 (',after='module packed_scratch_reference (')]))
wrapper=R/'fpga/experiments/cu66-v108-capacity/br88_packet_ingress_v91h.sv'
adapters.append(derive(wrapper,V/'br88_packet_ingress_v91h_reference.sv',[dict(before='module br88_packet_ingress_v91h #(',after='module br88_packet_ingress_v91h_reference #('),dict(before='        br88_packet_ingress_sync_v91h #(',after='        br88_packet_ingress_sync_v91h_reference #(')]))
manifest=dict(schema='v117-actual-routed-ingress-descriptor-extents-v1',production=[recipe],adapters=adapters,
 unchanged_verification={rel(OLD/'verification'/n):sha(OLD/'verification'/n)for n in ('ingress_probe.sv','tb_ingress.cpp')},
 unchanged_caller_verification={rel(AC/'verification'/n):sha(AC/'verification'/n)for n in ('tb_pipeline.cpp','caller_prepare.cpp','pair_adapter.hpp','br88_pipeline_pair.sv','br88_pipeline_candidate.sv')},
 declared_public_cycle_delta=0,actual_routed_cause='experiments/python-gamebub-v117/read-study/native/20261109T113046956485Z/receipt.json')
(S/'edit-recipes.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n');print('V117_INGRESS_PREPARED',recipe['candidate_sha256'])
