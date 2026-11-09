#!/usr/bin/env python3
"""Prepare a reversible V114 bench + frozen V91l live-service partition, no RTL run."""
import ast
import collections
import hashlib
import json
from pathlib import Path
import re

R=Path(__file__).resolve().parents[3]
S=R/'fpga/experiments/cu66-v115-live-parent'
SELECT=R/'experiments/python-gamebub-v115/spatial/results.json'
SELECT_SHA='52697a476f23ec0c44c17fc80026daeb63755d5481f2c360c8af9b4f557fc907'
BASE=R/'fpga/experiments/cu66-v114-harness/bench_command_api.cpp'
GEN=R/'fpga/experiments/cu66-v91l-live/make_bench.py'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return str(p.relative_to(R))
def write(p,q):p.write_text(json.dumps(q,indent=2,sort_keys=True)+'\n')
def main():
 assert sha(SELECT)==SELECT_SHA
 chosen=json.loads(SELECT.read_text());assert chosen['status']=='PASS_V115_SPATIAL_CANONICAL'
 assert sha(BASE)==chosen['source_sha256'][rel(BASE)]
 old_top=R/'fpga/experiments/cu66-v91k/cs88_pipeline_v91k.sv';new_top=R/'fpga/experiments/cu66-v114-control/cs88_pipeline_v91k.sv'
 def header(p):s=p.read_text();return s[s.index('(')+1:s.index(');')]
 assert header(old_top)==header(new_top)
 # These literal extensions contain the old actual C2/HUD/ACK/publication oracles.
 literals={}
 for node in ast.parse(GEN.read_text()).body:
  if isinstance(node,ast.Assign)and len(node.targets)==1 and isinstance(node.targets[0],ast.Name)and node.targets[0].id in ('helper','fields'):
   literals[node.targets[0].id]=ast.literal_eval(node.value)
 assert set(literals)=={'helper','fields'}
 original=BASE.read_text().split('int main(')[0];text=original;edits=[]
 def edit(before,after,count=1):
  nonlocal text
  assert text.count(before)==count,(before[:100],text.count(before),count)
  text=text.replace(before,after,count);edits.append(dict(before=before,after=after,occurrences=count))
 edit('Vcs88_pipeline_v91k','Vcs88_live_v91l',text.count('Vcs88_pipeline_v91k'))
 edit('cs88_pipeline_v91k__DOT__','cs88_live_v91l__DOT__producer__DOT__',text.count('cs88_pipeline_v91k__DOT__'))
 edit('#include "verilated.h"','#include "verilated.h"\n#include <string_view>\n#include "../../../experiments/cu66-native-v69/hud.hpp"')
 edit('struct Tuple{',literals['helper']+'\nstruct Tuple{')
 edit('    Vcs88_live_v91l d;',literals['fields']+'\n    Vcs88_live_v91l d;')
 edit('d.out_ready=0;','/* out_ready is driven by the unchanged ACK-coupled join. */')
 edit('d.cache_data=c.prior[i];','d.cache_data=accepted_qcache[i];')
 edit('        tick();d.reset=0;tick();','        d.power_on_reset=1;d.software_hud_valid=0;d.software_receipt_valid=0;d.candidate_rsp_valid=0;d.candidate_req_ready=0;d.present_vblank=1;d.present_drained=1;\n        tick();d.power_on_reset=0;d.reset=0;tick();')
 edit('d.clk=0;d.out_ready=!force_output_hold&&(profile==0||random(3)==0);','d.clk=0;live_before_eval();')
 edit('const auto &pixels=canonical_golden().reference;need(pixels.size()==518400,"reference bytes unavailable");','need(d.v_reference_bank_valid,"reference has no actual validated bank");const auto &bank_pixels=candidate_memory[d.v_reference_bank];need(bank_pixels.size()==560640,"actual candidate bank size");const std::basic_string_view<uint8_t> pixels(bank_pixels.data(),518400);need(pixels.size()==518400,"reference bytes unavailable");\n            for(unsigned n=0;n<64;++n)need(pixels[pixel_address(r.plane,r.tile,n)]==canonical_golden().reference[pixel_address(r.plane,r.tile,n)],"actual accepted reference differs from independent golden");')
 edit('d.eval();const bool cancel=d.reset||d.abort_packet;','d.eval();live_observe();const bool cancel=d.reset||d.power_on_reset||d.abort_packet||d.v_error||d.join_error||d.metadata_mismatch;')
 edit('if(d.in_valid&&d.in_ready){received.push_back(d.in_data);','if(d.in_valid&&d.in_ready){if(!first_outer)first_outer=cycle+1;last_outer=cycle+1;received.push_back(d.in_data);')
 edit('d.clk=1;d.eval();++cycle;','d.clk=1;d.eval();++cycle;live_after_edge();')
 edit('if(d.error||d.done){','if(d.error||d.done||d.v_error||d.join_error||d.metadata_mismatch){')
 # Preserve start_ready and every original assertion. This outer wrapper's credit
 # is withheld until C2/HUD validation; extend only the finite drain watchdog.
 edit('k<200000;','k<20000000;')
 # Cold reset is an actual reset input of the new outer wrapper.
 edit('const bool kill=d.reset||r.cs88_live_v91l__DOT__producer__DOT__accepted_start','const bool kill=d.reset||d.power_on_reset||r.cs88_live_v91l__DOT__producer__DOT__accepted_start')
 edit('if(d.reset||r.cs88_live_v91l__DOT__producer__DOT__accepted_start)','if(d.reset||d.power_on_reset||r.cs88_live_v91l__DOT__producer__DOT__accepted_start)')
 back=text
 for e in reversed(edits):
  assert back.count(e['after'])==e['occurrences'];back=back.replace(e['after'],e['before'],e['occurrences'])
 assert back==original
 # Preserve the canonical-only reference-size assertion through a bounded view
 # of the larger actual bank; all fetched bytes gain an independent golden check.
 normalized_original=original.replace('cs88_pipeline_v91k__DOT__','cs88_live_v91l__DOT__producer__DOT__')
 old=collections.Counter(re.findall(r'need\(.*?\);',normalized_original,re.S));new=collections.Counter(re.findall(r'need\(.*?\);',text,re.S))
 missing=list((old-new).elements());assert not missing,missing
 main=r'''
int main(int argc,char **argv){try{
 need(argc==10,"usage: live cases transforms canonical validation seed events actual hashes profile");
 auto cases=load(argv[1]);load_tiles(argv[2]);load_validation(argv[4]);unsigned seed=unsigned(std::stoul(argv[5])),profile=unsigned(std::stoul(argv[9]));need(profile<2,"finite service profile");
 Bench b(seed,argv[6],argv[3],argv[7]);b.hash_events.open(argv[8]);need(bool(b.hash_events),"hash events output");
 const Case*key=nullptr;for(const auto&c:cases)if(c.id=="actual_001")key=&c;need(key!=nullptr,"original keyframe fixture");
 b.cold_live();
 // Exercise a real accepted physical write before the newly registered local
 // producer cancellation. Parent hash/publication must remain invalid.
 b.prepare(*key,profile,false);b.stage_live(*key);b.preload(*key);b.begin(*key);b.hold_candidate=true;b.feed_until(11);
 for(unsigned n=0;n<6000000&&!b.candidate_pending&&!b.d.v_error;++n)b.tick();
 need(bool(b.candidate_pending),"owned candidate write before registered parent cancellation");
 const auto failed_owner=b.candidate_pending->q;b.wrong_ack=true;b.hold_candidate=false;b.tick();
 need(b.d.join_error==0x81&&b.d.join_physical_pending&&b.candidate_pending&&b.candidate_pending->q==failed_owner,"wrong ACK must retain actual physical debt");
 b.wrong_ack=false;b.drain_live();
 need(!b.d.v_accepted_valid&&!b.d.v_front_valid&&!b.d.v_pending_valid&&!b.candidate_pending&&!b.d.join_physical_pending,"failed parent transaction published or retained physical debt");
 b.nominal(*key,profile);
 need(b.d.v_accepted_valid&&b.d.v_front_valid&&b.d.v_front_fid==0&&!b.d.v_pending_valid,"validated keyframe abstract publication");
 need(b.candidate_requests==560640&&b.candidate_acks==560640&&b.hash_deliveries==560640,"exact finite candidate write/ACK/hash conservation");
 need(!b.pending&&!b.reference_pending&&!b.candidate_pending&&!b.d.join_physical_pending&&b.d.join_drained,"physical owners remain after publication");
 need(b.d.v_hash_jobs==1025&&b.d.v_pixel_bytes==518400&&b.d.v_hud_bytes==42240,"complete C2/HUD work");
 std::cout<<"{\"type\":\"live_parent_verdict\",\"status\":\"TEST_PASS\",\"seed\":"<<seed<<",\"profile\":"<<profile<<",\"keyframes\":1,\"canonical_bytes\":518400,\"hud_bytes\":42240,\"candidate_write_requests\":"<<b.candidate_requests<<",\"candidate_write_acks\":"<<b.candidate_acks<<",\"hash_deliveries\":"<<b.hash_deliveries<<",\"hash_jobs\":1025,\"elastic_accepted\":"<<b.elastic_total_up<<",\"elastic_delivered\":"<<b.elastic_total_down<<",\"clock_edges\":"<<b.cycle<<",\"directed_checks\":2,\"wrong_ack_owned_write_drained\":true,\"clean_retry_without_reset\":true,\"actual_C2_HUD_seal_validation\":true,\"abstract_publication\":true,\"software_HUD_decode\":true,\"physical_SDRAM\":false,\"hardware_30fps\":false}\n";return 0;
}catch(const std::exception&e){std::cerr<<"V115_LIVE_PARENT_FAIL "<<e.what()<<'\n';return 1;}}
'''
 bench=S/'tb_keyframe.cpp';bench.write_text(text+main)
 wrapper=R/'fpga/experiments/cu66-v91l-live/cs88_live_v91l.sv';wrap=wrapper.read_text();wrapper_edits=[]
 def wedit(a,b):
  nonlocal wrap
  assert wrap.count(a)==1,(a[:80],wrap.count(a));wrap=wrap.replace(a,b,1);wrapper_edits.append(dict(before=a,after=b))
 wedit(' logic active_key,fault_ack,fault_cancel,transaction_active;',''' logic active_key,fault_ack,fault_cancel,transaction_active;
 // A local registered cancel breaks producer masked-done -> parent fault ->
 // producer public-revocation feedback. Parent validation/write/hash cancel
 // remains immediate; external abort and cold/warm reset remain direct.
 logic producer_fault_cancel,parent_transfer_enable;
 logic producer_in_ready,producer_cache_ready,producer_mem_req_valid,producer_ref_req_valid;
 assign parent_transfer_enable=!(power_on_reset||reset||abort_packet||fault_cancel||producer_fault_cancel);
 assign in_ready=producer_in_ready&&parent_transfer_enable;
 assign cache_ready=producer_cache_ready&&parent_transfer_enable;
 assign mem_req_valid=producer_mem_req_valid&&parent_transfer_enable;
 assign ref_req_valid=producer_ref_req_valid&&parent_transfer_enable;
 always_ff @(posedge clk)begin
  if(power_on_reset||reset||abort_packet||accepted_start)producer_fault_cancel<=0;
  else producer_fault_cancel<=fault_cancel;
 end''')
 wedit('.abort_packet(abort_packet||fault_cancel),','.abort_packet(abort_packet||producer_fault_cancel),')
 for connection_old,connection_new in [('.in_valid(in_valid),','.in_valid(in_valid&&parent_transfer_enable),'),('.in_ready(in_ready),','.in_ready(producer_in_ready),'),('.cache_valid(cache_valid),','.cache_valid(cache_valid&&parent_transfer_enable),'),('.cache_ready(cache_ready),','.cache_ready(producer_cache_ready),'),('.mem_req_valid(mem_req_valid),','.mem_req_valid(producer_mem_req_valid),'),('.mem_req_ready(mem_req_ready),','.mem_req_ready(mem_req_ready&&parent_transfer_enable),'),('.ref_req_valid(ref_req_valid),','.ref_req_valid(producer_ref_req_valid),'),('.ref_req_ready(ref_req_ready),','.ref_req_ready(ref_req_ready&&parent_transfer_enable),')]:wedit(connection_old,connection_new)
 wedit('endmodule',''' // Accepted response channels are deliberately not masked: real physical
 // memory/reference/candidate debt must drain after parent revocation.
 always_ff @(posedge clk)if(!power_on_reset)begin
  if(fault_cancel||producer_fault_cancel||reset||abort_packet)begin
   assert(!in_ready&&!cache_ready&&!mem_req_valid&&!ref_req_valid)
    else $fatal(1,"parent revocation exposed a new producer request grant");
  end
  if(fault_cancel)begin
   assert(!candidate_req_valid&&!join_output_valid&&!software_hud_ready&&!start_ready)
    else $fatal(1,"immediate parent fault exposed new write/hash/HUD/admission work");
  end
 end
endmodule''')
 (S/wrapper.name).write_text(wrap);back=wrap
 for e in reversed(wrapper_edits):assert back.count(e['after'])==1;back=back.replace(e['after'],e['before'],1)
 assert back==wrapper.read_text()
 write(S/'derivation.json',dict(schema='v115-keyframe-live-parent-reversible-bench-v1',selected_spatial=dict(path=rel(SELECT),sha256=sha(SELECT)),base=dict(path=rel(BASE),sha256=sha(BASE),prefix_sha256=hashlib.sha256(original.encode()).hexdigest()),live_extensions=dict(path=rel(GEN),sha256=sha(GEN),literal_names=['helper','fields']),derived=dict(path=rel(bench),sha256=sha(bench)),edits=edits,main=main,reverse_verified=True,original_need_calls=len(list(old.elements())),changed_need_calls=missing,changed_need_reason='No original need() call removed; a bounded canonical view excludes the HUD suffix of the actual validated bank.',wrapper=dict(original=rel(wrapper),original_sha256=sha(wrapper),copy=rel(S/wrapper.name),sha256=sha(S/wrapper.name),byte_exact=False,edits=wrapper_edits,reverse_verified=True),selected_producer_header_equal_original=True,contract='V114 E/E+1 command delivery unchanged; selected V115 private preparation unchanged. Outer C2/HUD publication credit is waited on by the original start_ready drain condition, bounded at20M edges. Cold power reset participates in the retained coefficient-elastic monitor. Parent fault cancels join/validation immediately and producer locally one edge later; request grants are masked while accepted responses drain unchanged.',scope='Actual selected V115 component + unchanged V91l ACK join/C2-HUD validator/bank publication. Software HUD semantic decode; no ESP32/QSPI/physical SDRAM/RGB LCD execution.'))
 print('V115_LIVE_PARENT_PREPARED_NOT_RUN',sha(bench))
if __name__=='__main__':main()
