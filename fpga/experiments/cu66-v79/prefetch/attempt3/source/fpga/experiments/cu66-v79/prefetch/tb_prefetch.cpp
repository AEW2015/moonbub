#include "Vcu79_reference_prefetch.h"
#include "verilated.h"
#include <array>
#include <cstdint>
#include <functional>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
static void need(bool v,const std::string&s){if(!v)throw std::runtime_error(s);}
static uint16_t memory_word(uint32_t address){return uint16_t((address*4051u)^(address>>7)^0xa619u);}
static unsigned plane_of(unsigned ordinal){return ordinal<5400?0:ordinal<6750?1:2;}
static unsigned tile_of(unsigned ordinal){return ordinal<5400?ordinal:ordinal<6750?ordinal-5400:ordinal-6750;}
static uint32_t base(unsigned bank){return bank==0?0x080000:bank==1?0x480000:0x880000;}
static uint32_t address_of(unsigned bank,unsigned ordinal){return base(bank)+(plane_of(ordinal)==0?0:plane_of(ordinal)==1?172800:216000)+tile_of(ordinal)*32;}
struct Event {bool epoch=false,lookup=false,response=false,retire=false,command=false,beat=false;};
struct Sim {
 std::unique_ptr<VerilatedContext> context=std::make_unique<VerilatedContext>();Vcu79_reference_prefetch d{context.get()};
 uint32_t random=0x79ab318d;uint64_t cycles=0;unsigned commands=0,beats=0,max_slots=0;uint64_t gen=1;unsigned bank=0;
 bool backend=false,deliver=true,accept=true,randomize=true,check_walk=false,unsolicited=false;unsigned backend_beat=0;uint32_t backend_address=0;
 unsigned inject=0,inject_at=0,backend_inject=0,backend_inject_at=0;
 bool hold_ref=false,hold_request=false;uint32_t held_address=0;std::array<uint32_t,16> held_pixels{};uint64_t held_generation=0;unsigned held_bank=0,held_plane=0,held_tile=0;
 explicit Sim(uint32_t seed=0x79ab318d):random(seed){d.clk=0;d.rst=1;d.abort_i=0;d.epoch_valid=0;d.lease_held=1;d.lookup_valid=0;d.ref_ready=0;d.retire_valid=0;d.mem_req_ready=0;d.mem_rsp_valid=0;d.mem_rsp_data=0;d.mem_rsp_beat=0;d.mem_rsp_last=0;d.mem_rsp_error=0;step();step();d.rst=0;step();}
 uint32_t rng(){random^=random<<13;random^=random>>17;random^=random<<5;return random;}
 void identities(unsigned ordinal){d.lookup_generation=gen;d.lookup_reference_bank=bank;d.lookup_plane=plane_of(ordinal);d.lookup_tile=tile_of(ordinal);d.retire_generation=gen;d.retire_reference_bank=bank;d.retire_plane=plane_of(ordinal);d.retire_tile=tile_of(ordinal);}
 void start(uint64_t generation,unsigned reference_bank){gen=generation;bank=reference_bank;d.epoch_generation=gen;d.epoch_reference_bank=bank;d.epoch_valid=1;wait([&]{return bool(d.epoch_ready);});need(step().epoch,"epoch handshake");d.epoch_valid=0;need(d.epoch_active&&!d.epoch_fault,"valid epoch rejected");}
 void wait(const std::function<bool()>&condition,unsigned bound=2000){uint64_t start=cycles;d.eval();while(!condition()){need(cycles-start<bound,"wait timeout cycle="+std::to_string(cycles)+" lookup_tile="+std::to_string(d.lookup_tile)+" retire_tile="+std::to_string(d.retire_tile)+" slots="+std::to_string(d.slot_occupied)+" full="+std::to_string(d.slot_full)+" fills="+std::to_string(d.tiles_filled)+" retired="+std::to_string(d.tiles_retired)+" lookups="+std::to_string(d.lookups)+" fault="+std::to_string(d.fault_code));step();}}
 Event step(){
  need(cycles<5000000,"finite prototype test watchdog");
  d.mem_req_ready=accept&&(!randomize||(rng()%4!=0));
  d.mem_rsp_valid=unsolicited||(backend&&deliver&&(!randomize||(rng()%3!=0)));
  if(backend){d.mem_rsp_data=memory_word(backend_address+backend_beat);d.mem_rsp_beat=backend_beat;d.mem_rsp_last=backend_beat==7;d.mem_rsp_error=0;
   if(backend_beat==backend_inject_at){if(backend_inject==1)d.mem_rsp_error=1;if(backend_inject==2)d.mem_rsp_beat=(backend_beat+1)%8;if(backend_inject==3)d.mem_rsp_last=1;if(backend_inject==4)d.mem_rsp_last=0;}}
  d.clk=0;d.eval();
  const bool cancelled=d.abort_i||d.epoch_fault||!d.lease_held||d.rst||unsolicited;
  if(hold_ref&&!cancelled){need(d.ref_valid,"held reference response disappeared");need(d.ref_generation==held_generation&&d.ref_reference_bank==held_bank&&d.ref_plane==held_plane&&d.ref_tile==held_tile,"held reference identity changed");for(unsigned i=0;i<16;i++)need(d.ref_pixels[i]==held_pixels[i],"held reference payload changed");}
  if(hold_request&&!cancelled)need(d.mem_req_valid&&d.mem_req_address==held_address,"held memory request changed");
  hold_ref=d.ref_valid&&!d.ref_ready;held_generation=d.ref_generation;held_bank=d.ref_reference_bank;held_plane=d.ref_plane;held_tile=d.ref_tile;for(unsigned i=0;i<16;i++)held_pixels[i]=d.ref_pixels[i];
  hold_request=d.mem_req_valid&&!d.mem_req_ready;held_address=d.mem_req_address;
  unsigned slots=bool(d.slot_occupied&1)+bool(d.slot_occupied&2);max_slots=std::max(max_slots,slots);need(slots<=2,"more than two owned slots");need(bool(d.mem_outstanding)==backend||d.rst,"DUT/backend outstanding ownership differs");
  Event event;event.epoch=d.epoch_valid&&d.epoch_ready;event.lookup=d.lookup_valid&&d.lookup_ready;event.response=d.ref_valid&&d.ref_ready;event.retire=d.retire_valid&&d.retire_ready;event.command=d.mem_req_valid&&d.mem_req_ready;event.beat=d.mem_rsp_valid&&d.mem_rsp_ready;
  const unsigned address=d.mem_req_address;
  if(event.command){need(!backend,"two physical reads outstanding");need((address&7)==0,"unaligned BL8 request");if(check_walk){unsigned ordinal=commands/4,block=commands%4;need(ordinal<8100&&address==address_of(bank,ordinal)+block*8,"canonical all-tile address walk mismatch command="+std::to_string(commands));}}
  d.clk=1;d.eval();context->timeInc(5);d.clk=0;d.eval();context->timeInc(5);cycles++;
  if(event.beat){need(backend,"response without backend command");beats++;backend_beat++;if(backend_beat==8)backend=false;}
  if(event.command){backend=true;backend_beat=0;backend_address=address;backend_inject=inject;backend_inject_at=inject_at;commands++;}
  if(d.rst){backend=false;hold_ref=false;hold_request=false;}
  // A consumed backend beat is withdrawn before observing next-cycle ready signals.
  d.mem_rsp_valid=0;d.eval();return event;
 }
 void check_reference(unsigned ordinal){need(d.ref_valid,"missing reference");need(d.ref_generation==gen&&d.ref_reference_bank==bank&&d.ref_plane==plane_of(ordinal)&&d.ref_tile==tile_of(ordinal),"reference exact identity mismatch");for(unsigned word=0;word<32;word++)need(uint16_t(d.ref_pixels[word/2]>>(16*(word%2)))==memory_word(address_of(bank,ordinal)+word),"full reference tile data mismatch ordinal="+std::to_string(ordinal));}
 void lookup(unsigned ordinal){identities(ordinal);d.lookup_valid=1;wait([&]{return bool(d.lookup_ready);});need(step().lookup,"lookup handshake");d.lookup_valid=0;wait([&]{return bool(d.ref_valid);});check_reference(ordinal);}
 void response(){d.ref_ready=1;need(step().response,"reference response handshake");d.ref_ready=0;}
 void retire(unsigned ordinal,bool unused){identities(ordinal);d.retire_unused=unused;d.retire_valid=1;wait([&]{return bool(d.retire_ready);});need(step().retire,"retire handshake");d.retire_valid=0;}
 void abort_and_drain(){d.lookup_valid=0;d.retire_valid=0;d.abort_i=1;step();d.abort_i=0;wait([&]{return !d.lease_busy;});need(!backend&&!d.ref_valid&&!d.slot_occupied,"abort released accepted read or buffer ownership too early");}
};
static void full_replay(){Sim s;s.check_walk=true;s.start(0x790012345678ULL,2);s.wait([&]{return s.d.slot_full==3;});need(s.commands==8,"two-slot capacity before any retirement");for(unsigned i=0;i<100;i++)s.step();need(s.commands==8,"prefetch exceeded two slots while both retained");
 unsigned hidden=0,visible=0;
 for(unsigned ordinal=0;ordinal<8100;ordinal++){
  const bool unused=ordinal%11==0||ordinal==5399||ordinal==5400||ordinal==6749||ordinal==6750||ordinal==8099;
  if(unused){hidden++;s.retire(ordinal,true);}else{
   visible++;s.lookup(ordinal);for(unsigned i=0;i<2+ordinal%4;i++){s.check_reference(ordinal);s.step();}
   // An unused token cannot discard a delivered/held reference.
   s.d.retire_unused=1;s.d.retire_valid=1;s.d.eval();need(!s.d.retire_ready,"unused retirement claimed a held response");s.step();s.d.retire_valid=0;
   s.response();s.retire(ordinal,false);
  }
 }
 s.wait([&]{return !s.d.lease_busy;});need(!s.d.epoch_fault&&s.d.tiles_filled==8100&&s.d.tiles_retired==8100,"full replay completion counts");need(s.commands==32400&&s.beats==259200&&s.d.read_commands==32400&&s.d.read_beats==259200,"full replay physical command/beat counts");need(s.d.lookups==visible&&s.d.unused_retired==hidden&&s.max_slots==2,"full replay ownership counts");
 std::cout<<"PREFETCH_CASE_PASS case=full_replay tiles=8100 read_commands="<<s.commands<<" read_beats="<<s.beats<<" visible="<<visible<<" unused="<<hidden<<" max_slots="<<s.max_slots<<" cycles="<<s.cycles<<" seed=2041262477 simple_backend=1 physical_sdram_model=0\n";
}
static void identity_and_retirement(){Sim s;s.start(79,1);s.identities(0);s.d.retire_unused=1;s.d.retire_valid=1;s.d.eval();need(!s.d.retire_ready,"early retirement accepted before tile fill");
 // Keep hidden token held from before fill, but introduce a simultaneous lookup when full.
 s.wait([&]{return bool(s.d.slot_full&1);});s.d.lookup_valid=1;s.d.eval();need(s.d.lookup_ready&&!s.d.retire_ready,"lookup/unused retirement must be mutually exclusive for same slot");Event e=s.step();need(e.lookup&&!e.retire,"simultaneous slot double ownership");s.d.lookup_valid=0;
 s.wait([&]{return bool(s.d.ref_valid);});for(unsigned i=0;i<50;i++){need(!s.d.retire_ready,"hidden token freed held response");s.check_reference(0);s.step();}s.d.retire_valid=0;s.response();s.retire(0,false);
 // A late duplicate completion cannot retire a replacement slot.
 s.identities(0);s.d.retire_unused=0;s.d.retire_valid=1;for(unsigned i=0;i<50;i++){s.d.eval();need(!s.d.retire_ready,"late duplicate retirement accepted");s.step();}s.d.retire_valid=0;
 s.identities(1);s.d.lookup_valid=1;
 for(unsigned mismatch=0;mismatch<4;mismatch++){
  s.identities(1);if(mismatch==0)s.d.lookup_generation--;if(mismatch==1)s.d.lookup_reference_bank=2;if(mismatch==2)s.d.lookup_plane=2;if(mismatch==3)s.d.lookup_tile=123;
  for(unsigned i=0;i<8;i++){s.d.eval();need(!s.d.lookup_ready&&!s.d.ref_valid,"wrong/stale lookup identity accepted");s.step();}
 }
 s.d.lookup_valid=0;s.identities(1);s.d.retire_unused=1;s.d.retire_valid=1;
 for(unsigned mismatch=0;mismatch<4;mismatch++){
  s.identities(1);if(mismatch==0)s.d.retire_generation--;if(mismatch==1)s.d.retire_reference_bank=2;if(mismatch==2)s.d.retire_plane=2;if(mismatch==3)s.d.retire_tile=123;
  s.d.eval();need(!s.d.retire_ready,"wrong/stale retirement accepted");s.step();
 }
 s.d.retire_valid=0;s.lookup(1);s.response();s.retire(1,false);s.abort_and_drain();
 std::cout<<"PREFETCH_CASE_PASS case=identity_retirement_held_response concurrent_lookup_unused=1 wrong_identity_fields=4 stale_retire=1 early_retire=1\n";
}
static void hidden_early_retire(){Sim s;s.start(80,0);s.identities(0);s.d.retire_unused=1;s.d.retire_valid=1;unsigned waits=0;while(true){auto e=s.step();if(e.retire)break;need(++waits<2000,"hidden early retirement timeout");}s.d.retire_valid=0;need(s.d.unused_retired==1&&s.d.lookups==0&&!s.d.ref_valid,"hidden retirement did not remain unused");s.abort_and_drain();std::cout<<"PREFETCH_CASE_PASS case=hidden_early_retire backpressured_cycles="<<waits<<"\n";}
static void abort_offsets(){for(unsigned offset=0;offset<8;offset++){Sim s;s.randomize=false;s.start(100+offset,offset%3);s.wait([&]{return s.backend;});s.deliver=false;for(unsigned i=0;i<offset;i++){s.deliver=true;need(s.step().beat,"accepted pre-abort beat");s.deliver=false;}
  s.d.abort_i=1;s.step();s.d.abort_i=0;s.d.epoch_valid=1;s.d.epoch_generation=1000+offset;s.d.epoch_reference_bank=2;
  for(unsigned i=0;i<20;i++){need(!s.d.epoch_ready&&s.d.lease_busy&&!s.d.mem_req_valid&&!s.d.ref_valid,"abort failed to retain lease during missing beats");s.step();}
  s.deliver=true;while(s.backend){need(!s.d.epoch_ready,"new epoch admitted before old accepted BL8 drained");s.step();}s.wait([&]{return bool(s.d.epoch_ready);});need(s.beats==8&&!s.d.slot_occupied,"abort did not drain exactly8 actual beats");need(s.step().epoch,"new epoch blocked after full drain");s.d.epoch_valid=0;need(s.d.epoch_active&&!s.d.epoch_fault,"post-abort epoch rejected");s.abort_and_drain();
 }
 std::cout<<"PREFETCH_CASE_PASS case=abort_all_accepted_offsets offsets=8 missing_beat_hold=1\n";
}
static void abort_unaccepted_and_held(){
 {Sim s;s.accept=false;s.start(120,0);s.wait([&]{return bool(s.d.mem_req_valid);});for(unsigned i=0;i<20;i++)s.step();need(!s.backend,"unaccepted request became owned");s.abort_and_drain();need(s.commands==0,"abort issued blocked request");}
 {Sim s;s.start(121,1);s.lookup(0);for(unsigned i=0;i<20;i++)s.step();s.abort_and_drain();need(!s.d.ref_valid,"abort retained stale held response");}
 std::cout<<"PREFETCH_CASE_PASS case=abort_unaccepted_and_held_response\n";
}
static void faults_and_reset(){
 for(unsigned kind=1;kind<=4;kind++){Sim s;s.randomize=false;s.inject=kind;s.inject_at=kind==4?7:3;s.start(130+kind,1);s.wait([&]{return bool(s.d.epoch_fault);});need(s.d.fault_code==(kind==1?4:kind==2?5:6),"memory fault classification");s.wait([&]{return !s.d.lease_busy;});need(s.beats==8&&s.commands==1&&!s.d.ref_valid&&!s.d.slot_occupied,"malformed response did not drain actual8 beats");}
 {Sim s;s.start(140,2);s.wait([&]{return s.backend;});s.deliver=false;s.d.lease_held=0;s.step();need(s.d.epoch_fault&&s.d.fault_code==2&&s.d.lease_busy,"lost external lease not rejected");s.deliver=true;s.wait([&]{return !s.d.lease_busy;});}
 {Sim s;s.accept=false;s.start(145,0);s.unsolicited=true;s.step();s.unsolicited=false;need(s.d.epoch_fault&&s.d.fault_code==3,"unsolicited excess response not rejected");s.wait([&]{return !s.d.lease_busy;});need(s.commands==0&&s.beats==0,"unsolicited response fabricated accepted ownership");}
 // Reset is a joint module+backend reset, not an abort that drains a live backend.
 {Sim s;s.start(141,0);s.wait([&]{return s.backend;});s.deliver=false;s.d.rst=1;s.step();s.d.rst=0;s.step();need(!s.backend&&!s.d.lease_busy&&!s.d.slot_occupied&&!s.d.ref_valid,"joint reset contract");s.start(142,1);s.lookup(0);s.response();s.retire(0,false);s.abort_and_drain();}
 {Sim s;s.d.epoch_generation=0;s.d.epoch_reference_bank=3;s.d.epoch_valid=1;need(s.step().epoch,"bad epoch must be consumed/rejected");s.d.epoch_valid=0;need(s.d.epoch_fault&&s.d.fault_code==1&&!s.d.lease_busy&&s.commands==0,"bad epoch metadata escaped");}
 std::cout<<"PREFETCH_CASE_PASS case=memory_faults_lease_reset faults=4 joint_backend_reset=1 malformed_last_drain_actual8=1\n";
}
static void atomic_fault_edge(){Sim s;s.randomize=false;s.start(150,1);s.wait([&]{return s.d.tiles_filled==1;});s.accept=false;s.wait([&]{return bool(s.d.mem_req_valid);});need(!s.backend,"unexpected read pending in atomic fault test");s.identities(0);s.d.lookup_valid=1;s.d.retire_valid=1;s.d.retire_unused=1;s.unsolicited=true;s.d.mem_rsp_valid=1;s.d.eval();need(!s.d.mem_req_valid&&!s.d.lookup_ready&&!s.d.retire_ready&&!s.d.ref_valid,"fault edge accepted new work");auto e=s.step();need(!e.command&&!e.lookup&&!e.retire&&s.d.epoch_fault&&s.d.fault_code==3,"atomic protocol fault gating");s.unsolicited=false;s.d.lookup_valid=0;s.d.retire_valid=0;s.wait([&]{return !s.d.lease_busy;});std::cout<<"PREFETCH_CASE_PASS case=atomic_fault_edge no_new_request_lookup_retire=1\n";}
static void stale_epochs(){Sim s;s.start(1000,0);s.abort_and_drain();for(unsigned generation:{1000u,999u}){s.d.epoch_generation=generation;s.d.epoch_reference_bank=1;s.d.epoch_valid=1;need(s.step().epoch,"stale epoch consumed rejection");s.d.epoch_valid=0;need(s.d.epoch_fault&&s.d.fault_code==1&&!s.d.lease_busy,"duplicate/stale epoch acquired lease");}s.start(1001,2);s.lookup(0);s.response();s.retire(0,false);s.abort_and_drain();std::cout<<"PREFETCH_CASE_PASS case=monotonic_epoch duplicate_stale_rejected=2 fresh_recovery=1\n";}
int main(int argc,char**argv){Verilated::commandArgs(argc,argv);std::string phase="full_replay";try{full_replay();phase="identity_retirement";identity_and_retirement();phase="hidden_early_retire";hidden_early_retire();phase="abort_offsets";abort_offsets();phase="abort_unaccepted_held";abort_unaccepted_and_held();phase="faults_reset";faults_and_reset();phase="stale_epochs";stale_epochs();phase="atomic_fault_edge";atomic_fault_edge();std::cout<<"PREFETCH_PASS cases=8 full_replay_tiles=8100 read_commands=32400 read_beats=259200 logical_reference_bytes=128 physical_sdram_model=0 system_integration=0 speedup_proven=0\n";}catch(const std::exception&e){std::cerr<<"FAIL case="<<phase<<" "<<e.what()<<"\n";return 1;}}
