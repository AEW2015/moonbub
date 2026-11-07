"""Derive width-priced live comparison from frozen checked live testbench."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];AREA=Path(__file__).resolve().parent
s=(ROOT/'fpga/experiments/cu66-v91l-live/tb_live.cpp').read_text()
s=s.replace('Vcs88_live_v91l','Vcs88_rows_v91l')
s=s.replace('#include "verilated.h"','#include "verilated.h"\n#ifndef ROW_WRITES\n#error ROW_WRITES must select the static hardware build\n#endif\nstatic constexpr unsigned BATCH_BYTES=ROW_WRITES?8:1;')
s=s.replace('struct CandidateRequest {uint32_t epoch,token;unsigned bank,addr;uint8_t value;', 'struct CandidateRequest {uint32_t epoch,token;unsigned bank,addr,bytes;uint64_t value;')
s=s.replace('addr==x.addr&&value==x.value;', 'addr==x.addr&&bytes==x.bytes&&value==x.value;')
s=s.replace('uint8_t(d.candidate_req_data)};', 'unsigned(d.candidate_req_bytes),uint64_t(d.candidate_req_data)};')
s=s.replace('uint64_t first_outer=0', 'uint64_t candidate_data_beats=0,candidate_overhead_cycles=0,candidate_write_bytes=0;\n    uint64_t first_outer=0')
s=s.replace('candidate_hash=1469598103934665603ULL;', 'candidate_hash=1469598103934665603ULL;candidate_data_beats=candidate_overhead_cycles=candidate_write_bytes=0;')
s=s.replace('if(!bus_error)candidate_memory[q.bank][q.addr]=q.value;', 'if(!bus_error)for(unsigned j=0;j<q.bytes;++j)candidate_memory[q.bank][q.addr+j]=uint8_t(q.value>>(j*8));')
s=s.replace('q.epoch==frame_epoch&&q.bank==d.v_write_bank&&q.addr<560640', 'q.epoch==frame_epoch&&q.bank==d.v_write_bank&&q.bytes==BATCH_BYTES&&q.addr+q.bytes<=560640&&q.addr%q.bytes==0')
s=s.replace('uint8_t expected=q.addr<518400?canonical_golden().expected[q.addr]:provisional_hud[q.addr-518400];need(q.value==expected,"physical write byte vs actual independent expected");', '''for(unsigned j=0;j<q.bytes;++j){unsigned a=q.addr+j;uint8_t expected=a<518400?canonical_golden().expected[a]:provisional_hud[a-518400];need(uint8_t(q.value>>(8*j))==expected,"physical write payload vs actual independent expected");}
        candidate_write_bytes+=q.bytes;''')
s=s.replace('uint32_t(q.bank),uint32_t(q.addr)})', 'uint32_t(q.bank),uint32_t(q.addr),uint32_t(q.bytes)})')
s=s.replace('candidate_hash=hash_byte(candidate_hash,q.value);','for(unsigned j=0;j<q.bytes;++j)candidate_hash=hash_byte(candidate_hash,uint8_t(q.value>>(8*j)));')
s=s.replace('candidate_pending=CandidatePending{q,cycle+(profile?3+random(6):1)};++candidate_requests;', '''const unsigned payload_beats=(q.bytes+1)/2,overhead=profile?2+random(6):1;
        candidate_data_beats+=payload_beats;candidate_overhead_cycles+=overhead;
        candidate_pending=CandidatePending{q,cycle+payload_beats+overhead};++candidate_requests;''')
s=s.replace('d.join_requests==560640&&d.join_acks==560640', 'd.join_requests==560640/BATCH_BYTES&&d.join_acks==560640/BATCH_BYTES')
s=s.replace('candidate_requests==candidate_acks&&hash_deliveries==560640', 'candidate_requests==candidate_acks&&candidate_requests==560640/BATCH_BYTES&&candidate_write_bytes==560640&&hash_deliveries==560640')
s=s.replace('<<candidate_requests<<",\\"write_acks', '<<candidate_requests<<",\\"write_acks')
needle='<<candidate_acks<<",\\"hash_deliveries\\":"'
assert needle in s
s=s.replace(needle,'<<candidate_acks<<",\\"write_batch_bytes\\":"<<BATCH_BYTES<<",\\"x16_data_beats\\":"<<candidate_data_beats<<",\\"candidate_response_overhead_cycles\\":"<<candidate_overhead_cycles<<",\\"physical_write_bytes\\":"<<candidate_write_bytes<<",\\"hash_deliveries\\":"')
s=s.replace('std::cout<<"{\\"type\\":\\"verdict\\",\\"status\\":\\"TEST_PASS\\",\\"seed\\":"<<seed', 'std::cout<<"{\\"type\\":\\"verdict\\",\\"status\\":\\"TEST_PASS\\",\\"write_batch_bytes\\":"<<BATCH_BYTES<<",\\"seed\\":"<<seed')
s=s.replace('    std::ofstream hash_events;', r"""    std::ofstream hash_events,bus_events;
    void bus_event(unsigned kind,unsigned bank,unsigned bytes,uint32_t event_epoch,uint32_t token,unsigned addr,uint64_t value){
      if(!record)return;
      need(vf&&bool(bus_events),"binary bus trace owner");
      for(unsigned v:{kind,profile,bank,bytes})bus_events.put(char(v));
      for(uint32_t v:{be32(vf->packet,8),event_epoch,token,uint32_t(addr)})for(unsigned j=0;j<4;++j)bus_events.put(char(v>>(j*8)));
      for(unsigned j=0;j<8;++j)bus_events.put(char(value>>(j*8)));
      for(unsigned j=0;j<4;++j)bus_events.put(char(uint32_t(cycle+1)>>(j*8)));
    }""")
s=s.replace('        ++hash_deliveries;', '        bus_event(2,d.v_write_bank,1,frame_epoch,0,d.join_output_addr,d.join_output_data);++hash_deliveries;')
s=s.replace('candidate_pending.reset();++candidate_acks;last_write=cycle+1;', 'bus_event(1,q.bank,q.bytes,d.candidate_rsp_epoch,d.candidate_rsp_token,d.candidate_rsp_addr,q.value);candidate_pending.reset();++candidate_acks;last_write=cycle+1;')
s=s.replace('        candidate_write_bytes+=q.bytes;', '        bus_event(0,q.bank,q.bytes,q.epoch,q.token,q.addr,q.value);candidate_write_bytes+=q.bytes;')
s=s.replace('need(argc==9,', 'need(argc==10,').replace('actual hashes\");', 'actual hashes bus\");')
s=s.replace('need(bool(b.hash_events),"hash events output");', 'need(bool(b.hash_events),"hash events output");b.bus_events.open(argv[9],std::ios::binary);need(bool(b.bus_events),"bus events output");')
s=s.replace('uint64_t candidate_data_beats=0,candidate_overhead_cycles=0,candidate_write_bytes=0;', 'uint64_t candidate_data_beats=0,candidate_overhead_cycles=0,candidate_write_bytes=0,error_prefix_bytes=0;')
s=s.replace('candidate_hash=1469598103934665603ULL;candidate_data_beats=candidate_overhead_cycles=candidate_write_bytes=0;', 'candidate_hash=1469598103934665603ULL;candidate_data_beats=candidate_overhead_cycles=candidate_write_bytes=error_prefix_bytes=0;')
s=s.replace('if(!bus_error)for(unsigned j=0;j<q.bytes;++j)candidate_memory[q.bank][q.addr+j]=uint8_t(q.value>>(j*8));', r"""const unsigned written=bus_error?(q.bytes==8?4:1):q.bytes;
        const Bytes before(candidate_memory[q.bank].begin()+q.addr,candidate_memory[q.bank].begin()+q.addr+q.bytes);
        for(unsigned j=0;j<written;++j)candidate_memory[q.bank][q.addr+j]=uint8_t(q.value>>(j*8));
        if(bus_error){error_prefix_bytes+=written;for(unsigned j=written;j<q.bytes;++j)need(candidate_memory[q.bank][q.addr+j]==before[j],"bus error changed unacknowledged suffix");}""")
s=s.replace('unsigned accepted_bank=b.d.v_reference_bank;', 'unsigned accepted_bank=b.d.v_reference_bank;const Bytes accepted_bytes=b.candidate_memory[accepted_bank];')
s=s.replace('b.bus_error=false;}','need(b.error_prefix_bytes==(BATCH_BYTES==8?4:1),"provisional partial error write not exercised");pass("partial_candidate_write_error_preserves_accepted_bank");b.bus_error=false;}')
s=s.replace('"failure changed accepted reference");', '"failure changed accepted reference");need(b.candidate_memory[accepted_bank]==accepted_bytes,"failed provisional writes changed accepted bank bytes");')
(AREA/'tb_compare.cpp').write_text('// Generated from frozen live bench by make_bench.py; original checks retained.\n'+s)
print('ROW_COMPARISON_BENCH_GENERATED')
