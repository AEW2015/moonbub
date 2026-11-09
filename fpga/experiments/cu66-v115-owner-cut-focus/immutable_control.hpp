#define main frozen_full_main
#include "bench.cpp"
#undef main
#define T(n) d.rootp->cs88_pipeline_v91k__DOT__##n
struct Command {uint32_t bytes,epoch,fid;uint64_t generation;unsigned serial,write,prefetch,tile,ref,qcache;};
class ControlBench {
public:
 Vcs88_pipeline_v91k d;uint64_t cycle=0,accepts=0,deliveries=0,cancels=0,total_accepts=0,total_deliveries=0,total_cancels=0;unsigned next_epoch=1;std::optional<Command> pending;std::optional<Command> live;uint64_t due=0;std::ofstream trace;
 explicit ControlBench(const std::string&path):trace(path){need(bool(trace),"trace open");
 d.clk=0;d.reset=1;d.start=d.abort_packet=d.in_valid=d.in_last=d.cache_valid=d.cache_last=0;
 d.packet_bytes=30109;d.epoch=1;d.serial_clear=0;d.write_overlap=d.read_prefetch=d.tile_overlap=1;
 d.in_data=d.cache_data=0;d.cache_ref_fid=0;d.cache_ref_generation=0;d.accepted_ref_valid=d.accepted_qcache_valid=0;d.accepted_ref_fid=0;d.accepted_ref_generation=0;d.out_ready=d.ref_req_ready=d.mem_req_ready=0;
 d.ref_rsp_valid=d.ref_rsp_error=0;d.ref_rsp_epoch=d.ref_rsp_fid=d.ref_rsp_generation=d.ref_rsp_plane=d.ref_rsp_tile=0;for(unsigned k=0;k<16;++k)d.ref_rsp_pixels[k]=0;
 d.mem_rsp_valid=d.mem_rsp_error=d.mem_rsp_epoch=0;for(unsigned k=0;k<4;++k)d.mem_rsp_data[k]=0;
 tick();d.reset=0;tick();need(d.start_ready,"initial reservation not created after reset");
 }
 Command pins(){return {d.packet_bytes,d.epoch,d.accepted_ref_fid,d.accepted_ref_generation,unsigned(d.serial_clear),unsigned(d.write_overlap),unsigned(d.read_prefetch),unsigned(d.tile_overlap),unsigned(d.accepted_ref_valid),unsigned(d.accepted_qcache_valid)};}
 void check_command(const Command&c){need(T(command_packet_bytes)==c.bytes&&T(command_epoch)==c.epoch&&T(command_accepted_ref_fid)==c.fid&&T(command_accepted_ref_generation)==c.generation&&T(command_serial_clear)==c.serial&&T(command_write_overlap)==c.write&&T(command_read_prefetch)==c.prefetch&&T(command_tile_overlap)==c.tile&&T(command_accepted_ref_valid)==c.ref&&T(command_accepted_qcache_valid)==c.qcache,"accepted external command changed/replayed");}
 void tick(){d.clk=0;d.eval();bool kill=d.reset||d.abort_packet;bool ca=d.start&&d.start_ready&&!kill;bool deliver=T(accepted_start);
 need(ca==bool(T(command_accept)),"independent public command handshake");
 if(kill){if(pending){++total_cancels;if(!d.reset)++cancels;}pending.reset();live.reset();need(!deliver,"kill delivered a queued command");}
 else {
  if(pending){check_command(*pending);need(cycle==due&&deliver,"delivery must be exactly E+1");}
  else need(!deliver,"unowned or duplicate delivery");
  if(ca){need(!pending,"finite command slot overflow");pending=pins();due=cycle+1;++accepts;++total_accepts;}
 }
 auto delivered=pending&&deliver?pending:std::nullopt;
 if(T(command_pending)||T(public_revoked))need(!d.in_ready&&!d.out_valid&&!d.mem_req_valid&&!d.ref_req_valid&&!d.coefficient_valid&&!d.coefficient_ready&&!d.residual_valid&&!d.residual_ready,"hidden public transfer during pending/revocation");
 if(T(command_pending))need(!d.done&&d.error==0&&!d.cache_complete,"public admission did not consume old status/cache");
 trace<<"{\"cycle\":"<<cycle<<",\"reset\":"<<unsigned(d.reset)<<",\"abort\":"<<unsigned(d.abort_packet)<<",\"public_accept\":"<<ca<<",\"local_delivery\":"<<deliver<<",\"sequence\":"<<T(owner_sequence)<<",\"cache_accept\":"<<unsigned(d.cache_valid&&d.cache_ready)<<",\"error\":"<<unsigned(d.error)<<"}\n";
 d.clk=1;d.eval();++cycle;
 if(d.reset){accepts=deliveries=cancels=0;}
 if(delivered){++deliveries;++total_deliveries;live=delivered;pending.reset();
  need(T(coefficients__DOT__frame_epoch)==live->epoch&&T(coefficients__DOT__latched_size)==live->bytes,"producer saw live rather than accepted size/epoch");
  need(T(reconstruction__DOT__frame_epoch)==live->epoch&&T(reconstruction__DOT__snapshot_ref_valid)==live->ref&&T(reconstruction__DOT__snapshot_ref_fid)==live->fid&&T(reconstruction__DOT__snapshot_ref_generation)==live->generation,"reconstruction command snapshot");
 }
 if(pending)check_command(*pending);
 need(T(count_command_accepts)==accepts&&T(count_command_deliveries)==deliveries&&T(count_command_cancels)==cancels,"independent accepted/delivered/canceled command counters");
 need(accepts==deliveries+cancels+unsigned(bool(pending)),"finite command conservation");need(cycle<200000,"focused command watchdog");d.clk=0;d.eval();
 }
 void settle(){for(unsigned k=0;!d.start_ready;++k){need(k<100,"quiescent reservation watchdog");tick();}}
 void abort(){d.start=d.cache_valid=d.in_valid=0;d.abort_packet=1;tick();d.abort_packet=0;tick();settle();}
 void offer(unsigned flags=0){settle();d.packet_bytes=30109+(flags&7);d.epoch=next_epoch++;d.accepted_ref_fid=0x12340000U+flags;d.accepted_ref_generation=0xfedcba9876540000ULL+flags;d.serial_clear=(flags>>0)&1;d.write_overlap=(flags>>1)&1;d.read_prefetch=(flags>>2)&1;d.tile_overlap=(flags>>3)&1;d.accepted_ref_valid=(flags>>4)&1;d.accepted_qcache_valid=(flags>>5)&1;d.start=1;tick();d.start=0;}
 void poison(){d.packet_bytes^=0xffffffffU;d.epoch^=0xffffffffU;d.accepted_ref_fid^=0xffffffffU;d.accepted_ref_generation^=0xffffffffffffffffULL;d.serial_clear^=1;d.write_overlap^=1;d.read_prefetch^=1;d.tile_overlap^=1;d.accepted_ref_valid^=1;d.accepted_qcache_valid^=1;}
 void fault(unsigned mask){
  if(mask&1){T(coefficients__DOT__error)=65;T(coefficients__DOT__fault_o)=1;}
  if(mask&2){T(transform__DOT__error)=5;T(transform__DOT__fault_o)=1;T(transform__DOT__fault_pending_o)=!T(inverse_fault_ack);}
  if(mask&4){T(reconstruction__DOT__error)=3;T(reconstruction__DOT__fault_o)=1;T(reconstruction__DOT__fault_pending_o)=!T(reconstruction_fault_ack);}
  d.eval();
 }
};
int immutable_control_main(int argc,char**argv){try{
 need(argc==6,"control usage cases transforms canonical seed trace");unsigned seed=unsigned(std::stoul(argv[4]));std::mt19937 rng(seed);ControlBench b(argv[5]);auto&d=b.d;unsigned directed=0;
 for(unsigned flags=0;flags<64;++flags){b.offer(flags);b.poison();b.tick();for(unsigned k=0;k<3;++k){b.poison();b.tick();}b.abort();++directed;}
 // Both reset and abort revoke a real accepted-but-undelivered command.
 for(bool reset:{false,true}){b.offer();if(reset)b.d.reset=1;else b.d.abort_packet=1;b.tick();b.d.reset=b.d.abort_packet=0;b.tick();b.settle();++directed;}
 // A held start is one admission while the reservation is consumed.
 b.offer();b.d.start=1;b.tick();for(unsigned k=0;k<5;++k)b.tick();b.d.start=0;b.abort();++directed;
 // Partial preload owns admission; start wins over coincident cache when credit
 // exists, and a blocked start cannot mutate/reset another preload owner.
 b.settle();b.d.cache_ref_fid=77;b.d.cache_ref_generation=88;b.d.cache_valid=1;b.d.cache_last=0;b.d.cache_data=1;b.tick();need(!b.d.start_ready&&T(cache_owned)==1,"partial preload did not revoke frame credit");
 auto index=T(cache_index);b.d.start=1;b.d.cache_data=2;b.tick();need(T(cache_index)==index&&!b.d.cache_ready,"blocked start/cache consumed a hidden beat");b.d.start=0;b.d.cache_valid=0;b.abort();++directed;
 b.d.cache_ref_fid=77;b.d.cache_ref_generation=88;b.d.cache_valid=1;
 for(unsigned i=0;i<1350;++i){b.d.cache_data=rng()%3;b.d.cache_last=i==1349;need(b.d.cache_ready,"reserved preload stalled");b.tick();}
 b.d.cache_valid=0;b.d.cache_last=0;need(b.d.cache_complete&&b.d.start_ready,"terminal cache beat did not atomically return credit");
 b.d.cache_valid=1;b.d.cache_last=1;b.d.cache_data=2;b.d.start=1;b.d.epoch=b.next_epoch++;b.tick();need(!b.d.cache_complete&&T(cache_index)==0,"coincident start/cache lost priority");b.d.start=b.d.cache_valid=0;b.poison();b.tick();b.abort();++directed;
 // Prepared raw child fault states are verification-only adversarial injections
 // into the actual producers, not claims that these good packets reach errors.
 for(unsigned mask=1;mask<8;++mask){b.offer();b.tick();b.fault(mask);unsigned expected=(mask&4)?0xe3U:(mask&2)?0xc5U:65U;need(b.d.error==expected,"same-edge fault priority/mask");b.tick();need(b.d.error==expected&&T(terminal_valid),"first cause not registered");for(unsigned k=0;k<5;++k)b.tick();need(b.d.error==expected,"terminal cause changed during flush");b.abort();++directed;}
 // Old registered kill cannot apply to the new admission sequence.
 b.offer();T(base_kill_valid)=1;T(base_kill_owner)=T(owner_sequence)-1;b.poison();b.tick();need(T(owner_delivered)&&!T(base_abort),"retired kill revoked new delivery");b.abort();++directed;
 // Exercise wrap guard without executing 2^32 commands; explicit prepared
 // frontier fixture, with no accepted physical operations outstanding.
 T(owner_sequence)=0xfffffffeU;b.offer();b.tick();b.d.abort_packet=1;b.tick();b.d.abort_packet=0;for(unsigned k=0;k<10;++k)b.tick();need(!b.d.start_ready,"wrapped owner sequence reissued credit");b.d.reset=1;b.tick();b.d.reset=0;b.tick();need(b.d.start_ready,"drained reset session did not reestablish credit");++directed;
 // Reuse the frozen complete data/memory/reference oracles for real accepted
 // physical obligations; these bytes and responses go through all actual RTL.
 auto cases=load(argv[1]);load_tiles(argv[2]);const Case*good=nullptr,*delta=nullptr;for(const auto&c:cases)if(!c.error&&!c.dense[0].empty()){if(!good)good=&c;if(c.qvalid&&!delta)delta=&c;}need(good&&delta,"physical drain fixtures");
 Bench p(seed,"/tmp/control-events.jsonl",argv[3],"/tmp/control-canonical.tsv");unsigned physical=0;
 for(bool reset:{false,true}){
  p.prepare(*good,1,false);p.preload(*good);p.begin(*good);p.hold_response=true;p.feed_until(11);for(unsigned k=0;!p.pending;++k){need(k<2000000,"accepted write setup watchdog");p.tick();}auto owner=p.pending->req;
  p.d.in_valid=0;if(reset)p.d.reset=1;else p.d.abort_packet=1;p.tick();p.d.reset=p.d.abort_packet=0;need(!p.d.start_ready,"credit forgot accepted write");p.d.start=1;p.d.epoch=++p.next_epoch;p.tick();p.d.start=0;need(p.pending&&p.pending->req==owner&&!p.d.start_ready,"blocked command changed physical owner");p.hold_response=false;p.settle();++physical;
 }
 for(bool reset:{false,true}){
  p.prepare(*delta,1,false);p.preload(*delta);p.begin(*delta);p.hold_reference_response=true;p.feed_until(11);for(unsigned k=0;!p.reference_pending;++k){need(k<4000000,"accepted reference setup watchdog");p.tick();}auto owner=p.reference_pending->req;
  p.d.in_valid=0;if(reset)p.d.reset=1;else p.d.abort_packet=1;p.tick();p.d.reset=p.d.abort_packet=0;need(!p.d.start_ready&&p.d.ref_pending,"credit forgot accepted reference");p.d.start=1;p.d.epoch=++p.next_epoch;p.tick();p.d.start=0;need(p.reference_pending&&p.reference_pending->req==owner&&!p.d.start_ready,"blocked replacement changed reference owner");p.hold_reference_response=false;p.settle();++physical;
 }
 std::cout<<"{\"status\":\"TEST_PASS\",\"seed\":"<<seed<<",\"directed_checks\":"<<directed<<",\"real_physical_drain_checks\":"<<physical<<",\"focused_control_cycles\":"<<b.cycle<<",\"physical_control_cycles\":"<<p.cycle<<",\"accepted_commands\":"<<b.total_accepts<<",\"delivered_commands\":"<<b.total_deliveries<<",\"explicitly_canceled_commands\":"<<b.total_cancels<<",\"backdoor_fault_tests_declared\":7,\"original_bench_checks_removed\":0}\n";return 0;
}catch(const std::exception&e){std::cerr<<"IV114_CONTROL_FAIL "<<e.what()<<'\n';return 1;}}
