#!/usr/bin/env python3
"""Reversibly derive V116 LIVE row/byte parent from frozen V115 outer checks."""
import hashlib
import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
import instrumentation

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT/'fpga/experiments/cu66-v116-live-parent'
AREA = ROOT/'experiments/python-gamebub-v116/live-parent'
OLD = ROOT/'fpga/experiments/cu66-v115-live-parent'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write(p, obj):
    p.write_text(json.dumps(obj, indent=2, sort_keys=True)+'\n')


def main():
    SRC.mkdir(parents=True, exist_ok=True)
    AREA.mkdir(parents=True, exist_ok=True)
    records = []
    validator = ROOT/'fpga/experiments/cu66-v91l/cs88_validate_publish_v91l.sv'
    validator_text = validator.read_text()
    enum_match = re.search(r'localparam logic \[2:0\] LEAF=(\d+),EMPTY_LEAF=(\d+),NODE=(\d+),HUD=(\d+),SEAL=(\d+);', validator_text)
    assert enum_match and tuple(map(int,enum_match.groups())) == (0,1,2,3,4)
    assert 'job==NODE?node_width+node_index:10\'d0' in validator_text and 'if(node_width==1)begin\n                                    computed_root<=sha_digest;' in validator_text
    row_source = ROOT/'fpga/experiments/cu66-v116-rowjoin/cu66_row_write_hash_join_v91l.sv'
    assert 'FREE_SLOT=0,FILL_SLOT=1,READY_SLOT=2,WAIT_SLOT=3,HASH_SLOT=4' in row_source.read_text()

    def derive(name, edits):
        source = OLD/name
        text = source.read_text()
        (SRC/('frozen_'+name)).write_bytes(source.read_bytes())
        for before, after in edits:
            assert text.count(before) == 1, (name, before[:100], text.count(before))
            text = text.replace(before, after, 1)
        target = SRC/name
        target.write_text(text)
        for before, after in reversed(edits):
            assert text.count(after) == 1, (name, after[:100], text.count(after))
            text = text.replace(after, before, 1)
        assert text == source.read_text()
        records.append(dict(source=str(source.relative_to(ROOT)), source_sha256=sha(source), candidate=str(target.relative_to(ROOT)),
                            candidate_sha256=sha(target), edits=[dict(before=a, after=b) for a, b in edits]))

    wrapper = (OLD/'cs88_live_v91l.sv').read_text()
    first = wrapper.index(' cu66_write_hash_join_v91l joiner(')
    last = wrapper.index('\n', wrapper.index('.count_drops(join_drops));', first))
    instance = wrapper[first:last]
    row = instance.replace(' cu66_write_hash_join_v91l joiner(', ' cu66_row_write_hash_join_v91l joiner(')
    row = row.replace('.req_data(candidate_req_data),', '.req_data(candidate_req_data),.req_bytes(candidate_req_bytes),')
    row = row.replace('.state(join_state),', '.state(join_state),.fill_count(join_fill_count),.deliver_index(join_deliver_index),')
    byte = instance.replace('.req_data(candidate_req_data),', '.req_data(byte_data),').replace('.state(join_state),', '.state(byte_state),')
    replacement = ''' generate if(ROW_WRITES)begin: row_writes
'''+row+'''
 // Reporting-only views of the actual three bounded slot owners.
 assign join_slots_owned=2'(joiner.owner[0]!=0)+2'(joiner.owner[1]!=0)+2'(joiner.owner[2]!=0);
 assign join_phase_fill=joiner.owner[0]==1||joiner.owner[1]==1||joiner.owner[2]==1;
 assign join_phase_wait=join_physical_pending;
 assign join_phase_hash=joiner.owner[0]==4||joiner.owner[1]==4||joiner.owner[2]==4;
 end else begin: byte_writes
 logic [7:0] byte_data;
 logic [1:0] byte_state;
 assign candidate_req_data={56'd0,byte_data};
 assign candidate_req_bytes=4'd1;
 assign join_state={1'b0,byte_state};
 assign join_fill_count=0;assign join_deliver_index=0;
 assign join_slots_owned=join_busy?2'd1:2'd0;
 assign join_phase_fill=0;assign join_phase_wait=join_physical_pending;
 assign join_phase_hash=byte_state==3;
'''+byte+'''
 end endgenerate'''
    derive('cs88_live_v91l.sv', [
        ('module cs88_live_v91l (', 'module cs88_live_v91l #(parameter bit ROW_WRITES=1) ('),
        (' output logic [7:0] candidate_req_data,', ' output logic [63:0] candidate_req_data,output logic [3:0] candidate_req_bytes,'),
        (' output logic [1:0] join_state,output logic [7:0] join_error,', ' output logic [2:0] join_state,output logic [3:0] join_fill_count,\n output logic [2:0] join_deliver_index,output logic [1:0] join_slots_owned,\n output logic join_phase_fill,join_phase_wait,join_phase_hash,output logic [7:0] join_error,'),
        (instance, replacement),
    ])

    bench = (OLD/'tb_keyframe.cpp').read_text()
    edits = []

    def edit(before, after):
        assert bench.count(before) == 1, (before[:100], bench.count(before))
        edits.append((before, after))

    edit('#include "Vcs88_live_v91l.h"', '''#include "Vcs88_live_v91l.h"
#ifndef ROW_WRITES
#define ROW_WRITES 1
#endif
// Same full producer and C2/HUD oracles, separately compiled byte and row join.
static constexpr unsigned candidate_width=ROW_WRITES?8U:1U;''')
    edit('struct CandidateRequest {uint32_t epoch,token;unsigned bank,addr;uint8_t value;\n      bool operator==(const CandidateRequest &x)const{return epoch==x.epoch&&token==x.token&&bank==x.bank&&addr==x.addr&&value==x.value;}};',
         '''struct CandidateRequest {uint32_t epoch,token;unsigned bank,addr;uint64_t value;unsigned bytes;
      bool operator==(const CandidateRequest &x)const{return epoch==x.epoch&&token==x.token&&bank==x.bank&&addr==x.addr&&value==x.value&&bytes==x.bytes;}};''')
    edit('    uint64_t first_outer=0,last_outer=0,first_write=0,last_write=0,first_token=0,last_token=0;', '''    uint64_t first_outer=0,last_outer=0,first_write=0,last_write=0,first_token=0,last_token=0;
    uint64_t candidate_expanded_bytes=0,candidate_acked_bytes=0,service_data_edges=0,service_overhead_edges=0;
    uint64_t minimum_service=UINT64_MAX,maximum_service=0;
    std::array<std::vector<uint32_t>,3> candidate_ack_epoch{{std::vector<uint32_t>(560640),std::vector<uint32_t>(560640),std::vector<uint32_t>(560640)}};'''+instrumentation.FIELDS)
    edit('CandidateRequest candidate_request()const{return {d.candidate_req_epoch,d.candidate_req_token,unsigned(d.candidate_req_bank),unsigned(d.candidate_req_addr),uint8_t(d.candidate_req_data)};}',
         'CandidateRequest candidate_request()const{return {d.candidate_req_epoch,d.candidate_req_token,unsigned(d.candidate_req_bank),unsigned(d.candidate_req_addr),uint64_t(d.candidate_req_data),unsigned(d.candidate_req_bytes)};}')
    edit('      candidate_hash=1469598103934665603ULL;', '''      candidate_hash=1469598103934665603ULL;
      candidate_expanded_bytes=candidate_acked_bytes=service_data_edges=service_overhead_edges=0;
      minimum_service=UINT64_MAX;maximum_service=0;
      for(auto &bank:candidate_ack_epoch)std::fill(bank.begin(),bank.end(),0U);'''+instrumentation.RESET)
    edit('    void live_observe(){', instrumentation.METHODS+'    void live_observe(){')
    edit('      const bool kill=d.power_on_reset||d.reset||d.abort_packet||d.v_error||d.join_error||d.metadata_mismatch;',
         '      const bool kill=d.power_on_reset||d.reset||d.abort_packet||d.v_error||d.join_error||d.metadata_mismatch;\n      observe_fences(kill);')
    edit('    void live_after_edge(){', '    void live_after_edge(){\n'+instrumentation.AFTER_EDGE)
    edit('      record=false;tick();', '      record=false;tick();report_fences();')
    edit('        need(candidate_memory[d.v_write_bank][d.join_output_addr]==d.join_output_data,"hash delivery before actual ACK-committed write");',
         '''        need(candidate_memory[d.v_write_bank][d.join_output_addr]==d.join_output_data,"hash delivery before actual ACK-committed write");
        need(candidate_ack_epoch[d.v_write_bank][d.join_output_addr]==frame_epoch,"hash byte lacks successful matching ACK in current owner epoch");
        if(!d.join_output_hud){
          need(d.join_output_addr<518400&&++canonical_hash_bytes<=518400,"count every canonical hash byte");
          if(canonical_hash_bytes==518400)last_canonical_hash=cycle+1;
        }else{
          need(d.join_output_addr>=518400&&++hud_hash_bytes<=42240,"count every HUD hash byte");
          if(hud_hash_bytes==42240)last_hud_hash=cycle+1;
        }''')
    edit('        if(!bus_error)candidate_memory[q.bank][q.addr]=q.value;', '''        if(!bus_error)for(unsigned n=0;n<q.bytes;++n){
          candidate_memory[q.bank][q.addr+n]=uint8_t(q.value>>(8U*n));
          candidate_ack_epoch[q.bank][q.addr+n]=q.epoch;
          ++candidate_acked_bytes;
          if(q.addr+n<518400){need(++canonical_ack_bytes<=518400,"count every successful canonical ACK byte");if(canonical_ack_bytes==518400)last_canonical_ack=cycle+1;}
          else{need(++hud_ack_bytes<=42240,"count every successful HUD ACK byte");if(hud_ack_bytes==42240)last_hud_ack=cycle+1;}
        }''')
    edit('        need(q.epoch==frame_epoch&&q.bank==d.v_write_bank&&q.addr<560640,"candidate request owner/bounds");', '''        need(q.epoch==frame_epoch&&q.bank==d.v_write_bank&&q.addr<560640,"candidate request owner/bounds");
        need(q.bytes==candidate_width&&q.addr+q.bytes<=560640&&(!ROW_WRITES||(q.addr&7U)==0),"normalized bounded candidate row descriptor");''')
    edit('        uint8_t expected=q.addr<518400?canonical_golden().expected[q.addr]:provisional_hud[q.addr-518400];need(q.value==expected,"physical write byte vs actual independent expected");', '''        if(!ROW_WRITES){
          uint8_t expected=q.addr<518400?canonical_golden().expected[q.addr]:provisional_hud[q.addr-518400];need(q.value==expected,"physical write byte vs actual independent expected");
        }
        for(unsigned n=0;n<q.bytes;++n){
          const unsigned address=q.addr+n;
          uint8_t expected=address<518400?canonical_golden().expected[address]:provisional_hud[address-518400];
          need(uint8_t(q.value>>(8U*n))==expected,"expanded physical request byte vs independent canonical/HUD oracle");
          need(candidate_ack_epoch[q.bank][address]!=q.epoch,"candidate byte rewritten in one frame owner");
          if(address<518400)++canonical_request_bytes;else ++hud_request_bytes;
        }
        candidate_expanded_bytes+=q.bytes;''')
    edit('        candidate_hash=hash_byte(candidate_hash,q.value);', '        for(unsigned n=0;n<q.bytes;++n)candidate_hash=hash_byte(candidate_hash,uint8_t(q.value>>(8U*n)));')
    edit('        candidate_pending=CandidatePending{q,cycle+(profile?3+random(6):1)};++candidate_requests;', '''        // A single physical lease bounds the abstract service queue. One 8B
        // request consumes four 16-bit data edges plus explicit overhead.
        const uint64_t data_edges=(q.bytes+1U)/2U;
        const uint64_t overhead=profile?8U+random(9):2U;
        const uint64_t service=data_edges+overhead;
        service_data_edges+=data_edges;service_overhead_edges+=overhead;
        minimum_service=std::min(minimum_service,service);maximum_service=std::max(maximum_service,service);
        candidate_pending=CandidatePending{q,cycle+service};++candidate_requests;''')
    old_need = '      need(d.join_inputs==560640&&d.join_requests==560640&&d.join_acks==560640&&d.join_outputs==560640,"live write/hash conservation");'
    edit(old_need, '      if(!ROW_WRITES){\n'+old_need+'\n      }else need(d.join_inputs==560640&&d.join_requests==70080&&d.join_acks==70080&&d.join_outputs==560640,"row physical requests/ACKs and original expanded-byte conservation");\n      need(candidate_expanded_bytes==560640&&candidate_acked_bytes==560640,"all original bytes independently expanded and ACK committed");')
    old_need = ' need(b.candidate_requests==560640&&b.candidate_acks==560640&&b.hash_deliveries==560640,"exact finite candidate write/ACK/hash conservation");'
    edit(old_need, ' if(!ROW_WRITES){\n'+old_need+'\n }else need(b.candidate_requests==70080&&b.candidate_acks==70080&&b.hash_deliveries==560640,"exact finite row request/ACK and original hash-byte conservation");\n need(b.candidate_expanded_bytes==560640&&b.candidate_acked_bytes==560640,"original full candidate byte oracle after independent row expansion");')
    marker = ' std::cout<<"{\\"type\\":\\"live_parent_verdict\\",'
    edit(marker, ''' std::cout<<"{\\"type\\":\\"live_service_verdict\\",\\"status\\":\\"TEST_PASS\\",\\"row_writes\\":"<<unsigned(ROW_WRITES)
          <<",\\"request_bytes\\":"<<candidate_width<<",\\"expanded_bytes\\":"<<b.candidate_expanded_bytes<<",\\"acked_bytes\\":"<<b.candidate_acked_bytes
          <<",\\"service_queue_bound\\":1,\\"service_bus_bits\\":16,\\"service_data_edges\\":"<<b.service_data_edges<<",\\"service_overhead_edges\\":"<<b.service_overhead_edges
          <<",\\"minimum_service_edges\\":"<<b.minimum_service<<",\\"maximum_service_edges\\":"<<b.maximum_service<<",\\"physical_SDRAM\\":false}\\n";
'''+marker)
    hash_line = next(line for line in bench.splitlines() if line.startswith('      if(d.v_hash_result&&record){hash_events'))
    assert hash_line.count('<<cycle<<') == 1
    edit(hash_line, hash_line.replace('<<cycle<<', '<<(cycle+1)<<'))
    derive('tb_keyframe.cpp', edits)
    frozen = OLD/'derivation.json'
    write(SRC/'derivation.json', dict(schema='v116-live-row-and-byte-parent-reversible-v1', sources=records,
          frozen_derivation=dict(path=str(frozen.relative_to(ROOT)), sha256=sha(frozen)),
          validator_job_enum=dict(path=str(validator.relative_to(ROOT)), sha256=sha(validator), LEAF=0, EMPTY_LEAF=1, NODE=2, HUD=3, SEAL=4, root_kind=2, root_node=1),
          row_debug_owners=dict(path=str(row_source.relative_to(ROOT)), sha256=sha(row_source), FREE_SLOT=0, FILL_SLOT=1, READY_SLOT=2, WAIT_SLOT=3, HASH_SLOT=4),
          reverse_verified=True, original_oracles_retained=True,
          counted_schedule_change='Row mode replaces eight physical byte requests with one eight-byte request; full 560640-byte and1025-job oracles remain exact.',
          contract='Frozen V115 local registered fault cancellation and physical drain, actual V11618-source producer, bytejoin control or bounded three-slot rowjoin, independently expanded request bytes with matching ACK-before-hash epoch proof.',
          limits='Abstract 16-bit finite service model; no physical SDRAM, full-parent routed timing or hardware performance claim.'))
    write(AREA/'preparation.json', dict(status='PREPARED_NOT_RTL_QUALIFIED', actual_RTL_run=False,
          source_receipt_pending='experiments/python-gamebub-v116/spatial/results.json',
          dynamic_source_binding=True, fixed_precompletion_summary_sha_required=False,
          source_sha256={str((SRC/name).relative_to(ROOT)):sha(SRC/name) for name in ('cs88_live_v91l.sv','tb_keyframe.cpp','derivation.json')}))
    print('V116_LIVE_PARENT_PREPARED_NOT_RUN', sha(SRC/'cs88_live_v91l.sv'), sha(SRC/'tb_keyframe.cpp'))


if __name__ == '__main__':
    main()
